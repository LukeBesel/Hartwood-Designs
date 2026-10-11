// Hartwood 3D build app. Routes: /build/<kit>/step/<n> (or #/<kit>/step/<n> where the host has no rewrites).
// Progress is kept in localStorage; a service worker keeps the app and the opened kit available offline.
import * as H from '/js/hw3d.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const THREE = H.THREE;
const $ = id => document.getElementById(id);
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const usePath = location.protocol.startsWith('http') && !location.hash.startsWith('#/');
const ICONS = ['press', 'wax', 'flip', 'careful', 'test', 'centre', 'x2', 'x3', 'x4', 'x6', 'x8', 'glasses', 'spin', 'sand'];
const LAGOON = 0x0f8b7f;

let KITS = [];
let kitKey = null, kit = null, steps = null, ctx = null, n = 1;
let playing = !reduceMotion, colorBuilt = false, animT0 = performance.now(), tNow = reduceMotion ? 0.5 : 1;
let camTween = null, highlightTimer = null;

// ------------------------------------------------------------------ storage (never required to work)
const store = {
  get(k) { try { return JSON.parse(localStorage.getItem('hw:' + k)) || { done: 0, last: 1 }; } catch { return { done: 0, last: 1 }; } },
  set(k, v) { try { localStorage.setItem('hw:' + k, JSON.stringify(v)); } catch { /* private mode: progress not saved */ } },
};

