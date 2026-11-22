import { bundle } from '@remotion/bundler';
import { renderStill, selectComposition } from '@remotion/renderer';
import path from 'path';
const frames = process.argv.slice(2).map(Number);
const serveUrl = await bundle({ entryPoint: path.resolve('src/index.ts'), publicDir: path.resolve('public') });
const browserExecutable = '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
const composition = await selectComposition({ serveUrl, id: 'Reel', browserExecutable });
for (const frame of frames) {
  await renderStill({ composition, serveUrl, output: `out/still-${String(frame).padStart(4, '0')}.png`, frame, browserExecutable, scale: 0.5 });
  console.log('still', frame);
}
