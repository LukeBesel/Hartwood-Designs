"""Reusable shape and surface-detail generators for kit designs."""
from __future__ import annotations

import math

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, MultiLineString, Point, Polygon
from shapely.ops import unary_union

from .geom import circle, regular_star, gear_like  # noqa: F401


# ----------------------------------------------------------------------------- outlines
def ellipse(cx, cy, rx, ry, angle=0.0, n=48):
    pts = [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]
    p = Polygon(pts)
    return affinity.rotate(p, angle, origin=(cx, cy)) if angle else p


def petal(length, width, kind='round', base_w=None, n=40):
    """Single petal pointing along +x from the origin. kind: round, pointed, heart, long."""
    base_w = base_w if base_w is not None else width * 0.35
    pts = []
    for i in range(n + 1):
        t = i / n                      # 0 .. 1 along the petal
        if kind == 'pointed':
            w = width / 2 * math.sin(math.pi * t) ** 0.8 * (1 - 0.35 * t)
        elif kind == 'heart':
            w = width / 2 * math.sin(math.pi * t) ** 0.6
        elif kind == 'long':
            w = width / 2 * math.sin(math.pi * min(1, t * 1.05)) ** 0.5
        else:
            w = width / 2 * math.sin(math.pi * t) ** 0.55
        w = max(w, base_w / 2 * (1 - t))
        pts.append((t * length, w))
    top = pts
    bot = [(x, -y) for x, y in reversed(pts)]
    g = Polygon(top + bot).buffer(0)
    if kind == 'heart':
        notch = circle(length * 1.0, 0, width * 0.12)
        g = g.difference(notch)
    return g


def petal_ring(n, r_out, petal_w, r_hub, kind='round', rot=0.0, petal_len=None):
    """n petals radiating from a hub disc."""
    L = petal_len or r_out
    parts = [circle(0, 0, r_hub)]
    for i in range(n):
        p = petal(L, petal_w, kind)
        parts.append(affinity.rotate(p, rot + 360 * i / n, origin=(0, 0)))
    return unary_union(parts).buffer(0.2).buffer(-0.2)


def scalloped(r, n, depth, rot=0.0):
    """Disc with n round lobes (rose layer / cloud)."""
    lobes = [circle((r - depth) * math.cos(math.radians(rot + 360 * i / n)),
                    (r - depth) * math.sin(math.radians(rot + 360 * i / n)), depth * 1.35) for i in range(n)]
    return unary_union([circle(0, 0, r - depth)] + lobes).buffer(0.3).buffer(-0.3)


# ----------------------------------------------------------------------------- score patterns
def clip_lines(lines, region, inset=1.0):
    """Clip lines to the region shrunk by inset; drop tiny bits."""
    reg = region.buffer(-inset)
    out = []
    for l in lines:
        g = l.intersection(reg)
        for s in getattr(g, 'geoms', [g]):
            if isinstance(s, LineString) and s.length > 1.5:
                out.append(s)
    return out


def petal_veins(n, r_in, r_out, rot=0.0, side=True):
    lines = []
    for i in range(n):
        a = math.radians(rot + 360 * i / n)
        c, s = math.cos(a), math.sin(a)
        lines.append(LineString([(r_in * c, r_in * s), (r_out * c, r_out * s)]))
        if side:
            for f, da in ((0.55, 14), (0.55, -14)):
                rr = r_in + (r_out - r_in) * f
                b = a + math.radians(da)
                lines.append(LineString([(rr * 0.75 * c, rr * 0.75 * s),
                                         (rr * 1.15 * math.cos(b), rr * 1.15 * math.sin(b))]))
    return lines


def scale_pattern(region, size=6.0, rows_angle=0.0, inset=1.0):
    """Fish-scale arcs covering a region (dragon scales)."""
    minx, miny, maxx, maxy = region.bounds
    lines = []
    r = size / 2
    row = 0
    y = miny - size
    while y < maxy + size:
        off = (row % 2) * r
        x = minx - size + off
        while x < maxx + size:
            arc = [(x + r * math.cos(t), y + r * math.sin(t) * 0.9) for t in np.linspace(math.pi, 2 * math.pi, 9)]
            lines.append(LineString(arc))
            x += size
        y += r * 0.95
        row += 1
    if rows_angle:
        c = region.centroid
        lines = [affinity.rotate(l, rows_angle, origin=c) for l in lines]
    return clip_lines(lines, region, inset)


