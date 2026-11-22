"""Long-form versions of the most important public pages (SEO batch B).

seo_content.py holds every page's short version; DEEP replaces the sections and FAQ (and, where given, the answer or the
comparison lists) of the pages below with 800–1,500 words of steps, examples, tables and real dashboard screenshots
(static/seo/*.jpg, taken from the demo account). Facts about other tools stay hedged and dated ("checked November 2026").
"{brand}" is replaced with the brand name when rendering.
"""

WIDE = (1280, 800)
WIZ = (560, 768)


def fig(img, alt, caption, size=WIDE):
    w, h = size
    cls = ' class="narrow"' if w < 1000 else ""
    return (f'<figure{cls}><img src="/static/seo/{img}.jpg" alt="{alt}" width="{w}" height="{h}" loading="lazy" decoding="async">'
            f"<figcaption>{caption}</figcaption></figure>")


PLANS_TABLE = ("<div class=\"scroll\"><table><thead><tr><th>Plan</th><th>Price a month</th><th>DMs a month</th><th>What it adds</th></tr></thead><tbody>"
               "<tr><td>Free</td><td>₹0</td><td>1,000</td><td>Comment-to-DM, keyword DMs, Live comments, link in bio, 25 AI replies to try</td></tr>"
               "<tr><td>Starter</td><td>₹149 / $5</td><td>3,000</td><td>Follow to unlock, email and WhatsApp capture, story replies and mentions</td></tr>"
               "<tr><td>Creator</td><td>₹199 / $9</td><td>No monthly limit*</td><td>300 AI replies, Lead Qualifier agent, course extras</td></tr>"
               "<tr><td>Pro</td><td>₹599 / $19</td><td>No monthly limit*</td><td>3 accounts, 2,000 AI replies, Claude (MCP), 2% fee on sales</td></tr>"
               "<tr><td>Agency</td><td>₹2,000 / $59</td><td>No monthly limit*</td><td>10 accounts, 10,000 AI replies, one Claude link for all</td></tr>"
               "</tbody></table></div><p class=\"note\">* Fair use; Instagram's own limits still apply. Full details on the <a href=\"/pricing\">pricing page</a>.</p>")

DEEP = {}

# ---------------------------------------------------------------- features

DEEP[("feature", "comment-to-dm")] = {
    "sections": [
        ("What comment-to-DM is, in one example",
         "<p>You post a reel: <i>\"Maine 39 AI video prompts ki list banayi hai. Comment PROMPTS and I'll DM you all of them.\"</i> "
         "Priya comments <code>prompts 🔥</code>. Within a few seconds three things happen without you touching your phone:</p>"
         "<ol><li>Her comment gets a public reply such as <i>\"@priya Check your DM 📩\"</i>, which tells everyone else the offer is real.</li>"
         "<li>She gets a DM from you with the prompt pack, usually behind a button.</li>"
         "<li>Her handle (and, if you ask, her email or WhatsApp number) is saved in your Leads list, tagged with the reel she came from.</li></ol>"
         "<p>Multiply that by 800 comments on a reel that takes off, and you can see why creators use it: nobody waits, nobody is missed, "
         "and the comment count itself pushes the reel to more people.</p>"
         + fig("auto-dm-list", "ReplyInbox Auto DM dashboard showing DMs sent, leads collected, followers gained and a list of comment automations with runs and button clicks",
               "The Auto DM page: every automation with its runs, button clicks, followers gained and sales.")),
        ("How to set it up (5 minutes)",
         "<ol><li><b>Connect Instagram.</b> Sign in with Google, then connect your Instagram <b>Business or Creator</b> account through Meta's "
         "official login. {brand} never sees your password. (Personal account? <a href=\"/guides/switch-to-instagram-professional-account\">Switch "
         "for free</a> first.)</li>"
         "<li><b>Create automation → Comments on your post or reel.</b> Pick the reel, choose <b>any post</b> (one keyword for all your posts), "
         "or <b>your next post</b> so it's ready before you publish.</li>"
         "<li><b>Set the keyword.</b> One short word like <code>GUIDE</code> or <code>PROMPTS</code>. Capitals, plurals, small spelling "
         "mistakes and emojis around it still match. Add excluded words if you want to skip comments like \"price?\".</li>"
         "<li><b>Write up to 3 public replies.</b> One is picked at random each time so your replies don't look like a bot.</li>"
         "<li><b>Write the DM.</b> Add up to 3 link buttons, or a choice menu, and optionally a follow gate or email capture before the link.</li>"
         "<li><b>Review and launch.</b> The last step shows exactly what a fan will see, message by message.</li></ol>"
         + fig("wizard-keyword", "Automation editor step: choose specific keyword PROMPTS, once per person option and rotating comment replies",
               "Step 2: the keyword, once-per-person and the rotating public replies.", WIZ)),
        ("Everything you can add to the DM",
         "<div class=\"scroll\"><table><thead><tr><th>Option</th><th>What it does</th><th>Plan</th></tr></thead><tbody>"
         "<tr><td>Up to 3 link buttons</td><td>Course, freebie and product, each with its own button and click count</td><td>All</td></tr>"
         "<tr><td>Choice menu</td><td>Up to 3 options; each sends its own message (\"Free guide\" / \"Course details\")</td><td>All</td></tr>"
         "<tr><td>Opening message with a button</td><td>A short first DM; the tap opens the chat. Can be A/B tested</td><td>All</td></tr>"
         "<tr><td>Follow to unlock</td><td>The link goes only to people who follow you</td><td>Starter+</td></tr>"
         "<tr><td>Email or WhatsApp capture</td><td>Ask for it before the link, required or with a Skip button</td><td>Starter+</td></tr>"
         "<tr><td>Follow-up offer</td><td>A second DM 1–20 hours later, e.g. your paid product</td><td>All</td></tr>"
         "<tr><td>Delay</td><td>Wait 1–10 minutes before the first DM so it feels human</td><td>All</td></tr>"
         "<tr><td>Once per person</td><td>Someone who comments 5 times gets one DM</td><td>All</td></tr>"
         "<tr><td>Message variations</td><td><code>{Hi|Hey|Hello}</code> picks one option per person</td><td>All</td></tr>"
         "<tr><td>Schedule</td><td>Start and end time, e.g. a 48-hour launch offer</td><td>All</td></tr>"
         "</tbody></table></div>"),
        ("Instagram's rules, and how {brand} stays inside them",
         "<p>Instagram allows a business account to send <b>one private reply per comment, within 7 days</b> of the comment. After the person "
         "replies or taps a button, you can keep messaging them for 24 hours. Accounts also have hourly limits on automated messages, which a "
         "viral reel can reach.</p>"
         "<p>{brand} works on Meta's official Instagram API, so it follows these rules automatically: it slows down instead of failing when "
         "Instagram asks it to, retries DMs Instagram refused (once a day for 6 days), times follow-ups inside the 24-hour window and only "
         "sends to past comments that are less than 7 days old. Details: <a href=\"/guides/instagram-dm-limits\">Instagram DM limits explained</a>.</p>"),
        ("What results to expect",
         "<p>Numbers vary by niche and offer, but the pattern is consistent: a clear freebie plus a one-word keyword gets far more comments than "
         "\"link in bio\", because commenting is easier than leaving the app. Two things move the needle most:</p>"
         "<ul><li><b>The offer.</b> \"39 prompts\" beats \"my guide\". Specific and instant wins.</li>"
         "<li><b>Saying the keyword in the first 3 seconds</b> and showing it on screen, then repeating it in the caption.</li></ul>"
         "<p>The <a href=\"/features/sales-tracking\">reel report</a> shows the funnel for each reel: views, comments, how many used the keyword, "
         "got the DM, opened the link and followed. That tells you which hook to reuse.</p>"
         + fig("reel-report", "Reel report showing a funnel per reel: views, comments, used the keyword, got the DM, link sent and followed to unlock",
               "The reel report: from views to followers for every reel with an automation.")),
        ("Pricing", "<p>Comment-to-DM is on every plan, including Free with 1,000 DMs a month.</p>" + PLANS_TABLE),
    ],
    "faq": [
        ("Is comment-to-DM allowed by Instagram?", "Yes, when it uses Meta's official Instagram API. Instagram allows one private reply "
         "per comment within 7 days of the comment. {brand} uses the official API and never asks for your password."),
        ("Does it work on reels, posts and Lives?", "Yes: reels, photo and carousel posts, comments on your Live, plus story replies, story "
         "mentions and keyword DMs."),
        ("How many DMs can I send for free?", "1,000 DMs a month on the free plan, 3,000 on Starter, and no {brand} limit on Creator and above "
         "(fair use). Instagram's own hourly limits still apply."),
        ("Can I use one keyword on all my posts?", "Yes. Choose \"any post\" when you create the automation, and every post and reel answers that keyword."),
        ("What if someone comments the keyword twice?", "Turn on \"once per person\" and they get one DM, not two. It's safer for your account too."),
        ("Can it reply to comments without sending a DM?", "Yes. Turn off the DM and keep the public replies, or see "
         "<a href=\"/guides/auto-reply-instagram-comments\">auto-reply to Instagram comments</a>."),
    ],
}

