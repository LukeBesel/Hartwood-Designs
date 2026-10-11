"""Kit 3: Blossom Waltz - a flower music box.

A pastel box holds a purchased 18-note wind-up movement. The movement turns a wooden shaft that spins a
turntable; on it stands a vase of stacked rings with a bouquet of eight layered flowers on curved stems.

World: mm, y up, x right, z toward the viewer (front wall at +z).
Joints used: tabs in square holes (box), slices on keys (vase rings), discs on a square peg (flower heads,
feet, coupler), cross half-laps (leaves, butterfly).
"""
from __future__ import annotations

import math

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from hartwood.geom import Block, Kit, Part, Rod, T, circle, frame, rect, rect_c, rounded
from hartwood.joints import add_tabs, cross_halflap, edge_tabs, pierce, tab_joint
from hartwood import shapes as S

X, Y, Z = np.array([1., 0, 0]), np.array([0., 1, 0]), np.array([0., 0, 1])
DOWN = (0, -1, 0)

# ---------------------------------------------------------------- key dimensions (Estimate: verify movement)
FEET_H = 15.0                  # 5 layers
BASE_Y = FEET_H                # base plate bottom
BASE_TOP = BASE_Y + T
WALL_H = 66.0                  # wall height above base top
TOP_Y = BASE_TOP + WALL_H      # top plate bottom (84)
BOX = 126.0                    # base / top size
MOV = dict(w=52.0, h=22.0, d=40.0)   # 18-note movement body (Estimate, TODO_LUCAS measure)
SPINDLE_D = 4.0                # rotating output shaft diameter (Estimate)
KEY_X = 16.0                   # winding key position under the movement (Estimate)
TT_Y = TOP_Y + T + 1.0 + 2 * T  # turntable bottom (hub of 2 discs under it, 1 mm air gap)
VASE_Y = TT_Y + T              # vase bottom
N_RINGS = 28
RING_IN = 13.0
KEY_R = (15.5, 20.5)           # radial span of the two vase keys (at azimuth 90 and 270 deg)


def horiz(y, cx=0.0, cz=0.0):
    """Frame for a horizontal plate (XZ plane) whose top face points up. local (x, y) = world (x, -z)."""
    return frame((cx, y + T / 2, cz), X, -Z)


def vase_r(h):
    """Outer radius of the vase at height h (0..84 mm)."""
    pts = [(0, 24.0), (8, 27.5), (24, 30.5), (40, 29.0), (58, 24.0), (68, 23.0), (78, 24.5), (84, 26.5)]
    hs, rs = zip(*pts)
    return float(np.interp(h, hs, rs))


