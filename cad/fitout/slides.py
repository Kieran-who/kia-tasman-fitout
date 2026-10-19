"""
Heavy-duty slide-out platforms.

Each slide = fixed cassette (base plates, cross ties, runner angles) + moving carriage (RHS frame,
recessed 15 mm ply deck, centre L-track, ball-lock receiver grid). The power slide has a dropped
fridge well at its front, an outlet bulkhead, and is fed by an upright cable chain that runs in
the centre gap between the two slides.
"""
import cadquery as cq

import params as P

from .core import anchor, box, cyl, part, ring, tube_box, union_all


def _receivers(nm, g, cx0, cx1, cy0, cy1, yc, top, skip=None):
    pitch = P.RECEIVER_PITCH
    ny = int((cy1 - cy0 - 80) // pitch)
    nx = int((cx1 - cx0 - 80) // pitch)
    gx0 = cx0 + ((cx1 - cx0) - nx * pitch) / 2
    recs, bores = [], []
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = gx0 + i * pitch
            y = yc - ny * pitch / 2 + j * pitch
            if abs(y - yc) < 45 or (skip and skip[0] - 20 < x < skip[1] + 20):
                continue
            recs.append(ring(P.RECEIVER_D / 2, 4.2, 2.2, (x, y, top - 1)))
            bores.append(cyl(4.2, 2.4, (x, y, top - 1)))
    return [part(f"{nm}_receivers", g, union_all(recs), "receiver", kg=0.03 * len(recs), n_receivers=len(recs)),
            part(f"{nm}_receiver_bores", g, union_all(bores), "hole")]


def slide(side: str, ext: float, power: bool, runners: int):
    """side 'p' = passenger (-Y), 'd' = driver (+Y). ext = extension (0 = stowed)."""
    parts = []
    s = -1 if side == "p" else 1
    ya, yb = sorted((s * P.SLIDE_GAP_MID / 2, s * (P.SLIDE_GAP_MID / 2 + P.CASSETTE_W)))
    x0, x1 = P.SLIDE_X0, P.SLIDE_X0 + P.SLIDE_L
    g = f"slide_{side}"
    nm = "slide_power" if power else "slide_driver"
    ykc = (ya + yb) / 2
    bt = P.BASE_T
    # ------------------------------------------------ fixed cassette
    for yy in (ya, yb - 60):
        parts.append(part(f"{nm}_base_plate_{int(yy)}", g, box(x0, x1, yy, yy + 60, 0, bt), "alu", fab=True, mat="Plate 6 5052"))
    for i, xx in enumerate((x0 + 10, (x0 + x1) / 2 - 25, x1 - 60)):
        parts.append(part(f"{nm}_base_cross_{i}", g, box(xx, xx + 50, ya + 60, yb - 60, 0, 6), "alu", fab=True, mat="Flat 50x6 6060"))
    rz0, rz1 = bt, bt + P.RUNNER_H
    for lab, yy in (("a", ya), ("b", yb - P.SIDE_PLATE_T)):    # vertical runner plates welded to the base plates
        parts.append(part(f"{nm}_runner_plate_{lab}", g, box(x0, x1, yy, yy + P.SIDE_PLATE_T, bt, rz1 + 2), "alu", fab=True, mat="Plate 6 5052"))
    for yy in (ya + 30, yb - 70):   # UHMW stops: stowed carriage rests on these, road shock bypasses the runners
        parts.append(part(f"{nm}_uhmw_stop_{int(yy)}", g, box(x1 - 120, x1 - 20, yy, yy + 40, 25, 30), "uhmw", fab=True, mat="UHMW 10"))
    # ------------------------------------------------ runners (3-member, 100 % extension)
    third = P.RUNNER_T / 3
    rl = P.RUNNER_LEN

    def runner_set(y_face, dirn, label):
        for k, off in enumerate((0, ext / 2, ext)):
            yy0 = y_face + dirn * k * third
            parts.append(part(f"{nm}_runner_{label}_{k}", g, box(x0 + 3 + off, x0 + 3 + rl + off, yy0, yy0 + dirn * third, rz0 + 3, rz1 - 3),
                              "runner", kg=2.0))
    runner_set(ya + P.SIDE_PLATE_T, 1, "a")
    runner_set(yb - P.SIDE_PLATE_T, -1, "b")
    if runners == 4:
        parts.append(part(f"{nm}_keel", g, box(x0, x1, ykc - P.KEEL_T / 2, ykc + P.KEEL_T / 2, bt, rz1), "alu", fab=True, mat="Plate 6 5052"))
        runner_set(ykc + P.KEEL_T / 2, 1, "keel_a")
        runner_set(ykc - P.KEEL_T / 2, -1, "keel_b")
    # ------------------------------------------------ carriage
    cy0 = ya + P.SIDE_PLATE_T + P.RUNNER_T + 1
    cy1 = yb - P.SIDE_PLATE_T - P.RUNNER_T - 1
    cx0, cx1 = x0 + ext, x1 + ext
    top = P.DECK_TOP_Z
    deck_bot = top - P.DECK_T
    yc = (cy0 + cy1) / 2
    for i, yy in enumerate((cy0, cy1 - 25)):
        parts.append(part(f"{nm}_carr_side_{i}", g, tube_box(cx0, cx1, yy, yy + 25, rz0 + 1, top, axis="X"), "alu", fab=True, mat="RHS 75x25x2 6060"))
    if runners == 4:
        for dirn in (1, -1):
            yy = ykc + dirn * (P.KEEL_T / 2 + P.RUNNER_T + 1)
            parts.append(part(f"{nm}_keel_hanger_{dirn}", g, box(cx0, cx1, yy, yy + dirn * 25, rz0 + 1, deck_bot), "alu", fab=True, mat="RHS 75x25x2 6060"))
    # power slide: bulkhead + fridge well occupy the front; deck covers the rest
    well = None
    if power:
        wx0 = cx0 + P.BULKHEAD_D
        wx1 = wx0 + P.FRIDGE_WELL_L
        well = (wx0, wx1)
        dx0 = wx1
    else:
        dx0 = cx0
    n_cross = 4 if power else 5
    span0 = dx0 + 10
    for i in range(n_cross):
        xx = span0 + i * (cx1 - 60 - span0) / (n_cross - 1)
        parts.append(part(f"{nm}_carr_cross_{i}", g, tube_box(xx, xx + 50, cy0 + 25, cy1 - 25, deck_bot - 25, deck_bot, axis="Y"),
                          "alu", fab=True, mat="RHS 50x25x2 6060"))
    deck = box(dx0 + (0 if power else 4), cx1 - 4, cy0 + 25, cy1 - 25, deck_bot, top)
    deck = deck.cut(box(dx0 - 1, cx1, yc - P.LTRACK_W / 2, yc + P.LTRACK_W / 2, top - P.LTRACK_H, top + 1))
    parts.append(part(f"{nm}_deck", g, deck, "ply", fab=True, mat="Ply 15 marine"))
    track = box(dx0 + 15, cx1 - 15, yc - P.LTRACK_W / 2, yc + P.LTRACK_W / 2, top - P.LTRACK_H, top)
    track = track.cut(box(dx0 + 10, cx1 - 10, yc - 6, yc + 6, top - 6, top + 1))
    parts.append(part(f"{nm}_ltrack", g, track, "ltrack", fab=True, mat="L-track HD"))
    holes = union_all(cyl(6, 3, (dx0 + 30 + i * 25.4, yc, top - 0.5)) for i in range(int((cx1 - dx0 - 60) / 25.4)))
    parts.append(part(f"{nm}_ltrack_pockets", g, holes, "hole"))
    parts += _receivers(nm, g, dx0, cx1, cy0, cy1, yc, top)
    if power:
        wx0, wx1 = well
        zf = P.FRIDGE_WELL_Z
        # folded 3 mm pan bolted to the side RHS: floor + front/rear walls up to the deck
        pan = (box(wx0, wx1, cy0 + 25, cy1 - 25, zf - 3, zf)
               .union(box(wx0, wx0 + 3, cy0 + 25, cy1 - 25, zf - 3, top))
               .union(box(wx1 - 3, wx1, cy0 + 25, cy1 - 25, zf - 3, top)))
        parts.append(part(f"{nm}_fridge_well_pan", g, pan, "alu", fab=True, mat="Plate 3 5052"))
        for yy in (cy0 + 40, cy1 - 70):      # tie-down L-track on the pan floor for the fridge straps
            parts.append(part(f"{nm}_well_track_{int(yy)}", g, box(wx0 + 30, wx1 - 30, yy, yy + 30, zf, zf + 10), "ltrack",
                              fab=True, mat="L-track HD"))
        # power pod at the very front: sockets on its TOP face (plugs point up, clear of the fridge)
        bw0, bw1 = cy0 + 28, cy1 - 28
        pz = top + 216
        parts.append(part(f"{nm}_power_pod", g, box(cx0 + 2, cx0 + P.BULKHEAD_D, bw0, bw1, zf, pz), "alu_dark", fab=True, mat="Plate 3 5052"))
        px = cx0 + 8
        parts.append(part(f"{nm}_gpo", g, box(px, px + 58, bw0 + 12, bw0 + 128, pz - 2, pz + 8), "outlet", kg=0.4))
        parts.append(part(f"{nm}_anderson", g, box(px + 4, px + 54, bw0 + 145, bw0 + 205, pz - 2, pz + 10), "anderson", kg=0.1))
        parts.append(part(f"{nm}_12v", g, cyl(17, 10, (px + 29, bw0 + 245, pz + 3)), "usb", kg=0.05))
        parts.append(part(f"{nm}_usbc", g, cyl(15, 10, (px + 29, bw0 + 300, pz + 3)), "usb", kg=0.05))
        zb = pz
        anchor("slide_bulkhead", (cx0 + 25, (bw0 + bw1) / 2, zb))
    # rear face + handle
    parts.append(part(f"{nm}_rear_plate", g, box(cx1 - 3, cx1, cy0, cy1, rz0, top + 2), "alu", fab=True, mat="Plate 3 5052"))
    parts.append(part(f"{nm}_handle", g, box(cx1 - 3.5, cx1 + 1, yc - 120, yc + 120, top - 50, top - 20).cut(
        box(cx1 - 4, cx1 + 2, yc - 105, yc + 105, top - 44, top - 26)), "alu_dark", kg=0.3))   # flush pull + lock release
    # removable pin-in legs at the rear (deployed in camp mode; stored in the utility drawer)
    if ext > 0:
        zg = -P.FLOOR_ABOVE_GROUND
        for i, yy in enumerate((cy0 + P.LEG_INSET, cy1 - P.LEG_INSET - 30)):
            leg = tube_box(cx1 - 70, cx1 - 40, yy, yy + 30, zg, rz0 + 5, axis="Z").union(box(cx1 - 85, cx1 - 25, yy - 15, yy + 45, zg, zg + 6))
            parts.append(part(f"{nm}_leg_{i}", g, leg, "alu_dark", fab=True, mat="SHS 30x30x2 6060"))
    if power:
        parts += cable_chain(x0, cx0, s)
    return parts


def cable_chain(x0, cx0, s):
    """Upright chain in the centre gap: lower run on the floor, upper run attached to the power-slide front."""
    R, h, w = P.CHAIN_R, P.CHAIN_H, P.CHAIN_W
    xf = x0 + P.SLIDE_EXT / 2 + 40                       # fixed end at mid travel
    xm = cx0 + 110                                      # moving end (on the carriage)
    lc = (xf + (x0 + 110) - 2 * (x0 + 72)) + 3.14159 * R
    xb = (xf + xm - lc + 3.14159 * R) / 2               # bend position (toward the front)
    y0, y1 = -w / 2, w / 2
    zc = 3 + R + h / 2                                   # bend centre height (chain sits on a 3 mm UHMW trough)
    lower = box(xb, xf, y0, y1, 3, 3 + h)
    upper = box(xb, xm, y0, y1, 3 + 2 * R, 3 + 2 * R + h)
    bend = (cq.Workplane("XZ", origin=(0, y1, 0)).center(xb, zc).circle(R + h / 2).circle(R - h / 2).extrude(w)
            .cut(box(xb, xb + R + h, y0 - 1, y1 + 1, -1, 2 * R + h + 5)))
    parts = [part("slide_power_cable_chain", "slide_p", lower.union(upper).union(bend), "chain", kg=1.2, chain_length_mm=round(lc))]
    parts.append(part("slide_power_chain_bracket", "slide_p", box(xm - 30, xm + 30, s * 18, s * 76, P.DECK_TOP_Z, 3 + 2 * R + h + 8), "alu_dark",
                      fab=True, mat="Plate 3 5052"))
    parts.append(part("slide_power_chain_trough", "slide_p", box(x0 + 10, xf + 40, -w / 2 - 4, w / 2 + 4, 0, 3), "uhmw", fab=True, mat="UHMW 10"))
    anchor("chain_fixed", (xf, 0, h / 2))
    anchor("chain_moving", (xm, 0, 2 * R + h / 2))
    return parts


def slides(ext_p, ext_d):
    return (slide("p", ext_p, power=True, runners=P.RUNNERS_POWER)
            + slide("d", ext_d, power=False, runners=P.RUNNERS_DRIVER))
