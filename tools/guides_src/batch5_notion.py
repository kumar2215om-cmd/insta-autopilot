"""Guides rebuilt from the Notion PDFs (STRATEGY, PLAYBOOK, SKILLS, API) + new MOBILE. Run from repo root."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from guidepage import page
OUT = "freebies/guides"
G = {}

G["STRATEGY"] = page("STRATEGY", "The AI social media system:", "ideas, calendar, hooks",
 "Thanks for commenting STRATEGY! The full AI system from the reel, with copy-paste prompts. Works with Claude (claude.ai) or ChatGPT.", [
 ("Before you start", "Honest note", [
   ("warn", "AI does the thinking and drafting fast, but you still decide, record and post. Most people save about half their planning time. Your results depend on your niche and consistency.")]),
 ("Step 0", "Set up your brain (one time)", [
   ("p", "Create a **Project** in Claude (or a custom GPT) and paste this as the project instructions:"),
   ("prompt", "Project instructions", "You are my social media strategist.\nBrand: <name> | Niche: <niche> | Audience: <who, age, city, language>\nGoal: <followers / leads / sales>\nTone: <e.g. Hinglish, friendly, short lines>\nWhat worked before: <your top 5 posts + views>\nAlways answer in tables when planning. Be specific, no generic advice."),
   ("tip", "Upload your best captions or scripts as files so it learns your voice.")]),
 ("Steps 1–3", "Ideas, calendar, hooks", [
   ("prompt", "1 · Content ideas", "Give me 30 content ideas for my niche.\nMix: 40% educational, 30% relatable/story, 20% proof/results, 10% promo.\nTable: # | idea | angle | why my audience cares"),
   ("prompt", "2 · 30-day calendar", "Turn these ideas into a 30-day calendar.\nTable: date | topic | format (reel/carousel/static/story) | hook | CTA keyword\nDon't repeat the same topic within 7 days."),
   ("prompt", "3 · Hooks + format", "For idea #<n>, write 10 hooks (first 3 seconds, max 8 words each).\nThen tell me the best format for it and why.")]),
 ("Steps 4–5", "Captions, design + reel script", [
   ("prompt", "4 · Captions", "Write the caption for post #<n> in my tone.\nStructure: 1-line hook, 3–5 short value lines, 1 CTA, 8–10 hashtags."),
   ("prompt", "5 · Design + reel script", "Give me a slide-by-slide carousel outline (max 7 slides) for post #<n>.\nWrite a 30–45 sec reel script with on-screen text for every line."),
   ("tip", "Use **Canva** for design, and **CapCut** or **Claude Code + Remotion** to edit.")]),
 ("Steps 6–8", "Timing, comments, analytics", [
   ("p", "**6 · Best time to post.** Open Instagram → **Insights → Total followers → Most active times**, take a screenshot, and upload it:"),
   ("prompt", "6 · Best time", "From this screenshot, give me the best 2 posting slots for each day of the week."),
   ("prompt", "7 · Comments", "Here are 20 comments from my last reel. Group them into questions, objections and praise.\nWrite short replies in my tone, and suggest 3 new content ideas from the questions."),
   ("p", "**8 · Analytics (why reach dropped).** Screenshot the post insights (reach, watch time, skip rate, shares, saves) and upload them:"),
   ("prompt", "8 · Analytics", "Compare this post with my top 3 posts. Why did reach drop?\nCheck: hook, first 3 sec retention, length, topic, posting time.\nGive me 3 specific fixes for the next post.")]),
 ("Routine", "Weekly routine (about 2 hours)", [
   ("table", ["Day", "What to do"], [["**Monday**", "Ideas, calendar and hooks for the week (steps 1–3)."], ["**Tuesday**", "Captions and scripts (4–5), then record and edit."],
                                   ["**Daily**", "Post at your best slot, then reply to comments (7)."], ["**Sunday**", "Run the analytics review (8) and feed the learnings into next week."]])]),
])

G["PLAYBOOK"] = page("PLAYBOOK", "AI delegation:", "1 agent + playbooks",
 "Thanks for commenting PLAYBOOK! Stop building a new agent for every task. Run one agent and give it a playbook for each job. Every prompt included.", [
 ("The idea", "One agent, many playbooks", [
   ("p", "This works best in **Claude (Projects)**, and also works in ChatGPT (Projects or custom GPTs). The idea: stop building a new agent for every task. Run one agent and give it a **playbook** for each job."),
   ("p", "Anthropic engineers made the same point in their talk **\"Don't build agents, build skills instead\"**. A playbook is basically a skill: written instructions plus files the AI loads when it does that job.")]),
 ("Setup", "Setup (one time)", [
   ("p", "In Claude, create a Project called **\"My Delegation\"** with three parts:"),
   ("list", ["**PLAYBOOKS:** one file per job (e.g. `weekly-report.md`)", "**TOOLBOX:** approved scripts, templates, docs and examples", "**Project instructions:** the master prompt below"]),
   ("prompt", "Master prompt", "You are my delegate. Before any task:\n1. Find the matching playbook and follow it exactly.\n2. Use files from the toolbox instead of creating new versions.\n3. Before you show me anything, check your work against the playbook's DONE MEANS checklist and tell me which checks passed.\nIf no playbook exists for a task, say so and offer to interview me to create one.")]),
 ("01 · Interview", "Turn your work into a playbook", [
   ("prompt", "Interview prompt", "Interview me about how I do <task> until you could do it without me.\nAsk one question at a time: the goal, who it's for, the inputs, the steps, the format, the rules, common mistakes, and who signs it off.\nWhen you have enough, say \"READY\"."),
   ("prompt", "Then", "Turn everything I told you into a playbook file:\n# <Task name>\nGoal:\nInputs:\nSteps (numbered):\nRules (always / never):\nToolbox files to use:\nDONE MEANS (checklist):\nKeep it under one page.\nSave it in PLAYBOOKS.")]),
 ("02 · Toolbox", "Never make the same thing twice", [
   ("p", "Every time you approve an output (a script, a template, an email or a report), save it to the toolbox and link it in the playbook as a rule."),
   ("prompt", "Toolbox prompt", "This output is approved. Turn it into a reusable template (replace specifics with {placeholders}).\nThen add a rule to the <task> playbook: \"Always start from toolbox/<file>\".")]),
 ("03 · Proof", "The \"done\" checklist", [
   ("p", "Hardly anyone does this, and it's the step that makes the agent reliable."),
   ("prompt", "Checklist prompt", "Write a DONE MEANS checklist for <task>: 4–6 checks that are specific and verifiable (no \"looks good\").\nAdd it to the playbook. From now on, review your own work against it before you hand anything over, and show me pass/fail for each check."),
   ("p", "**Example for a weekly report:**"),
   ("list", ["Matches the brief", "Built from the toolbox template", "Every number double-checked against the source", "Ready to send as is"])]),
 ("04 · Fix loop", "The fix loop", [
   ("p", "When the agent messes up, don't correct it in the chat, because the chat is forgotten next time. **Fix the playbook instead:**"),
   ("prompt", "Fix prompt", "That was wrong because <reason>.\nUpdate the <task> playbook so this can't happen again (add a step, a rule or a check). Show me the diff."),
   ("tip", "**Playbook → run → check → fix playbook.** That's the whole loop. Each fix makes every future run better."),
   ("p", "**Starter playbook ideas:** weekly report · client emails · reel scripts · meeting notes to action items · invoice follow-ups · social captions · research summaries.")]),
])

SK = {
"motion-ad": ("1 · Premium motion ad", """---
name: motion-ad
description: Plans a premium 10–15s kinetic-typography 3D motion ad and writes AI video prompts for every shot. Use when the user wants a motion ad, logo reveal or hype promo.
---
# Motion ad
Ask for: brand, product, 3–5 word slogan, brand colours, platform (9:16 default).
Output:
1. Concept in one line + the slogan split into 3 beats.
2. Shot list (5–6 shots, 2–3s each): camera move, what appears, transition.
3. For EACH shot, one video prompt in this format:
   "3D kinetic typography, glossy {colour} extruded letters spelling '{word}', floating chrome ribbons and glossy spheres, confetti, {background colour} studio backdrop, soft rim light, camera {move}, 9:16, ultra-detailed, 24fps"
