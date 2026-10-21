"""
Slide-out platforms (v0.5 layout, v0.8 detail): side-mount locking runners with a COVERED deck.

Each slide = fixed cassette (base plates, cross ties, vertical runner plates) + moving carriage
(RHS side members on the runners, cross members, aluminium L-angles whose top leg reaches out over the
runners). A 15 mm ply deck sits on top and covers the full slide width, so the two decks meet in the
middle with a 6 mm gap: one continuous surface except the power slide's fridge well. v0.12: the cable chain lies
on its side under the power deck (on a glide tray below the raised fridge-well pan), so both decks are full width.

v0.8 adds geometric detail only (no layout change): the real 3-member DZ9308 cross-section with ball
races and the front lock lever, countersunk floor bolts, deck screw lines, the L-track profile with its
round pockets, flanged receiver bushes, the power-pod outlets (Iconic GPO, SB50 flush housing, 12 V socket;
the pod's dual USB-C was removed in v0.11), an igus-style link chain with end brackets, and the leg clevis / pins / foot / clip.
"""
import math

import cadquery as cq

import params as P

from .core import Part, anchor, box, part, tube_box

# ====================================================================== detail data
# Accuride DZ9308-E4 catalogue (09/21, pp.127-128, distributor copy https://www.albeco.com.pl/data/catalogueb/9308_PL.pdf
# brochure + Accuride EU catalogue 9308-E4 drawing):
#   section 76.2 x 19.1 [PUB]; 3 members (outer / intermediate / inner); M6 6.6 mm holes on the 38.1 centre line [PUB];
#   screw heads inside the slide max 12.7 dia x 4.8 high [PUB]; front lever lock release [PUB], the lever projects 26.9 mm
#   beyond the inner member [PUB]; weight 5.49 kg (44") / 6.00 kg (48") per slide -> ~5.75 kg at 46" [PUB, interpolated].
#   The member profiles below are [EST] from the catalogue section view (balls between outer/intermediate at the top and
#   bottom edges, between intermediate/inner just inside them).
DZ_KG = 5.75
DZ_C = 38.1                                   # [PUB] hole centre line above the slide bottom edge
# (u0, u1, v0, v1): u = from the mounting (cabinet) face across the 19.1 thickness, v = up the 76.2 height   [EST]
DZ_OUTER = ((0, 1.5, 0, 76.2), (0, 14, 0, 1.5), (12.5, 14, 0, 7.2), (0, 14, 74.7, 76.2), (12.5, 14, 69, 76.2))
DZ_INTER = ((9.5, 11, 12, 64.2), (3, 17, 12, 13.5), (3, 17, 62.7, 64.2), (3, 4.5, 64.2, 67.5), (3, 4.5, 8.7, 12))
DZ_INNER = ((17.6, 19.1, 19.5, 56.7), (13, 19.1, 19.5, 21), (13, 19.1, 55.2, 56.7))
DZ_BALL_O = (8.5, 69.45, 3.4)                 # outer <-> intermediate race (u, v, r), mirrored about mid height
DZ_BALL_I = (14.5, 59.45, 2.7)                # intermediate <-> inner race
# outer-member holes, mm back from its front end (K, M, N, P, Q, R + front holes; 44"/48" interpolated)  [PUB-interp]
DZ_HOLES_OUTER = (19.1, 41.4, 76.2, 235.0, 546.1, 908.1, 1066.8, 1124.0, 1143.0)
DZ_SCREWS_OUTER = (41.4, 235.0, 546.1, 908.1, 1124.0)        # [DES] M6 pan heads used (11.5 x 4.0 < 12.7 x 4.8 limit)
DZ_ACCESS_INTER = (127.0, 190.5, 368.3, 520.7, 957.3, 1017.5)  # [PUB-interp] A-F: screwdriver access through the intermediate
DZ_LEVER_PROTRUDE = 26.9                      # [PUB] -> does NOT fit: only 2.6 mm between the inner member and the rear plate

# igus E2.26 class chain: 1 m = 22 links -> 46 mm pitch [PUB, igus/TME E2.26.038.055.0 listing]; side-plate/crossbar sizes [EST]
CHAIN_PITCH = 46
CHAIN_PLATE_T = 3.5
# power-pod outlets
GPO_PLATE = (120, 78)          # [PUB] Clipsal Iconic 3025 horizontal double switched socket, W x H (clipsal.com) -> 78 > 68 pod depth
SB50_BEZEL = (62, 56)          # [EST] SB50 flush housing with spring lid (Altronics P7862 / Trailer Vision class), X x Y
SB50_OPEN = (24, 40)           # [PUB] 40 x 25 cut-out of the Trailer Vision slimline SB50 housing (X x Y here)
SOCKET_12V_FLANGE_R = 20       # [EST] Narva heavy-duty flush accessory socket: 29 mm hole [PUB], ~40 mm flange

# colours (RGBA) for purchased / decorative bits
BLACK = (30, 30, 32, 255)
RUBBER = (18, 18, 18, 255)
RED = (200, 35, 35, 255)
SB50_GREY = (128, 130, 132, 255)


# ====================================================================== small geometry helpers
def _v(*a):
    return cq.Vector(*a)


def _bx(x0, x1, y0, y1, z0, z1):
    return box(x0, x1, y0, y1, z0, z1).val()


# The GLB costs ~32 bytes per triangle and a true cylinder always tessellates to 18 facets (angular tolerance 0.35 rad), so
# small round features are n-sided prisms (n = 8..16): they read as round at render scale for a fraction of the triangles.
def _poly(n, r):
    return [(r * math.cos(2 * math.pi * (k + 0.5) / n), r * math.sin(2 * math.pi * (k + 0.5) / n)) for k in range(n)]


_PRISM = {}


def _prism(axis, r, length, n):
    """n-sided prism of circumradius r along +axis from the origin (cached prototype; callers translate a copy)."""
    key = (axis, round(r, 4), round(length, 4), n)
    if key not in _PRISM:
        plane = {"X": "YZ", "Y": "XZ", "Z": "XY"}[axis]
        w = cq.Workplane(plane).polyline(_poly(n, r)).close().extrude(length if axis != "Y" else -length)
        _PRISM[key] = w.val()
    return _PRISM[key]


def _cylx(r, xa, xb, y, z, n=10):
    xa, xb = sorted((xa, xb))
    return _prism("X", r, xb - xa, n).translate(_v(xa, y, z))


def _cyly(r, ya, yb, x, z, n=10):
    ya, yb = sorted((ya, yb))
    return _prism("Y", r, yb - ya, n).translate(_v(x, ya, z))


def _cylz(r, za, zb, x, y, n=10):
    za, zb = sorted((za, zb))
    return _prism("Z", r, zb - za, n).translate(_v(x, y, za))


