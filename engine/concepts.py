"""Concept boards: three directions per kit, scored. The chosen one uses its real render; the
runners-up are quick sketches drawn here (shapely shapes, sketchy lines).

    python engine/concepts.py   ->  review/concepts/<kit>_concepts.png, review/concepts/<kit>_<id>.png,
                                    review/concepts/CONCEPTS.md
"""
from __future__ import annotations

import math
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from PIL import Image, ImageDraw, ImageFont
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'review', 'concepts')
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
COL = {'natural': '#ecd2a6', 'orange': '#ff6a13', 'teal': '#7fb3c8', 'pink': '#f2a7bd', 'yellow': '#f6d65a',
       'green': '#8cc084', 'purple': '#a58ad6', 'red': '#d9483b', 'gold': '#d8b04a', 'white': '#f4f1ea'}
INK = '#5e3b22'

CRITERIA = ['Looks', 'Fun', 'Cut time', 'Cost', 'Unique', 'Risk']
WEIGHTS = [0.25, 0.25, 0.1, 0.1, 0.2, 0.1]


def tube(pts, r0, r1=None):
    """Tapered tube along a polyline (side view)."""
    r1 = r0 if r1 is None else r1
    ls = LineString(pts)
    n = 40
    parts = []
    for i in range(n):
        a = ls.interpolate(i / n, normalized=True); b = ls.interpolate((i + 1) / n, normalized=True)
        r = r0 + (r1 - r0) * (i + 0.5) / n
        parts.append(LineString([a, b]).buffer(r))
    return unary_union(parts)


def circ(x, y, r):
    return Point(x, y).buffer(r, 48)


def gear(x, y, r, n, depth=4):
    pts = []
    for k in range(n * 2):
        a = math.pi * k / n
        rr = r if k % 2 == 0 else r - depth
        for da in (-0.25, 0.25):
            pts.append((x + rr * math.cos(a + da * math.pi / n), y + rr * math.sin(a + da * math.pi / n)))
    return Polygon(pts)


# ------------------------------------------------------------------ runner-up sketches (side views, mm-ish)
def blaster_turret():
    s = [(box(-70, 0, 70, 16), 'natural'), (box(-50, 16, 50, 23), 'teal'),
         (Polygon([(-22, 23), (22, 23), (15, 62), (-15, 62)]), 'natural')]
    barrel = affinity.rotate(box(-60, 56, 60, 74), 14, origin=(0, 65))
    s.append((barrel, 'natural'))
    s.append((affinity.rotate(box(52, 56, 70, 74), 14, origin=(0, 65)), 'orange'))
    s.append((gear(-34, 66, 21, 6, 6), 'teal'))
    s.append((circ(-34, 66, 5), 'natural'))
    s.append((circ(30, 40, 6), 'orange'))
    s.append((box(29, 34, 31, 46).union(box(29, 22, 44, 25)), 'natural'))
    lines = [LineString([(-34, 87), (62, 90)]), LineString([(-13, 70), (62, 82)])]
    return s, lines, 'Comet Turret', 'Desk turret. Crank turns a 6-band carousel; pan and tilt to aim.'


def blaster_raptor():
    head = Polygon([(-60, 10), (-20, 30), (30, 34), (80, 22), (98, 10), (60, 4), (20, 2), (-55, -5)])
    jaw = Polygon([(10, 0), (60, 2), (92, 2), (70, -8), (20, -12)])
    grip = Polygon([(-50, -4), (-22, -4), (-28, -70), (-52, -70)])
    teeth = unary_union([Polygon([(x, 2), (x + 3, -3), (x + 6, 2)]) for x in range(30, 84, 9)])
    s = [(grip, 'natural'), (head, 'teal'), (jaw, 'natural'), (teeth, 'white'), (circ(40, 20, 6), 'yellow'),
         (circ(40, 20, 2.6), 'natural'), (Polygon([(88, 2), (100, 11), (96, 2)]).buffer(2), 'orange'),
         (box(-12, -30, -6, -4), 'orange'), (tube([(-48, 12), (-30, 40), (-10, 52)], 4, 1.5), 'natural')]
    lines = [LineString([(-20, 26), (60, 24)])]
    return s, lines, 'Raptor Snapper', 'Dinosaur head on a grip. The jaw snaps open to fire one band.'


