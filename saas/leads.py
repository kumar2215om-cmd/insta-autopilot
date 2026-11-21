"""Leads (like SuperProfile → Leads): everyone in one list, with automatic segments.

People come from: Instagram contacts (comments, DMs, follow gate, link-page signups), buyers (Store and Courses sales),
course students, and abandoned checkouts (an order created but never paid). They're merged by email; Instagram-only
contacts stay keyed by their handle.

Abandoned carts: every checkout adds its order id to s:t:<acc>:carts (shop.create_order / courses.order). An order still
unpaid after CART_AFTER seconds, whose buyer hasn't bought that item since, is an abandoned cart.
"""
import json
import time

import courses
import shop
import store

CART_AFTER = 30 * 60
CART_DAYS = 30
SEGMENTS = ("all", "customers", "instagram", "followers", "subscribers", "carts")


def _order(oid):
    return store.get_json(f"s:shoporder:{oid}")


def carts(acc_id, now=None, paid_keys=None):
    """Abandoned checkouts of the last CART_DAYS days, newest first (one per buyer and item)."""
    now = now or time.time()
    if paid_keys is None:
        paid_keys = {(s.get("email", ""), s.get("title", "")) for s in shop.sales(acc_id, 500)}
    out, seen = [], set()
    for oid in store.redis("LRANGE", store.account_key(acc_id, "carts"), 0, 499) or []:
        o = _order(oid)
        if not o or o.get("status") == "paid" or o.get("acc") != acc_id:
            continue
        at = o.get("created", 0)
        if not now - CART_DAYS * 86400 < at < now - CART_AFTER:
            continue
        k = (o.get("email", ""), o.get("title", ""))
        if k in paid_keys or k in seen:
            continue
        seen.add(k)
        out.append({"id": o["id"], "email": o.get("email", ""), "name": o.get("name", ""), "phone": o.get("phone", ""),
                    "title": o.get("title", ""), "type": o.get("type", "file"), "price": o.get("price", 0), "at": at,
                    "course": o.get("course", ""), "product": o.get("product", ""), "reminded": o.get("reminded")})
    return out


def people(acc):
    """All leads for an account, merged. Each: key, name, email, phone, username, followed, sources, items (bought),
    spent, students (course access), first_at, last_at, cart (an abandoned checkout)."""
    acc_id = acc["id"]
    by = {}

    def lead(key):
        return by.setdefault(key, {"key": key, "name": "", "email": "", "phone": "", "username": "", "followed": False, "sources": [],
                                   "items": [], "spent": 0, "access": [], "first_at": 0, "last_at": 0, "cart": None, "keyword": ""})

    def touch(p, at):
        if at:
            p["first_at"] = min(p["first_at"] or at, at)
            p["last_at"] = max(p["last_at"], at)

    def add_source(p, s):
        if s not in p["sources"]:
            p["sources"].append(s)

    handles = {}
    for c in store.contacts(acc_id):
        email = (c.get("email") or "").lower()
        p = lead(email) if email else lead("@" + (c.get("username") or c.get("igsid", "")).lower())
        p.update(username=c.get("username") or p["username"], phone=c.get("phone") or p["phone"], email=email or p["email"],
                 followed=p["followed"] or bool(c.get("followed")), keyword=c.get("keyword") or p["keyword"])
        add_source(p, "signup" if c.get("source") == "bio_page" else "instagram")
        if c.get("username"):
            handles[c["username"].lower()] = p["key"]
        touch(p, c.get("first_at") or c.get("last_at"))
        touch(p, c.get("last_at"))
    sales = shop.sales(acc_id, 500)
    for s in sales:
        email = (s.get("email") or "").lower()
        if not email:
            continue
        p = lead(email)
        p.update(email=email, name=s.get("name") or p["name"], phone=s.get("phone") or p["phone"])
        p["items"].append({"title": s.get("title", ""), "type": s.get("type", "file"), "price": s.get("price", 0), "at": s.get("paid_at", 0)})
        p["spent"] += int(s.get("price") or 0)
        add_source(p, "buyer")
        touch(p, s.get("paid_at"))
    for c in courses.of_account(acc_id):
        for e in courses.students(c["id"]):
            p = lead(e["email"].lower())
            p.update(email=e["email"].lower(), name=p["name"] or e.get("name", ""), phone=p["phone"] or e.get("phone", ""))
            p["access"].append({"title": c["title"], "until": e.get("until"), "percent": courses.percent(c, e)})
            if not any(i["title"] == c["title"] for i in p["items"]):
                p["items"].append({"title": c["title"], "type": "course", "price": 0, "at": e.get("at", 0)})
            add_source(p, "student")
            touch(p, e.get("at"))
    paid = {(s.get("email", ""), s.get("title", "")) for s in sales}
    for cart in carts(acc_id, paid_keys=paid):
        p = lead(cart["email"])
        p.update(email=cart["email"], name=p["name"] or cart["name"], phone=p["phone"] or cart["phone"])
        if not p["cart"]:
            p["cart"] = cart
        add_source(p, "cart")
        touch(p, cart["at"])
    for p in by.values():
        p["segments"] = segments_of(p)
    return sorted(by.values(), key=lambda p: -p["last_at"])