def _ringz(ro, ri, za, zb, x, y, n=16, ni=10):
    return _cylz(ro, za, zb, x, y, n).cut(_cylz(ri, za - 1, zb + 1, x, y, ni))


def _hexx(af, xa, xb, y, z):
    xa, xb = sorted((xa, xb))
    return cq.Workplane("YZ", origin=(xa, y, z)).polygon(6, af / math.cos(math.pi / 6)).extrude(xb - xa).val()


def _ball(r, c):
    """Ball hint: 8-sided roller along X (reads as a ball in the slide's end view, 36 triangles instead of ~300)."""
    return _cylx(r, c[0] - r, c[0] + r, c[1], c[2], n=8)


def _cmp(items):
    """Compound of solids without booleans (cheap; used for purchased / decorative parts)."""
    out = []
    for it in items:
        if it is None:
            continue
        if isinstance(it, (list, tuple)):
            out += _cmp(it).Solids()
        elif isinstance(it, cq.Workplane):
            out += [s for v in it.vals() for s in (v.Solids() if hasattr(v, "Solids") else [v])]
        else:
            out += it.Solids() if hasattr(it, "Solids") else [it]
    return cq.Compound.makeCompound(out)


def _cut(shape, tools):
    """Cut a list of tool solids in one boolean. The tools must not overlap each other (fuse overlapping ones first)."""
    tools = [t for t in tools if t is not None]
    if not tools:
        return shape
    s = shape.val() if isinstance(shape, cq.Workplane) else shape
    return s.cut(_cmp(tools))


def _prism_x(rects, x0, x1):
    """Fuse (y0, y1, z0, z1) rectangles into one section (2D sketch) and extrude it along X from x0 to x1."""
    sk = cq.Sketch()
    for y0, y1, z0, z1 in rects:
        y0, y1 = sorted((y0, y1))
        z0, z1 = sorted((z0, z1))
        sk = sk.push([((y0 + y1) / 2, (z0 + z1) / 2)]).rect(y1 - y0, z1 - z0).reset()
    return cq.Workplane("YZ", origin=(x0, 0, 0)).placeSketch(sk.clean()).extrude(x1 - x0).val()


def _try_fillet(w, sel, r):
    try:
        out = w.edges(sel).fillet(r)
        return out if out.val().isValid() else w
    except Exception:
        return w


_CSK_CACHE = {}


def _csk(x, y, ztop, r_head=6.0, r_hole=3.3, depth=2.7):
    """Countersink + clearance hole (cutting tool) and the matching recessed CSK head with a hex socket (prototype copies)."""
    key = (r_head, r_hole, depth)
    if key not in _CSK_CACHE:
        tool = [_cylz(r_head + 0.2, -0.8, 0.5, 0, 0, n=12)]                 # counter-sunk seat (shown as a shallow recess)
        head = _cylz(r_head, -0.8, -0.3, 0, 0, n=12).cut(_cylz(r_head * 0.25, -0.6, 0, 0, 0, n=6))   # head + hex socket
        _CSK_CACHE[key] = (tool, head)
    tool, head = _CSK_CACHE[key]
    d = _v(x, y, ztop)
    return [t.translate(d) for t in tool], head.translate(d)


# ====================================================================== layout (unchanged)
def slide_extent(side):
    """Y extents of the cassette / deck for a slide: (y_low, y_high)."""
    gap = P.SLIDE_GAP_MID / 2
    edge = P.ARCH_GAP / 2 - 3
    if side == "p":
        return -edge, -gap
    return gap, edge


def carriage_extent(side):
    """Y extents of the moving frame (between the runners)."""
    ya, yb = slide_extent(side)
    m = P.SIDE_PLATE_T + P.RUNNER_T + 1
    return ya + m, yb - m


def grid_positions(cx0, cx1, ya, yb, power):
    """Ball-lock receiver positions.
    Y: edge rows over the moving side members (37.6 mm in from each edge, the pin tip sits inside the RHS) +
       interior rows at 100 mm pitch centred on the L-track (same on both slides, so modules swap sides).
    X: front/rear edge rows over the end cross members + 100 mm pitch between them."""
    yc = (ya + yb) / 2
    e = P.SIDE_PLATE_T + P.RUNNER_T + 1 + 12.5
    ys = [ya + e, yb - e]
    k = 0
    while True:
        d = 50 + 100 * k
        if d > (yb - ya) / 2 - e - 60:
            break
        ys += [yc - d, yc + d]
        k += 1
    x_first = cx0 + (P.BULKHEAD_D + 65 if power else P.RECEIVER_EDGE_X)
    x_last = cx1 - P.RECEIVER_EDGE_X
    xs = []
    x = x_first
    while x < x_last - 60:
        xs.append(x)
        x += P.RECEIVER_PITCH
    xs.append(x_last)
    return [(x, y) for x in xs for y in sorted(ys)]


# ====================================================================== components
def _receiver_parts(name, g, pts, top):
    """Flanged stainless bushes: 22 mm flange (flush, 0.1 proud) and 8.4 mm bore (dark); the barrel is hidden in the ply."""
    if not pts:
        return []
    bush = _ringz(P.RECEIVER_D / 2, 4.3, top - 1.4, top + 0.1, 0, 0, n=16, ni=10)     # flange; the 12 mm barrel is hidden in the ply
    bore = _cylz(4.2, top - P.DECK_T + 0.5, top - 0.6, 0, 0, n=10)
    recs = [bush.translate(_v(x, y, 0)) for x, y in pts]          # copies of one prototype: no per-receiver booleans
    bores = [bore.translate(_v(x, y, 0)) for x, y in pts]
    return [part(f"{name}_receivers", g, _cmp(recs), "receiver", kg=0.03 * len(pts), n_receivers=len(pts)),
            part(f"{name}_receiver_bores", g, _cmp(bores), "hole")]


def _ltrack(x0, x1, yc, ztop, w=P.LTRACK_W, h=P.LTRACK_H, pockets=None):
    """Heavy-duty airline (L-) track [EST profile]: base web, two side walls, top lips with an 11 mm slot and 16 mm round
    pockets at 25.4 mm pitch [PUB 1" pitch]. Returns (track, dark core visible through the pockets)."""
    s = w / 35
    hw = w / 2
    wall, slot = 4.5 * s, 5.5 * s
    rects = [(yc - hw, yc + hw, ztop - h, ztop - h + 2 * s),
             (yc - hw, yc - hw + wall, ztop - h, ztop), (yc + hw - wall, yc + hw, ztop - h, ztop),
             (yc - hw + wall - 0.01, yc - slot, ztop - 3.5 * s, ztop), (yc + slot, yc + hw - wall + 0.01, ztop - 3.5 * s, ztop)]
    tr = _prism_x(rects, x0, x1)
    if pockets is None:
        pockets = [x0 + 15 + 25.4 * i for i in range(int((x1 - x0 - 30) / 25.4) + 1)]
    tr = _cut(tr, [_cylz(8 * s, ztop - 3.5 * s - 0.5, ztop + 1, px, yc, n=12) for px in pockets])
    core = _bx(x0 + 1, x1 - 1, yc - hw + wall + 0.2, yc + hw - wall - 0.2, ztop - h + 2 * s + 0.2, ztop - 3.5 * s - 0.6)
    return tr, core


