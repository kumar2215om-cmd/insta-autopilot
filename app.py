"""Insta Autopilot: auto comment-reply + DM on your reels, with a live stats dashboard.

Uses the official Instagram API (Instagram Login). Requires a Business or Creator account.
"""
import hashlib
import hmac
import json
import os
import random
import sqlite3
import threading
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, render_template, request

load_dotenv()

API_VERSION = os.environ.get("IG_API_VERSION", "v23.0")
GRAPH = f"https://graph.instagram.com/{API_VERSION}"


def secret(name, default=""):
    # Values pasted into hosting dashboards often pick up stray spaces, newlines or quotes.
    return os.environ.get(name, default).strip().strip("\"'").strip()


ACCESS_TOKEN = secret("IG_ACCESS_TOKEN")
APP_SECRET = secret("IG_APP_SECRET")
VERIFY_TOKEN = secret("IG_VERIFY_TOKEN", "change-me")
CRON_SECRET = secret("CRON_SECRET")
DASHBOARD_PASSWORD = secret("DASHBOARD_PASSWORD")
# Serverless functions freeze after responding, so webhook work can't run in background threads.
SERVERLESS = bool(os.environ.get("VERCEL"))
# On a server, point DATA_DIR at a persistent volume so rules and activity survive redeploys.
# Vercel only allows writing to /tmp (wiped often), which is why Redis is needed there.
DATA_DIR = os.environ.get("DATA_DIR", "/tmp" if SERVERLESS else ".")
os.makedirs(DATA_DIR, exist_ok=True)
RULES_FILE = os.environ.get("RULES_FILE", os.path.join(DATA_DIR, "rules.json"))
DB_FILE = os.environ.get("DB_FILE", os.path.join(DATA_DIR, "autopilot.db"))
STATS_CACHE_SECONDS = int(os.environ.get("STATS_CACHE_SECONDS", "60"))
# Serverless hosts (Vercel) have no lasting disk: store data in Upstash Redis when it's configured.
REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")

REEL_METRICS = "views,reach,likes,comments,shares,saved,total_interactions"

app = Flask(__name__)
_db_lock = threading.Lock()
_stats_cache = {"at": 0, "data": None}


# ---------- storage ----------

def redis(*command):
    r = requests.post(REDIS_URL, headers={"Authorization": f"Bearer {REDIS_TOKEN}"},
                      json=list(command), timeout=10)
    r.raise_for_status()
    return r.json()["result"]


