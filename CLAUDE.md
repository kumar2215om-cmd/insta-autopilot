# Insta Autopilot · notes for Claude

Om's (@aiwith.om) Instagram automation app + link-in-bio site. Flask on Vercel; **push to `main` = deploy** (~1 min).
Full handoff (routes, data shapes, env var names, Blob uploads, design system, themes, animations, gotchas): **docs/HANDOFF.md**. Read it before changing anything.

## Map
- `app.py`: everything server-side: IG webhook comment→DM automation, `/api/*`, `/links`, `/free`, guides, uploads.
- `templates/dashboard.html` (admin overview), `templates/links_edit.html` (link page editor), `templates/links.html` (public link page),
  shared admin look in `templates/_admin_style.html` + `_admin_nav.html`.
- `freebies/index.html`: public `/free` page; its data is the one-line JSON `const D={...};` (keep it one line ending `;\n`).
- `freebies/theme.css`: theme + motion for guide pages. `freebies/guides/`: guides, PDFs, kit zips.

## Rules
- Look: cream/rose "freebies style" (bg #F1EADC, ink #1C1A17, rose #FF2D95, cerulean #007BA7; Inter 900 + Anton). One editor theme setting drives /links, /free and guides; `studio` is the default.
- Every animation must stay off under `prefers-reduced-motion`; don't replay entrance animations on periodic re-renders.
- Public paths are whitelisted in `check_password()`; everything else needs `DASHBOARD_PASSWORD`.
- Uploads ≤ 4 MB (Vercel body limit). Blob store is **private**: files are served via `/free/f/…`. Never revoke the Blob token.
- No secrets in code/commits (env var names only). Keep public copy Hinglish and friendly.
- Not in this repo: reel making/editing (separate Remotion studio). Guide generator: `tools/guide_builder` in the handoff zip.

## Test locally
`D=$(mktemp -d); DATA_DIR=$D DASHBOARD_PASSWORD= python3 -c "import app; app.app.run(port=5055)"`. Restart after template edits (Jinja caches).
Mock `/api/stats`, `/api/activity`, `/api/rules`, `/api/retry-failed` with Playwright for the dashboard. The live vercel.app site may be unreachable from a cloud sandbox.
