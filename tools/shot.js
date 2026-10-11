// Screenshot helper: node tools/shot.js <url-or-file> <out.png> [width] [height] [fullPage=1] [theme=light|dark] [waitMs]
const { chromium } = require('../node_modules/playwright');
const path = require('path');
(async () => {
  const [, , target, out, w = '1280', h = '900', full = '1', theme = 'light', wait = '800'] = process.argv;
  const url = /^https?:/.test(target) ? target : 'file://' + path.resolve(target);
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: +w < 600 ? 2 : 1, colorScheme: theme });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(url, { waitUntil: 'load' });
  await page.waitForTimeout(+wait);
  await page.screenshot({ path: out, fullPage: full === '1' });
  if (errors.length) console.log('PAGE ERRORS:\n' + errors.join('\n'));
  await browser.close();
})();
