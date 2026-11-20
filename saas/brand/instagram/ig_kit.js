// @replyinbox.in Instagram kit in the ReplyInbox brand (paper, ink, cobalt #2E3BFF, volt #D4FF3A).
// Run from saas/: node brand/instagram/ig_kit.js brand/instagram
const {chromium} = require("playwright");
const OUT = process.argv[2] || ".";
const INK = "#111318", PAPER = "#F5F4EF", COBALT = "#2E3BFF", VOLT = "#D4FF3A";
const page = (bg, inner) => `<!doctype html><html><head><style>
html,body{margin:0;width:1080px;height:1080px;overflow:hidden}
body{background:${bg};display:grid;place-items:center}
</style></head><body>${inner}</body></html>`;

// profile photo: solid cobalt (Instagram crops it to a circle), the white reply bubble big in the middle
const mark = `<svg width="640" height="640" viewBox="0 0 32 32">
<path d="M9.6 8.5h12.8a3.1 3.1 0 0 1 3.1 3.1v7.1a3.1 3.1 0 0 1-3.1 3.1h-6.6l-4.6 3.6a.6.6 0 0 1-1-.5v-3.1h-.6a3.1 3.1 0 0 1-3.1-3.1v-7.1a3.1 3.1 0 0 1 3.1-3.1z" fill="#fff"/>
<path d="M15.4 11.9l-3.1 2.7 3.1 2.7" stroke="${COBALT}" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M12.7 14.6h5.5a2.6 2.6 0 0 1 2.6 2.6v1" stroke="${COBALT}" stroke-width="1.9" fill="none" stroke-linecap="round"/></svg>`;

// highlight covers: dot-grid paper, a volt disc with a thick ink outline and a hard shadow, an ink line icon
const ICONS = {
  start: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  demo: '<circle cx="12" cy="12" r="9"/><path d="M10 8.5v7l6-3.5z" fill="currentColor" stroke="none"/>',
  features: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
  pricing: '<path d="M7 5h10M7 9h10M14 5c3.5 0 3.5 8 0 8H7l8 7"/>',
  reviews: '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/>',
  help: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/><path d="M9.7 9.6a2.4 2.4 0 1 1 3.3 2.2c-.6.3-1 .8-1 1.4M12 16h.01"/>',
};
const dots = `radial-gradient(rgba(17,19,24,.16) 3px,transparent 3.6px) 0 0/54px 54px,${PAPER}`;
const cover = (k) => `<svg width="700" height="700" viewBox="0 0 100 100" style="overflow:visible">
<circle cx="53.5" cy="53.5" r="40" fill="${INK}"/>
<circle cx="50" cy="50" r="40" fill="${VOLT}" stroke="${INK}" stroke-width="3.2"/>
<g transform="translate(26 26) scale(2)" fill="none" stroke="${INK}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" color="${INK}">${ICONS[k]}</g></svg>`;

(async () => {
  const b = await chromium.launch({executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"});
  const p = await b.newPage({viewport: {width: 1080, height: 1080}});
  const shots = [["profile-photo", page(COBALT, mark)], ...Object.keys(ICONS).map(k => [`highlight-${k}`, page(dots, cover(k))])];
  for (const [name, html] of shots) { await p.setContent(html); await p.screenshot({path: `${OUT}/${name}.png`}); }
  await b.close();
})();
