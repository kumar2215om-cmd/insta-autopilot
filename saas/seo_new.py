"""SEO batch C: new pages for searches the site didn't cover, and the industry playbooks merged into one deep page.

- NEW_GUIDES / NEW_COMPARE are added to seo_content.GUIDES / COMPARE (and to a topic) when seo_content loads.
- INDUSTRY gives the by-industry topic page a real overview (table, shared funnel, rules, hand-off defaults) that links to each
  niche playbook. The playbooks themselves stay at their addresses: @replyinbox carousels and their DM links point to them.
Facts about other tools stay hedged and dated. "{brand}" is replaced with the brand name when rendering.
"""
from seo_deep import WIZ, fig

# ---------------------------------------------------------------- industries, one deep page

G = "/guides/instagram-dm-automation-for-"

INDUSTRY = {
    "description": "Instagram DM automation playbooks for coaches, fitness, finance, education, food, beauty, travel, real estate and astrology: "
                   "funnels, keywords and what the AI should answer.",
    "sections": [
        ("How to use these playbooks",
         "<p>Every niche uses the same building blocks: a reel with a keyword, a DM with something useful, lead capture, a follow-up offer and "
         "an AI agent for the questions that come after. What changes is the offer, the keywords, the questions people ask and the rules you "
         "have to respect. Find your niche in the table, open its playbook, copy the funnel into an automation and swap in your own offer.</p>"),
        ("Every niche at a glance",
         "<div class=\"scroll\"><table><thead><tr><th>Niche</th><th>Best keyword</th><th>Free offer</th><th>Lead step</th><th>Hand to a human</th></tr></thead><tbody>"
         f"<tr><td><a href=\"{G}coaches\">Coaches</a></td><td>GUIDE</td><td>Mini-course or worksheet</td><td>WhatsApp from \"ready to work together\"</td><td>Program fit, pricing exceptions</td></tr>"
         f"<tr><td><a href=\"{G}fitness-coaches\">Fitness</a></td><td>PLAN</td><td>7-day workout or meal plan</td><td>Menu by goal, WhatsApp for coaching</td><td>Injuries, medical conditions</td></tr>"
         f"<tr><td><a href=\"{G}finance-creators\">Finance</a></td><td>SHEET</td><td>Budget sheet, tax checklist</td><td>Email for a newsletter</td><td>What to buy or sell</td></tr>"
         f"<tr><td><a href=\"{G}educators\">Education</a></td><td>NOTES</td><td>Notes PDF, practice set</td><td>Menu by class, WhatsApp for batches</td><td>Refunds, a student's results</td></tr>"
         f"<tr><td><a href=\"{G}food-creators\">Food</a></td><td>RECIPE</td><td>Full recipe card</td><td>WhatsApp for cake orders</td><td>Custom orders, allergies</td></tr>"
         f"<tr><td><a href=\"{G}beauty-creators\">Beauty and fashion</a></td><td>LINK</td><td>Product list, routine</td><td>WhatsApp for bridal bookings</td><td>Bookings, complaints</td></tr>"
         f"<tr><td><a href=\"{G}travel-creators\">Travel</a></td><td>TRIP</td><td>Itinerary and map</td><td>WhatsApp for a custom quote</td><td>Quotes, cancellations</td></tr>"
         f"<tr><td><a href=\"{G}real-estate\">Real estate</a></td><td>PRICE</td><td>Brochure and price sheet</td><td>Menu by budget, WhatsApp for a site visit</td><td>Negotiation, loans, legal</td></tr>"
         f"<tr><td><a href=\"{G}astrologers\">Astrology</a></td><td>Your sign</td><td>Weekly reading</td><td>WhatsApp for a consultation</td><td>Personal readings</td></tr>"
         f"<tr><td><a href=\"{G}ecommerce\">Online stores</a></td><td>SHOP</td><td>Product link or code</td><td>Follow-up with an offer</td><td>Orders, returns</td></tr>"
         "</tbody></table></div>"),
        ("The same funnel, five steps",
         "<ol><li><b>Reel</b> with one clear promise and a one-word keyword said in the first 3 seconds.</li>"
         "<li><b>DM</b> with the free offer, often after a <a href=\"/features/follow-to-unlock\">follow gate</a>.</li>"
         "<li><b>Sort and capture</b>: a <a href=\"/guides/instagram-dm-choice-menus\">choice menu</a> by goal, class or budget, and a WhatsApp "
         "number or email from the people who want more.</li>"
         "<li><b>Follow-up</b> 3–6 hours later with your paid offer, call or batch.</li>"
         "<li><b>AI agent</b> answers price, timing and how-to questions from your FAQ, and hands the sensitive ones to you.</li></ol>"
         "<p>On Creator, the <b>Lead Qualifier agent</b> also sorts the people in your DMs into hot, warm and cold leads with what they want.</p>"),
        ("Niches with rules to respect",
         "<ul><li><b>Finance</b>: keep DMs educational. In India, unregistered creators should not give investment advice or stock tips; follow "
         "SEBI's current rules for finfluencers. <a href=\"" + G + "finance-creators\">Finance playbook</a>.</li>"
         "<li><b>Fitness and health</b>: no guaranteed results, a short disclaimer on free plans, and medical questions go to you. "
         "<a href=\"" + G + "fitness-coaches\">Fitness playbook</a>.</li>"
         "<li><b>Real estate</b>: show registration details where required (in India, the RERA number) and keep prices accurate. "
         "<a href=\"" + G + "real-estate\">Real estate playbook</a>.</li>"
         "<li><b>Food</b>: follow licence and labelling rules (FSSAI for home food businesses in India) and list allergens. "
         "<a href=\"" + G + "food-creators\">Food playbook</a>.</li>"
         "<li><b>Astrology</b>: no guaranteed outcomes; birth details only for paid readings, kept private. "
         "<a href=\"" + G + "astrologers\">Astrology playbook</a>.</li>"
         "<li><b>Affiliate links</b> (beauty, fashion, tech): turn off click tracking where the programme forbids redirects, and disclose "
         "affiliate links where required.</li></ul>"),
        ("Tell the AI what to hand over",
         "<p>The AI DM agent only answers from your FAQ and products, and you list the topics it must pass to you. A good default by niche:</p>"
         "<div class=\"scroll\"><table><thead><tr><th>Niche</th><th>The AI answers</th><th>Always handed to you</th></tr></thead><tbody>"
         "<tr><td>Coaching, fitness</td><td>Price, length, format, timings</td><td>Health conditions, refunds</td></tr>"
         "<tr><td>Education</td><td>Fees, batch timings, syllabus, language</td><td>Refunds, a student's results</td></tr>"
         "<tr><td>Finance</td><td>Your course, webinar and tools</td><td>Any \"what should I buy\" question</td></tr>"
         "<tr><td>Food, beauty, travel</td><td>Menu, prices, services, what's included</td><td>Custom orders, quotes, complaints</td></tr>"
         "<tr><td>Real estate</td><td>Location, sizes, amenities, starting prices</td><td>Negotiation, loans, legal</td></tr>"
         "</tbody></table></div><p>More in <a href=\"/guides/ai-handoff-rules\">AI hand-off rules</a>.</p>"),
        ("Measure what works in your niche",
         "<p>Give each reel its own keyword and check the reel report: views, comments, who used the keyword, got the DM, opened the link and "
         "followed. Sales tracking credits each payment to the reel and automation that brought it, so you can repeat the formats that sell. "
         "Leads go to Google Sheets, Zapier, Make or your CRM by webhook on every plan.</p>"
         + fig("reel-report", "Reel report showing for each reel the views, comments, keyword uses, DMs, links sent and follows",
               "The reel report: compare reels by what they actually brought in.")),
    ],
    "faq": [
        ("Does DM automation work for service businesses?", "Yes: real estate, salons, coaches, tutors and travel agencies use it to qualify "
         "enquiries before a call, with a menu to sort people and WhatsApp capture for serious leads."),
        ("Which plan do most niches need?", "Starter (₹149) for follow to unlock and lead capture; Creator (₹199) adds no DM cap, 300 AI "
         "replies and the Lead Qualifier agent."),
        ("Will the AI answer questions I'm not allowed to answer?", "Only if you let it. It answers from your FAQ and products, and you list "
         "the topics it must hand over, such as medical, investment or legal questions."),
        ("Can I send leads to my CRM or Google Sheets?", "Yes, on every plan, through a webhook in Settings → Integrations (Google Sheets, Zapier, Make or Pabbly)."),
    ],
}