def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _db_lock, db() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS processed (comment_id TEXT PRIMARY KEY)")
        conn.execute("CREATE TABLE IF NOT EXISTS retry (comment_id TEXT PRIMARY KEY, data TEXT)")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, media_id TEXT,
                username TEXT, comment TEXT, action TEXT, status TEXT, detail TEXT)"""
        )


def log_activity(media_id, username, comment, action, status, detail=""):
    at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if REDIS_URL:
        redis("LPUSH", "activity", json.dumps({
            "at": at, "media_id": media_id, "username": username, "comment": comment,
            "action": action, "status": status, "detail": detail[:500]}))
        redis("LTRIM", "activity", 0, 99)
        return
    with _db_lock, db() as conn:
        conn.execute(
            "INSERT INTO activity (at, media_id, username, comment, action, status, detail) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (at, media_id, username, comment, action, status, detail[:500]),
        )


def claim_comment(comment_id):
    """Returns True the first time a comment is seen, so each comment is handled once."""
    if REDIS_URL:
        # Instagram only allows private replies within 7 days, so 30 days of memory is plenty.
        return redis("SET", f"processed:{comment_id}", 1, "NX", "EX", 30 * 86400) == "OK"
    with _db_lock, db() as conn:
        cur = conn.execute("INSERT OR IGNORE INTO processed VALUES (?)", (comment_id,))
        return cur.rowcount == 1


def add_retry(comment_id, item):
    if REDIS_URL:
        redis("HSET", "dm_retry", comment_id, json.dumps(item))
        return
    with _db_lock, db() as conn:
        conn.execute("INSERT OR REPLACE INTO retry VALUES (?, ?)", (comment_id, json.dumps(item)))


def remove_retry(comment_id):
    if REDIS_URL:
        redis("HDEL", "dm_retry", comment_id)
        return
    with _db_lock, db() as conn:
        conn.execute("DELETE FROM retry WHERE comment_id = ?", (comment_id,))


def pending_retries():
    if REDIS_URL:
        flat = redis("HGETALL", "dm_retry") or []
        return {flat[i]: json.loads(flat[i + 1]) for i in range(0, len(flat), 2)}
    with db() as conn:
        return {r["comment_id"]: json.loads(r["data"]) for r in conn.execute("SELECT * FROM retry")}


def recent_activity():
    if REDIS_URL:
        return [json.loads(x) for x in redis("LRANGE", "activity", 0, 99)]
    with db() as conn:
        rows = conn.execute("SELECT * FROM activity ORDER BY id DESC LIMIT 100").fetchall()
    return [dict(r) for r in rows]


def load_rules():
    if REDIS_URL:
        raw = redis("GET", "rules")
        return json.loads(raw) if raw else {"reels": {}}
    try:
        with open(RULES_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"reels": {}}


def save_rules(rules):
    if REDIS_URL:
        redis("SET", "rules", json.dumps(rules, ensure_ascii=False))
        return
    tmp = RULES_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)
    os.replace(tmp, RULES_FILE)


# ---------- Instagram API ----------

def _env_token_id():
    return hashlib.sha256(ACCESS_TOKEN.encode()).hexdigest()[:16]


def current_token():
    """The latest auto-refreshed token, unless IG_ACCESS_TOKEN was changed since it was saved."""
    if REDIS_URL:
        saved = redis("GET", "ig_token")
        if saved:
            saved = json.loads(saved)
            if saved.get("env") == _env_token_id():
                return saved["token"]
    return ACCESS_TOKEN


def refresh_token():
    # Long-lived tokens last 60 days; refreshing returns a new 60-day token.
    r = requests.get("https://graph.instagram.com/refresh_access_token", timeout=20, params={
        "grant_type": "ig_refresh_token", "access_token": current_token()})
    r.raise_for_status()
    data = r.json()
    redis("SET", "ig_token", json.dumps({"token": data["access_token"], "env": _env_token_id()}))
    return data.get("expires_in")


def ig_get(path, **params):
    params["access_token"] = current_token()
    r = requests.get(f"{GRAPH}/{path}", params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def ig_post(path, payload):
    r = requests.post(f"{GRAPH}/{path}", params={"access_token": current_token()},
                      json=payload, timeout=20)
    if not r.ok:
        raise RuntimeError(f"{r.status_code}: {r.text}")
    return r.json()


def reply_to_comment(comment_id, text):
    return ig_post(f"{comment_id}/replies", {"message": text})


def send_dm(ig_user_id, recipient, message):
    """recipient is {"comment_id": ...} for a private reply, or {"id": igsid} inside a chat."""
    return ig_post(f"{ig_user_id}/messages", {"recipient": recipient, "message": message})


# Instagram's "thread owner has archived or deleted this conversation" error. It isn't documented;
# developers report it when Instagram temporarily refuses new DM threads (often after many sends).
CANT_OPEN_THREAD = "2534001"


def explain_error(err):
    err = str(err)
    if CANT_OPEN_THREAD in err:
        return ("Instagram refused to open a DM with this person right now (error 2534001). "
                "It will be retried automatically. | " + err)
    return err


def send_buttons(ig_user_id, recipient, text, postbacks=(), links=()):
    """Sends text with buttons. postbacks: [(title, payload)], links: [(title, url)].

    Tries a button template first; falls back to quick replies if Instagram rejects it.
    """
    buttons = ([{"type": "web_url", "title": t[:20], "url": u} for t, u in links]
               + [{"type": "postback", "title": t[:20], "payload": p} for t, p in postbacks])
    try:
        return send_dm(ig_user_id, recipient, {"attachment": {"type": "template", "payload": {
            "template_type": "button", "text": text[:640], "buttons": buttons[:3]}}})
    except RuntimeError as first:
        if CANT_OPEN_THREAD in str(first):
            raise  # retrying with another message style can't help, and hides the real error
        text += "".join(f"\n{t}: {u}" for t, u in links)
        try:
            return send_dm(ig_user_id, recipient, {"text": text, "quick_replies": [
                {"content_type": "text", "title": t[:20], "payload": p} for t, p in postbacks]})
        except RuntimeError as second:
            raise RuntimeError(f"button DM: {first} | plain DM: {second}") from second


def get_follow_status(igsid):
    """Only works after the user has interacted with our DM (e.g. tapped a button)."""
    data = ig_get(igsid, fields="username,is_user_follow_business")
    return data.get("username", ""), bool(data.get("is_user_follow_business"))


_my_username = {}


def my_username():
    if "u" not in _my_username:
        _my_username["u"] = ig_get("me", fields="username")["username"]
    return _my_username["u"]


def fetch_stats():
    me = ig_get("me", fields="user_id,username,followers_count,follows_count,media_count")
    media = ig_get("me/media", limit=50, fields=(
        "id,caption,media_type,media_product_type,permalink,thumbnail_url,"
        "media_url,timestamp,like_count,comments_count"))["data"]
    reels = []
    for m in media:
        if m.get("media_product_type") != "REELS":
            continue
        try:
            ins = ig_get(f"{m['id']}/insights", metric=REEL_METRICS)["data"]
            m["insights"] = {i["name"]: i["values"][0]["value"] for i in ins}
        except requests.HTTPError as e:
            m["insights"] = {}
            m["insights_error"] = str(e)
        reels.append(m)
    return {"account": me, "reels": reels,
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


# ---------- rule engine ----------

DEFAULT_OPENING = "Hey {username}! 👋 Tap the button below and I'll send it to you."
DEFAULT_FOLLOW = ("Almost there! 👀 Follow me first to unlock it, "
                  "then tap \"I followed\" below.")


def normalize_words(text):
    """Lowercase words with emoji/punctuation, repeated letters and a plural "s" removed.

    "PROMPTS!!🔥" -> ["prompt"], "Ootto" -> ["oto"], so variations of a keyword still match.
    """
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
    kw = normalize_words(keyword)
    words = normalize_words(text)
    if not kw:
        return False
    if len(kw) > 1:  # a phrase must appear as consecutive words
        return f" {' '.join(kw)} " in f" {' '.join(words)} "
    # Whole words only (so "ai" doesn't fire on "said"). Longer keywords tolerate one typo after
    # the first letter ("promt" -> prompt, but not "emerge" -> merge).
    k = kw[0]
    return any(w == k or (len(k) >= 5 and w[0] == k[0] and one_typo_apart(w, k)) for w in words)


def find_rule(rules, media_id, text):
    """Returns (rule_key, rule) for a comment, or (None, None)."""
    reels = rules.get("reels", {})
    key = media_id if media_id in reels else "*"
    rule = reels.get(key)
    if not rule or not rule.get("enabled", True):
        return None, None
    keywords = [k for k in rule.get("keywords", []) if k.strip()]
    if keywords and not any(keyword_matches(k, text) for k in keywords):
        return None, None
    return key, rule


def uses_button_flow(rule):
    return rule.get("require_follow") or rule.get("opening_dm")


def pick_reply(replies):
    """One line at random, so replies vary (identical repeats can look like spam to Instagram).

    Starts with an @mention like a normal Instagram reply, unless the line already uses {username}.
    """
    line = random.choice([l.strip() for l in replies.splitlines() if l.strip()])
    return line if "{username}" in line else "@{username} " + line


def handle_comment(ig_user_id, value):
    comment_id = value.get("id")
    text = value.get("text", "")
    sender = value.get("from", {})
    username = sender.get("username", "")
    media_id = value.get("media", {}).get("id", "")

    # Skip our own comments/replies and replies inside threads.
    if not comment_id or sender.get("id") == ig_user_id or value.get("parent_id"):
        return False
    key, rule = find_rule(load_rules(), media_id, text)
    if not rule or not claim_comment(comment_id):
        return False

    # DM first, so the public reply can tell people what to do if Instagram refuses the DM.
    item = {"ig_user_id": ig_user_id, "key": key, "media_id": media_id, "username": username,
            "text": text, "at": time.time()}
    dm_ok = send_comment_dm(comment_id, item, rule)
    if not dm_ok:
        add_retry(comment_id, item)

    reply = rule.get("comment_reply") if dm_ok else (rule.get("dm_fail_reply") or DEFAULT_DM_FAIL_REPLY)
    if reply:
        reply = pick_reply(reply).replace("{keyword}", dm_keywords(rule)[0].upper())
        try:
            reply_to_comment(comment_id, reply.replace("{username}", username))
            log_activity(media_id, username, text, "comment_reply" if dm_ok else "dm_fail_reply", "ok")
        except Exception as e:
            log_activity(media_id, username, text, "comment_reply", "error", str(e))
    return True


DEFAULT_DM_FAIL_REPLY = "@{username} your DM didn't come through 😅 DM me {keyword} and I'll send it instantly 📩"


def dm_keywords(rule):
    """Words that trigger this rule when someone DMs them; rules without keywords answer to LINK."""
    return [k.strip() for k in rule.get("keywords", []) if k.strip()] or ["LINK"]


def handle_dm_text(ig_user_id, igsid, text):
    """Someone DMed a keyword (e.g. because the comment DM was refused): start the same flow.

    Replying inside a conversation the person started works even when Instagram refuses to open
    new conversations from comments.
    """
    for key, rule in load_rules().get("reels", {}).items():
        if rule.get("enabled", True) and any(keyword_matches(k, text) for k in dm_keywords(rule)):
            break
    else:
        return
    # Answer the same keyword from the same person at most once per 10 minutes.
    if not claim_comment(f"dm:{igsid}:{key}:{int(time.time() // 600)}"):
        return
    try:
        username = ig_get(igsid, fields="username").get("username", "")
    except Exception:
        username = ""
    fill = lambda s: s.replace("{username}", username)
    try:
        if uses_button_flow(rule):
            send_buttons(ig_user_id, {"id": igsid}, fill(rule.get("opening_dm") or DEFAULT_OPENING),
                         postbacks=[(rule.get("button_text") or "Send me the link", f"GET|{key}")])
        else:
            send_dm(ig_user_id, {"id": igsid}, {"text": fill(rule["dm"])})
        log_activity(key, username or igsid, text, "dm_keyword", "ok")
        # They're being served now, so don't also send them the refused comment DM later.
        for comment_id, item in pending_retries().items():
            if username and item.get("username") == username:
                remove_retry(comment_id)
    except Exception as e:
        log_activity(key, username or igsid, text, "dm_keyword", "error", explain_error(e))


def send_comment_dm(comment_id, item, rule, retry=False):
    """Sends the first DM for a comment (a private reply). Returns True on success."""
    fill = lambda s: s.replace("{username}", item["username"])
    action = "opening_dm" if uses_button_flow(rule) else "dm"
    note = "sent on retry" if retry else ""
    recipient = {"comment_id": comment_id}
    try:
        if uses_button_flow(rule):
            # Step 1: opening DM with a button. The tap opens the conversation, which
            # Instagram requires before we can look up whether the user follows us.
            send_buttons(item["ig_user_id"], recipient, fill(rule.get("opening_dm") or DEFAULT_OPENING),
                         postbacks=[(rule.get("button_text") or "Send me the link", f"GET|{item['key']}")])
        elif rule.get("dm"):
            send_dm(item["ig_user_id"], recipient, {"text": fill(rule["dm"])})
        log_activity(item["media_id"], item["username"], item["text"], action, "ok", note)
        return True
    except Exception as e:
        log_activity(item["media_id"], item["username"], item["text"], action, "error", explain_error(e))
        return False


def retry_failed_dms(max_sends=30):
    """Retries DMs that Instagram refused earlier, while the 7-day private-reply window is open."""
    rules = load_rules().get("reels", {})
    counts = {"sent": 0, "still_failing": 0, "expired": 0}
    for comment_id, item in list(pending_retries().items()):
        rule = rules.get(item["key"])
        # Leave a day of margin: the window counts from the comment, which came slightly earlier.
        if not rule or time.time() - item["at"] > PRIVATE_REPLY_WINDOW - 86400:
            remove_retry(comment_id)
            counts["expired"] += 1
        elif counts["sent"] + counts["still_failing"] >= max_sends:
            break
        elif send_comment_dm(comment_id, item, rule, retry=True):
            remove_retry(comment_id)
            counts["sent"] += 1
        else:
            counts["still_failing"] += 1
    return counts


PRIVATE_REPLY_WINDOW = 7 * 86400  # Instagram allows a DM reply to a comment only within 7 days.


def backfill_comments(media_id, max_sends=50):
    """Runs a reel's rule on comments posted before the automation was set up."""
    ig_user_id = ig_get("me", fields="user_id")["user_id"]
    rules = load_rules()
    counts = {"sent": 0, "dm_retried": 0, "too_old": 0, "already_done_or_no_match": 0, "more_left": False}
    # People whose first DM failed on this reel (per the activity log) and never got one since.
    # Their comments are already marked handled, so they get the DM again without a new public reply.
    log = [a for a in recent_activity() if a.get("media_id") == media_id and a["action"] in ("opening_dm", "dm")]
    got_dm = {a["username"] for a in log if a["status"] == "ok"}
    dm_failed = {a["username"] for a in log if a["status"] == "error"} - got_dm
    page = ig_get(f"{media_id}/comments", fields="id,text,timestamp,from,username", limit=50)
    while page:
        for c in page.get("data", []):
            if counts["sent"] >= max_sends:
                counts["more_left"] = True
                return counts
            text = c.get("text", "")
            if not find_rule(rules, media_id, text)[1]:
                counts["already_done_or_no_match"] += 1
                continue
            age = time.time() - datetime.strptime(c["timestamp"], "%Y-%m-%dT%H:%M:%S%z").timestamp()
            if age > PRIVATE_REPLY_WINDOW:
                counts["too_old"] += 1
                continue
            sender = c.get("from") or {"username": c.get("username", "")}
            value = {"id": c["id"], "text": text, "from": sender, "media": {"id": media_id}}
            if handle_comment(ig_user_id, value):
                counts["sent"] += 1
            elif sender.get("username") in dm_failed:
                dm_failed.discard(sender["username"])
                key, rule = find_rule(rules, media_id, text)
                item = {"ig_user_id": ig_user_id, "key": key, "media_id": media_id,
                        "username": sender["username"], "text": text, "at": time.time()}
                if send_comment_dm(c["id"], item, rule, retry=True):
                    counts["dm_retried"] += 1
                else:
                    add_retry(c["id"], item)
                    counts["already_done_or_no_match"] += 1
            else:
                counts["already_done_or_no_match"] += 1
        next_url = page.get("paging", {}).get("next")
        page = requests.get(next_url, timeout=20).json() if next_url else None
    return counts


