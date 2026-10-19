"""Side pockets: passenger power cabinet + charging board, driver utility storage."""
import params as P

from .core import anchor, box, cyl, part

T = 12  # ply thickness for carcasses


def passenger():
    parts = []
    g = "power_cabinet"
    yo, yi = -P.POCKET_Y_OUT, -P.POCKET_Y_IN          # outer (wall) / inner (slide side)
    x0 = P.POCKET_X0
    xr = P.TUB_L - P.TAIL_BULGE_L - 6                 # outlet panel sits in front of the tail-light bulge
    zt = P.TOP_Z
    # ---- power cabinet carcass (12 mm ply): inner wall, front, top, bottom; outer side is the tub wall
    parts.append(part("pc_inner_wall", g, box(x0, xr, yi, yi - T, 0, zt), "ply", fab=True, mat="Ply 12 marine"))
    parts.append(part("pc_front", g, box(x0, x0 + T, yo, yi - T, 0, zt), "ply", fab=True, mat="Ply 12 marine"))
    parts.append(part("pc_top", g, box(x0, xr, yo, yi, zt - T, zt), "ply", fab=True, mat="Ply 12 marine"))
    parts.append(part("pc_bottom", g, box(x0 + T, xr, yo, yi - T, 0, T), "ply", fab=True, mat="Ply 12 marine"))
    parts.append(part("pc_outlet_panel", g, box(xr - 3, xr, yo, yi, T, zt - T), "alu", fab=True, mat="Plate 3 5052"))
    fx = xr
    ym = (yo + yi) / 2

    def face(n, col, y0, y1, z0, z1, kg):
        parts.append(part(n, g, box(fx - 16, fx + 2, y0, y1, z0, z1), col, kg=kg))   # flush-mounted
        anchor(n, (fx - 20, (y0 + y1) / 2, (z0 + z1) / 2))
    face("pc_gx_touch_50", "victron_dark", ym - 64, ym + 64, 400, 487, 0.3)
    face("pc_usbc", "usb", yo + 22, yo + 72, 340, 385, 0.05)
    parts.append(part("pc_12v", g, cyl(18, 18, (fx - 7, yi - 45, 362), "X"), "usb", kg=0.05))
    face("pc_gpo_1", "outlet", ym - 50, ym + 50, 225, 330, 0.4)
    face("pc_gpo_2", "outlet", ym - 50, ym + 50, 115, 220, 0.4)
    face("pc_anderson_1", "anderson", yo + 15, ym - 6, 28, 100, 0.1)
    face("pc_anderson_2", "anderson", ym + 6, yi - 15, 28, 100, 0.1)
    # inside the cabinet: RCBO enclosure, Cerbo GX, cable gland plate at the factory outlet hole
    parts.append(part("pc_rcbo_enclosure", "electrical", box(xr - 300, xr - 160, yo + 25, yi - 20, 260, 440), "outlet", kg=1.5))
    anchor("rcbo", (xr - 230, yi - 20, 350))
    cl, ct, ch = P.CERBO
    parts.append(part("cerbo_gx", "electrical", box(xr - 470, xr - 470 + cl, yi - T - ct, yi - T, 300, 300 + ch), "victron_dark", kg=0.4))
    anchor("cerbo", (xr - 470 + cl / 2, yi - T - ct, 300))
    # plug clearance zone behind the panel (plugs stay inside the tub with the tailgate shut)
    parts.append(part("pc_plug_zone", "future", box(xr, P.TUB_L - 4, yo + P.TAIL_BULGE_IN + 2, yi, T, zt - T), "ghost"))

    # ---- charging board above the passenger arch (vertical ply board on the tub wall + vented cover)
    zb = P.ARCH_H + 6
    xa0, xa1 = 10, P.ARCH_L - 10
    parts.append(part("charge_board", g, box(xa0, xa1, yo, yo + T, zb, zt), "ply", fab=True, mat="Ply 12 marine"))
    parts.append(part("charge_board_shelf", g, box(xa0, xa1, yo, yi, zb - 6, zb), "alu", fab=True, mat="Plate 6 5052"))
    parts.append(part("charge_board_cover", "bay_cover", box(xa0, xa1, yi - 2, yi, zb, zt).union(box(xa0, xa1, yo, yi, zt - 2, zt)),
                      "cover", fab=True, mat="Sheet 1.6 5005"))
    xb = xa0 + 25
    yb0 = yo + T
    for nm, dims, col, kg in (("orion_xs_50a", P.DCDC, "victron", 0.4), ("mppt_roof_100_50", P.MPPT_ROOF, "victron", 1.3),
                              ("mppt_tent_75_15", P.MPPT_TENT, "victron", 0.5), ("dc_fuse_block", P.FUSE_BLOCK, "fuse", 0.6)):
        l, t_, h = dims
        z0 = zb + 15
        parts.append(part(nm, "electrical", box(xb, xb + l, yb0, yb0 + t_, z0, z0 + h), col, kg=kg))
        anchor(nm, (xb + l / 2, yb0 + t_, z0))
        xb += l + 35
    return parts


