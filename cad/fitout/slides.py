"""
Under-mount slide-out platforms (v0.4).

Each slide = fixed cassette on the tub floor (base bars + cross ties + a row of sealed rollers on the rear
cross member) + a deck carried on flat-mounted telescopic rails underneath it. Deck height is just
base + rail thickness + ply. The two decks sit side by side with a 6 mm gap, so modules on the two
slides can butt against each other. The power slide gives up a lane on its outboard edge for an upright
cable chain and carries a power pod (sockets facing up) at its front.
"""
import cadquery as cq

import params as P

from .core import anchor, box, cyl, part, ring, tube_box, union_all


def _receivers(nm, g, cx0, cx1, cy0, cy1, yc, top):
    pitch = P.RECEIVER_PITCH
    ny = int((cy1 - cy0 - 80) // pitch)
    nx = int((cx1 - cx0 - 80) // pitch)
    gx0 = cx0 + ((cx1 - cx0) - nx * pitch) / 2
    recs, bores = [], []
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = gx0 + i * pitch
            y = yc - ny * pitch / 2 + j * pitch
            if abs(y - yc) < 45:
                continue
            recs.append(ring(P.RECEIVER_D / 2, 4.2, 2.2, (x, y, top - 1)))
            bores.append(cyl(4.2, 2.4, (x, y, top - 1)))
    return [part(f"{nm}_receivers", g, union_all(recs), "receiver", kg=0.03 * len(recs), n_receivers=len(recs)),
            part(f"{nm}_receiver_bores", g, union_all(bores), "hole")]


def slide_extent(side):
    """Y extents of the deck for a slide: (y_low, y_high)."""
    gap = P.SLIDE_GAP_MID / 2
    edge = P.ARCH_GAP / 2 - 3
    if side == "p":
        return -(edge - P.CHAIN_LANE), -gap
    return gap, edge


def slide(side: str, ext: float, power: bool):
    parts = []
    g = f"slide_{side}"
    nm = "slide_power" if power else "slide_driver"
    ya, yb = slide_extent(side)
    x0, x1 = P.SLIDE_X0, P.SLIDE_X0 + P.SLIDE_L
    bt = P.BASE_T
    rw, rh = P.UM_RAIL
    # rail centre lines across the deck
    n = P.UM_RAILS
    inset = rw / 2 + 25
    ys = [ya + inset + i * (yb - ya - 2 * inset) / (n - 1) for i in range(n)]
    # ------------------------------------------------ fixed cassette
    for i, y in enumerate(ys):   # base bars under each rail (bolt through the floor with spreader plates)
        parts.append(part(f"{nm}_base_bar_{i}", g, box(x0, x1, y - 30, y + 30, 0, bt), "alu", fab=True, mat="Flat 60x6 6060"))
    for i, xx in enumerate((x0 + 10, (x0 + x1) / 2 - 25)):
        parts.append(part(f"{nm}_base_tie_{i}", g, box(xx, xx + 50, ya + 10, yb - 10, 0, bt), "alu", fab=True, mat="Flat 50x6 6060"))
    # rear cross member with sealed rollers: the deck rides on these at the tub edge as it slides out
    rx = x1 - 40
    rys = [(ys[i] + ys[i + 1]) / 2 for i in range(n - 1)]
    zr = bt + rh + 1 - 11                       # roller (608-size bearing, 22 OD) top kisses the deck underside
    for k, y in enumerate(rys):   # roller + twin cheek brackets bolted to the floor in the gaps between rails
        parts.append(part(f"{nm}_roller_{k}", g, cyl(11, 24, (rx, y, zr), "Y"), "uhmw", kg=0.1))
        cheeks = box(rx - 20, rx + 20, y - 18, y - 13, 0, zr + 6).union(box(rx - 20, rx + 20, y + 13, y + 18, 0, zr + 6))
        parts.append(part(f"{nm}_roller_bracket_{k}", g, cheeks, "alu", fab=True, mat="Flat 50x6 6060"))
    # ------------------------------------------------ flat telescopic rails (fixed / intermediate / moving)
    for i, y in enumerate(ys):
        for k, off in enumerate((0, ext / 2, ext)):
            w = rw - k * 8
            parts.append(part(f"{nm}_rail_{i}_{k}", g, box(x0 + 3 + off, x0 + 3 + P.UM_RAIL_LEN + off, y - w / 2, y + w / 2,
                                                            bt + k * rh / 3, bt + (k + 1) * rh / 3), "runner", kg=P.UM_RAIL_KG / 3))
    # ------------------------------------------------ deck (moves with ext)
    cx0, cx1 = x0 + ext, x1 + ext
    z0 = bt + rh + 1
    top = z0 + P.DECK_T
    yc = (ya + yb) / 2
    deck = box(cx0, cx1, ya, yb, z0, top)
    deck = deck.cut(box(cx0 - 1, cx1 + 1, yc - P.LTRACK_W / 2, yc + P.LTRACK_W / 2, top - P.LTRACK_H, top + 1))
    parts.append(part(f"{nm}_deck", g, deck, "ply", fab=True, mat="Ply 18 marine"))
    # aluminium edge capping (protects the ply edges, stiffens the deck)
    cap = union_all([box(cx0, cx1, ya - 2, ya, z0 - 4, top), box(cx0, cx1, yb, yb + 2, z0 - 4, top),
                     box(cx1, cx1 + 3, ya - 2, yb + 2, z0 - 4, top)])
    parts.append(part(f"{nm}_edge_cap", g, cap, "alu", fab=True, mat="Angle 30x30x3 6060"))
    # wear strip on the deck underside where it rides on the rollers
    parts.append(part(f"{nm}_wear_strip", g, box(cx0 + 20, cx1 - 20, ya + 5, yb - 5, z0 - 1, z0), "alu_dark", fab=True, mat="Sheet 1.6 5005"))
    track = box(cx0 + 15, cx1 - 15, yc - P.LTRACK_W / 2, yc + P.LTRACK_W / 2, top - P.LTRACK_H, top)
    track = track.cut(box(cx0 + 10, cx1 - 10, yc - 6, yc + 6, top - 6, top + 1))
    parts.append(part(f"{nm}_ltrack", g, track, "ltrack", fab=True, mat="L-track HD"))
    holes = union_all(cyl(6, 3, (cx0 + 30 + i * 25.4, yc, top - 0.5)) for i in range(int((P.SLIDE_L - 60) / 25.4)))
    parts.append(part(f"{nm}_ltrack_pockets", g, holes, "hole"))
    rx0 = cx0 + (P.BULKHEAD_D if power else 0)
    parts += _receivers(nm, g, rx0, cx1, ya, yb, yc, top)
    # flush pull + lock release on the rear edge
    parts.append(part(f"{nm}_handle", g, box(cx1 + 1, cx1 + 6, yc - 120, yc + 120, z0 + 2, top - 2), "alu_dark", kg=0.3))
    # removable pin-in legs at the rear corners (camp mode)
    if ext > 0:
        zg = -P.FLOOR_ABOVE_GROUND
        for i, yy in enumerate((ya + P.LEG_INSET, yb - P.LEG_INSET - 30)):
            leg = tube_box(cx1 - 70, cx1 - 40, yy, yy + 30, zg, z0, axis="Z").union(box(cx1 - 85, cx1 - 25, yy - 15, yy + 45, zg, zg + 6))
            parts.append(part(f"{nm}_leg_{i}", g, leg, "alu_dark", fab=True, mat="SHS 30x30x2 6060"))
    if power:
        # power pod at the front: sockets face UP so plugs never foul whatever sits behind it
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
        parts += cable_chain(x0, cx0, ya)
    return parts


def cable_chain(x0, cx0, ya):
    """Upright chain in the lane on the power slide's outboard edge: lower run on the floor, upper run on the deck edge."""
    R, h, w = P.CHAIN_R, P.CHAIN_H, P.CHAIN_W
    xf = x0 + P.SLIDE_EXT / 2 + 40                       # fixed end at mid travel
    xm = cx0 + 110                                      # moving end (on the deck edge)
    lc = (xf + (x0 + 110) - 2 * (x0 + 72)) + 3.14159 * R
    xb = (xf + xm - lc + 3.14159 * R) / 2
    yl1 = ya - 3
    yl0 = yl1 - w
    zc = 3 + R + h / 2
    lower = box(xb, xf, yl0, yl1, 3, 3 + h)
    upper = box(xb, xm, yl0, yl1, 3 + 2 * R, 3 + 2 * R + h)
    bend = (cq.Workplane("XZ", origin=(0, yl1, 0)).center(xb, zc).circle(R + h / 2).circle(R - h / 2).extrude(w)
            .cut(box(xb, xb + R + h, yl0 - 1, yl1 + 1, -1, 2 * R + h + 5)))
    parts = [part("slide_power_cable_chain", "slide_p", lower.union(upper).union(bend), "chain", kg=1.2, chain_length_mm=round(lc))]
    parts.append(part("slide_power_chain_bracket", "slide_p", box(xm - 30, xm + 30, yl0, ya + 25, P.DECK_TOP_Z, 3 + 2 * R + h + 8), "alu_dark",
                      fab=True, mat="Plate 3 5052"))
    parts.append(part("slide_power_chain_trough", "slide_p", box(x0 + 10, xf + 40, yl0 - 4, yl1 + 2, 0, 3), "uhmw", fab=True, mat="UHMW 10"))
    anchor("chain_fixed", (xf, (yl0 + yl1) / 2, h / 2))
    anchor("chain_moving", (xm, (yl0 + yl1) / 2, 2 * R + h / 2))
    return parts


def slides(ext_p, ext_d):
    return slide("p", ext_p, power=True) + slide("d", ext_d, power=False)
