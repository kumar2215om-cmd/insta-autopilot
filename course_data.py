"""Content for the public course sales page (/course), in English (the course itself is taught in Hinglish). Edit the text here; price + buy link are set in /links/edit."""

TITLE = "Grow on Instagram with Claude"
TITLE_HI = "Claude se Instagram grow karo"  # the course's name on SuperProfile and in the lessons
# {F} = live follower count from Instagram (e.g. "24K"); FOLLOWERS_FALLBACK is used if Instagram is unreachable.
FOLLOWERS_FALLBACK = "24K"
COVER = "free/course_en.jpg"
LANG_NOTE = "🗣️ Classes are taught in Hinglish (Hindi + English)"
# Home page card text.
TITLE_EN = TITLE
SUBTITLE_EN = ("The exact system I used to grow @aiwith.om from 0 to {F}: profile, content plan, reels made with Claude, "
               "a comment → DM machine and a weekly growth loop. Step by step.")
SUBTITLE = ("The exact system I used to grow @aiwith.om from 0 to {F} followers. Profile, content plan, reels made with Claude, "
            "a comment → DM machine and a weekly growth loop. Step by step, no jargon.")

STATS = [("8", "modules"), ("32", "lessons"), ("~4.5h", "video"), ("6", "bonuses")]

OUTCOMES = [
    ("🧠", "Claude = your strategist", "A Project that remembers your brand and gives you every plan as a clear table."),
    ("👤", "A profile that gets follows", "Niche, name field, bio, highlights and link in bio, all set up right."),
    ("📅", "A 30-day plan in 10 minutes", "Outlier research, hook lab and a content calendar, with copy-ready prompts."),
    ("🎬", "Reels without a camera", "Script → voiceover → edit. CapCut (no code) or Claude Code + Remotion."),
    ("💬", "Comment → DM machine", "A keyword on every reel, a free guide in the DM, and more followers."),
    ("📈", "Weekly growth loop", "Read your Insights, find out why a reel flopped, and fix one thing every week."),
]

MODULES = [
    ("Module 0", "Welcome", "Free preview", [
        "My journey: 0 → {F}", "Tools and costs", "Make Claude your \"brain\""]),
    ("Module 1", "Niche + profile that converts", None, [
        "Pick a niche you can make 100 reels about (free preview)", "Name field, bio, link", "Highlights that build trust", "Link in bio + freebies page"]),
    ("Module 2", "Content plan with Claude", None, [
        "Find outliers (patterns, not copies)", "30-day calendar in 10 minutes", "Hook lab", "A comment keyword on every reel"]),
    ("Module 3", "Reels with Claude", None, [
        "Scripts that finish in 30–45 seconds", "Voiceover", "Path A: no-code edit (CapCut)", "Path B: Claude Code + Remotion reel factory",
        "Brand look + quality checklist", "Cover + caption + hashtags"]),
    ("Module 4", "The comment → DM machine", None, [
        "How it works", "Setup with a tool (ManyChat or similar)", "Follow-gate the right way", "Safety: Instagram's rules",
        "(Advanced) Build your own automation"]),
    ("Module 5", "Freebies that people actually want", None, [
        "Lead magnet ideas", "A guide page in 15 minutes"]),
    ("Module 6", "Analytics + growth loop", None, [
        "Learn to read Insights", "Why did a reel flop?", "Weekly routine (2 hours)", "Fix loop: playbooks"]),
    ("Module 7", "Monetize (optional, honest)", None, [
        "Affiliate links", "Digital products", "Brand collabs"]),
]

# Default live-batch plan (shown when the editor's schedule box is empty). One class per line.
LIVE_SESSIONS = ["Welcome + pick your niche (0.1–1.1)", "Profile, highlights, link in bio + outliers (1.2–2.1)",
                 "30-day calendar, hook lab, keywords, script (2.2–3.1)", "Voiceover, CapCut edit, Claude Code reels (3.2–3.4)",
                 "Quality checklist, covers, DM machine setup (3.5–4.2)", "Follow-gate, safety, automation, freebie ideas (4.3–5.1)",
                 "Guide page, Insights, flop diagnosis, weekly routine (5.2–6.3)", "Playbooks + honest monetizing + wrap-up (6.4–7.3)"]

FOR = ["Creators, freelancers and small businesses who want to grow on Instagram with AI",
       "People who can't edit or code (Path A is fully no-code)", "Anyone ready to post 3–4 reels a week"]
NOT_FOR = ["People looking for a \"follower hack\"", "Anyone who wants results without posting"]

INCLUDED = [("🎥", "32 video lessons", "Step by step on screen, taught in Hinglish"),
            ("📘", "Student workbook (PDF)", "A copy-ready Claude prompt for every lesson, plus templates and checklists"),
            ("🧩", "Templates", "Calendar, outlier log, DM messages, export checklist")]

BONUSES = [
    ("📕", "Viral Reels Playbook", "ebook", "The 3-second rule, 7 reel structures beat by beat, 50 hook templates, retention tricks, CTA patterns and a viral checklist."),
    ("🧠", "Claude Prompt Vault", "52 prompts", "Research, ideas, scripts, captions, repurposing, DMs and analytics: a copy-ready prompt for every job."),
    ("💡", "100 Reel Idea Formulas", "ebook", "Fill-in-the-blank ideas in 10 categories that work for any niche. You'll never run out of ideas."),
    ("💬", "DM + Comment Script Pack", "ebook", "15 comment replies, a keyword DM flow, FAQ, sales and collab replies, and how to answer negative comments."),
    ("🎬", "Reel Studio Kit + 3 kits", "files", "My Remotion reel project plus the Caption Sync, Motion and Character kits, ready to use with Claude Code."),
    ("👤", "Profile + Highlights Kit", "files", "Highlight covers, About me / Freebies / Tips / Reviews / Collab story templates and a copy-ready bio."),
]

