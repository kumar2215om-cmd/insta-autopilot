"""ReplyInbox (formerly LikhoDM): comment-to-DM automation for any Instagram creator ("Login with Instagram").

A separate app from ../app.py (Om's own site). Same approved Meta app, many accounts:
each creator connects their Instagram, sets keyword rules per reel, and gets the
comment reply → DM → follow check → link flow on their own account.
"""
import base64
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
    return store.load_account(session.get("uid"))


def public_account(acc):
    """What the dashboard may see: never the token."""
    return {k: acc.get(k) for k in ("id", "username", "name", "pic", "followers", "created", "paused")}


@app.context_processor
def brand():
    return {"brand": BRAND, "contact_email": CONTACT_EMAIL}


@app.before_request
def guard():
    # Logged-in API calls that change data must be JSON: a cross-site form can't send that without CORS.
    if request.path.startswith("/api/"):
        if not current_account():
            return jsonify(error="Please log in again."), 401
        if request.method in ("POST", "PUT", "DELETE") and not request.is_json:
            return jsonify(error="JSON required"), 415


# ---------- pages ----------

@app.get("/")
def landing():
    if current_account():
        return redirect(url_for("dashboard"))
    return render_template("landing.html", invite_only=SIGNUPS == "invite",
                           error=request.args.get("error", ""))


@app.get("/app")
def dashboard():
    acc = current_account()
    if not acc:
        return redirect(url_for("landing"))
    return render_template("app.html", acc=public_account(acc))


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
    if SIGNUPS == "invite":
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
    acc = store.load_account(ig_id) or {"id": ig_id, "created": int(time.time()), "paused": False}
    acc.update(asid=str(me.get("id", "")), username=me.get("username", ""), name=me.get("name", ""),
               pic=me.get("profile_picture_url", ""), followers=me.get("followers_count"),
               token=token, token_at=int(time.time()), invite=session.pop("invite", acc.get("invite", "")))
    store.save_account(acc)
    store.redis("DEL", store.account_key(ig_id, "token_dead"))
    try:  # without this subscription Instagram sends no comment/DM events for the account
        engine.Instagram(acc).post("me/subscribed_apps", subscribed_fields=WEBHOOK_FIELDS)
    except Exception as e:
        store.log_activity(ig_id, "", "", "", "connect", "error",
                           f"Couldn't turn on comment and DM events: {e}")
    session.permanent = True
    session["uid"] = ig_id
    return redirect(url_for("dashboard"))


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.post("/api/disconnect")
def api_disconnect():
    acc = current_account()
    try:  # stop Instagram sending this account's events; best effort
        requests.delete(f"{engine.GRAPH}/me/subscribed_apps", params={"access_token": acc["token"]}, timeout=10)
    except Exception:
        pass
    store.delete_account(acc["id"])
    session.clear()
    return jsonify(ok=True)


# ---------- dashboard API ----------

@app.get("/api/me")
def api_me():
    acc = current_account()
    c = store.counts(acc["id"])
    return jsonify(account=public_account(acc), blocked=engine.is_blocked(acc),
                   dms_this_month=c.get(f"dms:{engine.month()}", 0), dm_limit=engine.monthly_limit(acc),
                   totals={k: c.get(k, 0) for k in ("dms", "links_sent", "comment_replies", "gate_follows")})


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
    acc = current_account()
    key = store.account_key(acc["id"], "report")
    cached = store.get_json(key)
    if cached and not request.args.get("fresh"):
        return jsonify(cached)
    try:
        ig = engine.Instagram(acc)
        media = ig.get("me/media", limit=30, fields=(
            "id,caption,media_product_type,permalink,thumbnail_url,media_url,timestamp,comments_count,like_count"))["data"]
    except Exception as e:
        if cached:
            return jsonify({**cached, "warning": str(e)})
        return jsonify(error=str(e), reels=[]), 502
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
    return jsonify(data)


@app.get("/report")
def report_page():
    acc = current_account()
    if not acc:
        return redirect(url_for("landing"))
    return render_template("report.html", acc=public_account(acc))


@app.get("/api/rules")
def api_rules():
    return jsonify(store.load_rules(current_account()["id"]))


def valid_rule_key(key):
    return key == "*" or key.isdigit() or (engine.is_keyword_rule(key) and key[3:].replace("_", "").isalnum())


@app.put("/api/rules/<key>")
def api_put_rule(key):
    acc = current_account()
    if not valid_rule_key(key):
        return jsonify(error="Bad rule id"), 400
    data = request.get_json(force=True)
    rule = {
        "enabled": bool(data.get("enabled", True)),
        "keywords": [k.strip()[:40] for k in data.get("keywords", []) if k.strip()][:20],
        "comment_reply": str(data.get("comment_reply", ""))[:1000].strip(),
        "opening_dm": str(data.get("opening_dm", ""))[:640].strip(),
        "button_text": str(data.get("button_text", ""))[:20].strip(),
        "require_follow": bool(data.get("require_follow")),
        "follow_dm": str(data.get("follow_dm", ""))[:640].strip(),
        "followed_button_text": str(data.get("followed_button_text", ""))[:20].strip(),
        "dm": str(data.get("dm", ""))[:1000].strip(),
        "comments": bool(data.get("comments", True)),
        "label": str(data.get("label", ""))[:120],
    }
    if rule["enabled"] and not rule["dm"]:
        return jsonify(error="Add the final DM (your message and link) before turning the rule on."), 400
    if engine.is_keyword_rule(key) and not rule["keywords"]:
        rule["keywords"] = [key[3:]]
    rules = store.load_rules(acc["id"])
    rules.setdefault("reels", {})[key] = rule
    store.save_rules(acc["id"], rules)
    return jsonify(rules)


@app.delete("/api/rules/<key>")
def api_delete_rule(key):
    acc = current_account()
    rules = store.load_rules(acc["id"])
    rules.get("reels", {}).pop(key, None)
    store.save_rules(acc["id"], rules)
    return jsonify(rules)


@app.get("/api/activity")
def api_activity():
    return jsonify(store.recent_activity(current_account()["id"]))


@app.post("/api/pause")
def api_pause():
    acc = current_account()
    acc["paused"] = bool(request.get_json(force=True).get("paused"))
    store.save_account(acc)
    return jsonify(paused=acc["paused"])


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
    return "ok"


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8100")), debug=True)
