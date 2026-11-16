"""YouTube scheduling: upload a video, let the AI write the title, description and tags, approve, and YouTube publishes it.

Flow
1. The creator connects a channel once (Google OAuth, offline access, so we keep a refresh token).
2. Add a video: the browser uploads the file straight to YouTube as a private video (resumable upload with a short-lived
   access token from /api/youtube/token). Video bytes never pass through Vercel (its request limit is ~4.5 MB).
   The cover is made in the browser (1280x720 JPG under 2 MB) and sent straight to thumbnails.set too.
3. The AI writes the title, description and tags (one AI credit). The item waits in the approval queue ("draft").
4. Approve: the server calls videos.update with the details and status.publishAt, so YouTube publishes it at that time.

Availability: Google must review an app before strangers can grant YouTube upload access, so until then the feature is on
only for the Instagram usernames in YT_ACCOUNTS (comma separated). YT_PUBLIC=1 opens it to everyone.
Env: YT_CLIENT_ID, YT_CLIENT_SECRET, optional YT_REDIRECT_URI (default https://<host>/youtube/callback).
"""
import json
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import requests

import ai_agent
import store


def _env(name, default=""):
    return os.environ.get(name, default).strip().strip("\"'").strip()


AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
API = "https://www.googleapis.com/youtube/v3"
# youtube.upload: upload and thumbnails; youtube: update details, set publishAt, read status, delete.
SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube"
STATUSES = ("uploading", "draft", "approved", "scheduled", "published", "rejected", "failed")
CATEGORIES = {"22": "People & Blogs", "27": "Education", "28": "Science & Technology", "26": "Howto & Style",
              "24": "Entertainment", "10": "Music", "17": "Sports", "20": "Gaming", "25": "News & Politics"}
MAX_KEEP = 100
SHORTS_SECONDS = 180


class YTError(Exception):
    """A problem to show the creator as it is."""


def client_id():
    return _env("YT_CLIENT_ID")


def configured():
    return bool(client_id() and _env("YT_CLIENT_SECRET"))


def available(acc):
    """Shown in the app for the demo, everyone when YT_PUBLIC=1, else only the allowed usernames."""
    if acc.get("demo"):
        return True
    if not configured():
        return False
    if _env("YT_PUBLIC") == "1":
        return True
    allowed = {u.strip().lstrip("@").lower() for u in _env("YT_ACCOUNTS").split(",") if u.strip()}
    return (acc.get("username") or "").lower() in allowed or acc.get("id") in allowed


# ---------- connection ----------

def _conn_key(ig_id):
    return store.account_key(ig_id, "youtube")


def connection(acc):
    return store.get_json(_conn_key(acc["id"])) or {}


def auth_url(redirect_uri, state):
    return AUTH_URL + "?" + urlencode({
        "client_id": client_id(), "redirect_uri": redirect_uri, "response_type": "code", "scope": SCOPES,
        "access_type": "offline", "prompt": "consent", "include_granted_scopes": "true", "state": state})


def finish_connect(acc, code, redirect_uri):
    r = requests.post(TOKEN_URL, data={"code": code, "client_id": client_id(), "client_secret": _env("YT_CLIENT_SECRET"),
                                       "redirect_uri": redirect_uri, "grant_type": "authorization_code"}, timeout=20)
    data = r.json() if r.content else {}
    if not r.ok or "access_token" not in data:
        raise YTError(f"Google didn't connect the channel: {data.get('error_description') or data.get('error') or r.status_code}")
    granted = set(data.get("scope", SCOPES).split())
    if "https://www.googleapis.com/auth/youtube" not in granted:
        raise YTError("Please tick every YouTube permission on Google's screen, then connect again.")
    conn = {"refresh_token": data.get("refresh_token") or connection(acc).get("refresh_token", ""),
            "access_token": data["access_token"], "expires": int(time.time()) + int(data.get("expires_in", 3600)) - 60,
            "connected": int(time.time())}
    if not conn["refresh_token"]:
        raise YTError("Google sent no long-term access. Remove ReplyInbox from your Google account's third-party apps, then connect again.")
    store.set_json(_conn_key(acc["id"]), conn)
    ch = api(acc, "GET", "/channels", params={"part": "snippet,status", "mine": "true"}).get("items") or []
    if not ch:
        disconnect(acc)
        raise YTError("This Google account has no YouTube channel. Create one in YouTube first.")
    conn.update(channel_id=ch[0]["id"], channel_title=ch[0]["snippet"].get("title", ""),
                channel_pic=((ch[0]["snippet"].get("thumbnails") or {}).get("default") or {}).get("url", ""))
    store.set_json(_conn_key(acc["id"]), conn)
    return conn


