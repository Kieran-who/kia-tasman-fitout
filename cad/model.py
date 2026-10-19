"""
Parametric concept model of the Kia Tasman X-Pro tub fit-out.

Each builder returns a list of Part objects. build.py turns them into GLB (viewer/renders)
and STEP (CAD hand-off). All dimensions come from params.py.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import cadquery as cq

import params as P

# ------------------------------------------------------------------ colours (RGBA 0-255)
C = dict(
    body=(201, 191, 163, 255),       # Tasman sand
    trim=(40, 40, 42, 255),
    tyre=(25, 25, 25, 255),
    liner=(38, 38, 40, 255),
    glass=(60, 70, 80, 200),
    lid=(30, 30, 32, 255),
    tent=(22, 22, 22, 255),
    tent_rail=(55, 55, 58, 255),
    alu=(190, 194, 198, 255),
    alu_dark=(120, 124, 128, 255),
    ply=(214, 182, 134, 255),
    runner=(150, 155, 160, 255),
    battery=(30, 32, 35, 255),
    battery_accent=(240, 120, 20, 255),
    victron=(0, 92, 170, 255),
    victron_dark=(20, 40, 70, 255),
    fuse=(200, 40, 40, 255),
    copper=(196, 120, 60, 255),
    water=(150, 200, 235, 150),
    tank_hw=(230, 230, 230, 255),
    outlet=(240, 240, 240, 255),
    anderson=(210, 30, 30, 255),
    usb=(20, 20, 20, 255),
    cable_red=(200, 30, 30, 255),
    cable_blk=(20, 20, 20, 255),
    cable_240=(245, 130, 30, 255),
    cable_pv=(250, 200, 30, 255),
    solar=(20, 35, 75, 255),
    solar_frame=(170, 175, 180, 255),
    light=(250, 250, 240, 255),
    starlink=(235, 235, 235, 255),
    chain=(60, 60, 60, 255),
    receiver=(50, 50, 52, 255),
    ltrack=(170, 175, 180, 255),
    cover=(90, 95, 100, 90),
    kia_outlet=(255, 90, 0, 255),
    marker=(255, 0, 140, 255),
)


@dataclass
class Part:
    name: str
    group: str
    shape: cq.Shape | None = None          # CadQuery geometry (exported to STEP + GLB)
    color: tuple = (200, 200, 200, 255)
    tube: list | None = None               # polyline for cable routes (GLB only)
    tube_r: float = 6.0
    fab: bool = False                      # True = fabricated by the builder (goes to STEP/cut list)
    meta: dict = field(default_factory=dict)


# ------------------------------------------------------------------ geometry helpers
def box(x0, x1, y0, y1, z0, z1) -> cq.Workplane:
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(r, h, centre, axis="Z") -> cq.Workplane:
    w = cq.Workplane("XY").circle(r).extrude(h).translate((0, 0, -h / 2))
    if axis == "X":
        w = w.rotate((0, 0, 0), (0, 1, 0), 90)
    elif axis == "Y":
        w = w.rotate((0, 0, 0), (1, 0, 0), 90)
    return w.translate(centre)


def prof_xz(points, y0, y1) -> cq.Workplane:
    """Extrude a closed XZ polygon between y0 and y1."""
    w = cq.Workplane("XZ", origin=(0, y1, 0)).polyline(points).close().extrude(y1 - y0)
    return w


def S(w: cq.Workplane) -> cq.Shape:
    return w.val() if len(w.vals()) == 1 else cq.Compound.makeCompound(w.vals())


def part(name, group, w, color, fab=False, **meta):
    return Part(name, group, S(w), C[color] if isinstance(color, str) else color, fab=fab, meta=meta)


# ------------------------------------------------------------------ vehicle context
def vehicle(tailgate_open=False):
    parts = []
    hw = P.TUB_W / 2
    ow = hw + P.TUB_WALL_T
    zg = -P.FLOOR_ABOVE_GROUND
    # tub floor + walls (dark liner)
    parts.append(part("tub_floor", "vehicle", box(-P.TUB_WALL_T, P.TUB_L, -ow, ow, -25, 0), "liner"))
    for s, nm in ((1, "driver"), (-1, "passenger")):
        parts.append(part(f"tub_wall_{nm}", "vehicle", box(-P.TUB_WALL_T, P.TUB_L, s * hw, s * ow, -25, P.TUB_D), "liner"))
        arch = box(0, P.ARCH_L, s * P.ARCH_GAP / 2, s * hw, 0, P.ARCH_H).edges("|Y").edges(">Z").fillet(60)
        parts.append(part(f"wheel_arch_{nm}", "vehicle", arch, "liner"))
        # outer body skin over the tub sides
        parts.append(part(f"tub_skin_{nm}", "vehicle",
                          box(-P.TUB_WALL_T, P.TUB_L + P.TAILGATE_T, s * (ow), s * (ow + 30), -330, P.TUB_D - 10), "body"))
        parts.append(part(f"tub_rail_{nm}", "vehicle", box(-P.TUB_WALL_T, P.TUB_L + P.TAILGATE_T, s * hw, s * (ow + 30), P.TUB_D - 10, P.TUB_D), "trim"))
    parts.append(part("tub_front_wall", "vehicle", box(-P.TUB_WALL_T, 0, -hw, hw, -25, P.TUB_D), "liner"))
    if tailgate_open:
        tg = box(P.TUB_L, P.TUB_L + P.TUB_D - 30, -hw, hw, -P.TAILGATE_T, -2)
    else:
        tg = box(P.TUB_L, P.TUB_L + P.TAILGATE_T, -hw, hw, -25, P.TUB_D - 10)
    parts.append(part("tailgate", "vehicle", tg, "body"))
    # lower rear body / bumper
    parts.append(part("rear_bumper", "vehicle", box(P.TUB_L - 40, P.TUB_L + 130, -ow - 30, ow + 30, -470, -300), "trim"))
    parts.append(part("underbody", "vehicle", box(-P.TUB_WALL_T, P.TUB_L - 40, -500, 500, -420, -25), "trim"))
    parts.append(part("tub_underside", "vehicle", box(-P.TUB_WALL_T, P.TUB_L + P.TAILGATE_T, -ow, ow, -330, -25), "liner"))
    # cab + front body (simplified context shell)
    cw = 905
    pts = [(P.CAB_REAR_X, -470), (P.CAB_REAR_X, P.ROOF_Z), (P.CAB_FRONT_X, P.ROOF_Z), (-2450, 420),
           (-3650, 330), (-3720, -100), (-3700, -470)]
    parts.append(part("cab_body", "vehicle", prof_xz(pts, -cw, cw), "body"))
    glass = [(P.CAB_REAR_X + 5, 450), (P.CAB_REAR_X + 5, P.ROOF_Z - 60), (P.CAB_FRONT_X - 20, P.ROOF_Z - 60), (-2400, 440)]
    parts.append(part("cab_glass", "vehicle", prof_xz(glass, -cw - 3, cw + 3), "glass"))
    # factory roof rails
    for s in (1, -1):
        parts.append(part(f"roof_rail_{'d' if s > 0 else 'p'}", "vehicle",
                          box(P.CAB_FRONT_X + 60, P.CAB_REAR_X - 120, s * 640, s * 690, P.ROOF_Z, P.ROOF_Z + 40), "trim"))
    # wheels
    for x in (P.REAR_AXLE_X, P.REAR_AXLE_X - P.WHEELBASE):
        for s in (1, -1):
            parts.append(part(f"wheel_{int(x)}_{s}", "vehicle",
                              cyl(P.TYRE_D / 2, P.TYRE_W, (x, s * (805), zg + P.TYRE_D / 2), "Y"), "tyre"))
    return parts


# ------------------------------------------------------------------ load lid + tent
def lid_and_tent():
    parts = []
    z0 = P.TUB_D + P.LID_CLEAR
    z1 = z0 + P.LID_T
    x0, x1 = P.LID_X0, P.LID_X0 + P.LID_L
    parts.append(part("load_lid", "lid", box(x0, x1, -P.LID_W / 2, P.LID_W / 2, z0, z1), "lid"))
    for s in (1, -1):
        rail = box(x0 + 40, x1 - 40, s * (P.LID_W / 2 - 50), s * (P.LID_W / 2 - 10), z1, z1 + P.LID_RAIL_H)
        for i in range(10):
            xc = x0 + 120 + i * (P.LID_L - 240) / 9
            rail = rail.cut(cyl(16, 60, (xc, s * (P.LID_W / 2 - 30), z1 + P.LID_RAIL_H / 2), "Y"))
        parts.append(part(f"lid_rail_{s}", "lid", rail, "lid"))
    # tent (closed)
    t0 = z1
    tent = (box(P.TENT_X0, P.TENT_X0 + P.TENT_L, -P.TENT_W / 2, P.TENT_W / 2, t0, t0 + P.TENT_H)
            .edges("|Z").fillet(90).edges(">Z").fillet(50))
    parts.append(part("rooftop_tent", "tent", tent, "tent"))
    # top accessory rails (from 23Zero drawing: ~1045 apart across, ~890 long)
    bx0 = P.TENT_X0 + 130
    top = t0 + P.TENT_H - 25
    for s in (1, -1):
        parts.append(part(f"tent_top_bar_{s}", "tent",
                          box(bx0, bx0 + P.TENT_BAR_L, s * (P.TENT_BAR_CC / 2 - 15), s * (P.TENT_BAR_CC / 2 + 15), top, top + 25), "tent_rail"))
    # 2 x Sunman eArc 100 W bonded to a 3 mm ACM sheet spanning the two top bars
    pl, pw, _ = P.TENT_PANEL
    sx0 = bx0 + (P.TENT_BAR_L - pl) / 2
    parts.append(part("tent_solar_backing", "solar", box(sx0 - 10, sx0 + pl + 10, -pw - 10, pw + 10, top + 25, top + 28), "solar_frame", fab=True))
    for i, (ya, yb) in enumerate(((-pw - 2, -2), (2, pw + 2))):
        parts.append(part(f"tent_solar_{i+1}", "solar", box(sx0, sx0 + pl, ya, yb, top + 28, top + 31), "solar", watts=100))
    # tent services box: 240V outlet (heater) + 240V shore inlet + 12V, location TBC
    tsb = box(P.TENT_X0 + P.TENT_L - 160, P.TENT_X0 + P.TENT_L - 20, -560, -380, t0 + 20, t0 + 120)
    parts.append(part("tent_services_box", "tent", tsb, "outlet"))
    # lid underside connector panel (detachable tent umbilical) + gland
    parts.append(part("lid_connector_panel", "lid",
                      box(60, 160, -520, -300, z0 - 70, z0), "victron_dark"))
    return parts


# ------------------------------------------------------------------ front electrical bay
def electrical_bay():
    parts = []
    hw = P.BAY_W / 2
    d = P.BAY_D
    post = 30
    # welded aluminium frame: base tray, 4 posts, deck, top rails
    parts.append(part("bay_base_tray", "bay", box(0, d, -hw, hw, 0, 4), "alu", fab=True))
    for x in (0, d - post):
        for y in (-hw, hw - post):
            parts.append(part(f"bay_post_{x}_{y}", "bay", box(x, x + post, y, y + post, 4, P.BAY_H), "alu", fab=True))
    parts.append(part("bay_deck", "bay", box(0, d, -hw + post, hw - post, P.BAY_DECK_Z, P.BAY_DECK_Z + 4), "alu", fab=True))
    for x in (0, d - post):
        parts.append(part(f"bay_top_rail_{x}", "bay", box(x, x + post, -hw, hw, P.BAY_H - post, P.BAY_H), "alu", fab=True))
    for y in (-hw, hw - post):
        parts.append(part(f"bay_side_rail_{y}", "bay", box(0, d, y, y + post, P.BAY_H - post, P.BAY_H), "alu", fab=True))
    # batteries side by side across the tub
    bx0 = (d - P.BATT_W) / 2
    for i, (ya, yb) in enumerate(((-hw + 22, -hw + 22 + P.BATT_L), (hw - 22 - P.BATT_L, hw - 22))):
        parts.append(part(f"battery_{i+1}", "batteries", box(bx0, bx0 + P.BATT_W, ya, yb, 4, 4 + P.BATT_H - 15), "battery"))
        parts.append(part(f"battery_{i+1}_band", "batteries", box(bx0 - 1, bx0 + P.BATT_W + 1, ya + 30, yb - 30, 150, 175), "battery_accent"))
        for yt in (ya + 50, yb - 50):
            parts.append(part(f"battery_{i+1}_term_{int(yt)}", "batteries", cyl(12, 15, (bx0 + 60, yt, 4 + P.BATT_H - 7)), "copper"))
        # hold-down strap
        parts.append(part(f"battery_{i+1}_holddown", "bay", box(bx0 - 5, bx0 + P.BATT_W + 5, (ya + yb) / 2 - 20, (ya + yb) / 2 + 20, 4 + P.BATT_H - 15, 4 + P.BATT_H - 10), "alu_dark", fab=True))
    # components on deck: inverter/charger flat (with fan), Lynx Class-T + distributor, shunt
    z = P.BAY_DECK_Z + 4
    L, D, H = P.INVERTER
    yi0 = -hw + 35
    parts.append(part("inverter_charger_multiplus2_3000", "electrical", box(12, 12 + D, yi0, yi0 + L, z, z + H), "victron"))
    parts.append(part("inverter_fan", "electrical", cyl(40, 25, (12 + D / 2, yi0 + L + 30, z + 60), "Y"), "victron_dark"))
    yl = yi0 + L + 70
    for nm_, dims in (("lynx_class_t_power_in", P.LYNX_CT), ("lynx_distributor", P.LYNX_DIST)):
        l, dd, h = dims
        parts.append(part(nm_, "electrical", box(5, 5 + dd, yl, yl + l, z, z + h), "victron"))
        yl += l + 2
    l, dd, h = P.SHUNT
    parts.append(part("smartshunt_500a", "electrical", box(30, 30 + dd, yl + 25, yl + 25 + l, z, z + h), "victron_dark"))
    # battery isolator on the bay's rear face (reachable when the slides are out)
    parts.append(part("battery_isolator", "electrical", cyl(45, 30, (d + 10, 0, 170), "X"), "fuse"))
    for i, yy in enumerate((-hw + 22 + 60, hw - 22 - P.BATT_L + 60)):
        parts.append(part(f"mrbf_fuse_{i+1}", "electrical", box(30 + 40, 30 + 80, yy + 60, yy + 100, 4 + P.BATT_H - 15, 4 + P.BATT_H - 5), "fuse"))
    # removable vented cover (shown translucent)
    parts.append(part("bay_cover", "bay_cover", box(-2, d + 2, -hw - 2, hw + 2, P.BAY_H, P.BAY_H + 3), "cover", fab=True))
    return parts


# ------------------------------------------------------------------ slides
def slide(side: str, ext: float, power: bool):
    """side 'p' = passenger (-Y), 'd' = driver (+Y). ext = extension in mm (0 = stowed)."""
    parts = []
    s = -1 if side == "p" else 1
    y_in = s * P.SLIDE_GAP_MID / 2
    y_out = s * (P.SLIDE_GAP_MID / 2 + P.CASSETTE_W)
    ya, yb = sorted((y_in, y_out))
    x0, x1 = P.SLIDE_X0, P.SLIDE_X0 + P.SLIDE_L
    g = f"slide_{side}"
    nm = f"slide_{'power' if power else 'driver'}"
    # fixed cassette: 2 longitudinal base bars + 3 cross bars + vertical runner plates
    for yy in (ya, yb - 50):
        parts.append(part(f"{nm}_base_long_{int(yy)}", g, box(x0, x1, yy, yy + 50, 0, P.BASE_RAIL_H), "alu", fab=True))
    for xx in (x0, (x0 + x1) / 2 - 25, x1 - 50):
        parts.append(part(f"{nm}_base_cross_{int(xx)}", g, box(xx, xx + 50, ya + 50, yb - 50, 0, P.BASE_RAIL_H), "alu", fab=True))
    for yy, t in ((ya, P.SIDE_PLATE_T), (yb - P.SIDE_PLATE_T, P.SIDE_PLATE_T)):
        parts.append(part(f"{nm}_side_angle_{int(yy)}", g, box(x0, x1, yy, yy + t, P.BASE_RAIL_H, P.BASE_RAIL_H + P.RUNNER_H), "alu", fab=True))
    # runners (3-member full extension): fixed, intermediate, moving
    rz0, rz1 = P.BASE_RAIL_H, P.BASE_RAIL_H + P.RUNNER_H
    third = P.RUNNER_T / 3
    for side_y, dirn in ((ya + P.SIDE_PLATE_T, 1), (yb - P.SIDE_PLATE_T, -1)):
        for k, off in enumerate((0, ext / 2, ext)):
            yy0 = side_y + dirn * k * third
            yy1 = yy0 + dirn * third
            parts.append(part(f"{nm}_runner_{dirn}_{k}", g, box(x0 + 5 + off, x0 + 5 + P.RUNNER_LEN + off, yy0, yy1, rz0 + 4, rz1 - 4), "runner"))
    # centre keel: fixed plate on the base + a second runner pair back-to-back (DZ9301)
    ykc = (ya + yb) / 2
    parts.append(part(f"{nm}_keel_fixed", g, box(x0, x1, ykc - P.KEEL_T / 2, ykc + P.KEEL_T / 2, P.BASE_RAIL_H, P.BASE_RAIL_H + P.RUNNER_H), "alu", fab=True))
    for dirn in (1, -1):
        for k, off in enumerate((0, ext / 2, ext)):
            yy0 = ykc + dirn * (P.KEEL_T / 2 + k * third)
            parts.append(part(f"{nm}_keel_runner_{dirn}_{k}", g, box(x0 + 5 + off, x0 + 5 + P.RUNNER_LEN + off, yy0, yy0 + dirn * third, rz0 + 4, rz1 - 4), "runner"))
        # moving keel hanger plates on the carriage
        yy = ykc + dirn * (P.KEEL_T / 2 + P.RUNNER_T + 1)
        parts.append(part(f"{nm}_keel_hanger_{dirn}", g, box(x0 + ext, x1 + ext, yy, yy + dirn * 4, rz0 + 1, P.DECK_TOP_Z - P.DECK_T), "alu", fab=True))
    # carriage (moves with ext)
    cy0 = ya + P.SIDE_PLATE_T + P.RUNNER_T + 1
    cy1 = yb - P.SIDE_PLATE_T - P.RUNNER_T - 1
    cx0, cx1 = x0 + ext, x1 + ext
    top = P.DECK_TOP_Z
    deck_bot = top - P.DECK_T
    # carriage side members 75x25 RHS, cross members 50x25
    for yy in (cy0, cy1 - 25):
        parts.append(part(f"{nm}_carr_side_{int(yy)}", g, box(cx0, cx1, yy, yy + 25, rz0 + 1, deck_bot), "alu", fab=True))
    n_cross = 5
    for i in range(n_cross):
        xx = cx0 + i * (P.SLIDE_L - 50) / (n_cross - 1)
        parts.append(part(f"{nm}_carr_cross_{i}", g, box(xx, xx + 40, cy0 + 25, cy1 - 25, deck_bot - 20, deck_bot), "alu", fab=True))
    # deck ply
    parts.append(part(f"{nm}_deck", g, box(cx0, cx1, cy0, cy1, deck_bot, top), "ply", fab=True))
    # centre L-track (flush)
    yc = (cy0 + cy1) / 2
    parts.append(part(f"{nm}_ltrack", g, box(cx0 + 20, cx1 - 20, yc - P.LTRACK_W / 2, yc + P.LTRACK_W / 2, top - 9, top + 0.5), "ltrack"))
    slots = None
    for i in range(int((P.SLIDE_L - 60) / 25.4)):
        xx = cx0 + 30 + i * 25.4
        c = cyl(5.5, 2, (xx, yc, top + 1))
        slots = c if slots is None else slots.union(c)
    parts.append(part(f"{nm}_ltrack_slots", g, slots, "receiver"))
    # module receiver grid (countersunk female receivers)
    rec = None
    pitch = P.RECEIVER_PITCH
    ny = int((cy1 - cy0 - 60) // pitch)
    nx = int((P.SLIDE_L - 60) // pitch)
    gx0 = cx0 + (P.SLIDE_L - nx * pitch) / 2
    for i in range(nx + 1):
        for j in range(ny + 1):
            yy = (cy0 + cy1) / 2 - ny * pitch / 2 + j * pitch
            if abs(yy - yc) < 40:
                continue
            c = cyl(P.RECEIVER_D / 2, 2, (gx0 + i * pitch, yy, top + 1))
            rec = c if rec is None else rec.union(c)
    parts.append(part(f"{nm}_receivers", g, rec, "receiver"))
    # rear face plate + handle
    parts.append(part(f"{nm}_rear_plate", g, box(cx1 - 4, cx1, cy0, cy1, rz0, top + 40), "alu", fab=True))
    parts.append(part(f"{nm}_handle", g, box(cx1, cx1 + 25, yc - 120, yc + 120, top - 10, top + 15), "alu_dark"))
    if ext > 0:
        # fold-down support leg (deployed when extended with heavy loads)
        zg = -P.FLOOR_ABOVE_GROUND
        for yy in (cy0 + 30, cy1 - 55):
            parts.append(part(f"{nm}_leg_{int(yy)}", g, box(cx1 - 60, cx1 - 35, yy, yy + 25, zg, rz0), "alu_dark", fab=True))
    if power:
        # power bulkhead at the FRONT of the carriage: outlets face rearward over the deck
        bw0, bw1 = cy0 + 20, cy1 - 20
        parts.append(part(f"{nm}_power_bulkhead", g, box(cx0 + 5, cx0 + 55, bw0, bw1, top, top + 150), "alu_dark", fab=True))
        fx = cx0 + 55
        parts.append(part(f"{nm}_gpo", g, box(fx, fx + 12, bw0 + 30, bw0 + 150, top + 25, top + 125), "outlet"))
        parts.append(part(f"{nm}_anderson", g, box(fx, fx + 12, bw0 + 180, bw0 + 240, top + 40, top + 110), "anderson"))
        parts.append(part(f"{nm}_12v", g, cyl(18, 12, (fx + 6, bw0 + 300, top + 75), "X"), "usb"))
        parts.append(part(f"{nm}_usbc", g, box(fx, fx + 12, bw0 + 340, bw0 + 400, top + 55, top + 95), "usb"))
        # lay-flat cable chain under the carriage (bends in the horizontal plane)
        R = 55
        xf = x0 + P.SLIDE_EXT / 2 + 30           # fixed end at mid travel (floor)
        xm = cx0 + 30                              # moving end on carriage
        lc = (xf + (x0 + 30) - 2 * (x0 + 10)) + math.pi * R
        xb = (xf + xm - lc + math.pi * R) / 2
        yc0 = (cy0 + ykc) / 2 - R - 10 if side == 'd' else (ykc + cy1) / 2 - R + 10
        yc0 = (cy0 + 40) if side == 'p' else yc0
        zc0, zc1 = 16, 52
        run_a = box(xb, xf, yc0 - 18, yc0 + 18, zc0, zc1)
        run_b = box(xb, xm, yc0 + 2 * R - 18, yc0 + 2 * R + 18, zc0, zc1)
        bend = (cq.Workplane("XY").circle(R + 18).circle(R - 18).extrude(zc1 - zc0)
                .cut(box(0, R + 30, -R - 30, R + 30, -1, zc1)).translate((xb, yc0 + R, zc0)))
        parts.append(part(f"{nm}_cable_chain", g, run_a.union(run_b).union(bend), "chain"))
    return parts


# ------------------------------------------------------------------ side bays
def side_bays():
    parts = []
    hw = P.TUB_W / 2
    # ---------- passenger (-Y): power cabinet behind arch + overflow box above arch
    ya, yb = -hw + 4, -P.ARCH_GAP / 2 - 4
    x0, x1 = P.POCKET_X0, P.POCKET_X1
    t = 12
    cab = box(x0, x1, ya, yb, 0, P.WATER_TOP_Z).cut(box(x0 + t, x1 - t, ya + t, yb - t, t, P.WATER_TOP_Z - t))
    parts.append(part("power_cabinet", "power_cabinet", cab, "ply", fab=True))
    fx = x1
    # rear-facing outlet panel (top -> bottom): GX Touch 50, USB-C PD + 12 V, 2 x IP66 GPO, 2 x Anderson SB50
    ym = (ya + yb) / 2
    def face(n, col, y0, y1, z0, z1):
        parts.append(part(n, "power_cabinet", box(fx, fx + 12, y0, y1, z0, z1), col))
    face("pc_gx_touch_50", "victron_dark", ym - 64, ym + 64, 400, 487)
    face("pc_usbc", "usb", ya + 20, ya + 75, 345, 385)
    parts.append(part("pc_12v", "power_cabinet", cyl(18, 12, (fx + 6, yb - 45, 365), "X"), "usb"))
    face("pc_gpo_1", "outlet", ym - 50, ym + 50, 230, 335)
    face("pc_gpo_2", "outlet", ym - 50, ym + 50, 120, 225)
    face("pc_anderson_1", "anderson", ya + 15, ym - 8, 30, 105)
    face("pc_anderson_2", "anderson", ym + 8, yb - 15, 30, 105)
    parts.append(part("pc_rcbo_enclosure", "power_cabinet", box(x1 - 300, x1 - 160, ya + 20, yb - 20, 250, 420), "outlet"))
    # charging + monitoring board above the passenger arch (vertical board, ventilated cover)
    zb = P.ARCH_H + 6
    parts.append(part("charge_board", "power_cabinet", box(5, P.ARCH_L - 5, ya, ya + 12, zb, P.WATER_TOP_Z), "ply", fab=True))
    parts.append(part("charge_board_shelf", "power_cabinet", box(5, P.ARCH_L - 5, ya, yb, zb - 6, zb), "alu", fab=True))
    xb = 30
    for nm_, dims, col in (("orion_xs_1", P.DCDC, "victron"), ("orion_xs_2", P.DCDC, "victron"),
                           ("mppt_roof_100_50", P.MPPT_ROOF, "victron"), ("mppt_tent_75_15", P.MPPT_TENT, "victron"),
                           ("cerbo_gx", P.CERBO, "victron_dark")):
        l, t_, h = dims
        parts.append(part(nm_, "electrical", box(xb, xb + l, ya + 12, ya + 12 + t_, zb + 20, zb + 20 + h), col))
        xb += l + 30
    parts.append(part("dc_fuse_block", "electrical", box(xb, xb + 110, ya + 12, ya + 52, zb + 20, zb + 100), "fuse"))
    # factory Kia 230V outlet location (cable pass-through) [EST position]
    parts.append(part("kia_factory_outlet", "markers", cyl(35, 10, (1330, -hw + 2, 400), "Y"), "kia_outlet"))
    # ---------- driver (+Y): L-shaped water tank over arch + behind arch
    ya, yb = P.ARCH_GAP / 2 + 4, hw - 4
    xr = x1 - P.WATER_REAR_GAP
    tank = (box(x0, xr, ya, yb, 3, P.WATER_TOP_Z)
            .union(box(5, x0 + 10, ya, yb, P.ARCH_H + 3, P.WATER_TOP_Z)))
    tank = tank.edges("|Y").fillet(20)
    vol_l = (((xr - x0) * (yb - ya) * (P.WATER_TOP_Z - 3)) + ((x0 + 5) * (yb - ya) * (P.WATER_TOP_Z - P.ARCH_H - 3))) / 1e6
    parts.append(part("water_tank", "water", tank, "water", fab=True, gross_litres=round(vol_l, 1)))
    # pump / tap / hose compartment at the rear
    parts.append(part("water_tap_box", "water", box(xr + 3, x1, ya, yb, 0, P.WATER_TOP_Z), "ply", fab=True))
    parts.append(part("water_tap", "water", box(x1, x1 + 40, (ya + yb) / 2 - 15, (ya + yb) / 2 + 15, 380, 400), "tank_hw"))
    parts.append(part("water_hose_reel", "water", cyl(60, 12, (x1 + 6, (ya + yb) / 2, 250), "X"), "trim"))
    parts.append(part("water_filler", "water", cyl(30, 25, (400, (ya + yb) / 2, P.WATER_TOP_Z + 12)), "trim"))
    return parts


# ------------------------------------------------------------------ roof platform
def roof(cargo=True):
    parts = []
    x0, x1 = P.PLAT_X0, P.PLAT_X0 + P.PLAT_L
    hw = P.PLAT_W / 2
    z0, z1 = P.PLAT_Z, P.PLAT_Z + P.PLAT_T
    # perimeter frame + 2 internal cross members (slimline)
    for yy in (-hw, hw - 40):
        parts.append(part(f"plat_side_{yy}", "roof", box(x0, x1, yy, yy + 40, z0, z1), "trim"))
    for xx in (x0, x1 - 40):
        parts.append(part(f"plat_cross_{int(xx)}", "roof", box(xx, xx + 40, -hw, hw, z0, z1), "trim"))
    # front wind fairing with flush light bar
    fair = box(x0 - 90, x0, -hw, hw, z0 - 10, z1 + 10)
    parts.append(part("plat_fairing", "roof", fair, "trim"))
    parts.append(part("light_bar", "roof", box(x0 - 92, x0 - 85, -500, 500, z0 + 3, z1 + 3), "light"))
    # foot mounts onto factory rails
    for xx in (x0 + 150, x1 - 190):
        for s in (1, -1):
            parts.append(part(f"plat_foot_{int(xx)}_{s}", "roof", box(xx, xx + 40, s * 640, s * 690, P.ROOF_Z + 40, z0), "trim"))
    # two Victron BlueSolar 190 W panels (1485 x 668) running fore-aft, recessed inside the frame
    pl, pw, pt = P.ROOF_PANEL
    px0 = x0 + 45
    for i, (ya, yb) in enumerate(((-pw - 3, -3), (3, pw + 3))):
        parts.append(part(f"roof_solar_{i+1}", "solar", box(px0, px0 + pl, ya, yb, z0 + 4, z0 + 4 + pt - 6), "solar", watts=190))
        parts.append(part(f"roof_solar_frame_{i+1}", "solar", box(px0, px0 + pl, ya, yb, z0 + 2, z0 + 4), "solar_frame"))
    # Starlink Mini - fixed on a low bracket at the rear edge of the platform
    sl, sw, sh = P.STARLINK_MINI
    parts.append(part("starlink_mini", "roof", box(x1 - 10, x1 + sw - 10, -sl / 2, sl / 2, z1 + 5, z1 + 5 + sh), "starlink"))
    parts.append(part("starlink_bracket", "roof", box(x1 - 40, x1 + sw - 20, -60, 60, z0, z1 + 5), "trim"))
    if cargo:
        # removable cargo bars on risers (T-slot in side rails), sit above the panels
        for xx in (x0 + 250, x1 - 300):
            for s in (1, -1):
                parts.append(part(f"cargo_riser_{int(xx)}_{s}", "cargo", box(xx, xx + 50, s * (hw - 40), s * hw, z1, z1 + P.CARGO_BAR_Z), "alu_dark"))
            parts.append(part(f"cargo_bar_{int(xx)}", "cargo", box(xx - 10, xx + 60, -hw - 60, hw + 60, z1 + P.CARGO_BAR_Z, z1 + P.CARGO_BAR_Z + 35), "trim"))
    return parts


# ------------------------------------------------------------------ cable routes (schematic)
def cables():
    zl = P.TUB_D + P.LID_CLEAR
    return [
        Part("route_tent_umbilical", "cables", color=C["cable_240"], tube_r=8,
             tube=[(150, -400, P.BAY_H), (40, -400, P.BAY_H + 10), (40, -400, zl - 70)]),
        Part("route_rear_power_cabinet", "cables", color=C["cable_red"], tube_r=8,
             tube=[(60, -560, P.BAY_DECK_Z + 60), (60, -640, P.BAY_DECK_Z + 60), (60, -700, P.ARCH_H + 20),
                   (P.ARCH_L, -700, P.ARCH_H + 20), (P.POCKET_X0 + 50, -700, 300)]),
        Part("route_out_of_tub_via_factory_outlet", "cables", color=C["cable_blk"], tube_r=10,
             tube=[(P.POCKET_X0 + 40, -760, 420), (1330, -760, 420), (1330, -810, 400), (1330, -810, -60),
                   (1330, -450, -120), (-600, -450, -120)]),
        Part("route_engine_bay_alt_feed", "cables", color=C["cable_red"], tube_r=10,
             tube=[(-600, -450, -120), (-2900, -450, -120), (-2900, -450, 150)]),
        Part("route_cabin_rear_seat", "cables", color=C["cable_red"], tube_r=7,
             tube=[(-600, -450, -120), (-600, -400, 0)]),
        Part("route_roof_pv", "cables", color=C["cable_pv"], tube_r=6,
             tube=[(P.PLAT_X0 + P.PLAT_L - 60, -600, P.PLAT_Z), (-80, -600, P.ROOF_Z - 60), (-80, -600, P.BAY_H),
                   (150, -100, P.BAY_H)]),
    ]


def markers():
    return [part("cabin_under_seat_outlets", "markers", box(-750, -450, -450, -250, -60, 60), "marker")]


def build(state="camp"):
    """state: 'travel' (slides stowed, tailgate shut) or 'camp' (slides out, tailgate down)."""
    ext = P.SLIDE_EXT if state == "camp" else 0
    parts = []
    parts += vehicle(tailgate_open=(state == "camp"))
    parts += lid_and_tent()
    parts += electrical_bay()
    parts += slide("p", ext, power=True)
    parts += slide("d", ext * (0.6 if state == "camp" else 0), power=False)
    parts += side_bays()
    parts += roof()
    parts += cables()
    parts += markers()
    return parts
