"""Build a kit end to end:  ../.venv/bin/python run_kit.py floral [--no-checks] [--print]

--print builds the UV-printed color version (all parts on natural sheets plus print files) into
kits/<kit>/print_mode/ instead of kits/<kit>/.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hartwood import config as C  # noqa: E402
from hartwood.build import build  # noqa: E402

name = sys.argv[1]
mode = 'print' if '--print' in sys.argv else C.COLOR_MODE
mod = __import__(f'kits.{name}', fromlist=['build'])
t = time.time()
kit = mod.build()
print(f'{kit.name}: {len(kit.parts)} parts, {len(kit.hardware)} hardware, designed in {time.time() - t:.1f}s ({mode} color)')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kits', name)
if mode == 'print' and C.COLOR_MODE != 'print':
    out = os.path.join(out, 'print_mode')
build(kit, out, run_checks='--no-checks' not in sys.argv, color_mode=mode)
