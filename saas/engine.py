"""Comment → DM → follow check → link, for any connected account.

Same flow and matching as the single-account app (../app.py), with every call tied to one account.
"""
import hashlib
import json
import os
import random
import re
import time
from datetime import datetime, timezone

import requests

import ai_agent
import push
import store

API_VERSION = os.environ.get("IG_API_VERSION", "v23.0")
GRAPH = f"https://graph.instagram.com/{API_VERSION}"

# Meta's "too many requests" errors. Each failed call still counts, so after one we pause that account.
RATE_LIMIT_CODES = (4, 17, 32, 613)
RATE_LIMIT_BACKOFF = 15 * 60
CANT_OPEN_THREAD = "2534001"  # Instagram refused to open a new DM thread from this comment

# DMs per calendar month on the free plan (0 = no limit). Paid plans can raise it per account.
FREE_MONTHLY_DMS = int(os.environ.get("FREE_MONTHLY_DMS", "1000"))

DEFAULT_COMMENT_REPLY = ("@{username} Check your DM 📩\n"
                         "@{username} Sent! Check your inbox 📥\n"
                         "@{username} Done ✅ check your DMs")
DEFAULT_OPENING = "Hey {username}! 👋 Tap the button below and I'll send it to you."
DEFAULT_BUTTON = "Send me the link"
DEFAULT_FOLLOW = 'Almost there! 👀 Follow me first to unlock it, then tap "I followed" below.'
DEFAULT_FOLLOWED_BUTTON = "I followed ✅"
DEFAULT_EMAIL_ASK = "One last step ✉️ Reply with your email and I'll send it right away."
DEFAULT_EMAIL_RETRY = "Hmm, that doesn't look like an email 🤔 Please type it like name@gmail.com"
DEFAULT_PHONE_ASK = "Almost done 📱 Reply with your WhatsApp number and I'll send it right away."
DEFAULT_PHONE_RETRY = "Hmm, that doesn't look like a phone number 🤔 Please type your 10-digit number, like 98765 43210"
SKIP_BUTTON = "Skip"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")


# ---------- Instagram API for one account ----------

SPIN = re.compile(r"\{([^{}|]*\|[^{}]*)\}")


def vary(text):
    """Natural variations: "{Hi|Hey|Hello} {username}" → one option picked at random each time. {username} is left alone."""
    return SPIN.sub(lambda m: random.choice(m.group(1).split("|")), text or "")


class Instagram:
    def __init__(self, acc):
        self.acc = acc

    def _check(self, r):
        if r.ok:
            return r.json()
        body = r.text.replace(" ", "")
        if '"code":190' in body:
            store.redis("SET", store.account_key(self.acc["id"], "token_dead"), 1)
        elif any(f'"code":{c},' in body for c in RATE_LIMIT_CODES):
            store.redis("SET", store.account_key(self.acc["id"], "rate_limited"), 1, "EX", RATE_LIMIT_BACKOFF)
        raise RuntimeError(f"{r.status_code}: {r.text}")

    def get(self, path, **params):
        if self.acc.get("demo"):  # demo account: sample data, no Instagram call
            import demo
            return demo.ig_get(path, params)
        params["access_token"] = self.acc["token"]
        return self._check(requests.get(f"{GRAPH}/{path}", params=params, timeout=20))

    def post(self, path, payload=None, **params):
        if self.acc.get("demo"):
            return {"id": "demo"}
        params["access_token"] = self.acc["token"]
        return self._check(requests.post(f"{GRAPH}/{path}", params=params, json=payload, timeout=20))

    def delete(self, path, payload=None, **params):
        if self.acc.get("demo"):
            return {"success": True}
        params["access_token"] = self.acc["token"]
        return self._check(requests.delete(f"{GRAPH}/{path}", params=params, json=payload, timeout=20))

    def reply_to_comment(self, comment_id, text):
        return self.post(f"{comment_id}/replies", {"message": vary(text)})

    def send_dm(self, recipient, message):
        """recipient is {"comment_id": ...} for a private reply, or {"id": igsid} inside a chat."""
        if isinstance(message.get("text"), str):
            message = {**message, "text": vary(message["text"])}
        return self.post(f"{self.acc['id']}/messages", {"recipient": recipient, "message": message})

    def send_buttons(self, recipient, text, postbacks=(), links=()):
        """Text with buttons (button template); falls back to quick replies if Instagram rejects it."""
        text = vary(text)
        buttons = ([{"type": "web_url", "title": t[:20], "url": u} for t, u in links]
                   + [{"type": "postback", "title": t[:20], "payload": p} for t, p in postbacks])
        try:
            return self.send_dm(recipient, {"attachment": {"type": "template", "payload": {
                "template_type": "button", "text": text[:640], "buttons": buttons[:3]}}})
        except RuntimeError as first:
            if CANT_OPEN_THREAD in str(first) or is_blocked(self.acc):
                raise  # another message style can't help when the thread, login or rate limit is the problem
            text += "".join(f"\n{t}: {u}" for t, u in links)
            try:
                return self.send_dm(recipient, {"text": text, "quick_replies": [
                    {"content_type": "text", "title": t[:20], "payload": p} for t, p in postbacks]})
            except RuntimeError as second:
                raise RuntimeError(f"button DM: {first} | plain DM: {second}") from second

    def follow_status(self, igsid):
        """Only works after the person has interacted with our DM (e.g. tapped a button)."""
        data = self.get(igsid, fields="username,is_user_follow_business")
        return data.get("username", ""), bool(data.get("is_user_follow_business"))


def is_blocked(acc):
    """Why this account can't send right now ("" when it can)."""
    if store.redis("GET", store.account_key(acc["id"], "token_dead")):
        return "logged_out"
    if store.redis("GET", store.account_key(acc["id"], "rate_limited")):
        return "rate_limited"
    return ""


def month():
    return datetime.now(timezone.utc).strftime("%Y-%m")


PRO_MONTHLY_DMS = int(os.environ.get("PRO_MONTHLY_DMS", "0"))  # 0 = no ReplyInbox limit (Instagram's own limits still apply)


def monthly_limit(acc):
    if acc.get("dm_limit") is not None:
        return int(acc["dm_limit"])
    return PRO_MONTHLY_DMS if store.is_pro(acc) else FREE_MONTHLY_DMS


def dms_this_month(ig_id):
    return store.counts(ig_id).get(f"dms:{month()}", 0)


def over_limit(acc):
    limit = monthly_limit(acc)
    return bool(limit) and dms_this_month(acc["id"]) >= limit


def note_dm(acc):
    store.count(acc["id"], f"dms:{month()}")
    store.count(acc["id"], "dms")


# ---------- matching ----------

def normalize_words(text):
    """Lowercase words without emoji/punctuation, repeated letters or a plural "s" ("PROMPTS!!" -> "prompt")."""
    words = "".join(ch if ch.isalnum() else " " for ch in text.lower()).split()
    out = []
    for w in words:
        w = "".join(ch for i, ch in enumerate(w) if i == 0 or ch != w[i - 1])
        if len(w) > 3 and w.endswith("s"):
            w = w[:-1]
        out.append(w)
    return out


def one_typo_apart(a, b):
    """True if a and b differ by one inserted, deleted, changed or swapped letter."""
    if abs(len(a) - len(b)) > 1:
        return False
    diff = [i for i in range(len(a)) if len(a) == len(b) and a[i] != b[i]]
    if len(diff) == 2 and diff[1] == diff[0] + 1 and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]]:
        return True
    if len(a) > len(b):
        a, b = b, a
    i = j = edits = 0
    while i < len(a) and j < len(b):
        if a[i] != b[j]:
            edits += 1
            if edits > 1:
                return False
            if len(a) == len(b):
                i += 1
        else:
            i += 1
        j += 1
    return edits + (len(b) - j) <= 1


