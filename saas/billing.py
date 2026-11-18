"""ReplyInbox plan billing with Razorpay: prepaid monthly or yearly periods, paid in ₹.

1. The dashboard asks for an order (create_order): the amount always comes from plans.PLANS, never from the browser.
2. Razorpay Checkout takes the payment (UPI, cards, netbanking, wallets).
3. The browser sends back the payment id + signature (verify_checkout), and Razorpay also calls our webhook
   (handle_webhook). Both check Razorpay's HMAC signature and activate the order once (idempotent).
4. Activating sets the login's plan and its end date; every Instagram account under the login follows (users.set_plan).
   Paying again for the same plan adds time; switching plans turns the unused days into credit on the new plan.
5. When the period ends, plans.plan_of() falls back to Free. Reminders: banner + phone alert before the end.

Env: RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET (test keys start rzp_test_), RAZORPAY_WEBHOOK_SECRET,
optional BILLING_NAME (who the receipt is from).
"""
import hashlib
import hmac
import json
import os
import secrets
import sys
import time

import requests

import plans
import store
import users

API = "https://api.razorpay.com/v1"
DAYS = {"month": 30, "year": 365}
HISTORY = 50


class BillingError(Exception):
    """A problem to show the person as it is."""


def _env(name, default=""):
    return os.environ.get(name, default).strip().strip("\"'").strip()


def key_id():
    return _env("RAZORPAY_KEY_ID")


def ready():
    return bool(key_id() and _env("RAZORPAY_KEY_SECRET"))


def test_mode():
    return key_id().startswith("rzp_test_")


def price(plan, period):
    if plan not in plans.PAID or period not in DAYS:
        raise BillingError("Pick a plan and monthly or yearly.")
    p = plans.PLANS[plan]
    return p["price"] if period == "month" else p["yearly"]


def _credit_days(user, plan, now):
    """Unused days of the current paid plan, as days of the new plan (same money's worth)."""
    cur, until = user.get("plan"), user.get("plan_until") or 0
    if cur not in plans.PAID or until <= now:
        return 0.0
    left = (until - now) / 86400
    if cur == plan:
        return left
    per_day_old = plans.PLANS[cur]["price"] / 30
    per_day_new = plans.PLANS[plan]["price"] / 30
    return left * per_day_old / per_day_new


def quote(user, plan, period, now=None):
    """What paying now would give: amount in ₹ and the new end date."""
    now = now or time.time()
    days = DAYS[period] + _credit_days(user, plan, now)
    return {"plan": plan, "period": period, "amount": price(plan, period), "until": int(now + days * 86400),
            "credit_days": round(_credit_days(user, plan, now), 1)}


def create_order(user, plan, period):
    """Creates a Razorpay order for this login and plan. Returns what Razorpay Checkout needs."""
    if not ready():
        raise BillingError("Payments aren't switched on yet.")
    amount = price(plan, period)
    receipt = "ri_" + secrets.token_hex(6)
    try:
        r = requests.post(f"{API}/orders", timeout=20, auth=(key_id(), _env("RAZORPAY_KEY_SECRET")), json={
            "amount": amount * 100, "currency": "INR", "receipt": receipt,
            "notes": {"user": user["id"], "plan": plan, "period": period}})
    except requests.RequestException:
        raise BillingError("Razorpay didn't answer. Try again in a minute.")
    data = r.json() if r.content else {}
    if not r.ok or not data.get("id"):
        err = (data.get("error") or {}) if isinstance(data, dict) else {}
        print(f"Razorpay order refused: HTTP {r.status_code} {err.get('code', '')} {err.get('description', '')} "
              f"(key {key_id()[:9]}…)", file=sys.stderr)
        if r.status_code == 401:
            raise BillingError("Payments are misconfigured (Razorpay key). We're on it; please try again later.")
        raise BillingError("Razorpay couldn't start the payment. Try again.")
    order = {"id": data["id"], "user": user["id"], "plan": plan, "period": period, "amount": amount,
             "receipt": receipt, "status": "created", "created": int(time.time())}
    store.set_json(f"s:order:{data['id']}", order)
    return {"key": key_id(), "order_id": data["id"], "amount": amount * 100, "currency": "INR",
            "name": plans.PLANS[plan]["name"], "period": period, "email": user.get("email", ""),
            "test": test_mode()}


