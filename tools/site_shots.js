// Screenshots of every website page on desktop and phone, for review: node tools/site_shots.js [baseUrl] [outDir]
// Phone pages are captured screen by screen (scrolling), not as one tall image: tall captures repeat
// sticky headers and 100vh sections. Prints any page errors and horizontal overflow.
const { chromium } = require('../node_modules/playwright');
const fs = require('fs');
(async () => {
  const base = process.argv[2] || 'http://localhost:8099';
  const out = process.argv[3] || 'review/site';
  fs.mkdirSync(out, { recursive: true });
  const pages = [['home', '/'], ['kit_blaster', '/kits/star-slinger/'], ['kit_dragon', '/kits/emberwing/'], ['kit_floral', '/kits/blossom-waltz/'],
    ['faq', '/faq/'], ['contact', '/contact/'], ['checkout', '/checkout/'], ['about', '/about/'], ['safety', '/safety/'], ['build', '/build/']];
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const problems = [];
  for (const [mode, vw, vh, dpr] of [['desktop', 1280, 860, 1], ['phone', 390, 844, 2]]) {
    const ctx = await browser.newContext({ viewport: { width: vw, height: vh }, deviceScaleFactor: dpr, isMobile: mode === 'phone', hasTouch: mode === 'phone' });
    for (const [name, url] of pages) {
      const page = await ctx.newPage();
      page.on('pageerror', e => problems.push(`${mode} ${name}: ${e}`));
      page.on('console', m => { if (m.type() === 'error') problems.push(`${mode} ${name}: ${m.text()}`); });
      await page.goto(base + url, { waitUntil: 'load' });
      await page.waitForTimeout(name === 'build' ? 2500 : 700);
      const sw = await page.evaluate(() => document.documentElement.scrollWidth);
      if (sw > vw + 1) problems.push(`${mode} ${name}: horizontal overflow ${sw}px > ${vw}px`);
      if (mode === 'desktop') {
        await page.screenshot({ path: `${out}/${name}_desktop.png`, fullPage: true });
      } else {
        const h = await page.evaluate(() => document.documentElement.scrollHeight);
        const n = Math.min(4, Math.ceil(h / vh));
        for (let i = 0; i < n; i++) {
          await page.evaluate(y => window.scrollTo(0, y), i * vh);
          await page.waitForTimeout(250);
          await page.screenshot({ path: `${out}/${name}_phone_${i + 1}.png` });
        }
      }
      await page.close();
    }
    await ctx.close();
  }
  await browser.close();
  console.log(problems.length ? 'PROBLEMS:\n' + problems.join('\n') : 'no page errors, no overflow');
})();
