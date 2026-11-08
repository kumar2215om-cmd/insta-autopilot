# LikhoDM: comment-to-DM for any Instagram creator

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
   | `PUBLIC_URL` | this project's address, e.g. `https://likhodm.vercel.app` |
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
