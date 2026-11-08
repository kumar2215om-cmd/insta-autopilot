"""Comment → DM → follow check → link, for any connected account.

Same flow and matching as the single-account app (../app.py), with every call tied to one account.
"""
import os
import random
import time
from datetime import datetime, timezone

import requests

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


# ---------- Instagram API for one account ----------

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
        params["access_token"] = self.acc["token"]
        return self._check(requests.get(f"{GRAPH}/{path}", params=params, timeout=20))

    def post(self, path, payload=None, **params):
        params["access_token"] = self.acc["token"]
        return self._check(requests.post(f"{GRAPH}/{path}", params=params, json=payload, timeout=20))

    def reply_to_comment(self, comment_id, text):
        return self.post(f"{comment_id}/replies", {"message": text})

    def send_dm(self, recipient, message):
        """recipient is {"comment_id": ...} for a private reply, or {"id": igsid} inside a chat."""
        return self.post(f"{self.acc['id']}/messages", {"recipient": recipient, "message": message})

    def send_buttons(self, recipient, text, postbacks=(), links=()):
        """Text with buttons (button template); falls back to quick replies if Instagram rejects it."""
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


def monthly_limit(acc):
    return int(acc.get("dm_limit", FREE_MONTHLY_DMS))


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


def keywords_of(rule):
    return [k.strip() for k in rule.get("keywords", []) if k.strip()]


def find_rule(rules, media_id, text):
    """(key, rule) for a comment: the reel's own rule, then keyword rules, then the all-reels rule "*"."""
    reels = rules.get("reels", {})
    own = reels.get(media_id) if media_id and media_id != "*" and not is_keyword_rule(media_id) else None
    if own and own.get("enabled", True):
        words = keywords_of(own)
        if not words or any(keyword_matches(k, text) for k in words):
            return media_id, own
    for key, rule in reels.items():
        if (is_keyword_rule(key) and rule.get("enabled", True) and rule.get("comments", True)
                and any(keyword_matches(k, text) for k in keywords_of(rule))):
            return key, rule
    if own:  # a reel with its own rule never falls through to the all-reels rule
        return None, None
    rule = reels.get("*")
    if not rule or not rule.get("enabled", True):
        return None, None
    words = keywords_of(rule)
    if words and not any(keyword_matches(k, text) for k in words):
        return None, None
    return "*", rule


def uses_button_flow(rule):
    return rule.get("require_follow") or rule.get("opening_dm")


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
    if not comment_id or sender.get("id") == acc["id"] or value.get("parent_id"):
        return False  # own comments and replies inside threads
    key, rule = find_rule(store.load_rules(acc["id"]), media_id, text)
    if not rule or is_blocked(acc) or not store.claim(f"s:seen:{acc['id']}:{comment_id}"):
        return False
    ig = Instagram(acc)
    fill = lambda s: s.replace("{username}", username)

    if over_limit(acc):
        store.log_activity(acc["id"], media_id, username, text, "dm", "error",
                           f"Monthly DM limit reached ({monthly_limit(acc)}). Upgrade to keep sending.")
    else:
        action = "opening_dm" if uses_button_flow(rule) else "dm"
        try:
            if uses_button_flow(rule):
                ig.send_buttons({"comment_id": comment_id}, fill(rule.get("opening_dm") or DEFAULT_OPENING),
                                postbacks=[(rule.get("button_text") or DEFAULT_BUTTON, f"GET|{key}")])
            elif rule.get("dm"):
                ig.send_dm({"comment_id": comment_id}, {"text": fill(rule["dm"])})
                store.count(acc["id"], "links_sent")
            note_dm(acc)
            store.log_activity(acc["id"], media_id, username, text, action, "ok")
        except Exception as e:
            store.log_activity(acc["id"], media_id, username, text, action, "error", str(e))

    reply = rule.get("comment_reply", DEFAULT_COMMENT_REPLY)
    if reply.strip():
        try:
            ig.reply_to_comment(comment_id, fill(pick_reply(reply)))
            store.count(acc["id"], "comment_replies")
            store.log_activity(acc["id"], media_id, username, text, "comment_reply", "ok")
        except Exception as e:
            store.log_activity(acc["id"], media_id, username, text, "comment_reply", "error", str(e))
    return True