# ---------------------------------------------------------------- new guides

FREE = {
    "title": "Free Instagram auto DM: what you get on free plans (2026)",
    "description": "Free Instagram auto DM tools compared, and how to set up comment-to-DM for free with 1,000 DMs a month on {brand}.",
    "answer": "You can auto DM people who comment on your Instagram reels for free. {brand}'s free plan sends 1,000 DMs a month with "
              "comment-to-DM on every reel and post, keyword DMs and Live comments, with no card and no time limit. Other tools with free "
              "plans include LinkDM, ReplyKaro, InstantDM and ReplyRush; they differ in DM limits and which features are free.",
    "sections": [
        ("What \"free\" usually means",
         "<p>Almost every Instagram DM automation tool has a free plan. The differences are in three places: how many DMs a month you get, "
         "which features are locked behind a paid plan (usually follow to unlock, email capture and story replies), and whether the free plan "
         "is permanent or a trial that ends.</p>"),
        ("Free plans compared (checked November 2026)",
         "<div class=\"scroll\"><table><thead><tr><th>Tool</th><th>Free plan</th><th>Good to know</th></tr></thead><tbody>"
         "<tr><td><b>{brand}</b></td><td>1,000 DMs a month, forever</td><td>Comment-to-DM on every post, keyword DMs, Live comments, link in bio, 25 AI replies</td></tr>"
         "<tr><td>LinkDM</td><td>About 1,000 DMs</td><td>Simple comment-to-DM; paid plans in dollars</td></tr>"
         "<tr><td>ReplyKaro</td><td>About 1,000 DMs</td><td>Indian tool; cheapest paid plan about ₹99</td></tr>"
         "<tr><td>InstantDM</td><td>About 500 DMs</td><td>Low-cost paid plans</td></tr>"
         "<tr><td>ReplyRush</td><td>Free DMs</td><td>Plans by DM volume</td></tr>"
         "<tr><td>ManyChat</td><td>Small contact limit</td><td>Paid plan priced by contacts</td></tr>"
         "<tr><td>Meta Business Suite</td><td>Free</td><td>Basic automated replies; see <a href=\"/vs/meta-business-suite\">the comparison</a></td></tr>"
         "</tbody></table></div><p class=\"note\">From each tool's public pages, checked November 2026. Free plans change; check before relying on one.</p>"),
        ("What {brand}'s free plan includes",
         "<ul><li><b>1,000 DMs every month</b>, reset monthly, no card needed and no trial that expires.</li>"
         "<li><a href=\"/features/comment-to-dm\">Comment-to-DM</a> on any reel or post, all your posts, or your next post.</li>"
         "<li>Keyword DM automations, a welcome message and Live comment automation.</li>"
         "<li>Up to 3 link buttons or a choice menu, a follow-up offer, delays, once per person and message variations.</li>"
         "<li>Link in bio page, Leads, the reel report and a giveaway picker.</li>"
         "<li>25 AI replies to try the AI DM agent.</li>"
         "<li>Selling products and courses (5% + GST per sale, no monthly fee).</li></ul>"
         + fig("wizard-trigger", "Create automation screen with five triggers: comments, DMs, story replies, story mentions and Live comments",
               "Comment, DM and Live comment automations are on the free plan.", (560, 548))),
        ("Set it up for free in 5 minutes",
         "<ol><li>Switch to a <a href=\"/guides/switch-to-instagram-professional-account\">Creator or Business account</a> (free).</li>"
         "<li>Sign up on {brand} with Google. No card.</li>"
         "<li>Connect Instagram through Meta's login; {brand} never asks for your password.</li>"
         "<li>Auto DM → Create automation → Comments on your post or reel. Pick the reel and a keyword like GUIDE.</li>"
         "<li>Write the DM, put your link on a button, and launch.</li></ol>"
         "<p>Detailed walkthrough: <a href=\"/guides/how-to-auto-dm-instagram-comments\">how to auto DM people who comment</a>.</p>"),
        ("Is 1,000 DMs a month enough?",
         "<p>For most accounts under about 10,000 followers, yes. One DM is used per person who comments your keyword (the public reply "
         "doesn't count). If you post 3–4 keyword reels a month and each gets 100–250 keyword comments, you stay inside 1,000.</p>"
         "<p>You'll want more when a reel takes off. When you reach the limit, new DMs pause until next month or until you upgrade, and "
         "{brand} warns you when you've used 80%.</p>"),
        ("When to upgrade, and to what",
         "<div class=\"scroll\"><table><thead><tr><th>You want…</th><th>Plan</th></tr></thead><tbody>"
         "<tr><td>Only followers get the freebie (follow to unlock)</td><td>Starter ₹149</td></tr>"
         "<tr><td>Collect emails or WhatsApp numbers in the DM</td><td>Starter ₹149</td></tr>"
         "<tr><td>Story reply and mention automations</td><td>Starter ₹149</td></tr>"
         "<tr><td>More than 3,000 DMs, AI replies every month</td><td>Creator ₹199</td></tr>"
         "<tr><td>Several Instagram accounts, Claude</td><td>Pro ₹599 / Agency ₹2,000</td></tr>"
         "</tbody></table></div><p>All plans: <a href=\"/pricing\">{brand} pricing</a>.</p>"),
        ("Free tools to avoid",
         "<p>Be careful with \"free\" tools that ask for your Instagram password, send DMs to people who didn't ask, or run from a browser "
         "extension. They break Instagram's rules and put your account at risk. Use a tool on Meta's official API: you connect through "
         "Instagram's own login screen and can remove access any time. More in <a href=\"/guides/is-instagram-dm-automation-safe\">is Instagram DM "
         "automation safe?</a></p>"),
    ],
    "faq": [
        ("Is there a completely free Instagram auto DM tool?", "Yes. {brand}'s free plan is free forever with 1,000 DMs a month and no card. "
         "LinkDM, ReplyKaro, InstantDM and ReplyRush also have free plans."),
        ("Can I auto DM for free without a business account?", "You need a Creator or Business account, which is free to switch to in Instagram's settings."),
        ("Does Instagram itself offer free auto DMs?", "Instagram and Meta Business Suite have basic automated replies for messages. For comment-to-DM "
         "with keywords, follow gates and lead capture, creators use a tool on the official API."),
        ("What happens when I hit 1,000 DMs?", "New DMs pause until the next month, or you can upgrade any time. Your automations and data stay."),
        ("Is the follow gate free?", "Follow to unlock is on Starter (₹149 a month) and above."),
    ],
}

