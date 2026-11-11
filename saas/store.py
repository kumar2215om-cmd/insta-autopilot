"""Storage for the multi-account app: Upstash Redis (REST) in production, an in-memory stand-in locally.

Every key starts with "s:" so this app can share an Upstash database with the single-account app.
Per-account keys are "s:t:<ig_user_id>:...".
"""
import json
import os
import threading
import time

import requests

REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")


class MemoryRedis:
    """The handful of Redis commands this app uses, for local runs and tests (lost on restart)."""

    def __init__(self):
        self.data, self.expiry, self.lock = {}, {}, threading.RLock()

    def _alive(self, k):
        if k in self.expiry and self.expiry[k] < time.time():
            self.data.pop(k, None)
            self.expiry.pop(k, None)
        return k in self.data

    def __call__(self, cmd, *a):
        cmd = cmd.upper()
        with self.lock:
            if cmd == "GET":
                return self.data[a[0]] if self._alive(a[0]) else None
            if cmd == "SET":
                k, v, opts = a[0], str(a[1]), [str(o).upper() for o in a[2:]]
                if "NX" in opts and self._alive(k):
                    return None
                self.data[k] = v
                self.expiry.pop(k, None)
                if "EX" in opts:
                    self.expiry[k] = time.time() + int(a[2 + opts.index("EX") + 1])
                return "OK"
            if cmd == "DEL":
                return sum(self.data.pop(k, None) is not None for k in a)
            if cmd == "LPUSH":
                lst = self.data.setdefault(a[0], [])
                for v in a[1:]:
                    lst.insert(0, str(v))
                return len(lst)
            if cmd == "LTRIM":
                lst = self.data.get(a[0], [])
                stop = len(lst) if int(a[2]) == -1 else int(a[2]) + 1
                self.data[a[0]] = lst[int(a[1]):stop]
                return "OK"
            if cmd == "LRANGE":
                lst = self.data.get(a[0], [])
                stop = len(lst) if int(a[2]) == -1 else int(a[2]) + 1
                return lst[int(a[1]):stop]
            if cmd == "HINCRBY":
                h = self.data.setdefault(a[0], {})
                h[a[1]] = str(int(h.get(a[1], 0)) + int(a[2]))
                return int(h[a[1]])
            if cmd == "HSET":
                h = self.data.setdefault(a[0], {})
                added = 0
                for i in range(1, len(a), 2):
                    added += a[i] not in h
                    h[str(a[i])] = str(a[i + 1])
                return added
            if cmd == "HGET":
                return self.data.get(a[0], {}).get(str(a[1]))
            if cmd == "HDEL":
                h = self.data.get(a[0], {})
                return sum(1 for f in a[1:] if h.pop(str(f), None) is not None)
            if cmd == "EXPIRE":
                if a[0] in self.data:
                    self.expiry[a[0]] = time.time() + int(a[1])
                    return 1
                return 0
            if cmd == "HLEN":
                return len(self.data.get(a[0], {}))
            if cmd == "HGETALL":
                h = self.data.get(a[0], {})
                return [x for kv in h.items() for x in kv]
            if cmd == "SADD":
                s = self.data.setdefault(a[0], set())
                before = len(s)
                s.update(str(v) for v in a[1:])
                return len(s) - before
            if cmd == "SREM":
                s = self.data.get(a[0], set())
                return sum(1 for v in a[1:] if str(v) in s and not s.discard(str(v)))
            if cmd == "SMEMBERS":
                return sorted(self.data.get(a[0], set()))
            if cmd == "SCARD":
                return len(self.data.get(a[0], set()))
            if cmd == "ZADD":
                z = self.data.setdefault(a[0], {})
                added = 0
                for i in range(1, len(a), 2):
                    added += str(a[i + 1]) not in z
                    z[str(a[i + 1])] = float(a[i])
                return added
            if cmd == "ZRANGEBYSCORE":
                z = self.data.get(a[0], {})
                lo = float("-inf") if str(a[1]) == "-inf" else float(a[1])
                hi = float("inf") if str(a[2]) == "+inf" else float(a[2])
                rows = [m for m, sc in sorted(z.items(), key=lambda kv: kv[1]) if lo <= sc <= hi]
                if len(a) >= 6 and str(a[3]).upper() == "LIMIT":
                    rows = rows[int(a[4]):int(a[4]) + int(a[5])]
                return rows
            if cmd == "ZREM":
                z = self.data.get(a[0], {})
                return sum(1 for m in a[1:] if z.pop(str(m), None) is not None)
        raise ValueError(f"MemoryRedis: unsupported command {cmd}")


_memory = MemoryRedis()


def redis(*command):
    if not REDIS_URL:
        return _memory(*command)
    r = requests.post(REDIS_URL, headers={"Authorization": f"Bearer {REDIS_TOKEN}"},
                      json=[str(c) for c in command], timeout=10)
    r.raise_for_status()
    return r.json()["result"]


