"""Example payload on the slides (placeholders sized to typical products - not fabricated).

v0.8 detail: the fridge is shaped like a Dometic CFX3 45 (lid, hinges, latch, end handles, control panel, compressor vents),
the microwave like an NCE 20 L (mirror door with window, control panel), the drawer module has fronts with flush pulls and
locks, the food crate a lid, ribs and hand holds; straps carry cam buckles. The example fences / dividers show their
ball-lock pin heads (the divider walls are notched over each pin).
"""
import params as P

from .core import box, cyl, part
from .slides import _bx, _cmp, _cut, _cylx, _cyly, _cylz, _try_fillet

FRIDGE = (694, 398, 476)       # [PUB] Dometic CFX3 45: 694 x 398 x 476 (dometic.com / retailers); v0.7 used 716 [EST]
FRIDGE_LID_H = 56              # [EST] lid thickness at the top
FRIDGE_COMP_L = 175            # [EST] compressor end (control panel + vents), at the slide-out (+X) end for access
PIN_L = 32                     # 8 mm ball-lock pin shank below the deck top: through 15 ply + 3 angle + RHS wall, balls lock beneath
MICROWAVE = (440, 332, 259)    # [PUB] NCE 20 L RV microwave 440 x 332 x 259, 700 W out / 1150 W in (mygenerator.com.au)
MW_PANEL_W = 105               # [EST] control panel width (right of the door, viewed from the rear)

# colours (RGBA)
SLATE = (66, 70, 74, 255)        # CFX3 body
LIGHT = (176, 180, 182, 255)     # CFX3 lid
BLACK = (24, 24, 26, 255)
GLASS = (14, 16, 20, 255)
SMOKE = (48, 56, 64, 255)
DISPLAY = (60, 190, 220, 255)
LED_RED = (230, 50, 40, 255)
STEEL = (196, 198, 200, 255)
KEY = (150, 152, 156, 255)
CRATE_LID = (60, 90, 60, 255)


def _carriage(side, ext):
    from .slides import slide_extent
    ya, yb = slide_extent(side)
    return P.SLIDE_X0 + ext, P.SLIDE_X0 + P.SLIDE_L + ext, ya, yb


def _pin_head(x, y, z):
    """Button-handle head of an 8 mm ball-lock pin standing on a surface at z: collar, knob, push button."""
    return [_cylz(8.5, z, z + 2.5, x, y, n=12), _cylz(8, z + 2.5, z + 12, x, y, n=12), _cylz(3.5, z + 12, z + 14, x, y, n=8)]


def pins(name, x0, x1, y0, y1, z, g, grid=None, head_z=None):
    """Ball-lock pins near the module corners. With a receiver grid, each pin snaps to the grid point
    inside the footprint (>= 20 mm in) closest to its corner. head_z: draw the pin head standing on that surface."""
    corners = ((x0, y0), (x1, y0), (x0, y1), (x1, y1))
    if grid:
        inside = [(x, y) for x, y in grid if x0 + 20 <= x <= x1 - 20 and y0 + 20 <= y <= y1 - 20]
        pts = [min(inside, key=lambda q: (q[0] - cx) ** 2 + (q[1] - cy) ** 2) for cx, cy in corners] if inside else []
    else:
        pts = [(x0 + 50 if cx == x0 else x1 - 50, y0 + 50 if cy == y0 else y1 - 50) for cx, cy in corners]
    out = []
    for i, (x, y) in enumerate(pts):
        shank = cyl(4, PIN_L, (x, y, z + 14 - PIN_L / 2))
        shape = shank if head_z is None else _cmp([shank] + _pin_head(x, y, head_z))
        out.append(part(f"{name}_pin_{i}", g, shape, "receiver", kg=0.05))
    return out


def _buckle(x, y_face, s, z, w=25):
    """Cam buckle on a strap lying on a face at y_face (s = outward direction): frame + cam lever."""
    y0, y1 = sorted((y_face, y_face + s * 4))
    y2, y3 = sorted((y_face + s * 4, y_face + s * 6))
    return [_bx(x - 3, x + w + 3, y0, y1, z, z + 42), _bx(x - 1, x + w + 1, y2, y3, z + 14, z + 40)]


