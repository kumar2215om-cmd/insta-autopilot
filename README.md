# Insta Autopilot

A ManyChat-style "comment to get the link" flow for your reels:

1. Someone comments the keyword, for example **LINK** → it replies in public: *"Check your DM @user 📩"*
2. It DMs them: *"Hey! Tap below to get it 👇"* with a **[Send me the link]** button
3. They tap → it checks whether they **follow you**
   - **Following** → they get the link
   - **Not following** → *"Follow me first 👀"* with **[Open profile]** and **[I followed ✅]** buttons.
     Tapping "I followed" checks again.

The button step is required: Instagram only lets an app check whether someone follows you
after that person has interacted with the DM. ManyChat works the same way.

You set the keywords and messages for **each reel** from a dashboard. The dashboard also shows **live stats**: followers, and views, reach, likes, comments, shares and saves for each reel, plus a live activity feed.

It uses Instagram's **official API**, so your account is not at risk the way it would be with password-based bots.

## Requirements
- An Instagram **Business or Creator** account. It's free: Settings → Account type.
- A free Meta developer app.
- A public HTTPS URL for the webhook. For testing, use `ngrok http 8000`. To keep it running, deploy to Render, Railway, Fly.io or a VPS.

## Setup (one time)
1. Go to https://developers.facebook.com/apps → **Create app** → choose **Other** → **Business**.
2. Add the **Instagram** product → **API setup with Instagram login**.
3. Under **Generate access tokens**, add your Instagram account and generate a token.
   It needs these permissions: `instagram_business_basic`, `instagram_business_manage_comments`,
   `instagram_business_manage_messages`, `instagram_business_manage_insights`.
4. Copy `.env.example` to `.env` and fill in `IG_ACCESS_TOKEN`, `IG_APP_SECRET` (App settings → Basic),
   a random `IG_VERIFY_TOKEN` and a `DASHBOARD_PASSWORD`.
5. Run the app:
   ```bash
   pip install -r requirements.txt
   python app.py              # dashboard at http://localhost:8000
   ngrok http 8000            # in a second terminal; gives you https://xxxx.ngrok.app
   ```
6. In the Meta app, open **Configure webhooks**:
   - Callback URL: `https://xxxx.ngrok.app/webhook`
   - Verify token: the same value as `IG_VERIFY_TOKEN`
   - Subscribe to the **comments**, **messages** and **messaging_postbacks** fields,
     then turn on webhook subscription for your account.
7. In the Instagram app on your phone, go to Settings → Messages and story replies → Message controls →
   **Connected tools** and turn on **Allow access to messages**.
8. While the Meta app is in development mode, it only works for accounts added as testers or app roles.
   To make it work for everyone who comments, switch the app to **Live** in the dashboard.
   That needs App Review for the permissions above, and Advanced Access for comments and messages.

## Run 24/7 on Vercel (free)
1. On vercel.com: **Add New → Project** and import this GitHub repo. Keep the defaults, since Vercel detects Flask.
2. **Storage:** in the project, open **Storage → Create Database → Upstash (Redis)**, use the free plan
   and connect it to the project. This adds the `KV_REST_API_URL` / `KV_REST_API_TOKEN` variables,
   and the app then stores rules and activity there instead of on disk.
3. **Settings → Environment Variables:** add `IG_ACCESS_TOKEN`, `IG_APP_SECRET`, `IG_VERIFY_TOKEN`,
   `DASHBOARD_PASSWORD` (always set a password, because the dashboard is public) and `CRON_SECRET`
   (any long random string), then **Redeploy**.
   With `CRON_SECRET` set, a weekly Vercel Cron job (`vercel.json`) renews the Instagram token, so it never
   expires. If you paste a new `IG_ACCESS_TOKEN` later, the app switches to it.
4. In the Meta webhook settings, set the Callback URL to `https://<project>.vercel.app/webhook` and click
   **Verify and save**.

On Vercel, comments are handled before the app answers Instagram, because a serverless function stops once it responds.

## Run 24/7 on Railway
1. On railway.com: **New Project → Deploy from GitHub repo** and pick this repo.
2. **Variables:** add `IG_ACCESS_TOKEN`, `IG_APP_SECRET`, `IG_VERIFY_TOKEN`, `DASHBOARD_PASSWORD`
   (always set a password, because the dashboard is public on a server) and `DATA_DIR=/data`.
3. **Volume:** right-click the service → **Attach volume** with mount path `/data`. This keeps your rules
   and activity log when the app redeploys.
4. **Settings → Networking → Generate Domain** gives you `https://<name>.up.railway.app`.
5. In the Meta webhook settings, change the Callback URL to `https://<name>.up.railway.app/webhook`
   and click **Verify and save**.

