# Review mining: what buyers love and hate

Checked 2026-10-11. Sample: **68 review mentions** from **31 sources** covering **27 kits** (ROKR, Rowood and Ugears).
Raw data: [`data/review_mentions.csv`](data/review_mentions.csv). Each row has the link.

How I collected it: web search summaries of Trustpilot, eBay, Walmart, brand community forums, Pinside, independent review blogs and brand FAQ pages. I could not open Amazon, Reddit or YouTube pages from this build machine, so those are under-sampled. Counts are "mentions in my sample", not a survey. **Treat counts as directional (Estimate).** Quotes are short (under 15 words) and come from the linked page via the search summary.

## Kits covered (27)
ROKR: Marble Night City, Marble Spaceport, Marble Parkour, M416 Carbine, AK-47, Dream Gift Factory, Secret Garden, Magic Cello, Magic Piano, Owl Clock, Pendulum Clock, Mechanical Typewriter, 3D Pinball Machine, Vitascope, plus multi-kit Trustpilot and guide pages.
Rowood: Flower Bouquet.
Ugears: Locomotive, Aviator, Hogwarts Express, Safe, Treasure Box, Antique Box, a rubber band vehicle, plus multi-kit Trustpilot.

## What buyers hate (Pareto)
| Rank | Complaint | Mentions | Share | Cumulative | Example (short quote) |
|---|---|---|---|---|---|
| 1 | Mechanism does not work reliably (jams, stalls, stops) | 14 | 27% | 27% | "balls won't roll"; "rubber band got jammed/ fail to shoot"; "sometimes it stops" |
| 2 | Tight or hard fit (needs force, sanding, honing) | 11 | 21% | 48% | "a lot of sanding down to fit together in the holes" |
| 3 | Parts break during build or removal | 11 | 21% | 69% | "fit far too tightly or accidentally break" |
| 4 | Unclear instructions or easy-to-miss steps | 7 | 13% | 83% | "The black writing on the dark C sheet is hard to make out" |
| 5 | Wax and friction (missing wax, too much wax) | 5 | 10% | 92% | "proper sanding and waxing is definitely a must" |
| 6 | Support and replacement parts | 2 | 4% | 96% | Robotime suggests gluing broken parts; charges shipping |
| 7 | Fiddly small parts | 1 | 2% | 98% | "a little fiddly" |
| 8 | Missing or loose components | 1 | 2% | 100% | LED strip came loose the next day |

Top 3 = 69% of complaints, and they are linked: tight fits cause both breakage and stuck mechanisms. Fix the fit and you fix most of the list.

## What buyers love
| Theme | Mentions | Example |
|---|---|---|
| Spare parts and good support | 3 | Extras included for fragile pieces |
| Clear picture-based instructions | 3 | "almost completely relies on images" |
| Display-worthy finished model | 3 | Magic Piano 4.7 of 5 on Walmart (18 reviews) |
| Clean laser cutting, parts pop out easily | 3 | Little or no trouble popping pieces out |
| Fun challenge | 2 | "a bit frustrating but fun" |
| Satisfying working mechanism | 2 | "moves and spins wonderfully with no sticking or rubbing" |

## Design rules for every Hartwood kit (from the complaints)
| # | Rule | Fixes complaint |
|---|---|---|
| H1 | Every slot, hole and peg size comes from the **fit-test coupon** for the current wood batch. No joint should need sanding. | Tight fit, breakage |
| H2 | Tabs get a 0.3 mm **lead-in chamfer** at the tip so they start easily, then press tight. | Tight fit, breakage |
| H3 | No wall, bridge or tab thinner than **2.5 mm**. Thin long parts run with the outer grain along their length. | Breakage |
| H4 | Moving parts get **0.4 mm clearance** and turn on round dowels in round holes. Rubber bands sit in captive notches so they cannot slip off. | Mechanism unreliable |
| H5 | **"Test it now" step** right after each mechanism is built, with what "good" looks like. | Mechanism unreliable |
| H6 | Max **6 new parts per step**; new parts in color; codes and counts on every step. | Unclear instructions |
| H7 | **Poka-yoke:** asymmetric parts get a keyed tab or an engraved arrow so they cannot go in backwards. | Unclear instructions |
| H8 | Part codes engraved where readable (engraving on painted sheets shows light wood). | Unclear instructions |
| H9 | Micro-bridges (0.6 mm) on outside edges only, never on a mating face; tip card says "push from the back". | Breakage on removal |
| H10 | **Spares** of small or fragile parts placed in empty sheet space. Free replacement by part code. | Breakage, support |
| H11 | Include a wax stick and say exactly where to wax (icon in the step). | Wax and friction |
| H12 | Displays (dragon, flowers) must not depend on any mechanism to look good. | Mechanism unreliable |
