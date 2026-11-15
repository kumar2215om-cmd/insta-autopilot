"""Character sheet: all poses, expressions and outfits on one PNG.  Run: python3 tools/character/sheet.py OUT.png"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from character import EXPRESSIONS, POSES, bubble_html, svg  # noqa: E402

FONTS = '<link href="https://fonts.googleapis.com/css2?family=Anton&family=Poppins:wght@600;800&display=block" rel="stylesheet">'


def html():
    cell = lambda inner, label: (f'<div class="c">{inner}<div class="l">{label}</div></div>')
    poses = "".join(cell(svg(p, size=330, uid=f"p{i}"), p) for i, p in enumerate(POSES))
    faces = "".join(cell(svg("presenting", e, size=210, uid=f"e{i}", head_only=True), e) for i, e in enumerate(EXPRESSIONS))
    outfits = (cell(svg("pointing", outfit="black", sticker="#1A9E4B", size=300, uid="o1"), "@aiwith.om · black tee")
               + cell(svg("pointing", outfit="blue", sticker="#1F6BFF", size=300, uid="o2"), "@decodingwithom · blue shirt")
               + cell(svg("presenting", outfit="black", sticker="#7B5CFF", size=300, uid="o3"), "@replyinbox · violet sticker"))
    bubble = cell('<div style="padding:30px 0 50px">' + bubble_html("REPLY KAUN KAREGA? 😩") + "</div>", "speech bubble")
    return (f'<!doctype html><html><head><meta charset="utf-8">{FONTS}<style>'
            'body{margin:0;width:1600px;background:#F4F1E8;background-image:linear-gradient(#e2ddd0 1px,transparent 1px),linear-gradient(90deg,#e2ddd0 1px,transparent 1px);background-size:40px 40px;font-family:Poppins,sans-serif;padding:40px;box-sizing:border-box}'
            'h1{font:400 84px Anton,sans-serif;margin:0 0 6px;text-transform:uppercase}h1 mark{background:#C6F432;padding:0 12px}'
            'h2{font:400 40px Anton,sans-serif;text-transform:uppercase;margin:34px 0 12px}'
            '.row{display:flex;flex-wrap:wrap;gap:22px;align-items:flex-end}.c{background:#fff;border:5px solid #111;border-radius:22px;box-shadow:8px 8px 0 #111;padding:14px 18px;text-align:center}'
            '.l{font:600 22px Poppins;margin-top:6px;text-transform:uppercase;letter-spacing:.04em}</style></head><body>'
            f'<h1>Om · <mark>character sheet</mark></h1><div style="font:600 24px Poppins">Draft 1, drawn in code. Tell me what to change: face, beard, hair, skin, outfit.</div>'
            f'<h2>Poses</h2><div class="row">{poses}</div><h2>Expressions</h2><div class="row">{faces}</div>'
            f'<h2>Outfits per page + speech bubble</h2><div class="row">{outfits}{bubble}</div></body></html>')


def main(out):
    with tempfile.TemporaryDirectory() as tmp:
        page = os.path.join(tmp, "sheet.html")
        open(page, "w").write(html())
        js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
              "const p=await b.newPage({viewport:{width:1600,height:900},deviceScaleFactor:1});"
              f"await p.goto('file://{page}',{{waitUntil:'networkidle'}}).catch(()=>{{}});await p.evaluate(()=>document.fonts.ready);"
              f"await p.screenshot({{path:'{os.path.abspath(out)}',fullPage:true}});await b.close();}})()")
        subprocess.run(["node", "-e", js], check=True, cwd=tmp)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "character-sheet.png")
