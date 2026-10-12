#!/usr/bin/env bash
# Rebuild everything from the kit designs: checks, cut files, print files, renders, part images,
# booklets, kit pages and the website. Run from the project folder:  bash tools/rebuild_all.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
for k in blaster dragon floral; do
  (cd engine && ../$PY run_kit.py $k)                 # 5 design checks + cut files (COLOR_MODE in config)
  (cd engine && ../$PY run_kit.py $k --print --no-checks) || true   # UV-print version (skipped if already the default)
  $PY engine/render_kit.py $k                         # hero renders + one image per part code
  $PY engine/booklet.py $k                            # PDF + Word booklet with QR codes
done
(cd engine && ../$PY tests/test_checks.py)            # proof that every check catches a deliberate break
$PY engine/kit_summary.py
$PY engine/concepts.py
$PY tools/build_site.py
$PY tools/build_pages.py
$PY tools/make_supply.py                              # BOM, suppliers, reorder points, economics
$PY tools/make_planner_data.py                        # data for the workshop planner
$PY tools/make_capacity.py
$PY tools/make_quality.py
$PY tools/make_layout.py
$PY tools/make_sops.py                                # six SOPs as HTML + PDF
$PY brand/make_packaging.py                           # labels, sleeve, mockups
echo "done: open website/ with  node tools/serve.js  and check START_HERE.html"
