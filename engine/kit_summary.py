"""Write kits/<kit>/README.md from the build report (pieces, checks, sheets, cut time, wood cost, files).

    python engine/kit_summary.py
"""
from __future__ import annotations

import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
KITS = ['blaster', 'dragon', 'floral']
VIEW_ORDER = ['three_quarter', 'front', 'side', 'back', 'top']


def summary(kit):
    d = os.path.join(ROOT, 'kits', kit)
    r = json.load(open(os.path.join(d, f'{kit}_report.json')))
    s = json.load(open(os.path.join(d, f'{kit}_steps.json')))
    renders = sorted(f for f in os.listdir(os.path.join(d, 'renders')) if f.endswith('.jpg'))
    renders = sorted(renders, key=lambda f: (f.startswith('closeup'), VIEW_ORDER.index(f[:-4]) if f[:-4] in VIEW_ORDER else 9, f))
    L = [f"# {r['name']}", '', f"_{s['tagline']}_", '', s['story'], '',
         f"![{r['name']}](renders/{renders[0]})", '',
         '## At a glance', '',
         '| Item | Value |', '|---|---|',
         f"| Pieces (wood) | {r['pieces']} ({r['unique_codes']} different shapes) |",
         f"| Build steps | {len(s['steps'])} |",
         f"| Difficulty | {s['difficulty']} of 5, about {s['build_hours']} |",
         f"| Sheets | {r['n_sheets']} cut sheets = {r['sheet_equivalents']} full 12 x 12 in sheet equivalents ({', '.join(f'{v} {k}' for k, v in r['sheets_by_color'].items())}) |",
         f"| Laser time per kit | {r['laser_minutes']} min cutting + {r['swap_minutes']} min sheet swaps = **{r['cut_minutes_per_kit']} min** (Estimate, planning speeds) |",
         f"| Wood cost per kit | **${r['wood_cost_usd']:.2f}** (Estimate, sheet prices in `engine/hartwood/config.py`) |",
         f"| Target price | ${s['price']} |",
         f"| Extras in the box | {'; '.join(f'{k} x{v}' for k, v in s['extras'].items())} |",
         '', '## Design checks', '', '| Check | Result |', '|---|---|']
    for c in r['checks']:
        L.append(f"| {c['name']} | {'PASS' if c['pass'] else 'FAIL'}: {c['summary']} |")
    frag = r['checks'][3].get('fragile', [])
    if frag:
        L += ['', f"Fragile-part report: {len(frag)} small or thin parts, each cut with a spare: " +
              ', '.join(sorted({f['part'].rsplit('_peg', 1)[0] + ('_peg' if '_peg' in f['part'] else '') for f in frag}))[:600] + '.']
    if r['mechanism_parts']:
        L += ['', f"Mechanism parts marked **needs physical test**: {', '.join(r['mechanism_parts'])}."]
        if os.path.exists(os.path.join(d, 'mechanism_test_plan.md')):
            L.append('See [mechanism_test_plan.md](mechanism_test_plan.md).')
    L += ['', '## Sheets', '', '| Sheet | Color | Size | Parts | Spares | Used | Laser min |', '|---|---|---|---|---|---|---|']
    for sh in r['sheets']:
        L.append(f"| {sh['sheet']} | {sh['color']} | {sh['tile']} | {sh['parts']} | {sh['spares']} | {sh['used_pct']}% | {sh['total_s'] / 60:.1f} |")
    L += ['', 'Half and quarter tiles are cut 2 or 4 at a time on one 12 x 12 sheet (files ending `_x2_full` or `_x4_full`).',
          '', '## Files', '',
          f"- `cutfiles/`: one SVG, DXF and LightBurn file per sheet, plus `*_job*_bed` files that put two sheets on the 710 x 360 mm bed.",
          f"- `parts_map/`: a picture of each sheet with every part code (for the booklet and for packing).",
          f"- `parts/`: one picture per part code ({len(os.listdir(os.path.join(d, 'parts')))} images).",
          f"- `{kit}.glb`: the 3D model for the instruction app (one node per part).",
          f"- `{kit}_steps.json`: steps, parts per step, tips and tests.",
          f"- `{kit}_report.json`: the full build report.",
          '', '## Renders', '']
    for f in renders:
        L.append(f"![{f[:-4]}](renders/{f})")
    open(os.path.join(d, 'README.md'), 'w').write('\n'.join(L) + '\n')
    return {'kit': kit, 'name': r['name'], 'pieces': r['pieces'], 'steps': len(s['steps']),
            'sheet_equivalents': r['sheet_equivalents'], 'cut_minutes': r['cut_minutes_per_kit'],
            'wood_cost': r['wood_cost_usd'], 'price': s['price'], 'all_checks_pass': r['all_checks_pass'],
            'checks': {c['name']: c['pass'] for c in r['checks']}}


if __name__ == '__main__':
    rows = [summary(k) for k in KITS]
    json.dump(rows, open(os.path.join(ROOT, 'kits', 'kits_summary.json'), 'w'), indent=1)
    for row in rows:
        print(row)
