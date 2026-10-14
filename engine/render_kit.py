"""Hero renders, close-ups and one image per part code for a kit.

    python engine/render_kit.py blaster [--heroes] [--parts]

Writes kits/<kit>/renders/raw/*.webp (transparent), kits/<kit>/renders/*.png (on a backdrop) and
kits/<kit>/parts/<code>.png (transparent, laser face toward the camera).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

VIEWS = {
    'blaster': {
        'three_quarter': dict(view=[0.75, 0.35, 1.2]),
        'front': dict(view=[0.06, 0.12, 1.0]),
        'back': dict(view=[-0.75, 0.4, -1.0]),
        'top': dict(view=[0.1, 1.0, 0.45]),
        'closeup_wheel': dict(view=[0.35, 0.55, 1.0], target=[-55, 12, 10], zoom=3.2, square=True),
        'closeup_nose': dict(view=[1.0, 0.45, 0.75], target=[148, 10, 0], zoom=3.6, square=True),
        'closeup_stand': dict(view=[0.35, 0.3, 1.0], target=[80, -88, 0], zoom=2.4, square=True),
        'lifted': dict(view=[0.7, 0.3, 1.2], lift=('ship', 70.0)),
    },
    'dragon': {
        'three_quarter': dict(view=[0.75, 0.35, 1.2]),
        'front': dict(view=[1.0, 0.25, 0.3]),
        'side': dict(view=[0.05, 0.15, 1.0]),
        'back': dict(view=[-0.8, 0.4, -0.9]),
        'closeup_head': dict(view=[1.0, 0.3, 0.7], target=[95, 208, 0], zoom=3.6, square=True),
        'closeup_claws': dict(view=[0.85, 0.3, 1.0], target=[66, 90, 21], zoom=3.8, square=True),
        'closeup_chest': dict(view=[0.45, 0.3, 1.0], target=[30, 48, 68], zoom=3.4, square=True),
    },
    'floral': {
        'three_quarter': dict(view=[0.75, 0.45, 1.2]),
        'front': dict(view=[0.05, 0.2, 1.0]),
        'back': dict(view=[-0.6, 0.4, -1.0]),
        'top': dict(view=[0.1, 1.0, 0.35]),
        'closeup_flowers': dict(view=[0.4, 0.3, 1.0], target=[0, 238, 20], zoom=2.3, square=True),
        'closeup_rose': dict(view=[0.7, 0.35, 1.0], target=[46, 246, 19], zoom=4.5, square=True),
        'closeup_base': dict(view=[0.6, 0.45, 1.0], target=[0, 90, 0], zoom=2.0, square=True),
    },
}

BACKDROP = ((252, 247, 238), (233, 216, 190))     # cream centre, warm wood edge


def backdrop(w, h):
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w * 0.5) / (w * 0.75)) ** 2 + ((yy - h * 0.42) / (h * 0.8)) ** 2)
    t = np.clip(r, 0, 1)[..., None] ** 1.6
    c0, c1 = np.array(BACKDROP[0], float), np.array(BACKDROP[1], float)
    img = (c0 * (1 - t) + c1 * t).astype(np.uint8)
    return Image.fromarray(img, 'RGB')


def run_jobs(jobs):
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(jobs, f)
        path = f.name
    subprocess.run(['node', os.path.join(ROOT, 'engine/render/render.mjs'), path], check=True, cwd=ROOT,
                   stdout=subprocess.DEVNULL)
    os.unlink(path)


def heroes(kit):
    jobs = []
    for name, v in VIEWS[kit].items():
        w, h = (1400, 1400) if v.get('square') else (1800, 1350)
        j = {'glb': f'/kits/{kit}/{kit}.glb', 'out': f'kits/{kit}/renders/raw/{name}.png', 'mode': 'hero',
             'view': v['view'], 'width': w, 'height': h, 'margin': 1.0 if 'target' not in v else 1.06, 'shadow': 0.22}
        if 'target' in v:
            j['target'] = v['target']; j['zoom'] = v['zoom']
        if 'lift' in v:
            steps = json.load(open(os.path.join(ROOT, 'kits', kit, f'{kit}_steps.json')))
            members = [m_ for st in steps['steps'] for mo in st['mounts'] if mo['name'] == v['lift'][0] for m_ in mo['members']]
            j['lift'] = {'members': members, 'dy': v['lift'][1]}
        jobs.append(j)
    run_jobs(jobs)
    for name in VIEWS[kit]:
        raw = Image.open(os.path.join(ROOT, f'kits/{kit}/renders/raw/{name}.png')).convert('RGBA')
        bg = backdrop(*raw.size).convert('RGBA')
        bg.alpha_composite(raw)
        bg.convert('RGB').save(os.path.join(ROOT, f'kits/{kit}/renders/{name}.jpg'), quality=90)
        # keep the transparent version small: WebP with alpha for the website
        raw.save(os.path.join(ROOT, f'kits/{kit}/renders/raw/{name}.webp'), quality=88, method=5)
        os.unlink(os.path.join(ROOT, f'kits/{kit}/renders/raw/{name}.png'))
    print(f'{kit}: {len(jobs)} hero renders')


def parts(kit):
    steps = json.load(open(os.path.join(ROOT, f'kits/{kit}/{kit}_steps.json')))
    codes = [p['code'] for p in steps['parts']]
    out = os.path.join(ROOT, f'kits/{kit}/parts')
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.unlink(os.path.join(out, f))
    jobs = [{'glb': f'/kits/{kit}/{kit}.glb', 'out': f'kits/{kit}/parts/{c}.png', 'mode': 'part', 'codes': [c], 'single': True,
             'view': 'face', 'width': 480, 'height': 360, 'margin': 1.12} for c in codes]
    run_jobs(jobs)
    print(f'{kit}: {len(jobs)} part images')


if __name__ == '__main__':
    kit = sys.argv[1]
    flags = set(sys.argv[2:]) or {'--heroes', '--parts'}
    if '--heroes' in flags:
        heroes(kit)
    if '--parts' in flags:
        parts(kit)
