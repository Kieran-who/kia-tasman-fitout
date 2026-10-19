// Rasterise SVG sheets to PNG for previews: node svg2png.mjs out_dir file1.svg [file2.svg ...]
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
const [outDir, ...files] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1680, height: 1188 } });
for (const f of files) {
  const svg = fs.readFileSync(f, 'utf8');
  await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
  const out = path.join(outDir, path.basename(f).replace(/\.svg$/, '.png'));
  await page.screenshot({ path: out });
  console.log('png', out);
}
await browser.close();
