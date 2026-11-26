"""Follow-up emails for people who signed up but haven't connected Instagram yet.

A 7-email sequence from Om: a welcome right after sign-up, then follow-ups on days 1, 2, 4, 6, 9 and 13, each with one
idea (how it works, safety, followers, AI + Claude, a done-for-you offer, a last nudge) and one "Connect Instagram"
button. It stops the moment the login connects an Instagram account, for team members, and for anyone who unsubscribes
(one click, from any email). The daily cron sends what's due; a login that's behind (new feature, missed days) gets
only the latest due email, never a backlog.

Storage on the user: user["onb"] = {"sent": [step keys], "at": last send time}; user["emails_off"] = True after
unsubscribing. Sending: Resend (RESEND_API_KEY), from ONBOARD_FROM, replies to SUPPORT_EMAIL.
"""
import hashlib
import hmac
import html
import os
import re
import sys
import time
from urllib.parse import quote

import requests

import users

MAX_PER_RUN = 80  # stays under Resend's free daily limit (100) with room for login codes and receipts
e = html.escape


def _env(name, default=""):
    return os.environ.get(name, default).strip().strip("\"'").strip()


def site():
    return (_env("SITE_URL") or _env("PUBLIC_URL") or "https://replyinbox.in").rstrip("/")


def _link(path, step):
    sep = "&" if "?" in path else "?"
    return f"{site()}{path}{sep}utm_source=email&utm_medium=onboarding&utm_campaign={step}"


def _button(text, path, step):
    return (f'<p style="margin:22px 0"><a href="{e(_link(path, step))}" style="background:#2E3BFF;color:#fff;text-decoration:none;'
            f'font-weight:800;padding:12px 20px;border-radius:12px;display:inline-block">{e(text)}</a></p>')


CONNECT = "Connect Instagram →"