DEEP[("feature", "follow-to-unlock")] = {
    "sections": [
        ("Why creators use a follow gate",
         "<p>A reel can reach lakhs of people who don't follow you. Comment-to-DM turns some of them into leads, but most still leave without "
         "following. A follow gate fixes that: the freebie is only sent once they follow, so every interested viewer becomes a follower.</p>"
         "<p>It works because the person has already decided they want the thing. Tapping Follow is a tiny step at that moment, and they "
         "can see your other content while they're on your profile.</p>"),
        ("What the fan sees",
         "<ol><li>They comment your keyword and get an opening DM with a button such as <i>\"Send me the access\"</i>.</li>"
         "<li>When they tap it, {brand} asks Instagram whether they follow you.</li>"
         "<li><b>Already a follower</b>: they get the link right away.</li>"
         "<li><b>Not yet</b>: they get a friendly message with two buttons, <b>Visit Profile</b> and <b>I'm following ✅</b>. After they follow "
         "and tap the second button, {brand} checks again and sends the link.</li></ol>"
         + fig("wizard-review", "Review screen showing the DM sequence: opening message with a Send me the access button, then a follow request with Visit Profile and I'm following buttons",
               "The review step shows each message a fan will get, in order.", WIZ)),
        ("Why the first DM has a button",
         "<p>Instagram only lets apps check whether someone follows you after that person interacts with your DM, for example by tapping a "
         "button. That's why the follow gate always starts with a short opening message and a button. It also has a second benefit: once they "
         "tap, the chat is open for 24 hours, so the link, the email question and a follow-up can all be delivered.</p>"
         "<p>You can A/B test the opening message. {brand} sends version A to half the people and version B to the other half, and shows how "
         "many in each group got the link.</p>"),
        ("How to turn it on",
         "<ol><li>Open an automation (or create one) and go to the DMs step.</li>"
         "<li>Under <b>Before the primary DM, send them…</b>, switch on <b>A DM asking to follow you</b>.</li>"
         "<li>Edit the message and the two button labels if you like. Hinglish works well: <i>\"Bas ek step 👀 Profile pe jaake Follow karo, "
         "phir neeche button dabao.\"</i></li>"
         "<li>Save. From now on the link only goes to followers.</li></ol>"
         + fig("wizard-primary-dm", "Automation editor with A DM asking to follow you switched on, with Visit Profile and I'm following buttons, plus email and WhatsApp capture",
               "Follow to unlock, email and WhatsApp capture can be combined in one automation.", WIZ)),
        ("Combine it with email or WhatsApp capture",
         "<p>The order is: follow check → email → WhatsApp number → your link. You can make the email required or offer a Skip button. "
         "Combining them gives you a follower <i>and</i> a way to reach them outside Instagram. See "
         "<a href=\"/guides/how-to-collect-emails-from-instagram\">how to collect emails from Instagram</a>.</p>"),
        ("Best practices",
         "<ul><li>Say it in the reel: \"Follow and comment GUIDE\". People expect the step and don't drop off.</li>"
         "<li>Keep the follow message short and friendly; no guilt-tripping.</li>"
         "<li>Use it for your best freebies, not every post. For pure reach, skip the gate.</li>"
         "<li>Watch the <b>Followed to unlock</b> number in the reel report to see which reel grows you fastest.</li></ul>"),
        ("Plans", "<p>Follow to unlock is on <b>Starter (₹149 a month)</b> and every plan above it.</p>" + PLANS_TABLE),
    ],
    "faq": [
        ("Can Instagram see that I use a follow gate?", "It runs on the official API with normal DMs and buttons, so it is within Instagram's rules. "
         "Don't promise anything in exchange for a follow that you don't deliver."),
        ("What if they unfollow after getting the link?", "Some will, but most stay because they followed for your content. The reel report "
         "shows follows won per reel so you can judge."),
        ("Does it work for story replies too?", "Yes. Story reply automations (Starter and up) can use the same follow gate."),
        ("Which plan includes follow to unlock?", "Starter (₹149 / $5 a month) and above."),
        ("Do they need to comment again after following?", "No. They tap \"I'm following ✅\" in the same chat and the link arrives."),
    ],
}

DEEP[("feature", "ai-dm-agent")] = {
    "sections": [
        ("What the AI DM agent does",
         "<p>Keyword automations handle the predictable DMs. Everything else (\"price kya hai?\", \"does it work on iPhone?\", \"refund "
         "chahiye\") usually waits hours for a reply. The AI DM agent answers those messages for you, using only the information you give it: "
         "your FAQ, your products, prices and links.</p>"
         "<ul><li>Answers in the language the person writes in: English, Hindi, Hinglish, Spanish, Tamil and more.</li>"
         "<li>Never invents prices or links. If it isn't sure, it doesn't guess.</li>"
         "<li>Hands over refunds, collabs, complaints and anything unclear to you, with the reason and a suggested reply.</li>"
         "<li>Keyword DMs still run as automations first; the AI only takes the rest.</li></ul>"
         + fig("ai-inbox", "AI Inbox with conversations labelled AI, Needs you and You, and a chat where the AI answers a price question in Hinglish with a UPI payment answer",
               "The AI Inbox: the AI answers a price question in Hinglish; the chats it handed over are marked \"Needs you\".")),
        ("How to set it up",
         "<ol><li>Open <b>AI Inbox → Teach your AI</b>.</li>"
         "<li>Write your FAQ in plain words: what you sell, prices, delivery, refund policy, how to book a call. Short answers are best.</li>"
         "<li>Add your products and links (or let {brand} read them from your link in bio page).</li>"
         "<li>Choose what it must always hand to you: refunds, brand deals, anything about health or money advice.</li>"
         "<li>Use <b>Try it</b> to ask it questions like a fan would, and fix any answer you don't like.</li>"
         "<li>Switch the AI on.</li></ol>"
         "<p>Tips for a good FAQ are in <a href=\"/guides/write-faq-for-ai-dm-agent\">how to write a FAQ for your AI DM agent</a>.</p>"),
        ("You stay in control",
         "<p>Every conversation is in the AI Inbox with three filters: <b>Needs you</b> (handed over), <b>AI handling</b> and <b>You</b>. "
         "If you reply yourself, the AI stays quiet in that chat until you hand it back. <b>Keep AI out</b> turns it off for one person, "
         "for example a friend or a brand you're negotiating with.</p>"
         "<p>Hand-off rules are explained in <a href=\"/guides/ai-handoff-rules\">AI hand-off rules</a>.</p>"),
        ("Example conversations",
         "<div class=\"scroll\"><table><thead><tr><th>Fan writes</th><th>AI replies (from your FAQ)</th></tr></thead><tbody>"
         "<tr><td>Bhai ye prompt pack kitne ka hai?</td><td>Abhi sirf ₹149 hai 🙌 Saare 39 packs, lifetime access. Yahan se le lo 👉 (your link)</td></tr>"
         "<tr><td>Can I pay with UPI?</td><td>Yes! UPI, card and netbanking all work, and the download comes instantly.</td></tr>"
         "<tr><td>Mujhe refund chahiye</td><td>Hands over to you: \"Refund request. Suggested reply: Sorry to hear that! Share your order email and I'll check.\"</td></tr>"
         "<tr><td>Collab karna hai, rates?</td><td>Hands over as a brand enquiry. On Pro, the Brand Collab agent lists the offer and can ask the brand for budget, deliverables and timeline.</td></tr>"
         "</tbody></table></div>"
         "<p>More examples: <a href=\"/guides/ai-dm-agent-examples\">AI DM agent examples</a>.</p>"),
        ("Which AI it uses and what happens to the data",
         "<p>The agent runs on Anthropic's Claude through the API. Conversations are not used to train the model. {brand} sends the AI only what "
         "it needs to answer: your FAQ and the recent messages in that chat. Read more in <a href=\"/guides/is-ai-safe-for-instagram-dms\">is AI "
         "safe for Instagram DMs?</a></p>"),
        ("How many AI replies you get",
         "<div class=\"scroll\"><table><thead><tr><th>Plan</th><th>AI replies</th></tr></thead><tbody>"
         "<tr><td>Free / Starter</td><td>25 to try</td></tr><tr><td>Creator ₹199</td><td>300 a month</td></tr>"
         "<tr><td>Pro ₹599</td><td>2,000 a month</td></tr><tr><td>Agency ₹2,000</td><td>10,000 a month</td></tr>"
         "</tbody></table></div><p>Need more? Any paid plan can add 1,000 AI replies for ₹99. There's no separate AI credit wallet: one reply is one "
         "reply, whatever its length. Compare costs in <a href=\"/guides/instagram-ai-chatbot-cost\">what an Instagram AI chatbot costs</a>.</p>"),
    ],
    "faq": [
        ("Which AI model does it use?", "Anthropic's Claude, through the API. Conversations are not used to train the model."),
        ("Can I see and edit what the AI says?", "Yes. The AI Inbox shows every chat; you can reply yourself, and the AI stays quiet until you hand it back."),
        ("Will it reply in Hindi or Hinglish?", "Yes. It answers in the language and style the person writes in, including Hinglish in Roman script."),
        ("What if it doesn't know the answer?", "It hands the chat to you with the reason and a suggested reply instead of guessing."),
        ("Does the AI also answer keyword DMs?", "No. Keyword automations run first; the AI answers the other DMs."),
        ("Is it on the free plan?", "Free and Starter include 25 AI replies to try. Creator includes 300 a month."),
    ],
}

