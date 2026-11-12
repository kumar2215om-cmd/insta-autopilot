"""Public pages written to rank on Google (SEO), be quoted in answer boxes (AEO) and be cited by AI assistants (GEO).

Every page has: a direct answer in the first paragraph, short sections with clear headings, a FAQ (also sent as
FAQPage structured data) and an "updated" date. Competitor facts are dated, hedged and linked to where they were
checked; update them when competitors change prices. "{brand}" is replaced with the brand name when rendering.
"""

UPDATED = "2026-11-12"
CHECKED = "November 2026"

# ---------- feature pages: /features/<slug> ----------

FEATURES = {
    "comment-to-dm": {
        "title": "Instagram comment-to-DM automation",
        "h1": "Comment-to-DM: send a DM to everyone who comments your keyword",
        "description": "Automatically DM everyone who comments a keyword on your Instagram reel or post. Free plan with 1,000 DMs a month, official Meta API.",
        "answer": "Comment-to-DM automation sends an Instagram DM to every person who comments a chosen keyword (for example GUIDE) "
                  "on your reel or post, usually with a link, and can reply to the comment publicly. {brand} does this on the "
                  "official Meta API, on any post or only your next one, with 1,000 DMs a month free.",
        "sections": [
            ("How it works", "<ol><li>Pick the post or reel (or <b>any post</b>, or <b>your next post</b> before you publish it).</li>"
             "<li>Choose a keyword such as <code>GUIDE</code>. Plurals, capitals and emojis around it still match.</li>"
             "<li>Write the public reply (it rotates between up to 3 versions) and the DM with your link or button.</li>"
             "<li>Turn it on. Every matching comment gets a reply and a DM within seconds, 24/7.</li></ol>"),
            ("What you can add", "<ul><li><b>Follow to unlock</b>: the link is sent only after they follow you.</li>"
             "<li><b>Email or WhatsApp capture</b> before the link.</li><li><b>Choice menu</b>: up to 3 options, each with its own message.</li>"
             "<li><b>Follow-up offer</b> a few hours later (your paid product).</li><li><b>Message variations</b> like {Hi|Hey} so DMs don't look identical.</li>"
             "<li><b>Delay, once per person, excluded words</b> and a schedule.</li></ul>"),
            ("Why creators use it", "<p>Asking people to comment a keyword boosts the reel's engagement, and the DM turns that "
             "attention into followers, leads and sales. With click counting and sales tracking, {brand} shows which reel actually made money.</p>"),
        ],
        "faq": [
            ("Is comment-to-DM allowed by Instagram?", "Yes, when it uses Meta's official Instagram API. Instagram allows one private reply "
             "per comment within 7 days of the comment. {brand} uses the official API and never asks for your password."),
            ("Does it work on reels, posts and Lives?", "Yes. Reels and posts, comments on your Live, story replies and story mentions."),
            ("How many DMs can I send for free?", "1,000 DMs a month on the free plan. Paid plans have no {brand} limit; Instagram's own hourly limits still apply."),
        ],
    },
    "follow-to-unlock": {
        "title": "Follow to unlock: only send the link to followers",
        "h1": "Follow to unlock: turn commenters into followers before you send the link",
        "description": "Gate your Instagram freebie behind a follow. {brand} checks they follow you before sending the link, using the official API.",
        "answer": "Follow to unlock (also called a follow gate) means your DM link is sent only after the person follows you. "
                  "{brand} sends a short DM with a Visit profile button and an I'm following button, checks the follow through "
                  "Instagram's official API, then sends the link.",
        "sections": [
            ("How the follow check works", "<p>Instagram only lets apps check a follow after the person replies in the DM, so the "
             "first DM has a button. When they tap it, {brand} checks the follow. Followers get the link; others get a friendly "
             "\"follow first\" message with a button to try again.</p>"),
            ("Results", "<p>Creators typically see a big jump in followers from reels that use a keyword plus a follow gate, because "
             "the audience is already interested. {brand} counts follows won per automation and per reel.</p>"),
        ],
        "faq": [
            ("Can Instagram see that I use a follow gate?", "It runs on the official API with normal DMs and buttons, so it is within Instagram's rules."),
            ("Which plan includes follow to unlock?", "Starter and above. During the beta every feature is free."),
        ],
    },
    "ai-dm-agent": {
        "title": "AI that answers Instagram DMs in any language",
        "h1": "An AI agent that answers your Instagram DMs, in their language",
        "description": "An AI DM agent for Instagram that answers from your FAQ and products in the fan's language and hands refunds and collabs to you.",
        "answer": "{brand}'s AI DM agent answers Instagram DMs that don't match a keyword, using only your FAQ, products and links, "
                  "in the language the person writes in (English, Hindi, Spanish, Hinglish and more). Anything it isn't sure "
                  "about, like refunds or brand deals, is handed to you with a suggested reply.",
        "sections": [
            ("What it does", "<ul><li>Answers prices, links, how-to questions from your own FAQ.</li><li>Never invents prices or links.</li>"
             "<li>Hands over refunds, collabs and anything unclear, with the reason and a suggested reply.</li>"
             "<li>Works with keywords: keyword DMs still run as automations.</li></ul>"),
            ("Included AI replies", "<p>300 AI replies a month on Creator, 2,000 on Pro, 25 to try on Free. Extra replies are sold "
             "in packs of 1,000. No separate AI credit wallet to manage.</p>"),
        ],
        "faq": [
            ("Which AI model does it use?", "Anthropic's Claude, through the API. Conversations are not used to train the model."),
            ("Can I see and edit what the AI says?", "Yes. The AI Inbox shows every chat; you can reply yourself, and the AI stays quiet until you hand it back."),
        ],
    },
    "story-replies": {
        "title": "Instagram story reply and mention automation",
        "h1": "Auto-reply to Instagram story replies and mentions",
        "description": "Send a DM automatically when someone replies to your story or mentions you in theirs. Keywords, links and thank-you messages.",
        "answer": "Story automation sends a DM when someone replies to your Instagram story (optionally only with a keyword) or "
                  "mentions you in their story. {brand} handles both, so story links and thank-you messages go out instantly.",
        "sections": [
            ("Story replies", "<p>Add a keyword sticker idea to your story (\"reply LINK\"), and everyone who replies gets the link in "
             "seconds. Or reply to every story reply with the same message.</p>"),
            ("Story mentions", "<p>When someone mentions you in their story, thank them automatically, or send a discount code. It builds goodwill and more mentions.</p>"),
        ],
        "faq": [("Is it free?", "Yes, story replies and mentions are on every plan, including Free.")],
    },
    "lead-capture": {
        "title": "Collect emails and WhatsApp numbers in Instagram DMs",
        "h1": "Collect emails and WhatsApp numbers from Instagram DMs",
        "description": "Ask for an email or WhatsApp number in the DM before sending the link. Leads go to Contacts, CSV, Google Sheets or webhooks.",
        "answer": "{brand} can ask for an email address or WhatsApp number inside the Instagram DM before it sends your link. "
                  "The answer is checked, saved to Contacts with tags, and can be sent to Google Sheets or any webhook.",
        "sections": [
            ("How it works", "<p>Turn on \"ask for email\" or \"ask for WhatsApp\" in the automation. The DM asks, checks the format, "
             "asks again if it's wrong, and then sends the link. You can make it required or offer a Skip button.</p>"),
            ("Where leads go", "<ul><li>Contacts with tags (for example <i>prompts-lead</i>).</li><li>CSV export.</li>"
             "<li>Google Sheets, Zapier, Make or your own webhook (Pro).</li><li>A phone notification for every new lead.</li></ul>"),
        ],
        "faq": [("Does Instagram allow collecting emails in DMs?", "Yes, when the person types it themselves in reply to your message, as here.")],
    },
    "sales-tracking": {
        "title": "See which Instagram reel makes money",
        "h1": "Sales tracking: see which reel and DM made each sale",
        "description": "Track sales from Instagram DMs back to the exact reel and automation. Works with Razorpay, Instamojo and other payment pages.",
        "answer": "{brand} credits each sale to the Instagram reel and DM automation that brought the buyer. Links in DMs count "
                  "their clicks, and your payment page redirects to a {brand} sales link after payment, so you see ₹ or $ revenue per reel.",
        "sections": [
            ("Set up in two minutes", "<ol><li>Add your product and price on the Sales page.</li><li>Paste its sales link as your "
             "payment page's \"redirect after payment\" (Razorpay Payment Pages, Instamojo and most others have it).</li>"
             "<li>Keep using your normal link in DMs. Sales now show per automation and per reel.</li></ol>"),
            ("Also included", "<ul><li>Click counts on every DM link.</li><li>Automatic UTM tags for Google Analytics and Shopify.</li>"
             "<li>A notification for every sale.</li></ul>"),
        ],
        "faq": [("Do you see my customers' payment details?", "No. {brand} only receives that a sale happened (product, price, automation), never card or UPI details.")],
    },
}

