"""Guides rebuilt from the claude.ai artifact PDFs (AUTO/OOTTO, EDIT, GROW, SKILL, CLAUDE video editing). Run from repo root."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from guidepage import page
OUT = "freebies/guides"
CONNECT_NOTE = ("tip", "Custom connectors har Claude plan pe available nahi hote; option na dikhe to apna plan check karo.")

G = {}
G["AUTO"] = page("AUTO", "Claude + Instagram:", "setup + prompts",
 "Ootto connector se Claude aapki profile, top posts aur reach padh ke batata hai kya chal raha hai, competitors dekhta hai, aur mahine bhar ka content plan banata hai.", [
 ("Kya milega", "Claude aapke Instagram ke saath", [
   ("p", "Claude ke built-in Connectors mein Instagram nahi hai, isliye ye setup ek third-party connector (**Ootto**) se hota hai. Connect hone ke baad Claude aapki profile, top posts aur reach padh ke batata hai kya chal raha hai, competitors dekhta hai, aur mahine bhar ka content plan banata hai."),
   ("warn", "Zaroori: zyaadatar Instagram tools ke liye **Professional account** (Creator ya Business) chahiye. Ootto ki pricing aur terms use karne se pehle khud check karo.")]),
 ("Setup", "Setup (2 minute)", [
   ("ol", ["Instagram app mein check karo ki account Professional hai (**Settings → Account type and tools**).", "claude.ai kholo, **Customize** pe jao, phir **Connectors** tab.",
           "**Add custom connector** dabao.", "Name: **Ootto**. Remote MCP server URL: Ootto ki official website se link copy karke paste karo.",
           "**Add**, phir **Connect** dabao, Instagram se login karo.", "Permissions padho, phir **Allow**. Connectors list mein \"Connected\" dikhe to done."]),
   CONNECT_NOTE]),
 ("Prompts", "4 ready-made prompts", [
   ("p", "Pehle confirm karo ki Claude bole ki wo Ootto se connected hai. Phir ye prompts ek-ek karke chalao; brackets mein apni details bharo."),
   ("prompt", "1 · Reach audit", "Meri Instagram profile ke last 30 posts aur reels padho. Reach, saves, shares aur watch time ke hisaab se top 5 aur bottom 5 nikalo. Batao top posts mein kya common hai (hook, topic, length, posting time) aur reach kahan gir rahi hai. Answer table mein do."),
   ("prompt", "2 · Competitor research", "Mere niche [topic] mein 5 aise pages dhoondo jo mujhse thode bade hain. Har ek ke last 10 reels ke hooks, formats aur posting frequency compare karo. 3 cheezein batao jo wo kar rahe hain aur main nahi."),
   ("prompt", "3 · Monthly content calendar", "Upar ke audit aur competitor research ke basis pe agle 30 din ka content calendar banao. Har din: format (reel/carousel/story), topic, pehle 3 second ka hook, caption ka idea, aur comment keyword. Table mein do. Kuch bhi post mat karna."),
   ("prompt", "4 · DM reply drafts", "Mere pending DMs dekho aur unke reply drafts likho, mere tone mein (friendly, Hinglish, short). Sales ya personal sawaalon pe draft mat likho, unhe mere liye mark karo. Kuch bhi send mat karna; main padh ke approve karunga.")]),
 ("Safety", "Safety: account ki chaabi", [
   ("p", "Aap ek third-party app ko apne Instagram ka access de rahe ho, to ye rules follow karo."),
   ("list", ["**Permissions padho:** Allow se pehle dekho app kya kar sakta hai (posts padhna, DMs bhejna, comments).",
             "**Approval pehle:** prompts mein likha hai \"send/post mat karna\". Auto-send kabhi on mat karo jab tak replies khud check na kar lo.",
             "**Robotic DMs = unfollow:** same copy-paste reply sabko mat bhejo; short, personal aur honest raho.",
             "**Spam rules:** bahut zyada automated DMs ya comments se Instagram account restrict kar sakta hai. Dheere chalo.",
             "**Access hatana ho to:** Instagram mein Settings → Website permissions / Apps and websites se Ootto remove karo. Claude mein Customize → Connectors se disconnect karo."])]),
])

EDIT_SKILL = """name: video-editing
description: Meri raw clips ko short-form vertical video (Reels/Shorts) mein edit karo, mere style mein.

