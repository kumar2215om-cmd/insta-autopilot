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
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, redirect, render_template, request

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
LINKPAGE_FILE = os.environ.get("LINKPAGE_FILE", os.path.join(DATA_DIR, "linkpage.json"))
DB_FILE = os.environ.get("DB_FILE", os.path.join(DATA_DIR, "autopilot.db"))
# Stats cost one Instagram request per reel, so refresh them rarely (they share the app's hourly limit).
STATS_CACHE_SECONDS = int(os.environ.get("STATS_CACHE_SECONDS", "600"))
STATS_REELS = int(os.environ.get("STATS_REELS", "12"))
# Serverless hosts (Vercel) have no lasting disk: store data in Upstash Redis when it's configured.
REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")

REEL_METRICS = "views,reach,likes,comments,shares,saved,total_interactions"

app = Flask(__name__)
_db_lock = threading.RLock()  # re-entrant: counter_add holds it while calling kv_set
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
        conn.execute("CREATE TABLE IF NOT EXISTS clicks (item_id TEXT PRIMARY KEY, n INTEGER)")
        conn.execute("CREATE TABLE IF NOT EXISTS retry (comment_id TEXT PRIMARY KEY, data TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)")
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


def kv_get(k):
    if REDIS_URL:
        return redis("GET", f"kv:{k}")
    with db() as conn:
        row = conn.execute("SELECT v FROM kv WHERE k = ?", (k,)).fetchone()
        return row["v"] if row else None


def kv_set(k, v):
    if REDIS_URL:
        redis("SET", f"kv:{k}", v)
        return
    with _db_lock, db() as conn:
        conn.execute("INSERT OR REPLACE INTO kv VALUES (?, ?)", (k, str(v)))


def counter_add(name, field, n=1):
    if REDIS_URL:
        redis("HINCRBY", f"cnt:{name}", field, n)
        return
    with _db_lock:
        data = json.loads(kv_get(f"cnt:{name}") or "{}")
        data[field] = data.get(field, 0) + n
        kv_set(f"cnt:{name}", json.dumps(data))


def counter_all(name):
    if REDIS_URL:
        flat = redis("HGETALL", f"cnt:{name}") or []
        return {flat[i]: int(flat[i + 1]) for i in range(0, len(flat), 2)}
    return json.loads(kv_get(f"cnt:{name}") or "{}")


# ---------- follower growth ----------

IST = timezone(timedelta(hours=5, minutes=30))  # days are counted in Indian time


def today_ist(offset_days=0):
    return (datetime.now(IST) + timedelta(days=offset_days)).strftime("%Y-%m-%d")


def record_growth(stats):
    """Keeps one follower/views snapshot per day (first and latest), for the last 30 days."""
    followers = stats.get("account", {}).get("followers_count")
    if followers is None:
        return
    views = {r["id"]: r.get("insights", {}).get("views", 0) or 0 for r in stats.get("reels", [])}
    growth = json.loads(kv_get("growth") or "{}")
    day = growth.setdefault(today_ist(), {"f0": followers, "v0": views})
    day["f"], day["v"] = followers, views
    for old in sorted(growth)[:-30]:
        del growth[old]
    kv_set("growth", json.dumps(growth))


def growth_summary(days=7):
    """Followers and reel views gained per day, newest first, plus follows won by the follow gate."""
    growth = json.loads(kv_get("growth") or "{}")
    gate = counter_all("gate_follows_day")
    out = []
    for i in range(days):
        date = today_ist(-i)
        day = growth.get(date)
        if not day:
            continue
        prev = growth.get(today_ist(-i - 1))
        base_f = prev["f"] if prev else day["f0"]
        base_v = prev["v"] if prev else day["v0"]
        views = sum(max(v - base_v.get(rid, 0), 0) for rid, v in day["v"].items())
        gained = day["f"] - base_f
        out.append({"date": date, "followers": day["f"], "gained": gained, "views": views,
                    "per_1k_views": round(gained / views * 1000, 1) if views else None,
                    "gate_follows": gate.get(date, 0), "partial": not prev})
    return out


MAX_RETRIES = 1000  # beyond this, people still get the "DM me KEYWORD" reply


