"""Courses: sell a course of modules and lessons; students learn on ReplyInbox (like SuperProfile Courses).

Course (s:course:<id>; an account's list at s:t:<acc>:courses): sales page details, modules → lessons
(video / text / audio / quiz / assignment), pricing (fixed or customer decides, discount), validity (lifetime or N
months), live classes (weekly schedule + join link), certificate, coupons, checkout questions, Meta Pixel, theme.

Buying uses the Store checkout (shop.py): Razorpay order with a Route transfer of the creator's share; shop.fulfil()
calls enroll() for orders of type "course".
Students sign in with an email code (session["student"]) or the one-time link in their purchase email.
Enrollment: s:enr:<course>:<email> (progress, quiz scores, assignments, access until); s:enrs:<course> = emails;
s:mycourses:<email> = course ids. Certificates: s:cert:<id>.
"""
import calendar
import json
import os
import re
import secrets
import time

import shop
import store

MAX_COURSES, MAX_MODULES, MAX_LESSONS = 50, 40, 300
LESSON_TYPES = ("video", "text", "audio", "quiz", "assignment")
THEMES = ("light", "dark")
MONTH = 30 * 86400
GSTIN_RE = r"\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]"
COMMUNITY = ("whatsapp", "telegram", "discord", "other")


def fx():
    """₹ per US$ for showing dollar sales in rupees (the real rate comes from Razorpay's payment when it has one)."""
    try:
        return float(os.environ.get("USD_INR", "") or 85)
    except ValueError:
        return 85.0


class CourseError(Exception):
    """A problem to show the person as it is."""


def _s(v, n):
    return str(v or "").strip()[:n]


def _https(v):
    v = str(v or "").strip()
    return v if v.startswith("https://") else ""


def _img(v):
    """A cover image: an https link or one uploaded here (/f/<id>/<name>)."""
    v = str(v or "").strip()
    return v if v.startswith("https://") or re.fullmatch(r"/f/[\w-]{6,20}/[\w.-]{1,100}", v) else ""


def _int(v, lo, hi, default=0):
    try:
        return max(lo, min(hi, int(float(str(v).replace(",", "").replace("₹", "").strip()))))
    except (TypeError, ValueError):
        return default


def _id(v, n=10):
    v = re.sub(r"[^a-z0-9]", "", str(v or "").lower())[:n]
    return v or secrets.token_hex(n // 2)


def slugify(v):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(v or "").lower())).strip("-")[:60]


# ---------- storage ----------

def _list_key(acc_id):
    return store.account_key(acc_id, "courses")


def get(cid):
    return store.get_json(f"s:course:{cid}") if cid and re.fullmatch(r"[0-9a-f]{10}", str(cid)) else None


def of_account(acc_id):
    return [c for c in (get(cid) for cid in store.get_json(_list_key(acc_id), [])) if c]


def by_slug(acc_id, slug):
    cid = store.redis("GET", f"s:courseslug:{acc_id}:{slug}") if slug else None
    return get(cid) if cid else get(slug)


def create(acc, title):
    ids = store.get_json(_list_key(acc["id"]), [])
    if len(ids) >= MAX_COURSES:
        raise CourseError(f"You can have up to {MAX_COURSES} courses.")
    c = {"id": secrets.token_hex(5), "acc": acc["id"], "title": _s(title, 75) or "My course", "status": "draft",
         "created": int(time.time()), "price": 999, "button": "Join now 🚀", "modules": [
             {"id": _id(""), "title": "Module 1 · Welcome", "live": True, "unlock": "now", "delay": 0,
              "lessons": [{"id": _id(""), "type": "text", "title": "Start here", "body": "Welcome! 👋", "live": True, "free": True}]}],
         "validity": {"kind": "life", "months": 6}, "theme": "light", "terms": True, "ask_phone": False,
         "faqs": [], "benefits": [], "coupons": [], "live": {"enabled": False}, "cert": {"enabled": False}}
    c["slug"] = _free_slug(acc["id"], slugify(c["title"]) or c["id"], c["id"])
    store.redis("SET", f"s:courseslug:{acc['id']}:{c['slug']}", c["id"])
    store.set_json(f"s:course:{c['id']}", c)
    store.set_json(_list_key(acc["id"]), [c["id"]] + ids)
    return c


def _free_slug(acc_id, slug, cid):
    base, n = slug or cid, 1
    while True:
        cur = store.redis("GET", f"s:courseslug:{acc_id}:{slug}")
        if not cur or cur == cid:
            return slug
        n += 1
        slug = f"{base}-{n}"


