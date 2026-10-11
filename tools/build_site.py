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
                        'age': AGE, 'mechanism': bool(rep['mechanism_parts']), 'extras': steps['extras']})
        print(kit, 'assets copied')
    json.dump(summary, open(os.path.join(SITE, 'assets', 'kits', 'kits.json'), 'w'), indent=1)
    os.makedirs(os.path.join(SITE, 'assets', 'icons'), exist_ok=True)
    for f in os.listdir(os.path.join(ROOT, 'brand', 'icons')):
        if f.endswith('.svg'):
            shutil.copy(os.path.join(ROOT, 'brand', 'icons', f), os.path.join(SITE, 'assets', 'icons', f))


if __name__ == '__main__':
    main()
