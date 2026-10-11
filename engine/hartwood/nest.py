"""Nesting: pack parts onto 12 x 12 in sheets, one color per sheet.

Method (as specified): rasterize each part at 1 mm, use FFT correlation against the sheet's occupancy
grid to find every free position, pick the bottom-left one, try several rotations, then verify the
final layout with exact geometry (no overlaps, gaps >= PART_GAP, inside the margin).

Sheet coordinates: mm, origin bottom-left, y up (as seen from above, laser side up).
"""
from __future__ import annotations

import math
import string
from dataclasses import dataclass, field

import numpy as np
import shapely
from PIL import Image, ImageDraw
from scipy.signal import fftconvolve
from shapely import affinity
from shapely.ops import unary_union

from . import config as C
from .text import text_outline

RES = 1.0  # mm per cell


@dataclass
class Placed:
    part: object          # Part
    angle: float          # degrees, rotation about local origin
    dx: float             # translation after rotation
    dy: float
    spare: bool = False
    code: str = ''
    code_on_part: bool = True
    code_geom: object = None   # text outline in sheet coords

    def xf(self, g):
        return affinity.translate(affinity.rotate(g, self.angle, origin=(0, 0)), self.dx, self.dy)


TILES = {   # name: (width, height, fraction of a 12 x 12 sheet)
    'full': (C.SHEET_W, C.SHEET_H, 1.0),
    'half': (C.SHEET_W, C.SHEET_H / 2, 0.5),
    'quarter': (C.SHEET_W / 2, C.SHEET_H / 2, 0.25),
}


@dataclass
class Sheet:
    color: str
    tile: str = 'full'
    letter: str = ''
    placed: list = field(default_factory=list)
    occ: np.ndarray = None
    label_geom: object = None

    @property
    def W(self):
        return TILES[self.tile][0]

    @property
    def H(self):
        return TILES[self.tile][1]

    @property
    def fraction(self):
        return TILES[self.tile][2]

    def __post_init__(self):
        n = int(round(self.H / RES))
        m = int(round(self.W / RES))
        self.occ = np.zeros((n, m), dtype=np.float32)
        # parts are dilated by PART_GAP when placed, so the margin band only needs the rest
        k = int(math.ceil((C.SHEET_MARGIN - C.PART_GAP) / RES))
        self.occ[:k, :] = 1; self.occ[-k:, :] = 1; self.occ[:, :k] = 1; self.occ[:, -k:] = 1
        # keep a strip at the top-left for the sheet label
        kk = int(math.ceil(C.SHEET_MARGIN / RES))
        self.occ[-kk - 6:, kk:kk + (70 if self.tile == 'full' else 34)] = 1


def rasterize(g, res=RES, dilate=0.0):
    """Conservative raster: a cell is set if the (dilated) polygon touches it."""
    g = g.buffer(dilate + res * 0.71, join_style='mitre')
    minx, miny, maxx, maxy = g.bounds
    x0, y0 = math.floor(minx / res) * res, math.floor(miny / res) * res
    w = int(math.ceil((maxx - x0) / res)) + 1
    h = int(math.ceil((maxy - y0) / res)) + 1
    xs = x0 + (np.arange(w) + 0.5) * res
    ys = y0 + (np.arange(h) + 0.5) * res
    gx, gy = np.meshgrid(xs, ys)
    m = shapely.contains_xy(g, gx.ravel(), gy.ravel()).reshape(h, w)
    return m.astype(np.float32), x0, y0


def candidate_angles(g, grain_lock=False):
    mrr = g.minimum_rotated_rectangle
    xs, ys = mrr.exterior.coords.xy
    e = [(xs[1] - xs[0], ys[1] - ys[0]), (xs[2] - xs[1], ys[2] - ys[1])]
    long_e = max(e, key=lambda v: math.hypot(*v))
    a = -math.degrees(math.atan2(long_e[1], long_e[0]))  # rotate long side onto +x
    if grain_lock:
        return sorted({round(a % 360, 3), round((a + 180) % 360, 3)})
    base = {0.0, 90.0, 180.0, 270.0}
    base |= {round((a + k) % 360, 3) for k in (0, 90, 180, 270)}
    return sorted(base)


def is_long_thin(g):
    mrr = g.minimum_rotated_rectangle
    xs, ys = mrr.exterior.coords.xy
    sides = sorted(math.dist((xs[i], ys[i]), (xs[i + 1], ys[i + 1])) for i in range(4))
    return sides[-1] / max(sides[0], 0.1) > 4.0


