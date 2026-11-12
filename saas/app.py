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
from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for

import ai_agent
import demo
import push
import engine
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
app.config.update(SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=SERVERLESS,
                  SESSION_COOKIE_HTTPONLY=True, PERMANENT_SESSION_LIFETIME=30 * 86400)


def base_url():
    return PUBLIC_URL or request.host_url.rstrip("/")


def current_account():
    uid = session.get("uid")
    acc = store.load_account(uid)
    if not acc and uid == demo.DEMO_ID:  # demo data lives in memory without a database: recreate it
        acc = demo.seed()
    if acc and session.get("member") and not team_member(acc, session["member"]):
        return None  # removed from the team
    return acc


# ---------- team: managers and viewers who log in with an invite link ----------

ROLES = {"manager": "Manager", "viewer": "Viewer"}
OWNER_ONLY = ("/api/disconnect", "/api/team", "/api/mcp-key", "/api/integrations")
MAX_TEAM = 5


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


def public_account(acc):
    """What the dashboard may see: never the token."""
    return {**{k: acc.get(k) for k in ("id", "username", "name", "pic", "followers", "created", "paused", "demo", "plan",
                                        "pro_until")}, "pro": store.is_pro(acc)}


# Sections of the creator app. Core ones are always on; the rest can be switched off on the Apps page.
SECTIONS = [
    ("home", "/app", "Home", True), ("automations", "/app/automations", "Auto DM", True),
    ("inbox", "/app/inbox", "AI Inbox", False), ("activity", "/app/activity", "Activity", True),
    ("report", "/app/report", "Reel report", False), ("links", "/app/links", "Link in bio", False),
    ("contacts", "/app/contacts", "Contacts", False), ("giveaway", "/app/giveaway", "Giveaway", False), ("apps", "/app/apps", "Apps", True),
    ("settings", "/app/settings", "Settings", True),
]
DEFAULT_APPS = {"inbox": True, "report": True, "links": True, "contacts": True, "giveaway": True}


def apps_of(acc):
    return {**DEFAULT_APPS, **(acc.get("apps") or {})}


def render_app(template, active, **extra):
    acc = current_account()
    if not acc:
        return redirect(url_for("landing"))
    on = apps_of(acc)
    nav = [(key, href, label) for key, href, label, core in SECTIONS if core or on.get(key)]
    return render_template(template, acc=public_account(acc), active=active, nav=nav, apps=on, role=current_role(),
                           linked=[a for a in linked_accounts() if a["id"] != acc["id"]],
                           page_url=f"{request.host_url.rstrip('/')}/{acc.get('username', '')}", **extra)


@app.context_processor
def brand():
    return {"brand": BRAND, "contact_email": CONTACT_EMAIL, "public_url": base_url() if request else ""}


@app.before_request
def guard():
    # Logged-in API calls that change data must be JSON: a cross-site form can't send that without CORS.
    if request.path.startswith("/api/"):
        if not current_account():
            return jsonify(error="Please log in again."), 401
        if request.method in ("POST", "PUT", "DELETE") and not request.is_json:
            return jsonify(error="JSON required"), 415
        blocked = role_blocks(request.path, request.method)
        if blocked:
            return jsonify(error=blocked), 403


# ---------- pages ----------

@app.get("/")
def landing():
    if current_account():
        return redirect(url_for("dashboard"))
    ref = clean_ref(request.args.get("ref"))
    if ref:
        session["ref"] = ref
    referrer = store.account_by_username(session["ref"]) if session.get("ref") else None
    return render_template("landing.html", invite_only=SIGNUPS == "invite", error=request.args.get("error", ""),
                           referrer=referrer.get("username") if referrer else "")


# ---------- referrals: invite a creator, both get a free month of Pro ----------

REFERRAL_DAYS = 30
MAX_REFERRAL_REWARDS = 12  # free months one creator can earn by inviting


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


def reward_referral(new_acc):
    """Called once, when a new account is created after following an invite link."""
    referrer = store.account_by_username(session.pop("ref", "") or "")
    if not referrer or referrer["id"] == new_acc["id"] or referrer.get("demo"):
        return
    new_acc["referred_by"] = referrer["id"]
    store.grant_pro_days(new_acc, REFERRAL_DAYS)
    joined = referrer.setdefault("referrals", [])
    joined.append({"username": new_acc.get("username", ""), "at": int(time.time())})
    if sum(1 for r in joined if r.get("rewarded", True)) <= MAX_REFERRAL_REWARDS:
        store.grant_pro_days(referrer, REFERRAL_DAYS)
    else:
        joined[-1]["rewarded"] = False
    store.save_account(referrer)


