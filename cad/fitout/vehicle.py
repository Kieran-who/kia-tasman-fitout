"""Tub (factory liner) and a simplified Kia Tasman X-Pro body for context.

Everything here is context (group `vehicle`, plus the `markers` start battery / cabin box): it is excluded from the
fit-out weight. The tub INTERIOR (walls at +/-TUB_W/2, arch faces, floor rib tops at Z=0, rail top at TUB_D) is what the
fit-out was designed and clash-checked against, so liner detail is only ever cut INTO the walls (recesses), never added
inside the tub. The body is built from intersected extruded profiles (planar faces only) to keep the mesh light.
"""
import cadquery as cq

import params as P

from .core import S, anchor, box, cyl, part

# ------------------------------------------------------------------ published / estimated body figures (context only)
FRONT_OH = 855          # [PUB] X-Pro front overhang (carsales.com.au/research/kia/tasman/2025/x-pro); 855+3270+1285 = 5410 [PUB]
REAR_OH = 1285          # [PUB] X-Pro rear overhang (same source)
TRACK_F, TRACK_R = 1636, 1624   # [PUB] X-Pro tread front/rear (Kia owner's manual / carexpert X-Pro spec)
BODY_HW = 915           # [EST] half width over the doors / tub sides (overall 1930 [PUB] is over the flares)
FLARE_HW = 965          # [PUB] 1930 / 2: X-Pro wheel-arch cladding
RIM_R = 216             # [PUB] 17" rim (265/70 R17 [PUB]); bead seat 431.8 dia
ZG = -P.FLOOR_ABOVE_GROUND                  # ground in the tub frame
FRONT_AXLE_X = P.REAR_AXLE_X - P.WHEELBASE
NOSE_X = FRONT_AXLE_X - FRONT_OH            # -3695
TAIL_X = P.REAR_AXLE_X + REAR_OH            # 1715: rear bumper / step
WHEEL_ZC = ZG + P.TYRE_D / 2
SILL_Z = ZG + 470       # [EST] bottom of the doors
BELT_Z = 480            # [EST] window line (just under the tub rail, owner photo)
COWL_X = -2450          # [EST] base of the windscreen
BONNET_Z = (335, 440)   # [EST] bonnet front edge / cowl: high flat X-Pro bonnet meets the screen near the window line (owner photo)
SCREEN_BASE = (-2450, 430)   # [EST] windscreen base (side view)
SK = BODY_HW            # outer skin of the tub sides
SKIN_T = 25             # [EST] visual outer skin thickness (cavity between it and the liner wall carries the cables)

# lid gas struts (Ute Master hinges at the FRONT): modelled lying in a channel in the top of each tub side wall so they
# never enter the fit-out space. Owner (v0.9): the lid comes off with a few bolts, so the struts are taken to be
# outside the tub, not mounted inside it. [EST] exact position - photograph on the vehicle.
LID_STRUT = dict(x0=60, x1=560, z0=470, z1=522, dy=22, r_body=11, r_rod=5, body_l=290)

# colours (RGBA) used only here
RIM = (42, 42, 45, 255)
LED_AMBER = (255, 110, 20, 255)
TAIL_RED = (150, 20, 22, 255)
HEADLAMP = (215, 222, 228, 255)
CLEAT = (128, 130, 134, 255)


def _xy(pts, z0, z1):
    return cq.Workplane("XY", origin=(0, 0, z0)).polyline(pts).close().extrude(z1 - z0)


def _xz(pts, y0, y1, off=0.0):
    w = cq.Workplane("XZ", origin=(0, y1, 0)).polyline(pts).close()
    if off:
        w = w.offset2D(off, "intersection")
    return w.extrude(y1 - y0)


def _yz(pts, x0, x1, off=0.0):
    w = cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(pts).close()
    if off:
        w = w.offset2D(off, "intersection")
    return w.extrude(x1 - x0)


def comp(ws):
    """Compound of disjoint pieces (no boolean union: cheap and robust)."""
    return cq.Compound.makeCompound([S(w) for w in ws])


def _fillet(w, sel, r):
    try:
        return w.edges(sel).fillet(r)
    except Exception:
        return w


