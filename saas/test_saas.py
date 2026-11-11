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
        self.calls, self.follows, self.fail_dm, self.dead = [], True, False, False
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
            return Resp({"id": "asid9", "user_id": "1789", "username": "creator", "name": "C",
                         "profile_picture_url": "", "followers_count": 500})
        if url.endswith("/refresh_access_token"):
            return Resp({"access_token": "NEWER"})
        fields = (params or {}).get("fields", "")
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
