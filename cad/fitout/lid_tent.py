"""Ute Master Load-Lid, Destroyer side rails, Rhino-Rack Vortex bars on raised brackets, 23Zero Panther Horizon 1600."""
from math import atan2, cos, degrees, hypot, radians, sin

import cadquery as cq

import params as P

from .core import anchor, box, cyl, part
from .vehicle import LID_STRUT, _fillet, _xz, _yz, comp

# ------------------------------------------------------------------ local figures
# Panther Horizon 1600 closed shell, scaled from reference/23zero-panther-horizon-1600-top-drawing.png (1.165 mm/px):
SHELL_TOP_INSET = 100   # [EST] flat top is inset ~100 mm from the outline on all sides (chamfered corners in the drawing)
SHELL_WALL_H = 110      # [EST] vertical wall above the base before the bevel (owner photo)
SHELL_SLOPE_X = 504     # [EST] front crease: the flat top ends 504 mm from the front (bar-free end of the drawing)
SHELL_SLOPE_DROP = 0.2  # [EST] the front of the top falls ~100 mm over that length
TENT_HW_X = (255, 1290)  # [EST] hinge / latch positions from the REAR end (drawing: brackets on both long sides)
# Tent services box face (Clipsal 56 series are 101 x 107 mm faces [PUB], so the v0.7 150 x 95 face cannot hold them):
SV_L = 315              # [DES] length along X (was TENT_SERVICES d = 150): GPO + inlet + SB50 / PV column
SV_H = 125              # [DES] height (was 95): 38 mm still clear above the lid
# Rhino-Rack Vortex aero section (no official drawing found; 79 x 30 kept from params, teardrop shape per retailers)
VORTEX = [(-39.5, 13), (-37.5, 20.5), (-32, 26), (-23, 29.3), (-10, 30), (12, 29.6), (26, 26.5), (39.5, 19),
          (39.5, 13.5), (26, 5.5), (10, 1.0), (-8, 0), (-23, 1.2), (-32, 4.5), (-37.5, 8.5)]
# Sunman eArc 100 W cell layout (4 x 8 visible cells on 1093 x 552) [EST from product photos]
EARC_CELLS = (8, 4)

IP66 = (205, 207, 210, 255)        # Clipsal 56 series grey
IP66_LID = (150, 153, 158, 255)
MC4 = (28, 28, 30, 255)
GRID = (170, 180, 196, 255)

# intentional contacts declared for clash.py (kept tight)
CLASH_ALLOW = []


def _rrect(xa, xb, ya, yb, r, n=4):
    pts = []
    for cx, cy, a0 in ((xb - r, yb - r, 0), (xa + r, yb - r, 90), (xa + r, ya + r, 180), (xb - r, ya + r, 270)):
        for k in range(n + 1):
            a = radians(a0 + 90 * k / n)
            pts.append((cx + r * cos(a), cy + r * sin(a)))
    return pts


def _wire(pts, z):
    return cq.Wire.makePolygon([cq.Vector(x, y, z) for x, y in pts], close=True)


