"""
Side pockets. The load lid can't be opened with the tent on, so everything is reached from the tailgate:

passenger: LOWER power/control cabinet behind the arch (rear panel = controls + outlets, hinged to reach
           RCBOs / DC fuses / Cerbo) + UPPER long drawer over the arch (pulls out the back) + cable tray above it
driver:    LOWER pull-out utility drawer behind the arch + UPPER long drawer over the arch

v0.8 detail pass (geometry only - envelopes, part names, groups and anchors as v0.7):
- drawer boxes are separate 9 mm ply panels (finger-jointed corners, bottom housed in grooves) so the cut list and
  weight budget see real panels; 3-member full-extension runners; flush stainless paddle latches (rod bolt into a
  keeper on the carcass) so nothing protrudes past the closed tailgate; true U-channel divider slots; finger holes.
- control panel door: 3 mm 5052 overlay door on a vertical piano hinge along the INBOARD edge (a bottom hinge
  can't open: the 45-55 mm deep socket bodies behind the door hit the floor after ~25 deg), EPDM gasket,
  quarter-turn compression latch at the top outboard corner engaging the 30x30 angle stile on the tub-wall side.
- every panel item modelled from its real face (GX Touch 50, Contura II switches + guards, IP66 double GPO with
  flip lids, dual USB-C, SB50 flush housings with dust covers, 12 V socket with cap) + engraved label plates.
- behind the door: rear-facing IP66 RCBO enclosure (clear lid, DIN rail, 3 RCBOs + blank, glands), Blue Sea 5026
  at its real size with blade fuses and the negative bus, Cerbo GX MK2 with its connector rows, slotted wiring duct,
  cable glands where the trunk drops in from the wall channel and where the slide harness leaves the cabinet.

Performance: geometry is built once per configuration and cached (travel/camp builds and clash.py reuse it);
moving drawer parts are built closed and translated, door parts rotated. Decorative multi-solid features are
compounds (no booleans); fabricated panels stay single solids so mass (volume / thickness) and the cut list hold.
"""
import cadquery as cq

import params as P

from .core import S, anchor, box, cyl, part

T = 12   # carcass ply
T9 = 9
RUN = 13  # light-duty side runner thickness

# ------------------------------------------------------------------ purchased-part sizes used for the detail
RUNNER_H = 45            # [EST] 45 mm x 12.7 mm 3-member ball-bearing slide section (light/medium duty series)
UPPER_RUNNER_L = 1219    # [DES] 48" full extension, upper drawers
LOWER_RUNNER_L = 559     # [EST] 22" full extension, utility drawer (BOM says ~600 mm; a 24"/610 runner won't fit the 609 box)
DIV_CH = (12.7, 8.0, 1.2)  # [DES] divider U-channel: width x depth x wall -> 10.3 mm gap for 9 mm ply
#                            (BOM's 12x12x1.6 has only 8.8 mm inside - too tight for 9 mm marine ply)
PADDLE = (100, 64, 84, 48)  # [EST] stainless flush paddle latch: flange W x H, recess W x H (4WD-drawer type)
GX_SCREEN = (108, 65)     # [PUB] GX Touch 50: 5" 800x480 active area (body 128 x 87 x 12.4 = P.GX_TOUCH)
CONTURA = (23.4, 42.0, 21.1, 36.8)   # Carling Contura II: bezel W x H [EST], cut-out 0.83 x 1.45 in [PUB]
FUSE_5026 = (164, 39, 84)  # [PUB, retailer listing 6.47 x 1.52 x 3.32 in] Blue Sea 5026 (along X, off-wall, tall)
#                            params.FUSE_BLOCK (211 x 45 x 140) is kept as the reserved envelope
ATO = (5.1, 19.1, 14)      # [PUB] ATO/ATC blade fuse thickness x width; height proud of the block [EST]
RCBO_ENC = (92, 118, 190)  # [EST] IP66 4-module DIN enclosure (depth X incl. 6 mm lid, width Y, height Z); BOM 140x180x100
DIN_MOD = (18, 85, 66)     # [PUB] 1-module RCBO 1P+N: width, height; depth from the rail [EST]
SB50_HOUSING = (56, 60)    # [EST] SB50 flush mount housing face (Trailer Vision TVN-333820-50 / Altronics P7862 class)
USBC_R, SOCK12_R = 16.5, 18  # [EST] dual USB-C bezel (29 mm cut-out), 12 V accessory socket flange

# ------------------------------------------------------------------ local colours (RGBA)
K = dict(
    black=(28, 28, 30, 255), rubber=(16, 16, 17, 255), grey=(200, 202, 205, 255), duct=(150, 152, 155, 255),
    screen=(10, 22, 36, 255), ui=(0, 120, 210, 255), lens_red=(235, 40, 30, 255), lens_blue=(40, 140, 255, 255),
    plate=(30, 31, 34, 255), text=(242, 242, 236, 255), smoke=(70, 72, 78, 170), clear=(205, 225, 240, 70),
    white=(242, 242, 238, 255), fuse10=(215, 35, 35, 255), fuse15=(40, 95, 215, 255), fuse20=(240, 205, 30, 255),
    tin=(205, 205, 198, 255), green=(40, 150, 75, 255), cerbo=(0, 92, 170, 255), ply_line=(150, 112, 70, 255),
    sb50=(205, 35, 35, 255), rocker=(45, 45, 48, 255), cover=(60, 62, 66, 255),
)

# ------------------------------------------------------------------ geometry cache + spec realisation
_CACHE = {}
FIX, MOVE, HALF, DOOR, ANCHOR = range(5)


def _memo(key, fn):
    if key not in _CACHE:
        _CACHE[key] = fn()
    return _CACHE[key]


def _realise(specs, ext=0.0, door_deg=0.0, hinge=None):
    """specs: (mode, name, group, shape, colour, kw). MOVE translates by ext, HALF by ext/2, DOOR rotates about the
    vertical hinge axis; a runner is (FIX, MOVE/HALF members) as a tuple shape. ANCHOR re-registers anchors."""
    out = []
    for mode, name, grp, shp, col, kw in specs:
        if mode == ANCHOR:
            anchor(name, shp)
            continue
        if isinstance(shp, tuple):                      # 3-member runner: fixed, intermediate, inner
            o, m, n = shp
            shp = cq.Compound.makeCompound([o, m.translate((ext / 2, 0, 0)) if ext else m,
                                            n.translate((ext, 0, 0)) if ext else n])
        elif mode == MOVE and ext:
            shp = shp.translate((ext, 0, 0))
        elif mode == HALF and ext:
            shp = shp.translate((ext / 2, 0, 0))
        elif mode == DOOR and door_deg:
            shp = shp.rotate((hinge[0], hinge[1], 0), (hinge[0], hinge[1], 1), door_deg)
        out.append(part(name, grp, shp, col, **kw))
    return out


