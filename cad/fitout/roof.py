"""Roof platform: recessed solar, Starlink Mini inside the frame, removable cargo bars, flush light bar."""
import params as P

from .core import anchor, box, part, tube_box


def roof(cargo=True):
    parts = []
    g = "roof"
    x0, x1 = P.PLAT_X0, P.PLAT_X0 + P.PLAT_L
    hw = P.PLAT_W / 2
    z0, z1 = P.PLAT_Z, P.PLAT_Z + P.PLAT_T
    e = 40
    for yy in (-hw, hw - e):
        parts.append(part(f"plat_side_{int(yy)}", g, tube_box(x0, x1, yy, yy + e, z0, z1, axis="X"), "trim", kg=9.0))  # incl. share of slats/brackets (est)
    for xx in (x0, x1 - e):
        parts.append(part(f"plat_end_{int(xx)}", g, tube_box(xx, xx + e, -hw + e, hw - e, z0, z1, axis="Y"), "trim", kg=2.5))
    # centre spine between the two panel bays
    parts.append(part("plat_spine", g, tube_box(x0 + e, x1 - e, -15, 15, z0, z1, axis="X"), "trim", kg=2.0))
    # front fairing + flush light bar
    parts.append(part("plat_fairing", g, box(x0 - 90, x0, -hw, hw, z0 - 12, z1 + 8).edges("|Y").edges("<X").fillet(20), "trim", kg=2.5))
    parts.append(part("light_bar", g, box(x0 - 92, x0 - 84, -510, 510, z0 + 4, z1 - 2), "light", kg=3.0))
    # mounts to the factory roof points
    for xx in (x0 + 220, x1 - 260):
        for s in (1, -1):
            parts.append(part(f"plat_mount_{int(xx)}_{s}", g, box(xx, xx + 50, s * 600, s * 660, P.ROOF_Z, z0), "trim", kg=0.8))
    # recessed panels (on brackets inside the frame)
    zp = z0 + 2
    la, wa, ta = P.ROOF_PANEL_A
    parts.append(part("roof_solar_190w", "solar", box(x0 + e + 10, x0 + e + 10 + la, 16, 16 + wa, zp, zp + ta), "solar", kg=10.5, watts=190))
    lb, wb, tb = P.ROOF_PANEL_B
    parts.append(part("roof_solar_130w", "solar", box(x0 + e + 10, x0 + e + 10 + lb, -16 - wb, -16, zp, zp + tb), "solar", kg=7.1, watts=130))
    # Starlink Mini in the pocket behind panel B (passenger rear), low bracket, top just above the frame
    sl, sw, sh = P.STARLINK_MINI
    sx0 = x1 - e - 15 - sw
    parts.append(part("starlink_bracket", g, box(sx0 - 10, sx0 + sw + 10, -hw + e + 20, -40, z0 + 2, z0 + 8), "alu_dark", fab=True, mat="Plate 4 5052"))
    parts.append(part("starlink_mini", g, box(sx0, sx0 + sw, -16 - wb / 2 - sl / 2, -16 - wb / 2 + sl / 2, z0 + 8, z0 + 8 + sh),
                      "starlink", kg=1.16))
    anchor("starlink", (sx0 + sw / 2, -16 - wb / 2, z0 + 8))
    anchor("roof_pv", (x1 - e - 20, 0, z0 + 10))
    anchor("roof_drop", (P.CAB_REAR_X + 5, -560, P.ROOF_Z - 40))
    if cargo:
        for xx in (x0 + 260, x0 + 1050):
            for s in (1, -1):
                parts.append(part(f"cargo_riser_{int(xx)}_{s}", "cargo", box(xx, xx + 50, s * (hw - e), s * hw, z1, z1 + P.CARGO_BAR_Z), "alu_dark", kg=0.6))
            parts.append(part(f"cargo_bar_{int(xx)}", "cargo", box(xx - 10, xx + 60, -hw - 60, hw + 60, z1 + P.CARGO_BAR_Z, z1 + P.CARGO_BAR_Z + 30)
                              .edges("|Y").fillet(8), "trim", kg=3.0))
    return parts