def disconnect(acc):
    conn = connection(acc)
    if conn.get("refresh_token"):
        try:
            requests.post(REVOKE_URL, data={"token": conn["refresh_token"]}, timeout=10)
        except requests.RequestException:
            pass
    store.redis("DEL", _conn_key(acc["id"]))


def access_token(acc):
    """A valid access token, refreshed when needed. Returns (token, expires_at)."""
    conn = connection(acc)
    if not conn.get("refresh_token"):
        raise YTError("Connect your YouTube channel first.")
    if conn.get("access_token") and conn.get("expires", 0) > time.time() + 120:
        return conn["access_token"], conn["expires"]
    r = requests.post(TOKEN_URL, data={"client_id": client_id(), "client_secret": _env("YT_CLIENT_SECRET"),
                                       "refresh_token": conn["refresh_token"], "grant_type": "refresh_token"}, timeout=20)
    data = r.json() if r.content else {}
    if data.get("error") == "invalid_grant":
        conn["broken"] = True
        store.set_json(_conn_key(acc["id"]), conn)
        raise YTError("YouTube access was removed or expired. Connect your channel again.")
    if not r.ok or "access_token" not in data:
        raise YTError("Google didn't answer. Try again in a minute.")
    conn.update(access_token=data["access_token"], expires=int(time.time()) + int(data.get("expires_in", 3600)) - 60, broken=False)
    store.set_json(_conn_key(acc["id"]), conn)
    return conn["access_token"], conn["expires"]


FRIENDLY = {
    "quotaExceeded": "YouTube's daily upload limit for this app is used up. Your video stays in the queue; try again after midnight Pacific time.",
    "dailyLimitExceeded": "YouTube's daily limit for this app is used up. Try again tomorrow; nothing is lost.",
    "uploadLimitExceeded": "Your channel hit YouTube's upload limit for today. Try again tomorrow.",
    "forbidden": "YouTube refused this. If it's the cover: custom thumbnails need a phone-verified channel (youtube.com/verify).",
    "invalidPublishAt": "That publish time doesn't work: pick a time in the future.",
    "videoNotFound": "This video isn't on your channel any more.",
    "invalidTitle": "YouTube didn't accept the title. Keep it under 100 characters without < or >.",
    "invalidDescription": "YouTube didn't accept the description. Keep it under 5,000 characters without < or >.",
    "invalidTags": "YouTube didn't accept the tags. Use fewer or shorter tags.",
}


def api(acc, method, path, **kw):
    token, _ = access_token(acc)
    url = path if path.startswith("http") else API + path
    r = requests.request(method, url, headers={"Authorization": f"Bearer {token}", **kw.pop("headers", {})}, timeout=30, **kw)
    if r.status_code == 204:
        return {}
    data = r.json() if r.content else {}
    if not r.ok:
        err = data.get("error") or {}
        reason = ((err.get("errors") or [{}])[0]).get("reason", "") if isinstance(err, dict) else ""
        raise YTError(FRIENDLY.get(reason) or f"YouTube said: {err.get('message') if isinstance(err, dict) else err or r.status_code}")
    return data


# ---------- videos in the queue ----------

def _key(ig_id):
    return store.account_key(ig_id, "ytvideos")


def load(ig_id):
    return (store.get_json(_key(ig_id)) or {}).get("items", [])


def _save(ig_id, items):
    if len(items) > MAX_KEEP:
        old = sorted((v for v in items if v["status"] in ("published", "rejected", "failed")), key=lambda v: v["updated"])
        drop = {v["id"] for v in old[:len(items) - MAX_KEEP]}
        items = [v for v in items if v["id"] not in drop]
    store.set_json(_key(ig_id), {"items": items})


def get(acc, item_id):
    v = next((v for v in load(acc["id"]) if v["id"] == item_id), None)
    if not v:
        raise YTError("That video isn't in your queue any more.")
    return v


def _put(acc, item):
    items = [v for v in load(acc["id"]) if v["id"] != item["id"]] + [item]
    item["updated"] = int(time.time())
    _save(acc["id"], items)
    return item


def _clean_text(s, limit):
    return str(s or "").replace("<", "‹").replace(">", "›").strip()[:limit]


