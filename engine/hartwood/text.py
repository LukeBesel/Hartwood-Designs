"""Text to outlines (shapely polygons) with fontTools. Used for engraved part codes and labels."""
from __future__ import annotations

import functools
import os

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
]


class _FlatPen(BasePen):
    def __init__(self, glyphset, steps=6):
        super().__init__(glyphset)
        self.contours, self.cur, self.steps = [], [], steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps; u = 1 - t
            self.cur.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                             u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps; u = 1 - t
            self.cur.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                             u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        if len(self.cur) >= 3:
            self.contours.append(self.cur)
        self.cur = []

    _endPath = _closePath


@functools.lru_cache(maxsize=4)
def _font(path=None):
    for p in ([path] if path else []) + FONT_CANDIDATES:
        if p and os.path.exists(p):
            return TTFont(p)
    raise FileNotFoundError('no font found')


@functools.lru_cache(maxsize=4096)
def _glyph(ch, font_path=None):
    f = _font(font_path)
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    name = cmap.get(ord(ch))
    if name is None:
        return None, f['hmtx'][cmap.get(ord('?'))][0]
    pen = _FlatPen(gs)
    gs[name].draw(pen)
    adv = f['hmtx'][name][0]
    polys = [Polygon(c).buffer(0) for c in pen.contours if len(c) >= 3]
    polys = [p for p in polys if not p.is_empty]
    # even-odd fill: XOR all contours
    g = None
    for p in sorted(polys, key=lambda p: -p.area):
        g = p if g is None else g.symmetric_difference(p)
    return g, adv


def text_outline(s, height, x=0.0, y=0.0, anchor='left', font_path=None, tracking=0.04):
    """Return a (Multi)Polygon of text s with cap height ~= height mm, baseline at y."""
    f = _font(font_path)
    upm = f['head'].unitsPerEm
    cap = getattr(f['OS/2'], 'sCapHeight', 0) or upm * 0.72
    scale = height / cap
    pen_x = 0.0
    parts = []
    for ch in s:
        g, adv = _glyph(ch, font_path)
        if g is not None and not g.is_empty:
            parts.append(affinity.translate(g, pen_x, 0))
        pen_x += adv + tracking * upm
    width = (pen_x - tracking * upm) * scale
    if not parts:
        return Polygon(), width
    geom = unary_union(parts)
    geom = affinity.scale(geom, scale, scale, origin=(0, 0))
    dx = {'left': 0, 'center': -width / 2, 'right': -width}[anchor]
    return affinity.translate(geom, x + dx, y), width


def text_box(s, height, font_path=None):
    """Width and height of the text block in mm."""
    g, w = text_outline(s, height, font_path=font_path)
    return w, height
