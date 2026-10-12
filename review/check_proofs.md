# Proof that the checks work

Test model: `engine/kits/proofbox.py` (uses every joint type: tab in hole, cross half-lap, slices on a key, discs on a dowel). Each row breaks one thing on purpose.

| Case | Collision | Nothing floats | Assembly path | Min feature | Pop-out | Caught as expected? | What the check said |
|---|---|---|---|---|---|---|---|
| Clean model | PASS | PASS | PASS | PASS | PASS | yes |  |
| Wall pushed 6 mm into the spacers | FAIL | PASS | FAIL | PASS | PASS | yes | 2 overlapping pairs |
| Top slice lifted 30 mm | PASS | FAIL | PASS | PASS | PASS | yes | 1 floating, 2 separate pieces |
| Wheel pushed in sideways through a wall | PASS | PASS | FAIL | PASS | PASS | yes | 1 blocked insertions |
| Hole drilled 1.2 mm from the floor edge | PASS | PASS | PASS | FAIL | PASS | yes | 1 problems: parts in several pieces or features thinner than 2.5 mm |
| Floor cut as two separate pieces | PASS | PASS | PASS | FAIL | PASS | yes | 1 problems: parts in several pieces or features thinner than 2.5 mm |
| Small part nested in a hole of the floor | PASS | PASS | PASS | PASS | FAIL | yes | 1 pop-out problems |
| Bridge forced onto a sliding edge (tab) | PASS | PASS | PASS | PASS | FAIL | yes | 4 pop-out problems |

All cases behave as expected: **yes**. Re-run with `cd engine && ../.venv/bin/python tests/test_checks.py`.
