"""Where Instagram connects drop off, for /owner: how many logins clicked Connect, cancelled or failed on Instagram,
and connected, plus the last failures with Instagram's own reason (to see whether it's personal accounts,
cancelled logins or a real error)."""
import json
import time

import store

KEY = "s:funnel"
FAILS = "s:funnel:fails"
STEPS = [("clicked", "Clicked Connect"), ("cancelled", "Cancelled on Instagram"), ("expired", "Login expired"),
         ("signed_out", "Came back signed out (finished after signing in again)"), ("failed", "Instagram login failed"), ("refused", "Refused (plan limit / account owned by another login)"),
         ("connected", "Connected a new account"), ("reconnected", "Reconnected an account")]


def note(step, user=None, detail=""):
    """Counts one step. Never raises: tracking must not break connecting."""
    try:
        store.redis("HINCRBY", KEY, step, 1)
        if (user or {}).get("id"):
            store.redis("SADD", f"{KEY}:people:{step}", user["id"])  # unique logins, so repeat taps don't inflate it
        if step in ("cancelled", "failed", "refused", "expired"):
            store.redis("LPUSH", FAILS, json.dumps({"at": int(time.time()), "step": step, "email": (user or {}).get("email", ""),
                                                    "detail": str(detail)[:300]}))
            store.redis("LTRIM", FAILS, 0, 29)
    except Exception:
        pass


def stats():
    """(times by step, unique logins by step, recent failures newest first)."""
    try:
        res = store.pipeline([("HGETALL", KEY), ("LRANGE", FAILS, 0, 29)] + [("SCARD", f"{KEY}:people:{k}") for k, _ in STEPS])
        flat, fails = res[0] or [], [json.loads(x) for x in res[1] or []]
        counts = {flat[i]: int(flat[i + 1]) for i in range(0, len(flat), 2)}
        people = {k: int(n or 0) for (k, _), n in zip(STEPS, res[2:])}
    except Exception:
        counts, people, fails = {}, {}, []
    return {k: int(counts.get(k, 0)) for k, _ in STEPS}, {k: people.get(k, 0) for k, _ in STEPS}, fails