## Input
- Clips (mp4/mov), images (png/jpg), optional voiceover (mp3/wav)
- STYLE.md (agar ho) — reference videos se seekhe gaye style rules. Ye rules sabse upar.

## Edit rules
1. Har pause > 0.3 sec aur filler words (umm, aaa, matlab, like) cut karo.
2. Pehle 2 second mein sabse strong line ya visual rakho (hook).
3. Captions: bold, 2-3 words at a time, centre se thoda neeche, safe area ke andar. Keyword ek accent colour mein.
4. Har important line pe 110% punch-in zoom, 0.2 sec ease.
5. Har 2-3 sec mein visual change: cut, zoom, B-roll ya image.
6. Background music voice se 18-20 dB neeche; voice hamesha clear.
7. Loudness approx -14 LUFS.
8. End pe 1.5 sec CTA card (jo text main bataun).

## Output
- 1080x1920, 30 fps, H.264 mp4, file name: final_cut.mp4
- Saath mein ek short edit log: kya cut kiya, kitne captions, total length.

## Process
- Pehle plan batao (cut list + timeline), meri "ok" ke baad render karo.
- Kuch possible na ho (jaise koi effect), to saaf bata do aur closest option do."""
G["EDIT"] = page("EDIT", "ChatGPT video editing:", "skill + setup",
 "ChatGPT aapki raw clips aur images se ek edited short video banane ki koshish karta hai: pauses aur filler words cut, captions, zooms aur 9:16 export.", [
 ("Pehle padho", "Kya hoga, kya nahi", [
   ("p", "Is setup se ChatGPT aapki raw clips aur images se ek edited short video banane ki koshish karta hai: pauses aur filler words cut, captions, zooms aur 9:16 export. Iske liye ChatGPT ka wo plan chahiye jisme **file upload aur code/data analysis tool** chalta ho."),
   ("warn", "Sach: ChatGPT ka editing simple cuts, captions aur trims ke liye achha hai; heavy motion graphics ya perfect sync ki guarantee nahi hai. Pehle ek chhoti clip (30–60 sec) se test karo, phir lambi videos do.")]),
 ("Skill", "Video editing skill (SKILL.md)", [
   ("p", "Neeche ka poora text copy karke ek file banao **SKILL.md**. Har baar video edit karwate waqt ise upload karo, ya ChatGPT Project ke instructions mein paste kar do."),
   ("code", "SKILL.md", EDIT_SKILL)]),
 ("7 steps", "7 steps", [
   ("ol", ["**ChatGPT kholo.** Best hai ek naya Project banao (jaise \"Reels Editing\"), taaki style aur skill har chat mein yaad rahe.",
           "**References daalo.** 2–3 pasandida videos ke links do aur neeche wala STYLE prompt bhejo.",
           "**Skill add karo.** Upar wala SKILL.md file upload karo, ya Project instructions mein paste karo.",
           "**Footage taiyaar karo.** Clips (sabse achhe takes), images, aur agar ho to voiceover. AI visuals chahiye to kisi image/video tool se bana ke saath rakho.",
           "**Sab upload karo.** Clips, images, STYLE.md aur SKILL.md ek hi message mein.",
           "**Prompt bhejo** (neeche wala edit prompt).",
           "**Wait karo aur check karo.** Time file size par depend karta hai. Edit log padho, video dekho, phir changes maango."]),
   ("prompt", "Step 2 · STYLE prompt", "In videos ka editing style study karo: [links]. Cut speed, caption style, zooms, transitions, music level aur pacing ke rules nikalo, aur unhe STYLE.md file mein do jo main save kar saku."),
   ("tip", "Agar ChatGPT Instagram links na khol paaye, to videos download karke upload karo, ya ek connector (jaise Ootto) try karo. STYLE.md download karke rakh lo; ye sirf pehli baar karna hai."),
   ("prompt", "Step 6 · Edit prompt", "Meri video-editing skill aur STYLE.md follow karke in clips ko ek 30-45 second ki reel mein edit karo. Hook: [pehli line]. CTA card: \"Comment EDIT\". Pehle cut list dikhao, phir render karo.")]),
 ("Changes", "Changes maangne ke prompts", [
   ("list", ["\"Intro 2 second chhota karo, pehli line seedha shuru ho.\"", "\"Captions bade karo aur keyword green mein.\"",
             "\"Beech ke 5 second slow lag rahe hain, wahan B-roll daalo.\"", "\"Music thoda kam karo, voice aur clear.\"", "\"Same edit 1:1 square mein bhi export karo.\""]),
   ("tip", "**Ek baar mein ek change maango;** 3–4 changes ek saath dene se galti badhti hai. Achha result mile to bolo \"ye style STYLE.md mein update kar do\", agli video aur better aayegi. Final export khud phone pe dekh ke check karo: captions safe area mein hain, audio sync sahi hai.")]),
])

G["GROW"] = page("GROW", "Claude Instagram growth:", "walkthrough + prompts",
 "Claude ko aapke Instagram se jod ke research, planning aur content ek hi jagah karwana: outliers, 30-day dashboard aur roz ka content.", [
 ("Pehle padho", "Ye walkthrough kya hai", [
   ("p", "Maine Claude ke saath content bana ke apna Instagram **0 se 6,396 followers** tak pahunchaya. Ye walkthrough agla step hai: Claude ko aapke Instagram se jod ke research, planning aur content ek hi jagah karwana."),
   ("warn", "Sach: growth kisi tool se guarantee nahi hoti. Claude plan aur content mein help karta hai; consistency, achhe hooks aur aapka review hi asli farak laate hain. Ootto ek third-party connector hai, iski pricing aur features use karne se pehle khud check karo.")]),
 ("Step 1", "Ek baar connect karo", [
   ("ol", ["Instagram account **Professional** (Creator ya Business) hona chahiye.", "claude.ai kholo, **Customize** pe jao, phir **Connectors**.", "**Add custom connector** dabao.",
           "Name: **Ootto**. Remote MCP server URL: Ootto ki official website se copy karo (reel mein `mcp.ootto.ai/mcp` dikhaya tha; official site se confirm karo).",
           "**Connect** dabao, Instagram se login karo, permissions padh ke **Allow**.", "\"Connected\" dikhe to setup done. Ye sirf ek baar karna hai."]),
   CONNECT_NOTE]),
 ("Prompts", "Prompts (isi order mein)", [
   ("prompt", "1 · Outliers dhoondo", "Mera niche hai [topic], audience [kaun]. Mere niche ke outliers dhoondo: wo posts jo apne account ke average se 5x ya zyada chal rahe hain, pichhle 30 din mein. Har ek ka hook, format, length aur kyun chala, table mein do. Phir 5 patterns batao jo main copy kar sakta hoon."),
   ("prompt", "2 · 30-day content dashboard", "Upar ke outliers aur meri profile ke top posts ke basis pe 30 din ka content dashboard banao. Har din: format (reel/carousel/story), topic, pehle 3 second ka hook, CTA aur comment keyword. Mix rakho: 60% reels, 25% carousels, 15% stories. Table mein do."),
   ("prompt", "3 · Let's start", "Let's start. Dashboard ka Day 1 ka content banao: script (Hinglish, 40-50 sec), on-screen text, caption aur hashtags. Post karne se pehle mujhe dikhao."),
   ("prompt", "4 · Apni footage ke saath", "Use these: [clips upload]. Day 2 ka script inhi clips ke hisaab se adjust karo aur batao kaun sa clip kahan aayega.")]),
 ("Routine", "Roz 15 minute", [
   ("table", ["Kaam", "Time"], [["Aaj ka content kholo, script aur caption padho", "5 min"], ["Hook strong hai? Nahi to Claude se 3 naye hooks maango", "3 min"],
                                ["Post ya schedule karo", "2 min"], ["Kal ke post ke comments dekho, achhe sawaalon ka khud reply karo", "5 min"]]),
   ("tip", "Hafte mein ek baar: \"is hafte kya chala, kya nahi\" Claude se poochho aur dashboard update karwao.")]),
 ("Safety", "Safety", [
   ("list", ["Kuch bhi bina aapke review ke post ya DM na ho; prompts mein **\"post mat karna\"** likho.",
             "Permissions dhyan se padho; access hatana ho to Instagram Settings mein Apps and websites se aur Claude mein Connectors se disconnect karo.",
             "Bahut zyada automated DMs ya comments se Instagram account restrict kar sakta hai."])]),
])

SKILL_MD = """---
name: instagram-agent
description: Instagram content manager. Use when the user asks to write posts or reels, reply to comments, audit or optimise their profile, plan a week of content, analyse competitors, or find what is going viral in their niche and turn it into scripts.
---
# Instagram Agent
Pehle user se (ek baar) ye poochho aur yaad rakho: niche, audience, language (Hinglish/Hindi/English), tone, goal (followers / leads / sales), posting frequency.

