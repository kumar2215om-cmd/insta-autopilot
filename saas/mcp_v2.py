"""Connect Claude, version 2: everything sold and grown on ReplyInbox, controllable from Claude.

v2_tools(acc, svc) adds tools on top of mcp_tools.tools_for(): Store products, Courses (build from an outline,
coupons, students, grading), Leads and abandoned carts, Payments and payouts, the link-in-bio page and its analytics,
the AI agents, a one-prompt launch, and undo for the last changes Claude made.
agency(acc, svc, read_only) wraps everything for Agency logins: one Claude link for every Instagram account of the
login (each tool takes an optional "account"), plus list_accounts and all_accounts_report.
"""
import json
import re
import time

import agents
import courses
import leads
import pagestats
import plans
import shop
import store
from mcp_protocol import ToolError

_STR = {"type": "string"}
_BOOL = {"type": "boolean"}
_INT = {"type": "integer"}
UNDO_KEEP = 10


# ---------- undo: a snapshot of what a change can touch, taken before every change ----------

def _undo_key(acc_id):
    return store.account_key(acc_id, "mcp_undo")


def snapshot(acc, name, args):
    snap = {"tool": name, "at": int(time.time()), "rules": store.load_rules(acc["id"]), "page": store.load_page(acc["id"]),
            "products": shop.products(acc["id"])}
    cid = str((args or {}).get("course_id") or "")
    if cid and courses.get(cid) and courses.get(cid)["acc"] == acc["id"]:
        snap["course"] = courses.get(cid)
    store.redis("LPUSH", _undo_key(acc["id"]), json.dumps(snap, ensure_ascii=False))
    store.redis("LTRIM", _undo_key(acc["id"]), 0, UNDO_KEEP - 1)


def with_undo(acc, tools):
    """Every tool that changes something saves a snapshot first (so undo_last_change can put it back)."""
    for t in tools:
        if not t.get("read_only") and t["name"] not in ("undo_last_change",):
            fn, name = t["fn"], t["name"]

            def run(args, fn=fn, name=name):
                snapshot(acc, name, args)
                return fn(args)
            t["fn"] = run
    return tools


# ---------- helpers ----------

def _course(acc, cid):
    c = courses.get(str(cid or ""))
    if not c or c["acc"] != acc["id"] or c.get("deleted"):
        raise ToolError("Course not found. Use list_courses for the ids.")
    return c


def _course_view(svc, acc, c, full=False):
    n_mod, n_les = courses.counts(c)
    out = {"course_id": c["id"], "title": c["title"], "status": c["status"], "price_inr": courses.price_now(c),
           "list_price_inr": c.get("price"), "sales": c.get("sales", 0), "revenue_inr": c.get("revenue", 0),
           "students": len(store.redis("SMEMBERS", f"s:enrs:{c['id']}") or []), "modules": n_mod, "lessons": n_les,
           "url": svc.course_public_url(acc, c), "payments_paused": bool(c.get("paused"))}
    if full:
        out.update(description=c.get("desc", ""), button=c.get("button"), benefits=c.get("benefits", []), faqs=c.get("faqs", []),
                   validity=c.get("validity"), coupons=c.get("coupons", []), certificate=(c.get("cert") or {}).get("enabled"),
                   outline=[{"module_id": m["id"], "title": m["title"], "unlock": m.get("unlock"),
                             "lessons": [{"lesson_id": ls["id"], "title": ls["title"], "type": ls["type"], "free_preview": ls.get("free"),
                                          "live": ls.get("live", True)} for ls in m["lessons"]]} for m in c["modules"]])
    return out


def _save_course(acc, c, changes):
    """Applies changes to the whole course through courses.clean (the same checks as the editor)."""
    data = {**c, **changes, "discount": bool(changes.get("sale_price", c.get("sale_price")))}
    try:
        return courses.clean(acc, c["id"], data)
    except courses.CourseError as e:
        raise ToolError(str(e))


def _lessons(raw):
    out = []
    for ls in raw or []:
        if not isinstance(ls, dict) or not str(ls.get("title", "")).strip():
            continue
        kind = ls.get("type") if ls.get("type") in courses.LESSON_TYPES else ("video" if ls.get("video") else "text")
        item = {"type": kind, "title": str(ls["title"])[:150], "body": str(ls.get("body", "")), "video": ls.get("video", ""),
                "free": bool(ls.get("free_preview")), "live": True}
        if kind == "quiz":
            item["questions"] = [{"q": q.get("question", ""), "options": q.get("options", []), "answer": q.get("answer", 0)}
                                 for q in ls.get("questions") or [] if isinstance(q, dict)]
        out.append(item)
    return out


def _modules(raw):
    return [{"title": str(m.get("title", "Module"))[:150], "live": True, "unlock": "now", "lessons": _lessons(m.get("lessons"))}
            for m in raw or [] if isinstance(m, dict)]


