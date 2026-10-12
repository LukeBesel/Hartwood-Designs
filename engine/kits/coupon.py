"""Fit-test coupon: one 12 x 12 in natural sheet that calibrates every fit number in config.py.

Cut it on every new wood batch. It contains:
  1. Slot comb   : slots 2.70 .. 3.30 mm wide. Push a scrap strip of this sheet into each slot.
  2. Square holes: tab holes 2.8 .. 3.2 mm x 10 mm, and a 10 mm wide test tab cut from the sheet.
  3. Dowel holes : 4.4 .. 5.2 mm for the 3/16 in dowel (grip vs spin).
  4. Kerf square : a 30.00 mm square part with a 20.00 mm square hole. Measure both with calipers.
  5. Half-lap   : two 40 mm cross half-lap pieces.
  6. Bridges    : four tags held by 0.3 / 0.4 / 0.5 / 0.6 mm bridges. Pick the thinnest that still holds the
                  tag through shipping (shake test) and pops out with a thumb. Set C.BRIDGE to it.
  7. Speed ladder: 5 small squares on their own colors for 20 / 25 / 30 / 35 / 40 mm/s cuts.
  8. Engrave/score swatch.
Kerf compensation (config.KERF) is applied to everything except the speed ladder labels.
"""
import os
import sys

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, box
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hartwood import config as C  # noqa: E402
from hartwood.cutfiles import SheetPaths, bridge_positions, cut_time, split_ring, write_dxf, write_lbrn, write_svg  # noqa: E402
from hartwood.geom import circle, rect  # noqa: E402
from hartwood.text import text_outline  # noqa: E402

K = C.KERF / 2
GAP = C.BRIDGE + C.KERF


def outer(sp, g, bridges=2, bridge_len=None):
    g = g.buffer(K, join_style='mitre')
    for r in g.interiors:
        sp.cuts.append((np.array(r.coords), True, True))
    ext = LineString(g.exterior.coords)
    pos = bridge_positions(ext, None, bridges)
    if bridge_len is not None:
        import hartwood.cutfiles as cf
        old = cf.GAP_PATH
        cf.GAP_PATH = bridge_len + C.KERF
        segs = cf.split_ring(ext, pos)
        cf.GAP_PATH = old
    else:
        segs = split_ring(ext, pos)
    for s in segs:
        sp.cuts.append((s, False, False))


def label(sp, s, x, y, h=2.6, anchor='left'):
    g, _ = text_outline(s, h, x=x, y=y, anchor=anchor)
    sp.fills.extend(list(getattr(g, 'geoms', [g])))


