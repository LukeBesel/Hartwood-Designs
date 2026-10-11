"""Export a kit as GLB (one node per part, with extras) plus step JSON for the app, booklet and site.

Node extras: code, name, color, step, insert (world unit vector), explode (mm), sheet, mechanism, kind.
Units: the root node scales mm -> m (0.001), so any glTF viewer shows true size.
"""
from __future__ import annotations

import json
import math
import struct

import numpy as np
import shapely
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

from . import config as C
from .geom import T, Block, Part, Rod

DECAL_Z = 0.06      # engraving decals float this far above the face (mm)
SCORE_W = 0.35      # rendered width of a score line (mm)


# ----------------------------------------------------------------------------- triangulation
def tri_polygon(g):
    """Triangles (list of 3x2 arrays) covering polygon g (with holes)."""
    out = []
    for p in getattr(g, 'geoms', [g]):
        if p.is_empty or p.area < 1e-4:
            continue
        tris = shapely.constrained_delaunay_triangles(p)
        for t in tris.geoms:
            c = np.array(t.exterior.coords[:3])
            out.append(c)
    return out


class MeshBuilder:
    def __init__(self):
        self.pos, self.nrm, self.uv, self.idx = [], [], [], []

    def add_tri(self, a, b, c, n, uva, uvb, uvc):
        base = len(self.pos)
        self.pos += [a, b, c]; self.nrm += [n, n, n]; self.uv += [uva, uvb, uvc]
        self.idx += [base, base + 1, base + 2]

    def empty(self):
        return not self.idx

    def arrays(self):
        return (np.array(self.pos, np.float32), np.array(self.nrm, np.float32),
                np.array(self.uv, np.float32), np.array(self.idx, np.uint32))


def _ccw(tri):
    a, b, c = tri
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) > 0


def part_meshes(part: Part, grain_angle=0.0, code_geom=None):
    """Return dict of MeshBuilders: 'face', 'edge', 'engrave' in part-local coordinates."""
    g = part.outline()
    ca, sa = math.cos(math.radians(grain_angle)), math.sin(math.radians(grain_angle))

    def uvf(x, y):
        return ((x * ca - y * sa) / 120.0, (x * sa + y * ca) / 120.0)
    face, edge, eng = MeshBuilder(), MeshBuilder(), MeshBuilder()
    h = T / 2
    for tri in tri_polygon(g):
        if not _ccw(tri):
            tri = tri[::-1]
        a, b, c = tri
        face.add_tri((a[0], a[1], h), (b[0], b[1], h), (c[0], c[1], h), (0, 0, 1), uvf(*a), uvf(*b), uvf(*c))
        face.add_tri((a[0], a[1], -h), (c[0], c[1], -h), (b[0], b[1], -h), (0, 0, -1), uvf(*a), uvf(*c), uvf(*b))
    for p in getattr(g, 'geoms', [g]):
        rings = [shapely.geometry.polygon.orient(p, 1.0).exterior] + list(shapely.geometry.polygon.orient(p, 1.0).interiors)
        for r in rings:
            cs = np.array(r.coords)
            s = 0.0
            for i in range(len(cs) - 1):
                x0, y0 = cs[i]; x1, y1 = cs[i + 1]
                L = math.hypot(x1 - x0, y1 - y0)
                if L < 1e-6:
                    continue
                n = (y1 - y0) / L, -(x1 - x0) / L, 0.0   # outward for CCW exterior / CW holes
                u0, u1 = s / 50.0, (s + L) / 50.0
                edge.add_tri((x0, y0, -h), (x1, y1, -h), (x1, y1, h), n, (u0, 0), (u1, 0), (u1, 0.06))
                edge.add_tri((x0, y0, -h), (x1, y1, h), (x0, y0, h), n, (u0, 0), (u1, 0.06), (u0, 0.06))
                s += L
    decals = list(part.engrave) + [sc.buffer(SCORE_W / 2, cap_style='round') for sc in part.score]
    if code_geom is not None:
        decals.append(code_geom)
    if decals:
        dg = unary_union(decals).intersection(g)
        z = h + DECAL_Z
        for tri in tri_polygon(dg):
            if not _ccw(tri):
                tri = tri[::-1]
            a, b, c = tri
            eng.add_tri((a[0], a[1], z), (b[0], b[1], z), (c[0], c[1], z), (0, 0, 1), uvf(*a), uvf(*b), uvf(*c))
    return {'face': face, 'edge': edge, 'engrave': eng}