def _fridge(cx0, yc):
    """Dometic CFX3 45-like: slate body with black base, light lid over the cabinet, compressor end with the control panel
    and vents at the slide-out end, folding end handles, two lid hinges (outboard) and a latch (inboard)."""
    parts = []
    fl, fw, fh = FRIDGE
    fx0 = cx0 + P.BULKHEAD_D + 10
    fx1 = fx0 + fl
    zf = P.FRIDGE_WELL_Z           # v0.12: stands on the pan (no floor tracks: the chain runs under the pan)
    y0, y1 = yc - fw / 2, yc + fw / 2
    zl = zf + fh - FRIDGE_LID_H     # lid underside
    xc = fx1 - FRIDGE_COMP_L        # cabinet / compressor split
    zc = zf + fh - 36               # compressor housing top (a step below the lid)
    body = box(fx0, fx1, y0, y1, zf + 28, zl).union(box(xc, fx1, y0, y1, zl - 1, zc))
    body = _try_fillet(body, "|Z", 25)
    parts.append(part("fridge", "payload", body, SLATE, kg=55, note="45 L loaded", product="Dometic CFX3 45 (694 x 398 x 476)"))
    base = _try_fillet(box(fx0, fx1, y0, y1, zf, zf + 28), "|Z", 25)                       # black bumper base
    hinges = [_bx(x, x + 50, y0 - 6, y0, zl - 12, zl + 18) for x in (fx0 + 60, xc - 140)]   # outboard (-Y) side
    latch = [_bx(fx0 + 230, fx0 + 300, y1, y1 + 6, zl - 25, zl + 20)]                      # inboard (+Y) side
    handles = []                                                                            # folding end handles (stowed)
    for xf, s, zh in ((fx0, -1, zl - 50), (fx1, 1, zc - 130)):     # +X end: below the control panel
        handles += [_bx(xf, xf + s * 9, yc - 150, yc + 150, zh, zh + 10)]
        handles += [_bx(xf, xf + s * 9, yc + d - 6, yc + d + 6, zh, zh + 40) for d in (-150, 150)]
    vents = [_bx(x, x + 6, y0 - 1, y0, zf + 60, zf + 200) for x in range(int(xc + 32), int(fx1 - 30), 14)]
    vents += [_bx(x, x + 6, y1, y1 + 1, zf + 60, zf + 200) for x in range(int(xc + 32), int(fx1 - 30), 14)]
    vents += [_bx(fx1, fx1 + 1, y, y + 6, zf + 50, zf + 150) for y in range(int(y0 + 50), int(y1 - 50), 14)]
    parts.append(part("fridge_trim", "payload", _cmp([base] + hinges + latch + handles + vents), BLACK))
    lid = _try_fillet(box(fx0 + 4, xc - 4, y0 + 4, y1 - 4, zl, zf + fh), "|Z", 21)
    lid = _try_fillet(lid, ">Z", 6)
    lid = _cut(lid, [_bx(fx0 + 60, xc - 60, y0 + 50, y1 - 50, zf + fh - 3, zf + fh + 1)])   # recessed top panel
    parts.append(part("fridge_lid", "payload", lid, LIGHT))
    # control panel on the compressor housing's sloping top / end: display + buttons
    panel = _bx(fx1, fx1 + 1, yc - 80, yc + 80, zc - 70, zc - 15)
    parts.append(part("fridge_panel", "payload", _cmp([_bx(fx1 - 150, fx1 - 25, yc - 90, yc + 90, zc, zc + 1.5), panel]), GLASS))
    keys = [_bx(fx1 + 1, fx1 + 2.2, yc + d - 7, yc + d + 7, zc - 55, zc - 45) for d in (-60, -35, 35, 60)]
    keys.append(_bx(fx1 + 1, fx1 + 1.6, yc - 22, yc + 22, zc - 62, zc - 26))               # display
    parts.append(part("fridge_display", "payload", _cmp(keys), DISPLAY))
    # straps over the lid down to flush anchors on the pan floor, cam buckles on the inboard side
    for k, x in enumerate((fx0 + 150, xc - 85)):                 # both over the lid
        parts.append(part(f"fridge_strap_{k}", "payload", box(x, x + 25, y0 - 4, y1 + 4, zf + fh, zf + fh + 3).union(
            box(x, x + 25, y0 - 4, y0, zf, zf + fh)).union(box(x, x + 25, y1, y1 + 4, zf, zf + fh)), "strap"))
        parts.append(part(f"fridge_strap_{k}_buckle", "payload", _cmp(_buckle(x, y1 + 4, 1, zf + 230)), STEEL))
    return parts


