"""
Windscreen "visor" solar panel (v0.11).

Stowed: the panel lies flat in the ~70 mm layer between the roof skin and the platform frame, hinged at its rear edge
to a carriage that runs on two aluminium profile guide rails hung under the platform (one each side, inside the
platform mount towers). Deploying (vehicle parked, one button):
    1. the front stow latches release,
    2. a 12 V worm gearmotor at the rear of the platform drives both carriages forward together by toothed belts on a
       common cross shaft (no racking); the hinge arms carry the hinge ~70 mm ahead of the windscreen header,
    3. two self-locking worm-drive rotary actuators at the hinge ends tilt the panel down to TILT (20 deg);
       a mechanical hard stop at TILT_MAX (22 deg) keeps > 100 mm off the bonnet even if an actuator fails.
Stowing reverses it and the latches drop in. Limit switches at every end position; motor current trips on obstruction.
"""
import cadquery as cq

import params as P

from .core import anchor, box, cyl, part
from .vehicle import _fillet, comp

G = "visor"
V = P.VISOR
CELL = (22, 36, 72, 255)
GRIDC = (170, 180, 196, 255)
ACT = (40, 42, 46, 255)

CLASH_ALLOW = [("visor_rail", "visor_strap"), ("visor_rail", "visor_carriage"), ("visor_carriage", "visor_hinge_beam"),
               ("visor_hinge_beam", "visor_panel"), ("visor_tilt_drive", "visor_hinge_beam"), ("visor_tilt_drive", "visor_panel"),
               ("visor_strap", "plat_"), ("visor_drive", "visor_rail"), ("visor_drive", "visor_strap"), ("visor_latch", "visor_rail"),
               ("visor_belt", "visor_rail"), ("visor_latch", "visor_panel"), ("visor_belt", "visor_carriage"), ("visor_belt", "visor_drive")]


def _rot(w, xh, zh, deg):
    """Tilt the front (-X) of a shape down by deg about the hinge axis (parallel to Y) at (xh, zh)."""
    return w.rotate((xh, 0, zh), (xh, 1, zh), -deg) if deg else w