def _runners(nm, g, x0, ext, ya, yb, rz0, cx1):
    """Accuride DZ9308 46" pair: outer member fixed to the runner plate, intermediate at half travel, inner on the carriage."""
    parts = []
    L = P.RUNNER_LEN
    kg = DZ_KG / 3
    for lab, y_face, dirn in (("a", ya + P.SIDE_PLATE_T, 1), ("b", yb - P.SIDE_PLATE_T, -1)):
        def Y(u):
            return y_face + dirn * u

        def rects(prof):
            return [(Y(u0), Y(u1), rz0 + v0, rz0 + v1) for u0, u1, v0, v1 in prof]
        xa = [x0 + 3 + ext * f for f in (0, 0.5, 1)]
        xe = [a + L for a in xa]
        # outer: C channel, M6 holes on the centre line, pan-head screws inside, top + bottom ball rows at its front end
        outer = _prism_x(rects(DZ_OUTER), xa[0], xe[0])
        outer = _cut(outer, [_cyly(3.3, Y(-1), Y(3), xe[0] - d, rz0 + DZ_C) for d in DZ_HOLES_OUTER])
        heads = [_cyly(5.75, Y(1.5), Y(5.5), xe[0] - d, rz0 + DZ_C) for d in DZ_SCREWS_OUTER]
        uo, vo, ro = DZ_BALL_O
        balls_o = [_ball(ro, (xe[0] - 14 - 9 * j, Y(uo), rz0 + v)) for j in range(3) for v in (vo, P.RUNNER_H - vo)]
        parts.append(part(f"{nm}_runner_{lab}_0", g, _cmp([outer] + heads + balls_o), "runner", kg=kg))
        # intermediate: I-section with ball-race returns, access holes, inner ball rows at its front end
        inter = _prism_x(rects(DZ_INTER), xa[1], xe[1])
        inter = _cut(inter, [_cyly(3.55, Y(9), Y(11.5), xe[1] - d, rz0 + DZ_C) for d in DZ_ACCESS_INTER])
        ui, vi, ri = DZ_BALL_I
        balls_i = [_ball(ri, (xe[1] - 12 - 7 * j, Y(ui), rz0 + v)) for j in range(3) for v in (vi, P.RUNNER_H - vi)]
        parts.append(part(f"{nm}_runner_{lab}_1", g, _cmp([inter] + balls_i), "runner", kg=kg))
        # inner: shallow channel screwed to the carriage side member
        inner = _prism_x(rects(DZ_INNER), xa[2], xe[2])
        parts.append(part(f"{nm}_runner_{lab}_2", g, inner, "runner", kg=kg))
        # front lock lever (lock-in + lock-out release) in the inner member's channel; the real lever projects 26.9 mm past
        # the member end - here it stops at the rear plate (see DZ_LEVER_PROTRUDE) and is worked by the rear release cable
        lever = _prism_x([(Y(13.4), Y(17.3), rz0 + 30, rz0 + 46.2)], xe[2] - 55, xe[2] - 4)
        paddle = _prism_x([(Y(14.6), Y(17.3), rz0 + 33, rz0 + 43.5)], xe[2] - 4, min(xe[2] + DZ_LEVER_PROTRUDE, cx1 - 0.8))
        rivet = _cyly(2.6, Y(12.6), Y(13.4), xe[2] - 45, rz0 + 38.1)
        parts.append(part(f"{nm}_runner_{lab}_lever", g, _cmp([lever, paddle, rivet]), BLACK))
    return parts


def _cassette_bolts(x0, x1, ya, yb, bt):
    """CSK M6 floor bolts through the base plates and cross ties, M5 CSK screws in the UHMW stops."""
    tools = {"a": [], "b": [], "x": [], "s": []}
    heads = []
    bx = [x0 + 40, x0 + 330, x0 + 620, x0 + 910, x1 - 160]      # clear of the UHMW stops (x1-120..x1-20)
    for key, yy in (("a", ya + 42), ("b", yb - 42)):            # inboard of the runners, under the carriage side member
        for x in bx:
            t, hd = _csk(x, yy, bt)
            tools[key] += t
            heads.append(hd)
    yc = (ya + yb) / 2
    for xx in (x0 + 10, (x0 + x1) / 2 - 25, x1 - 60):
        for yy in (ya + 95, yc, yb - 95):
            t, hd = _csk(xx + 25, yy, bt)
            tools["x"].append((xx, t))
            heads.append(hd)
    for yy in (ya + 30, yb - 70):
        for xs in (x1 - 95, x1 - 45):
            t, hd = _csk(xs, yy + 20, bt + 5, r_head=4.8, r_hole=2.7, depth=2.1)
            tools["s"].append((yy, t))
            heads.append(hd)
    return tools, heads