## Jobs
1. Post writer: reel script (hook 0-3s, 3-5 beats, CTA), carousel (8-10 slides), caption + 5-10 hashtags.
2. Hook lab: har idea ke 5 hooks; curiosity, number, contrarian, result, mistake angles.
3. Comment replies: user ke pasted comments ke liye short, warm replies; sawaal ka seedha jawab; spam/abuse ko "skip" mark karo.
4. DM drafts: comment-keyword DMs aur FAQ replies (send khud mat karo, sirf draft).
5. Profile audit: name field keywords, bio (kaun, kya value, CTA), link, highlights, pinned posts. Score /10 + exact rewrites.
6. Weekly planner: 7 din, format mix (reels/carousels/stories), topic, hook, CTA, best time.
7. Monthly calendar: 30 din, content pillars ke hisaab se.
8. Competitor scan: diye gaye accounts ke top posts ka hook, format, length, posting pattern.
9. VIRALITY (most important): niche ke outlier reels (account average se 3-5x) lo; har ek ka WHY nikalo: hook type, format, topic angle, length, pacing, CTA. Phir user ke liye 3 winning scripts banao jo wahi patterns use karein but original hon.
10. Repurpose: ek reel ko carousel, story aur thread mein badlo.
11. Weekly review: user ke insights (reach, saves, shares, follows) padh ke batao kya chala, kya nahi, agle hafte kya badlein.

