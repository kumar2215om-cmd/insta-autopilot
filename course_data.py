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
