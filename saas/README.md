# ReplyInbox (formerly LikhoDM): comment-to-DM for any Instagram creator

The multi-account version of Insta Autopilot. Creators click **Continue with Instagram**, pick a reel, a
keyword and a link, and get the same flow: public comment reply → DM with a button → follow check → link.

It's a separate Flask app from the one in the repo root (Om's own site, courses and link page), using the
**same approved Meta app** (LikhoDm).

## What's in it
- `app.py`: pages, Login with Instagram, dashboard API, webhook, Meta deauthorize / data-deletion callbacks,
  daily token-renewal cron, `/owner` list of connected accounts.
- `engine.py`: keyword matching (typos, plurals, emojis), rules per reel + keyword rules + all-reels rule,
  comment/DM/button flows, monthly DM limit, per-account rate-limit and logged-out handling.
- `store.py`: Upstash Redis (keys start with `s:`, one prefix per account), in-memory store locally.
- `templates/`: landing page, dashboard, privacy/terms/data-deletion pages, owner page.
- `test_saas.py`: tests with Instagram mocked: `cd saas && python3 -m unittest test_saas`.

## Brand (11 Nov 2026)
- **Logo:** `templates/_logo.html` (`logo.mark(size, id)`, `logo.wordmark(size, id, dark)`, `logo.favicon`): a message bubble
  holding a reply arrow, on a violet → coral gradient tile (#7B5CFF → #B05CE8 → #FF7A59). Wordmark "Reply" + violet "Inbox".
- **Type:** Geist (UI and headings), Instrument Serif italic for one accent phrase per headline, Geist Mono for labels.
- **Colour:** ink #0C0B10, paper #F7F5F0, violet #6A4CFF (ink #4B2FE6, lavender #B9A8FF), coral #FF7A59.
- **Social share image:** `static/og.png` (1200×630), used by the Open Graph / Twitter tags on the landing page. Source:
  `brand/og.html`; re-render with Playwright at 1200×630, deviceScaleFactor 1.
- **App shell** (`_base.html`): dark ink sidebar with the gradient mark, grouped nav (Workspace / Grow and sell / Account)
  with a gradient active marker, warm paper canvas, white 18px cards, mono uppercase labels, the first stat tile in ink,
  gradient progress bars, a "Get Pro free" referral nudge. Page templates only use the shared tokens (`--accent`, `--line`…).
- **Landing** (`landing.html`): dark hero with the product UI, stat strip, bento feature grid, how it works, pricing + compare
  table, FAQ, final CTA, footer. Entrance animations run once and are off under `prefers-reduced-motion`.

## App sections (new design, 12 Nov 2026)
Sidebar app built on `templates/_base.html` (violet look from the design canvas): Home (`/app`), Automations
(`/app/automations`), Reel report (`/app/report`), Link in bio (`/app/links`, public page at `/<username>`, clicks via
`/<username>/go/<id>`), Contacts (`/app/contacts`, CSV at `/api/contacts.csv`), Apps (`/app/apps`, switches sections on/off
in `acc["apps"]`) and Settings (`/app/settings`: auto-setup template, Connect Claude, pause, disconnect).
- **Demo mode:** `/demo` logs into a sample account (`demo.py`) with made-up reels, automations, contacts and a link page.
  The demo account never calls Instagram (engine.Instagram answers from `demo.ig_get`).
- Contacts are saved from the automation itself (`store.touch_contact`): comment, DM keyword, button tap / follow.

## Team access (Settings → Team)
Owners invite up to 5 people as **Manager** (everything except `/api/disconnect`, `/api/team`, `/api/mcp-key`) or **Viewer**
(read-only; only `/api/onboarding` and `/api/guard/test` may POST). An invite is a one-time link `/join/<token>` valid 7 days
(only `sha256(token)` stored as `s:join:<hash>`); GET shows the invite, POST joins (so link previews don't use it up). The session
then holds `uid` + `member`; `current_account()` logs them out as soon as the owner removes them (`acc["team"]`).

## Onboarding checklist (Home)
`onboarding_steps(acc)`: connect, first automation, test (an ok DM in activity), link page, bio link (creator ticks "I did it"),
auto-setup, AI FAQ (if the AI Inbox app is on). Hidden when all done or dismissed (`acc["onboarding"]`).

## Templates
Automations → "Start from a template": Free guide, Lead magnet (email), Course launch (phone + follow-up), Giveaway entry,
Story link, Brand collabs. Client-side only (`TEMPLATES` in `automations.html`): fills the form as a draft; nothing is saved
until Save, and saving is blocked while a field still contains `https://your-link.com`.

## Weekly summary (Home)
`store.count` also adds to a per-day hash `s:t:<id>:day:<YYYY-MM-DD>` (India date, kept 40 days; monthly `x:YYYY-MM` counters
are skipped). `GET /api/week` returns the last 7 days vs the 7 before for DMs, links, follows, replies, emails, phones, AI
replies, follow-ups, story replies, hidden comments, and a 14-day daily series (Home bar chart).

## A/B test of the first DM
A rule with `opening_dm_b` sends version A or B at random (`engine.opening`); the button payload carries it
(`GET|<rule>|<media>|<A|B>`). Counters in `s:t:<id>:ab:<rule>`: `sent_*`, `tap_*` (once per person), `link_*` (once per person),
`follow_*`; the person's version is remembered 7 days (`abv:<igsid>:<rule>`). Changing either text resets the test.
The form shows the table and says which is ahead after 30+ sends each. `GET /api/ab`.

## Automation schedule
Every automation can have `starts_at` / `ends_at` (Unix seconds, optional; form: "Schedule"). `engine.is_live(rule)` is used
everywhere a rule is matched, so outside its window it behaves as off (a reel with its own scheduled rule still doesn't fall
through to the all-reels rule). People already mid-flow (button tapped) still get their link.

## Giveaway picker (`/app/giveaway`)
Pick a post → rules (keyword, number of @tags, "only people who followed through a DM follow gate" from Contacts, exclude
list, 1–20 winners) → `engine.pick_winners` reads up to 2,000 comments, gives each person one entry (never the creator),
and draws with `secrets.SystemRandom`. The last 10 draws are kept (`s:t:<id>:giveaways`). **Announce winners** replies
under each winner's comment and DMs them (private reply, only within 7 days of the comment).

## Comment guard
Settings → Comment guard (`acc["guard"]`: `enabled`, `links`, `words`): every new comment and thread reply is checked first
(`engine.guard_hides`); a match is hidden with `POST /<comment_id>?hide=true` and skips the automation. Counter
`hidden_comments`, activity action `comment_hidden`; `/api/guard/test` checks a sample comment.

## Chat menu (ice breakers)
Automations → Chat menu: up to 4 questions (80 chars) shown when someone opens the creator's DMs for the first time
(`acc["ice"]`, published with `POST me/messenger_profile` `{"platform": "instagram", "ice_breakers": [...]}`, removed with
`DELETE me/messenger_profile` `fields=["ice_breakers"]`). Tapping one sends a postback `ICE|<n>` → the written answer, or the
chosen keyword automation (`engine.handle_ice`).

## Story replies and mentions
- Rule `story:reply` (Automations → Stories): someone replies to a story → the same DM flow (button, follow gate, link).
  Keywords optional (empty = every story reply); once per person per story. A keyword automation in the reply wins;
  replies the rule doesn't cover go to the AI agent. Webhook: `message.reply_to.story`.
- Rule `story:mention`: someone mentions the creator in their story (`attachments[].type == "story_mention"`) → one DM per
  person per day (usually a thank-you). Counters `story_replies`, `story_mentions`; contacts get source `story` / `story_mention`.
- Story rules never answer ordinary DMs (`engine.dm_keyword_match` skips `story:` keys).

## Email and phone capture
Rule options **Ask for their phone / WhatsApp number** (`ask_phone`, `phone_dm`, `phone_required`) work like the email ones and
are asked after the email. Phones are stored in international form (`engine.parse_phone`: 10-digit Indian mobiles get +91);
Contacts links them to wa.me and the CSV has a phone column. Counter `phones`.
Rule option **Ask for their email** (`ask_email`, `email_dm`, `email_required`): after the button / follow check, the DM asks
for an email (with a "Skip" quick reply unless required) and waits 24 h (`s:t:<id>:wait_email:<igsid>`). The next DM with an
email saves it to Contacts (`emails` counter) and sends the final DM; a non-email gets one "doesn't look like an email" per
10 minutes; a keyword starts that automation instead. People whose email is already saved aren't asked again.

## Follow-up offer (freebie → paid)
Rule option **Follow-up offer** (`followup_on`, `followup_hours` 1/3/6/12/20, `followup_dm`, `followup_url`, `followup_button`):
after the final DM, one more DM (with a link button) is queued in the sorted set `s:followups`. It's sent once per person per
automation (30 days), and skipped if Instagram's 24-hour window (counted as 23 h from the link) has passed.
- No job runner: due follow-ups are sent after every webhook (`send_due_followups`), by `/cron/followups` and by the daily cron.
  **On Vercel Pro, add an hourly cron for `/cron/followups`** (Hobby only allows daily crons) so quiet accounts get theirs on time.
- A rule with a follow-up (or email capture) always uses the DM button, which opens the chat the follow-up needs.

## Send to past comments and retry refused DMs
- **Send to past comments** (button in a reel's automation form, `POST /api/reels/<id>/past-comments`, MCP
  `send_to_past_comments`): runs the automation on that reel's comments from the last 7 days (Instagram's private-reply
  window), up to 50 per click; each comment is still handled only once.
- **Refused DMs:** when Instagram won't open a chat from a comment (error 2534001), the comment goes to `s:t:<id>:retry`
  (max 500). The daily cron and **Retry now** on the Automations page (`POST /api/retry`, MCP `retry_refused_dms`) try again
  for 6 days, then drop it.

## Auto-setup and Reel report
- **Auto-setup new reels** (dashboard card): the creator saves a template once (reply, DM, follow gate, final DM with
  `{keyword}`). When a reel posted *after* switching it on says "Comment GUIDE" (a word in capitals or quotes after
  comment/type/likho, or "GUIDE comment karo"), its rule is created automatically: on the reel's first comment (caption read
  once per reel per day) or when the dashboard loads the reel list. A banner offers Review and Undo; undone reels are never
  set up again. Parser: `engine.caption_keyword`.