def _comp(ws):
    """Compound of disjoint/overlapping solids without booleans (decorative features, cutters)."""
    vals = []
    for w in ws:
        if w is None:
            continue
        vals += w.vals() if isinstance(w, cq.Workplane) else [w]
    return cq.Compound.makeCompound(vals)


def _txt(s, h, yc, zc, x, depth=0.35):
    """Printed legend facing +X (readable from the tailgate) at X = x + depth: only the glyph faces are kept
    (no side walls - 1/5 of the triangles). None if no font is available."""
    try:
        w = cq.Workplane("YZ", origin=(x, yc, zc)).text(s, h, depth, halign="center", valign="center", kind="bold")
        return cq.Compound.makeCompound(w.faces(">X").vals())
    except Exception:
        return None


def _txt_y(s, h, xc, zc, y, depth=0.35):
    """Legend on a face looking -Y (passenger-side outboard faces), glyph faces only."""
    try:
        w = cq.Workplane("XZ", origin=(xc, y, zc)).text(s, h, depth, halign="center", valign="center", kind="bold")
        return cq.Compound.makeCompound(w.faces("<Y").vals())
    except Exception:
        return None


def _pcyl(r, h, centre, axis="Z", n=8):
    """Low-poly cylinder (n-gon prism) for screw heads, studs and glands - keeps the GLB small."""
    w = cq.Workplane("XY").polygon(n, 2 * r).extrude(h).translate((0, 0, -h / 2))
    if axis == "X":
        w = w.rotate((0, 0, 0), (0, 1, 0), 90)
    elif axis == "Y":
        w = w.rotate((0, 0, 0), (1, 0, 0), 90)
    return w.translate(centre)


def _chamfer(w, sel, d):
    try:
        return w.edges(sel).chamfer(d)
    except Exception:
        return w


def _cb(x0, x1, yc, zc, w, h):
    """Box spanning x0..x1, centred on (yc, zc) with width w (Y) and height h (Z)."""
    return box(x0, x1, yc - w / 2, yc + w / 2, zc - h / 2, zc + h / 2)


def _cx(r, x0, x1, yc, zc):
    """Cylinder along X from x0 to x1."""
    return cyl(r, x1 - x0, ((x0 + x1) / 2, yc, zc), "X")


def _runner(xf, L, yc, sd, z0, H=RUNNER_H, t=RUN):
    """3-member full-extension ball-bearing slide, closed. xf = open end of the fixed member, yc = cabinet-side face,
    sd = +-1 direction from that face towards the drawer side, z0 = bottom edge.
    Returns ((outer, intermediate, inner), disconnect lever)."""
    def yy(a, b):
        return sorted((yc + sd * a, yc + sd * b))
    w = 1.2
    xo0 = xf - L
    outer = [box(xo0, xf, *yy(0, w), z0, z0 + H), box(xo0, xf, *yy(0, 8), z0, z0 + w),
             box(xo0, xf, *yy(0, 8), z0 + H - w, z0 + H)]
    outer += [box(x - 3, x + 3, *yy(w, w + 1), z0 + H / 2 - 3, z0 + H / 2 + 3)
              for x in (xo0 + 40 + k * (L - 80) / 4 for k in range(5))]          # mounting screws
    mid = [box(xo0 + 10, xf - 10, *yy(3.5, 4.7), z0 + 3.2, z0 + H - 3.2),
           box(xo0 + 10, xf - 10, *yy(3.5, 10), z0 + 3.2, z0 + 4.4), box(xo0 + 10, xf - 10, *yy(3.5, 10), z0 + H - 4.4, z0 + H - 3.2)]
    inner = [box(xo0 + 30, xf - 2, *yy(t - 1.5, t), z0 + 7.5, z0 + H - 7.5),
             box(xo0 + 30, xf - 2, *yy(7.5, t), z0 + 7.5, z0 + 8.7), box(xo0 + 30, xf - 2, *yy(7.5, t), z0 + H - 8.7, z0 + H - 7.5)]
    lever = box(xf - 70, xf - 40, *yy(9, t - 1.5), z0 + 16, z0 + H - 16)
    return (_comp(outer), _comp(mid), _comp(inner)), S(lever)


def _ply_box(base, g, x0, x1, ya, yb, z0, z1, t=T9, front_cut=None, bottom_up=8):
    """Open-top 9 mm ply drawer box: finger-jointed corners, bottom housed 4.5 mm into grooves.
    Specs (MOVE): <base> (bottom), <base>_side_0/1, <base>_back (x0 end), <base>_front (x1 end, the tailgate end)."""
    y0, y1 = sorted((ya, yb))
    H = z1 - z0
    n = max(3, int(round(H / 22)))
    n += 1 - n % 2
    fz = [z0 + H * k / n for k in range(n + 1)]
    bands = lambda par: [(fz[k], fz[k + 1]) for k in range(n) if k % 2 == par]  # noqa: E731
    cut_s = _comp(box(xa, xb, y0 - 1, y1 + 1, za, zb) for xa, xb in ((x0 - 1, x0 + t), (x1 - t, x1 + 1))
                  for za, zb in bands(1))
    cut_e = _comp(box(x0 - 1, x1 + 1, ya_, yb_, za, zb) for ya_, yb_ in ((y0 - 1, y0 + t), (y1 - t, y1 + 1))
                  for za, zb in bands(0))
    gd = 4.5
    zb = z0 + bottom_up
    bot = box(x0 + t - gd, x1 - t + gd, y0 + t - gd, y1 - t + gd, zb, zb + t)
    bs = bot.val()
    sides = [box(x0, x1, y0, y0 + t, z0, z1).cut(cut_s).cut(bs), box(x0, x1, y1 - t, y1, z0, z1).cut(cut_s).cut(bs)]
    back = box(x0, x0 + t, y0, y1, z0, z1).cut(cut_e).cut(bs)
    front = box(x1 - t, x1, y0, y1, z0, z1).cut(cut_e).cut(bs)
    if front_cut is not None:
        front = front.cut(front_cut)
    m = dict(fab=True, mat="Ply 9 marine")
    specs = [(MOVE, base, g, S(bot), "ply", m), (MOVE, f"{base}_side_0", g, S(sides[0]), "ply", m),
             (MOVE, f"{base}_side_1", g, S(sides[1]), "ply", m), (MOVE, f"{base}_back", g, S(back), "ply", m),
             (MOVE, f"{base}_front", g, S(front), "ply", m)]
    return specs, (y0 + t, y1 - t, zb + t)


