# Laser cutter comparison (budget: $6,000 or less including ventilation)

Checked 2026-10-11. **Verified** = seen in a search summary of the linked page that day (see `sources.md`, section S16). **Estimate** = my number, with the reasoning given.

## Our job in numbers
- Material: 3 mm basswood plywood, natural and pre-colored, in **12 x 12 in** sheets (see `materials.md` for why not 12 x 20).
- Work mix: about 90% vector cutting, 10% engraving (part codes, scales, veins). **Estimate** from our kit designs.
- So **cutting speed in 3 mm basswood ply** and **uptime** decide capacity. LightBurn matters for production (layers, job saving, camera alignment, material library).

## The table
| Machine | Price | Bed (cut area) | Fits 2 sheets of 12x12 side by side? | Tube | Tube life | 3 mm basswood ply cut speed | LightBurn | Camera | Air assist | Cooling | Warranty |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **OMTech Polar 2, 70W glass** | **$3,699.99** Verified | 710 x 360 mm Verified | **Yes** (610 mm used, 50 mm spare) | DC glass CO2 | 2 to 4 years (consumable) Verified | **~30 mm/s Estimate** (between P2S 55W at 27 to 35 and P3 80W at 50) | License included Verified | 16MP autofocus Verified | Built-in pump 14-17 L/min Verified | Built-in closed water loop, 4.3 L Verified | 2 yr machine, 1 yr tube (70W+) Verified |
| OMTech Polar 2, 50W RF | $4,999.99 Verified | 710 x 360 mm Verified | Yes | RF metal | up to 30,000 h rated Verified | ~20 mm/s Estimate (RF at equal output cuts about the same or slightly slower than glass; 50W < 70W) | License included Verified | 16MP Verified | Yes | Air-cooled Verified | 2 yr (reseller) Verified |
| xTool P2S 55W | $2,999 to $3,399 Verified | 600 x 305 mm Verified | Only with zero margin (needs 600 mm exactly) | DC glass | 6,000 to 8,000 h (P2 data) Verified | 27 to 35 mm/s Verified (settings site / xTool claim) | **Removed on firmware after 2026-06-29**; old firmware only Verified | Dual 16MP Verified | Yes | Water | not found |
| Thunder Laser Bolt 30W RF | from $5,795 Verified | 500 x 300 mm Verified | **No** (one sheet, and 12 in is 305 mm, larger than 300) | RF metal | long; replacement $2,400, recharge $1,050 Verified | ~9 mm/s Estimate (30W RF) | Included Verified | Yes | Yes | Air | 2 yr Verified |
| OneLaser XRF 38W RF | $4,399 to $5,699 Verified | 600 x 300 mm Verified | No (300 mm < 305 mm) | RF metal | long | 10 mm/s at 90% Verified (vendor chart) | not confirmed | Yes | Yes | Air | not found |
| Monport 60W | $2,249.99 Verified | 24 x 16 in (610 x 406 mm) Verified | Yes, just (610 mm) | DC glass | glass | ~25 mm/s Estimate | not confirmed | not confirmed | not confirmed | Water | not found |
| Aeon MIRA 5S 45W | $3,999 to $4,999 (conflicting) Verified | 500 x 300 mm Verified | No | DC glass | glass | ~16 mm/s Estimate | not confirmed | Yes | Yes | Water | not found |
| xTool P3 80W | $6,999 base Verified | 914 x 457 mm Verified | Yes (3 sheets) | DC glass | glass | 50 mm/s at 80% Verified | not confirmed | Yes | Yes | Water | **Over budget** |
| Gweike Cloud Pro II 50W | unclear ($1,659 sale, sold out) Verified | 510 x 300 mm Verified | No | DC glass | glass | 14 to 15 mm/s Verified (vendor guide for 50W) | not confirmed | Yes | Yes | Water | not found |

Thunder Bolt price check: you remembered "from about $5,800". The 30W Bolt is **$5,795**, which matches. **Verified**. But its 500 x 300 mm cut area cannot cut a full 12 in (305 mm) sheet, and the 60W Bolt Plus 24 is $9,995.
xTool P2S check: LightBurn support was removed by recent firmware, per LightBurn's own docs. **Verified**. You can stay on old firmware, but that is a production risk.

## Decision: OMTech Polar 2, 70W glass ($3,699.99)
Why (one line each):
1. **Fastest cutting in budget** (Estimate ~30 mm/s on 3 mm basswood ply). The laser is our bottleneck, so speed is capacity.
2. **Two 12 x 12 sheets per job** on the 710 x 360 bed. Load two, cut two: half the door openings.
3. **LightBurn license included** and supported. Layers, saved jobs, camera alignment.
4. **Leaves ~$2,300** for ventilation, a spare tube, fire safety and air filtering.
5. Built-in air assist, camera, exhaust fan and closed water loop: nothing else needed to start.

Risks and how we handle them:
- Glass tube is a consumable with a 1-year warranty. **Buy a spare tube** in year 1 (Estimate $350 to $500; TODO_LUCAS to confirm price).
- **Water cooling in a Minnesota garage can freeze.** The cell must stay above 10 C (50 F) all year, or drain the loop. Heating also keeps the plywood stable, which our fit depends on.
- Speed numbers are Estimates until Lucas runs the fit coupon and a speed ladder on the real machine.

Runner-up: **Polar 2 50W RF ($4,999.99)** if the garage cannot be heated or Lucas prefers zero tube swaps. Same bed and software, air-cooled, much longer tube life, but about 1/3 slower cutting (Estimate) and only ~$1,000 left for ventilation.

## Ventilation (fits in the remaining budget)
- The Polar 2 has an internal exhaust fan with ducting. **Verified**. Run its duct straight outside through a window or wall vent. Short and straight is best.
- Optional: inline booster fan on the duct (Estimate $100 to $200).
- Indoor filter only if venting outside is impossible: OMTech 300W 4-stage extractor $749.99 **Verified**. Filters are a running cost.

All machine settings in this project use these planning speeds (Estimate, to be measured):
| Operation | Speed | Power |
|---|---|---|
| Cut 3 mm basswood ply | 30 mm/s | 65% |
| Score line (engraved line) | 300 mm/s | 18% |
| Fill engrave (part codes, small areas) | 400 mm/s, 0.1 mm line interval | 20% |
| Travel (laser off) | 300 mm/s effective | - |
