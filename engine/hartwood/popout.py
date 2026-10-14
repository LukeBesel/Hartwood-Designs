"""Pop-out: every part must press out of its sheet easily, cleanly, and without breaking.

How a part is held: the cut line around it stops for a short "bridge" (micro-joint), C.BRIDGE mm of wood.
The builder pushes the part out from the back; the bridges snap and leave a tiny nub on the edge.

Rules
1. Bridges never sit on a mating edge: an edge that touches another part in the finished model (tabs,
   half-lap slots, edges that butt against a wall). The nub would make that joint tight. Mating edges are
   found from the 3D model, not guessed.
2. Bridges sit where the part is at least STRONG_W wide, so the bridge breaks, not the part.
3. Bridges sit on straight runs (no corner within CORNER_CLEAR mm), where the nub is easy to sand.
4. Count by size: tiny parts 1, small 2, medium 3, large 4. Spread evenly around the outline.
5. Holes are cut before outlines and have no bridges, so hole waste drops out and the part does not shift.
6. No part sits inside another part's hole (the hole waste would fall out with it).
"""
from __future__ import annotations

import math

import numpy as np
import shapely
from shapely.geometry import LineString, MultiPoint, Point, Polygon
from shapely.ops import unary_union

from . import config as C
from .geom import T, apply

STRONG_W = 4.0        # part width at a bridge (mm)
WEAK_W = C.MIN_FEATURE  # below this a bridge counts as a failure, between WEAK_W and STRONG_W a warning
CORNER_CLEAR = 1.5    # straight edge needed on each side of a bridge (mm)
MATE_CLEAR = 1.0      # keep bridges this far from a mating edge (mm)
MATE_PROBE = 0.15     # probe distance outside the edge when looking for touching parts (mm)


# ----------------------------------------------------------------------------- mating edges from the model
def mating_edges(kit, step=0.5):
    """For every part, two local 2D regions where bridges should not go:
    mate_hard: the edge SLIDES past another part while it is put in (peg sides, tab sides, a plug in a box).
               A bridge stub there binds the joint. Never used for bridges.
    mate_soft: the edge only BUTTS against another part (a peg end on a wall, a rib edge on a wall).
               A stub there leaves a gap of about 0.2 mm at most. Used only when nothing better exists."""
    sol = kit.solids()
    for s in kit.parts:
        s.freeze()
    boxes = {id(s): s.aabb() for s in sol}
    for p in kit.parts:
        g = p.outline()
        probes, normals = [], []
        for poly in getattr(g, 'geoms', [g]):
            ext = LineString(poly.exterior.coords)
            ring = poly.buffer(MATE_PROBE, join_style='mitre', mitre_limit=2.0).exterior
            for s_ in np.arange(0, ring.length, step):
                q = ring.interpolate(s_)
                near = ext.interpolate(ext.project(q))
                n = np.array([q.x - near.x, q.y - near.y]); n /= max(np.linalg.norm(n), 1e-9)
                probes.append((q.x, q.y)); normals.append(n)
        if not probes:
            p.__dict__['mate_hard'] = p.__dict__['mate_soft'] = Polygon()
            continue
        P2, N2 = np.array(probes), np.array(normals)
        hit = np.zeros(len(P2), bool)
        lo, hi = boxes[id(p)]
        for z in (-T / 3, 0.0, T / 3):
            W = apply(p.mat, np.column_stack([P2, np.full(len(P2), z)]))
            for s in sol:
                if s is p:
                    continue
                blo, bhi = boxes[id(s)]
                if np.any(blo > hi + 1.0) or np.any(bhi < lo - 1.0):
                    continue
                todo = ~hit
                if todo.any():
                    hit[todo] |= s.contains(W[todo], grow=0.05)
        d = np.linalg.inv(p.mat[:3, :3]) @ (np.asarray(p.insert, float) / np.linalg.norm(p.insert))
        slide = np.abs(N2 @ d[:2]) < 0.5          # edge normal across the insertion direction: it slides
        hard, soft = hit & slide, hit & ~slide
        buf = MATE_CLEAR + MATE_PROBE
        p.__dict__['mate_hard'] = MultiPoint([tuple(x) for x in P2[hard]]).buffer(buf) if hard.any() else Polygon()
        p.__dict__['mate_soft'] = MultiPoint([tuple(x) for x in P2[soft]]).buffer(buf) if soft.any() else Polygon()
    for s in kit.parts:
        s.thaw()


