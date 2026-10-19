"""
Slide-out platforms (v0.5): side-mount locking runners with a COVERED deck.

Each slide = fixed cassette (base plates, cross ties, vertical runner plates) + moving carriage
(RHS side members on the runners, cross members, aluminium L-angles whose top leg reaches out over the
runners). A 15 mm ply deck sits on top and covers the full slide width, so the two decks meet in the
middle with a 6 mm gap: one continuous surface except the power slide's fridge well. The upright cable
chain runs in a lane on the power slide's outboard side.
"""
import cadquery as cq

import params as P

from .core import anchor, box, cyl, part, ring, tube_box, union_all


def slide_extent(side):
    """Y extents of the cassette / deck for a slide: (y_low, y_high)."""
    gap = P.SLIDE_GAP_MID / 2
    edge = P.ARCH_GAP / 2 - 3
    if side == "p":
        return -(edge - P.CHAIN_LANE), -gap
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


def _receiver_parts(name, g, pts, top):
    recs = [ring(P.RECEIVER_D / 2, 4.2, 2.2, (x, y, top - 1)) for x, y in pts]
    bores = [cyl(4.2, 2.4, (x, y, top - 1)) for x, y in pts]
    if not recs:
        return []
    return [part(f"{name}_receivers", g, union_all(recs), "receiver", kg=0.03 * len(recs), n_receivers=len(recs)),
            part(f"{name}_receiver_bores", g, union_all(bores), "hole")]


