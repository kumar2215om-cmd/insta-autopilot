"""Guides rebuilt from the claude.ai artifact PDFs (REPO, FREE, SEED, LINK, YOUTUBE). Run from repo root:
    python3 tools/guides_src/batch1_artifacts.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from guidepage import page
from md2guide import update_index
OUT = "freebies/guides"
gh = lambda p: f"[{p}](https://github.com/{p})"

G = {}
G["REPO"] = page("REPO", "₹200 AdBlock chip", "+ 9 GitHub repos",
 "Reel ke saare 10 repos: ₹200 wali ESP32-C3 AdBlock chip ka setup, aur 9 kamaal ke GitHub repos. Har repo ka GitHub path diya hai.", [
 ("Pehle padho", "Ye list kaise use karein", [
   ("p", "Har repo ka GitHub path diya hai; `github.com/` ke baad paste karo (ya seedha link pe tap karo)."),
   ("warn", "GitHub pe naam badalte rehte hain aur kai naye repos ki details verify nahi ho paati. Kuch bhi install karne se pehle repo khud kholo: **stars, README aur last update** dekho.")]),
 ("AdBlock chip", "₹200 AdBlock chip: ESP32-C3 Adblock", [
   ("p", f"Repo: {gh('M-Abozaid/esp32-c3-adblock')}. Ye Pi-hole jaisa DNS blocker hai jo ad domains ki request ghar ke network pe hi rok deta hai."),
   ("list", ["ESP32-C3 SuperMini board (online lagbhag ₹150–350)", "USB-C data cable aur ek laptop", "Router ka admin login (DNS setting badalne ke liye)"]),
   ("ol", ["Laptop pe **VS Code** aur **PlatformIO** extension install karo.", "GitHub se repo download karo aur PlatformIO mein folder kholo.",
           "README ke hisaab se apna WiFi naam aur password config mein daalo.", "Board USB se lagao aur **Upload** dabao (firmware flash hoga).",
           "Board ko router ke USB ya kisi charger se power do; README se uska IP address note karo.",
           "Router ki DNS setting mein wo IP daalo aur save karo. Ab ghar ke har device pe ad domains block honge."]),
   ("warn", "**Limits (sach):** YouTube aur Instagram ke ads nahi rukte, kyunki wo usi server se aate hain jisse video. Board band hua to internet DNS ki wajah se ruk sakta hai; router mein **backup DNS** rakho. Exact steps aur supported features repo ke README se confirm karo.")]),
 ("9 repos", "9 kamaal ke repos", [
   ("table", ["#", "Repo", "Kya karta hai", "GitHub"], [
     ["1", "**DeepSeek Harness**", "DeepSeek ka agent harness, ek npx command aur browser mein Web UI (developer preview)", gh("deepseek-ai/deepseek-harness")],
     ["2", "**BrowserSkill**", "AI agent aapke logged-in Chrome mein forms bharta hai, pages padhta hai", gh("Tencent/BrowserSkill")],
     ["3", "**Laya**", "100+ languages mein support tickets route karta hai, bahut tez", gh("NandhaKishorM/laya")],
     ["4", "**OpenDesign**", "Brief do, agent aapke design system mein prototype banata hai", gh("nexu-io/open-design")],
     ["5", "**Shaders**", "200+ WebGPU effects, seedha React ya Vue mein", gh("shader-effects-inc/shaders")],
     ["6", "**Answer Me With HTML**", "Lamba text nahi, diagrams wala page aur explainer video", gh("QingYuan/answer-me-with-html")],
     ["7", "**iFixAi**", "2 minute mein AI agent ka report card, A se F tak", gh("ifixai-ai/iFixAi")],
     ["8", "**VibeWise**", "AI code likhne se pehle approach poochta hai, trade-offs samjhata hai", gh("nyboot/vibe-wise")],
     ["9", "**Plexo**", "WiFi aur phone hotspot milake ek fast download", gh("anmolkapil/plexo")]]),
   ("tip", "DeepSeek Harness ka naam aur star count humne verify nahi kiya; agar repo na mile ya alag owner ka ho, use skip karo.")]),
 ("Safety", "GitHub repos chalane se pehle", [
   ("list", ["**Owner check karo:** naam copy karne wale fake repos bhi hote hain; official org ya jaana-maana developer ho.",
             "**README aur Issues padho:** dekho kitne log use kar rahe hain aur kya problems aa rahi hain.",
             "Browser ya account access wale tools (jaise BrowserSkill) pehle ek **test account** pe chalao.",
             "**Command copy karne se pehle samjho:** npx ya script seedha aapke system pe code chalata hai."])]),
])

G["FREE"] = page("FREE", "10 open-source", "alternatives to paid apps",
 "Ye 10 open-source repos paid tools ka kaam kar sakte hain, kyunki aap inhe apne server pe khud chalate ho (self-hosting).", [
 ("Pehle padho", "Free software, par zimmedari aapki", [
   ("p", "Software free hai, par **server, setup, updates aur backups** ka kharcha aur zimmedari aapki hai. Testing aur chhoti teams ke liye ye bahut paise bachate hain."),
   ("p", "Har repo ka GitHub path diya hai; `github.com/` ke baad paste karo (ya link pe tap karo).")]),
 ("10 repos", "10 repos aur kis paid tool ki jagah", [
   ("table", ["#", "Repo", "Kiski jagah", "Kya karta hai", "GitHub"], [
     ["1", "**Coolify**", "Vercel, Heroku, Netlify", "Apne server pe app deploy, git push se live", gh("coollabsio/coolify")],
     ["2", "**OpenHands**", "Paid AI coding agents", "AI agent jo code likhta, commands chalata, web browse karta hai", gh("OpenHands/OpenHands")],
     ["3", "**Maxun**", "Paid web scrapers", "Bina code ke website scrape, point and click", gh("getmaxun/maxun")],
     ["4", "**Open WebUI**", "ChatGPT jaisa interface", "Apni machine pe chat UI, Ollama ke saath offline", gh("open-webui/open-webui")],
     ["5", "**Browser Use**", "Paid browser automation", "AI websites pe forms bharta, shopping karta, data nikalta hai", gh("browser-use/browser-use")],
     ["6", "**Langflow**", "Paid AI workflow builders", "Drag and drop se AI workflows aur RAG, API ki tarah chalao", gh("langflow-ai/langflow")],
     ["7", "**Supabase**", "Firebase", "Postgres database, login, storage, realtime", gh("supabase/supabase")],
     ["8", "**Stirling PDF**", "Paid PDF editors", "50+ PDF tools (merge, split, sign, OCR), files apne server pe", gh("Stirling-Tools/Stirling-PDF")],
     ["9", "**Crawl4AI**", "Paid crawling APIs", "Kisi bhi website ko AI-ready clean markdown mein badlo", gh("unclecode/crawl4ai")],
     ["10", "**Dify**", "Paid AI app platforms", "Agents, workflows aur RAG ek platform pe", gh("langgenius/dify")]]),
   ("tip", "Repo naam kabhi-kabhi badalte hain; GitHub purane link ko aksar naye pe redirect kar deta hai.")]),
 ("Shuru karo", "Kahan se shuru karein", [
   ("ol", ["**Pehle laptop pe try karo:** Open WebUI + Ollama ya Stirling PDF jaise tools Docker se local chal jaate hain, server ki zaroorat nahi.",
           "**Server chahiye to:** ek chhota VPS (cloud server) lo, aur us pe Coolify install karo; baaki apps Coolify se deploy karna aasaan hai.",
           "**Backups on rakho:** database wale tools (Supabase, Dify) ke liye regular backup set karo.",
           "**Updates:** mahine mein ek baar version update aur security patches check karo.",
           "**Licence padho:** kuch repos (jaise Dify, ya AGPL wale) commercial ya multi-tenant use pe shartein lagate hain; business mein use se pehle LICENSE file padho."])]),
])

G["SEED"] = page("SEED", "Seedance free credits:", "apps list",
 "Seedance ByteDance ka AI video model hai: prompt likho, cinematic video banti hai. Kuch apps roz free credits dete hain jo daily refill hote hain.", [
 ("Pehle padho", "Free credits ka sach", [
   ("p", "Seedance kai apps ke andar chalta hai, aur unme se kuch roz free credits dete hain jo daily refill hote hain."),
   ("warn", "Free credits limited hote hain, queue lambi ho sakti hai aur kuch apps watermark lagate hain. Free offers jaldi badalte hain, isliye neeche ki list ek starting point hai; har app mein khud check karo ki abhi Seedance aur free credits available hain ya nahi.")]),
 ("Apps", "Kahan try karein", [
   ("table", ["App", "Kiske liye", "Free offer (last known, verify)", "Kahan"], [
     ["**Dreamina**", "Creators, bina code", "Daily free credits, refill hote hain", "dreamina.capcut.com"],
     ["**CapCut**", "Video editing + AI features", "Kuch AI features pe limited free credits", "capcut.com (app ya web)"],
     ["**BytePlus ModelArk**", "Developers (API)", "Naye account pe free trial tokens", "byteplus.com, ModelArk section"],
     ["**fal.ai / Replicate**", "Developers (API)", "Pay-per-use; kabhi-kabhi naye users ko thode credits", "fal.ai, replicate.com"]]),
   ("tip", "\"Free offer\" column last-known jaankari hai; use karne se pehle app ke pricing/credits page pe confirm karo. App mein model list mein **\"Seedance\"** dhoondo; kai apps naye version ko alag naam se dikhate hain.")]),
 ("Credits", "Credits bachane ke tips", [
   ("list", ["**Pehle short clip:** 5 second ki video se prompt test karo, sahi lage tab lambi banao.",
             "**Low resolution pehle:** draft kam quality mein, final hi high quality mein.",
             "**Roz use karo:** daily credits aksar jama nahi hote; jo aaj ke hain, aaj use karo.",
             "**Prompt ek baar mein pakka:** neeche wala template bharo, baar-baar regenerate nahi karna padega."]),
   ("prompt", "Prompt template", "[Shot type: drone / close-up / wide], [subject + action], [location], [time of day + light], [mood], [camera move: slow push-in / pan left], cinematic, [aspect ratio 9:16], [audio: ambient sound / music style]"),
   ("p", "**Example:** drone shot, ek akela traveller pahaad ki choti pe khada, golden hour sunset, peaceful mood, slow push-in, cinematic, 9:16, soft wind sound.")]),
 ("Bacho", "In \"unlimited free tricks\" se bacho", [
   ("list", ["**Fake / multiple accounts:** app ke terms todte hain; account aur credits dono ban ho sakte hain.",
             "**Leaked API keys:** kisi aur ki key use karna galat hai, aur aksar wo key band ho jaati hai.",
             "**\"Unlimited\" mod apps / APK:** inme malware ka khatra hota hai; sirf official app ya website use karo.",
             "**Paid course ya \"secret trick\" bechne wale:** jo free hai, wo upar ki list mein hai."])]),
])

G["LINK"] = page("LINK", "AI tools affiliate programs:", "free list",
 "Kai AI tools commission dete hain jab koi aapke link se unka paid plan leta hai. AI tools pe content banate ho to ye sabse natural side income hai.", [
 ("Pehle samjho", "Affiliate marketing kya hai", [
   ("p", "Kai AI tools aapko commission dete hain jab koi aapke link se unka paid plan leta hai. Isse **affiliate marketing** kehte hain."),
   ("warn", "Seedha sach: audience ke bina pehle mahine shayad ek bhi sale nahi hogi. Ye list shuruaat ke liye hai, \"raaton-raat ameer\" plan nahi.")]),
 ("5 steps", "5 steps mein kaise kaam karta hai", [
   ("ol", ["**Tool chuno jo aap sach mein use karte ho.** Jo tool aapne khud use nahi kiya, uski recommendation log pakad lete hain.",
           "**Affiliate program join karo.** Tool ki website ke footer mein \"Affiliates\" ya \"Partners\" link dhoondo, form bharo, approval ka wait karo (aksar 1 se 7 din).",
           "**Apna link lo.** Approval ke baad dashboard mein aapka unique tracking link milta hai.",
           "**Content banao, link share karo.** Tutorial reel, before/after, ya comparison banao. Link bio mein ya DM mein do, aur saaf likho ki ye affiliate link hai.",
           "**Commission track karo.** Koi aapke link se plan khareede to dashboard mein sale dikhti hai. Kai tools monthly subscription pe har mahine commission dete hain, ek fixed period tak."])]),
 ("Programs", "AI tools jinke affiliate programs hain", [
   ("tip", "Rates programs badalte rehte hain, isliye \"Last known\" column sirf andaaza hai: join karne se pehle tool ka affiliate page zaroor check karo."),
   ("table", ["Tool", "Kya karta hai", "Type", "Last known (verify)", "Kahan"], [
     ["**ElevenLabs**", "AI voice, voiceover, dubbing", "Recurring", "~22% for first 12 months", "elevenlabs.io footer → Affiliates"],
     ["**Writesonic**", "AI writing, SEO articles", "Recurring", "~30% recurring", "writesonic.com footer → Affiliate"],
     ["**Surfer SEO**", "AI SEO content optimisation", "Recurring", "~25% recurring", "surferseo.com → Affiliate program"],
     ["**Semrush**", "SEO + AI marketing suite", "One-time per sale", "~$200 per new subscription", "semrush.com → Affiliate program"],
     ["**Synthesia**", "AI avatar videos", "Recurring", "Check page", "synthesia.io footer → Affiliates"],
     ["**HeyGen**", "AI avatar + video translation", "Check page", "Check page", "heygen.com footer → Affiliates"],
     ["**Descript**", "AI video and podcast editing", "Check page", "Check page", "descript.com footer → Affiliates"],
     ["**Murf AI**", "AI voiceover", "Recurring", "Check page", "murf.ai footer → Affiliate"],
     ["**InVideo AI**", "Prompt se video", "Recurring", "Check page", "invideo.io footer → Affiliate"],
     ["**Make**", "No-code automation", "Recurring", "Check page", "make.com → Partners / Affiliate"],
     ["**Notion**", "Notes, docs, Notion AI", "Check page", "Check page", "notion.com → Affiliates"]]),
   ("p", "ChatGPT, Claude, Midjourney aur Gemini jaise bade AI tools ka (last known) koi open public affiliate program nahi hai, isliye wo is list mein nahi hain.")]),
 ("Networks", "Aur programs kahan milenge", [
   ("p", "Zyaadatar SaaS aur AI tools apna affiliate program kisi network pe chalaate hain. Ek account banao, wahan se kai programs mein apply kar sakte ho."),
   ("list", ["**PartnerStack:** bahut saare SaaS aur AI tools yahan hain, ek hi dashboard mein sab programs.",
             "**Impact.com:** bade software brands ke programs.",
             "**Rewardful / FirstPromoter:** chhote AI startups inse program chalaate hain; link tool ki website pe hi milta hai."]),
   ("tip", "Shortcut: kisi bhi tool ki website ke footer mein \"Affiliates\", \"Partners\" ya \"Refer & earn\" search karo.")]),
 ("Rules", "Rules aur asli catch", [
   ("warn", "India mein **ASCI ke influencer guidelines** kehte hain ki paid ya affiliate promotion saaf label karo. Post ke shuru mein \"#ad\" ya \"Affiliate link\" likho, caption ke end mein chhupao mat."),
   ("list", ["**Audience pehle:** sales tab aati hain jab log aapke recommendations pe trust karte hain. Pehle 1 se 3 mahine zero ho sakte hain.",
             "**Cookie window:** link pe click ke baad ek fixed time (aksar 30 se 90 din) tak ki sale hi aapki count hoti hai.",
             "**Payout:** zyaadatar programs PayPal, Stripe ya bank transfer se dete hain, minimum threshold ke baad, aur 30 se 60 din ki delay ke saath.",
             "**Refunds:** customer refund le le to commission wapas kat jaata hai.",
             "**Tax:** foreign income bhi taxable hai, apne CA se ek baar baat kar lo.",
             "**Program ke rules padho:** kai programs brand-name ads, coupon sites aur self-referral ban karte hain; tod diya to account band."])]),
 ("Ideas", "Link promote karne ke 5 content ideas", [
   ("list", ["**60-second tutorial:** tool se ek real kaam karke dikhao, start se result tak.",
             "**Before / after:** bina tool vs tool ke saath, same kaam.",
             "**Comparison:** 2 tools, ek task, kaun jeeta aur kyun.",
             "**Free vs paid:** free plan kahan tak chalta hai, paid kab lena chahiye. Isse trust banta hai.",
             "**Comment-to-DM:** reel mein ek keyword do; approved automation tool se DM mein link bhejo, \"Affiliate link\" label ke saath."])]),
])

G["YOUTUBE"] = page("YOUTUBE", "Claude as your", "YouTube manager",
 "Claude aapke channel ki videos aur views padhta hai, aur agle hafte ke titles, hooks, descriptions aur schedule ka draft banata hai. Final \"yes\" hamesha aapka.", [
 ("Kya milega", "Setup se kya hoga", [
   ("p", "Is setup se Claude aapke YouTube channel ki videos aur views padhta hai, aur agle hafte ke titles, hooks, descriptions aur schedule ka draft banata hai. **Final \"yes\" hamesha aapka:** bina approval kuch post mat hone do."),
   ("warn", "Ye setup ek third-party service (**Uplika**) ke through hai. Use karne se pehle unki pricing aur terms khud check karo.")]),
 ("Setup", "Setup (5 minute)", [
   ("ol", ["claude.ai kholo aur left menu mein **Customize** pe jao.", "**Connectors** tab kholo, phir **Add custom connector** dabao.",
           "Name: **Uplika**. Remote MCP server URL: Uplika ki website pe diya hua link paste karo (sirf official site se lo).",
           "**Add**, phir **Connect** dabao. Uplika mein sign in karo.", "YouTube chuno, apna channel select karo, permissions padho, phir **Allow**.",
           "Connectors list mein Uplika ke saamne **Connected** dikhe, to setup done."]),
   ("tip", "Custom connectors har Claude plan pe available nahi ho sakte; agar option na dikhe to apna plan check karo.")]),
 ("Prompt", "Ready-made prompt", [
   ("p", "Neeche wala prompt copy karke Claude mein paste karo. Pehle confirm karo ki Claude bole \"Connected to Uplika\". Brackets wali jagah apni details bharo."),
   ("prompt", "Copy karo", "Tum mere YouTube channel ke manager ho. Channel: [channel name], niche: [topic], audience: [kaun dekhta hai], language: [Hinglish/Hindi/English].\n\n1. Mere last 30 videos aur unke views, watch time padho. Top 5 aur bottom 5 videos batao, aur unme kya fark hai.\n2. Mere niche mein abhi jo Shorts chal rahe hain, unke 5 patterns batao (hook style, length, topic).\n3. Agle 7 din ke liye 7 upload ideas do. Har ek ke liye: title (60 characters se kam), pehle 3 second ka hook, description (keywords ke saath), aur best posting time.\n4. Meri purani videos mein se 5 kamzor titles chuno aur better titles suggest karo. Badlav khud mat karna.\n5. Pending comments ke liye reply drafts likho, mere tone mein. Post mat karna.\n\nRules: kuch bhi publish, schedule ya edit karne se pehle mujhse \"yes\" lo. Har jawab table mein do.")]),
 ("Routine", "Har hafte ka routine (15 minute)", [
   ("table", ["Din", "Kya karna hai"], [
     ["**Monday**", "\"Pichle hafte ki videos ka performance batao, kya chala aur kya nahi.\""],
     ["**Monday**", "\"Is hafte ke 7 uploads ka plan do\" (upar wala prompt, step 3)."],
     ["**Tuesday**", "Clips record karo, Claude ko titles aur descriptions final karne do."],
     ["**Tuesday**", "Schedule check karo, sab sahi lage tabhi \"yes\" bolo."],
     ["**Friday**", "\"Naye comments ke reply drafts do\", padh ke khud approve karo."]])]),
 ("Safety", "Safety: channel ki chaabi sambhal ke", [
   ("p", "Aap ek third-party app ko apne channel ka access de rahe ho, to ye 4 cheezein zaroor karo."),
   ("list", ["**Permissions padho:** Allow se pehle dekho app kya kar sakta hai (videos edit, comments post, upload).",
             "**Approval rule:** prompt mein likha hai ki bina \"yes\" kuch publish na ho. Ise kabhi mat hatao.",
             "**Auto-replies pe nazar:** AI replies kabhi galat ya robotic lag sakte hain; post hone se pehle padho.",
             "**Access hatana ho to:** Google account → Security → \"Third-party apps with account access\" se Uplika remove karo. Claude mein bhi Customize → Connectors se disconnect karo."])]),
])

N = {"REPO": 1, "FREE": 2, "SEED": 3, "LINK": 5, "YOUTUBE": 6}
for k, html in G.items():
    open(os.path.join(OUT, f"{k}.html"), "w", encoding="utf-8").write(html)
    print(k, "written,", "cards updated:", update_index(k, N[k]))
