"""Digital products: creators sell files (PDFs, packs) and get paid straight to their bank, like SuperProfile.

Money flow (Razorpay Route): the buyer pays ReplyInbox's Razorpay account; each order carries a transfer of the
creator's share to the creator's Route "linked account", which Razorpay settles to the creator's bank. ReplyInbox keeps
its plan fee (plans.platform_fee). Route must be enabled on the Razorpay account (Dashboard → Route).

1. Payouts (once per login): onboard() creates the linked account (v2 Accounts API, type "route"), a stakeholder,
   the Route product configuration and its settlement bank details. Razorpay checks them (activation_status).
   Only the last 4 digits of the bank account are stored here.
2. Products (per Instagram account): title, price, description, optional cover image, and a private file (uploaded
   through files.py with paid=True, so /f/<id>/<name> never serves it).
3. Buying: /<username>/p/<id> → create_order() (amount from the product, never from the browser) → Razorpay Checkout →
   verify_checkout() or the webhook → fulfil() once: a download link /d/<token> (30 days, 20 downloads), an email to the
   buyer, the sale in the creator's Sales.
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import time

import requests

import plans
import store
import users

API = "https://api.razorpay.com"
MAX_PRODUCTS = 50
DL_DAYS, DL_MAX = 30, 20
PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)


class ShopError(Exception):
    """A problem to show the person as it is."""


def _env(name, default=""):
    return os.environ.get(name, default).strip().strip("\"'").strip()


def ready():
    return bool(_env("RAZORPAY_KEY_ID") and _env("RAZORPAY_KEY_SECRET"))


def _rzp(method, path, body=None):
    try:
        r = requests.request(method, API + path, json=body, timeout=25, auth=(_env("RAZORPAY_KEY_ID"), _env("RAZORPAY_KEY_SECRET")))
    except requests.RequestException:
        raise ShopError("Razorpay didn't answer. Try again in a minute.")
    data = r.json() if r.content else {}
    if not r.ok:
        err = (data.get("error") or {}) if isinstance(data, dict) else {}
        desc = err.get("description") or f"HTTP {r.status_code}"
        print(f"Razorpay {method} {path} refused: {r.status_code} {err.get('code', '')} {desc}")
        if "route" in desc.lower() and ("not enabled" in desc.lower() or "not activated" in desc.lower()):
            raise ShopError("Payouts aren't switched on for ReplyInbox yet. Please try again in a few days.")
        raise ShopError(f"Razorpay: {desc}")
    return data


# ---------- payouts: the creator's Route linked account ----------

def payout(user):
    return (user or {}).get("payout") or {}


def can_sell(user):
    return payout(user).get("status") == "activated"


def onboard(user, data):
    """Creates (or finishes) the creator's linked account with their bank details. Returns the payout record."""
    if not ready():
        raise ShopError("Payments aren't switched on yet.")
    d = {k: str(data.get(k, "")).strip() for k in ("name", "email", "phone", "pan", "account_number", "ifsc", "street",
                                                   "city", "state", "pincode")}
    d["pan"], d["ifsc"] = d["pan"].upper(), d["ifsc"].upper()
    d["phone"] = re.sub(r"\D", "", d["phone"])[-10:]
    d["account_number"] = re.sub(r"\s", "", d["account_number"])
    if len(d["name"]) < 3:
        raise ShopError("Enter the account holder's full name (as on the bank account).")
    if not EMAIL_RE.match(d["email"]):
        raise ShopError("Enter a valid email.")
    if len(d["phone"]) != 10:
        raise ShopError("Enter a 10-digit mobile number.")
    if not PAN_RE.match(d["pan"]):
        raise ShopError("Enter a valid PAN (like ABCDE1234F).")
    if not re.fullmatch(r"\d{9,18}", d["account_number"]):
        raise ShopError("Enter a valid bank account number.")
    if not IFSC_RE.match(d["ifsc"]):
        raise ShopError("Enter a valid IFSC code (like HDFC0001234).")
    if not (d["street"] and d["city"] and d["state"] and re.fullmatch(r"\d{6}", d["pincode"])):
        raise ShopError("Enter your full address with a 6-digit PIN code.")
    p = payout(user)
    if not p.get("account_id"):
        acc = _rzp("POST", "/v2/accounts", {
            "email": d["email"], "phone": d["phone"], "type": "route", "reference_id": user["id"][:20],
            "legal_business_name": d["name"], "business_type": "individual", "contact_name": d["name"],
            "profile": {"category": "education", "subcategory": "elearning", "addresses": {"registered": {
                "street1": d["street"][:100], "street2": d["city"][:100], "city": d["city"], "state": d["state"],
                "postal_code": d["pincode"], "country": "IN"}}},
            "legal_info": {"pan": d["pan"]}})
        p = {"account_id": acc["id"]}
        _rzp("POST", f"/v2/accounts/{acc['id']}/stakeholders", {"name": d["name"], "email": d["email"]})
    if not p.get("product_id"):
        prod = _rzp("POST", f"/v2/accounts/{p['account_id']}/products", {"product_name": "route", "tnc_accepted": True})
        p["product_id"] = prod["id"]
    conf = _rzp("PATCH", f"/v2/accounts/{p['account_id']}/products/{p['product_id']}", {
        "settlements": {"account_number": d["account_number"], "ifsc_code": d["ifsc"], "beneficiary_name": d["name"]},
        "tnc_accepted": True})
    p.update(name=d["name"], email=d["email"], bank=f"•••• {d['account_number'][-4:]}", ifsc=d["ifsc"],
             status=conf.get("activation_status") or "under_review", requirements=_reqs(conf), at=int(time.time()))
    user["payout"] = p
    users.save(user)
    return p