@app.get("/api/referrals")
def api_referrals():
    acc = current_account()
    joined = acc.get("referrals") or []
    return jsonify(link=f"{base_url()}/r/{acc.get('username', '')}", joined=joined[::-1],
                   months_earned=sum(1 for r in joined if r.get("rewarded", True)), max_months=MAX_REFERRAL_REWARDS,
                   pro=store.is_pro(acc), pro_until=acc.get("pro_until", 0), plan=acc.get("plan", ""))


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
def legal():
    return render_template("legal.html", page=request.path.strip("/"))


@app.get("/deletion")
def deletion_status():
    code = request.args.get("code", "")
    done = bool(code) and store.redis("GET", f"s:deleted:{code}")
    return render_template("legal.html", page="deletion", code=code, done=done)


# ---------- Login with Instagram ----------

@app.get("/login")
def login():
    adding = bool(session.get("accounts")) and request.args.get("add") == "1"
    if SIGNUPS == "invite" and not adding:
        code = request.args.get("invite", "").strip().upper()
        if code not in INVITE_CODES:
            return redirect(url_for("landing", error="invite"))
        session["invite"] = code
    if not IG_APP_ID:
        return redirect(url_for("landing", error="setup"))
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
    if request.args.get("error") or not request.args.get("code"):
        return redirect(url_for("landing", error="denied"))
    if request.args.get("state") != session.pop("oauth_state", None):
        return redirect(url_for("landing", error="state"))
    try:
        token = exchange_code(request.args["code"])
        r = requests.get(f"{engine.GRAPH}/me", timeout=20, params={
            "access_token": token,
            "fields": "id,user_id,username,name,profile_picture_url,followers_count,account_type"})
        r.raise_for_status()
        me = r.json()
    except Exception as e:
        app.logger.warning("Instagram login failed: %s", e)
        return redirect(url_for("landing", error="login"))

    ig_id = str(me["user_id"])  # the ID Instagram puts in webhooks ("entry.id")
    existing = store.load_account(ig_id)
    acc = existing or {"id": ig_id, "created": int(time.time()), "paused": False}
    acc.update(asid=str(me.get("id", "")), username=me.get("username", ""), name=me.get("name", ""),
               pic=me.get("profile_picture_url", ""), followers=me.get("followers_count"),
               token=token, token_at=int(time.time()), invite=session.pop("invite", acc.get("invite", "")))
    if not existing:
        reward_referral(acc)
    store.save_account(acc)
    store.redis("DEL", store.account_key(ig_id, "token_dead"))
    try:  # without this subscription Instagram sends no comment/DM events for the account
        try:
            engine.Instagram(acc).post("me/subscribed_apps", subscribed_fields=LIVE_FIELDS)
        except RuntimeError:
            engine.Instagram(acc).post("me/subscribed_apps", subscribed_fields=WEBHOOK_FIELDS)
    except Exception as e:
        store.log_activity(ig_id, "", "", "", "connect", "error",
                           f"Couldn't turn on comment and DM events: {e}")
    session.permanent = True
    linked = [a for a in session.get("accounts", []) if a != ig_id] if not session.get("member") else []
    session.pop("member", None)
    session["accounts"] = ([ig_id] + linked)[:MAX_LINKED]
    session["uid"] = ig_id
    return redirect(url_for("dashboard"))


# ---------- several Instagram accounts in one login ----------

MAX_LINKED = 10


def linked_accounts():
    """The Instagram accounts this browser logged in to as the owner (for the account switcher)."""
    out = []
    for ig_id in session.get("accounts", []):
        acc = store.load_account(ig_id)
        if acc:
            out.append({"id": ig_id, "username": acc.get("username", ""), "pic": acc.get("pic", "")})
    return out


@app.post("/api/switch")
def api_switch():
    target = str(request.get_json(force=True).get("id", ""))
    if target not in session.get("accounts", []) or not store.load_account(target):
        return jsonify(error="Log in to that account first."), 403
    session.pop("member", None)
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
    if len(team) >= MAX_TEAM:
        return jsonify(error=f"A team can have up to {MAX_TEAM} people."), 400
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
    session.clear()
    return redirect(url_for("landing"))


