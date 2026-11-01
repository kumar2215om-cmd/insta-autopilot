# START HERE · Insta Autopilot: dashboard, link page & freebies (handoff)

Owner: Om · Instagram **@aiwith.om** ("AI Tools & Tips Daily", Hinglish).
Scope of this handoff: the **Insta Autopilot web app**: admin dashboard, link-in-bio page + editor, `/free` freebies page, guide pages, uploads, themes and animations.
**Not included:** reel making/editing (the Remotion studio in `/home/user/aiwithom/template`). That has its own v3 handoff.

Last updated: 1 Nov 2026 (v2) · see `git log` for the latest commit.

---

## 1. Where things live

| What | Where |
|---|---|
| Live app | https://insta-autopilot-ten.vercel.app |
| Public link page (put in IG bio) | https://insta-autopilot-ten.vercel.app/links |
| Freebies page | https://insta-autopilot-ten.vercel.app/free/ (deep link: `/free?k=KEYWORD`) |
| Admin dashboard (password) | https://insta-autopilot-ten.vercel.app/ |
| Link page editor (password) | https://insta-autopilot-ten.vercel.app/links/edit |
| GitHub repo | `kumar2215om-cmd/insta-autopilot` (branch `main`) |
| Hosting | Vercel project `insta-autopilot` (team "om", Hobby). **Every push to `main` auto-deploys** (~1 min). |
| Storage | Upstash Redis (`upstash-kv-coral-diamond`) for rules/link page/activity · Vercel Blob `insta-autopilot-blob` (Private) for uploaded freebie files |

Deploy = `git push origin main`. No build step: Flask on Vercel's Python runtime.

---

## 2. Code map (repo root)

```
app.py                     Flask app: Instagram webhook automation, APIs, link page, freebies, uploads
templates/
  _admin_style.html        Shared admin CSS (freebies-style palette, sidebar shell, buttons, inputs, admin motion)
  _admin_nav.html          Shared admin sidebar (Overview / Link page / Freebies + public page links)
  dashboard.html           Admin "Your overview": KPIs, follower growth, reels + comment→DM rules, live activity
  links_edit.html          Link page editor: profile, theme, socials, links & products, 🎁 Freebies (upload), live preview
  links.html               PUBLIC link page (/links): freebies-style layout, 6 themes, animations
freebies/
  index.html               PUBLIC /free page. Data is a JSON blob `const D={...};\n` inside the file (57 built-in items)
  theme.css                Theme colours + motion for the guide pages (linked by the server)
  avatar.png, og.png       Avatar + social share preview (og:image 1200×630)
  guides/                  8 HTML guides + CHAT.html, 11 PDFs, 4 kit zips, img/
vercel.json                Crons only (token refresh Mon 03:00, retry failed DMs 04:30)
README.md, .env.example    Setup notes; env var names
```

