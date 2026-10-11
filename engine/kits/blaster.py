"""Kit 1: Star Slinger - an original starship-shaped rubber band slinger.

Not a replica of any firearm: it is a spaceship with wings, a cockpit, thrusters and a tail fin.
The blaze orange nose box covers the full muzzle circumference for 32 mm (15 CFR 1150.3(b) asks for at least 6 mm),
and an orange plug and cap close the muzzle end flush (1150.3(a): recessed no more than 6 mm).

Mechanism (NEEDS PHYSICAL TEST, see kits/blaster/mechanism_test_plan.md)
- 8-tooth star wheel at the rear. Each loaded band stretches from the orange nose hook to one tooth.
  The bands' own tension turns the wheel clockwise (seen from the right side).
- Escapement: the trigger lever is one piece with an anchor that carries two pallets, 2.5 teeth apart.
  At rest the front pallet B holds a tooth. Pulling the trigger swaps the pallets: the wheel turns half a
  tooth and is caught by the back pallet A. Releasing the trigger swaps back: another half tooth.
  One full pull = one tooth = one band released when its tooth passes the front.
- A small rubber band returns the trigger. Loading: thumb the exposed wheel backward; the pallets click
  over the sloped backs of the teeth like a ratchet. Holds up to 7 bands.

World: mm, x forward (nose at +x), y up, z to the right. Centre plane z = 0.
Construction: two inner walls with edge-on ribs between them (9.6 mm gap for the 9 mm wheel and anchor),
decorated outer skins, all glue-free.
"""
from __future__ import annotations

import math

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from hartwood.geom import Kit, Part, Rod, T, circle, frame, rect, rect_c, rounded
from hartwood.joints import add_tabs, cross_halflap, edge_tabs, pierce, tab_joint
from hartwood import shapes as S
from hartwood.text import text_outline

X, Y, Z = np.array([1., 0, 0]), np.array([0., 1, 0]), np.array([0., 0, 1])
GAP = 9.6                       # clear width between inner walls (wheel and anchor are 9.0)
ZW = GAP / 2 + T / 2            # inner wall centre plane (6.3)
ZS = ZW + T                     # outer skin centre plane (9.3)
W = np.array([-55.0, 8.0])      # star wheel centre
R_ROOT, R_TIP = 15.0, 24.0
P = np.array([-55.0, -32.0])    # anchor pivot
NOSE_X = 160.0                  # muzzle end
ORANGE_X = 140.0                # orange nose walls start here; orange skins start at 128 (32 mm of blaze orange)
TOOTH_PHASE = 326.25            # leading faces of the teeth (deg), so pallet B holds one at rest
DOWEL = 4.76


def opening(g, r=1.3):
    return g.buffer(-r, join_style='round').buffer(r, join_style='round')


def polar(c, r, deg):
    a = math.radians(deg)
    return (c[0] + r * math.cos(a), c[1] + r * math.sin(a))


# ---------------------------------------------------------------- mechanism shapes (world XY)
def wheel_shape():
    pts = []
    for k in range(8):
        th = TOOTH_PHASE + 45 * k
        # leading face radial at th (front when turning clockwise), hooked back for the band
        for r, d in ((R_ROOT, 0), (R_TIP, 0), (R_TIP, 9), (R_TIP - 4.5, 15), (R_ROOT + 3.0, 26), (R_ROOT, 33)):
            pts.append(polar(W, r, th + d))
    g = Polygon(pts).buffer(0)
    return opening(g, 0.9).union(circle(*W, R_ROOT + 0.5)).buffer(0)


def anchor_shape():
    """Anchor + trigger in one plate. Pallet B (front) engaged at rest; pallet A (back) withdrawn."""
    A_ang, B_ang = 213.75, 326.25
    b_tip = polar(W, 18.0, B_ang - 2.0)          # inside the tooth gap, just ahead of a leading face
    a_tip = polar(W, R_TIP + 2.2, A_ang)         # clear of the tooth tips at rest
    arm_b = LineString([tuple(P), polar(W, 30, B_ang - 8), b_tip]).buffer(3.6, cap_style='round', join_style='round')
    arm_a = LineString([tuple(P), polar(W, 33, A_ang + 6), a_tip]).buffer(3.6, cap_style='round', join_style='round')
    boss = circle(*P, 7.5)
    trig = LineString([tuple(P), (-46, -50), (-40, -60), (-37, -66)]).buffer(4.5, cap_style='round', join_style='round')
    pad = rounded(rect(-44, -70, -33, -56), 3.0)
    hook = circle(-32, -64, 3.4)                 # return band hooks here
    g = unary_union([arm_a, arm_b, boss, trig, pad, hook])
    # keep clear of the wheel except the pallet tips
    clear = circle(*W, R_TIP + 1.2)
    tips = unary_union([circle(*b_tip, 3.6), circle(*a_tip, 3.6)])
    g = g.difference(clear.difference(tips.buffer(0.01)))
    g = g.difference(wheel_shape().buffer(0.6))
    return opening(g, 1.25)


def hull_rear():
    """Rear inner wall (side view): hull, tail, grip and trigger guard."""
    pts = [(10, 20), (-28, 20), (-30, 12), (-80, 12), (-82, 24), (-122, 24), (-130, 14), (-130, 2), (-112, -6),
           (-104, -28), (-100, -112), (-96, -120), (-70, -120), (-66, -112), (-66, -76), (-60, -76), (-14, -76),
           (-10, -70), (-10, -12), (10, -12)]
    g = Polygon(pts).buffer(0)
    finger = rounded(rect(-58, -70, -18, -36), 6)
    g = g.difference(finger)
    # the wheel and anchor sit between the walls; the walls only need the axle bosses
    return opening(g, 1.3)


def hull_front():
    return Polygon([(10, 20), (60, 18), (ORANGE_X, 16), (ORANGE_X, -8), (60, -8), (10, -12)]).buffer(0)


