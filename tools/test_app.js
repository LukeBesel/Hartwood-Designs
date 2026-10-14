// End-to-end test of the 3D build app: node tools/test_app.js http://localhost:8123
const { chromium } = require('../node_modules/playwright');
const base = process.argv[2] || 'http://localhost:8123';
const out = process.argv[3] || 'review/app';
const results = [];
const ok = (name, cond, extra = '') => { results.push(`${cond ? 'PASS' : 'FAIL'}  ${name}${extra ? '  (' + extra + ')' : ''}`); };
(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  const ready = () => page.waitForFunction(() => document.getElementById('loading').hidden && document.getElementById('stepTitle').textContent !== 'Loading...', null, { timeout: 60000 });

  await page.goto(base + '/build/blaster');
  await ready();
  ok('opening /build/blaster goes to step 1', page.url().endsWith('/build/blaster/step/1'), page.url());
  await page.click('#nextBtn'); await ready();
  await page.click('#nextBtn'); await ready();
  ok('Next moves to step 3', page.url().endsWith('/step/3'), page.url());
  const saved = await page.evaluate(() => JSON.parse(localStorage.getItem('hw:blaster')));
  ok('progress saved in localStorage', saved && saved.done === 2 && saved.last === 3, JSON.stringify(saved));
  await page.goto(base + '/build/blaster'); await ready();
  ok('reopening resumes at the saved step', page.url().endsWith('/step/3'), page.url());
  await page.click('#tray button');
  await page.waitForTimeout(300);
  const info = await page.evaluate(() => !document.getElementById('partInfo').hidden && document.getElementById('partInfo').textContent);
  ok('tapping a part in the tray shows its code and sheet', !!info && /Sheet/.test(info), info || '');
  await page.screenshot({ path: `${out}/phone_part_info.png` });
  await page.click('#menuBtn');
  await page.waitForTimeout(200);
  ok('step list opens', await page.isVisible('#stepList'));
  await page.screenshot({ path: `${out}/phone_step_list.png` });
  await page.click('#stepItems li:nth-child(6) a'); await ready();
  ok('step list jumps to step 6', page.url().endsWith('/step/6'), page.url());
  await page.click('#prevBtn'); await ready();
  ok('Back moves to step 5', page.url().endsWith('/step/5'));
  // tap on the model: raycast pick
  const box = await page.locator('#c').boundingBox();
  let picked = false;
  for (const [fx, fy] of [[0.5, 0.5], [0.45, 0.45], [0.55, 0.5], [0.4, 0.55], [0.6, 0.4]]) {
    await page.mouse.click(box.x + box.width * fx, box.y + box.height * fy);
    await page.waitForTimeout(150);
    picked = await page.evaluate(() => !document.getElementById('partInfo').hidden);
    if (picked) break;
  }
  ok('tapping the model shows the part', picked);
  // hash routing (hosts without rewrites)
  await page.goto(base + '/build/#/dragon/step/2'); await ready();
  ok('hash route works', (await page.textContent('#stepCount')).includes('Step 2 of'), await page.textContent('#stepCount'));
  // offline: wait for the service worker, cache the kit, then go offline and reload
  await page.goto(base + '/build/floral/step/4'); await ready();
  await page.waitForFunction(() => navigator.serviceWorker && navigator.serviceWorker.controller, null, { timeout: 30000 }).catch(() => {});
  await page.reload(); await ready();
  await page.waitForTimeout(4000);
  await ctx.setOffline(true);
  await page.reload(); 
  let offlineOk = false;
  try { await ready(); offlineOk = (await page.textContent('#stepCount')).includes('Step 4'); } catch (e) { offlineOk = false; }
  ok('works offline after the first visit', offlineOk);
  await page.screenshot({ path: `${out}/phone_offline_floral.png` });
  await ctx.setOffline(false);
  // picker
  await page.goto(base + '/build/'); await page.waitForTimeout(1500);
  ok('kit picker lists 3 kits', (await page.$$('.kitcard')).length === 3);
  await page.screenshot({ path: `${out}/phone_picker.png` });
  ok('no console errors', errors.length === 0, errors.slice(0, 3).join(' | '));
  console.log(results.join('\n'));
  await browser.close();
})();
