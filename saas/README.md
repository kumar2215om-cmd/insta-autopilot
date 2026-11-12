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
- **Full access or read-only:** the card picks the mode; the key maps to `<account>` or `<account>|read`. Read-only links
  list and run only `read_only` tools. Every change Claude makes is logged in Activity (action `claude`).
- **Tools** (`mcp_tools.py`, 31). They use the same app functions as the dashboard (`mcp_services()` in app.py), so the
  checks are identical.
  - Overview: get_account_summary, get_trends, get_best_posting_times, list_reels, get_reel_report, get_recent_activity.
  - Automations: list_automations (with stats and sort_by), get_automation, get_automation_insights, save_automation
    (every wizard option: targets reel / keyword / all / next_post / story_replies / story_mentions / live, menu, email
    and WhatsApp capture, follow-up, A/B, schedule in IST, tags, exclude, delay, dm_only), duplicate_automation,
    set_automation_enabled, delete_automation, pause_all_automations, send_to_past_comments, retry_refused_dms.
  - Money: get_sales, add_product, delete_product, set_utm_tags.
  - People and DMs: search_contacts, tag_contacts, list_inbox, get_conversation, reply_in_dm, hand_chat_to,
    broadcast_to_recent_chats (preview unless confirm=true), get_messaging_settings, set_welcome_message,
    update_ai_agent, test_ai_reply.
