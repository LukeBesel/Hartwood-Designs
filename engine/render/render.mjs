// Batch renderer: node engine/render/render.mjs jobs.json
// jobs.json: [{glb:'/kits/x/x.glb', out:'kits/x/renders/hero.png', mode:'hero'|'step'|'part'|'upto', ...}]
// Serves the repo root over http so ES modules load, drives headless Chromium (SwiftShader WebGL).
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const { chromium } = require(path.join(ROOT, 'node_modules/playwright'));
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.glb': 'model/gltf-binary', '.png': 'image/png', '.svg': 'image/svg+xml', '.css': 'text/css' };

const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const port = server.address().port;
const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 400, height: 300 } });
page.on('pageerror', e => console.error('PAGE ERROR', e.message));
page.on('console', m => { if (m.type() === 'error') console.error('CONSOLE', m.text()); });
await page.goto(`http://127.0.0.1:${port}/engine/render/render.html`);
await page.waitForFunction(() => window.ready === true, null, { timeout: 60000 });
const meta = [];
for (const job of jobs) {
  const t = Date.now();
  const r = await page.evaluate(j => window.renderJob(j), job);
  const out = path.resolve(ROOT, job.out);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, Buffer.from(r.png.split(',')[1], 'base64'));
  meta.push({ out: job.out, labels: r.labels, ms: Date.now() - t });
  process.stdout.write(`rendered ${job.out} (${Date.now() - t} ms)\n`);
}
if (process.argv[3]) fs.writeFileSync(process.argv[3], JSON.stringify(meta, null, 1));
await browser.close(); server.close();
