"""Comic, neo-brutalist Instagram carousels (8 slides, 1080x1350) for @replyinbox, @aiwith.om and @decodingwithom.

A carousel is a small JSON spec written in Hinglish (see content/comic/replyinbox/ai-dm-agent-examples.json):
  {"page": "replyinbox", "slug": "...", "keyword": "EXAMPLES", "hashtags": [...], "slides": [
     {"headline": "500 DMs… [REPLY] KAUN KAREGA?",      # [word] = highlighter block, 2 lines max
      "label": "THE TOOL I USE",                        # small tag on the card (optional)
      "lines": ["Routine sawaal **AI** handle karta hai"],   # **word** = coloured key word
      "steps": ["...", "..."],                          # numbered circles (instead of lines)
      "chat": [["Fan", "bhai kitne ka hai?"], ["AI", "Sirf ₹149"]],
      "bubble": "INBOX PHAT GAYA 😵",                    # character's speech bubble
      "mood": ["stressed", "problem"],                 # used to pick a pose; or "pose": "stressed-phone"
      "bg": "sunburst"}, ...]}                           # grid | sunburst | dots | solid (default: rotates)
The last slide should be the CTA ("COMMENT [KEYWORD]").

Characters: content/characters/<page>/ holds Om's PNGs (transparent background) and characters.json:
  {"stressed-phone": {"file": "stressed-phone.png", "emotion": "worried", "tags": ["overload", "problem"]}, ...}
Each slide gets the pose whose tags/emotion best match its "mood", never repeating within a carousel while unused poses
remain; "pose" on a slide overrides. The white + page-colour sticker outline is added here (SVG filter), so the PNGs
don't need one. Without a characters folder, the code-drawn placeholder in tools/character is used.

Run (from saas/):
  python3 tools/comic.py content/comic/replyinbox/ai-dm-agent-examples.json    # → content/comic/replyinbox/<slug>/
  python3 tools/comic.py --check replyinbox     # cut out white backgrounds (originals kept in originals/), trim, check
                                                # size, update characters.json, write contact-sheet.png to review
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SAAS = os.path.dirname(HERE)
sys.path.insert(0, HERE)

MAX_WORDS = 25
SLIDES = 8

PAGES = {
    "aiwithom": dict(handle="@AIWITH.OM", accent="#C6F432", key="#1A9E4B", hl="#C6F432", hl_ink="#111", sticker="#1A9E4B",
                     tint="#EAF8C8", tint2="#D8F3E2", outfit="black"),
    "decodingwithom": dict(handle="@DECODINGWITHOM", accent="#FFD21F", key="#1F6BFF", hl="#FFD21F", hl_ink="#111", sticker="#1F6BFF",
                           tint="#FFF1B8", tint2="#DCE8FF", outfit="blue"),
    "replyinbox": dict(handle="@REPLYINBOX", accent="#7B5CFF", key="#6A4CFF", hl="#FF7A59", hl_ink="#111", sticker="#7B5CFF",
                       tint="#E7E0FF", tint2="#FFE3D8", outfit="black"),
}
BGS = ("grid", "sunburst", "dots", "solid")


# ---------- text ----------

def plain(text):
    return re.sub(r"[\[\]*]", "", text or "")


def words(text):
    return len(re.findall(r"[\w₹$@%][\w'’.,/%₹$@+-]*", plain(text)))


def slide_words(s):
    parts = [s.get("headline", ""), s.get("label", ""), s.get("bubble", "")] + s.get("lines", []) + s.get("steps", [])
    parts += [f"{a} {b}" for a, b in s.get("chat", [])]
    return sum(words(p) for p in parts)


def rich(text, key):
    t = html.escape(text, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", rf'<b style="color:{key}">\1</b>', t)


def headline_html(text):
    t = html.escape(text, quote=False)
    return re.sub(r"\[(.+?)\]", r'<mark>\1</mark>', t)


# ---------- characters ----------

def char_dir(page):
    return os.path.join(SAAS, "content", "characters", page)


def load_index(page):
    """{pose: {"src": file path or "svg:<pose>", "emotion", "tags"}}: Om's PNGs if present, else the placeholder."""
    path = os.path.join(char_dir(page), "characters.json")
    if os.path.exists(path):
        idx = json.load(open(path))
        return {k: dict(v, src=os.path.join(char_dir(page), v["file"])) for k, v in idx.items()}
    import character
    tags = {"stressed": ["stressed", "problem", "overload", "worried", "hook"], "pointing": ["tool", "laptop", "smug", "show", "how"],
            "chilling": ["relax", "automatic", "cool", "result", "easy"], "thinking": ["question", "think", "doubt", "why", "choose"],
            "celebrating": ["win", "result", "cta", "happy", "done"], "presenting": ["explain", "steps", "answer", "tip", "control"]}
    return {p: {"src": "svg:" + p, "emotion": character.POSES[p]["expression"], "tags": tags.get(p, [])} for p in character.POSES}


