"""ReplyInbox (formerly LikhoDM): comment-to-DM automation for any Instagram creator ("Login with Instagram").

A separate app from ../app.py (Om's own site). Same approved Meta app, many accounts:
each creator connects their Instagram, sets keyword rules per reel, and gets the
comment reply → DM → follow check → link flow on their own account.
"""
import base64
import csv
import io
import re
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urlencode

import requests
from flask import Flask, abort, jsonify, make_response, Response, redirect, render_template, request, session, url_for

import ai_agent
import content_drafts
import users
import billing
import referrals
import shop
import courses
import pagestats
import agents
import assistant
import leads
import devices
import videos
import youtube
import files
import guides
import demo
import push
import engine
import plans
import store


def env(name, default=""):
    return os.environ.get(name, default).strip().strip('"').strip("'")


IG_APP_ID = env("IG_APP_ID")              # Instagram app ID (Instagram → API setup with Instagram business login)
IG_APP_SECRET = env("IG_APP_SECRET")      # Instagram app secret (also signs webhooks)
VERIFY_TOKEN = env("IG_VERIFY_TOKEN", "change-me")
CRON_SECRET = env("CRON_SECRET")
OWNER_PASSWORD = env("OWNER_PASSWORD")    # for /owner (list of connected accounts)
PUBLIC_URL = env("PUBLIC_URL").rstrip("/")  # e.g. https://app.likhodm.com; else taken from the request
BRAND = env("BRAND_NAME", "ReplyInbox")
CONTACT_EMAIL = env("CONTACT_EMAIL")
# "open": anyone can connect. "invite": only with a code from INVITE_CODES (comma separated), e.g. for a beta.
SIGNUPS = env("SIGNUPS", "open")
INVITE_CODES = {c.strip().upper() for c in env("INVITE_CODES").split(",") if c.strip()}
SERVERLESS = bool(os.environ.get("VERCEL"))

SCOPES = ("instagram_business_basic,instagram_business_manage_messages,"
          "instagram_business_manage_comments,instagram_business_manage_insights")
WEBHOOK_FIELDS = "comments,messages,messaging_postbacks"
LIVE_FIELDS = WEBHOOK_FIELDS + ",live_comments"  # tried first; falls back if the Meta app doesn't have live_comments yet
REELS_CACHE_SECONDS = 300
REPORT_CACHE_SECONDS = 600  # each reel's insights is one request against Instagram's hourly limit
REPORT_REELS = 12

app = Flask(__name__)
app.secret_key = env("SECRET_KEY") or secrets.token_hex(32)  # set SECRET_KEY in production, or logins reset
app.config.update(MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # Vercel refuses bigger bodies anyway
                  SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=SERVERLESS,
                  SESSION_COOKIE_HTTPONLY=True, PERMANENT_SESSION_LIFETIME=30 * 86400)


def client_ip():
    """The visitor's IP for rate limits. On Vercel the edge sets x-real-ip itself, so a client can't fake it."""
    for h in ("x-real-ip", "x-vercel-forwarded-for"):
        v = request.headers.get(h, "").split(",")[0].strip()
        if v and SERVERLESS:
            return v
    return request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip() if not SERVERLESS else (request.remote_addr or "")


def base_url():
    return PUBLIC_URL or request.host_url.rstrip("/")


def current_user():
    """The signed-in ReplyInbox user (Google or email login), or None."""
    return users.get(session.get("user")) if session.get("user") else None


def current_account():
    uid = session.get("uid")
    acc = store.load_account(uid)
    if not acc and uid == demo.DEMO_ID:  # demo data lives in memory without a database: recreate it
        acc = demo.seed()
    if not acc and not session.get("member") and current_user():  # this account was removed: open another one
        others = users.accounts(current_user())
        if others:
            acc = others[0]
            session["uid"] = acc["id"]
    if acc and session.get("member"):
        return acc if team_member(acc, session["member"]) else None  # removed from the team
    if acc and not demo.is_demo(acc):
        user = current_user()
        if not user or not users.owns(user, acc["id"]):
            return None  # an Instagram account opens only for the user who connected it
    return acc


# ---------- team: managers and viewers who log in with an invite link ----------

ROLES = {"manager": "Manager", "viewer": "Viewer"}
OWNER_ONLY = ("/api/disconnect", "/api/team", "/api/mcp-key", "/api/integrations", "/api/billing", "/api/refer", "/api/shop", "/api/courses", "/api/payments")
MAX_TEAM = 5


def locked(acc, feature):
    """None when the plan has the feature, else a 403 that says which plan it needs (the dashboard shows the message)."""
    if plans.has(acc, feature):
        return None
    return jsonify(error=plans.upgrade_msg(feature), upgrade=plans.needs(feature), feature=feature), 403


def team_member(acc, member_id):
    return next((m for m in acc.get("team") or [] if m["id"] == member_id), None)


def current_role():
    """"owner", or the logged-in team member's role."""
    acc = store.load_account(session.get("uid"))
    member = team_member(acc, session["member"]) if acc and session.get("member") else None
    return member["role"] if member else "owner"


def role_blocks(path, method):
    """Why the logged-in person may not do this, or ""."""
    role = current_role()
    if role == "owner":
        return ""
    if any(path.startswith(p) for p in OWNER_ONLY):
        return "Only the account owner can do this."
    if role == "viewer" and method in ("POST", "PUT", "DELETE") and path not in ("/api/onboarding", "/api/guard/test"):
        return "You have view-only access."
    return ""


def avatar_url(acc):
    """Instagram's picture links are signed and expire after a few days, so pages use /avatar/<id>, which keeps it fresh."""
    return f"/avatar/{acc['id']}" if acc and acc.get("pic") and not acc.get("demo") else ""


def public_account(acc):
    """What the dashboard may see: never the token."""
    return {**{k: acc.get(k) for k in ("id", "username", "name", "followers", "created", "paused", "demo", "plan",
                                        "pro_until")}, "pic": avatar_url(acc), "pro": store.is_pro(acc), "plan_name": plans.PLANS[plans.plan_of(acc)]["name"],
            "follow_gate": plans.has(acc, "follow_gate"), "locks_on": plans.LOCKS_ON, "plan_view": plans.view(acc)}


# Sections of the creator app. Core ones are always on; the rest can be switched off on the Apps page.
SECTIONS = [
    ("home", "/app", "Home", True), ("automations", "/app/automations", "Auto DM", True),
    ("inbox", "/app/inbox", "AI Inbox", False), ("agents", "/app/agents", "AI agents", False), ("activity", "/app/activity", "Activity", True),
    ("sales", "/app/sales", "Sales", True), ("payments", "/app/payments", "Payments", False), ("shop", "/app/products", "Store", False), ("courses", "/app/courses", "Courses", False), ("plan", "/app/plan", "Content plan", False), ("youtube", "/app/youtube", "YouTube", False),
    ("report", "/app/report", "Reel report", False), ("links", "/app/links", "Link in bio", False), ("files", "/app/files", "Files", False),
    ("contacts", "/app/leads", "Leads", False), ("giveaway", "/app/giveaway", "Giveaway", False), ("apps", "/app/apps", "Apps", True),
    ("billing", "/app/billing", "Plan & billing", True), ("refer", "/app/refer", "Refer & earn", True),
    ("settings", "/app/settings", "Settings", True),
]
DEFAULT_APPS = {"agents": True, "payments": True, "shop": True, "courses": True, "plan": True, "youtube": True, "inbox": True, "report": True, "links": True, "files": True, "contacts": True, "giveaway": True}


def apps_of(acc):
    return {**DEFAULT_APPS, **(acc.get("apps") or {})}


def render_app(template, active, **extra):
    acc = current_account()
    if not acc:
        user = current_user()
        if user and not session.get("member"):
            first = next(iter(users.accounts(user)), None)
            if first:  # signed in but no account picked (new device, or the last one was removed)
                session["uid"] = first["id"]
                return redirect(request.path)
            if active == "billing":  # plans can be bought before connecting Instagram
                stub = {"id": "", "username": "", "pic": user.get("pic", ""), "pro": False, "demo": False,
                        "plan_name": plans.PLANS[users.current_plan(user)]["name"]}
                return render_template(template, acc=stub, active=active, role="owner", user=user, no_account=True,
                                       nav=[("billing", "/app/billing", "Plan & billing")], apps={}, linked=[], page_url="", **extra)
            return redirect(url_for("connect_page"))
        return redirect(url_for("signin_page"))
    on = apps_of(acc)
    nav = [(key, href, label) for key, href, label, core in SECTIONS
           if (core or on.get(key)) and (key != "youtube" or youtube.available(acc)) and (key != "files" or files.available(acc))]
    return render_template(template, acc=public_account(acc), active=active, nav=nav, apps=on, role=current_role(),
                           linked=[a for a in linked_accounts() if a["id"] != acc["id"]], user=current_user(),
                           page_url=f"{request.host_url.rstrip('/')}/{acc.get('username', '')}", **extra)


SITE_URL = env("SITE_URL").rstrip("/")  # the address search engines should index; set it once the main domain works


def site_url():
    """Canonical address for public pages: SITE_URL when set, else the address this request came in on."""
    return SITE_URL or request.host_url.rstrip("/")


# Google Search Console HTML-tag verification for replyinbox.in (public by design; override with the env var)
GOOGLE_SITE_VERIFICATION = env("GOOGLE_SITE_VERIFICATION", "SVdI_dSxjwmjhHFP0wxRZa-GRUsDbV_GRLqhqWvm2-s")


@app.context_processor
def brand():
    return {"brand": BRAND, "contact_email": CONTACT_EMAIL, "public_url": base_url() if request else "",
            "site_url": site_url() if request else "", "google_site_verification": GOOGLE_SITE_VERIFICATION}


PRIVATE_PREFIXES = ("/app", "/api", "/owner", "/demo", "/join", "/l", "/s", "/r", "/auth", "/login", "/cron", "/mcp", "/report",
                    "/billing", "/signin", "/connect", "/admin", "/f", "/d", "/learn", "/cert")


def is_private_path(path):
    """True for the dashboard, demo, short links and the like (whole path segments only, so /apple.store stays public)."""
    return any(path == p or path.startswith(p + "/") for p in PRIVATE_PREFIXES)


CSP = ("default-src 'self' https:; "
       "script-src 'self' 'unsafe-inline' https://checkout.razorpay.com https://www.googletagmanager.com https://connect.facebook.net "
       "https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; "
       "img-src 'self' data: blob: https:; media-src 'self' blob: https:; frame-src 'self' https:; connect-src 'self' https:; worker-src 'self'; "
       "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'")


@app.after_request
def no_index_private(resp):
    """Keep the dashboard, demo and redirect links out of search results, and send the security headers on every page."""
    if is_private_path(request.path):
        resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    h = resp.headers
    h.setdefault("X-Content-Type-Options", "nosniff")
    h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    h.setdefault("X-Frame-Options", "SAMEORIGIN")
    h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(self \"https://checkout.razorpay.com\" \"https://api.razorpay.com\")")
    h.setdefault("Cross-Origin-Opener-Policy", "same-origin-allow-popups")
    if resp.mimetype == "text/html":
        h.setdefault("Content-Security-Policy", CSP)
    if SERVERLESS:
        h.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if request.path.startswith(("/api/", "/learn", "/owner", "/app")) and "Cache-Control" not in h:
        h["Cache-Control"] = "private, no-store"  # personal data never sits in a shared cache
    return resp


@app.before_request
def no_trailing_slash():
    """/features/ → /features (one address per page; the slash version used to be a 404)."""
    path = request.path
    if request.method in ("GET", "HEAD") and len(path) > 1 and path.endswith("/") and not path.startswith(("/api/", "/static/")):
        target = path.rstrip("/") or "/"
        if request.query_string:
            target += "?" + request.query_string.decode("latin-1")
        return redirect(target, 301)


@app.errorhandler(404)
def not_found(e):
    """A branded page with a way back for people; JSON for the API."""
    if request.path.startswith("/api/"):
        return jsonify(error="Not found"), 404
    page = {"kind": "notfound", "title": "Page not found", "h1": "This page doesn't exist",
            "description": f"The page you opened isn't on {BRAND}.",
            "cards": [{"url": "/", "title": f"{BRAND} home", "text": "Instagram DM automation for creators."},
                      {"url": "/pricing", "title": "Pricing", "text": "Free plan and paid plans in ₹ and $."},
                      {"url": "/guides", "title": "Guides", "text": "How to auto DM, grow followers and sell on Instagram."},
                      {"url": "/features", "title": "Features", "text": "Comment-to-DM, follow to unlock, AI replies and more."}]}
    return render_template("content.html", page=page, path=request.path, crumbs=[("Not found", None)], related=[], schema=[],
                           updated="", checked=seo.CHECKED, topic=None, noindex=True), 404


@app.before_request
def guard():
    # a sign-in that was signed out from another device (Settings → Security) ends here
    if session.get("user") and (request.path.startswith("/app") or request.path.startswith("/api/")):
        if not session.get("sid"):  # signed in before devices were tracked
            session["sid"] = devices.start(session["user"], *client_info())
        elif not devices.check(session["user"], session["sid"], *client_info()):
            session.clear()
            if request.path.startswith("/api/"):
                return jsonify(error="You were signed out. Please log in again."), 401
            return redirect("/signin")
    # Logged-in API calls that change data must be JSON: a cross-site form can't send that without CORS.
    if request.path.startswith(("/api/", "/owner")) and request.method in ("POST", "PUT", "DELETE") \
            and request.headers.get("Sec-Fetch-Site") == "cross-site":
        return jsonify(error="Cross-site request refused."), 403  # a second lock on top of the JSON rule
    if request.path.startswith("/api/"):
        if not current_account() and not ((request.path == "/api/switch" or request.path.startswith("/api/billing")) and current_user()):
            return jsonify(error="Please log in again."), 401
        # file uploads are multipart; a custom header still can't be sent cross-site without CORS
        upload = (request.path in ("/api/files", "/api/shop/upload", "/api/courses/upload") or request.path.startswith("/api/courses/video/")) \
            and request.headers.get("X-Upload") == "1"
        if request.method in ("POST", "PUT", "DELETE") and not request.is_json and not upload:
            return jsonify(error="JSON required"), 415
        blocked = role_blocks(request.path, request.method)
        if blocked:
            return jsonify(error=blocked), 403


# ---------- pages ----------

@app.get("/")
def landing():
    # Logged-in creators can still read the landing page; the nav then offers "Open dashboard".
    ref = clean_ref(request.args.get("ref"))
    if ref:
        session["ref"] = ref
    referrer = store.account_by_username(session["ref"]) if session.get("ref") else None
    return render_template("landing.html", invite_only=SIGNUPS == "invite", error=request.args.get("error", ""),
                           signed_in=bool(current_user() or current_account()), schema=landing_schema(), billing_live=billing.ready(),
                           referrer=referrer.get("username") if referrer else "")


# ---------- public pages for search engines and AI assistants (SEO / AEO / GEO) ----------

import seo_content as seo  # noqa: E402
import seo_dates  # noqa: E402
from markupsafe import escape  # noqa: E402


def fill(value):
    """Replaces {brand} in page content (strings, lists, tuples, dicts)."""
    if isinstance(value, str):
        return value.replace("{brand}", BRAND)
    if isinstance(value, (list, tuple)):
        return type(value)(fill(v) for v in value)
    if isinstance(value, dict):
        return {k: fill(v) for k, v in value.items()}
    return value


# Public profiles of the product. ReplyInbox (Instagram DM automation, replyinbox.in) is a different company from
# ReplyInbox the AI email tool (replyinbox.com); sameAs and disambiguatingDescription tell search engines and AI apart.
SAME_AS = [u for u in env("BRAND_PROFILES", "https://www.instagram.com/replyinbox.in/").split() if u.startswith("https://")]


def org_schema():
    return {"@type": "Organization", "@id": f"{site_url()}/#org", "name": BRAND, "alternateName": f"{BRAND} Instagram DM automation",
            "url": f"{site_url()}/", "logo": f"{site_url()}/static/icon-512.png", "sameAs": SAME_AS,
            "description": "Instagram DM automation for creators in India and worldwide: comment-to-DM, follow to unlock, AI DM replies and sales tracking.",
            "disambiguatingDescription": f"{BRAND} at {site_url().split('//')[-1]} is an Instagram DM automation tool. It is not the AI email "
                                         "reply tool of the same name at replyinbox.com.",
            "areaServed": "IN", **({"email": CONTACT_EMAIL} if CONTACT_EMAIL else {})}


def faq_schema(faq):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}


_LANDING_FAQ = None


def landing_faq():
    """The landing page's FAQ, read from the template so the page and its structured data never disagree."""
    global _LANDING_FAQ
    live = billing.ready()
    if _LANDING_FAQ is None or _LANDING_FAQ[0] != live:
        src = open(os.path.join(app.root_path, "templates", "landing.html"), encoding="utf-8").read()
        # keep only the branch the page actually shows (e.g. the "how do I pay" answer once billing is on)
        src = re.sub(r"\{% if billing_live %\}(.*?)\{% else %\}(.*?)\{% endif %\}",
                     lambda m: m.group(1) if live else m.group(2), src, flags=re.S)
        strip = lambda h: re.sub(r"\s+", " ", re.sub(r"<[^>]+>|\{%.*?%\}", "", h)).replace("{{ brand }}", BRAND).strip()
        _LANDING_FAQ = (live, [(strip(q), strip(a)) for q, a in re.findall(r"<details><summary>(.*?)</summary><p>(.*?)</p></details>", src)])
    return _LANDING_FAQ[1]


def landing_schema():
    offers = [{"@type": "Offer", "name": p["name"], "price": str(p["price"]), "priceCurrency": "INR", "url": f"{site_url()}/pricing"}
              for k, p in plans.PLANS.items()]
    offers += [{"@type": "Offer", "name": plans.PLANS[k]["name"], "price": str(m), "priceCurrency": "USD", "url": f"{site_url()}/pricing"}
               for k, (m, _) in plans.USD.items()]
    return [
        {"@context": "https://schema.org", **org_schema()},
        {"@context": "https://schema.org", "@type": "WebSite", "@id": f"{site_url()}/#website", "name": BRAND, "url": f"{site_url()}/", "publisher": {"@id": f"{site_url()}/#org"}},
        {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": BRAND, "url": f"{site_url()}/",
         "applicationCategory": "BusinessApplication", "applicationSubCategory": "Instagram DM automation", "operatingSystem": "Web, Android, iOS",
         "description": "Instagram DM automation for creators: comment-to-DM, follow to unlock, story replies, email and WhatsApp "
                        "capture, follow-up offers, an AI that answers DMs in any language, and sales tracking per reel.",
         "featureList": ["Comment-to-DM", "Follow to unlock", "Story reply and mention automation", "Email and WhatsApp capture",
                         "AI DM agent in any language", "Follow-up offers", "Broadcast to recent chats", "Sales tracking per reel",
                         "Link in bio page", "Claude (MCP) integration"],
         "offers": offers, "publisher": {"@id": f"{site_url()}/#org"}},
        faq_schema(landing_faq()),
    ]


def entity_ld(key):
    e = seo.ENTITIES[key]
    return {"@type": e["type"], "name": e["name"], "sameAs": e["sameAs"]}


def term_ld(key):
    name, text, _ = seo.GLOSSARY[key]
    return {"@type": "DefinedTerm", "@id": f"{site_url()}/glossary#{key}", "name": name, "description": fill(text),
            "inDefinedTermSet": f"{site_url()}/glossary"}


_ANCHOR_RE = None


def autolink(html, path, used):
    """Links the first mention of each known phrase (seo.ANCHORS) to the page that explains it: in-body links between
    related pages. Skips text inside links, headings, code and tables, never links a page to itself, at most 6 per page."""
    global _ANCHOR_RE
    if _ANCHOR_RE is None:
        _ANCHOR_RE = re.compile(r"(?<![\w/-])(" + "|".join(re.escape(a) for a, _ in sorted(seo.ANCHORS, key=lambda x: -len(x[0]))) + r")(?![\w-])",
                                re.I)
    urls = {a.lower(): u for a, u in seo.ANCHORS}
    out, skip = [], 0
    for part in re.split(r"(<[^>]+>)", html):
        if part.startswith("<"):
            tag = re.match(r"</?\s*(\w+)", part)
            if tag and tag.group(1).lower() in ("a", "h2", "h3", "code", "table", "summary"):
                skip += -1 if part.startswith("</") else 1
            out.append(part)
            continue
        if skip > 0 or len(used) >= 6:
            out.append(part)
            continue

        def link(m):
            url = urls[m.group(1).lower()]
            if url == path or url in used or len(used) >= 6:
                return m.group(0)
            used.add(url)
            return f'<a href="{url}">{m.group(0)}</a>'
        out.append(_ANCHOR_RE.sub(link, part))
    return "".join(out)


def content_page(page, path, crumbs, related=(), pillar=None):
    """Renders a public content page. pillar: the topic hub this page belongs to (hub-and-spoke linking + schema)."""
    page = fill(page)
    used = {c["url"] for c in related} if page.get("kind") == "pillar" else set()
    page["sections"] = [(h, autolink(html, path, used)) for h, html in page.get("sections") or []]
    if page.get("kind") in ("feature", "compare", "guide"):
        # a few related pages inside the article itself (descriptive links; the cards below are the full list)
        more = [c for c in related if c["url"] not in used][:3]
        if more:
            page["sections"].append(("Aur padho" if page.get("lang") == "hi-Latn" else "Keep reading", "<ul>" + "".join(
                f'<li><a href="{c["url"]}">{escape(c["title"])}</a>: {escape(c["text"])}</li>' for c in more) + "</ul>"))
    schema = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": name, "item": f"{site_url()}{url or path}"}
        for i, (name, url) in enumerate([("Home", "/")] + list(crumbs))]}]
    kind = page.get("kind")
    if kind in ("feature", "compare", "guide"):
        art = {"@context": "https://schema.org", "@type": "Article", "headline": page.get("h1") or page["title"],
               "description": page["description"], "dateModified": seo_dates.modified(path), "datePublished": seo_dates.published(path),
               "mainEntityOfPage": f"{site_url()}{path}", "author": {"@id": f"{site_url()}/#org"},
               "publisher": org_schema(), "image": f"{site_url()}/static/og.png"}
        if pillar:
            p = seo.PILLARS[pillar]
            art["isPartOf"] = {"@type": "CollectionPage", "@id": f"{site_url()}/{pillar}", "name": fill(p["title"])}
            art["about"] = [entity_ld(e) for e in p["about"]]
            art["mentions"] = [term_ld(t) for t in p["terms"]]
        schema.append(art)
    if page.get("faq"):
        schema.append(faq_schema(page["faq"]))
    schema += page.pop("extra_schema", [])
    topic = None
    if pillar:
        topic = {"url": f"/{pillar}", "title": fill(seo.PILLARS[pillar]["title"]), "short": seo.PILLARS[pillar]["short"]}
    return render_template("content.html", page=page, path=path, crumbs=crumbs, related=fill(list(related)), schema=schema,
                           updated=seo_dates.modified(path), checked=seo.CHECKED, topic=topic)


def cluster_item(kind, slug):
    return {"feature": seo.FEATURES, "compare": seo.COMPARE, "guide": seo.GUIDES}[kind][slug]


def cluster_context(kind, slug, title):
    """The pillar a cluster page belongs to, its breadcrumbs and its sibling pages (spokes link up and across)."""
    pillar = seo.pillar_of()[(kind, slug)]
    p = seo.PILLARS[pillar]
    siblings = [card(k, s_, cluster_item(k, s_)) for k, s_ in p["clusters"] if (k, s_) != (kind, slug)]
    return pillar, [(p["short"], f"/{pillar}"), (title, None)], siblings[:6]


def card(kind, slug, item):
    url = {"feature": "/features/", "compare": "/vs/", "guide": "/guides/"}[kind] + slug
    title = item["title"] if kind != "compare" else f"{BRAND} vs {item['name']}"
    return {"url": url, "title": fill(title), "text": fill(item["description"])}


