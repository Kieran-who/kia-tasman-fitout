"""Roof platform: recessed solar, Starlink Mini inside the frame, removable cargo bars, flush light bar.

Wedgetail Adventure WT-KT-1614U (1600 x 1450, black powder-coated extrusions): side rails with an accessory T-slot,
end members, centre spine, angled wind fairing with the light bar recessed flush in its face, recessed solar brackets
under the panels, slats in the uncovered bay. Victron BlueSolar panels: anodised frame, glass/cell laminate with the
cell grid, junction box on the back.
"""
import params as P

from .core import anchor, box, part
from .vehicle import _fillet, _xz, _yz, comp

CELLS = {"190w": (9, 4), "130w": (9, 4)}   # [EST] 36-cell 12 V modules (4 rows x 9), from Victron product photos
FRAME_W = 20                               # [EST] visible frame width of the BlueSolar modules
GRID = (175, 185, 200, 255)
JBOX = (28, 28, 30, 255)
LENS = (245, 245, 235, 255)

CLASH_ALLOW = []


def _rail_x(x0, x1, ya, yb, z0, z1, slot_side):
    """Platform extrusion along X: chamfered top-outer edge, accessory T-slot on the outer face, hollow core."""
    yo, yi = (yb, ya) if slot_side > 0 else (ya, yb)
    sec = [(yi, z0), (yo, z0), (yo, z1 - 8), (yo - slot_side * 8, z1), (yi, z1)]
    r = _yz(sec, x0, x1)
    r = r.cut(box(x0 - 1, x1 + 1, yo - slot_side * 7, yo + slot_side, z0 + 14, z0 + 24))    # T-slot mouth
    r = r.cut(box(x0 - 1, x1 + 1, yo - slot_side * 13, yo - slot_side * 6, z0 + 10, z0 + 28))  # T-slot undercut
    r = r.cut(box(x0 - 1, x1 + 1, yi + slot_side * 3, yo - slot_side * 16, z0 + 3, z1 - 4))   # hollow core
    return r


def _panel(parts, key, x0, y0, L, W, zp, t, kg, watts):
    """Victron BlueSolar: frame ring (solar_frame), laminate (the named, massed part), grid lines, junction box."""
    name = f"roof_solar_{key}"
    f = FRAME_W
    frame = box(x0, x0 + L, y0, y0 + W, zp, zp + t).cut(box(x0 + f, x0 + L - f, y0 + f, y0 + W - f, zp - 1, zp + t + 1))
    frame = frame.union(box(x0 + f, x0 + L - f, y0 + f, y0 + W - f, zp, zp + 3)).cut(
        box(x0 + f + 25, x0 + L - f - 25, y0 + f + 25, y0 + W - f - 25, zp - 1, zp + 4))       # back flange
    parts.append(part(f"{name}_frame", "solar", frame, "solar_frame"))
    zl = zp + t - 4
    parts.append(part(name, "solar", box(x0 + f, x0 + L - f, y0 + f, y0 + W - f, zl - 3, zl), "solar", kg=kg, watts=watts))
    nx, ny = CELLS[key]
    ix0, ix1, iy0, iy1 = x0 + f + 6, x0 + L - f - 6, y0 + f + 6, y0 + W - f - 6
    lines = [box(ix0, ix1, iy0 + k * (iy1 - iy0) / ny - 1.5, iy0 + k * (iy1 - iy0) / ny + 1.5, zl, zl + 0.5) for k in range(1, ny)]
    lines += [box(ix0 + k * (ix1 - ix0) / nx - 1.5, ix0 + k * (ix1 - ix0) / nx + 1.5, iy0, iy1, zl, zl + 0.5) for k in range(1, nx)]
    parts.append(part(f"{name}_grid", "solar", comp(lines), GRID))
    jx = x0 + L - f - 160
    parts.append(part(f"{name}_jbox", "solar", box(jx, jx + 110, y0 + W / 2 - 60, y0 + W / 2 + 60, zp + 4, zl - 3), JBOX))


