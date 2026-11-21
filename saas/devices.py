"""Signed-in devices for a ReplyInbox login (Settings → Security), like SuperProfile's "Your devices".

Each sign-in gets a random id kept in the (signed) session cookie and in s:usess:<user> = {sid: {ua, ip, city, country,
created, seen}}. A request whose id was removed (signed out from another device) loses its session at once.
"""
import json
import re
import secrets
import time

import store

MAX = 30


def _key(uid):
    return f"s:usess:{uid}"


def label(ua):
    """'Chrome · Mac' from a User-Agent string."""
    ua = ua or ""
    browser = next((n for p, n in ((r"Edg/", "Edge"), (r"OPR/|Opera", "Opera"), (r"SamsungBrowser", "Samsung Internet"), (r"Firefox/", "Firefox"),
                                   (r"CriOS|Chrome/", "Chrome"), (r"Safari/", "Safari")) if re.search(p, ua)), "Browser")
    osn = next((n for p, n in ((r"iPhone|iPad|iOS", "iPhone"), (r"Android", "Android"), (r"Mac OS X|Macintosh", "Mac"), (r"Windows", "Windows"),
                               (r"CrOS", "Chromebook"), (r"Linux", "Linux")) if re.search(p, ua)), "")
    return f"{browser} · {osn}" if osn else browser


def start(uid, ua, ip, city="", country=""):
    sid = secrets.token_urlsafe(12)
    now = int(time.time())
    store.redis("HSET", _key(uid), sid, json.dumps({"ua": (ua or "")[:300], "ip": (ip or "")[:60], "city": (city or "")[:60],
                                                     "country": (country or "")[:4], "created": now, "seen": now}))
    _trim(uid)
    return sid


def _trim(uid):
    items = all_of(uid)
    for d in sorted(items, key=lambda d: d["seen"])[:max(0, len(items) - MAX)]:
        store.redis("HDEL", _key(uid), d["sid"])


def all_of(uid):
    raw = store.redis("HGETALL", _key(uid)) or []
    pairs = raw.items() if isinstance(raw, dict) else zip(raw[::2], raw[1::2])
    out = []
    for sid, v in pairs:
        try:
            out.append({"sid": sid, **json.loads(v)})
        except (TypeError, ValueError):
            pass
    return sorted(out, key=lambda d: -d.get("seen", 0))


def check(uid, sid, ua="", ip="", city="", country=""):
    """True if this sign-in is still allowed. Refreshes 'last active' at most every 5 minutes."""
    raw = store.redis("HGET", _key(uid), sid)
    if not raw:
        return False
    try:
        d = json.loads(raw)
    except ValueError:
        return False
    if time.time() - d.get("seen", 0) > 300:
        d.update(seen=int(time.time()), ip=(ip or d.get("ip", ""))[:60], city=(city or d.get("city", ""))[:60], country=(country or d.get("country", ""))[:4])
        store.redis("HSET", _key(uid), sid, json.dumps(d))
    return True


def end(uid, sid):
    store.redis("HDEL", _key(uid), sid)


def end_others(uid, keep):
    n = 0
    for d in all_of(uid):
        if d["sid"] != keep:
            end(uid, d["sid"])
            n += 1
    return n