# ---------- comparison pages: /vs/<slug> ----------
# Facts about other tools come from their pages or public reviews, checked in CHECKED. Keep them neutral and dated.

COMPARE = {
    "manychat": {
        "name": "ManyChat",
        "title": "ManyChat alternative for Instagram",
        "description": "{brand} vs ManyChat for Instagram DM automation: pricing, AI, follow gate and sales tracking compared.",
        "answer": "ManyChat is a powerful multi-channel chatbot builder priced by active contacts (from about $17/month, AI on "
                  "higher plans). {brand} is focused on Instagram creators: flat pricing from ₹199 / $9 a month, AI replies "
                  "included, follow to unlock, email and WhatsApp capture, and sales tracking per reel.",
        "them": ["Visual flow builder for complex chatbots", "Instagram, Messenger, WhatsApp, TikTok, Telegram",
                 "Pricing by active contacts; costs grow with your audience", "AI features on higher plans"],
        "us": ["Simple 4-step Auto DM builder made for creators", "Instagram-first, with AI replies included",
               "Flat price, no per-contact charges", "Sales per reel, click counts, UTM tags", "Pricing in ₹ and $"],
        "choose_them": "you need one bot across many messaging channels or very complex flows.",
        "choose_us": "you're a creator or coach on Instagram who wants comment-to-DM, a follow gate, leads and sales without per-contact pricing.",
    },
    "linkdm": {
        "name": "LinkDM",
        "title": "LinkDM alternative",
        "description": "{brand} vs LinkDM: free plan, pricing, follow gate, AI replies and sales tracking for Instagram DMs.",
        "answer": "LinkDM is a popular Instagram comment-to-DM tool with a free plan (about 1,000 DMs a month with LinkDM branding) "
                  "and Pro from about $19/month. {brand} offers the same core automation plus an AI DM agent, choice menus and "
                  "sales tracking, from ₹199 / $9 a month.",
        "them": ["Comment-to-DM and story automations", "Lead forms to email tools", "Pro from about $19/month for up to 3 accounts",
                 "Follow check on Pro"],
        "us": ["AI DM agent included (300 replies on Creator)", "Choice menus, follow-ups and broadcasts", "Sales per reel",
               "Creator at ₹199 / $9 a month"],
        "choose_them": "you want a well-known, simple comment-to-DM tool and send very high volumes on one plan.",
        "choose_us": "you also want AI replies, follow-ups and to see which reel makes money, at a lower price.",
    },
    "superprofile": {
        "name": "SuperProfile AutoDM",
        "title": "SuperProfile AutoDM alternative",
        "description": "{brand} vs SuperProfile AutoDM: pricing, platform fees, AI replies and features compared.",
        "answer": "SuperProfile combines a creator store with AutoDM; its Creator plan is about ₹499 a month in India, and it "
                  "charges a platform fee on sales (around 5% + GST, as seen on its payment dashboard). {brand} is a dedicated "
                  "DM automation tool from ₹199 a month with AI replies included and sales tracking that works with any payment page.",
        "them": ["Store, courses and payment pages in one place", "AutoDM on the paid plan", "Platform fee on each sale"],
        "us": ["Deeper DM automation: menus, follow-ups, broadcast, AI agent", "Works with your existing payment page",
               "Creator at ₹199 a month", "No fee on sales made on your own payment page"],
        "choose_them": "you want your store, course hosting and DMs in one product.",
        "choose_us": "you already sell somewhere and want the best Instagram DM automation for less.",
    },
    "repli": {
        "name": "Repli",
        "title": "Repli alternative",
        "description": "{brand} vs Repli for Instagram: plans, AI credits, story replies and pricing compared.",
        "answer": "Repli covers Instagram and WhatsApp: its Creator plan (₹249) is comment-to-DM only, and Pro (₹499) adds story "
                  "replies, lead forms, follow-ups and broadcasts, with AI sold as separate credits. {brand}'s Creator plan "
                  "(₹199) already includes story replies, follow-ups, broadcasts and 300 AI replies.",
        "them": ["Instagram and WhatsApp automation, CRM and Shopify plans", "Creator ₹249 (comment-to-DM only)",
                 "Pro ₹499; AI replies bought as credits", "Extra Instagram account ₹249 a month"],
        "us": ["Creator ₹199 with story replies, follow-ups, broadcast", "AI replies included in the plan",
               "Pro ₹499 with 3 accounts and 2,000 AI replies", "Extra account ₹149 a month"],
        "choose_them": "you need WhatsApp campaigns and a CRM together with Instagram.",
        "choose_us": "Instagram is your main channel and you want more included for less.",
    },
    "replykaro": {
        "name": "ReplyKaro",
        "title": "ReplyKaro alternative",
        "description": "{brand} vs ReplyKaro: Instagram auto DM pricing in India, features and AI compared.",
        "answer": "ReplyKaro is a low-cost Indian auto DM tool (free plan with about 1,000 DMs, paid plans from about ₹99 a month). "
                  "{brand} costs a little more (₹199) but adds an AI DM agent, follow-ups, choice menus, broadcasts and sales tracking per reel.",
        "them": ["Very low entry price (about ₹99)", "Comment-to-DM and story replies", "UPI billing in India"],
        "us": ["AI DM agent included", "Follow-up offers, menus, broadcast", "Sales per reel and insights", "Phone app with alerts"],
        "choose_them": "you only need basic comment-to-DM at the lowest possible price.",
        "choose_us": "you sell products or courses and want automation that also makes and measures money.",
    },
    "instantdm": {
        "name": "InstantDM",
        "title": "InstantDM alternative",
        "description": "{brand} vs InstantDM: plans, AI replies, follow-ups and pricing for Instagram DM automation.",
        "answer": "InstantDM offers a free plan (about 500 DMs a month) and paid plans from about $9.99 a month, with follow-ups "
                  "on its higher plan. {brand} includes follow-ups, broadcasts and AI replies from $9 / ₹199 a month.",
        "them": ["Free plan around 500 DMs a month", "Paid from about $9.99/month", "Follow-ups and API on the higher plan"],
        "us": ["Free plan with 1,000 DMs a month", "Follow-ups, menus and broadcast on Creator", "AI replies included", "₹ and $ pricing"],
        "choose_them": "you prefer its interface or need its API on the higher plan.",
        "choose_us": "you want more included on the free and entry plans.",
    },
}

