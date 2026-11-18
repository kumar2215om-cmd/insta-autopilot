"""Turn ReplyInbox's guides, comparisons and feature pages into ready-to-post Instagram carousels.

For every page in seo_content.py (GUIDES, COMPARE, FEATURES) this writes, under saas/content/carousels/<slug>/:
  01.png … 08.png   6–8 slides at 1080x1350: hook → one idea per slide → "Comment KEYWORD" CTA
  caption.txt       hook, 3–5 value lines, CTA with the keyword, hashtags
  automation.json   a comment-to-DM rule for the keyword (fields as save_rule in app.py accepts)

The text comes only from seo_content.py (shortened, never rewritten into new claims), so it stays as accurate as
the site. Slides are rendered with the pre-installed Playwright Chromium through Node.

Run (from saas/):
  python3 tools/carousels.py                         # every page
  python3 tools/carousels.py manychat instagram-dm-limits   # only these slugs
  python3 tools/carousels.py --list                  # slugs, keywords and slide text, no images
  python3 tools/carousels.py --no-png                # captions + automations only (fast)
  python3 tools/carousels.py --voice hinglish SLUG   # light-Hinglish CTA/caption for @aiwith.om (writes <slug>-hinglish/)
Options: --out DIR (default content/carousels), --site-url URL (default $SITE_URL or https://replyinbox.in),
         --handle @name (default @replyinbox).
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
SAAS = os.path.dirname(HERE)
sys.path.insert(0, SAAS)

import seo_content  # noqa: E402

BRAND = "ReplyInbox"
MAX_WORDS = 25          # per slide, all slide text except the logo, page counter and "Swipe"
MIN_SLIDES, MAX_SLIDES = 6, 8
CHROMIUM = "/opt/pw-browsers/chromium"

# ---------- text helpers ----------

def words(text):
    return len(re.findall(r"[\w₹$@%][\w'’.,/%₹$@+-]*", text or ""))


def clean(text):
    text = html.unescape(re.sub(r"\s+", " ", text or "")).replace("{brand}", BRAND).strip()
    return re.sub(r"\s+([,.;:!?])", r"\1", text)


def no_parens(text):
    return re.sub(r"\s*\([^()]*\)", "", text).strip()


def sentences(text):
    """Splits at sentence ends, but never inside a "quoted message"."""
    out, cur = [], ""
    for piece in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"“₹${])", text):
        cur = (cur + " " + piece).strip()
        if re.search(r"\b(e\.g|i\.e|etc|vs)\.$", cur):
            continue
        if cur.count('"') % 2 == 0 and cur.count("“") == cur.count("”"):
            out.append(cur)
            cur = ""
    return [s for s in out + [cur] if s]


def shorten(text, limit, hard=False):
    """The shortest faithful version of `text` within `limit` words: drops asides and later clauses, never rewords.
    Returns "" when nothing short enough is left."""
    text = clean(text)
    for cand in (text, no_parens(text)):
        if words(cand) <= limit:
            return cand
    first = (sentences(no_parens(text)) or [""])[0]
    if words(first) <= limit:
        return first
    for sep in ("; ", " — ", " – "):
        head = first.split(sep)[0]
        if words(head) <= limit:
            return head.rstrip(",;:") + ("." if not head.endswith((".", "?", "!")) else "")
    parts = re.split(r"(?<=,) ", first)          # cut at a comma boundary
    out = ""
    for p in parts:
        if words(out + " " + p) > limit:
            break
        out = (out + " " + p).strip()
    if out and words(out) >= max(5, limit // 2):
        return out.rstrip(",") + "…"
    if hard and limit >= 6:                      # last resort for list items: cut at a word, marked with "…"
        cut = " ".join(first.split()[:limit]).rstrip(",;:")
        if cut.count('"') % 2:                   # never leave a quote open
            cut = cut[:cut.rfind('"')].rstrip(" ,;:")
        return cut + "…"
    return ""


# ---------- HTML sections → blocks ----------

class Blocks(HTMLParser):
    """Splits a section's HTML into ("p", lines) / ("ul"|"ol", items) / ("table", rows) / ("chat", [(who, text)])."""

    def __init__(self):
        super().__init__()
        self.blocks, self.buf, self.cells, self.row, self.rows, self.items, self.kind = [], "", [], None, None, None, None
        self.in_head = False

    def flush_p(self):
        text = self.buf
        self.buf = ""
        lines = [clean(re.sub(r"<[^>]+>", "", l)) for l in text.split("\n")]
        lines = [l for l in lines if l]
        if not lines:
            return
        chat = [re.match(r"^\[\[(.+?):\]\]\s*(.*)$", l) for l in lines]
        if all(chat):
            self.blocks.append(("chat", [(m.group(1), m.group(2)) for m in chat]))
        else:
            self.blocks.append(("p", [re.sub(r"\[\[(.+?)\]\]", r"\1", l) for l in lines]))

    def handle_starttag(self, tag, attrs):
        if tag in ("ul", "ol"):
            self.flush_p()
            self.kind, self.items = tag, []
        elif tag == "li":
            self.buf = ""
        elif tag == "table":
            self.flush_p()
            self.rows = []
        elif tag == "thead":
            self.in_head = True
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.buf = ""
        elif tag == "br":
            self.buf += "\n"
        elif tag == "b" and self.items is None and self.rows is None:
            self.buf += "[["
        elif tag == "p":
            self.flush_p()

    def handle_endtag(self, tag):
        if tag == "li" and self.items is not None:
            self.items.append(clean(self.buf))
            self.buf = ""
        elif tag in ("ul", "ol") and self.items is not None:
            self.blocks.append((self.kind, [i for i in self.items if i]))
            self.items = None
        elif tag in ("td", "th") and self.row is not None:
            self.row.append(clean(self.buf))
            self.buf = ""
        elif tag == "tr" and self.row is not None:
            if not self.in_head:
                self.rows.append(self.row)
            self.row = None
        elif tag == "thead":
            self.in_head = False
        elif tag == "table" and self.rows is not None:
            self.blocks.append(("table", self.rows))
            self.rows = None
        elif tag == "b" and self.items is None and self.rows is None:
            self.buf += "]]"
        elif tag in ("p", "pre"):
            self.flush_p()

    def handle_data(self, data):
        self.buf += data

    def close(self):
        super().close()
        self.flush_p()
        return self.blocks


