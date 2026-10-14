"""Glue-free joints, computed from the 3D placement so holes always match their tabs.

Four joint types (all a kit needs):
1. tab into square hole      -> add_tabs(B, tabs) then pierce(A, B, tabs)
2. cross half-lap            -> cross_halflap(A, B)
3. slices on a key plate     -> pierce(slice, key) for every slice
4. layered discs on a peg    -> pierce(disc, peg) for every disc

`pierce` computes the exact footprint of (B prism ∩ A slab) projected onto A's plane, so a tab
that enters at an angle gets a correctly stretched and rotated hole. Square holes and the tab
that goes through them therefore always share the same rotation.
"""
from __future__ import annotations

import numpy as np
import shapely
from shapely.geometry import MultiPoint, Polygon
from shapely.ops import unary_union

from .geom import T, Part, apply, rect

EPS = 1e-6


def _convex_pieces(g):
    """Split a polygon into convex pieces (triangles) for exact footprinting."""
    if isinstance(g, Polygon) and g.equals(g.convex_hull):
        return [g]
    tris = shapely.constrained_delaunay_triangles(g)
    return [t for t in tris.geoms if t.area > 1e-6]


def _footprint_convex(piece_b: Polygon, M: np.ndarray, tA: float, tB: float):
    """piece_b: convex polygon in B-local. M maps B-local -> A-local. Returns A-local 2D polygon or None."""
    xy = np.array(piece_b.exterior.coords[:-1])
    n = len(xy)
    lo = np.column_stack([xy, np.full(n, -tB / 2)])
    hi = np.column_stack([xy, np.full(n, tB / 2)])
    L, H = apply(M, lo), apply(M, hi)
    verts = list(L) + list(H)
    edges = [(L[i], L[(i + 1) % n]) for i in range(n)] + [(H[i], H[(i + 1) % n]) for i in range(n)] + \
            [(L[i], H[i]) for i in range(n)]
    z0, z1 = -tA / 2, tA / 2
    keep = [v for v in verts if z0 - EPS <= v[2] <= z1 + EPS]
    for a, b in edges:
        for zc in (z0, z1):
            da, db = a[2] - zc, b[2] - zc
            if (da < -EPS and db > EPS) or (da > EPS and db < -EPS):
                t = da / (da - db)
                keep.append(a + t * (b - a))
    # cap faces may lie entirely inside the slab when the plates are parallel: handled by verts.
    # Also the slab planes may cut the prism interior without edges crossing (prism thicker than slab
    # and parallel): then cap vertices are outside but the cross-section is the cap polygon itself.
    if len(keep) < 3:
        zs = np.concatenate([L[:, 2], H[:, 2]])
        if zs.min() < z0 and zs.max() > z1:
            # parallel case: use projection of the whole cap
            keep = list(L)
        else:
            return None
    pts = np.array(keep)[:, :2]
    hull = MultiPoint([tuple(p) for p in pts]).convex_hull
    if not isinstance(hull, Polygon) or hull.area < 1e-6:
        return None
    return hull


def footprint(A: Part, B: Part, region=None):
    """Exact footprint (A-local polygon) of B's solid (or a region of B) where it passes through A."""
    region = B.shape if region is None else region
    M = np.linalg.inv(A.mat) @ B.mat
    pieces = []
    for g in getattr(region, 'geoms', [region]):
        for cp in _convex_pieces(g):
            f = _footprint_convex(cp, M, T, T)
            if f is not None:
                pieces.append(f)
    if not pieces:
        return None
    return unary_union(pieces).buffer(0)


def pierce(A: Part, B: Part, region=None, fit='press', clip=True):
    """Cut a hole in A wherever B (or region of B) passes through it. Returns the hole polygon."""
    fp = footprint(A, B, region)
    if fp is None or fp.area < 0.01:
        raise ValueError(f'pierce: {B.name} does not pass through {A.name}')
    A.cuts.append((fp, fit))
    return fp


def add_tabs(B: Part, tabs):
    """Union tab rectangles (B-local) onto B's outline."""
    tabs = tabs if isinstance(tabs, (list, tuple)) else [tabs]
    B.shape = unary_union([B.shape] + list(tabs)).buffer(0)
    B.__dict__.setdefault('tabs', []).extend(tabs)   # no micro-bridges on mating faces
    return tabs


def tab_joint(A: Part, B: Part, tabs, fit='press'):
    """B gets tabs (B-local rectangles reaching through A); A gets matching holes."""
    add_tabs(B, tabs)
    holes = []
    for t in (tabs if isinstance(tabs, (list, tuple)) else [tabs]):
        holes.append(pierce(A, B, t, fit))
    return holes


