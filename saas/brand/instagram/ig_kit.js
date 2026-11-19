const {chromium} = require("playwright");
const OUT = process.argv[2];
const G = `<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7B5CFF"/><stop offset=".62" stop-color="#B05CE8"/><stop offset="1" stop-color="#FF7A59"/></linearGradient>`;
const base = (inner) => `<!doctype html><html><head><link href="https://fonts.googleapis.com/css2?family=Geist:wght@500;600;700&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<style>html,body{margin:0;width:1080px;height:1080px;overflow:hidden}
body{background:radial-gradient(60% 60% at 30% 20%,#2A1F4D 0%,#14111F 55%,#0B0A10 100%);display:grid;place-items:center;font-family:Geist,Inter,sans-serif;color:#fff}
.glow{position:absolute;width:760px;height:760px;border-radius:50%;background:radial-gradient(circle,rgba(176,92,232,.35),transparent 65%);filter:blur(30px)}
</style></head><body><div class="glow"></div>${inner}</body></html>`;
// profile photo: the mark, big, on the dark glow
const mark = `<svg width="560" height="560" viewBox="0 0 32 32" style="position:relative;filter:drop-shadow(0 30px 60px rgba(123,92,255,.45))"><defs><linearGradient id="t" x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#7B5CFF"/><stop offset=".62" stop-color="#B05CE8"/><stop offset="1" stop-color="#FF7A59"/></linearGradient></defs>
<rect width="32" height="32" rx="9" fill="url(#t)"/><path d="M9.6 8.5h12.8a3.1 3.1 0 0 1 3.1 3.1v7.1a3.1 3.1 0 0 1-3.1 3.1h-6.6l-4.6 3.6a.6.6 0 0 1-1-.5v-3.1h-.6a3.1 3.1 0 0 1-3.1-3.1v-7.1a3.1 3.1 0 0 1 3.1-3.1z" fill="#fff"/>
<path d="M15.4 11.9l-3.1 2.7 3.1 2.7" stroke="#6A4CFF" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M12.7 14.6h5.5a2.6 2.6 0 0 1 2.6 2.6v1" stroke="#6A4CFF" stroke-width="1.9" fill="none" stroke-linecap="round"/></svg>`;
// highlight covers: thin gradient ring, line icon, small label
const ICONS = {
  start: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  demo: '<circle cx="12" cy="12" r="9"/><path d="M10 8.5v7l6-3.5z" fill="url(#g)" stroke="none"/>',
  features: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
  pricing: '<path d="M7 5h10M7 9h10M14 5c3.5 0 3.5 8 0 8H7l8 7"/>',
  reviews: '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/>',
  help: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/><path d="M9.7 9.6a2.4 2.4 0 1 1 3.3 2.2c-.6.3-1 .8-1 1.4M12 16h.01"/>',
};
const cover = (k) => `<svg width="620" height="620" viewBox="0 0 100 100" style="position:relative"><defs>${G}</defs>
<circle cx="50" cy="50" r="46" fill="rgba(255,255,255,.03)" stroke="url(#g)" stroke-width="1.6"/>
<circle cx="50" cy="50" r="40.5" fill="none" stroke="rgba(255,255,255,.08)" stroke-width=".6"/>
<g transform="translate(26 26) scale(2)" fill="none" stroke="url(#g)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${ICONS[k]}</g></svg>`;
(async () => {
  const b = await chromium.launch({executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"});
  const p = await b.newPage({viewport: {width: 1080, height: 1080}});
  const shots = [["profile-photo", base(mark)], ...Object.keys(ICONS).map(k => [`highlight-${k}`, base(cover(k))])];
  for (const [name, html] of shots) { await p.setContent(html, {waitUntil: "networkidle"}); await p.screenshot({path: `${OUT}/${name}.png`}); }
  await b.close();
})();
