"""
Vehicle measurement pack: every dimension the model still estimates, with diagrams and boxes to fill in.

Reads cad/params.py (so each item shows what the model currently assumes) and writes:
    docs/measurements/measurement-sheet.html   A4 portrait, print it or open it in a browser
    docs/measurements/measurements.csv         the same items, one row per value, for entering results digitally
    docs/measurements/diagrams/*.svg           the diagrams on their own
Make the PDF with:  cd tools/render && node wiring_pdf.mjs ../../docs/measurements/measurement-sheet.html \
                        ../../docs/measurements/measurement-sheet.pdf

Usage:  python3 tools/measure/measure_sheet.py
"""
import csv
import math
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cad"))
import params as P  # noqa: E402

OUT = ROOT / "docs/measurements"
DATE = "2026-10-20"
RED = "#c92a2a"


# ============================================================================ SVG helpers
class Fig:
    """A diagram in model millimetres. map(x, z) -> paper px; dims and callouts are drawn in paper space."""

    def __init__(self, key, title, w, h, x0, z0, s, ox=40, oy=None):
        self.key, self.title, self.w, self.h = key, title, w, h
        self.x0, self.z0, self.s, self.ox = x0, z0, s, ox
        self.oy = h - 40 if oy is None else oy
        self.el = []

    def m(self, x, z):
        return (self.ox + (x - self.x0) * self.s, self.oy - (z - self.z0) * self.s)

    def raw(self, s):
        self.el.append(s)

    def poly(self, pts, cls="o", close=True, fill=None):
        d = " ".join(f"{a:.1f},{b:.1f}" for a, b in (self.m(*p) for p in pts))
        tag = "polygon" if close else "polyline"
        f = f' fill="{fill}"' if fill else ""
        self.raw(f'<{tag} points="{d}" class="{cls}"{f}/>')

    def rect(self, x1, z1, x2, z2, cls="o", fill=None):
        self.poly([(x1, z1), (x2, z1), (x2, z2), (x1, z2)], cls, fill=fill)

    def line(self, x1, z1, x2, z2, cls="o"):
        (a, b), (c, d) = self.m(x1, z1), self.m(x2, z2)
        self.raw(f'<line x1="{a:.1f}" y1="{b:.1f}" x2="{c:.1f}" y2="{d:.1f}" class="{cls}"/>')

    def circle(self, x, z, r, cls="o", fill=None):
        a, b = self.m(x, z)
        f = f' fill="{fill}"' if fill else ""
        self.raw(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="{r * self.s:.1f}" class="{cls}"{f}/>')

    def text(self, x, z, s, size=10, anchor="middle", cls="t", dx=0, dy=0, rot=0):
        a, b = self.m(x, z)
        a, b = a + dx, b + dy
        r = f' transform="rotate({rot} {a:.1f} {b:.1f})"' if rot else ""
        self.raw(f'<text x="{a:.1f}" y="{b:.1f}" font-size="{size}" text-anchor="{anchor}" class="{cls}"{r}>{escape(s)}</text>')

    def bubble(self, px, py, label):
        w = max(22, len(label) * 7.2 + 8)
        self.raw(f'<rect x="{px - w / 2:.1f}" y="{py - 8:.1f}" width="{w:.1f}" height="16" rx="8" class="bub"/>'
                 f'<text x="{px:.1f}" y="{py + 3.8:.1f}" font-size="10.5" text-anchor="middle" class="bt">{escape(label)}</text>')

    def dim(self, a, b, off, label, at=0.5, ext=True):
        """Dimension between model points a, b; off = paper px offset (perpendicular, + = left of a->b)."""
        (x1, y1), (x2, y2) = self.m(*a), self.m(*b)
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        p1 = (x1 + nx * off, y1 + ny * off)
        p2 = (x2 + nx * off, y2 + ny * off)
        if ext and abs(off) > 2:
            for (sx, sy), (ex, ey) in (((x1, y1), p1), ((x2, y2), p2)):
                o = 3 if off > 0 else -3
                self.raw(f'<line x1="{sx + nx * o:.1f}" y1="{sy + ny * o:.1f}" x2="{ex + nx * o:.1f}" y2="{ey + ny * o:.1f}" class="ext"/>')
        self.raw(f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" class="dim" '
                 f'marker-start="url(#ar)" marker-end="url(#ar)"/>')
        self.bubble(p1[0] + (p2[0] - p1[0]) * at, p1[1] + (p2[1] - p1[1]) * at, label)

    def call(self, pt, label, dx, dy):
        """Callout: leader from model point pt to a bubble offset (dx, dy) paper px."""
        x, y = self.m(*pt)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" fill="{RED}"/>'
                 f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + dx:.1f}" y2="{y + dy:.1f}" class="lead"/>')
        self.bubble(x + dx, y + dy, label)

    def note(self, px, py, s, size=9.5, anchor="start"):
        self.raw(f'<text x="{px}" y="{py}" font-size="{size}" text-anchor="{anchor}" class="n">{escape(s)}</text>')

    def svg(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="100%" '
                f'font-family="Inter, Segoe UI, Arial, sans-serif"><defs>'
                f'<marker id="ar" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                f'<path d="M0,2 L5,5 L0,8 M10,2 L5,5 L10,8" fill="none" stroke="{RED}" stroke-width="1.4"/></marker>'
                f'<pattern id="hat" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                f'<line x1="0" y1="0" x2="0" y2="6" stroke="#adb5bd" stroke-width="1.2"/></pattern></defs>'
                f'<style>.o{{fill:none;stroke:#212529;stroke-width:1.5}}.l{{fill:none;stroke:#868e96;stroke-width:1;stroke-dasharray:5 3}}'
                f'.f{{fill:#e9ecef;stroke:#495057;stroke-width:1.2}}.h{{fill:url(#hat);stroke:#495057;stroke-width:1.2}}'
                f'.c{{fill:none;stroke:#495057;stroke-width:0.8;stroke-dasharray:12 3 2 3}}'
                f'.dim{{stroke:{RED};stroke-width:1.1}}.ext{{stroke:{RED};stroke-width:0.6;opacity:.7}}.lead{{stroke:{RED};stroke-width:0.9}}'
                f'.bub{{fill:#fff;stroke:{RED};stroke-width:1.2}}.bt{{fill:{RED};font-weight:700}}.t{{fill:#343a40}}'
                f'.n{{fill:#495057;font-style:italic}}</style>' + "".join(self.el) + "</svg>")


# ============================================================================ diagrams
TL, TW, TD = P.TUB_L, P.TUB_W, P.TUB_D
HW, AG, AH, AL = TW / 2, P.ARCH_GAP / 2, P.ARCH_H, P.ARCH_L
UL, LT = P.UNDER_LID_Z, P.LID_TOP_Z
TZ = P.TENT_Z0
BAR_T = P.RACK_BAR[1]