def lid():
    parts = []
    z0, z1 = P.UNDER_LID_Z, P.LID_TOP_Z
    x0, x1 = P.LID_X0, P.LID_X0 + P.LID_L
    hw = P.LID_W / 2
    zm = (z0 + z1) / 2
    body = box(x0, x1, -hw, hw, z0, z1).edges("|Z").fillet(40)
    try:
        body = body.faces(">Z").edges().chamfer(6)
    except Exception:
        pass
    body = body.cut(box(x1 - 22, x1 + 1, -130, 130, z0 + 9, z1 - 9))           # rear handle pocket
    parts.append(part("load_lid", "lid", body, "lid", kg=60))
    parts.append(part("lid_handle", "lid", box(x1 - 18, x1 - 5, -105, 105, z0 + 15, z1 - 15), "rail"))
    parts.append(part("lid_lock", "lid", cyl(9, 8, (x1 + 2, 175, zm), "X"), "alu"))
    parts.append(part("lid_badge", "lid", box(x1 - 95, x1 - 60, -80, 80, z1, z1 + 1.2), "alu"))
    # hinges at the FRONT (cab end): leaf on the lid top + knuckle along the front edge
    for s in (1, -1):
        yc = s * 700
        h = box(x0 + 5, x0 + 75, yc - 45, yc + 45, z1, z1 + 4).union(cyl(9, 90, (x0 + 2, yc, z1 - 2), "Y"))
        parts.append(part(f"lid_hinge_{s}", "lid", h, "alu_dark"))
    # gas struts (lift the rear): lying in a channel in the top of each tub side wall, bracket up to the lid underside
    st = LID_STRUT
    dx, dz = st["x1"] - st["x0"], st["z1"] - st["z0"]
    ln = hypot(dx, dz)
    ang = -degrees(atan2(dz, dx))
    for s in (1, -1):
        y = s * (P.TUB_W / 2 + st["dy"])

        def place(w):
            return w.rotate((0, 0, 0), (0, 1, 0), ang).translate((st["x0"], y, st["z0"]))
        bodyc = cyl(st["r_body"], st["body_l"], (st["body_l"] / 2, 0, 0), "X")
        rod = cyl(st["r_rod"], ln - st["body_l"], (st["body_l"] + (ln - st["body_l"]) / 2, 0, 0), "X")
        parts.append(part(f"lid_gas_strut_{s}", "lid", place(bodyc), "rack"))
        parts.append(part(f"lid_gas_strut_rod_{s}", "lid", place(rod), "alu"))
        yb0, yb1 = sorted((s * (P.TUB_W / 2 + 10), s * (P.TUB_W / 2 + 34)))
        parts.append(part(f"lid_strut_bracket_{s}", "lid", box(st["x1"] - 15, st["x1"] + 15, yb0, yb1, st["z1"] - 8, z0), "alu_dark"))
    # Destroyer side rails: tall section, chamfered top, T-track, ramped ends, hex cut-outs (tie-down points)
    rt = z1 + P.LID_RAIL_H
    for s in (1, -1):
        yc = s * P.LID_RAIL_Y
        w2 = P.LID_RAIL_W / 2
        sec = [(yc - w2, z1), (yc + w2, z1), (yc + w2, z1 + 42), (yc + 12, rt), (yc - 12, rt), (yc - w2, z1 + 42)]
        rail = _yz(sec, x0 + 30, x1 - 30)
        rail = rail.intersect(_xz([(x0 + 30, z1), (x1 - 30, z1), (x1 - 30, z1 + 18), (x1 - 85, rt), (x0 + 85, rt), (x0 + 30, z1 + 18)],
                                  yc - 40, yc + 40))
        rail = rail.cut(box(x0 + 20, x1 - 20, yc - 6, yc + 6, rt - 14, rt + 1)).cut(box(x0 + 20, x1 - 20, yc - 10, yc + 10, rt - 14, rt - 8))
        for i in range(11):
            xc = x0 + 110 + i * (P.LID_L - 220) / 10
            hexa = (cq.Workplane("XZ", origin=(0, yc + 40, 0)).center(xc, z1 + 24).polygon(6, 30).extrude(80))
            rail = rail.cut(hexa)
        parts.append(part(f"lid_destroyer_rail_{s}", "lid", rail, "rail", kg=4))
    return parts