def keyword_matches(keyword, text):
    kw, words = normalize_words(keyword), normalize_words(text)
    if not kw:
        return False
    if len(kw) > 1:  # a phrase must appear as consecutive words
        return f" {' '.join(kw)} " in f" {' '.join(words)} "
    k = kw[0]
    return any(w == k or (len(k) >= 5 and w[0] == k[0] and one_typo_apart(w, k)) for w in words)


def is_keyword_rule(key):
    return str(key).startswith("kw:")


def rule_tags(rule):
    """Tags an automation adds to everyone who goes through it."""
    return [t for t in str(rule.get("tags", "")).split(",") if t.strip()]


def is_live(rule):
    """On, and inside its schedule (starts_at / ends_at, Unix seconds, either optional)."""
    if not rule.get("enabled", True):
        return False
    now = time.time()
    return not (rule.get("starts_at") and now < rule["starts_at"]) and not (rule.get("ends_at") and now >= rule["ends_at"])


def is_story_rule(key):
    return str(key).startswith("story:")


STORY_KEYS = ("story:reply", "story:mention")


def keywords_of(rule):
    return [k.strip() for k in rule.get("keywords", []) if k.strip()]


def excluded(rule, text):
    """True when the comment or DM has one of the automation's excluded words ("scam", "fake"…)."""
    return any(keyword_matches(w, text) for w in rule.get("exclude") or [] if str(w).strip())


def find_rule(rules, media_id, text):
    """(key, rule) for a comment: the reel's own rule, then keyword rules, then the all-reels rule "*"."""
    reels = rules.get("reels", {})
    own = reels.get(media_id) if media_id and media_id != "*" and not is_keyword_rule(media_id) else None
    if own and is_live(own) and not excluded(own, text):
        words = keywords_of(own)
        if not words or any(keyword_matches(k, text) for k in words):
            return media_id, own
    for key, rule in reels.items():
        if (is_keyword_rule(key) and is_live(rule) and rule.get("comments", True) and not excluded(rule, text)
                and any(keyword_matches(k, text) for k in keywords_of(rule))):
            return key, rule
    if own:  # a reel with its own rule never falls through to the all-reels rule
        return None, None
    rule = reels.get("*")
    if not rule or not is_live(rule) or excluded(rule, text):
        return None, None
    words = keywords_of(rule)
    if words and not any(keyword_matches(k, text) for k in words):
        return None, None
    return "*", rule


DELAYS = (0, 1, 2, 5, 10)


def delay_minutes(rule):
    return int(rule.get("delay_min") or 0) if int(rule.get("delay_min") or 0) in DELAYS else 0


def find_live_rule(rules, text):
    """(key, rule) for a comment on a Live broadcast: the "live" automation, if its keywords match."""
    rule = rules.get("reels", {}).get("live")
    if not rule or not is_live(rule) or excluded(rule, text):
        return None, None
    words = keywords_of(rule)
    if words and not any(keyword_matches(k, text) for k in words):
        return None, None
    return "live", rule


def uses_button_flow(rule):
    # the email question and the follow-up need the chat the button opens
    return (rule.get("require_follow") or rule.get("opening_dm") or rule.get("ask_email") or rule.get("ask_phone")
            or rule.get("followup_on"))


def pick_reply(replies):
    """One line at random (identical repeats look like spam), starting with an @mention."""
    line = random.choice([l.strip() for l in replies.splitlines() if l.strip()])
    return line if "{username}" in line else "@{username} " + line


# ---------- flows ----------

def handle_comment(acc, value):
    comment_id, text = value.get("id"), value.get("text", "")
    sender = value.get("from", {})
    username = sender.get("username", "")
    media_id = value.get("media", {}).get("id", "")
    if not comment_id or sender.get("id") == acc["id"]:
        return False  # own comments
    if guard_hides(acc, value):
        return False
    if value.get("parent_id"):
        return False  # replies inside threads
    live = bool(value.get("_live"))
    if media_id and not live and not is_blocked(acc):
        auto_setup_from_comment(acc, media_id)
    key, rule = find_live_rule(store.load_rules(acc["id"]), text) if live else find_rule(store.load_rules(acc["id"]), media_id, text)
    if not rule or is_blocked(acc) or not store.claim(f"s:seen:{acc['id']}:{comment_id}"):
        return False
    if rule.get("once_per_person") and sender.get("id") and not store.claim(
            f"s:seen:{acc['id']}:once:{key}:{media_id}:{sender['id']}", 60 * 86400):
        store.log_activity(acc["id"], media_id, username, text, "dm", "ok", "Skipped: already sent to this person for this post")
        return False
    store.media_count(acc["id"], media_id, "keyword")
    store.touch_contact(acc["id"], username, keyword=(keywords_of(rule) or [""])[0], source=media_id, tags=rule_tags(rule))
    ig = Instagram(acc)
    fill = lambda s: s.replace("{username}", username)

    if over_limit(acc):
        store.log_activity(acc["id"], media_id, username, text, "dm", "error",
                           f"Monthly DM limit reached ({monthly_limit(acc)}). Upgrade to keep sending.")
    elif delay_minutes(rule):
        store.schedule(time.time() + delay_minutes(rule) * 60, {"kind": "comment_dm", "acc": acc["id"], "comment_id": comment_id,
                                                                "key": key, "media_id": media_id, "username": username, "text": text[:300]})
        store.log_activity(acc["id"], media_id, username, text, "dm", "ok", f"DM queued for {delay_minutes(rule)} min")
    else:
        send_comment_dm(acc, ig, comment_id, key, rule, media_id, username, text)

    reply = rule.get("comment_reply", DEFAULT_COMMENT_REPLY) if rule.get("replies_on", True) and not live else ""
    if reply.strip():
        try:
            ig.reply_to_comment(comment_id, fill(pick_reply(reply)))
            store.count(acc["id"], "comment_replies")
            store.log_activity(acc["id"], media_id, username, text, "comment_reply", "ok")
        except Exception as e:
            store.log_activity(acc["id"], media_id, username, text, "comment_reply", "error", str(e))
    return True


# ---------- integrations: new leads to Google Sheets, Zapier, Make or any webhook ----------

def safe_hook_url(url):
    """The URL if it's https to a public address, else "" (so it can't reach the server's own network)."""
    import ipaddress
    import socket
    from urllib.parse import urlparse
    url = str(url or "").strip()
    parts = urlparse(url)
    if parts.scheme != "https" or not parts.hostname or len(url) > 500:
        return ""
    try:
        addrs = {a[4][0] for a in socket.getaddrinfo(parts.hostname, parts.port or 443)}
    except OSError:
        return ""
    for a in addrs:
        ip = ipaddress.ip_address(a)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            return ""
    return url


def send_hook(acc, event, data, test=False):
    """POSTs {"event", "account", "at", ...data} to the creator's webhook. Never raises; returns an error text or ""."""
    hook = acc.get("hook") or {}
    if not (hook.get("enabled") or test) or not hook.get("url") or acc.get("demo"):
        return "" if not test else ("" if acc.get("demo") else "Add a webhook URL first.")
    url = safe_hook_url(hook["url"])
    if not url:
        return "The webhook URL must be https and reach the public internet."
    payload = {"event": event, "account": acc.get("username", ""), "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **data}
    try:
        r = requests.post(url, json=payload, timeout=4, allow_redirects=False)
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}")
        store.count(acc["id"], "hook_sent")
        return ""
    except Exception as e:
        store.log_activity(acc["id"], "integration", data.get("username", ""), event, "integration", "error", str(e)[:200])
        return f"Couldn't reach the webhook: {str(e)[:120]}"


