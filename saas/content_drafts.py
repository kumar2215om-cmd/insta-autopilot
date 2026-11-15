"""Content plan: the AI drafts a week of posts, the creator approves, changes or rejects each one.

Nothing is posted automatically. An approved draft is ready to film or post; marking it "posted" keeps the plan tidy.
Each draft the AI writes (or rewrites) uses one AI credit from the plan's AI allowance, like an AI DM reply.
Rejected drafts and the creator's notes teach the next week's drafts what to avoid.
"""
import json
import secrets
import time
from datetime import date, timedelta

import ai_agent
import store

FORMATS = ("reel", "carousel", "post", "story")
STATUSES = ("draft", "approved", "rejected", "posted")
MAX_KEEP = 80  # drafts kept per account (oldest rejected/posted ones go first)
MAX_DAYS = 14


def _key(ig_id):
    return store.account_key(ig_id, "drafts")


def load(ig_id):
    return (store.get_json(_key(ig_id)) or {}).get("items", [])


def _save(ig_id, items):
    if len(items) > MAX_KEEP:
        done = sorted((d for d in items if d["status"] in ("rejected", "posted")), key=lambda d: d["updated"])
        drop = {d["id"] for d in done[:len(items) - MAX_KEEP]}
        items = [d for d in items if d["id"] not in drop][-MAX_KEEP:]
    store.set_json(_key(ig_id), {"items": items})


def list_drafts(acc, status="", upcoming_only=False):
    items = load(acc["id"])
    if status:
        items = [d for d in items if d["status"] == status]
    if upcoming_only:
        today = date.today().isoformat()
        items = [d for d in items if d["date"] >= today]
    return sorted(items, key=lambda d: (d["date"], d["created"]))


def get(acc, draft_id):
    return next((d for d in load(acc["id"]) if d["id"] == draft_id), None)


def _clean(d):
    fmt = str(d.get("format", "reel")).lower()
    return {
        "format": fmt if fmt in FORMATS else "reel",
        "hook": str(d.get("hook", "")).strip()[:200],
        "caption": str(d.get("caption", "")).strip()[:2200],
        "outline": [str(x).strip()[:300] for x in (d.get("outline") or []) if str(x).strip()][:10],
        "keyword": str(d.get("keyword", "")).strip().upper().replace(" ", "")[:20],
    }


def update(acc, draft_id, data):
    """Edits fields and/or sets the status. Raises ValueError on bad input or an unknown draft."""
    items = load(acc["id"])
    d = next((x for x in items if x["id"] == draft_id), None)
    if not d:
        raise ValueError("That draft doesn't exist any more.")
    if "status" in data:
        if data["status"] not in STATUSES:
            raise ValueError("Status must be draft, approved, rejected or posted.")
        d["status"] = data["status"]
    if "note" in data:
        d["note"] = str(data["note"] or "").strip()[:500]
    if "date" in data:
        try:
            d["date"] = date.fromisoformat(str(data["date"])).isoformat()
        except ValueError:
            raise ValueError("Date must look like 2026-11-20.")
    edits = {k: data[k] for k in ("format", "hook", "caption", "outline", "keyword") if k in data}
    if edits:
        if isinstance(edits.get("outline"), str):
            edits["outline"] = [x for x in edits["outline"].splitlines()]
        d.update(_clean({**d, **edits}))
        d["edited"] = True
    d["updated"] = int(time.time())
    _save(acc["id"], items)
    return d


def delete(acc, draft_id):
    items = load(acc["id"])
    left = [d for d in items if d["id"] != draft_id]
    if len(left) == len(items):
        raise ValueError("That draft doesn't exist any more.")
    _save(acc["id"], left)


def credits_left(acc):
    _, limit = ai_agent.allowance(acc)
    return max(0, limit - ai_agent.used(acc)) if limit else 10 ** 6


# ---------- the AI ----------

SCHEMA = {
    "type": "object",
    "properties": {"drafts": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "YYYY-MM-DD"},
            "format": {"type": "string", "enum": list(FORMATS)},
            "hook": {"type": "string", "description": "The first line / on-screen hook, max ~12 words."},
            "outline": {"type": "array", "items": {"type": "string"},
                        "description": "Reel: 3-6 script beats. Carousel: one line per slide. Post/story: 1-3 lines."},
            "caption": {"type": "string", "description": "The Instagram caption, ready to paste, with the call to action."},
            "keyword": {"type": "string", "description": "One-word comment keyword for the Auto DM freebie, or empty."},
        },
        "required": ["date", "format", "hook", "outline", "caption", "keyword"],
        "additionalProperties": False,
    }}},
    "required": ["drafts"],
    "additionalProperties": False,
}


