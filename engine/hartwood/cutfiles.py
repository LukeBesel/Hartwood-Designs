"""Cut files: SVG (mm), DXF R12 and LightBurn .lbrn2 per sheet, plus two-sheet bed jobs.

Layers
- CUT     red    #FF0000, 0.1 mm stroke : through cuts, kerf compensated, with micro-bridges (C.BRIDGE, rules in popout.py)
- SCORE   black  #000000, 0.1 mm stroke : low-power line engraving (surface detail)
- ENGRAVE blue   #0000FF, filled        : fill engraving (part codes, labels; text is outlines)

Sheet coordinates are mm, origin bottom-left, y up. SVG is written y-down (y_svg = H - y).
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass, field

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, MultiLineString, Point, Polygon
from shapely.ops import unary_union

from . import config as C
from . import popout as PO

GAP_PATH = C.BRIDGE + C.KERF   # length of the break in the cut path that leaves BRIDGE of wood


@dataclass
class SheetPaths:
    letter: str
    color: str
    cuts: list = field(default_factory=list)      # list of (coords Nx2, closed: bool, inner: bool)
    scores: list = field(default_factory=list)    # list of coords
    fills: list = field(default_factory=list)     # list of Polygon
    stats: dict = field(default_factory=dict)
    bridges: list = field(default_factory=list)   # one dict per bridge: pid, at (x, y), tier, width, mating
    targets: list = field(default_factory=list)   # print mode: registration target centres (never cut)


# ----------------------------------------------------------------------------- bridges
def bridge_positions(ring: LineString, no_go, n):
    """Pick n arc-length positions on a closed ring, on straight runs, away from corners and mating faces."""
    L = ring.length
    if n <= 0 or L < 8:
        return []
    cand = np.arange(0, L, 0.5)
    pts = [ring.interpolate(s) for s in cand]
    ok = np.ones(len(cand), bool)
    # avoid mating faces
    if no_go is not None and not no_go.is_empty:
        for i, p in enumerate(pts):
            if no_go.contains(p) or no_go.distance(p) < 0.8:
                ok[i] = False
    # avoid corners: direction change within +-1.5 mm
    for i, s in enumerate(cand):
        if not ok[i]:
            continue
        a = ring.interpolate((s - 1.5) % L); b = ring.interpolate(s); c = ring.interpolate((s + 1.5) % L)
        v1 = np.array([b.x - a.x, b.y - a.y]); v2 = np.array([c.x - b.x, c.y - b.y])
        n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if n1 < 1e-6 or n2 < 1e-6:
            ok[i] = False; continue
        cosang = np.dot(v1, v2) / (n1 * n2)
        if cosang < math.cos(math.radians(20)):
            ok[i] = False
    good = cand[ok]
    if not len(good):
        good = cand  # fall back: anywhere
    # spread evenly: target spacing L/n, choose the candidate nearest each target
    start = good[0]
    chosen = []
    for k in range(n):
        target = (start + k * L / n) % L
        d = np.minimum(np.abs(good - target), L - np.abs(good - target))
        chosen.append(float(good[np.argmin(d)]))
    return sorted(set(round(c, 2) for c in chosen))


def n_bridges(perimeter):
    if perimeter < 25:
        return 1
    if perimeter < 120:
        return 2
    if perimeter < 350:
        return 3
    return 4


def split_ring(ring: LineString, positions):
    """Cut a closed ring into open polylines with GAP_PATH breaks centred on positions."""
    L = ring.length
    if not positions:
        return [np.array(ring.coords)]
    gaps = sorted(((p - GAP_PATH / 2) % L, (p + GAP_PATH / 2) % L) for p in positions)
    segs = []
    for i in range(len(gaps)):
        s0 = gaps[i][1]
        s1 = gaps[(i + 1) % len(gaps)][0]
        if s1 <= s0:
            s1 += L
        coords = _substring(ring, s0, s1)
        segs.append(coords)
    return segs


def _substring(ring, s0, s1):
    L = ring.length
    cs = np.array(ring.coords)
    seglen = np.hypot(np.diff(cs[:, 0]), np.diff(cs[:, 1]))
    cum = np.concatenate([[0], np.cumsum(seglen)])
    out = [ring.interpolate(s0 % L).coords[0]]
    # walk vertices
    for lap in (0, 1):
        for i in range(1, len(cum)):
            s = cum[i] + lap * L
            if s0 < s < s1:
                out.append(tuple(cs[i]))
    out.append(ring.interpolate(s1 % L).coords[0])
    return np.array(out)


# ----------------------------------------------------------------------------- sheet geometry
def sheet_paths(sheet, fit=None) -> SheetPaths:
    fit = C.FIT if fit is None else fit
    sp = SheetPaths(sheet.letter, sheet.color)
    n_br = 0
    for pl in sheet.placed:
        part = pl.part
        g = part.outline(fit=fit)
        g = g.buffer(C.KERF / 2, join_style='mitre', mitre_limit=3.0)  # kerf compensation
        g = pl.xf(g)
        no_go = []
        for t in part.__dict__.get('tabs', []):
            no_go.append(pl.xf(t).buffer(0.3))
        for c, _cls in part.cuts:
            no_go.append(pl.xf(c).buffer(0.3))
        hard, soft = part.__dict__.get('mate_hard'), part.__dict__.get('mate_soft')
        mate_core, soft_s = None, None
        if hard is not None and not hard.is_empty:
            no_go.append(pl.xf(hard))
            mate_core = pl.xf(hard.buffer(-(PO.MATE_CLEAR - 0.5)))
        if soft is not None and not soft.is_empty:
            soft_s = pl.xf(soft)
        no_go_u = unary_union(no_go) if no_go else None
        for poly in getattr(g, 'geoms', [g]):
            for r in poly.interiors:     # holes first (inner shapes cut before the outline), no bridges: waste drops out
                sp.cuts.append((np.array(r.coords), True, True))
            ext = LineString(poly.exterior.coords)
            chosen = PO.choose_bridges(Polygon(poly.exterior), no_go_u, PO.n_bridges(Polygon(poly.exterior)), soft=soft_s)
            pos = [c for c, _ in chosen]
            n_br += len(pos)
            for (c, tier) in chosen:
                q = ext.interpolate(c)
                sp.bridges.append({'pid': id(pl), 'at': (round(q.x, 2), round(q.y, 2)), 'tier': tier,
                                   'width': PO.local_width(poly, q),
                                   'mating': bool(mate_core is not None and not mate_core.is_empty and mate_core.contains(q))})
            for seg in split_ring(ext, pos):
                sp.cuts.append((seg, False, False))
        for s in part.score:
            ls = pl.xf(s)
            for l in getattr(ls, 'geoms', [ls]):
                sp.scores.append(np.array(l.coords))
        for e in part.engrave:
            eg = pl.xf(e)
            sp.fills.extend(list(getattr(eg, 'geoms', [eg])))
        if pl.code_geom is not None:
            sp.fills.extend(list(getattr(pl.code_geom, 'geoms', [pl.code_geom])))
    if sheet.label_geom is not None:
        sp.fills.extend(list(getattr(sheet.label_geom, 'geoms', [sheet.label_geom])))
    sp.stats['bridges'] = n_br
    order_paths(sp)
    sp.stats.update(cut_time(sp))
    return sp


def order_paths(sp):
    """Nearest-neighbour order: within the cut layer inner shapes come before outer pieces."""
    def nn(items, key_start, key_end, start=(0.0, 0.0)):
        rest = list(items); out = []; cur = np.array(start)
        while rest:
            d = [np.hypot(*(key_start(it) - cur)) for it in rest]
            i = int(np.argmin(d)); it = rest.pop(i); out.append(it); cur = key_end(it)
        return out
    inner = [c for c in sp.cuts if c[2]]
    outer = [c for c in sp.cuts if not c[2]]
    st = lambda c: c[0][0]; en = lambda c: c[0][-1]
    sp.cuts = nn(inner, st, en) + nn(outer, st, en)
    sp.scores = nn(sp.scores, lambda c: c[0], lambda c: c[-1])


def _plen(c):
    return float(np.sum(np.hypot(np.diff(c[:, 0]), np.diff(c[:, 1]))))


def cut_time(sp):
    cut_len = sum(_plen(c[0]) for c in sp.cuts)
    score_len = sum(_plen(s) for s in sp.scores)
    n_cut = len(sp.cuts); n_score = len(sp.scores)
    # fill: each connected fill shape is scanned on its own (LightBurn "fill shapes individually")
    fill_s = 0.0
    groups = unary_union(sp.fills) if sp.fills else None
    fill_area = 0.0
    if groups is not None and not groups.is_empty:
        # merge glyphs of one word: cluster by buffering 1.2 mm
        clusters = unary_union([f.buffer(1.2) for f in sp.fills])
        for cl in getattr(clusters, 'geoms', [clusters]):
            members = [f for f in sp.fills if f.intersects(cl)]
            minx, miny, maxx, maxy = unary_union(members).bounds
            lines = (maxy - miny) / C.FILL_INTERVAL
            fill_s += lines * ((maxx - minx) + 2 * C.FILL_OVERSCAN) / C.FILL_SPEED
        fill_area = groups.area
    # travel: between path ends in order
    pts = [c[0] for c in sp.cuts] + sp.scores
    travel = 0.0
    cur = np.array([0.0, 0.0])
    for p in pts:
        travel += float(np.hypot(*(p[0] - cur))); cur = p[-1]
    t = {
        'cut_mm': round(cut_len, 1), 'score_mm': round(score_len, 1), 'fill_area_mm2': round(fill_area, 1),
        'pierces': n_cut + n_score,
        'cut_s': cut_len / C.CUT_SPEED + n_cut * C.PIERCE_TIME,
        'score_s': score_len / C.SCORE_SPEED + n_score * C.PIERCE_TIME,
        'fill_s': fill_s,
        'travel_s': travel / C.TRAVEL_SPEED,
    }
    t['total_s'] = t['cut_s'] + t['score_s'] + t['fill_s'] + t['travel_s']
    t['total_min'] = round(t['total_s'] / 60, 2)
    for k in ('cut_s', 'score_s', 'fill_s', 'travel_s', 'total_s'):
        t[k] = round(t[k], 1)
    return t


# ----------------------------------------------------------------------------- writers
def _svg_path(coords, closed, H):
    d = 'M' + ' L'.join(f'{x:.3f},{H - y:.3f}' for x, y in coords)
    return d + (' Z' if closed else '')


def _poly_d(poly, H):
    d = _svg_path(np.array(poly.exterior.coords), True, H)
    for r in poly.interiors:
        d += ' ' + _svg_path(np.array(r.coords), True, H)
    return d


def write_svg(sp, path, W=C.SHEET_W, H=C.SHEET_H, x_off=0.0, show_sheet=True, title=''):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
           f'<title>{title or "Hartwood sheet " + sp.letter}</title>']
    if show_sheet:
        out.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="none" stroke="#00a000" stroke-width="0.1" '
                   f'stroke-dasharray="2 2"><title>sheet edge (do not cut)</title></rect>')
    out.append('<g id="ENGRAVE" fill="#0000ff" stroke="none" fill-rule="evenodd">')
    for f in sp.fills:
        out.append(f'<path d="{_poly_d(f, H)}"/>')
    out.append('</g>')
    out.append('<g id="SCORE" fill="none" stroke="#000000" stroke-width="0.1">')
    for s in sp.scores:
        out.append(f'<path d="{_svg_path(s, False, H)}"/>')
    out.append('</g>')
    out.append('<g id="CUT" fill="none" stroke="#ff0000" stroke-width="0.1">')
    for c, closed, _inner in sp.cuts:
        out.append(f'<path d="{_svg_path(c, closed, H)}"/>')
    out.append('</g>')
    if sp.targets:
        r = C.PRINT['target_r']
        out.append('<g id="REGISTRATION" fill="none" stroke="#00a000" stroke-width="0.1"><title>Print and Cut targets: do not cut</title>')
        for x, y in sp.targets:
            out.append(f'<circle cx="{x}" cy="{H - y}" r="{r}"/><path d="M{x - r * 1.6} {H - y}H{x + r * 1.6}M{x} {H - y - r * 1.6}V{H - y + r * 1.6}"/>')
        out.append('</g>')
    out.append('</svg>')
    open(path, 'w').write('\n'.join(out))


def write_dxf(sp, path):
    """DXF R12: POLYLINE entities, colors CUT=1 (red), ENGRAVE=5 (blue), SCORE=7."""
    L = ['0', 'SECTION', '2', 'HEADER', '9', '$ACADVER', '1', 'AC1009', '9', '$INSUNITS', '70', '4', '0', 'ENDSEC',
         '0', 'SECTION', '2', 'TABLES', '0', 'TABLE', '2', 'LAYER', '70', '3']
    for name, col in (('CUT', 1), ('ENGRAVE', 5), ('SCORE', 7)):
        L += ['0', 'LAYER', '2', name, '70', '0', '62', str(col), '6', 'CONTINUOUS']
    L += ['0', 'ENDTAB', '0', 'ENDSEC', '0', 'SECTION', '2', 'ENTITIES']

    def pl(coords, closed, layer, col):
        nonlocal L
        L += ['0', 'POLYLINE', '8', layer, '62', str(col), '66', '1', '70', '1' if closed else '0']
        for x, y in coords:
            L += ['0', 'VERTEX', '8', layer, '10', f'{x:.4f}', '20', f'{y:.4f}', '30', '0.0']
        L += ['0', 'SEQEND', '8', layer]
    for c, closed, _ in sp.cuts:
        pl(c, closed, 'CUT', 1)
    for s in sp.scores:
        pl(s, False, 'SCORE', 7)
    for f in sp.fills:
        pl(np.array(f.exterior.coords), True, 'ENGRAVE', 5)
        for r in f.interiors:
            pl(np.array(r.coords), True, 'ENGRAVE', 5)
    L += ['0', 'ENDSEC', '0', 'EOF']
    open(path, 'w').write('\n'.join(L) + '\n')


def write_lbrn(sps, path, offsets=None):
    """LightBurn project (FormatVersion 0 style). Layer C00 = cut, C01 = fill, C02 = score.
    Unverified: open it in LightBurn once; if it fails, import the SVG instead (TODO_LUCAS)."""
    offsets = offsets or [(0.0, 0.0)] * len(sps)
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<LightBurnProject AppVersion="1.0.06" FormatVersion="0" MaterialHeight="3" MirrorX="False" MirrorY="False">',
         '    <Thumbnail Source=""/>']

    def cs(idx, name, typ, speed, power, extra=''):
        return (f'    <CutSetting type="{typ}">\n        <index Value="{idx}"/>\n        <name Value="{name}"/>\n'
                f'        <minPower Value="{power}"/>\n        <maxPower Value="{power}"/>\n'
                f'        <minPower2 Value="{power}"/>\n        <maxPower2 Value="{power}"/>\n'
                f'        <speed Value="{speed}"/>\n        <priority Value="{idx}"/>\n{extra}    </CutSetting>')
    L.append(cs(2, 'Score', 'Cut', C.SCORE_SPEED, C.SCORE_POWER))
    L.append(cs(1, 'Engrave fill', 'Scan', C.FILL_SPEED, C.FILL_POWER,
                f'        <interval Value="{C.FILL_INTERVAL}"/>\n        <overscanning Value="{C.FILL_OVERSCAN}"/>\n'))
    L.append(cs(0, 'Cut 3mm basswood', 'Cut', C.CUT_SPEED, C.CUT_POWER, '        <numPasses Value="1"/>\n'))
    if any(sp.targets for sp in sps):
        L.append(cs(3, 'Print and Cut targets (no output)', 'Cut', C.CUT_SPEED, 0, '        <doOutput Value="0"/>\n'))

    def shape(coords, closed, idx, ox, oy):
        s = [f'    <Shape Type="Path" CutIndex="{idx}">', '        <XForm>1 0 0 1 0 0</XForm>']
        pts = coords[:-1] if closed and np.allclose(coords[0], coords[-1]) else coords
        for x, y in pts:
            s.append(f'        <V vx="{x + ox:.3f}" vy="{y + oy:.3f}"/>')
        n = len(pts)
        for i in range(n - 1):
            s.append(f'        <P T="L" p0="{i}" p1="{i + 1}"/>')
        if closed:
            s.append(f'        <P T="L" p0="{n - 1}" p1="0"/>')
        s.append('    </Shape>')
        return '\n'.join(s)
    for sp, (ox, oy) in zip(sps, offsets):
        for f in sp.fills:
            L.append(shape(np.array(f.exterior.coords), True, 1, ox, oy))
            for r in f.interiors:
                L.append(shape(np.array(r.coords), True, 1, ox, oy))
        for s in sp.scores:
            L.append(shape(s, False, 2, ox, oy))
        for c, closed, _ in sp.cuts:
            L.append(shape(c, closed, 0, ox, oy))
        for x, y in sp.targets:
            r = C.PRINT['target_r']
            ring = np.array([(x + r * np.cos(a), y + r * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 33)])
            L.append(shape(ring, True, 3, ox, oy))
    L.append('</LightBurnProject>')
    open(path, 'w').write('\n'.join(L) + '\n')


TILE_OFFSETS = {'quarter': [(0, 0), (150, 0), (0, 150), (150, 150)], 'half': [(0, 0), (0, 150)]}


def tile_batch(sp, tile):
    """Compose copies of one tile into a full 12 x 12 sheet with bridged separation cuts.
    Returns a new SheetPaths (2 halves or 4 quarters = parts for 2 or 4 kits)."""
    offs = TILE_OFFSETS[tile]
    out = SheetPaths(sp.letter + '_x' + str(len(offs)), sp.color)
    for ox, oy in offs:
        sh = lambda c: np.asarray(c) + np.array([ox, oy])
        out.cuts.extend((sh(c), cl, inner) for c, cl, inner in sp.cuts)
        out.scores.extend(sh(s_) for s_ in sp.scores)
        out.fills.extend(affinity.translate(f, ox, oy) for f in sp.fills)
    lines = [LineString([(0, 150), (300, 150)])]
    if tile == 'quarter':
        lines.append(LineString([(150, 0), (150, 300)]))
    for ln in lines:
        L = ln.length
        pos = list(np.linspace(L / 12, L - L / 12, 6))
        breaks = sorted(pos)
        s0 = 0.0
        for b in breaks:
            seg = [ln.interpolate(s0).coords[0], ln.interpolate(b - 0.6).coords[0]]
            out.cuts.append((np.array(seg), False, False))
            s0 = b + 0.6
        out.cuts.append((np.array([ln.interpolate(s0).coords[0], ln.interpolate(L).coords[0]]), False, False))
    order_paths(out)
    out.stats = cut_time(out)
    return out


def write_bed_svg(sps, path, gap=5.0):
    """Two sheets side by side for one laser job on the 710 x 360 mm bed."""
    W = len(sps) * C.SHEET_W + (len(sps) - 1) * gap
    H = C.SHEET_H
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">']
    for i, sp in enumerate(sps):
        ox = i * (C.SHEET_W + gap)
        out.append(f'<g transform="translate({ox},0)">')
        out.append(f'<rect x="0" y="0" width="{C.SHEET_W}" height="{H}" fill="none" stroke="#00a000" stroke-width="0.1" stroke-dasharray="2 2"/>')
        out.append('<g fill="#0000ff" stroke="none" fill-rule="evenodd">' + ''.join(f'<path d="{_poly_d(f, H)}"/>' for f in sp.fills) + '</g>')
        out.append('<g fill="none" stroke="#000000" stroke-width="0.1">' + ''.join(f'<path d="{_svg_path(s, False, H)}"/>' for s in sp.scores) + '</g>')
        out.append('<g fill="none" stroke="#ff0000" stroke-width="0.1">' + ''.join(f'<path d="{_svg_path(c, cl, H)}"/>' for c, cl, _ in sp.cuts) + '</g>')
        out.append('</g>')
    out.append('</svg>')
    open(path, 'w').write('\n'.join(out))