def handle_button(ig_user_id, igsid, payload):
    """User tapped "Send me the link" or "I followed": check follow, then deliver or ask."""
    step, _, key = payload.partition("|")
    rule = load_rules().get("reels", {}).get(key)
    if step not in ("GET", "FOLLOWED") or not rule:
        return
    recipient = {"id": igsid}
    username, follows = "", True
    if rule.get("require_follow"):
        try:
            username, follows = get_follow_status(igsid)
        except Exception as e:
            # Strict gate: no confirmed follow, no link. They get the follow prompt and can tap
            # "I followed" to be checked again.
            follows = False
            log_activity(key, igsid, payload, "follow_check", "error",
                         "Couldn't confirm they follow you, so the link was held back. | " + str(e))
    fill = lambda s: s.replace("{username}", username)
    try:
        if follows:
            if not rule.get("dm"):
                raise RuntimeError("Final DM is empty: add your message and link to this rule in the dashboard")
            send_dm(ig_user_id, recipient, {"text": fill(rule["dm"])})
            log_activity(key, username or igsid, payload, "dm", "ok")
        else:
            me = my_username()
            send_buttons(ig_user_id, recipient, fill(rule.get("follow_dm") or DEFAULT_FOLLOW),
                         links=[("Open profile", f"https://www.instagram.com/{me}/")],
                         postbacks=[(rule.get("followed_button_text") or "I followed ✅",
                                     f"FOLLOWED|{key}")])
            log_activity(key, username or igsid, payload, "follow_prompt", "ok")
    except Exception as e:
        log_activity(key, username or igsid, payload, "dm", "error", str(e))


