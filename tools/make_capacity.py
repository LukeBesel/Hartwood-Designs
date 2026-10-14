"""Capacity model: takt time, kits per day, week and month at 1, 2 and 3 shifts, and where the bottleneck moves
(laser, UV printer, or you).

    .venv/bin/python tools/make_capacity.py   ->  production/capacity.md, capacity.png, capacity_bottleneck.png
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
DAYS = 5
WEEKS_PER_MONTH = 52 / 12
EFF = {'laser': 0.85, 'printer': 0.85, 'you': 0.85}      # Estimate: warm-up, cleaning, breaks, changeovers
CHECK_MIN = 3.0       # Estimate: unload and pop-out check per laser job (SOP-3); loading is in the laser's sheet-swap time
PACK_MIN = 6.0        # Estimate: kitting and packing per kit (SOP-4), the same 6 min as the cost model
SHIP_MIN = 2.0        # Estimate: label, tape, planner (SOP-7)
SERIES = ['#2a78d6', '#eb6834', '#1baf7a']
INK2, GRID, BG = '#52514e', '#e7e5df', '#fcfcfb'


def per_kit(mode):
    out = {}
    for k in KITS:
        base = os.path.join(ROOT, 'kits', k)
        r = json.load(open(os.path.join(base, 'print_mode' if mode == 'print' else '', f'{k}_report.json')))
        jobs = sum(1.0 / min(j['kits_per_sheet']) for j in r['jobs'])      # laser jobs per kit (tiles serve 2 or 4 kits)
        out[k] = {'laser': r['cut_minutes_per_kit'], 'print': r.get('print', {}).get('print_minutes', 0.0),
                  'print_one_side': sum(s['front']['minutes'] for s in r.get('print', {}).get('sheets', []) if s.get('front')),
                  'jobs': jobs, 'you': jobs * CHECK_MIN + PACK_MIN + SHIP_MIN}
    return out


def mix_avg(d, key):
    n = sum(MIX.values())
    return sum(d[k][key] * MIX[k] for k in KITS) / n


def per_week(min_per_kit, shifts=1):
    return SHIFT_MIN / min_per_kit * DAYS * shifts


def main():
    res = {}
    for mode in ('sheets', 'print'):
        d = per_kit(mode)
        st = {'Laser (attended)': mix_avg(d, 'laser') / EFF['laser'], 'You (check, pack, ship)': mix_avg(d, 'you') / EFF['you']}
        if mode == 'print':
            st['UV printer (both sides)'] = mix_avg(d, 'print') / EFF['printer']
            st['UV printer (show face only)'] = mix_avg(d, 'print_one_side') / EFF['printer']
        res[mode] = (d, st)
    demand = sum(MIX.values())
    laser_s = res['sheets'][1]['Laser (attended)']
    you_s = res['sheets'][1]['You (check, pack, ship)']
    L = ['# Capacity model', '',
         'One OMTech Polar 2, 8-hour shifts, 5 days a week. All numbers are **Estimate**: laser minutes come from the engine '
         '(planning speeds in `engine/hartwood/config.py`; measure real speeds with the coupon speed ladder). Hands-on times are '
         f'{CHECK_MIN:g} min to unload and check each laser job, {PACK_MIN:g} min to pack and {SHIP_MIN:g} min to ship each kit. '
         f"Efficiency allows for warm-up, cleaning, breaks and changeovers: {int(EFF['laser'] * 100)}%. "
         f"Product mix = the launch plan ({MIX['blaster']} Star Slinger : {MIX['dragon']} Emberwing : {MIX['floral']} Blossom Waltz).", '',
         '## Takt time', '',
         f'Launch demand is **{demand} kits a week** (Estimate). If you cut on **one day a week**, takt time = {SHIFT_MIN} min / {demand} kits = '
         f'**{SHIFT_MIN / demand:.0f} min per kit**. The laser needs {laser_s:.0f} min per kit and your hands-on work {you_s:.0f} min, '
         f'so one cutting day a week meets launch demand. On five days a week the takt time is {SHIFT_MIN * DAYS / demand:.0f} min per kit: '
         'there is lots of room to grow.', '',
         '## Minutes per kit', '',
         '| Kit | Laser jobs per kit | Laser + sheet swaps | You: check, pack, ship | Laser (UV print) | UV printing both sides | UV printing show face only |',
         '|---|---|---|---|---|---|---|']
    for k in KITS:
        a = res['sheets'][0][k]; b = res['print'][0][k]
        L.append(f"| {NAMES[k]} | {a['jobs']:.1f} | {a['laser']:.1f} | {a['you']:.1f} | {b['laser']:.1f} | {b['print']:.1f} | {b['print_one_side']:.1f} |")
    L += ['', 'Half and quarter color tiles serve 2 or 4 kits per job, so a kit can need a fraction of a job.', '',
          '## Kits per day, week and month (each station alone; the smallest number is the bottleneck)', '',
          '| Color method | Station | Min per kit (mix, at efficiency) | Per day, 1 shift | Per week, 1 shift | Per month, 1 shift | Per month, 2 shifts | Per month, 3 shifts |',
          '|---|---|---|---|---|---|---|---|']
    chart, lines = [], []
    for mode, label in (('sheets', 'Pre-colored sheets'), ('print', 'UV-printed color')):
        stations = res[mode][1]
        for st, m in stations.items():
            w = per_week(m)
            L.append(f"| {label} | {st} | {m:.1f} | {SHIFT_MIN / m:.0f} | {w:.0f} | {w * WEEKS_PER_MONTH:.0f} | {2 * w * WEEKS_PER_MONTH:.0f} | {3 * w * WEEKS_PER_MONTH:.0f} |")
        core = {k: v for k, v in stations.items() if 'show face' not in k}
        bott = max(core, key=core.get)
        cap = per_week(core[bott])
        chart.append((label, cap, bott))
        lines.append(f"- **{label}:** the bottleneck is the {bott.split(' (')[0].lower().replace('uv', 'UV')}, about **{cap:.0f} kits a week** "
                     f"({cap * WEEKS_PER_MONTH:.0f} a month) on one shift.")
    # where the bottleneck moves
    you_p = res['print'][1]['You (check, pack, ship)']
    pr = res['print'][1]['UV printer (both sides)']
    scen = [('1 laser, you alone, pre-colored sheets', {'laser': per_week(laser_s), 'you': per_week(you_s)}),
            ('1 laser + UV printer (both sides), you alone', {'laser': per_week(res['print'][1]['Laser (attended)']), 'UV printer': per_week(pr), 'you': per_week(you_p)}),
            ('2 lasers, you alone', {'2 lasers': 2 * per_week(laser_s), 'you': per_week(you_s)}),
            ('2 lasers, you + a part-time packer', {'2 lasers': 2 * per_week(laser_s), 'you + packer': 2 * per_week(you_s)})]
    L += ['', '## Bottleneck', ''] + lines + ['', '## Where the bottleneck moves (one shift)', '',
                                               '| Setup | Laser | UV printer | People | Kits per week | Bottleneck |', '|---|---|---|---|---|---|']
    srows = []
    for name, caps in scen:
        b = min(caps, key=caps.get)
        las = next((v for k, v in caps.items() if 'laser' in k), None)
        ppl = next((v for k, v in caps.items() if 'you' in k), None)
        L.append(f"| {name} | {las:.0f} | {caps.get('UV printer', 0) and round(caps['UV printer']) or '-'} | {ppl:.0f} | **{caps[b]:.0f}** | {b} |")
        srows.append((name, caps[b], b))
    L += ['',
          f'- **Launch ({demand} a week):** nothing limits you. About {demand * laser_s / 60:.0f} hours of laser time a week, with your checking and packing done during the cuts.',
          '- **Growing on one laser:** the laser is the bottleneck. It must be attended while it runs (fire rule), so you check, pack and ship at the bench beside it while it cuts.',
          '- **With UV printing on both sides, the printer is the bottleneck** (the floral kit needs 43 min). Print the show face only (`two_sided = False`), buy the dual-head model, or run the printer when the laser is off. A UV-LED printer has no open flame like the laser, but check the maker\'s manual before leaving it alone.',
          '- **Add a second laser and you become the bottleneck.** Your hands-on minutes per kit are then the limit. A part-time packer, or less checking per job once the first-pass yield is high, moves it back to the lasers.',
          '- **2 and 3 shifts need more people.** You cannot attend the laser for 16 or 24 hours. CO2 glass tubes are commonly quoted at a few thousand hours (Estimate), so budget a spare tube once you pass 2 shifts.',
          '', '![Capacity](capacity.png)', '', '![Where the bottleneck moves](capacity_bottleneck.png)', '',
          'How to grow, cheapest first: (1) measure the real cut speed (it may be faster than 30 mm/s); (2) tighter nesting cuts laser minutes per kit; '
          '(3) a second laser (about $3,700) plus a part-time packer roughly doubles output.']
    open(os.path.join(ROOT, 'production', 'capacity.md'), 'w').write('\n'.join(L) + '\n')

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
    fig, ax = plt.subplots(figsize=(9, 3.6), dpi=150)
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    xs = range(3)
    for j, (label, cap, bott) in enumerate(chart):
        ys = [cap * s for s in (1, 2, 3)]
        bars = ax.bar([x + (j - 0.5) * 0.36 for x in xs], ys, width=0.34, color=SERIES[j], edgecolor=BG, linewidth=2,
                      label=f"{label}: limited by the {bott.split(' (')[0].lower().replace('uv', 'UV')}")
        for b, y in zip(bars, ys):
            ax.text(b.get_x() + b.get_width() / 2, y + 6, f'{y:.0f}', ha='center', fontsize=10, color=INK2)
    ax.axhline(demand, color=INK2, linewidth=1.2, linestyle=(0, (4, 3)), label=f'Launch demand: {demand} kits a week')
    ax.set_xticks(list(xs)); ax.set_xticklabels(['1 shift', '2 shifts', '3 shifts'])
    ax.set_ylabel('Kits per week'); ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', color=GRID, linewidth=0.8); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, loc='upper left')
    ax.set_title('Weekly capacity, one laser (Estimate)', loc='left', fontsize=13)
    fig.tight_layout(); fig.savefig(os.path.join(ROOT, 'production', 'capacity.png')); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 3.3), dpi=150)
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ys = list(range(len(srows)))[::-1]
    ax.barh(ys, [c for _, c, _ in srows], height=0.58, color=SERIES[0], edgecolor=BG, linewidth=2)
    for y, (_, c, b) in zip(ys, srows):
        ax.text(c + 3, y, f'{c:.0f} a week, limited by {b}', va='center', fontsize=10, color=INK2)
    ax.set_yticks(ys); ax.set_yticklabels([n for n, _, _ in srows])
    ax.set_xlim(0, max(c for _, c, _ in srows) * 1.8)
    ax.set_xlabel('Kits per week on one shift')
    ax.spines[['top', 'right', 'left']].set_visible(False); ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', color=GRID, linewidth=0.8); ax.set_axisbelow(True)
    ax.set_title('Where the bottleneck moves (Estimate)', loc='left', fontsize=13)
    fig.tight_layout(); fig.savefig(os.path.join(ROOT, 'production', 'capacity_bottleneck.png')); plt.close(fig)
    print('\n'.join(lines))
    for r in srows:
        print(r)


if __name__ == '__main__':
    main()
