"""Guides rebuilt from the Notion PDFs (EBOOK, LAUNCH). Run from repo root."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from guidepage import page
OUT = "freebies/guides"
SP = "https://superprofile.bio/?referralCode=Akgjjy&referralType=creatorReferral&source=referralPage"
G = {}

TOPICS = [
 ("Money & career", ["Personal finance basics for first-job earners", "How to save your first ₹1 lakh", "Budgeting on a ₹20,000 salary", "Mutual funds and SIP for beginners",
   "Credit score: how to build and fix it", "Freelancing: getting your first client", "Resume that gets interview calls", "Cracking HR interviews: 50 questions",
   "LinkedIn profile that attracts recruiters", "Side incomes for students", "Salary negotiation scripts", "Starting a small online business with ₹5,000",
   "GST basics for small sellers", "Selling on Meesho / Amazon for beginners", "Cold email templates for freelancers"]),
 ("Skills & software", ["Excel for beginners in 7 days", "Advanced Excel formulas cheat book", "Google Sheets for small businesses", "Canva for small business owners",
   "Video editing on phone (CapCut)", "ChatGPT / Claude prompts for daily work", "AI tools for students", "AI tools for teachers", "Power BI basics", "SQL for absolute beginners",
   "Python in 30 days", "Notion for students and planners", "Touch typing and productivity shortcuts", "Photography with a phone", "Basic graphic design rules"]),
 ("Social media & marketing", ["Instagram growth for local shops", "Reels scripting: 50 hook templates", "YouTube Shorts for beginners", "WhatsApp Business selling guide",
   "Personal branding on LinkedIn", "Content calendar for 30 days", "Copywriting for Instagram captions", "Facebook ads for small budgets", "Google My Business for local shops",
   "Influencer collaborations for small brands", "Starting a faceless page", "Email marketing basics"]),
 ("Health & fitness", ["Home workout plan (no equipment)", "Weight loss with Indian food", "High-protein vegetarian meal plan", "Yoga for back pain", "Desk-job posture fixes",
   "Beginner running plan (5K)", "PCOS-friendly diet guide", "Diabetes-friendly Indian recipes", "Better sleep in 14 days", "Gym beginner's 12-week plan",
   "Healthy tiffin ideas for kids", "Skin care routine on a budget"]),
 ("Education & exams", ["Study planner for board exams", "How to study 6 hours without burnout", "Spoken English in 30 days", "Vocabulary builder: 500 useful words",
   "Interview English for freshers", "UPSC prelims strategy for beginners", "Note-making methods that work", "Memory techniques for students", "Math shortcuts for competitive exams",
   "Study abroad guide: step by step", "IELTS speaking practice book", "Public speaking for shy students"]),
 ("Food & home", ["Meal prep on a budget", "30 quick dinners in 20 minutes", "Baking basics without an oven", "Starting a home tiffin service", "Home organisation for small flats",
   "Indoor plants care guide", "Kitchen gardening on a balcony", "Festival recipes collection", "Lunchbox ideas for office", "Minimalism for Indian homes"]),
 ("Parenting & relationships", ["Screen time rules for kids", "Activities for toddlers at home", "Teaching kids about money", "Pregnancy diet guide (Indian)", "Wedding planning checklist",
   "Communication tips for couples", "Parenting teenagers", "Baby's first year guide"]),
 ("Mindset & productivity", ["Morning routine for busy people", "Beating procrastination in 21 days", "Journaling prompts: 100 days", "Habit tracker workbook", "Time blocking for freelancers",
   "Digital detox plan", "Focus techniques for remote work", "Goal setting workbook"]),
 ("Business & niche", ["Starting a cloud kitchen", "Opening a small café: checklist", "Event planning business basics", "Real estate agent's first year", "Starting a tuition business",
   "Pet care guide for first-time owners", "Travel India on a budget", "Solo travel safety guide for women", "Car buying guide for first-timers",
   "Basic legal documents every freelancer needs", "Starting a clothing brand on Instagram", "Handmade products: pricing and selling", "Wedding photography starter guide"]),
]
assert sum(len(t) for _, t in TOPICS) == 105
topic_sections = [(name.split(" & ")[0], f"{name}", [("ol", items)]) for name, items in TOPICS]

G["EBOOK"] = page("EBOOK", "100+ high-demand ebook topics,", "the prompt + full setup",
 "Thanks for commenting EBOOK! Everything from the reel: the prompt, the 3 steps, where to sell, and 100+ topics to pick from.", [
 ("Before you start", "Honest note", [
   ("warn", "₹10,713 was my real collected amount over 7 days (before fees). Results vary. This works only if the ebook genuinely solves a problem.")]),
 ("Step 1", "Pick a topic", [
   ("p", "Pick a **specific problem people already pay to solve** (save money, get a job, learn a skill, fix health or habits, grow a business). \"My life story\" doesn't sell. \"Excel for beginners in 7 days\" does. The list is below.")]),
 ("Step 2", "The Claude prompt", [
   ("p", "Replace **[TOPIC]** and **[READER]** and paste it into Claude:"),
   ("prompt", "Copy karo", "You are an expert author and teacher. Write a practical ebook on [TOPIC] for [READER, e.g. complete beginners in India].\nStructure:\n1. A strong title + subtitle (give 5 options, pick the best)\n2. Introduction: the problem, who this is for, what they will be able to do after reading\n3. 7 chapters, each with: a clear explanation, a real-world example (Indian context where it fits), common mistakes, and 3 action steps\n4. A quick-start checklist and a 7-day action plan\n5. A short conclusion\nRules: simple language, short paragraphs, no filler, no exaggerated claims. Mark any fact or number I should verify with [CHECK]. Write chapter by chapter. Start with the outline and wait for my OK.")]),
 ("Step 3", "Design it in Gamma", [
   ("ol", ["Go to [gamma.app](https://gamma.app/), choose **Create new → Paste in text**, and paste Claude's text.", "Pick a document-style theme, add a cover, then **Export → PDF**."]),
   ("p", "**Before you sell (don't skip)**"),
   ("list", ["Read it fully once", "Check every [CHECK] fact and remove anything you can't verify",
             "Add your own examples, screenshots or templates. This is what makes it worth paying for", "Add a short \"who this is NOT for\" line to avoid refunds"])]),
 ("Where to sell", "Where to sell", [
   ("table", ["Platform", "Notes"], [
     [f"**SuperProfile** (what I use)", f"Your own store, UPI payments, link in bio. Traffic comes from your reels. 👉 [Create your SuperProfile store here]({SP}) (my referral link)"],
     ["**Gumroad**", "About 10% + $0.50 per direct sale, with card processing on top; 30% if the buyer comes through Gumroad Discover."],
     ["**Etsy**", "$0.20 listing fee, 6.5% transaction fee and payment processing, and AI-made products must be disclosed."],
     ["**Amazon KDP**", "You must disclose AI-generated text, and new uploads are limited to 3 titles a day."]]),
   ("tip", "Fees can change, so check each platform before pricing. A good starting price in India is **₹99–₹299**.")]),
] + topic_sections)
# number the 105 topics continuously across the category lists
_h = G["EBOOK"]; _parts = _h.split('<ol class="num">'); _out = _parts[0]; _n = 1; _starts = {}
_k = 0
for name, items in TOPICS: _starts[name] = _n; _n += len(items)
_topic_starts = [ _starts[name] for name, _ in TOPICS ]
_ol_index = 0
for _part in _parts[1:]:
    _ol_index += 1
    # first ol is Step 3 (Gamma); topic lists follow in order
    if _ol_index >= 2 and _ol_index - 2 < len(_topic_starts):
        _out += f'<ol class="num" start="{_topic_starts[_ol_index - 2]}">' + _part
    else:
        _out += '<ol class="num">' + _part
G["EBOOK"] = _out

G["LAUNCH"] = page("LAUNCH", "5 places to launch your app", "(with links + tips)",
 "Thanks for commenting LAUNCH! Post your app in these 5 places first, one at a time, not everywhere on the same day.", [
 ("1 · Reddit", "1 · Reddit r/SideProject", [
   ("p", "[reddit.com/r/SideProject](https://www.reddit.com/r/SideProject/)"),
   ("list", ["Write it like a builder: what it does, who it's for, and \"would love honest feedback\". Reply to every comment.",
             "Read the sub's rules first, and don't post the same link across 10 subs at once."])]),
 ("2 · Hacker News", "2 · Hacker News (Show HN)", [
   ("p", "[news.ycombinator.com/showhn.html](https://news.ycombinator.com/showhn.html)"),
   ("code", "Title format", "Show HN: [App name] – [what it does in plain words]"),
   ("list", ["Link to something people can try without a long signup.", "Hitting the front page is never guaranteed, but when it happens, thousands of people can see it in a day."])]),
 ("3 · Product Hunt", "3 · Product Hunt", [
   ("p", "[producthunt.com](https://www.producthunt.com/)"),
   ("list", ["Launches go live at **12:01 AM Pacific time** (about 12:30 PM in India).",
             "**Tue–Thu:** most traffic, but also the toughest competition. **Weekends:** fewer launches, so it's easier to rank. Pick based on your goal.",
             "Prepare a tagline, 3–5 screenshots or a short demo video, and a first comment explaining why you built it."])]),
 ("4 · Indie Hackers", "4 · Indie Hackers", [
   ("p", "[indiehackers.com](https://www.indiehackers.com/)"),
   ("p", "Share your story and numbers (what you built, why, first results). Founders here try new tools and give feedback.")]),
 ("5 · Uneed", "5 · Uneed", [
   ("p", "[uneed.best](https://www.uneed.best/)"),
   ("list", ["Only a few products launch per day, so you don't get buried. Every launch gets a lifetime backlink to your site.",
             "The free option puts you in a waiting queue; paid lets you pick your date."])]),
 ("Checklist", "Launch-week checklist", [
   ("list", ["One clear sentence: what your app does and for whom", "A landing page that works on mobile and has an email or signup capture",
             "3–5 screenshots or a 30-second demo", "Spread the launches over 1–2 weeks so you can reply to everyone", "Write down every piece of feedback, then fix the top 3 issues"]),
   ("warn", "Visitor and vote numbers in the reel are examples, not promises. Platform rules and pricing can change, so check each site before posting.")]),
])

for name, html in G.items():
    open(os.path.join(OUT, f"{name}.html"), "w", encoding="utf-8").write(html)
TARGET = {36: "LAUNCH", 37: "EBOOK"}
p = "freebies/index.html"; s = open(p, encoding="utf-8").read()
i = s.index("const D=") + 8; j = s.index(";\n", i); d = json.loads(s[i:j])
for x in d["items"]:
    if x["n"] in TARGET:
        x["u"] = f"guides/{TARGET[x['n']]}.html"; print(x["n"], x["k"], "->", x["u"])
open(p, "w", encoding="utf-8").write(s[:i] + json.dumps(d, ensure_ascii=False) + s[j:])
