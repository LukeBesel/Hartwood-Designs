"""Capacity model: kits per shift and per week at 1, 2 and 3 shifts, and the bottleneck, for both color methods.

    .venv/bin/python tools/make_capacity.py   ->  production/capacity.md, production/capacity.png
"""
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
KITS = ['blaster', 'dragon', 'floral']
NAMES = {'blaster': 'Star Slinger', 'dragon': 'Emberwing', 'floral': 'Blossom Waltz'}
MIX = {'blaster': 6, 'dragon': 5, 'floral': 6}          # launch plan per week (Estimate), also the product mix
SHIFT_MIN = 8 * 60
EFF = {'laser': 0.85, 'printer': 0.85, 'pack': 0.80}     # Estimate: warm-up, cleaning, breaks, changeovers
PACK_MIN = 6.0                                            # Estimate: hands-on per kit that cannot overlap a cut
DAYS = 5
SERIES = ['#2a78d6', '#eb6834', '#1baf7a']


def per_kit(mode):
    out = {}
    for k in KITS:
        base = os.path.join(ROOT, 'kits', k)
        r = json.load(open(os.path.join(base, 'print_mode' if mode == 'print' else '', f'{k}_report.json')))
        out[k] = {'laser': r['cut_minutes_per_kit'], 'print': r.get('print', {}).get('print_minutes', 0.0),
                  'print_one_side': sum(s['front']['minutes'] for s in r.get('print', {}).get('sheets', []) if s.get('front'))}
    return out


def lower_first(name):
    """'Laser (attended)' -> 'laser (attended)', but keep 'UV printer' as it is."""
    return name if name[:2].isupper() else name[0].lower() + name[1:]


def short(name):
    """Legend name without brackets: 'UV printer (both sides)' -> 'UV printer, both sides'."""
    return lower_first(name).replace(' (', ', ').replace(')', '')


def mix_avg(d, key):
    n = sum(MIX.values())
    return sum(d[k][key] * MIX[k] for k in KITS) / n


def main():
    rows, lines = [], []
    res = {}
    for mode in ('sheets', 'print'):
        d = per_kit(mode)
        laser = mix_avg(d, 'laser')
        stations = {'Laser (attended)': laser / EFF['laser'], 'Packing bench': PACK_MIN / EFF['pack']}
        if mode == 'print':
            stations['UV printer (both sides)'] = mix_avg(d, 'print') / EFF['printer']
            stations['UV printer (show face only)'] = mix_avg(d, 'print_one_side') / EFF['printer']
        res[mode] = (d, stations)
    L = ['# Capacity model', '',
         'One OMTech Polar 2, one person per shift, 8-hour shifts, 5 days a week. All numbers are **Estimate**: laser minutes come from the engine '
         '(planning speeds in `engine/hartwood/config.py`; measure real speeds with the coupon speed ladder). Efficiency allows for warm-up, '
         f"cleaning, breaks and changeovers: laser {int(EFF['laser'] * 100)}%, printer {int(EFF['printer'] * 100)}%, packing {int(EFF['pack'] * 100)}%. "
         f"Product mix = the launch plan ({MIX['blaster']} Star Slinger : {MIX['dragon']} Emberwing : {MIX['floral']} Blossom Waltz).", '',
         '## Minutes per kit', '', '| Kit | Laser + sheet swaps (sheets) | Laser (UV print) | UV printing both sides | UV printing show face only |',
         '|---|---|---|---|---|']
    for k in KITS:
        a = res['sheets'][0][k]; b = res['print'][0][k]
        L.append(f"| {NAMES[k]} | {a['laser']:.1f} | {b['laser']:.1f} | {b['print']:.1f} | {b['print_one_side']:.1f} |")
    L += ['', '## Kits per shift and per week (each station alone; the smallest number is the bottleneck)', '',
          '| Color method | Station | Min per kit (mix, at efficiency) | Kits per shift | Kits per week, 1 shift | 2 shifts | 3 shifts |',
          '|---|---|---|---|---|---|---|']
    chart = []
    for mode, label in (('sheets', 'Pre-colored sheets'), ('print', 'UV-printed color')):
        stations = res[mode][1]
        for st, m in stations.items():
            per_shift = SHIFT_MIN / m
            L.append(f"| {label} | {st} | {m:.1f} | {per_shift:.0f} | {per_shift * DAYS:.0f} | {2 * per_shift * DAYS:.0f} | {3 * per_shift * DAYS:.0f} |")
        core = {k: v for k, v in stations.items() if 'show face' not in k}
        bott = max(core, key=core.get)
        cap = SHIFT_MIN / core[bott] * DAYS
        chart.append((label, cap, bott))
        lines.append(f"- **{label}:** the bottleneck is the {lower_first(bott)}, about **{cap:.0f} kits a week on one shift**, {2 * cap:.0f} on two, {3 * cap:.0f} on three.")
    demand = sum(MIX.values())
    L += ['', '## Bottleneck', ''] + lines + [
        f'- **Launch demand is {demand} kits a week**, so one shift on 1 to 2 days a week covers it. The rest of the time is for website, marketing and new designs.',
        '- **The laser is the bottleneck with pre-colored sheets.** It must be attended while it runs (fire rule). Packing happens at the bench beside it during each cut, so it does not add time.',
        '- **With UV printing, the printer becomes the bottleneck when both sides are printed** (the floral kit needs 43 min). Print the show face only (`two_sided = False`), buy the dual-head model, or run the printer in a second shift without the laser. A UV-LED printer has no open flame like the laser, but check the maker\'s manual before leaving it alone.',
        '- **3 shifts** need two more people and a laser that runs 24 h. CO2 glass tubes are commonly quoted at a few thousand hours (Estimate), so budget a spare tube once you pass 2 shifts.',
        '', '![Capacity](capacity.png)', '',
        'How to grow: (1) measure the real cut speed (it may be faster than 30 mm/s); (2) a second laser doubles laser capacity for about $3,700; '
        '(3) a parts-per-sheet review on the engine (tighter nesting) cuts minutes per kit directly.']
    open(os.path.join(ROOT, 'production', 'capacity.md'), 'w').write('\n'.join(L) + '\n')

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
    fig, ax = plt.subplots(figsize=(9, 3.6), dpi=150)
    fig.patch.set_facecolor('#fcfcfb'); ax.set_facecolor('#fcfcfb')
    xs = range(3)
    for j, (label, cap, bott) in enumerate(chart):
        ys = [cap * s for s in (1, 2, 3)]
        bars = ax.bar([x + (j - 0.5) * 0.36 for x in xs], ys, width=0.34, color=SERIES[j], edgecolor='#fcfcfb', linewidth=2,
                      label=f'{label}: limited by the {short(bott)}')
        for b, y in zip(bars, ys):
            ax.text(b.get_x() + b.get_width() / 2, y + 6, f'{y:.0f}', ha='center', fontsize=10, color='#52514e')
    ax.axhline(demand, color='#52514e', linewidth=1.2, linestyle=(0, (4, 3)), label=f'Launch demand: {demand} kits a week')
    ax.set_xticks(list(xs)); ax.set_xticklabels(['1 shift', '2 shifts', '3 shifts'])
    ax.set_ylabel('Kits per week'); ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', color='#e7e5df', linewidth=0.8); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, loc='upper left')
    ax.set_title('Weekly capacity, one laser (Estimate)', loc='left', fontsize=13)
    fig.tight_layout(); fig.savefig(os.path.join(ROOT, 'production', 'capacity.png')); plt.close(fig)
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