def rod_mesh(rod: Rod, seg=16):
    a, b = np.asarray(rod.p0, float), np.asarray(rod.p1, float)
    u = b - a; L = np.linalg.norm(u); u /= L
    ref = np.array([1, 0, 0]) if abs(u[0]) < 0.9 else np.array([0, 1, 0])
    e1 = np.cross(u, ref); e1 /= np.linalg.norm(e1); e2 = np.cross(u, e1)
    r = rod.d / 2
    m = MeshBuilder()
    for i in range(seg):
        t0, t1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
        n0 = math.cos(t0) * e1 + math.sin(t0) * e2
        n1 = math.cos(t1) * e1 + math.sin(t1) * e2
        p00, p01 = a + r * n0, a + r * n1
        p10, p11 = b + r * n0, b + r * n1
        nn = (n0 + n1) / 2
        m.add_tri(tuple(p00), tuple(p10), tuple(p11), tuple(nn), (0, 0), (1, 0), (1, 1))
        m.add_tri(tuple(p00), tuple(p11), tuple(p01), tuple(nn), (0, 0), (1, 1), (0, 1))
        m.add_tri(tuple(a), tuple(p01), tuple(p00), tuple(-u), (0, 0), (0, 0), (0, 0))
        m.add_tri(tuple(b), tuple(p10), tuple(p11), tuple(u), (0, 0), (0, 0), (0, 0))
    return m


def block_mesh(bl: Block):
    lo, hi = np.asarray(bl.lo, float), np.asarray(bl.hi, float)
    m = MeshBuilder()
    for axis in range(3):
        for side in (0, 1):
            n = np.zeros(3); n[axis] = 1 if side else -1
            o = [i for i in range(3) if i != axis]
            c = lo.copy(); c[axis] = hi[axis] if side else lo[axis]
            q = []
            for (s0, s1) in ((0, 0), (1, 0), (1, 1), (0, 1)):
                p = c.copy()
                p[o[0]] = hi[o[0]] if s0 else lo[o[0]]
                p[o[1]] = hi[o[1]] if s1 else lo[o[1]]
                q.append(tuple(p))
            m.add_tri(q[0], q[1], q[2], tuple(n), (0, 0), (1, 0), (1, 1))
            m.add_tri(q[0], q[2], q[3], tuple(n), (0, 0), (1, 1), (0, 1))
    return m


