// Hartwood 3D: shared by the instruction app (website/build) and the render pipeline (engine/render).
// Loads a kit GLB exported by the Python engine and styles it: natural wood with grain, burned laser
// edges, engraved detail, colored sheets, and "booklet" mode (built parts gray, new parts orange outline).
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js';
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';

export { THREE };

export const ORANGE = 0xff7a1a;      // new-part outline
const GRAY_FACE = 0xe9e6e1;
const GRAY_EDGE = 0xb9b3aa;

// ------------------------------------------------------------------ procedural textures
function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

const texCache = {};
export function woodTexture(base = '#e6c99a', seed = 7, painted = false) {
  const key = base + seed + painted;
  if (texCache[key]) return texCache[key];
  const N = 512, c = document.createElement('canvas'); c.width = c.height = N;
  const g = c.getContext('2d'), r = rng(seed);
  g.fillStyle = base; g.fillRect(0, 0, N, N);
  const col = new THREE.Color(base);
  if (!painted) {
    // grain: wavy streaks along x
    for (let i = 0; i < 140; i++) {
      const y0 = r() * N, amp = 2 + r() * 6, freq = 0.004 + r() * 0.01, ph = r() * 6.28;
      const dark = r() < 0.6; const a = 0.05 + r() * 0.10;
      const cc = col.clone().offsetHSL(0, dark ? 0.02 : -0.02, dark ? -0.10 - r() * 0.08 : 0.05);
      g.strokeStyle = `rgba(${(cc.r * 255) | 0},${(cc.g * 255) | 0},${(cc.b * 255) | 0},${a})`;
      g.lineWidth = 0.6 + r() * 2.2; g.beginPath();
      for (let x = -10; x <= N + 10; x += 8) { const y = y0 + amp * Math.sin(x * freq + ph) + 3 * Math.sin(x * freq * 3.1 + ph * 2); x < 0 ? g.moveTo(x, y) : g.lineTo(x, y); }
      g.stroke();
    }
  }
  // fine noise
  const img = g.getImageData(0, 0, N, N), d = img.data;
  for (let i = 0; i < d.length; i += 4) { const n = (r() - 0.5) * (painted ? 6 : 10); d[i] += n; d[i + 1] += n; d[i + 2] += n; }
  g.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  texCache[key] = t; return t;
}

// ------------------------------------------------------------------ materials
const matCache = {};
function srgbHex(mat) { return '#' + mat.color.clone().convertLinearToSRGB().getHexString(); }

