"""Tests for the multi-account app, with Instagram mocked. Run: python3 -m unittest test_saas (in saas/)."""
import base64
import hashlib
import hmac
import io
import json
import re
import os
import time
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlparse

os.environ.update(IG_APP_ID="123", IG_APP_SECRET="shh", CRON_SECRET="cron", OWNER_PASSWORD="boss",
                  SECRET_KEY="test", FREE_MONTHLY_DMS="3")
for k in ("UPSTASH_REDIS_REST_URL", "KV_REST_API_URL", "VERCEL"):
    os.environ.pop(k, None)

import ai_agent  # noqa: E402
import app as saas  # noqa: E402
import demo  # noqa: E402
import engine  # noqa: E402
import store  # noqa: E402
import users  # noqa: E402
import billing  # noqa: E402
import youtube  # noqa: E402


class Resp:
    def __init__(self, data, status=200):
        self.data, self.status_code = data, status
        self.ok = status < 400
        self.text = json.dumps(data)
        self.content = self.text.encode()

    def json(self):
        return self.data

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError(self.text)


class FakeInstagram:
    """Records every call; answers like the Instagram API."""

    def __init__(self):
        self.calls, self.follows, self.fail_dm, self.dead, self.comments = [], True, False, False, []
        self.me = {"id": "asid9", "user_id": "1789", "username": "creator", "name": "C", "profile_picture_url": "", "followers_count": 500}
        self.media = [
            {"id": "777", "caption": "Naya reel! Comment GUIDE and I'll DM you", "timestamp": "2999-01-01T00:00:00+0000",
             "media_product_type": "REELS", "comments_count": 30, "thumbnail_url": "t.jpg"},
            {"id": "555", "caption": "Old reel. Comment OLD", "timestamp": "2020-01-01T00:00:00+0000",
             "media_product_type": "REELS", "comments_count": 50},
        ]

    def get(self, url, params=None, timeout=None):
        self.calls.append(("GET", url, params))
        if url.endswith("/access_token"):
            return Resp({"access_token": "LONG", "expires_in": 5184000})
        if url.endswith("/me"):
            return Resp(self.me)
        if url.endswith("/refresh_access_token"):
            return Resp({"access_token": "NEWER"})
        fields = (params or {}).get("fields", "")
        if url.endswith("/comments"):
            return Resp({"data": self.comments})
        if url.endswith("/me/media"):
            return Resp({"data": self.media})
        if url.endswith("/insights"):
            return Resp({"data": [{"name": "views", "values": [{"value": 2000}]}, {"name": "saved", "values": [{"value": 7}]}]})
        if "caption" in fields:
            mid = url.rsplit("/", 1)[1]
            return Resp(next(m for m in self.media if m["id"] == mid))
        if "is_user_follow_business" in fields:
            return Resp({"username": "fan", "is_user_follow_business": self.follows})
        return Resp({"username": "fan"})

    def post(self, url, params=None, json=None, data=None, timeout=None, **kw):
        self.calls.append(("POST", url, json or data))
        if self.dead and "graph.instagram.com" in url:
            return Resp({"error": {"code": 190, "message": "Session invalidated"}}, 400)
        if url.endswith("/oauth/access_token"):
            return Resp({"access_token": "SHORT", "user_id": 1789, "permissions": []})
        if url.endswith("/messages") and self.fail_dm:
            return Resp({"error": {"code": 10, "error_subcode": 2534001}}, 400)
        return Resp({"success": True, "id": "x"})

    def messages(self):
        return [c[2] for c in self.calls if c[1].endswith("/messages")]

    def replies(self):
        return [c[2] for c in self.calls if c[1].endswith("/replies")]


def signed(body):
    raw = json.dumps(body).encode()
    return raw, {"X-Hub-Signature-256": "sha256=" + hmac.new(b"shh", raw, hashlib.sha256).hexdigest(),
                 "Content-Type": "application/json"}


class FakeClaude:
    """Stands in for the Anthropic client: returns the queued answers and records each request."""

    def __init__(self):
        self.requests, self.answers = [], []
        self.beta = self
        self.messages = self

    def create(self, **kw):
        self.requests.append(kw)
        answer = self.answers.pop(0) if self.answers else {"reply": "Hi!", "needs_human": False, "reason": "", "suggested_reply": ""}
        if answer == "refusal":
            return mock.Mock(stop_reason="refusal", content=[])
        return mock.Mock(stop_reason="end_turn", content=[mock.Mock(type="text", text=json.dumps(answer))])


class FakeGoogle:
    """Google OAuth + YouTube Data API, enough for the YouTube scheduler."""

    def __init__(self):
        self.calls, self.fail = [], {}
        self.public = set()

    def post(self, url, data=None, **kw):
        self.calls.append(("POST", url, data))
        if url.endswith("/token"):
            if data.get("grant_type") == "authorization_code":
                return Resp({"access_token": "ya29.A", "refresh_token": "1//R", "expires_in": 3599,
                             "scope": youtube.SCOPES})
            return Resp({"access_token": "ya29.B", "expires_in": 3599})
        return Resp({})

    def request(self, method, url, params=None, json=None, **kw):
        self.calls.append((method, url, params, json))
        if url in self.fail:
            return Resp({"error": {"message": "nope", "errors": [{"reason": self.fail[url]}]}}, 403)
        if url.endswith("/channels"):
            return Resp({"items": [{"id": "UC1", "snippet": {"title": "Om Tech", "thumbnails": {"default": {"url": "p.jpg"}}}}]})
        if url.endswith("/videos") and method == "GET":
            return Resp({"items": [{"id": i, "status": {"privacyStatus": "public" if i in self.public else "private"}}
                                   for i in params["id"].split(",")]})
        if method == "DELETE":
            return Resp({}, 204)
        return Resp({"id": (json or {}).get("id", "")})


def dm(text, sender="88", mid=""):
    return {"entry": [{"id": "1789", "messaging": [{"sender": {"id": sender}, "message": {"text": text, "mid": mid or text}}]}]}


def comment(text, cid="c1", media="555", who="fan"):
    return {"entry": [{"id": "1789", "changes": [{"field": "comments", "value": {
        "id": cid, "text": text, "from": {"id": "77", "username": who}, "media": {"id": media}}}]}]}


