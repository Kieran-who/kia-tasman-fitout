"""
Side pockets. The load lid can't be opened with the tent on, so everything is reached from the tailgate:

passenger: LOWER power/control cabinet behind the arch (rear panel = controls + outlets, hinged to reach
           RCBOs / DC fuses / Cerbo) + UPPER long drawer over the arch (pulls out the back) + cable tray above it
driver:    LOWER pull-out utility drawer behind the arch + UPPER long drawer over the arch
"""
import params as P

from .core import anchor, box, cyl, part

T = 12   # carcass ply
T9 = 9
RUN = 13  # light-duty side runner thickness


def _upper_drawer(yo, yi, ext, gap=0.0):
    """Full-length drawer over the arch. yo = wall side, yi = inboard side (signed)."""
    s = 1 if yi > 0 else -1
    g = "utility" if s > 0 else "power_cabinet"
    nm = "ud_driver" if s > 0 else "ud_pass"
    parts = []
    x0, x1 = 5, P.POCKET_X1
    z0, z1 = P.UPPER_Z0, P.UPPER_Z1
    # carcass: floor (spans the arch top and the lower unit), inboard wall, wall-side runner panel
    parts.append(part(f"{nm}_floor", g, box(x0, x1, yo, yi, z0, z0 + T9), "ply", fab=True, mat="Ply 9 marine"))
    parts.append(part(f"{nm}_inner_wall", g, box(x0, x1, yi, yi + s * T, z0 + T9, z1), "ply", fab=True, mat="Ply 12 marine"))
    yp = yo - s * gap
    parts.append(part(f"{nm}_runner_panel", g, box(x0, x1, yp, yp - s * T9, z0 + T9, z1), "ply", fab=True, mat="Ply 9 marine"))
    # drawer box (open top, dividers) on a pair of 48" light-duty runners
    ya = yp - s * (T9 + RUN)
    yb = yi + s * (T + RUN)
    dl = x1 - x0 - 30
    dx1 = x1 + ext
    dx0 = dx1 - dl
    zb0, zb1 = z0 + T9 + 4, z1 - 6
    box_ = box(dx0, dx1 - 15, ya, yb, zb0, zb1).cut(box(dx0 + T9, dx1 - 15 - T9, ya - s * T9, yb + s * T9, zb0 + T9, zb1 + 1))
    parts.append(part(f"{nm}_box", g, box_, "ply", fab=True, mat="Ply 9 marine"))
    for k, xd in enumerate((dx0 + 380, dx0 + 760, dx0 + 1100)):
        parts.append(part(f"{nm}_divider_{k}", g, box(xd, xd + T9, ya - s * T9, yb + s * T9, zb0 + T9, zb1 - 40), "ply", fab=True, mat="Ply 9 marine"))
    parts.append(part(f"{nm}_front", g, box(dx1 - 15, dx1 + 3, ya + s * 6, yb - s * 6, zb0 - 2, zb1), "alu_dark", fab=True, mat="Plate 3 5052"))
    yc = (ya + yb) / 2
    parts.append(part(f"{nm}_pull", g, box(dx1 - 1, dx1 + 4, yc - 40, yc + 40, zb1 - 50, zb1 - 25), "alu", kg=0.1))
    for k, (yy, dy) in enumerate(((ya, s * RUN), (yb, -s * RUN))):
        parts.append(part(f"{nm}_runner_{k}", g, box(x0 + 10, x0 + 10 + 1219 + ext * 0.5, yy, yy + dy, zb0 + 40, zb0 + 85), "runner", kg=1.6))
    return parts


