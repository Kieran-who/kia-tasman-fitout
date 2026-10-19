"""Example payload on the slides (placeholders sized to typical products - not fabricated)."""
import params as P

from .core import box, cyl, part

FRIDGE = (716, 398, 476)       # [EST] 45 L class (e.g. Dometic CFX3 45 is 476 tall) - sits in the fridge well
MICROWAVE = (440, 332, 259)    # [PUB] e.g. NCE 20 L RV microwave 440 x 332 x 259, 700 W out / 1150 W in


def _carriage(side, ext):
    from .slides import slide_extent
    ya, yb = slide_extent(side)
    return P.SLIDE_X0 + ext, P.SLIDE_X0 + P.SLIDE_L + ext, ya, yb


def pins(name, x0, x1, y0, y1, z, g):
    """Ball-lock pins at the module corners (drop into the receiver grid)."""
    out = []
    for i, (x, y) in enumerate(((x0 + 50, y0 + 50), (x1 - 50, y0 + 50), (x0 + 50, y1 - 50), (x1 - 50, y1 - 50))):
        out.append(part(f"{name}_pin_{i}", g, cyl(9, 14, (x, y, z + 7)), "receiver", kg=0.05))
    return out


def payload(ext_p, ext_d):
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
    parts += pins("microwave_base", mx1 - md, mx1, yc - mw / 2, yc + mw / 2, top - 14, "payload")
    # ---- driver slide: 2-drawer module (ball-lock pins), dry-food crate strapped to the L-track
    cx0, cx1, cy0, cy1 = _carriage("d", ext_d)
    yc = (cy0 + cy1) / 2
    dx1 = cx1 - 10
    dx0 = dx1 - 560
    parts.append(part("drawer_module", "payload", box(dx0, dx1, cy0 + 10, cy1 - 10, top, top + 240), "ply", kg=18))
    for k, z in enumerate((top + 10, top + 125)):
        parts.append(part(f"drawer_module_front_{k}", "payload", box(dx1, dx1 + 4, cy0 + 20, cy1 - 20, z, z + 105), "alu_dark"))
    parts += pins("drawer_module", dx0, dx1, cy0 + 10, cy1 - 10, top - 14, "payload")
    parts.append(part("food_crate", "payload", box(cx0 + 40, cx0 + 520, cy0 + 30, cy1 - 30, top, top + 330).edges("|Z").fillet(20),
                      "payload", kg=22))
    for k, x in enumerate((cx0 + 140, cx0 + 420)):
        parts.append(part(f"crate_strap_{k}", "payload", box(x, x + 25, cy0 + 26, cy1 - 26, top + 330, top + 334).union(
            box(x, x + 25, cy0 + 26, cy0 + 30, top, top + 334)).union(box(x, x + 25, cy1 - 30, cy1 - 26, top, top + 334)), "strap"))
    return parts