def delete(acc, cid):
    c = get(cid)
    if not c or c["acc"] != acc["id"]:
        return False
    store.set_json(_list_key(acc["id"]), [x for x in store.get_json(_list_key(acc["id"]), []) if x != cid])
    store.redis("DEL", f"s:courseslug:{acc['id']}:{c.get('slug', '')}")
    c["status"], c["deleted"] = "unpublished", int(time.time())  # students keep access; the page stops selling
    store.set_json(f"s:course:{cid}", c)
    return True


def clean(acc, cid, data):
    """Validates and saves the editor's whole course. Returns the saved course."""
    c = get(cid)
    if not c or c["acc"] != acc["id"]:
        raise CourseError("Course not found.")
    d = data or {}
    out = {**c,
           "title": _s(d.get("title"), 75) or c["title"], "cover": _img(d.get("cover")), "cover_video": _https(d.get("cover_video")),
           "desc": _s(d.get("desc"), 20000), "button": _s(d.get("button"), 25) or "Join now",
           "about": _s(d.get("about"), 4000), "show_about": bool(d.get("show_about", True)),
           "show_enrolled": bool(d.get("show_enrolled")), "status": d.get("status") if d.get("status") in ("draft", "published", "unpublished") else c["status"],
           "theme": d.get("theme") if d.get("theme") in THEMES else "light", "terms": d.get("terms", True) is not False,
           "ask_phone": bool(d.get("ask_phone")), "pixel": re.sub(r"\D", "", str(d.get("pixel", "")))[:20],
           "faqs": [{"q": _s(f.get("q"), 200), "a": _s(f.get("a"), 2000)} for f in (d.get("faqs") or [])[:30]
                    if isinstance(f, dict) and _s(f.get("q"), 200)],
           "benefits": [_s(b, 200) for b in (d.get("benefits") or [])[:20] if _s(b, 200)]}
    # pricing
    mode = "pwyw" if d.get("price_mode") == "pwyw" else "fixed"
    price = _int(d.get("price"), 0, 500000, c.get("price", 0))
    sale = _int(d.get("sale_price"), 0, 500000, 0) if d.get("discount") else 0
    if mode == "fixed" and not 10 <= (sale or price) <= 500000:
        raise CourseError("Price must be at least ₹10 (or set it free with 'Customer decides' and a minimum).")
    if sale and sale >= price:
        raise CourseError("The discounted price must be lower than the price.")
    out.update(price_mode=mode, price=price, sale_price=sale, min_price=_int(d.get("min_price"), 0, 500000, 0))
    if mode == "pwyw" and out["min_price"] and out["min_price"] < 10:
        raise CourseError("The minimum price must be ₹10 or more (or 0 for free).")
    v = d.get("validity") or {}
    out["validity"] = {"kind": "limited" if v.get("kind") == "limited" else "life", "months": _int(v.get("months"), 1, 60, 6)}
    # modules and lessons
    mods, n_lessons = [], 0
    for m in (d.get("modules") or [])[:MAX_MODULES]:
        if not isinstance(m, dict):
            continue
        lessons = []
        for ls in (m.get("lessons") or []):
            if not isinstance(ls, dict) or n_lessons >= MAX_LESSONS:
                continue
            kind = ls.get("type") if ls.get("type") in LESSON_TYPES else "text"
            item = {"id": _id(ls.get("id")), "type": kind, "title": _s(ls.get("title"), 150) or "Untitled lesson",
                    "live": ls.get("live", True) is not False, "free": bool(ls.get("free")),
                    "body": _s(ls.get("body"), 30000), "video": _https(ls.get("video")), "audio": _https(ls.get("audio")),
                    "audio_file": _s(ls.get("audio_file"), 20), "video_file": _s(ls.get("video_file"), 24), "video_name": _s(ls.get("video_name"), 100),
                    "files": [{"id": _s(f.get("id"), 20), "name": _s(f.get("name"), 100), "size": _int(f.get("size"), 0, 10 ** 9)}
                              for f in (ls.get("files") or [])[:10] if isinstance(f, dict) and f.get("id")]}
            if kind == "quiz":
                qs = []
                for q in (ls.get("questions") or [])[:50]:
                    opts = [_s(o, 300) for o in (q.get("options") or [])[:6] if _s(o, 300)] if isinstance(q, dict) else []
                    if isinstance(q, dict) and _s(q.get("q"), 500) and len(opts) >= 2:
                        qs.append({"q": _s(q.get("q"), 500), "options": opts, "answer": _int(q.get("answer"), 0, len(opts) - 1, 0)})
                item.update(questions=qs, pass_pct=_int(ls.get("pass_pct"), 0, 100, 60))
            lessons.append(item)
            n_lessons += 1
        unlock = m.get("unlock") if m.get("unlock") in ("now", "delay", "after_prev") else "now"
        mods.append({"id": _id(m.get("id")), "title": _s(m.get("title"), 150) or "Untitled module", "live": m.get("live", True) is not False,
                     "unlock": unlock, "delay": _int(m.get("delay"), 0, 365, 0), "lessons": lessons})
    out["modules"] = mods
    # live classes
    lv = d.get("live") or {}
    days = sorted({int(x) for x in lv.get("days") or [] if str(x).isdigit() and int(x) < 7})
    out["live"] = {"enabled": bool(lv.get("enabled")), "link": _https(lv.get("link")), "provider": _s(lv.get("provider"), 30) or "Zoom",
                   "days": days, "start": _s(lv.get("start"), 5), "end": _s(lv.get("end"), 5),
                   "from": _s(lv.get("from"), 10), "to": _s(lv.get("to"), 10), "title": _s(lv.get("title"), 80) or "Live class"}
    if out["live"]["enabled"] and not (days and _date(out["live"]["from"]) and _date(out["live"]["to"]) and _hm(out["live"]["start"]) is not None):
        raise CourseError("Live classes: pick the days, the start time and the first and last date.")
    ct = d.get("cert") or {}
    out["cert"] = {"enabled": bool(ct.get("enabled")), "signer": _s(ct.get("signer"), 80), "title": _s(ct.get("title"), 80)}
    # coupons
    coupons = []
    old = {x["code"]: x for x in c.get("coupons") or []}
    for cp in (d.get("coupons") or [])[:50]:
        code = re.sub(r"[^A-Z0-9]", "", str((cp or {}).get("code", "")).upper())[:20]
        if not code:
            continue
        coupons.append({"code": code, "kind": "flat" if cp.get("kind") == "flat" else "pct", "value": _int(cp.get("value"), 1, 100000, 10),
                        "max": _int(cp.get("max"), 0, 100000, 0), "used": (old.get(code) or {}).get("used", 0), "on": cp.get("on", True) is not False})
    out["coupons"] = coupons
    # international price (US$, cards from outside India)
    it = d.get("intl") or {}
    usd, usd_sale = _int(it.get("usd"), 0, 5000, 0), _int(it.get("usd_sale"), 0, 5000, 0)
    out["intl"] = {"enabled": bool(it.get("enabled")), "usd": usd, "usd_sale": usd_sale if 0 < usd_sale < usd else 0}
    if out["intl"]["enabled"] and (mode != "fixed" or not (out["intl"]["usd_sale"] or usd)):
        raise CourseError("International price: use a fixed price and enter a US$ price of at least $1.")
    # GST added on top of the price (Indian buyers)
    g = d.get("gst") or {}
    gstin = re.sub(r"[^0-9A-Z]", "", str(g.get("gstin", "")).upper())[:15]
    if gstin and not re.fullmatch(GSTIN_RE, gstin):
        raise CourseError("That GSTIN doesn't look right (15 characters, like 07ABCDE1234F1Z5).")
    out["gst"] = {"enabled": bool(g.get("enabled")), "pct": _int(g.get("pct"), 1, 28, 18), "gstin": gstin, "name": _s(g.get("name"), 100)}
    # bump offer: one extra product or course ticked at checkout
    b = d.get("bump") or {}
    out["bump"] = {"enabled": bool(b.get("enabled")), "kind": "product" if b.get("kind") == "product" else "course",
                   "id": _s(b.get("id"), 20), "price": _int(b.get("price"), 0, 500000, 0), "title": _s(b.get("title"), 100), "desc": _s(b.get("desc"), 300)}
    if out["bump"]["enabled"]:
        target = bump_target({**out, "id": cid})
        if not target:
            raise CourseError("Bump offer: pick one of your other courses or a file / locked-content product.")
        if out["bump"]["price"] < 1:
            raise CourseError("Bump offer: enter its price (₹1 or more).")
        out["bump"]["title"] = out["bump"]["title"] or target["title"]
    # automatic emails to students, N days after they enroll
    emails = []
    for x in (d.get("emails") or [])[:12]:
        if isinstance(x, dict) and _s(x.get("subject"), 120) and _s(x.get("body"), 5000):
            emails.append({"id": _id(x.get("id"), 8), "days": _int(x.get("days"), 1, 365, 1), "subject": _s(x.get("subject"), 120),
                           "body": _s(x.get("body"), 5000), "unfinished": bool(x.get("unfinished"))})
    out["emails"] = emails
    store.redis("SADD" if emails else "SREM", "s:courseseq", cid)
    # Google Analytics
    ga = str(d.get("ga", "")).strip().upper()
    if ga and not re.fullmatch(r"G-[A-Z0-9]{4,14}", ga):
        raise CourseError("Google Analytics: paste the Measurement ID, like G-AB12CD34EF.")
    out["ga"] = ga
    # community for students
    cm = d.get("community") or {}
    out["community"] = {"enabled": bool(cm.get("enabled")), "kind": cm.get("kind") if cm.get("kind") in COMMUNITY else "whatsapp",
                        "link": _https(cm.get("link")), "note": _s(cm.get("note"), 300)}
    if out["community"]["enabled"] and not out["community"]["link"]:
        raise CourseError("Community: paste the invite link (https://…).")
    # page URL
    slug = slugify(d.get("slug")) or c.get("slug") or c["id"]
    if slug != c.get("slug"):
        slug = _free_slug(acc["id"], slug, cid)
        store.redis("DEL", f"s:courseslug:{acc['id']}:{c.get('slug', '')}")
        store.redis("SET", f"s:courseslug:{acc['id']}:{slug}", cid)
    out["slug"] = slug
    if out["status"] == "published" and not any(ls for m in mods for ls in m["lessons"]):
        raise CourseError("Add at least one lesson before publishing.")
    store.set_json(f"s:course:{cid}", out)
    return out


