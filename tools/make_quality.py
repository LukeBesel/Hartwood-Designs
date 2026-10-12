"""Quality loop pictures: the starting Pareto (competitor complaints from review mining) and the loop diagram.

    .venv/bin/python tools/make_quality.py   ->  production/quality/pareto_start.png, production/quality/loop.png
"""
import os
import re
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker  # noqa: F401

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'production', 'quality')
BLUE = '#2a78d6'                      # first color of the validated categorical palette (single series)
INK, INK2, GRID, BG = '#2b2a28', '#52514e', '#e7e5df', '#fcfcfb'


def complaints():
    rows = []
    in_table = False
    for line in open(os.path.join(ROOT, 'research', 'review_mining.md')):
        if line.startswith('## What buyers hate'):
            in_table = True
            continue
        if in_table and line.startswith('## '):
            break
        m = re.match(r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|', line)
        if in_table and m:
            rows.append((m.group(2), int(m.group(3))))
    return rows


def pareto(rows):
    short = {'Mechanism does not work reliably (jams, stalls, stops)': 'Mechanism jams or stalls',
             'Tight or hard fit (needs force, sanding, honing)': 'Too tight, needs sanding',
             'Parts break during build or removal': 'Parts break',
             'Unclear instructions or easy-to-miss steps': 'Unclear instructions',
             'Wax and friction (missing wax, too much wax)': 'Wax and friction',
             'Support and replacement parts': 'Support and spare parts',
             'Fiddly small parts': 'Fiddly small parts',
             'Missing or loose components': 'Missing or loose parts'}
    rows = sorted(rows, key=lambda r: -r[1])
    total = sum(n for _, n in rows)
    labels = [short.get(a, a) for a, _ in rows]
    vals = [n for _, n in rows]
    cum, c = [], 0
    for v in vals:
        c += v
        cum.append(100.0 * c / total)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    y = list(range(len(vals)))[::-1]
    ax.barh(y, vals, height=0.62, color=BLUE, edgecolor=BG, linewidth=2)
    for yi, v, cu in zip(y, vals, cum):
        ax.text(v + 0.25, yi, f'{v}   (cumulative {cu:.0f}%)', va='center', fontsize=10, color=INK2)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=INK)
    ax.set_xlabel('Mentions in buyer reviews of other brands (52 in total)', color=INK2)
    ax.set_xlim(0, max(vals) * 1.55)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title('Starting Pareto: what wooden kit buyers complain about', loc='left', fontsize=13, color=INK)
    fig.text(0.01, 0.01, 'Source: research/review_mining.md (reviews of ROKR, Ugears and others, checked 2026-10-11). Fix the top 3 first: they are 69%.',
             fontsize=8.5, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(os.path.join(OUT, 'pareto_start.png'))
    plt.close(fig)


def loop():
    steps = [('1  Find', 'checks at every station\nand customer messages'), ('2  Log', 'Quality tab: kit, part\ncode, problem, count'),
             ('3  Pareto', 'every Friday, last\n4 weeks'), ('4  Fix the top bar', 'one change at a time,\nwritten in the change log'),
             ('5  Check', 'did the bar shrink\nthe next weeks?'), ('6  Lock it in', 'engine setting, SOP or\nbooklet step updated')]
    import math
    W, H, R = 900, 520, 185
    cx, cy = W / 2, H / 2 + 6
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         '<defs><marker id="h" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#0F8B7F"/></marker></defs>',
         f'<rect width="{W}" height="{H}" fill="#FCF8F1"/>',
         f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#D7EFEB" stroke-width="18"/>',
         f'<text x="{cx}" y="{cy - 6}" font-family="Fraunces, Georgia, serif" font-size="26" font-weight="700" fill="#3A2A1F" text-anchor="middle">Quality loop</text>',
         f'<text x="{cx}" y="{cy + 20}" font-family="Inter, Arial, sans-serif" font-size="14" fill="#5C4636" text-anchor="middle">15 minutes every Friday</text>']
    n = len(steps)
    for i in range(n):
        a2 = -math.pi / 2 + 2 * math.pi * (i + 1) / n - 0.24
        a1 = -math.pi / 2 + 2 * math.pi * i / n + 0.24
        x1, y1 = cx + R * math.cos(a1), cy + R * math.sin(a1)
        x2, y2 = cx + R * math.cos(a2), cy + R * math.sin(a2)
        s.append(f'<path d="M{x1:.1f},{y1:.1f} A{R},{R} 0 0,1 {x2:.1f},{y2:.1f}" fill="none" stroke="#0F8B7F" stroke-width="4" marker-end="url(#h)"/>')
    for i, (t, sub) in enumerate(steps):
        a = -math.pi / 2 + 2 * math.pi * i / n
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        w, h = 210, 70
        s.append(f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w}" height="{h}" rx="14" fill="#fff" stroke="#3A2A1F" stroke-width="2"/>')
        s.append(f'<text x="{x:.1f}" y="{y - 12:.1f}" font-family="Inter, Arial, sans-serif" font-size="16" font-weight="800" fill="#0B6158" text-anchor="middle">{t}</text>')
        for j, ln in enumerate(sub.split('\n')):
            s.append(f'<text x="{x:.1f}" y="{y + 8 + j * 16:.1f}" font-family="Inter, Arial, sans-serif" font-size="13" fill="#5C4636" text-anchor="middle">{ln}</text>')
    s.append('</svg>')
    svg = os.path.join(OUT, 'loop.svg')
    open(svg, 'w').write('\n'.join(s))
    fonts = os.path.join(ROOT, 'brand', 'fonts')
    html = os.path.join(OUT, '_tmp.html')
    open(html, 'w').write(f"""<html><head><style>@font-face{{font-family:Fraunces;src:url(file://{fonts}/Fraunces-700.ttf);font-weight:700}}
@font-face{{font-family:Inter;src:url(file://{fonts}/Inter-400.ttf);font-weight:400}}@font-face{{font-family:Inter;src:url(file://{fonts}/Inter-800.ttf);font-weight:800}}
body{{margin:0}}</style></head><body>{open(svg).read()}</body></html>""")
    subprocess.run(['node', os.path.join(ROOT, 'tools', 'shot.js'), html, os.path.join(OUT, 'loop.png'), str(W), str(H), '0', 'light', '300'], check=True)
    os.remove(html)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    rows = complaints()
    assert sum(n for _, n in rows) == 52, rows
    pareto(rows)
    loop()
    print('quality pictures written')
