"""Text freebies (.txt / .md uploaded in Files) shown as designed guide pages, in the same look as the link page.

/f/<id>/<name>.txt opens as a guide: the creator's photo and handle, a big two-tone title, section chips, one card
per heading, copy buttons on prompts and code, the creator's top product as a card in the middle and a slim bar on
top, and a Follow button at the end. ?raw=1 gives the plain file.

Text → Markdown comes from the root app's tools/doc2md.py (headings guessed from short lines, bullets, numbered
steps); the page itself follows tools/guidepage.py. Theme colours: static/guide-theme.css (copy of freebies/theme.css).
"""
import html
import re
from collections import Counter

e = html.escape
BULLET = re.compile(r"^\s*[•●▪◦‣∙·\-–*]\s+")
NUMBERED = re.compile(r"^\s*(\d{1,2})[.)]\s+")
HEADWORD = re.compile(r"^(step|module|part|chapter|section|bonus|day|lesson|prompt)\s*\d*\b", re.I)
GUIDE_EXTS = ("txt", "md")


# ---------- plain text → Markdown (from tools/doc2md.py) ----------

def _is_heading(line, prev_blank, next_blank):
    s = line.strip()
    if not (2 < len(s) <= 70) or BULLET.match(s) or s.endswith((",", ";")):
        return False
    letters = [c for c in s if c.isalpha()]
    if len(letters) >= 3 and s.upper() == s and not s.endswith("."):
        return True
    if HEADWORD.match(s) and len(s.split()) <= 9 and not s.endswith("."):
        return True
    return prev_blank and next_blank and len(s.split()) <= 8 and not s.endswith((".", "?", "!", ":"))


def text_to_md(text, max_chars=60000):
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    if re.search(r"^#{1,3} ", text, re.M):
        return text.strip()[:max_chars]
    raw = [l.rstrip() for l in text.split("\n")]
    seen = Counter(l.strip() for l in raw if l.strip())
    raw = [l for l in raw if not (l.strip() and len(l.strip()) < 100 and seen[l.strip()] >= 3)]
    out, para = [], []

    def flush():
        if para:
            out.append("\n".join(para))  # keep line breaks: prompts show them, paragraphs join them
            out.append("")
            para.clear()

    first = True
    for i, line in enumerate(raw):
        s = line.strip()
        if not s:
            flush()
            continue
        prev_blank = i == 0 or not raw[i - 1].strip()
        next_blank = i + 1 >= len(raw) or not raw[i + 1].strip()
        if first and len(s) <= 90 and next_blank:  # the first short line is the title
            out.extend([f"# {s}", ""])
            first = False
            continue
        first = False
        if _is_heading(s, prev_blank, next_blank):
            flush()
            if out and out[-1] != "":
                out.append("")
            out.extend([f"## {s.rstrip(':')}", ""])
            continue
        if BULLET.match(s):
            flush()
            out.append("- " + BULLET.sub("", s))
            continue
        m = NUMBERED.match(s)
        if m:
            flush()
            out.append(f"{m.group(1)}. " + NUMBERED.sub("", s))
            continue
        para.append(s)
    flush()
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()[:max_chars]


# ---------- Markdown → guide page ----------

