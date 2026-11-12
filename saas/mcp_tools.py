"""What Claude can do on one ReplyInbox account (see the /mcp route in app.py).

tools_for(acc, svc) returns the tools; prompts() returns the ready-made requests shown in Claude.
svc carries app.py functions (save_rule, rule_insights, sales_summary, broadcast_batch, ...) so the dashboard and
Claude share one implementation and the same checks. Tool names from the first version are kept.
"""
import json
import re
import secrets
import time
from datetime import datetime, timedelta, timezone

import ai_agent
import engine
import push
import store
from mcp_protocol import ToolError

_STR = {"type": "string"}
_BOOL = {"type": "boolean"}
_INT = {"type": "integer"}
IST = timezone(timedelta(hours=5, minutes=30))

TARGETS = {"all": "*", "next_post": "next", "story_replies": "story:reply", "story_mentions": "story:mention", "live": "live"}
KIND = {"*": "comments on any post", "next": "comments on your next post", "story:reply": "story replies",
        "story:mention": "story mentions", "live": "comments on your Live"}
# save_rule fields Claude may set as they are (see save_automation's schema)
PASS = ("comment_reply", "opening_dm", "opening_dm_b", "button_text", "require_follow", "follow_dm", "followed_button_text",
        "dm_button_text", "dm_button_url", "replies_on", "exclude", "menu", "track_links", "once_per_person", "delay_min",
        "tags", "ask_email", "email_dm", "email_required", "ask_phone", "phone_dm", "phone_required", "followup_on",
        "followup_hours", "followup_dm", "followup_button", "followup_url", "label")
STAT_FIELDS = ("runs", "clicks", "link_clicks", "follows", "leads", "sales", "revenue")


def kind_of(key, rule):
    if engine.is_keyword_rule(key):
        return "keyword in a DM" if rule.get("comments") is False else "keyword in comments on any post, or in a DM"
    return KIND.get(key) or "comments on one post or reel"


def when(ts):
    return datetime.fromtimestamp(ts, IST).strftime("%Y-%m-%d %H:%M IST") if ts else None


def as_ts(value):
    """Unix seconds from a number or an ISO date/time (India time when no zone is given); 0 for empty."""
    if value in (None, "", 0):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    try:
        dt = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        raise ToolError(f"Couldn't read the time {value!r}. Use e.g. 2026-11-20T18:00 (India time).")
    return int((dt if dt.tzinfo else dt.replace(tzinfo=IST)).timestamp())


def _stats(st):
    out = {f: st.get(f, 0) for f in STAT_FIELDS}
    out["link_open_rate"] = round(out["link_clicks"] / out["runs"], 3) if out["runs"] else None
    out["sales_per_link_open"] = round(out["sales"] / out["link_clicks"], 3) if out["link_clicks"] else None
    return out


def _rule_view(key, r, st=None, full=False):
    view = {"automation_id": key, "name": r.get("label") or ", ".join(r.get("keywords") or []) or KIND.get(key, key),
            "trigger": kind_of(key, r), "enabled": r.get("enabled", True) is not False, "keywords": r.get("keywords", []),
            "final_dm": r.get("dm", ""), "require_follow": bool(r.get("require_follow")),
            "collects": [x for x, on in (("email", r.get("ask_email")), ("whatsapp", r.get("ask_phone"))) if on],
            "menu_options": [m.get("title") for m in r.get("menu") or []], "followup": bool(r.get("followup_on")),
            "auto_setup": bool(r.get("auto"))}
    if st is not None:
        view["stats_all_time"] = _stats(st)
    if full:
        view["settings"] = {k: r.get(k) for k in PASS + ("dm", "starts_at", "ends_at", "comments")}
        view["settings"]["starts_at"], view["settings"]["ends_at"] = when(r.get("starts_at")), when(r.get("ends_at"))
    return view