def build():
    k = Kit('floral', 'Blossom Waltz')
    k.tagline = 'A flower music box that turns while it plays.'
    k.story = ('Wind the key and the bouquet starts to dance. Blossom Waltz is a pastel garden in a box: '
               'eight layered flowers in a striped vase turn slowly on a little stage while a real '
               'wind-up movement plays. Every petal is cut from colored wood, with veins drawn by the laser. '
               'Build it in an evening, give it to someone, and watch them wind it again and again.')
    k.difficulty = 3
    k.build_hours = '4 to 5 h'
    k.price = 49.99
    k.extras = {'18-note wind-up music movement with rotating shaft': 1, '3/16 in birch dowel, 55 mm': 1,
                'wax stick': 1, 'sandpaper 240 grit': 1}

    step = [0]

    def nxt(title, **kw):
        step[0] += 1
        k.step(step[0], title, **kw)
        return step[0]

    # ------------------------------------------------------------ feet (discs on a square peg)
    s_feet = nxt('Build the four feet', tip='Push each peg into the bottom square first, then stack the rest.',
                 icons=['x4', 'press'])
    feet_pegs = []
    for i, (fx, fz) in enumerate([(-50, -50), (50, -50), (-50, 50), (50, 50)]):
        peg = Part(f'foot_peg{i}', rect(-3, 0, 3, BASE_TOP), color='natural',
                   mat=frame((fx, 0, fz), X, Y), step=s_feet, insert=DOWN, group='feet')
        feet_pegs.append(peg)
        k.add(peg)
        for j in range(5):
            r = 9.0 - 0.6 * j
            sq = Part(f'foot{i}_{j}', rounded(rect_c(0, 0, 2 * r, 2 * r), 2.5), color='natural' if j % 2 else 'white',
                      mat=horiz(j * T, fx, fz), step=s_feet, insert=DOWN, group='feet')
            pierce(sq, peg, fit='snug')
            k.add(sq)

    # ------------------------------------------------------------ base plate
    s_base = nxt('Add the base plate', tip='The round hole is for the winding key.', icons=['press'])
    base = Part('base', rounded(rect_c(0, 0, BOX, BOX), 8), color='natural', mat=horiz(BASE_Y), step=s_base,
                insert=DOWN)
    for peg in feet_pegs:
        pierce(base, peg, fit='press')
    base.cuts.append((circle(KEY_X, 0, 7.5), 'press'))   # key clearance hole
    k.add(base)

    # ------------------------------------------------------------ movement cradle and movement
    s_cradle = nxt('Build the movement cradle', tip='Four low walls hold the music movement.', icons=['press'])
    mw, md = MOV['w'], MOV['d']
    ch = 14.0
    cradle = []
    for i, zc in enumerate((-(md / 2 + T / 2), md / 2 + T / 2)):
        c = Part(f'cradle_fb{i}', rect(-(mw / 2 + T), BASE_TOP, mw / 2 + T, BASE_TOP + ch), color='natural',
                 mat=frame((0, 0, zc), X, Y), step=s_cradle, insert=DOWN, group='cradle')
        tab_joint(base, c, edge_tabs(-mw / 2, mw / 2, BASE_TOP, -T, n=2, width=10))
        cradle.append(c)
    for i, xc in enumerate((-(mw / 2 + T / 2), mw / 2 + T / 2)):
        c = Part(f'cradle_side{i}', rect(-md / 2, BASE_TOP, md / 2, BASE_TOP + ch), color='natural',
                 mat=frame((xc, 0, 0), -Z, Y), step=s_cradle, insert=DOWN, group='cradle')
        tab_joint(base, c, edge_tabs(-md / 2 + 4, md / 2 - 4, BASE_TOP, -T, n=1, width=12))
        cradle.append(c)
    k.add(*cradle)

    s_mov = nxt('Drop in the music movement', tip='Key side down. The key goes through the round hole.',
                icons=['careful'], test='Wind the key two turns. You should hear music.')
    mov = Block('music movement', (-mw / 2, BASE_TOP, -md / 2), (mw / 2, BASE_TOP + MOV['h'], md / 2),
                step=s_mov, insert=DOWN, note='18-note wind-up movement (bought part)')
    key_rod = Rod('winding key shaft', (KEY_X, BASE_Y - 10, 0), (KEY_X, BASE_TOP, 0), d=5.0, step=s_mov,
                  insert=DOWN, note='part of the movement')
    key_rod.kind = 'rod'; key_rod.color = 'metal'
    spindle_top = BASE_TOP + MOV['h'] + 7.0
    spindle = Rod('movement shaft', (0, BASE_TOP + MOV['h'], 0), (0, spindle_top, 0), d=SPINDLE_D,
                  step=s_mov, insert=DOWN, note='part of the movement')
    spindle.color = 'metal'
    k.add(key_rod, mov, spindle)

    # ------------------------------------------------------------ coupler (discs on two square pegs)
    s_coup = nxt('Build the drive coupler', tip='Two pegs lock the four discs together. Wax the top hole.',
                 icons=['wax', 'press'])
    cy0 = BASE_TOP + MOV['h'] + 1.0
    cpegs = []
    for i, sx in enumerate((1, -1)):
        p = Part(f'coupler_peg{i}', rect(5.2 * sx, cy0, 8.7 * sx, cy0 + 4 * T), color='natural',
                 mat=frame((0, 0, 0), X, Y), step=s_coup, insert=DOWN, group='coupler', mechanism=True)
        cpegs.append(p)
    k.add(*cpegs)
    coupler = []
    for j in range(4):
        d = Part(f'coupler{j}', circle(0, 0, 12), color='natural', mat=horiz(cy0 + j * T), step=s_coup,
                 insert=DOWN, group='coupler', mechanism=True,
                 note='Grip fit on the metal shaft (lower two) and on the dowel (upper two).')
        d.cuts.append((circle(0, 0, (SPINDLE_D if j < 2 else 4.76) / 2), 'grip'))
        for p in cpegs:
            pierce(d, p, fit='snug')
        coupler.append(d)
    k.add(*coupler)

    # ------------------------------------------------------------ walls
    s_walls = nxt('Stand up the front and back walls', tip='Window faces front.', icons=['press'])
    wy0, wy1 = BASE_TOP, TOP_Y
    walls = {}
    for name, zc, col in (('wall_front', BOX / 2 - 3 - T / 2, 'white'), ('wall_back', -(BOX / 2 - 3 - T / 2), 'white')):
        w = Part(name, rect(-(BOX / 2 - 3), wy0, BOX / 2 - 3, wy1), color=col, mat=frame((0, 0, zc), X, Y),
                 step=s_walls, insert=DOWN, group='box')
        tab_joint(base, w, edge_tabs(-48, 48, wy0, -T, n=3, width=12))
        walls[name] = w
    win = S.ellipse(0, wy0 + 30, 22, 14)
    walls['wall_front'].cuts.append((win, 'press'))
    s_sides = nxt('Add the side walls', tip='Their tabs lock into the front and back walls.', icons=['press'])
    inner_z = BOX / 2 - 3 - T
    for name, xc in (('wall_left', -(BOX / 2 - 3 - T - 3 - T / 2)), ('wall_right', BOX / 2 - 3 - T - 3 - T / 2)):
        w = Part(name, rect(-inner_z, wy0, inner_z, wy1), color='pink', mat=frame((xc, 0, 0), -Z if xc > 0 else Z, Y),
                 step=s_sides, insert=DOWN, group='box')
        tab_joint(base, w, edge_tabs(-40, 40, wy0, -T, n=2, width=12))
        walls[name] = w
    k.add(*walls.values())

    # side walls stand inside the front/back walls; check widths
    # ------------------------------------------------------------ overlays on walls (layers on square pegs)
    s_dec = nxt('Decorate the walls', tip='Each picture is held by little square pegs. Push from outside.',
                icons=['press'])

    def overlay(name, shape, wall, color, pegs_at, outward, engrave=None, score=None):
        """Plate lying on the outside face of `wall`, held by pegs that pass through both."""
        wn = wall.mat[:3, 2] * outward
        o = Part(name, shape, color=color, step=s_dec, insert=tuple(-wn), group='decor')
        o.mat = wall.mat.copy()
        o.mat[:3, 3] = wall.mat[:3, 3] + wn * T
        if outward < 0:
            o.flip()
        if engrave:
            o.engrave.extend(engrave)
        if score:
            o.score.extend(score)
        k.add(o)
        for j, (px, py) in enumerate(pegs_at):
            # peg: small plate perpendicular to the wall, through overlay + wall + 3 mm inside
            c_world = wall.mat[:3, 3] + wall.mat[:3, 0] * px + wall.mat[:3, 1] * py
            ax = wall.mat[:3, 0]
            peg = Part(f'{name}_peg{j}', rect(-2.0, -1.5 * T, 2.0, 1.5 * T), color='natural', step=s_dec,
                       insert=tuple(-wn), group='decor')
            peg.mat = frame(c_world, ax, wn)
            pierce(o, peg, fit='snug'); pierce(wall, peg, fit='press')
            k.add(peg)
        return o

    fw = walls['wall_front']
    frame_shape = S.ellipse(0, wy0 + 30, 31, 22).difference(S.ellipse(0, wy0 + 30, 22, 14))
    overlay('window_frame', frame_shape, fw, 'pink', [(-26.5, wy0 + 30), (26.5, wy0 + 30)], 1,
            score=S.clip_lines([LineString([(26.5 * math.cos(a), wy0 + 30 + 18 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 60)])], frame_shape, 0.6))
    # flower emblems on the side walls
    for side in ('wall_left', 'wall_right'):
        w = walls[side]
        petals = S.petal_ring(6, 20, 12, 7, 'round')
        petals = affinity.translate(petals, 0, wy0 + 36)
        ctr = circle(0, wy0 + 36, 7)
        overlay(f'{side}_flower', petals, w, 'yellow', [(0, wy0 + 36)], 1,
                score=S.clip_lines([affinity.translate(l, 0, wy0 + 36) for l in S.petal_veins(6, 8.5, 18.5, side=False)], petals, 0.8))
        leafs = unary_union([affinity.translate(affinity.rotate(S.leaf(30, 12, 2), a, origin=(0, 0)), 0, wy0 + 12)
                             for a in (20, 160)]).buffer(0)
        leafs = leafs.difference(circle(0, wy0 + 36, 21)).buffer(-1.4).buffer(1.4)
        overlay(f'{side}_leaves', leafs, w, 'green', [(-14.1, wy0 + 17.1), (14.1, wy0 + 17.1)], 1)
    bw = walls['wall_back']
    plaque = rounded(rect_c(0, wy0 + 33, 76, 26), 6)
    from hartwood.text import text_outline
    txt, _ = text_outline('HARTWOOD', 6.0, x=0, y=wy0 + 33, anchor='center')
    overlay('back_plaque', plaque, bw, 'pink', [(-30, wy0 + 33), (30, wy0 + 33)], -1,
            engrave=[affinity.translate(txt, 0, -3.0)])

    # ------------------------------------------------------------ top plate
    s_top = nxt('Close the box with the lid', tip='Line up the round bearing hole with the coupler.', icons=['press'])
    top = Part('top', rounded(rect_c(0, 0, BOX, BOX), 8), color='white', mat=horiz(TOP_Y), step=s_top, insert=DOWN)
    for name in ('wall_front', 'wall_back'):
        add_tabs(walls[name], edge_tabs(-48, 48, wy1, T, n=3, width=12))
        for t in walls[name].__dict__['tabs'][-3:]:
            pierce(top, walls[name], t)
    for name in ('wall_left', 'wall_right'):
        add_tabs(walls[name], edge_tabs(-30, 30, wy1, T, n=2, width=12))
        for t in walls[name].__dict__['tabs'][-2:]:
            pierce(top, walls[name], t)
    top.cuts.append((circle(0, 0, 4.76 / 2), 'spin'))      # bearing for the drive dowel
    top.score.extend(S.clip_lines([LineString([(54 * math.cos(a), 54 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 120)])],
                                  top.shape, 1))
    k.add(top)

    # ------------------------------------------------------------ dowel, hub, turntable
    s_tt = nxt('Fit the drive dowel and the turntable', tip='Wax the dowel where it turns in the lid.',
               icons=['wax', 'press'], test='Wind the movement. The turntable should spin smoothly.')
    dowel = Rod('drive dowel', (0, cy0 + 2 * T, 0), (0, VASE_Y, 0), step=s_tt, insert=DOWN, mechanism=True,
                note='3/16 in birch dowel cut to length')
    k.add(dowel)
    hub_y = TOP_Y + T + 1.0
    hpegs = []
    for i, sx in enumerate((1, -1)):
        p = Part(f'hub_peg{i}', rect(5.2 * sx, hub_y, 8.7 * sx, hub_y + 3 * T), color='natural',
                 mat=frame((0, 0, 0), Z, Y), step=s_tt, insert=DOWN, group='turntable', mechanism=True)
        hpegs.append(p)
    k.add(*hpegs)
    for j in range(2):
        d = Part(f'hub{j}', circle(0, 0, 12), color='natural', mat=horiz(hub_y + j * T), step=s_tt, insert=DOWN,
                 group='turntable', mechanism=True)
        d.cuts.append((circle(0, 0, 4.76 / 2), 'grip'))
        for p in hpegs:
            pierce(d, p, fit='snug')
        k.add(d)
    tt = Part('turntable', circle(0, 0, 38), color='pink', mat=horiz(TT_Y), step=s_tt, insert=DOWN,
              group='turntable', mechanism=True)
    tt.cuts.append((circle(0, 0, 4.76 / 2), 'grip'))
    for p in hpegs:
        pierce(tt, p, fit='snug')
    tt.score.extend(S.clip_lines([LineString([(r * math.cos(a), r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 100)])
                                  for r in (35,)], tt.shape, 1))
    for a in range(0, 360, 30):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        tt.score.append(LineString([(25 * ca, 25 * sa), (32 * ca, 32 * sa)]))
    k.add(tt)

    # ------------------------------------------------------------ fence around the turntable
    s_fence = nxt('Plant the garden fence', tip='Eight fence pieces slot into the lid.', icons=['press', 'x8'])
    R_f = 47.0
    seg_len = 2 * R_f * math.tan(math.radians(22.5)) - 9
    fences = []
    for i in range(8):
        a = math.radians(22.5 + 45 * i)
        d = np.array([math.cos(a), 0, math.sin(a)])
        tdir = np.array([-math.sin(a), 0, math.cos(a)])
        pick = [rect(-seg_len / 2, TOP_Y + T, seg_len / 2, TOP_Y + T + 4)]
        n_p = 5
        for j in range(n_p):
            x0 = -seg_len / 2 + 1 + j * (seg_len - 2 - 5) / (n_p - 1)
            pick.append(Polygon([(x0, TOP_Y + T), (x0 + 5, TOP_Y + T), (x0 + 5, TOP_Y + T + 12), (x0 + 2.5, TOP_Y + T + 15),
                                 (x0, TOP_Y + T + 12)]))
        pick.append(rect(-seg_len / 2, TOP_Y + T + 7, seg_len / 2, TOP_Y + T + 10))
        f = Part(f'fence{i}', unary_union(pick).buffer(0), color='white', mat=frame(d * R_f, tdir, Y),
                 step=s_fence, insert=DOWN, group='fence')
        tab_joint(top, f, [rect(-4, TOP_Y + T, 4, TOP_Y)])
        fences.append(f)
    k.add(*fences)

    # ------------------------------------------------------------ vase: rings on two keys
    s_keys = nxt('Stand the two vase keys in the turntable', tip='They are the backbone of the vase.',
                 icons=['press'])
    vkeys = []
    for i, az in enumerate((90, 270)):
        a = math.radians(az)
        d = np.array([math.cos(a), 0, math.sin(a)])
        vk = Part(f'vase_key{i}', rect(KEY_R[0], VASE_Y, KEY_R[1], VASE_Y + N_RINGS * T), color='natural',
                  mat=frame((0, 0, 0), d, Y), step=s_keys, insert=DOWN, group='vase')
        tab_joint(tt, vk, [rect(KEY_R[0] + 1, VASE_Y, KEY_R[1] - 1, VASE_Y - T)])
        vkeys.append(vk)
    k.add(*vkeys)
    ring_colors = ['white', 'teal', 'white', 'pink']
    stems_az = [22.5 + 45 * i for i in range(8)]
    FROG, GUIDE = N_RINGS - 1, N_RINGS - 9
    rings = []
    groups = [(0, 7), (7, 14), (14, 21), (21, N_RINGS)]
    s_rings = []
    for gi, (a0, a1) in enumerate(groups):
        s_rings.append(nxt(f'Stack vase rings {a0 + 1} to {a1}', tip='Slide each ring down both keys. Watch the colors.',
                           icons=['press']))
    for i in range(N_RINGS):
        h = i * T + T / 2
        r = vase_r(h)
        gi = next(g for g, (a0, a1) in enumerate(groups) if a0 <= i < a1)
        if i in (FROG, GUIDE):
            shape = circle(0, 0, r)
            col = 'green' if i == FROG else 'white'
        else:
            shape = circle(0, 0, r).difference(circle(0, 0, RING_IN))
            col = ring_colors[i % len(ring_colors)]
        ring = Part(f'ring{i:02d}' if i not in (FROG, GUIDE) else ('frog' if i == FROG else 'guide'), shape,
                    color=col, mat=horiz(VASE_Y + i * T), step=s_rings[gi], insert=DOWN, group='vase')
        for vk in vkeys:
            pierce(ring, vk, fit='snug')
        rings.append(ring)
        k.add(ring)
    # vase surface detail: score a band on the belly rings? (rings are edge-on; detail lives on the frog)
    rings[FROG].score.extend(S.clip_lines([LineString([(r * math.cos(a), r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 80)])
                                           for r in (20.5,)], rings[FROG].shape, 1))

    # ------------------------------------------------------------ flowers
    specs = [
        # name, az index, head radius (horizontal distance), head height above vase top, tilt deg, kind
        ('rose', 0, 46, 60, 38, 'rose'),
        ('daisy', 1, 56, 44, 56, 'daisy'),
        ('lavender1', 2, 30, 72, 18, 'lavender'),
        ('tulip', 3, 38, 66, 30, 'tulip'),
        ('sunflower', 4, 58, 52, 58, 'sunflower'),
        ('lavender2', 5, 34, 58, 22, 'lavender'),
        ('rosebud', 6, 46, 40, 50, 'rose_small'),
        ('cornflower', 7, 50, 70, 40, 'cornflower'),
    ]
    vase_top = VASE_Y + N_RINGS * T
    for (name, ai, R_head, H_head, tilt, kind) in specs:
        az = stems_az[ai]
        a = math.radians(az)
        d = np.array([math.cos(a), 0, math.sin(a)])
        s_f = nxt(f'Build and plant the {name.rstrip("12").replace("rose_small", "rosebud")}',
                  tip='Stem first, then leaves, then stack the petals from big to small.', icons=['press'])
        stem_outline, head_frame, peg_poly, leaf_pts, veins = _stem(R_head, vase_top, H_head, tilt, kind)
        stem = Part(f'{name}_stem', stem_outline, color='green', mat=frame((0, 0, 0), d, Y), step=s_f,
                    insert=DOWN, group=name)
        stem.score.extend(veins)
        # the stem passes through frog and guide discs
        lower = rect(7.5, VASE_Y + GUIDE * T - 1, 12.5, vase_top)
        pierce(rings[FROG], stem, lower, fit='press')
        pierce(rings[GUIDE], stem, lower, fit='press')
        k.add(stem)
        # leaves (cross half-lap)
        for li, (lx, ly, across, size) in enumerate(leaf_pts):
            leaf = _leaf_pair(f'{name}_leaf{li}', stem, lx, ly, across, size, s_f)
            k.add(leaf)
        # head discs along the peg
        hp, e = head_frame
        layers = _head_layers(kind)
        n_ax = stem.mat[:3, 2]
        e_w = stem.mat[:3, :3] @ np.array([e[0], e[1], 0.0])
        hp_w = stem.mat[:3, :3] @ np.array([hp[0], hp[1], 0.0]) + stem.mat[:3, 3]
        for j, (shape, col, score, eng) in enumerate(layers):
            v = np.cross(e_w, n_ax)
            m = frame(hp_w + e_w * (j * T + T / 2), n_ax, v)
            dpart = Part(f'{name}_head{j}', shape, color=col, mat=m, step=s_f, insert=tuple(-e_w), group=name,
                         explode=30)
            dpart.score.extend(score)
            dpart.engrave.extend(eng)
            pierce(dpart, stem, peg_poly, fit='snug')
            k.add(dpart)

    # ------------------------------------------------------------ butterflies on the lid corners
    s_bf = nxt('Let the butterflies land', tip='Push each body into the lid, then slide the wings down.',
               icons=['press'])
    for bi, az in enumerate((45, 225)):
        a = math.radians(az)
        d = np.array([math.cos(a), 0, math.sin(a)]); tdir = np.array([-math.sin(a), 0, math.cos(a)])
        base_pt = d * 72.0 + Y * (TOP_Y + T)
        body_shape = unary_union([rect(-2.5, 0, 2.5, 16), circle(0, 17, 3.2), rect(-4, -T, 4, 0)]).buffer(0)
        body = Part(f'butterfly{bi}_body', body_shape, color='natural', mat=frame(base_pt, d, Y), step=s_bf,
                    insert=DOWN, group='butterfly', explode=25)
        pierce(top, body, rect(-4, -T, 4, 0), fit='press')
        k.add(body)
        up = (0.35 * d + Y); up = up / np.linalg.norm(up)
        wings = unary_union([S.ellipse(9, 4, 8, 6, 25), S.ellipse(-9, 4, 8, 6, -25), S.ellipse(7, -4, 5, 4, -20),
                             S.ellipse(-7, -4, 5, 4, 20), rect(-4.6, -8, 4.6, 8)]).buffer(0.8).buffer(-0.8)
        wing = Part(f'butterfly{bi}_wings', wings, color='purple' if bi == 0 else 'teal',
                    mat=frame(base_pt + Y * 9.0 + d * 1.5, tdir, up), step=s_bf, insert=tuple(-up),
                    group='butterfly', explode=25)
        wing.score.extend(S.clip_lines([S.ellipse(9, 4, 4.5, 3, 25).exterior, S.ellipse(-9, 4, 4.5, 3, -25).exterior], wings, 0.6))
        cross_halflap(wing, body, a_from_start=True, fit='snug')
        dline = np.cross(wing.mat[:3, 2], body.mat[:3, 2]); dline /= np.linalg.norm(dline)
        wing.insert = tuple(-dline)
        k.add(wing)
    # show faces: codes go on the sheet beside the part, not on the part
    hidden = ('foot', 'base', 'cradle', 'coupler', 'hub', 'vase_key', 'ring', 'guide', '_peg')
    for p in k.parts:
        if not any(h in p.name for h in hidden):
            p.code_on_part = False
    return k