def retry_count():
    if REDIS_URL:
        return int(redis("HLEN", "dm_retry") or 0)
    with db() as conn:
        return conn.execute("SELECT COUNT(*) FROM retry").fetchone()[0]


def add_retry(comment_id, item):
    if retry_count() >= MAX_RETRIES:
        return
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


# ---------- link-in-bio page ----------

THEMES = ["sunset", "midnight", "ocean", "candy", "mono"]
SOCIALS = ["instagram", "youtube", "whatsapp", "email", "x", "website"]


def load_linkpage():
    if REDIS_URL:
        raw = redis("GET", "linkpage")
        page = json.loads(raw) if raw else {}
    else:
        try:
            with open(LINKPAGE_FILE) as f:
                page = json.load(f)
        except FileNotFoundError:
            page = {}
    page.setdefault("name", "")
    page.setdefault("bio", "")
    page.setdefault("avatar", "")
    page.setdefault("theme", "sunset")
    page.setdefault("socials", {})
    page.setdefault("items", [])
    return page


def save_linkpage(page):
    if REDIS_URL:
        redis("SET", "linkpage", json.dumps(page, ensure_ascii=False))
        return
    tmp = LINKPAGE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(page, f, indent=2, ensure_ascii=False)
    os.replace(tmp, LINKPAGE_FILE)


def safe_url(url):
    """Only real web, email and phone links; blocks javascript: and similar."""
    url = (url or "").strip()
    if url and not url.lower().startswith(("http://", "https://", "mailto:", "tel:")):
        url = "https://" + url if "." in url and ":" not in url.split("/")[0] else ""
    return url


def clean_linkpage(data):
    items = []
    for it in data.get("items", [])[:100]:
        url = safe_url(it.get("url"))
        if not (it.get("title") or "").strip() or not url:
            continue
        items.append({
            "id": "".join(ch for ch in str(it.get("id") or os.urandom(4).hex()) if ch.isalnum())[:16],
            "type": "product" if it.get("type") == "product" else "link",
            "title": it["title"].strip()[:120],
            "subtitle": (it.get("subtitle") or "").strip()[:200],
            "price": (it.get("price") or "").strip()[:30],
            "image": safe_url(it.get("image")),
            "url": url,
            "featured": bool(it.get("featured")),
            "enabled": it.get("enabled", True) is not False,
        })
    socials = {k: (data.get("socials", {}).get(k) or "").strip()[:200] for k in SOCIALS}
    return {
        "name": (data.get("name") or "").strip()[:80],
        "bio": (data.get("bio") or "").strip()[:300],
        "avatar": safe_url(data.get("avatar")),
        "theme": data.get("theme") if data.get("theme") in THEMES else "sunset",
        "socials": socials,
        "items": items,
    }


def social_links(socials):
    """(label, icon, url) for each filled-in social; accepts handles, numbers or full links."""
    out = []
    for key in SOCIALS:
        v = (socials.get(key) or "").strip()
        if not v:
            continue
        handle = v.lstrip("@")
        url = {
            "instagram": v if v.startswith("http") else f"https://instagram.com/{handle}",
            "youtube": v if v.startswith("http") else f"https://youtube.com/@{handle}",
            "whatsapp": v if v.startswith("http") else "https://wa.me/" + "".join(ch for ch in v if ch.isdigit()),
            "email": v if v.startswith("mailto:") else f"mailto:{v}",
            "x": v if v.startswith("http") else f"https://x.com/{handle}",
            "website": safe_url(v),
        }[key]
        label = {"instagram": "Instagram", "youtube": "YouTube", "whatsapp": "WhatsApp",
                 "email": "Email", "x": "X", "website": "Website"}[key]
        out.append((key, label, url))
    return out


def count_click(item_id):
    if REDIS_URL:
        redis("HINCRBY", "link_clicks", item_id, 1)
        return
    with _db_lock, db() as conn:
        conn.execute("INSERT INTO clicks VALUES (?, 1) ON CONFLICT(item_id) DO UPDATE SET n = n + 1",
                     (item_id,))


def click_counts():
    if REDIS_URL:
        flat = redis("HGETALL", "link_clicks") or []
        return {flat[i]: int(flat[i + 1]) for i in range(0, len(flat), 2)}
    with db() as conn:
        return {r["item_id"]: r["n"] for r in conn.execute("SELECT * FROM clicks")}