def roof(cargo=True):
    parts = []
    g = "roof"
    x0, x1 = P.PLAT_X0, P.PLAT_X0 + P.PLAT_L
    hw = P.PLAT_W / 2
    z0, z1 = P.PLAT_Z, P.PLAT_Z + P.PLAT_T
    e = 40
    for yy in (-hw, hw - e):
        sd = 1 if yy > 0 else -1
        parts.append(part(f"plat_side_{int(yy)}", g, _rail_x(x0, x1, yy, yy + e, z0, z1, sd), "trim", kg=9.0))  # incl. share of slats/brackets (est)
    for xx in (x0, x1 - e):
        sec = [(xx, z0), (xx + e, z0), (xx + e, z1), (xx, z1)]
        end = _xz(sec, -hw + e, hw - e).cut(box(xx + 3, xx + e - 3, -hw + e - 1, hw - e + 1, z0 + 3, z1 - 3))
        parts.append(part(f"plat_end_{int(xx)}", g, end, "trim", kg=2.5))
    # centre spine between the two panel bays
    sp = _yz([(-15, z0), (15, z0), (15, z1 - 4), (11, z1), (-11, z1), (-15, z1 - 4)], x0 + e, x1 - e)
    parts.append(part("plat_spine", g, sp.cut(box(x0 + e - 1, x1 - e + 1, -12, 12, z0 + 3, z1 - 7)), "trim", kg=2.0))
    # front wind fairing: vertical face carrying the flush light bar, sloping back to the frame top
    fx0 = x0 - 95
    fair = _xz([(fx0, z0 - 12), (x0, z0 - 12), (x0, z1 + 8), (x0 - 40, z1 + 8), (fx0, z1 - 2)], -hw, hw)
    fair = _fillet(fair, "|Z", 30)
    fair = fair.cut(box(fx0 - 1, fx0 + 14, -518, 518, z0 - 4, z1 - 6))         # light-bar recess
    parts.append(part("plat_fairing", g, fair, "trim", kg=2.5))
    lb = box(fx0 + 2, fx0 + 14, -512, 512, z0 - 2, z1 - 8)
    parts.append(part("light_bar", g, lb, LENS, kg=3.0))
    parts.append(part("light_bar_optics", g, comp([box(fx0 + 1.5, fx0 + 2, y - 30, y + 30, z0 + 2, z1 - 12)
                                                    for y in range(-480, 481, 80)]), "alu"))
    # mounts to the factory roof points: tapered towers on a foot pad
    for xx in (x0 + 220, x1 - 260):
        for s in (1, -1):
            ya, yb = sorted((s * 600, s * 660))
            tw = _xz([(xx - 10, P.ROOF_Z), (xx + 60, P.ROOF_Z), (xx + 50, z0), (xx, z0)], ya, yb)
            parts.append(part(f"plat_mount_{int(xx)}_{s}", g, tw, "trim", kg=0.8))
    # recessed panels (on brackets inside the frame)
    zp = z0 + 2
    la, wa, ta = P.ROOF_PANEL_A
    _panel(parts, "190w", x0 + e + 10, 16, la, wa, zp, ta, 10.5, 190)
    lb_, wb, tb = P.ROOF_PANEL_B
    _panel(parts, "130w", x0 + e + 10, -16 - wb, lb_, wb, zp, tb, 7.1, 130)
    # Wedgetail recessed solar brackets under the panels (spine -> side rail), clear of the roof mounts
    br = []
    for xb, side in ((x0 + 400, 1), (x0 + 1150, 1), (x0 + 400, -1), (x0 + 900, -1)):
        ya, yb = sorted((side * 15, side * (hw - e)))
        br.append(box(xb, xb + 40, ya, yb, zp - 18, zp))
    parts.append(part("plat_solar_brackets", g, comp(br), "trim"))
    # slats in the uncovered passenger bay between panel B and the Starlink pocket
    sl, sw, sh = P.STARLINK_MINI
    sx0 = x1 - e - 15 - sw
    slats = [box(xs, xs + 40, -hw + e, -15, z1 - 20, z1) for xs in (x0 + e + 10 + lb_ + 25, x0 + e + 10 + lb_ + 110)]
    parts.append(part("plat_slats", g, comp(slats), "trim"))
    # Starlink Mini in the pocket behind panel B (passenger rear), low bracket, top just above the frame
    parts.append(part("starlink_bracket", g, box(sx0 - 10, sx0 + sw + 10, -hw + e + 20, -40, z0 + 2, z0 + 8), "alu_dark", fab=True, mat="Plate 4 5052"))
    yc = -16 - wb / 2
    dish = _fillet(box(sx0, sx0 + sw, yc - sl / 2, yc + sl / 2, z0 + 8, z0 + 8 + sh), "|Z", 28)
    try:
        dish = dish.faces(">Z").edges().chamfer(7)
    except Exception:
        pass
    parts.append(part("starlink_mini", g, dish, "starlink", kg=1.16))
    anchor("starlink", (sx0 + sw / 2, yc, z0 + 8))
    anchor("roof_pv", (x1 - e - 20, 0, z0 + 10))
    anchor("roof_drop", (P.CAB_REAR_X + 5, -560, P.ROOF_Z - 40))
    if cargo:
        for xx in (x0 + 260, x0 + 1050):
            for s in (1, -1):
                ya, yb = sorted((s * (hw - e), s * hw))
                riser = _xz([(xx - 8, z1), (xx + 58, z1), (xx + 45, z1 + P.CARGO_BAR_Z), (xx + 5, z1 + P.CARGO_BAR_Z)], ya, yb)
                riser = riser.cut(_fillet(box(xx + 14, xx + 36, ya - 1, yb + 1, z1 + 25, z1 + P.CARGO_BAR_Z - 25), "|Y", 8))
                parts.append(part(f"cargo_riser_{int(xx)}_{s}", "cargo", riser, "alu_dark", kg=0.6))
            bar = _fillet(box(xx - 10, xx + 60, -hw - 45, hw + 45, z1 + P.CARGO_BAR_Z, z1 + P.CARGO_BAR_Z + 30), "|Y", 6)
            bar = bar.cut(box(xx + 18, xx + 32, -hw - 46, hw + 46, z1 + P.CARGO_BAR_Z + 22, z1 + P.CARGO_BAR_Z + 31))
            parts.append(part(f"cargo_bar_{int(xx)}", "cargo", bar, "trim", kg=3.0))
            for s in (1, -1):
                ya, yb = sorted((s * (hw + 45), s * (hw + 60)))
                parts.append(part(f"cargo_bar_cap_{int(xx)}_{s}", "cargo",
                                  _fillet(box(xx - 11, xx + 61, ya, yb, z1 + P.CARGO_BAR_Z - 1, z1 + P.CARGO_BAR_Z + 31), "|Y", 8), "rack"))
    return parts