@app.get("/features")
def features_hub():
    return content_page({"kind": "hub", "title": "Features", "h1": f"Everything {BRAND} does on Instagram",
                         "description": f"All {BRAND} features: comment-to-DM, follow to unlock, AI DM agent, story replies, lead capture and sales tracking.",
                         "intro": "Pick a feature to see how it works, what it costs and common questions.",
                         "cards": [card("feature", k, v) for k, v in seo.FEATURES.items()]}, "/features", [("Features", None)])


@app.get("/features/<slug>")
def feature_page(slug):
    item = seo.FEATURES.get(slug) or abort(404)
    pillar, crumbs, related = cluster_context("feature", slug, item["title"])
    return content_page({**item, "kind": "feature"}, f"/features/{slug}", crumbs, related, pillar)


@app.get("/compare")
def compare_hub():
    return content_page({"kind": "hub", "title": "Compare Instagram DM automation tools", "h1": f"{BRAND} compared with other tools",
                         "description": f"Honest comparisons of {BRAND} with ManyChat, LinkDM, SuperProfile, Repli, ReplyKaro, InstantDM, ReplyRush, CreatorFlow, Zorcha, Inrō and RapidDM.",
                         "intro": "Side-by-side comparisons with prices and features, checked " + seo.CHECKED + ".",
                         "cards": [card("compare", k, v) for k, v in seo.COMPARE.items()]
                                  + [card("guide", g, seo.GUIDES[g]) for g in ("best-instagram-dm-automation-tools", "manychat-alternatives",
                                                                               "instagram-dm-automation-pricing")]},
                        "/compare", [("Compare", None)])


@app.get("/vs/<slug>")
def compare_page(slug):
    item = seo.COMPARE.get(slug) or abort(404)
    page = {**item, "kind": "compare", "h1": f"{BRAND} vs {item['name']}: the {item['name']} alternative for Instagram",
            "title": next(t for t in (f"{item['name']} alternative: {BRAND} vs {item['name']} (2026)",
                                         f"{item['name']} alternative: {BRAND} vs {item['name']}",
                                         f"{item['name']} alternative for Instagram (2026)") if len(t) <= 65),
            "faq": [(f"Is {BRAND} a good {item['name']} alternative?", f"Yes, if {item['choose_us']}"),
                    (f"How much does {BRAND} cost?", "Free for 1,000 DMs a month; Starter is ₹149 / $5, and Creator ₹199 / $9 a month "
                                                     "with no monthly DM limit and AI replies included.")] + list(item.get("faq_extra", []))}
    pillar, crumbs, related = cluster_context("compare", slug, f"vs {item['name']}")
    return content_page(page, f"/vs/{slug}", crumbs, related, pillar)


@app.get("/guides")
def guides_hub():
    """The learning centre: every topic (pillar) with all its pages."""
    groups = [{"title": fill(p["title"]), "url": f"/{k}", "text": fill(p["description"]),
               "cards": [card(kind, s_, cluster_item(kind, s_)) for kind, s_ in p["clusters"]]} for k, p in seo.PILLARS.items()]
    return content_page({"kind": "hub", "title": "Instagram DM automation guides", "h1": "Learn Instagram DM automation",
                         "description": "Guides on Instagram DM automation, lead generation, selling, AI replies, tools and industry playbooks.",
                         "intro": "Six topics, each with a complete overview and step-by-step pages. Start with a topic, or jump to a guide.",
                         "groups": groups}, "/guides", [("Guides", None)])


@app.get("/guides/<slug>")
def guide_page(slug):
    item = seo.GUIDES.get(slug) or abort(404)
    pillar, crumbs, related = cluster_context("guide", slug, item["title"])
    return content_page({**item, "kind": "guide"}, f"/guides/{slug}", crumbs, related, pillar)


def pillar_page(slug):
    """A topic hub: the full overview, then every page in the topic, the key terms and the other topics."""
    p = seo.PILLARS[slug]
    clusters = [card(kind, s_, cluster_item(kind, s_)) for kind, s_ in p["clusters"]]
    others = [{"url": f"/{k}", "title": fill(o["title"]), "text": fill(o["description"])} for k, o in seo.PILLARS.items() if k != slug]
    page = {**p, "kind": "pillar", "h1": p["title"], "cards": clusters,
            "terms_list": [(k, seo.GLOSSARY[k][0], seo.GLOSSARY[k][1]) for k in p["terms"]],
            "extra_schema": [{"@context": "https://schema.org", "@type": "CollectionPage", "@id": f"{site_url()}/{slug}",
                              "name": fill(p["title"]), "description": fill(p["description"]), "url": f"{site_url()}/{slug}",
                              "dateModified": seo_dates.modified(f"/{slug}"), "isPartOf": {"@id": f"{site_url()}/#website", "@type": "WebSite", "name": BRAND},
                              "about": [entity_ld(e) for e in p["about"]], "mentions": [term_ld(t) for t in p["terms"]],
                              "hasPart": [{"@type": "WebPage", "url": f"{site_url()}{c['url']}", "name": c["title"]} for c in clusters]}]}
    return content_page(page, f"/{slug}", [(p["short"], None)], others)


for _slug in seo.PILLARS:
    app.add_url_rule(f"/{_slug}", f"pillar_{_slug.replace('-', '_')}", lambda _slug=_slug: pillar_page(_slug))


def pricing_sections():
    """The /pricing page body, built from plans.py so it always shows the live prices and limits."""
    P, U = plans.PLANS, plans.USD
    order = ["free", "starter", "creator", "pro", "agency"]
    inr = lambda k: f"₹{P[k]['price']:,}"
    usd = lambda k: f"${U[k][0]}"
    yr = lambda k: f"₹{P[k]['yearly']:,}" if P[k]["yearly"] else "–"
    dms = lambda k: f"{P[k]['monthly_dms']:,}" if P[k]["monthly_dms"] else "No limit*"
    ai = lambda k: f"{P[k]['ai_replies']:,} to try" if P[k].get("ai_kind") == "trial" else f"{P[k]['ai_replies']:,} a month"
    lim = lambda k, f: f"{P[k][f]:,}" if P[k].get(f) else "–"  # the plan's own numbers, whether or not plan locks are on
    yes = lambda k, f: "✓" if plans.ORDER.index(k) >= plans.ORDER.index(plans.FEATURES[f]) else "–"
    rows = [("Price a month", inr), ("Price in US$", usd), ("Price a year", yr), ("DMs a month", dms),
            ("Instagram accounts", lambda k: {"pro": "3", "agency": "10"}.get(k, "1")), ("AI DM replies", ai),
            ("Comment-to-DM, keyword DMs, Live comments, link in bio", lambda k: "✓"),
            ("Follow to unlock, email and WhatsApp capture, story replies", lambda k: yes(k, "follow_gate")),
            ("Lead Qualifier agent (chats a month)", lambda k: lim(k, "lead_agent")),
            ("Brand Collab agent (brand DMs a month)", lambda k: lim(k, "brand_agent")),
            ("Automatic course emails a month", lambda k: lim(k, "course_emails")),
            ("Course video upload", lambda k: f"{P[k]['video_gb']} GB" if P[k].get("video_gb") else "–"),
            ("Connect Claude (MCP)", lambda k: yes(k, "mcp")),
            ("Team members", lambda k: lim(k, "team")),
            ("Fee per sale through " + BRAND, lambda k: "2% + GST" if k in ("pro", "agency") else "5% + GST")]
    table = ("<div class=\"scroll\"><table><thead><tr><th>Plan</th>" + "".join(f"<th>{P[k]['name']}</th>" for k in order) + "</tr></thead><tbody>"
             + "".join(f"<tr><td>{name}</td>" + "".join(f"<td>{fn(k)}</td>" for k in order) + "</tr>" for name, fn in rows)
             + "</tbody></table></div><p class=\"note\">* Fair use. Instagram's own limits still apply: one private reply per comment within "
               "7 days, and hourly limits on very busy reels. ₹ prices include GST.</p>")
    choose = "<ul>" + "".join(f"<li><b>{name}</b> ({inr(name.lower())}): {fill(text)}</li>" for name, text in seo.PRICING["choose"]) + "</ul>"
    save = ("<p>Yearly plans cost about 10 months' price for 12 months: " + ", ".join(f"{P[k]['name']} {yr(k)}" for k in order[1:])
            + " a year. Need one more Instagram account on Creator or Pro? It's "
            f"₹{plans.EXTRA_ACCOUNT['price']} a month. More AI replies on any paid plan: {plans.AI_TOPUP['replies']:,} for ₹{plans.AI_TOPUP['price']}.</p>")
    sell = ("<p>Selling products, 1:1 calls, events or courses through " + BRAND + " costs <b>5% + GST per sale</b> on Free, Starter and Creator, "
            "and <b>2% + GST</b> (plus the payment gateway's charge) on Pro and Agency. Buyers pay with UPI or card, and your share goes "
            "to your bank account, usually the next working day. Links to your own payment page (Razorpay, Instamojo, Gumroad, "
            "SuperProfile) have no " + BRAND + " fee, and sales tracking still shows which reel made the sale.</p>")
    compare = ("<p>Most Instagram DM automation tools charge $9–$40 a month, and ManyChat's price rises with the number of contacts. "
               "Indian tools are usually ₹99–₹499 a month. See the <a href=\"/guides/instagram-dm-automation-pricing\">full price comparison</a> "
               "or the <a href=\"/vs/manychat\">ManyChat comparison</a>.</p>")
    return [("All plans compared", table), ("Which plan should you pick?", choose), ("Yearly plans and add-ons", save),
            ("Selling through " + BRAND, sell), ("How this compares", compare)]


@app.get("/pricing")
def pricing_page():
    P = plans.PLANS
    page = {**seo.PRICING, "kind": "pricing",
            "answer": f"{BRAND} has a free plan with {P['free']['monthly_dms']:,} DMs a month. Paid plans are Starter ₹{P['starter']['price']}, "
                      f"Creator ₹{P['creator']['price']} (no monthly DM limit, 300 AI replies), Pro ₹{P['pro']['price']} (3 accounts, Claude) "
                      f"and Agency ₹{P['agency']['price']:,} (10 accounts) a month, taxes included, or about 2 months free when paid yearly.",
            "sections": pricing_sections(),
            "extra_schema": [{"@context": "https://schema.org", "@type": "Product", "name": f"{BRAND} Instagram DM automation",
                              "brand": {"@id": f"{site_url()}/#org"}, "url": f"{site_url()}/pricing",
                              "offers": [{"@type": "Offer", "name": p["name"], "price": str(p["price"]), "priceCurrency": "INR",
                                          "url": f"{site_url()}/pricing"} for p in P.values()]}]}
    return content_page(page, "/pricing", [("Pricing", None)], [card("guide", g, seo.GUIDES[g]) for g in
                        ("instagram-dm-automation-pricing", "manychat-alternatives", "how-to-auto-dm-instagram-comments")])


@app.get("/llms-full.txt")
def llms_full_txt():
    """Every public page as plain text, for AI assistants that read the whole site at once."""
    u, out = site_url(), [f"# {BRAND}: every page in full", "",
                          f"> {BRAND} (replyinbox.in) is Instagram DM automation for creators. Not the AI email tool replyinbox.com.", ""]
    text = lambda h: re.sub(r"[ \t]+", " ", re.sub(r"<li>", "\n- ", re.sub(r"</(p|tr|h\d)>", "\n", h))).strip()
    strip = lambda h: re.sub(r"\n\s*\n+", "\n\n", re.sub(r"<[^>]+>", "", text(h))).strip()
    groups = [("features", seo.FEATURES), ("vs", seo.COMPARE), ("guides", seo.GUIDES)]
    for prefix, items in groups:
        for slug, item in items.items():
            item = fill(item)
            title = item["title"] if prefix != "vs" else f"{BRAND} vs {item['name']}"
            out += [f"## {title}", f"URL: {u}/{prefix}/{slug}", f"Updated: {seo_dates.modified(f'/{prefix}/{slug}')}", "", item["answer"], ""]
            if prefix == "vs":
                out += [f"{item['name']}: " + "; ".join(item["them"]), f"{BRAND}: " + "; ".join(item["us"]), ""]
            for h, html in item.get("sections", []):
                out += [f"### {h}", strip(html), ""]
            for q, a in item.get("faq", []):
                out += [f"Q: {q}", f"A: {a}", ""]
    for slug, p in seo.PILLARS.items():
        p = fill(p)
        out += [f"## {p['title']}", f"URL: {u}/{slug}", "", p["answer"], ""]
        for h, html in p.get("sections", []):
            out += [f"### {h}", strip(html), ""]
    return "\n".join(out) + "\n", 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.get("/glossary")
def glossary_page():
    terms = [(k, name, fill(text), url) for k, (name, text, url) in seo.GLOSSARY.items()]
    page = {"kind": "glossary", "title": "Instagram DM automation glossary", "h1": "Instagram DM automation glossary",
            "description": "Definitions of Instagram DM automation terms: comment-to-DM, private reply, 24-hour window, follow gate, lead magnet and more.",
            "answer": f"Plain definitions of the terms used in Instagram DM automation, each linked to a page that explains it in depth.",
            "terms": terms,
            "extra_schema": [{"@context": "https://schema.org", "@type": "DefinedTermSet", "@id": f"{site_url()}/glossary",
                              "name": "Instagram DM automation glossary", "hasDefinedTerm": [term_ld(k) for k in seo.GLOSSARY]}]}
    return content_page(page, "/glossary", [("Glossary", None)])


@app.get("/robots.txt")
def robots_txt():
    lines = ["# Search engines and AI assistants are welcome on the public pages.", "User-agent: *", "Allow: /"]
    lines += [f"Disallow: {p}/" for p in PRIVATE_PREFIXES] + [f"Disallow: /{p}$" for p in ("app", "demo", "login", "owner", "report")]
    lines += ["", f"Sitemap: {site_url()}/sitemap.xml"]
    return "\n".join(lines) + "\n", 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.get("/sitemap.xml")
def sitemap_xml():
    urls = "".join(f"<url><loc>{site_url()}{p}</loc><lastmod>{seo_dates.modified(p)}</lastmod></url>" for p in seo.all_paths())
    return (f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
            200, {"Content-Type": "application/xml; charset=utf-8"})


@app.get("/llms.txt")
def llms_txt():
    """A plain summary for AI assistants (the llms.txt convention): what the product is, prices, and where details live."""
    u = site_url()
    p = plans.PLANS
    out = [f"# {BRAND}", "",
           f"> {BRAND} is Instagram DM automation for creators, coaches and brands: comment-to-DM, follow to unlock, story reply and "
           "mention automation, email and WhatsApp capture, follow-up offers, broadcasts to recent chats, an AI agent that answers "
           "DMs in the fan's language, and sales tracking that shows which reel made money. Built on Meta's official Instagram API; "
           "no Instagram password needed.", "",
           "## Pricing (monthly)",
           f"- Free: ₹0 / $0, {p['free']['monthly_dms']:,} DMs a month, 25 AI replies to try",
           f"- Starter: ₹{p['starter']['price']} / ${plans.USD['starter'][0]}, 3,000 DMs, follow to unlock, email and WhatsApp capture, story replies",
           f"- Creator: ₹{p['creator']['price']} / ${plans.USD['creator'][0]}, unlimited DMs, 300 AI replies, Lead Qualifier agent, course extras (US$ price, GST, bump offers), course emails",
           f"- Pro: ₹{p['pro']['price']} / ${plans.USD['pro'][0]}, 3 Instagram accounts, 2,000 AI replies, Connect Claude (MCP), Brand Collab agent, course video upload, no ReplyInbox branding",
           f"- Agency: ₹{p['agency']['price']:,} / ${plans.USD['agency'][0]}, 10 accounts, 10,000 AI replies, one Claude link for every account",
           "- Selling through ReplyInbox: 5% + GST per sale on Free, Starter and Creator; 2% + GST (plus the payment gateway's charge) on Pro and Agency.", "",
           "## Topics"]
    for k, pil in seo.PILLARS.items():
        out += ["", f"### [{fill(pil['title'])}]({u}/{k})", fill(pil["answer"])]
        for kind, s_ in pil["clusters"]:
            c = card(kind, s_, cluster_item(kind, s_))
            out.append(f"- [{c['title']}]({u}{c['url']}): {fill(cluster_item(kind, s_)['answer'])}")
    out += ["", "## Glossary", f"- [{BRAND} glossary]({u}/glossary): definitions of Instagram DM automation terms"]
    out += [
           "", "## Links", f"- Website: {u}/", f"- Pricing: {u}/pricing", f"- Every page in full: {u}/llms-full.txt", f"- Live demo: {u}/demo", f"- Privacy: {u}/privacy"]
    return "\n".join(out) + "\n", 200, {"Content-Type": "text/plain; charset=utf-8"}


# ---------- refer & earn (see referrals.py) ----------

def clean_ref(value):
    value = str(value or "").strip().lstrip("@").lower()
    return value if re.fullmatch(r"[a-z0-9._]{1,30}", value) else ""


@app.get("/r/<code>")
def referral_link(code):
    """Short invite link: replyinbox.in/r/<username>."""
    ref = clean_ref(code)
    if ref:
        session["ref"] = ref
    return redirect(url_for("landing"))


@app.get("/app/refer")
def refer_page():
    return render_app("refer.html", "refer", starter_price=plans.PLANS["starter"]["price"])


def refer_user():
    user = current_user()
    if not user:
        abort(403)
    return user


@app.get("/api/refer")
def api_refer():
    acc = current_account()
    if acc.get("demo"):
        return jsonify(error="Refer & earn isn't available in the demo."), 403
    return jsonify(referrals.summary(refer_user(), f"{base_url()}/r/{acc.get('username', '')}"))


@app.put("/api/refer/upi")
def api_refer_upi():
    try:
        return jsonify(upi=referrals.set_upi(refer_user(), (request.get_json(force=True) or {}).get("upi")))
    except referrals.ReferralError as e:
        return jsonify(error=str(e)), 400


@app.post("/api/refer/payout")
def api_refer_payout():
    try:
        return jsonify(payout=referrals.request_payout(refer_user()))
    except referrals.ReferralError as e:
        return jsonify(error=str(e)), 400


@app.get("/app")
def dashboard():
    return render_app("home.html", "home")


@app.get("/app/automations")
def automations_page():
    return render_app("automations.html", "automations")


@app.get("/app/links")
def links_page():
    return render_app("links_edit.html", "links")


@app.get("/app/contacts")
def contacts_page():
    return render_app("contacts.html", "contacts")


@app.get("/app/inbox")
def inbox_page():
    return render_app("inbox.html", "inbox")


@app.get("/app/giveaway")
def giveaway_page():
    return render_app("giveaway.html", "giveaway")


@app.get("/app/apps")
def apps_page():
    return render_app("apps.html", "apps")


@app.get("/app/settings")
def settings_page():
    return render_app("settings.html", "settings")


@app.get("/demo")
def demo_login():
    """Opens the app with a sample account (no Instagram login), to preview everything."""
    demo.seed()
    session.clear()
    session["uid"] = demo.DEMO_ID
    return redirect(url_for("dashboard"))


@app.get("/privacy")
@app.get("/terms")
@app.get("/data-deletion")
@app.get("/refund")
@app.get("/contact")
@app.get("/shipping")
def legal():
    # BUSINESS_NAME / BUSINESS_ADDRESS / CONTACT_PHONE: shown on the contact page (Razorpay's website review asks for them)
    business = {"name": env("BUSINESS_NAME"), "address": env("BUSINESS_ADDRESS"), "phone": env("CONTACT_PHONE")}
    return render_template("legal.html", page=request.path.strip("/"), business=business, updated="18 Nov 2026")


@app.get("/deletion")
def deletion_status():
    code = request.args.get("code", "")
    done = bool(code) and store.redis("GET", f"s:deleted:{code}")
    return render_template("legal.html", page="deletion", code=code, done=done)


# ---------- ReplyInbox login: Google or a 6-digit email code (users.py) ----------

def invite_ok(code):
    return SIGNUPS != "invite" or str(code or "").strip().upper() in INVITE_CODES


def start_session(user):
    """Signs the user in and picks their first Instagram account; returns where to go next."""
    keep = {k: session[k] for k in ("ref", "next") if k in session}
    session.clear()
    session.update(keep)
    session.permanent = True
    session["user"] = user["id"]
    session["sid"] = devices.start(user["id"], *client_info())
    first = next(iter(users.accounts(user)), None)
    if first:
        session["uid"] = first["id"]
        return session.pop("next", None) or url_for("dashboard")
    if session.get("next") == "/app/billing":  # buying a plan works before Instagram is connected
        return session.pop("next")
    return url_for("connect_page")


def client_info():
    """(user agent, ip, city, country) of this request, for Settings → Security."""
    from urllib.parse import unquote
    ip = client_ip()
    return (request.headers.get("User-Agent", ""), ip, unquote(request.headers.get("x-vercel-ip-city", "")),
            request.headers.get("x-vercel-ip-country", ""))


def new_user_allowed(email):
    """Invite-only mode: a new email needs the invite code entered on the sign-in page."""
    return users.by_email(email) is not None or invite_ok(session.get("invite"))


@app.get("/signin")
def signin_page():
    nxt = request.args.get("next", "")
    nxt = nxt if nxt.startswith("/app/") and "//" not in nxt and "\\" not in nxt else ""  # only our own dashboard pages
    if current_user():
        return redirect(nxt or url_for("dashboard"))
    if request.args.get("invite"):
        session["invite"] = request.args["invite"].strip().upper()
    if nxt:
        session["next"] = nxt
    return render_template("signin.html", google=users.google_ready(), email=users.email_ready(), review=users.review_ready(),
                           invite_only=SIGNUPS == "invite",
                           error=request.args.get("error", ""))


@app.post("/auth/email/start")
def auth_email_start():
    if not request.is_json:  # a cross-site form can't send JSON without CORS
        return jsonify(error="JSON required"), 415
    data = request.get_json(force=True)
    if data.get("invite"):
        session["invite"] = str(data["invite"]).strip().upper()
    try:
        email = users.clean_email(data.get("email"))
        if not new_user_allowed(email):
            return jsonify(error="Sign-ups are invite-only right now. Enter your invite code."), 403
        users.start_email(email, client_ip())
    except users.LoginError as e:
        return jsonify(error=str(e)), 400
    return jsonify(ok=True, email=email)


@app.post("/auth/email/verify")
def auth_email_verify():
    if not request.is_json:
        return jsonify(error="JSON required"), 415
    data = request.get_json(force=True)
    try:
        email = users.verify_email(data.get("email"), data.get("code"))
        if not new_user_allowed(email):
            return jsonify(error="Sign-ups are invite-only right now."), 403
        user = users.login_email(email, invite=session.get("invite", ""))
    except users.LoginError as e:
        return jsonify(error=str(e)), 400
    return jsonify(ok=True, next=start_session(user))


@app.post("/auth/password")
def auth_password():
    """Password sign-in for the one reviewer account (REVIEW_EMAIL / REVIEW_PASSWORD)."""
    if not request.is_json:
        return jsonify(error="JSON required"), 415
    d = request.get_json(force=True)
    try:
        user = users.review_login(d.get("email"), d.get("password"),
                                  client_ip())
    except users.LoginError as e:
        return jsonify(error=str(e)), 400
    session["next"] = "/app/billing"  # reviewers come to see the checkout
    return jsonify(ok=True, next=start_session(user))


def google_redirect_uri():
    return base_url() + "/auth/google/callback"


@app.get("/auth/google")
def auth_google():
    if not users.google_ready():
        return redirect(url_for("signin_page", error="Google sign-in isn't switched on yet. Use your email."))
    session["g_state"] = state = secrets.token_urlsafe(24)
    return redirect(users.google_url(google_redirect_uri(), state))