@app.post("/api/disconnect")
def api_disconnect():
    acc = current_account()
    if demo.is_demo(acc):
        session.clear()
        return jsonify(ok=True)
    try:  # stop Instagram sending this account's events; best effort
        requests.delete(f"{engine.GRAPH}/me/subscribed_apps", params={"access_token": acc["token"]}, timeout=10)
    except Exception:
        pass
    store.delete_account(acc["id"])
    others = [a for a in session.get("accounts", []) if a != acc["id"] and store.load_account(a)]
    session.clear()
    if others:  # stay logged in to the other accounts
        session.permanent = True
        session.update(accounts=others, uid=others[0])
    return jsonify(ok=True, switched=bool(others))


# ---------- dashboard API ----------

@app.get("/api/me")
def api_me():
    acc = current_account()
    c = store.counts(acc["id"])
    return jsonify(account=public_account(acc), blocked=engine.is_blocked(acc),
                   dms_this_month=c.get(f"dms:{engine.month()}", 0), dm_limit=engine.monthly_limit(acc),
                   totals={k: c.get(k, 0) for k in ("dms", "links_sent", "comment_replies", "gate_follows", "ai_replies")},
                   inbox_waiting=sum(t.get("status") == "needs_you" for t in ai_agent.threads(acc["id"])))


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
    source = store.load_rules(acc["id"]).get("reels", {}).get(key)
    if not source:
        return jsonify(error="Automation not found."), 404
    targets = [str(t) for t in (data.get("targets") or [])][:50]
    done, skipped = [], []
    for target in targets:
        if target == key or not valid_rule_key(target):
            continue
        if target in store.load_rules(acc["id"]).get("reels", {}) and not data.get("replace"):
            skipped.append(target)
            continue
        copy = {k: v for k, v in source.items() if k not in ("auto", "label")}
        if engine.is_keyword_rule(target):
            copy["keywords"] = [target[3:]]
        try:
            save_rule(acc, target, copy)
            done.append(target)
        except ValueError as e:
            return jsonify(error=str(e)), 400
    return jsonify(copied=done, skipped=skipped, rules=store.load_rules(acc["id"]))


@app.delete("/api/rules/<key>")
def api_delete_rule(key):
    acc = current_account()
    rules = store.load_rules(acc["id"])
    rules.get("reels", {}).pop(key, None)
    store.save_rules(acc["id"], rules)
    store.redis("DEL", store.account_key(acc["id"], f"rs:{key}"), store.account_key(acc["id"], f"ab:{key}"))
    return jsonify(rules)


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

@app.get("/l/<code>")
def short_link(code):
    url = engine.link_click(code) if re.fullmatch(r"[0-9a-f]{10}", code) else ""
    return redirect(url) if url else abort(404)


@app.get("/api/welcome")
def api_welcome():
    return jsonify(engine.welcome_settings(current_account()))


@app.put("/api/welcome")
def api_put_welcome():
    acc = current_account()
    data = request.get_json(force=True)
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
        return jsonify(error="Write the welcome message first."), 400
    acc["welcome"] = {"enabled": bool(data.get("enabled")), "text": text, "buttons": buttons}
    store.save_account(acc)
    return jsonify(engine.welcome_settings(acc))


BROADCAST_BATCH = 40  # messages per request, so one request stays well inside the time limit


@app.get("/api/broadcast")
def api_broadcast_info():
    acc = current_account()
    return jsonify(eligible=len(engine.recent_chats(acc)), history=[json.loads(x) for x in
                   store.redis("LRANGE", store.account_key(acc["id"], "broadcasts"), 0, 9) or []])


@app.post("/api/broadcast")
def api_broadcast():
    """Sends one message to everyone who DMed in the last 24 h. Call again with the same id until done is true."""
    acc = current_account()
    data = request.get_json(force=True)
    text = str(data.get("text", "")).strip()[:640]
    bid = re.sub(r"[^a-z0-9]", "", str(data.get("id", "")).lower())[:16]
    url, button = safe_url(data.get("url")), str(data.get("button", "")).strip()[:20] or "Open"
    if not text or not bid:
        return jsonify(error="Write the message first."), 400
    if data.get("url") and not url:
        return jsonify(error="The link must start with https://"), 400
    if engine.is_blocked(acc):
        return jsonify(error="Instagram is limiting this account right now. Try again later."), 400
    if engine.over_limit(acc):
        return jsonify(error="This month's DM limit is reached."), 400
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
    return jsonify(sent=sent, failed=failed, left=left, done=not left)