# ---------- helpers for pages ----------

def _date(v):
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(v or ""))
    if not m:
        return None
    try:
        return calendar.timegm((int(m.group(1)), int(m.group(2)), int(m.group(3)), 0, 0, 0)) - shop.IST
    except (ValueError, OverflowError):
        return None


def _hm(v):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", str(v or ""))
    return int(m.group(1)) * 60 + int(m.group(2)) if m and int(m.group(1)) < 24 and int(m.group(2)) < 60 else None


def price_now(c):
    return c.get("sale_price") or c.get("price") or 0


def lessons(c, include_drafts=False):
    """[(module, lesson)] in order (published modules and lessons only, unless include_drafts)."""
    return [(m, ls) for m in c.get("modules", []) if include_drafts or m.get("live", True)
            for ls in m["lessons"] if include_drafts or ls.get("live", True)]


def counts(c):
    mods = [m for m in c.get("modules", []) if m.get("live", True)]
    return len(mods), sum(1 for m in mods for ls in m["lessons"] if ls.get("live", True))


def sessions(c, now=None):
    """Live class sessions: [{n, start, end, done}] from the weekly schedule."""
    lv = c.get("live") or {}
    if not lv.get("enabled"):
        return []
    now = now or time.time()
    a, b, st, en = _date(lv.get("from")), _date(lv.get("to")), _hm(lv.get("start")), _hm(lv.get("end"))
    if a is None or b is None or st is None:
        return []
    en = en if en is not None and en > st else st + 60
    out, day = [], a
    while day <= b and len(out) < 200:
        if time.gmtime(day + shop.IST).tm_wday in lv.get("days", []):
            out.append({"n": len(out) + 1, "start": day + st * 60, "end": day + en * 60, "done": day + en * 60 < now})
        day += 86400
    return out