def _clean_tags(tags):
    if isinstance(tags, str):
        tags = tags.split(",")
    out, total = [], 0
    for t in tags or []:
        t = _clean_text(t, 60).replace('"', "").strip().lstrip("#")
        if t and t.lower() not in {x.lower() for x in out} and total + len(t) + 2 <= 480:
            out.append(t)
            total += len(t) + 2
    return out[:30]


def is_short(item):
    return bool(item.get("vertical")) and 0 < float(item.get("duration") or 0) <= SHORTS_SECONDS


def _with_shorts(item):
    if is_short(item) and "#shorts" not in item["description"].lower():
        item["description"] = (item["description"].rstrip() + "\n\n#Shorts").strip()[:5000]
    return item


def _publish_at(value):
    """ISO time (from the browser, in UTC) → 'YYYY-MM-DDTHH:MM:SSZ'. Must be at least 10 minutes ahead."""
    try:
        when = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        raise YTError("Pick a date and time to publish.")
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    when = when.astimezone(timezone.utc).replace(microsecond=0)
    if when < datetime.now(timezone.utc) + timedelta(minutes=10):
        raise YTError("Pick a publish time at least 10 minutes from now.")
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def create(acc, data):
    """A new queue item before the browser uploads the file. Status 'uploading'."""
    now = int(time.time())
    item = {"id": secrets.token_hex(5), "status": "uploading", "video_id": "", "file_name": _clean_text(data.get("file_name"), 120),
            "size": int(data.get("size") or 0), "duration": float(data.get("duration") or 0), "vertical": bool(data.get("vertical")),
            "title": _clean_text(data.get("title") or re.sub(r"\.[a-z0-9]{2,4}$", "", str(data.get("file_name") or "")), 100) or "New video",
            "description": _clean_text(data.get("description"), 5000), "tags": _clean_tags(data.get("tags")),
            "category": str(data.get("category") or "22") if str(data.get("category") or "22") in CATEGORIES else "22",
            "publish_at": "", "notes": _clean_text(data.get("notes"), 4000), "thumb": "", "error": "", "created": now, "updated": now}
    if data.get("publish_at"):
        item["publish_at"] = _publish_at(data["publish_at"])
    if acc.get("demo"):  # nothing is uploaded in the demo; go straight to review
        item["status"] = "draft"
    return _put(acc, _with_shorts(item))


def uploaded(acc, item_id, video_id):
    item = get(acc, item_id)
    if not re.fullmatch(r"[A-Za-z0-9_-]{6,20}", str(video_id or "")):
        raise YTError("YouTube didn't return a video id.")
    item.update(video_id=video_id, status="draft", error="")
    return _put(acc, item)


def upload_failed(acc, item_id, error):
    item = get(acc, item_id)
    if item["status"] == "uploading":
        item.update(status="failed", error=_clean_text(error, 300) or "The upload stopped.")
    return _put(acc, item)


def thumb_result(acc, item_id, ok, error=""):
    item = get(acc, item_id)
    item["thumb"] = "set" if ok else ""
    item["thumb_error"] = "" if ok else (_clean_text(error, 300) or FRIENDLY["forbidden"])
    return _put(acc, item)


def update(acc, item_id, data):
    """Edits the details. If the video is already scheduled on YouTube, the change is sent there too."""
    item = get(acc, item_id)
    if item["status"] == "published":
        raise YTError("This video is already live; change it in YouTube Studio.")
    if "title" in data:
        item["title"] = _clean_text(data["title"], 100) or item["title"]
    if "description" in data:
        item["description"] = _clean_text(data["description"], 5000)
    if "tags" in data:
        item["tags"] = _clean_tags(data["tags"])
    if "category" in data and str(data["category"]) in CATEGORIES:
        item["category"] = str(data["category"])
    if "notes" in data:
        item["notes"] = _clean_text(data["notes"], 4000)
    if data.get("publish_at"):
        item["publish_at"] = _publish_at(data["publish_at"])
    _with_shorts(item)
    if item["status"] == "scheduled":
        _send(acc, item)
    return _put(acc, item)


def _send(acc, item):
    """Puts the details and the publish time on YouTube. The whole snippet and status are sent: YouTube clears what's left out."""
    if not item.get("video_id"):
        raise YTError("The video hasn't finished uploading.")
    if not item.get("publish_at"):
        raise YTError("Pick a date and time to publish.")
    _publish_at(item["publish_at"])  # still in the future?
    api(acc, "PUT", "/videos", params={"part": "snippet,status"}, json={
        "id": item["video_id"],
        "snippet": {"title": item["title"], "description": item["description"], "tags": item["tags"], "categoryId": item["category"]},
        "status": {"privacyStatus": "private", "publishAt": item["publish_at"], "selfDeclaredMadeForKids": False,
                   "embeddable": True, "license": "youtube", "publicStatsViewable": True}})


