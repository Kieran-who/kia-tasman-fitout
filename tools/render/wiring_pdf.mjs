// Print the wiring diagram page to an A3-landscape PDF: node wiring_pdf.mjs <in.html> <out.pdf>
import { chromium } from 'playwright';
import path from 'node:path';
const [inp, out] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1588, height: 1123 } });
await page.goto('file://' + path.resolve(inp), { waitUntil: 'load', timeout: 60000 }).catch(() => {});
await page.waitForTimeout(1500);
await page.pdf({ path: out, preferCSSPageSize: true, printBackground: true });
await browser.close();
console.log('pdf', out);
