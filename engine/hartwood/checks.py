"""Automated design checks. All must pass before a kit design is called done.

1. collisions      : sample points inside every solid (shrunk 0.15 mm) and test them against every
                     other solid. Touching faces do not count. Result must be zero overlaps.
2. floating        : every solid touches at least one other solid, and the model is one piece.
3. assembly paths  : each new solid is swept from its exploded position to its final position along
                     its insertion direction; it must never pass through a solid that is already placed.
4. features        : every part is one piece, minimum feature (no wall, bridge or tab thinner than
                     MIN_FEATURE) and a fragile-part report (long thin parts, tiny parts).
"""
from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
from shapely.geometry import Polygon

from . import config as C
from .geom import Part

SHRINK = 0.15
TOUCH = 0.30   # a solid "touches" another if grown by this it captures the other's interior samples


def _prep(kit):
    for p in kit.parts:
        p.freeze()
    sol = kit.solids()
    boxes = [s.aabb() for s in sol]
    return sol, boxes


def _overlap(b1, b2, pad=0.0):
    return np.all(b1[0] - pad <= b2[1]) and np.all(b2[0] - pad <= b1[1])


def _samples(s, spacing):
    key = ('_samples', spacing)
    cache = s.__dict__.setdefault('_sample_cache', {})
    if spacing not in cache:
        cache[spacing] = s.sample(spacing=spacing, shrink=SHRINK)
    return cache[spacing]


# ----------------------------------------------------------------------------- 1 collisions
def check_collisions(kit, spacing=1.0):
    sol, boxes = _prep(kit)
    hits = []
    for i, a in enumerate(sol):
        pa = _samples(a, spacing)
        for j, b in enumerate(sol):
            if j <= i or not _overlap(boxes[i], boxes[j]):
                continue
            pb = _samples(b, spacing)
            n1 = int(b.contains(pa).sum()) if len(pa) else 0
            n2 = int(a.contains(pb).sum()) if len(pb) else 0
            if n1 or n2:
                bad = pa[b.contains(pa)] if n1 else pb[a.contains(pb)]
                hits.append({'a': a.name, 'b': b.name, 'points': n1 + n2, 'where': bad.mean(0).round(1).tolist()})
    return {'name': 'Collision check', 'pass': not hits, 'count': len(hits), 'details': hits,
            'summary': f'{len(hits)} overlapping pairs' if hits else 'zero overlaps'}


# ----------------------------------------------------------------------------- 2 floating
def contact_graph(kit, spacing=1.0):
    sol, boxes = _prep(kit)
    adj = defaultdict(set)
    for i, a in enumerate(sol):
        for j, b in enumerate(sol):
            if j <= i or not _overlap(boxes[i], boxes[j], pad=TOUCH + 0.1):
                continue
            pb = _samples(b, spacing)
            touch = len(pb) and a.contains(pb, grow=TOUCH).any()
            if not touch:
                pa = _samples(a, spacing)
                touch = len(pa) and b.contains(pa, grow=TOUCH).any()
            if touch:
                adj[a.name].add(b.name)
                adj[b.name].add(a.name)
    return sol, adj


def check_floating(kit, spacing=1.0):
    sol, adj = contact_graph(kit, spacing)
    names = [s.name for s in sol]
    floating = [n for n in names if not adj[n]]
    # connected components
    seen, comps = set(), []
    for n in names:
        if n in seen:
            continue
        stack, comp = [n], []
        seen.add(n)
        while stack:
            x = stack.pop(); comp.append(x)
            for y in adj[x]:
                if y not in seen:
                    seen.add(y); stack.append(y)
        comps.append(comp)
    ok = not floating and len(comps) == 1
    return {'name': 'Nothing-floats check', 'pass': ok, 'count': len(floating), 'details': {
        'floating': floating, 'components': len(comps),
        'component_sizes': sorted((len(c) for c in comps), reverse=True),
        'small_components': [c for c in comps if len(c) < max(len(x) for x in comps)]},
        'summary': ('every part touches another; model is one piece' if ok else
                    f'{len(floating)} floating, {len(comps)} separate pieces')}


# ----------------------------------------------------------------------------- 3 assembly paths
def _sweep_hits(pts, d, D, obstacle, step_mm):
    offs = np.arange(0.0, D + 1e-9, step_mm)
    for k0 in range(0, len(offs), 40):
        ch = offs[k0:k0 + 40]
        P = (pts[None, :, :] - ch[:, None, None] * d[None, None, :]).reshape(-1, 3)
        hit = obstacle.contains(P)
        if hit.any():
            hk = hit.reshape(len(ch), -1).any(1)
            return float(ch[np.argmax(hk)])
    return None