4. Music + SFX notes (whooshes on each word).
Rules: max 3 words on screen per shot. Strong colour contrast. End on the logo + CTA."""),
"claymation-spot": ("2 · Claymation spot", """---
name: claymation-spot
description: Plans a cute 15–20s stop-motion claymation ad and writes prompts per shot. Use for warm, handmade-feel brand spots.
---
# Claymation spot
Ask for: brand, product, hero character idea, setting.
Output:
1. Mini story in 3 beats (setup → problem → product saves the day).
2. Character sheet: shape, colours, outfit, expression.
3. 5–7 shots with action + camera.
4. Prompt per shot:
   "stop-motion claymation, handmade plasticine {character} with visible fingerprints, {action}, miniature {setting} set, warm soft lighting, shallow depth of field, slightly jittery 12fps stop-motion feel, 9:16"
5. A voiceover or caption line per shot.
Rules: keep the character identical in every prompt (copy the character sheet in)."""),
"docu-trailer": ("3 · Netflix-style documentary", """---
name: docu-trailer
description: Plans a cinematic Netflix-style documentary teaser (20–30s) with narration and shot prompts.
---
# Documentary teaser
Ask for: topic, the one big question, tone (awe / mystery / emotional).
Output:
1. Narration script: 4–6 short lines, deep calm voice, ending on a question.
2. Shot list: wide establishing → detail → subject reveal → emotional close.
3. Prompt per shot:
   "cinematic documentary footage, {subject}, {location}, god rays, natural colour grade, anamorphic lens, slow push-in, film grain, 9:16"