// ------------------------------------------------------------------ routing
function resolveKit(s) { const k = KITS.find(x => x.kit === s || x.url === s); return k ? k.kit : null; }
function parseRoute() {
  let m = location.hash.match(/^#\/([\w-]+)(?:\/step\/(\d+))?/);
  if (!m) m = location.pathname.match(/\/build\/([\w-]+)(?:\/step\/(\d+))?/);
  return m ? { kit: resolveKit(m[1]), n: m[2] ? +m[2] : null } : { kit: null, n: null };
}
function routeUrl(k, step) { return usePath ? `/build/${k}/step/${step}` : `#/${k}/step/${step}`; }
function go(k, step, replace = false) {
  const url = routeUrl(k, step);
  if (usePath) history[replace ? 'replaceState' : 'pushState']({}, '', url); else if (location.hash !== url) location.hash = url;
  route();
}

// ------------------------------------------------------------------ three.js setup
const canvas = $('c');
const renderer = H.makeRenderer(canvas, { alpha: true, shadows: true });
renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(30, 1, 0.001, 50);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true; controls.screenSpacePanning = true; controls.zoomSpeed = 0.9;
const res = new THREE.Vector2(1, 1);
let lightsAdded = false;

function resize() {
  const r = $('stage').getBoundingClientRect();
  renderer.setSize(r.width, r.height, false);
  camera.aspect = r.width / Math.max(1, r.height); camera.updateProjectionMatrix();
  res.set(r.width, r.height);
  if (kit) kit.items.forEach(it => { if (it.outline) it.outline.material.resolution.copy(res); });
}
new ResizeObserver(resize).observe($('stage'));

// ------------------------------------------------------------------ loading a kit
async function loadKit(k) {
  if (kitKey === k && kit) return;
  $('loading').hidden = false; $('loadingText').textContent = 'Loading the model...';
  if (kit) { scene.remove(kit.scene); }
  const base = `/assets/kits/${k}/`;
  [steps, kit] = await Promise.all([fetch(base + 'steps.json').then(r => r.json()), H.loadKit(base + 'kit.glb')]);
  kitKey = k;
  scene.add(kit.scene);
  kit.items.forEach(it => H.setLook(it, 'color'));
  kit.scene.updateMatrixWorld(true);
  const box = H.visibleBox(kit.items);
  if (!lightsAdded) { H.addLights(scene, box); lightsAdded = true; }
  scene.children.filter(o => o.userData.ground).forEach(o => scene.remove(o));
  const g = H.addGround(scene, box, 0.2); g.userData.ground = true;
  const info = KITS.find(x => x.kit === k);
  $('kitName').textContent = info ? info.name : steps.name;
  document.title = `${steps.name}: build in 3D | Hartwood Designs`;
  buildStepList();
  $('loading').hidden = true;
  cacheForOffline(k);
}

// ------------------------------------------------------------------ showing a step
function showStep(step) {
  n = Math.min(Math.max(1, step), steps.steps.length);
  const st = steps.steps[n - 1];
  ctx = H.stepContext(kit, steps, st.n);
  H.applyStep(kit, ctx, 0, { res, colorBuilt });
  kit.scene.updateMatrixWorld(true);
  // fit on the final and the exploded positions so the camera does not jump while the parts move
  H.moveStep(ctx, 1); kit.scene.updateMatrixWorld(true);
  const ex = new THREE.Box3(); ctx.newItems.concat(ctx.mountItems).forEach(it => { if (it.node.visible) ex.expandByObject(it.node); });
  H.moveStep(ctx, 0); kit.scene.updateMatrixWorld(true);
  const fit = H.stepFitBox(kit, ctx, ex.isEmpty() ? null : ex);
  const tmp = camera.clone();
  H.frameCamera(tmp, fit, st.view || H.autoView(ctx), { margin: 1.12, aspect: camera.aspect });
  const target = fit.getCenter(new THREE.Vector3());
  tweenCamera(tmp.position, target, tmp.up);
  animT0 = performance.now();
  tNow = playing ? 1 : (reduceMotion ? 0.5 : 0);
  H.moveStep(ctx, tNow);
  renderPanel(st);
  const p = store.get(kitKey); p.last = n; store.set(kitKey, p);
  updateProgress();
  hideInfo();
}

function tweenCamera(pos, target, up) {
  if (!camTween && camera.position.lengthSq() === 0) {
    camera.position.copy(pos); controls.target.copy(target); camera.up.copy(up); controls.update(); return;
  }
  camTween = { p0: camera.position.clone(), t0: controls.target.clone(), p1: pos.clone(), t1: target.clone(), up: up.clone(),
    start: performance.now(), dur: reduceMotion ? 1 : 650 };
}

function renderPanel(st) {
  $('stepNum').textContent = n;
  $('stepTitle').textContent = st.title;
  $('stepCount').textContent = `Step ${n} of ${steps.steps.length}`;
  $('stepTip').textContent = st.tip || '';
  $('stepIcons').innerHTML = st.icons.concat(st.test ? ['test'] : []).filter(i => ICONS.includes(i))
    .map(i => `<img src="/assets/icons/${i}.svg" alt="${i.replace('-', ' ')}" title="${i}">`).join('');
  const t = $('stepTest'); t.hidden = !st.test; t.querySelector('span').textContent = st.test || '';
  const tray = $('tray'); tray.innerHTML = '';
  const tiles = st.parts.map(p => ({ code: p.code, qty: p.qty, img: `/assets/kits/${kitKey}/parts/${p.code}.webp` }))
    .concat(st.hardware.map(h => ({ code: 'Dowel', qty: 1, img: null, note: h.note })));
  $('trayCount').textContent = tiles.length ? `(${tiles.reduce((a, b) => a + b.qty, 0)})` : '';
  if (!tiles.length) tray.innerHTML = '<p class="none">No new parts. Move the finished section into place.</p>';
  tiles.forEach(tile => {
    const b = document.createElement('button');
    b.setAttribute('role', 'listitem');
    b.innerHTML = (tile.img ? `<img src="${tile.img}" alt="" loading="lazy">` : '<svg viewBox="0 0 76 57" width="76" height="57" aria-hidden="true"><rect x="6" y="25" width="64" height="7" rx="3.5" fill="#B9895B"/></svg>')
      + `${tile.code}${tile.qty > 1 ? ' x' + tile.qty : ''}`;
    b.setAttribute('aria-label', `Part ${tile.code}${tile.qty > 1 ? ', ' + tile.qty + ' pieces' : ''}. Show it in the model.`);
    b.onclick = () => { tray.querySelectorAll('button').forEach(x => x.classList.remove('active')); b.classList.add('active'); highlight(tile.code, tile.note); };
    tray.appendChild(b);
  });
  $('prevBtn').disabled = n <= 1;
  $('nextBtn').textContent = n >= steps.steps.length ? 'Finish' : 'Done, next';
  document.querySelectorAll('#stepItems a').forEach(a => a.toggleAttribute('aria-current', +a.dataset.n === n));
  if (document.querySelector('#stepItems a[aria-current]')) document.querySelector('#stepItems a[aria-current]').setAttribute('aria-current', 'step');
}

function buildStepList() {
  const ol = $('stepItems'); ol.innerHTML = '';
  const p = store.get(kitKey);
  steps.steps.forEach((s, i) => {
    const li = document.createElement('li'); if (i + 1 <= p.done) li.className = 'done';
    li.innerHTML = `<a href="${routeUrl(kitKey, i + 1)}" data-n="${i + 1}"><span class="n">${i + 1}</span><span>${s.title}</span></a>`;
    li.querySelector('a').onclick = e => { e.preventDefault(); toggleList(false); go(kitKey, i + 1); };
    ol.appendChild(li);
  });
}

function updateProgress() {
  const p = store.get(kitKey);
  $('progressFill').style.width = `${Math.round(100 * p.done / steps.steps.length)}%`;
  document.querySelectorAll('#stepItems li').forEach((li, i) => li.classList.toggle('done', i + 1 <= p.done));
}

// ------------------------------------------------------------------ part info and highlight
function prettyName(nm) { return (nm || '').replace(/_peg\d*$/, ' peg').replace(/_/g, ' ').replace(/\b([lr])\b/g, m => (m === 'l' ? 'left' : 'right')); }
function showInfo(it, note) {
  const box = $('partInfo');
  if (!it) { box.innerHTML = `<div><b>Dowel</b><br>${note || ''}</div>`; box.hidden = false; return; }
  const pi = steps.parts_info[it.code] || {};
  const when = it.step === ctx.st.n ? 'New in this step' : `Fitted in step ${steps.steps.findIndex(s => s.n === it.step) + 1}`;
  const img = it.ex.kind === 'part' ? `<img src="/assets/kits/${kitKey}/parts/${it.code}.webp" alt="">` : '';
  const here = ctx.st.parts.find(p => p.code === it.code);
  const qty = here && it.step === ctx.st.n ? here.qty : 0;
  box.innerHTML = `${img}<div><b>${it.ex.kind === 'part' ? it.code : 'Dowel'}</b> ${qty > 1 ? 'x' + qty + ' in this step' : ''}<br>`
    + `${it.ex.kind === 'part' ? `Sheet ${pi.sheet}, ${pi.color}` : (it.ex.note || it.ex.name)}<br><small>${when}`
    + `${pi.mechanism ? '. Moving part: test it as shown.' : ''}</small></div>`;
  box.hidden = false;
}
function hideInfo() { $('partInfo').hidden = true; }
function highlight(code, note) {
  clearTimeout(highlightTimer);
  const its = kit.items.filter(it => it.node.visible && (code === 'Dowel' ? it.ex.kind !== 'part' && it.step === ctx.st.n : it.code === code));
  its.forEach(it => H.setOutline(it, true, LAGOON, 5, res));
  showInfo(code === 'Dowel' ? its[0] || null : its[0], note);
  highlightTimer = setTimeout(() => its.forEach(it => H.restyleItem(ctx, it, res)), 2200);
}

const ray = new THREE.Raycaster();
let downAt = null;
canvas.addEventListener('pointerdown', e => { downAt = [e.clientX, e.clientY]; });
canvas.addEventListener('pointerup', e => {
  if (!downAt || Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 6 || !kit) return;
  const r = canvas.getBoundingClientRect();
  ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), camera);
  const meshes = kit.items.filter(it => it.node.visible).flatMap(it => it.meshes);
  const hit = ray.intersectObjects(meshes, false)[0];
  if (!hit) { hideInfo(); return; }
  let o = hit.object; while (o && !o.userData.item) o = o.parent;
  if (o) { const it = o.userData.item; clearTimeout(highlightTimer); H.setOutline(it, true, LAGOON, 5, res); showInfo(it);
    highlightTimer = setTimeout(() => H.restyleItem(ctx, it, res), 2200); }
});