def _product_view(svc, acc, p):
    return {"product_id": p["id"], "type": p.get("type", "file"), "title": p["title"], "price_inr": p["price"], "on_sale": p.get("enabled", True),
            "sales": p.get("sales", 0), "revenue_inr": p.get("revenue", 0), "url": f"{svc.site_url()}/{acc.get('username', '')}/p/{p['id']}",
            "when": shop.when_text(p["start"], p.get("minutes", 0)) if p.get("type") == "event" else None}


def _need(acc, feature):
    if not plans.has(acc, feature):
        raise ToolError(plans.upgrade_msg(feature))


# ---------- the tools ----------

def v2_tools(acc, svc, base=None):
    ig = acc["id"]
    raw = {t["name"]: t["fn"] for t in (base or [])}  # before undo wrapping: a launch is one change

    # store
    def list_products(_):
        return {"products": [_product_view(svc, acc, p) for p in shop.products(ig)]}

    def save_product(a):
        data = {"id": a.get("product_id"), "type": a.get("type"), "title": a.get("title"), "price": a.get("price_inr"),
                "desc": a.get("description", ""), "content": a.get("locked_content", ""), "enabled": a.get("on_sale", True),
                "start": a.get("event_start"), "minutes": a.get("minutes"), "capacity": a.get("seats"), "join_url": a.get("join_url"),
                "days": a.get("booking_days"), "from": a.get("booking_from"), "to": a.get("booking_to")}
        cur = shop.get(ig, str(a.get("product_id") or "")) if a.get("product_id") else None
        if cur:  # an update keeps what Claude didn't mention
            data = {**cur, **{k: v for k, v in data.items() if v not in (None, "")}, "id": cur["id"],
                    "from": a.get("booking_from") or (f"{cur['frm'] // 60:02d}:{cur['frm'] % 60:02d}" if cur.get("frm") is not None else None),
                    "to": a.get("booking_to") or (f"{cur['to'] // 60:02d}:{cur['to'] % 60:02d}" if cur.get("to") is not None else None)}
        if (data.get("type") or "file") == "file" and not (cur or {}).get("file_id"):
            raise ToolError("A file product needs its file uploaded in the dashboard (Store → New product). From Claude you can create "
                            "'locked' (text/links unlocked after payment), 'event' or 'booking' products.")
        try:
            p = shop.save_product(acc, data)
        except shop.ShopError as e:
            raise ToolError(str(e))
        return {"saved": _product_view(svc, acc, p), "created": not cur}

    def delete_product(a):
        if not shop.delete_product(acc, str(a.get("product_id", ""))):
            raise ToolError("Product not found.")
        return {"deleted": a.get("product_id")}

    # courses
    def list_courses(_):
        return {"courses": [_course_view(svc, acc, c) for c in courses.of_account(ig) if not c.get("deleted")]}

    def get_course(a):
        return _course_view(svc, acc, _course(acc, a.get("course_id")), full=True)

    def create_course(a):
        try:
            c = courses.create(acc, a.get("title"))
        except courses.CourseError as e:
            raise ToolError(str(e))
        changes = {"desc": a.get("description", ""), "price": a.get("price_inr") or 999, "benefits": a.get("benefits") or [],
                   "faqs": [{"q": f.get("question", ""), "a": f.get("answer", "")} for f in a.get("faqs") or [] if isinstance(f, dict)],
                   "about": a.get("about", ""), "status": "draft"}
        if a.get("sale_price_inr"):
            changes["sale_price"] = a["sale_price_inr"]
        if a.get("modules"):
            changes["modules"] = _modules(a["modules"])
        c = _save_course(acc, c, changes)
        if a.get("publish"):
            c = _save_course(acc, c, {"status": "published"})
        return {"created": _course_view(svc, acc, c, full=True),
                "next": "Videos: add YouTube (unlisted) / Vimeo links with update_course, or upload files in the dashboard editor."}

    def update_course(a):
        c = _course(acc, a.get("course_id"))
        changes = {}
        for src, dst in (("title", "title"), ("description", "desc"), ("button_text", "button"), ("about", "about"),
                         ("price_inr", "price"), ("sale_price_inr", "sale_price"), ("benefits", "benefits")):
            if a.get(src) is not None:
                changes[dst] = a[src]
        if a.get("status") in ("draft", "published", "unpublished"):
            changes["status"] = a["status"]
        if a.get("faqs") is not None:
            changes["faqs"] = [{"q": f.get("question", ""), "a": f.get("answer", "")} for f in a["faqs"] if isinstance(f, dict)]
        mods = [dict(m) for m in c["modules"]]
        if a.get("add_modules"):
            mods += _modules(a["add_modules"])
        for upd in a.get("lesson_updates") or []:  # e.g. set a video link or make a lesson a free preview
            for m in mods:
                for ls in m["lessons"]:
                    if ls["id"] == upd.get("lesson_id"):
                        for k_src, k_dst in (("title", "title"), ("body", "body"), ("video", "video"), ("free_preview", "free"), ("live", "live")):
                            if upd.get(k_src) is not None:
                                ls[k_dst] = upd[k_src]
        changes["modules"] = mods
        if a.get("payments_paused") is not None:
            c["paused"] = bool(a["payments_paused"])
        return {"saved": _course_view(svc, acc, _save_course(acc, c, changes), full=True)}

    def add_coupon(a):
        c = _course(acc, a.get("course_id"))
        coupons = c.get("coupons", []) + [{"code": a.get("code"), "kind": "flat" if a.get("kind") == "flat" else "pct",
                                           "value": a.get("value"), "max": a.get("max_uses") or 0, "on": True}]
        c = _save_course(acc, c, {"coupons": coupons})
        return {"coupons": c["coupons"]}

    def list_students(a):
        c = _course(acc, a.get("course_id"))
        return {"students": [{"email": e["email"], "name": e.get("name", ""), "phone": e.get("phone", ""), "enrolled": e.get("at"),
                              "percent_done": courses.percent(c, e), "access_until": e.get("until")} for e in courses.students(c["id"])][:300]}

    def list_assessments(a):
        out = {"assignments": [], "quizzes": []}
        for c in courses.of_account(ig):
            if a.get("course_id") and c["id"] != a["course_id"]:
                continue
            titles = {ls["id"]: ls["title"] for _, ls in courses.lessons(c, True)}
            for e in courses.students(c["id"]):
                for lid, w in (e.get("work") or {}).items():
                    if not a.get("to_review_only") or not w.get("grade"):
                        out["assignments"].append({"course_id": c["id"], "course": c["title"], "lesson_id": lid, "lesson": titles.get(lid, ""),
                                                   "email": e["email"], "name": e.get("name", ""), "answer": w.get("text", ""),
                                                   "link": w.get("link", ""), "grade": w.get("grade"), "feedback": w.get("feedback", "")})
                for lid, q in (e.get("quiz") or {}).items():
                    out["quizzes"].append({"course": c["title"], "lesson": titles.get(lid, ""), "email": e["email"], **q})
        return out

    def grade_assignment(a):
        c = _course(acc, a.get("course_id"))
        try:
            return {"graded": courses.review_work(c, str(a.get("email", "")).lower(), str(a.get("lesson_id", "")),
                                                  a.get("grade"), a.get("feedback"))}
        except courses.CourseError as e:
            raise ToolError(str(e))

    # leads, carts, payments
    def search_leads(a):
        args = {"segment": a.get("segment", "all"), "q": a.get("query", ""), "item": a.get("bought", ""),
                "min_spent": a.get("min_spent_inr") or 0, "sort": a.get("sort", "new")}
        rows, out = svc.leads_filtered(acc, args)
        counts = {s: sum(1 for p in rows if s in p["segments"]) for s in leads.SEGMENTS}
        keep = ("name", "email", "phone", "username", "followed", "sources", "spent", "last_at")
        return {"total": len(out), "segment_counts": counts,
                "leads": [{**{k: p[k] for k in keep}, "bought": [i["title"] for i in p["items"]],
                           "cart": ({"order_id": p["cart"]["id"], "item": p["cart"]["title"], "price_inr": p["cart"]["price"],
                                     "reminded": bool(p["cart"].get("reminded"))} if p["cart"] else None)}
                          for p in out[:int(a.get("limit") or 50)]]}

    def send_cart_reminder(a):
        _need(acc, "cart_tools")
        try:
            leads.remind(acc, str(a.get("order_id", "")))
        except shop.ShopError as e:
            raise ToolError(str(e))
        return {"sent": True}

    def get_payments(a):
        args = {"period": str(a.get("period", "30")), "item": a.get("product", ""), "from": a.get("from", ""), "to": a.get("to", "")}
        s = svc.payments_summary(acc, args, svc.owner_of(acc))
        return {k: s[k] for k in ("earned", "gross", "count", "change", "payout")} | {
            "transactions": [{k: t.get(k) for k in ("paid_at", "name", "email", "title", "type", "price", "creator_gets")} for t in s["transactions"][:50]],
            "abandoned_checkouts": len(s["abandoned"]), "earned_means": "₹ reaching your bank after the fee and GST"}

    def get_payouts(_):
        return {"payouts": svc.payouts_list(acc)}

    # link in bio
    def get_link_page(a):
        page = store.load_page(ig) or svc.default_page(acc)
        stats = pagestats.report(ig, int(a.get("analytics_days") or 7))
        return {"url": f"{svc.site_url()}/{acc.get('username', '')}", "name": page.get("name"), "bio": page.get("bio"), "theme": page.get("theme"),
                "items": [{"item_id": it["id"], "type": it["type"], "title": it["title"], "url": it["url"], "price": it.get("price"),
                           "featured": it.get("featured"), "shown": it.get("enabled", True)} for it in page.get("items", [])],
                "analytics": {k: stats[k] for k in ("days", "visits", "unique", "clicks", "ctr", "time_to_click", "countries", "sources", "links")}}

    def update_link_page(a):
        page = dict(store.load_page(ig) or svc.default_page(acc))
        items = list(page.get("items") or [])
        for it in a.get("add_items") or []:
            items.insert(0, {"type": "product" if it.get("type") == "product" else "link", "title": it.get("title", ""), "url": it.get("url", ""),
                             "subtitle": it.get("subtitle", ""), "price": it.get("price", ""), "featured": bool(it.get("featured")), "enabled": True})
        if a.get("remove_item_ids"):
            items = [it for it in items if it.get("id") not in set(a["remove_item_ids"])]
        page["items"] = items
        for k in ("name", "bio", "theme", "accent", "layout"):
            if a.get(k) is not None:
                page[k] = a[k]
        if a.get("seo_title") is not None or a.get("seo_description") is not None:
            page["seo"] = {**(page.get("seo") or {}), "title": a.get("seo_title", (page.get("seo") or {}).get("title", "")),
                           "description": a.get("seo_description", (page.get("seo") or {}).get("description", ""))}
        saved = svc.clean_page(page, acc)
        store.save_page(ig, saved)
        return {"saved": True, "items": len(saved["items"]), "url": f"{svc.site_url()}/{acc.get('username', '')}"}

    # agents
    def agent_status(_):
        s = agents.settings(acc)
        return {"lead_qualifier": {"on": s["lead"]["enabled"], "allowed": plans.has(acc, "lead_agent"), "used": agents.used(acc, "lead"), "limit": agents.cap(acc, "lead")},
                "brand_collab": {"on": s["brand"]["enabled"], "allowed": plans.has(acc, "brand_agent"), "used": agents.used(acc, "brand"), "limit": agents.cap(acc, "brand")},
                "hot_leads": agents.leads(acc, "hot")[:20], "new_brand_requests": agents.requests(acc, "new")[:20]}

    def set_brand_request(a):
        r = agents.set_status(acc, str(a.get("chat_id", "")), a.get("status"))
        if not r:
            raise ToolError("Brand request not found, or status isn't new / interested / declined / done.")
        return {"request": r}

    # launch in one prompt
    def launch_offer(a):
        """Creates (or uses) a product or course, a keyword automation that DMs its link, a link-page card and a coupon."""
        done = {}
        if a.get("course_id"):
            c = _course(acc, a["course_id"])
            if c["status"] != "published":
                c = _save_course(acc, c, {"status": "published"})
            url, title, price = svc.course_public_url(acc, c), c["title"], courses.price_now(c)
            done["course"] = c["id"]
            if a.get("coupon_code"):
                c = _save_course(acc, c, {"coupons": c.get("coupons", []) + [{"code": a["coupon_code"], "kind": "pct",
                                                                               "value": a.get("coupon_percent") or 10, "max": 0, "on": True}]})
                done["coupon"] = a["coupon_code"].upper()
        else:
            p = shop.get(ig, str(a.get("product_id", ""))) if a.get("product_id") else None
            if not p:
                try:
                    p = shop.save_product(acc, {"type": "locked", "title": a.get("title"), "price": a.get("price_inr"),
                                                "desc": a.get("description", ""), "content": a.get("locked_content", "")})
                except shop.ShopError as e:
                    raise ToolError(f"{e} (pass product_id or course_id to launch something that exists, or locked_content for a new product)")
            url, title, price = _product_view(svc, acc, p)["url"], p["title"], p["price"]
            done["product"] = p["id"]
        keyword = re.sub(r"[^A-Za-z0-9]", "", str(a.get("keyword", ""))).upper()
        if keyword:
            dm = a.get("dm") or f"{{Hi|Hey}} {{username}}! Here's {title} 👉 {url}" + (f"\nUse code {done['coupon']} for {a.get('coupon_percent') or 10}% off 🎁" if done.get("coupon") else "")
            fns = raw
            if "save_automation" not in fns:
                raise ToolError("Automations can't be changed on this connection.")
            target = str(a.get("reel_id") or "next_post")
            r = fns["save_automation"]({"target": target, "keywords": [keyword], "final_dm": dm, "require_follow": bool(a.get("followers_only", True)),
                                        "label": f"Launch: {title}"[:60]})
            done["automation"] = r["saved"].get("automation_id") or target
            fns["save_automation"]({"target": "keyword", "keywords": [keyword], "final_dm": dm, "dm_only": True, "label": f"{keyword} (DM)"})
            done["dm_keyword"] = keyword
        if a.get("add_to_link_page", True):
            page = dict(store.load_page(ig) or svc.default_page(acc))
            items = list(page.get("items") or [])
            if not any(it.get("url") == url for it in items):
                items.insert(0, {"type": "product", "title": title, "url": url, "price": f"₹{price}", "featured": True, "enabled": True})
                store.save_page(ig, svc.clean_page({**page, "items": items}, acc))
            done["link_page"] = True
        return {"launched": title, "url": url, "price_inr": price, **done,
                "tell_them": f"Post the reel and ask people to comment {keyword}." if keyword else ""}

    # undo
    def list_changes(_):
        raw = store.redis("LRANGE", _undo_key(ig), 0, UNDO_KEEP - 1) or []
        return {"changes": [{"tool": s["tool"], "at": s["at"]} for s in (json.loads(x) for x in raw)],
                "note": "undo_last_change puts automations, the link page, products (and a course it touched) back as they were before the newest one."}

    def undo_last_change(_):
        got = store.redis("LRANGE", _undo_key(ig), 0, 0) or []
        if not got:
            raise ToolError("Nothing to undo.")
        raw = got[0]
        store.redis("LTRIM", _undo_key(ig), 1, -1)
        s = json.loads(raw)
        store.save_rules(ig, s["rules"])
        if s.get("page") is not None:
            store.save_page(ig, s["page"])
        else:  # there was no saved page yet: back to the default one
            store.redis("DEL", store.account_key(ig, "page"))
        store.set_json(shop._key(ig), s["products"])
        if s.get("course"):
            store.set_json(f"s:course:{s['course']['id']}", s["course"])
        store.log_activity(ig, "", "Claude", "undo", "claude", "ok", f"Undid {s['tool']}")
        return {"undone": s["tool"], "from": s["at"], "note": "Messages already sent and emails already delivered can't be taken back."}

    S = _STR
    tools = [
        # store
        {"name": "list_products", "title": "Store products", "read_only": True, "fn": list_products,
         "description": "Store products (file, locked content, event tickets, 1:1 bookings) with price, sales, ₹ revenue and link.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "save_product", "title": "Create or update a Store product", "fn": save_product,
         "description": "Creates or updates a Store product sold with UPI/cards (money to the creator's bank). Types from Claude: 'locked' "
                        "(text/links unlocked after payment), 'event' (ticket, needs event_start), 'booking' (1:1 calls, needs booking_days + hours). "
                        "File products need the file uploaded in the dashboard. Updates keep fields left out.",
         "input_schema": {"type": "object", "properties": {
             "product_id": S, "type": {"type": "string", "enum": ["locked", "event", "booking", "file"]}, "title": S, "price_inr": _INT,
             "description": S, "locked_content": S, "on_sale": _BOOL, "event_start": {"type": "string", "description": "e.g. 2026-12-05T19:30 (India time)"},
             "minutes": _INT, "seats": _INT, "join_url": S, "booking_days": {"type": "array", "items": {"type": "integer", "minimum": 0, "maximum": 6},
                                                                           "description": "0 = Monday … 6 = Sunday"},
             "booking_from": {"type": "string", "description": "HH:MM"}, "booking_to": {"type": "string", "description": "HH:MM"}}}},
        {"name": "delete_product", "title": "Delete a Store product", "destructive": True, "fn": delete_product,
         "description": "Deletes a Store product (its page stops selling; past buyers keep access). Ask first.",
         "input_schema": {"type": "object", "required": ["product_id"], "properties": {"product_id": S}}},
        # courses
        {"name": "list_courses", "title": "Courses", "read_only": True, "fn": list_courses,
         "description": "Every course with status, price, students, sales, ₹ revenue and its sales page link.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "get_course", "title": "Course details", "read_only": True, "fn": get_course,
         "description": "One course: description, benefits, FAQs, coupons and the full outline (module and lesson ids).",
         "input_schema": {"type": "object", "required": ["course_id"], "properties": {"course_id": S}}},
        {"name": "create_course", "title": "Create a course", "fn": create_course,
         "description": "Builds a course from an outline: modules with lessons (video link, text, quiz), price, sale price, description, "
                        "benefits and FAQs. Created as a draft unless publish=true (publish only on the creator's say-so).",
         "input_schema": {"type": "object", "required": ["title"], "properties": {
             "title": S, "description": S, "price_inr": _INT, "sale_price_inr": _INT, "about": S, "publish": _BOOL,
             "benefits": {"type": "array", "items": S}, "faqs": {"type": "array", "items": {"type": "object", "properties": {"question": S, "answer": S}}},
             "modules": {"type": "array", "items": {"type": "object", "required": ["title"], "properties": {
                 "title": S, "lessons": {"type": "array", "items": {"type": "object", "required": ["title"], "properties": {
                     "title": S, "type": {"type": "string", "enum": ["video", "text", "quiz", "assignment"]}, "body": S,
                     "video": {"type": "string", "description": "YouTube (unlisted) / Vimeo / Loom / Drive link"}, "free_preview": _BOOL,
                     "questions": {"type": "array", "items": {"type": "object", "properties": {
                         "question": S, "options": {"type": "array", "items": S}, "answer": {"type": "integer", "description": "index of the right option"}}}}}}}}}}}}},
        {"name": "update_course", "title": "Change a course", "fn": update_course,
         "description": "Changes a course: title, description, price, sale price, benefits, FAQs, status (draft/published/unpublished), pause "
                        "payments, add modules with lessons, or update lessons by lesson_id (e.g. set the video link, free preview).",
         "input_schema": {"type": "object", "required": ["course_id"], "properties": {
             "course_id": S, "title": S, "description": S, "button_text": S, "about": S, "price_inr": _INT, "sale_price_inr": _INT,
             "benefits": {"type": "array", "items": S}, "faqs": {"type": "array", "items": {"type": "object", "properties": {"question": S, "answer": S}}},
             "status": {"type": "string", "enum": ["draft", "published", "unpublished"]}, "payments_paused": _BOOL,
             "add_modules": {"type": "array", "items": {"type": "object"}},
             "lesson_updates": {"type": "array", "items": {"type": "object", "required": ["lesson_id"], "properties": {
                 "lesson_id": S, "title": S, "body": S, "video": S, "free_preview": _BOOL, "live": _BOOL}}}}}},
        {"name": "add_coupon", "title": "Add a course coupon", "fn": add_coupon,
         "description": "Adds a discount code to a course: kind pct (percent) or flat (₹), optional max_uses.",
         "input_schema": {"type": "object", "required": ["course_id", "code", "value"], "properties": {
             "course_id": S, "code": S, "kind": {"type": "string", "enum": ["pct", "flat"]}, "value": _INT, "max_uses": _INT}}},
        {"name": "list_students", "title": "Course students", "read_only": True, "fn": list_students,
         "description": "Students of a course with email, phone, % done and access end date.",
         "input_schema": {"type": "object", "required": ["course_id"], "properties": {"course_id": S}}},
        {"name": "list_assessments", "title": "Assignments and quiz results", "read_only": True, "fn": list_assessments,
         "description": "Assignment answers (with grade/feedback) and quiz scores across courses; to_review_only for ungraded ones.",
         "input_schema": {"type": "object", "properties": {"course_id": S, "to_review_only": _BOOL}}},
        {"name": "grade_assignment", "title": "Grade an assignment", "fn": grade_assignment,
         "description": "Saves a grade and feedback on a student's assignment (the student sees it on the lesson).",
         "input_schema": {"type": "object", "required": ["course_id", "email", "lesson_id", "grade"], "properties": {
             "course_id": S, "email": S, "lesson_id": S, "grade": S, "feedback": S}}},
        # leads and money
        {"name": "search_leads", "title": "Leads", "read_only": True, "fn": search_leads,
         "description": "Everyone merged by email (Instagram contacts, link-page signups, buyers, students, abandoned carts). Segments: all, "
                        "customers, instagram, followers, subscribers, carts. Filter by query, bought item, min spend; sort new/old/az/za/spent.",
         "input_schema": {"type": "object", "properties": {
             "segment": {"type": "string", "enum": list(leads.SEGMENTS)}, "query": S, "bought": S, "min_spent_inr": _INT,
             "sort": {"type": "string", "enum": ["new", "old", "az", "za", "spent"]}, "limit": {"type": "integer", "minimum": 1, "maximum": 200}}}},
        {"name": "send_cart_reminder", "title": "Remind an abandoned checkout", "destructive": True, "fn": send_cart_reminder,
         "description": "Emails a person who started a checkout but didn't pay a 'complete my purchase' link (once per cart). Sends a real email: ask first.",
         "input_schema": {"type": "object", "required": ["order_id"], "properties": {"order_id": S}}},
        {"name": "get_payments", "title": "Payments", "read_only": True, "fn": get_payments,
         "description": "Store + Course earnings for a period (today, yesterday, 7, 30, 90, life, custom with from/to YYYY-MM-DD) and product: "
                        "₹ earned (after fees), paid by buyers, % change vs the period before, transactions, abandoned checkouts, payout account status.",
         "input_schema": {"type": "object", "properties": {"period": {"type": "string", "enum": ["today", "yesterday", "7", "30", "90", "life", "custom"]},
                                                           "product": S, "from": S, "to": S}}},
        {"name": "get_payouts", "title": "Payouts to the bank", "read_only": True, "fn": get_payouts,
         "description": "The creator's share of each recent sale and whether it has reached their bank (completed / processing / on_hold / failed).",
         "input_schema": {"type": "object", "properties": {}}},
        # link in bio
        {"name": "get_link_page", "title": "Link in bio", "read_only": True, "fn": get_link_page,
         "description": "The link-in-bio page (items, theme) and its analytics: visits, unique, clicks, CTR, time to click, countries, sources, top links.",
         "input_schema": {"type": "object", "properties": {"analytics_days": {"type": "integer", "minimum": 1, "maximum": 90}}}},
        {"name": "update_link_page", "title": "Change the link in bio", "fn": update_link_page,
         "description": "Adds items (link or product cards, optionally featured), removes items by id, or changes name, bio, theme "
                        "(studio, sunset, midnight, ocean, candy, mono), brand colour (#RRGGBB), layout (single/two) and SEO title/description.",
         "input_schema": {"type": "object", "properties": {
             "add_items": {"type": "array", "items": {"type": "object", "required": ["title", "url"], "properties": {
                 "title": S, "url": S, "type": {"type": "string", "enum": ["link", "product"]}, "subtitle": S, "price": S, "featured": _BOOL}}},
             "remove_item_ids": {"type": "array", "items": S}, "name": S, "bio": S, "theme": S, "accent": S,
             "layout": {"type": "string", "enum": ["single", "two"]}, "seo_title": S, "seo_description": S}}},
        # agents
        {"name": "get_agents", "title": "AI agents", "read_only": True, "fn": agent_status,
         "description": "Lead Qualifier and Brand Collab: on/off, usage this month, hot leads and new brand requests.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "set_brand_request", "title": "Sort a brand request", "fn": set_brand_request,
         "description": "Moves a brand request to interested, declined, done or back to new.",
         "input_schema": {"type": "object", "required": ["chat_id", "status"], "properties": {
             "chat_id": S, "status": {"type": "string", "enum": ["new", "interested", "declined", "done"]}}}},
        # launch + undo
        {"name": "launch_offer", "title": "Launch an offer in one go", "fn": launch_offer,
         "description": "One step launch: uses a course (course_id) or Store product (product_id), or creates a locked-content product "
                        "(title, price_inr, locked_content); publishes it; adds a comment keyword automation (reel_id or next_post) plus "
                        "the same keyword in DMs that sends the link; puts a featured card on the link page; optional course coupon. "
                        "Show the plan to the creator first.",
         "input_schema": {"type": "object", "properties": {
             "course_id": S, "product_id": S, "title": S, "price_inr": _INT, "description": S, "locked_content": S,
             "keyword": {"type": "string", "description": "The comment word, e.g. PROMPTS"}, "reel_id": S, "dm": S,
             "followers_only": _BOOL, "add_to_link_page": _BOOL, "coupon_code": S, "coupon_percent": _INT}}},
        {"name": "list_changes", "title": "Recent changes by Claude", "read_only": True, "fn": list_changes,
         "description": "The last changes made through Claude that undo_last_change can reverse.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "undo_last_change", "title": "Undo the last change", "fn": undo_last_change,
         "description": "Puts automations, the link page, Store products and a touched course back as they were before the newest change "
                        "made through Claude. Sent DMs/emails can't be unsent.",
         "input_schema": {"type": "object", "properties": {}}},
    ]
    return tools


