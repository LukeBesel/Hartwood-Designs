"""Build a kit end to end:  ../.venv/bin/python run_kit.py floral [--no-checks]"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hartwood.build import build  # noqa: E402

name = sys.argv[1]
mod = __import__(f'kits.{name}', fromlist=['build'])
t = time.time()
kit = mod.build()
print(f'{kit.name}: {len(kit.parts)} parts, {len(kit.hardware)} hardware, designed in {time.time() - t:.1f}s')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kits', name)
build(kit, out, run_checks='--no-checks' not in sys.argv)
