"""Turn an uploaded .txt / .md / .pdf into guide-box Markdown (## headings = cards, - bullets, 1. steps).

Used by the editor: upload a PDF or text file on a freebie and it lands in the 📝 guide box, so it becomes a
/free/g/KEYWORD guide page (themed, with the course card) instead of a bare file link.
"""
import io, re

BULLET = re.compile(r"^\s*[•●▪◦‣∙·\-–*]\s+")
NUMBERED = re.compile(r"^\s*(\d{1,2})[.)]\s+")
HEADWORD = re.compile(r"^(step|module|part|chapter|section|bonus|day|lesson)\s*\d*\b", re.I)


def pdf_text(data):
    from pypdf import PdfReader  # requirements.txt
    reader = PdfReader(io.BytesIO(data))
    pages = []
    for p in reader.pages:
        try:
            pages.append(p.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n\n".join(pages)


def _is_heading(line, prev_blank, next_blank):
    s = line.strip()
    if not (2 < len(s) <= 70) or BULLET.match(s) or s.endswith((",", ";")):
        return False
    letters = [c for c in s if c.isalpha()]
    if len(letters) >= 3 and s.upper() == s and not s.endswith("."):
        return True                       # ALL CAPS line
    if HEADWORD.match(s) and len(s.split()) <= 9:
        return True                       # "Step 3 ...", "Module 2: ..."
    return prev_blank and next_blank and len(s.split()) <= 8 and not s.endswith((".", "?", "!", ":"))


def text_to_md(text, max_chars=60000):
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    if re.search(r"^#{1,3} ", text, re.M):      # already Markdown with headings: keep as is
        return text.strip()[:max_chars]
    raw = [l.rstrip() for l in text.split("\n")]
    from collections import Counter
    seen = Counter(l.strip() for l in raw if l.strip())
    raw = [l for l in raw if not (l.strip() and len(l.strip()) < 100 and seen[l.strip()] >= 3)]  # repeated headers/footers
    raw = [re.sub(r"\s*·?\s*\d{1,3}\s*/\s*\d{1,3}\s*$", "", l) if re.search(r"·\s*\d{1,3}\s*/\s*\d{1,3}\s*$", l) else l for l in raw]
    raw = [l for l in raw if not re.fullmatch(r"\s*(\d{1,3}|page \d+( of \d+)?|\d+\s*/\s*\d+)\s*", l, re.I)]  # page numbers
    out, para = [], []

    def flush():
        if para:
            out.append(" ".join(para)); out.append(""); para.clear()

    for i, line in enumerate(raw):
        s = line.strip()
        if not s:
            flush(); continue
        prev_blank = i == 0 or not raw[i - 1].strip()
        next_blank = i + 1 >= len(raw) or not raw[i + 1].strip()
        if _is_heading(s, prev_blank, next_blank):
            flush()
            title = s.title() if s.upper() == s and len(s) > 4 else s
            if out and out[-1] != "":
                out.append("")
            out.extend([f"## {title.rstrip(':')}", ""]); continue
        if BULLET.match(s):
            flush()
            if out and out[-1] != "" and not out[-1].startswith("- "):
                out.append("")
            out.append("- " + BULLET.sub("", s)); continue
        m = NUMBERED.match(s)
        if m:
            flush(); out.append(f"{m.group(1)}. " + NUMBERED.sub("", s)); continue
        if out and (out[-1].startswith("- ") or re.match(r"\d+\. ", out[-1])) and not para and not prev_blank:
            out[-1] += " " + s; continue  # wrapped list item
        para.append(s)
    flush()
    md = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
    if "\n## " not in "\n" + md:          # no headings found: split into parts so the guide has cards
        blocks = [b for b in md.split("\n\n") if b.strip()]
        if len(blocks) > 1:
            intro, rest = blocks[0], blocks[1:]
            size = max(2, (len(rest) + 3) // 4)
            parts = [rest[j:j + size] for j in range(0, len(rest), size)]
            md = intro + "\n\n" + "\n\n".join(f"## Part {n}\n\n" + "\n\n".join(p) for n, p in enumerate(parts, 1))
    return md[:max_chars]


def file_to_md(filename, data, max_chars=60000):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        text = pdf_text(data)
        if len(text.strip()) < 40:
            raise ValueError("Is PDF mein text nahi mila (shayad scanned images hain). Text wala PDF ya .txt upload karo.")
    elif ext in ("txt", "md"):
        text = data.decode("utf-8", errors="replace")
    else:
        raise ValueError("Only .pdf, .txt or .md can go into the guide box.")
    return text_to_md(text, max_chars)
