"""ReplyInbox plans and the business model (internal: the per-sale fee is not shown on the landing page).

Two revenue streams:
1. Subscriptions: Free / Starter (decoy) / Creator / Pro / Agency (prices below, in ₹ per month).
2. A platform fee on sales collected through ReplyInbox (UPI / card payments in DM, once Razorpay is connected),
   like SuperProfile's ~5% + GST. Free, Starter and Creator: 5% + GST, all-in (we pay the gateway out of it).
   Pro and Agency: 2% + GST plus the payment gateway's own charges (Razorpay's fee + its GST), passed through at cost.
   Sales on the creator's own payment pages (the Sales page's tracking links) carry no fee: that money never
   passes through us.

A plan is set on the account as "plan" (by hand from /owner until billing exists). Free months earned through
referrals ("pro_until") count as Pro. Every number here can be changed in one place.
"""
import os
import time

GST = 0.18  # charged on our fee, as SuperProfile does
# Plan locks are on: each feature needs the plan named in FEATURES. PLAN_LOCKS=off (env) unlocks everything again.
LOCKS_ON = os.environ.get("PLAN_LOCKS", "on").lower() != "off"
ORDER = ("free", "starter", "creator", "pro", "agency")
# feature -> the lowest plan that has it (every plan above it has it too)
FEATURES = {
    "follow_gate": "starter",     # follow to unlock
    "capture": "starter",         # ask for email / WhatsApp number in a DM
    "story_replies": "starter",   # story reply and story mention automations
    "page_pro": "starter",        # link page: brand colour, two-column desktop layout, SEO and share image
    "cart_tools": "starter",      # abandoned-cart reminders, Leads and Payments CSV export
    "sell_extras": "creator",     # courses: US$ price, bump offer, GST on top, Google Analytics
    "lead_agent": "creator",      # Lead Qualifier agent
    "course_emails": "creator",   # automatic course emails
    "team": "creator",
    "brand_agent": "pro",         # Brand Collab agent
    "video_upload": "pro",        # course video files
    "remove_branding": "pro",     # no "Made with ReplyInbox" on the link page
    "mcp": "pro",                 # Connect Claude
    "mcp_multi": "agency",        # one Claude link for every account of the login
}
FEATURE_NAMES = {"follow_gate": "Follow to unlock", "capture": "Email and WhatsApp capture", "story_replies": "Story reply automations",
                 "page_pro": "Brand colour, layout and SEO", "cart_tools": "Cart reminders and CSV export",
                 "sell_extras": "US$ pricing, bump offers, GST and Google Analytics", "lead_agent": "Lead Qualifier agent",
                 "course_emails": "Automatic course emails", "team": "Team members", "brand_agent": "Brand Collab agent",
                 "video_upload": "Course video upload", "remove_branding": "Removing \"Made with ReplyInbox\"",
                 "mcp": "Connect Claude", "mcp_multi": "One Claude link for all accounts"}
# Razorpay's standard fee, used when the real fee of a payment isn't known yet (check the current rate when signing up)
GATEWAY_PCT = float(os.environ.get("GATEWAY_FEE_PCT", "2.0"))