def dragon_hoard():
    chest = box(-60, 0, 60, 48)
    lid = Polygon([(-63, 48), (63, 48), (63, 58), (40, 66), (0, 69), (-40, 66), (-63, 58)])
    body = tube([(-70, 50), (-50, 78), (-10, 84), (30, 76), (54, 82), (70, 70)], 13, 6)
    tail = tube([(-70, 50), (-78, 25), (-62, 8), (-40, 6)], 6, 2)
    head = Polygon([(58, 78), (86, 82), (100, 74), (84, 66), (62, 68)])
    wing = Polygon([(-20, 90), (10, 96), (34, 88), (6, 84)])
    s = [(chest, 'natural'), (lid, 'natural'), (tail, 'green'), (body, 'green'), (wing, 'purple'),
         (head, 'green'), (circ(84, 77, 2.5), 'yellow')]
    s += [(circ(x, 4, 7), 'gold') for x in (-82, -70, 74, 86)]
    s += [(box(-8, 18, 8, 32), 'gold')]
    lines = [LineString([(-60, 24), (60, 24)]), LineString([(-30, 0), (-30, 48)]), LineString([(30, 0), (30, 48)])]
    return s, lines, 'Hoard Keeper', 'Coiled sleeping dragon on a treasure chest that opens as a trinket box.'


def dragon_glider():
    base = Polygon([(-50, 0), (50, 0), (40, 12), (-40, 12)])
    pole = box(-3, 12, 3, 92)
    body = tube([(-90, 98), (-50, 104), (0, 100), (40, 108), (60, 120)], 3, 12)
    body = tube([(-95, 96), (-55, 103), (-5, 101), (35, 108), (58, 120)], 2.5, 11)
    head = Polygon([(55, 116), (82, 124), (95, 118), (78, 110), (58, 110)])
    wing_l = Polygon([(-20, 104), (-50, 150), (-10, 140), (10, 160), (20, 110)])
    wing_r = Polygon([(-10, 104), (-30, 136), (0, 128), (20, 144), (24, 108)])
    crank = circ(0, 30, 12)
    s = [(base, 'natural'), (pole, 'natural'), (wing_r, 'purple'), (body, 'red'), (head, 'red'), (wing_l, 'pink'),
         (crank, 'gold'), (circ(0, 30, 3), 'natural'), (box(10, 28, 26, 32), 'natural'), (circ(84, 119, 2), 'yellow')]
    lines = [LineString([(0, 42), (0, 98)])]
    return s, lines, 'Sky Glider', 'Flying dragon on a pole. Turn the crank and the wings flap.'


def floral_glasshouse():
    base = box(-58, 0, 58, 24)
    house = Polygon([(-52, 24), (52, 24), (52, 76), (0, 108), (-52, 76)])
    s = [(base, 'pink'), (house, 'white')]
    for x, c in ((-34, 'pink'), (-12, 'yellow'), (12, 'purple'), (34, 'pink')):
        s.append((box(x - 1.5, 24, x + 1.5, 44), 'green'))
        s.append((circ(x, 48, 7), c))
    s.append((box(60, 8, 72, 14).union(circ(76, 11, 6)), 'natural'))
    grid = [LineString([(x, 24), (x, 110)]) for x in (-26, 0, 26)] + [LineString([(-60, y), (60, y)]) for y in (50, 76)]
    lines = [g.intersection(house.buffer(-1)) for g in grid]
    return s, lines, 'Glasshouse Serenade', 'Pastel greenhouse; the flower bed inside turns to the music.'


def floral_carousel():
    base = box(-58, 0, 58, 18)
    roof = Polygon([(-64, 88), (0, 122), (64, 88)])
    scallop = unary_union([circ(x, 88, 8) for x in range(-56, 64, 16)]).intersection(box(-70, 70, 70, 88))
    s = [(base, 'green'), (box(-6, 18, 6, 88), 'natural')]
    for x, y, c in ((-40, 40, 'purple'), (-14, 54, 'yellow'), (14, 36, 'pink'), (40, 50, 'teal')):
        s.append((box(x - 1.3, 18, x + 1.3, 88), 'natural'))
        s.append((affinity.rotate(Polygon([(x, y), (x - 12, y + 10), (x - 10, y - 6)]), 0).union(
            Polygon([(x, y), (x + 12, y + 10), (x + 10, y - 6)])).buffer(1), c))
    s += [(roof, 'pink'), (scallop, 'white'), (circ(0, 128, 8), 'yellow'), (circ(0, 128, 3), 'orange')]
    return s, [], 'Bloom Carousel', 'Flower carousel; butterflies ride the poles up and down.'