def _u_channel(xd, yface, d, zc0, zc1):
    """Divider U-channel (single solid) on a box inner face at yface, opening in direction d (+-1)."""
    w, dp, wl = DIV_CH
    ys = sorted((yface, yface + d * dp))
    yi = sorted((yface + d * wl, yface + d * (dp + 1)))
    return [S(box(xd - w / 2, xd + w / 2, *ys, zc0, zc1).cut(box(xd - w / 2 + wl, xd + w / 2 - wl, *yi, zc0 - 1, zc1 + 1)))]


def _paddle_latch(xf, yc, zl, bolt_to_y, depth_in=9):
    """Flush stainless paddle latch (lockable). xf = outer face of the drawer front plate. Returns (stainless, pan):
    flange + paddle + key barrel + rod bolt (to bolt_to_y), and the black recess pan + housing."""
    fw, fh, rw, rh = PADDLE
    flange = _cb(xf, xf + 1.5, yc, zl, fw, fh).cut(_cb(xf - 1, xf + 2, yc, zl, rw, rh))
    paddle = _cb(xf - 2.5, xf, yc, zl + 6, rw - 6, rh - 14)      # finger gap below the paddle
    key = _cx(5.5, xf, xf + 1.5, yc + 26, zl + 8)
    bolt = cyl(3, abs(bolt_to_y - yc), (xf - depth_in - 23, (bolt_to_y + yc) / 2, zl), "Y")
    pan = _cb(xf - 25, xf, yc, zl, rw, rh).cut(_cb(xf - 23.8, xf + 1, yc, zl, rw - 2.4, rh - 2.4))
    housing = _cb(xf - depth_in - 32, xf - 25, yc, zl, 70, 40)
    return _comp([flange, paddle, key, bolt]), _comp([pan, housing])


def _ply_lines(x, spans, axis):
    """Lamination lines on exposed ply end faces at X = x. spans: [((a0, a1), (b0, b1))] with a = along the edge,
    b = across the thickness. axis 'Z': the panel stands vertical (lines run along Z), 'Y': lies flat."""
    out = []
    for (a0, a1), (b0, b1) in spans:
        nply = 7 if abs(b1 - b0) > 10 else 5
        for k in range(1, nply):
            b = b0 + (b1 - b0) * k / nply
            if axis == "Z":
                out.append(box(x, x + 0.4, b - 0.25, b + 0.25, a0, a1))
            else:
                out.append(box(x, x + 0.4, a0, a1, b - 0.25, b + 0.25))
    return out