# ---------- webhook ----------

@app.get("/webhook")
def verify_webhook():
    if (request.args.get("hub.mode") == "subscribe"
            and request.args.get("hub.verify_token") == VERIFY_TOKEN):
        return request.args.get("hub.challenge", "")
    abort(403)


def run_task(fn, *args):
    # Respond to Instagram fast by doing API calls in the background, except on serverless
    # hosts where the function would be frozen before the thread finishes.
    if SERVERLESS:
        fn(*args)
    else:
        threading.Thread(target=fn, args=args).start()


@app.post("/webhook")
def receive_webhook():
    if APP_SECRET:
        expected = "sha256=" + hmac.new(APP_SECRET.encode(), request.get_data(),
                                        hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, request.headers.get("X-Hub-Signature-256", "")):
            abort(403)
    body = request.get_json(silent=True) or {}
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") == "comments":
                run_task(handle_comment, entry.get("id"), change.get("value", {}))
        for event in entry.get("messaging", []):
            msg = event.get("message", {})
            payload = (event.get("postback", {}).get("payload")
                       or msg.get("quick_reply", {}).get("payload"))
            if msg.get("is_echo"):
                continue  # our own outgoing messages
            if payload:
                run_task(handle_button, entry.get("id"), event["sender"]["id"], payload)
            elif msg.get("text"):
                run_task(handle_dm_text, entry.get("id"), event["sender"]["id"], msg["text"])
    return "ok"