def edge_tabs(x0, x1, y_edge, depth, n=2, width=None, direction=1, inset=None):
    """Rectangles along a horizontal edge of B (B-local), pointing up (direction=+1) or down (-1).

    depth is how far the tab sticks out (normally the thickness of the part it enters).
    """
    L = x1 - x0
    width = width or min(12.0, max(5.0, L / (2 * n + 1)))
    inset = inset if inset is not None else (L - n * width) / (n + 1)
    tabs = []
    if n == 1:
        cx = (x0 + x1) / 2
        tabs.append(rect(cx - width / 2, y_edge, cx + width / 2, y_edge + direction * depth))
        return tabs
    step = (L - 2 * inset - width) / (n - 1) if n > 1 else 0
    for i in range(n):
        a = x0 + inset + i * step
        tabs.append(rect(a, y_edge, a + width, y_edge + direction * depth))
    return tabs


def cross_halflap(A: Part, B: Part, a_from_start=True, fit='press', a_open=None):
    """Two crossing plates, each slotted halfway. A's slot opens toward the start of the overlap
    (along the intersection line direction n_A x n_B), B's toward the end. Swap with a_from_start=False.
    a_open: optional world vector; A's slot then opens toward that side (overrides a_from_start).
    Stores A.lap_insert: the direction A travels to slide on (B placed first).
    """
    nA = A.mat[:3, 2]; nB = B.mat[:3, 2]
    d = np.cross(nA, nB)
    s = np.linalg.norm(d)
    if s < 1e-6:
        raise ValueError('cross_halflap: plates are parallel')
    d /= s
    if a_open is not None:
        a_from_start = float(np.dot(d, a_open)) < 0
    # a point on both mid-planes
    pA, pB = A.mat[:3, 3], B.mat[:3, 3]
    Mx = np.array([nA, nB, d])
    rhs = np.array([nA @ pA, nB @ pB, d @ pA])
    p0 = np.linalg.solve(Mx, rhs)
    ts = np.linspace(-600, 600, 12001)
    cos_a = abs(float(nA @ nB))
    # strip of the other slab as seen in each plate's plane. For an oblique crossing the slab
    # projects wider than T: w = (T + T * |cos a|) / sin a  (a = angle between the plates)
    w = (T + T * cos_a) / s

    def inside(P: Part):
        """True where the strip (width w around the line, in P's plane) touches P's shape."""
        uP = np.cross(P.mat[:3, 2], d)
        uP /= np.linalg.norm(uP)
        inv = np.linalg.inv(P.mat)
        acc = np.zeros(len(ts), bool)
        for o in np.linspace(-w / 2, w / 2, 7):
            pts = p0 + np.outer(ts, d) + uP * o
            loc = apply(inv, pts)
            acc |= shapely.contains_xy(P.shape, loc[:, 0], loc[:, 1])
        return acc

    def on_line(P: Part):
        loc = apply(np.linalg.inv(P.mat), p0 + np.outer(ts, d))
        return shapely.contains_xy(P.shape, loc[:, 0], loc[:, 1])

    both = on_line(A) & on_line(B)
    if not both.any():
        raise ValueError(f'cross_halflap: {A.name} and {B.name} do not cross')
    idx = np.nonzero(both)[0]
    # longest contiguous run
    runs, start = [], idx[0]
    for i, j in zip(idx[:-1], idx[1:]):
        if j != i + 1:
            runs.append((start, i)); start = j
    runs.append((start, idx[-1]))
    i0, i1 = max(runs, key=lambda r: r[1] - r[0])
    t0, t1 = ts[i0], ts[i1]
    tm = (t0 + t1) / 2

    def run_ends(mask):
        lo = i0
        while lo > 0 and mask[lo - 1]:
            lo -= 1
        hi = i1
        while hi < len(mask) - 1 and mask[hi + 1]:
            hi += 1
        return ts[lo] - 1.0, ts[hi] + 1.0

    a_lo, a_hi = run_ends(inside(A))
    b_lo, b_hi = run_ends(inside(B))
    a_rng = (a_lo, tm) if a_from_start else (tm, a_hi)
    b_rng = (tm, b_hi) if a_from_start else (b_lo, tm)
    for P, (ta, tb) in ((A, a_rng), (B, b_rng)):
        inv = np.linalg.inv(P.mat)
        c0 = apply(inv, [p0 + d * ta])[0][:2]
        c1 = apply(inv, [p0 + d * tb])[0][:2]
        ldir = (c1 - c0) / np.linalg.norm(c1 - c0)
        half = (w / 2) * np.array([-ldir[1], ldir[0]])
        slot = Polygon([c0 + half, c1 + half, c1 - half, c0 - half])
        P.cuts.append((slot, fit))
    # direction A must travel to slide on (open end of its slot first); callers may use it as A.insert
    A.__dict__['lap_insert'] = tuple(-d if a_from_start else d)
    return tm


def square_peg_hole(A: Part, peg: Part, fit='snug'):
    """Alias for slices or discs threaded on a square peg / key plate."""
    return pierce(A, peg, None, fit)