def fig_plan():
    f = Fig("d1-tub-plan", "D1 · Tub, plan view (from above)", 760, 640, -200, -880, 0.31, ox=60, oy=40 + 1760 * 0.31)
    # map: x along, z slot = Y (driver up)
    f.rect(-55, -HW - 55, TL + P.TAILGATE_T, HW + 55, "l")
    f.rect(0, -HW, TL, HW)
    for s in (1, -1):
        f.rect(0, s * HW, AL, s * AG, "h")
        a = P.ARCH_POCKET
        f.rect(a["x0"], s * AG, a["x1"], s * (AG + 25), "f")
    for k in range(-7, 8):
        f.line(5, k * P.RIB_PITCH, TL - 5, k * P.RIB_PITCH, "l")
    f.line(-150, 0, TL + 120, 0, "c")
    f.rect(TL, -HW, TL + P.TAILGATE_T, HW, "f")
    f.rect(P.FACTORY_OUTLET[0] - 50, -HW, P.FACTORY_OUTLET[0] + 50, -HW + 22, "f")
    f.rect(-150, -HW + 60, P.CAB_REAR_X, HW - 60, "l")
    f.text(-125, 0, "CAB", 10, rot=-90, dx=-4)
    f.text(TL + 30, 0, "TAILGATE", 10, rot=90, dx=4)
    f.text(1150, HW, "DRIVER SIDE", 10, dy=-22)
    f.text(1150, -HW, "PASSENGER SIDE", 10, dy=34)
    f.text(AL / 2, AG + 95, "arch", 10)
    f.text(AL / 2, -AG - 95, "arch", 10)
    f.text(1000, 40, "centreline (Y = 0)", 9, cls="n")
    # dims
    f.dim((0, 80), (TL, 80), -0, "T1")
    for s, lab in ((1, "T2 D"), (-1, "T2 P")):
        f.dim((AL, s * (HW - 60)), (TL, s * (HW - 60)), 0, lab)
    f.dim((1000, -HW), (1000, HW), 0, "T3", at=0.62)
    f.dim((1460, -HW), (1460, HW), 0, "T4", at=0.38)
    f.dim((25, -HW), (25, HW), 0, "T5", at=0.86)
    for x, at in ((100, 0.3), (430, 0.5), (760, 0.7)):
        f.dim((x, -AG), (x, AG), 0, "W4", at=at)
    f.dim((0, -HW - 55), (AL, -HW - 55), 16, "W2 P")
    f.dim((0, HW + 55), (AL, HW + 55), -16, "W2 D")
    f.dim((600, HW), (600, AG), 0, "W6", at=0.5)
    f.call((0, AG + 40), "W1", -45, 28)
    f.call((P.ARCH_POCKET["x0"] + 80, -AG - 12), "W9", 30, 38)
    f.dim((0, -HW - 55), (P.FACTORY_OUTLET[0], -HW - 55), 40, "F1 X", at=0.8)
    f.call((P.FACTORY_OUTLET[0], -HW + 10), "F1", 40, -30)
    f.dim((TL + P.TAILGATE_T, -HW), (TL + P.TAILGATE_T, HW), -26, "T15", at=0.75)
    f.call((700, -300), "T10", 0, 0)
    f.call((1200, HW - 2), "F3", 30, -26)
    f.call((AL, AG - 2), "W8", 34, -26)
    f.note(60, 632, "X from the tub front wall (liner face) · Y from the centreline · all in mm · ribs shown at the assumed 100 mm pitch", 9)
    return f


def fig_side():
    f = Fig("d2-tub-side", "D2 · Tub, side section (looking at the passenger wall from the centre)", 760, 450, -230, -40, 0.355, ox=40, oy=425)
    f.rect(0, 0, TL, TD, "l")
    f.poly([(0, 0), (TL, 0)], "o", close=False)
    f.poly([(0, 0), (0, TD)], "o", close=False)
    f.rect(TL, 0, TL + P.TAILGATE_T, P.TAILGATE_H, "f")
    f.rect(0, 0, AL, AH, "h")
    a = P.ARCH_POCKET
    f.rect(a["x0"], a["z0"], a["x1"], a["z1"], "f")
    fo = P.FACTORY_OUTLET
    f.rect(fo[0] - 50, fo[2] - 40, fo[0] + 50, fo[2] + 40, "f")
    f.rect(P.LID_X0, UL, P.LID_X0 + P.LID_L, LT, "f")
    f.rect(P.LID_X0, LT, P.LID_X0 + P.LID_L, LT + P.LID_RAIL_H, "l")
    for bx in P.RACK_BAR_X:
        f.rect(bx - P.RACK_BAR[0] / 2, TZ - BAR_T, bx + P.RACK_BAR[0] / 2, TZ, "f")
        f.rect(bx - 30, LT + P.LID_RAIL_H, bx + 30, TZ - BAR_T, "l")
        f.line(bx - 20, TZ - BAR_T, bx - 20, TZ - BAR_T - P.TENT_BOLT_DROP, "o")
    f.rect(P.TENT_X0, TZ, P.TENT_X0 + P.TENT_L, TZ + P.TENT_BASE_H, "o")
    f.poly([(P.TENT_X0, TZ + P.TENT_BASE_H), (P.TENT_X0 + P.TENT_SLOPE_L, TZ + P.TENT_H), (P.TENT_X0 + P.TENT_L, TZ + P.TENT_H),
            (P.TENT_X0 + P.TENT_L, TZ + P.TENT_BASE_H)], "l", close=False)
    f.rect(-200, 0, P.CAB_REAR_X, 1000, "l")
    f.text(-150, 500, "CAB", 10, rot=-90)
    f.text(AL / 2, AH / 2, "arch", 10)
    f.text(1250, TZ + 270, "tent (closed)", 10, cls="n")
    f.text(1300, UL + 18, "Load-Lid", 9.5, cls="n")
    # dims
    for x, lab, at in ((100, "T6", 0.75), (1460, "T6", 0.45)):
        f.dim((x, 0), (x, TD), 0, lab, at=at)
    f.dim((AL - 60, 0), (AL - 60, AH), 0, "W3", at=0.35)
    f.dim((430, AH), (430, UL), 0, "W10")
    f.call((AL, AH / 2), "W8", 40, 0)
    f.call((a["x1"], a["z1"]), "W9", 36, -24)
    f.dim((fo[0] - 110, 0), (fo[0] - 110, fo[2]), 0, "F1 Z", at=0.3)
    f.call((fo[0] + 50, fo[2]), "F1", 30, -10)
    f.call((P.LID_X0, LT - 10), "L2", -36, -14)
    f.call((TL + 20, UL - 4), "L5", 46, 12)
    f.call((700, UL), "L6", 0, 38)
    f.dim((TL + P.LID_X0 + P.LID_L - TL, LT + 70), (TL + P.TAILGATE_T, LT + 70), 0, "L3", ext=False, at=0.6)
    f.dim((0, TZ + 110), (P.RACK_BAR_X[0], TZ + 110), 0, "R1", at=0.5)
    f.dim((0, TZ + 200), (P.RACK_BAR_X[1], TZ + 200), 0, "R1", at=0.6)
    bx = P.RACK_BAR_X[1]
    f.dim((bx + 70, LT), (bx + 70, TZ - BAR_T), 0, "R4", at=0.5)
    f.call((bx - 20, TZ - BAR_T - P.TENT_BOLT_DROP), "R7", -40, 22)
    f.dim((1300, LT), (1300, TZ), 0, "R8")
    f.call((P.TENT_X0, TZ + 25), "R9", -40, -18)
    f.dim((P.TENT_X0 + P.TENT_L + 40, TZ), (P.TENT_X0 + P.TENT_L + 40, TZ + P.TENT_H), 0, "R10", at=0.5)
    f.dim((P.CAB_REAR_X, 300), (0, 300), 0, "B1", ext=False)
    f.call((TL + P.TAILGATE_T / 2, 260), "T14", 40, 0)
    f.call((0, TD - 30), "T7", -36, 0)
    f.note(40, 462, "Z from the top of the floor ribs · X from the tub front wall · bar, bolt and tent positions are the model's guesses", 9)
    return f


