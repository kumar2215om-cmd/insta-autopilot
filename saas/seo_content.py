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


def all_paths():
    return (["/", "/features", "/compare", "/guides", "/privacy", "/terms"]
            + [f"/features/{k}" for k in FEATURES] + [f"/vs/{k}" for k in COMPARE] + [f"/guides/{k}" for k in GUIDES])