function styledMaterial(orig) {
  const name = orig.name || '';
  if (matCache[name]) return matCache[name];
  const base = srgbHex(orig);
  let m;
  if (name === 'face_natural') {
    m = new THREE.MeshStandardMaterial({ map: woodTexture(base, 3), roughness: 0.78, metalness: 0 });
  } else if (name.startsWith('face_')) {
    m = new THREE.MeshStandardMaterial({ map: woodTexture(base, 5, true), roughness: 0.62, metalness: 0 });
  } else if (name.startsWith('edge_')) {
    m = new THREE.MeshStandardMaterial({ color: base, roughness: 1.0, metalness: 0 });
  } else if (name.startsWith('engrave_')) {
    m = new THREE.MeshStandardMaterial({ color: base, roughness: 1.0, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  } else if (name === 'dowel') {
    m = new THREE.MeshStandardMaterial({ map: woodTexture('#d9b98a', 11), roughness: 0.7 });
  } else if (name === 'metal') {
    m = new THREE.MeshStandardMaterial({ color: base, roughness: 0.35, metalness: 0.8 });
  } else {
    m = orig;
  }
  m.name = name; matCache[name] = m; return m;
}

const grayMats = {
  face: new THREE.MeshStandardMaterial({ color: GRAY_FACE, roughness: 0.9 }),
  edge: new THREE.MeshStandardMaterial({ color: GRAY_EDGE, roughness: 1 }),
  engrave: new THREE.MeshStandardMaterial({ color: 0xcfc9c0, roughness: 1, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }),
};
const ghostMat = new THREE.MeshStandardMaterial({ color: GRAY_FACE, roughness: 1, transparent: true, opacity: 0.35, depthWrite: false });

function primKind(name) {
  if (name.startsWith('face_') || name === 'dowel' || name === 'metal') return 'face';
  if (name.startsWith('edge_')) return 'edge';
  if (name.startsWith('engrave_')) return 'engrave';
  return 'face';
}

// ------------------------------------------------------------------ loading
export async function loadKit(url) {
  const gltf = await new GLTFLoader().loadAsync(url);
  const root = gltf.scene.children[0] || gltf.scene;
  const items = [];
  root.children.forEach(node => {
    const ex = node.userData || {};
    const meshes = [];
    node.traverse(o => {
      if (o.isMesh) {
        o.userData.origMat = o.material;
        o.userData.kind = primKind(o.material.name || '');
        o.material = styledMaterial(o.material);
        o.userData.colorMat = o.material;
        o.castShadow = true; o.receiveShadow = true;
        meshes.push(o);
      }
    });
    const item = {
      node, meshes, ex, code: ex.code || node.name, step: ex.step || 1,
      final: node.position.clone(), insert: new THREE.Vector3(...(ex.insert || [0, -1, 0])),
      explode: ex.explode || 40, outline: null,
    };
    node.userData.item = item;
    items.push(item);
  });
  const steps = [...new Set(items.map(i => i.step))].sort((a, b) => a - b);
  return { scene: gltf.scene, root, items, steps };
}

// ------------------------------------------------------------------ styling
export function edgeLines(item, color, widthPx, res) {
  const pos = [];
  item.meshes.filter(m => m.userData.kind === 'edge' || item.ex.kind !== 'part').forEach(m => {
    const eg = new THREE.EdgesGeometry(m.geometry, 28);
    const a = eg.attributes.position.array;
    for (let i = 0; i < a.length; i++) pos.push(a[i]);
    eg.dispose();
  });
  const g = new LineSegmentsGeometry(); g.setPositions(pos);
  const mat = new LineMaterial({ color, linewidth: widthPx, worldUnits: false });
  if (res) mat.resolution.copy(res);
  const l = new LineSegments2(g, mat); l.computeLineDistances?.(); l.renderOrder = 2;
  return l;
}

export function setLook(item, look, opts = {}) {
  // look: 'color' | 'gray' | 'ghost' | 'hidden'
  item.node.visible = look !== 'hidden';
  item.meshes.forEach(m => {
    if (look === 'color') m.material = m.userData.colorMat;
    else if (look === 'gray') m.material = grayMats[m.userData.kind] || grayMats.face;
    else if (look === 'ghost') m.material = ghostMat;
  });
}

export function setOutline(item, on, color = ORANGE, widthPx = 3, res = null) {
  if (item.outline) { item.node.remove(item.outline); item.outline.geometry.dispose(); item.outline = null; }
  if (on) { item.outline = edgeLines(item, color, widthPx, res); item.node.add(item.outline); }
}

export function setExplode(item, t) {
  // t = 0 final position, 1 fully exploded (back along -insert by `explode` mm, in root units)
  item.node.position.copy(item.final).addScaledVector(item.insert, -item.explode * t);
}

// ------------------------------------------------------------------ scene helpers
export function makeRenderer(canvas, { alpha = true, preserve = false, shadows = true } = {}) {
  const r = new THREE.WebGLRenderer({ canvas, antialias: true, alpha, preserveDrawingBuffer: preserve });
  r.outputColorSpace = THREE.SRGBColorSpace;
  r.toneMapping = THREE.NeutralToneMapping; r.toneMappingExposure = 1.0;
  r.shadowMap.enabled = shadows; r.shadowMap.type = THREE.PCFSoftShadowMap;
  return r;
}

export function addLights(scene, box) {
  const size = box.getSize(new THREE.Vector3()).length() || 1;
  const c = box.getCenter(new THREE.Vector3());
  scene.add(new THREE.HemisphereLight(0xfff6e8, 0x8a7a66, 1.15));
  const key = new THREE.DirectionalLight(0xffffff, 2.1);
  key.position.set(c.x + size * 0.6, c.y + size * 1.1, c.z + size * 0.8);
  key.target.position.copy(c);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048);
  const s = size * 0.8; Object.assign(key.shadow.camera, { left: -s, right: s, top: s, bottom: -s, near: 0.001, far: size * 4 });
  key.shadow.bias = -0.0004; key.shadow.normalBias = 0.002 * size; key.shadow.radius = 4;
  scene.add(key, key.target);
  const fill = new THREE.DirectionalLight(0xdfe8ff, 0.55); fill.position.set(c.x - size, c.y + size * 0.4, c.z - size * 0.3); scene.add(fill);
  const rim = new THREE.DirectionalLight(0xffffff, 0.45); rim.position.set(c.x - size * 0.3, c.y + size * 0.5, c.z - size * 1.2); scene.add(rim);
  return { key, fill, rim };
}

export function addGround(scene, box, shadowOpacity = 0.22) {
  const size = box.getSize(new THREE.Vector3());
  const g = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.ShadowMaterial({ opacity: shadowOpacity }));
  g.rotation.x = -Math.PI / 2; g.scale.setScalar(Math.max(size.x, size.z) * 6 + 0.5);
  g.position.set((box.min.x + box.max.x) / 2, box.min.y - 0.0002, (box.min.z + box.max.z) / 2);
  g.receiveShadow = true; scene.add(g); return g;
}