@app.get("/auth/google/callback")
def auth_google_callback():
    state = session.pop("g_state", None)
    if request.args.get("error"):
        return redirect(url_for("signin_page", error="Google sign-in was cancelled."))
    if not state or not hmac.compare_digest(state, request.args.get("state", "")):
        return redirect(url_for("signin_page", error="That sign-in link expired. Try again."))
    try:
        info = users.google_finish(request.args.get("code", ""), google_redirect_uri())
        email = users.clean_email(info.get("email"))
        if not new_user_allowed(email) and not store.redis("GET", f"s:ugoogle:{info.get('sub', '')}"):
            return redirect(url_for("signin_page", error="Sign-ups are invite-only right now. Enter your invite code first."))
        user = users.login_google(info, invite=session.get("invite", ""))
    except users.LoginError as e:
        return redirect(url_for("signin_page", error=str(e)))
    return redirect(start_session(user))


@app.get("/connect")
def connect_page():
    """Step 2 after signing up (and the place to add more): connect an Instagram account."""
    user = current_user()
    if not user:
        return redirect(url_for("signin_page"))
    accs = [{**a, "pic": avatar_url(a)} for a in users.accounts(user)]
    return render_template("connect.html", user=user, accounts=accs, limit=users.limit(user), locks=plans.LOCKS_ON,
                           error=request.args.get("error", ""), ready=bool(IG_APP_ID))


# ---------- Connect an Instagram account (Instagram business login) ----------

@app.get("/login")
def login():
    """Starts Instagram login to connect (or reconnect) an account to the signed-in user."""
    user = current_user()
    if not user:
        return redirect(url_for("signin_page"))
    if not IG_APP_ID:
        return redirect(url_for("connect_page", error="Instagram connect isn't set up yet. Please try again later."))
    session["oauth_state"] = state = secrets.token_urlsafe(24)
    return redirect("https://www.instagram.com/oauth/authorize?" + urlencode({
        "enable_fb_login": 0, "force_reauth": "true", "client_id": IG_APP_ID,
        "redirect_uri": base_url() + "/auth/callback", "response_type": "code",
        "scope": SCOPES, "state": state}))


def exchange_code(code):
    r = requests.post("https://api.instagram.com/oauth/access_token", timeout=20, data={
        "client_id": IG_APP_ID, "client_secret": IG_APP_SECRET, "grant_type": "authorization_code",
        "redirect_uri": base_url() + "/auth/callback", "code": code})
    r.raise_for_status()
    data = r.json()
    short = (data.get("data") or [data])[0]["access_token"]  # newer API versions wrap it in "data"
    r = requests.get("https://graph.instagram.com/access_token", timeout=20, params={
        "grant_type": "ig_exchange_token", "client_secret": IG_APP_SECRET, "access_token": short})
    r.raise_for_status()
    return r.json()["access_token"]  # long-lived: 60 days, renewed by the daily cron


@app.get("/auth/callback")
def auth_callback():
    user = current_user()
    if not user:
        return redirect(url_for("signin_page"))
    if request.args.get("error") or not request.args.get("code"):
        return redirect(url_for("connect_page", error="Instagram login was cancelled. Try again whenever you're ready."))
    expected = session.pop("oauth_state", None)
    if not expected or not hmac.compare_digest(str(expected), request.args.get("state", "")):
        return redirect(url_for("connect_page", error="That Instagram login expired. Try again."))
    try:
        token = exchange_code(request.args["code"])
        r = requests.get(f"{engine.GRAPH}/me", timeout=20, params={
            "access_token": token,
            "fields": "id,user_id,username,name,profile_picture_url,followers_count,account_type"})
        r.raise_for_status()
        me = r.json()
    except Exception as e:
        app.logger.warning("Instagram login failed: %s", e)
        return redirect(url_for("connect_page", error="Instagram login didn't finish. Your account must be a Business or Creator account."))

    ig_id = str(me["user_id"])  # the ID Instagram puts in webhooks ("entry.id")
    existing = store.load_account(ig_id)
    try:
        users.check_can_add(user, existing, ig_id)
    except users.LoginError as e:
        return redirect(url_for("connect_page", error=str(e)))
    acc = existing or {"id": ig_id, "created": int(time.time()), "paused": False}
    acc.update(asid=str(me.get("id", "")), username=me.get("username", ""), name=me.get("name", ""),
               pic=me.get("profile_picture_url", ""), followers=me.get("followers_count"),
               token=token, token_at=int(time.time()), invite=acc.get("invite") or user.get("invite", ""))
    if not existing:  # a login's first Instagram account counts as a referral sign-up
        referrals.record_signup(user, session.pop("ref", ""), acc.get("username", ""))
    users.claim(user, acc)  # saves the account with its owner and the user's plan
    store.redis("DEL", store.account_key(ig_id, "token_dead"))
    try:  # without this subscription Instagram sends no comment/DM events for the account
        try:
            engine.Instagram(acc).post("me/subscribed_apps", subscribed_fields=LIVE_FIELDS)
        except RuntimeError:
            engine.Instagram(acc).post("me/subscribed_apps", subscribed_fields=WEBHOOK_FIELDS)
    except Exception as e:
        store.log_activity(ig_id, "", "", "", "connect", "error",
                           f"Couldn't turn on comment and DM events: {e}")
    session.pop("member", None)
    session["uid"] = ig_id
    return redirect(session.pop("next", None) or url_for("dashboard"))


# ---------- profile pictures ----------

AVATAR_CHECK = 6 * 3600  # how long a picture link that worked is trusted before checking it again


@app.get("/avatar/<ig_id>")
def avatar(ig_id):
    """Redirects to the account's Instagram picture, asking Instagram for a new link when the saved one has expired."""
    acc = store.load_account(ig_id) if re.fullmatch(r"\d{1,25}", ig_id or "") else None
    if not acc or not acc.get("pic"):
        abort(404)
    ok_key = store.account_key(ig_id, "pic_ok")
    url = acc["pic"]
    if not store.redis("GET", ok_key):
        try:
            alive = requests.head(url, timeout=5, allow_redirects=True).status_code == 200
        except requests.RequestException:
            alive = False
        if not alive:
            try:
                fresh = engine.Instagram(acc).get("me", fields="profile_picture_url").get("profile_picture_url")
            except Exception:
                fresh = ""
            if not fresh:
                abort(404)
            url = acc["pic"] = fresh
            store.save_account(acc)
        store.redis("SET", ok_key, "1", "EX", AVATAR_CHECK)
    resp = redirect(url)
    resp.headers["Cache-Control"] = "public, max-age=3600"
    return resp


# ---------- several Instagram accounts in one login ----------

def linked_accounts():
    """The signed-in user's Instagram accounts (for the account switcher)."""
    return [{"id": a["id"], "username": a.get("username", ""), "pic": avatar_url(a)}
            for a in users.accounts(current_user())] if current_user() else []


@app.post("/api/switch")
def api_switch():
    target = str(request.get_json(force=True).get("id", ""))
    if session.get("member") or not users.owns(current_user(), target):
        return jsonify(error="That account isn't connected to your login."), 403
    session["uid"] = target
    return jsonify(ok=True)


@app.get("/api/team")
def api_team():
    acc = current_account()
    return jsonify(team=acc.get("team") or [], roles=ROLES)


@app.post("/api/team")
def api_team_invite():
    """Creates a one-time invite link (valid 7 days). Only its SHA-256 is stored."""
    acc = current_account()
    data = request.get_json(force=True)
    name, role = str(data.get("name", "")).strip()[:40], data.get("role")
    if not name or role not in ROLES:
        return jsonify(error="Add their name and pick a role."), 400
    team = acc.setdefault("team", [])
    cap = min(MAX_TEAM, plans.limit(acc, "team"))
    if not cap:
        return locked(acc, "team")
    if len(team) >= cap:
        return jsonify(error=f"Your plan allows {cap} team member{'s' if cap != 1 else ''}. Upgrade in Plan & billing for more."), 400
    member = {"id": secrets.token_hex(6), "name": name, "role": role, "invited": int(time.time()), "joined": 0}
    token = secrets.token_urlsafe(24)
    store.redis("SET", f"s:join:{hashlib.sha256(token.encode()).hexdigest()}",
                json.dumps({"acc": acc["id"], "member": member["id"]}), "EX", 7 * 86400)
    team.append(member)
    store.save_account(acc)
    return jsonify(member=member, link=f"{base_url()}/join/{token}", team=team)


@app.delete("/api/team/<member_id>")
def api_team_remove(member_id):
    acc = current_account()
    acc["team"] = [m for m in acc.get("team") or [] if m["id"] != member_id]
    store.save_account(acc)
    return jsonify(team=acc["team"])


@app.route("/join/<token>", methods=["GET", "POST"])
def join_team(token):
    """GET shows who invited them (link previews don't use up the invite); POST joins."""
    key = f"s:join:{hashlib.sha256(token.encode()).hexdigest()}"
    raw = store.redis("GET", key)
    invite = json.loads(raw) if raw else None
    acc = store.load_account(invite["acc"]) if invite else None
    member = team_member(acc, invite["member"]) if acc else None
    if not member:
        return render_template("join.html", error="This invite link has expired or was already used. Ask for a new one."), 404
    if request.method == "GET":
        return render_template("join.html", owner=acc.get("username", ""), member=member, role=ROLES[member["role"]])
    if not store.redis("DEL", key):
        return render_template("join.html", error="This invite link was already used."), 404
    member["joined"] = int(time.time())
    store.save_account(acc)
    session.clear()
    session.permanent = True
    session.update(uid=acc["id"], member=member["id"])
    return redirect(url_for("dashboard"))


@app.post("/logout")
def logout():
    if session.get("user") and session.get("sid"):
        devices.end(session["user"], session["sid"])
    session.clear()
    return redirect(url_for("landing"))


def remove_account(acc):
    """Disconnects an Instagram account: stops its webhooks, revokes YouTube, unlinks it from its login, deletes its data."""
    try:  # stop Instagram sending this account's events; best effort
        requests.delete(f"{engine.GRAPH}/me/subscribed_apps", params={"access_token": acc.get("token", "")}, timeout=10)
    except Exception:
        pass
    try:
        youtube.disconnect(acc)  # revokes Google access too
    except Exception:
        pass
    try:
        files.delete_all(acc)
    except Exception:
        pass
    users.remove(users.owner_of(acc), acc["id"])
    store.delete_account(acc["id"])


@app.post("/api/disconnect")
def api_disconnect():
    """Removes the current Instagram account (and its data) from the user's login."""
    acc = current_account()
    if demo.is_demo(acc):
        session.clear()
        return jsonify(ok=True)
    remove_account(acc)
    user = current_user()
    others = users.accounts(user)
    session.pop("uid", None)
    if others:
        session["uid"] = others[0]["id"]
    return jsonify(ok=True, switched=bool(others), next="/app" if others else "/connect")


# ---------- dashboard API ----------

@app.get("/api/security")
def api_security():
    """Settings → Security: everywhere this login is signed in."""
    u = current_user()
    if not u:
        return jsonify(devices=[])
    return jsonify(devices=[{"sid": d["sid"], "name": devices.label(d.get("ua")), "city": d.get("city", ""), "country": d.get("country", ""),
                             "ip": d.get("ip", ""), "created": d.get("created"), "seen": d.get("seen"),
                             "this": d["sid"] == session.get("sid")} for d in devices.all_of(u["id"])])


@app.post("/api/security/signout")
def api_security_signout():
    u = current_user()
    d = request.get_json(force=True) or {}
    if not u:
        return jsonify(error="Please log in again."), 401
    if d.get("all"):
        return jsonify(ended=devices.end_others(u["id"], session.get("sid")))
    sid = str(d.get("sid", ""))
    if sid == session.get("sid"):
        return jsonify(error="Use Log out to sign out of this device."), 400
    devices.end(u["id"], sid)
    return jsonify(ended=1)


@app.post("/api/feedback")
def api_feedback():
    """Feature requests and help messages from the account menu: kept for the owner page and emailed to support."""
    acc, u = current_account(), current_user()
    d = request.get_json(force=True) or {}
    text = str(d.get("text", "")).strip()[:3000]
    kind = "help" if d.get("kind") == "help" else "feature"
    if len(text) < 5:
        return jsonify(error="Write a few words first."), 400
    k = f"s:fbrate:{(u or {}).get('id') or acc['id']}:{int(time.time() // 3600)}"
    if (store.redis("INCR", k) or 0) > 5:
        return jsonify(error="That's a lot of messages. Try again in an hour."), 429
    store.redis("EXPIRE", k, 3600)
    item = {"at": int(time.time()), "kind": kind, "text": text, "email": (u or {}).get("email", ""), "username": acc.get("username", "")}
    store.redis("LPUSH", "s:feedback", json.dumps(item))
    store.redis("LTRIM", "s:feedback", 0, 499)
    to = os.environ.get("SUPPORT_EMAIL", "").strip()
    if to:
        shop._mail(to, f"{'Help request' if kind == 'help' else 'Feature request'} from @{item['username'] or item['email']}",
                   f"<p style=\"white-space:pre-line\">{shop._esc(text)}</p><p>{shop._esc(item['email'])} · @{shop._esc(item['username'])}</p>",
                   reply_to=item["email"] or None)
    return jsonify(ok=True)


@app.get("/api/me")
def api_me():
    acc = current_account()
    c = store.counts(acc["id"])
    return jsonify(account=public_account(acc), blocked=engine.is_blocked(acc),
                   dms_this_month=c.get(f"dms:{engine.month()}", 0), dm_limit=engine.monthly_limit(acc),
                   totals={k: c.get(k, 0) for k in ("dms", "links_sent", "comment_replies", "gate_follows", "ai_replies")},
                   inbox_waiting=sum(t.get("status") == "needs_you" for t in ai_agent.threads(acc["id"])),
                   billing=billing_banner())


def billing_banner():
    """Plan ending soon / ended, for the owner's banner."""
    user = current_user()
    if not user or session.get("member"):
        return None
    st = billing.status(user)
    if st["expired"]:
        return {"kind": "expired", "plan": plans.PLANS[st["set_plan"]]["name"]}
    if billing.renewal_due(user):
        return {"kind": "soon", "plan": st["plan_name"], "days": st["days_left"]}
    return None


# ---------- plan billing (Razorpay, see billing.py) ----------

@app.get("/app/billing")
def billing_page():
    return render_app("billing.html", "billing", test_mode=billing.test_mode())


def billing_user():
    user = current_user()
    if not user or session.get("member"):
        return None
    return user


@app.get("/api/billing")
def api_billing():
    user = billing_user()
    if not user:
        return jsonify(error="Only the account owner can see billing."), 403
    st = billing.status(user)
    st["quotes"] = {p: {per: billing.quote(user, p, per) for per in billing.DAYS} for p in plans.PAID}
    return jsonify(st)


@app.post("/api/billing/order")
def api_billing_order():
    user = billing_user()
    if not user:
        return jsonify(error="Only the account owner can pay."), 403
    d = request.get_json(force=True)
    try:
        return jsonify(billing.create_order(user, d.get("plan"), d.get("period")))
    except billing.BillingError as e:
        return jsonify(error=str(e)), 400


@app.post("/api/billing/verify")
def api_billing_verify():
    user = billing_user()
    if not user:
        return jsonify(error="Only the account owner can pay."), 403
    d = request.get_json(force=True)
    try:
        order = billing.verify_checkout(user, d.get("order_id"), d.get("payment_id"), d.get("signature"))
    except billing.BillingError as e:
        return jsonify(error=str(e)), 400
    if current_account():
        store.log_activity(current_account()["id"], "", "", "", "billing", "ok",
                           f"{plans.PLANS[order['plan']]['name']} plan paid (₹{order['amount']})")
    return jsonify(ok=True, order=order["id"], **billing.status(users.get(user["id"])))


@app.post("/billing/webhook")
def billing_webhook():
    """Razorpay → us (set this URL and RAZORPAY_WEBHOOK_SECRET in Razorpay → Webhooks; events payment.captured, order.paid)."""
    ok = billing.handle_webhook(request.get_data(), request.headers.get("X-Razorpay-Signature", ""))
    return ("", 200) if ok else ("bad signature", 400)


@app.get("/app/billing/receipt/<order_id>")
def billing_receipt(order_id):
    user = billing_user()
    r = billing.receipt(user, order_id) if user else None
    if not r:
        abort(404)
    return render_template("receipt.html", r=r)


@app.get("/api/reels")
def api_reels():
    acc = current_account()
    key = store.account_key(acc["id"], "stats")
    cached = store.get_json(key)
    if cached and not request.args.get("fresh"):
        return jsonify(cached)
    try:
        ig = engine.Instagram(acc)
        me = ig.get("me", fields="username,profile_picture_url,followers_count,media_count")
        media = ig.get("me/media", limit=24, fields=(
            "id,caption,media_type,media_product_type,permalink,thumbnail_url,media_url,"
            "timestamp,like_count,comments_count"))["data"]
    except Exception as e:
        if cached:
            return jsonify({**cached, "warning": str(e)})
        return jsonify(error=str(e), reels=[]), 502
    acc.update(followers=me.get("followers_count"), pic=me.get("profile_picture_url", acc.get("pic")))
    store.save_account(acc)
    created = [m["id"] for m in media if engine.auto_setup(acc, m)]  # new reels whose caption asks for a keyword
    data = {"followers": me.get("followers_count"), "media_count": me.get("media_count"),
            "reels": media, "fetched_at": int(time.time()), "auto_created": created}
    store.redis("SET", key, json.dumps(data), "EX", REELS_CACHE_SECONDS)
    return jsonify(data)


# ---------- auto-setup ----------

def ig_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000")  # Instagram's timestamp format


@app.get("/api/auto-setup")
def api_get_auto_setup():
    acc = current_account()
    return jsonify(settings=engine.auto_settings(acc), recent=store.recent_autos(acc["id"]))


@app.put("/api/auto-setup")
def api_put_auto_setup():
    acc = current_account()
    data = request.get_json(force=True)
    t = data.get("template") or {}
    template = {
        "comment_reply": str(t.get("comment_reply", ""))[:1000].strip(),
        "opening_dm": str(t.get("opening_dm", ""))[:640].strip(),
        "button_text": str(t.get("button_text", ""))[:20].strip(),
        "require_follow": bool(t.get("require_follow")),
        "follow_dm": str(t.get("follow_dm", ""))[:640].strip(),
        "followed_button_text": str(t.get("followed_button_text", ""))[:20].strip(),
        "dm": str(t.get("dm", ""))[:1000].strip(),
    }
    enabled = bool(data.get("enabled"))
    if enabled and not template["dm"]:
        return jsonify(error="Add the final DM first. Use {keyword} for the word from the caption."), 400
    old = engine.auto_settings(acc)
    # Turning it on starts the clock: only reels posted from now on are set up automatically.
    since = old.get("since") if old.get("enabled") and enabled else (ig_now() if enabled else "")
    acc["auto_setup"] = {"enabled": enabled, "since": since, "template": template}
    store.save_account(acc)
    return jsonify(settings=acc["auto_setup"])


@app.post("/api/auto-setup/<media_id>/undo")
def api_undo_auto_setup(media_id):
    acc = current_account()
    rules = store.load_rules(acc["id"])
    rule = rules.get("reels", {}).get(media_id)
    if rule and rule.get("auto"):
        rules["reels"].pop(media_id)
        store.save_rules(acc["id"], rules)
    events = store.recent_autos(acc["id"])
    for e in events:
        if e.get("media_id") == media_id:
            e["undone"] = True
    store.redis("DEL", store.account_key(acc["id"], "autos"))
    for e in reversed(events):
        store.log_auto(acc["id"], e)
    return jsonify(rules)


# ---------- reel report ----------

def reel_views(ig, media_id):
    try:
        data = ig.get(f"{media_id}/insights", metric="views,reach,saved,shares")["data"]
        return {i["name"]: i["values"][0]["value"] for i in data}
    except Exception:
        return {}


@app.get("/api/report")
def api_report():
    try:
        return jsonify(build_report(current_account(), bool(request.args.get("fresh"))))
    except RuntimeError as e:
        return jsonify(error=str(e), reels=[]), 502


def build_report(acc, fresh=False):
    key = store.account_key(acc["id"], "report")
    cached = store.get_json(key)
    if cached and not fresh:
        return cached
    try:
        ig = engine.Instagram(acc)
        media = ig.get("me/media", limit=30, fields=(
            "id,caption,media_product_type,permalink,thumbnail_url,media_url,timestamp,comments_count,like_count"))["data"]
    except Exception as e:
        if cached:
            return {**cached, "warning": str(e)}
        raise RuntimeError(str(e))
    reels = [m for m in media if m.get("media_product_type") == "REELS"][:REPORT_REELS]
    with ThreadPoolExecutor(max_workers=6) as pool:
        insights = list(pool.map(lambda m: reel_views(ig, m["id"]), reels))
    rules = store.load_rules(acc["id"]).get("reels", {})
    rows = []
    for m, ins in zip(reels, insights):
        c = store.media_counts(acc["id"], m["id"])
        rule = rules.get(m["id"])
        views = ins.get("views") or 0
        rows.append({
            "id": m["id"], "caption": (m.get("caption") or "").strip().split("\n")[0][:140],
            "thumb": m.get("thumbnail_url") or m.get("media_url", ""), "permalink": m.get("permalink", ""),
            "timestamp": m.get("timestamp", ""), "views": views, "reach": ins.get("reach"),
            "saves": ins.get("saved"), "shares": ins.get("shares"), "comments": m.get("comments_count") or 0,
            "keyword": c.get("keyword", 0), "dm": c.get("dm", 0), "link": c.get("link", 0), "follow": c.get("follow", 0),
            "has_rule": bool(rule and rule.get("enabled", True)), "auto": bool(rule and rule.get("auto")),
            "keywords": (rule or {}).get("keywords", []), "require_follow": bool((rule or {}).get("require_follow")),
            "per_1k": round(c.get("follow", 0) / views * 1000, 1) if views else None,
        })
    rated = [r["per_1k"] for r in rows if r["has_rule"] and r["per_1k"] is not None and r["views"] >= 1000]
    avg = round(sum(rated) / len(rated), 1) if rated else None
    ranked = sorted((r for r in rows if r["per_1k"] is not None), key=lambda r: -r["per_1k"])
    for r in rows:
        r["tips"] = engine.reel_tips(r, avg)
        r["rank"] = next((i + 1 for i, x in enumerate(ranked) if x["id"] == r["id"]), None)
    data = {"reels": rows, "avg_per_1k": avg, "ranked_count": len(ranked), "steps": engine.REPORT_STEPS,
            "fetched_at": int(time.time())}
    store.redis("SET", key, json.dumps(data), "EX", REPORT_CACHE_SECONDS)
    return data


@app.get("/app/report")
def report_page():
    return render_app("report.html", "report")


@app.get("/report")
def old_report_page():
    return redirect(url_for("report_page"))


@app.get("/api/rules")
def api_rules():
    acc = current_account()
    rules = store.load_rules(acc["id"])
    return jsonify({**rules, "stats": store.rule_stats(acc["id"], rules.get("reels", {}).keys())})


@app.get("/api/autodm-summary")
def api_autodm_summary():
    """Totals and a 14-day series for the Auto DM page's cards."""
    acc = current_account()
    c = store.counts(acc["id"])
    rows = store.days(acc["id"], 14)
    series = lambda *fields: [sum(int(d.get(f, 0)) for f in fields) for _, d in rows]
    return jsonify(dms=c.get("dms", 0), leads=c.get("emails", 0) + c.get("phones", 0) + c.get("page_signups", 0),
                   follows=c.get("gate_follows", 0), daily={"dms": series("dms"), "leads": series("emails", "phones", "page_signups"),
                                                         "follows": series("gate_follows")})


def valid_rule_key(key):
    return key in ("*", "next", "live") or key.isdigit() or key in engine.STORY_KEYS or (engine.is_keyword_rule(key) and key[3:].replace("_", "").isalnum())


@app.put("/api/rules/<key>")
def api_put_rule(key):
    try:
        return jsonify(save_rule(current_account(), key, request.get_json(force=True)))
    except ValueError as e:
        return jsonify(error=str(e)), 400


def as_time(value):
    """Unix seconds from the form (0 = no limit)."""
    try:
        return max(int(float(value or 0)), 0)
    except (TypeError, ValueError):
        return 0