class SaasTest(unittest.TestCase):
    def setUp(self):
        store._memory.data.clear()
        store._memory.expiry.clear()
        self.ig = FakeInstagram()
        patches = [mock.patch.object(m.requests, n, getattr(self.ig, n if n != "delete" else "post"))
                   for m in (saas, engine) for n in ("get", "post")]
        patches.append(mock.patch.object(saas.requests, "delete", lambda *a, **k: Resp({})))
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        # webhooks run in a thread locally; in tests (as on Vercel) they finish before the response, so checks don't race
        p = mock.patch.object(saas, "run_task", lambda fn, *args: fn(*args))
        p.start()
        self.addCleanup(p.stop)
        self.c = saas.app.test_client()
        self.codes = {}
        p = mock.patch.object(users, "deliver", lambda email, code: self.codes.__setitem__(email, code))
        p.start()
        self.addCleanup(p.stop)

    def signin(self, client=None, email="om@example.com"):
        """Signs in to ReplyInbox with an email code; returns where it sends you next."""
        c = client or self.c
        self.assertEqual(c.post("/auth/email/start", json={"email": email}).status_code, 200)
        r = c.post("/auth/email/verify", json={"email": email, "code": self.codes[email]})
        self.assertEqual(r.status_code, 200)
        return r.get_json()["next"]

    def connect_ig(self, client=None):
        c = client or self.c
        r = c.get("/login")
        state = parse_qs(urlparse(r.location).query)["state"][0]
        return c.get(f"/auth/callback?code=abc&state={state}")

    def login(self, client=None, email="om@example.com"):
        c = client or self.c
        with c.session_transaction() as sess:
            signed_in = bool(sess.get("user"))
        if not signed_in:
            self.signin(c, email)
        r = self.connect_ig(c)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.location.endswith("/app"))

    def put_rule(self, key, **rule):
        body = {"enabled": True, "keywords": ["PROMPTS"], "comment_reply": "Check your DM 📩",
                "require_follow": True, "dm": "Here you go https://x.com", **rule}
        return self.c.put(f"/api/rules/{key}", json=body)

    def hook(self, body):
        raw, headers = signed(body)
        return self.c.post("/webhook", data=raw, headers=headers)

    def test_login_saves_account_and_subscribes(self):
        self.assertTrue(self.c.get("/login").location.endswith("/signin"))  # sign in to ReplyInbox first
        self.assertTrue(self.signin().endswith("/connect"))  # then Instagram is required before the dashboard
        self.assertTrue(self.c.get("/app").location.endswith("/connect"))
        r = self.c.get("/login")
        q = parse_qs(urlparse(r.location).query)
        self.assertIn("instagram_business_manage_messages", q["scope"][0])
        self.assertEqual(q["redirect_uri"][0], "http://localhost/auth/callback")
        self.login()
        acc = store.load_account("1789")
        self.assertEqual((acc["username"], acc["token"], acc["asid"]), ("creator", "LONG", "asid9"))
        self.assertTrue(any(c[1].endswith("/me/subscribed_apps") for c in self.ig.calls))
        me = self.c.get("/api/me").get_json()
        self.assertNotIn("token", me["account"])

    def test_login_rejects_bad_state(self):
        self.signin()
        self.c.get("/login")
        r = self.c.get("/auth/callback?code=abc&state=wrong")
        self.assertIn("/connect?error=", r.location)
        self.assertIsNone(store.load_account("1789"))

    def test_invite_only(self):
        with mock.patch.object(saas, "SIGNUPS", "invite"), mock.patch.object(saas, "INVITE_CODES", {"BETA"}):
            self.assertEqual(self.c.post("/auth/email/start", json={"email": "a@b.co", "invite": "nope"}).status_code, 403)
            self.assertEqual(self.c.post("/auth/email/start", json={"email": "a@b.co", "invite": "beta"}).status_code, 200)
            self.c.post("/auth/email/verify", json={"email": "a@b.co", "code": self.codes["a@b.co"]})
            self.assertIn("instagram.com/oauth", self.c.get("/login").location)

    def test_user_login_email_code(self):
        self.assertEqual(self.c.post("/auth/email/start", json={"email": "not-an-email"}).status_code, 400)
        self.assertEqual(self.c.post("/auth/email/start", data="email=a@b.co").status_code, 415)  # JSON only (no cross-site forms)
        self.c.post("/auth/email/start", json={"email": "Om@Example.com "})
        code = self.codes["om@example.com"]
        wrong = "000000" if code != "000000" else "111111"
        for _ in range(4):
            self.assertIn("isn't right", self.c.post("/auth/email/verify", json={"email": "om@example.com", "code": wrong}).get_json()["error"])
        self.assertIn("Too many", self.c.post("/auth/email/verify", json={"email": "om@example.com", "code": wrong}).get_json()["error"])
        self.assertIn("expired", self.c.post("/auth/email/verify", json={"email": "om@example.com", "code": code}).get_json()["error"])
        for _ in range(4):
            self.c.post("/auth/email/start", json={"email": "om@example.com"})
        self.assertIn("Too many codes", self.c.post("/auth/email/start", json={"email": "om@example.com"}).get_json()["error"])
        # a code works once; the same email always reaches the same user
        self.assertTrue(self.signin(email="two@example.com").endswith("/connect"))
        uid = users.by_email("two@example.com")["id"]
        self.c.post("/logout")
        self.signin(email="two@example.com")
        with self.c.session_transaction() as sess:
            self.assertEqual(sess["user"], uid)
        self.assertNotIn("two@example.com", [k for k in self.codes if store.redis("GET", f"s:ecode:{k}")])

    def test_user_login_google(self):
        self.assertIn("isn", self.c.get("/auth/google", follow_redirects=True).get_data(as_text=True))  # not set up
        self.signin(email="om@example.com")  # an email user first
        uid = users.by_email("om@example.com")["id"]
        self.c.post("/logout")
        with mock.patch.dict(os.environ, GOOGLE_CLIENT_ID="gid", GOOGLE_CLIENT_SECRET="gs"), \
             mock.patch.object(users, "google_finish", lambda code, uri: {"sub": "g1", "email": "Om@example.com",
                                                                          "email_verified": True, "name": "Om", "picture": "p.jpg"}):
            r = self.c.get("/auth/google")
            q = parse_qs(urlparse(r.location).query)
            self.assertEqual((q["scope"][0], q["redirect_uri"][0]), ("openid email profile", "http://localhost/auth/google/callback"))
            self.assertIn("expired", self.c.get("/auth/google/callback?code=x&state=bad", follow_redirects=True).get_data(as_text=True))
            r = self.c.get("/auth/google")
            r = self.c.get(f"/auth/google/callback?code=x&state={parse_qs(urlparse(r.location).query)['state'][0]}")
            self.assertTrue(r.location.endswith("/connect"))
        user = users.get(uid)  # same email → same user, now linked to Google
        self.assertEqual((user["google"], user["name"]), ("g1", "Om"))
        self.assertIn("om@example.com", self.c.get("/connect").get_data(as_text=True))

    def test_accounts_belong_to_their_user(self):
        self.login()  # om@example.com connects @creator (1789)
        other = saas.app.test_client()
        self.signin(other, "mallory@example.com")
        with other.session_transaction() as sess:
            sess["uid"] = "1789"  # pretends to be on @creator
        self.assertEqual(other.get("/api/me").status_code, 401)
        self.assertTrue(other.get("/app").location.endswith("/connect"))
        self.assertEqual(other.post("/api/switch", json={"id": "1789"}).status_code, 403)
        r = self.connect_ig(other)  # can't take over an account another login owns
        self.assertIn("another", urlparse(r.location).query.replace("+", " "))
        self.assertEqual(store.load_account("1789")["owner"], users.by_email("om@example.com")["id"])

    def test_plan_limits_and_plan_follows_the_user(self):
        self.login()
        user = users.by_email("om@example.com")
        self.ig.me = {"id": "asid3", "user_id": "3003", "username": "second.page", "name": "S", "profile_picture_url": "", "followers_count": 5}
        with mock.patch.object(users.plans, "LOCKS_ON", True):
            r = self.connect_ig()  # Free plan: 1 account
            self.assertIn("allows 1 Instagram account", urlparse(r.location).query.replace("+", " "))
            self.assertIsNone(store.load_account("3003"))
            self.assertIn("1 of 1 account", self.c.get("/connect").get_data(as_text=True))
            users.set_plan(users.get(user["id"]), "pro")  # Pro: 3 accounts
            self.assertTrue(self.connect_ig().location.endswith("/app"))
        self.assertEqual([plans_of["plan"] for plans_of in users.accounts(users.get(user["id"]))], ["pro", "pro"])
        # the owner page sets the plan on the login: every account follows
        h = {"Authorization": "Basic " + base64.b64encode(b"x:boss").decode()}
        self.c.post("/owner/plan", json={"id": "1789", "plan": "creator"}, headers=h)
        self.assertEqual({store.load_account(i)["plan"] for i in ("1789", "3003")}, {"creator"})
        page = self.c.get("/owner", headers=h).get_data(as_text=True)
        self.assertIn("om@example.com", page)
        # one login with two Instagram accounts: one row group, one plan picker, counted once
        self.assertEqual(page.count("<select data-p"), 1)
        self.assertEqual(page.count("<b>om@example.com</b>"), 1)
        self.assertIn("Logins <span class=\"hl\">1</span>", page)
        self.assertIn("2 Instagram accounts", page)
        self.assertIn("Creator 1", page)
        self.assertIn(f"MRR ₹{saas.plans.PLANS['creator']['price']}", page)
        # the owner can remove an account: it leaves the login and its data is gone; the demo never shows up
        self.c.application.test_client().get("/demo")
        self.assertNotIn("demo.creator", self.c.get("/owner", headers=h).get_data(as_text=True))
        self.assertEqual(self.c.post("/owner/remove", json={"id": "3003"}).status_code, 401)
        self.assertEqual(self.c.post("/owner/remove", headers=h, json={"id": "nope"}).status_code, 400)
        self.assertTrue(self.c.post("/owner/remove", headers=h, json={"id": "3003"}).get_json()["ok"])
        self.assertIsNone(store.load_account("3003"))
        self.assertEqual(users.get(user["id"])["accounts"], ["1789"])
        # removing the last account sends you to connect one again
        self.assertEqual(self.c.post("/api/disconnect", json={}).get_json()["next"], "/connect")
        self.assertEqual(users.get(user["id"])["accounts"], [])
        self.assertTrue(self.c.get("/app").location.endswith("/connect"))

    def test_accounts_from_before_logins_are_claimed(self):
        store.save_account({"id": "1789", "username": "creator", "token": "OLD", "plan": "pro", "created": 1})
        self.login()  # signs in, logs in with Instagram as the same account
        acc, user = store.load_account("1789"), users.by_email("om@example.com")
        self.assertEqual((acc["owner"], acc["token"], user["plan"], acc["plan"]), (user["id"], "LONG", "pro", "pro"))

    def test_billing_with_razorpay(self):
        self.login()
        uid = users.by_email("om@example.com")["id"]
        self.assertFalse(self.c.get("/api/billing").get_json()["ready"])
        self.assertIn("launching soon", self.c.get("/").get_data(as_text=True))
        self.assertEqual(self.c.post("/api/billing/order", json={"plan": "creator", "period": "month"}).status_code, 400)
        orders = []

        def rzp(url, auth=None, json=None, timeout=None, **kw):
            orders.append((url, auth, json))
            return Resp({"id": f"order_{len(orders)}", "amount": json["amount"]})
        self.enterContext(mock.patch.dict(os.environ, RAZORPAY_KEY_ID="rzp_test_k", RAZORPAY_KEY_SECRET="sek", RAZORPAY_WEBHOOK_SECRET="wh"))
        self.enterContext(mock.patch.object(billing.requests, "post", rzp))
        self.assertIn("Get Creator", self.c.get("/").get_data(as_text=True))
        self.assertIn("/app/billing", self.c.get("/signin?next=/app/billing").location)  # already signed in → straight to billing
        st = self.c.get("/api/billing").get_json()
        self.assertEqual((st["plan"], st["ready"], st["test"], st["quotes"]["creator"]["year"]["amount"]), ("free", True, True, 1999))
        # the price comes from the server, whatever the browser sends
        o = self.c.post("/api/billing/order", json={"plan": "creator", "period": "month", "amount": 1}).get_json()
        self.assertEqual((o["amount"], o["key"], orders[0][2]["amount"], orders[0][2]["notes"]["user"]), (19900, "rzp_test_k", 19900, uid))
        self.assertEqual(self.c.post("/api/billing/order", json={"plan": "free", "period": "month"}).status_code, 400)
        sign = lambda oid, pid: hmac.new(b"sek", f"{oid}|{pid}".encode(), hashlib.sha256).hexdigest()
        bad = self.c.post("/api/billing/verify", json={"order_id": o["order_id"], "payment_id": "pay_1", "signature": "nope"})
        self.assertEqual(bad.status_code, 400)
        r = self.c.post("/api/billing/verify", json={"order_id": o["order_id"], "payment_id": "pay_1", "signature": sign(o["order_id"], "pay_1")}).get_json()
        self.assertEqual(r["plan"], "creator")
        self.assertAlmostEqual(r["until"], time.time() + 30 * 86400, delta=60)
        self.assertEqual(store.load_account("1789")["plan"], "creator")  # every account under the login follows
        self.assertEqual(self.c.get("/api/me").get_json()["account"]["pro"], True)
        # paying twice for the same order changes nothing
        again = self.c.post("/api/billing/verify", json={"order_id": o["order_id"], "payment_id": "pay_1", "signature": sign(o["order_id"], "pay_1")}).get_json()
        self.assertEqual(again["until"], r["until"])
        self.assertEqual(len(users.get(uid)["payments"]), 1)
        # upgrading to Pro turns ~30 Creator days (₹199) into ~12 Pro days (₹499), on top of the new month
        q = self.c.get("/api/billing").get_json()["quotes"]["pro"]["month"]
        self.assertAlmostEqual(q["credit_days"], 30 * 199 / 499, delta=0.2)
        # the webhook activates too (when the browser closed early); bad signatures are refused
        o2 = self.c.post("/api/billing/order", json={"plan": "pro", "period": "year"}).get_json()
        body = json.dumps({"event": "payment.captured", "payload": {"payment": {"entity": {
            "id": "pay_2", "order_id": o2["order_id"], "status": "captured", "amount": 499900}}}}).encode()
        self.assertEqual(self.c.post("/billing/webhook", data=body, headers={"X-Razorpay-Signature": "x"}).status_code, 400)
        wsig = hmac.new(b"wh", body, hashlib.sha256).hexdigest()
        self.assertEqual(self.c.post("/billing/webhook", data=body, headers={"X-Razorpay-Signature": wsig}).status_code, 200)
        u = users.get(uid)
        self.assertEqual(u["plan"], "pro")
        self.assertGreater(u["plan_until"], time.time() + 365 * 86400)  # a year plus the Creator credit
        rid = u["payments"][0]["id"]
        self.assertIn("₹4,999", self.c.get(f"/app/billing/receipt/{rid}").get_data(as_text=True))
        self.assertEqual(self.c.get("/app/billing/receipt/order_999").status_code, 404)
        h = {"Authorization": "Basic " + base64.b64encode(b"x:boss").decode()}
        self.assertIn("pay_2", self.c.get("/owner", headers=h).get_data(as_text=True))
        # a period that ran out falls back to Free, with a banner
        u["plan_until"] = int(time.time()) - 10
        users.save(u)
        users.sync_plan(u)
        self.assertEqual(billing.plans.plan_of(store.load_account("1789")), "free")
        self.assertEqual(self.c.get("/api/me").get_json()["billing"]["kind"], "expired")
        u["plan_until"] = int(time.time()) + 2 * 86400
        users.save(u)
        self.assertEqual(self.c.get("/api/me").get_json()["billing"]["kind"], "soon")
        # team members can't see or pay
        acc = store.load_account("1789")
        acc["team"] = [{"id": "m1", "name": "Ed", "role": "manager", "invited": 1, "joined": 1}]
        store.save_account(acc)
        ed = saas.app.test_client()
        with ed.session_transaction() as sess:
            sess.update(uid="1789", member="m1")
        self.assertEqual(ed.get("/api/billing").status_code, 403)
        self.assertEqual(ed.post("/api/billing/order", json={"plan": "pro", "period": "month"}).status_code, 403)

    def test_reviewer_login_and_billing_without_instagram(self):
        self.assertNotIn("Sign in with a password", self.c.get("/signin").get_data(as_text=True))
        self.assertEqual(self.c.post("/auth/password", json={"email": "r@x.co", "password": "p"}).status_code, 400)
        self.enterContext(mock.patch.dict(os.environ, REVIEW_EMAIL="Review@x.co", REVIEW_PASSWORD="s3cret-pass"))
        self.assertIn("Sign in with a password", self.c.get("/signin").get_data(as_text=True))
        self.assertIn("don't match", self.c.post("/auth/password", json={"email": "review@x.co", "password": "wrong"}).get_json()["error"])
        r = self.c.post("/auth/password", json={"email": "review@x.co", "password": "s3cret-pass"}).get_json()
        self.assertEqual(r["next"], "/app/billing")  # straight to the plans, even without Instagram
        page = self.c.get("/app/billing")
        self.assertEqual(page.status_code, 200)
        self.assertIn("connect your Instagram account", page.get_data(as_text=True))
        self.assertEqual(self.c.get("/api/billing").get_json()["plan"], "free")  # billing API works without an account
        self.assertTrue(self.c.get("/app").location.endswith("/connect"))  # the rest still needs Instagram
        self.assertEqual(self.c.get("/api/me").status_code, 401)
        for _ in range(9):
            self.c.post("/auth/password", json={"email": "x@x.co", "password": "x"})
        self.assertIn("Too many", self.c.post("/auth/password", json={"email": "review@x.co", "password": "s3cret-pass"}).get_json()["error"])

    def test_api_needs_login_and_json(self):
        self.assertEqual(self.c.get("/api/rules").status_code, 401)
        self.login()
        self.assertEqual(self.c.put("/api/rules/555", data="enabled=1").status_code, 415)
        self.assertEqual(self.put_rule("555", dm="").status_code, 400)  # on without a final DM
        self.assertEqual(self.put_rule("../x").status_code, 404)
        self.assertEqual(self.put_rule("abc").status_code, 400)
        self.assertEqual(self.put_rule("555").status_code, 200)

    def test_comment_flow_with_follow_gate(self):
        self.login()
        self.put_rule("555")
        self.assertEqual(self.hook(comment("promts pls")).status_code, 200)  # one typo still matches
        first = self.ig.messages()[0]
        self.assertEqual(first["recipient"], {"comment_id": "c1"})
        self.assertEqual(first["message"]["attachment"]["payload"]["buttons"][0]["payload"], "GET|555|555")
        self.assertEqual(self.ig.replies(), [{"message": "@fan Check your DM 📩"}])
        # the same comment again (Instagram retries webhooks): handled once
        self.hook(comment("promts pls"))
        self.assertEqual(len(self.ig.messages()), 1)

        # tap → not following → follow prompt; follow → "I followed" → link
        self.ig.follows = False
        tap = {"entry": [{"id": "1789", "messaging": [{"sender": {"id": "77"}, "postback": {"payload": "GET|555"}}]}]}
        self.hook(tap)
        prompt = self.ig.messages()[-1]["message"]["attachment"]["payload"]
        self.assertIn("Follow me first", prompt["text"])
        self.assertEqual(prompt["buttons"][0]["url"], "https://www.instagram.com/creator/")
        self.ig.follows = True
        tap["entry"][0]["messaging"][0]["postback"]["payload"] = "FOLLOWED|555"
        self.hook(tap)
        self.assertEqual(self.ig.messages()[-1]["message"], {"text": "Here you go https://x.com"})
        totals = self.c.get("/api/me").get_json()["totals"]
        self.assertEqual((totals["links_sent"], totals["gate_follows"], totals["comment_replies"]), (1, 1, 1))

    def test_other_reels_and_unknown_accounts_are_ignored(self):
        self.login()
        self.put_rule("555")
        self.hook(comment("PROMPTS", media="999"))  # reel without a rule, no fallback
        body = comment("PROMPTS", cid="c2")
        body["entry"][0]["id"] = "4242"  # not connected
        self.hook(body)
        self.assertEqual(self.ig.messages(), [])

    def test_keyword_rule_answers_dms_and_any_reel(self):
        self.login()
        self.put_rule("kw:GUIDE", keywords=["GUIDE"], require_follow=False, comment_reply="")
        self.hook(comment("guide please", media="999"))
        self.assertEqual(self.ig.messages()[-1]["message"], {"text": "Here you go https://x.com"})
        self.assertEqual(self.ig.replies(), [])  # empty reply text = no public reply
        dm = {"entry": [{"id": "1789", "messaging": [{"sender": {"id": "88"}, "message": {"text": "GUIDE"}}]}]}
        self.hook(dm)
        self.assertEqual(self.ig.messages()[-1]["recipient"], {"id": "88"})

    def test_bad_signature_rejected(self):
        raw, headers = signed(comment("PROMPTS"))
        headers["X-Hub-Signature-256"] = "sha256=00"
        self.assertEqual(self.c.post("/webhook", data=raw, headers=headers).status_code, 403)

    def test_monthly_limit_and_pause(self):
        self.login()
        self.put_rule("555", require_follow=False)
        for i in range(4):
            self.hook(comment("PROMPTS", cid=f"c{i}"))
        self.assertEqual(len(self.ig.messages()), 3)  # FREE_MONTHLY_DMS=3
        self.assertEqual(len(self.ig.replies()), 4)  # the public reply still goes out
        self.c.post("/api/pause", json={"paused": True})
        self.hook(comment("PROMPTS", cid="c9"))
        self.assertEqual(len(self.ig.replies()), 4)

    def test_logged_out_account_stops(self):
        self.login()
        self.put_rule("555")
        self.ig.dead = True
        self.hook(comment("PROMPTS"))
        self.hook(comment("PROMPTS", cid="c2"))
        self.assertEqual(sum(1 for c in self.ig.calls if c[1].endswith("/messages")), 1)  # stopped after the 190
        self.ig.dead = False
        self.assertEqual(self.c.get("/api/me").get_json()["blocked"], "logged_out")
        self.login()  # logging in again clears it
        self.assertEqual(self.c.get("/api/me").get_json()["blocked"], "")

    def test_data_deletion_and_disconnect(self):
        self.login()
        payload = base64.urlsafe_b64encode(json.dumps({"user_id": "asid9"}).encode()).decode().rstrip("=")
        sig = base64.urlsafe_b64encode(hmac.new(b"shh", payload.encode(), hashlib.sha256).digest()).decode().rstrip("=")
        self.assertEqual(self.c.post("/meta/data-deletion", data={"signed_request": "bad.sig"}).status_code, 400)
        r = self.c.post("/meta/data-deletion", data={"signed_request": f"{sig}.{payload}"}).get_json()
        self.assertIsNone(store.load_account("1789"))
        self.assertIn("deleted", self.c.get(f"/deletion?code={r['confirmation_code']}").get_data(as_text=True))
        self.login()
        self.c.post("/api/disconnect", json={})
        self.assertIsNone(store.load_account("1789"))
        self.assertEqual(store.account_ids(), [])

    def test_cron_refresh_and_owner(self):
        self.login()
        acc = store.load_account("1789")
        acc["token_at"] = 0
        store.save_account(acc)
        self.assertEqual(self.c.get("/cron/refresh-tokens").status_code, 401)
        r = self.c.get("/cron/refresh-tokens", headers={"Authorization": "Bearer cron"}).get_json()
        self.assertEqual(r["refreshed"], 1)
        self.assertEqual(store.load_account("1789")["token"], "NEWER")
        self.assertEqual(self.c.get("/owner").status_code, 401)
        auth = {"Authorization": "Basic " + base64.b64encode(b"x:boss").decode()}
        self.assertIn("@creator", self.c.get("/owner", headers=auth).get_data(as_text=True))

    def test_caption_keyword(self):
        cases = {'Comment "GPT" for full setup': "GPT", "comment karo GUIDE 🔥": "GUIDE", "GPT comment karo": "GPT",
                 "Comment below 👇 PROMPTS": "PROMPTS", "comment below your thoughts": "", "likho AUDIT": "AUDIT",
                 "Comment “Otto” and I will DM": "OTTO", "": ""}
        for caption, want in cases.items():
            self.assertEqual(engine.caption_keyword(caption), want, caption)

    def turn_on_auto(self, **template):
        body = {"enabled": True, "template": {"comment_reply": "Sent 📩", "require_follow": False,
                                              "dm": "Here: https://x.com/free?k={keyword}", **template}}
        return self.c.put("/api/auto-setup", json=body)

    def test_auto_setup_on_first_comment_and_undo(self):
        self.login()
        self.assertEqual(self.c.put("/api/auto-setup", json={"enabled": True, "template": {}}).status_code, 400)
        self.assertEqual(self.turn_on_auto().status_code, 200)
        self.hook(comment("guide please", media="777"))
        rule = self.c.get("/api/rules").get_json()["reels"]["777"]
        self.assertEqual((rule["keywords"], rule["auto"], rule["dm"]), (["GUIDE"], True, "Here: https://x.com/free?k=GUIDE"))
        self.assertEqual(self.ig.messages()[-1]["message"], {"text": "Here: https://x.com/free?k=GUIDE"})
        recent = self.c.get("/api/auto-setup").get_json()["recent"]
        self.assertEqual(recent[0]["keyword"], "GUIDE")
        self.c.post("/api/auto-setup/777/undo", json={})
        self.assertNotIn("777", self.c.get("/api/rules").get_json()["reels"])
        self.assertTrue(self.c.get("/api/auto-setup").get_json()["recent"][0]["undone"])
        self.hook(comment("GUIDE", cid="c2", media="777"))  # undone stays undone
        self.assertNotIn("777", self.c.get("/api/rules").get_json()["reels"])

    def test_auto_setup_skips_old_reels_and_works_from_reel_list(self):
        self.login()
        self.turn_on_auto()
        self.hook(comment("OLD", media="555"))  # posted before auto-setup was turned on
        self.assertNotIn("555", self.c.get("/api/rules").get_json()["reels"])
        data = self.c.get("/api/reels?fresh=1").get_json()
        self.assertEqual(data["auto_created"], ["777"])

    def test_report_counts_per_reel(self):
        self.login()
        self.put_rule("777", keywords=["GUIDE"])
        self.hook(comment("GUIDE", media="777"))
        tap = {"entry": [{"id": "1789", "messaging": [{"sender": {"id": "77"}, "postback": {"payload": "FOLLOWED|777|777"}}]}]}
        self.hook(tap)
        reels = {r["id"]: r for r in self.c.get("/api/report").get_json()["reels"]}
        r = reels["777"]
        self.assertEqual((r["views"], r["comments"], r["keyword"], r["dm"], r["link"], r["follow"]), (2000, 30, 1, 1, 1, 1))
        self.assertEqual(r["per_1k"], 0.5)
        self.assertTrue(r["has_rule"])
        self.assertIn("50 comments and no automation", reels["555"]["tips"][0])
        self.assertEqual(self.c.get("/app/report").status_code, 200)

    def test_mcp_server(self):
        self.login()
        self.assertEqual(self.c.post("/mcp", json={}).status_code, 401)
        key = self.c.post("/api/mcp-key", json={}).get_json()["key"]
        H = {"Authorization": f"Bearer {key}"}
        rpc = lambda method, params=None, i=1: self.c.post("/mcp", headers=H, json={
            "jsonrpc": "2.0", "id": i, "method": method, **({"params": params} if params is not None else {})}).get_json()
        call = lambda name, args: rpc("tools/call", {"name": name, "arguments": args})["result"]
        self.assertEqual(rpc("initialize", {"protocolVersion": "2025-06-18"})["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(self.c.post("/mcp", headers=H, json={"jsonrpc": "2.0", "method": "notifications/initialized"}).status_code, 202)
        names = [t["name"] for t in rpc("tools/list")["result"]["tools"]]
        self.assertIn("save_automation", names)
        self.assertEqual(call("get_account_summary", {})["structuredContent"]["account"], "@creator")
        self.assertEqual(call("list_reels", {})["structuredContent"]["reels"][0]["id"], "777")
        self.assertTrue(call("save_automation", {"target": "777", "keywords": ["GUIDE"]})["isError"])  # no final DM
        saved = call("save_automation", {"target": "777", "keywords": ["GUIDE"], "final_dm": "https://x.com"})["structuredContent"]["saved"]
        self.assertEqual((saved["keywords"], saved["require_follow"]), (["GUIDE"], True))
        self.assertEqual(call("save_automation", {"target": "777", "require_follow": False})["structuredContent"]["saved"]["final_dm"], "https://x.com")
        self.assertFalse(call("set_automation_enabled", {"automation_id": "777", "enabled": False})["structuredContent"]["enabled"])
        self.assertTrue(call("pause_all_automations", {"paused": True})["structuredContent"]["paused"])
        self.assertEqual(call("delete_automation", {"automation_id": "777"})["structuredContent"], {"deleted": "777"})
        # ?key= works too (claude.ai connector link); another account's key can't see this one; disconnect kills it
        self.assertIn("result", self.c.post(f"/mcp?key={key}", json={"jsonrpc": "2.0", "id": 5, "method": "ping"}).get_json())
        self.c.delete("/api/mcp-key", json={})
        self.assertEqual(self.c.post("/mcp", headers=H, json={}).status_code, 401)

    def test_mcp_advanced_tools(self):
        self.login()
        key = self.c.post("/api/mcp-key", json={}).get_json()["key"]
        H = {"Authorization": f"Bearer {key}"}
        rpc = lambda method, params=None: self.c.post("/mcp", headers=H, json={
            "jsonrpc": "2.0", "id": 1, "method": method, **({"params": params} if params is not None else {})}).get_json()
        call = lambda name, args={}: rpc("tools/call", {"name": name, "arguments": args})["result"]
        out = lambda name, args={}: call(name, args)["structuredContent"]
        init = rpc("initialize", {"protocolVersion": "2025-06-18"})["result"]
        self.assertIn("prompts", init["capabilities"])
        self.assertIn("@creator", init["instructions"])
        self.assertGreaterEqual(len(rpc("tools/list")["result"]["tools"]), 30)
        # prompts
        names = [p["name"] for p in rpc("prompts/list")["result"]["prompts"]]
        self.assertEqual(names, ["weekly_review", "launch_plan", "new_reel_automation", "plan_my_week", "fix_problems", "inbox_catchup"])
        msg = rpc("prompts/get", {"name": "launch_plan", "arguments": {"product": "Prompt pack", "price": "149"}})["result"]["messages"][0]
        self.assertIn("Prompt pack", msg["content"]["text"])
        self.assertIn("error", rpc("prompts/get", {"name": "launch_plan", "arguments": {}}))  # product is required
        # full wizard options through Claude
        saved = out("save_automation", {"target": "next_post", "keywords": ["PROMPTS"], "final_dm": "{Hi|Hey} {username}! Pick one:",
                                         "menu": [{"title": "Free", "text": "https://f.com"}, {"title": "Paid", "text": "₹149 https://p.com"}],
                                         "ask_phone": True, "followup_dm": "Pack is ₹149 today", "followup_url": "https://p.com",
                                         "starts_at": "2030-01-01T18:00", "label": "Launch reel"})
        self.assertTrue(saved["created"])
        st = saved["saved"]["settings"]
        self.assertEqual((st["ask_phone"], st["followup_on"], len(st["menu"]), st["starts_at"]), (True, True, 2, "2030-01-01 18:00 IST"))
        self.assertEqual(saved["saved"]["trigger"], "comments on your next post")
        story = out("save_automation", {"target": "story_replies", "final_dm": "Thanks!"})["saved"]
        self.assertFalse(story["require_follow"])
        dm_only = out("save_automation", {"target": "keyword", "keywords": ["price"], "final_dm": "₹149", "dm_only": True})["saved"]
        self.assertEqual(dm_only["trigger"], "keyword in a DM")
        self.assertEqual(out("duplicate_automation", {"automation_id": "next", "to": ["777", "GUIDE"]})["copied_to"], ["777", "kw:GUIDE"])
        self.assertTrue(call("save_automation", {"target": "nonsense"})["isError"])
        # numbers
        self.hook(dm("PRICE", sender="44"))
        rows = out("list_automations", {"sort_by": "runs"})["automations"]
        self.assertEqual(rows[0]["automation_id"], "kw:PRICE")
        self.assertEqual(out("get_automation_insights", {"automation_id": "kw:PRICE"})["last_30_days"]["runs"], 1)
        self.assertEqual(out("get_trends", {"days": 7})["metrics"]["dms"]["this_period"], 1)
        self.assertIn("busiest_hours", out("get_best_posting_times"))
        self.assertEqual(out("get_automation", {"automation_id": "next"})["settings"]["label"], "Launch reel")
        # products and sales
        prod = out("add_product", {"name": "Prompt pack", "price": 149})["product"]
        self.assertIn("/s/", prod["link"])
        self.assertEqual(out("get_sales")["products"][0]["name"], "Prompt pack")
        self.assertFalse(out("set_utm_tags", {"on": False})["utm_tags_on"])
        # contacts and tags
        found = out("search_contacts", {"query": "fan"})
        self.assertEqual(found["matches"], 1)
        self.assertEqual(out("tag_contacts", {"contact_ids": ["@fan", "ghost"], "add_tags": ["vip"]}), {"updated": 1, "not_found": ["ghost"]})
        self.assertEqual(out("search_contacts", {"tag": "vip"})["matches"], 1)
        out("tag_contacts", {"contact_ids": ["fan"], "remove_tags": ["vip"]})
        self.assertEqual(out("search_contacts", {"tag": "vip"})["matches"], 0)
        # welcome, broadcast (preview, then send)
        self.assertEqual(len(out("set_welcome_message", {"text": "Hi!", "buttons": [{"title": "Price", "automation_id": "kw:PRICE"},
                                                                                   {"title": "Shop", "link": "https://s.com"}]})["welcome_message"]["buttons"]), 2)
        before = len(self.ig.messages())
        prev = out("broadcast_to_recent_chats", {"text": "Live in 1 hour!"})
        self.assertEqual((prev["preview"], prev["would_reach"], len(self.ig.messages())), (True, 1, before))
        store.redis("DEL", store.account_key("1789", "counts"))
        sent = out("broadcast_to_recent_chats", {"text": "Live in 1 hour!", "confirm": True})
        self.assertEqual((sent["sent"], sent["done"]), (1, True))
        self.assertEqual(out("get_messaging_settings")["welcome_message"]["text"], "Hi!")
        # inbox
        import ai_agent
        ai_agent.add_message("1789", "44", "fan", "refund chahiye", "fan", status="needs_you", reason="Refund")
        chats = out("list_inbox")["chats"]
        self.assertEqual((chats[0]["chat_id"], chats[0]["can_reply"]), ("44", True))
        self.assertEqual(out("get_conversation", {"chat_id": "44"})["messages"][-1]["text"], "refund chahiye")
        self.assertTrue(out("reply_in_dm", {"chat_id": "44", "text": "Sorry! Sending now"})["sent"])
        self.assertEqual(out("hand_chat_to", {"chat_id": "44", "to": "ai"})["handled_by"], "ai")
        self.assertTrue(call("reply_in_dm", {"chat_id": "nope", "text": "x"})["isError"])
        # every change is in the activity log
        claude = [a for a in self.c.get("/api/activity?all=1").get_json() if a["action"] == "claude"]
        self.assertIn("Created Launch reel", [a["detail"] for a in claude])
        self.assertNotIn("Preview only", [a["detail"] for a in claude])
        self.assertTrue(out("delete_automation", {"automation_id": "kw:GUIDE"}))

    def test_mcp_read_only_link(self):
        self.login()
        d = self.c.post("/api/mcp-key", json={"read_only": True}).get_json()
        self.assertTrue(d["read_only"])
        self.assertTrue(self.c.get("/api/mcp-key").get_json()["read_only"])
        H = {"Authorization": f"Bearer {d['key']}"}
        rpc = lambda method, params=None: self.c.post("/mcp", headers=H, json={
            "jsonrpc": "2.0", "id": 1, "method": method, **({"params": params} if params is not None else {})}).get_json()
        tools = rpc("tools/list")["result"]["tools"]
        self.assertTrue(all(t["annotations"]["readOnlyHint"] for t in tools))
        self.assertNotIn("save_automation", [t["name"] for t in tools])
        self.assertIn("error", rpc("tools/call", {"name": "pause_all_automations", "arguments": {"paused": True}}))
        self.assertIn("read-only", rpc("initialize", {})["result"]["instructions"])
        self.assertFalse(store.load_account("1789").get("paused"))

    def test_plans_and_sale_fee(self):
        import plans
        import time as _t
        free, creator, pro = {"plan": "free"}, {"plan": "creator"}, {"plan": "pro"}
        # SuperProfile-style fee: ₹499 on Free = 5% + 18% GST on the fee
        f = plans.platform_fee(free, 499)
        self.assertEqual((f["fee"], f["gst"], f["total_fee"], f["creator_gets"]), (24.95, 4.49, 29.44, 469.56))
        self.assertEqual(f["gateway"], 0)  # Free's 5% is all-in
        c = plans.platform_fee(creator, 499)  # 2% + GST, plus the gateway's charge passed through
        self.assertEqual((c["fee"], c["gst"], c["gateway"], c["total_fee"], c["creator_gets"]), (9.98, 1.8, 11.78, 23.56, 475.44))
        self.assertEqual(plans.platform_fee(pro, 499, gateway_fee=5.0)["total_fee"], 16.78)  # real gateway charge when known
        self.assertEqual(plans.platform_fee({"plan": "agency"}, 499)["total_fee"], 23.56)
        # referral months count as Pro; unknown plans as Free
        self.assertEqual(plans.plan_of({"plan": "free", "pro_until": _t.time() + 99}), "pro")
        self.assertEqual(plans.plan_of({"plan": "gold"}), "free")
        self.assertTrue(store.is_pro(creator))
        # Starter (the decoy): paid, 3,000 DMs, no monthly AI, 2% fee
        self.assertEqual(engine.monthly_limit({"plan": "starter"}), 3000)
        self.assertEqual(ai_agent.allowance({"plan": "starter"}), ("trial", 25))
        self.assertEqual(plans.platform_fee({"plan": "starter"}, 499)["total_fee"], 23.56)
        self.assertFalse(store.is_pro(free))
        # limits follow the plan
        self.assertEqual(ai_agent.allowance({"plan": "creator"}), ("month", 300))
        self.assertEqual(ai_agent.allowance({"plan": "agency"}), ("month", 10000))
        self.assertEqual(ai_agent.allowance({}), ("trial", 25))
        self.assertEqual(engine.monthly_limit({"plan": "creator"}), 0)
        # the owner sets plans by hand; MRR shows on /owner
        self.login()
        auth = {"Authorization": "Basic " + base64.b64encode(b"x:boss").decode()}
        self.assertEqual(self.c.post("/owner/plan", json={"id": "1789", "plan": "pro"}).status_code, 401)
        self.assertEqual(self.c.post("/owner/plan", headers=auth, data="id=1789&plan=pro").status_code, 415)
        self.assertEqual(self.c.post("/owner/plan", headers=auth, json={"id": "1789", "plan": "gold"}).status_code, 400)
        self.assertEqual(self.c.post("/owner/plan", headers=auth, json={"id": "1789", "plan": "creator"}).get_json()["plan"], "creator")
        page = self.c.get("/owner", headers=auth).get_data(as_text=True)
        self.assertIn("MRR ₹199", page)
        self.assertNotIn("sale_fee", self.c.get("/").get_data(as_text=True))

    def test_follow_gate_is_paid(self):
        import plans
        self.login()
        self.put_rule("555", comment_reply="", require_follow=True, opening_dm="Hi", dm="Link https://x.com")
        tap = lambda: {"entry": [{"id": "1789", "messaging": [{"sender": {"id": "52"}, "postback": {"payload": "GET|555|555"}}]}]}
        self.ig.follows = False
        with mock.patch.object(plans, "LOCKS_ON", False):  # beta: everyone has it
            self.hook(tap())
        self.assertNotIn("https://x.com", json.dumps(self.ig.messages()[-1]))  # asked to follow first
        with mock.patch.object(plans, "LOCKS_ON", True):  # locks on, Free plan: no gate, the link goes out
            self.assertFalse(plans.has(store.load_account("1789"), "follow_gate"))
            self.assertFalse(self.c.get("/api/me").get_json()["account"]["follow_gate"])
            self.hook(tap())
            self.assertIn("https://x.com", json.dumps(self.ig.messages()[-1]))
            acc = store.load_account("1789")
            acc["plan"] = "starter"
            store.save_account(acc)
            self.assertTrue(plans.has(acc, "follow_gate"))

    def test_seo_pages_and_files(self):
        import re as _re
        import seo_content as seo
        for path in seo.all_paths():
            r = self.c.get(path)
            self.assertEqual(r.status_code, 200, path)
            self.assertIsNone(r.headers.get("X-Robots-Tag"), path)
            html = r.get_data(as_text=True)
            self.assertIn('<link rel="canonical" href="http://localhost' + (path if path != "/" else "/") + '"', html, path)
            for block in _re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, _re.S):
                json.loads(block)  # every structured-data block is valid JSON
            self.assertNotIn("{brand}", html, path)
        page = self.c.get("/vs/manychat").get_data(as_text=True)
        self.assertIn('"@type": "FAQPage"', page.replace('":"', '": "'))
        self.assertIn("not affiliated", page)
        self.assertEqual(self.c.get("/vs/nobody").status_code, 404)
        sitemap = self.c.get("/sitemap.xml").get_data(as_text=True)
        self.assertIn("<loc>http://localhost/vs/repli</loc>", sitemap)
        robots = self.c.get("/robots.txt").get_data(as_text=True)
        self.assertIn("Sitemap: http://localhost/sitemap.xml", robots)
        self.assertIn("Disallow: /app/", robots)
        llms = self.c.get("/llms.txt").get_data(as_text=True)
        self.assertIn("Creator: ₹199 / $9", llms)
        self.assertIn("/features/ai-dm-agent", llms)
        # private pages stay out of search; creator link pages don't
        self.assertEqual(self.c.get("/app").headers.get("X-Robots-Tag"), "noindex, nofollow")
        self.assertEqual(self.c.get("/demo").headers.get("X-Robots-Tag"), "noindex, nofollow")
        self.assertFalse(saas.is_private_path("/apple.store"))
        self.assertTrue(saas.is_private_path("/l/abc"))
        landing = self.c.get("/").get_data(as_text=True)
        self.assertIn('"SoftwareApplication"', landing.replace('": "', '":"'))
        with mock.patch.object(saas, "SITE_URL", "https://replyinbox.in"):
            self.assertIn('<link rel="canonical" href="https://replyinbox.in/">', self.c.get("/").get_data(as_text=True))

    def test_pillar_cluster_architecture(self):
        import re as _re
        import seo_content as seo
        owner = seo.pillar_of()
        every = [("feature", k) for k in seo.FEATURES] + [("compare", k) for k in seo.COMPARE] + [("guide", k) for k in seo.GUIDES]
        self.assertEqual(sorted(owner), sorted(every))  # every page belongs to exactly one pillar
        url = {"feature": "/features/", "compare": "/vs/", "guide": "/guides/"}
        for slug, pillar in seo.PILLARS.items():
            hub = self.c.get(f"/{slug}").get_data(as_text=True)
            for kind, s_ in pillar["clusters"]:  # the hub links down to every spoke
                self.assertIn(f'href="{url[kind]}{s_}"', hub, (slug, s_))
            self.assertIn('"CollectionPage"', hub.replace('": "', '":"'))
        for (kind, s_), pillar in owner.items():  # every spoke links up to its hub, with matching schema
            page = self.c.get(f"{url[kind]}{s_}").get_data(as_text=True)
            self.assertIn(f'<a href="/{pillar}">', page, s_)
            self.assertIn(f'/{pillar}", "@type": "CollectionPage"'.replace('", "', '","'), page.replace('", "', '","'), s_)
        glossary = self.c.get("/glossary").get_data(as_text=True)
        anchors = set(_re.findall(r'<div id="([a-z0-9-]+)">', glossary))
        self.assertEqual(anchors, set(seo.GLOSSARY))
        for slug in seo.PILLARS:  # term links from hubs resolve
            for term in _re.findall(r'/glossary#([a-z0-9-]+)', self.c.get(f"/{slug}").get_data(as_text=True)):
                self.assertIn(term, anchors)
        self.assertIn("### [Instagram lead generation with DMs]", self.c.get("/llms.txt").get_data(as_text=True))

    def test_demo_mode(self):
        r = self.c.get("/demo")
        self.assertTrue(r.location.endswith("/app"))
        for path in ("/app", "/app/automations", "/app/report", "/app/links", "/app/contacts", "/app/apps", "/app/settings"):
            self.assertEqual(self.c.get(path).status_code, 200, path)
        report = self.c.get("/api/report").get_json()
        self.assertEqual(len(report["reels"]), 5)
        self.assertEqual(self.c.get("/api/contacts").get_json()["contacts"][0]["username"], "rahul.creates")
        self.assertIn("demo.creator", self.c.get("/demo.creator").get_data(as_text=True))
        self.assertEqual(len(self.ig.calls), 0)  # the demo never calls Instagram
        self.c.post("/api/disconnect", json={})
        self.assertIsNotNone(store.load_account(demo.DEMO_ID))  # demo data isn't deleted, just logged out

    def test_link_page_contacts_and_apps(self):
        self.login()
        body = {"name": "Creator", "bio": "Hi", "theme": "mint", "socials": {"youtube": "https://yt.com"},
                "items": [{"type": "product", "title": "Pack", "url": "https://shop.com/p", "price": "₹149", "featured": True},
                          {"type": "link", "title": "Bad", "url": "javascript:alert(1)"}]}
        page = self.c.put("/api/page", json=body).get_json()["page"]
        self.assertEqual([i["title"] for i in page["items"]], ["Pack"])  # unsafe link dropped
        html = self.c.get("/creator").get_data(as_text=True)
        self.assertIn("Pack", html)
        self.assertIn('class="t-ocean"', html)  # old "mint" pages open as ocean
        go = self.c.get(f"/creator/go/{page['items'][0]['id']}")
        self.assertEqual(go.location, "https://shop.com/p")
        self.assertEqual(list(self.c.get("/api/page").get_json()["clicks"].values()), [1])
        self.assertEqual(self.c.get("/nobody").status_code, 404)
        # contacts come from the automation
        self.put_rule("555")
        self.hook(comment("PROMPTS"))
        c = self.c.get("/api/contacts").get_json()["contacts"]
        self.assertEqual((c[0]["username"], c[0]["keyword"]), ("fan", "PROMPTS"))
        self.assertIn("fan,", self.c.get("/api/contacts.csv").get_data(as_text=True))
        # apps switch sections off
        self.c.put("/api/apps", json={"contacts": False})
        self.assertNotIn('href="/app/contacts"', self.c.get("/app").get_data(as_text=True))

    def test_ai_agent_replies_and_hands_over(self):
        self.login()
        # without the server's Claude key the AI can't be switched on
        with mock.patch.object(ai_agent, "client", lambda: None):
            self.assertEqual(self.c.put("/api/ai", json={"enabled": True}).status_code, 400)
        claude = FakeClaude()
        self.enterContext(mock.patch.object(ai_agent, "client", lambda: claude))
        self.c.put("/api/page", json={"items": [{"type": "product", "title": "Prompt Pack", "url": "https://shop.com/p", "price": "₹149"}]})
        self.put_rule("kw:GUIDE", keywords=["GUIDE"], require_follow=False, comment_reply="")
        state = self.c.put("/api/ai", json={"enabled": True, "faq": "Q: UPI? A: Yes", "language": "hinglish"}).get_json()
        self.assertTrue(state["settings"]["enabled"])
        # keyword DMs still go to the automation, not the AI
        self.hook(dm("GUIDE"))
        self.assertEqual(claude.requests, [])
        # anything else: Claude answers from the creator's products and FAQ
        claude.answers.append({"reply": "Sirf ₹149 👉 https://shop.com/p", "needs_human": False, "reason": "", "suggested_reply": ""})
        self.hook(dm("price kya hai?"))
        system = claude.requests[0]["system"][0]["text"]
        self.assertIn("Prompt Pack", system)
        self.assertIn("₹149", system)
        self.assertIn("Q: UPI? A: Yes", system)
        self.assertIn("Hinglish", system)
        self.assertEqual(claude.requests[0]["messages"][-1], {"role": "user", "content": "price kya hai?"})
        self.assertEqual(claude.requests[0]["model"], "claude-haiku-5-5")
        self.assertNotIn("fallbacks", claude.requests[0])  # Haiku has no server-side fallbacks
        self.assertEqual(self.ig.messages()[-1], {"recipient": {"id": "88"}, "message": {"text": "Sirf ₹149 👉 https://shop.com/p"}})
        self.hook(dm("price kya hai?"))  # Instagram delivering the same message again
        self.assertEqual(len(claude.requests), 1)
        # a refund: handed over with a suggestion and one holding message, then the AI stays quiet
        claude.answers.append({"reply": "", "needs_human": True, "reason": "Refund", "suggested_reply": "Sorry! Sending it now"})
        sent = len(self.ig.messages())
        self.hook(dm("refund chahiye", mid="m2"))
        self.assertEqual(self.ig.messages()[-1]["message"]["text"], ai_agent.DEFAULT_HOLD)
        self.hook(dm("hello??", mid="m3"))
        self.assertEqual(len(self.ig.messages()), sent + 1)
        self.assertEqual(len(claude.requests), 2)
        inbox = self.c.get("/api/inbox").get_json()
        t = inbox["threads"][0]
        self.assertEqual((t["status"], t["reason"], t["suggestion"], t["username"]), ("needs_you", "Refund", "Sorry! Sending it now", "fan"))
        self.assertEqual(self.c.get("/api/me").get_json()["inbox_waiting"], 1)
        # the creator answers: the AI stays out until it's handed back
        r = self.c.post("/api/inbox/88/send", json={"text": "Bhej diya 🙏"}).get_json()
        self.assertEqual(r["thread"]["status"], "you")
        self.assertEqual([m["role"] for m in r["messages"]], ["fan", "ai", "fan", "ai", "fan", "you"])
        self.hook(dm("thanks", mid="m4"))
        self.assertEqual(len(claude.requests), 2)
        self.c.post("/api/inbox/88/status", json={"status": "ai"})
        self.hook(dm("one more question", mid="m5"))
        self.assertEqual(len(claude.requests), 3)
        self.assertEqual(claude.requests[2]["messages"][-1]["role"], "user")
        # refusals and errors hand over instead of sending anything
        claude.answers.append("refusal")
        sent = len(self.ig.messages())
        self.hook(dm("hmm", sender="99"))
        self.assertEqual(ai_agent.get_thread("1789", "99")["status"], "needs_you")
        # try-it box doesn't send
        sent = len(self.ig.messages())
        self.assertEqual(self.c.post("/api/ai/test", json={"message": "hi"}).get_json()["reply"], "Hi!")
        self.assertEqual(len(self.ig.messages()), sent)
        # monthly AI limit
        acc = store.load_account("1789")
        acc["ai_limit"] = 1
        store.save_account(acc)
        self.c.post("/api/inbox/88/status", json={"status": "ai"})
        self.hook(dm("are you there", mid="m6"))
        self.assertIn("used up", ai_agent.get_thread("1789", "88")["reason"])
        # disconnect removes the conversations
        self.c.post("/api/disconnect", json={})
        self.assertEqual(ai_agent.threads("1789"), [])
        self.assertIsNone(store.redis("GET", store.account_key("1789", "chat:88")))
        self.assertEqual(store.redis("LRANGE", store.account_key("1789", "chat:88"), 0, -1), [])

    def test_ai_free_trial_and_paid_plan(self):
        self.login()
        claude = FakeClaude()
        self.enterContext(mock.patch.object(ai_agent, "client", lambda: claude))
        self.enterContext(mock.patch.object(ai_agent, "FREE_AI_TRIAL", 2))
        self.c.put("/api/ai", json={"enabled": True})
        for i in range(3):
            self.hook(dm(f"question {i}", sender=f"7{i}"))
        self.assertEqual(len(claude.requests), 2)  # the third is handed over: trial used up
        self.assertIn("free AI replies are used up", ai_agent.get_thread("1789", "72")["reason"])
        state = self.c.get("/api/inbox").get_json()
        self.assertEqual((state["kind"], state["used"], state["limit"], state["over"]), ("trial", 2, 2, True))
        acc = store.load_account("1789")
        acc["plan"] = "pro"
        store.save_account(acc)
        state = self.c.get("/api/inbox").get_json()
        self.assertEqual((state["kind"], state["limit"], state["over"]), ("month", 2000, False))
        self.hook(dm("question 3", sender="73"))
        self.assertEqual(len(claude.requests), 3)
        with mock.patch.object(ai_agent, "AI_MODEL", "claude-opus-5-5"):
            self.hook(dm("question 4", sender="74"))
        self.assertEqual(claude.requests[-1]["fallbacks"], "default")

    def test_story_replies_and_mentions(self):
        self.login()
        story = lambda text, sender="61", sid="st1": {"entry": [{"id": "1789", "messaging": [{"sender": {"id": sender}, "message": {
            "mid": f"{sender}{sid}{text}", "text": text, "reply_to": {"story": {"id": sid, "url": "https://x"}}}}]}]}
        self.hook(story("GUIDE"))  # nothing set up: nothing sent
        self.assertEqual(self.ig.messages(), [])
        self.assertEqual(self.put_rule("story:reply", keywords=[], require_follow=False, dm="Story link https://s.com").status_code, 200)
        self.hook(story("🔥🔥"))
        self.assertEqual(self.ig.messages()[-1], {"recipient": {"id": "61"}, "message": {"text": "Story link https://s.com"}})
        self.hook(story("again"))  # once per person per story
        self.assertEqual(len(self.ig.messages()), 1)
        # a keyword automation wins over the story rule
        self.put_rule("kw:PROMPTS", keywords=["PROMPTS"], require_follow=False, comment_reply="", dm="Prompts https://p.com")
        self.hook(story("PROMPTS", sender="62"))
        self.assertEqual(self.ig.messages()[-1]["message"], {"text": "Prompts https://p.com"})
        # story rule with a keyword and the follow gate: button first, then the usual follow check
        self.put_rule("story:reply", keywords=["LINK"], require_follow=True, dm="Gated https://g.com")
        self.hook(story("hello", sender="63"))
        self.assertEqual(len(self.ig.messages()), 2)  # no keyword: not answered
        self.hook(story("link please", sender="63"))
        self.assertEqual(self.ig.messages()[-1]["message"]["attachment"]["payload"]["buttons"][0]["payload"], "GET|story:reply")
        self.hook({"entry": [{"id": "1789", "messaging": [{"sender": {"id": "63"}, "postback": {"payload": "GET|story:reply"}}]}]})
        self.assertEqual(self.ig.messages()[-1]["message"], {"text": "Gated https://g.com"})
        # the story rule doesn't answer plain DMs
        self.hook(dm("link", sender="64"))
        self.assertFalse(any(m["recipient"] == {"id": "64"} for m in self.ig.messages()))
        # mentions: thank-you once a day
        store.redis("DEL", store.account_key("1789", "counts"))  # tests run with a 3-DM monthly limit
        self.put_rule("story:mention", keywords=[], require_follow=False, dm="Thanks {username}! 🙏")
        mention = {"entry": [{"id": "1789", "messaging": [{"sender": {"id": "65"}, "message": {
            "mid": "mm", "attachments": [{"type": "story_mention", "payload": {"url": "https://x"}}]}}]}]}
        self.hook(mention)
        self.hook(mention)
        sent = [m for m in self.ig.messages() if m["recipient"] == {"id": "65"}]
        self.assertEqual(sent, [{"recipient": {"id": "65"}, "message": {"text": "Thanks fan! 🙏"}}])
        self.assertEqual(store.counts("1789").get("story_mentions"), 1)
        c = {x["username"]: x for x in self.c.get("/api/contacts").get_json()["contacts"]}
        self.assertIn("fan", c)

    def test_email_capture(self):
        self.login()
        self.put_rule("kw:GUIDE", keywords=["GUIDE"], require_follow=False, comment_reply="", ask_email=True, dm="Guide https://g.com")
        self.hook(dm("GUIDE", sender="81"))
        self.assertIn("buttons", self.ig.messages()[-1]["message"]["attachment"]["payload"])  # button first
        tap = lambda p, who="81": {"entry": [{"id": "1789", "messaging": [{"sender": {"id": who}, "postback": {"payload": p}}]}]}
        self.hook(tap("GET|kw:GUIDE"))
        ask = self.ig.messages()[-1]["message"]
        self.assertIn("email", ask["text"])
        self.assertEqual(ask["quick_replies"][0]["payload"], "SKIPMAIL|kw:GUIDE|")
        self.hook(dm("hmm what", sender="81", mid="e1"))
        self.assertIn("doesn't look like an email", self.ig.messages()[-1]["message"]["text"])
        self.hook(dm("sure: Fan.Name@Gmail.com", sender="81", mid="e2"))
        self.assertEqual(self.ig.messages()[-1]["message"], {"text": "Guide https://g.com"})
        c = self.c.get("/api/contacts").get_json()["contacts"][0]
        self.assertEqual(c["email"], "fan.name@gmail.com")
        # asked only once: next time the link comes straight away
        self.hook(tap("GET|kw:GUIDE"))
        self.assertEqual(self.ig.messages()[-1]["message"], {"text": "Guide https://g.com"})
        # skip (optional email) delivers too; required email can't be skipped
        self.ig.calls.clear()
        store.redis("DEL", store.account_key("1789", "contacts"), store.account_key("1789", "counts"))
        self.hook(tap("GET|kw:GUIDE", who="82"))
        self.hook({"entry": [{"id": "1789", "messaging": [{"sender": {"id": "82"}, "message": {
            "mid": "q1", "text": "Skip", "quick_reply": {"payload": "SKIPMAIL|kw:GUIDE|"}}}]}]})
        self.assertEqual(self.ig.messages()[-1]["message"], {"text": "Guide https://g.com"})
        self.put_rule("kw:GUIDE", keywords=["GUIDE"], require_follow=False, comment_reply="", ask_email=True,
                      email_required=True, dm="Guide https://g.com")
        store.redis("DEL", store.account_key("1789", "contacts"))
        self.hook(tap("GET|kw:GUIDE", who="83"))
        self.assertNotIn("quick_replies", self.ig.messages()[-1]["message"])
        sent = len(self.ig.messages())
        self.hook(tap("SKIPMAIL|kw:GUIDE|", who="83"))
        self.assertEqual(len(self.ig.messages()), sent)

    def test_followup_offer(self):
        self.login()
        r = self.put_rule("kw:GUIDE", keywords=["GUIDE"], require_follow=False, comment_reply="", dm="Guide https://g.com",
                          followup_on=True, followup_hours=3, followup_dm="Full pack ₹149 {username}",
                          followup_url="https://shop.com/p", followup_button="Buy now")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.put_rule("kw:X", followup_on=True, followup_dm="").status_code, 400)
        self.hook(dm("GUIDE", sender="91"))  # a follow-up needs the chat the button opens
        tap = {"entry": [{"id": "1789", "messaging": [{"sender": {"id": "91"}, "postback": {"payload": "GET|kw:GUIDE"}}]}]}
        self.hook(tap)
        self.assertEqual(self.ig.messages()[-1]["message"], {"text": "Guide https://g.com"})
        self.hook(tap)  # a second tap doesn't schedule a second follow-up
        self.assertEqual(len(store.redis("ZRANGEBYSCORE", store.FOLLOWUPS, "-inf", "+inf")), 1)
        self.assertEqual(engine.send_due_followups(), 0)  # not due yet
        later = engine.time.time() + 3 * 3600 + 5
        with mock.patch.object(engine.time, "time", lambda: later), mock.patch.object(store.time, "time", lambda: later):
            self.assertEqual(engine.send_due_followups(), 1)
        msg = self.ig.messages()[-1]["message"]["attachment"]["payload"]
        self.assertEqual(msg["text"], "Full pack ₹149 fan")
        self.assertEqual(msg["buttons"][0], {"type": "web_url", "title": "Buy now", "url": "https://shop.com/p"})
        self.assertEqual(store.counts("1789").get("followups_sent"), 1)
        # past Instagram's 24 hours: skipped
        store.schedule(0, {"acc": "1789", "igsid": "92", "key": "kw:GUIDE", "since": 1})
        sent = len(self.ig.messages())
        self.assertEqual(engine.send_due_followups(), 0)
        self.assertEqual(len(self.ig.messages()), sent)
        # the cron also sends them
        self.assertEqual(self.c.get("/cron/followups", headers={"Authorization": "Bearer cron"}).get_json(), {"sent": 0})

    def test_past_comments_and_retries(self):
        self.login()
        self.assertEqual(self.c.post("/api/reels/555/past-comments", json={}).status_code, 400)  # no automation yet
        self.put_rule("555", require_follow=False, comment_reply="Sent!", dm="Here https://x.com")
        stamp = lambda h: engine.datetime.fromtimestamp(engine.time.time() - h * 3600, engine.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
        self.ig.comments = [{"id": "p1", "text": "PROMPTS", "timestamp": stamp(5), "from": {"id": "11", "username": "a"}},
                            {"id": "p2", "text": "nice", "timestamp": stamp(5), "from": {"id": "12", "username": "b"}},
                            {"id": "p3", "text": "PROMPTS", "timestamp": stamp(24 * 8), "from": {"id": "13", "username": "c"}}]
        r = self.c.post("/api/reels/555/past-comments", json={}).get_json()
        self.assertEqual((r["sent"], r["too_old"], r["already_done_or_no_match"]), (1, 1, 1))
        self.assertEqual(self.ig.messages()[-1], {"recipient": {"comment_id": "p1"}, "message": {"text": "Here https://x.com"}})
        self.assertEqual(self.c.post("/api/reels/555/past-comments", json={}).get_json()["sent"], 0)  # never twice
        # Instagram refuses to open the chat: queued, then retried
        self.ig.fail_dm = True
        self.hook(comment("PROMPTS", cid="c9"))
        self.assertEqual(self.c.get("/api/retry").get_json(), {"waiting": 1})
        r = self.c.post("/api/retry", json={}).get_json()
        self.assertEqual((r["sent"], r["still_failing"], r["waiting"]), (0, 1, 1))
        self.ig.fail_dm = False
        store.redis("DEL", store.account_key("1789", "counts"))  # tests run with a 3-DM monthly limit
        r = self.c.post("/api/retry", json={}).get_json()
        self.assertEqual((r["sent"], r["waiting"]), (1, 0))
        self.assertEqual(self.ig.messages()[-1]["recipient"], {"comment_id": "c9"})
        # too old to retry: dropped
        engine.add_retry(store.load_account("1789"), "old", {"key": "555", "media_id": "555", "username": "z", "text": "x", "at": 1})
        self.assertEqual(self.c.post("/api/retry", json={}).get_json()["expired"], 1)

    def test_phone_capture(self):
        for text, want in [("98765 43210", "+919876543210"), ("my no is +91-98765-43210", "+919876543210"),
                           ("09876543210", "+919876543210"), ("+44 7700 900123", "+447700900123"),
                           ("12345", ""), ("call me", ""), ("1234567890", "")]:
            self.assertEqual(engine.parse_phone(text), want, text)
        self.login()
        self.put_rule("kw:GUIDE", keywords=["GUIDE"], require_follow=False, comment_reply="", ask_email=True,
                      ask_phone=True, phone_required=True, dm="Guide https://g.com")
        tap = lambda p, who="71": {"entry": [{"id": "1789", "messaging": [{"sender": {"id": who}, "postback": {"payload": p}}]}]}
        self.hook(tap("GET|kw:GUIDE"))
        self.assertIn("email", self.ig.messages()[-1]["message"]["text"])
        # skip the email: the phone is asked next, and it's required (no Skip button)
        self.hook(tap("SKIPMAIL|kw:GUIDE|"))
        ask = self.ig.messages()[-1]["message"]
        self.assertIn("WhatsApp", ask["text"])
        self.assertNotIn("quick_replies", ask)
        self.hook(dm("abc", sender="71", mid="p0"))
        self.assertIn("doesn't look like a phone number", self.ig.messages()[-1]["message"]["text"])
        self.hook(dm("98765 43210", sender="71", mid="p1"))
        self.assertEqual(self.ig.messages()[-1]["message"], {"text": "Guide https://g.com"})
        c = self.c.get("/api/contacts").get_json()["contacts"][0]
        self.assertEqual((c["phone"], c["email"]), ("+919876543210", ""))
        self.assertIn("+919876543210", self.c.get("/api/contacts.csv").get_data(as_text=True))
        sent = len(self.ig.messages())
        self.hook(tap("SKIPPHONE|kw:GUIDE|", who="72"))  # a required phone can't be skipped
        self.assertEqual(len(self.ig.messages()), sent)
        # both given in a row: email, then phone, then the link
        store.redis("DEL", store.account_key("1789", "contacts"), store.account_key("1789", "counts"))
        self.hook(tap("GET|kw:GUIDE", who="73"))
        self.hook(dm("me@x.com", sender="73", mid="p2"))
        self.assertIn("WhatsApp", self.ig.messages()[-1]["message"]["text"])
        self.hook(dm("+91 91234 56789", sender="73", mid="p3"))
        self.assertEqual(self.ig.messages()[-1]["message"], {"text": "Guide https://g.com"})
        self.assertEqual(store.counts("1789").get("phones"), 1)

    def test_chat_menu(self):
        self.login()
        self.put_rule("kw:GUIDE", keywords=["GUIDE"], require_follow=False, comment_reply="", dm="Guide https://g.com")
        bad = self.c.put("/api/ice", json={"enabled": True, "items": [{"question": "Price?", "answer": ""}]})
        self.assertEqual(bad.status_code, 400)
        r = self.c.put("/api/ice", json={"enabled": True, "items": [
            {"question": "How do I buy?", "answer": "Here {username}: https://shop.com"},
            {"question": "Free guide?", "answer": "", "rule": "kw:GUIDE"}, {"question": "", "answer": "x"}]}).get_json()
        self.assertEqual(len(r["items"]), 2)
        profile = [c for c in self.ig.calls if c[1].endswith("/me/messenger_profile")][-1][2]
        self.assertEqual(profile["ice_breakers"][0]["call_to_actions"][1], {"question": "Free guide?", "payload": "ICE|1"})
        tap = lambda p: {"entry": [{"id": "1789", "messaging": [{"sender": {"id": "41"}, "postback": {"payload": p}}]}]}
        self.hook(tap("ICE|0"))
        self.assertEqual(self.ig.messages()[-1], {"recipient": {"id": "41"}, "message": {"text": "Here fan: https://shop.com"}})
        self.hook(tap("ICE|1"))
        self.assertEqual(self.ig.messages()[-1]["message"], {"text": "Guide https://g.com"})
        self.hook(tap("ICE|9"))  # unknown question: nothing
        self.assertEqual(len(self.ig.messages()), 2)
        deleted = []
        with mock.patch.object(engine.requests, "delete", lambda url, **k: deleted.append((url, k.get("json"))) or Resp({})):
            self.assertFalse(self.c.put("/api/ice", json={"enabled": False, "items": []}).get_json()["enabled"])
        self.assertEqual(deleted[0][1], {"platform": "instagram", "fields": ["ice_breakers"]})

    def test_comment_guard(self):
        self.login()
        self.put_rule("555")
        self.c.put("/api/guard", json={"enabled": True, "links": True, "words": "cheap followers, crypto"})
        self.assertEqual(self.c.post("/api/guard/test", json={"text": "Buy CHEAP followers!!"}).get_json()["reason"],
                         'blocked word "cheap followers"')
        self.assertEqual(self.c.post("/api/guard/test", json={"text": "visit mysite.xyz"}).get_json()["reason"], "link")
        self.assertEqual(self.c.post("/api/guard/test", json={"text": "great reel"}).get_json()["reason"], "")
        self.hook(comment("PROMPTS crypto giveaway", cid="g1"))
        hide = [c for c in self.ig.calls if c[1].endswith("/g1")]
        self.assertEqual(hide[0][0], "POST")
        self.assertEqual(self.ig.messages(), [])  # hidden comments don't get the automation
        self.hook({"entry": [{"id": "1789", "changes": [{"field": "comments", "value": {
            "id": "g2", "text": "DM me www.spam.com", "parent_id": "g0", "from": {"id": "8", "username": "spammer"}, "media": {"id": "555"}}}]}]})
        self.assertTrue(any(c[1].endswith("/g2") for c in self.ig.calls))  # replies in threads are guarded too
        g = self.c.get("/api/guard").get_json()
        self.assertEqual((g["total"], g["hidden"][0]["username"]), (2, "spammer"))
        self.hook(comment("PROMPTS", cid="g3"))
        self.assertEqual(len(self.ig.messages()), 1)  # normal comments still work

    def test_giveaway(self):
        self.login()
        self.assertEqual(self.c.get("/app/giveaway").status_code, 200)
        self.ig.comments = [{"id": f"w{i}", "text": t, "from": {"id": str(i), "username": u}}
                            for i, (u, t) in enumerate([("a", "WIN @x @y"), ("a", "WIN again @x @y"), ("b", "win @x"),
                                                        ("c", "nice"), ("creator", "WIN @x @y"), ("d", "WIN @p @q")])]
        r = self.c.post("/api/giveaway", json={"media_id": "555", "keyword": "WIN", "min_mentions": 2, "winners": 5,
                                               "exclude": "d"}).get_json()
        self.assertEqual((r["entries"], [w["username"] for w in r["winners"]]), (1, ["a"]))  # one entry each, own account out
        r = self.c.post("/api/giveaway", json={"media_id": "555", "winners": 2}).get_json()
        self.assertEqual((r["entries"], len(r["winners"])), (4, 2))
        store.save_contact("1789", {"username": "b", "followed": True})
        r = self.c.post("/api/giveaway", json={"media_id": "555", "followed_only": True}).get_json()
        self.assertEqual([w["username"] for w in r["winners"]], ["b"])
        self.assertEqual(len(self.c.get("/api/giveaway").get_json()["history"]), 3)
        res = self.c.post("/api/giveaway/announce", json={"winners": r["winners"], "reply": "Congrats @{username}!",
                                                           "dm": "You won {username}"}).get_json()["results"]
        self.assertEqual(res, [{"username": "b", "reply": "ok", "dm": "ok"}])
        self.assertEqual(self.ig.messages()[-1], {"recipient": {"comment_id": "w2"}, "message": {"text": "You won b"}})

    def test_automation_schedule(self):
        self.login()
        now = int(engine.time.time())
        self.assertEqual(self.put_rule("555", starts_at=now + 100, ends_at=now + 50).status_code, 400)
        self.put_rule("555", comment_reply="", require_follow=False, starts_at=now + 3600)  # not started yet
        self.hook(comment("PROMPTS", cid="s1"))
        self.assertEqual(self.ig.messages(), [])
        self.put_rule("555", comment_reply="", require_follow=False, starts_at=now - 60, ends_at=now + 3600)  # running
        self.hook(comment("PROMPTS", cid="s2"))
        self.assertEqual(len(self.ig.messages()), 1)
        self.put_rule("555", comment_reply="", require_follow=False, ends_at=now - 1)  # ended
        self.hook(comment("PROMPTS", cid="s3"))
        self.assertEqual(len(self.ig.messages()), 1)
        self.assertEqual(store.load_rules("1789")["reels"]["555"]["ends_at"], now - 1)

    def test_ab_test_first_dm(self):
        self.login()
        self.put_rule("555", comment_reply="", require_follow=True, opening_dm="Version A text", opening_dm_b="Version B text")
        tap = lambda p, who: {"entry": [{"id": "1789", "messaging": [{"sender": {"id": who}, "postback": {"payload": p}}]}]}
        with mock.patch.object(engine.random, "random", lambda: 0.9):  # B
            self.hook(comment("PROMPTS", cid="ab1"))
        first = self.ig.messages()[-1]["message"]["attachment"]["payload"]
        self.assertEqual(first["text"], "Version B text")
        payload = first["buttons"][0]["payload"]
        self.assertEqual(payload, "GET|555|555|B")
        self.hook(tap(payload, "51"))  # follows (fake) → link
        self.hook(tap(payload, "51"))  # a second tap isn't counted twice
        with mock.patch.object(engine.random, "random", lambda: 0.1):  # A
            self.hook(comment("PROMPTS", cid="ab2"))
        self.assertEqual(self.ig.messages()[-1]["message"]["attachment"]["payload"]["text"], "Version A text")
        st = self.c.get("/api/ab").get_json()["555"]
        self.assertEqual((st["sent_A"], st["sent_B"], st["tap_B"], st["link_B"]), (1, 1, 1, 1))
        self.assertNotIn("tap_A", st)
        # changing a version starts a fresh test
        self.put_rule("555", comment_reply="", opening_dm="Version A text", opening_dm_b="New B")
        self.assertEqual(self.c.get("/api/ab").get_json()["555"], {})
        # without version B there's no test and the payload stays as before
        self.put_rule("555", comment_reply="", opening_dm="Only A", opening_dm_b="")
        self.hook(comment("PROMPTS", cid="ab3"))
        self.assertEqual(self.ig.messages()[-1]["message"]["attachment"]["payload"]["buttons"][0]["payload"], "GET|555|555")
        self.assertEqual(self.c.get("/api/ab").get_json(), {})

    def test_week_summary(self):
        self.login()
        store.count("1789", "links_sent", 3)
        store.count("1789", f"dms:{engine.month()}")  # monthly counters aren't split by day
        old = store.account_key("1789", f"day:{store.day_str(8)}")
        store.redis("HINCRBY", old, "links_sent", 6)
        w = self.c.get("/api/week").get_json()
        self.assertEqual((w["this_week"]["links_sent"], w["last_week"]["links_sent"]), (3, 6))
        self.assertEqual(len(w["daily"]), 14)
        self.assertEqual(w["daily"][-1]["date"], store.day_str())
        self.c.post("/api/disconnect", json={})
        self.assertIsNone(store.redis("HGET", old, "links_sent"))

    def test_onboarding_checklist(self):
        self.login()
        o = self.c.get("/api/onboarding").get_json()
        state = {s["id"]: s["done"] for s in o["steps"]}
        self.assertEqual((state["connect"], state["automation"], state["test"], o["hidden"]), (True, False, False, False))
        self.put_rule("555", require_follow=False, comment_reply="")
        self.hook(comment("PROMPTS"))
        o = self.c.post("/api/onboarding", json={"done": "bio"}).get_json()
        state = {s["id"]: s["done"] for s in o["steps"]}
        self.assertEqual((state["automation"], state["test"], state["bio"]), (True, True, True))
        self.assertTrue(self.c.post("/api/onboarding", json={"dismissed": True}).get_json()["hidden"])
        self.assertIn('id="onb"', self.c.get("/app").get_data(as_text=True))

    def test_team_access(self):
        self.login()
        self.assertEqual(self.c.post("/api/team", json={"name": "", "role": "manager"}).status_code, 400)
        m = self.c.post("/api/team", json={"name": "Riya", "role": "manager"}).get_json()
        v = self.c.post("/api/team", json={"name": "Aman", "role": "viewer"}).get_json()
        path = lambda link: "/join/" + link.rsplit("/join/", 1)[1]
        owner = self.c
        # the manager joins in their own browser
        mgr = saas.app.test_client()
        self.assertIn("Join @creator", mgr.get(path(m["link"])).get_data(as_text=True))  # GET doesn't use the invite
        self.assertEqual(mgr.post(path(m["link"])).status_code, 302)
        self.assertEqual(saas.app.test_client().post(path(m["link"])).status_code, 404)  # one time only
        self.assertIn("Manager access", mgr.get("/app").get_data(as_text=True))
        self.assertEqual(mgr.put("/api/rules/555", json={"enabled": True, "keywords": ["X"], "dm": "hi"}).status_code, 200)
        for method, url in (("post", "/api/disconnect"), ("get", "/api/team"), ("post", "/api/mcp-key")):
            self.assertEqual(getattr(mgr, method)(url, json={}).status_code, 403, url)
        # the viewer can look but not change
        view = saas.app.test_client()
        view.post(path(v["link"]))
        self.assertEqual(view.get("/api/rules").status_code, 200)
        self.assertEqual(view.put("/api/rules/555", json={"enabled": False, "dm": "x"}).status_code, 403)
        self.assertIn("view-only", view.get("/app").get_data(as_text=True))
        # removing someone logs them out
        owner.delete(f"/api/team/{m['member']['id']}", json={})
        self.assertEqual(mgr.get("/api/rules").status_code, 401)
        self.assertEqual([x["name"] for x in owner.get("/api/team").get_json()["team"]], ["Aman"])
        self.assertEqual(owner.get("/app/settings").status_code, 200)

    def test_pro_plan_limits(self):
        acc = {"id": "1", "plan": "pro"}
        self.assertEqual(engine.monthly_limit(acc), 0)  # no ReplyInbox DM limit
        self.assertEqual(engine.monthly_limit({"id": "1"}), 3)  # free (tests run with FREE_MONTHLY_DMS=3)
        self.assertEqual(engine.monthly_limit({"id": "1", "plan": "pro", "dm_limit": 50}), 50)
        html = self.c.get("/").get_data(as_text=True)
        self.assertIn('property="og:image" content="http://localhost/static/og.png"', html)
        self.assertEqual(self.c.get("/static/og.png").status_code, 200)
        for text in ("₹149", "₹199", "₹499", "₹1,499", 'data-usd="$9"', 'data-usd-m="$19"', "MOST POPULAR", "1,000 DMs every month", "25 AI replies", "AI DM agent", "Giveaway picker", "Team access"):
            self.assertIn(text, html)

    def test_referrals(self):
        import referrals
        import users
        self.login()  # @creator, om@example.com
        r = self.c.get("/api/refer").get_json()
        self.assertTrue(r["link"].endswith("/r/creator"))
        self.assertEqual((r["signups"], r["to_next"], r["pct"]), (0, 10, 20))
        self.assertEqual(self.c.get("/app/refer").status_code, 200)
        me_id = users.by_email("om@example.com")["id"]
        creator_me = self.ig.me
        self.c.post("/logout")
        # a new creator follows the invite link, signs in and connects Instagram: one sign-up, no free Pro any more
        self.ig.calls.clear()
        self.ig.me = {"id": "asid2", "user_id": "2002", "username": "friend.creates", "name": "F", "profile_picture_url": "", "followers_count": 10}
        new = saas.app.test_client()
        new.get("/r/creator")
        self.assertIn("@creator invited you", new.get("/").get_data(as_text=True))
        self.login(new, "friend@example.com")
        friend = users.by_email("friend@example.com")
        self.assertEqual(friend["referred_by"], me_id)
        self.assertFalse(store.is_pro(store.load_account("2002")))
        me = users.get(me_id)
        self.assertEqual([x["username"] for x in me["ref_signups"]], ["friend.creates"])
        # connecting again (or another account) doesn't count twice; nor does inviting yourself
        new.get("/r/creator")
        self.connect_ig(new)
        self.assertEqual(len(users.get(me_id)["ref_signups"]), 1)
        self.assertIsNone(referrals.record_signup(users.get(me_id), "creator"))
        # 10 sign-ups: one free month of Starter for every Instagram account of the referrer
        for i in range(9):
            u = users.create(f"f{i}@example.com")
            self.assertIsNotNone(referrals.record_signup(u, "creator", f"f{i}"))
        me = users.get(me_id)
        self.assertEqual(me["ref_months"], 1)
        self.assertEqual(users.current_plan(me), "starter")
        self.assertEqual(billing.plans.plan_of(store.load_account("1789")), "starter")
        # a referrer on a paid plan gets the Starter price as earnings instead
        users.set_plan(users.get(me_id), "pro")
        for i in range(10):
            referrals.record_signup(users.create(f"g{i}@example.com"), "creator")
        me = users.get(me_id)
        self.assertEqual((me["ref_months"], me["earnings"][0]["kind"], me["earnings"][0]["commission"]), (2, "bonus", 149))
        # the friend pays: 20% to the referrer, once
        store.set_json("s:order:order_F", {"id": "order_F", "user": friend["id"], "plan": "pro", "period": "month", "amount": 499,
                                           "receipt": "r", "status": "created", "created": int(time.time())})
        billing.activate("order_F", "pay_F")
        billing.activate("order_F", "pay_F")
        me = users.get(me_id)
        comm = [e for e in me["earnings"] if e["kind"] == "commission"]
        self.assertEqual([(e["amount"], e["commission"], e["from"]) for e in comm], [(499, 100, "fr•••@example.com")])
        self.assertEqual(referrals.balance(me)["available"], 249)
        # withdraw: needs a UPI ID and ₹500
        self.ig.me = creator_me
        self.login()
        self.assertEqual(self.c.post("/api/refer/payout", json={}).status_code, 400)
        self.assertEqual(self.c.put("/api/refer/upi", json={"upi": "not a upi"}).status_code, 400)
        self.assertEqual(self.c.put("/api/refer/upi", json={"upi": "om@okaxis"}).get_json()["upi"], "om@okaxis")
        self.assertIn("from ₹500", self.c.post("/api/refer/payout", json={}).get_json()["error"])
        me = users.get(me_id)
        me["earnings"].insert(0, {"id": "x", "kind": "commission", "amount": 2000, "commission": 400, "plan": "pro", "at": 1, "from": "x"})
        users.save(me)
        p = self.c.post("/api/refer/payout", json={}).get_json()["payout"]
        self.assertEqual((p["amount"], p["upi"], p["status"]), (649, "om@okaxis", "requested"))
        self.assertEqual(self.c.get("/api/refer").get_json()["available"], 0)
        # the team marks it paid on /owner
        h = {"Authorization": "Basic " + base64.b64encode(b"x:boss").decode()}
        self.assertIn("om@okaxis", self.c.get("/owner", headers=h).get_data(as_text=True))
        self.assertEqual(self.c.post("/owner/payout", json={"user": me_id, "id": p["id"]}).status_code, 401)
        self.assertEqual(self.c.post("/owner/payout", headers=h, json={"user": me_id, "id": p["id"]}).get_json()["payout"]["status"], "paid")
        r = self.c.get("/api/refer").get_json()
        self.assertEqual((r["paid"], r["requested"], r["payouts"][0]["status"]), (649, 0, "paid"))

    def test_bio_signup_form(self):
        self.login()
        self.c.put("/api/page", json={"items": [{"type": "link", "title": "Site", "url": "https://x.com"}],
                                      "signup": {"enabled": True, "ask": "both", "title": "Free guide", "link": "https://g.com"}})
        html = self.c.get("/creator").get_data(as_text=True)
        self.assertIn("Free guide", html)
        self.assertIn('name="phone"', html)
        fan = saas.app.test_client()
        r = fan.post("/creator/join", data={"email": "nope", "phone": "98765 43210"})
        self.assertIn("error=invalid", r.location)
        r = fan.post("/creator/join", data={"email": "Fan@Mail.com", "phone": "98765 43210", "instagram": "@fan.page"})
        self.assertIn("joined=1", r.location)
        self.assertIn("https://g.com", fan.get("/creator?joined=1").get_data(as_text=True))
        c = {x["username"]: x for x in self.c.get("/api/contacts").get_json()["contacts"]}
        self.assertEqual((c["fan.page"]["email"], c["fan.page"]["phone"], c["fan.page"]["source"]), ("fan@mail.com", "+919876543210", "bio_page"))
        self.assertIn("slow", fan.post("/creator/join", data={"email": "b@b.com", "phone": "9876543211"}).location)  # one per minute
        self.assertIn("joined=1", fan.post("/creator/join", data={"website": "spam"}).location)  # bots are silently ignored
        self.assertEqual(self.c.get("/api/page").get_json()["signups"], 1)
        self.c.put("/api/page", json={"signup": {"enabled": False}})
        self.assertEqual(fan.post("/creator/join", data={"email": "c@c.com"}).status_code, 404)

    def test_copy_automation(self):
        self.login()
        self.put_rule("555", keywords=["PROMPTS"], dm="Prompts https://p.com", followup_on=True, followup_dm="Offer")
        self.put_rule("777", keywords=["OTHER"], dm="Keep me")
        r = self.c.post("/api/rules/555/copy", json={"targets": ["777", "888", "kw:GUIDE", "bad key"]}).get_json()
        self.assertEqual((r["copied"], r["skipped"]), (["888", "kw:GUIDE"], ["777"]))
        reels = r["rules"]["reels"]
        self.assertEqual((reels["888"]["dm"], reels["888"]["followup_dm"]), ("Prompts https://p.com", "Offer"))
        self.assertEqual(reels["kw:GUIDE"]["keywords"], ["GUIDE"])
        self.assertEqual(reels["777"]["dm"], "Keep me")
        r = self.c.post("/api/rules/555/copy", json={"targets": ["777"], "replace": True}).get_json()
        self.assertEqual(r["rules"]["reels"]["777"]["dm"], "Prompts https://p.com")
        self.assertEqual(self.c.post("/api/rules/999/copy", json={"targets": ["1"]}).status_code, 404)

    def test_multiple_accounts(self):
        self.login()  # @creator (1789)
        self.ig.me = {"id": "asid3", "user_id": "3003", "username": "second.page", "name": "S", "profile_picture_url": "", "followers_count": 5}
        self.connect_ig()
        self.assertEqual(self.c.get("/api/me").get_json()["account"]["username"], "second.page")
        html = self.c.get("/app").get_data(as_text=True)
        self.assertIn('data-switch="1789"', html)
        self.assertEqual(self.c.post("/api/switch", json={"id": "1789"}).status_code, 200)
        self.assertEqual(self.c.get("/api/me").get_json()["account"]["username"], "creator")
        self.assertEqual(self.c.post("/api/switch", json={"id": "9999"}).status_code, 403)  # not connected to this login
        # disconnecting one keeps you in the other
        self.assertTrue(self.c.post("/api/disconnect", json={}).get_json()["switched"])
        self.assertEqual(self.c.get("/api/me").get_json()["account"]["username"], "second.page")
        self.c.post("/logout")
        self.assertEqual(self.c.get("/api/me").status_code, 401)

    def test_saved_replies(self):
        self.login()
        r = self.c.put("/api/saved-replies", json={"replies": [{"title": "UPI", "text": "UPI chalta hai {username}"}, {"title": "", "text": "x"}]})
        self.assertEqual(r.get_json()["replies"], [{"title": "UPI", "text": "UPI chalta hai {username}"}])
        self.assertEqual(len(self.c.get("/api/saved-replies").get_json()["replies"]), 1)

    def test_contact_tags(self):
        self.login()
        self.put_rule("555", require_follow=False, comment_reply="", tags="Prompts Lead, launch")
        self.assertEqual(store.load_rules("1789")["reels"]["555"]["tags"], "prompts lead, launch")
        self.hook(comment("PROMPTS"))
        c = self.c.get("/api/contacts").get_json()["contacts"][0]
        self.assertEqual(c["tags"], ["prompts lead", "launch"])
        r = self.c.put("/api/contacts/tags", json={"key": c["key"], "tags": "vip, VIP, bought"}).get_json()
        self.assertEqual(r["contact"]["tags"], ["vip", "bought"])
        csv = self.c.get("/api/contacts.csv?tag=vip").get_data(as_text=True)
        self.assertIn("vip; bought", csv)
        self.assertEqual(self.c.get("/api/contacts.csv?tag=nobody").get_data(as_text=True).count("\n"), 1)
        self.assertEqual(self.c.put("/api/contacts/tags", json={"key": "nope", "tags": "x"}).status_code, 404)

    def test_autodm_wizard_backend(self):
        self.login()
        # primary DM with a button, comment replies switched off, per-automation numbers
        self.put_rule("555", require_follow=True, comment_reply="Thanks!", replies_on=False, dm="Here you go",
                      dm_button_text="Open", dm_button_url="https://x.com/p")
        self.assertEqual(self.put_rule("556", dm="x", dm_button_url="javascript:1").status_code, 400)
        self.hook(comment("PROMPTS", cid="w1"))
        self.assertEqual(self.ig.replies(), [])  # replies switched off
        payload = self.ig.messages()[-1]["message"]["attachment"]["payload"]["buttons"][0]["payload"]
        tap = lambda p: {"entry": [{"id": "1789", "messaging": [{"sender": {"id": "31"}, "postback": {"payload": p}}]}]}
        self.hook(tap(payload))
        final = self.ig.messages()[-1]["message"]["attachment"]["payload"]
        self.assertEqual((final["text"], final["buttons"][0]["url"]), ("Here you go", "https://x.com/p"))
        st = self.c.get("/api/rules").get_json()["stats"]["555"]
        self.assertEqual((st["runs"], st["clicks"]), (1, 1))
        summary = self.c.get("/api/autodm-summary").get_json()
        self.assertEqual(len(summary["daily"]["dms"]), 14)
        # "next post": waits, then moves onto the first reel posted after it was created
        self.assertEqual(self.put_rule("next", keywords=["GUIDE"], require_follow=False, comment_reply="", dm="Guide!").status_code, 200)
        since = store.load_rules("1789")["reels"]["next"]["since"]
        self.assertTrue(since)
        self.ig.media[0]["timestamp"] = "2999-01-01T00:00:00+0000"  # reel 777 is newer
        self.hook(comment("GUIDE pls", cid="w2", media="777"))
        reels = store.load_rules("1789")["reels"]
        self.assertNotIn("next", reels)
        self.assertEqual(reels["777"]["dm"], "Guide!")
        self.assertEqual(self.ig.messages()[-1]["recipient"], {"comment_id": "w2"})
        # deleting removes its numbers
        self.c.delete("/api/rules/555", json={})
        self.assertNotIn("555", self.c.get("/api/rules").get_json()["stats"])

    def test_exclude_once_delay(self):
        self.login()
        self.put_rule("555", keywords=["PROMPTS"], require_follow=False, comment_reply="", dm="Here", exclude=["scam"],
                      once_per_person=True)
        self.hook(comment("PROMPTS scam?", cid="x1"))
        self.assertEqual(self.ig.messages(), [])  # excluded word
        self.hook(comment("PROMPTS", cid="x2"))
        self.hook(comment("PROMPTS again", cid="x3"))  # same person, same post
        self.assertEqual(len(self.ig.messages()), 1)
        # delay: queued, then sent when due
        self.put_rule("777", keywords=["GUIDE"], require_follow=False, comment_reply="Sent!", dm="Guide", delay_min=5)
        self.hook(comment("GUIDE", cid="x4", media="777"))
        self.assertEqual(len(self.ig.messages()), 1)
        self.assertEqual(len(self.ig.replies()), 1)  # the public reply doesn't wait
        later = engine.time.time() + 5 * 60 + 5
        with mock.patch.object(engine.time, "time", lambda: later), mock.patch.object(store.time, "time", lambda: later):
            self.assertEqual(engine.send_due_followups(), 1)
        self.assertEqual(self.ig.messages()[-1], {"recipient": {"comment_id": "x4"}, "message": {"text": "Guide"}})
        self.assertEqual(self.put_rule("778", dm="x", delay_min=7).get_json()["reels"]["778"]["delay_min"], 0)

    def test_integrations_webhook(self):
        self.login()
        self.assertEqual(self.c.put("/api/integrations", json={"url": "http://x.com/h", "enabled": True}).status_code, 400)
        self.assertEqual(self.c.put("/api/integrations", json={"url": "https://127.0.0.1/h", "enabled": True}).status_code, 400)
        public = lambda host, port: [(2, 1, 6, "", ("93.184.216.34", port))]
        with mock.patch("socket.getaddrinfo", public):
            r = self.c.put("/api/integrations", json={"url": "https://hooks.example.com/catch/1", "enabled": True}).get_json()
            self.assertTrue(r["enabled"])
            self.assertEqual(self.c.post("/api/integrations/test", json={}).status_code, 200)
            # a lead from the DM flow is sent too
            self.put_rule("kw:GUIDE", keywords=["GUIDE"], require_follow=False, comment_reply="", ask_email=True, dm="Guide")
            tap = {"entry": [{"id": "1789", "messaging": [{"sender": {"id": "71"}, "postback": {"payload": "GET|kw:GUIDE"}}]}]}
            self.hook(tap)
            self.hook(dm("me@x.com", sender="71", mid="h1"))
        hooks = [c[2] for c in self.ig.calls if c[1] == "https://hooks.example.com/catch/1"]
        self.assertEqual([h["event"] for h in hooks], ["test", "lead"])
        self.assertEqual((hooks[1]["email"], hooks[1]["automation"], hooks[1]["account"]), ("me@x.com", "kw:GUIDE", "creator"))

    def test_live_variations_activity(self):
        self.login()
        # Live comments: the "live" automation, private-reply DM, no public reply
        self.assertEqual(self.put_rule("live", keywords=["LINK"], require_follow=False, comment_reply="x", dm="{Hi|Hey} there").status_code, 200)
        body = {"entry": [{"id": "1789", "changes": [{"field": "live_comments", "value": {
            "id": "lc1", "text": "link please", "from": {"id": "44", "username": "viewer"}, "media": {"id": "999"}}}]}]}
        self.hook(body)
        msg = self.ig.messages()[-1]
        self.assertEqual(msg["recipient"], {"comment_id": "lc1"})
        self.assertIn(msg["message"]["text"], ("Hi there", "Hey there"))  # variations
        self.assertEqual(self.ig.replies(), [])
        self.hook(comment("LINK", cid="lc2"))  # ordinary comments don't use the Live automation
        self.assertEqual(len(self.ig.messages()), 1)
        self.assertEqual(engine.vary("{username} {a|b}") in ("{username} a", "{username} b"), True)
        # activity page and CSV
        self.assertEqual(self.c.get("/app/activity").status_code, 200)
        self.assertGreaterEqual(len(self.c.get("/api/activity?all=1").get_json()), 1)
        self.assertIn("viewer", self.c.get("/api/activity.csv").get_data(as_text=True))

    def test_demo_inbox(self):
        self.c.get("/demo")
        self.assertEqual(self.c.get("/app/inbox").status_code, 200)
        inbox = self.c.get("/api/inbox").get_json()
        self.assertTrue(inbox["ready"])
        self.assertEqual(sum(t["status"] == "needs_you" for t in inbox["threads"]), 2)
        self.assertTrue(self.c.post("/api/ai/test", json={"message": "refund chahiye"}).get_json()["needs_human"])
        self.hook({"entry": [{"id": demo.DEMO_ID, "messaging": [{"sender": {"id": "5"}, "message": {"text": "kitne ka hai", "mid": "d1"}}]}]})
        self.assertIn("₹149", ai_agent.messages(demo.DEMO_ID, "5")[-1]["text"])
        self.assertEqual(len(self.ig.calls), 0)

    def tap(self, payload, sender="41"):
        return self.hook({"entry": [{"id": "1789", "messaging": [{"sender": {"id": sender}, "postback": {"payload": payload}}]}]})

    def test_quick_reply_menu(self):
        self.login()
        r = self.put_rule("kw:START", keywords=["START"], require_follow=False, comment_reply="", dm="Kya chahiye {username}?",
                          menu=[{"title": "Free guide", "text": "Ye lo guide", "url": "https://g.com", "button": "Open"},
                                {"title": "Course", "text": "Course details"}, {"title": "", "text": "dropped"},
                                {"title": "4th", "text": "x"}, {"title": "5th", "text": "y"}])
        self.assertEqual(len(r.get_json()["rule"]["menu"]) if "rule" in r.get_json() else
                         len(store.load_rules("1789")["reels"]["kw:START"]["menu"]), 3)
        self.hook(dm("start", sender="41"))
        first = json.dumps(self.ig.messages()[-1])
        self.assertIn("MENU|kw:START|0", first)
        self.assertIn("Kya chahiye fan?", first)
        self.tap("MENU|kw:START|0")
        last = json.dumps(self.ig.messages()[-1])
        self.assertIn("Ye lo guide", last)
        self.assertIn("https://g.com", last)
        self.tap("MENU|kw:START|1")
        self.assertIn("Course details", json.dumps(self.ig.messages()[-1]))
        n = len(self.ig.messages())
        self.tap("MENU|kw:START|7")
        self.tap("MENU|kw:NOPE|0")
        self.assertEqual(len(self.ig.messages()), n)
        self.assertEqual(store.rule_stats("1789", ["kw:START"])["kw:START"].get("menu_0"), 1)

    def test_welcome_message(self):
        self.login()
        self.put_rule("kw:GUIDE", keywords=["GUIDE"], require_follow=False, comment_reply="", dm="Guide https://g.com")
        self.assertEqual(self.c.put("/api/welcome", json={"enabled": True, "text": ""}).status_code, 400)
        w = self.c.put("/api/welcome", json={"enabled": True, "text": "Hi {username}! Kya chahiye?", "buttons": [
            {"type": "url", "title": "Shop", "value": "https://shop.com"}, {"type": "kw", "title": "Guide", "value": "kw:GUIDE"},
            {"type": "kw", "title": "Bad", "value": "kw:MISSING"}, {"type": "url", "title": "Bad", "value": "javascript:x"}]}).get_json()
        self.assertEqual([b["title"] for b in w["buttons"]], ["Shop", "Guide"])
        self.hook(dm("hello", sender="61"))
        first = json.dumps(self.ig.messages()[-1])
        self.assertIn("Hi fan! Kya chahiye?", first)
        self.assertIn("KW|kw:GUIDE", first)
        n = len(self.ig.messages())
        self.hook(dm("hello again", sender="61", mid="m2"))  # only the first time
        self.assertEqual(len(self.ig.messages()), n)
        self.tap("KW|kw:GUIDE", sender="61")
        self.assertIn("Guide https://g.com", json.dumps(self.ig.messages()[-1]))
        self.hook(dm("GUIDE", sender="62"))  # a keyword wins over the welcome
        self.assertNotIn("Kya chahiye", json.dumps(self.ig.messages()[-1]))

    def test_link_click_tracking(self):
        self.login()
        with mock.patch.object(engine, "PUBLIC_URL", "https://replyinbox.in"):
            self.put_rule("kw:GUIDE", keywords=["GUIDE"], require_follow=False, comment_reply="", dm="Guide https://g.com/x?a=1",
                          dm_button_text="Open", dm_button_url="https://shop.com")
            self.put_rule("kw:AFF", keywords=["AFF"], require_follow=False, comment_reply="", dm="Deal https://amzn.to/abc", track_links=False)
            self.hook(dm("GUIDE", sender="71"))
            sent = json.dumps(self.ig.messages()[-1])
            self.assertNotIn("g.com", sent)
            self.assertNotIn("shop.com", sent)
            codes = __import__("re").findall(r"https://replyinbox.in/l/([0-9a-f]{10})", sent)
            self.assertEqual(len(codes), 2)
            self.hook(dm("AFF", sender="72"))
            self.assertIn("https://amzn.to/abc", json.dumps(self.ig.messages()[-1]))
        self.c.get("/logout")
        r = self.c.get(f"/l/{codes[0]}")
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.location.startswith(("https://g.com/x?a=1&utm_source=instagram&utm_medium=dm&utm_campaign=guide",
                                                "https://shop.com?utm_source=instagram")), r.location)
        self.c.get(f"/l/{codes[1]}")
        self.assertEqual(self.c.get("/l/0000000000").status_code, 404)
        self.assertEqual(self.c.get("/l/../etc").status_code, 404)
        self.assertEqual(store.rule_stats("1789", ["kw:GUIDE"])["kw:GUIDE"].get("link_clicks"), 2)

    def test_broadcast_to_recent_chats(self):
        self.login()
        for i in range(3):
            self.hook(dm("hi", sender=f"9{i}", mid=f"b{i}"))
        old = store.account_key("1789", "recent")
        store.redis("HSET", old, "999", 1)  # a chat from long ago is outside Instagram's window
        info = self.c.get("/api/broadcast").get_json()
        self.assertEqual(info["eligible"], 3)
        self.assertEqual(self.c.post("/api/broadcast", json={"id": "x1", "text": ""}).status_code, 400)
        self.assertEqual(self.c.post("/api/broadcast", json={"id": "x1", "text": "Live!", "url": "ftp://x"}).status_code, 400)
        store.redis("DEL", store.account_key("1789", "counts"))
        before = len(self.ig.messages())
        with mock.patch.object(saas, "BROADCAST_BATCH", 2):
            r1 = self.c.post("/api/broadcast", json={"id": "x1", "text": "Live in 1 hour {username}!", "url": "https://live.com", "button": "Join"}).get_json()
            self.assertEqual((r1["sent"], r1["done"]), (2, False))
            r2 = self.c.post("/api/broadcast", json={"id": "x1", "text": "Live in 1 hour {username}!", "url": "https://live.com", "button": "Join"}).get_json()
            self.assertEqual((r2["sent"], r2["left"], r2["done"]), (1, 0, True))
        sent = self.ig.messages()[before:]
        self.assertEqual(sorted(m["recipient"]["id"] for m in sent), ["90", "91", "92"])
        self.assertIn("https://live.com", json.dumps(sent[0]))
        self.assertEqual(self.c.get("/api/broadcast").get_json()["history"][0]["to"], 3)

    def test_push_notifications_and_app(self):
        import push
        self.assertEqual(self.c.get("/manifest.webmanifest").status_code, 200)
        sw = self.c.get("/sw.js")
        self.assertEqual(sw.status_code, 200)
        self.assertIn("/api/notifications/latest", sw.get_data(as_text=True))
        self.login()
        info = self.c.get("/api/notifications").get_json()
        self.assertEqual(len(base64.urlsafe_b64decode(info["key"] + "==")), 65)
        bad = self.c.post("/api/notifications/subscribe", json={"endpoint": "https://evil.example.com/x"})
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(self.c.post("/api/notifications/subscribe", json={"endpoint": "http://fcm.googleapis.com/x"}).status_code, 400)
        ep = "https://fcm.googleapis.com/fcm/send/abc"
        self.assertEqual(self.c.post("/api/notifications/subscribe", json={"endpoint": ep}).status_code, 200)
        self.assertEqual(self.c.get("/api/notifications").get_json()["devices"], 1)
        pushes = []
        with mock.patch.object(push.requests, "post", lambda url, **k: pushes.append((url, k["headers"])) or Resp({}, 201)):
            self.assertEqual(self.c.post("/api/notifications/test", json={}).get_json()["sent"], 1)
        self.assertEqual(pushes[0][0], ep)
        self.assertTrue(pushes[0][1]["Authorization"].startswith("vapid t="))
        header = json.loads(base64.urlsafe_b64decode(pushes[0][1]["Authorization"][8:].split(".")[0] + "=="))
        self.assertEqual(header["alg"], "ES256")
        self.assertTrue(self.c.get("/api/notifications/latest").get_json()["title"])
        with mock.patch.object(push.requests, "post", lambda url, **k: Resp({}, 410)):
            push.notify(store.load_account("1789"), "x", "y")
        self.assertEqual(push.devices("1789"), 0)  # an expired device is dropped
        self.c.put("/api/notifications/prefs", json={"lead": False, "handoff": True})
        self.assertEqual(self.c.get("/api/notifications").get_json()["prefs"]["lead"], False)
        self.assertEqual(push.notify({"demo": True, "id": "d"}, "x", "y"), 0)

    def test_automation_insights(self):
        self.login()
        self.put_rule("kw:GUIDE", keywords=["GUIDE"], require_follow=False, comment_reply="", dm="Guide https://g.com",
                      menu=[{"title": "A", "text": "a"}, {"title": "B", "text": "b"}])
        self.hook(dm("GUIDE", sender="31"))
        self.tap("MENU|kw:GUIDE|1", sender="31")
        r = self.c.get("/api/rules/kw:GUIDE/insights").get_json()
        self.assertEqual(len(r["daily"]), 30)
        self.assertEqual(r["daily"][-1]["runs"], 1)
        self.assertEqual(r["last30"]["runs"], 1)
        self.assertEqual(sum(r["hours"]), 1)
        self.assertEqual(len(r["best_hours"]), 3)
        self.assertEqual([m["picked"] for m in r["menu"]], [0, 1])
        self.assertEqual(self.c.get("/api/rules/kw:NOPE/insights").status_code, 404)
        # stats follow a next-post automation onto the reel, and go away with the automation
        store.rule_count("1789", "next", "runs", 2)
        store.move_rule_stats("1789", "next", "777")
        self.assertEqual(store.rule_daily("1789", "777", 1)[0][1]["runs"], 2)
        self.c.delete("/api/rules/kw:GUIDE", json={})
        self.assertEqual(store.hash_all(store.account_key("1789", "rsd:kw:GUIDE")), {})

    def test_content_plan_approval_queue(self):
        self.login()
        claude = FakeClaude()
        self.enterContext(mock.patch.object(ai_agent, "client", lambda: claude))
        self.enterContext(mock.patch.object(ai_agent, "FREE_AI_TRIAL", 5))
        week = lambda n, start="2030-01-01": {"drafts": [
            {"date": f"2030-01-0{i + 1}", "format": "reel" if i % 2 == 0 else "carousel", "hook": f"Hook {i}",
             "outline": ["beat 1", "beat 2"], "caption": f"Caption {i}. Comment GUIDE", "keyword": "guide" if i == 0 else ""}
            for i in range(n)]}
        self.assertIn("Content plan", self.c.get("/app/plan").get_data(as_text=True))
        # 7 days needs 7 credits; the free trial here has 5
        r = self.c.post("/api/drafts/fill", json={"days": 7, "start": "2030-01-01"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("7 AI credits", r.get_json()["error"])
        self.assertEqual(claude.requests, [])
        claude.answers.append(week(3))
        d = self.c.post("/api/drafts/fill", json={"days": 3, "start": "2030-01-01", "brief": "Launch on Friday"}).get_json()
        self.assertEqual((d["added"], d["counts"]["draft"], d["credits_left"]), (3, 3, 2))
        self.assertIn("Launch on Friday", claude.requests[0]["messages"][0]["content"])
        self.assertEqual(claude.requests[0]["model"], ai_agent.AI_MODEL)
        first = d["drafts"][0]
        self.assertEqual((first["keyword"], first["status"], first["format"]), ("GUIDE", "draft", "reel"))
        # approve / reject with a note / edit / bad status; PATCH-style changes go through PUT so viewers stay read-only
        did = first["id"]
        self.assertEqual(self.c.put(f"/api/drafts/{did}", json={"status": "approved"}).get_json()["counts"]["approved"], 1)
        other = d["drafts"][1]["id"]
        self.c.put(f"/api/drafts/{other}", json={"status": "rejected", "note": "too salesy"})
        self.assertEqual(self.c.put(f"/api/drafts/{did}", json={"status": "nope"}).status_code, 400)
        edited = self.c.put(f"/api/drafts/{did}", json={"hook": "New hook", "outline": "a\nb\n", "format": "story"}).get_json()
        e = next(x for x in edited["drafts"] if x["id"] == did)
        self.assertEqual((e["hook"], e["outline"], e["format"], e["edited"], e["status"]), ("New hook", ["a", "b"], "story", True, "approved"))
        # the next week's prompt learns from approvals and rejections
        claude.answers.append({"drafts": [{"date": "2030-01-03", "format": "carousel", "hook": "Better hook", "outline": [],
                                           "caption": "c", "keyword": ""}]})
        r = self.c.post(f"/api/drafts/{d['drafts'][2]['id']}/rewrite", json={"feedback": "funnier"}).get_json()
        rw = next(x for x in r["drafts"] if x["id"] == d["drafts"][2]["id"])
        self.assertEqual((rw["hook"], rw["note"], r["credits_left"]), ("Better hook", "funnier", 1))
        system = claude.requests[1]["system"][0]["text"]
        self.assertIn("New hook", system)
        self.assertIn("too salesy", system)
        self.assertIn("funnier", claude.requests[1]["messages"][0]["content"])
        # delete; unknown id
        self.assertEqual(self.c.delete(f"/api/drafts/{other}", json={}).get_json()["counts"]["rejected"], 0)
        self.assertEqual(self.c.delete("/api/drafts/zzz", json={}).status_code, 400)
        # Claude (MCP) sees and decides on drafts
        key = self.c.post("/api/mcp-key", json={}).get_json()["key"]
        H = {"Authorization": f"Bearer {key}"}
        call = lambda name, args={}: self.c.post("/mcp", headers=H, json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                                                          "params": {"name": name, "arguments": args}}).get_json()["result"]
        listed = call("list_drafts", {})["structuredContent"]
        self.assertEqual([x["hook"] for x in listed["drafts"]], ["Better hook"])
        self.assertEqual(call("approve_draft", {"draft_id": listed["drafts"][0]["id"], "decision": "approve"})["structuredContent"]["draft"]["status"], "approved")
        self.assertTrue(call("approve_draft", {"draft_id": "zzz"})["isError"])
        claude.answers.append(week(1))
        self.assertEqual(call("draft_week", {"days": 1, "start_date": "2030-02-01"})["structuredContent"]["added"], 1)
        self.assertTrue(call("draft_week", {"days": 2})["isError"])  # out of credits
        self.assertEqual(call("edit_draft", {"draft_id": did, "caption": "Short"})["structuredContent"]["draft"]["caption"], "Short")
        self.assertIn("plan", [a["action"] for a in self.c.get("/api/activity").get_json()])

    def test_content_plan_demo(self):
        self.c.get("/demo")
        d = self.c.post("/api/drafts/fill", json={"days": 7}).get_json()
        self.assertEqual(d["added"], 7)
        self.assertTrue(all(x["hook"] and x["caption"] for x in d["drafts"]))

    def test_youtube_scheduling(self):
        self.login()
        g = FakeGoogle()
        # off unless configured and allowed for this username
        self.assertNotIn("/app/youtube", self.c.get("/app/plan").get_data(as_text=True))
        self.assertEqual(self.c.post("/api/youtube/videos", json={}).status_code, 403)
        self.enterContext(mock.patch.dict(os.environ, YT_CLIENT_ID="cid", YT_CLIENT_SECRET="sec", YT_ACCOUNTS="@Creator, other"))
        self.enterContext(mock.patch.object(youtube.requests, "post", g.post))
        self.enterContext(mock.patch.object(youtube.requests, "request", g.request))
        self.assertIn("/app/youtube", self.c.get("/app/plan").get_data(as_text=True))
        self.assertIsNone(self.c.get("/api/youtube").get_json()["channel"])
        # connect: state is checked, offline access asked, channel saved
        r = self.c.get("/youtube/connect")
        q = parse_qs(urlparse(r.location).query)
        self.assertEqual((q["access_type"][0], q["prompt"][0]), ("offline", "consent"))
        self.assertTrue(q["redirect_uri"][0].endswith("/youtube/callback"))
        self.assertIn("error", self.c.get("/youtube/callback?code=x&state=wrong").location)
        r = self.c.get("/youtube/connect")
        state = parse_qs(urlparse(r.location).query)["state"][0]
        self.assertIn("connected=1", self.c.get(f"/youtube/callback?code=x&state={state}").location)
        st = self.c.get("/api/youtube").get_json()
        self.assertEqual(st["channel"]["title"], "Om Tech")
        self.assertNotIn("1//R", json.dumps(st))  # the refresh token never reaches the browser
        self.assertEqual(self.c.post("/api/youtube/token", json={}).get_json()["access_token"], "ya29.A")
        # add a short (vertical, 40 s): #Shorts is added; tags cleaned; then the browser reports the upload
        item = self.c.post("/api/youtube/videos", json={"file_name": "tip.mp4", "duration": 40, "vertical": True, "title": "Tip <1>",
                                                        "description": "One tip", "tags": "#ai, AI, chatgpt", "category": "28"}).get_json()["item"]
        self.assertEqual((item["status"], item["title"], item["tags"], item["short"]), ("uploading", "Tip ‹1›", ["ai", "chatgpt"], True))
        self.assertTrue(item["description"].endswith("#Shorts"))
        self.assertEqual(self.c.post(f"/api/youtube/videos/{item['id']}/uploaded", json={"video_id": "bad id!"}).status_code, 400)
        v = self.c.post(f"/api/youtube/videos/{item['id']}/uploaded", json={"video_id": "abc123XYZ_-"}).get_json()["item"]
        self.assertEqual((v["status"], v["studio_url"]), ("draft", "https://studio.youtube.com/video/abc123XYZ_-/edit"))
        v = self.c.post(f"/api/youtube/videos/{item['id']}/thumb", json={"ok": False, "error": "verify your phone"}).get_json()["item"]
        self.assertEqual(v["thumb_error"], "verify your phone")
        # approve: past time refused; future time → videos.update with the whole snippet and status.publishAt
        r = self.c.post(f"/api/youtube/videos/{item['id']}/approve", json={"publish_at": "2020-01-01T10:00:00Z"})
        self.assertIn("10 minutes", r.get_json()["error"])
        g.fail[youtube.API + "/videos"] = "quotaExceeded"
        r = self.c.post(f"/api/youtube/videos/{item['id']}/approve", json={"publish_at": "2099-05-01T12:30:00.000Z"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("daily upload limit", r.get_json()["error"])
        kept = next(x for x in r.get_json()["items"] if x["id"] == item["id"])
        self.assertEqual(kept["status"], "approved")  # stays in the queue, with the error, to retry
        del g.fail[youtube.API + "/videos"]
        v = self.c.post(f"/api/youtube/videos/{item['id']}/approve", json={}).get_json()["item"]
        self.assertEqual((v["status"], v["error"], v["publish_at"]), ("scheduled", "", "2099-05-01T12:30:00Z"))
        put = [c for c in g.calls if c[0] == "PUT"][-1]
        self.assertEqual(put[2], {"part": "snippet,status"})
        self.assertEqual(put[3]["status"], {"privacyStatus": "private", "publishAt": "2099-05-01T12:30:00Z", "selfDeclaredMadeForKids": False,
                                            "embeddable": True, "license": "youtube", "publicStatsViewable": True})
        self.assertEqual((put[3]["snippet"]["categoryId"], put[3]["snippet"]["tags"]), ("28", ["ai", "chatgpt"]))
        # editing a scheduled video updates YouTube too
        n = len(g.calls)
        self.c.put(f"/api/youtube/videos/{item['id']}", json={"title": "Better tip"})
        self.assertEqual(g.calls[n][3]["snippet"]["title"], "Better tip")
        # Claude sees it and can stop it
        key = self.c.post("/api/mcp-key", json={}).get_json()["key"]
        call = lambda name, args={}: self.c.post("/mcp", headers={"Authorization": f"Bearer {key}"}, json={
            "jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}}).get_json()["result"]
        self.assertEqual(call("list_youtube_videos", {"status": "scheduled"})["structuredContent"]["videos"][0]["title"], "Better tip")
        self.assertEqual(call("approve_youtube_video", {"video_id": item["id"], "decision": "reject"})["structuredContent"]["video"]["status"], "rejected")
        self.assertEqual([c for c in g.calls if c[0] == "PUT"][-1][3]["status"], {"privacyStatus": "private", "selfDeclaredMadeForKids": False})
        self.c.post(f"/api/youtube/videos/{item['id']}/review", json={})
        self.c.post(f"/api/youtube/videos/{item['id']}/approve", json={})
        # once YouTube makes it public, the queue shows it as published
        g.public.add("abc123XYZ_-")
        with mock.patch.object(youtube.time, "strftime", lambda f, t=None: "2099-05-01T13:00:00Z"):
            st = self.c.get("/api/youtube").get_json()
        self.assertEqual(st["items"][0]["status"], "published")
        # AI details: needs notes; uses a credit
        claude = FakeClaude()
        claude.answers.append({"title": "Best tip", "description": "Desc", "tags": ["a", "b"]})
        self.enterContext(mock.patch.object(ai_agent, "client", lambda: claude))
        self.assertEqual(self.c.post("/api/youtube/details", json={}).status_code, 400)
        d = self.c.post("/api/youtube/details", json={"notes": "AI tools", "duration": 30, "vertical": True}).get_json()
        self.assertEqual((d["title"], d["description"]), ("Best tip", "Desc\n\n#Shorts"))
        self.assertIn("YouTube Short", claude.requests[0]["messages"][0]["content"])
        # disconnect revokes at Google
        self.c.post("/api/youtube/disconnect", json={})
        self.assertTrue(any(c[1] == youtube.REVOKE_URL for c in g.calls))
        self.assertIsNone(self.c.get("/api/youtube").get_json()["channel"])

    def test_unsaved_link_page_previews_for_owner_only(self):
        self.login()
        self.assertEqual(self.c.get("/creator").status_code, 200)
        self.assertEqual(saas.app.test_client().get("/creator").status_code, 404)

    def test_studio_link_page_theme(self):
        import store
        self.login()
        acc = store.load_account("1789")
        acc["followers"] = 28709
        store.save_account(acc)
        self.c.put("/api/page", json={"name": "Om AI Tips", "theme": "studio", "socials": {"instagram": "aiwith.om"},
                                      "items": [{"title": "Freebies", "url": "https://x.com/free", "featured": True},
                                                {"type": "product", "title": "Course", "url": "https://x.com/c", "price": "₹499"}]})
        h = self.c.get("/creator").get_data(as_text=True)
        for part in ('class="t-studio"', "Om <span>AI Tips</span>", "28K followers", "Follow @aiwith.om", "FREE FOR YOU", "Links &amp; products", "₹499"):
            self.assertIn(part, h)
        self.assertEqual([saas.compact_number(n) for n in (950, 1250, 28709, 1_250_000)], ["950", "1.2K", "28K", "1.2M"])

    def test_link_page_themes_and_socials(self):
        self.login()
        # pages saved with the old theme names still open in the new look
        self.c.put("/api/page", json={"name": "C", "theme": "violet", "socials": {"youtube": "@chan", "whatsapp": "+91 98765 43210",
                                                                                  "email": "a@b.co", "x": "@me", "website": "me.in"}})
        h = self.c.get("/creator").get_data(as_text=True)
        for part in ('class="t-studio"', "https://www.youtube.com/@chan", "https://wa.me/919876543210", "mailto:a@b.co",
                     "https://x.com/me", "https://me.in", "https://www.instagram.com/creator/"):
            self.assertIn(part, h)
        self.c.put("/api/page", json={"name": "C", "theme": "ocean", "photo": "javascript:alert(1)"})
        page = self.c.get("/api/page").get_json()["page"]
        self.assertEqual((page["theme"], page["photo"]), ("ocean", ""))
        self.assertIn('class="t-ocean"', self.c.get("/creator").get_data(as_text=True))

    def test_avatar_link_stays_fresh(self):
        self.login()
        acc = store.load_account("1789")
        acc["pic"] = "https://cdn.example/old.jpg"
        store.save_account(acc)
        self.assertEqual(self.c.get("/api/me").get_json().get("pic", "/avatar/1789"), "/avatar/1789")
        heads = []

        def head(url, **kw):
            heads.append(url)
            return mock.Mock(status_code=403 if "old" in url else 200)
        with mock.patch.object(saas.requests, "head", head), \
                mock.patch.object(engine.Instagram, "get", return_value={"profile_picture_url": "https://cdn.example/new.jpg"}):
            r = saas.app.test_client().get("/avatar/1789")  # works without logging in (link pages use it)
            self.assertEqual((r.status_code, r.location), (302, "https://cdn.example/new.jpg"))
            self.assertEqual(store.load_account("1789")["pic"], "https://cdn.example/new.jpg")
            saas.app.test_client().get("/avatar/1789")
            self.assertEqual(heads, ["https://cdn.example/old.jpg"])  # checked once, then trusted for a while
        self.assertEqual(saas.app.test_client().get("/avatar/999").status_code, 404)
        self.assertEqual(saas.app.test_client().get("/avatar/x;y").status_code, 404)
        self.assertEqual(saas.avatar_url({"id": "1", "pic": "https://x", "demo": True}), "")

    def test_text_files_open_as_guides(self):
        import files
        import guides
        self.login()
        self.c.put("/api/page", json={"theme": "candy", "items": [{"type": "product", "title": "My Course", "url": "https://x.com/c",
                                                                   "price": "499", "featured": True}]})
        text = ("My Guide: Day 1 Plan\n\nWelcome to the plan.\n\nThe rules\n\n1. Post daily\n2. Track numbers\n\n"
                "Prompt 1: ideas\n\nGive me 30 ideas\nfor my niche.\n\nToolkit\n\n- Claude\n- Canva\n\n<script>alert(1)</script>")
        rec = {"id": "abc", "acc": "1789", "name": "guide.txt"}
        with mock.patch.object(files, "fetch", return_value=(text.encode(), "text/plain", rec)):
            h = saas.app.test_client().get("/f/abc/guide.txt").get_data(as_text=True)
            raw = saas.app.test_client().get("/f/abc/guide.txt?raw=1")
        for part in ('class="t-candy"', "My Guide:", "<span>Day 1 Plan</span>", 'class="stag">The rules', '<ol class="num">',
                     "Give me 30 ideas\nfor my niche.", "My Course", "₹499 · Get it", "Follow @creator", "?raw=1"):
            self.assertIn(part, h)
        self.assertNotIn("<script>alert", h)  # text is escaped
        self.assertEqual(raw.get_data(as_text=True), text)
        self.assertEqual(guides.product_promo({"items": []}, "x"), ("", ""))

    def test_freebies_page(self):
        self.login()
        anon = saas.app.test_client()
        self.c.put("/api/page", json={"name": "C", "freebies": []})
        self.assertNotIn("FREEBIES", anon.get("/creator").get_data(as_text=True))
        self.assertEqual(anon.get("/creator/free").status_code, 404)
        page = self.c.put("/api/page", json={"name": "C", "freebies": [
            {"k": "live!", "t": "Live Clipper guide", "topic": "AI video", "u": "https://x.com/live"},
            {"k": "tools", "t": "Clip Tools", "topic": "AI editing", "u": "https://x.com/tools"},
            {"k": "bad", "t": "No link", "u": "javascript:alert(1)"},
            {"k": "off", "t": "Hidden", "u": "https://x.com/off", "enabled": False}]}).get_json()["page"]
        self.assertEqual([f["k"] for f in page["freebies"]], ["LIVE", "TOOLS", "OFF"])
        h = anon.get("/creator").get_data(as_text=True)
        self.assertIn("FREEBIES", h)
        self.assertIn("2 FREE", h)
        self.assertIn('href="/creator/free"', h)
        f = anon.get("/creator/free").get_data(as_text=True)
        for part in ("All my freebies", "COMMENT KEYWORD", ">LIVE<", "Clip Tools", 'data-topic="AI video"', "2 free guides"):
            self.assertIn(part, f)
        self.assertNotIn("Hidden", f)
        live = page["freebies"][0]["id"]
        self.assertEqual(anon.get(f"/creator/free/{live}").location, "https://x.com/live")
        self.assertEqual(self.c.get("/api/page").get_json()["clicks"].get("fb_" + live), 1)
        self.assertEqual(anon.get(f"/creator/free/{page['freebies'][2]['id']}").status_code, 404)

    def test_owner_gives_timed_plans_and_deletes_logins(self):
        import users
        self.login()
        h = {"Authorization": "Basic " + base64.b64encode(b"x:boss").decode()}
        uid = users.by_email("om@example.com")["id"]
        self.assertEqual(self.c.post("/owner/plan", json={"user": uid, "plan": "pro", "days": 30}).status_code, 401)
        self.assertEqual(self.c.post("/owner/plan", headers=h, json={"user": uid, "plan": "gold", "days": 30}).status_code, 400)
        r = self.c.post("/owner/plan", headers=h, json={"user": uid, "plan": "pro", "days": 30}).get_json()
        self.assertEqual(r["plan"], "pro")
        self.assertAlmostEqual(r["until"], time.time() + 30 * 86400, delta=60)
        # the same plan again adds the days; the Instagram accounts follow
        r = self.c.post("/owner/plan", headers=h, json={"user": uid, "plan": "pro", "days": 90}).get_json()
        self.assertAlmostEqual(r["until"], time.time() + 120 * 86400, delta=60)
        self.assertEqual(store.load_account("1789")["plan_until"], r["until"])
        # no end date
        self.assertIsNone(self.c.post("/owner/plan", headers=h, json={"user": uid, "plan": "agency", "days": 0}).get_json()["until"])
        self.assertIn("no end date", self.c.get("/owner", headers=h).get_data(as_text=True))
        # a login without Instagram shows up and can be deleted; deleting a login removes its accounts too
        other = users.create("solo@example.com")
        page = self.c.get("/owner", headers=h).get_data(as_text=True)
        self.assertIn("solo@example.com", page)
        self.assertIn("no Instagram connected yet", page)
        self.assertTrue(self.c.post("/owner/user/delete", headers=h, json={"user": other["id"]}).get_json()["ok"])
        self.assertIsNone(users.by_email("solo@example.com"))
        r = self.c.post("/owner/user/delete", headers=h, json={"user": uid}).get_json()
        self.assertEqual(r["accounts_removed"], 1)
        self.assertIsNone(store.load_account("1789"))
        self.assertIsNone(users.get(uid))
        self.assertNotIn("om@example.com", self.c.get("/owner", headers=h).get_data(as_text=True))
        self.assertEqual(self.c.post("/owner/user/delete", headers=h, json={"user": uid}).status_code, 400)

    def test_digital_products_route_flow(self):
        import files
        import shop
        import users
        self.login()
        self.enterContext(mock.patch.dict(os.environ, RAZORPAY_KEY_ID="rzp_test_k", RAZORPAY_KEY_SECRET="sek",
                                          RAZORPAY_WEBHOOK_SECRET="whs", BLOB_READ_WRITE_TOKEN="vercel_blob_rw_store9_secret"))
        calls = []

        def rzp(method, url, json=None, timeout=None, auth=None):
            calls.append((method, url.replace(shop.API, ""), json))
            path = url.replace(shop.API, "")
            if path == "/v2/accounts":
                return Resp({"id": "acc_L1"})
            if path.endswith("/stakeholders"):
                return Resp({"id": "sth_1"})
            if path.endswith("/products") and method == "POST":
                return Resp({"id": "acc_prd_1", "activation_status": "requested"})
            if "/products/" in path:
                return Resp({"id": "acc_prd_1", "activation_status": "activated", "requirements": []})
            if path == "/v1/orders":
                return Resp({"id": "order_S1"})
            return Resp({}, 404)
        self.enterContext(mock.patch.object(shop.requests, "request", rzp))
        blobs = {}

        def put(url, params=None, data=None, headers=None, timeout=None):
            blobs[params["pathname"]] = data
            return Resp({"url": f"https://store9.private.blob.vercel-storage.com/{params['pathname']}", "pathname": params["pathname"]})

        def get(url, headers=None, timeout=None):
            r = Resp({}, 200 if url.split(".com/", 1)[1] in blobs else 404)
            r.content, r.headers = blobs.get(url.split(".com/", 1)[1], b""), {"content-type": "application/pdf"}
            return r
        self.enterContext(mock.patch.object(files.requests, "put", put))
        self.enterContext(mock.patch.object(files.requests, "get", get))
        self.enterContext(mock.patch.object(shop.requests, "post", lambda *a, **k: Resp({"id": "email"})))
        anon = saas.app.test_client()
        # payouts: validation, then the linked account with bank details; only the last 4 digits are kept
        bank = {"name": "Om Kumar", "email": "om@example.com", "phone": "98765 43210", "pan": "abcde1234f",
                "account_number": "4052842007", "ifsc": "kkbk0008072", "street": "12 MG Road", "city": "Bengaluru",
                "state": "Karnataka", "pincode": "560102"}
        self.assertIn("PAN", self.c.put("/api/shop/payout", json={**bank, "pan": "123"}).get_json()["error"])
        p = self.c.put("/api/shop/payout", json=bank).get_json()["payout"]
        self.assertEqual((p["account_id"], p["status"], p["bank"], p["ifsc"]), ("acc_L1", "activated", "•••• 2007", "KKBK0008072"))
        patch = [c for c in calls if c[0] == "PATCH"][0][2]
        self.assertEqual(patch["settlements"], {"account_number": "4052842007", "ifsc_code": "KKBK0008072", "beneficiary_name": "Om Kumar"})
        self.assertNotIn("4052842007", json.dumps(users.by_email("om@example.com")))
        # a product with a private file
        up = self.c.post("/api/shop/upload", data={"file": (io.BytesIO(b"%PDF-pack"), "pack.pdf")}, headers={"X-Upload": "1"},
                         content_type="multipart/form-data").get_json()
        self.assertEqual(anon.get(f"/f/{up['file_id']}/pack.pdf").status_code, 404)  # never public
        self.assertEqual(self.c.get("/api/files").status_code, 403)  # and not in Files
        self.assertIn("Price", self.c.put("/api/shop/products", json={"title": "Pack", "price": "5", **up}).get_json()["error"])
        prod = self.c.put("/api/shop/products", json={"title": "Prompt Pack", "price": "₹499", "desc": "39 prompts", **up}).get_json()["product"]
        page = anon.get(f"/creator/p/{prod['id']}").get_data(as_text=True)
        self.assertIn("Buy now · ₹499", page)
        # order: amount from the product, creator's share transferred to the linked account
        o = anon.post(f"/creator/p/{prod['id']}/order", json={"email": "Fan@Mail.com"}).get_json()
        self.assertEqual((o["order_id"], o["amount"]), ("order_S1", 49900))
        order_body = [c for c in calls if c[1] == "/v1/orders"][0][2]
        share = saas.plans.platform_fee(store.load_account("1789"), 499)["creator_gets"]
        self.assertEqual(order_body["transfers"][0]["account"], "acc_L1")
        self.assertEqual(order_body["transfers"][0]["amount"], int(round(share * 100)))
        self.assertLess(order_body["transfers"][0]["amount"], 49900)
        # wrong signature refused; right one delivers once
        self.assertEqual(anon.post(f"/creator/p/{prod['id']}/paid", json={"order_id": "order_S1", "payment_id": "pay_1", "signature": "x"}).status_code, 400)
        sig = hmac.new(b"sek", b"order_S1|pay_1", hashlib.sha256).hexdigest()
        dl = anon.post(f"/creator/p/{prod['id']}/paid", json={"order_id": "order_S1", "payment_id": "pay_1", "signature": sig}).get_json()["download"]
        body = json.dumps({"event": "payment.captured", "payload": {"payment": {"entity": {"id": "pay_1", "order_id": "order_S1", "status": "captured", "amount": 49900}}}}).encode()
        wsig = hmac.new(b"whs", body, hashlib.sha256).hexdigest()
        self.assertEqual(anon.post("/billing/webhook", data=body, headers={"X-Razorpay-Signature": wsig}).status_code, 200)
        r = self.c.get("/api/shop").get_json()
        self.assertEqual((len(r["sales"]), r["products"][0]["sales"], r["sales"][0]["email"]), (1, 1, "fan@mail.com"))
        self.assertIn("Prompt Pack", anon.get(dl).get_data(as_text=True))
        f = anon.get(dl + "/file")
        self.assertEqual((f.status_code, f.data), (200, b"%PDF-pack"))
        self.assertEqual(anon.get("/d/nope-nope-nope/file").status_code, 404)
        # deleting the product keeps the buyer's download
        self.c.delete(f"/api/shop/products/{prod['id']}", json={})
        self.assertEqual(anon.get(dl + "/file").status_code, 200)
        self.assertEqual(anon.get(f"/creator/p/{prod['id']}").status_code, 404)

    def test_store_locked_event_booking(self):
        import shop
        import users
        self.login()
        self.enterContext(mock.patch.dict(os.environ, RAZORPAY_KEY_ID="rzp_test_k", RAZORPAY_KEY_SECRET="sek"))
        u = users.by_email("om@example.com")
        u["payout"] = {"account_id": "acc_L1", "product_id": "p", "status": "activated"}
        users.save(u)
        n = {"i": 0}
        mails = []

        def rzp(method, url, json=None, timeout=None, auth=None):
            n["i"] += 1
            return Resp({"id": f"order_{n['i']}"})
        self.enterContext(mock.patch.object(shop.requests, "request", rzp))
        self.enterContext(mock.patch.object(shop, "_mail", lambda to, subject, html, reply_to=None: mails.append((to, subject)) or True))
        anon = saas.app.test_client()

        def buy(pid, **buyer):
            o = anon.post(f"/creator/p/{pid}/order", json={"email": "fan@x.co", **buyer})
            if o.status_code != 200:
                return o.get_json()
            oid = o.get_json()["order_id"]
            sig = hmac.new(b"sek", f"{oid}|pay_{oid}".encode(), hashlib.sha256).hexdigest()
            return anon.post(f"/creator/p/{pid}/paid", json={"order_id": oid, "payment_id": f"pay_{oid}", "signature": sig}).get_json()

        # locked content: no file needed; the access page shows the content
        self.assertIn("unlock", self.c.put("/api/shop/products", json={"type": "locked", "title": "VIP", "price": 49}).get_json()["error"])
        lk = self.c.put("/api/shop/products", json={"type": "locked", "title": "VIP list", "price": 49,
                                                    "content": "Join https://chat.example/vip and use code OM10"}).get_json()["product"]
        self.assertIn("Unlock · ₹49", anon.get(f"/creator/p/{lk['id']}").get_data(as_text=True))
        page = anon.get(buy(lk["id"])["download"]).get_data(as_text=True)
        self.assertIn("code OM10", page)
        self.assertIn('href="https://chat.example/vip"', page)
        # event: date in the future, seats, sold out
        start = time.strftime("%Y-%m-%dT19:30", time.gmtime(time.time() + 5 * 86400 + shop.IST))
        ev = self.c.put("/api/shop/products", json={"type": "event", "title": "Live class", "price": 99, "start": start,
                                                    "minutes": 90, "capacity": 1, "join_url": "https://meet.example/abc"}).get_json()["product"]
        self.assertIn("1 seat left", anon.get(f"/creator/p/{ev['id']}").get_data(as_text=True))
        page = anon.get(buy(ev["id"])["download"]).get_data(as_text=True)
        self.assertIn("https://meet.example/abc", page)
        self.assertIn("calendar.google.com", page)
        self.assertIn("Sold out", anon.get(f"/creator/p/{ev['id']}").get_data(as_text=True))
        self.assertEqual(buy(ev["id"])["error"], "Sold out.")
        self.assertIn("past", self.c.put("/api/shop/products", json={"type": "event", "title": "Old", "price": 99,
                                                                     "start": "2020-01-01T10:00"}).get_json()["error"])
        # booking: free slots, a slot is held while paying and booked after
        bk = self.c.put("/api/shop/products", json={"type": "booking", "title": "1:1 call", "price": 499, "minutes": 30,
                                                    "days": [0, 1, 2, 3, 4, 5, 6], "from": "18:00", "to": "19:00", "ahead": 7,
                                                    "notice": 0}).get_json()["product"]
        days = anon.get(f"/creator/p/{bk['id']}/slots").get_json()["days"]
        first = days[-1]["slots"][0]["ts"]
        self.assertEqual(len(days[-1]["slots"]), 2)  # 18:00 and 18:30
        self.assertIn("name", buy(bk["id"], slot=first)["error"])
        anon.post(f"/creator/p/{bk['id']}/order", json={"email": "a@x.co", "name": "A", "slot": first})  # held, not paid
        self.assertIn("taken", buy(bk["id"], name="B", slot=first)["error"])
        store.redis("DEL", f"s:slothold:{bk['id']}:{first}")
        r = buy(bk["id"], name="Riya", slot=first)
        self.assertIn("/d/", r["download"])
        free = [t["ts"] for d in anon.get(f"/creator/p/{bk['id']}/slots").get_json()["days"] for t in d["slots"]]
        self.assertNotIn(first, free)
        self.assertTrue(any(to == "om@example.com" and "New booking" in sub for to, sub in mails))
        sales = self.c.get("/api/shop").get_json()["sales"]
        self.assertEqual(sales[0]["name"], "Riya")
        # reminders: events/bookings in the next 24 hours get one email
        self.assertEqual(shop.send_reminders(now=first - 3600), 1)
        self.assertEqual(shop.send_reminders(now=first - 1800), 0)

    def test_product_page_without_payouts_cant_buy(self):
        import shop
        self.login()
        self.enterContext(mock.patch.dict(os.environ, RAZORPAY_KEY_ID="rzp_test_k", RAZORPAY_KEY_SECRET="sek"))
        store.set_json(store.account_key("1789", "shop"), [{"id": "abcdef1234", "title": "Pack", "price": 99, "file_id": "x", "enabled": True}])
        anon = saas.app.test_client()
        self.assertIn("isn't on sale right now", anon.get("/creator/p/abcdef1234").get_data(as_text=True))
        self.assertEqual(anon.post("/creator/p/abcdef1234/order", json={"email": "a@b.co"}).status_code, 400)
        self.assertFalse(shop.can_sell({}))

    def test_private_files(self):
        import files
        self.login()
        # off unless the username is in FILES_ACCOUNTS
        self.assertNotIn("/app/files", self.c.get("/app/plan").get_data(as_text=True))
        self.assertEqual(self.c.get("/api/files").status_code, 403)
        self.assertEqual(self.c.get("/app/files").status_code, 302)
        self.enterContext(mock.patch.dict(os.environ, FILES_ACCOUNTS="@Creator", BLOB_READ_WRITE_TOKEN="vercel_blob_rw_store9_secret"))
        blobs = {}

        def put(url, params=None, data=None, headers=None, timeout=None):
            path = params["pathname"]
            self.assertEqual(headers["x-vercel-blob-store-id"], "store9")
            if headers["x-vercel-blob-access"] != "private":
                return Resp({}, 400)
            blobs[path] = data
            return Resp({"url": f"https://store9.private.blob.vercel-storage.com/{path}", "pathname": path})

        def get(url, headers=None, timeout=None):
            path = url.split(".com/", 1)[1]
            r = Resp({}, 200 if path in blobs and headers["authorization"].endswith("secret") else 404)
            r.content, r.headers = blobs.get(path, b""), {"content-type": "application/pdf"}
            return r

        def post(url, json=None, headers=None, timeout=None):
            for u in json["urls"]:
                blobs.pop(u.split(".com/", 1)[1], None)
            return Resp({})
        self.enterContext(mock.patch.object(files.requests, "put", put))
        self.enterContext(mock.patch.object(files.requests, "get", get))
        self.enterContext(mock.patch.object(files.requests, "post", post))
        self.assertIn("/app/files", self.c.get("/app/plan").get_data(as_text=True))
        self.assertEqual(self.c.get("/app/files").status_code, 200)
        up = lambda name, body, hdr=True: self.c.post("/api/files", data={"file": (io.BytesIO(body), name)},
                                                      headers={"X-Upload": "1"} if hdr else {}, content_type="multipart/form-data")
        self.assertEqual(up("guide.pdf", b"%PDF", hdr=False).status_code, 415)  # cross-site forms can't upload
        self.assertIn("isn't allowed", up("run.exe", b"MZ").get_json()["error"])
        self.assertIn("over 4 MB", up("big.pdf", b"x" * (4 * 1024 * 1024 + 1)).get_json()["error"])
        f = up("My Guide!.pdf", b"%PDF-1").get_json()["file"]
        self.assertEqual(f["name"], "My-Guide-.pdf")
        self.assertEqual(f["url"], f"/f/{f['id']}/My-Guide-.pdf")
        # anyone with the link can open it (no login), a wrong name can't
        r = saas.app.test_client().get(f["url"])
        self.assertEqual((r.status_code, r.data, r.mimetype), (200, b"%PDF-1", "application/pdf"))
        self.assertEqual(saas.app.test_client().get(f"/f/{f['id']}/other.pdf").status_code, 404)
        self.assertEqual([x["id"] for x in self.c.get("/api/files").get_json()["files"]], [f["id"]])
        # delete: gone from the list, the store and the link
        self.assertTrue(self.c.delete(f"/api/files/{f['id']}", json={}).get_json()["ok"])
        self.assertEqual(self.c.get("/api/files").get_json()["files"], [])
        self.assertEqual(blobs, {})
        self.assertEqual(saas.app.test_client().get(f["url"]).status_code, 404)

    def test_youtube_demo(self):
        self.c.get("/demo")
        st = self.c.get("/api/youtube").get_json()
        self.assertEqual((st["channel"]["title"], len(st["items"])), ("Demo channel", 2))
        self.assertEqual(self.c.post("/api/youtube/token", json={}).status_code, 403)
        v = self.c.post("/api/youtube/videos/demo1/approve", json={}).get_json()["item"]
        self.assertEqual(v["status"], "scheduled")
        self.assertEqual(self.c.get("/app/youtube").status_code, 200)

    def test_sales_tracking_and_utm(self):
        self.login()
        self.assertEqual(self.c.post("/api/products", json={"name": "", "price": 1}).status_code, 400)
        self.assertEqual(self.c.post("/api/products", json={"name": "X", "price": "abc"}).status_code, 400)
        self.assertEqual(self.c.post("/api/products", json={"name": "X", "price": 9, "thanks_url": "javascript:alert(1)"}).status_code, 400)
        prods = self.c.post("/api/products", json={"name": "Prompt pack", "price": "₹149"}).get_json()["products"]
        self.c.post("/api/products", json={"name": "Course", "price": 999, "thanks_url": "https://me.com/thanks"})
        pid, pid2 = [p["id"] for p in self.c.get("/api/sales").get_json()["products"]]
        self.assertTrue(prods[0]["link"].endswith(f"/s/{pid}"))
        with mock.patch.object(engine, "PUBLIC_URL", "https://replyinbox.in"):
            self.put_rule("kw:GUIDE", keywords=["GUIDE"], require_follow=False, comment_reply="", dm="Buy https://shop.com/p", label="Prompts reel")
            self.hook(dm("GUIDE", sender="51"))
            code = __import__("re").search(r"/l/([0-9a-f]{10})", json.dumps(self.ig.messages()[-1])).group(1)
        self.c.get("/logout")
        buyer = saas.app.test_client()
        r = buyer.get(f"/l/{code}")
        self.assertIn("utm_campaign=prompts-reel", r.location)
        r = buyer.get(f"/s/{pid}")  # the payment page sends the buyer back here
        self.assertEqual(r.status_code, 200)
        self.assertIn("Payment received", r.get_data(as_text=True))
        buyer.get(f"/s/{pid}")  # a refresh isn't a second sale
        self.assertEqual(buyer.get(f"/s/{pid2}?order=ord_1").location, "https://me.com/thanks")
        buyer.get(f"/s/{pid2}?order=ord_1")
        saas.app.test_client().get(f"/s/{pid}")  # someone who never tapped a DM link
        self.assertEqual(buyer.get("/s/ffffffffffff").status_code, 404)
        self.login()
        s = self.c.get("/api/sales").get_json()
        self.assertEqual((s["sales"], s["revenue"]), (3, 149 + 999 + 149))
        self.assertEqual(s["by_rule"]["kw:GUIDE"], {"sales": 2, "revenue": 1148, "link_clicks": 1})
        self.assertEqual(s["daily"][-1]["revenue"], 1297)
        self.assertEqual(s["recent"][0]["key"], "")
        self.assertEqual(self.c.get("/api/rules/kw:GUIDE/insights").get_json()["last30"]["revenue"], 1148)
        # UTM off: links go out as they are; existing utm tags are never touched
        self.c.put("/api/utm", json={"on": False})
        self.assertEqual(saas.app.test_client().get(f"/l/{code}").location, "https://shop.com/p")
        self.assertEqual(engine.with_utm("https://a.com/?utm_source=yt", "x"), "https://a.com/?utm_source=yt")
        self.assertEqual(engine.campaign_of("18001234567890", {}), "reel-567890")
        self.c.delete(f"/api/products/{pid}", json={})
        self.assertEqual(saas.app.test_client().get(f"/s/{pid}").status_code, 404)
        self.assertEqual(self.c.get("/app/sales").status_code, 200)

    def test_health_alerts(self):
        import push
        self.login()
        notes = []
        with mock.patch.object(push, "notify", lambda acc, title, body, url="/app": notes.append(title) or 1):
            acc = store.load_account("1789")
            store.redis("DEL", store.account_key("1789", "counts"))
            self.put_rule("kw:A", keywords=["A"], require_follow=False, comment_reply="", dm="hi")
            acc["dm_limit"] = 5
            store.save_account(acc)
            for i in range(5):
                self.hook(dm("A", sender=f"6{i}", mid=f"h{i}"))
            self.assertEqual([n for n in notes if "DM" in n], ["80% of your DMs used ⚠️", "Monthly DM limit reached ⛔"])
            notes.clear()
            self.ig.dead = True
            store.redis("DEL", store.account_key("1789", "counts"))
            self.hook(dm("A", sender="69", mid="h9"))
            store.redis("DEL", store.account_key("1789", "counts"))
            self.hook(dm("A", sender="70", mid="h10"))
            self.assertEqual(notes.count("Instagram logged you out ⚠️"), 1)  # once a day, not on every failure
            self.ig.dead = False
            store.redis("DEL", store.account_key("1789", "token_dead"))
            notes.clear()
            acc = store.load_account("1789")
            for i in range(engine.REFUSED_ALERT):
                engine.add_retry(acc, f"cm{i}", {"key": "kw:A"})
            self.assertEqual(notes, ["Instagram is refusing DMs"])
            notes.clear()
            self.c.put("/api/notifications/prefs", json={"health": False, "lead": True, "handoff": True, "sale": True})
            store.redis("DEL", f"s:seen:1789:alert:refused")
            engine.add_retry(store.load_account("1789"), "cmx", {"key": "kw:A"})
            self.assertEqual(notes, [])
        self.assertIn("health", [a["action"] for a in self.c.get("/api/activity?all=1").get_json()])

    def test_pages_render(self):
        for path in ("/", "/privacy", "/terms", "/data-deletion"):
            self.assertEqual(self.c.get(path).status_code, 200, path)
        self.login()
        home = self.c.get("/")  # logged in: the landing page still shows, with a way back to the dashboard
        self.assertEqual(home.status_code, 200)
        self.assertIn('href="/app">Open dashboard', home.get_data(as_text=True))
        self.assertIn("@creator", self.c.get("/app").get_data(as_text=True))

    def course_setup(self):
        import shop
        import users
        self.login()
        self.enterContext(mock.patch.dict(os.environ, RAZORPAY_KEY_ID="rzp_test_k", RAZORPAY_KEY_SECRET="sek", RAZORPAY_WEBHOOK_SECRET="whs"))
        u = users.by_email("om@example.com")
        u["payout"] = {"account_id": "acc_L1", "product_id": "p", "status": "activated"}
        users.save(u)
        self.rzp_calls, self.mails = [], []

        def rzp(method, url, json=None, timeout=None, auth=None):
            self.rzp_calls.append((method, url.replace(shop.API, ""), json))
            return Resp({"id": f"order_C{len(self.rzp_calls)}"})
        self.enterContext(mock.patch.object(shop.requests, "request", rzp))
        self.enterContext(mock.patch.object(shop, "_mail", lambda to, subject, html, reply_to=None: self.mails.append((to, subject, html)) or True))
        cid = self.c.post("/api/courses", json={"title": "Reels Mastery"}).get_json()["id"]
        return cid

    def course_body(self, cid, **over):
        c = self.c.get(f"/api/courses/{cid}").get_json()["course"]
        c.update(status="published", price=999, slug="reels", desc="Learn **reels**.", benefits=["Hook formulas"],
                 faqs=[{"q": "Refunds?", "a": "7 days."}], show_enrolled=True,
                 modules=[{"id": "m1", "title": "Basics", "live": True, "unlock": "now", "lessons": [
                              {"id": "l1", "type": "video", "title": "Intro", "live": True, "free": True, "video": "https://youtu.be/abcdefgh123"},
                              {"id": "l2", "type": "quiz", "title": "Check", "live": True, "pass_pct": 50,
                               "questions": [{"q": "2+2?", "options": ["3", "4"], "answer": 1}, {"q": "Sky?", "options": ["blue", "green"], "answer": 0}]}]},
                          {"id": "m2", "title": "Advanced", "live": True, "unlock": "after_prev", "lessons": [
                              {"id": "l3", "type": "assignment", "title": "Make a reel", "live": True, "body": "Post one reel."},
                              {"id": "l4", "type": "text", "title": "Draft lesson", "live": False}]},
                          {"id": "m3", "title": "Bonus", "live": True, "unlock": "delay", "delay": 7, "lessons": [
                              {"id": "l5", "type": "text", "title": "Bonus tips", "live": True, "body": "Tips"}]}],
                 cert={"enabled": True, "signer": "Om"}, coupons=[{"code": "om10", "kind": "pct", "value": 10, "max": 5}])
        c.update(over)
        r = self.c.put(f"/api/courses/{cid}", json=c)
        self.assertEqual(r.status_code, 200, r.get_json())
        return r.get_json()["course"]

    def test_course_editor_and_sales_page(self):
        cid = self.course_setup()
        self.assertEqual(self.c.get("/app/courses").status_code, 200)
        self.assertIn("Edit course", self.c.get(f"/app/courses/{cid}").get_data(as_text=True))
        anon = saas.app.test_client()
        c = self.c.get(f"/api/courses/{cid}").get_json()["course"]
        self.assertEqual(c["status"], "draft")
        self.assertEqual(anon.get(f"/creator/c/{c['slug']}").status_code, 404)  # drafts are private
        self.assertEqual(self.c.get(f"/creator/c/{c['slug']}").status_code, 200)  # but the owner sees them
        # validation
        bad = self.c.put(f"/api/courses/{cid}", json={**c, "discount": True, "price": 500, "sale_price": 600}).get_json()
        self.assertIn("lower", bad["error"])
        c = self.course_body(cid, discount=True, sale_price=499)
        self.assertEqual((c["slug"], c["price"], c["sale_price"]), ("reels", 999, 499))
        page = anon.get("/creator/c/reels").get_data(as_text=True)
        for s in ("Reels Mastery", "₹499", "₹999", "50% off", "Hook formulas", "Refunds?", "Free preview", "Certificate", "<b>reels</b>"):
            self.assertIn(s, page)
        self.assertNotIn("Draft lesson", page)
        # free preview lesson is public, paid ones are not
        self.assertIn("youtube-nocookie.com/embed/abcdefgh123", anon.get("/creator/c/reels/preview/l1").get_data(as_text=True))
        self.assertEqual(anon.get("/creator/c/reels/preview/l2").status_code, 404)
        self.assertEqual(anon.get(f"/learn/{cid}/l2").status_code, 302)
        # owner preview of the student views
        self.assertIn("Preview", self.c.get(f"/learn/{cid}").get_data(as_text=True))
        self.assertIn("Lesson 2/2", self.c.get(f"/learn/{cid}/l2").get_data(as_text=True))
        rows = self.c.get("/api/courses").get_json()
        self.assertEqual(rows["courses"][0]["lessons"], 4)
        self.assertGreaterEqual(rows["courses"][0]["views"], 1)  # visitors count, the owner doesn't
        # signed-out visitors can't use the editor API
        self.assertIn(anon.get(f"/api/courses/{cid}").status_code, (302, 401, 403, 404))

    def test_course_paid_enrol_and_learning(self):
        import courses
        cid = self.course_setup()
        self.course_body(cid)
        anon = saas.app.test_client()
        self.assertIn("coupon", anon.post("/creator/c/reels/order", json={"name": "Fan", "email": "fan@x.co", "coupon": "NOPE"}).get_json()["error"])
        o = anon.post("/creator/c/reels/order", json={"name": "Fan", "email": "Fan@X.co", "coupon": "om10"}).get_json()
        self.assertEqual(o["amount"], 89900)  # 10% off ₹999
        body = [x for x in self.rzp_calls if x[1] == "/v1/orders"][-1][2]
        self.assertEqual(body["transfers"][0]["account"], "acc_L1")
        self.assertLess(body["transfers"][0]["amount"], 89900)
        sig = hmac.new(b"sek", f"{o['order_id']}|pay_c1".encode(), hashlib.sha256).hexdigest()
        self.assertEqual(anon.post("/creator/c/reels/paid", json={"order_id": o["order_id"], "payment_id": "pay_c1", "signature": "x"}).status_code, 400)
        nxt = anon.post("/creator/c/reels/paid", json={"order_id": o["order_id"], "payment_id": "pay_c1", "signature": sig}).get_json()["next"]
        self.assertEqual(nxt, f"/learn/{cid}")
        # the webhook for the same payment doesn't enrol twice
        wb = json.dumps({"event": "payment.captured", "payload": {"payment": {"entity": {"id": "pay_c1", "order_id": o["order_id"], "status": "captured", "amount": 89900}}}}).encode()
        anon.post("/billing/webhook", data=wb, headers={"X-Razorpay-Signature": hmac.new(b"whs", wb, hashlib.sha256).hexdigest()})
        c = courses.get(cid)
        self.assertEqual((c["sales"], c["revenue"], c["coupons"][0]["used"]), (1, 899, 1))
        self.assertTrue(any("You're in" in m[1] and "/learn/in/" in m[2] for m in self.mails))
        dash = anon.get(nxt).get_data(as_text=True)
        self.assertIn("Start course", dash)
        self.assertIn("Finish the previous module", dash)  # after_prev drip
        self.assertIn("Unlocks on", dash)  # delay drip
        self.assertEqual(anon.get(f"/learn/{cid}/l3").status_code, 302)  # locked
        self.assertEqual(anon.get(f"/learn/{cid}/l4").status_code, 404)  # draft
        self.assertIn("Mark as complete", anon.get(f"/learn/{cid}/l1").get_data(as_text=True))
        self.assertEqual(anon.post(f"/learn/{cid}/l1/done", json={}).get_json()["pct"], 25)
        # quiz: fail, then pass (passing completes it)
        self.assertFalse(anon.post(f"/learn/{cid}/l2/quiz", json={"answers": [0, 1]}).get_json()["result"]["passed"])
        r = anon.post(f"/learn/{cid}/l2/quiz", json={"answers": [1, 1]}).get_json()["result"]
        self.assertEqual((r["passed"], r["score"]), (True, 50))
        self.assertEqual(anon.post(f"/learn/{cid}/l3/work", json={"text": ""}).status_code, 400)
        self.assertEqual(anon.get(f"/learn/{cid}/l3").status_code, 200)  # module 2 unlocked now
        anon.post(f"/learn/{cid}/l3/work", json={"text": "My reel", "link": "https://instagram.com/reel/x"})
        # creator reviews the assignment
        st = self.c.get(f"/api/courses/{cid}/students").get_json()["students"]
        self.assertEqual((st[0]["email"], st[0]["work"][0]["text"]), ("fan@x.co", "My reel"))
        self.assertEqual(self.c.put(f"/api/courses/{cid}/review", json={"email": "fan@x.co", "lesson": "l3", "grade": "A", "feedback": "Great"}).status_code, 200)
        self.assertIn("Great", anon.get(f"/learn/{cid}/l3").get_data(as_text=True))
        self.assertIn("fan@x.co", self.c.get(f"/api/courses/{cid}/students.csv").get_data(as_text=True))
        # bonus module unlocks after 7 days; then 100% gives the certificate
        e = courses.enrollment(cid, "fan@x.co")
        e["at"] -= 8 * 86400
        store.set_json(f"s:enr:{cid}:fan@x.co", e)
        self.assertEqual(anon.post(f"/learn/{cid}/l5/done", json={}).get_json()["pct"], 100)
        dash = anon.get(f"/learn/{cid}").get_data(as_text=True)
        cert = re.search(r'/cert/([0-9a-f]{12})', dash).group(1)
        page = saas.app.test_client().get(f"/cert/{cert}").get_data(as_text=True)
        self.assertIn("Fan", page)
        self.assertIn("Reels Mastery", page)
        self.assertEqual(saas.app.test_client().get("/cert/000000000000").status_code, 404)
        # my courses list
        self.assertIn("100% complete", anon.get("/learn").get_data(as_text=True))

    def test_course_free_signin_and_validity(self):
        import courses
        cid = self.course_setup()
        self.course_body(cid, price_mode="pwyw", min_price=0, validity={"kind": "limited", "months": 1}, ask_phone=True)
        anon = saas.app.test_client()
        self.assertIn("mobile", anon.post("/creator/c/reels/order", json={"name": "A", "email": "a@x.co"}).get_json()["error"])
        r = anon.post("/creator/c/reels/order", json={"name": "A", "email": "a@x.co", "phone": "9876543210", "amount": 0}).get_json()
        self.assertEqual((r["free"], r["next"]), (True, f"/learn/{cid}"))
        self.assertEqual(anon.get(f"/learn/{cid}").status_code, 200)
        self.assertEqual(courses.enrollment(cid, "a@x.co")["phone"], "9876543210")
        # pay-what-you-want with an amount goes to Razorpay
        self.assertEqual(anon.post("/creator/c/reels/order", json={"name": "B", "email": "b@x.co", "phone": "9876543210", "amount": 200}).get_json()["amount"], 20000)
        # sign in on another device with an email code, and with the magic link
        other = saas.app.test_client()
        self.assertIn("Send code", other.get("/learn").get_data(as_text=True))
        other.post("/learn/start", json={"email": "a@x.co"})
        self.assertEqual(other.post("/learn/verify", json={"email": "a@x.co", "code": self.codes["a@x.co"]}).get_json()["next"], "/learn")
        self.assertIn("Reels Mastery", other.get("/learn").get_data(as_text=True))
        third = saas.app.test_client()
        tok = courses.magic_link("a@x.co", cid).rsplit("/", 1)[1]
        self.assertTrue(third.get(f"/learn/in/{tok}").location.endswith(f"/learn/{cid}"))
        self.assertEqual(third.get("/learn/in/bad-token-bad-token-bad").location, "/learn")
        # access ends after the validity period
        e = courses.enrollment(cid, "a@x.co")
        e["until"] = int(time.time()) - 10
        store.set_json(f"s:enr:{cid}:a@x.co", e)
        self.assertIn("has ended", anon.get(f"/learn/{cid}").get_data(as_text=True))
        self.assertEqual(anon.get(f"/learn/{cid}/l1").status_code, 302)
        self.assertEqual(anon.post(f"/learn/{cid}/l1/done", json={}).status_code, 403)
        # unpublishing stops new sales; deleting keeps students' access
        self.course_body(cid, status="unpublished")
        self.assertEqual(saas.app.test_client().get("/creator/c/reels").status_code, 404)
        self.assertEqual(self.c.delete(f"/api/courses/{cid}", json={}).status_code, 200)
        self.assertEqual(self.c.get("/api/courses").get_json()["courses"], [])

    def test_course_live_sessions_and_embeds(self):
        import courses
        self.assertEqual(courses.embed("https://www.youtube.com/watch?v=dQw4w9WgXcQ"), "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?rel=0&modestbranding=1")
        self.assertEqual(courses.embed("https://vimeo.com/123456"), "https://player.vimeo.com/video/123456")
        self.assertEqual(courses.embed("https://www.loom.com/share/abc123"), "https://www.loom.com/embed/abc123")
        self.assertEqual(courses.embed("https://evil.com/x"), "")
        cid = self.course_setup()
        today = time.strftime("%Y-%m-%d", time.gmtime(time.time() + saas.shop.IST))
        later = time.strftime("%Y-%m-%d", time.gmtime(time.time() + 20 * 86400 + saas.shop.IST))
        self.assertIn("days", self.c.put(f"/api/courses/{cid}", json={**self.c.get(f"/api/courses/{cid}").get_json()["course"],
                                                                     "live": {"enabled": True}}).get_json().get("error", "days"))
        c = self.course_body(cid, live={"enabled": True, "link": "https://zoom.us/j/1", "days": [0, 1, 2, 3, 4, 5, 6], "start": "20:00", "end": "21:00",
                                        "from": today, "to": later, "title": "Weekly Q&A"})
        s = courses.sessions(c)
        self.assertEqual(len(s), 21)
        self.assertIn("Weekly Q&amp;A", self.c.get(f"/learn/{cid}").get_data(as_text=True))
        self.assertIn("21 live classes", saas.app.test_client().get("/creator/c/reels").get_data(as_text=True))

    def test_course_gst_bump_usd_and_extras(self):
        import courses
        import shop
        cid = self.course_setup()
        other = self.c.post("/api/courses", json={"title": "Hook Vault"}).get_json()["id"]
        self.assertIn("GSTIN", self.c.put(f"/api/courses/{cid}", json={**self.c.get(f"/api/courses/{cid}").get_json()["course"],
                                                                      "gst": {"enabled": True, "gstin": "BAD"}}).get_json()["error"])
        self.assertIn("Measurement", self.c.put(f"/api/courses/{cid}", json={**self.c.get(f"/api/courses/{cid}").get_json()["course"], "ga": "UA-1"}).get_json()["error"])
        opts = self.c.get(f"/api/courses/{cid}").get_json()["bump_options"]
        self.assertEqual([o["id"] for o in opts], [other])
        self.course_body(cid, gst={"enabled": True, "pct": 18, "gstin": "07ABCDE1234F1Z5", "name": "Om Media"},
                         bump={"enabled": True, "kind": "course", "id": other, "price": 199, "desc": "100 hooks"},
                         intl={"enabled": True, "usd": 29, "usd_sale": 19}, ga="g-ab12cd34ef",
                         community={"enabled": True, "kind": "whatsapp", "link": "https://chat.whatsapp.com/xyz"},
                         emails=[{"days": 1, "subject": "Day 1 {name}", "body": "Hi {name}, start {course}."},
                                 {"days": 5, "subject": "Stuck?", "body": "Finish it!", "unfinished": True}])
        anon = saas.app.test_client()
        page = anon.get("/creator/c/reels").get_data(as_text=True)
        for t in ("+ 18% GST", "Yes, add Hook Vault for ₹199", "$19", "G-AB12CD34EF", "Private WhatsApp group", 'data-cur="INR"'):
            self.assertIn(t, page)
        self.assertNotIn("chat.whatsapp.com", page)  # the invite is for students only
        self.assertIn('data-cur="USD"', anon.get("/creator/c/reels", headers={"x-vercel-ip-country": "US"}).get_data(as_text=True))
        # ₹999 + 18% GST + ₹199 bump, coupon 10% on the course only
        o = anon.post("/creator/c/reels/order", json={"name": "Fan", "email": "fan@x.co", "coupon": "OM10", "bump": True}).get_json()
        self.assertEqual(o["amount"], (899 + 162 + 199) * 100)
        sig = hmac.new(b"sek", f"{o['order_id']}|pay_g1".encode(), hashlib.sha256).hexdigest()
        anon.post("/creator/c/reels/paid", json={"order_id": o["order_id"], "payment_id": "pay_g1", "signature": sig})
        self.assertTrue(courses.enrollment(other, "fan@x.co"))  # the bump course
        self.assertEqual((courses.get(cid)["revenue"], courses.get(other)["revenue"]), (899 + 162, 199))
        welcome = [m[2] for m in self.mails if "Reels Mastery" in m[1]][0]
        for t in ("GST 18%", "₹162", "Hook Vault", "₹1,260", "07ABCDE1234F1Z5", "chat.whatsapp.com/xyz"):
            self.assertIn(t, welcome)
        self.assertIn("Join the WhatsApp group", anon.get(f"/learn/{cid}").get_data(as_text=True))
        # dollars: no GST, no bump, no transfer in the order; the share is transferred after capture
        o2 = anon.post("/creator/c/reels/order", json={"name": "Amy", "email": "amy@x.co", "currency": "USD", "bump": True}).get_json()
        self.assertEqual((o2["amount"], o2["currency"]), (1900, "USD"))
        body = [x for x in self.rzp_calls if x[1] == "/v1/orders"][-1][2]
        self.assertNotIn("transfers", body)
        n = len(self.rzp_calls)
        wb = json.dumps({"event": "payment.captured", "payload": {"payment": {"entity": {"id": "pay_u1", "order_id": o2["order_id"], "status": "captured", "amount": 1900}}}}).encode()
        anon.post("/billing/webhook", data=wb, headers={"X-Razorpay-Signature": hmac.new(b"whs", wb, hashlib.sha256).hexdigest()})
        self.assertTrue(courses.enrollment(cid, "amy@x.co"))
        tr = [x for x in self.rzp_calls[n:] if x[1] == "/v1/payments/pay_u1/transfers"]
        self.assertEqual(tr[0][2]["transfers"][0]["currency"], "INR")
        self.assertEqual(store.get_json(f"s:shoporder:{o2['order_id']}")["transfer"], "done")
        # automatic emails: day 1 once; day 5 only while unfinished; never weeks later
        e = courses.enrollment(cid, "fan@x.co")
        self.mails.clear()
        self.assertEqual(courses.send_sequences(now=e["at"] + 3600), 0)
        self.assertEqual(courses.send_sequences(now=e["at"] + 86400 + 60), 2)  # fan and amy
        self.assertEqual(courses.send_sequences(now=e["at"] + 86400 + 120), 0)
        self.assertIn("Day 1 Fan", [m[1] for m in self.mails])
        self.assertIn("Hi Fan, start Reels Mastery.", self.mails[0][2] + self.mails[1][2])
        self.assertEqual(courses.send_sequences(now=e["at"] + 40 * 86400), 0)

    def test_course_bump_product_and_video_upload(self):
        import courses
        import files
        import videos
        cid = self.course_setup()
        self.enterContext(mock.patch.dict(os.environ, BLOB_READ_WRITE_TOKEN="vercel_blob_rw_store9_secret"))
        blobs = {}

        def put(url, params=None, data=None, headers=None, timeout=None):
            blobs[params["pathname"]] = data
            return Resp({"url": f"https://store9.private.blob.vercel-storage.com/{params['pathname']}", "pathname": params["pathname"]})

        def get(url, headers=None, timeout=None):
            data = blobs.get(url.split(".com/", 1)[1], b"")
            m = re.match(r"bytes=(\d+)-(\d+)", (headers or {}).get("Range", ""))
            r = Resp({}, 206 if m else 200)
            r.content, r.headers = (data[int(m.group(1)):int(m.group(2)) + 1] if m else data), {"content-type": "application/octet-stream"}
            return r
        self.enterContext(mock.patch.object(files.requests, "put", put))
        self.enterContext(mock.patch.object(files.requests, "get", get))
        self.enterContext(mock.patch.object(videos.requests, "put", put))
        self.enterContext(mock.patch.object(videos.requests, "get", get))
        self.enterContext(mock.patch.object(videos, "CHUNK", 10))
        # a 25-byte "video" in pieces of 10
        self.assertIn("MP4", self.c.post("/api/courses/video", json={"name": "a.exe", "size": 5}).get_json()["error"])
        v = self.c.post("/api/courses/video", json={"name": "Lesson 1.mp4", "size": 25}).get_json()
        self.assertEqual(v["parts"], 3)
        data = bytes(range(25))
        self.assertEqual(self.c.post(f"/api/courses/video/{v['id']}/done", json={}).status_code, 400)  # pieces missing
        for n in range(3):
            r = self.c.put(f"/api/courses/video/{v['id']}/{n}", data=data[n * 10:(n + 1) * 10], headers={"X-Upload": "1"},
                           content_type="application/octet-stream")
            self.assertEqual(r.status_code, 200, r.get_json())
        self.assertEqual(self.c.put(f"/api/courses/video/{v['id']}/0", data=b"x", content_type="application/octet-stream").status_code, 415)
        self.assertEqual(self.c.post(f"/api/courses/video/{v['id']}/done", json={}).get_json()["name"], "Lesson-1.mp4")
        # a file product as the bump offer
        prod = self.c.put("/api/shop/products", json={"type": "locked", "title": "Hook list", "price": 99, "content": "Hook #1: stop scrolling"}).get_json()["product"]
        c = self.course_body(cid, bump={"enabled": True, "kind": "product", "id": prod["id"], "price": 49})
        c["modules"][0]["lessons"][0].update(video_file=v["id"], video_name="Lesson-1.mp4")
        self.c.put(f"/api/courses/{cid}", json=c)
        anon = saas.app.test_client()
        # free preview lesson streams the uploaded video in pieces
        self.assertIn(f"/learn/{cid}/l1/video", anon.get("/creator/c/reels/preview/l1").get_data(as_text=True))
        r = anon.get(f"/learn/{cid}/l1/video", headers={"Range": "bytes=0-"})
        self.assertEqual((r.status_code, r.data, r.headers["Content-Range"]), (206, data[:10], "bytes 0-9/25"))
        r = anon.get(f"/learn/{cid}/l1/video", headers={"Range": "bytes=12-30"})
        self.assertEqual((r.data, r.headers["Content-Range"]), (data[12:20], "bytes 12-19/25"))
        self.assertEqual(anon.get(f"/learn/{cid}/l1/video", headers={"Range": "bytes=99-"}).status_code, 416)
        self.assertEqual(anon.get(f"/learn/{cid}/l2/video").status_code, 404)  # paid lesson, not enrolled
        o = anon.post("/creator/c/reels/order", json={"name": "Fan", "email": "fan@x.co", "bump": True}).get_json()
        self.assertEqual(o["amount"], (999 + 49) * 100)
        sig = hmac.new(b"sek", f"{o['order_id']}|pay_b1".encode(), hashlib.sha256).hexdigest()
        anon.post("/creator/c/reels/paid", json={"order_id": o["order_id"], "payment_id": "pay_b1", "signature": sig})
        self.assertTrue(any("Hook list" in m[1] for m in self.mails))  # the product's access email
        self.assertEqual(self.c.get("/api/shop").get_json()["products"][0]["sales"], 1)

    def test_batch_a_devices_menus_assessments_feedback(self):
        import courses
        import shop
        cid = self.course_setup()
        # signed-in devices: a second sign-in shows up, can be signed out from here, and loses access at once
        other = saas.app.test_client()
        self.signin(other)
        devs = self.c.get("/api/security").get_json()["devices"]
        self.assertEqual((len(devs), sum(d["this"] for d in devs)), (2, 1))
        mine = next(d for d in devs if d["this"])
        self.assertEqual(self.c.post("/api/security/signout", json={"sid": mine["sid"]}).status_code, 400)
        theirs = next(d for d in devs if not d["this"])
        self.c.post("/api/security/signout", json={"sid": theirs["sid"]})
        self.assertEqual(other.get("/api/me").status_code, 401)
        self.assertEqual(self.c.get("/api/me").status_code, 200)
        third = saas.app.test_client()
        self.signin(third)
        self.assertEqual(self.c.post("/api/security/signout", json={"all": True}).get_json()["ended"], 1)
        self.assertEqual(third.get("/app/courses").status_code, 302)
        # course menu: duplicate (draft copy), pause payments, unpublish, add to link in bio
        self.course_body(cid, emails=[{"days": 1, "subject": "Hi", "body": "Hello"}])
        dup = self.c.post(f"/api/courses/{cid}/duplicate", json={}).get_json()["id"]
        d = courses.get(dup)
        self.assertEqual((d["status"], d["title"], d.get("sales", 0), len(d["modules"])), ("draft", "Reels Mastery (copy)", 0, 3))
        self.assertNotEqual(d["slug"], "reels")
        self.c.put(f"/api/courses/{cid}/flags", json={"paused": True})
        anon = saas.app.test_client()
        self.assertIn("Enrolment is paused", anon.get("/creator/c/reels").get_data(as_text=True))
        self.assertIn("paused", anon.post("/creator/c/reels/order", json={"name": "A", "email": "a@x.co"}).get_json()["error"])
        self.c.put(f"/api/courses/{cid}/flags", json={"paused": False, "status": "unpublished"})
        self.assertEqual(anon.get("/creator/c/reels").status_code, 404)
        url = self.c.get("/api/courses").get_json()["courses"][-1]["url"]
        self.assertTrue(self.c.post("/api/page/add", json={"title": "Reels Mastery", "url": url, "price": "₹999"}).get_json()["added"])
        self.assertTrue(self.c.post("/api/page/add", json={"title": "x", "url": url}).get_json()["already"])
        self.assertEqual(self.c.post("/api/page/add", json={"title": "x", "url": "https://evil.com/x"}).status_code, 400)
        self.assertIn(url, json.dumps(self.c.get("/api/page").get_json()["page"]))
        # product duplicate is hidden until switched on
        prod = self.c.put("/api/shop/products", json={"type": "locked", "title": "VIP", "price": 49, "content": "secret"}).get_json()["product"]
        cp = self.c.post(f"/api/shop/products/{prod['id']}/duplicate", json={}).get_json()["product"]
        self.assertEqual((cp["title"], cp["enabled"], cp["sales"]), ("VIP (copy)", False, 0))
        self.assertEqual(len(self.c.get("/api/shop").get_json()["products"]), 2)
        # assessments across courses
        self.c.put(f"/api/courses/{cid}/flags", json={"status": "published"})
        courses.enroll({"id": "free_1", "course": cid, "email": "s@x.co", "name": "Sam", "price": 0})
        c = courses.get(cid)
        courses.mark(c, "s@x.co", "l1")
        ls = {l["id"]: l for _, l in courses.lessons(c)}
        courses.grade_quiz(c, "s@x.co", ls["l2"], [1, 0])
        courses.submit_work(c, "s@x.co", ls["l3"], "My answer", "")
        a = self.c.get("/api/courses/assessments").get_json()
        self.assertEqual((a["work"][0]["text"], a["work"][0]["title"], a["quizzes"][0]["score"]), ("My answer", "Make a reel", 100))
        self.assertIn("Assessments", self.c.get("/app/courses/assessments").get_data(as_text=True))
        # feature requests reach the owner page
        self.assertEqual(self.c.post("/api/feedback", json={"text": "hi"}).status_code, 400)
        self.assertEqual(self.c.post("/api/feedback", json={"kind": "feature", "text": "Please add Telegram memberships"}).status_code, 200)
        with mock.patch.object(saas, "OWNER_PASSWORD", "pw"):
            page = self.c.get("/owner", headers={"Authorization": "Basic " + base64.b64encode(b"o:pw").decode()}).get_data(as_text=True)
        self.assertIn("Please add Telegram memberships", page)
        # refer & earn: windows and people
        r = self.c.get("/api/refer").get_json()
        self.assertEqual((r["earned_today"], r["earned_week"], r["people"]), (0, 0, []))

    def test_batch_b_leads_carts_payments(self):
        import courses
        import leads
        import shop
        cid = self.course_setup()
        self.course_body(cid, ask_phone=True)
        acc = store.load_account("1789")
        anon = saas.app.test_client()
        # an Instagram contact (follower) and a link-page subscriber
        store.touch_contact("1789", "fan_one", "11", keyword="REELS", followed=True)
        store.touch_contact("1789", "", "web:sub@x.co", source="bio_page", email="sub@x.co")
        # a buyer (paid) and an abandoned checkout
        o = anon.post("/creator/c/reels/order", json={"name": "Buyer B", "email": "buy@x.co", "phone": "9876543210"}).get_json()
        sig = hmac.new(b"sek", f"{o['order_id']}|pay_l1".encode(), hashlib.sha256).hexdigest()
        anon.post("/creator/c/reels/paid", json={"order_id": o["order_id"], "payment_id": "pay_l1", "signature": sig})
        o2 = anon.post("/creator/c/reels/order", json={"name": "Cart C", "email": "cart@x.co", "phone": "9123456780"}).get_json()
        self.assertEqual(self.c.get("/api/leads?segment=carts").get_json()["total"], 0)  # too fresh to count
        rec = store.get_json(f"s:shoporder:{o2['order_id']}")
        rec["created"] -= 3600
        store.set_json(f"s:shoporder:{o2['order_id']}", rec)
        d = self.c.get("/api/leads").get_json()
        self.assertEqual({k: d["counts"][k] for k in ("all", "customers", "instagram", "followers", "subscribers", "carts")},
                         {"all": 4, "customers": 1, "instagram": 1, "followers": 1, "subscribers": 2, "carts": 1})
        b = next(p for p in d["leads"] if p["email"] == "buy@x.co")
        self.assertEqual((b["spent"], b["phone"], b["access"][0]["title"], sorted(b["sources"])), (999, "9876543210", "Reels Mastery", ["buyer", "student"]))
        self.assertEqual([p["email"] for p in self.c.get("/api/leads?segment=customers&min_spent=500").get_json()["leads"]], ["buy@x.co"])
        self.assertEqual(self.c.get("/api/leads?min_spent=5000").get_json()["total"], 0)
        self.assertEqual(self.c.get("/api/leads?q=fan_one").get_json()["leads"][0]["keyword"], "REELS")
        self.assertEqual(self.c.get("/api/leads?sort=spent").get_json()["leads"][0]["email"], "buy@x.co")
        # remind once
        cart = self.c.get("/api/leads?segment=carts").get_json()["leads"][0]["cart"]
        self.mails.clear()
        self.assertEqual(self.c.post(f"/api/leads/carts/{cart['id']}/remind", json={}).status_code, 200)
        self.assertTrue(any(m[0] == "cart@x.co" and "/creator/c/reels" in m[2] for m in self.mails))
        self.assertIn("already", self.c.post(f"/api/leads/carts/{cart['id']}/remind", json={}).get_json()["error"])
        # buying later clears the cart
        sig = hmac.new(b"sek", f"{o2['order_id']}|pay_l2".encode(), hashlib.sha256).hexdigest()
        anon.post("/creator/c/reels/paid", json={"order_id": o2["order_id"], "payment_id": "pay_l2", "signature": sig})
        self.assertEqual(self.c.get("/api/leads").get_json()["counts"]["carts"], 0)
        # CSV is formula-safe
        store.touch_contact("1789", "", "web:=x@x.co", source="bio_page", email="=cmd@x.co")
        self.assertIn("'=cmd@x.co", self.c.get("/api/leads.csv").get_data(as_text=True))
        # payments: earnings, period, product filter, payouts status
        p = self.c.get("/api/payments?period=7").get_json()
        self.assertEqual((p["count"], p["gross"], len(p["series"])), (2, 1998, 7))
        self.assertGreater(p["earned"], 0)
        self.assertEqual(self.c.get("/api/payments?period=7&item=Nope").get_json()["count"], 0)
        self.assertEqual(self.c.get("/api/payments?period=custom&from=2020-01-01&to=2020-01-02").get_json()["count"], 0)
        self.assertIn("Reels Mastery", self.c.get("/api/payments.csv?period=life").get_data(as_text=True))

        def rzp(method, url, json=None, timeout=None, auth=None):
            return Resp({"items": [{"id": "trf_1", "status": "processed", "settlement_status": "settled", "recipient_settlement_id": "setl_1"}]})
        with mock.patch.object(shop.requests, "request", rzp):
            po = self.c.get("/api/payments/payouts").get_json()["payouts"]
        self.assertEqual([x["status"] for x in po], ["completed", "completed"])
        self.assertEqual(store.get_json(f"s:shoporder:{o['order_id']}")["payout_status"], "completed")
        self.assertIn("Payments", self.c.get("/app/payments").get_data(as_text=True))
        self.assertIn("Abandoned carts", self.c.get("/app/leads").get_data(as_text=True))

    def test_batch_c_agents_assistant_home(self):
        import agents
        import assistant
        self.login()

        def block(**kw):
            b = mock.Mock(**{k: v for k, v in kw.items() if k != "name"})
            if "name" in kw:
                b.name = kw["name"]
            return b

        class Seq:
            """Fake Claude: returns queued responses (text JSON for agents, tool calls for the assistant)."""
            def __init__(self):
                self.queue, self.requests = [], []
                self.messages, self.beta = self, self

            def create(self, **kw):
                self.requests.append(kw)
                item = self.queue.pop(0)
                if isinstance(item, dict):
                    return mock.Mock(stop_reason="end_turn", content=[block(type="text", text=json.dumps(item))])
                return mock.Mock(stop_reason="tool_use" if any(getattr(b, "type", "") == "tool_use" for b in item) else "end_turn", content=item)
        fake = Seq()
        self.enterContext(mock.patch.object(ai_agent, "client", lambda: fake))
        # agents run on DMs even with the AI DM agent off
        self.assertEqual(self.c.put("/api/agents", json={"lead": {"enabled": True, "hot": "asks price"},
                                                          "brand": {"enabled": True, "min_budget": 5000, "auto_ask": True}}).status_code, 200)
        fake.queue += [{"is_brand_offer": True, "brand": "Boat", "offer": "2 reels for earbuds", "budget": "", "deliverables": "2 reels",
                        "timeline": "Dec", "fit": "good", "why": "Tech audience", "missing": ["budget"]},
                       {"temperature": "warm", "interest": "collab", "reason": "brand", "name": "Riya", "next_step": "Check rates"}]
        self.hook(dm("Hi, we are Boat and want a paid collab with you"))
        reqs = self.c.get("/api/agents").get_json()
        self.assertEqual((reqs["brands"][0]["brand"], reqs["brands"][0]["fit"], reqs["brands"][0]["asked"]), ("Boat", "good", True))
        self.assertIn("budget", self.ig.messages()[-1]["message"]["text"])  # the automatic ask
        self.assertEqual(reqs["leads"][0]["temperature"], "warm")
        self.assertEqual(ai_agent.get_thread("1789", "88")["status"], "you")  # the AI DM agent stays out
        self.assertEqual(self.c.put("/api/agents/brands/88", json={"status": "interested"}).get_json()["request"]["status"], "interested")
        # a normal DM without brand words: only the lead qualifier (at most every 10 minutes per chat)
        n = len(fake.requests)
        self.hook(dm("price kya hai?"))
        self.assertEqual(len(fake.requests), n)
        # home: alerts and today
        h = self.c.get("/api/home").get_json()
        self.assertIn("today", h)
        self.assertTrue(isinstance(h["alerts"], list))
        # assistant: looks things up on its own, asks before changing anything
        self.put_rule("555")
        fake.queue += [[block(type="tool_use", id="t1", name="list_automations", input={})],
                       [block(type="text", text="You have 1 automation. Pausing it:"), block(type="tool_use", id="t2", name="set_automation_enabled",
                                                                                              input={"automation_id": "555", "enabled": False})]]
        r = self.c.post("/api/assistant", json={"text": "pause my reel automation"}).get_json()
        self.assertEqual(r["pending"]["name"], "set_automation_enabled")
        self.assertTrue(store.load_rules("1789")["reels"]["555"].get("enabled", True))  # not yet
        sent = fake.requests[-1]["messages"]
        self.assertTrue(any(isinstance(m["content"], list) and m["content"][0].get("type") == "tool_result" for m in sent))  # the lookup ran
        fake.queue += [[block(type="text", text="Done, it's paused.")]]
        r = self.c.post("/api/assistant/decide", json={"approve": True}).get_json()
        self.assertIsNone(r["pending"])
        self.assertFalse(store.load_rules("1789")["reels"]["555"]["enabled"])
        self.assertEqual([m["role"] for m in r["shown"]], ["you", "ai", "action", "ai"])
        # declining by writing something new
        fake.queue += [[block(type="tool_use", id="t3", name="delete_automation", input={"automation_id": "555"})], [block(type="text", text="OK")]]
        self.assertTrue(self.c.post("/api/assistant", json={"text": "delete it"}).get_json()["pending"]["destructive"])
        self.c.post("/api/assistant", json={"text": "actually no"})
        self.assertIn("555", store.load_rules("1789")["reels"])
        # daily limit
        store.redis("SET", f"s:asstuse:1789:{assistant._day()}", 999)
        self.assertIn("today", self.c.post("/api/assistant", json={"text": "hi"}).get_json()["error"])
        self.assertEqual(self.c.post("/api/assistant/reset", json={}).get_json()["shown"], [])
        self.assertIn("Lead Qualifier", self.c.get("/app/agents").get_data(as_text=True))
        self.assertIn("What should we work on", self.c.get("/app").get_data(as_text=True))



class CarouselTest(unittest.TestCase):
    """tools/carousels.py: every guide, comparison and feature becomes a postable carousel (no rendering here)."""

    @classmethod
    def setUpClass(cls):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
        import carousels
        cls.m = carousels
        cls.all = [(kind, slug, page, carousels.build(kind, slug, page)) for kind, slug, page in carousels.pages()]

    def test_every_page_gets_a_readable_carousel(self):
        import re
        import seo_content
        self.assertEqual(len(self.all), len(seo_content.GUIDES) + len(seo_content.COMPARE) + len(seo_content.FEATURES))
        for kind, slug, page, c in self.all:
            slides = c["slides"]
            self.assertTrue(6 <= len(slides) <= 8, (slug, len(slides)))
            self.assertEqual((slides[0]["kind"], slides[-1]["kind"]), ("hook", "cta"), slug)
            self.assertEqual(slides[-1]["keyword"], c["keyword"])
            source = json.dumps(page, ensure_ascii=False) + seo_content.CHECKED
            for i, s in enumerate(slides, 1):
                self.assertLessEqual(self.m.slide_words(s), 25, (slug, i))
                text = json.dumps(s, ensure_ascii=False)
                self.assertNotIn("{brand}", text)
                for num in re.findall(r"\d[\d,.]*\d|\d", " ".join(str(s.get(k, "")) for k in ("title", "accent", "sub", "body", "note", "cta"))):
                    self.assertIn(num, source, f"{slug} slide {i}: {num} is not in the page text")
                self.assertIn(f"{i}/{len(slides)}", self.m.slide_html(s, i, len(slides), ""))

    def test_keywords_and_automations_fit_the_rule_form(self):
        kws = [c["keyword"] for *_, c in self.all]
        self.assertEqual(len(kws), len(set(kws)), "comment keywords must be unique")
        for kind, slug, page, c in self.all:
            url = self.m.page_url(kind, slug, "https://replyinbox.in")
            a = self.m.automation(c, url)
            self.assertTrue(saas.valid_rule_key(a["key"]), a["key"])
            saved = saas.save_rule({"id": "carousel-test"}, a["key"], a["rule"])
            rule = saved["reels"][a["key"]]
            self.assertEqual({k: rule[k] for k in a["rule"]}, a["rule"], "save_rule must keep every field as written")
            self.assertEqual(rule["dm_button_url"], url)
            self.assertIn(url, rule["dm"])
            self.assertTrue(2 <= len(rule["comment_reply"].splitlines()) <= 3)
            self.assertEqual(rule["keywords"], [c["keyword"]])

    def test_caption(self):
        for kind, slug, page, c in self.all:
            text = self.m.caption_text(c, page)
            self.assertIn(f"Comment {c['keyword']}", text)
            tags = text.strip().splitlines()[-1].split()
            self.assertTrue(5 <= len(tags) <= 8 and all(t.startswith("#") for t in tags), (slug, tags))
            if kind == "compare":
                self.assertIn("checked", text)


class ComicTest(unittest.TestCase):
    """tools/comic.py: comic carousel specs and pose picking (no rendering here)."""

    def setUp(self):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
        import comic
        self.m = comic

    def test_sample_spec_is_valid(self):
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "comic")
        specs = [os.path.join(d, f) for d, _, fs in os.walk(root) for f in fs if f.endswith(".json") and f != "poses.json"]
        self.assertTrue(specs)
        for p in specs:
            spec = json.load(open(p))
            self.assertEqual(self.m.validate(spec), [], p)
            self.assertIn(f"Comment {spec['keyword']}", self.m.caption(spec))

    def test_comic_facts_come_from_the_guides(self):
        """Every number on a @replyinbox comic slide (except single-digit step numbers) is in the page it came from."""
        import glob
        import re
        import seo_content
        for p in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "comic", "replyinbox", "*.json")):
            spec = json.load(open(p))
            pages = {"guide": seo_content.GUIDES, "compare": seo_content.COMPARE, "feature": seo_content.FEATURES}
            src = json.dumps(pages[spec.get("kind", "guide")][spec["slug"]], ensure_ascii=False) + seo_content.CHECKED
            for k, s in enumerate(spec["slides"], 1):
                text = self.m.plain(" ".join([s.get("headline", ""), s.get("bubble", "")] + s.get("lines", []) + s.get("steps", [])
                                             + [" ".join(c) for c in s.get("chat", [])]))
                for n in re.findall(r"\d[\d,.]*\d|\d", text):
                    if len(n) > 1:
                        self.assertIn(n, src, f"{spec['slug']} slide {k}: {n}")

    def test_pose_picking_avoids_repeats_and_honours_override(self):
        index = {f"p{k}": {"src": "x", "emotion": "", "tags": [t]} for k, t in enumerate(["sad", "happy", "think"])}
        slides = [{"mood": ["happy"]}, {"mood": ["happy"]}, {"mood": ["think"]}, {"pose": "p1"}]
        poses = self.m.pick_poses(slides, index)
        self.assertEqual(poses[0], "p1")
        self.assertEqual(len(set(poses[:3])), 3)
        self.assertEqual(poses[3], "p1")


if __name__ == "__main__":
    unittest.main()