# ======================================================================================== upper drawers
def _upper_drawer_specs(yo, yi, gap, gland):
    s = 1 if yi > 0 else -1
    g = "utility" if s > 0 else "power_cabinet"
    nm = "ud_driver" if s > 0 else "ud_pass"
    sp = []
    x0, x1 = 5, P.POCKET_X1
    z0, z1 = P.UPPER_Z0, P.UPPER_Z1
    yp = yo - s * gap
    # carcass: floor with 4 mm dados for both walls (spans the arch top and the lower unit)
    floor = box(x0, x1, yo, yi, z0, z0 + T9).cut(_comp([box(x0 - 1, x1 + 1, yi, yi + s * T, z0 + T9 - 4, z0 + T9 + 1),
                                                        box(x0 - 1, x1 + 1, yp, yp - s * T9, z0 + T9 - 4, z0 + T9 + 1)]))
    if gland:
        floor = floor.cut(cyl(10.5, 40, (gland[0], gland[1], z0 + 4)))
    sp.append((FIX, f"{nm}_floor", g, S(floor), "ply", dict(fab=True, mat="Ply 9 marine")))
    sp.append((FIX, f"{nm}_inner_wall", g, S(box(x0, x1, yi, yi + s * T, z0 + T9 - 4, z1)), "ply", dict(fab=True, mat="Ply 12 marine")))
    sp.append((FIX, f"{nm}_runner_panel", g, S(box(x0, x1, yp, yp - s * T9, z0 + T9 - 4, z1)), "ply", dict(fab=True, mat="Ply 9 marine")))
    # exposed rear ply edges + aluminium angle trim on the floor edge (the drawer front closes over it)
    sp.append((FIX, f"{nm}_ply_lines", g, _comp(_ply_lines(x1, [((z0 + T9, z1), (yi, yi + s * T)),
                                                                ((z0 + T9, z1), (yp, yp - s * T9))], "Z")), K["ply_line"], {}))
    trim = _comp([box(x1, x1 + 1.6, yo, yi, z0 - 2, z0 + T9),
                  box(x1 - 20, x1 + 1.6, yi + s * T, yp - s * T9, z0 + T9, z0 + T9 + 1.6)])
    sp.append((FIX, f"{nm}_trim", g, trim, "alu", dict(kg=0.05)))
    # drawer box (built closed; MOVE specs follow the drawer) on a pair of 48" full-extension runners
    ya = yp - s * (T9 + RUN)
    yb = yi + s * (T + RUN)
    dl = x1 - x0 - 30
    dx1 = x1
    dx0 = dx1 - dl
    zb0, zb1 = z0 + T9 + 4, z1 - 6
    yc = (ya + yb) / 2
    zl = zb1 - 37                                     # latch / handle centre
    recess = _cb(dx1 - T9 - 1, dx1 + 4, yc, zl, PADDLE[2], PADDLE[3])
    bspecs, (ywa, ywb, zbot) = _ply_box(f"{nm}_box", g, dx0, dx1, ya, yb, zb0, zb1, front_cut=recess)
    sp += bspecs
    # removable dividers: lift-out 9 mm ply panels in aluminium U-channel slots on both inner faces (120 mm pitch)
    pitch = 120
    xs = [dx0 + T9 + 60 + i * pitch for i in range(int((dl - 15 - 2 * T9 - 60) // pitch))]
    slots = _comp(b for x in xs for yw, d in ((ywa, 1), (ywb, -1)) for b in _u_channel(x, yw, d, zbot, zb1 - 2))
    sp.append((MOVE, f"{nm}_divider_slots", g, slots, "alu", dict(kg=0.04 * 2 * len(xs), n_slots=len(xs))))
    ymid = (ywa + ywb) / 2
    for k, i in enumerate((2, 5, 8)):
        if i < len(xs):
            xd = xs[i]
            dv = box(xd - 4.5, xd + 4.5, ywa + DIV_CH[2], ywb - DIV_CH[2], zbot, zb1 - 30).cut(
                box(xd - 6, xd + 6, ymid - 22, ymid + 22, zb1 - 62, zb1 - 46))      # finger hole
            sp.append((MOVE, f"{nm}_divider_{k}", g, S(dv), "ply", dict(fab=True, mat="Ply 9 marine", removable=True)))
    # 3 mm aluminium face plate over the box front (covers the runners) with the paddle-latch recess
    sp.append((MOVE, f"{nm}_front", g, S(box(dx1, dx1 + 3, ya + s * 6, yb - s * 6, zb0 - 2, zb1).cut(recess)),
               "alu_dark", dict(fab=True, mat="Plate 3 5052")))
    ykeep = yi + s * (T + 5)
    stainless, pan = _paddle_latch(dx1 + 3, yc, zl, ykeep)
    sp.append((MOVE, f"{nm}_pull", g, stainless, "alu", dict(kg=0.25)))
    sp.append((MOVE, f"{nm}_pull_pan", g, pan, K["black"], {}))
    # latch keeper on the carcass inner wall (the rod bolt engages it when the drawer is shut)
    kx = x1 - 32
    keeper = box(kx - 12, kx + 12, yi + s * T, yi + s * (T + 10), zl - 14, zl + 14).cut(cyl(4, 30, (kx, ykeep, zl), "Y"))
    sp.append((FIX, f"{nm}_keeper", g, S(keeper), "alu", dict(kg=0.04)))
    for k, (yy, sd) in enumerate(((yp - s * T9, -s), (yi + s * T, s))):
        members, lever = _runner(x1 - 6, UPPER_RUNNER_L, yy, sd, zb0 + 40)
        sp.append((FIX, f"{nm}_runner_{k}", g, members, "runner", dict(kg=1.6)))
        sp.append((MOVE, f"{nm}_runner_lever_{k}", g, lever, K["black"], {}))
    return sp


def _upper_drawer(yo, yi, ext, gap=0.0, gland=None):
    """Full-length drawer over the arch. yo = wall side, yi = inboard side (signed). gland = (x, y) cable drop."""
    sp = _memo(("ud", yo, yi, gap, gland), lambda: _upper_drawer_specs(yo, yi, gap, gland))
    return _realise(sp, ext)


# ======================================================================================== passenger cabinet
def _passenger_specs():
    sp = []
    g = "power_cabinet"
    yo, yi = -P.POCKET_Y_OUT, -P.POCKET_Y_IN
    x0 = P.POCKET_X0
    xr = P.REAR_PANEL_X
    zt = P.LOWER_TOP_Z
    gl = (P.FACTORY_OUTLET[0] + 30, yo + 11)             # trunk drop: wall channel -> cabinet (wiring 'cab_in')

    def fx(name, w, col, grp=g, **kw):
        sp.append((FIX, name, grp, S(w) if isinstance(w, cq.Workplane) else w, col, kw))

    def dp(name, w, col, grp=g, **kw):
        sp.append((DOOR, name, grp, S(w) if isinstance(w, cq.Workplane) else w, col, kw))

    def anc(name, xyz):
        sp.append((ANCHOR, name, None, tuple(float(v) for v in xyz), None, None))

    # ---- carcass (floor -> arch height). Top sits in a 6 mm rebate on the inner wall; front/bottom butt-jointed.
    iw = box(x0, xr, yi, yi - T, 0, zt).cut(box(x0 - 1, xr + 1, yi - 6, yi - T - 1, zt - T, zt + 1))
    fx("pc_inner_wall", iw, "ply", fab=True, mat="Ply 12 marine")
    fx("pc_front", box(x0, x0 + T, yo, yi - T, 0, zt - T), "ply", fab=True, mat="Ply 12 marine")
    fx("pc_top", box(x0, xr, yo, yi - 6, zt - T, zt).cut(cyl(10.5, 40, (gl[0], gl[1], zt - 6))), "ply", fab=True,
       mat="Ply 12 marine")
    fx("pc_bottom", box(x0 + T, xr, yo, yi - T, 0, T), "ply", fab=True, mat="Ply 12 marine")
    # door stile on the tub-wall side (there is no outboard ply wall): carries the gasket face and the latch keeper
    fx("pc_door_stile", box(xr - 30, xr, yo, yo + 3, T, zt - T).union(box(xr - 3, xr, yo, yo + 30, T, zt - T)), "alu",
       fab=True, mat="Angle 30x30x3 6060")
    # screws: inner wall into the bottom and front panel edges (seen from the slide side)
    scr = [_pcyl(4, 1.2, (x, yi + 0.6, T / 2), "Y") for x in range(x0 + 60, int(xr) - 20, 110)]
    scr += [_pcyl(4, 1.2, (x0 + T / 2, yi + 0.6, z), "Y") for z in (40, 140, 240)]
    fx("pc_screws", _comp(scr), "alu_dark")

    # ---- rear panel = overlay door on a vertical piano hinge (inboard edge), gasket, quarter-turn latch
    BF = xr + 2.0                             # back face of the door (2 mm compressed gasket)
    XF = BF + 3                               # outer face of the door (panel items mount here)
    dy0, dy1, dz0, dz1 = yo + 1, yi - 8.5, 1, zt - 1
    cut = []

    def face_anchor(n, y, z):
        anc(n, (xr - 30, y, z))               # cable end behind the door (x as v0.7)

    legends = []
    # GX Touch 50 (surface mount, 12.4 proud) - centre 8 mm lower than v0.7 to clear the latch
    gy, gz = yo + 74, 223.5
    gw, gh, gd = P.GX_TOUCH[0], P.GX_TOUCH[2], 12.4
    dp("pc_gx_touch_50", _comp([_chamfer(_cb(XF, XF + gd, gy, gz, gw, gh), ">X", 1.5), _cx(9, BF - 18, BF, gy, gz)]),
       "victron_dark", kg=0.3)
    cut.append(_cx(10, xr - 1, XF + 1, gy, gz))
    sw_, sh_ = GX_SCREEN
    dp("pc_gx_touch_50_screen", _cb(XF + gd, XF + gd + 0.3, gy, gz + 1, sw_, sh_), K["screen"])
    ui = [(-36, 14, 30, 22), (0, 14, 30, 22), (36, 14, 30, 22), (-36, -15, 30, 22), (18, -15, 66, 22), (0, 29, 104, 4)]
    dp("pc_gx_touch_50_ui", _comp(_cb(XF + gd + 0.3, XF + gd + 0.5, gy + a, gz + 1 + b, w, h) for a, b, w, h in ui), K["ui"])
    face_anchor("pc_gx_touch_50", gy, gz)

    # two illuminated Contura II rockers (battery isolate = ML-RBS, inverter remote on/off) with guards + legends
    swy = yi - 32
    bw, bh, cw, ch = CONTURA
    guards = []
    for n, z, lens, lg in (("pc_sw_battery", 252, K["lens_red"], "BATT"), ("pc_sw_inverter", 208, K["lens_blue"], "INV")):
        dp(n, _comp([_chamfer(_cb(XF, XF + 4, swy, z, bw, bh), ">X", 0.8), _cb(BF - 35, BF, swy, z, cw - 0.6, ch - 0.6)]),
           K["black"], kg=0.05)
        cut.append(_cb(xr - 1, XF + 1, swy, z, cw, ch))
        piv = ((XF + 4, swy - 20, z), (XF + 4, swy + 20, z))
        dp(f"{n}_rocker", _cb(XF + 1, XF + 7, swy, z, bw - 4.4, bh - 6).rotate(*piv, 7), K["rocker"])
        dp(f"{n}_lens", _cb(XF + 7, XF + 7.4, swy, z + 11, 9, 6).rotate(*piv, 7), lens)
        lt = _txt(lg, 4.2, swy, z - 6, XF + 7, 0.3)
        legends.append(lt.rotate(*piv, 7) if lt is not None else None)
        guards += [_cb(XF, XF + 16, swy + d * (bw / 2 + 1.3), z, 2.4, bh + 3) for d in (-1, 1)]
        guards.append(_cb(XF, XF + 6, swy, z - bh / 2 - 0.7, bw + 5, 1.6))
        face_anchor(n, swy, z)
    dp("pc_sw_guards", _comp(guards), K["black"])

    # flush double GPO (Clipsal Iconic horizontal double, 120 x 78 skin, as on the power pod) under one clear
    # weatherproof flip cover. v0.9: an IP66 twin (~146 x 117) doesn't fit the panel; the panel sits recessed
    # 105 mm behind the tailgate and under the lid, so a flush GPO + cover is used to keep the panel size.
    py_, pz = yo + 70, 127
    gpo = [_chamfer(_cb(XF, XF + 6, py_, pz, 120, 78), ">X", 1.2), _cb(BF - 45, BF, py_, pz, 100, 64)]
    slots, rockers = [], []
    for dyy in (-30, 30):
        cy_ = py_ + dyy
        # AS/NZS 3112 face: two flat pins at +-30 deg (inverted V) above a vertical earth pin
        slots += [_cb(XF + 6, XF + 6.4, cy_ + dy_, pz - 4, 1.8, 7).rotate((0, cy_ + dy_, pz - 4), (1, cy_ + dy_, pz - 4), ang)
                  for dy_, ang in ((-7, 30), (7, -30))]
        slots.append(_cb(XF + 6, XF + 6.4, cy_, pz - 18, 1.8, 8))
        rockers.append(_cb(XF + 6, XF + 9, cy_, pz + 24, 16, 10))                      # Iconic rocker switch
    dp("pc_gpo_double", _comp(gpo), K["white"], kg=0.4)
    dp("pc_gpo_double_slots", _comp(slots + rockers), K["black"])
    cut.append(_cb(xr - 1, XF + 1, py_, pz, 100, 64))
    lids = [_cb(XF + 10, XF + 13, py_, pz, 118, 82),                                    # clear top-hinged cover
            _cb(XF + 6, XF + 13, py_, pz + 40, 118, 3),                                 # hinge rail
            _cb(XF + 10, XF + 22, py_, pz - 42, 20, 3)]                                 # thumb tab
    dp("pc_gpo_double_lids", _comp(lids), K["smoke"])
    face_anchor("pc_gpo_double", py_, pz)

    # 2 x dual USB-C PD sockets (29 mm cut-out), 4 mm inboard of v0.7 to clear the hinge leaf
    bez = []
    uy = swy - 2
    for n, z in (("pc_usbc_1", 158), ("pc_usbc_2", 114)):
        b = _cx(USBC_R, XF, XF + 4, uy, z).cut(_comp(_cb(XF + 1, XF + 5, uy, z + dz, 8.4, 2.6) for dz in (-5, 5)))
        dp(n, _comp([b, _cx(14, BF - 42, BF, uy, z)]), "usb", kg=0.05)
        cut.append(_cx(14.5, xr - 1, XF + 1, uy, z))
        bez.append(_cx(USBC_R + 0.6, XF + 3.2, XF + 4.2, uy, z).cut(_cx(USBC_R - 2.2, XF, XF + 5, uy, z)))
        face_anchor(n, uy, z)
    dp("pc_usbc_bezels", _comp(bez), "alu")

    # 2 x Anderson SB50 flush housings: #1 dust cover shut, #2 flipped open showing the red SB50
    hw_, hh_ = SB50_HOUSING
    plugs = []
    for n, y, zz, opn in (("pc_anderson_1", yo + 49, 50, False), ("pc_anderson_2", yo + 109, 50, True)):
        h = _chamfer(_cb(XF, XF + 8, y, zz, hw_, hh_), ">X", 1.5).cut(_cb(XF + 2, XF + 9, y, zz - 2, 40, 20))
        dp(n, _comp([h, _cb(BF - 50, BF, y, zz - 2, 38, 18)]), K["black"], kg=0.1)
        cut.append(_cb(xr - 1, XF + 1, y, zz - 2, 38, 18))
        plugs.append(_cb(XF + 2, XF + 5, y, zz - 2, 38, 17).cut(_comp([_cb(XF + 3, XF + 6, y - 9, zz - 2, 9, 6),
                                                                       _cb(XF + 3, XF + 6, y + 9, zz - 2, 9, 6)])))
        cov = _comp([_cb(XF + 8, XF + 11, y, zz - 3, 46, 30), _cb(XF + 8, XF + 14, y, zz - 18, 16, 3)])
        if opn:
            cov = cov.rotate(cq.Vector(XF + 8, 0, zz + 12), cq.Vector(XF + 8, 1, zz + 12), -100)
        dp(f"{n}_cover", cov, K["cover"])
        face_anchor(n, y, zz)
    dp("pc_anderson_plugs", _comp(plugs), K["sb50"])

    # 12 V accessory socket with its rubber cap
    dp("pc_12v", _comp([_cx(SOCK12_R, XF, XF + 3, uy, 52), _cx(14, XF + 3, XF + 9, uy, 52), _cx(13, BF - 55, BF, uy, 52),
                        _cx(14.5, XF + 9, XF + 15, uy, 52), _cb(XF + 3, XF + 6, uy, 52 - 18, 8, 6)]), "usb", kg=0.05)
    cut.append(_cx(14.5, xr - 1, XF + 1, uy, 52))
    face_anchor("pc_12v", uy, 52)

    # engraved label plates (traffolyte style: black plate, white legend)
    plates = [(py_, 175.5, 96, 7.5, "240V 10A  RCD"), (yo + 49, 13, 44, 6.5, "12V 50A"), (yo + 109, 13, 44, 6.5, "12V 50A"),
              (uy, 91, 32, 8, "USB-C"), (gy + 12, 276, 52, 8, "POWER")]
    dp("pc_labels", _comp(_cb(XF, XF + 0.6, y, z, w, h) for y, z, w, h, _ in plates), K["plate"])
    legends += [_txt(t_, h - 3.2, y, z, XF + 0.6) for y, z, w, h, t_ in plates]
    legends.append(_txt("12V", 5.5, uy, 52, XF + 15))
    if any(lg_ is not None for lg_ in legends):
        dp("pc_labels_text", _comp(legends), K["text"])

    # quarter-turn compression latch (keyed) at the top outboard corner; its cam hooks behind the stile
    ly, lz = yo + 40, 278
    dp("pc_door_latch", _comp([_cx(9, XF, XF + 4, ly, lz).cut(_cb(XF + 3, XF + 5, ly, lz, 1.6, 9)),
                               _cx(8, BF - 14, BF, ly, lz), box(xr - 6, xr - 3, yo + 6, ly, lz - 5, lz + 5)]), "alu", kg=0.06)
    cut.append(_cx(8.5, xr - 1, XF + 1, ly, lz))

    # door plate (3 mm 5052, overlay) + gasket + hinge leaf/screws on the door
    dp("pc_door", box(BF, XF, dy0, dy1, dz0, dz1).cut(_comp(cut)), "alu", fab=True, mat="Plate 3 5052")
    dp("pc_door_gasket", box(xr, BF, dy0 + 2, dy1 - 2, dz0 + 2, dz1 - 2).cut(
        box(xr - 1, BF + 1, dy0 + 10, dy1 - 10, dz0 + 10, dz1 - 10)), K["rubber"])
    dp("pc_door_hardware", _comp([box(XF, XF + 1.2, dy1 - 7, dy1, 6, zt - 6)] +
                                 [_pcyl(2.6, 0.8, (XF + 1.6, dy1 - 3.5, z), "X") for z in (30, 100, 190, 260)]), "alu_dark")
    # fixed half of the piano hinge: knuckle + leaf on the inner wall's inboard face
    fx("pc_door_hinge", _comp([cyl(3.5, zt - 12, (BF + 1.5, yi - 5, zt / 2)), box(xr - 25, xr + 1, yi, yi + 1.2, 6, zt - 6)]),
       "alu_dark", kg=0.15)

    # ---- behind the door
    # IP66 RCBO enclosure facing the door (clear lid): DIN rail, 3 RCBOs 1P+N + blank, glands underneath + side entry
    ed, ew, eh = RCBO_ENC
    ex1 = xr - 82                                   # lid face: >30 mm clear of the socket bodies on the door
    ex0 = ex1 - ed
    ey1 = yi - T - 2
    ey0 = ey1 - ew
    ez0 = 60
    enc = box(ex0, ex1 - 6, ey0, ey1, ez0, ez0 + eh).cut(box(ex0 + 3, ex1, ey0 + 3, ey1 - 3, ez0 + 3, ez0 + eh - 3))
    lugs = [box(x - 7, x + 7, ey1, yi - T, z - 4, z + 4) for x in (ex0 + 15, ex1 - 25) for z in (ez0 + 12, ez0 + eh - 12)]
    fx("pc_rcbo_enclosure", _comp([enc] + lugs), K["grey"], grp="electrical", kg=1.2)
    anc("rcbo", (xr - 90, yi - T - 120, 200))
    fx("pc_rcbo_lid", box(ex1 - 6, ex1, ey0, ey1, ez0, ez0 + eh), K["clear"], grp="electrical")
    ry = (ey0 + ey1) / 2
    rz = ez0 + eh / 2 + 5
    rail = [box(ex0 + 3, ex0 + 10.5, ey0 + 8, ey1 - 8, rz - 17.5, rz + 17.5)]
    rail += [_pcyl(3, 7.1, (ex1 - 2.95, y, z), "X") for y in (ey0 + 6, ey1 - 6) for z in (ez0 + 6, ez0 + eh - 6)]   # lid screws
    fx("pc_rcbo_din", _comp(rail), "alu", grp="electrical")
    mw, mh, md = DIN_MOD
    mods, togg = [], []
    xm = ex0 + 10.5
    for k in range(4):
        y = ry - 1.5 * mw + k * mw
        mods += [_cb(xm, xm + md - 16, y, rz, mw - 0.4, mh), _cb(xm + md - 16, xm + md, y, rz, mw - 0.4, 45)]
        if k < 3:
            togg += [_cb(xm + md, xm + md + 8, y, rz + 7, 7, 12), _cb(xm + md, xm + md + 2, y, rz - 14, 6, 5)]
    fx("pc_rcbo_modules", _comp(mods), K["white"], grp="electrical")
    fx("pc_rcbo_toggles", _comp(togg), K["black"], grp="electrical")
    glands = [w for y in (ry - 34, ry, ry + 34) for w in (_pcyl(10, 16, (ex0 + 46, y, ez0 - 8), n=12),
                                                          _pcyl(12, 4, (ex0 + 46, y, ez0 - 2), n=6))]
    glands += [_pcyl(10, 14, (xr - 98, ey0 - 7, 200), "Y", 12), _pcyl(12, 4, (xr - 98, ey0 - 2, 200), "Y", 6)]
    fx("pc_rcbo_glands", _comp(glands), K["black"], grp="electrical")

    # Blue Sea 5026 at its real size: 12 ATO blade fuses in two rows, + bus stud, negative bus with 12 screws
    fl, ft, fh = FUSE_5026
    fcx, fz1 = xr - 372 + P.FUSE_BLOCK[0] / 2, 70 + P.FUSE_BLOCK[2]
    fx0, fx1, fz0 = fcx - fl / 2, fcx + fl / 2, fz1 - fh
    fy0, fy1 = yi - T, yi - T - 25
    fx("dc_fuse_block", _chamfer(box(fx0, fx1, fy0, fy1, fz0, fz1), "<Y", 2), K["black"], grp="electrical", kg=0.6)
    anc("dc_fuse_block", (xr - 372 + P.FUSE_BLOCK[0] / 2, yi - T - P.FUSE_BLOCK[1], 70 + P.FUSE_BLOCK[2]))
    rows = (fz0 + 56, fz0 + 32)
    fuses = {"10": [], "15": [], "20": []}
    rating = ["10", "10", "15", "10", "20", "15", "10", "15", "20", "10", "15", "20"]
    for r, zr in enumerate(rows):
        for i in range(6):
            x = fx0 + 52 + i * 13.5
            fuses[rating[r * 6 + i]].append(box(x - ATO[0] / 2, x + ATO[0] / 2, fy1, fy1 - ATO[2], zr - ATO[1] / 2, zr + ATO[1] / 2))
    for rt, col in (("10", "fuse10"), ("15", "fuse15"), ("20", "fuse20")):
        fx(f"pc_fuse_blades_{rt}a", _comp(fuses[rt]), K[col], grp="electrical")
    bus = [box(fx0 + 30, fx1 - 12, fy1, fy1 - 2, fz0 + 4, fz0 + 12)]
    bus += [_pcyl(3, 2, (fx0 + 38 + i * 10, fy1 - 3, fz0 + 8), "Y", 6) for i in range(12)]
    bus += [_pcyl(3, 2, (fx0 + 52 + i * 13.5, fy1 - 1, fz1 - 6), "Y", 6) for i in range(6)]
    bus += [_pcyl(5, 12, (fx0 + 16, fy1 - 6, (rows[0] + rows[1]) / 2), "Y", 6), _pcyl(4, 10, (fx1 - 8, fy1 - 5, fz0 + 8), "Y", 6)]
    fx("pc_fuse_bus", _comp(bus), K["tin"], grp="electrical")

    # Cerbo GX MK2 (154 x 78 x 48): RJ45 / VE.Direct / USB along the top edge, green terminal blocks underneath
    cl, ct, ch_ = P.CERBO
    cx0, cz0 = x0 + 14, 150
    fx("cerbo_gx", _chamfer(box(cx0, cx0 + cl, yi - T, yi - T - ct, cz0, cz0 + ch_), "<Y", 3), K["cerbo"], grp="electrical", kg=0.4)
    anc("cerbo", (x0 + 14 + cl / 2, yi - T - ct, 150 + ch_))
    ports = [box(cx0 + 8 + i * 17, cx0 + 23 + i * 17, yi - T - 10, yi - T - 38, cz0 + ch_, cz0 + ch_ + 2.5) for i in range(5)]
    ports += [box(cx0 + 96 + i * 11, cx0 + 104 + i * 11, yi - T - 18, yi - T - 30, cz0 + ch_, cz0 + ch_ + 2.5) for i in range(3)]
    ports += [box(cx0 + 131, cx0 + 145, yi - T - 18, yi - T - 25, cz0 + ch_, cz0 + ch_ + 2.5)]
    fx("pc_cerbo_ports", _comp(ports), "alu", grp="electrical")
    fx("pc_cerbo_terminals", box(cx0 + 6, cx0 + cl - 6, yi - T - 12, yi - T - 32, cz0 - 4, cz0), K["green"], grp="electrical")
    lab = [_txt_y("victron energy", 5, cx0 + cl / 2, cz0 + 52, yi - T - ct, 0.3),
           _txt_y("Cerbo GX", 8, cx0 + cl / 2, cz0 + 30, yi - T - ct, 0.3)]
    if any(w is not None for w in lab):
        fx("pc_cerbo_label", _comp(lab), K["text"], grp="electrical")

    # slotted wiring duct along the inner wall above the Cerbo and fuse block; cable glands
    duct = box(x0 + 20, ex0 - 8, yi - T, yi - T - 40, 238, 272).cut(
        _comp(box(x - 3, x + 3, yi - T - 4, yi - T - 36, 237, 242) for x in range(x0 + 32, int(ex0) - 12, 12)))
    fx("pc_wire_duct", duct, K["duct"], kg=0.15)
    zf = P.UPPER_Z0 + T9
    fx("pc_gland_top", _comp([_pcyl(10, zf - (zt - T), (gl[0], gl[1], (zt - T + zf) / 2), n=12),
                              _pcyl(11, 6, (gl[0], gl[1], zf + 3), n=6), _pcyl(11, 6, (gl[0], gl[1], zt - T - 3), n=6)]), K["black"])
    # (v0.12: no low gland to the slide - the power slide is now fed from the bay through the front of the cassette)
    fx("pc_plug_zone", box(XF + 1, P.TUB_L - 4, yo + 2, yi, T, zt - T), "ghost", grp="future")
    tray = box(20, 1400, yo, yo + 90, P.UPPER_Z1 + 2, P.UPPER_Z1 + 5).union(
        box(20, 1400, yo + 87, yo + 90, P.UPPER_Z1 + 2, P.UPPER_Z1 + 25))
    tray = tray.cut(_comp(box(x, x + 4, yo + 86, yo + 91, P.UPPER_Z1 + 12, P.UPPER_Z1 + 18) for x in range(80, 1400, 120)))
    fx("cable_tray", tray, "alu", fab=True, mat="Plate 3 5052")
    return sp, (BF + 1.5, yi - 5), gl


def passenger(drawer_out=0.0, panel_open=0.0):
    """panel_open: control-panel door angle in degrees about its inboard piano hinge (0 = shut, as assembly.py uses).
    90 = fully open: fit a stay there - past ~90 deg the door's free edge crosses the extended power-slide deck edge."""
    sp, hinge, gl = _memo("pc", _passenger_specs)
    parts = _realise(sp, 0.0, panel_open, hinge)
    # ---- upper long drawer with a cable channel behind it (gland drop); the cable tray is above it
    yo, yi = -P.POCKET_Y_OUT, -P.POCKET_Y_IN
    ud = _upper_drawer(yo, yi, drawer_out, gap=P.CABLE_GAP, gland=gl)
    tray = [p for p in parts if p.name == "cable_tray"]
    return [p for p in parts if p.name != "cable_tray"] + ud + tray


# ======================================================================================== driver utility drawer
def _driver_specs():
    sp = []
    g = "utility"
    yi, yo = P.POCKET_Y_IN, P.POCKET_Y_OUT
    x0 = P.POCKET_X0
    zt = P.LOWER_TOP_Z
    xr = P.POCKET_X1

    def add(mode, name, w, col, **kw):
        sp.append((mode, name, g, S(w) if isinstance(w, cq.Workplane) else w, col, kw))

    add(FIX, "ut_inner_wall", box(x0, xr, yi, yi + T, 0, zt).cut(box(x0 - 1, xr + 1, yi + 6, yi + T + 1, zt - T, zt + 1)),
        "ply", fab=True, mat="Ply 12 marine")
    add(FIX, "ut_front", box(x0, x0 + T, yi + T, yo, 0, zt - T), "ply", fab=True, mat="Ply 12 marine")
    add(FIX, "ut_top", box(x0, xr, yi + 6, yo, zt - T, zt), "ply", fab=True, mat="Ply 12 marine")
    add(FIX, "ut_ply_lines", _comp(_ply_lines(xr, [((0, zt - T), (yi, yi + T))], "Z") +
                                   _ply_lines(xr, [((yi + 6, yo), (zt - T, zt))], "Y")), K["ply_line"])
    add(FIX, "ut_screws", _comp(_pcyl(4, 1.2, (x0 + T / 2, yi - 0.6, z), "Y") for z in (40, 140, 240)), "alu_dark")
    # outboard runner mounting plate against the tub wall (the pocket has no outboard ply wall) + cleats
    add(FIX, "ut_runner_plate", box(x0, xr, yo, yo + 3, 95, zt - T), "alu", fab=True, mat="Plate 3 5052")
    add(FIX, "ut_runner_cleats", _comp([box(x0 + T, x0 + T + 20, yo - 1.6, yo, 95, 260), box(x0 + T, x0 + T + 1.6, yo - 20, yo, 95, 260),
                                        box(x0 + T, xr, yo - 14, yo, zt - T - 1.6, zt - T),
                                        box(x0 + T, xr, yo - 1.6, yo, zt - T - 14, zt - T)]), "alu", kg=0.2)
    # drawer (built closed, MOVE specs follow drawer_out)
    dw0, dw1 = yi + T + RUN, yo - RUN
    dl = xr - x0 - T - 20
    dx1 = xr
    dx0 = dx1 - dl
    yc = (dw0 + dw1) / 2
    zl = zt - 57.5
    recess = _cb(dx1 - T9 - 1, dx1 + 4, yc, zl, PADDLE[2], PADDLE[3])
    bspecs, (ya_, yb_, zbot) = _ply_box("ut_drawer_box", g, dx0, dx1, dw0, dw1, 8, zt - T - 6, front_cut=recess)
    sp += bspecs
    add(MOVE, "ut_drawer_front", box(dx1, dx1 + 3, dw0 - 8, dw1 + 8, 6, zt - T - 3).cut(recess), "alu_dark", fab=True,
        mat="Plate 3 5052")
    ykeep = yi + T + 5
    stainless, pan = _paddle_latch(dx1 + 3, yc, zl, ykeep)
    add(MOVE, "ut_drawer_pull", stainless, "alu", kg=0.25)
    add(MOVE, "ut_drawer_pull_pan", pan, K["black"])
    kx = xr - 32
    add(FIX, "ut_drawer_keeper", box(kx - 12, kx + 12, yi + T, yi + T + 10, zl - 14, zl + 14).cut(cyl(4, 30, (kx, ykeep, zl), "Y")),
        "alu", kg=0.04)
    xd = dx0 + 304.5
    add(MOVE, "ut_drawer_divider", box(xd - 4.5, xd + 4.5, ya_ + DIV_CH[2], yb_ - DIV_CH[2], zbot, zt - 60).cut(
        box(xd - 6, xd + 6, yc - 22, yc + 22, zt - 92, zt - 76)), "ply", fab=True, mat="Ply 9 marine")
    add(MOVE, "ut_drawer_divider_slots", _comp(_u_channel(xd, ya_, 1, zbot, zt - T - 8) + _u_channel(xd, yb_, -1, zbot, zt - T - 8)),
        "alu", kg=0.06)
    # folding D-ring tie-downs on the box sides + an elastic strap between the rear pair
    tds = []
    for xx in (dx0 + 360, dx1 - 60):
        for yw, d in ((ya_, 1), (yb_, -1)):
            tds.append(box(xx - 15, xx + 15, *sorted((yw, yw + d * 2.5)), zbot + 12, zbot + 34))
            tds.append(box(xx - 12, xx + 12, *sorted((yw + d * 2.5, yw + d * 6)), zbot + 4, zbot + 22).cut(
                box(xx - 9, xx + 9, *sorted((yw + d * 1, yw + d * 7)), zbot + 7, zbot + 19)))
    add(MOVE, "ut_drawer_tiedowns", _comp(tds), "alu", kg=0.12)
    sp.append((MOVE, "ut_drawer_strap", "payload", S(box(dx1 - 66, dx1 - 54, ya_ + 6, yb_ - 6, zbot + 12, zbot + 14)), "strap", {}))
    for k, (yy, sd) in enumerate(((yi + T, 1), (yo, -1))):
        members, lever = _runner(xr - 6, LOWER_RUNNER_L, yy, sd, 120)
        add(FIX, f"ut_drawer_runner_{k}", members, "runner", kg=1.0)
        add(MOVE, f"ut_drawer_runner_lever_{k}", lever, K["black"])
    return sp


def driver(drawer_out=0.0, upper_out=0.0):
    """Always-in-the-car utility storage: lower pull-out drawer + upper long drawer."""
    yi, yo = P.POCKET_Y_IN, P.POCKET_Y_OUT
    parts = _realise(_memo("ut", _driver_specs), drawer_out)
    parts += _upper_drawer(yo, yi, upper_out)
    for k in range(3):   # example contents: strap rolls in the upper drawer
        x = P.POCKET_X1 - 120 - k * 90 + upper_out
        parts.append(part(f"ud_strap_roll_{k}", "payload", cyl(38, 50, (x, (yi + yo) / 2, P.UPPER_Z0 + 50)), "strap", kg=0.6))
    return parts


# intentional contacts declared for clash.py (kept tight: only parts that genuinely touch/interlock across prefixes)
CLASH_ALLOW = []