# (key, day, subject, preview line, body HTML with {name}; ends with the button)
STEPS = [
    ("welcome", 0, "Welcome to ReplyInbox 👋 one step left",
     "Connect Instagram in 2 minutes and your first auto-DM is ready.",
     "<p>Hi {name},</p><p>I'm Om, I built ReplyInbox. Thanks for signing up! 🙌</p>"
     "<p>There's just <b>one step left: connect your Instagram</b>. It takes 2 minutes through Instagram's own login, "
     "and we never ask for your password.</p>"
     "<p>Once it's connected: someone comments a keyword on your reel, and they get your link in DM within seconds, "
     "24/7, even while you sleep.</p>{button}"
     "<p>Stuck anywhere? Just reply to this email, I read every one.</p><p>Om<br>Founder, ReplyInbox</p>"),
    ("day1", 1, "Your first auto-DM in 2 minutes",
     "Pick a reel, pick a keyword, write the DM. Done.",
     "<p>Hi {name},</p><p>Here's all it takes to send your first automatic DM:</p>"
     "<ol><li>Connect your Instagram (Creator or Business account).</li><li>Pick a reel.</li>"
     "<li>Choose a keyword, like <b>GUIDE</b>.</li><li>Write the DM and add your link. Turn it on.</li></ol>"
     "<p>Now say “comment GUIDE” in your next reel. Everyone who comments gets the link instantly, and the extra "
     "comments help the reel reach more people.</p>{button}"
     "<p>Step-by-step with screenshots: <a href=\"{guide}\">how to auto DM people who comment</a>.</p><p>Om</p>"),
    ("day2", 2, "Is it safe to connect Instagram? (short answer: yes)",
     "Official Meta API, no password, disconnect any time.",
     "<p>Hi {name},</p><p>The most common question I get: <i>“Will connecting a tool get my account in trouble?”</i></p>"
     "<ul><li>ReplyInbox uses <b>Meta's official Instagram API</b>, the same one Meta approves for business tools.</li>"
     "<li>You connect through <b>Instagram's own login screen</b>. We never see your password.</li>"
     "<li>It only DMs people who <b>asked</b> by commenting your keyword, and it follows Instagram's limits for you.</li>"
     "<li>You can disconnect any time from Instagram's settings or ours.</li></ul>{button}"
     "<p>More detail: <a href=\"{safe}\">is Instagram DM automation safe?</a></p><p>Om</p>"),
    ("day4", 4, "Turn reel views into followers",
     "Only send the link to people who follow you.",
     "<p>Hi {name},</p><p>A reel reaches lots of people who don't follow you. Most watch and scroll away.</p>"
     "<p><b>Follow to unlock</b> fixes that: people comment your keyword, and the link reaches them only after they "
     "follow you. They already want the thing, so following takes them one second. (It's on Starter, ₹149 a month; "
     "comment-to-DM itself is free.)</p>"
     "<p>ReplyInbox also shows you, per reel, how many people commented, got the DM, opened the link and followed, "
     "so you know which content actually grows you.</p>{button}<p>Om</p>"),
    ("day6", 6, "Your DMs, answered in Hinglish (and run from Claude)",
     "An AI that replies in your fans' language, and an assistant you can just chat with.",
     "<p>Hi {name},</p><p>Two things no other DM tool I know does:</p>"
     "<p>🤖 <b>An AI that answers your DMs</b> in Hinglish, Hindi or any language, using only your FAQ, prices and "
     "links. Refunds and brand deals come to you with a suggested reply.</p>"
     "<p>✦ <b>Run Instagram from Claude.</b> Connect ReplyInbox to Claude and just ask: <i>“set up a DM for my new "
     "reel”</i> or <i>“which reel got the most leads this week?”</i>, and it's done inside your account.</p>"
     "<p>Every account gets 25 AI replies to try for free (300 a month on Creator, ₹199); Claude comes with Pro. "
     "Connect your Instagram and try the AI on your own DMs.</p>{button}<p>Om</p>"),
    ("day9", 9, "Want me to set it up for you?",
     "Reply with your reel link and I'll build your first automation.",
     "<p>Hi {name},</p><p>I noticed your Instagram isn't connected yet, so let me make it easy.</p>"
     "<p><b>Reply to this email</b> with:</p><ol><li>Your Instagram handle</li><li>The reel you want to automate</li>"
     "<li>What you want to send (a PDF, a link, your course…)</li></ol>"
     "<p>I'll set up your first automation myself, free. You only need to connect your Instagram (2 minutes) so it "
     "can run.</p>{button}<p>Om</p>"),
    ("day13", 13, "Last email from me (your free plan stays)",
     "1,000 free DMs a month, whenever you're ready.",
     "<p>Hi {name},</p><p>This is my last email about getting started, I don't want to crowd your inbox.</p>"
     "<p>Your account stays open, and the <b>free plan stays free</b>: 1,000 DMs a month, comment-to-DM on every reel, "
     "no card. If you ever upgrade, paying yearly gets you 2+ months free.</p>"
     "<p>Whenever your next reel is ready, your first automation is 2 minutes away.</p>{button}"
     "<p>Thanks for giving ReplyInbox a look. If something stopped you, I'd love to know: just reply.</p><p>Om</p>"),
]
KEYS = [k for k, *_ in STEPS]


def _token(uid):
    secret = (_env("SECRET_KEY") or "dev").encode()
    return hmac.new(secret, f"onb-stop:{uid}".encode(), hashlib.sha256).hexdigest()[:24]


def stop_url(uid):
    return f"{site()}/email/stop?u={quote(uid)}&t={_token(uid)}"


def check_token(uid, token):
    return bool(uid) and hmac.compare_digest(_token(uid), str(token or ""))


def eligible(user):
    """Gets the sequence: a real login, no Instagram connected yet, not a team member, not unsubscribed."""
    if not user or not user.get("email") or user.get("emails_off") or user.get("invite"):
        return False
    if user.get("email") == _env("REVIEW_EMAIL").lower():
        return False
    return not users.accounts(user)


def due_step(user, now=None):
    """The step to send now, or None. Only the latest due step: someone 5 days in starts at day 4, not the welcome."""
    now = now or time.time()
    sent = set((user.get("onb") or {}).get("sent", []))
    if (user.get("onb") or {}).get("at", 0) > now - 20 * 3600:
        return None  # at most one email a day
    days = (now - user.get("created", now)) / 86400
    due = [k for k, day, *_ in STEPS if day <= days and k not in sent]
    if not due:
        return None
    last = due[-1]
    if not sent and last == "day13":
        last = "day9"  # an old sign-up we never emailed: open with the done-for-you offer, not "last email"
    if any(KEYS.index(s) > KEYS.index(last) for s in sent):
        return None  # already past it
    return last