DEEP[("feature", "story-replies")] = {
    "sections": [
        ("Two story automations",
         "<p><b>Story replies</b>: when someone replies to your story, they get a DM. You can reply to every story reply, or only to replies "
         "that contain a keyword like <code>LINK</code>. <b>Story mentions</b>: when someone mentions you in their own story, they get a DM, "
         "usually a thank-you or a discount code.</p>"
         "<p>Stories disappear in 24 hours, so speed matters. An instant DM catches people while they're still interested.</p>"),
        ("Why story replies work so well",
         "<ul><li><b>No link sticker limits.</b> Instead of one link sticker, say \"Reply LINK\" and send different links on different days.</li>"
         "<li><b>It opens a conversation.</b> A reply is a DM, so after your automated message you can keep chatting for 24 hours, "
         "add a <a href=\"/guides/instagram-follow-up-messages\">follow-up offer</a> or let the AI answer questions.</li>"
         "<li><b>Stories reach your warmest audience</b>: people who already follow you and watch daily. They convert better than reel viewers.</li></ul>"),
        ("How to set up a story reply automation",
         "<ol><li>Auto DM → <b>Create automation</b> → <b>Replies to your story</b>.</li>"
         "<li>Choose <b>any reply</b> or a <b>specific keyword</b> (LINK, YES, PRICE). Keyword matching ignores capitals and emojis.</li>"
         "<li>Optional: an opening message with a button, a follow gate, email or WhatsApp capture.</li>"
         "<li>Write the DM and add up to 3 link buttons.</li>"
         "<li>Save. It runs on every story you post until you switch it off.</li></ol>"
         + fig("wizard-story", "Story reply automation editor with an opening message, Send me the access button and the follow request switched on",
               "A story reply automation with an opening button and a follow gate.", WIZ)
         + "<p>Each person gets the DM once per story, so someone replying three times isn't messaged three times.</p>"),
        ("Story mention thank-yous",
         "<p>Create a second automation: <b>Mentions you in their story</b>. Write a warm message: <i>\"Thank you so much for the shoutout "
         "{username}! 🙏 Here's 10% off as a thank-you: THANKS10\"</i>. Each person gets it at most once a day. It costs you nothing, makes "
         "people feel seen and leads to more mentions.</p>"),
        ("Story ideas that get replies",
         "<div class=\"scroll\"><table><thead><tr><th>Story</th><th>Keyword</th><th>What the DM sends</th></tr></thead><tbody>"
         "<tr><td>\"Aaj ka offer sirf 24 ghante\"</td><td>LINK</td><td>The offer page with a buy button</td></tr>"
         "<tr><td>Poll: \"Want my editing preset?\"</td><td>YES</td><td>The preset download</td></tr>"
         "<tr><td>Behind the scenes of a product</td><td>PRICE</td><td>Price, link and a choice menu</td></tr>"
         "<tr><td>Webinar reminder</td><td>JOIN</td><td>The joining link and calendar time</td></tr>"
         "<tr><td>Reshared customer review</td><td>REVIEW</td><td>More reviews plus the course page</td></tr>"
         "</tbody></table></div>"
         "<p>Step by step with more ideas: <a href=\"/guides/instagram-story-auto-reply\">how to set up Instagram story auto-reply</a>.</p>"),
        ("Plans", "<p>Story reply and mention automations are on <b>Starter (₹149 a month)</b> and above. On Free, story replies are answered "
         "by the AI agent (25 replies to try) or by keyword DM automations.</p>" + PLANS_TABLE),
    ],
    "faq": [
        ("Which plan includes story automations?", "Starter (₹149 / $5 a month) and above, for both story replies and story mentions."),
        ("Can I reply only to replies with a keyword?", "Yes. Pick \"specific keyword\" and only replies containing it get the DM; others go to the AI or to you."),
        ("Does it work on close friends stories?", "Replies to any of your stories arrive as DMs, so the automation answers them the same way."),
        ("Will someone get the DM twice?", "No. Each person gets one DM per story, and one mention thank-you per day."),
        ("Can I add a follow gate to story replies?", "Yes, the same follow to unlock, email and WhatsApp steps work for stories."),
    ],
}

# ---------------------------------------------------------------- comparisons

DEEP[("compare", "manychat")] = {
    "sections": [
        ("Pricing: per contact vs flat",
         "<p>The biggest practical difference is how you pay. ManyChat prices its Pro plan by the number of <b>active contacts</b> (people "
         "who interacted with your account), starting at about $17 a month (checked November 2026) and rising as that number grows. A "
         "single viral reel can add thousands of contacts in a weekend, and the bill follows.</p>"
         "<p>{brand} charges a flat price that doesn't change when a reel goes viral, in rupees or dollars:</p>"
         "<div class=\"scroll\"><table><thead><tr><th></th><th>ManyChat</th><th>{brand}</th></tr></thead><tbody>"
         "<tr><td>Free plan</td><td>Yes, small contact limit</td><td>Yes, 1,000 DMs a month</td></tr>"
         "<tr><td>Entry paid plan</td><td>About $17/month, rises with contacts</td><td>₹149 / $5 (Starter), ₹199 / $9 (Creator)</td></tr>"
         "<tr><td>When a reel goes viral</td><td>Price can jump to the next contact tier</td><td>Same price (no DM cap from Creator up)</td></tr>"
         "<tr><td>AI replies</td><td>On higher plans or as an add-on</td><td>Included: 300 a month on Creator, 2,000 on Pro</td></tr>"
         "<tr><td>Currency and billing</td><td>US dollars, card</td><td>₹ with UPI or card (GST included), or $</td></tr>"
         "</tbody></table></div><p class=\"note\">ManyChat prices from its public pricing page, checked November 2026. Check its site before deciding.</p>"),
        ("Feature by feature (for Instagram)",
         "<div class=\"scroll\"><table><thead><tr><th>Feature</th><th>ManyChat</th><th>{brand}</th></tr></thead><tbody>"
         "<tr><td>Comment-to-DM with keywords</td><td>Yes</td><td>Yes, plus any-post and next-post</td></tr>"
         "<tr><td>Follow to unlock</td><td>Possible with flow conditions</td><td>Built in, one switch (Starter+)</td></tr>"
         "<tr><td>Email and WhatsApp number capture</td><td>Yes, with flow building</td><td>Built in, required or skippable</td></tr>"
         "<tr><td>Story replies and mentions</td><td>Yes</td><td>Yes (Starter+)</td></tr>"
         "<tr><td>AI answers to other DMs</td><td>On higher plans or add-on</td><td>Included, any language incl. Hinglish</td></tr>"
         "<tr><td>Sales per reel</td><td>Via integrations</td><td>Built in: reel report, click counts, UTM tags</td></tr>"
         "<tr><td>Sell products and courses</td><td>Via integrations</td><td>Built in store, courses and payments to your bank</td></tr>"
         "<tr><td>Other channels (Messenger, WhatsApp bot, TikTok, Telegram)</td><td>Yes</td><td>No, Instagram only</td></tr>"
         "<tr><td>Visual flow builder for complex bots</td><td>Yes, very flexible</td><td>No; a 4-step builder</td></tr>"
         "</tbody></table></div>"),
        ("Where ManyChat is the better choice",
         "<p>Be honest about what you need. ManyChat is the stronger tool if you run one bot across Instagram, Facebook Messenger, WhatsApp "
         "and Telegram, need complex branching flows with conditions and custom fields, or have a team that already knows it. Its template "
         "library and agency ecosystem are large.</p>"),
        ("Where {brand} is the better choice",
         "<ul><li>You're a creator, coach or small brand and mostly need comment-to-DM, a follow gate and lead capture.</li>"
         "<li>You don't want the price to rise when a reel takes off.</li>"
         "<li>You want an AI that answers DMs in Hindi, Hinglish or any language without paying extra.</li>"
         "<li>You want to see which reel made money, and sell products or courses without another tool.</li>"
         "<li>You'd rather set up an automation in 5 minutes than build a flow.</li></ul>"
         + fig("wizard-trigger", "ReplyInbox create automation screen with five triggers: comments on a post or reel, a DM, story replies, story mentions and Live comments",
               "Creating an automation in {brand} starts with one of five triggers.", (560, 548))),
        ("How to switch from ManyChat in 15 minutes",
         "<ol><li>Write down your live ManyChat automations: keyword, reel and the DM text with links.</li>"
         "<li>Sign up for {brand} free and connect the same Instagram account.</li>"
         "<li>Recreate each automation: pick the reel (or any post), add the keyword, paste the DM and links. Templates make common ones one click.</li>"
         "<li>Turn the {brand} automation on and the ManyChat one off for the same reel, so people don't get two DMs.</li>"
         "<li>If your ManyChat plan lets you export contacts, export them for your email tool.</li></ol>"
         "<p>Only one tool should answer a given keyword. Both can be connected to the same Instagram account while you move over.</p>"),
    ],
    "faq_extra": [
        ("Is {brand} cheaper than ManyChat?", "For most Instagram creators, yes: flat ₹149–₹599 a month with AI replies included from ₹199, "
         "while ManyChat's price rises with active contacts and charges for AI separately."),
        ("Can I import my ManyChat flows?", "Not automatically. Most creator flows are a keyword plus a DM, which takes a minute each to recreate."),
        ("Does {brand} work with Facebook Messenger or WhatsApp?", "No. It's built only for Instagram. It can collect WhatsApp numbers inside Instagram DMs."),
    ],
}

