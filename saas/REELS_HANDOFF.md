# @replyinbox.in: Reel Pipeline Handoff

Updated 21 Nov 2026. **Status:** the pipeline is set up; no ReplyInbox reel has been made yet.

Read this together with Om's `HANDOFF_aiwithom.md` (the @aiwith.om reel pipeline). This file only lists what is different for ReplyInbox.

---

## 1. Who / what

- **Account:** **@replyinbox.in**, the Instagram page for ReplyInbox (replyinbox.in), Om's Instagram DM automation SaaS.
- **Format:** faceless Hinglish reels, **9:16 (1080×1920)**, built in code with Remotion, the same way as @aiwith.om.
- **Idea:** Om sends a **reference reel**. We keep its script word for word, but the product it promotes becomes **ReplyInbox** ("our tool").
- **Voice:** Om records the voiceover MP3 from our script. @aiwith.om uses the ElevenLabs "Aman – Indian male" voice; use the same voice unless Om says otherwise.
- **Ending:** every reel ends with "Comment KEYWORD" (an auto-DM sends the guide or link) and a **@replyinbox.in FollowCard**.

## 2. Workflow (per reel)

1. **Reference reel in**
   - Transcribe it (Whisper small q8, Hindi + English) and make a frame grid.
   - Fact-check it.
   - Write the voiceover script with the **exact hook and structure**, and swap the promoted tool/brand for ReplyInbox.
   - Only change what is false, stale, or something ReplyInbox doesn't do. **List every change for Om.**
2. **Product truth check.** Every ReplyInbox claim must exist on the live site: compare with `saas/plans.py`, `saas/templates/landing.html` and `saas/seo_content.py` on `main`. If the reference promises a feature we don't have, rewrite that line to a real feature, or tell Om.
3. **MP3 + length limit in.** Build the reel (§4).
4. **Post-production** (same as @aiwith.om):
   - render
   - loudnorm −14 LUFS
   - cut silences
   - speed up to land under the limit (1.2x default, up to 1.35x)
   - no trailing silence after the FollowCard
5. **Deliverables:**
   - reel MP4 + cover PNG inline
   - ZIP with the reel, cover, caption TXT and `automation.json` (comment-to-DM rule, same format as `saas/content/carousels/*/automation.json`)
   - a guide PDF/TXT if the keyword promises one
6. **Logging:** there is no ReplyInbox reel tracker yet. Ask Om whether to add a "ReplyInbox Reels" database in Notion (same columns as the @aiwith.om Reel Tracker) or reuse that tracker with a page column.

## 3. Standing rules