def slide(side: str, ext: float, power: bool):
    parts = []
    g = f"slide_{side}"
    nm = "slide_power" if power else "slide_driver"
    ya, yb = slide_extent(side)
    x0, x1 = P.SLIDE_X0, P.SLIDE_X0 + P.SLIDE_L
    bt = P.BASE_T
    rz0, rz1 = bt, bt + P.RUNNER_H
    camp = ext > 0
    # ------------------------------------------------ fixed cassette
    tools, heads = _cassette_bolts(x0, x1, ya, yb, bt)
    for key, yy in (("a", ya), ("b", yb - 60)):
        parts.append(part(f"{nm}_base_plate_{int(yy)}", g, _cut(box(x0, x1, yy, yy + 60, 0, bt), tools[key]),
                          "alu", fab=True, mat="Plate 6 5052"))
    for i, xx in enumerate((x0 + 10, (x0 + x1) / 2 - 25, x1 - 60)):
        tl = [s for x_, t in tools["x"] if x_ == xx for s in t]
        parts.append(part(f"{nm}_base_cross_{i}", g, _cut(box(xx, xx + 50, ya + 60, yb - 60, 0, bt), tl), "alu", fab=True,
                          mat="Flat 50x6 6060"))
    for lab, yy in (("a", ya), ("b", yb - P.SIDE_PLATE_T)):    # vertical runner plates welded to the base plates
        parts.append(part(f"{nm}_runner_plate_{lab}", g, box(x0, x1, yy, yy + P.SIDE_PLATE_T, bt, rz1), "alu", fab=True, mat="Plate 6 5052"))
    for yy in (ya + 30, yb - 70):   # UHMW stops: stowed carriage rests on these, road shock bypasses the runners
        tl = [s for y_, t in tools["s"] if y_ == yy for s in t]
        stop = _cut(box(x1 - 120, x1 - 20, yy, yy + 40, bt, bt + 5), tl)
        parts.append(part(f"{nm}_uhmw_stop_{int(yy)}", g, stop, "uhmw", fab=True, mat="UHMW 10"))
    parts.append(part(f"{nm}_base_bolts", g, _cmp(heads), "receiver", note="CSK M6 floor bolts + M5 stop screws (in the part kg)"))
    # ------------------------------------------------ runners (3-member, 100 % extension, lock in + out)
    cx0, cx1 = x0 + ext, x1 + ext
    parts += _runners(nm, g, x0, ext, ya, yb, rz0, cx1)
    # ------------------------------------------------ carriage
    cy0, cy1 = carriage_extent(side)
    zlip = P.DECK_BOT_Z - P.LIP_T
    zb, top = P.DECK_BOT_Z, P.DECK_TOP_Z
    yc = (ya + yb) / 2
    caps = []
    for i, (yy, edge, dirn) in enumerate(((cy0, ya, -1), (cy1 - 25, yb, 1))):
        parts.append(part(f"{nm}_carr_side_{i}", g, tube_box(cx0, cx1, yy, yy + 25, rz0 + 6, zlip, axis="X"), "alu", fab=True,
                          mat="RHS 75x25x2 6060"))
        caps.append(_bx(cx0 - 2, cx0, yy, yy + 25, rz0 + 6, zlip))          # plastic end plug on the open front end
        # L-angle: vertical leg on the inner face of the side member, top leg reaching out over the runner to the deck edge
        yin = yy + 25 if i == 0 else yy
        leg_v = box(cx0, cx1, yin, yin - dirn * 3, zb - 40, zb)
        leg_h = box(cx0, cx1, yin - dirn * 3, edge, zlip, zb)
        parts.append(part(f"{nm}_deck_angle_{i}", g, leg_v.union(leg_h), "alu", fab=True, mat="Angle 60x40x3 6060"))
    parts.append(part(f"{nm}_carr_end_caps", g, _cmp(caps), BLACK))
    well = None
    if power:
        wx0 = cx0 + P.BULKHEAD_D
        wx1 = wx0 + P.FRIDGE_WELL_L
        well = ((wx0, wx1), (cy0 + 28, cy1 - 28))
    n_cross = 5
    cross_x = []
    for i in range(n_cross):
        xx = cx0 + 10 + i * (P.SLIDE_L - 70) / (n_cross - 1)
        if well and well[0][0] - 50 < xx < well[0][1]:
            continue
        cross_x.append(xx)
        parts.append(part(f"{nm}_carr_cross_{i}", g, tube_box(xx, xx + 50, cy0 + 28, cy1 - 28, zb - 25, zb, axis="Y"),
                          "alu", fab=True, mat="RHS 50x25x2 6060"))
    # ------------------------------------------------ deck: covered, full width, minus the fridge well and the L-track channel
    def in_well(x, y, m=0):
        return well and well[0][0] - m < x < well[0][1] + m and well[1][0] - m < y < well[1][1] + m
    tx0 = well[0][1] if well else cx0
    pts = grid_positions(cx0, cx1, ya, yb, power)
    # screw lines: along both deck-carrier angles (over the runners) and across every cross member, avoiding receivers
    scr = [(x, yy) for yy in (ya + 10, yb - 10) for x in [cx0 + 40 + 150 * k for k in range(int((P.SLIDE_L - 80) / 150) + 1)]]
    for xx in cross_x:
        scr += [(xx + 25, yc + d) for d in (-200, -100, 100, 200) if ya + 60 < yc + d < yb - 60]
    scr = [(x, y) for x, y in scr if not in_well(x, y, 8) and all((x - px) ** 2 + (y - py) ** 2 > 20 ** 2 for px, py in pts)
           and not abs(y - yc) < P.LTRACK_W / 2 + 6]
    deck = box(cx0, cx1 - 3, ya, yb, zb, top)
    if well:
        (wx0, wx1), (wy0, wy1) = well
        deck = deck.cut(box(wx0, wx1, wy0, wy1, zb - 1, top + 1))
    deck = deck.cut(box(tx0 - 1, cx1 + 1, yc - P.LTRACK_W / 2, yc + P.LTRACK_W / 2, top - P.LTRACK_H, top + 1))
    parts.append(part(f"{nm}_deck", g, deck, "ply", fab=True, mat="Ply 15 marine"))
    screws = [_cylz(4.0, top, top + 0.2, x, y, n=8) for x, y in scr]
    # aluminium edge cap: 2 mm face over the ply edge + angle lip, rounded top edge, CSK screws into the ply edge
    cap_a = _try_fillet(box(cx0, cx1, ya - 2, ya, zlip, top), "|X and >Z and <Y", 1.5)
    cap_b = _try_fillet(box(cx0, cx1, yb, yb + 2, zlip, top), "|X and >Z and >Y", 1.5)
    parts.append(part(f"{nm}_edge_cap", g, cap_a.union(cap_b), "alu", fab=True, mat="Angle 30x30x3 6060"))
    zm = (zlip + top) / 2
    for x in [cx0 + 60 + 200 * k for k in range(int((P.SLIDE_L - 100) / 200) + 1)]:
        screws.append(_cyly(3.4, ya - 2.3, ya - 2, x, zm, n=8))
        screws.append(_cyly(3.4, yb + 2, yb + 2.3, x, zm, n=8))
    parts.append(part(f"{nm}_deck_screws", g, _cmp(screws), "receiver"))
    # L-track in the deck channel (behind the fridge well on the power slide)
    pockets = [tx0 + 30 + i * 25.4 for i in range(int((cx1 - tx0 - 60) / 25.4))]
    track, core = _ltrack(tx0 + 15, cx1 - 15, yc, top, pockets=pockets)
    parts.append(part(f"{nm}_ltrack", g, track, "ltrack", fab=True, mat="L-track HD"))
    parts.append(part(f"{nm}_ltrack_pockets", g, core, "hole"))
    if well:
        (wx0, wx1), (wy0, wy1) = well
        in_w = [(x, y) for x, y in pts if wx0 < x < wx1 and wy0 < y < wy1]
        pts = [q for q in pts if q not in in_w]
    parts += _receiver_parts(nm, g, pts, top)
    if power:
        (wx0, wx1), (wy0, wy1) = well
        zf = P.FRIDGE_WELL_Z
        pan = (box(wx0, wx1, wy0, wy1, zf - 3, zf)
               .union(box(wx0, wx0 + 3, wy0, wy1, zf - 3, zb))
               .union(box(wx1 - 3, wx1, wy0, wy1, zf - 3, zb))
               .union(box(wx0, wx1, wy0, wy0 + 3, zf - 3, zb))
               .union(box(wx0, wx1, wy1 - 3, wy1, zf - 3, zb)))
        pan = _cut(pan, [_cylz(5, zf - 4, zf + 1, x, y) for x in (wx0 + 14, wx1 - 14) for y in (wy0 + 12, wy1 - 12)])   # drains
        parts.append(part(f"{nm}_fridge_well_pan", g, pan, "alu", fab=True, mat="Plate 3 5052"))
        # v0.12: no floor L-tracks (they'd cost 10 mm of fridge height); 4 flush strap anchors riveted to the pan floor
        # v0.13: one in each well corner (28 x 37 mm pocket beyond the centred fridge's ends), for the handle straps
        anchors_ = [box(x - 11, x + 11, y - 14, y + 14, zf, zf + 3) for x in (wx0 + 14, wx1 - 14) for y in (wy0 + 18, wy1 - 18)]
        anchors_ += [_cylz(4, zf + 3, zf + 7, x, y) for x in (wx0 + 14, wx1 - 14) for y in (wy0 + 18, wy1 - 18)]   # folded ring
        parts.append(part(f"{nm}_well_strap_anchors", g, _cmp(anchors_), "alu_dark", kg=0.2,
                          note="flush folding tie-down rings (4), one per well corner, for the fridge handle straps"))
        # removable well filler: 15 mm ply panel on two 18 mm ply risers standing on the pan (walls locate it),
        # flush with the deck and carrying the same receiver grid + L-track (fridge out = full flat slide)
        fg = "well_filler"
        fz0 = zf                                         # risers stand on the pan floor, located by the well walls
        xs_w = sorted({x for x, _ in in_w})
        finger = [((xs_w[0] + xs_w[1]) / 2 if len(xs_w) > 1 else wx0 + 60, yc + s * 100) for s in (-1, 1)] + \
                 [((xs_w[-1] + xs_w[-2]) / 2 if len(xs_w) > 1 else wx1 - 60, yc + s * 100) for s in (-1, 1)]
        panel = box(wx0 + 4, wx1 - 4, wy0 + 4, wy1 - 4, zb, top).cut(
            box(wx0, wx1, yc - P.LTRACK_W / 2, yc + P.LTRACK_W / 2, top - P.LTRACK_H, top + 1))
        panel = _cut(panel, [_cylz(14, zb - 1, top + 1, x, y) for x, y in finger])      # 28 mm finger holes to lift it out
        parts.append(part(f"{nm}_filler_panel", fg, panel, "ply", fab=True, mat="Ply 15 marine"))
        for k, yy in enumerate((wy0 + 26, wy1 - 44)):
            parts.append(part(f"{nm}_filler_riser_{k}", fg, box(wx0 + 30, wx1 - 30, yy, yy + 18, fz0, zb), "ply_edge", fab=True, mat="Ply 18 marine"))
        ftrack, fcore = _ltrack(wx0 + 15, wx1 - 15, yc, top)
        parts.append(part(f"{nm}_filler_ltrack", fg, ftrack, "ltrack", fab=True, mat="L-track HD"))
        parts.append(part(f"{nm}_filler_ltrack_pockets", fg, fcore, "hole"))
        parts += _receiver_parts(f"{nm}_filler", fg, in_w, top)
        parts += _power_pod(nm, g, cx0, ya, yb, top, camp)
    # ------------------------------------------------ rear face + recessed pull with the lock-release lever
    hz0, hz1 = rz0 + 24, rz0 + 46                       # recess opening
    rear = box(cx1 - 3, cx1, cy0, cy1, rz0 + 6, zlip).union(box(cx1 - 3, cx1, ya, yb, zlip, top))   # clears the fixed runner plates
    rear = rear.cut(box(cx1 - 4, cx1 + 1, yc - 105, yc + 105, hz0, hz1))
    parts.append(part(f"{nm}_rear_plate", g, rear, "alu", fab=True, mat="Plate 3 5052"))
    frame = box(cx1, cx1 + 1.5, yc - 118, yc + 118, hz0 - 6, hz1 + 6).cut(box(cx1 - 1, cx1 + 2, yc - 105, yc + 105, hz0, hz1))
    frame = _try_fillet(frame, "|X", 2.0)
    cup = box(cx1 - 26, cx1, yc - 106.5, yc + 106.5, hz0 - 1.5, hz1 + 1.5).cut(box(cx1 - 24.5, cx1 + 1, yc - 105, yc + 105, hz0, hz1))
    parts.append(part(f"{nm}_handle", g, frame.union(cup), "alu_dark", kg=0.3, note="recessed pull, stainless dish"))
    trig = _cmp([_bx(cx1 - 15, cx1 - 9, yc - 70, yc + 70, hz1 - 9, hz1 - 4),
                 _bx(cx1 - 22, cx1 - 15, yc - 70, yc - 62, hz1 - 9, hz1 - 4), _bx(cx1 - 22, cx1 - 15, yc + 62, yc + 70, hz1 - 9, hz1 - 4)])
    parts.append(part(f"{nm}_handle_release", g, trig, RED, note="pull to release both runner locks (Bowden cables)"))
    for lab, yl, s in (("a", ya + P.SIDE_PLATE_T + 15.4, -1), ("b", yb - P.SIDE_PLATE_T - 15.4, 1)):
        pts_c = [(cx1 - 18, yc + s * 66, hz1 - 6.5), (cx1 - 30, yc + s * 100, rz0 + 30), (cx1 - 30, (cy0 + 12) if s < 0 else (cy1 - 12), rz0 + 30),
                 (cx1 - 30, yl, rz0 + 38)]
        parts.append(Part(f"{nm}_release_cable_{lab}", g, color=BLACK, tube=pts_c, tube_r=2.2))
    parts += fold_legs(nm, g, cx0, cx1, cy0, cy1, ext)
    if power:
        parts += cable_chain(x0, cx0, cy0, cy1, top)
    return parts