def rack_and_tent():
    parts = []
    rail_top = P.LID_TOP_Z + P.LID_RAIL_H
    bar_w, bar_h = P.RACK_BAR
    bar_z1 = P.TENT_Z0
    bar_z0 = bar_z1 - bar_h
    L2 = P.RACK_BAR_L / 2
    # raised brackets on the Destroyer rails (foot plate, tapered tower with a lightening slot, clamp saddle) + Vortex bars
    for xc in P.RACK_BAR_X:
        for s in (1, -1):
            yc = s * P.LID_RAIL_Y
            foot = box(xc - 45, xc + 45, yc - 22, yc + 22, rail_top, rail_top + 6)
            tower = _xz([(xc - 38, rail_top + 6), (xc + 38, rail_top + 6), (xc + 27, bar_z0 - 6), (xc - 27, bar_z0 - 6)], yc - 17, yc + 17)
            tower = tower.cut(_fillet(box(xc - 12, xc + 12, yc - 20, yc + 20, rail_top + 18, bar_z0 - 20), "|Y", 6))
            clamp = box(xc - 46, xc + 46, yc - 20, yc + 20, bar_z0 - 8, bar_z0 + 12)
            parts.append(part(f"rack_bracket_{xc}_{s}", "rack", foot.union(tower).union(clamp), "rack", kg=1.2))
        prof = [(xc + u, bar_z0 + v) for u, v in VORTEX]
        bar = _xz(prof, -L2 + 12, L2 - 12).cut(box(xc - 7, xc + 7, -L2, L2, bar_z1 - 6, bar_z1 + 1))   # top accessory channel
        parts.append(part(f"rack_bar_{xc}", "rack", bar, "rack", kg=4.5))
        for s in (1, -1):
            cap = cq.Workplane("XZ", origin=(0, max(s * L2, s * (L2 - 12)), 0)).polyline(prof).close().offset2D(1.5, "intersection").extrude(12)
            parts.append(part(f"rack_bar_endcap_{xc}_{s}", "rack", cap, "trim"))
    # tent mounting: a clamp plate under each bar where a tent under-rail crosses it, two bolts whose tails hang
    # well below the bar [EST] - the under-tent storage keeps clear of these four spots
    cl, cw, ct = P.TENT_BOLT_CLAMP
    for xc in P.RACK_BAR_X:
        for s in (1, -1):
            yc = s * P.TENT_UNDER_RAILS_CC / 2
            plate = box(xc - cl / 2, xc + cl / 2, yc - cw / 2, yc + cw / 2, bar_z0 - ct, bar_z0)
            bolts = [cyl(5, P.TENT_BOLT_DROP, (xc + dx, yc, bar_z0 - ct - P.TENT_BOLT_DROP / 2)) for dx in (-cl / 2 + 12, cl / 2 - 12)]
            nuts = [cyl(9, 8, (xc + dx, yc, bar_z0 - ct - 4)) for dx in (-cl / 2 + 12, cl / 2 - 12)]
            parts.append(part(f"tent_mount_clamp_{xc}_{s}", "rack", comp([plate] + bolts + nuts), "rack", kg=0.4))
    # ---- tent (closed)
    x0, x1 = P.TENT_X0, P.TENT_X0 + P.TENT_L
    hw = P.TENT_W / 2
    zb0 = P.TENT_Z0
    zb1 = zb0 + P.TENT_BASE_H
    zt = zb0 + P.TENT_H - 25
    sf = P.TENT_FOLDOUT_SIDE
    # underside mounting rails (sit on the bars): slotted extrusion with chamfered ends
    for s in (1, -1):
        yc = s * P.TENT_UNDER_RAILS_CC / 2
        r = box(x0 + 55, x0 + 55 + 1440, yc - 20, yc + 20, zb0, zb0 + 25).cut(box(x0 + 50, x0 + 1500, yc - 5, yc + 5, zb0 - 1, zb0 + 9))
        parts.append(part(f"tent_under_rail_{s}", "tent", _fillet(r, "|Y and <Z", 8), "tent_rail"))
    parts.append(part("tent_base", "tent", box(x0, x1, -hw, hw, zb0 + 25, zb1).edges("|Z").fillet(60), "tent_base"))
    # hard shell: vertical wall, bevel to a flat top inset on all sides (drawing), creased slope at the front end
    wires = [_wire(_rrect(x0 + 5, x1 - 5, -hw + 5, hw - 5, 70), zb1),
             _wire(_rrect(x0 + 5, x1 - 5, -hw + 5, hw - 5, 70), zb1 + SHELL_WALL_H),
             _wire(_rrect(x0 + SHELL_TOP_INSET, x1 - SHELL_TOP_INSET, -hw + SHELL_TOP_INSET, hw - SHELL_TOP_INSET, 45), zt)]
    shell = cq.Workplane("XY").add(cq.Solid.makeLoft(wires, True))
    xs = x0 + SHELL_SLOPE_X
    zf = zt - (xs - x0 + 5) * SHELL_SLOPE_DROP
    shell = shell.intersect(_xz([(x0 - 5, zb1 - 5), (x1 + 5, zb1 - 5), (x1 + 5, zt + 5), (xs + 25, zt + 5), (xs, zt), (x0 - 5, zf)],
                                -hw - 5, hw + 5))
    parts.append(part("tent_shell", "tent", shell, "tent", kg=P.TENT_KG))
    lip = (cq.Workplane("XY").add(cq.Solid.makeLoft([_wire(_rrect(x0, x1, -hw, hw, 72), zb1), _wire(_rrect(x0, x1, -hw, hw, 72), zb1 + 12)], True))
           .cut(box(x0 + 9, x1 - 9, -hw + 9, hw - 9, zb1 - 1, zb1 + 13)))
    parts.append(part("tent_shell_lip", "tent", lip, "tent_rail"))
    # top bars toward the rear (flat part of the shell): T-slot extrusions + two ribbed cross members (drawing)
    bx1 = x1 - 120
    bx0 = bx1 - P.TENT_BAR_L
    for s in (1, -1):
        yc = s * P.TENT_BAR_CC / 2
        sec = [(yc - 15, zt), (yc + 15, zt), (yc + 15, zt + 20), (yc + 11, zt + 25), (yc - 11, zt + 25), (yc - 15, zt + 20)]
        b = _yz(sec, bx0, bx1).cut(box(bx0 - 1, bx1 + 1, yc - 4, yc + 4, zt + 17, zt + 26))
        parts.append(part(f"tent_top_bar_{s}", "tent", b, "tent_rail"))
    yi_ = P.TENT_BAR_CC / 2 - 15
    for i, xa in enumerate((bx0 + 20, bx1 - 90)):
        c = box(xa, xa + 70, -yi_, yi_, zt, zt + 18)
        for g in range(4):
            c = c.cut(box(xa + 9 + g * 16, xa + 13 + g * 16, -yi_ - 1, yi_ + 1, zt + 14, zt + 19))
        parts.append(part(f"tent_top_cross_{i}", "tent", c, "tent_rail"))
    # hardware: hinges on the fold-out side, over-centre latches opposite, grab handles, end latches, ladder bracket
    so = -sf
    for i, d in enumerate(TENT_HW_X):
        xh = x1 - d
        yb0, yb1 = sorted((sf * (hw - 6), sf * (hw + 6)))
        hinge = box(xh - 45, xh + 45, yb0, yb1, zb0 + 25, zb1 + 45).union(cyl(8, 90, (xh, sf * (hw + 8), zb1), "X"))
        parts.append(part(f"tent_hinge_{i}", "tent", hinge, "alu_dark"))
        la0, la1 = sorted((so * (hw - 6), so * (hw + 14)))
        lv0, lv1 = sorted((so * (hw + 14), so * (hw + 20)))
        latch = box(xh - 25, xh + 25, la0, la1, zb0 + 28, zb1 + 30).union(box(xh - 18, xh + 18, lv0, lv1, zb0 + 35, zb1 + 20))
        parts.append(part(f"tent_latch_{i}", "tent", latch, "alu_dark"))
    xm = (x0 + x1) / 2
    for s in (1, -1):
        o0, o1 = sorted((s * (hw - 2), s * (hw + 26)))
        i0, i1 = sorted((s * (hw + 4), s * (hw + 20)))
        h = box(xm - 75, xm + 75, o0, o1, zb1 - 5, zb1 + 25).cut(box(xm - 60, xm + 60, i0, i1, zb1 - 6, zb1 + 26))
        parts.append(part(f"tent_handle_{s}", "tent", h, "rack"))
    for i, xe in enumerate((x0, x1)):
        e = 1 if i else -1
        ya, yb = sorted((sf * (hw - 230), sf * (hw - 170)))
        parts.append(part(f"tent_end_latch_{i}", "tent", box(xe - e * 4, xe + e * 14, ya, yb, zb0 + 28, zb1 + 30), "alu_dark"))
    lb0, lb1 = sorted((sf * (hw - 2), sf * (hw + 32)))
    li0, li1 = sorted((sf * (hw + 4), sf * (hw + 26)))
    ladder = box(x1 - 430, x1 - 300, lb0, lb1, zb0 + 4, zb1 + 6).cut(box(x1 - 420, x1 - 310, li0, li1, zb0 + 3, zb1 + 7))
    parts.append(part("tent_ladder_bracket", "tent", ladder, "alu_dark"))
    # 2 x Sunman eArc 100 W on a 3 mm ACM sheet spanning the two top bars: cell grid + junction box
    pl, pw, _ = P.TENT_PANEL
    sx0 = (bx0 + bx1) / 2 - pl / 2
    parts.append(part("tent_solar_backing", "solar", box(sx0 - 10, sx0 + pl + 10, -pw - 10, pw + 10, zt + 25, zt + 28),
                      "solar_frame", fab=True, mat="ACM 3"))
    nx, ny = EARC_CELLS
    for i, (ya, yb) in enumerate(((-pw - 2, -2), (2, pw + 2))):
        parts.append(part(f"tent_solar_{i+1}", "solar", box(sx0, sx0 + pl, ya, yb, zt + 28, zt + 31), "solar", kg=2.0, watts=100))
        lines = [box(sx0 + 8, sx0 + pl - 8, ya + k * (yb - ya) / ny - 1.2, ya + k * (yb - ya) / ny + 1.2, zt + 31, zt + 31.5)
                 for k in range(1, ny)]
        lines += [box(sx0 + k * pl / nx - 1.2, sx0 + k * pl / nx + 1.2, ya + 8, yb - 8, zt + 31, zt + 31.5) for k in range(1, nx)]
        parts.append(part(f"tent_solar_{i+1}_grid", "solar", comp(lines), GRID))
    parts.append(part("tent_solar_jbox", "solar", box(sx0 + 20, sx0 + 75, -pw + 20, -pw + 60, zt + 31, zt + 41), MC4))
    anchor("tent_pv_jbox", (sx0 + 40, -pw + 40, zt + 28))
    # ---- tent services box: under the tent base, toward the front, inset from the fold-out side
    sv = P.TENT_SERVICES
    s = sf
    yo = s * (hw - sv["inset"])           # outboard face of the box
    yi = yo - s * sv["w"]
    sx = x0 + sv["x"]
    ya, yb = sorted((yi, yo))
    parts.append(part("tent_services_box", "tent_services", _fillet(box(sx, sx + SV_L, ya, yb, zb0 - SV_H, zb0), "|Z", 6),
                      "outlet", kg=2.5))
    zc = zb0 - SV_H / 2

    def out(a, b):
        return sorted((yo + s * a, yo + s * b))
    # IP66 10 A outlet (heater) and IP66 15 A inlet (shore): Clipsal 56 series 101 x 107 faces with flip lids
    for nm, xa in (("tent_heater_gpo", sx + 10), ("tent_shore_inlet", sx + 121)):
        b0, b1 = out(0, 22)
        dev = box(xa, xa + 101, b0, b1, zc - 53.5, zc + 53.5)
        if nm == "tent_shore_inlet":
            c0 = yo + s * 37
            dev = dev.union(cyl(30, 30, (xa + 50.5, c0, zc - 8), "Y"))         # plug boss
        parts.append(part(nm, "tent_services", dev, IP66))
        l0, l1 = out(22, 30) if nm == "tent_heater_gpo" else out(52, 56)
        lidp = box(xa + 8, xa + 93, l0, l1, zc - 40, zc + 44) if nm == "tent_heater_gpo" else cyl(33, 4, (xa + 50.5, yo + s * 54, zc - 8), "Y")
        parts.append(part(nm + "_lid", "tent_services", lidp, IP66_LID))
    # Anderson SB50 (12 V to the tent) in a flush housing, PV MC4 bulkhead pair below it
    h0, h1 = out(0, 20)
    parts.append(part("tent_services_sb50", "tent_services", box(sx + 233, sx + 303, h0, h1, zb0 - 60, zb0 - 10), "anderson_grey"))
    p0, p1 = out(20, 42)
    parts.append(part("tent_services_sb50_plug", "tent_services", box(sx + 246, sx + 290, p0, p1, zb0 - 50, zb0 - 20), "anderson"))
    q0, q1 = out(0, 6)
    pv = box(sx + 233, sx + 303, q0, q1, zb0 - 115, zb0 - 70)
    for xq in (sx + 252, sx + 284):
        pv = pv.union(cyl(8, 30, (xq, yo + s * 18, zb0 - 92), "Y"))
    parts.append(part("tent_services_pv", "tent_services", pv, MC4))
    anchor("tent_services", (sx + 10, (yi + yo) / 2, zb0 - 10))
    anchor("tent_front_drop", (x0 + 15, -hw + 120, zb0 - 10))
    return parts
