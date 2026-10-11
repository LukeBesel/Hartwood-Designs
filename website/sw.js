// Hartwood service worker: the build app and every kit you open keep working offline.
const VERSION = 'hw-2026-10-11a';
const SHELL = [
  '/build/index.html', '/build/app.js', '/build/app.css', '/css/site.css', '/js/hw3d.js', '/favicon.svg',
  '/manifest.webmanifest', '/assets/kits/kits.json',
  '/vendor/three/three.module.min.js', '/vendor/three/addons/controls/OrbitControls.js',
  '/vendor/three/addons/loaders/GLTFLoader.js', '/vendor/three/addons/utils/BufferGeometryUtils.js',
  '/vendor/three/addons/lines/LineMaterial.js', '/vendor/three/addons/lines/LineSegments2.js',
  '/vendor/three/addons/lines/LineSegmentsGeometry.js',
  '/fonts/Fraunces-700.woff2', '/fonts/Fraunces-800.woff2', '/fonts/Inter-400.woff2', '/fonts/Inter-500.woff2',
  '/fonts/Inter-600.woff2', '/fonts/Inter-700.woff2',
  ...['press', 'wax', 'flip', 'careful', 'test', 'centre', 'x2', 'x3', 'x4', 'x6', 'x8', 'glasses', 'spin', 'sand']
    .map(i => `/assets/icons/${i}.svg`),
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => !k.startsWith(VERSION)).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return;
  if (req.mode === 'navigate' && url.pathname.startsWith('/build')) {
    // app routes: try the network, fall back to the cached app shell
    e.respondWith(fetch(req).catch(() => caches.match('/build/index.html')));
    return;
  }
  // everything else: cached copy first, refreshed in the background
  e.respondWith(caches.match(req).then(hit => {
    const net = fetch(req).then(res => {
      if (res.ok && /^\/(assets|vendor|fonts|js|css|build)\//.test(url.pathname)) {
        const copy = res.clone(); caches.open(VERSION + '-runtime').then(c => c.put(req, copy));
      }
      return res;
    }).catch(() => hit);
    return hit || net;
  }));
});
self.addEventListener('message', e => {
  if (!e.data || e.data.type !== 'cache-kit') return;
  e.waitUntil(caches.open(VERSION + '-kits').then(c => c.addAll(e.data.urls)).then(() =>
    self.clients.matchAll().then(cs => cs.forEach(cl => cl.postMessage({ type: 'kit-cached', kit: e.data.kit })))).catch(() => {}));
});