def pick_poses(slides, index):
    used, out = {}, []
    for k, s in enumerate(slides):
        if s.get("pose"):
            if s["pose"] not in index:
                sys.exit(f"Slide {k + 1}: unknown pose {s['pose']!r}; have {sorted(index)}")
            choice = s["pose"]
        else:
            mood = set(m.lower() for m in s.get("mood", []))
            def score(p):
                v = index[p]
                hit = len(mood & set(t.lower() for t in v.get("tags", []))) + (2 if v.get("emotion", "").lower() in mood else 0)
                return (-used.get(p, 0), hit, -list(index).index(p))   # unused first, then best match
            choice = max(index, key=score)
        used[choice] = used.get(choice, 0) + 1
        out.append(choice)
    return out


def character_svg(src, sticker, outfit, uid):
    if src.startswith("svg:"):
        import character
        return character.svg(src[4:], outfit=outfit, sticker=sticker, uid=uid)
    flt = (f'<filter id="{uid}" x="-10%" y="-10%" width="120%" height="120%">'
           f'<feMorphology in="SourceAlpha" operator="dilate" radius="16" result="o2"/><feFlood flood-color="{sticker}"/>'
           f'<feComposite in2="o2" operator="in" result="c"/><feMorphology in="SourceAlpha" operator="dilate" radius="8" result="o1"/>'
           f'<feFlood flood-color="#fff"/><feComposite in2="o1" operator="in" result="w"/>'
           f'<feMerge><feMergeNode in="c"/><feMergeNode in="w"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 640"><defs>{flt}</defs>'
            f'<image href="file://{html.escape(os.path.abspath(src))}" x="20" y="20" width="480" height="620" '
            f'preserveAspectRatio="xMidYMax meet" filter="url(#{uid})"/></svg>')


def cutout(path, tol=28):
    """Removes a plain light background connected to the image edges (white eyes/teeth inside the figure stay), trims to
    the figure and saves a transparent PNG in place. The original is kept in originals/."""
    from collections import deque
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()
    bg = px[0, 0][:3]
    close = lambda c: max(abs(c[0] - bg[0]), abs(c[1] - bg[1]), abs(c[2] - bg[2])) <= tol
    seen = bytearray(w * h)
    q = deque((x, y) for x in range(w) for y in (0, h - 1)) + deque((x, y) for y in range(h) for x in (0, w - 1))
    while q:
        x, y = q.popleft()
        i = y * w + x
        if seen[i] or not close(px[x, y]):
            continue
        seen[i] = 1
        px[x, y] = (0, 0, 0, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                q.append((nx, ny))
    box = im.getchannel("A").getbbox()
    orig = os.path.join(os.path.dirname(path), "originals")
    os.makedirs(orig, exist_ok=True)
    os.replace(path, os.path.join(orig, os.path.basename(path)))
    (im.crop(box) if box else im).save(os.path.splitext(path)[0] + ".png")


def contact_sheet(page, out):
    """All cut-outs of a page on a grey checker background, with their pose names."""
    d = char_dir(page)
    files = sorted(f for f in os.listdir(d) if f.lower().endswith(".png") and f != "contact-sheet.png")
    cells = "".join(f'<figure><img src="file://{html.escape(os.path.join(d, f))}"><figcaption>{html.escape(f[:-4])}</figcaption></figure>' for f in files)
    doc = ('<!doctype html><body style="margin:0;padding:20px;width:1600px;font:600 20px sans-serif;display:flex;flex-wrap:wrap;gap:14px;'
           'background:repeating-conic-gradient(#ddd 0 25%,#f6f6f6 0 50%) 0 0/24px 24px">'
           '<style>figure{margin:0;width:240px;text-align:center}img{width:240px;height:300px;object-fit:contain}</style>' + cells + "</body>")
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "s.html"), "w").write(doc)
        js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1640,height:800}});"
              f"await p.goto('file://{tmp}/s.html');await p.screenshot({{path:'{os.path.abspath(out)}',fullPage:true}});await b.close();}})()")
        subprocess.run(["node", "-e", js], check=True, cwd=tmp, env={**os.environ, "NODE_PATH": __import__("carousels").node_path()})