def slide(side: str, ext: float, power: bool):
    parts = []
    g = f"slide_{side}"
    nm = "slide_power" if power else "slide_driver"
    ya, yb = slide_extent(side)
    x0, x1 = P.SLIDE_X0, P.SLIDE_X0 + P.SLIDE_L
    bt = P.BASE_T
    rz0, rz1 = bt, bt + P.RUNNER_H
    # ------------------------------------------------ fixed cassette
    for yy in (ya, yb - 60):
        parts.append(part(f"{nm}_base_plate_{int(yy)}", g, box(x0, x1, yy, yy + 60, 0, bt), "alu", fab=True, mat="Plate 6 5052"))
    for i, xx in enumerate((x0 + 10, (x0 + x1) / 2 - 25, x1 - 60)):
        parts.append(part(f"{nm}_base_cross_{i}", g, box(xx, xx + 50, ya + 60, yb - 60, 0, bt), "alu", fab=True, mat="Flat 50x6 6060"))
    for lab, yy in (("a", ya), ("b", yb - P.SIDE_PLATE_T)):    # vertical runner plates welded to the base plates
        parts.append(part(f"{nm}_runner_plate_{lab}", g, box(x0, x1, yy, yy + P.SIDE_PLATE_T, bt, rz1), "alu", fab=True, mat="Plate 6 5052"))
    for yy in (ya + 30, yb - 70):   # UHMW stops: stowed carriage rests on these, road shock bypasses the runners
        parts.append(part(f"{nm}_uhmw_stop_{int(yy)}", g, box(x1 - 120, x1 - 20, yy, yy + 40, bt, bt + 5), "uhmw", fab=True, mat="UHMW 10"))
    # ------------------------------------------------ runners (3-member, 100 % extension, lock in + out)
    third = P.RUNNER_T / 3
    for lab, y_face, dirn in (("a", ya + P.SIDE_PLATE_T, 1), ("b", yb - P.SIDE_PLATE_T, -1)):
        for k, off in enumerate((0, ext / 2, ext)):
            yy0 = y_face + dirn * k * third
            parts.append(part(f"{nm}_runner_{lab}_{k}", g, box(x0 + 3 + off, x0 + 3 + P.RUNNER_LEN + off, yy0, yy0 + dirn * third,
                                                                rz0 + 3, rz1 - 3), "runner", kg=2.1))
    # ------------------------------------------------ carriage
    cy0, cy1 = carriage_extent(side)
    cx0, cx1 = x0 + ext, x1 + ext
    zlip = P.DECK_BOT_Z - P.LIP_T
    zb, top = P.DECK_BOT_Z, P.DECK_TOP_Z
    yc = (ya + yb) / 2
    for i, (yy, edge, dirn) in enumerate(((cy0, ya, -1), (cy1 - 25, yb, 1))):
        parts.append(part(f"{nm}_carr_side_{i}", g, tube_box(cx0, cx1, yy, yy + 25, rz0 + 6, zlip, axis="X"), "alu", fab=True,
                          mat="RHS 75x25x2 6060"))
        # L-angle: vertical leg on the inner face of the side member, top leg reaching out over the runner to the deck edge
        yin = yy + 25 if i == 0 else yy
        leg_v = box(cx0, cx1, yin, yin - dirn * 3, zb - 40, zb)
        leg_h = box(cx0, cx1, yin - dirn * 3, edge, zlip, zb)
        parts.append(part(f"{nm}_deck_angle_{i}", g, leg_v.union(leg_h), "alu", fab=True, mat="Angle 60x40x3 6060"))
    well = None
    if power:
        wx0 = cx0 + P.BULKHEAD_D
        wx1 = wx0 + P.FRIDGE_WELL_L
        well = ((wx0, wx1), (cy0 + 28, cy1 - 28))
    n_cross = 5
    for i in range(n_cross):
        xx = cx0 + 10 + i * (P.SLIDE_L - 70) / (n_cross - 1)
        if well and well[0][0] - 50 < xx < well[0][1]:
            continue
        parts.append(part(f"{nm}_carr_cross_{i}", g, tube_box(xx, xx + 50, cy0 + 28, cy1 - 28, zb - 25, zb, axis="Y"),
                          "alu", fab=True, mat="RHS 50x25x2 6060"))
    # covered deck: full width of the slide (over the runners), minus the fridge well and the L-track channel
    deck = box(cx0, cx1 - 3, ya, yb, zb, top)
    if well:
        (wx0, wx1), (wy0, wy1) = well
        deck = deck.cut(box(wx0, wx1, wy0, wy1, zb - 1, top + 1))
    tx0 = well[0][1] if well else cx0
    deck = deck.cut(box(tx0 - 1, cx1 + 1, yc - P.LTRACK_W / 2, yc + P.LTRACK_W / 2, top - P.LTRACK_H, top + 1))
    parts.append(part(f"{nm}_deck", g, deck, "ply", fab=True, mat="Ply 15 marine"))
    parts.append(part(f"{nm}_edge_cap", g, union_all([box(cx0, cx1, ya - 2, ya, zlip, top), box(cx0, cx1, yb, yb + 2, zlip, top)]),
                      "alu", fab=True, mat="Angle 30x30x3 6060"))
    track = box(tx0 + 15, cx1 - 15, yc - P.LTRACK_W / 2, yc + P.LTRACK_W / 2, top - P.LTRACK_H, top)
    track = track.cut(box(tx0 + 10, cx1 - 10, yc - 6, yc + 6, top - 6, top + 1))
    parts.append(part(f"{nm}_ltrack", g, track, "ltrack", fab=True, mat="L-track HD"))
    holes = union_all(cyl(6, 3, (tx0 + 30 + i * 25.4, yc, top - 0.5)) for i in range(int((cx1 - tx0 - 60) / 25.4)))
    parts.append(part(f"{nm}_ltrack_pockets", g, holes, "hole"))
    pts = grid_positions(cx0, cx1, ya, yb, power)
    if well:
        (wx0, wx1), (wy0, wy1) = well
        in_well = [(x, y) for x, y in pts if wx0 < x < wx1 and wy0 < y < wy1]
        pts = [q for q in pts if q not in in_well]
    parts += _receiver_parts(nm, g, pts, top)
    if power:
        (wx0, wx1), (wy0, wy1) = well
        zf = P.FRIDGE_WELL_Z
        pan = (box(wx0, wx1, wy0, wy1, zf - 3, zf)
               .union(box(wx0, wx0 + 3, wy0, wy1, zf - 3, zb))
               .union(box(wx1 - 3, wx1, wy0, wy1, zf - 3, zb))
               .union(box(wx0, wx1, wy0, wy0 + 3, zf - 3, zb))
               .union(box(wx0, wx1, wy1 - 3, wy1, zf - 3, zb)))
        parts.append(part(f"{nm}_fridge_well_pan", g, pan, "alu", fab=True, mat="Plate 3 5052"))
        for yy in (wy0 + 20, wy1 - 50):      # tie-down L-track on the pan floor for the fridge straps
            parts.append(part(f"{nm}_well_track_{int(yy)}", g, box(wx0 + 30, wx1 - 30, yy, yy + 30, zf, zf + 10), "ltrack",
                              fab=True, mat="L-track HD"))
        # removable well filler: 15 mm ply panel on two 18 mm ply risers that stud into the pan L-tracks,
        # flush with the deck and carrying the same receiver grid + L-track (fridge out = full flat slide)
        fg = "well_filler"
        fz0 = zf + 10                                    # top of the pan L-tracks
        parts.append(part(f"{nm}_filler_panel", fg, box(wx0 + 4, wx1 - 4, wy0 + 4, wy1 - 4, zb, top).cut(
            box(wx0, wx1, yc - P.LTRACK_W / 2, yc + P.LTRACK_W / 2, top - P.LTRACK_H, top + 1)), "ply", fab=True, mat="Ply 15 marine"))
        for k, yy in enumerate((wy0 + 26, wy1 - 44)):
            parts.append(part(f"{nm}_filler_riser_{k}", fg, box(wx0 + 30, wx1 - 30, yy, yy + 18, fz0, zb), "ply_edge", fab=True, mat="Ply 18 marine"))
        ftrack = box(wx0 + 15, wx1 - 15, yc - P.LTRACK_W / 2, yc + P.LTRACK_W / 2, top - P.LTRACK_H, top).cut(
            box(wx0 + 10, wx1 - 10, yc - 6, yc + 6, top - 6, top + 1))
        parts.append(part(f"{nm}_filler_ltrack", fg, ftrack, "ltrack", fab=True, mat="L-track HD"))
        parts += _receiver_parts(f"{nm}_filler", fg, in_well, top)
        # power pod at the very front: sockets face UP so plugs never foul the fridge
        pw0, pw1 = ya + 20, yb - 20
        pz = top + 150
        parts.append(part(f"{nm}_power_pod", g, box(cx0 + 2, cx0 + P.BULKHEAD_D, pw0, pw1, top, pz), "alu_dark", fab=True, mat="Plate 3 5052"))
        px = cx0 + 8
        parts.append(part(f"{nm}_gpo", g, box(px, px + 58, pw0 + 12, pw0 + 128, pz - 2, pz + 8), "outlet", kg=0.4))
        parts.append(part(f"{nm}_anderson", g, box(px + 4, px + 54, pw0 + 145, pw0 + 205, pz - 2, pz + 10), "anderson", kg=0.1))
        parts.append(part(f"{nm}_12v", g, cyl(17, 10, (px + 29, pw0 + 245, pz + 3)), "usb", kg=0.05))
        parts.append(part(f"{nm}_usbc", g, cyl(15, 10, (px + 29, pw0 + 300, pz + 3)), "usb", kg=0.05))
        parts.append(part(f"{nm}_usbc_2", g, cyl(15, 10, (px + 29, pw0 + 345, pz + 3)), "usb", kg=0.05))
        anchor("slide_bulkhead", (cx0 + 25, ya + 10, top + 20))
    # rear face + recessed pull / lock release
    rear = box(cx1 - 3, cx1, cy0, cy1, rz0 + 6, zlip).union(box(cx1 - 3, cx1, ya, yb, zlip, top))   # clears the fixed runner plates
    parts.append(part(f"{nm}_rear_plate", g, rear, "alu", fab=True, mat="Plate 3 5052"))
    parts.append(part(f"{nm}_handle", g, box(cx1 - 3.5, cx1 + 1, yc - 120, yc + 120, rz0 + 20, rz0 + 50).cut(
        box(cx1 - 4, cx1 + 2, yc - 105, yc + 105, rz0 + 26, rz0 + 44)), "alu_dark", kg=0.3))
    # removable pin-in legs at the rear corners (camp mode)
    if ext > 0:
        zg = -P.FLOOR_ABOVE_GROUND
        for i, yy in enumerate((cy0 + P.LEG_INSET, cy1 - P.LEG_INSET - 30)):
            leg = tube_box(cx1 - 70, cx1 - 40, yy, yy + 30, zg, rz0 + 5, axis="Z").union(box(cx1 - 85, cx1 - 25, yy - 15, yy + 45, zg, zg + 6))
            parts.append(part(f"{nm}_leg_{i}", g, leg, "alu_dark", fab=True, mat="SHS 30x30x2 6060"))
    if power:
        parts += cable_chain(x0, cx0, ya)
    return parts