def embed(url):
    """A YouTube / Vimeo / Loom / Google Drive link → an embeddable player URL ('' if not one of those)."""
    u = str(url or "")
    m = re.search(r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/|live/)|youtu\.be/)([\w-]{6,})", u)
    if m:
        return f"https://www.youtube-nocookie.com/embed/{m.group(1)}?rel=0&modestbranding=1"
    m = re.search(r"vimeo\.com/(?:video/)?(\d+)(?:/(\w+))?", u)
    if m:
        return f"https://player.vimeo.com/video/{m.group(1)}" + (f"?h={m.group(2)}" if m.group(2) else "")
    m = re.search(r"loom\.com/(?:share|embed)/(\w+)", u)
    if m:
        return f"https://www.loom.com/embed/{m.group(1)}"
    m = re.search(r"drive\.google\.com/file/d/([\w-]+)", u)
    if m:
        return f"https://drive.google.com/file/d/{m.group(1)}/preview"
    return ""


def apply_coupon(c, code, amount, usd=False):
    code = re.sub(r"[^A-Z0-9]", "", str(code or "").upper())
    if not code:
        return amount, None
    cp = next((x for x in c.get("coupons") or [] if x["code"] == code and x.get("on", True)), None)
    if not cp or (cp.get("max") and cp.get("used", 0) >= cp["max"]):
        raise CourseError("That coupon isn't valid.")
    # flat coupons are in rupees; for a dollar price they take off the same value in dollars
    off = round(amount * cp["value"] / 100) if cp["kind"] == "pct" else (round(cp["value"] / fx()) if usd else cp["value"])
    return max(0, amount - off), cp["code"]