**Look: ReplyInbox brand only** (Om's choice, 21 Nov 2026). Do not use @aiwith.om's cream/rose.

| Token | Hex | Use |
|---|---|---|
| Paper | `#F5F4EF` | background, with a dot grid (ink at ~13% opacity, 48–54 px spacing) |
| Ink | `#111318` | text, 4–6 px outlines, hard offset shadows (8–14 px) |
| Cobalt | `#2E3BFF` | main accent, key words, CTA screens, logo tile |
| Volt | `#D4FF3A` | highlighter behind the key word of a headline, pill tags, numbered circles |
| Coral | `#FF5B3A` | "the catch" / problem beats |
| Mist | `#E6E5DE` | panels, chat bubbles |
| Win | `#16A34A` | — |
| Loss | `#E5484D` | — |

- **Fonts:**
  - Bricolage Grotesque 800: headlines, punch words, captions.
  - Manrope 600–800: body text.
  - JetBrains Mono 700: labels, numbers, keywords, the handle.
  - Noto Sans Devanagari only where Hindi script is shown.
- **Style:** the comic / neo-brutalist look of `saas/tools/comic.py`: ink-outlined cards and chat bubbles with hard shadows, a volt highlighter, pill tags. Phone/DM mock-ups go on cards, not floating text.
- **Logo:** solid cobalt tile with the white bubble + reply arrow (`saas/templates/_logo.html` `mark()`). No violet/coral gradients any more.
- **Character (optional):** Om's 90 cut-out poses, `saas/content/characters/om/` (index `characters.json`, slide roles in `roles.json`). Add the white + cobalt sticker outline in code. The poses are low-res (~150–300 px), so upscale (`comic.hd()`) and keep them ≤ ~700 px tall on screen.
- **Density** (same as @aiwith.om): no blank screens. Each line gets a big visual (~900 px wide, y 400–1400) and a big punch word. Word-by-word headline captions at the top, with key words in cobalt or on volt.
- **Motion and SFX** (same as @aiwith.om):
  - drop + squash, scramble counters, stamps, hard cuts
  - per-word ticks, a click on every cut, a kick on every drop
  - a light lo-fi bed
- **Instagram safe zones:** keep text out of the top ~250 px and bottom ~300 px.

**Honesty**
- Real proof only. Use real ReplyInbox screenshots from Om, cropped. Never invent numbers, testimonials or results.
- A mock-up of the product UI must look like the real app and be labelled as an illustration if it shows made-up data.
- Competitor names and prices only as they appear (dated) in `saas/seo_content.py`, hedged ("about", "as checked Nov 2026").
- Credit the reference creator in the caption: `Idea credit: @handle`.
- Skip or push back on references built on false facts, or that need features ReplyInbox doesn't have.

## 4. Build recipe

- **Toolchain** (installed 21 Nov 2026 in `/home/user/replyinbox-reels/`, **outside the repo**; the container can be wiped, so always send deliverables to Om):
  - Node 22: `remotion@4.0.545`, `@remotion/cli`, `@remotion/media-utils`, `react@18`, `@fontsource/{bricolage-grotesque,manrope,jetbrains-mono,anton,noto-sans-devanagari}`, `@huggingface/transformers` (Whisper)
  - Python: numpy, soundfile, Pillow
  - ffmpeg 6.1
- **Rebuild** if the folder is gone:
  ```
  mkdir -p /home/user/replyinbox-reels && cd /home/user/replyinbox-reels && npm init -y
  npm install remotion@4 @remotion/cli@4 @remotion/media-utils@4 react@18 react-dom@18 @fontsource/bricolage-grotesque @fontsource/manrope @fontsource/jetbrains-mono @fontsource/anton @fontsource/noto-sans-devanagari @huggingface/transformers
  pip install numpy soundfile Pillow
  ```
- **Project files:** the same layout as the @aiwith.om reels.
  - `src/Scenes.tsx`, `src/Reel.tsx`, `src/FollowCard.tsx` (@replyinbox.in), `src/kit.tsx` (FPS 30), `src/brand.ts` (the tokens above)
  - `head.py` → `src/data.json` captions, `build_audio.py` → `public/mix.wav`
  - `stills.mjs` (contact sheet by frame), `cut_silence.py`, `doc2pdf.py`
  - Never call `useT()` conditionally.
- **Render** (the browser path for this container):
  ```
  npx remotion render src/index.ts Reel out/raw.mp4 --codec=h264 --crf=16 --audio-codec=aac --audio-bitrate=320k \
    --browser-executable=/opt/pw-browsers/chromium_headless_shell-1243/chrome-linux/headless_shell --concurrency=4
  find /tmp -maxdepth 1 -name 'remotion-*' -exec rm -rf {} +
  ```
  Then do loudnorm, cut silences and set the speed exactly as in `HANDOFF_aiwithom.md` §4.
- **Covers:** 1080×1920 stills in the brand. Put a "Comment KEYWORD" pill in the safe zone. `saas/tools/story.py` already lays out a branded 1080×1920 frame and can be reused for covers.

## 5. Product facts to use (checked on `main`, 21 Nov 2026)

- **Comment → DM automation:** keyword on a reel/post/Live/story. Public reply + DM, follow to unlock, email/WhatsApp capture, follow-ups.
- **Link in bio** with a freebies page.
- **Store + courses:** sales page, student dashboard, certificates; also files, event tickets and 1:1 calls.
- **Payments:** add a bank account once; buyers pay by UPI or card; money goes to the creator's bank.
- **AI agents** (AI DM replies in the fan's language) and **MCP** (run it from Claude, from the Pro plan).
- **Plans** (₹/month):

  | Plan | Price | Fee per sale |
  |---|---|---|
  | Free | ₹0 | 5% + GST |
  | Starter | ₹149 | 5% + GST |
  | Creator | ₹199 | 5% + GST |
  | Pro | ₹599 | 2% + GST |
  | Agency | ₹2,000 | 2% + GST |

  Always say "+ GST" with the fees.
- Official Meta API, no password needed. Free plan: 1,000 DMs/month.

## 6. Related content already made (branch `seo-launch`)

- **Carousels:** `saas/tools/carousels.py` (classic) and `saas/tools/comic.py` (comic), for all 63 guides, comparisons and features in `saas/content/comic/replyinbox/`. Captions + `automation.json` per page.
- **Pinned posts:** comment-to-dm (COMMENTDM), ai-dm-agent (AGENT), manychat (MANYCHAT).
- **Stories:** `saas/tools/story.py`.
  - `content/stories/replyinbox/promo-2026-11/` (4 frames)
  - `promo-1page-2026-11/` (1 frame, "Link in bio")
- **Keywords already used by carousels** (see `KEYWORDS` in `saas/tools/carousels.py`): don't reuse one for a reel unless the reel promotes the same guide.

## 7. Open items

- **Waiting on Om:**
  1. The first reference reel.
  2. The voiceover MP3 and length limit.
  3. Real ReplyInbox screenshots for proof.
- **To decide:** where to log ReplyInbox reels (§2.6).
- **@aiwith.om reel carousels** (from the Notion Reel Tracker): paused by Om on 21 Nov 2026.
