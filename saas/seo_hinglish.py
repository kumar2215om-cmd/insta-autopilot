"""SEO batch D: Instagram auto DM guides in Hinglish (Hindi in Roman script), for the way most Indian creators search.

HINGLISH_GUIDES are added to seo_content.GUIDES and grouped under the HINGLISH_PILLAR topic page. Every page has
"lang": "hi-Latn", so the page's <html lang> tells search engines it is Hindi written in Latin script. Facts match the
English pages (plans, Instagram's rules). "{brand}" is replaced with the brand name when rendering.
"""
from seo_deep import WIZ, fig

LANG = "hi-Latn"

PLANS_HI = ("<div class=\"scroll\"><table><thead><tr><th>Plan</th><th>Price / mahina</th><th>DMs / mahina</th><th>Kya milta hai</th></tr></thead><tbody>"
            "<tr><td>Free</td><td>₹0</td><td>1,000</td><td>Comment-to-DM, keyword DMs, Live comments, link in bio, 25 AI replies try karne ke liye</td></tr>"
            "<tr><td>Starter</td><td>₹149</td><td>3,000</td><td>Follow to unlock, email aur WhatsApp number lena, story replies</td></tr>"
            "<tr><td>Creator</td><td>₹199</td><td>Koi monthly limit nahi*</td><td>300 AI replies, Lead Qualifier agent, course extras</td></tr>"
            "<tr><td>Pro</td><td>₹599</td><td>Koi monthly limit nahi*</td><td>3 accounts, 2,000 AI replies, Claude (MCP), sale par sirf 2%</td></tr>"
            "<tr><td>Agency</td><td>₹2,000</td><td>Koi monthly limit nahi*</td><td>10 accounts, 10,000 AI replies</td></tr>"
            "</tbody></table></div><p class=\"note\">* Fair use. Instagram ki apni limits phir bhi lagti hain. GST price mein included hai. "
            "Poori details: <a href=\"/pricing\">pricing page</a>.</p>")

H = "/guides/"

