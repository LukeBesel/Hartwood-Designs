"""Copy kit data into the static website (website/assets/kits/<kit>/) in web-friendly sizes.

    .venv/bin/python tools/build_site.py
"""
from __future__ import annotations

import json
import os
import shutil

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SITE = os.path.join(ROOT, 'website')
KITS = ['blaster', 'dragon', 'floral']
AGE = '14+'
SLUG_URL = {'blaster': 'star-slinger', 'dragon': 'emberwing', 'floral': 'blossom-waltz'}
COLOR_LABEL = None


def webp(src, dst, width=None, quality=82):
    im = Image.open(src)
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, 'WEBP', quality=quality, method=5)


def glb_size_mm(path):
    """Finished size (x length, y height, z depth) in mm from the GLB node matrices and mesh bounds."""
    import struct
    import numpy as np
    b = open(path, 'rb').read()
    n = struct.unpack('<I', b[12:16])[0]
    js = json.loads(b[20:20 + n])
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    root = js['nodes'][0]
    for ci in root.get('children', []):
        node = js['nodes'][ci]
        if 'mesh' not in node:
            continue
        M = np.array(node.get('matrix', np.eye(4).flatten().tolist())).reshape(4, 4).T
        for prim in js['meshes'][node['mesh']]['primitives']:
            acc = js['accessors'][prim['attributes']['POSITION']]
            mn, mx = acc['min'], acc['max']
            for i in range(8):
                c = np.array([mx[0] if i & 1 else mn[0], mx[1] if i & 2 else mn[1], mx[2] if i & 4 else mn[2], 1.0])
                w = (M @ c)[:3]
                lo = np.minimum(lo, w); hi = np.maximum(hi, w)
    return [round(float(v)) for v in (hi - lo)]


def main():
    import sys
    sys.path.insert(0, os.path.join(ROOT, 'engine'))
    from hartwood import config as C
    summary = []
    for kit in KITS:
        src = os.path.join(ROOT, 'kits', kit)
        dst = os.path.join(SITE, 'assets', 'kits', kit)
        shutil.rmtree(dst, ignore_errors=True)
        os.makedirs(os.path.join(dst, 'parts')); os.makedirs(os.path.join(dst, 'renders'))
        shutil.copy(os.path.join(src, f'{kit}.glb'), os.path.join(dst, 'kit.glb'))
        steps = json.load(open(os.path.join(src, f'{kit}_steps.json')))
        views = json.load(open(os.path.join(src, 'booklet', 'step_views.json')))
        for s in steps['steps']:
            s['view'] = s['view'] or views.get(str(s['n']))
        for sh in steps['sheets']:
            sh['face'] = C.MATERIALS[sh['color']]['face']
        steps['parts_info'] = {p['code']: {'sheet': p['sheet'], 'color': C.MATERIALS[p['color']]['label'], 'qty': p['qty'],
                                           'mechanism': p['mechanism']} for p in steps['parts']}
        json.dump(steps, open(os.path.join(dst, 'steps.json'), 'w'), separators=(',', ':'))
        for f in os.listdir(os.path.join(src, 'parts')):
            webp(os.path.join(src, 'parts', f), os.path.join(dst, 'parts', f[:-4] + '.webp'), 240, 80)
        for f in os.listdir(os.path.join(src, 'renders')):
            if f.endswith('.jpg'):
                webp(os.path.join(src, 'renders', f), os.path.join(dst, 'renders', f[:-4] + '.webp'), 1400, 82)
                webp(os.path.join(src, 'renders', f), os.path.join(dst, 'renders', f[:-4] + '_sm.webp'), 640, 78)
        for f in os.listdir(os.path.join(src, 'renders', 'raw')):
            shutil.copy(os.path.join(src, 'renders', 'raw', f), os.path.join(dst, 'renders', 'cut_' + f))
        shutil.copy(os.path.join(src, 'booklet', f'{kit}_instructions.pdf'), os.path.join(dst, f'{kit}_instructions.pdf'))
        rep = json.load(open(os.path.join(src, f'{kit}_report.json')))
        summary.append({'kit': kit, 'url': SLUG_URL[kit], 'name': steps['name'], 'tagline': steps['tagline'],
                        'story': steps['story'], 'price': steps['price'], 'pieces': steps['piece_count'],
                        'steps': len(steps['steps']), 'hours': steps['build_hours'], 'difficulty': steps['difficulty'],
                        'age': AGE, 'mechanism': bool(rep['mechanism_parts']), 'extras': steps['extras'],
                        'size_mm': glb_size_mm(os.path.join(src, f'{kit}.glb')),
                        'sheets': [f"{sh['label']}" for sh in steps['sheets']]})
        print(kit, 'assets copied')
    json.dump(summary, open(os.path.join(SITE, 'assets', 'kits', 'kits.json'), 'w'), indent=1)
    os.makedirs(os.path.join(SITE, 'assets', 'icons'), exist_ok=True)
    for f in os.listdir(os.path.join(ROOT, 'brand', 'icons')):
        if f.endswith('.svg'):
            shutil.copy(os.path.join(ROOT, 'brand', 'icons', f), os.path.join(SITE, 'assets', 'icons', f))


if __name__ == '__main__':
    main()