def draw_sketch(shapes, lines, path):
    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=160)
    fig.patch.set_facecolor('#fbf6ee'); ax.set_facecolor('#fbf6ee')
    for g, c in shapes:
        for poly in getattr(g, 'geoms', [g]):
            if poly.is_empty or poly.geom_type != 'Polygon':
                continue
            verts = list(poly.exterior.coords); codes = [Path.MOVETO] + [Path.LINETO] * (len(verts) - 2) + [Path.CLOSEPOLY]
            for r in poly.interiors:
                rv = list(r.coords); verts += rv; codes += [Path.MOVETO] + [Path.LINETO] * (len(rv) - 2) + [Path.CLOSEPOLY]
            pp = PathPatch(Path(verts, codes), facecolor=COL[c], edgecolor=INK, lw=1.6, alpha=0.95)
            pp.set_sketch_params(1.2, 60, 1.5)
            ax.add_patch(pp)
    for ln in lines:
        for l in getattr(ln, 'geoms', [ln]):
            if l.is_empty or l.geom_type != 'LineString':
                continue
            xs, ys = l.xy
            a, = ax.plot(xs, ys, color=INK, lw=1.0, alpha=0.7)
            a.set_sketch_params(1.0, 50, 1.5)
    ax.set_aspect('equal'); ax.autoscale_view(); ax.margins(0.08); ax.axis('off')
    fig.savefig(path, facecolor=fig.get_facecolor(), bbox_inches='tight', pad_inches=0.15)
    plt.close(fig)


KITS = {
    'blaster': {
        'title': 'Kit 1: rubber band blaster',
        'concepts': [
            {'id': 'A', 'name': 'Star Slinger', 'chosen': True, 'render': 'kits/blaster/renders/three_quarter.jpg',
             'pitch': 'Starship with a clockwork star wheel: 7 bands, one per pull. Stand, target and safety plaque.',
             'scores': [4, 5, 4, 5, 4, 3],
             'why': 'Most fun per dollar: 7 shots, a mechanism you can see working, and it reads as a spaceship, not a gun.'},
            {'id': 'B', 'sketch': blaster_turret, 'scores': [3, 4, 3, 3, 4, 3],
             'why': 'Fun on a desk, but more parts for the pan, tilt and carousel (cost and cut time up). Less to hold.'},
            {'id': 'C', 'sketch': blaster_raptor, 'scores': [4, 3, 4, 4, 5, 4],
             'why': 'Very original and simple, but one shot per load gets boring fast (review rule H1: play value).'},
        ]},
    'dragon': {
        'title': 'Kit 2: dragon',
        'concepts': [
            {'id': 'A', 'name': 'Emberwing', 'chosen': True, 'render': 'kits/dragon/renders/three_quarter.jpg',
             'pitch': 'Dragon rearing on a ruined tower, claws on the battlements. Jaw and chest lid move. Layered wings.',
             'scores': [5, 4, 3, 3, 4, 4],
             'why': 'Strongest silhouette on a shelf; two simple moving parts; the tower gives a story and a base.'},
            {'id': 'B', 'sketch': dragon_hoard, 'scores': [4, 3, 4, 4, 3, 5],
             'why': 'Useful as a box and easy to cut, but dragon-on-chest boxes already exist and it hides the wings.'},
            {'id': 'C', 'sketch': dragon_glider, 'scores': [4, 5, 2, 2, 4, 2],
             'why': 'Flapping is great fun, but the crank linkage adds parts, cut time and the top review complaint (mechanism).'},
        ]},
    'floral': {
        'title': 'Kit 3: pastel floral gift',
        'concepts': [
            {'id': 'A', 'name': 'Blossom Waltz', 'chosen': True, 'render': 'kits/floral/renders/three_quarter.jpg',
             'pitch': 'Bouquet of 7 flowers in a vase that turns on a wind-up music box. Picket fence and butterflies.',
             'scores': [4, 4, 3, 3, 4, 4],
             'why': 'Flowers that never wilt plus music: the clearest gift. Nearly empty space in the market map.'},
            {'id': 'B', 'sketch': floral_glasshouse, 'scores': [4, 3, 3, 3, 4, 4],
             'why': 'Charming, but the glass panes would be open frames: fragile thin bars and flowers hidden inside.'},
            {'id': 'C', 'sketch': floral_carousel, 'scores': [4, 4, 3, 3, 3, 3],
             'why': 'Up-and-down riders need a cam ring (more risk); carousels are already a big ROKR/Robotime line.'},
        ]},
}