def approve(acc, item_id, publish_at=None):
    """The creator's yes: schedule it on YouTube. On a YouTube error the item stays 'approved' with the error, to retry."""
    item = get(acc, item_id)
    if item["status"] in ("uploading", "failed"):
        raise YTError("The video hasn't finished uploading.")
    if item["status"] == "published":
        raise YTError("This video is already live.")
    if publish_at:
        item["publish_at"] = _publish_at(publish_at)
    if not item.get("publish_at"):
        raise YTError("Pick a date and time to publish.")
    item["status"] = "approved"
    try:
        if not acc.get("demo"):
            _send(acc, item)
    except YTError as e:
        item["error"] = str(e)
        _put(acc, item)
        raise
    item.update(status="scheduled", error="")
    return _put(acc, item)


def reject(acc, item_id, note=""):
    """Not this one: if it was scheduled, it goes back to plain private on YouTube so it never publishes."""
    item = get(acc, item_id)
    if item["status"] == "published":
        raise YTError("This video is already live; hide it in YouTube Studio.")
    if item["status"] == "scheduled" and not acc.get("demo"):
        api(acc, "PUT", "/videos", params={"part": "status"}, json={
            "id": item["video_id"], "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}})
    item.update(status="rejected", note=_clean_text(note, 300), error="")
    return _put(acc, item)


def back_to_review(acc, item_id):
    item = get(acc, item_id)
    if item["status"] not in ("rejected", "approved"):
        raise YTError("Only rejected or not-yet-scheduled videos go back to review.")
    item.update(status="draft" if item.get("video_id") else "failed", error="")
    return _put(acc, item)


def remove(acc, item_id, from_youtube=False):
    item = get(acc, item_id)
    if from_youtube and item.get("video_id") and item["status"] != "published" and not acc.get("demo"):
        try:
            api(acc, "DELETE", "/videos", params={"id": item["video_id"]})
        except YTError as e:
            if "isn't on your channel" not in str(e):
                raise
    _save(acc["id"], [v for v in load(acc["id"]) if v["id"] != item_id])


def refresh_statuses(acc):
    """Marks scheduled videos as published once YouTube has made them public (one cheap list call)."""
    items = load(acc["id"])
    due = [v for v in items if v["status"] == "scheduled" and v.get("video_id") and v.get("publish_at", "") <= time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())]
    if not due or acc.get("demo"):
        return items
    try:
        got = api(acc, "GET", "/videos", params={"part": "status", "id": ",".join(v["video_id"] for v in due[:50])}).get("items", [])
    except YTError:
        return items
    public = {g["id"] for g in got if (g.get("status") or {}).get("privacyStatus") == "public"}
    gone = {v["video_id"] for v in due[:50]} - {g["id"] for g in got}
    changed = False
    for v in items:
        if v.get("video_id") in public:
            v.update(status="published", updated=int(time.time()))
            changed = True
        elif v.get("video_id") in gone and v["status"] == "scheduled":
            v.update(status="failed", error="This video was deleted on YouTube.", updated=int(time.time()))
            changed = True
    if changed:
        _save(acc["id"], items)
    return items


def studio_url(item):
    return f"https://studio.youtube.com/video/{item['video_id']}/edit" if item.get("video_id") else ""


def view(acc, item):
    return {**item, "studio_url": studio_url(item), "watch_url": f"https://youtu.be/{item['video_id']}" if item.get("video_id") else "",
            "short": is_short(item)}


# ---------- the AI writes the details ----------

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Max 100 characters, ideally 50-70. Main keyword early. No clickbait lies."},
        "description": {"type": "string", "description": "Max 4,500 characters. See the rules."},
        "tags": {"type": "array", "items": {"type": "string"}, "description": "8-15 search phrases people type."},
    },
    "required": ["title", "description", "tags"],
    "additionalProperties": False,
}


