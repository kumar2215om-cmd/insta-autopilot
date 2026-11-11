"""AI DM agent: Claude answers fans' DMs from the creator's own products, links and FAQ.

Used when someone DMs a message that isn't one of the creator's keywords. Claude either replies
(in the fan's language) or hands the chat to the creator with a suggested reply.
"""
import json
import os
import time

import store

AI_MODEL = os.environ.get("AI_MODEL", "claude-haiku-5-5")
# Free plan: a one-time trial. Paid plan ("plan": "pro" on the account): a monthly allowance.
FREE_AI_TRIAL = int(os.environ.get("FREE_AI_TRIAL_REPLIES", "25"))
PAID_MONTHLY_AI_REPLIES = int(os.environ.get("PAID_MONTHLY_AI_REPLIES", "1000"))
# Models with server-side refusal fallbacks (Haiku has none).
FALLBACK_MODELS = ("claude-opus-", "claude-sonnet-5-5", "claude-fable-")
HISTORY = 12  # messages of the conversation Claude sees
DEFAULT_HOLD = "Thanks for your message! I'll get back to you personally soon 🙏"
DEFAULT_HANDOFF = ["refunds or payment problems", "brand deals and collaborations", "anything you are not sure about"]

_client = None


def client():
    """The Anthropic client, or None when no API key is configured."""
    global _client
    if _client is None and os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic
        _client = anthropic.Anthropic(timeout=25.0, max_retries=1)
    return _client


def settings(acc):
    s = acc.get("ai") or {}
    return {"enabled": bool(s.get("enabled")), "language": s.get("language", "match"), "about": s.get("about", ""),
            "faq": s.get("faq", ""), "handoff": s.get("handoff") or DEFAULT_HANDOFF,
            "hold_message": s.get("hold_message", DEFAULT_HOLD), "send_hold": s.get("send_hold", True) is not False}


# ---------- conversations ----------

def _chat_key(ig_id, igsid):
    return store.account_key(ig_id, f"chat:{igsid}")


def add_message(ig_id, igsid, role, text, username="", **thread_fields):
    """role: fan, ai or you. Also updates the conversation's row in the inbox; returns that row."""
    key = _chat_key(ig_id, igsid)
    store.redis("LPUSH", key, json.dumps({"role": role, "text": text[:2000], "at": int(time.time())}, ensure_ascii=False))
    store.redis("LTRIM", key, 0, 39)
    thread = get_thread(ig_id, igsid) or {"igsid": igsid, "username": username, "status": "ai"}
    thread.update(last_text=text[:160], last_role=role, last_at=int(time.time()), **thread_fields)
    if role == "fan":
        thread["last_fan_at"] = thread["last_at"]
    if username:
        thread["username"] = username
    save_thread(ig_id, igsid, thread)
    return thread


def update_thread(ig_id, igsid, **fields):
    thread = get_thread(ig_id, igsid)
    if thread:
        thread.update(fields)
        save_thread(ig_id, igsid, thread)
    return thread


def messages(ig_id, igsid):
    return list(reversed([json.loads(x) for x in store.redis("LRANGE", _chat_key(ig_id, igsid), 0, 39) or []]))


def get_thread(ig_id, igsid):
    raw = store.redis("HGET", store.account_key(ig_id, "threads"), igsid)
    return json.loads(raw) if raw else None


def save_thread(ig_id, igsid, thread):
    store.redis("HSET", store.account_key(ig_id, "threads"), igsid, json.dumps(thread, ensure_ascii=False))


def threads(ig_id):
    flat = store.redis("HGETALL", store.account_key(ig_id, "threads")) or []
    rows = [json.loads(flat[i + 1]) for i in range(0, len(flat), 2)]
    return sorted(rows, key=lambda t: -t.get("last_at", 0))


# ---------- monthly AI replies ----------

def month():
    return time.strftime("%Y-%m", time.gmtime())


def is_paid(acc):
    return acc.get("plan") == "pro"


def allowance(acc):
    """("month", n) for paid plans or a custom "ai_limit"; ("trial", n) for the free plan's one-time trial."""
    if acc.get("ai_limit") is not None:
        return "month", int(acc["ai_limit"])
    return ("month", PAID_MONTHLY_AI_REPLIES) if is_paid(acc) else ("trial", FREE_AI_TRIAL)


def used(acc):
    kind, _ = allowance(acc)
    c = store.counts(acc["id"])
    return c.get(f"ai:{month()}", 0) if kind == "month" else c.get("ai_total", 0)


def over_quota(acc):
    _, limit = allowance(acc)
    return bool(limit) and used(acc) >= limit


def quota_reason(acc):
    kind, limit = allowance(acc)
    if kind == "trial":
        return f"Your {limit} free AI replies are used up. Upgrade to keep AI replies on."
    return f"This month's {limit} AI replies are used up."


def note_use(acc):
    store.count(acc["id"], f"ai:{month()}")
    store.count(acc["id"], "ai_total")


def ready(acc):
    """The demo answers with sample replies; real accounts need the server's Claude key."""
    return bool(acc.get("demo")) or client() is not None


# ---------- what Claude knows ----------