def inline(t):
    t = e(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    t = re.sub(r"\[(.+?)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r'(?<!["=>])(https?://[^\s<]+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', t)
    return t


def copy_box(text, label="Copy"):
    return (f'<div class="code prompt"><button class="cp" type="button" onclick="cp(this)">copy</button>'
            f'<div class="lbl">{e(label)}</div><pre>{e(text)}</pre></div>')


def blocks_html(md, prompts=False):
    """A section's Markdown → HTML. In a "Prompt …" section, plain paragraphs become copyable prompt boxes."""
    out, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            out.append(copy_box("\n".join(lines[i + 1:j]), s.strip("`") or "Copy"))
            i = j + 1
            continue
        if s.startswith(("- ", "* ")):
            items = []
            while i < len(lines) and lines[i].strip().startswith(("- ", "* ")):
                items.append(lines[i].strip()[2:])
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue
        if NUMBERED.match(s):
            items = []
            while i < len(lines) and NUMBERED.match(lines[i].strip()):
                items.append(NUMBERED.sub("", lines[i].strip()))
                i += 1
            out.append('<ol class="num">' + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue
        if s.startswith(">"):
            out.append(f'<div class="tip">💡 {inline(s.lstrip("> "))}</div>')
            i += 1
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("```", "- ", "* ", ">")) \
                and not NUMBERED.match(lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append(copy_box("\n".join(para), "Prompt · copy karo") if prompts else f"<p>{inline(' '.join(para))}</p>")
    return "".join(out)


def split_title(t):
    if ":" in t:
        a, b = t.split(":", 1)
        return a.strip() + ":", b.strip()
    w = t.split()
    return (" ".join(w[:-2]), " ".join(w[-2:])) if len(w) > 3 else ("", t)


def parse(md, fallback_title):
    m = re.search(r"^#\s+(.+)$", md, re.M)
    title = m.group(1).strip() if m else fallback_title
    rest = md[m.end():] if m else md
    parts = re.split(r"^##\s+(.+)$", rest, flags=re.M)
    lead = parts[0].strip()
    intro, _, lead_rest = lead.partition("\n\n")
    sections = []
    if lead_rest.strip():
        sections.append(("Start here", "Before you begin", blocks_html(lead_rest)))
    for k in range(1, len(parts), 2):
        h2 = parts[k].strip()
        words = re.sub(r"[^\w\s]", " ", h2).split()
        tag = " ".join(words[:3])[:22] if words else f"Part {k // 2 + 1}"
        sections.append((tag, h2, blocks_html(parts[k + 1], prompts=h2.lower().startswith("prompt"))))
    if not sections:
        sections = [("Guide", title, blocks_html(rest))]
    return title, intro.replace("\n", " ").strip(), sections


def product_promo(page, username):
    """The creator's featured (else first) product from the link page: a card for the middle and a bar for the top."""
    items = [it for it in (page or {}).get("items", []) if it.get("enabled", True) and it.get("type") == "product"]
    it = next((x for x in items if x.get("featured")), items[0] if items else None)
    if not it:
        return "", ""
    price = (it.get("price") or "").strip()
    price = ("₹" + price) if price[:1].isdigit() else price
    href = f"/{e(username)}/go/{e(it['id'])}"
    card = ('<section class="cpromo" style="background:#0C0B10;color:#fff;border:0">'
            '<span class="stag" style="color:#B9A8FF;background:rgba(185,168,255,.18)">🛍 From the creator</span>'
            f'<h2 style="margin:10px 0 6px;color:#fff">{e(it["title"])}</h2>'
            + (f'<p style="margin:0;color:rgba(255,255,255,.78);font-weight:600;line-height:1.5">{e(it.get("subtitle") or "")}</p>' if it.get("subtitle") else "")
            + f'<a href="{href}" style="display:inline-block;margin-top:12px;background:linear-gradient(120deg,#7B5CFF 0%,#B05CE8 55%,#FF7A59 100%);color:#fff;text-decoration:none;'
            f'font-weight:900;border-radius:30px;padding:11px 18px">{e(price) + " · " if price else ""}Get it →</a></section>')
    bar = ('<div class="cbn" id="cbn"><style>'
           '.cbn{position:relative;z-index:50;margin:12px auto 0;max-width:640px;width:calc(100% - 32px);box-sizing:border-box;display:flex;align-items:center;gap:12px;'
           'background:#0C0B10;color:#fff;border-radius:18px;padding:10px 12px 10px 16px;font:700 13.5px/1.35 Inter,system-ui,sans-serif;box-shadow:0 12px 28px rgba(40,30,80,.2)}'
           '.cbn a.cbn-go{margin-left:auto;flex:none;background:linear-gradient(120deg,#7B5CFF 0%,#B05CE8 55%,#FF7A59 100%);color:#fff;text-decoration:none;font-weight:900;border-radius:30px;padding:8px 14px;white-space:nowrap}'
           '.cbn b{color:#B9A8FF}.cbn button{flex:none;background:none;border:0;color:#bbb;font-size:18px;line-height:1;cursor:pointer;padding:2px 4px}'
           '@media (max-width:420px){.cbn{font-size:12.5px}.cbn a.cbn-go{padding:7px 11px}}</style>'
           f'<span>✨ <b>New:</b> {e(it["title"])}</span><a class="cbn-go" href="{href}">{e(price) + " · " if price else ""}See it →</a>'
           '<button type="button" aria-label="Hide" onclick="try{sessionStorage.setItem(\'cbn\',\'1\')}catch(e){}this.parentNode.remove()">×</button>'
           '<script>try{if(sessionStorage.getItem("cbn"))document.getElementById("cbn").remove()}catch(e){}</script></div>')
    return card, bar


THEMES = ("studio", "sunset", "midnight", "ocean", "candy", "mono")


def render(text, filename, acc, page, raw_url, brand="ReplyInbox"):
    """A text file → full guide page HTML."""
    username = acc.get("username", "")
    md = text_to_md(text)
    base = re.sub(r"[-_]+", " ", filename.rsplit(".", 1)[0]).strip()
    title, intro, sections = parse(md, base or "Guide")
    t1, t2 = split_title(title)
    theme = (page or {}).get("theme")
    theme = {"violet": "studio", "mint": "ocean"}.get(theme, theme)
    theme = theme if theme in THEMES else "studio"
    card, bar = product_promo(page, username)
    secs = [f'<section id="s{i}"><span class="stag">{e(tag)}</span><h2>{inline(h)}</h2>{body}</section>'
            for i, (tag, h, body) in enumerate(sections)]
    if card:
        secs.insert(max(1, (len(secs) + 1) // 2), card)
    nav = "".join(f'<a href="#s{i}">{e(tag)}</a>' for i, (tag, _, _) in enumerate(sections))
    avatar = f'<img src="/avatar/{e(acc["id"])}" alt="" onerror="this.remove()">' if acc.get("pic") else ""
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} | @{e(username)}</title><meta name="description" content="{e(intro[:150])}"><meta name="robots" content="noindex">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@500;700;800;900&family=JetBrains+Mono:wght@500;700&family=Noto+Sans+Devanagari:wght@700;800&display=swap" rel="stylesheet">
<style>
:root{{--bg:#F7F5F0;--ink:#0C0B10;--rose:#6A4CFF;--cer:#FF7A59;--mute:#66636F;--line:#E7E3DA;--sh:0 18px 40px rgba(40,30,80,.12)}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);background-attachment:fixed;color:var(--ink);font:500 15.5px/1.6 Inter,'Noto Sans Devanagari',system-ui,sans-serif}}
main{{max-width:640px;margin:0 auto;padding:20px 16px 60px}}a{{color:var(--rose)}}
.top{{display:flex;align-items:center;gap:10px;flex-wrap:wrap}}.top img{{width:44px;height:44px;border-radius:50%;border:3px solid #fff;box-shadow:var(--sh);object-fit:cover}}
.pill{{font:800 11px Inter;color:#fff;background:var(--rose);border-radius:20px;padding:3px 10px;text-decoration:none}}
h1{{font-size:36px;line-height:1.05;letter-spacing:-1px;margin:14px 0 8px;font-weight:900}}h1 span{{color:var(--rose)}}
.intro{{color:#4A4757;font-weight:600}}.back{{font-weight:800;text-decoration:none;font-size:14px}}
.nav{{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}}.nav a{{text-decoration:none;color:var(--ink);background:#fff;border:2px solid var(--line);border-radius:20px;padding:4px 11px;font:800 12px Inter}}
section{{background:#fff;border-radius:22px;padding:20px;margin:16px 0;box-shadow:var(--sh)}}
.stag{{display:inline-block;font:800 11px Inter;letter-spacing:1px;text-transform:uppercase;color:var(--cer);background:rgba(255,122,89,.1);border-radius:20px;padding:3px 10px}}
h2{{font-size:23px;line-height:1.2;margin:8px 0 10px;font-weight:900}}
code{{font:500 .9em 'JetBrains Mono',monospace;background:#F6F2EC;border-radius:6px;padding:1px 6px}}
.code{{position:relative;background:#0C0B10;border-radius:14px;padding:12px 14px;margin:12px 0}}.code pre{{margin:6px 0 0;color:#F3EDE3;font:500 13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap;word-break:break-word}}
.code .lbl{{font:800 10px Inter;letter-spacing:1px;text-transform:uppercase;color:#B5A893}}.cp{{position:absolute;right:10px;top:10px;border:0;background:var(--rose);color:#fff;font:800 11px Inter;border-radius:8px;padding:4px 10px;cursor:pointer}}
.prompt{{background:#F4F1FF;border:2px solid #DDD5FF}}.prompt pre{{color:var(--ink);padding-right:56px}}.prompt .lbl{{color:var(--rose)}}
.tip{{border-radius:12px;padding:10px 13px;margin:12px 0;font-weight:600;font-size:14px;background:#EAF6FB;border-left:4px solid var(--cer)}}
ol.num{{padding-left:20px}}ol.num li,ul li{{margin:5px 0}}
.end{{text-align:center;background:var(--ink);color:#fff;border-radius:20px;padding:20px;margin-top:20px}}.end a{{display:inline-block;margin-top:10px;background:var(--rose);color:#fff;text-decoration:none;font-weight:900;border-radius:12px;padding:10px 18px}}
.dl{{display:block;text-align:center;font-size:13px;font-weight:700;margin-top:14px;color:var(--mute)}}
.made{{text-align:center;font-size:12px;color:var(--mute);margin-top:18px}}.made a{{color:inherit;font-weight:800}}
</style><link rel="stylesheet" href="/static/guide-theme.css"></head><body class="t-{theme}">{bar}<main>
<a class="back" href="/{e(username)}">← More from @{e(username)}</a>
<div class="top" style="margin-top:12px">{avatar}<b>@{e(username)}</b><span class="pill">free guide</span></div>
<h1>{e(t1)} <span>{e(t2)}</span></h1>{f'<p class="intro">{inline(intro)}</p>' if intro else ""}
<div class="nav">{nav}</div>{"".join(secs)}
<div class="end"><b style="font-size:18px">Found this useful? 🙌</b><br>Follow for more free guides<br><a href="https://www.instagram.com/{e(username)}/" target="_blank" rel="noopener">Follow @{e(username)}</a></div>
<a class="dl" href="{e(raw_url)}" download>Download the text file</a>
<p class="made">Made with <a href="/">{e(brand)}</a></p>
</main><script>function cp(b){{const t=b.parentElement.querySelector('pre').innerText;navigator.clipboard.writeText(t).then(()=>{{b.textContent='copied ✓';setTimeout(()=>b.textContent='copy',1500)}})}}</script></body></html>'''
