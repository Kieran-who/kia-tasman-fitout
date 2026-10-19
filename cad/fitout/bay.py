"""
Front battery + inverter bay (between the wheel arches, against the front wall).

Layout across the tub (passenger -> driver):
    [MultiPlus-II 12/3000 flat] [distribution column] [battery 1 on end] [battery 2 on end]
    + charging board (Orion XS, 2 x MPPT) on the front wall ABOVE the inverter, ~140 mm air gap.

Battery bank (optimal for 2 x iTech400X Pro in parallel):
    each battery + -> MRBF 300 A on the terminal -> equal-length 70 mm2 -> bank + busbar
    each battery - -> equal-length 70 mm2 -> bank - busbar -> SmartShunt -> system - busbar
    bank + -> ML-RBS 500 A remote battery switch (controlled from the rear panel) -> system + busbar
    system + -> Class-T 400 A -> 2 x 50 mm2 -> MultiPlus-II ; MIDI fuses -> Orion / MPPTs / rear DC fuse block
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
    z0 = 6
    # ---- frame: base tray, two rear posts, rear top rail; battery cage straps
    parts.append(part("bay_base_tray", g, box(0, d, -hw, hw, 0, z0), "alu", fab=True, mat="Plate 6 5052"))
    for y in (-hw, hw - s):
        parts.append(part(f"bay_rear_post_{int(y)}", g, tube_box(d - s, d, y, y + s, z0, P.BAY_H, axis="Z"), "alu", fab=True, mat=shs))
    parts.append(part("bay_rear_top", g, tube_box(d - s, d, -hw + s, hw - s, P.BAY_H - s, P.BAY_H, axis="Y"), "alu", fab=True, mat=shs))
    # ---- MultiPlus-II lying flat, passenger side, DC/AC terminals toward the distribution column (+Y)
    L, D, H = P.INVERTER
    yq0, yq1 = -hw + 2, -hw + 2 + L
    xq0 = 4
    zq = z0 + 4
    parts.append(part("inverter_charger_multiplus2_3000", "electrical", box(xq0, xq0 + D, yq0, yq1, zq, zq + H), "victron", kg=P.INVERTER_KG))
    parts.append(part("inverter_standoffs", g, box(xq0 + 20, xq0 + D - 20, yq0 + 20, yq1 - 20, z0, zq), "alu_dark", fab=True, mat="Plate 4 5052"))
    parts.append(part("inverter_fan", "electrical", cyl(46, 25, (xq0 + D / 2, yq0 + L / 2, zq + H + 40)), "victron_dark", kg=0.3))
    anchor("inv_dc_pos", (xq0 + D - 50, yq1, zq + 40))
    anchor("inv_dc_neg", (xq0 + D - 110, yq1, zq + 40))
    anchor("inv_ac", (xq0 + 60, yq1, zq + 90))
    anchor("inv_comms", (xq0 + 150, yq1, zq + 110))
    # ---- charging board on the front wall above the inverter (vertical, terminals down)
    zc = P.CHARGE_BOARD_Z
    parts.append(part("charge_board", g, box(0, 6, yq0 + 5, yq1 - 5, zc, P.BAY_H), "alu", fab=True, mat="Plate 6 5052"))
    yb = yq0 + 20
    for nm, dims, kg in (("orion_xs_50a", P.DCDC, 0.4), ("mppt_roof_100_50", P.MPPT_ROOF, 1.3), ("mppt_tent_75_15", P.MPPT_TENT, 0.5)):
        l, t_, h = dims
        parts.append(part(nm, "electrical", box(6, 6 + t_, yb, yb + l, zc + 15, zc + 15 + h), "victron", kg=kg))
        anchor(nm, (6 + t_, yb + l / 2, zc + 15))
        yb += l + 25
    # ---- batteries on end, driver side, terminals facing the rear (+X)
    bw, bd = P.BATT_W, P.BATT_H
    bx0 = 8
    ybs = [hw - 2 - 2 * bw - 10, hw - 2 - bw]
    for i, ya in enumerate(ybs):
        n = i + 1
        parts.append(part(f"battery_{n}", "batteries", box(bx0, bx0 + bd - 15, ya, ya + bw, z0, z0 + P.BATT_L), "battery", kg=P.BATT_KG))
        parts.append(part(f"battery_{n}_band", "batteries", box(bx0 + 40, bx0 + bd - 14, ya - 1, ya + bw + 1, z0 + 300, z0 + 325), "battery_accent"))
        tx = bx0 + bd - 15
        for pol, zt in (("pos", z0 + P.BATT_L - 60), ("neg", z0 + 60)):
            parts.append(part(f"battery_{n}_{pol}", "batteries", cyl(11, 15, (tx + 7, ya + bw / 2, zt), "X"), "copper"))
            anchor(f"batt{n}_{pol}", (tx + 15, ya + bw / 2, zt))
        ml, md, mh = P.MRBF
        zt = z0 + P.BATT_L - 60
        parts.append(part(f"battery_{n}_mrbf", "electrical", box(tx + 15, tx + 15 + mh, ya + bw / 2 - md / 2, ya + bw / 2 + md / 2,
                                                                  zt - ml / 2, zt + ml / 2), "fuse", kg=0.1))
        anchor(f"batt{n}_pos", (tx + 15 + mh, ya + bw / 2, zt))
        for zz in (z0 + 150, z0 + 420):   # cage straps (flat bar) tied to the rear posts and front-wall brackets
            parts.append(part(f"battery_{n}_strap_{zz}", g, box(bx0 - 3, bx0 + bd - 12, ya - 3, ya + bw + 3, zz, zz + 40).cut(
                box(bx0, bx0 + bd - 15, ya, ya + bw, zz - 1, zz + 41)), "alu_dark", fab=True, mat="Flat 50x6 6060"))
    # ---- distribution column between the inverter and battery 1 (components on a board, facing +Y)
    yd0 = yq1 + 8
    parts.append(part("dist_board", g, box(30, d - 34, yd0, yd0 + 6, z0, P.BAY_H - 10), "alu", fab=True, mat="Plate 6 5052"))
    yf = yd0 + 6

    def comp(name, x0, x1, z_0, z_1, depth, col, kg, anchors=()):
        parts.append(part(name, "electrical", box(x0, x1, yf, yf + depth, z_0, z_1), col, kg=kg))
        for an, (ax, az) in anchors:
            anchor(an, (ax, yf + depth, az))
    bl, bdp, bh = P.BUSBAR
    comp("busbar_bank_pos", 235, 235 + bh, 320, 320 + bl, bdp, "fuse", 0.6, [("bus_bank_pos", (255, 500))])
    rl, rd, rh = P.RBS
    comp("remote_battery_switch_500a", 105, 105 + rd, 400, 400 + rh, 60, "victron_dark", 0.9, [("rbs_in", (190, 470)), ("rbs_out", (125, 410))])
    comp("busbar_sys_pos", 235, 235 + bh, 90, 90 + bl, bdp, "fuse", 0.6, [("bus_sys_pos", (255, 270)), ("midi_fuses", (255, 110))])
    ctl, ctd, cth = P.CLASS_T
    comp("class_t_400a", 140, 140 + cth, 230, 230 + ctl, ctd, "fuse", 0.5, [("classT_in", (170, 330)), ("classT_out", (170, 240))])
    comp("busbar_bank_neg", 40, 40 + bh, 300, 300 + bl, bdp, "usb", 0.6, [("bus_bank_neg", (60, 320))])
    sl, sd, sh = P.SHUNT
    comp("smartshunt_500a", 40, 40 + sh, 150, 150 + sl, sd, "victron_dark", 0.2, [("shunt", (60, 260)), ("shunt_sys", (60, 160))])
    comp("busbar_sys_neg", 110, 110 + 120, 40, 40 + bh, bdp, "usb", 0.5, [("bus_sys_neg", (130, 60))])
    # ---- guard on the bay's rear face (protects terminals from slide cargo)
    parts.append(part("bay_guard", "bay_cover", box(d - 2, d, -hw + s, hw - s, 160, P.BAY_H - s), "cover", fab=True, mat="Sheet 1.6 5005"))
    return parts