# ---------- A/B test of the first DM ----------

def opening(rule):
    """(variant, text) of the first DM: "A" or "B" at random when the rule has a second version, else ("", text)."""
    a = rule.get("opening_dm") or DEFAULT_OPENING
    if not rule.get("opening_dm_b"):
        return "", a
    return ("A", a) if random.random() < 0.5 else ("B", rule["opening_dm_b"])


def ab_key(acc, key):
    return store.account_key(acc["id"], f"ab:{key}")


def ab_count(acc, key, variant, field):
    if variant in ("A", "B"):
        store.redis("HINCRBY", ab_key(acc, key), f"{field}_{variant}", 1)


def ab_stats(acc, key):
    return store.hash_all(ab_key(acc, key))


def ab_variant(acc, igsid, key):
    return store.redis("GET", store.account_key(acc["id"], f"abv:{igsid}:{key}")) or ""


def send_comment_dm(acc, ig, comment_id, key, rule, media_id, username, text, retry=False):
    """The private-reply DM to a comment. When Instagram refuses to open the chat, the comment is queued for a retry."""
    fill = lambda s: s.replace("{username}", username)
    action = "opening_dm" if uses_button_flow(rule) else "dm"
    try:
        variant = ""
        if uses_button_flow(rule):
            variant, first = opening(rule)
            ig.send_buttons({"comment_id": comment_id}, fill(first),
                            postbacks=[(rule.get("button_text") or DEFAULT_BUTTON, f"GET|{key}|{media_id}|{variant}".rstrip("|"))])
            ab_count(acc, key, variant, "sent")
        elif rule.get("dm"):
            ig.send_dm({"comment_id": comment_id}, {"text": fill(rule["dm"])})
            store.count(acc["id"], "links_sent")
            store.media_count(acc["id"], media_id, "link")
        note_dm(acc)
        store.rule_count(acc["id"], key, "runs")
        store.media_count(acc["id"], media_id, "dm")
        store.log_activity(acc["id"], media_id, username, text, action, "ok", "sent on retry" if retry else "")
        return True
    except Exception as e:
        store.log_activity(acc["id"], media_id, username, text, action, "error", str(e))
        if CANT_OPEN_THREAD in str(e) and not retry:
            add_retry(acc, comment_id, {"key": key, "media_id": media_id, "username": username, "text": text[:300],
                                        "at": int(time.time())})
        return False


# ---------- refused DMs and comments from before the automation ----------

PRIVATE_REPLY_WINDOW = 7 * 86400  # Instagram allows a DM reply to a comment only within 7 days
MAX_RETRIES = 500


def retry_key(acc):
    return store.account_key(acc["id"], "retry")


def add_retry(acc, comment_id, item):
    if int(store.redis("HLEN", retry_key(acc)) or 0) < MAX_RETRIES:
        store.redis("HSET", retry_key(acc), comment_id, json.dumps(item, ensure_ascii=False))


def pending_retries(acc):
    flat = store.redis("HGETALL", retry_key(acc)) or []
    return {flat[i]: json.loads(flat[i + 1]) for i in range(0, len(flat), 2)}


def retry_failed_dms(acc, max_sends=30):
    """Tries refused comment DMs again while Instagram's 7-day window is open (with a day of margin)."""
    counts = {"sent": 0, "still_failing": 0, "expired": 0, "skipped": ""}
    if is_blocked(acc) or acc.get("paused"):
        counts["skipped"] = "The automation is paused or Instagram is blocking requests right now."
        return counts
    rules = store.load_rules(acc["id"]).get("reels", {})
    ig = Instagram(acc)
    for comment_id, item in pending_retries(acc).items():
        rule = rules.get(item["key"])
        if not rule or not is_live(rule) or time.time() - item["at"] > PRIVATE_REPLY_WINDOW - 86400:
            store.redis("HDEL", retry_key(acc), comment_id)
            counts["expired"] += 1
        elif counts["sent"] + counts["still_failing"] >= max_sends or over_limit(acc) or is_blocked(acc):
            break
        elif send_comment_dm(acc, ig, comment_id, item["key"], rule, item["media_id"], item["username"], item["text"], retry=True):
            store.redis("HDEL", retry_key(acc), comment_id)
            counts["sent"] += 1
        else:
            counts["still_failing"] += 1
    return counts


def backfill_comments(acc, media_id, max_sends=50):
    """Runs a reel's automation on comments posted before it was set up (last 7 days only)."""
    reels = store.load_rules(acc["id"]).get("reels", {})
    if not (media_id in reels or "*" in reels or any(is_keyword_rule(k) for k in reels)):
        raise RuntimeError("This reel has no automation yet.")
    counts = {"sent": 0, "too_old": 0, "already_done_or_no_match": 0, "more_left": False}
    ig = Instagram(acc)
    params = {"fields": "id,text,timestamp,from,username", "limit": 50}
    for _ in range(20):  # up to 1,000 comments
        page = ig.get(f"{media_id}/comments", **params)
        for c in page.get("data", []):
            if counts["sent"] >= max_sends or over_limit(acc) or is_blocked(acc):
                counts["more_left"] = True
                return counts
            try:
                age = time.time() - datetime.strptime(c["timestamp"], "%Y-%m-%dT%H:%M:%S%z").timestamp()
            except (KeyError, ValueError):
                age = 0
            if age > PRIVATE_REPLY_WINDOW - 3600:
                counts["too_old"] += 1
                continue
            sender = c.get("from") or {"username": c.get("username", "")}
            value = {"id": c["id"], "text": c.get("text", ""), "from": sender, "media": {"id": media_id}}
            if handle_comment(acc, value):
                counts["sent"] += 1
            else:
                counts["already_done_or_no_match"] += 1
        after = (page.get("paging") or {}).get("cursors", {}).get("after")
        if not after or not (page.get("paging") or {}).get("next"):
            break
        params["after"] = after
    return counts


# ---------- comment guard: hide spam and blocked words ----------

LINK_RE = re.compile(r"https?://|www\.|\b[a-z0-9-]+\.(?:com|in|net|org|io|me|ly|xyz|link|shop|site|online|co|app|info|biz)\b", re.I)


def guard_settings(acc):
    g = acc.get("guard") or {}
    return {"enabled": bool(g.get("enabled")), "words": g.get("words") or [], "links": bool(g.get("links"))}


def guard_reason(acc, text):
    """Why a comment should be hidden, or "" to keep it."""
    g = guard_settings(acc)
    if not g["enabled"]:
        return ""
    if g["links"] and LINK_RE.search(text or ""):
        return "link"
    words = f" {' '.join(normalize_words(text))} "
    for w in g["words"]:
        phrase = " ".join(normalize_words(w))
        if phrase and f" {phrase} " in words:
            return f'blocked word "{w}"'
    return ""


def guard_hides(acc, value):
    """Hides the comment when the guard catches it. True when hidden (the automation then skips it)."""
    reason = guard_reason(acc, value.get("text", ""))
    if not reason or is_blocked(acc) or not store.claim(f"s:seen:{acc['id']}:hide:{value['id']}"):
        return bool(reason)
    who = (value.get("from") or {}).get("username", "")
    media_id = (value.get("media") or {}).get("id", "")
    try:
        Instagram(acc).post(value["id"], hide="true")
        store.count(acc["id"], "hidden_comments")
        store.log_activity(acc["id"], media_id, who, value.get("text", ""), "comment_hidden", "ok", reason)
    except Exception as e:
        store.log_activity(acc["id"], media_id, who, value.get("text", ""), "comment_hidden", "error", str(e))
    return True