def handle_dm_text(acc, igsid, text):
    """Someone DMed a keyword: start the same flow inside that chat (works even when comment DMs are refused)."""
    if is_blocked(acc):
        return
    rules = store.load_rules(acc["id"]).get("reels", {})
    ordered = sorted(rules.items(), key=lambda kv: not is_keyword_rule(kv[0]))
    match = next(((k, r) for k, r in ordered if r.get("enabled", True)
                  and any(keyword_matches(w, text) for w in keywords_of(r))), None)
    if not match or not store.claim(f"s:seen:{acc['id']}:dm:{igsid}:{match[0]}:{int(time.time() // 600)}"):
        return
    key, rule = match
    ig = Instagram(acc)
    try:
        username = ig.get(igsid, fields="username").get("username", "")
    except Exception:
        username = ""
    if over_limit(acc):
        store.log_activity(acc["id"], key, username or igsid, text, "dm_keyword", "error", "Monthly DM limit reached.")
        return
    fill = lambda s: s.replace("{username}", username)
    try:
        if uses_button_flow(rule):
            ig.send_buttons({"id": igsid}, fill(rule.get("opening_dm") or DEFAULT_OPENING),
                            postbacks=[(rule.get("button_text") or DEFAULT_BUTTON, f"GET|{key}")])
        else:
            ig.send_dm({"id": igsid}, {"text": fill(rule.get("dm", ""))})
            store.count(acc["id"], "links_sent")
        note_dm(acc)
        store.log_activity(acc["id"], key, username or igsid, text, "dm_keyword", "ok")
    except Exception as e:
        store.log_activity(acc["id"], key, username or igsid, text, "dm_keyword", "error", str(e))


def handle_button(acc, igsid, payload):
    """They tapped "Send me the link" or "I followed": check the follow, then send the link or ask again."""
    step, _, key = payload.partition("|")
    rule = store.load_rules(acc["id"]).get("reels", {}).get(key)
    if step not in ("GET", "FOLLOWED") or not rule or is_blocked(acc):
        return
    ig = Instagram(acc)
    username, follows = "", True
    if rule.get("require_follow"):
        try:
            username, follows = ig.follow_status(igsid)
        except Exception as e:
            follows = False  # strict gate: no confirmed follow, no link
            store.log_activity(acc["id"], key, igsid, payload, "follow_check", "error", str(e))
    fill = lambda s: s.replace("{username}", username)
    try:
        if follows:
            if not rule.get("dm"):
                raise RuntimeError("The final DM is empty: add your message and link to this rule")
            ig.send_dm({"id": igsid}, {"text": fill(rule["dm"])})
            store.count(acc["id"], "links_sent")
            store.log_activity(acc["id"], key, username or igsid, payload, "dm", "ok")
            if step == "FOLLOWED" and rule.get("require_follow") and store.claim(f"s:seen:{acc['id']}:gate:{igsid}"):
                store.count(acc["id"], "gate_follows")
        else:
            ig.send_buttons({"id": igsid}, fill(rule.get("follow_dm") or DEFAULT_FOLLOW),
                            links=[("Open profile", f"https://www.instagram.com/{acc['username']}/")],
                            postbacks=[(rule.get("followed_button_text") or DEFAULT_FOLLOWED_BUTTON,
                                        f"FOLLOWED|{key}")])
            store.log_activity(acc["id"], key, username or igsid, payload, "follow_prompt", "ok")
    except Exception as e:
        store.log_activity(acc["id"], key, username or igsid, payload, "dm", "error", str(e))


def dispatch(body, run):
    """Routes a webhook body to the connected accounts it belongs to. run(fn, *args) executes a task."""
    for entry in body.get("entry", []):
        acc = store.load_account(str(entry.get("id", "")))
        if not acc or acc.get("paused"):
            continue
        for change in entry.get("changes", []):
            if change.get("field") == "comments":
                run(handle_comment, acc, change.get("value", {}))
        for event in entry.get("messaging", []):
            msg = event.get("message", {})
            if msg.get("is_echo"):
                continue
            payload = event.get("postback", {}).get("payload") or msg.get("quick_reply", {}).get("payload")
            sender = event.get("sender", {}).get("id")
            if payload:
                run(handle_button, acc, sender, payload)
            elif msg.get("text"):
                run(handle_dm_text, acc, sender, msg["text"])
