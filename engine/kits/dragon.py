"""Kit 2: Emberwing - a dragon guarding a ruined tower.

The dragon body is 19 stacked slices (3 mm each) cut from a 3D shape, threaded on square keys.
Moving parts: the lower jaw opens on a dowel, and the treasure chest lid opens on a dowel.
The front claws really grip the parapet: each claw slice and the merlon under it are cross half-lapped.

World: mm, y up, x = the dragon's facing direction, z toward the viewer.
"""
from __future__ import annotations

import math

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from hartwood.geom import Kit, Part, Rod, T, circle, frame, rect, rect_c, rounded
from hartwood.joints import add_tabs, cross_halflap, edge_tabs, footprint, pierce, tab_joint
from hartwood import shapes as S
from hartwood.text import text_outline
from kits import dragon_shape as D

X, Y, Z = np.array([1., 0, 0]), np.array([0., 1, 0]), np.array([0., 0, 1])
DOWN, UP = (0, -1, 0), (0, 1, 0)
TOP = D.TOP
N_SL = 19
ZS = [(i - 9) * T for i in range(N_SL)]          # slice centre planes
TOWER = dict(x0=-75.0, x1=75.0, z0=-42.0, z1=42.0)
GROUND_Y = 0.0
KEY_W, KEY_H = 3.0, 8.0                           # key bar footprint in a slice (x by y)
HINGE = np.array([88.0, TOP + 134.0])
JAW_OPEN = 14.0


def opening(g, r=1.3):
    return g.buffer(-r, join_style='round').buffer(r, join_style='round')


def slice_frame(z):
    """Right side and centre: laser face toward +z. Left side: laser face toward -z (outward)."""
    return frame((0, 0, z), X, Y) if z >= 0 else frame((0, 0, z), -X, Y)


def to_local(g, z):
    return g if z >= 0 else affinity.scale(g, -1, 1, origin=(0, 0))


def jaw_shape(open_deg=JAW_OPEN):
    hx, hy = HINGE
    top = [(hx, hy), (100, TOP + 132), (116, TOP + 129.5), (128, TOP + 127), (133, TOP + 125)]
    bottom = [(132, TOP + 121), (118, TOP + 119.5), (100, TOP + 119.5), (90, TOP + 122.5)]
    body = Polygon(top + bottom).buffer(0)
    teeth = [Polygon([(x - 1.6, y - 0.2), (x + 1.6, y - 0.2), (x, y + 3.2)]) for x, y in
             ((104, TOP + 131.6), (112, TOP + 130.2), (120, TOP + 128.6))]
    g = unary_union([body, circle(hx, hy, 6.5)] + teeth)
    g = opening(g, 1.25)
    return affinity.rotate(g, -open_deg, origin=(hx, hy))


