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


# ---------- guides, batch 3 ----------

GUIDES.update({
    "instagram-comment-keyword-ideas": {
        "title": "40 comment keyword ideas for Instagram reels (with freebie ideas)",
        "description": "Comment keyword and freebie ideas for Instagram reels: what to ask people to comment, and what to send in the DM.",
        "answer": "Good Instagram comment keywords are one short, specific word tied to what people get, such as GUIDE, PROMPTS, "
                  "RECIPE, PLAN or LINK. Say it early in the reel and in the caption, and send the promised freebie by DM the "
                  "moment someone comments it.",
        "sections": [
            ("Rules for a keyword that works", "<ul><li>One word, easy to spell, no symbols.</li><li>Matches the promise (comment RECIPE for a recipe).</li>"
             "<li>Different per reel, so you can see which reel performs.</li><li>Said in the first 3 seconds and written on screen and in the caption.</li></ul>"),
            ("Keyword and freebie ideas by niche", "<div class=\"scroll\"><table><thead><tr><th>Niche</th><th>Keywords</th><th>What to send</th></tr></thead><tbody>"
             "<tr><td>AI and tech</td><td>PROMPTS, TOOLS, AI, CODE</td><td>Prompt pack, tool list, starter template</td></tr>"
             "<tr><td>Fitness</td><td>PLAN, ABS, MEAL, STRETCH</td><td>7-day plan, meal sheet, routine video</td></tr>"
             "<tr><td>Food</td><td>RECIPE, SAUCE, MENU</td><td>Full recipe, grocery list</td></tr>"
             "<tr><td>Finance</td><td>BUDGET, SIP, TAX, SHEET</td><td>Budget sheet, checklist</td></tr>"
             "<tr><td>Coaching</td><td>CALL, GUIDE, START, FREE</td><td>Mini-course, booking link</td></tr>"
             "<tr><td>Fashion and beauty</td><td>LINK, SHOP, LOOK, SKIN</td><td>Product links, routine</td></tr>"
             "<tr><td>Travel</td><td>TRIP, ITINERARY, MAP</td><td>Itinerary, saved-places map</td></tr>"
             "<tr><td>Education</td><td>NOTES, PDF, MOCK, PYQ</td><td>Notes, practice set</td></tr>"
             "<tr><td>Business and marketing</td><td>SCRIPT, HOOKS, AUDIT, DECK</td><td>Script template, hook list</td></tr>"
             "<tr><td>Design</td><td>FONTS, TEMPLATE, PRESET, KIT</td><td>Template or preset download</td></tr></tbody></table></div>"),
            ("Reel scripts you can copy", "<ul><li>\"Comment PROMPTS and I'll DM you all 39.\"</li><li>\"Want the full plan? Comment PLAN.\"</li>"
             "<li>\"I made a sheet for this. Comment SHEET and it's yours.\"</li></ul>"),
        ],
        "faq": [("Does the keyword have to be exact?", "No. {brand} matches capitals, plurals and emojis around the word, so \"prompts!!\" still counts as PROMPTS."),
                ("Can one reel have several keywords?", "Yes, add several keywords to one automation, or use a choice menu in the DM instead.")],
    },
    "auto-reply-instagram-comments": {
        "title": "How to auto-reply to Instagram comments",
        "description": "Automatically reply to Instagram comments publicly (and by DM) with rotating replies that don't look like spam.",
        "answer": "To auto-reply to Instagram comments, use a tool on Meta's official API that posts a public reply to each matching "
                  "comment and, optionally, sends a DM. Rotate 2–3 different replies and mention the person, so replies look "
                  "natural and Instagram doesn't treat them as spam.",
        "sections": [
            ("Set it up", "<ol><li>Create a comment automation on a reel, on any post, or on your next post.</li><li>Choose a keyword or reply to every comment.</li>"
             "<li>Write 2–3 public replies, e.g. \"Sent! Check your DMs 📩\". {brand} picks one at random and adds @username.</li>"
             "<li>Add the DM, or turn the DM off if you only want public replies.</li></ol>"),
            ("Why reply publicly", "<p>Replies show other viewers that commenting works, which brings more comments and pushes the reel to more people.</p>"),
            ("Stay safe", "<ul><li>Use variations like {Sent|Done|Check your DMs}.</li><li>Don't put links in public replies.</li><li>Hide spam comments automatically with a comment guard.</li></ul>"),
        ],
        "faq": [("Can I reply only with a DM and no public comment?", "Yes, turn public replies off in the automation.")],
    },
    "why-instagram-dm-not-sent": {
        "title": "Why didn't my Instagram auto DM send? (Fixes)",
        "description": "Troubleshooting Instagram DM automation: common reasons an auto DM wasn't delivered and how to fix each one.",
        "answer": "An automated Instagram DM usually fails for one of these reasons: the comment is older than 7 days, Instagram "
                  "refused to open a new chat, the account hit its hourly limit, the keyword didn't match, the automation was "
                  "paused or scheduled, or the Instagram login expired. Each has a simple fix.",
        "sections": [
            ("Check these in order", "<ol><li><b>Automation on?</b> Not paused, and inside its start/end time.</li>"
             "<li><b>Keyword matched?</b> Check excluded words and that the comment is on the right post.</li>"
             "<li><b>Already sent?</b> With once per person on, each person gets one DM.</li>"
             "<li><b>Older than 7 days?</b> Instagram doesn't allow DMs to older comments.</li>"
             "<li><b>Refused by Instagram?</b> Sometimes it won't open a new chat; {brand} retries daily for several days.</li>"
             "<li><b>Hourly limit?</b> On viral reels, sending pauses and resumes by itself.</li>"
             "<li><b>Logged out?</b> Log in with Instagram again; you'll get an alert if this happens.</li></ol>"),
            ("Where to look in {brand}", "<p>The Activity page lists every event with errors in plain words, and the Auto DM page shows refused DMs waiting for a retry.</p>"),
        ],
        "faq": [("Do people need to follow me to get the DM?", "Only if you turned on follow to unlock; then they get a follow request first and the link after following.")],
    },
    "switch-to-instagram-professional-account": {
        "title": "How to switch to an Instagram Business or Creator account",
        "description": "DM automation needs an Instagram professional account. How to switch for free, and Business vs Creator.",
        "answer": "Instagram DM automation needs a professional (Business or Creator) account. Switching is free: in the Instagram "
                  "app open your profile, go to Settings, find Account type and tools, and choose Switch to professional account. "
                  "Either type works with {brand}.",
        "sections": [
            ("Business or Creator?", "<ul><li><b>Creator</b>: for influencers, artists, coaches and personal brands.</li>"
             "<li><b>Business</b>: for shops, brands and service businesses.</li><li>Both work for comment-to-DM and the AI agent; you can switch back any time.</li></ul>"),
            ("Then connect", "<p>Open {brand}, tap Continue with Instagram, and approve the permissions on Instagram's own screen. You never share your password.</p>"),
        ],
        "faq": [("Will switching change my followers or reach?", "No, your followers stay the same, and you get insights and contact options."),
                ("Do I need a Facebook page?", "No, {brand} uses Instagram Login, so a Facebook page isn't required.")],
    },
    "instagram-ai-chatbot": {
        "title": "How to set up an AI chatbot for Instagram DMs",
        "description": "Set up an AI that answers Instagram DMs from your FAQ, in the fan's language, and hands tricky chats to you.",
        "answer": "To set up an AI chatbot for Instagram DMs, connect your account to an official-API tool with an AI agent, write "
                  "a short About section and an FAQ with your products, prices and links, choose which topics it must hand to you, "
                  "test it with sample questions, and turn it on.",
        "sections": [
            ("What to put in the FAQ", "<ul><li>Each product: name, price, what's inside, the link.</li><li>Delivery and access: \"you get it instantly by email\".</li>"
             "<li>Payment methods and refund policy.</li><li>Common questions copied from your real DMs.</li></ul>"),
            ("Hand-offs that keep you safe", "<p>Send refunds, payment problems, collabs and anything the AI isn't sure about to you, with a suggested reply. The AI never invents prices or links.</p>"),
            ("Test before going live", "<p>Use the test box with real questions in different languages, then check the AI Inbox daily for the first week.</p>"),
        ],
        "faq": [("Does it reply in Hindi or other languages?", "Yes, by default it replies in the language the person writes in.")],
    },
    "instagram-lead-magnet-ideas": {
        "title": "Instagram lead magnet ideas that get comments",
        "description": "Lead magnet ideas for Instagram creators and coaches that people will comment for, plus how to deliver them by DM.",
        "answer": "The best Instagram lead magnets are quick wins people can use today: checklists, templates, prompt packs, short "
                  "guides, swipe files and mini video lessons. Promise one specific result, ask for a comment keyword, and deliver "
                  "it by DM (optionally after collecting an email).",
        "sections": [
            ("Ideas that work", "<ul><li>Checklist (\"10-point reel checklist\").</li><li>Template (Notion, Canva, Sheets).</li>"
             "<li>Prompt pack or script pack.</li><li>Cheat sheet or one-page guide.</li><li>Recorded mini-lesson (5–10 minutes).</li>"
             "<li>Resource list (tools, books, places).</li><li>Free audit or quiz result.</li></ul>"),
            ("Make it convert", "<ul><li>Specific beats general: \"7 hooks for coaches\" beats \"marketing tips\".</li>"
             "<li>Deliver instantly by DM.</li><li>Follow up later with the paid next step.</li></ul>"),
        ],
        "faq": [("Should I ask for an email?", "If you'll email them later, yes. If you mainly want followers, use follow to unlock and skip the email.")],
    },
    "instagram-dm-automation-for-ecommerce": {
        "title": "Instagram DM automation for online stores",
        "description": "How online stores use Instagram DM automation: product links on comments, price questions, offers and sales tracking.",
        "answer": "Online stores use Instagram DM automation to send product links when people comment (\"LINK\" or \"PRICE\"), "
                  "answer stock and price questions with an AI agent, send discount codes to story mentions, and track which "
                  "post brought each sale with UTM tags and sales links.",
        "sections": [
            ("Automations to set up", "<ol><li><b>Comment PRICE</b> on product reels → DM with price and a Buy button.</li>"
             "<li><b>Story replies</b> → link to the product in the story.</li><li><b>Story mentions</b> → thank-you plus a discount code.</li>"
             "<li><b>AI agent</b> for sizes, shipping and returns from your FAQ.</li><li><b>Broadcast</b> on sale day to people who DMed in the last 24 hours.</li></ol>"),
            ("Measure revenue", "<p>UTM tags show the traffic in Shopify or Google Analytics, and a sales link on your thank-you page credits each order to the post.</p>"),
        ],
        "faq": [("Does it work with Shopify?", "Yes, through links and UTM tags; add a sales link as the order confirmation redirect if your checkout allows it.")],
    },
    "run-instagram-giveaway": {
        "title": "How to run an Instagram giveaway and pick a winner",
        "description": "Run a fair Instagram giveaway: entry rules, picking a random winner from comments, and announcing it.",
        "answer": "To run an Instagram giveaway, post clear entry rules (comment a word, follow, optional tag), set an end date, "
                  "then pick a random winner from the comments with a giveaway picker that skips duplicates and your own account, "
                  "and announce the winner publicly and by DM.",
        "sections": [
            ("Rules to post", "<ul><li>How to enter (comment, follow, tag a friend).</li><li>End date and time.</li>"
             "<li>Prize and who can enter (country, age).</li><li>\"Not sponsored or endorsed by Instagram.\"</li></ul>"),
            ("Pick a fair winner", "<p>{brand}'s giveaway picker loads the comments, keeps one entry per person, skips your own account, can require the keyword or a number of tagged friends, and picks at random. It can then reply under each winner's comment and DM them. Screen-record the draw for transparency.</p>"),
            ("Grow from it", "<p>Add a comment-to-DM automation so every entrant gets a thank-you and a small freebie: everyone wins something and you collect leads.</p>"),
        ],
        "faq": [("Is a giveaway picker free?", "Yes, it's included on every {brand} plan.")],
    },
})


