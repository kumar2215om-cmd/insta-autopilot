"""ReplyInbox plans and the business model (internal: the per-sale fee is not shown on the landing page).

Two revenue streams:
1. Subscriptions: Free / Starter (decoy) / Creator / Pro / Agency (prices below, in ₹ per month).
2. A platform fee on sales collected through ReplyInbox (UPI / card payments in DM, once Razorpay is connected),
   like SuperProfile's ~5% + GST. Free: 5% + GST, all-in (we pay the gateway out of it). Paid plans: 2% + GST plus
   the payment gateway's own charges (Razorpay's fee + its GST), passed through at cost.
   Sales on the creator's own payment pages (the Sales page's tracking links) carry no fee: that money never
   passes through us.

A plan is set on the account as "plan" (by hand from /owner until billing exists). Free months earned through
referrals ("pro_until") count as Pro. Every number here can be changed in one place.
"""
import os
import time

GST = 0.18  # charged on our fee, as SuperProfile does
# Paid-only features. Locked only when PLAN_LOCKS=on (turn it on with billing; during the beta every feature is free).
PAID_FEATURES = {"follow_gate"}
LOCKS_ON = os.environ.get("PLAN_LOCKS", "off").lower() == "on"
# Razorpay's standard fee, used when the real fee of a payment isn't known yet (check the current rate when signing up)
GATEWAY_PCT = float(os.environ.get("GATEWAY_FEE_PCT", "2.0"))

PLANS = {
    "free": {"name": "Free", "price": 0, "yearly": 0, "monthly_dms": 1000, "ai_replies": 25, "ai_kind": "trial",
             "accounts": 1, "sale_fee_pct": 5.0, "pass_gateway": False},
    # Starter is the decoy: a little more than Free, none of the money features, so Creator looks like the obvious pick
    "starter": {"name": "Starter", "price": 149, "yearly": 1499, "monthly_dms": 3000, "ai_replies": 25, "ai_kind": "trial",
                "accounts": 1, "sale_fee_pct": 2.0, "pass_gateway": True},
    "creator": {"name": "Creator", "price": 199, "yearly": 1999, "monthly_dms": 0, "ai_replies": 300, "ai_kind": "month",
                "accounts": 1, "sale_fee_pct": 2.0, "pass_gateway": True},
    "pro": {"name": "Pro", "price": 499, "yearly": 4999, "monthly_dms": 0, "ai_replies": 2000, "ai_kind": "month",
            "accounts": 3, "sale_fee_pct": 2.0, "pass_gateway": True},
    "agency": {"name": "Agency", "price": 1499, "yearly": 14999, "monthly_dms": 0, "ai_replies": 10000, "ai_kind": "month",
               "accounts": 10, "sale_fee_pct": 2.0, "pass_gateway": True},
}
PAID = ("starter", "creator", "pro", "agency")
AI_TOPUP = {"replies": 1000, "price": 99}  # extra AI replies, any paid plan
# One more Instagram account on Creator or Pro, per month (each Instagram account is its own account here; charged with billing)
EXTRA_ACCOUNT = {"price": 149, "plans": ("creator", "pro")}


def plan_of(acc):
    """The account's plan id. Referral months count as Pro; an unknown value counts as Free."""
    if not acc:
        return "free"
    plan = acc.get("plan") or "free"
    if plan not in PLANS:
        plan = "free"
    if plan in ("free", "starter", "creator") and acc.get("pro_until", 0) > time.time():
        return "pro"
    return plan


def plan(acc):
    return {"id": plan_of(acc), **PLANS[plan_of(acc)]}


def is_paid(acc):
    return plan_of(acc) in PAID


def has(acc, feature):
    """Whether the account's plan includes a feature (always true while plan locks are off)."""
    return not LOCKS_ON or feature not in PAID_FEATURES or is_paid(acc)


def platform_fee(acc, amount, gateway_fee=None):
    """What a sale of `amount` ₹ collected through ReplyInbox splits into, in paise-rounded rupees.
    fee: our cut; gst: 18% on our cut; gateway: the payment gateway's charge passed to the creator (paid plans only;
    `gateway_fee` is the real charge incl. its GST when known, else GATEWAY_PCT + GST); creator_gets: the rest.
    E.g. ₹499 on Free: fee 24.95 + gst 4.49 = 29.44 all-in. On Creator: 9.98 + 1.80 + gateway 11.78 = 23.56."""
    p = PLANS[plan_of(acc)]
    fee = round(amount * p["sale_fee_pct"] / 100, 2)
    gst = round(fee * GST, 2)
    gateway = 0.0
    if p["pass_gateway"]:
        gateway = round(gateway_fee if gateway_fee is not None else amount * GATEWAY_PCT / 100 * (1 + GST), 2)
    total = round(fee + gst + gateway, 2)
    return {"plan": plan_of(acc), "fee_pct": p["sale_fee_pct"], "fee": fee, "gst": gst, "gateway": gateway,
            "total_fee": total, "creator_gets": round(amount - total, 2)}