def check_assembly_paths(kit, spacing=1.5, step_mm=0.75):
    """Each solid slides from its exploded position to its final position along its insertion
    direction without passing through anything already placed. Sub-assemblies are first checked on
    their own, then swept as one rigid unit at their mount step."""
    sol, boxes = _prep(kit)
    idx = {s.name: i for i, s in enumerate(sol)}
    member_of = {}
    for sa in kit.subassemblies:          # inner sub-assemblies are listed after the outer ones
        for n in sa['members']:
            member_of[n] = sa['name']
    # events: (step, order, kind, payload)
    events = []
    for i, s in enumerate(sol):
        events.append((s.step, 0, i, 'part', i))
    for j, sa in enumerate(kit.subassemblies):
        events.append((sa['step'], 1, j, 'mount', sa))
    events.sort(key=lambda e: (e[0], e[1], e[2]))
    placed_world = []                 # parts in the main assembly
    placed_sub = {sa['name']: [] for sa in kit.subassemblies}
    problems = []

    def blocked_by(i, d, D, others):
        s = sol[i]
        pts = _samples(s, spacing)
        if not len(pts):
            return None
        lo, hi = boxes[i]
        sw_lo, sw_hi = np.minimum(lo, lo - d * D), np.maximum(hi, hi - d * D)
        for j in others:
            if not _overlap((sw_lo, sw_hi), boxes[j]):
                continue
            mm = _sweep_hits(pts, d, D, sol[j], step_mm)
            if mm is not None:
                return sol[j].name, mm
        return None

    for _step, _o, _k, kind, payload in events:
        if kind == 'part':
            i = payload
            s = sol[i]
            d = np.asarray(s.insert, float); d = d / np.linalg.norm(d)
            D = float(getattr(s, 'explode', 40.0))
            grp = member_of.get(s.name)
            others = placed_sub[grp] if grp else placed_world
            hit = blocked_by(i, d, D, others)
            if hit:
                problems.append({'part': s.name, 'step': s.step, 'blocked_by': hit[0], 'mm_from_final': round(hit[1], 2)})
            (placed_sub[grp] if grp else placed_world).append(i)
        else:
            sa = payload
            d = np.asarray(sa['insert'], float); d = d / np.linalg.norm(d)
            D = float(sa.get('explode', 60.0))
            members = placed_sub[sa['name']]
            target = placed_sub[sa['into']] if sa.get('into') else placed_world
            for i in members:
                hit = blocked_by(i, d, D, target)
                if hit:
                    problems.append({'part': f"{sa['name']} (mount) / {sol[i].name}", 'step': sa['step'],
                                     'blocked_by': hit[0], 'mm_from_final': round(hit[1], 2)})
                    break
            target.extend(members)
    return {'name': 'Assembly path check', 'pass': not problems, 'count': len(problems), 'details': problems,
            'summary': 'every part slides into place without hitting a placed part' if not problems else
            f'{len(problems)} blocked insertions'}


# ----------------------------------------------------------------------------- 4 features
def thin_regions(g, min_w=C.MIN_FEATURE):
    r = min_w / 2
    opened = g.buffer(-r, join_style='mitre', mitre_limit=10).buffer(r, join_style='mitre', mitre_limit=10)
    thin = g.difference(opened.buffer(0.05, join_style='mitre'))
    out = []
    for p in getattr(thin, 'geoms', [thin]):
        if p.is_empty or p.area < 0.6:
            continue
        # estimate width: 2 * area / length of the region's long side
        mrr = p.minimum_rotated_rectangle
        xs, ys = mrr.exterior.coords.xy
        sides = sorted([math.dist((xs[k], ys[k]), (xs[k + 1], ys[k + 1])) for k in range(4)])
        w = sides[0]
        if w < min_w - 0.15 and sides[-1] > 1.2:
            out.append({'width': round(w, 2), 'length': round(sides[-1], 1), 'at': [round(p.centroid.x, 1), round(p.centroid.y, 1)]})
    return out


def check_features(kit):
    issues, fragile = [], []
    for p in kit.parts:
        g = p.outline()
        if g.is_empty or g.area < 1.0:
            issues.append({'part': p.name, 'width': 0.0, 'length': 0.0, 'at': [0, 0], 'why': 'empty outline'})
            continue
        pieces = [q for q in getattr(g, 'geoms', [g]) if q.area >= 1.0]
        if len(pieces) > 1:
            c = [round(v, 1) for v in min(pieces, key=lambda q: q.area).centroid.coords[0]]
            issues.append({'part': p.name, 'width': 0.0, 'length': 0.0, 'at': c,
                           'why': f'{len(pieces)} separate pieces: a part must be one piece (smallest piece at {c})'})
        for t in thin_regions(g):
            issues.append({'part': p.name, **t})
        mrr = g.minimum_rotated_rectangle
        xs, ys = mrr.exterior.coords.xy
        sides = sorted([math.dist((xs[k], ys[k]), (xs[k + 1], ys[k + 1])) for k in range(4)])
        w, L = sides[0], sides[-1]
        reasons = []
        if w < 7 and L / max(w, 0.1) > 9:
            reasons.append(f'long and thin ({L:.0f} x {w:.1f} mm)')
        if g.area < 30:
            reasons.append(f'tiny ({g.area:.0f} mm2)')
        if reasons:
            fragile.append({'part': p.name, 'why': ', '.join(reasons), 'spares': p.spares})
    return {'name': 'Minimum feature check', 'pass': not issues, 'count': len(issues), 'details': issues,
            'fragile': fragile,
            'summary': (f'every part is one piece; no feature thinner than {C.MIN_FEATURE} mm' if not issues else
                        f'{len(issues)} problems: parts in several pieces or features thinner than {C.MIN_FEATURE} mm')}


def run_all(kit, spacing=1.0):
    res = [check_collisions(kit, spacing), check_floating(kit, spacing), check_assembly_paths(kit),
           check_features(kit)]
    for p in kit.parts:
        p.thaw()
        p.__dict__.pop('_sample_cache', None)
    for h in kit.hardware:
        h.__dict__.pop('_sample_cache', None)
    return res