def _power_pod(nm, g, cx0, ya, yb, top, camp):
    """Power pod at the very front of the power slide: sockets face UP so plugs never foul the fridge."""
    parts = []
    pw0, pw1 = ya + 20, yb - 20
    pz = top + 150
    xc = cx0 + 2 + (P.BULKHEAD_D - 2) / 2                 # pod centre in X
    parts.append(part(f"{nm}_power_pod", g, box(cx0 + 2, cx0 + P.BULKHEAD_D, pw0, pw1, top, pz), "alu_dark", fab=True, mat="Plate 3 5052"))
    parts.append(part(f"{nm}_power_pod_screws", g, _cmp([_cylz(3.2, pz, pz + 0.4, x, y) for x in (cx0 + 8, cx0 + P.BULKHEAD_D - 6)
                                                          for y in (pw0 + 5, pw1 - 5)]), "receiver"))
    # --- Clipsal Iconic-style horizontal double switched socket (real skin 120 x 78: overhangs the 68 mm pod)
    gw, gh = GPO_PLATE
    gy = pw0 + 10 + gw / 2
    plate = box(xc - gh / 2, xc + gh / 2, gy - gw / 2, gy + gw / 2, pz - 2, pz + 7)
    plate = _try_fillet(plate, "|Z", 6.0)
    plate = _try_fillet(plate, ">Z", 2.0)
    slots, rock = [], []
    for sy in (gy - 30, gy + 30):
        sx = xc - 9                                       # socket "up" = +X (switch above it)
        for lat in (-1, 1):                               # active / neutral: 30 deg inverted V
            sl = cq.Workplane("XY").box(7.5, 2.2, 14).rotate((0, 0, 0), (0, 0, 1), lat * 30).translate((sx + 3, sy + lat * 7, pz + 4)).val()
            slots.append(sl)
        slots.append(_bx(sx - 13.5, sx - 5, sy - 1.1, sy + 1.1, pz - 3, pz + 10))   # earth
        rock.append(_bx(xc + 17, xc + 33, sy - 6, sy + 6, pz + 7, pz + 8.6))        # rocker switch
    plate = _cut(plate, slots)
    parts.append(part(f"{nm}_gpo", g, plate, "outlet", kg=0.4, product="Clipsal Iconic 3025 (120 x 78)"))
    parts.append(part(f"{nm}_gpo_switches", g, _cmp(rock), (206, 208, 211, 255)))
    # --- Anderson SB50 flush housing with spring lid (lid open in camp), grey 12 V SB50 inside
    ay = pw0 + 175
    bw, bh = SB50_BEZEL
    ox, oy = SB50_OPEN
    bez = box(xc - bw / 2, xc + bw / 2, ay - bh / 2, ay + bh / 2, pz - 2, pz + 6).cut(box(xc - ox / 2, xc + ox / 2, ay - oy / 2, ay + oy / 2, pz - 3, pz + 7))
    bez = _try_fillet(bez, "|Z", 4.0)
    xh = xc - bw / 2 + 2                                   # lid hinge line (-X edge: the open lid stands behind the plug)
    if camp:
        lid = _bx(xh - 3, xh, ay - bh / 2 + 3, ay + bh / 2 - 3, pz + 6, pz + 6 + bw - 6)
    else:
        lid = _bx(xh, xc + bw / 2 - 2, ay - bh / 2 + 3, ay + bh / 2 - 3, pz + 6, pz + 9)
    hinge = _cyly(2.2, ay - bh / 2 + 6, ay + bh / 2 - 6, xh - 1.5, pz + 7.5)
    parts.append(part(f"{nm}_anderson", g, _cmp([bez, lid, hinge]), BLACK, kg=0.1, product="SB50 flush housing (Altronics P7862 class)"))
    sb = box(xc - ox / 2 + 1, xc + ox / 2 - 1, ay - oy / 2 + 1, ay + oy / 2 - 1, pz - 12, pz + 4.5)
    sb = _cut(sb, [_bx(xc - 5, xc + 5, ay + s * 9 - 4, ay + s * 9 + 4, pz - 6, pz + 6) for s in (-1, 1)])
    parts.append(part(f"{nm}_anderson_sb50", g, sb, SB50_GREY))
    # --- 12 V accessory socket (Narva heavy-duty flush class) with tethered cap (open in camp)
    sy = pw0 + 245

    def cap(x, y, r, z0):
        if camp:      # flipped up on its -X hinge
            return _cmp([_cylx(r, x - r - 6, x - r - 1, y, z0 + r + 2, n=16), _bx(x - r - 2, x - r + 3, y - 3, y + 3, z0, z0 + 3)])
        return _cmp([_cylz(r, z0, z0 + 5, x, y, n=16), _bx(x - r - 2, x - r + 3, y - 3, y + 3, z0, z0 + 3)])
    s12 = _cmp([_ringz(SOCKET_12V_FLANGE_R, 10.6, pz - 1, pz + 3, xc, sy, n=20, ni=14),
                _cylz(10.5, pz, pz + 0.6, xc, sy, n=14), _cylz(2.4, pz + 0.6, pz + 2.5, xc, sy, n=8), cap(xc, sy, 16.5, pz + 3)])
    parts.append(part(f"{nm}_12v", g, s12, "usb", kg=0.05, product="Narva HD flush accessory socket, 29 mm hole"))
    # (v0.11: no USB-C on the pod - owner: Anderson, 12 V and 230 V only; USB-C lives on the rear panel and in the cabin box)
    return parts