def all_tools(acc, svc, read_only=False):
    """v1 + v2 tools for one account, with undo snapshots on every change."""
    import mcp_tools
    base = mcp_tools.tools_for(acc, svc, read_only=read_only)
    extra = v2_tools(acc, svc, base)
    if read_only:
        extra = [t for t in extra if t.get("read_only")]
    else:
        for t in extra:
            if not t.get("read_only"):
                t["fn"] = mcp_tools._audited(acc, t["name"], t["fn"])
    return with_undo(acc, base + extra)


def agency(acc, svc, accounts, read_only=False):
    """One Claude link for every Instagram account of an Agency login: each tool takes an optional "account" (username or id)."""
    by_name = {(a.get("username") or "").lower(): a for a in accounts}
    by_id = {a["id"]: a for a in accounts}
    cache = {}

    def tools_of(a):
        if a["id"] not in cache:
            cache[a["id"]] = {t["name"]: t for t in all_tools(a, svc, read_only)}
        return cache[a["id"]]

    def pick(args):
        ref = str((args or {}).pop("account", "") or "").lstrip("@").lower()
        if not ref:
            return acc
        a = by_name.get(ref) or by_id.get(ref)
        if not a:
            raise ToolError(f"No account '{ref}' on this login. Use list_accounts.")
        return a

    base = list(tools_of(acc).values())
    out = []
    for t in base:
        name = t["name"]

        def run(args, name=name):
            target = pick(args)
            tool = tools_of(target).get(name)
            if not tool:
                raise ToolError(f"{name} isn't available for @{target.get('username')}.")
            return {"account": target.get("username"), **(tool["fn"](args) or {})}
        schema = json.loads(json.dumps(t["input_schema"]))
        schema.setdefault("properties", {})["account"] = {"type": "string", "description": "Which Instagram account (username); default: "
                                                                                             f"@{acc.get('username')}"}
        out.append({**t, "fn": run, "input_schema": schema})

    def list_accounts(_):
        return {"accounts": [{"username": a.get("username"), "id": a["id"], "plan": plans.plan_of(a), "followers": a.get("followers")} for a in accounts]}

    def report(a):
        rows = []
        for x in accounts:
            t = tools_of(x)
            try:
                summ = t["get_account_summary"]["fn"]({})
            except Exception as e:  # one broken account shouldn't stop the report
                summ = {"error": str(e)[:120]}
            try:
                pay = t["get_payments"]["fn"]({"period": str(a.get("period") or "7")})
                money = {k: pay.get(k) for k in ("earned", "count", "change")}
            except Exception:
                money = {}
            rows.append({"account": x.get("username"), "summary": summ, "store_and_courses": money})
        return {"accounts": rows}

    out += [{"name": "list_accounts", "title": "Accounts on this login", "read_only": True, "fn": list_accounts,
             "description": "Every Instagram account this Agency link can manage. Pass account=<username> to any tool.",
             "input_schema": {"type": "object", "properties": {}}},
            {"name": "all_accounts_report", "title": "Report across all accounts", "read_only": True, "fn": report,
             "description": "Each account's overview (DMs, leads, follows, sales, problems) and Store/Course earnings for the period, "
                            "for a client report or a quick check of everything at once.",
             "input_schema": {"type": "object", "properties": {"period": {"type": "string", "enum": ["7", "30", "90"]}}}}]
    return out