def check(page):
    """Checks Om's character PNGs: transparent background, ≥1000px tall. Writes a starter characters.json for new files."""
    from PIL import Image
    d = char_dir(page)
    if not os.path.isdir(d):
        sys.exit(f"No folder {os.path.relpath(d, SAAS)}: put the PNGs there first.")
    idx_path = os.path.join(d, "characters.json")
    idx = json.load(open(idx_path)) if os.path.exists(idx_path) else {}
    problems, sizes = [], []
    for f in sorted(os.listdir(d)):             # white/solid backgrounds (PNG or JPG) are cut out first
        path = os.path.join(d, f)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) and os.path.isfile(path):
            im = Image.open(path)
            if "A" not in im.convert("RGBA").getbands() or im.convert("RGBA").getchannel("A").getextrema()[0] == 255:
                cutout(path)
                print("cut out background:", f)
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith(".png") or f == "contact-sheet.png":
            continue
        im = Image.open(os.path.join(d, f))
        sizes.append((f, im.size))
        if im.mode not in ("RGBA", "LA", "P") or "A" not in im.getbands() and "transparency" not in im.info:
            problems.append(f"{f}: no transparency (background must be transparent)")
        else:
            a = im.convert("RGBA").getchannel("A")
            w, h = im.size
            corners = [a.getpixel(p) for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
            if max(corners[:2]) > 10:
                problems.append(f"{f}: top corners aren't transparent (background left in?)")
        if im.size[1] < 1000:
            problems.append(f"{f}: only {im.size[1]}px tall (need ≥1000)")
        name = os.path.splitext(f)[0]
        idx.setdefault(name, {"file": f, "emotion": "", "tags": [t for t in re.split(r"[-_ ]", name) if t]})
    json.dump(idx, open(idx_path, "w"), ensure_ascii=False, indent=2)
    print(f"{len(sizes)} PNG(s); index: {os.path.relpath(idx_path, SAAS)}")
    print("\n".join(problems) or "All files pass (transparent, tall enough). Check by eye that it's the same character.")
    sheet = os.path.join(d, "contact-sheet.png")
    contact_sheet(page, sheet)
    print("contact sheet:", os.path.relpath(sheet, SAAS))


# ---------- slide HTML ----------

FONTS = ('<link href="https://fonts.googleapis.com/css2?family=Anton&family=Poppins:wght@500;600;700;800'
         '&display=block" rel="stylesheet">')


def css(t):
    return f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:1080px;height:1350px;overflow:hidden}}