def get_json(key, default=None):
    raw = redis("GET", key)
    return json.loads(raw) if raw else default


def set_json(key, value):
    redis("SET", key, json.dumps(value, ensure_ascii=False))


def claim(key, seconds=30 * 86400):
    """True the first time a key is claimed, so each comment/button tap is handled once."""
    return redis("SET", key, 1, "NX", "EX", seconds) == "OK"


def hash_all(key):
    flat = redis("HGETALL", key) or []
    return {flat[i]: int(flat[i + 1]) for i in range(0, len(flat), 2)}


# ---------- scheduled follow-up DMs ----------

FOLLOWUPS = "s:followups"


def schedule(due_at, item):
    redis("ZADD", FOLLOWUPS, int(due_at), json.dumps(item, sort_keys=True))


def take_due(limit=25):
    """Due items, each returned to exactly one caller (ZREM decides who got it)."""
    out = []
    for raw in redis("ZRANGEBYSCORE", FOLLOWUPS, "-inf", int(time.time()), "LIMIT", 0, limit) or []:
        if int(redis("ZREM", FOLLOWUPS, raw) or 0):
            out.append(json.loads(raw))
    return out


# ---------- per-automation numbers (Auto DM list) ----------

def rule_count(ig_id, key, field, n=1):
    redis("HINCRBY", account_key(ig_id, f"rs:{key}"), field, n)


def rule_stats(ig_id, keys):
    return {k: hash_all(account_key(ig_id, f"rs:{k}")) for k in keys}


# ---------- plans ----------

def is_pro(acc):
    """Pro by plan (set by hand until billing exists) or by free months earned through referrals."""
    return bool(acc) and (acc.get("plan") == "pro" or acc.get("pro_until", 0) > time.time())


def grant_pro_days(acc, days):
    acc["pro_until"] = int(max(time.time(), acc.get("pro_until", 0)) + days * 86400)


# ---------- accounts ----------

def account_key(ig_id, part=""):
    return f"s:t:{ig_id}" + (f":{part}" if part else "")


def load_account(ig_id):
    return get_json(account_key(ig_id)) if ig_id else None


def save_account(acc):
    set_json(account_key(acc["id"]), acc)
    redis("SADD", "s:accounts", acc["id"])
    if acc.get("username"):  # public link page lookup: replyinbox.in/<username>
        redis("SET", f"s:user:{acc['username'].lower()}", acc["id"])


def account_by_username(username):
    return load_account(redis("GET", f"s:user:{username.lower()}"))


def account_ids():
    return redis("SMEMBERS", "s:accounts") or []


def delete_account(ig_id):
    """Removes an account and everything stored for it (used by Disconnect and Meta's deletion callback)."""
    parts = ["", "rules", "activity", "counts", "rate_limited", "token_dead", "stats", "report", "autos", "medias",
             "page", "contacts", "clicks", "retry", "giveaways"]
    medias = redis("SMEMBERS", account_key(ig_id, "medias")) or []
    acc = load_account(ig_id) or {}
    if acc.get("mcp_key_hash"):
        redis("DEL", f"s:mcpkey:{acc['mcp_key_hash']}")
    if acc.get("username") and redis("GET", f"s:user:{acc['username'].lower()}") == ig_id:
        redis("DEL", f"s:user:{acc['username'].lower()}")
    redis("DEL", *[account_key(ig_id, f"day:{day_str(i)}") for i in range(41)])
    abs_ = [account_key(ig_id, f"{p}:{k}") for k in load_rules(ig_id).get("reels", {}) for p in ("ab", "rs")]
    if abs_:
        redis("DEL", *abs_)
    threads = redis("HGETALL", account_key(ig_id, "threads")) or []
    chats = [account_key(ig_id, f"chat:{u}") for u in threads[::2]]
    redis("DEL", *[account_key(ig_id, p) for p in parts + ["threads"]], *chats,
          *[account_key(ig_id, f"m:{m}") for m in medias])
    redis("SREM", "s:accounts", ig_id)


def load_rules(ig_id):
    return get_json(account_key(ig_id, "rules"), {"reels": {}})


def save_rules(ig_id, rules):
    set_json(account_key(ig_id, "rules"), rules)


def log_activity(ig_id, media_id, username, comment, action, status, detail=""):
    key = account_key(ig_id, "activity")
    redis("LPUSH", key, json.dumps({
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "media_id": media_id,
        "username": username, "comment": comment[:300], "action": action, "status": status,
        "detail": str(detail)[:500]}, ensure_ascii=False))
    redis("LTRIM", key, 0, 99)