MANYCHAT_INR = {
    "title": "ManyChat pricing in India (in ₹) and cheaper options",
    "description": "What ManyChat costs in rupees for Indian Instagram creators, how its contact-based pricing grows, and cheaper flat-price alternatives.",
    "answer": "ManyChat's Pro plan starts at about $17 a month (checked November 2026), roughly ₹1,450 at ₹85 to the dollar, before forex "
              "charges on Indian cards. The price rises with your number of active contacts, and AI features cost extra. Indian Instagram "
              "tools are usually ₹99–₹499 a month; {brand} is ₹149, or ₹199 with no DM cap and AI replies included.",
    "sections": [
        ("ManyChat's price in rupees",
         "<div class=\"scroll\"><table><thead><tr><th></th><th>In dollars</th><th>In rupees (at ₹85 = $1)</th></tr></thead><tbody>"
         "<tr><td>Free plan</td><td>$0, small contact limit</td><td>₹0</td></tr>"
         "<tr><td>Pro, entry tier</td><td>About $17 a month</td><td>About ₹1,450 a month</td></tr>"
         "<tr><td>Pro, larger contact tiers</td><td>Rises with active contacts</td><td>Rises with active contacts</td></tr>"
         "<tr><td>AI features</td><td>Extra</td><td>Extra</td></tr>"
         "</tbody></table></div>"
         "<p class=\"note\">ManyChat prices from its public pricing page, checked November 2026. The exchange rate and ManyChat's prices "
         "change; use its pricing calculator for your contact count.</p>"),
        ("Why the bill grows",
         "<p>ManyChat counts <b>active contacts</b>: people who interacted with your account through ManyChat. For an Instagram creator, every "
         "person who comments your keyword and gets a DM becomes a contact. A reel that gets 10,000 keyword comments can add 10,000 contacts in "
         "a few days, which can move you up the pricing tiers. The more successful your reels, the more you pay.</p>"),
        ("Costs Indian creators often miss",
         "<ul><li><b>Forex markup.</b> Indian cards usually add a foreign-currency charge on dollar payments, often a few percent.</li>"
         "<li><b>GST and invoices.</b> Check whether you get an invoice that works for your GST filing.</li>"
         "<li><b>Card-only billing.</b> UPI isn't an option for dollar subscriptions on most tools.</li>"
         "<li><b>AI as an add-on</b> if you want automatic answers to DMs.</li></ul>"),
        ("Flat-price alternatives in ₹",
         "<div class=\"scroll\"><table><thead><tr><th>Tool</th><th>Price a month</th><th>Notes</th></tr></thead><tbody>"
         "<tr><td>{brand}</td><td>₹149 / ₹199</td><td>Flat; no DM cap and 300 AI replies on ₹199; UPI, GST included</td></tr>"
         "<tr><td>ReplyKaro</td><td>About ₹99</td><td>Basic comment-to-DM</td></tr>"
         "<tr><td>Repli</td><td>₹249</td><td>Adds WhatsApp and a CRM</td></tr>"
         "<tr><td>SuperProfile</td><td>About ₹499</td><td>Creator store with AutoDM; fee on sales</td></tr>"
         "</tbody></table></div><p class=\"note\">Checked November 2026. See <a href=\"/guides/manychat-alternatives\">all ManyChat alternatives</a>.</p>"),
        ("A year of costs, side by side",
         "<div class=\"scroll\"><table><thead><tr><th></th><th>ManyChat Pro (entry tier)</th><th>{brand} Creator</th></tr></thead><tbody>"
         "<tr><td>Monthly</td><td>About ₹1,450 + forex</td><td>₹199</td></tr>"
         "<tr><td>Yearly</td><td>About ₹17,400 + forex, more as contacts grow</td><td>₹1,999 (paid yearly)</td></tr>"
         "<tr><td>AI replies</td><td>Extra</td><td>300 a month included</td></tr>"
         "</tbody></table></div>"),
        ("How to estimate your own bill",
         "<ol><li>Look at your last 3 keyword reels and add up the comments that used the keyword. Each of those people becomes a contact.</li>"
         "<li>Add the people who DMed you or replied to your stories in the same period.</li>"
         "<li>Enter that number in ManyChat's pricing calculator to see your tier, and multiply the dollar price by today's rate plus your "
         "card's forex charge.</li>"
         "<li>Do the same for a month where a reel went viral. That's the bill to plan for, not the quiet month.</li></ol>"
         "<p>With a flat-price tool the calculation is simpler: the plan price, whatever happens. On {brand}, Creator is ₹199 a month or "
         "₹1,999 a year with GST included, and Pro (₹599) adds 3 accounts and Claude. The free plan covers 1,000 DMs a month if you want "
         "to compare both tools on the same reel first.</p>"),
        ("Moving from ManyChat to a ₹ plan",
         "<p>Most Instagram creator setups in ManyChat are a few keyword automations. Recreate each one in {brand} (pick the reel, add the "
         "keyword, paste the DM and links), switch it on, then switch off the ManyChat automation for that reel so nobody gets two DMs. "
         "There's nothing to migrate on Instagram's side: both tools connect through Meta's official login.</p>"),
        ("When ManyChat is still worth it",
         "<p>If you run automations across Instagram, Messenger, WhatsApp and Telegram, need complex flows with conditions and custom fields, or "
         "your agency already builds in ManyChat, the higher price can be worth it. For Instagram-only creators who mainly need comment-to-DM, "
         "a follow gate and lead capture, a flat-price tool does the same job for much less. Compare in detail: <a href=\"/vs/manychat\">{brand} vs ManyChat</a>.</p>"),
    ],
    "faq": [
        ("How much is ManyChat per month in India?", "About $17 a month for the entry Pro tier (checked November 2026), roughly ₹1,450, plus forex "
         "charges, and more as your active contacts grow."),
        ("Can I pay ManyChat with UPI?", "ManyChat bills in dollars by card. Indian tools like {brand} accept UPI with GST included."),
        ("Is there a cheaper ManyChat alternative in India?", "Yes. {brand} is ₹149–₹199 a month flat, ReplyKaro about ₹99, Repli ₹249."),
        ("Does ManyChat charge more when a reel goes viral?", "Its price depends on active contacts, so a reel that brings thousands of new contacts can move you to a higher tier."),
    ],
}