def build(out_dir):
    sp = SheetPaths('COUPON', 'natural')
    M = C.SHEET_MARGIN
    label(sp, 'HARTWOOD FIT-TEST COUPON  3 MM BASSWOOD', M + 2, 300 - M - 6, 3.2)
    label(sp, f'KERF SET {C.KERF:.2f}  CUT {C.CUT_SPEED:.0f} MM/S {C.CUT_POWER}%', M + 2, 300 - M - 12, 2.4)
    # 1 slot comb: a bar 200 x 22 with slots from the bottom edge
    widths = [2.70, 2.80, 2.90, 3.00, 3.10, 3.20, 3.30]
    bx0, by0 = M + 4, 220.0
    bar = rect(bx0, by0, bx0 + 7 * 26 + 6, by0 + 26)
    slots = []
    for i, w in enumerate(widths):
        cx = bx0 + 16 + i * 26
        slots.append(rect(cx - w / 2, by0 - 1, cx + w / 2, by0 + 12))
        label(sp, f'{w:.2f}', cx, by0 + 16, 2.4, anchor='center')
    outer(sp, bar.difference(unary_union(slots)), 3)
    label(sp, '1 SLOT COMB: PUSH A 3 MM STRIP IN. PICK SNUG = PRESS FIT', bx0, by0 + 29, 2.2)
    # 2 square holes plate + test tab
    px0, py0 = M + 4, 160.0
    plate = rect(px0, py0, px0 + 150, py0 + 40)
    holes = []
    for i, w in enumerate([2.80, 2.90, 3.00, 3.10, 3.20]):
        cx = px0 + 18 + i * 28
        holes.append(rect(cx - 5, py0 + 14 - w / 2, cx + 5, py0 + 14 + w / 2))
        label(sp, f'{w:.2f}', cx, py0 + 24, 2.4, anchor='center')
    outer(sp, plate.difference(unary_union(holes)), 3)
    tab = rect(px0 + 160, py0, px0 + 200, py0 + 10)
    outer(sp, tab, 2)
    label(sp, 'TAB 10', px0 + 162, py0 + 13, 2.2)
    label(sp, '2 SQUARE HOLES: PUSH TAB IN EACH. NOTE THE FIRST THAT HOLDS BY ITSELF', px0, py0 + 43, 2.2)
    # 3 dowel holes
    dx0, dy0 = M + 4, 112.0
    dplate = rect(dx0, dy0, dx0 + 190, dy0 + 30)
    dh = []
    ds = [4.40, 4.50, 4.60, 4.70, 4.80, 4.90, 5.00, 5.10, 5.20]
    for i, d in enumerate(ds):
        cx = dx0 + 12 + i * 21
        dh.append(circle(cx, dy0 + 11, d / 2, 48))
        label(sp, f'{d:.1f}', cx, dy0 + 19, 2.2, anchor='center')
    outer(sp, dplate.difference(unary_union(dh)), 3)
    label(sp, '3 DOWEL HOLES (3/16 IN DOWEL): TIGHT = GRIP, FREE TURN = SPIN', dx0, dy0 + 33, 2.2)
    # 4 kerf square
    kx0, ky0 = M + 4, 52.0
    sq = rect(kx0, ky0, kx0 + 30, ky0 + 30).difference(rect(kx0 + 5, ky0 + 5, kx0 + 25, ky0 + 25))
    outer(sp, sq, 2)
    inner = rect(kx0 + 40, ky0, kx0 + 60, ky0 + 20)
    outer(sp, inner, 2)
    label(sp, '4 KERF: MEASURE 30.00 SQUARE, 20.00 HOLE, 20.00 PART', kx0, ky0 + 33, 2.2)
    # 5 half-lap pair
    hx0, hy0 = kx0 + 75, ky0
    for j in range(2):
        x = hx0 + j * 50
        piece = rect(x, hy0, x + 40, hy0 + 20).difference(rect(x + 20 - 1.5, hy0 + 10 if j == 0 else hy0 - 1, x + 20 + 1.5, hy0 + 21 if j == 0 else hy0 + 10))
        outer(sp, piece, 2)
    label(sp, '5 HALF-LAP (3.00 SLOT)', hx0, hy0 + 23, 2.2)
    # 6 bridge tags
    tx0, ty0 = hx0 + 105, ky0
    for j, bl in enumerate([0.3, 0.4, 0.5, 0.6]):
        g = rect(tx0 + j * 17, ty0, tx0 + j * 17 + 13, ty0 + 24)
        outer(sp, g, 2, bridge_len=bl)
        label(sp, f'{bl:.1f}', tx0 + j * 17 + 6.5, ty0 + 27, 2.2, anchor='center')
    label(sp, '6 BRIDGES', tx0, ty0 + 33, 2.2)
    # 7 speed ladder (own layers: colors 03..07 in LightBurn)
    ladder = []
    for j, v in enumerate([20, 25, 30, 35, 40]):
        x = M + 4 + j * 24
        ladder.append((np.array(rect(x, M + 4, x + 14, M + 18).buffer(K, join_style='mitre').exterior.coords), v))
        label(sp, f'{v}', x + 7, M + 21, 2.2, anchor='center')
    label(sp, '7 SPEED LADDER MM/S: LOWEST SPEED THAT DROPS OUT CLEAN + 15%', M + 4, M + 27, 2.2)
    # 8 engrave + score swatch
    ex0 = M + 140
    sw = rect(ex0, M + 4, ex0 + 60, M + 24)
    outer(sp, sw, 2)
    for i in range(6):
        sp.scores.append(np.array([(ex0 + 4, M + 7 + i * 3), (ex0 + 30, M + 7 + i * 3)]))
    g, _ = text_outline('ABC 123', 4, x=ex0 + 33, y=M + 10)
    sp.fills.extend(list(getattr(g, 'geoms', [g])))
    label(sp, '8 SCORE + FILL', ex0, M + 27, 2.2)
    sp.stats = cut_time(sp)
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, 'fit_test_coupon')
    write_svg(sp, base + '.svg', title='Hartwood fit-test coupon')
    # add ladder squares to svg as separate colors
    s = open(base + '.svg').read()
    cols = ['#00a0a0', '#a000a0', '#a0a000', '#00a000', '#808080']
    extra = ''.join(f'<g id="LADDER_{v}" fill="none" stroke="{c}" stroke-width="0.1"><path d="M' +
                    ' L'.join(f'{x:.3f},{300 - y:.3f}' for x, y in sq_) + ' Z"/></g>' for (sq_, v), c in zip(ladder, cols))
    open(base + '.svg', 'w').write(s.replace('</svg>', extra + '</svg>'))
    write_dxf(sp, base + '.dxf')
    write_lbrn([sp], base + '.lbrn2')
    return sp


if __name__ == '__main__':
    out = os.path.join(os.path.dirname(__file__), '..', '..', 'kits', 'coupon')
    sp = build(out)
    print('coupon cut time', sp.stats)