# ---------- giveaway picker ----------

def all_comments(acc, media_id, max_pages=40):
    """Every top-level comment on a post (up to 2,000)."""
    ig, out = Instagram(acc), []
    params = {"fields": "id,text,timestamp,from,username", "limit": 50}
    for _ in range(max_pages):
        page = ig.get(f"{media_id}/comments", **params)
        out += page.get("data", [])
        after = (page.get("paging") or {}).get("cursors", {}).get("after")
        if not after or not (page.get("paging") or {}).get("next"):
            break
        params["after"] = after
    return out


def pick_winners(acc, media_id, winners=1, keyword="", min_mentions=0, followed_only=False, exclude=()):
    """Draws random winners among the people who commented (one entry per person) and match the filters."""
    import secrets
    followed = {c["username"].lower() for c in store.contacts(acc["id"]) if c.get("followed") and c.get("username")}
    skip = {e.lower().lstrip("@") for e in exclude if e} | {acc.get("username", "").lower()}
    entries = {}
    for c in all_comments(acc, media_id):
        user = ((c.get("from") or {}).get("username") or c.get("username") or "").lower()
        text = c.get("text", "")
        if (not user or user in skip or user in entries or (keyword and not keyword_matches(keyword, text))
                or text.count("@") < min_mentions or (followed_only and user not in followed)):
            continue
        entries[user] = {"username": user, "text": text[:300], "comment_id": c.get("id"), "timestamp": c.get("timestamp")}
    pool = list(entries.values())
    rng = secrets.SystemRandom()
    chosen = rng.sample(pool, min(max(int(winners), 1), len(pool))) if pool else []
    result = {"media_id": media_id, "entries": len(pool), "winners": chosen, "at": int(time.time()),
              "filters": {"keyword": keyword, "min_mentions": min_mentions, "followed_only": followed_only}}
    key = store.account_key(acc["id"], "giveaways")
    store.redis("LPUSH", key, json.dumps(result, ensure_ascii=False))
    store.redis("LTRIM", key, 0, 9)
    return result


def dm_keyword_match(rules, text):
    """(key, rule) of the first keyword automation a DM matches: keyword rules first, then reel rules."""
    ordered = sorted(((k, r) for k, r in rules.items() if not is_story_rule(k) and k not in ("next", "live")), key=lambda kv: not is_keyword_rule(kv[0]))
    return next(((k, r) for k, r in ordered if is_live(r) and not excluded(r, text)
                 and any(keyword_matches(w, text) for w in keywords_of(r))), (None, None))


def username_of(ig, igsid):
    try:
        return ig.get(igsid, fields="username").get("username", "")
    except Exception:
        return ""


def send_rule_dm(acc, ig, igsid, key, rule, username, text, action):
    """Starts a rule's DM flow inside an open chat: the button (and follow gate) or the final DM straight away."""
    who = username or igsid
    if over_limit(acc):
        store.log_activity(acc["id"], key, who, text, action, "error", "Monthly DM limit reached.")
        return False
    fill = lambda s: s.replace("{username}", username)
    try:
        if uses_button_flow(rule):
            variant, first = opening(rule)
            ig.send_buttons({"id": igsid}, fill(first),
                            postbacks=[(rule.get("button_text") or DEFAULT_BUTTON, f"GET|{key}||{variant}".rstrip("|"))])
            ab_count(acc, key, variant, "sent")
            store.log_activity(acc["id"], key, who, text, action, "ok")
        else:
            deliver(acc, ig, igsid, key, rule, username, "", text, action)
        note_dm(acc)
        store.rule_count(acc["id"], key, "runs")
        return True
    except Exception as e:
        store.log_activity(acc["id"], key, who, text, action, "error", str(e))
        return False


def handle_dm_text(acc, igsid, text, mid=""):
    """Someone DMed a keyword: start the same flow inside that chat (works even when comment DMs are refused).
    Any other message goes to the AI DM agent when it's on."""
    if is_blocked(acc) or handle_email_reply(acc, igsid, text):
        return
    key, rule = dm_keyword_match(store.load_rules(acc["id"]).get("reels", {}), text)
    if not rule:
        if not send_welcome(acc, igsid):
            handle_ai_dm(acc, igsid, text, mid)
        return
    if not store.claim(f"s:seen:{acc['id']}:dm:{igsid}:{key}:{int(time.time() // 600)}"):
        return
    ig = Instagram(acc)
    username = username_of(ig, igsid)
    store.touch_contact(acc["id"], username, igsid, keyword=(keywords_of(rule) or [""])[0], source="dm", tags=rule_tags(rule))
    send_rule_dm(acc, ig, igsid, key, rule, username, text, "dm_keyword")


def handle_story_reply(acc, igsid, text, story_id="", mid=""):
    """Someone replied to a story: a keyword automation if the reply has one, else the story rule, else the AI."""
    if is_blocked(acc):
        return
    rules = store.load_rules(acc["id"]).get("reels", {})
    if dm_keyword_match(rules, text)[1]:
        return handle_dm_text(acc, igsid, text, mid)
    rule = rules.get("story:reply")
    words = keywords_of(rule or {})
    if not rule or not is_live(rule) or excluded(rule, text) or (words and not any(keyword_matches(w, text) for w in words)):
        return handle_ai_dm(acc, igsid, text, mid)
    # once per person per story (or per day when Instagram doesn't say which story)
    if not store.claim(f"s:seen:{acc['id']}:story:{igsid}:{story_id or int(time.time() // 86400)}", 2 * 86400):
        return
    ig = Instagram(acc)
    username = username_of(ig, igsid)
    store.touch_contact(acc["id"], username, igsid, keyword=(words or ["STORY"])[0], source="story", tags=rule_tags(rule))
    if send_rule_dm(acc, ig, igsid, "story:reply", rule, username, text, "story_reply"):
        store.count(acc["id"], "story_replies")


def handle_story_mention(acc, igsid):
    """Someone mentioned the creator in their story: one thank-you DM per person per day."""
    rule = store.load_rules(acc["id"]).get("reels", {}).get("story:mention")
    if not rule or not is_live(rule) or is_blocked(acc):
        return
    if not store.claim(f"s:seen:{acc['id']}:mention:{igsid}:{int(time.time() // 86400)}", 2 * 86400):
        return
    ig = Instagram(acc)
    username = username_of(ig, igsid)
    store.touch_contact(acc["id"], username, igsid, source="story_mention", tags=rule_tags(rule))
    if send_rule_dm(acc, ig, igsid, "story:mention", rule, username, "(mentioned you in their story)", "story_mention"):
        store.count(acc["id"], "story_mentions")


