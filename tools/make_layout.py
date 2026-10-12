"""Workshop layout for a one-car garage (top view, to scale): production/layout/workshop_layout.svg + .png

    .venv/bin/python tools/make_layout.py

Room size and the laser footprint are Estimates (measure both before building benches; see TODO_LUCAS).
The eufyMake E1 size is Verified (590 x 250 mm). Stations follow the SOP flow: sheets -> (print) -> laser -> pop-out
check -> kitting -> packed shelf -> door. The packing bench faces the laser so cuts stay attended.
"""
import os
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'production', 'layout')
FT = 40                       # px per foot
OX, OY = 50, 110              # plan origin (top-left inner wall corner)
RW, RH = 20, 12               # room, feet (Estimate: typical one-car garage)
WAL, WAL2, OAK, MAPLE, BIRCH, PAPER = '#3A2A1F', '#5C4636', '#B9895B', '#EBD5B0', '#F6EEE1', '#FCF8F1'
LAG, LAGD, LAGL, RED, GREEN, GRAY = '#0F8B7F', '#0B6158', '#D7EFEB', '#b3261e', '#1d7a3a', '#8c8579'


def X(f):
    return OX + f * FT


def Y(f):
    return OY + f * FT


def rect(x, y, w, h, fill, stroke=WAL, sw=2, rx=4, extra=''):
    return f'<rect x="{X(x):.1f}" y="{Y(y):.1f}" width="{w * FT:.1f}" height="{h * FT:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def text(x, y, s, size=13, weight=600, color=WAL, anchor='middle'):
    return f'<text x="{X(x):.1f}" y="{Y(y):.1f}" font-family="Inter, Arial, sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{s}</text>'


def badge(x, y, n, color=LAG):
    return (f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="13" fill="{color}" stroke="#fff" stroke-width="2"/>'
            f'<text x="{X(x):.1f}" y="{Y(y) + 5:.1f}" font-family="Inter, Arial, sans-serif" font-size="14" font-weight="800" fill="#fff" text-anchor="middle">{n}</text>')