def _microwave(cx1, yc, top, grid):
    """NCE 20 L-like: stainless case on rubber feet, mirror-glass door with a smoked window, control panel on the right
    (viewed from the rear), door faces the slide-out end."""
    parts = []
    mw, md, mh = MICROWAVE
    mx1 = cx1 - 3
    md = min(md, P.MICROWAVE_D)
    z0 = top + 5
    y0, y1 = yc - mw / 2, yc + mw / 2
    case = _try_fillet(box(mx1 - md, mx1 - 3, y0, y1, z0, z0 + mh), "|X", 4)
    case = _cut(case, [_bx(mx1 - md + 40 + 12 * k, mx1 - md + 46 + 12 * k, y0 - 1, y0 + 1.5, z0 + 60, z0 + 200) for k in range(8)])  # side vents
    parts.append(part("microwave", "payload", case, STEEL, kg=11, product="NCE 20 L RV microwave 440 x 332 x 259"))
    parts.append(part("microwave_feet", "payload", _cmp([_cylz(9, top, z0, x, y, n=10) for x in (mx1 - md + 30, mx1 - 33)
                                                         for y in (y0 + 30, y1 - 30)]), BLACK))
    yd = y1 - MW_PANEL_W                  # door | panel split (+Y = right when viewed from the rear)
    door = box(mx1 - 3, mx1, y0 + 2, yd - 1, z0 + 2, z0 + mh - 2)
    door = _try_fillet(door, "|X", 3)
    door = _cut(door, [_bx(mx1 - 1, mx1 + 1, yd - 30, yd - 8, z0 + 90, z0 + 170)])       # finger recess on the opening edge
    parts.append(part("microwave_door", "payload", door, GLASS))
    parts.append(part("microwave_window", "payload", _bx(mx1, mx1 + 0.4, y0 + 40, yd - 50, z0 + 40, z0 + mh - 40), SMOKE))
    parts.append(part("microwave_panel", "payload", _bx(mx1 - 3, mx1 - 0.5, yd, y1 - 2, z0 + 2, z0 + mh - 2), BLACK))
    keys = [_bx(mx1 - 0.5, mx1 + 0.3, yd + 14 + 26 * c, yd + 34 + 26 * c, z0 + 120 - 20 * r, z0 + 132 - 20 * r)
            for r in range(4) for c in range(3)]
    keys += [_bx(mx1 - 0.5, mx1 + 0.6, yd + 14, yd + MW_PANEL_W - 16, z0 + 22, z0 + 40)]          # start / door release
    parts.append(part("microwave_keys", "payload", _cmp(keys), KEY))
    parts.append(part("microwave_led", "payload", _bx(mx1 - 0.5, mx1 + 0.3, yd + 22, yd + MW_PANEL_W - 24, z0 + 190, z0 + 210), LED_RED))
    parts += pins("microwave_base", mx1 - md, mx1, y0, y1, top - 14, "payload", grid)
    return parts


def _drawers(cx0, cx1, cy0, cy1, top, grid):
    """2-drawer module: 12 mm ply carcass, alu fronts with flush stainless pulls and push-button locks."""
    parts = []
    dx1 = cx1 - 10
    dx0 = dx1 - 560
    parts.append(part("drawer_module", "payload", _try_fillet(box(dx0, dx1, cy0 + 10, cy1 - 10, top, top + 240), "|Z", 3), "ply", kg=18))
    yc = (cy0 + cy1) / 2
    for k, z in enumerate((top + 10, top + 125)):
        fr = _try_fillet(box(dx1, dx1 + 4, cy0 + 20, cy1 - 20, z, z + 105), "|X", 6)
        zc = z + 105 / 2
        fr = _cut(fr, [_bx(dx1 - 1, dx1 + 5, yc - 50, yc + 50, zc - 12, zc + 12)])            # pull opening
        parts.append(part(f"drawer_module_front_{k}", "payload", fr, "alu_dark"))
        bez = _cut(_bx(dx1 + 4, dx1 + 5.5, yc - 58, yc + 58, zc - 19, zc + 19), [_bx(dx1 + 3, dx1 + 7, yc - 50, yc + 50, zc - 12, zc + 12)])
        lock = _cylx(7, dx1 + 4, dx1 + 7, yc + 95, zc, n=12)
        parts.append(part(f"drawer_module_front_{k}_pull", "payload", _cmp([bez, lock]), STEEL))
        parts.append(part(f"drawer_module_front_{k}_pull_recess", "payload",
                          _bx(dx1, dx1 + 0.3, yc - 50, yc + 50, zc - 12, zc + 12), BLACK))
    parts += pins("drawer_module", dx0, dx1, cy0 + 10, cy1 - 10, top - 14, "payload", grid)
    return parts