DEEP[("compare", "superprofile")] = {
    "answer": "SuperProfile is an Indian creator store with AutoDM included; its Creator plan is about ₹499 a month and it takes a platform "
              "fee on sales (around 5% + GST, checked November 2026). {brand} is DM automation first, from ₹149 a month, with an AI DM "
              "agent, follow to unlock and reel-level sales tracking, plus a store and courses of its own (5% + GST per sale, 2% on Pro).",
    "them": ["Store, courses, payment pages and link in bio in one place", "AutoDM on the paid plan", "Platform fee on each sale",
             "Large creator community in India"],
    "us": ["Deeper DM automation: follow gate, choice menus, follow-ups, broadcast, AI agent", "Store, courses and payments too, or keep your own payment page",
           "From ₹149 a month (Creator ₹199)", "No fee on sales made on your own payment page", "Reel report: which reel brought followers and sales"],
    "choose_them": "you want an established all-in-one creator store, and DM automation is a small part of what you need.",
    "choose_us": "Instagram DMs are how you get leads and sales, and you want the deepest DM automation for less, with or without our store.",
    "sections": [
        ("Pricing compared",
         "<div class=\"scroll\"><table><thead><tr><th></th><th>SuperProfile</th><th>{brand}</th></tr></thead><tbody>"
         "<tr><td>Plan with auto DM</td><td>About ₹499 a month (Creator)</td><td>Free (1,000 DMs), Starter ₹149, Creator ₹199</td></tr>"
         "<tr><td>Fee when you sell through it</td><td>Around 5% + GST</td><td>5% + GST; 2% + GST on Pro (₹599)</td></tr>"
         "<tr><td>Fee when you sell on your own page</td><td>Not applicable</td><td>None; sales tracking still works</td></tr>"
         "<tr><td>AI answers to DMs</td><td>AI features vary by plan</td><td>300 replies on Creator, 2,000 on Pro</td></tr>"
         "</tbody></table></div><p class=\"note\">SuperProfile figures from its public pages and payment dashboard, checked November 2026.</p>"),
        ("DM automation, side by side",
         "<div class=\"scroll\"><table><thead><tr><th>Feature</th><th>SuperProfile AutoDM</th><th>{brand}</th></tr></thead><tbody>"
         "<tr><td>Comment-to-DM with keywords</td><td>Yes</td><td>Yes, any post or next post too</td></tr>"
         "<tr><td>Buttons in the DM</td><td>Up to 3</td><td>Up to 3 links, or a 3-option choice menu</td></tr>"
         "<tr><td>Follow to unlock</td><td>Yes</td><td>Yes, with A/B tested opening message</td></tr>"
         "<tr><td>Email capture</td><td>Yes</td><td>Yes, plus WhatsApp numbers; required or skippable</td></tr>"
         "<tr><td>Follow-up DM hours later</td><td>Varies</td><td>Yes, 1–20 hours, with a button</td></tr>"
         "<tr><td>AI agent for other DMs</td><td>Agents available</td><td>AI Inbox + Lead Qualifier and Brand Collab agents</td></tr>"
         "<tr><td>Per-reel funnel</td><td>Clicks and runs</td><td>Views → comments → DM → link → follow, per reel</td></tr>"
         "</tbody></table></div>"
         + fig("wizard-review", "ReplyInbox review screen previewing an automation: public reply, opening DM with a button, follow request and email question",
               "{brand} previews every message in the sequence before you launch.", WIZ)),
        ("Selling: use our store, or keep yours",
         "<p>If you already sell on SuperProfile, you don't have to move your store. Put your SuperProfile product link in a {brand} DM button; "
         "{brand} adds click tracking and there's no {brand} fee on that sale. If you'd rather have everything in one place, {brand} has its own "
         "store (files, events, 1:1 calls), courses with certificates, and payouts straight to your bank via UPI or card.</p>"),
        ("Where SuperProfile is the better choice",
         "<p>SuperProfile has been a creator store for longer, with many payment page types, communities and a large Indian user base. If "
         "your main need is a store and DMs are secondary, it's a reasonable all-in-one choice.</p>"),
        ("How to move your AutoDMs",
         "<ol><li>List your SuperProfile automations: keyword, reel and the buttons with links.</li>"
         "<li>Connect the same Instagram account to {brand} (free).</li>"
         "<li>Recreate each one, pasting the same links (your SuperProfile product links keep working).</li>"
         "<li>Switch off the SuperProfile automation for that reel the moment the {brand} one is on, so fans don't get two DMs.</li></ol>"),
    ],
    "faq_extra": [
        ("Can I keep selling on SuperProfile and use {brand} for DMs?", "Yes. Add your SuperProfile links to the DM buttons; {brand} tracks clicks "
         "and takes no fee on those sales."),
        ("Is {brand} cheaper than SuperProfile?", "For DM automation, yes: Starter is ₹149 and Creator ₹199 a month, against about ₹499 for "
         "SuperProfile's Creator plan (checked November 2026)."),
    ],
}

DEEP[("compare", "replykaro")] = {
    "sections": [
        ("Pricing compared",
         "<div class=\"scroll\"><table><thead><tr><th></th><th>ReplyKaro</th><th>{brand}</th></tr></thead><tbody>"
         "<tr><td>Free plan</td><td>About 1,000 DMs a month</td><td>1,000 DMs a month</td></tr>"
         "<tr><td>Cheapest paid plan</td><td>About ₹99 a month</td><td>₹149 (Starter, 3,000 DMs)</td></tr>"
         "<tr><td>No monthly DM limit</td><td>Check current plans</td><td>₹199 (Creator), with 300 AI replies</td></tr>"
         "<tr><td>UPI billing</td><td>Yes</td><td>Yes, GST included</td></tr>"
         "</tbody></table></div><p class=\"note\">ReplyKaro figures from its public pages, checked November 2026.</p>"
         "<p>If price is the only thing that matters, ReplyKaro's entry plan is cheaper. The question is whether the extra ₹50–₹100 a month "
         "earns itself back.</p>"),
        ("What the extra money buys",
         "<ul><li><b>An AI DM agent.</b> It answers price, link and how-to questions in Hinglish or any language, from your FAQ, and hands "
         "refunds and collabs to you. On Creator, 300 replies a month are included.</li>"
         "<li><b>Follow-up offers.</b> A second DM a few hours later (\"Prompts try kiye? Full pack ₹149 today\") is often where the sale happens.</li>"
         "<li><b>Choice menus and up to 3 buttons</b> so one keyword can offer a freebie, a course and a call.</li>"
         "<li><b>Broadcasts</b> to everyone who messaged you in the last 24 hours.</li>"
         "<li><b>Sales per reel.</b> Click counts, UTM tags and the reel report show which reel made money.</li>"
         "<li><b>A store and courses</b> with payouts to your bank, if you don't have one already.</li></ul>"
         + fig("sales", "ReplyInbox Sales page showing revenue and orders attributed to Instagram automations",
               "The Sales page ties orders back to the automation and reel that brought them.")),
        ("Feature by feature",
         "<div class=\"scroll\"><table><thead><tr><th>Feature</th><th>ReplyKaro</th><th>{brand}</th></tr></thead><tbody>"
         "<tr><td>Comment-to-DM</td><td>Yes</td><td>Yes</td></tr><tr><td>Story replies</td><td>Yes</td><td>Yes (Starter+)</td></tr>"
         "<tr><td>Follow to unlock</td><td>Check current plans</td><td>Yes (Starter+)</td></tr>"
         "<tr><td>Email / WhatsApp capture</td><td>Check current plans</td><td>Yes (Starter+)</td></tr>"
         "<tr><td>AI answers to other DMs</td><td>Not listed*</td><td>Yes</td></tr>"
         "<tr><td>Follow-up DM, broadcast, menus</td><td>Not listed*</td><td>Yes</td></tr>"
         "<tr><td>Sales tracking per reel</td><td>Not listed*</td><td>Yes</td></tr>"
         "</tbody></table></div><p class=\"note\">* Not listed on ReplyKaro's public pages when checked in November 2026. Check its site for current features.</p>"),
        ("Who should pick which",
         "<p><b>Pick ReplyKaro</b> if you just want comments answered with a link, you don't sell anything yet and every rupee counts.</p>"
         "<p><b>Pick {brand}</b> if you sell (a course, a product, coaching) or plan to soon. The AI agent and follow-ups typically pay "
         "for the plan with one extra sale a month. You can start on the free plan and upgrade only when you need it.</p>"),
        ("Switching takes a few minutes",
         "<ol><li>Connect your Instagram account to {brand} (free).</li><li>Recreate your active keyword automations; copy the DM text and links.</li>"
         "<li>Turn off the ReplyKaro automation for the same reel so people get one DM, not two.</li></ol>"),
    ],
    "faq_extra": [
        ("Is ReplyKaro cheaper than {brand}?", "Its entry plan is (about ₹99 vs ₹149, checked November 2026). {brand} adds an AI agent, "
         "follow-ups, menus and sales tracking."),
        ("Do both work on the official Instagram API?", "{brand} does; check any tool you use never asks for your Instagram password."),
    ],
}

# ---------------------------------------------------------------- guides

DEEP[("guide", "manychat-alternatives")] = {
    "sections": [
        ("Why creators look for a ManyChat alternative",
         "<p>ManyChat is a capable chatbot builder, but three things push Instagram creators, especially in India, to look elsewhere:</p>"
         "<ul><li><b>Per-contact pricing.</b> The paid plan is priced by active contacts (from about $17 a month, checked November 2026). "
         "A viral reel can add thousands of contacts in days, and the price follows.</li>"
         "<li><b>Complexity.</b> The visual flow builder is powerful, but a simple \"comment GUIDE, get the PDF\" takes longer to build than it should.</li>"
         "<li><b>Dollar billing and paid AI.</b> Billing is in US dollars by card, and AI features cost extra.</li></ul>"),
        ("The alternatives at a glance",
         "<div class=\"scroll\"><table><thead><tr><th>Tool</th><th>Free plan</th><th>Entry paid plan</th><th>Best for</th></tr></thead><tbody>"
         "<tr><td><b>{brand}</b></td><td>1,000 DMs/month</td><td>₹149 / $5; ₹199 / $9 with AI replies</td><td>Creators who sell; follow gate, AI, sales per reel</td></tr>"
         "<tr><td>LinkDM</td><td>About 1,000 DMs</td><td>About $19/month</td><td>Simple comment-to-DM, global</td></tr>"
         "<tr><td>InstantDM</td><td>About 500 DMs</td><td>About $9.99/month</td><td>Low-cost global plan</td></tr>"
         "<tr><td>ReplyRush</td><td>Free DMs</td><td>Plans by DM volume</td><td>Simple comment replies</td></tr>"
         "<tr><td>Repli</td><td>1 automation</td><td>₹249/month</td><td>Instagram plus WhatsApp and a CRM</td></tr>"
         "<tr><td>ReplyKaro</td><td>About 1,000 DMs</td><td>About ₹99/month</td><td>Cheapest basic comment-to-DM in India</td></tr>"
         "<tr><td>SuperProfile</td><td>Limited</td><td>About ₹499/month + fee on sales</td><td>All-in-one creator store</td></tr>"
         "</tbody></table></div><p class=\"note\">Prices from each tool's public pages, checked November 2026. They change often; check before you buy.</p>"),
        ("{brand}: best for creators who sell",
         "<p>{brand} is built only for Instagram. Setting up comment-to-DM takes four steps, and the extras ManyChat users usually build by hand "
         "are switches: <a href=\"/features/follow-to-unlock\">follow to unlock</a>, email and WhatsApp capture, a follow-up offer hours later, "
         "up to 3 buttons or a choice menu. An AI agent answers other DMs in any language (300 replies included on Creator), and the reel "
         "report shows which reel brought followers and sales. Prices are flat, in ₹ with UPI or in $.</p>"
         + fig("auto-dm-list", "ReplyInbox dashboard listing comment automations with followers gained, runs, button clicks and revenue",
               "{brand}'s Auto DM page shows runs, clicks, followers and revenue for each automation.")),
        ("The others, honestly",
         "<ul><li><b>LinkDM</b>: a simple comment-to-DM tool with a free tier; a good fit if you only need keyword replies and pay in dollars.</li>"
         "<li><b>InstantDM</b>: low-cost global plans; fine for basic automation on a budget.</li>"
         "<li><b>ReplyRush</b>: free DMs and plans that scale by volume; simple to start.</li>"
         "<li><b>Repli</b>: adds WhatsApp and a CRM, useful if WhatsApp is your main sales channel.</li>"
         "<li><b>ReplyKaro</b>: the cheapest paid entry point in India for basic comment-to-DM.</li>"
         "<li><b>SuperProfile</b>: a creator store with AutoDM included; pick it if you want store-first.</li></ul>"
         "<p>Detailed comparisons: <a href=\"/vs/linkdm\">vs LinkDM</a>, <a href=\"/vs/instantdm\">vs InstantDM</a>, <a href=\"/vs/replyrush\">vs "
         "ReplyRush</a>, <a href=\"/vs/repli\">vs Repli</a>, <a href=\"/vs/replykaro\">vs ReplyKaro</a>, <a href=\"/vs/superprofile\">vs SuperProfile</a>.</p>"),
        ("How to choose in 2 minutes",
         "<ol><li><b>Do you need channels other than Instagram?</b> Yes → stay on ManyChat (or Repli for WhatsApp).</li>"
         "<li><b>Do you sell something?</b> Yes → pick a tool with follow-ups and sales tracking ({brand}).</li>"
         "<li><b>Do people DM you questions in Hindi or Hinglish?</b> Yes → you want an AI agent that's included, not an add-on.</li>"
         "<li><b>Only need basic replies at the lowest price?</b> → a free plan or ReplyKaro.</li></ol>"),
        ("Moving off ManyChat",
         "<p>Most creator setups are a handful of keyword automations. Recreate each in the new tool (a minute each), switch it on, then switch "
         "off the ManyChat version for that reel so fans don't get two DMs. Step by step: <a href=\"/vs/manychat\">{brand} vs ManyChat</a>.</p>"),
    ],
    "faq": [
        ("Is there a free ManyChat alternative?", "Yes. {brand}, LinkDM, ReplyRush, InstantDM and ReplyKaro have free plans; {brand}'s includes 1,000 DMs a month."),
        ("What is the best ManyChat alternative in India?", "For creators who sell, {brand}: flat ₹149–₹599 pricing with UPI, an AI agent that "
         "replies in Hinglish, and sales tracking per reel. For the lowest price, ReplyKaro."),
        ("Which alternative includes AI replies?", "{brand} includes AI replies from the Creator plan (300 a month, ₹199). Many others sell AI separately or don't offer it."),
        ("Can I use two tools on one Instagram account?", "Yes, but give each keyword to only one tool, or people get two DMs."),
    ],
}