def _leg_frame(deployed, xl, yp, zc, h, dirn, ztop):
    """Map (s along the leg from its top end) -> (y, z) on the leg axis, for the deployed or folded leg."""
    if deployed:
        return lambda s: (yp, ztop - s)
    y0 = yp - dirn * h
    return lambda s: (y0 + dirn * s, zc)


def _ball_lock_pin(xa, xb, y, z, head_dir=1, r=4.0):
    """8 mm ball-lock pin along X: shank from xa to xb, button handle + push button on the head side, 2 locking balls."""
    xs, xt = (xb, xa) if head_dir > 0 else (xa, xb)
    d = head_dir
    return [_cylx(r, xa, xb, y, z, n=8), _cylx(8, xs, xs + d * 11, y, z, n=12), _cylx(3.4, xs + d * 11, xs + d * 13, y, z, n=8),
            _cylx(r * 0.75, xt - d * 1.5, xt, y, z, n=8)]


def fold_legs(nm, g, cx0, cx1, cy0, cy1, ext):
    """Two fold-out telescopic legs per slide. Each pivots on a clevis on the inner face of one carriage side member
    (in the rear bay, between the last two cross members). Stowed: folded across under the deck, nested, clipped to the
    opposite side member. Deployed (slide out past the open tailgate): swung down 90 deg, locked by a ball-lock pin through
    the clevis, sections extended to the ground and pinned, swivel foot screwed down to take the load.
    v0.8 detail: clevis = 4 mm base plate bolted to the side member + two 5 mm cheeks with an M10 shoulder-bolt pivot and a
    ball-lock pin hole that passes through the leg in BOTH positions (locks it folded or vertical); 8.4 mm holes at 25 mm
    pitch; swivel foot = rubber pad, steel cup, ball, M10 stud and lock nut; spring tool clip on the UHMW block."""
    parts = []
    (s0, w0, l0), (s1, w1, l1), (s2, w2, l2) = P.LEG_SECTIONS
    fd, fh = P.LEG_FOOT
    zc = P.LEG_Z + s0 / 2                       # pivot / folded-leg centreline height
    tg_tip = P.TUB_L + 10 + P.TAILGATE_H        # open tailgate tip: legs must land behind it
    xs = [cx1 - d for d in P.LEG_X_FROM_REAR]
    deployed = ext > 0 and min(xs) - s0 / 2 > tg_tip + 15
    h = s0 / 2
    ztop = zc + h
    zg = -P.FLOOR_ABOVE_GROUND
    for i, (xl, yface, dirn) in enumerate(((xs[0], cy0 + 25, 1), (xs[1], cy1 - 25, -1))):
        yp = yface + dirn * P.LEG_PIVOT_DY
        ylk, zlk = yp + dirn * 11, zc + 11             # lock-pin hole (inside the leg folded AND vertical)
        # ---- clevis: base plate (bolted through the RHS, below the deck-angle leg) + two D-shaped cheeks
        base = _bx(xl - 35, xl + 35, yface, yface + dirn * 4, zc - 21, P.DECK_BOT_Z - 40 - 0.5)   # stays below the deck-angle leg
        cheeks = []
        for xa_, xb_ in ((xl - h - 5, xl - h), (xl + h, xl + h + 5)):
            ch = _bx(xa_, xb_, yface + dirn * 3.5, yp, zc - 21, zc + 21).fuse(_cylx(22, xa_, xb_, yp, zc))
            ch = ch.cut(_bx(xa_ - 1, xb_ + 1, yface - dirn * 5, yface + dirn * 3.5, zc - 30, zc + 30))
            ch = ch.cut(_cmp([_cylx(5.3, xa_ - 1, xb_ + 1, yp, zc), _cylx(4.25, xa_ - 1, xb_ + 1, ylk, zlk)]))
            cheeks.append(ch)
        parts.append(part(f"{nm}_leg_clevis_{i}", g, _cmp([base.fuse(cheeks[0]).fuse(cheeks[1])]), "alu_dark", fab=True, mat="Plate 6 5052"))
        hw = [_hexx(17, xl - h - 5 - 6.5, xl - h - 5, yp, zc), _cylx(5, xl - h - 5, xl + h + 5 + 9, yp, zc),     # M10 shoulder bolt
              _hexx(17, xl + h + 5, xl + h + 5 + 8, yp, zc), _cylx(6.5, xl + h + 5 + 8, xl + h + 5 + 9.5, yp, zc)]  # nyloc
        hw += _ball_lock_pin(xl - h - 5 - 3, xl + h + 5 + 0.5, ylk, zlk, head_dir=-1, r=4.0)                   # clevis lock pin
        hw += [_cyly(5.5, yface + dirn * 4, yface + dirn * 7.5, xl + s * 28, zc + dz) for s in (-1, 1) for dz in (-10, 10)]  # M6 buttons
        W = _leg_frame(deployed, xl, yp, zc, h, dirn, ztop)
        if deployed:
            s_end = ztop - (zg + fh)
            spans = [(0, l0), (l0 - P.LEG_OVERLAP, l0 - P.LEG_OVERLAP + l1), (s_end - l2, s_end)]
            pins = [l0 - 20, spans[1][1] - 20]
        else:
            s_end = l0
            spans = [(0, l0), (5, 5 + l1), (l0 - l2, l0)]
            pins = [l0 - 20, l0 - 45]                  # stowed: both pins parked through the nested sections
        for k, ((sz, wl, ln), (sa, sb)) in enumerate(zip(P.LEG_SECTIONS, spans)):
            if deployed:
                tb = tube_box(xl - sz / 2, xl + sz / 2, yp - sz / 2, yp + sz / 2, ztop - sb, ztop - sa, wall=wl, axis="Z")
            else:
                ya_, yb_ = sorted((W(sa)[0], W(sb)[0]))
                tb = tube_box(xl - sz / 2, xl + sz / 2, ya_, yb_, zc - sz / 2, zc + sz / 2, wall=wl, axis="Y")
            if k == 0:
                holes = [l0 - 20, l0 - 45]
            else:
                holes = [p for p in pins if sa + 8 < p < sb - 8]
                holes += [s for s in [sa + 15 + 25 * j for j in range(int((sb - sa - 25) / 25) + 1)]
                          if s < sb - 10 and all(abs(s - p) > 12 for p in holes)]
            tb = _cut(tb, [_cylx(4.2, xl - sz / 2 - 2, xl + sz / 2 + 2, *W(s)) for s in holes])
            parts.append(part(f"{nm}_leg_{i}_s{k}", g, tb, "alu_dark", fab=True, mat=f"SHS {sz}x{sz}x{wl:g} 6060"))
        for p in pins:          # joint pins: shank through the outermost section at that point, button head to +X (rear)
            sz = max(sz_ for (sz_, _, _), (sa, sb) in zip(P.LEG_SECTIONS, spans) if sa <= p <= sb)
            hw += _ball_lock_pin(xl - sz / 2 - 3, xl + sz / 2 + 0.5, *W(p), head_dir=1)
        parts.append(part(f"{nm}_leg_{i}_hw", g, _cmp(hw), "receiver", note="M10 shoulder bolt, lock + joint ball-lock pins, M6 buttons"))
        # ---- swivel levelling foot, built along +Z from the pad underside, then placed
        foot = [cq.Workplane("XY", origin=(0, 0, 3)).polyline(_poly(16, fd / 2)).close().workplane(offset=6).polyline(_poly(16, fd / 2 - 6))
                .close().loft().val(), _cylz(9, 9, 15, 0, 0, n=12), _cylz(5, 15, fh, 0, 0, n=8),
                _hexx(17, 0, 6, 0, 0).rotate(_v(0, 0, 0), _v(0, 1, 0), -90).translate((0, 0, fh - 12))]
        pad = [_cylz(fd / 2, 0, 3, 0, 0, n=16), _bx(-s2 / 2 + 0.3, s2 / 2 - 0.3, -s2 / 2 + 0.3, s2 / 2 - 0.3, fh - 3, fh)]   # + end plug
        if deployed:
            place = (lambda sh: sh.translate(_v(xl, yp, zg)))
        else:
            yfoot = yp - dirn * h + dirn * (l0 + fh)
            place = (lambda sh: sh.rotate(_v(0, 0, 0), _v(1, 0, 0), 90 * dirn).translate(_v(xl, yfoot, zc)))
        parts.append(part(f"{nm}_leg_{i}_foot", g, place(_cmp(foot)), "alu", kg=0.15))
        parts.append(part(f"{nm}_leg_{i}_foot_pad", g, place(_cmp(pad)), RUBBER))
        # ---- stow clip: UHMW block under the deck + spring-steel tool clip (fixed to the carriage in both states)
        ym = yp - dirn * h + dirn * l0 * 0.6
        blk = box(xl - 25, xl + 25, ym - 20, ym + 20, zc, P.DECK_BOT_Z).cut(
            box(xl - h - 2.2, xl + h + 2.2, ym - 21, ym + 21, zc - 1, zc + h + 2.2))
        parts.append(part(f"{nm}_leg_clip_{i}", g, blk, "uhmw", fab=True, mat="UHMW 10"))
        jaws = [_bx(xl + s * (h + 0.6), xl + s * (h + 1.8), ym - 12, ym + 12, zc - 7, zc + h + 1.8) for s in (-1, 1)]
        jaws.append(_bx(xl - h - 1.8, xl + h + 1.8, ym - 12, ym + 12, zc + h + 0.6, zc + h + 1.8))     # U-clip back
        parts.append(part(f"{nm}_leg_clip_{i}_spring", g, _cmp(jaws), "runner"))
    return parts