def tools_for(acc, svc, read_only=False):
    ig_id = acc["id"]

    def rules():
        return store.load_rules(ig_id).get("reels", {})

    def need_rule(args):
        key = str(args.get("automation_id", ""))
        if key not in rules():
            raise ToolError("No automation with that id. Use list_automations.")
        return key

    def report(fresh=False):
        try:
            return svc.build_report(acc, fresh)
        except RuntimeError as e:
            raise ToolError(f"Instagram didn't answer: {e}")

    # ---------- overview ----------

    def summary(_):
        c = store.counts(ig_id)
        r = rules()
        last30 = store.days(ig_id, 30)
        s30 = lambda *f: sum(d.get(x, 0) for _, d in last30 for x in f)
        return {"account": "@" + str(acc.get("username")), "followers": acc.get("followers"),
                "plan": "pro" if store.is_pro(acc) else "free",
                "dms_this_month": c.get(f"dms:{engine.month()}", 0), "monthly_dm_limit": engine.monthly_limit(acc) or "no limit",
                "last_30_days": {"dms": s30("dms"), "leads": s30("emails", "phones", "page_signups"), "follows_won": s30("gate_follows"),
                                 "link_opens": s30("link_clicks"), "sales": s30("sales"), "revenue_inr": s30("revenue")},
                "all_time": {"dms": c.get("dms", 0), "links_sent": c.get("links_sent", 0), "follows_won": c.get("gate_follows", 0),
                             "sales": c.get("sales", 0), "revenue_inr": c.get("revenue", 0)},
                "automations_on": sum(1 for x in r.values() if x.get("enabled", True) is not False), "automations_total": len(r),
                "ai_agent_on": ai_agent.settings(acc)["enabled"], "chats_waiting_for_you":
                    sum(1 for t in ai_agent.threads(ig_id) if t.get("status") == "needs_you"),
                "refused_dms_waiting_for_retry": len(engine.pending_retries(acc)),
                "phones_with_notifications": push.devices(ig_id), "paused": bool(acc.get("paused")),
                "problem": {"logged_out": "Instagram logged the account out: log in again in the dashboard",
                            "rate_limited": "Instagram is slowing DMs for a while; it continues by itself"}.get(engine.is_blocked(acc))}

    def trends(args):
        n = max(1, min(int(args.get("days") or 7), 30))
        rows = store.days(ig_id, 2 * n)
        fields = {"dms": ("dms",), "leads": ("emails", "phones", "page_signups"), "follows_won": ("gate_follows",),
                  "link_opens": ("link_clicks",), "sales": ("sales",), "revenue_inr": ("revenue",), "comment_replies": ("comment_replies",)}
        total = lambda part, fs: sum(d.get(f, 0) for _, d in part for f in fs)
        out = {}
        for name, fs in fields.items():
            now, before = total(rows[n:], fs), total(rows[:n], fs)
            out[name] = {"this_period": now, "previous_period": before,
                         "change_pct": round(100 * (now - before) / before) if before else None}
        return {"period_days": n, "this_period": f"{rows[n][0]} to {rows[-1][0]}", "metrics": out,
                "per_day": [{"date": d, **{k: sum(v.get(f, 0) for f in fs) for k, fs in fields.items()}} for d, v in rows[n:]]}

    def best_times(_):
        hours = [0] * 24
        for key in rules():
            for h, v in enumerate(store.rule_hours(ig_id, key)):
                hours[h] += v
        if not any(hours):
            return {"note": "Not enough activity yet. Numbers build up as automations run."}
        top = sorted(range(24), key=lambda h: -hours[h])[:3]
        name = lambda h: f"{h % 12 or 12} {'am' if h < 12 else 'pm'}"
        return {"timezone": "India (IST)", "busiest_hours": [name(h) for h in top],
                "suggestion": f"Post 30–60 minutes before {name(top[0])}, when your audience comments and DMs most.",
                "activity_by_hour": {name(h): hours[h] for h in range(24)}}

    def list_reels(args):
        rows = report()["reels"][: int(args.get("limit") or 12)]
        return {"reels": [{k: r.get(k) for k in ("id", "caption", "timestamp", "views", "comments", "has_rule",
                                                  "keywords", "per_1k", "permalink")} for r in rows]}

    def reel_report(args):
        data = report(bool(args.get("refresh")))
        rid = str(args.get("reel_id") or "")
        if rid:
            row = next((r for r in data["reels"] if r["id"] == rid), None)
            if not row:
                raise ToolError("That reel isn't among the latest 12 reels.")
            return row
        return {"avg_follows_per_1k_views": data.get("avg_per_1k"), "reels": data["reels"]}

    # ---------- automations ----------

    def list_automations(args):
        r = rules()
        st = store.rule_stats(ig_id, r.keys())
        rows = [_rule_view(k, v, st.get(k, {})) for k, v in r.items()]
        sort = args.get("sort_by")
        if sort in STAT_FIELDS:
            rows.sort(key=lambda x: -x["stats_all_time"][sort])
        elif sort == "conversion":
            rows.sort(key=lambda x: -(x["stats_all_time"]["sales_per_link_open"] or 0))
        return {"automations": rows}

    def get_automation(args):
        key = need_rule(args)
        return _rule_view(key, rules()[key], store.rule_stats(ig_id, [key])[key], full=True)

    def insights(args):
        key = need_rule(args)
        data = svc.rule_insights(acc, key)
        name = lambda h: f"{h % 12 or 12} {'am' if h < 12 else 'pm'}"
        l30 = data["last30"]
        funnel = [("got the DM", l30["runs"]), ("opened the link", l30["link_clicks"]), ("followed", l30["follows"]),
                  ("shared email/phone", l30["leads"]), ("bought", l30["sales"])]
        return {"automation_id": key, "last_30_days": l30, "all_time": data["total"],
                "funnel_30_days": [{"step": s, "people": n, "pct_of_dms": round(100 * n / l30["runs"]) if l30["runs"] else None}
                                   for s, n in funnel],
                "busiest_hours_ist": [name(h) for h in data["best_hours"]], "menu_option_picks": data["menu"],
                "per_day": [d for d in data["daily"] if any(d[f] for f in STAT_FIELDS)]}

    def save_automation(args):
        target = str(args.get("target") or "").strip()
        keywords = [str(k).strip() for k in args.get("keywords") or [] if str(k).strip()]
        if target == "keyword":
            if not keywords:
                raise ToolError("A keyword automation needs at least one keyword.")
            key = "kw:" + re.sub(r"[^A-Za-z0-9_]", "", keywords[0].upper().replace(" ", "_"))[:32]
        elif target in TARGETS:
            key = TARGETS[target]
        elif target.isdigit():
            key = target
        elif target in rules():
            key = target
        else:
            raise ToolError('target must be a reel id (from list_reels), an automation_id, or one of: "keyword", "all", '
                            '"next_post", "story_replies", "story_mentions", "live".')
        old = rules().get(key, {})
        new = not old
        data = dict(old)  # updating keeps everything Claude didn't mention
        for field in PASS:
            if args.get(field) is not None:
                data[field] = args[field]
        if args.get("final_dm") is not None:
            data["dm"] = args["final_dm"]
        for f in ("starts_at", "ends_at"):
            if f in args:
                data[f] = as_ts(args[f])
        if engine.is_keyword_rule(key) and args.get("dm_only") is not None:
            data["comments"] = not args["dm_only"]
        data["keywords"] = keywords or old.get("keywords", [])
        comment_based = key not in ("story:reply", "story:mention") and not (engine.is_keyword_rule(key) and data.get("comments") is False)
        if new:
            data.setdefault("comment_reply", engine.DEFAULT_COMMENT_REPLY if comment_based and key != "live" else "")
            data.setdefault("require_follow", comment_based)
            data.setdefault("once_per_person", comment_based)
        if args.get("followup_dm") and args.get("followup_on") is None:
            data["followup_on"] = True
        data["enabled"] = args.get("enabled", old.get("enabled", True)) is not False
        try:
            saved = svc.save_rule(acc, key, data)
        except ValueError as e:
            raise ToolError(str(e))
        return {"saved": _rule_view(key, saved["reels"][key], full=True), "created": new}

    def duplicate(args):
        key = need_rule(args)
        targets = []
        for t in args.get("to") or []:
            t = str(t).strip()
            targets.append(TARGETS.get(t) or (t if t.isdigit() or t.startswith("kw:") else "kw:" + re.sub(r"[^A-Za-z0-9_]", "", t.upper())[:32]))
        if not targets:
            raise ToolError("Say where to copy it: reel ids, keywords, or next_post.")
        try:
            done, skipped = svc.copy_rule(acc, key, targets, bool(args.get("replace")))
        except ValueError as e:
            raise ToolError(str(e))
        return {"copied_to": done, "skipped_already_exist": skipped}

    def set_enabled(args):
        key = need_rule(args)
        data = store.load_rules(ig_id)
        data["reels"][key]["enabled"] = bool(args.get("enabled"))
        store.save_rules(ig_id, data)
        return {"automation_id": key, "enabled": data["reels"][key]["enabled"]}

    def delete(args):
        key = need_rule(args)
        svc.delete_rule(acc, key)
        return {"deleted": key}

    def pause(args):
        fresh = store.load_account(ig_id) or acc
        fresh["paused"] = bool(args.get("paused"))
        store.save_account(fresh)
        return {"paused": fresh["paused"]}

    def send_past(args):
        rid = str(args.get("reel_id", ""))
        if not rid.isdigit():
            raise ToolError("reel_id must be a reel id from list_reels.")
        try:
            return engine.backfill_comments(acc, rid)
        except RuntimeError as e:
            raise ToolError(str(e)[:300])

    def retry(_):
        return {**engine.retry_failed_dms(acc), "waiting": len(engine.pending_retries(acc))}

    def activity(args):
        items = store.recent_activity(ig_id, 500)
        if args.get("errors_only"):
            items = [a for a in items if a.get("status") == "error"]
        if args.get("action"):
            items = [a for a in items if a.get("action") == args["action"]]
        items = items[: min(int(args.get("limit") or 20), 100)]
        return {"activity": [{k: a.get(k) for k in ("at", "username", "comment", "action", "status", "detail")} for a in items]}

    # ---------- money ----------

    def sales(_):
        s = svc.sales_summary(acc)
        names = {k: _rule_view(k, v)["name"] for k, v in rules().items()}
        last30 = s["daily"]
        return {"all_time": {"sales": s["sales"], "revenue_inr": s["revenue"], "dm_link_opens": s["link_clicks"]},
                "last_30_days": {"sales": sum(d["sales"] for d in last30), "revenue_inr": sum(d["revenue"] for d in last30)},
                "by_automation": sorted([{"automation_id": k, "name": names.get(k, "deleted automation"), **v}
                                         for k, v in s["by_rule"].items()], key=lambda x: -x["revenue"]),
                "products": [{k: p[k] for k in ("id", "name", "price", "link")} for p in s["products"]],
                "recent_sales": [{"product": x["product"], "price_inr": x["price"], "automation": names.get(x["key"]) if x["key"] else None,
                                  "at": when(x["at"])} for x in s["recent"][:10]],
                "utm_tags_on": s["utm"],
                "how_tracking_works": "Each product has a sales link; the creator sets it as the payment page's redirect after "
                                      "payment. The sale is credited to the last DM link the buyer tapped."}

    def add_product(args):
        try:
            prod = svc.add_product(store.load_account(ig_id) or acc, args)
        except ValueError as e:
            raise ToolError(str(e))
        return {"product": prod, "next_step": "Paste the link as the payment page's 'redirect after payment' URL."}

    def delete_product(args):
        fresh = store.load_account(ig_id) or acc
        pid = str(args.get("product_id", ""))
        if not any(p["id"] == pid for p in engine.products(fresh)):
            raise ToolError("No product with that id. Use get_sales.")
        fresh["products"] = [p for p in engine.products(fresh) if p["id"] != pid]
        store.save_account(fresh)
        store.redis("DEL", f"s:prod:{pid}")
        return {"deleted": pid}

    # ---------- people ----------

    def search_contacts(args):
        q = str(args.get("query") or "").strip().lower()
        tag = str(args.get("tag") or "").strip().lower()
        rows = store.contacts(ig_id)
        out = []
        for c in rows:
            if tag and tag not in (c.get("tags") or []):
                continue
            if args.get("has_email") and not c.get("email"):
                continue
            if args.get("has_phone") and not c.get("phone"):
                continue
            if args.get("followed") and not c.get("followed"):
                continue
            if q and q not in " ".join(str(c.get(k, "")) for k in ("username", "email", "phone", "keyword")).lower() \
                    and q not in (c.get("tags") or []):
                continue
            out.append(c)
        tags = {}
        for c in rows:
            for t in c.get("tags") or []:
                tags[t] = tags.get(t, 0) + 1
        limit = max(1, min(int(args.get("limit") or 25), 200))
        return {"total_contacts": len(rows), "matches": len(out), "tags": tags,
                "contacts": [{"contact_id": store.contact_key(c.get("username"), c.get("igsid", "")), "username": c.get("username"),
                              "email": c.get("email") or None, "phone": c.get("phone") or None, "followed": bool(c.get("followed")),
                              "keyword": c.get("keyword"), "tags": c.get("tags") or [], "interactions": c.get("interactions", 0),
                              "last_seen": when(c.get("last_at"))} for c in out[:limit]]}

    def tag_contacts(args):
        ids = [str(x).strip().lstrip("@").lower() for x in args.get("contact_ids") or [] if str(x).strip()][:500]
        add = [str(t) for t in args.get("add_tags") or []]
        remove = {str(t).strip().lower() for t in args.get("remove_tags") or []}
        done, missing = [], []
        for cid in ids:
            raw = store.redis("HGET", store.account_key(ig_id, "contacts"), cid)
            if not raw:
                missing.append(cid)
                continue
            current = json.loads(raw).get("tags") or []
            store.set_contact_tags(ig_id, cid, [t for t in current if t not in remove] + add)
            done.append(cid)
        return {"updated": len(done), "not_found": missing}

    # ---------- DMs ----------

    def inbox(args):
        status = args.get("status") or "needs_you"
        rows = [t for t in ai_agent.threads(ig_id) if status == "all" or t.get("status") == status]
        now = time.time()
        return {"chats": [{"chat_id": t.get("igsid"), "username": t.get("username"), "status": t.get("status"),
                           "why_it_needs_you": t.get("reason") or None, "ai_suggested_reply": t.get("suggestion") or None,
                           "last_message": t.get("last_text"), "last_from": t.get("last_role"), "at": when(t.get("last_at")),
                           "can_reply": now - t.get("last_fan_at", 0) < 24 * 3600}
                          for t in rows[: min(int(args.get("limit") or 20), 100)]],
                "statuses": "needs_you = the AI handed it to the creator; ai = the AI is answering; you = the creator took over"}

    def conversation(args):
        cid = str(args.get("chat_id", ""))
        thread = ai_agent.get_thread(ig_id, cid)
        if not thread:
            raise ToolError("No chat with that id. Use list_inbox.")
        return {"chat": {k: thread.get(k) for k in ("username", "status", "reason", "suggestion")},
                "messages": [{"from": m["role"], "text": m["text"], "at": when(m["at"])} for m in ai_agent.messages(ig_id, cid)]}

    def reply(args):
        try:
            svc.inbox_send(acc, str(args.get("chat_id", "")), args.get("text", ""))
        except (ValueError, RuntimeError) as e:
            raise ToolError(str(e))
        return {"sent": True, "note": "The AI stays out of this chat until you hand it back (hand_chat_to)."}

    def hand_to(args):
        who = args.get("to")
        if who not in ("ai", "you"):
            raise ToolError('to must be "ai" or "you".')
        thread = ai_agent.update_thread(ig_id, str(args.get("chat_id", "")), status=who, reason="", suggestion="", hold_sent=False)
        if not thread:
            raise ToolError("No chat with that id.")
        return {"chat_id": args["chat_id"], "handled_by": who}

    def broadcast(args):
        text = str(args.get("text") or "").strip()
        reach = len(engine.recent_chats(acc))
        if not args.get("confirm"):
            return {"preview": True, "would_reach": reach, "text": text,
                    "note": "Nothing sent. Show this to the user; call again with confirm=true once they say yes."}
        bid = re.sub(r"[^a-z0-9]", "", str(args.get("broadcast_id") or "").lower())[:16] or secrets.token_hex(5)
        try:
            r = svc.broadcast_batch(acc, {"id": bid, "text": text, "url": args.get("link") or "", "button": args.get("button_text") or ""})
        except ValueError as e:
            raise ToolError(str(e))
        return {**r, "broadcast_id": bid,
                "next": None if r["done"] else "More people left: call again with the same broadcast_id and confirm=true."}

    def messaging_settings(_):
        fresh = store.load_account(ig_id) or acc
        ai = ai_agent.settings(fresh)
        return {"welcome_message": engine.welcome_settings(fresh), "chat_menu": engine.ice_settings(fresh),
                "ai_agent": {**{k: ai[k] for k in ("enabled", "language", "about", "faq", "handoff")},
                             "replies_used": ai_agent.used(fresh), "reply_limit": ai_agent.allowance(fresh)[1]},
                "utm_tags_on": fresh.get("utm", True), "notifications": {"handoff": True, "lead": True, "sale": True, "health": True,
                                                                         **(fresh.get("notify") or {})},
                "people_reachable_by_broadcast_now": len(engine.recent_chats(fresh))}

    def welcome(args):
        fresh = store.load_account(ig_id) or acc
        buttons = []
        for b in args.get("buttons") or []:
            if b.get("automation_id"):
                buttons.append({"type": "kw", "title": b.get("title", ""), "value": b["automation_id"]})
            else:
                buttons.append({"type": "url", "title": b.get("title", ""), "value": b.get("link", "")})
        try:
            return {"welcome_message": svc.set_welcome(fresh, {"enabled": args.get("enabled", True), "text": args.get("text", ""),
                                                               "buttons": buttons})}
        except ValueError as e:
            raise ToolError(str(e))

    def update_ai(args):
        fresh = store.load_account(ig_id) or acc
        data = {k: args[k] for k in ("enabled", "language", "about", "faq") if args.get(k) is not None}
        if args.get("handoff") is not None:
            data["handoff"] = "\n".join(args["handoff"]) if isinstance(args["handoff"], list) else str(args["handoff"])
        try:
            state = svc.update_ai(fresh, data)
        except ValueError as e:
            raise ToolError(str(e))
        return {"ai_agent": {k: state["settings"][k] for k in ("enabled", "language", "about", "faq", "handoff")}}

    def test_ai(args):
        fresh = store.load_account(ig_id) or acc
        text = str(args.get("message") or "").strip()[:1000]
        if not text:
            raise ToolError("Give a sample fan message.")
        if not ai_agent.ready(fresh):
            raise ToolError("The AI isn't set up on the server yet.")
        if ai_agent.over_quota(fresh):
            raise ToolError(ai_agent.quota_reason(fresh))
        answer = ai_agent.answer(fresh, [{"role": "fan", "text": text}], ai_agent.settings(fresh))
        ai_agent.note_use(fresh)
        return {"would_reply": answer.get("reply"), "would_hand_to_you": answer.get("needs_human"), "why": answer.get("reason") or None}

    def utm(args):
        fresh = store.load_account(ig_id) or acc
        fresh["utm"] = bool(args.get("on"))
        store.save_account(fresh)
        return {"utm_tags_on": fresh["utm"]}

    automation_props = {
        "target": {"type": "string", "description": 'A reel id (list_reels), an existing automation_id, or "keyword", "all", '
                                                     '"next_post", "story_replies", "story_mentions", "live".'},
        "keywords": {"type": "array", "items": _STR, "description": "Words that trigger it (case and plurals don't matter)."},
        "final_dm": {"type": "string", "description": "The main DM with the link. {username} = their name; {Hi|Hey} = random variation."},
        "label": {"type": "string", "description": "A name for the automation."},
        "comment_reply": {"type": "string", "description": "Public replies, one per line (rotated); empty = no public reply."},
        "replies_on": _BOOL,
        "opening_dm": {"type": "string", "description": "First DM with a button; the tap opens the chat so Instagram allows the rest."},
        "opening_dm_b": {"type": "string", "description": "Version B of the opening DM for an A/B test."},
        "button_text": {"type": "string", "maxLength": 20},
        "require_follow": {"type": "boolean", "description": "Only send the link to followers."},
        "follow_dm": _STR, "followed_button_text": {"type": "string", "maxLength": 20},
        "dm_button_text": {"type": "string", "maxLength": 20}, "dm_button_url": {"type": "string", "description": "https:// link button on the final DM."},
        "menu": {"type": "array", "maxItems": 3, "description": "Instead of one link: up to 3 options, each sends its own message.",
                 "items": {"type": "object", "properties": {"title": {"type": "string", "maxLength": 20}, "text": _STR, "url": _STR,
                                                            "button": {"type": "string", "maxLength": 20}}, "required": ["title"]}},
        "ask_email": _BOOL, "email_dm": _STR, "email_required": _BOOL,
        "ask_phone": {"type": "boolean", "description": "Ask for their WhatsApp number before the link."}, "phone_dm": _STR, "phone_required": _BOOL,
        "followup_dm": {"type": "string", "description": "A later offer (e.g. the paid product), sent once within 24 hours."},
        "followup_hours": {"type": "integer", "enum": [1, 3, 6, 12, 20]}, "followup_url": _STR,
        "followup_button": {"type": "string", "maxLength": 20}, "followup_on": _BOOL,
        "exclude": {"type": "array", "items": _STR, "description": "Comments with these words are ignored."},
        "once_per_person": _BOOL, "delay_min": {"type": "integer", "enum": list(engine.DELAYS)},
        "tags": {"type": "string", "description": "Comma-separated contact tags given to everyone it reaches."},
        "track_links": {"type": "boolean", "description": "Count link clicks (turn off for affiliate links)."},
        "starts_at": {"type": "string", "description": "Optional start, e.g. 2026-11-20T18:00 (India time)."},
        "ends_at": {"type": "string", "description": "Optional end time."},
        "dm_only": {"type": "boolean", "description": "Keyword automations only: react to DMs, not comments."},
        "enabled": _BOOL}

    tools = [
        # overview
        {"name": "get_account_summary", "title": "Account overview", "read_only": True, "fn": summary,
         "description": "Start here. Plan, DMs used vs the monthly limit, last-30-day and all-time totals (DMs, leads, follows, "
                        "link opens, sales, revenue in ₹), chats waiting, refused DMs, and any problem with the account.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "get_trends", "title": "Compare periods", "read_only": True, "fn": trends,
         "description": "This period vs the one before (default 7 days): DMs, leads, follows, link opens, sales, revenue, with % change "
                        "and a per-day series. Good for weekly reviews.",
         "input_schema": {"type": "object", "properties": {"days": {"type": "integer", "minimum": 1, "maximum": 30}}}},
        {"name": "get_best_posting_times", "title": "Best time to post", "read_only": True, "fn": best_times,
         "description": "When the audience comments and DMs most (India time), from all automations.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "list_reels", "title": "List reels", "read_only": True, "fn": list_reels,
         "description": "The latest reels with id, caption, views, comments and whether an automation is on. Use the id elsewhere.",
         "input_schema": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 12}}}},
        {"name": "get_reel_report", "title": "Reel report", "read_only": True, "fn": reel_report,
         "description": "Per-reel funnel (views, comments, keyword, DM, link, follows), follows per 1K views, rank and tips.",
         "input_schema": {"type": "object", "properties": {"reel_id": _STR, "refresh": _BOOL}}},
        # automations
        {"name": "list_automations", "title": "List automations", "read_only": True, "fn": list_automations,
         "description": "Every automation with its trigger, keywords, on/off and all-time numbers (runs, link opens, follows, leads, "
                        "sales, ₹ revenue, open and conversion rates). sort_by ranks them, e.g. revenue or conversion.",
         "input_schema": {"type": "object", "properties": {"sort_by": {"type": "string", "enum": list(STAT_FIELDS) + ["conversion"]}}}},
        {"name": "get_automation", "title": "Automation details", "read_only": True, "fn": get_automation,
         "description": "Every setting of one automation (messages, buttons, menu, follow gate, email/phone, follow-up, schedule) and its numbers.",
         "input_schema": {"type": "object", "required": ["automation_id"], "properties": {"automation_id": _STR}}},
        {"name": "get_automation_insights", "title": "Automation insights", "read_only": True, "fn": insights,
         "description": "30 days for one automation: per-day numbers, the DM → link → follow → lead → sale funnel, busiest hours, menu picks.",
         "input_schema": {"type": "object", "required": ["automation_id"], "properties": {"automation_id": _STR}}},
        {"name": "save_automation", "title": "Create or update an automation", "fn": save_automation,
         "description": "Creates an automation or updates one (fields you leave out stay as they are). Comment automations reply "
                        "publicly and DM the commenter; story/mention/live/keyword-DM automations only DM. Optional: follow gate, email "
                        "or WhatsApp capture, a 3-option menu, a follow-up offer, A/B opening DM, schedule, tags. Show the user the "
                        "messages before turning on something new.",
         "input_schema": {"type": "object", "required": ["target"], "properties": automation_props}},
        {"name": "duplicate_automation", "title": "Copy an automation", "fn": duplicate,
         "description": "Copies an automation to other reels (ids), keywords, or next_post. Existing ones are skipped unless replace=true.",
         "input_schema": {"type": "object", "required": ["automation_id", "to"], "properties": {
             "automation_id": _STR, "to": {"type": "array", "items": _STR}, "replace": _BOOL}}},
        {"name": "set_automation_enabled", "title": "Pause or resume an automation", "fn": set_enabled,
         "description": "Turns one automation on or off without deleting it.",
         "input_schema": {"type": "object", "required": ["automation_id", "enabled"], "properties": {"automation_id": _STR, "enabled": _BOOL}}},
        {"name": "delete_automation", "title": "Delete an automation", "destructive": True, "fn": delete,
         "description": "Deletes one automation and its numbers for good. Ask the user first.",
         "input_schema": {"type": "object", "required": ["automation_id"], "properties": {"automation_id": _STR}}},
        {"name": "pause_all_automations", "title": "Pause or resume everything", "fn": pause,
         "description": "paused=true stops all replies and DMs for the account; paused=false starts them again.",
         "input_schema": {"type": "object", "required": ["paused"], "properties": {"paused": _BOOL}}},
        {"name": "send_to_past_comments", "title": "Send to past comments", "destructive": True, "fn": send_past,
         "description": "Runs a reel's automation on its comments from the last 7 days that came before it was set up (up to 50 per "
                        "call; call again if more_left). Sends real DMs: ask the user first.",
         "input_schema": {"type": "object", "required": ["reel_id"], "properties": {"reel_id": _STR}}},
        {"name": "retry_refused_dms", "title": "Retry refused DMs", "fn": retry,
         "description": "Sends again the comment DMs Instagram refused earlier, while its 7-day window is open (up to 30).",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "get_recent_activity", "title": "Recent activity", "read_only": True, "fn": activity,
         "description": "Latest events (replies, DMs, leads, sales, errors, account alerts), newest first. errors_only finds problems.",
         "input_schema": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100},
                                                           "errors_only": _BOOL, "action": _STR}}},
        # money
        {"name": "get_sales", "title": "Sales and revenue", "read_only": True, "fn": sales,
         "description": "Sales and ₹ revenue (all time and 30 days), revenue per automation, products with their sales links, recent sales.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "add_product", "title": "Add a product", "fn": add_product,
         "description": "Adds a product to track sales of; returns its sales link to set as the payment page's redirect after payment.",
         "input_schema": {"type": "object", "required": ["name", "price"], "properties": {
             "name": _STR, "price": {"type": "integer", "description": "Price in ₹"},
             "thanks_url": {"type": "string", "description": "Optional own thank-you page (https://)."}}}},
        {"name": "delete_product", "title": "Delete a product", "destructive": True, "fn": delete_product,
         "description": "Deletes a product; its sales link stops working. Ask the user first.",
         "input_schema": {"type": "object", "required": ["product_id"], "properties": {"product_id": _STR}}},
        {"name": "set_utm_tags", "title": "UTM tags on DM links", "fn": utm,
         "description": "Turns automatic utm_source=instagram&utm_medium=dm&utm_campaign=<automation> tags on DM links on or off.",
         "input_schema": {"type": "object", "required": ["on"], "properties": {"on": _BOOL}}},
        # people
        {"name": "search_contacts", "title": "Find contacts", "read_only": True, "fn": search_contacts,
         "description": "People who interacted: search by username/email/phone/keyword, filter by tag, has_email, has_phone, followed. "
                        "Also returns every tag with its count.",
         "input_schema": {"type": "object", "properties": {"query": _STR, "tag": _STR, "has_email": _BOOL, "has_phone": _BOOL,
                                                           "followed": _BOOL, "limit": {"type": "integer", "minimum": 1, "maximum": 200}}}},
        {"name": "tag_contacts", "title": "Tag contacts", "fn": tag_contacts,
         "description": "Adds and/or removes tags (e.g. vip, bought) on contacts, by contact_id or username.",
         "input_schema": {"type": "object", "required": ["contact_ids"], "properties": {
             "contact_ids": {"type": "array", "items": _STR}, "add_tags": {"type": "array", "items": _STR},
             "remove_tags": {"type": "array", "items": _STR}}}},
        # DMs
        {"name": "list_inbox", "title": "AI Inbox", "read_only": True, "fn": inbox,
         "description": "DM chats from the AI Inbox. Default: the ones the AI handed to the creator, with the reason and a suggested reply.",
         "input_schema": {"type": "object", "properties": {"status": {"type": "string", "enum": ["needs_you", "ai", "you", "all"]},
                                                           "limit": {"type": "integer", "minimum": 1, "maximum": 100}}}},
        {"name": "get_conversation", "title": "Read a chat", "read_only": True, "fn": conversation,
         "description": "The last 40 messages of one DM chat.",
         "input_schema": {"type": "object", "required": ["chat_id"], "properties": {"chat_id": _STR}}},
        {"name": "reply_in_dm", "title": "Reply in a DM", "destructive": True, "fn": reply,
         "description": "Sends a DM in a chat as the creator (only within 24 hours of the person's last message). Show the user "
                        "the text and get a yes first.",
         "input_schema": {"type": "object", "required": ["chat_id", "text"], "properties": {"chat_id": _STR, "text": _STR}}},
        {"name": "hand_chat_to", "title": "Hand a chat to the AI or the creator", "fn": hand_to,
         "description": 'to="ai" lets the AI answer this chat again; to="you" keeps the AI out of it.',
         "input_schema": {"type": "object", "required": ["chat_id", "to"], "properties": {"chat_id": _STR, "to": {"type": "string", "enum": ["ai", "you"]}}}},
        {"name": "broadcast_to_recent_chats", "title": "Message recent chats", "destructive": True, "fn": broadcast,
         "description": "Sends one message (optional link button) to everyone who DMed in the last 24 hours, Instagram's limit. "
                        "Without confirm=true it only previews how many it would reach. Get the user's yes before confirming.",
         "input_schema": {"type": "object", "required": ["text"], "properties": {
             "text": _STR, "link": _STR, "button_text": {"type": "string", "maxLength": 20}, "confirm": _BOOL, "broadcast_id": _STR}}},
        {"name": "get_messaging_settings", "title": "DM settings", "read_only": True, "fn": messaging_settings,
         "description": "Welcome message, chat menu, AI agent setup and usage, UTM tags, notification choices, people reachable by broadcast.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "set_welcome_message", "title": "Welcome message", "fn": welcome,
         "description": "The message first-time DMers get when no keyword matches, with up to 3 buttons: a link, or an "
                        "automation_id (keyword automation) to start.",
         "input_schema": {"type": "object", "required": ["text"], "properties": {
             "enabled": _BOOL, "text": _STR, "buttons": {"type": "array", "maxItems": 3, "items": {"type": "object", "required": ["title"],
                 "properties": {"title": {"type": "string", "maxLength": 20}, "link": _STR, "automation_id": _STR}}}}}},
        {"name": "update_ai_agent", "title": "Set up the AI DM agent", "fn": update_ai,
         "description": "Changes the AI agent: on/off, language (match/hinglish/hindi/english), about the creator, FAQ and products "
                        "with prices and links, and topics to hand over (refunds, collabs...). Only the fields given change.",
         "input_schema": {"type": "object", "properties": {"enabled": _BOOL, "language": {"type": "string", "enum": ["match", "hinglish", "hindi", "english"]},
                                                           "about": _STR, "faq": _STR, "handoff": {"type": "array", "items": _STR}}}},
        {"name": "test_ai_reply", "title": "Test the AI agent", "fn": test_ai,
         "description": "Shows what the AI agent would answer to a sample fan message, without sending. Uses one AI reply credit.",
         "input_schema": {"type": "object", "required": ["message"], "properties": {"message": _STR}}},
    ]
    if read_only:
        tools = [t for t in tools if t.get("read_only")]
    for t in tools:
        if not t.get("read_only"):
            t["fn"] = _audited(acc, t["name"], t["fn"])
    return tools