DEEP[("guide", "instagram-dm-automation-pricing")] = {
    "sections": [
        ("Typical prices (checked November 2026)",
         "<div class=\"scroll\"><table><thead><tr><th>Tool</th><th>Free plan</th><th>Entry paid plan</th><th>How price grows</th></tr></thead><tbody>"
         "<tr><td>ManyChat</td><td>Small contact limit</td><td>About $17/month</td><td>By active contacts</td></tr>"
         "<tr><td>LinkDM</td><td>About 1,000 DMs</td><td>About $19/month</td><td>By plan</td></tr>"
         "<tr><td>InstantDM</td><td>About 500 DMs</td><td>About $9.99/month</td><td>By plan</td></tr>"
         "<tr><td>SuperProfile AutoDM</td><td>Limited</td><td>About ₹499/month</td><td>Plus a fee on sales</td></tr>"
         "<tr><td>Repli</td><td>1 automation</td><td>₹249/month</td><td>By plan</td></tr>"
         "<tr><td>ReplyKaro</td><td>About 1,000 DMs</td><td>About ₹99/month</td><td>By plan</td></tr>"
         "<tr><td>{brand}</td><td>1,000 DMs</td><td>₹149 / $5</td><td>Flat; no DM cap from ₹199</td></tr>"
         "</tbody></table></div><p class=\"note\">Prices change often. Check each tool's pricing page before buying.</p>"),
        ("The four pricing models",
         "<ol><li><b>Per contact</b> (ManyChat): you pay for the number of people who interacted. Cheap when small, expensive after a viral reel.</li>"
         "<li><b>Per DM volume</b>: plans by DMs a month. Predictable, but a viral reel can push you up a tier mid-month.</li>"
         "<li><b>Flat</b> ({brand} from Creator): one price whatever happens. Easiest to budget.</li>"
         "<li><b>Platform fee on sales</b> (creator stores): a low or free plan, but a percentage of everything you sell through it.</li></ol>"),
        ("What a viral month really costs",
         "<p>Say a reel gets 20,000 comments with your keyword and you sell a ₹499 product to 2% of them (400 sales, ₹1,99,600).</p>"
         "<div class=\"scroll\"><table><thead><tr><th>Model</th><th>What you pay that month</th></tr></thead><tbody>"
         "<tr><td>Per contact</td><td>Your plan can move up several contact tiers, and stays there while those contacts are active</td></tr>"
         "<tr><td>Per DM volume</td><td>A top-tier plan for that month</td></tr>"
         "<tr><td>Flat ({brand} Creator)</td><td>₹199, same as any month</td></tr>"
         "<tr><td>5% fee on sales through a store</td><td>About ₹9,980 in fees on top of the plan (2% on {brand} Pro: about ₹3,992)</td></tr>"
         "</tbody></table></div>"
         "<p>If you sell through your own payment page (Razorpay, Instamojo, Gumroad, SuperProfile), {brand} charges no fee on those sales, "
         "and click tracking still shows which reel sold.</p>"),
        ("Hidden costs to check",
         "<ul><li><b>AI credits.</b> Are AI replies included, or sold as a separate wallet that runs out?</li>"
         "<li><b>Feature gates.</b> Is the follow gate, email capture or story reply on the plan you're buying, or one tier up?</li>"
         "<li><b>Fees on sales.</b> A 5% fee costs more than any plan once you sell regularly.</li>"
         "<li><b>Currency.</b> Dollar plans add forex charges on Indian cards; ₹ plans with UPI don't.</li>"
         "<li><b>GST.</b> Check whether the price includes it ({brand}'s ₹ prices do).</li>"
         "<li><b>Extra accounts.</b> Managing two Instagram accounts can double the bill. On {brand}, Pro covers 3 and Agency 10.</li></ul>"),
        ("{brand}'s plans", PLANS_TABLE),
        ("Which plan do you actually need?",
         "<ul><li><b>Just starting, under ~10k followers:</b> the free plan (1,000 DMs a month) is usually enough.</li>"
         "<li><b>Growing followers and an email list:</b> Starter (₹149) adds follow to unlock and lead capture.</li>"
         "<li><b>Reels regularly past 1,000 comments, or you sell:</b> Creator (₹199): no DM cap, AI replies, follow-ups.</li>"
         "<li><b>Full-time with several accounts:</b> Pro (₹599) or Agency (₹2,000).</li></ul>"
         "<p>See the full breakdown on the <a href=\"/pricing\">{brand} pricing page</a>.</p>"),
    ],
    "faq": [
        ("What is the cheapest Instagram auto DM tool?", "Several tools have free plans (500–1,500 DMs a month). For paid plans, Indian tools start around "
         "₹99–₹249 a month; {brand} is ₹149, or ₹199 with no DM cap and AI replies included."),
        ("Is ManyChat expensive for Instagram?", "It can be, because its price rises with active contacts. For a creator with viral reels, a flat-price tool is usually cheaper."),
        ("Do I pay GST on top?", "{brand}'s ₹ prices include GST. Check other tools' pricing pages; dollar plans may add forex charges on Indian cards."),
        ("Is a free plan enough?", "For many accounts under 10,000 followers, yes. Upgrade when reels regularly pass 1,000 comments a month or you need a follow gate."),
    ],
}