FAQ = [("Do I need Claude Pro?", "No. Most lessons work on the free plan. Long sessions and Claude Code (Path B reels) need a paid plan."),
       ("Do I need to know coding?", "No. Path A (CapCut) needs zero coding. Path B is optional."),
       ("What language is the course in?", "Hinglish: a natural mix of Hindi and English. This page is in English, but the video lessons and live classes are in Hinglish, so please make sure you're comfortable with that before you buy."),
       ("How long do I get access?", "6 months from the day you buy: all videos, the workbook and the bonuses. You can download the bonus files and keep them forever."),
       ("What happens after I pay?", "The course opens on SuperProfile right away: videos, workbook, all bonuses and resources. The Zoom link for the live batch is in the same student dashboard."),
       ("What if I miss a live class?", "No problem. Every class is recorded and the recording is added to the course."),
       ("Can I get a refund?", "It's a digital course, so there are no refunds once access is given. If there's any problem with payment or access, email us or DM on Instagram and we'll sort it out within 48 hours. Full policy: advocmedia.in/refund-policy."),
       ("Are followers guaranteed?", "No. No honest course can promise that. You get the system; the work is yours.")]

# ---------------- Sales page v2 (templates/course_v2.html) ----------------
HOOK_A = "Grow on Instagram with Claude."
HOOK_B = "Even from zero."
PAINS = ["…and stop guessing what to post every single day.",
         "No editor, no team, no ₹15,000/month agency."]
FOLDERS = ["welcome", "niche-profile", "content-plan", "reels", "dm-machine", "freebies", "growth-loop", "monetize"]
FREE_PREVIEW = True  # Module 0 is a free preview on SuperProfile: shows "Watch a free lesson"

# Real numbers from @aiwith.om (Instagram API, checked 21 Nov 2026). Update when they grow.
PROOF_ASOF = "21 Nov 2026"
PROOF_STATS = [("{F}", "followers on @aiwith.om"), ("1.8M+", "views from just my top 3 reels"), ("914K", "views on one reel")]
# Top reels of all time (views from Instagram, 21 Nov 2026). Images: the reel covers in freebies/videos/.
PROOF_REELS = [
    {"img": "/free/videos/top-ootto.jpg", "views": "914K", "what": "Connect Claude to Instagram", "note": "Comment → DM machine: OOTTO", "url": "https://www.instagram.com/reel/De1b4eETKjy/"},
    {"img": "/free/videos/top-launch.jpg", "views": "535K", "what": "5 places to launch your app", "note": "Comment → DM machine: LAUNCH", "url": "https://www.instagram.com/reel/DfB3RKmJbCJ/"},
    {"img": "/free/videos/top-youtube.jpg", "views": "379K", "what": "Claude as your YouTube manager", "note": "Comment → DM machine: YOUTUBE", "url": "https://www.instagram.com/reel/DfKVYcxzBTT/"},
]

TIMING = [("Now", "Early", "Very few creators use Claude properly. Huge reach for whoever shows up."),
          ("Next year", "Crowded", "Everyone has an AI workflow. Reach gets harder."),
          ("After that", "Saturated", "Only the best systems win. The early advantage is gone.")]
TIMING_LINE = "Jo pehle aayega, wahi jeetega."

# The "₹499 math": the real alternative is paying someone to do it (typical Indian market ranges).
MATH_COLS = ("Hire a social media manager", "This course")
MATH = [("Cost", "₹10,000–30,000 every month", "₹499 once"),
        ("Who knows the system", "They do. It leaves with them", "You do, for good"),
        ("Content plan", "Wait for their calendar", "30 days in 10 minutes with Claude"),
        ("Reels", "Brief, wait, revise", "Script → voice → edit yourself"),
        ("Comment → DM", "Extra tool, extra fee", "Set up in the course"),
        ("Language", "Usually 1–2", "Any language Claude writes")]

STEPS = [("Join", "Pay ₹499 on SuperProfile. The course opens instantly: videos, workbook and all 6 bonuses.", "Instant"),
         ("Follow the plan", "Module by module: niche, profile, 30-day plan, reels, DM machine. Copy-ready Claude prompts for each lesson.", "1 module a day"),
         ("Post and grow", "Post with a plan, let the DM machine work every comment, and fix one thing a week with the growth loop.", "Every week")]

FINAL_PUNCH = "Soch lo: ek aur mahina guesswork, ya ek system jo kaam karta hai?"
# Default "made with Claude" demo reels (720p, under 4 MB each, in freebies/videos/). The editor's video links replace these.
DEMO_VIDEOS = [
    {"url": "/free/videos/docu-code.mp4", "title": "One line in, a finished reel out"},
    {"url": "/free/videos/claude-instagram.mp4", "title": "Connect Claude to Instagram in 2 minutes"},
    {"url": "/free/videos/sales-plugin.mp4", "title": "A fully animated explainer, made with Claude"},
]
TESTIMONIALS = []  # (quote, name, role) — only real student messages, added with permission

FAQ = FAQ + [("Can I do this on my phone?", "Mostly yes: Claude, Instagram and CapCut all work on a phone. Path B reels (Claude Code + Remotion) need a laptop, and they're optional."),
             ("I have zero followers. Will this work?", "Yes, the course starts from zero: niche, profile and your first 30 days. No course can guarantee followers, but you get the exact system I used.")]