def _try_place(sheet, g, angles):
    best = None
    for ang in angles:
        gr = affinity.rotate(g, ang, origin=(0, 0))
        K, kx0, ky0 = rasterize(gr, dilate=C.PART_GAP)
        h, w = K.shape
        H, W = sheet.occ.shape
        if h > H or w > W:
            continue
        corr = fftconvolve(sheet.occ, K[::-1, ::-1], mode='valid')
        free = np.argwhere(corr < 0.5)
        if not len(free):
            continue
        # bottom-left: lowest row (y) first, then lowest column (x)
        order = np.lexsort((free[:, 1], free[:, 0]))
        r, c = free[order[0]]
        score = (r, c)
        if best is None or score < best[0]:
            # grid offset -> translation: cell (r, c) holds raster cell (0,0) which sits at (kx0, ky0)
            dx = c * RES - kx0
            dy = r * RES - ky0
            best = (score, ang, dx, dy, K, r, c)
    return best


def _mark(sheet, gr_placed):
    K, kx0, ky0 = rasterize(gr_placed, dilate=0.0)
    r0, c0 = int(round(ky0 / RES)), int(round(kx0 / RES))
    h, w = K.shape
    H, W = sheet.occ.shape
    rr0, cc0 = max(r0, 0), max(c0, 0)
    rr1, cc1 = min(r0 + h, H), min(c0 + w, W)
    sheet.occ[rr0:rr1, cc0:cc1] = np.maximum(sheet.occ[rr0:rr1, cc0:cc1], K[rr0 - r0:rr1 - r0, cc0 - c0:cc1 - c0])


def _place_into(sheet, p):
    g = p.outline()
    best = _try_place(sheet, g, candidate_angles(g, grain_lock=is_long_thin(g)))
    if not best:
        return False
    _, ang, dx, dy, *_ = best
    pl = Placed(p, ang, dx, dy)
    sheet.placed.append(pl)
    _mark(sheet, pl.xf(g))
    return True


def _nest_once(plist, tile):
    sheets = []
    for p in plist:
        if not any(_place_into(sh, p) for sh in sheets):
            sh = Sheet(plist[0].color, tile)
            if not _place_into(sh, p):
                return None
            sheets.append(sh)
    return sheets


def _bbox(p):
    b = p.outline().bounds
    return b[2] - b[0], b[3] - b[1]


ORDERS = [
    lambda p: -p.outline().area,
    lambda p: -max(_bbox(p)),
    lambda p: -_bbox(p)[1] * 1000 - _bbox(p)[0],
    lambda p: -p.outline().length,
]


def _nest_group(plist, tile):
    """Nest all parts of one color into as few sheets of this tile size as possible (tries several
    part orders, keeps the best). None if a part does not fit."""
    best = None
    for key in ORDERS:
        order = sorted(plist, key=lambda p: (key(p), p.name))
        res = _nest_once(order, tile)
        if res is None:
            continue
        top = max(max(pl.xf(pl.part.outline()).bounds[3] for pl in sh.placed) for sh in res)
        score = (len(res), top)
        if best is None or score < best[0]:
            best = (score, res)
        if len(res) == 1 and tile != 'full':
            break
    return None if best is None else best[1]


def nest(parts, max_sheets=60, allow_tiles=True):
    """Place every part (plus spares). One color per sheet. Small color groups go on half or quarter
    tiles (2 or 4 kits share one physical sheet; the packer snaps it apart). Returns list of Sheet."""
    sheets = []
    order = sorted(parts, key=lambda p: (-p.outline().area, p.name))
    by_color = {}
    for p in order:
        by_color.setdefault(p.color, []).append(p)
    for color, plist in by_color.items():
        area = sum(p.outline().area for p in plist)
        result = None
        if allow_tiles:
            for tile in ('quarter', 'half'):
                w, h, _ = TILES[tile]
                inner = (w - 2 * C.SHEET_MARGIN) * (h - 2 * C.SHEET_MARGIN - 6)
                if area < 0.80 * inner:
                    result = _nest_group(plist, tile)
                    if result and len(result) == 1:
                        break
                    result = None
        if result is None:
            result = _nest_group(plist, 'full')
            if result is None:
                raise ValueError(f'a {color} part does not fit on a sheet')
            # the last full sheet may shrink to a tile
            if allow_tiles and len(result) > 1:
                last = result[-1]
                lp = [pl.part for pl in last.placed]
                for tile in ('quarter', 'half'):
                    alt = _nest_group(lp, tile)
                    if alt and len(alt) == 1:
                        result[-1] = alt[0]
                        break
        sheets.extend(result)
        if len(sheets) > max_sheets:
            raise RuntimeError('too many sheets')
    # spares into leftover space only (never open a new sheet for spares)
    for p in order:
        for _ in range(getattr(p, 'spares', 0)):
            g = p.outline()
            angles = candidate_angles(g, grain_lock=is_long_thin(g))
            for sh in [s for s in sheets if s.color == p.color]:
                best = _try_place(sh, g, angles)
                if best:
                    _, ang, dx, dy, *_ = best
                    pl = Placed(p, ang, dx, dy, spare=True)
                    sh.placed.append(pl)
                    _mark(sh, pl.xf(g))
                    break
    return sheets


