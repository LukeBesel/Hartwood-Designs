// Test the preview build the way the claude.ai host serves it:  node tools/test_preview.js PREVIEW_DIR [SCREENSHOT_DIR]
// The built-in server only serves real files (a folder address is a 404, like on the host), every link in every
// page must point at a file in the build, and the test taps through the main paths a visitor uses.
// jsDelivr is not reachable from the build machine, so its three.js URLs are answered from node_modules/three
// (the same version, 0.169.0): this proves the import map and paths are right.
const { chromium } = require('../node_modules/playwright');
const fs = require('fs');
const http = require('http');
const path = require('path');

const root = path.resolve(process.argv[2] || '');
const out = process.argv[3] || 'review/preview';
const three = path.resolve(__dirname, '../node_modules/three');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.csv': 'text/csv',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.pdf': 'application/pdf' };
const problems = [];

function fileFor(urlPath) {
  const f = path.join(root, decodeURIComponent(urlPath));
  return f.startsWith(root) && fs.existsSync(f) && fs.statSync(f).isFile() ? f : null;
}

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)]);
}

// Every href and src in every page must resolve (through <base> if the page has one) to a file in the build.
function checkLinks() {
  let n = 0;
  for (const f of walk(root).filter(f => f.endsWith('.html'))) {
    const rel = path.relative(root, f).split(path.sep).join('/');
    const html = fs.readFileSync(f, 'utf8');
    const scan = html.replace(/<base [^>]*>/g, '');
    const page = new URL('http://host/' + rel);
    const b = html.match(/<base href="([^"]*)"/);
    const base = b ? new URL(b[1], page) : page;
    for (const m of scan.matchAll(/\s(?:href|src|content="\d+;\s*url)="?([^"]*)"/g)) {
      const u = m[1];
      if (!u || u.includes('${') || /^(https?:|mailto:|tel:|data:|javascript:)/.test(u)) continue;
      const t = new URL(u, base);
      n++;
      if (!fileFor(t.pathname)) problems.push(`${rel}: link "${u}" goes to ${t.pathname}, which is not a file`);
      else if (u.startsWith('#') && t.pathname !== page.pathname) problems.push(`${rel}: "${u}" leaves the page (goes to ${t.pathname})`);
    }
  }
  return n;
}

(async () => {
  if (!fs.existsSync(path.join(root, 'index.html'))) { console.error('usage: node tools/test_preview.js PREVIEW_DIR [SCREENSHOT_DIR]'); process.exit(2); }
  fs.mkdirSync(out, { recursive: true });
  const links = checkLinks();

  const server = http.createServer((req, res) => {
    const f = fileFor(new URL(req.url, 'http://host').pathname);
    if (!f) { res.writeHead(404); res.end('not found'); return; }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' });
    fs.createReadStream(f).pipe(res);
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = `http://127.0.0.1:${server.address().port}`;

  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  async function open(name, url, w, h) {
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
    return { ctx, page };
  }
  async function stepShown(name, page, want) {
    await page.waitForFunction(() => /Step \d+ of/.test(document.querySelector('#stepCount')?.textContent || ''), null, { timeout: 15000 })
      .catch(() => {});
    const t = await page.textContent('#stepCount').catch(() => '');
    if (!(want || /Step \d+ of/).test(t)) problems.push(`${name}: step counter shows "${t}" at ${page.url()}`);
  }

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
  for (const [name, url, w, h] of pages) {
    const { ctx, page } = await open(name, url, w, h);
    await page.waitForTimeout(name.startsWith('app') || name === 'site_kit' ? 4000 : 1200);
    if (name === 'site_kit') {           // the 3D model loads on request
      const btn = await page.$('button:has-text("Load the 3D model")');
      if (btn) { await btn.click(); await page.waitForTimeout(4000); }
    }
    const sw = await page.evaluate(() => document.documentElement.scrollWidth);
    if (sw > w + 1) problems.push(`${name}: horizontal overflow ${sw}px`);
    if (name === 'app_step') await stepShown(name, page, /Step 4 of/);
    await page.screenshot({ path: `${out}/${name}.png`, fullPage: !name.startsWith('app') });
    await ctx.close();
  }

  // Taps a visitor makes: each must land on a real page that works.
  const flows = [
    ['tap: hub > 3D app', '/index.html', 'a.tile >> nth=1', /\/site\/build\/index\.html$/, true],
    ['tap: app picker > Emberwing', '/site/build/index.html', 'a.kitcard >> nth=1', /\/site\/build\/index\.html$/, true],
    ['tap: site home > Shop the kits', '/site/index.html', 'a:has-text("Shop the kits")', /\/site\/index\.html$/, false],
    ['tap: kit page > Build in 3D', '/site/kits/star-slinger/index.html', 'a[href*="build/index.html#/"] >> nth=0', /\/site\/build\/index\.html$/, true],
    ['tap: hub > order list', '/index.html', 'a:has-text("Open the order list")', /\/guides\/blaster_test\.html$/, false],
  ];
  for (const [name, url, sel, want, isApp] of flows) {
    const { ctx, page } = await open(name, url, 390, 844);
    await page.waitForTimeout(isApp && url.includes('build') ? 3000 : 800);
    try {
      await page.click(sel, { timeout: 5000 });
      await page.waitForLoadState('load');
      await page.waitForTimeout(isApp ? 1500 : 500);
      const p = new URL(page.url()).pathname;
      if (!want.test(p)) problems.push(`${name}: landed on ${p}`);
      else if (isApp) await stepShown(name, page);
    } catch (e) { problems.push(`${name}: ${e.message.split('\n')[0]}`); }
    await ctx.close();
  }

  await browser.close();
  server.close();
  console.log(`${links} links checked, ${pages.length} pages and ${flows.length} taps tested`);
  console.log(problems.length ? 'PROBLEMS:\n' + problems.join('\n') : 'no problems');
  process.exit(problems.length ? 1 : 0);
})();
