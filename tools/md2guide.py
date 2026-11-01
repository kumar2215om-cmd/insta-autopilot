"""Turn a Markdown guide (e.g. a Notion "Export → Markdown") into a /free guide page in the FACTORY style.

    python3 tools/md2guide.py path/to/page.md KEYWORD            # writes freebies/guides/KEYWORD.html
    python3 tools/md2guide.py page.md KEYWORD --update-index      # also points the /free card at the new page

Images next to the .md file are copied to freebies/guides/img/KEYWORD/. Theme + animations are added by the server.
"""
import argparse, html, json, os, re, shutil, sys, urllib.parse
import markdown
sys.path.insert(0, os.path.dirname(__file__))
from guidepage import page

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUIDES = os.path.join(ROOT, "freebies", "guides")

def clean_notion(md):
    # callouts (<aside>…</aside>) → blockquote, shown as a tip box
    md = re.sub(r"<aside>(.*?)</aside>",
                lambda m: "\n\n" + "\n".join("> " + l.strip() for l in m.group(1).strip().splitlines() if l.strip()) + "\n\n",
                md, flags=re.S)
    # a list right after a paragraph needs a blank line before it in Markdown
    md = re.sub(r"(^[^\s>|#\-*\d][^\n]*)\n(\s*(?:[-*+]|\d+\.)\s)", r"\1\n\n\2", md, flags=re.M)
    md = re.sub(r"^(Created|Last edited|Tags|Status|Property)[^\n]*:\s.*$", "", md, flags=re.M)  # page properties
    return md

def body_html(md, img_map):
    out = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
    out = re.sub(r"<pre><code(?: class=\"[^\"]*\")?>(.*?)</code></pre>",
                 lambda m: f'<div class="code"><button class="cp" onclick="cp(this)">copy</button><pre>{m.group(1)}</pre></div>', out, flags=re.S)
    out = re.sub(r"<blockquote>\s*(.*?)\s*</blockquote>", lambda m: f'<div class="tip">{re.sub(r"</?p>", "", m.group(1))}</div>', out, flags=re.S)
    out = out.replace("<ol>", '<ol class="num">')
    out = re.sub(r'<img alt="([^"]*)" src="([^"]+)"',
                 lambda m: f'<figure><img loading="lazy" src="{img_map.get(urllib.parse.unquote(m.group(2)), m.group(2))}" alt="{m.group(1)}"', out)
    out = re.sub(r'(<figure><img[^>]*>)', r'\1</figure>', out)
    out = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', out)
    return out

def split_title(t):
    if ":" in t: a, b = t.split(":", 1); return a.strip() + ":", b.strip()
    w = t.split(); return (" ".join(w[:-2]), " ".join(w[-2:])) if len(w) > 3 else ("", t)

def convert(md_path, kw, credit=None):
    kw = kw.upper()
    md = clean_notion(open(md_path, encoding="utf-8").read())
    # images: copy local files next to the .md into img/KW/
    img_map, src_dir = {}, os.path.dirname(os.path.abspath(md_path))
    for ref in set(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md)):
        local = os.path.join(src_dir, urllib.parse.unquote(ref))
        if not ref.startswith("http") and os.path.isfile(local):
            dest = os.path.join(GUIDES, "img", kw); os.makedirs(dest, exist_ok=True)
            name = re.sub(r"[^\w.-]", "-", os.path.basename(local))
            shutil.copy(local, os.path.join(dest, name)); img_map[urllib.parse.unquote(ref)] = f"img/{kw}/{name}"
    m = re.search(r"^#\s+(.+)$", md, re.M)
    title = m.group(1).strip() if m else kw.title()
    rest = md[m.end():] if m else md
    parts = re.split(r"^##\s+(.+)$", rest, flags=re.M)
    lead = parts[0].strip()
    intro_par = re.split(r"\n\s*\n", lead, maxsplit=1)
    intro = re.sub(r"[*_`]", "", intro_par[0]).strip() if lead else ""
    lead_rest = intro_par[1] if len(intro_par) > 1 else ""
    sections = []
    if lead_rest.strip():
        sections.append(("Shuruaat", "Pehle ye jaano", [("raw", body_html(lead_rest, img_map))]))
    for i in range(1, len(parts), 2):
        h2, body = parts[i].strip(), parts[i + 1]
        step = i // 2 + 1
        words = re.sub(r"[^\w\s]", " ", h2).split()
        tag = f"Step {step}" if re.match(r"^\s*(\d+|step)", h2, re.I) or not words else " ".join(words[:3])[:22]
        sections.append((tag, html.escape(h2), [("raw", body_html(body, img_map))]))
    if not sections:
        sections = [("Guide", html.escape(title), [("raw", body_html(rest, img_map))])]
    t1, t2 = split_title(title)
    out = page(kw, t1, t2, intro or title, sections, credit=credit)
    path = os.path.join(GUIDES, f"{kw}.html")
    open(path, "w", encoding="utf-8").write(out)
    return path

def update_index(kw, n=None):
    p = os.path.join(ROOT, "freebies", "index.html"); s = open(p, encoding="utf-8").read()
    i = s.index("const D=") + 8; j = s.index(";\n", i); d = json.loads(s[i:j])
    hits = [x for x in d["items"] if x["k"] == kw and (n is None or x["n"] == n)]
    for x in hits: x["u"] = f"guides/{kw}.html"
    open(p, "w", encoding="utf-8").write(s[:i] + json.dumps(d, ensure_ascii=False) + s[j:])
    return len(hits)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("md"); ap.add_argument("keyword")
    ap.add_argument("--n", type=int, help="card number when a keyword is used twice (e.g. CLAUDE)")
    ap.add_argument("--update-index", action="store_true"); ap.add_argument("--credit")
    a = ap.parse_args()
    print("wrote", convert(a.md, a.keyword, a.credit))
    if a.update_index: print("cards updated:", update_index(a.keyword.upper(), a.n))
