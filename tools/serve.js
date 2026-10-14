// Local static server for website/ with the same rewrites as the host: node tools/serve.js [port]
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..', 'website');
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2', '.pdf': 'application/pdf', '.csv': 'text/csv' };
function resolve(p) {
  let f = path.join(ROOT, decodeURIComponent(p));
  if (!f.startsWith(ROOT)) return null;
  if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html');
  if (fs.existsSync(f)) return f;
  if (fs.existsSync(f + '.html')) return f + '.html';
  if (p.startsWith('/build/')) return path.join(ROOT, 'build', 'index.html');
  return null;
}
const port = +(process.argv[2] || 8080);
http.createServer((req, res) => {
  const f = resolve(req.url.split('?')[0]);
  if (!f) { res.writeHead(404, { 'Content-Type': 'text/html' }); fs.createReadStream(path.join(ROOT, '404.html')).on('error', () => res.end('Not found')).pipe(res); return; }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(res);
}).listen(port, () => console.log(`Hartwood site on http://localhost:${port}`));
