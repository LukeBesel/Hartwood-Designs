"""Print mode: UV-printed color on natural sheets (the way most commercial kits show color only on the parts).

Per sheet this writes
- <sheet>_print_front.svg / .pdf : the color layer, exact size (300 x 300 mm), every colored part filled with its
  color and grown by a bleed so a small misalignment never shows bare wood at the cut line. Registration targets
  (black ring + cross) at C.PRINT['targets'], the same spots as the tool-layer targets in the cut file.
- <sheet>_print_white.svg : the white underbase (black = print white there). Pastel colors need it on wood.
- <sheet>_print_back.svg / .pdf : only if a colored part shows its back face in the finished model. It is the
  mirror image: flip the printed sheet left to right, print again, then cut.
- <sheet>_print_preview.png : what the printed sheet looks like before cutting.

Workflow (see docs in research/color_printing.md): print on the UV printer with the sheet against a corner jig,
move it to the laser against the same corner, align with LightBurn Print and Cut on the two targets, cut.
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageDraw
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

from . import config as C
from .geom import T, apply


# ----------------------------------------------------------------------------- which backs show
def back_visibility(kit, spacing=2.0):
    """For each colored part: how much of its front and back faces is NOT covered by another part.
    print_front = False when under 3 percent of the front shows (nothing to print: e.g. a stacked ring).
    print_back  = True when more than 40 percent of the back shows (print both sides, if C.PRINT allows)."""
    import shapely
    sol = kit.solids()
    for p in kit.parts:
        p.freeze()
    boxes = {id(s): s.aabb() for s in sol}
    for p in kit.parts:
        p.__dict__['print_back'] = False
        p.__dict__['print_front'] = p.color != 'natural'
        if p.color == 'natural':
            continue
        g = p.outline().buffer(-0.6)
        if g.is_empty:
            continue
        minx, miny, maxx, maxy = g.bounds
        xs, ys = np.meshgrid(np.arange(minx, maxx, spacing), np.arange(miny, maxy, spacing))
        pts = np.column_stack([xs.ravel(), ys.ravel()])
        pts = pts[shapely.contains_xy(g, pts[:, 0], pts[:, 1])]
        if not len(pts):
            continue
        lo, hi = boxes[id(p)]
        near = [s for s in sol if s is not p and not (np.any(boxes[id(s)][0] > hi + 2) or np.any(boxes[id(s)][1] < lo - 2))]
        free = {}
        for side, z in (('front', T / 2 + 0.4), ('back', -T / 2 - 0.4)):
            W = apply(p.mat, np.column_stack([pts, np.full(len(pts), z)]))
            covered = np.zeros(len(pts), bool)
            for s in near:
                covered |= s.contains(W, grow=0.3)
            free[side] = 1.0 - covered.mean()
        p.__dict__['front_free'] = round(float(free['front']), 2)
        p.__dict__['back_free'] = round(float(free['back']), 2)
        p.__dict__['print_front'] = bool(free['front'] > 0.03)
        p.__dict__['print_back'] = bool(free['back'] > 0.4) and C.PRINT.get('two_sided', True)
    for p in kit.parts:
        p.thaw()


# ----------------------------------------------------------------------------- layers
def color_layers(sheet, side='front'):
    """[(hex, polygon in sheet mm)] for every printed part on this sheet (front or mirrored back)."""
    bleed = C.PRINT['bleed_mm']
    out = []
    for pl in sheet.placed:
        p = pl.part
        if p.color == 'natural' or (side == 'back' and not p.__dict__.get('print_back')) \
                or (side == 'front' and not p.__dict__.get('print_front', True)):
            continue
        g = pl.xf(p.outline()).buffer(bleed, join_style='mitre', mitre_limit=2.0)
        if side == 'back':
            g = affinity.scale(g, -1, 1, origin=(sheet.W / 2, 0))
        out.append((C.MATERIALS[p.color]['face'], g))
    return out


def _targets(sheet, side):
    ts = [tuple(t) for t in C.PRINT['targets']]
    if side == 'back':
        ts = [(sheet.W - x, y) for x, y in ts]
    return ts


def _path_d(g, H):
    d = []
    for poly in getattr(g, 'geoms', [g]):
        for ring in [poly.exterior] + list(poly.interiors):
            cs = list(ring.coords)
            d.append('M' + ' L'.join(f'{x:.3f} {H - y:.3f}' for x, y in cs) + ' Z')
    return ' '.join(d)


def write_print_svg(sheet, path, side='front', white=False):
    W, H = sheet.W, sheet.H
    layers = color_layers(sheet, side)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
           f'<title>Hartwood print {sheet.letter} {side}{" white underbase" if white else ""}</title>']
    if white:
        u = unary_union([g for _, g in layers])
        if not u.is_empty:
            out.append(f'<path d="{_path_d(u, H)}" fill="#000000" fill-rule="evenodd"/>')
    else:
        for hexc, g in layers:
            out.append(f'<path d="{_path_d(g, H)}" fill="{hexc}" fill-rule="evenodd"/>')
    r = C.PRINT['target_r']
    for x, y in _targets(sheet, side):
        out.append(f'<circle cx="{x}" cy="{H - y}" r="{r}" fill="none" stroke="#000" stroke-width="0.3"/>'
                   f'<path d="M{x - r * 1.6} {H - y}H{x + r * 1.6}M{x} {H - y - r * 1.6}V{H - y + r * 1.6}" stroke="#000" stroke-width="0.3"/>')
    out.append('</svg>')
    open(path, 'w').write('\n'.join(out))
    return len(layers)


def write_print_pdf(sheet, path, side='front'):
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(path, pagesize=(sheet.W * mm, sheet.H * mm))
    c.setTitle(f'Hartwood print {sheet.letter} {side}')
    for hexc, g in color_layers(sheet, side):
        c.setFillColor(HexColor(hexc)); c.setStrokeColor(HexColor(hexc))
        for poly in getattr(g, 'geoms', [g]):
            pth = c.beginPath()
            for ring in [poly.exterior] + list(poly.interiors):
                cs = list(ring.coords)
                pth.moveTo(cs[0][0] * mm, cs[0][1] * mm)
                for x, y in cs[1:]:
                    pth.lineTo(x * mm, y * mm)
                pth.close()
            c.drawPath(pth, stroke=0, fill=1, fillMode=0)
    r = C.PRINT['target_r']
    c.setStrokeColor(HexColor('#000000')); c.setLineWidth(0.3 * mm)
    for x, y in _targets(sheet, side):
        c.circle(x * mm, y * mm, r * mm, stroke=1, fill=0)
        c.line((x - r * 1.6) * mm, y * mm, (x + r * 1.6) * mm, y * mm)
        c.line(x * mm, (y - r * 1.6) * mm, x * mm, (y + r * 1.6) * mm)
    c.showPage(); c.save()


def preview_png(sheet, sp, path, px_per_mm=3.0):
    """Printed natural sheet with the cut lines on top."""
    S = px_per_mm
    W, H = int(sheet.W * S), int(sheet.H * S)
    im = Image.new('RGB', (W, H), (236, 214, 178))
    d = ImageDraw.Draw(im)
    tf = lambda x, y: (x * S, H - y * S)
    for hexc, g in color_layers(sheet):
        col = tuple(int(hexc[i:i + 2], 16) for i in (1, 3, 5))
        for poly in getattr(g, 'geoms', [g]):
            d.polygon([tf(*q) for q in poly.exterior.coords], fill=col)
            for r in poly.interiors:
                d.polygon([tf(*q) for q in r.coords], fill=(236, 214, 178))
    for c, closed, _ in sp.cuts:
        d.line([tf(*q) for q in c], fill=(70, 40, 20), width=1)
    for x, y in C.PRINT['targets']:
        r = C.PRINT['target_r'] * S
        cx, cy = tf(x, y)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(0, 0, 0), width=2)
    im.save(path)


def print_stats(sheet):
    """Printed area, band, time and ink for one sheet (front, plus back if any). Estimates from C.PRINT."""
    st = {}
    for side in ('front', 'back'):
        layers = color_layers(sheet, side)
        if not layers:
            st[side] = None
            continue
        u = unary_union([g for _, g in layers])
        minx, miny, maxx, maxy = u.bounds
        band = min(maxx - minx, maxy - miny)               # print with the short side across the passes
        swept_m2 = band / 1000.0 * C.PRINT['bed_mm'][0] / 1000.0
        minutes = C.PRINT['overhead_min'] + 60.0 * swept_m2 / C.PRINT['rate_m2_per_h']
        ink_ml = u.area / 1e6 * C.PRINT['ink_ml_per_m2']
        st[side] = {'printed_mm2': round(u.area), 'band_mm': round(band, 1), 'minutes': round(minutes, 1),
                    'ink_ml': round(ink_ml, 2), 'ink_usd': round(ink_ml * C.PRINT['ink_usd_per_ml'], 2)}
    return st


def write_all(sheet, sp, base):
    """Write the print files for one sheet. base = path prefix. Returns stats."""
    st = print_stats(sheet)
    if st['front'] is None:
        return st
    write_print_svg(sheet, base + '_print_front.svg', 'front')
    write_print_pdf(sheet, base + '_print_front.pdf', 'front')
    write_print_svg(sheet, base + '_print_white.svg', 'front', white=True)
    if st['back']:
        write_print_svg(sheet, base + '_print_back.svg', 'back')
        write_print_pdf(sheet, base + '_print_back.pdf', 'back')
    preview_png(sheet, sp, base + '_print_preview.png')
    return st