def verify(sheets):
    """Exact-geometry verification. Returns list of problems (empty = good)."""
    probs = []
    for sh in sheets:
        lo, hi = C.SHEET_MARGIN, sh.W - C.SHEET_MARGIN
        geoms = [pl.xf(pl.part.outline()) for pl in sh.placed]
        tree = shapely.STRtree(geoms)
        for i, g in enumerate(geoms):
            minx, miny, maxx, maxy = g.bounds
            if minx < lo - 1e-6 or miny < lo - 1e-6 or maxx > hi + 1e-6 or maxy > sh.H - C.SHEET_MARGIN + 1e-6:
                probs.append(f'{sh.letter}: {sh.placed[i].part.name} outside margin')
            for j in tree.query(g.buffer(C.PART_GAP - 0.05)):
                if j <= i:
                    continue
                d = g.distance(geoms[j])
                if d < C.PART_GAP - 0.05:
                    probs.append(f'{sh.letter}: {sh.placed[i].part.name} and {sh.placed[j].part.name} only {d:.2f} mm apart')
    return probs


def assign_codes(sheets, kit_name='', code_h=2.4):
    """Letter sheets by first assembly step, number parts in reading order, shared code for identical
    parts on the same sheet. Engrave the code on the part if it fits, else on the sheet beside it."""
    sheets.sort(key=lambda s: (min(pl.part.step for pl in s.placed), s.color != 'natural'))
    letters = string.ascii_uppercase
    for i, sh in enumerate(sheets):
        sh.letter = letters[i] if i < 26 else letters[i // 26 - 1] + letters[i % 26]
    for sh in sheets:
        # reading order: top row first (high y), then left to right
        def key(pl):
            b = pl.xf(pl.part.outline()).bounds
            return (-round(b[3] / 25), b[0])
        num = {}
        for pl in sorted(sh.placed, key=key):
            sk = pl.part.shape_key()
            if sk not in num:
                num[sk] = len(num) + 1
            pl.code = f'{sh.letter}{num[sk]}'
            if not pl.spare:
                pl.part.code = pl.code
                pl.part.sheet = sh.letter
        # code geometry
        occupied = unary_union([pl.xf(pl.part.outline()).buffer(0.8) for pl in sh.placed])
        for pl in sh.placed:
            pl._sheet_wh = (sh.W, sh.H)
            pl.code_geom, pl.code_on_part = _place_code(pl, code_h, occupied)
            if pl.code_geom is not None and not pl.code_on_part:
                occupied = occupied.union(pl.code_geom.envelope.buffer(0.6))
        # sheet label in the reserved top-left strip
        if sh.tile == 'full':
            lab = f'HARTWOOD  {kit_name.upper()}  SHEET {sh.letter}  {C.MATERIALS[sh.color]["label"].upper()}'
            g, w = text_outline(lab, 3.0, x=C.SHEET_MARGIN + 1, y=sh.H - C.SHEET_MARGIN - 5.0)
            if w > 160:
                g, w = text_outline(f'HARTWOOD {kit_name.upper()} {sh.letter}', 3.0, x=C.SHEET_MARGIN + 1,
                                    y=sh.H - C.SHEET_MARGIN - 5.0)
        else:
            g, w = text_outline(f'{kit_name.upper()[:10]} {sh.letter}', 2.6, x=C.SHEET_MARGIN + 1,
                                y=sh.H - C.SHEET_MARGIN - 4.2)
        sh.label_geom = g
    return sheets


def _fit_box(region, w, h, res=0.25):
    """Lower-left corner where a w x h axis-aligned box fits inside region, closest to its middle."""
    from scipy.ndimage import uniform_filter
    if region.is_empty:
        return None
    minx, miny, maxx, maxy = region.bounds
    nx, ny = int((maxx - minx) / res) + 1, int((maxy - miny) / res) + 1
    if nx < 2 or ny < 2:
        return None
    xs = minx + (np.arange(nx) + 0.5) * res
    ys = miny + (np.arange(ny) + 0.5) * res
    gx, gy = np.meshgrid(xs, ys)
    m = shapely.contains_xy(region, gx.ravel(), gy.ravel()).reshape(ny, nx).astype(np.float32)
    bw, bh = int(math.ceil(w / res)) + 1, int(math.ceil(h / res)) + 1
    if bw > nx or bh > ny:
        return None
    full = uniform_filter(m, size=(bh, bw), mode='constant', cval=0.0) > 0.999
    pts = np.argwhere(full)
    if not len(pts):
        return None
    c = region.representative_point()
    cy = ys[pts[:, 0]]; cx = xs[pts[:, 1]]
    k = np.argmin((cx - c.x) ** 2 + (cy - c.y) ** 2)
    return cx[k] - w / 2, cy[k] - h / 2


def _place_code(pl, h, occupied):
    part = pl.part
    txt = pl.code + ('s' if pl.spare else '')
    tg, w = text_outline(txt, h)
    pad = 0.4
    outline = pl.xf(part.outline())
    avoid = [pl.xf(e).buffer(0.4) for e in part.engrave] + [pl.xf(s.buffer(0.6)) for s in part.score]
    allowed = outline.buffer(-0.9, join_style='mitre')
    if avoid:
        allowed = allowed.difference(unary_union(avoid))
    beside = _place_beside(pl, tg, w, h, pad, outline, occupied) if not getattr(part, 'code_on_part', True) else None
    if beside is not None:
        return beside, False
    if not allowed.is_empty:
        # try horizontal text, then text along the part's long axis
        mrr = outline.minimum_rotated_rectangle
        xs, ys = mrr.exterior.coords.xy
        e = max([(xs[1] - xs[0], ys[1] - ys[0]), (xs[2] - xs[1], ys[2] - ys[1])], key=lambda v: math.hypot(*v))
        a = math.degrees(math.atan2(e[1], e[0]))
        a = (a + 90) % 180 - 90  # keep text upright-ish
        for ang in (0.0, a):
            c = allowed.centroid
            reg = affinity.rotate(allowed, -ang, origin=c)
            spot = _fit_box(reg, w + 2 * pad, h + 2 * pad)
            if spot:
                g = affinity.translate(tg, spot[0] + pad, spot[1] + pad)
                return affinity.rotate(g, ang, origin=c), True
    g = _place_beside(pl, tg, w, h, pad, outline, occupied)
    return (g, False) if g is not None else (None, False)


def _place_beside(pl, tg, w, h, pad, outline, occupied):
    """Code text on the sheet skeleton next to the part, or None."""
    minx, miny, maxx, maxy = outline.bounds
    tb = shapely.box(-pad, -pad, w + pad, h + pad)
    sw, shh = getattr(pl, '_sheet_wh', (C.SHEET_W, C.SHEET_H))
    lo = 2.0
    cands = [(maxx + 1.0, (miny + maxy) / 2 - h / 2), (minx - w - 1.0, (miny + maxy) / 2 - h / 2),
             ((minx + maxx) / 2 - w / 2, maxy + 1.0), ((minx + maxx) / 2 - w / 2, miny - h - 1.0)]
    for r in np.arange(1.0, 10, 0.75):
        for ang in range(0, 360, 20):
            cx = (minx + maxx) / 2 + ((maxx - minx) / 2 + r + w / 2) * math.cos(math.radians(ang))
            cy = (miny + maxy) / 2 + ((maxy - miny) / 2 + r + h / 2) * math.sin(math.radians(ang))
            cands.append((cx - w / 2, cy - h / 2))
    for xx, yy in cands:
        cand = affinity.translate(tb, xx, yy)
        b = cand.bounds
        if b[0] < lo or b[1] < lo or b[2] > sw - 2.0 or b[3] > shh - 2.0:
            continue
        if cand.intersects(occupied):
            continue
        return affinity.translate(tg, xx, yy)
    return None