def _reqs(conf):
    return [str(r.get("reason_code") or r.get("field_reference") or r)[:80] for r in (conf.get("requirements") or [])][:5]


def refresh(user):
    """Asks Razorpay for the latest activation status (when it isn't activated yet)."""
    p = payout(user)
    if not p.get("product_id") or p.get("status") == "activated" or not ready():
        return p
    try:
        conf = _rzp("GET", f"/v2/accounts/{p['account_id']}/products/{p['product_id']}")
    except ShopError:
        return p
    p.update(status=conf.get("activation_status") or p.get("status"), requirements=_reqs(conf))
    user["payout"] = p
    users.save(user)
    return p


# ---------- products ----------

def _key(acc_id):
    return store.account_key(acc_id, "shop")


def products(acc_id):
    return store.get_json(_key(acc_id), [])


def get(acc_id, pid):
    return next((p for p in products(acc_id) if p["id"] == pid), None)


def save_product(acc, data):
    items = products(acc["id"])
    pid = str(data.get("id") or "")
    cur = next((p for p in items if p["id"] == pid), None)
    title = str(data.get("title", "")).strip()[:100]
    try:
        price = int(float(str(data.get("price", "")).replace("₹", "").replace(",", "").strip()))
    except ValueError:
        price = 0
    if not title:
        raise ShopError("Give the product a title.")
    if not 10 <= price <= 100000:
        raise ShopError("Price must be between ₹10 and ₹1,00,000.")
    cover = str(data.get("cover", "")).strip()
    p = {**(cur or {"id": secrets.token_hex(5), "created": int(time.time()), "sales": 0, "revenue": 0}),
         "title": title, "price": price, "desc": str(data.get("desc", "")).strip()[:2000],
         "cover": cover if cover.startswith("https://") else "", "enabled": data.get("enabled", True) is not False,
         "file_id": str(data.get("file_id") or (cur or {}).get("file_id") or ""),
         "file_name": str(data.get("file_name") or (cur or {}).get("file_name") or "")[:100]}
    if not p["file_id"]:
        raise ShopError("Upload the file buyers get.")
    if not cur and len(items) >= MAX_PRODUCTS:
        raise ShopError(f"You can have up to {MAX_PRODUCTS} products.")
    items = [p if x["id"] == p["id"] else x for x in items] if cur else [p] + items
    store.set_json(_key(acc["id"]), items)
    return p


