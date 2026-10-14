# Star Slinger mechanism test plan

Status: **NEEDS PHYSICAL TEST.** The software checks prove that parts fit, touch and slide in. They cannot prove that a rubber band is held and released. Do these tests on the first 3 cut kits before selling any.

## Parts marked "needs physical test"

| Code | Part | Qty | Why it needs a test |
|---|---|---|---|
| B1, D19 | Star wheel discs (2 natural, 1 Haze Blue) | 3 | Tooth hook must hold a #64 band and let it go at the front |
| A7, C21, B2 | Trigger and anchor plates (natural, orange, natural) | 3 | Pallet depth and timing decide one band per pull |
| A2 | Square pegs that lock the wheel and trigger stacks | 4 of 10 | Snug fit (-0.03 mm) must hold the 3 layers as one |
| C8, C6, C28 | Nose hook plates and their peg | 4 | Must hold 7 stretched bands for days |
| B3, C3 | Target plate and hinge ears | 3 | Plate must swing on the dowel and fall back |
| Dowels | Wheel axle, trigger pivot, return band post, target hinge | 4 | Grip fit in the walls (-0.05 mm), spin fit in moving parts (+0.20 mm) |

## Before you start

1. Cut the fit-test coupon (`kits/coupon/`) first. Set `KERF` and the fit offsets in `engine/hartwood/config.py` from it, then rebuild with `python engine/run_kit.py blaster`.
2. Use real #64 bands (3.5 x 1/4 in) and a #16 band for the return. Write down the brand.
3. Wear safety glasses for every firing test. Fire only at the paper target or a wall. Never at a person or a pet.
4. Use the record sheet at the end. One row per kit per test.

## Tests

| # | Test | How | Pass when | If it fails, change |
|---|---|---|---|---|
| T1 | Wheel spin | After step 3, flick the wheel by hand | Turns 1 full turn freely, wobble under 1 mm | Wax the axle hole. Raise `FIT['spin']` by 0.05 |
| T2 | Escapement timing | After step 5, press the trigger slowly, then let go. Watch the wheel | Press = half a tooth, release = half a tooth, 8 pulls = 1 turn | Pallet B too shallow: lower the `18.0` radius of `b_tip` in `anchor_shape()` by 0.5. Pallet A hits a tooth tip: raise `R_TIP + 2.2` |
| T3 | Loading | Load 7 bands, one per tooth: hook on the nose, stretch back, drop over a tooth, thumb the wheel back one click | Wheel clicks back like a ratchet, each band stays put | Teeth back slope too steep: change the `(R_ROOT + 3.0, 26)` point in `wheel_shape()` |
| T4 | Hold | Loaded with 7 bands, leave on the stand for 24 h | No band fires on its own, no wall bulges more than 0.5 mm, no tab works loose | Add a fourth rib behind the wheel or a second peg in the trigger stack |
| T5 | One band per pull | Fire 50 pulls (7 loaded, reload as needed) | 50 shots, 0 doubles, at most 1 jam | Doubles: pallet B releases too early, deepen it. Jams: band slides off the hook, deepen the tooth hook (`R_TIP - 4.5`) |
| T6 | Trigger pull | Hang a luggage scale from the trigger pad, pull slowly with 7 bands loaded | 0.3 to 1.2 kg | Too heavy: move the wheel centre 1 mm up (less pallet bite). Too light: second #16 band |
| T7 | Return | Release the trigger after a pull | Trigger snaps back every time | Use a shorter #16 band or move the post `(-16, -64)` forward |
| T8 | Durability | 500 pulls in sessions of 50 | No cracked tooth, no wear flat over 0.3 mm on a pallet | Switch wheel and anchor to 3 mm birch ply (harder face) |
| T9 | Nose hook strength | 7 bands loaded for 72 h | Hook plates stay straight, peg in place | Make the hook upright 2 mm wider |
| T10 | Range and energy check | Fire 10 shots level from 1 m height, measure distance | Average 3 to 6 m. Note it on the box | Over 7 m: shorten the stretch by moving the nose hook back |
| T11 | Drop | Drop the empty ship from 1 m onto carpet, 3 times | No part falls off; any part that does is easy to push back | Tighten the fit on the part that fell |
| T12 | Target swing | Hit the target 20 times | Plate swings and settles, ears stay on | Raise the ear spin fit by 0.05 |
| T13 | Blaze orange check | Compare the orange nose, plug and cap with a FED-STD-595 12199 swatch in daylight | Same or brighter orange | Change the orange sheet supplier (see `TODO_LUCAS.md`) |

## Estimates behind the design (all Estimate, to confirm with the tests)

- Band stretch: hook at x = 155 mm, top tooth at about x = -55 mm. A #64 band (178 mm loop) stretches to about 420 mm, about 2.4 times its length. Typical wooden band guns stretch 2 to 3 times.
- The wheel holds up to 7 bands (8 teeth; one tooth sits at the release point).
- Wheel and anchor are 3 layers of 3 mm (9 mm stack) in a 9.6 mm gap, so 0.3 mm side play on each side.

## Record sheet

| Date | Kit # | Sheet batch | Band brand | T1 | T2 | T3 | T4 | T5 doubles/jams | T6 kg | T7 | T8 | T9 | T10 m | T11 | T12 | T13 | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | | | | | | | | |
| | | | | | | | | | | | | | | | | | |
| | | | | | | | | | | | | | | | | | |
