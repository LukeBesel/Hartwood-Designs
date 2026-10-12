// Smoke test for the workshop planner: node tools/test_planner.js [screenshot.png]
// Adds orders, logs problems inside and outside the 4-week window, checks the Pareto and that no page errors occur.
const { chromium } = require('../node_modules/playwright');
const path = require('path');
(async () => {
  const shot = process.argv[2];
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1180, height: 820 } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto('file://' + path.resolve(__dirname, '../production/planner/index.html'));
  const results = [];
  const check = (name, ok, info = '') => { results.push([name, ok, info]); };

  await page.evaluate(() => {
    const P = window.HW_PLANNER;
    P.state.orders = []; P.state.defects = [];
    P.addOrder({ kit: 'dragon', qty: 2, customer: 'Test', channel: 'own site' });
    const day = n => new Date(Date.now() - n * 864e5).toISOString().slice(0, 10);
    P.state.defects.push(
      { date: day(60), kit: 'blaster', code: 'B1', cat: 'burn', count: 9, note: 'old' },
      { date: day(10), kit: 'dragon', code: 'C12', cat: 'tight', count: 4, note: '' },
      { date: day(3), kit: 'floral', code: 'D3', cat: 'bridge', count: 2, note: '' },
      { date: day(1), kit: 'dragon', code: 'A4', cat: 'tight', count: 1, note: '' });
    P.save(); P.render();
  });
  await page.click('[data-tab="quality"]');
  const fix4 = await page.textContent('#fixFirst');
  check('4-week Pareto ignores old problems', /too tight/i.test(fix4), fix4);
  await page.selectOption('#paretoWin', '0');
  const fixAll = await page.textContent('#fixFirst');
  check('all-time Pareto includes old problems', /burn/i.test(fixAll), fixAll);
  await page.selectOption('#paretoWin', '28');
  const bars = await page.$$eval('#pareto .pbar', b => b.length);
  check('4-week Pareto has 2 bars', bars === 2, String(bars));
  if (shot) await page.screenshot({ path: shot, fullPage: true });
  // print view of the schedule: only the schedule shows
  await page.click('[data-tab="queue"]');
  page.once('dialog', d => d.accept());
  await page.click('#startBatch');
  await page.click('[data-tab="orders"]');
  await page.emulateMedia({ media: 'print' });
  const vis = await page.evaluate(() => ({ sched: getComputedStyle(document.querySelector('#schedule')).display,
    top: getComputedStyle(document.querySelector('.top')).display, orders: getComputedStyle(document.querySelector('#orders')).display,
    slots: document.querySelectorAll('#timeline .slot').length }));
  check('print view shows only the schedule', vis.sched !== 'none' && vis.top === 'none' && vis.orders === 'none', JSON.stringify(vis));
  check('schedule has laser runs', vis.slots > 0, JSON.stringify(vis));
  if (shot) await page.screenshot({ path: shot.replace('.png', '_print.png'), fullPage: true });
  await page.emulateMedia({ media: 'screen' });
  check('no page errors', errors.length === 0, errors.join(' | '));
  await page.evaluate(() => { localStorage.clear(); });
  await browser.close();
  let fail = 0;
  for (const [n, ok, info] of results) { console.log(`${ok ? 'PASS' : 'FAIL'}  ${n}${ok ? '' : '  -> ' + info}`); if (!ok) fail++; }
  console.log(`${results.length - fail} of ${results.length} passed`);
  process.exit(fail ? 1 : 0);
})();
