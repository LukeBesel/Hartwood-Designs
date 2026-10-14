"""Update wood cost in every kit report from the current sheet prices (no re-nesting).

    .venv/bin/python tools/recost.py
"""
import glob
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'engine'))
from hartwood import config as C  # noqa: E402

for p in glob.glob(os.path.join(ROOT, 'kits', '*', '*_report.json')) + glob.glob(os.path.join(ROOT, 'kits', '*', 'print_mode', '*_report.json')):
    r = json.load(open(p))
    if 'sheets' not in r:
        continue
    wood = sum(s['fraction'] * C.SHEET_COST['natural' if s['color'] == 'natural' else 'colored'] for s in r['sheets'])
    r['wood_cost_usd'] = round(wood, 2)
    json.dump(r, open(p, 'w'), indent=1, default=str)
    print(os.path.relpath(p, ROOT), r['wood_cost_usd'])