The `Procfile` starts the app with gunicorn. Keep it at one worker, because the stats cache lives in memory.

## Usage
Open the dashboard. Under any reel, open **Auto comment + DM rule** and fill in:
1. **Keywords**: only comments containing one of these words trigger a reply. Matching is forgiving:
   capitals, emojis, punctuation, plural "s", repeated letters and one typo don't matter
   (`PROMPTS` matches prompt, Prompts!!, promt, pormpt 🔥; `OTTO` matches Ootto). It matches whole words, so
   `AI` won't fire on "said". Leave it empty to reply to every comment.
2. **Public comment reply**: one per line, for example `@{username} Check your DM 📩`. A random line is
   used each time, which keeps replies looking natural. Lines without `{username}` get the @mention added in front.
3. **Opening DM + button text**. Leave them empty to use the defaults.
4. **Must follow me first**, plus the "follow me" message and button text
5. **Final DM**: the link or reward

`{username}` is replaced with the commenter's name. If you untick "Must follow me first"
and leave the opening DM empty, the final DM is sent straight away with no button.

The **Rule for ALL reels** box is a fallback for reels that don't have their own rule.

**📨 Send to past comments** (on the card of a reel that has a rule) runs the rule on comments left before the automation was
set up. Instagram only allows a DM reply within 7 days of a comment, so older comments are skipped. Each
comment is handled once, so the button is safe to click again. It handles up to 50 comments per click.

## Follower growth
The dashboard shows followers gained today (Indian time) and a 7-day table: followers, gained, reel views,
followers per 1,000 views, and **followers from automation**, meaning people who followed after the "Follow me first" DM
and then got the link (also shown per reel). A snapshot is taken whenever stats refresh and once a day by the
daily Vercel Cron job. Reel views are counted for the latest 12 reels.

When a comment DM is refused, the public reply asks people to **follow + DM the keyword**. Rules still using the
first version of that reply ("your DM didn't come through…") switch to the follow-first text automatically.

## Link-in-bio page
A Linktree-style page for your Instagram bio at `/links` (for example `https://<project>.vercel.app/links`).
Edit it at `/links/edit`, or with **🔗 Link page** on the dashboard (password protected):
- profile: name, bio and photo (your Instagram name and photo are used when left empty), plus 5 colour themes
- social buttons for Instagram, YouTube, WhatsApp, email, X and your website
- **links** and **products** (image, price, "Get it" button); ⭐ featured items glow; hide, reorder or delete any item
- click counts for every item (each tap goes through `/go/<id>`, which counts it and redirects)
- a pulsing **Follow @you on Instagram** button under your bio

Only `http(s)`, `mailto:` and `tel:` links are accepted. Images are links to pictures hosted elsewhere.

## Notes and limits
- Sometimes Instagram refuses to open a DM from a comment (error 2534001, "thread owner has archived or
  deleted this conversation"), often after many automated DMs in a short time. The app sends the DM first; if it's
  refused, the public reply asks the person to **DM you the keyword** instead (step "!" in the rule). When someone
  DMs a keyword, the app answers in that conversation with the same button → follow check → link flow, which works
  even while comment DMs are refused. Refused DMs are also retried once a day (Vercel Cron) or with
  **🔁 Retry failed DMs**, while Instagram's 7-day window is open.
- The follow gate is strict: the link is only sent once Instagram confirms the person follows you. If the check
  fails (an API error), they get the "follow me first" message instead and can tap "I followed" to be checked again;
  the error appears in the activity feed.
- Button labels can be at most 20 characters (an Instagram limit).
- Each comment is handled only once. Your own comments and replies inside threads are ignored.
- Instagram allows **one DM per comment, within 7 days**. Normal messaging rules apply after that.
- The access token expires after 60 days. On Vercel it renews itself every week (see above). Elsewhere, refresh it with
  `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=TOKEN`.
- Instagram limits how many requests an app makes per hour (error code 4, "Application request limit reached").
  After one such error the app stops calling Instagram for 15 minutes, leaves new comments unhandled so
  **📨 Send to past comments** can answer them afterwards, and shows a banner on the dashboard.
- After 15 refused comment DMs in a row (error 2534001), comment DMs pause for 30 minutes; commenters get the
  "Follow + DM me KEYWORD" reply instead. While paused, one test DM is tried every 5 minutes, and DMs resume as soon
  as Instagram accepts one. If Instagram logs the app out (error 190, e.g. after a password change), a red
  banner explains how to reconnect and comments are kept until then.
- Stats are refreshed at most every 10 minutes (`STATS_CACHE_SECONDS`) for the latest 12 reels (`STATS_REELS`),
  because each reel costs one request against the same hourly limit. The retry list holds at most 1,000 people.
