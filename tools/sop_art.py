"""Flat pictograms for the visual SOPs (inline SVG, 240 x 140 view box, brand colors).

Each public function returns one SVG string. Drawings are original and simple on purpose:
one idea per picture, big shapes, readable from a meter away on a printed sheet.
"""
from __future__ import annotations

import math

WAL, WAL2, OAK, MAPLE, BIRCH, PAPER = '#3A2A1F', '#5C4636', '#B9895B', '#EBD5B0', '#F6EEE1', '#FCF8F1'
LAG, LAGD, LAGL, BLAZE = '#0F8B7F', '#0B6158', '#D7EFEB', '#FF6A13'
RED, REDL, GREEN, GREENL, GRAY, LIGHT, WHITE = '#b3261e', '#fde7e5', '#1d7a3a', '#e3f3e7', '#8c8579', '#e6ded1', '#ffffff'
SKIN = '#E7C3A0'
SW = 2.5          # default stroke width


def svg(*els, bg=BIRCH):
    body = ''.join(els)
    return (f'<svg viewBox="0 0 240 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true">'
            f'<rect width="240" height="140" fill="{bg}"/>{body}</svg>')


def T(x, y, s, size=13, weight=700, color=WAL, anchor='middle', family='Inter'):
    return (f'<text x="{x}" y="{y}" font-family="{family}, sans-serif" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}">{s}</text>')


