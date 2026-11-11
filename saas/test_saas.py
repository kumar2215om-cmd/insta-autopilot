"""Tests for the multi-account app, with Instagram mocked. Run: python3 -m unittest test_saas (in saas/)."""
import base64
import hashlib
import hmac
import json
import os
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


class Resp:
    def __init__(self, data, status=200):
        self.data, self.status_code = data, status
        self.ok = status < 400
        self.text = json.dumps(data)

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

    def post(self, url, params=None, json=None, data=None, timeout=None):
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
        self.c = saas.app.test_client()

    def login(self):
        r = self.c.get("/login")
        state = parse_qs(urlparse(r.location).query)["state"][0]
        r = self.c.get(f"/auth/callback?code=abc&state={state}")
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
        self.c.get("/login")
        r = self.c.get("/auth/callback?code=abc&state=wrong")
        self.assertIn("error=state", r.location)
        self.assertIsNone(store.load_account("1789"))

    def test_invite_only(self):
        with mock.patch.object(saas, "SIGNUPS", "invite"), mock.patch.object(saas, "INVITE_CODES", {"BETA"}):
            self.assertIn("error=invite", self.c.get("/login?invite=nope").location)
            self.assertIn("instagram.com/oauth", self.c.get("/login?invite=beta").location)

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
        self.assertEqual(call("get_account_summary", {})["structuredContent"]["account"], "creator")
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
        self.assertIn("mint", html)
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
        self.assertEqual((state["kind"], state["limit"], state["over"]), ("month", 1000, False))
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
        for text in ("₹299", "1,000 DMs every month", "25 AI replies", "AI DM agent", "Giveaway picker", "Team access"):
            self.assertIn(text, html)

    def test_referrals(self):
        self.login()  # @creator
        self.assertTrue(self.c.get("/api/referrals").get_json()["link"].endswith("/r/creator"))
        self.c.post("/logout")
        # a new creator follows the invite link and signs up
        self.ig.calls.clear()
        friend = {"id": "asid2", "user_id": "2002", "username": "friend.creates", "name": "F", "profile_picture_url": "", "followers_count": 10}
        self.ig.me = friend
        new = saas.app.test_client()
        new.get("/r/creator")
        self.assertIn("@creator invited you", new.get("/").get_data(as_text=True))
        r = new.get("/login")
        state = parse_qs(urlparse(r.location).query)["state"][0]
        new.get(f"/auth/callback?code=abc&state={state}")
        friend_acc, me = store.load_account("2002"), store.load_account("1789")
        self.assertTrue(store.is_pro(friend_acc) and store.is_pro(me))
        self.assertEqual(engine.monthly_limit(me), 0)
        self.assertEqual(friend_acc["referred_by"], "1789")
        self.assertEqual(me["referrals"][0]["username"], "friend.creates")
        # logging in again doesn't reward twice
        until = me["pro_until"]
        new.get("/r/creator")
        r = new.get("/login")
        new.get(f"/auth/callback?code=abc&state={parse_qs(urlparse(r.location).query)['state'][0]}")
        self.assertEqual(store.load_account("1789")["pro_until"], until)
        self.assertIn("Pro plan", new.get("/app").get_data(as_text=True))

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
        r = self.c.get("/login?add=1")
        self.c.get(f"/auth/callback?code=abc&state={parse_qs(urlparse(r.location).query)['state'][0]}")
        self.assertEqual(self.c.get("/api/me").get_json()["account"]["username"], "second.page")
        html = self.c.get("/app").get_data(as_text=True)
        self.assertIn('data-switch="1789"', html)
        self.assertEqual(self.c.post("/api/switch", json={"id": "1789"}).status_code, 200)
        self.assertEqual(self.c.get("/api/me").get_json()["account"]["username"], "creator")
        self.assertEqual(self.c.post("/api/switch", json={"id": "9999"}).status_code, 403)  # not logged in to it
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

    def test_pages_render(self):
        for path in ("/", "/privacy", "/terms", "/data-deletion"):
            self.assertEqual(self.c.get(path).status_code, 200, path)
        self.login()
        self.assertIn("@creator", self.c.get("/app").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