# ---------- niche guides ----------

GUIDES.update({
    "instagram-dm-automation-for-fitness-coaches": {
        "title": "Instagram DM automation for fitness coaches and trainers",
        "description": "How fitness coaches use Instagram comment-to-DM to send free plans, collect WhatsApp leads and sell coaching programs.",
        "answer": "Fitness coaches use Instagram DM automation to send a free workout or meal plan to everyone who comments a "
                  "keyword like PLAN, collect WhatsApp numbers from people who want coaching, follow up with a program offer "
                  "a few hours later, and let an AI answer common questions about price, duration and diet.",
        "sections": [
            ("A funnel that works for fitness", "<ol><li><b>Reel</b>: a quick result (\"3 moves for lower back pain\", \"high-protein breakfast in 5 minutes\") ending with \"comment PLAN\".</li>"
             "<li><b>DM</b>: the free 7-day plan, sent after they follow you.</li>"
             "<li><b>Choice menu</b>: \"Fat loss / Muscle gain / Just staying fit\", each with its own plan, so you know their goal.</li>"
             "<li><b>WhatsApp capture</b> on the \"I want coaching\" option, so you can call serious leads.</li>"
             "<li><b>Follow-up</b> 3 hours later: \"Want me to build this around your schedule? Coaching starts at ₹1,999/month.\"</li></ol>"),
            ("Keyword ideas", "<p>PLAN, ABS, MEAL, PROTEIN, STRETCH, HOME, GYM, 30DAY, YOGA, RUN.</p>"),
            ("What the AI agent should answer", "<ul><li>Program price, length and what's included.</li><li>Online vs in-person, timings, language.</li>"
             "<li>How to pay and when it starts.</li></ul><p>Hand over anything about injuries, medical conditions, pregnancy or medication to yourself.</p>"),
            ("Stay responsible", "<ul><li>Add a short disclaimer to free plans (\"consult a doctor if you have a condition\").</li>"
             "<li>Don't promise guaranteed results in automated DMs.</li><li>Keep medical questions out of the AI's hands.</li></ul>"),
        ],
        "faq": [("Which plan do fitness coaches need?", "Creator (₹199 / $9) covers unlimited DMs, menus, WhatsApp capture, follow-ups and 300 AI replies a month."),
                ("Can I see which reel brought paying clients?", "Yes, sales tracking credits each payment to the reel and automation that brought it.")],
    },
    "instagram-dm-automation-for-finance-creators": {
        "title": "Instagram DM automation for finance creators",
        "description": "How personal-finance creators use Instagram comment-to-DM for budget sheets, checklists and courses, while staying compliant.",
        "answer": "Finance creators use Instagram DM automation to deliver budget sheets, tax checklists and calculators to people who "
                  "comment a keyword like SHEET, collect emails for a newsletter, and promote courses or webinars, while keeping "
                  "automated DMs educational and free of personalised investment advice.",
        "sections": [
            ("A funnel for finance content", "<ol><li><b>Reel</b>: one clear concept (\"the 50/30/20 rule\", \"5 tax-saving options\") ending with \"comment SHEET\".</li>"
             "<li><b>DM</b>: the budget sheet or checklist, after asking for their email.</li>"
             "<li><b>Choice menu</b>: \"Budgeting / Investing basics / Taxes\", each with its own resource.</li>"
             "<li><b>Follow-up</b>: invite them to your free webinar or paid course.</li>"
             "<li><b>Tags</b> by topic, so your newsletter can send the right content.</li></ol>"),
            ("Keyword ideas", "<p>SHEET, BUDGET, TAX, SIP, EMI, SAVE, CALC, CHECKLIST, GUIDE, WEBINAR.</p>"),
            ("Stay compliant", "<ul><li>Keep DMs <b>educational</b>: explain concepts, share tools, not \"buy this stock\".</li>"
             "<li>In India, unregistered creators should not give investment advice or stock tips; follow SEBI's current rules for finfluencers. Elsewhere, follow your country's rules.</li>"
             "<li>Add a disclaimer to resources (\"for education, not financial advice\").</li>"
             "<li>Tell the AI agent to hand over any question asking what to buy or sell.</li></ul>"),
        ],
        "faq": [("Can the AI agent answer money questions?", "It answers from your FAQ (your products, prices, how your course works). Set it to hand over any request for personal investment advice."),
                ("How do I send leads to my newsletter?", "Ask for the email in the DM and send it to Google Sheets, Mailchimp or another tool through a webhook (Pro).")],
    },
    "instagram-dm-automation-for-educators": {
        "title": "Instagram DM automation for teachers and education creators",
        "description": "How teachers, tutors and exam-prep creators use Instagram DMs to share notes, run batch enrolments and answer parents and students.",
        "answer": "Teachers and education creators use Instagram DM automation to send notes, PDFs and practice sets to students who "
                  "comment a keyword like NOTES, collect WhatsApp numbers for batch or class groups, announce new batches to "
                  "recent chats, and let an AI answer questions about fees, timings and syllabus.",
        "sections": [
            ("A funnel for education", "<ol><li><b>Reel</b>: a quick concept, trick or exam tip ending with \"comment NOTES for the PDF\".</li>"
             "<li><b>DM</b>: the notes or practice set, optionally after a follow.</li>"
             "<li><b>Choice menu</b>: by class, exam or subject (\"Class 10 / Class 12 / Competitive exams\").</li>"
             "<li><b>WhatsApp capture</b> for students (or parents) who want batch details.</li>"
             "<li><b>Broadcast</b> on enrolment day to everyone who messaged in the last 24 hours.</li></ol>"),
            ("Keyword ideas", "<p>NOTES, PDF, PYQ, MOCK, FORMULA, SYLLABUS, BATCH, DEMO, MAP, VOCAB.</p>"),
            ("What the AI agent should answer", "<ul><li>Fees, batch timings, language, online or offline.</li><li>Syllabus covered and study material.</li>"
             "<li>How to join and pay.</li></ul><p>Hand over refund requests, complaints and anything about a specific student's results.</p>"),
            ("Tips", "<ul><li>One keyword per chapter or topic, so you see which topics drive enrolments.</li>"
             "<li>Use story replies for daily quiz answers.</li><li>Track which reel brought each enrolment with sales tracking.</li></ul>"),
        ],
        "faq": [("Can it reply in Hindi or regional languages?", "Yes, the AI agent replies in the language the student or parent writes in."),
                ("Can I send different notes for different classes?", "Yes, use a choice menu with one option per class or exam, each with its own PDF link.")],
    },
})