def _history(acc):
    """Approved and rejected drafts (with the creator's notes), so the AI learns the creator's taste."""
    items = sorted(load(acc["id"]), key=lambda d: d["updated"], reverse=True)
    liked = [f"- {d['format']}: {d['hook']}" for d in items if d["status"] in ("approved", "posted")][:8]
    nope = [f"- {d['format']}: {d['hook']}" + (f" (creator's note: {d['note']})" if d.get("note") else "")
            for d in items if d["status"] == "rejected"][:8]
    return "\n".join(liked) or "(none yet)", "\n".join(nope) or "(none yet)"


def system_prompt(acc):
    s = ai_agent.settings(acc)
    liked, nope = _history(acc)
    return f"""You are the content strategist for the Instagram creator @{acc.get('username', '')}. You draft posts the creator will review, edit and film themselves.

About the creator (written by them):
{s['about'] or '(not provided: infer the niche from the products and freebies below, and keep ideas general)'}

Their products, links and comment-keyword freebies:
{ai_agent.knowledge(acc)}

Drafts the creator approved before (match this voice and these topics):
{liked}

Drafts the creator rejected (avoid these angles; follow their notes):
{nope}

Rules:
- {ai_agent.LANGUAGE.get(s['language'], ai_agent.LANGUAGE['match']).replace('Reply', 'Write').replace('the fan writes in', 'the creator uses in their About and FAQ')}
- Mostly reels, plus some carousels; a mix of teaching, story, myth-busting and soft-selling. At most one soft sell in three posts.
- When a post can end with a freebie, use the creator's existing keyword (from the list) or suggest a new short keyword, and end the caption with "Comment KEYWORD and I'll DM you ...". Otherwise leave keyword empty.
- Only use facts, prices and links from above. Never invent numbers, results, testimonials or claims.
- Hooks are specific and scroll-stopping, not clickbait. Captions are short: hook line, 2-5 value lines, the call to action, 3-6 hashtags."""


