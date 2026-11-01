"""Guides rebuilt from the Notion PDFs (SENIOR, FIX, CODING, TOKENS, SAFE). Run from repo root."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from guidepage import page
OUT = "freebies/guides"
gh = lambda p: f"[github.com/{p}](https://github.com/{p})"
G = {}

G["SENIOR"] = page("SENIOR", "4 Claude Code plugins", "to install before vibe coding",
 "Thanks for commenting SENIOR! All 4 plugins with links and install commands. Run the commands inside Claude Code.", [
 ("Before you start", "Plugins change fast", [
   ("tip", "If a command fails, check the repo's README for the latest install steps. Part 2 is the [CODING guide](CODING.html), Part 3 is the [TOKENS guide](TOKENS.html).")]),
 ("1 · Superpowers", "1 · Superpowers", [
   ("p", "Stops Claude from jumping straight into code. It brainstorms with you first, writes a spec you approve, then plans the work and has sub-agents build it test-first, so long sessions stay on plan."),
   ("p", f"Repo: {gh('obra/superpowers')} (MIT)"),
   ("code", "Official Claude plugin marketplace", "/plugin install superpowers@claude-plugins-official"),
   ("code", "Or via its own marketplace", "/plugin marketplace add obra/superpowers-marketplace\n/plugin install superpowers@superpowers-marketplace")]),
 ("2 · Karpathy", "2 · Karpathy Skills", [
   ("p", "A single CLAUDE.md inspired by Andrej Karpathy's complaint that models write 1,000 lines when 100 would do. Four rules: **think before coding, keep it simple, touch only what was asked, prove it works.**"),
   ("p", f"Repo: {gh('forrestchang/andrej-karpathy-skills')}"),
   ("code", "Install", "/plugin marketplace add forrestchang/andrej-karpathy-skills\n/plugin install andrej-karpathy-skills@karpathy-skills"),
   ("tip", "Or just copy its CLAUDE.md into your project root.")]),
 ("3 · i-have-adhd", "3 · i-have-adhd", [
   ("p", "Stops Claude from burying the answer. No \"great question\", no \"hope this helps\". Next action first, numbered steps, lists capped at 5."),
   ("p", f"Repo: {gh('ayghri/i-have-adhd')} (MIT)"),
   ("code", "Install (in your terminal)", "claude plugin marketplace add ayghri/i-have-adhd\nclaude plugin install i-have-adhd@i-have-adhd"),
   ("p", "Use: `/i-have-adhd`")]),
 ("4 · Octopus", "4 · Claude Octopus", [
   ("p", "Sends the same task to other AI models (Codex, Gemini, Copilot, Qwen, Ollama, Perplexity, OpenRouter…) and flags where they disagree before you ship."),
   ("p", f"Repo: {gh('nyldn/claude-octopus')}"),
   ("code", "Install", "/plugin marketplace add https://github.com/nyldn/claude-octopus.git"),
   ("p", "Then install the plugin from that marketplace and run `/octo:setup` to detect your providers."),
   ("tip", "The other models need their own CLIs or API keys (optional). Needs a recent Claude Code version.")]),
 ("Workflow", "Suggested workflow", [
   ("ol", ["**Superpowers** → brainstorm and approve the spec.", "**Karpathy rules** keep the code small and focused.",
           "**i-have-adhd** keeps Claude's replies short and actionable.", "**Octopus** cross-checks big decisions before you ship."])]),
])

G["CODING"] = page("CODING", "4 more Claude Code plugins", "(Part 2)",
 "Thanks for commenting CODING! All 4 plugins from Part 2: Supabase, Vercel, oh-my-claudecode and Chrome DevTools MCP. Run the slash commands inside Claude Code.", [
 ("Before you start", "Plugins update often", [
   ("tip", "If a command fails, check the repo's README for the latest steps. Part 1 (Superpowers, Karpathy Skills, i-have-adhd, Claude Octopus) is in the [SENIOR guide](SENIOR.html).")]),
 ("1 · Supabase", "1 · Supabase (official)", [
   ("p", "Connects Claude straight to your Supabase project: run SQL, apply migrations, generate TypeScript types, and check security and performance advisors, without opening the dashboard."),
   ("p", "**Easiest:** open `/plugin` in Claude Code, browse the official marketplace, and install **supabase**. Or add the Supabase MCP server: see supabase.com/docs/guides/getting-started/mcp"),
   ("warn", "Start in read-only mode and on a dev project, not production.")]),
 ("2 · Vercel", "2 · Vercel (official)", [
   ("p", "Say \"deploy my app\" and Claude builds and ships it to a preview or production URL, all from the terminal."),
   ("p", "Open `/plugin` and install **vercel** from the official marketplace, or use Vercel's MCP: vercel.com/docs/mcp. You'll log in to Vercel once.")]),
 ("3 · oh-my-claudecode", "3 · oh-my-claudecode", [
   ("p", "Turns Claude into a team of specialized agents. Type `team` and they plan, write the PRD, build, verify and fix together. There's also autopilot and parallel \"ultrawork\" modes."),
   ("p", f"Repo: {gh('Yeachan-Heo/oh-my-claudecode')}"),
   ("code", "Install", "/plugin marketplace add Yeachan-Heo/oh-my-claudecode"),
   ("p", "Then install it from that marketplace and run its setup command (see the README)."),
   ("tip", "Team features use Claude Code's experimental agent-teams setting, and they use more tokens.")]),
 ("4 · Chrome DevTools", "4 · Chrome DevTools MCP (by Google's Chrome team)", [
   ("p", "Gives Claude eyes on a real Chrome browser: it reads console errors, inspects network requests, takes screenshots and runs performance traces, instead of coding blindfolded."),
   ("p", f"Repo: {gh('ChromeDevTools/chrome-devtools-mcp')}"),
   ("code", "Install (in your terminal)", "claude mcp add chrome-devtools -- npx chrome-devtools-mcp@latest"),
   ("prompt", "Try", "Open localhost:3000, check the console and network for errors, and fix them.")]),
 ("Workflow", "Suggested workflow", [
   ("ol", ["Build with **oh-my-claudecode**'s team.", "Debug in the real browser with **Chrome DevTools MCP**.", "Manage the database with **Supabase**.", "Ship with **Vercel**."])]),
])

G["TOKENS"] = page("TOKENS", "4 Claude Code plugins", "to save tokens",
 "Thanks for commenting TOKENS! The 4 plugins from Part 3: Ponytail, OmniRoute, Graphify and Agent Skills. Run the commands inside Claude Code unless noted.", [
 ("Before you start", "Honest note", [
   ("warn", "Token savings depend heavily on your project. Independent tests show much smaller savings than the marketing numbers, so try them on your own codebase. Repos change often, so check each README for the latest install steps."),
   ("tip", "Part 1 = [SENIOR guide](SENIOR.html), Part 2 = [CODING guide](CODING.html).")]),
 ("1 · Ponytail", "1 · Ponytail", [
   ("p", "Pushes Claude to write less, simpler code (a YAGNI-style \"do we really need this?\" ladder), so you spend fewer tokens and get less bloat."),
   ("code", "Install (send as two separate messages)", "/plugin marketplace add DietrichGebert/ponytail\n/plugin install ponytail@ponytail"),
   ("tip", "There's a known Windows slowdown issue. Check the repo if messages stall.")]),
 ("2 · OmniRoute", "2 · OmniRoute", [
   ("p", "An open-source AI gateway that routes Claude Code to many free-tier providers (Gemini, Groq, Qwen, DeepSeek…). When one limit runs out, it falls back to the next model automatically."),
   ("p", "Find it on GitHub by searching **\"OmniRoute\"** and follow its setup (it runs a local endpoint that Claude Code points to)."),
   ("warn", "**Privacy:** your prompts and code go to third-party providers, each with their own terms. Don't use it for client or confidential code. Free-tier limits also change often.")]),
 ("3 · Graphify", "3 · Graphify", [
   ("p", "Turns your whole codebase into a knowledge graph, so the agent can query structure instead of re-reading files again and again. It helps most on large repos (100+ files)."),
   ("p", "MIT licensed. Search GitHub for **\"graphify\" Claude Code** and follow the README install."),
   ("tip", "Rebuild the graph after big refactors (it can go stale), and check the README for Claude Code version compatibility.")]),
 ("4 · Agent Skills", "4 · Agent Skills (by Addy Osmani)", [
   ("p", "A skill pack that makes Claude work like a senior engineer, with dedicated skills for spec, plan, build, test, review and ship that activate at the right stage."),
   ("p", f"Repo: {gh('addyosmani/agent-skills')} (MIT)"),
   ("code", "Install", "/plugin marketplace add addyosmani/agent-skills\n/plugin install agent-skills@addy-agent-skills"),
   ("p", "Commands: `/spec` `/plan` `/build` `/test` `/review` `/ship`")]),
 ("Free tips", "Free tips that also save tokens", [
   ("list", ["Keep a short, clear **CLAUDE.md** (project rules) so Claude doesn't re-discover things.", "Use `/clear` between unrelated tasks.", "Ask for plans first, then code."]),
   ("p", "Idea credit: @adilet.fndr.")]),
])

G["FIX"] = page("FIX", "One Claude prompt to fix", "6 legal traps in your app",
 "Thanks for commenting FIX! Paste the prompt below into Claude Code, inside your app's repo. It audits your app for the 6 traps and fixes what it can.", [
 ("Before you start", "Not legal advice", [
   ("warn", "**Not legal advice.** These are mainly US and EU laws (COPPA, CAN-SPAM, California CIPA and auto-renewal law, DMCA, GDPR) and the figures are maximums (\"up to\"). If you have users there, get a lawyer to review. India's DPDP Act also applies to Indian users (see the [RULES checklist](RULES.html)).")]),
 ("The prompt", "The prompt", [
   ("prompt", "Paste into Claude Code", "You are auditing this app for 6 common legal risks in vibe-coded apps. For each one: (1) find where it applies in this codebase, (2) explain the risk in one line, (3) implement the fix, (4) list anything I must do manually outside the code.\n\n1. AGE / COPPA: Signup has no age check. Add an age or date-of-birth gate; block under-13s (or route to verifiable parental consent); don't store data for blocked users. Add a line about children in the privacy policy.\n\n2. GOOGLE FONTS / GDPR: Fonts load from fonts.googleapis.com / fonts.gstatic.com. Self-host all fonts (download the woff2 files into /public/fonts, use @font-face or next/font local), and remove every request to Google font servers.\n\n3. SESSION REPLAY / WIRETAP: Find analytics tools with session replay or keystroke capture (PostHog, Hotjar, LogRocket, FullStory, Clarity, etc.). Turn replay off by default, mask all inputs, and only enable it after explicit consent from a cookie/consent banner. Add a consent banner if none exists (Accept / Reject / Manage; non-essential off until accepted).\n\n4. EMAIL / CAN-SPAM: Every marketing email template must include a working one-click unsubscribe link (plus List-Unsubscribe headers), the business's physical postal address, and an honest subject and from-name. Respect unsubscribes immediately.\n\n5. SUBSCRIPTIONS / AUTO-RENEWAL: Next to every subscribe or checkout button, clearly show the price, billing interval, that it renews automatically until cancelled, and how to cancel. Get affirmative consent (unchecked checkbox), send a confirmation email with these terms, and make online cancellation easy (Stripe customer portal link).\n\n6. USER UPLOADS / DMCA: If users can upload images or content, add a /dmca (copyright) page with a takedown process and a designated agent contact, add upload terms (users own and license their content), and add a report button on user content.\n\nAlso add or update: privacy policy, terms of service, and a footer with links to both.\n\nAt the end, give me a checklist table: item | status (fixed / needs manual action) | file(s) changed.")]),
 ("Manual", "Manual steps the code can't do", [
   ("list", ["Register a **DMCA designated agent** with the US Copyright Office (online, a small fee; renew every 3 years) if you host user uploads and have US users.",
             "Add your real postal address (a business address or PO box) to email settings.", "Have a lawyer review the privacy policy and terms if you're serious about the US or EU market.",
             "Re-test signup, emails, checkout and the cookie banner after the changes."])]),
 ("Self-check", "Quick self-check (2 minutes)", [
   ("list", ["Open your site with **DevTools → Network**, and search \"fonts.g\". Should be 0 requests.", "Sign up with age 12. Should be blocked.",
             "Send yourself a marketing email. Unsubscribe and an address should be in the footer.", "Look at the checkout button. Renewal terms should be right next to it."]),
   ("p", "Part 2 (cost and security traps) is in the [SAFE guide](SAFE.html). Idea credit: @adilet.fndr.")]),
])

G["SAFE"] = page("SAFE", "One Claude prompt to fix", "5 cost & security traps",
 "Thanks for commenting SAFE! Paste this into Claude Code inside your app's repo. Part 1 (age gate, fonts, session replay, email, renewals, DMCA) is in the FIX guide.", [
 ("Before you start", "Not legal advice", [
   ("warn", "**Not legal advice.** The figures come from real cases and legal maximums (mostly US). Test changes on a staging environment first."),
   ("tip", "Part 1 is the [FIX guide](FIX.html).")]),
 ("The prompt", "The prompt", [
   ("prompt", "Paste into Claude Code", "Audit this app for 5 cost and security risks. For each: find where it applies, explain the risk in one line, implement the fix, and list manual steps I must do in dashboards.\n\n1. TRAFFIC / BILL SHOCK: Protect against DDoS and bandwidth spikes. Put the site behind a CDN/WAF (e.g. Cloudflare), add rate limiting on API routes, cache static assets, and tell me exactly which hosting setting enables spend caps or alerts (and which ones only alert).\n\n2. ACCESSIBILITY: Make the whole site keyboard-usable (visible focus, logical tab order, no keyboard traps), add meaningful alt text to all images, add labels to form inputs, check color contrast, and add an accessibility statement page. Run an automated check (axe / Lighthouse) and fix the issues.\n\n3. SUPABASE SECURITY: Find every table. Enable Row Level Security on ALL of them and write least-privilege policies (users can only read and write their own rows). Make sure the service_role key is never in client code (only the anon key). List any table that is still publicly readable.\n\n4. SMS / TCPA: Find any code that sends SMS or WhatsApp marketing. Require explicit opt-in (unchecked checkbox plus consent text and a timestamp stored in the DB), support STOP / opt-out, and block sends to anyone without recorded consent.\n\n5. RUNAWAY FUNCTIONS: Find cloud functions, triggers, webhooks or cron jobs that could call themselves or loop (e.g. a function that updates the same record that triggers it). Add recursion guards, idempotency checks, max-retry limits and timeouts, and set max instances / concurrency limits. Tell me how to set a hard budget cap or kill switch on my cloud provider.\n\nAt the end, give a table: item | status (fixed / manual) | files changed | manual steps.")]),
 ("Manual", "Manual steps the code can't do", [
   ("list", ["Enable spend limits on your host or cloud. Note that budget alerts only notify: set max instances or a hard cap where available.",
             "In Supabase, open **Advisors → Security** and fix every warning.", "Put your domain behind **Cloudflare** (free plan) for DDoS protection.",
             "Re-test with a keyboard only (Tab / Shift+Tab / Enter)."])]),
 ("Self-check", "60-second self-check", [
   ("list", ["Supabase: does any table show **RLS disabled**? Fix it.", "Open your site and press **Tab** repeatedly. Can you reach every button?",
             "Search your code for `service_role`. It must never be in frontend code."]),
   ("p", "Idea credit: @adilet.fndr.")]),
])

for name, html in G.items():
    open(os.path.join(OUT, f"{name}.html"), "w", encoding="utf-8").write(html)
TARGET = {31: "SENIOR", 32: "FIX", 33: "CODING", 34: "TOKENS", 35: "SAFE"}
p = "freebies/index.html"; s = open(p, encoding="utf-8").read()
i = s.index("const D=") + 8; j = s.index(";\n", i); d = json.loads(s[i:j])
for x in d["items"]:
    if x["n"] in TARGET:
        x["u"] = f"guides/{TARGET[x['n']]}.html"; print(x["n"], x["k"], "->", x["u"])
open(p, "w", encoding="utf-8").write(s[:i] + json.dumps(d, ensure_ascii=False) + s[j:])