# ---------- guides: /guides/<slug> ----------

GUIDES = {
    "how-to-auto-dm-instagram-comments": {
        "title": "How to auto DM people who comment on your Instagram reel",
        "description": "Step-by-step: send an automatic DM to everyone who comments a keyword on your Instagram reel, for free.",
        "answer": "To auto DM everyone who comments on your reel: connect your Instagram professional account to a comment-to-DM "
                  "tool that uses Meta's official API (like {brand}), pick the reel, set a keyword such as GUIDE, write the DM "
                  "with your link, and turn it on. Every matching comment then gets a DM within seconds.",
        "sections": [
            ("What you need", "<ul><li>An Instagram <b>Business or Creator</b> account (free to switch in Settings).</li>"
             "<li>A tool on Meta's official API. Avoid tools that ask for your password.</li><li>A freebie or link worth commenting for.</li></ul>"),
            ("Steps", "<ol><li>Log in to {brand} with Instagram.</li><li>Auto DM → Create automation → Comments on your post or reel.</li>"
             "<li>Pick the reel (or <i>next post</i> if it's not live yet).</li><li>Add the keyword and 2–3 public replies.</li>"
             "<li>Write the DM, add a button with your link, and optionally ask them to follow first.</li><li>Review and launch.</li></ol>"),
            ("Tips that raise results", "<ul><li>Say the keyword in the first 3 seconds of the reel and in the caption.</li>"
             "<li>Use a single short word (GUIDE, LINK, PROMPTS).</li><li>Add a follow gate to grow followers.</li>"
             "<li>Send a follow-up offer a few hours later.</li><li>Check which reel brought sales and repeat that format.</li></ul>"),
        ],
        "faq": [("Is it free?", "Yes, {brand}'s free plan includes 1,000 DMs a month."),
                ("Will my account get banned?", "Tools on the official API, with natural message variations and Instagram's limits respected, are within the rules.")],
    },
    "instagram-dm-automation-pricing": {
        "title": "Instagram DM automation pricing compared (2026)",
        "description": "What Instagram DM automation tools cost in 2026: ManyChat, LinkDM, InstantDM, SuperProfile, Repli, ReplyKaro and {brand}.",
        "answer": "Instagram DM automation in 2026 costs from free (500–1,500 DMs a month) to about $9–$40 a month for "
                  "creator plans. Indian tools are typically ₹99–₹499 a month. {brand} is free for 1,000 DMs a month and "
                  "₹199 / $9 a month for unlimited DMs with AI replies included.",
        "sections": [
            ("Typical prices (checked " + CHECKED + ")", "<table><thead><tr><th>Tool</th><th>Free plan</th><th>Entry paid plan</th></tr></thead><tbody>"
             "<tr><td>ManyChat</td><td>Small contact limit</td><td>About $17/month, priced by contacts</td></tr>"
             "<tr><td>LinkDM</td><td>About 1,000 DMs</td><td>About $19/month</td></tr>"
             "<tr><td>InstantDM</td><td>About 500 DMs</td><td>About $9.99/month</td></tr>"
             "<tr><td>SuperProfile AutoDM</td><td>Limited</td><td>About ₹499/month + fee on sales</td></tr>"
             "<tr><td>Repli</td><td>1 automation</td><td>₹249/month (comment-to-DM only)</td></tr>"
             "<tr><td>ReplyKaro</td><td>About 1,000 DMs</td><td>About ₹99/month</td></tr>"
             "<tr><td><b>{brand}</b></td><td><b>1,000 DMs</b></td><td><b>₹199 / $9 a month, AI included</b></td></tr></tbody></table>"
             "<p class=\"note\">Prices change often. Check each tool's pricing page before buying.</p>"),
            ("How to compare", "<ul><li><b>Per-contact pricing</b> gets expensive when a reel goes viral; flat pricing doesn't.</li>"
             "<li>Check whether <b>AI replies</b> are included or sold as credits.</li><li>Check if the <b>follow gate</b> and "
             "<b>story replies</b> are on the plan you're buying.</li><li>Check for <b>fees on sales</b>.</li></ul>"),
        ],
        "faq": [("What is the cheapest Instagram auto DM tool?", "Several tools have free plans (500–1,500 DMs a month). For unlimited DMs, Indian tools start around ₹99–₹249 a month; {brand} is ₹199 with AI replies included.")],
    },
    "is-instagram-dm-automation-safe": {
        "title": "Is Instagram DM automation safe for your account?",
        "description": "Will Instagram ban you for auto DMs? How official-API tools work, Instagram's limits, and how to stay safe.",
        "answer": "Instagram DM automation is safe when it runs on Meta's official Instagram API, never asks for your password, "
                  "and respects Instagram's limits (one private reply per comment within 7 days, other DMs within 24 hours of "
                  "the person's last message, and hourly rate limits). Tools that log in with your password break the rules.",
        "sections": [
            ("Safe vs unsafe tools", "<ul><li><b>Safe</b>: you log in with Instagram's official login screen; the tool gets a token, not your password.</li>"
             "<li><b>Unsafe</b>: browser bots or apps that ask for your password, mass-DM strangers or scrape followers.</li></ul>"),
            ("How {brand} keeps accounts safe", "<ul><li>Official Meta API only.</li><li>Message variations like {Hi|Hey}.</li>"
             "<li>Waits and resumes automatically when Instagram slows DMs.</li><li>Alerts you if anything goes wrong.</li></ul>"),
        ],
        "faq": [("Can Instagram ban me for comment-to-DM?", "Not for using an official-API tool within the limits. Spammy content or password-based bots are what get accounts restricted.")],
    },
    "get-followers-from-reels": {
        "title": "How to turn reel views into followers with comment-to-DM",
        "description": "A simple system to convert reel viewers into followers: keyword in the reel, follow gate in the DM, follow-up later.",
        "answer": "To turn reel views into followers, ask viewers to comment a keyword for a freebie, then send the freebie by DM "
                  "only after they follow you (a follow gate). Interested viewers follow to get it, and the comments also boost the reel.",
        "sections": [
            ("The system", "<ol><li>Make a reel that promises something specific (a guide, template or list).</li>"
             "<li>Say \"comment GUIDE and I'll DM it to you\" early, and put it in the caption.</li>"
             "<li>Set up comment-to-DM with follow to unlock.</li><li>Send a follow-up offer 3 hours later.</li>"
             "<li>Check follows per 1,000 views in the reel report; repeat what works.</li></ol>"),
        ],
        "faq": [("How many followers can I expect?", "It depends on the reel and the offer; {brand}'s reel report shows follows per 1,000 views so you can compare reels.")],
    },
}