# ---------- niche guides, batch 2 ----------

GUIDES.update({
    "instagram-dm-automation-for-food-creators": {
        "title": "Instagram DM automation for food creators and home bakers",
        "description": "How food creators and home bakers use Instagram comment-to-DM for recipes, e-books, cooking classes and orders.",
        "answer": "Food creators use Instagram DM automation to send the full recipe to everyone who comments a keyword like RECIPE, "
                  "grow followers with a follow gate, sell recipe e-books or cooking classes with a follow-up offer, and (for home "
                  "bakers and cloud kitchens) answer menu, price and delivery questions with an AI agent.",
        "sections": [
            ("A funnel for food content", "<ol><li><b>Reel</b>: the dish in 30 seconds, ending with \"comment RECIPE for the full recipe\".</li>"
             "<li><b>DM</b>: the recipe with measurements, after a follow.</li><li><b>Follow-up</b>: \"Want 50 more like this? The e-book is ₹199 today.\"</li>"
             "<li><b>Choice menu</b> for bakers: \"Order a cake / See the menu / Baking classes\".</li>"
             "<li><b>WhatsApp capture</b> for orders, so you can confirm date, flavour and address.</li></ol>"),
            ("Keyword ideas", "<p>RECIPE, MENU, SAUCE, CAKE, ORDER, CLASS, EBOOK, DIET, TIFFIN, MASALA.</p>"),
            ("What the AI agent should answer", "<ul><li>Menu, prices, sizes and flavours.</li><li>Delivery areas, timings and how far ahead to order.</li>"
             "<li>Egg/eggless, vegan and common allergens, from your FAQ.</li></ul><p>Hand over custom orders, complaints and allergy questions you haven't covered.</p>"),
            ("If you sell food", "<p>Follow your local food-licence and labelling rules (in India, FSSAI registration for home food businesses) and list allergens clearly.</p>"),
        ],
        "faq": [("Can I take cake orders through Instagram DMs?", "Yes: use a choice menu, collect the customer's WhatsApp number, and confirm details there. The AI can answer menu and price questions first."),
                ("Which keyword gets the most comments?", "RECIPE works well because the promise is clear; test one keyword per reel and compare in the reel report.")],
    },
    "instagram-dm-automation-for-beauty-creators": {
        "title": "Instagram DM automation for beauty, makeup and fashion creators",
        "description": "How beauty and fashion creators send product links, routines and affiliate offers by Instagram DM, and how salons take bookings.",
        "answer": "Beauty and fashion creators use Instagram DM automation to send product links and routines to everyone who "
                  "comments a keyword like LINK or SHOP, earn more from affiliate links (with click tracking turned off for them), "
                  "and, for salons and makeup artists, answer price questions and collect booking requests automatically.",
        "sections": [
            ("For creators", "<ol><li><b>Reel</b>: a look, routine or haul ending with \"comment LINK for everything I used\".</li>"
             "<li><b>DM</b>: a short list with product links, or a menu (\"Skincare / Makeup / Outfit\").</li>"
             "<li><b>Story replies</b>: \"reply SHOP for today's finds\".</li>"
             "<li><b>Follow-up</b> for your own product, preset pack or course.</li></ol>"),
            ("For salons and makeup artists", "<ul><li>Comment BOOK on a reel → price list and a booking link.</li>"
             "<li>WhatsApp capture for bridal enquiries, with date and location.</li><li>AI answers services, prices, timings and location from your FAQ.</li></ul>"),
            ("Affiliate links", "<p>Turn off click counting for affiliate links (some programmes don't allow redirects) and say the link is affiliate where your country's rules require it.</p>"),
            ("Keyword ideas", "<p>LINK, SHOP, LOOK, SKIN, ROUTINE, SHADE, OUTFIT, BOOK, BRIDAL, PRESET.</p>"),
        ],
        "faq": [("Will Instagram mind product links in DMs?", "Links in DMs sent through the official API are fine; avoid putting links in public comment replies."),
                ("Can I see which products people tapped?", "Yes, with click counting on, each link counts its clicks per automation (keep it off for affiliate links).")],
    },
    "instagram-dm-automation-for-travel-creators": {
        "title": "Instagram DM automation for travel creators and agencies",
        "description": "How travel creators send itineraries and maps by DM, and how travel agencies turn reel comments into trip enquiries.",
        "answer": "Travel creators use Instagram DM automation to send itineraries, saved-places maps and budget breakdowns to everyone "
                  "who comments a keyword like TRIP, and travel agencies use it to turn reel comments into enquiries by asking for "
                  "dates, group size and a WhatsApp number in the DM.",
        "sections": [
            ("For creators", "<ol><li><b>Reel</b>: a place or route ending with \"comment TRIP for the full itinerary\".</li>"
             "<li><b>DM</b>: the day-by-day plan and a map link.</li><li><b>Follow-up</b>: your paid guide, preset pack or group-trip waitlist.</li></ol>"),
            ("For travel agencies and tour operators", "<ol><li>Comment PACKAGE or PRICE on a destination reel.</li>"
             "<li>DM with the package brochure and a menu: \"Honeymoon / Family / Group\".</li>"
             "<li>Ask for WhatsApp to send a custom quote.</li><li>Broadcast seasonal offers to everyone who messaged in the last 24 hours.</li></ol>"),
            ("What the AI agent should answer", "<ul><li>What's included, starting prices, best season.</li><li>Visa and documents (general info from your FAQ).</li></ul>"
             "<p>Hand over custom quotes, cancellations and payment issues.</p>"),
            ("Keyword ideas", "<p>TRIP, ITINERARY, MAP, BUDGET, PACKAGE, VISA, HONEYMOON, TREK, HOSTELS, GUIDE.</p>"),
        ],
        "faq": [("Can I send a different itinerary for each reel?", "Yes, each reel can have its own automation, keyword and link."),
                ("Can agencies see which destination reels bring bookings?", "Yes, sales tracking and lead counts show results per reel.")],
    },
    "instagram-dm-automation-for-real-estate": {
        "title": "Instagram DM automation for real estate agents and builders",
        "description": "How real estate agents and builders turn Instagram reel comments into qualified property leads with DMs and WhatsApp capture.",
        "answer": "Real estate agents and builders use Instagram DM automation to send brochures, price sheets and site-visit links "
                  "to everyone who comments a keyword like PRICE or DETAILS on a property reel, collect WhatsApp numbers, and sort "
                  "leads by budget or property type with a choice menu, so agents only call serious buyers.",
        "sections": [
            ("A lead funnel for property", "<ol><li><b>Reel</b>: a walkthrough ending with \"comment PRICE for the price sheet\".</li>"
             "<li><b>DM</b>: brochure and price sheet, then a menu: \"2 BHK / 3 BHK / Plots\" or by budget.</li>"
             "<li><b>WhatsApp capture</b> with \"want a site visit?\".</li><li><b>Tags</b> per project and budget for follow-up.</li>"
             "<li><b>Leads to Google Sheets</b> or your CRM through a webhook (Pro).</li></ol>"),
            ("What the AI agent should answer", "<ul><li>Location, sizes, amenities and starting prices from your FAQ.</li><li>Possession dates and site-visit timings.</li></ul>"
             "<p>Hand over price negotiation, loan questions and anything legal.</p>"),
            ("Stay compliant", "<p>Show registration details where your local rules require them (in India, the RERA registration number for registered projects and agents), and keep prices and offers accurate.</p>"),
            ("Keyword ideas", "<p>PRICE, DETAILS, BROCHURE, VISIT, 2BHK, 3BHK, PLOT, RENT, EMI, LOCATION.</p>"),
        ],
        "faq": [("Can I send leads straight to my sales team?", "Yes, through Google Sheets or a webhook to your CRM, and team members can be invited to the dashboard (Pro)."),
                ("Does it work for rentals too?", "Yes, use a RENT keyword and ask for move-in date and budget in the DM.")],
    },
    "instagram-dm-automation-for-astrologers": {
        "title": "Instagram DM automation for astrologers and tarot readers",
        "description": "How astrologers and tarot readers share free readings, collect birth details and sell consultations through Instagram DMs.",
        "answer": "Astrologers and tarot readers use Instagram DM automation to send a free weekly reading or guide to everyone who "
                  "comments their sign or a keyword, collect WhatsApp numbers for paid consultations, and let an AI agent answer "
                  "questions about consultation types, prices and booking, while personal readings stay with the reader.",
        "sections": [
            ("A funnel for astrology content", "<ol><li><b>Reel</b>: \"this week for your sign\" ending with \"comment your sign\" (one automation with all 12 signs as keywords).</li>"
             "<li><b>DM</b>: a choice menu so they pick their sign group, each option with its reading (a menu has up to 3 options, so group signs, e.g. by element, or make one automation per sign).</li>"
             "<li><b>Follow-up</b>: \"Want a personal reading? Consultations start at ₹499.\"</li>"
             "<li><b>WhatsApp capture</b> for booking, then collect birth details there.</li></ol>"),
            ("What the AI agent should answer", "<ul><li>Consultation types (call, chat, report), prices and duration.</li><li>How to book and pay, languages offered.</li></ul>"
             "<p>Keep personal readings, health, legal and money questions with the reader, not the AI.</p>"),
            ("Be responsible", "<ul><li>Don't promise guaranteed outcomes in automated messages.</li><li>Add \"for guidance and entertainment\" style disclaimers where appropriate.</li>"
             "<li>Ask for birth details only for paid readings, and keep them private.</li></ul>"),
            ("Keyword ideas", "<p>The 12 signs (ARIES … PISCES), TAROT, READING, KUNDLI, NUMEROLOGY, LOVE, CAREER, REMEDY, CONSULT.</p>"),
        ],
        "faq": [("Can one reel react to all 12 signs?", "Yes. Either add all 12 signs as keywords to one automation that sends a menu, or create one automation per sign so each sign gets its own reading."),
                ("Can the AI give readings?", "Set it to answer only about your services and booking; personal readings should come from you.")],
    },
})


