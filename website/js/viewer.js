// Product page 3D viewer: loads the kit model only when asked (saves data on phones).
import * as H from '/js/hw3d.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const box = document.getElementById('viewer');
const btn = document.getElementById('viewerBtn');
if (box && btn) {
  btn.addEventListener('click', async () => {
    btn.disabled = true; btn.textContent = 'Loading...';
    const THREE = H.THREE;
    const canvas = document.getElementById('viewerCanvas');
    const renderer = H.makeRenderer(canvas, { alpha: true, shadows: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    const scene = new THREE.Scene();
    const kit = await H.loadKit(box.dataset.glb);
    kit.items.forEach(it => H.setLook(it, 'color'));
    scene.add(kit.scene); kit.scene.updateMatrixWorld(true);
    const bb = H.visibleBox(kit.items);
    H.addLights(scene, bb); H.addGround(scene, bb, 0.2);
    const camera = new THREE.PerspectiveCamera(30, 1, 0.001, 50);
    const controls = new OrbitControls(camera, canvas);
    controls.enableDamping = true; controls.autoRotate = !matchMedia('(prefers-reduced-motion: reduce)').matches; controls.autoRotateSpeed = 1.2;
    box.classList.add('loaded');
    const fit = () => {
      const r = box.getBoundingClientRect(); renderer.setSize(r.width, r.height, false);
      camera.aspect = r.width / r.height; H.frameCamera(camera, bb, [0.75, 0.4, 1.1], { margin: 1.05, aspect: camera.aspect });
      controls.target.copy(bb.getCenter(new THREE.Vector3())); controls.update();
    };
    fit(); new ResizeObserver(fit).observe(box);
    controls.addEventListener('start', () => { controls.autoRotate = false; });
    renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
  });
}