def _crate(cx0, cy0, cy1, top):
    """Dry-food crate (Wolf-pack class): ribbed body, separate lid with latches, hand holds in the ends; two straps."""
    parts = []
    x0, x1 = cx0 + 40, cx0 + 520
    y0, y1 = cy0 + 30, cy1 - 30
    zt = top + 330
    parts.append(part("food_crate", "payload", box(x0, x1, y0, y1, top, zt - 45).edges("|Z").fillet(20), "payload", kg=22))
    lid = _try_fillet(box(x0, x1, y0, y1, zt - 45, zt).edges("|Z").fillet(20), ">Z", 5)
    parts.append(part("food_crate_lid", "payload", lid, CRATE_LID))
    det = []
    straps = ((cx0 + 140, cx0 + 165), (cx0 + 420, cx0 + 445))
    ribs = [x for x in range(int(x0 + 60), int(x1 - 50), 70) if all(not (a - 12 < x < b + 6) for a, b in straps)]
    det += [_bx(x, x + 6, y0 - 3, y0, top + 20, zt - 60) for x in ribs] + [_bx(x, x + 6, y1, y1 + 3, top + 20, zt - 60) for x in ribs]
    for xf, s in ((x0, -1), (x1, 1)):
        det.append(_bx(xf, xf + s * 1, (y0 + y1) / 2 - 60, (y0 + y1) / 2 + 60, zt - 110, zt - 80))         # hand hold
        det += [_bx(xf, xf + s * 5, yy - 15, yy + 15, zt - 60, zt - 25) for yy in ((y0 + y1) / 2 - 110, (y0 + y1) / 2 + 110)]  # latches
    parts.append(part("food_crate_detail", "payload", _cmp(det), BLACK))
    for k, (x, _) in enumerate(straps):
        parts.append(part(f"crate_strap_{k}", "payload", box(x, x + 25, cy0 + 26, cy1 - 26, zt, zt + 4).union(
            box(x, x + 25, cy0 + 26, cy0 + 30, top, zt + 4)).union(box(x, x + 25, cy1 - 30, cy1 - 26, top, zt + 4)), "strap"))
        parts.append(part(f"crate_strap_{k}_buckle", "payload", _cmp(_buckle(x, cy1 - 26, 1, top + 150)), STEEL))
    return parts


def payload(ext_p, ext_d):
    from .slides import grid_positions
    parts = []
    top = P.DECK_TOP_Z
    # ---- power slide: fridge in the well behind the power pod, microwave at the rear (door faces rear)
    cx0, cx1, cy0, cy1 = _carriage("p", ext_p)
    yc = (cy0 + cy1) / 2
    parts += _fridge(cx0, yc)
    parts += _microwave(cx1, yc, top, grid_positions(cx0, cx1, cy0, cy1, True))
    # ---- driver slide: 2-drawer module (ball-lock pins), dry-food crate strapped to the L-track
    cx0, cx1, cy0, cy1 = _carriage("d", ext_d)
    parts += _drawers(cx0, cx1, cy0, cy1, top, grid_positions(cx0, cx1, cy0, cy1, False))
    parts += _crate(cx0, cy0, cy1, top)
    return parts


FENCE_H = 150      # edge fence / divider wall height above the deck (anything up to ~180 clears the upper drawers when stowed)
FENCE_T = 12       # ply wall
FOOT_W = 60        # 60 x 6 alu flat foot, carries the ball-lock pins