def arrow(pts, color=LAG, sw=4, dash=''):
    d = 'M' + ' L'.join(f'{X(a):.1f},{Y(b):.1f}' for a, b in pts)
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round" {dash} marker-end="url(#head{color[1:]})"/>'


STATIONS = [
    # n, x, y, w, h, fill, label lines, legend text
    (1, 0.3, 0.3, 2.2, 2.2, BIRCH, ['Sheet', 'rack'], 'Flat sheet rack by color, off the floor. New sheets rest here 48 h before cutting (Estimate).'),
    (2, 2.9, 0.3, 2.4, 1.9, '#fff', ['', 'UV printer'], 'UV printer table (only with printed color). eufyMake E1 is 590 x 250 mm (Verified).'),
    (3, 6.0, 0.3, 6.0, 2.6, MAPLE, ['Laser bench'], 'Laser bench, 6 x 2.5 ft. OMTech Polar 2 with LightBurn computer at the right end.'),
    (4, 13.3, 0.4, 1.4, 1.4, '#e9e4dc', ['Scrap', 'bin'], 'Metal scrap bin with lid. Empty it outside at the end of each day (SOP-1).'),
    (5, 6.0, 9.0, 8.0, 2.7, MAPLE, ['Pop-out check and kitting bench'], 'Pop-out check and kitting bench, 8 x 2.7 ft, with a lamp. It faces the laser, so you pack while you watch the cut.'),
    (6, 14.4, 10.2, 3.0, 1.5, BIRCH, ['Extras bins'], 'Extras bins: bands, dowels (with the saw jig), wax, sandpaper, movements, small bags.'),
    (7, 2.4, 10.0, 3.2, 1.7, BIRCH, ['Boxes and', 'booklets'], 'Mailer boxes, booklets, labels and filler. Next to the left end of the kitting bench.'),
    (8, 17.9, 6.6, 1.8, 5.1, BIRCH, ['Packed', 'kits'], 'Packed kits shelf, by the garage door for pickup and drop-off.'),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    W, H = 1240, 760
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         '<defs>' + ''.join(
             f'<marker id="head{c[1:]}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">'
             f'<path d="M0,0 L10,5 L0,10 Z" fill="{c}"/></marker>' for c in (LAG, GREEN, GRAY)) +
         f'<pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="8" stroke="{GREEN}" stroke-width="2" stroke-opacity=".25"/></pattern></defs>',
         f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
         f'<text x="50" y="48" font-family="Fraunces, Georgia, serif" font-size="28" font-weight="700" fill="{WAL}">Workshop layout: one-car garage</text>',
         f'<text x="50" y="76" font-family="Inter, Arial, sans-serif" font-size="14" fill="{WAL2}">Top view to scale. Room 20 x 12 ft and the laser size are Estimates: measure yours first. Numbers follow the work flow.</text>']
    # walls
    s.append(f'<rect x="{X(0) - 8}" y="{Y(0) - 8}" width="{RW * FT + 16}" height="{RH * FT + 16}" fill="{WAL}" rx="2"/>')
    s.append(f'<rect x="{X(0)}" y="{Y(0)}" width="{RW * FT}" height="{RH * FT}" fill="#fbf6ee"/>')
    # garage door (right wall), house door (left wall), window (top wall)
    s.append(f'<rect x="{X(RW) - 2}" y="{Y(1.5)}" width="12" height="{9 * FT}" fill="#d9d2c5" stroke="{WAL}" stroke-width="1.5"/>')
    s.append(f'<text x="{X(RW) + 26}" y="{Y(6)}" font-family="Inter, Arial, sans-serif" font-size="13" font-weight="700" fill="{WAL2}" text-anchor="middle" transform="rotate(90 {X(RW) + 26} {Y(6)})">Garage door (9 ft)</text>')
    s.append(f'<rect x="{X(0) - 10}" y="{Y(7.6)}" width="14" height="{3 * FT}" fill="#fbf6ee"/>')
    s.append(f'<path d="M{X(0)},{Y(7.6)} A{3 * FT},{3 * FT} 0 0,1 {X(3)},{Y(10.6)}" fill="none" stroke="{GRAY}" stroke-width="1.5" stroke-dasharray="4 4"/>'
             f'<line x1="{X(0)}" y1="{Y(7.6)}" x2="{X(0)}" y2="{Y(10.6)}" stroke="{WAL2}" stroke-width="4"/>')
    s.append(f'<text x="{X(0) - 26}" y="{Y(9.1)}" font-family="Inter, Arial, sans-serif" font-size="13" font-weight="700" fill="{WAL2}" text-anchor="middle" transform="rotate(-90 {X(0) - 26} {Y(9.1)})">House door</text>')
    s.append(f'<rect x="{X(7.5)}" y="{Y(0) - 10}" width="{3 * FT}" height="12" fill="#cfe8f0" stroke="{WAL}" stroke-width="1.5"/>')
    s.append(text(9, -0.55, 'Window with exhaust vent', 13, 700, WAL2))
    # escape route
    s.append(f'<rect x="{X(0.2)}" y="{Y(3.6)}" width="{17.4 * FT}" height="{4.9 * FT}" fill="url(#hatch)" rx="8"/>')
    s.append(text(10.8, 6.3, 'Keep clear: walkway and exit routes (3 ft or more)', 14, 700, GREEN))
    # stations
    for n, x, y, w, h, fill, lines, _ in STATIONS:
        s.append(rect(x, y, w, h, fill))
        if n == 2:
            s.append(rect(3.15, 0.5, 1.94, 0.82, '#e6ded1', WAL, 1.5, 3))
        cy = y + h / 2 - (len(lines) - 1) * 0.2 + 0.12
        for i, ln in enumerate(lines):
            s.append(text(x + w / 2, cy + i * 0.4, ln, 14 if w > 2 else 12, 700))
        s.append(badge(x + 0.05, y + 0.05, n))
    # laser and computer on the bench, duct to the window
    s.append(rect(6.4, 0.45, 3.9, 2.25, '#ffffff', WAL, 2, 6))
    s.append(rect(6.75, 0.75, 2.33, 1.18, '#e6ded1', WAL2, 1, 2))
    s.append(text(8.35, 2.4, 'Polar 2 (Estimate size)', 11, 600, WAL2))
    s.append(rect(10.6, 0.7, 1.1, 0.7, '#2d3a33', WAL, 1.5, 3))
    s.append(text(11.15, 1.85, 'PC', 11, 700, WAL2))
    s.append(f'<path d="M{X(8.8)},{Y(0.45)} L{X(8.8)},{Y(0) - 2}" stroke="{GRAY}" stroke-width="10"/>')
    # fire kit, first aid, heater, smoke alarm
    s.append(f'<rect x="{X(12.35)}" y="{Y(0.15)}" width="16" height="34" rx="5" fill="{RED}" stroke="{WAL}" stroke-width="1.5"/>')
    s.append(text(12.55, 1.55, 'CO2 +', 11, 800, RED) + text(12.55, 1.9, 'blanket', 11, 800, RED))
    s.append(f'<rect x="{X(0.15)}" y="{Y(6.6)}" width="22" height="22" rx="3" fill="#fff" stroke="{RED}" stroke-width="2"/>'
             f'<path d="M{X(0.15) + 11},{Y(6.6) + 5} v12 M{X(0.15) + 5},{Y(6.6) + 11} h12" stroke="{RED}" stroke-width="3"/>')
    s.append(text(1.0, 6.95, 'First aid,', 11, 700, WAL2, 'start') + text(1.0, 7.3, 'call card', 11, 700, WAL2, 'start'))
    s.append(rect(0.3, 4.0, 1.0, 0.8, '#fde7e5', RED, 1.5, 3) + text(1.5, 4.5, 'Heater: keep above 10 °C', 11, 700, WAL2, 'start'))
    s.append(f'<circle cx="{X(10)}" cy="{Y(4.6)}" r="9" fill="#fff" stroke="{WAL}" stroke-width="1.5"/><circle cx="{X(10)}" cy="{Y(4.6)}" r="3" fill="{RED}"/>')
    s.append(text(10.4, 4.72, 'Smoke alarm (ceiling)', 11, 600, WAL2, 'start'))
    # tablet and saw jig on the kitting bench
    s.append(rect(12.6, 9.3, 0.9, 0.6, '#2d3a33', WAL, 1.2, 3) + text(13.05, 10.3, 'Planner', 10, 700, WAL2))
    s.append(rect(6.3, 10.9, 1.6, 0.5, '#d0d4d8', WAL, 1.2, 2) + text(7.1, 10.75, 'Dowel jig', 10, 700, WAL2))
    # flow arrows
    s.append(arrow([(2.5, 1.4), (2.9, 1.4)], LAG, 4))
    s.append(arrow([(5.3, 1.1), (6.0, 1.1)], LAG, 4))
    s.append(arrow([(1.4, 2.5), (1.4, 3.2), (5.7, 3.2), (6.3, 2.9)], LAG, 3, 'stroke-dasharray="7 5"'))
    s.append(text(3.3, 3.05, 'natural or pre-colored sheets', 11, 600, LAGD))
    s.append(arrow([(9.0, 2.9), (9.0, 8.95)], LAG, 4))
    s.append(text(9.15, 8.3, 'cut sheets', 11, 700, LAGD, 'start'))
    s.append(arrow([(14.0, 10.0), (17.85, 9.0)], LAG, 4))
    s.append(arrow([(19.7, 8.0), (20.5, 8.0)], LAG, 4))
    s.append(f'<path d="M{X(9.6)},{Y(8.9)} C{X(9.6)},{Y(6)} {X(10.2)},{Y(4)} {X(10.2)},{Y(3.0)}" fill="none" stroke="{GRAY}" stroke-width="2" stroke-dasharray="3 5" marker-end="url(#head{GRAY[1:]})"/>')
    s.append(text(10.0, 7.9, 'line of sight', 10, 600, GRAY, 'start'))
    # exit arrows
    s.append(arrow([(6.0, 4.4), (1.2, 8.6), (0.35, 9.1)], GREEN, 3, 'stroke-dasharray="8 6"'))
    s.append(arrow([(13.0, 4.4), (19.6, 4.4)], GREEN, 3, 'stroke-dasharray="8 6"'))
    # scale bar
    sb_y = Y(RH) + 40
    s.append(f'<rect x="{X(0)}" y="{sb_y}" width="{5 * FT}" height="6" fill="{WAL}"/>' + ''.join(
        f'<rect x="{X(i)}" y="{sb_y}" width="{FT}" height="6" fill="#fff" stroke="{WAL}" stroke-width="1"/>' for i in (1, 3)))
    s.append(f'<text x="{X(0)}" y="{sb_y + 22}" font-family="Inter, Arial, sans-serif" font-size="12" fill="{WAL2}">0</text>'
             f'<text x="{X(5)}" y="{sb_y + 22}" font-family="Inter, Arial, sans-serif" font-size="12" fill="{WAL2}" text-anchor="middle">5 ft (1.5 m)</text>')
    # legend
    lx = 940
    s.append(f'<text x="{lx}" y="{Y(0) + 4}" font-family="Fraunces, Georgia, serif" font-size="18" font-weight="700" fill="{WAL}">Stations</text>')
    yy = Y(0) + 26
    import textwrap
    for n, *_rest, legend in STATIONS:
        s.append(f'<circle cx="{lx + 12}" cy="{yy}" r="11" fill="{LAG}"/><text x="{lx + 12}" y="{yy + 4.5}" font-family="Inter, Arial, sans-serif" font-size="12" font-weight="800" fill="#fff" text-anchor="middle">{n}</text>')
        for i, ln in enumerate(textwrap.wrap(legend, 38)):
            s.append(f'<text x="{lx + 30}" y="{yy + 5 + i * 16}" font-family="Inter, Arial, sans-serif" font-size="12.5" fill="{WAL}">{ln}</text>')
        yy += 16 * len(textwrap.wrap(legend, 38)) + 12
    yy += 6
    for color, dash, label in ((LAG, '', 'Work flow'), (GREEN, 'stroke-dasharray="8 6"', 'Exit route, keep clear'), (GRAY, 'stroke-dasharray="3 5"', 'Line of sight to the laser')):
        s.append(f'<line x1="{lx}" y1="{yy}" x2="{lx + 26}" y2="{yy}" stroke="{color}" stroke-width="3" {dash}/>'
                 f'<text x="{lx + 34}" y="{yy + 4.5}" font-family="Inter, Arial, sans-serif" font-size="12.5" fill="{WAL}">{label}</text>')
        yy += 20
    s.append('</svg>')
    svg_path = os.path.join(OUT, 'workshop_layout.svg')
    open(svg_path, 'w').write('\n'.join(s))
    html = os.path.join(OUT, '_tmp.html')
    fonts = os.path.join(ROOT, 'brand', 'fonts')
    open(html, 'w').write(f"""<html><head><style>@font-face{{font-family:Fraunces;src:url(file://{fonts}/Fraunces-700.ttf);font-weight:700}}
@font-face{{font-family:Inter;src:url(file://{fonts}/Inter-400.ttf);font-weight:400}}@font-face{{font-family:Inter;src:url(file://{fonts}/Inter-600.ttf);font-weight:600}}
@font-face{{font-family:Inter;src:url(file://{fonts}/Inter-700.ttf);font-weight:700}}@font-face{{font-family:Inter;src:url(file://{fonts}/Inter-800.ttf);font-weight:800}}
body{{margin:0}}</style></head><body>{open(svg_path).read()}</body></html>""")
    subprocess.run(['node', os.path.join(ROOT, 'tools', 'shot.js'), html, os.path.join(OUT, 'workshop_layout.png'), str(W), str(H), '0', 'light', '400'], check=True)
    os.remove(html)
    print('layout written')


if __name__ == '__main__':
    main()