def driver(drawer_out=0.0):
    """Always-in-the-car utility storage (replaces the water tank)."""
    parts = []
    g = "utility"
    yi, yo = P.POCKET_Y_IN, P.POCKET_Y_OUT
    x0 = P.POCKET_X0
    xr = P.TUB_L - P.TAIL_BULGE_L - 6
    zt = P.TOP_Z
    # carcass
    parts.append(part("ut_inner_wall", g, box(x0, xr, yi, yi + T, 0, zt), "ply", fab=True, mat="Ply 12 marine"))
    parts.append(part("ut_front", g, box(x0, x0 + T, yi + T, yo, 0, zt), "ply", fab=True, mat="Ply 12 marine"))
    parts.append(part("ut_top", g, box(x0, xr, yi, yo, zt - T, zt), "ply", fab=True, mat="Ply 12 marine"))
    # pull-out utility drawer (pulls rearward, tailgate down). Its width clears the tail-light bulge [EST - measure];
    # without the bulge it can grow to the full pocket width. Runs on a pair of under-mount runners.
    dw0, dw1 = yi + T + 6, yo - P.TAIL_BULGE_IN - 6
    dl = 480
    dx1 = xr + drawer_out
    dx0 = dx1 - dl
    parts.append(part("ut_drawer_box", g, box(dx0, dx1 - 15, dw0, dw1, 26, zt - T - 8).cut(
        box(dx0 + 9, dx1 - 24, dw0 + 9, dw1 - 9, 35, zt)), "ply", fab=True, mat="Ply 9 marine"))
    parts.append(part("ut_drawer_front", g, box(dx1 - 15, dx1 + 3, dw0 - 4, dw1 + 4, 22, zt - T - 4), "alu_dark", fab=True, mat="Plate 3 5052"))
    parts.append(part("ut_drawer_handle", g, box(dx1 + 3, dx1 + 25, (dw0 + dw1) / 2 - 35, (dw0 + dw1) / 2 + 35, zt - 90, zt - 70), "alu", kg=0.1))
    for k, z in enumerate((170, 320)):
        parts.append(part(f"ut_drawer_shelf_{k}", g, box(dx0 + 9, dx1 - 24, dw0 + 9, dw1 - 9, z, z + 9), "ply", fab=True, mat="Ply 9 marine"))
    for k, yy in enumerate((dw0 + 15, dw1 - 45)):
        parts.append(part(f"ut_drawer_runner_{k}", g, box(xr - dl, dx1 - 15, yy, yy + 30, 4, 24), "runner", kg=1.0))
    # behind the drawer (toward the arch): fixed open bay for long/soft items (straps, tarps, ratchets)
    parts.append(part("ut_divider", g, box(xr - dl - T, xr - dl, yi + T, yo, 0, zt - T), "ply", fab=True, mat="Ply 12 marine"))
    # over-arch gear tray with dividers + strap pegs (lid access)
    zb = P.ARCH_H + 6
    parts.append(part("ut_arch_tray", g, box(10, P.ARCH_L - 10, yi, yo, zb - 6, zb), "alu", fab=True, mat="Plate 3 5052"))
    parts.append(part("ut_arch_tray_lip", g, box(10, P.ARCH_L - 10, yi, yi + 3, zb, zb + 90), "alu", fab=True, mat="Plate 3 5052"))
    for k, x in enumerate((220, 440, 640)):
        parts.append(part(f"ut_tray_divider_{k}", g, box(x, x + 3, yi + 3, yo, zb, zb + 90), "alu", fab=True, mat="Plate 3 5052"))
    for k, x in enumerate((60, 120, 180)):
        parts.append(part(f"ut_strap_peg_{k}", g, cyl(10, 60, (x, yo - 30, zb + 30)), "alu_dark", kg=0.05))
    # example contents (payload)
    for k, x in enumerate((60, 120, 180)):
        parts.append(part(f"ut_strap_roll_{k}", "payload", cyl(28, 45, (x, yo - 30, zb + 25)), "strap", kg=0.6))
    return parts
