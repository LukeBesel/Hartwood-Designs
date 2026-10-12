// HTML page to a Letter PDF with a footer on every page:
//   node tools/html2pdf.js in.html out.pdf ["footer text"] [landscape=0]
// The footer shows the text plus "page n of m". Backgrounds are printed.
const { chromium } = require('../node_modules/playwright');
const path = require('path');
(async () => {
  const [, , src, out, footer = '', landscape = '0'] = process.argv;
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('requestfailed', r => errors.push('missing: ' + r.url()));
  await page.goto('file://' + path.resolve(src), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({
    path: out, format: 'Letter', landscape: landscape === '1', printBackground: true,
    margin: { top: '0.4in', bottom: '0.55in', left: '0.4in', right: '0.4in' },
    displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: `<div style="width:100%;font:8px Inter,Arial,sans-serif;color:#5C4636;padding:0 0.4in;display:flex;justify-content:space-between">
      <span>${footer.replace(/</g, '&lt;')}</span><span>page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>`,
  });
  if (errors.length) console.log('PAGE ERRORS:\n' + errors.join('\n'));
  await browser.close();
})();