def total(scores):
    return round(sum(s * w for s, w in zip(scores, WEIGHTS)), 2)


def card(c, W=620, H=820):
    im = Image.new('RGB', (W, H), (255, 252, 246))
    d = ImageDraw.Draw(im)
    f_t = ImageFont.truetype(BOLD, 30); f_b = ImageFont.truetype(FONT, 19); f_s = ImageFont.truetype(BOLD, 19)
    pic = Image.open(c['image']).convert('RGB')
    pic.thumbnail((W - 40, 400))
    im.paste(pic, ((W - pic.width) // 2, 20 + (400 - pic.height) // 2))
    y = 440
    d.text((24, y), f"{c['id']}. {c['name']}", font=f_t, fill=(40, 28, 18)); y += 44
    for line in wrap(c['pitch'], f_b, W - 48, d):
        d.text((24, y), line, font=f_b, fill=(70, 55, 40)); y += 26
    y += 8
    for crit, sc in zip(CRITERIA, c['scores']):
        d.text((24, y), crit, font=f_b, fill=(70, 55, 40))
        for k in range(5):
            x0 = 160 + k * 34
            d.rounded_rectangle([x0, y + 2, x0 + 28, y + 22], 5, fill=(255, 106, 19) if k < sc else (236, 226, 210))
        y += 30
    d.text((24, y + 4), f"Weighted score: {total(c['scores']):.2f} / 5", font=f_s, fill=(40, 28, 18))
    if c.get('chosen'):
        d.rounded_rectangle([W - 170, 16, W - 16, 56], 10, fill=(43, 122, 120))
        d.text((W - 152, 24), 'CHOSEN', font=f_s, fill=(255, 255, 255))
        d.rectangle([0, 0, W - 1, H - 1], outline=(43, 122, 120), width=6)
    else:
        d.rectangle([0, 0, W - 1, H - 1], outline=(214, 200, 178), width=2)
    return im


def wrap(text, font, width, d):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) > width:
            lines.append(cur); cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def main():
    os.makedirs(OUT, exist_ok=True)
    md = ['# Concept directions', '',
          'Three directions per kit, scored 1 to 5 (5 = best; for Cut time, Cost and Risk 5 means fastest, cheapest, '
          'lowest risk). Weights: Looks 25%, Fun 25%, Unique 20%, Cut time 10%, Cost 10%, Risk 10%. '
          'Scores are my judgment (Estimate), using the review rules in `research/review_mining.md` and the white-space '
          'map in the research dashboard. Runner-up sketches are kept here so they can be built later.', '']
    for kit, spec in KITS.items():
        cards = []
        md += [f"## {spec['title']}", '', '| Direction | ' + ' | '.join(CRITERIA) + ' | Weighted | Verdict |',
               '|---|' + '---|' * (len(CRITERIA) + 2)]
        for c in spec['concepts']:
            if 'sketch' in c:
                shapes, lines, name, pitch = c['sketch']()
                c['name'], c['pitch'] = name, pitch
                p = os.path.join(OUT, f"{kit}_{c['id']}_{name.lower().replace(' ', '_')}.png")
                draw_sketch(shapes, lines, p)
                c['image'] = p
            else:
                c['image'] = os.path.join(ROOT, c['render'])
            cards.append(card(c))
            verdict = 'CHOSEN' if c.get('chosen') else 'Runner-up'
            md.append(f"| {c['id']}. {c['name']}: {c['pitch']} | " + ' | '.join(str(s) for s in c['scores']) +
                      f" | {total(c['scores']):.2f} | {verdict}: {c['why']} |")
        board = Image.new('RGB', (3 * 620 + 4 * 24, 820 + 110), (246, 239, 228))
        d = ImageDraw.Draw(board)
        d.text((24, 28), spec['title'] + ': three directions', font=ImageFont.truetype(BOLD, 40), fill=(40, 28, 18))
        for i, cimg in enumerate(cards):
            board.paste(cimg, (24 + i * 644, 90))
        board.save(os.path.join(OUT, f'{kit}_concepts.png'))
        md += ['', f'![{kit} concepts]({kit}_concepts.png)', '']
    open(os.path.join(OUT, 'CONCEPTS.md'), 'w').write('\n'.join(md) + '\n')
    print('concept boards written to', OUT)


if __name__ == '__main__':
    main()
