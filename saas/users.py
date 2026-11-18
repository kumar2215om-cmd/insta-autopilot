"""ReplyInbox logins: a user (Google or email code) owns one or more Instagram accounts, like ManyChat or SuperProfile.

- The user signs in first, then must connect an Instagram account before the dashboard opens.
- The plan belongs to the user and is copied onto each of its Instagram accounts (so plans.plan_of(acc) keeps working).
- How many Instagram accounts a user may connect comes from the plan (plans.PLANS[...]["accounts"]) plus bought extras;
  it's enforced only once billing is on (PLAN_LOCKS=on), until then up to MAX_ACCOUNTS.
- Email login: a 6-digit code, valid 10 minutes, 5 tries, sent with Resend (RESEND_API_KEY, MAIL_FROM).
- Google login: OpenID Connect (GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET, or the YouTube client YT_CLIENT_ID / YT_CLIENT_SECRET).

Storage: s:u:<uid> (user JSON), s:uemail:<email> → uid, s:ugoogle:<sub> → uid; accounts carry "owner": uid.
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import time
from urllib.parse import urlencode

import requests

import plans
import store

MAX_ACCOUNTS = 10          # cap before billing is on
CODE_TTL = 600             # email code lifetime, seconds
CODE_TRIES = 5
SENDS_PER_HOUR = 5         # codes per email address per hour
SENDS_PER_IP_HOUR = 20
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[a-z]{2,}$", re.I)
PLAN_ORDER = ("free", "starter", "creator", "pro", "agency")


class LoginError(Exception):
    """A problem to show the person as it is."""


def _env(name, default=""):
    return os.environ.get(name, default).strip().strip("\"'").strip()


# ---------- users ----------

def get(uid):
    return store.get_json(f"s:u:{uid}") if uid else None


def save(user):
    store.set_json(f"s:u:{user['id']}", user)


def clean_email(value):
    email = str(value or "").strip().lower()
    if not EMAIL_RE.match(email) or len(email) > 254:
        raise LoginError("That doesn't look like an email address.")
    return email


def by_email(email):
    return get(store.redis("GET", f"s:uemail:{email}"))


def create(email, name="", pic="", invite=""):
    user = {"id": secrets.token_hex(8), "email": email, "name": name[:80], "pic": pic, "google": "", "plan": "free",
            "extra_accounts": 0, "accounts": [], "invite": invite, "created": int(time.time())}
    save(user)
    store.redis("SET", f"s:uemail:{email}", user["id"])
    return user


def login_email(email, invite=""):
    """The user with this (verified) email, created on first sign-in."""
    return by_email(email) or create(email, invite=invite)


def login_google(info, invite=""):
    """The user for a verified Google profile: by Google id, else by email (then linked), else new."""
    sub, email = str(info.get("sub", "")), clean_email(info.get("email"))
    if not sub or info.get("email_verified") is False:
        raise LoginError("Google didn't confirm this email address.")
    user = get(store.redis("GET", f"s:ugoogle:{sub}")) or by_email(email) or create(email, invite=invite)
    user.update(google=sub, name=user.get("name") or str(info.get("name", ""))[:80], pic=user.get("pic") or info.get("picture", ""))
    save(user)
    store.redis("SET", f"s:ugoogle:{sub}", user["id"])
    return user


def is_new(user):
    return not user.get("accounts")


# ---------- Instagram accounts owned by a user ----------

def accounts(user):
    """The user's Instagram accounts that still exist, in order."""
    out = []
    for ig_id in (user or {}).get("accounts", []):
        acc = store.load_account(ig_id)
        if acc and acc.get("owner") == user["id"]:
            out.append(acc)
    return out


def limit(user):
    if not plans.LOCKS_ON:
        return MAX_ACCOUNTS
    return plans.PLANS.get(user.get("plan") or "free", plans.PLANS["free"])["accounts"] + int(user.get("extra_accounts") or 0)


def owns(user, ig_id):
    acc = store.load_account(ig_id) if user else None
    return bool(acc) and acc.get("owner") == user["id"] and ig_id in user.get("accounts", [])


def check_can_add(user, acc_or_none, ig_id):
    """Raises LoginError when this Instagram account can't be added to this user."""
    if acc_or_none and acc_or_none.get("owner") and acc_or_none["owner"] != user["id"] and get(acc_or_none["owner"]):
        raise LoginError("This Instagram account is already connected to another ReplyInbox login. "
                         "Remove it there first, or write to us.")
    if ig_id not in user.get("accounts", []) and len(accounts(user)) >= limit(user):
        raise LoginError(f"Your plan allows {limit(user)} Instagram account{'s' if limit(user) != 1 else ''}. "
                         "Upgrade or add an extra account to connect another.")


def claim(user, acc):
    """Makes the user the owner of acc (call check_can_add first). Saves both."""
    # Accounts from before user logins kept their own plan: the user gets the better of the two.
    if PLAN_ORDER.index(plans.plan_of({"plan": acc.get("plan")})) > PLAN_ORDER.index(user.get("plan") or "free"):
        user["plan"] = acc["plan"]
    acc["owner"] = user["id"]
    acc["plan"] = user.get("plan") or "free"
    if acc["id"] not in user["accounts"]:
        user["accounts"].append(acc["id"])
    save(user)
    store.save_account(acc)
    sync_plan(user)


def remove(user, ig_id):
    if user and ig_id in user.get("accounts", []):
        user["accounts"].remove(ig_id)
        save(user)


