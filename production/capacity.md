# Capacity model

One OMTech Polar 2, one person per shift, 8-hour shifts, 5 days a week. All numbers are **Estimate**: laser minutes come from the engine (planning speeds in `engine/hartwood/config.py`; measure real speeds with the coupon speed ladder). Efficiency allows for warm-up, cleaning, breaks and changeovers: laser 85%, printer 85%, packing 80%. Product mix = the launch plan (6 Star Slinger : 5 Emberwing : 6 Blossom Waltz).

## Minutes per kit

| Kit | Laser + sheet swaps (sheets) | Laser (UV print) | UV printing both sides | UV printing show face only |
|---|---|---|---|---|
| Star Slinger | 17.6 | 18.0 | 13.2 | 6.6 |
| Emberwing | 24.4 | 23.9 | 14.6 | 7.4 |
| Blossom Waltz | 20.7 | 21.5 | 42.9 | 21.8 |

## Kits per shift and per week (each station alone; the smallest number is the bottleneck)

| Color method | Station | Min per kit (mix, at efficiency) | Kits per shift | Kits per week, 1 shift | 2 shifts | 3 shifts |
|---|---|---|---|---|---|---|
| Pre-colored sheets | Laser (attended) | 24.3 | 20 | 99 | 197 | 296 |
| Pre-colored sheets | Packing bench | 7.5 | 64 | 320 | 640 | 960 |
| UV-printed color | Laser (attended) | 24.7 | 19 | 97 | 195 | 292 |
| UV-printed color | Packing bench | 7.5 | 64 | 320 | 640 | 960 |
| UV-printed color | UV printer (both sides) | 28.3 | 17 | 85 | 169 | 254 |
| UV-printed color | UV printer (show face only) | 14.4 | 33 | 167 | 334 | 502 |

## Bottleneck

- **Pre-colored sheets:** the bottleneck is the laser (attended), about **99 kits a week on one shift**, 197 on two, 296 on three.
- **UV-printed color:** the bottleneck is the UV printer (both sides), about **85 kits a week on one shift**, 169 on two, 254 on three.
- **Launch demand is 17 kits a week**, so one shift on 1 to 2 days a week covers it. The rest of the time is for website, marketing and new designs.
- **The laser is the bottleneck with pre-colored sheets.** It must be attended while it runs (fire rule). Packing happens at the bench beside it during each cut, so it does not add time.
- **With UV printing, the printer becomes the bottleneck when both sides are printed** (the floral kit needs 43 min). Print the show face only (`two_sided = False`), buy the dual-head model, or run the printer in a second shift without the laser. A UV-LED printer has no open flame like the laser, but check the maker's manual before leaving it alone.
- **3 shifts** need two more people and a laser that runs 24 h. CO2 glass tubes are commonly quoted at a few thousand hours (Estimate), so budget a spare tube once you pass 2 shifts.

![Capacity](capacity.png)

How to grow: (1) measure the real cut speed (it may be faster than 30 mm/s); (2) a second laser doubles laser capacity for about $3,700; (3) a parts-per-sheet review on the engine (tighter nesting) cuts minutes per kit directly.
