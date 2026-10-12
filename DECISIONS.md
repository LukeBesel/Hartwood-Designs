# Decisions log

One line per decision: what I chose and why. Newest at the bottom of each section.
Labels: **Verified** = backed by a source in `research/sources.md`. **Estimate** = my best guess.

## Setup
- D001: Python engine lives in `engine/` with its own `.venv` (not committed). Reason: keeps installs inside this folder as required.
- D002: Renders use three.js in headless Chromium (Playwright). Reason: Blender is not installed, and using the same renderer as the 3D app keeps renders and app identical.

## Research
- D003: Web facts come from search-result summaries because this build machine cannot open web pages (egress policy). Labeled Verified only when the summary for that URL shows the number. Reason: honest labeling beats guessing.
- D004: ROKR table has 51 products; Amazon prices are mostly blank because Amazon pages hide prices from search summaries. Reason: I would rather leave a blank than invent a price.
- D005: Review counts are "mentions in a 68-mention sample", not a survey. Reason: Amazon, Reddit and YouTube could not be opened.
- D006: Keep all three themes (blaster, dragon, floral). The white-space map shows zero kits found for an original toy-look blaster, zero dragons at $45 to $60, and only one garden music box. No other theme beat them.
- D007: Floral kit = flower music box (bouquet in a vase on a wind-up music base). Reason: music boxes are ROKR's largest line (13 of 51 found) and flowers + music + pastel is nearly empty.
- D008: Initial target prices: blaster $49.99, dragon $54.99, flower music box $49.99 (confirmed or changed in `supply/unit_economics`). Reason: gift sweet spot $30 to $60 and our higher unit cost vs Robotime.

## Machine and material
- D009: Laser = OMTech Polar 2, 70W glass tube, $3,699.99. Reason: fastest cutting in budget (Estimate), 710 x 360 mm bed takes two 12 x 12 sheets, LightBurn included, leaves ~$2,300 for ventilation and a spare tube.
- D010: Runner-up = Polar 2 50W RF ($4,999.99) if the garage cannot stay above 10 C (water loop can freeze). Reason: air-cooled, long tube life, same bed and software.
- D011: Rejected xTool P2S (LightBurn removed on current firmware), Thunder Bolt 30W (500 x 300 mm area cannot cut a 12 in sheet, $5,795 leaves little for ventilation), OneLaser XRF and Aeon MIRA 5S (300 mm axis too small), xTool P3 (over budget).
- D012: One sheet size = 12 x 12 in x 3 mm, designed as 300 x 300 mm with an 8 mm margin (284 x 284 mm nest area). Reason: pre-colored 3 mm sheets are only sold in 12 x 12 (no 12 x 20 colored sheets found); 12 x 20 would fit the bed but breaks "one size".
- D013: Colors limited to supplier-confirmed names: Natural, Sunset Orange, Haze Blue, Pink, Yellow, Green, Purple, Red, Gold, White. Black is not used (dark sheets hurt readability, a review complaint).
- D014: Planning speeds (Estimate until measured): cut 30 mm/s, score 300 mm/s, fill engrave 400 mm/s at 0.1 mm interval.
- D015: Added a third layer besides red cut and blue fill: black 0.1 mm "score" lines for surface detail (scales, veins, panel lines). Reason: a vector score is about 10x faster than fill-engraving the same art.

## Kit engine
- D016: Colored parts are nested on half or quarter tiles when they fill less than half a sheet. One 12 x 12 colored sheet then serves 2 or 4 kits and snaps apart on bridged lines. Wood cost per kit counts only its fraction. Reason: each kit uses only a little of each color; full sheets wasted 60 to 80 percent.
- D017: Show-face parts (skins, petals, decor) carry their code on the sheet next to the part, not on the part. Inner parts carry the code on the part. Reason: review rule H4 (codes on the sheet help) without marking the visible faces.
- D018: Oblique half-lap slots are cut (T + T|cos a|) / sin a wide. Reason: the plain T-wide slot binds when the parts cross at an angle (found by the collision check on the floral leaves).
- D019: A sub-assembly (chest lid, wings, the whole ship) is checked on its own first, then mounted as one rigid unit. Reason: matches how people build (build the lid, then drop it on), and lets the path check accept steps that a part-by-part check would block.

## Kits
- D020: Blaster mechanism = 8-tooth star wheel driven by the band tension, held by a two-pallet escapement that is one piece with the trigger. One full pull releases one band. Holds 7 bands. Reason: fewest moving parts (2 rotating stacks, 1 return band) that give one shot per pull; no spring steel.
- D021: Blaster look = starship (wings, canopy, thruster, tail fin) in natural, Haze Blue and orange. No real-gun details (no magazine shape, no rails, no stock). Reason: the spec, Etsy's weapons policy (S15) and 15 CFR 1150.3(d)-style bright colors.
- D022: Blaster blaze orange: the nose box is orange around its full circumference for 32 mm, and an orange plug plus cap close the muzzle end flush. Reason: covers both 15 CFR 1150.3(a) (plug, recess at most 6 mm) and (b) (marking at least 6 mm deep around the circumference).
- D023: Blaster ships with a display stand, swinging target and a safety plaque ("AIM AT TARGETS / NEVER AT FACES"). Reason: it is shelf decor first; the plaque repeats the safety rule every time someone picks it up.

## Pop-out and color (added after Lucas's question about popping parts out and ROKR-style color)
- D024: New fifth design check, the pop-out check (`engine/hartwood/popout.py`). Bridges go only where the part is at least 4 mm wide, on straight runs, and never on an edge that slides into another part. Sliding edges are found from the 3D model: tab sides, peg sides, half-lap slots, a plug in a box. A bridge may sit on an edge that only butts against another part (a peg end, a rib edge on a wall), with a note. Holes are cut first with no bridges, and no part may sit inside another part's hole. Reason: parts must press out with a thumb and the leftover nub must never make a joint tight.
- D025: Bridge width 0.5 mm (was 0.6), LightBurn's default tab size. The coupon now tests 0.3, 0.4, 0.5 and 0.6 mm. Reason: easier pop-out; to be confirmed on real wood.
- D026: Nesting never puts a part inside another part's hole. Reason: the hole is cut first and its waste can drop through the bed, taking the small part with it. 8 parts had landed in holes (blaster and floral); fixed.
- D027: New rule in the minimum feature check: every part must be one piece. It found real bugs:
  - the blaster's front pallet tip was cut off from the trigger (the mechanism could not have worked);
  - the dragon's wing and foot tabs were 0.2 mm short of their parts;
  - two flower stems had a loose head peg;
  - the floral wall leaves were two pieces sharing one part.

  All are fixed; the floral kit now has 158 parts.
- D028: Color files are built both ways. The default (every booklet and app code matches it) is pre-colored sheets, so you can launch with no extra machine. A complete UV-print version of every kit is in `kits/<kit>/print_mode/`: natural sheets, print files with a 0.6 mm bleed, a white underlayer, back-side files, and LightBurn Print and Cut targets. **Recommendation: buy a desktop UV printer (about $1,700) and switch with `COLOR_MODE = 'print'`.** At real sheet prices it saves $3 to $14 of material per kit and lifts the flower kit from a 1% to a 21% margin at $49.99. It pays back in about 12 weeks (Estimate). Without a printer, price Blossom Waltz at $59.99. See `research/color_printing.md` and `supply/unit_economics.csv`.
- D029: Sheet prices updated from research (S21): natural $0.92 and colored about $4.50 a sheet (was $1.60 and $3.10). Reason: real 48 to 50 packs of natural sheets are cheaper, and colored sheets cost more than assumed.