# ---------- notifications and the installable app ----------

@app.get("/api/notifications")
def api_notifications():
    acc = current_account()
    return jsonify(key=push.public_key(), devices=push.devices(acc["id"]), prefs=acc.get("notify") or {"handoff": True, "lead": True})


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
    acc["notify"] = {"handoff": bool(data.get("handoff")), "lead": bool(data.get("lead"))}
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


@app.get("/app/activity")
def activity_page():
    return render_app("activity.html", "activity")


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
    data = request.get_json(force=True)
    old = ai_agent.settings(acc)
    handoff = [h.strip()[:120] for h in str(data.get("handoff", "")).splitlines() if h.strip()][:10] \
        if "handoff" in data else old["handoff"]
    acc["ai"] = {"enabled": bool(data.get("enabled", old["enabled"])),
                 "language": data.get("language") if data.get("language") in LANGUAGES else old["language"],
                 "about": str(data.get("about", old["about"]))[:1500], "faq": str(data.get("faq", old["faq"]))[:6000],
                 "handoff": handoff, "hold_message": str(data.get("hold_message", old["hold_message"]))[:500],
                 "send_hold": bool(data.get("send_hold", old["send_hold"]))}
    if acc["ai"]["enabled"] and not ai_agent.ready(acc):
        return jsonify(error="The AI isn't set up on the server yet (ANTHROPIC_API_KEY)."), 400
    store.save_account(acc)
    return jsonify(ai_state(acc))


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
    thread = ai_agent.get_thread(acc["id"], igsid)
    text = str(request.get_json(force=True).get("text", "")).strip()[:1000]
    if not thread or not text:
        return jsonify(error="Write a message first."), 400
    if time.time() - thread.get("last_fan_at", 0) > 24 * 3600:
        return jsonify(error="Instagram only allows replies within 24 hours of their last message."), 400
    try:
        engine.Instagram(acc).send_dm({"id": igsid}, {"text": text})
    except Exception as e:
        return jsonify(error=f"Instagram didn't send it: {str(e)[:200]}"), 502
    ai_agent.add_message(acc["id"], igsid, "you", text, status="you", reason="", suggestion="", unread=False)
    store.log_activity(acc["id"], "ai", thread.get("username") or igsid, text, "inbox_reply", "ok")
    return jsonify(thread=ai_agent.get_thread(acc["id"], igsid), messages=ai_agent.messages(acc["id"], igsid))


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


THEMES = ["violet", "sunset", "midnight", "mint", "mono"]
SOCIALS = ["instagram", "youtube", "whatsapp", "email", "website"]


def safe_url(url):
    url = str(url or "").strip()
    return url if url.startswith(("https://", "http://", "mailto:", "tel:")) else ""


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
                      "image": image if image.startswith("https://") else "",
                      "featured": bool(it.get("featured")), "enabled": it.get("enabled", True) is not False})
    socials = data.get("socials") or {}
    sign = data.get("signup") or {}
    signup = {"enabled": bool(sign.get("enabled")), "ask": sign.get("ask") if sign.get("ask") in ("email", "phone", "both") else "email",
              "title": str(sign.get("title", "")).strip()[:80] or "Get my free guide",
              "button": str(sign.get("button", "")).strip()[:30] or "Send it to me",
              "thanks": str(sign.get("thanks", "")).strip()[:200] or "Done! Check your inbox 🎉",
              "link": safe_url(sign.get("link"))}
    return {"signup": signup, "name": str(data.get("name", "")).strip()[:60] or acc.get("name") or acc.get("username", ""),
            "bio": str(data.get("bio", "")).strip()[:300],
            "theme": data.get("theme") if data.get("theme") in THEMES else "violet",
            "socials": {k: str(socials.get(k, "")).strip()[:200] for k in SOCIALS}, "items": items}


def default_page(acc):
    return {"name": acc.get("name") or acc.get("username", ""), "bio": "", "theme": "violet",
            "socials": {"instagram": acc.get("username", "")}, "items": []}


@app.get("/api/page")
def api_get_page():
    acc = current_account()
    return jsonify(page=store.load_page(acc["id"]) or default_page(acc), clicks=store.clicks(acc["id"]),
                   signups=store.counts(acc["id"]).get("page_signups", 0),
                   url=f"{request.host_url.rstrip('/')}/{acc.get('username', '')}")