# ---------- more comparisons ----------

COMPARE.update({
    "replyrush": {
        "name": "ReplyRush",
        "title": "ReplyRush alternative",
        "description": "{brand} vs ReplyRush: free plan, DM limits, follow gate, AI replies and pricing compared.",
        "answer": "ReplyRush prices by DM volume: a free plan of about 1,500 DMs a month (follow gate, comment replies and email "
                  "capture are on paid plans), then about $10 for 7,500 DMs and $25 for 40,000. {brand} gives 1,000 free DMs and "
                  "unlimited DMs from ₹199 / $9, with the follow gate from Starter and AI replies on Creator.",
        "them": ["Generous free DM count (about 1,500 a month)", "Paid plans capped by DM volume", "Instagram and Facebook",
                 "Follow gate and email capture on paid plans"],
        "us": ["No DM cap on Creator and above", "AI replies included", "Follow-ups, menus, broadcast", "Sales tracking per reel"],
        "choose_them": "you need Facebook automation too, or the most free DMs with basic replies.",
        "choose_us": "you expect a reel to go viral and don't want a DM cap, or you want AI replies and sales tracking.",
    },
    "creatorflow": {
        "name": "CreatorFlow",
        "title": "CreatorFlow alternative",
        "description": "{brand} vs CreatorFlow: free plan, DM limits, follow-ups, AI and pricing for Instagram creators.",
        "answer": "CreatorFlow has a free plan of about 500 DMs a month and Pro around $15 for about 5,000 DMs, with flows of one "
                  "DM plus an optional step. {brand} offers 1,000 free DMs, unlimited DMs from $9 / ₹199, and multi-step flows "
                  "(follow gate, email or WhatsApp, menu, follow-up offer) plus AI replies.",
        "them": ["Free plan about 500 DMs", "Pro about $15/month for about 5,000 DMs", "Simple one-step flows", "Extra DM add-ons"],
        "us": ["1,000 free DMs, unlimited from $9", "Multi-step flows: follow, email/WhatsApp, menu, follow-up", "AI replies included",
               "Sales per reel"],
        "choose_them": "you want the simplest possible setup and send modest volumes.",
        "choose_us": "you want longer flows, AI replies and no DM cap for less.",
    },
    "zorcha": {
        "name": "Zorcha",
        "title": "Zorcha alternative",
        "description": "{brand} vs Zorcha: Instagram DM automation plans, prices in ₹, email collection and AI compared.",
        "answer": "Zorcha is an Indian Instagram DM tool with free core features and paid plans reported from about ₹1,199 a month "
                  "(email collection on its higher plan). {brand}'s Creator plan is ₹199 a month and includes email and WhatsApp "
                  "capture, follow-ups, broadcasts and AI replies.",
        "them": ["Indian pricing in ₹", "Core automation free", "Paid plans from about ₹1,199", "AI credits"],
        "us": ["Creator ₹199 with email and WhatsApp capture", "AI replies included", "Follow-ups and broadcast", "Sales per reel"],
        "choose_them": "you're already set up on it and its credit model suits you.",
        "choose_us": "you want lead capture, AI and follow-ups at a fraction of the price.",
    },
    "inro": {
        "name": "Inrō",
        "title": "Inrō alternative",
        "description": "{brand} vs Inrō: AI DM agent, contact-based pricing and Instagram automation compared.",
        "answer": "Inrō is an AI-first Instagram DM tool priced by active contacts (free for about 100 contacts, Pro from about "
                  "€12.99 a month for 500+). {brand} has flat pricing (₹199 / $9 a month, unlimited DMs) with AI replies included, "
                  "a follow gate, lead capture and sales tracking.",
        "them": ["AI agent included", "Pricing by active contacts", "Done-for-you service on request", "Euro pricing"],
        "us": ["Flat price, no per-contact charges", "AI replies included (300 a month on Creator)", "Follow gate, menus, follow-ups",
               "Pricing in ₹ and $"],
        "choose_them": "you want a done-for-you managed setup.",
        "choose_us": "you want predictable flat pricing as your audience grows.",
    },
    "rapiddm": {
        "name": "RapidDM",
        "title": "RapidDM alternative",
        "description": "{brand} vs RapidDM: Indian Instagram auto DM tools compared on price, follow gate and features.",
        "answer": "RapidDM is an Indian Instagram auto DM tool; public sources report prices from about ₹499 a month (some list "
                  "dollar plans instead) with a follow gate and story replies. {brand} starts free (1,000 DMs) and is ₹199 a "
                  "month for unlimited DMs, AI replies, follow-ups and sales tracking.",
        "them": ["Comment-to-DM, story replies, follow gate", "Paid plans reported around ₹499", "Short free trial"],
        "us": ["Free plan, no trial clock", "Creator ₹199 with AI replies", "Follow-ups, menus, broadcast", "Sales per reel and insights"],
        "choose_them": "you prefer its interface.",
        "choose_us": "you want a free plan and more features for less.",
    },
})

