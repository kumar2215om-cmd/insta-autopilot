"""AI agents that work the creator's DMs (like SuperProfile → AutoDM → Agents).

Lead Qualifier: reads DM chats and sorts the people into hot / warm / cold leads, with what they want.
Brand Collab: spots brand and collaboration offers in DMs and lists them (brand, offer, budget, deliverables, fit), so
the creator decides from one list. It can also ask the brand for the missing details automatically.

Both run on new fan DMs (engine.handle_ai_dm) through Claude with a small JSON answer, and have monthly limits.
Settings: acc["agents"] = {"lead": {...}, "brand": {...}}.
Data: thread["lead"] on the AI inbox thread; brand requests in s:t:<acc>:brands (a hash by chat id).
"""
import json
import re
import time

import ai_agent
import plans
import store

BRAND_RE = re.compile(r"collab|sponsor|brand|paid promo|promotion|partnership|partner|barter|campaign|rate ?card|"
                      r"commercials?|deliverables|influencer|ugc|promote (our|my)|budget|agency|endorse", re.I)
DEFAULT_ASK = ("Hi! Thanks for reaching out 🙌 To check fit, could you share: the brand/product, what you'd like "
               "(reel, story, post), timeline, and your budget?")

LEAD_SCHEMA = {"type": "object", "additionalProperties": False,
               "required": ["temperature", "interest", "reason", "name", "next_step"],
               "properties": {"temperature": {"type": "string", "enum": ["hot", "warm", "cold"]},
                              "interest": {"type": "string", "description": "What they want, in a few words."},
                              "reason": {"type": "string", "description": "Why this temperature, one short sentence."},
                              "name": {"type": "string", "description": "Their name if they gave it, else empty."},
                              "next_step": {"type": "string", "description": "What the creator should do next, one short sentence."}}}
BRAND_SCHEMA = {"type": "object", "additionalProperties": False,
                "required": ["is_brand_offer", "brand", "offer", "budget", "deliverables", "timeline", "fit", "why", "missing"],
                "properties": {"is_brand_offer": {"type": "boolean"},
                               "brand": {"type": "string"}, "offer": {"type": "string", "description": "What they propose, one sentence."},
                               "budget": {"type": "string", "description": "Amount and currency as said, or empty."},
                               "deliverables": {"type": "string"}, "timeline": {"type": "string"},
                               "fit": {"type": "string", "enum": ["good", "maybe", "poor"]},
                               "why": {"type": "string", "description": "Why this fit, one short sentence."},
                               "missing": {"type": "array", "items": {"type": "string"}, "description": "Details still unknown, e.g. budget."}}}


def settings(acc):
    a = acc.get("agents") or {}
    lead, brand = a.get("lead") or {}, a.get("brand") or {}
    return {"lead": {"enabled": bool(lead.get("enabled")), "hot": lead.get("hot", "")},
            "brand": {"enabled": bool(brand.get("enabled")), "min_budget": int(brand.get("min_budget") or 0),
                      "niches": brand.get("niches", ""), "avoid": brand.get("avoid", ""), "auto_ask": bool(brand.get("auto_ask")),
                      "ask_text": brand.get("ask_text") or DEFAULT_ASK}}


def clean(data):
    d = data or {}
    lead, brand = d.get("lead") or {}, d.get("brand") or {}
    try:
        budget = max(0, min(10 ** 8, int(brand.get("min_budget") or 0)))
    except (TypeError, ValueError):
        budget = 0
    return {"lead": {"enabled": bool(lead.get("enabled")), "hot": str(lead.get("hot", ""))[:600]},
            "brand": {"enabled": bool(brand.get("enabled")), "min_budget": budget, "niches": str(brand.get("niches", ""))[:400],
                      "avoid": str(brand.get("avoid", ""))[:400], "auto_ask": bool(brand.get("auto_ask")),
                      "ask_text": str(brand.get("ask_text") or DEFAULT_ASK)[:600]}}