export function visibleBox(items) {
  const b = new THREE.Box3();
  items.forEach(it => { if (it.node.visible) b.expandByObject(it.node); });
  return b;
}

export function frameCamera(camera, box, dir, { margin = 1.12, aspect = 1 } = {}) {
  const c = box.getCenter(new THREE.Vector3());
  const d = new THREE.Vector3(...dir).normalize();
  const up = Math.abs(d.y) > 0.98 ? new THREE.Vector3(0, 0, -1) : new THREE.Vector3(0, 1, 0);
  const size = box.getSize(new THREE.Vector3()).length();
  camera.up.copy(up);
  if (camera.isOrthographicCamera) {
    camera.position.copy(c).addScaledVector(d, size * 2); camera.lookAt(c);
    camera.updateMatrixWorld();
    // fit box corners in view space
    const inv = camera.matrixWorldInverse; let mx = 0, my = 0;
    for (let i = 0; i < 8; i++) {
      const p = new THREE.Vector3(i & 1 ? box.max.x : box.min.x, i & 2 ? box.max.y : box.min.y, i & 4 ? box.max.z : box.min.z).applyMatrix4(inv);
      const q = c.clone().applyMatrix4(inv);
      mx = Math.max(mx, Math.abs(p.x - q.x)); my = Math.max(my, Math.abs(p.y - q.y));
    }
    let hw = mx * margin, hh = my * margin;
    if (hw / hh > aspect) hh = hw / aspect; else hw = hh * aspect;
    Object.assign(camera, { left: -hw, right: hw, top: hh, bottom: -hh, near: 0.0001, far: size * 6 });
    camera.updateProjectionMatrix();
  } else {
    const fov = THREE.MathUtils.degToRad(camera.fov);
    const radius = box.getBoundingSphere(new THREE.Sphere()).radius;
    const dist = radius * margin / Math.sin(Math.min(fov, fov * aspect) / 2);
    camera.position.copy(c).addScaledVector(d, dist); camera.lookAt(c);
    camera.near = dist / 100; camera.far = dist * 10; camera.updateProjectionMatrix();
  }
  return c;
}

export function arrow(from, to, color = 0x2b1d12, radius = 0.0012) {
  const g = new THREE.Group();
  const dir = to.clone().sub(from); const L = dir.length(); if (L < 1e-6) return g;
  const head = Math.min(L * 0.35, radius * 7);
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, L - head, 12), new THREE.MeshBasicMaterial({ color }));
  shaft.position.y = (L - head) / 2;
  const cone = new THREE.Mesh(new THREE.ConeGeometry(radius * 3, head, 16), new THREE.MeshBasicMaterial({ color }));
  cone.position.y = L - head / 2;
  g.add(shaft, cone);
  g.position.copy(from);
  g.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());
  g.renderOrder = 3;
  return g;
}

export function worldCenter(item) {
  const b = new THREE.Box3().expandByObject(item.node);
  return b.getCenter(new THREE.Vector3());
}
