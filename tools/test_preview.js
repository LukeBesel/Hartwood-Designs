// Smoke test for the preview build: node tools/test_preview.js http://localhost:PORT OUTDIR
// jsDelivr is not reachable from the build machine, so its three.js URLs are answered from node_modules/three
// (the same version, 0.169.0): this proves the import map and paths are right.
const { chromium } = require('../node_modules/playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const base = process.argv[2], out = process.argv[3] || 'review/preview';
  fs.mkdirSync(out, { recursive: true });
  const three = path.resolve(__dirname, '../node_modules/three');
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const pages = [
    ['hub', '/index.html', 1280, 900],
    ['site_home', '/site/index.html', 1280, 900],
    ['site_kit', '/site/kits/star-slinger/index.html', 1280, 900],
    ['app_step', '/site/build/index.html#/blaster/step/4', 390, 844],
    ['app_picker', '/site/build/index.html', 390, 844],
    ['guide_order', '/guides/blaster_test.html', 1100, 900],
    ['guide_cut', '/guides/how_to_cut.html', 1100, 900],
    ['planner', '/planner/index.html', 1180, 820],
    ['sops', '/sops/index.html', 1100, 900],
    ['hub_phone', '/index.html', 390, 844],
  ];
  const problems = [];
  for (const [name, url, w, h] of pages) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: w < 500 ? 2 : 1 });
    await ctx.route('https://cdn.jsdelivr.net/npm/three@0.169.0/**', async route => {
      const rel = route.request().url().split('three@0.169.0/')[1];
      const f = path.join(three, rel);
      if (fs.existsSync(f)) await route.fulfill({ path: f, contentType: 'text/javascript' });
      else await route.fulfill({ status: 404, body: 'missing ' + rel });
    });
    const page = await ctx.newPage();
    page.on('pageerror', e => problems.push(`${name}: ${e}`));
    page.on('console', m => { if (m.type() === 'error') problems.push(`${name}: ${m.text()}`); });
    page.on('requestfailed', r => { if (!r.url().includes('fonts.g')) problems.push(`${name}: failed ${r.url()}`); });
    page.on('response', r => { if (r.status() >= 400 && !r.url().includes('fonts.g')) problems.push(`${name}: ${r.status()} ${r.url()}`); });
    await page.goto(base + url, { waitUntil: 'load' });
    await page.waitForTimeout(name.startsWith('app') || name === 'site_kit' ? 4000 : 1200);
    if (name === 'site_kit') {           // the 3D model loads on request
      const btn = await page.$('button:has-text("Load the 3D model")');
      if (btn) { await btn.click(); await page.waitForTimeout(4000); }
    }
    const sw = await page.evaluate(() => document.documentElement.scrollWidth);
    if (sw > w + 1) problems.push(`${name}: horizontal overflow ${sw}px`);
    if (name === 'app_step') {
      const t = await page.textContent('#stepCount').catch(() => '');
      if (!/Step 4 of/.test(t)) problems.push(`${name}: step counter shows "${t}"`);
    }
    await page.screenshot({ path: `${out}/${name}.png`, fullPage: !name.startsWith('app') });
    await ctx.close();
  }
  await browser.close();
  console.log(problems.length ? 'PROBLEMS:\n' + problems.join('\n') : `all ${pages.length} pages load without errors`);
  process.exit(problems.length ? 1 : 0);
})();
