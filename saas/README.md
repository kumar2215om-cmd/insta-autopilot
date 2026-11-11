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

## App sections (new design, 12 Nov 2026)
Sidebar app built on `templates/_base.html` (violet look from the design canvas): Home (`/app`), Automations
(`/app/automations`), Reel report (`/app/report`), Link in bio (`/app/links`, public page at `/<username>`, clicks via
`/<username>/go/<id>`), Contacts (`/app/contacts`, CSV at `/api/contacts.csv`), Apps (`/app/apps`, switches sections on/off
in `acc["apps"]`) and Settings (`/app/settings`: auto-setup template, Connect Claude, pause, disconnect).
- **Demo mode:** `/demo` logs into a sample account (`demo.py`) with made-up reels, automations, contacts and a link page.
  The demo account never calls Instagram (engine.Instagram answers from `demo.ig_get`).
- Contacts are saved from the automation itself (`store.touch_contact`): comment, DM keyword, button tap / follow.

## Story replies and mentions
- Rule `story:reply` (Automations → Stories): someone replies to a story → the same DM flow (button, follow gate, link).
  Keywords optional (empty = every story reply); once per person per story. A keyword automation in the reply wins;
  replies the rule doesn't cover go to the AI agent. Webhook: `message.reply_to.story`.
- Rule `story:mention`: someone mentions the creator in their story (`attachments[].type == "story_mention"`) → one DM per
  person per day (usually a thank-you). Counters `story_replies`, `story_mentions`; contacts get source `story` / `story_mention`.
- Story rules never answer ordinary DMs (`engine.dm_keyword_match` skips `story:` keys).

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

## Limits and notes
- One DM per comment, within 7 days of the comment (Instagram rule). The follow check only works after the
  person taps a button in the DM, which is why the first DM has one.
- Meta's rate limits apply per connected account. After a rate-limit error the account pauses for 15 minutes.
- If an account's login breaks (password change, app removed), it stops and the dashboard asks to log in again.
- The free plan's monthly DM limit is `FREE_MONTHLY_DMS`. Per-account limits can be set by adding
  `"dm_limit": N` to that account's record (`s:t:<id>`); billing isn't built yet.
- Don't add rules for Om's own account here: the root app already answers it.
