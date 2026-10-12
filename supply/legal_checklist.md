# Must-do legal checklist (before the first sale)

I am not a lawyer. These are the rules the research turned up, from secondary sources checked on 2026-10-12 (search log S15, S19, S22). **Confirm each one with the agency, or a Minnesota small-business attorney, before launch.** Items marked ⚠ affect the product design.

## 1. Business setup
- [ ] **Form a Minnesota LLC.** Articles of Organization cost $155 online or in person ($135 by mail). The annual renewal costs $0 and is due by Dec 31, starting the year after you file. If you miss it, the state dissolves the LLC. *(S22, zenind.com, ezel.ai)*
- [ ] **Get an EIN** from the IRS (free) and open a business bank account.
- [ ] **Check the name.** A quick search found no "Hartwood" trademark for toys. "HEARTWOOD" is registered in class 35 for conservation services, and a "Harthwood" kitchenware brand exists. Run a full USPTO search for class 28 (toys, model kits) before printing boxes. Consider filing for your own mark later. *(S22)*
- [ ] **Check city zoning** for a home-based business with a laser in the garage. Some cities need a home occupation permit.

## 2. Sales tax
- [ ] **Register for a Minnesota sales tax permit** (Minnesota Department of Revenue, e-Services; reported to be free). You have a physical presence in Minnesota, so you collect tax on your own-site sales to Minnesota buyers. *(S22, TaxJar, Avalara)*
- [ ] **Marketplaces collect for you.** Etsy and Amazon are marketplace facilitators: they collect and remit sales tax on their sales.
- [ ] **Watch other states.** Remote sellers usually only register in another state after passing that state's threshold, often $100,000 or 200 sales. Shopify Tax or a similar tool can track this.

## 3. Product safety: keep the kits for ages 14 and up
- [ ] **Age grade every kit 14+**, on the box, the website and the booklet. That is already in the files. CPSC treats a product as a children's product if it is designed or intended mainly for children 12 or younger, judged on four factors (16 CFR 1200.2). If people over 12 are as likely to use it, it is probably a general use product. Children's products need third-party lab testing and a Children's Product Certificate. *(S22, CPSC)*
- [ ] **Keep the marketing consistent with 14+.** No cartoon kid models, no "for kids", no toy-aisle placement. Hobby, gift and "for teens and adults" are fine. CPSC looks at marketing as well as the label.
- [ ] **Small parts warning:** the federal choking-hazard label is required for toys meant for ages 3 to under 6 (16 CFR 1500.19). Our kits are 14+, so it is not required. Keep the plain warning anyway: "Small parts. Not for children under 14." It is already on the box art and in the booklet. *(S22)*
- [ ] **Keep a technical file per kit:** the design report (`kits/<kit>/<kit>_report.json`), the material sources, and the mechanism test results. It helps with insurers and marketplaces.

## 4. The rubber band blaster ⚠
- [ ] **Federal marking (15 CFR 1150).** Toy, look-alike or imitation firearms need a blaze orange plug (recessed no more than 6 mm) or a blaze orange band around the muzzle at least 6 mm deep. The Star Slinger has both: a 32 mm orange nose box, plus an orange plug and cap flush with the muzzle (D022). Check the orange against FED-STD-595 color 12199 (TODO_LUCAS item). *(S19)*
- [ ] ⚠ **California and New York color rules.**
  - California exempts imitation firearms whose surface is entirely, or mostly, bright colors (Penal Code 20175). It also requires a packaging advisory on imitation firearms made after 2005.
  - New York (2022) requires imitation weapons to be bright colors or see-through.
  - It is not clear that a rubber band "spaceship" counts as an imitation firearm. **Ask an attorney.** If yes, either:
    - make the visible surface mostly bright (print or use Haze Blue and white skins; UV printing makes this easy, see D028); or
    - do not ship the blaster to those states.

  *(S22, Giffords Law Center summary, Spectrum News)*
- [ ] **Marketplace rules.** Etsy bans realistic replicas even with orange tips but may allow bright, clearly toy-like designs. Amazon restricts toy guns without the required markings. List the blaster on your own site first, then test Etsy with the spaceship styling. *(S15)*
- [ ] **Safety warnings** on the box and in the booklet: wear eye protection, never aim at people or animals, #64 bands only. Already in the files.

## 5. California Prop 65 (wood dust)
- [ ] Wood dust has been on the Prop 65 list since 2010. **Businesses with fewer than 10 employees are exempt** by law. Retail partners sometimes require a warning by contract, so check before you sign wholesale deals. *(S22, OEHHA presentation)*

## 5b. Box labels
- [ ] **Label every box** with what it is, the net contents (count of parts and extras), and your business name and place of business (Fair Packaging and Labeling Act, FTC). The info label in `brand/packaging/` has all three; fill in your city. *(S24)*
- [ ] **No unqualified "Made in USA".** The FTC rule (16 CFR 323) needs all or virtually all parts made in the US. The labels say "Designed and laser cut in Minnesota with imported materials." Check where your plywood, bands and music movements are made before changing that line. *(S24)*

## 6. Insurance
- [ ] **Product liability plus general liability.** The average small-business product liability policy costs about $1,192 a year (AdvisorSmith). Toys are priced higher, and $1 million or $2 million limits are typical. Tell the insurer it is a 14+ hobby kit. Many marketplaces ask for proof of coverage at some sales level. *(S22)*
- [ ] **Home insurance:** tell your home insurer about the laser in the garage. Many policies exclude business equipment, or fires caused by it.

## 7. Laser workshop safety
- [ ] **Never leave the laser running unattended.** Keep a **CO2 extinguisher** (Amerex 322, about $218) and a fire blanket at the machine. On a flare: stop the job, keep the lid closed, smother. *(S22, Carnegie Mellon and Stanford EHS)*
- [ ] **Exhaust to the outside** through the built-in fan and a window vent. Run it before and during every job. Basswood plywood glue gives off fumes.
- [ ] Keep the CO2 water loop above 10 C (50 F). Freezing cracks the tube.
- [ ] Follow the six SOPs in `production/sops/`.

## 8. Selling online
- [ ] **Policies on the website:** shipping, returns, privacy and terms. Placeholders are in `website/terms/` and `website/privacy/`. If you add analytics or email marketing, update the privacy page.
- [ ] **Show your business name and a contact address** on the site and in packing slips. A PO box or virtual address keeps your home address private.
- [ ] **CAN-SPAM** (if you email customers): an unsubscribe link and your postal address in every marketing email.
- [ ] **Music in Blossom Waltz:** use a public-domain tune (for example Brahms' Lullaby or Für Elise). Don't put a copyrighted song on a custom movement without a license.

## 9. Intellectual property
- [ ] **Our designs are original.** Research only linked to ROKR, Ugears and others and never copied their images, text, instructions or designs. Keep the review images in `review/concepts/` as proof of independent design.
- [ ] Don't use other brands' names in ads or listing titles (for example "ROKR compatible"). Comparisons in your own words are fine.