# ---------- more guides ----------

GUIDES.update({
    "best-instagram-dm-automation-tools": {
        "title": "Best Instagram DM automation tools in 2026",
        "description": "The best Instagram DM automation tools in 2026 for creators, coaches and businesses, with prices and who each is for.",
        "answer": "The best Instagram DM automation tool depends on what you need: ManyChat for complex multi-channel bots, "
                  "LinkDM or ReplyRush for simple comment-to-DM, Repli for Instagram plus WhatsApp, SuperProfile if you also "
                  "want a store, and {brand} for creators who want comment-to-DM, AI replies and sales tracking at a flat, low price.",
        "sections": [
            ("Quick picks (checked " + CHECKED + ")", "<div class=\"scroll\"><table><thead><tr><th>Tool</th><th>Best for</th><th>Starts at</th></tr></thead><tbody>"
             "<tr><td><b>{brand}</b></td><td>Creators who sell: AI replies, follow gate, sales per reel</td><td>Free; ₹199 / $9</td></tr>"
             "<tr><td>ManyChat</td><td>Complex bots across many channels</td><td>Free; about $17, by contacts</td></tr>"
             "<tr><td>LinkDM</td><td>Simple comment-to-DM</td><td>Free; about $19</td></tr>"
             "<tr><td>ReplyRush</td><td>Most free DMs, Instagram and Facebook</td><td>Free; about $10</td></tr>"
             "<tr><td>InstantDM</td><td>Low-cost global plan</td><td>Free; about $9.99</td></tr>"
             "<tr><td>Repli</td><td>Instagram plus WhatsApp and CRM</td><td>Free; ₹249</td></tr>"
             "<tr><td>SuperProfile</td><td>Store plus AutoDM</td><td>About ₹499 + fee on sales</td></tr>"
             "<tr><td>ReplyKaro</td><td>Lowest price in India</td><td>Free; about ₹99</td></tr></tbody></table></div>"
             "<p class=\"note\">Prices change often; check each tool's own pricing page.</p>"),
            ("What to look for", "<ul><li>Built on Meta's <b>official API</b> (never give your password).</li>"
             "<li><b>Flat vs per-contact</b> pricing: per-contact gets expensive when a reel goes viral.</li>"
             "<li>Whether <b>follow gate, story replies and email capture</b> are on the plan you'll buy.</li>"
             "<li>Whether <b>AI replies</b> are included or sold as credits.</li><li>Whether you can see <b>which reel made sales</b>.</li></ul>"),
        ],
        "faq": [("Which Instagram DM automation tool is free?", "Most have free plans of roughly 500–1,500 DMs a month, including {brand} (1,000 DMs a month)."),
                ("Which is best for Indian creators?", "Look for ₹ pricing and UPI billing. {brand}, Repli, ReplyKaro and SuperProfile all price in ₹; {brand} includes AI replies from ₹199.")],
    },
    "manychat-alternatives": {
        "title": "ManyChat alternatives for Instagram (2026)",
        "description": "Cheaper, simpler ManyChat alternatives for Instagram comment-to-DM and AI replies, with prices.",
        "answer": "Good ManyChat alternatives for Instagram are {brand} (flat ₹199 / $9 with AI replies included), LinkDM and "
                  "ReplyRush (simple comment-to-DM), InstantDM (low-cost global plan) and Repli (Instagram plus WhatsApp). "
                  "Most charge a flat price instead of ManyChat's per-contact pricing.",
        "sections": [
            ("Why people switch from ManyChat", "<ul><li>Pricing by active contacts rises fast when a reel goes viral.</li>"
             "<li>The flow builder is powerful but slow to learn for simple comment-to-DM.</li><li>AI features cost more.</li></ul>"),
            ("The alternatives", "<ul><li><a href=\"/vs/manychat\"><b>{brand}</b></a>: 4-step builder, follow gate, email/WhatsApp, AI replies included, sales per reel.</li>"
             "<li><a href=\"/vs/linkdm\">LinkDM</a>: simple comment-to-DM with a free plan.</li><li><a href=\"/vs/replyrush\">ReplyRush</a>: free DMs, DM-volume plans.</li>"
             "<li><a href=\"/vs/instantdm\">InstantDM</a>: low-cost plans.</li><li><a href=\"/vs/repli\">Repli</a>: adds WhatsApp and CRM.</li></ul>"),
        ],
        "faq": [("Is there a free ManyChat alternative?", "Yes. {brand}, LinkDM, ReplyRush and InstantDM have free plans.")],
    },
    "instagram-dm-limits": {
        "title": "Instagram DM limits explained (24-hour window, 7-day replies, hourly caps)",
        "description": "Instagram's rules for automated DMs: the 24-hour messaging window, private replies to comments, and rate limits.",
        "answer": "Instagram lets automation tools send a private reply DM to a comment once, within 7 days of the comment; "
                  "after someone messages you, you can reply freely for 24 hours from their last message; and accounts have "
                  "hourly limits on automated messages. Good tools respect these limits and pause instead of failing.",
        "sections": [
            ("The three rules", "<ol><li><b>Private replies to comments</b>: one DM per comment, within 7 days.</li>"
             "<li><b>24-hour window</b>: after a person sends you a message (or taps a button in your DM), you can message them for 24 hours.</li>"
             "<li><b>Hourly limits</b>: Instagram caps how many automated messages an account sends per hour; viral reels can hit it.</li></ol>"),
            ("What this means in practice", "<ul><li>Follow-up offers must go within 24 hours of the person's last message.</li>"
             "<li>You can't DM all your followers at once, only people who messaged you in the last 24 hours (a broadcast to recent chats).</li>"
             "<li>Old comments (older than 7 days) can't get a DM.</li></ul>"),
            ("How {brand} handles them", "<p>It times follow-ups inside the 24-hour window, sends past-comment DMs only within 7 days, "
             "queues and retries refused DMs, waits when Instagram slows sending, and alerts you if the account hits a problem.</p>"),
        ],
        "faq": [("Why didn't someone get my DM?", "Common reasons: the comment was older than 7 days, Instagram refused to open a new chat, or the hourly limit was reached. {brand} retries refused DMs for several days.")],
    },
    "how-to-collect-emails-from-instagram": {
        "title": "How to collect emails from Instagram followers",
        "description": "Collect emails from Instagram with a comment keyword and a DM that asks for the email before sending your freebie.",
        "answer": "The easiest way to collect emails from Instagram is a comment-to-DM automation that asks for the email inside "
                  "the DM before sending a freebie: people comment a keyword, get a DM asking for their email, reply with it, and "
                  "receive the link. Emails are saved automatically and can go to Google Sheets or your email tool.",
        "sections": [
            ("Steps", "<ol><li>Create a freebie worth an email (checklist, template, mini-course).</li><li>Post a reel: \"Comment GUIDE and I'll send it\".</li>"
             "<li>In {brand}, create a comment automation, turn on <b>Ask for email</b>, and add the link.</li>"
             "<li>Optional: make the email required, and send leads to Google Sheets or Mailchimp via webhook.</li></ol>"),
            ("Tips", "<ul><li>Say why you need the email (\"so I can send updates\").</li><li>Offer a Skip button if your goal is reach, not leads.</li>"
             "<li>Tag leads by reel so you know which topic attracts buyers.</li></ul>"),
        ],
        "faq": [("Can I collect WhatsApp numbers too?", "Yes, {brand} can ask for a WhatsApp number in the same way.")],
    },
    "instagram-dm-automation-for-coaches": {
        "title": "Instagram DM automation for coaches",
        "description": "How coaches use Instagram DM automation to book calls, qualify leads and sell programs without living in the inbox.",
        "answer": "Coaches use Instagram DM automation to turn reel comments into qualified leads: a keyword triggers a DM with a "
                  "free resource, the DM collects an email or WhatsApp number, a choice menu sorts people by goal, a follow-up "
                  "offers a call or program, and an AI agent answers common questions while handing serious leads to the coach.",
        "sections": [
            ("A simple funnel", "<ol><li>Reel with a clear promise and a keyword.</li><li>DM with the free resource and a 3-option menu (\"beginner / stuck / ready to work together\").</li>"
             "<li>Ask for WhatsApp from the \"ready\" option.</li><li>Follow-up 3 hours later with your call or program link.</li>"
             "<li>AI agent answers price and schedule questions; anything sensitive comes to you.</li></ol>"),
            ("Measure it", "<p>Use sales tracking so every program sale is credited to the reel and automation that brought it.</p>"),
        ],
        "faq": [("Will the AI promise things I don't offer?", "No. It answers only from your FAQ and products, and hands anything unclear to you.")],
    },
    "sell-digital-products-on-instagram": {
        "title": "How to sell digital products on Instagram with DMs",
        "description": "Sell guides, courses and templates on Instagram: comment keyword, free value in DM, follow-up offer, track sales per reel.",
        "answer": "To sell digital products on Instagram, give something free in exchange for a comment keyword, deliver it by DM, "
                  "follow up a few hours later with the paid product, and track which reel made each sale so you can repeat what works.",
        "sections": [
            ("The playbook", "<ol><li>Reel → \"comment PROMPTS for the free pack\".</li><li>DM delivers the free pack (optionally after a follow).</li>"
             "<li>3 hours later: \"The full pack is ₹149 today\" with a button.</li><li>Your payment page redirects to a {brand} sales link, so the sale is credited to the reel.</li>"
             "<li>Broadcast launch-day messages to everyone who DMed in the last 24 hours.</li></ol>"),
            ("Pricing tips", "<ul><li>Low-ticket first (₹99–₹499), then upsell.</li><li>Use a choice menu to offer free vs paid in one DM.</li></ul>"),
        ],
        "faq": [("Which payment pages work?", "Any page that can redirect after payment, such as Razorpay Payment Pages or Instamojo.")],
    },
    "instagram-story-auto-reply": {
        "title": "How to set up Instagram story auto-reply",
        "description": "Automatically DM people who reply to your Instagram story or mention you, with a keyword or for every reply.",
        "answer": "To auto-reply to Instagram stories, connect a tool on the official API, create a story-reply automation (for "
                  "every reply or only replies with a keyword like LINK), write the DM with your link, and turn it on. You can also "
                  "thank everyone who mentions you in their story automatically.",
        "sections": [
            ("Steps in {brand}", "<ol><li>Auto DM → Create → When someone replies to your story.</li><li>Choose any reply or a keyword.</li>"
             "<li>Write the DM and add a link button.</li><li>Optional: a separate automation for story mentions.</li></ol>"),
            ("Ideas", "<ul><li>\"Reply LINK for today's offer\".</li><li>Poll follow-up: \"reply YES for the guide\".</li><li>Thank-you plus a discount for mentions.</li></ul>"),
        ],
        "faq": [("Is story auto-reply free?", "Yes, on every {brand} plan.")],
    },
})


def all_paths():
    return (["/", "/features", "/compare", "/guides", "/privacy", "/terms"]
            + [f"/features/{k}" for k in FEATURES] + [f"/vs/{k}" for k in COMPARE] + [f"/guides/{k}" for k in GUIDES])