def _sign(message, secret):
    return hmac.new(secret.encode(), message.encode() if isinstance(message, str) else message, hashlib.sha256).hexdigest()


def verify_checkout(user, order_id, payment_id, signature):
    """The browser's proof of payment (Razorpay signs order_id|payment_id with our key secret)."""
    order = store.get_json(f"s:order:{order_id}")
    if not order or order["user"] != user["id"]:
        raise BillingError("That payment isn't for this login.")
    expected = _sign(f"{order_id}|{payment_id}", _env("RAZORPAY_KEY_SECRET"))
    if not signature or not hmac.compare_digest(expected, str(signature)):
        raise BillingError("We couldn't confirm the payment. If money was taken, it's activated automatically within minutes.")
    return activate(order_id, payment_id)


def handle_webhook(raw_body, signature):
    """Razorpay's server-to-server notice (payment.captured / order.paid). Returns True when handled."""
    secret = _env("RAZORPAY_WEBHOOK_SECRET")
    if not secret or not signature or not hmac.compare_digest(_sign(raw_body, secret), signature):
        return False
    event = json.loads(raw_body or b"{}")
    if event.get("event") not in ("payment.captured", "order.paid"):
        return True
    pay = ((event.get("payload") or {}).get("payment") or {}).get("entity") or {}
    if pay.get("order_id") and pay.get("status") == "captured":
        try:
            activate(pay["order_id"], pay.get("id", ""), paid_amount=pay.get("amount"))
        except BillingError:
            pass
    return True


def activate(order_id, payment_id, paid_amount=None):
    """Applies a paid order to its login, once. Returns the order."""
    key = f"s:order:{order_id}"
    if not store.redis("SET", f"s:orderlock:{order_id}", "1", "NX", "EX", 60):
        time.sleep(0.5)  # the webhook and the browser can arrive together: let the first one finish
    order = store.get_json(key)
    if not order:
        raise BillingError("Unknown order.")
    if order["status"] == "paid":
        return order
    if paid_amount is not None and int(paid_amount) != order["amount"] * 100:
        raise BillingError("The amount paid doesn't match the plan price.")
    user = users.get(order["user"])
    if not user:
        raise BillingError("That login no longer exists.")
    now = time.time()
    q = quote(user, order["plan"], order["period"], now)
    users.set_plan(user, order["plan"], q["until"])
    order.update(status="paid", payment_id=payment_id, paid_at=int(now), until=q["until"], credit_days=q["credit_days"])
    store.set_json(key, order)
    user = users.get(order["user"])
    hist = user.setdefault("payments", [])
    hist.insert(0, {k: order[k] for k in ("id", "plan", "period", "amount", "paid_at", "until", "payment_id", "receipt")})
    del hist[HISTORY:]
    users.save(user)
    store.redis("LPUSH", "s:payments", json.dumps({"user": user["id"], "email": user.get("email", ""), **hist[0]}))
    store.redis("LTRIM", "s:payments", 0, 999)
    return order


def status(user):
    """For the Billing page and banners."""
    now = time.time()
    until = user.get("plan_until") or 0
    plan = users.current_plan(user)
    days_left = max(0, int((until - now) // 86400)) if until else None
    return {"plan": plan, "plan_name": plans.PLANS[plan]["name"], "set_plan": user.get("plan") or "free",
            "until": until or None, "days_left": days_left, "expired": bool(until) and until < now and user.get("plan") != "free",
            "manual": user.get("plan") in plans.PAID and not until, "payments": user.get("payments", [])[:20],
            "ready": ready(), "test": test_mode(),
            "plans": {k: {"name": v["name"], "month": v["price"], "year": v["yearly"], "accounts": v["accounts"],
                          "ai_replies": v["ai_replies"], "monthly_dms": v["monthly_dms"]} for k, v in plans.PLANS.items() if k in plans.PAID}}


def receipt(user, order_id):
    order = store.get_json(f"s:order:{order_id}")
    if not order or order["user"] != user["id"] or order["status"] != "paid":
        return None
    return {**order, "plan_name": plans.PLANS[order["plan"]]["name"], "from": _env("BILLING_NAME", "ReplyInbox"),
            "email": user.get("email", "")}


def renewal_due(user, within_days=3):
    """True when a paid period ends within `within_days` (for reminders)."""
    until = user.get("plan_until") or 0
    return user.get("plan") in plans.PAID and until and 0 < until - time.time() <= within_days * 86400
