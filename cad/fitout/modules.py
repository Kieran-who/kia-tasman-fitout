"""Example payload on the slides (placeholders sized to typical products - not fabricated)."""
import params as P

from .core import box, cyl, part

FRIDGE = (716, 398, 476)       # [EST] 45 L class (e.g. Dometic CFX3 45 is 476 tall) - sits in the fridge well
PIN_L = 32                     # 8 mm ball-lock pin shank below the deck top: through 15 ply + 3 angle + RHS wall, balls lock beneath
MICROWAVE = (440, 332, 259)    # [PUB] e.g. NCE 20 L RV microwave 440 x 332 x 259, 700 W out / 1150 W in


def _carriage(side, ext):
    from .slides import slide_extent
    ya, yb = slide_extent(side)
    return P.SLIDE_X0 + ext, P.SLIDE_X0 + P.SLIDE_L + ext, ya, yb


def pins(name, x0, x1, y0, y1, z, g, grid=None):
    """Ball-lock pins near the module corners. With a receiver grid, each pin snaps to the grid point
    inside the footprint (>= 20 mm in) closest to its corner."""
    corners = ((x0, y0), (x1, y0), (x0, y1), (x1, y1))
    if grid:
        inside = [(x, y) for x, y in grid if x0 + 20 <= x <= x1 - 20 and y0 + 20 <= y <= y1 - 20]
        pts = [min(inside, key=lambda q: (q[0] - cx) ** 2 + (q[1] - cy) ** 2) for cx, cy in corners] if inside else []
    else:
        pts = [(x0 + 50 if cx == x0 else x1 - 50, y0 + 50 if cy == y0 else y1 - 50) for cx, cy in corners]
    out = []
    for i, (x, y) in enumerate(pts):
        out.append(part(f"{name}_pin_{i}", g, cyl(4, PIN_L, (x, y, z + 14 - PIN_L / 2)), "receiver", kg=0.05))
    return out


def payload(ext_p, ext_d):
    from .slides import grid_positions
    parts = []
    top = P.DECK_TOP_Z
    # ---- power slide: fridge in the well behind the power pod, microwave at the rear (door faces rear)
    cx0, cx1, cy0, cy1 = _carriage("p", ext_p)
    yc = (cy0 + cy1) / 2
    fl, fw, fh = FRIDGE
    fx0 = cx0 + P.BULKHEAD_D + 10
    zf = P.FRIDGE_WELL_Z + 10      # stands on the two L-tracks in the well pan
    parts.append(part("fridge", "payload", box(fx0, fx0 + fl, yc - fw / 2, yc + fw / 2, zf, zf + fh).edges("|Z").fillet(25),
                      "fridge", kg=55, note="45 L loaded"))
    for k, x in enumerate((fx0 + 150, fx0 + fl - 175)):
        parts.append(part(f"fridge_strap_{k}", "payload", box(x, x + 25, yc - fw / 2 - 4, yc + fw / 2 + 4, zf + fh, zf + fh + 3).union(
            box(x, x + 25, yc - fw / 2 - 4, yc - fw / 2, zf, zf + fh)).union(box(x, x + 25, yc + fw / 2, yc + fw / 2 + 4, zf, zf + fh)), "strap"))
    mw, md, mh = MICROWAVE
    mx1 = cx1 - 3
    md = min(md, P.MICROWAVE_D)
    parts.append(part("microwave", "payload", box(mx1 - md, mx1, yc - mw / 2, yc + mw / 2, top + 5, top + 5 + mh), "outlet", kg=11))
    parts.append(part("microwave_door", "payload", box(mx1 - 1, mx1 + 0.5, yc - mw / 2 + 10, yc + mw / 2 - 90, top + 20, top + mh - 10), "usb"))
    parts += pins("microwave_base", mx1 - md, mx1, yc - mw / 2, yc + mw / 2, top - 14, "payload", grid_positions(cx0, cx1, cy0, cy1, True))
    # ---- driver slide: 2-drawer module (ball-lock pins), dry-food crate strapped to the L-track
    cx0, cx1, cy0, cy1 = _carriage("d", ext_d)
    yc = (cy0 + cy1) / 2
    dx1 = cx1 - 10
    dx0 = dx1 - 560
    parts.append(part("drawer_module", "payload", box(dx0, dx1, cy0 + 10, cy1 - 10, top, top + 240), "ply", kg=18))
    for k, z in enumerate((top + 10, top + 125)):
        parts.append(part(f"drawer_module_front_{k}", "payload", box(dx1, dx1 + 4, cy0 + 20, cy1 - 20, z, z + 105), "alu_dark"))
    parts += pins("drawer_module", dx0, dx1, cy0 + 10, cy1 - 10, top - 14, "payload", grid_positions(cx0, cx1, cy0, cy1, False))
    parts.append(part("food_crate", "payload", box(cx0 + 40, cx0 + 520, cy0 + 30, cy1 - 30, top, top + 330).edges("|Z").fillet(20),
                      "payload", kg=22))
    for k, x in enumerate((cx0 + 140, cx0 + 420)):
        parts.append(part(f"crate_strap_{k}", "payload", box(x, x + 25, cy0 + 26, cy1 - 26, top + 330, top + 334).union(
            box(x, x + 25, cy0 + 26, cy0 + 30, top, top + 334)).union(box(x, x + 25, cy1 - 30, cy1 - 26, top, top + 334)), "strap"))
    return parts


FENCE_H = 95       # edge fence / divider wall height: wall top 101 above the deck clears the front bed hooks (bottom ~108) when stowed
FENCE_T = 12       # ply wall
FOOT_W = 60        # 60 x 6 alu flat foot, carries the ball-lock pins


def _fence(name, g, x0, x1, y_edge, s, top, pin_xs):
    """Long-edge fence: wall flush with the deck edge (s = +1 driver-side edge, -1 passenger-side edge),
    foot running inboard over the edge receiver row (37.6 mm in)."""
    yo, yi = y_edge, y_edge - s * FOOT_W
    ylo, yhi = min(yo, yi), max(yo, yi)
    out = [part(f"{name}_foot", g, box(x0, x1, ylo, yhi, top, top + 6), "alu", fab=True, mat="Flat 60x6 6060"),
           part(f"{name}_wall", g, box(x0, x1, min(yo, yo - s * FENCE_T), max(yo, yo - s * FENCE_T), top + 6, top + 6 + FENCE_H),
                "ply", fab=True, mat="Ply 12 marine")]
    pe = P.SIDE_PLATE_T + P.RUNNER_T + 1 + 12.5
    for i, x in enumerate(pin_xs):
        out.append(part(f"{name}_pin_{i}", g, cyl(4, PIN_L, (x, yo - s * pe, top - PIN_L / 2)), "receiver", kg=0.05))
    return out


def _cross(name, g, x, ya, yb, top, pin_ys):
    """Cross divider: 12 mm wall on a foot, pins in the interior rows, ends butt into the edge fences."""
    out = [part(f"{name}_foot", g, box(x - FOOT_W / 2, x + FOOT_W / 2, ya, yb, top, top + 6), "alu", fab=True, mat="Flat 60x6 6060"),
           part(f"{name}_wall", g, box(x - FENCE_T / 2, x + FENCE_T / 2, ya, yb, top + 6, top + 6 + FENCE_H), "ply", fab=True, mat="Ply 12 marine")]
    for i, y in enumerate(pin_ys):
        out.append(part(f"{name}_pin_{i}", g, cyl(4, PIN_L, (x, y, top - PIN_L / 2)), "receiver", kg=0.05))
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