# ----------------------------------------------------------------------------- GLB writer
class GLB:
    def __init__(self):
        self.bin = bytearray()
        self.gltf = {'asset': {'version': '2.0', 'generator': 'Hartwood engine'}, 'scenes': [{'nodes': [0]}],
                     'scene': 0, 'nodes': [], 'meshes': [], 'materials': [], 'accessors': [], 'bufferViews': [],
                     'buffers': []}
        self.mat_index = {}

    def material(self, key, color_hex, rough=0.85, metal=0.0, double=False):
        if key in self.mat_index:
            return self.mat_index[key]
        c = color_hex.lstrip('#')
        rgb = [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        lin = [((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in rgb]
        self.gltf['materials'].append({'name': key, 'pbrMetallicRoughness': {
            'baseColorFactor': lin + [1.0], 'roughnessFactor': rough, 'metallicFactor': metal},
            'doubleSided': double})
        self.mat_index[key] = len(self.gltf['materials']) - 1
        return self.mat_index[key]

    def _view(self, data: bytes, target=None):
        while len(self.bin) % 4:
            self.bin.append(0)
        off = len(self.bin)
        self.bin += data
        v = {'buffer': 0, 'byteOffset': off, 'byteLength': len(data)}
        if target:
            v['target'] = target
        self.gltf['bufferViews'].append(v)
        return len(self.gltf['bufferViews']) - 1

    def _acc(self, arr, typ, comp, target, minmax=False):
        view = self._view(arr.tobytes(), target)
        a = {'bufferView': view, 'componentType': comp, 'count': int(arr.shape[0]), 'type': typ}
        if minmax:
            a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
        self.gltf['accessors'].append(a)
        return len(self.gltf['accessors']) - 1

    def primitive(self, mb: MeshBuilder, mat):
        pos, nrm, uv, idx = mb.arrays()
        return {'attributes': {'POSITION': self._acc(pos, 'VEC3', 5126, 34962, True),
                               'NORMAL': self._acc(nrm, 'VEC3', 5126, 34962),
                               'TEXCOORD_0': self._acc(uv, 'VEC2', 5126, 34962)},
                'indices': self._acc(idx, 'SCALAR', 5125, 34963), 'material': mat}

    def mesh(self, name, prims):
        self.gltf['meshes'].append({'name': name, 'primitives': prims})
        return len(self.gltf['meshes']) - 1

    def node(self, name, mesh=None, matrix=None, extras=None, children=None, scale=None):
        n = {'name': name}
        if mesh is not None:
            n['mesh'] = mesh
        if matrix is not None:
            n['matrix'] = [float(v) for v in np.asarray(matrix).T.ravel()]   # column-major
        if scale is not None:
            n['scale'] = scale
        if extras:
            n['extras'] = extras
        if children:
            n['children'] = children
        self.gltf['nodes'].append(n)
        return len(self.gltf['nodes']) - 1

    def save(self, path):
        self.gltf['buffers'] = [{'byteLength': len(self.bin)}]
        js = json.dumps(self.gltf, separators=(',', ':')).encode()
        while len(js) % 4:
            js += b' '
        while len(self.bin) % 4:
            self.bin.append(0)
        total = 12 + 8 + len(js) + 8 + len(self.bin)
        with open(path, 'wb') as f:
            f.write(struct.pack('<III', 0x46546C67, 2, total))
            f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
            f.write(struct.pack('<II', len(self.bin), 0x004E4942)); f.write(bytes(self.bin))


def export_glb(kit, sheets, path):
    """sheets: nested sheets (to recover grain angle and on-part code engraving)."""
    glb = GLB()
    root_children = []
    glb.gltf['nodes'].append(None)  # placeholder root at index 0
    pl_of = {}
    for sh in sheets:
        for pl in sh.placed:
            if not pl.spare and id(pl.part) not in pl_of:
                pl_of[id(pl.part)] = pl
    for p in kit.parts:
        pl = pl_of.get(id(p))
        grain = -pl.angle if pl else 0.0
        code_local = None
        if pl and pl.code_on_part and pl.code_geom is not None:
            code_local = affinity.rotate(affinity.translate(pl.code_geom, -pl.dx, -pl.dy), -pl.angle, origin=(0, 0))
        ms = part_meshes(p, grain, code_local)
        m = C.MATERIALS[p.color]
        prims = [glb.primitive(ms['face'], glb.material('face_' + p.color, m['face'], 0.8)),
                 glb.primitive(ms['edge'], glb.material('edge_' + p.color, m['edge'], 0.95))]
        if not ms['engrave'].empty():
            prims.append(glb.primitive(ms['engrave'], glb.material('engrave_' + p.color, m['engrave'], 0.95)))
        mi = glb.mesh(p.name, prims)
        ext = {'kind': 'part', 'code': p.code, 'name': p.name, 'color': p.color, 'step': p.step,
               'insert': [round(float(v), 4) for v in np.asarray(p.insert) / np.linalg.norm(p.insert)],
               'explode': p.explode, 'sheet': p.sheet, 'mechanism': p.mechanism, 'group': p.group}
        root_children.append(glb.node(p.code or p.name, mi, p.mat, ext))
    for h in kit.hardware:
        if isinstance(h, Rod):
            mb = rod_mesh(h); mat = glb.material('dowel', '#d9b98a', 0.7)
        else:
            mb = block_mesh(h); mat = glb.material('metal', '#b8bcc2', 0.35, 0.8)
        mi = glb.mesh(h.name, [glb.primitive(mb, mat)])
        ext = {'kind': h.kind, 'code': h.code or h.name, 'name': h.name, 'step': h.step,
               'insert': [round(float(v), 4) for v in np.asarray(h.insert) / np.linalg.norm(h.insert)],
               'explode': h.explode, 'mechanism': getattr(h, 'mechanism', False), 'note': h.note}
        root_children.append(glb.node(h.name, mi, None, ext))
    glb.gltf['nodes'][0] = {'name': kit.slug, 'scale': [0.001, 0.001, 0.001], 'children': root_children,
                            'extras': {'kit': kit.slug, 'name': kit.name, 'units': 'mm (root scaled to m)'}}
    glb.save(path)
    return path


def steps_json(kit, sheets, hardware_codes=None):
    parts = {}
    for p in kit.parts:
        e = parts.setdefault(p.code, {'code': p.code, 'name': p.name, 'sheet': p.sheet, 'color': p.color,
                                      'qty': 0, 'step': p.step, 'mechanism': p.mechanism})
        e['qty'] += 1
        e['step'] = min(e['step'], p.step)
    steps = []
    for n in sorted({s.step for s in kit.solids()}):
        st = kit.steps.get(n)
        new = {}
        for p in kit.parts:
            if p.step == n:
                e = new.setdefault(p.code, {'code': p.code, 'qty': 0, 'sheet': p.sheet, 'name': p.name,
                                            'color': p.color})
                e['qty'] += 1
        hw = [{'name': h.name, 'kind': h.kind, 'note': h.note} for h in kit.hardware if h.step == n]
        steps.append({'n': n, 'title': st.title if st else f'Step {n}', 'tip': st.tip if st else '',
                      'icons': st.icons if st else [], 'test': st.test if st else '',
                      'view': list(st.view) if st and st.view else None,
                      'parts': sorted(new.values(), key=lambda e: (e['sheet'], int(''.join(ch for ch in e['code'] if ch.isdigit()) or 0))),
                      'hardware': hw})
    sheet_info = [{'letter': sh.letter, 'color': sh.color, 'label': C.MATERIALS[sh.color]['label'],
                   'parts': len([pl for pl in sh.placed if not pl.spare]),
                   'spares': len([pl for pl in sh.placed if pl.spare])} for sh in sheets]
    return {'kit': kit.slug, 'name': kit.name, 'tagline': kit.tagline, 'story': kit.story,
            'difficulty': kit.difficulty, 'build_hours': kit.build_hours, 'price': kit.price,
            'piece_count': len(kit.parts), 'unique_codes': len(parts), 'sheets': sheet_info,
            'extras': kit.extras, 'steps': steps, 'parts': sorted(parts.values(), key=lambda e: e['code'])}
