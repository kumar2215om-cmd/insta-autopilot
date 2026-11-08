# Handoff: Insta Autopilot (@aiwith.om)

Last updated: 8 Nov 2026. Read this first, then `README.md` for setup and feature details.

## What this is
A self-hosted, ManyChat-style Instagram automation for the creator account **@aiwith.om**
(Hindi/English AI content, about 15K followers). It sells the **PromptBundle** (39 AI video prompt packs)
at https://promptbundle.store/.

The flow: someone comments a keyword on a reel → public reply ("check your DM") → a DM with a button →
a follow check ("follow me first") → the link. A dashboard shows live stats, follower growth and activity,
and there is a Linktree-style link page.

## Where things live
| What | Where |
|---|---|
| Code | GitHub `kumar2215om-cmd/insta-autopilot`, branch `main` (pushing deploys automatically) |
| Hosting | Vercel project → https://insta-autopilot-ten.vercel.app/ (dashboard, password protected) |
| Link page | https://insta-autopilot-ten.vercel.app/links (public), editor at `/links/edit` |
| Storage | Upstash Redis, connected through Vercel (`KV_REST_API_URL` / `KV_REST_API_TOKEN`) |
| Meta app | **LikhoDm** (Instagram API with Instagram Login), developers.facebook.com |
| Webhook | `https://insta-autopilot-ten.vercel.app/webhook` (fields: comments, messages, messaging_postbacks) |
| Business | Udyam registered; Meta business verification done; site https://likholabs.in/ |

## Status
- **Meta App Review: APPROVED (8 Nov 2026).** All four permissions have Advanced Access:
  `instagram_business_basic`, `instagram_business_manage_messages`, `instagram_business_manage_comments`,
  `instagram_business_manage_insights`. The app is **Published (Live)**, so it now works for every commenter,
  not just testers.
- **While review was pending, automations moved to SuperProfile AutoDM.** It has about 10 automations
  (1K+ DMs sent, 800+ followers gained). In our dashboard, every reel covered by SuperProfile is set to
  **paused**, and the "Rule for ALL reels (fallback)" is **not set (off)**. Only the reviewers' test reel
  (keyword **PROMPTS**) was left enabled.
- **Rule: never run both tools on the same reel.** Instagram allows one private reply (DM) per comment,
  so they would collide, and each comment would get two public replies.

## Next steps after approval
1. **Change `DASHBOARD_PASSWORD`** in Vercel → Settings → Environment Variables, then Redeploy.
   The old one was shared with Meta's reviewers.
2. **Test our app as a normal user.** From an account that is not an app tester, comment PROMPTS on the
   test reel. Check that the DM arrives and that the activity feed shows no `2534001` errors.
   Advanced Access should fix most of the DM refusals seen before approval.
3. **Choose per reel which tool runs it.** To move a reel back to our app: turn its automation off in
   SuperProfile, then enable its rule in our dashboard (Auto comment + DM rule → Enabled → Save rule).
   Move one reel first and watch for a day before moving the rest.
4. **Old retry queue.** It showed about 17K pending DMs from before approval. Items older than 6 days
   expire on the next daily cron (`/cron/retry-failed`), and paused rules drop their retries. If a big
   backlog remains, do not mass-retry; it burns the hourly request limit.
5. **Keep prices consistent.** Website ₹399; SuperProfile payment page was set at ₹199, and a story offer
   used ₹149. Whatever the current offer is, the website, payment page, DMs and stories should match, and
   "limited time" offers need a real end date.

## How the code is organised
- `app.py`: Flask app, everything server-side.
  - Webhook (`/webhook`): HMAC check with the app secret, then `handle_comment`, `handle_button`
    (postbacks) and `handle_dm_text` (someone DMs a keyword). On Vercel, work runs inline before replying.
  - Matching: `keyword_matches` is forgiving (case, emojis, plurals, one typo if the word has 5+ letters
    and the first letter matches, adjacent swaps).
  - Rules: one per reel id, plus `*` as the fallback. A paused reel rule does **not** fall through to `*`.
  - Safety: code 190 (token invalid) and codes 4/17/32/613 (rate limit, 15-minute backoff) are detected in
    `_check`; comments are not claimed while either is active. `DM_AUTO_PAUSE=1` is optional and off.
  - Crons (`vercel.json`): weekly token refresh, daily retry of refused DMs plus a follower snapshot.
    Both need `CRON_SECRET`.
  - Stats: reel insights are cached for 10 minutes (latest 12 reels), the follower count every 2 minutes.
- `templates/dashboard.html`: dashboard (stats, growth, reel cards, rule forms, live activity).
- `templates/links.html`, `templates/links_edit.html`: link page and its editor.
- `story/`: Instagram story images for the prompt pack offer (`story.html` + frames, rendered with
  Playwright to `story_1.png` / `story_2.png`).

## Environment variables (Vercel)
`IG_ACCESS_TOKEN`, `IG_APP_SECRET`, `IG_VERIFY_TOKEN`, `DASHBOARD_PASSWORD`, `CRON_SECRET`,
plus the Upstash variables Vercel adds. Optional: `DM_AUTO_PAUSE`, `STATS_CACHE_SECONDS`, `STATS_REELS`,
`ACCOUNT_CACHE_SECONDS`. Values are only in Vercel. Never paste them into chat, code or screenshots.

## Known gotchas
- **Changing the Instagram password invalidates the token** (error 190). Fix: generate a new token in the
  Meta app (Instagram → API setup → Generate token), paste it into `IG_ACCESS_TOKEN`, Redeploy.
- **Rate limit:** Meta allows a limited number of requests per hour per connected account (about 200
  before approval). Viral reels can hit it; the app then backs off for 15 minutes and shows a banner.
  **📨 Send to past comments** catches up on missed comments within 7 days.
- **DMs only within 7 days of a comment**, one per comment.
- **Button labels:** max 20 characters (Instagram limit).
- Do not remove the app from Instagram → Settings → Apps and websites, and keep the Meta webhook
  subscription on, or everything stops.

## Ideas not started
- SaaS version (many accounts): needs per-user Instagram login, a real database, a send queue and billing.
  The approved Meta app is the hard part that is now done.
- Story-reply and DM-keyword automations as separate rule types.