def passenger(drawer_out=0.0):
    parts = []
    g = "power_cabinet"
    yo, yi = -P.POCKET_Y_OUT, -P.POCKET_Y_IN
    x0 = P.POCKET_X0
    xr = P.REAR_PANEL_X
    zt = P.LOWER_TOP_Z
    # ---- lower power/control cabinet (floor -> arch height)
    parts.append(part("pc_inner_wall", g, box(x0, xr, yi, yi - T, 0, zt), "ply", fab=True, mat="Ply 12 marine"))
    parts.append(part("pc_front", g, box(x0, x0 + T, yo, yi - T, 0, zt), "ply", fab=True, mat="Ply 12 marine"))
    parts.append(part("pc_top", g, box(x0, xr, yo, yi, zt - T, zt), "ply", fab=True, mat="Ply 12 marine"))
    parts.append(part("pc_bottom", g, box(x0 + T, xr, yo, yi - T, 0, T), "ply", fab=True, mat="Ply 12 marine"))
    # rear panel = hinged door (bottom hinge): controls + outlets on its face; RCBOs, DC fuses, Cerbo behind it
    parts.append(part("pc_door", g, box(xr - 3, xr, yo + 2, yi - 2, T, zt - T), "alu", fab=True, mat="Plate 3 5052"))
    parts.append(part("pc_door_hinge", g, cyl(5, 170, (xr + 2, (yo + yi) / 2, T + 4), "Y"), "alu_dark", kg=0.1))
    fx = xr

    def face(n, col, y0, y1, z0, z1, kg):
        parts.append(part(n, g, box(fx - 16, fx + 2, y0, y1, z0, z1), col, kg=kg))   # flush-mounted
        anchor(n, (fx - 30, (y0 + y1) / 2, (z0 + z1) / 2))

    def knob(n, col, y, z, r, kg):
        parts.append(part(n, g, cyl(r, 18, (fx - 7, y, z), "X"), col, kg=kg))
        anchor(n, (fx - 30, y, z))
    face("pc_gx_touch_50", "victron_dark", yo + 10, yo + 138, 188, 275, 0.3)
    knob("pc_sw_battery", "fuse", yi - 28, 252, 14, 0.05)        # remote battery switch ON/OFF (ML-RBS)
    knob("pc_sw_inverter", "victron", yi - 28, 208, 14, 0.05)    # MultiPlus remote on/off
    face("pc_gpo_double", "outlet", yo + 10, yo + 130, 92, 178, 0.5)
    knob("pc_usbc", "usb", yi - 30, 155, 15, 0.05)
    knob("pc_12v", "usb", yi - 30, 112, 17, 0.05)
    face("pc_anderson_1", "anderson", yo + 10, yo + 82, 18, 84, 0.1)
    face("pc_anderson_2", "anderson", yo + 92, yo + 164, 18, 84, 0.1)
    # behind the door
    parts.append(part("pc_rcbo_enclosure", "electrical", box(xr - 157, xr - 19, yi - T - 120, yi - T, 60, 250), "outlet", kg=1.2))
    anchor("rcbo", (xr - 90, yi - T - 120, 200))
    fl, ft, fh = P.FUSE_BLOCK
    parts.append(part("dc_fuse_block", "electrical", box(xr - 372, xr - 372 + fl, yi - T - ft, yi - T, 70, 70 + fh), "fuse", kg=0.6))
    anchor("dc_fuse_block", (xr - 372 + fl / 2, yi - T - ft, 70 + fh))
    cl, ct, ch = P.CERBO
    parts.append(part("cerbo_gx", "electrical", box(x0 + 14, x0 + 14 + cl, yi - T - ct, yi - T, 150, 150 + ch), "victron_dark", kg=0.4))
    anchor("cerbo", (x0 + 14 + cl / 2, yi - T - ct, 150 + ch))
    parts.append(part("pc_plug_zone", "future", box(xr, P.TUB_L - 4, yo + 2, yi, T, zt - T), "ghost"))
    # ---- upper long drawer with a cable channel behind it (gland drop) + cable tray above it
    parts += _upper_drawer(yo, yi, drawer_out, gap=P.CABLE_GAP)
    parts.append(part("cable_tray", g, box(20, 1400, yo, yo + 90, P.UPPER_Z1 + 2, P.UPPER_Z1 + 5).union(
        box(20, 1400, yo + 87, yo + 90, P.UPPER_Z1 + 2, P.UPPER_Z1 + 25)), "alu", fab=True, mat="Plate 3 5052"))
    return parts


def driver(drawer_out=0.0, upper_out=0.0):
    """Always-in-the-car utility storage: lower pull-out drawer + upper long drawer."""
    parts = []
    g = "utility"
    yi, yo = P.POCKET_Y_IN, P.POCKET_Y_OUT
    x0 = P.POCKET_X0
    zt = P.LOWER_TOP_Z
    xr = P.POCKET_X1
    parts.append(part("ut_inner_wall", g, box(x0, xr, yi, yi + T, 0, zt), "ply", fab=True, mat="Ply 12 marine"))
    parts.append(part("ut_front", g, box(x0, x0 + T, yi + T, yo, 0, zt), "ply", fab=True, mat="Ply 12 marine"))
    parts.append(part("ut_top", g, box(x0, xr, yi, yo, zt - T, zt), "ply", fab=True, mat="Ply 12 marine"))
    dw0, dw1 = yi + T + RUN, yo - RUN
    dl = xr - x0 - T - 20
    dx1 = xr + drawer_out
    dx0 = dx1 - dl
    parts.append(part("ut_drawer_box", g, box(dx0, dx1 - 15, dw0, dw1, 8, zt - T - 6).cut(
        box(dx0 + T9, dx1 - 15 - T9, dw0 + T9, dw1 - T9, 8 + T9, zt)), "ply", fab=True, mat="Ply 9 marine"))
    parts.append(part("ut_drawer_front", g, box(dx1 - 15, dx1 + 3, dw0 - 8, dw1 + 8, 6, zt - T - 3), "alu_dark", fab=True, mat="Plate 3 5052"))
    parts.append(part("ut_drawer_pull", g, box(dx1 - 1, dx1 + 4, (dw0 + dw1) / 2 - 40, (dw0 + dw1) / 2 + 40, zt - 70, zt - 45), "alu", kg=0.1))
    parts.append(part("ut_drawer_divider", g, box(dx0 + 300, dx0 + 309, dw0 + T9, dw1 - T9, 8 + T9, zt - 60), "ply", fab=True, mat="Ply 9 marine"))
    for k, yy in enumerate((dw0 - RUN, dw1)):
        parts.append(part(f"ut_drawer_runner_{k}", g, box(x0 + T + 5, x0 + T + 5 + 560 + drawer_out * 0.5, yy, yy + RUN, 120, 165), "runner", kg=1.0))
    parts += _upper_drawer(yo, yi, upper_out)
    for k in range(3):   # example contents: strap rolls in the upper drawer
        x = P.POCKET_X1 - 120 - k * 90 + upper_out
        parts.append(part(f"ud_strap_roll_{k}", "payload", cyl(38, 50, (x, (yi + yo) / 2, P.UPPER_Z0 + 50)), "strap", kg=0.6))
    return parts