# ---------- guides, batch 4 ----------

GUIDES.update({
    # selling
    "instagram-follow-up-messages": {
        "title": "How to write Instagram follow-up messages that sell",
        "description": "Write follow-up DMs that turn freebie takers into buyers: timing inside the 24-hour window, templates and mistakes to avoid.",
        "answer": "A good Instagram follow-up message is sent a few hours after the freebie, inside Instagram's 24-hour window, "
                  "asks how the freebie went or adds one tip, then makes one clear paid offer with a single button. Timing (1 to "
                  "20 hours later) and a specific, time-bound offer matter more than long copy.",
        "sections": [
            ("When to send it", "<p>{brand} lets you send the follow-up 1, 3, 6, 12 or 20 hours after the first DM. Three hours works well for "
             "most freebies; use 12–20 hours for longer resources. It must arrive within 24 hours of the person's last message.</p>"),
            ("Templates", "<ul><li>\"Did you get a chance to try it, {username}? The full pack (39 more) is ₹149 today 👇\"</li>"
             "<li>\"Quick tip to get more from the guide: … If you want the complete course, it's here 👇\"</li>"
             "<li>\"A few spots left in this week's batch. Want in? 👇\"</li></ul>"),
            ("Mistakes to avoid", "<ul><li>Several offers in one message.</li><li>Sending after the 24-hour window (it won't deliver).</li>"
             "<li>Fake urgency; use real deadlines.</li><li>No link button; buttons get more taps than links in text.</li></ul>"),
        ],
        "faq": [("How many follow-ups can I send?", "One per person per automation in {brand}, timed inside Instagram's 24-hour window.")],
    },
    "instagram-broadcast-messages": {
        "title": "How to send an Instagram broadcast to your DMs",
        "description": "Message everyone who DMed you recently in one go: what Instagram allows, when to use it and what to send.",
        "answer": "Instagram only lets business accounts message people inside the 24-hour window after their last message, so a "
                  "DM broadcast reaches everyone who messaged you in the last day, not all followers. Use it for launches, live "
                  "sessions and last-call offers, with one short message and one button.",
        "sections": [
            ("Who it reaches", "<p>Everyone who DMed you (or tapped a button in your DM) in roughly the last 24 hours. A reel with a "
             "comment keyword fills this list fast, so post a keyword reel the day before a launch.</p>"),
            ("What to send", "<ul><li>\"Live in 1 hour 🔴 Join here 👇\"</li><li>\"Doors close tonight for the course 👇\"</li>"
             "<li>\"New drop is live, first 50 get the early price 👇\"</li></ul>"),
            ("In {brand}", "<p>Auto DM → Broadcast shows how many people you can reach now, sends in batches, and counts link clicks.</p>"),
        ],
        "faq": [("Can I message all my followers?", "No. Instagram doesn't allow that; only people who messaged you in the last 24 hours.")],
    },
    "instagram-dm-sales-funnel": {
        "title": "How to build an Instagram DM sales funnel",
        "description": "A complete Instagram DM funnel: reel, keyword, freebie, lead capture, follow-up offer, broadcast and tracking.",
        "answer": "An Instagram DM sales funnel has six steps: a reel with a comment keyword, an automatic DM with a freebie, a follow "
                  "or contact capture, a follow-up offer a few hours later, a broadcast on launch days, and sales tracking so you "
                  "know which reels sell.",
        "sections": [
            ("The six steps", "<ol><li><b>Attention</b>: a reel with one promise and a keyword.</li><li><b>Delivery</b>: DM with the freebie.</li>"
             "<li><b>Capture</b>: follow gate, email or WhatsApp.</li><li><b>Offer</b>: follow-up with the paid product.</li>"
             "<li><b>Push</b>: broadcast to recent chats on launch day.</li><li><b>Measure</b>: sales per reel, then repeat the winners.</li></ol>"),
            ("Numbers to watch", "<ul><li>Comments per 1,000 views.</li><li>Link opens per DM sent.</li><li>Follows and leads per DM.</li>"
             "<li>Sales per link open.</li></ul><p>{brand}'s insights show each step for every automation.</p>"),
        ],
        "faq": [("How long does it take to set up?", "About 10 minutes for the first automation; after that, copy it to new reels in one tap.")],
    },
    "track-instagram-sales-with-utm": {
        "title": "How to track Instagram sales with UTM links",
        "description": "See which Instagram reel and DM brought each visitor and sale using UTM parameters and a sales link.",
        "answer": "To track Instagram sales, add UTM parameters (utm_source=instagram, utm_medium=dm, utm_campaign=reel-name) to "
                  "every link you send so analytics shows where visitors came from, and credit each completed payment to the DM "
                  "link the buyer tapped. {brand} adds the UTM tags automatically and records sales through a sales link.",
        "sections": [
            ("UTM basics", "<ul><li><code>utm_source=instagram</code>: the platform.</li><li><code>utm_medium=dm</code>: the channel.</li>"
             "<li><code>utm_campaign=prompts-reel</code>: the reel or automation.</li></ul><p>Google Analytics, Shopify and most website tools read these automatically.</p>"),
            ("From visits to sales", "<p>UTM tags show visits; to count sales, set your payment page's \"redirect after payment\" to your "
             "product's {brand} sales link. Each sale is credited to the last DM link the buyer tapped.</p>"),
        ],
        "faq": [("Do UTM tags break affiliate links?", "They can. {brand} skips links that already have UTM tags, and you can turn click tracking off for affiliate automations.")],
    },
    # AI
    "write-faq-for-ai-dm-agent": {
        "title": "How to write an FAQ for your Instagram AI DM agent",
        "description": "What to put in the FAQ your AI DM agent answers from: products, prices, links, policies and hand-off rules, with a template.",
        "answer": "Write your AI agent's FAQ as short facts it can quote: each product with price, what's included and link; how "
                  "delivery and payment work; your refund policy; and real questions from your DMs with your answers. Then list "
                  "the topics it must hand to you.",
        "sections": [
            ("Template", "<pre style=\"white-space:pre-wrap\">PRODUCTS\n- AI Prompt Pack: ₹149. 39 prompts + guide. Instant download. Link: https://…\n"
             "- Reels Masterclass: ₹999. 6 videos, lifetime access. Link: https://…\n\nPAYMENT AND DELIVERY\n- UPI, cards, netbanking. Access email arrives in 2 minutes.\n\n"
             "POLICIES\n- Refunds: hand to me.\n\nCOMMON QUESTIONS\n- Is it for beginners? Yes, no experience needed.\n- Language? Hindi and English.</pre>"),
            ("Hand-off topics", "<p>Refunds, payment failures, collaborations, complaints, anything personal or legal, and anything not in the FAQ.</p>"),
            ("Test it", "<p>Ask 10 real questions from your inbox in the test box, including one in another language and one it should hand over.</p>"),
        ],
        "faq": [("How long should the FAQ be?", "As long as needed, but each answer short; {brand} accepts up to about 6,000 characters.")],
    },
    "ai-vs-keyword-dm-automation": {
        "title": "AI replies vs keyword automations for Instagram DMs",
        "description": "When to use keyword automations and when to use an AI DM agent on Instagram, and how they work together.",
        "answer": "Use keyword automations for predictable, high-volume flows (comment GUIDE, get the guide) because they are "
                  "instant, exact and free of AI cost. Use an AI DM agent for open questions people type in their own words "
                  "(price, how it works, which plan). The best setup uses both: keywords first, AI for everything else.",
        "sections": [
            ("Side by side", "<div class=\"scroll\"><table><thead><tr><th></th><th>Keyword automation</th><th>AI DM agent</th></tr></thead><tbody>"
             "<tr><td>Best for</td><td>Freebies, links, lead capture</td><td>Questions in free text</td></tr>"
             "<tr><td>Speed</td><td>Instant</td><td>Seconds</td></tr><tr><td>Cost</td><td>Included</td><td>Uses AI replies</td></tr>"
             "<tr><td>Languages</td><td>The text you wrote</td><td>Replies in their language</td></tr></tbody></table></div>"),
            ("How {brand} combines them", "<p>A DM that matches a keyword runs the automation; anything else goes to the AI (if on), "
             "or to a welcome message for first-time chats.</p>"),
        ],
        "faq": [("Do I need AI to start?", "No. Most creators start with keyword automations and add AI when DMs get busy.")],
    },
    # lead generation
    "collect-whatsapp-numbers-from-instagram": {
        "title": "How to collect WhatsApp numbers from Instagram",
        "description": "Ask for a WhatsApp number inside the Instagram DM before sending your freebie, and send leads to Sheets or your CRM.",
        "answer": "To collect WhatsApp numbers from Instagram, use a comment-to-DM automation that asks for the number in the DM "
                  "before sending the freebie. The number is checked, saved to your contacts and can go to Google Sheets or a "
                  "CRM, so you can follow up on WhatsApp.",
        "sections": [
            ("Setup", "<ol><li>Create a comment or DM keyword automation.</li><li>Turn on <b>Ask for WhatsApp number</b>; choose required or with a Skip button.</li>"
             "<li>Write why you need it (\"to send updates and the class link\").</li><li>Connect Google Sheets or a webhook if your team follows up.</li></ol>"),
            ("Respect consent", "<p>Only message numbers people gave you for that purpose, say what you'll send, and make it easy to opt out.</p>"),
        ],
        "faq": [("Does it check the number format?", "Yes, and it asks again politely if the reply isn't a valid number.")],
    },
    "instagram-dm-choice-menus": {
        "title": "How to use choice menus in Instagram DMs",
        "description": "Let people pick what they want in your Instagram DM with up to 3 buttons: free vs paid, by goal, by level or by product.",
        "answer": "A choice menu is a DM with up to three buttons, each sending its own message and link. Use it to let people "
                  "pick free vs paid, their goal, their level or a product, so one automation serves different people and you "
                  "learn what your audience wants from the picks.",
        "sections": [
            ("Menu ideas", "<ul><li>\"Free guide / Full course / Book a call\".</li><li>\"Beginner / Intermediate / Advanced\".</li>"
             "<li>\"Skincare / Makeup / Outfit\".</li><li>\"Class 10 / Class 12 / Competitive exams\".</li></ul>"),
            ("Learn from the picks", "<p>{brand}'s insights count how many people picked each option, so you know what to make next.</p>"),
        ],
        "faq": [("Why only three options?", "Instagram allows up to three buttons in a DM message.")],
    },
    # DM automation
    "instagram-next-post-automation": {
        "title": "How to set up Instagram auto DMs before you post",
        "description": "Create the comment-to-DM automation before posting a reel, so the first comments get answered instantly.",
        "answer": "To have auto DMs ready before you post, create the automation for your next post instead of a specific reel. "
                  "When you publish, the automation attaches to the new reel by itself, so even the first comments get their DM "
                  "within seconds.",
        "sections": [
            ("Steps in {brand}", "<ol><li>Auto DM → Create → Comments on your post or reel → <b>Next post</b>.</li><li>Add the keyword, replies and DM.</li>"
             "<li>Publish the reel whenever you like; the automation moves onto it automatically.</li></ol>"),
            ("Auto-setup from the caption", "<p>Or turn on auto-setup: write \"Comment GUIDE\" in the caption and {brand} creates the automation from your template.</p>"),
        ],
        "faq": [("What if I post a story or another reel first?", "It attaches to the next post or reel published after you created it.")],
    },
    "instagram-live-comment-automation": {
        "title": "How to auto DM people who comment on your Instagram Live",
        "description": "Send a link by DM to everyone who comments a keyword during your Instagram Live, without stopping the stream.",
        "answer": "To auto DM people during an Instagram Live, set up a Live-comment automation with a keyword such as LINK; "
                  "everyone who comments it during the Live gets a DM with your link, so you can keep talking while the links go out.",
        "sections": [
            ("Setup", "<ol><li>Auto DM → Create → Comments on your Live.</li><li>Keyword (LINK, JOIN, OFFER) and the DM with a button.</li>"
             "<li>Say \"comment LINK\" a few times during the Live.</li></ol>"),
            ("Good to know", "<p>Live comments get a DM only (no public reply). The feature is in beta and needs Live comment events enabled for the app.</p>"),
        ],
        "faq": [("Does it work after the Live ends?", "Comments made during the Live are handled; the DM must go within Instagram's private-reply window.")],
    },
    "instagram-welcome-message": {
        "title": "How to set an automatic welcome message on Instagram",
        "description": "Greet everyone who DMs you for the first time with an automatic message and buttons to your links or automations.",
        "answer": "An Instagram welcome message is sent automatically the first time someone DMs you (when their message doesn't "
                  "match a keyword), with buttons to your main links or automations, so new chats get an instant answer instead "
                  "of waiting.",
        "sections": [
            ("What to write", "<p>\"Hey {username}! 👋 Thanks for the message. What are you looking for?\" with up to three buttons: "
             "\"Free guide\", \"Courses\", \"Work with me\".</p>"),
            ("Welcome message vs chat menu", "<ul><li>The <b>welcome message</b> is sent once to new chats.</li>"
             "<li>The <b>chat menu</b> (ice breakers) shows up to four questions before someone types.</li><li>Use both for the smoothest first contact.</li></ul>"),
        ],
        "faq": [("Will regulars get it again?", "No, each person gets it once.")],
    },
    "instagram-ice-breakers": {
        "title": "Instagram ice breakers: set up a DM chat menu",
        "description": "Add up to 4 ice breaker questions to your Instagram DMs and answer them automatically or start an automation.",
        "answer": "Instagram ice breakers are up to four questions shown to people when they open a chat with you for the first "
                  "time. Tapping one sends it, and {brand} answers it automatically or starts one of your automations.",
        "sections": [
            ("Good ice breakers", "<ul><li>\"How do I buy the course?\"</li><li>\"Where are the free guides?\"</li>"
             "<li>\"Do you do collaborations?\"</li><li>\"What's the price?\"</li></ul>"),
            ("Setup", "<p>Auto DM → Chat menu: add up to four questions, choose an answer or an automation for each, and publish.</p>"),
        ],
        "faq": [("How many questions can I add?", "Up to four, Instagram's limit.")],
    },
})


