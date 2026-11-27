"""Health alerts for the owner: errors, the database refusing requests, traffic spikes, and a daily report.

- on_error: any unhandled error in a request. Emails the owner at most once per 30 minutes per kind of error. A
  database refusal (Upstash 4xx/5xx, e.g. the monthly or budget limit) gets its own alert with what to do. Sent
  straight through Resend, so it still works while the database is down.
- note_webhook: counts Instagram webhooks per hour by sampling 1 in 10 (to keep database usage tiny) and alerts once a
  day when the hour is far above normal (LOAD_ALERT_PER_HOUR, default 1,500).
- daily_report: from the daily cron. Database reachable and how fast, logins, sign-ups, connected accounts, DMs and
  errors in the last day, and the follow-up emails sent.

Alerts go to ALERT_EMAIL (else SUPPORT_EMAIL, else CONTACT_EMAIL).
"""
import html
import os
import random
import sys
import threading
import time
import traceback

import requests

import store

_lock = threading.Lock()
_last_sent = {}  # alert kind -> time, per server (plus a database claim when it's reachable, to avoid one per server)
THROTTLE = 30 * 60
SAMPLE = 10
e = html.escape


def _env(name, default=""):
    return os.environ.get(name, default).strip().strip("\"'").strip()


def recipient():
    return _env("ALERT_EMAIL") or _env("SUPPORT_EMAIL") or _env("CONTACT_EMAIL")


def email(subject, body_html, text):
    """Sends one email to the owner. Never raises."""
    key, to = _env("RESEND_API_KEY"), recipient()
    if not key or not to:
        print(f"[alert] {subject}\n{text}", file=sys.stderr)
        return False
    brand = _env("BRAND_NAME", "ReplyInbox")
    try:
        r = requests.post("https://api.resend.com/emails", timeout=10, headers={"Authorization": f"Bearer {key}"},
                          json={"from": _env("MAIL_FROM", f"{brand} <no-reply@replyinbox.in>"), "to": [to],
                                "subject": subject, "text": text,
                                "html": f'<div style="font-family:system-ui,sans-serif;max-width:620px;line-height:1.55">{body_html}</div>'})
        return r.ok
    except requests.RequestException:
        return False


def alert(kind, subject, body_html, text, every=THROTTLE):
    """One email per `kind` per `every` seconds."""
    now = time.time()
    with _lock:
        if now - _last_sent.get(kind, 0) < every:
            return False
        _last_sent[kind] = now
    try:  # other servers may hit the same problem: let only one of them email (skipped when the database is down)
        if not store.claim(f"s:alert:{kind}", every):
            return False
    except Exception:
        pass
    return email(subject, body_html, text)


def _is_database_error(exc):
    text = f"{type(exc).__name__} {exc}"
    return "upstash.io" in text or "Upstash" in text


def on_error(sender, exception=None, **extra):
    """Flask's got_request_exception signal."""
    try:
        from flask import request
        path = f"{request.method} {request.path}"
    except Exception:
        path = "?"
    try:
        _count_error()
        tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))[-2500:]
        if _is_database_error(exception):
            alert("database",
                  "⚠️ ReplyInbox: the database is refusing requests",
                  "<h2>The database is refusing requests</h2>"
                  f"<p>Requests to Upstash are failing (latest on <code>{e(path)}</code>). While this lasts, automations, "
                  "DM links and the dashboard don't work.</p><p><b>Most likely:</b> the Upstash monthly budget or plan limit "
                  "was reached. Open <a href=\"https://console.upstash.com\">console.upstash.com</a>, check the database's "
                  "Usage and Cost, and raise the budget if it's at the limit.</p>"
                  f"<pre style=\"white-space:pre-wrap;font-size:12px;background:#f5f5f5;padding:10px\">{e(tb)}</pre>",
                  f"The database (Upstash) is refusing requests, latest on {path}. Check Usage and Cost at "
                  f"https://console.upstash.com and raise the budget if it's at the limit.\n\n{tb}")
        else:
            alert(f"error:{type(exception).__name__}:{path.split('/')[1] if '/' in path else path}",
                  f"⚠️ ReplyInbox error: {type(exception).__name__} on {path}",
                  f"<h2>An error on replyinbox.in</h2><p><code>{e(path)}</code>: {e(str(exception))[:300]}</p>"
                  f"<pre style=\"white-space:pre-wrap;font-size:12px;background:#f5f5f5;padding:10px\">{e(tb)}</pre>"
                  "<p>More of the same kind within 30 minutes won't send another email.</p>",
                  f"An error on replyinbox.in: {path}: {exception}\n\n{tb}")
    except Exception as err:  # monitoring must never make things worse
        print(f"monitor failed: {err}", file=sys.stderr)


