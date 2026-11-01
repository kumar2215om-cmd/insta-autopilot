"""Guides rebuilt from the Notion PDFs (MONTH, VIRAL, AUTOPILOT, SETUP, GPT). Run from repo root."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from guidepage import page
OUT = "freebies/guides"
CONNECT_NOTE = ("tip", "Custom connectors har Claude plan pe available nahi hote; option na dikhe to apna plan check karo.")
G = {}

G["MONTH"] = page("MONTH", "Claude se 30 reels:", "poora setup",
 "Claude ko Ootto connector se apne Instagram se jodo, phir ek line bolo: \"Mere brand ke liye 30 reels banao.\" Pehle research, phir har reel.", [
 ("Ye kya hai", "Ye doc kya hai?", [
   ("p", "Tumne **MONTH** comment kiya tha, to ye raha poora setup. 🙌 Idea: Claude ko Ootto connector se apne Instagram se jodo, phir ek line bolo: **\"Mere brand ke liye 30 reels banao.\"** Ye pehle research karta hai (competitors, niche, tumhara brand), phir usi research se har reel likhta hai."),
   ("warn", "**Honest note:** Ootto ek third-party connector hai, Claude ka official Instagram feature nahi; connect karne se pehle permissions padho. Done-for-you (har mahine 30 reels bhejna) Ootto ki paid service hai, meri nahi; pricing aur reels ki quality khud check karo. \"Har reel bana ke schedule karna\" Ootto ka claim hai; pehle 2–3 reels khud dekh ke hi auto-schedule pe bharosa karo.")]),
 ("Step 1", "Ootto ko Claude se jodo (ek baar)", [
   ("ol", ["Instagram account **Professional** (Creator ya Business) hona chahiye.", "claude.ai kholo → **Settings → Connectors**.", "**Add custom connector** dabao.",
           "Name: **Ootto**. Remote MCP server URL: Ootto ki official website se link copy karke paste karo. Kisi random DM ya comment wala link mat use karo.",
           "**Add → Connect** → Ootto mein sign in → Instagram account choose karo → **Allow**.", "Connectors list mein **Ootto ✓ Connected** dikhe to done."]),
   CONNECT_NOTE]),
 ("Step 2", "Wo ek line", [
   ("p", "Naya chat kholo, confirm karo ki Ootto connected hai, aur ye bhejo:"),
   ("prompt", "Copy karo", "Mere brand ke liye 30 reels banao.\nBrand: @[handle] | Niche: [topic] | Audience: [kaun] | Language: Hinglish\nPehle research karo:\n1. Mere 3-5 competitors ki top reels (hooks, formats)\n2. Mere niche mein last 30 din ke outliers (average nahi)\n3. Meri profile se mera brand: awaaz, offer, audience\nPhir har reel ke liye: hook (pehle 2 sec), script (30-45 sec), on-screen text, caption, comment keyword.\nPehle 30 din ka plan table mein dikhao. Meri approval ke bina kuch bhi schedule ya post mat karna.")]),
 ("Step 3", "Review karo, phir schedule", [
   ("list", ["Plan table padho: koi topic repeat to nahi, koi claim galat to nahi.", "Pehli 3 reels poori check karo (hook, captions, sound).", "Sahi lage tab bolo: \"Theek hai, schedule kar do.\""]),
   ("tip", "**Done-for-you (optional, paid):** Ootto mein Done-for-you on karne pe wo har mahine 30 reels bhejne ka offer deta hai, har din ke liye ek. Ye unki service hai: pricing, terms aur sample reels unki site pe dekho, phir decide karo.")]),
 ("Checklist", "Checklist", [
   ("list", ["Instagram Professional account hai", "Ootto connector add kiya, \"Connected\" dikh raha hai", "Step 2 wala prompt chalaya, 30 din ka plan mila", "Pehli 3 reels khud check ki", "Approve karke hi schedule kiya"])]),
])

G["VIRAL"] = page("VIRAL", "Free virality skill", "for Claude",
 "Ek free, open-source (MIT) Claude skill jo 262 posts ke winners aur flops ko frame by frame compare karke bani hai.", [
 ("Ye kya hai", "Claude Virality Skill", [
   ("p", "Tumne **VIRAL** comment kiya tha, to ye raha link. 🙌 Claude Virality Skill ek free, open-source (MIT) Claude skill hai: [github.com/Ootto-AI/claude-virality-skill](https://github.com/Ootto-AI/claude-virality-skill). Ye ek creator (@jayantcreates.ai) ke 262 posts aur 35 lakh views ke winners aur flops ko frame by frame compare karke bani hai."),
   ("table", ["Period", "Posts", "10,000+ views", "1,00,000+ views"], [["June–August", "132", "3", "—"], ["September–October", "130", "31", "9"]]),
   ("warn", "Ye numbers unke page ke hain (public README se), mere nahi. Skill patterns sikhati hai; views ki guarantee koi skill nahi de sakti.")]),
 ("4 patterns", "4 patterns jo farak laaye", [
   ("ol", ["**Pehle 3 seconds mein screen pe kuch zabardast ho.** Title card, logo fade ya \"Hi guys\" nahi. Ek event jo aankh ignore na kar sake.",
           "**Darshak ka Instagram dikhao, apna tool nahi.** Jo cheez wo roz dekhte hain, wahi screen pe ho.",
           "**Har line pe ek visual.** Koi frame khaali ya static nahi.", "**Comment karne ki ek wajah.** Keyword + kuch value jo DM mein milegi."])]),
 ("Install", "Install", [
   ("p", "**Claude (claude.ai ya desktop app):**"),
   ("ol", ["GitHub repo kholo → green **Code** button → **Download ZIP**.", "Sirf **virality** folder ko zip karo.", "Claude mein **Settings → Capabilities → Skills** mein jao aur zip upload karo. Skill on karo."]),
   ("p", "**Claude Code:**"),
   ("code", "Terminal", "git clone https://github.com/Ootto-AI/claude-virality-skill\ncp -r claude-virality-skill/virality ~/.claude/skills/"),
   ("tip", "Optional: apni reels Claude ko seedha padhwani ho to Ootto connector se Instagram connect kar sakte ho (Settings → Connectors → Add custom connector). Bina connector ke bhi chalega: apni reels ke links ya screenshots paste karo.")]),
 ("Use", "Use kaise karein", [
   ("prompt", "Agli reel plan karo", "Virality skill use karke meri agli reel plan karo.\nTopic: [topic] | Niche: [niche] | Language: Hinglish | Length: 30-45 sec\nPehle 3 seconds ka visual event batao (frame 0 pe kya dikhega),\nphir har line ke saath on-screen visual, aur end mein comment keyword."),
   ("prompt", "Last reel kyun flop hui", "Ye meri last reel hai [link/screenshot]. Virality skill ke rules se batao\nflop kyun hui, aur hook ke pehle 3 seconds kaise badlun.")]),
 ("Checklist", "Checklist", [
   ("list", ["Skill install kiya (Claude Skills ya Claude Code)", "Agli reel ka hook skill se plan kiya", "Frame 0 pe event hai, title card nahi", "Har line pe visual hai", "End mein comment ki wajah hai"])]),
])

G["AUTOPILOT"] = page("AUTOPILOT", "Claude se Instagram autopilot", "(safe setup)",
 "Claude tumhara Instagram dekhe, niche ke top creators aur is hafte ke topics padhe, product reels banaye, aur comments ko leads mein badle. 4 steps.", [
 ("Ye kya hai", "Connect → Creators → Topics → Posts", [
   ("p", "Tumne **AUTOPILOT** comment kiya tha, to ye raha poora setup. 🙌 Idea: Claude ko tumhara Instagram dikhao, wo niche ke top creators aur is hafte ke topics padhe, tumhare product ke liye reels banaye, aur comments ko leads mein badle."),
   ("warn", "**Honest + safe note:** Instagram connection Ootto (third-party connector) se hota hai, Claude ka official feature nahi. Har reel post hone se pehle khud approve karo; fully automatic posting aur replies robotic lag sakte hain. Ek account pe consistency rakho: bahut saare accounts se same product push karna ya mass automated DMs/comments Instagram ke spam rules todte hain, aur account restrict ya ban ho sakta hai. Reel mein dikhaye leads ek example the.")]),
 ("Step 1", "Connect", [
   ("ol", ["Instagram account **Professional** (Creator ya Business) hona chahiye.", "claude.ai → **Settings → Connectors → Add custom connector**.",
           "Name: **Ootto**. URL: Ootto ki official website se copy karo.", "**Connect** → Instagram login → permissions padho → **Allow**. \"Connected\" dikhe to done."])]),
 ("Step 2", "Creators", [
   ("prompt", "Copy karo", "Mere niche [niche] ke top 5 creators dhoondo jo is hafte sabse zyada chal rahe hain.\nHar ek ki top 3 reels ke hooks todo: pehle 3 second mein kya dikha, kya bola.\nTable mein do: creator, reel, views, hook type.")]),
 ("Step 3", "Topics → product reel", [
   ("prompt", "Copy karo", "Is hafte mere niche mein kya sach mein chal raha hai (topics + formats jo saves la rahe hain)?\nUnmein se 3 topics chuno jo mere product [product + 1 line] se jud sakte hain.\nHar ek ke liye reel banao: hook (pehle 2 sec), 30-40 sec script, on-screen text,\ncaption aur comment keyword. Pehle mujhe dikhao, post mat karna.")]),
 ("Step 4", "Posts + comments → leads", [
   ("prompt", "Copy karo", "Maine Day 1 reel approve kar di hai. Ise publish karo.\nPhir comments ke reply drafts likho: short, friendly, Hinglish.\nJo bhi price, link ya \"kaise\" pooche, unhe LEAD mark karo aur DM ka draft do.\nKoi bhi DM bhejne se pehle mujhe dikhao."),
   ("tip", "**Comment → DM automatic chahiye?** Iske liye ManyChat jaisa approved Instagram tool use karo: trigger = keyword comment, action = DM mein link. Ye Meta ke rules ke andar chalta hai.")]),
 ("Routine", "Roz ka routine (15 min)", [
   ("list", ["Aaj ki reel padho aur approve karo", "Kal ke comments ke reply drafts check karke bhejo", "LEAD wale logon ki list dekho, khud follow-up karo",
             "Hafte mein ek baar: \"kya chala, kya nahi\" poochho aur agle hafte ka plan update karo"])]),
])

G["SETUP"] = page("SETUP", "Plan 100 researched reels,", "edit them as one journey",
 "Thanks for commenting SETUP! The full workflow from the reel: 100 research-based reel scripts in Claude, then a seamless one-camera edit in Remotion.", [
 ("Before you start", "Honest note", [
   ("warn", "Claude plans and scripts the reels for you. It doesn't post them. Check every script and every video yourself before posting.")]),
 ("Part 1", "100 reel scripts, built from research (not random)", [
   ("p", "**What you need**"),
   ("list", ["A Claude account (Pro or higher is best for long sessions)", "Claude Code, if you want to install skills as a plugin",
             "Two free, open-source skill packs (MIT): [claude-content-skills](https://github.com/Ootto-AI/claude-content-skills) (research, hooks and scripting skills) and [claude-virality-skill](https://github.com/Ootto-AI/claude-virality-skill) (patterns from what actually went viral)"]),
   ("p", "**Install.** In Claude Code, run:"),
   ("code", "Claude Code", "/plugin marketplace add Ootto-AI/claude-content-skills\n/plugin marketplace add Ootto-AI/claude-virality-skill"),
   ("p", "Then open `/plugin` and install both. In the Claude app, you can instead download the skill folders from GitHub and upload them under **Settings → Capabilities → Skills**.")]),
 ("Inputs", "The 4 research inputs (same as in the reel)", [
   ("ol", ["**Your niche:** tell Claude your niche, audience and language, e.g. \"AI tools for Indian creators, Hinglish\". Ask it to search what's trending this month.",
           "**Competitor trends:** paste 3–5 competitor handles and their top reel topics or hooks. Ask Claude to find the common patterns.",
           "**Your own best reels:** paste the titles, hooks and views of your top 5–10 reels. Claude finds what your audience responds to.",
           "**Hooks + language from the internet:** ask Claude to collect real phrases people use (YouTube comments, Reddit, X) so your scripts sound like your audience."]),
   ("prompt", "The prompt", "Use the content research + virality skills.\nMy niche: <niche>. Audience: <who>. Language: Hinglish.\nCompetitors: <handles + their top topics>.\nMy best reels: <hook – views> x 5.\nStep 1: research trends + patterns and show me a summary.\nStep 2: plan 100 reels as a table: # | topic | hook (first 3 sec) | angle | CTA keyword.\nStep 3: write full scripts for the first 10 (max 45 sec each)."),
   ("tip", "Work in batches of 10–20 scripts so quality stays high, then edit them in your own voice.")]),
 ("Part 2", "Edit like this reel (one camera, no cuts)", [
   ("p", "This reel was built with **Claude Code + Remotion** (code-based video editing)."),
   ("ol", ["Install Node.js, then run `npx create-video@latest` to create a Remotion project.", "Open the folder in Claude Code.",
           "Give Claude your voiceover file and script, then use the prompt below.", "Preview with `npx remotion studio`, ask Claude for fixes, then render with `npx remotion render`."]),
   ("prompt", "Step 3 · Prompt", "Build a 9:16 reel in Remotion from this voiceover.\nLayout: put every scene as a \"station\" on one big canvas (3x3 grid).\nCamera: ONE continuous camera that flies from station to station, no cuts.\nAt the end, zoom out to show the whole journey, then land on the CTA.\nAdd word-by-word captions synced to the voice, plus light SFX on each move."),
   ("tip", "**Why it works:** a seamless camera turns the reel into one story instead of separate slides, so viewers keep watching to see where the camera goes next.")]),
 ("Tips", "Tips", [
   ("list", ["Rendering takes a few minutes per reel, so batch it.", "Keep reels under 50 seconds.", "Always review the facts and numbers before posting."])]),
])

G["GPT"] = page("GPT", "Connect ChatGPT to Instagram", "with Ootto",
 "Thanks for commenting GPT! The full setup from the reel: Ootto connected to ChatGPT as an MCP app, so you can audit your reels and create new ones from a chat.", [
 ("Before you start", "Read this first", [
   ("warn", "This uses **Ootto** (ootto.ai), a third-party tool, connected to ChatGPT as an MCP app. Menu names in ChatGPT change often. If you don't see **Plugins**, look under **Settings → Apps & Connectors** (you may need to turn on Developer mode under Advanced). Check pricing and plan limits on ootto.ai before you connect your account.")]),
 ("What it does", "What it does", [
   ("list", ["**Audit:** looks at your page and shows where viewers dropped off on your last reel, and why it may not have gone viral.", "**Create:** makes reels for you on autopilot, from inside ChatGPT."])]),
 ("Setup", "Setup (about 2 minutes)", [
   ("ol", ["**Open Plugins:** in ChatGPT, open **Plugins** in the left sidebar.", "**Add:** press **Add** (top right) and choose **Create MCP App**.",
           "**Fill the form** (values below). Tick **I understand and want to continue**, then press **Create**.",
           "**Connect:** ChatGPT asks you to connect Ootto. Press **Continue to ootto**.",
           "**Sign in** to Ootto, or sign up if you're new. You land back in ChatGPT with Ootto connected. No API key to copy.",
           "**Ask:** open a new chat and type `@ootto create reel`. That's one message."]),
   ("table", ["Field", "Value"], [["Name", "`ootto`"], ["Server URL", "`https://mcp.ootto.ai/mcp`"], ["Authentication", "OAuth"], ["Icon", "Ootto logo (optional)"]])]),
 ("Prompts", "Good prompts to try", [
   ("prompt", "Audit", "@ootto audit my last 5 reels and tell me where people dropped off"),
   ("prompt", "Create", "@ootto create a reel about <topic> with a strong hook in the first 3 seconds")]),
 ("Tips", "Tips", [
   ("list", ["Review every reel before it goes live. Autopilot doesn't mean unchecked.", "If the server URL doesn't work, get the latest one from ootto.ai.", "Workflow credit: @jayantcreates.ai / Ootto."])]),
])

for name, html in G.items():
    open(os.path.join(OUT, f"{name}.html"), "w", encoding="utf-8").write(html)
TARGET = {18: "MONTH", 19: "VIRAL", 20: "AUTOPILOT", 21: "SETUP", 22: "GPT"}
p = "freebies/index.html"; s = open(p, encoding="utf-8").read()
i = s.index("const D=") + 8; j = s.index(";\n", i); d = json.loads(s[i:j])
for x in d["items"]:
    if x["n"] in TARGET:
        x["u"] = f"guides/{TARGET[x['n']]}.html"; print(x["n"], x["k"], "->", x["u"])
open(p, "w", encoding="utf-8").write(s[:i] + json.dumps(d, ensure_ascii=False) + s[j:])
