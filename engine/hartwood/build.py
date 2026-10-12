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
from . import popout as PO
from . import printfiles as PF
from .cutfiles import sheet_paths, tile_batch, write_bed_svg, write_dxf, write_lbrn, write_svg
from .export import export_glb, steps_json
from .nest import assign_codes, nest, verify
from .cutfiles import TILE_OFFSETS

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def _hex(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def parts_map_png(sheet, sp, path, px_per_mm=3.0):
    S = px_per_mm
    W = int(sheet.W * S); H = int(sheet.H * S)
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
    tile = '' if sheet.tile == 'full' else f', {sheet.tile} sheet'
    dr.text((10, 8), f'Sheet {sheet.letter}  ({m["label"]}{tile})', fill=(30, 20, 10), font=ImageFont.truetype(FONT, int((6 if sheet.tile == 'full' else 4.2) * S)))
    im.save(path)


def build(kit, outdir, run_checks=True, check_spacing=1.0, log=print, color_mode=None):
    mode = color_mode or C.COLOR_MODE
    t0 = time.time()
    os.makedirs(outdir, exist_ok=True)
    report = {'kit': kit.slug, 'name': kit.name}
    kit.compact_steps()
    if run_checks:
        res = CK.run_all(kit, spacing=check_spacing)
        report['checks'] = res
        for r in res:
            log(f"  {r['name']}: {'PASS' if r['pass'] else 'FAIL'} - {r['summary']}")
    PO.mating_edges(kit)           # edges that touch other parts: no bridges there
    if mode == 'print':
        PF.back_visibility(kit)    # which colored parts show their back face (print both sides)
    sheets = nest(kit.parts, mode=mode, allow_tiles=(mode != 'print'))
    assign_codes(sheets, kit.name)
    probs = verify(sheets)
    report['nest_problems'] = probs
    if probs:
        log('  NEST PROBLEMS: ' + '; '.join(probs[:5]))
    import shutil
    cdir = os.path.join(outdir, 'cutfiles'); shutil.rmtree(cdir, ignore_errors=True); os.makedirs(cdir)
    mdir = os.path.join(outdir, 'parts_map'); shutil.rmtree(mdir, ignore_errors=True); os.makedirs(mdir)
    bdir = os.path.join(outdir, 'popout'); shutil.rmtree(bdir, ignore_errors=True); os.makedirs(bdir)
    sps = []
    batch = []      # physical 12 x 12 sheets to cut (tiles composed into full sheets)
    prints = []
    for sh in sheets:
        sp = sheet_paths(sh)
        if mode == 'print':
            sp.targets = [tuple(t) for t in C.PRINT['targets']]
        sps.append(sp)
        tag = '' if sh.tile == 'full' else f'_{sh.tile}'
        base = os.path.join(cdir, f'{kit.slug}_sheet_{sh.letter}_{sh.color}{tag}')
        write_svg(sp, base + '.svg', W=sh.W, H=sh.H,
                  title=f'Hartwood {kit.name} sheet {sh.letter} ({C.MATERIALS[sh.color]["label"]}, {sh.tile})')
        write_dxf(sp, base + '.dxf')
        write_lbrn([sp], base + '.lbrn2')
        parts_map_png(sh, sp, os.path.join(mdir, f'sheet_{sh.letter}.png'))
        PO.bridge_map_png(sh, sp, os.path.join(bdir, f'sheet_{sh.letter}.png'))
        if mode == 'print':
            prints.append({'sheet': sh.letter, **PF.write_all(sh, sp, base)})
        if sh.tile == 'full':
            batch.append((sp, 1))
        else:
            tb = tile_batch(sp, sh.tile)
            n = len(TILE_OFFSETS[sh.tile])
            write_svg(tb, os.path.join(cdir, f'{kit.slug}_sheet_{sh.letter}_{sh.color}_x{n}_full.svg'),
                      title=f'Hartwood {kit.name} sheet {sh.letter} x{n} kits ({C.MATERIALS[sh.color]["label"]})')
            write_dxf(tb, os.path.join(cdir, f'{kit.slug}_sheet_{sh.letter}_{sh.color}_x{n}_full.dxf'))
            write_lbrn([tb], os.path.join(cdir, f'{kit.slug}_sheet_{sh.letter}_{sh.color}_x{n}_full.lbrn2'))
            batch.append((tb, n))
    pop = PO.check_popout(sheets, sps)
    log(f"  {pop['name']}: {'PASS' if pop['pass'] else 'FAIL'} - {pop['summary']}")
    if run_checks:
        report['checks'].append(pop)
    report['popout'] = pop
    # laser jobs: two full sheets per job on the bed
    jobs = []
    fulls = [b for b in batch]
    for i in range(0, len(fulls), C.SHEETS_PER_JOB):
        grp = [b[0] for b in fulls[i:i + C.SHEETS_PER_JOB]]
        name = f'{kit.slug}_job{i // C.SHEETS_PER_JOB + 1}_' + '-'.join(g.letter for g in grp)
        write_bed_svg(grp, os.path.join(cdir, name + '_bed.svg'))
        write_lbrn(grp, os.path.join(cdir, name + '_bed.lbrn2'),
                   offsets=[(k * (C.SHEET_W + 5.0), 0.0) for k in range(len(grp))])
        jobs.append({'job': name, 'sheets': [g.letter for g in grp],
                     'laser_min': round(sum(g.stats['total_s'] for g in grp) / 60, 2),
                     'kits_per_sheet': [b[1] for b in fulls[i:i + C.SHEETS_PER_JOB]]})
    # 3D + steps
    glb_path = os.path.join(outdir, f'{kit.slug}.glb')
    export_glb(kit, sheets, glb_path)
    sj = steps_json(kit, sheets)
    json.dump(sj, open(os.path.join(outdir, f'{kit.slug}_steps.json'), 'w'), indent=1)
    # report
    sheet_rows = []
    for sh, sp in zip(sheets, sps):
        sheet_rows.append({'sheet': sh.letter, 'color': sh.color, 'tile': sh.tile, 'fraction': sh.fraction,
                           'parts': len([p for p in sh.placed if not p.spare]),
                           'spares': len([p for p in sh.placed if p.spare]),
                           'used_pct': round(100 * sum(p.xf(p.part.outline()).area for p in sh.placed) /
                                             (sh.W * sh.H), 1), **sp.stats})
    laser_s = sum(r['total_s'] for r in sheet_rows)
    sheet_eq = sum(sh.fraction for sh in sheets)
    swap_s = sheet_eq / C.SHEETS_PER_JOB * C.SHEET_SWAP_S
    nat = sum(sh.fraction for sh in sheets if sh.color == 'natural')
    col = sheet_eq - nat
    mat_cost = nat * C.SHEET_COST['natural'] + col * C.SHEET_COST['colored']
    report.update({
        'pieces': len(kit.parts), 'unique_codes': len({p.code for p in kit.parts}),
        'hardware': [{'name': h.name, 'kind': h.kind, 'note': h.note} for h in kit.hardware],
        'extras': kit.extras,
        'sheets': sheet_rows, 'jobs': jobs, 'n_sheets': len(sheets), 'sheet_equivalents': round(sheet_eq, 2),
        'sheets_by_color': {c: sum(1 for s in sheets if s.color == c) for c in sorted({s.color for s in sheets})},
        'laser_minutes': round(laser_s / 60, 1), 'swap_minutes': round(swap_s / 60, 1),
        'cut_minutes_per_kit': round((laser_s + swap_s) / 60, 1),
        'wood_cost_usd': round(mat_cost, 2),
        'mechanism_parts': sorted({p.code for p in kit.parts if p.mechanism}),
        'color_mode': mode,
        'build_seconds': round(time.time() - t0, 1),
    })
    if mode == 'print':
        fr = [p['front'] for p in prints if p.get('front')]
        bk = [p['back'] for p in prints if p.get('back')]
        report['print'] = {
            'sheets': prints, 'printed_sheet_sides': len(fr) + len(bk),
            'print_minutes': round(sum(x['minutes'] for x in fr + bk), 1),
            'ink_usd': round(sum(x['ink_usd'] for x in fr + bk), 2),
            'two_sided_parts': sorted({p.code for p in kit.parts if p.__dict__.get('print_back')}),
            'colored_parts': sum(1 for p in kit.parts if p.color != 'natural')}
        log(f"  print: {len(fr)} front + {len(bk)} back sides, about {report['print']['print_minutes']} min printing, "
            f"ink ${report['print']['ink_usd']}")
    if run_checks:
        report['all_checks_pass'] = all(r['pass'] for r in report['checks']) and not probs
    json.dump(report, open(os.path.join(outdir, f'{kit.slug}_report.json'), 'w'), indent=1, default=str)
    log(f"  {report['pieces']} pieces, {len(sheets)} sheets ({sheet_eq:.2f} full-sheet equivalents), laser {report['laser_minutes']} min "
        f"(+{report['swap_minutes']} min sheet swaps), wood ${report['wood_cost_usd']}")
    return report, sheets, sps
