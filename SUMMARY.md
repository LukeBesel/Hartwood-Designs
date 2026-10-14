# Hartwood Designs: summary

Three original wooden model kits, designed in code and cut on one desktop laser, plus everything needed to make, sell and ship them. Open `START_HERE.html` for the visual version with links to every file.

## Numbers at a glance

| Kit | Pieces | Sheets | Laser min per kit | Cost per kit | Price | Profit per kit, own site | Checks |
|---|---|---|---|---|---|---|---|
| Star Slinger (rubber band starship) | 153 | 4 | 17.6 | $12.97 | $49.99 | $18.11 (36%) | 5 of 5 |
| Emberwing (dragon on a tower) | 152 | 8 | 24.4 | $18.69 | $54.99 | $12.97 (24%) | 5 of 5 |
| Blossom Waltz (flower music box) | 158 | 8 | 20.7 | $27.55 | $49.99 | $0.50 (1%) | 5 of 5 |

Cost is materials and packaging with pre-colored sheets. Profit is after free shipping, Shopify fees and your labor at $20/h. With a UV printer, profit rises to $20.01, $19.61 and $10.34. All money and time figures are Estimates built on Verified prices. Blossom Waltz needs $59.99 or a UV printer.

## What was built

1. **Research** (`research/`): a 51-product ROKR table, 45 competitor products, 68 review mentions turned into 12 design rules, a laser comparison of 9 machines, materials and color printing studies, and a visual dashboard (`research/dashboard/index.html`) with price vs pieces, price per piece, category mix, the complaints Pareto and a white-space map. 258 sources are listed in `research/sources.md`.
2. **Machine and design rules:** the OMTech Polar 2 70W ($3,699.99), one sheet size (12 x 12 in, 3 mm), a fit-test coupon, and planning speeds (D009 to D015).
3. **Kit engine** (`engine/`): Python with shapely. Glue-free joints (tabs, half-laps, slices on keys, discs on pegs), five design checks (collision, nothing floats, assembly path, minimum feature with a one-piece rule, and pop-out), nesting with half and quarter color tiles, cut files (SVG, DXF, LightBurn) with kerf compensation and 0.5 mm bridges, a UV-print mode with Print and Cut targets, GLB and step JSON, renders and part images. Each check is proven by breaking a test model on purpose: 7 of 7 breaks are caught, and the clean model passes.
4. **Three kits** (`kits/`): 3 scored concepts each (`review/concepts/`), hero renders and close-ups, a part image for every code (91, 107 and 106 images), cut files per sheet, bridge maps, and a mechanism test plan for the blaster. The blaster has a permanent blaze orange nose, plug and cap (15 CFR 1150).
5. **Instructions:** picture booklets as PDF and Word (22, 28 and 32 pages) with a QR code per step, and a phone-first three.js app (`/build/<kit>/step/<n>`) with animated insertion, a parts tray, tap-to-identify, saved progress and offline use. 13 of 13 app tests pass.
6. **Website and brand** (`website/`, `brand/`): a static site with a page per kit (spinning 3D model, renders, details), FAQ, safety, about, contact and checkout placeholders; logo, colors, fonts and icons; box labels, an optional retail sleeve and mockups. Screenshots of every page on desktop and phone are in `review/site/`.
7. **Production** (`production/`): a capacity model with takt time and where the bottleneck moves, a tablet planner (orders, cut queue, printable schedule, tracking board, inventory with reorder alerts, quality log with Pareto and a design-change list; 8 of 8 tests pass), seven one-page picture SOPs, a to-scale garage layout and the quality loop.
8. **Supply** (`supply/`): BOM per kit and for 25 and 100 kits, 2 or more suppliers per item, a startup shopping list (about $7,526 required), reorder points, unit economics at 3 prices with charts, and a legal must-do checklist with sources.
9. **Records:** `DECISIONS.md` (42 decisions with reasons), `TODO_LUCAS.md`, and review images for every visual in `review/`.
10. **Blaster test and preview** (`guides/`): an order list for 3 Star Slingers with a direct link for every material, tool and safety item (`BLASTER_TEST.md`, about $165 of materials), and a step-by-step LightBurn cutting guide (`HOW_TO_CUT.md`). The ship now lifts off its stand. A private claude.ai preview shows the website, 3D app, planner, SOPs and guides (`tools/build_preview.py`; the test checks 417 links, 10 pages and 5 taps, served like the real host).

