"""Booklet and app icons, drawn in the brand style (walnut ink on a maple disc). PNG 256 px + SVG.

    python engine/icons.py  ->  brand/icons/<name>.png and .svg
"""
from __future__ import annotations

import os
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'brand', 'icons')
INK, DISC, ACC, BLAZE, OAK = '#3A2A1F', '#EBD5B0', '#0F8B7F', '#FF6A13', '#B9895B'
SW = 'stroke="%s" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none"' % INK

ICONS = {
    # thumb pressing a tab into a slot
    'press': f'''<rect x="24" y="66" width="52" height="14" rx="2" fill="{OAK}" stroke="{INK}" stroke-width="5"/>
      <rect x="42" y="48" width="16" height="22" rx="2" fill="#F6EEE1" stroke="{INK}" stroke-width="5"/>
      <path d="M50 14 L50 38 M41 29 L50 38 L59 29" {SW}/>''',
    # wax stick rubbing a hole
    'wax': f'''<rect x="30" y="18" width="20" height="44" rx="4" transform="rotate(35 40 40)" fill="#F6EEE1" stroke="{INK}" stroke-width="5"/>
      <circle cx="62" cy="68" r="12" fill="{OAK}" stroke="{INK}" stroke-width="5"/>
      <path d="M50 82 Q62 90 76 80" {SW}/>''',
    # flip the model over
    'flip': f'''<path d="M26 44 A26 26 0 0 1 74 40" {SW}/><path d="M66 30 L75 41 L62 46" {SW}/>
      <path d="M74 58 A26 26 0 0 1 26 62" {SW}/><path d="M34 72 L25 61 L38 56" {SW}/>''',
    # take care: warning triangle
    'careful': f'''<path d="M50 16 L84 78 L16 78 Z" fill="#FCE9A8" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>
      <path d="M50 38 L50 58" {SW}/><circle cx="50" cy="68" r="4" fill="{INK}"/>''',
    # test it now: check mark in a ring
    'test': f'''<circle cx="50" cy="50" r="30" fill="#D7EFEB" stroke="{ACC}" stroke-width="6"/>
      <path d="M36 51 L46 61 L65 40" stroke="{ACC}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    # centre: start from the middle
    'centre': f'''<circle cx="50" cy="50" r="28" {SW}/><circle cx="50" cy="50" r="8" fill="{ACC}"/>
      <path d="M50 12 L50 24 M50 76 L50 88 M12 50 L24 50 M76 50 L88 50" {SW}/>''',
    # do not glue
    'no-glue': f'''<path d="M38 30 L62 30 L60 76 L40 76 Z" fill="#F6EEE1" stroke="{INK}" stroke-width="5"/>
      <path d="M44 30 L46 18 L54 18 L56 30" {SW}/><circle cx="50" cy="50" r="38" stroke="#C0392B" stroke-width="6" fill="none"/>
      <path d="M23 77 L77 23" stroke="#C0392B" stroke-width="6" stroke-linecap="round"/>''',
    # push parts out from the back of the sheet
    'push-out': f'''<rect x="16" y="22" width="68" height="56" rx="3" fill="{OAK}" stroke="{INK}" stroke-width="5"/>
      <rect x="34" y="36" width="32" height="28" rx="2" fill="#F6EEE1" stroke="{INK}" stroke-width="5" stroke-dasharray="6 4"/>
      <path d="M50 92 L50 70 M42 78 L50 70 L58 78" {SW}/>''',
    # sand a tight tab
    'sand': f'''<rect x="22" y="40" width="40" height="26" rx="3" fill="#E8C9A0" stroke="{INK}" stroke-width="5"/>
      <circle cx="32" cy="50" r="2" fill="{INK}"/><circle cx="42" cy="56" r="2" fill="{INK}"/><circle cx="52" cy="48" r="2" fill="{INK}"/>
      <path d="M66 46 L82 46 M66 60 L82 60" {SW}/>''',
    # rubber band safety: eye protection
    'glasses': f'''<circle cx="33" cy="54" r="14" {SW}/><circle cx="67" cy="54" r="14" {SW}/>
      <path d="M47 52 Q50 48 53 52 M19 50 L10 42 M81 50 L90 42" {SW}/>''',
    # turn / spin freely
    'spin': f'''<circle cx="50" cy="50" r="8" fill="{ACC}"/><path d="M78 50 A28 28 0 1 1 64 26" {SW}/>
      <path d="M58 16 L66 27 L54 32" {SW}/>''',
    # sort the parts by sheet
    'sort': f'''<rect x="14" y="56" width="20" height="24" rx="2" fill="{OAK}" stroke="{INK}" stroke-width="4"/>
      <rect x="40" y="46" width="20" height="34" rx="2" fill="#F6EEE1" stroke="{INK}" stroke-width="4"/>
      <rect x="66" y="36" width="20" height="44" rx="2" fill="#D7EFEB" stroke="{INK}" stroke-width="4"/>
      <path d="M18 30 L84 20" {SW}/>''',
}


def counter(n):
    return (f'<rect x="18" y="28" width="64" height="44" rx="12" fill="{ACC}"/>'
            f'<text x="50" y="62" text-anchor="middle" font-family="Inter, DejaVu Sans, sans-serif" font-weight="800" '
            f'font-size="32" fill="#FFFFFF">x{n}</text>')


for n in (2, 3, 4, 6, 8):
    ICONS[f'x{n}'] = counter(n)


def svg(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="256" height="256">'
            f'<circle cx="50" cy="50" r="48" fill="{DISC}"/>{body}</svg>\n')


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, body in ICONS.items():
        p = os.path.join(OUT, f'{name}.svg')
        open(p, 'w').write(svg(body))
        subprocess.run(['node', os.path.join(ROOT, 'tools/svg2png.js'), p, p[:-4] + '.png', '256', '256'], check=True)
    print(len(ICONS), 'icons in', OUT)


if __name__ == '__main__':
    main()