# ----------------------------------------------------------------------------- bridge placement
def n_bridges(poly):
    per, area = poly.exterior.length, poly.area
    if area < 40:
        return 1
    if per < 120:
        return 2
    if per < 350:
        return 3
    return 4


def _straight(ring, s, L):
    a = ring.interpolate((s - CORNER_CLEAR) % L); b = ring.interpolate(s); c = ring.interpolate((s + CORNER_CLEAR) % L)
    v1 = np.array([b.x - a.x, b.y - a.y]); v2 = np.array([c.x - b.x, c.y - b.y])
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 < 1e-6 or n2 < 1e-6:
        return False
    return np.dot(v1, v2) / (n1 * n2) > math.cos(math.radians(20))


def local_width(poly, pt):
    """Largest disc (diameter, mm) that fits inside poly and touches pt, capped at 2 * STRONG_W."""
    for w in (2 * STRONG_W, STRONG_W, 3.5, WEAK_W, 2.5, 2.0):
        inner = poly.buffer(-w / 2)
        if not inner.is_empty and inner.distance(pt) <= w / 2 + 0.3:
            return w
    return 0.0


def choose_bridges(poly, nogo, n, soft=None, spacing=0.4):
    """Bridge positions (arc length along poly.exterior) and a quality tier per bridge:
    0 = every rule met, 1 = part only WEAK_W..STRONG_W wide there, 2 = on an edge that butts against another
    part, 3 = near a corner, 4 = narrow spot, 5 = on a sliding edge (only if nothing else exists; fails the check)."""
    ring = LineString(poly.exterior.coords)
    L = ring.length
    if n <= 0 or L < 6:
        return []
    cand = np.arange(0, L, spacing)
    pts = [ring.interpolate(s) for s in cand]
    hard_ok = np.array([nogo is None or nogo.is_empty or nogo.distance(q) > 0 for q in pts])
    soft_ok = np.array([soft is None or soft.is_empty or soft.distance(q) > 0 for q in pts])
    nogo_ok = hard_ok & soft_ok
    straight = np.array([_straight(ring, s, L) for s in cand])
    strong_in = poly.buffer(-STRONG_W / 2)
    weak_in = poly.buffer(-WEAK_W / 2)
    strong = np.array([not strong_in.is_empty and strong_in.distance(q) <= STRONG_W / 2 + 0.3 for q in pts])
    weak_ok = np.array([not weak_in.is_empty and weak_in.distance(q) <= WEAK_W / 2 + 0.3 for q in pts])
    tiers = [(0, nogo_ok & straight & strong), (1, nogo_ok & straight & weak_ok), (2, hard_ok & straight & weak_ok),
             (3, hard_ok & weak_ok), (4, hard_ok), (5, np.ones(len(cand), bool))]
    chosen = []
    for tier, mask in tiers:
        if tier == 5 and chosen:
            break                      # fewer bridges beat a bridge on a sliding edge
        good = cand[mask]
        while len(chosen) < n and len(good):
            if not chosen:
                # start on the longest straight stretch: the candidate with most good neighbours
                dens = np.array([np.sum(np.abs(good - g) < 3.0) for g in good])
                pick = good[int(np.argmax(dens))]
            else:
                ch = np.array([c for c, _ in chosen])
                d = np.min(np.minimum(np.abs(good[:, None] - ch[None, :]), L - np.abs(good[:, None] - ch[None, :])), axis=1)
                if d.max() < max(4.0, L / (n * 3)):
                    break
                pick = good[int(np.argmax(d))]
            chosen.append((float(pick), tier))
        if len(chosen) >= n:
            break
    return sorted(chosen)