def build():
    k = Kit('dragon', 'Emberwing')
    k.tagline = 'A dragon guarding its tower. The jaw opens. So does the treasure chest.'
    k.story = ('High on a broken tower, Emberwing keeps watch over a chest of gold. Her wings are spread, '
               'her claws lock onto the stone, and her jaw opens in a silent roar. Every slice of her body is '
               'a 3 mm layer, stacked on hidden keys, with scales drawn by the laser. Lift the lid of the chest '
               'to check the gold is still there.')
    k.difficulty = 4
    k.build_hours = '6 to 8 h'
    k.price = 54.99
    k.extras = {'3/16 in birch dowel, 21 mm (jaw)': 1, '3/16 in birch dowel, 56 mm (chest hinge)': 1,
                'sandpaper 240 grit': 1}
    step = [0]

    def nxt(title, **kw):
        step[0] += 1
        k.step(step[0], title, **kw)
        return step[0]

    # ================================================================ DRAGON (sub-assembly)
    dragon_members = set()

    def dadd(*ps):
        for p in ps:
            dragon_members.add(p.name)
            k.add(p)

    # ---------------------------------------------------------------- slice regions
    tower_clip = unary_union([box(TOWER['x0'] - 1, -200, TOWER['x1'] + 1, TOP),
                              box(-400, -200, 400, GROUND_Y + T + 1.5)])   # not into the tower or the ground
    jaw_closed = jaw_shape(0)
    sweep = unary_union([jaw_shape(a) for a in np.linspace(-2, JAW_OPEN + 6, 8)]).buffer(1.0)
    regions = {}
    for z in ZS:
        g = D.slice_at(z)
        if g.is_empty:
            continue
        g = g.difference(tower_clip)
        # merlons under the front claws are cut out later by the half-laps; jaw zone:
        if abs(z) <= 3:
            g = g.difference(sweep)
        elif abs(z) <= 9:
            keep = unary_union([circle(*HINGE, 6.5), rect(HINGE[0] - 6.5, HINGE[1], HINGE[0] + 6.5, HINGE[1] + 16)])
            g = g.difference(sweep.difference(keep))
        g = opening(g.buffer(0), 1.3)
        regions[z] = g
    # dorsal spikes and tail spade on the centre slice
    cz = regions[0.0]
    top_edge = []
    spikes = []
    for t in np.linspace(0.30, 0.86, 13):
        i = int(t * (len(D.CURVE) - 1))
        p = D.CURVE[i]; q = D.CURVE[min(i + 3, len(D.CURVE) - 1)]
        tng = (q - p) / np.linalg.norm(q - p)
        nrm = np.array([-tng[1], tng[0]])
        ry = D.RY[i]
        base = p + nrm * (ry - 1.0)
        h = 7.0 + 3.0 * math.sin(math.pi * (t - 0.3) / 0.56)
        spikes.append(Polygon([base - tng * 4.5, base + tng * 4.5, base + nrm * h - tng * 2.0]))
    spade_c = D.CURVE[0]
    spade = Polygon([spade_c + (-7, 3), spade_c + (7, 3), spade_c + (0, -12)]).buffer(1.5)
    cz = unary_union([cz] + spikes + [spade]).difference(tower_clip)
    regions[0.0] = opening(cz, 1.3)

    # split into islands, drop crumbs
    islands = []           # (z, polygon)
    for z, g in regions.items():
        for p in getattr(g, 'geoms', [g]):
            if p.area >= 90:
                islands.append((z, p))

    # ---------------------------------------------------------------- keys
    MARGIN = 6.9
    import shapely as _shp
    _inner = {}
    for z, p in islands:
        q = p.buffer(-MARGIN)
        _shp.prepare(q)
        _inner[id(p)] = q

    def fits(poly, x, y):
        q = _inner.get(id(poly))
        if q is None:
            q = poly.buffer(-MARGIN)
        return bool(_shp.contains_xy(q, x, y))

    key_specs = []

    def key_poly(x, y):
        return rect_c(x, y, KEY_W, KEY_H)

    def run_for(x, y, z_seed):
        zs_ok = sorted(z for z, p in islands if fits(p, x, y))
        if z_seed not in zs_ok:
            return None
        # contiguous run around the seed
        lo = hi = z_seed
        while lo - T in zs_ok:
            lo -= T
        while hi + T in zs_ok:
            hi += T
        return lo, hi

    main_keys = [('key_hips', -28, TOP + 44), ('key_back', 2, TOP + 51), ('key_chest', 30, TOP + 64),
                 ('key_neck_low', 50, TOP + 90), ('key_neck_high', 60, TOP + 118), ('key_skull', 80, TOP + 143),
                 ('key_tail_base', -70, TOP + 31), ('key_tail_mid', -110, TOP + 4), ('key_tail_low', -118, TOP - 26)]
    centre = [p for z, p in islands if abs(z) < 1e-6]

    def snap(x, y, reach=18.0):
        """Nearest point to (x, y) where a key fits in the centre slice; prefer long runs."""
        best = None
        for dx in np.arange(-reach, reach + 0.1, 1.5):
            for dy in np.arange(-reach, reach + 0.1, 1.5):
                px, py = x + dx, y + dy
                if not any(fits(c, px, py) for c in centre):
                    continue
                r = run_for(px, py, 0.0)
                if r is None:
                    continue
                score = math.hypot(dx, dy) - 1.5 * (r[1] - r[0]) / T
                if best is None or score < best[0]:
                    best = (score, px, py, r)
        return best

    for name, x, y in main_keys:
        b = snap(x, y)
        if b is None:
            print(f'  note: no room for {name} near ({x}, {y}); skipped')
            continue
        _, px, py, r = b
        if r[1] - r[0] < T - 1e-6:
            print(f'  note: {name} would pass one slice only; skipped')
            continue
        if any(key_poly(px, py).distance(key_poly(kx, ky)) < 3.0 for _n, kx, ky, _r in key_specs):
            continue
        key_specs.append((name, px, py, r))
    # wing bar: a long key across the shoulders that sticks out both sides for the wings
    _wb = snap(16.0, TOP + 76.0, reach=10.0)
    WB = (float(_wb[1]), float(_wb[2]))
    key_specs.append(('wing_bar', WB[0], WB[1], (-33.0, 33.0)))

    def covered(z, p):
        for _n, x, y, (lo, hi) in key_specs:
            if lo - 1e-6 <= z <= hi + 1e-6 and p.contains(key_poly(x, y)):
                return True
        return False

    auto = 0
    for z, p in sorted(islands, key=lambda e: abs(e[0])):
        if covered(z, p):
            continue
        # try candidate points inside the island, far from existing key holes
        inner = p.buffer(-MARGIN)
        if inner.is_empty:
            continue
        cands = []
        for q in getattr(inner, 'geoms', [inner]):
            c = q.representative_point()
            cands.append((c.x, c.y))
            minx, miny, maxx, maxy = q.bounds
            for xx in np.arange(minx, maxx, 3.0):
                for yy in np.arange(miny, maxy, 3.0):
                    if q.contains(Point(xx, yy)):
                        cands.append((xx, yy))
        best = None
        for (x, y) in cands:
            r = run_for(x, y, z)
            if r is None or r[1] - r[0] < T - 1e-6:
                continue
            # keep away from other key holes in shared slices
            clash = False
            for _n, kx, ky, (lo, hi) in key_specs:
                if hi >= r[0] - 1e-6 and lo <= r[1] + 1e-6 and key_poly(kx, ky).distance(key_poly(x, y)) < 3.0:
                    clash = True; break
            if clash:
                continue
            score = (r[1] - r[0])
            if best is None or score > best[0]:
                best = (score, x, y, r)
        if best:
            auto += 1
            key_specs.append((f'key_aux{auto}', best[1], best[2], best[3]))

    # ---------------------------------------------------------------- slice parts
    s_core = nxt('Start the dragon: centre slice and keys',
                 tip='The red centre slice carries the spikes. Push every key halfway through it.',
                 icons=['press', 'centre'])
    right_groups = [(3, 9), (12, 18), (21, 27)]
    s_right = [nxt(f'Right side: slices {lo // 3 + 1} to {hi // 3 + 1} from the centre',
                   tip='Slide each slice onto the keys. Match the outline to the slice below.', icons=['press'])
               for lo, hi in right_groups]
    s_left = [nxt(f'Left side: slices {lo // 3 + 1} to {hi // 3 + 1} from the centre',
                  tip='Same as the right side, mirror image.', icons=['press', 'flip'])
              for lo, hi in right_groups]
    slice_parts = []
    counts = {}
    for z, p in sorted(islands, key=lambda e: (abs(e[0]), e[0] < 0)):
        az = abs(z)
        if az < 1e-6:
            st = s_core
        else:
            gi = next(i for i, (lo, hi) in enumerate(right_groups) if lo - 1e-6 <= az <= hi + 1e-6)
            st = s_right[gi] if z > 0 else s_left[gi]
        idx = counts.get(z, 0); counts[z] = idx + 1
        sgn = 'c' if az < 1e-6 else ('r' if z > 0 else 'l')
        name = f'slice_{sgn}{int(az // 3)}' + (f'_{idx}' if idx else '')
        part = Part(name, to_local(p, z), color='red' if az < 1e-6 else 'natural', mat=slice_frame(z), step=st,
                    insert=(0, 0, -1) if z > 0 else (0, 0, 1), explode=30, group='dragon')
        part.code_on_part = False                      # slice faces show; codes go on the sheet
        part.__dict__['z'] = z
        slice_parts.append(part)
    keys = []
    for name, x, y, (lo, hi) in key_specs:
        kp = Part(name, rect(lo - T / 2, y - KEY_H / 2, hi + T / 2, y + KEY_H / 2), color='natural',
                  mat=frame((x, 0, 0), Z, Y), step=s_core, insert=(0, 0, -1), explode=max(30, hi + 10),
                  group='dragon')
        keys.append(kp)
    zstep = {}
    for sp in slice_parts:
        zstep[round(sp.__dict__['z'], 3)] = sp.step
    for kp, (name, x, y, (lo, hi)) in zip(keys, key_specs):
        if name.startswith('key_aux'):
            outer = hi if abs(hi) >= abs(lo) else lo
            kp.step = zstep.get(round(outer, 3), s_core)
            kp.insert = (0, 0, -1) if outer > 0 else (0, 0, 1)
            kp.explode = 30
    for kp, (name, x, y, (lo, hi)) in zip(keys, key_specs):
        fp_world = key_poly(x, y)
        for sp in slice_parts:
            z = sp.__dict__['z']
            if z < lo - 1e-6 or z > hi + 1e-6:
                continue
            wp = sp.shape if z >= 0 else affinity.scale(sp.shape, -1, 1, origin=(0, 0))
            if wp.buffer(-2.4).contains(fp_world):
                sp.cuts.append((to_local(fp_world, z), 'snug'))
            elif wp.intersects(fp_world):
                # key exits the body here: clean notch, no thin walls
                notch = fp_world.buffer(2.6, join_style='mitre')
                sp.shape = to_local(opening(wp.difference(notch), 1.3), z)
    # center slice + keys first, then the side slices
    dadd(next(sp for sp in slice_parts if abs(sp.__dict__['z']) < 1e-6))
    for kp in keys:
        dadd(kp)
    for sp in slice_parts:
        if abs(sp.__dict__['z']) > 1e-6:
            dadd(sp)
    # scales: score fish-scales on the visible band of each side slice (the part not covered by the next slice out)
    by_z = {}
    for sp in slice_parts:
        by_z.setdefault(sp.__dict__['z'], []).append(sp)

    def world_shape(sp):
        z = sp.__dict__['z']
        return sp.shape if z >= 0 else affinity.scale(sp.shape, -1, 1, origin=(0, 0))
    for sp in slice_parts:
        z = sp.__dict__['z']
        if abs(z) < 1e-6:
            continue
        nxt_z = z + (T if z > 0 else -T)
        outer = unary_union([world_shape(o) for o in by_z.get(nxt_z, [])]) if nxt_z in by_z else None
        band = world_shape(sp) if outer is None else world_shape(sp).difference(outer.buffer(0.5))
        band = band.intersection(world_shape(sp).buffer(-0.9))
        if band.is_empty or band.area < 20:
            continue
        lines = S.scale_pattern(band, size=5.5, inset=0.6)
        sp.score.extend(to_local(l, z) for l in lines)

    # ---------------------------------------------------------------- jaw (moving part 1)
    s_jaw = nxt('Build the jaw and fit it with the dowel',
                tip='The jaw turns on the short dowel. Wax the dowel.', icons=['wax', 'press'],
                test='Open and close the jaw. It should swing freely and stay where you leave it.')
    jaw_parts = []
    for z in (-T, 0.0, T):
        jp = Part(f'jaw_{"c" if z == 0 else ("r" if z > 0 else "l")}', to_local(jaw_shape(), z),
                  color='red' if z == 0 else 'natural', mat=slice_frame(z), step=s_jaw,
                  insert=(0, 0, -1) if z >= 0 else (0, 0, 1), explode=30, group='dragon', mechanism=True,
                  note='Must swing on the dowel without rubbing the head slices.')
        jp.__dict__['z'] = z
        jp.code_on_part = False
        jaw_parts.append(jp)
    jaw_key_pt = (98.0, TOP + 126.0)
    jaw_key_pt = tuple(np.array(affinity.rotate(Point(*jaw_key_pt), -JAW_OPEN, origin=tuple(HINGE)).coords[0]))
    jk = Part('jaw_key', rect(-T * 1.5, jaw_key_pt[1] - 2.5, T * 1.5, jaw_key_pt[1] + 2.5), color='natural',
              mat=frame((jaw_key_pt[0], 0, 0), Z, Y), step=s_jaw, insert=(0, 0, -1), explode=25, group='dragon',
              mechanism=True)
    for jp in jaw_parts:
        pierce(jp, jk, fit='snug')
        jp.cuts.append((to_local(circle(*HINGE, 4.76 / 2), jp.__dict__['z']), 'spin'))
    jaw_dowel = Rod('jaw dowel', (HINGE[0], HINGE[1], -10.5), (HINGE[0], HINGE[1], 10.5), step=s_jaw,
                    insert=(0, 0, -1), explode=30, mechanism=True, note='3/16 in dowel, 21 mm')
    # cheek slices (|z| = 6) hold the dowel
    for sp in slice_parts:
        if abs(sp.__dict__['z']) in (2 * T, 3 * T) and world_shape(sp).intersects(circle(*HINGE, 2.4)):
            sp.cuts.append((to_local(circle(*HINGE, 4.76 / 2), sp.__dict__['z']), 'grip'))
    for jp in jaw_parts:
        dadd(jp)
    dadd(jk)
    k.add(jaw_dowel); dragon_members.add(jaw_dowel.name)
    # jaw parts go in before the cheeks: move them to the core step
    for jp in jaw_parts + [jk]:
        jp.step = s_core
    jaw_dowel.step = s_left[0]

    # ---------------------------------------------------------------- eyes and claws (overlays on the outer slices)
    s_eye = nxt('Give her golden eyes', tip='Each eye sits in its socket and is held by one square peg.', icons=['press', 'x2'])
    eye_pt = (101.0, TOP + 140.0)

    def outermost(pt, side, margin=5.0):
        best = None
        for sp in slice_parts:
            z = sp.__dict__['z']
            if (z > 0) != (side > 0) or abs(z) < 1e-6:
                continue
            if world_shape(sp).buffer(-margin).contains(Point(*pt)):
                if best is None or abs(z) > abs(best.__dict__['z']):
                    best = sp
        return best

    def overlay_on(sp, shape_w, name, color, peg_at, step, score=None, engrave=None):
        sgn = 1 if sp.__dict__['z'] > 0 else -1
        fp0 = rect_c(peg_at[0], peg_at[1], 4, 3).buffer(3.0)
        holders = [o for o in slice_parts if (o.__dict__['z'] > 0) == (sgn > 0) and abs(o.__dict__['z']) > 1e-6
                   and world_shape(o).contains(fp0)]
        if not holders:
            raise ValueError(f'{name}: no slice can hold the peg')
        sp = max(holders, key=lambda o: abs(o.__dict__['z']))
        z = sp.__dict__['z']
        oz = z + sgn * T
        # sockets: slices in the overlay plane and beyond make room for it
        for o in slice_parts:
            oz_ = o.__dict__['z']
            if (oz_ > 0) == (sgn > 0) and abs(oz_) >= abs(oz) - 1e-6 and world_shape(o).intersects(shape_w):
                o.shape = to_local(opening(world_shape(o).difference(shape_w.buffer(0.3)), 1.3), oz_)
        o = Part(name, to_local(shape_w, oz), color=color, mat=slice_frame(oz), step=step,
                 insert=(0, 0, -sgn), explode=25, group='dragon')
        o.__dict__['z'] = oz
        if score:
            o.score.extend(to_local(l, oz) for l in score)
        if engrave:
            o.engrave.extend(to_local(e, oz) for e in engrave)
        o.code_on_part = False
        # peg spot: deepest point of (overlay and slice) so both keep thick walls around the hole
        common = shape_w.intersection(world_shape(sp)).buffer(-4.0)
        if not common.is_empty:
            from shapely.ops import polylabel
            cpoly = max(getattr(common, 'geoms', [common]), key=lambda q: q.area)
            pl_ = polylabel(cpoly, 0.2)
            peg_at = (pl_.x, pl_.y)
        inner_z = z - sgn * T
        fp = rect_c(peg_at[0], peg_at[1], 4, 3)
        inner_ok = any(abs(sp2.__dict__['z'] - inner_z) < 1e-6 and world_shape(sp2).buffer(-2.5).contains(fp)
                       for sp2 in slice_parts)
        inner_touch = any(abs(sp2.__dict__['z'] - inner_z) < 1e-6 and world_shape(sp2).intersects(fp.buffer(0.5))
                          for sp2 in slice_parts)
        layers = 3 if inner_ok else 2
        if not inner_ok and inner_touch:
            layers = 2
        y0 = -T * 0.5 if layers == 2 else -T * 1.5
        peg = Part(name + '_peg', rect(-2.0, y0, 2.0, y0 + layers * T), color='natural',
                   mat=frame((peg_at[0], peg_at[1], z + sgn * T / 2), X, (0, 0, sgn)), step=step,
                   insert=(0, 0, -sgn), explode=25, group='dragon', spares=1)
        pierce(o, peg, fit='snug'); pierce(sp, peg, fit='press')
        if layers == 3:
            for sp2 in slice_parts:
                if abs(sp2.__dict__['z'] - inner_z) < 1e-6 and world_shape(sp2).buffer(-2.5).contains(fp):
                    pierce(sp2, peg, fit='press')
        dadd(o); dadd(peg)
        return o
    for side in (1, -1):
        sp = outermost(eye_pt, side)
        if sp is None:
            raise ValueError('no slice for the eye')
        eye = circle(*eye_pt, 6.0).union(Polygon([(eye_pt[0] + 3, eye_pt[1] + 4), (eye_pt[0] + 10, eye_pt[1] + 1),
                                                   (eye_pt[0] + 3, eye_pt[1] - 2.5)])).buffer(0)
        pupil = S.ellipse(eye_pt[0] + 2.2, eye_pt[1], 1.2, 3.6)
        overlay_on(sp, opening(eye, 1.3), f'eye_{"r" if side > 0 else "l"}', 'gold', (eye_pt[0] - 1.0, eye_pt[1]),
                   s_eye, engrave=[pupil])
    # ---------------------------------------------------------------- wings
    s_wbones = None
    s_wing = nxt('Attach the wings', tip='Slide each purple wing forward through the shoulder bar. Then add '
                 'the bones and the gold thumb claw with their pegs.', icons=['press', 'x2'])
    wing_sets = []
    for side in (1, -1):
        members = set()

        def wadd(p, members=members):
            members.add(p.name)
            k.add(p)
        _wing(k, wadd, side, WB, s_wbones, s_wing)
        wing_sets.append(members)

    k.subassemblies.append({'name': 'dragon', 'members': dragon_members, 'step': None, 'insert': DOWN,
                            'explode': 60.0})
    for side, members in zip((1, -1), wing_sets):
        k.subassemblies.append({'name': f'wing_{"r" if side > 0 else "l"}', 'members': members, 'step': s_wing,
                                'insert': (1, 0, 0), 'explode': 30.0, 'into': 'dragon'})

    # ================================================================ TOWER
    _tower(k, nxt, slice_parts, world_shape)
    return k