# =====================================================================================================================
# Pillar-cluster (hub-and-spoke) architecture with entity-first coverage.
# Each PILLAR is a topic hub: a long overview page that links down to every cluster page in its topic. Every cluster
# page (feature, comparison or guide) belongs to exactly one pillar, links back up to it and across to its siblings.
# ENTITIES are the real-world things the topic is about (sent as schema.org "about"/"mentions" with sameAs links);
# GLOSSARY defines the domain concepts as DefinedTerms that pages link to.
# =====================================================================================================================

ENTITIES = {
    "instagram": {"name": "Instagram", "type": "Thing", "sameAs": "https://en.wikipedia.org/wiki/Instagram"},
    "meta": {"name": "Meta Platforms", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/Meta_Platforms"},
    "whatsapp": {"name": "WhatsApp", "type": "Thing", "sameAs": "https://en.wikipedia.org/wiki/WhatsApp"},
    "chatbot": {"name": "Chatbot", "type": "Thing", "sameAs": "https://en.wikipedia.org/wiki/Chatbot"},
    "lead-generation": {"name": "Lead generation", "type": "Thing", "sameAs": "https://en.wikipedia.org/wiki/Lead_generation"},
    "influencer-marketing": {"name": "Influencer marketing", "type": "Thing", "sameAs": "https://en.wikipedia.org/wiki/Influencer_marketing"},
    "utm": {"name": "UTM parameters", "type": "Thing", "sameAs": "https://en.wikipedia.org/wiki/UTM_parameters"},
    "claude": {"name": "Claude (language model)", "type": "Thing", "sameAs": "https://en.wikipedia.org/wiki/Claude_(language_model)"},
    "ecommerce": {"name": "E-commerce", "type": "Thing", "sameAs": "https://en.wikipedia.org/wiki/E-commerce"},
}

PILLARS = {
    "instagram-dm-automation": {
        "title": "Instagram DM automation: the complete guide",
        "short": "Instagram DM automation",
        "description": "Everything about Instagram DM automation: how comment-to-DM and story replies work, Instagram's rules and limits, safety, setup and troubleshooting.",
        "answer": "Instagram DM automation is software that sends Instagram direct messages for you when something happens: "
                  "someone comments a keyword, replies to your story, mentions you, or messages you. It runs on Meta's official "
                  "Instagram API, follows Instagram's messaging rules (a private reply within 7 days of a comment, a 24-hour "
                  "window after their last message) and lets creators reply to thousands of people instantly.",
        "about": ["instagram", "meta", "chatbot"],
        "terms": ["comment-to-dm", "keyword-trigger", "private-reply", "messaging-window", "opening-dm", "story-reply-automation",
                  "story-mention", "rate-limit", "professional-account", "instagram-api", "message-variations"],
        "sections": [
            ("How it works", "<p>A creator connects an Instagram <a href=\"/glossary#professional-account\">professional account</a> "
             "through the <a href=\"/glossary#instagram-api\">official Instagram API</a> and sets triggers. The most common is "
             "<a href=\"/features/comment-to-dm\">comment-to-DM</a>: a <a href=\"/glossary#keyword-trigger\">keyword</a> in a comment "
             "starts a public reply and a DM. Others are <a href=\"/features/story-replies\">story replies and mentions</a> and keyword DMs. "
             "Start with <a href=\"/guides/how-to-auto-dm-instagram-comments\">how to auto DM people who comment</a>.</p>"),
            ("Instagram's rules", "<p>Instagram allows one <a href=\"/glossary#private-reply\">private reply</a> per comment within 7 days, "
             "messages within the <a href=\"/glossary#messaging-window\">24-hour window</a> after a person's last message, and caps "
             "messages per hour. <a href=\"/guides/instagram-dm-limits\">Instagram DM limits explained</a> covers each rule.</p>"),
            ("Safety", "<p>Tools on the official API, without your password and with <a href=\"/glossary#message-variations\">message variations</a>, "
             "stay within the rules. Read <a href=\"/guides/is-instagram-dm-automation-safe\">is Instagram DM automation safe?</a></p>"),
            ("Setup and troubleshooting", "<ul><li><a href=\"/guides/switch-to-instagram-professional-account\">Switch to a professional account</a></li>"
             "<li><a href=\"/guides/instagram-comment-keyword-ideas\">40 keyword ideas</a></li><li><a href=\"/guides/auto-reply-instagram-comments\">Auto-reply to comments</a></li>"
             "<li><a href=\"/guides/instagram-story-auto-reply\">Story auto-reply</a></li><li><a href=\"/guides/instagram-next-post-automation\">Set it up before you post</a></li>"
             "<li><a href=\"/guides/instagram-live-comment-automation\">Auto DM on Live comments</a></li><li><a href=\"/guides/instagram-welcome-message\">Welcome message</a> and <a href=\"/guides/instagram-ice-breakers\">ice breakers</a></li>"
             "<li><a href=\"/guides/why-instagram-dm-not-sent\">Why a DM wasn't sent</a></li></ul>"),
        ],
        "faq": [("What is Instagram DM automation?", "Software that sends Instagram DMs automatically when someone comments a keyword, replies to a story, mentions you or messages you, using Meta's official API."),
                ("Is it allowed?", "Yes, when it uses the official Instagram API and follows Instagram's messaging rules."),
                ("What do I need to start?", "An Instagram Business or Creator account and a tool such as {brand}; the free plan includes 1,000 DMs a month.")],
        "clusters": [("guide", "instagram-next-post-automation"), ("guide", "instagram-live-comment-automation"), ("guide", "instagram-welcome-message"), ("guide", "instagram-ice-breakers"), ("feature", "comment-to-dm"), ("feature", "story-replies"), ("guide", "how-to-auto-dm-instagram-comments"),
                     ("guide", "auto-reply-instagram-comments"), ("guide", "instagram-story-auto-reply"), ("guide", "instagram-comment-keyword-ideas"),
                     ("guide", "instagram-dm-limits"), ("guide", "is-instagram-dm-automation-safe"), ("guide", "why-instagram-dm-not-sent"),
                     ("guide", "switch-to-instagram-professional-account")],
    },
    "instagram-lead-generation": {
        "title": "Instagram lead generation with DMs",
        "short": "Instagram lead generation",
        "description": "How to turn Instagram followers and reel viewers into leads: follow gates, email and WhatsApp capture, lead magnets and giveaways.",
        "answer": "Instagram lead generation with DMs means offering something useful (a lead magnet) for a comment, then using the "
                  "DM to win a follow, collect an email or WhatsApp number, and tag the person by interest, so you can follow up "
                  "later instead of losing them after one view.",
        "about": ["lead-generation", "instagram", "whatsapp"],
        "terms": ["lead-magnet", "follow-gate", "lead-capture", "contact-tags", "giveaway-picker"],
        "sections": [
            ("The building blocks", "<ul><li>A <a href=\"/glossary#lead-magnet\">lead magnet</a>: see <a href=\"/guides/instagram-lead-magnet-ideas\">lead magnet ideas</a>.</li>"
             "<li>A <a href=\"/glossary#follow-gate\">follow gate</a>: <a href=\"/features/follow-to-unlock\">follow to unlock</a> turns viewers into followers.</li>"
             "<li><a href=\"/glossary#lead-capture\">Lead capture</a> in the DM: <a href=\"/features/lead-capture\">emails and WhatsApp numbers</a>.</li>"
             "<li><a href=\"/glossary#contact-tags\">Tags</a> by topic, so follow-ups are relevant.</li></ul>"),
            ("Playbooks", "<ul><li><a href=\"/guides/get-followers-from-reels\">Turn reel views into followers</a></li>"
             "<li><a href=\"/guides/how-to-collect-emails-from-instagram\">Collect emails from Instagram</a></li>"
             "<li><a href=\"/guides/run-instagram-giveaway\">Run a giveaway and pick a winner</a></li>"
             "<li><a href=\"/guides/collect-whatsapp-numbers-from-instagram\">Collect WhatsApp numbers</a></li><li><a href=\"/guides/instagram-dm-choice-menus\">Use choice menus</a> to sort leads by interest</li></ul>"),
        ],
        "faq": [("What's the best way to get leads from Instagram?", "Ask for a comment keyword in exchange for a free resource, then collect an email or WhatsApp number in the DM before sending it."),
                ("Should I gate with a follow or an email?", "A follow grows your audience; an email or WhatsApp number lets you reach people outside Instagram. Many creators use both.")],
        "clusters": [("guide", "collect-whatsapp-numbers-from-instagram"), ("guide", "instagram-dm-choice-menus"), ("feature", "follow-to-unlock"), ("feature", "lead-capture"), ("guide", "get-followers-from-reels"),
                     ("guide", "how-to-collect-emails-from-instagram"), ("guide", "instagram-lead-magnet-ideas"), ("guide", "run-instagram-giveaway")],
    },
    "sell-on-instagram": {
        "title": "Selling on Instagram with DMs",
        "short": "Selling on Instagram",
        "description": "How creators and stores sell on Instagram through DMs: follow-up offers, broadcasts, product links and tracking which reel made each sale.",
        "answer": "Selling on Instagram with DMs works by giving value first (a freebie by DM), following up within 24 hours with "
                  "the paid product, broadcasting launches to recent chats, and attributing each sale to the reel that brought it, "
                  "so you know which content actually earns money.",
        "about": ["ecommerce", "instagram", "utm"],
        "terms": ["follow-up-message", "broadcast", "sales-attribution", "utm-parameters", "choice-menu"],
        "sections": [
            ("The selling loop", "<ol><li>Free value by DM.</li><li>A <a href=\"/glossary#follow-up-message\">follow-up offer</a> inside the 24-hour window.</li>"
             "<li>A <a href=\"/glossary#broadcast\">broadcast</a> on launch day.</li><li><a href=\"/glossary#sales-attribution\">Sales attribution</a> per reel: <a href=\"/features/sales-tracking\">sales tracking</a>.</li></ol>"),
            ("Playbooks", "<ul><li><a href=\"/guides/instagram-dm-sales-funnel\">Build a DM sales funnel</a></li><li><a href=\"/guides/instagram-follow-up-messages\">Write follow-ups that sell</a></li>"
             "<li><a href=\"/guides/instagram-broadcast-messages\">Broadcast to recent chats</a></li><li><a href=\"/guides/track-instagram-sales-with-utm\">Track sales with UTM links</a></li>"
             "<li><a href=\"/guides/sell-digital-products-on-instagram\">Sell digital products</a></li>"
             "<li><a href=\"/guides/instagram-dm-automation-for-ecommerce\">DM automation for online stores</a></li></ul>"),
        ],
        "faq": [("How do I know which reel made a sale?", "Use tracked links and a sales link on your payment page's thank-you redirect; {brand} credits each sale to the reel and automation."),
                ("When should I send the paid offer?", "A few hours after the free resource, inside Instagram's 24-hour messaging window.")],
        "clusters": [("guide", "instagram-dm-sales-funnel"), ("guide", "instagram-follow-up-messages"), ("guide", "instagram-broadcast-messages"), ("guide", "track-instagram-sales-with-utm"), ("feature", "sales-tracking"), ("guide", "sell-digital-products-on-instagram"), ("guide", "instagram-dm-automation-for-ecommerce")],
    },
    "ai-instagram-dm-replies": {
        "title": "AI replies for Instagram DMs",
        "short": "AI for Instagram DMs",
        "description": "How AI agents answer Instagram DMs: what they should and shouldn't answer, languages, hand-offs to a human, and setup.",
        "answer": "An AI DM agent for Instagram reads incoming messages that don't match an automation and replies from the "
                  "creator's own FAQ, products and links, in the language the person writes in, and hands sensitive chats "
                  "(refunds, collaborations, anything uncertain) to a human with a suggested reply.",
        "about": ["chatbot", "claude", "instagram"],
        "terms": ["ai-dm-agent", "human-handoff", "messaging-window"],
        "sections": [
            ("What a good AI agent does", "<ul><li>Answers only from your information; never invents prices or links.</li>"
             "<li>Replies in the person's language.</li><li>Uses a <a href=\"/glossary#human-handoff\">human hand-off</a> for anything sensitive.</li></ul>"
             "<p>See the <a href=\"/features/ai-dm-agent\">AI DM agent</a>, <a href=\"/guides/instagram-ai-chatbot\">how to set up an AI chatbot for Instagram</a>, "
             "<a href=\"/guides/write-faq-for-ai-dm-agent\">how to write its FAQ</a> and <a href=\"/guides/ai-vs-keyword-dm-automation\">when to use AI vs keywords</a>.</p>"),
        ],
        "faq": [("Can AI reply to Instagram DMs automatically?", "Yes, through the official API, within Instagram's 24-hour messaging window.")],
        "clusters": [("guide", "write-faq-for-ai-dm-agent"), ("guide", "ai-vs-keyword-dm-automation"), ("feature", "ai-dm-agent"), ("guide", "instagram-ai-chatbot")],
    },
    "instagram-dm-automation-tools": {
        "title": "Instagram DM automation tools compared",
        "short": "DM automation tools",
        "description": "Compare Instagram DM automation tools: prices, free plans, follow gates, AI replies and per-contact vs flat pricing.",
        "answer": "Instagram DM automation tools differ mainly in pricing model (per contact, per DM volume or flat), free-plan size "
                  "(about 500–1,500 DMs a month), whether the follow gate and story replies are on the plan you buy, and whether "
                  "AI replies are included. Start with the overview, then compare tools one by one.",
        "about": ["instagram", "chatbot", "influencer-marketing"],
        "terms": ["per-contact-pricing", "follow-gate", "ai-dm-agent"],
        "sections": [
            ("Start here", "<ul><li><a href=\"/guides/best-instagram-dm-automation-tools\">Best Instagram DM automation tools in 2026</a></li>"
             "<li><a href=\"/guides/instagram-dm-automation-pricing\">Pricing compared</a></li><li><a href=\"/guides/manychat-alternatives\">ManyChat alternatives</a></li></ul>"),
            ("One-to-one comparisons", "<p>Each comparison is dated and notes where the other tool is the better choice. See them all below.</p>"),
        ],
        "faq": [("What does Instagram DM automation cost?", "From free (about 500–1,500 DMs a month) to about $9–$40 a month; Indian tools are typically ₹99–₹499. {brand} is ₹199 / $9.")],
        "clusters": [("guide", "best-instagram-dm-automation-tools"), ("guide", "instagram-dm-automation-pricing"), ("guide", "manychat-alternatives")]
                    + [("compare", k) for k in ("manychat", "linkdm", "superprofile", "repli", "replykaro", "instantdm", "replyrush",
                                                 "creatorflow", "zorcha", "inro", "rapiddm")],
    },
    "instagram-automation-by-industry": {
        "title": "Instagram DM automation by industry",
        "short": "By industry",
        "description": "Instagram DM automation playbooks for coaches, fitness, finance, education, food, beauty, travel, real estate and astrology.",
        "answer": "Every industry uses the same building blocks (keyword, DM, lead capture, follow-up, AI answers), but the offer, "
                  "keywords and compliance points differ. These playbooks give each niche a ready funnel, keyword list and the "
                  "questions an AI agent should and shouldn't answer.",
        "about": ["influencer-marketing", "lead-generation", "instagram"],
        "terms": ["lead-magnet", "choice-menu", "human-handoff"],
        "sections": [
            ("How to use these playbooks", "<p>Pick your niche, copy the funnel into an automation, swap in your offer and keywords, and "
             "list the hand-off topics for the AI. Compliance notes (finance, real estate, food, health) are included where they matter.</p>"),
        ],
        "faq": [("Does DM automation work for service businesses?", "Yes: real estate, salons, coaches, tutors and travel agencies use it to qualify enquiries before a call.")],
        "clusters": [("guide", g) for g in ("instagram-dm-automation-for-coaches", "instagram-dm-automation-for-fitness-coaches",
                                             "instagram-dm-automation-for-finance-creators", "instagram-dm-automation-for-educators",
                                             "instagram-dm-automation-for-food-creators", "instagram-dm-automation-for-beauty-creators",
                                             "instagram-dm-automation-for-travel-creators", "instagram-dm-automation-for-real-estate",
                                             "instagram-dm-automation-for-astrologers")],
    },
}

# Domain concepts, defined once and linked from pages (schema.org DefinedTerm on /glossary).
GLOSSARY = {
    "instagram-dm-automation": ("Instagram DM automation", "Software that sends Instagram direct messages automatically when a trigger happens, such as a keyword comment, story reply or DM.", "/instagram-dm-automation"),
    "comment-to-dm": ("Comment-to-DM", "An automation that sends a DM (and often a public reply) to each person who comments a chosen keyword on a post or reel.", "/features/comment-to-dm"),
    "keyword-trigger": ("Keyword trigger", "The word that starts an automation when it appears in a comment, story reply or DM, matched regardless of capitals, plurals and emojis.", "/guides/instagram-comment-keyword-ideas"),
    "private-reply": ("Private reply", "Instagram's name for a DM sent to someone in response to their comment; allowed once per comment within 7 days.", "/guides/instagram-dm-limits"),
    "messaging-window": ("24-hour messaging window", "The period after a person's last message during which a business account may send them messages.", "/guides/instagram-dm-limits"),
    "opening-dm": ("Opening DM", "The first message of a flow, usually with a button; tapping it opens the chat so later messages and follow checks are allowed.", "/features/comment-to-dm"),
    "follow-gate": ("Follow gate (follow to unlock)", "A step that sends the promised link only after the person follows the account, checked through the official API.", "/features/follow-to-unlock"),
    "lead-magnet": ("Lead magnet", "A free resource (checklist, template, guide) offered in exchange for a comment, follow or contact details.", "/guides/instagram-lead-magnet-ideas"),
    "lead-capture": ("Lead capture", "Asking for an email address or WhatsApp number inside the DM before sending the resource, and saving the answer.", "/features/lead-capture"),
    "contact-tags": ("Contact tags", "Labels added to people automatically (for example by reel or topic) so follow-ups and exports can be targeted.", "/features/lead-capture"),
    "story-reply-automation": ("Story reply automation", "A DM sent automatically when someone replies to your Instagram story, optionally only with a keyword.", "/features/story-replies"),
    "story-mention": ("Story mention automation", "A DM sent automatically when someone mentions your account in their story, often a thank-you.", "/features/story-replies"),
    "choice-menu": ("Choice menu", "A DM with up to three buttons, each sending its own message and link, so people pick what they want.", "/guides/instagram-dm-automation-for-coaches"),
    "follow-up-message": ("Follow-up message", "A second DM sent hours after the first, inside the 24-hour window, usually with a paid offer.", "/guides/sell-digital-products-on-instagram"),
    "broadcast": ("Broadcast to recent chats", "One message sent to everyone who messaged the account in the last 24 hours, the only group Instagram allows.", "/sell-on-instagram"),
    "ai-dm-agent": ("AI DM agent", "An AI that answers DMs from the creator's own FAQ and products, in the person's language, and hands sensitive chats to a human.", "/features/ai-dm-agent"),
    "human-handoff": ("Human hand-off", "When the AI stops answering a chat and passes it to the creator with the reason and a suggested reply.", "/guides/instagram-ai-chatbot"),
    "message-variations": ("Message variations", "Writing {Hi|Hey|Hello} so each person gets one option at random, so automated DMs don't look identical.", "/guides/is-instagram-dm-automation-safe"),
    "rate-limit": ("Rate limit", "Instagram's cap on how many automated messages an account can send in a period; good tools pause and resume.", "/guides/instagram-dm-limits"),
    "professional-account": ("Instagram professional account", "A Business or Creator account, required for DM automation; switching is free.", "/guides/switch-to-instagram-professional-account"),
    "instagram-api": ("Instagram API with Instagram Login", "Meta's official API that lets approved apps read comments and send DMs for a professional account without its password.", "/guides/is-instagram-dm-automation-safe"),
    "utm-parameters": ("UTM parameters", "Tags added to a link (utm_source, utm_medium, utm_campaign) so analytics tools show where visitors came from.", "/features/sales-tracking"),
    "sales-attribution": ("Sales attribution", "Crediting each sale to the reel and automation whose link the buyer tapped before paying.", "/features/sales-tracking"),
    "per-contact-pricing": ("Per-contact pricing", "A pricing model that charges by the number of people messaged, which rises when a reel goes viral; the alternative is flat pricing.", "/instagram-dm-automation-tools"),
    "giveaway-picker": ("Giveaway picker", "A tool that picks random winners from a post's comments, one entry per person, with optional rules.", "/guides/run-instagram-giveaway"),
}


def pillar_of():
    """(kind, slug) → pillar slug, for every cluster page."""
    return {c: p for p, data in PILLARS.items() for c in data["clusters"]}


def all_paths():
    return (["/", "/features", "/compare", "/guides", "/glossary", "/privacy", "/terms"] + [f"/{k}" for k in PILLARS]
            + [f"/features/{k}" for k in FEATURES] + [f"/vs/{k}" for k in COMPARE] + [f"/guides/{k}" for k in GUIDES])
