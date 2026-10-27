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

Rules still using the earlier default public replies switch automatically to the new ones that also ask people to follow.

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
  deleted this conversation"), often after many automated DMs in a short time. The normal public reply still posts,
  refused DMs are retried once a day (Vercel Cron) or with **🔁 Retry failed DMs** while Instagram's 7-day window is
  open, and people who DM you the keyword are answered in that chat with the same button → follow check → link flow.
- Meta's app-level limit is about 200 Instagram requests per hour per connected account. Each keyword comment uses
  roughly 2-3 requests, so very busy reels can hit the limit; the app then waits 15 minutes (see below).
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
- Every keyword comment gets a DM attempt and the normal public reply (the default replies also ask people to
  follow). DMs that Instagram refuses (error 2534001) are retried later, and people who DM the keyword are answered
  in that chat. Optional: set `DM_AUTO_PAUSE=1` to pause comment DMs for 30 minutes after 15 refusals in a row
  (one test DM every 5 minutes; **▶️ Resume DMs now** lifts it). If Instagram logs the app out (error 190, e.g.
  after a password change), a red banner explains how to reconnect and comments are kept until then.
- Reel stats refresh every 10 minutes (`STATS_CACHE_SECONDS`) for the latest 12 reels (`STATS_REELS`), loaded in parallel;
  the follower count refreshes every 2 minutes (`ACCOUNT_CACHE_SECONDS`) and **↻ Refresh** forces a full update after 30 seconds,
  because each reel costs one request against the same hourly limit. The retry list holds at most 1,000 people.

## LinkedIn: scheduled posts + comment automation
Open **💼 LinkedIn** on the dashboard (`/linkedin`). It can:
- **Manage your profile and company pages together:** switch accounts at the top to see each one's calendar,
  scheduled and posted counts, next post, and its own AI voice.
- **Write captions with AI (Claude):** type rough notes, pick a tone (professional, story, bold, friendly, tips,
  news) and length, and get 3 ready posts with a hook, short paragraphs and hashtags. It writes "I" for your
  profile and "we" for a page, looks at the images you attach, and can **improve your own draft**. Set a
  **🎙️ Voice** per account (what you do, who you talk to) so every caption sounds like you. You see a
  LinkedIn-style preview before scheduling.
- **Schedule posts** (text, #hashtags, up to 20 images) to your **profile** or your **company pages**, or post right away.
- On **company page** posts: watch comments for your keywords, **reply in public**, and put each person in a
  **DM queue** with your message ready. Click **📋 Copy**, then **Open comment**, click their name → Message,
  paste, and mark it **✅ Sent**.

**Why DMs aren't sent automatically:** LinkedIn's messaging API is closed to almost all apps, and tools that
auto-DM run a logged-in browser on your account. That breaks LinkedIn's terms and often gets accounts
restricted, so this app only uses the official API. Also, LinkedIn's API can't read comments on **personal
profile** posts, so comment automation works on company page posts only.

### Setup
1. Go to https://www.linkedin.com/developers/apps → **Create app**. LinkedIn requires a company page to link
   the app to; any page you admin works.
2. **Products** tab: add **Share on LinkedIn** and **Sign In with LinkedIn using OpenID Connect**
   (both approved instantly). For company pages, also request **Community Management API**, which LinkedIn reviews.
3. **Auth** tab: under *Authorized redirect URLs*, add `https://<your-domain>/linkedin/callback`
   (`http://localhost:8000/linkedin/callback` for local testing). Copy the **Client ID** and **Client Secret**.
4. For the AI caption writer, create an API key at https://platform.claude.com and add it as `ANTHROPIC_API_KEY`
   (each set of 3 captions costs a few US cents).
5. Add the env variables `LI_CLIENT_ID` and `LI_CLIENT_SECRET`, plus `LI_PAGES=1` once Community Management is
   approved. Redeploy, open `/linkedin` and click **Connect LinkedIn**. After turning on `LI_PAGES`,
   click **Reconnect** so your pages are added.

### When posts go out
- **Railway / a server:** the app checks every minute, so posts go out on time.
- **Vercel:** the free plan's cron runs only once a day. For on-time posts, create a free job at
  https://cron-job.org that opens `https://<project>.vercel.app/cron/linkedin?key=<CRON_SECRET>` every 5 minutes.
  While the LinkedIn dashboard is open in a tab, it also publishes due posts itself.

### Notes
- Profile logins last 60 days, and the dashboard warns you a week before. Apps approved for Community Management
  get a refresh token, so their login renews itself.
- Comments are checked every 5 minutes (`LI_POLL_SECONDS`). Each comment is handled once, and your own comments are ignored.
- LinkedIn doesn't tell the app who commented by name. **Open comment** takes you straight to the comment.
- Links in post text stay as plain text. LinkedIn's API doesn't create link previews by itself.