def set_plan(user, plan):
    user["plan"] = plan
    save(user)
    sync_plan(user)


def sync_plan(user):
    for acc in accounts(user):
        if acc.get("plan") != user["plan"]:
            acc["plan"] = user["plan"]
            store.save_account(acc)


def owner_of(acc):
    return get(acc.get("owner")) if acc else None


# ---------- email codes ----------

def _hash(email, code):
    return hashlib.sha256(f"{email}|{code}".encode()).hexdigest()


def _bump(key, ttl):
    n = int(store.redis("INCR", key) or 0)
    if n == 1:
        store.redis("EXPIRE", key, ttl)
    return n


def start_email(email, ip=""):
    """Creates and sends a 6-digit code. Raises LoginError (bad email, too many codes, mail not set up)."""
    email = clean_email(email)
    if _bump(f"s:ecount:{email}", 3600) > SENDS_PER_HOUR or (ip and _bump(f"s:eip:{ip}", 3600) > SENDS_PER_IP_HOUR):
        raise LoginError("Too many codes asked for. Wait an hour, or use Google.")
    code = f"{secrets.randbelow(10 ** 6):06d}"
    store.redis("SET", f"s:ecode:{email}", json.dumps({"h": _hash(email, code), "tries": 0}), "EX", CODE_TTL)
    deliver(email, code)
    return email


def verify_email(email, code):
    """True once for the right code; wrong codes count towards CODE_TRIES."""
    email = clean_email(email)
    code = re.sub(r"\D", "", str(code or ""))
    raw = store.redis("GET", f"s:ecode:{email}")
    if not raw:
        raise LoginError("That code expired. Ask for a new one.")
    rec = json.loads(raw)
    if len(code) == 6 and hmac.compare_digest(rec["h"], _hash(email, code)):
        store.redis("DEL", f"s:ecode:{email}")
        return email
    rec["tries"] += 1
    if rec["tries"] >= CODE_TRIES:
        store.redis("DEL", f"s:ecode:{email}")
        raise LoginError("Too many wrong tries. Ask for a new code.")
    store.redis("SET", f"s:ecode:{email}", json.dumps(rec), "KEEPTTL")
    raise LoginError("That code isn't right. Check the latest email and try again.")


def deliver(email, code):
    """Sends the code with Resend. Without a key: printed to the server log locally, refused on Vercel."""
    key, brand = _env("RESEND_API_KEY"), _env("BRAND_NAME", "ReplyInbox")
    if not key:
        if os.environ.get("VERCEL"):
            raise LoginError("Email login isn't switched on yet. Use Google for now.")
        print(f"[dev] login code for {email}: {code}", file=sys.stderr)
        return
    sender = _env("MAIL_FROM", f"{brand} <login@replyinbox.in>")
    html = (f"<div style=\"font-family:system-ui,sans-serif;max-width:420px;margin:auto;padding:24px\">"
            f"<h2 style=\"margin:0 0 8px\">Your {brand} code</h2>"
            f"<p style=\"color:#555\">Enter this code to sign in. It works for 10 minutes.</p>"
            f"<p style=\"font-size:34px;font-weight:800;letter-spacing:8px;margin:18px 0\">{code}</p>"
            f"<p style=\"color:#888;font-size:13px\">If you didn't ask for it, ignore this email.</p></div>")
    try:
        r = requests.post("https://api.resend.com/emails", timeout=15, headers={"Authorization": f"Bearer {key}"},
                          json={"from": sender, "to": [email], "subject": f"{code} is your {brand} code",
                                "html": html, "text": f"Your {brand} code: {code} (valid 10 minutes)"})
    except requests.RequestException:
        raise LoginError("We couldn't send the email. Try again, or use Google.")
    if not r.ok:
        print(f"Resend refused the login email: {r.status_code} {r.text[:200]}", file=sys.stderr)
        raise LoginError("We couldn't send the email. Try again, or use Google.")


def email_ready():
    """Email codes can be sent (Resend key set), or this is a local run where codes go to the log."""
    return bool(_env("RESEND_API_KEY")) or not os.environ.get("VERCEL")


# ---------- Google ----------

def google_client():
    return (_env("GOOGLE_CLIENT_ID") or _env("YT_CLIENT_ID"), _env("GOOGLE_CLIENT_SECRET") or _env("YT_CLIENT_SECRET"))


def google_ready():
    cid, secret = google_client()
    return bool(cid and secret)


def google_url(redirect_uri, state):
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": google_client()[0], "redirect_uri": redirect_uri, "response_type": "code",
        "scope": "openid email profile", "state": state, "prompt": "select_account"})


def google_finish(code, redirect_uri):
    """The verified Google profile {sub, email, email_verified, name, picture} for an authorization code."""
    cid, secret = google_client()
    try:
        r = requests.post("https://oauth2.googleapis.com/token", timeout=20, data={
            "code": code, "client_id": cid, "client_secret": secret, "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"})
        token = r.json().get("access_token") if r.ok else None
        if not token:
            raise LoginError("Google sign-in didn't finish. Try again.")
        r = requests.get("https://openidconnect.googleapis.com/v1/userinfo", timeout=20,
                         headers={"Authorization": f"Bearer {token}"})
        if not r.ok:
            raise LoginError("Google sign-in didn't finish. Try again.")
        return r.json()
    except requests.RequestException:
        raise LoginError("Google didn't answer. Try again.")
