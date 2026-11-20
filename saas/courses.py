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
import re
import secrets
import time

import shop
import store

MAX_COURSES, MAX_MODULES, MAX_LESSONS = 50, 40, 300
LESSON_TYPES = ("video", "text", "audio", "quiz", "assignment")
THEMES = ("light", "dark")
MONTH = 30 * 86400


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
                    "audio_file": _s(ls.get("audio_file"), 20),
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


def apply_coupon(c, code, amount):
    code = re.sub(r"[^A-Z0-9]", "", str(code or "").upper())
    if not code:
        return amount, None
    cp = next((x for x in c.get("coupons") or [] if x["code"] == code and x.get("on", True)), None)
    if not cp or (cp.get("max") and cp.get("used", 0) >= cp["max"]):
        raise CourseError("That coupon isn't valid.")
    off = round(amount * cp["value"] / 100) if cp["kind"] == "pct" else cp["value"]
    return max(0, amount - off), cp["code"]


def quote(c, amount=None, coupon=""):
    """What a buyer pays: fixed (discounted) price, or their own amount (≥ minimum) for 'customer decides'."""
    if c.get("price_mode") == "pwyw":
        pay = _int(amount, 0, 500000, -1)
        if pay < (c.get("min_price") or 0):
            raise CourseError(f"Enter an amount of at least ₹{c.get('min_price') or 0}.")
    else:
        pay = price_now(c)
    pay, used = apply_coupon(c, coupon, pay)
    if 0 < pay < 10:
        pay = 10
    return pay, used


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
    pay, coupon = quote(c, buyer.get("amount"), buyer.get("coupon"))
    if pay == 0:
        rec = {"id": "free_" + secrets.token_hex(6), "acc": acc["id"], "course": c["id"], "title": c["title"], "price": 0,
               "email": email, "name": name, "phone": phone, "coupon": coupon, "type": "course", "status": "paid", "paid_at": int(time.time())}
        e = enroll(rec)
        return {"free": True, "link": magic_link(email, c["id"]), "enrolled": bool(e)}
    import users
    owner = users.owner_of(acc)
    if not shop.ready() or not owner or not shop.can_sell(owner):
        raise CourseError("Payments for this course aren't switched on yet. Please try again later.")
    s = shop.split(acc, pay)
    o = shop._rzp("POST", "/v1/orders", {
        "amount": pay * 100, "currency": "INR", "receipt": "rc_" + secrets.token_hex(6),
        "notes": {"kind": "course", "account": acc["id"], "course": c["id"]},
        "transfers": [{"account": shop.payout(owner)["account_id"], "amount": int(round(s["creator"] * 100)), "currency": "INR",
                       "notes": {"course": c["title"][:60], "buyer": email[:60]}, "linked_account_notes": ["course"], "on_hold": 0}]})
    rec = {"id": o["id"], "acc": acc["id"], "course": c["id"], "product": c["id"], "title": c["title"], "price": pay,
           "creator_gets": s["creator"], "fee": s["fee"], "email": email, "name": name, "phone": phone, "coupon": coupon,
           "type": "course", "status": "created", "created": int(time.time())}
    store.set_json(f"s:shoporder:{o['id']}", rec)
    return {"key": shop._env("RAZORPAY_KEY_ID"), "order_id": o["id"], "amount": pay * 100, "currency": "INR",
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
    c["sales"], c["revenue"] = int(c.get("sales") or 0) + 1, int(c.get("revenue") or 0) + int(o.get("price") or 0)
    store.set_json(f"s:course:{c['id']}", c)
    store.count(c["acc"], "sales")
    store.count(c["acc"], "revenue", int(o.get("price") or 0))
    store.log_activity(c["acc"], "", "", c["title"], "sale", "ok", f"₹{o.get('price', 0)} · course · {o.get('name') or o['email']}")
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

def send_welcome(c, o):
    acc = store.load_account(c["acc"]) or {}
    by = f"@{acc.get('username')}" if acc.get("username") else "your creator"
    link = magic_link(o["email"], c["id"])
    html = (f"<h2 style=\"margin:0 0 8px\">Welcome to {shop._esc(c['title'])} 🎉</h2>"
            f"<p>Hi {shop._esc(o.get('name') or '')}, you're enrolled in <b>{shop._esc(c['title'])}</b> by {by}.</p>"
            + shop._button(link, "Start learning") +
            f"<p style=\"color:#5E6068;font-size:13px\">This button signs you in (it works for 14 days). Later, sign in at "
            f"{shop._site()}/learn with this email.{' Paid ₹' + format(o['price'], ',') + ' · order ' + o['id'] + '.' if o.get('price') else ''}</p>")
    shop._mail(o["email"], f"You're in: {c['title']}", html)