def delete_product(acc, pid):
    items = products(acc["id"])
    store.set_json(_key(acc["id"]), [p for p in items if p["id"] != pid])
    return len(items) != len(products(acc["id"]))


# ---------- buying ----------

def split(acc, price):
    """₹ the creator gets and our cut, for a sale of `price` ₹ on this account's plan."""
    f = plans.platform_fee(acc, price)
    return {"creator": max(0, f["creator_gets"]), "fee": f["total_fee"]}


def create_order(acc, prod, buyer):
    owner = users.owner_of(acc)
    if not ready() or not owner or not can_sell(owner):
        raise ShopError("This product can't be bought right now. Please try again later.")
    if not prod.get("enabled", True):
        raise ShopError("This product isn't for sale right now.")
    email = str(buyer.get("email", "")).strip().lower()[:200]
    if not EMAIL_RE.match(email):
        raise ShopError("Enter your email: the download link is sent there.")
    s = split(acc, prod["price"])
    receipt = "rs_" + secrets.token_hex(6)
    order = _rzp("POST", "/v1/orders", {
        "amount": prod["price"] * 100, "currency": "INR", "receipt": receipt,
        "notes": {"kind": "shop", "account": acc["id"], "product": prod["id"]},
        "transfers": [{"account": payout(owner)["account_id"], "amount": int(round(s["creator"] * 100)), "currency": "INR",
                       "notes": {"product": prod["title"][:60], "buyer": email[:60]},
                       "linked_account_notes": ["product"], "on_hold": 0}]})
    rec = {"id": order["id"], "acc": acc["id"], "product": prod["id"], "title": prod["title"], "price": prod["price"],
           "creator_gets": s["creator"], "fee": s["fee"], "email": email, "name": str(buyer.get("name", "")).strip()[:80],
           "status": "created", "created": int(time.time())}
    store.set_json(f"s:shoporder:{order['id']}", rec)
    return {"key": _env("RAZORPAY_KEY_ID"), "order_id": order["id"], "amount": prod["price"] * 100, "currency": "INR",
            "name": prod["title"], "email": email}


def _sign(message, secret):
    return hmac.new(secret.encode(), message.encode() if isinstance(message, str) else message, hashlib.sha256).hexdigest()


def is_shop_order(order_id):
    return bool(order_id and store.get_json(f"s:shoporder:{order_id}"))


def verify_checkout(order_id, payment_id, signature):
    expected = _sign(f"{order_id}|{payment_id}", _env("RAZORPAY_KEY_SECRET"))
    if not signature or not hmac.compare_digest(expected, str(signature)):
        raise ShopError("We couldn't confirm the payment. If money was taken, the download link reaches your email within minutes.")
    return fulfil(order_id, payment_id)