def recent_activity(ig_id):
    return [json.loads(x) for x in redis("LRANGE", account_key(ig_id, "activity"), 0, 99) or []]


def day_str(offset_days=0):
    """Today's date in India (most creators are there), or offset_days earlier."""
    return time.strftime("%Y-%m-%d", time.gmtime(time.time() + 19800 - offset_days * 86400))


def count(ig_id, field, n=1):
    redis("HINCRBY", account_key(ig_id, "counts"), field, n)
    if ":" not in field:  # per-day numbers for the weekly summary (monthly counters already carry their month)
        key = account_key(ig_id, f"day:{day_str()}")
        redis("HINCRBY", key, field, n)
        redis("EXPIRE", key, 40 * 86400)


def days(ig_id, n=14):
    """[(date, {field: count})] for the last n days, oldest first."""
    return [(day_str(i), hash_all(account_key(ig_id, f"day:{day_str(i)}"))) for i in range(n - 1, -1, -1)]


def counts(ig_id):
    return hash_all(account_key(ig_id, "counts"))


# ---------- per-reel numbers and auto-setup log ----------

def media_count(ig_id, media_id, field, n=1):
    if not media_id or not str(media_id).isdigit():
        return
    redis("HINCRBY", account_key(ig_id, f"m:{media_id}"), field, n)
    redis("SADD", account_key(ig_id, "medias"), media_id)


def media_counts(ig_id, media_id):
    return hash_all(account_key(ig_id, f"m:{media_id}"))


def log_auto(ig_id, event):
    key = account_key(ig_id, "autos")
    redis("LPUSH", key, json.dumps(event, ensure_ascii=False))
    redis("LTRIM", key, 0, 19)


def recent_autos(ig_id):
    return [json.loads(x) for x in redis("LRANGE", account_key(ig_id, "autos"), 0, 19) or []]


# ---------- link-in-bio page ----------

def load_page(ig_id):
    return get_json(account_key(ig_id, "page"))


def save_page(ig_id, page):
    set_json(account_key(ig_id, "page"), page)


def count_click(ig_id, item_id):
    redis("HINCRBY", account_key(ig_id, "clicks"), item_id, 1)


def clicks(ig_id):
    return hash_all(account_key(ig_id, "clicks"))


# ---------- contacts: everyone who commented, DMed or tapped a button ----------

MAX_CONTACTS = 5000


def contact_key(username, igsid=""):
    return (username or "").lower() or f"id:{igsid}"


def save_contact(ig_id, contact):
    key = account_key(ig_id, "contacts")
    redis("HSET", key, contact_key(contact.get("username"), contact.get("igsid", "")), json.dumps(contact, ensure_ascii=False))


def get_contact(ig_id, username="", igsid=""):
    raw = redis("HGET", account_key(ig_id, "contacts"), contact_key(username, igsid))
    return json.loads(raw) if raw else None


def clean_tags(tags):
    out = []
    for t in tags or []:
        t = " ".join(str(t).strip().lower().split())[:24]
        if t and t not in out:
            out.append(t)
    return out[:20]


def touch_contact(ig_id, username="", igsid="", keyword="", followed=None, source="", email="", phone="", tags=()):
    """Adds or updates one person who interacted with an automation."""
    if not username and not igsid:
        return
    key = account_key(ig_id, "contacts")
    field = contact_key(username, igsid)
    raw = redis("HGET", key, field)
    now = int(time.time())
    if raw:
        c = json.loads(raw)
    else:
        if int(redis("HLEN", key) or 0) >= MAX_CONTACTS if REDIS_URL else False:
            return
        c = {"username": username, "igsid": igsid, "first_at": now, "interactions": 0, "email": "", "followed": False}
    c["last_at"] = now
    c["interactions"] = c.get("interactions", 0) + 1
    if username:
        c["username"] = username
    if igsid:
        c["igsid"] = igsid
    if keyword:
        c["keyword"] = keyword
    if source:
        c["source"] = source
    if followed:
        c["followed"] = True
    if email:
        c["email"] = email
    if phone:
        c["phone"] = phone
    if tags:
        c["tags"] = clean_tags(list(c.get("tags") or []) + list(tags))
    redis("HSET", key, field, json.dumps(c, ensure_ascii=False))


def set_contact_tags(ig_id, key, tags):
    raw = redis("HGET", account_key(ig_id, "contacts"), key)
    if not raw:
        return None
    c = json.loads(raw)
    c["tags"] = clean_tags(tags)
    redis("HSET", account_key(ig_id, "contacts"), key, json.dumps(c, ensure_ascii=False))
    return c


def contacts(ig_id):
    flat = redis("HGETALL", account_key(ig_id, "contacts")) or []
    rows = [json.loads(flat[i + 1]) for i in range(0, len(flat), 2)]
    return sorted(rows, key=lambda c: -c.get("last_at", 0))