def _arch_open(xc, grow=0.0, z_bot=None):
    """Squared X-Pro wheel-arch opening (side view) around a wheel at xc."""
    zc = WHEEL_ZC
    a, b, top = 455 + grow, 320 + grow, zc + 445 + grow
    zb = ZG - 10 if z_bot is None else z_bot
    return [(xc - a, zb), (xc - a, zc + 90), (xc - b, top), (xc + b, top), (xc + a, zc + 90), (xc + a, zb)]


def _flare(xc, y_in, y_out, z_bot):
    y0, y1 = min(y_in, y_out), max(y_in, y_out)
    outer = _xz(_arch_open(xc, 70), y0, y1).intersect(box(xc - 700, xc + 700, y0 - 1, y1 + 1, z_bot, 2000))
    return outer.cut(_xz(_arch_open(xc), y0 - 1, y1 + 1))


# ================================================================== tub
def _tailgate_local(L):
    """Tailgate in a local frame: u (X) from the hinge up, Y across, t (Z) from the INNER face outward."""
    T = P.TAILGATE_T
    hy = P.TUB_W / 2 - 20
    g = box(0, L, -hy, hy, 0, T)
    g = _fillet(g, "|Y and >Z", 10)                                            # rounded outer edges
    g = g.cut(_fillet(box(70, L - 60, -(hy - 70), hy - 70, -1, 5), "|Z", 25))      # inner pressed panel (recessed only)
    g = g.cut(_fillet(box(115, L - 150, -(hy - 120), hy - 120, T - 4, T + 1), "|Z", 30))   # outer feature panel
    g = g.cut(_fillet(box(L - 95, L - 38, -95, 95, T - 16, T + 1), "|Z", 12))     # handle pocket (top centre, outside)
    handle = box(L - 88, L - 46, -80, 80, T - 15, T - 7)
    badge = box(L - 260, L - 236, -170, 170, T - 4, T - 2.5)                     # TASMAN lettering strip
    return g, comp([handle, badge])


def _tailgate(open_):
    if open_:
        L = P.TAILGATE_H

        def tf(w):
            return w.rotate((0, 0, 0), (1, 0, 0), 180).translate((P.TUB_L + 10, 0, -5))
    else:
        L = P.TUB_D - 10 + 25

        def tf(w):
            return w.rotate((0, 0, 0), (0, 1, 0), 90).rotate((0, 0, 0), (1, 0, 0), 180).translate((P.TUB_L, 0, -25))
    g, trim = _tailgate_local(L)
    return tf(g), tf(cq.Workplane("XY").add(trim))