HINGLISH_GUIDES = {
    "instagram-auto-dm-kya-hai": {
        "lang": LANG,
        "title": "Instagram auto DM kya hai? Simple bhasha mein samjho",
        "description": "Instagram auto DM kya hota hai, kaise kaam karta hai, kya ye safe hai aur creators isse followers, leads aur sales kaise banate hain.",
        "answer": "Instagram auto DM ek tool hai jo aapki taraf se apne aap DM bhejta hai, jab koi aapki reel par keyword comment kare (jaise "
                  "GUIDE), story ka reply kare ya aapko DM kare. Ye Meta ki official Instagram API par chalta hai, aapka password nahi maangta, "
                  "aur {brand} par 1,000 DMs har mahine free hain.",
        "sections": [
            ("Ek example se samjho",
             "<p>Aapne reel daali: <i>\"Maine 39 AI prompts ki list banayi hai, comment karo PROMPTS aur main DM kar dunga.\"</i> Rahul ne "
             "comment kiya <code>prompts 🔥</code>. Kuch hi seconds mein:</p>"
             "<ol><li>Uske comment par public reply chala gaya: <i>\"@rahul DM check karo 📩\"</i>.</li>"
             "<li>Use DM mein prompts ka link mil gaya, ek button ke saath.</li>"
             "<li>Uska naam (aur chaho toh email ya WhatsApp number) aapki Leads list mein save ho gaya.</li></ol>"
             "<p>Aapko phone bhi nahi uthana pada. Reel viral hui aur 2,000 log comment karein, tab bhi sabko turant DM milta hai.</p>"),
            ("Auto DM kis kis cheez par chalta hai",
             "<div class=\"scroll\"><table><thead><tr><th>Jab koi…</th><th>Example</th></tr></thead><tbody>"
             "<tr><td>Reel ya post par keyword comment kare</td><td>\"Comment GUIDE\" → guide DM mein</td></tr>"
             "<tr><td>Aapko keyword DM kare</td><td>\"PRICE\" likhe → price aur link</td></tr>"
             "<tr><td>Story ka reply kare</td><td>\"Reply LINK\" → offer ka link</td></tr>"
             "<tr><td>Apni story mein aapko mention kare</td><td>Thank you message ya discount code</td></tr>"
             "<tr><td>Live par keyword comment kare</td><td>\"Comment JOIN\" → link DM mein</td></tr>"
             "<tr><td>Koi aur sawaal DM kare</td><td>AI aapke FAQ se jawab deta hai</td></tr>"
             "</tbody></table></div>"),
            ("Creators ise kyun use karte hain",
             "<ul><li><b>Engagement badhta hai.</b> Log \"link in bio\" se zyada aasani se comment karte hain, aur zyada comments se reel aur logon tak jaati hai.</li>"
             "<li><b>Followers badhte hain.</b> <a href=\"/features/follow-to-unlock\">Follow to unlock</a> se link sirf followers ko jaata hai.</li>"
             "<li><b>Leads milti hain.</b> DM mein hi email ya WhatsApp number le sakte ho.</li>"
             "<li><b>Sales hoti hain.</b> Kuch ghante baad ek follow-up DM mein apna paid product offer kar sakte ho.</li>"
             "<li><b>Time bachta hai.</b> Har DM ka jawab haath se dene ki zaroorat nahi.</li></ul>"),
            ("Ye kaam kaise karta hai (thoda technical)",
             "<p>Aap apna Instagram <b>Creator ya Business account</b> Meta ke official login se tool ke saath connect karte ho. Instagram "
             "tool ko batata hai jab koi comment ya DM aata hai, aur tool aapke set kiye rules ke hisaab se jawab bhejta hai. Instagram ke "
             "3 rules hain: ek comment par ek private DM (7 din ke andar), insaan ke last message ke 24 ghante tak messages, aur har ghante "
             "ki limit. Achha tool in sab ka khayal apne aap rakhta hai. Details: <a href=\"/guides/instagram-dm-limits\">Instagram DM limits</a>.</p>"
             + fig("auto-dm-list", "ReplyInbox ka Auto DM dashboard: DMs sent, leads aur followers gained, automations ki list ke saath",
                   "{brand} ka Auto DM page: har automation ke runs, clicks aur followers.")),
            ("Kya ye safe hai?",
             "<p>Haan, agar tool Meta ki official API par chalta hai, password nahi maangta, aur aap sirf unhe DM karte ho jinhone keyword "
             "comment karke maanga hai. Jo tools password maangte hain ya anjaan logon ko DM bhejte hain, unse bacho. Poori baat: "
             "<a href=\"" + H + "kya-instagram-auto-dm-safe-hai\">kya Instagram auto DM safe hai?</a></p>"),
            ("Shuru kaise karein",
             "<ol><li>Instagram ko <a href=\"/guides/switch-to-instagram-professional-account\">Creator account</a> par switch karo (free hai).</li>"
             "<li>{brand} par Google se sign up karo, card ki zaroorat nahi.</li>"
             "<li>Instagram connect karo aur pehla automation banao.</li></ol>"
             "<p>Step by step: <a href=\"" + H + "instagram-auto-dm-kaise-lagaye\">Instagram auto DM kaise lagaye</a>.</p>"),
            ("Kitna kharcha hai", PLANS_HI),
        ],
        "faq": [
            ("Instagram auto DM free hai kya?", "Haan, {brand} ke free plan mein har mahine 1,000 DMs milte hain, bina card ke."),
            ("Kya iske liye business account chahiye?", "Creator ya Business account chahiye. Dono free hain aur kabhi bhi wapas switch kar sakte ho."),
            ("Kya account ban ho sakta hai?", "Official API wale tools, sirf maangne walon ko DM, aur messages mein variety rakhne se account safe rehta hai."),
            ("Auto DM aur AI reply mein kya fark hai?", "Auto DM keyword par fixed message bhejta hai. AI reply baaki sawaalon ka jawab aapke FAQ se, user ki bhasha mein deta hai."),
        ],
    },

    "instagram-auto-dm-kaise-lagaye": {
        "lang": LANG,
        "title": "Instagram auto DM kaise lagaye: 5 steps mein (2026)",
        "description": "Instagram par auto DM kaise set karein: account connect karna, keyword, public reply, DM aur button, step by step screenshots ke saath.",
        "answer": "Instagram auto DM lagane ke liye: account ko Creator ya Business par switch karo, {brand} jaise official API wale tool se "
                  "connect karo, Auto DM → Create automation mein reel aur keyword (jaise GUIDE) chuno, DM mein link wala button lagao aur on "
                  "kar do. Iske baad har keyword comment par seconds mein DM jaata hai.",
        "sections": [
            ("Pehle ye ready rakho",
             "<ul><li><b>Creator ya Business account</b>: Settings → Account type and tools → Switch to professional account.</li>"
             "<li>Ek <b>freebie</b> jiske liye log comment karein: PDF, prompt pack, template, recipe ya discount code.</li>"
             "<li>Uska <b>link</b> (Google Drive, apna page ya {brand} ke Files mein upload karke).</li></ul>"),
            ("Step 1: Sign up aur Instagram connect",
             "<p>{brand} par Google se sign up karo (free). <b>Connect Instagram</b> dabao, Instagram ki apni screen par permissions allow "
             "karo. Ek minute lagta hai. Password kabhi nahi maanga jaata.</p>"),
            ("Step 2: Automation banao",
             "<p><b>Auto DM → Create automation → Comments on your post or reel</b>. Phir chuno:</p>"
             "<ul><li><b>Specific reel</b>: sabse common.</li><li><b>Any post</b>: ek keyword saare posts par.</li>"
             "<li><b>Next post</b>: reel daalne se pehle hi ready, taaki pehle comments ko bhi turant DM mile.</li></ul>"
             + fig("wizard-trigger", "Create automation screen: comments, DM, story reply, story mention aur Live comments ke options",
                   "Trigger chuno: comment, DM, story, mention ya Live.", (560, 548))),
            ("Step 3: Keyword aur public reply",
             "<p>Ek chhota keyword likho, jaise <code>GUIDE</code>, aur Enter dabao. Capital, small, plural, choti spelling galti aur emoji "
             "sab match ho jaate hain, toh \"guides 🔥\" bhi chalega. Phir 3 public replies likho, har baar ek random jaayega:</p>"
             "<ul><li>@{username} DM check karo 📩</li><li>Bhej diya! Inbox dekho 📥</li><li>Done ✅ DM mein hai</li></ul>"
             "<p><b>Once per person</b> on rakho, taaki 5 baar comment karne wale ko ek hi DM jaaye.</p>"
             + fig("wizard-keyword", "Keyword step: PROMPTS keyword, once per person switch aur comment replies",
                   "Keyword, once per person aur rotating public replies.", WIZ)),
            ("Step 4: DM likho",
             "<p>Chhota rakho, batao kya mil raha hai, aur link button par lagao:</p>"
             "<blockquote>Hey {username}! 👋 Ye rahi tumhari free guide 🎁 Neeche button dabao.<br>[ Guide kholo ]</blockquote>"
             "<p>Chaho toh aur bhi jod sakte ho: follow to unlock, email ya WhatsApp number maangna, 3 tak buttons, aur kuch ghante baad "
             "follow-up offer. Ready messages: <a href=\"/guides/instagram-dm-templates\">DM templates</a>.</p>"),
            ("Step 5: Review karo aur on karo",
             "<p>Last step mein poori conversation dikhti hai, bilkul waise jaise fan ko milegi. Link check karo aur on kar do. Test karne ke "
             "liye kisi dost se doosre account se keyword comment karwao, kyunki apne hi comment par auto DM nahi jaata.</p>"
             + fig("wizard-review", "Review screen: public reply, opening DM button ke saath, follow request aur email sawaal",
                   "Review: fan ko kya kya milega, step by step.", WIZ)),
            ("Purani reel par bhi chala sakte ho",
             "<p>Reel pehle se live hai? Automation banao, naye comments ko DM jaayega. Purane comments ke liye <b>Send to past comments</b> "
             "use karo, lekin Instagram sirf 7 din purane comments tak DM allow karta hai.</p>"),
            ("Results badhane ke tips",
             "<ul><li>Keyword reel ke pehle 3 second mein bolo, screen par dikhao, caption aur pinned comment mein bhi likho.</li>"
             "<li>Har reel ka alag keyword rakho, taaki reel report mein pata chale kaunsi reel chali.</li>"
             "<li>Best freebie par follow gate lagao, followers badhenge.</li>"
             "<li>3–6 ghante baad follow-up bhejo, sale aksar wahin hoti hai.</li></ul>"),
        ],
        "faq": [
            ("Kitna time lagta hai?", "Pehli baar 5–10 minute. Uske baad naya automation 2 minute mein ban jaata hai."),
            ("DM nahi gaya toh kya karein?", "Check karo keyword sahi hai, comment 7 din se purana nahi hai, aur Activity page dekho. "
             "<a href=\"/guides/why-instagram-dm-not-sent\">DM kyun nahi gaya</a> guide mein saare reasons hain."),
            ("Kya mobile se set kar sakte hain?", "Haan, {brand} phone ke browser mein chalta hai aur phone app ki tarah install bhi ho sakta hai."),
            ("Kya ye free hai?", "Haan, free plan mein har mahine 1,000 DMs hain."),
        ],
    },

    "comment-par-automatic-dm-kaise-bheje": {
        "lang": LANG,
        "title": "Comment par automatic DM kaise bheje: Instagram guide",
        "description": "Instagram reel ya post par comment karne walon ko automatic DM kaise bhejein: keyword, any post, next post, buttons aur menu.",
        "answer": "Instagram par comment karne walon ko automatic DM bhejne ke liye comment-to-DM automation banao: reel chuno, keyword "
                  "set karo (jaise LINK), DM mein link ka button lagao. Har matching comment par public reply aur DM seconds mein jaata hai, "
                  "24 ghante, bina aapke kuch kiye.",
        "sections": [
            ("Teen tarah ke comment automation",
             "<div class=\"scroll\"><table><thead><tr><th>Option</th><th>Kab use karein</th></tr></thead><tbody>"
             "<tr><td>Ek specific reel</td><td>Har reel ka apna freebie aur keyword ho</td></tr>"
             "<tr><td>Any post (saare posts)</td><td>Ek hi offer har jagah, jaise \"comment COURSE\"</td></tr>"
             "<tr><td>Next post</td><td>Reel daalne se pehle set karna ho, taaki pehle comment ko bhi DM mile</td></tr>"
             "</tbody></table></div>"
             "<p>Keyword ki jagah <b>any comment</b> bhi chun sakte ho, lekin tab har comment par DM jaayega, chahe log sirf \"nice\" likhein. "
             "Keyword zyada achha rehta hai.</p>"),
            ("Keyword kaisa ho",
             "<ul><li>Ek chhota word, spelling aasaan: GUIDE, LINK, PDF, RECIPE.</li>"
             "<li>Promise se match kare: recipe ke liye RECIPE.</li>"
             "<li>English ya Hinglish dono chalega. Chaho toh dono add kar do: RECIPE aur NUSKHA.</li>"
             "<li>Jo words log waise bhi likhte hain (YES, WOW) unse bacho, warna bina maange DM chala jaayega.</li></ul>"
             "<p>40 ideas yahan hain: <a href=\"/guides/instagram-comment-keyword-ideas\">comment keyword ideas</a>.</p>"),
            ("DM mein kya kya bhej sakte ho",
             "<ul><li><b>3 tak link buttons</b>: freebie, course aur WhatsApp group, sab alag button par.</li>"
             "<li><b>Choice menu</b>: 3 options, har option ka alag message (\"Free guide / Course details / Call book karo\").</li>"
             "<li><b>Opening message</b> ek button ke saath, jisse chat khulti hai aur follow check ho sakta hai.</li>"
             "<li><b>Email ya WhatsApp number</b> link se pehle (Starter plan se).</li>"
             "<li><b>Follow-up</b> 1 se 20 ghante baad, apne paid product ke saath.</li></ul>"
             + fig("wizard-primary-dm", "DM step: follow request, email aur WhatsApp number maangne ke switches",
                   "Link se pehle follow, email aur WhatsApp ke steps on kar sakte ho.", WIZ)),
            ("Spam jaisa na lage, iske liye",
             "<ul><li><code>{Hi|Hey|Hello}</code> likho, har insaan ko alag word milega. Sabko bilkul same message nahi jaata.</li>"
             "<li>1 se 10 minute ka <b>delay</b> rakh sakte ho, DM insaan jaisa lagta hai. Public reply phir bhi turant jaata hai.</li>"
             "<li><b>Once per person</b> on rakho.</li>"
             "<li>DM chhota rakho, link pehle do, baatein baad mein.</li></ul>"),
            ("Instagram ke rules",
             "<p>Ek comment par ek private DM, aur woh bhi comment ke 7 din ke andar. Jab user button dabata hai ya reply karta hai, tab 24 "
             "ghante tak aur messages bhej sakte ho. Viral reel par Instagram har ghante ki limit lagata hai; {brand} tab ruk kar baad mein "
             "bhejta hai, aur jo DM Instagram ne refuse kiye unhe 6 din tak roz retry karta hai.</p>"),
            ("Kaunsi reel kitna laayi, ye dekho",
             "<p>Reel report har reel ka funnel dikhata hai: views, comments, kitno ne keyword likha, DM mila, link khula aur follow kiya. "
             "Isse pata chalta hai kaunsa hook dobara use karna hai.</p>"
             + fig("reel-report", "Reel report: har reel ke views, comments, keyword, DM, link aur follows",
                   "Reel report: har reel ka poora hisaab.")),
        ],
        "faq": [
            ("Kya Instagram comment par auto DM allow karta hai?", "Haan, official API se. Ek comment par ek DM, comment ke 7 din ke andar."),
            ("Kya ek reel par do keyword chal sakte hain?", "Haan, ek automation mein kai keywords add kar sakte ho."),
            ("Kya photo post aur carousel par bhi chalega?", "Haan, reels, photo aur carousel posts sab par, aur Live comments par bhi."),
            ("Comment ka public reply band kar sakte hain?", "Haan, public reply off karke sirf DM bhej sakte ho."),
        ],
    },

    "instagram-par-followers-kaise-badhaye-dm-se": {
        "lang": LANG,
        "title": "Instagram par followers kaise badhaye: auto DM wala tarika",
        "description": "Reels ke views ko followers mein kaise badlein: comment keyword aur follow to unlock, real steps aur tips ke saath.",
        "answer": "Reels se followers badhane ka sabse seedha tarika hai comment keyword + follow to unlock: reel mein free cheez offer karo, "
                  "log keyword comment karein, aur DM mein link tabhi jaaye jab woh aapko follow karein. Jo log pehle se interested hain, "
                  "woh follow karne mein ek second lagate hain.",
        "sections": [
            ("Views hain, followers kyun nahi?",
             "<p>Reel lakhon logon tak pahunch jaati hai, lekin zyada log dekh kar aage scroll kar dete hain. Unke paas follow karne ki koi "
             "wajah nahi hoti. Follow to unlock unhe wajah deta hai: jo cheez unhe chahiye, woh follow ke baad milti hai.</p>"),
            ("Fan ko kya dikhta hai",
             "<ol><li>Woh keyword comment karta hai aur ek DM aata hai button ke saath: \"Send me the access\".</li>"
             "<li>Button dabane par {brand} Instagram se check karta hai ki woh follow karta hai ya nahi.</li>"
             "<li><b>Follow karta hai</b>: link turant mil jaata hai.</li>"
             "<li><b>Nahi karta</b>: ek friendly message aata hai do buttons ke saath, <b>Visit Profile</b> aur <b>I'm following ✅</b>. "
             "Follow karke button dabata hai, aur link aa jaata hai.</li></ol>"
             + fig("wizard-review", "Review screen: opening DM button ke saath, phir Visit Profile aur I'm following buttons",
                   "Follow to unlock ka poora flow.", WIZ)),
            ("Pehla DM button ke saath kyun?",
             "<p>Instagram apps ko follow check tabhi karne deta hai jab user DM mein kuch kare, jaise button dabaye. Isliye flow ek chhote "
             "opening message se shuru hota hai. Fayda ye bhi hai ki button dabate hi 24 ghante ke liye chat khul jaati hai, toh link, email "
             "ka sawaal aur follow-up sab bhej sakte ho.</p>"),
            ("Set kaise karein",
             "<ol><li>Automation kholo ya naya banao, DMs step par jao.</li>"
             "<li><b>A DM asking to follow you</b> on karo.</li>"
             "<li>Message apne style mein likho: <i>\"Bas ek step 👀 Profile pe jaake Follow karo, phir neeche button dabao.\"</i></li>"
             "<li>Save karo. Ab link sirf followers ko jaayega.</li></ol>"),
            ("Aisi reels jo followers laati hain",
             "<ul><li><b>Specific freebie</b>: \"39 prompts\", \"7 din ka diet plan\", \"poori recipe\". \"Meri guide\" nahi.</li>"
             "<li><b>Keyword pehle 3 second mein</b>: \"Comment PLAN karo, poora plan DM karta hoon.\"</li>"
             "<li><b>Reel mein bolo ki follow karna hai</b>: \"Follow karke comment karo\". Log expect karte hain toh drop nahi karte.</li>"
             "<li><b>Series banao</b>: \"Part 2 ke liye follow karo\" aur DM mein Part 1 ka link.</li></ul>"),
            ("Result kaise check karein",
             "<p>Reel report mein <b>Followed to unlock</b> number dikhta hai, aur <b>follows per 1K views</b> se reels compare kar sakte ho. "
             "Jis reel ka number zyada ho, uska hook aur format dobara use karo. Auto DM page par har automation ke <b>followers gained</b> "
             "bhi dikhte hain.</p>"
             + fig("reel-report", "Reel report: follows per 1K views aur Followed to unlock numbers",
                   "Kaunsi reel se kitne followers aaye.")),
            ("Plan", "<p>Follow to unlock <b>Starter (₹149 / mahina)</b> aur usse upar ke plans mein hai.</p>" + PLANS_HI),
        ],
        "faq": [
            ("Kya follow to unlock Instagram ke rules ke against hai?", "Nahi, official API par normal DM aur buttons se chalta hai. Bas jo promise "
             "karo, woh do."),
            ("Link milne ke baad log unfollow kar denge?", "Kuch log karte hain, lekin zyada log aapke content ki wajah se rukte hain. Reel report "
             "mein har reel se jeete follows dikhte hain."),
            ("Kya story reply par bhi follow gate laga sakte hain?", "Haan, Starter plan se story reply automation mein bhi."),
            ("Kitne followers expect karein?", "Niche aur offer par depend karta hai. Clear freebie aur keyword wali reels mein follow gate ka asar sabse zyada dikhta hai."),
        ],
    },
}