def fulfil(order_id, payment_id, paid_amount=None):
    """Delivers a paid order once: download token, buyer email, the creator's sale. Returns the order."""
    key = f"s:shoporder:{order_id}"
    if not store.redis("SET", f"s:shoplock:{order_id}", "1", "NX", "EX", 60):
        time.sleep(0.5)
    o = store.get_json(key)
    if not o:
        raise ShopError("Unknown order.")
    if o["status"] == "paid":
        return o
    if paid_amount is not None and int(paid_amount) != o["price"] * 100:
        raise ShopError("The amount paid doesn't match the price.")
    token = secrets.token_urlsafe(16)
    prod = get(o["acc"], o["product"]) or {}
    store.set_json(f"s:dl:{token}", {"order": order_id, "acc": o["acc"], "product": o["product"], "n": 0, "title": o["title"],
                                     "file_id": prod.get("file_id", ""), "until": int(time.time() + DL_DAYS * 86400)})
    o.update(status="paid", payment_id=payment_id, paid_at=int(time.time()), token=token)
    store.set_json(key, o)
    items = products(o["acc"])
    for p in items:
        if p["id"] == o["product"]:
            p["sales"] = int(p.get("sales") or 0) + 1
            p["revenue"] = int(p.get("revenue") or 0) + o["price"]
    store.set_json(_key(o["acc"]), items)
    sales = store.account_key(o["acc"], "shopsales")
    store.redis("LPUSH", sales, json.dumps({k: o[k] for k in ("id", "title", "price", "creator_gets", "email", "paid_at")}))
    store.redis("LTRIM", sales, 0, 499)
    store.count(o["acc"], "sales")
    store.count(o["acc"], "revenue", o["price"])
    store.log_activity(o["acc"], "", "", o["title"], "sale", "ok", f"₹{o['price']} · digital product")
    acc = store.load_account(o["acc"]) or {}
    try:
        import push
        if (acc.get("notify") or {}).get("sale", True):
            push.notify(acc, f"New sale 💰 ₹{o['price']:,}", o["title"], "/app/products")
    except Exception:
        pass
    send_download_email(o, acc)
    return o


def sales(acc_id, n=100):
    return [json.loads(x) for x in store.redis("LRANGE", store.account_key(acc_id, "shopsales"), 0, n - 1) or []]


# ---------- delivery ----------

def download(token):
    """The download record for a valid token, or None."""
    d = store.get_json(f"s:dl:{token}") if token and re.fullmatch(r"[A-Za-z0-9_-]{10,40}", token) else None
    if not d or d["until"] < time.time():
        return None
    return d


def count_download(token):
    d = download(token)
    if not d or d["n"] >= DL_MAX:
        return False
    d["n"] += 1
    store.set_json(f"s:dl:{token}", d)
    return True


def send_download_email(o, acc):
    key = _env("RESEND_API_KEY")
    site = (_env("SITE_URL") or _env("PUBLIC_URL") or "https://replyinbox.in").rstrip("/")
    link = f"{site}/d/{o['token']}"
    if not key:
        print(f"[dev] download link for {o['email']}: {link}")
        return
    brand = _env("BRAND_NAME", "ReplyInbox")
    by = f"@{acc.get('username')}" if acc.get("username") else "the creator"
    html = (f"<div style=\"font-family:system-ui,sans-serif;max-width:460px;margin:auto;padding:24px;color:#111318\">"
            f"<h2 style=\"margin:0 0 8px\">Your download is ready 🎉</h2>"
            f"<p>Thanks for buying <b>{_esc(o['title'])}</b> from {by}.</p>"
            f"<p><a href=\"{link}\" style=\"display:inline-block;background:#2E3BFF;color:#fff;text-decoration:none;font-weight:800;"
            f"border-radius:999px;padding:12px 22px\">Download</a></p>"
            f"<p style=\"color:#5E6068;font-size:13px\">The link works for {DL_DAYS} days. Paid ₹{o['price']:,} · order {o['id']}.</p></div>")
    try:
        requests.post("https://api.resend.com/emails", timeout=15, headers={"Authorization": f"Bearer {key}"},
                      json={"from": _env("MAIL_FROM", f"{brand} <no-reply@replyinbox.in>"), "to": [o["email"]],
                            "subject": f"Your download: {o['title']}", "html": html,
                            "text": f"Thanks for buying {o['title']} from {by}. Download: {link} (works {DL_DAYS} days)",
                            **({"reply_to": _env("SUPPORT_EMAIL") or _env("CONTACT_EMAIL")} if (_env("SUPPORT_EMAIL") or _env("CONTACT_EMAIL")) else {})})
    except requests.RequestException:
        pass


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