// ------------------------------------------------------------------ controls
$('prevBtn').onclick = () => go(kitKey, n - 1);
$('nextBtn').onclick = () => {
  const p = store.get(kitKey); p.done = Math.max(p.done, n); store.set(kitKey, p); updateProgress();
  if (n < steps.steps.length) go(kitKey, n + 1);
  else { $('stepTitle').textContent = 'You built it! Well done.'; $('stepTip').textContent = 'Set it on a shelf where you can see it every day.'; }
};
$('playBtn').onclick = () => {
  playing = !playing; animT0 = performance.now() - (playing ? 0 : 0);
  $('playBtn').setAttribute('aria-pressed', String(playing));
  $('playBtn').querySelector('span').textContent = playing ? 'Pause' : 'Play';
  $('playBtn').setAttribute('aria-label', playing ? 'Pause the animation' : 'Play the animation');
  $('playIcon').setAttribute('d', playing ? 'M7 5h3v14H7zM14 5h3v14h-3z' : 'M8 5l11 7-11 7z');
};
$('viewBtn').onclick = () => showStep(n);
$('colorBtn').onclick = () => {
  colorBuilt = !colorBuilt; $('colorBtn').setAttribute('aria-pressed', String(colorBuilt));
  H.applyStep(kit, ctx, tNow, { res, colorBuilt });
};
function toggleList(open) { $('stepList').hidden = !open; $('menuBtn').setAttribute('aria-expanded', String(open)); }
$('menuBtn').onclick = () => toggleList($('stepList').hidden);
$('closeList').onclick = () => toggleList(false);
$('resetProgress').onclick = () => { store.set(kitKey, { done: 0, last: 1 }); updateProgress(); };
addEventListener('keydown', e => {
  if (!kit || $('picker').hidden === false) return;
  if (e.key === 'ArrowRight') $('nextBtn').click();
  if (e.key === 'ArrowLeft' && n > 1) go(kitKey, n - 1);
  if (e.key === 'Escape') toggleList(false);
});

