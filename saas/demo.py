"""Demo mode: a sample creator account with made-up data, so ReplyInbox can be tried without an Instagram login.

The demo account never calls Instagram: engine.Instagram answers its requests from the samples below,
and DMs or replies "sent" from it go nowhere.
"""
import json
import time

import store

DEMO_ID = "17840000000000001"
USERNAME = "demo.creator"

REELS = [
    ("18000000000000001", "Comment PROMPTS and I'll DM you 39 AI video prompts 🎬", 30000, 842, 750, 150, 1),
    ("18000000000000002", "Claude se Instagram grow karo, comment GUIDE for the full setup", 49000, 311, 1225, 245, 2),
    ("18000000000000003", "ChatGPT ko Instagram se connect karo. Comment GPT", 4100, 161, 101, 6, 3),
    ("18000000000000004", "My desk setup tour 🖥️", 2100, 57, 52, 10, 5),
    ("18000000000000005", "5 free AI tools nobody talks about. Comment TOOLS", 12800, 402, 380, 90, 6),
]


def _media():
    now = time.time()
    return [{"id": rid, "caption": cap, "media_type": "VIDEO", "media_product_type": "REELS",
             "permalink": "https://www.instagram.com/", "thumbnail_url": "", "media_url": "",
             "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime(now - days * 86400)),
             "comments_count": comments, "like_count": comments * 3}
            for rid, cap, views, comments, saves, shares, days in REELS]


def ig_get(path, params):
    """Answers Instagram API reads for the demo account."""
    if path.endswith("/insights"):
        rid = path.split("/")[0]
        row = next((r for r in REELS if r[0] == rid), None)
        if not row:
            return {"data": []}
        _, _, views, _, saves, shares, _ = row
        return {"data": [{"name": n, "values": [{"value": v}]} for n, v in
                         (("views", views), ("reach", int(views * 0.7)), ("saved", saves), ("shares", shares))]}
    if path == "me/media":
        return {"data": _media()}
    if path == "me":
        return {"id": "demo", "user_id": DEMO_ID, "username": USERNAME, "name": "Demo Creator",
                "profile_picture_url": "", "followers_count": 15330, "media_count": 48}
    media = next((m for m in _media() if m["id"] == path), None)
    if media:
        return media
    return {"username": "fan.account", "is_user_follow_business": True}