TPL = [
    ("Public replies to comments (rotate 3)", [
        "@{username} Check your DM 📩", "Sent! Inbox check karo 📥", "Done ✅ DM mein bhej diya",
        "@{username} it's in your DMs 🎁", "On its way to your inbox ✨"]),
    ("Opening message with a button", [
        "Hey {username}! 👋 Thanks for commenting. Tap below and I'll send it right away ✨ [Send me the access]",
        "Hi {username}! Guide ready hai 🔥 Neeche button dabao [Send it]",
        "{Hey|Hi} {username}! Your freebie is one tap away 👇 [Get it]"]),
    ("Follow to unlock", [
        "Almost there! 👀 Please visit my profile and tap Follow, then tap the button below. [Visit Profile] [I'm following ✅]",
        "Bas ek step 👀 Profile pe jaake Follow karo, phir neeche button dabao. [Visit Profile] [Follow kar liya ✅]"]),
    ("Asking for an email or WhatsApp number", [
        "One last step ✉️ Reply with your email and I'll send it right away.",
        "Apna email bhejo, guide turant aa jayegi 📩",
        "Reply with your WhatsApp number and I'll add you to the free class group 📱"]),
    ("The main DM with the link", [
        "Here's your guide 🎁 Tap below to open it. [Open the guide]",
        "Ye lo tumhari free guide 🎁 Kuch bhi doubt ho toh yahin poochna. [Open]",
        "Here are all 39 prompts 🔥 Save this chat so you don't lose them. [Get the prompts] [Watch the tutorial]",
        "Recipe yahan hai 👇 Bana ke tag karna, I'll repost! [Full recipe]"]),
    ("Follow-up offers (1–20 hours later)", [
        "Prompts try kiye {username}? 🙌 The full pack with the master guide is just ₹149 today. [Get the full pack]",
        "Did the plan help? If you want me to build one around your schedule, coaching starts at ₹1,999/month. [See coaching]",
        "Early-bird price sirf aaj raat tak hai ⏳ Seat book kar lo! [Join now]",
        "Webinar 7 baje start ho raha hai 🎥 Ye raha joining link, see you there! [Join the webinar]",
        "Liked the free guide? The full course goes step by step, with templates. Want a look inside? [See the course]"]),
    ("Story replies and mentions", [
        "Here's the link from my story 👇 [Open link]",
        "Thank you so much for the shoutout {username}! 🙏 Here's 10% off as a thank-you: THANKS10",
        "Thanks for voting! 🗳️ Here's the template I promised. [Get the template]",
        "Aaj ka offer sirf 24 ghante ke liye hai ⏳ Yahan dekho 👇 [See the offer]"]),
    ("Welcome message for new DMs", [
        "Hi {username}! 👋 What can I help with? [Free guides] [My course] [Work with me]",
        "Hey! Thanks for messaging 🙌 Pick one below, or type your question and I'll reply soon. [Prices] [Free stuff]"]),
    ("Choice menus", [
        "What are you working on? [Just starting] [Stuck on growth] [Ready to work together]",
        "Kaunsa chahiye? [Skincare] [Makeup] [Outfit]",
        "Which class? [Class 10] [Class 12] [Competitive exams]"]),
]