# ----------------------------------------------------------------------------- the check
def check_popout(sheets, sps):
    """Result in the same shape as the other design checks."""
    fails, warns, rows = [], [], []
    for sh, sp in zip(sheets, sps):
        by_part = {}
        for b in sp.bridges:
            by_part.setdefault(b['pid'], []).append(b)
        geoms = [pl.xf(pl.part.outline()) for pl in sh.placed]
        filled = [unary_union([Polygon(q.exterior) for q in getattr(g, 'geoms', [g])]) for g in geoms]
        for i, pl in enumerate(sh.placed):
            name = pl.part.name
            bl = by_part.get(id(pl), [])
            if not bl:
                fails.append({'sheet': sh.letter, 'part': name, 'why': 'no bridge: the part falls out while cutting'})
            for b in bl:
                if b['mating'] or b['tier'] >= 5:
                    fails.append({'sheet': sh.letter, 'part': name, 'why': 'bridge on an edge that slides into another part',
                                  'at': b['at'], 'tier': b['tier']})
                elif b['width'] < WEAK_W:
                    fails.append({'sheet': sh.letter, 'part': name, 'why': f"bridge where the part is only {b['width']:.1f} mm wide", 'at': b['at']})
                elif b['tier'] >= 1:
                    why = {1: f"part only {b['width']:.1f} mm wide at the bridge", 2: 'bridge on an edge that butts against another part',
                           3: 'bridge near a corner', 4: 'bridge on a narrow spot', 5: 'bridge on the only spot left'}[b['tier']]
                    warns.append({'sheet': sh.letter, 'part': name, 'why': why, 'at': b['at']})
            for j in range(len(sh.placed)):
                if j != i and not geoms[j].is_empty and filled[i].contains(geoms[j].representative_point()) \
                        and not geoms[i].contains(geoms[j].representative_point()):
                    fails.append({'sheet': sh.letter, 'part': sh.placed[j].part.name, 'why': f'sits inside a hole of {name}'})
            if len(bl) == 1 and pl.part.outline().area > 400:
                warns.append({'sheet': sh.letter, 'part': name, 'why': 'only 1 bridge on a large part (its free edges are short)'})
            rows.append({'sheet': sh.letter, 'part': name, 'code': pl.code, 'bridges': len(bl),
                         'bridge_mm': round(len(bl) * C.BRIDGE, 2)})
        # cut order: every hole before any outline
        inner_idx = [k for k, c in enumerate(sp.cuts) if c[2]]
        outer_idx = [k for k, c in enumerate(sp.cuts) if not c[2]]
        if inner_idx and outer_idx and max(inner_idx) > min(outer_idx):
            fails.append({'sheet': sh.letter, 'part': '-', 'why': 'an outline is cut before a hole'})
    n_br = sum(r['bridges'] for r in rows)
    ok = not fails
    return {'name': 'Pop-out check', 'pass': ok, 'count': len(fails), 'details': fails, 'warnings': warns,
            'parts': rows,
            'summary': (f'{len(rows)} parts held by {n_br} bridges of {C.BRIDGE} mm, none on a mating edge or a weak spot, '
                        f'holes cut first, nothing nested in a hole' + (f' ({len(warns)} bridges with a note, see warnings)' if warns else ''))
            if ok else f'{len(fails)} pop-out problems'}


def bridge_map_png(sheet, sp, path, px_per_mm=3.0):
    """Picture of a sheet: parts, sliding edges (blue), butting edges (lilac), bridges (green good, orange note, red failure)."""
    from PIL import Image, ImageDraw
    S = px_per_mm
    W, H = int(sheet.W * S), int(sheet.H * S)
    im = Image.new('RGB', (W, H), (250, 246, 238))
    d = ImageDraw.Draw(im)
    tf = lambda x, y: (x * S, H - y * S)
    for pl in sheet.placed:
        g = pl.xf(pl.part.outline())
        for poly in getattr(g, 'geoms', [g]):
            d.polygon([tf(*c) for c in poly.exterior.coords], fill=(236, 214, 178), outline=(90, 60, 40))
            for r in poly.interiors:
                d.polygon([tf(*c) for c in r.coords], fill=(250, 246, 238), outline=(90, 60, 40))
        for key, col in (('mate_soft', (150, 120, 220)), ('mate_hard', (40, 110, 200))):
            ng = pl.part.__dict__.get(key)
            if ng is not None and not ng.is_empty:
                ex = pl.xf(pl.part.outline()).boundary.intersection(pl.xf(ng.buffer(-(MATE_CLEAR - 0.3))))
                for l in getattr(ex, 'geoms', [ex]):
                    if l.geom_type == 'LineString' and len(l.coords) > 1:
                        d.line([tf(*c) for c in l.coords], fill=col, width=4)
    for b in sp.bridges:
        x, y = tf(*b['at'])
        col = (220, 40, 40) if (b['mating'] or b['width'] < WEAK_W) else ((240, 140, 20) if b['tier'] else (20, 150, 70))
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=col, outline=(30, 20, 10))
    im.save(path)
