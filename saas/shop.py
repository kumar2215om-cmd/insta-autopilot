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


TYPES = ("file", "locked", "event", "booking")


def duplicate(acc, pid):
    """A hidden copy of a product (same file, price and settings; no sales) to edit and switch on."""
    items = products(acc["id"])
    p = next((x for x in items if x["id"] == pid), None)
    if not p:
        raise ShopError("Product not found.")
    if len(items) >= MAX_PRODUCTS:
        raise ShopError(f"You can have up to {MAX_PRODUCTS} products.")
    copy = {**p, "id": secrets.token_hex(5), "title": (p["title"] + " (copy)")[:100], "created": int(time.time()),
            "sales": 0, "revenue": 0, "enabled": False}
    items.insert(items.index(p) + 1, copy)
    store.set_json(_key(acc["id"]), items)
    return copy
IST = 19800  # India Standard Time, UTC+5:30: creators set times in IST
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _https(v):
    v = str(v or "").strip()
    return v if v.startswith("https://") else ""


def _int(v, lo, hi, default):
    try:
        n = int(float(str(v).strip()))
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def _hhmm(v):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", str(v or "").strip())
    return int(m.group(1)) * 60 + int(m.group(2)) if m and int(m.group(1)) < 24 and int(m.group(2)) < 60 else None


def parse_local(v):
    """'2026-12-05T19:30' in IST → epoch seconds, or None."""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})", str(v or "").strip())
    if not m:
        return None
    import calendar
    y, mo, d, h, mi = map(int, m.groups())
    try:
        return calendar.timegm((y, mo, d, h, mi, 0)) - IST
    except (ValueError, OverflowError):
        return None


def when_text(ts, minutes=0):
    t = time.gmtime(ts + IST)
    s = time.strftime("%a %d %b %Y, %I:%M %p", t).replace(" 0", " ")
    return s + (f" ({minutes} min)" if minutes else "") + " IST"


def save_product(acc, data):
    items = products(acc["id"])
    pid = str(data.get("id") or "")
    cur = next((p for p in items if p["id"] == pid), None)
    kind = data.get("type") if data.get("type") in TYPES else (cur or {}).get("type", "file")
    title = str(data.get("title", "")).strip()[:100]
    try:
        price = int(float(str(data.get("price", "")).replace("₹", "").replace(",", "").strip()))
    except ValueError:
        price = 0
    if not title:
        raise ShopError("Give the product a title.")
    if not 10 <= price <= 100000:
        raise ShopError("Price must be between ₹10 and ₹1,00,000.")
    p = {**(cur or {"id": secrets.token_hex(5), "created": int(time.time()), "sales": 0, "revenue": 0}),
         "type": kind, "title": title, "price": price, "desc": str(data.get("desc", "")).strip()[:2000],
         "cover": _https(data.get("cover")), "enabled": data.get("enabled", True) is not False,
         "file_id": str(data.get("file_id") or (cur or {}).get("file_id") or ""),
         "file_name": str(data.get("file_name") or (cur or {}).get("file_name") or "")[:100]}
    if data.get("remove_file"):
        p["file_id"] = p["file_name"] = ""
    if kind == "file" and not p["file_id"]:
        raise ShopError("Upload the file buyers get.")
    if kind == "locked":
        p["content"] = str(data.get("content", "")).strip()[:5000]
        if not p["content"] and not p["file_id"]:
            raise ShopError("Add the content buyers unlock (text or links), or a file.")
    if kind == "event":
        start = parse_local(data.get("start"))
        if not start:
            raise ShopError("Pick the event date and time.")
        if not cur and start < time.time():
            raise ShopError("The event date is in the past.")
        p.update(start=start, minutes=_int(data.get("minutes"), 10, 600, 60), capacity=_int(data.get("capacity"), 0, 100000, 0),
                 join_url=_https(data.get("join_url")))
    if kind == "booking":
        frm, to = _hhmm(data.get("from")), _hhmm(data.get("to"))
        days = sorted({int(d) for d in data.get("days") or [] if str(d).isdigit() and int(d) < 7})
        minutes = _int(data.get("minutes"), 10, 240, 30)
        if frm is None or to is None or to - frm < minutes:
            raise ShopError("Set your hours (e.g. 18:00 to 21:00), long enough for one session.")
        if not days:
            raise ShopError("Pick at least one day of the week.")
        p.update(minutes=minutes, days=days, frm=frm, to=to, ahead=_int(data.get("ahead"), 1, 60, 14),
                 notice=_int(data.get("notice"), 0, 72, 3), join_url=_https(data.get("join_url")))
    if not cur and len(items) >= MAX_PRODUCTS:
        raise ShopError(f"You can have up to {MAX_PRODUCTS} products.")
    items = [p if x["id"] == p["id"] else x for x in items] if cur else [p] + items
    store.set_json(_key(acc["id"]), items)
    return p


