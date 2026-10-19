"""Tub (factory liner) and a simplified vehicle body for context."""
import params as P

from .core import anchor, box, cyl, part, prof_xz, union_all


def tub(tailgate_open=False):
    parts = []
    hw = P.TUB_W / 2
    ow = hw + P.TUB_WALL_T
    # floor: liner base at -RIB_H with fore-aft ribs whose tops are Z = 0
    parts.append(part("tub_floor", "vehicle", box(-P.TUB_WALL_T, P.TUB_L, -ow, ow, -25, -P.RIB_H), "liner"))
    n = int(P.ARCH_GAP // P.RIB_PITCH)
    y0 = -(n - 1) * P.RIB_PITCH / 2
    ribs = union_all(box(0, P.TUB_L - 20, y0 + i * P.RIB_PITCH - P.RIB_W / 2, y0 + i * P.RIB_PITCH + P.RIB_W / 2,
                         -P.RIB_H, 0).edges("|X").fillet(4) for i in range(n))
    parts.append(part("tub_floor_ribs", "vehicle", ribs, "liner_rib"))
    for s, nm in ((1, "driver"), (-1, "passenger")):
        wall = box(-P.TUB_WALL_T, P.TUB_L, s * hw, s * ow, -25, P.TUB_D)
        parts.append(part(f"tub_wall_{nm}", "vehicle", wall, "liner"))
        # wheel arch: box from the front wall, rounded top inboard edge and rear edge
        arch = (box(0, P.ARCH_L, s * P.ARCH_GAP / 2, s * hw, -P.RIB_H, P.ARCH_H)
                .edges("|X").edges(">Z").edges("<Y" if s > 0 else ">Y").fillet(P.ARCH_R)
                .edges("|Y").edges(">X").edges(">Z").fillet(P.ARCH_R))
        parts.append(part(f"wheel_arch_{nm}", "vehicle", arch, "liner"))
        # tail-light housing bulge at the rear corner
        if P.TAIL_BULGE_L and P.TAIL_BULGE_IN:
            bul = box(P.TUB_L - P.TAIL_BULGE_L, P.TUB_L, s * hw, s * (hw - P.TAIL_BULGE_IN), -P.RIB_H, P.TUB_D - 30)
            parts.append(part(f"tail_bulge_{nm}", "vehicle", bul.edges("|Z").fillet(25), "liner"))
        # body skin + rail cap
        parts.append(part(f"tub_skin_{nm}", "vehicle",
                          box(-P.TUB_WALL_T, P.TUB_L + P.TAILGATE_T, s * ow, s * (ow + 30), -330, P.TUB_D - 10), "body"))
        parts.append(part(f"tub_rail_{nm}", "vehicle",
                          box(-P.TUB_WALL_T, P.TUB_L + P.TAILGATE_T, s * (hw - 5), s * (ow + 30), P.TUB_D - 10, P.TUB_D), "trim"))
    parts.append(part("tub_front_wall", "vehicle", box(-P.TUB_WALL_T, 0, -hw, hw, -25, P.TUB_D), "liner"))
    # factory bed hooks
    for i, (x, s, z) in enumerate(P.BED_HOOKS):
        y = s * (P.ARCH_GAP / 2 if x < P.ARCH_L else hw)
        hook = box(x - 25, x + 25, y, y - s * 18, z - 30, z + 10).union(box(x - 25, x + 25, y - s * 18, y - s * 26, z - 30, z - 18))
        parts.append(part(f"bed_hook_{i+1}", "vehicle", hook, "alu_dark"))
    # factory 240 V outlet (to be removed; its hole becomes the cable gland plate)
    fx, fs, fz = P.FACTORY_OUTLET
    parts.append(part("factory_outlet_gland_plate", "markers", box(fx - 60, fx + 60, fs * hw, fs * (hw - 6), fz - 45, fz + 45), "kia_outlet"))
    anchor("exit_inside", (fx, fs * (hw - 10), fz))
    anchor("exit_outside", (fx, fs * (ow + 10), fz))
    # tailgate
    if tailgate_open:
        tg = box(P.TUB_L + 10, P.TUB_L + 10 + P.TAILGATE_H, -hw + 20, hw - 20, -P.TAILGATE_T - 5, -5)
    else:
        tg = box(P.TUB_L, P.TUB_L + P.TAILGATE_T, -hw + 20, hw - 20, -25, P.TUB_D - 10)
    parts.append(part("tailgate", "vehicle", tg, "body"))
    return parts


def body_context():
    parts = []
    hw = P.TUB_W / 2
    ow = hw + P.TUB_WALL_T
    zg = -P.FLOOR_ABOVE_GROUND
    parts.append(part("rear_bumper", "vehicle", box(P.TUB_L - 40, P.TUB_L + 130, -ow - 30, ow + 30, -470, -300), "trim"))
    parts.append(part("tub_underside", "vehicle", box(-P.TUB_WALL_T, P.TUB_L + P.TAILGATE_T, -ow, ow, -330, -25), "liner"))
    # chassis rails (context for cable routing)
    for s in (1, -1):
        parts.append(part(f"chassis_rail_{s}", "vehicle",
                          box(-3400, P.TUB_L, s * (P.CHASSIS_RAIL_Y - 30), s * (P.CHASSIS_RAIL_Y + 30), P.CHASSIS_Z - 180, P.CHASSIS_Z), "trim"))
    cw = 905
    pts = [(P.CAB_REAR_X, -470), (P.CAB_REAR_X, P.ROOF_Z), (P.CAB_FRONT_X, P.ROOF_Z), (-2450, 420),
           (-3650, 330), (-3720, -100), (-3700, -470)]
    parts.append(part("cab_body", "vehicle", prof_xz(pts, -cw, cw), "body"))
    glass = [(P.CAB_REAR_X + 5, 450), (P.CAB_REAR_X + 5, P.ROOF_Z - 60), (P.CAB_FRONT_X - 20, P.ROOF_Z - 60), (-2400, 440)]
    parts.append(part("cab_glass", "vehicle", prof_xz(glass, -cw - 3, cw + 3), "glass"))
    for s in (1, -1):
        parts.append(part(f"roof_rail_{s}", "vehicle",
                          box(P.CAB_FRONT_X + 60, P.CAB_REAR_X - 120, s * 640, s * 690, P.ROOF_Z, P.ROOF_Z + 40), "trim"))
    for x in (P.REAR_AXLE_X, P.REAR_AXLE_X - P.WHEELBASE):
        for s in (1, -1):
            parts.append(part(f"wheel_{int(x)}_{s}", "vehicle", cyl(P.TYRE_D / 2, P.TYRE_W, (x, s * 805, zg + P.TYRE_D / 2), "Y"), "tyre"))
    # context markers: start battery + under-seat outlet box
    bx, by, bz = P.ENGINE_BAY_BATT
    parts.append(part("start_battery", "markers", box(bx - 130, bx + 130, by - 90, by + 90, bz - 100, bz + 100), "battery"))
    anchor("start_battery", (bx, by, bz + 100))
    cx, cy, cz = P.CABIN_SEAT_BOX
    parts.append(part("cabin_outlet_box", "markers", box(cx - 60, cx + 60, cy - 110, cy + 110, cz - 50, cz + 50), "marker"))
    anchor("cabin_outlets", (cx, cy, cz - 50))
    return parts
