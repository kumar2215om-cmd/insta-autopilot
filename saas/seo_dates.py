"""Real per-page dates for the public pages (sitemap lastmod, the "Updated" line and the Article schema).

Each public path has a fingerprint of the content it is built from. seo_dates.json stores, per path, that fingerprint,
the date the page was first published and the date its content last changed. When a page's content changes, run
`python3 tools/seo_dates.py` (a test fails until you do): only the pages whose fingerprint changed get today's date.
"""
import hashlib
import json
import os

import plans
import seo_content as seo

HERE = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(HERE, "seo_dates.json")
LEGAL = ("/privacy", "/terms", "/refund", "/shipping", "/contact")


def _h(value):
    return hashlib.sha1(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:12]


def _file(name):
    with open(os.path.join(HERE, "templates", name), encoding="utf-8") as f:
        return f.read()


def source(path):
    """What the page at path is built from (its fingerprint changes when, and only when, that changes)."""
    parts = path.strip("/").split("/")
    if path == "/":
        return _file("landing.html")
    if path == "/pricing":
        return [plans.PLANS, plans.USD, seo.PRICING]
    if path in LEGAL:
        return _file("legal.html")
    if len(parts) == 2:
        group = {"features": seo.FEATURES, "vs": seo.COMPARE, "guides": seo.GUIDES}[parts[0]]
        return group[parts[1]]
    if parts[0] in seo.PILLARS:
        return seo.PILLARS[parts[0]]
    if path == "/glossary":
        return seo.GLOSSARY
    hub = {"/features": seo.FEATURES, "/compare": seo.COMPARE, "/guides": seo.PILLARS}[path]
    return {k: (v.get("title"), v.get("description")) for k, v in hub.items()}


def fingerprint(path):
    return _h(source(path))


_cache = None


def load():
    global _cache
    if _cache is None:
        try:
            with open(FILE, encoding="utf-8") as f:
                _cache = json.load(f)
        except (OSError, ValueError):
            _cache = {}
    return _cache


def modified(path):
    """The date (YYYY-MM-DD) the page's content last changed."""
    return (load().get(path) or {}).get("modified") or seo.UPDATED


def published(path):
    return (load().get(path) or {}).get("published") or seo.UPDATED


def stale():
    """Paths whose content changed (or that are new) since seo_dates.json was last refreshed."""
    data = load()
    return [p for p in seo.all_paths() if (data.get(p) or {}).get("hash") != fingerprint(p)]


def refresh(today):
    """Gives changed and new pages today's date; keeps every other date. Returns the paths it changed."""
    global _cache
    data, changed = dict(load()), []
    for p in seo.all_paths():
        fp, row = fingerprint(p), data.get(p)
        if not row:
            data[p] = {"published": today, "modified": today, "hash": fp}
            changed.append(p)
        elif row.get("hash") != fp:
            data[p] = {**row, "modified": today, "hash": fp}
            changed.append(p)
    data = {p: data[p] for p in seo.all_paths()}
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
        f.write("\n")
    _cache = data
    return changed