### Routes added/changed today
| Route | Auth | What |
|---|---|---|
| `GET /free` | public | 301 → `/free/` (keeps query string) |
| `GET /free/` | public | `freebies_index()`: static page + editor freebies merged **on top** (`pin: true`), theme class injected, `Cache-Control: no-store` |
| `GET /free/guides/*.html` | public | `themed_guide()`: adds `theme.css` + `t-THEME` body class + scroll-reveal script, no-store. Path-checked against escaping the folder |
| `GET /free/f/<pathname>` | public | Streams a file from the **private** Blob store (`serve_private_blob`), only under `freebies/` |
| `GET /free/uploads/<name>` | public | Local-disk uploads (only when Blob isn't configured, i.e. local dev) |
| `GET /free/<other>` | public | Static files from `freebies/` (Cache-Control 300) |
| `POST /api/freebies/upload` | password | Upload (pdf zip png jpg jpeg webp gif mp4 txt md csv json, **≤ 4 MB**: Vercel's body limit is 4.5 MB) |
| `GET/PUT /api/linkpage` | password | Link page data incl. `theme` and `freebies[]` |

Public-path whitelist lives in `check_password()` (`/links`, `/free`, `/free/…`, `/go/…`, `/webhook`, `/cron/…`). Everything else needs the basic-auth `DASHBOARD_PASSWORD`.

### Data shapes
Link page (`load_linkpage()` / `clean_linkpage()`), stored in Redis (or `linkpage.json` locally):
```json
{"name":"Om | AI Tools & Tips Daily","bio":"…","avatar":"","theme":"studio",
 "socials":{"instagram":"aiwith.om","youtube":"","whatsapp":"","email":"","x":"","website":""},
 "items":[{"id":"a1","type":"product|link","title":"","url":"","subtitle":"","price":"149","image":"","featured":true,"enabled":true}],
 "freebies":[{"id":"x","k":"CHAT","t":"Title","topic":"Free tools","e":"🎁","u":"/free/f/freebies/file-abc.pdf","enabled":true}]}
```
- Freebie keyword `k`: uppercase A–Z0–9, ≤ 24 chars. `u` must be an https link or start with `/free/uploads/` or `/free/f/`.
- Items/freebies missing title/link are dropped on save (the editor tells you how many).
- `theme` ∈ `studio` (default) · `sunset` · `midnight` · `ocean` · `candy` · `mono`.
- Link page also shows `followers_count` (from the IG profile call, cached 1 h) and the freebie count (`freebies_count()`).

---

## 3. Environment variables (names only, values live in Vercel → Settings → Environment Variables)

`IG_ACCESS_TOKEN`, `IG_APP_SECRET`, `IG_VERIFY_TOKEN`, `IG_API_VERSION`, `DASHBOARD_PASSWORD`, `CRON_SECRET`,
`UPSTASH_REDIS_REST_URL`/`_TOKEN` (or `KV_REST_API_URL`/`_TOKEN`),
**`BLOB_READ_WRITE_TOKEN`, `BLOB_STORE_ID`, `BLOB_WEBHOOK_PUBLIC_KEY`** (added today by connecting the Blob store),
optional: `STATS_CACHE_SECONDS`, `STATS_REELS`, `ACCOUNT_CACHE_SECONDS`, `DM_AUTO_PAUSE`, `DATA_DIR`, `LINKPAGE_FILE`, `RULES_FILE`, `DB_FILE`.

### Vercel Blob: how uploads work (set up today)
- Store **`insta-autopilot-blob`**, region iad1, access **Private**, connected to Production + Preview.
- Upload: `PUT https://vercel.com/api/blob/?pathname=freebies/<name>` with headers `authorization: Bearer <token>`, `x-api-version: 13`, `x-vercel-blob-store-id`, `x-vercel-blob-access` (tries `public`, then `private`), `x-add-random-suffix: 1`, `x-content-type`. Mirrors the official `@vercel/blob` SDK.
- Auth: `BLOB_READ_WRITE_TOKEN` if set, else the Vercel OIDC token (`x-vercel-oidc-token` header / `VERCEL_OIDC_TOKEN`) + `BLOB_STORE_ID`.
- Private files are served through the app at `/free/f/freebies/<file>` (GET `https://<storeId>.private.blob.vercel-storage.com/<pathname>` with the bearer token).
- ⚠️ **Don't click "Revoke Token"** on the Blob store page: the app uses that token.

---

## 4. Design system (shared by every page)

Freebies style ("cream / rose"):
- Colours: bg `#F1EADC`, ink `#1C1A17`, rose `#FF2D95`, cerulean `#007BA7`, mute `#8C8780`, line `#E7E0D4`, cards `#fff`, shadow `0 18px 40px rgba(60,40,20,.14)`.
- Fonts: **Inter 900** headings with a rose `<span>` highlight ("Saare freebies, **ek jagah**"), **Anton** for big keyword/number text, small cerulean UPPERCASE letter-spaced labels ("COMMENT KEYWORD").
- Avatar: conic ring `rose → #F5B83D → cerulean`. Buttons: black "Follow", rose "Open/Kholo/Get it".
- Admin pages use the same palette (`_admin_style.html` tokens), sidebar with rose active item.

### Themes
One setting (editor → Profile → Theme) drives **all public pages**: `/links` (`links.html` CSS vars per `.t-<theme>`), `/free` (body class injected by `freebies_index`, vars in `index.html`), guides (`theme.css`). `studio` = the original cream look. Admin pages don't change with the theme.

### Animations (all pages, all CSS + tiny JS, all disabled under `prefers-reduced-motion`)
- **Link page:** spinning avatar ring + ripple, chip pop-in + icon wave + brand colour on hover, Follow glow/sweep/wiggle, freebies card (ring, bobbing gift, sparkles, pulsing count, nudging arrow), product cards (swinging bag, shine, image zoom, pulsing Get it, featured ring), link cards (staggered slide-in, tilting letter tile, nudging arrow).
- **/free:** same avatar/Follow/chip effects; cards rise in on load and on topic change (not on every keystroke); bobbing emoji, shine, NEW pulse, nudging Kholo; **exact keyword match gets a glowing ring**.
- **Guides:** header pop/rise/wiggle, nav chips pop in, sections reveal on scroll (IntersectionObserver; jumping reveals skipped sections; without JS everything just shows), sliding tips, hover lifts, glowing end card.
- **Dashboard/editor:** spinning logo ring, sliding nav, cards rise in, shine on rose buttons, KPI numbers **count up** and pop rose when they change (`countTo()`), reels rise in on first load only, **new activity items slide in once** (tracked by key so the 5-second refresh doesn't replay them).

---

## 5. Everything done today (in order)

1. **/free freebies page** in the app, rebuilt as Om's own guides/kits (57 cards, search, topic chips, `?k=` deep link) + "🎁 Free guides & kits" button on `/links` + og share image + share images for Instagram (story/post).
2. **🎁 Freebies editor section** in `/links/edit` with **⬆️ Upload file** (later: keyword typing bug fixed: the card no longer re-draws while typing).
3. **Vercel Blob uploads**: works with the Private store (OIDC or token); private files served via `/free/f/…`.
4. **Redesign** of dashboard + editor (sidebar app layout, KPI tiles, step-by-step rule builder, section tabs, floating save bar, **Link page / Freebies preview switch**).
5. **Public link page redesign** in the freebies style + new default `studio` theme, follower count, freebie count, share button, ₹ auto-prefix on numeric prices, broken product images hide themselves.
6. **Admin pages in the freebies style.**
7. **Uploaded freebies always first** on /free (pinned, NEW tag), `/free/` never cached.
8. **Animations** on link page (Follow, freebies card, products, links, socials, avatar), /free, guides, dashboard + editor.
9. **Theme follows everywhere**: /free and all guide pages use the editor's theme.

10. **CLAUDE.md** in the repo root so every new Claude Code session understands the app (points here).
11. **All freebies moved onto our site:** the 37 cards that opened Notion / claude.ai were rebuilt from their PDFs as FACTORY-style guides (`tools/guides_src/batch1–8*.py`). Every card on `/free` now opens `/free/guides/…`. New card **MOBILE** (#60). Related guides cross-link (SENIOR → CODING → TOKENS, FIX ↔ SAFE, FIX → RULES → CONTRACT).
12. **Wide tables** on guide pages scroll inside their card on phones (no sideways page scroll).
13. **Write freebie guides in the editor:** 📝 box on each freebie card (template, toolbar, image upload, preview) → live at `/free/g/KEYWORD`. No Notion needed for future freebies.
14. Outside the repo (in the handoff zip, `instagram_profile_kit/`): highlight covers, About me / Freebies / Tips / Tutorials / Reviews / Collab / Results / AI Tools highlight stories, profile mockup and copy-ready bio.

Commits (oldest → newest): `db7add4 c75bfb4 a9715ae 12140bb 099f5f7 733a2d7 e24c992 afe0633 a31c821 e753f50 47c4b70 56720d9 c8e1afa 59b0094 141875f c229b62 d7587f0 eff74db b6e395c 4f282f7`.

---

## 6. How to… (common tasks)

**Add a freebie (no code):** `/links/edit` → 🎁 Freebies → ＋ Add freebie → keyword, title, topic, emoji → ⬆️ Upload file (≤ 4 MB) or paste a link → **💾 Save page** → check with the 🎁 Freebies preview tab. DM link to use in auto-DMs: `https://insta-autopilot-ten.vercel.app/free?k=KEYWORD`.

**Write a new freebie guide on the site (no Notion):** `/links/edit` → 🎁 Freebies → ＋ Add freebie → keyword + title → open **📝 Write the guide here** → ✨ Start with template (or the toolbar: Section, Tip, Warning, Prompt box, Code box, Steps, Table, Image) → **👀 Preview** → **💾 Save page**. It goes live at `/free/g/KEYWORD` and the card links there automatically. Syntax: first line = intro, `## Heading` = new card, `> 💡 …` tip, `> ⚠️ …` warning, ```` ```prompt ```` pink copy box, ```` ```terminal ```` code box. Stored as `body` (Markdown, ≤ 60k chars) on the freebie in Redis; rendered by `render_editor_guide()` → `tools/md2guide.py:md_to_page` (raw HTML is escaped). Needs the `markdown` package (requirements.txt).

**Add a built-in freebie (code):** edit the `const D={"items":[…],"topics":[…]}` JSON in `freebies/index.html` (keep it on one line ending with `;\n`, give it the next `n`), put the file in `freebies/guides/`, push.

**Make a new HTML guide:** the generator lives outside the repo at `/home/user/aiwithom/linkbio/_build/guidepage.py` (copy in the handoff zip under `tools/guide_builder/`). `page(kw, title1, title2, intro, sections)` with blocks `p, code, list, ol, tip, warn, cmds, table, repo, prompt, img, plugs`. Write the output to `freebies/guides/KEYWORD.html`, add a card to `index.html`, push. Theme + animations are applied automatically by the server.

**Guides rebuilt from Notion / claude.ai PDFs:** every freebie now opens on our own site. Their sources live in `tools/guides_src/batch*.py` (one file per batch, written with `tools/guidepage.py` blocks); re-run a batch file from the repo root to regenerate its pages and re-point the `/free` cards. `tools/md2guide.py` converts a Markdown/Notion export directly. Keyword clashes: CLAUDE #12 = `CLAUDE_VIDEO.html`, CLAUDE #26 = `CLAUDE.html`; AUTO + OOTTO share `AUTO.html`. MOBILE (#60) was added as a new card.

**Change colours/animation:** public link page → `templates/links.html`; /free → `freebies/index.html` (theme block + motion block at the end of `<style>`); guides → `freebies/theme.css`; admin → `templates/_admin_style.html` (+ page-specific `<style>` in `dashboard.html` / `links_edit.html`).

---

## 7. Testing locally (what worked today)

```bash
pip install flask requests            # (use --ignore-installed blinker if pip complains)
D=$(mktemp -d); DATA_DIR=$D DASHBOARD_PASSWORD= python3 -c "import app; app.app.run(port=5055)"
```
- Flask caches templates: **restart the server after editing a template**.
- Dashboard needs Instagram: mock `/api/stats`, `/api/activity`, `/api/rules`, `/api/retry-failed` with Playwright `page.route(...)` (Chromium is preinstalled; `require('playwright')`).
- To fake the IG profile on `/links`: `app._profile_cache.update(at=9e12, data={...})` before `run()`.
- Freeze animations for screenshots: `document.getAnimations().forEach(a => { a.pause(); a.currentTime = T })`.
- The cloud sandbox's proxy **can't reach the live vercel.app site**: verify live changes in a real browser.

## 8. Gotchas learned today
- `freebies_index()` finds the data by `const D=` … `;\n`: don't reformat that line. Inject anything that changes length (theme class) **before** computing those indices.
- Replace the real body tag only (`'<body>\n<div class="wrap">'` / regex `<body>(?=\s*<main)`): a CSS comment once contained `<body>` and got replaced instead.
- Infinite CSS animations with `forwards` fill block hover transforms: use `backwards` fill for entrance animations.
- Re-rendering lists (`innerHTML`) restarts CSS animations: gate entrance animations behind a temporary class (`intro`) or a "seen" set.
- Vercel function body limit 4.5 MB → uploads capped at 4 MB (bigger files: paste a Google Drive link).
- Browser cache was why a saved freebie "didn't show": `/free/` and guides are now `no-store`.

## 9. Open items / reminders
- Point SuperProfile / auto-DM messages at `insta-autopilot-ten.vercel.app/free?k=KEYWORD`.
- Older guide links (#1–38, outside this app) need their public access checked.
- Notion connector isn't connected (was blocked in the sandbox).
- Delete any TEST freebie added while trying uploads; Om's saved theme was `candy` at last check: pick **studio** for the exact freebies look.
- Idea backlog: per-freebie click counts on /free, drag-to-reorder in the editor, image upload for product cards via Blob.

## 10. House rules
- No secrets in code or commits; env var **names** only.
- Commit attribution lines are required on commits; never put model IDs in commits/PRs/code.
- Keep Hinglish, friendly copy on public pages; keep the cream/rose freebies look as the default.