# ---------------------------------------------------------------- flower helpers
def _stem(R_head, vase_top, H_head, tilt_deg, kind):
    """Stem plate outline in its radial plane (local x = radial distance, y = world height).

    Returns outline, (head point, head direction) in local 2D, peg polygon, half-lap leaf anchors,
    and score lines (veins of the leaf that is part of the stem plate)."""
    y_top = vase_top
    bottom = 7.5, 12.5
    # centre line: vertical through the frog, then a smooth curve out to the head
    p0 = np.array([10.0, y_top])
    p3 = np.array([R_head, y_top + H_head])
    tilt = math.radians(tilt_deg)
    e = np.array([math.sin(tilt), math.cos(tilt)])          # head direction (outward + up)
    p1 = p0 + np.array([0, H_head * 0.45])
    p2 = p3 - e * (H_head * 0.35)
    ts = np.linspace(0, 1, 60)
    curve = np.array([(1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3 for t in ts])
    w_stem = 5.0
    body = LineString(curve).buffer(w_stem / 2, cap_style='flat', join_style='round')
    lower = rect(bottom[0], y_top - 30, bottom[1], y_top + 1)
    shoulder = rect(7.0, y_top, 13.5, y_top + 4.0)
    n_layers = len(_head_layers(kind))
    peg_len = n_layers * T
    perp = np.array([-e[1], e[0]])
    c0 = p3
    peg = Polygon([c0 - perp * 3, c0 + perp * 3, c0 + perp * 3 + e * peg_len, c0 - perp * 3 + e * peg_len])
    collar = Polygon([c0 - perp * 4.5 - e * 4, c0 + perp * 4.5 - e * 4, c0 + perp * 4.5, c0 - perp * 4.5])
    parts = [body, lower, shoulder, collar]
    # one leaf in the stem plane (no joint needed), on the outer side
    i_leaf = int(0.30 * (len(curve) - 1))
    tng = curve[i_leaf + 1] - curve[i_leaf - 1]; tng /= np.linalg.norm(tng)
    ang = math.degrees(math.atan2(tng[1], tng[0])) - 50
    lf = affinity.translate(affinity.rotate(S.leaf(20, 8.5, 1.2), ang, origin=(0, 0)), *curve[i_leaf])
    parts.append(lf)
    veins = [affinity.translate(affinity.rotate(v, ang, origin=(0, 0)), *curve[i_leaf]) for v in S.leaf_veins(20, 8.5, 1.2, 3)]
    # half-lap leaf pair anchor: bulge on the stem
    leaf_pts = []
    if kind != 'lavender':
        i = int(0.70 * (len(curve) - 1))
        tng = curve[i + 1] - curve[i - 1]; tng /= np.linalg.norm(tng)
        across = np.array([tng[1], -tng[0]])
        parts.append(circle(curve[i][0], curve[i][1], 4.6))
        leaf_pts.append((curve[i][0], curve[i][1], across, 1.0))
    outline = unary_union(parts).buffer(0.4).buffer(-0.4)
    # nothing of the stem may poke past the collar except the peg
    beyond = Polygon([c0 - perp * 60, c0 + perp * 60, c0 + perp * 60 + e * 80, c0 - perp * 60 + e * 80])
    outline = outline.difference(beyond).union(peg).buffer(0)
    peg_only = Polygon([c0 - perp * 3 + e * 0.05, c0 + perp * 3 + e * 0.05, c0 + perp * 3 + e * (peg_len + 0.5),
                        c0 - perp * 3 + e * (peg_len + 0.5)])
    veins = S.clip_lines(veins, lf.difference(body.buffer(1.0)), 0.8)
    return outline, (c0, e), peg_only, leaf_pts, veins


def _leaf_pair(name, stem, lx, ly, across2d, size, step):
    """Two leaves on one plate, square to the stem, crossing it with a half-lap at (lx, ly)."""
    n = stem.mat[:3, 2]
    p = stem.mat[:3, :3] @ np.array([lx, ly, 0.0]) + stem.mat[:3, 3]
    across = stem.mat[:3, :3] @ np.array([across2d[0], across2d[1], 0.0])
    L, W = 16 * size, 9 * size
    shape = unary_union([S.leaf(L, W, 1.2), affinity.rotate(S.leaf(L, W, 1.2), 180, origin=(0, 0)),
                         rect(-4.6, -6, 4.6, 6)]).buffer(0.6).buffer(-0.6)
    leaf = Part(name, shape, color='green', mat=frame(p, n, across), step=step, group=stem.group, explode=25)
    vs = S.leaf_veins(L, W, 1.2, 3) + [affinity.rotate(v, 180, origin=(0, 0)) for v in S.leaf_veins(L, W, 1.2, 3)]
    leaf.score = S.clip_lines(vs, shape.difference(rect(-5, -7, 5, 7)), 0.8)
    cross_halflap(leaf, stem, a_from_start=True, fit='snug')
    dline = np.cross(leaf.mat[:3, 2], stem.mat[:3, 2]); dline /= np.linalg.norm(dline)
    leaf.insert = tuple(-dline)
    return leaf


def _head_layers(kind):
    """List of (shape, color, score lines, engrave polys) from the stem collar outward."""
    L = []
    if kind in ('rose', 'rose_small'):
        radii = [20, 17, 14, 11, 8] if kind == 'rose' else [16, 13, 10, 7]
        L.append((S.regular_star(0, 0, radii[0] - 1, radii[0] * 0.55, 5, 18).buffer(1.2).buffer(-0.6), 'green', [], []))
        for i, r in enumerate(radii):
            sh = S.scalloped(r, 5, r * 0.32, rot=36 * i + 18)
            col = 'pink' if i % 2 == 0 else 'white'
            if kind == 'rose_small':
                col = 'pink' if i % 2 else 'white'
            sc = [] if r < 9 else S.clip_lines([LineString([(r * 0.5 * math.cos(a), r * 0.5 * math.sin(a)),
                                                            (r * 0.85 * math.cos(a + 0.25), r * 0.85 * math.sin(a + 0.25))])
                                                for a in np.radians(np.arange(5) * 72 + 36 * i + 18)], sh, 0.8)
            L.append((sh, col, sc, []))
        L.append((circle(0, 0, 5.6), 'pink', [], []))
    elif kind == 'daisy':
        for i in range(2):
            sh = S.petal_ring(14, 22, 6.0, 7, 'round', rot=i * 12.86)
            L.append((sh, 'white', S.clip_lines([l for l in S.petal_veins(14, 9, 20, rot=i * 12.86, side=False)], sh, 0.8), []))
        L.append((circle(0, 0, 8), 'yellow', [], []))
        L.append((circle(0, 0, 6), 'yellow', [], [circle(2.5 * math.cos(a), 2.5 * math.sin(a), 0.7) for a in np.linspace(0, 6.28, 7)[:-1]]))
    elif kind == 'tulip':
        L.append((S.petal_ring(3, 20, 15, 6, 'pointed', rot=90), 'purple', S.clip_lines(S.petal_veins(3, 7, 18, rot=90), S.petal_ring(3, 20, 15, 6, 'pointed', rot=90), 0.8), []))
        L.append((S.petal_ring(3, 17, 13, 6, 'pointed', rot=30), 'pink', S.clip_lines(S.petal_veins(3, 7, 15, rot=30), S.petal_ring(3, 17, 13, 6, 'pointed', rot=30), 0.8), []))
        L.append((S.petal_ring(3, 12, 10, 6, 'pointed', rot=90), 'purple', [], []))
        L.append((circle(0, 0, 6), 'yellow', [], []))
    elif kind == 'sunflower':
        for i in range(2):
            sh = S.petal_ring(16, 27, 7, 10, 'pointed', rot=i * 11.25)
            L.append((sh, 'yellow', S.clip_lines(S.petal_veins(16, 12, 25, rot=i * 11.25, side=False), sh, 0.8), []))
        L.append((circle(0, 0, 12), 'natural', [], []))
        seeds = []
        for j in range(60):
            rr = 1.4 * math.sqrt(j) + 1.0
            if rr > 7.4:
                break
            a = j * 2.39996
            seeds.append(circle(rr * math.cos(a), rr * math.sin(a), 0.55, 8))
        L.append((circle(0, 0, 9), 'natural', [], seeds))
    elif kind == 'cornflower':
        for i in range(2):
            sh = S.petal_ring(8, 18, 8.5, 6, 'heart', rot=i * 22.5)
            L.append((sh, 'teal', S.clip_lines(S.petal_veins(8, 7, 16, rot=i * 22.5, side=False), sh, 0.8), []))
        L.append((S.regular_star(0, 0, 7, 4, 8), 'purple', [], []))
        L.append((circle(0, 0, 5.6), 'purple', [], []))
    elif kind == 'lavender':
        # a spike of small buds (discs) on the peg
        for i, r in enumerate([9, 8.5, 8, 7.5, 7]):
            L.append((S.scalloped(r, 6, 1.2, rot=30 * i), 'purple', [], []))
    return L
