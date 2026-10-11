"""Hartwood Designs brand files: logo SVGs (text converted to paths), PNG versions, palette JSON, favicon.

    python brand/make_brand.py
"""
from __future__ import annotations

import json
import os
import subprocess

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PALETTE = {
    'walnut': {'hex': '#3A2A1F', 'use': 'text, outlines'},
    'oak': {'hex': '#B9895B', 'use': 'secondary wood tone, borders'},
    'maple': {'hex': '#EBD5B0', 'use': 'wood light, cards'},
    'birch': {'hex': '#F6EEE1', 'use': 'surfaces, page bands'},
    'paper': {'hex': '#FCF8F1', 'use': 'page background'},
    'lagoon': {'hex': '#0F8B7F', 'use': 'the one bright accent: buttons, links, highlights'},
    'lagoon_dark': {'hex': '#0B6158', 'use': 'accent text on light backgrounds (AA contrast)'},
    'lagoon_light': {'hex': '#D7EFEB', 'use': 'accent tint backgrounds'},
    'blaze': {'hex': '#FF6A13', 'use': 'safety orange: only for the blaster tip and safety notes'},
}
FONTS = {'display': 'Fraunces (SIL OFL), weights 600 to 800', 'body': 'Inter (SIL OFL), weights 400 to 700'}


def text_path(txt, font_file, size, x, y, tracking=0.0):
    """SVG path data for txt, baseline at y, starting at x. Returns (d, advance width)."""
    f = TTFont(font_file)
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    upm = f['head'].unitsPerEm
    s = size / upm
    pen = SVGPathPen(gs)
    cx = x
    for ch in txt:
        gname = cmap.get(ord(ch))
        if gname is None:
            continue
        tp = TransformPen(pen, (s, 0, 0, -s, cx, y))
        gs[gname].draw(tp)
        cx += gs[gname].width * s + tracking * size
    return pen.getCommands(), cx - x - tracking * size


def mark(x=0, y=0, size=100):
    """The mark: an H built from two planks and a half-lapped crossbar on a lagoon tile with growth rings."""
    k = size / 100
    P = PALETTE
    g = [f'<g transform="translate({x},{y}) scale({k})">',
         f'<rect x="0" y="0" width="100" height="100" rx="22" fill="{P["lagoon"]["hex"]}"/>',
         '<g fill="none" stroke="#FFFFFF" stroke-opacity="0.16" stroke-width="2.2">',
         '<circle cx="50" cy="50" r="40"/><circle cx="50" cy="50" r="31"/><circle cx="50" cy="50" r="22"/></g>',
         # crossbar behind, with two square pegs
         f'<rect x="27" y="43" width="46" height="14" rx="2.5" fill="{P["oak"]["hex"]}" stroke="{P["walnut"]["hex"]}" stroke-width="2"/>',
         # planks
         f'<rect x="22" y="19" width="15" height="62" rx="3" fill="{P["maple"]["hex"]}" stroke="{P["walnut"]["hex"]}" stroke-width="2"/>',
         f'<rect x="63" y="19" width="15" height="62" rx="3" fill="{P["maple"]["hex"]}" stroke="{P["walnut"]["hex"]}" stroke-width="2"/>',
         # half-lap notches where the bar passes through
         f'<path d="M37 43 L41 43 M37 57 L41 57 M59 43 L63 43 M59 57 L63 57" stroke="{P["walnut"]["hex"]}" stroke-width="2"/>',
         f'<rect x="46.5" y="46.5" width="7" height="7" rx="1" fill="{P["lagoon"]["hex"]}" stroke="{P["walnut"]["hex"]}" stroke-width="1.6"/>',
         # grain lines on the planks
         f'<path d="M27 26 Q29 40 27 54 M32 30 Q34 48 32 74 M68 24 Q70 44 68 62 M73 34 Q75 52 73 76" fill="none" '
         f'stroke="{P["oak"]["hex"]}" stroke-width="1.3" stroke-linecap="round"/>',
         '</g>']
    return '\n'.join(g)


def lockup(dark=False):
    ink = '#FFFFFF' if dark else PALETTE['walnut']['hex']
    sub = PALETTE['lagoon_light']['hex'] if dark else PALETTE['lagoon_dark']['hex']
    d1, w1 = text_path('Hartwood', os.path.join(HERE, 'fonts/Fraunces-700.ttf'), 64, 122, 66)
    d2, w2 = text_path('DESIGNS', os.path.join(HERE, 'fonts/Inter-600.ttf'), 15.5, 125, 94, tracking=0.32)
    W = int(122 + max(w1, w2) + 8)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 110" width="{W * 2}" height="220" role="img" '
            f'aria-label="Hartwood Designs">\n{mark(4, 5, 100)}\n<path d="{d1}" fill="{ink}"/>\n'
            f'<path d="{d2}" fill="{sub}"/>\n</svg>\n'), W


def main():
    svg, W = lockup()
    open(os.path.join(HERE, 'logo.svg'), 'w').write(svg)
    open(os.path.join(HERE, 'logo_on_dark.svg'), 'w').write(lockup(dark=True)[0])
    m = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="512" height="512" role="img" aria-label="Hartwood mark">\n{mark()}\n</svg>\n'
    open(os.path.join(HERE, 'logo_mark.svg'), 'w').write(m)
    os.makedirs(os.path.join(ROOT, 'website'), exist_ok=True)
    open(os.path.join(ROOT, 'website', 'favicon.svg'), 'w').write(m)
    json.dump({'palette': PALETTE, 'fonts': FONTS}, open(os.path.join(HERE, 'brand.json'), 'w'), indent=1)
    # PNGs via the headless browser (shot.js)
    for name, w, h in (('logo', W * 4, 440), ('logo_mark', 512, 512), ('logo_on_dark', W * 4, 440)):
        subprocess.run(['node', os.path.join(ROOT, 'tools/svg2png.js'), os.path.join(HERE, f'{name}.svg'),
                        os.path.join(HERE, f'{name}.png'), str(w), str(h)], check=True, stdout=subprocess.DEVNULL)
    print('brand files written')


if __name__ == '__main__':
    main()
