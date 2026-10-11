"""Build pipeline for one kit: checks -> nesting -> cut files -> GLB + steps JSON -> report."""
from __future__ import annotations

import json
import os
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.ops import unary_union

from . import checks as CK
from . import config as C
from .cutfiles import sheet_paths, write_bed_svg, write_dxf, write_lbrn, write_svg
from .export import export_glb, steps_json
from .nest import assign_codes, nest, verify

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def _hex(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def parts_map_png(sheet, sp, path, px_per_mm=3.0):
    S = px_per_mm
    W = int(C.SHEET_W * S); H = int(C.SHEET_H * S)
    im = Image.new('RGB', (W, H), (250, 246, 238))
    dr = ImageDraw.Draw(im)
    m = C.MATERIALS[sheet.color]
    face = _hex(m['face']); edge = (60, 40, 25)
    dr.rectangle([0, 0, W - 1, H - 1], outline=(180, 170, 150), width=2)
    font = ImageFont.truetype(FONT, int(5.5 * S))
    small = ImageFont.truetype(FONT, int(3.6 * S))
    for pl in sheet.placed:
        g = pl.xf(pl.part.outline())
        for poly in getattr(g, 'geoms', [g]):
            ext = [(x * S, H - y * S) for x, y in poly.exterior.coords]
            dr.polygon(ext, fill=face if not pl.spare else tuple(int(v * 0.85 + 30) for v in face), outline=edge)
            for r in poly.interiors:
                dr.polygon([(x * S, H - y * S) for x, y in r.coords], fill=(250, 246, 238), outline=edge)
    for pl in sheet.placed:
        g = pl.xf(pl.part.outline())
        c = g.representative_point()
        txt = pl.code + (' spare' if pl.spare else '')
        f = font if g.area > 300 else small
        bb = dr.textbbox((0, 0), txt, font=f)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        x, y = c.x * S - tw / 2, H - c.y * S - th / 2
        dr.rounded_rectangle([x - 4, y - 3, x + tw + 4, y + th + 6], radius=6, fill=(255, 255, 255), outline=edge)
        dr.text((x, y), txt, fill=(30, 20, 10), font=f)
    hdr = ImageFont.truetype(FONT, int(6 * S))
    dr.text((10, 8), f'Sheet {sheet.letter}  ({m["label"]})', fill=(30, 20, 10), font=hdr)
    im.save(path)


def build(kit, outdir, run_checks=True, check_spacing=1.0, log=print):
    t0 = time.time()
    os.makedirs(outdir, exist_ok=True)
    report = {'kit': kit.slug, 'name': kit.name}
    if run_checks:
        res = CK.run_all(kit, spacing=check_spacing)
        report['checks'] = res
        for r in res:
            log(f"  {r['name']}: {'PASS' if r['pass'] else 'FAIL'} - {r['summary']}")
    sheets = nest(kit.parts)
    assign_codes(sheets, kit.name)
    probs = verify(sheets)
    report['nest_problems'] = probs
    if probs:
        log('  NEST PROBLEMS: ' + '; '.join(probs[:5]))
    cdir = os.path.join(outdir, 'cutfiles'); os.makedirs(cdir, exist_ok=True)
    mdir = os.path.join(outdir, 'parts_map'); os.makedirs(mdir, exist_ok=True)
    sps = []
    for sh in sheets:
        sp = sheet_paths(sh)
        sps.append(sp)
        base = os.path.join(cdir, f'{kit.slug}_sheet_{sh.letter}_{sh.color}')
        write_svg(sp, base + '.svg', title=f'Hartwood {kit.name} sheet {sh.letter} ({C.MATERIALS[sh.color]["label"]})')
        write_dxf(sp, base + '.dxf')
        write_lbrn([sp], base + '.lbrn2')
        parts_map_png(sh, sp, os.path.join(mdir, f'sheet_{sh.letter}.png'))
    # two sheets per laser job (same job = same material settings, so any colors can pair)
    jobs = []
    for i in range(0, len(sps), C.SHEETS_PER_JOB):
        grp = sps[i:i + C.SHEETS_PER_JOB]
        name = f'{kit.slug}_job{i // C.SHEETS_PER_JOB + 1}_' + ''.join(s.letter for s in grp)
        write_bed_svg(grp, os.path.join(cdir, name + '_bed.svg'))
        write_lbrn(grp, os.path.join(cdir, name + '_bed.lbrn2'),
                   offsets=[(k * (C.SHEET_W + 5.0), 0.0) for k in range(len(grp))])
        jobs.append({'job': name, 'sheets': [s.letter for s in grp],
                     'laser_min': round(sum(s.stats['total_s'] for s in grp) / 60, 2)})
    # 3D + steps
    glb_path = os.path.join(outdir, f'{kit.slug}.glb')
    export_glb(kit, sheets, glb_path)
    sj = steps_json(kit, sheets)
    json.dump(sj, open(os.path.join(outdir, f'{kit.slug}_steps.json'), 'w'), indent=1)
    # report
    sheet_rows = []
    for sh, sp in zip(sheets, sps):
        sheet_rows.append({'sheet': sh.letter, 'color': sh.color, 'parts': len([p for p in sh.placed if not p.spare]),
                           'spares': len([p for p in sh.placed if p.spare]),
                           'used_pct': round(100 * sum(p.xf(p.part.outline()).area for p in sh.placed) /
                                             (C.SHEET_W * C.SHEET_H), 1), **sp.stats})
    laser_s = sum(r['total_s'] for r in sheet_rows)
    swap_s = len(jobs) * C.SHEET_SWAP_S
    n_nat = sum(1 for s in sheets if s.color == 'natural')
    n_col = len(sheets) - n_nat
    mat_cost = n_nat * C.SHEET_COST['natural'] + n_col * C.SHEET_COST['colored']
    report.update({
        'pieces': len(kit.parts), 'unique_codes': len({p.code for p in kit.parts}),
        'hardware': [{'name': h.name, 'kind': h.kind, 'note': h.note} for h in kit.hardware],
        'extras': kit.extras,
        'sheets': sheet_rows, 'jobs': jobs, 'n_sheets': len(sheets),
        'sheets_by_color': {c: sum(1 for s in sheets if s.color == c) for c in sorted({s.color for s in sheets})},
        'laser_minutes': round(laser_s / 60, 1), 'swap_minutes': round(swap_s / 60, 1),
        'cut_minutes_per_kit': round((laser_s + swap_s) / 60, 1),
        'wood_cost_usd': round(mat_cost, 2),
        'mechanism_parts': sorted({p.code for p in kit.parts if p.mechanism}),
        'build_seconds': round(time.time() - t0, 1),
    })
    if run_checks:
        report['all_checks_pass'] = all(r['pass'] for r in report['checks']) and not probs
    json.dump(report, open(os.path.join(outdir, f'{kit.slug}_report.json'), 'w'), indent=1, default=str)
    log(f"  {report['pieces']} pieces, {len(sheets)} sheets, laser {report['laser_minutes']} min "
        f"(+{report['swap_minutes']} min sheet swaps), wood ${report['wood_cost_usd']}")
    return report, sheets, sps