// ------------------------------------------------------------------ render loop
const ease = x => (x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2);
function frame(now) {
  requestAnimationFrame(frame);
  if (!kit || !ctx) return;
  if (camTween) {
    const u = Math.min(1, (now - camTween.start) / camTween.dur), k = ease(u);
    camera.position.lerpVectors(camTween.p0, camTween.p1, k); controls.target.lerpVectors(camTween.t0, camTween.t1, k);
    camera.up.copy(camTween.up); if (u >= 1) camTween = null;
  }
  if (playing) {
    const ph = ((now - animT0) / 1000) % 3.2;
    tNow = ph < 0.5 ? 1 : ph < 2.0 ? 1 - ease((ph - 0.5) / 1.5) : 0;
    H.moveStep(ctx, tNow);
  }
  controls.update();
  renderer.render(scene, camera);
}
requestAnimationFrame(frame);

// ------------------------------------------------------------------ offline
function cacheForOffline(k) {
  if (!('serviceWorker' in navigator) || !navigator.serviceWorker.controller) return;
  const base = `/assets/kits/${k}/`;
  const urls = [base + 'kit.glb', base + 'steps.json', ...steps.parts.map(p => `${base}parts/${p.code}.webp`)];
  navigator.serviceWorker.controller.postMessage({ type: 'cache-kit', kit: k, urls });
}
if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
  navigator.serviceWorker.register('/sw.js').catch(() => {});
  navigator.serviceWorker.addEventListener('message', e => {
    if (e.data && e.data.type === 'kit-cached' && e.data.kit === kitKey) {
      $('offlineBadge').hidden = false; setTimeout(() => { $('offlineBadge').hidden = true; }, 3500);
    }
  });
}

// ------------------------------------------------------------------ start
function showPicker() {
  $('picker').hidden = false;
  $('kitCards').innerHTML = KITS.map(k => {
    const p = store.get(k.kit);
    return `<a class="kitcard" href="${routeUrl(k.kit, p.last || 1)}"><img src="/assets/kits/${k.kit}/renders/three_quarter_sm.webp" alt="${k.name}">`
      + `<div><h3>${k.name}</h3><p class="meta">${k.pieces} pieces, ${k.steps} steps${p.done ? `, ${p.done} done` : ''}</p></div></a>`;
  }).join('');
}

async function route() {
  const r = parseRoute();
  if (!r.kit) { showPicker(); return; }
  $('picker').hidden = true;
  try { await loadKit(r.kit); } catch (err) {
    $('loadingText').textContent = 'Could not load this kit. Check your connection and try again.'; return;
  }
  if (!r.n) { go(r.kit, store.get(r.kit).last || 1, true); return; }
  resize();
  showStep(r.n);
}

addEventListener('popstate', route);
addEventListener('hashchange', route);
fetch('/assets/kits/kits.json').then(r => r.json()).then(k => { KITS = k; route(); })
  .catch(() => { $('loadingText').textContent = 'Could not load the kit list.'; });
