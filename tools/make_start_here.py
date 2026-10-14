"""START_HERE.html: one visual page that links to everything, with the TODO_LUCAS list at the top and a scoreboard.

    .venv/bin/python tools/make_start_here.py [--no-tests]

Runs the three test suites (engine check proofs, 3D app, planner) unless --no-tests, and reads every number
from the kit reports, steps JSON and supply data, so the page is always current.
"""
from __future__ import annotations

import csv
import html
import json
import os
import re
import socket
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
KITS = ['blaster', 'dragon', 'floral']
COLORS = {'natural': '#E9D3AE', 'orange': '#F28C3A', 'teal': '#4FA8A0', 'red': '#C8473A', 'gold': '#D9A93B', 'purple': '#9C7BC4',
          'green': '#6DAE6B', 'white': '#F7F5EF', 'pink': '#F2A7BD', 'yellow': '#F2D35E'}


def E(s):
    return html.escape(str(s), quote=True)


# ---------------------------------------------------------------- tests
def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close()
    return p


def run_tests():
    res = {}
    out = subprocess.run([os.path.join(ROOT, '.venv', 'bin', 'python'), 'tests/test_checks.py'], cwd=os.path.join(ROOT, 'engine'),
                         capture_output=True, text=True).stdout
    cases = [l for l in out.splitlines() if l.startswith(('Clean model', 'Wall', 'Top', 'Wheel', 'Hole', 'Floor', 'Small', 'Bridge'))]
    broken = [l for l in cases if not l.startswith('Clean model')]
    res['proofs'] = (sum(1 for l in broken if 'FAIL' in l), len(broken), any('Clean model' in l and 'FAIL' not in l for l in cases))
    out = subprocess.run(['node', 'tools/test_planner.js'], cwd=ROOT, capture_output=True, text=True).stdout
    m = re.search(r'(\d+) of (\d+) passed', out)
    res['planner'] = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    port = free_port()
    srv = subprocess.Popen(['node', 'tools/serve.js', str(port)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1.0)
        out = subprocess.run(['node', 'tools/test_app.js', f'http://localhost:{port}', os.path.join(ROOT, 'review', 'app')], cwd=ROOT,
                             capture_output=True, text=True, timeout=300).stdout
    finally:
        srv.terminate()
    res['app'] = (out.count('PASS  '), out.count('PASS  ') + out.count('FAIL  '))
    return res


# ---------------------------------------------------------------- markdown (just what TODO_LUCAS.md uses)
def inline(s):
    s = E(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'`(.+?)`', lambda m: '<code>' + m.group(1) + '</code>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    s = re.sub(r'(?<!["=>])(https?://[^\s<)]+)', r'<a href="\1">\1</a>', s)
    return s


def todo_sections():
    """[(title, html)] from TODO_LUCAS.md, one per ## section."""
    text = open(os.path.join(ROOT, 'TODO_LUCAS.md')).read()
    intro, *parts = re.split(r'^## ', text, flags=re.M)
    lead = ' '.join(l for l in intro.splitlines()[1:] if l.strip())
    out = []
    for p in parts:
        title, *lines = p.splitlines()
        h, in_list, in_table = [], None, False
        for ln in lines:
            m = re.match(r'^(\d+\.|-)\s+\[ \]\s+(.*)', ln)
            if m:
                if in_table:
                    h.append('</tbody></table></div>'); in_table = False
                tag = 'ol' if m.group(1)[0].isdigit() else 'ul'
                if in_list != tag:
                    if in_list:
                        h.append(f'</{in_list}>')
                    h.append(f'<{tag} class="todo">'); in_list = tag
                key = re.sub(r'\W+', '', m.group(2))[:60]
                h.append(f'<li><label><input type="checkbox" data-k="{E(key)}"><span>{inline(m.group(2))}</span></label></li>')
                continue
            if ln.startswith('|'):
                cells = [c.strip() for c in ln.strip('|').split('|')]
                if set(''.join(cells)) <= set('-: '):
                    continue
                if in_list:
                    h.append(f'</{in_list}>'); in_list = None
                if not in_table:
                    h.append('<div class="tw"><table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in cells) + '</tr></thead><tbody>')
                    in_table = True
                else:
                    h.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in cells) + '</tr>')
                continue
            if ln.strip():
                if in_list:
                    h.append(f'</{in_list}>'); in_list = None
                if in_table:
                    h.append('</tbody></table></div>'); in_table = False
                h.append(f'<p>{inline(ln)}</p>')
        if in_list:
            h.append(f'</{in_list}>')
        if in_table:
            h.append('</tbody></table></div>')
        out.append((title.strip(), '\n'.join(h)))
    return lead, out


# ---------------------------------------------------------------- data
def kit_rows():
    econ = list(csv.DictReader(open(os.path.join(ROOT, 'supply', 'unit_economics.csv'))))
    rows = []
    for k in KITS:
        rep = json.load(open(os.path.join(ROOT, 'kits', k, f'{k}_report.json')))
        st = json.load(open(os.path.join(ROOT, 'kits', k, f'{k}_steps.json')))
        prp = os.path.join(ROOT, 'kits', k, 'print_mode', f'{k}_report.json')
        pr = json.load(open(prp)) if os.path.exists(prp) else None
        pages = subprocess.run(['pdfinfo', os.path.join(ROOT, 'kits', k, 'booklet', f'{k}_instructions.pdf')], capture_output=True, text=True).stdout
        pages = int(re.search(r'Pages:\s+(\d+)', pages).group(1)) if 'Pages' in pages else 0
        checks = [(c['name'].replace(' check', ''), c['pass']) for c in rep['checks']]
        if not any(n.startswith('Pop-out') for n, _ in checks):
            checks.append(('Pop-out', rep['popout']['pass']))

        def prof(mode):
            r = next((r for r in econ if r['kit'] == st['name'] and r['color method'] == mode and r['channel'].startswith('own site')
                      and abs(float(r['price']) - st['price']) < 0.01), None)
            return (float(r['materials + packaging']), float(r['profit after labor']), r['margin after labor']) if r else None
        rows.append({'kit': k, 'name': st['name'], 'tagline': st['tagline'], 'price': st['price'], 'pieces': st['piece_count'],
                     'steps': len(st['steps']), 'difficulty': st['difficulty'], 'hours': st['build_hours'],
                     'sheets': [(s['sheet'], s['color'], s['tile']) for s in rep['sheets']], 'sheet_eq': rep['sheet_equivalents'],
                     'laser': rep['cut_minutes_per_kit'], 'wood': rep['wood_cost_usd'], 'checks': checks,
                     'popout': rep['popout']['summary'], 'pages': pages, 'sheets_mode': prof('pre-colored sheets'),
                     'print_mode': prof('UV-printed color'), 'print_wood': pr['wood_cost_usd'] if pr else None,
                     'print_min': pr['print']['print_minutes'] if pr else None})
    return rows


def count_sources():
    t = open(os.path.join(ROOT, 'research', 'sources.md')).read()
    m = re.search(r'Total distinct source URLs: (\d+)', t)
    return int(m.group(1)) if m else 0


def count_decisions():
    return len(re.findall(r'^- D\d{3}', open(os.path.join(ROOT, 'DECISIONS.md')).read(), flags=re.M))


# ---------------------------------------------------------------- page
CSS = """
:root { --walnut:#3A2A1F; --walnut-2:#5C4636; --oak:#B9895B; --maple:#EBD5B0; --birch:#F6EEE1; --paper:#FCF8F1; --line:#E6D9C4;
  --lagoon:#0F8B7F; --lagoon-dark:#0B6158; --lagoon-light:#D7EFEB; --blaze:#FF6A13; --ok:#1d7a3a; --ok-bg:#e3f3e7; --bad:#b3261e; --white:#fff; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--walnut); font: 16px/1.5 Inter, system-ui, -apple-system, 'Segoe UI', sans-serif; }
a { color: var(--lagoon-dark); }
.wrap { max-width: 1180px; margin: 0 auto; padding: 0 16px; }
header.hero { background: var(--walnut); color: #fff; padding: 22px 0 26px; }
header.hero .wrap { display: flex; flex-wrap: wrap; gap: 14px 28px; align-items: center; justify-content: space-between; }
header.hero img { height: 54px; }
header.hero h1 { font: 700 clamp(1.6rem, 3.5vw, 2.3rem)/1.15 Fraunces, Georgia, serif; margin: 6px 0 4px; }
header.hero p { margin: 0; color: #f1e6d6; max-width: 720px; }
h2 { font: 700 1.55rem/1.2 Fraunces, Georgia, serif; margin: 34px 0 12px; }
h3 { margin: 0 0 6px; font-size: 1.05rem; }
.lead { color: var(--walnut-2); margin-top: -4px; }
.todo-first { background: #fff; border: 2px solid var(--blaze); border-radius: 18px; padding: 16px 18px; margin-top: 18px; }
.todo-first h2 { margin-top: 0; }
ol.todo, ul.todo { list-style: none; padding: 0; margin: 6px 0 10px; counter-reset: n; }
ol.todo li { counter-increment: n; }
.todo li label { display: grid; grid-template-columns: 26px 1fr; gap: 8px; padding: 7px 0; border-top: 1px dashed var(--line); cursor: pointer; align-items: start; }
ol.todo li label::before { content: counter(n); grid-column: 1; grid-row: 1; width: 24px; height: 24px; border-radius: 50%; background: var(--blaze); color: #fff;
  font-weight: 800; font-size: .85rem; display: grid; place-items: center; }
ol.todo li input { position: absolute; opacity: 0; }
ul.todo li input { width: 20px; height: 20px; margin: 2px 0 0; accent-color: var(--lagoon); }
.todo li input:checked + span { text-decoration: line-through; color: #8c8579; }
ol.todo li input:checked ~ span::after { content: "  (done)"; color: var(--ok); font-weight: 700; text-decoration: none; }
.secs { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 500px), 1fr)); gap: 10px; align-items: start; }
details.sec { background: var(--paper); border: 1px solid var(--line); border-radius: 14px; padding: 2px 14px 8px; font-size: .93rem; }
details.sec .tw { font-size: .86rem; }
details.sec summary { cursor: pointer; font-weight: 800; padding: 10px 0; min-height: 44px; display: flex; align-items: center; justify-content: space-between; }
details.sec summary span { font-weight: 600; color: var(--walnut-2); font-size: .9rem; }
.tw { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: .93rem; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { background: var(--birch); font-size: .78rem; text-transform: uppercase; letter-spacing: .04em; color: var(--walnut-2); }
code { background: var(--birch); padding: 1px 5px; border-radius: 5px; font-size: .88em; overflow-wrap: anywhere; }
.tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 10px; }
.tile { background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 12px 14px; }
.tile b { display: block; font: 800 1.6rem/1.1 Inter; color: var(--walnut); }
.tile span { font-size: .85rem; color: var(--walnut-2); }
.tile.good b { color: var(--ok); }
.score { background: #fff; border: 1px solid var(--line); border-radius: 16px; overflow: hidden; }
.score td { vertical-align: middle; }
.score img { width: 110px; height: 82px; object-fit: cover; border-radius: 10px; display: block; background: var(--birch); }
.kname { font: 700 1.15rem Fraunces, Georgia, serif; }
.muted { color: var(--walnut-2); font-size: .85rem; font-weight: 400; }
.kc { min-width: 170px; }
.chips { display: flex; flex-wrap: wrap; gap: 3px; max-width: 150px; }
.chip { width: 18px; height: 18px; border-radius: 4px; border: 1px solid rgba(58,42,31,.35); font-size: .6rem; display: grid; place-items: center; font-weight: 700; }
.chip.half { width: 13px; } .chip.quarter { width: 9px; }
.pass { display: inline-block; background: var(--ok-bg); color: var(--ok); border-radius: 999px; padding: 2px 9px; font-weight: 700; font-size: .85rem; white-space: nowrap; }
.fail { background: #fde7e5; color: var(--bad); }
.num { font-weight: 800; white-space: nowrap; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
.card { background: #fff; border: 1px solid var(--line); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; }
.card .pic { aspect-ratio: 16 / 10; background: var(--birch); overflow: hidden; }
.card .pic img { width: 100%; height: 100%; object-fit: cover; object-position: top; display: block; }
.card .body { padding: 12px 14px 14px; display: flex; flex-direction: column; gap: 6px; flex: 1; }
.card ul { margin: 0; padding-left: 18px; font-size: .93rem; }
.card li { margin: 3px 0; }
.note { background: var(--lagoon-light); border-radius: 12px; padding: 10px 14px; font-size: .93rem; }
footer { margin: 40px 0 0; padding: 20px 0 30px; color: var(--walnut-2); font-size: .85rem; border-top: 1px solid var(--line); }
@media (max-width: 760px) { .score .hide-sm { display: none; } .score img { width: 72px; height: 56px; } }
"""


def scoreboard(rows):
    h = ['<div class="score tw"><table><thead><tr><th>Kit</th><th></th><th>Pieces</th><th>Sheets</th><th class="hide-sm">Laser min per kit</th>'
         '<th>Cost per kit</th><th>Price</th><th>Profit per kit, own site</th><th>Checks</th></tr></thead><tbody>']
    for r in rows:
        chips = ''.join(f'<span class="chip {t}" title="Sheet {s}: {c}, {t}" style="background:{COLORS.get(c, "#ccc")}">{s}</span>' for s, c, t in r['sheets'])
        npass = sum(1 for _, p in r['checks'] if p)
        sm, pm = r['sheets_mode'], r['print_mode']
        h.append(f"""<tr><td><a href="kits/{r['kit']}/README.md"><img src="kits/{r['kit']}/renders/three_quarter.jpg" alt="{E(r['name'])}"></a></td>
<td class="kc"><div class="kname">{E(r['name'])}</div><div class="muted">{r['steps']} steps, {r['pages']}-page booklet, {E(r['hours'])}</div></td>
<td class="num">{r['pieces']}</td>
<td><div class="chips">{chips}</div><div class="muted">{len(r['sheets'])} sheets ({r['sheet_eq']:.1f} full)</div></td>
<td class="num hide-sm">{r['laser']:.1f}<div class="muted">UV: +{r['print_min']:.0f} min printing</div></td>
<td class="num">${sm[0]:.2f}<div class="muted">wood ${r['wood']:.2f}</div><div class="muted">UV: ${pm[0]:.2f}</div></td>
<td class="num">${r['price']:.2f}</td>
<td class="num">${sm[1]:.2f} ({sm[2]})<div class="muted">UV: ${pm[1]:.2f} ({pm[2]})</div></td>
<td><span class="pass{'' if npass == len(r['checks']) else ' fail'}">{npass} of {len(r['checks'])}</span>
<div class="muted">{', '.join(n for n, _ in r['checks'])}</div></td></tr>""")
    h.append('</tbody></table></div>')
    h.append('<p class="muted">Profit after free shipping, Shopify fees and your labor at $20/h. Cost and profit are Estimates built from Verified prices '
             '(see <a href="supply/README.md">supply/README.md</a>). Laser minutes are Estimates from planning speeds until you cut the speed ladder. '
             'UV = the UV-printed color version. Hover a sheet chip for its color; narrow chips are half and quarter tiles that serve 2 or 4 kits.</p>')
    return '\n'.join(h)


def card(title, img, links, text=''):
    pic = f'<div class="pic"><img src="{img}" alt=""></div>' if img else ''
    lis = ''.join(f'<li><a href="{u}">{E(t)}</a>{(" " + E(n)) if n else ""}</li>' for t, u, n in links)
    return f'<div class="card">{pic}<div class="body"><h3>{E(title)}</h3>{f"<p class=muted>{text}</p>" if text else ""}<ul>{lis}</ul></div></div>'


def main(tests=True):
    rows = kit_rows()
    t = run_tests() if tests else None
    lead, secs = todo_sections()
    sup = json.load(open(os.path.join(ROOT, 'supply', 'supply_data.json')))['startup_totals']
    total_pieces = sum(r['pieces'] for r in rows)
    checks_ok = sum(sum(1 for _, p in r['checks'] if p) for r in rows)
    checks_all = sum(len(r['checks']) for r in rows)
    tiles = [(f'{len(rows)} kits', f'{total_pieces} pieces in all', False),
             (f'{checks_ok} of {checks_all}', f'design checks pass ({checks_all // len(rows)} per kit)', checks_ok == checks_all)]
    if t:
        tiles += [(f"{t['proofs'][0]} of {t['proofs'][1]}", 'deliberate breaks caught by the checks', t['proofs'][0] == t['proofs'][1]),
                  (f"{t['app'][0]} of {t['app'][1]}", '3D app tests pass', t['app'][0] == t['app'][1]),
                  (f"{t['planner'][0]} of {t['planner'][1]}", 'planner tests pass', t['planner'][0] == t['planner'][1])]
    tiles += [(f'{count_sources()}', 'sources in research/sources.md', False), (f'{count_decisions()}', 'decisions in DECISIONS.md', False),
              ('$3,699.99', 'OMTech Polar 2 70W laser (Verified)', False), (f"${sup['required']:,.0f}", 'startup budget, required (mixed)', False),
              ('99 a week', 'kits on one shift; launch plan is 17 (Estimate)', False)]
    tiles_h = ''.join(f'<div class="tile{" good" if g else ""}"><b>{E(a)}</b><span>{E(b)}</span></div>' for a, b, g in tiles)

    first = secs[0]
    rest = ''.join(f'<details class="sec" open><summary>{inline(ti)} <span>{h.count("<li>") + max(0, h.count("<tr>") - 1)} items</span></summary>{h}</details>'
                   for ti, h in secs[1:])

    kit_cards = ''.join(card(r['name'], f"kits/{r['kit']}/renders/front.jpg", [
        ('Kit README (story, sheets, parts)', f"kits/{r['kit']}/README.md", ''),
        ('Hero renders and close-ups', f"kits/{r['kit']}/renders/", ''),
        ('Part images, one per code', f"kits/{r['kit']}/parts/", ''),
        ('Cut files (SVG, DXF, LightBurn)', f"kits/{r['kit']}/cutfiles/", ''),
        ('Booklet PDF', f"kits/{r['kit']}/booklet/{r['kit']}_instructions.pdf", f"({r['pages']} pages)"),
        ('Booklet Word', f"kits/{r['kit']}/booklet/{r['kit']}_instructions.docx", ''),
        ('Parts maps', f"kits/{r['kit']}/parts_map/", ''), ('Bridge maps (pop-out)', f"kits/{r['kit']}/popout/", ''),
        ('UV-print version', f"kits/{r['kit']}/print_mode/", ''), ('3D model (GLB)', f"kits/{r['kit']}/{r['kit']}.glb", '')]
        + ([('Mechanism test plan', 'kits/blaster/mechanism_test_plan.md', '')] if r['kit'] == 'blaster' else [])) for r in rows)

    cards = ''.join([
        card('Blaster test: order and cut', 'guides/img/blaster_job1_bed.png', [
            ('What to order, with direct links', 'guides/BLASTER_TEST.md', '(about $165 for 3 kits)'),
            ('How to cut on the laser (LightBurn)', 'guides/HOW_TO_CUT.md', ''),
            ('Private preview of the site and apps', 'https://claude.ai/artifact/Us7byCEqYgrpMZUNkgTNFP', '(only you can open it)')],
            'Cut the coupon, then 3 Star Slingers. The ship lifts off its stand.'),
        card('Research dashboard', 'review/research_dashboard_desktop.png', [
            ('Open the dashboard', 'research/dashboard/index.html', ''), ('ROKR deep dive', 'research/rokr_deep_dive.md', ''),
            ('Design language', 'research/design_language.md', ''), ('Review mining', 'research/review_mining.md', ''),
            ('Competitors', 'research/competitors.md', ''), ('Laser comparison', 'research/lasers.md', ''),
            ('Materials', 'research/materials.md', ''), ('Color printing', 'research/color_printing.md', ''),
            ('All sources', 'research/sources.md', '')]),
        card('Concepts (3 per kit, scored)', 'review/concepts/dragon_concepts.png', [
            ('Scores and reasons', 'review/concepts/CONCEPTS.md', ''), ('Concept boards', 'review/concepts/', '')]),
        card('3D instruction app', 'review/app/phone_step4.png', [
            ('Start the local server: node tools/serve.js', 'tools/serve.js', ''), ('Then open localhost:8080/build/', 'http://localhost:8080/build/', ''),
            ('App code', 'website/build/', ''), ('App screenshots', 'review/app/', '')],
            'Routes like /build/dragon/step/7, saved progress, works offline. It needs a web server, so run the local one first.'),
        card('Website', 'review/site/home_desktop.png', [
            ('Open localhost:8080 (after node tools/serve.js)', 'http://localhost:8080/', ''), ('Site files', 'website/', ''),
            ('Screenshots, desktop and phone', 'review/site/', ''), ('Checkout placeholder', 'website/checkout/index.html', '')]),
        card('Brand and packaging', 'brand/packaging/mockup_lineup.png', [
            ('Logo (SVG)', 'brand/logo.svg', ''), ('Colors and fonts', 'brand/brand.json', ''), ('Packaging and labels', 'brand/packaging/README.md', ''),
            ('Lid labels (print PDFs)', 'brand/packaging/', '')]),
        card('Production planner (tablet)', 'review/production/planner_quality.png', [
            ('Open the planner', 'production/planner/index.html', ''), ('How to use it', 'production/README.md', ''),
            ('Sample orders CSV', 'production/planner/sample_orders.csv', '')]),
        card('Visual SOPs', 'review/production/sops/SOP-3_p1.png', [
            ('All seven SOPs', 'production/sops/index.html', ''), ('SOP-1 Start-up', 'production/sops/SOP-1_startup_shutdown.pdf', ''),
            ('SOP-2 Load and cut', 'production/sops/SOP-2_load_and_cut.pdf', ''), ('SOP-3 Pop-out check', 'production/sops/SOP-3_unload_and_popout.pdf', ''),
            ('SOP-4 Kitting', 'production/sops/SOP-4_kitting_and_packing.pdf', ''), ('SOP-5 Maintenance', 'production/sops/SOP-5_weekly_maintenance.pdf', ''),
            ('SOP-6 Fire', 'production/sops/SOP-6_fire_and_emergency.pdf', ''), ('SOP-7 Shipping', 'production/sops/SOP-7_shipping.pdf', '')]),
        card('Capacity, layout, quality', 'production/capacity_bottleneck.png', [
            ('Capacity model', 'production/capacity.md', ''), ('Workshop layout', 'production/layout/workshop_layout.png', ''),
            ('Quality loop', 'production/quality_loop.md', ''), ('Starting Pareto', 'production/quality/pareto_start.png', '')]),
        card('Supply and money', 'supply/unit_economics_prices.png', [
            ('Supply overview', 'supply/README.md', ''), ('BOM per kit', 'supply/bom_per_kit.csv', ''), ('BOM for 25 and 100', 'supply/bom_batches.csv', ''),
            ('Suppliers (2+ per item)', 'supply/suppliers.csv', ''), ('Startup shopping list', 'supply/startup_shopping_list.csv', ''),
            ('Reorder points', 'supply/reorder_points.csv', ''), ('Unit economics', 'supply/unit_economics.csv', ''),
            ('Legal checklist', 'supply/legal_checklist.md', '')]),
        card('Kit engine', 'review/coupon_svg.png', [
            ('Engine code', 'engine/', ''), ('Config (kerf, fits, speeds)', 'engine/hartwood/config.py', ''),
            ('Fit-test coupon', 'kits/coupon/', ''), ('Proof that every check works', 'review/check_proofs.md', ''),
            ('Rebuild everything: bash tools/rebuild_all.sh', 'tools/rebuild_all.sh', '')]),
        card('Records', '', [
            ('SUMMARY.md: what is built, verified, guessed', 'SUMMARY.md', ''), ('DECISIONS.md', 'DECISIONS.md', ''),
            ('TODO_LUCAS.md', 'TODO_LUCAS.md', ''), ('Review images', 'review/', '')]),
    ])

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hartwood Designs: start here</title>
<link rel="icon" href="website/favicon.svg" type="image/svg+xml">
<style>
@font-face {{ font-family: Fraunces; src: url(brand/fonts/Fraunces-700.ttf); font-weight: 700; }}
@font-face {{ font-family: Inter; src: url(brand/fonts/Inter-400.ttf); font-weight: 400; }}
@font-face {{ font-family: Inter; src: url(brand/fonts/Inter-600.ttf); font-weight: 600; }}
@font-face {{ font-family: Inter; src: url(brand/fonts/Inter-700.ttf); font-weight: 700; }}
@font-face {{ font-family: Inter; src: url(brand/fonts/Inter-800.ttf); font-weight: 800; }}
{CSS}</style></head>
<body>
<header class="hero"><div class="wrap">
  <div><img src="brand/logo_on_dark.svg" alt="Hartwood Designs"><h1>Start here</h1>
  <p>Three wooden model kits, designed in code and cut on one desktop laser, plus the instructions, website, workshop system and supply plan. Open anything below.</p></div>
</div></header>
<main class="wrap">
<section class="todo-first">
  <h2>Your to-do list</h2>
  <p class="lead">{inline(lead)} Tick items as you go: the ticks are saved in this browser.</p>
  <h3>{inline(first[0])}</h3>{first[1]}
  <p class="muted"><a href="#scoreboard">Jump to the scoreboard</a> or <a href="#kits">the kits</a>.</p>
  <div class="secs">{rest}</div>
</section>

<h2 id="scoreboard">Scoreboard</h2>
<div class="tiles">{tiles_h}</div>
<p></p>
{scoreboard(rows)}

<h2 id="kits">The kits</h2>
<div class="cards">{kit_cards}</div>

<h2>Everything else</h2>
<div class="note">The website and the 3D app use web routes, so they need a small server: in this folder run <code>node tools/serve.js</code> and open
<a href="http://localhost:8080/">localhost:8080</a>. Everything else opens straight from this page.</div>
<p></p>
<div class="cards">{cards}</div>
</main>
<footer><div class="wrap">Made by <code>tools/make_start_here.py</code> from the kit reports, the supply data and the test results on {time.strftime('%Y-%m-%d')}.
Every number is Verified (source in research/sources.md) or an Estimate.</div></footer>
<script>
document.querySelectorAll('input[data-k]').forEach(cb => {{
  const k = 'hw-start-' + cb.dataset.k;
  try {{ cb.checked = localStorage.getItem(k) === '1'; }} catch (e) {{}}
  cb.addEventListener('change', () => {{ try {{ localStorage.setItem(k, cb.checked ? '1' : '0'); }} catch (e) {{}} }});
}});
</script>
</body></html>"""
    open(os.path.join(ROOT, 'START_HERE.html'), 'w').write(page)
    print('START_HERE.html written', t)


if __name__ == '__main__':
    main(tests='--no-tests' not in sys.argv)