def save_rule(acc, key, data):
    """Creates or replaces one rule (reel id, "kw:WORD" or "*"); returns all rules. Raises ValueError on bad input."""
    if not valid_rule_key(key):
        raise ValueError("Bad rule id")
    rule = {
        "enabled": bool(data.get("enabled", True)),
        "keywords": [k.strip()[:40] for k in data.get("keywords", []) if k.strip()][:20],
        "comment_reply": str(data.get("comment_reply", ""))[:1000].strip(),
        "opening_dm": str(data.get("opening_dm", ""))[:640].strip(),
        "opening_dm_b": str(data.get("opening_dm_b", ""))[:640].strip(),
        "button_text": str(data.get("button_text", ""))[:20].strip(),
        "require_follow": bool(data.get("require_follow")),
        "follow_dm": str(data.get("follow_dm", ""))[:640].strip(),
        "followed_button_text": str(data.get("followed_button_text", ""))[:20].strip(),
        "dm": str(data.get("dm", ""))[:1000].strip(),
        "dm_button_text": str(data.get("dm_button_text", ""))[:20].strip(),
        "dm_button_url": safe_url(data.get("dm_button_url")),
        "dm_buttons_more": [{"text": str(b.get("text", "")).strip()[:20], "url": safe_url(b.get("url"))}
                            for b in (data.get("dm_buttons_more") or [])[:2] if isinstance(b, dict) and str(b.get("url", "")).strip()],
        "replies_on": data.get("replies_on", True) is not False,
        "exclude": [k.strip()[:40] for k in data.get("exclude", []) if str(k).strip()][:20],
        "menu": [{"title": str(m.get("title", "")).strip()[:20], "text": str(m.get("text", "")).strip()[:640],
                  "url": safe_url(m.get("url")), "button": str(m.get("button", "")).strip()[:20]}
                 for m in [m for m in (data.get("menu") or []) if isinstance(m, dict) and str(m.get("title", "")).strip()][:3]],
        "track_links": data.get("track_links", True) is not False,
        "once_per_person": bool(data.get("once_per_person")),
        "delay_min": int(data.get("delay_min") or 0) if int(data.get("delay_min") or 0) in engine.DELAYS else 0,
        "since": str(data.get("since", "")) if key == "next" else "",
        "tags": ", ".join(store.clean_tags(str(data.get("tags", "")).split(","))[:5]),
        "ask_email": bool(data.get("ask_email")),
        "followup_on": bool(data.get("followup_on")),
        "followup_hours": int(data.get("followup_hours") or 3) if str(data.get("followup_hours") or 3).isdigit() else 3,
        "followup_dm": str(data.get("followup_dm", ""))[:640].strip(),
        "followup_button": str(data.get("followup_button", ""))[:20].strip(),
        "followup_url": safe_url(data.get("followup_url")),
        "email_dm": str(data.get("email_dm", ""))[:640].strip(),
        "email_required": bool(data.get("email_required")),
        "ask_phone": bool(data.get("ask_phone")),
        "phone_dm": str(data.get("phone_dm", ""))[:640].strip(),
        "phone_required": bool(data.get("phone_required")),
        "comments": bool(data.get("comments", True)),
        "starts_at": as_time(data.get("starts_at")),
        "ends_at": as_time(data.get("ends_at")),
        "label": str(data.get("label", ""))[:120],
    }
    if rule["enabled"] and not rule["dm"]:
        raise ValueError("Add the final DM (your message and link) before turning the rule on.")
    if key == "next" and not rule["since"]:
        rule["since"] = (store.load_rules(acc["id"]).get("reels", {}).get("next") or {}).get("since") or ig_now()
    if data.get("dm_button_url") and not rule["dm_button_url"]:
        raise ValueError("The button link must start with https://")
    if any(not b["url"] for b in rule["dm_buttons_more"]):
        raise ValueError("Every button link must start with https://")
    if not rule["dm_button_url"] or rule["menu"]:
        rule["dm_buttons_more"] = []  # extra buttons only go with the first link button
    if rule["starts_at"] and rule["ends_at"] and rule["ends_at"] <= rule["starts_at"]:
        raise ValueError("The end time must be after the start time.")
    if rule["followup_on"] and not rule["followup_dm"]:
        raise ValueError("Write the follow-up message, or turn the follow-up off.")
    if data.get("followup_url") and not rule["followup_url"]:
        raise ValueError("The follow-up link must start with https://")
    if engine.is_keyword_rule(key) and not rule["keywords"]:
        rule["keywords"] = [key[3:]]
    rules = store.load_rules(acc["id"])
    before = rules.get("reels", {}).get(key) or {}
    if (before.get("opening_dm"), before.get("opening_dm_b")) != (rule["opening_dm"], rule["opening_dm_b"]):
        store.redis("DEL", engine.ab_key(acc, key))  # new messages: a fresh test
    rules.setdefault("reels", {})[key] = rule
    store.save_rules(acc["id"], rules)
    return rules


@app.post("/api/rules/<key>/copy")
def api_copy_rule(key):
    """Copies one automation to other reels and / or new keywords. Existing automations are kept unless "replace" is set."""
    acc = current_account()
    data = request.get_json(force=True)
    try:
        done, skipped = copy_rule(acc, key, data.get("targets") or [], bool(data.get("replace")))
    except LookupError:
        return jsonify(error="Automation not found."), 404
    except ValueError as e:
        return jsonify(error=str(e)), 400
    return jsonify(copied=done, skipped=skipped, rules=store.load_rules(acc["id"]))


def copy_rule(acc, key, targets, replace=False):
    """Copies an automation to other rule ids; returns (copied, skipped). LookupError if the source is missing."""
    source = store.load_rules(acc["id"]).get("reels", {}).get(key)
    if not source:
        raise LookupError(key)
    targets = [str(t) for t in targets][:50]
    done, skipped = [], []
    for target in targets:
        if target == key or not valid_rule_key(target):
            continue
        if target in store.load_rules(acc["id"]).get("reels", {}) and not replace:
            skipped.append(target)
            continue
        copy = {k: v for k, v in source.items() if k not in ("auto", "label")}
        if engine.is_keyword_rule(target):
            copy["keywords"] = [target[3:]]
        save_rule(acc, target, copy)
        done.append(target)
    return done, skipped


@app.delete("/api/rules/<key>")
def api_delete_rule(key):
    return jsonify(delete_rule(current_account(), key))


def delete_rule(acc, key):
    rules = store.load_rules(acc["id"])
    rules.get("reels", {}).pop(key, None)
    store.save_rules(acc["id"], rules)
    store.redis("DEL", *[store.account_key(acc["id"], f"{p}:{key}") for p in ("rs", "rsd", "rsh", "ab")])
    return rules


@app.post("/api/reels/<media_id>/past-comments")
def api_past_comments(media_id):
    """Sends the reel's automation to comments from the last 7 days that came before it was set up."""
    if not media_id.isdigit():
        return jsonify(error="Bad reel id"), 400
    try:
        return jsonify(engine.backfill_comments(current_account(), media_id))
    except RuntimeError as e:
        return jsonify(error=str(e)[:300]), 400


@app.get("/api/retry")
def api_retry_count():
    return jsonify(waiting=len(engine.pending_retries(current_account())))


@app.post("/api/retry")
def api_retry():
    acc = current_account()
    return jsonify(**engine.retry_failed_dms(acc), waiting=len(engine.pending_retries(acc)))


@app.get("/api/ice")
def api_get_ice():
    return jsonify(engine.ice_settings(current_account()))


@app.put("/api/ice")
def api_put_ice():
    """Saves the chat menu and puts it on Instagram."""
    acc = current_account()
    data = request.get_json(force=True)
    rules = store.load_rules(acc["id"]).get("reels", {})
    items = []
    for it in (data.get("items") or [])[:engine.MAX_ICE]:
        question = str(it.get("question", "")).strip()[:80]
        rule = str(it.get("rule", "")) if str(it.get("rule", "")) in rules else ""
        answer = str(it.get("answer", "")).strip()[:1000]
        if not question:
            continue
        if not rule and not answer:
            return jsonify(error=f'Write an answer for "{question}" or pick an automation.'), 400
        items.append({"question": question, "answer": answer, "rule": rule})
    old = acc.get("ice")
    acc["ice"] = {"enabled": bool(data.get("enabled")) and bool(items), "items": items}
    try:
        engine.publish_ice(acc)
    except RuntimeError as e:
        acc["ice"] = old
        return jsonify(error=f"Instagram didn't accept the chat menu: {str(e)[:200]}"), 502
    store.save_account(acc)
    return jsonify(engine.ice_settings(acc))


@app.get("/api/guard")
def api_get_guard():
    acc = current_account()
    hidden = [a for a in store.recent_activity(acc["id"]) if a["action"] == "comment_hidden"]
    return jsonify(**engine.guard_settings(acc), hidden=hidden[:20], total=store.counts(acc["id"]).get("hidden_comments", 0))


@app.put("/api/guard")
def api_put_guard():
    acc = current_account()
    data = request.get_json(force=True)
    words = data.get("words", [])
    if isinstance(words, str):
        words = re.split(r"[,\n]", words)
    acc["guard"] = {"enabled": bool(data.get("enabled")), "links": bool(data.get("links")),
                    "words": [w.strip()[:40] for w in words if w.strip()][:100]}
    store.save_account(acc)
    return jsonify(engine.guard_settings(acc))


@app.post("/api/guard/test")
def api_guard_test():
    return jsonify(reason=engine.guard_reason(current_account(), str(request.get_json(force=True).get("text", ""))[:500]))


@app.get("/api/giveaway")
def api_giveaways():
    acc = current_account()
    return jsonify(history=[json.loads(x) for x in store.redis("LRANGE", store.account_key(acc["id"], "giveaways"), 0, 9) or []])


@app.post("/api/giveaway")
def api_giveaway():
    acc = current_account()
    data = request.get_json(force=True)
    media_id = str(data.get("media_id", ""))
    if not media_id.isdigit():
        return jsonify(error="Pick a post first."), 400
    try:
        return jsonify(engine.pick_winners(
            acc, media_id, winners=min(int(data.get("winners") or 1), 20), keyword=str(data.get("keyword", "")).strip()[:40],
            min_mentions=min(int(data.get("min_mentions") or 0), 10), followed_only=bool(data.get("followed_only")),
            exclude=[e.strip() for e in str(data.get("exclude", "")).replace("\n", ",").split(",")][:50]))
    except (RuntimeError, ValueError) as e:
        return jsonify(error=f"Couldn't read the comments: {str(e)[:200]}"), 502


@app.post("/api/giveaway/announce")
def api_giveaway_announce():
    """Replies under each winner's comment and DMs them (Instagram allows the DM within 7 days of the comment)."""
    acc = current_account()
    data = request.get_json(force=True)
    reply, message = str(data.get("reply", "")).strip()[:500], str(data.get("dm", "")).strip()[:1000]
    ig, done = engine.Instagram(acc), []
    for w in (data.get("winners") or [])[:20]:
        row = {"username": w.get("username", ""), "reply": None, "dm": None}
        fill = lambda s: s.replace("{username}", row["username"])
        for field, text, send in (("reply", reply, lambda t: ig.reply_to_comment(w["comment_id"], t)),
                                  ("dm", message, lambda t: ig.send_dm({"comment_id": w["comment_id"]}, {"text": t}))):
            if text:
                try:
                    send(fill(text))
                    row[field] = "ok"
                    if field == "dm":
                        engine.note_dm(acc)
                except Exception as e:
                    row[field] = str(e)[:160]
        store.log_activity(acc["id"], "giveaway", row["username"], "", "giveaway_winner", "ok")
        done.append(row)
    return jsonify(results=done)


@app.get("/api/ab")
def api_ab():
    """A/B test numbers for every automation that has a second first-DM version."""
    acc = current_account()
    return jsonify({k: engine.ab_stats(acc, k) for k, r in store.load_rules(acc["id"]).get("reels", {}).items()
                    if r.get("opening_dm_b")})


WEEK_FIELDS = ["dms", "links_sent", "gate_follows", "comment_replies", "emails", "phones", "ai_replies",
               "followups_sent", "story_replies", "hidden_comments"]


@app.get("/api/week")
def api_week():
    """This week (last 7 days) against the 7 days before, and a daily series of DMs and follows."""
    rows = store.days(current_account()["id"], 14)
    total = lambda part, f: sum(int(d.get(f, 0)) for _, d in part)
    return jsonify(this_week={f: total(rows[7:], f) for f in WEEK_FIELDS},
                   last_week={f: total(rows[:7], f) for f in WEEK_FIELDS},
                   daily=[{"date": day, "dms": int(d.get("dms", 0)), "follows": int(d.get("gate_follows", 0))} for day, d in rows])


def onboarding_steps(acc):
    rules = store.load_rules(acc["id"]).get("reels", {})
    page = store.load_page(acc["id"]) or {}
    worked = any(a["status"] == "ok" and a["action"] in ("opening_dm", "dm", "dm_keyword")
                 for a in store.recent_activity(acc["id"]))
    marked = acc.get("onboarding") or {}
    steps = [
        ("connect", "Connect Instagram", "Done when you logged in.", True, ""),
        ("automation", "Create your first automation", "Start from a template, add your link, Save.", bool(rules), "/app/automations"),
        ("test", "Test it", "From another account, comment your keyword on a reel (or DM it). The DM should arrive in seconds.",
         worked, "/app/automations"),
        ("page", "Set up your link in bio", "Add your products and links.", bool(page.get("items")), "/app/links"),
        ("bio", "Put the link in your Instagram bio", "Instagram → Edit profile → Links.", bool(marked.get("bio")), ""),
        ("auto", "Turn on auto-setup", 'New reels whose caption says "Comment WORD" set themselves up.',
         bool(engine.auto_settings(acc).get("enabled")), "/app/settings"),
    ]
    if apps_of(acc).get("inbox"):
        steps.append(("ai", "Teach your AI", "Add your FAQ so it can answer fans' questions.", ai_agent.settings(acc)["enabled"], "/app/inbox"))
    return [{"id": i, "title": t, "hint": h, "done": d, "href": href} for i, t, h, d, href in steps]


@app.get("/api/onboarding")
def api_onboarding():
    acc = current_account()
    steps = onboarding_steps(acc)
    return jsonify(steps=steps, hidden=bool((acc.get("onboarding") or {}).get("dismissed")) or all(s["done"] for s in steps))


@app.post("/api/onboarding")
def api_onboarding_mark():
    """{"done": "bio"} ticks a step only the creator can confirm; {"dismissed": true} hides the checklist."""
    acc = current_account()
    data = request.get_json(force=True)
    marks = acc.setdefault("onboarding", {})
    if data.get("done") == "bio":
        marks["bio"] = True
    if "dismissed" in data:
        marks["dismissed"] = bool(data["dismissed"])
    store.save_account(acc)
    return api_onboarding()


@app.get("/api/integrations")
def api_integrations():
    acc = current_account()
    hook = acc.get("hook") or {}
    return jsonify(url=hook.get("url", ""), enabled=bool(hook.get("enabled")), sent=store.counts(acc["id"]).get("hook_sent", 0))


@app.put("/api/integrations")
def api_put_integrations():
    acc = current_account()
    data = request.get_json(force=True)
    url = str(data.get("url", "")).strip()
    if url and not engine.safe_hook_url(url):
        return jsonify(error="Use an https:// webhook URL that's reachable on the internet."), 400
    acc["hook"] = {"url": url, "enabled": bool(data.get("enabled")) and bool(url)}
    store.save_account(acc)
    return api_integrations()


@app.post("/api/integrations/test")
def api_test_integration():
    acc = current_account()
    err = engine.send_hook(acc, "test", {"username": "test.fan", "email": "test@example.com", "phone": "+919876543210",
                                         "automation": "test"}, test=True)
    return (jsonify(error=err), 400) if err else jsonify(ok=True)


# ---------- welcome message, short links, send to recent chats ----------

COOKIE_DAYS = 30


@app.get("/l/<code>")
def short_link(code):
    url = engine.link_click(code) if re.fullmatch(r"[0-9a-f]{10}", code) else ""
    if not url:
        abort(404)
    # Remember the last DM link this browser tapped, so a sale on the creator's payment page can be credited to it.
    resp = redirect(url)
    resp.set_cookie("ri_l", code, max_age=COOKIE_DAYS * 86400, secure=request.is_secure, httponly=True, samesite="Lax")
    return resp


@app.get("/s/<pid>")
def sale_return(pid):
    """Payment pages redirect here after a successful payment (set as their "redirect URL"). Counts the sale."""
    if not re.fullmatch(r"[0-9a-f]{12}", pid):
        abort(404)
    visitor = request.cookies.get("ri_v") or secrets.token_hex(8)
    order = re.sub(r"[^A-Za-z0-9_-]", "", request.args.get("order") or request.args.get("razorpay_payment_id")
                   or request.args.get("payment_id") or "")[:64]
    acc, prod = engine.record_sale(pid, request.cookies.get("ri_l", ""), visitor, order)
    if not prod:
        abort(404)
    resp = redirect(prod["thanks_url"]) if prod.get("thanks_url") else make_response(render_template(
        "thanks.html", product=prod["name"], creator=acc.get("username", "")))
    resp.set_cookie("ri_v", visitor, max_age=365 * 86400, secure=request.is_secure, httponly=True, samesite="Lax")
    return resp


@app.get("/api/sales")
def api_sales():
    return jsonify(sales_summary(current_account()))


def sales_summary(acc):
    days = store.days(acc["id"], 30)
    keys = list(store.load_rules(acc["id"]).get("reels", {}))
    by_rule = {k: v for k, v in store.rule_stats(acc["id"], keys).items() if v.get("sales")}
    c = store.counts(acc["id"])
    return dict(products=[{**p, "link": f"{base_url()}/s/{p['id']}"} for p in engine.products(acc)],
                sales=c.get("sales", 0), revenue=c.get("revenue", 0), link_clicks=c.get("link_clicks", 0),
                daily=[{"date": d, "sales": v.get("sales", 0), "revenue": v.get("revenue", 0)} for d, v in days],
                recent=[json.loads(x) for x in store.redis("LRANGE", store.account_key(acc["id"], "sales"), 0, 19) or []],
                by_rule={k: {"sales": v.get("sales", 0), "revenue": v.get("revenue", 0), "link_clicks": v.get("link_clicks", 0)}
                         for k, v in by_rule.items()},
                utm=acc.get("utm", True))


@app.post("/api/products")
def api_add_product():
    try:
        add_product(current_account(), request.get_json(force=True))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    return api_sales()


def add_product(acc, data):
    """Adds a product and returns it with its sales link; raises ValueError on bad input."""
    name = str(data.get("name", "")).strip()[:80]
    try:
        price = int(float(str(data.get("price", "0")).replace(",", "").replace("₹", "").strip() or 0))
    except ValueError:
        price = -1
    thanks = str(data.get("thanks_url", "")).strip()
    if not name:
        raise ValueError("Give the product a name.")
    if not 0 <= price <= 1_000_000:
        raise ValueError("Price must be a number in ₹.")
    if thanks and not safe_url(thanks):
        raise ValueError("The thank-you page must start with https://")
    items = engine.products(acc)
    if len(items) >= engine.MAX_PRODUCTS:
        raise ValueError(f"Up to {engine.MAX_PRODUCTS} products.")
    pid = secrets.token_hex(6)
    store.redis("SET", f"s:prod:{pid}", acc["id"])
    prod = {"id": pid, "name": name, "price": price, "thanks_url": safe_url(thanks) if thanks else ""}
    acc["products"] = items + [prod]
    store.save_account(acc)
    return {**prod, "link": f"{base_url()}/s/{pid}"}


@app.delete("/api/products/<pid>")
def api_delete_product(pid):
    acc = current_account()
    acc["products"] = [p for p in engine.products(acc) if p["id"] != pid]
    store.save_account(acc)
    if store.redis("GET", f"s:prod:{pid}") == acc["id"]:
        store.redis("DEL", f"s:prod:{pid}")
    return api_sales()


@app.put("/api/utm")
def api_utm():
    acc = current_account()
    acc["utm"] = bool(request.get_json(force=True).get("on"))
    store.save_account(acc)
    return jsonify(utm=acc["utm"])


@app.get("/api/rules/<key>/insights")
def api_rule_insights(key):
    data = rule_insights(current_account(), key)
    return jsonify(data) if data else (jsonify(error="Automation not found"), 404)


def rule_insights(acc, key):
    """30 days of one automation's numbers, its busiest hours and how its menu options were picked (None if unknown)."""
    rule = store.load_rules(acc["id"]).get("reels", {}).get(key)
    if not rule:
        return None
    fields = ("runs", "clicks", "link_clicks", "follows", "leads", "sales", "revenue")
    daily = [{"date": d, **{f: v.get(f, 0) for f in fields}} for d, v in store.rule_daily(acc["id"], key, 30)]
    total = store.rule_stats(acc["id"], [key])[key]
    hours = store.rule_hours(acc["id"], key)
    best = sorted(range(24), key=lambda h: -hours[h])[:3] if any(hours) else []
    menu = [{"title": m.get("title", ""), "picked": total.get(f"menu_{i}", 0)} for i, m in enumerate(rule.get("menu") or [])]
    return dict(daily=daily, total={f: total.get(f, 0) for f in fields}, hours=hours, best_hours=best, menu=menu,
                last30={f: sum(d[f] for d in daily) for f in fields})


@app.get("/api/welcome")
def api_welcome():
    return jsonify(engine.welcome_settings(current_account()))


@app.put("/api/welcome")
def api_put_welcome():
    try:
        return jsonify(set_welcome(current_account(), request.get_json(force=True)))
    except ValueError as e:
        return jsonify(error=str(e)), 400


def set_welcome(acc, data):
    rules = store.load_rules(acc["id"]).get("reels", {})
    buttons = []
    for b in (data.get("buttons") or [])[:3]:
        title = str(b.get("title", "")).strip()[:20]
        if b.get("type") == "url" and title and safe_url(b.get("value")):
            buttons.append({"type": "url", "title": title, "value": safe_url(b.get("value"))})
        elif b.get("type") == "kw" and title and str(b.get("value")) in rules:
            buttons.append({"type": "kw", "title": title, "value": str(b["value"])})
    text = str(data.get("text", "")).strip()[:640]
    if data.get("enabled") and not text:
        raise ValueError("Write the welcome message first.")
    acc["welcome"] = {"enabled": bool(data.get("enabled")), "text": text, "buttons": buttons}
    store.save_account(acc)
    return engine.welcome_settings(acc)


BROADCAST_BATCH = 40  # messages per request, so one request stays well inside the time limit


@app.get("/api/broadcast")
def api_broadcast_info():
    acc = current_account()
    return jsonify(eligible=len(engine.recent_chats(acc)), history=[json.loads(x) for x in
                   store.redis("LRANGE", store.account_key(acc["id"], "broadcasts"), 0, 9) or []])


@app.post("/api/broadcast")
def api_broadcast():
    """Sends one message to everyone who DMed in the last 24 h. Call again with the same id until done is true."""
    try:
        return jsonify(broadcast_batch(current_account(), request.get_json(force=True)))
    except ValueError as e:
        return jsonify(error=str(e)), 400