## What is verified

"Verified" means I saw it in a web search summary of the linked page on 2026-10-11 or 2026-10-12. This build machine could not open web pages directly, so spot-check the important ones before you spend money.

- Laser facts: the Polar 2 70W price, bed size, LightBurn license, camera, air assist and warranty; the other 8 machines in `research/lasers.md`.
- Supply prices: natural basswood sheets, colored maker boards, rubber bands, dowels, music movements, mailers, bags, sandpaper, wax, booklet printing, shipping rates and marketplace fees (search log S21).
- Rules: 15 CFR 1150 (toy gun marking), CPSC children's product definition and the small parts rule, California Prop 65 small-business exemption, Minnesota LLC fee, Minnesota sales tax, the FTC labeling and Made in USA rules (secondary sources; confirm with the agencies or an attorney).
- From the engine itself: every part fits without overlaps, nothing floats, every step can be assembled in order, no feature is under 2.5 mm, every part is one piece, and every part has bridges only where it will pop out cleanly. These are geometry checks on the model, not tests on real wood.

## What is still a guess (Estimate)

- **Cut speeds and laser minutes** (30 mm/s cutting). Measure with the speed ladder.
- **Fit:** kerf 0.15 mm, the fit offsets and the 0.5 mm bridge. Measure with the coupon.
- **Whether the mechanisms work in real wood:** the blaster's escapement, the dragon's jaw and lid, the music box drive. Each is marked "needs physical test".
- **Colored sheet price** ($4.50 a sheet), booklet ($3.61), labels ($0.35), music movement ($3.00), and hands-on times (6 min packing, 3 min check per job, 2 min shipping).
- **Demand** (17 kits a week at launch) and 85% efficiency.
- **UV printing:** print speed, ink use and the Print and Cut accuracy.
- **Sizes I could not find:** the Polar 2's outside size, your garage, and whether your sheets measure 12 in or a bit more (box fit).
- **How ROKR colors parts:** I assumed UV printing from photos. No source confirmed it.
- **The LightBurn files** are written by my own code and have not been opened in LightBurn. The SVG and DXF files are the safe fallback.

## The first 5 things to do

1. **Choose the color method:** pre-colored sheets now, or a UV printer for about $1,700 more (D028).
2. **Order samples:** one natural sheet pack, one mixed color pack, bands, dowels and one music movement. Check the colors and measure the movement.
3. **Buy and set up the laser** direct from OMTech, in a garage kept above 10 °C, venting outside. Read SOP-6 first.
4. **Calibrate:** cut the fit coupon and a speed ladder, put the numbers in `engine/hartwood/config.py`, and run `bash tools/rebuild_all.sh`. Check one LightBurn file opens.
5. **Build 3 of each kit**, run the blaster test plan, log every problem in the planner, and fix the top bar before you sell.

Start the LLC, sales tax permit and insurance at the same time. The full list is in `TODO_LUCAS.md`.

## How to rebuild everything

```
bash tools/rebuild_all.sh             # kits, checks, cut files, renders, booklets, site, supply, SOPs, packaging
.venv/bin/python tools/make_start_here.py   # refresh START_HERE.html and run all tests
node tools/serve.js                   # then open http://localhost:8080 for the website and 3D app
.venv/bin/python tools/build_preview.py OUT   # private preview copy (hash routes, CDN three.js, glTF JSON)
node tools/test_preview.js OUT         # serve it like the host, check every link, page and main tap
```
