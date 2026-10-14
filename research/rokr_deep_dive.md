# ROKR / Robotime deep dive

Checked 2026-10-11. Labels: **Verified** = seen in a web search summary of the linked page on that date (see `sources.md`). **Estimate** = my judgment.
Note: this build container could not open web pages directly (network policy), so "Verified" means the number appeared in a search-engine summary of that exact page. Lucas should spot-check prices before relying on them (see `TODO_LUCAS.md`).

## Company in 6 lines
- Robotime was founded in 2007 in China. It grew out of a group called "Noah Models Dynamic". Its first wooden DIY toy was an electric T-Rex in 2008. **Verified** ([robotime.com/pages/about-us](https://robotime.com/pages/about-us))
- Sub-brands: **Rolife** (miniature houses, book nooks) and **ROKR** (mechanical wooden models) launched in 2017; **robud** in 2020. **Verified** (same page)
- **Rowood** is listed as another sub-brand (colored wooden puzzles). Some sources list MewooFun instead. **Verified, sources disagree** ([Wikipedia](https://en.wikipedia.org/wiki/Robotime_Technology), [b2brazil listing](https://b2brazil.com/hotsite/suzhouropetco))
- Location: a Suzhou trade listing describes a 200,000 m2 plant (incl. under construction), 400+ machines, 1,000 to 5,000 staff, USD 50M to 100M sales, about 40% export. **Verified as a claim, not audited** ([b2brazil](https://b2brazil.com/hotsite/suzhouropetco))
- Sales channels: own stores (rokronline.com, robotimeonline.com, rolifeonline.com), Amazon, Walmart (sold by "Robotime Flagship Store"), many resellers. **Verified**
- Kits are sold as 14+ and "glue-free". **Verified** on many listings.

## Product lines (what each line is)
| Line | What it is | Typical pieces | Typical price | Example |
|---|---|---|---|---|
| Mechanical models | Working machines: engines, locomotives, typewriter, projector | 180 to 900 | $45 to $160 | Steam Engine LKA01, 469 pcs, $55.99 |
| Marble runs | Crank or motor lifts marbles; tracks and stunts | 130 to 650 | $20 to $57 | Marble Night City LGA01, 294 pcs |
| Music boxes | Wind-up spring movement plays a tune; scene moves | 84 to 600 | $30 to $70 | Magic Piano AMK81, 223 pcs, $41.99 |
| Clocks (Time Art) | Quartz or spring clocks with visible gears | 160 to 440 | $42 to $70 | Owl Clock LK503, 161 pcs, $49.99 |
| Rubber band guns | Shoot rubber bands; most are named after real firearms | 170 to 410 | $27 to $66 | M416 LQB02, 410 pcs, $59.99 |
| Flowers (Rowood) | Layered wooden flowers and bouquets | about 100 per flower | $12 to $42 | Flower Bouquet TW01H, 581 pcs, $39.99 |
| Vehicles | Small rolling cars, trains, jeeps | about 300 | $25 to $27 | Prime Steam Express MC501, 308 pcs |
| Rolife | Miniature houses, book nooks (glue, paper, LEDs) | about 100 to 200 | $30 to $60 | Corner bookstore, ~108 pcs |

All rows: **Verified** from the product table below, except "Typical" ranges, which are my summary (**Estimate**).

## Product table (51 products)
Full data with every source: [`data/rokr_products.csv`](data/rokr_products.csv). Blank cell = not found in search results.
Amazon prices were mostly hidden from search summaries, so the Amazon column is thin. That gap is in `TODO_LUCAS.md`.

| # | Product | Line | Pieces | Difficulty | Build h | Official $ | Amazon $ | Walmart $ |
|---|---|---|---|---|---|---|---|---|
| R01 | Locomotive (LK701) | Mechanical vehicle | 349 | 5.5 of 6 stars | 6 |  |  |  |
| R02 | Mechanical Typewriter (LK703B) | Mechanical | 320 | 6 of 6 stars | 12 |  | 98.99 |  |
| R03 | 3D Pinball Machine (EG01) | Mechanical game | 482 | Advanced | 12 | 158.99 |  |  |
| R04 | Dream Coffee Factory (EAB02) | Music box | 593 | 5 stars | 10 | 69.99 |  |  |
| R05 | Steam Engine (LKA01) | Mechanical vehicle | 469 | 5 of 5 stars | 7 | 55.99 |  |  |
| R06 | Space Shuttle (LKA02) | Mechanical vehicle | 446 | 5 stars | 6 |  |  |  |
| R07 | Vitascope Movie Projector (LK601) | Mechanical | 183 |  | 5 to 6 | 49.99 |  |  |
| R08 | Marble Night City (LGA01) | Marble run | 294 |  | 7 |  |  | 56.99 |
| R09 | Hip-Hop Street (MR03S) | Marble run | 134 | 3 stars | 1.5 to 2 |  |  |  |
| R10 | Marble Parkour (LG501) | Marble run | 254 |  | 6 | 39.99 | 19.99 |  |
| R11 | Marble Explorer (Swingback Wall) (LG503) | Marble run |  |  |  | 39.99 |  |  |
| R12 | Marble Spaceport (LGC01) | Marble run | 472 | Advanced | 5.5 |  |  |  |
| R13 | Gear Ball Challenge (EGC01) | Marble run game | 653 | 4 of 5 stars | 5 | 49.99 |  |  |
| R14 | Fortune Quest (EGM01) | Mechanical game | 907 |  |  | 109.99 |  |  |
| R15 | Dream Gift Factory (EAB01) | Music box | 449 |  | 12 (reviewer) | 69.99 |  |  |
| R16 | Swing Ride (EA02) | Music box | 289 | 4 of 5 stars | 6 | 49.99 |  |  |
| R17 | Tilt-A-Whirl (EA04) | Music box | 280 |  |  | 54.99 |  |  |
| R18 | Secret Garden (AMK52) | Music box | 315 |  |  | 36.99 |  |  |
| R19 | Starry Night Orrery (AMK51) | Music box | 84 |  |  | 32.99 |  | 32.99 |
| R20 | Magic Piano (AMK81) | Music box | 223 | Advanced | 4.5 | 41.99 |  | 39.99 |
| R21 | Magic Cello (AMK63) | Music box | 199 | 4 of 5 stars | 4.5 | 36.99 |  | 36.99 |
| R22 | Airplane Control Tower (AMK41) | Music box | 255 |  | 3 | 29.99 |  | 29.99 |
| R23 | Romantic Carousel (AMK62) | Music box | 336 |  | 4.5 | 36.99 |  |  |
| R24 | Owl Clock (LK503) | Clock | 161 | Advanced | 4 | 49.99 |  | 49.99 |
| R25 | Pendulum Clock (LK501) | Clock | 166 |  | 6 | 42.49 |  |  |
| R26 | Zodiac Wall Clock (LC601) | Clock | 168 |  | 3.5 | 56.99 |  |  |
| R27 | Cuckoo Clock  | Clock | 435 | Advanced | 6 to 8 | 69.99 |  | 69.99 |
| R28 | Romantic Note Wall Clock (LC701) | Clock | 231 | Advanced | 5.5 |  |  |  |
| R29 | M416 Carbine (LQB02) | Rubber band gun | 410 | 4 of 5 stars | 6 | 59.99 |  |  |
| R30 | Thompson Submachine Gun (LQB01) | Rubber band gun | 275 |  | 2 | 46.99 |  |  |
| R31 | AK-47 Assault Rifle (LQ901) | Rubber band gun | 315 |  |  | 42.99 |  |  |
| R32 | Rotating-Barrel Machine Gun (LQA01) | Rubber band gun | 412 |  |  | 59.99 |  |  |
| R33 | Mini Gun (LQ502) | Rubber band gun |  |  |  | 26.99 |  |  |
| R34 | Toy Shotgun  | Rubber band gun | 170 |  |  |  |  |  |
| R35 | Wooden Flower Bouquet (TW01H) | Flower | 581 | 3 of 5 stars | 3 | 39.99 |  | 39.99 |
| R36 | Vintage Car (MC801) | Vehicle |  |  |  | 26.99 |  |  |
| R37 | Prime Steam Express (MC501) | Vehicle | 308 |  |  | 24.99 |  |  |
| R38 | Army Jeep (MC701) | Vehicle |  |  |  | 24.99 |  |  |
| R39 | Treasure Box (LK502) | Puzzle box | 158 |  |  | 32.99 |  |  |
| R40 | Classic Printing Press (LK602) | Mechanical | 303 | 4 of 5 stars | 5 |  |  |  |
| R41 | Rhinoceros Beetle (MI01) | Creature | 156 | 3 of 5 stars | 3 |  |  |  |
| R42 | Globe  | Mechanical | 567 |  |  |  |  |  |
| R43 | Catapult  | Launcher | 142 |  |  |  |  |  |
| R44 | Chocolate Factory  | Marble run | 420 |  |  |  |  |  |
| R45 | Magic Harp  | Music box |  |  |  |  |  | 41.99 |
| R46 | Symphony of Gorgeous Dreams (AMK63M) | Music box |  |  |  |  |  | 44.99 |
| R47 | Penholder Calendar (LC501) | Desk item |  |  |  | 13.99 |  |  |
| R48 | Electric Guitar  | Music themed |  |  |  |  |  |  |
| R49 | London Tower Bridge  | Architecture | 113 |  |  |  |  |  |
| R50 | Ferris Wheel (TGN01) | Amusement |  |  |  | 29.99 |  |  |
| R51 | Red Boats (Wood Bloom Craft)  | Art scene | 219 |  |  |  |  |  |

## What the numbers say (my reading, **Estimate**)
- Price per piece clusters around $0.10 to $0.20. Music boxes and guns sit at the top of that band; marble runs and vehicles at the bottom.
- The sweet spot for gift buyers is $30 to $60 with 150 to 450 pieces and a 3 to 6 hour build.
- ROKR runs constant "sales" (regular price vs sale price on almost every page). Their real price is the sale price.
- Every rubber band gun found is a replica of a real firearm (M416, AK-47, Thompson). That limits where they can be sold (Etsy bans realistic replicas). An original, clearly-a-toy blaster is open ground.
- No ROKR dragon was found. Dragons from others are either cheap and static ($25 to $29) or premium and mechanical ($62 to $150).
- ROKR flowers are natural-wood-heavy; pastel colors plus music is only partly served (Secret Garden AMK52).