def tub(tailgate_open=False):
    parts = []
    hw = P.TUB_W / 2
    ow = hw + P.TUB_WALL_T
    xr = P.TUB_L + P.TAILGATE_T                 # rear face of the tub sides
    # floor: liner base at -RIB_H with fore-aft ribs whose tops are Z = 0
    parts.append(part("tub_floor", "vehicle", box(-P.TUB_WALL_T, P.TUB_L, -ow, ow, -25, -P.RIB_H), "liner"))
    n = int(P.ARCH_GAP // P.RIB_PITCH)
    y0 = -(n - 1) * P.RIB_PITCH / 2
    ribs = [box(0, P.TUB_L - 20, y0 + i * P.RIB_PITCH - P.RIB_W / 2, y0 + i * P.RIB_PITCH + P.RIB_W / 2, -P.RIB_H, 0)
            for i in range(n)]
    # short ribs continue behind the arches (owner photo: ribs run out to the side walls at the rear)
    for s in (1, -1):
        for k in (1, 2):
            yc = s * (y0 * -1 + k * P.RIB_PITCH)
            if abs(yc) + P.RIB_W / 2 < hw - 20:
                ribs.append(box(P.ARCH_L + 15, P.TUB_L - 20, yc - P.RIB_W / 2, yc + P.RIB_W / 2, -P.RIB_H, 0))
    ribs = [_fillet(r, "|X", 4) for r in ribs]
    # tie-down / drain buttons moulded in the valleys at the tailgate end (owner photo), below the rib tops
    buttons = [cyl(13, 6, (P.TUB_L - 60, y0 + (i + 0.5) * P.RIB_PITCH, -P.RIB_H + 3)) for i in range(0, n - 1, 2)]
    parts.append(part("tub_floor_ribs", "vehicle", comp(ribs + buttons), "liner_rib"))

    for s, nm in ((1, "driver"), (-1, "passenger")):
        # ---- liner side wall: everything below is cut INTO the wall (outward of the inner face)
        wall = box(-P.TUB_WALL_T, P.TUB_L, s * hw, s * ow, -25, P.TUB_D - 10)
        cuts = [
            box(-P.TUB_WALL_T - 1, P.TUB_L + 1, s * (hw - 1), s * (hw + 12), 470, P.TUB_D),           # step under the rail
            _fillet(box(P.ARCH_L + 45, P.TUB_L - 55, s * (hw - 1), s * (hw + 5), 35, 440), "|Y", 30),  # panel behind arch
            _fillet(box(70, P.ARCH_L - 50, s * (hw - 1), s * (hw + 5), P.ARCH_H + 35, 440), "|Y", 30),  # panel over arch
        ]
        st = LID_STRUT
        cuts.append(box(st["x0"] - 40, st["x1"] + 30, s * (hw + 6), s * (hw + 40), st["z0"] - 22, P.TUB_D))  # strut channel
        if s == P.FACTORY_OUTLET[1]:
            fx, fs, fz = P.FACTORY_OUTLET
            cuts.append(box(fx - 75, fx + 75, s * (hw - 1), s * (hw + 16), fz - 62, fz + 62))   # outlet housing pocket
        for c in cuts:
            wall = wall.cut(c)
        parts.append(part(f"tub_wall_{nm}", "vehicle", wall, "liner"))
        # ---- wheel arch hump: box from the front wall, rounded top inboard + rear edges (unchanged interior envelope)
        arch = (box(0, P.ARCH_L, s * P.ARCH_GAP / 2, s * hw, -P.RIB_H, P.ARCH_H)
                .edges("|X").edges(">Z").edges("<Y" if s > 0 else ">Y").fillet(P.ARCH_R)
                .edges("|Y").edges(">X").edges(">Z").fillet(P.ARCH_R))
        ya_ = s * P.ARCH_GAP / 2
        # moulded relief panel on the hump face (3 mm, recessed) + the recessed well (owner photo, P.ARCH_POCKET)
        ap = P.ARCH_POCKET
        arch = arch.cut(_fillet(box(ap["x0"] - 70, ap["x1"] + 50, ya_ - s * 1, ya_ + s * 3, 70, ap["z1"] + 25), "|Y", 25))
        arch = arch.cut(_fillet(box(ap["x0"], ap["x1"], ya_ - s * 1, ya_ + s * ap["depth"], ap["z0"], ap["z1"]), "|Y", 12))
        # horizontal step along the hump top (the 'shelf' line in the photo), recessed into the shelf front edge
        arch = arch.cut(box(40, P.ARCH_L - 90, ya_ - s * 1, ya_ + s * 10, P.ARCH_H - 95, P.ARCH_H - 85))
        parts.append(part(f"wheel_arch_{nm}", "vehicle", arch, "liner"))
        # tail-light housing bulge at the rear corner (owner: none)
        if P.TAIL_BULGE_L and P.TAIL_BULGE_IN:
            bul = box(P.TUB_L - P.TAIL_BULGE_L, P.TUB_L, s * hw, s * (hw - P.TAIL_BULGE_IN), -P.RIB_H, P.TUB_D - 30)
            parts.append(part(f"tail_bulge_{nm}", "vehicle", bul.edges("|Z").fillet(25), "liner"))
        # ---- outer skin (body colour) with the rear wheel opening, a character line and a corner post at the tailgate
        skin = box(-P.TUB_WALL_T, xr, s * (SK - SKIN_T), s * SK, -330, 505)
        skin = skin.cut(_xz(_arch_open(P.REAR_AXLE_X), *sorted((s * (SK - SKIN_T - 1), s * (SK + 1)))))
        skin = skin.cut(box(P.REAR_AXLE_X + 520, xr - 30, s * (SK - 3), s * (SK + 1), 175, 190))
        parts.append(part(f"tub_skin_{nm}", "vehicle", skin, "body"))
        parts.append(part(f"tub_skin_post_{nm}", "vehicle", box(P.TUB_L, xr, s * hw, s * (SK - SKIN_T), -330, P.TUB_D - 10), "body"))
        # ---- rail cap: rounded outer shoulder, recessed dashed tie-down slots with rails in them (owner photo)
        rp = [(hw - 5, 530), (hw - 5, P.TUB_D), (SK - 12, P.TUB_D), (SK, P.TUB_D - 12), (SK, 500), (SK - SKIN_T, 500),
              (SK - SKIN_T, 530)]
        rail = _yz([(s * y, z) for y, z in rp], -P.TUB_WALL_T, xr)
        ys = s * (hw + 52)
        slots = [(x, ys) for x in range(35, int(xr) - 60, 75)]
        rail = rail.cut(cq.Workplane("XY", origin=(0, 0, P.TUB_D - 3)).pushPoints(slots).rect(48, 8).extrude(4))
        parts.append(part(f"tub_rail_{nm}", "vehicle", rail, "trim"))
        parts.append(part(f"tub_rail_tiedown_{nm}", "vehicle",
                          comp([box(x - 22, x + 22, ys - 2, ys + 2, P.TUB_D - 3, P.TUB_D - 1) for x, _ in slots]), "alu_dark"))
        # corner tie-down cleats on the rail top (low: the lid sits 8 mm above the rail)
        for i, (xa, xb) in enumerate(((-45, 45), (xr - 95, xr - 5))):
            cl = _fillet(box(xa, xb, s * (hw + 2), s * (hw + 70), P.TUB_D, P.TUB_D + 6), "|Z", 10)
            parts.append(part(f"tub_rail_cleat_{nm}_{i}", "vehicle", cl, CLEAT))
        # tail light (vertical housing at the rear corner, amber 'C' LED signature - owner photo)
        hx0, hx1 = xr, xr + 16
        ya, yb = s * (hw + 6), s * (SK + 4)
        parts.append(part(f"tail_light_{nm}", "vehicle", _fillet(box(hx0, hx1, ya, yb, 170, 470), "|X", 12), TAIL_RED))
        yo = s * (SK - 12)
        yi = s * (hw + 30)
        led = [box(hx1, hx1 + 3, yo - s * 6, yo, 200, 440), box(hx1, hx1 + 3, yi, yo, 434, 440), box(hx1, hx1 + 3, yi, yo, 200, 206)]
        parts.append(part(f"tail_light_{nm}_led", "vehicle", comp(led), LED_AMBER))
    # front wall: recessed panel + the same step under the rail; front rail cap
    fw = box(-P.TUB_WALL_T, 0, -hw, hw, -25, P.TUB_D - 10)
    fw = fw.cut(_fillet(box(-4, 1, -hw + 70, hw - 70, 60, 440), "|X", 30)).cut(box(-12, 1, -hw - 1, hw + 1, 470, P.TUB_D))
    parts.append(part("tub_front_wall", "vehicle", fw, "liner"))
    parts.append(part("tub_rail_front", "vehicle", box(-P.TUB_WALL_T - 5, 0, -SK, SK, 530, P.TUB_D), "trim"))
    # factory bed hooks
    for i, (x, s, z) in enumerate(P.BED_HOOKS):
        y = s * (P.ARCH_GAP / 2 if x < P.ARCH_L else hw)
        hook = box(x - 25, x + 25, y, y - s * 18, z - 30, z + 10).union(box(x - 25, x + 25, y - s * 18, y - s * 26, z - 30, z - 18))
        parts.append(part(f"bed_hook_{i+1}", "vehicle", hook, "alu_dark"))
    # factory 240 V outlet (to be removed; its hole becomes the cable gland plate): housing recessed in the wall
    fx, fs, fz = P.FACTORY_OUTLET
    housing = box(fx - 75, fx + 75, fs * (hw + 16), fs * (hw + 12), fz - 62, fz + 62).union(
        box(fx - 75, fx + 75, fs * (hw + 12), fs * hw, fz - 62, fz + 62).cut(box(fx - 58, fx + 58, fs * (hw + 13), fs * (hw - 1), fz - 47, fz + 47)))
    parts.append(part("factory_outlet_housing", "vehicle", housing, "trim"))
    # its hinged weather cover + the socket below it, still recessed behind the wall face
    parts.append(part("factory_outlet_cover", "vehicle",
                      comp([box(fx - 48, fx + 48, fs * (hw + 12), fs * (hw + 4), fz - 8, fz + 40),
                            box(fx - 30, fx + 30, fs * (hw + 12), fs * (hw + 8), fz - 40, fz - 14)]), "anderson_grey"))
    parts.append(part("factory_outlet_gland_plate", "markers", box(fx - 60, fx + 60, fs * hw, fs * (hw - 6), fz - 45, fz + 45), "kia_outlet"))
    anchor("exit_inside", (fx, fs * (hw - 10), fz))
    anchor("exit_outside", (fx, fs * (ow + 10), fz))
    # tailgate: same envelope as before in both states (the slides/legs are clash-checked against it)
    tg, tg_trim = _tailgate(tailgate_open)
    parts.append(part("tailgate", "vehicle", tg, "body"))
    parts.append(part("tailgate_trim", "vehicle", tg_trim, "trim"))
    return parts


# ================================================================== body
def _wheel(s):
    """Tyre (revolved section with shoulders) + 6-spoke 17" rim, built at the origin, axis along Y, outer face to s*Y."""
    r, w = P.TYRE_D / 2, P.TYRE_W
    h = w / 2
    sec = [(RIM_R, -h + 12), (300, -h - 3), (r - 32, -h), (r, -h + 32), (r, h - 32), (r - 32, h), (300, h + 3), (RIM_R, h - 12)]
    tyre = cq.Workplane("XY").polyline(sec).close().revolve(360, (0, 0, 0), (0, 1, 0))
    # rim: face disc recessed 25 mm with 6 trapezoid windows, outer lip, hub cap, dark barrel behind
    face = cq.Workplane("XZ", origin=(0, h - 22, 0)).circle(RIM_R).extrude(18)
    win = [(70, -32), (175, -55), (190, 0), (175, 55), (70, 32)]
    for k in range(6):
        wnd = cq.Workplane("XZ", origin=(0, h - 20, 0)).polyline(win).close().extrude(25)
        face = face.cut(wnd.rotate((0, 0, 0), (0, 1, 0), 30 + 60 * k))
    lip = cq.Workplane("XZ", origin=(0, h - 12, 0)).circle(RIM_R).circle(RIM_R - 14).extrude(12)
    cap = cq.Workplane("XZ", origin=(0, h - 8, 0)).circle(55).extrude(12)
    barrel = cq.Workplane("XZ", origin=(0, h - 120, 0)).circle(RIM_R - 1).extrude(6)
    rim = comp([face, lip, cap, barrel])
    if s < 0:
        tyre = tyre.mirror("XZ")
        rim = cq.Workplane("XY").add(rim).mirror("XZ")
    return tyre, rim


def _cab():
    """Lower body (side profile & section & plan) + greenhouse with window openings; glass = greenhouse inset 6 mm."""
    xb = P.CAB_REAR_X
    side = [(NOSE_X + 30, -400), (NOSE_X, -150), (NOSE_X, BONNET_Z[0] - 60), (NOSE_X + 70, BONNET_Z[0]), (COWL_X, BONNET_Z[1]), (-2330, BELT_Z),
            (xb, BELT_Z + 25), (xb, SILL_Z), (NOSE_X + 400, SILL_Z), (NOSE_X + 250, -400)]
    sec = [(-880, SILL_Z - 60), (880, SILL_Z - 60), (SK, SILL_Z + 80), (SK, 300), (SK - 30, BELT_Z + 40),
           (-(SK - 30), BELT_Z + 40), (-SK, 300), (-SK, SILL_Z + 80)]
    plan = [(NOSE_X, -(SK - 120)), (NOSE_X + 160, -SK), (xb, -SK), (xb, SK), (NOSE_X + 160, SK), (NOSE_X, SK - 120)]
    lower = _xz(side, -1000, 1000).intersect(_yz(sec, NOSE_X - 10, xb + 1)).intersect(_xy(plan, -1000, 1000))
    for s in (1, -1):
        lower = lower.cut(_xz(_arch_open(FRONT_AXLE_X), *sorted((s * 600, s * 1000))))
    # greenhouse: windscreen rake, roof at ROOF_Z, upright back; tumblehome in section
    gh_side = [SCREEN_BASE, (-1815, 945), (-1760, P.ROOF_Z), (xb - 30, P.ROOF_Z), (xb, P.ROOF_Z - 30), (xb, 380)]
    gh_sec = [(-880, 370), (880, 370), (866, BELT_Z), (752, P.ROOF_Z - 25), (728, P.ROOF_Z), (-728, P.ROOF_Z),
              (-752, P.ROOF_Z - 25), (-866, BELT_Z)]

    def gh(off):
        return _xz(gh_side, -1000, 1000, off).intersect(_yz(gh_sec, -2600, xb + 1, off))
    shell = gh(0)

    def xa(z):                                     # A-pillar line
        return SCREEN_BASE[0] + (z - SCREEN_BASE[1]) * ((-1815 - SCREEN_BASE[0]) / (945 - SCREEN_BASE[1]))
    zt = P.ROOF_Z - 70
    wins = [
        _xz([(xa(BELT_Z + 10) + 100, BELT_Z + 10), (-1330, BELT_Z + 10), (-1330, zt), (xa(zt) + 100, zt)], -1000, 1000),
        _xz([(-1245, BELT_Z + 14), (-560, BELT_Z + 20), (-470, zt - 120), (-470, zt), (-1245, zt)], -1000, 1000),
        _xz([(-2700, BONNET_Z[1]), (-1500, BONNET_Z[1]), (-1500, P.ROOF_Z - 38), (-2700, P.ROOF_Z - 38)], -1000, 1000).intersect(
            _yz([(-800, BONNET_Z[1]), (800, BONNET_Z[1]), (690, P.ROOF_Z - 38), (-690, P.ROOF_Z - 38)], -2700, -1500)),
        box(xb - 90, xb + 5, -560, 560, 590, zt),
    ]
    for wcut in wins:
        shell = shell.cut(wcut)
    body = lower.union(shell)
    glass = gh(-6)
    return body, glass, xa


def body_context():
    parts = []
    hw = P.TUB_W / 2
    ow = hw + P.TUB_WALL_T
    xb = P.CAB_REAR_X
    # ---- rear: step bumper, hitch receiver, tub underside with wheel wells
    rb = _xz([(P.TUB_L - 40, -300), (TAIL_X - 15, -300), (TAIL_X, -325), (TAIL_X, -430), (TAIL_X - 40, -480),
              (P.TUB_L - 40, -480)], -SK - 10, SK + 10)
    rb = rb.cut(box(TAIL_X - 160, TAIL_X + 1, -420, 420, -306, -299))     # step tread recess
    parts.append(part("rear_bumper", "vehicle", rb, "trim"))
    parts.append(part("rear_bumper_step", "vehicle", box(TAIL_X - 155, TAIL_X - 5, -415, 415, -306, -301), "alu_dark"))
    parts.append(part("rear_bumper_hitch", "vehicle", comp([box(TAIL_X - 60, TAIL_X + 90, -32, 32, -505, -440),
                                                             box(TAIL_X + 70, TAIL_X + 120, -12, 12, -470, -455)]), "rack"))
    und = box(-P.TUB_WALL_T, P.TUB_L + P.TAILGATE_T, -ow, ow, -330, -25)
    for s in (1, -1):
        und = und.cut(_xz(_arch_open(P.REAR_AXLE_X, 25), *sorted((s * 640, s * (ow + 1)))))
    parts.append(part("tub_underside", "vehicle", und, "liner"))
    # ---- chassis: C-section rails (open inboard), cross members, live rear axle + diff
    for s in (1, -1):
        y_in, y_out = s * (P.CHASSIS_RAIL_Y - 30), s * (P.CHASSIS_RAIL_Y + 30)
        rail = box(-3400, P.TUB_L, y_in, y_out, P.CHASSIS_Z - 180, P.CHASSIS_Z)
        rail = rail.cut(box(-3401, P.TUB_L + 1, y_in - s * 1, y_out - s * 6, P.CHASSIS_Z - 172, P.CHASSIS_Z - 8))
        parts.append(part(f"chassis_rail_{s}", "vehicle", rail, "trim"))
    xs = (-2600, -1500, -350, 800, 1450)
    cross = [box(x - 35, x + 35, -(P.CHASSIS_RAIL_Y - 30), P.CHASSIS_RAIL_Y - 30, P.CHASSIS_Z - 140, P.CHASSIS_Z - 50) for x in xs]
    parts.append(part("chassis_rail_cross", "vehicle", comp(cross), "trim"))
    axle = comp([cyl(48, 2 * (TRACK_R / 2 - 120), (P.REAR_AXLE_X, 0, WHEEL_ZC), "Y"),
                 cyl(140, 220, (P.REAR_AXLE_X, 60, WHEEL_ZC), "Y"),
                 cyl(42, 2 * (TRACK_F / 2 - 160), (FRONT_AXLE_X, 0, WHEEL_ZC), "Y")])
    parts.append(part("chassis_rail_axles", "vehicle", axle, "trim"))
    # ---- cab
    body, glass, xa = _cab()
    parts.append(part("cab_body", "vehicle", body, "body"))
    parts.append(part("cab_glass", "vehicle", glass, "glass"))
    trim = []
    # front bumper + X-Pro wheel-arch cladding + sill cladding + side steps + mirrors + door handles + bonnet garnish
    trim.append(_xz([(NOSE_X - 25, -520), (NOSE_X - 25, -150), (NOSE_X + 260, -150), (NOSE_X + 330, -420),
                     (NOSE_X + 150, -545)], -(SK - 70), SK - 70))
    for s in (1, -1):
        trim.append(_flare(FRONT_AXLE_X, s * (SK - 6), s * FLARE_HW, SILL_Z - 20))
        trim.append(_flare(P.REAR_AXLE_X, s * (SK - 4), s * FLARE_HW, -330))
        trim.append(box(FRONT_AXLE_X + 530, xb - 5, s * (SK - 2), s * (SK + 8), SILL_Z, SILL_Z + 120))
        trim.append(box(FRONT_AXLE_X + 470, P.REAR_AXLE_X - 470, s * (SK - 40), s * (SK + 85), SILL_Z - 105, SILL_Z - 80))
        mx = xa(BELT_Z) + 120
        trim.append(box(mx, mx + 60, s * (SK - 40), s * (SK + 30), BELT_Z + 10, BELT_Z + 50))
        trim.append(_fillet(box(mx - 30, mx + 90, s * (SK + 30), s * (SK + 150), BELT_Z + 20, BELT_Z + 175), "|Y", 25))
        for hx in (-1450, -560):
            trim.append(box(hx, hx + 150, s * (SK - 16), s * (SK + 2), 395, 420))
    for s in (1, -1):
        trim.append(box(xb - 35, xb, s * (SK - 60), s * SK, SILL_Z, BELT_Z + 20))    # C-pillar / rear door shut cap
    def zb(x):                                     # bonnet surface line
        return BONNET_Z[0] + (x - NOSE_X - 70) * (BONNET_Z[1] - BONNET_Z[0]) / (COWL_X - NOSE_X - 70)
    xs0, xs1 = NOSE_X + 95, NOSE_X + 300           # X-Pro black bonnet scoop/garnish (owner photo), raised at the front
    trim.append(_xz([(xs0, zb(xs0) - 2), (xs1, zb(xs1) - 2), (xs1, zb(xs1) + 3), (xs0 + 20, zb(xs0 + 20) + 30),
                     (xs0, zb(xs0) + 26)], -380, 380))
    parts.append(part("cab_body_trim", "vehicle", comp(trim), "trim"))
    # front: dark grille, vertical corner lamps + full-width DRL line, skid plate
    parts.append(part("cab_body_grille", "vehicle",
                      comp([box(NOSE_X - 4, NOSE_X + 1, -560, 560, -110, 250)] +
                           [box(NOSE_X - 8, NOSE_X - 4, -560, 560, z, z + 12) for z in (-80, -25, 30, 85, 140, 195)]), "hole"))
    lamps = [box(NOSE_X - 6, NOSE_X + 1, -760, 760, BONNET_Z[0] - 77, BONNET_Z[0] - 63)]
    for s in (1, -1):
        lamps.append(box(NOSE_X - 6, NOSE_X + 1, s * 600, s * 790, -10, 250))
    parts.append(part("cab_body_lights", "vehicle", comp(lamps), HEADLAMP))
    parts.append(part("cab_body_skid", "vehicle", box(NOSE_X + 40, NOSE_X + 650, -430, 430, -560, -545), "alu_dark"))
    # door shut lines (front door leading edge, B pillar, rear door trailing edge, lower edge)
    lines = []
    for s in (1, -1):
        for x in (xa(BELT_Z) + 60, -1290, -470):
            lines.append(box(x, x + 4, s * (SK - 1), s * (SK + 1), SILL_Z + 125, 300))
        lines.append(box(xa(BELT_Z) + 60, -470, s * (SK - 1), s * (SK + 1), SILL_Z + 121, SILL_Z + 125))
    parts.append(part("cab_body_shutlines", "vehicle", comp(lines), "hole"))
    # bridge-type roof rails (kept clear under the platform side members)
    for s in (1, -1):
        rr = [box(P.CAB_FRONT_X + 90, xb - 190, s * 685, s * 715, P.ROOF_Z + 22, P.ROOF_Z + 45)]
        for x in (P.CAB_FRONT_X + 90, xb - 260):
            rr.append(box(x, x + 70, s * 680, s * 720, P.ROOF_Z, P.ROOF_Z + 45))
        parts.append(part(f"roof_rail_{s}", "vehicle", comp(rr), "trim"))
    # ---- wheels: tyre (wheel_*) + rim (wheel_*_rim) at the published tracks
    for x, tr in ((P.REAR_AXLE_X, TRACK_R), (FRONT_AXLE_X, TRACK_F)):
        for s in (1, -1):
            tyre, rim = _wheel(s)
            c = (x, s * tr / 2, WHEEL_ZC)
            parts.append(part(f"wheel_{int(x)}_{s}", "vehicle", tyre.translate(c), "tyre"))
            parts.append(part(f"wheel_{int(x)}_{s}_rim", "vehicle", rim.translate(c), RIM))
    # ---- context markers: start battery + under-seat outlet box
    bx, by, bz = P.ENGINE_BAY_BATT
    batt = _fillet(box(bx - 130, bx + 130, by - 90, by + 90, bz - 100, bz + 92), "|Z", 6)
    batt = batt.union(box(bx - 120, bx + 120, by - 80, by + 80, bz + 92, bz + 100))
    parts.append(part("start_battery", "markers", batt, "battery"))
    parts.append(part("start_battery_terminals", "markers", comp([cyl(9, 18, (bx + s * 95, by + 55, bz + 109)) for s in (1, -1)]),
                      "copper"))
    anchor("start_battery", (bx, by, bz + 100))
    cx, cy, cz = P.CABIN_SEAT_BOX
    parts.append(part("cabin_outlet_box", "markers", _fillet(box(cx - 60, cx + 60, cy - 110, cy + 110, cz - 50, cz + 50), "|X", 8),
                      "victron_dark"))
    face = [box(cx - 64, cx - 60, cy - 95, cy - 25, cz - 30, cz + 30),             # Anderson SB50 housing
            box(cx - 64, cx - 60, cy + 10, cy + 40, cz - 15, cz + 15),             # USB-C dual
            box(cx - 64, cx - 60, cy + 55, cy + 95, cz - 20, cz + 20)]             # 12 V socket
    parts.append(part("cabin_outlet_face", "markers", comp(face), "anderson_grey"))
    anchor("cabin_outlets", (cx, cy, cz - 50))
    return parts
