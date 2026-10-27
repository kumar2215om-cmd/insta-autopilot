"""LinkedIn autopilot: scheduled posts, keyword auto-replies on page posts, and a DM queue.

Uses LinkedIn's official API only. LinkedIn does not let apps send DMs, so commenters who
match a keyword land in a queue on the dashboard with a ready-made message: one click opens
the comment, one click copies the message. Automating DMs through a logged-in browser breaks
LinkedIn's terms and gets accounts restricted, so this app does not do that.

- Posting to your profile: "Share on LinkedIn" + "Sign In with LinkedIn using OpenID Connect"
  products (self-serve, approved instantly).
- Posting to a company page and reading/replying to its comments: "Community Management API"
  product (needs LinkedIn's approval). Set LI_PAGES=1 once it's approved.
"""
import base64
import hashlib
import json
import os
import random
import re
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlencode

import anthropic
import requests
from flask import Blueprint, abort, jsonify, redirect, render_template, request


def _env(name, default=""):
    return os.environ.get(name, default).strip().strip("\"'").strip()


CLIENT_ID = _env("LI_CLIENT_ID")
CLIENT_SECRET = _env("LI_CLIENT_SECRET")
REDIRECT_URI = _env("LI_REDIRECT_URI")  # optional; defaults to https://<this host>/linkedin/callback
PAGES = _env("LI_PAGES") == "1"
# Comments are polled (LinkedIn sends no comment webhooks to most apps), at most this often.
POLL_SECONDS = int(_env("LI_POLL_SECONDS", "300"))
# AI captions use Claude; needs ANTHROPIC_API_KEY.
AI_MODEL = _env("LI_AI_MODEL", "claude-opus-5-5")

SCOPES = "openid profile w_member_social"
PAGE_SCOPES = " r_organization_social w_organization_social rw_organization_admin"
OAUTH = "https://www.linkedin.com/oauth/v2"
REST = "https://api.linkedin.com/rest"


def _default_version():
    # LinkedIn's REST API needs a "YYYYMM" version header, and each version is retired after
    # about a year. Two months back is always released and never close to retirement.
    d = datetime.now(timezone.utc).replace(day=1) - timedelta(days=45)
    return d.strftime("%Y%m")


API_VERSION = _env("LI_API_VERSION") or _default_version()

bp = Blueprint("linkedin", __name__)
_lock = threading.RLock()
_deps = {}


def register(app, *, kv_get, kv_set, claim, matches, cron_secret, serverless):
    """Plugs LinkedIn into the main app, reusing its storage, de-duplication and keyword matching."""
    _deps.update(kv_get=kv_get, kv_set=kv_set, claim=claim, matches=matches, cron_secret=cron_secret)
    app.register_blueprint(bp)
    if not serverless:
        threading.Thread(target=_worker, daemon=True).start()


def _worker():
    while True:
        time.sleep(60)
        try:
            tick()
        except Exception as e:
            log("worker", "error", str(e))


# ---------- storage (JSON blobs in the app's key-value store) ----------

def _load(key, default):
    raw = _deps["kv_get"](key)
    return json.loads(raw) if raw else default


def _save(key, value):
    _deps["kv_set"](key, json.dumps(value, ensure_ascii=False))


def log(kind, status, detail=""):
    with _lock:
        items = _load("li_log", [])
        items.insert(0, {"at": time.time(), "kind": kind, "status": status, "detail": detail[:400]})
        _save("li_log", items[:100])


def load_posts():
    return _load("li_posts", [])


def update_post(post_id, **fields):
    with _lock:
        posts = load_posts()
        for p in posts:
            if p["id"] == post_id:
                p.update(fields)
        _save("li_posts", posts)


def load_rules():
    return _load("li_rules", {})


# ---------- auth ----------

def load_auth():
    return _load("li_auth", {})