HINGLISH_GUIDES.update({
    "instagram-se-email-whatsapp-number-kaise-le": {
        "lang": LANG,
        "title": "Instagram se email aur WhatsApp number kaise le",
        "description": "Instagram followers ke email aur WhatsApp number DM mein kaise collect karein, kahan save hote hain aur unka use kaise karein.",
        "answer": "Instagram se email ya WhatsApp number lene ka sabse aasaan tarika: reel par freebie ke liye keyword comment karwao, DM mein "
                  "pehle email ya number maango, aur jawab aate hi freebie bhej do. {brand} mein ye ek switch hai; leads apne aap save hoti "
                  "hain aur Google Sheets ya CSV mein ja sakti hain.",
        "sections": [
            ("Kyun zaroori hai",
             "<p>Followers algorithm ke haath mein hain: aaj reel chali, kal nahi. Email aur WhatsApp list aapki apni hai. Launch ke din sabko "
             "ek saath bata sakte ho, webinar ka link bhej sakte ho, aur list wale log ek reel dekhne walon se kahin zyada khareedte hain.</p>"),
            ("Flow: comment → DM → email → freebie",
             "<ol><li>Ek aisa freebie banao jiske liye log email dein: checklist, template, mini-course, prompt pack.</li>"
             "<li>Reel: <i>\"Comment GUIDE karo, main bhej dunga.\"</i></li>"
             "<li>Comment karne wale ko DM: <i>\"Apna email bhejo, guide turant aa jayegi 📩\"</i></li>"
             "<li>Email aate hi freebie ka link chala jaata hai.</li>"
             "<li>Email Leads mein save, reel ke keyword ke tag ke saath.</li></ol>"),
            ("{brand} mein set kaise karein",
             "<ol><li>Comment automation kholo, DMs step par jao.</li>"
             "<li><b>A DM asking for their email</b> on karo, message apne style mein likho.</li>"
             "<li><b>Required</b> chuno agar sirf email dene walon ko freebie dena hai, ya Skip button rehne do agar reach zyada zaroori hai.</li>"
             "<li>Chaho toh <b>A DM asking for their WhatsApp number</b> bhi on karo.</li>"
             "<li>Primary DM mein freebie ka link lagao aur launch karo.</li></ol>"
             + fig("wizard-follow-email", "DM step: email aur WhatsApp number maangne wale switches, Required option ke saath",
                   "Email aur WhatsApp number dono maang sakte ho, required ya skip ke saath.", WIZ)
             + "<p>Agar koi galat email likhe (jaise \"rahul@gmail\"), {brand} politely dobara poochta hai: <i>\"Hmm, ye email jaisa nahi lag "
             "raha 🤔\"</i>. WhatsApp number ke saath bhi aisa hi hota hai.</p>"),
            ("Leads kahan jaati hain",
             "<ul><li><b>Leads page</b>: har insaan ka handle, email, phone, kahan se aaya aur kya khareeda.</li>"
             "<li><b>CSV export</b>: Mailchimp, Brevo, ConvertKit ya kisi bhi email tool ke liye.</li>"
             "<li><b>Webhook</b>: Google Sheets, Zapier, Make ya Pabbly mein turant (Settings → Integrations, har plan par).</li></ul>"
             + fig("leads", "Leads page: Instagram contacts ke email, phone, source aur last seen",
                   "Leads: sab ek jagah, email se merge.")),
            ("Message aisa likho ki log haan bolein",
             "<ul><li>Wajah batao: <i>\"taaki next part bhi bhej sakun\"</i>.</li>"
             "<li>Ek line, bas. Freebie hi reward hai.</li>"
             "<li>Har reel par email aur number dono mat maango. Jo use karoge, wahi maango.</li>"
             "<li>Follow to unlock ke saath jodo: ek comment se follower bhi, email bhi.</li></ul>"),
            ("List ka use kaise karein",
             "<ol><li>Usi din ek welcome email bhejo, freebie dobara ke saath.</li>"
             "<li>Tag se segment karo: BUDGET wale ko finance launch, PLAN wale ko fitness.</li>"
             "<li>Launch pehle list ko: early-bird price sirf list ke liye.</li>"
             "<li>WhatsApp time-sensitive cheezon ke liye (webinar 7 baje), email baaki sab ke liye.</li></ol>"
             "<p>Sirf wahi bhejo jiska wada kiya tha, aur email tool mein unsubscribe link rakho.</p>"),
        ],
        "faq": [
            ("Email capture kis plan mein hai?", "Starter (₹149 / mahina) aur usse upar."),
            ("Kya Google Sheets mein ja sakti hain leads?", "Haan, webhook se (Settings → Integrations), 2 minute ki Google Apps Script recipe ke saath, ya Zapier/Make se."),
            ("Kya WhatsApp number bhi le sakte hain?", "Haan, email se pehle ya baad mein, same tarike se."),
            ("Galat email aaye toh?", "{brand} format check karke dobara poochta hai. Skip allowed ho toh bina email ke bhi freebie mil jaata hai."),
        ],
    },

    "instagram-dm-automation-free-mein": {
        "lang": LANG,
        "title": "Instagram DM automation free mein kaise karein",
        "description": "Bina paise ke Instagram auto DM kaise chalayein: free plan mein kya milta hai, 1,000 DMs kaafi hain ya nahi, aur kab upgrade karein.",
        "answer": "Haan, Instagram DM automation free mein ho sakta hai. {brand} ke free plan mein har mahine 1,000 DMs, har reel aur post "
                  "par comment-to-DM, keyword DMs aur Live comments milte hain, bina card ke aur bina trial khatam hone ke. Follow to unlock, "
                  "email capture aur story replies ke liye ₹149 ka Starter plan chahiye.",
        "sections": [
            ("Free plan mein kya milta hai",
             "<ul><li><b>1,000 DMs har mahine</b>, hamesha ke liye free, card nahi chahiye.</li>"
             "<li>Comment-to-DM: koi bhi reel, saare posts, ya next post.</li>"
             "<li>Keyword DMs, welcome message aur Live comment automation.</li>"
             "<li>3 tak link buttons ya choice menu, follow-up offer, delay, once per person.</li>"
             "<li>Link in bio page, Leads, reel report aur giveaway picker.</li>"
             "<li>AI DM agent try karne ke liye 25 AI replies.</li>"
             "<li>Products aur courses bechna (5% + GST har sale par, koi monthly fee nahi).</li></ul>"),
            ("Kya 1,000 DMs kaafi hain?",
             "<p>10,000 se kam followers wale zyada accounts ke liye haan. Ek DM tab use hota hai jab koi keyword comment karta hai (public "
             "reply count nahi hota). Mahine mein 3–4 keyword reels, har ek par 100–250 keyword comments, toh 1,000 ke andar rahoge.</p>"
             "<p>Limit ke paas pahunchne par {brand} 80% par alert deta hai. Limit poori hone par naye DMs agle mahine tak ruk jaate hain, "
             "ya upgrade kar sakte ho. Automations aur data waise hi rehte hain.</p>"),
            ("Free mein set kaise karein",
             "<ol><li>Instagram ko Creator account par switch karo.</li>"
             "<li>{brand} par Google se sign up karo.</li><li>Instagram connect karo (official login, password nahi).</li>"
             "<li>Auto DM → Create automation → reel aur keyword chuno.</li><li>DM likho, link button lagao, on karo.</li></ol>"
             + fig("wizard-trigger", "Create automation: comments, DM, story reply, mention aur Live ke options",
                   "Comment, DM aur Live automations free plan mein hain.", (560, 548))
             + "<p>Detail mein: <a href=\"" + H + "instagram-auto-dm-kaise-lagaye\">Instagram auto DM kaise lagaye</a>.</p>"),
            ("Doosre free tools",
             "<div class=\"scroll\"><table><thead><tr><th>Tool</th><th>Free plan</th></tr></thead><tbody>"
             "<tr><td>{brand}</td><td>1,000 DMs / mahina, hamesha</td></tr>"
             "<tr><td>LinkDM</td><td>Lagbhag 1,000 DMs</td></tr><tr><td>ReplyKaro</td><td>Lagbhag 1,000 DMs</td></tr>"
             "<tr><td>InstantDM</td><td>Lagbhag 500 DMs</td></tr><tr><td>ManyChat</td><td>Chhoti contact limit</td></tr>"
             "</tbody></table></div><p class=\"note\">Har tool ke public page se, November 2026 mein check kiya. Free plans badalte rehte hain.</p>"
             "<p>English mein poora comparison: <a href=\"/guides/free-instagram-auto-dm\">free Instagram auto DM</a>.</p>"),
            ("Kab upgrade karein",
             "<div class=\"scroll\"><table><thead><tr><th>Aapko chahiye…</th><th>Plan</th></tr></thead><tbody>"
             "<tr><td>Link sirf followers ko (follow to unlock)</td><td>Starter ₹149</td></tr>"
             "<tr><td>DM mein email ya WhatsApp number lena</td><td>Starter ₹149</td></tr>"
             "<tr><td>Story reply aur mention automation</td><td>Starter ₹149</td></tr>"
             "<tr><td>3,000 se zyada DMs, har mahine AI replies</td><td>Creator ₹199</td></tr>"
             "<tr><td>Kai Instagram accounts</td><td>Pro ₹599 / Agency ₹2,000</td></tr>"
             "</tbody></table></div>"),
            ("Free ke chakkar mein galti mat karna",
             "<p>Jo \"free\" tool aapka Instagram password maange, browser extension se DM bheje, ya anjaan logon ko message kare, usse bacho. "
             "Ye Instagram ke rules todte hain aur account risk mein daalte hain. Hamesha official API wala tool lo, jo Instagram ki apni login "
             "screen se connect ho aur jise kabhi bhi hata sako.</p>"),
        ],
        "faq": [
            ("Kya sach mein hamesha free hai?", "Haan, free plan ka koi trial period nahi hai: har mahine 1,000 DMs, bina card ke."),
            ("Free plan mein AI hai?", "25 AI replies try karne ke liye. Creator plan (₹199) mein har mahine 300."),
            ("UPI se pay kar sakte hain?", "Haan, upgrade karte waqt UPI ya card, GST price mein included."),
            ("Free plan mein follow gate hai?", "Nahi, follow to unlock Starter (₹149) se shuru hota hai."),
        ],
    },

    "instagram-story-reply-automatic": {
        "lang": LANG,
        "title": "Instagram story reply ka automatic jawab kaise de",
        "description": "Story reply aur story mention par automatic DM kaise bhejein: keyword, follow gate, thank you message aur story ideas.",
        "answer": "Story reply ka automatic jawab dene ke liye {brand} mein \"Replies to your story\" automation banao: har reply par ya sirf "
                  "keyword (jaise LINK) wale reply par DM bhejo, link button ke saath. Story mention par apne aap thank you ya discount code "
                  "bhi bhej sakte ho. Ye Starter plan (₹149) se milta hai.",
        "sections": [
            ("Do tarah ke story automation",
             "<ul><li><b>Story reply</b>: koi aapki story ka reply kare, use DM milta hai. Har reply par, ya sirf keyword wale reply par.</li>"
             "<li><b>Story mention</b>: koi apni story mein aapko tag kare, use thank you DM milta hai (ek insaan ko din mein ek baar).</li></ul>"
             "<p>Story 24 ghante mein chali jaati hai, isliye speed zaroori hai. Turant DM se log tab pakde jaate hain jab interest sabse zyada hai.</p>"),
            ("Story reply automation set karna",
             "<ol><li><b>Auto DM → Create automation → Replies to your story</b>.</li>"
             "<li><b>Any reply</b> ya <b>specific keyword</b> chuno. Agar followers se normal baat bhi karte ho, toh keyword better hai.</li>"
             "<li>Chaho toh opening message button ke saath, follow gate, email ya WhatsApp number.</li>"
             "<li>DM likho, 3 tak link buttons lagao, save karo.</li></ol>"
             + fig("wizard-story", "Story reply automation: opening message, Send me the access button aur follow request",
                   "Story reply automation, follow gate ke saath.", WIZ)
             + "<p>Ye har story par chalta hai jab tak off na karo, aur ek insaan ko ek story par ek hi DM jaata hai.</p>"),
            ("Mention par thank you",
             "<p>Ek aur automation banao: <b>Mentions you in their story</b>. Message: <i>\"Shoutout ke liye bahut shukriya {username}! 🙏 Thank you "
             "ke liye 10% off: THANKS10\"</i>. Logon ko achha lagta hai aur aur mentions aate hain.</p>"),
            ("Story ideas jinpe reply aate hain",
             "<div class=\"scroll\"><table><thead><tr><th>Story</th><th>Kya likhwao</th><th>DM mein kya</th></tr></thead><tbody>"
             "<tr><td>Flash sale</td><td>\"Reply LINK, offer sirf 24 ghante\"</td><td>Product link</td></tr>"
             "<tr><td>Poll: \"Template chahiye?\"</td><td>\"Reply YES\"</td><td>Template</td></tr>"
             "<tr><td>Webinar reminder</td><td>\"Reply JOIN\"</td><td>Joining link aur time</td></tr>"
             "<tr><td>Naya reel teaser</td><td>\"Reply EARLY\"</td><td>Early access link</td></tr>"
             "<tr><td>Customer review</td><td>\"Reply COURSE\"</td><td>Course page aur agle din follow-up</td></tr>"
             "</tbody></table></div>"),
            ("Link sticker vs reply keyword",
             "<p>Link sticker se ek tap mein link khul jaata hai, lekin baat-cheet shuru nahi hoti. Reply keyword se DM khulta hai: 24 ghante "
             "tak follow-up bhej sakte ho, follow check kar sakte ho, email le sakte ho aur 3 links de sakte ho. Dono use karo: sticker unke "
             "liye jo bas link chahte hain, keyword unke liye jinse baat aage badhani hai.</p>"),
            ("Reply ka jawab nahi gaya?",
             "<ul><li>Keyword mode hai aur reply mein keyword nahi tha: any reply chuno ya keyword ke variants add karo.</li>"
             "<li>Us insaan ko is story par DM pehle hi ja chuka hai.</li>"
             "<li>Automation off hai ya schedule ke bahar hai.</li>"
             "<li>Free plan hai: story automation ke liye Starter chahiye; free mein keyword DM automation use karo.</li></ul>"),
        ],
        "faq": [
            ("Story automation kis plan mein hai?", "Starter (₹149 / mahina) aur upar, story reply aur mention dono."),
            ("Free mein story reply ka jawab de sakte hain?", "Keyword wale story replies ko keyword DM automation free plan mein bhi jawab deta hai, aur baaki ko AI (25 replies try)."),
            ("Emoji reaction par bhi DM jaayega?", "Nahi, sirf likhe hue replies par."),
            ("Kya AI story replies ka jawab de sakta hai?", "Haan, jo reply kisi automation se match nahi hota, woh AI agent ke paas jaata hai."),
        ],
    },

    "instagram-ai-se-dm-reply-hindi": {
        "lang": LANG,
        "title": "AI se Instagram DM ka reply Hindi aur Hinglish mein",
        "description": "Instagram DMs ka jawab AI se Hindi, Hinglish ya kisi bhi bhasha mein: kaise kaam karta hai, kaise set karein, aur kya AI ko nahi karna chahiye.",
        "answer": "{brand} ka AI DM agent Instagram DMs ka jawab usi bhasha mein deta hai jismein user likhta hai: Hindi, Hinglish, English, "
                  "Tamil, Marathi ya koi aur. Ye sirf aapke FAQ, products aur links se jawab deta hai, price ya link kabhi khud se nahi banata, "
                  "aur refund ya collab jaise sawaal aapko suggested reply ke saath bhej deta hai.",
        "sections": [
            ("AI kya karta hai",
             "<p>Keyword automations fixed DMs sambhalte hain. Baaki DMs (\"price kya hai?\", \"iPhone par chalega?\", \"refund chahiye\") ghanton "
             "pade rehte hain. AI agent in sab ka jawab deta hai, aapki di hui jaankari se.</p>"
             + fig("ai-inbox", "AI Inbox: AI Hinglish mein price ka jawab de raha hai, kuch chats Needs you mein",
                   "AI Inbox: \"price kitne ka hai?\" ka jawab Hinglish mein, AI ne.")),
            ("Asli example",
             "<div class=\"scroll\"><table><thead><tr><th>Fan likhta hai</th><th>AI ka jawab (aapke FAQ se)</th></tr></thead><tbody>"
             "<tr><td>Bhai ye prompt pack kitne ka hai?</td><td>Abhi sirf ₹149 hai 🙌 Saare 39 packs, lifetime access. Yahan se le lo 👉 (link)</td></tr>"
             "<tr><td>UPI se ho jayega?</td><td>Haan bilkul! UPI, card ya netbanking sab chalta hai. Download turant milta hai 😊</td></tr>"
             "<tr><td>Mujhe refund chahiye</td><td>Aapko bhej deta hai: \"Refund request. Suggested reply: Sorry! Apna order email bhejo, main check karta hoon.\"</td></tr>"
             "<tr><td>Collab karna hai, rates?</td><td>Brand enquiry ke roop mein aapko bhej deta hai.</td></tr>"
             "</tbody></table></div>"),
            ("Set kaise karein",
             "<ol><li><b>AI Inbox → Teach your AI</b> kholo.</li>"
             "<li>Apna FAQ simple bhasha mein likho: kya bechte ho, price, delivery, refund policy, call kaise book karein. Chhote jawab best hain.</li>"
             "<li>Products aur links add karo (link in bio page se AI khud padh leta hai).</li>"
             "<li>Batao kya hamesha aapko bhejna hai: refund, brand deals, health ya paise ki salah.</li>"
             "<li><b>Try it</b> mein fan ki tarah sawaal poochho, jo jawab pasand na aaye woh FAQ mein theek karo.</li>"
             "<li>AI on karo.</li></ol>"),
            ("Control aapke haath mein",
             "<p>Har chat AI Inbox mein dikhti hai, teen filters ke saath: <b>Needs you</b>, <b>AI handling</b> aur <b>You</b>. Aap khud reply "
             "karo toh AI us chat mein chup ho jaata hai jab tak wapas na do. <b>Keep AI out</b> se kisi ek insaan ke liye AI band kar sakte ho.</p>"),
            ("AI ko kya nahi karna chahiye",
             "<ul><li>Medical ya health advice (fitness coaches ke liye zaroori).</li>"
             "<li>\"Kaunsa stock lu\" jaise investment sawaal (SEBI rules).</li>"
             "<li>Refund ka faisla, legal ya personal baatein.</li></ul>"
             "<p>Ye topics hand-off list mein daal do, AI inhe aapko bhej dega. Details: <a href=\"/guides/ai-handoff-rules\">AI hand-off rules</a>.</p>"),
            ("Kaunsa AI aur data ka kya",
             "<p>AI Anthropic ka Claude hai, API ke through. Aapki conversations model ki training mein use nahi hoti. AI ko sirf utna bheja "
             "jaata hai jitna jawab ke liye chahiye: aapka FAQ aur us chat ke recent messages.</p>"),
            ("Kitne AI replies milte hain",
             "<div class=\"scroll\"><table><thead><tr><th>Plan</th><th>AI replies</th></tr></thead><tbody>"
             "<tr><td>Free / Starter</td><td>25 try karne ke liye</td></tr><tr><td>Creator ₹199</td><td>300 / mahina</td></tr>"
             "<tr><td>Pro ₹599</td><td>2,000 / mahina</td></tr><tr><td>Agency ₹2,000</td><td>10,000 / mahina</td></tr>"
             "</tbody></table></div><p>Aur chahiye toh kisi bhi paid plan par 1,000 AI replies ₹99 mein. Ek reply ek hi gina jaata hai, chahe "
             "kitna bhi lamba ho.</p>"),
        ],
        "faq": [
            ("Kya AI Hinglish samajhta hai?", "Haan, Roman script wali Hinglish bhi, aur usi style mein jawab deta hai."),
            ("Kya AI galat price bata sakta hai?", "Nahi, woh sirf aapke FAQ aur products se jawab deta hai. Pata na ho toh aapko bhej deta hai."),
            ("Keyword DM ka jawab bhi AI dega?", "Nahi, keyword automations pehle chalte hain; AI baaki DMs ka jawab deta hai."),
            ("AI free hai?", "Free aur Starter mein 25 replies try karne ke liye; Creator (₹199) mein har mahine 300."),
        ],
    },

    "instagram-dm-se-paise-kaise-kamaye": {
        "lang": LANG,
        "title": "Instagram DM se paise kaise kamaye: creators ka funnel",
        "description": "Instagram DMs se digital products, courses aur coaching kaise bechein: free offer, follow-up, payment aur kaunsi reel ne becha.",
        "answer": "Instagram DM se paise kamane ka simple funnel: reel par free cheez ke liye keyword comment karwao, DM mein freebie do, "
                  "kuch ghante baad follow-up mein paid product offer karo, aur AI ko price aur payment ke sawaalon ka jawab dene do. {brand} "
                  "mein product, course aur UPI payment bhi hai, aur har sale ka hisaab reel ke hisaab se dikhta hai.",
        "sections": [
            ("Funnel, 5 steps mein",
             "<ol><li><b>Reel</b> jo ek problem solve kare aur end mein bole: \"Comment GUIDE, free guide DM karta hoon.\"</li>"
             "<li><b>DM</b> mein free guide, chaho toh follow gate ke baad.</li>"
             "<li><b>Email ya WhatsApp</b> unse lo jo aur chahte hain.</li>"
             "<li><b>Follow-up</b> 3–6 ghante baad: <i>\"Guide pasand aayi {username}? Poora course aaj ₹499 mein.\"</i></li>"
             "<li><b>AI agent</b> \"UPI chalega?\", \"lifetime access hai?\" jaise sawaalon ka jawab deta hai.</li></ol>"
             "<p>English mein poora breakdown: <a href=\"/guides/instagram-dm-sales-funnel\">Instagram DM sales funnel</a>.</p>"),
            ("Kya bech sakte ho",
             "<div class=\"scroll\"><table><thead><tr><th>Product</th><th>Example</th></tr></thead><tbody>"
             "<tr><td>Digital product</td><td>Prompt pack, Notion template, Lightroom preset, e-book</td></tr>"
             "<tr><td>Course</td><td>Recorded lessons, quizzes aur certificate ke saath</td></tr>"
             "<tr><td>1:1 call</td><td>Consultation, career call, profile audit</td></tr>"
             "<tr><td>Event</td><td>Webinar, workshop ya live class ka ticket</td></tr>"
             "<tr><td>Coaching</td><td>Monthly program, WhatsApp par baat ke baad</td></tr>"
             "</tbody></table></div>"),
            ("Payment kaise lein",
             "<p><b>Option 1: {brand} ka store aur courses.</b> Product ya course banao, buyer UPI ya card se pay karta hai, file ya access "
             "turant milta hai, aur paisa aapke bank account mein (Payments mein ek baar bank account add karna hota hai). Fee: Free, Starter "
             "aur Creator par 5% + GST har sale, Pro aur Agency par 2% + GST.</p>"
             "<p><b>Option 2: apna payment page.</b> Razorpay, Instamojo, Gumroad ya SuperProfile ka link DM button mein lagao. {brand} us "
             "sale par koi fee nahi leta, aur click tracking se pata chalta hai kaunsi reel se log aaye.</p>"),
            ("Follow-up hi asli game hai",
             "<p>Zyada log pehle DM mein nahi khareedte. Freebie use karne ke baad, kuch ghante mein, woh zyada ready hote hain. Follow-up 1, "
             "3, 6, 12 ya 20 ghante baad bhej sakte ho, button ke saath. Instagram ka rule: 24 ghante ke andar hi.</p>"
             "<blockquote>Prompts try kiye {username}? 🙌 Full pack master guide ke saath aaj sirf ₹149.<br>[ Full pack lo ]</blockquote>"),
            ("Kaunsi reel ne becha, ye dekho",
             "<p>Sales page har order ko us automation aur reel se jodta hai jisse woh aaya, chahe sale {brand} ke store mein hui ho ya aapke "
             "apne page par (UTM tags ke through). Jo format bechta hai, wahi dobara banao.</p>"
             + fig("sales", "Sales page: orders aur revenue, automations aur reels ke hisaab se",
                   "Sales: har order kis reel se aaya.")),
            ("Shuru karne ke liye checklist",
             "<ul><li>Ek freebie aur ek paid product jo uske baad natural lage.</li>"
             "<li>Ek keyword reel, follow gate ke saath.</li><li>3–6 ghante wala follow-up.</li>"
             "<li>AI ka FAQ: price, payment, delivery, refund policy.</li>"
             "<li>Bank account Payments mein add (agar {brand} store use kar rahe ho).</li></ul>"),
        ],
        "faq": [
            ("Kya bina website ke bech sakte hain?", "Haan, {brand} ka store, course page aur link in bio sab included hai, aur payment UPI se."),
            ("Kitna fee lagta hai?", "{brand} store mein 5% + GST (Pro par 2% + GST). Apne payment page ki sale par {brand} ka koi fee nahi."),
            ("Paise kab milte hain?", "Payment ke baad aapka hissa seedha bank account mein, aam taur par agle working day."),
            ("Kya follow-up spam lagta hai?", "Ek, kaam ka follow-up nahi lagta. Wahi message dobara mat bhejo; naya offer ya agla step do."),
        ],
    },

    "kya-instagram-auto-dm-safe-hai": {
        "lang": LANG,
        "title": "Kya Instagram auto DM safe hai? Ban se kaise bachein",
        "description": "Instagram auto DM tools safe hain ya nahi, account ban kab hota hai, aur kaunse tools aur aadatein se bachna chahiye.",
        "answer": "Haan, Instagram auto DM safe hai jab tool Meta ki official API par chalta hai, aapka password nahi maangta, aur sirf unhe DM "
                  "karta hai jinhone khud keyword comment ya message karke maanga ho. Risk tab hai jab tool password se login kare, anjaan "
                  "logon ko DM bheje, ya Instagram ki limits ignore kare.",
        "sections": [
            ("Safe aur unsafe tool mein fark",
             "<div class=\"scroll\"><table><thead><tr><th></th><th>Safe tool</th><th>Risky tool</th></tr></thead><tbody>"
             "<tr><td>Connect kaise</td><td>Instagram ki apni login screen (official API)</td><td>Aapka username aur password maangta hai</td></tr>"
             "<tr><td>Kisko DM</td><td>Sirf jinhone comment ya message kiya</td><td>Followers ya anjaan logon ko bulk DM</td></tr>"
             "<tr><td>Limits</td><td>Instagram ki limits par ruk jaata hai</td><td>Jitna ho sake utna bhejta hai</td></tr>"
             "<tr><td>Kahan chalta hai</td><td>Server par, Meta ki permission se</td><td>Browser extension ya aapke phone se</td></tr>"
             "<tr><td>Access hatana</td><td>Instagram settings se kabhi bhi</td><td>Password badalna padta hai</td></tr>"
             "</tbody></table></div>"),
            ("Instagram ke rules jo tool ko follow karne chahiye",
             "<ul><li>Ek comment par ek private DM, comment ke 7 din ke andar.</li>"
             "<li>User ke last message ke 24 ghante tak hi messages.</li>"
             "<li>Har ghante automated messages ki limit; viral reel par ruk kar baad mein bhejna.</li></ul>"
             "<p>{brand} ye sab apne aap karta hai: limit par rukta hai, refuse hue DMs 6 din tak roz retry karta hai, aur follow-ups 24 ghante "
             "ke andar bhejta hai. Details: <a href=\"/guides/instagram-dm-limits\">Instagram DM limits</a>.</p>"),
            ("Aapki taraf se safe aadatein",
             "<ul><li><b>Sirf maangne walon ko DM</b>: keyword comment ya message ke jawab mein.</li>"
             "<li><b>Jo promise kiya woh do</b>: reel mein guide boli, DM mein guide hi bhejo.</li>"
             "<li><b>Once per person</b> on rakho.</li>"
             "<li><b>Message variations</b>: <code>{Hi|Hey|Hello}</code> se har insaan ko thoda alag text.</li>"
             "<li><b>1–10 minute delay</b> chahiye toh lagao, DM insaan jaisa lagta hai.</li>"
             "<li>Bahut lambe same messages hazaaron logon ko mat bhejo.</li></ul>"
             + fig("wizard-keyword", "Automation editor: once per person switch aur rotating comment replies",
                   "Once per person aur alag-alag public replies spam jaisa feel kam karte hain.", WIZ)),
            ("Account par problem aaye toh",
             "<p>Kabhi Instagram connection expire ho jaata hai (jaise password badalne par) ya account par temporary limit lagti hai. {brand} "
             "aise mein alert deta hai aur DMs rok deta hai, taaki problem badhe nahi. Reconnect karne par sab wapas chalne lagta hai. "
             "DM nahi gaya toh: <a href=\"/guides/why-instagram-dm-not-sent\">DM kyun nahi gaya</a>.</p>"),
            ("Data aur privacy",
             "<p>Official API wala tool sirf wahi data le sakta hai jiski permission aapne Instagram ki screen par di. {brand} aapka password "
             "kabhi nahi dekhta. Instagram Settings → Business integrations (ya Apps and websites) se access kabhi bhi hata sakte ho, aur "
             "{brand} mein disconnect karke apna data delete kar sakte ho.</p>"),
        ],
        "faq": [
            ("Kya auto DM se account ban hota hai?", "Official API tool aur sirf maangne walon ko DM bhejne par nahi. Ban ka risk password wale tools aur bulk cold DMs se hai."),
            ("Kya Instagram ko pata chalta hai?", "Haan, kyunki official API Meta ki hi hai. Isliye ye rules ke andar hai."),
            ("Password dena safe hai?", "Nahi. Koi bhi tool jo Instagram password maange, usse bacho. {brand} kabhi password nahi maangta."),
            ("Bahut saare DMs ek saath gaye toh?", "Viral reel par Instagram speed kam karta hai; achha tool ruk kar baad mein bhejta hai, koi DM khota nahi."),
        ],
    },
})

