# TODO for Lucas

Things I was not allowed to do (buy, sign up, publish, contact) or that need your hands and eyes.
Search the project for `TODO_LUCAS` to find every placeholder in files.

## Network (do first if you want me to re-verify facts)
- [ ] This build machine could not open web pages (environment network policy). All facts came from search summaries. To let a future session open pages directly, widen the environment's network access (cloud environment menu > Edit > Network access) or add the store domains to Allowed domains. Steps: https://code.claude.com/docs/en/cloud-environments#network-access

## Research spot-checks
- [ ] Spot-check 10 ROKR prices on rokronline.com / robotimeonline.com, Amazon and Walmart (Amazon column is mostly blank; Amazon hid prices from search). File: `research/data/rokr_products.csv`.
- [ ] Read 20 Amazon and Reddit reviews for ROKR M416 and Magic Piano and add rows to `research/data/review_mentions.csv` (those sites were blocked).

## Machine
- [ ] Confirm Polar 2 70W glass price, tube warranty (12 vs 24 months on OMTech page) and spare tube price with OMTech before buying. Buy direct from omtech.com (warranty does not cover Amazon/eBay third-party purchases).
- [ ] Keep the garage cell above 10 C (50 F) year round, or drain the water loop. Freezing cracks glass tubes.
- [ ] After setup: cut the fit-test coupon (`kits/coupon/`) and the speed ladder, then put real numbers into `engine/hartwood/config.py`.

## Materials
- [ ] Order one mixed 8-color pack of Creatorally 12 x 12 x 1/8 in pre-painted basswood and check that Pink, Haze Blue, Yellow and White look pastel enough.
- [ ] Check "Sunset Orange" against blaze orange (FED-STD-595 color 12199) for the blaster muzzle tip, or buy a blaze orange sheet.

## Pop-out and printed color (added 2026-10-12)
- [ ] Cut the coupon and test the four bridge tags (0.3 / 0.4 / 0.5 / 0.6 mm): pick the thinnest one that survives a shake test and still pops out with a thumb. Put it in `BRIDGE` in `engine/hartwood/config.py` and rerun the kits.
- [ ] Look at the bridge maps in `kits/<kit>/popout/` (green = good bridge, orange = note, blue = sliding edge kept clear). Press out one full sheet per kit and note any part that was hard to free.
- [ ] Decide on printed color (see `research/color_printing.md`). If yes: ask xTool or eufyMake for a test print on 3 mm basswood, time a full-sheet print, then buy the printer and set `COLOR_MODE = 'print'`. Every print file is already in `kits/<kit>/print_mode/`.
- [ ] If you print: make two identical corner jigs (printer bed and laser bed) and try LightBurn Print and Cut once with the targets in the cut files.

## Production (added 2026-10-12)
- [ ] Measure the garage and the laser (the Polar 2's outside size was not published) before building the 6 x 2.5 ft laser bench and 8 x 2.7 ft packing bench. Plan: `production/layout/workshop_layout.png`.
- [ ] Print the six SOPs (`production/sops/*.pdf`) and hang each at its station. Read SOP-6 before the first cut and practice it once.
- [ ] Fill in the call card in SOP-6: workshop address for 911, nearest urgent care, OMTech support number.
- [ ] Check the SOP steps against the OMTech manual (lid sensor, emergency stop, water alarm, lens orientation, rail oiling). No source confirmed these for the Polar 2.
- [ ] Decide on free spare parts (recommended, D034). The site already says "we will mail one free".
- [ ] After the first month, replace the Estimate times in `tools/make_capacity.py` (packing 6 min, 85% efficiency) with your own and rerun it.
