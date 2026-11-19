"""Refer & earn.

A creator shares replyinbox.in/r/<their Instagram username>. A referral counts once the invited person signs in
and connects their first Instagram account (so throwaway emails don't count).

- Every SIGNUPS_PER_MONTH referrals: the referrer gets 1 month of Starter free. If they already pay for a plan,
  that month's Starter price is added to their earnings instead.
- Every payment a referred login makes in its first WINDOW_DAYS: the referrer earns COMMISSION_PCT of it.
- Earnings are paid out by UPI on request (at least PAYOUT_MIN); the team marks payouts paid on /owner.

Stored on the user (s:u:<id>): referred_by, referred_at (on the invited login); ref_signups, ref_months,
bonus_until, earnings, payouts, upi (on the referrer). Global lists for /owner: s:commissions, s:payouts.
"""
import json
import re
import secrets
import time

import plans
import store
import users

SIGNUPS_PER_MONTH = 10
BONUS_PLAN = "starter"
BONUS_DAYS = 30
COMMISSION_PCT = 20
WINDOW_DAYS = 365
PAYOUT_MIN = 500
UPI_RE = re.compile(r"^[a-zA-Z0-9.\-_]{2,64}@[a-zA-Z][a-zA-Z0-9.]{1,32}$")


class ReferralError(Exception):
    """A problem to show the person as it is."""


def referrer_for(code):
    """The login behind an invite code (an Instagram username connected to ReplyInbox), or None."""
    acc = store.account_by_username(code) if code else None
    return users.owner_of(acc) if acc and not acc.get("demo") else None


def record_signup(user, code, username=""):
    """Called when a login connects its first Instagram account. Returns the referrer if this counted."""
    if not code or user.get("referred_by") or user.get("accounts"):
        return None
    ref = referrer_for(code)
    if not ref or ref["id"] == user["id"]:
        return None
    user["referred_by"], user["referred_at"] = ref["id"], int(time.time())
    users.save(user)
    ref = users.get(ref["id"])
    signups = ref.setdefault("ref_signups", [])
    if any(s["uid"] == user["id"] for s in signups):
        return None
    signups.append({"uid": user["id"], "username": username, "at": int(time.time())})
    if len(signups) % SIGNUPS_PER_MONTH == 0:
        _grant_month(ref)
    users.save(ref)
    return ref


def _grant_month(ref):
    """One free month of Starter, or its price as earnings when the referrer already pays for a plan."""
    now = time.time()
    ref["ref_months"] = int(ref.get("ref_months") or 0) + 1
    if users.current_plan(ref) == "free":
        ref["bonus_until"] = int(max(now, ref.get("bonus_until") or 0) + BONUS_DAYS * 86400)
        users.save(ref)
        users.sync_plan(ref)
    else:
        price = plans.PLANS[BONUS_PLAN]["price"]
        ref.setdefault("earnings", []).insert(0, {"id": "bonus_" + secrets.token_hex(4), "kind": "bonus", "amount": 0,
                                                  "commission": price, "plan": BONUS_PLAN, "at": int(now),
                                                  "from": f"{SIGNUPS_PER_MONTH} sign-ups"})


def on_payment(user, order):
    """Called once per paid order (billing.activate). Credits the referrer's commission."""
    ref_id = user.get("referred_by")
    if not ref_id or time.time() - (user.get("referred_at") or 0) > WINDOW_DAYS * 86400:
        return None
    ref = users.get(ref_id)
    if not ref:
        return None
    earnings = ref.setdefault("earnings", [])
    if any(e["id"] == order["id"] for e in earnings):
        return None
    entry = {"id": order["id"], "kind": "commission", "amount": order["amount"], "plan": order["plan"],
             "period": order.get("period", "month"), "commission": round(order["amount"] * COMMISSION_PCT / 100),
             "at": int(time.time()), "from": mask(user.get("email", ""))}
    earnings.insert(0, entry)
    users.save(ref)
    store.redis("LPUSH", "s:commissions", json.dumps({"ref": ref["id"], "ref_email": ref.get("email", ""), **entry}))
    store.redis("LTRIM", "s:commissions", 0, 999)
    return entry


def mask(email):
    name, _, domain = (email or "").partition("@")
    return (name[:2] + "•••@" + domain) if domain else "a creator"


def balance(user):
    earned = sum(e["commission"] for e in user.get("earnings") or [])
    paid = sum(p["amount"] for p in user.get("payouts") or [] if p["status"] == "paid")
    requested = sum(p["amount"] for p in user.get("payouts") or [] if p["status"] == "requested")
    return {"earned": earned, "paid": paid, "requested": requested, "available": earned - paid - requested}


def set_upi(user, upi):
    upi = str(upi or "").strip()
    if not UPI_RE.match(upi):
        raise ReferralError("That doesn't look like a UPI ID (e.g. name@okaxis).")
    user["upi"] = upi
    users.save(user)
    return upi


def request_payout(user):
    b = balance(user)
    if not user.get("upi"):
        raise ReferralError("Add your UPI ID first.")
    if b["available"] < PAYOUT_MIN:
        raise ReferralError(f"You can withdraw from ₹{PAYOUT_MIN}. You have ₹{b['available']} now.")
    p = {"id": "po_" + secrets.token_hex(5), "amount": b["available"], "upi": user["upi"], "at": int(time.time()),
         "status": "requested"}
    user.setdefault("payouts", []).insert(0, p)
    users.save(user)
    store.redis("LPUSH", "s:payouts", json.dumps({"user": user["id"], "email": user.get("email", ""), "id": p["id"]}))
    return p


def mark_paid(user_id, payout_id):
    user = users.get(user_id)
    p = next((x for x in (user or {}).get("payouts") or [] if x["id"] == payout_id), None)
    if not p:
        raise ReferralError("Unknown payout.")
    p.update(status="paid", paid_at=int(time.time()))
    users.save(user)
    return p


def payout_requests():
    """Every payout ever requested (newest first), with its current status, for /owner."""
    out = []
    for raw in store.redis("LRANGE", "s:payouts", 0, 199) or []:
        ref = json.loads(raw)
        user = users.get(ref["user"])
        p = next((x for x in (user or {}).get("payouts") or [] if x["id"] == ref["id"]), None)
        if p:
            out.append({**p, "user": ref["user"], "email": ref.get("email", "")})
    return out


def summary(user, link):
    signups = user.get("ref_signups") or []
    return {"link": link, "signups": len(signups), "per_month": SIGNUPS_PER_MONTH,
            "to_next": SIGNUPS_PER_MONTH - len(signups) % SIGNUPS_PER_MONTH, "months": int(user.get("ref_months") or 0),
            "bonus_until": user.get("bonus_until") if (user.get("bonus_until") or 0) > time.time() else None,
            "pct": COMMISSION_PCT, "window_months": WINDOW_DAYS // 30, "payout_min": PAYOUT_MIN,
            "recent": [{"username": s.get("username", ""), "at": s["at"]} for s in signups[::-1][:50]],
            "paying": len({e["from"] for e in user.get("earnings") or [] if e["kind"] == "commission"}),
            "earnings": (user.get("earnings") or [])[:100], "payouts": (user.get("payouts") or [])[:50],
            "upi": user.get("upi", ""), **balance(user)}
