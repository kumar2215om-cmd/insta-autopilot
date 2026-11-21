"""Instagram stories (1080x1920) in the comic style and a page's brand, with Om's character.

Text stays inside the safe zone (y 260–1620): Instagram puts its own bars and buttons in the top ~250px and the
bottom ~300px. A story is a JSON spec like content/stories/replyinbox/promo-2026-11.json:
  {"page": "replyinbox", "slug": "promo-2026-11", "frames": [
     {"headline": "...[WORD]...", "label": "...", "lines": [...] | "steps": [...] | "rows": [[a, b], ...],
      "bubble": "...", "role": "hook", "bg": "sunburst"}, ...]}
Run (from saas/): python3 tools/story.py content/stories/replyinbox/promo-2026-11.json
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import comic  # noqa: E402

W, H, TOP, BOTTOM = 1080, 1920, 260, 1620

STORY_CSS = """
html,body{height:1920px}.s{height:1920px}
.pill{top:270px}
h1{position:static;margin:0;font-size:132px}
.wrap{position:absolute;left:56px;right:56px;top:360px;display:flex;flex-direction:column;gap:56px}
.card{position:relative;left:auto;right:auto;font-size:48px}
.rows{display:flex;flex-direction:column;gap:14px}
.row{display:flex;justify-content:space-between;gap:20px;align-items:baseline;border-bottom:3px dashed rgba(17,19,24,.18);padding-bottom:12px}
.row:last-child{border-bottom:0;padding-bottom:0}
.row b{font-family:'JetBrains Mono',monospace;font-weight:700;white-space:nowrap}
.char{width:600px;height:740px;bottom:0}
.bubble{bottom:auto;top:1230px;width:430px}
.left .bubble{left:600px}.right .bubble{right:600px}
.cta-link{display:inline-block;margin-top:8px;background:#D4FF3A;color:#111318;border:6px solid #111318;border-radius:999px;box-shadow:10px 10px 0 #111318;
  padding:16px 40px;font:700 58px 'JetBrains Mono',monospace;letter-spacing:-.01em}
"""

FIT_JS = r"""
() => {
  const wrap = document.querySelector('.wrap'), h1 = document.querySelector('h1'), card = document.querySelector('.card');
  const limit = 1190;                                    // content ends above the character
  for (let k = 0; k < 150; k++) {
    const bottom = wrap.offsetTop + wrap.offsetHeight;
    const hs = parseFloat(getComputedStyle(h1).fontSize);
    if (h1.scrollWidth > h1.clientWidth + 2 && hs > 90) { h1.style.fontSize = (hs - 3) + 'px'; continue; }
    if (bottom <= limit) break;
    const cs = card ? parseFloat(getComputedStyle(card).fontSize) : 0;
    if (card && cs > 38) { card.style.fontSize = (cs - 2) + 'px'; continue; }
    if (hs > 90) { h1.style.fontSize = (hs - 3) + 'px'; continue; }
    break;
  }
  return wrap.offsetTop + wrap.offsetHeight > limit + 20;
}
"""


def frame_html(f, i, t, char):
    side = comic.side_of(i)
    bg = f.get("bg") or comic.BGS[(i - 1) % len(comic.BGS)]
    key = t["key"]
    if f.get("steps"):
        body = '<ol class="steps">' + "".join(f'<li><span class="n">{k}</span><span>{comic.rich(x, key)}</span></li>'
                                              for k, x in enumerate(f["steps"], 1)) + "</ol>"
    elif f.get("rows"):
        body = '<div class="rows">' + "".join(f'<div class="row"><span>{comic.rich(a, key)}</span><b>{comic.rich(b, key)}</b></div>'
                                              for a, b in f["rows"]) + "</div>"
    else:
        body = "".join(f"<p>{comic.rich(x, key)}</p>" for x in f.get("lines", []))
    if f.get("link"):
        body += f'<div><span class="cta-link">{html.escape(f["link"])}</span></div>'
    tag = f'<span class="tag">{html.escape(f["label"])}</span>' if f.get("label") else ""
    card = f'<div class="card">{tag}{body}</div>' if body else ""
    bubble = f'<div class="bubble">{html.escape(f["bubble"])}</div>' if f.get("bubble") else ""
    look = comic.look(t)
    return (f'<!doctype html><html><head><meta charset="utf-8">{look["fonts"]}<style>{comic.css(t)}{STORY_CSS}</style></head><body>'
            f'<div class="s bg-{bg} {side}"><div class="pill"><i></i>{t["handle"]}</div>'
            f'<div class="wrap"><h1>{comic.headline_html(f["headline"])}</h1>{card}</div>'
            f'<div class="char">{char}</div>{bubble}</div></body></html>')


def build(spec_path, out_dir=None):
    spec = json.load(open(spec_path))
    t = comic.PAGES[spec["page"]]
    frames = spec["frames"]
    for k, f in enumerate(frames, 1):
        if comic.slide_words(f) + sum(len(re.findall(r"\w+", a + " " + b)) for a, b in f.get("rows", [])) > 32:
            sys.exit(f"Frame {k} has too many words for a story")
    index = comic.load_index(spec["page"])
    poses = comic.pick_poses(frames, index, comic.load_roles(spec["page"]), seed=spec["slug"])
    out = out_dir or os.path.join(comic.SAAS, "content", "stories", spec["page"], spec["slug"])
    os.makedirs(out, exist_ok=True)
    jobs = []
    for i, (f, pose) in enumerate(zip(frames, poses), 1):
        char = comic.character_svg(index[pose]["src"], t["sticker"], t["outfit"], f"c{i}")
        jobs.append((frame_html(f, i, t, char), os.path.join(out, f"{i:02d}.png")))
    old = comic.FIT_JS
    comic.FIT_JS = FIT_JS
    try:
        bad = render(jobs)
    finally:
        comic.FIT_JS = old
    for b in bad:
        print("Warning: text runs into the character on", os.path.relpath(b, comic.SAAS))
    print(f"Wrote {len(frames)} story frames to {os.path.relpath(out, os.getcwd())} (poses: {', '.join(poses)})")
    return out


def render(jobs):
    js = comic.RENDER_JS.replace("width: 1080, height: 1350", f"width: {W}, height: {H}")
    old = comic.RENDER_JS
    comic.RENDER_JS = js
    try:
        return comic.render(jobs)
    finally:
        comic.RENDER_JS = old


if __name__ == "__main__":
    for p in sys.argv[1:]:
        build(p)