def handle_ai_dm(acc, igsid, text, mid=""):
    """The AI DM agent: answers from the creator's products, links and FAQ, or hands the chat to them."""
    s = ai_agent.settings(acc)
    if not s["enabled"]:
        return
    once = mid or hashlib.sha1(f"{igsid}|{text}".encode()).hexdigest()[:16] + f":{int(time.time() // 300)}"
    if not store.claim(f"s:seen:{acc['id']}:ai:{once}", 86400):
        return  # Instagram sometimes delivers a message twice
    ig = Instagram(acc)
    try:
        username = ig.get(igsid, fields="username").get("username", "")
    except Exception:
        username = ""
    store.touch_contact(acc["id"], username, igsid, source="dm")
    thread = ai_agent.add_message(acc["id"], igsid, "fan", text, username, unread=True)
    if thread.get("status") == "you":
        return  # the creator took over this chat
    who = username or igsid

    def hand_over(reason, suggestion=""):
        thread = ai_agent.update_thread(acc["id"], igsid, status="needs_you", reason=reason[:200], suggestion=suggestion)
        if (acc.get("notify") or {}).get("handoff", True):
            push.notify(acc, f"@{username or 'Someone'} needs you", reason[:120], "/app/inbox")
        store.log_activity(acc["id"], "ai", who, text, "ai_handoff", "ok", reason)
        if s["send_hold"] and s["hold_message"] and not thread.get("hold_sent"):
            try:
                ig.send_dm({"id": igsid}, {"text": s["hold_message"]})
                ai_agent.add_message(acc["id"], igsid, "ai", s["hold_message"], hold_sent=True)
            except Exception as e:
                store.log_activity(acc["id"], "ai", who, text, "ai_reply", "error", str(e))

    if thread.get("status") == "needs_you":
        return  # still waiting for the creator: don't answer around them
    if not ai_agent.ready(acc):
        return hand_over("AI isn't set up on the server yet.")
    if ai_agent.over_quota(acc):
        return hand_over(ai_agent.quota_reason(acc))
    try:
        answer = ai_agent.answer(acc, ai_agent.messages(acc["id"], igsid), s)
    except Exception as e:
        return hand_over(f"The AI couldn't answer ({str(e)[:120]}).")
    ai_agent.note_use(acc)
    if answer["needs_human"]:
        return hand_over(answer["reason"] or "Needs your answer.", answer["suggested_reply"])
    if not answer["reply"]:
        return
    try:
        ig.send_dm({"id": igsid}, {"text": answer["reply"][:1000]})
        ai_agent.add_message(acc["id"], igsid, "ai", answer["reply"])
        store.count(acc["id"], "ai_replies")
        store.log_activity(acc["id"], "ai", who, text, "ai_reply", "ok")
    except Exception as e:
        ai_agent.update_thread(acc["id"], igsid, status="needs_you", reason="Instagram didn't deliver the AI reply.",
                               suggestion=answer["reply"])
        store.log_activity(acc["id"], "ai", who, text, "ai_reply", "error", str(e))


# ---------- chat menu: ice breakers shown when someone opens the creator's DMs ----------

MAX_ICE = 4  # Instagram's limit


def ice_settings(acc):
    ice = acc.get("ice") or {}
    return {"enabled": bool(ice.get("enabled")), "items": ice.get("items") or []}


def publish_ice(acc):
    """Puts the questions on the creator's Instagram chat (or removes them). Raises when Instagram refuses."""
    ice, ig = ice_settings(acc), Instagram(acc)
    if ice["enabled"] and ice["items"]:
        ig.post("me/messenger_profile", {"platform": "instagram", "ice_breakers": [{"locale": "default", "call_to_actions": [
            {"question": it["question"], "payload": f"ICE|{i}"} for i, it in enumerate(ice["items"][:MAX_ICE])]}]})
    else:
        ig.delete("me/messenger_profile", {"platform": "instagram", "fields": ["ice_breakers"]})


def handle_ice(acc, igsid, index):
    """They tapped one of the chat menu questions: send the answer, or start the chosen keyword automation."""
    items = ice_settings(acc)["items"]
    if not index.isdigit() or int(index) >= len(items) or is_blocked(acc):
        return
    item = items[int(index)]
    if not store.claim(f"s:seen:{acc['id']}:ice:{igsid}:{index}:{int(time.time() // 60)}", 120):
        return
    ig = Instagram(acc)
    username = username_of(ig, igsid)
    store.touch_contact(acc["id"], username, igsid, source="chat_menu")
    rule = store.load_rules(acc["id"]).get("reels", {}).get(item.get("rule", ""))
    if rule and is_live(rule):
        send_rule_dm(acc, ig, igsid, item["rule"], rule, username, item["question"], "chat_menu")
        return
    try:
        ig.send_dm({"id": igsid}, {"text": item.get("answer", "").replace("{username}", username)})
        store.count(acc["id"], "chat_menu_answers")
        store.log_activity(acc["id"], "chat_menu", username or igsid, item["question"], "chat_menu", "ok")
    except Exception as e:
        store.log_activity(acc["id"], "chat_menu", username or igsid, item["question"], "chat_menu", "error", str(e))


def handle_button(acc, igsid, payload):
    """They tapped "Send me the link" or "I followed": check the follow, then send the link or ask again."""
    step, key, media_id, variant = (payload.split("|") + ["", "", ""])[:4]
    if step == "ICE":
        return handle_ice(acc, igsid, key)
    if step == "MENU":
        return handle_menu(acc, igsid, key, media_id)
    if step == "KW":
        return start_keyword(acc, igsid, key)
    if step == "GET" and store.claim(f"s:seen:{acc['id']}:click:{igsid}:{key}", 30 * 86400):
        store.rule_count(acc["id"], key, "clicks")
    if step == "GET" and variant in ("A", "B"):
        store.redis("SET", store.account_key(acc["id"], f"abv:{igsid}:{key}"), variant, "EX", 7 * 86400)
        if store.claim(f"s:seen:{acc['id']}:abtap:{igsid}:{key}", 7 * 86400):
            ab_count(acc, key, variant, "tap")
    media_id = media_id or (key if key.isdigit() else "")  # older buttons carried only the rule key
    rule = store.load_rules(acc["id"]).get("reels", {}).get(key)
    if step not in ("GET", "FOLLOWED", *SKIP_STEPS) or not rule or is_blocked(acc):
        return
    ig = Instagram(acc)
    username, follows = "", True
    if rule.get("require_follow"):
        try:
            username, follows = ig.follow_status(igsid)
        except Exception as e:
            follows = False  # strict gate: no confirmed follow, no link
            store.log_activity(acc["id"], key, igsid, payload, "follow_check", "error", str(e))
    try:
        if follows:
            skipped = SKIP_STEPS.get(step)
            if skipped and rule.get(f"{skipped}_required"):
                return
            if rule.get("ask_email") or rule.get("ask_phone"):
                username = username or username_of(ig, igsid)
                if ask_next(acc, ig, igsid, key, rule, media_id, username, after=skipped):
                    return
            store.redis("DEL", pending_key(acc, igsid))
            deliver(acc, ig, igsid, key, rule, username, media_id, payload)
            if step == "FOLLOWED" and rule.get("require_follow") and store.claim(f"s:seen:{acc['id']}:gate:{igsid}"):
                store.count(acc["id"], "gate_follows")
                store.rule_count(acc["id"], key, "follows")
                send_hook(acc, "follow", {"username": username, "automation": key})
                store.media_count(acc["id"], media_id, "follow")
                ab_count(acc, key, ab_variant(acc, igsid, key), "follow")
            store.touch_contact(acc["id"], username, igsid, followed=bool(rule.get("require_follow") and follows))
        else:
            ig.send_buttons({"id": igsid}, (rule.get("follow_dm") or DEFAULT_FOLLOW).replace("{username}", username),
                            links=[("Open profile", f"https://www.instagram.com/{acc['username']}/")],
                            postbacks=[(rule.get("followed_button_text") or DEFAULT_FOLLOWED_BUTTON,
                                        f"FOLLOWED|{key}|{media_id}")])
            store.log_activity(acc["id"], key, username or igsid, payload, "follow_prompt", "ok")
    except Exception as e:
        store.log_activity(acc["id"], key, username or igsid, payload, "dm", "error", str(e))