- **Prompts** (shown in Claude's menu): weekly_review, launch_plan, new_reel_automation, fix_problems, inbox_catchup.
- **Instructions** sent at connect explain ids, ₹/IST, `{username}` and `{a|b}`, Instagram's windows, and to ask before
  sending or deleting.
- Protocol code: `mcp_protocol.py` (identical copy at the repo root for Om's app; keep them the same). Prompts are an
  optional argument, so Om's app is unchanged.
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
   | `SHORT_LINK_URL` | optional: address for click-counting links `/l/<code>` (default `PUBLIC_URL`); set to the vercel.app address while the main domain is down |
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

## Auto DM page (`/app/automations`, sidebar "Auto DM")
Laid out like SuperProfile's AutoDM: stat cards (DMs sent, leads collected, followers gained, with 14-day sparklines from
`GET /api/autodm-summary`), tabs (Automations · Chat menu · Templates), search and filter, and one row per automation with
followers gained / runs / button clicks (`store.rule_count`, hash `s:t:<id>:rs:<rule>`; `GET /api/rules` returns them as
`stats`) and a ⋮ menu (edit, rename, pause, duplicate, comment replies on/off, send to past comments, view on Instagram,
delete). "Create automation" opens a step-by-step wizard: trigger (comment / DM keyword / story reply / story mention) → post
(specific, any, or **next post**) → keywords and 3 rotating public replies → DMs (opening message + button, follow check,
email, WhatsApp, primary DM with an optional link button, follow-up, more options) → review → launch.
- Wizard → rule key: specific post = media id; any post = `kw:WORD` (or `*` for any comment); next post = `next`
  (`engine.attach_next` moves it onto the first reel posted after `since`); DM = `kw:WORD` with `comments: false`; stories
  `story:reply` / `story:mention`. Editing that changes the key deletes the old rule.
- New rule fields: `replies_on`, `dm_button_text`, `dm_button_url` (the final DM is sent as a button template), `since`.
- `/app/automations#<key>` opens that automation in the wizard (used by the Reel report and Home).

## Excluded keywords, once per person, delay, integrations
- `rule["exclude"]`: words that stop the automation (`engine.excluded`), checked for comments, keyword DMs and story replies.
- `rule["once_per_person"]` (on by default in the wizard): one DM per person per automation and post for 60 days.
- `rule["delay_min"]` (0/1/2/5/10): the first comment DM is queued in `s:followups` as `{"kind": "comment_dm"}` and sent by
  `send_due_followups` (after webhooks / cron, like follow-ups; on Vercel Hobby it can run late on quiet accounts). The
  public reply goes right away.
- **Integrations** (Settings, owner only): `acc["hook"] = {url, enabled}`. New leads (email/phone from DMs, link-page signups)
  and DM-gate follows are POSTed as JSON (`event`, `account`, `at`, `username`, `email`, `phone`, `automation`) by
  `engine.send_hook` (4 s timeout, no redirects). `safe_hook_url` only allows https to public IPs. `/api/integrations`,
  `/api/integrations/test`. The card includes a Google Apps Script snippet for Google Sheets.

## Live comments, message variations, activity log
- **Comments on your Live (beta):** rule key `live` (wizard trigger "Comments on your Live"). Webhook field `live_comments`
  goes through `handle_comment` with `_live`, matched by `engine.find_live_rule`; private-reply DM only, no public reply.
  Login subscribes `comments,messages,messaging_postbacks,live_comments` and falls back without `live_comments` if refused.
  **Needs `live_comments` ticked in the Meta app's Instagram webhook fields** (Meta app → Webhooks → Instagram).
- **Variations:** `engine.vary` turns `{Hi|Hey|Hello}` into one option at random in every DM, button-template text and
  public reply (`{username}` is left alone). The wizard's "Account safety" box explains it; the review shows the first option.
- **Activity** (`/app/activity`): the latest 500 events (`store.ACTIVITY_KEEP`), filters (DMs, replies, leads, AI, errors),
  search, `GET /api/activity?all=1`, CSV at `/api/activity.csv`.

## Choice menus, welcome message, link clicks, broadcast, phone app, notifications
- **Let them choose (menu):** a rule's `menu` (≤3 `{title, text, url, button}`) sends the primary DM with postback buttons
  `MENU|<key>|<i>`; `engine.handle_menu` sends that option's message (+ link button) and counts `menu_<i>` in `rs:<key>`.
- **Welcome message** (Auto DM → Welcome): `acc.welcome = {enabled, text, buttons}`; sent once per person (claim
  `welcomed:<igsid>`, 1 year) when a first DM matches no keyword, before the AI agent. Buttons open a link or post
  `KW|<rule key>` to start an automation. `GET/PUT /api/welcome`.
- **Link click counting:** links in DMs (text and buttons) become `<SHORT_LINK_URL or PUBLIC_URL>/l/<code>`
  (`s:link:<code>`, 180 days) and `/l/<code>` redirects, counting `link_clicks` per rule and per day. Off per automation with
  `track_links: false` (wizard → More options), and off entirely when neither URL is set.
- **Broadcast** (Auto DM → Broadcast): `POST /api/broadcast {id, text, url, button}` sends to everyone who messaged in the
  last 23 h (`s:t:<id>:recent`, Instagram's 24-hour window) in batches of 40; the page calls it again until `done`.
- **Phone app:** `/manifest.webmanifest`, icons in `static/`, service worker `/sw.js` (no caching). Install from Settings →
  Phone app and notifications (Android/desktop prompt; iPhone: Share → Add to Home Screen).
- **Notifications:** `push.py` sends Web Push with no payload (VAPID ES256 signed with `cryptography`, key derived from
  `SECRET_KEY`); the service worker shows `/api/notifications/latest`. Sent for new leads (email, phone, signup) and AI
  handoffs, per `acc.notify` prefs. Endpoints only on known push hosts; dead ones (404/410) are removed. iPhone needs the
  installed app (iOS 16.4+).

## Automation insights, sales, UTM tags, health alerts
- **Insights** (Auto DM → ⋮ → Insights, or click the Runs number): `GET /api/rules/<key>/insights` gives 30 days of
  runs, link opens, follows, leads, sales and revenue, a DM-to-sale funnel, busiest hours (India time) and menu picks.
  `store.rule_count` also writes `rsd:<key>` (`<date>|<field>`, days older than 90 pruned on read) and `rsh:<key>`
  (`<hour>|<field>`). `store.move_rule_stats` moves all three when a next-post automation lands on its reel.
- **Sales** (`/app/sales`): the creator adds products (name, ₹ price, optional thank-you page) and pastes each product's
  sales link `/s/<12 hex>` into their payment page as the "redirect after payment" URL. `/l/<code>` sets the `ri_l` cookie
  (last DM link tapped, 30 days); `/s/<id>` credits the sale to that automation (`engine.record_sale`: counts `sales` and
  `revenue` per account, day and automation, logs it, sends the `sale` integration event and a push). One sale per
  `?order=` / `razorpay_payment_id`, else per visitor (`ri_v`) per 10 minutes. No payment details are received.
- **UTM tags:** `/l/<code>` adds `utm_source=instagram&utm_medium=dm&utm_campaign=<automation name>` unless the link
  already has utm_ tags or the creator turned it off (`acc.utm`, Sales page, `PUT /api/utm`).
- **Health alerts** (`engine.alert`, push + activity log, pref `notify.health`): logged out by Instagram (daily), rate
  limited (6 h), 10+ refused comment DMs waiting (`REFUSED_ALERT`, daily), 80% and 100% of the monthly DM limit (once a
  month), and login renewal failing in the daily cron.

## SEO, answer engines and AI assistants (SEO / AEO / GEO)
- **Pages** (`seo_content.py` → `templates/content.html`): `/features` + 6 feature pages, `/compare` + 6 `/vs/<tool>` pages,
  `/guides` + 4 guides. Each starts with a direct answer, has short sections, a FAQ, an "Updated" date, related links and a CTA.
  Competitor facts are dated (`CHECKED`) with a "not affiliated" note; refresh them when competitors change prices.
- **Pillar-cluster (hub-and-spoke) architecture** (`seo_content.PILLARS`): 6 topic hubs at the top level
  (`/instagram-dm-automation`, `/instagram-lead-generation`, `/sell-on-instagram`, `/ai-instagram-dm-replies`,
  `/instagram-dm-automation-tools`, `/instagram-automation-by-industry`). Every feature, comparison and guide belongs to
  exactly one hub (`pillar_of()`): its breadcrumb runs Home → hub → page, it shows "Part of …", and "More in …" links to its
  siblings; the hub links down to every page in its topic and across to the other hubs. `/guides` lists all hubs with
  their pages. Adding a page: write it in FEATURES / COMPARE / GUIDES and add it to one hub's `clusters` (a test enforces this).
- **Entity-first coverage**: `ENTITIES` (Instagram, Meta, WhatsApp, chatbots, lead generation… with Wikipedia `sameAs`)
  are each hub's `about`; `GLOSSARY` defines 25 domain terms on `/glossary` (DefinedTermSet, one anchor per term) that hubs
  link to and every page `mentions` in its Article schema, with `isPartOf` pointing at its hub (CollectionPage + `hasPart`).
- **Structured data (JSON-LD)**: landing page has Organization, WebSite, SoftwareApplication (₹ and $ offers from `plans.py`)
  and FAQPage (read from the landing FAQ itself); content pages have BreadcrumbList, Article and FAQPage.
- **`/robots.txt`** allows everything public (including AI crawlers) and blocks private paths; **`/sitemap.xml`** lists every
  public page; **`/llms.txt`** is a plain summary with prices and links for AI assistants.
- **Private pages** (`/app`, `/api`, `/demo`, `/l`, `/s`, `/owner`, …) send `X-Robots-Tag: noindex`. Creator link pages stay indexable.
- **Canonical address**: `SITE_URL` (env). Unset = the address the request came in on (likhodm.vercel.app today). Set
  `SITE_URL=https://replyinbox.in` only once that domain works, then submit `/sitemap.xml` in Google Search Console and Bing.

## Contact tags
Contacts have `tags` (lower-case, up to 20). An automation's "Tag these people" field (`rule["tags"]`, comma separated, up
to 5) adds tags to everyone who goes through it (comments, keyword DMs, story replies and mentions). Creators edit tags
inline on the Contacts page (`PUT /api/contacts/tags` with the contact `key`), filter by tag, and download a tag's CSV
(`/api/contacts.csv?tag=vip`).

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

## Plans and revenue model (`plans.py`)
All plan numbers live in `plans.py`; `store.is_pro`, `engine.monthly_limit` and `ai_agent.allowance` read them.
| Plan | ₹/month (yearly) | DMs/month | AI replies | Accounts | Fee on sales through ReplyInbox |
|---|---|---|---|---|---|
| free | 0 | 1,000 | 25 once | 1 | 5% + 18% GST, all-in |
| starter (decoy) | 149 (1,499) | 3,000 | 25 once | 1 | 2% + GST + gateway charges |
| creator | 199 (1,999) | no limit | 300/month | 1 | 2% + GST + gateway charges |
| pro | 499 (4,999) | no limit | 2,000/month | 3 | 2% + GST + gateway charges |
| agency | 1,499 (14,999) | no limit | 10,000/month | 10 | 2% + GST + gateway charges |
- Two revenue streams: subscriptions, and a SuperProfile-style platform fee (`plans.platform_fee`; paid plans also pass
  the gateway's charge through at cost, `GATEWAY_FEE_PCT` = 2 by default, or the real fee per payment) on payments collected
  through ReplyInbox (UPI/card in DM, once Razorpay is connected). Sales on the creator's own payment pages (Sales page
  tracking links) carry no fee. **The fee is not shown on the landing page** (owner's decision).
- **US$ prices** (`plans.USD`): Starter $5 ($48/yr), Creator $9 ($84/yr), Pro $19 ($180/yr), Agency $49 ($468/yr); extra
  account $5, AI top-up $2 per 1,000. The pricing page shows ₹ when the visitor's time zone is India, else $; the ₹/$ switch
  remembers the choice (localStorage).
- **Add-ons** (`plans.py`): extra AI replies ₹99 per 1,000; one more Instagram account on Creator or Pro ₹149/month
  (`EXTRA_ACCOUNT`; each Instagram account is its own account here, so this is charged once billing exists).
- **Paid-only features** (`plans.PAID_FEATURES`, checked with `plans.has(acc, feature)`): the follow gate. Locked only
  when `PLAN_LOCKS=on` (set it in Vercel when billing goes live; during the beta every feature is free). With locks on, a
  Free account's automations skip the follow check and send the link, and the wizard shows "Upgrade" instead of the toggle.
- Plans are set by hand on `/owner` (plan picker per account, MRR and plan counts on top) until billing exists. Referral
  months (`pro_until`) count as Pro but not in MRR. `"dm_limit"` / `"ai_limit"` on an account override the plan; the env
  vars `FREE_MONTHLY_DMS`, `FREE_AI_TRIAL_REPLIES`, `PRO_MONTHLY_DMS`, `PAID_MONTHLY_AI_REPLIES` override too when set.
- The landing page shows the four plans (monthly/yearly switch, "launching soon", beta = every feature free) but not the sale fee; keep it in sync with `plans.py`.

## Limits and notes
- One DM per comment, within 7 days of the comment (Instagram rule). The follow check only works after the
  person taps a button in the DM, which is why the first DM has one.
- Meta's rate limits apply per connected account. After a rate-limit error the account pauses for 15 minutes.
- If an account's login breaks (password change, app removed), it stops and the dashboard asks to log in again.
- The free plan's monthly DM limit is `FREE_MONTHLY_DMS`. Per-account limits can be set by adding
  `"dm_limit": N` to that account's record (`s:t:<id>`); billing isn't built yet.
- Don't add rules for Om's own account here: the root app already answers it.