DEEP[("guide", "how-to-auto-dm-instagram-comments")] = {
    "sections": [
        ("What you need first",
         "<ul><li>An Instagram <b>Business or Creator</b> account. It's free to switch: Settings → Account type and tools. "
         "<a href=\"/guides/switch-to-instagram-professional-account\">Step-by-step guide</a>.</li>"
         "<li>A tool on Meta's official API. Never use one that asks for your Instagram password.</li>"
         "<li>Something worth commenting for: a PDF, prompt pack, template, discount code or a link to your course.</li></ul>"),
        ("Step 1: Connect your account",
         "<p>Sign up on {brand} with Google (free, no card). Click <b>Connect Instagram</b> and approve the permissions on Instagram's own "
         "screen. It takes about a minute, and {brand} only gets the permissions Meta lists, never your password.</p>"),
        ("Step 2: Create the automation",
         "<p>Go to <b>Auto DM → Create automation → Comments on your post or reel</b>. Then choose which posts it runs on:</p>"
         "<ul><li><b>A specific reel</b>: the most common choice.</li><li><b>Any post</b>: one keyword that works on all your posts.</li>"
         "<li><b>Next post</b>: set it up before you publish, so the first comments are answered instantly. "
         "<a href=\"/guides/instagram-next-post-automation\">How next-post automation works</a>.</li></ul>"
         + fig("wizard-trigger", "Create automation dialog with options: comments on your post or reel, sends you a DM, replies to your story, mentions you in their story, comments on your Live",
               "Pick the trigger: comments, DMs, story replies, mentions or Live comments.", (560, 548))),
        ("Step 3: Set the keyword and the public reply",
         "<p>Type one keyword, for example <code>GUIDE</code>, and press Enter. Matching ignores capitals, plurals, small typos and emojis, so "
         "\"guides 🔥\" counts. Then write up to 3 public replies; one is used at random each time:</p>"
         "<ul><li>@{username} Check your DM 📩</li><li>Sent! Inbox check karo 📥</li><li>Done ✅ check your messages</li></ul>"
         "<p>Turn on <b>once per person</b> so repeat commenters get one DM. Need ideas? See <a href=\"/guides/instagram-comment-keyword-ideas\">40 "
         "comment keyword ideas</a>.</p>"
         + fig("wizard-keyword", "Keyword step with PROMPTS entered, once per person switch and rotating auto-replies to comments",
               "The keyword step with rotating public replies.", WIZ)),
        ("Step 4: Write the DM",
         "<p>Keep it short, say what they get, and put the link on a button:</p>"
         "<blockquote>Hey {username}! 👋 Here's the guide you asked for 🎁 Tap below to open it.<br>[ Open the guide ]</blockquote>"
         "<p>Optional extras before the link: an opening message with a button (lets you check follows), <b>follow to unlock</b>, and email or "
         "WhatsApp capture. After the link: a <b>follow-up offer</b> a few hours later. You can add up to 3 buttons, for example the freebie, "
         "your course and your WhatsApp group.</p>"),
        ("Step 5: Review and launch",
         "<p>The last step shows the whole conversation as the fan will see it. Check the link works, then switch it on. To test, ask a friend "
         "to comment the keyword from their account (Instagram doesn't send automated DMs to your own comments).</p>"
         + fig("wizard-review", "Review and launch screen showing the comment reply, opening DM, follow request and email question in order",
               "Review: exactly what a fan receives, step by step.", WIZ)),
        ("Already posted? DM people who commented earlier",
         "<p>If the reel is already live with comments, open the automation and use <b>send to past comments</b>. Instagram allows a private "
         "reply up to 7 days after a comment, so comments older than that can't get a DM.</p>"),
        ("Tips that raise results",
         "<ul><li>Say the keyword in the first 3 seconds, show it on screen, and repeat it in the caption and a pinned comment.</li>"
         "<li>Use one short word that matches the promise (RECIPE for a recipe).</li>"
         "<li>Use a different keyword per reel so the reel report shows which one worked.</li>"
         "<li>Add a follow gate on your best freebies to turn viewers into followers.</li>"
         "<li>Send a follow-up offer 3–6 hours later; that's where many sales happen.</li></ul>"),
        ("If a DM didn't arrive",
         "<p>The usual reasons: the comment didn't contain the keyword, it's older than 7 days, the person has restricted message requests, or "
         "Instagram's hourly limit was reached on a viral reel. {brand} retries DMs Instagram refused and shows each one in Activity. More in "
         "<a href=\"/guides/why-instagram-dm-not-sent\">why an Instagram DM wasn't sent</a>.</p>"),
    ],
    "faq": [
        ("Is it free?", "Yes, {brand}'s free plan includes 1,000 DMs a month and comment-to-DM on every reel and post."),
        ("Will my account get banned?", "Tools on the official API, with natural message variations and Instagram's limits respected, are within the rules. "
         "Read <a href=\"/guides/is-instagram-dm-automation-safe\">is Instagram DM automation safe?</a>"),
        ("Can I auto DM on old reels?", "Yes, set up an automation on any reel; new comments get DMs. Past comments can get one only within 7 days."),
        ("Do I need a business account?", "A Business or Creator account. Both are free and you can switch back any time."),
        ("How fast is the DM sent?", "Usually within seconds. You can add a 1–10 minute delay so it feels more human."),
    ],
}

DEEP[("guide", "instagram-dm-limits")] = {
    "sections": [
        ("The rules at a glance",
         "<div class=\"scroll\"><table><thead><tr><th>Rule</th><th>What it means</th><th>What to do</th></tr></thead><tbody>"
         "<tr><td>Private reply to a comment</td><td>One DM per comment, within 7 days of the comment</td><td>Set up automations before or soon after posting</td></tr>"
         "<tr><td>24-hour messaging window</td><td>After someone messages you or taps a button in your DM, you can message them for 24 hours</td><td>Send follow-ups inside that window</td></tr>"
         "<tr><td>Hourly limits</td><td>Instagram caps automated messages per account per hour</td><td>Let the tool queue and slow down on viral reels</td></tr>"
         "<tr><td>Message requests</td><td>Instagram may not open a new chat from a comment for some people</td><td>Retry later; offer the link in a pinned comment too</td></tr>"
         "</tbody></table></div>"),
        ("Rule 1: one private reply per comment, within 7 days",
         "<p>When someone comments on your post, the Instagram API lets a business send that person <b>one</b> DM in response to that comment, "
         "and only within <b>7 days</b>. That's why comment-to-DM sends one message first; everything after it depends on the person replying "
         "or tapping a button.</p>"
         "<p>It also means you can't DM people who commented weeks ago. If a reel is already live, use <b>send to past comments</b> soon after "
         "posting, while the comments are still under 7 days old.</p>"),
        ("Rule 2: the 24-hour window",
         "<p>Once a person sends you a message, or taps a button in your DM (which counts as a message), you can send them messages for "
         "<b>24 hours from their last message</b>. Each new message from them restarts the 24 hours.</p>"
         "<p>This is why the opening message with a button matters: a tap opens the window, so the follow check, the email question, the "
         "link and a follow-up offer can all be delivered. It's also why a <a href=\"/guides/instagram-follow-up-messages\">follow-up</a> must go "
         "within 24 hours (choose 1, 3, 6, 12 or 20 hours in {brand}), and why a <a href=\"/guides/instagram-broadcast-messages\">broadcast</a> "
         "only reaches people who messaged you in the last 24 hours.</p>"),
        ("Rule 3: hourly limits on automated messages",
         "<p>Instagram limits how many automated messages an account can send per hour. Meta doesn't publish one fixed number for every account, "
         "and it can change. Most accounts never notice it. A reel that gets thousands of keyword comments in an hour can reach it.</p>"
         "<p>When that happens, a good tool doesn't fail the DMs. {brand} slows down when Instagram asks, queues the rest and keeps sending as "
         "capacity frees up, so everyone gets their DM, a little later.</p>"),
        ("What this means in practice",
         "<ul><li>You can't DM all your followers at once. Only people who interacted recently can be messaged.</li>"
         "<li>Old comments (over 7 days) can't get a DM; reply to them publicly instead.</li>"
         "<li>Follow-ups have to be timed inside 24 hours.</li>"
         "<li>Viral reels may take longer to answer everyone, but shouldn't lose anyone.</li></ul>"),
        ("How {brand} handles every limit",
         "<ul><li>Times follow-ups and broadcasts inside the 24-hour window automatically.</li>"
         "<li>Sends past-comment DMs only to comments under 7 days old.</li>"
         "<li>Retries DMs that Instagram refused, once a day for 6 days, and shows them on the Auto DM page.</li>"
         "<li>Waits and queues when Instagram slows sending.</li>"
         "<li>Rotates message variations like <code>{Hi|Hey}</code> so DMs don't look identical.</li>"
         "<li>Alerts you if the account hits a problem, such as an expired connection.</li></ul>"
         + fig("auto-dm-list", "Auto DM dashboard with a notice that 2 DMs were refused by Instagram and will be retried once a day for 6 days, with a Retry now button",
               "Refused DMs are retried automatically; you can also retry them now.")),
        ("Staying safe",
         "<p>Limits exist to stop spam. Keep your automations useful: only DM people who asked (by commenting the keyword), deliver what you "
         "promised, use \"once per person\", and avoid sending the exact same long message thousands of times. More in "
         "<a href=\"/guides/is-instagram-dm-automation-safe\">is Instagram DM automation safe?</a></p>"),
    ],
    "faq": [
        ("Why didn't someone get my DM?", "Common reasons: the comment was older than 7 days, Instagram refused to open a new chat, or the hourly "
         "limit was reached. {brand} retries refused DMs for several days. See <a href=\"/guides/why-instagram-dm-not-sent\">why a DM wasn't sent</a>."),
        ("How many DMs can I send per day on Instagram?", "There's no single public number; Instagram limits automated messages per hour and "
         "per account. Tools on the official API slow down automatically when they reach it."),
        ("Can I message someone after 24 hours?", "Not with automation, unless they message you again. Each new message from them restarts the 24 hours."),
        ("Can I DM people who commented last month?", "No. Instagram allows a private reply to a comment only within 7 days."),
    ],
}

KEYWORDS = [
    ("AI and tech", [("PROMPTS", "A prompt pack (\"all 39 prompts\")"), ("TOOLS", "A list of the AI tools in the reel"),
                     ("CODE", "The code or script from the video"), ("NOTION", "A Notion template")]),
    ("Fitness", [("PLAN", "A 7-day workout plan PDF"), ("MEAL", "A meal plan or grocery list"),
                 ("ABS", "The exact routine from the reel"), ("STRETCH", "A daily mobility video")]),
    ("Food", [("RECIPE", "The full recipe card"), ("SAUCE", "The sauce or masala recipe"),
              ("MENU", "A week's menu with shopping list"), ("TIFFIN", "5 quick lunchbox ideas")]),
    ("Finance", [("BUDGET", "A budget spreadsheet"), ("SIP", "A SIP calculator sheet"),
                 ("TAX", "A tax-saving checklist"), ("SHEET", "An expense tracker")]),
    ("Coaching and courses", [("GUIDE", "A free mini-guide"), ("START", "The first lesson free"),
                              ("CALL", "A booking link for a discovery call"), ("WEBINAR", "The webinar registration link")]),
    ("Fashion and beauty", [("LINK", "Links to every product in the video"), ("LOOK", "The full outfit details"),
                            ("SKIN", "The skincare routine and products"), ("SHADE", "A shade-matching guide")]),
    ("Travel", [("TRIP", "The full itinerary"), ("MAP", "A saved Google Maps list"),
                ("BUDGET", "A trip cost breakdown"), ("STAY", "The hotel or homestay links")]),
    ("Education and exams", [("NOTES", "Chapter notes PDF"), ("PYQ", "Previous year questions"),
                             ("MOCK", "A free mock test"), ("PLANNER", "A study timetable")]),
    ("Business and marketing", [("HOOKS", "100 reel hooks"), ("SCRIPT", "The reel script template"),
                                ("AUDIT", "A free profile audit form"), ("DECK", "A pitch deck template")]),
    ("Design and editing", [("PRESET", "The Lightroom preset"), ("FONTS", "The font list"),
                            ("TEMPLATE", "The Canva template"), ("LUT", "The colour grading LUT")]),
]