def fig_cross():
    f = Fig("d3-tub-section", "D3 · Cross-section looking forward from the tailgate (driver side on the right)", 760, 560, -980, -260, 0.36, ox=24)
    # chassis rails under the floor
    for s in (1, -1):
        f.rect(s * P.CHASSIS_RAIL_Y - 30, P.CHASSIS_Z - 200, s * P.CHASSIS_RAIL_Y + 30, P.CHASSIS_Z, "f")
    f.line(-HW, -40, HW, -40, "l")
    f.poly([(-HW, TD), (-HW, 0), (HW, 0), (HW, TD)], "o", close=False)
    for s in (1, -1):
        r = P.ARCH_R
        pts = [(s * HW, 0), (s * AG, 0), (s * AG, AH - r)]
        for k in range(1, 7):
            t = math.pi / 2 * k / 6
            pts.append((s * (AG + r - r * math.cos(t)), AH - r + r * math.sin(t)))
        pts.append((s * HW, AH))
        f.poly(pts, "h")
        f.rect(s * HW, TD - 20, s * (HW + 60), TD, "f")
    for k in range(-5, 6):
        x = k * P.RIB_PITCH
        f.rect(x - P.RIB_W / 2, -P.RIB_H, x + P.RIB_W / 2, 0, "l")
    f.rect(-P.LID_W / 2, UL, P.LID_W / 2, LT, "f")
    for s in (1, -1):
        y = s * P.LID_RAIL_Y
        f.rect(y - P.LID_RAIL_W / 2, LT, y + P.LID_RAIL_W / 2, LT + P.LID_RAIL_H, "o")
        f.rect(y - 25, LT + P.LID_RAIL_H, y + 25, TZ - BAR_T, "l")
        u = s * P.TENT_UNDER_RAILS_CC / 2
        f.rect(u - 50, TZ - BAR_T - 6, u + 50, TZ - BAR_T, "f")
        f.line(u, TZ - BAR_T - 6, u, TZ - BAR_T - P.TENT_BOLT_DROP, "o")
        f.rect(u - 20, TZ, u + 20, TZ + 25, "f")
    f.rect(-P.RACK_BAR_L / 2, TZ - BAR_T, P.RACK_BAR_L / 2, TZ, "o")
    f.rect(-P.TENT_W / 2, TZ, P.TENT_W / 2, TZ + P.TENT_BASE_H, "o")
    f.rect(-P.TENT_W / 2, TZ + P.TENT_BASE_H, P.TENT_W / 2, TZ + P.TENT_H, "l")
    f.line(0, -230, 0, TZ + P.TENT_H + 30, "c")
    f.text(-HW + 20, 230, "PASSENGER", 9, anchor="start")
    f.text(HW - 20, 230, "DRIVER", 9, anchor="end")
    f.text(0, -190, "chassis rails", 9, cls="n")
    # dims
    f.dim((-HW, 15), (HW, 15), 0, "T3", at=0.35)
    f.dim((-HW, TD - 40), (HW, TD - 40), 0, "T3", at=0.35)
    f.dim((-AG, 60), (AG, 60), 0, "W4", at=0.65)
    f.dim((-AG, AH - 90), (AG, AH - 90), 0, "W5", at=0.65)
    f.dim((HW, AH + 25), (AG, AH + 25), 0, "W6", at=0.5)
    f.call((AG + 20, AH - 20), "W7", -40, -24)
    f.call((-HW - 30, TD - 10), "T13", -40, 26)
    f.call((-HW, TD - 160), "T8", -30, 0)
    f.call((200, -5), "T10", 30, 30)
    f.dim((-P.LID_W / 2, UL - 22), (P.LID_W / 2, UL - 22), 0, "L1", at=0.2, ext=False)
    f.dim((P.LID_W / 2 + 25, UL), (P.LID_W / 2 + 25, LT), 0, "L4", ext=False)
    f.dim((0, LT + 8), (P.LID_RAIL_Y, LT + 8), 0, "L10", at=0.3)
    f.call((P.LID_RAIL_Y + 22, LT + P.LID_RAIL_H), "L11", 40, -10)
    f.dim((-P.RACK_BAR_L / 2, TZ + P.TENT_H + 25), (P.RACK_BAR_L / 2, TZ + P.TENT_H + 25), 0, "R2", at=0.85, ext=False)
    f.call((-P.RACK_BAR_L / 2 + 20, TZ - 10), "R3", -24, -30)
    f.dim((-P.LID_RAIL_Y - 60, LT), (-P.LID_RAIL_Y - 60, TZ - BAR_T), 0, "R4", at=0.4)
    f.call((-P.LID_RAIL_Y, LT + P.LID_RAIL_H + 30), "R5", -40, -34)
    f.dim((-P.TENT_UNDER_RAILS_CC / 2, TZ + 120), (P.TENT_UNDER_RAILS_CC / 2, TZ + 120), 0, "R6", at=0.4, ext=False)
    f.call((P.TENT_UNDER_RAILS_CC / 2, TZ - BAR_T - P.TENT_BOLT_DROP), "R7", 40, -12)
    f.dim((-200, LT), (-200, TZ), 0, "R8", at=0.3)
    f.dim((P.TENT_W / 2, TZ + 60), (P.LID_W / 2, TZ + 60), 0, "R9", at=0.5, ext=True)
    f.dim((-P.CHASSIS_RAIL_Y, -230), (P.CHASSIS_RAIL_Y, -230), 0, "B6", at=0.25)
    f.dim((P.CHASSIS_RAIL_Y + 60, P.CHASSIS_Z), (P.CHASSIS_RAIL_Y + 60, 0), 0, "B6", at=0.5)
    return f


def fig_lid_plan():
    f = Fig("d4-lid-plan", "D4 · Load-Lid, bars and tent, plan view (from above)", 760, 680, -200, -960, 0.30, ox=60, oy=40 + 1920 * 0.30)
    f.rect(0, -HW, TL, HW, "l")
    f.rect(P.LID_X0, -P.LID_W / 2, P.LID_X0 + P.LID_L, P.LID_W / 2, "o")
    for s in (1, -1):
        y = s * P.LID_RAIL_Y
        f.rect(P.LID_X0 + 10, y - P.LID_RAIL_W / 2, P.LID_X0 + P.LID_L - 10, y + P.LID_RAIL_W / 2, "f")
    for bx in P.RACK_BAR_X:
        f.rect(bx - P.RACK_BAR[0] / 2, -P.RACK_BAR_L / 2, bx + P.RACK_BAR[0] / 2, P.RACK_BAR_L / 2, "f")
        for s in (1, -1):
            f.rect(bx - 60, s * P.LID_RAIL_Y - 35, bx + 60, s * P.LID_RAIL_Y + 35, "o")
            u = s * P.TENT_UNDER_RAILS_CC / 2
            f.circle(bx, u, 22, "o", fill="#fff")
    f.rect(P.TENT_X0, -P.TENT_W / 2, P.TENT_X0 + P.TENT_L, P.TENT_W / 2, "l")
    for s in (1, -1):
        u = s * P.TENT_UNDER_RAILS_CC / 2
        x0 = P.TENT_X0 + (P.TENT_L - 1440) / 2
        f.line(x0, u, x0 + 1440, u, "l")
    f.line(-180, 0, TL + 100, 0, "c")
    f.text(-140, 0, "FRONT", 10, rot=-90)
    f.text(800, P.LID_W / 2, "DRIVER (tent folds out this side)", 10, dy=-14)
    f.text(800, -P.LID_W / 2, "PASSENGER", 10, dy=26)
    f.text(560, 250, "tent outline (closed)", 9, cls="n")
    # dims
    f.dim((P.LID_X0, -P.LID_W / 2), (P.LID_X0 + P.LID_L, -P.LID_W / 2), 30, "L1", at=0.6)
    f.dim((P.LID_X0 + P.LID_L, -P.LID_W / 2), (P.LID_X0 + P.LID_L, P.LID_W / 2), 30, "L1", at=0.3)
    f.call((P.LID_X0, -P.LID_W / 2 + 120), "L2", -40, 0)
    f.dim((P.LID_X0, -560), (P.RACK_BAR_X[0], -560), 0, "R1", at=0.5)
    f.dim((P.LID_X0, -660), (P.RACK_BAR_X[1], -660), 0, "R1", at=0.7)
    f.dim((P.RACK_BAR_X[1] + 120, -P.RACK_BAR_L / 2), (P.RACK_BAR_X[1] + 120, P.RACK_BAR_L / 2), 0, "R2", at=0.9)
    f.call((P.RACK_BAR_X[0] + 60, P.LID_RAIL_Y + 35), "R5", 40, -18)
    f.dim((P.RACK_BAR_X[0] - 120, -P.TENT_UNDER_RAILS_CC / 2), (P.RACK_BAR_X[0] - 120, P.TENT_UNDER_RAILS_CC / 2), 0, "R6", at=0.5)
    for bx in P.RACK_BAR_X:
        for s in (1, -1):
            f.call((bx, s * P.TENT_UNDER_RAILS_CC / 2), "R7", 34, -s * 22)
    f.dim((P.LID_X0 + P.LID_L - 200, P.LID_RAIL_Y), (P.LID_X0 + P.LID_L - 200, 0), 0, "L10", at=0.5)
    f.call((P.TENT_X0, P.TENT_W / 2 - 60), "R9", 40, 14)
    f.call((P.TENT_X0 + P.TENT_L, -150), "R9", -40, 0)
    f.call((1300, P.TENT_W / 2), "R11", 30, -18)
    f.call((P.LID_X0 + 30, 300), "L7", -46, 0)
    f.call((P.LID_X0 + P.LID_L - 30, 300), "L7", 46, 0)
    f.call((P.LID_X0 + 300, -P.LID_W / 2 + 25), "L8", 30, -26)
    f.call((900, 0), "L12", 26, 20)
    return f