def intl_price(c):
    it = c.get("intl") or {}
    return (it.get("usd_sale") or it.get("usd") or 0) if it.get("enabled") and c.get("price_mode") != "pwyw" else 0


def quote(c, amount=None, coupon="", currency="INR", bump=False):
    """What a buyer pays, in whole rupees (or dollars): {currency, base, course, coupon, gst, bump, total}.
    base: fixed (discounted) price or their own amount (≥ minimum) for 'customer decides'; course: after the coupon;
    gst: added on top for Indian buyers when switched on; bump: the ticked bump offer (rupee orders)."""
    usd = currency == "USD" and intl_price(c) > 0
    if usd:
        base = intl_price(c)
    elif c.get("price_mode") == "pwyw":
        base = _int(amount, 0, 500000, -1)
        if base < (c.get("min_price") or 0):
            raise CourseError(f"Enter an amount of at least ₹{c.get('min_price') or 0}.")
    else:
        base = price_now(c)
    course, used = apply_coupon(c, coupon, base, usd)
    if not usd and 0 < course < 10:
        course = 10
    g = c.get("gst") or {}
    gst = round(course * g.get("pct", 18) / 100) if g.get("enabled") and not usd else 0
    b = c.get("bump") or {}
    extra = b.get("price", 0) if bump and b.get("enabled") and not usd and bump_target(c) else 0
    return {"currency": "USD" if usd else "INR", "base": base, "course": course, "coupon": used, "gst": gst, "bump": extra,
            "total": course + gst + extra}


def bump_target(c):
    """The bump offer's course or product ({kind, id, title}) if it still exists and can be sold, else None."""
    b = c.get("bump") or {}
    if not b.get("id"):
        return None
    if b.get("kind") == "product":
        p = shop.get(c["acc"], b["id"])
        return {"kind": "product", "id": p["id"], "title": p["title"]} if p and p.get("type", "file") in ("file", "locked") and p.get("enabled", True) else None
    o = get(b["id"])
    return {"kind": "course", "id": o["id"], "title": o["title"]} if o and o["acc"] == c["acc"] and o["id"] != c["id"] and not o.get("deleted") else None


# ---------- buying and enrolling ----------