@app.put("/api/page")
def api_put_page():
    acc = current_account()
    page = clean_page(request.get_json(force=True), acc)
    store.save_page(acc["id"], page)
    return jsonify(page=page)


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
from mcp_protocol import handle_http  # noqa: E402


def mcp_account():
    header = request.headers.get("Authorization", "")
    key = header[7:].strip() if header.lower().startswith("bearer ") else request.args.get("key", "")
    if not key.startswith("ri_"):
        return None
    ig_id = store.redis("GET", f"s:mcpkey:{hashlib.sha256(key.encode()).hexdigest()}")
    return store.load_account(ig_id) if ig_id else None


@app.route("/mcp", methods=["GET", "POST", "DELETE"])
def mcp_endpoint():
    acc = mcp_account()
    if not acc:
        return jsonify(error=f"Missing or wrong key. Create a new Claude link in your {BRAND} dashboard."), 401
    if request.method != "POST":
        return "", 405, {"Allow": "POST"}
    tools = mcp_tools.tools_for(acc, save_rule=save_rule, build_report=build_report)
    status, body = handle_http(request.get_data(), tools, BRAND.lower(),
                               f"{BRAND}: Instagram comment-to-DM automation for @{acc.get('username')}. "
                               "Ask before deleting automations.")
    return (jsonify(body), status) if body is not None else ("", status)


@app.route("/api/mcp-key", methods=["GET", "POST", "DELETE"])
def api_mcp_key():
    acc = current_account()
    if request.method == "GET":
        return jsonify(active=bool(acc.get("mcp_key_hash")))
    if acc.get("mcp_key_hash"):  # a new link (or disconnect) turns off the old one
        store.redis("DEL", f"s:mcpkey:{acc['mcp_key_hash']}")
        acc["mcp_key_hash"] = ""
    if request.method == "POST":
        key = "ri_" + secrets.token_urlsafe(32)  # shown once; only its hash is stored
        acc["mcp_key_hash"] = hashlib.sha256(key.encode()).hexdigest()
        store.redis("SET", f"s:mcpkey:{acc['mcp_key_hash']}", acc["id"])
    store.save_account(acc)
    if request.method == "DELETE":
        return jsonify(active=False)
    return jsonify(active=True, key=key, url=f"{base_url()}/mcp?key={key}", endpoint=f"{base_url()}/mcp")


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
    return jsonify(refreshed=done, failed=failed)


# ---------- owner view ----------

@app.get("/owner")
def owner():
    auth = request.authorization
    if not OWNER_PASSWORD or not auth or not hmac.compare_digest(auth.password or "", OWNER_PASSWORD):
        return ("Login required", 401, {"WWW-Authenticate": 'Basic realm="owner"'})
    rows = []
    for ig_id in store.account_ids():
        acc = store.load_account(ig_id)
        if acc:
            c = store.counts(ig_id)
            rows.append({**public_account(acc), "invite": acc.get("invite", ""), "blocked": engine.is_blocked(acc),
                         "dms_month": c.get(f"dms:{engine.month()}", 0), "dms": c.get("dms", 0),
                         "rules": len(store.load_rules(ig_id).get("reels", {}))})
    rows.sort(key=lambda r: -(r.get("created") or 0))
    return render_template("owner.html", rows=rows)


# ---------- public link-in-bio page: replyinbox.in/<username> ----------

USERNAME_RE = re.compile(r"[A-Za-z0-9._]{1,30}")


def public_page(username):
    if not USERNAME_RE.fullmatch(username or ""):
        abort(404)
    acc = store.account_by_username(username)
    if not acc and username.lower() == demo.USERNAME:  # demo data lives in memory without a database
        acc = demo.seed()
    page = store.load_page(acc["id"]) if acc else None
    if not acc or not page:
        abort(404)
    return acc, page


@app.get("/<username>")
def bio_page(username):
    acc, page = public_page(username)
    items = [it for it in page.get("items", []) if it.get("enabled", True)]
    items.sort(key=lambda it: not it.get("featured"))
    socials = [(k, v) for k, v in (page.get("socials") or {}).items() if v]
    return render_template("bio.html", acc=public_account(acc), page=page, items=items, socials=socials,
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
    ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "").split(",")[0].strip()
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
    return redirect(item["url"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8100")), debug=True)
