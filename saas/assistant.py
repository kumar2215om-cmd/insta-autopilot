"""The in-app AI assistant ("Ask anything, or tell me what to set up" on Home), like SuperProfile's SuperAI.

Claude works with the same tools as Connect Claude (mcp_tools.py). Looking things up runs straight away; anything that
changes, sends or deletes is shown to the creator as a card and only runs when they tap Approve.

One chat per account (s:t:<acc>:assistant): the API messages (with tool calls) plus what the page shows.
"""
import json
import os
import time

import ai_agent
import store

MODEL = os.environ.get("ASSISTANT_MODEL", "claude-haiku-5-5")  # the low-cost model; set ASSISTANT_MODEL to upgrade later
MAX_STEPS = 5
DAILY = {"free": 10, "paid": 50}
KEEP = 40


class AssistantError(Exception):
    """A problem to show the person as it is."""


def _key(acc_id):
    return store.account_key(acc_id, "assistant")


def load(acc_id):
    return store.get_json(_key(acc_id)) or {"messages": [], "shown": [], "pending": None}


def save(acc_id, chat):
    chat["messages"] = _trim(chat["messages"])
    chat["shown"] = chat["shown"][-KEEP:]
    store.set_json(_key(acc_id), chat)


def _trim(msgs):
    """Keeps the last ~20 turns, starting at a plain user message (never between a tool call and its result)."""
    if len(msgs) <= 40:
        return msgs
    cut = msgs[-40:]
    while cut and not (cut[0]["role"] == "user" and isinstance(cut[0]["content"], str)):
        cut = cut[1:]
    return cut


def reset(acc_id):
    store.redis("DEL", _key(acc_id))


def _day():
    return time.strftime("%Y%m%d", time.gmtime(time.time() + 19800))


def left(acc):
    limit = DAILY["paid" if store.is_pro(acc) else "free"]
    used = int(store.redis("GET", f"s:asstuse:{acc['id']}:{_day()}") or 0)
    return max(0, limit - used)


def _use(acc):
    k = f"s:asstuse:{acc['id']}:{_day()}"
    store.redis("INCR", k)
    store.redis("EXPIRE", k, 2 * 86400)


SYSTEM = """You are the AI assistant inside {brand}, the Instagram growth and selling app of @{username}.
Help them understand their numbers and set things up. Be brief: short paragraphs or a few bullets, simple words.
Reply in the language they write in (Hinglish is fine). Money is in ₹, times are India time.
Use the tools to look things up; never guess numbers. To change, send or delete anything, call the tool directly:
the app shows the creator a card to approve first, so don't ask "shall I?" in text before calling it.
When something isn't possible with your tools, say where in the app they can do it.
{extra}"""


def _tool_defs(tools):
    return [{"name": t["name"], "description": t["description"][:1000], "input_schema": t["input_schema"]} for t in tools]


def _block(b):
    if b.type == "text":
        return {"type": "text", "text": b.text}
    if b.type == "tool_use":
        return {"type": "tool_use", "id": b.id, "name": b.name, "input": b.input}
    return None


def _run(tool, args):
    try:
        out = tool["fn"](args or {})
        return json.dumps(out, ensure_ascii=False, default=str)[:20000], False
    except Exception as e:  # ToolError and friends: tell Claude what went wrong
        return str(e)[:500] or "That didn't work.", True


def _call(c, acc, chat, tools, system):
    req = dict(model=MODEL, max_tokens=1200, system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
               tools=_tool_defs(tools), messages=chat["messages"])
    if MODEL.startswith(ai_agent.FALLBACK_MODELS):
        return c.beta.messages.create(**req, betas=["server-side-fallback-2026-07-01"], fallbacks="default")
    return c.messages.create(**req)


def _process(tools, chat, uses, results):
    """Runs tool calls in order; stops at the first one that needs the creator's approval (saved as chat["pending"])."""
    by = {t["name"]: t for t in tools}
    for i, u in enumerate(uses):
        t = by.get(u["name"])
        if not t:
            results.append({"type": "tool_result", "tool_use_id": u["id"], "content": "Unknown tool.", "is_error": True})
            continue
        if t.get("read_only"):
            text, err = _run(t, u["input"])
            results.append({"type": "tool_result", "tool_use_id": u["id"], "content": text, **({"is_error": True} if err else {})})
            continue
        chat["pending"] = {"use": u, "rest": uses[i + 1:], "results": results, "title": t.get("title") or u["name"],
                           "name": u["name"], "args": u["input"], "destructive": bool(t.get("destructive"))}
        return False
    return True