TEMPLATES = {
    "title": "Instagram DM templates: 30+ auto DM messages to copy",
    "description": "Copy-paste Instagram DM templates for comment replies, opening messages, follow to unlock, email capture, links, follow-ups, stories and menus, in English and Hinglish.",
    "answer": "Good Instagram auto DM templates are short, say exactly what the person gets, and put the link on a button. Below are 30+ "
              "messages to copy for every step: public comment replies, opening messages, follow to unlock, email and WhatsApp capture, "
              "the main DM, follow-up offers, story replies, welcome messages and choice menus, in English and Hinglish.",
    "sections": [
        ("How to use these templates",
         "<ul><li><code>{username}</code> is replaced with the person's Instagram name.</li>"
         "<li><code>{Hi|Hey|Hello}</code> picks one option per person, so not everyone gets the same text. Instagram is less likely to treat "
         "varied messages as spam.</li>"
         "<li>Text in [square brackets] is a button. Keep button text under 20 characters.</li>"
         "<li>Keep messages under 3 short lines. Most people read DMs on a lock screen.</li></ul>")]
    + [(heading, "<ul>" + "".join(f"<li><code>{t}</code></li>" for t in items) + "</ul>") for heading, items in TPL]
    + [("Put a template to work",
        "<p>In {brand}, create an automation and paste the templates into each step: public replies on the keyword step, then the opening "
        "message, follow gate, email question and main DM on the DMs step, and the follow-up at the bottom. The review step shows the whole "
        "conversation before you launch.</p>"
        + fig("wizard-review", "Review screen showing a full automated DM conversation built from templates", "Each template in place, previewed before launch.", WIZ)),
       ("Mistakes that make DMs feel spammy",
        "<ul><li>Long paragraphs before the link. Deliver first, explain later.</li>"
        "<li>The same long message to thousands of people. Use variations.</li>"
        "<li>Asking for a follow, an email <i>and</i> a WhatsApp number for a small freebie. Ask for one thing.</li>"
        "<li>A follow-up that just repeats the first DM. Make it a new offer or a useful next step.</li>"
        "<li>ALL CAPS and too many emojis.</li></ul>")],
    "faq": [
        ("Can I use these templates in any tool?", "Yes. The text works anywhere; {username} and {Hi|Hey} variations are {brand} features, so other tools may use different placeholders."),
        ("Should I write DMs in English or Hinglish?", "Match how you speak in your reels. Many Indian creators get more replies with Hinglish."),
        ("How long should an auto DM be?", "One to three short lines plus a button. Put details on the page the button opens."),
        ("Can the AI write replies for me?", "For questions people ask after the link, yes: the AI DM agent answers from your FAQ in the person's language."),
    ],
}

