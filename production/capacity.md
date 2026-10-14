# Capacity model

One OMTech Polar 2, 8-hour shifts, 5 days a week. All numbers are **Estimate**: laser minutes come from the engine (planning speeds in `engine/hartwood/config.py`; measure real speeds with the coupon speed ladder). Hands-on times are 3 min to unload and check each laser job, 6 min to pack and 2 min to ship each kit. Efficiency allows for warm-up, cleaning, breaks and changeovers: 85%. Product mix = the launch plan (6 Star Slinger : 5 Emberwing : 6 Blossom Waltz).

## Takt time

Launch demand is **17 kits a week** (Estimate). If you cut on **one day a week**, takt time = 480 min / 17 kits = **28 min per kit**. The laser needs 24 min per kit and your hands-on work 19 min, so one cutting day a week meets launch demand. On five days a week the takt time is 141 min per kit: there is lots of room to grow.

## Minutes per kit

| Kit | Laser jobs per kit | Laser + sheet swaps | You: check, pack, ship | Laser (UV print) | UV printing both sides | UV printing show face only |
|---|---|---|---|---|---|---|
| Star Slinger | 1.5 | 17.6 | 12.5 | 17.8 | 13.5 | 6.8 |
| Emberwing | 3.5 | 24.4 | 18.5 | 23.9 | 14.6 | 7.4 |
| Blossom Waltz | 3.0 | 20.7 | 17.0 | 21.5 | 42.9 | 21.8 |

Half and quarter color tiles serve 2 or 4 kits per job, so a kit can need a fraction of a job.

## Kits per day, week and month (each station alone; the smallest number is the bottleneck)

| Color method | Station | Min per kit (mix, at efficiency) | Per day, 1 shift | Per week, 1 shift | Per month, 1 shift | Per month, 2 shifts | Per month, 3 shifts |
|---|---|---|---|---|---|---|---|
| Pre-colored sheets | Laser (attended) | 24.3 | 20 | 99 | 427 | 854 | 1282 |
| Pre-colored sheets | You (check, pack, ship) | 18.7 | 26 | 129 | 558 | 1115 | 1673 |
| UV-printed color | Laser (attended) | 24.6 | 20 | 98 | 423 | 846 | 1269 |
| UV-printed color | You (check, pack, ship) | 17.5 | 27 | 137 | 594 | 1188 | 1782 |
| UV-printed color | UV printer (both sides) | 28.5 | 17 | 84 | 365 | 731 | 1096 |
| UV-printed color | UV printer (show face only) | 14.4 | 33 | 166 | 720 | 1441 | 2161 |

## Bottleneck

- **Pre-colored sheets:** the bottleneck is the laser, about **99 kits a week** (427 a month) on one shift.
- **UV-printed color:** the bottleneck is the UV printer, about **84 kits a week** (365 a month) on one shift.

## Where the bottleneck moves (one shift)

| Setup | Laser | UV printer | People | Kits per week | Bottleneck |
|---|---|---|---|---|---|
| 1 laser, you alone, pre-colored sheets | 99 | - | 129 | **99** | laser |
| 1 laser + UV printer (both sides), you alone | 98 | 84 | 137 | **84** | UV printer |
| 2 lasers, you alone | 197 | - | 129 | **129** | you |
| 2 lasers, you + a part-time packer | 197 | - | 257 | **197** | 2 lasers |

- **Launch (17 a week):** nothing limits you. About 7 hours of laser time a week, with your checking and packing done during the cuts.
- **Growing on one laser:** the laser is the bottleneck. It must be attended while it runs (fire rule), so you check, pack and ship at the bench beside it while it cuts.
- **With UV printing on both sides, the printer is the bottleneck** (the floral kit needs 43 min). Print the show face only (`two_sided = False`), buy the dual-head model, or run the printer when the laser is off. A UV-LED printer has no open flame like the laser, but check the maker's manual before leaving it alone.
- **Add a second laser and you become the bottleneck.** Your hands-on minutes per kit are then the limit. A part-time packer, or less checking per job once the first-pass yield is high, moves it back to the lasers.
- **2 and 3 shifts need more people.** You cannot attend the laser for 16 or 24 hours. CO2 glass tubes are commonly quoted at a few thousand hours (Estimate), so budget a spare tube once you pass 2 shifts.

![Capacity](capacity.png)

![Where the bottleneck moves](capacity_bottleneck.png)

How to grow, cheapest first: (1) measure the real cut speed (it may be faster than 30 mm/s); (2) tighter nesting cuts laser minutes per kit; (3) a second laser (about $3,700) plus a part-time packer roughly doubles output.