def _audited(acc, name, fn):
    """Changes Claude makes show up in the account's Activity log."""
    def run(args):
        try:
            out = fn(args)
        except ToolError as e:
            store.log_activity(acc["id"], "", "Claude", name, "claude", "error", str(e)[:200])
            raise
        detail = {"save_automation": lambda: f"{'Created' if out.get('created') else 'Updated'} {out['saved']['name']}",
                  "broadcast_to_recent_chats": lambda: "Preview only" if out.get("preview") else f"Sent to {out.get('sent')}",
                  }.get(name, lambda: "")()
        if not (isinstance(out, dict) and out.get("preview")):
            store.log_activity(acc["id"], "", "Claude", name.replace("_", " "), "claude", "ok", detail)
        return out
    return run


INSTRUCTIONS = """{brand} runs Instagram comment-to-DM automations, an AI DM agent, lead capture and sales tracking for @{username}.
- Start with get_account_summary. Money is in Indian rupees (₹) and times are India time (IST).
- Automation ids: a reel id, "kw:WORD" (keyword), "*" (any post), "next" (next post), "story:reply", "story:mention", "live".
- In messages, {{username}} becomes the person's name and {{Hi|Hey|Hello}} picks one option at random (safer for the account).
- Instagram rules: one DM per comment within 7 days; other DMs only within 24 hours of the person's last message.
- Before anything that sends real messages (broadcast_to_recent_chats, send_to_past_comments, reply_in_dm) or deletes, show the
  user exactly what will happen and get a clear yes.
- Write public copy in friendly Hinglish unless the creator writes in another language.
{mode}"""


