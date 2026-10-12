"""Supply files from the kit reports: BOM per kit and per batch, suppliers (2+ per item), reorder points,
startup shopping list, unit economics at three prices (with charts).

    .venv/bin/python tools/make_supply.py      ->  supply/*.csv, supply/*.png, supply/README.md

Prices: Verified = seen in a search summary on 2026-10-12 (research/raw/search_log.md S21); Estimate = my
assumption, marked as such. Change a number in ITEMS and rerun.
"""
from __future__ import annotations

import csv
import json
import math
import os
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'supply')
KITS = ['blaster', 'dragon', 'floral']
PRICES = {'blaster': (39.99, 49.99, 59.99), 'dragon': (44.99, 54.99, 64.99), 'floral': (39.99, 49.99, 59.99)}
LABOR_RATE = 20.0          # USD per hour, owner's time (Estimate)
HANDS_ON_MIN = 6.0         # pop-out spot check, cut dowels, bag extras, pack (Estimate), on top of the attended laser time
WEEKLY_PLAN = {'blaster': 6, 'dragon': 5, 'floral': 6}    # kits per week at launch (Estimate)

# unit cost = the supplier we would buy from at a 25 to 100 kit batch; every item has 2+ suppliers
ITEMS = {
    'sheet_natural': {'name': 'Natural basswood plywood 12 x 12 x 1/8 in', 'unit': 'sheet', 'cost': 0.92, 'status': 'Verified',
                      'lead_days': 4, 'pack': 48, 'suppliers': [
                          ('ESRICH 48-pack (WoodArtSupply)', '$42.48 per 48 = $0.89', 'Verified'),
                          ('MITINU 50-pack (WoodArtSupply), poplar core: test first', '$45.99 per 50 = $0.92', 'Verified'),
                          ('Creality Falcon 10-pack', '$16.99 per 10 = $1.70', 'Verified'),
                          ('LotFancy 12-pack (Walmart)', '$19.99 per 12 = $1.67', 'Verified')]},
    'sheet_color': {'name': 'Pre-painted basswood plywood 12 x 12 x 1/8 in (one color)', 'unit': 'sheet', 'cost': 4.50,
                    'status': 'Estimate', 'lead_days': 5, 'pack': 10, 'suppliers': [
                        ('Craft Closet Maker Boards Colors (double-sided, 17 colors)', '$59.99 per 9 = $6.67', 'Verified'),
                        ('TwoTrees 3 mm colored basswood 300 x 300, 10-pack', 'EUR 34.95 per 10 = about $3.80', 'Verified (EU price)'),
                        ('Creatorally pre-painted 12 x 12 (Amazon)', 'price not shown in search: TODO_LUCAS', 'Estimate')]},
    'band_64': {'name': '#64 rubber band (3.5 x 1/4 in), blaster ammo', 'unit': 'band', 'cost': 0.032, 'status': 'Verified',
                'lead_days': 2, 'pack': 380, 'suppliers': [
                    ('Staples Economy #64, 380 per pack', '$11.99 = $0.032', 'Verified'),
                    ('Alliance Sterling #64, 1 lb about 425 (Quill)', '$16.79 = $0.040', 'Verified')]},
    'band_16': {'name': '#16 rubber band (2.5 x 1/16 in), trigger return', 'unit': 'band', 'cost': 0.0041, 'status': 'Verified',
                'lead_days': 2, 'pack': 2300, 'suppliers': [
                    ('Alliance Sterling #16, 1 lb about 2,300 (Staples)', '$9.49 = $0.0041', 'Verified'),
                    ('Same item at Walmart (sale)', '$6.90 = $0.0030', 'Verified')]},
    'dowel': {'name': '3/16 in birch dowel, 36 in (cut to length)', 'unit': 'mm', 'cost': 0.40 / 914, 'status': 'Verified',
              'lead_days': 5, 'pack': 914 * 25, 'suppliers': [
                  ('Lee Valley birch 3/16 x 36 in', '$0.40 each', 'Verified'),
                  ('Madison Mill poplar 3/16 x 36 in, 25-pack (Walmart)', '$38.01 = $1.52 each', 'Verified'),
                  ('Valley Wide Coop poplar 3/16 x 36 in (multiples of 25)', '$1.49 each', 'Verified')]},
    'movement': {'name': '18-note wind-up music movement with turning shaft', 'unit': 'each', 'cost': 3.00, 'status': 'Estimate',
                 'lead_days': 30, 'pack': 100, 'suppliers': [
                     ('B2B supplier via Alibaba (order samples first, check shaft and size)', '$1.77 to $2.12 for a battery model; wind-up quote TODO_LUCAS', 'Verified (listing)'),
                     ('eBay 18-note wind-up movement (retail, for prototypes)', '$6.99', 'Verified'),
                     ('National Artcraft 18-note (Walmart)', '$9.85 to $12.89', 'Verified')]},
    'wax': {'name': 'Wax stick (paraffin, cut from a 1 lb block)', 'unit': 'stick', 'cost': 0.08, 'status': 'Estimate',
            'lead_days': 3, 'pack': 200, 'suppliers': [
                ('Alexes paraffin 1 lb (about 200 sticks)', '$15.99', 'Verified'),
                ('Blended Waxes paraffin 1 lb (eBay)', 'from $15.58', 'Verified')]},
    'sandpaper': {'name': 'Sandpaper 240 grit, 1/8 of a 9 x 11 sheet', 'unit': 'piece', 'cost': 31.36 / 100 / 8, 'status': 'Verified',
                  'lead_days': 4, 'pack': 800, 'suppliers': [
                      ('AA Abrasives 9 x 11 240 A/O, 100 sheets', '$31.36', 'Verified'),
                      ('eBay 240 grit 9 x 11, 50 sheets', '$33.27', 'Verified')]},
    'bag': {'name': 'Zip bag 3 x 4 in (extras)', 'unit': 'bag', 'cost': 0.016, 'status': 'Verified', 'lead_days': 3, 'pack': 1000,
            'suppliers': [('UOFFICE 3 x 4 in 2 mil, 1,000 (Walmart)', '$15.67', 'Verified'),
                          ('American Retail Supply 3 x 4 in 4 mil, 1,000', '$27.68', 'Verified'),
                          ('Uline S-1292 3 x 4 in 2 mil', 'price: check uline.com', 'Estimate')]},
    'box': {'name': 'White mailer box 12 x 12 x 2 in (sheets must measure 12 in or less)', 'unit': 'box', 'cost': 1.83, 'status': 'Verified',
            'lead_days': 2, 'pack': 100, 'suppliers': [
                ('Uline S-5817 (50: $1.99, 100: $1.83, 500: $1.51, 1,000: $1.47)', '$1.83 at 100', 'Verified'),
                ('Interplas CP-121202P, bundle of 50', '$88.35 = $1.77', 'Verified'),
                ('Global Industrial WBB40305, 50', '$113.00 = $2.26', 'Verified')]},
    'booklet': {'name': 'Printed color booklet (22 to 32 pages)', 'unit': 'booklet', 'cost': 3.61, 'status': 'Estimate',
                'lead_days': 7, 'pack': 100, 'suppliers': [
                    ('4OVER4 booklets, 100 run (page count to confirm)', '$3.61 each', 'Verified (listing)'),
                    ('In-house color laser printer + long-reach stapler', 'about $1.50 each (Estimate)', 'Estimate')]},
    'sticker': {'name': 'Brand label on the box lid (4 x 4 in)', 'unit': 'label', 'cost': 0.25, 'status': 'Estimate', 'lead_days': 7,
                'pack': 250, 'suppliers': [('Any online sticker printer (quote TODO_LUCAS)', 'about $0.25', 'Estimate'),
                                           ('In-house: label printer + color labels', 'about $0.20', 'Estimate')]},
    'targets': {'name': 'Paper target (printed in-house)', 'unit': 'sheet', 'cost': 0.04, 'status': 'Estimate', 'lead_days': 1,
                'pack': 500, 'suppliers': [('Copy paper + home printer', '$0.04', 'Estimate'), ('Office store copies', '$0.10', 'Estimate')]},
    'filler': {'name': 'Kraft paper filler and tape', 'unit': 'kit', 'cost': 0.12, 'status': 'Estimate', 'lead_days': 2, 'pack': 300,
               'suppliers': [('Uline kraft roll', 'about $0.08 per box', 'Estimate'), ('Any packing tape', 'about $0.04 per box', 'Estimate')]},
}
SHIP_BASE, SHIP_PER_LB = 9.30, 1.00          # USPS Ground Advantage 2 lb zone 5 $8.60 to $9.95 (Verified range); +$1/lb (Estimate)
SHEET_KG = 0.13                               # 12 x 12 x 3 mm basswood ply, about 450 kg/m3 (Estimate)
FEES = {'own site (Shopify)': lambda p: 0.029 * p + 0.30, 'Etsy': lambda p: 0.065 * p + 0.03 * p + 0.25 + 0.20}