def access_token():
    auth = load_auth()
    if not auth.get("access_token"):
        raise RuntimeError("LinkedIn is not connected")
    # Tokens last 60 days. Apps approved for the Community Management API also get a
    # refresh token (1 year), so renew a week early when one is available.
    if auth.get("refresh_token") and auth.get("expires_at", 0) - time.time() < 7 * 86400:
        r = requests.post(f"{OAUTH}/accessToken", timeout=20, data={
            "grant_type": "refresh_token", "refresh_token": auth["refresh_token"],
            "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET})
        if r.ok:
            auth.update(_token_fields(r.json()))
            _save("li_auth", auth)
            log("token_refresh", "ok")
        else:
            log("token_refresh", "error", r.text)
    if auth.get("expires_at", 0) < time.time():
        raise RuntimeError("LinkedIn login expired: click Reconnect")
    return auth["access_token"]


def _token_fields(data):
    out = {"access_token": data["access_token"], "expires_at": time.time() + data.get("expires_in", 0),
           "scope": data.get("scope", "")}
    if data.get("refresh_token"):
        out["refresh_token"] = data["refresh_token"]
        out["refresh_expires_at"] = time.time() + data.get("refresh_token_expires_in", 0)
    return out


def api(method, path, **kw):
    headers = {"Authorization": f"Bearer {access_token()}", "LinkedIn-Version": API_VERSION,
               "X-Restli-Protocol-Version": "2.0.0", **kw.pop("headers", {})}
    r = requests.request(method, f"{REST}/{path}", headers=headers, timeout=30, **kw)
    if not r.ok:
        raise RuntimeError(f"{r.status_code}: {r.text[:400]}")
    return r


def _redirect_uri():
    if REDIRECT_URI:
        return REDIRECT_URI
    proto = request.headers.get("X-Forwarded-Proto", request.scheme)
    return f"{proto}://{request.host}/linkedin/callback"


def _fetch_pages(token):
    """Company pages this account administers, as [{"urn", "name"}]."""
    headers = {"Authorization": f"Bearer {token}", "LinkedIn-Version": API_VERSION,
               "X-Restli-Protocol-Version": "2.0.0"}
    r = requests.get(f"{REST}/organizationAcls", headers=headers, timeout=20, params={
        "q": "roleAssignee", "role": "ADMINISTRATOR", "state": "APPROVED"})
    r.raise_for_status()
    pages = []
    for el in r.json().get("elements", []):
        urn = el.get("organization", "")
        name = urn
        org = requests.get(f"{REST}/organizations/{urn.rsplit(':', 1)[-1]}", headers=headers, timeout=20)
        if org.ok:
            name = org.json().get("localizedName", urn)
        pages.append({"urn": urn, "name": name})
    return pages


@bp.get("/linkedin/connect")
def connect():
    if not CLIENT_ID or not CLIENT_SECRET:
        return "Set LI_CLIENT_ID and LI_CLIENT_SECRET first (see README → LinkedIn).", 400
    state = secrets.token_urlsafe(16)
    _deps["kv_set"]("li_oauth_state", state)
    return redirect(f"{OAUTH}/authorization?" + urlencode({
        "response_type": "code", "client_id": CLIENT_ID, "redirect_uri": _redirect_uri(),
        "state": state, "scope": SCOPES + (PAGE_SCOPES if PAGES else "")}))


@bp.get("/linkedin/callback")
def callback():
    if request.args.get("error"):
        return f"LinkedIn said: {request.args.get('error_description', request.args['error'])}", 400
    if not request.args.get("state") or request.args["state"] != _deps["kv_get"]("li_oauth_state"):
        abort(403)
    r = requests.post(f"{OAUTH}/accessToken", timeout=20, data={
        "grant_type": "authorization_code", "code": request.args.get("code", ""),
        "redirect_uri": _redirect_uri(), "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET})
    if not r.ok:
        return f"LinkedIn login failed: {r.text}", 502
    auth = _token_fields(r.json())
    me = requests.get("https://api.linkedin.com/v2/userinfo", timeout=20,
                      headers={"Authorization": f"Bearer {auth['access_token']}"}).json()
    auth.update(person_urn=f"urn:li:person:{me['sub']}", name=me.get("name", ""),
                picture=me.get("picture", ""), pages=[])
    if "rw_organization_admin" in auth["scope"]:
        try:
            auth["pages"] = _fetch_pages(auth["access_token"])
        except Exception as e:
            log("connect", "error", f"Could not list your company pages: {e}")
    _save("li_auth", auth)
    log("connect", "ok", auth["name"])
    return redirect("/linkedin")


@bp.post("/api/linkedin/disconnect")
def disconnect():
    _deps["kv_set"]("li_auth", "")
    return "", 204


def authors(auth=None):
    auth = auth or load_auth()
    if not auth.get("person_urn"):
        return []
    return ([{"urn": auth["person_urn"], "name": f"{auth.get('name') or 'Me'} (profile)", "page": False}]
            + [{**p, "page": True} for p in auth.get("pages", [])])


# ---------- posting ----------

RESERVED = set("\\|{}@[]()<>#*_~")


def _escape(text):
    return "".join("\\" + c if c in RESERVED else c for c in text)


def little_text(text):
    """LinkedIn's post text format: reserved characters must be escaped or the post gets cut off.

    #words at the start of a word become real hashtags; everything else is shown as typed.
    """
    parts = re.split(r"((?<!\S)#\w+)", text)
    return "".join("{hashtag|\\#|" + _escape(p[1:]) + "}" if i % 2 else _escape(p)
                   for i, p in enumerate(parts))


def upload_image(owner, data):
    init = api("POST", "images?action=initializeUpload",
               json={"initializeUploadRequest": {"owner": owner}}).json()["value"]
    r = requests.put(init["uploadUrl"], data=data, timeout=60,
                     headers={"Authorization": f"Bearer {access_token()}"})
    if not r.ok:
        raise RuntimeError(f"Image upload failed: {r.status_code} {r.text[:200]}")
    return init["image"]


def _wait_for_images(urns):
    # Images are processed for a few seconds after upload; posting before that fails.
    for urn in urns:
        for _ in range(10):
            status = api("GET", f"images/{quote(urn, safe='')}").json().get("status")
            if status != "PROCESSING" and status != "WAITING_UPLOAD":
                break
            time.sleep(1.5)


def create_post(p):
    body = {"author": p["author"], "commentary": little_text(p["text"]), "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [],
                             "thirdPartyDistributionChannels": []},
            "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False}
    images = p.get("images", [])
    if images:
        _wait_for_images(images)
    if len(images) == 1:
        body["content"] = {"media": {"id": images[0]}}
    elif images:
        body["content"] = {"multiImage": {"images": [{"id": i} for i in images]}}
    r = api("POST", "posts", json=body)
    return r.headers.get("x-restli-id") or r.headers.get("x-linkedin-id", "")


def publish(post_id):
    with _lock:
        p = next((p for p in load_posts() if p["id"] == post_id), None)
        if not p or p["status"] not in ("scheduled", "failed"):
            return
        attempt = p.get("attempt", 0) + 1
        # Several workers or tabs can tick at once: only one may publish each attempt.
        if not _deps["claim"](f"li-pub:{post_id}:{attempt}"):
            return
        update_post(post_id, status="publishing", attempt=attempt, started_at=time.time())
    try:
        urn = create_post(p)
    except Exception as e:
        update_post(post_id, status="failed", error=str(e))
        log("publish", "error", str(e))
        return
    update_post(post_id, status="published", post_urn=urn, published_at=time.time(), error="")
    log("publish", "ok", p["text"][:80])
    if p.get("rule") and urn:
        with _lock:
            rules = load_rules()
            rules[urn] = {**p["rule"], "author": p["author"], "text": p["text"][:120]}
            _save("li_rules", rules)
        _deps["kv_set"]("li_last_poll", 0)


# ---------- comments → public reply + DM queue ----------

def post_link(post_urn, comment_urn=""):
    url = f"https://www.linkedin.com/feed/update/{post_urn}/"
    return url + (f"?commentUrn={quote(comment_urn, safe='')}" if comment_urn else "")


def _queue_id(comment_urn):
    return hashlib.sha256(comment_urn.encode()).hexdigest()[:12]


def poll_comments():
    auth = load_auth()
    found = 0
    for post_urn, rule in load_rules().items():
        if not rule.get("enabled", True):
            continue
        try:
            comments = api("GET", f"socialActions/{quote(post_urn, safe='')}/comments",
                           params={"count": 100}).json().get("elements", [])
        except Exception as e:
            log("comments", "error", f"{post_urn}: {e}")
            continue
        keywords = [k for k in rule.get("keywords", []) if k.strip()]
        for c in comments:
            comment_urn = c.get("commentUrn") or c.get("$URN") or ""
            actor = c.get("actor", "")
            text = c.get("message", {}).get("text", "")
            if not comment_urn or actor in (rule.get("author"), auth.get("person_urn")):
                continue  # our own comments and replies
            if keywords and not any(_deps["matches"](k, text) for k in keywords):
                continue
            if not _deps["claim"](f"li-c:{comment_urn}"):
                continue
            found += 1
            replied = ""
            if rule.get("comment_reply"):
                line = random.choice(
                    [l.strip() for l in rule["comment_reply"].splitlines() if l.strip()])
                try:
                    api("POST", f"socialActions/{quote(post_urn, safe='')}/comments", json={
                        "actor": rule["author"], "object": post_urn,
                        "parentComment": comment_urn, "message": {"text": line}})
                    replied = line
                except Exception as e:
                    log("reply", "error", str(e))
            if rule.get("dm"):
                with _lock:
                    queue = _load("li_queue", [])
                    queue.insert(0, {"id": _queue_id(comment_urn), "at": time.time(), "post_urn": post_urn,
                                     "comment": text[:500], "actor": actor, "dm": rule["dm"],
                                     "replied": replied, "link": post_link(post_urn, comment_urn),
                                     "status": "pending"})
                    _save("li_queue", queue[:300])
            log("comment", "ok", text[:80])
    return found


def tick():
    """Publishes due posts and checks comments. Runs every minute on a server, from the
    dashboard while it's open, and from /cron/linkedin."""
    out = {"published": 0, "comments": 0}
    if not load_auth().get("access_token"):
        return out
    now = time.time()
    for p in load_posts():
        if p["status"] == "scheduled" and p["publish_at"] <= now:
            publish(p["id"])
            out["published"] += 1
        elif p["status"] == "publishing" and now - p.get("started_at", now) > 15 * 60:
            update_post(p["id"], status="failed",
                        error="Interrupted while publishing. Check LinkedIn before retrying.")
    if PAGES and now - float(_deps["kv_get"]("li_last_poll") or 0) > POLL_SECONDS:
        _deps["kv_set"]("li_last_poll", now)
        out["comments"] = poll_comments()
    return out


# ---------- AI captions ----------

TONES = {
    "professional": "clear, credible and confident, like a respected expert talking to peers",
    "story": "a short personal story with a lesson: a hook, a moment of tension, then the takeaway",
    "bold": "punchy and opinionated, with a scroll-stopping first line and short lines",
    "friendly": "warm, conversational and humble, like talking to a friend over coffee",
    "educational": "practical and skimmable: a promise in the first line, then numbered tips",
    "announcement": "upbeat and concise news: what's new, why it matters, what to do next",
}
LENGTHS = {"short": "40-80 words", "medium": "100-180 words", "long": "200-300 words"}

CAPTION_SCHEMA = {
    "type": "object",
    "properties": {"captions": {"type": "array", "items": {"type": "string"}}},
    "required": ["captions"],
    "additionalProperties": False,
}


def load_voices():
    return _load("li_voice", {})


def write_captions(*, author, notes, draft, tone, length, cta, images):
    """Three LinkedIn caption options, written for a profile ("I") or a company page ("we")."""
    a = next((a for a in authors() if a["urn"] == author), None)
    if not a:
        raise ValueError("Pick who to post as first.")
    voice = load_voices().get(author, "").strip()
    who = (f'the company page "{a["name"]}". Write as the brand ("we"), never as one person'
           if a["page"] else f'{a["name"].replace(" (profile)", "")}\'s personal profile. Write in first person ("I")')
    system = (
        "You write LinkedIn posts that people stop scrolling for.\n"
        f"You are writing for {who}.\n"
        + (f"About this account, in their words: {voice}\n" if voice else "")
        + "Rules:\n"
        "- The first line is the hook: it must make people tap 'see more'. No clickbait or fake claims.\n"
        "- Short paragraphs of 1-2 lines with blank lines between them. Plain text only: no markdown, "
        "no bold or asterisks, no headings.\n"
        "- At most 2 emojis, and only where they add something.\n"
        "- End with 3-5 relevant hashtags on their own final line.\n"
        "- Never invent facts, numbers, names or results that the notes don't give.\n"
        "- Write in the same language as the notes.\n"
        "Return exactly 3 different options, each a complete post ready to publish."
    )
    ask = [f"Tone: {TONES.get(tone, TONES['professional'])}.", f"Length: {LENGTHS.get(length, LENGTHS['medium'])}."]
    if cta:
        ask.append(f"End with this call to action before the hashtags: {cta}")
    if draft:
        ask.append(f"Improve this draft, keeping its meaning and facts:\n<draft>\n{draft}\n</draft>")
    if notes:
        ask.append(f"What the post is about:\n<notes>\n{notes}\n</notes>")
    if images:
        ask.append("The attached image(s) will be posted with it; refer to what they show where it helps.")
    content = [{"type": "image", "source": {"type": "base64", "media_type": mt,
                                            "data": base64.standard_b64encode(data).decode()}}
               for mt, data in images]
    content.append({"type": "text", "text": "\n\n".join(ask)})

    client = anthropic.Anthropic()
    response = client.beta.messages.create(
        model=AI_MODEL,
        max_tokens=16000,
        system=system,
        messages=[{"role": "user", "content": content}],
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": CAPTION_SCHEMA}},
        # If Claude's safety checks decline, the API retries on a fallback model in the same call.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        raise ValueError("Claude declined to write this one. Try rewording your notes.")
    text = next((b.text for b in response.content if b.type == "text"), "")
    return [c.strip()[:3000] for c in json.loads(text)["captions"] if c.strip()]


# ---------- routes ----------

@bp.get("/linkedin")
def page():
    return render_template("linkedin.html")


@bp.get("/api/linkedin/status")
def status():
    auth = load_auth()
    return jsonify({
        "configured": bool(CLIENT_ID and CLIENT_SECRET), "pages_enabled": PAGES,
        "ai_ready": bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")),
        "connected": bool(auth.get("access_token")), "name": auth.get("name", ""),
        "picture": auth.get("picture", ""), "expires_at": auth.get("expires_at"),
        "can_refresh": bool(auth.get("refresh_token")), "authors": authors(auth),
        "log": _load("li_log", [])[:30]})


@bp.get("/api/linkedin/posts")
def list_posts():
    return jsonify(sorted(load_posts(), key=lambda p: -p["publish_at"]))


@bp.post("/api/linkedin/posts")
def add_post():
    f = request.form
    text = f.get("text", "").strip()
    author = f.get("author", "")
    if not text:
        return jsonify({"error": "Write something first."}), 400
    if len(text) > 3000:
        return jsonify({"error": "LinkedIn posts can be at most 3,000 characters."}), 400
    if author not in [a["urn"] for a in authors()]:
        return jsonify({"error": "Pick who to post as (reconnect if your page is missing)."}), 400
    files = request.files.getlist("images")[:20]
    try:
        images = [upload_image(author, fl.read()) for fl in files if fl.filename]
    except Exception as e:
        return jsonify({"error": str(e)}), 502
    post = {"id": secrets.token_hex(6), "author": author, "text": text, "images": images,
            "publish_at": float(f.get("publish_at") or time.time()), "status": "scheduled",
            "created_at": time.time(), "attempt": 0}
    keywords = [k.strip() for k in f.get("keywords", "").split(",") if k.strip()]
    if f.get("auto_reply") == "1" and author.startswith("urn:li:organization:"):
        post["rule"] = {"enabled": True, "keywords": keywords,
                        "comment_reply": f.get("comment_reply", "").strip(), "dm": f.get("dm", "").strip()}
    with _lock:
        _save("li_posts", load_posts() + [post])
    if post["publish_at"] <= time.time():
        publish(post["id"])
    return jsonify(next(p for p in load_posts() if p["id"] == post["id"]))


@bp.post("/api/linkedin/posts/<post_id>/publish")
def publish_now(post_id):
    update_post(post_id, publish_at=time.time())
    publish(post_id)
    return jsonify(next((p for p in load_posts() if p["id"] == post_id), {}))


@bp.delete("/api/linkedin/posts/<post_id>")
def delete_post(post_id):
    with _lock:
        _save("li_posts", [p for p in load_posts() if p["id"] != post_id or p["status"] == "published"])
    return "", 204


@bp.get("/api/linkedin/page-posts")
def page_posts():
    """Recent posts on your company pages, with their comment rules."""
    if not PAGES:
        return jsonify([])
    rules = load_rules()
    out = []
    for a in authors():
        if not a["page"]:
            continue
        try:
            items = api("GET", "posts", headers={"X-RestLi-Method": "FINDER"}, params={
                "q": "author", "author": a["urn"], "count": 15}).json().get("elements", [])
        except Exception as e:
            return jsonify({"error": str(e)}), 502
        for it in items:
            out.append({"urn": it["id"], "author": a["urn"], "page": a["name"],
                        "text": it.get("commentary", "")[:300], "at": it.get("publishedAt") or it.get("createdAt"),
                        "link": post_link(it["id"]), "rule": rules.get(it["id"])})
    return jsonify(out)


@bp.put("/api/linkedin/rules")
def put_rule():
    d = request.get_json(force=True)
    with _lock:
        rules = load_rules()
        rules[d["urn"]] = {"enabled": bool(d.get("enabled", True)), "author": d["author"],
                           "keywords": [k.strip() for k in d.get("keywords", []) if k.strip()],
                           "comment_reply": d.get("comment_reply", "").strip(),
                           "dm": d.get("dm", "").strip(), "text": d.get("text", "")[:120]}
        _save("li_rules", rules)
    _deps["kv_set"]("li_last_poll", 0)  # check the new rule on the next tick
    return jsonify(rules[d["urn"]])


@bp.delete("/api/linkedin/rules")
def delete_rule():
    with _lock:
        rules = load_rules()
        rules.pop(request.args.get("urn", ""), None)
        _save("li_rules", rules)
    return "", 204


@bp.get("/api/linkedin/queue")
def get_queue():
    return jsonify(_load("li_queue", []))


@bp.post("/api/linkedin/queue/<item_id>")
def set_queue_status(item_id):
    new = request.get_json(force=True).get("status")
    if new not in ("pending", "sent", "skipped"):
        abort(400)
    with _lock:
        queue = _load("li_queue", [])
        for it in queue:
            if it["id"] == item_id:
                it["status"] = new
        _save("li_queue", queue)
    return "", 204


@bp.post("/api/linkedin/tick")
def api_tick():
    try:
        return jsonify(tick())
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@bp.get("/cron/linkedin")
def cron():
    # Vercel Cron sends "Authorization: Bearer <CRON_SECRET>"; free pingers like cron-job.org can use ?key=.
    key = _deps["cron_secret"]
    if not key or (request.headers.get("Authorization") != f"Bearer {key}"
                   and request.args.get("key") != key):
        abort(403)
    return jsonify(tick())


@bp.post("/api/linkedin/captions")
def api_captions():
    f = request.form
    if not (f.get("notes", "").strip() or f.get("draft", "").strip()):
        return jsonify({"error": "Write a few words about the post (or a draft to improve) first."}), 400
    images = [(fl.mimetype, fl.read()) for fl in request.files.getlist("images")[:3]
              if fl.mimetype in ("image/png", "image/jpeg", "image/gif", "image/webp")]
    images = [(mt, data) for mt, data in images if len(data) <= 5 * 1024 * 1024]
    try:
        captions = write_captions(author=f.get("author", ""), notes=f.get("notes", "").strip(),
                                  draft=f.get("draft", "").strip(), tone=f.get("tone", ""),
                                  length=f.get("length", ""), cta=f.get("cta", "").strip(), images=images)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except anthropic.AuthenticationError:
        return jsonify({"error": "Set a valid ANTHROPIC_API_KEY to use the AI writer."}), 503
    except anthropic.RateLimitError:
        return jsonify({"error": "The AI writer is busy. Try again in a minute."}), 429
    except anthropic.APIStatusError as e:
        return jsonify({"error": f"AI writer error: {e.message}"}), 502
    except anthropic.APIConnectionError:
        return jsonify({"error": "Couldn't reach the AI writer. Check the server's internet connection."}), 502
    return jsonify({"captions": captions})


@bp.get("/api/linkedin/voice")
def get_voice():
    return jsonify(load_voices())


@bp.put("/api/linkedin/voice")
def put_voice():
    d = request.get_json(force=True)
    with _lock:
        voices = load_voices()
        voices[d["urn"]] = d.get("voice", "").strip()[:1500]
        _save("li_voice", voices)
    return "", 204
