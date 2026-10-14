"""Packaging for each kit: print-ready labels for the launch box, an optional retail sleeve, and mockups.

    .venv/bin/python brand/make_packaging.py

Launch packaging (in the BOM): a plain white 12 x 12 x 2 in mailer with
  - a 4 x 4 in lid label (front of the product), and
  - a 4 x 2 in info label on the bottom (identity, contents, maker, warnings, batch code box).
Phase 2 (retail or wholesale): a full-color sleeve that slides over the same mailer.

Output in brand/packaging/: <kit>_lid_label.pdf/.png, <kit>_info_label.pdf/.png, <kit>_sleeve.pdf/.png,
sleeve_dieline.svg, mockup_<kit>.png, mockup_lineup.png, and proof images with trim and safe lines.
Print PDFs include 0.125 in bleed on every side. Proof PNGs show the trim (solid) and safe area (dashed).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import qrcode
import qrcode.image.svg

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'engine'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from hartwood import config as C  # noqa: E402
import make_supply as MS  # noqa: E402

OUT = os.path.join(ROOT, 'brand', 'packaging')
BLEED = 0.125
KITS = ['blaster', 'dragon', 'floral']
THEME = {
    'blaster': {'accent': '#1f5f86', 'accent2': '#FF6A13', 'tint': '#dceaf3', 'tint2': '#f3f8fb'},
    'dragon': {'accent': '#8e2a20', 'accent2': '#c99a2e', 'tint': '#f3dfcf', 'tint2': '#fbf3ec'},
    'floral': {'accent': '#a8406a', 'accent2': '#4f9d84', 'tint': '#f6dde8', 'tint2': '#fcf3f7'},
}
WARN = {
    'blaster': 'Shoots rubber bands. Wear eye protection. Never aim at faces, people or animals. Use #64 bands only. Keep the blaze orange tip on.',
    'dragon': 'Moving jaw and chest lid: do not force them past their stops.',
    'floral': 'Wind-up music movement inside: wind gently, do not over-wind.',
}
FEATURE = {
    'blaster': 'Clockwork star wheel: load seven bands, fire one per pull.',
    'dragon': 'The jaw opens and the treasure chest lid lifts.',
    'floral': 'Wind the key: the bouquet turns while the music plays.',
}
# box outside size in inches (Estimate: Uline S-5817 is 12 x 12 x 2 inside; measure a real box before ordering sleeves)
BOX = {'w': 12.0, 'top': 12.3, 'side': 2.15, 'glue': 0.6}


def site_host():
    return C.SITE_URL.replace('https://', '').replace('http://', '').rstrip('/')


def qr_svg(url, path):
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, border=1)
    img.save(path)
    return os.path.basename(path)


def kit_facts(kit):
    rep = json.load(open(os.path.join(ROOT, 'kits', kit, f'{kit}_report.json')))
    steps = json.load(open(os.path.join(ROOT, 'kits', kit, f'{kit}_steps.json')))
    _, _, rows = MS.kit_bom(kit)
    bands = sum(q for i, q, _ in rows if i.startswith('band_'))
    rods = [h for h in rep['hardware'] if h['kind'] == 'rod' and 'dowel' in h['note']]
    spares = sum(s.get('spares', 0) for s in rep['sheets'])
    contents = [f"{steps['piece_count']} wooden parts on {len(rep['sheets'])} sheets"]
    if spares:
        contents[0] += f' (plus {spares} spare small parts)'
    if rods:
        contents.append(f"{len(rods)} birch dowel{'s' if len(rods) > 1 else ''}")
    if bands:
        contents.append(f'{bands:g} rubber bands')
    for i, q, n in rows:
        if i == 'movement':
            contents.append('1 wind-up music movement')
        if i == 'targets':
            contents.append(f'{q:g} paper targets')
    contents += ['wax stick' for i, q, n in rows if i == 'wax'] + ['sandpaper', 'picture instruction booklet']
    size = size_mm(kit)
    return {'kit': kit, 'name': steps['name'], 'tagline': steps['tagline'], 'story': steps['story'], 'pieces': steps['piece_count'],
            'hours': steps['build_hours'], 'difficulty': steps['difficulty'], 'spares': spares, 'contents': ', '.join(contents),
            'size_cm': ' x '.join(f'{v / 10:.0f}' for v in size), 'size_in': ' x '.join(f'{v / 25.4:.1f}' for v in size),
            'sheets': [s['sheet'] for s in rep['sheets']], 'colors': [s['color'] for s in rep['sheets']]}


def size_mm(kit):
    """Finished model length x width x height from the GLB (y is up)."""
    import trimesh
    sc = trimesh.load(os.path.join(ROOT, 'kits', kit, f'{kit}.glb'))
    x, y, z = (v * 1000 for v in sc.extents)
    return (max(x, z), min(x, z), y)


FONTS = """
@font-face { font-family: Fraunces; src: url(../fonts/Fraunces-700.ttf); font-weight: 700; }
@font-face { font-family: Fraunces; src: url(../fonts/Fraunces-800.ttf); font-weight: 800; }
@font-face { font-family: Inter; src: url(../fonts/Inter-400.ttf); font-weight: 400; }
@font-face { font-family: Inter; src: url(../fonts/Inter-600.ttf); font-weight: 600; }
@font-face { font-family: Inter; src: url(../fonts/Inter-700.ttf); font-weight: 700; }
@font-face { font-family: Inter; src: url(../fonts/Inter-800.ttf); font-weight: 800; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: Inter, Arial, sans-serif; color: #3A2A1F; background: #fff; }
.abs { position: absolute; }
.guide { position: absolute; pointer-events: none; z-index: 50; }
.trim { border: 1px solid #e0007a; }
.safe { border: 1px dashed #00a0e0; }
.fold { border-left: 1px dashed #e0007a; }
.hfold { border-top: 1px dashed #e0007a; }
"""


def guides(w, h, folds=(), proof=True):
    if not proof:
        return ''
    g = [f'<div class="guide trim" style="left:{BLEED}in;top:{BLEED}in;width:{w - 2 * BLEED}in;height:{h - 2 * BLEED}in"></div>',
         f'<div class="guide safe" style="left:{BLEED + 0.125}in;top:{BLEED + 0.125}in;width:{w - 2 * BLEED - 0.25}in;height:{h - 2 * BLEED - 0.25}in"></div>']
    for y in folds:
        g.append(f'<div class="guide hfold" style="left:0;top:{y}in;width:{w}in;height:0"></div>')
    return ''.join(g)


def chips(f, t, size='8pt'):
    return (f'<span>{f["pieces"]} parts</span><span>No glue</span><span>{f["hours"]}</span>')


def lid_label(f, proof):
    t = THEME[f['kit']]
    W = H = 4 + 2 * BLEED
    qr = qr_svg(f'{C.SITE_URL}/build/{f["kit"]}', os.path.join(OUT, f'qr_build_{f["kit"]}.svg'))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}
.page {{ position: relative; width: {W}in; height: {H}in; overflow: hidden; background: radial-gradient(circle at 50% 46%, #fff 0, {t['tint2']} 38%, {t['tint']} 75%); }}
.logo {{ left: 0.33in; top: 0.32in; width: 1.45in; }}
.age {{ right: 0.33in; top: 0.28in; width: 0.56in; height: 0.56in; border-radius: 50%; background: #3A2A1F; color: #fff; text-align: center;
  font: 800 13pt/1 Inter; padding-top: 0.1in; }}
.age small {{ display: block; font: 700 5.5pt Inter; letter-spacing: .06em; margin-top: 1px; }}
.hero {{ left: 50%; top: 0.62in; height: 2.2in; transform: translateX(-50%); filter: drop-shadow(0 0.04in 0.05in rgba(58,42,31,.25)); }}
.name {{ left: 0; right: 0; top: 2.78in; text-align: center; font: 800 25pt/1 Fraunces; color: #3A2A1F; }}
.tag {{ left: 0.45in; right: 0.45in; top: 3.16in; text-align: center; font: 600 7pt/1.25 Inter; color: #5C4636; }}
.band {{ left: 0; right: 0; bottom: 0; height: {0.6 + BLEED}in; background: {t['accent']}; padding: 0.1in {0.3 + 0.62}in {BLEED}in 0.33in;
  display: flex; align-items: center; gap: 0.1in; color: #fff; font: 800 7pt Inter; letter-spacing: .07em; text-transform: uppercase; }}
.band span + span::before {{ content: ""; display: inline-block; width: 4px; height: 4px; border-radius: 50%; background: {t['accent2']}; margin: 0 0.08in 1px 0; vertical-align: middle; }}
.qr {{ right: 0.3in; bottom: {BLEED + 0.06}in; width: 0.5in; height: 0.5in; background: #fff; border-radius: 4px; padding: 2px; }}
.qrlab {{ right: 0.86in; bottom: {BLEED + 0.4}in; font: 700 4.5pt Inter; color: #fff; opacity: .9; letter-spacing: .05em; text-transform: uppercase; }}
</style></head><body><div class="page">
<img class="abs logo" src="../logo.svg" alt="Hartwood Designs">
<div class="abs age">14+<small>AGES</small></div>
<img class="abs hero" src="../../kits/{f['kit']}/renders/raw/three_quarter.webp" alt="">
<div class="abs name">{f['name']}</div>
<div class="abs tag">{f['tagline']}</div>
<div class="abs band">{chips(f, t)}</div>
<div class="abs qrlab">Build in 3D</div>
<img class="abs qr" src="{qr}" alt="">
{guides(W, H, proof=proof)}
</div></body></html>"""


def info_label(f, proof):
    t = THEME[f['kit']]
    W, H = 4 + 2 * BLEED, 2 + 2 * BLEED
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}
.page {{ position: relative; width: {W}in; height: {H}in; overflow: hidden; background: #fff; }}
.bar {{ left: 0; top: 0; bottom: 0; width: {0.16 + BLEED}in; background: {t['accent']}; }}
.col1 {{ left: 0.42in; top: 0.27in; width: 2.3in; font: 400 5.6pt/1.3 Inter; }}
.col1 h1 {{ font: 800 9pt/1.1 Fraunces; margin-bottom: 2px; }}
.col1 b {{ font-weight: 700; }}
.col1 p {{ margin-bottom: 3px; }}
.col2 {{ left: 2.82in; top: 0.27in; width: 1.1in; font: 400 5.4pt/1.25 Inter; }}
.warn {{ border: 1.2px solid #3A2A1F; border-radius: 4px; padding: 3px 4px; margin-bottom: 4px; }}
.warn b {{ display: block; font: 800 6pt Inter; letter-spacing: .04em; }}
.batch {{ border: 1px solid #3A2A1F; border-radius: 3px; height: 0.3in; padding: 2px 4px; font: 700 5pt Inter; text-transform: uppercase; letter-spacing: .05em; }}
.mark {{ right: 0.3in; bottom: 0.26in; width: 0.32in; }}
</style></head><body><div class="page">
<div class="abs bar"></div>
<div class="abs col1">
<h1>{f['name']}: wooden 3D model kit</h1>
<p><b>Contents:</b> {f['contents']}.</p>
<p><b>Finished size:</b> about {f['size_cm']} cm ({f['size_in']} in). <b>Build time:</b> {f['hours']}. No glue or tools needed.</p>
<p><b>Made by:</b> Hartwood Designs, TODO_LUCAS city, Minnesota, USA. {site_host()}</p>
<p>Designed and laser cut in Minnesota with imported materials.</p>
</div>
<div class="abs col2">
<div class="warn"><b>WARNING</b>Small parts. Not for children under 14. {WARN[f['kit']]}</div>
<div class="batch">Batch</div>
</div>
<img class="abs mark" src="../logo_mark.svg" alt="">
{guides(W, H, proof=proof)}
</div></body></html>"""


def sleeve(f, proof):
    """Vertical flat: top panel, front edge, bottom panel, back edge (upside down), glue flap."""
    t = THEME[f['kit']]
    b = BOX
    W = b['w'] + 2 * BLEED
    y_top = BLEED
    y_front = y_top + b['top']
    y_bottom = y_front + b['side']
    y_back = y_bottom + b['top']
    y_glue = y_back + b['side']
    H = y_glue + b['glue'] + BLEED
    qr = qr_svg(f'{C.SITE_URL}/build/{f["kit"]}', os.path.join(OUT, f'qr_build_{f["kit"]}.svg'))
    sheets = ''.join(f'<img src="../../kits/{f["kit"]}/parts_map/sheet_{s}.png" style="transform:rotate({r}deg)">'
                     for s, r in zip(pick_sheets(f), (-6, 0, 6)))
    dots = ''.join(f'<i class="{"on" if i < f["difficulty"] else ""}"></i>' for i in range(5))
    closeups = sorted(x for x in os.listdir(os.path.join(ROOT, 'kits', f['kit'], 'renders', 'raw')) if x.startswith('closeup'))[:3]
    cl = ''.join(f'<div class="cu"><img src="../../kits/{f["kit"]}/renders/raw/{x}"></div>' for x in closeups)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}
.page {{ position: relative; width: {W}in; height: {H}in; overflow: hidden; background: #fff; }}
.panel {{ position: absolute; left: 0; width: {W}in; overflow: hidden; }}
.top {{ top: 0; height: {y_front}in; background: radial-gradient(circle at 50% 52%, #fff 0, {t['tint2']} 35%, {t['tint']} 72%); }}
.top .logo {{ left: 0.7in; top: 0.7in; width: 3.2in; }}
.top .age {{ right: 0.7in; top: 0.62in; width: 1.15in; height: 1.15in; border-radius: 50%; background: #3A2A1F; color: #fff; text-align: center; font: 800 26pt/1 Inter; padding-top: 0.22in; }}
.top .age small {{ display: block; font: 700 9pt Inter; letter-spacing: .08em; }}
.top .hero {{ left: 50%; top: 1.6in; height: 7.4in; transform: translateX(-50%); filter: drop-shadow(0 0.08in 0.1in rgba(58,42,31,.25)); }}
.top .name {{ left: 0.7in; top: 9.15in; font: 800 54pt/1 Fraunces; }}
.top .tag {{ left: 0.72in; top: 10.12in; width: 6.6in; font: 600 13pt/1.3 Inter; color: #5C4636; }}
.top .feat {{ right: 0.7in; top: 9.25in; width: 3.6in; background: {t['accent']}; color: #fff; border-radius: 0.18in; padding: 0.16in 0.2in; font: 700 11pt/1.3 Inter; }}
.top .feat b {{ display: block; color: {t['accent2']}; font: 800 8pt Inter; letter-spacing: .1em; text-transform: uppercase; margin-bottom: 2px; }}
.top .chips {{ left: 0.7in; top: 10.95in; display: flex; gap: 0.12in; }}
.chips span {{ background: #fff; border: 1.5px solid #3A2A1F; border-radius: 999px; padding: 0.06in 0.2in; font: 700 13pt Inter; }}
.front {{ top: {y_front}in; height: {b['side']}in; background: {t['accent']}; color: #fff; display: flex; align-items: center; justify-content: space-between; padding: 0 0.7in; }}
.front .nm {{ font: 800 28pt Fraunces; }}
.front .mk {{ height: 0.9in; }}
.front .meta {{ font: 700 11pt Inter; text-align: right; line-height: 1.4; letter-spacing: .04em; }}
.bottom {{ top: {y_bottom}in; height: {b['top']}in; background: #FCF8F1; padding: 0.6in 0.7in; display: flex; flex-direction: column; gap: 0.3in; }}
.row1 {{ display: grid; grid-template-columns: 1fr 4.7in; gap: 0.4in; }}
.bottom h2 {{ font: 800 28pt Fraunces; margin-bottom: 0.12in; }}
.bottom .story {{ font: 400 12.5pt/1.45 Inter; color: #3A2A1F; }}
.sheets {{ position: relative; height: 2.75in; }}
.sheets img {{ position: absolute; top: 0.1in; width: 2.0in; border: 2px solid #fff; box-shadow: 0 0.03in 0.08in rgba(0,0,0,.25); }}
.sheets img:nth-child(1) {{ left: 0; }} .sheets img:nth-child(2) {{ left: 1.35in; top: 0; }} .sheets img:nth-child(3) {{ left: 2.7in; }}
.sheets p {{ position: absolute; top: 2.35in; left: 0; right: 0; text-align: center; font: 700 10.5pt Inter; color: #5C4636; }}
.cus {{ display: flex; gap: 0.2in; height: 2.9in; }}
.cu {{ flex: 1; background: radial-gradient(circle, #fff, {t['tint']}); border-radius: 0.18in; overflow: hidden; }}
.cu img {{ width: 100%; height: 100%; object-fit: cover; }}
.grid3 {{ display: grid; grid-template-columns: 1.1fr 1fr 1fr; gap: 0.32in; font: 400 10.5pt/1.42 Inter; }}
.grid3 h3 {{ font: 800 11pt Inter; letter-spacing: .06em; text-transform: uppercase; color: {t['accent']}; margin-bottom: 0.08in; }}
.grid3 li {{ list-style: none; padding-left: 0.2in; position: relative; margin-bottom: 0.05in; }}
.grid3 li::before {{ content: ""; position: absolute; left: 0; top: 0.07in; width: 0.09in; height: 0.09in; border-radius: 50%; background: {t['accent2']}; }}
.qrbox {{ display: flex; gap: 0.14in; align-items: center; margin-top: 0.12in; }}
.qrbox img {{ width: 1.05in; height: 1.05in; }}
.spec td {{ padding: 1px 0.12in 2px 0; vertical-align: top; }} .spec td:first-child {{ font-weight: 700; white-space: nowrap; }}
.dots i {{ display: inline-block; width: 0.11in; height: 0.11in; border-radius: 50%; border: 1.2px solid #3A2A1F; margin-right: 2px; }} .dots i.on {{ background: #3A2A1F; }}
.warn {{ border: 2px solid #3A2A1F; border-radius: 0.08in; padding: 0.08in 0.12in; font: 400 9.5pt/1.35 Inter; margin-top: 0.12in; }}
.warn b {{ font-weight: 800; }}
.legal {{ margin-top: auto; display: flex; justify-content: space-between; align-items: flex-end; font: 400 9.5pt/1.4 Inter; color: #5C4636; }}
.upc {{ width: 1.7in; height: 1.0in; border: 1.5px dashed #5C4636; display: grid; place-items: center; font: 700 9pt Inter; text-align: center; background: #fff; }}
.back {{ top: {y_back}in; height: {b['side']}in; background: #3A2A1F; color: #fff; transform: rotate(180deg); display: flex; align-items: center; justify-content: space-between; padding: 0 0.7in; }}
.back img {{ height: 0.85in; }}
.back span {{ font: 700 13pt Inter; letter-spacing: .04em; }}
.glue {{ top: {y_glue}in; height: {b['glue'] + BLEED}in; background: #fff; }}
</style></head><body><div class="page">
<div class="panel top">
  <img class="abs logo" src="../logo.svg" alt="Hartwood Designs">
  <div class="abs age">14+<small>AGES</small></div>
  <img class="abs hero" src="../../kits/{f['kit']}/renders/raw/three_quarter.webp" alt="">
  <div class="abs name">{f['name']}</div>
  <div class="abs tag">{f['tagline']}</div>
  <div class="abs feat"><b>It really works</b>{FEATURE[f['kit']]}</div>
  <div class="abs chips"><span>{f['pieces']} parts</span><span>No glue, no tools</span><span>{f['hours']}</span><span>3D instructions</span></div>
</div>
<div class="panel front"><img class="mk" src="../logo_mark.svg" alt=""><div class="nm">{f['name']}</div><div class="meta">{f['pieces']} PARTS<br>AGES 14+</div></div>
<div class="panel bottom">
  <div class="row1"><div><h2>Build {'an' if f['name'][0] in 'AEIOU' else 'a'} {f['name']}</h2><p class="story">{f['story']}</p></div>
    <div class="sheets">{sheets}<p>What's inside: {len(f['sheets'])} sheets that press out by hand</p></div></div>
  <div class="cus">{cl}</div>
  <div class="grid3">
    <div><h3>In the box</h3><p>{f['contents']}.</p></div>
    <div><h3>Easy to build</h3><ul><li>Every joint is a press fit. No glue.</li><li>Big picture steps, part codes on every sheet.</li>
      {'<li>Spare small parts on the sheets.</li>' if f['spares'] else ''}</ul>
      <div class="qrbox"><img src="{qr}" alt=""><span>Scan to build in 3D on your phone, step by step.</span></div></div>
    <div><h3>Details</h3><table class="spec"><tr><td>Parts</td><td>{f['pieces']}</td></tr><tr><td>Size</td><td>{f['size_cm']} cm<br>{f['size_in']} in</td></tr>
      <tr><td>Build time</td><td>{f['hours']}</td></tr><tr><td>Level</td><td class="dots">{dots}</td></tr><tr><td>Ages</td><td>14 and up</td></tr></table>
      <div class="warn"><b>WARNING:</b> Small parts. Not for children under 14. {WARN[f['kit']]}</div></div>
  </div>
  <div class="legal"><div>Hartwood Designs, TODO_LUCAS city, Minnesota, USA &nbsp;|&nbsp; {site_host()}<br>Designed and laser cut in Minnesota with imported materials.</div>
    <div class="upc">UPC barcode<br>TODO_LUCAS</div></div>
</div>
<div class="panel back"><img src="../logo_on_dark.svg" alt=""><span>{site_host()}</span></div>
<div class="panel glue"></div>
{guides(W, H, folds=(y_front, y_bottom, y_back, y_glue), proof=proof)}
</div></body></html>""", W, H, (y_front, y_bottom, y_back, y_glue)


def pick_sheets(f):
    """One natural sheet and two colored ones for the 'what's inside' fan."""
    nat = [s for s, c in zip(f['sheets'], f['colors']) if c == 'natural']
    col = [s for s, c in zip(f['sheets'], f['colors']) if c != 'natural']
    out = (col[:1] + nat[:1] + col[1:2]) if len(col) >= 2 else (nat[:2] + col[:1])
    return (out + f['sheets'])[:3]


def dieline(W, H, folds):
    w, h = BOX['w'], H - 2 * BLEED
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}in" height="{h}in" viewBox="0 0 {w * 72} {h * 72}">',
         f'<rect x="0" y="0" width="{w * 72}" height="{h * 72}" fill="none" stroke="#e0007a" stroke-width="1"/>']
    for y in folds:
        s.append(f'<line x1="0" y1="{(y - BLEED) * 72}" x2="{w * 72}" y2="{(y - BLEED) * 72}" stroke="#e0007a" stroke-width="1" stroke-dasharray="6 4"/>')
    labels = [('TOP of box (front of pack)', BOX['top'] / 2), ('front edge', BOX['top'] + BOX['side'] / 2),
              ('BOTTOM of box (back of pack)', BOX['top'] + BOX['side'] + BOX['top'] / 2), ('back edge (upside down)', 2 * BOX['top'] + 1.5 * BOX['side']),
              ('glue flap', 2 * BOX['top'] + 2 * BOX['side'] + BOX['glue'] / 2)]
    for t, y in labels:
        s.append(f'<text x="{w * 36}" y="{y * 72 + 4}" font-family="Arial" font-size="12" fill="#e0007a" text-anchor="middle">{t}</text>')
    s.append(f'<text x="6" y="14" font-family="Arial" font-size="9" fill="#e0007a">Sleeve dieline, trim size {w} x {h:.2f} in. Solid = cut, dashed = fold. '
             f'Panel sizes are Estimates for a 12 x 12 x 2 in mailer: measure a real box first.</text></svg>')
    open(os.path.join(OUT, 'sleeve_dieline.svg'), 'w').write('\n'.join(s))


def render(html_name, w, h, pdf, png, dpi):
    subprocess.run(['node', os.path.join(ROOT, 'tools', 'html2print.js'), os.path.join(OUT, html_name), f'{w}', f'{h}',
                    pdf or '-', png or '-', str(dpi)], check=True)


def mockups(facts):
    """Simple 3D views: the sleeved box, and the launch mailer with its lid label."""
    from PIL import Image
    tiles = {}
    for f in facts:
        k = f['kit']
        im = Image.open(os.path.join(OUT, f'_{k}_sleeve_full.png'))
        dpi = im.width / (BOX['w'] + 2 * BLEED)
        px = lambda v: int(round(v * dpi))
        top = im.crop((px(BLEED), px(BLEED), px(BLEED + BOX['w']), px(BLEED + BOX['top'])))
        front = im.crop((px(BLEED), px(BLEED + BOX['top']), px(BLEED + BOX['w']), px(BLEED + BOX['top'] + BOX['side'])))
        top.save(os.path.join(OUT, f'_{k}_top.png')); front.save(os.path.join(OUT, f'_{k}_front.png'))
        tiles[k] = (f'_{k}_top.png', f'_{k}_front.png')

    def box(k, sleeve=True):
        if sleeve:
            t, fr = tiles[k]
            top = f'<div class="face top" style="background-image:url({t})"></div>'
            front = f'<div class="face front" style="background-image:url({fr})"></div>'
        else:
            top = f'<div class="face top white"><img class="lbl" src="{k}_lid_label.png"></div>'
            front = '<div class="face front white"></div>'
        side = '<div class="face side"></div>'
        return f'<div class="scene"><div class="box">{top}{front}{side}</div></div>'

    css = """body{margin:0;background:linear-gradient(#f6eee1,#e9dcc6);font-family:Inter,Arial}
.row{display:flex;gap:30px;justify-content:center;align-items:flex-end;padding:40px 30px 60px}
.scene{width:360px;height:330px;perspective:1400px;position:relative}
.box{position:absolute;left:50%;top:40px;width:300px;height:300px;transform-style:preserve-3d;transform:translateX(-50%) rotateX(58deg) rotateZ(-28deg)}
.face{position:absolute;background-size:cover;background-position:center}
.top{width:300px;height:300px;transform:translateZ(50px);box-shadow:0 0 0 1px rgba(0,0,0,.06)}
.front{width:300px;height:50px;top:300px;transform-origin:top;transform:translateZ(50px) rotateX(-90deg);filter:brightness(.92)}
.side{width:50px;height:300px;left:300px;transform-origin:left;transform:translateZ(50px) rotateY(90deg);background:#e8e4dc}
.white{background:#fbfbf9}.front.white{background:#ecebe6}
.lbl{position:absolute;left:100px;top:100px;width:100px;height:100px;box-shadow:0 1px 2px rgba(0,0,0,.2)}
.shadow{position:absolute;left:40px;right:40px;bottom:-10px;height:40px;background:radial-gradient(rgba(58,42,31,.28),transparent 70%)}
h1{font:700 28px Georgia;color:#3A2A1F;text-align:center;margin:28px 0 0}"""
    for f in facts:
        k = f['kit']
        open(os.path.join(OUT, '_mock.html'), 'w').write(
            f'<html><head><style>{css}</style></head><body><div class="row">{box(k, True)}{box(k, False)}</div></body></html>')
        render('_mock.html', 8.6, 4.6, None, os.path.join(OUT, f'mockup_{k}.png'), 150)
    open(os.path.join(OUT, '_mock.html'), 'w').write(
        f'<html><head><style>{css}</style></head><body><div class="row">{"".join(box(f["kit"], True) for f in facts)}</div></body></html>')
    render('_mock.html', 12.5, 4.6, None, os.path.join(OUT, 'mockup_lineup.png'), 120)


def main():
    os.makedirs(OUT, exist_ok=True)
    facts = [kit_facts(k) for k in KITS]
    for f in facts:
        k = f['kit']
        for proof in (False, True):
            sfx = '_proof' if proof else ''
            open(os.path.join(OUT, f'_{k}_lid{sfx}.html'), 'w').write(lid_label(f, proof))
            open(os.path.join(OUT, f'_{k}_info{sfx}.html'), 'w').write(info_label(f, proof))
            html, W, H, folds = sleeve(f, proof)
            open(os.path.join(OUT, f'_{k}_sleeve{sfx}.html'), 'w').write(html)
        L = 4 + 2 * BLEED
        render(f'_{k}_lid.html', L, L, os.path.join(OUT, f'{k}_lid_label.pdf'), os.path.join(OUT, f'{k}_lid_label.png'), 300)
        render(f'_{k}_lid_proof.html', L, L, None, os.path.join(OUT, f'{k}_lid_label_proof.png'), 150)
        render(f'_{k}_info.html', L, 2 + 2 * BLEED, os.path.join(OUT, f'{k}_info_label.pdf'), None, 300)
        render(f'_{k}_info_proof.html', L, 2 + 2 * BLEED, None, os.path.join(OUT, f'{k}_info_label_proof.png'), 200)
        render(f'_{k}_sleeve.html', W, H, os.path.join(OUT, f'{k}_sleeve.pdf'), os.path.join(OUT, f'_{k}_sleeve_full.png'), 100)
        render(f'_{k}_sleeve_proof.html', W, H, None, os.path.join(OUT, f'{k}_sleeve_proof.png'), 40)
        print(k, 'packaging done')
    dieline(W, H, folds)
    mockups(facts)
    for f in os.listdir(OUT):
        if f.startswith('_'):
            os.remove(os.path.join(OUT, f))


if __name__ == '__main__':
    main()