def broadcast_batch(acc, data):
    """One batch of a broadcast; raises ValueError for bad input or when the account can't send."""
    text = str(data.get("text", "")).strip()[:640]
    bid = re.sub(r"[^a-z0-9]", "", str(data.get("id", "")).lower())[:16]
    url, button = safe_url(data.get("url")), str(data.get("button", "")).strip()[:20] or "Open"
    if not text or not bid:
        raise ValueError("Write the message first.")
    if data.get("url") and not url:
        raise ValueError("The link must start with https://")
    if engine.is_blocked(acc):
        raise ValueError("Instagram is limiting this account right now. Try again later.")
    if engine.over_limit(acc):
        raise ValueError("This month's DM limit is reached.")
    done_key = store.account_key(acc["id"], f"bc:{bid}")
    already = set(store.redis("SMEMBERS", done_key) or [])
    todo = [i for i in engine.recent_chats(acc) if i not in already]
    ig, sent, failed = engine.Instagram(acc), 0, 0
    for igsid in todo[:BROADCAST_BATCH]:
        if engine.over_limit(acc):
            break
        store.redis("SADD", done_key, igsid)
        try:
            msg = engine.track_text(acc, "broadcast", text)
            if url:
                ig.send_buttons({"id": igsid}, msg, links=[(button, engine.track(acc, "broadcast", url))])
            else:
                ig.send_dm({"id": igsid}, {"text": msg})
            engine.note_dm(acc)
            sent += 1
        except Exception as e:
            failed += 1
            store.log_activity(acc["id"], "broadcast", igsid, text, "broadcast", "error", str(e)[:200])
    store.redis("EXPIRE", done_key, 2 * 86400)
    left = max(len(todo) - sent - failed, 0)
    if not left:
        total = len(store.redis("SMEMBERS", done_key) or [])
        store.redis("LPUSH", store.account_key(acc["id"], "broadcasts"),
                    json.dumps({"id": bid, "text": text[:120], "to": total, "at": int(time.time())}, ensure_ascii=False))
        store.redis("LTRIM", store.account_key(acc["id"], "broadcasts"), 0, 9)
        store.log_activity(acc["id"], "broadcast", "", text, "broadcast", "ok", f"Sent to {total} people")
    return {"sent": sent, "failed": failed, "left": left, "done": not left}


# ---------- notifications and the installable app ----------

@app.get("/api/notifications")
def api_notifications():
    acc = current_account()
    return jsonify(key=push.public_key(), devices=push.devices(acc["id"]), prefs={"handoff": True, "lead": True, "sale": True, "health": True, **(acc.get("notify") or {})})


@app.post("/api/notifications/subscribe")
def api_push_subscribe():
    acc = current_account()
    data = request.get_json(force=True)
    try:
        push.subscribe(acc["id"], str(data.get("endpoint", "")))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    return jsonify(devices=push.devices(acc["id"]))


@app.post("/api/notifications/unsubscribe")
def api_push_unsubscribe():
    acc = current_account()
    push.unsubscribe(acc["id"], str(request.get_json(force=True).get("endpoint", "")))
    return jsonify(devices=push.devices(acc["id"]))


@app.put("/api/notifications/prefs")
def api_push_prefs():
    acc = current_account()
    data = request.get_json(force=True)
    acc["notify"] = {k: bool(data.get(k, True)) for k in ("handoff", "lead", "sale", "health")}
    store.save_account(acc)
    return jsonify(prefs=acc["notify"])


@app.post("/api/notifications/test")
def api_push_test():
    acc = current_account()
    sent = push.notify(acc, "ReplyInbox notifications are on ✅", "You'll hear about new leads and chats that need you.", "/app")
    return jsonify(sent=sent)


@app.get("/api/notifications/latest")
def api_push_latest():
    return jsonify(push.latest(current_account()["id"]) or {"title": BRAND, "body": "Open ReplyInbox", "url": "/app"})


@app.get("/sw.js")
def service_worker():
    return app.send_static_file("sw.js"), 200, {"Content-Type": "text/javascript", "Service-Worker-Allowed": "/", "Cache-Control": "no-cache"}