# ======================================================================== wings
def _wing_outline():
    """Bat wing in local coords: x = forward (world +x), y = up-and-out along the wing plane. Root at (0, 0)."""
    tips = [(12, 96), (-14, 150), (-58, 140), (-94, 108), (-112, 64)]
    root = (0.0, 0.0)
    wrist = tips[0]
    pts = [root, (6, 40), wrist]
    prev = wrist
    for t in tips[1:]:
        pts.append(t)
    # trailing edge scallops between finger tips are added as arcs (concave)
    poly = [root, (7, 45), (12, 96), (2, 128), (-14, 150)]
    for a, b in ((tips[1], tips[2]), (tips[2], tips[3]), (tips[3], tips[4])):
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        # pull the midpoint toward the wrist to make the scallop
        wv = (wrist[0] - mid[0], wrist[1] - mid[1])
        L = math.hypot(*wv)
        sc = (mid[0] + wv[0] / L * 16, mid[1] + wv[1] / L * 16)
        for t in np.linspace(0.15, 0.85, 6):
            # quadratic bezier a -> sc -> b
            x = (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * sc[0] + t ** 2 * b[0]
            y = (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * sc[1] + t ** 2 * b[1]
            poly.append((x, y))
        poly.append(b)
    poly += [(-70, 26), (-34, 6), (-10, -2)]
    membrane = Polygon(poly).buffer(0)
    bone_lines = [[(-1, 4), (7, 45), (12, 96)]] + [[wrist, t] for t in tips[1:]]
    bones = unary_union([LineString(b).buffer(3.4, cap_style='round') for b in bone_lines[:1]] +
                        [LineString([wrist, (wrist[0] + (t[0] - wrist[0]) * 0.93, wrist[1] + (t[1] - wrist[1]) * 0.93)]).buffer(2.6, cap_style='round')
                         for t in tips[1:]] + [circle(*wrist, 6.0), circle(2, 22, 5.0)])
    thumb = unary_union([circle(*wrist, 4.0), Polygon([(wrist[0] - 2, wrist[1] + 2), (wrist[0] + 12, wrist[1] + 6),
                                                       (wrist[0] + 3, wrist[1] - 3)]).buffer(1.4)])
    keepout = box(-0.2, -20, 40, 14)          # the wing bar sits here; only the tab passes through it
    membrane = membrane.difference(keepout)
    bones = bones.difference(keepout)
    return opening(membrane, 1.3), opening(bones, 1.3), opening(thumb, 1.3), tips


def _wing(k, dadd, side, WB, s_bones, s_wing):
    tilt = math.radians(36)
    up = np.array([0.0, math.cos(tilt), side * math.sin(tilt)])
    root = np.array([WB[0] - T / 2 - 0.0, WB[1], side * 24.0])
    # membrane frame: local x = forward, y = up-and-out; normal faces the viewer side (+z) for both wings
    m = frame(root, X, up)
    if m[2, 2] * side < 0:
        pass
    membrane, bones, thumb, tips = _wing_outline()
    tab = rect(0, -3.0, 3.6, 3.0)
    tag = 'r' if side > 0 else 'l'
    mem = Part(f'wing_{tag}', membrane, color='purple', mat=m, step=s_bones, insert=(1, 0, 0), explode=40,
               group='dragon')
    mem.code_on_part = False
    # veins between the bones
    wrist = tips[0]
    vs = []
    for a, b in zip(tips[1:], tips[2:]):
        for f in (0.35, 0.65):
            t = (a[0] * (1 - f) + b[0] * f, a[1] * (1 - f) + b[1] * f)
            vs.append(LineString([(wrist[0] + (t[0] - wrist[0]) * 0.25, wrist[1] + (t[1] - wrist[1]) * 0.25),
                                  (wrist[0] + (t[0] - wrist[0]) * 0.80, wrist[1] + (t[1] - wrist[1]) * 0.80)]))
    mem.score.extend(S.clip_lines(vs, membrane.difference(bones.buffer(1.0)), 1.0))
    add_tabs(mem, tab)
    # bones layer on the membrane's laser face, held by three pegs
    n = m[:3, 2]
    bm = m.copy(); bm[:3, 3] = m[:3, 3] + n * T
    bone = Part(f'wing_{tag}_bones', bones, color='natural', mat=bm, step=s_bones, insert=tuple(-n), explode=25,
                group='dragon')
    bone.code_on_part = False
    tm = bm.copy(); tm[:3, 3] = bm[:3, 3] + n * T
    th = Part(f'wing_{tag}_thumb', thumb, color='gold', mat=tm, step=s_bones, insert=tuple(-n), explode=25,
              group='dragon')
    th.code_on_part = False
    dadd(mem); dadd(bone); dadd(th)
    peg_pts = [(2, 22), (wrist[0], wrist[1])]
    for j, (px, py) in enumerate(peg_pts):
        c = m[:3, :3] @ np.array([px, py, 0.0]) + m[:3, 3]
        long_ = 3 if j == 1 else 2         # the wrist peg also goes through the thumb
        peg = Part(f'wing_{tag}_peg{j}', rect(-2.0, -T / 2, 2.0, -T / 2 + long_ * T), color='natural',
                   mat=frame(c, m[:3, 0], n), step=s_bones, insert=tuple(-n), explode=25, group='dragon')
        pierce(mem, peg, fit='press'); pierce(bone, peg, fit='snug')
        if j == 1:
            pierce(th, peg, fit='snug')
        dadd(peg)
    # the root tab goes through the wing bar
    bar = k.by_name('wing_bar')
    pierce(bar, mem, tab, fit='press')
    for p in [mem, bone, th] + [k.by_name(f'wing_{tag}_peg{j}') for j in range(2)]:
        p.step = s_wing


# ======================================================================== tower
def _tower(k, nxt, slice_parts, world_shape):
    x0, x1, z0, z1 = TOWER['x0'], TOWER['x1'], TOWER['z0'], TOWER['z1']
    wall_y0, wall_y1 = GROUND_Y + T, TOP - T
    s_ground = nxt('Lay the ground plate', tip='This is the rocky ground under the tower.', icons=[])
    gx0, gx1, gz0, gz1 = -134.0, 108.0, -52.0, 94.0
    ground = Part('ground', rounded(rect(gx0, gz0, gx1, gz1), 10), color='natural',
                  mat=frame((0, GROUND_Y + T / 2, 0), X, -Z), step=s_ground, insert=DOWN)
    # local (x, y) = world (x, -z): convert footprint rect in world xz -> local
    ground.shape = rounded(rect(gx0, -gz1, gx1, -gz0), 10)
    stones = []
    rng = np.random.default_rng(3)
    for i in range(70):
        cx, cz = rng.uniform(gx0 + 8, gx1 - 8), rng.uniform(gz0 + 8, gz1 - 8)
        if x0 - 4 < cx < x1 + 4 and z0 - 4 < cz < z1 + 4:
            continue
        stones.append(S.ellipse(cx, -cz, rng.uniform(4, 8), rng.uniform(3, 6), rng.uniform(0, 180), 18).exterior)
    ground.score.extend(S.clip_lines([LineString(s.coords) for s in stones], ground.shape, 2))
    k.add(ground)
    s_walls = nxt('Build the tower walls', tip='Front and back first, then the sides.', icons=['press'])
    walls = {}
    for name, zc in (('wall_front', z1 + T / 2), ('wall_back', z0 - T / 2)):
        w = Part(name, rect(x0 - T, wall_y0, x1 + T, wall_y1), color='natural', mat=frame((0, 0, zc), X, Y),
                 step=s_walls, insert=DOWN)
        bottom_tabs = [rect(x, wall_y0, x + 12, wall_y0 - T) for x in (-62, -40, 28, 50)]
        tab_joint(ground, w, bottom_tabs)
        add_tabs(w, edge_tabs(x0 + 10, x1 - 10, wall_y1, T, n=4, width=12))
        if name == 'wall_back':
            w.flip()
        walls[name] = w
    for name, xc in (('wall_right', x1 + T / 2), ('wall_left', x0 - T / 2)):
        u = -Z if xc > 0 else Z
        w = Part(name, rect(z0, wall_y0, z1, wall_y1), color='natural', mat=frame((xc, 0, 0), u, Y),
                 step=s_walls, insert=DOWN)
        tab_joint(ground, w, edge_tabs(z0 + 8, z1 - 8, wall_y0, -T, n=2, width=12))
        add_tabs(w, edge_tabs(z0 + 8, z1 - 8, wall_y1, T, n=2, width=12))
        walls[name] = w
    # door (front) and arrow slit (right side)
    door = Polygon([(-16, wall_y0), (16, wall_y0), (16, wall_y0 + 30)] +
                   [(16 * math.cos(a), wall_y0 + 30 + 16 * math.sin(a)) for a in np.linspace(0, math.pi, 16)] +
                   [(-16, wall_y0 + 30)])
    walls['wall_front'].shape = walls['wall_front'].shape.difference(door.buffer(0))
    slit = rounded(rect_c(0, wall_y0 + 46, 6, 22), 2.8)
    walls['wall_right'].cuts.append((slit, 'press'))
    for w in walls.values():
        g = w.outline()
        w.score.extend(S.brick_pattern(g, w=15, h=7.5, inset=1.5))
        w.code_on_part = False
    k.add(*walls.values())
    # tower top
    s_top = nxt('Put the top on the tower', tip='Tabs from all four walls lock it in.', icons=['press'])
    top = Part('tower_top', rect(x0 - T, -(z1 + T), x1 + T, -(z0 - T)), color='natural',
               mat=frame((0, TOP - T / 2, 0), X, -Z), step=s_top, insert=DOWN)
    for w in walls.values():
        for t in w.__dict__['tabs'][-4 if 'front' in w.name or 'back' in w.name else -2:]:
            pierce(top, w, t)
    top.score.extend(S.brick_pattern(top.shape, w=18, h=18, inset=2))
    top.code_on_part = False
    k.add(top)
    # merlons: stone blocks standing on the top edge. Two under the front claws are half-lapped with them.
    s_mer = nxt('Stand the battlements', tip='Broken ones are on purpose: this tower is a ruin.', icons=['press'])
    mer = []
    claw_x = 64.0 + 2.0
    # front-edge merlons (YZ plane) under the claws
    for side in (1, -1):
        zc = side * 21.0
        m = Part(f'merlon_claw_{"r" if side > 0 else "l"}', rect(-7.5, TOP, 7.5, D.PARAPET), color='natural',
                 mat=frame((claw_x, 0, zc), -Z if side > 0 else Z, Y), step=s_mer, insert=DOWN)
        tab_joint(top, m, [rect(-5, TOP, 5, TOP - T)])
        mer.append(m)
    # other merlons around the edge (some broken)
    spots = [(-60, z1 - 1.5, 'x', 18), (-20, z1 - 1.5, 'x', 12), (25, z1 - 1.5, 'x', 18),
             (-60, z0 + 1.5, 'x', 16), (0, z0 + 1.5, 'x', 18), (45, z0 + 1.5, 'x', 10),
             (x0 + 1.5, 20, 'z', 18), (x0 + 1.5, -22, 'z', 14)]
    for i, (cx, cz, ax, h) in enumerate(spots):
        shape = Polygon([(-8, TOP), (8, TOP), (8, TOP + h), (3, TOP + h + 2), (-2, TOP + h - 1), (-8, TOP + h)])
        if i % 3 == 1:
            shape = Polygon([(-8, TOP), (8, TOP), (8, TOP + h * 0.6), (1, TOP + h), (-8, TOP + h * 0.8)])
        u = X if ax == 'x' else Z
        m = Part(f'merlon{i}', opening(shape.buffer(0), 1.3), color='natural', mat=frame((cx, 0, cz), u, Y),
                 step=s_mer, insert=DOWN)
        tab_joint(top, m, [rect(-4, TOP, 4, TOP - T)])
        m.score.extend(S.brick_pattern(m.shape, w=8, h=6, inset=1.2))
        m.code_on_part = False
        mer.append(m)
    k.add(*mer)
    # ---- set the dragon on the tower: feet tabs into the top, claw half-laps with the claw merlons
    s_mount = nxt('Set Emberwing on her tower', tip='Hind feet tabs go into the top. Front claws slide down over '
                  'the two front stones.', icons=['press', 'careful'])
    for sp in slice_parts:
        g = world_shape(sp)
        z = sp.__dict__['z']
        # hind feet: region touching the top surface inside the tower footprint
        band = g.intersection(box(x0 + 4, TOP - 0.01, x1 - 20, TOP + 1.5))
        if not band.is_empty and band.area > 6:
            for piece in getattr(band, 'geoms', [band]):
                bx0, _, bx1, _ = piece.bounds
                if bx1 - bx0 >= 7:
                    tab_w = rect(bx0 + 1.5, TOP - T, bx1 - 1.5, TOP + 0.01)
                    sp.shape = sp.shape.union(to_local(tab_w, z)).buffer(0)
                    sp.__dict__.setdefault('tabs', []).append(to_local(tab_w, z))
                    pierce(top, sp, to_local(tab_w, z))
    # front claws: extend the foot slices down over the claw merlons and half-lap them
    for m in mer[:2]:
        zc = m.mat[2, 3]
        half_span = 7.5
        for sp in slice_parts:
            z = sp.__dict__['z']
            if abs(z - zc) > half_span + T / 2 - 1e-6:
                continue
            g = world_shape(sp)
            near = g.intersection(box(claw_x - 8, D.PARAPET - 1, claw_x + 10, D.PARAPET + 8))
            if near.is_empty or near.area < 8:
                continue
            grip = rounded(rect(claw_x - 7, D.PARAPET - 7, claw_x + 7, D.PARAPET + 2), 2.0)
            sp.shape = sp.shape.union(to_local(grip, z)).buffer(0)
            cross_halflap(sp, m, fit='press', a_open=np.array([0, -1.0, 0]))
    next(sa for sa in k.subassemblies if sa['name'] == 'dragon')['step'] = s_mount
    # ---- door, ivy, torch
    s_dec = nxt('Add the door, the ivy and the torch', tip='Little square pegs hold each piece.', icons=['press'])
    fw = walls['wall_front']

    def wall_overlay(wall, name, shape, color, pegs, score=None, engrave=None):
        wn = wall.mat[:3, 2]
        if (wall.name == 'wall_back') or (wall.name == 'wall_left' and wn[0] > 0) or (wall.name == 'wall_right' and wn[0] < 0):
            pass
        o = Part(name, shape, color=color, step=s_dec, insert=tuple(-wn), explode=25)
        o.mat = wall.mat.copy(); o.mat[:3, 3] = wall.mat[:3, 3] + wn * T
        if score:
            o.score.extend(score)
        if engrave:
            o.engrave.extend(engrave)
        o.code_on_part = False
        k.add(o)
        for j, (px, py) in enumerate(pegs):
            c = wall.mat[:3, :3] @ np.array([px, py, 0]) + wall.mat[:3, 3]
            peg = Part(f'{name}_peg{j}', rect(-2.0, -1.5 * T, 2.0, 1.5 * T), color='natural',
                       mat=frame(c, wall.mat[:3, 0], wn), step=s_dec, insert=tuple(-wn), explode=25)
            pierce(o, peg, fit='snug'); pierce(wall, peg, fit='press')
            k.add(peg)
        return o
    door_leaf = Polygon([(-15, wall_y0 + 0.5), (15, wall_y0 + 0.5), (15, wall_y0 + 30)] +
                        [(15 * math.cos(a), wall_y0 + 30 + 15 * math.sin(a)) for a in np.linspace(0, math.pi, 16)] +
                        [(-15, wall_y0 + 30)]).buffer(0)
    door_frame = door.buffer(10).difference(door.buffer(0.01)).intersection(box(-60, wall_y0 + 0.5, 60, 200))
    planks = [LineString([(x, wall_y0 + 1), (x, wall_y0 + 44)]) for x in (-9, -3, 3, 9)]
    # door leaf sits in the opening, flush with the wall: held by the frame overlay
    wall_overlay(fw, 'door_arch', opening(door_frame, 1.3), 'natural', [(-21, wall_y0 + 10), (21, wall_y0 + 10)],
                 score=S.clip_lines([LineString([((16 + 3) * math.cos(a), wall_y0 + 30 + (16 + 3) * math.sin(a))
                                                   for a in np.linspace(0, math.pi, 30)])], door_frame, 0.6))
    ivy = []
    for i in range(7):
        a = 0.4 + i * 0.6
        ivy.append(affinity.translate(affinity.rotate(S.leaf(14, 9, 1.0), 40 + 25 * math.sin(i), origin=(0, 0)),
                                      38 + 4 * i, wall_y0 + 8 + 7 * i))
    vine = LineString([(36, wall_y0 + 5), (48, wall_y0 + 20), (52, wall_y0 + 40), (64, wall_y0 + 58)]).buffer(4.6)
    ivy_g = opening(unary_union(ivy + [vine]), 1.3).intersection(box(-100, wall_y0 + 0.5, 100, 200))
    wall_overlay(fw, 'ivy_front', ivy_g, 'green', [(48.5, wall_y0 + 20.5), (56.5, wall_y0 + 46)],
                 score=S.clip_lines([l for lf in ivy for l in [LineString(list(lf.exterior.coords)[:2])]], ivy_g, 0.8))
    flame = opening(unary_union([S.ellipse(-48, wall_y0 + 57, 6, 8), Polygon([(-54, wall_y0 + 58), (-48, wall_y0 + 72),
                                                                               (-42, wall_y0 + 58)])]), 1.3)
    flame = flame.intersection(box(-100, wall_y0 + 49.5, 100, 200))
    torch_g = opening(unary_union([rect(-53, wall_y0 + 28, -43, wall_y0 + 46), rect(-56, wall_y0 + 44, -40, wall_y0 + 49)]), 1.3)
    wall_overlay(fw, 'torch', torch_g, 'natural', [(-48, wall_y0 + 36)])
    wall_overlay(fw, 'torch_flame', flame, 'gold', [(-48, wall_y0 + 57)])
    for j, (bx, by) in enumerate([(-62, wall_y0 + 14), (-24, wall_y0 + 64)]):
        blk = rounded(rect_c(bx, by, 20, 10), 1.5)
        wall_overlay(fw, f'front_stone{j}', blk, 'natural', [(bx - 5, by), (bx + 5, by)],
                     score=[LineString([(bx - 7, by - 2), (bx - 1, by + 3)])])
    # stone blocks sticking out of the side walls (layered depth on the ruin)
    for wname in ('wall_right', 'wall_left'):
        w = walls[wname]
        for j, (bx, by) in enumerate([(-24, wall_y0 + 12), (18, wall_y0 + 30), (-10, wall_y0 + 58)]):
            blk = rounded(rect_c(bx, by, 22, 11), 1.5)
            wall_overlay(w, f'{wname}_stone{j}', blk, 'natural', [(bx - 5, by), (bx + 5, by)],
                         score=[LineString([(bx - 8, by - 2), (bx - 2, by + 3)])])
    # ---- rubble piles: fallen stones stacked on pegs
    s_rub = nxt('Scatter the fallen stones', tip='Each pile sits on one peg. Big stone at the bottom.', icons=['press'])
    ground = k.by_name('ground')
    rng = np.random.default_rng(11)
    for j, (rx, rz) in enumerate(((-98, 30), (-60, 62), (96, -20), (-112, -36))):
        peg = Part(f'rubble_peg{j}', rect(-2.0, GROUND_Y, 2.0, GROUND_Y + 4 * T), color='natural',
                   mat=frame((rx, 0, rz), X, Y), step=s_rub, insert=DOWN, explode=25)
        pierce(ground, peg, fit='press')
        k.add(peg)
        for i in range(3):
            r0 = 11 - 2.5 * i
            pts = [(r0 * (0.8 + 0.25 * rng.random()) * math.cos(a), r0 * (0.8 + 0.25 * rng.random()) * math.sin(a))
                   for a in np.linspace(0, 2 * math.pi, 7)[:-1]]
            st = Part(f'rubble{j}_{i}', opening(Polygon(pts).buffer(0.8), 1.3), color='natural',
                      mat=frame((rx, GROUND_Y + T + i * T + T / 2, rz), X, -Z), step=s_rub, insert=DOWN, explode=25)
            pierce(st, peg, fit='snug')
            st.score.append(LineString([(-r0 * 0.4, -r0 * 0.2), (r0 * 0.3, r0 * 0.25)]))
            st.code_on_part = False
            k.add(st)
    # ---- banner on a pole at the back corner of the tower
    s_ban = nxt('Raise the banner', tip='The pole goes into the tower top. The flag hooks on.', icons=['press'])
    top = k.by_name('tower_top')
    pole = Part('banner_pole', unary_union([rect(-2.5, TOP - T, 2.5, TOP + 74), circle(0, TOP + 76, 3.5)]), color='natural',
                mat=frame((62, 0, -32), X, Y), step=s_ban, insert=DOWN, explode=40)
    pierce(top, pole, rect(-2.5, TOP - T, 2.5, TOP), fit='press')
    pole.code_on_part = False
    k.add(pole)
    flag_shape = Polygon([(2.5, TOP + 44), (42, TOP + 50), (34, TOP + 59), (42, TOP + 68), (2.5, TOP + 72)])
    flag = Part('banner', opening(flag_shape.buffer(0), 1.3), color='red', mat=frame((62, 0, -32 - T), X, Y),
                step=s_ban, insert=(0, 0, 1), explode=25)
    flag.engrave.append(affinity.translate(S.regular_star(0, 0, 6, 2.6, 5, 90), 16, TOP + 58))
    flag.code_on_part = False
    k.add(flag)
    for j, fy in enumerate((TOP + 50, TOP + 66)):
        fp = Part(f'banner_peg{j}', rect(-2.0, -T / 2, 2.0, -T / 2 + 2 * T), color='natural',
                  mat=frame((62 + 7, fy, -32 - T / 2), X, -Z), step=s_ban, insert=(0, 0, 1), explode=25, spares=1)
        pierce(flag, fp, fit='snug')
        k.add(fp)
    # the pegs go through the flag and the pole: widen the pole there
    pole.shape = unary_union([pole.shape] + [rounded(rect_c(7, fy, 14, 10), 2) for fy in (TOP + 50, TOP + 66)]).buffer(0)
    for j in range(2):
        pierce(pole, k.by_name(f'banner_peg{j}'), fit='press')
    # ---- treasure chest with opening lid (moving part 2)
    _chest(k, nxt)


# ======================================================================== chest
def _chest(k, nxt):
    ground = k.by_name('ground')
    cx, cz = 30.0, 72.0
    L, W, H = 52.0, 32.0, 24.0
    y0 = GROUND_Y + T
    s_box = nxt('Build the treasure chest', tip='Gold bands go on last.', icons=['press'])
    bottom = Part('chest_bottom', rect(cx - L / 2, -(cz + W / 2), cx + L / 2, -(cz - W / 2)), color='natural',
                  mat=frame((0, y0 + T / 2, 0), X, -Z), step=s_box, insert=DOWN)
    bpegs = []
    k.add(bottom)
    # two pegs fix the chest to the ground
    for j, dx in enumerate((-14, 14)):
        peg = Part(f'chest_peg{j}', rect(-2.5, GROUND_Y, 2.5, y0 + T), color='natural',
                   mat=frame((cx + dx, 0, cz), X, Y), step=s_box, insert=DOWN, explode=25)
        pierce(ground, peg, fit='press'); pierce(bottom, peg, fit='snug')
        k.add(peg)
        bpegs.append(peg)
    bottom.step = s_box
    yb = y0 + T
    walls = []
    for name, zc in (('chest_front', cz + W / 2 - T / 2), ('chest_back', cz - W / 2 + T / 2)):
        w = Part(name, rect(cx - L / 2, yb, cx + L / 2, yb + H), color='natural', mat=frame((0, 0, zc), X, Y),
                 step=s_box, insert=DOWN)
        tab_joint(bottom, w, edge_tabs(cx - L / 2 + 6, cx + L / 2 - 6, yb, -T, n=2, width=10))
        walls.append(w)
    for name, xc in (('chest_right', cx + L / 2 - T / 2 - T), ('chest_left', cx - L / 2 + T / 2 + T)):
        u = -Z if xc > cx else Z
        lo, hi = (-(cz + W / 2 - T), -(cz - W / 2 + T)) if xc > cx else (cz - W / 2 + T, cz + W / 2 - T)
        hz_l = -(cz - W / 2 + 9.0) if xc > cx else (cz - W / 2 + 9.0)
        ear = unary_union([circle(hz_l, yb + H + 5.0, 6.0), rect(hz_l - 6.0, yb + H - 1, hz_l + 6.0, yb + H + 5.0)])
        w = Part(name, unary_union([rect(lo, yb, hi, yb + H), ear]).buffer(0), color='natural',
                 mat=frame((xc, 0, 0), u, Y), step=s_box, insert=DOWN)
        mid = (lo + hi) / 2
        tab_joint(bottom, w, [rect(mid - 5, yb, mid + 5, yb - T)])
        walls.append(w)
    for w in walls:
        w.score.extend(S.clip_lines([LineString([(-500, y), (500, y)]) for y in (yb + 8, yb + 16)], w.shape, 1.5))
        w.code_on_part = False
    k.add(*walls)
    fw = walls[0]
    for j, gx in enumerate((cx - 12, cx + 12)):
        gem = Part(f'gem{j}', S.regular_star(gx, yb + 12, 6.0, 4.2, 6).buffer(0.6).buffer(-0.6), color='red',
                   mat=fw.mat.copy(), step=s_box, insert=(0, 0, -1), explode=25)
        gem.mat[:3, 3] = fw.mat[:3, 3] + np.array([0, 0, T])
        gem.code_on_part = False
        k.add(gem)
        gp = Part(f'gem{j}_peg', rect(-2.0, -1.5 * T, 2.0, 1.5 * T), color='natural',
                  mat=frame((gx, yb + 12, fw.mat[2, 3]), X, Z), step=s_box, insert=(0, 0, -1), explode=25, spares=1)
        pierce(gem, gp, fit='snug'); pierce(fw, gp, fit='press')
        k.add(gp)
    # hinge dowel along x through the side walls' raised ears, at the back top
    hz = cz - W / 2 + 9.0
    hy = yb + H + 5.0
    for w in walls[2:]:
        hl = frame((0, 0, 0), np.eye(3)[0], np.eye(3)[1])
        loc = np.linalg.inv(w.mat) @ np.array([w.mat[0, 3], hy, hz, 1.0])
        w.cuts.append((circle(loc[0], loc[1], 4.76 / 2), 'grip'))
    s_lid = nxt('Hinge the lid', tip='Push the long dowel through both sides. The lid should swing open.',
                icons=['wax', 'press'], test='Open and close the lid. It should not rub the walls.')
    ang = 35.0
    # lid: top plate + two ears + front plate, built around the hinge, then rotated open
    lid_parts = []
    R = np.array([[1, 0, 0], [0, math.cos(math.radians(ang)), math.sin(math.radians(ang))],
                  [0, -math.sin(math.radians(ang)), math.cos(math.radians(ang))]])
    piv = np.array([0.0, hy, hz])

    def rot_frame(origin, u, v):
        o = R @ (np.asarray(origin, float) - piv) + piv
        return frame(o, R @ np.asarray(u, float), R @ np.asarray(v, float))
    lw = L - 4 * T - 1.0
    lid_top = Part('lid_top', rect(cx - L / 2, -(cz + W / 2 + 1), cx + L / 2, -(hz - 3)), color='natural',
                   mat=rot_frame((0, hy + 7.0 + T / 2, 0), X, -Z), step=s_lid, insert=DOWN, mechanism=True)
    ears = []
    for name, xc in (('lid_ear_r', cx + lw / 2 - T / 2), ('lid_ear_l', cx - lw / 2 + T / 2)):
        e = Part(name, unary_union([circle(hz, hy, 6.0), rect(hz, hy - 3, cz + W / 2 - 2 * T, hy + 7.0)]).buffer(0),
                 color='gold', mat=rot_frame((xc, 0, 0), Z, Y), step=s_lid, insert=DOWN, mechanism=True)
        e.cuts.append((circle(hz, hy, 4.76 / 2), 'spin'))
        tab_joint(lid_top, e, [rect(hz + 8, hy + 7.0, hz + 18, hy + 7.0 + T)])
        ears.append(e)
    front = Part('lid_front', rect(cx - lw / 2 + T, hy - 3, cx + lw / 2 - T, hy + 7.0), color='natural',
                 mat=rot_frame((0, 0, cz + W / 2 - 1.5 * T), X, Y), step=s_lid, insert=DOWN, mechanism=True)
    tab_joint(lid_top, front, edge_tabs(cx - lw / 2 + 4, cx + lw / 2 - 4, hy + 7.0, T, n=2, width=8))
    lid_top.score.extend(S.clip_lines([LineString([(x, -500), (x, 500)]) for x in (cx - 12, cx + 12)], lid_top.shape, 1.5))
    lid_top.code_on_part = False
    up_r = R @ Y
    lid_top.insert = tuple(-up_r)
    for e in ears + [front]:
        e.insert = tuple(up_r)
    front.code_on_part = False
    for e in ears:
        e.code_on_part = False
    k.add(lid_top, *ears, front)
    k.subassemblies.append({'name': 'lid', 'members': {lid_top.name, front.name, *[e.name for e in ears]},
                            'step': s_lid, 'insert': DOWN, 'explode': 40.0})
    s_hinge = nxt('Push the hinge dowel through', tip='Wax it first. Then try the lid.', icons=['wax', 'press'],
                  test='Open and close the lid. It should not rub the walls.')
    hinge = Rod('chest hinge dowel', (cx - L / 2 + T, hy, hz), (cx + L / 2 - T, hy, hz), step=s_hinge, insert=(-1, 0, 0),
                explode=60, mechanism=True, note='3/16 in dowel, 46 mm')
    k.add(hinge)
    # ---- coins: gold discs on two pegs, spilling in front
    s_gold = nxt('Pile up the gold', tip='Stack the coins on the little pegs.', icons=['press'])
    for j, (gx, gz, n) in enumerate(((cx - 34, cz + 4, 4), (cx + 36, cz - 2, 3), (cx - 50, cz - 10, 3))):
        peg = Part(f'coin_peg{j}', rect(-2.0, GROUND_Y, 2.0, y0 + n * T), color='natural',
                   mat=frame((gx, 0, gz), X, Y), step=s_gold, insert=DOWN, explode=25)
        pierce(ground, peg, fit='press')
        k.add(peg)
        for i in range(n):
            c = Part(f'coin{j}_{i}', circle(0.8 * (i % 2), 0.5 * (i % 3), 7.5 - 0.4 * i), color='gold',
                     mat=frame((gx, y0 + i * T + T / 2, gz), X, -Z), step=s_gold, insert=DOWN, explode=25)
            c.score.append(LineString(circle(0.8 * (i % 2), 0.5 * (i % 3), 5.6 - 0.4 * i).exterior.coords))
            pierce(c, peg, fit='snug')
            c.code_on_part = False
            k.add(c)
