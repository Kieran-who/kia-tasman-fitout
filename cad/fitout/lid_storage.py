"""
Under-tent storage on the Load-Lid (v0.10): the 163 mm gap between the lid top and the tent.

Plan (X rearward, passenger side -Y):
    front bar | 30 L water across the vehicle (captive, filled and drawn in place)  | services box (driver front)
              | outer lanes between the bars: bolt-on space on the rivnut cross-bars
    rear bar  | rear-loading drawer cassette in the middle, between the tent-bolt lines (table + flat gear)
    rear edge | 2 kg extinguisher in a quick-release bracket (passenger corner), RotopaX 1 gal diesel (driver corner)

Everything sits on 40 x 5 aluminium cross-bars clamped into the Destroyer rails' T-track (no holes in the lid),
with M8 rivnuts at 100 mm pitch so lock mounts, the cassette and tie-downs bolt anywhere.
Group 'lid_storage' = fixed hardware (fit-out mass); 'lid_cargo' = the cans, extinguisher and table (payload).
"""
import params as P

from .core import anchor, box, cyl, part
from .vehicle import _fillet, comp

G, GC = "lid_storage", "lid_cargo"
XB_W, XB_T = 40, 5                  # cross-bar section
RAIL_IN = P.LID_RAIL_Y - P.LID_RAIL_W / 2 - 1   # inner face of the Destroyer rails (-1 mm)
WATER_GREEN = (88, 102, 64, 255)
DIESEL_YELLOW = (226, 184, 32, 255)
EXT_RED = (196, 30, 36, 255)
STRAP = (40, 40, 44, 255)
TABLE_TOP = (205, 208, 212, 255)
SHEET = (176, 182, 188, 255)

CLASH_ALLOW = [("uts_cassette", "uts_drawer"), ("uts_water_jacket", "uts_water_strap"),
               ("uts_water", "uts_water_strap"), ("uts_diesel", "uts_diesel_mount"), ("uts_exting", "uts_exting_bracket"),
               ("uts_table", "uts_drawer"), ("uts_xbar_end", "lid_destroyer_rail")]