def _wall_slots(x0, x1, y0, y1, z_top, along):
    """Hand slots (rounded 110 x 28) near the top of a wall: one per ~500 mm of wall length."""
    L = (x1 - x0) if along == "X" else (y1 - y0)
    n = max(1, int(L // 500))
    out = []
    for k in range(n):
        c = (x0 if along == "X" else y0) + L * (k + 0.5) / n
        if along == "X":
            sl = _bx(c - 41, c + 41, y0 - 1, y1 + 1, z_top - 52, z_top - 24).fuse(
                _cyly(14, y0 - 1, y1 + 1, c - 41, z_top - 38, n=12), _cyly(14, y0 - 1, y1 + 1, c + 41, z_top - 38, n=12))
        else:
            sl = _bx(x0 - 1, x1 + 1, c - 41, c + 41, z_top - 52, z_top - 24).fuse(
                _cylx(14, x0 - 1, x1 + 1, c - 41, z_top - 38, n=12), _cylx(14, x0 - 1, x1 + 1, c + 41, z_top - 38, n=12))
        out.append(sl.clean())          # one fused tool per slot (overlapping tools in one compound do not cut cleanly)
    return out


def _fence(name, g, x0, x1, y_edge, s, top, pin_xs):
    """Long-edge fence: wall flush with the deck edge (s = +1 driver-side edge, -1 passenger-side edge),
    foot running inboard over the edge receiver row (37.6 mm in)."""
    yo, yi = y_edge, y_edge - s * FOOT_W
    ylo, yhi = min(yo, yi), max(yo, yi)
    pe = P.SIDE_PLATE_T + P.RUNNER_T + 1 + 12.5
    foot = _cut(box(x0, x1, ylo, yhi, top, top + 6), [_cylz(4.3, top - 1, top + 7, x, yo - s * pe) for x in pin_xs])
    wy0, wy1 = min(yo, yo - s * FENCE_T), max(yo, yo - s * FENCE_T)
    zt = top + 6 + FENCE_H
    wall = _try_fillet(box(x0, x1, wy0, wy1, top + 6, zt), "|X and >Z", 3)
    wall = _cut(wall, _wall_slots(x0, x1, wy0, wy1, zt, "X"))
    out = [part(f"{name}_foot", g, foot, "alu", fab=True, mat="Flat 60x6 6060"),
           part(f"{name}_wall", g, wall, "ply", fab=True, mat="Ply 12 marine")]
    for i, x in enumerate(pin_xs):
        y = yo - s * pe
        out.append(part(f"{name}_pin_{i}", g, _cmp([cyl(4, PIN_L, (x, y, top - PIN_L / 2))] + _pin_head(x, y, top + 6)), "receiver", kg=0.05))
    return out


def _cross(name, g, x, ya, yb, top, pin_ys):
    """Cross divider: 12 mm wall on a foot, pins in the interior rows (wall notched over each pin head), ends butt into the
    edge fences."""
    foot = _cut(box(x - FOOT_W / 2, x + FOOT_W / 2, ya, yb, top, top + 6), [_cylz(4.3, top - 1, top + 7, x, y) for y in pin_ys])
    zt = top + 6 + FENCE_H
    wall = _try_fillet(box(x - FENCE_T / 2, x + FENCE_T / 2, ya, yb, top + 6, zt), "|Y and >Z", 3)
    wall = _cut(wall, [_bx(x - FENCE_T, x + FENCE_T, y - 12, y + 12, top + 5, top + 6 + 20) for y in pin_ys] +
                _wall_slots(x - FENCE_T / 2, x + FENCE_T / 2, ya, yb, zt, "Y"))
    out = [part(f"{name}_foot", g, foot, "alu", fab=True, mat="Flat 60x6 6060"),
           part(f"{name}_wall", g, wall, "ply", fab=True, mat="Ply 12 marine")]
    for i, y in enumerate(pin_ys):
        out.append(part(f"{name}_pin_{i}", g, _cmp([cyl(4, PIN_L, (x, y, top - PIN_L / 2))] + _pin_head(x, y, top + 6)), "receiver", kg=0.05))
    return out


def edge_modules(ext_p, ext_d):
    """Example flush edge fences + cross dividers (option group 'modules', shown with the payload hidden)."""
    from .slides import grid_positions
    g, top, parts = "modules", P.DECK_TOP_Z, []
    for side, power in (("p", True), ("d", False)):
        cx0, cx1, ya, yb = _carriage(side, ext_p if power else ext_d)
        pts = grid_positions(cx0, cx1, ya, yb, power)
        xs = sorted({x for x, _ in pts})
        ys = sorted({y for _, y in pts})
        fx0 = cx0 + (P.BULKHEAD_D + 6 if power else 4)
        fx1 = cx1 - 4
        pin_xs = xs[::2] if xs[-1] in xs[::2] else xs[::2] + [xs[-1]]
        nm = f"{side}_fence"
        parts += _fence(f"{nm}_out" if power else f"{nm}_in", g, fx0, fx1, ya, -1, top, pin_xs)
        parts += _fence(f"{nm}_in" if power else f"{nm}_out", g, fx0, fx1, yb, +1, top, pin_xs)
        xm = xs[len(xs) // 2]
        parts += _cross(f"{side}_divider", g, xm, ya + FOOT_W, yb - FOOT_W, top, ys[1:-1][::2])
    return parts


# intentional contacts declared for clash.py
CLASH_ALLOW = []
