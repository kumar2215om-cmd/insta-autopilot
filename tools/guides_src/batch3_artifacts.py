"""Guides rebuilt from the claude.ai artifact PDFs (REELS, FLOP, GUIDE, CODE, INSTAGRAM). Run from repo root."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from guidepage import page
OUT = "freebies/guides"
G = {}

G["REELS"] = page("REELS", "Claude mega prompt:", "a week of reels",
 "Ye mega prompt Claude ko aapka reel producer bana deta hai: profile padhna, niche research, aur 7 reels ka poora plan.", [
 ("Pehle padho", "Mega prompt kya karta hai", [
   ("p", "Ye mega prompt Claude ko aapka reel producer bana deta hai: profile padhna, niche research, aur **7 reels ka poora plan** (hook, script, on-screen text, voiceover script, music notes). Claude ko Instagram data seedha milta hai ek connector (jaise Ootto) se; bina connector ke bhi chalega agar aap apne top posts ke links ya screenshots paste karo."),
   ("warn", "Sach: actual video render, voiceover aur auto-posting connector/tools pe depend karte hain aur verify nahi kiye gaye. Har reel post karne se pehle khud review karo.")]),
 ("Step 1", "Ek baar connect karo", [
   ("ol", ["claude.ai → **Customize** → **Connectors** → **Add custom connector**.", "Name: **Ootto**, URL: Ootto ki official site se copy karo → **Connect** → **Allow**.",
           "Ootto mein sign in → Instagram chuno (Professional account) → **Allow**.", "Connectors list mein \"Connected\" dikhe to done."])]),
 ("Mega prompt", "Mega prompt", [
   ("p", "Poora copy karke Claude mein paste karo. Pehle confirm karo ki Claude bole \"Connected to Ootto\"."),
   ("prompt", "Copy karo", "Tum mere Instagram ke reel producer ho. Mera handle: [@handle], niche: [topic], audience: [kaun], language: [Hinglish], brand colours: [hex], tone: [friendly/pro].\n\nPHASE 1 — PROFILE: Meri profile ke last 30 posts padho. Top 5 aur bottom 5 (reach, saves, shares) nikalo; top posts mein kya common hai (hook, format, length, topic) table mein do.\n\nPHASE 2 — NICHE: Mere niche mein pichhle 30 din ke outlier reels dhoondo (account average se 3x+). Har ek ka WHY: hook type, format, pacing, CTA. 5 patterns likho jo main use karun.\n\nPHASE 3 — 7 REELS: Agle 7 din ke liye 7 reels banao. Har reel ke liye:\n- Hook (pehle 2 sec, 1 line)\n- Script (30-45 sec, Hinglish, short lines)\n- On-screen text (har beat ke liye 2-5 words)\n- Motion/visual notes (har beat kya dikhe)\n- Voiceover script (ElevenLabs-ready: numbers Hindi words mein, acronyms spaced)\n- Music mood + BPM\n- Caption + 8 hashtags + comment keyword\nSab mere brand colours aur tone mein.\n\nPHASE 4 — REVIEW: Ek table do: Day, Topic, Hook, Format, Keyword. Phir ruk jao aur meri approval lo.\n\nRules: kisi ka content copy mat karo (patterns lo, words apne); kuch bhi post ya schedule mat karna bina mere \"yes\" ke; unverified claims mat likho.")]),
 ("Uske baad", "Follow-up prompts", [
   ("list", ["\"Day 1 ki reel final karo; hook ke 3 aur options do.\"", "\"Ye meri footage hai [upload]. Day 2 ka script inhi clips ke hisaab se adjust karo.\"",
             "\"Is hafte ke results ye hain [insights]. Agle hafte ka plan update karo.\""])]),
 ("Checklist", "Har reel post se pehle check karo", [
   ("list", ["Hook pehle 2 second mein clear hai", "Koi claim galat ya unverified nahi", "Captions safe area mein, spelling sahi", "Comment keyword aur DM doc ready", "Approve karke hi post / schedule"])]),
])

G["FLOP"] = page("FLOP", "Claude se pucho:", "reel flop kyun hui?",
 "Claude ko apne Instagram se connect karo, phir pucho \"meri last reel flop kyun hui?\". Wo retention batata hai, fix suggest karta hai, aur agli script likh deta hai.", [
 ("Ye kya hai", "Ye doc kya hai?", [
   ("p", "Tumne reel pe **FLOP** comment kiya tha, to ye raha poora setup. 🙌 Claude ko apne Instagram se connect karo, phir pucho \"meri last reel flop kyun hui?\". Claude tumhari asli reels padhta hai, retention batata hai (kitne log pehle 5 sec mein chale gaye), fix suggest karta hai, aur agli script bhi likh deta hai."),
   ("warn", "**Honest note:** Ye connection **Ootto** naam ke third-party connector se hota hai, Claude ka official Instagram feature nahi hai. Connect karne se pehle permissions padho. Reel mein dikhaya 31% sirf ek example hai, tumhara number alag hoga. Koi bhi reel post karne se pehle khud review karo.")]),
 ("Step 1", "Connector add karo (sirf ek baar)", [
   ("ol", ["claude.ai kholo (desktop/browser pe best).", "**Settings → Connectors** mein jao.", "**Add custom connector** pe click karo.", "Name mein likho: **Ootto**",
           "Remote MCP server URL mein Ootto ka MCP link paste karo. Ye link Ootto ki website/dashboard pe milta hai. Hamesha official site se hi copy karo, kisi random DM ya comment se nahi.",
           "**Add** dabao → **Connect** → Ootto mein sign in karo → apna Instagram account choose karo → **Allow**.", "Connectors list mein **Ootto ✓ Connected** dikhna chahiye. Bas, setup done! ✅"]),
   ("tip", "Custom connectors kuch plans pe hi available hote hain. Option nahi dikh raha to apna Claude plan aur settings check karo.")]),
 ("Step 2", "Pucho \"flop kyun hui?\"", [
   ("p", "Naya chat kholo, check karo ki Ootto connected hai, aur ye prompt copy-paste karo:"),
   ("prompt", "Copy karo", "Ootto connector se meri Instagram profile ki last 12 reels padho.\nMeri sabse latest reel ka analysis karo aur batao:\n1. Retention: pehle 3 aur 5 second mein kitne % log chale gaye?\n2. Flop ki top 3 wajah (hook, pacing, payoff, caption, topic).\n3. Meri best-performing reel se compare karo: usme kya alag tha?\n4. Har problem ka ek clear fix, simple Hinglish mein.\nJo data connector se nahi mil raha, wo saaf batao. Guess mat karo."),
   ("list", ["Retention ka breakdown (jaise: \"31% log pehle 5 sec mein gaye\")", "Flop ki wajah, tumhari hi reels ke data se", "Ek seedha fix, jaise \"payoff ko frame 0 pe dikhao\""])]),
 ("Uske baad", "Follow-up prompts", [
   ("prompt", "Agli script likhwao", "Is analysis ke basis pe meri agli reel ki script likho.\nHook pehle 1 second mein, payoff frame 0 pe dikhe.\nFormat: timestamp + line (0.0s, 1.4s, 4s...), 30-40 sec, Hinglish."),
   ("prompt", "Reel banwao (Ootto)", "Is script se Ootto ke through reel bana do. Mere pichhle reels jaisa style rakho."),
   ("prompt", "Apni footage edit karwao", "Ye meri raw footage hai. Dead air aur lambe pauses kaat do, aur hook ko shuru mein laao."),
   ("tip", "**Done-for-you mode:** Ootto mein ye mode on karne pe wo tumhari reels se seekhta hai, trending research karta hai, idea banata hai, aur finished reels tumhe bhejta hai. Post tum khud karo, har reel pehle dekh ke. Ye Ootto ka feature hai: kya available hai aur kitne ka hai, unki site pe check karo.")]),
 ("Checklist", "Checklist + kuch kaam nahi kar raha?", [
   ("list", ["Ootto connector add kiya, aur list mein \"Connected\" dikh raha hai", "Instagram account Allow kiya (sahi account choose kiya)",
             "Step 2 wala prompt chalaya, retention + flop ki wajah mili", "Agli script likhwayi", "Har reel post karne se pehle khud dekhi"]),
   ("table", ["Problem", "Fix"], [
     ["\"Add custom connector\" nahi dikh raha", "Apna Claude plan check karo, ye har plan pe nahi hota."],
     ["Claude bole \"I can't see your Instagram\"", "Naye chat mein check karo ki Ootto connector on hai."],
     ["Retention data nahi aa raha", "Instagram professional (creator/business) account chahiye ho sakta hai. Ootto ke docs dekho."]])]),
])

G["GUIDE"] = page("GUIDE", "Claude se reels kaise banwayein", "(4 steps)",
 "Mere page ki reels isi tarah banti hain: 4 steps, idea se leads tak. Study → Write → Build → Leads.", [
 ("Ye guide kya hai", "4 steps, idea se leads tak", [
   ("p", "Tumne **GUIDE** comment kiya tha, to ye raha poora process. 🙌 Mere page ki reels isi tarah banti hain:"),
   ("ol", ["**Study:** viral reel ko frame by frame samjho", "**Write:** original hook + script", "**Build:** poori reel (music, captions, animations, voiceover)", "**Leads:** comment karne walon ko auto-DM"]),
   ("warn", "**Honest note:** Voiceover ElevenLabs se banta hai; Claude script likhta hai aur voice ko reel mein jodta hai. Auto-DM ke liye ek alag tool chahiye (jaise ManyChat); Claude akela Instagram pe DM nahi bhejta. Viral reel ko copy mat karo: uska structure seekho (hook, pacing, beats), content apna banao.")]),
 ("Kya chahiye", "Kya chahiye?", [
   ("table", ["Kaam", "Tool", "Note"], [
     ["Study + script", "Claude (claude.ai)", "Reel ka video/screenshots + transcript do"],
     ["Reel build", "Claude Code • Remotion", "Remotion = code se video banane wala free framework"],
     ["Voiceover", "ElevenLabs", "Hinglish voice, MP3 download"],
     ["Auto-DM", "ManyChat (ya koi bhi Instagram auto-DM tool)", "Comment keyword pe DM bhejta hai"]]),
   ("tip", "Claude Code terminal mein chalta hai. Pehli baar setup karne mein 15-20 min lagte hain, uske baad har reel fast banti hai.")]),
 ("Step 1", "Study: viral reel ko samjho", [
   ("p", "Viral reel download karo (ya uske screenshots, har 0.5 sec pe ek) aur Claude ko do, saath mein ye prompt:"),
   ("prompt", "Study prompt", "Ye ek viral reel hai. Isko frame by frame study karo aur batao:\n1. Hook: pehle 1-2 second mein kya dikhta aur bola jaata hai?\n2. Beats: har scene ka time, on-screen text, visual, animation.\n3. Pacing: kitne second pe cut hota hai, kab SFX/zoom aata hai.\n4. CTA: end mein kya keyword aur kya offer hai.\n5. Ye reel viral kyun hui, 3 points mein.")]),
 ("Step 2", "Write: original hook + script", [
   ("prompt", "Script prompt", "Is structure ko use karke MERE niche ke liye ek ORIGINAL reel script likho.\nNiche: [apna niche]  |  Language: Hinglish  |  Length: 30-45 sec\nSame beats aur order rakho, lekin content, examples aur claims mere apne ho.\nHook pehle 1 second mein. Har line ke saath on-screen text bhi do.\nEnd mein CTA: Comment \"[KEYWORD]\".\nKoi bhi claim jo verify nahi ho sakta, use mark karo.")]),
 ("Step 3", "Build: poori reel", [
   ("ol", ["Script ko **ElevenLabs** mein paste karo, Hinglish voice choose karo, aur MP3 download karo.", "Ek folder banao, usme MP3 daalo, aur **Claude Code** kholo.", "Neeche wala prompt do.",
           "Stills check karo, jo cluttered lage use theek karwao, phir render karwao.", "Final MP3/MP4 ki loudness Instagram ke liye **-14 LUFS** rakho, aur lambe pauses kaat do (reel 50 sec se kam)."]),
   ("prompt", "Claude Code prompt", "Remotion project banao: 1080x1920, 30fps.\nvo.mp3 mera voiceover hai. Har line ka timing nikaalo aur uske hisaab se scenes banao:\n- Har beat ka headline upar (bada, clean), ek main visual beech mein\n- Karaoke caption pill neeche (max 5 words)\n- Spring pop-ins, 3D whip transitions, har click/pop pe SFX\n- Halka lo-fi music voice ke neeche\nMera brand: cream background, cerulean + pink accents.\nRender se pehle key frames ki stills dikhao, taaki main check kar sakun.")]),
 ("Step 4", "Leads: comment → auto DM", [
   ("ol", ["**ManyChat** (ya koi Instagram auto-DM tool) ko apne Instagram professional account se connect karo.",
           "Ek automation banao: trigger = comment mein keyword (jaise GUIDE), aur action = DM mein tumhara doc/link.",
           "Reel ke caption aur end-screen pe wahi keyword likho.", "DM ka message Claude se likhwao: chhota, friendly, aur ek clear link."])]),
 ("Checklist", "Checklist", [
   ("list", ["Viral reel study ki (hook, beats, pacing, CTA)", "Original script likhi, copy nahi ki", "ElevenLabs voiceover ready hai",
             "Claude Code + Remotion se reel build ki, stills check kiye", "Reel 50 sec se kam aur -14 LUFS par hai", "Keyword auto-DM test kiya (khud comment karke)"])]),
])

G["CODE"] = page("CODE", "Claude skill se unlimited reels", "(no credits)",
 "Mere page ki reels kisi AI video model se nahi bantin. Ye code se bantin hain: Claude Code likhta hai, Remotion MP4 render karta hai. Per-reel cost ₹0.", [
 ("Ye kya hai", "Code se reels, credits ke bina", [
   ("p", "Tumne **CODE** comment kiya tha, to ye rahi saari details. 🙌 Mere page ki reels kisi AI video model se nahi bantin. Ye code se bantin hain, ek free framework **Remotion** ke saath. Claude Code wo code likhta hai: scenes, animations, captions, SFX. Phir Remotion usse MP4 render karta hai."),
   ("p", "**No credits kyun?** AI video tools har video ke credits kaatte hain. Yahan video tumhare computer pe render hoti hai, isliye per-reel cost ₹0 hai aur style bhi koi bhi ho sakta hai."),
   ("warn", "**Honest catches:** Claude Code ke liye Claude ka paid plan chahiye. Remotion individuals aur chhoti teams ke liye free hai; badi companies ko company license lena padta hai (remotion.dev pe check karo). Voiceover ElevenLabs (ya koi TTS) se aata hai; Remotion voice nahi banata.")]),
 ("Setup", "Setup (ek baar, ~20 min)", [
   ("ol", ["**Node.js** install karo (nodejs.org se, LTS version).", "**Claude Code** install karo. Steps Anthropic ki docs mein hain (docs.claude.com → Claude Code).",
           "Naya Remotion project banao (neeche wala command).", "Us folder mein terminal kholo aur `claude` likho. Claude Code shuru ho jayega.",
           "**Remotion skill:** Remotion ki official docs mein AI / Claude Code wala section hai. Wahan unka agent skill install karne ka command milega. Usse Claude ko Remotion ke best practices pata rehte hain, aur reels zyada clean banti hain."]),
   ("code", "Step 3 · terminal", "npx create-video@latest"),
   ("tip", "Claude Code mein \"skill\" ek instructions ka folder hota hai (SKILL.md). Tum apna khud ka skill bhi bana sakte ho: apna brand, colors, fonts aur caption style likh do, aur har reel usi style mein banegi.")]),
 ("Pehli reel", "Pehli reel: copy-paste prompt", [
   ("p", "Apna voiceover `public/vo.mp3` mein daalo, phir Claude Code ko ye do:"),
   ("prompt", "Copy karo", "Is Remotion project mein ek Instagram reel banao: 1080x1920, 30fps.\npublic/vo.mp3 mera voiceover hai. Pehle iska transcript aur har line ka timing nikaalo.\nPhir har line ke liye ek scene banao:\n- Upar bada headline (2-5 words), payoff word alag color mein\n- Beech mein ek hi visual (window card, chart, ya icons)\n- Neeche karaoke caption pill (max 5 words, bole gaye words dark)\n- Spring pop-ins, 3D whip transitions, har pop/click pe chhota SFX\n- Halka background music, voice ke neeche\nStyle: [cream bg + blue/pink accents]  (ya jo style chahiye)\nRender se pehle 12 key frames ki stills dikhao."),
   ("p", "**Style ideas** (prompt mein `Style:` badal do):"),
   ("list", ["Cream + serif headlines (clean, premium)", "Dark terminal / code look (tech)", "Pixel-game (Silkscreen font, retro)", "Bold neon + glass cards"])]),
 ("Quality", "Reels bekaar na lagen: quality tips", [
   ("list", ["**Ek frame, ek idea:** headline + ek visual + caption, bas. Zyada text = clutter.", "**Hook pehle 1 second mein:** pehle frame pe hi payoff dikhao.",
             "**Stills check karo:** render se pehle frames dekho. Kuch overlap ya cut ho raha ho to Claude ko bolo theek kare.",
             "**Viral reel ka structure seekho:** kisi viral reel ke hook, beats aur CTA ko frame by frame samjho, phir apna content usi structure mein daalo. Copy nahi karna.",
             "**Sound:** har pop/transition pe SFX + halka music. Final audio -14 LUFS rakho.", "**Lambai:** 30-50 sec. Pauses kaat do.",
             "**Sach bolo:** jo numbers ya claims verify nahi hote, wo mat daalo."])]),
 ("Checklist", "Checklist", [
   ("list", ["Node.js + Claude Code install kiya", "`npx create-video@latest` se Remotion project banaya", "Remotion ka agent skill add kiya (docs se)", "Apna brand style skill / prompt mein likha",
             "Voiceover `public/vo.mp3` mein daala", "Stills check kiye, phir render kiya", "Reel 50 sec se kam aur -14 LUFS par hai"])]),
])

G["INSTAGRAM"] = page("INSTAGRAM", "Claude Content Skills ka", "poora setup",
 "Ek free GitHub repo jisme 50+ Claude skills hain: hooks, scripts, carousels, captions, comment replies, content calendar aur content research.", [
 ("Ye kya hai", "Claude Content Skills kya hai", [
   ("p", "Tumne **INSTAGRAM** comment kiya tha, to ye raha poora setup. 🙌 Claude Content Skills ek free GitHub repo hai: [github.com/Ootto-AI/claude-content-skills](https://github.com/Ootto-AI/claude-content-skills). Isme 50+ Claude skills hain (abhi 54 folders), aur har skill ek kaam karti hai: hooks, scripts, carousels, captions, comment replies, content calendar aur content research."),
   ("warn", "**Honest note:** Repo Ootto ne banaya hai, MIT license, aur bilkul free hai. README mein unke paid autopilot ka promotion bhi hai; skills use karne ke liye wo zaroori nahi. Ye **Claude Code** mein chalti hain (normal claude.ai chat mein link paste karne se install nahi hoti). Skills text/plan banati hain; voiceover, video render aur auto-DM ke liye alag tools lagte hain (ElevenLabs, Remotion/CapCut, ManyChat).")]),
 ("Install", "Install (2 minute)", [
   ("p", "**Option A: Claude Code plugin (recommended).** Claude Code kholo aur ye 2 commands ek-ek karke paste karo:"),
   ("code", "Claude Code", "/plugin marketplace add Ootto-AI/claude-content-skills\n/plugin install claude-content-skills@ootto-content-skills"),
   ("p", "**Option B: Manual (macOS / Linux terminal):**"),
   ("code", "Terminal", "git clone --depth 1 https://github.com/Ootto-AI/claude-content-skills.git\nbash claude-content-skills/install.sh"),
   ("p", "Dono tarike skills ko `~/.claude/skills/` mein daal dete hain. Claude Code restart karo, aur skills ready hain."),
   ("tip", "**Option C: Claude Code nahi hai?** Har skill ek plain prompt hai. GitHub pe skill ki SKILL.md file kholo, prompt copy karo, aur claude.ai mein apne idea ke saath paste kar do.")]),
 ("Skills", "Kaunsi skill kya karti hai", [
   ("table", ["Skill", "Kaam", "Kab use karo"], [
     ["`/content-research`", "Niche/creator ki outlier reels dhoondh ke hook, format aur retention pattern todta hai", "\"Kya post karun?\" wale din"],
     ["`/reel-analyzer`", "Kisi bhi viral reel ka frame-by-frame breakdown", "Koi reel achhi lage tab"],
     ["`/viral-hook-writer`", "10 ranked hooks (pehle 1-3 sec)", "Har reel se pehle"],
     ["`/reel-scripter`", "30-45 sec ki original script, proven structure mein", "Hook final hone ke baad"],
     ["`/reel-builder`", "Beat-by-beat plan: on-screen text, visual, caption", "Shoot/edit se pehle"],
     ["`/carousel-builder`", "10-slide carousel, end mein save CTA", "Educational posts"],
     ["`/caption-and-hashtags`", "Caption + hashtags + first comment", "Post karte waqt"],
     ["`/comment-responder`", "Comments ke reply drafts + DM text", "Post ke baad"],
     ["`/content-calendar`", "2 hafte / mahine ka posting plan", "Week ki shuruaat"],
     ["`/content-factory`", "Upar wali sab skills ek order mein chalata hai", "Sab ek saath chahiye"]])]),
 ("Prompts", "Copy-paste prompts", [
   ("prompt", "Content research (sabse kamaal ki skill)", "/content-research\nMera niche: [AI tools / fitness / finance ...]\nIs niche ke 3 creators: @___ @___ @___\nInki outlier reels dhoondo (jo baaki se kaafi zyada chali),\nhar ek ka hook, structure aur title pattern todo,\nphir top 3 ideas MERI awaaz mein, MERI audience ke liye dobara likho (Hinglish)."),
   ("prompt", "Poora pipeline ek command mein", "/content-factory\nNiche: [ ]  |  Handle: @[ ]  |  CTA keyword: [ ]\nModel karne ke liye viral reel: [link]\nHook, script, beats, caption aur comment-reply plan, sab do."),
   ("prompt", "Mahine ka plan", "/content-calendar\nAgle 30 din ka reel plan banao: har din 1 reel, format aur hook ke saath.\nMere 3 content pillars: [ ], [ ], [ ]")]),
 ("Checklist", "Checklist", [
   ("list", ["Claude Code install kiya (ya Option C wala paste tarika)", "Skills install kiye, aur Claude Code restart kiya", "`/content-research` apne niche pe chalaya",
             "Top idea ka hook + script banaya", "Voice/video apne tool se banaya, aur post se pehle khud check kiya", "Comment-reply ke liye auto-DM tool set kiya (optional)"])]),
])

for name, html in G.items():
    open(os.path.join(OUT, f"{name}.html"), "w", encoding="utf-8").write(html)
TARGET = {13: "REELS", 14: "FLOP", 15: "GUIDE", 16: "CODE", 17: "INSTAGRAM"}
p = "freebies/index.html"; s = open(p, encoding="utf-8").read()
i = s.index("const D=") + 8; j = s.index(";\n", i); d = json.loads(s[i:j])
for x in d["items"]:
    if x["n"] in TARGET:
        x["u"] = f"guides/{TARGET[x['n']]}.html"; print(x["n"], x["k"], "->", x["u"])
open(p, "w", encoding="utf-8").write(s[:i] + json.dumps(d, ensure_ascii=False) + s[j:])