def render(user, key):
    _, day, subject, preview, body = STEPS[KEYS.index(key)]
    name = e((user.get("name") or user.get("email", "").split("@")[0] or "there").split()[0].title())
    html_body = body.format(name=name, button=_button(CONNECT, "/connect", key),
                            guide=e(_link("/guides/how-to-auto-dm-instagram-comments", key)),
                            safe=e(_link("/guides/is-instagram-dm-automation-safe", key)))
    stop = stop_url(user["id"])
    page = (f'<div style="display:none;max-height:0;overflow:hidden">{e(preview)}</div>'
            f'<div style="font-family:system-ui,-apple-system,Segoe UI,sans-serif;max-width:540px;margin:auto;padding:24px;'
            f'color:#111318;font-size:15.5px;line-height:1.6">{html_body}'
            f'<p style="color:#888;font-size:12px;margin-top:28px;border-top:1px solid #eee;padding-top:12px">'
            "You're getting this because you signed up at replyinbox.in. "
            f'<a href="{e(stop)}" style="color:#888">Unsubscribe</a> from these emails.</p></div>')
    text = html.unescape(re.sub(r"<[^>]+>", "", body.replace("</p>", "\n\n").replace("<li>", "- ").replace("</li>", "\n")
                                               .format(name=name, button=f"Connect Instagram: {_link('/connect', key)}\n\n",
                                                       guide=_link("/guides/how-to-auto-dm-instagram-comments", key),
                                                       safe=_link("/guides/is-instagram-dm-automation-safe", key))))
    return subject, page, text.strip() + f"\n\n--\nUnsubscribe: {stop}"


def send(user, key):
    """Sends one step to the user and records it. Returns True when sent (or logged, locally)."""
    subject, page, text = render(user, key)
    api_key = _env("RESEND_API_KEY")
    if api_key:
        brand = _env("BRAND_NAME", "ReplyInbox")
        reply_to = _env("SUPPORT_EMAIL") or _env("CONTACT_EMAIL")
        stop = stop_url(user["id"])
        try:
            r = requests.post("https://api.resend.com/emails", timeout=15, headers={"Authorization": f"Bearer {api_key}"},
                              json={"from": _env("ONBOARD_FROM", f"Om from {brand} <hello@replyinbox.in>"), "to": [user["email"]],
                                    "subject": subject, "html": page, "text": text, **({"reply_to": reply_to} if reply_to else {}),
                                    "headers": {"List-Unsubscribe": f"<{stop}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"},
                                    "tags": [{"name": "sequence", "value": "onboarding"}, {"name": "step", "value": key}]})
        except requests.RequestException as err:
            print(f"onboarding email to {user['id']} failed: {err}", file=sys.stderr)
            return False
        if not r.ok:
            print(f"Resend refused onboarding {key} for {user['id']}: {r.status_code} {r.text[:200]}", file=sys.stderr)
            return False
    elif os.environ.get("VERCEL"):
        return False  # no email service set up
    else:
        print(f"[dev] onboarding email {key} to {user['email']}: {subject}", file=sys.stderr)
    fresh = users.get(user["id"]) or user  # don't overwrite anything saved meanwhile
    onb = fresh.get("onb") or {}
    fresh["onb"] = {"sent": [s for s in KEYS if s in set(onb.get("sent", [])) | {key}], "at": int(time.time())}
    users.save(fresh)
    return True


def welcome(user):
    """Right after sign-up."""
    if eligible(user) and not (user.get("onb") or {}).get("sent"):
        send(user, "welcome")


def run(now=None, limit=MAX_PER_RUN):
    """The daily job: send every due step. Returns how many were sent."""
    sent = 0
    for uid in users.all_ids():
        if sent >= limit:
            break
        user = users.get(uid)
        if not eligible(user):
            continue
        key = due_step(user, now)
        if key and send(user, key):
            sent += 1
    return sent


def stats():
    """For /owner: how many logins got each step, and how many unsubscribed."""
    out = {k: 0 for k in KEYS}
    off = 0
    for uid in users.all_ids():
        u = users.get(uid) or {}
        off += bool(u.get("emails_off"))
        for k in (u.get("onb") or {}).get("sent", []):
            if k in out:
                out[k] += 1
    return out, off