def blocks_of(section_html):
    p = Blocks()
    p.feed(section_html.replace("{brand}", BRAND))
    return p.close()


# ---------- slides ----------
# A slide is a dict: kind ("hook"|"answer"|"list"|"text"|"chat"|"cta"), kicker, title, body (list of lines), note,
# ordered (bool), start (first number of an ordered list).

def slide_words(s):
    parts = [s.get("kicker", ""), s.get("title", ""), s.get("accent", ""), s.get("sub", ""), s.get("note", ""),
             s.get("keyword", ""), s.get("cta", ""), s.get("follow", "")]
    parts += [l if isinstance(l, str) else " ".join(l) for l in s.get("body", [])]
    return sum(words(p) for p in parts)


def fit_lines(items, budget, per_item=10):
    """Shortened items that fit the word budget, in order; stops at the first item that doesn't fit."""
    out = []
    for it in items:
        left = budget - sum(words(o) for o in out)
        short = shorten(it, min(per_item, left)) or (shorten(it, left, hard=True) if left >= 6 else "")
        if not short:
            break
        out.append(short)
    return out


HEDGE = re.compile(r"^(Prices|Competitor|Note|Plans)\b")


def section_slides(heading, body_html, n):
    dated = re.search(r"\(([^()]+)\)", clean(heading))   # "(checked November 2026)", "(handed over)" stay visible
    heading = shorten(no_parens(clean(heading)), 7) or clean(heading)
    kicker = f"{n:02d}" + (f" · {dated.group(1)}" if dated else "")
    budget = MAX_WORDS - words(heading) - words(kicker)
    blocks = blocks_of(body_html)
    hedge = next((" ".join(d) for k, d in blocks if k == "p" and HEDGE.match(" ".join(d))), "")
    hedge = shorten(hedge, 8) if hedge else ""
    slides = []
    for kind, data in blocks:
        if kind == "ol":
            steps = [shorten(it, 12, hard=True) for it in data]
            start, part = 1, []
            for st in steps:                          # steps keep their order: packed over slides, never skipped
                if part and words(" ".join(part + [st])) > budget:
                    slides.append(dict(kind="list", kicker=kicker, title=heading, body=part, ordered=True, start=start))
                    start, part = start + len(part), []
                part.append(st)
            if part:
                slides.append(dict(kind="list", kicker=kicker, title=heading, body=part, ordered=True, start=start))
        elif kind == "ul":
            part = fit_lines(data, budget) or fit_lines(data[:1], budget, per_item=budget)
            if len(part) >= 2 or (part and len(data) == 1):
                slides.append(dict(kind="list", kicker=kicker, title=heading, body=part, ordered=False))
        elif kind == "table":
            rows = [f"{r[0]}: {r[-1]}" if len(r) > 1 else r[0] for r in data]
            chunks = []
            while rows:
                part = fit_lines(rows, budget - words(hedge), per_item=11)
                if not part:
                    break
                chunks.append(part)
                rows = rows[len(part):]
            flat = [r for c in chunks for r in c]
            if len(chunks) > 1:                       # even out the slides (no lonely last row)
                per = -(-len(flat) // len(chunks))
                even = [flat[k:k + per] for k in range(0, len(flat), per)]
                if len(even) == len(chunks) and all(sum(words(r) for r in c) <= budget - words(hedge) for c in even):
                    chunks = even
            for part in chunks:                       # every slide of a price table carries the section's hedge
                slides.append(dict(kind="list", kicker=kicker, title=heading, body=part, ordered=False, table=True, note=hedge))
        elif kind == "chat":
            lines, used = [], 0
            for who, text in data:
                short = shorten(text, budget - used - words(who))
                if not short:
                    break
                lines.append((who, short))
                used += words(who) + words(short)
            if lines:
                slides.append(dict(kind="chat", kicker=kicker, title=heading, body=lines))
        elif kind == "p":
            text = " ".join(data)
            if HEDGE.match(text):                    # a hedge: already shown on the table slides above
                if slides and not slides[-1].get("note"):
                    slides[-1]["note"] = shorten(text, MAX_WORDS - slide_words(slides[-1]))
                continue
            part = fit_lines(sentences(text), budget, per_item=budget)
            if part:
                slides.append(dict(kind="text", kicker=kicker, title=heading, body=[" ".join(part)]))
    return slides


def title_hook(title, override=None):
    """(plain, accent) for the hook headline; accent is set in Instrument Serif italic."""
    if override:
        return override
    t = no_parens(clean(title))
    w = t.split()
    k = 1 if len(w) <= 4 else 2
    return " ".join(w[:-k]), " ".join(w[-k:])


HOOKS = {
    "is-instagram-dm-automation-safe": ("Will auto DMs get your Instagram", "banned?"),
    "why-instagram-dm-not-sent": ("Auto DM not sending?", "Here's why"),
    "instagram-dm-limits": ("Instagram's DM limits,", "explained"),
    "get-followers-from-reels": ("Turn reel views into", "followers"),
    "instagram-comment-keyword-ideas": ("40 comment keyword ideas for your", "reels"),
    "instagram-dm-automation-pricing": ("What Instagram DM automation really", "costs"),
    "how-to-auto-dm-instagram-comments": ("Auto DM everyone who comments on your", "reel"),
    "ai-dm-agent-examples": ("What an AI DM agent actually", "says"),
    "manage-instagram-automations-with-claude": ("Run your Instagram automations from", "Claude"),
}

# Comment keywords: one short word per carousel, unique, valid for a "kw:" rule. Auto-picked from the slug unless set here.
KEYWORDS = {
    "how-to-auto-dm-instagram-comments": "AUTODM", "best-instagram-dm-automation-tools": "TOOLS",
    "manychat-alternatives": "ALTERNATIVES", "how-to-collect-emails-from-instagram": "EMAILS",
    "sell-digital-products-on-instagram": "SELL", "instagram-story-auto-reply": "STORY",
    "instagram-comment-keyword-ideas": "KEYWORDS", "auto-reply-instagram-comments": "REPLIES",
    "why-instagram-dm-not-sent": "FIX", "switch-to-instagram-professional-account": "SWITCH",
    "instagram-ai-chatbot": "CHATBOT", "instagram-lead-magnet-ideas": "MAGNET", "instagram-dm-automation-for-ecommerce": "STORE",
    "run-instagram-giveaway": "GIVEAWAY", "instagram-dm-automation-for-real-estate": "PROPERTY",
    "instagram-follow-up-messages": "FOLLOWUP", "instagram-dm-sales-funnel": "FUNNEL", "track-instagram-sales-with-utm": "UTM",
    "write-faq-for-ai-dm-agent": "FAQ", "ai-vs-keyword-dm-automation": "AIVSKEYWORD", "collect-whatsapp-numbers-from-instagram": "WHATSAPP",
    "instagram-dm-choice-menus": "MENU", "instagram-next-post-automation": "NEXTPOST", "instagram-live-comment-automation": "LIVE",
    "instagram-welcome-message": "WELCOME", "instagram-ice-breakers": "ICEBREAKERS", "ai-dm-replies-in-any-language": "LANGUAGE",
    "ai-handoff-rules": "HANDOFF", "instagram-ai-chatbot-cost": "AICOST", "is-ai-safe-for-instagram-dms": "AISAFE",
    "ai-inbox-daily-workflow": "ROUTINE", "manage-instagram-automations-with-claude": "CLAUDE", "ai-dm-agent-examples": "EXAMPLES",
    "is-instagram-dm-automation-safe": "SAFE", "comment-to-dm": "COMMENTDM", "follow-to-unlock": "UNLOCK", "ai-dm-agent": "AGENT",
    "story-replies": "STORIES", "lead-capture": "LEADS", "sales-tracking": "SALES",
}
STOP = set("how to the a an for and on your with of is in why what instagram dm dms automation set up get from vs messages "
           "people who best".split())


def keyword_for(slug):
    if slug in KEYWORDS:
        return KEYWORDS[slug]
    if slug in seo_content.COMPARE:
        return re.sub(r"[^A-Z0-9]", "", seo_content.COMPARE[slug]["name"].upper().split()[0])
    rest = [w for w in slug.split("-") if w not in STOP]
    return (rest[0] if rest else slug.split("-")[0]).upper()


def pages():
    """[(kind, slug, page)] for every guide, comparison and feature, in site order."""
    return ([("guide", s, p) for s, p in seo_content.GUIDES.items()] + [("compare", s, p) for s, p in seo_content.COMPARE.items()]
            + [("feature", s, p) for s, p in seo_content.FEATURES.items()])


def page_url(kind, slug, site):
    return site.rstrip("/") + {"guide": "/guides/", "compare": "/vs/", "feature": "/features/"}[kind] + slug


VAGUE = re.compile(r"^(Each|It|This|That|They|These|Those|Both|Here|So)\b")


def answer_slides(answer, title="The short answer", reserve=0):
    """The answer's sentences as slides: the first one that fits whole leads; a cut sentence ("…") only if none fits."""
    budget = MAX_WORDS - words(title) - 2 - reserve
    whole, lead = [], []
    for k, s in enumerate(sentences(clean(answer))):
        short = shorten(s, budget)
        if not short or (k and (VAGUE.match(short) or words(short) < 7)):
            continue
        if k == 0 and (short.endswith("…") or words(short) >= words(no_parens(s)) * 0.6):
            lead = [short]                        # the first sentence leads, even shortened
        elif words(short) >= words(no_parens(s)) * 0.6 and not short.endswith("…"):
            whole.append(short)
    picked = (lead + whole) if lead else whole
    return [dict(kind="answer", kicker="In short", title=title if k == 0 else "Good to know", body=[b])
            for k, b in enumerate(picked)]


def build(kind, slug, page, voice="english", handle="@replyinbox"):
    """The carousel for one page: {'slug', 'kind', 'keyword', 'slides', 'caption', 'url'} (url without site)."""
    kw = keyword_for(slug)
    if kind == "compare":
        name = page["name"]
        hook = dict(kind="hook", kicker=f"Compared · {seo_content.CHECKED}", title=f"{name} vs", accent=BRAND,
                    sub="Which one fits you? A quick, honest look.")
        content = answer_slides(page["answer"], "The short version", reserve=4)[:1]
        for s in content:
            s["note"] = f"As checked {seo_content.CHECKED}."
        them = fit_lines(page["them"], MAX_WORDS - 4 - 6, per_item=9)
        us = fit_lines(page["us"], MAX_WORDS - 4 - 2, per_item=9)
        content += [dict(kind="list", kicker=f"{name} · as checked {seo_content.CHECKED}", title=f"What {name} offers", body=them),
                    dict(kind="list", kicker=BRAND, title=f"What {BRAND} offers", body=us, ours=True),
                    dict(kind="text", kicker="Choose", title=f"Pick {name} if", body=[shorten(page["choose_them"], 18)]),
                    dict(kind="text", kicker="Choose", title=f"Pick {BRAND} if", body=[shorten(page["choose_us"], 18)], ours=True)]
        what = "full comparison"
    else:
        plain, accent = title_hook(page["title"], HOOKS.get(slug))
        sub = shorten(page["description"], min(16, MAX_WORDS - words(plain + " " + accent) - 2))
        sub = "" if sub.endswith("…") or sub.rstrip(".?!").lower() in (plain + " " + accent).lower() else sub
        hook = dict(kind="hook", kicker="Feature" if kind == "feature" else "Guide", title=plain, accent=accent, sub=sub)
        answers = answer_slides(page["answer"])
        sections = []
        for i, (h, b) in enumerate(page["sections"], 1):
            sections += section_slides(h, b, i)
        faq = []
        for q, a in page.get("faq", []):
            q = clean(q)
            a = shorten(a, MAX_WORDS - words(q) - 1)
            if a and words(q) <= 12:
                faq.append(dict(kind="text", kicker="FAQ", title=q, body=[a]))
        content = answers[:1] + sections
        content += faq + answers[1:]                     # fillers if the sections are short
        what = "full guide"
    content = [s for s in content if s.get("body") and all(s["body"])][:MAX_SLIDES - 2]
    if voice == "hinglish":
        cta = dict(kind="cta", cta_pre="Comment", keyword=kw, cta=f"karo, main {what} DM kar dunga", follow=f"Follow {handle} for more")
    else:
        cta = dict(kind="cta", cta_pre="Comment", keyword=kw, cta=f"and I'll DM you the {what}", follow=f"Follow {handle} for more")
    slides = [hook] + content + [cta]
    return dict(slug=slug, kind=kind, keyword=kw, slides=slides, what=what,
                caption=caption(kind, page, hook, content, kw, what, voice))


# ---------- caption + automation ----------

TAGS_BASE = ["#instagramtips", "#instagramautomation", "#creatortips"]
TAGS_TOPIC = [
    (r"\bai\b|chatbot|agent|claude|language", ["#aitools", "#chatbot"]),
    (r"sell|sales|ecommerce|store|funnel|utm|product", ["#digitalproducts", "#onlinebusiness"]),
    (r"email|lead|whatsapp|magnet", ["#leadgeneration", "#emailmarketing"]),
    (r"coach", ["#coachingbusiness"]),
    (r"fitness", ["#fitnesscoach"]),
    (r"finance", ["#financecreator"]),
    (r"educator", ["#edtech"]),
    (r"food", ["#homebaker"]),
    (r"beauty", ["#beautycreator"]),
    (r"travel", ["#travelcreator"]),
    (r"real-estate", ["#realestatemarketing"]),
    (r"astrolog", ["#astrology"]),
    (r"reel|follower|keyword|giveaway|story|live", ["#reelstips", "#instagramgrowth"]),
    (r"safe|limit|not-sent|professional", ["#instagramhelp"]),
]


def hashtags(kind, slug, page):
    tags = list(TAGS_BASE)
    for pat, add in TAGS_TOPIC:
        if re.search(pat, slug):
            tags += [t for t in add if t not in tags]
    if kind == "compare":
        tags.append("#" + re.sub(r"[^a-z0-9]", "", page["name"].lower()))
    for extra in ("#dmautomation", "#contentcreator", "#socialmediamarketing"):
        if len(tags) >= 6:
            break
        tags.append(extra)
    return tags[:8]


def caption(kind, page, hook, content, kw, what, voice):
    head = (hook["title"] + " " + hook["accent"]).strip()
    lines = []
    for s in content:
        for b in s["body"]:
            text = b if isinstance(b, str) else f"{b[0]}: {b[1]}"
            if text not in lines:
                lines.append(text)
    whole = [l for l in lines if words(l) <= 25 and not l.endswith("…")]
    value = (whole if len(whole) >= 3 else whole + [l for l in lines if l.endswith("…")])[:5]
    out = [head, ""] + ["→ " + l for l in value] + [""]
    if kind == "compare" or "pricing" in page.get("title", "").lower():
        out += [f"Competitor details as checked {seo_content.CHECKED}; prices and plans change, so check their site.", ""]
    if voice == "hinglish":
        out.append(f"Comment {kw} karo, main {what} DM kar dunga 📩")
    else:
        out.append(f"Comment {kw} and I'll DM you the {what} 📩")
    return out


def caption_text(c, page):
    lines = c["caption"] + ["", " ".join(hashtags(c["kind"], c["slug"], page))]
    return "\n".join(lines).strip() + "\n"


def automation(c, url, voice="english"):
    """A keyword rule for PUT /api/rules/kw:<KEYWORD> (or the save_automation tool): fields as save_rule accepts."""
    kw = c["keyword"]
    if voice == "hinglish":
        replies = ["@{username} DM check karo 📩", "Bhej diya! Inbox dekho ✅", "@{username} Sent! Requests folder bhi check kar lena 🙌"]
        dm = f"Ye raha {c['what']} 👇\n{url}\n\nKoi sawaal ho toh yahin reply karo 🙌"
    else:
        replies = ["@{username} Sent! Check your DMs 📩", "Done ✅ check your inbox", "@{username} DM sent! Peek in your requests if you don't see it 🙌"]
        dm = f"Here's the {c['what']} 👇\n{url}\n\nQuestions? Just reply here 🙌"
    return {
        "key": "kw:" + kw,
        "rule": {
            "enabled": True,
            "keywords": [kw],
            "comment_reply": "\n".join(replies),
            "replies_on": True,
            "opening_dm": "Hey {username}! 👋 Tap below and I'll send it right over.",
            "button_text": "Send it",
            "require_follow": True,
            "follow_dm": 'Almost there! 👀 Follow us first, then tap "I followed" below.',
            "followed_button_text": "I followed ✅",
            "dm": dm,
            "dm_button_text": "Open the guide" if c["what"] == "full guide" else "Open it",
            "dm_button_url": url,
            "once_per_person": True,
            "track_links": True,
            "tags": "carousel",
            "label": f"Carousel: {c['slug']}",
        },
    }


# ---------- HTML ----------

def logo_mark(size, uid):
    import jinja2
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(SAAS, "templates")))
    return str(env.get_template("_logo.html").module.mark(size, uid))


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1350px;overflow:hidden}
body{font-family:Geist,Inter,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.s{position:relative;width:1080px;height:1350px;padding:88px 92px 0;display:flex;flex-direction:column;overflow:hidden}
.ink{background:#0C0B10;color:#fff}.paper{background:#F7F5F0;color:#0C0B10}
.grad{background:linear-gradient(140deg,#7B5CFF 0%,#B05CE8 55%,#FF7A59 100%);color:#fff}
.glow{position:absolute;inset:0;background:radial-gradient(55% 45% at 15% 12%,rgba(123,92,255,.55),transparent 70%),radial-gradient(50% 40% at 100% 100%,rgba(255,122,89,.38),transparent 70%)}
.grid{position:absolute;inset:0;opacity:.6;background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:72px 72px;-webkit-mask-image:radial-gradient(90% 70% at 25% 25%,#000 30%,transparent 85%)}
.paper .grid{background-image:linear-gradient(rgba(12,11,16,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(12,11,16,.05) 1px,transparent 1px)}
.top{position:relative;display:flex;align-items:center;justify-content:space-between}
.logo{display:flex;align-items:center;gap:20px;font-weight:600;font-size:44px;letter-spacing:-.035em}
.logo span{color:#6A4CFF}.ink .logo span,.grad .logo span{color:#B9A8FF}.grad .logo span{color:#fff;opacity:.8}
.count{font:500 40px "Geist Mono",monospace;opacity:.55;letter-spacing:.02em}
.main{position:relative;flex:1;display:flex;flex-direction:column;justify-content:center;padding-bottom:40px}
.kicker{font:500 40px "Geist Mono",monospace;text-transform:uppercase;letter-spacing:.06em;color:#6A4CFF;margin-bottom:34px}
.ink .kicker{color:#B9A8FF}
h1{font-weight:600;font-size:112px;line-height:1.0;letter-spacing:-.05em}
h2{font-weight:600;font-size:94px;line-height:1.04;letter-spacing:-.045em;margin-bottom:52px}
em{font-family:"Instrument Serif",serif;font-weight:400;font-style:italic;letter-spacing:-.01em;background:linear-gradient(120deg,#8B6CFF,#C06BE6 55%,#FF8A6A);-webkit-background-clip:text;background-clip:text;color:transparent;padding-right:.08em}
.sub{margin-top:44px;font-size:54px;line-height:1.3;color:#B4B0C0;letter-spacing:-.02em}
.body{font-size:68px;line-height:1.28;letter-spacing:-.025em}
.text{color:#2A2733}.ink .text{color:#ECE9F2}
ul.l{list-style:none;display:flex;flex-direction:column;gap:40px}
ul.l li{display:flex;gap:30px;align-items:flex-start;font-size:62px;line-height:1.22;letter-spacing:-.025em}
.mk{flex:none;width:84px;height:84px;border-radius:24px;display:flex;align-items:center;justify-content:center;font:600 44px "Geist Mono",monospace;color:#fff;background:linear-gradient(140deg,#7B5CFF,#B05CE8 60%,#FF7A59);margin-top:-8px}
.dot{flex:none;width:28px;height:28px;border-radius:50%;margin-top:24px;background:linear-gradient(140deg,#7B5CFF,#FF7A59)}
.them .dot{background:#9C98A8}
.chat{display:flex;flex-direction:column;gap:30px}
.b{max-width:90%;padding:32px 40px;border-radius:40px;font-size:56px;line-height:1.28;letter-spacing:-.02em}
.b small{display:block;font:500 40px "Geist Mono",monospace;opacity:.7;margin-bottom:8px;letter-spacing:.04em}
.b.in{background:#fff;border:2px solid #E6E1D6;align-self:flex-start;border-bottom-left-radius:12px}
.b.out{background:#6A4CFF;color:#fff;align-self:flex-end;border-bottom-right-radius:12px}
.note{margin-top:44px;font:500 40px/1.3 "Geist Mono",monospace;color:#6B6777;letter-spacing:-.01em}
.foot{position:relative;display:flex;align-items:center;justify-content:space-between;height:150px;font:500 40px "Geist Mono",monospace;opacity:.6}
.bar{position:absolute;left:0;bottom:0;height:14px;background:linear-gradient(90deg,#7B5CFF,#B05CE8 60%,#FF7A59)}
.cta-pre{font-weight:600;font-size:96px;letter-spacing:-.045em}
.kw{display:inline-block;margin:36px 0 40px;padding:26px 52px;border-radius:36px;background:#fff;color:#4B2FE6;font:600 128px "Geist Mono",monospace;letter-spacing:-.02em;box-shadow:0 30px 80px -20px rgba(40,10,90,.45);white-space:nowrap}
.cta{font-weight:600;font-size:84px;line-height:1.05;letter-spacing:-.045em}
.cta em{background:none;color:#fff;-webkit-background-clip:initial;background-clip:initial}
.follow{margin-top:60px;font:500 44px "Geist Mono",monospace;opacity:.85}
"""

FONTS = ('<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@500;600'
         '&family=Instrument+Serif:ital@1&display=block" rel="stylesheet">')


def e(text):
    return html.escape(text, quote=False)


def slide_html(s, i, n, mark):
    tone = {"hook": "ink", "answer": "ink", "cta": "grad"}.get(s["kind"], "paper")
    top = (f'<div class="top"><div class="logo">{mark}<div>Reply<span>Inbox</span></div></div>'
           f'<div class="count">{i}/{n}</div></div>')
    if s["kind"] == "hook":
        main = (f'<div class="kicker">{e(s["kicker"])}</div><h1>{e(s["title"])} <em>{e(s["accent"])}</em></h1>'
                + (f'<p class="sub">{e(s["sub"])}</p>' if s.get("sub") else ""))
        foot = '<div class="foot"><span>Swipe</span><span>→</span></div>'
    elif s["kind"] == "cta":
        what = s["cta"]
        for phrase in ("full guide", "full comparison"):
            what = e(what).replace(phrase, f"<em>{phrase}</em>") if phrase in what else what
        main = (f'<div class="cta-pre">{e(s["cta_pre"])}</div><div><span class="kw">{e(s["keyword"])}</span></div>'
                f'<div class="cta">{what if "<em>" in what else e(what)}</div><div class="follow">{e(s["follow"])}</div>')
        foot = '<div class="foot"></div>'
    else:
        if s["kind"] in ("text", "answer"):
            body = f'<p class="body text">{e(s["body"][0])}</p>'
        elif s["kind"] == "chat":
            body = '<div class="chat">' + "".join(
                f'<div class="b {"in" if who.lower() in ("fan", "brand", "you", "customer") else "out"}"><small>{e(who)}</small>{e(t)}</div>'
                for who, t in s["body"]) + "</div>"
        else:
            start = s.get("start", 1)
            body = f'<ul class="l{"" if s.get("ours") or s.get("ordered") or s.get("table") else " them" if s["title"].startswith("What ") else ""}">' + "".join(
                f'<li>{f"<span class=mk>{start + k}</span>" if s.get("ordered") else "<span class=dot></span>"}<span>{e(t)}</span></li>'
                for k, t in enumerate(s["body"])) + "</ul>"
        note = f'<p class="note">{e(s["note"])}</p>' if s.get("note") else ""
        main = f'<div class="kicker">{e(s["kicker"])}</div><h2>{e(s["title"])}</h2>{body}{note}'
        foot = '<div class="foot"></div>'
    bar = f'<div class="bar" style="width:{round(100 * i / n, 2)}%"></div>'
    glow = '<div class="glow"></div><div class="grid"></div>' if tone == "ink" else '<div class="grid"></div>' if tone == "paper" else ""
    return (f'<!doctype html><html><head><meta charset="utf-8">{FONTS}<style>{CSS}</style></head>'
            f'<body><div class="s {tone}">{glow}{top}<div class="main">{main}</div>{foot}{bar}</div></body></html>')


# Shrinks text that would overflow (long headings or bodies) down to readable floors, then reports what still overflows.
FIT_JS = r"""
() => {
  const main = document.querySelector('.main');
  const over = () => main.scrollHeight > main.clientHeight + 1 || [...document.querySelectorAll('.kw')].some(k => k.scrollWidth > 900);
  const shrink = (sel, floor) => { for (const el of document.querySelectorAll(sel)) {
      let fs = parseFloat(getComputedStyle(el).fontSize); if (fs > floor) { el.style.fontSize = (fs - 2) + 'px'; return true; } } return false; };
  for (let k = 0; k < 200 && over(); k++) {
    if (!(shrink('.kw', 72) || shrink('h1', 84) || shrink('h2', 64) || shrink('ul.l li', 46) || shrink('.body', 46)
          || shrink('.b', 44) || shrink('.sub', 42))) break;
  }
  return over();
}
"""

RENDER_JS = r"""
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const fit = eval(fs.readFileSync(process.argv[3], 'utf8'));
  let browser;
  try { browser = await chromium.launch(); } catch (e) { browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' }); }
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  const bad = [];
  for (const j of jobs) {
    await page.goto('file://' + j.html, { waitUntil: 'networkidle', timeout: 30000 }).catch(() => {});
    await page.evaluate(() => document.fonts.ready);
    if (await page.evaluate(fit)) bad.push(j.png);
    await page.screenshot({ path: j.png, type: 'png' });
  }
  await browser.close();
  if (bad.length) console.log('OVERFLOW ' + JSON.stringify(bad));
})();
"""


def render(jobs):
    """jobs: [(html_text, png_path)]. Renders all in one Chromium. Returns the PNGs whose text still overflows."""
    with tempfile.TemporaryDirectory() as tmp:
        spec = []
        for k, (doc, png) in enumerate(jobs):
            path = os.path.join(tmp, f"{k}.html")
            with open(path, "w") as f:
                f.write(doc)
            spec.append({"html": path, "png": os.path.abspath(png)})
        for name, text in (("jobs.json", json.dumps(spec)), ("fit.js", FIT_JS), ("render.js", RENDER_JS)):
            with open(os.path.join(tmp, name), "w") as f:
                f.write(text)
        out = subprocess.run(["node", os.path.join(tmp, "render.js"), os.path.join(tmp, "jobs.json"), os.path.join(tmp, "fit.js")],
                             capture_output=True, text=True, cwd=tmp, env={**os.environ, "NODE_PATH": node_path()})
        if out.returncode:
            sys.exit("Rendering failed:\n" + out.stderr[-2000:])
        m = re.search(r"OVERFLOW (\[.*\])", out.stdout)
        return json.loads(m.group(1)) if m else []


def node_path():
    """Where the pre-installed playwright package lives, so `require('playwright')` works from a temp dir."""
    try:
        root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
    except OSError:
        root = ""
    return os.pathsep.join(p for p in (os.environ.get("NODE_PATH", ""), root) if p)


# ---------- main ----------

def write(c, page, out_dir, site, voice, png):
    d = os.path.join(out_dir, c["slug"] + ("-hinglish" if voice == "hinglish" else ""))
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d) if png else []:       # old slides go only when new ones are rendered
        if re.match(r"^\d\d\.png$", f):
            os.remove(os.path.join(d, f))
    url = page_url(c["kind"], c["slug"], site)
    with open(os.path.join(d, "caption.txt"), "w") as f:
        f.write(caption_text(c, page))
    with open(os.path.join(d, "automation.json"), "w") as f:
        json.dump(automation(c, url, voice), f, ensure_ascii=False, indent=2)
        f.write("\n")
    jobs = []
    if png:
        n = len(c["slides"])
        for i, s in enumerate(c["slides"], 1):
            jobs.append((slide_html(s, i, n, logo_mark(60, f"ri{i}")), os.path.join(d, f"{i:02d}.png")))
    return jobs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--out", default=os.path.join(SAAS, "content", "carousels"))
    ap.add_argument("--site-url", default=os.environ.get("SITE_URL") or "https://replyinbox.in")
    ap.add_argument("--handle", default="@replyinbox")
    ap.add_argument("--voice", choices=("english", "hinglish"), default="english")
    ap.add_argument("--list", action="store_true", help="print slugs, keywords and slide text only")
    ap.add_argument("--no-png", action="store_true", help="write caption.txt and automation.json only")
    a = ap.parse_args(argv)
    todo = [(k, s, p) for k, s, p in pages() if not a.slugs or s in a.slugs]
    missing = set(a.slugs) - {s for _, s, _ in todo}
    if missing:
        sys.exit("Unknown slug(s): " + ", ".join(sorted(missing)))
    jobs = []
    for kind, slug, page in todo:
        c = build(kind, slug, page, a.voice, a.handle)
        if a.list:
            print(f"\n== {slug}  [{kind}]  keyword {c['keyword']}  {len(c['slides'])} slides")
            for i, s in enumerate(c["slides"], 1):
                body = " | ".join(b if isinstance(b, str) else f"{b[0]}: {b[1]}" for b in s.get("body", []))
                print(f"  {i}. ({slide_words(s)}w) {s.get('title', s.get('cta_pre', ''))} {s.get('accent', s.get('keyword', ''))} :: "
                      f"{s.get('sub', '')}{body}{s.get('cta', '')}{(' [' + s['note'] + ']') if s.get('note') else ''}")
            continue
        jobs += write(c, page, a.out, a.site_url, a.voice, not a.no_png)
    if jobs:
        bad = render(jobs)
        for b in bad:
            print("Warning: text still overflows on", os.path.relpath(b, SAAS))
    if not a.list:
        print(f"Wrote {len(todo)} carousel(s) to {os.path.relpath(a.out, os.getcwd())}"
              + ("" if a.no_png else f" ({len(jobs)} slides)"))


if __name__ == "__main__":
    main()