def fig_vehicle():
    s = 0.125
    f = Fig("d5-vehicle-side", "D5 · Vehicle side view (passenger side): heights from the ground, positions from the tub front wall", 760, 360,
            -3900, 0, s, ox=28, oy=330)
    G = P.FLOOR_ABOVE_GROUND
    ra, fa = P.REAR_AXLE_X, P.REAR_AXLE_X - P.WHEELBASE
    f.line(-3900, 0, 1900, 0, "o")
    for x in (ra, fa):
        f.circle(x, P.TYRE_D / 2, P.TYRE_D / 2, "o")
        f.circle(x, P.TYRE_D / 2, 30, "o")
    f.rect(0, G - 40, TL, G + TD, "o")
    f.rect(TL, G - 40, TL + 60, G + TD - 15, "f")
    cr, hx = P.CAB_REAR_X, P.CAB_FRONT_X
    roof = P.ROOF_Z + G
    bon_x, bon_z = hx - 820, G + 330
    f.poly([(cr, G - 60), (cr, roof - 40), (cr - 60, roof), (hx, roof), (bon_x, bon_z), (-3800, G + 230), (-3850, G - 200),
            (fa + 500, G - 200), (cr, G - 60)], "o")
    f.line(hx, roof, bon_x, bon_z, "o")
    f.rect(P.PLAT_X0, P.PLAT_Z + G, P.PLAT_X0 + P.PLAT_L, P.PLAT_Z + G + P.PLAT_T, "f")
    f.rect(P.LID_X0, UL + G, P.LID_X0 + P.LID_L, LT + G, "f")
    f.rect(P.TENT_X0, TZ + G, P.TENT_X0 + P.TENT_L, TZ + G + P.TENT_H, "l")
    f.text(700, TZ + G + 160, "tent", 9.5, cls="n")
    f.text(-1050, G + 300, "cab", 10)
    # dims
    f.dim((TL + 120, 0), (TL + 120, G + TD), 0, "B3", at=0.5)
    f.dim((-60, 0), (-60, G + TD), 0, "B3", at=0.35)
    f.dim((0, 60), (ra, 60), 0, "B4", ext=True, at=0.5)
    f.dim((fa, 140), (ra, 140), 0, "B5", at=0.3)
    f.call((cr / 2, G + 420), "B1", 20, -30)
    for x, at in ((hx + 200, 0.6), ((hx + cr) / 2, 0.7), (cr - 100, 0.8)):
        f.dim((x, 0), (x, roof), 0, "G3", at=at)
    f.dim((hx, roof + 260), (0, roof + 260), 0, "G1", at=0.6)
    f.dim((hx, roof + 180), (cr, roof + 180), 0, "G2", at=0.4, ext=False)
    f.call(((hx + bon_x) / 2, (roof + bon_z) / 2), "G9", -50, -8)
    f.call(((hx + bon_x) / 2 + 80, (roof + bon_z) / 2 - 60), "G10", 30, 26)
    f.call((bon_x, bon_z), "G11", -30, 30)
    f.dim((bon_x - 100, 0), (bon_x - 100, bon_z), 0, "G11", at=0.7)
    f.call((P.PLAT_X0 + 80, P.PLAT_Z + G), "G12", -36, 20)
    f.dim((TL + 220, 0), (TL + 220, TZ + G + P.TENT_H), 0, "G13", at=0.8)
    f.call((P.TENT_X0, TZ + G + 30), "R13", -36, -30)
    f.call((TL + 60, G + 200), "T16", 40, -10)
    f.note(28, 354, "Park on level ground, normal tyre pressures, unladen. Use a plumb line or level to transfer points to the ground.", 9)
    return f


def fig_roof():
    f = Fig("d6-roof-crown", "D6 · Roof crown: straight edge across the roof (repeat at the front, middle and rear)", 760, 300, -900, -80, 0.40,
            ox=20, oy=210)
    w = 680
    pts = [(-w - 40, -40)]
    for k in range(-20, 21):
        y = k * w / 20
        pts.append((y, 30 * math.cos(y / w * math.pi / 2) - 0))
    pts.append((w + 40, -40))
    f.poly(pts, "o", close=False)
    f.line(-w - 60, 40, w + 60, 40, "o")
    f.text(0, 55, "straight edge (aluminium level) resting on the rail feet / highest points", 9.5)
    for y, lab in ((0, "0"), (350, "±350"), (560, "±560"), (700, "±700")):
        for s in ((1, -1) if y else (1,)):
            yy = s * min(y, w - 5)
            f.line(yy, 30 * math.cos(yy / w * math.pi / 2), yy, 40, "dim")
        f.text(y if y else 0, -25, lab, 9, cls="n")
    f.call((0, 35), "G4", 0, -50)
    f.dim((-w, -40), (w, -40), 26, "G5", at=0.7, ext=False)
    for y in (-520, 520):
        f.circle(y, 28, 18, "f")
    f.call((520, 28), "G6", 40, 30)
    f.call((-w, 0), "G7", -10, 40)
    f.call((-300, 25), "G8", 0, 34)
    f.note(20, 290, "Measure the gap from the straight edge down to the roof skin at each mark, both sides. Rear view; driver side on the right.", 9)
    return f