def deliver(acc, ig, igsid, key, rule, username, media_id, detail, action="dm"):
    """Sends the rule's final DM (message and link, or a menu of choices). Raises when Instagram refuses."""
    if not rule.get("dm"):
        raise RuntimeError("The final DM is empty: add your message and link to this rule")
    text = track_text(acc, key, rule["dm"].replace("{username}", username), rule)
    menu = [m for m in rule.get("menu") or [] if m.get("title")][:3]
    if menu:
        ig.send_buttons({"id": igsid}, text, postbacks=[(m["title"], f"MENU|{key}|{i}") for i, m in enumerate(menu)])
    elif rule.get("dm_button_url"):
        ig.send_buttons({"id": igsid}, text, links=[(rule.get("dm_button_text") or "Open", track(acc, key, rule["dm_button_url"], rule))])
    else:
        ig.send_dm({"id": igsid}, {"text": text})
    store.count(acc["id"], "links_sent")
    store.media_count(acc["id"], media_id, "link")
    store.log_activity(acc["id"], key, username or igsid, detail, action, "ok")
    if store.claim(f"s:seen:{acc['id']}:ablink:{igsid}:{key}", 7 * 86400):
        ab_count(acc, key, ab_variant(acc, igsid, key), "link")
    schedule_followup(acc, igsid, key, rule, username)


def handle_menu(acc, igsid, key, index):
    """They tapped one choice of a DM menu: send that choice's message and link."""
    rule = store.load_rules(acc["id"]).get("reels", {}).get(key) or {}
    menu = rule.get("menu") or []
    if not index.isdigit() or int(index) >= len(menu) or is_blocked(acc):
        return
    if not store.claim(f"s:seen:{acc['id']}:menu:{igsid}:{key}:{index}:{int(time.time() // 60)}", 120):
        return
    item, ig = menu[int(index)], Instagram(acc)
    username = username_of(ig, igsid)
    text = track_text(acc, key, (item.get("text") or item["title"]).replace("{username}", username), rule)
    try:
        if item.get("url"):
            ig.send_buttons({"id": igsid}, text, links=[(item.get("button") or "Open", track(acc, key, item["url"], rule))])
        else:
            ig.send_dm({"id": igsid}, {"text": text})
        store.rule_count(acc["id"], key, f"menu_{index}")
        store.count(acc["id"], "links_sent")
        store.log_activity(acc["id"], key, username or igsid, item["title"], "menu_choice", "ok")
    except Exception as e:
        store.log_activity(acc["id"], key, username or igsid, item["title"], "menu_choice", "error", str(e))


# ---------- link click tracking ----------

# Short links for click counting; SHORT_LINK_URL overrides (e.g. the vercel.app address while the main domain is down).
PUBLIC_URL = (os.environ.get("SHORT_LINK_URL") or os.environ.get("PUBLIC_URL", "")).rstrip("/")
URL_RE = re.compile(r"https?://[^\s<>\"']+")


def track(acc, key, url, rule=None):
    """A short /l/<code> link that counts the click and redirects to url (off when the automation turns tracking off)."""
    if not url or not PUBLIC_URL or (rule or {}).get("track_links") is False or url.startswith(PUBLIC_URL + "/l/"):
        return url
    code = hashlib.sha1(f"{acc['id']}|{key}|{url}".encode()).hexdigest()[:10]
    store.redis("SET", f"s:link:{code}", json.dumps({"acc": acc["id"], "key": key, "url": url}), "EX", 180 * 86400)
    return f"{PUBLIC_URL}/l/{code}"


def track_text(acc, key, text, rule=None):
    return URL_RE.sub(lambda m: track(acc, key, m.group(0), rule), text or "")


def link_click(code):
    """The target of a short link, counting the click; "" when unknown."""
    raw = store.redis("GET", f"s:link:{code}")
    if not raw:
        return ""
    link = json.loads(raw)
    store.rule_count(link["acc"], link["key"], "link_clicks")
    store.count(link["acc"], "link_clicks")
    return link["url"]


# ---------- welcome message for people who DM for the first time ----------

def welcome_settings(acc):
    w = acc.get("welcome") or {}
    return {"enabled": bool(w.get("enabled")), "text": w.get("text", ""), "buttons": w.get("buttons") or []}


def send_welcome(acc, igsid):
    """True when this person got the welcome message now (only the first time they ever DM)."""
    w = welcome_settings(acc)
    if not w["enabled"] or not w["text"].strip() or not store.claim(f"s:seen:{acc['id']}:welcomed:{igsid}", 365 * 86400):
        return False
    ig = Instagram(acc)
    username = username_of(ig, igsid)
    text = track_text(acc, "welcome", w["text"].replace("{username}", username))
    links = [(b["title"], track(acc, "welcome", b["value"])) for b in w["buttons"] if b.get("type") == "url" and b.get("value")]
    posts = [(b["title"], f"KW|{b['value']}") for b in w["buttons"] if b.get("type") == "kw" and b.get("value")]
    try:
        if links or posts:
            ig.send_buttons({"id": igsid}, text, links=links[:3], postbacks=posts[:3 - len(links[:3])])
        else:
            ig.send_dm({"id": igsid}, {"text": text})
        store.touch_contact(acc["id"], username, igsid, source="dm")
        store.count(acc["id"], "welcomes")
        store.log_activity(acc["id"], "welcome", username or igsid, "", "welcome", "ok")
        return True
    except Exception as e:
        store.log_activity(acc["id"], "welcome", username or igsid, "", "welcome", "error", str(e))
        return False


def start_keyword(acc, igsid, key):
    """A welcome button that starts a keyword automation."""
    rule = store.load_rules(acc["id"]).get("reels", {}).get(key)
    if not rule or not is_live(rule) or is_blocked(acc):
        return
    if not store.claim(f"s:seen:{acc['id']}:dm:{igsid}:{key}:{int(time.time() // 600)}"):
        return
    ig = Instagram(acc)
    username = username_of(ig, igsid)
    store.touch_contact(acc["id"], username, igsid, keyword=(keywords_of(rule) or [""])[0], source="dm", tags=rule_tags(rule))
    send_rule_dm(acc, ig, igsid, key, rule, username, "(welcome button)", "dm_keyword")


# ---------- people who messaged in the last 24 hours (for "Send to recent chats") ----------

def note_recent(acc, igsid):
    if igsid and igsid != acc["id"]:
        store.redis("HSET", store.account_key(acc["id"], "recent"), igsid, int(time.time()))


def recent_chats(acc, hours=23):
    """igsids who messaged within Instagram's 24-hour window (23 h to be safe); older ones are dropped."""
    key = store.account_key(acc["id"], "recent")
    flat = store.redis("HGETALL", key) or []
    now, keep, old = time.time(), [], []
    for i in range(0, len(flat), 2):
        (keep if now - int(flat[i + 1]) < hours * 3600 else old).append(flat[i])
    if old:
        store.redis("HDEL", key, *old)
    return keep


# ---------- follow-up offer: a second DM some hours after the freebie ----------

FOLLOWUP_HOURS = (1, 3, 6, 12, 20)
WINDOW = 23 * 3600  # Instagram allows messages until 24 h after the person's last message