## Rules
- Kabhi kisi ka content copy mat karo; patterns lo, words apne.
- Har output table ya numbered list mein.
- Kuch bhi post/send karne se pehle user ka "yes" lo.
- Unverified claims (income, results) mat likho."""
G["SKILL"] = page("SKILL", "Instagram agent skill", "for Claude",
 "Ek Claude skill jo Claude ko aapka Instagram content manager bana deti hai: posts, comment replies, profile audit, weekly plan, aur virality analysis.", [
 ("Pehle padho", "Ye skill kya karti hai", [
   ("p", "Ye ek Claude skill hai jo Claude ko aapka Instagram content manager bana deti hai: posts likhna, comment replies draft karna, profile audit, weekly plan, aur sabse important, **virality analysis** jo niche ki best reels se winning scripts banata hai."),
   ("warn", "Sach: skill akele Instagram pe post ya reply nahi karti; wo drafts aur plans banati hai jo aap khud post karte ho. Seedha Instagram data padhne ya post karne ke liye ek connector chahiye (jaise Ootto). Bina connector ke, aap reels ke links, screenshots ya insights paste karke bhi isse use kar sakte ho.")]),
 ("SKILL.md", "SKILL.md (copy karo)", [
   ("p", "Neeche ka text ek folder **instagram-agent** mein **SKILL.md** naam se save karo."),
   ("code", "instagram-agent/SKILL.md", SKILL_MD)]),
 ("Install", "Claude mein install kaise karein", [
   ("ol", ["Upar ka text copy karke ek folder **instagram-agent** banao, usme **SKILL.md** file save karo.", "Folder ko zip karo (**instagram-agent.zip**).",
           "claude.ai kholo, **Customize** (ya Settings) mein **Skills** section pe jao.", "**Upload skill / Add skill** dabao aur zip upload karo. Skill ko on karo.",
           "Naya chat kholo aur likho: \"instagram-agent skill use karke mera profile audit karo\". Claude pehle aapka niche aur audience poochega."]),
   ("tip", "Skills ka option aur menu ka naam Claude ke plan aur version ke hisaab se thoda alag ho sakta hai. Skills option na mile to SKILL.md ka text ek **Project ke instructions** mein paste karke bhi same kaam ho jaata hai.")]),
 ("Use", "Kaise use karein (example commands)", [
   ("table", ["Job", "Claude ko bolo"], [
     ["**Virality**", "\"Ye 5 viral reels hain [links/screenshots]. Inka WHY nikalo aur mere liye 3 winning scripts banao.\""],
     ["**Post writer**", "\"Kal ke liye ek 45 sec reel script do: topic [X], Hinglish.\""],
     ["**Hook lab**", "\"Is idea ke 5 hooks do: [idea].\""],
     ["**Comment replies**", "\"Ye comments hain [paste]. Har ek ka short reply draft karo.\""],
     ["**Profile audit**", "\"Mera bio, name aur highlights ye hain [paste]. Audit karo aur rewrite do.\""],
     ["**Weekly plan**", "\"Agle 7 din ka content plan do.\""],
     ["**Weekly review**", "\"Is hafte ke insights ye hain [paste]. Kya chala, kya badlein?\""]]),
   ("tip", "**Virality job se shuru karo,** wahi sabse zyada value deta hai. Har hafte 15 minute review aur ek naya virality round.")]),
])

BOOK = """# MY BRAND GUIDANCE BOOK