def _loop(acc, chat, tools, system):
    c = ai_agent.client()
    if c is None:
        raise AssistantError("The AI isn't set up on the server yet.")
    for _ in range(MAX_STEPS):
        r = _call(c, acc, chat, tools, system)
        if r.stop_reason == "refusal":
            chat["shown"].append({"role": "ai", "text": "Sorry, I can't help with that one."})
            chat["messages"].append({"role": "assistant", "content": [{"type": "text", "text": "(declined)"}]})
            return
        content = [b for b in (_block(x) for x in r.content) if b]
        chat["messages"].append({"role": "assistant", "content": content or [{"type": "text", "text": "…"}]})
        text = "\n".join(b["text"] for b in content if b["type"] == "text").strip()
        if text:
            chat["shown"].append({"role": "ai", "text": text})
        uses = [b for b in content if b["type"] == "tool_use"]
        if not uses:
            return
        results = []
        if not _process(tools, chat, uses, results):
            return  # waiting for the creator's approval
        chat["messages"].append({"role": "user", "content": results})
    chat["shown"].append({"role": "ai", "text": "That took more steps than I can do at once. Ask me to continue."})


def ask(acc, tools, text, brand, extra=""):
    """A new message from the creator. Returns the chat."""
    text = str(text or "").strip()[:4000]
    if not text:
        raise AssistantError("Type a question first.")
    if left(acc) <= 0:
        raise AssistantError("You've used today's AI messages. They refill tomorrow" + ("." if store.is_pro(acc) else ", or upgrade for more."))
    chat = load(acc["id"])
    _use(acc)
    if chat.get("pending"):  # a new message means "no" to the waiting change (and skips the calls after it)
        results, rest = _decide(chat, tools, False)
        results += [{"type": "tool_result", "tool_use_id": u["id"], "content": "Skipped: the creator moved on."} for u in rest]
        chat["messages"].append({"role": "user", "content": results + [{"type": "text", "text": text}]})
    else:
        chat["messages"].append({"role": "user", "content": text})
    chat["shown"].append({"role": "you", "text": text})
    system = SYSTEM.format(brand=brand, username=acc.get("username", ""), extra=extra)
    try:
        _loop(acc, chat, tools, system)
    finally:
        save(acc["id"], chat)
    return chat


def _decide(chat, tools, approve):
    p = chat.pop("pending")
    u = p["use"]
    by = {t["name"]: t for t in tools}
    if approve and u["name"] in by:
        out, err = _run(by[u["name"]], u["input"])
        chat["shown"].append({"role": "action", "text": p["title"], "status": "error" if err else "done", "detail": out[:300] if err else ""})
    else:
        out, err = "The creator said no; nothing was changed. Don't try again unless they ask.", False
        chat["shown"].append({"role": "action", "text": p["title"], "status": "declined"})
    results = p["results"] + [{"type": "tool_result", "tool_use_id": u["id"], "content": out, **({"is_error": True} if err else {})}]
    return results, p["rest"]


def decide(acc, tools, approve, brand, extra=""):
    """The creator approved or declined the waiting change; the assistant carries on."""
    chat = load(acc["id"])
    if not chat.get("pending"):
        raise AssistantError("Nothing is waiting for approval.")
    results, rest = _decide(chat, tools, approve)
    try:
        if _process(tools, chat, rest, results):
            chat["messages"].append({"role": "user", "content": results})
            _loop(acc, chat, tools, SYSTEM.format(brand=brand, username=acc.get("username", ""), extra=extra))
    finally:
        save(acc["id"], chat)
    return chat


def view(acc, chat):
    p = chat.get("pending")
    return {"shown": chat.get("shown", []), "left": left(acc),
            "pending": {"title": p["title"], "name": p["name"], "args": p["args"], "destructive": p["destructive"]} if p else None}
