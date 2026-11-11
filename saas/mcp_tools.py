"""The tools Claude can use on one ReplyInbox account (see the /mcp route in app.py).

Same tool names and shapes as the single-account app's MCP server (../app.py, MCP_TOOLS).
"""
import re

import engine
import store
from mcp_protocol import ToolError

_STR = {"type": "string"}


def _rule_view(key, r):
    kind = ("keyword (any reel + DMs)" if engine.is_keyword_rule(key) else "all reels" if key == "*"
            else {"story:reply": "story replies", "story:mention": "story mentions"}.get(key, "reel"))
    return {"automation_id": key, "type": kind, "enabled": r.get("enabled", True) is not False,
            "keywords": r.get("keywords", []), "final_dm": r.get("dm", ""), "require_follow": bool(r.get("require_follow")),
            "comment_reply": r.get("comment_reply", ""), "auto_setup": bool(r.get("auto")), "label": r.get("label", "")}


def tools_for(acc, save_rule, build_report):
    """save_rule(acc, key, data) and build_report(acc, fresh) come from app.py."""
    ig_id = acc["id"]

    def report(fresh=False):
        try:
            return build_report(acc, fresh)
        except RuntimeError as e:
            raise ToolError(f"Instagram didn't answer: {e}")

    def summary(_):
        c = store.counts(ig_id)
        rules = store.load_rules(ig_id).get("reels", {})
        return {"account": acc.get("username"), "followers": acc.get("followers"),
                "dms_this_month": c.get(f"dms:{engine.month()}", 0), "monthly_dm_limit": engine.monthly_limit(acc),
                "links_sent_total": c.get("links_sent", 0), "follows_from_dms_total": c.get("gate_follows", 0),
                "comment_replies_total": c.get("comment_replies", 0),
                "automations_on": sum(1 for r in rules.values() if r.get("enabled", True) is not False),
                "auto_setup_on": bool(engine.auto_settings(acc).get("enabled")), "paused": bool(acc.get("paused")),
                "problem": engine.is_blocked(acc) or None}

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

    def list_automations(_):
        return {"automations": [_rule_view(k, r) for k, r in store.load_rules(ig_id).get("reels", {}).items()]}

    def save_automation(args):
        target = str(args.get("target") or "").strip()
        keywords = [str(k).strip() for k in args.get("keywords") or [] if str(k).strip()]
        if target == "keyword":
            if not keywords:
                raise ToolError("A keyword automation needs at least one keyword.")
            key = "kw:" + re.sub(r"[^A-Za-z0-9_]", "", keywords[0].upper())[:32]
        elif target == "all":
            key = "*"
        elif target.isdigit():
            key = target
        else:
            raise ToolError('target must be a reel id (from list_reels), "keyword" or "all".')
        old = store.load_rules(ig_id).get("reels", {}).get(key, {})
        data = dict(old)  # updating keeps the fields Claude didn't mention
        for field in ("comment_reply", "opening_dm", "button_text", "follow_dm", "followed_button_text", "require_follow"):
            if args.get(field) is not None:
                data[field] = args[field]
        if args.get("final_dm") is not None:
            data["dm"] = args["final_dm"]
        data["keywords"] = keywords or old.get("keywords", [])
        data.setdefault("comment_reply", engine.DEFAULT_COMMENT_REPLY)
        data.setdefault("require_follow", True)
        data["enabled"] = args.get("enabled", old.get("enabled", True)) is not False
        try:
            rules = save_rule(acc, key, data)
        except ValueError as e:
            raise ToolError(str(e))
        return {"saved": _rule_view(key, rules["reels"][key])}

    def set_enabled(args):
        key = str(args.get("automation_id", ""))
        rules = store.load_rules(ig_id)
        if key not in rules.get("reels", {}):
            raise ToolError("No automation with that id. Use list_automations.")
        rules["reels"][key]["enabled"] = bool(args.get("enabled"))
        store.save_rules(ig_id, rules)
        return {"automation_id": key, "enabled": rules["reels"][key]["enabled"]}

    def delete(args):
        key = str(args.get("automation_id", ""))
        rules = store.load_rules(ig_id)
        if rules.get("reels", {}).pop(key, None) is None:
            raise ToolError("No automation with that id.")
        store.save_rules(ig_id, rules)
        return {"deleted": key}

    def activity(args):
        items = store.recent_activity(ig_id)[: min(int(args.get("limit") or 20), 100)]
        return {"activity": [{k: a.get(k) for k in ("at", "username", "comment", "action", "status", "detail")} for a in items]}

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

    return [
        {"name": "send_to_past_comments", "title": "Send to past comments", "destructive": True, "fn": send_past,
         "description": "Runs a reel's automation on comments from the last 7 days that came before it was set up (public reply "
                        "+ DM, up to 50 per call; call again if more_left). Ask the user first: it sends real DMs.",
         "input_schema": {"type": "object", "required": ["reel_id"], "properties": {"reel_id": _STR}}},
        {"name": "retry_refused_dms", "title": "Retry refused DMs", "fn": retry,
         "description": "Sends again the comment DMs Instagram refused earlier, while its 7-day window is open (up to 30).",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "get_account_summary", "title": "Account summary", "read_only": True, "fn": summary,
         "description": "Followers, DMs this month and the monthly limit, links sent, follows won by the DM follow gate, "
                        "automations on, and whether anything is blocking the account.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "list_reels", "title": "List reels", "read_only": True, "fn": list_reels,
         "description": "The latest reels with id, caption, views, comments and whether a comment-to-DM automation is on. "
                        "Use the id in other tools.",
         "input_schema": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 12}}}},
        {"name": "get_reel_report", "title": "Reel report", "read_only": True, "fn": reel_report,
         "description": "Per-reel funnel (views, comments, used the keyword, got the DM, link sent, followed to unlock), "
                        "follows per 1K views, rank and tips. Give reel_id for one reel, or nothing for all.",
         "input_schema": {"type": "object", "properties": {"reel_id": _STR, "refresh": {"type": "boolean"}}}},
        {"name": "list_automations", "title": "List automations", "read_only": True, "fn": list_automations,
         "description": "All comment-to-DM automations: id, type (reel / keyword / all reels), keywords, final DM, follow gate, on or off.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "save_automation", "title": "Create or update an automation", "fn": save_automation,
         "description": ("Creates or updates a comment-to-DM automation. target: a reel id (from list_reels), \"keyword\" (works on "
                         "every reel and when someone DMs the word), or \"all\" (every reel without its own rule). People who comment "
                         "a keyword get a public reply and a DM; with require_follow they must follow before final_dm (the link) is "
                         "sent. Use {username} for the commenter's name."),
         "input_schema": {"type": "object", "required": ["target"], "properties": {
             "target": _STR, "keywords": {"type": "array", "items": _STR}, "final_dm": _STR,
             "comment_reply": {"type": "string", "description": "Public replies, one per line; empty = no public reply"},
             "opening_dm": _STR, "button_text": {"type": "string", "maxLength": 20}, "require_follow": {"type": "boolean"},
             "follow_dm": _STR, "followed_button_text": {"type": "string", "maxLength": 20}, "enabled": {"type": "boolean"}}}},
        {"name": "set_automation_enabled", "title": "Pause or resume an automation", "fn": set_enabled,
         "description": "Turns one automation on or off without deleting it.",
         "input_schema": {"type": "object", "required": ["automation_id", "enabled"],
                          "properties": {"automation_id": _STR, "enabled": {"type": "boolean"}}}},
        {"name": "delete_automation", "title": "Delete an automation", "destructive": True, "fn": delete,
         "description": "Deletes one automation for good.",
         "input_schema": {"type": "object", "required": ["automation_id"], "properties": {"automation_id": _STR}}},
        {"name": "get_recent_activity", "title": "Recent activity", "read_only": True, "fn": activity,
         "description": "The latest automation events (comment replies, DMs, follow checks, errors), newest first.",
         "input_schema": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}}}},
        {"name": "pause_all_automations", "title": "Pause or resume everything", "fn": pause,
         "description": "paused=true stops all replies and DMs for the account; paused=false starts them again.",
         "input_schema": {"type": "object", "required": ["paused"], "properties": {"paused": {"type": "boolean"}}}},
    ]