## Brand
- Channel: [@handle], niche: [topic], audience: [kaun]
- Language: [Hinglish / Hindi / English], tone: [friendly / pro / funny]

## Look
- Colours: main [#hex], accent [#hex], background [#hex]
- Fonts: headline [font], captions [font, bold]
- Logo/handle: [kahan aur kab dikhe]

## Pacing
- Pehle 1 second mein hook (strongest line ya visual)
- Har line / har 1.5-2 sec pe cut
- Har pause > 0.3 sec aur filler words hatao
- Total length: [30-45 sec]

## Captions
- 2-3 words at a time, bold, centre se thoda neeche
- Keyword [accent colour] mein
- Safe area: upar-neeche 15% khaali

## Motion
- Key lines pe 110% punch-in zoom
- B-roll / image har claim pe
- Transitions: simple cut ya quick whip, koi heavy effect nahi

## Audio
- Music voice se ~18 dB neeche, voice clear
- Loudness approx -14 LUFS

## End
- CTA card 1.5 sec: "Comment [KEYWORD]" + follow [@handle]

## Export
- 1080x1920, 30 fps, mp4"""
VSKILL = """---
name: video-editing
description: Edit raw clips into a short vertical reel following the user's GUIDANCE_BOOK.md. Use when the user uploads footage and asks to edit, cut, caption or export a video.
---
# Video Editing
1. GUIDANCE_BOOK.md padho; uske rules sabse upar.
2. Clips ka audio transcribe karo; pauses > 0.3s aur filler words ki list banao.
3. Plan dikhao (cut list + timeline + captions) aur user ka "ok" lo.
4. Edit karo: cuts, captions (book ke style mein), punch-in zooms, B-roll/images, music duck.
5. Export: 1080x1920, 30 fps, mp4 (final_cut.mp4) + short edit log.
6. Revision: sirf wahi badlo jo user bole; baaki same rakho.

Rules: kuch possible na ho to saaf bolo aur closest option do. Kabhi bina bataye content mat hatao."""
G["CLAUDE_VIDEO"] = page("CLAUDE", "Video editing with Claude:", "guidance book + skill",
 "Claude video \"edit\" karta hai code aur tools ke through: clips cut, captions aur export. Ek Guidance Book aur ek skill se har reel aapke style mein.", [
 ("Pehle padho", "Claude video kaise edit karta hai", [
   ("p", "Claude video \"edit\" karta hai code aur tools ke through: wo aapki clips ko cut karta hai, captions lagata hai aur export karta hai. Ye best chalta hai Claude ke wo setups mein jahan **file upload aur code chalane** ki facility ho (jaise analysis tool, ya Claude Code)."),
   ("warn", "Sach: simple cuts, captions, zooms aur 9:16 export ke liye achha hai; heavy motion graphics ki guarantee nahi. Time file size aur model pe depend karta hai. Pehle 30–60 sec ki chhoti clip se test karo.")]),
 ("Guidance Book", "Guidance Book template", [
   ("p", "Brackets bharo aur **GUIDANCE_BOOK.md** naam se save karo. Ye ek baar banana hai; har video ke saath upload karo."),
   ("code", "GUIDANCE_BOOK.md", BOOK)]),
 ("Skill", "Video editing skill (SKILL.md)", [
   ("p", "Folder **video-editing** mein **SKILL.md** naam se save karo, zip karke Claude ke Skills mein upload karo (ya Project instructions mein paste karo)."),
   ("code", "video-editing/SKILL.md", VSKILL)]),
 ("7 steps", "7 steps + prompts", [
   ("ol", ["Claude kholo (best: ek Project banao **\"Reels Editing\"**).", "Guidance book bharo aur upload karo.", "Skill add karo (upar wala SKILL.md).",
           "Footage + materials ready: best takes, pictures, music/sound.", "Sab ek message mein upload karo.", "Neeche wala prompt bhejo.", "Wait karo, edit log padho, video check karo."]),
   ("prompt", "Step 6 · Prompt", "Meri GUIDANCE_BOOK.md aur video-editing skill follow karke in clips se 30-45 sec ki reel banao. Hook: [pehli line]. CTA: \"Comment [KEYWORD]\". Pehle plan dikhao, phir edit karo.")]),
 ("Revisions", "Revision prompts", [
   ("list", ["\"Intro 2 second ka karo.\"", "\"Captions bade aur keyword accent colour mein.\"", "\"Beech ka slow part cut karo.\"", "\"Music thoda kam.\""])]),
])

for name, html in G.items():
    open(os.path.join(OUT, f"{name}.html"), "w", encoding="utf-8").write(html)
# point the /free cards at the new pages (by card number; CLAUDE and AUTO/OOTTO need care)
TARGET = {7: "AUTO", 8: "AUTO", 9: "EDIT", 10: "GROW", 11: "SKILL", 12: "CLAUDE_VIDEO"}
p = "freebies/index.html"; s = open(p, encoding="utf-8").read()
i = s.index("const D=") + 8; j = s.index(";\n", i); d = json.loads(s[i:j])
for x in d["items"]:
    if x["n"] in TARGET:
        x["u"] = f"guides/{TARGET[x['n']]}.html"; print(x["n"], x["k"], "->", x["u"])
open(p, "w", encoding="utf-8").write(s[:i] + json.dumps(d, ensure_ascii=False) + s[j:])