def prompts():
    """New ready-made requests (added to mcp_tools.prompts())."""
    return [
        {"name": "launch_product", "title": "Launch a product",
         "description": "Create the offer, its comment keyword automation, a link-page card and a coupon, in one go.",
         "arguments": [{"name": "what", "description": "What you're selling", "required": True},
                       {"name": "price", "description": "Price in ₹", "required": False},
                       {"name": "keyword", "description": "Comment keyword", "required": False}],
         "render": lambda a: (
             f"Launch '{a['what']}'" + (f" at ₹{a['price']}" if a.get("price") else "") + (f" with the keyword {a['keyword']}" if a.get("keyword") else "") +
             ". Check list_courses and list_products for something that already exists. Then show me the plan: the product or course, "
             "the DM text, keyword, link-page card and an optional launch coupon. After I say yes, do it with launch_offer and tell me what to post.")},
        {"name": "recover_carts", "title": "Recover abandoned carts",
         "description": "Find people who started paying but didn't, and win them back.",
         "render": lambda a: (
             "Use search_leads with segment carts. Show me each person, what they left and how long ago. Suggest who to remind first, "
             "then send_cart_reminder only for the ones I approve. Also suggest a WhatsApp line I can send myself to the ones with a phone number.")},
        {"name": "brand_deals", "title": "Reply to brand deals",
         "description": "Go through brand requests from your DMs and draft replies.",
         "render": lambda a: (
             "Use get_agents to see new brand requests. For each: summarise brand, offer, budget and fit in one line, and draft a short reply "
             "(ask for missing details, or a polite no for a poor fit). Show me all drafts; send with reply_in_dm only after I approve, then "
             "set_brand_request to interested or declined.")},
        {"name": "course_from_topic", "title": "Build a course",
         "description": "Plan a course outline with lessons, quizzes and pricing, then create it as a draft.",
         "arguments": [{"name": "topic", "description": "What the course teaches", "required": True},
                       {"name": "price", "description": "Price in ₹", "required": False}],
         "render": lambda a: (
             f"Design a course on '{a['topic']}'" + (f" priced at ₹{a['price']}" if a.get("price") else "") + ": 4–6 modules, 3–5 short lessons "
             "each (mostly video placeholders, one quiz per module), a sales description, 5 benefits and 4 FAQs. Show me the outline first; "
             "after my yes, call create_course (as a draft) and tell me where to add the videos.")},
        {"name": "client_report", "title": "Client report (Agency)",
         "description": "A short report for every client account.",
         "render": lambda a: (
             "Use all_accounts_report for the last 7 days. For each account write a short client-ready report: DMs, followers won, leads, "
             "sales and earnings with % change, the best automation, any problem, and 2 next steps. Keep each under 120 words.")},
    ]