def kit_bom(kit):
    rep = json.load(open(os.path.join(ROOT, 'kits', kit, f'{kit}_report.json')))
    steps = json.load(open(os.path.join(ROOT, 'kits', kit, f'{kit}_steps.json')))
    rows = []
    nat = sum(s['fraction'] for s in rep['sheets'] if s['color'] == 'natural')
    rows.append(('sheet_natural', nat, f"{len([s for s in rep['sheets'] if s['color'] == 'natural'])} full sheets"))
    for s in rep['sheets']:
        if s['color'] != 'natural':
            rows.append(('sheet_color', s['fraction'], f"{s['color']}, {s['tile']} sheet (sheet {s['sheet']})"))
    dowel_mm = 0.0
    for name, q in steps['extras'].items():
        n = name.lower()
        if '#64' in n:
            rows.append(('band_64', q, name))
        elif '#16' in n:
            rows.append(('band_16', q, name))
        elif 'dowel' in n:
            mm = float(re.search(r'([0-9.]+) mm', n).group(1))
            dowel_mm += mm * q
        elif 'music movement' in n:
            rows.append(('movement', q, name))
        elif 'wax' in n:
            rows.append(('wax', q, name))
        elif 'sandpaper' in n:
            rows.append(('sandpaper', q, name))
        elif 'target' in n:
            rows.append(('targets', q, name))
    if dowel_mm:
        rows.append(('dowel', dowel_mm * 1.1, f'{dowel_mm:.0f} mm of dowel (+10% saw waste)'))
    rows += [('bag', 2, 'extras + spare small parts'), ('box', 1, 'shipping box'), ('booklet', 1, 'instructions'),
             ('sticker', 1, 'lid label'), ('filler', 1, 'filler and tape')]
    return rep, steps, rows