_profile_cache = {"at": 0, "data": {}}


def instagram_profile():
    """Name/photo from Instagram for the link page, cached for an hour; {} if unavailable."""
    if time.time() - _profile_cache["at"] > 3600:
        try:
            _profile_cache["data"] = ig_get("me", fields="username,name,profile_picture_url")
        except Exception:
            pass  # keep the last good one (or none); the page still renders
        _profile_cache["at"] = time.time()
    return _profile_cache["data"]


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


def _check(r):
    if r.ok:
        return r.json()
    body = r.text.replace(" ", "")
    if '"code":190' in body:
        kv_set("token_invalid", _env_token_id())  # until IG_ACCESS_TOKEN is replaced
    elif any(f'"code":{c},' in body for c in RATE_LIMIT_CODES):
        kv_set("rate_limited_until", time.time() + RATE_LIMIT_BACKOFF)
    raise RuntimeError(f"{r.status_code}: {r.text}")


# Meta's "too many requests" errors (app, user and page level). Each failed call still counts,
# so after one we stop calling for a while instead of making it worse.
RATE_LIMIT_CODES = (4, 17, 32, 613)
RATE_LIMIT_BACKOFF = 15 * 60


def rate_limited_until():
    until = float(kv_get("rate_limited_until") or 0)
    return until if until > time.time() else 0


def ig_get(path, **params):
    params["access_token"] = current_token()
    return _check(requests.get(f"{GRAPH}/{path}", params=params, timeout=20))


def ig_post(path, payload):
    return _check(requests.post(f"{GRAPH}/{path}", params={"access_token": current_token()},
                                json=payload, timeout=20))


def token_is_dead():
    """Instagram invalidated the login (error 190) and IG_ACCESS_TOKEN hasn't been replaced since."""
    return kv_get("token_invalid") == _env_token_id()


# When Instagram keeps refusing comment DMs, stop trying for a while: every refused attempt
# is another automated message, and the "DM me KEYWORD" reply works without one.
DM_PAUSE_AFTER_FAILURES = 15
DM_PAUSE_SECONDS = 30 * 60
DM_PROBE_SECONDS = 5 * 60  # while paused, try one real DM this often to see if Instagram accepts them again


def dms_paused_until():
    return float(kv_get("dm_paused_until") or 0)


def dm_probe_due():
    """While DMs are paused, allow one test DM every few minutes (and claim the slot)."""
    if time.time() - float(kv_get("dm_last_probe") or 0) < DM_PROBE_SECONDS:
        return False
    kv_set("dm_last_probe", time.time())
    return True


def record_dm_result(ok):
    if ok:
        kv_set("dm_fail_streak", 0)
        if dms_paused_until():
            kv_set("dm_paused_until", 0)  # Instagram accepted a DM again: resume right away
        return
    streak = int(kv_get("dm_fail_streak") or 0) + 1
    kv_set("dm_fail_streak", streak)
    # After a manual "Resume DMs now", don't pause again for a while (e.g. while recording a demo).
    if streak >= DM_PAUSE_AFTER_FAILURES and time.time() > float(kv_get("dm_pause_blocked_until") or 0):
        kv_set("dm_paused_until", time.time() + DM_PAUSE_SECONDS)
        kv_set("dm_fail_streak", 0)


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
    media = ig_get("me/media", limit=STATS_REELS, fields=(
        "id,caption,media_type,media_product_type,permalink,thumbnail_url,"
        "media_url,timestamp,like_count,comments_count"))["data"]
    reels = []
    for m in media:
        if m.get("media_product_type") != "REELS":
            continue
        try:
            ins = ig_get(f"{m['id']}/insights", metric=REEL_METRICS)["data"]
            m["insights"] = {i["name"]: i["values"][0]["value"] for i in ins}
        except Exception as e:
            if rate_limited_until():
                raise  # stop here; keep showing the last stats
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
    # While the login is dead, leave comments unhandled so "Send to past comments" can reach them later.
    # While logged out or rate limited, leave comments unhandled so "Send to past comments" reaches them later.
    if not rule or token_is_dead() or rate_limited_until() or not claim_comment(comment_id):
        return False

    # DM first, so the public reply can tell people what to do if Instagram refuses the DM.
    item = {"ig_user_id": ig_user_id, "key": key, "media_id": media_id, "username": username,
            "text": text, "at": time.time()}
    if time.time() < dms_paused_until() and not dm_probe_due():
        dm_ok = False  # skip the attempt; the reply below asks them to DM the keyword
    else:
        dm_ok = send_comment_dm(comment_id, item, rule)
        if not dm_ok:
            add_retry(comment_id, item)

    fail_reply = rule.get("dm_fail_reply") or DEFAULT_DM_FAIL_REPLY
    if fail_reply.strip() == OLD_DM_FAIL_REPLY:
        fail_reply = DEFAULT_DM_FAIL_REPLY
    reply = rule.get("comment_reply") if dm_ok else fail_reply
    if reply:
        reply = pick_reply(reply).replace("{keyword}", dm_keywords(rule)[0].upper())
        try:
            reply_to_comment(comment_id, reply.replace("{username}", username))
            log_activity(media_id, username, text, "comment_reply" if dm_ok else "dm_fail_reply", "ok")
        except Exception as e:
            log_activity(media_id, username, text, "comment_reply", "error", str(e))
    return True


