"""Text for the public policy pages (/terms, /refund-policy, /privacy-policy, /contact). Edit the wording here."""

UPDATED = "7 November 2026"
EMAIL = "kumarom1315@gmail.com"
OWNER = "Om Kumar (@aiwith.om)"

# slug: (title, Hinglish one-line summary, [(heading, [paragraphs or "• bullet" lines])])
PAGES = {
    "terms": ("Terms & Conditions", "Course sirf tumhare personal use ke liye hai, 6 mahine ka access, aur followers ya income ki koi guarantee nahi.", [
        ("Who we are", [f"This website (advocmedia.in) and the course \"Claude se Instagram grow karo\" are run by {OWNER}. "
                        f"Questions: {EMAIL}."]),
        ("The course", [
            "• The course is sold and delivered through SuperProfile. Payment, invoice and course access happen on SuperProfile.",
            "• Access lasts 6 months from the date of purchase. Bonus files you download are yours to keep for personal use.",
            "• Batch 1 includes live classes on Zoom (Sat & Sun, 9–10 PM IST, 14 Nov – 6 Dec 2026). Classes are recorded and the recordings are added to the course. "
            "If you attend, your name or chat messages may appear in the recording; you can keep your camera off and we blur or cut other students' faces and names before uploading.",
            "• If a live class has to move, we announce the new time in the course and by email before the class."]),
        ("Your use of the content", [
            "• The videos, workbook, bonuses and templates are for your own personal use.",
            "• Please don't share your login, or re-sell, re-upload or publicly post the course content.",
            "• You can use the prompts and templates to make your own content and run your own Instagram page."]),
        ("No guarantees", ["The course teaches the system Om used on his own page. It does not guarantee followers, views, sales or income. "
                           "Results depend on your niche, consistency and content."]),
        ("Third-party tools", ["The course mentions tools like Claude, CapCut, ElevenLabs, ManyChat and Instagram. They have their own terms and prices, "
                               "which can change. Check each tool's pricing page before you sign up. We are not responsible for changes to those tools."]),
        ("Free guides and automation", ["Free guides on advocmedia.in/free are provided as they are, for learning. "
                                        "When you comment a keyword on our Instagram reels, our automation replies and sends you the guide link in your DMs."]),
        ("Changes", ["We may update these terms. The date at the top shows the latest version."]),
    ]),
    "refund-policy": ("Refund Policy", "Digital course hai, isliye access milne ke baad refund nahi hota. Access ya payment ki koi problem ho, to email karo, 48 ghante mein solve karenge.", [
        ("Digital product", ["The course, workbook and bonuses are digital and available immediately after payment, so we don't offer refunds once access is given."]),
        ("When we will help", [
            "• You paid but did not get access: email us and we'll fix it, or refund you if we can't.",
            "• You were charged twice for the same purchase: the extra payment is refunded.",
            "• A live class is cancelled and not rescheduled: you get the recording of the topic, or a refund if we can't provide it."]),
        ("How to ask", [f"Email {EMAIL} (or DM @aiwith.om on Instagram) with your name, the email you used at checkout and your payment ID. "
                        "We reply within 48 hours. Approved refunds go back to your original payment method; banks usually take 5–7 working days."]),
    ]),
    "privacy-policy": ("Privacy Policy", "Hum sirf wahi data rakhte hain jo course aur DMs ke liye zaroori hai, aur kisi ko bechte ya share nahi karte.", [
        ("What we collect", [
            "• Course buyers: name, email, phone number and Instagram username you enter at checkout (collected by SuperProfile).",
            "• Instagram automation: when you comment a keyword on our reels or message our account, we receive your Instagram username, "
            "the comment or message and whether you follow the account, through Instagram's official API. We use this only to reply and send the link you asked for.",
            "• Website: we count clicks on links on our link page. On the home page (advocmedia.in) and the course page (advocmedia.in/course) we use the Meta Pixel to measure our Instagram/Facebook ads: it tells Meta that a page was viewed and, on the course page, when Join now is tapped, so we can see which ads work. It uses Meta cookies; you can limit this in your Meta ad settings or by blocking third-party cookies."]),
        ("How we use it", ["To give course access, send class updates, deliver the free guides you request, answer your questions and see which content helps people. "
                           "We don't sell or rent your data, and we don't share it except with the services that run the course and website."]),
        ("Services we use", ["SuperProfile (course checkout, payments and access), Zoom (live classes), Instagram/Meta (comments, DMs and ad measurement with the Meta Pixel) and our hosting and database providers. "
                             "Card and UPI details are handled by the payment provider; we never see or store them."]),
        ("How long we keep it", ["Buyer details are kept for as long as you have course access and as needed for invoices and the law. "
                                 "Automation activity is kept only for a short recent history."]),
        ("Your choices", [f"You can ask us to show, correct or delete your data: email {EMAIL}. You can stop DMs anytime by not commenting keywords, or by blocking or messaging the account."]),
    ]),
    "contact": ("Contact", "Course, payment, live class ya collab: kisi bhi baat ke liye email ya Instagram DM karo.", [
        ("Email", [f"{EMAIL}", "We reply within 48 hours (usually faster)."]),
        ("Instagram", ["DM @aiwith.om. Students: start your message with \"STUDENT\" so we see it first.", "Brands: DM \"COLLAB\" or email us."]),
        ("Course help", ["Payment done but no access? Send the email you used at checkout and your payment ID, and we'll sort it out."]),
    ]),
}