def instructions(acc, brand, read_only):
    return INSTRUCTIONS.format(brand=brand, username=acc.get("username"),
                               mode="- This is a read-only connection: you can look at everything but not change or send anything."
                               if read_only else "")


def prompts():
    """Ready-made requests the creator can pick in Claude (the + menu or slash commands)."""
    return [
        {"name": "weekly_review", "title": "Weekly review",
         "description": "How did this week go, what made money, and 3 things to do next.",
         "arguments": [{"name": "days", "description": "Days to review (default 7)", "required": False}],
         "render": lambda a: (
             f"Do a review of my last {a.get('days') or 7} days on ReplyInbox. Use get_trends, get_sales, list_automations "
             "(sort_by revenue and then link_clicks), get_best_posting_times and get_recent_activity with errors_only. "
             "Tell me in short Hinglish: what grew or dropped (with numbers), which automation made the most money and why, "
             "anything broken, the best time to post, and exactly 3 concrete actions for next week. Don't change anything.")},
        {"name": "launch_plan", "title": "Plan a launch",
         "description": "Turn a product launch into automations: keyword, menu, follow-up, welcome, broadcast.",
         "arguments": [{"name": "product", "description": "What you're launching", "required": True},
                       {"name": "price", "description": "Price in ₹", "required": False},
                       {"name": "link", "description": "Payment / product link", "required": False},
                       {"name": "launch_date", "description": "When it goes live", "required": False}],
         "render": lambda a: (
             f"Help me launch '{a['product']}'" + (f" at ₹{a['price']}" if a.get("price") else "") +
             (f" (link: {a['link']})" if a.get("link") else "") + (f" on {a['launch_date']}" if a.get("launch_date") else "") +
             ". First look at get_account_summary, list_automations and get_best_posting_times. Then propose a plan: a keyword for "
             "the launch reel (next_post automation), the DMs (with a 3-option menu if useful, WhatsApp capture for warm leads, and a "
             "follow-up offer), a product in sales tracking, a welcome-message tweak, and a broadcast message for launch day. "
             "Show me every message first; create things only after I say yes. Never send a broadcast without my confirmation.")},
        {"name": "new_reel_automation", "title": "Set up a reel",
         "description": "Write and create the automation for a new or upcoming reel.",
         "arguments": [{"name": "topic", "description": "What the reel is about", "required": True},
                       {"name": "freebie_link", "description": "The link people get", "required": True},
                       {"name": "reel_id", "description": "Reel id, or leave empty for your next post", "required": False}],
         "render": lambda a: (
             f"Set up an automation for my reel about '{a['topic']}'. People get: {a['freebie_link']}. "
             f"Target: {'reel ' + a['reel_id'] if a.get('reel_id') else 'my next post (next_post)'}. Suggest one short keyword, "
             "3 rotating public replies, the DM with {Hi|Hey} variations, and whether to ask for follow or email, based on what "
             "worked best in list_automations. Show me the draft, then save it with save_automation once I approve.")},
        {"name": "fix_problems", "title": "Health check",
         "description": "Find anything broken: logins, refused DMs, limits, errors, paused automations.",
         "render": lambda a: (
             "Do a health check of my ReplyInbox account: get_account_summary, get_recent_activity (errors_only, limit 50), "
             "list_automations. List each problem in plain words with how to fix it, fix the safe ones (like retry_refused_dms) only "
             "after asking me, and tell me what I must do myself in the dashboard or Instagram.")},
        {"name": "inbox_catchup", "title": "Catch up on DMs",
         "description": "Go through chats waiting for you and draft replies.",
         "render": lambda a: (
             "Open list_inbox (needs_you). For each chat, read it with get_conversation and draft a short, warm reply in the "
             "fan's language. Show me all drafts together; send each with reply_in_dm only after I approve it, then hand_chat_to "
             "ai when it's resolved.")},
    ]
