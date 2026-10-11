"""A small test assembly that uses every joint type. Used to prove the checks work."""
import numpy as np

from hartwood.geom import Kit, Part, Rod, T, frame, rect, circle, rect_c
from hartwood.joints import edge_tabs, tab_joint, pierce, cross_halflap

X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)


def build():
    k = Kit('proofbox', 'Proof Box')
    # floor in the XZ plane, top face up (+Y): u = X, v = -Z  -> normal = X x -Z = +Y
    floor = Part('floor', rect(-50, -30, 50, 30), mat=frame((0, T / 2, 0), X, (0, 0, -1)), step=1)
    # two walls standing on the floor, in the XY plane at z = +-24
    walls = []
    for i, z in enumerate((-24.0, 24.0)):
        w = Part(f'wall{i}', rect(-50, T, 50, 50), mat=frame((0, 0, z), X, Y), step=2,
                 insert=(0, -1, 0))
        tab_joint(floor, w, edge_tabs(-40, 40, T, -T, n=3), fit='press')
        walls.append(w)
    # a dowel axle through both walls, a wheel turning on it between them
    axle = Rod('axle', (-20, 35, -27.5), (-20, 35, 27.5), step=4, insert=(0, 0, -1))
    hub = Part('wheel', circle(0, 0, 12), mat=frame((-20, 35, 0), X, Y), step=3, insert=(0, -1, 0),
               mechanism=True)
    for w in walls:
        w.cuts.append((circle(-20, 35, axle.d / 2), 'spin'))
    hub.cuts.append((circle(0, 0, axle.d / 2), 'spin'))
    # spacers keep the wheel centred: two discs on the axle each side
    spacers = []
    for i, z in enumerate([-21, -18, -15, -12, -9, -6, -3, 3, 6, 9, 12, 15, 18, 21]):
        s = Part(f'spacer{i}', circle(0, 0, 6), mat=frame((-20, 35, z), X, Y), step=3, insert=(0, -1, 0))
        s.cuts.append((circle(0, 0, axle.d / 2), 'spin'))
        spacers.append(s)
    # stacked slices on a key plate (key stands on the floor in the YZ plane)
    zc = -12.0
    key = Part('key', rect(zc - 3, T, zc + 3, 40), mat=frame((25, 0, 0), (0, 0, 1), Y), step=3, insert=(0, -1, 0))
    tab_joint(floor, key, [rect(zc - 2, T, zc + 2, 0)], fit='press')
    slices = []
    for i in range(4):
        y = 12 + i * T
        sl = Part(f'slice{i}', rect_c(0, 0, 30 - 4 * i, 16), mat=frame((25, y + T / 2, zc), X, (0, 0, -1)),
                  step=3 + 0, insert=(0, -1, 0))
        pierce(sl, key, fit='snug')
        slices.append(sl)
    # slices need support: bottom slice rests on a ledge block made of a cross half-lap pair
    a = Part('lap_a', rect(-6, T, 6, 12), mat=frame((35, 0, zc), X, Y), step=3, insert=(0, -1, 0))
    b = Part('lap_b', rect(-6, T, 6, 12), mat=frame((35, 0, zc), (0, 0, 1), Y), step=3, insert=(0, -1, 0))
    cross_halflap(a, b, a_from_start=True)
    tab_joint(floor, a, [rect(-4, T, 4, 0)])
    k.add(floor, *walls, hub, *spacers, axle, key, a, b, *slices)
    return k