def _ask(acc, request_text, n):
    c = ai_agent.client()
    if c is None:
        raise RuntimeError("AI isn't set up yet: add ANTHROPIC_API_KEY to the server.")
    response = c.messages.create(
        model=ai_agent.AI_MODEL, max_tokens=1500 * n + 1000,
        system=[{"type": "text", "text": system_prompt(acc), "cache_control": {"type": "ephemeral"}}],
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": request_text}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("The AI declined this request. Try a different brief.")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("The AI's answer was cut off. Try fewer days.")
    text = next((b.text for b in response.content if b.type == "text"), "{}")
    return json.loads(text).get("drafts", [])


def _sample(days, start, brief):
    """Demo account and previews: realistic drafts without calling the AI."""
    ideas = [
        ("reel", "3 AI tools jo mera 2 ghante ka kaam 10 min mein karte hain", "TOOLS"),
        ("carousel", "ChatGPT prompts that actually work (save this)", "PROMPTS"),
        ("reel", "Beginners ki sabse badi galti: yeh mat karo", ""),
        ("reel", "Maine 30 din daily reel post kiya. Yeh hua.", ""),
        ("carousel", "Free vs paid tools: kab paisa lagana chahiye?", "GUIDE"),
        ("story", "Poll: aapko next kis topic pe reel chahiye?", ""),
        ("reel", "Ek prompt jo har caption better bana deta hai", "PROMPTS"),
    ]
    out = []
    for i in range(days):
        fmt, hook, kw = ideas[i % len(ideas)]
        cta = f"\n\nComment {kw} and I'll DM you the full list 📩" if kw else "\n\nSave this for later 🔖"
        out.append({"date": (start + timedelta(days=i)).isoformat(), "format": fmt, "hook": hook,
                    "outline": {"reel": ["Hook on screen in the first second", "Show the problem", "Show the fix, step by step",
                                         "Result + call to action"],
                                "carousel": ["Slide 1: hook", "Slides 2-6: one tip each", "Last slide: call to action"],
                                }.get(fmt, ["Poll sticker with 2 topic options"]),
                    "caption": f"{hook}{cta}\n\n#instagramtips #aitools #creator", "keyword": kw})
    return out


def _new(acc, raw, batch):
    now = int(time.time())
    d = _clean(raw)
    try:
        when = date.fromisoformat(str(raw.get("date", ""))).isoformat()
    except ValueError:
        when = date.today().isoformat()
    return {"id": secrets.token_hex(5), "date": when, **d, "status": "draft", "note": "", "batch": batch,
            "created": now, "updated": now}


def fill_week(acc, brief="", days=7, start=None, posts_per_day=1):
    """Drafts posts for `days` days from `start` (default tomorrow). Returns the new drafts.
    Raises ValueError for bad input or too few AI credits, RuntimeError when the AI can't answer."""
    days = max(1, min(MAX_DAYS, int(days or 7)))
    per_day = max(1, min(2, int(posts_per_day or 1)))
    n = days * per_day
    try:
        start = date.fromisoformat(str(start)) if start else date.today() + timedelta(days=1)
    except ValueError:
        raise ValueError("Start date must look like 2026-11-20.")
    brief = str(brief or "").strip()[:1000]
    if not acc.get("demo"):
        if not ai_agent.ready(acc):
            raise RuntimeError("AI isn't set up yet: add ANTHROPIC_API_KEY to the server.")
        if credits_left(acc) < n:
            raise ValueError(f"This needs {n} AI credits and you have {credits_left(acc)} left. "
                             "Try fewer days, or upgrade for more AI credits.")
    taken = sorted({d["date"] for d in load(acc["id"]) if d["status"] != "rejected" and d["date"] >= start.isoformat()})
    if acc.get("demo"):
        raw = _sample(n, start, brief)
    else:
        raw = _ask(acc, f"Draft {n} Instagram posts: {per_day} per day from {start.isoformat()} to "
                        f"{(start + timedelta(days=days - 1)).isoformat()}, one entry per post with its date."
                        + (f"\nDays that already have a planned post (pick other angles): {', '.join(taken)}" if taken else "")
                        + (f"\nThe creator's brief for this week: {brief}" if brief else ""), n)
        for _ in raw[:n]:
            ai_agent.note_use(acc)
    batch = secrets.token_hex(3)
    new = [_new(acc, r, batch) for r in raw[:n] if str(r.get("hook", "")).strip()]
    items = load(acc["id"]) + new
    _save(acc["id"], items)
    return new


def rewrite(acc, draft_id, feedback=""):
    """Rewrites one draft with the creator's feedback (one AI credit). Returns the updated draft."""
    d = get(acc, draft_id)
    if not d:
        raise ValueError("That draft doesn't exist any more.")
    feedback = str(feedback or "").strip()[:500]
    if acc.get("demo"):
        raw = {**d, "hook": d["hook"] + (" (shorter)" if not feedback else f" ({feedback[:40]})")}
    else:
        if not ai_agent.ready(acc):
            raise RuntimeError("AI isn't set up yet: add ANTHROPIC_API_KEY to the server.")
        if credits_left(acc) < 1:
            raise ValueError("No AI credits left this month.")
        current = {k: d[k] for k in ("date", "format", "hook", "outline", "caption", "keyword")}
        got = _ask(acc, "Rewrite this draft (return exactly one draft, same date unless the feedback says otherwise).\n"
                        f"Draft: {json.dumps(current, ensure_ascii=False)}\n"
                        f"Creator's feedback: {feedback or 'make it better: sharper hook, tighter caption'}", 1)
        if not got:
            raise RuntimeError("The AI didn't return a draft. Try again.")
        raw = got[0]
        ai_agent.note_use(acc)
    return update(acc, draft_id, {**_clean(raw), "status": "draft", "note": feedback or d.get("note", "")})


def summary(acc):
    items = load(acc["id"])
    by = {s: sum(1 for d in items if d["status"] == s) for s in STATUSES}
    kind, limit = ai_agent.allowance(acc)
    return {"counts": by, "credits_left": credits_left(acc) if limit else None, "credit_kind": kind,
            "ai_ready": ai_agent.ready(acc)}