NEW_GUIDES = {"free-instagram-auto-dm": FREE, "manychat-pricing-india": MANYCHAT_INR, "instagram-dm-templates": TEMPLATES}

# ---------------------------------------------------------------- Meta Business Suite comparison

META = {
    "name": "Meta Business Suite",
    "title": "Meta Business Suite auto reply vs a DM automation tool",
    "description": "Meta Business Suite's free Instagram automated replies compared with {brand}: comment-to-DM, follow to unlock, lead capture and AI.",
    "answer": "Meta Business Suite is Meta's free tool for managing Facebook and Instagram messages. Its automated responses cover basics "
              "such as instant replies, away messages and FAQ answers. {brand} is built for creators who grow and sell through comments: "
              "keyword comment-to-DM on any reel, follow to unlock, email and WhatsApp capture, follow-ups, an AI agent and sales per reel.",
    "them": ["Free, made by Meta", "One inbox for Facebook and Instagram messages", "Basic automated responses: instant reply, away message, FAQs",
             "Good for answering messages by hand"],
    "us": ["Keyword comment-to-DM on any reel, all posts or the next post", "Follow to unlock, email and WhatsApp capture", "Follow-ups, broadcasts, up to 3 buttons, menus",
           "AI agent answers in any language", "Reel report and sales per automation"],
    "choose_them": "you mainly answer messages yourself and want Meta's free inbox for Facebook and Instagram together.",
    "choose_us": "you use reels with a comment keyword to grow followers, collect leads or sell, and want that to run on its own.",
    "sections": [
        ("What Meta Business Suite automates",
         "<p>In Meta Business Suite's inbox you can set up automated responses for Instagram and Facebook messages, such as an instant reply "
         "to a first message, an away message outside your hours and answers to frequently asked questions. It's free, made by Meta and fine "
         "for businesses that mostly answer DMs by hand. Meta adds features over time, so check the Automations section in your account for "
         "what's available to you (checked November 2026).</p>"),
        ("What creators need that it doesn't cover",
         "<div class=\"scroll\"><table><thead><tr><th>Need</th><th>Meta Business Suite</th><th>{brand}</th></tr></thead><tbody>"
         "<tr><td>DM everyone who comments a keyword on a reel</td><td>Not a core feature when checked</td><td>Yes, any reel, all posts or the next post</td></tr>"
         "<tr><td>Only send the link to followers</td><td>Not built in</td><td>Yes (Starter+)</td></tr>"
         "<tr><td>Collect emails and WhatsApp numbers into a list</td><td>Not built in</td><td>Yes, with CSV and webhook export</td></tr>"
         "<tr><td>Follow-up offer hours later</td><td>Not built in</td><td>Yes</td></tr>"
         "<tr><td>AI answers from your FAQ in any language</td><td>FAQ answers to set questions</td><td>Yes, free-text questions, with hand-off</td></tr>"
         "<tr><td>Which reel brought followers and sales</td><td>Not built in</td><td>Yes, reel report and sales tracking</td></tr>"
         "<tr><td>Price</td><td>Free</td><td>Free for 1,000 DMs; from ₹149</td></tr>"
         "</tbody></table></div>"),
        ("Can you use both?",
         "<p>Yes. Both connect to Instagram through Meta's official systems. Many creators keep Meta Business Suite for ads and the shared inbox, "
         "and use {brand} for comment automations and the AI agent. Avoid setting an instant reply in both, or new messages get two answers.</p>"
         + fig("ai-inbox", "ReplyInbox AI Inbox with conversations handled by the AI and ones that need the creator",
               "{brand}'s AI Inbox: the AI answers, and hands the rest to you.")),
        ("Which one to pick",
         "<ul><li><b>Meta Business Suite</b> if you answer most DMs yourself, run Facebook and Instagram together and only need a greeting and away message.</li>"
         "<li><b>{brand}</b> if your reels ask people to comment a keyword, you want followers and leads from that, and you want the DMs "
         "after it answered in Hinglish or any language without you.</li></ul>"
         "<p>Start free: {brand}'s free plan includes 1,000 DMs a month. See <a href=\"/guides/free-instagram-auto-dm\">free Instagram auto DM options</a>.</p>"),
    ],
    "faq_extra": [
        ("Is Meta Business Suite auto reply free?", "Yes, it's free. It covers basic automated responses; keyword comment-to-DM, follow gates and lead capture need a tool like {brand}."),
        ("Will using {brand} affect Meta Business Suite?", "No. Both use Meta's official systems. Just don't set an instant reply in both tools."),
    ],
}

NEW_COMPARE = {"meta-business-suite": META}
