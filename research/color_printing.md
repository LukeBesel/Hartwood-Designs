# Color only on the parts (like ROKR): how to do it

Your observation is right: on ROKR sheets most of the board is natural wood and only some parts carry color.
No source says how Robotime does it (S20). From photos it looks like color printed onto the board before
laser cutting, lined up with the cut lines. That is an assumption, not a verified fact.

Our kits currently use **pre-colored sheets**: every orange part is cut from an orange sheet. That works, but
the leftover frame is colored too, each color is a separate sheet to stock, and colors are limited to what
suppliers sell.

## Three ways to get color

| | A. Pre-colored sheets (current) | B. UV printer + laser (ROKR look) | C. Mask and spray paint |
|---|---|---|---|
| How | Buy 12 x 12 sheets in each color, cut colored parts from them | Print color on natural sheets, then cut along the print | Tape the sheet, score the mask with the laser, peel the colored parts, spray, cut |
| Look | Both faces colored; edges brown | Color on the show face (or both faces), edges brown; any color, gradients and pictures possible | Flat colors; some bleed risk |
| Extra equipment | None | Desktop UV printer, about $1,700 to $2,700 | Spray booth, masking film |
| Sheet types to stock | 1 natural + 9 colors | 1 (natural only) | 1 + paints |
| Extra time per kit | None | 13 to 43 min of printing (machine time, Estimate) | 30+ min of hands-on work (Estimate) |
| Risk | Low, proven | New machine to learn; alignment; ink on basswood to test | Messy, slow, inconsistent |

C is only worth it for a few prototypes. The real choice is A now, or B when you are ready.

## Printers that fit our 12 x 12 sheet

All three below have a 330 x 420 mm bed, which takes a 300 x 300 sheet. Prices are from search summaries (S20, checked 2026-10-12). Verify them before buying.

| Printer | Price | Ink | Speed (claims) | Notes |
|---|---|---|---|---|
| xTool O1 Omni, single UV | $1,699 | $19.99 per 125 ml ($0.16/ml) | not published for single head | Best value on paper. New product: wait for owner reviews. |
| xTool O1 Omni, dual UV | $2,699 | same | about 20 sq ft/h claimed by a reseller (about 4 to 5 min per full sheet) | Faster with two heads. |
| eufyMake E1 | about $1,999 to $2,299 | $0.30/ml after the July 2026 price cut | A4 in 9.5 min (bidirectional) to 18.5 min (maker test) | Slow by most reviews; good software. |
| Procolored V11 Pro (A3) | $5,999 | varies | not checked | Over budget for now. |

## What our engine now does for printed color

Run `cd engine && ../.venv/bin/python run_kit.py <kit> --print`. It writes `kits/<kit>/print_mode/`:

- every part nested on **natural sheets only**, with colored parts grouped together so the printer covers less area;
- per sheet:
  - `*_print_front.svg` and `.pdf`: the color layer at exact size, each colored part grown by a **0.6 mm bleed**, so a small misalignment never shows bare wood at the cut line;
  - `*_print_white.svg`: the white underlayer, so pastels look right on wood;
  - `*_print_back.*`: the back side, only when a colored part shows its back in the finished model (flower petals, wings);
  - `*_print_preview.png`: what the printed sheet looks like;
- cut files with two **registration targets** in the corners, on a no-output layer, for LightBurn **Print and Cut**;
- parts whose colored face is completely hidden in the model (for example stacked vase rings) are **not printed**.

Example: `kits/floral/print_mode/cutfiles/floral_sheet_A_natural_print_preview.png` (copy in `review/print_mode/`).

## Numbers per kit (Estimate; sheet prices from S21: natural $0.92, colored about $4.50 a sheet)

| Kit | Wood with pre-colored sheets | Wood + ink with UV print | Saved per kit | Laser min (sheets / print) | Print min (both sides / one side) |
|---|---|---|---|---|---|
| Star Slinger | $6.34 | $2.76 + $0.21 = $2.97 | $3.37 | 17.6 / 18.0 | 13.2 / 6.6 |
| Emberwing | $12.68 | $4.60 + $0.27 = $4.87 | $7.81 | 24.4 / 23.9 | 14.6 / 7.4 |
| Blossom Waltz | $18.46 | $3.68 + $0.67 = $4.35 | $14.11 | 20.7 / 21.5 | 42.9 / 21.8 |

- **Margin on your own site at the middle price, after $20/h labor** (`supply/unit_economics.csv`):

  | Kit | Pre-colored sheets | UV print |
  |---|---|---|
  | Star Slinger | 36% | 40% |
  | Emberwing | 24% | 36% |
  | Blossom Waltz | 1% | 21% |

  The flower kit uses many colors (white, pink, green, yellow, blue, purple), so pre-colored sheets make it barely profitable at $49.99.
- **Payback:** at the launch plan of about 17 kits a week, printing saves about $140 a week. A $1,699 printer pays for itself in about 12 weeks (Estimate).
- **Printing time** runs on its own machine, in parallel with the laser. The floral kit needs more printing time than laser time if both sides are printed. Set `C.PRINT['two_sided'] = False` to print only the show face. From photos, ROKR seems to print one side only (assumption).

## Workflow (UV print, then cut)

1. Put a corner jig (two strips at 90 degrees) on the printer bed and the same jig on the laser bed.
2. Print `*_print_white` then `*_print_front` (most printer software takes white as its own channel) with the sheet against the jig.
3. For two-sided sheets: flip the sheet left to right, put it back against the jig, and print `*_print_back`.
4. Move the sheet to the laser, against the jig. In LightBurn, select the two targets, then **Print and Cut**: jog to target 1, set it; jog to target 2, set it; **Align output**.
5. Cut as usual. The UV ink is cured, so wipe smoke off printed faces with a damp cloth.
6. Once the two jigs are dialed in, do Print and Cut on the first sheet of a batch only. Then cut the rest straight from the jig and check one target per sheet by eye.

## Tests before you buy or switch (TODO_LUCAS)

- Ask the seller for a test print on 3 mm basswood: color plus white, then try cutting it on your laser. Check for ink chipping at the cut edge and for smoke stains.
- Time one full 300 x 300 print in color plus white. Put the real number in `C.PRINT['rate_m2_per_h']`.
- Rub test: does the ink survive pressing parts out, and the sandpaper?

## Recommendation

**Plan for UV-printed color. Buy a desktop UV printer before launch if you can spend about $1,700 more.** On real sheet prices it:

- saves $3 to $14 of material on every kit;
- makes the flower kit profitable at $49.99;
- gives the ROKR look;
- leaves one sheet type to stock.

Order a test print on basswood first (TODO_LUCAS). The xTool O1 Omni single-head ($1,699) is the value pick on paper. The dual-head ($2,699) is faster if printing becomes the bottleneck.

**If you launch without a printer**, use the pre-colored sheet files (they are the current default and every booklet matches them) and **price Blossom Waltz at $59.99**.

Switching is one setting: `COLOR_MODE = 'print'` in `engine/hartwood/config.py`, then `bash tools/rebuild_all.sh`. That reruns the booklets and the app with the print-mode part codes. Recorded as D028.