def system_prompt(acc):
    s = ai_agent.settings(acc)
    return f"""You write YouTube titles, descriptions and tags for the creator @{acc.get('username', '')} (also on Instagram), to rank in YouTube and Google search and get clicks.

About the creator:
{s['about'] or '(not provided)'}

Their products, links and freebies (the only links and prices you may use):
{ai_agent.knowledge(acc)}

Rules:
- Write in the language and style of the creator's notes or transcript (Hinglish stays Hinglish). If unsure, English.
- Title: the searchable topic first, specific and honest, at most 70 characters when possible (100 max). No ALL CAPS sentences.
- Description: first 2 lines (about 150 characters) say what the viewer gets, with the main keyword, because search shows them.
  Then 3-6 short lines of value. Then the creator's relevant links from the list above, each on its own line. Then 3-5 hashtags.
- Chapters: only if the transcript has real timestamps, list them as "0:00 Intro" lines starting at 0:00. Never invent timestamps.
- Only facts from the notes, transcript and the lists above. Never invent numbers, results, offers or links.
- Tags: phrases people actually search, most specific first; no hashtags in tags."""


def write_details(acc, notes="", transcript="", file_name="", duration=0, vertical=False):
    """Returns {"title", "description", "tags"}; one AI credit. Raises YTError when it can't."""
    notes, transcript = str(notes or "")[:4000], str(transcript or "")[:20000]
    if not notes.strip() and not transcript.strip():
        raise YTError("Tell the AI what the video is about (notes or transcript).")
    short = bool(vertical) and 0 < float(duration or 0) <= SHORTS_SECONDS
    if acc.get("demo"):
        topic = (notes or transcript).strip().splitlines()[0][:60]
        return {"title": f"{topic} (step by step)"[:100],
                "description": f"{topic}: everything you need, in simple steps.\n\nIn this video:\n- The tool\n- How to set it up\n- Mistakes to avoid\n\n#aitools #tutorial"
                               + ("\n\n#Shorts" if short else ""),
                "tags": ["ai tools", "tutorial", topic.lower()[:40]]}
    c = ai_agent.client()
    if c is None:
        raise YTError("AI isn't set up yet: add ANTHROPIC_API_KEY to the server.")
    if ai_agent.over_quota(acc):
        raise YTError(ai_agent.quota_reason(acc))
    mins = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "unknown"
    ask = (f"Video file: {file_name or '(unnamed)'}; length {mins}; {'vertical' if vertical else 'horizontal'}"
           + ("; this is a YouTube Short: keep the description short and end it with #Shorts." if short else ".")
           + (f"\n\nCreator's notes:\n{notes}" if notes.strip() else "") + (f"\n\nTranscript:\n{transcript}" if transcript.strip() else ""))
    response = c.messages.create(
        model=ai_agent.AI_MODEL, max_tokens=4000,
        system=[{"type": "text", "text": system_prompt(acc), "cache_control": {"type": "ephemeral"}}],
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": ask}])
    if response.stop_reason == "refusal":
        raise YTError("The AI declined to write this one. Write the details yourself.")
    if response.stop_reason == "max_tokens":
        raise YTError("The AI's answer was cut off. Try shorter notes.")
    data = json.loads(next((b.text for b in response.content if b.type == "text"), "{}"))
    ai_agent.note_use(acc)
    out = {"title": _clean_text(data.get("title"), 100), "description": _clean_text(data.get("description"), 5000),
           "tags": _clean_tags(data.get("tags"))}
    if short and "#shorts" not in out["description"].lower():
        out["description"] = (out["description"] + "\n\n#Shorts")[:5000]
    return out


def demo_items():
    """Sample queue for the demo account."""
    now = int(time.time())
    at = lambda d: (datetime.now(timezone.utc) + timedelta(days=d)).replace(hour=12, minute=30, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    base = {"size": 48_000_000, "category": "28", "thumb": "set", "error": "", "notes": "", "created": now, "updated": now, "tags": ["ai tools", "chatgpt"]}
    return [
        {**base, "id": "demo1", "status": "draft", "video_id": "dQw4w9WgXcQ", "file_name": "ai-tools.mp4", "duration": 412, "vertical": False,
         "title": "5 Free AI Tools That Save 2 Hours a Day (2026)", "publish_at": at(1),
         "description": "5 free AI tools I use every day to save 2 hours of work.\n\n0:00 Intro\n0:40 Tool 1\n...\n\n#aitools #productivity"},
        {**base, "id": "demo2", "status": "scheduled", "video_id": "9bZkp7q19f0", "file_name": "prompt-short.mp4", "duration": 42, "vertical": True,
         "title": "This ChatGPT prompt fixes every caption", "publish_at": at(2), "thumb": "",
         "description": "One prompt for better captions. Comment PROMPTS on Instagram for the full list.\n\n#chatgpt #Shorts"},
    ]


def ensure_demo(acc):
    if acc.get("demo") and not load(acc["id"]):
        _save(acc["id"], demo_items())