4. Title card text + music direction (low strings, swells on the reveal).
Rules: no on-screen text except the title. Let shots breathe (3–4s)."""),
"animated-song": ("4 · Disney-style song", """---
name: animated-song
description: Writes an original Disney-inspired song (lyrics + style prompt) and a matching animated music video shot list.
---
# Animated song
Ask for: theme or product, mascot character, mood.
Output:
1. Original lyrics: verse + chorus (catchy, simple rhymes, 30–45s).
2. Music prompt for Suno/Udio: "whimsical orchestral pop, musical-theatre style, bright strings, glockenspiel, {mood}".
3. Character sheet for the mascot.
4. 6–8 shots synced to the lyric lines, each with a prompt:
   "3D animated feature-film style, cute {character}, {action}, glowing magical forest, fireflies, volumetric light, vibrant colours, 9:16"
Rules: original lyrics only, never copy real song lyrics or real Disney characters."""),
"product-commercial": ("5 · Product commercial", """---
name: product-commercial
description: Plans a high-end 10–15s product commercial (drinks, beauty, gadgets) with hero shots and prompts.
---
# Product commercial
Ask for: product, 3 key ingredients or features, brand colours, tagline.
Output:
1. Hook shot idea (first 1.5s must stop the scroll).
2. Shot list: splash/explosion hero → ingredient macro → product rotate → tagline.
3. Prompt per shot:
   "premium product commercial, {product} centred, {ingredients} exploding around it in slow motion, liquid splash, {colour} gradient backdrop, studio lighting, ultra-sharp macro, 9:16"
4. On-screen text (max 4 words per shot) + SFX.
Rules: the product label always faces the camera. One colour family."""),
"3d-short-film": ("6 · Hollywood 3D short", """---
name: 3d-short-film
description: Plans a 30–60s Pixar/Hollywood-style 3D animated short with story beats and consistent character prompts.
---
# 3D short film
Ask for: hero character, world, emotion.
Output:
1. Logline + 5-beat story (world → want → obstacle → choice → payoff).
2. Character sheet + world sheet (lighting, palette, time of day).
3. 8–10 shots with camera, action, emotion.
4. Prompt per shot:
   "high-end 3D animated film still, {character sheet}, {action}, {world sheet}, cinematic lighting, depth of field, rain/lantern glow details, 9:16"