def visor(state="travel"):
    parts = []
    x0, x1 = P.PLAT_X0, P.PLAT_X0 + P.PLAT_L
    zf = P.PLAT_Z                                 # platform frame underside
    L, W, T = V["L"], V["W"], V["T"]
    ry, rw, rh = V["rail_y"], V["rail_w"], V["rail_h"]
    zs0, zs1 = zf - 5, zf                         # hanger straps under the frame
    zr0, zr1 = zs0 - rh, zs0                      # guide rails under the straps
    zh = V["hinge_z"]
    deployed = state == "camp"
    # ---- hanger straps (front + rear end beams, one mid strap under the side rails) and the two guide rails
    straps = [box(xs - 20, xs + 20, -P.PLAT_W / 2, P.PLAT_W / 2, zs0, zs1) for xs in (x0 + 25, (x0 + x1) / 2, x1 - 25)]
    parts.append(part("visor_straps", G, comp(straps), "alu", fab=True, mat="Flat 40x5 6060"))
    rx0, rx1 = x0 + 5, x1 - 5
    for s in (1, -1):
        rail = box(rx0, rx1, s * ry - rw / 2, s * ry + rw / 2, zr0, zr1).cut(box(rx0 - 1, rx1 + 1, s * ry - 9, s * ry + 9, zr0 - 1, zr0 + 8))
        parts.append(part(f"visor_rail_{s}", G, rail, "runner", kg=2.4, note="aluminium profile guide rail ~1.7 m, roller carriages"))
    # ---- carriage position: stowed at the rear, deployed at the front of the rails
    cl = V["car_l"]
    cx = (rx1 - cl / 2) if not deployed else (rx0 + cl / 2)
    xh = cx - V["arm"]                            # hinge axis x (panel rear edge)
    for s in (1, -1):
        parts.append(part(f"visor_carriage_{s}", G, box(cx - cl / 2, cx + cl / 2, s * ry - rw / 2, s * ry + rw / 2, zr0 - 15, zr0),
                          "alu_dark", kg=0.6))
    # hinge beam: cross tube behind the hinge + two arms forward to the hinge knuckles
    zb0, zb1 = zh - 24, zr0 - 15
    beam = box(cx - 20, cx + 20, -ry - rw / 2, ry + rw / 2, zb0, zb1)
    arms = [box(xh, cx, min(s * (W / 2 + 4), s * (W / 2 + 26)), max(s * (W / 2 + 4), s * (W / 2 + 26)), zb0, zb1) for s in (1, -1)]
    parts.append(part("visor_hinge_beam", G, comp([beam] + arms), "alu_dark", fab=True, mat="RHS 50x25x2 6060"))
    # ---- panel (cells on a honeycomb sandwich with an alu edge frame), hinged at its rear-top edge
    tilt = V["tilt"] if deployed else 0
    pan = box(xh - L, xh, -W / 2, W / 2, zh - T, zh)
    frame = pan.cut(box(xh - L + 18, xh - 18, -W / 2 + 18, W / 2 - 18, zh - T - 1, zh + 1))
    cells = box(xh - L + 22, xh - 22, -W / 2 + 22, W / 2 - 22, zh - 3, zh - 0.5)
    lines = [box(xh - L + 22, xh - 22, y - 0.8, y + 0.8, zh - 0.6, zh - 0.2) for y in range(-W // 2 + 22 + 120, W // 2 - 22, 120)]
    lines += [box(x - 0.8, x + 0.8, -W / 2 + 22, W / 2 - 22, zh - 0.6, zh - 0.2) for x in range(int(xh - L + 22 + 160), int(xh - 22), 160)]
    core = box(xh - L + 18, xh - 18, -W / 2 + 18, W / 2 - 18, zh - T + 2, zh - 3)
    parts.append(part("visor_panel", "solar", _rot(core.union(cells), xh, zh, tilt), CELL, kg=V["kg"], watts=V["watts"]))
    parts.append(part("visor_panel_frame", "solar", _rot(frame, xh, zh, tilt), "solar_frame"))
    parts.append(part("visor_panel_grid", "solar", _rot(comp(lines), xh, zh, tilt), GRIDC))
    bump = box(xh - L - 12, xh - L, -W / 2, W / 2, zh - T, zh)        # rubber bump strip on the front edge
    parts.append(part("visor_panel_bumper", "solar", _rot(bump, xh, zh, tilt), "trim"))
    anchor("visor_pv", (xh - 60, 0, zh - T))
    # ---- tilt: worm-drive rotary actuators on the hinge axis at both ends (self-locking), with the hard-stop lugs
    for s in (1, -1):
        yc = s * (W / 2 + 14)
        drv = cyl(26, 22, (xh, yc, zh - 12), "Y").union(box(xh, xh + 70, yc - 11, yc + 11, zh - 34, zh - 4))
        parts.append(part(f"visor_tilt_drive_{s}", G, drv, ACT, kg=1.4, note="12 V worm-drive rotary actuator, self-locking"))
    # ---- drive: worm gearmotor + cross shaft at the rear, toothed belt along each rail to the carriage
    xm = x1 - 20
    parts.append(part("visor_drive_motor", G, box(xm - 70, xm, -60, 60, zr0 - 12, zr1).union(
        cyl(8, 2 * ry, (xm - 35, 0, zr0 + 4), "Y")), ACT, kg=2.6, note="12 V worm gearmotor + cross shaft, manual hex override"))
    for s in (1, -1):
        parts.append(part(f"visor_belt_{s}", G, box(rx0 + 10, rx1 - 10, s * ry - 7, s * ry + 7, zr0 - 3, zr0), "rack", kg=0.3))
    # ---- front stow latches (electric, engage the panel's front corners when stowed)
    for s in (1, -1):
        parts.append(part(f"visor_latch_{s}", G, box(rx0, rx0 + 40, min(s * (W / 2 - 20), s * (ry - rw / 2)),
                                                          max(s * (W / 2 - 20), s * (ry - rw / 2)), zr0 - 10, zr0), ACT, kg=0.2))
    # ---- U11 controller: IP66 box between the passenger guide rail and the roof rail, ahead of the rear strap (v0.13).
    # Cable entries: rear face (feeds from the end-member loom), inboard face (visor chain from the panel)
    ux0, ux1, uy0, uy1 = x1 - 190, x1 - 55, -ry - 118, -ry - 43
    parts.append(part("visor_controller_box", G, box(ux0, ux1, uy0, uy1, P.ROOF_Z + 6, zf - 6), "victron_dark", kg=1.2,
                      note="U11: IP66 box, PLC + 2 x dual H-bridge, per-channel fuses"))
    anchor("visor_ctrl", (ux1, (uy0 + uy1) / 2, P.ROOF_Z + 40))
    anchor("visor_ctrl_side", ((ux0 + ux1) / 2, uy1, P.ROOF_Z + 35))
    anchor("visor_pv_rear", (xh - 30, -W / 2 + 30, zh - T - 7))           # panel junction box, under the rear corner
    return parts