DEEP[("guide", "instagram-comment-keyword-ideas")] = {
    "sections": [
        ("What makes a keyword work",
         "<ul><li><b>One short word</b>, easy to spell on a phone. No symbols, no spaces.</li>"
         "<li><b>Matches the promise.</b> Comment RECIPE for a recipe; people remember it without rewatching.</li>"
         "<li><b>Different on every reel</b>, so the reel report shows which one performed.</li>"
         "<li><b>Said in the first 3 seconds</b>, shown on screen, and repeated in the caption and a pinned comment.</li>"
         "<li><b>English or Hinglish both work</b>: RECIPE and NUSKHA are equally fine; pick what your audience types.</li></ul>"),
        ("40 keyword ideas by niche",
         "<p>Each keyword comes with what to send in the DM. Swap in your own offer.</p>"
         + "".join(f"<h3>{niche}</h3><div class=\"scroll\"><table><thead><tr><th>Keyword</th><th>What to send</th></tr></thead><tbody>"
                   + "".join(f"<tr><td><code>{k}</code></td><td>{v}</td></tr>" for k, v in items) + "</tbody></table></div>"
                   for niche, items in KEYWORDS)),
        ("Reel scripts you can copy",
         "<ul><li>\"Maine 39 prompts ki list banayi hai. Comment <b>PROMPTS</b> and I'll DM you all of them.\"</li>"
         "<li>\"Want the full 7-day plan? Comment <b>PLAN</b>.\"</li>"
         "<li>\"I made a sheet for this. Comment <b>SHEET</b> and it's yours.\"</li>"
         "<li>\"Recipe chahiye? Comment <b>RECIPE</b>, seedha DM mein bhej dunga.\"</li>"
         "<li>\"Every product from this video: comment <b>LINK</b>.\"</li></ul>"),
        ("Set it up in {brand}",
         "<ol><li>Auto DM → Create automation → Comments on your post or reel.</li>"
         "<li>Pick the reel, or <b>next post</b> if you haven't published yet.</li>"
         "<li>Type the keyword. Add a second one if your audience might type a variant (RECIPE and NUSKHA).</li>"
         "<li>Write the DM with the freebie link on a button, then launch.</li></ol>"
         + fig("wizard-keyword", "Keyword step in the ReplyInbox automation editor with the keyword PROMPTS and comment replies",
               "Keywords are matched without caring about capitals, plurals or emojis.", WIZ)
         + "<p>Full walkthrough: <a href=\"/guides/how-to-auto-dm-instagram-comments\">how to auto DM people who comment</a>.</p>"),
        ("Mistakes to avoid",
         "<ul><li><b>Long phrases</b> (\"SEND ME THE GUIDE\"): people misspell them and the match fails.</li>"
         "<li><b>Common words</b> (\"YES\", \"WOW\") on a reel that also gets normal comments: you'll DM people who didn't ask.</li>"
         "<li><b>Same keyword everywhere</b>: fine for an always-on offer (use <i>any post</i>), but you lose per-reel data.</li>"
         "<li><b>Promising more than the DM gives.</b> Deliver exactly what the reel said, instantly.</li></ul>"),
    ],
    "faq": [
        ("Does the keyword have to be exact?", "No. {brand} matches capitals, plurals, small typos and emojis around the word, so \"prompts!!\" still counts as PROMPTS."),
        ("Can one reel have several keywords?", "Yes, add several keywords to one automation, or use a choice menu in the DM instead."),
        ("Should the keyword be in English or Hindi?", "Whatever your audience types most. Many Indian creators use English keywords with Hinglish captions; you can add both."),
        ("Can I use the same keyword on every post?", "Yes: choose \"any post\" when creating the automation. Use per-reel keywords when you want to compare reels."),
    ],
}

DEEP[("guide", "how-to-collect-emails-from-instagram")] = {
    "sections": [
        ("Why collect emails (and WhatsApp numbers)",
         "<p>Followers are rented: the algorithm decides who sees your posts. An email list or WhatsApp list is yours. You can announce a "
         "launch to everyone at once, and buyers on a list typically convert far better than viewers of a single reel.</p>"),
        ("The method: comment → DM → email → freebie",
         "<ol><li>Make a freebie worth an email: a checklist, template, mini-course or prompt pack.</li>"
         "<li>Post a reel: <i>\"Comment GUIDE and I'll send it.\"</i></li>"
         "<li>Everyone who comments GUIDE gets a DM asking for their email.</li>"
         "<li>They reply with it, and the freebie arrives instantly.</li>"
         "<li>The email is saved in Leads, tagged with the reel it came from.</li></ol>"),
        ("Set it up in {brand}",
         "<ol><li>Create (or open) a comment automation and go to the DMs step.</li>"
         "<li>Switch on <b>A DM asking for their email</b> and edit the message, e.g. <i>\"One last step ✉️ Reply with your email and I'll send "
         "it right away.\"</i></li>"
         "<li>Choose <b>Required</b> (no Skip button) if you want only people who give an email, or leave it skippable if reach matters more.</li>"
         "<li>Optional: switch on <b>A DM asking for their WhatsApp number</b> too.</li>"
         "<li>Add the freebie link to the primary DM and launch.</li></ol>"
         + fig("wizard-follow-email", "Automation editor with A DM asking for their email and A DM asking for their WhatsApp number switched on, each with a Required option",
               "Email and WhatsApp capture, each optional or required.", WIZ)
         + "<p>{brand} checks the reply looks like a real email (or phone number) and asks again politely if it doesn't.</p>"),
        ("Where the emails go",
         "<ul><li><b>Leads</b>: every contact with their handle, email, phone, where they came from and what they bought.</li>"
         "<li><b>CSV export</b> for Mailchimp, ConvertKit, Brevo or any email tool.</li>"
         "<li><b>Webhook</b> to Google Sheets, Zapier, Make or Pabbly the moment a lead arrives (Settings → Integrations).</li></ul>"
         + fig("leads", "Leads page listing Instagram contacts with email, phone, source and last seen, with filters for customers, followers and subscribers",
               "Leads: everyone you collected, merged by email.")),
        ("Write the ask so people say yes",
         "<ul><li>Say why: <i>\"so I can send you the next part too\"</i>.</li>"
         "<li>Keep it one line; the freebie is the reward.</li>"
         "<li>Hinglish is fine: <i>\"Apna email bhejo, guide turant aa jayegi 📩\"</i>.</li>"
         "<li>Don't ask for both email and phone on every reel. Pick the one you'll actually use.</li></ul>"),
        ("Combine it with a follow gate",
         "<p>Turn on <a href=\"/features/follow-to-unlock\">follow to unlock</a> as well, and one comment gives you a follower, an email and a "
         "warm lead. The order is follow check, then email, then WhatsApp, then the link.</p>"),
        ("Stay on the right side of privacy rules",
         "<p>Only use emails for what you said you'd send. Add an unsubscribe link in your email tool, and don't sell or share the list. "
         "{brand} stores leads securely and you can delete them any time.</p>"),
    ],
    "faq": [
        ("Can I collect WhatsApp numbers too?", "Yes, {brand} can ask for a WhatsApp number the same way, before or after the email."),
        ("Which plan includes email capture?", "Starter (₹149 a month) and above."),
        ("Can I send the emails to Google Sheets?", "Yes, through a webhook (Settings → Integrations), with a 2-minute Google Apps Script recipe, or via Zapier or Make."),
        ("What if someone types a wrong email?", "{brand} checks the format and asks again. If it's skippable, they can still get the freebie."),
    ],
}

DEEP[("guide", "instagram-story-auto-reply")] = {
    "sections": [
        ("Two kinds of story auto-reply",
         "<ul><li><b>Story replies</b>: someone replies to your story, and gets a DM. For every reply, or only replies with a keyword like LINK.</li>"
         "<li><b>Story mentions</b>: someone tags you in their story, and gets a thank-you DM (once a day per person).</li></ul>"),
        ("Step by step: story replies",
         "<ol><li>In {brand}, go to <b>Auto DM → Create automation → Replies to your story</b>.</li>"
         "<li>Choose <b>any reply</b> or a <b>specific keyword</b>. A keyword is better if you also chat with followers normally.</li>"
         "<li>Optional: an opening message with a button, a follow gate, email or WhatsApp capture.</li>"
         "<li>Write the DM and add up to 3 link buttons.</li>"
         "<li>Save. It works on every story until you switch it off; each person gets it once per story.</li></ol>"
         + fig("wizard-story", "Story reply automation with an opening message and button, and a follow request switched on",
               "A story reply automation in {brand}.", WIZ)),
        ("Step by step: story mentions",
         "<ol><li>Create automation → <b>Mentions you in their story</b>.</li>"
         "<li>Write a thank-you: <i>\"Thank you so much for the shoutout {username}! 🙏 Here's 10% off: THANKS10\"</i>.</li>"
         "<li>Save. You can still reshare their story manually.</li></ol>"),
        ("Story ideas that get replies",
         "<div class=\"scroll\"><table><thead><tr><th>Story</th><th>Ask</th><th>DM sends</th></tr></thead><tbody>"
         "<tr><td>Flash sale</td><td>\"Reply LINK, offer 24 ghante ke liye\"</td><td>Product link with a buy button</td></tr>"
         "<tr><td>Poll: \"Want my template?\"</td><td>\"Reply YES\"</td><td>The template</td></tr>"
         "<tr><td>Webinar reminder</td><td>\"Reply JOIN\"</td><td>Joining link and time</td></tr>"
         "<tr><td>New reel teaser</td><td>\"Reply EARLY\"</td><td>Early access link</td></tr>"
         "<tr><td>Customer review</td><td>\"Reply COURSE\"</td><td>Course page and a follow-up next day</td></tr>"
         "</tbody></table></div>"),
        ("Make it convert",
         "<ul><li>Put the keyword in big text on the story; most viewers don't read small stickers.</li>"
         "<li>Add a <a href=\"/guides/instagram-follow-up-messages\">follow-up</a> 3–6 hours later for paid offers.</li>"
         "<li>Let the <a href=\"/features/ai-dm-agent\">AI agent</a> answer the questions that come after the link.</li>"
         "<li>The Activity page lists every story reply that was answered, so you can see which stories pull replies.</li></ul>"),
        ("Plans",
         "<p>Story reply and story mention automations are on <b>Starter (₹149 / $5 a month)</b> and above. On the free plan, keyword DM "
         "automations and the AI agent (25 replies to try) can still answer story replies that contain a keyword.</p>"),
    ],
    "faq": [
        ("Is story auto-reply free?", "Story automations are on Starter (₹149 a month) and above. Free accounts can use keyword DM automations for story replies with a keyword."),
        ("Will it reply to emoji reactions?", "Quick emoji reactions aren't treated as text replies; written replies are."),
        ("Can I use a different link every day?", "Yes. Edit the automation's DM whenever you post a new story, or create one per campaign with a schedule."),
        ("Does it work with the link sticker?", "Yes, use both: the sticker for tappers, the reply keyword for people who prefer to DM."),
    ],
}