# Per-plan limits (0 = none). assistant_day: Home AI questions a day; lead_agent / brand_agent: chats read a month;
# course_emails: automatic course emails a month; video_gb: course video storage; team: team members.
PLANS = {
    "free": {"name": "Free", "price": 0, "yearly": 0, "monthly_dms": 1000, "ai_replies": 25, "ai_kind": "trial",
             "accounts": 1, "sale_fee_pct": 5.0, "pass_gateway": False,
             "assistant_day": 2, "lead_agent": 0, "brand_agent": 0, "course_emails": 0, "video_gb": 0, "team": 0},
    # Starter is the decoy: a little more than Free, none of the money features, so Creator looks like the obvious pick
    "starter": {"name": "Starter", "price": 149, "yearly": 1499, "monthly_dms": 3000, "ai_replies": 25, "ai_kind": "trial",
                "accounts": 1, "sale_fee_pct": 5.0, "pass_gateway": False,
                "assistant_day": 3, "lead_agent": 0, "brand_agent": 0, "course_emails": 0, "video_gb": 0, "team": 0},
    "creator": {"name": "Creator", "price": 199, "yearly": 1999, "monthly_dms": 0, "ai_replies": 300, "ai_kind": "month",
                "accounts": 1, "sale_fee_pct": 5.0, "pass_gateway": False,
                "assistant_day": 10, "lead_agent": 50, "brand_agent": 0, "course_emails": 1000, "video_gb": 0, "team": 1},
    "pro": {"name": "Pro", "price": 599, "yearly": 5999, "monthly_dms": 0, "ai_replies": 2000, "ai_kind": "month",
            "accounts": 3, "sale_fee_pct": 2.0, "pass_gateway": True,
            "assistant_day": 25, "lead_agent": 300, "brand_agent": 100, "course_emails": 5000, "video_gb": 10, "team": 2},
    "agency": {"name": "Agency", "price": 2000, "yearly": 19999, "monthly_dms": 0, "ai_replies": 10000, "ai_kind": "month",
               "accounts": 10, "sale_fee_pct": 2.0, "pass_gateway": True,
               "assistant_day": 60, "lead_agent": 1500, "brand_agent": 500, "course_emails": 20000, "video_gb": 50, "team": 5},
}
PAID = ("starter", "creator", "pro", "agency")
# Prices outside India, in US$ (monthly, yearly); shown by the pricing page's currency switch
USD = {"free": (0, 0), "starter": (5, 48), "creator": (9, 84), "pro": (19, 180), "agency": (59, 564)}
USD_ADDONS = {"extra_account": 5, "ai_topup": 2}
AI_TOPUP = {"replies": 1000, "price": 99}  # extra AI replies, any paid plan
# One more Instagram account on Creator or Pro, per month (each Instagram account is its own account here; charged with billing)
EXTRA_ACCOUNT = {"price": 149, "plans": ("creator", "pro")}


def plan_of(acc):
    """The account's plan id. Old referral months count as Pro, earned Starter months as Starter; an unknown value counts as Free."""
    if not acc:
        return "free"
    plan = acc.get("plan") or "free"
    if plan not in PLANS:
        plan = "free"
    if plan != "free" and acc.get("plan_until") and acc["plan_until"] < time.time():
        plan = "free"  # a paid period ran out (plans set by hand on /owner have no end date)
    if plan in ("free", "starter", "creator") and acc.get("pro_until", 0) > time.time():
        return "pro"
    if plan == "free" and (acc.get("starter_until") or 0) > time.time():
        return "starter"  # a free Starter month earned by referring creators
    return plan


def plan(acc):
    return {"id": plan_of(acc), **PLANS[plan_of(acc)]}


def is_paid(acc):
    return plan_of(acc) in PAID


def has(acc, feature):
    """Whether the account's plan includes a feature (always true while plan locks are off)."""
    if not LOCKS_ON or feature not in FEATURES:
        return True
    return ORDER.index(plan_of(acc)) >= ORDER.index(FEATURES[feature])


def limit(acc, key):
    """A per-plan number (assistant_day, lead_agent, brand_agent, course_emails, video_gb, team); the top plan's while locks are off."""
    return PLANS["agency" if not LOCKS_ON else plan_of(acc)][key]


def needs(feature):
    """'Pro' for a Pro feature: the plan to show on lock badges and upgrade messages."""
    return PLANS[FEATURES.get(feature, "free")]["name"]


def upgrade_msg(feature):
    return f"{FEATURE_NAMES.get(feature, 'This')} is on the {needs(feature)} plan and up. Upgrade in Plan & billing."


def view(acc):
    """What the dashboard needs to show locks: {feature: True/False}, the limits and each feature's plan."""
    return {"plan": plan_of(acc), "locks": LOCKS_ON, "has": {f: has(acc, f) for f in FEATURES},
            "needs": {f: needs(f) for f in FEATURES}, "limits": {k: limit(acc, k) for k in ("assistant_day", "lead_agent", "brand_agent",
                                                                                           "course_emails", "video_gb", "team")}}


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