def segments_of(p):
    s = ["all"]
    if p["spent"] > 0 or p["access"]:
        s.append("customers")
    if p["username"]:
        s.append("instagram")
    if p["followed"]:
        s.append("followers")
    if (p["email"] or p["phone"]) and "customers" not in s:
        s.append("subscribers")
    if p["cart"]:
        s.append("carts")
    return s


def remind(acc, order_id):
    """Emails an abandoned checkout a link back to the item (once per cart). Returns the order."""
    o = _order(order_id)
    if not o or o.get("acc") != acc["id"] or o.get("status") == "paid":
        raise shop.ShopError("That checkout isn't open any more.")
    if o.get("reminded"):
        raise shop.ShopError("You already sent this person a reminder.")
    if o.get("type") == "course":
        c = courses.get(o.get("course"))
        if not c or c.get("status") != "published":
            raise shop.ShopError("That course isn't on sale right now.")
        link = f"{shop._site()}/{acc.get('username', '')}/c/{c.get('slug') or c['id']}"
    else:
        link = f"{shop._site()}/{acc.get('username', '')}/p/{o.get('product', '')}"
    by = f"@{acc['username']}" if acc.get("username") else "the creator"
    html = (f"<p>Hi {shop._esc((o.get('name') or '').split(' ')[0] or 'there')},</p>"
            f"<p>You were one step away from getting <b>{shop._esc(o['title'])}</b> from {by}. Your spot is still open:</p>"
            + shop._button(link, "Complete my purchase") +
            "<p style=\"color:#5E6068;font-size:13px\">If you've already bought it, ignore this email.</p>")
    if not shop._mail(o["email"], f"Still want {o['title']}?", html):
        raise shop.ShopError("The email couldn't be sent. Try again later.")
    o["reminded"] = int(time.time())
    store.set_json(f"s:shoporder:{order_id}", o)
    return o


def csv_rows(rows):
    yield ["Name", "Email", "Phone", "Instagram", "Followed", "Sources", "Bought", "Spent (₹)", "First seen", "Last seen"]
    for p in rows:
        yield [p["name"], p["email"], p["phone"], ("@" + p["username"]) if p["username"] else "", "yes" if p["followed"] else "",
               " ".join(p["sources"]), "; ".join(i["title"] for i in p["items"]), p["spent"],
               time.strftime("%Y-%m-%d", time.gmtime(p["first_at"])) if p["first_at"] else "",
               time.strftime("%Y-%m-%d", time.gmtime(p["last_at"])) if p["last_at"] else ""]
