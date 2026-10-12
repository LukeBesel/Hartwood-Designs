"""Prove every check works: the clean model passes, and each deliberately broken model fails
the right check. Run:  ../.venv/bin/python -m pytest tests/test_checks.py   (from engine/)
or simply:            ../.venv/bin/python tests/test_checks.py  (also writes review/check_proofs.md)
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from shapely.geometry import LineString  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

from hartwood import checks  # noqa: E402
from hartwood import popout as PO  # noqa: E402
from hartwood.cutfiles import sheet_paths  # noqa: E402
from hartwood.geom import circle, rect, translate  # noqa: E402
from hartwood.nest import assign_codes, nest  # noqa: E402
from kits import proofbox  # noqa: E402

NAMES = ('Collision check', 'Nothing-floats check', 'Assembly path check', 'Minimum feature check', 'Pop-out check')


def results(k, sheet_hook=None):
    r = {x['name']: x for x in checks.run_all(k)}
    PO.mating_edges(k)
    sheets = nest(k.parts)
    assign_codes(sheets, k.name)
    if sheet_hook:
        sheet_hook(sheets)
    sps = [sheet_paths(sh) for sh in sheets]
    r['Pop-out check'] = PO.check_popout(sheets, sps)
    return r


def clean():
    return results(proofbox.build())


def broken_collision():
    k = proofbox.build()
    w = k.by_name('wall1')
    w.mat = translate(0, 0, -6) @ w.mat          # push the wall 6 mm into the spacers
    return results(k)


def broken_float():
    k = proofbox.build()
    s = k.by_name('slice3')
    s.mat = translate(0, 30, 0) @ s.mat          # lift the top slice 30 mm into the air
    return results(k)


def broken_path():
    k = proofbox.build()
    wheel = k.by_name('wheel')
    wheel.insert = (0, 0, -1)                    # try to push the wheel in sideways through a wall
    return results(k)


def broken_feature():
    k = proofbox.build()
    f = k.by_name('floor')
    f.cuts.append((circle(0, -27.0 + 0.0, 1.8), 'press'))   # hole 1.2 mm from the floor edge
    return results(k)


def broken_two_pieces():
    k = proofbox.build()
    f = k.by_name('floor')
    f.shape = unary_union([f.shape, rect(60, 60, 70, 70)])      # a loose square, 'part' of the floor
    return results(k)


def broken_nested():
    k = proofbox.build()
    f = k.by_name('floor')
    f.cuts.append((circle(0, 0, 14.0), 'press'))                  # a big hole in the floor

    def hook(sheets):
        for sh in sheets:
            host = next((pl for pl in sh.placed if pl.part.name == 'floor'), None)
            if host is None:
                continue
            small = min((pl for pl in sh.placed if pl is not host), key=lambda pl: pl.part.outline().area)
            hc = host.xf(circle(0, 0, 14.0)).centroid
            sc = small.xf(small.part.outline()).centroid
            small.dx += hc.x - sc.x; small.dy += hc.y - sc.y          # drop a small part into the hole
            return
    return results(k, hook)


def broken_bridge():
    k = proofbox.build()
    real = PO.choose_bridges

    def on_the_tab(poly, nogo, n, soft=None, spacing=0.4):
        if nogo is None or nogo.is_empty:
            return real(poly, nogo, n, soft, spacing)
        ring = LineString(poly.exterior.coords)
        return [(ring.project(nogo.centroid), 0)]                 # bridge right on a sliding edge
    PO.choose_bridges = on_the_tab
    try:
        return results(k)
    finally:
        PO.choose_bridges = real


CASES = [
    ('Clean model', clean, None),
    ('Wall pushed 6 mm into the spacers', broken_collision, 'Collision check'),
    ('Top slice lifted 30 mm', broken_float, 'Nothing-floats check'),
    ('Wheel pushed in sideways through a wall', broken_path, 'Assembly path check'),
    ('Hole drilled 1.2 mm from the floor edge', broken_feature, 'Minimum feature check'),
    ('Floor cut as two separate pieces', broken_two_pieces, 'Minimum feature check'),
    ('Small part nested in a hole of the floor', broken_nested, 'Pop-out check'),
    ('Bridge forced onto a sliding edge (tab)', broken_bridge, 'Pop-out check'),
]


def test_clean_passes():
    r = clean()
    assert all(v['pass'] for v in r.values()), {k: v['summary'] for k, v in r.items()}


def test_collision_caught():
    assert not broken_collision()['Collision check']['pass']


def test_float_caught():
    assert not broken_float()['Nothing-floats check']['pass']


def test_path_caught():
    assert not broken_path()['Assembly path check']['pass']


def test_feature_caught():
    assert not broken_feature()['Minimum feature check']['pass']


def test_two_pieces_caught():
    assert not broken_two_pieces()['Minimum feature check']['pass']


def test_nested_caught():
    assert not broken_nested()['Pop-out check']['pass']


def test_bridge_caught():
    assert not broken_bridge()['Pop-out check']['pass']


if __name__ == '__main__':
    rows = []
    ok_all = True
    for label, fn, expect_fail in CASES:
        r = fn()
        line = []
        for name in NAMES:
            v = r[name]
            line.append('PASS' if v['pass'] else 'FAIL')
        if expect_fail is None:
            good = all(v['pass'] for v in r.values())
        else:
            good = not r[expect_fail]['pass']
        ok_all &= good
        detail = '' if expect_fail is None else r[expect_fail]['summary']
        rows.append((label, *line, 'yes' if good else 'NO', detail))
        print(label, line, 'caught' if good else 'MISSED', detail)
    out = os.path.join(HERE, '..', '..', 'review', 'check_proofs.md')
    with open(out, 'w') as f:
        f.write('# Proof that the checks work\n\n')
        f.write('Test model: `engine/kits/proofbox.py` (uses every joint type: tab in hole, cross half-lap, '
                'slices on a key, discs on a dowel). Each row breaks one thing on purpose.\n\n')
        f.write('| Case | Collision | Nothing floats | Assembly path | Min feature | Pop-out | Caught as expected? | What the check said |\n')
        f.write('|---|---|---|---|---|---|---|---|\n')
        for r in rows:
            f.write('| ' + ' | '.join(r) + ' |\n')
        f.write(f'\nAll cases behave as expected: **{"yes" if ok_all else "NO"}**. '
                'Re-run with `cd engine && ../.venv/bin/python tests/test_checks.py`.\n')
    sys.exit(0 if ok_all else 1)