def _count_error():
    try:
        key = f"s:health:errors:{store.day_str()}"
        store.redis("INCR", key)
        store.expire_daily(key, 8 * 86400)
    except Exception:
        pass  # the database itself may be the problem


def note_webhook():
    """Called for every Instagram webhook; touches the database for 1 in SAMPLE of them."""
    if random.randrange(SAMPLE):
        return
    try:
        hour = time.strftime("%Y-%m-%d-%H", time.gmtime())
        key = f"s:health:hooks:{hour}"
        n = int(store.redis("INCR", key) or 0) * SAMPLE
        store.expire_daily(key, 3 * 86400)
        limit = int(_env("LOAD_ALERT_PER_HOUR", "1500") or 1500)
        if n >= limit:
            alert("load", f"📈 ReplyInbox: traffic spike (~{n:,} Instagram events this hour)",
                  f"<h2>Traffic spike</h2><p>About <b>{n:,}</b> Instagram events in the last hour (alert level {limit:,}). "
                  "Usually a reel going viral, so automations are busy, which is good.</p>"
                  "<p>Each event uses database commands, so watch the Upstash cost at "
                  "<a href=\"https://console.upstash.com\">console.upstash.com</a> if this lasts for hours.</p>",
                  f"Traffic spike: about {n:,} Instagram events this hour. Watch the Upstash cost if it lasts.",
                  every=24 * 3600)
    except Exception:
        pass


def hooks_last_day():
    hours = [time.strftime("%Y-%m-%d-%H", time.gmtime(time.time() - h * 3600)) for h in range(24)]
    try:
        vals = store.pipeline([("GET", f"s:health:hooks:{h}") for h in hours])
        return sum(int(v or 0) for v in vals) * SAMPLE
    except Exception:
        return None


def daily_report():
    """From the daily cron: a short health email."""
    import onboarding
    import users
    t0 = time.time()
    try:
        store.redis("GET", "s:health:ping")  # any cheap read proves the database answers
        db = f"OK, answered in {int((time.time() - t0) * 1000)} ms"
    except Exception as err:
        db = f"NOT reachable: {err}"
    try:
        yesterday = store.day_str(1)
        errors = int(store.redis("GET", f"s:health:errors:{yesterday}") or 0) + int(store.redis("GET", f"s:health:errors:{store.day_str()}") or 0)
        ids = users.all_ids()
        people = [users.get(u) or {} for u in ids]
        day = 86400
        signups = sum(1 for u in people if u.get("created", 0) > time.time() - day)
        connected = sum(1 for u in people if u.get("accounts"))
        accounts = store.account_ids()
        dms = 0
        for ig_id in accounts:
            d = store.hash_all(store.account_key(ig_id, f"day:{yesterday}"))
            dms += d.get("dms", 0)
        sent, off = onboarding.stats()
        hooks = hooks_last_day()
        rows = [("Database", db), ("Errors (yesterday + today)", f"{errors:,}"),
                ("Instagram events, last 24 h", "–" if hooks is None else f"~{hooks:,}"),
                ("DMs sent yesterday", f"{dms:,}"), ("Logins", f"{len(ids):,} ({connected:,} with Instagram connected)"),
                ("New sign-ups, last 24 h", f"{signups:,}"), ("Instagram accounts", f"{len(accounts):,}"),
                ("Follow-up emails sent (all time)", f"{sum(sent.values()):,} · {off} unsubscribed")]
    except Exception as err:
        rows = [("Database", db), ("Report", f"couldn't be built: {err}")]
    ok = db.startswith("OK")
    table = "".join(f"<tr><td style=\"padding:6px 12px 6px 0;color:#555\">{e(k)}</td><td style=\"padding:6px 0\"><b>{e(v)}</b></td></tr>" for k, v in rows)
    email(f"{'✅' if ok else '⚠️'} ReplyInbox daily health · {time.strftime('%d %b', time.gmtime())}",
          f"<h2>Daily health</h2><table>{table}</table><p style=\"color:#777;font-size:13px\">Database cost and usage: "
          "<a href=\"https://console.upstash.com\">console.upstash.com</a> (budget limit $20).</p>",
          "\n".join(f"{k}: {v}" for k, v in rows))
    return rows
