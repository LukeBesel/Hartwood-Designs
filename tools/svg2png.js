// SVG to transparent PNG: node tools/svg2png.js in.svg out.png width height
const { chromium } = require('../node_modules/playwright');
const fs = require('fs');
(async () => {
  const [, , src, out, w, h] = process.argv;
  const svg = fs.readFileSync(src, 'utf8');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: +w, height: +h } });
  await page.setContent(`<html><body style="margin:0;background:transparent">
    <div style="width:${w}px;height:${h}px">${svg.replace(/width="[^"]*" height="[^"]*"/, 'width="100%" height="100%"')}</div></body></html>`);
  await page.screenshot({ path: out, omitBackground: true });
  await browser.close();
})();