- **Reel report** (`/report`): for the latest 12 reels, views (Instagram insights) → comments → used the keyword → got the DM
  → link sent → followed to unlock, follows per 1K views, rank, and "Reel Doctor" tips (`engine.reel_tips`, rule-based, not AI).
  Per-reel counts are stored in `s:t:<id>:m:<media_id>` from the moment a reel's automation runs; button payloads now carry
  the reel (`GET|<rule>|<media_id>`). Cached 10 minutes; ↻ Refresh fetches again.

## AI DM agent and AI Inbox (`/app/inbox`)
DMs that aren't one of the creator's keywords go to the AI (`engine.handle_ai_dm`, `ai_agent.py`) when it's switched on.
- Claude (`AI_MODEL`, default `claude-haiku-5-5`, effort low; Opus/Sonnet models also get server-side refusal fallbacks) reads the last 12 messages and answers from the
  creator's Link-in-bio products/prices, automation links, "About you" and FAQ, in the fan's language (or a fixed one). It returns
  JSON `{reply, needs_human, reason, suggested_reply}`; it never invents prices or links.
- **Hand-over:** refunds, collabs and anything unsure (the creator's list) mark the chat **Needs you** with a suggested reply; one
  holding message is sent; the AI then stays quiet in that chat. Refusals, errors and the monthly limit hand over too.
- When the creator replies from the inbox, the chat becomes **You** (AI out) until **Hand back to AI**. Replies only within
  Instagram's 24 hours of the fan's last message.
- Storage: `s:t:<id>:threads` (hash igsid → row), `s:t:<id>:chat:<igsid>` (last 40 messages); removed on disconnect.
- **Try it** box (`/api/ai/test`) shows an answer without sending. Demo account: sample answers, no API call.
- **Plans:** free accounts get a one-time trial of `FREE_AI_TRIAL_REPLIES` (default 25, counter `ai_total`); accounts with
  `"plan": "pro"` get `PAID_MONTHLY_AI_REPLIES` per month (default 1000, counter `ai:<YYYY-MM>`); `"ai_limit": N` on an account
  overrides with N per month. When used up, new DMs are handed to the creator. Set `"plan"` by hand until billing exists.
- Env: `ANTHROPIC_API_KEY` (required; without it AI can't be switched on), optional `AI_MODEL`. Cost on Haiku 5.5: about
  ₹0.04 per reply (~2.5K input tokens), so 1,000 replies ≈ ₹35.

## Connect Claude (MCP server)
`POST /mcp` is a Model Context Protocol server (Streamable HTTP, JSON responses, stateless), so creators can run
ReplyInbox from claude.ai (Settings → Connectors → Add custom connector), Claude Desktop or Claude Code.
- Dashboard card **Connect Claude** creates a per-account key `ri_…` (shown once; only its SHA-256 is stored as
  `s:mcpkey:<hash>` → account). The connector link is `https://<PUBLIC_URL>/mcp?key=ri_…`; Claude Code can send it as
  `Authorization: Bearer ri_…`. A new link or Disconnect revokes the old key; deleting the account removes it.
- Tools (`mcp_tools.py`): get_account_summary, list_reels, get_reel_report, list_automations, save_automation,
  set_automation_enabled, delete_automation, get_recent_activity, pause_all_automations.
- Protocol code: `mcp_protocol.py` (identical copy at the repo root for Om's app; keep them the same).
- Costs nothing extra: Claude usage is on the creator's own Claude plan; each tool call is a normal request here.

## How events reach it
Instagram sends **every** connected account's webhook events to the one callback URL set in the Meta app,
which stays pointed at the root app (`/webhook`). The root app answers only Om's account and forwards
the rest, signature included, to this app's `/webhook` when `SAAS_WEBHOOK_URL` is set.
No Meta webhook change needed.

## Go live (one time)
1. **Vercel → Add New → Project →** import the same GitHub repo, and set **Root Directory = `saas`**.
2. **Storage:** connect the same Upstash database (keys don't clash) or a new one.
3. **Environment variables** (Settings → Environment Variables), then Redeploy:

   | Name | Value |
   |---|---|
   | `IG_APP_ID` | Meta app → Instagram → API setup with Instagram business login → **Instagram app ID** (not the Facebook App ID) |
   | `IG_APP_SECRET` | the **Instagram app secret** from the same page (same value as the root project) |
   | `IG_VERIFY_TOKEN` | same value as the root project |
   | `SECRET_KEY` | any long random string (keeps people logged in) |
   | `CRON_SECRET` | any long random string |
   | `OWNER_PASSWORD` | password for `/owner` |
   | `PUBLIC_URL` | this project's address, e.g. `https://replyinbox.in` |
   | `CONTACT_EMAIL` | shown on the privacy, terms and data-deletion pages |
   | optional | `BRAND_NAME` (default LikhoDM), `FREE_MONTHLY_DMS` (default 1000, 0 = no limit), `SIGNUPS=invite` + `INVITE_CODES=BETA1,BETA2` for an invite-only beta |
4. **Meta app → Instagram → API setup with Instagram business login → Business login settings:**
   - OAuth redirect URI: `https://<PUBLIC_URL>/auth/callback`
   - Deauthorize callback URL: `https://<PUBLIC_URL>/meta/deauthorize`
   - Data deletion request URL: `https://<PUBLIC_URL>/meta/data-deletion`
5. **Root project (Om's app) → Environment Variables:** `SAAS_WEBHOOK_URL=https://<PUBLIC_URL>/webhook`, Redeploy.
6. **Test:** log in with a second Instagram Business/Creator account, set up a rule on one of its reels,
   comment the keyword from a third account, and watch the activity feed.

If Meta asks for **Access verification (Tech Provider)** in the app dashboard, complete it: it's required
for apps used by businesses other than the app owner.

## Saved replies (AI Inbox)
`acc["saved_replies"]` (up to 30 × {title, text}), edited in the AI Inbox's "Saved replies" panel (`GET/PUT /api/saved-replies`).
They show as buttons above the reply box; tapping one fills the box with `{username}` replaced.

## Several Instagram accounts in one login
Every owner login adds the account to `session["accounts"]` (up to 10). The sidebar's "Switch account" menu lists them
(`POST /api/switch`, only accounts this browser logged in to) and "Add another Instagram account" (`/login?add=1`, skips the
beta invite code). Disconnecting one account keeps you logged in to the others; Log out ends them all.

## Copy an automation
"Copy to…" in an automation form → pick reels and / or type new keywords. `POST /api/rules/<key>/copy`
`{"targets": [...], "replace": false}` copies everything except the auto-setup flag and label; keyword targets get their own
word. Reels that already have an automation are skipped unless "replace" is ticked.

## Link page signup form
Link in bio → "Signup form" (`page["signup"]`: enabled, ask email / phone / both, heading, button, thank-you, optional link).
The public page posts to `/<username>/join`: validated with `engine.parse_email` / `parse_phone`, a hidden honeypot field
drops bots, one signup per minute per IP, saved with `store.touch_contact(..., source="bio_page")`, counter `page_signups`.

## Referrals
Invite link `/r/<username>` (or `/?ref=<username>`) remembers the referrer in the session; the landing page then says who
invited them. When a **new** account is created at login (`reward_referral`), both accounts get 30 days of Pro
(`acc["pro_until"]`, stacked; the referrer earns at most 12 free months). `store.is_pro(acc)` = `plan == "pro"` or
`pro_until` in the future; it drives the DM and AI limits. Settings → "Invite creators" shows the link, a WhatsApp share and
who joined (`GET /api/referrals`).

## Plans (landing page pricing)
- **Free:** `FREE_MONTHLY_DMS` (1,000) DMs a month, `FREE_AI_TRIAL_REPLIES` (25) AI replies once, every feature.
- **Pro (₹299/month, "launching soon" until billing exists):** account field `"plan": "pro"` → `PRO_MONTHLY_DMS`
  (default 0 = no ReplyInbox limit) and `PAID_MONTHLY_AI_REPLIES` (1,000). Set by hand for now; `"dm_limit"` / `"ai_limit"`
  on an account override both. Keep `templates/landing.html` in sync if these change.

## Limits and notes
- One DM per comment, within 7 days of the comment (Instagram rule). The follow check only works after the
  person taps a button in the DM, which is why the first DM has one.
- Meta's rate limits apply per connected account. After a rate-limit error the account pauses for 15 minutes.
- If an account's login breaks (password change, app removed), it stops and the dashboard asks to log in again.
- The free plan's monthly DM limit is `FREE_MONTHLY_DMS`. Per-account limits can be set by adding
  `"dm_limit": N` to that account's record (`s:t:<id>`); billing isn't built yet.
- Don't add rules for Om's own account here: the root app already answers it.