# ---------- dashboard ----------

@app.before_request
def check_password():
    if not DASHBOARD_PASSWORD or request.path.startswith(("/webhook", "/cron/")):
        return
    auth = request.authorization
    if not auth or (auth.password or "").strip() != DASHBOARD_PASSWORD:
        return ("Login required", 401, {"WWW-Authenticate": 'Basic realm="autopilot"'})


@app.post("/api/retry-failed")
def api_retry_failed():
    return jsonify(retry_failed_dms())


@app.get("/api/retry-failed")
def api_retry_count():
    return jsonify({"pending": len(pending_retries())})


@app.get("/cron/retry-failed")
def cron_retry_failed():
    if not CRON_SECRET or request.headers.get("Authorization") != f"Bearer {CRON_SECRET}":
        abort(403)
    return jsonify(retry_failed_dms())


@app.get("/cron/refresh-token")
def cron_refresh_token():
    # Vercel Cron sends "Authorization: Bearer <CRON_SECRET>".
    if not CRON_SECRET or request.headers.get("Authorization") != f"Bearer {CRON_SECRET}":
        abort(403)
    if not REDIS_URL:
        return jsonify({"error": "token refresh needs Redis storage"}), 400
    try:
        expires_in = refresh_token()
        log_activity("", "system", "", "token_refresh", "ok")
        return jsonify({"expires_in_days": round((expires_in or 0) / 86400)})
    except Exception as e:
        log_activity("", "system", "", "token_refresh", "error", str(e))
        return jsonify({"error": str(e)}), 502


