"""Ute Master Load-Lid, Destroyer side rails, Rhino-Rack bars on raised brackets, 23Zero tent."""
import cadquery as cq

import params as P

from .core import anchor, box, part, prof_xz


def lid():
    parts = []
    z0, z1 = P.UNDER_LID_Z, P.LID_TOP_Z
    x0, x1 = P.LID_X0, P.LID_X0 + P.LID_L
    hw = P.LID_W / 2
    parts.append(part("load_lid", "lid", box(x0, x1, -hw, hw, z0, z1).edges("|Z").fillet(40), "lid", kg=60))
    # Destroyer side rails: T-track on top + hex cut-outs (tie-down points)
    for s in (1, -1):
        yc = s * P.LID_RAIL_Y
        rail = box(x0 + 30, x1 - 30, yc - P.LID_RAIL_W / 2, yc + P.LID_RAIL_W / 2, z1, z1 + P.LID_RAIL_H)
        rail = rail.cut(box(x0 + 20, x1 - 20, yc - 6, yc + 6, z1 + P.LID_RAIL_H - 14, z1 + P.LID_RAIL_H + 1))
        for i in range(11):
            xc = x0 + 110 + i * (P.LID_L - 220) / 10
            hexa = (cq.Workplane("XZ", origin=(0, yc + 40, 0)).center(xc, z1 + 24)
                    .polygon(6, 30).extrude(80))
            rail = rail.cut(hexa)
        parts.append(part(f"lid_destroyer_rail_{s}", "lid", rail, "rail", kg=4))
    return parts


def rack_and_tent():
    parts = []
    rail_top = P.LID_TOP_Z + P.LID_RAIL_H
    bar_w, bar_h = P.RACK_BAR
    bar_z1 = P.TENT_Z0
    bar_z0 = bar_z1 - bar_h
    # raised brackets on the Destroyer rails + Rhino-Rack Vortex bars across
    for xc in P.RACK_BAR_X:
        for s in (1, -1):
            yc = s * P.LID_RAIL_Y
            leg = box(xc - 35, xc + 35, yc - 22, yc + 22, rail_top, bar_z0).edges("|Y").fillet(8)
            parts.append(part(f"rack_bracket_{xc}_{s}", "rack", leg, "rack", kg=1.2))
        bar = box(xc - bar_w / 2, xc + bar_w / 2, -P.RACK_BAR_L / 2, P.RACK_BAR_L / 2, bar_z0, bar_z1).edges("|Y").fillet(9)
        parts.append(part(f"rack_bar_{xc}", "rack", bar, "rack", kg=4.5))
    # future storage volume between lid and tent (slim jerry cans etc. - to be measured)
    fx0, fx1 = P.RACK_BAR_X[0] + bar_w / 2 + 10, P.RACK_BAR_X[1] - bar_w / 2 - 10
    parts.append(part("under_tent_storage_volume", "future",
                      box(fx0, fx1, -P.LID_RAIL_Y + 40, P.LID_RAIL_Y - 40, P.LID_TOP_Z + 2, bar_z1 - 5), "ghost"))
    # ---- tent (closed)
    x0, x1 = P.TENT_X0, P.TENT_X0 + P.TENT_L
    hw = P.TENT_W / 2
    zb0 = P.TENT_Z0
    zb1 = zb0 + P.TENT_BASE_H
    zt = zb0 + P.TENT_H - 25
    # underside mounting rails (sit on the bars)
    for s in (1, -1):
        yc = s * P.TENT_UNDER_RAILS_CC / 2
        parts.append(part(f"tent_under_rail_{s}", "tent", box(x0 + 55, x0 + 55 + 1440, yc - 20, yc + 20, zb0, zb0 + 25), "tent_rail"))
    parts.append(part("tent_base", "tent", box(x0, x1, -hw, hw, zb0 + 25, zb1).edges("|Z").fillet(60), "tent_base"))
    prof = [(x0, zb1), (x1, zb1), (x1, zt), (x0 + P.TENT_SLOPE_L, zt), (x0, zb1 + 80)]
    shell = prof_xz(prof, -hw + 10, hw - 10)
    try:
        shell = shell.edges("|Z").fillet(60)
    except Exception:
        pass
    parts.append(part("tent_shell", "tent", shell, "tent", kg=P.TENT_KG))
    # top bars toward the rear (flat part of the shell)
    bx1 = x1 - 120
    bx0 = bx1 - P.TENT_BAR_L
    for s in (1, -1):
        parts.append(part(f"tent_top_bar_{s}", "tent",
                          box(bx0, bx1, s * (P.TENT_BAR_CC / 2 - 15), s * (P.TENT_BAR_CC / 2 + 15), zt, zt + 25), "tent_rail"))
    # 2 x Sunman eArc 100 W on a 3 mm ACM sheet spanning the two top bars
    pl, pw, _ = P.TENT_PANEL
    sx0 = (bx0 + bx1) / 2 - pl / 2
    parts.append(part("tent_solar_backing", "solar", box(sx0 - 10, sx0 + pl + 10, -pw - 10, pw + 10, zt + 25, zt + 28),
                      "solar_frame", fab=True, mat="ACM 3"))
    for i, (ya, yb) in enumerate(((-pw - 2, -2), (2, pw + 2))):
        parts.append(part(f"tent_solar_{i+1}", "solar", box(sx0, sx0 + pl, ya, yb, zt + 28, zt + 31), "solar", kg=2.0, watts=100))
    anchor("tent_pv_jbox", (sx0 + 40, -pw + 40, zt + 28))
    # ---- tent services box: under the tent base, toward the front, inset from the fold-out side
    sv = P.TENT_SERVICES
    s = P.TENT_FOLDOUT_SIDE
    yo = s * (hw - sv["inset"])           # outboard face of the box
    yi = yo - s * sv["w"]
    sx = x0 + sv["x"]
    parts.append(part("tent_services_box", "tent_services", box(sx, sx + sv["d"], yi, yo, zb0 - sv["h"], zb0), "outlet", kg=2.5))
    # faces on the outboard side: 240 V outlet (heater) + 15 A shore inlet
    fz = zb0 - sv["h"] / 2
    parts.append(part("tent_heater_gpo", "tent_services", box(sx + 15, sx + 70, yo, yo + s * 10, fz - 25, fz + 25), "outlet"))
    parts.append(part("tent_shore_inlet", "tent_services", box(sx + 80, sx + 135, yo, yo + s * 10, fz - 25, fz + 25), "anderson_grey"))
    anchor("tent_services", (sx + 10, (yi + yo) / 2, zb0 - 10))
    anchor("tent_front_drop", (x0 + 15, -hw + 120, zb0 - 10))
    return parts