def order(acc, c, buyer):
    """Starts a purchase. Free courses enroll straight away (returns {'free': True, 'link': ...})."""
    if c.get("status") != "published" or c.get("deleted"):
        raise CourseError("This course isn't open for enrolment right now.")
    email = str(buyer.get("email", "")).strip().lower()[:200]
    if not shop.EMAIL_RE.match(email):
        raise CourseError("Enter your email: your course access is sent there.")
    name = _s(buyer.get("name"), 80)
    if not name:
        raise CourseError("Enter your name.")
    phone = re.sub(r"\D", "", str(buyer.get("phone", "")))[-10:]
    if c.get("ask_phone") and len(phone) != 10:
        raise CourseError("Enter a 10-digit mobile number.")
    q = quote(c, buyer.get("amount"), buyer.get("coupon"), buyer.get("currency") or "INR", bool(buyer.get("bump")))
    usd = q["currency"] == "USD"
    if q["total"] == 0:
        rec = {"id": "free_" + secrets.token_hex(6), "acc": acc["id"], "course": c["id"], "title": c["title"], "price": 0,
               "email": email, "name": name, "phone": phone, "coupon": q["coupon"], "type": "course", "status": "paid", "paid_at": int(time.time())}
        e = enroll(rec)
        return {"free": True, "link": magic_link(email, c["id"]), "enrolled": bool(e)}
    import users
    owner = users.owner_of(acc)
    if not shop.ready() or not owner or not shop.can_sell(owner):
        raise CourseError("Payments for this course aren't switched on yet. Please try again later.")
    inr = round(q["total"] * fx()) if usd else q["total"]  # what the sale is worth in rupees
    s = shop.split(acc, inr)
    body = {"amount": q["total"] * 100, "currency": q["currency"], "receipt": "rc_" + secrets.token_hex(6),
            "notes": {"kind": "course", "account": acc["id"], "course": c["id"]}}
    if not usd:  # Route transfers are in rupees: dollar payments are transferred once captured (shop.transfer_payment)
        body["transfers"] = [{"account": shop.payout(owner)["account_id"], "amount": int(round(s["creator"] * 100)), "currency": "INR",
                              "notes": {"course": c["title"][:60], "buyer": email[:60]}, "linked_account_notes": ["course"], "on_hold": 0}]
    o = shop._rzp("POST", "/v1/orders", body)
    rec = {"id": o["id"], "acc": acc["id"], "course": c["id"], "product": c["id"], "title": c["title"], "price": inr,
           "creator_gets": s["creator"], "fee": s["fee"], "email": email, "name": name, "phone": phone, "coupon": q["coupon"],
           "type": "course", "status": "created", "created": int(time.time()), "currency": q["currency"], "amount_minor": q["total"] * 100,
           "quote": q, "course_price": round((q["course"] + q["gst"]) * fx()) if usd else q["course"] + q["gst"]}
    if q["bump"]:
        rec["bump"] = {**bump_target(c), "price": q["bump"]}
    store.set_json(f"s:shoporder:{o['id']}", rec)
    return {"key": shop._env("RAZORPAY_KEY_ID"), "order_id": o["id"], "amount": q["total"] * 100, "currency": q["currency"],
            "name": c["title"], "email": email, "phone": phone}


def enroll(o):
    """Gives the buyer access (called once per paid order). Returns the enrollment."""
    c = get(o["course"])
    if not c:
        return None
    key = f"s:enr:{c['id']}:{o['email']}"
    e = store.get_json(key) or {"email": o["email"], "course": c["id"], "acc": c["acc"], "at": int(time.time()),
                                "progress": {}, "quiz": {}, "work": {}}
    v = c.get("validity") or {}
    start = max(time.time(), e.get("until") or 0) if e.get("until") else time.time()
    e.update(name=o.get("name") or e.get("name", ""), phone=o.get("phone") or e.get("phone", ""), order=o["id"], paid=o.get("price", 0),
             until=int(start + v.get("months", 6) * MONTH) if v.get("kind") == "limited" else None)
    store.set_json(key, e)
    store.redis("SADD", f"s:enrs:{c['id']}", o["email"])
    store.redis("SADD", f"s:mycourses:{o['email']}", c["id"])
    if o.get("coupon"):
        for cp in c.get("coupons") or []:
            if cp["code"] == o["coupon"]:
                cp["used"] = cp.get("used", 0) + 1
    paid = int(o.get("course_price", o.get("price")) or 0)
    c["sales"], c["revenue"] = int(c.get("sales") or 0) + 1, int(c.get("revenue") or 0) + paid
    store.set_json(f"s:course:{c['id']}", c)
    store.count(c["acc"], "sales")
    store.count(c["acc"], "revenue", paid)
    store.log_activity(c["acc"], "", "", c["title"], "sale", "ok", f"₹{paid} · course · {o.get('name') or o['email']}")
    send_welcome(c, o)
    return e


def enrollment(cid, email):
    e = store.get_json(f"s:enr:{cid}:{email}") if cid and email else None
    if e and e.get("until") and e["until"] < time.time():
        return {**e, "expired": True}
    return e


def students(cid):
    out = [store.get_json(f"s:enr:{cid}:{em}") for em in store.redis("SMEMBERS", f"s:enrs:{cid}") or []]
    return sorted([e for e in out if e], key=lambda e: -e.get("at", 0))


def my_courses(email):
    return [c for c in (get(cid) for cid in store.redis("SMEMBERS", f"s:mycourses:{email}") or []) if c]


# ---------- student access ----------

def magic_link(email, cid=""):
    tok = secrets.token_urlsafe(24)
    store.redis("SET", f"s:magic:{tok}", json.dumps({"email": email, "course": cid}), "EX", 14 * 86400)
    return f"{shop._site()}/learn/in/{tok}"


def use_magic(tok):
    raw = store.redis("GET", f"s:magic:{tok}") if tok and re.fullmatch(r"[\w-]{20,60}", tok) else None
    return json.loads(raw) if raw else None


