"""Shop parameters. Every number here is an Estimate until Lucas measures it.

Change these after cutting the fit-test coupon (kits/coupon) on the real laser and wood batch.
All sizes in millimetres.
"""

# --- material -------------------------------------------------------------
THICK = 3.0                 # nominal plywood thickness (Estimate: real sheets run 2.8 to 3.2)
SHEET_W = 300.0             # design sheet size (12 x 12 in sheets measure 300 to 305 mm)
SHEET_H = 300.0
SHEET_MARGIN = 8.0          # keep-out border on every sheet edge
PART_GAP = 3.0              # design gap between parts; leaves a 2.7 mm web after kerf
MIN_FEATURE = 2.5           # no wall, bridge or tab thinner than this

# --- laser ----------------------------------------------------------------
KERF = 0.15                 # full kerf width of the cut (Estimate, measure with coupon)
BRIDGE = 0.6                # micro-bridge that holds a part in the sheet

# Fit classes. Value = how much each side of a cut feature (slot, hole) moves outward
# after kerf compensation. Positive = looser. Calibrate with the coupon.
FIT = {
    'press': 0.00,          # tab in square hole, static joint (snug, no glue)
    'snug': -0.03,          # stacked slices on a key, should not slide off
    'slip': 0.15,           # part must slide or turn freely on a wooden key
    'spin': 0.20,           # round hole that turns on a dowel
    'grip': -0.05,          # round hole that holds a dowel tight
}

# --- planning speeds for the OMTech Polar 2 70W glass (Estimate) -----------
CUT_SPEED = 30.0            # mm/s, 3 mm basswood plywood, one pass
CUT_POWER = 65              # percent
SCORE_SPEED = 300.0         # mm/s, vector line engrave
SCORE_POWER = 18
FILL_SPEED = 400.0          # mm/s, raster fill engrave
FILL_POWER = 20
FILL_INTERVAL = 0.1         # mm line spacing for fill
FILL_OVERSCAN = 2.5         # mm each side of each fill line (acceleration room)
TRAVEL_SPEED = 300.0        # mm/s effective rapid move
PIERCE_TIME = 0.05          # s per laser on/off event (accel + fire delay)
SHEET_SWAP_S = 45.0         # s to open lid, swap two sheets, close, start (Estimate)
SHEETS_PER_JOB = 2          # two 12x12 sheets side by side on the 710 x 360 mm bed

# --- dowels and hardware ---------------------------------------------------
DOWEL_D = 4.76              # 3/16 in birch dowel pins (Estimate of a common bulk size)
RUBBER_BAND = '#64 rubber band, 3.5 x 1/4 in (Estimate)'

# --- colors (only supplier-confirmed 3 mm colors, see research/materials.md) ---
MATERIALS = {
    'natural': {'label': 'Natural basswood', 'face': '#ecd2a6', 'edge': '#4f301b', 'engrave': '#7a4a28'},
    'orange':  {'label': 'Sunset Orange (blaze tip)', 'face': '#ff6a13', 'edge': '#5a2a10', 'engrave': '#c9a27a'},
    'teal':    {'label': 'Haze Blue', 'face': '#7fb3c8', 'edge': '#3c3a36', 'engrave': '#d9c29f'},
    'pink':    {'label': 'Pink', 'face': '#f2a7bd', 'edge': '#6d3f3f', 'engrave': '#d8b48c'},
    'yellow':  {'label': 'Yellow', 'face': '#f6d65a', 'edge': '#6a5326', 'engrave': '#c9a26a'},
    'green':   {'label': 'Green', 'face': '#8cc084', 'edge': '#3c4a2e', 'engrave': '#d8c49a'},
    'purple':  {'label': 'Purple', 'face': '#a58ad6', 'edge': '#3e3352', 'engrave': '#d9c4a2'},
    'red':     {'label': 'Red', 'face': '#d9483b', 'edge': '#4a1c16', 'engrave': '#d8b48c'},
    'gold':    {'label': 'Gold', 'face': '#d8b04a', 'edge': '#5c4417', 'engrave': '#8e6a2a'},
    'white':   {'label': 'White', 'face': '#f4f1ea', 'edge': '#6b5b4a', 'engrave': '#c9a77f'},
}

# --- cost inputs (Estimate; see supply/ for sources) -----------------------
SHEET_COST = {               # USD per 12 x 12 in x 3 mm sheet
    'natural': 1.60,
    'colored': 3.10,
}
