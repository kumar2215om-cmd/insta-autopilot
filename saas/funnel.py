"""Where Instagram connects drop off, for /owner: how many logins clicked Connect, cancelled or failed on Instagram,
and connected, plus the last failures with Instagram's own reason (to see whether it's personal accounts,
cancelled logins or a real error)."""
import json
import time

import store

KEY = "s:funnel"
FAILS = "s:funnel:fails"
STEPS = [("clicked", "Clicked Connect"), ("cancelled", "Cancelled on Instagram"), ("expired", "Login expired"),
         ("failed", "Instagram login failed"), ("refused", "Refused (plan limit / account owned by another login)"),
         ("connected", "Connected a new account"), ("reconnected", "Reconnected an account")]


def note(step, user=None, detail=""):
    """Counts one step. Never raises: tracking must not break connecting."""
    try:
        store.redis("HINCRBY", KEY, step, 1)
        if step in ("cancelled", "failed", "refused", "expired"):
            store.redis("LPUSH", FAILS, json.dumps({"at": int(time.time()), "step": step, "email": (user or {}).get("email", ""),
                                                    "detail": str(detail)[:300]}))
            store.redis("LTRIM", FAILS, 0, 29)
    except Exception:
        pass


def stats():
    """(counts by step, recent failures newest first)."""
    try:
        counts = store.hash_all(KEY)
        fails = [json.loads(x) for x in store.redis("LRANGE", FAILS, 0, 29) or []]
    except Exception:
        counts, fails = {}, []
    return {k: int(counts.get(k, 0)) for k, _ in STEPS}, fails