def wants_messages(acc):
    s = settings(acc)
    return s["lead"]["enabled"] or s["brand"]["enabled"]


def cap(acc, kind):
    """Chats an agent may read this month on the account's plan."""
    return plans.limit(acc, "lead_agent" if kind == "lead" else "brand_agent")


def _month():
    return time.strftime("%Y-%m", time.gmtime())


def used(acc, kind):
    return int(store.counts(acc["id"]).get(f"agent_{kind}:{_month()}", 0))


def _note(acc, kind):
    store.count(acc["id"], f"agent_{kind}:{_month()}")


def _ask(acc, system, history, schema):
    c = ai_agent.client()
    if c is None:
        return None
    convo = "\n".join(f"{'Them' if m['role'] == 'fan' else 'Creator'}: {m['text']}" for m in history[-14:])
    r = c.messages.create(model=ai_agent.AI_MODEL, max_tokens=800, system=system,
                          output_config={"effort": "low", "format": {"type": "json_schema", "schema": schema}},
                          messages=[{"role": "user", "content": f"The DM chat with @{history[-1].get('username', '') if history else ''}:\n\n{convo}"}])
    if r.stop_reason in ("refusal", "max_tokens"):
        return None
    text = next((b.text for b in r.content if b.type == "text"), "")
    return json.loads(text)


# ---------- lead qualifier ----------

def qualify(acc, igsid, username=""):
    """Scores one chat (at most every 10 minutes). Returns the lead dict, or None."""
    s = settings(acc)["lead"]
    if not s["enabled"] or not plans.has(acc, "lead_agent") or used(acc, "lead") >= cap(acc, "lead"):
        return None
    thread = ai_agent.get_thread(acc["id"], igsid) or {}
    if (thread.get("lead") or {}).get("at", 0) > time.time() - 600:
        return thread.get("lead")
    history = ai_agent.messages(acc["id"], igsid)
    if not any(m["role"] == "fan" for m in history):
        return None
    system = (f"You sort Instagram DM leads for the creator @{acc.get('username', '')}. Hot: wants to buy or book soon, asks price/how to pay, "
              f"or matches what the creator calls hot. Warm: interested, asking questions. Cold: just saying hi, spam, or not a buyer. "
              f"Write in short simple English.\nWhat the creator sells and about them:\n{ai_agent.knowledge(acc)[:3000]}\n"
              f"The creator's idea of a hot lead: {s['hot'] or '(not given)'}")
    out = _ask(acc, system, history, LEAD_SCHEMA)
    if not out:
        return None
    _note(acc, "lead")
    lead = {**{k: str(out.get(k, ""))[:200] for k in ("temperature", "interest", "reason", "name", "next_step")}, "at": int(time.time())}
    if lead["temperature"] not in ("hot", "warm", "cold"):
        lead["temperature"] = "warm"
    ai_agent.update_thread(acc["id"], igsid, lead=lead)
    if lead["temperature"] == "hot" and (thread.get("lead") or {}).get("temperature") != "hot":
        try:
            import push
            if (acc.get("notify") or {}).get("lead", True):
                push.notify(acc, f"🔥 Hot lead: @{username or thread.get('username') or 'someone'}", lead["interest"] or lead["reason"], "/app/agents#leads")
        except Exception:
            pass
    return lead


def leads(acc, temperature=""):
    out = []
    for t in ai_agent.threads(acc["id"]):
        lead = t.get("lead")
        if lead and (not temperature or lead["temperature"] == temperature):
            out.append({"chat_id": t["igsid"], "username": t.get("username", ""), "last_text": t.get("last_text", ""),
                        "last_at": t.get("last_at", 0), **lead})
    order = {"hot": 0, "warm": 1, "cold": 2}
    return sorted(out, key=lambda x: (order.get(x["temperature"], 3), -x["last_at"]))


# ---------- brand collab ----------

def _brands_key(acc_id):
    return store.account_key(acc_id, "brands")


