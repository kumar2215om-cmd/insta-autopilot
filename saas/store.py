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


# ---------- accounts ----------

def account_key(ig_id, part=""):
    return f"s:t:{ig_id}" + (f":{part}" if part else "")


def load_account(ig_id):
    return get_json(account_key(ig_id)) if ig_id else None


def save_account(acc):
    set_json(account_key(acc["id"]), acc)
    redis("SADD", "s:accounts", acc["id"])


def account_ids():
    return redis("SMEMBERS", "s:accounts") or []


def delete_account(ig_id):
    """Removes an account and everything stored for it (used by Disconnect and Meta's deletion callback)."""
    parts = ["", "rules", "activity", "counts", "rate_limited", "token_dead", "stats", "report", "autos", "medias"]
    medias = redis("SMEMBERS", account_key(ig_id, "medias")) or []
    redis("DEL", *[account_key(ig_id, p) for p in parts], *[account_key(ig_id, f"m:{m}") for m in medias])
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


def count(ig_id, field, n=1):
    redis("HINCRBY", account_key(ig_id, "counts"), field, n)


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