# ---------------------------------------------------------------- the topic page that groups them

HINGLISH_PILLAR = {
    "lang": LANG,
    "title": "Instagram auto DM guides Hinglish mein",
    "short": "Hinglish guides",
    "description": "Instagram auto DM, followers, leads aur sales ki saari guides Hinglish mein: kya hai, kaise lagaye, free mein, safe hai ya nahi.",
    "answer": "Yahan Instagram DM automation ki saari zaroori guides Hinglish mein hain: auto DM kya hai, kaise lagaye, comment par DM, "
              "followers badhana, email aur WhatsApp number lena, free plan, story replies, AI se Hindi mein reply, DM se kamai, aur safety.",
    "about": ["instagram", "meta", "lead-generation"],
    "terms": ["comment-to-dm", "follow-gate", "lead-capture", "ai-dm-agent", "messaging-window"],
    "sections": [
        ("Kahan se shuru karein",
         "<ol><li>Naye ho? Pehle padho <a href=\"" + H + "instagram-auto-dm-kya-hai\">Instagram auto DM kya hai</a>.</li>"
         "<li>Phir <a href=\"" + H + "instagram-auto-dm-kaise-lagaye\">5 steps mein auto DM lagao</a>.</li>"
         "<li>Followers chahiye: <a href=\"" + H + "instagram-par-followers-kaise-badhaye-dm-se\">follow to unlock</a>.</li>"
         "<li>List banani hai: <a href=\"" + H + "instagram-se-email-whatsapp-number-kaise-le\">email aur WhatsApp number</a>.</li>"
         "<li>Bechna hai: <a href=\"" + H + "instagram-dm-se-paise-kaise-kamaye\">DM se paise kaise kamaye</a>.</li></ol>"),
        ("Ek nazar mein",
         "<div class=\"scroll\"><table><thead><tr><th>Sawaal</th><th>Chhota jawab</th></tr></thead><tbody>"
         "<tr><td>Free hai?</td><td>Haan, 1,000 DMs / mahina, bina card</td></tr>"
         "<tr><td>Safe hai?</td><td>Official API wala tool, password nahi, sirf maangne walon ko DM</td></tr>"
         "<tr><td>Kitna time?</td><td>Pehli baar 5–10 minute</td></tr>"
         "<tr><td>Hindi mein AI reply?</td><td>Haan, Hindi, Hinglish aur kisi bhi bhasha mein</td></tr>"
         "<tr><td>Follow gate kis plan mein?</td><td>Starter ₹149 se</td></tr>"
         "</tbody></table></div>"
         "<p>English mein aur detail chahiye? <a href=\"/instagram-dm-automation\">Instagram DM automation: the complete guide</a>.</p>"),
    ],
    "faq": [
        ("Instagram auto DM kya hota hai?", "Ek tool jo keyword comment, story reply ya DM par apne aap aapki taraf se DM bhejta hai, Meta ki official API se."),
        ("Kya ye free mein ho sakta hai?", "Haan, {brand} ke free plan mein har mahine 1,000 DMs hain."),
        ("Kya Hinglish mein DM bhej sakte hain?", "Haan, message aap jaise chaho likh sakte ho, aur AI agent Hinglish mein jawab deta hai."),
    ],
    "clusters": [("guide", g) for g in ("instagram-auto-dm-kya-hai", "instagram-auto-dm-kaise-lagaye", "comment-par-automatic-dm-kaise-bheje",
                                        "instagram-par-followers-kaise-badhaye-dm-se", "instagram-se-email-whatsapp-number-kaise-le",
                                        "instagram-dm-automation-free-mein", "instagram-story-reply-automatic", "instagram-ai-se-dm-reply-hindi",
                                        "instagram-dm-se-paise-kaise-kamaye", "kya-instagram-auto-dm-safe-hai")],
}
PILLAR_SLUG = "instagram-auto-dm-hindi"
