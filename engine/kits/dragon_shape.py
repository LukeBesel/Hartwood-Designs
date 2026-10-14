"""3D shape of the Emberwing dragon as an implicit function, sliced into 3 mm layers.

The body is a union of elliptical tubes along a spine curve (tail -> body -> neck -> skull), plus legs,
horns, brow and snout. `slice_at(z)` returns the 2D region (world XY) of the dragon in the plane z.
Pose: rearing on top of a ruined tower, front claws on the parapet, tail curled down the back wall.
"""
from __future__ import annotations

import numpy as np

from hartwood import shapes as S

TOP = 78.0          # tower top surface (y) where the hind feet stand
PARAPET = TOP + 14  # top of the front merlons the front claws grip


def bezier(pts, n=60):
    pts = np.asarray(pts, float)
    out = []
    for i in range(0, len(pts) - 1, 3):
        p0, p1, p2, p3 = pts[i:i + 4]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)
    out.append(pts[-1])
    return np.array(out)


def resample(curve, step=1.0):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(curve, axis=0), axis=1))]
    s = np.arange(0, d[-1], step)
    return np.column_stack([np.interp(s, d, curve[:, i]) for i in range(curve.shape[1])]), s / d[-1]


# spine in the side view (x forward, y up); one curve from tail tip to the back of the skull
SPINE = bezier([
    (-102, TOP - 50), (-122, TOP - 34), (-122, TOP - 2), (-100, TOP + 12),     # tail curl down the back wall
    (-80, TOP + 26), (-58, TOP + 36), (-34, TOP + 42),                         # tail base -> hips
    (-8, TOP + 48), (16, TOP + 58), (34, TOP + 70),                            # back rising to the shoulders
    (48, TOP + 80), (48, TOP + 100), (56, TOP + 116),                          # neck, first bend
    (64, TOP + 130), (78, TOP + 140), (92, TOP + 138),                         # neck, second bend to skull
])
CURVE, T_PARAM = resample(SPINE, 1.0)
PROF_T = [0.00, 0.06, 0.16, 0.27, 0.36, 0.45, 0.53, 0.60, 0.66, 0.74, 0.84, 0.93, 1.00]
PROF_RY = [2.2, 3.6, 6.5, 10.5, 16.0, 22.0, 24.5, 22.0, 17.0, 14.0, 12.5, 12.5, 12.0]
PROF_RZ = [2.2, 3.4, 5.8, 9.5, 16.0, 23.5, 25.0, 21.0, 14.0, 11.0, 10.0, 10.5, 10.5]
RY = np.interp(T_PARAM, PROF_T, PROF_RY)
RZ = np.interp(T_PARAM, PROF_T, PROF_RZ)


def _poly3(points, step=1.0):
    P = np.array([p[:3] for p in points], float)
    R = np.array([p[3:5] if len(p) > 4 else (p[3], p[3]) for p in points], float)
    out = []
    for i in range(len(P) - 1):
        L = np.linalg.norm(P[i + 1] - P[i])
        n = max(2, int(L / step))
        for t in np.linspace(0, 1, n, endpoint=False):
            p = P[i] + t * (P[i + 1] - P[i]); r = R[i] + t * (R[i + 1] - R[i])
            out.append((p[0], p[1], p[2], r[0], r[1]))
    out.append((*P[-1], *R[-1]))
    return out


TUBES = []      # (x, y, z, ry, rz) samples
for (x, y), ry, rz in zip(CURVE, RY, RZ):
    TUBES.append((x, y, 0.0, ry, rz))
for side in (1, -1):
    # hind leg: big thigh, knee forward, shin back, foot flat on the tower top
    TUBES += _poly3([(-30, TOP + 40, 14 * side, 15), (-8, TOP + 26, 22 * side, 11), (-26, TOP + 12, 23 * side, 7),
                     (-24, TOP + 5.0, 23 * side, 5.2), (-10, TOP + 4.6, 23 * side, 4.8)])
    # front leg: shoulder, elbow, forearm to the parapet, claws over the merlon top
    TUBES += _poly3([(34, TOP + 58, 13 * side, 11), (52, TOP + 42, 19 * side, 8), (62, TOP + 26, 20 * side, 6.0),
                     (64, PARAPET + 4.5, 20 * side, 5.0), (72, PARAPET + 4.0, 20 * side, 4.4)])
    # horns sweeping back and up from the brow
    TUBES += _poly3([(84, TOP + 146, 6 * side, 4.4), (72, TOP + 156, 8 * side, 3.6), (58, TOP + 162, 9 * side, 2.8),
                     (48, TOP + 160, 9 * side, 2.0)])
    # brow ridge over the eye
    TUBES += _poly3([(86, TOP + 145, 7.5 * side, 3.2), (100, TOP + 141, 6.5 * side, 2.6)])
# snout: tapered, slightly down-turned
TUBES += _poly3([(92, TOP + 138, 0, 12.5, 11.0), (106, TOP + 134, 0, 9.5, 8.8), (122, TOP + 128, 0, 7.0, 6.8),
                 (130, TOP + 125, 0, 5.5, 5.6)])
TUBES = np.array(TUBES)

BOUNDS = (-140, TOP - 72, 145, TOP + 172)
RES = 0.8


def _grid(res=RES):
    xs = np.arange(BOUNDS[0], BOUNDS[2] + res, res)
    ys = np.arange(BOUNDS[1], BOUNDS[3] + res, res)
    return xs, ys


def field_plane(z, res=RES):
    """Implicit field on the grid of the plane z (values < 0 inside)."""
    xs, ys = _grid(res)
    F = np.full((len(ys), len(xs)), 1e3)
    for x, y, zc, ry, rz in TUBES:
        dz2 = (z - zc) ** 2 / rz ** 2
        if dz2 >= 1.0:
            continue
        r = max(ry, rz)
        i0 = max(0, int((x - r - BOUNDS[0]) / res) - 1); i1 = min(len(xs), int((x + r - BOUNDS[0]) / res) + 2)
        j0 = max(0, int((y - r - BOUNDS[1]) / res) - 1); j1 = min(len(ys), int((y + r - BOUNDS[1]) / res) + 2)
        X = xs[i0:i1][None, :]; Y = ys[j0:j1][:, None]
        d = (np.sqrt(((X - x) ** 2 + (Y - y) ** 2) / ry ** 2 + dz2) - 1.0) * min(ry, rz)
        F[j0:j1, i0:i1] = np.minimum(F[j0:j1, i0:i1], d)
    return xs, ys, F


def slice_at(z, res=RES):
    import contourpy
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    xs, ys, F = field_plane(z, res)
    if F.min() >= 0:
        return Polygon()
    gen = contourpy.contour_generator(xs, ys, F, fill_type=contourpy.FillType.OuterOffset)
    filled, offsets = gen.filled(-1e9, 0.0)
    polys = []
    for pts, offs in zip(filled, offsets):
        rings = [pts[offs[i]:offs[i + 1]] for i in range(len(offs) - 1)]
        if len(rings[0]) < 4:
            continue
        p = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0)
        if p.area > 1:
            polys.append(p)
    return unary_union(polys) if polys else Polygon()