def seed():
    """Creates (or resets) the demo account with sample automations, activity and numbers."""
    acc = {"id": DEMO_ID, "username": USERNAME, "name": "Demo Creator", "pic": "", "followers": 15330,
           "token": "demo", "token_at": int(time.time()), "created": int(time.time()), "paused": False, "demo": True,
           "auto_setup": {"enabled": True, "since": "2026-01-01T00:00:00+0000",
                          "template": {"comment_reply": "@{username} Check your DM 📩", "require_follow": True,
                                       "dm": "Here you go 🎁 https://example.com/free?k={keyword}"}},
           "apps": {"inbox": True, "links": True, "contacts": True, "report": True},
           "ai": {"enabled": True, "language": "match",
                  "about": "I make Hindi reels about AI tools for creators. Friendly, bhai-style tone.",
                  "faq": "Q: Payment kaise karu? A: Link pe UPI, card ya netbanking. Download turant milta hai.\n"
                         "Q: Beginners ke liye hai? A: Haan, har pack mein step-by-step guide hai."}}
    store.save_account(acc)
    store.redis("SET", f"s:user:{USERNAME}", DEMO_ID)
    store.save_rules(DEMO_ID, {"reels": {
        "18000000000000001": {"enabled": True, "keywords": ["PROMPTS"], "comment_reply": "@{username} Check your DM 📩",
                              "require_follow": True, "dm": "Here are your 39 prompts 🎁 https://example.com/prompts"},
        "18000000000000002": {"enabled": True, "keywords": ["GUIDE"], "auto": True, "comment_reply": "@{username} Sent 📥",
                              "require_follow": True, "dm": "Full setup guide 👉 https://example.com/guide",
                              "label": "Claude se Instagram grow karo"},
        "kw:AUDIT": {"enabled": True, "keywords": ["AUDIT"], "comments": True, "require_follow": False,
                     "comment_reply": "", "dm": "Send me your handle and I'll audit your page 🙌"},
    }})
    import ai_agent
    for t in ai_agent.threads(DEMO_ID):
        store.redis("DEL", store.account_key(DEMO_ID, f"chat:{t['igsid']}"))
    for key in ("activity", "counts", "autos", "contacts", "page", "threads"):
        store.redis("DEL", store.account_key(DEMO_ID, key))
    for mid, c in (("18000000000000001", {"keyword": 389, "dm": 352, "link": 301, "follow": 290}),
                   ("18000000000000002", {"keyword": 120, "dm": 118, "link": 96, "follow": 93})):
        store.redis("DEL", store.account_key(DEMO_ID, f"m:{mid}"))
        for field, n in c.items():
            store.media_count(DEMO_ID, mid, field, n)
    from engine import month
    for field, n in ((f"dms:{month()}", 412), ("dms", 1980), ("links_sent", 230), ("comment_replies", 398), ("gate_follows", 61)):
        store.count(DEMO_ID, field, n)
    store.log_auto(DEMO_ID, {"media_id": "18000000000000002", "keyword": "GUIDE", "label": "Claude se Instagram grow karo",
                             "at": int(time.time()) - 3600})
    for user, comment, action, status, detail in [
        ("rahul.creates", "PROMPTS 🔥", "comment_reply", "ok", ""),
        ("rahul.creates", "PROMPTS 🔥", "opening_dm", "ok", ""),
        ("priya.ai", "prompts pls", "opening_dm", "error", "400: Instagram refused to open a DM with this person right now (2534001)"),
        ("jay_kukadiya", "GET|18000000000000001", "follow_prompt", "ok", ""),
        ("jay_kukadiya", "FOLLOWED|18000000000000001", "dm", "ok", ""),
        ("techwithneha", "AUDIT", "dm_keyword", "ok", ""),
    ]:
        store.log_activity(DEMO_ID, "18000000000000001", user, comment, action, status, detail)
    now = int(time.time())
    for i, (user, kw, followed, email) in enumerate([
        ("rahul.creates", "PROMPTS", True, ""), ("priya.ai", "PROMPTS", False, ""), ("jay_kukadiya", "PROMPTS", True, "jay@example.com"),
        ("techwithneha", "AUDIT", True, ""), ("sana.creates", "GUIDE", True, "sana@example.com"), ("kunal.ai", "GUIDE", False, ""),
    ]):
        store.save_contact(DEMO_ID, {"username": user, "first_at": now - (i + 1) * 5400, "last_at": now - i * 3600,
                                     "keyword": kw, "followed": followed, "email": email, "interactions": 1 + i % 3})
    for igsid, user, chat, extra in [
        ("900001", "ankit.edits", [("fan", "Bhai ye prompt pack kitne ka hai?"),
                                   ("ai", "Abhi sirf ₹149 hai 🙌 Saare 39 packs, lifetime access. Yahan se le lo 👉 https://example.com/prompts"),
                                   ("fan", "UPI se ho jayega?"),
                                   ("ai", "Haan bilkul! Link pe UPI, card ya netbanking sab chalta hai. Download turant milta hai 😊")], {}),
        ("900002", "meera.designs", [("fan", "Hi! I run a skincare brand, want to collab on 2 reels. What are your rates?"),
                                     ("ai", "Thanks for your message! I'll get back to you personally soon 🙏")],
         {"status": "needs_you", "reason": "Brand collaboration request", "hold_sent": True,
          "suggestion": "Hi Meera! Thanks for reaching out 😊 Please share your brand page and what you have in mind, and I'll send my rates."}),
        ("900003", "rohit_9", [("fan", "Payment ho gaya but download link nahi aaya 😟")],
         {"status": "needs_you", "reason": "Payment problem", "unread": True,
          "suggestion": "Sorry for the trouble! Apna payment screenshot bhej do, main abhi link bhejta hoon 🙏"}),
        ("900004", "sana.creates", [("fan", "Guide mil gayi, thank you so much!! ❤️"),
                                    ("ai", "Bahut khushi hui 😊 Koi doubt ho to yahin pooch lena!"),
                                    ("you", "Aur haan, next reel mein part 2 aa raha hai 🔥")], {"status": "you"}),
    ]:
        for i, (role, text) in enumerate(chat):
            ai_agent.add_message(DEMO_ID, igsid, role, text, user)
        ai_agent.update_thread(DEMO_ID, igsid, **{"unread": False, **extra})
    store.count(DEMO_ID, f"ai:{ai_agent.month()}", 37)
    store.count(DEMO_ID, "ai_replies", 37)
    store.save_page(DEMO_ID, {
        "name": "Demo Creator", "bio": "AI tools and tips you can use today. New reel every day 👇", "theme": "violet",
        "socials": {"instagram": USERNAME, "youtube": "https://youtube.com", "email": "", "website": ""},
        "items": [
            {"id": "p1", "type": "product", "title": "39 AI Video Prompt Packs", "subtitle": "Prompts + step-by-step guide",
             "url": "https://example.com/prompts", "price": "₹149", "featured": True, "enabled": True},
            {"id": "l1", "type": "link", "title": "Free guides and kits", "subtitle": "62 free downloads",
             "url": "https://example.com/free", "price": "", "featured": False, "enabled": True},
            {"id": "l2", "type": "link", "title": "Watch my latest reel", "subtitle": "", "url": "https://www.instagram.com/",
             "price": "", "featured": False, "enabled": True},
        ]})
    return acc


def is_demo(acc):
    return bool(acc and acc.get("demo"))


def dumps(value):
    return json.dumps(value, ensure_ascii=False)
