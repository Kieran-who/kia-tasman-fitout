"""
Front battery + inverter bay (between the wheel arches, against the front wall).

Layout across the tub (passenger -> driver):
    [Quattro 12/5000 lying flat] [distribution column] [battery 1 on end] [battery 2 on end]
The Quattro sits beside the batteries, never above them (Victron requirement). Battery terminals
face the rear so they, the Class-T fuses and the isolator are reachable with the slides out.
"""
import params as P

from .core import anchor, box, cyl, part, tube_box


def bay():
    parts = []
    hw = P.BAY_W / 2
    d = P.BAY_D
    s = 30
    g = "bay"
    shs = "SHS 30x30x2 6060"
    # frame: base tray, two rear posts, rear top rail, side top rails (front ends bolt to the tub front wall)
    parts.append(part("bay_base_tray", g, box(0, d, -hw, hw, 0, 6), "alu", fab=True, mat="Plate 6 5052"))
    for y in (-hw, hw - s):
        parts.append(part(f"bay_rear_post_{int(y)}", g, tube_box(d - s, d, y, y + s, 6, P.BAY_H, axis="Z"), "alu", fab=True, mat=shs))
        parts.append(part(f"bay_side_top_{int(y)}", g, tube_box(0, d - s, y, y + s, P.BAY_H - s, P.BAY_H, axis="X"), "alu", fab=True, mat=shs))
        parts.append(part(f"bay_front_bracket_{int(y)}", g, box(0, 6, y, y + s, P.BAY_H - 120, P.BAY_H - s), "alu", fab=True, mat="Plate 6 5052"))
    parts.append(part("bay_rear_top", g, tube_box(d - s, d, -hw + s, hw - s, P.BAY_H - s, P.BAY_H, axis="Y"), "alu", fab=True, mat=shs))
    parts.append(part("bay_rear_low", g, tube_box(d - s, d, -40, hw - s, 6, 6 + s, axis="Y"), "alu", fab=True, mat=shs))
    z0 = 6
    # ---- Quattro lying flat on the passenger side, cable face toward the distribution column (+Y)
    L, D, H = P.INVERTER
    yq0 = -hw + s + 2
    yq1 = yq0 + L
    xq0 = 4
    parts.append(part("inverter_charger_quattro_12_5000", "electrical", box(xq0, xq0 + D, yq0, yq1, z0 + 4, z0 + 4 + H), "victron", kg=P.INVERTER_KG))
    parts.append(part("quattro_standoffs", g, box(xq0 + 20, xq0 + D - 20, yq0 + 20, yq1 - 20, z0, z0 + 4), "alu_dark", fab=True, mat="Plate 4 5052"))
    parts.append(part("quattro_fan", "electrical", cyl(46, 25, ((xq0 + D) / 2, yq0 + L / 2, z0 + H + 30)), "victron_dark", kg=0.3))
    anchor("inv_dc_pos", (xq0 + D - 60, yq1, z0 + 60))
    anchor("inv_dc_neg", (xq0 + D - 130, yq1, z0 + 60))
    anchor("inv_ac", (xq0 + 80, yq1, z0 + 120))
    anchor("inv_comms", (xq0 + 170, yq1, z0 + 180))
    # ---- batteries on end, driver side, terminals facing the rear (+X)
    bw, bd = P.BATT_W, P.BATT_H     # footprint: 240 along Y, 235 along X (incl. terminals)
    bx0 = 8
    yb = [hw - s - 4 - 2 * bw - 12, hw - s - 4 - bw]
    for i, ya in enumerate(yb):
        n = i + 1
        parts.append(part(f"battery_{n}", "batteries", box(bx0, bx0 + bd - 15, ya, ya + bw, z0, z0 + P.BATT_L), "battery", kg=P.BATT_KG))
        parts.append(part(f"battery_{n}_band", "batteries", box(bx0 + 40, bx0 + bd - 14, ya - 1, ya + bw + 1, z0 + 300, z0 + 325), "battery_accent"))
        tx = bx0 + bd - 15
        for pol, zt in (("pos", z0 + P.BATT_L - 60), ("neg", z0 + 60)):
            parts.append(part(f"battery_{n}_{pol}", "batteries", cyl(11, 15, (tx + 7, ya + bw / 2, zt), "X"), "copper"))
            anchor(f"batt{n}_{pol}", (tx + 15, ya + bw / 2, zt))
        # hold-down cage straps
        for zz in (z0 + 150, z0 + 420):
            parts.append(part(f"battery_{n}_strap_{zz}", g, box(bx0 - 3, bx0 + bd - 12, ya - 3, ya + bw + 3, zz, zz + 40).cut(
                box(bx0, bx0 + bd - 15, ya, ya + bw, zz - 1, zz + 41)), "alu_dark", fab=True, mat="Flat 50x6 6060"))
    # ---- distribution column between the Quattro and battery 1
    yd0, yd1 = yq1 + 8, yb[0] - 8
    yc = (yd0 + yd1) / 2
    xr = d - s - 6
    parts.append(part("dist_board", g, box(xr - 6, xr, yd0, yd1, z0, P.BAY_H - s), "alu", fab=True, mat="Plate 6 5052"))
    ct_l, ct_d, ct_h = P.CLASS_T
    zz = P.BAY_H - 40 - ct_l
    for i, xx in enumerate((xr - 6 - ct_h, xr - 6 - 2 * ct_h - 10)):
        parts.append(part(f"class_t_400a_{i+1}", "electrical", box(xx, xx + ct_h, yc - ct_d / 2, yc + ct_d / 2, zz, zz + ct_l), "fuse", kg=0.5))
        anchor(f"classT_{i+1}_in", (xx + ct_h / 2, yc + ct_d / 2, zz + ct_l - 10))
        anchor(f"classT_{i+1}_out", (xx + ct_h / 2, yc + ct_d / 2, zz + 10))
    bl, bdp, bh = P.BUSBAR
    parts.append(part("busbar_pos", "electrical", box(xr - 6 - bh, xr - 6, yc - bdp / 2, yc + bdp / 2, z0 + 40, z0 + 40 + bl), "fuse", kg=0.8))
    anchor("bus_pos", (xr - 6 - bh, yc, z0 + 40 + bl - 20))
    anchor("midi_fuses", (xr - 6 - bh, yc, z0 + 60))
    parts.append(part("busbar_neg", "electrical", box(xr - 120 - bh, xr - 120, yc - bdp / 2, yc + bdp / 2, z0 + 20, z0 + 20 + bl), "usb", kg=0.8))
    anchor("bus_neg", (xr - 120 - bh, yc, z0 + 40))
    sl, sd, sh = P.SHUNT
    parts.append(part("smartshunt_1000a", "electrical", box(xr - 120 - bh - sh, xr - 120 - bh, yc - sd / 2, yc + sd / 2, z0 + 300, z0 + 300 + sl),
                      "victron_dark", kg=0.3))
    anchor("shunt", (xr - 120 - bh - sh, yc, z0 + 300 + sl))
    anchor("shunt_sys", (xr - 120 - bh - sh, yc, z0 + 300))
    # ---- isolator on the bay rear face, centred high
    parts.append(part("isolator_plate", g, box(d, d + 5, yc - 70, yc + 70, 300, 470), "alu", fab=True, mat="Plate 4 5052"))
    parts.append(part("battery_isolator_600a", "electrical", cyl(45, 32, (d + 20, yc, 400), "X"), "fuse", kg=0.6))
    anchor("isolator", (d + 5, yc, 400))
    parts.append(part("bay_cover", "bay_cover", box(0, d + 2, -hw - 2, hw + 2, P.BAY_H, P.BAY_H + 3), "cover", fab=True, mat="Sheet 1.6 5005"))
    return parts