def fig_details():
    """Six small detail views on one sheet (not to scale)."""
    f = Fig("d7-details", "D7 · Details (not to scale)", 760, 520, 0, 0, 1, ox=0, oy=0)
    box = lambda x, y, t: (f.raw(f'<rect x="{x}" y="{y}" width="240" height="235" rx="6" fill="none" stroke="#ced4da"/>'),  # noqa: E731
                           f.raw(f'<text x="{x + 10}" y="{y + 18}" font-size="11" font-weight="700" fill="#343a40">{escape(t)}</text>'))
    R = lambda *a: f.raw('<rect x="{}" y="{}" width="{}" height="{}" class="{}"/>'.format(*a))  # noqa: E731
    L = lambda x1, y1, x2, y2, c="o": f.raw(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{c}"/>')  # noqa: E731

    def D(x1, y1, x2, y2, lab, at=0.5):
        f.raw(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="dim" marker-start="url(#ar)" marker-end="url(#ar)"/>')
        f.bubble(x1 + (x2 - x1) * at, y1 + (y2 - y1) * at, lab)

    # (a) floor ribs
    box(5, 5, "a · Floor ribs (T10)")
    L(20, 170, 230, 170)
    for k in range(3):
        x = 35 + k * 70
        f.raw(f'<polygon points="{x},170 {x + 6},140 {x + 34},140 {x + 40},170" class="f"/>')
    D(35, 190, 105, 190, "pitch")
    D(41, 128, 69, 128, "top w")
    D(150, 140, 150, 170, "h", 0.5)
    f.note(15, 225, "rib height · top width · pitch · count", 9)
    # (b) Destroyer rail
    box(260, 5, "b · Destroyer rail + T-slot (L10, L11)")
    f.raw('<path d="M300,190 L300,80 L330,80 L330,95 L340,95 L340,80 L370,80 L370,190 Z" class="f"/>')
    f.raw('<path d="M318,95 L352,95 L352,112 L318,112 Z" fill="#fff" stroke="#495057"/>')
    L(280, 190, 480, 190)
    D(395, 80, 395, 190, "h")
    D(300, 205, 370, 205, "w")
    D(330, 70, 340, 70, "open", 0.5)
    D(445, 95, 445, 112, "slot")
    f.note(270, 232, "height · width · slot opening · slot depth · inner width", 9)
    # (c) tent bolt crossing
    box(515, 5, "c · Tent bolt at each bar (R7)")
    R(535, 60, 200, 30, "f")
    R(600, 90, 70, 8, "f")
    L(635, 98, 635, 170)
    R(625, 158, 20, 12, "f")
    f.raw('<line x1="690" y1="90" x2="690" y2="170" class="dim" marker-start="url(#ar)" marker-end="url(#ar)"/>')
    f.bubble(705, 130, "drop")
    D(600, 112, 670, 112, "plate", 0.5)
    f.note(530, 200, "Vortex bar · clamp plate · bolt + nut", 9)
    f.note(530, 225, "measure bar underside → lowest point", 9)
    # (d) factory outlet
    box(5, 255, "d · Factory 240 V outlet (F1, F2)")
    R(60, 300, 120, 100, "f")
    R(95, 325, 50, 50, "o")
    D(60, 415, 180, 415, "W")
    D(45, 300, 45, 400, "H")
    f.raw('<path d="M200,300 L215,300 L215,400 L200,400" class="o"/>')
    D(200, 290, 215, 290, "proud")
    f.note(15, 480, "housing W × H · how far it stands proud", 9)
    # (e) arch well
    box(260, 255, "e · Arch well (W9)")
    R(285, 290, 190, 140, "h")
    R(330, 330, 100, 50, "f")
    D(330, 395, 430, 395, "x0 → x1")
    D(450, 330, 450, 380, "z0 → z1")
    f.note(270, 455, "X of front/rear edge from the front wall,", 9)
    f.note(270, 470, "Z of bottom/top above the floor, depth, radius", 9)
    # (f) liner edge
    box(515, 255, "f · Liner and rail cap (T11, T13)")
    f.raw('<path d="M560,300 L700,300 L700,315 L585,315 L585,450 L560,450 Z" class="f"/>')
    f.raw('<path d="M585,315 L593,315 L593,450 L585,450 Z" fill="#868e96"/>')
    D(560, 290, 700, 290, "cap w")
    D(585, 465, 593, 465, "liner", 0.5)
    D(712, 300, 712, 315, "lip", 0.5)
    f.note(525, 485, "cap width · lip overhang · liner thickness", 9)
    return f


def fig_datums():
    f = Fig("d0-datums", "D0 · Reference lines (datums) used on every sheet", 760, 230, 0, 0, 1, ox=0, oy=0)
    f.raw('<rect x="40" y="40" width="300" height="150" fill="#f8f9fa" stroke="#212529" stroke-width="1.5"/>')
    f.raw('<line x1="40" y1="115" x2="340" y2="115" class="c"/>')
    f.raw('<line x1="40" y1="40" x2="40" y2="190" stroke="#c92a2a" stroke-width="3"/>')
    f.note(48, 58, "X = 0: inner face of the tub front wall", 10)
    f.note(48, 108, "Y = 0: centreline (tape line)", 10)
    f.raw('<line x1="60" y1="150" x2="140" y2="150" class="dim" marker-end="url(#ar)"/>')
    f.note(150, 154, "+X towards the tailgate", 10)
    f.raw('<line x1="300" y1="115" x2="300" y2="60" class="dim" marker-end="url(#ar)"/>')
    f.note(250, 82, "+Y driver", 10)
    f.note(190, 210, "plan view, front of the vehicle on the left", 9, anchor="middle")
    f.raw('<rect x="420" y="80" width="300" height="110" fill="#f8f9fa" stroke="#212529" stroke-width="1.5"/>')
    for k in range(6):
        x = 440 + k * 50
        f.raw(f'<rect x="{x}" y="182" width="22" height="8" fill="#ced4da" stroke="#495057"/>')
    f.raw('<line x1="420" y1="182" x2="720" y2="182" stroke="#c92a2a" stroke-width="3"/>')
    f.note(430, 175, "Z = 0: top of the floor ribs", 10)
    f.raw('<line x1="700" y1="175" x2="700" y2="100" class="dim" marker-end="url(#ar)"/>')
    f.note(690, 120, "+Z up", 10, anchor="end")
    f.note(570, 210, "side view", 9, anchor="middle")
    return f


FIGS = {f.key: f for f in (fig_datums(), fig_plan(), fig_side(), fig_cross(), fig_lid_plan(), fig_vehicle(), fig_roof(), fig_details())}

# ============================================================================ the measurements
# (id, what, how / where, model assumes, param, boxes, stage)  boxes: list of box labels, or ("notes", lines)
FB = ["Front", "Mid", "Rear"]
DP = ["Driver", "Passenger"]
N = lambda k=2: ("notes", k)  # noqa: E731
r0 = lambda v: f"{v:g}"  # noqa: E731

SECTIONS = [
    ("1", "Tub: floor, walls and tailgate", ["d1-tub-plan", "d3-tub-section"], [
        ("T1", "Floor length on the centreline", "Front wall liner face → inside face of the closed tailgate, at rib-top height", r0(TL), "TUB_L", ["mm"], "1 3"),
        ("T2", "Floor length beside the arches", "Rear end of each arch → tailgate inside face, 50 mm in from the side wall", r0(TL - AL), "TL − ARCH_L", DP, "3"),
        ("T3", "Width wall to wall behind the arches", "Liner face to liner face at X ≈ 1000: at floor, at 270 high, and just below the rail", r0(TW), "TUB_W",
         ["Floor", "270 high", "Rail"], "1 3"),
        ("T4", "Width wall to wall at the tailgate", "Same, at X ≈ 1460", r0(TW), "TUB_W", ["Floor", "Rail"], "3"),
        ("T5", "Width above the arches at the front", "Wall to wall at X ≈ 50, just above arch height and at rail height", r0(TW), "TUB_W", ["Above arch", "Rail"], "1"),
        ("T6", "Tub depth", "Rib top → top of the tub rail (inside edge), at each corner", r0(TD), "TUB_D",
         ["Front D", "Front P", "Rear D", "Rear P"], "1 3"),
        ("T7", "Front wall lean", "Level held vertical against the front wall: gap at rail height (+ = wall leans back)", "0", "-", ["mm"], "1"),
        ("T8", "Side wall lean", "Same on each side wall behind the arch (+ = tub wider at the top)", "0", "-", DP, "3"),
        ("T9", "Corner radii", "Floor-to-wall radius, and the radius in the front corners (vertical)", "–", "-", ["Floor/wall", "Front corners"], "1 3"),
        ("T10", "Floor ribs (detail a)", "Rib height above the valleys, rib top width, pitch, how many, Y of the middle rib, X where they start and end",
         f"{r0(P.RIB_H)} / {r0(P.RIB_W)} / {r0(P.RIB_PITCH)}", "RIB_H, RIB_W, RIB_PITCH",
         ["Height", "Top width", "Pitch", "Count", "Mid rib Y", "Start X", "End X"], "1 3"),
        ("T11", "Liner thickness (detail f)", "Calipers on an exposed liner edge (rail lip or tailgate gap)", r0(P.LINER_ALLOW), "LINER_ALLOW", ["mm"], "3"),
        ("T12", "Liner type", "Drop-in or spray-in? How is it fixed? Can it come out to bolt through the floor?", "drop-in", "-", N(2), "1"),
        ("T13", "Tub rail cap (detail f)", "Width of the rail's flat top, how far its inside lip overhangs the wall, lip depth", "–", "-",
         ["Cap width", "Lip overhang", "Lip depth"], "3"),
        ("T14", "Tailgate inner panel", "Thickness inside face → outer skin at mid-height; note any handles or bulges facing the tub", r0(P.TAILGATE_T), "TAILGATE_T",
         ["Thickness", "Bulges?"], "3"),
        ("T15", "Tailgate opening", "Clear width between the latch pillars at the floor and at the top; height of the closed tailgate top above the floor",
         f"– / {r0(P.TAILGATE_H)}", "TAILGATE_H", ["Width floor", "Width top", "Height"], "3"),
        ("T16", "Tailgate open", "Tailgate down: its top surface vs the tub floor (+ above / − below), its length from the hinge, the cable stay rating",
         "–", "-", ["Height diff", "Length", "Rating kg"], "3"),
        ("T17", "Holes in the floor", "X, Y of any drain holes or existing bolt holes (lift the liner if it's drop-in)", "–", "-", N(2), "1"),
    ]),
    ("2", "Wheel arches", ["d1-tub-plan", "d2-tub-side", "d3-tub-section"], [
        ("W1", "Arch start", "Gap from the front wall to the front of each arch at the floor and at the top (0 if they meet)", "0", "-",
         ["D floor", "D top", "P floor", "P top"], "1"),
        ("W2", "Arch length", "Front → rear end of each arch along its inner face, at the floor and at the top", r0(AL), "ARCH_L",
         ["D floor", "D top", "P floor", "P top"], "1 3"),
        ("W3", "Arch height", "Rib top → top of each arch at the front, middle and rear of its flat top", r0(AH), "ARCH_H",
         ["D front", "D mid", "D rear", "P front", "P mid", "P rear"], "1 3"),
        ("W4", "Width between the arches (floor)", "Arch face to arch face just above the floor at X ≈ 100, 430, 760", r0(P.ARCH_GAP), "ARCH_GAP", FB, "1 3"),
        ("W5", "Width between the arches (top)", "Same three positions, just below the top radius", r0(P.ARCH_GAP), "ARCH_GAP", FB, "1 3"),
        ("W6", "Arch intrusion", "Side wall face → arch inner face at mid-length", r0(P.ARCH_IN), "ARCH_IN", DP, "3"),
        ("W7", "Arch top shape", "Flat width of the top (wall → start of the radius) and the radius on its inboard edge", f"– / {r0(P.ARCH_R)}", "ARCH_R",
         ["D flat", "D radius", "P flat", "P radius"], "3"),
        ("W8", "Arch rear end", "Vertical, sloped or curved? How far the top's rear edge sits forward of the floor's rear edge", "vertical", "-",
         ["Driver", "Passenger"], "3"),
        ("W9", "Arch well (detail e)", "The recess in each arch face: X of its front and rear edges, Z of its bottom and top, depth",
         f"{P.ARCH_POCKET['x0']}–{P.ARCH_POCKET['x1']} / {P.ARCH_POCKET['z0']}–{P.ARCH_POCKET['z1']} / {P.ARCH_POCKET['depth']}", "ARCH_POCKET",
         ["D x0", "D x1", "D z0", "D z1", "D depth", "P x0", "P x1", "P z0", "P z1", "P depth"], "3"),
        ("W10", "Space above the arch", "Arch top → underside of the closed Load-Lid (lowest part of its frame), front and rear of each arch",
         r0(UL - AH), "UNDER_LID_Z − ARCH_H", ["D front", "D rear", "P front", "P rear"], "3"),
    ]),
    ("3", "Factory fittings in the tub", ["d1-tub-plan", "d2-tub-side", "d7-details"], [
        ("F1", "Factory 240 V outlet (detail d)", "Centre X from the front wall, centre Z above the floor, housing width × height, how far it stands proud",
         f"{P.FACTORY_OUTLET[0]} / {P.FACTORY_OUTLET[2]}", "FACTORY_OUTLET", ["X", "Z", "W", "H", "Proud"], "1"),
        ("F2", "Behind the outlet", "With the outlet removed: hole size in the steel, cavity depth behind (model: 49 mm between liner and skin), "
         "and the way out at the cavity bottom for a 50 mm and a 25 mm conduit (routes R14 / R15, sheet E12)",
         "– / 49", "-", ["Hole W", "Hole H", "Cavity", "Exit"], "1"),
        ("F3", "Tie-down points", "Every tie-down or rail: wall, X, Z, type and how far it stands proud", "none on the arches", "-", N(3), "1 3"),
        ("F4", "Other protrusions", "Bolt heads, cleats, liner bosses, light: position and how far they stand proud", "–", "-", N(2), "3"),
    ]),
    ("4", "Load-Lid and Destroyer rails", ["d2-tub-side", "d3-tub-section", "d4-lid-plan"], [
        ("L1", "Lid size", "Overall length (along) and width (across) including edge trims", f"{r0(P.LID_L)} × {r0(P.LID_W)}", "LID_L, LID_W",
         ["Length", "Width"], "6"),
        ("L2", "Lid front edge", "Lid front edge relative to the tub front wall face (− = ahead of the wall)", r0(P.LID_X0), "LID_X0", ["mm"], "6"),
        ("L3", "Lid rear edge", "Lid rear edge relative to the closed tailgate's outer face (+ = overhangs)", "–", "-", ["mm"], "6"),
        ("L4", "Lid thickness", "Top skin → lowest part of its perimeter frame", r0(P.LID_T), "LID_T", ["mm"], "3 6"),
        ("L5", "Gap rail → lid", "Tub rail top → lid underside at the four corners", r0(P.LID_CLEAR), "LID_CLEAR", ["FD", "FP", "RD", "RP"], "3"),
        ("L6", "Lid frame inside the tub", "Anything below the tub rail level (cross members, brackets, seals): what, X position, how far down",
         "nothing", "UNDER_LID_Z", ["Max drop"] + [""] * 0, "3"),
        ("L7", "Hinges and lock", "Hinge type and positions; lock/latch positions and how far they reach into the tub", "–", "-", N(2), "3"),
        ("L8", "Gas struts", "Both ends of each strut: on the lid / on the body, X, Y, Z. Inside the tub?", "not in the tub", "-", N(2), "3"),
        ("L9", "Lid clamps", "How the lid bolts to the tub; clamp positions and how far they stick inside the tub walls", "–", "-", N(2), "3"),
        ("L10", "Destroyer rails (detail b)", "Height above the lid top, width, length, X of the front and rear ends, Y of the rail centre from the centreline",
         f"{r0(P.LID_RAIL_H)} / {r0(P.LID_RAIL_W)} / – / {r0(P.LID_RAIL_Y)}", "LID_RAIL_H, LID_RAIL_W, LID_RAIL_Y",
         ["Height", "Width", "Length", "Front X", "Rear X", "Y"], "6"),
        ("L11", "Rail T-slot (detail b)", "Slot opening, slot depth, inner width, lip thickness; T-bolt size used", "–", "-",
         ["Opening", "Depth", "Inner w", "Lip", "Bolt"], "6"),
        ("L12", "Lid top surface", "Chequer pattern height; flat or crowned (straight edge across: gap at the centre)", "flat", "-", ["Pattern", "Crown"], "6"),
    ]),
    ("5", "Rack bars and tent", ["d2-tub-side", "d3-tub-section", "d4-lid-plan", "d7-details"], [
        ("R1", "Bar positions", "Centre line of each Vortex bar from the lid front edge (or from the tub front wall, say which)",
         " / ".join(r0(x) for x in P.RACK_BAR_X) + " (from tub wall)", "RACK_BAR_X", ["Front bar", "Rear bar", "Datum"], "6"),
        ("R2", "Bar length and overhang", "Overall length; overhang past each leg", r0(P.RACK_BAR_L), "RACK_BAR_L", ["Length", "D overhang", "P overhang"], "6"),
        ("R3", "Bar section", "Width × height of the bar; top slot width", f"{P.RACK_BAR[0]} × {P.RACK_BAR[1]}", "RACK_BAR", ["W", "H", "Slot"], "6"),
        ("R4", "Bar height", "Lid top → underside of each bar beside each leg", r0(TZ - BAR_T - LT), "TENT_GAP − bar",
         ["Front D", "Front P", "Rear D", "Rear P"], "6"),
        ("R5", "Legs / brackets", "Footprint on the rail (along × across), leg height, part number", "–", "-", ["Footprint", "Height", "Part no."], "6"),
        ("R6", "Tent under-rails", "Y of each under-rail centre from the centreline; X of the rail ends", f"±{r0(P.TENT_UNDER_RAILS_CC / 2)}",
         "TENT_UNDER_RAILS_CC", ["D Y", "P Y", "Front X", "Rear X"], "6"),
        ("R7", "Tent bolt tails (detail c)", "At each of the 4 crossings: bar underside → lowest point of bolt, nut or plate; plate size; bolt size",
         r0(P.TENT_BOLT_DROP), "TENT_BOLT_DROP", ["Front D", "Front P", "Rear D", "Rear P", "Plate", "Bolt"], "6"),
        ("R8", "Gap lid → tent", "Lid top → lowest part of the tent base at the front, middle and rear, both sides", r0(P.TENT_GAP), "TENT_GAP",
         ["Front D", "Front P", "Mid D", "Mid P", "Rear D", "Rear P"], "6"),
        ("R9", "Tent position", "Tent front and rear edges from the lid front edge; overhang past the lid edge each side", r0(P.TENT_X0), "TENT_X0",
         ["Front", "Rear", "D overhang", "P overhang"], "6"),
        ("R10", "Tent shape", "Closed height (base → top of the roof bars), length of the front slope, top-bar spacing and length",
         f"{r0(P.TENT_H)} / {r0(P.TENT_SLOPE_L)} / {r0(P.TENT_BAR_CC)} / {r0(P.TENT_BAR_L)}", "TENT_H, TENT_SLOPE_L, TENT_BAR_CC, TENT_BAR_L",
         ["Height", "Slope", "Bar c/c", "Bar length"], "5"),
        ("R11", "Ladder bracket", "Where it is and how far it sticks out or down", "–", "-", N(1), "6"),
        ("R12", "Tent open", "How far the open tent reaches past the driver side; floor height when open", "–", "-", ["Reach", "Floor height"], "-"),
        ("R13", "Tent to cab", "Tent front face → cab rear at tent-base height", "–", "-", ["mm"], "4"),
    ]),
    ("6", "Body, cab gap and chassis", ["d5-vehicle-side", "d3-tub-section"], [
        ("B1", "Cab–tub gap", "Cab back wall → tub front wall at the top, middle and bottom", r0(-P.CAB_REAR_X - 55), "CAB_REAR_X", ["Top", "Mid", "Bottom"], "1 4"),
        ("B2", "In the gap", "Body mounts, hoses, lines, wiring. Free space near the passenger top corner for a ~150 × 150 × 90 junction box?",
         "–", "-", ["Free W", "Free H", "Free D"], "4"),
        ("B3", "Tub height", "Ground → top of the tub rail at the tailgate and at the front corner (the floor is this minus T6)",
         r0(P.FLOOR_ABOVE_GROUND + TD), "FLOOR_ABOVE_GROUND", ["Rear", "Front"], "1"),
        ("B4", "Rear wheel centre", "Plumb from the tub front edge and from the wheel centre; distance along the ground", r0(P.REAR_AXLE_X), "REAR_AXLE_X", DP, "1"),
        ("B5", "Wheelbase check", "Front → rear wheel centres", r0(P.WHEELBASE), "WHEELBASE", DP, "-"),
        ("B6", "Chassis rails", "Centre Y of each rail; top of the rail below the tub floor; rail width × height",
         f"±{r0(P.CHASSIS_RAIL_Y)} / {r0(P.CHASSIS_Z)}", "CHASSIS_RAIL_Y, CHASSIS_Z", ["D Y", "P Y", "Top Z", "W", "H"], "1"),
        ("B7", "Cable route", "Outlet → passenger chassis rail → cab gap: obstacles, existing clips and holes", "–", "-", N(2), "1"),
        ("B8", "Tub underside", "Cross-member positions (X) under the tub floor, in case anything bolts through", "–", "-", N(1), "1"),
    ]),
    ("7", "Roof, windscreen and platform", ["d5-vehicle-side", "d6-roof-crown"], [
        ("G1", "Header to tub", "Horizontal: top of the windscreen (header seal) → tub front wall (plumb line from the header)", r0(-P.CAB_FRONT_X),
         "CAB_FRONT_X", ["mm"], "2 7"),
        ("G2", "Roof length", "Header → rear edge of the roof skin", r0(P.CAB_REAR_X - P.CAB_FRONT_X), "-", ["mm"], "2"),
        ("G3", "Roof height", "Ground → roof skin on the centreline, 200 mm behind the header, middle, 100 mm from the rear",
         r0(P.ROOF_Z + P.FLOOR_ABOVE_GROUND), "ROOF_Z", FB, "2 7"),
        ("G4", "Roof crown (D6)", "Straight edge across the roof: gap to the skin at each mark. Rows: front / mid / rear", "flat", "-",
         ("grid", FB, ["P 700", "P 560", "P 350", "0", "D 350", "D 560", "D 700"]), "2 7"),
        ("G5", "Roof width", "Skin width between the drip channels at the front, middle, rear", "–", "-", FB, "2"),
        ("G6", "Roof mounting points", "How many; X (from the header) and Y of each; thread; cover type", "–", "-", N(2), "2"),
        ("G7", "Roof rails", "Height, foot positions; do they come off for the Wedgetail kit?", "–", "-", N(1), "2"),
        ("G8", "Roof items", "Shark-fin antenna position and height; anything else on the roof", "–", "-", N(1), "2 7"),
        ("G9", "Windscreen angle", "Angle finder flat on the glass at the centre, from horizontal", "–", "-", ["degrees"], "7"),
        ("G10", "Windscreen size", "Length along the glass (header → bottom edge, centre) and width at the top", "–", "-", ["Length", "Width"], "7"),
        ("G11", "Bonnet rear edge", "Height above ground and horizontal distance from the header at the centre; top of the parked wipers", "–", "-",
         ["Height", "From header", "Wipers"], "7"),
        ("G12", "Platform (once fitted)", "Platform underside above the roof skin at the front and rear; front edge vs the header",
         f"{r0(P.PLAT_Z - P.ROOF_Z)}", "PLAT_Z", ["Front", "Rear", "Front edge"], "2 7"),
        ("G13", "Overall height", "Ground → top of the closed tent; ground → top of the platform", r0(round(TZ + P.TENT_H + P.FLOOR_ABOVE_GROUND)), "-",
         ["Tent", "Platform"], "-"),
        ("G14", "Headlining and roof cables", "How far the headlining drops to reach the roof points; path for a cable roof → cab (which pillar?)", "–", "-",
         N(2), "2"),
    ]),
    ("8", "Engine bay and cabin", [], [
        ("E1", "Start battery", "Type and size; terminal type; room for a MIDI fuse holder within 300 mm of the + terminal", "–", "-", N(2), "1"),
        ("E2", "Fuse box", "Location; fuse type (mini / micro2) for the add-a-fuse; an ignition-switched circuit to tap", "–", "-", N(2), "1"),
        ("E3", "Alternator", "Rated current on its label (amps)", "unknown", "-", ["Amps"], "1"),
        ("E4", "Engine bay → chassis", "Path for the 25 mm² twin from the start battery to the passenger chassis rail (R21); exhaust distance along the rail (R17–R19)", "–", "-", N(2), "1"),
        ("E5", "Under the rear seat", "Space for the cabin outlet box: length × width × height, what's there now", "45 L", "CABIN_SEAT_BOX",
         ["L", "W", "H"], "5"),
        ("E6", "Cab floor grommets", "Existing grommets that could take the cabin feed from the chassis rail (R20)", "–", "-", N(1), "5"),
        ("E8", "Cab back (C-pillar corner)", "Flat face up the passenger corner of the cab back for the 32 mm conduit (R25), and the gap between the cab top and the platform rear member", "–", "-", ["Width", "Gap"], "2"),
        ("E9", "Chassis rail web", "Height of the passenger rail web and the free length for the two conduits from the tub to the cab-tub gap (R16 / R17)", "180 / –", "-", ["Web H", "Free L"], "1"),
        ("E7", "Dash switch blanks", "Free switch blanks on the dash (optional visor stow switch)", "–", "-", N(1), "7"),
    ]),
    ("9", "Equipment and vehicle details", [], [
        ("Q1", "Fridge", "Confirmed Dometic CFX3 45 (694 × 398 × 476): check the handle height and that the handles fold up for the straps", "CFX3 45", "-",
         ["Model", "L", "W", "H", "Lid"], "3"),
        ("Q2", "Accessories fitted", "Tow bar (ball weight), bull bar, side steps, snorkel, anything else", "–", "-", N(2), "-"),
        ("Q3", "Compliance plate", "GVM, GCM, rear axle rating", "GVM 3250", "-", ["GVM", "GCM", "Rear axle"], "-"),
        ("Q4", "Weighbridge (optional)", "Front and rear axle weights, unladen, full fuel", "–", "-", ["Front", "Rear"], "-"),
        ("Q5", "Tyres", "Size and pressures", "265/70R17", "-", ["Size", "Pressures"], "-"),
    ]),
]

PHOTOS = ["Whole tub from the tailgate, from each rear corner and from above (lid open)",
          "Each arch: side on, with a tape along it; close-up of each arch well with a rule in it",
          "Front wall and both front corners; the floor ribs with a rule across them",
          "Factory outlet: on, and removed showing the hole and what's behind",
          "Every tie-down and protrusion with a rule beside it",
          "Under the lid: hinges, lock, struts, clamps, any frame members",
          "Destroyer rail end-on (T-slot profile) with calipers",
          "Each of the 4 tent-bolt crossings from the side, with a rule from the bar to the lowest point",
          "Cab–tub gap from above and below; chassis rail beside the gap",
          "Roof: straight edge across with the gaps visible; the roof mounting points uncovered",
          "Side profile of the windscreen and bonnet with a level for reference",
          "Engine bay: start battery, fuse box, route to the chassis; under the rear seat"]


# ============================================================================ output
CSS = """
@page { size: A4 portrait; margin: 11mm 11mm 13mm; }
* { box-sizing: border-box; }
body { font-family: Inter, 'Segoe UI', Arial, sans-serif; color: #212529; font-size: 9pt; margin: 0; }
h1 { font-size: 20pt; margin: 0 0 2mm; } h2 { font-size: 13pt; margin: 0 0 2mm; border-bottom: 2px solid #212529; padding-bottom: 1mm; }
h3 { font-size: 10.5pt; margin: 3mm 0 1mm; }
.page { page-break-after: always; } .page:last-child { page-break-after: auto; }
.fig { margin: 0 0 3mm; page-break-inside: avoid; } .fig .cap { font-weight: 700; font-size: 9.5pt; margin: 0 0 1mm; }
table.m { width: 100%; border-collapse: collapse; margin-top: 2mm; }
table.m th { background: #212529; color: #fff; text-align: left; padding: 1.2mm 1.5mm; font-size: 8pt; }
table.m td { border-bottom: 1px solid #ced4da; padding: 1.5mm; vertical-align: top; }
table.m tr { page-break-inside: avoid; }
.id { font-weight: 800; color: #c92a2a; white-space: nowrap; width: 9mm; }
.what { width: 52mm; } .what b { display: block; font-size: 9pt; } .what span { color: #495057; font-size: 8pt; }
.model { width: 18mm; color: #495057; font-size: 8pt; } .model code { display:block; font-size: 6.5pt; color: #868e96; word-break: break-all; }
.boxes { display: flex; flex-wrap: wrap; gap: 1.2mm; }
.bx { width: 17mm; } .bx i { display: block; font-style: normal; font-size: 6.5pt; color: #6c757d; height: 2.6mm; }
.bx div { height: 7.5mm; border: 1px solid #495057; border-radius: 1mm; }
.notes div { height: 7mm; border-bottom: 1px dotted #868e96; width: 100%; }
.grid td, .grid th { border: 1px solid #495057; height: 7mm; width: 12mm; font-size: 7pt; text-align: center; padding: 0 1mm; }
.grid th { background: #f1f3f5; color: #212529; }
.st { width: 9mm; text-align: center; font-size: 8pt; color: #495057; }
.ph { width: 6mm; text-align: center; } .ph div { width: 4mm; height: 4mm; border: 1px solid #495057; margin: 1mm auto 0; }
.intro p, .intro li { font-size: 9.5pt; line-height: 1.45; } .intro ul { margin: 1mm 0 2mm 5mm; padding: 0; }
.cols { display: flex; gap: 6mm; } .cols > div { flex: 1; }
.foot { font-size: 7.5pt; color: #868e96; margin-top: 2mm; }
.chk li { list-style: none; margin: 0 0 1.6mm; } .chk li::before { content: ""; display: inline-block; width: 3.5mm; height: 3.5mm;
  border: 1px solid #495057; margin-right: 2mm; vertical-align: -0.6mm; }
.lines div { height: 8mm; border-bottom: 1px solid #ced4da; }
"""


def boxes_html(b):
    if isinstance(b, tuple) and b[0] == "notes":
        return '<div class="notes">' + "<div></div>" * b[1] + "</div>"
    if isinstance(b, tuple) and b[0] == "grid":
        _, rows, cols = b
        h = '<table class="grid"><tr><th></th>' + "".join(f"<th>{escape(c)}</th>" for c in cols) + "</tr>"
        for r in rows:
            h += f"<tr><th>{escape(r)}</th>" + "<td></td>" * len(cols) + "</tr>"
        return h + "</table>"
    return '<div class="boxes">' + "".join(f'<div class="bx"><i>{escape(x)}</i><div></div></div>' for x in b) + "</div>"


def table_html(items):
    h = ['<table class="m"><tr><th>ID</th><th>Measure</th><th>Model now</th><th>Your values (mm unless noted)</th><th>Stage</th><th>📷</th></tr>']
    for iid, what, how, model, param, b, st in items:
        pm = f"<code>{escape(param)}</code>" if param and param != "-" else ""
        h.append(f'<tr><td class="id">{iid}</td><td class="what"><b>{escape(what)}</b><span>{escape(how)}</span></td>'
                 f'<td class="model">{escape(model)}{pm}</td><td>{boxes_html(b)}</td><td class="st">{escape(st)}</td>'
                 f'<td class="ph"><div></div></td></tr>')
    return "".join(h) + "</table>"


def fig_html(key):
    f = FIGS[key]
    return f'<div class="fig"><div class="cap">{escape(f.title)}</div>{f.svg()}</div>'


def page_intro():
    n = sum(len(s[3]) for s in SECTIONS)
    return f"""<div class="page intro">
<p style="color:#c92a2a;font-weight:700;margin:0">KIA TASMAN X-PRO FIT-OUT · {escape(P.VERSION)} · {DATE}</p>
<h1>Vehicle measurement sheet</h1>
<p>Every dimension the 3D model still guesses: {n} items in nine areas. Fill these in, send back a photo of the pages (or the CSV),
and the model gets updated. Then the cutting lists can be trusted. Each item shows <b>what the model assumes now</b>. A big difference
from that is exactly what we need to catch. The <b>Stage</b> column shows the first build stage that depends on it (see docs/build-stages.md), and the 📷 box is for ticking off a photo.</p>
<div class="cols"><div>
<h3>Before you start</h3>
<ul><li>Park on level ground, normal tyre pressures, unladen, and note the fuel level.</li>
<li>Everything is in <b>mm</b>, measured to the <b>liner surface</b> (what the furniture will touch) unless it says otherwise.</li>
<li>Driver side = right (D), passenger side = left (P).</li>
<li>Run masking tape along the tub centreline (half the wall-to-wall width, marked at the front and at the tailgate). That's Y = 0.</li>
<li>"Front / mid / rear" in the tub means X ≈ 100, 750 and 1400 unless an item says otherwise.</li>
<li>Photograph each item with the tape in shot and its ID written on masking tape.</li>
<li>Measure twice. If two readings differ by more than 2 mm, write both.</li></ul>
</div><div>
<h3>Tools</h3>
<ul><li>5 m tape and a 1 m steel rule</li><li>300 mm steel rule and digital calipers</li>
<li>Straight edge ≥ 1.8 m (an aluminium level is ideal) and a spirit level</li><li>Digital angle finder (a phone app works)</li>
<li>Plumb bob or a laser line, string line</li><li>Masking tape, marker, a radius gauge or a few coins</li></ul>
<h3>Priority</h3>
<ul><li><b>Stages 1 and 3</b> (tub, arches, fittings, chassis): needed before cutting anything for the battery bay, cabinets and slides.</li>
<li><b>Stage 6</b> (lid, bars, tent): under-tent storage.</li><li><b>Stages 2 and 7</b> (roof, windscreen): platform and visor.</li></ul>
</div></div>
{fig_html("d0-datums")}
<p class="foot">Generated from cad/params.py by tools/measure/measure_sheet.py. The diagrams are schematic, drawn from the model's current guesses, so they may not
look exactly like your ute. Measure what's really there.</p>
</div>"""


def build():
    pages = [page_intro()]
    shown = set()
    for num, title, figs, items in SECTIONS:
        body = [f"<h2>{num} · {escape(title)}</h2>"]
        for k in figs:
            if k not in shown:
                body.append(fig_html(k))
                shown.add(k)
        refs = ", ".join(FIGS[k].title.split(" · ")[0] for k in figs)
        if refs:
            body.append(f'<p class="foot">Diagrams: {refs}</p>')
        body.append(table_html(items))
        pages.append('<div class="page">' + "".join(body) + "</div>")
    if "d7-details" not in shown:
        pages.insert(1, '<div class="page">' + fig_html("d7-details") + "</div>")
    pages.append('<div class="page"><h2>Photo checklist</h2><ul class="chk">' + "".join(f"<li>{escape(p)}</li>" for p in PHOTOS) +
                 '</ul><h2 style="margin-top:6mm">Notes and sketches</h2><div class="lines">' + "<div></div>" * 22 + "</div></div>")
    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>Tasman measurement sheet</title><style>{CSS}</style></head><body>' + "".join(pages) + "</body></html>")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "measurement-sheet.html").write_text(html)
    (OUT / "diagrams").mkdir(exist_ok=True)
    for k, f in FIGS.items():
        (OUT / "diagrams" / f"{k}.svg").write_text(f.svg().replace('width="100%"', f'width="{f.w}" height="{f.h}"', 1))
    with open(OUT / "measurements.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "section", "measure", "how", "model assumes", "param", "value label", "your value", "notes"])
        for num, title, _, items in SECTIONS:
            for iid, what, how, model, param, b, st in items:
                if isinstance(b, tuple) and b[0] == "notes":
                    labels = ["notes"]
                elif isinstance(b, tuple) and b[0] == "grid":
                    labels = [f"{r} {c}" for r in b[1] for c in b[2]]
                else:
                    labels = list(b)
                for lab in labels:
                    w.writerow([iid, f"{num} {title}", what, how, model, param, lab, "", ""])
    n = sum(len(s[3]) for s in SECTIONS)
    print(f"{n} items; wrote {OUT.relative_to(ROOT)}/measurement-sheet.html, measurements.csv, diagrams/")


if __name__ == "__main__":
    build()
