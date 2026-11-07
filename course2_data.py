"""Content for the Course 2 sales page (/digital-products). Same template as /course; defaults below; link, price, MRP, note and on/off are set in /links/edit → 🎓 Course 2."""

TITLE = "AI se Digital Products banao aur becho"
OG_TITLE = "AI se Digital Products banao aur becho: idea → product → pehli sale"
KICKER = "Course 2 · Hinglish video course"
H1_A = "AI se Digital Products"
H1_B = "banao aur becho"
SUBTITLE = ("Idea se pehli sale tak ka poora system: kya banana hai, Claude se kaise banana hai, sales page, checkout aur "
            "Instagram launch. Wahi process jisse maine apna prompt bundle aur course banaya aur becha. Hinglish mein, step by step.")
PROOF_A = "Idea →"
PROOF_B = "Sale"
PROOF_C = ""
PROOF_T = "Real case study: mera prompt bundle, start to finish"
PROOF_S = "Process milega, income ki guarantee nahi. Honest course."
COVER = "free/course2.jpg"
KEYWORD = "PRODUCT"
PRICE_NOTE = "Course 1 (Batch 1) students: coupon se ₹499"
HONEST = ("Honest baat: ye income ki guarantee nahi hai. Pehle 1–3 mahine sales kam ho sakti hain. Ye wo system hai jo maine khud use kiya; "
          "results tumhari audience, product aur consistency pe depend karenge.")
FINAL = "Idea se pehli sale tak, poora system."

DEFAULTS = {"enabled": True, "url": "", "price": "799", "mrp": "", "live": {"enabled": False}}

STATS = [("8", "modules"), ("31", "lessons"), ("~4h", "video"), ("6", "bonuses")]

OUTCOMES = [
    ("🔎", "Idea jo bike", "DMs aur comments se pain list, aur banane se pehle validation: poll, waitlist, pre-sale."),
    ("🤖", "Claude se product banao", "Ebook, prompt pack, templates ya mini-course: apni awaaz mein, quality check ke saath."),
    ("💰", "Sahi price", "₹99 se ₹999 ka price ladder, aur pehle product ka price kaise chunein."),
    ("🧾", "Sales page jo convert kare", "Offer stack, honest copy, proof bina jhooth ke, aur zaroori policy pages."),
    ("⚡", "Checkout + delivery", "SuperProfile setup, direct checkout link, delivery aur GST basics."),
    ("🚀", "Instagram launch", "3 launch reels, story sequence aur comment → DM se seedha product page tak."),
]

MODULES = [
    ("Module 0", "Welcome + honest reality", "Free preview", [
        "Digital product kya hai: ek baar banao, baar-baar becho", "Maine kya banaya (aur kaise)", "Tools aur kharcha", "Honest expectations"]),
    ("Module 1", "Idea jo bike", None, [
        "DMs + comments se \"pain list\" nikalo (free preview)", "5 product types: kaunsa kab", "Banane se pehle validate karo", "Pricing: ₹99 se ₹999 ka ladder"]),
    ("Module 2", "Product banao Claude ke saath", None, [
        "Outline jo transformation de", "Ebook / guide: apni awaaz mein", "Prompt pack", "Templates: Notion, Sheets, Canva",
        "Mini-course + workbook", "Design: cover, mockup, PDF", "Quality check"]),
    ("Module 3", "Offer + sales page", None, [
        "Offer stack", "Sales copy with Claude", "Proof bina jhooth ke", "Sales page banao", "Refund, terms, privacy, contact"]),
    ("Module 4", "Checkout + delivery", None, [
        "SuperProfile setup", "Delivery", "Checkout friction kam karo", "GST + invoice basics"]),
    ("Module 5", "Launch on Instagram", None, [
        "Launch plan", "3 launch reels", "Story sequence", "Comment keyword → DM → product", "Launch week checklist"]),
    ("Module 6", "After the sale", None, [
        "Support", "Real testimonials", "Refunds + updates", "Buyers list"]),
    ("Module 7", "Scale", None, [
        "Bundles, bump offers, upsells", "Evergreen selling", "Price test + second product", "Collabs + affiliates"]),
    ("Bonus class", "Prompt Bundle case study", "Bonus", [
        "Idea → build → price → listing → promotion → kya chala, kya nahi → kaise wo Course 1 ka bonus bana"]),
]

INCLUDED = [("🎥", "31 video lessons + bonus class", "Screen pe step by step, Hinglish mein"),
            ("📘", "Workbook (PDF)", "Har lesson ka copy-ready Claude prompt, checklists aur case-study template"),
            ("🧩", "Real examples", "Mere course launch ke asli pages, reels, stories aur setup: seekhne ke liye")]

BONUSES = [
    ("🔎", "Product Idea Finder", "prompt pack", "Pain finder, idea scorer, price ladder aur outline builder: idea se outline tak."),
    ("🧾", "Sales Page Template", "template", "Fill-in copy aur structure: headline, outcomes, curriculum, FAQ, honest note."),
    ("🚀", "Launch Kit", "scripts + templates", "3 launch reel scripts, 9 story frame templates aur posting guide."),
    ("📜", "Legal Pages Template", "template", "Terms, refund, privacy aur contact: simple English + Hinglish summary."),
    ("✅", "SuperProfile Setup Checklist", "checklist", "Har field, sahi order mein: product, price, coupon, checkout, delivery."),
    ("📊", "Pricing + Launch Tracker", "Google Sheet", "Price ladder, launch week plan aur sales tracking ek sheet mein."),
]

FOR = ["Creators jinke paas audience hai (1–5K followers bhi chalega)", "Freelancers, teachers aur coaches jo apna knowledge bechna chahte hain",
       "Course 1 students jo ab page se kamana chahte hain"]
NOT_FOR = ["\"Overnight passive income\" dhoondne wale", "Jo kisi aur ka content copy ya resell karna chahte hain"]

FAQ = [("Kya badi audience chahiye?", "Nahi. Chhoti, engaged audience kaafi hai. Module 1 mein sikhoge ki banane se pehle demand kaise check karein."),
       ("Kya design ya coding aani chahiye?", "Nahi. Claude, Canva aur Google Docs/Notion se sab hota hai. Coding zaroori nahi."),
       ("Course 1 ke students ke liye discount?", "Haan. Course 1 (Batch 1) students ko ₹499 ka coupon course ke andar milega."),
       ("Access kitne time ke liye hai?", "Purchase ke din se 6 mahine tak: saare videos, workbook aur bonuses. Bonus files download karke rakh sakte ho."),
       ("Course kahan milega?", "Payment ke baad course SuperProfile pe khulta hai: videos, workbook aur saare bonuses wahin."),
       ("Kya income guaranteed hai?", "Nahi. Koi bhi honest course ye promise nahi kar sakta. System milega; kaam tumhe karna hai.")]
