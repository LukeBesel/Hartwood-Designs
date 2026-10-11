"""Core geometry: flat parts (2D polygon + 4x4 placement), hardware solids, kits.

Conventions
- World is Y-up (same as three.js / glTF). Units are millimetres.
- A part is a flat 2D outline in its local (x, y) plane, extruded THICK along local z,
  centred on z = 0 (so it occupies -T/2 .. +T/2). Local +z is the laser side: engraving lands there.
- `mat` maps local (x, y, z, 1) to world.
- The model is NOMINAL: a slot is exactly as wide as the tab that goes in it. Fit allowances
  (press, slip, spin...) are applied only when cut files are written (see cutfiles.py).
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field

import numpy as np
import shapely
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

from . import config as C

T = C.THICK


# ----------------------------------------------------------------------------- matrices
def translate(x=0.0, y=0.0, z=0.0):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def rot_x(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1.0]])


def rot_y(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1.0]])


def rot_z(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])


def frame(origin, u, v):
    """Matrix whose local x axis = u, local y = v, local z = u x v, placed at origin."""
    u = np.asarray(u, float); u /= np.linalg.norm(u)
    v = np.asarray(v, float); v = v - u * np.dot(u, v); v /= np.linalg.norm(v)
    w = np.cross(u, v)
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = u, v, w, origin
    return m


def apply(m, pts):
    pts = np.asarray(pts, float)
    return pts @ m[:3, :3].T + m[:3, 3]


def apply_dir(m, d):
    return np.asarray(d, float) @ m[:3, :3].T


# ----------------------------------------------------------------------------- 2D helpers
def rect(x0, y0, x1, y1):
    return box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def rect_c(cx, cy, w, h, angle=0.0):
    r = box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    return affinity.rotate(r, angle, origin=(cx, cy)) if angle else r


def circle(cx, cy, r, n=None):
    n = n or max(24, int(2 * math.pi * r / 1.2))
    return Polygon([(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)])


def rounded(poly, r):
    """Round convex corners by r (keeps size)."""
    return poly.buffer(-r, join_style='mitre').buffer(r, quad_segs=8)


def poly(points):
    return Polygon(points)


def polyline_stroke(points, width):
    return LineString(points).buffer(width / 2, cap_style='round', join_style='round')


def regular_star(cx, cy, r_out, r_in, n, rot=0.0):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot) + math.pi * i / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return Polygon(pts)


def gear_like(cx, cy, r_root, r_tip, teeth, tip_frac=0.45, rot=0.0):
    """Simple trapezoid-tooth wheel (decorative or ratchet)."""
    pts = []
    for i in range(teeth):
        a0 = math.radians(rot) + 2 * math.pi * i / teeth
        da = 2 * math.pi / teeth
        for f, r in ((0.0, r_root), (0.5 - tip_frac / 2, r_tip), (0.5 + tip_frac / 2, r_tip), (1.0, r_root)):
            a = a0 + f * da
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return Polygon(pts).buffer(0)


def largest(g):
    if isinstance(g, Polygon):
        return g
    if hasattr(g, 'geoms'):
        polys = [p for p in g.geoms if isinstance(p, Polygon)]
        return max(polys, key=lambda p: p.area)
    raise ValueError('no polygon')


def mirror_x(g):
    return affinity.scale(g, -1, 1, origin=(0, 0))


# ----------------------------------------------------------------------------- solids
@dataclass
class Part:
    name: str
    shape: Polygon
    color: str = 'natural'
    mat: np.ndarray = field(default_factory=lambda: np.eye(4))
    step: int = 1
    insert: tuple = (0.0, -1.0, 0.0)       # world direction the part travels into place
    explode: float = 40.0                  # mm back along -insert for the exploded view
    cuts: list = field(default_factory=list)       # [(Polygon, fit_class)]
    engrave: list = field(default_factory=list)    # fill polygons (local coords)
    score: list = field(default_factory=list)      # LineStrings (local coords)
    group: str = ''
    mechanism: bool = False                # part of a working mechanism -> needs physical test
    note: str = ''
    spares: int = 0                        # extra copies to cut into free sheet space
    code: str = ''                         # assigned by nesting, e.g. 'B12'
    sheet: str = ''
    kind: str = 'part'

    # -- geometry
    def outline(self, fit: dict | None = None) -> Polygon | MultiPolygon:
        g = self.shape
        if self.cuts:
            holes = []
            for p, cls in self.cuts:
                if fit is not None:
                    d = fit.get(cls, 0.0)
                    p = p.buffer(d, join_style='mitre', mitre_limit=4.0) if d else p
                holes.append(p)
            g = g.difference(unary_union(holes))
        return g.buffer(0)

    @property
    def T(self):
        return T

    def shape_key(self) -> str:
        """Same key = same physical part (geometry + color + engraving), so they share a part code."""
        o = shapely.normalize(shapely.set_precision(self.outline(), 0.01))
        eng = [shapely.set_precision(e, 0.05).wkb for e in self.engrave]
        sc = [shapely.set_precision(s, 0.05).wkb for s in self.score]
        h = hashlib.sha1(o.wkb + b''.join(sorted(eng)) + b''.join(sorted(sc)) + self.color.encode())
        return h.hexdigest()[:16]

    def place(self, m):
        self.mat = m
        return self

    def flip(self):
        """Swap which face is the laser (engrave) side without moving the part in the world."""
        self.shape = mirror_x(self.shape)
        self.cuts = [(mirror_x(p), c) for p, c in self.cuts]
        self.engrave = [mirror_x(p) for p in self.engrave]
        self.score = [mirror_x(s) for s in self.score]
        self.mat = self.mat @ rot_y(180)
        return self

    # -- solid queries (world space)
    def local(self, pts):
        inv = np.linalg.inv(self.mat)
        return apply(inv, pts)

    def freeze(self):
        """Cache outline, inverse matrix and prepared geometry for fast repeated queries."""
        g = self.outline()
        shapely.prepare(g)
        self._frozen = {'g': g, 'inv': np.linalg.inv(self.mat), 'grown': {}}
        return self

    def thaw(self):
        self.__dict__.pop('_frozen', None)
        return self

    def contains(self, pts, grow=0.0):
        fz = getattr(self, '_frozen', None)
        inv = fz['inv'] if fz else np.linalg.inv(self.mat)
        loc = apply(inv, pts)
        ok = np.abs(loc[:, 2]) < T / 2 + grow
        if not ok.any():
            return ok
        if fz:
            if grow:
                if grow not in fz['grown']:
                    gg = fz['g'].buffer(grow, join_style='mitre')
                    shapely.prepare(gg)
                    fz['grown'][grow] = gg
                g = fz['grown'][grow]
            else:
                g = fz['g']
        else:
            g = self.outline()
            if grow:
                g = g.buffer(grow, join_style='mitre')
        idx = np.nonzero(ok)[0]
        inside = shapely.contains_xy(g, loc[idx, 0], loc[idx, 1])
        ok[idx] = inside
        return ok

    def sample(self, spacing=1.0, shrink=0.15, zlevels=3):
        g = self.outline().buffer(-shrink, join_style='mitre')
        if g.is_empty:
            return np.zeros((0, 3))
        minx, miny, maxx, maxy = g.bounds
        xs = np.arange(minx + spacing / 2, maxx, spacing)
        ys = np.arange(miny + spacing / 2, maxy, spacing)
        gx, gy = np.meshgrid(xs, ys)
        gx, gy = gx.ravel(), gy.ravel()
        m = shapely.contains_xy(g, gx, gy)
        pts2 = [np.column_stack([gx[m], gy[m]])]
        # boundary samples catch thin tabs
        rings = []
        for p in getattr(g, 'geoms', [g]):
            rings.append(p.exterior)
            rings.extend(p.interiors)
        for r in rings:
            n = max(4, int(r.length / (spacing / 2)))
            ds = np.linspace(0, r.length, n, endpoint=False)
            pts2.append(np.array([r.interpolate(d).coords[0] for d in ds]))
        p2 = np.vstack(pts2)
        zt = T / 2 - shrink
        zs = np.linspace(-zt, zt, zlevels) if zlevels > 1 else [0.0]
        p3 = np.vstack([np.column_stack([p2, np.full(len(p2), z)]) for z in zs])
        return apply(self.mat, p3)

    def corners_world(self):
        minx, miny, maxx, maxy = self.shape.bounds
        c = np.array([[x, y, z] for x in (minx, maxx) for y in (miny, maxy) for z in (-T / 2, T / 2)])
        return apply(self.mat, c)

    def aabb(self):
        c = self.corners_world()
        return c.min(0), c.max(0)

    def centroid_world(self):
        c = self.shape.centroid
        return apply(self.mat, [[c.x, c.y, 0]])[0]


@dataclass
class Rod:
    """Hardware dowel or axle: a cylinder from p0 to p1 (world)."""
    name: str
    p0: tuple
    p1: tuple
    d: float = C.DOWEL_D
    step: int = 1
    insert: tuple = (1.0, 0.0, 0.0)
    explode: float = 40.0
    kind: str = 'rod'
    color: str = 'dowel'
    code: str = ''
    mechanism: bool = False
    note: str = ''
    group: str = ''

    def _axis(self):
        a, b = np.asarray(self.p0, float), np.asarray(self.p1, float)
        L = np.linalg.norm(b - a)
        return a, (b - a) / L, L

    @property
    def length(self):
        return self._axis()[2]

    def contains(self, pts, grow=0.0):
        a, u, L = self._axis()
        v = np.asarray(pts) - a
        t = v @ u
        r = np.linalg.norm(v - np.outer(t, u), axis=1)
        return (t > -grow) & (t < L + grow) & (r < self.d / 2 + grow)

    def sample(self, spacing=1.0, shrink=0.15, zlevels=3):
        a, u, L = self._axis()
        ref = np.array([1, 0, 0]) if abs(u[0]) < 0.9 else np.array([0, 1, 0])
        e1 = np.cross(u, ref); e1 /= np.linalg.norm(e1)
        e2 = np.cross(u, e1)
        r = self.d / 2 - shrink
        pts = []
        for t in np.arange(shrink, L - shrink + 1e-9, spacing / 2):
            for rr in (0.0, r * 0.5, r):
                n = 1 if rr == 0 else 8
                for k in range(n):
                    ang = 2 * math.pi * k / n
                    pts.append(a + u * t + rr * (math.cos(ang) * e1 + math.sin(ang) * e2))
        return np.array(pts)

    def aabb(self):
        a, b = np.asarray(self.p0, float), np.asarray(self.p1, float)
        r = self.d / 2
        return np.minimum(a, b) - r, np.maximum(a, b) + r

    def centroid_world(self):
        return (np.asarray(self.p0, float) + np.asarray(self.p1, float)) / 2


@dataclass
class Block:
    """Bought hardware approximated as a box (e.g. wind-up music movement). Axis-aligned in world."""
    name: str
    lo: tuple
    hi: tuple
    step: int = 1
    insert: tuple = (0.0, -1.0, 0.0)
    explode: float = 40.0
    kind: str = 'block'
    color: str = 'metal'
    code: str = ''
    mechanism: bool = True
    note: str = ''
    group: str = ''

    def contains(self, pts, grow=0.0):
        p = np.asarray(pts)
        lo, hi = np.asarray(self.lo) - grow, np.asarray(self.hi) + grow
        return np.all((p > lo) & (p < hi), axis=1)

    def sample(self, spacing=2.0, shrink=0.15, zlevels=3):
        lo, hi = np.asarray(self.lo) + shrink, np.asarray(self.hi) - shrink
        axes = [np.linspace(lo[i], hi[i], max(2, int((hi[i] - lo[i]) / spacing) + 1)) for i in range(3)]
        g = np.meshgrid(*axes, indexing='ij')
        return np.column_stack([a.ravel() for a in g])

    def aabb(self):
        return np.asarray(self.lo, float), np.asarray(self.hi, float)

    def centroid_world(self):
        return (np.asarray(self.lo, float) + np.asarray(self.hi, float)) / 2


@dataclass
class Step:
    n: int
    title: str
    tip: str = ''
    icons: list = field(default_factory=list)     # e.g. ['press', 'flip', 'test', 'wax', 'no-glue']
    test: str = ''                                # "test it now" instruction for mechanism steps
    view: tuple | None = None                     # optional camera direction for the step image


@dataclass
class Kit:
    slug: str
    name: str
    parts: list = field(default_factory=list)
    hardware: list = field(default_factory=list)  # Rod / Block objects
    steps: dict = field(default_factory=dict)
    story: str = ''
    difficulty: int = 3
    build_hours: str = ''
    price: float = 0.0
    tagline: str = ''
    extras: dict = field(default_factory=dict)    # loose hardware: {'rubber bands': 10, ...}

    def add(self, *parts):
        for p in parts:
            if isinstance(p, (list, tuple)):
                self.add(*p)
            elif isinstance(p, Part):
                self.parts.append(p)
            else:
                self.hardware.append(p)
        return parts[0] if len(parts) == 1 else parts

    def step(self, n, title, **kw):
        self.steps[n] = Step(n, title, **kw)

    def solids(self):
        return list(self.parts) + list(self.hardware)

    def by_name(self, name):
        for s in self.solids():
            if s.name == name:
                return s
        raise KeyError(name)
