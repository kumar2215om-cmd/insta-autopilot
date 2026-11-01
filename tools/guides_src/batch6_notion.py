"""Guides rebuilt from the Notion PDFs (CLAUDE #26, ANDROMEDA, COMPANY, CONTRACT, RULES). Run from repo root."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from guidepage import page
OUT = "freebies/guides"
LEGAL = "**Not legal advice.** This is general information. Have a lawyer review it for your business."
G = {}

G["CLAUDE"] = page("CLAUDE", "13 free Claude skills", "that run your Instagram",
 "Thanks for commenting CLAUDE! The full setup for claude-ig, a free, open-source (MIT) Instagram content engine with 13 sub-skills for Claude Code.", [
 ("Good to know", "What claude-ig is", [
   ("p", "Repo: [github.com/nicojunk/claude-ig](https://github.com/nicojunk/claude-ig)"),
   ("warn", "This runs in **Claude Code** (Anthropic's terminal app), not the normal Claude chat app. The writing skills (reels, hooks, captions, carousels, stories, calendar) work right away. Live analytics (`/ig analyze`, and live competitor scraping) need an Instagram Graph API token or an Apify token. Apify has a free tier.")]),
 ("Step 1", "Install Claude Code", [
   ("p", "Follow the official guide: docs.anthropic.com → Claude Code. You need a Claude Pro/Max plan or an API account.")]),
 ("Step 2", "Install the skills", [
   ("code", "Mac / Linux (one command)", "curl -fsSL https://raw.githubusercontent.com/nicojunk/claude-ig/main/install.sh | bash"),
   ("code", "Or manually", "git clone https://github.com/nicojunk/claude-ig.git\ncd claude-ig\nchmod +x install.sh && ./install.sh"),
   ("tip", "Then restart Claude Code. On Windows, run the commands inside **WSL**.")]),
 ("Step 3", "Use the commands", [
   ("table", ["Command", "What it does"], [
     ["`/ig reel <topic>`", "Full reel: hook, script, caption, thumbnail"], ["`/ig hook <topic>`", "Writes hooks and scores them"],
     ["`/ig caption <topic>`", "Optimised caption with a save CTA"], ["`/ig story <topic>`", "Story sequence (slides, stickers, polls)"],
     ["`/ig carousel <topic>`", "Carousel: cover, slides, CTA"], ["`/ig competitor <accounts>`", "What's working for competitors in your niche"],
     ["`/ig audit`", "Full content audit with a 100-point score"], ["`/ig calendar weekly`", "Weekly or monthly content calendar"],
     ["`/ig strategy`", "Positioning and content strategy"], ["`/ig comment`", "Comment reply strategy"],
     ["`/ig repurpose <post>`", "Repurpose for other platforms"], ["`/ig affiliate <partner>`", "Compliant affiliate content"],
     ["`/ig analyze <post-url>`", "Post performance (needs an API token)"]])]),
 ("Step 4", "(Optional) live data", [
   ("code", "Terminal", "export INSTAGRAM_ACCESS_TOKEN=\"your-token\"\n# or\nexport APIFY_TOKEN=\"your-apify-token\"\npip install -r requirements.txt   # Python 3.12+")]),
 ("Routine", "A simple daily routine", [
   ("ol", ["`/ig competitor @acc1 @acc2`: spot what's trending in your niche.", "`/ig reel <that topic>`: get the hook, script, caption and thumbnail.",
           "Record or edit, then post.", "Once a week, run `/ig audit` and `/ig calendar weekly`."]),
   ("tip", "Always read and personalise the output before posting. It's a strong first draft, not a replacement for your voice.")]),
])

G["ANDROMEDA"] = page("ANDROMEDA", "Meta's new AI ad system", "+ the structure that works",
 "Thanks for commenting ANDROMEDA! The full breakdown of Meta's AI ad retrieval system, and a simple campaign structure that works with it.", [
 ("What is it", "What is Andromeda?", [
   ("p", "Andromeda is Meta's AI-powered ad retrieval system, announced by Meta Engineering in December 2024. Before the ad auction, it picks a few thousand candidate ads for each person out of tens of millions. It was built because generative AI made ad volume explode (Meta said advertisers created 15 million+ ads with its GenAI tools in a single month), and the old system couldn't keep up."),
   ("tip", "**What it means for you:** Andromeda decides who sees your ad mostly by understanding your creative. So the creative now does the targeting.")]),
 ("3 changes", "The 3 big changes", [
   ("p", "**1 · Creative = targeting.** Meta reads your video, image and text to work out who the ad is for. Different creatives reach different people automatically, so you don't need tight interest targeting anymore."),
   ("p", "**2 · Real creative diversity.** Small tweaks (a new colour, the same video with a new headline) look like the same ad to Andromeda. You need ads that are genuinely different:"),
   ("list", ["**Hook:** a different first 3 seconds or opening line", "**Format:** video vs static vs carousel vs UGC vs founder-to-camera", "**Angle:** problem, benefit, social proof, comparison, offer, story"]),
   ("p", "**3 · Simple structure, broad audience.** Fewer campaigns and ad sets, with a broad audience, so all the learning data goes to one place.")]),
 ("Structure", "A simple campaign structure (starter)", [
   ("code", "Campaign structure", "Campaign: 1 · Sales (Advantage+ or manual CBO)\n  Ad set: 1 · Broad (country, age 18–65+, no interests)\n    Ads: 8–15 truly different creatives\n      - 3 hooks × 2–3 formats × 2 angles\nBudget: enough for ~50 conversions/week if possible\nRule: don't touch it for 3–7 days. Then cut losers, keep winners, add 3–5 new concepts every week."),
   ("p", "**Creative diversity checklist**"),
   ("list", ["At least 3 different hooks", "At least 2 different formats (e.g. video and static)", "At least 2 different angles", "Different people or faces and settings where possible", "A clear offer and CTA in every ad"])]),
 ("Prompts", "Claude prompts to make variations fast", [
   ("prompt", "10 concepts", "My product: <product>. Audience: <who>. Offer: <offer>.\nGive me 10 ad concepts that are TRULY different for Meta Andromeda:\nvary the hook, format (video / static / carousel / UGC) and angle (problem, benefit, proof, comparison, story).\nTable: # | angle | format | hook (first 3 sec) | script or copy | visual idea"),
   ("prompt", "One concept, two ads", "Turn concept #<n> into a 20-second UGC video script with on-screen text, and a static ad version (headline + 1 line + CTA).")]),
 ("Remember", "Remember", [
   ("p", "Andromeda pushes good ads further, but it won't save bad ones. **Spend your time on better creatives, not more ad sets.**"),
   ("p", "Idea credit: @usman.scaless.")]),
])

def bp(items): return ("ol", items)
G["COMPANY"] = page("COMPANY", "20 AI employees on n8n", "(full blueprints)",
 "Thanks for commenting COMPANY! Blueprints for all 20 AI employees: each one is a single n8n workflow (trigger → nodes → AI step → output). Build them one at a time.", [
 ("Before you start", "Honest note", [
   ("warn", "These are **blueprints, not finished files**. You build each workflow in n8n (about 15–45 min per workflow once you know n8n). Salary is ₹0, but the AI brain (OpenAI, Claude or Gemini API) costs a little per run, and some apps (WhatsApp Cloud API, Twilio) have their own small fees. Test everything on demo data first.")]),
 ("Setup", "Setup (one time)", [
   ("ol", ["**n8n:** use n8n Cloud (free trial) or self-host it for free with Docker (command below).",
           "**Credentials:** add these in n8n → Credentials: an AI model (OpenAI, Anthropic or Gemini), Google Sheets, Gmail, Google Calendar, and WhatsApp (Cloud API, or a provider like Interakt or Wati).",
           "**One Google Sheet as your mini-CRM:** tabs for Leads, Customers, Invoices, Tasks.",
           "**The AI step:** use the AI Agent or Basic LLM Chain node, with the prompt shown in each blueprint."]),
   ("code", "Self-host n8n", "docker run -it -p 5678:5678 n8nio/n8n")]),
 ("💼 Sales", "Sales (1–4)", [bp([
   "**Lead Finder:** Schedule (daily 9 AM) → HTTP Request (Google Maps / Places API: \"<category> in <city>\") → Split Out → Remove Duplicates → AI: \"Score this business 1–10 as a fit for <my offer>; give one line why.\" → Google Sheets (append to Leads).",
   "**Replier:** WhatsApp Trigger (new message) → AI Agent with a Sheets tool (FAQ + prices): \"Reply in Hinglish in 2 lines, answer from the FAQ, then ask one qualifying question.\" → WhatsApp Send → Sheets (log).",
   "**Call Booker:** Sheets Trigger (lead score ≥ 7) → AI: write a short message with a booking link → WhatsApp Send (Cal.com or Calendly link) → Cal.com Trigger (booked) → Sheets update + Gmail confirmation.",
   "**Re-order Bot:** Schedule (daily) → Sheets (customers whose last order was more than X days ago) → AI: \"Friendly re-order reminder mentioning <product>, max 2 lines.\" → WhatsApp Send."])]),
 ("🎧 Support", "Support (5–8)", [("ol", [
   "**Receptionist:** WhatsApp/Webhook → AI Agent with a Google Calendar tool (check free slots, create event) → WhatsApp confirm → Schedule a reminder 2 hours before.",
   "**Call Rescuer:** Twilio/Exotel webhook (missed call) → Wait 1 min → WhatsApp Send: \"Sorry we missed your call! How can we help?\" → Sheets (log the lead).",
   "**Inbox Sorter:** Gmail Trigger → AI (Text Classifier: lead / support / invoice / spam) → Switch → Gmail Add Label + Slack/WhatsApp ping for urgent mail.",
   "**FAQ Bot:** Webhook (website chat) or WhatsApp → AI Agent with a vector store (upload your FAQ docs) → reply → hand over to a human if confidence is low."]),
   ]),
 ("📣 Marketing", "Marketing (9–12)", [("ol", [
   "**SEO Writer:** Schedule (weekly) → Sheets (keyword list) → AI: \"Write a 700-word local SEO page for <service> in <area> with H2s, FAQs and a CTA.\" → WordPress/Webflow (create draft).",
   "**Repurposer:** Google Drive Trigger (new video) → transcribe (OpenAI Whisper node) → AI: \"Turn this transcript into 5 posts: 1 reel script, 1 carousel, 1 tweet thread, 1 LinkedIn post, 1 caption.\" → Sheets/Notion (content calendar).",
   "**Review Bot:** Schedule (hourly) → Google Business Profile API (new reviews) → AI: \"Reply warmly, mention their detail, max 40 words; apologise and offer a fix if negative.\" → post the reply (or send it to you for approval).",
   "**Review Asker:** Sheets Trigger (order delivered) → Wait 2 days → WhatsApp Send (personal ask + review link)."])]),
 ("💰 Finance", "Finance (13–16)", [("ol", [
   "**Bill Reader:** Gmail Trigger (has attachment) → Extract From File (PDF) → AI (Information Extractor: vendor, date, amount, GST, due date) → Sheets (Invoices).",
   "**Collector:** Schedule (daily) → Sheets (unpaid invoices past their due date) → AI: polite reminder, firmer each time → WhatsApp/Gmail → log the attempt number.",
   "**Statement AI:** Upload bank statement CSV (Form trigger) → AI: categorise each transaction (rent, ads, salary, software…) → Sheets → monthly summary to Gmail.",
   "**GST Clerk:** Sheets Trigger (new sales invoice) → Code node (calculate CGST/SGST/IGST) → Sheets (GST register in GSTR-1 format). Have your CA review it before filing."])]),
 ("⚙️ Ops", "Ops (17–20)", [("ol", [
   "**HR Screener:** Form/Gmail (resume) → Extract From File → AI: \"Score 1–10 against this JD; list 3 strengths and 2 gaps.\" → Sheets → notify for scores ≥ 8.",
   "**No-show Stop:** Calendar Trigger (event in 24h) → WhatsApp \"Reply YES to confirm\" → Wait for reply → IF no reply after 3h, send a second reminder and alert you.",
   "**Deadline Bot:** Schedule (8 AM daily) → Sheets/Notion (tasks due within 48h) → AI: write a crisp to-do summary → WhatsApp/Slack to the owner.",
   "**Doc Chaser:** Sheets (client → missing docs) → Schedule → WhatsApp/Gmail request with an upload link (Drive folder or form) → Drive Trigger (file received) → mark done."])]),
 ("Build order", "Build order (recommended)", [
   ("p", "Start with the ones that make or save money fastest: **Call Rescuer (6) → Replier (2) → No-show Stop (18) → Review Asker (12) → Collector (14).** Then add the rest."),
   ("prompt", "Get Claude to help you build any of them", "I'm building this n8n workflow: <paste blueprint>.\nGive me step-by-step node settings (exact fields), the AI prompt, test data, and common errors to watch for.")]),
])

G["CONTRACT"] = page("CONTRACT", "Developer contract checklist", "(DPDP Act basics)",
 "Thanks for commenting CONTRACT! The checklist to protect yourself before getting a website or app built.", [
 ("Before you start", "Not legal advice", [
   ("warn", "**Not legal advice.** This is general information. Get your contract reviewed by a lawyer. The DPDP Rules, 2025 were notified in Nov 2025 and apply in phases, with most duties expected by around mid-2027. Starting now is the smart move.")]),
 ("Why", "Why it matters (DPDP Act, 2023)", [
   ("list", ["Whoever decides why and how personal data is used is the **Data Fiduciary**. If it's your website, that's you.",
             "**Section 8(1):** you are responsible for processing done on your behalf by a Data Processor (your developer or agency), irrespective of any agreement to the contrary.",
             "Failing to take reasonable security safeguards can attract a penalty of **up to ₹250 crore**.",
             "The developer isn't automatically off the hook, but to recover your losses you need clear written terms."])]),
 ("Must-dos", "The 3 must-dos", [
   ("ol", ["**A written contract** (not a WhatsApp \"bhai bana do\").", "**The domain in your name,** registered with your own account and email.",
           "**Admin logins with you:** hosting, CMS, database, analytics and payment gateway. The developer gets their own separate user, never your master login."])]),
 ("Contract", "What to put in the contract (checklist)", [
   ("list", ["**Scope and deliverables:** pages, features, timeline, handover date.", "**Ownership:** you own the code, design, content and data. Assignment of IP on payment.",
             "**Data protection clause:** the developer acts only on your written instructions, processes data only for this project, and never shares or sells it.",
             "**Security standards:** HTTPS, form data encrypted, admin 2FA, regular updates and backups, no plain-text passwords.",
             "**Access control:** least-privilege access, removed at the end of the project.",
             "**Breach notice:** the developer must tell you immediately (e.g. within 24 hours) about any breach or suspected leak, and help you respond.",
             "**Sub-contractors:** no third party touches the data without your written OK.",
             "**Indemnity:** the developer compensates you for losses caused by their negligence or breach of the contract.",
             "**Confidentiality:** survives after the project ends.",
             "**Handover and deletion:** full code and credentials handed over; the developer deletes all copies of customer data at the end and confirms it in writing.",
             "**Maintenance terms:** who patches security issues, for how long, and at what cost.", "**Jurisdiction and dispute resolution.**"])]),
 ("Owner basics", "Your own basics (as the owner)", [
   ("list", ["Collect only the data you need on forms.", "Add a clear privacy notice and consent checkbox.",
             "Know where form data is stored (email, sheet, database) and who can see it.", "Keep a simple log of who has access."])]),
 ("Prompt", "Claude prompt to draft your contract", [
   ("prompt", "Copy karo", "Draft a website development agreement between <my business> (client, India) and <developer>.\nInclude: scope, timeline, payment milestones, IP ownership to client, a data processing clause aligned with India's DPDP Act 2023 (developer = data processor acting on client instructions), security standards, 24-hour breach notification, no sub-processors without consent, indemnity, confidentiality, handover of code and credentials, deletion of personal data at the end, and jurisdiction <city>.\nUse simple English and add a one-page summary in Hinglish."),
   ("warn", "Then have a lawyer review it before signing.")]),
])

G["RULES"] = page("RULES", "Website compliance checklist", "before May 2027",
 "Thanks for commenting RULES! The full 8-point checklist (DPDP Act + basics) to make your website ready.", [
 ("Before you start", "Not legal advice", [
   ("warn", f"{LEGAL} The DPDP Act, 2023 and the DPDP Rules, 2025 (notified Nov 2025) apply in phases, with most duties in force by around May 2027. Points 5 and 6 come from consumer and e-commerce rules, not the DPDP Act.")]),
 ("Why now", "Why now", [
   ("p", "If your site has a contact form, signup, checkout, WhatsApp opt-in or a tracking pixel, you're collecting personal data. Failing to protect it can mean penalties of **up to ₹250 crore** under the DPDP Act.")]),
 ("1–2", "Privacy notice + consent", [
   ("p", "**1 · Privacy notice / policy**"),
   ("list", ["Lists exactly what data you collect (name, phone, email, location, cookies…)", "Why you collect each item (specific purpose)", "How long you keep it, and when it's deleted",
             "Who you share it with (payment gateway, courier, CRM, ad platforms)", "How users can access, correct or delete their data and withdraw consent",
             "Written in clear, simple language (English plus a local language is better)"]),
   ("p", "**2 · Consent**"),
   ("list", ["No pre-ticked boxes. Consent needs a clear action.", "Separate consent for marketing (WhatsApp, SMS, email offers)",
             "Withdrawing is as easy as giving (an unsubscribe link, a toggle, \"STOP\")", "Keep a record of when and how consent was given"])]),
 ("3–4", "Grievance contact + cookies", [
   ("p", "**3 · Grievance officer / contact**"),
   ("list", ["Name (or role) plus email or phone, clearly visible on the site", "A simple process to respond to complaints within a fixed time"]),
   ("p", "**4 · Cookies & tracking**"),
   ("list", ["A cookie or tracking banner that tells visitors what you track (analytics, Meta pixel, Google Ads)", "Accept, Reject and Manage options, with non-essential tracking off until accepted"])]),
 ("5–7", "Terms, selling online, children", [
   ("p", "**5 · Terms & conditions**"), ("list", ["The rules of your service: payments, cancellations, liability, disputes"]),
   ("p", "**6 · If you sell online**"), ("list", ["Return, refund and shipping policies", "Legal business name, address and contact details on the site"]),
   ("p", "**7 · Children's data**"), ("list", ["If users can be under 18, get verifiable parental consent", "No tracking or targeted ads aimed at children"])]),
 ("8", "Security & breach response", [
   ("list", ["HTTPS / SSL on every page", "Strong admin passwords plus 2FA, regular updates and backups", "Access limited to the people who need it",
             "A breach plan: inform affected users and the Data Protection Board without delay"]),
   ("p", "**Also don't forget**"),
   ("list", ["Delete data you no longer need (set retention periods)", "Keep simple records of processing and consents",
             "Contracts with your developer and vendors (see the [CONTRACT checklist](CONTRACT.html))"])]),
 ("Prompts", "Claude prompts", [
   ("prompt", "Privacy notice", "Write a clear privacy notice for <business> (India) that collects <data list> for <purposes>, shares with <vendors>, keeps data for <period>. Follow the DPDP Act 2023 notice requirements. Simple English + Hindi summary."),
   ("prompt", "Consent + cookie banner", "Write consent text and a cookie banner for my website: separate checkboxes for marketing, Accept / Reject / Manage options, and an easy withdraw option."),
   ("p", "Idea credit: @ecolatur.")]),
])

# COMPANY: keep blueprint numbers running across departments (Sales 1-4, Support 5-8, ...)
_h = G["COMPANY"]; _parts = _h.split('<ol class="num">'); _out = _parts[0]; _start = {2: 1, 3: 5, 4: 9, 5: 13, 6: 17}
for _k, _part in enumerate(_parts[1:], 1):
    _out += (f'<ol class="num" start="{_start[_k]}">' if _k in _start else '<ol class="num">') + _part
G["COMPANY"] = _out

for name, html in G.items():
    open(os.path.join(OUT, f"{name}.html"), "w", encoding="utf-8").write(html)
TARGET = {26: "CLAUDE", 27: "ANDROMEDA", 28: "COMPANY", 29: "CONTRACT", 30: "RULES"}
p = "freebies/index.html"; s = open(p, encoding="utf-8").read()
i = s.index("const D=") + 8; j = s.index(";\n", i); d = json.loads(s[i:j])
for x in d["items"]:
    if x["n"] in TARGET:
        x["u"] = f"guides/{TARGET[x['n']]}.html"; print(x["n"], x["k"], "->", x["u"])
open(p, "w", encoding="utf-8").write(s[:i] + json.dumps(d, ensure_ascii=False) + s[j:])