def R(x, y, w, h, fill=WHITE, stroke=WAL, sw=SW, rx=4, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def Cc(x, y, r, fill=WHITE, stroke=WAL, sw=SW, extra=''):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def L(x1, y1, x2, y2, stroke=WAL, sw=SW, extra=''):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" {extra}/>'


def P(d, fill='none', stroke=WAL, sw=SW, extra=''):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round" {extra}/>'


def arrow(x1, y1, x2, y2, color=LAG, sw=4, head=9):
    a = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(a), y2 - head * math.sin(a)
    p1 = (bx + head * 0.6 * math.cos(a + math.pi / 2), by + head * 0.6 * math.sin(a + math.pi / 2))
    p2 = (bx + head * 0.6 * math.cos(a - math.pi / 2), by + head * 0.6 * math.sin(a - math.pi / 2))
    return (L(x1, y1, bx, by, color, sw) +
            f'<polygon points="{x2},{y2} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="{color}"/>')


def ok(x, y, r=11):
    return Cc(x, y, r, GREEN, WHITE, 2) + P(f'M{x - r * .45},{y} L{x - r * .1},{y + r * .38} L{x + r * .5},{y - r * .38}', 'none', WHITE, 2.6)


def no(x, y, r=11):
    k = r * .38
    return Cc(x, y, r, RED, WHITE, 2) + L(x - k, y - k, x + k, y + k, WHITE, 2.6) + L(x + k, y - k, x - k, y + k, WHITE, 2.6)


def flame(cx, cy, s=1.0):
    d = 'M0,-22 C9,-11 13,-4 13,5 C13,14 7,20 0,20 C-7,20 -13,14 -13,5 C-13,-3 -6,-8 0,-22 Z'
    d2 = 'M0,-6 C4,0 6,4 6,8 C6,13 3,15 0,15 C-3,15 -6,13 -6,8 C-6,4 -3,1 0,-6 Z'
    return (f'<g transform="translate({cx},{cy}) scale({s})"><path d="{d}" fill="{BLAZE}" stroke="{RED}" stroke-width="2"/>'
            f'<path d="{d2}" fill="#ffd34d"/></g>')


def laser(x=40, y=40, w=160, lid='closed', inside='', flame_s=0):
    """Front view of a desktop CO2 laser. lid: closed | open."""
    h_body = 54
    out = []
    if lid == 'open':
        out.append(P(f'M{x + 6},{y + 26} L{x + 18},{y - 22} L{x + w - 18},{y - 22} L{x + w - 6},{y + 26} Z', LIGHT, WAL, SW))
        out.append(P(f'M{x + 20},{y + 18} L{x + 28},{y - 14} L{x + w - 28},{y - 14} L{x + w - 20},{y + 18} Z', '#cfe3e6', WAL, 1.5))
    out.append(R(x, y + 26, w, h_body, WHITE, WAL, SW, 6))                     # body
    if lid == 'closed':
        out.append(R(x + 4, y, w - 8, 30, LIGHT, WAL, SW, 6))                   # lid
        out.append(R(x + 16, y + 6, w - 32, 18, '#7d8f93', WAL, 1.5, 3, 'fill-opacity="0.45"'))
    out.append(L(x + 14, y + 40, x + w - 46, y + 40, WAL2, 2))                  # bed line
    out.append(R(x + w - 38, y + 34, 28, 34, BIRCH, WAL, 1.8, 3))                # control panel
    out.append(Cc(x + w - 24, y + 44, 4, RED, WAL, 1.2))
    out.append(R(x + w - 33, y + 54, 18, 8, LAG, WAL, 1, 2))
    out.append(R(x + 10, y + 26 + h_body, 14, 6, WAL, WAL, 1, 1) + R(x + w - 24, y + 26 + h_body, 14, 6, WAL, WAL, 1, 1))
    if flame_s:
        out.append(flame(x + w / 2 - 20, y + 16 if lid == 'closed' else y + 22, flame_s))
    out.append(inside)
    return ''.join(out)


def sheet_top(x, y, s, fill=MAPLE, parts=True, stroke=WAL2):
    out = [R(x, y, s, s, fill, stroke, 1.8, 2)]
    if parts:
        k = s / 100
        out += [R(x + 8 * k, y + 8 * k, 50 * k, 16 * k, 'none', stroke, 1.2, 2), R(x + 64 * k, y + 8 * k, 28 * k, 40 * k, 'none', stroke, 1.2, 4),
                Cc(x + 25 * k, y + 50 * k, 14 * k, 'none', stroke, 1.2), R(x + 46 * k, y + 32 * k, 12 * k, 50 * k, 'none', stroke, 1.2, 2),
                R(x + 8 * k, y + 72 * k, 32 * k, 20 * k, 'none', stroke, 1.2, 3), R(x + 64 * k, y + 56 * k, 28 * k, 36 * k, 'none', stroke, 1.2, 6)]
    return ''.join(out)


def finger(x, y, ang=0, s=1.0):
    """A pressing finger, tip at (x, y), pointing at angle ang (deg, 0 = down)."""
    return (f'<g transform="translate({x},{y}) rotate({ang}) scale({s})">'
            f'<path d="M-9,-60 L-9,-8 C-9,0 -5,4 0,4 C5,4 9,0 9,-8 L9,-60 Z" fill="{SKIN}" stroke="{WAL}" stroke-width="2"/>'
            f'<path d="M-5,-8 C-5,-3 5,-3 5,-8 L5,-16 L-5,-16 Z" fill="#f6e0cc" stroke="{WAL2}" stroke-width="1.2"/></g>')


def power_icon(cx, cy, color):
    return (f'<path d="M{cx - 8.5},{cy - 8.5} A12,12 0 1,0 {cx + 8.5},{cy - 8.5}" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round"/>'
            + L(cx, cy - 15, cx, cy - 2, color, 4))


def thermo(x, y, level=0.6, color=LAG):
    h = 70
    return (R(x - 7, y, 14, h, WHITE, WAL, SW, 7) + Cc(x, y + h + 6, 12, color, WAL, SW) +
            R(x - 3, y + h * (1 - level), 6, h * level + 4, color, color, 0, 3) +
            ''.join(L(x + 8, y + 10 + i * 14, x + 14, y + 10 + i * 14, WAL2, 1.5) for i in range(4)))


def clock(x, y, r=26, label='', frac=0.25):
    a = -math.pi / 2 + 2 * math.pi * frac
    wedge = (f'<path d="M{x},{y} L{x},{y - r + 4} A{r - 4},{r - 4} 0 {1 if frac > .5 else 0},1 {x + (r - 4) * math.cos(a):.1f},{y + (r - 4) * math.sin(a):.1f} Z" '
             f'fill="{LAGL}"/>')
    return Cc(x, y, r, WHITE, WAL, SW) + wedge + L(x, y, x, y - r + 8, WAL, 2.5) + L(x, y, x + 10, y + 4, WAL, 2.5) + (T(x, y + r + 16, label, 13) if label else '')


def tablet(x, y, w=92, h=64, rows=4, title='Planner'):
    out = [R(x, y, w, h, WAL, WAL, SW, 8), R(x + 6, y + 6, w - 12, h - 12, WHITE, WAL, 0, 3),
           R(x + 6, y + 6, w - 12, 12, LAG, LAG, 0, 3), T(x + 12, y + 16, title, 8, 700, WHITE, 'start')]
    for i in range(rows):
        yy = y + 24 + i * 9
        if yy > y + h - 10:
            break
        out.append(R(x + 12, yy, w * 0.45, 5, LIGHT, LIGHT, 0, 2))
        out.append(R(x + w - 30, yy, 14, 5, [GREEN, BLAZE, LAG, GRAY][i % 4], 'none', 0, 2))
    return ''.join(out)


def bag(x, y, w=56, h=70, items=''):
    return (R(x, y, w, h, '#ffffff', WAL, SW, 4, 'fill-opacity="0.85"') + L(x + 4, y + 10, x + w - 4, y + 10, LAG, 3) + items)


def box(x, y, w=110, h=50, open_=True):
    out = [R(x, y, w, h, WHITE, WAL, SW, 3)]
    if open_:
        out.append(P(f'M{x},{y} L{x + 14},{y - 26} L{x + w + 14},{y - 26} L{x + w},{y} Z', '#f3f1ec', WAL, SW))
    return ''.join(out)


def extinguisher(x, y, s=1.0):
    return (f'<g transform="translate({x},{y}) scale({s})">'
            f'<rect x="-14" y="0" width="28" height="70" rx="10" fill="{RED}" stroke="{WAL}" stroke-width="2.5"/>'
            f'<rect x="-6" y="-10" width="12" height="12" fill="{WAL2}" stroke="{WAL}" stroke-width="2"/>'
            f'<path d="M6,-6 L26,-10 L30,-4" fill="none" stroke="{WAL}" stroke-width="3" stroke-linecap="round"/>'
            f'<path d="M-6,-4 C-24,-2 -26,16 -22,30 L-30,40 L-16,40 L-18,30" fill="none" stroke="{WAL}" stroke-width="3" stroke-linejoin="round"/>'
            f'<rect x="-9" y="16" width="18" height="16" rx="2" fill="{WHITE}" stroke="{WAL}" stroke-width="1.5"/>'
            f'<text x="0" y="28" font-family="Inter, sans-serif" font-size="8" font-weight="800" fill="{WAL}" text-anchor="middle">CO2</text></g>')


def eye(x, y, s=1.0):
    return (f'<g transform="translate({x},{y}) scale({s})"><path d="M-30,0 C-14,-20 14,-20 30,0 C14,20 -14,20 -30,0 Z" fill="{WHITE}" stroke="{WAL}" stroke-width="2.5"/>'
            f'<circle r="10" fill="{LAG}" stroke="{WAL}" stroke-width="2"/><circle r="4" fill="{WAL}"/></g>')


# ---------------------------------------------------------------- SOP-1 start-up and shut-down

def warm_room():
    return svg(thermo(70, 26, 0.62), T(150, 62, 'above', 15, 600, WAL2), T(150, 88, '10 °C', 28, 800, LAGD), T(150, 108, '(50 °F)', 14, 600, WAL2))


def clear_area():
    return svg(laser(20, 44, 130), extinguisher(196, 54, 0.9),
               R(160, 100, 18, 10, WHITE, WAL, 1.5, 1) + R(163, 94, 18, 10, WHITE, WAL, 1.5, 1) + no(190, 32, 10) +
               R(30, 26, 40, 14, MAPLE, WAL2, 1.5, 1) + no(64, 24, 9))


def exhaust_on():
    out = [R(130, 20, 92, 100, '#d9ecf2', WAL, SW, 4), L(176, 20, 176, 120, WAL, SW), L(130, 70, 222, 70, WAL, SW),
           R(28, 74, 54, 42, WHITE, WAL, SW, 6)]
    # duct
    out.append(P('M70,74 L70,48 L150,48', 'none', GRAY, 12))
    out.append(P('M70,74 L70,48 L150,48', 'none', WAL, 1.5, 'stroke-dasharray="4 4"'))
    out += [arrow(158, 40, 214, 40, LAG, 3.5), arrow(158, 58, 214, 58, LAG, 3.5)]
    fan = ''.join(f'<ellipse cx="55" cy="95" rx="13" ry="5" transform="rotate({a} 55 95)" fill="{LAG}" fill-opacity=".8"/>' for a in (0, 60, 120))
    out.append(fan + Cc(55, 95, 4, WAL, WAL, 1))
    return svg(*out)


def water_ok():
    out = [R(60, 22, 70, 96, '#e9f5f8', WAL, SW, 8), R(62, 52, 66, 64, '#8fd0dc', 'none', 0, 6),
           L(132, 40, 144, 40, WAL, 2), T(150, 44, 'MAX', 11, 700, WAL2, 'start'),
           L(132, 96, 144, 96, WAL, 2), T(150, 100, 'MIN', 11, 700, WAL2, 'start'),
           arrow(186, 60, 140, 60, LAG, 3, 8), T(196, 64, 'here', 12, 700, LAGD, 'start')]
    out.append(P('M95,64 C101,74 104,79 104,84 C104,90 100,94 95,94 C90,94 86,90 86,84 C86,79 89,74 95,64 Z', WHITE, LAGD, 2))
    return svg(*out)


def power_on():
    return svg(laser(20, 40, 150), R(186, 46, 40, 56, WHITE, WAL, SW, 6),
               power_icon(206, 68, LAG), T(206, 96, 'ON', 12, 800, LAGD))


def lightburn_ready():
    out = [R(30, 16, 180, 100, WAL, WAL, SW, 8), R(38, 24, 164, 84, WHITE, WAL, 0, 3), R(110, 116, 20, 10, WAL, WAL, 0, 0), R(90, 124, 60, 6, WAL, WAL, 0, 3)]
    for i, (c, n) in enumerate(((WAL, 'engrave'), ('#2a78d6', 'score'), (RED, 'cut'))):
        out.append(R(46, 32 + i * 16, 12, 10, c, 'none', 0, 2) + T(64, 41 + i * 16, n, 10, 600, WAL, 'start'))
    out.append(R(124, 30, 70, 50, BIRCH, LIGHT, 1, 3) + sheet_top(136, 34, 42) )
    out.append(R(46, 84, 148, 18, GREENL, GREEN, 1.5, 4) + T(120, 97, 'Ready', 12, 800, GREEN))
    return svg(*out)


def lens_check():
    out = [Cc(86, 70, 40, '#e9f5f8', WAL, SW), Cc(86, 70, 30, 'none', '#9fc9d1', 2),
           P('M66,56 C72,48 82,44 92,44', 'none', WHITE, 5),
           Cc(100, 82, 5, '#a08260', 'none', 0, 'fill-opacity=".6"') + Cc(76, 88, 3, '#a08260', 'none', 0, 'fill-opacity=".6"'),
           P('M150,40 L210,30 L218,74 L160,88 Z', WHITE, WAL, SW), L(158, 50, 206, 42, LIGHT, 2) + L(160, 62, 210, 54, LIGHT, 2),
           arrow(150, 76, 126, 74, LAG, 3.5, 8), T(186, 112, 'lens tissue', 12, 600, WAL2)]
    return svg(*out)


def wait_smoke():
    return svg(laser(20, 46, 130, inside=''.join(f'<circle cx="{60 + i * 18}" cy="{58 - (i % 2) * 4}" r="7" fill="{GRAY}" fill-opacity=".35"/>' for i in range(4))),
               clock(196, 60, 26, '5 min', 5 / 60 * 12 * 0.083))


def power_off():
    return svg(laser(20, 40, 150), R(186, 46, 40, 56, WHITE, WAL, SW, 6),
               power_icon(206, 68, GRAY), T(206, 96, 'OFF', 12, 800, WAL2))


def tray_clean():
    out = [R(24, 70, 140, 34, '#d9d2c5', WAL, SW, 4)]
    for i in range(14):
        out.append(R(32 + (i * 37) % 128, 76 + (i * 13) % 20, 6 + i % 3 * 3, 4, OAK, 'none', 0, 1))
    out.append(P('M176,42 L210,22 L218,34 L184,54 Z', OAK, WAL, SW))
    out.append(P('M184,54 L176,42 L150,60 L166,76 Z', WAL2, WAL, SW))
    out += [arrow(150, 86, 196, 112, LAG, 3.5), R(196, 100, 30, 30, WHITE, WAL, SW, 3), T(211, 120, 'bin', 10, 700, WAL2)]
    return svg(*out)


def log_planner(title='Planner'):
    return svg(tablet(64, 28, 112, 84, 6, title), ok(176, 32, 12))


# ---------------------------------------------------------------- SOP-2 load and cut

def flat_check():
    out = [R(14, 82, 186, 8, MAPLE, WAL2, 1.8, 1), R(14, 70, 186, 6, '#cfd6da', WAL, 1.5, 1),
           P('M18,124 Q107,96 196,124', MAPLE, WAL2, 1.8), L(14, 122, 200, 122, WAL, 1),
           ok(220, 78, 10), no(220, 114, 10), T(120, 44, 'ruler', 12, 700, WAL2), L(120, 50, 120, 68, WAL2, 1.2)]
    return svg(*out)


def two_sheets():
    out = [R(14, 18, 212, 108, '#cfc6b6', WAL, SW, 4)]
    for i in range(21):
        out.append(L(18 + i * 10, 22, 18 + i * 10, 122, '#bdb3a2', 1))
    out.append(sheet_top(22, 26, 92))
    out.append(sheet_top(126, 26, 92, '#f2a57a'))
    out.append(P('M18,22 L54,22 M18,22 L18,58', 'none', LAGD, 6))
    out.append(arrow(70, 136, 70, 122, LAG, 3, 7) + arrow(176, 136, 176, 122, LAG, 3, 7))
    return svg(*out)


def focus():
    out = [R(20, 104, 200, 12, MAPLE, WAL2, 1.8, 1), R(20, 116, 200, 10, '#cfc6b6', WAL, 1.5, 1),
           P('M100,20 L140,20 L136,62 L128,78 L112,78 L104,62 Z', '#d9d2c5', WAL, SW),
           L(120, 78, 120, 104, BLAZE, 3, 'stroke-dasharray="3 3"'),
           L(160, 78, 160, 104, WAL, 1.5) + arrow(160, 90, 160, 80, WAL, 1.5, 6) + arrow(160, 92, 160, 102, WAL, 1.5, 6),
           T(170, 96, 'focus', 13, 700, WAL, 'start'), T(52, 98, '3 mm', 14, 800, LAGD)]
    return svg(*out)


def frame():
    out = [R(14, 18, 212, 108, '#cfc6b6', WAL, SW, 4), sheet_top(22, 26, 92), sheet_top(126, 26, 92, '#f2a57a'),
           R(28, 32, 184, 80, 'none', BLAZE, 3, 2, 'stroke-dasharray="7 5"'),
           Cc(212, 32, 8, '#d9d2c5', WAL, 2), Cc(212, 32, 2.5, BLAZE, 'none', 0)]
    return svg(*out)


def start_job():
    return svg(laser(20, 40, 150), Cc(206, 72, 22, LAG, WAL, SW), P('M199,61 L216,72 L199,83 Z', WHITE, WHITE, 1))


def watch_cut():
    return svg(laser(20, 50, 140), eye(196, 42, 0.9), T(196, 92, 'stay', 14, 800, LAGD), T(196, 110, 'and watch', 12, 700, WAL2))


def flare_pause():
    return svg(laser(20, 50, 140, flame_s=0.75), Cc(198, 64, 22, '#eda100', WAL, SW),
               R(189, 54, 6, 20, WAL, 'none', 0, 1) + R(201, 54, 6, 20, WAL, 'none', 0, 1),
               T(198, 108, 'lid shut', 12, 800, RED))


def print_and_cut():
    out = [sheet_top(28, 20, 104, MAPLE, False)]
    for (x, y, w, h, c) in ((40, 32, 44, 18, '#0F8B7F'), (92, 32, 30, 46, '#FF6A13'), (40, 58, 26, 54, '#0F8B7F'), (72, 88, 50, 24, '#d9638b')):
        out.append(R(x, y, w, h, c, WAL2, 1, 3))
    out += [Cc(36, 28, 5, 'none', WAL, 1.8), L(30, 28, 42, 28, WAL, 1) + L(36, 22, 36, 34, WAL, 1),
            Cc(124, 116, 5, 'none', WAL, 1.8), L(118, 116, 130, 116, WAL, 1) + L(124, 110, 124, 122, WAL, 1),
            arrow(162, 40, 132, 30, BLAZE, 3, 8), arrow(162, 108, 134, 114, BLAZE, 3, 8),
            T(190, 66, '2 targets', 13, 800, WAL), T(190, 84, 'line up,', 12, 600, WAL2), T(190, 100, 'then cut', 12, 600, WAL2)]
    return svg(*out)


def cool_wait():
    return svg(laser(20, 46, 130, inside=''.join(f'<circle cx="{60 + i * 18}" cy="{58 - (i % 2) * 4}" r="7" fill="{GRAY}" fill-opacity=".35"/>' for i in range(4))),
               clock(196, 60, 26, '30 s', 0.5))


# ---------------------------------------------------------------- SOP-3 unload and pop-out

def press_corner():
    out = [R(14, 18, 212, 108, '#cfc6b6', WAL, SW, 4), sheet_top(30, 26, 92)]
    out += [Cc(110, 44, 9, 'none', BLAZE, 2.5), finger(112, 46, -25, 0.9), ok(150, 46, 12), T(190, 80, 'moves?', 13, 800, WAL), T(190, 98, 'then lift', 12, 600, WAL2)]
    return svg(*out)


def recut():
    return svg(laser(12, 46, 128), T(194, 44, 'stuck?', 14, 800, RED), T(194, 64, 'run the cut', 12, 600, WAL2), T(194, 80, 'layer again', 12, 600, WAL2),
               T(194, 102, 'keep the sheet', 11, 700, LAGD), T(194, 116, 'in place', 11, 700, LAGD))


def light_check():
    out = [Cc(54, 70, 26, '#fff4c2', '#eda100', SW), ''.join(L(54 + 34 * math.cos(a), 70 + 34 * math.sin(a), 54 + 44 * math.cos(a), 70 + 44 * math.sin(a), '#eda100', 3) for a in [i * math.pi / 4 for i in range(8)]),
           P('M118,24 L206,32 L200,122 L112,114 Z', MAPLE, WAL2, 2)]
    for (a, b, c, d) in ((128, 42, 186, 46), (128, 60, 180, 64), (132, 80, 196, 86), (124, 98, 170, 102)):
        out.append(L(a, b, c, d, '#fff4c2', 3.5))
    out.append(L(186, 46, 196, 47, WAL, 3.5))
    out.append(Cc(190, 46, 9, 'none', RED, 2))
    return svg(*out)


def push_section():
    """Cross-section: part in the sheet, held by a bridge. Push from the back next to the bridge."""
    out = [R(10, 66, 66, 12, MAPLE, WAL2, 1.8, 0), R(88, 66, 66, 12, MAPLE, WAL2, 1.8, 0), R(166, 66, 64, 12, MAPLE, WAL2, 1.8, 0),
           R(76, 70, 12, 4, BLAZE, 'none', 0, 0), R(154, 70, 12, 4, BLAZE, 'none', 0, 0),
           T(122, 60, 'part', 12, 700, WAL2), T(40, 60, 'sheet', 12, 700, WAL2), T(198, 60, 'sheet', 12, 700, WAL2),
           finger(98, 82, 180, 0.75), arrow(132, 124, 132, 92, LAG, 3, 8),
           T(82, 30, 'bridge', 12, 800, BLAZE), L(82, 36, 82, 64, BLAZE, 1.5)]
    return svg(*out)


def snap_tiles():
    out = [P('M24,40 L116,40 L116,122 L24,122 Z', '#f2a57a', WAL2, 2), P('M124,40 L212,30 L220,112 L124,122 Z', '#f2a57a', WAL2, 2),
           L(120, 36, 120, 128, WAL, 2, 'stroke-dasharray="6 5"'),
           P('M104,22 C120,10 136,10 150,20', 'none', LAG, 3.5), f'<polygon points="152,22 140,22 148,12" fill="{LAG}"/>',
           T(70, 86, 'kit 1', 14, 800, WAL), T(172, 82, 'kit 2', 14, 800, WAL)]
    return svg(*out)


def burn_marks():
    out = [R(24, 30, 96, 70, MAPLE, WAL2, 2, 6), f'<ellipse cx="72" cy="62" rx="26" ry="12" fill="#7a5233" fill-opacity=".45"/>',
           ok(116, 32, 10), T(72, 124, 'light: sand it', 11, 700, GREEN),
           R(140, 30, 80, 70, MAPLE, WAL2, 2, 6), f'<ellipse cx="180" cy="62" rx="32" ry="20" fill="#3a2414" fill-opacity=".75"/>',
           no(216, 32, 10), T(180, 124, 'dark: remake', 11, 700, RED)]
    return svg(*out)


def bridge_fail():
    out = [sheet_top(22, 26, 74), R(48, 108, 22, 14, MAPLE, WAL2, 1.5, 2), arrow(58, 92, 58, 106, RED, 2.5, 7),
           T(58, 18, 'falls out', 12, 800, RED),
           sheet_top(144, 26, 74), Cc(181, 76, 14, MAPLE, WAL2, 1.5), P('M172,70 L186,84 M186,70 L176,78', 'none', RED, 2.5),
           T(181, 18, 'snaps / tears', 12, 800, RED)]
    return svg(*out)


def stack_label():
    out = []
    for i in range(5):
        out.append(R(40 + i * 4, 92 - i * 12, 120, 14, [MAPLE, MAPLE, '#f2a57a', '#7fc8bf', MAPLE][i], WAL2, 1.6, 2))
    out.append(R(150, 30, 66, 40, WHITE, WAL, 2, 3) + T(183, 46, 'D-0412', 11, 800, WAL) + T(183, 62, 'Emberwing', 9, 600, WAL2))
    out.append(L(150, 50, 160, 54, WAL, 1.5))
    return svg(*out)


# ---------------------------------------------------------------- SOP-4 kitting and packing

def kit_card():
    out = [R(60, 14, 120, 112, WHITE, WAL, SW, 6), R(60, 14, 120, 20, LAG, WAL, SW, 6), T(120, 29, 'Kit card', 12, 800, WHITE)]
    for i, (l, c) in enumerate((('A', MAPLE), ('B', MAPLE), ('C', '#f2a57a'), ('D', '#7fc8bf'))):
        out.append(R(72, 42 + i * 18, 14, 12, c, WAL2, 1.2, 2) + T(79, 52 + i * 18, l, 9, 800, WAL))
        out.append(R(94, 46 + i * 18, 50, 5, LIGHT, 'none', 0, 2) + ok(160, 48 + i * 18, 6))
    return svg(*out)


def collect_sheets():
    out = []
    for i, c in enumerate((MAPLE, MAPLE, '#f2a57a', '#7fc8bf')):
        x = 22 + i * 52
        out.append(sheet_top(x, 40, 44, c) + T(x + 22, 108, 'ABCD'[i], 16, 800, WAL))
    out.append(T(120, 28, 'every letter, right color', 12, 700, WAL2))
    return svg(*out)


def extras_bag():
    items = (''.join(f'<ellipse cx="{98 + i * 6}" cy="{70 + i * 4}" rx="16" ry="7" fill="none" stroke="{OAK}" stroke-width="3"/>' for i in range(3)) +
             R(86, 94, 44, 5, '#c9a46e', WAL2, 1, 2) + R(86, 102, 30, 5, '#c9a46e', WAL2, 1, 2) +
             R(132, 60, 10, 26, '#f5e6c8', WAL2, 1.2, 2) + R(136, 92, 20, 18, '#d8c6a4', WAL2, 1.2, 1))
    return svg(bag(78, 40, 84, 82, items), T(120, 28, 'extras bag', 13, 800, WAL))


def weigh():
    out = [R(40, 96, 160, 20, '#d9d2c5', WAL, SW, 4), R(84, 116, 72, 10, WAL2, WAL, 1, 2),
           R(70, 56, 100, 40, WHITE, WAL, SW, 3), R(184, 100, 34, 12, WAL, 'none', 0, 2),
           T(201, 109, '1.9', 9, 800, '#7CFFB2'),
           T(120, 34, 'within 5% of the', 12, 700, WAL2), T(120, 50, 'first good box', 12, 700, WAL2)]
    return svg(*out)


def pack_box():
    out = [box(60, 72, 120, 50, True), R(80, 48, 70, 50, LAG, WAL, 2, 3, 'transform="rotate(-6 115 73)"'),
           T(114, 76, 'booklet', 11, 800, WHITE), R(140, 54, 30, 34, '#ffffff', WAL, 1.8, 3, 'fill-opacity=".9"')]
    return svg(*out)


def box_label():
    out = [R(40, 40, 160, 70, WHITE, WAL, SW, 3), R(116, 52, 74, 46, WHITE, WAL, 1.5, 2),
           T(153, 66, 'Emberwing', 10, 800, WAL), T(153, 80, 'batch D-0412', 9, 600, WAL2),
           ''.join(R(122 + i * 5, 86, 2 + (i % 3), 8, WAL, 'none', 0, 0) for i in range(12)),
           R(52, 52, 52, 46, LAGL, LAG, 1.5, 3), T(78, 80, 'logo', 10, 700, LAGD)]
    return svg(*out)


# ---------------------------------------------------------------- SOP-5 weekly maintenance

def honeycomb():
    out = [R(26, 74, 188, 40, '#cfc6b6', WAL, SW, 3)]
    for i in range(9):
        for j in range(3):
            cx, cy = 40 + i * 20 + (j % 2) * 10, 84 + j * 10
            out.append(f'<polygon points="{cx - 5},{cy} {cx - 2.5},{cy - 4.3} {cx + 2.5},{cy - 4.3} {cx + 5},{cy} {cx + 2.5},{cy + 4.3} {cx - 2.5},{cy + 4.3}" fill="none" stroke="#9c927f" stroke-width="1.2"/>')
    out += [arrow(60, 66, 60, 26, LAG, 3.5), arrow(180, 66, 180, 26, LAG, 3.5), T(120, 46, 'lift out, brush', 12, 800, WAL)]
    return svg(*out)


def mirrors():
    pts = [(40, 40), (200, 40), (200, 90)]
    out = [L(16, 40, 40, 40, RED, 2, 'stroke-dasharray="5 4"'), L(40, 40, 200, 40, RED, 2, 'stroke-dasharray="5 4"'),
           L(200, 40, 200, 90, RED, 2, 'stroke-dasharray="5 4"'), L(200, 100, 200, 126, RED, 2, 'stroke-dasharray="5 4"')]
    for i, (x, y) in enumerate(pts[:2]):
        out.append(f'<rect x="{x - 12}" y="{y - 3}" width="24" height="6" rx="2" fill="#cfe3e6" stroke="{WAL}" stroke-width="2" transform="rotate(45 {x} {y})"/>')
        out.append(T(x, y + 24, str(i + 1), 13, 800, WAL))
    out.append(P('M188,90 L212,90 L208,104 L192,104 Z', '#d9d2c5', WAL, 2) + T(178, 100, '3', 13, 800, WAL, 'end'))
    out.append(f'<ellipse cx="200" cy="96" rx="8" ry="3" fill="#cfe3e6" stroke="{WAL}" stroke-width="1.5"/>')
    out.append(T(110, 92, 'mirrors 1, 2, 3', 13, 800, WAL) + T(110, 110, 'and the lens', 12, 600, WAL2))
    return svg(*out)


def rails():
    out = [R(20, 70, 200, 12, '#d0d4d8', WAL, SW, 3), R(90, 52, 44, 22, '#d9d2c5', WAL, SW, 3),
           P('M170,26 C176,36 180,42 180,48 C180,54 176,58 170,58 C164,58 160,54 160,48 C160,42 164,36 170,26 Z', '#eda100', WAL, 2),
           T(120, 112, 'wipe, then oil as the manual says', 11, 700, WAL2)]
    return svg(*out)


def water_temp():
    return svg(R(40, 26, 70, 92, '#e9f5f8', WAL, SW, 8), R(42, 52, 66, 64, '#8fd0dc', 'none', 0, 6),
               thermo(160, 26, 0.55), T(200, 60, 'clear', 11, 700, LAGD, 'start'), T(200, 76, 'full', 11, 700, LAGD, 'start'),
               T(200, 92, '>10 °C', 11, 700, LAGD, 'start'))


def air_assist():
    out = [P('M100,20 L140,20 L136,62 L128,78 L112,78 L104,62 Z', '#d9d2c5', WAL, SW),
           R(20, 112, 200, 10, MAPLE, WAL2, 1.8, 1), P('M140,30 C170,30 180,20 210,20', 'none', GRAY, 5)]
    for dx in (-10, 0, 10):
        out.append(arrow(120 + dx * 0.4, 84, 120 + dx, 106, LAG, 2.5, 7))
    out.append(T(40, 60, 'air', 14, 800, LAGD))
    return svg(*out)


def coupon_measure():
    out = [R(20, 30, 200, 70, MAPLE, WAL2, 2, 2)]
    for i in range(7):
        x = 36 + i * 26
        out.append(R(x, 30, 3 + i * 0.6, 26, BIRCH, WAL2, 1.2, 0) + T(x + 2, 76, f'{2.7 + i * 0.1:.1f}', 10, 700, WAL))
    out.append(R(110, 4, 6, 50, OAK, WAL, 1.5, 1) + ok(140, 16, 9))
    out.append(T(120, 122, 'snug slot = press fit', 12, 800, LAGD))
    return svg(*out)


def caliper():
    """Measure the kerf square of the coupon with a caliper."""
    out = [R(20, 40, 200, 14, '#d0d4d8', WAL, SW, 2), P('M30,54 L30,104 L44,104 L44,54', '#d0d4d8', WAL, SW),
           P('M150,30 L150,104 L136,104 L136,54', '#d0d4d8', WAL, SW), R(126, 22, 70, 36, '#d0d4d8', WAL, SW, 4),
           R(134, 28, 54, 18, '#2d3a33', WAL, 1, 2), T(161, 42, '30.00', 13, 800, '#7CFFB2'),
           R(44, 64, 92, 40, MAPLE, WAL2, 1.8, 1)]
    for i in range(18):
        out.append(L(52 + i * 9, 40, 52 + i * 9, 46 + (i % 2) * 3, WAL, 1))
    out.append(T(90, 124, 'kerf square: 30.00 mm', 12, 800, LAGD))
    return svg(*out)


def call_card():
    return svg(R(52, 16, 136, 108, WHITE, WAL, SW, 8), R(52, 16, 136, 22, RED, WAL, SW, 8), T(120, 32, 'Call card', 12, 800, WHITE),
               ''.join(R(64, 50 + i * 20, 112, 8, LIGHT, 'none', 0, 3) for i in range(4)))


def gauge_check():
    return svg(extinguisher(80, 42, 1.0), Cc(160, 62, 26, WHITE, WAL, SW),
               P('M140,66 A20,20 0 0,1 151,46', 'none', RED, 6) + P('M152,45 A20,20 0 0,1 170,46', 'none', GREEN, 6) + P('M171,47 A20,20 0 0,1 180,66', 'none', RED, 6),
               L(160, 64, 160, 46, WAL, 2.5), Cc(160, 64, 3, WAL, WAL, 1), T(160, 108, 'needle in green', 12, 700, GREEN))


# ---------------------------------------------------------------- SOP-6 fire and emergency

def lid_shut_fire():
    return svg(laser(30, 46, 150, flame_s=0.85), T(206, 56, 'KEEP', 13, 800, RED), T(206, 72, 'LID', 13, 800, RED), T(206, 88, 'SHUT', 13, 800, RED))


def stop_job():
    return svg(Cc(70, 70, 40, RED, WAL, SW), Cc(70, 70, 30, '#d23a30', WAL, 1.5), T(70, 75, 'STOP', 14, 800, WHITE),
               Cc(184, 70, 30, '#eda100', WAL, SW), R(174, 56, 7, 28, WAL, 'none', 0, 1) + R(188, 56, 7, 28, WAL, 'none', 0, 1),
               T(131, 76, 'or', 14, 700, WAL2))


def ten_seconds():
    return svg(laser(20, 50, 130, flame_s=0.6), clock(192, 62, 28, '10 s', 10 / 60))


def use_extinguisher():
    out = [laser(14, 52, 120, 'open', flame_s=0.7), extinguisher(196, 46, 0.9),
           P('M168,40 C150,44 132,60 118,74', 'none', '#cfe3e6', 10, 'stroke-opacity=".9"'),
           T(196, 128, 'aim at the base', 11, 700, WAL2)]
    return svg(*out)


def blanket():
    out = [R(30, 98, 180, 10, MAPLE, WAL2, 2, 1), flame(120, 82, 0.8),
           P('M50,96 C60,40 180,40 190,96 Z', '#c9c2b3', WAL, SW, 'fill-opacity=".92"'),
           arrow(120, 18, 120, 40, LAG, 3.5), T(120, 128, 'smother small flames outside the machine', 10, 700, WAL2)]
    return svg(*out)


def get_out():
    out = [R(30, 20, 66, 104, OAK, WAL, SW, 2), R(36, 26, 54, 98, '#d9ecf2', WAL, 1.5, 1), Cc(80, 76, 3, WAL, WAL, 1),
           arrow(108, 72, 150, 72, GREEN, 5, 11),
           R(166, 34, 44, 76, WAL, WAL, SW, 8), R(171, 42, 34, 54, WHITE, 'none', 0, 2), T(188, 76, '911', 14, 800, RED)]
    return svg(*out)


def watch_after():
    return svg(laser(20, 50, 130), eye(190, 46, 0.8), clock(190, 96, 18, '', 0.5), T(190, 132, '30 min', 12, 800, WAL))


def leak():
    out = [R(50, 30, 100, 56, WHITE, WAL, SW, 6), R(60, 40, 80, 20, '#8fd0dc', WAL, 1.5, 3),
           P('M110,86 C116,96 118,100 118,104 C118,110 114,114 110,114 C106,114 102,110 102,104 C102,100 104,96 110,86 Z', '#8fd0dc', WAL, 2),
           f'<ellipse cx="110" cy="124" rx="40" ry="6" fill="#8fd0dc" fill-opacity=".7"/>',
           R(176, 46, 40, 56, WHITE, WAL, SW, 6), power_icon(196, 76, GRAY)]
    return svg(*out)


def burn_first_aid():
    out = [P('M70,20 L70,46 C70,60 60,62 60,72', 'none', WAL, 4), R(52, 12, 36, 12, '#d0d4d8', WAL, 2, 3)]
    for i in range(4):
        out.append(L(64 + i * 4, 78 + i * 2, 62 + i * 4, 100 + i * 2, '#5bb6c9', 2.5))
    out.append(P('M40,110 C70,100 110,100 150,112 L150,128 L40,128 Z', SKIN, WAL, 2))
    out.append(clock(190, 64, 26, '10 min', 1 / 6))
    return svg(*out)


ALL = {k: v for k, v in globals().items() if callable(v) and v.__module__ == __name__ and v.__code__.co_argcount == 0
       and not v.__code__.co_flags & 4}
