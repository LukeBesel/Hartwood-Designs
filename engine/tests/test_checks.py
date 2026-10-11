"""Prove every check works: the clean model passes, and each deliberately broken model fails
the right check. Run:  ../.venv/bin/python -m pytest tests/test_checks.py   (from engine/)
or simply:            ../.venv/bin/python tests/test_checks.py  (also writes review/check_proofs.md)
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from hartwood import checks  # noqa: E402
from hartwood.geom import circle, translate  # noqa: E402
from kits import proofbox  # noqa: E402


def results(k):
    return {r['name']: r for r in checks.run_all(k)}


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


CASES = [
    ('Clean model', clean, None),
    ('Wall pushed 6 mm into the spacers', broken_collision, 'Collision check'),
    ('Top slice lifted 30 mm', broken_float, 'Nothing-floats check'),
    ('Wheel pushed in sideways through a wall', broken_path, 'Assembly path check'),
    ('Hole drilled 1.2 mm from the floor edge', broken_feature, 'Minimum feature check'),
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


if __name__ == '__main__':
    rows = []
    ok_all = True
    for label, fn, expect_fail in CASES:
        r = fn()
        line = []
        for name in ('Collision check', 'Nothing-floats check', 'Assembly path check', 'Minimum feature check'):
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
        f.write('| Case | Collision | Nothing floats | Assembly path | Min feature | Caught as expected? | What the check said |\n')
        f.write('|---|---|---|---|---|---|---|\n')
        for r in rows:
            f.write('| ' + ' | '.join(r) + ' |\n')
        f.write(f'\nAll cases behave as expected: **{"yes" if ok_all else "NO"}**. '
                'Re-run with `cd engine && ../.venv/bin/python tests/test_checks.py`.\n')
    sys.exit(0 if ok_all else 1)