def unlocked(c, e, mod_index):
    """Whether a module is open for this student (drip: after N days, or after finishing the previous module)."""
    m = c["modules"][mod_index]
    if m.get("unlock") == "delay":
        return time.time() >= (e or {}).get("at", 0) + m.get("delay", 0) * 86400
    if m.get("unlock") == "after_prev" and mod_index > 0:
        prev = [ls for ls in c["modules"][mod_index - 1]["lessons"] if ls.get("live", True)]
        return all(ls["id"] in (e or {}).get("progress", {}) for ls in prev)
    return True


def percent(c, e):
    ids = [ls["id"] for _, ls in lessons(c)]
    done = sum(1 for i in ids if i in (e or {}).get("progress", {}))
    return round(100 * done / len(ids)) if ids else 0


def mark(c, email, lesson_id, done=True):
    key = f"s:enr:{c['id']}:{email}"
    e = store.get_json(key)
    if not e:
        raise CourseError("You're not enrolled in this course.")
    if done:
        e.setdefault("progress", {})[lesson_id] = int(time.time())
    else:
        e.setdefault("progress", {}).pop(lesson_id, None)
    store.set_json(key, e)
    return e


def grade_quiz(c, email, lesson, answers):
    qs = lesson.get("questions") or []
    if not qs:
        raise CourseError("This quiz has no questions yet.")
    right = sum(1 for i, q in enumerate(qs) if i < len(answers) and _int(answers[i], -1, 99, -1) == q["answer"])
    score = round(100 * right / len(qs))
    passed = score >= lesson.get("pass_pct", 60)
    key = f"s:enr:{c['id']}:{email}"
    e = store.get_json(key)
    e.setdefault("quiz", {})[lesson["id"]] = {"score": score, "right": right, "total": len(qs), "passed": passed, "at": int(time.time())}
    if passed:
        e.setdefault("progress", {})[lesson["id"]] = int(time.time())
    store.set_json(key, e)
    return e["quiz"][lesson["id"]]


def submit_work(c, email, lesson, text, link):
    key = f"s:enr:{c['id']}:{email}"
    e = store.get_json(key)
    text, link = _s(text, 10000), _https(link)
    if not text and not link:
        raise CourseError("Write your answer or add a link.")
    e.setdefault("work", {})[lesson["id"]] = {"text": text, "link": link, "at": int(time.time()), "grade": None, "feedback": ""}
    e.setdefault("progress", {})[lesson["id"]] = int(time.time())
    store.set_json(key, e)
    return e["work"][lesson["id"]]


def review_work(c, email, lesson_id, grade, feedback):
    key = f"s:enr:{c['id']}:{email}"
    e = store.get_json(key)
    w = (e or {}).get("work", {}).get(lesson_id)
    if not w:
        raise CourseError("No submission to review.")
    w.update(grade=_s(grade, 20), feedback=_s(feedback, 3000), reviewed=int(time.time()))
    store.set_json(key, e)
    return w


def certificate(c, email):
    """The student's certificate (created once they finish every lesson), or None."""
    e = store.get_json(f"s:enr:{c['id']}:{email}")
    if not e or not (c.get("cert") or {}).get("enabled") or percent(c, e) < 100:
        return None
    if not e.get("cert"):
        cid = secrets.token_hex(6)
        store.set_json(f"s:cert:{cid}", {"id": cid, "name": e.get("name") or email.split("@")[0], "course": c["title"],
                                          "course_id": c["id"], "acc": c["acc"], "signer": (c.get("cert") or {}).get("signer", ""),
                                          "at": int(time.time())})
        e["cert"] = cid
        store.set_json(f"s:enr:{c['id']}:{email}", e)
    return store.get_json(f"s:cert:{e['cert']}")


def get_cert(cert_id):
    return store.get_json(f"s:cert:{cert_id}") if cert_id and re.fullmatch(r"[0-9a-f]{12}", cert_id) else None


def count_view(c):
    store.redis("INCR", f"s:courseviews:{c['id']}")


def views(c):
    return int(store.redis("GET", f"s:courseviews:{c['id']}") or 0)


# ---------- emails ----------

COMMUNITY_NAMES = {"whatsapp": "WhatsApp group", "telegram": "Telegram group", "discord": "Discord server", "other": "community"}


def money(amount, currency="INR"):
    return f"${amount:,}" if currency == "USD" else f"₹{amount:,}"