def lid_storage(state="travel"):
    parts = []
    z0 = P.LID_TOP_Z
    zb = z0 + XB_T                                   # top of the cross-bars = floor of the storage
    # ---- cross-bars with rivnut holes (100 mm pitch) and end clamps into the rail T-track
    for i, xc in enumerate(P.UT_XBARS):
        bar = box(xc - XB_W / 2, xc + XB_W / 2, -RAIL_IN, RAIL_IN, z0, zb)
        holes = comp([cyl(4.5, XB_T + 2, (xc, y, z0 + XB_T / 2)) for y in range(-750, 751, 100)])
        parts.append(part(f"uts_xbar_{i}", G, bar.cut(holes), "alu", fab=True, mat="Flat 40x5 6060"))
        ends = comp([box(xc - XB_W / 2, xc + XB_W / 2, s * RAIL_IN - (s > 0) * 4, s * RAIL_IN + (s < 0) * 4, zb, z0 + 35)
                     for s in (1, -1)])
        parts.append(part(f"uts_xbar_end_{i}", G, ends, "alu_dark", kg=0.1))
    # ---- 30 L water: lying flat across the vehicle between the services box line and the passenger rail
    w = P.UT_WATER
    wx0, wy0 = w["x0"], w["y0"]
    can = _fillet(box(wx0, wx0 + w["W"], wy0, wy0 + w["L"], zb, zb + w["H"]), "|Z", 30)
    for k in range(3):                                # three moulded grip recesses along the top edge
        yy = wy0 + 120 + k * 300
        can = can.cut(box(wx0 - 1, wx0 + 40, yy, yy + 110, zb + 30, zb + w["H"] - 30))
    parts.append(part("uts_water_30l", GC, can, WATER_GREEN, kg=w["kg"], note="OnTrack slimline 30 L, full; check food-grade"))
    parts.append(part("uts_water_cap", GC, cyl(22, 18, (wx0 + w["W"] - 60, wy0 - 9, zb + w["H"] - 40), "Y"), "trim"))
    # v0.14 cold-weather jacket (docs/cold-weather.md): closed-cell foam top (30 mm, grooved over the tent under-rail),
    # sides 18-20 mm, closed end 20 mm; the cap end stays open for filling and the tap. A 50 W pad (HP3) lies on a
    # foam strip between the two cross-bars under the can; its lead comes from the tent services box (WHT).
    zj = zb + w["H"] + 30                             # 778: jacket top, 3 mm under the tent base (27 mm over the straps)
    top = box(wx0 - 20, wx0 + w["W"] + 18, wy0, wy0 + w["L"] + 20, zb + w["H"] + 3, zj)       # over the can straps
    top = top.cut(box(wx0 - 21, wx0 + w["W"] + 19, -425, -375, zb + w["H"] + 7, zj + 1))     # tent under-rail (y -420..-380)
    sides = comp([box(wx0 - 20, wx0, wy0, wy0 + w["L"] + 20, z0, zb + w["H"] + 3)
                  .cut(box(wx0 - 21, wx0 - 9, -430, -370, z0 - 1, zb + w["H"] + 4)),           # tent mount clamp (y -425..-375)
                  box(wx0 + w["W"], wx0 + w["W"] + 18, wy0, wy0 + w["L"] + 20, z0, zb + w["H"] + 3),
                  box(wx0, wx0 + w["W"], wy0 + w["L"], wy0 + w["L"] + 20, zb, zb + w["H"] + 3)
                  .cut(box(wx0 + 180, wx0 + 220, wy0 + w["L"] - 1, wy0 + w["L"] + 21, zb - 1, zb + 8))])     # pad lead notch
    parts.append(part("uts_water_jacket", G, comp([top, sides]), (52, 56, 60, 255), kg=0.6,
                      product="Water can jacket: closed-cell foam, fabric covered (made to fit)"))
    xp0, xp1 = P.UT_XBARS[0] + XB_W / 2 + 5, P.UT_XBARS[1] - XB_W / 2 - 5        # 325 .. 495: between the bars
    parts.append(part("uts_water_pad_foam", G, box(xp0, xp1, wy0 + 85, wy0 + w["L"] - 30, z0, zb - 1.5), (172, 178, 184, 255),
                      kg=0.05, product="Closed-cell foam 3 mm"))
    parts.append(part("uts_water_heat_pad", G, box(xp0 + 5, xp1 - 5, wy0 + 90, wy0 + w["L"] - 35, zb - 1.5, zb), (196, 74, 44, 255),
                      kg=0.1, product="12 V 50 W silicone heater pad 160 x 735 with 45 C NC cut-out (HP3)"))
    anchor("water_heat_pad", (wx0 + 200, wy0 + w["L"] - 35, zb - 2.5))
    straps = [box(x, x + 25, wy0 + 60, wy0 + 64, zb, zb + w["H"] + 3).union(box(x, x + 25, wy0 + 60, wy0 + w["L"] - 60, zb + w["H"], zb + w["H"] + 3))
              .union(box(x, x + 25, wy0 + w["L"] - 64, wy0 + w["L"] - 60, zb, zb + w["H"] + 3)) for x in (wx0 + 60, wx0 + w["W"] - 85)]
    parts.append(part("uts_water_straps", G, comp(straps), STRAP, kg=0.3))
    # ---- rear-loading drawer: cassette (sides + top) between the tent-bolt lines, drawer box on side-mount runners
    d = P.UT_DRAWER
    x0, x1, hw, h = d["x0"], d["x1"], d["hw"], d["h"]
    zt = zb + h
    sides = comp([box(x0, x1, s * hw - (s > 0) * 2, s * hw + (s < 0) * 2, zb, zt - 1.6) for s in (1, -1)])
    parts.append(part("uts_cassette_sides", G, sides, SHEET, fab=True, mat="Sheet 1.6 5005"))
    parts.append(part("uts_cassette_top", G, box(x0, x1, -hw, hw, zt - 1.6, zt), SHEET, fab=True, mat="Sheet 1.6 5005"))
    parts.append(part("uts_cassette_front", G, box(x0, x0 + 1.6, -hw + 2, hw - 2, zb, zt - 1.6), SHEET, fab=True, mat="Sheet 1.6 5005"))
    ext = d["travel"] if state == "camp" else 0
    rw = 13                                           # runner thickness each side
    dy0, dy1 = -hw + 2 + rw, hw - 2 - rw
    dx0, dx1 = x0 + 6 + ext, x1 - 3 + ext
    dz0, dz1 = zb + 3, zt - 6
    runners = comp([box(x0 + 10 + ext * k / 2, x1 - 10 + ext * k / 2, s * (hw - 2) - (s > 0) * rw, s * (hw - 2) + (s < 0) * rw,
                        dz0 + 25, dz0 + 70) for s in (1, -1) for k in (0, 1, 2)])
    parts.append(part("uts_drawer_runners", G, runners, "runner", kg=3.0, note="36 in full-extension locking side-mount pair"))
    tray = box(dx0, dx1, dy0, dy1, dz0, dz1).cut(box(dx0 + 1.6, dx1 - 1.6, dy0 + 1.6, dy1 - 1.6, dz0 + 1.6, dz1 + 1))
    parts.append(part("uts_drawer_box", G, tray, SHEET, fab=True, mat="Sheet 1.6 5005"))
    face = box(dx1, dx1 + 3, -hw, hw, zb, zt).cut(box(dx1 - 1, dx1 + 4, -110, 110, dz0 + 30, dz0 + 70))
    parts.append(part("uts_drawer_face", G, face, "alu_dark", fab=True, mat="Plate 3 5052"))
    parts.append(part("uts_drawer_handle", G, box(dx1 + 0.5, dx1 + 2.5, -100, 100, dz0 + 44, dz0 + 56), "rail"))
    parts.append(part("uts_drawer_lock", G, cyl(9, 8, (dx1 + 5, 160, (zb + zt) / 2), "X"), "alu", kg=0.1))
    tl, tw, tt, tkg = P.UT_TABLE
    tx0 = dx0 + 40
    parts.append(part("uts_table_folded", GC, box(tx0, tx0 + tl, -tw / 2, tw / 2, dz0 + 1.6, dz0 + 1.6 + tt).edges("|Z").fillet(10),
                      TABLE_TOP, kg=tkg, note="Wanderer Lightweight Steel Folding Table II, packed 800 x 600 x 40"))
    # ---- RotopaX 1 gal diesel pack on its pack mount (rear driver corner)
    r = P.UT_DIESEL
    rx0, ry0 = r["x0"], r["y0"]
    pack = _fillet(box(rx0, rx0 + r["W"], ry0, ry0 + r["L"], zb + 6, zb + 6 + r["H"]), "|Z", 40)
    pack = pack.cut(cyl(28, r["H"] + 4, (rx0 + r["W"] / 2, ry0 + r["L"] / 2, zb + 6 + r["H"] / 2)))
    parts.append(part("uts_diesel_rotopax", GC, pack, DIESEL_YELLOW, kg=r["kg"], note="RotopaX 1 gal diesel, full"))
    mount = box(rx0 + 20, rx0 + r["W"] - 20, ry0 + 60, ry0 + r["L"] - 60, zb, zb + 6).union(
        cyl(27, r["H"] + 14, (rx0 + r["W"] / 2, ry0 + r["L"] / 2, zb + 6 + (r["H"] + 14) / 2)))
    parts.append(part("uts_diesel_mount", G, mount, "alu_dark", kg=0.8, note="RotopaX pack mount + lock"))
    # ---- 2 kg ABE extinguisher, lying across the vehicle, quick-release strap bracket, handle toward the passenger side
    e = P.UT_EXTING
    zc = zb + 8 + e["r"]
    ey0 = e["y0"]
    body = cyl(e["r"], e["L"] - 110, (e["xc"], ey0 + 110 + (e["L"] - 110) / 2, zc), "Y")
    head = cyl(22, 60, (e["xc"], ey0 + 80, zc), "Y").union(box(e["xc"] - 12, e["xc"] + 12, ey0, ey0 + 70, zc + 10, zc + 30))
    parts.append(part("uts_exting_2kg", GC, body, EXT_RED, kg=e["kg"], note="2 kg ABE dry powder, AS/NZS 1841"))
    parts.append(part("uts_exting_head", GC, head, "trim"))
    br = [box(e["xc"] - 50, e["xc"] + 50, ey0 + 120, ey0 + e["L"] - 10, zb, zb + 8)]
    for yy in (ey0 + 150, ey0 + e["L"] - 60):
        br += [box(e["xc"] - e["r"] - 4, e["xc"] - e["r"], yy, yy + 30, zb + 8, zc + 10),
               box(e["xc"] + e["r"], e["xc"] + e["r"] + 4, yy, yy + 30, zb + 8, zc + 10)]
    parts.append(part("uts_exting_bracket", G, comp(br), "alu_dark", kg=0.6, note="quick-release strap bracket"))
    return parts