def knowledge(acc):
    """The creator's products, links, keyword offers and FAQ, as text for the system prompt."""
    lines = []
    page = store.load_page(acc["id"]) or {}
    for it in page.get("items", []):
        if it.get("enabled", True):
            price = f" — price {it['price']}" if it.get("price") else ""
            sub = f" ({it['subtitle']})" if it.get("subtitle") else ""
            lines.append(f"- {it.get('type', 'link').title()}: {it['title']}{sub}{price}. Link: {it['url']}")
    for key, rule in store.load_rules(acc["id"]).get("reels", {}).items():
        if rule.get("enabled", True) and rule.get("dm") and rule.get("keywords"):
            lines.append(f"- Freebie for keyword {', '.join(rule['keywords'])}: {rule['dm']}")
    return "\n".join(lines) or "- (no products or links added yet)"


LANGUAGE = {
    "match": "Reply in the same language and style the fan writes in: Hinglish (Hindi in Latin letters), Hindi or English.",
    "hinglish": "Always reply in Hinglish (Hindi written in Latin letters, mixed with English), like Indian creators text.",
    "hindi": "Always reply in Hindi (Devanagari).",
    "english": "Always reply in simple English.",
}


def system_prompt(acc, s):
    handoff = "\n".join(f"- {h}" for h in s["handoff"])
    return f"""You reply to Instagram DMs on behalf of the creator @{acc.get('username', '')}, as their assistant, in their voice: warm, short and helpful, like a real person texting. Most fans are Indian.

About the creator (written by them):
{s['about'] or '(not provided)'}

Products and links you may share (the only prices and links you may mention):
{knowledge(acc)}

Creator's FAQ (answer from this when it fits):
{s['faq'] or '(none)'}

How to reply:
- {LANGUAGE.get(s['language'], LANGUAGE['match'])}
- Keep it to 1–4 short sentences. An emoji or two is fine. No markdown, no bullet lists.
- Only use facts from above. Never invent prices, discounts, dates, links, guarantees or results. If you don't know, hand over.
- When a fan wants a product, give its exact link from the list.
- Don't ask for passwords, OTPs, payment details or other personal data.
- Hand over to the creator (needs_human = true) for:
{handoff}
  When you hand over, write in suggested_reply what the creator could send, and leave reply empty.
- If the message needs no answer (just "ok", "thanks", an emoji), set reply to a very short friendly answer or leave it empty."""


SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {"type": "string", "description": "The DM to send now. Empty when handing over or when no reply is needed."},
        "needs_human": {"type": "boolean"},
        "reason": {"type": "string", "description": "Short reason for handing over, else empty."},
        "suggested_reply": {"type": "string", "description": "When handing over: a reply the creator could send."},
    },
    "required": ["reply", "needs_human", "reason", "suggested_reply"],
    "additionalProperties": False,
}


def ask_claude(acc, history, s):
    """Returns {"reply", "needs_human", "reason", "suggested_reply"} for the conversation so far."""
    c = client()
    if c is None:
        raise RuntimeError("AI isn't set up yet: add ANTHROPIC_API_KEY to the server.")
    convo = []
    for m in history[-HISTORY:]:
        role = "user" if m["role"] == "fan" else "assistant"
        if convo and convo[-1]["role"] == role:
            convo[-1]["content"] += "\n" + m["text"]
        else:
            convo.append({"role": role, "content": m["text"]})
    if not convo or convo[0]["role"] != "user":
        convo.insert(0, {"role": "user", "content": "(conversation start)"})
    if convo[-1]["role"] != "user":
        convo.append({"role": "user", "content": "(no new message)"})
    request = dict(
        model=AI_MODEL,
        max_tokens=4000,
        system=[{"type": "text", "text": system_prompt(acc, s), "cache_control": {"type": "ephemeral"}}],
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=convo,
    )
    if AI_MODEL.startswith(FALLBACK_MODELS):
        response = c.beta.messages.create(**request, betas=["server-side-fallback-2026-07-01"], fallbacks="default")
    else:
        response = c.messages.create(**request)
    if response.stop_reason == "refusal":
        return {"reply": "", "needs_human": True, "reason": "The AI declined to answer this message.", "suggested_reply": ""}
    if response.stop_reason == "max_tokens":
        return {"reply": "", "needs_human": True, "reason": "The AI's answer was cut off.", "suggested_reply": ""}
    text = next((b.text for b in response.content if b.type == "text"), "")
    data = json.loads(text)
    return {"reply": str(data.get("reply", "")).strip(), "needs_human": bool(data.get("needs_human")),
            "reason": str(data.get("reason", "")), "suggested_reply": str(data.get("suggested_reply", "")).strip()}


def answer(acc, history, s):
    """The AI's answer to the newest fan message (sample answers for the demo account)."""
    if acc.get("demo"):
        return sample_answer(history[-1]["text"] if history else "")
    return ask_claude(acc, history, s)


def sample_answer(text):
    """Used in demo mode (and previews without an API key) so the inbox can be tried."""
    low = text.lower()
    if any(w in low for w in ("refund", "paisa wapas", "money back")):
        return {"reply": "", "needs_human": True, "reason": "Refund request",
                "suggested_reply": "Sorry it didn't work for you! I've noted your request and will get back within 24 hours 🙏"}
    if any(w in low for w in ("price", "kitna", "cost", "kitne")):
        return {"reply": "Abhi sirf ₹149 hai 🙌 Saare 39 packs, lifetime access. Yahan se le lo 👉 https://example.com/prompts",
                "needs_human": False, "reason": "", "suggested_reply": ""}
    return {"reply": "Haan bilkul! Har pack mein step-by-step guide hai, beginners ke liye bhi easy hai 😊 Koi aur sawaal ho to poocho!",
            "needs_human": False, "reason": "", "suggested_reply": ""}