def schedule_followup(acc, igsid, key, rule, username=""):
    if not (rule.get("followup_on") and rule.get("followup_dm")):
        return
    if not store.claim(f"s:seen:{acc['id']}:followup:{igsid}:{key}", 30 * 86400):
        return  # one follow-up per person per automation per month
    hours = rule.get("followup_hours") if rule.get("followup_hours") in FOLLOWUP_HOURS else 3
    now = int(time.time())
    store.schedule(now + hours * 3600, {"acc": acc["id"], "igsid": igsid, "key": key, "username": username, "since": now})


def send_due_followups(limit=25):
    """Sends follow-ups whose time has come. Runs after webhooks and from the cron, so no job runner is needed."""
    sent = 0
    for item in store.take_due(limit):
        acc = store.load_account(item["acc"])
        if item.get("kind") == "comment_dm":  # a first DM held back by the automation's delay
            rule = (store.load_rules(item["acc"]).get("reels", {}).get(item["key"]) if acc else None) or {}
            if acc and rule and not acc.get("paused") and not is_blocked(acc) and not over_limit(acc):
                if send_comment_dm(acc, Instagram(acc), item["comment_id"], item["key"], rule, item["media_id"],
                                   item["username"], item["text"]):
                    sent += 1
            continue
        rule = (store.load_rules(item["acc"]).get("reels", {}).get(item["key"]) if acc else None) or {}
        if not acc or acc.get("paused") or is_blocked(acc) or not rule.get("followup_on") or not rule.get("followup_dm"):
            continue
        who = item.get("username") or item["igsid"]
        if time.time() - item.get("since", 0) > WINDOW:
            store.log_activity(acc["id"], item["key"], who, "", "followup", "error", "Skipped: Instagram's 24-hour window had passed.")
            continue
        ig = Instagram(acc)
        username = item.get("username") or (username_of(ig, item["igsid"]) if "{username}" in rule["followup_dm"] else "")
        text = rule["followup_dm"].replace("{username}", username)
        try:
            text = track_text(acc, item["key"], text, rule)
            if rule.get("followup_url"):
                ig.send_buttons({"id": item["igsid"]}, text, links=[(rule.get("followup_button") or "Get it",
                                                                    track(acc, item["key"], rule["followup_url"], rule))])
            else:
                ig.send_dm({"id": item["igsid"]}, {"text": text})
            note_dm(acc)
            store.count(acc["id"], "followups_sent")
            store.log_activity(acc["id"], item["key"], who, "", "followup", "ok")
            sent += 1
        except Exception as e:
            store.log_activity(acc["id"], item["key"], who, "", "followup", "error", str(e))
    return sent


# ---------- email and phone capture: asked in the DM before the link ----------

FIELDS = ("email", "phone")
SKIP_STEPS = {"SKIPMAIL": "email", "SKIPPHONE": "phone"}
ASK = {"email": (DEFAULT_EMAIL_ASK, DEFAULT_EMAIL_RETRY, "SKIPMAIL"), "phone": (DEFAULT_PHONE_ASK, DEFAULT_PHONE_RETRY, "SKIPPHONE")}
PHONE_RE = re.compile(r"\+?\d[\d\s\-().]{7,18}\d")


def parse_email(text):
    found = EMAIL_RE.search(text)
    return found.group(0).lower() if found else ""


def parse_phone(text):
    """A phone number in international form; 10-digit Indian mobiles get +91. "" when there isn't one."""
    found = PHONE_RE.search(text)
    if not found:
        return ""
    raw, digits = found.group(0), re.sub(r"\D", "", found.group(0))
    if len(digits) == 10 and digits[0] in "6789":
        return "+91" + digits
    if len(digits) == 11 and digits[0] == "0" and digits[1] in "6789":
        return "+91" + digits[1:]
    if len(digits) == 12 and digits.startswith("91") and digits[2] in "6789":
        return "+" + digits
    if raw.startswith("+") and 8 <= len(digits) <= 15:
        return "+" + digits
    return ""


PARSE = {"email": parse_email, "phone": parse_phone}


def pending_key(acc, igsid):
    return store.account_key(acc["id"], f"wait_email:{igsid}")


def ask_next(acc, ig, igsid, key, rule, media_id, username, after=None):
    """Asks for the next detail the rule wants and the person hasn't given yet. False when nothing is left to ask."""
    contact = store.get_contact(acc["id"], username, igsid) or {}
    for field in FIELDS[FIELDS.index(after) + 1 if after else 0:]:
        if rule.get(f"ask_{field}") and not contact.get(field):
            ask_field(acc, ig, igsid, key, rule, media_id, username, field)
            return True
    return False


def ask_field(acc, ig, igsid, key, rule, media_id, username, field):
    default, _, skip_step = ASK[field]
    message = {"text": (rule.get(f"{field}_dm") or default).replace("{username}", username)}
    if not rule.get(f"{field}_required"):
        message["quick_replies"] = [{"content_type": "text", "title": SKIP_BUTTON, "payload": f"{skip_step}|{key}|{media_id}"}]
    ig.send_dm({"id": igsid}, message)
    store.redis("SET", pending_key(acc, igsid), json.dumps({"key": key, "media_id": media_id, "username": username,
                                                           "field": field}), "EX", 86400)
    store.log_activity(acc["id"], key, username or igsid, "", f"{field}_ask", "ok")


def handle_email_reply(acc, igsid, text):
    """True when this DM answered our email or phone question (and was handled)."""
    raw = store.redis("GET", pending_key(acc, igsid))
    if not raw:
        return False
    wait = json.loads(raw)
    field = wait.get("field", "email")
    rule = store.load_rules(acc["id"]).get("reels", {}).get(wait["key"])
    if not rule:
        store.redis("DEL", pending_key(acc, igsid))
        return False
    ig = Instagram(acc)
    username = wait.get("username", "")
    value = PARSE[field](text)
    try:
        if not value:
            if dm_keyword_match(store.load_rules(acc["id"]).get("reels", {}), text)[1]:
                return False  # they typed a keyword instead: start that automation
            if store.claim(f"s:seen:{acc['id']}:{field}retry:{igsid}:{int(time.time() // 600)}", 900):
                ig.send_dm({"id": igsid}, {"text": ASK[field][1]})
            return True
        store.redis("DEL", pending_key(acc, igsid))
        store.touch_contact(acc["id"], username, igsid, source=field, **{field: value})
        store.count(acc["id"], f"{field}s")
        send_hook(acc, "lead", {"username": username, field: value, "automation": wait["key"]})
        if (acc.get("notify") or {}).get("lead", True):
            push.notify(acc, "New lead 🎉", f"@{username or 'someone'} shared their {'email' if field == 'email' else 'WhatsApp number'}", "/app/contacts")
        if not ask_next(acc, ig, igsid, wait["key"], rule, wait.get("media_id", ""), username, after=field):
            deliver(acc, ig, igsid, wait["key"], rule, username, wait.get("media_id", ""), f"({field})")
    except Exception as e:
        store.log_activity(acc["id"], wait["key"], username or igsid, text, "dm", "error", str(e))
    return True


# ---------- auto-setup: "Comment GUIDE" in a new reel's caption creates its automation ----------

QUOTES = "\"'“”‘’«»"
# "Comment GUIDE", "comment karo \"gpt\"", "Type LINK below", "likho PROMPTS"
_AFTER = re.compile(r"\b(?:comment|type|likho|write)(?:\s+(?:karo|kare|karein|kijiye|kar\s+do|below|now|here|down|me|the\s+word|word))*"
                    r"[^A-Za-z0-9" + QUOTES + r"]{1,8}([" + QUOTES + r"]?)([A-Za-z0-9]{2,24})", re.I)