def requests(acc, status=""):
    flat = store.redis("HGETALL", _brands_key(acc["id"])) or []
    pairs = flat.items() if isinstance(flat, dict) else zip(flat[::2], flat[1::2])
    rows = [json.loads(v) for _, v in pairs]
    rows = [r for r in rows if not status or r.get("status") == status]
    return sorted(rows, key=lambda r: -r.get("updated", 0))


def set_status(acc, chat_id, status):
    raw = store.redis("HGET", _brands_key(acc["id"]), chat_id)
    if not raw or status not in ("new", "interested", "declined", "done"):
        return None
    r = json.loads(raw)
    r["status"] = status
    store.redis("HSET", _brands_key(acc["id"]), chat_id, json.dumps(r))
    return r


def check_brand(acc, igsid, username, text, send=None):
    """Looks at a chat when its newest message sounds like a brand offer (or it's already a brand chat).
    Returns the saved request or None. `send(text)` DMs the brand (for the automatic ask)."""
    s = settings(acc)["brand"]
    if not s["enabled"]:
        return None
    existing = store.redis("HGET", _brands_key(acc["id"]), igsid)
    hit = BRAND_RE.search(text or "")
    if not existing and not hit:
        return None
    if existing and not hit and json.loads(existing).get("updated", 0) > time.time() - 600:
        return None  # a follow-up in a brand chat is re-read at most every 10 minutes
    if not plans.has(acc, "brand_agent") or used(acc, "brand") >= cap(acc, "brand"):
        return None
    system = (f"You are the brand-deal receptionist for the Instagram creator @{acc.get('username', '')}. Decide if this DM chat is a "
              f"brand / business collaboration offer (paid or barter promotion, sponsorship, UGC, affiliate). Extract the details "
              f"said so far; don't invent any. Judge the fit for this creator.\nAbout the creator: {ai_agent.knowledge(acc)[:1500]}\n"
              f"Minimum budget they accept: ₹{s['min_budget'] or 'not set'}. Niches they like: {s['niches'] or 'any that fit'}. "
              f"They avoid: {s['avoid'] or 'nothing listed'}.")
    out = _ask(acc, system, [{**m, "username": username} for m in ai_agent.messages(acc["id"], igsid)], BRAND_SCHEMA)
    if not out:
        return None
    _note(acc, "brand")
    if not out.get("is_brand_offer"):
        return None
    old = json.loads(existing) if existing else {}
    now = int(time.time())
    r = {"chat_id": igsid, "username": username or old.get("username", ""), "status": old.get("status", "new"),
         "created": old.get("created", now), "updated": now, "asked": old.get("asked", False),
         **{k: str(out.get(k, ""))[:300] for k in ("brand", "offer", "budget", "deliverables", "timeline", "why")},
         "fit": out.get("fit") if out.get("fit") in ("good", "maybe", "poor") else "maybe",
         "missing": [str(x)[:40] for x in (out.get("missing") or [])][:6]}
    if s["auto_ask"] and not r["asked"] and r["missing"] and send:
        try:
            send(s["ask_text"])
            ai_agent.add_message(acc["id"], igsid, "ai", s["ask_text"])
            r["asked"] = True
        except Exception:
            pass
    store.redis("HSET", _brands_key(acc["id"]), igsid, json.dumps(r))
    if not existing:
        try:
            import push
            push.notify(acc, f"🤝 Brand request from @{username or 'someone'}", (r["brand"] + " · " + r["offer"])[:120], "/app/agents#brands")
        except Exception:
            pass
        store.log_activity(acc["id"], "agent", username or igsid, text[:200], "brand_request", "ok", r["brand"])
    return r


def on_fan_message(acc, igsid, username, text, send=None):
    """Called for every fan DM stored in the inbox. Never raises: agents are a bonus, not part of the DM flow."""
    for fn in (lambda: check_brand(acc, igsid, username, text, send), lambda: qualify(acc, igsid, username)):
        try:
            fn()
        except Exception as e:
            print(f"agent failed for {acc.get('id')}: {e}")