DEFAULT_DM_FAIL_REPLY = ("@{username} Follow me + DM \"{keyword}\" 📩 I'll send it instantly!\n"
                         "@{username} Follow karo aur DM karo \"{keyword}\" 🔥 link turant milega\n"
                         "@{username} Follow + DM me \"{keyword}\" for the link ✅")
# The first version of this reply didn't ask for a follow; rules saved with it get the new one.
OLD_DM_FAIL_REPLY = "@{username} your DM didn't come through 😅 DM me {keyword} and I'll send it instantly 📩"


def dm_keywords(rule):
    """Words that trigger this rule when someone DMs them; rules without keywords answer to LINK."""
    return [k.strip() for k in rule.get("keywords", []) if k.strip()] or ["LINK"]


def handle_dm_text(ig_user_id, igsid, text):
    """Someone DMed a keyword (e.g. because the comment DM was refused): start the same flow.

    Replying inside a conversation the person started works even when Instagram refuses to open
    new conversations from comments.
    """
    if token_is_dead():
        return
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
        record_dm_result(True)
        return True
    except Exception as e:
        log_activity(item["media_id"], item["username"], item["text"], action, "error", explain_error(e))
        if CANT_OPEN_THREAD in str(e):
            record_dm_result(False)
        return False


def retry_failed_dms(max_sends=30):
    """Retries DMs that Instagram refused earlier, while the 7-day private-reply window is open."""
    rules = load_rules().get("reels", {})
    counts = {"sent": 0, "still_failing": 0, "expired": 0, "skipped": ""}
    if token_is_dead():
        counts["skipped"] = "Instagram login expired: reconnect the app first."
        return counts
    if time.time() < dms_paused_until():
        counts["skipped"] = "Comment DMs are paused because Instagram kept refusing them. Try again later."
        return counts
    if rate_limited_until():
        counts["skipped"] = "Instagram's hourly request limit was reached. Try again in 15 minutes."
        return counts
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
            if time.time() < dms_paused_until():
                break
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
    if step not in ("GET", "FOLLOWED") or not rule or token_is_dead():
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
            # Tapped "I followed" after the follow prompt and now follows: a follower won by the gate.
            if step == "FOLLOWED" and rule.get("require_follow") and claim_comment(f"gatefollow:{igsid}"):
                counter_add("gate_follows", key)
                counter_add("gate_follows_day", today_ist())
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
    # The link page and its click redirects are public; its editor (/links/edit) is not.
    public = request.path in ("/links", "/links/") or request.path.startswith(("/webhook", "/cron/", "/go/"))
    if not DASHBOARD_PASSWORD or public:
        return
    auth = request.authorization
    if not auth or (auth.password or "").strip() != DASHBOARD_PASSWORD:
        return ("Login required", 401, {"WWW-Authenticate": 'Basic realm="autopilot"'})


RESUME_HOLD_SECONDS = 20 * 60


