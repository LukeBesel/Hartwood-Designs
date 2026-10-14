"""Build the research dashboard (research/dashboard/index.html) from the CSV files.

Run from repo root:  .venv/bin/python research/tools/build_dashboard.py
"""
import csv
import json
import statistics
from collections import Counter, defaultdict

R = 'research/data/'


def num(x):
    try:
        return float(str(x).replace('$', '').strip())
    except ValueError:
        return None


products = []
for r in csv.DictReader(open(R + 'rokr_products.csv')):
    price = num(r['price_official_usd']) or num(r['price_walmart_usd']) or num(r['price_amazon_usd'])
    cat = r['category']
    products.append(dict(brand='ROKR', name=r['product'], cat=cat, pieces=num(r['pieces']), price=price,
                         line=r['line'], src=r['source_ids']))
for r in csv.DictReader(open(R + 'competitor_products.csv')):
    products.append(dict(brand=r['brand'].split(' (')[0], name=r['product'], cat=r['category'],
                         pieces=num(r['pieces']), price=num(r['price_usd']), line=r['brand'], src=r['source_ids']))

# Normalise categories into dashboard groups
GROUP = {
    'Mechanical vehicle': 'Vehicle', 'Vehicle': 'Vehicle', 'Licensed vehicle': 'Vehicle',
    'Mechanical': 'Mechanical', 'Mechanical game': 'Mechanical', 'Kinetic art': 'Mechanical',
    'Marble run': 'Marble run', 'Marble run game': 'Marble run',
    'Music box': 'Music box', 'Music instrument': 'Music box', 'Music themed': 'Music box',
    'Clock': 'Clock', 'Rubber band gun': 'Rubber band gun', 'Launcher': 'Mechanical',
    'Flower': 'Flower', 'Puzzle box': 'Puzzle box', 'Creature': 'Creature',
    'Metal model': 'Metal model',
}
for p in products:
    p['group'] = GROUP.get(p['cat'], 'Other')

scatter = [p for p in products if p['pieces'] and p['price']]

# price per piece by group
ppp = defaultdict(list)
for p in scatter:
    ppp[p['group']].append(p['price'] / p['pieces'])
ppp_rows = sorted(({'group': g, 'median': round(statistics.median(v), 3), 'n': len(v),
                    'min': round(min(v), 3), 'max': round(max(v), 3)} for g, v in ppp.items()),
                  key=lambda r: -r['median'])

# brand median price per piece
bppp = defaultdict(list)
for p in scatter:
    bppp[p['brand']].append(p['price'] / p['pieces'])
brand_ppp = {b: round(statistics.median(v), 3) for b, v in bppp.items()}

# category mix per brand (counts of products found)
mix = defaultdict(Counter)
for p in products:
    mix[p['brand']][p['group']] += 1
brands = sorted(mix, key=lambda b: -sum(mix[b].values()))
groups = sorted({p['group'] for p in products}, key=lambda g: -sum(mix[b][g] for b in brands))
mix_rows = [{'brand': b, 'counts': [mix[b][g] for g in groups], 'total': sum(mix[b].values())} for b in brands]

# complaints pareto
hate = Counter()
love = Counter()
for r in csv.DictReader(open(R + 'review_mentions.csv')):
    (hate if r['sentiment'] == 'hate' else love)[r['theme']] += 1
total = sum(hate.values())
cum = 0
pareto = []
for theme, c in hate.most_common():
    cum += c
    pareto.append({'theme': theme, 'count': c, 'share': round(100 * c / total, 1), 'cum': round(100 * cum / total, 1)})

# white space map: theme x price band
BANDS = ['< $30', '$30-45', '$45-60', '$60-90', '$90+']


def band(price):
    if price < 30: return 0
    if price < 45: return 1
    if price < 60: return 2
    if price < 90: return 3
    return 4


def theme_of(p):
    n = p['name'].lower()
    if p['group'] == 'Rubber band gun':
        return 'Rubber band blaster, original toy look' if False else 'Rubber band blaster, real-gun replica'
    if 'dragon' in n:
        return 'Dragon'
    if p['group'] == 'Creature':
        return 'Other animals and creatures'
    if p['group'] == 'Flower':
        return 'Flowers'
    if p['group'] == 'Music box':
        if 'garden' in n:
            return 'Flower or garden music box'
        return 'Music box (other themes)'
    return {'Vehicle': 'Vehicles and trains', 'Mechanical': 'Mechanical machines', 'Marble run': 'Marble runs',
            'Clock': 'Clocks', 'Puzzle box': 'Puzzle boxes', 'Metal model': 'Metal models'}.get(p['group'], 'Other')


THEMES = ['Rubber band blaster, original toy look', 'Rubber band blaster, real-gun replica', 'Dragon',
          'Other animals and creatures', 'Flower or garden music box', 'Flowers', 'Music box (other themes)',
          'Marble runs', 'Clocks', 'Mechanical machines', 'Vehicles and trains', 'Puzzle boxes', 'Metal models']
grid = {t: [0] * len(BANDS) for t in THEMES}
for p in products:
    if not p['price']:
        continue
    t = theme_of(p)
    if t in grid:
        grid[t][band(p['price'])] += 1
targets = [
    {'theme': 'Rubber band blaster, original toy look', 'band': 2, 'label': 'Hartwood blaster'},
    {'theme': 'Dragon', 'band': 2, 'label': 'Hartwood dragon'},
    {'theme': 'Flower or garden music box', 'band': 2, 'label': 'Hartwood flowers'},
]
white = {'themes': THEMES, 'bands': BANDS, 'grid': [grid[t] for t in THEMES], 'targets': targets}

hartwood_targets = [
    {'name': 'Hartwood blaster (target)', 'pieces': 220, 'price': 49.99},
    {'name': 'Hartwood dragon (target)', 'pieces': 240, 'price': 54.99},
    {'name': 'Hartwood flower music box (target)', 'pieces': 200, 'price': 49.99},
]

data = dict(scatter=[{k: p[k] for k in ('brand', 'name', 'group', 'pieces', 'price')} for p in scatter],
            ppp=ppp_rows, brand_ppp=brand_ppp, mix={'groups': groups, 'rows': mix_rows}, pareto=pareto,
            love=love.most_common(), white=white, targets=hartwood_targets,
            counts=dict(products=len(products), rokr=sum(1 for p in products if p['brand'] == 'ROKR'),
                        priced=len(scatter), mentions=total + sum(love.values()), complaints=total))

html = open('research/tools/dashboard_template.html').read().replace('/*DATA*/null', json.dumps(data))
open('research/dashboard/index.html', 'w').write(html)
print('products', len(products), 'scatter', len(scatter), 'brand ppp', brand_ppp)
print('ppp', ppp_rows)
