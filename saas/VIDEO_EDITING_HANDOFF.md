# ReplyInbox: Video Editing Handoff (@replyinbox.in reels)

Updated 22 Nov 2026 (after reels R01 and R02). This is for recreating **competitor SaaS reels** for ReplyInbox.
- Keep the reference's **pacing and structure**.
- Replace everything else with **ReplyInbox's own product, screens, copy and brand**.
- The build pipeline is in `saas/REELS_HANDOFF.md`.
- A worked example is reel **R01** (`saas/content/reels/r01/`).

---

## 1. Golden rules

1. **Reference = format and timing only.**
   - Never use a competitor's **name, logo, UI, footage, music, characters or exact on-screen design**.
   - Copy the beat structure: hook length, number of steps, where the "twist" lands, CTA timing.
   - The script can follow the reference's line-by-line rhythm, but every claim must be about ReplyInbox and true (§4).
2. **Real product only.**
   - Show real ReplyInbox screens: the screenshots in §3, or a screen recording of `/demo`.
   - A mock-up is fine for flows that are hard to record (e.g. Instagram's own DM view). If it shows made-up numbers, label it **"Illustration"** on screen.
3. **No invented results.** No fake follower counts, revenue or testimonials. Om's real numbers only, as cropped screenshots.
4. **Instagram safe zones** (1080×1920): keep text and key UI out of the top **250 px** and bottom **300 px**. The right edge (~120 px) holds the like/comment buttons, so don't put text there either.
5. **Every reel ends** with "Comment KEYWORD" plus the @replyinbox.in FollowCard, and no silence after it.
6. **Hinglish voiceover**, friendly and simple. On-screen text in Roman Hinglish/English.

## 2. Brand kit

| Token | Hex | Use |
|---|---|---|
| Paper | `#F5F4EF` | background; dot grid of ink at 13% opacity, 3 px dots every 48–54 px |
| Ink | `#111318` | text, **4–6 px outlines**, **hard offset shadows 8–16 px** (no blur) |
| Cobalt | `#2E3BFF` | accent, buttons, CTA screen background, logo tile, sticker outline on the character |
| Volt | `#D4FF3A` | highlighter behind the headline's key word, pill tags, numbered circles, keyword box |
| Coral | `#FF5B3A` | "the problem / the catch" beats |
| Mist | `#E6E5DE` | panels, chat bubbles |
| Win | `#16A34A` | "✓ Connected", "DM sent", money in |
| Loss | `#E5484D` | "❌ missed DMs", money lost |

- **Fonts:**
  - **Bricolage Grotesque 800:** headlines, punch words, captions; tight tracking (−0.04em).
  - **Manrope 600–800:** body text.
  - **JetBrains Mono 700:** labels, pills, numbers, keywords, @handle.
  - Google Fonts / `@fontsource`.
- **Shapes:**
  - Cards: white, 5 px ink border, radius 32–34, shadow 14 px 14 px ink.
  - Pills: radius 999, 4 px border.
  - Browser-window frames around screenshots: mist top bar with 3 dots and a URL pill.
- **Logo:** solid cobalt tile, white chat bubble with a reply arrow (`saas/templates/_logo.html` → `mark()`). Wordmark "Reply" ink + "Inbox" cobalt; on dark, "Inbox" in volt. No gradients.
- **Character (optional):** Om's cut-out poses in `saas/content/characters/om/` (90 poses, tags in `characters.json`, slide roles in `roles.json`).
  - Add a white (≈8 px) + cobalt (≈16 px) sticker outline.
  - Bottom of frame, ≤ 650 px tall.
  - A different pose per scene.

## 3. Assets for B-roll

**Real dashboard screenshots** (`saas/static/seo/*.jpg`; put them in a browser-window frame and zoom/pan into the relevant part):

| File | Shows | Good for |
|---|---|---|
| `auto-dm-list.jpg` | Auto DM list with automations | "all your automations in one place" |
| `wizard-trigger.jpg` | step 1: what triggers it (reel / all posts / next post / story / Live) | "pick the reel" |
| `wizard-keyword.jpg` | keyword + public replies | "set the keyword" |
| `wizard-follow-email.jpg` | follow to unlock + email/WhatsApp capture | "followers + leads" |
| `wizard-primary-dm.jpg` | the DM with link buttons | "your link in their DM" |
| `wizard-review.jpg` | review and launch | "turn it on" |
| `wizard-story.jpg` | story replies automation | story beats |
| `ai-inbox.jpg` | AI DM agent inbox | "AI replies for you" |
| `leads.jpg` | contacts with email/WhatsApp, tags | "your leads list" |
| `reel-report.jpg` | reel funnel: views → comments → DM → link → follows | "see which reel works" |
| `sales.jpg` | sales and revenue per reel/automation | "see which reel made money" |

- **Screen recording:** `replyinbox.in/demo` (demo account: sample reels, automations, contacts). Record at 1080 px wide or more. Hide the browser chrome or frame it in our window card.
- **Instagram-side mock-ups:** draw them in brand (comment bubbles, DM bubbles, a phone frame). Use fake usernames that look generic (`riya.creates`), never real people.

## 4. Product facts (live, checked on `main` 22 Nov 2026)

Use only these. If a reference shows a feature we don't have, rewrite that beat to the nearest real feature, or skip it, and tell Om.

**Comment → DM**
- Works on any reel, on all posts, or on the **next post** (set it up before posting).
- Public replies rotate between up to 3 versions.
- The DM has **up to 3 link buttons**, or a **choice menu** with up to 3 options.

**Growth and leads**
- **Follow to unlock:** link only after they follow. Starter and up.
- **Email and WhatsApp capture** inside the DM. Starter and up.
- **Follow-up DM** 1, 3, 6, 12 or 20 hours later, inside Instagram's 24 h window.
- **Story replies and mentions.** Starter and up.
- **Live comments** (beta).

**AI DM agent**
- Replies from your FAQ in **Hinglish or any language**.
- Hands refunds and brand deals to you with a suggested reply.

**Reports**
- **Reel report:** views → comments → DM → link → follows (and follows per 1K views).
- Sales per reel/automation.

**Store + courses**
- Sales page, student dashboard, certificates.
- **UPI/card payouts to your bank** (add the bank account once).

**Other**
- **Switch between Instagram accounts** inside the editor.
- **Connect Claude (MCP)**: Pro plan, asks before every change.

**Pricing** (₹/month):

| Plan | Price | Sale fee |
|---|---|---|
| Free | ₹0, 1,000 DMs/month | 5% + GST |
| Starter | ₹149 | 5% + GST |
| Creator | ₹199 | 5% + GST |
| Pro | ₹599 | 2% + GST |
| Agency | ₹2,000 | 2% + GST |

Always say **"+ GST"** with the fees.

- **Safety line:** official Meta API, never asks for your Instagram password.
- **Competitors:** only by name if a reel is explicitly a comparison, and only with the dated, hedged facts in `saas/seo_content.py` ("about …, checked Nov 2026"). Default: no competitor names.

## 5. Workflow per reference reel

1. **Break down the reference** (fill §6 "Reference breakdown"):
   - duration
   - every cut with its timestamp
   - hook type (question / bold claim / pain)
   - number of steps
   - where the twist / "best part" lands
   - CTA wording and timing
   - music feel
   - caption style
2. **Map beats to ReplyInbox.** For each beat, pick the real feature and the screen (§3) that shows it. Flag any beat with no true equivalent.
3. **Write the Hinglish VO**, keeping the reference's rhythm and roughly its words per beat.
   - Send Om the script and a list of what changed and why.
   - Format it for ElevenLabs: Hindi in Devanagari, English words in Latin script, "…" for pauses, "Reply Inbox" as two words.
   - Voice: Aman – Indian male, stability ~37, similarity ~75, v4.
4. **Om records the VO** and gives a length limit. Trim pauses (keep ~0.15 s), then speed up to fit (1.2x default, max 1.35x).
5. **Build** (shot list → screens → motion → SFX), render, loudnorm −14 LUFS.
6. **Deliver:**
   - MP4
   - cover PNG
   - caption TXT (with "Idea credit: @handle" only if it's a creator reference; **no credit line naming a competitor brand**)
   - `automation.json` for the comment keyword
   - ZIP of all of the above
7. **Save the source** in `saas/content/reels/rNN/` on `seo-launch`.

## 6. Per-reel template (copy for each reel)

```
# RNN: <working title>   ·  keyword: <KEYWORD>  ·  target length: <≤ N s>  ·  reference: <link / file>

## Reference breakdown
| # | Time | What happens (format only) | Purpose (hook / step / proof / twist / CTA) |
|---|------|----------------------------|---------------------------------------------|

## Beat map → ReplyInbox
| # | Reference beat | ReplyInbox feature (§4) | Screen / asset (§3) | True? notes |

## Voiceover (ElevenLabs, Hinglish)
<script, one line per beat>

## Shot list
| # | In–Out (s) | VO line | Visual (screen/mock-up/character pose) | On-screen text (≤ 6 words) | Motion | SFX |
|---|-----------|---------|-----------------------------------------|----------------------------|--------|-----|

## Captions burned in
Word-by-word, ink pill with cobalt shadow, key words in volt, max 2 lines, at y ≈ 1180–1300.

## Music + SFX
Bed: <lo-fi / upbeat / none>, −26 dB under VO. Cues: ticks on words, click on cuts, whoosh into new scenes, kick on stamps/drops, coin for money beats.

## Cover
Headline (≤ 5 words, 1 volt word) + "Comment KEYWORD" pill inside the safe zone + character pose.

## Caption + automation
Caption: hook line · 3–5 "→" value lines · note (plan/illustration) · "Comment KEYWORD …" · 6–8 hashtags.
automation.json: kw:KEYWORD, 3 rotating public replies, follow gate, DM with link button to the matching replyinbox.in guide.

## QA
[ ] ≤ target length  [ ] no competitor name/logo/footage  [ ] every claim in §4  [ ] made-up numbers labelled "Illustration"
[ ] text inside safe zones  [ ] captions match VO  [ ] −14 LUFS, no clipping  [ ] FollowCard at end, no trailing silence
[ ] keyword unique (not in carousels KEYWORDS)  [ ] automation tested on the demo/test account
```

## 7. Motion and sound kit

- **Entrances:**
  - **Drop + squash:** fall 120 px with a spring (damping 11, stiffness 170), squash 0.96 on landing.
  - **Stamp:** scale 2.2 → 1 with a slight rotation (−6° to 8°), plus a kick.
  - **Pop:** scale 0 → 1.05 → 1.
- **Screens:**
  - Slow push-in (100% → 108% over the beat).
  - Cursor moves with ease-out cubic; a click is a 0.85 scale plus a cobalt ring (80 px, fades in 0.4 s).
  - Typed fields: a character every ~70 ms with a cobalt caret.
- **Highlights:** volt box behind the key word (slight −1.5° tilt, ink border, hard shadow); volt row highlight for the selected menu item.
- **Counters:** scramble-then-settle over 0.5 s for numbers (illustration or real).
- **Transitions:** hard cuts on VO pauses; a whoosh 0.12 s before the cut and a click on it. No crossfades.
- **Captions:** current word scales 1.08, spoken words full white/volt, upcoming words 35% white.
- **Sound:**
  - VO normalised −14 LUFS integrated, true peak −1.5 dB.
  - Ticks 2.4 kHz (15 ms) on each word, a bit louder on key words.
  - Click (noise burst) on cuts.
  - Kick (120 → 45 Hz sweep) on stamps.
  - Soft lo-fi chord bed at about −26 dB.
- **Export:** 1080×1920, 30 fps, H.264 CRF 16, AAC 320 kbps 48 kHz, fade the audio out over the last 0.4 s.

## 8. Worked example: R01 (Claude × ReplyInbox setup, keyword SETUP)

| Item | Detail |
|---|---|
| Reference | @jayantcreates.ai, 42 s: hook "turn me into your Instagram manager" → 2-part connect steps → "I study your profile" → week of content → "wildest part" → Comment SETUP |
| Rewrite | connect steps became ReplyInbox (login with Instagram → Settings → Create Claude link → Claude connector) |
| Claims removed | "makes voiceover/music" and "posts for you daily" (not true for ReplyInbox) |
| Claims added | reel report, "Fill my week" drafts waiting for approval, comment-to-DM set by Claude after a yes |
| Result | 42.7 s, 13 scenes, 13 character poses, illustration label on the report, "Pro plan" and "asks first" on screen |
| Files | `saas/content/reels/r01/` (source, timeline, audio scripts, cover, caption, automation) |

## 9. What Om needs to send per reel

1. The **reference video** (MP4) or link, plus the competitor/creator handle (for our notes only).
2. The **target length**, and which feature this reel should sell (if he has a preference).
3. After the script is approved: the **ElevenLabs MP3**.
4. Optional: **real proof screenshots** (his own dashboard numbers), cropped.

## 10. Delivered reels: shot lists (for re-edits)

Times are in the final video (VO already trimmed and sped up). Captions run through the whole VO.

### R01: "Claude ko Insta manager banao" · keyword SETUP · 42.7 s · VO 1.24x · `saas/content/reels/r01/`

| In–Out | VO (Hinglish) | Visual | Pose |
|---|---|---|---|
| 0.0–2.3 | Aise mujhe apna personal Instagram manager banao | Hook card: Claude × ReplyInbox logos, "Apna **Insta manager** banao 👇" | pointing at viewer |
| 2.3–5.3 | Pehle… ReplyInbox kholo, Instagram se login karo | STEP 1 pill; replyinbox.in window, "Continue with Instagram" click | phone smiling |
| 5.3–7.75 | Settings mein jao… Create Claude link dabao | Settings window, sidebar highlight, "Create Claude link" click → "Copied ✓" | laptop typing |
| 7.75–10.6 | Phir Claude kholo… Customize… Connectors | STEP 2; Claude window: Customize → Connectors highlight | pointing to side |
| 10.6–15.4 | Add Custom Connector… naam do ReplyInbox… link paste… Add | "Add custom connector" dialog: typed name, URL pasted, Add click | laptop cross-legged |
| 15.4–17.95 | Ho gaya! Ab tumhara Insta mujhse connected hai | Volt stamp "HO GAYA!" + connectors list "ReplyInbox ✓ Connected" | thumbs up |
| 17.95–23.5 | profile study… followers aur sales… reels plan | Claude chat "Meri profile study karo" + reel report bars (**Illustration**) + "FOLLOWERS + SALES" stamp | hand on chin |
| 23.5–28.1 | Hook… script… caption… comment keyword | Reel draft card, 4 ticks in sync, keyword pill SETUP | presenting |
| 28.1–32.55 | poore hafte ka reel plan… approval ka wait | 7-day grid pops in, "1 WEEK" stamp, "Waiting for your approval" | hands behind head |
| 32.55–33.55 | Aur sabse mast part? | Coral stamp "SABSE MAST PART?" | fists up shouting |
| 33.55–37.8 | comment-to-DM set… har comment pe link | Comments with "DM sent" pills → auto-DM bubble "Open the guide" | peace sign |
| 37.8–39.05 | Tumhe bas… haan bolna hai | Claude asks "set karun?" → Haan click → "Automation on"; pills "asks first" + "Pro plan" | beckoning |
| 39.05–41.2 | SETUP comment karo… setup bhej dunga | Cobalt CTA: "Comment" + volt **SETUP** box | jumping |
| 41.2–42.7 | — | FollowCard @replyinbox.in | — |

### R02: "Claude ko Instagram se connect karo" · keyword CLAUDE · 36.2 s · VO 1.2x · `saas/content/reels/r02/`

| In–Out | VO (Hinglish) | Visual | Pose |
|---|---|---|---|
| 0.0–3.0 | Claude ko apne Instagram se connect karo… kuch hi minute mein | Instagram ⟷ Claude tiles with a dotted line filling; title with volt "Instagram"; coral pill | pointing at viewer |
| 3.0–7.7 | kya post karna hai… kaunsi reel chal rahi… DMs sambhale | 3 green-tick pills drop in on each phrase (title shrinks to fit) | reading phone |
| 7.7–10.7 | Claude kholo, Connectors… Instagram wahan hai hi nahi | Claude Connectors window, search "Instagram" typed → "No results" (loss red) | scratching head |
| 10.7–12.5 | Zyadatar log… yahin ruk jaate hain | ✋ + "Zyadatar log / **yahin ruk jaate hain.**" (coral) | stop palm |
| 12.5–13.6 | Asli move ye hai | "ASLI" + volt "MOVE" stamp + cobalt underline | arms crossed smile |
| 13.6–16.75 | ReplyInbox pe login… Settings mein Claude link banao | STEP 1: login window → Settings "Connect Claude" → Create Claude link → Copied ✓ | phone |
| 16.75–21.15 | custom connector… naam do ReplyInbox… link paste… Add | STEP 2: connector dialog; then the link line lights cobalt with the ReplyInbox tile + "✓ Connected" | beanbag laptop |
| 21.15–23.1 | top reels ka breakdown | **Real screen** `reel-report.jpg`, crop x270 y60 1000×640, slow push-in | hand on chin |
| 23.1–24.5 | kaunsi reel se followers aur sales | **Real screen** `sales.jpg`, crop x270 y90 1000×640 | hand on chin |
| 24.5–25.2 | poore hafte ka content plan | 7-day grid pop | presenting |
| 25.2–26.55 | har reel ka comment-to-DM | **Real screen** `wizard-keyword.jpg`, crop y150 560×520 | presenting |
| 26.55–28.7 | DMs ke reply draft | **Real screen** `ai-inbox.jpg`, crop x270 y180 1000×620 | laptop typing |
| 28.7–30.55 | Sab kuch… tumhare ek haan pe | Claude "Plan ready… Kar doon?" → Haan click; pills "asks before every change" + "Pro plan · Illustration" | thumbs up |
| 30.55–31.8 | Bilkul is reel ki tarah | Phone mock-up of this reel: comment "CLAUDE" → "DM sent: setup + prompts" | peace sign |
| 31.8–34.76 | CLAUDE comment karo… setup aur ready prompts DM | Cobalt CTA: volt **CLAUDE** box + "DM: setup + ready prompts" | jumping |
| 34.76–36.2 | — | FollowCard @replyinbox.in | — |

Real screens carry a "REAL SCREEN · DEMO DATA" pill (they show the demo banner).

## 11. Toolchain notes and gotchas (learned on R01/R02)

- **Workspace:** `/home/user/replyinbox-reels/`, with one shared `node_modules` and one folder per reel (`rNN/` symlinks `node_modules`).
  - Shared helpers live in `src/kit.tsx`: Drop, Stamp, Cursor, Typed, Window, Card, Pill, Btn, Logo, ClaudeMark, Dots.
  - Scenes, timeline and CHARS (pose per time range) live in `src/Reel.tsx`.
- **Browser:** `/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell`.
  - Always pass `--public-dir=$PWD/public` to `remotion render`, and `publicDir` to `bundle()` in `stills.mjs`. Otherwise every image 404s.
- **Hooks:** never call `useT()` / `useCurrentFrame()` inside a conditional or `&&` in JSX (React error #310). Read the frame once at the top of the scene.
- **No speech recognition here:** huggingface.co and openaipublic are blocked by the network policy.
  - Read the reference script from its burned-in captions: grab frames at 2–4 fps, crop the caption band, and review sheets.
  - Time our VO by pauses: `silencedetect -38 dB / 0.1 s`, plus a second pass at `-30 dB / 0.07 s` for short pauses.
  - Map lines to pause-separated segments using syllable counts (≈ 8 syllables/s at 1.2x) and energy-peak counts.
  - Ask Om to watch captions once.
- **Audio prep:**
  1. `cut_silence.py in out 0.16 0.06` (keeps 0.16 s gaps).
  2. `atempo` R.
  3. `loudnorm`.
  4. `build_audio.py` adds ticks per word, clicks + whooshes on `cuts`, kicks on `drops`, and the lo-fi bed. Edit the `cuts`/`drops` lists per reel.
  5. Final `loudnorm I=-14` + `afade` out 0.4 s on the rendered MP4.
- **Length:** final = VO length + 1.4 s FollowCard. Pick R so that VO ≤ limit − 1.5 s.
- **Character PNGs:** upscale with `comic.hd(path, 1300)`, then a white (MaxFilter 15) + cobalt (MaxFilter 29) outline → `public/chars/<pose>.png`. Wide poses look small; prefer portrait/half framing on busy scenes.
- **Covers:** `saas/tools/story.py` with a one-frame spec (`cover/cover.json`), headline + "COMMENT KEYWORD" link pill + bubble.
- **Unverifiable claims:** e.g. "in 2 minutes" became "kuch hi minute mein". Keep a "Claude asks before every change" and "Pro plan" pill whenever Claude acts.