@app.post("/api/resume-dms")
def api_resume_dms():
    kv_set("dm_paused_until", 0)
    kv_set("dm_fail_streak", 0)
    kv_set("dm_pause_blocked_until", time.time() + RESUME_HOLD_SECONDS)
    return jsonify({"resumed": True, "no_pause_until": time.time() + RESUME_HOLD_SECONDS})


@app.post("/api/retry-failed")
def api_retry_failed():
    return jsonify(retry_failed_dms())


@app.get("/api/retry-failed")
def api_retry_count():
    return jsonify({"pending": retry_count()})


@app.get("/cron/retry-failed")
def cron_retry_failed():
    if not CRON_SECRET or request.headers.get("Authorization") != f"Bearer {CRON_SECRET}":
        abort(403)
    # Daily job: also takes a follower snapshot, so growth is tracked even if nobody opens the dashboard.
    if not token_is_dead() and not rate_limited_until():
        try:
            record_growth(fetch_stats())
        except Exception:
            pass
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


@app.get("/links")
@app.get("/links/")
def link_page():
    page = load_linkpage()
    ig = instagram_profile()
    items = [it for it in page["items"] if it["enabled"]]
    return render_template(
        "links.html", page=page, items=items, socials=social_links(page["socials"]),
        name=page["name"] or ig.get("name") or ig.get("username", ""),
        avatar=page["avatar"] or ig.get("profile_picture_url", ""),
        username=ig.get("username", ""))


@app.get("/go/<item_id>")
def go(item_id):
    for it in load_linkpage()["items"]:
        if it["id"] == item_id and it["enabled"]:
            try:
                count_click(item_id)
            except Exception:
                pass  # never block the visitor over a counter
            return redirect(it["url"], code=302)
    abort(404)


@app.get("/links/edit")
def link_page_editor():
    return render_template("links_edit.html", themes=THEMES)


@app.get("/api/linkpage")
def api_get_linkpage():
    return jsonify({"page": load_linkpage(), "clicks": click_counts(), "profile": instagram_profile()})


@app.put("/api/linkpage")
def api_put_linkpage():
    page = clean_linkpage(request.get_json(force=True))
    save_linkpage(page)
    return jsonify(page)


@app.get("/api/stats")
def api_stats():
    dead = token_is_dead()
    limited = rate_limited_until()
    if not _stats_cache["data"]:
        # Serverless instances start empty: reuse the last stats saved by any instance.
        saved = kv_get("stats_cache")
        if saved:
            _stats_cache.update(json.loads(saved))
    stale = time.time() - _stats_cache["at"] > STATS_CACHE_SECONDS
    if not dead and not limited and (stale or (request.args.get("refresh") and time.time() - _stats_cache["at"] > 60)):
        try:
            _stats_cache["data"] = fetch_stats()
            _stats_cache["at"] = time.time()
            kv_set("stats_cache", json.dumps(_stats_cache))
            record_growth(_stats_cache["data"])
        except Exception as e:
            limited = rate_limited_until()
            dead = token_is_dead()
            if not _stats_cache["data"] and not dead and not limited:
                return jsonify({"error": str(e)}), 502
    data = dict(_stats_cache["data"] or {"account": {}, "reels": [], "fetched_at": None})
    if dead:
        data["alert"] = ("Instagram logged the app out (error 190), so nothing is being sent. Fix: Meta app → "
                         "API setup with Instagram login → Generate token, paste it into Vercel → Settings → "
                         "Environment Variables → IG_ACCESS_TOKEN, then Redeploy. Comments that arrive "
                         "meanwhile are kept: use “Send to past comments” afterwards.")
    paused = dms_paused_until()
    if not dead and time.time() < paused:
        data["paused_until"] = paused
    if not dead and limited:
        data["rate_limited_until"] = limited
    if SERVERLESS and not REDIS_URL:
        data["warning"] = ("No database connected: rules and activity will be lost. "
                           "In Vercel, add Storage → Upstash Redis and redeploy.")
    data["growth"] = growth_summary()
    data["gate_follows"] = counter_all("gate_follows")
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
    if rate_limited_until():
        return jsonify({"error": "Instagram's hourly request limit was reached. Try again in 15 minutes."}), 429
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