@app.get("/manifest.webmanifest")
def manifest():
    return jsonify({"name": BRAND, "short_name": BRAND, "start_url": "/app", "scope": "/", "display": "standalone",
                    "background_color": "#0C0B10", "theme_color": "#0C0B10", "description": "Instagram DM automation for creators",
                    "icons": [{"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png"},
                              {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png"},
                              {"src": "/static/icon-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}), \
        200, {"Content-Type": "application/manifest+json"}


@app.get("/api/activity")
def api_activity():
    return jsonify(store.recent_activity(current_account()["id"], store.ACTIVITY_KEEP if request.args.get("all") else 100))


@app.get("/api/activity.csv")
def api_activity_csv():
    acc = current_account()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["time_utc", "action", "status", "username", "text", "automation_or_post", "detail"])
    for a in store.recent_activity(acc["id"], store.ACTIVITY_KEEP):
        w.writerow([a.get("at", ""), a.get("action", ""), a.get("status", ""), a.get("username", ""), a.get("comment", ""),
                    a.get("media_id", ""), a.get("detail", "")])
    return out.getvalue(), 200, {"Content-Type": "text/csv; charset=utf-8",
                                 "Content-Disposition": f"attachment; filename={acc.get('username', 'account')}-activity.csv"}


# ---------- private file uploads (see files.py) ----------

@app.get("/app/files")
def files_page():
    acc = current_account()
    if acc and not files.available(acc):
        return redirect("/app")
    return render_app("files.html", "files", files_ready=files.configured(), max_mb=files.MAX_MB, types=sorted(files.TYPES))


@app.get("/api/files")
def api_files():
    acc = current_account()
    if not files.available(acc):
        return jsonify(error="Not available."), 403
    return jsonify(files=[files.view(f) for f in files.load(acc["id"])], ready=files.configured())


@app.post("/api/files")
def api_files_upload():
    acc = current_account()
    if not files.available(acc):
        return jsonify(error="Not available."), 403
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(error="No file chosen."), 400
    try:
        item = files.upload(acc, f.filename, f.read(), f.mimetype)
    except files.FileError as e:
        return jsonify(error=str(e)), 400
    return jsonify(file=files.view(item))


@app.delete("/api/files/<fid>")
def api_files_delete(fid):
    acc = current_account()
    if not files.available(acc):
        return jsonify(error="Not available."), 403
    return jsonify(ok=files.delete(acc, fid))


@app.get("/f/<fid>/<name>")
def file_download(fid, name):
    got = files.fetch(fid, name)
    if not got:
        abort(404)
    data, ctype, rec = got
    if name.rsplit(".", 1)[-1].lower() in guides.GUIDE_EXTS and not request.args.get("raw"):
        acc = store.load_account(rec["acc"]) or {"id": rec["acc"]}
        page = store.load_page(acc["id"]) or default_page(acc)
        return Response(guides.render(data.decode("utf-8", errors="replace"), name, acc, page, f"/f/{fid}/{name}?raw=1", BRAND),
                        mimetype="text/html", headers={"Cache-Control": "public, max-age=300"})
    ctype, disp = files.type_for(name)
    return Response(data, content_type=ctype, headers={"Cache-Control": "public, max-age=3600", "X-Content-Type-Options": "nosniff",
                                                       "Content-Security-Policy": "default-src 'none'; img-src 'self'; media-src 'self'; style-src 'unsafe-inline'; sandbox",
                                                       "Content-Disposition": f'{disp}; filename="{name}"'})


# ---------- digital products (see shop.py) ----------

@app.get("/app/products")
def products_page():
    return render_app("products.html", "shop")


def shop_owner():
    user = current_user()
    if not user:
        abort(403)
    return user


@app.get("/api/shop")
def api_shop():
    acc = current_account()
    if acc.get("demo"):
        return jsonify(demo=True, ready=False, payout={}, products=[], sales=[], plan_fee=plans.platform_fee(acc, 499))
    user = shop_owner()
    base = f"{site_url()}/{acc.get('username', '')}/p/"
    return jsonify(ready=shop.ready(), payout=shop.refresh(user),
                   products=[{**p, "url": base + p["id"], "seats_left": shop.seats_left(p),
                              "when": shop.when_text(p["start"], p.get("minutes", 0)) if p.get("type") == "event" else ""}
                             for p in shop.products(acc["id"])],
                   sales=shop.sales(acc["id"], 50), plan_fee=plans.platform_fee(acc, 499))


@app.post("/api/shop/products/<pid>/duplicate")
def api_product_duplicate(pid):
    acc = current_account()
    try:
        p = shop.duplicate(acc, pid)
    except shop.ShopError as e:
        return jsonify(error=str(e)), 400
    return jsonify(product=p)


@app.put("/api/shop/payout")
def api_shop_payout():
    try:
        return jsonify(payout=shop.onboard(shop_owner(), request.get_json(force=True) or {}))
    except shop.ShopError as e:
        return jsonify(error=str(e)), 400


@app.put("/api/shop/products")
def api_shop_save():
    try:
        return jsonify(product=shop.save_product(current_account(), request.get_json(force=True) or {}))
    except shop.ShopError as e:
        return jsonify(error=str(e)), 400


@app.delete("/api/shop/products/<pid>")
def api_shop_delete(pid):
    return jsonify(ok=shop.delete_product(current_account(), pid))


@app.post("/api/shop/upload")
def api_shop_upload():
    """The file a product delivers: stored privately, only served with a buyer's download link."""
    acc = current_account()
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(error="No file chosen."), 400
    try:
        item = files.upload(acc, f.filename, f.read(), f.mimetype, paid=True, listed=False)
    except files.FileError as e:
        return jsonify(error=str(e)), 400
    return jsonify(file_id=item["id"], file_name=item["name"], size=item["size"])


def shop_product(username, pid):
    acc = store.account_by_username(username) if USERNAME_RE.fullmatch(username or "") else None
    prod = shop.get(acc["id"], pid) if acc and re.fullmatch(r"[0-9a-f]{10}", pid or "") else None
    if not prod or not prod.get("enabled", True):
        abort(404)
    return acc, prod


@app.get("/<username>/p/<pid>")
def product_page(username, pid):
    acc, prod = shop_product(username, pid)
    owner = users.owner_of(acc)
    page = store.load_page(acc["id"]) or default_page(acc)
    kind = prod.get("type", "file")
    over = kind == "event" and prod["start"] + prod.get("minutes", 60) * 60 < time.time()
    return render_template("product.html", acc=public_account(acc), prod=prod, page={**page, "theme": theme_of(page)},
                           can_buy=shop.ready() and bool(owner) and shop.can_sell(owner) and not over, kind=kind, over=over,
                           when=shop.when_text(prod["start"], prod.get("minutes", 0)) if kind == "event" else "",
                           seats=shop.seats_left(prod) if kind == "event" else None,
                           days=", ".join(shop.DAYS[d] for d in prod.get("days", [])) if kind == "booking" else "")


@app.get("/<username>/p/<pid>/slots")
def product_slots(username, pid):
    acc, prod = shop_product(username, pid)
    if prod.get("type") != "booking":
        abort(404)
    out = {}
    for ts in shop.slots(acc["id"], prod):
        t = time.gmtime(ts + shop.IST)
        out.setdefault(time.strftime("%Y-%m-%d", t), {"label": time.strftime("%a %d %b", t).replace(" 0", " "), "slots": []})
        out[time.strftime("%Y-%m-%d", t)]["slots"].append({"ts": ts, "label": time.strftime("%I:%M %p", t).lstrip("0")})
    resp = jsonify(days=list(out.values()), minutes=prod["minutes"])
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.post("/<username>/p/<pid>/order")
def product_order(username, pid):
    acc, prod = shop_product(username, pid)
    if not request.is_json:
        return jsonify(error="JSON required"), 415
    ip = client_ip()
    k = f"s:shopip:{ip}:{int(time.time() // 60)}"
    if (store.redis("INCR", k) or 0) > 10:  # at most 10 order attempts a minute per IP
        return jsonify(error="Too many tries. Wait a minute, then try again."), 429
    store.redis("EXPIRE", k, 60)
    try:
        return jsonify(shop.create_order(acc, prod, request.get_json(force=True) or {}))
    except shop.ShopError as e:
        return jsonify(error=str(e)), 400


@app.post("/<username>/p/<pid>/paid")
def product_paid(username, pid):
    shop_product(username, pid)
    if not request.is_json:
        return jsonify(error="JSON required"), 415
    d = request.get_json(force=True) or {}
    try:
        o = shop.verify_checkout(str(d.get("order_id", "")), str(d.get("payment_id", "")), d.get("signature"))
    except shop.ShopError as e:
        return jsonify(error=str(e)), 400
    return jsonify(download=f"/d/{o['token']}")


@app.get("/d/<token>")
def download_page(token):
    d = shop.download(token)
    if not d:
        return render_template("download.html", missing=True, acc={}, prod={}, left=0), 404
    acc = store.load_account(d["acc"]) or {}
    prod = shop.get(d["acc"], d["product"]) or {"title": d.get("title", "Your download")}
    kind = d.get("type", "file")
    content = (prod.get("content") if prod.get("id") else None) or d.get("content", "")
    join = (prod.get("join_url") if prod.get("id") else None) or d.get("join_url", "")
    cal = ""
    if d.get("when"):
        fmt = lambda ts: time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(ts))
        cal = "https://calendar.google.com/calendar/render?" + urlencode({
            "action": "TEMPLATE", "text": d.get("title", ""), "dates": f"{fmt(d['when'])}/{fmt(d['when'] + (d.get('minutes') or 60) * 60)}",
            "details": (f"Join: {join}\n" if join else "") + f"Details: {site_url()}/d/{token}"})
    return render_template("download.html", missing=False, acc=public_account(acc) if acc else {}, prod=prod, kind=kind,
                           token=token, left=max(0, shop.DL_MAX - d["n"]), content=content, join=join, cal=cal,
                           when=shop.when_text(d["when"], d.get("minutes") or 0) if d.get("when") else "",
                           started=bool(d.get("when")) and time.time() > d["when"] - 15 * 60,
                           has_file=bool(d.get("file_id")))


@app.get("/d/<token>/file")
def download_file(token):
    d = shop.download(token)
    if not d or not d.get("file_id") or not shop.count_download(token):
        abort(404)
    got = files.fetch(d["file_id"], paid_ok=True)  # the file as it was when they paid
    if not got:
        abort(404)
    data, ctype, rec = got
    return Response(data, mimetype=ctype, headers={"Content-Disposition": f'attachment; filename="{rec["name"]}"',
                                                   "Cache-Control": "no-store"})


# ---------- courses (see courses.py) ----------

@app.get("/app/courses")
def courses_page():
    return render_app("courses.html", "courses")


@app.get("/app/courses/<cid>")
def course_edit_page(cid):
    acc = current_account()
    c = courses.get(cid)
    if acc and (not c or c["acc"] != acc["id"]):
        return redirect("/app/courses")
    return render_app("course_edit.html", "courses", course_id=cid)


def my_course(cid):
    acc = current_account()
    c = courses.get(cid)
    if not c or c["acc"] != acc["id"] or c.get("deleted"):
        abort(404)
    return acc, c


def course_public_url(acc, c):
    return f"{site_url()}/{acc.get('username', '')}/c/{c.get('slug') or c['id']}"


@app.get("/api/courses")
def api_courses():
    acc = current_account()
    rows = []
    for c in courses.of_account(acc["id"]):
        if c.get("deleted"):
            continue
        n_mod, n_les = courses.counts(c)
        v = courses.views(c)
        rows.append({"id": c["id"], "title": c["title"], "status": c["status"], "price": courses.price_now(c), "cover": c.get("cover", ""),
                     "sales": c.get("sales", 0), "revenue": c.get("revenue", 0), "views": v, "modules": n_mod, "lessons": n_les,
                     "url": course_public_url(acc, c), "created": c.get("created"), "paused": bool(c.get("paused")),
                     "conversion": round(100 * c.get("sales", 0) / v, 1) if v else 0})
    sales, revenue, views = sum(r["sales"] for r in rows), sum(r["revenue"] for r in rows), sum(r["views"] for r in rows)
    return jsonify(courses=rows, sales=sales, revenue=revenue, conversion=round(100 * sales / views, 1) if views else 0,
                   payouts=shop.can_sell(current_user()) if current_user() else False)


@app.post("/api/courses")
def api_course_create():
    try:
        c = courses.create(current_account(), (request.get_json(force=True) or {}).get("title"))
    except courses.CourseError as e:
        return jsonify(error=str(e)), 400
    return jsonify(id=c["id"])


@app.get("/api/courses/<cid>")
def api_course_get(cid):
    acc, c = my_course(cid)
    bump = [{"kind": "course", "id": x["id"], "title": x["title"]} for x in courses.of_account(acc["id"]) if x["id"] != cid and not x.get("deleted")]
    bump += [{"kind": "product", "id": p["id"], "title": p["title"]} for p in shop.products(acc["id"]) if p.get("type", "file") in ("file", "locked")]
    return jsonify(course=c, url=course_public_url(acc, c), sessions=courses.sessions(c), plan_fee=plans.platform_fee(acc, 499),
                   payouts=shop.can_sell(current_user()) if current_user() else False, bump_options=bump, usd_inr=courses.fx())


@app.put("/api/courses/<cid>")
def api_course_save(cid):
    acc, c = my_course(cid)
    try:
        c = courses.clean(acc, cid, request.get_json(force=True) or {})
    except courses.CourseError as e:
        return jsonify(error=str(e)), 400
    return jsonify(course=c, url=course_public_url(acc, c), sessions=courses.sessions(c))


@app.delete("/api/courses/<cid>")
def api_course_delete(cid):
    acc, c = my_course(cid)
    return jsonify(ok=courses.delete(acc, cid))


@app.post("/api/courses/upload")
def api_course_upload():
    """Uploads for courses: kind=cover (public image) or kind=file (private: lesson resources and audio)."""
    acc = current_account()
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(error="No file chosen."), 400
    cover = request.args.get("kind") == "cover"
    if cover and not re.search(r"\.(png|jpe?g|webp|gif)$", f.filename, re.I):
        return jsonify(error="Use a PNG, JPG, WEBP or GIF image."), 400
    try:
        item = files.upload(acc, f.filename, f.read(), f.mimetype, paid=not cover, listed=False)
    except files.FileError as e:
        return jsonify(error=str(e)), 400
    return jsonify(id=item["id"], name=item["name"], size=item["size"], url=files.link(item) if cover else "")


@app.post("/api/courses/video")
def api_video_start():
    d = request.get_json(force=True) or {}
    if locked(current_account(), "video_upload"):
        return locked(current_account(), "video_upload")
    try:
        v = videos.start(current_account(), d.get("name"), d.get("size"), plans.limit(current_account(), "video_gb"))
    except videos.VideoError as e:
        return jsonify(error=str(e)), 400
    return jsonify(id=v["id"], parts=v["parts"], chunk=videos.CHUNK, name=v["name"])


@app.put("/api/courses/video/<vid>/<int:n>")
def api_video_chunk(vid, n):
    try:
        got = videos.put_chunk(current_account(), vid, n, request.get_data())
    except videos.VideoError as e:
        return jsonify(error=str(e)), 400
    return jsonify(received=got)


@app.post("/api/courses/video/<vid>/done")
def api_video_done(vid):
    try:
        v = videos.finish(current_account(), vid)
    except videos.VideoError as e:
        return jsonify(error=str(e)), 400
    return jsonify(id=v["id"], name=v["name"], size=v["size"])


@app.get("/app/courses/assessments")
def assessments_page():
    return render_app("assessments.html", "courses")


@app.get("/api/courses/assessments")
def api_assessments():
    """Every assignment submission and quiz attempt across this account's courses."""
    acc = current_account()
    work, quizzes = [], []
    for c in courses.of_account(acc["id"]):
        titles = {ls["id"]: ls["title"] for _, ls in courses.lessons(c, True)}
        for e in courses.students(c["id"]):
            who = {"email": e["email"], "name": e.get("name", ""), "course": c["title"], "course_id": c["id"]}
            for lid, w in (e.get("work") or {}).items():
                work.append({**who, **w, "lesson": lid, "title": titles.get(lid, "Assignment")})
            for lid, q in (e.get("quiz") or {}).items():
                quizzes.append({**who, **q, "lesson": lid, "title": titles.get(lid, "Quiz")})
    work.sort(key=lambda w: (w.get("grade") is not None, -w.get("at", 0)))
    quizzes.sort(key=lambda q: -q.get("at", 0))
    return jsonify(work=work, quizzes=quizzes)


@app.post("/api/courses/<cid>/duplicate")
def api_course_duplicate(cid):
    acc, c = my_course(cid)
    try:
        copy = courses.duplicate(acc, c)
    except courses.CourseError as e:
        return jsonify(error=str(e)), 400
    return jsonify(id=copy["id"])


@app.put("/api/courses/<cid>/flags")
def api_course_flags(cid):
    """Quick switches from the course list: publish / unpublish, pause / resume payments."""
    acc, c = my_course(cid)
    d = request.get_json(force=True) or {}
    if "paused" in d:
        c["paused"] = bool(d["paused"])
    if d.get("status") in ("published", "unpublished", "draft"):
        if d["status"] == "published" and not courses.lessons(c):
            return jsonify(error="Add at least one lesson before publishing."), 400
        c["status"] = d["status"]
    store.set_json(f"s:course:{cid}", c)
    return jsonify(status=c["status"], paused=bool(c.get("paused")))


@app.post("/api/page/add")
def api_page_add():
    """Adds a product or course card to the link-in-bio page (from the Store and Courses lists)."""
    acc = current_account()
    d = request.get_json(force=True) or {}
    url, title = str(d.get("url", "")), str(d.get("title", "")).strip()[:100]
    if not url.startswith(site_url() + "/") or not title:
        return jsonify(error="Nothing to add."), 400
    page = store.load_page(acc["id"]) or default_page(acc)
    items = page.get("items") or []
    if any(i.get("url") == url for i in items):
        return jsonify(added=False, already=True)
    items.insert(0, {"type": "product", "title": title, "url": url, "price": str(d.get("price", ""))[:20], "featured": False})
    page = clean_page({**page, "items": items}, acc)
    store.save_page(acc["id"], page)
    return jsonify(added=True)


@app.get("/api/courses/<cid>/students")
def api_course_students(cid):
    acc, c = my_course(cid)
    titles = {ls["id"]: ls["title"] for _, ls in courses.lessons(c, True)}
    out = []
    for e in courses.students(cid):
        out.append({"email": e["email"], "name": e.get("name", ""), "phone": e.get("phone", ""), "at": e.get("at"), "until": e.get("until"),
                    "paid": e.get("paid", 0), "percent": courses.percent(c, e),
                    "work": [{"lesson": lid, "title": titles.get(lid, ""), **w} for lid, w in (e.get("work") or {}).items()]})
    return jsonify(students=out)


@app.get("/api/courses/<cid>/students.csv")
def api_course_students_csv(cid):
    acc, c = my_course(cid)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["name", "email", "phone", "enrolled", "paid", "progress %", "access until"])
    for e in courses.students(cid):
        w.writerow([e.get("name", ""), e["email"], e.get("phone", ""), time.strftime("%Y-%m-%d", time.gmtime(e.get("at", 0))),
                    e.get("paid", 0), courses.percent(c, e), time.strftime("%Y-%m-%d", time.gmtime(e["until"])) if e.get("until") else "lifetime"])
    return Response(buf.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f'attachment; filename="{c.get("slug") or cid}-students.csv"'})


@app.put("/api/courses/<cid>/review")
def api_course_review(cid):
    acc, c = my_course(cid)
    d = request.get_json(force=True) or {}
    try:
        return jsonify(work=courses.review_work(c, str(d.get("email", "")).lower(), str(d.get("lesson", "")), d.get("grade"), d.get("feedback")))
    except courses.CourseError as e:
        return jsonify(error=str(e)), 400


def public_course(username, slug):
    acc = store.account_by_username(username) if USERNAME_RE.fullmatch(username or "") else None
    c = courses.by_slug(acc["id"], slug) if acc else None
    if not c or c["acc"] != acc["id"] or c.get("deleted"):
        abort(404)
    mine = (current_account() or {}).get("id") == acc["id"]
    if c["status"] != "published" and not mine:
        abort(404)
    return acc, c, mine


@app.get("/<username>/c/<slug>")
def course_sales_page(username, slug):
    acc, c, mine = public_course(username, slug)
    if not mine:
        courses.count_view(c)
    owner = users.owner_of(acc)
    n_mod, n_les = courses.counts(c)
    free = next(((m, ls) for m, ls in courses.lessons(c) if ls.get("free")), None)
    return render_template("course_sales.html", acc=public_account(acc), c=c, n_mod=n_mod, n_les=n_les, mine=mine,
                           desc_html=guides.blocks_html(c.get("desc", "")), about_html=guides.blocks_html(c.get("about", "")),
                           enrolled=len(store.redis("SMEMBERS", f"s:enrs:{c['id']}") or []), free=free,
                           price=courses.price_now(c), pay_ok=shop.ready() and bool(owner) and shop.can_sell(owner),
                           free_ok=c.get("price_mode") == "pwyw" and not c.get("min_price"),
                           sessions=courses.sessions(c), when=shop.when_text, embed=courses.embed(c.get("cover_video", "")),
                           usd=courses.intl_price(c), abroad=request.headers.get("x-vercel-ip-country", "IN").upper() not in ("IN", ""),
                           bump=courses.bump_target(c) if (c.get("bump") or {}).get("enabled") else None)


@app.post("/<username>/c/<slug>/order")
def course_order(username, slug):
    acc, c, _ = public_course(username, slug)
    if not request.is_json:
        return jsonify(error="JSON required"), 415
    ip = client_ip()
    k = f"s:shopip:{ip}:{int(time.time() // 60)}"
    if (store.redis("INCR", k) or 0) > 10:
        return jsonify(error="Too many tries. Wait a minute, then try again."), 429
    store.redis("EXPIRE", k, 60)
    try:
        r = courses.order(acc, c, request.get_json(force=True) or {})
    except (courses.CourseError, shop.ShopError) as e:
        return jsonify(error=str(e)), 400
    if r.get("free"):
        grant_course(c["id"], str((request.get_json(force=True) or {}).get("email", "")).strip().lower())
        r["next"] = f"/learn/{c['id']}"
    return jsonify(r)


@app.post("/<username>/c/<slug>/paid")
def course_paid(username, slug):
    acc, c, _ = public_course(username, slug)
    if not request.is_json:
        return jsonify(error="JSON required"), 415
    d = request.get_json(force=True) or {}
    try:
        o = shop.verify_checkout(str(d.get("order_id", "")), str(d.get("payment_id", "")), d.get("signature"))
    except shop.ShopError as e:
        return jsonify(error=str(e)), 400
    if o.get("course") != c["id"]:
        return jsonify(error="That payment is for something else."), 400
    grant_course(c["id"], o["email"])
    return jsonify(next=f"/learn/{c['id']}")


@app.get("/<username>/c/<slug>/preview/<lid>")
def course_free_lesson(username, slug, lid):
    acc, c, mine = public_course(username, slug)
    pair = next(((m, ls) for m, ls in courses.lessons(c) if ls["id"] == lid and (ls.get("free") or mine)), None)
    if not pair:
        abort(404)
    return learn_render(acc, c, None, pair, preview=True)


# ---------- students ----------

def student():
    """The email signed in to /learn (by email code or the link in their email)."""
    return session.get("student") or ""


def student_for(cid):
    """The student for one course: the signed-in email, or the email that just enrolled in or bought this course here.
    Enrolling only opens that course: typing someone else's email at checkout never shows their other courses."""
    return student() or (session.get("access") or {}).get(cid, "")


def grant_course(cid, email):
    acc_map = dict(session.get("access") or {})
    acc_map[cid] = email
    session["access"] = dict(list(acc_map.items())[-20:])


@app.get("/learn")
def learn_home():
    email = student()
    if not email:
        return render_template("learn_login.html", email_ready=users.email_ready())
    rows = []
    for c in courses.my_courses(email):
        e = courses.enrollment(c["id"], email)
        if e:
            acc = store.load_account(c["acc"]) or {}
            rows.append({"c": c, "pct": courses.percent(c, e), "expired": e.get("expired"), "by": acc.get("username", "")})
    return render_template("learn_home.html", email=email, rows=rows)


@app.post("/learn/start")
def learn_start():
    if not request.is_json:
        return jsonify(error="JSON required"), 415
    ip = client_ip()
    try:
        email = users.start_email((request.get_json(force=True) or {}).get("email"), ip)
    except users.LoginError as e:
        return jsonify(error=str(e).replace(" Wait an hour, or use Google.", " Wait an hour.").replace(" Use Google for now.", "")), 400
    return jsonify(email=email)


@app.post("/learn/verify")
def learn_verify():
    if not request.is_json:
        return jsonify(error="JSON required"), 415
    d = request.get_json(force=True) or {}
    try:
        email = users.verify_email(d.get("email"), d.get("code"))
    except users.LoginError as e:
        return jsonify(error=str(e)), 400
    session["student"] = email
    return jsonify(next="/learn")


@app.get("/learn/in/<tok>")
def learn_magic(tok):
    m = courses.use_magic(tok)
    if not m:
        return redirect("/learn")
    session["student"] = m["email"]
    return redirect(f"/learn/{m['course']}" if m.get("course") else "/learn")


@app.post("/learn/logout")
def learn_logout():
    session.pop("student", None)
    session.pop("access", None)
    return redirect("/learn")


def learner(cid):
    """(account, course, enrollment, preview) for the signed-in student, or the creator previewing their own course."""
    c = courses.get(cid)
    if not c:
        abort(404)
    acc = store.load_account(c["acc"]) or {"id": c["acc"]}
    if (current_account() or {}).get("id") == c["acc"] and not courses.enrollment(cid, student_for(cid)):
        return acc, c, {"email": "", "name": "Preview", "progress": {}, "quiz": {}, "work": {}, "at": 0}, True
    email = student_for(cid)
    e = courses.enrollment(cid, email) if email else None
    if not e:
        return acc, c, None, False
    return acc, c, e, False


@app.get("/learn/<cid>")
def learn_dashboard(cid):
    acc, c, e, preview = learner(cid)
    if not e:
        return redirect("/learn")
    if e.get("expired"):
        return render_template("learn_home.html", email=student(), rows=[], expired=c)
    mods = []
    flat = courses.lessons(c)
    for i, m in enumerate(c["modules"]):
        if not m.get("live", True):
            continue
        ls = [x for x in m["lessons"] if x.get("live", True)]
        mods.append({"m": m, "lessons": ls, "open": preview or courses.unlocked(c, e, i), "done": sum(1 for x in ls if x["id"] in e["progress"])})
    nxt = next((ls for _, ls in flat if ls["id"] not in e["progress"]), flat[0][1] if flat else None)
    cert = courses.certificate(c, e["email"]) if not preview else None
    return render_template("learn_dash.html", acc=public_account(acc) if acc.get("username") else {}, c=c, e=e, mods=mods, preview=preview,
                           pct=courses.percent(c, e), nxt=nxt, n_les=len(flat), sessions=courses.sessions(c), when=shop.when_text,
                           cert=cert, started=bool(e.get("progress")), now=time.time())


def learn_lesson_pair(c, e, lid, preview):
    for i, m in enumerate(c["modules"]):
        for ls in m["lessons"]:
            if ls["id"] == lid and m.get("live", True) and ls.get("live", True):
                if not preview and not courses.unlocked(c, e, i):
                    raise courses.CourseError("This lesson unlocks later.")
                return m, ls
    abort(404)


@app.get("/learn/<cid>/<lid>")
def learn_lesson(cid, lid):
    acc, c, e, preview = learner(cid)
    if not e or e.get("expired"):
        return redirect("/learn")
    try:
        pair = learn_lesson_pair(c, e, lid, preview)
    except courses.CourseError:
        return redirect(f"/learn/{cid}")
    return learn_render(acc, c, e, pair, preview=preview)


def learn_render(acc, c, e, pair, preview=False):
    m, ls = pair
    flat = courses.lessons(c)
    idx = next(i for i, (_, x) in enumerate(flat) if x["id"] == ls["id"])
    mod_lessons = [x for x in m["lessons"] if x.get("live", True)]
    return render_template("learn_lesson.html", c=c, m=m, ls=ls, e=e or {"progress": {}, "quiz": {}, "work": {}}, preview=preview,
                           guest=e is None, idx=idx, flat=flat, prev=flat[idx - 1][1] if idx > 0 else None,
                           nxt=flat[idx + 1][1] if idx + 1 < len(flat) else None, body_html=guides.blocks_html(ls.get("body", "")),
                           embed=courses.embed(ls.get("video", "")), pos=mod_lessons.index(ls) + 1 if ls in mod_lessons else 1,
                           mod_count=len(mod_lessons), mod_index=[x for x in c["modules"] if x.get("live", True)].index(m) if m in c["modules"] else 0,
                           unlocked={i: (preview or e is None or courses.unlocked(c, e, i)) for i in range(len(c["modules"]))},
                           acc=public_account(acc) if acc.get("username") else {})


def learn_json(cid, lid):
    if not request.is_json:
        abort(415)
    acc, c, e, preview = learner(cid)
    if not e or e.get("expired") or preview:
        abort(403)
    try:
        _, ls = learn_lesson_pair(c, e, lid, False)
    except courses.CourseError as err:
        return c, None, str(err)
    return c, ls, None


@app.post("/learn/<cid>/<lid>/done")
def learn_done(cid, lid):
    c, ls, err = learn_json(cid, lid)
    if err:
        return jsonify(error=err), 400
    e = courses.mark(c, student_for(cid), lid, (request.get_json(force=True) or {}).get("done", True) is not False)
    return jsonify(pct=courses.percent(c, e))


@app.post("/learn/<cid>/<lid>/quiz")
def learn_quiz(cid, lid):
    c, ls, err = learn_json(cid, lid)
    if err or ls.get("type") != "quiz":
        return jsonify(error=err or "Not a quiz."), 400
    try:
        return jsonify(result=courses.grade_quiz(c, student_for(cid), ls, (request.get_json(force=True) or {}).get("answers") or []))
    except courses.CourseError as e:
        return jsonify(error=str(e)), 400


@app.post("/learn/<cid>/<lid>/work")
def learn_work(cid, lid):
    c, ls, err = learn_json(cid, lid)
    if err or ls.get("type") != "assignment":
        return jsonify(error=err or "Not an assignment."), 400
    d = request.get_json(force=True) or {}
    try:
        return jsonify(work=courses.submit_work(c, student_for(cid), ls, d.get("text"), d.get("link")))
    except courses.CourseError as e:
        return jsonify(error=str(e)), 400


@app.get("/learn/<cid>/<lid>/video")
def learn_video(cid, lid):
    """An uploaded lesson video, streamed piece by piece (Range requests) to enrolled students and free previews."""
    acc, c, e, preview = learner(cid)
    pair = next(((m, ls) for m, ls in courses.lessons(c) if ls["id"] == lid), None)
    if not pair or not (e or pair[1].get("free")) or (e and e.get("expired")):
        abort(404)
    v = videos.get(pair[1].get("video_file"))
    if not v or v["acc"] != c["acc"] or not v.get("done"):
        abort(404)
    try:
        data, a, b = videos.read(v, request.headers.get("Range", ""))
    except videos.VideoError as err:
        if str(err) == "range":
            return Response(status=416, headers={"Content-Range": f"bytes */{v['size']}"})
        abort(502)
    return Response(data, status=206, mimetype=v["type"], headers={
        "Content-Range": f"bytes {a}-{b}/{v['size']}", "Accept-Ranges": "bytes", "Content-Length": str(len(data)),
        "Cache-Control": "private, max-age=3600", "Content-Disposition": "inline"})


@app.get("/learn/<cid>/<lid>/file/<fid>")
def learn_file(cid, lid, fid):
    acc, c, e, preview = learner(cid)
    pair = next(((m, ls) for m, ls in courses.lessons(c) if ls["id"] == lid), None)
    if not pair or not (e or pair[1].get("free")) or (e and e.get("expired")):
        abort(404)
    ls = pair[1]
    if fid not in [f["id"] for f in ls.get("files", [])] + [ls.get("audio_file")]:
        abort(404)
    got = files.fetch(fid, paid_ok=True)
    if not got:
        abort(404)
    data, ctype, rec = got
    ctype, disp = files.type_for(rec["name"])
    inline = request.args.get("inline") == "1" and disp == "inline"
    return Response(data, content_type=ctype, headers={"Content-Disposition": f'{"inline" if inline else "attachment"}; filename="{rec["name"]}"',
                                                       "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
                                                       "Content-Security-Policy": "default-src 'none'; sandbox"})


@app.get("/cert/<cert_id>")
def cert_page(cert_id):
    cert = courses.get_cert(cert_id)
    if not cert:
        abort(404)
    acc = store.load_account(cert["acc"]) or {}
    return render_template("cert.html", cert=cert, by=acc.get("username", ""), date=time.strftime("%d %B %Y", time.gmtime(cert["at"] + shop.IST)))


# ---------- YouTube scheduling (see youtube.py) ----------

def yt_redirect_uri():
    # The exact address registered in Google Cloud; the request's own host by default (not PUBLIC_URL, which may be a parked domain).
    return youtube._env("YT_REDIRECT_URI") or request.host_url.rstrip("/") + "/youtube/callback"


def yt_call(fn):
    """Runs a YouTube action for the logged-in account; YTError becomes a 400 with its friendly message."""
    acc = current_account()
    if not youtube.available(acc):
        return jsonify(error="YouTube scheduling isn't switched on for this account yet."), 403
    try:
        item = fn(acc)
    except youtube.YTError as e:
        return jsonify({**yt_state(acc), "error": str(e)}), 400
    except Exception as e:
        return jsonify({**yt_state(acc), "error": f"Something went wrong talking to YouTube: {e}"}), 502
    body = yt_state(acc)
    if isinstance(item, dict) and item.get("id"):
        body["item"] = youtube.view(acc, item)
    return jsonify(body)


def yt_state(acc):
    youtube.ensure_demo(acc)
    conn = youtube.connection(acc)
    items = youtube.refresh_statuses(acc) if conn.get("refresh_token") or acc.get("demo") else youtube.load(acc["id"])
    channel = ({"title": "Demo channel", "pic": "", "broken": False} if acc.get("demo") else
               {"title": conn.get("channel_title", ""), "pic": conn.get("channel_pic", ""), "broken": bool(conn.get("broken"))}
               if conn.get("refresh_token") else None)
    return {"available": youtube.available(acc), "configured": youtube.configured(), "channel": channel, "demo": bool(acc.get("demo")),
            "items": sorted([youtube.view(acc, v) for v in items], key=lambda v: (v.get("publish_at") or "9", v["created"])),
            "categories": youtube.CATEGORIES, "credits_left": content_drafts.credits_left(acc)}


@app.get("/app/youtube")
def youtube_page():
    acc = current_account()
    if acc and not youtube.available(acc):
        return redirect("/app/apps")
    return render_app("youtube.html", "youtube", yt_error=request.args.get("error", ""), yt_connected=bool(request.args.get("connected")))


@app.get("/youtube/connect")
def youtube_connect():
    acc = current_account()
    if not acc:
        return redirect(url_for("landing"))
    if acc.get("demo") or not youtube.configured() or not youtube.available(acc) or current_role() == "viewer":
        return redirect("/app/youtube?error=" + "YouTube connect isn't available for this account.")
    session["yt_state"] = secrets.token_urlsafe(16)
    return redirect(youtube.auth_url(yt_redirect_uri(), session["yt_state"]))


@app.get("/youtube/callback")
def youtube_callback():
    acc = current_account()
    if not acc:
        return redirect(url_for("landing"))
    state = session.pop("yt_state", None)
    if request.args.get("error"):
        return redirect("/app/youtube?" + urlencode({"error": "Google sign-in was cancelled."}))
    if not state or not hmac.compare_digest(state, request.args.get("state", "")):
        return redirect("/app/youtube?" + urlencode({"error": "That sign-in link expired. Try Connect again."}))
    try:
        youtube.finish_connect(acc, request.args.get("code", ""), yt_redirect_uri())
    except youtube.YTError as e:
        return redirect("/app/youtube?" + urlencode({"error": str(e)}))
    store.log_activity(acc["id"], "", "", "", "youtube", "ok", "YouTube channel connected")
    return redirect("/app/youtube?connected=1")


@app.get("/api/youtube")
def api_youtube():
    acc = current_account()
    if not youtube.available(acc):
        return jsonify(available=False, configured=youtube.configured())
    return jsonify(yt_state(acc))


@app.post("/api/youtube/disconnect")
def api_youtube_disconnect():
    return yt_call(youtube.disconnect)


@app.post("/api/youtube/token")
def api_youtube_token():
    """A short-lived access token so the browser uploads the file straight to YouTube (never through Vercel)."""
    acc = current_account()
    if not youtube.available(acc) or acc.get("demo"):
        return jsonify(error="Uploads are switched off here."), 403
    try:
        token, expires = youtube.access_token(acc)
    except youtube.YTError as e:
        return jsonify(error=str(e)), 400
    return jsonify(access_token=token, expires=expires)


@app.post("/api/youtube/details")
def api_youtube_details():
    acc = current_account()
    if not youtube.available(acc):
        return jsonify(error="YouTube scheduling isn't switched on for this account yet."), 403
    d = request.get_json(force=True)
    try:
        out = youtube.write_details(acc, d.get("notes", ""), d.get("transcript", ""), d.get("file_name", ""),
                                    float(d.get("duration") or 0), bool(d.get("vertical")))
    except youtube.YTError as e:
        return jsonify(error=str(e)), 400
    except Exception as e:
        return jsonify(error=f"The AI couldn't write right now: {e}"), 502
    return jsonify(out)


@app.post("/api/youtube/videos")
def api_youtube_add():
    d = request.get_json(force=True)
    return yt_call(lambda acc: youtube.create(acc, d))


@app.post("/api/youtube/videos/<item_id>/<action>")
def api_youtube_action(item_id, action):
    d = request.get_json(force=True)
    acts = {
        "uploaded": lambda acc: youtube.uploaded(acc, item_id, d.get("video_id")),
        "upload-failed": lambda acc: youtube.upload_failed(acc, item_id, d.get("error", "")),
        "thumb": lambda acc: youtube.thumb_result(acc, item_id, bool(d.get("ok")), d.get("error", "")),
        "approve": lambda acc: youtube.approve(acc, item_id, d.get("publish_at")),
        "reject": lambda acc: youtube.reject(acc, item_id, d.get("note", "")),
        "review": lambda acc: youtube.back_to_review(acc, item_id),
    }
    if action not in acts:
        abort(404)
    resp = yt_call(acts[action])
    if action == "approve" and not isinstance(resp, tuple):
        store.log_activity(current_account()["id"], "", "", "", "youtube", "ok", "YouTube video scheduled")
    return resp


@app.put("/api/youtube/videos/<item_id>")
def api_youtube_update(item_id):
    d = request.get_json(force=True)
    return yt_call(lambda acc: youtube.update(acc, item_id, d))


@app.delete("/api/youtube/videos/<item_id>")
def api_youtube_delete(item_id):
    d = request.get_json(force=True)
    return yt_call(lambda acc: youtube.remove(acc, item_id, bool(d.get("from_youtube"))))


@app.get("/app/activity")
def activity_page():
    return render_app("activity.html", "activity")


@app.get("/app/sales")
def sales_page():
    return render_app("sales.html", "sales")


# ---------- content plan: AI drafts a week of posts, the creator approves ----------

@app.get("/app/plan")
def plan_page():
    return render_app("plan.html", "plan")


def drafts_view(acc):
    return {"drafts": content_drafts.list_drafts(acc), **content_drafts.summary(acc)}


@app.get("/api/drafts")
def api_drafts():
    return jsonify(drafts_view(current_account()))


@app.post("/api/drafts/fill")
def api_drafts_fill():
    acc = current_account()
    data = request.get_json(force=True)
    try:
        new = content_drafts.fill_week(acc, data.get("brief", ""), data.get("days", 7), data.get("start"), data.get("per_day", 1))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except Exception as e:
        return jsonify(error=f"The AI couldn't draft right now: {e}"), 502
    store.log_activity(acc["id"], "", "", "", "plan", "ok", f"{len(new)} post drafts written")
    return jsonify({**drafts_view(acc), "added": len(new)})


@app.put("/api/drafts/<draft_id>")
def api_draft_update(draft_id):
    acc = current_account()
    try:
        content_drafts.update(acc, draft_id, request.get_json(force=True))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    return jsonify(drafts_view(acc))


@app.post("/api/drafts/<draft_id>/rewrite")
def api_draft_rewrite(draft_id):
    acc = current_account()
    try:
        content_drafts.rewrite(acc, draft_id, request.get_json(force=True).get("feedback", ""))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except Exception as e:
        return jsonify(error=f"The AI couldn't rewrite right now: {e}"), 502
    return jsonify(drafts_view(acc))


@app.delete("/api/drafts/<draft_id>")
def api_draft_delete(draft_id):
    acc = current_account()
    try:
        content_drafts.delete(acc, draft_id)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    return jsonify(drafts_view(acc))


@app.post("/api/pause")
def api_pause():
    acc = current_account()
    acc["paused"] = bool(request.get_json(force=True).get("paused"))
    store.save_account(acc)
    return jsonify(paused=acc["paused"])


# ---------- apps, link-in-bio page, contacts ----------

@app.get("/api/apps")
def api_get_apps():
    return jsonify(apps_of(current_account()))


@app.put("/api/apps")
def api_put_apps():
    acc = current_account()
    data = request.get_json(force=True)
    acc["apps"] = {k: bool(data.get(k, v)) for k, v in DEFAULT_APPS.items()}
    store.save_account(acc)
    return jsonify(acc["apps"])


# ---------- AI DM agent and inbox ----------

LANGUAGES = ["match", "hinglish", "hindi", "english"]


def ai_state(acc):
    return {"settings": ai_agent.settings(acc), "ready": ai_agent.ready(acc), "demo": bool(acc.get("demo")),
            "used": ai_agent.used(acc), "limit": ai_agent.allowance(acc)[1], "kind": ai_agent.allowance(acc)[0],
            "over": ai_agent.over_quota(acc)}


@app.get("/api/inbox")
def api_inbox():
    acc = current_account()
    return jsonify(threads=ai_agent.threads(acc["id"]), **ai_state(acc))


@app.put("/api/ai")
def api_put_ai():
    acc = current_account()
    try:
        update_ai(acc, request.get_json(force=True))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    return jsonify(ai_state(acc))


def update_ai(acc, data):
    """Changes only the AI agent settings present in data."""
    old = ai_agent.settings(acc)
    handoff = [h.strip()[:120] for h in str(data.get("handoff", "")).splitlines() if h.strip()][:10] \
        if "handoff" in data else old["handoff"]
    acc["ai"] = {"enabled": bool(data.get("enabled", old["enabled"])),
                 "language": data.get("language") if data.get("language") in LANGUAGES else old["language"],
                 "about": str(data.get("about", old["about"]))[:1500], "faq": str(data.get("faq", old["faq"]))[:6000],
                 "handoff": handoff, "hold_message": str(data.get("hold_message", old["hold_message"]))[:500],
                 "send_hold": bool(data.get("send_hold", old["send_hold"]))}
    if acc["ai"]["enabled"] and not ai_agent.ready(acc):
        acc["ai"] = old
        raise ValueError("The AI isn't set up on the server yet (ANTHROPIC_API_KEY).")
    store.save_account(acc)
    return ai_state(acc)


@app.post("/api/ai/test")
def api_ai_test():
    """Shows what the AI would answer, without sending anything."""
    acc = current_account()
    text = str(request.get_json(force=True).get("message", "")).strip()[:1000]
    if not text:
        return jsonify(error="Type a message to test."), 400
    if not ai_agent.ready(acc):
        return jsonify(error="The AI isn't set up on the server yet (ANTHROPIC_API_KEY)."), 400
    if ai_agent.over_quota(acc):
        return jsonify(error=ai_agent.quota_reason(acc)), 400
    try:
        answer = ai_agent.answer(acc, [{"role": "fan", "text": text}], ai_agent.settings(acc))
    except Exception as e:
        return jsonify(error=f"The AI couldn't answer: {str(e)[:200]}"), 502
    ai_agent.note_use(acc)
    return jsonify(answer)


@app.get("/api/saved-replies")
def api_saved_replies():
    return jsonify(replies=current_account().get("saved_replies") or [])


@app.put("/api/saved-replies")
def api_put_saved_replies():
    acc = current_account()
    rows = request.get_json(force=True).get("replies") or []
    acc["saved_replies"] = [{"title": str(r.get("title", "")).strip()[:40], "text": str(r.get("text", "")).strip()[:1000]}
                            for r in rows[:30] if str(r.get("title", "")).strip() and str(r.get("text", "")).strip()]
    store.save_account(acc)
    return jsonify(replies=acc["saved_replies"])


@app.get("/api/inbox/<igsid>")
def api_thread(igsid):
    acc = current_account()
    thread = ai_agent.update_thread(acc["id"], igsid, unread=False)
    if not thread:
        return jsonify(error="Conversation not found."), 404
    return jsonify(thread=thread, messages=ai_agent.messages(acc["id"], igsid))


@app.post("/api/inbox/<igsid>/send")
def api_thread_send(igsid):
    """The creator answers by hand. The AI then stays quiet in this chat until they hand it back."""
    acc = current_account()
    try:
        inbox_send(acc, igsid, request.get_json(force=True).get("text", ""))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except RuntimeError as e:
        return jsonify(error=str(e)), 502
    return jsonify(thread=ai_agent.get_thread(acc["id"], igsid), messages=ai_agent.messages(acc["id"], igsid))


def inbox_send(acc, igsid, text):
    """A reply typed by the creator (or Claude for them). The AI then stays out of this chat until handed back."""
    thread = ai_agent.get_thread(acc["id"], igsid)
    text = str(text or "").strip()[:1000]
    if not thread or not text:
        raise ValueError("Write a message first." if thread else "Conversation not found.")
    if time.time() - thread.get("last_fan_at", 0) > 24 * 3600:
        raise ValueError("Instagram only allows replies within 24 hours of their last message.")
    try:
        engine.Instagram(acc).send_dm({"id": igsid}, {"text": text})
    except Exception as e:
        raise RuntimeError(f"Instagram didn't send it: {str(e)[:200]}")
    ai_agent.add_message(acc["id"], igsid, "you", text, status="you", reason="", suggestion="", unread=False)
    store.log_activity(acc["id"], "ai", thread.get("username") or igsid, text, "inbox_reply", "ok")


@app.post("/api/inbox/<igsid>/status")
def api_thread_status(igsid):
    """status "ai" hands the chat back to the AI; "you" keeps the AI out of it."""
    acc = current_account()
    status = request.get_json(force=True).get("status")
    if status not in ("ai", "you"):
        return jsonify(error="Unknown status."), 400
    thread = ai_agent.update_thread(acc["id"], igsid, status=status, reason="", suggestion="", hold_sent=False)
    if not thread:
        return jsonify(error="Conversation not found."), 404
    return jsonify(thread=thread)


THEMES = ["studio", "sunset", "midnight", "ocean", "candy", "mono"]
OLD_THEMES = {"violet": "studio", "mint": "ocean"}  # pages saved before the redesign
SOCIALS = ["instagram", "youtube", "whatsapp", "email", "x", "website"]


def safe_url(url):
    url = str(url or "").strip()
    return url if url.startswith(("https://", "http://", "mailto:", "tel:")) and not re.search(r"[\s<>\"'`\\]", url) else ""


def safe_img(url):
    """An image link that is safe inside src="" and CSS url(''): https only, no quotes, brackets or spaces."""
    url = str(url or "").strip()
    return url if re.fullmatch(r"https://[^\s<>\"'`()\\]+", url) else ""


def clean_page(data, acc):
    items = []
    for i, it in enumerate((data.get("items") or [])[:30]):
        title, url = str(it.get("title", "")).strip()[:80], safe_url(it.get("url"))
        if not title or not url:
            continue
        image = str(it.get("image", "")).strip()
        items.append({"id": re.sub(r"[^a-z0-9]", "", str(it.get("id", "")).lower())[:12] or f"i{i}{secrets.token_hex(3)}",
                      "type": "product" if it.get("type") == "product" else "link", "title": title, "url": url,
                      "subtitle": str(it.get("subtitle", "")).strip()[:120], "price": str(it.get("price", "")).strip()[:20],
                      "image": safe_img(image),
                      "featured": bool(it.get("featured")), "enabled": it.get("enabled", True) is not False})
    socials = data.get("socials") or {}
    sign = data.get("signup") or {}
    signup = {"enabled": bool(sign.get("enabled")), "ask": sign.get("ask") if sign.get("ask") in ("email", "phone", "both") else "email",
              "title": str(sign.get("title", "")).strip()[:80] or "Get my free guide",
              "button": str(sign.get("button", "")).strip()[:30] or "Send it to me",
              "thanks": str(sign.get("thanks", "")).strip()[:200] or "Done! Check your inbox 🎉",
              "link": safe_url(sign.get("link"))}
    freebies = []
    for i, fb in enumerate((data.get("freebies") or [])[:200]):
        if not isinstance(fb, dict):
            continue
        kw = re.sub(r"[^A-Za-z0-9]", "", str(fb.get("k", ""))).upper()[:24]
        title, url = str(fb.get("t", "")).strip()[:100], safe_url(fb.get("u"))
        if not title or not url:
            continue
        freebies.append({"id": re.sub(r"[^a-z0-9]", "", str(fb.get("id", "")).lower())[:12] or f"f{i}{secrets.token_hex(3)}",
                         "k": kw, "t": title, "topic": str(fb.get("topic", "")).strip()[:30], "u": url,
                         "enabled": fb.get("enabled", True) is not False})
    seo = data.get("seo") or {}
    seo_img = str(seo.get("image", "")).strip()
    accent = str(data.get("accent", "")).strip()
    pro = plans.has(acc, "page_pro")
    look = {"accent": accent if pro and re.fullmatch(r"#[0-9a-fA-F]{6}", accent) else "", "layout": "two" if pro and data.get("layout") == "two" else "single",
            "hide_brand": bool(data.get("hide_brand")) and plans.has(acc, "remove_branding"),
            "seo": {} if not pro else {"title": str(seo.get("title", "")).strip()[:70], "description": str(seo.get("description", "")).strip()[:160],
                    "image": safe_img(seo_img) or (seo_img if re.fullmatch(r"/f/[\w-]{6,20}/[\w.-]{1,100}", seo_img) else "")}}
    return {**look, "signup": signup, "freebies": freebies,
            "name": str(data.get("name", "")).strip()[:60] or acc.get("name") or acc.get("username", ""),
            "bio": str(data.get("bio", "")).strip()[:300],
            "theme": theme_of(data),
            "photo": safe_img(data.get("photo")),
            "socials": {k: str(socials.get(k, "")).strip()[:200] for k in SOCIALS}, "items": items}


def theme_of(page):
    t = OLD_THEMES.get(page.get("theme"), page.get("theme"))
    return t if t in THEMES else "studio"


def social_url(key, value):
    """What a social field links to: handles and numbers become full links."""
    v = str(value or "").strip()
    if not v:
        return ""
    if key == "email":
        return "mailto:" + v.removeprefix("mailto:") if "@" in v else ""
    if v.startswith(("https://", "http://")):
        return v
    handle = v.lstrip("@").strip("/")
    if key == "instagram":
        return f"https://www.instagram.com/{handle}/"
    if key == "youtube":
        return f"https://www.youtube.com/@{handle}"
    if key == "x":
        return f"https://x.com/{handle}"
    if key == "whatsapp":
        digits = re.sub(r"\D", "", v)
        return f"https://wa.me/{digits}" if len(digits) >= 8 else ""
    if key == "website" and "." in v and " " not in v:
        return "https://" + v
    return ""


def default_page(acc):
    return {"name": acc.get("name") or acc.get("username", ""), "bio": "", "theme": "studio",
            "socials": {"instagram": acc.get("username", "")}, "items": []}


@app.get("/api/page")
def api_get_page():
    acc = current_account()
    return jsonify(page=store.load_page(acc["id"]) or default_page(acc), clicks=store.clicks(acc["id"]),
                   signups=store.counts(acc["id"]).get("page_signups", 0),
                   url=f"{request.host_url.rstrip('/')}/{acc.get('username', '')}")


@app.get("/api/page/analytics")
def api_page_analytics():
    acc = current_account()
    try:
        days = int(request.args.get("days", 7))
    except ValueError:
        days = 7
    r = pagestats.report(acc["id"], days)
    page = store.load_page(acc["id"]) or default_page(acc)
    titles = {it["id"]: it["title"] for it in page.get("items", [])}
    titles.update({"fb_" + f["id"]: "Freebie: " + (f.get("t") or f.get("k", "")) for f in page.get("freebies", [])})
    r["links"] = [[titles.get(k, k), v] for k, v in r["links"]]
    return jsonify(r)


@app.put("/api/page")
def api_put_page():
    acc = current_account()
    page = clean_page(request.get_json(force=True), acc)
    store.save_page(acc["id"], page)
    return jsonify(page=page)


# ---------- Home: alerts, today so far, the AI assistant (assistant.py), agents (agents.py) ----------

def home_alerts(acc):
    """Things that need the creator now, each {text, href, tone}."""
    out, now = [], time.time()
    if acc.get("paused"):
        out.append({"text": "All automations are paused", "href": "/app/settings", "tone": "bad"})
    refused = len(engine.pending_retries(acc))
    if refused:
        out.append({"text": f"{refused} DM{'s' if refused != 1 else ''} Instagram refused: retry them", "href": "/app/activity", "tone": "bad"})
    waiting = sum(1 for t in ai_agent.threads(acc["id"]) if t.get("status") == "needs_you")
    if waiting:
        out.append({"text": f"{waiting} chat{'s' if waiting != 1 else ''} waiting for your reply", "href": "/app/inbox", "tone": "warn"})
    brands = len(agents.requests(acc, "new"))
    if brands:
        out.append({"text": f"{brands} brand request{'s' if brands != 1 else ''} waiting on you", "href": "/app/agents#brands", "tone": "warn"})
    hot = sum(1 for x in agents.leads(acc, "hot") if x["last_at"] > now - 7 * 86400)
    if hot:
        out.append({"text": f"🔥 {hot} hot lead{'s' if hot != 1 else ''} this week", "href": "/app/agents#leads", "tone": "ok"})
    carts = sum(1 for c in leads.carts(acc["id"]) if c["at"] > now - 7 * 86400 and not c.get("reminded"))
    if carts:
        out.append({"text": f"🛒 {carts} abandoned checkout{'s' if carts != 1 else ''}: send a reminder", "href": "/app/leads?segment=carts", "tone": "warn"})
    review = 0
    for c in courses.of_account(acc["id"]):
        for e in courses.students(c["id"]):
            review += sum(1 for w in (e.get("work") or {}).values() if not w.get("grade"))
    if review:
        out.append({"text": f"{review} assignment{'s' if review != 1 else ''} to review", "href": "/app/courses/assessments", "tone": "warn"})
    user = current_user()
    if user and shop.products(acc["id"]) and not shop.can_sell(user):
        out.append({"text": "Add your bank account so your products can sell", "href": "/app/payments#bank", "tone": "bad"})
    return out


def today_so_far(acc):
    """Orders, new leads and DMs today (IST) vs the same time yesterday."""
    now = time.time()
    day0 = now - (now + shop.IST) % 86400
    since = now - day0
    sales = shop.sales(acc["id"], 500)
    in_ = lambda t, a, b: a <= (t or 0) < b
    orders = sum(1 for s in sales if in_(s.get("paid_at"), day0, now))
    orders_y = sum(1 for s in sales if in_(s.get("paid_at"), day0 - 86400, day0 - 86400 + since))
    people = store.contacts(acc["id"])
    new = sum(1 for c in people if in_(c.get("first_at"), day0, now))
    new_y = sum(1 for c in people if in_(c.get("first_at"), day0 - 86400, day0 - 86400 + since))
    days = store.days(acc["id"], 2)
    dms = int(days[-1][1].get("dms", 0)) if days else 0
    dms_y = int(days[0][1].get("dms", 0)) if len(days) > 1 else 0
    revenue = round(sum(float(s.get("creator_gets") or 0) for s in sales if in_(s.get("paid_at"), day0, now)), 2)
    return {"orders": orders, "orders_y": orders_y, "revenue": revenue, "leads": new, "leads_y": new_y, "dms": dms, "dms_y": dms_y}


@app.get("/api/home")
def api_home():
    acc = current_account()
    if acc.get("demo"):
        return jsonify(alerts=[], today={"orders": 0, "orders_y": 0, "revenue": 0, "leads": 0, "leads_y": 0, "dms": 0, "dms_y": 0}, ai=False)
    return jsonify(alerts=home_alerts(acc), today=today_so_far(acc), ai=ai_agent.client() is not None)


def assistant_tools(acc):
    """The Connect Claude tools plus a few only the in-app assistant has. Viewers get read-only tools."""
    tools = mcp_v2.all_tools(acc, mcp_services(), read_only=current_role() == "viewer")
    tools += [
        {"name": "get_alerts", "title": "What needs attention", "read_only": True,
         "fn": lambda a: {"alerts": home_alerts(acc), "today": today_so_far(acc)},
         "description": "Problems and to-dos right now (refused DMs, chats waiting, brand requests, carts, assignments) and today's numbers.",
         "input_schema": {"type": "object", "properties": {}}},
    ]
    return tools


def assistant_extra(acc):
    alerts = home_alerts(acc)
    return ("Right now: " + "; ".join(a["text"] for a in alerts) + ".") if alerts else ""


@app.get("/api/assistant")
def api_assistant():
    acc = current_account()
    return jsonify(assistant.view(acc, assistant.load(acc["id"])))


@app.post("/api/assistant")
def api_assistant_ask():
    acc = current_account()
    if acc.get("demo"):
        return jsonify(error="The AI assistant isn't available in the demo."), 403
    try:
        chat = assistant.ask(acc, assistant_tools(acc), (request.get_json(force=True) or {}).get("text"), BRAND, assistant_extra(acc))
    except assistant.AssistantError as e:
        return jsonify(error=str(e)), 400
    except Exception as e:
        print(f"assistant failed: {e}")
        return jsonify(error="The AI couldn't answer right now. Try again in a minute."), 502
    return jsonify(assistant.view(acc, chat))


@app.post("/api/assistant/decide")
def api_assistant_decide():
    acc = current_account()
    try:
        chat = assistant.decide(acc, assistant_tools(acc), bool((request.get_json(force=True) or {}).get("approve")), BRAND, assistant_extra(acc))
    except assistant.AssistantError as e:
        return jsonify(error=str(e)), 400
    except Exception as e:
        print(f"assistant failed: {e}")
        return jsonify(error="The AI couldn't continue right now. Try again in a minute."), 502
    return jsonify(assistant.view(acc, chat))


@app.post("/api/assistant/reset")
def api_assistant_reset():
    acc = current_account()
    assistant.reset(acc["id"])
    return jsonify(assistant.view(acc, assistant.load(acc["id"])))


@app.get("/app/agents")
def agents_page():
    return render_app("agents.html", "agents")


@app.get("/api/agents")
def api_agents():
    acc = current_account()
    return jsonify(settings=agents.settings(acc), used={"lead": agents.used(acc, "lead"), "brand": agents.used(acc, "brand")},
                   limits={"lead": agents.cap(acc, "lead"), "brand": agents.cap(acc, "brand")}, ai=ai_agent.client() is not None,
                   allowed={"lead": plans.has(acc, "lead_agent"), "brand": plans.has(acc, "brand_agent")},
                   needs={"lead": plans.needs("lead_agent"), "brand": plans.needs("brand_agent")},
                   leads=agents.leads(acc)[:300], brands=agents.requests(acc), ai_inbox=ai_agent.settings(acc)["enabled"],
                   guard=bool((acc.get("guard") or {}).get("enabled")))


@app.put("/api/agents")
def api_agents_save():
    acc = current_account()
    if acc.get("demo"):
        return jsonify(error="Not available in the demo."), 403
    data = agents.clean(request.get_json(force=True))
    for kind, feature in (("lead", "lead_agent"), ("brand", "brand_agent")):
        if data[kind]["enabled"] and not plans.has(acc, feature):
            return locked(acc, feature)
    if (data["lead"]["enabled"] or data["brand"]["enabled"]) and ai_agent.client() is None:
        return jsonify(error="The AI isn't set up on the server yet (ANTHROPIC_API_KEY)."), 400
    acc["agents"] = data
    store.save_account(acc)
    return api_agents()


@app.put("/api/agents/brands/<chat_id>")
def api_brand_status(chat_id):
    r = agents.set_status(current_account(), chat_id, (request.get_json(force=True) or {}).get("status"))
    return (jsonify(request=r), 200) if r else (jsonify(error="Not found."), 404)


@app.post("/api/agents/leads/run")
def api_leads_run():
    """Sorts recent chats that haven't been scored yet (up to 10 per tap)."""
    acc = current_account()
    if not agents.settings(acc)["lead"]["enabled"]:
        return jsonify(error="Turn the Lead Qualifier on first."), 400
    n, week = 0, time.time() - 7 * 86400
    for t in ai_agent.threads(acc["id"]):
        if n >= 10:
            break
        if t.get("last_fan_at", 0) > week and not t.get("lead"):
            if agents.qualify(acc, t["igsid"], t.get("username", "")):
                n += 1
    return jsonify(scored=n)


@app.get("/app/leads")
def leads_page():
    return render_app("leads.html", "contacts")


def csv_safe(v):
    """A CSV cell that spreadsheets won't run as a formula."""
    v = "" if v is None else str(v)
    return "'" + v if v[:1] in ("=", "+", "-", "@", "\t", "\r") else v


def leads_filtered(acc, args):
    rows = leads.people(acc)
    seg = args.get("segment") if args.get("segment") in leads.SEGMENTS else "all"
    q, item = str(args.get("q", "")).strip().lower(), str(args.get("item", ""))
    try:
        min_spent = int(args.get("min_spent") or 0)
    except ValueError:
        min_spent = 0
    expiring = args.get("expiry")  # "soon" (within 7 days) or "ended"
    now = time.time()

    def ok(p):
        if seg not in p["segments"] or (item and not any(i["title"] == item for i in p["items"])) or p["spent"] < min_spent:
            return False
        if expiring == "soon" and not any(a["until"] and now < a["until"] < now + 7 * 86400 for a in p["access"]):
            return False
        if expiring == "ended" and not any(a["until"] and a["until"] < now for a in p["access"]):
            return False
        return not q or q in " ".join([p["name"], p["email"], p["phone"], p["username"], p["keyword"]]).lower()
    out = [p for p in rows if ok(p)]
    order = args.get("sort", "new")
    if order == "az":
        out.sort(key=lambda p: (p["name"] or p["username"] or p["email"]).lower())
    elif order == "za":
        out.sort(key=lambda p: (p["name"] or p["username"] or p["email"]).lower(), reverse=True)
    elif order == "old":
        out.sort(key=lambda p: p["first_at"] or p["last_at"])
    elif order == "spent":
        out.sort(key=lambda p: -p["spent"])
    return rows, out


@app.get("/api/leads")
def api_leads():
    acc = current_account()
    rows, out = leads_filtered(acc, request.args)
    counts = {s: sum(1 for p in rows if s in p["segments"]) for s in leads.SEGMENTS}
    items = sorted({i["title"] for p in rows for i in p["items"]})
    return jsonify(leads=out[:1000], total=len(out), counts=counts, items=items)


@app.get("/api/leads.csv")
def api_leads_csv():
    if locked(current_account(), "cart_tools"):
        return locked(current_account(), "cart_tools")
    _, out = leads_filtered(current_account(), request.args)
    buf = io.StringIO()
    w = csv.writer(buf)
    for r in leads.csv_rows(out):
        w.writerow([csv_safe(x) for x in r])
    return Response(buf.getvalue(), mimetype="text/csv", headers={"Content-Disposition": 'attachment; filename="leads.csv"'})


@app.post("/api/leads/carts/<oid>/remind")
def api_cart_remind(oid):
    if locked(current_account(), "cart_tools"):
        return locked(current_account(), "cart_tools")
    try:
        leads.remind(current_account(), oid)
    except shop.ShopError as e:
        return jsonify(error=str(e)), 400
    return jsonify(ok=True)


@app.get("/app/payments")
def payments_page():
    return render_app("payments.html", "payments")


def payments_window(args):
    """(start, end) epoch seconds for ?period=today|yesterday|7|30|90|life|custom (&from=&to= as YYYY-MM-DD, IST)."""
    now = time.time()
    day0 = now - (now + shop.IST) % 86400
    period = args.get("period", "30")
    if period == "today":
        return day0, now
    if period == "yesterday":
        return day0 - 86400, day0
    if period == "life":
        return 0, now
    if period == "custom":
        a, b = courses._date(args.get("from")), courses._date(args.get("to"))
        if a is not None and b is not None and a <= b:
            return a, b + 86400
    days = {"7": 7, "30": 30, "90": 90}.get(period, 30)
    return day0 - (days - 1) * 86400, now


@app.get("/api/payments")
def api_payments():
    """Payments (like SuperProfile → Payments): earnings for a period and product, the chart, transactions and abandoned checkouts."""
    acc = current_account()
    if acc.get("demo"):
        return jsonify(demo=True)
    return jsonify(payments_summary(acc, request.args, current_user()))


def payments_summary(acc, args, user=None):
    start, end = payments_window(args)
    item = str(args.get("item", ""))
    sales = [s for s in shop.sales(acc["id"], 500) if not item or s.get("title") == item]
    inside = [s for s in sales if start <= s.get("paid_at", 0) < end]
    span = end - start
    before = [s for s in sales if start - span <= s.get("paid_at", 0) < start] if start else []
    earned = round(sum(float(s.get("creator_gets") or 0) for s in inside), 2)
    prev = round(sum(float(s.get("creator_gets") or 0) for s in before), 2)
    # one point per IST day (or per month for long periods)
    first = start or min([s.get("paid_at", end) for s in sales] or [end])
    days = max(1, int((end - first) // 86400) + 1)
    step = 86400 if days <= 120 else 30 * 86400
    series, t = [], first - (first + shop.IST) % 86400
    while t < end and len(series) < 400:
        series.append({"t": int(t), "v": round(sum(float(s.get("creator_gets") or 0) for s in inside if t <= s.get("paid_at", 0) < t + step), 2)})
        t += step
    cart = [c for c in leads.carts(acc["id"]) if start <= c["at"] < end and (not item or c["title"] == item)]
    pay = shop.payout(user) if user else {}
    return dict(earned=earned, gross=sum(int(s.get("price") or 0) for s in inside), count=len(inside),
                   change=round(100 * (earned - prev) / prev) if prev else None, series=series, step=step,
                   transactions=inside, abandoned=cart, items=sorted({s.get("title", "") for s in shop.sales(acc["id"], 500)}),
                   payout={"status": pay.get("status", ""), "bank": pay.get("bank", ""), "name": pay.get("name", ""), "ifsc": pay.get("ifsc", "")})


@app.get("/api/payments/payouts")
def api_payouts():
    """The creator's share of each recent sale and whether it has reached their bank (Razorpay Route transfers)."""
    return jsonify(payouts=payouts_list(current_account()))


def payouts_list(acc):
    out = []
    for s in shop.sales(acc["id"], 30):
        o = store.get_json(f"s:shoporder:{s['id']}") or {}
        if not o.get("payment_id"):
            continue
        out.append({"id": s["id"], "title": s.get("title", ""), "email": s.get("email", ""), "paid_at": s.get("paid_at"),
                    "amount": s.get("creator_gets"), "status": shop.transfer_status(o)})
    return out


@app.get("/api/payments.csv")
def api_payments_csv():
    acc = current_account()
    if locked(acc, "cart_tools"):
        return locked(acc, "cart_tools")
    start, end = payments_window(request.args)
    item = str(request.args.get("item", ""))
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Date (IST)", "Name", "Email", "Phone", "Item", "Type", "Paid (₹)", "You get (₹)", "Order"])
    for s in shop.sales(acc["id"], 500):
        if start <= s.get("paid_at", 0) < end and (not item or s.get("title") == item):
            w.writerow([csv_safe(x) for x in [time.strftime("%Y-%m-%d %H:%M", time.gmtime(s["paid_at"] + shop.IST)), s.get("name", ""), s.get("email", ""),
                                              s.get("phone", ""), s.get("title", ""), s.get("type", ""), s.get("price", 0), s.get("creator_gets", 0), s.get("id", "")]])
    return Response(buf.getvalue(), mimetype="text/csv", headers={"Content-Disposition": 'attachment; filename="payments.csv"'})


@app.get("/api/contacts")
def api_contacts():
    rows = store.contacts(current_account()["id"])
    for c in rows:
        c["key"] = store.contact_key(c.get("username"), c.get("igsid", ""))
    return jsonify(contacts=rows)


@app.put("/api/contacts/tags")
def api_contact_tags():
    data = request.get_json(force=True)
    tags = data.get("tags") or []
    if isinstance(tags, str):
        tags = tags.split(",")
    c = store.set_contact_tags(current_account()["id"], str(data.get("key", "")), tags)
    if not c:
        return jsonify(error="Contact not found."), 404
    return jsonify(contact=c)


@app.get("/api/contacts.csv")
def api_contacts_csv():
    acc = current_account()
    if locked(acc, "cart_tools"):
        return locked(acc, "cart_tools")
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["username", "email", "phone", "followed", "keyword", "tags", "interactions", "first_seen", "last_seen"])
    tag = request.args.get("tag", "").strip().lower()
    for c in store.contacts(acc["id"]):
        if tag and tag not in (c.get("tags") or []):
            continue
        fmt = lambda t: datetime.fromtimestamp(t or 0, timezone.utc).strftime("%Y-%m-%d %H:%M")
        w.writerow([c.get("username", ""), c.get("email", ""), c.get("phone", ""), "yes" if c.get("followed") else "no", c.get("keyword", ""),
                    "; ".join(c.get("tags") or []), c.get("interactions", 0), fmt(c.get("first_at")), fmt(c.get("last_at"))])
    return out.getvalue(), 200, {"Content-Type": "text/csv; charset=utf-8",
                                 "Content-Disposition": f"attachment; filename={acc.get('username', 'contacts')}-contacts.csv"}


# ---------- MCP server: creators run ReplyInbox from Claude ----------

import mcp_tools  # noqa: E402
import mcp_v2  # noqa: E402
from mcp_protocol import handle_http  # noqa: E402


def mcp_account():
    """(account, read_only) for the key in the Authorization header or ?key=; (None, False) when unknown."""
    header = request.headers.get("Authorization", "")
    key = header[7:].strip() if header.lower().startswith("bearer ") else request.args.get("key", "")
    if not key.startswith("ri_"):
        return None, False
    value = store.redis("GET", f"s:mcpkey:{hashlib.sha256(key.encode()).hexdigest()}") or ""
    ig_id, _, mode = value.partition("|")
    acc = store.load_account(ig_id) if ig_id else None
    return acc, mode == "read"


def mcp_services():
    """The app functions the MCP tools share with the dashboard."""
    from types import SimpleNamespace
    return SimpleNamespace(save_rule=save_rule, build_report=build_report, delete_rule=delete_rule, copy_rule=copy_rule,
                           rule_insights=rule_insights, sales_summary=sales_summary, add_product=add_product,
                           broadcast_batch=broadcast_batch, inbox_send=inbox_send, set_welcome=set_welcome, update_ai=update_ai,
                           clean_page=clean_page, default_page=default_page, site_url=site_url, course_public_url=course_public_url,
                           leads_filtered=leads_filtered, payments_summary=payments_summary, payouts_list=payouts_list,
                           home_alerts=home_alerts, today_so_far=today_so_far, owner_of=users.owner_of)


@app.route("/mcp", methods=["GET", "POST", "DELETE"])
def mcp_endpoint():
    acc, read_only = mcp_account()
    if not acc:
        return jsonify(error=f"Missing or wrong key. Create a new Claude link in your {BRAND} dashboard."), 401
    k = f"s:mcprate:{acc['id']}:{int(time.time() // 60)}"
    if (store.redis("INCR", k) or 0) > 240:
        return jsonify(error="Too many requests. Wait a minute."), 429
    store.redis("EXPIRE", k, 120)
    if not plans.has(acc, "mcp"):
        return jsonify(error=f"Connect Claude is on the {plans.needs('mcp')} plan and up. Upgrade in your {BRAND} dashboard → Plan & billing."), 403
    if request.method != "POST":
        return "", 405, {"Allow": "POST"}
    owner = users.owner_of(acc)
    multi = plans.has(acc, "mcp_multi") and owner and len(users.accounts(owner)) > 1
    tools = (mcp_v2.agency(acc, mcp_services(), users.accounts(owner), read_only) if multi
             else mcp_v2.all_tools(acc, mcp_services(), read_only=read_only))
    status, body = handle_http(request.get_data(), tools, BRAND.lower(), mcp_tools.instructions(acc, BRAND, read_only, multi=bool(multi)),
                               prompts=mcp_tools.prompts() + mcp_v2.prompts())
    return (jsonify(body), status) if body is not None else ("", status)


@app.route("/api/mcp-key", methods=["GET", "POST", "DELETE"])
def api_mcp_key():
    acc = current_account()
    if request.method == "GET":
        return jsonify(active=bool(acc.get("mcp_key_hash")) and plans.has(acc, "mcp"), read_only=acc.get("mcp_mode") == "read",
                       allowed=plans.has(acc, "mcp"), needs=plans.needs("mcp"))
    if request.method == "POST" and not plans.has(acc, "mcp"):
        return locked(acc, "mcp")
    if acc.get("mcp_key_hash"):  # a new link (or disconnect) turns off the old one
        store.redis("DEL", f"s:mcpkey:{acc['mcp_key_hash']}")
        acc["mcp_key_hash"] = ""
    if request.method == "POST":
        key = "ri_" + secrets.token_urlsafe(32)  # shown once; only its hash is stored
        acc["mcp_key_hash"] = hashlib.sha256(key.encode()).hexdigest()
        acc["mcp_mode"] = "read" if (request.get_json(silent=True) or {}).get("read_only") else "full"
        store.redis("SET", f"s:mcpkey:{acc['mcp_key_hash']}", acc["id"] + ("|read" if acc["mcp_mode"] == "read" else ""))
    store.save_account(acc)
    if request.method == "DELETE":
        return jsonify(active=False)
    return jsonify(active=True, key=key, url=f"{base_url()}/mcp?key={key}", endpoint=f"{base_url()}/mcp",
                   read_only=acc["mcp_mode"] == "read")


# ---------- webhook (comments + DMs for every connected account) ----------

@app.get("/webhook")
def verify_webhook():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge", "")
    abort(403)


def valid_signature(raw, header):
    expected = "sha256=" + hmac.new(IG_APP_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return bool(IG_APP_SECRET) and hmac.compare_digest(expected, header or "")


def run_task(fn, *args):
    # Serverless functions freeze once they respond, so work happens before the reply there.
    if SERVERLESS:
        fn(*args)
    else:
        threading.Thread(target=fn, args=args).start()


@app.post("/webhook")
def receive_webhook():
    if not valid_signature(request.get_data(), request.headers.get("X-Hub-Signature-256")):
        abort(403)
    engine.dispatch(request.get_json(silent=True) or {}, run_task)
    run_task(send_followups_safely)
    return "ok"


def send_followups_safely():
    try:
        engine.send_due_followups()
    except Exception:
        pass  # never fail a webhook because of a follow-up


@app.get("/cron/followups")
def cron_followups():
    """Also sends due follow-ups (add an hourly cron on Vercel Pro; webhooks trigger it too)."""
    if not CRON_SECRET or request.headers.get("Authorization") != f"Bearer {CRON_SECRET}":
        abort(401)
    return jsonify(sent=engine.send_due_followups(100))


# ---------- Meta callbacks: app removed / data deletion request ----------

def parse_signed_request(signed):
    try:
        sig, payload = signed.split(".", 1)
        pad = lambda s: s + "=" * (-len(s) % 4)
        expected = hmac.new(IG_APP_SECRET.encode(), payload.encode(), hashlib.sha256).digest()
        if not IG_APP_SECRET or not hmac.compare_digest(base64.urlsafe_b64decode(pad(sig)), expected):
            return None
        return json.loads(base64.urlsafe_b64decode(pad(payload)))
    except Exception:
        return None


def forget_user(user_id):
    """Deletes the account Meta names, by Instagram user ID or app-scoped ID."""
    user_id = str(user_id)
    for ig_id in store.account_ids():
        acc = store.load_account(ig_id)
        if acc and user_id in (acc.get("id"), acc.get("asid")):
            youtube.disconnect(acc)
            users.remove(users.owner_of(acc), ig_id)
            store.delete_account(ig_id)


@app.post("/meta/deauthorize")
def meta_deauthorize():
    data = parse_signed_request(request.form.get("signed_request", ""))
    if not data:
        abort(400)
    forget_user(data.get("user_id", ""))
    return "ok"


@app.post("/meta/data-deletion")
def meta_data_deletion():
    data = parse_signed_request(request.form.get("signed_request", ""))
    if not data:
        abort(400)
    forget_user(data.get("user_id", ""))
    code = secrets.token_hex(8)
    store.redis("SET", f"s:deleted:{code}", 1, "EX", 90 * 86400)
    return jsonify(url=f"{base_url()}/deletion?code={code}", confirmation_code=code)


# ---------- cron: keep every login alive ----------

@app.get("/cron/refresh-tokens")
def cron_refresh_tokens():
    if not CRON_SECRET or request.headers.get("Authorization") != f"Bearer {CRON_SECRET}":
        abort(401)
    engine.send_due_followups(100)
    try:
        shop.send_reminders()  # events and bookings happening in the next 24 hours
    except Exception as e:
        print(f"shop reminders failed: {e}")
    try:
        courses.send_sequences()  # course emails N days after enrolling
    except Exception as e:
        print(f"course emails failed: {e}")
    for ig_id in store.account_ids():  # refused comment DMs get another try once a day
        acc = store.load_account(ig_id)
        if acc and not acc.get("demo") and engine.pending_retries(acc):
            try:
                engine.retry_failed_dms(acc)
            except Exception:
                pass
    done = failed = 0
    for ig_id in store.account_ids():
        acc = store.load_account(ig_id)
        # Long-lived tokens last 60 days and can be renewed once they're a day old: renew weekly.
        if not acc or time.time() - acc.get("token_at", 0) < 7 * 86400:
            continue
        try:
            r = requests.get("https://graph.instagram.com/refresh_access_token", timeout=20, params={
                "grant_type": "ig_refresh_token", "access_token": acc["token"]})
            r.raise_for_status()
            acc.update(token=r.json()["access_token"], token_at=int(time.time()))
            store.save_account(acc)
            done += 1
        except Exception as e:
            failed += 1
            store.log_activity(ig_id, "", "", "", "token_refresh", "error",
                               f"Couldn't renew the Instagram login. Log in again. | {e}")
            engine.alert(acc, "renew", "Your Instagram login needs renewing ⚠️",
                         "Log in with Instagram again soon, or Auto DMs will stop when the login expires.", "/app")
    return jsonify(refreshed=done, failed=failed)


# ---------- owner view ----------

def owner_ok():
    """The owner's password (HTTP basic auth). 10 wrong tries from one IP lock it for 15 minutes."""
    auth = request.authorization
    if not OWNER_PASSWORD or not auth:
        return False
    k = f"s:ownerfail:{client_ip()}"
    if int(store.redis("GET", k) or 0) >= 10:
        return False
    if hmac.compare_digest(auth.password or "", OWNER_PASSWORD):
        return True
    store.redis("INCR", k)
    store.redis("EXPIRE", k, 900)
    return False


@app.post("/owner/plan")
def owner_set_plan():
    """Gives a login (or an account from before logins) a plan by hand: for 30/90/365 days, or with no end (days 0).
    The same plan given again adds the days to the time left. JSON only, so a cross-site form can't trigger it."""
    if not owner_ok():
        return ("Login required", 401, {"WWW-Authenticate": 'Basic realm="owner"'})
    if not request.is_json:
        return jsonify(error="JSON required"), 415
    data = request.get_json(force=True)
    plan, days = data.get("plan"), int(data.get("days") or 0) if str(data.get("days") or 0).isdigit() else -1
    if plan not in plans.PLANS or days < 0 or days > 3660:
        return jsonify(error="Pick a plan and a length."), 400
    owner = users.get(str(data.get("user", ""))) if data.get("user") else None
    acc = None if owner else store.load_account(str(data.get("id", "")))
    if not owner and acc:
        owner = users.owner_of(acc)
    if not owner and not acc:
        return jsonify(error="Unknown login or account."), 400
    target = owner or acc
    now = time.time()
    until = None
    if days and plan != "free":
        start = target.get("plan_until") or 0
        start = start if target.get("plan") == plan and start > now else now
        until = int(start + days * 86400)
    if owner:  # the plan belongs to the login and covers all its Instagram accounts
        users.set_plan(owner, plan, until)
        return jsonify(user=owner["id"], plan=users.current_plan(users.get(owner["id"])), until=until)
    acc["plan"], acc["plan_until"] = plan, until
    store.save_account(acc)
    return jsonify(id=acc["id"], plan=plans.plan_of(acc), until=until)


@app.post("/owner/user/delete")
def owner_delete_user():
    """Deletes a login and every Instagram account under it (same clean-up as Disconnect). JSON only."""
    if not owner_ok():
        return ("Login required", 401, {"WWW-Authenticate": 'Basic realm="owner"'})
    if not request.is_json:
        return jsonify(error="JSON required"), 415
    user = users.get(str((request.get_json(force=True) or {}).get("user", "")))
    if not user:
        return jsonify(error="Unknown login."), 400
    removed = 0
    for acc in users.accounts(user):
        remove_account(acc)
        removed += 1
    users.delete(user)
    return jsonify(ok=True, accounts_removed=removed)


@app.post("/owner/remove")
def owner_remove():
    """Removes a connected account and its data (same as the person pressing Disconnect). JSON only."""
    if not owner_ok():
        return ("Login required", 401, {"WWW-Authenticate": 'Basic realm="owner"'})
    if not request.is_json:
        return jsonify(error="JSON required"), 415
    acc = store.load_account(str((request.get_json(force=True) or {}).get("id", "")))
    if not acc:
        return jsonify(error="Unknown account."), 400
    if demo.is_demo(acc):
        store.redis("SREM", "s:accounts", acc["id"])  # the demo is recreated in memory when /demo is opened
    else:
        remove_account(acc)
    return jsonify(ok=True)


@app.post("/owner/payout")
def owner_payout():
    """Marks a referral payout as sent (after paying it by UPI). JSON only."""
    if not owner_ok():
        return ("Login required", 401, {"WWW-Authenticate": 'Basic realm="owner"'})
    if not request.is_json:
        return jsonify(error="JSON required"), 415
    d = request.get_json(force=True) or {}
    try:
        return jsonify(payout=referrals.mark_paid(str(d.get("user", "")), str(d.get("id", ""))))
    except referrals.ReferralError as e:
        return jsonify(error=str(e)), 400


@app.get("/admin")
def admin_alias():
    return redirect("/owner")


@app.get("/owner")
def owner():
    if not owner_ok():
        return ("Login required", 401, {"WWW-Authenticate": 'Basic realm="owner"'})
    rows = []
    for ig_id in store.account_ids():
        acc = store.load_account(ig_id)
        if acc and not demo.is_demo(acc):  # the /demo account isn't a customer
            c = store.counts(ig_id)
            owner = users.owner_of(acc)
            rows.append({**public_account(acc), "invite": acc.get("invite", ""), "blocked": engine.is_blocked(acc),
                         "owner_email": owner.get("email", "") if owner else "", "owner_id": owner["id"] if owner else "",
                         "plan_until": (owner or acc).get("plan_until"),
                         "limit": users.limit(owner) if owner else 1,
                         "dms_month": c.get(f"dms:{engine.month()}", 0), "dms": c.get("dms", 0),
                         "rules": len(store.load_rules(ig_id).get("reels", {})), "plan_id": plans.plan_of(acc),
                         "plan_set": acc.get("plan") or "free", "referral_pro": acc.get("pro_until", 0) > time.time()})
    rows.sort(key=lambda r: -(r.get("created") or 0))
    # one plan per login: group its Instagram accounts under it (accounts from before logins stand alone)
    logins = {}
    for r in rows:
        acc_owner = r["owner_id"] or "acc:" + r["id"]
        g = logins.setdefault(acc_owner, {"key": acc_owner, "email": r["owner_email"], "plan_set": r["plan_set"],
                                          "plan_id": r["plan_id"], "referral_pro": r["referral_pro"], "accounts": [],
                                          "limit": r["limit"], "created": r.get("created") or 0, "user": r["owner_id"],
                                          "until": r.get("plan_until")})
        g["accounts"].append(r)
    # logins that signed up but haven't connected Instagram yet
    for uid in users.all_ids():
        if uid in logins:
            continue
        u = users.get(uid)
        if u:
            logins[uid] = {"key": uid, "email": u.get("email", ""), "plan_set": u.get("plan") or "free",
                           "plan_id": users.current_plan(u), "referral_pro": False, "accounts": [], "limit": users.limit(u),
                           "created": u.get("created") or 0, "user": uid, "until": u.get("plan_until")}
    groups = sorted(logins.values(), key=lambda g: -g["created"])
    feedback = [json.loads(x) for x in store.redis("LRANGE", "s:feedback", 0, 99) or []]
    by_plan = {k: sum(1 for g in groups if g["plan_id"] == k) for k in plans.PLANS}
    # MRR counts only plans set by hand (paying); free Pro months from referrals bring no money
    mrr = sum(plans.PLANS[g["plan_set"]]["price"] for g in groups if g["plan_set"] in plans.PLANS and g["plan_id"] == g["plan_set"])
    payments = [json.loads(x) for x in store.redis("LRANGE", "s:payments", 0, 49) or []]
    month_start = time.mktime(time.strptime(time.strftime("%Y-%m-01"), "%Y-%m-%d"))
    paid_month = sum(p["amount"] for p in payments if p.get("paid_at", 0) >= month_start)
    return render_template("owner.html", feedback=feedback, rows=rows, groups=groups, now=time.time(), plans=plans.PLANS, by_plan=by_plan, mrr=mrr, locks=plans.LOCKS_ON,
                           payments=payments, paid_month=paid_month, payouts=referrals.payout_requests(), billing_ready=billing.ready(), billing_test=billing.test_mode())


# ---------- public link-in-bio page: replyinbox.in/<username> ----------

USERNAME_RE = re.compile(r"[A-Za-z0-9._]{1,30}")


def public_page(username):
    if not USERNAME_RE.fullmatch(username or ""):
        abort(404)
    acc = store.account_by_username(username)
    if not acc and username.lower() == demo.USERNAME:  # demo data lives in memory without a database
        acc = demo.seed()
    page = store.load_page(acc["id"]) if acc else None
    if acc and not page:
        mine = current_account()
        if mine and mine["id"] == acc["id"]:  # the owner sees a preview before the first save; others get 404
            page = default_page(acc)
    if not acc or not page:
        abort(404)
    return acc, page


@app.template_filter("compact")
def compact_number(n):
    """28709 → 28K, 1250000 → 1.2M (follower badges)."""
    n = int(n or 0)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    if n >= 10_000:
        return f"{n // 1000}K"
    if n >= 1000:
        return f"{n / 1000:.1f}".rstrip("0").rstrip(".") + "K"
    return str(n)


@app.get("/<username>")
def bio_page(username):
    acc, page = public_page(username)
    items = [it for it in page.get("items", []) if it.get("enabled", True)]
    items.sort(key=lambda it: not it.get("featured"))
    socials_map = page.get("socials") or {}
    social_links = [(k, u) for k in SOCIALS for u in [social_url(k, socials_map.get(k))] if u]
    if not any(k == "instagram" for k, _ in social_links):
        social_links.insert(0, ("instagram", f"https://www.instagram.com/{acc.get('username', '')}/"))
    page = {**page, "theme": theme_of(page)}
    if not plans.has(acc, "page_pro"):  # a plan that ended: back to the theme's own look
        page.update(accent="", layout="single", seo={})
    page["hide_brand"] = bool(page.get("hide_brand")) and plans.has(acc, "remove_branding")
    if (current_account() or {}).get("id") != acc["id"]:  # the owner's own visits don't count
        ip = client_ip()
        from urllib.parse import unquote
        try:
            pagestats.visit(acc["id"], ip, request.headers.get("User-Agent", ""), request.headers.get("x-vercel-ip-country", ""),
                            unquote(request.headers.get("x-vercel-ip-city", "")), request.referrer or "")
        except Exception as e:  # analytics must never break the page
            print(f"page visit not counted: {e}")
    return render_template("bio.html", acc=public_account(acc), page=page, items=items, socials_map=socials_map, social_links=social_links,
                           joined=request.args.get("joined") == "1", error=request.args.get("error", ""))


@app.post("/<username>/join")
def bio_signup(username):
    """The signup form on a link page: saves the email / phone to the creator's Contacts."""
    acc, page = public_page(username)
    form = page.get("signup") or {}
    if not form.get("enabled"):
        abort(404)
    if request.form.get("website"):  # hidden field only bots fill in
        return redirect(f"/{username}?joined=1")
    ask = form.get("ask", "email")
    email = engine.parse_email(request.form.get("email", "")) if ask in ("email", "both") else ""
    phone = engine.parse_phone(request.form.get("phone", "")) if ask in ("phone", "both") else ""
    if (ask in ("email", "both") and not email) or (ask in ("phone", "both") and not phone):
        return redirect(f"/{username}?error=invalid#join")
    ip = client_ip()
    if not store.claim(f"s:seen:signup:{acc['id']}:{ip}:{int(time.time() // 60)}", 120):
        return redirect(f"/{username}?error=slow#join")  # one signup per minute from the same place
    handle = clean_ref(request.form.get("instagram", ""))
    store.touch_contact(acc["id"], handle, "" if handle else f"web:{email or phone}", source="bio_page", email=email, phone=phone)
    store.count(acc["id"], "page_signups")
    engine.send_hook(acc, "lead", {"username": handle, "email": email, "phone": phone, "automation": "link page"})
    if (acc.get("notify") or {}).get("lead", True):
        push.notify(acc, "New signup 🎉", f"{email or phone} joined from your link page", "/app/contacts")
    return redirect(f"/{username}?joined=1#join")


@app.get("/<username>/go/<item_id>")
def bio_click(username, item_id):
    acc, page = public_page(username)
    item = next((it for it in page.get("items", []) if it.get("id") == item_id and it.get("enabled", True)), None)
    if not item:
        abort(404)
    store.count_click(acc["id"], item_id)
    if (current_account() or {}).get("id") != acc["id"]:
        try:
            secs = float(request.args.get("t", "")) if request.args.get("t") else None
        except ValueError:
            secs = None
        try:
            pagestats.click(acc["id"], item_id, request.headers.get("User-Agent", ""), secs)
        except Exception as e:
            print(f"page click not counted: {e}")
    return redirect(item["url"])


@app.get("/<username>/free")
def bio_freebies(username):
    """All of a creator's freebies on one page: search by the reel keyword, filter by topic."""
    acc, page = public_page(username)
    freebies = [f for f in page.get("freebies", []) if f.get("enabled", True)]
    if not freebies:
        abort(404)
    topics = sorted({f["topic"] for f in freebies if f.get("topic")})
    page = {**page, "theme": theme_of(page)}
    return render_template("free.html", acc=public_account(acc), page=page, freebies=freebies, topics=topics,
                           socials_map=page.get("socials") or {})


@app.get("/<username>/free/<fid>")
def bio_freebie_click(username, fid):
    acc, page = public_page(username)
    fb = next((f for f in page.get("freebies", []) if f.get("id") == fid and f.get("enabled", True)), None)
    if not fb:
        abort(404)
    store.count_click(acc["id"], "fb_" + fid)
    if (current_account() or {}).get("id") != acc["id"]:
        try:
            pagestats.click(acc["id"], "fb_" + fid, request.headers.get("User-Agent", ""))
        except Exception as e:
            print(f"freebie click not counted: {e}")
    return redirect(fb["u"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8100")), debug=True)
