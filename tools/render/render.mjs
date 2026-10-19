// Headless renders of the viewer via Playwright.
// Usage: node render.mjs <shots.json> <outdir>
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '../..');
const [shotsFile, outDir] = process.argv.slice(2);
const shots = JSON.parse(fs.readFileSync(shotsFile, 'utf8'));
fs.mkdirSync(outDir, { recursive: true });

const types = { '.html': 'text/html', '.js': 'text/javascript', '.glb': 'model/gltf-binary', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const p = path.join(process.env.VIEWER_ROOT || path.join(repo, 'viewer'), decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream' }); res.end(d); });
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage();
// serve three.js from the local node_modules instead of the CDN
await page.route('https://cdn.jsdelivr.net/npm/three@0.160.0/**', async route => {
  const rel = route.request().url().split('three@0.160.0/')[1];
  route.fulfill({ path: path.join(here, 'node_modules/three', rel), contentType: 'text/javascript' });
});
page.on('pageerror', e => console.error('pageerror', e.message));
for (const s of shots) {
  const w = s.w || 1600, h = s.h || 1000;
  await page.setViewportSize({ width: w, height: h });
  const qs = new URLSearchParams({ render: '1', w, h, ...s.params });
  await page.goto(`http://localhost:${port}/${process.env.VIEWER_PAGE || 'index.html'}?${qs}`);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  await page.waitForTimeout(300);
  const out = path.join(outDir, `${s.name}.png`);
  await page.screenshot({ path: out });
  console.log('rendered', out);
}
await browser.close();
server.close();
