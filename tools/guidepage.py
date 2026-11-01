# Build a cream/rose freebie guide page (HTML) for the aiwith.om link-in-bio site.
import html, re
e = html.escape
def md(t):
    t = e(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    t = re.sub(r'\[(.+?)\]\((https?://[^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r'\[(.+?)\]\(([\w./-]+\.html)\)', r'<a href="\2">\1</a>', t)
    return t
def block(b):
    k = b[0]
    if k == 'p': return f'<p>{md(b[1])}</p>'
    if k == 'code': return f'<div class="code"><button class="cp" onclick="cp(this)">copy</button><div class="lbl">{e(b[1])}</div><pre>{e(b[2])}</pre></div>'
    if k == 'list': return '<ul>' + ''.join(f'<li>{md(x)}</li>' for x in b[1]) + '</ul>'
    if k == 'ol': return '<ol class="num">' + ''.join(f'<li>{md(x)}</li>' for x in b[1]) + '</ol>'
    if k == 'tip': return f'<div class="tip">💡 {md(b[1])}</div>'
    if k == 'warn': return f'<div class="warn">⚠️ {md(b[1])}</div>'
    if k == 'cmds': return '<div class="cmds">' + ''.join(f'<div class="cmd"><code>{e(c)}</code><span>{md(d)}</span></div>' for c, d in b[1]) + '</div>'
    if k == 'table': return '<table><tr>' + ''.join(f'<th>{md(h)}</th>' for h in b[1]) + '</tr>' + ''.join('<tr>' + ''.join(f'<td>{md(c)}</td>' for c in r) + '</tr>' for r in b[2]) + '</table>'
    if k == 'repo': return f'<a class="repo" href="https://github.com/{b[1]}" target="_blank" rel="noopener"><div class="rlogo">⌥</div><div><b>{e(b[2])}</b><div class="rurl">github.com/{e(b[1])}</div><div class="rdesc">{md(b[3])}</div><div class="badges">' + ''.join(f'<span>{e(x)}</span>' for x in b[4]) + '</div></div></a>'
    if k == 'img': return f'<figure><img src="{b[1]}" alt="" loading="lazy"><figcaption>{md(b[2])}</figcaption></figure>'
    if k == 'plugs':
        out = '<div class="plugs">'
        for name, repo, desc, cmd, lic, warns in b[1]:
            w = ''.join(f'<span class="w">⚠ {e(x)}</span>' for x in warns)
            c = f'<div class="code sm"><button class="cp" onclick="cp(this)">copy</button><pre>{e(cmd)}</pre></div>' if cmd else ''
            out += f'<div class="plug"><div class="ph"><b>{e(name)}</b><span class="lic">{e(lic)}</span></div><a class="rurl" href="https://github.com/{repo}" target="_blank" rel="noopener">github.com/{e(repo)}</a><div class="pd">{md(desc)}</div>{c}<div>{w}</div></div>'
        return out + '</div>'
    if k == 'prompt': return f'<div class="code prompt"><button class="cp" onclick="cp(this)">copy</button><div class="lbl">{e(b[1])}</div><pre>{e(b[2])}</pre></div>'
    if k == 'raw': return b[1]  # pre-built HTML (used by md2guide.py)
    raise ValueError(k)
def page(kw, title1, title2, intro, sections, credit=None, updated='Nov 2026'):
    nav = ''.join(f'<a href="#s{i}">{e(s[0])}</a>' for i, s in enumerate(sections))
    secs = ''.join(f'<section id="s{i}"><span class="stag">{e(s[0])}</span><h2>{md(s[1])}</h2>{"".join(block(b) for b in s[2])}</section>' for i, s in enumerate(sections))
    cred = f'<p class="credit">Idea credit: {e(credit)} · Facts checked {updated} from the official source. Tools badalte rehte hain, latest README zaroor dekho.</p>' if credit else ''
    return f'''<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(kw)} · {e(title1)} {e(title2)} | aiwith.om</title><meta name="description" content="{e(intro[:150])}">
<link rel="icon" href="../avatar.png"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@500;700;800;900&family=JetBrains+Mono:wght@500;700&family=Noto+Sans+Devanagari:wght@700;800&display=swap" rel="stylesheet">
<style>
:root{{--bg:#F1EADC;--ink:#1C1A17;--rose:#FF2D95;--cer:#007BA7;--mute:#8C8780;--line:#E7E0D4;--sh:0 18px 40px rgba(60,40,20,.13)}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:500 15.5px/1.6 Inter,'Noto Sans Devanagari',system-ui,sans-serif}}
main{{max-width:640px;margin:0 auto;padding:20px 16px 60px}}a{{color:var(--rose)}}
.top{{display:flex;align-items:center;gap:10px;flex-wrap:wrap}}.top img{{width:44px;height:44px;border-radius:50%;border:3px solid #fff;box-shadow:var(--sh)}}
.pill{{font:800 11px Inter;color:#fff;background:var(--rose);border-radius:20px;padding:3px 10px;text-decoration:none}}.pill.c{{background:var(--cer)}}
h1{{font-size:36px;line-height:1.05;letter-spacing:-1px;margin:14px 0 8px;font-weight:900}}h1 span{{color:var(--rose)}}
.intro{{color:#4A4540;font-weight:600}}.back{{font-weight:800;text-decoration:none;font-size:14px}}
.nav{{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}}.nav a{{text-decoration:none;color:var(--ink);background:#fff;border:2px solid var(--line);border-radius:20px;padding:4px 11px;font:800 12px Inter}}
section{{background:#fff;border-radius:22px;padding:20px;margin:16px 0;box-shadow:var(--sh)}}
.stag{{display:inline-block;font:800 11px Inter;letter-spacing:1px;text-transform:uppercase;color:var(--cer);background:rgba(0,123,167,.09);border-radius:20px;padding:3px 10px}}
h2{{font-size:23px;line-height:1.2;margin:8px 0 10px;font-weight:900}}
code{{font:500 .9em 'JetBrains Mono',monospace;background:#F6F2EC;border-radius:6px;padding:1px 6px}}
.code{{position:relative;background:#1C1A17;border-radius:14px;padding:12px 14px;margin:12px 0}}.code pre{{margin:6px 0 0;color:#F3EDE3;font:500 13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap;word-break:break-word}}
.code .lbl{{font:800 10px Inter;letter-spacing:1px;text-transform:uppercase;color:#B5A893}}.cp{{position:absolute;right:10px;top:10px;border:0;background:var(--rose);color:#fff;font:800 11px Inter;border-radius:8px;padding:4px 10px;cursor:pointer}}
.prompt{{background:#FFF7FB;border:2px solid #FFD0E6}}.prompt pre{{color:var(--ink)}}.prompt .lbl{{color:var(--rose)}}
.tip,.warn{{border-radius:12px;padding:10px 13px;margin:12px 0;font-weight:600;font-size:14px}}.tip{{background:#EAF6FB;border-left:4px solid var(--cer)}}.warn{{background:#FFF0F6;border-left:4px solid var(--rose)}}
.cmds{{display:grid;gap:8px}}.cmd{{display:flex;gap:10px;align-items:flex-start;border:1.5px solid var(--line);border-radius:12px;padding:9px 11px}}.cmd code{{flex:none;font-weight:700;color:var(--rose);background:#FFF0F6}}.cmd span{{font-size:14px}}
table{{width:100%;border-collapse:collapse;font-size:14px}}th{{text-align:left;color:var(--cer);border-bottom:2px solid var(--line);padding:7px}}td{{border-bottom:1px solid #F1ECE3;padding:7px;vertical-align:top}}
.repo{{display:flex;gap:12px;text-decoration:none;color:var(--ink);border:2px solid var(--line);border-radius:16px;padding:13px;margin:10px 0}}.rlogo{{flex:none;width:46px;height:46px;border-radius:12px;background:#1C1A17;color:#fff;display:flex;align-items:center;justify-content:center;font-size:24px}}
.rurl{{font:500 12px 'JetBrains Mono',monospace;color:var(--cer)}}.rdesc{{font-size:13.5px;margin-top:4px}}.badges span{{display:inline-block;margin:6px 6px 0 0;font:800 11px Inter;border:1.5px solid var(--line);border-radius:8px;padding:2px 7px}}
ol.num{{padding-left:20px}}ol.num li,ul li{{margin:5px 0}}
.plugs{{display:grid;gap:10px}}.plug{{border:1.5px solid var(--line);border-radius:14px;padding:11px 13px}}.ph{{display:flex;justify-content:space-between;align-items:center;gap:8px}}.ph b{{font-size:16px}}.lic{{font:800 10px Inter;border:1.5px solid var(--line);border-radius:8px;padding:1px 7px;color:var(--mute);white-space:nowrap}}.pd{{font-size:14px;margin-top:3px}}.code.sm{{padding:8px 12px;margin:8px 0 4px}}.code.sm pre{{margin:0;font-size:12px;padding-right:56px}}.w{{display:inline-block;margin:4px 6px 0 0;font:800 11px Inter;color:#B4235F;background:#FFF0F6;border-radius:8px;padding:2px 8px}}
figure{{margin:12px 0}}figure img{{width:100%;border-radius:14px;display:block}}figcaption{{font-size:12.5px;color:var(--mute);margin-top:6px;text-align:center}}
.credit{{font-size:12.5px;color:var(--mute);text-align:center;margin-top:20px}}
.end{{text-align:center;background:var(--ink);color:#fff;border-radius:20px;padding:20px;margin-top:20px}}.end a{{display:inline-block;margin-top:10px;background:var(--rose);color:#fff;text-decoration:none;font-weight:900;border-radius:12px;padding:10px 18px}}
</style></head><body><main>
<a class="back" href="../index.html">← Saare freebies</a>
<div class="top" style="margin-top:12px"><img src="../avatar.png" alt=""><b>@aiwith.om</b><span class="pill">freebie · comment {e(kw)}</span></div>
<h1>{e(title1)} <span>{e(title2)}</span></h1><p class="intro">{md(intro)}</p>
<div class="nav">{nav}</div>{secs}{cred}
<div class="end"><b style="font-size:18px">Kaam aaya? 🙌</b><br>Aise hi free AI tools &amp; guides ke liye follow karo<br><a href="https://www.instagram.com/aiwith.om/" target="_blank" rel="noopener">Follow @aiwith.om</a></div>
</main><script>function cp(b){{const t=b.parentElement.querySelector('pre').innerText;navigator.clipboard.writeText(t).then(()=>{{b.textContent='copied ✓';setTimeout(()=>b.textContent='copy',1500)}})}}</script></body></html>'''