def brick_pattern(region, w=14.0, h=6.0, inset=1.0, angle=0.0):
    minx, miny, maxx, maxy = region.bounds
    lines = []
    y = miny
    row = 0
    while y < maxy + h:
        lines.append(LineString([(minx - w, y), (maxx + w, y)]))
        x = minx - (row % 2) * w / 2
        while x < maxx + w:
            lines.append(LineString([(x, y), (x, y + h)]))
            x += w
        y += h
        row += 1
    if angle:
        c = region.centroid
        lines = [affinity.rotate(l, angle, origin=c) for l in lines]
    return clip_lines(lines, region, inset)


def panel_lines(region, spacing=18.0, angle=0.0, inset=2.0, rivets=False):
    """Sci-fi hull panel seams: offset outline plus a few cross seams."""
    lines = []
    inner = region.buffer(-inset - 1.5, join_style='mitre')
    for p in getattr(inner, 'geoms', [inner]):
        if p.area > 40:
            lines.append(LineString(p.exterior.coords))
    minx, miny, maxx, maxy = region.bounds
    x = minx + spacing
    while x < maxx - spacing / 2:
        lines.append(LineString([(x, miny - 5), (x, maxy + 5)]))
        x += spacing
    if angle:
        c = region.centroid
        lines = [affinity.rotate(l, angle, origin=c) for l in lines]
    return clip_lines(lines, region, inset)


def leaf(length, width, curve=0.0, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        w = width / 2 * math.sin(math.pi * t) ** 0.7 * (1 - 0.15 * t)
        y0 = curve * math.sin(math.pi * t)
        pts.append((t * length, y0 + w))
    bot = []
    for i in range(n, -1, -1):
        t = i / n
        w = width / 2 * math.sin(math.pi * t) ** 0.7 * (1 - 0.15 * t)
        y0 = curve * math.sin(math.pi * t)
        bot.append((t * length, y0 - w))
    return Polygon(pts + bot).buffer(0)


def leaf_veins(length, width, curve=0.0, n_side=4):
    mid = [(t * length, curve * math.sin(math.pi * t)) for t in np.linspace(0.05, 0.92, 12)]
    lines = [LineString(mid)]
    for k in range(1, n_side + 1):
        t = k / (n_side + 1)
        x0, y0 = t * length, curve * math.sin(math.pi * t)
        w = width / 2 * math.sin(math.pi * t) ** 0.7 * 0.75
        for sgn in (1, -1):
            lines.append(LineString([(x0, y0), (x0 + length * 0.09, y0 + sgn * w)]))
    return lines


# ----------------------------------------------------------------------------- slicing implicit shapes
def slice_sdf(sdf, z, bounds, res=0.6, level=0.0):
    """Region where sdf(x, y, z) < level on the plane z, as shapely (Multi)Polygon."""
    import contourpy
    minx, miny, maxx, maxy = bounds
    xs = np.arange(minx, maxx + res, res)
    ys = np.arange(miny, maxy + res, res)
    X, Y = np.meshgrid(xs, ys)
    V = sdf(X, Y, np.full_like(X, z))
    if V.min() >= level:
        return Polygon()
    gen = contourpy.contour_generator(xs, ys, V, fill_type=contourpy.FillType.OuterOffset)
    polys = []
    filled, offsets = gen.filled(-1e9, level)
    for pts, offs in zip(filled, offsets):
        rings = [pts[offs[i]:offs[i + 1]] for i in range(len(offs) - 1)]
        if not rings or len(rings[0]) < 4:
            continue
        p = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0)
        if p.area > 1:
            polys.append(p)
    return unary_union(polys) if polys else Polygon()


def smooth(g, r=0.8):
    return g.buffer(r, join_style='round').buffer(-2 * r, join_style='round').buffer(r, join_style='round')


def simplify(g, tol=0.12):
    return g.simplify(tol, preserve_topology=True)
