"""Six visual SOPs for the workshop: HTML (tablet) and PDF (print, hang at the station).

    .venv/bin/python tools/make_sops.py        ->  production/sops/SOP-<n>_<name>.html + .pdf, index.html
                                                   review/production/sops/*.png (page images to check)

Pictures come from tools/sop_art.py (drawn) and from the engine outputs (bridge map, print preview,
tiled sheet, fit coupon). Times and settings are Estimates until measured on the real machine.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'engine'))
import sop_art as A  # noqa: E402
import make_supply as MS  # noqa: E402
from hartwood import config as C  # noqa: E402

OUT = os.path.join(ROOT, 'production', 'sops')
IMG = os.path.join(OUT, 'img')
REVIEW = os.path.join(ROOT, 'review', 'production', 'sops')
REV, DATE = 'Rev A', '2026-10-12'
KITS = ['blaster', 'dragon', 'floral']


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def md(s):
    """Tiny markup: **bold** and `code`."""
    import re
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    return re.sub(r'`(.+?)`', r'<code>\1</code>', s)


# ------------------------------------------------------------------ real images
def prepare_images():
    os.makedirs(IMG, exist_ok=True)
    shutil.copy(os.path.join(ROOT, 'kits', 'blaster', 'popout', 'sheet_A.png'), os.path.join(IMG, 'bridge_map_blaster_A.png'))
    shutil.copy(os.path.join(ROOT, 'kits', 'blaster', 'print_mode', 'cutfiles', 'blaster_sheet_A_natural_print_preview.png'),
                os.path.join(IMG, 'print_preview_blaster_A.png'))
    tiled = os.path.join(IMG, 'tiled_dragon_H_x4.png')
    src = os.path.join(ROOT, 'kits', 'dragon', 'cutfiles', 'dragon_sheet_H_green_x4_full.svg')
    svg = open(src).read().replace('<svg ', '<svg style="background:#bfe0c6" ', 1).replace('stroke-width="0.1"', 'stroke-width="0.9"')
    tmp = os.path.join(IMG, '_tmp.svg')
    open(tmp, 'w').write(svg)
    subprocess.run(['node', os.path.join(ROOT, 'tools', 'svg2png.js'), tmp, tiled, '900', '900'], check=True)
    os.remove(tmp)


def photo(name, zoom=1.0, x=50, y=50, alt=''):
    """Real image cropped into the 240 x 140 picture box. x, y = focus point in % of the image."""
    if zoom <= 1.0:
        return f'<div class="pic photo"><img src="img/{name}" alt="{esc(alt)}" style="object-fit:contain;width:100%;height:100%"></div>'
    return (f'<div class="pic photo"><img src="img/{name}" alt="{esc(alt)}" '
            f'style="position:absolute;width:{zoom * 100:.0f}%;left:{50 - x * zoom:.1f}%;top:50%;'
            f'transform:translateY(-{y:.0f}%)"></div>')


# ------------------------------------------------------------------ kit facts for the cards
def kit_facts():
    out = {}
    for k in KITS:
        rep = json.load(open(os.path.join(ROOT, 'kits', k, f'{k}_report.json')))
        steps = json.load(open(os.path.join(ROOT, 'kits', k, f'{k}_steps.json')))
        _, _, rows = MS.kit_bom(k)
        extras = [(q, n) for i, q, n in rows if i not in ('sheet_natural', 'sheet_color', 'box', 'booklet', 'sticker', 'filler', 'bag', 'dowel')]
        rods = [h['note'].split(', ')[-1].split(';')[0] for h in rep['hardware'] if h['kind'] == 'rod' and 'dowel' in h['note'] and ' mm' in h['note']]
        if not rods:
            rods = [f"{q / 1.1:.0f} mm total" for i, q, n in rows if i == 'dowel']
        sheets = ', '.join(f"{s['sheet']} {s['color']}{'' if s['tile'] == 'full' else ' ' + s['tile']}" for s in rep['sheets'])
        out[k] = {'name': steps['name'], 'sheets': sheets, 'n': len(rep['sheets']), 'extras': extras, 'rods': rods,
                  'jobs': [j['job'] for j in rep['jobs']]}
    return out


# ------------------------------------------------------------------ content
def sops(F):
    extras_rows = ''.join(
        f"<tr><td><b>{esc(F[k]['name'])}</b></td><td>{esc(F[k]['sheets'])}</td>"
        f"<td>{esc('; '.join(f'{q:g} x {n}' for q, n in F[k]['extras']))}"
        f"{esc('; dowels (3/16 in): ' + ', '.join(F[k]['rods']))}</td></tr>" for k in KITS)
    return [
        dict(n=1, slug='startup_shutdown', title='Start-up and shut-down', color='lagoon',
             when='Every day you cut', time='10 min to start, 10 min to close (Estimate)', who='Whoever runs the laser that day',
             need=['Room thermometer', 'Lens tissue and lens cleaner', 'Brush and bin', 'Planner tablet'],
             blocks=[
                 ('section', 'Start of the day'),
                 ('steps', [
                     (A.warm_room(), 'Check the room temperature.', 'The water loop must stay above 10 °C (50 °F). Cold, damp wood also fits differently.', 'Below 10 °C: do not start. Warm the room first.'),
                     (A.clear_area(), 'Clear around the laser.', 'Nothing on the lid. No paper, offcuts or rags next to the machine.', 'CO2 extinguisher and fire blanket within reach.'),
                     (A.exhaust_on(), 'Open the vent. Switch on the exhaust.', 'Run it before, during and after every job.', 'A tissue held at the intake gets pulled in.'),
                     (A.water_ok(), 'Look at the cooling water.', 'Clear, between MIN and MAX, no bubbles in the tube.', 'Low or cloudy: top up with distilled water (SOP-5).'),
                     (A.power_on(), 'Turn on the laser.', 'Wait until the head moves home and stops.', 'No error on the control panel.'),
                     (A.lightburn_ready(), 'Open LightBurn and connect.', 'Use the saved device profile. Do not change layer settings by hand.', 'Status shows Ready.'),
                     (A.lens_check(), 'Look at the lens.', 'A smoke film or dots on the lens make weak cuts. Wipe with lens tissue and cleaner.', 'Clean, no cracks, no pits.'),
                     ('box', 'stop', 'Stop and fix first if', ['Smoke smell in the room while a job runs: the exhaust is not pulling.',
                                                              'The water is warm, low, or has bubbles in the tube.',
                                                              'The control panel shows an error, or the head does not home.']),
                 ]),
                 ('section', 'End of the day'),
                 ('steps', [
                     (A.wait_smoke(), 'Let the smoke clear.', 'Leave the exhaust on for 5 minutes after the last job.', 'No smoke smell when you lift the lid.'),
                     (A.tray_clean(), 'Empty the crumb tray. Sweep the bed.', 'Small scraps are fuel for a fire.', 'Tray empty, bed clear, bin emptied outside.'),
                     (A.power_off(), 'Switch off: laser first, then exhaust.', 'Close the window vent.', 'Winter: the room stays above 10 °C overnight, or drain the water loop.'),
                     (A.log_planner(), 'Log the day in the planner.', 'Mark the batches you cut. Log any problem on the Quality tab.', 'Every batch cut today shows Cut.'),
                 ]),
             ]),
        dict(n=2, slug='load_and_cut', title='Load and cut a job', color='lagoon',
             when='Every laser job (two 12 x 12 sheets)', time='2 to 3 min hands-on, then 15 to 25 min of attended cutting (Estimate)', who='Laser operator',
             need=['Planner tablet', 'Sheets for the job', 'Straight ruler', 'Honeycomb pins'],
             blocks=[
                 ('steps', [
                     (A.svg(A.tablet(64, 28, 112, 84, 6, 'Cut queue')), 'Pick the next job in the planner.', 'Cut queue lists the job file and the sheet colors. Oldest orders first.', 'Example job: dragon_job3_E-F_x4.'),
                     (A.flat_check(), 'Check each sheet.', 'Lay it on the bench under a straight ruler. Color face up.', 'Bowed more than 1 mm (Estimate): use it for the coupon or scrap.'),
                     (A.lightburn_ready(), 'Open the job file.', '`<job>_bed.lbrn2` in the kit\'s `cutfiles` folder. The order is set: engrave, score, holes, outlines.', 'Speeds match the label on the machine.'),
                     (A.two_sheets(), 'Load two sheets.', 'First sheet letter on the left, in the corner stop. Second sheet beside it, 5 mm gap.', 'Flat on the bed. Pin a corner if it lifts.'),
                     (A.focus(), 'Set the focus.', 'Autofocus, or enter 3 mm material height.', 'The nozzle does not touch the wood.'),
                     (A.frame(), 'Frame the job.', 'Press Frame. The red dot traces the outline.', 'The outline stays on both sheets, with margin all round.'),
                     (A.start_job(), 'Close the lid and start.', 'Air assist and exhaust must be on.', 'Cut lines look thin and dark, not wide and black.'),
                     (A.watch_cut(), 'Stay and watch the whole job.', 'Never leave the room while the laser runs, not even for a minute.', 'A small flicker at the head is normal.'),
                     (A.flare_pause(), 'A flame stays after the head moves on? Press Pause.', 'Keep the lid shut. Most go out by themselves. If not: SOP-6.', 'Log it as a burn on the Quality tab.'),
                     (A.cool_wait(), 'When it ends, wait 30 seconds.', 'Let the exhaust clear the smoke before you open the lid.', 'Then unload with SOP-3.'),
                     (photo('print_preview_blaster_A.png', 1.0, alt='Printed sheet preview'), 'UV-printed color: print first.', 'Print the front, white and back files from the kit\'s `print_mode` folder.', 'The print shows the 2 corner targets.'),
                     (A.print_and_cut(), 'UV-printed color: Print and Cut.', 'In LightBurn, jog the red dot to target 1 and set it, then target 2, then align.', 'The cut lands on the print edge. The 0.6 mm bleed hides small errors.'),
                 ]),
                 ('box', 'info', 'Planning settings (Estimate until you cut the coupon, SOP-5)', [
                     'Cut: 30 mm/s at 65% power. Score: 300 mm/s at 18%. Engrave: 400 mm/s at 20%, 0.1 mm line interval.',
                     'After the coupon, write your own numbers on a label on the machine: cut ____ mm/s ____%   kerf ____ mm.']),
             ]),
        dict(n=3, slug='unload_and_popout', title='Unload and pop-out check', color='lagoon',
             when='Every job, before the sheets leave the laser', time='2 to 4 min per job (Estimate)', who='Laser operator',
             need=['Bridge map for the sheet (`kits/<kit>/popout/`)', 'A lamp or window', 'Planner tablet'],
             blocks=[
                 ('steps', [
                     (A.press_corner(), 'Before you lift: test a corner part.', 'Press lightly on a small part near each corner. It should move a little.', 'Moves: go on. Stuck: next step.'),
                     (A.recut(), 'Stuck? Run the cut layer again.', 'Do not move the sheet. Turn off engrave and score. Run cut once.', 'Still stuck: weak power or dirty lens (SOP-5).'),
                     (A.light_check(), 'Lift the sheet flat. Hold it to the light.', 'Use both hands and do not bend it. Light should show along every cut line.', 'A dark spot in a line is an uncut spot. Log "uncut".'),
                     (photo('bridge_map_blaster_A.png', 2.2, 22, 30, 'Bridge map'), 'Compare with the bridge map.', 'Green dots show the bridges. Each part hangs by 1 to 4 bridges, 0.5 mm wide.', 'Blue edges slide into other parts: never a bridge there.'),
                     (A.push_section(), 'Pop test: first sheet of each batch.', 'Press from the back, right next to a bridge. One thumb should pop the part.', 'Put the test parts in the kit\'s small-parts bag.'),
                     (A.bridge_fail(), 'Falls out alone, or tears when pushed?', 'Falls out: the kerf is too wide, lower cut power 5%. Tears or needs force: clean the lens, check focus.', 'Recut the coupon bridges (SOP-5). Log "bridge".'),
                     (photo('tiled_dragon_H_x4.png', 1.0, alt='Quarter tiles on one sheet'), 'Half and quarter sheets: snap the tiles.', 'Bend gently along the long separation cut. Each tile goes to a different kit.', 'Clean edge, no part broken off at the line.'),
                     (A.burn_marks(), 'Check the show faces.', 'A light smoke stain sands off. A dark scorch on a visible part means remake the sheet.', 'Log "burn" if you remake it.'),
                     (A.stack_label(), 'Stack flat by kit, with a label.', 'Label: kit, batch, date. Then mark the batch Cut in the planner.', 'Sheet letters match the job name.'),
                 ]),
                 ('box', 'stop', 'Stop the batch and fix first if', [
                     'Two or more uncut spots on one sheet, or parts falling out on two sheets in a row.',
                     'A crack runs through a part (bad sheet: set the stack of that lot aside).']),
             ]),
        dict(n=4, slug='kitting_and_packing', title='Kitting and packing', color='lagoon',
             when='Every kit', time='About 6 min per kit (Estimate, the same as the cost model)', who='Packer',
             need=['Planner tablet', 'Sheets per kit', 'Extras: bands, dowels, wax, sandpaper, movement', 'Small zip bags, mailer boxes, booklets, labels, scale'],
             blocks=[
                 ('steps', [
                     (A.kit_card(), 'Open the kit card.', 'Planner, Tracking tab: tap the kit. The card lists sheet letters, colors and extras.', 'Order number and kit name match the packing slip.'),
                     (A.collect_sheets(), 'Take one of each sheet letter.', 'A half or quarter tile counts as one sheet. Look at both faces.', 'Right colors, all letters, no cracked parts.'),
                     (A.extras_bag(), 'Fill the extras bag.', 'Use the extras list below. Dowels come pre-cut in batches on the stop-block jig.', 'Count bands and dowels twice.'),
                     (A.pack_box(), 'Pack: sheets, extras bag, booklet on top.', 'Largest sheets at the bottom. Kraft filler in the gaps so nothing slides.', 'The lid closes flat without pressing on the sheets.'),
                     (A.weigh(), 'Weigh the packed box.', 'Write the first good box weight on the kit card. Later boxes should be within 5% (Estimate).', 'More or less: something is missing or extra. Recount.'),
                     (A.box_label(), 'Label the box.', 'Lid label on top. Info label on the bottom: write the batch code in its box.', 'The batch code matches the planner.'),
                     (A.log_planner('Tracking'), 'Move the kit to Packed in the planner.', 'Packing takes the extras out of stock. Buy the shipping label in your shop app.', 'Inventory goes down. Reorder alerts show in red.'),
                 ]),
                 ('table', 'Extras list per kit (from `supply/bom_per_kit.csv`)',
                  '<table class="xt"><thead><tr><th>Kit</th><th>Sheets</th><th>Extras bag</th></tr></thead><tbody>' + extras_rows + '</tbody></table>'),
             ]),
        dict(n=7, slug='shipping', title='Shipping', color='lagoon',
             when='Every packed kit, once a day', time='About 2 min per kit (Estimate)', who='Packer',
             need=['Planner tablet', 'Shop app (Shopify or Etsy)', 'Shipping scale', '4 x 6 in label printer', 'Packing tape'],
             blocks=[
                 ('steps', [
                     (A.svg(A.tablet(64, 28, 112, 84, 6, 'Tracking')), 'Open the Packed column in the planner.', 'Ship the oldest orders first.', 'Every packed kit has an order.'),
                     (A.match_order(), 'Match the box to the order.', 'Kit name on the order = kit name on the lid label.', 'Gift order? No price slip in the box.'),
                     (A.tape_box(), 'Close and tape the box.', 'One strip across the opening edge.', 'Sheets do not slide when you tilt it.'),
                     (A.label_printer(), 'Weigh it and buy the label.', 'In the shop app, USPS Ground Advantage. Round the weight up.', 'Address matches the order.'),
                     (A.bottom_labels(), 'Stick the label on the bottom.', 'Not over the info label. The lid stays clean, because many kits are gifts.', 'Barcode flat, no wrinkles.'),
                     (A.log_planner('Tracking'), 'Mark it Shipped in the planner.', 'The shop app emails the tracking number to the customer.', 'Packed column is empty.'),
                     (A.pickup(), 'Hand over to USPS.', 'Book a free USPS Package Pickup on usps.com (check that it takes Ground Advantage), or drop off at the post office.', 'Keep the scan receipt until delivered.'),
                     ('box', 'stop', 'Hold the box if', ['The order changed or was cancelled.', 'The address looks incomplete (no apartment number, no ZIP).',
                                                         'The box is crushed or a corner is open: repack it.']),
                 ]),
             ]),
        dict(n=5, slug='weekly_maintenance', title='Weekly maintenance and calibration', color='lagoon',
             when='Every week (Friday after the last job), after a tube change, and after moving the laser', time='About 45 min (Estimate)', who='Owner',
             need=['Lens tissue and lens cleaner', 'Brush and vacuum', 'Distilled water', 'Fit coupon file', 'A scrap sheet', 'The log at the end of this SOP'],
             blocks=[
                 ('steps', [
                     (A.power_off(), 'Switch off and unplug.', 'Let the tube and head cool for 10 minutes.', 'Exhaust off, vent closed.'),
                     (A.honeycomb(), 'Clean the honeycomb and tray.', 'Lift out the honeycomb, brush off resin, empty and vacuum the tray under it.', 'No scraps left under the bed.'),
                     (A.mirrors(), 'Clean mirrors 1, 2, 3 and the lens.', 'Lens cleaner on lens tissue, one wipe per tissue. Put each part back the same way round.', 'Cracked, pitted or brown: replace it.'),
                     (A.rails(), 'Wipe the rails and belts.', 'Dry cloth on the rails. Oil only where and when the OMTech manual says.', 'The head slides smoothly by hand.'),
                     (A.water_temp(), 'Check the water loop.', 'Level, clear water, no algae. Top up with distilled water. Change it as the manual says.', 'Above 10 °C. In winter keep the heat on.'),
                     (A.air_assist(), 'Check air assist and exhaust.', 'Feel the air at the nozzle. Look in the duct for soot and grease. Clean the fan monthly.', 'Steady air. Duct clear.'),
                     (A.coupon_measure(), 'Cut the fit coupon on this week\'s wood.', 'File `fit_test_coupon` in `kits/coupon`. Push a 3 mm strip into the slot comb. Note the snug slot.', 'Snug slot moved 0.1 mm or more: update the kerf.'),
                     (A.caliper(), 'Measure the kerf squares.', 'The square part should be 30.00 mm, the hole 20.00 mm. Also try the dowel holes and the 0.3 to 0.6 mm bridges.', 'Changed: set `KERF` in `config.py`, then run `rebuild_all.sh`.'),
                     (A.frame(), 'Check the camera and frame.', 'Frame a shape on a scrap. The red dot should land where the camera image shows.', 'Off by more than 1 mm: recalibrate the camera in LightBurn.'),
                     (A.gauge_check(), 'Check the fire kit.', 'Extinguisher needle in green, pin and seal in place, blanket on its hook.', 'The smoke alarm beeps when tested.'),
                 ]),
                 ('log', 'Weekly log', ['Week of', 'Bed and tray', 'Mirrors and lens', 'Rails', 'Water', 'Air and exhaust', 'Snug slot (mm)', 'Kerf (mm)', 'Fire kit', 'Initials'], 8),
             ]),
        dict(n=6, slug='fire_and_emergency', title='Fire and emergency', color='red',
             when='Any flame that does not go out, smoke, water leak or injury. Read it before you first use the laser, and practice it.',
             time='Seconds count', who='Everyone in the workshop',
             need=['CO2 extinguisher at the laser (5 lb, B:C)', 'Fire blanket', 'Phone', 'Smoke alarm', 'First aid kit'],
             blocks=[
                 ('section', 'Flame in the laser'),
                 ('steps', [
                     (A.stop_job(), 'Press Pause or Stop.', 'This stops the beam. If the air assist keeps blowing, switch it off.', 'Do not open the lid.'),
                     (A.lid_shut_fire(), 'Keep the lid shut.', 'Without fresh air most small flames die out in seconds.', 'Watch through the window.'),
                     (A.ten_seconds(), 'Still burning after 10 seconds, or growing?', 'Switch off the laser at the power switch. Get the extinguisher. (10 s is an Estimate.)', 'Exhaust stays on only if smoke is going outside.'),
                     (A.use_extinguisher(), 'Use the CO2 extinguisher.', 'Pull the pin. Open the lid a little. Aim at the base of the flame. Squeeze in short bursts.', 'CO2 leaves no powder in the machine.'),
                     (A.blanket(), 'A burning sheet outside the machine?', 'Lay the fire blanket over it. Leave it until it is cold.', 'Never carry a burning sheet.'),
                     (A.get_out(), 'Cannot stop it? Get out.', 'Close the door behind you. Call 911 from outside. Do not go back in.', 'Your safety first. The laser can be replaced.'),
                     (A.watch_after(), 'After any flame: watch for 30 minutes.', 'Embers can relight. Check the lens and bed before the next job.', 'Log it on the Quality tab and find the cause.'),
                     ('box', 'stop', 'Prevent it', ['Never leave the laser running.', 'Empty the crumb tray every day. Keep paper and scraps away.',
                                                   'Check the air assist before every job. Dirty optics and slow speeds cause flare-ups.']),
                 ]),
                 ('section', 'Other emergencies'),
                 ('steps', [
                     (A.leak(), 'Water leak or a water alarm.', 'Switch off the laser. Never run the tube without cooling water. Mop up, then check the hoses.', 'Run again only when the loop is full and clear.'),
                     (A.burn_first_aid(), 'Small burn on the skin.', 'Cool (not cold) running water for about 10 minutes (Mayo Clinic). Large or blistered burns: get medical help.', 'Restock the first aid kit.'),
                     (A.call_card(), 'Fill in the call card. Tape it here.', 'Workshop address for 911: TODO_LUCAS. Nearest urgent care: TODO_LUCAS. OMTech support: TODO_LUCAS.', 'Everyone knows where the card is.'),
                 ]),
             ]),
    ]


# ------------------------------------------------------------------ HTML
CSS = """
@font-face { font-family: Fraunces; src: url(../../brand/fonts/Fraunces-700.ttf); font-weight: 700; }
@font-face { font-family: Inter; src: url(../../brand/fonts/Inter-400.ttf); font-weight: 400; }
@font-face { font-family: Inter; src: url(../../brand/fonts/Inter-600.ttf); font-weight: 600; }
@font-face { font-family: Inter; src: url(../../brand/fonts/Inter-700.ttf); font-weight: 700; }
@font-face { font-family: Inter; src: url(../../brand/fonts/Inter-800.ttf); font-weight: 800; }
:root { --walnut:#3A2A1F; --walnut-2:#5C4636; --birch:#F6EEE1; --paper:#FCF8F1; --line:#E6D9C4; --lagoon:#0F8B7F; --lagoon-dark:#0B6158;
  --lagoon-light:#D7EFEB; --red:#b3261e; --red-bg:#fde7e5; --ok:#1d7a3a; --accent: var(--lagoon); --accent-dark: var(--lagoon-dark); --accent-light: var(--lagoon-light); }
.red { --accent: #b3261e; --accent-dark: #8c1d17; --accent-light: #fde7e5; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; font-family: Inter, Arial, sans-serif; color: var(--walnut); background: var(--paper); font-size: 10.5pt; line-height: 1.3; }
.sheet { max-width: 7.7in; margin: 0 auto; }
@media screen { body { padding: 16px; } .sheet { max-width: 1100px; } }
header.sop { background: var(--walnut); color: #fff; border-radius: 14px; padding: 12px 16px; display: grid; grid-template-columns: auto 1fr; gap: 4px 14px; align-items: center; }
.num { grid-row: span 2; background: var(--accent); border-radius: 12px; min-width: 64px; height: 64px; display: grid; place-items: center; font: 800 13pt Inter; letter-spacing: .02em; }
.num b { display: block; font-size: 24pt; line-height: 1; }
h1 { font: 700 20pt/1.1 Fraunces, Georgia, serif; margin: 0; }
.meta { display: flex; flex-wrap: wrap; gap: 4px 16px; font-size: 9pt; color: #f1e6d6; }
.meta b { color: #fff; }
.need { margin: 8px 0 4px; display: flex; flex-wrap: wrap; gap: 6px; font-size: 9pt; align-items: center; }
.need span { background: var(--birch); border: 1px solid var(--line); border-radius: 999px; padding: 2px 9px; }
.need strong { margin-right: 2px; }
h2 { font: 700 13pt Fraunces, Georgia, serif; margin: 10px 0 4px; color: var(--accent-dark); break-after: avoid; page-break-after: avoid; }
.grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 6px; }
@media print { body { background: #fff; } }
@media screen and (max-width: 1000px) { .grid { grid-template-columns: repeat(3, 1fr); } }
@media screen and (max-width: 760px) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media screen and (max-width: 480px) { .grid { grid-template-columns: 1fr; } }
.step { background: #fff; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; break-inside: avoid; page-break-inside: avoid; display: flex; flex-direction: column; }
.pic { position: relative; aspect-ratio: 240 / 140; overflow: hidden; background: var(--birch); }
.pic svg { display: block; width: 100%; height: 100%; }
.pic.photo { background: #f4efe6; }
.n { position: absolute; left: 5px; top: 5px; width: 22px; height: 22px; border-radius: 50%; background: var(--accent); color: #fff; font: 800 10pt/22px Inter; text-align: center; z-index: 2; }
.txt { padding: 6px 8px 7px; display: flex; flex-direction: column; gap: 3px; flex: 1; }
.txt .act { font-weight: 800; font-size: 9.6pt; line-height: 1.2; }
.txt .det { font-size: 8.2pt; color: var(--walnut-2); }
.txt .chk { margin-top: auto; font-size: 8pt; font-weight: 600; color: var(--ok); padding-left: 16px; position: relative; }
.txt .chk::before { content: ""; position: absolute; left: 0; top: 2px; width: 11px; height: 11px; border-radius: 50%; background: var(--ok); }
.txt .chk::after { content: ""; position: absolute; left: 3px; top: 4.5px; width: 4px; height: 2px; border: solid #fff; border-width: 0 0 1.6px 1.6px; transform: rotate(-45deg); }
code { font-size: .92em; background: var(--birch); padding: 0 3px; border-radius: 3px; overflow-wrap: anywhere; }
.box { border-radius: 12px; padding: 9px 12px; margin-top: 10px; break-inside: avoid; }
.box h3 { margin: 0 0 4px; font: 800 10.5pt Inter; }
.box ul { margin: 0; padding-left: 18px; font-size: 9.2pt; }
.box.incard { margin-top: 0; break-inside: avoid; }
.box.incard ul { font-size: 8.6pt; padding-left: 15px; } .box.incard li { margin-bottom: 4px; }
.box.stop { background: var(--red-bg); border: 1.5px solid #f0b8b3; } .box.stop h3 { color: var(--red); }
.box.info { background: var(--lagoon-light); border: 1.5px solid #a9d8d0; } .box.info h3 { color: var(--lagoon-dark); }
.xt, .log { width: 100%; border-collapse: collapse; font-size: 8.8pt; background: #fff; break-inside: avoid; }
.xt th, .xt td, .log th, .log td { border: 1px solid var(--line); padding: 5px 7px; text-align: left; vertical-align: top; }
.xt th, .log th { background: var(--birch); font-size: 8pt; text-transform: uppercase; letter-spacing: .03em; }
.log td { height: 26px; }
.logwrap { break-before: page; }
.foot { margin-top: 10px; font-size: 8pt; color: var(--walnut-2); }
"""


def ordered(all_sops):
    return sorted(all_sops, key=lambda s: s['n'])


def render_sop(s):
    cls = ' red' if s['color'] == 'red' else ''
    h = [f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
         f'<title>SOP-{s["n"]} {esc(s["title"])} | Hartwood</title><style>{CSS}</style></head><body class="{cls.strip()}"><div class="sheet">',
         f'<header class="sop"><div class="num">SOP<b>{s["n"]}</b></div><h1>{esc(s["title"])}</h1>',
         f'<div class="meta"><span><b>When:</b> {esc(s["when"])}</span><span><b>Time:</b> {esc(s["time"])}</span><span><b>Who:</b> {esc(s["who"])}</span></div></header>',
         '<div class="need"><strong>You need:</strong>' + ''.join(f'<span>{md(x)}</span>' for x in s['need']) + '</div>']
    k = 0
    for b in s['blocks']:
        if b[0] == 'section':
            h.append(f'<h2>{esc(b[1])}</h2>')
        elif b[0] == 'steps':
            h.append('<div class="grid">')
            for item in b[1]:
                if item[0] == 'box':
                    h.append(f'<div class="box {item[1]} incard"><h3>{esc(item[2])}</h3><ul>' + ''.join(f'<li>{md(x)}</li>' for x in item[3]) + '</ul></div>')
                    continue
                art, act, det, chk = item
                k += 1
                pic = art if art.startswith('<div class="pic') else f'<div class="pic">{art}</div>'
                h.append(f'<div class="step">{pic[:pic.index(">") + 1]}<div class="n">{k}</div>{pic[pic.index(">") + 1:]}'
                         f'<div class="txt"><div class="act">{md(act)}</div><div class="det">{md(det)}</div><div class="chk">{md(chk)}</div></div></div>')
            h.append('</div>')
        elif b[0] == 'box':
            h.append(f'<div class="box {b[1]}"><h3>{esc(b[2])}</h3><ul>' + ''.join(f'<li>{md(x)}</li>' for x in b[3]) + '</ul></div>')
        elif b[0] == 'table':
            h.append(f'<h2>{md(b[1])}</h2>{b[2]}')
        elif b[0] == 'log':
            cols, rows = b[2], b[3]
            h.append(f'<div class="logwrap"><h2>{esc(b[1])}</h2><p class="foot">Tick each box when done. Write the numbers from the coupon. Keep this page at the laser.</p>'
                     '<table class="log"><thead><tr>' + ''.join(f'<th>{esc(c)}</th>' for c in cols) + '</tr></thead><tbody>' +
                     ''.join('<tr>' + '<td></td>' * len(cols) + '</tr>' for _ in range(rows)) + '</tbody></table></div>')
    h.append(f'<p class="foot">Hartwood Designs, SOP-{s["n"]}, {REV}, {DATE}. Times and settings marked Estimate are planning numbers until measured on the real machine. '
             'Machine details follow the OMTech manual when it differs from this sheet.</p>')
    h.append('</div></body></html>')
    return '\n'.join(h)


def index_html(all_sops):
    cards = ''.join(
        f'<a class="card" href="SOP-{s["n"]}_{s["slug"]}.html"><img src="../../review/production/sops/SOP-{s["n"]}_p1.png" alt="">'
        f'<b>SOP-{s["n"]}: {esc(s["title"])}</b><span>{esc(s["when"])}</span><span class="dl">PDF: SOP-{s["n"]}_{s["slug"]}.pdf</span></a>' for s in all_sops)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Workshop SOPs | Hartwood</title><style>{CSS}
.cards {{ display:grid; gap:14px; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); }}
.card {{ background:#fff; border:1px solid var(--line); border-radius:14px; padding:10px; text-decoration:none; color:var(--walnut); display:flex; flex-direction:column; gap:4px; }}
.card img {{ width:100%; border-radius:8px; border:1px solid var(--line); }}
.card span {{ font-size:.9rem; color:var(--walnut-2); }} .card .dl {{ font-size:.8rem; }}
</style></head><body><div class="sheet"><header class="sop"><div class="num">SOP<b>{len(all_sops)}</b></div><h1>Workshop SOPs</h1>
<div class="meta"><span>Print each PDF and hang it at its station. On the tablet, open the HTML.</span></div></header>
<p>Station map: <a href="../layout/workshop_layout.svg">workshop layout</a>. Quality loop: <a href="../quality_loop.md">quality_loop.md</a>.</p>
<div class="cards">{cards}</div></div></body></html>"""


def main():
    prepare_images()
    os.makedirs(REVIEW, exist_ok=True)
    F = kit_facts()
    all_sops = ordered(sops(F))
    for s in all_sops:
        base = f'SOP-{s["n"]}_{s["slug"]}'
        html = os.path.join(OUT, base + '.html')
        open(html, 'w').write(render_sop(s))
        pdf = os.path.join(OUT, base + '.pdf')
        r = subprocess.run(['node', os.path.join(ROOT, 'tools', 'html2pdf.js'), html, pdf,
                            f'Hartwood Designs  |  SOP-{s["n"]} {s["title"]}  |  {REV}  |  {DATE}'], capture_output=True, text=True)
        if r.stdout.strip() or r.returncode:
            print(r.stdout, r.stderr)
        for f in os.listdir(REVIEW):
            if f.startswith(f'SOP-{s["n"]}_p'):
                os.remove(os.path.join(REVIEW, f))
        subprocess.run(['pdftoppm', '-png', '-r', '80', pdf, os.path.join(REVIEW, f'SOP-{s["n"]}_p')], check=True)
        for f in sorted(os.listdir(REVIEW)):           # pdftoppm names pages p-1.png or p-01.png
            if f.startswith(f'SOP-{s["n"]}_p-'):
                os.rename(os.path.join(REVIEW, f), os.path.join(REVIEW, f'SOP-{s["n"]}_p{int(f.split("-")[-1][:-4])}.png'))
        pages = len([f for f in os.listdir(REVIEW) if f.startswith(f'SOP-{s["n"]}_p')])
        print(f'{base}: {pages} page(s)')
    open(os.path.join(OUT, 'index.html'), 'w').write(index_html(all_sops))


if __name__ == '__main__':
    main()