@app.get("/")
def dashboard():
    return render_template("dashboard.html")


@app.get("/api/stats")
def api_stats():
    if request.args.get("refresh") or time.time() - _stats_cache["at"] > STATS_CACHE_SECONDS:
        try:
            _stats_cache["data"] = fetch_stats()
            _stats_cache["at"] = time.time()
        except Exception as e:
            if not _stats_cache["data"]:
                return jsonify({"error": str(e)}), 502
    data = dict(_stats_cache["data"])
    if SERVERLESS and not REDIS_URL:
        data["warning"] = ("No database connected: rules and activity will be lost. "
                           "In Vercel, add Storage → Upstash Redis and redeploy.")
    return jsonify(data)


@app.get("/api/activity")
def api_activity():
    return jsonify(recent_activity())


@app.get("/api/rules")
def api_get_rules():
    return jsonify(load_rules())


@app.put("/api/rules/<media_id>")
def api_put_rule(media_id):
    data = request.get_json(force=True)
    rules = load_rules()
    rules.setdefault("reels", {})[media_id] = {
        "enabled": bool(data.get("enabled", True)),
        "keywords": [k.strip() for k in data.get("keywords", []) if k.strip()],
        "comment_reply": data.get("comment_reply", "").strip(),
        "opening_dm": data.get("opening_dm", "").strip(),
        "button_text": data.get("button_text", "").strip()[:20],
        "require_follow": bool(data.get("require_follow")),
        "follow_dm": data.get("follow_dm", "").strip(),
        "dm_fail_reply": data.get("dm_fail_reply", "").strip(),
        "followed_button_text": data.get("followed_button_text", "").strip()[:20],
        "dm": data.get("dm", "").strip(),
    }
    save_rules(rules)
    return jsonify(rules["reels"][media_id])


@app.post("/api/backfill/<media_id>")
def api_backfill(media_id):
    try:
        return jsonify(backfill_comments(media_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.delete("/api/rules/<media_id>")
def api_delete_rule(media_id):
    rules = load_rules()
    rules.get("reels", {}).pop(media_id, None)
    save_rules(rules)
    return "", 204


if not REDIS_URL:
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