# ---------- events and bookings ----------

def seats_left(p):
    return None if not p.get("capacity") else max(0, p["capacity"] - int(p.get("sales") or 0))


def _booked_key(acc_id, pid):
    return store.account_key(acc_id, f"booked:{pid}")


def slots(acc_id, p, now=None):
    """Free start times (epoch) for a booking product, in the next `ahead` days."""
    now = now or time.time()
    booked = set(store.redis("SMEMBERS", _booked_key(acc_id, p["id"])) or [])
    out = []
    day0 = int((now + IST) // 86400) * 86400 - IST  # today 00:00 IST
    for d in range(p.get("ahead", 14) + 1):
        base = day0 + d * 86400
        if time.gmtime(base + IST).tm_wday not in p.get("days", []):
            continue
        t = p["frm"]
        while t + p["minutes"] <= p["to"]:
            ts = base + t * 60
            if ts >= now + p.get("notice", 3) * 3600 and str(ts) not in booked and not store.redis("GET", f"s:slothold:{p['id']}:{ts}"):
                out.append(ts)
            t += p["minutes"]
    return out[:400]


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
        raise ShopError("Enter your email: your access link is sent there.")
    name = str(buyer.get("name", "")).strip()[:80]
    kind, slot = prod.get("type", "file"), None
    if kind == "event":
        if prod["start"] + prod.get("minutes", 60) * 60 < time.time():
            raise ShopError("This event is over.")
        if seats_left(prod) == 0:
            raise ShopError("Sold out.")
    if kind == "booking":
        if not name:
            raise ShopError("Enter your name for the booking.")
        try:
            slot = int(buyer.get("slot"))
        except (TypeError, ValueError):
            slot = 0
        if slot not in slots(acc["id"], prod):
            raise ShopError("That time was just taken. Pick another slot.")
    s = split(acc, prod["price"])
    receipt = "rs_" + secrets.token_hex(6)
    order = _rzp("POST", "/v1/orders", {
        "amount": prod["price"] * 100, "currency": "INR", "receipt": receipt,
        "notes": {"kind": "shop", "account": acc["id"], "product": prod["id"]},
        "transfers": [{"account": payout(owner)["account_id"], "amount": int(round(s["creator"] * 100)), "currency": "INR",
                       "notes": {"product": prod["title"][:60], "buyer": email[:60]},
                       "linked_account_notes": ["product"], "on_hold": 0}]})
    rec = {"id": order["id"], "acc": acc["id"], "product": prod["id"], "title": prod["title"], "price": prod["price"],
           "creator_gets": s["creator"], "fee": s["fee"], "email": email, "name": name, "type": kind,
           "status": "created", "created": int(time.time())}
    if kind == "event":
        rec.update(when=prod["start"], minutes=prod.get("minutes", 60))
    if slot:
        rec.update(when=slot, minutes=prod["minutes"])
        store.redis("SET", f"s:slothold:{prod['id']}:{slot}", order["id"], "EX", 900)  # held 15 min while they pay
    store.set_json(f"s:shoporder:{order['id']}", rec)
    track_cart(acc["id"], order["id"])
    return {"key": _env("RAZORPAY_KEY_ID"), "order_id": order["id"], "amount": prod["price"] * 100, "currency": "INR",
            "name": prod["title"], "email": email}


def transfer_payment(o, payment_id):
    """Sends the creator's share of a dollar payment (Route transfers are in rupees, so they happen after capture)."""
    key = f"s:shoporder:{o['id']}"
    try:
        acc = store.load_account(o["acc"]) or {"id": o["acc"]}
        owner = users.owner_of(acc)
        p = _rzp("GET", f"/v1/payments/{payment_id}")
        inr = p.get("base_amount") if p.get("base_currency", "INR") == "INR" and p.get("base_amount") else o["price"] * 100
        f = plans.platform_fee(acc, inr / 100, gateway_fee=(p.get("fee") or 0) / 100 if p.get("fee") else None)
        amount = int(round(max(0, f["creator_gets"]) * 100))
        _rzp("POST", f"/v1/payments/{payment_id}/transfers", {"transfers": [{
            "account": payout(owner)["account_id"], "amount": amount, "currency": "INR",
            "notes": {"course": o["title"][:60], "buyer": o["email"][:60]}, "on_hold": 0}]})
        o.update(transfer="done", price=int(inr // 100), creator_gets=f["creator_gets"], fee=f["total_fee"])
    except Exception as e:
        print(f"transfer for {o['id']} failed: {e}")
        o["transfer"] = "pending"
    store.set_json(key, o)
    return o


def track_cart(acc_id, order_id):
    """Every checkout is remembered for Leads → Abandoned carts (leads.py)."""
    key = store.account_key(acc_id, "carts")
    store.redis("LPUSH", key, order_id)
    store.redis("LTRIM", key, 0, 499)


SETTLED = "completed"


def transfer_status(o):
    """Where the creator's share of a paid order is: completed (in their bank), processing, on_hold or failed.
    Asks Razorpay at most every 30 minutes per order; a completed answer is kept on the order."""
    if o.get("payout_status") == SETTLED or not o.get("payment_id") or str(o.get("id", "")).startswith("free_"):
        return o.get("payout_status") or (SETTLED if o.get("payment_id") else "")
    cache = f"s:trcache:{o['id']}"
    hit = store.redis("GET", cache)
    if hit:
        return hit
    status = "processing"
    try:
        items = (_rzp("GET", f"/v1/payments/{o['payment_id']}/transfers") or {}).get("items") or []
        t = items[0] if items else {}
        if t.get("status") in ("failed", "reversed"):
            status = "failed"
        elif t.get("settlement_status") == "settled" or t.get("recipient_settlement_id"):
            status = SETTLED
        elif t.get("on_hold") or t.get("settlement_status") == "on_hold":
            status = "on_hold"
    except ShopError:
        pass
    if status == SETTLED:
        o["payout_status"] = SETTLED
        store.set_json(f"s:shoporder:{o['id']}", o)
    store.redis("SET", cache, status, "EX", 1800)
    return status


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
        if o.get("transfer") == "pending":  # a dollar payment whose transfer failed before capture: try again
            transfer_payment(o, payment_id or o.get("payment_id", ""))
        return o
    if paid_amount is not None and int(paid_amount) != o.get("amount_minor", o["price"] * 100):
        raise ShopError("The amount paid doesn't match the price.")
    if o.get("type") == "course":  # a course purchase (see courses.py)
        import courses
        o.update(status="paid", payment_id=payment_id, paid_at=int(time.time()))
        store.set_json(key, o)
        if o.get("currency") == "USD":
            transfer_payment(o, payment_id)
        courses.enroll(o)
        sales = store.account_key(o["acc"], "shopsales")
        store.redis("LPUSH", sales, json.dumps({**{k: o[k] for k in ("id", "title", "creator_gets", "email", "paid_at")},
                                                "price": o.get("course_price", o["price"]), "name": o.get("name", ""), "type": "course",
                                                "phone": o.get("phone", ""), "currency": o.get("currency", "INR")}))
        store.redis("LTRIM", sales, 0, 499)
        b = o.get("bump")
        if b:  # the bump offer ticked at checkout
            try:
                if b["kind"] == "course":
                    courses.enroll({**o, "id": o["id"] + "_b", "course": b["id"], "price": b["price"], "course_price": b["price"],
                                    "coupon": None, "bump": None})
                else:
                    store.set_json(f"s:shoporder:{o['id']}_b", {
                        "id": o["id"] + "_b", "acc": o["acc"], "product": b["id"], "title": b["title"], "price": b["price"],
                        "creator_gets": split(store.load_account(o["acc"]) or {"id": o["acc"]}, b["price"])["creator"], "fee": 0,
                        "email": o["email"], "name": o.get("name", ""), "type": (get(o["acc"], b["id"]) or {}).get("type", "file"),
                        "status": "created", "created": int(time.time())})
                    fulfil(o["id"] + "_b", payment_id)
            except Exception as e:
                print(f"bump delivery failed for {o['id']}: {e}")
        return o
    token = secrets.token_urlsafe(16)
    prod = get(o["acc"], o["product"]) or {}
    until = time.time() + DL_DAYS * 86400
    if o.get("when"):  # events and bookings: the page stays open until a week after it happened
        until = max(until, o["when"] + 7 * 86400)
    store.set_json(f"s:dl:{token}", {"order": order_id, "acc": o["acc"], "product": o["product"], "n": 0, "title": o["title"],
                                     "type": o.get("type", "file"), "file_id": prod.get("file_id", ""), "content": prod.get("content", ""),
                                     "when": o.get("when"), "minutes": o.get("minutes"), "join_url": prod.get("join_url", ""),
                                     "name": o.get("name", ""), "until": int(until)})
    if o.get("type") == "booking" and o.get("when"):
        store.redis("SADD", _booked_key(o["acc"], o["product"]), str(o["when"]))
    if o.get("when"):
        up = store.get_json("s:shopupcoming", [])
        up = [x for x in up if x["when"] > time.time() - 86400] + [{"order": order_id, "when": o["when"]}]
        store.set_json("s:shopupcoming", up[-2000:])
    o.update(status="paid", payment_id=payment_id, paid_at=int(time.time()), token=token)
    store.set_json(key, o)
    items = products(o["acc"])
    for p in items:
        if p["id"] == o["product"]:
            p["sales"] = int(p.get("sales") or 0) + 1
            p["revenue"] = int(p.get("revenue") or 0) + o["price"]
    store.set_json(_key(o["acc"]), items)
    sales = store.account_key(o["acc"], "shopsales")
    store.redis("LPUSH", sales, json.dumps({**{k: o[k] for k in ("id", "title", "price", "creator_gets", "email", "paid_at")},
                                            "name": o.get("name", ""), "type": o.get("type", "file"), "when": o.get("when")}))
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
    if o.get("type") == "booking":
        owner = users.owner_of(acc)
        if owner and owner.get("email"):
            _mail(owner["email"], f"New booking: {o.get('name') or o['email']} · {when_text(o['when'])}",
                  f"<p><b>{_esc(o.get('name') or '')}</b> ({_esc(o['email'])}) booked <b>{_esc(o['title'])}</b> for "
                  f"<b>{when_text(o['when'], o.get('minutes') or 0)}</b> and paid ₹{o['price']:,}.</p>"
                  f"<p>Reply to this email to reach them, or write to {_esc(o['email'])}.</p>", reply_to=o["email"])
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


def _site():
    return (_env("SITE_URL") or _env("PUBLIC_URL") or "https://replyinbox.in").rstrip("/")


def _mail(to, subject, html, reply_to=None):
    key = _env("RESEND_API_KEY")
    if not key:
        print(f"[dev] email to {to}: {subject}")
        return False
    brand = _env("BRAND_NAME", "ReplyInbox")
    rt = reply_to or _env("SUPPORT_EMAIL") or _env("CONTACT_EMAIL")
    body = (f"<div style=\"font-family:system-ui,sans-serif;max-width:480px;margin:auto;padding:24px;color:#111318\">{html}"
            f"<p style=\"color:#5E6068;font-size:12px;margin-top:22px\">Sent by {brand} on behalf of the creator.</p></div>")
    try:
        requests.post("https://api.resend.com/emails", timeout=15, headers={"Authorization": f"Bearer {key}"},
                      json={"from": _env("MAIL_FROM", f"{brand} <no-reply@replyinbox.in>"), "to": [to], "subject": subject,
                            "html": body, **({"reply_to": rt} if rt else {})})
        return True
    except requests.RequestException:
        return False


def _button(link, label):
    return (f"<p><a href=\"{link}\" style=\"display:inline-block;background:#2E3BFF;color:#fff;text-decoration:none;font-weight:800;"
            f"border-radius:999px;padding:12px 22px\">{label}</a></p>")


def send_download_email(o, acc):
    link = f"{_site()}/d/{o['token']}"
    by = f"@{acc.get('username')}" if acc.get("username") else "the creator"
    kind = o.get("type", "file")
    if kind in ("event", "booking"):
        what = "Your booking is confirmed ✅" if kind == "booking" else "You're in! 🎟"
        html = (f"<h2 style=\"margin:0 0 8px\">{what}</h2><p><b>{_esc(o['title'])}</b> with {by}</p>"
                f"<p style=\"font-size:18px;font-weight:800\">{when_text(o['when'], o.get('minutes') or 0)}</p>"
                + _button(link, "See details and join link") +
                f"<p style=\"color:#5E6068;font-size:13px\">We'll remind you on the day. Paid ₹{o['price']:,} · order {o['id']}.</p>")
        _mail(o["email"], f"{'Booked' if kind == 'booking' else 'Your ticket'}: {o['title']} · {when_text(o['when'])}", html,
              reply_to=None)
        return
    label = "Open your content" if kind == "locked" else "Download"
    html = (f"<h2 style=\"margin:0 0 8px\">{'Unlocked' if kind == 'locked' else 'Your download is ready'} 🎉</h2>"
            f"<p>Thanks for buying <b>{_esc(o['title'])}</b> from {by}.</p>" + _button(link, label) +
            f"<p style=\"color:#5E6068;font-size:13px\">The link works for {DL_DAYS} days. Paid ₹{o['price']:,} · order {o['id']}.</p>")
    _mail(o["email"], f"{'Unlocked' if kind == 'locked' else 'Your download'}: {o['title']}", html)


def send_reminders(now=None):
    """Events and bookings starting in the next 24 hours get one reminder email (run daily by the cron)."""
    now = now or time.time()
    up, keep, sent = store.get_json("s:shopupcoming", []), [], 0
    for x in up:
        if x["when"] < now:
            continue
        if x["when"] > now + 86400:
            keep.append(x)
            continue
        o = store.get_json(f"s:shoporder:{x['order']}")
        if o and o.get("status") == "paid" and not o.get("reminded"):
            link = f"{_site()}/d/{o['token']}"
            _mail(o["email"], f"Today: {o['title']} · {when_text(o['when'])}",
                  f"<h2 style=\"margin:0 0 8px\">Reminder ⏰</h2><p><b>{_esc(o['title'])}</b> is coming up:</p>"
                  f"<p style=\"font-size:18px;font-weight:800\">{when_text(o['when'], o.get('minutes') or 0)}</p>" + _button(link, "Join details"))
            o["reminded"] = int(now)
            store.set_json(f"s:shoporder:{x['order']}", o)
            sent += 1
    store.set_json("s:shopupcoming", keep)
    return sent


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
