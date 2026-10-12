// Render an HTML page at an exact print size, to PDF and/or PNG:
//   node tools/html2print.js in.html widthIn heightIn [out.pdf|-] [out.png|-] [dpi=150]
// The page must lay itself out at widthIn x heightIn (CSS inches). No margins, backgrounds printed.
const { chromium } = require('../node_modules/playwright');
const path = require('path');
(async () => {
  const [, , src, wIn, hIn, pdf = '-', png = '-', dpi = '150'] = process.argv;
  const w = Math.round(+wIn * 96), h = Math.round(+hIn * 96);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: +dpi / 96 });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('requestfailed', r => errors.push('missing: ' + r.url()));
  await page.goto('file://' + path.resolve(src), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  if (pdf !== '-') await page.pdf({ path: pdf, width: wIn + 'in', height: hIn + 'in', printBackground: true, margin: { top: 0, bottom: 0, left: 0, right: 0 } });
  if (png !== '-') await page.screenshot({ path: png, clip: { x: 0, y: 0, width: w, height: h } });
  if (errors.length) console.log('PAGE ERRORS:\n' + errors.join('\n'));
  await browser.close();
})();
