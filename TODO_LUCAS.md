# TODO_LUCAS

Things only you can do. I was not allowed to buy anything, create accounts, publish, contact anyone, or set your policies, so each of those is here. Search the project for `TODO_LUCAS` to find every placeholder in the files.

## The first 5 things (in this order)

1. [ ] **Choose the color method.** Pre-colored sheets (launch with no extra machine) or a UV printer (about $1,700 more, the ROKR look, better margins). See D028 and `research/color_printing.md`. It changes the shopping list and the Blossom Waltz price ($59.99 without a printer).
2. [ ] **Order samples before anything big:** one natural 12 x 12 x 1/8 in basswood pack, one mixed color pack (check Pink, Haze Blue, Yellow, White look pastel, and Sunset Orange against blaze orange), #64 and #16 bands, 3/16 in birch dowels, and one 18-note wind-up movement. Measure the movement and put its size in `MOV` in `engine/kits/floral.py`.
3. [ ] **Buy and set up the laser.** Confirm the OMTech Polar 2 70W price, tube warranty and spare tube price with OMTech, then buy direct from omtech.com (D009). Keep the garage above 10 °C (50 °F) and vent the exhaust outside. Read SOP-6 before the first cut.
4. [ ] **Calibrate.** Cut the fit coupon (`kits/coupon/`) and a speed ladder. Put your kerf, bridge width (pick from the 0.3 to 0.6 mm tags) and real speeds into `engine/hartwood/config.py`, then run `bash tools/rebuild_all.sh`. Open one `.lbrn2` file in LightBurn: the LightBurn files are written by my own code and are untested. If one will not open, import the SVG instead.
5. [ ] **Build 3 of each kit.** Run the blaster mechanism test plan (`kits/blaster/mechanism_test_plan.md`), press every sheet out, and log every problem in the planner's Quality tab. Fix the top bar before you sell.

Start the business setup (section "Legal and money") at the same time: it takes weeks.

## Purchases (I did not buy anything)

- [ ] Startup list: `supply/startup_shopping_list.csv`. Required about $7,526, recommended (UV printer) $1,759, optional $1,150. All Estimates or prices seen on 2026-10-12.
- [ ] Spare CO2 tube in year 1 (price to confirm with OMTech).
- [ ] CO2 extinguisher (Amerex 322 or similar), fire blanket, smoke alarm, first aid kit.
- [ ] Shipping scale, 4 x 6 in label printer, 12 x 12 x 2 in mailers (Uline S-5817 or similar).
- [ ] Measure a real mailer and a sheet pack. The mailer only fits if your sheets measure 12 in or less. Otherwise trim sheets on the laser or order a 12.5 in custom box.

## Accounts to create (I did not create any)

- [ ] **Store:** Shopify (Buy Button), Stripe Payment Links (one per kit) or Etsy. Paste the links where `STORE_NOTE` is in `tools/build_pages.py` and on `website/checkout/`, then run `tools/build_pages.py`. No custom payment code is needed.
- [ ] **Domain and hosting** for the static site (for example Cloudflare Pages or Netlify; `website/_redirects` is ready for both).
- [ ] **Contact form** (Formspree or Netlify Forms) and **email list** (Mailchimp or Buttondown): placeholders on the contact and home pages.
- [ ] **Shipping:** USPS rates through your shop app; check whether free USPS Package Pickup takes Ground Advantage on its own (S24).
- [ ] **GS1 US barcode**, only if a shop or Amazon asks for one (retail sleeve).

## Publishing (I did not publish anything)

- [ ] Set `SITE_URL` in `engine/hartwood/config.py` to your domain, then run `bash tools/rebuild_all.sh`. Every QR code (booklets, lid labels, sleeves) points to it.
- [ ] Deploy the `website/` folder as a static site. Test `/build/<kit>/step/1` on your phone, then turn on airplane mode and reload: it should still work.
- [ ] Print the booklets (`kits/<kit>/booklet/*.pdf`) at a print shop, or start with the PDF and the 3D app.
- [ ] Print the labels (`brand/packaging/*_label.pdf`). The sleeves are optional (phase 2).

## People to contact (I did not contact anyone)