# "GPT comment karo", "\"GUIDE\" likho"
_BEFORE = re.compile(r"([" + QUOTES + r"]?)\b([A-Z][A-Z0-9]{1,23})\b[" + QUOTES + r"]?[^A-Za-z0-9]{1,6}(?:comment|likho|type)\b", re.I)
_NOT_KEYWORDS = {"below", "karo", "kare", "here", "now", "down", "and", "aur", "for", "the", "your", "this", "me",
                 "kar", "karna", "comment", "comments", "type", "likho", "box", "section", "if", "to", "in", "on"}


def caption_keyword(caption):
    """The keyword a caption asks people to comment, or "". Only a quoted or ALL-CAPS word counts,
    so "comment below your thoughts" doesn't create anything."""
    caption = caption or ""
    found = []
    for pattern in (_AFTER, _BEFORE):
        for m in pattern.finditer(caption):
            quote, word = m.group(1), m.group(2)
            caught = caption[m.start(2):m.end(2)]
            if word.lower() in _NOT_KEYWORDS:
                continue
            if quote or (caught.isupper() and any(c.isalpha() for c in caught)):
                found.append((m.start(), word.upper()))
    return min(found)[1] if found else ""


def auto_settings(acc):
    return acc.get("auto_setup") or {}


def attach_next(acc, media):
    """A "next post" automation moves onto the first reel posted after it was created."""
    rules = store.load_rules(acc["id"])
    reels = rules.get("reels", {})
    nxt = reels.get("next")
    if not nxt or media["id"] in reels or (media.get("timestamp") or "") < nxt.get("since", ""):
        return False
    rule = reels.pop("next")
    rule["label"] = rule.get("label") or (media.get("caption") or "").strip().split("\n")[0][:120]
    reels[media["id"]] = rule
    store.save_rules(acc["id"], rules)
    for f, n in store.hash_all(store.account_key(acc["id"], "rs:next")).items():
        store.rule_count(acc["id"], media["id"], f, n)
    store.redis("DEL", store.account_key(acc["id"], "rs:next"))
    store.log_activity(acc["id"], media["id"], "", rule["label"], "auto_setup", "ok", "Next-post automation is now on this reel")
    return True


def auto_setup(acc, media):
    """Creates the rule for one new reel from the account's template. Returns the keyword, or ""."""
    if attach_next(acc, media):
        return (store.load_rules(acc["id"])["reels"][media["id"]].get("keywords") or ["any comment"])[0]
    cfg = auto_settings(acc)
    if not cfg.get("enabled") or not (cfg.get("template") or {}).get("dm"):
        return ""
    # Only reels posted after auto-setup was switched on, so old reels are never touched.
    posted = media.get("timestamp", "")
    if posted and posted < cfg.get("since", ""):
        return ""
    rules = store.load_rules(acc["id"])
    if media["id"] in rules.get("reels", {}) or not store.claim(f"s:seen:{acc['id']}:auto:{media['id']}", 90 * 86400):
        return ""
    keyword = caption_keyword(media.get("caption", ""))
    if not keyword:
        return ""
    template = cfg["template"]
    rule = {k: v.replace("{keyword}", keyword) if isinstance(v, str) else v for k, v in template.items()}
    rule.update(enabled=True, keywords=[keyword], auto=True, comments=True,
                label=(media.get("caption") or "").strip().split("\n")[0][:120])
    rules.setdefault("reels", {})[media["id"]] = rule
    store.save_rules(acc["id"], rules)
    store.log_auto(acc["id"], {"media_id": media["id"], "keyword": keyword, "label": rule["label"],
                               "thumb": media.get("thumbnail_url") or media.get("media_url", ""), "at": int(time.time())})
    store.log_activity(acc["id"], media["id"], "", rule["label"], "auto_setup", "ok", f"Keyword {keyword}")
    return keyword


def auto_setup_from_comment(acc, media_id):
    """First comment on a reel without a rule: read its caption once and set it up if it asks for a keyword."""
    reels = store.load_rules(acc["id"]).get("reels", {})
    if not (auto_settings(acc).get("enabled") or "next" in reels) or media_id in reels:
        return ""
    if not store.claim(f"s:seen:{acc['id']}:autolook:{media_id}", 86400):
        return ""  # looked at this reel recently
    try:
        media = Instagram(acc).get(media_id, fields="id,caption,timestamp,thumbnail_url,media_url,media_product_type")
    except Exception:
        return ""
    return auto_setup(acc, media)


# ---------- reel report ----------

REPORT_STEPS = [("views", "Views"), ("comments", "Comments"), ("keyword", "Used the keyword"),
                ("dm", "Got the DM"), ("link", "Link sent"), ("follow", "Followed to unlock")]


def reel_tips(row, avg_per_1k):
    """Plain advice from a reel's numbers (shown as "Reel Doctor")."""
    tips, kw = [], (row.get("keywords") or ["your keyword"])[0]
    views, comments, used, dms, follows = (row.get(k, 0) for k in ("views", "comments", "keyword", "dm", "follow"))
    if not row.get("has_rule"):
        if comments >= 10:
            tips.append(f"{comments} comments and no automation on this reel. Add a keyword so these people get a DM and follow you.")
        return tips or ["No automation on this reel yet."]
    if comments >= 20 and used / comments < 0.4:
        tips.append(f"Only {round(used / comments * 100)}% of comments used {kw}. Say \"Comment {kw}\" in the first 3 seconds "
                    "and pin a comment with it.")
    if used >= 10 and dms / used < 0.8:
        tips.append(f"Instagram refused some DMs on this reel. Add \"or DM me {kw}\" to the caption: "
                    "people who DM you the word still get it.")
    if row.get("require_follow") and dms >= 20 and follows / dms < 0.05:
        tips.append("Few people followed to unlock. Make the first DM say exactly what they get, then ask for the follow.")
    per_1k = row.get("per_1k")
    if per_1k is not None and avg_per_1k and views >= 1000:
        if per_1k >= 1.5 * avg_per_1k:
            tips.append(f"{per_1k} follows per 1K views, well above your average of {avg_per_1k}. Reuse this hook and format.")
        elif per_1k <= 0.5 * avg_per_1k:
            tips.append(f"{per_1k} follows per 1K views, below your average of {avg_per_1k}. Try a stronger reason to comment.")
    return tips or ["Doing fine. Tips appear here when a number stands out."]


def dispatch(body, run):
    """Routes a webhook body to the connected accounts it belongs to. run(fn, *args) executes a task."""
    for entry in body.get("entry", []):
        acc = store.load_account(str(entry.get("id", "")))
        if not acc or acc.get("paused"):
            continue
        for change in entry.get("changes", []):
            if change.get("field") == "comments":
                run(handle_comment, acc, change.get("value", {}))
            elif change.get("field") == "live_comments":
                run(handle_comment, acc, {**change.get("value", {}), "_live": True})
        for event in entry.get("messaging", []):
            msg = event.get("message", {})
            if msg.get("is_echo"):
                continue
            payload = event.get("postback", {}).get("payload") or msg.get("quick_reply", {}).get("payload")
            sender = event.get("sender", {}).get("id")
            note_recent(acc, sender)
            story = (msg.get("reply_to") or {}).get("story")
            if payload:
                run(handle_button, acc, sender, payload)
            elif any(a.get("type") == "story_mention" for a in msg.get("attachments") or []):
                run(handle_story_mention, acc, sender)
            elif story and msg.get("text"):
                run(handle_story_reply, acc, sender, msg["text"], str(story.get("id", "")), msg.get("mid", ""))
            elif msg.get("text"):
                run(handle_dm_text, acc, sender, msg["text"], msg.get("mid", ""))