DEEP[("pillar", "instagram-dm-automation")] = {
    "sections": [
        ("What it is",
         "<p>Instagram DM automation is software that sends direct messages for you when something happens on your account: someone comments "
         "a keyword, replies to your story, mentions you, comments on your Live or sends you a DM. It runs on Meta's official Instagram API "
         "and is used by creators, coaches and brands to answer thousands of people instantly, grow followers and collect leads.</p>"
         + fig("auto-dm-list", "Auto DM dashboard: DMs sent, leads collected and followers gained, with a list of automations",
               "A typical Auto DM dashboard: messages sent, leads and followers from automations.")),
        ("The triggers",
         "<div class=\"scroll\"><table><thead><tr><th>Trigger</th><th>Example</th><th>Learn more</th></tr></thead><tbody>"
         "<tr><td>Comment with a keyword</td><td>\"Comment GUIDE\" → the guide by DM</td><td><a href=\"/features/comment-to-dm\">Comment-to-DM</a></td></tr>"
         "<tr><td>Story reply</td><td>\"Reply LINK\" → the offer link</td><td><a href=\"/guides/instagram-story-auto-reply\">Story auto-reply</a></td></tr>"
         "<tr><td>Story mention</td><td>Thank-you plus a discount code</td><td><a href=\"/features/story-replies\">Story automations</a></td></tr>"
         "<tr><td>Keyword DM</td><td>Someone DMs \"PRICE\" → price and link</td><td><a href=\"/guides/instagram-welcome-message\">Welcome message</a></td></tr>"
         "<tr><td>Live comment</td><td>\"Comment JOIN\" during a Live → the link</td><td><a href=\"/guides/instagram-live-comment-automation\">Live comments</a></td></tr>"
         "<tr><td>Any other DM</td><td>The AI answers from your FAQ</td><td><a href=\"/features/ai-dm-agent\">AI DM agent</a></td></tr>"
         "</tbody></table></div>"),
        ("How a comment-to-DM conversation flows",
         "<ol><li>A fan comments your keyword. The automation replies publicly (\"Check your DM 📩\").</li>"
         "<li>They get an opening DM with a button. The tap opens a 24-hour messaging window.</li>"
         "<li>Optional: a follow check, then an email or WhatsApp question.</li>"
         "<li>They get the link (up to 3 buttons, or a choice menu).</li>"
         "<li>Hours later, a follow-up with your paid offer.</li></ol>"
         + fig("wizard-review", "Preview of an automated Instagram conversation: comment reply, opening DM with button, follow request, then the link",
               "The full conversation, previewed before launch.", WIZ)),
        ("Instagram's rules",
         "<p>Automation has to follow three rules: one private reply per comment within 7 days, messages only within 24 hours of the person's "
         "last message, and hourly limits on automated messages. Tools on the official API handle these for you. "
         "<a href=\"/guides/instagram-dm-limits\">Instagram DM limits explained</a> covers each rule.</p>"),
        ("Is it safe?",
         "<p>Yes, when the tool uses Meta's official API, never asks for your password, and you only message people who asked (by commenting "
         "the keyword). Use message variations and \"once per person\". Avoid tools that log in with your password or send cold DMs; those "
         "break Instagram's terms. Read <a href=\"/guides/is-instagram-dm-automation-safe\">is Instagram DM automation safe?</a></p>"),
        ("Get started in 10 minutes",
         "<ol><li><a href=\"/guides/switch-to-instagram-professional-account\">Switch to a professional account</a> (free).</li>"
         "<li>Sign up for {brand} free and connect Instagram.</li>"
         "<li>Pick a freebie and a <a href=\"/guides/instagram-comment-keyword-ideas\">keyword</a>.</li>"
         "<li>Create the automation: <a href=\"/guides/how-to-auto-dm-instagram-comments\">how to auto DM commenters</a>.</li>"
         "<li>Post the reel and say the keyword in the first 3 seconds.</li></ol>"),
        ("What it costs",
         "<p>Most tools have a free plan (500–1,500 DMs a month) and paid plans from about ₹99 to $40 a month. {brand} is free for 1,000 DMs a "
         "month; Starter is ₹149 and Creator ₹199 with no DM cap and AI replies. Compare in <a href=\"/guides/instagram-dm-automation-pricing\">"
         "Instagram DM automation pricing</a> or see <a href=\"/pricing\">{brand} pricing</a>.</p>"),
        ("Troubleshooting",
         "<ul><li>No DM? Check the keyword, the comment's age (under 7 days) and Activity. <a href=\"/guides/why-instagram-dm-not-sent\">Why a DM wasn't sent</a>.</li>"
         "<li>Test from a second account: automated DMs aren't sent to your own comments.</li>"
         "<li>Two DMs per comment? Two tools are answering the same keyword; switch one off.</li></ul>"),
    ],
}

# ---------------------------------------------------------------- extra sections (appended so the pages reach full depth)

DEEP[("guide", "how-to-collect-emails-from-instagram")]["sections"].insert(5, (
    "What to do with the list",
    "<ol><li><b>Send a welcome email the same day</b> with the freebie again and one line about who you are. People forget where they signed up.</li>"
    "<li><b>Tag by reel.</b> {brand} saves the keyword each lead came from, so someone who commented BUDGET gets your finance launch, not your fitness one.</li>"
    "<li><b>Give before you sell.</b> Two or three useful emails before a launch email convert better than an immediate pitch.</li>"
    "<li><b>Launch to the list first.</b> An early-bird price for the list rewards people for joining and gives you first-day sales.</li>"
    "<li><b>Use WhatsApp for time-sensitive things</b> (a webinar starting, a 24-hour offer) and email for everything else.</li></ol>"
    "<p>Pair the list with a <a href=\"/guides/instagram-lead-magnet-ideas\">lead magnet</a> people actually want, and see "
    "<a href=\"/guides/collect-whatsapp-numbers-from-instagram\">how to collect WhatsApp numbers</a> for the WhatsApp side.</p>"))

DEEP[("guide", "instagram-story-auto-reply")]["sections"].insert(4, (
    "Story reply keyword vs the link sticker",
    "<div class=\"scroll\"><table><thead><tr><th></th><th>Link sticker</th><th>Reply keyword + auto DM</th></tr></thead><tbody>"
    "<tr><td>Effort for the viewer</td><td>One tap</td><td>Type one word</td></tr>"
    "<tr><td>Opens a conversation</td><td>No</td><td>Yes, 24 hours to follow up</td></tr>"
    "<tr><td>Can check they follow you</td><td>No</td><td>Yes (follow to unlock)</td></tr>"
    "<tr><td>Collects email or WhatsApp</td><td>No</td><td>Yes</td></tr>"
    "<tr><td>Several links</td><td>One per sticker</td><td>Up to 3 buttons</td></tr>"
    "</tbody></table></div><p>Use both: the sticker for people who just want the link, the keyword for people you want to keep talking to.</p>"))
DEEP[("guide", "instagram-story-auto-reply")]["sections"].insert(5, (
    "If replies aren't being answered",
    "<ul><li><b>Keyword mode, but the reply didn't contain the keyword</b>: switch to \"any reply\" or add the variants people type.</li>"
    "<li><b>The person already got the DM for this story</b>: each person is answered once per story.</li>"
    "<li><b>The automation is off or scheduled</b>: check its status and start and end times on the Auto DM page.</li>"
    "<li><b>Free plan</b>: story automations need Starter; on Free, use a keyword DM automation instead.</li>"
    "<li><b>Messages to your account are restricted</b> in Instagram's settings: allow message requests from everyone.</li></ul>"))

DEEP[("guide", "manychat-alternatives")]["sections"].insert(4, (
    "What to look for in any alternative",
    "<ul><li><b>Official API.</b> It should connect through Instagram's own login and never ask for your password.</li>"
    "<li><b>Flat or predictable pricing</b> that doesn't jump when a reel goes viral.</li>"
    "<li><b>Follow gate and lead capture on the plan you'll buy</b>, not one tier up.</li>"
    "<li><b>Retries and queueing</b> when Instagram refuses or slows DMs, so a viral reel doesn't lose people.</li>"
    "<li><b>Reporting by reel</b>, so you know which content brings followers and sales.</li>"
    "<li><b>Billing you can use</b>: UPI and ₹ prices with GST in India, or dollars elsewhere.</li></ul>"))

DEEP[("compare", "replykaro")]["sections"].insert(4, (
    "A simple way to decide",
    "<p>Start both free plans if you like; each has about 1,000 DMs a month. Run the same keyword reel through one tool at a time and "
    "compare: how many people got the DM, how many tapped the link, how many followed. If you only ever need the DM, the cheapest tool "
    "is fine. If you start selling, the follow-up, AI replies and per-reel sales numbers are what decide which tool pays for itself.</p>"))

DEEP[("guide", "instagram-dm-automation-pricing")]["sections"].insert(3, (
    "See what each reel earns",
    "<p>Whatever tool you pick, the price only makes sense against what it brings in. {brand} shows sales per automation and per reel, "
    "whether the sale happened in its store or on your own payment page (through tracked links and UTM tags).</p>"
    + fig("sales", "ReplyInbox Sales page with revenue and orders tied to automations and reels", "Sales tied back to the reel and automation that brought them.")))
DEEP[("guide", "instagram-story-auto-reply")]["faq"] += [
    ("Can I add a follow gate to story replies?", "Yes. The same follow to unlock, email and WhatsApp steps from comment automations work on story replies, "
     "so a story can grow followers and your list at the same time."),
    ("Can the AI answer story replies too?", "Yes. Story replies that don't match an automation go to the AI agent, which answers from your FAQ in the "
     "person's language and hands anything unclear to you."),
]