- [ ] **OMTech:** price, warranty, spare tube, the Polar 2's outside size (not published anywhere I could find), and whether it has a lid sensor, an emergency stop and a water flow alarm. Check SOP-1, SOP-5 and SOP-6 against the manual.
- [ ] **Material suppliers:** bulk quotes for natural and colored 12 x 12 sheets (`supply/suppliers.csv`), and a wind-up movement supplier (name the tune; use a public-domain one).
- [ ] **UV printer makers** (if you chose printing): ask for a test print on 3 mm basswood and time a full sheet.
- [ ] **Sticker printer and booklet printer:** quotes (labels are $0.35 a set and booklets $3.61 in the costs, both Estimates).
- [ ] **Insurance agent:** product liability plus general liability; tell your home insurer about the laser.
- [ ] **A Minnesota small-business attorney** (one meeting): the blaster and California or New York imitation-firearm rules, the origin wording on the labels, and your terms and returns page.

## Placeholders in the files

| Placeholder | Where it is | What to put |
|---|---|---|
| Your domain | `engine/hartwood/config.py` (`SITE_URL`) | e.g. https://hartwooddesigns.com, then rebuild |
| Store links | `tools/build_pages.py` (`STORE_NOTE`), `website/checkout/` | Buy Button code or payment links |
| Legal company name | Website footer (`tools/build_pages.py`) | e.g. Hartwood Designs LLC |
| Support email | Contact page, booklets (`engine/booklet.py`) | a shop email address |
| Your city | Box labels and sleeves (`brand/make_packaging.py`) | city name; a PO box works |
| About page story and photo | `tools/build_pages.py` | your story, a workshop photo |
| Terms, shipping, returns, privacy | `website/terms/`, `website/privacy/`, FAQ | your policies (have them checked) |
| Music box tune | FAQ in `tools/build_pages.py` | the movement's tune |
| SOP-6 call card | `production/sops/SOP-6_fire_and_emergency.pdf` (print, then write on it) | workshop address, urgent care, OMTech support |
| UPC barcode | Retail sleeve (`brand/make_packaging.py`) | only if needed |
| Sticker printer quote | `supply/suppliers.csv` (via `tools/make_supply.py`) | price per label set |

## Legal and money

Details and sources: `supply/legal_checklist.md`.

- [ ] Form a Minnesota LLC ($155 online), get an EIN, open a business bank account.
- [ ] Register for a Minnesota sales tax permit.
- [ ] Run a full USPTO trademark search for "Hartwood" in class 28 (toys) before printing boxes.
- [ ] Check city zoning for a home business with a laser.
- [ ] Product liability insurance (about $1,192 a year average for small businesses, toys cost more).
- [ ] Keep every kit 14+ on the box, site and booklet, and in your marketing.
- [ ] Blaster: check the orange against FED-STD-595 color 12199; ask the attorney about California and New York rules; read Etsy's and Shopify's policies before listing it (S15, S24).
- [ ] Labels: no unqualified "Made in USA" (S24).
- [ ] Decide on free spare parts (recommended, D034). The site already says "we will mail one free".

## Check my research (spot-checks)

- [ ] This build machine could not open web pages: every fact came from web search summaries (see `research/sources.md`). Spot-check 10 ROKR prices in `research/data/rokr_products.csv` (the Amazon column is mostly blank) and the laser and material prices before you buy.
- [ ] Read 20 Amazon and Reddit reviews for the ROKR M416 and Magic Piano and add rows to `research/data/review_mentions.csv` (those sites were blocked).
- [ ] To let a future session open pages directly, widen the environment's network access (cloud environment menu > Edit > Network access): https://code.claude.com/docs/en/cloud-environments#network-access

## Workshop

- [ ] Measure the garage and the laser before building the 6 x 2.5 ft laser bench and the 8 x 2.7 ft packing bench (`production/layout/workshop_layout.png`).
- [ ] Print the seven SOPs (`production/sops/*.pdf`) and hang each at its station. Practice SOP-6 once.
- [ ] Keep the garage above 10 °C (50 °F) all year, or drain the water loop. Freezing cracks glass tubes.
- [ ] After the first month, replace my Estimate times in `tools/make_capacity.py` (3 min check per job, 6 min packing, 2 min shipping, 85% efficiency) with your own and rerun it.

## Pop-out and printed color

- [ ] Look at the bridge maps in `kits/<kit>/popout/` (green = good bridge, orange = note, blue = sliding edge kept clear). Press out one full sheet per kit and note any part that was hard to free.
- [ ] If you print: make two identical corner jigs (printer bed and laser bed) and try LightBurn Print and Cut once with the targets in the cut files.
