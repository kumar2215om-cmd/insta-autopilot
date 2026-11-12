"""ReplyInbox plans and the business model (internal: the per-sale fee is not shown on the landing page).

Two revenue streams:
1. Subscriptions: Free / Creator / Pro / Agency (prices below, in ₹ per month).
2. A platform fee on sales collected through ReplyInbox (UPI / card payments in DM, once Razorpay is connected),
   like SuperProfile's ~5% + GST: 5% on Free, 2% on every paid plan (plus 18% GST on the fee).
   Sales on the creator's own payment pages (the Sales page's tracking links) carry no fee: that money never
   passes through us.

A plan is set on the account as "plan" (by hand from /owner until billing exists). Free months earned through
referrals ("pro_until") count as Pro. Every number here can be changed in one place.
"""
import time

GST = 0.18  # charged on our fee, as SuperProfile does

PLANS = {
    "free": {"name": "Free", "price": 0, "yearly": 0, "monthly_dms": 1000, "ai_replies": 25, "ai_kind": "trial",
             "accounts": 1, "sale_fee_pct": 5.0},
    "creator": {"name": "Creator", "price": 199, "yearly": 1999, "monthly_dms": 0, "ai_replies": 300, "ai_kind": "month",
                "accounts": 1, "sale_fee_pct": 2.0},
    "pro": {"name": "Pro", "price": 499, "yearly": 4999, "monthly_dms": 0, "ai_replies": 2000, "ai_kind": "month",
            "accounts": 3, "sale_fee_pct": 2.0},
    "agency": {"name": "Agency", "price": 1499, "yearly": 14999, "monthly_dms": 0, "ai_replies": 10000, "ai_kind": "month",
               "accounts": 10, "sale_fee_pct": 2.0},
}
PAID = ("creator", "pro", "agency")
AI_TOPUP = {"replies": 1000, "price": 99}  # extra AI replies, any paid plan


def plan_of(acc):
    """The account's plan id. Referral months count as Pro; an unknown value counts as Free."""
    if not acc:
        return "free"
    plan = acc.get("plan") or "free"
    if plan not in PLANS:
        plan = "free"
    if plan in ("free", "creator") and acc.get("pro_until", 0) > time.time():
        return "pro"
    return plan


def plan(acc):
    return {"id": plan_of(acc), **PLANS[plan_of(acc)]}


def is_paid(acc):
    return plan_of(acc) in PAID


def platform_fee(acc, amount):
    """What a sale of `amount` ₹ collected through ReplyInbox splits into, in paise-rounded rupees:
    fee (our cut), gst (18% on the fee), creator_gets (the rest). E.g. Free plan, ₹499: fee 24.95, gst 4.49."""
    pct = PLANS[plan_of(acc)]["sale_fee_pct"]
    fee = round(amount * pct / 100, 2)
    gst = round(fee * GST, 2)
    return {"plan": plan_of(acc), "fee_pct": pct, "fee": fee, "gst": gst, "total_fee": round(fee + gst, 2),
            "creator_gets": round(amount - fee - gst, 2)}
