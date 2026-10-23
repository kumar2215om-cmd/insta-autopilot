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
1. **Keywords**: only comments that contain one of these trigger a reply (case doesn't matter).
   Leave it empty to reply to every comment.
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

## Notes and limits
- If the follow check itself fails (an API error), the link is still sent and the error appears in the activity feed,
  so nobody gets stuck.
- Button labels can be at most 20 characters (an Instagram limit).
- Each comment is handled only once. Your own comments and replies inside threads are ignored.
- Instagram allows **one DM per comment, within 7 days**. Normal messaging rules apply after that.
- The access token expires after 60 days. On Vercel it renews itself every week (see above). Elsewhere, refresh it with
  `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=TOKEN`.
- Stats are cached for 60 seconds (`STATS_CACHE_SECONDS`) to stay under API rate limits.