def money(x):
    return f'${x:,.2f}'


def main():
    os.makedirs(OUT, exist_ok=True)
    econ, bom_rows, batch_rows, summary = [], [], [], {}
    for kit in KITS:
        rep, steps, rows = kit_bom(kit)
        mat = sum(ITEMS[i]['cost'] * q for i, q, _ in rows)
        for i, q, note in rows:
            it = ITEMS[i]
            bom_rows.append([steps['name'], it['name'], round(q, 3), it['unit'], round(it['cost'], 4),
                             round(it['cost'] * q, 2), it['status'], note])
        for n in (25, 100):
            agg = {}
            for i, q, note in rows:
                if i == 'sheet_color':
                    key = (i, note.split(',')[0])
                    frac = q
                    agg[key] = agg.get(key, 0) + math.ceil(n * frac - 1e-9) if frac >= 1 else agg.get(key, 0) + math.ceil(n * frac)
                else:
                    key = (i, '')
                    agg[key] = agg.get(key, 0) + q * n
            for (i, extra), q in agg.items():
                it = ITEMS[i]
                qq = math.ceil(q) if it['unit'] in ('sheet', 'band', 'each', 'stick', 'piece', 'bag', 'box', 'booklet', 'label', 'kit') else round(q)
                packs = math.ceil(qq / it['pack']) if it['pack'] else None
                batch_rows.append([steps['name'], n, it['name'] + (f' ({extra})' if extra else ''), qq, it['unit'],
                                   packs, money(qq * it['cost'])])
        sheets_n = len(rep['sheets'])
        weight_lb = (sheets_n * SHEET_KG + 0.35) * 2.2046
        ship = SHIP_BASE + max(0.0, math.ceil(weight_lb) - 2) * SHIP_PER_LB
        labor_min = rep['cut_minutes_per_kit'] + HANDS_ON_MIN
        labor = labor_min / 60 * LABOR_RATE
        summary[kit] = {'name': steps['name'], 'materials': mat, 'ship': ship, 'labor': labor, 'labor_min': labor_min,
                        'weight_lb': weight_lb}
        # print mode: all sheets natural, plus ink, plus printing time (attended part of it: 2 min per side)
        prep = os.path.join(ROOT, 'kits', kit, 'print_mode', f'{kit}_report.json')
        modes = [('pre-colored sheets', mat, labor)]
        if os.path.exists(prep):
            pr = json.load(open(prep))
            wood_s = sum(ITEMS['sheet_natural' if s['color'] == 'natural' else 'sheet_color']['cost'] * s['fraction'] for s in rep['sheets'])
            wood_p = sum(ITEMS['sheet_natural']['cost'] * s['fraction'] for s in pr['sheets'])
            mat_p = mat - wood_s + wood_p + pr['print']['ink_usd']
            labor_p = (pr['cut_minutes_per_kit'] + HANDS_ON_MIN + 2.0 * pr['print']['printed_sheet_sides']) / 60 * LABOR_RATE
            modes.append(('UV-printed color', mat_p, labor_p))
            summary[kit].update({'materials_print': mat_p, 'labor_print': labor_p, 'wood_sheets': wood_s, 'wood_print': wood_p,
                                 'ink': pr['print']['ink_usd'], 'print_min': pr['print']['print_minutes']})
        for mode, m_, lab_ in modes:
            for channel, fee in FEES.items():
                for price in PRICES[kit]:
                    f = fee(price)
                    before = price - m_ - ship - f
                    after = before - lab_
                    econ.append([steps['name'], mode, channel, price, round(m_, 2), round(ship, 2), round(f, 2), round(before, 2),
                                 round(lab_, 2), round(after, 2), f'{100 * after / price:.0f}%'])

    with open(os.path.join(OUT, 'bom_per_kit.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['kit', 'item', 'qty per kit', 'unit', 'unit cost', 'cost per kit', 'price status', 'note'])
        w.writerows(bom_rows)
    with open(os.path.join(OUT, 'bom_batches.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['kit', 'batch size', 'item', 'quantity', 'unit', 'packs to buy', 'cost'])
        w.writerows(batch_rows)
    with open(os.path.join(OUT, 'suppliers.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['item', 'supplier and product', 'price seen', 'status', 'lead time days (Estimate)'])
        for k, it in ITEMS.items():
            for s in it['suppliers']:
                w.writerow([it['name'], s[0], s[1], s[2], it['lead_days']])
    with open(os.path.join(OUT, 'unit_economics.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['kit', 'color method', 'channel', 'price', 'materials + packaging', 'shipping (free to customer)', 'fees',
                    'profit before labor', 'labor at $20/h', 'profit after labor', 'margin after labor'])
        w.writerows(econ)

    # reorder points: weekly use at the launch plan, lead time, one week of safety stock
    use = {}
    for kit in KITS:
        _, _, rows = kit_bom(kit)
        for i, q, note in rows:
            key = i if i != 'sheet_color' else 'sheet_color'
            use[key] = use.get(key, 0) + q * WEEKLY_PLAN[kit]
    rp = []
    for i, wk in use.items():
        it = ITEMS[i]
        daily = wk / 7
        rop = daily * it['lead_days'] + wk          # lead-time demand + one week safety
        order = max(it['pack'], math.ceil(4 * wk / it['pack']) * it['pack'])   # about four weeks, whole packs
        unit = it['unit']
        rp.append([it['name'], round(wk, 1), unit, it['lead_days'], math.ceil(rop), order])
    with open(os.path.join(OUT, 'reorder_points.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['item', 'use per week (launch plan)', 'unit', 'lead time days', 'reorder when stock falls to', 'order quantity'])
        w.writerows(rp)
    json.dump({'items': ITEMS, 'weekly_plan': WEEKLY_PLAN, 'summary': summary}, open(os.path.join(OUT, 'supply_data.json'), 'w'),
              indent=1, default=str)

    charts(econ, summary)
    rows_s, tot = startup(batch_rows)
    json.dump({'items': ITEMS, 'weekly_plan': WEEKLY_PLAN, 'summary': summary, 'startup_totals': tot},
              open(os.path.join(OUT, 'supply_data.json'), 'w'), indent=1, default=str)
    print('supply files written to', OUT, 'startup totals', tot)
    return summary, econ, rp


SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']   # validated categorical order


def charts(econ, summary):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'axes.edgecolor': '#c9c6bd',
                         'axes.labelcolor': '#52514e', 'xtick.color': '#52514e', 'ytick.color': '#52514e'})
    # 1. where the money goes (own site, middle price)
    fig, ax = plt.subplots(figsize=(10, 4.6), dpi=150)
    fig.patch.set_facecolor('#fcfcfb'); ax.set_facecolor('#fcfcfb')
    names = [summary[k]['name'] for k in KITS]
    parts = ['Materials and packaging', 'Shipping', 'Fees', 'Labor', 'Profit']
    vals = []
    for k in KITS:
        price = PRICES[k][1]
        row = next(r for r in econ if r[0] == summary[k]['name'] and r[1] == 'pre-colored sheets' and r[2] == 'own site (Shopify)' and r[3] == price)
        vals.append([row[4], row[5], row[6], row[8], row[9]])
    left = [0] * len(KITS)
    for j, label in enumerate(parts):
        widths = [v[j] for v in vals]
        bars = ax.barh(names, widths, left=left, color=SERIES[j], edgecolor='#fcfcfb', linewidth=2, height=0.55, label=label)
        for b, wv in zip(bars, widths):
            if wv > 3.2:
                ax.text(b.get_x() + wv / 2, b.get_y() + b.get_height() / 2, f'${wv:.0f}', ha='center', va='center',
                        color='#ffffff' if j in (0, 1, 5) else '#0b0b0b', fontsize=10)
        left = [l + w_ for l, w_ in zip(left, widths)]
    for i, k in enumerate(KITS):
        ax.text(left[i] + 0.6, i, f'price ${PRICES[k][1]:.2f}', va='center', color='#52514e', fontsize=10)
    ax.invert_yaxis(); ax.set_xlabel('US dollars per kit sold on your own site (free shipping, middle price)')
    ax.set_xlim(0, max(left) + 12)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='x', color='#e7e5df', linewidth=0.8); ax.set_axisbelow(True)
    ax.legend(ncol=5, loc='upper center', bbox_to_anchor=(0.5, 1.16), frameon=False, fontsize=10)
    ax.set_title('Where the money goes, per kit', loc='left', fontsize=14, color='#0b0b0b', pad=34)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'unit_economics_breakdown.png')); plt.close(fig)

    # 2. profit after labor at three prices: pre-colored sheets vs UV-printed color (own site)
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.8), dpi=150, sharey=True)
    fig.patch.set_facecolor('#fcfcfb')
    for ax, k in zip(axs, KITS):
        ax.set_facecolor('#fcfcfb')
        for j, mode in enumerate(('pre-colored sheets', 'UV-printed color')):
            ys = [next((r[9] for r in econ if r[0] == summary[k]['name'] and r[1] == mode and r[2] == 'own site (Shopify)'
                        and r[3] == p), 0.0) for p in PRICES[k]]
            xs = [x + (j - 0.5) * 0.36 for x in range(3)]
            bars = ax.bar(xs, ys, width=0.34, color=SERIES[j], edgecolor='#fcfcfb', linewidth=2, label=mode)
            for b, y in zip(bars, ys):
                ax.text(b.get_x() + b.get_width() / 2, y + (0.6 if y >= 0 else -1.6), (f'${y:.0f}' if y >= 0 else f'-${-y:.0f}'), ha='center', fontsize=9, color='#52514e')
        ax.set_xticks(range(3)); ax.set_xticklabels([f'${p:.0f}' for p in PRICES[k]])
        ax.axhline(0, color='#8a877e', linewidth=1)
        ax.set_title(summary[k]['name'], fontsize=12, color='#0b0b0b')
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='y', color='#e7e5df', linewidth=0.8); ax.set_axisbelow(True)
    axs[0].set_ylabel('Profit per kit after labor (USD)')
    axs[0].legend(frameon=False, fontsize=9, loc='upper left')
    fig.suptitle('Profit per kit at three prices, own site (labor $20/h, free shipping)', x=0.01, ha='left', fontsize=14, color='#0b0b0b')
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'unit_economics_prices.png')); plt.close(fig)