body{{font-family:Poppins,Montserrat,sans-serif;color:#111;-webkit-font-smoothing:antialiased}}
.s{{position:relative;width:1080px;height:1350px;overflow:hidden}}
.bg-grid{{background:#F6F2E7;background-image:linear-gradient(rgba(17,17,17,.07) 2px,transparent 2px),linear-gradient(90deg,rgba(17,17,17,.07) 2px,transparent 2px);background-size:54px 54px}}
.bg-sunburst{{background:repeating-conic-gradient(from 0deg at 50% 78%,{t['tint']} 0 7.5deg,#FFFDF6 7.5deg 15deg)}}
.bg-dots{{background:{t['tint2']};background-image:radial-gradient(rgba(17,17,17,.16) 4px,transparent 4.5px);background-size:44px 44px}}
.bg-solid{{background:{t['accent']}}}
.pill{{position:absolute;top:52px;left:52px;display:flex;align-items:center;gap:14px;background:#111;color:#fff;border-radius:99px;padding:14px 28px 14px 22px;font:800 36px Poppins;letter-spacing:.04em}}
.pill i{{width:24px;height:24px;border-radius:50%;background:{t['accent']};border:3px solid #fff}}
.count{{position:absolute;top:44px;right:52px;background:{t['accent']};color:{'#fff' if t['accent'] in ('#7B5CFF',) else '#111'};border:6px solid #111;border-radius:22px;box-shadow:8px 8px 0 #111;padding:6px 22px;font:400 48px Anton}}
.swipe{{position:absolute;right:48px;bottom:48px;z-index:5;background:#111;color:#fff;border-radius:99px;padding:14px 30px;font:400 40px Anton;letter-spacing:.06em}}
.swipe b{{color:{t['accent']};font-weight:400}}
h1{{position:absolute;left:52px;right:52px;top:150px;font:400 128px/1.0 Anton,'Bebas Neue',Impact,sans-serif;text-transform:uppercase;letter-spacing:.005em}}
.bg-solid h1{{color:#111}}
mark{{background:{t['hl']};color:{t['hl_ink']};padding:0 14px;border:6px solid #111;border-radius:14px;box-shadow:7px 7px 0 #111;display:inline-block;line-height:1.02;transform:rotate(-1.5deg)}}
.card{{position:absolute;left:52px;right:52px;background:#fff;border:6px solid #111;border-radius:32px;box-shadow:14px 14px 0 #111;padding:40px 44px 36px;font:600 46px/1.3 Poppins}}
.tag{{position:absolute;top:-30px;left:36px;background:{t['accent']};color:{'#fff' if t['accent'] in ('#7B5CFF',) else '#111'};border:5px solid #111;border-radius:12px;padding:2px 18px;font:400 38px Anton;letter-spacing:.05em;text-transform:uppercase}}
.card p+p{{margin-top:14px}}
.steps{{list-style:none;display:flex;flex-direction:column;gap:20px}}
.steps li{{display:flex;gap:22px;align-items:flex-start}}
.steps .n{{flex:none;width:68px;height:68px;border-radius:50%;background:{t['accent']};color:{'#fff' if t['accent'] in ('#7B5CFF',) else '#111'};border:5px solid #111;display:flex;align-items:center;justify-content:center;font:400 40px Anton}}
.chat{{display:flex;flex-direction:column;gap:16px}}
.msg{{max-width:92%;border:5px solid #111;border-radius:26px;padding:14px 24px;font:600 42px/1.28 Poppins}}
.msg small{{display:block;font:400 30px Anton;letter-spacing:.06em;text-transform:uppercase;opacity:.7}}
.msg.in{{align-self:flex-start;background:#F2F0EA;border-bottom-left-radius:8px}}
.msg.out{{align-self:flex-end;background:{t['tint']};border-bottom-right-radius:8px}}
.char{{position:absolute;bottom:-6px;width:560px;height:690px;z-index:2}}
.char svg{{width:100%;height:100%}}
.left .char{{left:-10px}}.right .char{{right:-10px}}
.bubble{{position:absolute;z-index:3;bottom:330px;width:440px;background:#fff;border:6px solid #111;border-radius:30px;box-shadow:10px 10px 0 #111;padding:22px 28px;font:italic 400 54px/1.04 Anton,'Bebas Neue',Impact,sans-serif;text-transform:uppercase;transform:skew(-4deg)}}
.left .bubble{{left:560px}}.right .bubble{{right:560px}}
.bubble:after{{content:"";position:absolute;bottom:22px;width:0;height:0;border-top:22px solid transparent;border-bottom:22px solid transparent}}
.left .bubble:after{{left:-40px;border-right:36px solid #111}}
.right .bubble:after{{right:-40px;border-left:36px solid #111}}
"""


def slide_html(s, i, n, t, char):
    side = "left" if i % 2 else "right"
    bg = s.get("bg") or BGS[(i - 1) % len(BGS)]
    if s.get("steps"):
        body = '<ol class="steps">' + "".join(f'<li><span class="n">{k}</span><span>{rich(x, t["key"])}</span></li>'
                                              for k, x in enumerate(s["steps"], 1)) + "</ol>"
    elif s.get("chat"):
        body = '<div class="chat">' + "".join(
            f'<div class="msg {"in" if k % 2 == 0 else "out"}"><small>{html.escape(who)}</small>{rich(x, t["key"])}</div>'
            for k, (who, x) in enumerate(s["chat"])) + "</div>"
    else:
        body = "".join(f"<p>{rich(x, t['key'])}</p>" for x in s.get("lines", []))
    tag = f'<span class="tag">{html.escape(s["label"])}</span>' if s.get("label") else ""
    card = f'<div class="card">{tag}{body}</div>' if body else ""
    bubble = f'<div class="bubble">{html.escape(s["bubble"])}</div>' if s.get("bubble") else ""
    swipe = '<div class="swipe">SWIPE <b>→</b></div>' if i < n else ""
    return (f'<!doctype html><html><head><meta charset="utf-8">{FONTS}<style>{css(t)}</style></head><body>'
            f'<div class="s bg-{bg} {side}"><div class="pill"><i></i>{t["handle"]}</div><div class="count">{i}/{n}</div>'
            f'<h1>{headline_html(s["headline"])}</h1>{card}<div class="char">{char}</div>{bubble}{swipe}</div></body></html>')


# Lays out the card under the headline, then shrinks headline/card text until it all sits above the character's head.
FIT_JS = r"""
() => {
  const h1 = document.querySelector('h1'), card = document.querySelector('.card'), bub = document.querySelector('.bubble');
  const limit = 1350 - 520;                                   // character + bubble zone starts here
  const place = () => { if (card) card.style.top = (h1.offsetTop + h1.offsetHeight + 44) + 'px'; };
  const bottom = () => card ? card.offsetTop + card.offsetHeight : h1.offsetTop + h1.offsetHeight;
  const lines = () => Math.round(h1.offsetHeight / parseFloat(getComputedStyle(h1).lineHeight || 128));
  place();
  for (let k = 0; k < 120; k++) {
    const hs = parseFloat(getComputedStyle(h1).fontSize);
    if (h1.scrollWidth > h1.clientWidth + 2 || h1.offsetHeight > hs * 2.25) { if (hs > 84) { h1.style.fontSize = (hs - 3) + 'px'; place(); continue; } }
    if (bottom() > limit && card) {
      const cs = parseFloat(getComputedStyle(card).fontSize);
      if (cs > 36) { card.style.fontSize = (cs - 2) + 'px'; card.querySelectorAll('.msg').forEach(m => m.style.fontSize = (cs - 4) + 'px'); place(); continue; }
      if (hs > 84) { h1.style.fontSize = (hs - 3) + 'px'; place(); continue; }
    }
    break;
  }
  // the character fills the space under the card (never over it), at least 470px tall
  const ch = document.querySelector('.char');
  const room = Math.max(470, Math.min(690, 1350 - bottom() + 40));
  ch.style.height = room + 'px'; ch.style.width = Math.round(room * 560 / 690) + 'px';
  const side = document.querySelector('.s').classList.contains('left') ? 'left' : 'right';
  if (bub) { bub.style[side] = (ch.offsetWidth + 10) + 'px'; bub.style.bottom = Math.min(room * 0.48, 1350 - bottom() - 40 - bub.offsetHeight) + 'px'; }
  return bottom() > 1350 - 470 + 40;
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
    from carousels import node_path
    with tempfile.TemporaryDirectory() as tmp:
        spec = []
        for k, (doc, png) in enumerate(jobs):
            p = os.path.join(tmp, f"{k}.html")
            open(p, "w").write(doc)
            spec.append({"html": p, "png": os.path.abspath(png)})
        for name, text in (("jobs.json", json.dumps(spec)), ("fit.js", FIT_JS), ("render.js", RENDER_JS)):
            open(os.path.join(tmp, name), "w").write(text)
        out = subprocess.run(["node", "render.js", "jobs.json", "fit.js"], capture_output=True, text=True, cwd=tmp,
                             env={**os.environ, "NODE_PATH": node_path()})
        if out.returncode:
            sys.exit("Rendering failed:\n" + out.stderr[-2000:])
        m = re.search(r"OVERFLOW (\[.*\])", out.stdout)
        return json.loads(m.group(1)) if m else []


# ---------- spec → files ----------

def validate(spec):
    errs = []
    if spec.get("page") not in PAGES:
        errs.append(f"page must be one of {sorted(PAGES)}")
    if len(spec.get("slides", [])) != SLIDES:
        errs.append(f"need exactly {SLIDES} slides, got {len(spec.get('slides', []))}")
    for k, s in enumerate(spec.get("slides", []), 1):
        if not s.get("headline"):
            errs.append(f"slide {k}: headline missing")
        if slide_words(s) > MAX_WORDS:
            errs.append(f"slide {k}: {slide_words(s)} words (max {MAX_WORDS})")
    if spec.get("keyword") and spec["keyword"].upper() not in plain(spec["slides"][-1]["headline"]).upper():
        errs.append("last slide's headline should say the comment keyword")
    return errs


def caption(spec):
    s = spec["slides"]
    hook = plain(s[0]["headline"]).strip()
    value = []
    for sl in s[1:-1]:
        for x in sl.get("lines", []) + sl.get("steps", []):
            if plain(x) not in value:
                value.append(plain(x))
    tags = spec.get("hashtags") or ["#instagramtips", "#creatortips", "#aitools", "#instagramautomation", "#dmautomation"]
    cta = spec.get("cta_caption") or f"Comment {spec['keyword']} aur main full guide DM kar dunga 📩"
    return "\n".join([hook, ""] + ["→ " + v for v in value[:5]] + ["", cta, "", " ".join(tags[:8])]) + "\n"


def build(spec_path, out_dir=None):
    spec = json.load(open(spec_path))
    errs = validate(spec)
    if errs:
        sys.exit("Spec problems:\n  " + "\n  ".join(errs))
    t = PAGES[spec["page"]]
    index = load_index(spec["page"])
    poses = pick_poses(spec["slides"], index)
    out = out_dir or os.path.join(SAAS, "content", "comic", spec["page"], spec["slug"])
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if re.match(r"^\d\d\.png$", f):
            os.remove(os.path.join(out, f))
    jobs = []
    for i, (s, pose) in enumerate(zip(spec["slides"], poses), 1):
        char = character_svg(index[pose]["src"], t["sticker"], t["outfit"], f"c{i}")
        jobs.append((slide_html(s, i, SLIDES, t, char), os.path.join(out, f"{i:02d}.png")))
    bad = render(jobs)
    open(os.path.join(out, "caption.txt"), "w").write(caption(spec))
    json.dump({"poses": poses}, open(os.path.join(out, "poses.json"), "w"), indent=2)
    for b in bad:
        print("Warning: text runs into the character on", os.path.relpath(b, SAAS))
    print(f"Wrote {SLIDES} slides to {os.path.relpath(out, os.getcwd())} (poses: {', '.join(poses)})")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("specs", nargs="*")
    ap.add_argument("--check", metavar="PAGE", help="check content/characters/PAGE/*.png and update characters.json")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    if a.check:
        return check(a.check)
    for p in a.specs:
        build(p, a.out)


if __name__ == "__main__":
    main()