def build():
    k = Kit('blaster', 'Star Slinger')
    k.tagline = 'A starship that slings rubber bands. Seven shots, one at a time.'
    k.story = ('The Star Slinger is a little starfighter with a big secret: a clockwork star wheel in its engine. '
               'Load up to seven rubber bands, aim at a paper target, and each pull of the trigger lets exactly '
               'one band fly. Its blaze orange nose is built into the ship, so it always looks like what it is: '
               'a toy. Build the mechanism, test it at each step, then show it off on its launch stand.')
    k.difficulty = 4
    k.build_hours = '5 to 6 h'
    k.price = 49.99
    k.extras = {'#64 rubber bands (3.5 x 1/4 in), ammo': 12, '#16 rubber band, trigger return': 2,
                '3/16 in birch dowel, 15.6 mm': 3, 'wax stick': 1, 'sandpaper 240 grit': 1,
                'paper targets (printed)': 3}
    step = [0]

    def nxt(title, **kw):
        step[0] += 1
        k.step(step[0], title, **kw)
        return step[0]

    def wall_frame(z):
        return frame((0, 0, z), X, Y)            # laser face toward +z for both sides (left gets flipped)

    # ------------------------------------------------------------ inner walls (left first, the kit is built lying on its left side)
    s_left = nxt('Lay down the left inner walls', tip='Build the ship lying on its left side.', icons=['flip'])
    walls = {}
    for side in (-1, 1):
        for part_name, shape, col in (('rear', hull_rear(), 'natural'), ('front', hull_front(), 'natural'),
                                      ('nose', rect(ORANGE_X, -8, NOSE_X, 16), 'orange')):
            w = Part(f'wall_{"l" if side < 0 else "r"}_{part_name}', shape, color=col,
                     mat=wall_frame(side * ZW), step=s_left, insert=(0, 0, -1), explode=40)
            walls[(side, part_name)] = w
    # ------------------------------------------------------------ ribs between the walls (edge-on, 9.6 mm wide)
    s_ribs = nxt('Stand the ribs in the left walls', tip='Each rib has tabs on both long edges.', icons=['press'])
    ribs = []

    def rib(name, a, b, normal_up=True, color='natural', parts=('rear', 'front'), n_tabs=None, tab_w=8.0):
        """A rib along the segment a->b (side view), spanning the gap; tabs into the walls that it overlaps."""
        a = np.asarray(a, float); b = np.asarray(b, float)
        L = np.linalg.norm(b - a)
        u = np.array([*(b - a) / L, 0.0])
        o = np.array([a[0], a[1], 0.0])
        # plate in the plane spanned by u and z; local x along u, local y along z
        m = frame(o, u, Z)
        r = Part(name, rect(0, -GAP / 2, L, GAP / 2), color=color, mat=m, step=s_ribs, insert=(0, 0, -1),
                 explode=30)
        # shift so the rib's face sits on the segment line (plate centred 1.5 below/above): keep centred
        n = n_tabs or max(1, int(L // 28))
        tabs_l, tabs_r = [], []
        xs = np.linspace(L / (2 * n), L - L / (2 * n), n)
        for x in xs:
            pw = None
            p3 = o + u * x
            for (sd, pn), w in walls.items():
                if pn in parts:
                    loc = np.linalg.inv(w.mat) @ np.array([*p3, 1.0])
                    if w.shape.buffer(-2.5).contains(Point(loc[0], loc[1])):
                        pw = pw or []
                        pw.append(sd)
            if pw and -1 in pw and 1 in pw:
                tabs_l.append(rect(x - tab_w / 2, -GAP / 2 - T, x + tab_w / 2, -GAP / 2))
                tabs_r.append(rect(x - tab_w / 2, GAP / 2, x + tab_w / 2, GAP / 2 + T))
        add_tabs(r, tabs_l + tabs_r)
        for t in tabs_l + tabs_r:
            for (sd, pn), w in walls.items():
                if pn in parts:
                    try:
                        pierce(w, r, t, fit='press')
                    except ValueError:
                        pass
        ribs.append(r)
        return r
    # rib planes sit just inside the outline edges (centre line 1.5 mm inside)
    rib('rib_deck', (-26, 18.5), (ORANGE_X, 14.5))
    rib('rib_keel', (20, -3.5), (ORANGE_X, -3.5))
    rib('nose_top', (ORANGE_X, 14.5), (NOSE_X, 14.5), parts=('nose',), n_tabs=1, color='orange')
    rib('nose_bottom', (ORANGE_X, -6.5), (NOSE_X, -6.5), parts=('nose',), n_tabs=1, color='orange')
    rib('rib_tail_top', (-124, 22.5), (-84, 22.5), parts=('rear',))
    rib('rib_tail_end', (-128.5, 4), (-128.5, 13), parts=('rear',), n_tabs=1, tab_w=6)
    rib('rib_grip_back', (-102.5, -34), (-99, -108), parts=('rear',), n_tabs=2)
    rib('rib_grip_bottom', (-94, -118.5), (-72, -118.5), parts=('rear',), n_tabs=1, tab_w=10)
    rib('rib_guard', (-56, -74.5), (-16, -74.5), parts=('rear',), n_tabs=2)
    rib('rib_guard_front', (-11.5, -66), (-11.5, -16), parts=('rear',), n_tabs=2)
    rib('rib_grip_front', (-67.5, -110), (-67.5, -80), parts=('rear',), n_tabs=1, tab_w=10)

    # ------------------------------------------------------------ star wheel (3 discs on 2 square pegs, turns on a dowel)
    s_wheel = nxt('Build the star wheel and put it on its axle',
                  tip='Three discs, two pegs. Wax the axle hole.', icons=['wax', 'press'],
                  test='Spin the wheel with a finger. It should turn freely and wobble less than 1 mm.')
    wheel_axle = Rod('wheel axle', (W[0], W[1], -ZW - T / 2), (W[0], W[1], ZW + T / 2), step=s_wheel,
                     insert=(0, 0, -1), explode=30, mechanism=True, note='3/16 in dowel, 15.6 mm')
    wpegs = []
    for j, ang in enumerate((90, 270)):
        c = polar(W, 9.5, ang)
        p = Part(f'wheel_peg{j}', rect(-2.0, -1.5 * T, 2.0, 1.5 * T), color='natural',
                 mat=frame((c[0], c[1], 0), X, Z), step=s_wheel, insert=(0, 0, -1), explode=30, mechanism=True,
                 spares=1)
        wpegs.append(p)
    wheel = []
    for i, z in enumerate((-T, 0.0, T)):
        d = Part(f'wheel{i}', wheel_shape(), color='teal' if i == 1 else 'natural', mat=wall_frame(z),
                 step=s_wheel, insert=(0, 0, -1), explode=30, mechanism=True,
                 note='Teeth must catch a #64 band and release it at the front. Needs physical test.')
        d.cuts.append((circle(*W, DOWEL / 2), 'spin'))
        for p in wpegs:
            pierce(d, p, fit='snug')
        wheel.append(d)
    for (sd, pn), w in walls.items():
        if pn == 'rear':
            w.cuts.append((circle(*W, DOWEL / 2), 'grip'))

    # ------------------------------------------------------------ anchor + trigger (3 layers, 2 pegs, pivot dowel)
    s_anchor = nxt('Build the trigger and fit it under the wheel',
                   tip='The two pallets must point at the wheel. Wax the pivot.', icons=['wax', 'press'],
                   test='Press the trigger slowly: the wheel turns half a tooth. Release: another half tooth.')
    pivot = Rod('trigger pivot', (P[0], P[1], -ZW - T / 2), (P[0], P[1], ZW + T / 2), step=s_anchor,
                insert=(0, 0, -1), explode=30, mechanism=True, note='3/16 in dowel, 15.6 mm')
    apegs = []
    for j, c in enumerate(((-49.5, -45.5), (-38.5, -63.0))):
        p = Part(f'trigger_peg{j}', rect(-2.0, -1.5 * T, 2.0, 1.5 * T), color='natural',
                 mat=frame((c[0], c[1], 0), X, Z), step=s_anchor, insert=(0, 0, -1), explode=30, mechanism=True,
                 spares=1)
        apegs.append(p)
    anchor = []
    for i, z in enumerate((-T, 0.0, T)):
        a = Part(f'trigger{i}', anchor_shape(), color='orange' if i == 1 else 'natural', mat=wall_frame(z),
                 step=s_anchor, insert=(0, 0, -1), explode=30, mechanism=True,
                 note='Escapement anchor: pallet depth and timing need physical test.')
        a.cuts.append((circle(*P, DOWEL / 2), 'spin'))
        for p in apegs:
            pierce(a, p, fit='snug')
        anchor.append(a)
    spring_post = Rod('return band post', (-16.0, -64.0, -ZW - T / 2), (-16.0, -64.0, ZW + T / 2), step=s_anchor,
                      insert=(0, 0, -1), explode=30, mechanism=True, note='3/16 in dowel, 15.6 mm; the #16 band '
                      'runs from here to the hook on the trigger')
    for (sd, pn), w in walls.items():
        if pn == 'rear':
            w.cuts.append((circle(*P, DOWEL / 2), 'grip'))
            w.cuts.append((circle(-16.0, -64.0, DOWEL / 2), 'grip'))

    # ------------------------------------------------------------ right inner walls close the sandwich
    s_right = nxt('Close it with the right inner walls', tip='Line up the three dowels and all the rib tabs, '
                  'then press evenly.', icons=['press'],
                  test='Pull the trigger 8 times. The wheel should step one tooth per pull.')
    for (sd, pn), w in walls.items():
        if sd > 0:
            w.step = s_right

    # ------------------------------------------------------------ orange nose box (blaze orange tip)
    s_nose = nxt('Build the blaze orange nose', tip='This orange box must stay on the ship: it marks it as a toy.',
                 icons=['press', 'careful'])
    nose_parts = [walls[(-1, 'nose')], walls[(1, 'nose')], next(r for r in ribs if r.name == 'nose_top'),
                  next(r for r in ribs if r.name == 'nose_bottom')]
    # band hook: three orange plates standing on the nose top, keyed by a peg
    hook_shape = opening(unary_union([rect(142, 16, 157, 25), rect(150, 16, 156, 33), rect(150, 30, 160, 33)]), 1.3)
    hooks = []
    for i, z in enumerate((-T, 0.0, T)):
        h = Part(f'nose_hook{i}', hook_shape, color='orange', mat=wall_frame(z), step=s_nose, insert=(0, -1, 0),
                 explode=25)
        hooks.append(h)
    nose_top = nose_parts[2]
    t = rect(145, 13, 149, 16)              # only the centre plate tabs into the nose top rib
    add_tabs(hooks[1], t)
    pierce(nose_top, hooks[1], t, fit='press')
    hpeg = Part('nose_hook_peg', rect(-2.0, -1.5 * T, 2.0, 1.5 * T), color='orange',
                mat=frame((146.5, 20.5, 0), X, Z), step=s_nose, insert=(0, 0, -1), explode=25, spares=1)
    for h in hooks:
        pierce(h, hpeg, fit='snug')
    # muzzle plug (fills the nose box end, flush) and cap, both blaze orange, locked by one peg
    plug = Part('nose_plug', rect(-GAP / 2, -5.0, GAP / 2, 13.0), color='orange',
                mat=frame((NOSE_X - T / 2, 0, 0), -Z, Y), step=s_nose, insert=(-1, 0, 0), explode=25)
    cap = Part('nose_cap', rounded(rect(-ZS - T / 2, -8.0, ZS + T / 2, 16.0), 2.5), color='orange',
               mat=frame((NOSE_X + T / 2, 0, 0), -Z, Y), step=s_nose, insert=(-1, 0, 0), explode=25)
    from hartwood.geom import regular_star
    cap.engrave.append(regular_star(0, 9.5, 4.2, 1.9, 5, rot=90))
    cap_peg = Part('nose_cap_peg', rect(-2.0, -T, 2.0, T), color='orange', mat=frame((NOSE_X, 1.5, 0), Z, X),
                   step=s_nose, insert=(-1, 0, 0), explode=25, spares=1)
    pierce(plug, cap_peg, fit='press'); pierce(cap, cap_peg, fit='snug')
    hooks += [plug, cap, cap_peg]

    # ------------------------------------------------------------ outer skins with pegs
    s_skin_r = nxt('Add the right hull skins', tip='Square pegs lock each skin to the wall.', icons=['press'])
    s_skin_l = nxt('Turn the ship over and add the left hull skins', tip='Mirror image of the last step.',
                   icons=['flip', 'press'])
    skins = []

    def layer_below(side, z_part):
        """Parts whose slab is the one just inside z_part on this side."""
        zb = z_part - side * T
        out = []
        for w in walls.values():
            if abs(w.mat[2, 3] - zb) < 1e-6:
                out.append(w)
        for sk in skins:
            if abs(sk.mat[2, 3] - zb) < 1e-6 and not sk.name.endswith(tuple(f'_peg{i}' for i in range(9))):
                out.append(sk)
        return out

    def add_peg(part, side, px, py, step):
        """Peg through `part` and the layer below. Moves up to 8 mm to find a spot with 2.5 mm walls."""
        below = layer_below(side, part.mat[2, 3])

        def world(q):
            return q.shape if q.mat[0, 0] > 0 else affinity.scale(q.shape, -1, 1, origin=(0, 0))
        pw = world(part).buffer(-2.5)
        best = None
        for r in np.arange(0, 8.01, 0.5):
            for a in np.linspace(0, 2 * math.pi, max(1, int(r * 4)) + 1)[:-1] if r else [0.0]:
                cx, cy = px + r * math.cos(a), py + r * math.sin(a)
                fp = rect_c(cx, cy, 4, 3)
                if not pw.contains(fp):
                    continue
                hits = [q for q in below if world(q).buffer(-2.5).contains(fp)]
                if hits:
                    best = (cx, cy, hits); break
            if best:
                break
        if best is None:
            raise ValueError(f'peg of {part.name} near ({px}, {py}) has nothing under it')
        cx, cy, hits = best
        zc = part.mat[2, 3] - side * T / 2          # boundary between the part and the layer below
        n = len([q for q in skins if q.name.startswith(part.name + '_peg')])
        peg = Part(f'{part.name}_peg{n}', rect(-2.0, -T, 2.0, T), color='natural',
                   mat=frame((cx, cy, zc), X, (0, 0, side)), step=step, insert=(0, 0, -side), explode=30, spares=1)
        pierce(part, peg, fit='snug')
        for q in hits:
            pierce(q, peg, fit='press')
        skins.append(peg)

    def skin(name, shape, side, color, pegs, score=None, text=None, z_extra=0.0, step=None):
        z = side * (ZS + z_extra)
        st = step or (s_skin_r if side > 0 else s_skin_l)
        sk = Part(name, shape, color=color, mat=wall_frame(z), step=st, insert=(0, 0, -side), explode=30)
        if side < 0:
            sk.flip()
        if score:
            sk.score.extend(score if side > 0 else [affinity.scale(l, -1, 1, origin=(0, 0)) for l in score])
        if text:
            txt, h, tx, ty = text
            g, _ = text_outline(txt, h, x=tx if side > 0 else -tx, y=ty, anchor='center')
            sk.engrave.append(g)
        sk.code_on_part = False
        skins.append(sk)
        for (px, py) in pegs:
            add_peg(sk, side, px, py, st)
        return sk
    for side in (1, -1):
        tag = 'r' if side > 0 else 'l'
        rear_skin = Polygon([(40, 18.8), (10, 20), (-28, 20), (-30, 12), (-80, 12), (-82, 24), (-122, 24), (-130, 14),
                             (-130, 2), (-112, -6), (-104, -28), (-70, -28), (-14, -20), (-10, -12), (10, -12),
                             (40, -10)]).buffer(0)
        rear_skin = opening(rear_skin.difference(circle(*W, 11.0)), 1.3)
        skin(f'skin_rear_{tag}', rear_skin, side, 'natural', [(-100, 10), (-20, 10), (25, 12), (-90, -14)],
             score=S.panel_lines(rear_skin, spacing=26, inset=2.0))
        front_skin = opening(Polygon([(40, 18.8), (60, 18), (128, 16.3), (128, -8), (60, -8), (40, -10)]).buffer(0), 1.3)
        skin(f'skin_front_{tag}', front_skin, side, 'natural', [(52, 5), (116, 5)],
             score=S.panel_lines(front_skin, spacing=24, inset=2.0))
        skin(f'skin_nose_{tag}', rect(128, -8, NOSE_X, 16), side, 'orange', [(132, 4), (151, 4)])
        eng = opening(Polygon([(-34, 10), (-84, 10), (-86, 0), (-80, -12), (-36, -12)]).buffer(0)
                      .difference(circle(*W, 9.0)), 1.3)
        skin(f'engine_panel_{tag}', eng, side, 'teal', [(-74, -5), (-40, -4)],
             score=S.clip_lines([LineString([(x, -14), (x, 12)]) for x in (-44, -48, -66, -70)], eng, 1.2), z_extra=T)
        ck = opening(Polygon([(62, 17.6), (100, 16.6), (112, 7), (60, 7)]).buffer(0), 1.3)
        skin(f'cockpit_side_{tag}', ck, side, 'teal', [(84, 12.0)], z_extra=T)
        stripe = opening(Polygon([(46, -7.6), (124, -7.2), (124, 1.4), (46, 1.4)]).buffer(0), 1.3)
        skin(f'stripe_{tag}', stripe, side, 'orange', [(52, -3.0), (119, -3.0)], z_extra=T,
             text=('STAR SLINGER', 4.4, 86, -3.2))
        # air intake under the wing root, across the rear/front skin seam
        intake = opening(Polygon([(14, -11.0), (44, -9.0), (44, -1.2), (24, -1.2)]).buffer(0), 1.3)
        skin(f'intake_{tag}', intake, side, 'teal', [(33, -5.4)], z_extra=T,
             score=S.clip_lines([LineString([(x, -12), (x, 0)]) for x in (20, 24, 40)], intake, 1.2))

    for side in (1, -1):
        tag = 'r' if side > 0 else 'l'
        for j, poly_ in enumerate((Polygon([(-122, 21.5), (-96, 21.5), (-90, 12.5), (-122, 12.5)]),
                                   Polygon([(-24, 17.2), (6, 17.2), (6, 8.2), (-20, 8.2)]))):
            pnl = opening(poly_.buffer(0), 1.0)
            skin(f'panel_{tag}{j}', pnl, side, 'natural' if j else 'teal', [tuple(np.array(pnl.centroid.coords[0]))],
                 score=S.clip_lines([LineString([(pnl.bounds[0] + 3, pnl.centroid.y), (pnl.bounds[2] - 3, pnl.centroid.y)])], pnl, 1.0),
                 z_extra=T)

    # ------------------------------------------------------------ reactor rings around the wheel axle (decoration)
    s_reactor = nxt('Add the reactor rings', tip='Rings sit around the wheel axle on both sides.', icons=['press'])
    for side in (1, -1):
        tag = 'r' if side > 0 else 'l'
        made = []
        peg_at = [(W[0], W[1] - 14.0), (W[0], W[1] + 13.8)]
        for i, (ro, ri) in enumerate(((19.5, 9.5), (18.2, 9.5))):
            rg = skin(f'reactor_{tag}{i}', circle(*W, ro).difference(circle(*W, ri)), side,
                      'teal' if i == 0 else 'orange', [], z_extra=2 * T + i * T, step=s_reactor,
                      score=S.clip_lines([LineString([polar(W, ri + 1.5, a), polar(W, ro - 1.5, a)])
                                          for a in range(0, 360, 30)], circle(*W, ro).difference(circle(*W, ri)), 0.6)
                      if i == 0 else None)
            made.append(rg)
            add_peg(rg, side, peg_at[i][0], peg_at[i][1], s_reactor)

    # ------------------------------------------------------------ canopy (teal, three layers on the deck)
    s_canopy = nxt('Fit the cockpit canopy', tip='The canopy tabs go into the deck rib.', icons=['press'])
    deck = next(r for r in ribs if r.name == 'rib_deck')
    canopy = []

    def deck_top(x):
        return 18.5 - (x + 26) * 4.0 / 166.0 + T / 2
    for i, (z, top) in enumerate(((-T, 26.0), (0.0, 26.5), (T, 26.0))):
        cs = opening(Polygon([(64, deck_top(64)), (102, deck_top(102)), (99, top - 1), (88, top), (72, top - 0.5)]).buffer(0), 1.3)
        cp = Part(f'canopy{i}', cs, color='teal', mat=wall_frame(z), step=s_canopy, insert=(0, -1, 0), explode=25)
        cp.code_on_part = False
        canopy.append(cp)
    t = Polygon([(76, deck_top(76) - T), (86, deck_top(86) - T), (86, deck_top(86) + 0.2), (76, deck_top(76) + 0.2)])
    add_tabs(canopy[1], t)
    pierce(deck, canopy[1], t, fit='press')
    cpeg = Part('canopy_peg', rect(-2.0, -1.5 * T, 2.0, 1.5 * T), color='natural', mat=frame((90.0, 21.7, 0), X, Z),
                step=s_canopy, insert=(0, 0, -1), explode=25, spares=1)
    for cp in canopy:
        pierce(cp, cpeg, fit='snug')

    # ------------------------------------------------------------ wings (through skin and wall)
    s_wings = nxt('Slide in the wings', tip='Each wing has two tabs that go through the skin and the wall.',
                  icons=['press', 'x2'])
    wings = []
    for side in (1, -1):
        span = 62.0
        # wing in the XZ plane at y = 2; local x = world x, local y = world z * side
        ws = Polygon([(-28, ZS + T / 2), (40, ZS + T / 2), (14, ZS + span), (-22, ZS + span), (-32, ZS + 20)]).buffer(0)
        ws = opening(ws, 1.3)
        m = frame((0, 2.0, 0), X, (0, 0, side))
        wg = Part(f'wing_{"r" if side > 0 else "l"}', ws, color='natural', mat=m, step=s_wings, insert=(0, 0, -side),
                  explode=30)
        if wg.mat[1, 2] < 0:          # keep the laser face up
            wg.flip()
        wing_tabs = [rect(-22, ZW - T / 2, -12, ZS + T / 2), rect(18, ZW - T / 2, 28, ZS + T / 2)]
        if wg.mat[0, 0] < 0:
            wing_tabs = [affinity.scale(t, -1, 1, origin=(0, 0)) for t in wing_tabs]
        add_tabs(wg, wing_tabs)
        for t in wing_tabs:
            for sk in skins:
                if sk.name.startswith(('skin_rear', 'skin_front')) and '_peg' not in sk.name and ((sk.mat[2, 3] > 0) == (side > 0)):
                    try:
                        pierce(sk, wg, t, fit='press')
                    except ValueError:
                        pass
            for (sd, pn), w in walls.items():
                if sd == side:
                    try:
                        pierce(w, wg, t, fit='press')
                    except ValueError:
                        pass
        wg.score.extend(S.clip_lines([LineString([(-26 + 10 * i, 0), (-18 + 10 * i, 80)]) for i in range(7)],
                                     wg.shape, 1.5))
        wg.code_on_part = False
        wings.append(wg)
        # orange wing tip fin (vertical), cross half-lapped onto the wing near its tip
        fin_z = side * (ZS + span - 8)
        fn = Part(f'wing_fin_{"r" if side > 0 else "l"}', opening(Polygon([(-24, -4), (10, -4), (6, 12), (-16, 14)]).buffer(0), 1.3),
                  color='orange', mat=frame((0, 2.0, fin_z), X, Y), step=s_wings, insert=(0, -1, 0), explode=25)
        fn.code_on_part = False
        cross_halflap(fn, wg, fit='snug', a_open=np.array([0, -1.0, 0]))
        fn.insert = fn.__dict__['lap_insert']
        wings.append(fn)
        # engine pod hanging under the wing (tabs up into the wing) with a layer on each side
        pz = side * (ZS + 36.0)
        pod = Part(f'pod_{"r" if side > 0 else "l"}', opening(unary_union([rounded(rect(-14, -14, 30, 0.5), 6.5),
                                                                          rect(-2, 0.5, 6, 2.0), rect(14, 0.5, 22, 2.0)]), 1.0),
                   color='teal', mat=frame((0, 0, pz), X, Y), step=s_wings, insert=(0, 1, 0), explode=25)
        pt = [rect(-2, 0.5, 6, 3.5), rect(14, 0.5, 22, 3.5)]
        pod.shape = unary_union([pod.shape] + pt).buffer(0)
        pod.__dict__.setdefault('tabs', []).extend(pt)
        for t_ in pt:
            pierce(wg, pod, t_, fit='press')
        pod.code_on_part = False
        wings.append(pod)
        for li, lz in enumerate((pz + T, pz - T)):
            toward = 1.0 if pz > lz else -1.0
            outer = abs(lz) > abs(pz)
            lay = Part(f'pod_{"r" if side > 0 else "l"}_side{li}', opening(rounded(rect(-10, -12, 24, -2), 4.5), 1.0),
                       color='orange' if outer else 'natural', mat=frame((0, 0, lz), X, Y), step=s_wings,
                       insert=(0, 0, toward), explode=25 if outer else 12)
            if lz < pz:
                lay.flip()
            lay.code_on_part = False
            wings.append(lay)
        ppeg = Part(f'pod_{"r" if side > 0 else "l"}_peg', rect(-2.0, -1.5 * T, 2.0, 1.5 * T), color='natural',
                    mat=frame((8.0, -7.0, pz), X, Z), step=s_wings, insert=(0, 0, -side), explode=25, spares=1)
        for q in wings[-3:]:
            pierce(q, ppeg, fit='snug')
        wings.append(ppeg)
        # missile under the wing tip, tabbed up into the wing
        ms = Part(f'missile_{"r" if side > 0 else "l"}',
                  opening(Polygon([(-20, 0.5), (12, 0.5), (20, -3.5), (12, -7.5), (-16, -7.5), (-22, -12), (-26, -12),
                                   (-22, -3)]).buffer(0), 1.0),
                  color='orange', mat=frame((0, 0, side * (ZS + 47.0)), X, Y), step=s_wings, insert=(0, 1, 0), explode=25)
        mt = [rect(-12, 0.5, -6, 3.5), rect(2, 0.5, 8, 3.5)]
        ms.shape = unary_union([ms.shape] + mt).buffer(0)
        ms.__dict__.setdefault('tabs', []).extend(mt)
        for t_ in mt:
            pierce(wg, ms, t_, fit='press')
        if side < 0:
            ms.flip()
        ms.code_on_part = False
        wings.append(ms)
        # orange stripe on top of the wing
        sw_ = opening(Polygon([(-8, ZS + 20), (14, ZS + 20), (6, ZS + 48), (-12, ZS + 48)]).buffer(0), 1.0)
        st_ = Part(f'wing_stripe_{"r" if side > 0 else "l"}', sw_, color='orange', mat=frame((0, 2.0 + T, 0), X, (0, 0, side)),
                   step=s_wings, insert=(0, -1, 0), explode=25)
        if st_.mat[1, 2] < 0:
            st_.flip()
        st_.code_on_part = False
        wings.append(st_)
        cpt = np.array([2.0, 2.0 + T / 2, side * (ZS + 26)])
        speg = Part(f'wing_stripe_{"r" if side > 0 else "l"}_peg', rect(-2.0, -T, 2.0, T), color='natural',
                    mat=frame(cpt, X, Y), step=s_wings, insert=(0, -1, 0), explode=25, spares=1)
        pierce(st_, speg, fit='snug'); pierce(wg, speg, fit='press')
        wings.append(speg)

    # ------------------------------------------------------------ tail fin
    s_fin = nxt('Raise the tail fin', tip='Its two tabs go into the top rib behind the wheel.', icons=['press'])
    tail_rib = next(r for r in ribs if r.name == 'rib_tail_top')
    fin = Part('tail_fin', opening(Polygon([(-122, 24), (-88, 24), (-104, 56), (-118, 58)]).buffer(0), 1.3),
               color='teal', mat=wall_frame(0.0), step=s_fin, insert=(0, -1, 0), explode=30)
    ft = [rect(-118, 21, -110, 24), rect(-102, 21, -94, 24)]
    add_tabs(fin, ft)
    for t in ft:
        pierce(tail_rib, fin, t, fit='press')
    fin.score.extend(S.clip_lines([LineString([(-118, 30 + 6 * i), (-96, 30 + 6 * i)]) for i in range(4)], fin.shape, 1.5))
    fin.code_on_part = False
    side_fins = []
    for side in (1, -1):
        sfn = Part(f'tail_fin_{"r" if side > 0 else "l"}', opening(Polygon([(-120, 24), (-94, 24), (-106, 42), (-118, 44)]).buffer(0), 1.3),
                   color='orange', mat=wall_frame(side * T), step=s_fin, insert=(0, 0, -side), explode=25)
        if side < 0:
            sfn.flip()
        sfn.code_on_part = False
        side_fins.append(sfn)
    fpeg = Part('tail_fin_peg', rect(-2.0, -1.5 * T, 2.0, 1.5 * T), color='natural', mat=frame((-110.0, 32.0, 0), X, Z),
                step=s_fin, insert=(0, 0, -1), explode=25, spares=1)
    for f_ in [fin] + side_fins:
        pierce(f_, fpeg, fit='snug')

    # ------------------------------------------------------------ thrusters (stacked rings on pegs at the tail)
    s_thr = nxt('Build the thruster', tip='The peg goes into the tail. Then stack the rings, big ones first.', icons=['press'])
    thrusters = []
    tail_end = next(r for r in ribs if r.name == 'rib_tail_end')
    ty = 8.5
    tpeg = Part('thruster_peg', rect(-148.0, ty - 2.0, -124.0, ty + 2.0), color='natural', mat=wall_frame(0.0),
                step=s_thr, insert=(1, 0, 0), explode=25, spares=1)
    pierce(tail_end, tpeg, rect(-130, ty - 2.0, -127, ty + 2.0), fit='press')
    thrusters.append(tpeg)
    for i, (r_o, col) in enumerate(((9.0, 'teal'), (10.0, 'orange'), (8.5, 'teal'), (9.5, 'orange'), (8.0, 'teal'), (6.5, 'natural'))):
        x = -130.0 - T / 2 - i * T - 0.0
        ring = Part(f'thruster{i}', circle(0, 0, r_o).difference(circle(0, 0, 0.01)) if False else circle(0, 0, r_o),
                    color=col, mat=frame((x, ty, 0), -Z, Y), step=s_thr, insert=(1, 0, 0), explode=25)
        pierce(ring, tpeg, fit='snug')
        ring.code_on_part = False
        thrusters.append(ring)
    # ------------------------------------------------------------ grip skins
    s_grip = nxt('Add the grip panels', tip='Textured panels on both sides of the grip.', icons=['press'])
    grip_parts = []
    for side in (1, -1):
        gs = opening(Polygon([(-102, -30), (-70, -30), (-67, -78), (-68, -112), (-97, -116), (-100, -108)]).buffer(0), 1.3)
        skin(f'grip_{"r" if side > 0 else "l"}', gs, side, 'natural', [(-86, -50), (-84, -96)],
             score=S.clip_lines([LineString([(-110, y), (-60, y + 6)]) for y in range(-112, -28, 6)], gs, 1.5),
             step=s_grip)

    # ------------------------------------------------------------ belly fin (tabs up into the keel rib) with orange side layers
    s_belly = nxt('Add the belly fin', tip='Tabs up into the keel, then a stripe on each side and one peg.',
                  icons=['press'])
    keel = next(r for r in ribs if r.name == 'rib_keel')
    belly = []
    bf = Part('belly_fin', opening(Polygon([(62, -5), (108, -5), (104, -12), (94, -24), (82, -24), (70, -12)]).buffer(0), 1.3),
              color='teal', mat=wall_frame(0.0), step=s_belly, insert=(0, 1, 0), explode=30)
    bt = [rect(72, -5, 80, -2), rect(90, -5, 98, -2)]
    add_tabs(bf, bt)
    for t in bt:
        pierce(keel, bf, t, fit='press')
    bf.code_on_part = False
    belly.append(bf)
    for side in (1, -1):
        bl = Part(f'belly_fin_{"r" if side > 0 else "l"}', opening(Polygon([(72, -9), (102, -9), (96, -19), (80, -19)]).buffer(0), 1.3),
                  color='orange', mat=wall_frame(side * T), step=s_belly, insert=(0, 0, -side), explode=25)
        if side < 0:
            bl.flip()
        bl.code_on_part = False
        belly.append(bl)
    bpeg = Part('belly_fin_peg', rect(-2.0, -1.5 * T, 2.0, 1.5 * T), color='natural', mat=frame((88.0, -13.5, 0), X, Z),
                step=s_belly, insert=(0, 0, -1), explode=25, spares=1)
    for b_ in belly:
        pierce(b_, bpeg, fit='snug')
    belly.append(bpeg)

    # ------------------------------------------------------------ display stand
    s_stand = nxt('Build the launch stand and the target', tip='The target hangs on its dowel and swings when hit.',
                  icons=['press'], test='Tap the target plate. It should swing back and settle again.')
    stand = _stand(k, s_stand)
    s_mount = nxt('Put the ship on its launch stand', tip='Grip between the two boots, barrel on the upright.',
                  icons=['careful'])

    for p in list(walls.values()) + ribs + wheel + wpegs + anchor + apegs + hooks + [hpeg] + skins + \
            canopy + [cpeg] + wings + [fin] + side_fins + [fpeg] + thrusters + belly + stand:
        k.add(p)
    k.add(wheel_axle, pivot, spring_post)
    for w in walls.values():
        w.code_on_part = True
    ship = {p.name for p in k.parts if p not in stand} | {wheel_axle.name, pivot.name, spring_post.name}
    k.subassemblies.append({'name': 'ship', 'members': ship, 'step': s_mount, 'insert': (0, -1, 0), 'explode': 60.0})
    k.extras['3/16 in birch dowel, 63 mm (target hinge)'] = 1
    return k


def _stand(k, step):
    """Launch stand: the ship stands on its grip between two boots, the barrel rests on an upright.
    A swinging target and a band rack plug into the same base."""
    parts = []
    DOWN = (0, -1, 0)
    by = -120.0 - T / 2
    base = Part('stand_base', rounded(rect(-118, -40, 150, 40), 10), color='natural',
                mat=frame((0, by, 0), X, -Z), step=step, insert=DOWN, explode=30)
    t, _ = text_outline('STAR SLINGER', 7.0, x=-30, y=-30.0, anchor='center')
    base.engrave.append(t)
    base.code_on_part = False
    parts.append(base)
    for side in (1, -1):
        zc = side * (ZS + T / 2 + 0.4 + T / 2)
        b = Part(f'stand_boot_{"r" if side > 0 else "l"}', rounded(rect(-102, -120, -64, -108), 3), color='teal',
                 mat=frame((0, 0, zc), X, Y), step=step, insert=DOWN, explode=30)
        tab_joint(base, b, [rect(-96, -120, -86, -120 - T), rect(-80, -120, -70, -120 - T)])
        b.code_on_part = False
        parts.append(b)
    up = Part('stand_upright', opening(Polygon([(-24, -120), (24, -120), (12, -8.0), (-12, -8.0)]).buffer(0), 1.3),
              color='teal', mat=frame((116.0, 0, 0), Z, Y), step=step, insert=DOWN, explode=30)
    tab_joint(base, up, [rect(-12, -120, 12, -120 - T)])
    up.code_on_part = False
    parts.append(up)
    # band rack: hooks for spare bands
    rack = Part('band_rack', opening(unary_union([rect(20, -120, 64, -104)] + [rect(24 + 12 * i, -104, 30 + 12 * i, -94)
                                                                                for i in range(4)] +
                                                [rect(22 + 12 * i, -96, 32 + 12 * i, -92) for i in range(4)]), 1.3),
                color='orange', mat=frame((0, 0, 26.0), X, Y), step=step, insert=DOWN, explode=30)
    tab_joint(base, rack, [rect(26, -120, 36, -120 - T), rect(48, -120, 58, -120 - T)])
    rack.code_on_part = False
    parts.append(rack)
    # swinging target: frame of two uprights with feet + a cross rib, a plate hanging on a dowel
    s_t = step
    tz, tx0, tx1 = -26.0, 40.0, 100.0
    ups = []
    for i, x in enumerate((tx0, tx1)):
        u = Part(f'target_side{i}', opening(unary_union([rect(-12, -120, 12, -116), Polygon([(-5, -116), (5, -116), (4, -38), (-4, -38)]),
                                                         circle(0, -42, 5.0)]), 1.3),
                 color='teal', mat=frame((x, 0, tz), Z, Y), step=s_t, insert=DOWN, explode=30)
        tab_joint(base, u, [rect(-4, -120, 4, -120 - T)])
        u.cuts.append((circle(0, -42, DOWEL / 2), 'grip'))
        u.code_on_part = False
        ups.append(u)
        parts.append(u)
    plate = Part('target_plate', rounded(rect(tx0 + T / 2 + 2.0, -102, tx1 - T / 2 - 2.0, -49), 4),
                 color='natural', mat=frame((0, 0, tz), X, Y), step=s_t, insert=DOWN, explode=30, mechanism=True,
                 note='Swings back when hit, falls back by gravity. Needs physical test.')
    plate.code_on_part = False
    parts.append(plate)
    for i, ex in enumerate((tx0 + 10, tx1 - 10)):
        ear = Part(f'target_ear{i}', opening(unary_union([rect(-6, -56, 6, -42), circle(0, -42, 6.0)]), 1.3), color='orange',
                   mat=frame((ex, 0, tz), Z, Y), step=s_t, insert=DOWN, explode=25, mechanism=True)
        ear.cuts.append((circle(0, -42, DOWEL / 2), 'spin'))
        cross_halflap(ear, plate, fit='snug', a_open=np.array([0, -1.0, 0]))
        ear.insert = ear.__dict__['lap_insert']
        ear.code_on_part = False
        parts.append(ear)
    cx_, cy_ = (tx0 + tx1) / 2, -74.0
    rings = []
    for i, (shape, col, zl) in enumerate(((circle(cx_, cy_, 21).difference(circle(cx_, cy_, 11.5)), 'orange', 1),
                                          (circle(cx_, cy_, 11.0), 'teal', 1), (circle(cx_, cy_, 6.0), 'orange', 2))):
        o = Part(f'target_ring{i}', shape, color=col, mat=frame((0, 0, tz + zl * T), X, Y), step=s_t, insert=(0, 0, -1),
                 explode=25)
        o.code_on_part = False
        parts.append(o)
        rings.append(o)
    pg = Part('target_ring0_peg', rect(-2.0, -T, 2.0, T), color='natural', mat=frame((cx_, cy_ + 16.2, tz + T / 2), X, Z),
              step=s_t, insert=(0, 0, -1), explode=25, spares=1)
    pierce(rings[0], pg, fit='snug'); pierce(plate, pg, fit='press')
    parts.append(pg)
    # bullseye: one long peg through the dot, the teal disc and the plate
    pg = Part('target_dot_peg', rect(-2.0, -1.5 * T, 2.0, 1.5 * T), color='natural', mat=frame((cx_, cy_, tz + T), X, Z),
              step=s_t, insert=(0, 0, -1), explode=25, spares=1)
    pierce(rings[2], pg, fit='snug'); pierce(rings[1], pg, fit='press'); pierce(plate, pg, fit='press')
    parts.append(pg)
    # safety plaque at the front of the base: teal backing and engraved orange plate
    pz_ = 30.0
    back = Part('safety_back', rounded(rect(70, -120, 120, -95), 3), color='teal', mat=frame((0, 0, pz_ - T), X, Y),
                step=step, insert=DOWN, explode=30)
    tab_joint(base, back, [rect(72, -120, 80, -120 - T), rect(110, -120, 118, -120 - T)])
    plq = Part('safety_plaque', rounded(rect(73, -120, 117, -98), 2.5), color='orange', mat=frame((0, 0, pz_), X, Y),
               step=step, insert=DOWN, explode=30)
    tab_joint(base, plq, [rect(84, -120, 92, -120 - T), rect(98, -120, 106, -120 - T)])
    for line, ty_ in (('AIM AT TARGETS', -103.5), ('NEVER AT FACES', -109.0)):
        g, _ = text_outline(line, 3.0, x=95.0, y=ty_, anchor='center')
        plq.engrave.append(g)
    plq.code_on_part = False
    back.code_on_part = False
    spg = Part('safety_peg', rect(-2.0, -T, 2.0, T), color='natural', mat=frame((95.0, -114.5, pz_ - T / 2), X, Z),
               step=step, insert=(0, 0, -1), explode=25, spares=1)
    pierce(plq, spg, fit='snug'); pierce(back, spg, fit='press')
    parts += [back, plq, spg]
    k.add(Rod('target hinge dowel', (tx0 - T / 2, -42, tz), (tx1 + T / 2, -42, tz), step=s_t, insert=(-1, 0, 0),
              explode=70, mechanism=True, note='3/16 in dowel, 63 mm'))
    return parts
