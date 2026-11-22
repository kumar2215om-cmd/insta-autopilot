# ReplyInbox: Video Editing Handoff (@replyinbox.in reels)

Updated 22 Nov 2026. This is for recreating **competitor SaaS reels** for ReplyInbox.
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