5. Sound design notes.
Rules: paste the same character + world sheet into every prompt for consistency."""),
"kids-cartoon": ("7 · Kids cartoon", """---
name: kids-cartoon
description: Plans a bright 30–60s educational kids cartoon episode (song or story) with simple shot prompts.
---
# Kids cartoon
Ask for: lesson (counting, colours, manners...), age (2–6), characters.
Output:
1. Episode idea + a simple repeating song or chant.
2. Characters (max 3): animal, colour, personality.
3. 6–8 shots, each with a prompt:
   "2D cartoon for kids, bright flat colours, thick outlines, {characters} {action}, sunny hills and candy trees, cheerful, simple shapes, 9:16"
4. Narration lines (short, repetitive, easy words).
Rules: safe and positive, no scary elements, one idea per episode."""),
}
skill_secs = [(t.split(" · ")[1][:22], t, [("code", f"{k}/SKILL.md", body)]) for k, (t, body) in SK.items()]
G["SKILLS"] = page("SKILLS", "7 Claude skills for", "agency-level AI videos",
 "Thanks for commenting SKILLS! All 7 skills: each one turns Claude into a specialist that writes the script, shot list and copy-paste video prompts for one style.", [
 ("How it works", "Honest version", [
   ("warn", "Claude plans and writes the prompts. The actual video is rendered in an AI video tool like **Kling, Veo, Runway, Hailuo or Higgsfield**. Results depend on the tool you use. The example videos in the reel are by @guipaulinooo.")]),
 ("Install", "How to install a skill in Claude", [
   ("ol", ["For each skill below, create a folder (e.g. `motion-ad`) with a file named **SKILL.md** inside, and paste the skill text into it.", "Zip the folder.",
           "In Claude, go to **Settings → Capabilities → Skills → Upload skill**, and upload the zip.", "In a new chat, say e.g. \"Use the motion-ad skill for my coffee brand\"."]),
   ("tip", "No skills feature on your plan? Paste the skill text at the start of a chat (or into a Project's instructions). It works the same way.")]),
] + skill_secs + [
 ("Workflow", "Workflow tips", [
   ("list", ["Generate one shot at a time in your video tool, then stitch them in CapCut.", "Keep a character sheet and paste it into every prompt so the character stays consistent.",
             "Make 2–3 variations per shot and keep the best one."])]),
])

G["API"] = page("API", "Run Claude Code", "without a subscription",
 "Thanks for commenting API! The full setup from the reel: Claude Desktop Developer Mode + a gateway, the gateway options, and how to keep costs low.", [
 ("Before you start", "Honest note", [
   ("warn", "This is **not free**. You skip the $20/month subscription and pay per token for what you use. Light use is often cheaper; heavy coding can cost more than $20.")]),
 ("Steps", "Step by step", [
   ("ol", ["Download **Claude Desktop** from claude.com/download and install it.", "Open the menu (••• or the top menu bar) → **Help → Troubleshooting → Enable Developer Mode**.",
           "A new **Developer** menu appears → **Configure Third-Party Inference**.", "Fill in the fields (table below).",
           "Click **Apply**, then fully quit Claude (not just close the window) and reopen it.", "Open the **Code** tab. Claude Code now runs through your gateway."]),
   ("table", ["Field", "Value"], [["Connection", "Gateway (Anthropic-compatible)"], ["Credential kind", "Static API key"],
                                ["Gateway base URL", "Your gateway's URL (from its docs)"], ["Gateway API key", "Your key"]])]),
 ("Gateways", "Gateway options", [
   ("list", ["**Anthropic API directly:** create a key at console.anthropic.com and pay per token for Claude models.",
             "**Cloudflare AI Gateway:** setup guide for Claude Desktop. Adds logging, caching and spend visibility.",
             "**Other gateways** (TrueFoundry, agentgateway and others) can route to other model providers too. Follow their own Claude Desktop docs, because field names can differ."])]),
 ("Costs", "Keep costs low", [
   ("list", ["Set a **monthly spend limit** on your API account before you start.", "Use a smaller, faster model for simple tasks and the big model only for hard ones.",
             "Start a new chat for each new task, because long chats send more tokens every message.", "Check your usage dashboard after the first few days."])]),
 ("Help", "If it doesn't show up", [
   ("list", ["Make sure you fully quit and reopened Claude after Apply.", "On some Team or enterprise accounts this option may be hidden.", "Update Claude Desktop to the latest version."])]),
])

G["MOBILE"] = page("MOBILE", "Make a full video from your phone", "with Claude Code",
 "Thanks for commenting MOBILE! The full phone setup from the reel, plus the free-plan jugaad prompt.", [
 ("Before you start", "Honest note", [
   ("warn", "The **Code** tab (Claude Code cloud sessions) needs a paid plan (Pro or Max). If you don't see the Code tab, your plan doesn't include it, so use the free jugaad at the bottom.")]),
 ("Setup", "One-time setup", [
   ("ol", ["Install the **Claude app** (iOS / Android) and log in.", "Make a free **GitHub** account and create a repo (e.g. `my-reels`). This is where your videos and code get saved.",
           "In the Claude app, open the **Code** tab, then connect GitHub when it asks and pick your repo.", "Environment: keep **Default**."])]),
 ("Every time", "Make a video (every time)", [
   ("ol", ["Open **Code** → pick your repo → type or hold the mic and say what you want.", "Paste the prompt below (edit the song and style).",
           "Lock your phone. It runs in Claude's cloud, so you can come back later.", "When it's done, open the repo (GitHub app or website) → `out/video.mp4` → download → post."]),
   ("prompt", "Prompt", "Make a 1080x1920 vertical lyric video for Instagram using Remotion.\nSong lyrics (one line per caption): [PASTE LYRICS]\nStyle: dark night sky, thin neon line-art city skyline that draws itself, soft glow, handwritten-style text that fades in word by word, gentle camera drift.\nLength: [15-30] seconds, 30 fps. Add my audio file [audio.mp3] if I uploaded it to the repo, otherwise no audio.\nRender the final MP4 to out/video.mp4, commit it to the repo, and tell me when it's done."),
   ("tip", "Only use songs you have the rights to use, or add the music inside Instagram from its library.")]),
 ("Free jugaad", "Free plan jugaad (no Code tab)", [
   ("ol", ["Open a normal chat in the Claude app.", "Paste the prompt below.",
           "Open the artifact full screen → start your phone's screen recording → crop it in the gallery or CapCut → add music → post.", "Quality is a bit lower than a real render, but it works."]),
   ("prompt", "Jugaad prompt", "Create an artifact: a full-screen animated lyric video in HTML/CSS/JS, vertical 9:16.\nLyrics: [PASTE LYRICS]\nStyle: dark night sky, neon line-art skyline that draws itself, words fade in one by one, loops smoothly. No sound needed. Make it start automatically.")]),
])

for name, html in G.items():
    open(os.path.join(OUT, f"{name}.html"), "w", encoding="utf-8").write(html)
TARGET = {23: "STRATEGY", 24: "PLAYBOOK", 25: "SKILLS", 38: "API"}
p = "freebies/index.html"; s = open(p, encoding="utf-8").read()
i = s.index("const D=") + 8; j = s.index(";\n", i); d = json.loads(s[i:j])
for x in d["items"]:
    if x["n"] in TARGET:
        x["u"] = f"guides/{TARGET[x['n']]}.html"; print(x["n"], x["k"], "->", x["u"])
if not any(x["k"] == "MOBILE" for x in d["items"]):
    n = max(x["n"] for x in d["items"]) + 1
    d["items"].insert(0, {"n": n, "k": "MOBILE", "t": "Phone se poori video: Claude Code + free jugaad", "topic": "Claude makes reels", "e": "📱", "u": "guides/MOBILE.html"})
    print("added MOBILE as card", n)
open(p, "w", encoding="utf-8").write(s[:i] + json.dumps(d, ensure_ascii=False) + s[j:])