def receipt_html(c, o):
    """The payment lines for the welcome email: course, GST (with the creator's GSTIN), bump offer, total."""
    q = o.get("quote")
    if not q or not q.get("total"):
        return ""
    cur, g = q.get("currency", "INR"), c.get("gst") or {}
    rows = [(c["title"], money(q["course"], cur))]
    if q.get("gst"):
        rows.append((f"GST {g.get('pct', 18)}%", money(q["gst"], cur)))
    if q.get("bump") and o.get("bump"):
        rows.append((o["bump"]["title"], money(q["bump"], cur)))
    rows.append(("<b>Total paid</b>", f"<b>{money(q['total'], cur)}</b>"))
    cells = "".join(f"<tr><td style=\"padding:4px 0\">{a if a.startswith('<b>') else shop._esc(a)}</td><td style=\"padding:4px 0;text-align:right\">{b}</td></tr>"
                    for a, b in rows)
    seller = (f"<br>Sold by {shop._esc(g.get('name') or '')} · GSTIN {g['gstin']}" if g.get("gstin") else "")
    return (f"<table style=\"width:100%;border-collapse:collapse;font-size:14px;border-top:1px solid #DCDBD3;margin-top:14px\">{cells}</table>"
            f"<p style=\"color:#5E6068;font-size:12px\">Order {shop._esc(o['id'])}{seller}</p>")


def send_welcome(c, o):
    acc = store.load_account(c["acc"]) or {}
    by = f"@{acc.get('username')}" if acc.get("username") else "your creator"
    link = magic_link(o["email"], c["id"])
    cm = c.get("community") or {}
    community = (f"<p>👥 Join the course {COMMUNITY_NAMES.get(cm.get('kind'), 'community')}: "
                 f"<a href=\"{shop._esc(cm['link'])}\">{shop._esc(cm['link'])}</a></p>" if cm.get("enabled") and cm.get("link") else "")
    html = (f"<h2 style=\"margin:0 0 8px\">Welcome to {shop._esc(c['title'])} 🎉</h2>"
            f"<p>Hi {shop._esc(o.get('name') or '')}, you're enrolled in <b>{shop._esc(c['title'])}</b> by {by}.</p>"
            + shop._button(link, "Start learning") + community +
            f"<p style=\"color:#5E6068;font-size:13px\">This button signs you in (it works for 14 days). Later, sign in at "
            f"{shop._site()}/learn with this email.</p>" + receipt_html(c, o))
    shop._mail(o["email"], f"You're in: {c['title']}", html)


# ---------- automatic emails (sent by the daily cron) ----------

def _fill(text, e, c):
    return (text.replace("{name}", (e.get("name") or "there").split(" ")[0]).replace("{course}", c["title"]))


def send_sequences(now=None, limit=300):
    """Sends each course's automatic emails that are due: email N goes `days` after the student enrolled.
    Only within 3 days of its due date (so adding an email later doesn't mail every old student), once per student."""
    now, sent = now or time.time(), 0
    for cid in store.redis("SMEMBERS", "s:courseseq") or []:
        c = get(cid)
        if not c or c.get("deleted") or not c.get("emails"):
            store.redis("SREM", "s:courseseq", cid)
            continue
        acc = store.load_account(c["acc"]) or {}
        by = f"@{acc['username']}" if acc.get("username") else ""
        for email in store.redis("SMEMBERS", f"s:enrs:{cid}") or []:
            e = store.get_json(f"s:enr:{cid}:{email}")
            if not e or (e.get("until") and e["until"] < now):
                continue
            done = e.setdefault("sent", [])
            changed = False
            for m in c["emails"]:
                due = e.get("at", 0) + m["days"] * 86400
                if m["id"] in done or not due <= now < due + 3 * 86400 or (m.get("unfinished") and percent(c, e) >= 100):
                    continue
                if sent >= limit:
                    return sent
                body = "".join(f"<p>{shop._esc(_fill(p, e, c))}</p>".replace("\n", "<br>") for p in m["body"].split("\n\n") if p.strip())
                html = body + shop._button(magic_link(email, cid), "Open the course") + (
                    f"<p style=\"color:#5E6068;font-size:12px\">You're getting this because you enrolled in {shop._esc(c['title'])}{' by ' + by if by else ''}.</p>")
                if shop._mail(email, _fill(m["subject"], e, c), html):
                    sent += 1
                done.append(m["id"])
                changed = True
            if changed:
                store.set_json(f"s:enr:{cid}:{email}", e)
    return sent