def cable_chain(x0, cx0, ya):
    """Upright chain in the lane on the power slide's outboard side; upper run fixed to the deck edge."""
    R, h, w = P.CHAIN_R, P.CHAIN_H, P.CHAIN_W
    xf = x0 + P.SLIDE_EXT / 2 + 40                       # fixed end at mid travel
    xm = cx0 + 120                                      # moving end (bracket on the deck edge)
    xb_min = x0 + 30 + R + h / 2
    lc = (xf + (x0 + 120) - 2 * xb_min) + 3.14159 * R
    xb = (xf + xm - lc + 3.14159 * R) / 2
    yl1 = ya - 5
    yl0 = yl1 - w
    zc = 3 + R + h / 2
    lower = box(xb, xf, yl0, yl1, 3, 3 + h)
    upper = box(xb, xm, yl0, yl1, 3 + 2 * R, 3 + 2 * R + h)
    bend = (cq.Workplane("XZ", origin=(0, yl1, 0)).center(xb, zc).circle(R + h / 2).circle(R - h / 2).extrude(w)
            .cut(box(xb, xb + R + h, yl0 - 1, yl1 + 1, -1, 2 * R + h + 5)))
    parts = [part("slide_power_cable_chain", "slide_p", lower.union(upper).union(bend), "chain", kg=1.4, chain_length_mm=round(lc))]
    parts.append(part("slide_power_chain_bracket", "slide_p", box(xm - 30, xm + 30, yl0, ya - 2, P.DECK_BOT_Z, 3 + 2 * R + h + 8), "alu_dark",
                      fab=True, mat="Plate 3 5052"))
    parts.append(part("slide_power_chain_trough", "slide_p", box(x0 + 10, xf + 40, yl0 - 3, yl1 + 2, 0, 3), "uhmw", fab=True, mat="UHMW 10"))
    anchor("chain_fixed", (xf, (yl0 + yl1) / 2, h / 2))
    anchor("chain_moving", (xm, (yl0 + yl1) / 2, 2 * R + h / 2))
    return parts


def slides(ext_p, ext_d):
    return slide("p", ext_p, power=True) + slide("d", ext_d, power=False)