STARTUP = [
    # (item, cost, status, where, required?)
    ('OMTech Polar 2 70W glass CO2 laser (bed 710 x 360 mm, LightBurn included)', 3699.99, 'Verified (S16)', 'omtech.com (buy direct for warranty)', 'required'),
    ('Window vent kit and 4 in duct for the built-in exhaust fan', 40.00, 'Estimate', 'hardware store', 'required'),
    ('CO2 fire extinguisher 5 lb (Amerex 322)', 218.00, 'Verified (S21)', 'Walmart, Airgas, Tiger Medical', 'required'),
    ('Smoke alarm and fire blanket', 45.00, 'Estimate', 'hardware store', 'required'),
    ('Digital calipers 150 mm (kerf, fit coupon, sheet size)', 25.00, 'Estimate', 'any', 'required'),
    ('Spare focus lens and mirror set', 60.00, 'Estimate', 'OMTech parts store', 'required'),
    ('Distilled water and coolant for the water loop', 20.00, 'Estimate', 'grocery / OMTech', 'required'),
    ('Small shop vacuum (bed and honeycomb)', 60.00, 'Estimate', 'any', 'required'),
    ('Packing table and two wire shelving units', 250.00, 'Estimate', 'any', 'required'),
    ('Thermal shipping label printer 4 x 6 and labels', 180.00, 'Estimate', 'any', 'required'),
    ('Shipping scale', 30.00, 'Estimate', 'any', 'required'),
    ('Fine razor saw, miter box and stop block (dowels)', 35.00, 'Estimate', 'any', 'required'),
    ('Minnesota LLC filing (online)', 155.00, 'Verified (S22)', 'Minnesota Secretary of State', 'required'),
    ('Product liability insurance, first year', 1200.00, 'Estimate (S22 average $1,192)', 'broker or online insurer', 'required'),
    ('Fume extractor OMTech 300W 4-stage (only if you cannot vent outside)', 749.99, 'Verified (S17)', 'omtech.com', 'optional'),
    ('UV printer xTool O1 Omni single head (recommended, see D028)', 1699.00, 'Verified (S20)', 'xtool.com', 'recommended'),
    ('Extra UV ink set', 60.00, 'Estimate', 'xtool.com', 'recommended'),
    ('Color laser printer for booklets (only if printing in-house)', 400.00, 'Estimate', 'any', 'optional'),
]


def startup(batch_rows):
    mats = 0.0
    for r in batch_rows:
        if r[1] == 25:
            mats += float(r[6].replace('$', '').replace(',', ''))
    rows = [list(x) for x in STARTUP] + [['Starter materials: 25 kits of each design (from bom_batches.csv)', round(mats, 2),
                                          'Mixed (see suppliers.csv)', 'see suppliers.csv', 'required']]
    with open(os.path.join(OUT, 'startup_shopping_list.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['item', 'cost USD', 'price status', 'where', 'need'])
        w.writerows(rows)
    tot = {k: round(sum(r[1] for r in rows if r[4] == k), 2) for k in ('required', 'recommended', 'optional')}
    return rows, tot


if __name__ == '__main__':
    main()