def _chain_link_flat(p, h, w, z0, odd):
    """One igus E2-style link lying on its side at the origin, along +X: the two stadium side plates are horizontal
    (bottom and top), crossbars stand vertical at the inner and outer radius (local +/-Y). Bends in the X-Y plane."""
    t = CHAIN_PLATE_T
    ins = 1.0 if odd else 0.0
    sol = [cq.Workplane("XY", origin=(0, 0, za)).slot2D(p + 6, h).extrude(t).val()
           for za in (z0 + ins, z0 + w - ins - t)]
    sol += [_bx(-p / 2 + 7, p / 2 - 7, s0, s1, z0 + t, z0 + w - t) for s0, s1 in ((h / 2 - 3.5, h / 2), (-h / 2, -h / 2 + 3.5))]
    return sol


def cable_chain(x0, cx0, cy0, cy1, top):
    """v0.12: chain lying on its side under the power deck, both runs side by side on a glide tray (bends in plan).
    Fixed end at the centre of the moving end's travel, length = travel/2 + pi R (as v0.8). Moving end: bracket hung from
    the front cross member, reaching back under the raised well pan. The trunk from the bay enters the front of the cassette
    and runs along the tray outboard of the fixed run."""
    R, h, w = P.CHAIN_R, P.CHAIN_H, P.CHAIN_W
    yc = (cy0 + cy1) / 2                                # band centre under the deck
    yfix, ymov = yc - R, yc + R                         # fixed (outboard) run, moving (inboard) run
    zt = P.BASE_T + P.CHAIN_TRAY_T                      # tray top
    xm = cx0 + P.CHAIN_MOVE_DX                          # moving end
    xf = P.SLIDE_X0 + P.CHAIN_MOVE_DX + P.SLIDE_EXT / 2  # fixed end: centre of the moving end's travel
    straight = P.SLIDE_EXT / 2
    lc = straight + math.pi * R
    xb = (xf + xm - straight) / 2                        # bend; stowed: at the moving end, extended: at the fixed end
    assert xb - R - h / 2 >= x0 + 30 - 1e-6, "chain bend fouls the bay"
    assert zt + w + 4 <= P.FRIDGE_WELL_Z - 3 + 1e-6, "chain fouls the well pan"
    la = xf - xb
    n = max(2, round(lc / CHAIN_PITCH))
    step = lc / n
    links = [_chain_link_flat(step, h, w, zt, False), _chain_link_flat(step, h, w, zt, True)]
    sols = []
    for i in range(n):
        s = (i + 0.5) * step
        if s < la:
            px, py, tx, ty = xf - s, yfix, -1.0, 0.0
        elif s < la + math.pi * R:
            ph = (s - la) / R
            px, py, tx, ty = xb - R * math.sin(ph), yc - R * math.cos(ph), -math.cos(ph), math.sin(ph)
        else:
            px, py, tx, ty = xb + (s - la - math.pi * R), ymov, 1.0, 0.0
        ang = math.degrees(math.atan2(ty, tx))
        sols += [sh.rotate(_v(0, 0, 0), _v(0, 0, 1), ang).translate(_v(px, py, 0)) for sh in links[i % 2]]
    parts = [part("slide_power_cable_chain", "slide_p", _cmp(sols), "chain", kg=1.4, chain_length_mm=round(lc), links=n,
                  product="igus E2.15 (R75) lying on its side, 38 mm tall")]
    # moving end: 4 mm plate hung from the front cross member (flange under it), reaching back under the well pan
    yb0 = ymov + h / 2 + 1
    zx = P.DECK_BOT_Z - 25                               # cross member underside
    mb = (box(cx0 + 20, xm + 15, yb0, yb0 + 4, zt + 3, zt + w)
          .union(box(cx0 + 20, cx0 + 60, yb0, yb0 + 4, zt + 3, zx))
          .union(box(cx0 + 15, cx0 + 60, yb0 - 16, yb0 + 4, zx - 3, zx)))
    parts.append(part("slide_power_chain_bracket", "slide_p", mb, "alu_dark", fab=True, mat="Plate 4 5052", kg=0.12))
    # fixed end: bracket bolted through the tray to a base cross tie
    fb = box(xf - 4, xf + 40, yfix - h / 2 - 6, yfix + h / 2 + 6, zt, zt + 3).union(
        box(xf - 4, xf - 1, yfix - h / 2 - 6, yfix + h / 2 + 6, zt + 3, zt + w))
    parts.append(part("slide_power_chain_bracket_fixed", "slide_p", fb, "alu_dark", fab=True, mat="Plate 3 5052", kg=0.05))
    parts.append(part("slide_power_chain_bracket_bolts", "slide_p", _cmp([_cylz(4.5, zt + 3, zt + 6, xf + 26, yfix + s * 10) for s in (-1, 1)]),
                      "receiver"))
    # glide tray: 3 mm aluminium on the base cross ties, low lips on both edges (stay under the stowed legs)
    ty_ = yfix - h / 2 - 34                              # trunk lane (outboard of the fixed run)
    y_lo, y_hi = ty_ - 14, ymov + h / 2 + 12
    tray = box(x0 + 8, x0 + P.SLIDE_L - 4, y_lo, y_hi, P.BASE_T, zt)
    lips = [box(x0 + 8, x0 + P.SLIDE_L - 4, yy, yy + 3, zt, zt + 6) for yy in (y_lo, y_hi - 3)]
    parts.append(part("slide_power_chain_tray", "slide_p", tray.union(_cmp(lips)), "alu", fab=True, mat="Plate 3 5052",
                      kg=1.4, note="glide tray + 6 mm lips; the fixed run and loop are open to inspect with the slide fully out"))
    anchor("slide_entry", (x0 + 12, ty_, zt + 8))
    anchor("chain_trunk_end", (xf - 30, ty_, zt + 8))
    anchor("chain_fixed", (xf, yfix, zt + w / 2))
    anchor("chain_bend_fixed", (xb, yfix, zt + w / 2))              # cables follow the chain round its loop
    anchor("chain_bend_tip", (xb - R, yc, zt + w / 2))
    anchor("chain_moving", (xm, ymov, zt + w / 2))
    anchor("pod_cable_in", (cx0 + 72, ymov, zt + w / 2))
    anchor("slide_bulkhead", (cx0 + 72, ymov, top + 20))
    return parts


def slides(ext_p, ext_d):
    return slide("p", ext_p, power=True) + slide("d", ext_d, power=False)


# intentional contacts declared for clash.py
CLASH_ALLOW = []
