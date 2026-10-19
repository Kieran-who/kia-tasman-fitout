"""
Front battery + inverter bay (between the wheel arches, against the front wall).

Layout across the tub (passenger -> driver):
    [MultiPlus-II 12/3000 flat] [distribution column] [battery 1 on end] [battery 2 on end]
    + charging board (Orion XS, 2 x MPPT) on the front wall ABOVE the inverter, ~140 mm air gap.

Battery bank (optimal for 2 x iTech400X Pro in parallel):
    each battery + -> MRBF 300 A on the terminal -> equal-length 70 mm2 -> bank + busbar
    each battery - -> equal-length 70 mm2 -> bank - busbar -> SmartShunt -> system - busbar
    bank + -> ML-RBS 500 A remote battery switch (controlled from the rear panel) -> system + busbar
    system + -> Class-T 400 A -> 2 x 50 mm2 -> MultiPlus-II ; MIDI fuses -> Orion / MPPTs / rear DC fuse block

v0.8 detail pass: every purchased component is modelled on its published drawing / photos (sources inline).
Sub-features (terminals, covers, glands, studs, lugs) are separate parts with NO mass and NO material, so
the purchased masses (kg=) and the cut list are unchanged; only the main part of each component carries kg.
"""
import math

import cadquery as cq
import params as P

from .core import C, anchor, box, part, tube_box

# ====================================================================== real-product dimensions (mm)
# The params.py envelopes stay the source of the layout; these module-local figures shape the detail inside them.
# MultiPlus-II 12/3000/120-32 230V: Victron datasheet "Dimensions (hxwxd) 546 x 275 x 147 mm", "Weight 19 kg"
#   https://www.victronenergy.com/upload/documents/Datasheet-MultiPlus-II-inverter-charger-EN.pdf  [PUB]
#   -> envelope matches P.INVERTER; the published mass is 19 kg (P.INVERTER_KG = 20 kept, see report).
#   Connection-area layout (AC blocks left, VE.Bus/aux centre, DC +/- right, seen from the front, cables up
#   through the bottom face) from the datasheet photo "Connection Area MultiPlus-II 3k".  [PUB photo / EST mm]
MP2_CONN_U = 438       # [EST] start of the connection compartment from the top (hanging-bracket) end
MP2_CAP_U = 492        # [EST] black bottom cap (cable entries) from here to the end
# Orion XS 12/12-50A: Victron dimension drawing ORI121217040: 123.1 w x 137.3 h x 40 d, holes 4 x 4.3 on
#   109.3 x 113.0; IN / GND / OUT cable entries under a black cover, remote H/L plug left, VE.Direct right [PUB]
#   https://www.victronenergy.com/media/pg/Orion_XS_12-12-50A_DC-DC_battery_charger/en/technical-data.html
ORION = (123.1, 40.0, 137.3)
# SmartSolar MPPT 100/30: datasheet "Dimensions (h x w x d) 130 x 186 x 70 mm" -> 186 WIDE x 130 TALL [PUB]
#   (P.MPPT_ROOF = (130, 70, 186) has width/height swapped: modelled at the published 186 w x 130 h)
#   https://www.victronenergy.com/upload/documents/Datasheet-SmartSolar-charge-controller-MPPT-100-30-&-100-50-EN.pdf
MPPT_100_30 = (186.0, 70.0, 130.0)
# SmartSolar MPPT 75/15: datasheet "100 x 113 x 40 mm" (h x w x d); terminals BATT+ BATT- PV- PV+ LOAD- LOAD+ [PUB]
#   https://www.victronenergy.com/upload/documents/Datasheet-SmartSolar-charge-controller-MPPT-75-10,-75-15,-100-15,-100-20-EN.pdf
MPPT_75_15 = (113.0, 40.0, 100.0)
CHARGE_GAP = 30        # [DES] gap between the charging-board units (was 25; the 100/30 is wider than modelled before)
# iTech400X Pro: 525 x 240 x 220 (235 incl. terminals), 38 kg; BOTH M8 terminals at one end of the orange lid,
#   ~47 mm from the end, ~50 mm in from each long edge; black handle lugs on both ends [PUB photos]
#   https://itechworld.com.au/products/12v-400ah-lithium-battery-with-bluetooth-itech400x-pro
BATT_TERM_IN = 47      # [EST from photo] terminal centre from the (top) end
BATT_TERM_EDGE = 50    # [EST from photo] terminal centre from the long edge
BATT_LID = 20          # [EST] orange lid depth
BATT_LUG = 8           # [EST] handle lugs stand proud of each end
# Blue Sea 5191 MRBF terminal fuse block: 60.9 L x 44.5 W x 20 T (excl. cap), M10 hole on the battery post,
#   M8 output stud [retailer spec, 12voltplanet / Current Connected]
MRBF_5191 = (61.0, 44.5, 20.0)
# Blue Sea 2104 PowerBar 600 A: 7.000" x 2.000" x 1.980" (177.8 x 51 x 50.8), 4 x 3/8"-16 studs, mounting holes
#   6.25" (158.75) c/c [retailer spec: powerwerx / philippi-online]  (P.BUSBAR = 200 x 50 x 45 is the envelope)
POWERBAR = (177.8, 51.0, 50.8)
POWERBAR_PITCH = 38    # [EST] stud pitch (not published in text)
# Blue Sea 7713 ML-RBS: owner's manual drawing 138.94 x 95.25 x 51.56, holes 76.2 x 114.3, studs 3/8"-16
#   48.26 c/c, 26.16 above the base, studs + harness exit the bottom end [PUB]
#   https://productimageserver.com/literature/ownersManual/53464OM.pdf
RBS_7713 = (138.94, 95.25, 51.56)
# Blue Sea 5502 Class-T block: ~7.0 x 2.0 x 2.3 in (178 x 51 x 58) [retailer spec]; stud c/c [EST]
CLASS_T_5502 = (178.0, 51.0, 58.0)
CLASS_T_STUDS = 82     # [EST]
# Victron SmartShunt 500 A: datasheet "46 x 120 x 54 mm" (h x w x d), M10 bolts [PUB]
#   https://www.victronenergy.com/upload/documents/Datasheet-SmartShunt-EN.pdf
# Blue Sea 5151 MIDI/AMI fuse block (and a MEGA holder of the same footprint): ~72 x 32 x 32 [EST]
MIDI_BLOCK = (72.0, 32.0, 32.0)
FAN = (92.0, 25.0)     # [PUB] generic 92 mm 12 V fan, 92 x 92 x 25

# ====================================================================== colours (RGBA)
BLUE = C["victron"]
HS_BLACK = (34, 36, 40, 255)        # anodised heatsinks / MultiPlus base
CAP_BLACK = (22, 22, 24, 255)       # black plastics
DARK_GREY = (55, 58, 62, 255)       # ML-RBS body
TERM_GREY = (205, 205, 198, 255)    # terminal blocks / nylon glands
TERM_GREEN = (40, 160, 80, 255)
TERM_BLUE = (35, 110, 205, 255)
TIN = (200, 200, 194, 255)          # tinned copper, studs, nuts
STEEL = (150, 153, 157, 255)
BRASS = (196, 156, 72, 255)
MANGANIN = (160, 112, 60, 255)
ORANGE = (240, 112, 24, 255)        # Victron label stripe / iTech lid
RED_BOOT = (190, 32, 32, 255)
BLACK_BOOT = (28, 28, 30, 255)
YELLOW = (238, 192, 24, 255)
WINDOW = (150, 156, 162, 255)
FIBRE = (205, 182, 132, 255)        # Class-T fuse tube
MIDI_FUSE = (226, 96, 28, 255)
CLEAR = (215, 220, 225, 80)         # clear fuse-holder covers
CONN_COVER = (0, 92, 170, 70)       # MultiPlus connection-area cover, shown see-through
GUARD = (110, 115, 120, 150)        # slotted rear guard

DIST_WINDOW_Z = 108       # [DES] top of the cable window in the distribution board (clears the MultiPlus entries)

# intra-component contacts (sub-parts sit on / in their own body) and genuine mounting contacts
CLASH_ALLOW = [("dist_board_window_trim", "dist_board"), ("busbar_sys_neg", "bay_base_tray"),
    ("inverter_charger_multiplus2_3000", "inverter_charger_multiplus2_3000"),
    ("orion_xs_50a", "orion_xs_50a"), ("mppt_roof_100_30", "mppt_roof_100_30"), ("mppt_tent_75_15", "mppt_tent_75_15"),
    ("busbar_bank_pos", "busbar_bank_pos"), ("busbar_bank_neg", "busbar_bank_neg"),
    ("busbar_sys_pos", "busbar_sys_pos"), ("busbar_sys_neg", "busbar_sys_neg"),
    ("remote_battery_switch_500a", "remote_battery_switch_500a"), ("class_t_400a", "class_t_400a"),
    ("smartshunt_500a", "smartshunt_500a"), ("fuse_holders_midi", "fuse_holders_midi"),
    ("fuse_link_strap", "fuse_holders_midi"), ("fuse_link_strap", "busbar_sys_pos"),
    ("inverter_fan", "bay_fan_bracket"), ("lugs_dc", "lugs_dc"), ("lugs_batt", "lugs_batt"),
]

_AX = {"X": 0, "Y": 1, "Z": 2}


# ====================================================================== geometry helpers
def _orient(w, axis):
    if axis == "X":
        return w.rotate((0, 0, 0), (0, 1, 0), 90)
    if axis == "Y":
        return w.rotate((0, 0, 0), (1, 0, 0), 90)
    return w


def hexp(af, h, centre, axis="Z"):
    """Hex prism (nut / bolt head) with across-flats `af`."""
    w = cq.Workplane("XY").polygon(6, af / math.cos(math.pi / 6)).extrude(h).translate((0, 0, -h / 2))
    return _orient(w, axis).translate(centre)


def pcyl(r, h, centre, axis="Z", n=12):
    """Low-poly cylinder (n-gon prism): small round features cost a fraction of a true cylinder in the GLB."""
    w = cq.Workplane("XY").polygon(n, 2 * r).extrude(h).translate((0, 0, -h / 2))
    return _orient(w, axis).translate(centre)


def pring(ro, ri, h, centre, axis="Z", n=12):
    return pcyl(ro, h, centre, axis, n).cut(pcyl(ri, h + 2, centre, axis, max(6, n - 4)))


def soft(w, sel, r, round_=False):
    """Soften edges: chamfer by default (flat faces keep the GLB small), fillet when round_; safe fallback."""
    try:
        e = w.edges(sel)
        out = e.fillet(r) if round_ else e.chamfer(r * 0.6)
        return out if out.val().isValid() else w
    except Exception:
        return w


def grp(*items):
    """Compound of solids (no boolean union: fast, and fine for display / bbox / clash)."""
    sol = []

    def add(x):
        if x is None:
            return
        if isinstance(x, (list, tuple)):
            for y in x:
                add(y)
        elif isinstance(x, cq.Workplane):
            sol.extend(v for v in x.vals() if isinstance(v, cq.Shape))
        else:
            sol.append(x)
    add(items)
    return cq.Compound.makeCompound(sol)


class Frame:
    """Local box frame: local axes (a, b, c) run along the global axes `axes` (positive), origin `o`."""

    def __init__(self, o, axes):
        self.o, self.names = o, axes
        self.ax = [_AX[a] for a in axes]

    def pt(self, a, b, c):
        g = list(self.o)
        for v, i in zip((a, b, c), self.ax):
            g[i] += v
        return tuple(g)

    def box(self, a0, a1, b0, b1, c0, c1):
        p, q = self.pt(a0, b0, c0), self.pt(a1, b1, c1)
        return box(p[0], q[0], p[1], q[1], p[2], q[2])

    def _ctr(self, k, lo, hi, p, q):
        loc = [0.0, 0.0, 0.0]
        o = [i for i in range(3) if i != k]
        loc[o[0]], loc[o[1]], loc[k] = p, q, (lo + hi) / 2
        return self.pt(*loc), abs(hi - lo), self.names[k]

    def cyl(self, r, k, lo, hi, p, q, n=8):
        """Cylinder (n-gon prism) along local axis k (0=a, 1=b, 2=c) from lo to hi; (p, q) = the other two local coords."""
        c, h, ax = self._ctr(k, lo, hi, p, q)
        return pcyl(r, h, c, ax, n)

    def ring(self, ro, ri, k, lo, hi, p, q, n=16):
        c, h, ax = self._ctr(k, lo, hi, p, q)
        return pring(ro, ri, h, c, ax, n)

    def hexp(self, af, k, lo, hi, p, q):
        c, h, ax = self._ctr(k, lo, hi, p, q)
        return hexp(af, h, c, ax)


class Lugs:
    """Tinned ring lugs + coloured heat-shrink boots on the studs where cables land (decorative, no mass)."""

    def __init__(self, prefix="lugs_dc", group="electrical"):
        self.prefix, self.group = prefix, group
        self.tin, self.pos, self.neg = [], [], []

    def add(self, centre, axis, d, pol, r_stud=4.8, size=1.0, ln=1.0):
        """centre = lug ring centre on the stud; axis = the stud's outward direction ('+Y' = stud points +Y);
        d = barrel direction ('+X' / '-Z' ...). The crimp barrel is offset outward, off the mounting surface."""
        sgn, da = (1 if d[0] == "+" else -1), d[1]
        asg, an = (1 if axis[0] == "+" else -1), axis[1]
        i, j = _AX[da], _AX[an]
        ro = 11 * size
        self.tin.append(pring(ro, r_stud + 0.5, 3, centre, an, 8))
        L0, L1, L2 = ro - 1, ro + 14 * ln, ro + 30 * ln       # tongue end, barrel end, boot end
        lift = 4 * size

        def at(s, up=0.0):
            p = list(centre)
            p[i] += sgn * s
            p[j] += asg * up
            return tuple(p)
        # tongue (flat, in the ring plane) + crimp barrel + boot, along the barrel direction
        tw = [0, 0, 0]
        tw[i] = L0 + 2
        tw[j] = 3
        other = [k for k in range(3) if k not in (i, j)][0]
        tw[other] = 15 * size
        c = at(L0 / 2 + 1)
        self.tin.append(box(c[0] - tw[0] / 2, c[0] + tw[0] / 2, c[1] - tw[1] / 2, c[1] + tw[1] / 2, c[2] - tw[2] / 2, c[2] + tw[2] / 2))
        self.tin.append(pcyl(6.5 * size, L1 - L0 + 2, at((L0 + L1) / 2, lift), da, 8))
        (self.pos if pol == "+" else self.neg).append(pcyl(8 * size, L2 - L1 + 4, at((L1 + L2) / 2, lift), da, 10))

    def parts(self):
        out = []
        if self.tin:
            out.append(part(f"{self.prefix}_tinned", self.group, grp(self.tin), TIN))
        if self.pos:
            out.append(part(f"{self.prefix}_boots_pos", self.group, grp(self.pos), RED_BOOT))
        if self.neg:
            out.append(part(f"{self.prefix}_boots_neg", self.group, grp(self.neg), BLACK_BOOT))
        return out


# ====================================================================== components
def multiplus(parts, xq0, yq0, zq):
    """Victron MultiPlus-II 12/3000 lying on its back; connection (bottom) end toward +Y (the distribution column).
    Local frame: u = along the unit from the hanging-bracket end (Y), w = across (X), h = up from the back (Z).
    Seen from the front with the unit upright, AC is on the left and DC on the right -> lying here, DC is at LOW X
    (front-wall side) and AC at HIGH X."""
    L, D, H = P.INVERTER
    F = Frame((xq0, yq0, zq), ("Y", "X", "Z"))
    nm = "inverter_charger_multiplus2_3000"
    uc, ue = MP2_CONN_U, MP2_CAP_U
    # blue steel cover (front + sides), rounded front edges
    cover = soft(F.box(18, uc, 2, D - 2, 12, H - 1), "|Y and >Z", 9, True)
    parts.append(part(nm, "electrical", cover, BLUE, kg=P.INVERTER_KG))
    # dark steel back/base + top hanging bracket with keyholes + connection-compartment chassis with vent slots
    base = F.box(18, ue, 1, D - 1, 0, 12)
    brk = F.box(0, 20, 60, 215, 0, 3)
    for w in (85, 190):
        brk = brk.cut(F.cyl(5.5, 2, -1, 4, 9, w)).cut(F.box(9, 16, w - 2.5, w + 2.5, -1, 4))
    floor = F.box(uc, ue, 4, D - 4, 12, 62)
    slots = [F.box(441, 462, w, w + 5, 52, 63) for w in list(range(10, 106, 9)) + list(range(172, 266, 9))]
    floor = floor.cut(grp(slots))
    parts.append(part(f"{nm}_base", "electrical", grp(base, brk, floor), HS_BLACK))
    # black end caps (two top corner caps, full-width bottom cap with the cable entries), LED panel, grommets
    blk = [soft(F.box(0, 88, 0, 56, 0, H + 2), "|Z", 6), soft(F.box(0, 88, D - 56, D, 0, H + 2), "|Z", 6),
           soft(F.box(ue, L, 0, D, 0, H + 2), "|Z", 6),
           F.box(300, 360, 145, 250, H - 1, H + 0.6)]                                  # charger/inverter LED panel
    for w in (54, 91):                                                                # DC cable grommets
        blk.append(F.ring(14, 9, 0, L - 1, L + 4, w, 40))
    blk.append(F.box(L - 1, L + 3, 136, 176, 104, 116))                               # comms grommet (VE.Bus, remote)
    parts.append(part(f"{nm}_caps", "electrical", grp(blk), CAP_BLACK))
    parts.append(part(f"{nm}_stripe", "electrical", F.box(232, 246, 6, D - 6, H - 1, H - 0.2), ORANGE))
    parts.append(part(f"{nm}_labels", "electrical", grp(F.box(392, 428, 12, 140, H - 1, H - 0.4),     # warning label
                                                       F.box(262, 286, 150, 200, H - 1, H - 0.4)),     # model plate
                      (232, 234, 236, 255)))
    # connection compartment: AC terminal blocks (AC-in, AC-out-1, AC-out-2) + AC cable glands
    ac = []
    for w0 in (166, 197, 228):
        blkw = F.box(468, 490, w0, w0 + 28, 62, 80)
        for i in range(4):
            blkw = blkw.cut(F.box(477, 481, w0 + 1.5 + 7 * i, w0 + 5.5 + 7 * i, 75, 81))
        ac.append(blkw)
    for w in (180, 210, 240):                                                         # M20 nylon glands, bottom face
        ac += [F.hexp(22, 0, L - 1, L + 3, w, 80), F.cyl(9, 0, L + 3, L + 6, w, 80, 12)]
    parts.append(part(f"{nm}_ac_terminals", "electrical", grp(ac), TERM_GREY))
    parts.append(part(f"{nm}_aux_terminals", "electrical", F.box(444, 488, 116, 132, 62, 74), TERM_GREEN))
    parts.append(part(f"{nm}_remote_terminal", "electrical", F.box(476, 490, 156, 168, 62, 72), TERM_BLUE))
    # metal: VE.Bus RJ45 x 2 + temp-sense RJ12 stack, DC- stud on its bus pad, chassis-earth stud on the bottom face
    met = []
    for u0 in (446, 460, 474):
        met.append(F.box(u0, u0 + 12, 137, 153, 62, 76).cut(F.box(u0 + 2, u0 + 10, 140, 150, 70, 77)))
    met += [F.box(468, 490, 42, 66, 62, 66), F.cyl(4, 2, 66, 90, 479, 54), F.hexp(13, 2, 70, 77, 479, 54),
            F.cyl(3, 0, L - 1, L + 7, 22, 28), F.hexp(10, 0, L + 1, L + 5, 22, 28)]
    parts.append(part(f"{nm}_metal", "electrical", grp(met), TIN))
    parts.append(part(f"{nm}_dc_pos_boot", "electrical", soft(F.box(468, 490, 78, 104, 62, 94), "|Z", 4), RED_BOOT))
    # removable connection cover, shown see-through so the terminals stay visible
    parts.append(part(f"{nm}_conn_cover", "electrical", F.box(uc, ue, 2, D - 2, 12, H - 1), CONN_COVER))
    # anchors: cable entries on the bottom (end) face, at the real terminal positions
    yend = yq0 + L
    anchor("inv_dc_pos", (xq0 + 91, yend, zq + 40))
    anchor("inv_dc_neg", (xq0 + 54, yend, zq + 40))
    anchor("inv_ac", (xq0 + 210, yend, zq + 80))
    anchor("inv_comms", (xq0 + 145, yend, zq + 110))
    anchor("inv_remote", (xq0 + 165, yend, zq + 110))
    anchor("inv_chassis_earth", (xq0 + 22, yend + 6, zq + 28))


def fan(parts, fx, fy, fz):
    """92 mm 12 V fan blowing down onto the inverter, hung from a 3 mm plate bracket off the front wall."""
    s, t = FAN
    h = s / 2
    frame = box(fx - h, fx + h, fy - h, fy + h, fz - t / 2, fz + t / 2).cut(pcyl(45, t + 2, (fx, fy, fz), n=32))
    for dx in (-41.25, 41.25):
        for dy in (-41.25, 41.25):
            frame = frame.cut(pcyl(2.2, t + 2, (fx + dx, fy + dy, fz), n=8))
    sh = [frame, pcyl(19, t - 4, (fx, fy, fz), n=20)]
    for k in range(7):                                                                 # 7 pitched blades
        b = cq.Workplane("XY").box(25, 15, 1.6).rotate((0, 0, 0), (1, 0, 0), 28).translate((31, 0, 0))
        sh.append(b.rotate((0, 0, 0), (0, 0, 1), k * 360 / 7).translate((fx, fy, fz)))
    zg = fz - t / 2 - 0.75                                                             # finger guard on the outlet side
    sh += [pring(23, 21.5, 1.5, (fx, fy, zg), "Z", 20), pring(37, 35.5, 1.5, (fx, fy, zg), "Z", 28),
           box(fx - 45, fx + 45, fy - 0.8, fy + 0.8, zg - 0.75, zg + 0.75), box(fx - 0.8, fx + 0.8, fy - 45, fy + 45, zg - 0.75, zg + 0.75)]
    parts.append(part("inverter_fan", "electrical", grp(sh), CAP_BLACK, kg=0.3))
    zt = fz + t / 2
    plate = box(0, fx + h + 4, fy - h, fy + h, zt, zt + 3).cut(pcyl(44, 10, (fx, fy, zt), n=32))
    for dx in (-41.25, 41.25):
        for dy in (-41.25, 41.25):
            plate = plate.cut(pcyl(2.2, 10, (fx + dx, fy + dy, zt), n=8))
    parts.append(part("bay_fan_bracket", "bay", plate, "alu", fab=True, mat="Plate 3 5052"))
    parts.append(part("bay_fan_bracket_leg", "bay", box(0, 3, fy - h, fy + h, zt + 3, P.CHARGE_BOARD_Z - 5), "alu",
                      fab=True, mat="Plate 3 5052"))


def orion(parts, y0, zb):
    """Victron Orion XS 12/12-50A on the front-wall board, terminals down (dimension drawing ORI121217040)."""
    W, T, Hh = ORION
    F = Frame((6, y0, zb), ("Y", "X", "Z"))              # a = across (Y), t = off the board (X), v = up (Z)
    nm = "orion_xs_50a"
    body = soft(F.box(3, W - 3, 0, T - 4, 6, Hh - 4), "|Z and >X", 5)
    ridges = [soft(F.box(a0, a0 + 24, 0, T, 8, Hh - 6), "|Z and >X", 5) for a0 in (3, W - 27)]
    tabs = []
    for a in (6.9, W - 6.9):
        for v in (16, 129.7):
            tabs.append(F.box(a - 6.9, a + 6.9, 0, 4, v - 7, v + 7).cut(F.cyl(2.15, 1, -1, 5, a, v)))
    parts.append(part(nm, "electrical", grp(body, ridges, tabs), BLUE, kg=0.4))
    cov = soft(F.box(38, 85, 4, 38, 0, 28), "|Y", 4)
    for a in (46, 61.3, 76.7):                                                         # IN / GND / OUT cable entries
        cov = cov.cut(F.cyl(5, 2, -1, 10, a, 20.5))
    blk = [cov, F.box(25, 37, 12, 30, 1, 12),                                          # remote H/L plug
           soft(F.box(86, 93, 36, 37.5, 98, 116), "|X", 3)]                            # 3-LED window
    parts.append(part(f"{nm}_terminal_cover", "electrical", grp(blk), CAP_BLACK))
    parts.append(part(f"{nm}_stripe", "electrical", F.box(30, 93, T - 4, T - 3.4, 76, 79), ORANGE))
    parts.append(part(f"{nm}_vedirect", "electrical", F.box(86, 98, 14, 24, 2, 8), TERM_GREY))
    anchor(nm, F.pt(W / 2, T, 0))
    anchor("orion_in", F.pt(46, 20.5, 0))
    anchor("orion_out", F.pt(76.7, 20.5, 0))
    anchor("orion_remote", F.pt(31, 21, 1))


def mppt_100_30(parts, y0, zb):
    """SmartSolar MPPT 100/30: black finned heatsink behind a blue body, terminal block at the bottom centre."""
    W, T, Hh = MPPT_100_30
    F = Frame((6, y0, zb), ("Y", "X", "Z"))
    nm = "mppt_roof_100_30"
    body = soft(F.box(18, W - 18, 20, T - 4, 6, Hh), "|Z and >X", 8)
    hood = soft(F.box(70, 124, T - 4, T, 4, 32), "|Z and >X", 4)
    for a in (77, 90.5, 104, 117):                                                     # terminal screw access
        hood = hood.cut(F.cyl(3, 1, T - 3, T + 1, a, 12))
    parts.append(part(nm, "electrical", grp(body, hood), BLUE, kg=1.3))
    hs = F.box(0, W, 14, 20, 0, Hh)
    for a in (4, W - 14):                                                              # mounting slots in the flanges
        for v in (12, Hh - 22):
            hs = hs.cut(F.box(a + 2, a + 8, 13, 21, v, v + 10))
    fins = [F.box(a, a + 2.4, 0, 14, 2, Hh - 2) for a in [8 + 13.5 * k for k in range(13)]]
    led = F.box(146, 162, T - 4, T - 3, 16, 50)
    parts.append(part(f"{nm}_heatsink", "electrical", grp(hs, fins, led), HS_BLACK))
    tb = F.box(72, 122, 26, 54, 0, 8)
    for a in (77, 90.5, 104, 117):
        tb = tb.cut(F.box(a - 3, a + 3, 36, 44, -1, 5))
    parts.append(part(f"{nm}_terminals", "electrical", grp(tb, F.box(148, 160, 34, 44, 2, 8)), TERM_GREY))
    parts.append(part(f"{nm}_stripe", "electrical", F.box(30, 140, T - 4, T - 3.4, 58, 64), ORANGE))
    # terminal order (front view, left -> right = -Y -> +Y): BAT+ BAT- PV- PV+
    anchor(nm, F.pt(W / 2, T, 0))
    anchor("mppt_roof_bat", F.pt(83.75, 40, 0))
    anchor("mppt_roof_pv", F.pt(110.5, 40, 0))


def mppt_75_15(parts, y0, zb):
    """SmartSolar MPPT 75/15: one-piece blue case, 4 ears, 6-way terminal strip in the bottom face."""
    W, T, Hh = MPPT_75_15
    F = Frame((6, y0, zb), ("Y", "X", "Z"))
    nm = "mppt_tent_75_15"
    body = soft(F.box(7, W - 7, 0, T, 3, Hh), "|Z and >X", 6)
    tpos = [30.25 + 10.5 * i for i in range(6)]                                       # BAT+ BAT- PV- PV+ LOAD- LOAD+
    for a in tpos:
        body = body.cut(F.cyl(2.6, 1, T - 3, T + 1, a, 11))
    ears = []
    for a in (0, W - 9):
        for v in (8, Hh - 20):
            ears.append(F.box(a, a + 9, 0, 4, v, v + 12).cut(F.cyl(2.2, 1, -1, 5, a + 4.5, v + 6)))
    parts.append(part(nm, "electrical", grp(body, ears), BLUE, kg=0.5))
    tb = F.box(24, 89, 8, 30, 0, 12)
    for a in tpos:
        tb = tb.cut(F.box(a - 2.5, a + 2.5, 16, 22, -1, 5))
    parts.append(part(f"{nm}_terminals", "electrical", tb, TERM_GREEN))
    parts.append(part(f"{nm}_stripe", "electrical", F.box(14, W - 14, T, T + 0.6, 62, 66), ORANGE))
    anchor(nm, F.pt(56.5, T, 0))
    anchor("mppt_tent_bat", F.pt((tpos[0] + tpos[1]) / 2, 19, 0))
    anchor("mppt_tent_pv", F.pt((tpos[2] + tpos[3]) / 2, 19, 0))


def battery(parts, n, bx0, ya, z0, lugs):
    """iTech400X Pro standing on end, lid (terminal face) toward the rear (+X), terminals at the TOP end."""
    bw, bt, bl = P.BATT_W, P.BATT_H - 15, P.BATT_L          # 240 wide, 220 deep (excl. terminals), 525 long
    xl = bx0 + bt - BATT_LID                                # lid starts here
    xf = bx0 + bt                                           # lid face
    zt = z0 + bl - BATT_TERM_IN                             # terminal height (both terminals)
    yp, yn = ya + BATT_TERM_EDGE, ya + bw - BATT_TERM_EDGE  # + toward the distribution column, - outboard
    body = soft(box(bx0, xl, ya + 2, ya + bw - 2, z0, z0 + bl), "|Z", 6, True)
    hand = []
    for ze, zz in ((z0 + bl, z0 + bl + BATT_LUG), (z0 - 6, z0)):                       # end handle lugs (top + bottom)
        for yy in (ya + 48, ya + 172):
            hand.append(box(xl - 12, xl + 14, yy, yy + 20, ze, zz))
    hand.append(box(xl - 6, xl + 8, ya + 68, ya + 172, z0 + bl, z0 + bl + 4))         # folded carry strap (top end)
    parts.append(part(f"battery_{n}", "batteries", grp(body, hand), "battery", kg=P.BATT_KG))
    parts.append(part(f"battery_{n}_band", "batteries", soft(box(xl, xf, ya, ya + bw, z0 + 1, z0 + bl - 1), "|X", 5, True),
                      "battery_accent"))                                               # orange lid
    parts.append(part(f"battery_{n}_pad_pos", "batteries", box(xf, xf + 2, yp - 20, yp + 20, zt - 17, zt + 17), RED_BOOT))
    parts.append(part(f"battery_{n}_pad_neg", "batteries", box(xf, xf + 2, yn - 20, yn + 20, zt - 17, zt + 17), BLACK_BOOT))
    # terminals: M8 bolt inserts; + carries the MRBF 300 A block, output stud toward the battery centre
    ml, mw, mt = MRBF_5191
    xm = xf + 6                                             # MRBF base sits on the + terminal boss
    yo = yp + 40                                            # MRBF output stud
    pos = [pcyl(8, 6, (xf + 3, yp, zt), "X"), hexp(13, 6, (xm + mt + 8, yp, zt), "X"), pcyl(4, 18, (xm + mt + 9, yo, zt), "X", 8),
           hexp(13, 6, (xm + mt + 12, yo, zt), "X")]
    parts.append(part(f"battery_{n}_pos", "batteries", grp(pos), TIN))
    neg = [pcyl(8, 6, (xf + 3, yn, zt), "X"), hexp(13, 6, (xf + 12, yn, zt), "X")]
    parts.append(part(f"battery_{n}_neg", "batteries", grp(neg), TIN))
    mrbf = soft(box(xm, xm + mt, yp - 22, yp - 22 + ml, zt - mw / 2, zt + mw / 2), "|X", 5)
    parts.append(part(f"battery_{n}_mrbf", "electrical", mrbf, CAP_BLACK, kg=0.1))
    parts.append(part(f"battery_{n}_mrbf_fuse", "electrical",
                      grp(box(xm + mt, xm + mt + 2, yp - 8, yo + 8, zt - 10, zt + 10),
                          box(xm + mt + 2, xm + mt + 6, yp + 10, yo - 10, zt - 9, zt + 9)), MIDI_FUSE))
    anchor(f"batt{n}_pos", (xm + mt + 7.5, yo, zt))         # lug on the MRBF output stud
    anchor(f"batt{n}_neg", (xf + 7.5, yn, zt))              # lug on the - terminal
    lugs.add((xm + mt + 7.5, yo, zt), "+X", "+Z", "+")
    lugs.add((xf + 7.5, yn, zt), "+X", "+Z", "-")
    return xf


def powerbar(parts, F, nm, kg, used):
    """Blue Sea 2104 PowerBar 600 A on the board: black base, tinned bar, 4 x 3/8" studs, 4 small screws."""
    L, W, Hh = POWERBAR
    base = F.box(0, L, 0, W, 0, 14)
    for s in (9.5, L - 9.5):                                                           # recessed mounting holes
        base = base.cut(F.cyl(6, 2, 8, 15, s, W / 2)).cut(F.cyl(3.3, 2, -1, 15, s, W / 2))
    parts.append(part(nm, "electrical", base, CAP_BLACK, kg=kg))
    studs = [L / 2 + POWERBAR_PITCH * k for k in (-1.5, -0.5, 0.5, 1.5)]
    tin = [F.box(14, L - 14, 6, W - 6, 14, 24)]
    tin += [F.cyl(4.76, 2, 24, Hh, s, W / 2) for s in studs]
    tin += [F.cyl(2.6, 2, 24, 27, s, w) for s in (20, L - 20) for w in (12, W - 12)]
    tin += [F.hexp(14.3, 2, 27, 34, studs[i], W / 2) for i in used]                   # nuts on the studs in use
    parts.append(part(f"{nm}_bar", "electrical", grp(tin), TIN))
    return [F.pt(s, W / 2, 25.5) for s in studs]           # lug positions (ring centre on the bar)


def remote_switch(parts, F, lugs):
    """Blue Sea ML-RBS 7713: studs and control harness out of the bottom end, yellow manual-control knob on top."""
    Lr, Wr, Hr = RBS_7713
    nm = "remote_battery_switch_500a"
    body = soft(F.box(30, 124, 6, Wr - 6, 0, Hr - 3), "|X", 6)
    top = soft(F.box(122, Lr, 14, Wr - 14, 0, Hr), "|X", 4)
    low = soft(F.box(12, 32, 3, Wr - 3, 0, 40), "|X", 4)
    tabs = []
    for w in (9.5, Wr - 9.5):
        for s in (15, 128):
            tabs.append(F.box(s - 7, s + 7, w - 8, w + 8, 0, 4).cut(F.cyl(2.8, 2, -1, 5, s, w)))
    harness = [F.box(-4, 12, Wr / 2 - 8, Wr / 2 + 8, 4, 20)] + [F.cyl(1.6, 0, -10, -4, Wr / 2 + dw, 12) for dw in (-4, 0, 4)]
    parts.append(part(nm, "electrical", grp(body, top, low, tabs, harness), DARK_GREY, kg=0.9))
    parts.append(part(f"{nm}_knob", "electrical", soft(F.box(130, Lr + 3, 32, 64, 24, Hr + 2), "|X", 3), YELLOW))
    parts.append(part(f"{nm}_window", "electrical", F.box(70, 110, 20, 75, Hr - 3, Hr - 2), WINDOW))
    sw = [Wr / 2 - 24.13, Wr / 2 + 24.13]                    # A (out), B (in)
    hs = 26.16
    met = [F.cyl(4.76, 0, 0, 12, w, hs) for w in sw] + [F.hexp(14.3, 0, 3, 9, w, hs) for w in sw]
    parts.append(part(f"{nm}_studs", "electrical", grp(met), TIN))
    a_out, a_in = F.pt(10.5, sw[0], hs), F.pt(10.5, sw[1], hs)
    lugs.add(a_out, "-Z", "+Y", "+")
    lugs.add(a_in, "-Z", "+Y", "+")
    anchor("rbs_out", a_out)
    anchor("rbs_in", a_in)
    anchor("rbs_ctrl", F.pt(-10, Wr / 2, 12))


def class_t(parts, F, lugs):
    """Blue Sea 5502 Class-T block with a 400 A Class-T fuse (fibre tube, silver ferrules, bolted blades)."""
    Lc, Wc, Hc = CLASS_T_5502
    nm = "class_t_400a"
    s_out, s_in = Lc / 2 - CLASS_T_STUDS / 2, Lc / 2 + CLASS_T_STUDS / 2
    base = soft(F.box(0, Lc, 0, Wc, 0, 16), "|Y", 6)
    ped = [F.box(s - 16, s + 16, 4, Wc - 4, 16, 20) for s in (s_out, s_in)]
    for s in (8, Lc - 8):
        base = base.cut(F.cyl(3.3, 2, -1, 17, s, Wc / 2))
    parts.append(part(nm, "electrical", grp(base, ped), CAP_BLACK, kg=0.5))
    w2 = Wc / 2
    parts.append(part(f"{nm}_fuse", "electrical", F.cyl(13, 0, s_out + 20, s_in - 20, w2, 36, 16), FIBRE))
    met = [F.cyl(14, 0, s_out + 15, s_out + 21, w2, 36, 16), F.cyl(14, 0, s_in - 21, s_in - 15, w2, 36, 16),       # ferrules
           F.box(s_out - 12, s_out + 17, w2 - 11, w2 + 11, 20, 23), F.box(s_in - 17, s_in + 12, w2 - 11, w2 + 11, 20, 23),  # blades
           F.box(s_out + 13, s_out + 17, w2 - 10, w2 + 10, 20, 36), F.box(s_in - 17, s_in - 13, w2 - 10, w2 + 10, 20, 36)]
    met += [F.cyl(4.76, 2, 20, 44, s, w2) for s in (s_out, s_in)] + [F.hexp(14.3, 2, 26, 33, s, w2) for s in (s_out, s_in)]
    parts.append(part(f"{nm}_metal", "electrical", grp(met), TIN))
    p_out, p_in = F.pt(s_out, w2, 24.5), F.pt(s_in, w2, 24.5)
    lugs.add(p_out, "+Y", "-Z", "+")
    lugs.add(p_in, "+Y", "+X", "+")
    anchor("classT_out", p_out)
    anchor("classT_in", p_in)


def smartshunt(parts, F, lugs):
    """Victron SmartShunt 500 A: black base, brass end blocks with M10 bolts, blue electronics housing."""
    nm = "smartshunt_500a"
    sl, sw, sh = P.SHUNT[0], P.SHUNT[2], P.SHUNT[1]          # 120 long, 54 wide, 46 deep
    sb, ss = 19, sl - 19                                     # system-side bolt (bottom), battery-side bolt (top)
    parts.append(part(nm, "electrical", soft(F.box(30, 90, 18, sw, 8, 36), "|X", 4), BLUE, kg=0.2))
    parts.append(part(f"{nm}_base", "electrical", soft(F.box(0, sl, 6, 36, 0, 8), "|Y", 4), CAP_BLACK))
    br = [F.box(6, 32, 4, 36, 8, 30), F.box(sl - 32, sl - 6, 4, 36, 8, 30), F.box(32, sl - 32, 6, 30, 8, 12)]
    br += [F.hexp(17, 2, 33, 42, s, 20) for s in (sb, ss)]
    parts.append(part(f"{nm}_brass", "electrical", grp(br), BRASS))
    parts.append(part(f"{nm}_vedirect", "electrical", F.box(34, 46, sw, sw + 2, 14, 24).cut(F.box(36, 44, sw + 1, sw + 3, 17, 21)),
                      TERM_GREY))
    parts.append(part(f"{nm}_vbatt_terminal", "electrical", F.box(74, 86, sw - 4, sw + 3, 12, 26), TERM_GREEN))
    p_sys, p_bat = F.pt(sb, 20, 31.5), F.pt(ss, 20, 31.5)
    lugs.add(p_bat, "+Y", "+Z", "-", r_stud=5.2)
    lugs.add(p_sys, "+Y", "-Z", "-", r_stud=5.2)
    anchor("shunt", F.pt(ss, 20, sh))
    anchor("shunt_sys", F.pt(sb, 20, sh))
    anchor("shunt_vbatt", F.pt(80, sw + 3, 19))
    anchor("shunt_vedirect", F.pt(40, sw + 2, 19))


def fuse_holders(parts, x0s, yf, zb, link_to):
    """4 x Blue Sea 5151-type MIDI/MEGA holders below the Class-T, inputs linked to a system + stud by a tinned strap."""
    Lm, Wm, Hm = MIDI_BLOCK
    bases, met, fuses, covers = [], [], [], []
    outs = []
    for x0 in x0s:
        F = Frame((x0, yf, zb), ("Z", "X", "Y"))
        bases.append(soft(F.box(0, Lm, 0, Wm, 0, 18), "|Y", 3))
        fuses.append(F.box(20, 52, 6, 26, 18, 25))
        met += [F.box(6, 66, 9, 23, 18, 20)] + [F.cyl(4, 2, 18, 44, s, Wm / 2) for s in (12, 60)] + \
               [F.hexp(13, 2, 37, 43, s, Wm / 2) for s in (12, 60)]
        covers.append(F.box(2, Lm - 2, 1, Wm - 1, 25, 32))
        outs.append(F.pt(12, Wm / 2, 33 + 1.5))
    parts.append(part("fuse_holders_midi", "electrical", grp(bases), CAP_BLACK))
    parts.append(part("fuse_holders_midi_metal", "electrical", grp(met), TIN))
    parts.append(part("fuse_holders_midi_fuses", "electrical", grp(fuses), MIDI_FUSE))
    parts.append(part("fuse_holders_midi_cover", "electrical", grp(covers), CLEAR))
    # tinned link strap: holder inputs (z = zb + 60) -> system + busbar stud `link_to`
    zi, ys = zb + 60, yf + 34
    lx, _, lz = link_to
    strap = [box(x0s[0] + 8, lx + 8, ys, ys + 3, zi - 9, zi + 9), box(lx - 9, lx + 9, ys, ys + 3, lz - 9, zi + 9),
             pcyl(8, ys - (yf + 24), (lx, (ys + yf + 24) / 2, lz), "Y")]
    parts.append(part("fuse_link_strap", "electrical", grp(strap), TIN))
    return outs


# ====================================================================== bay
def bay():
    parts = []
    lugs = Lugs()                                   # distribution column lugs
    blugs = Lugs("lugs_batt", "batteries")          # battery terminal lugs (hide with the batteries)
    hw = P.BAY_W / 2
    d = P.BAY_D
    s = 30
    g = "bay"
    shs = "SHS 30x30x2 6060"
    z0 = 6
    bw = P.BATT_W
    bx0 = 8
    ybs = [hw - 2 - 2 * bw - 10, hw - 2 - bw]
    # ---- frame: base tray (relief slots under the batteries' bottom handle lugs), two rear posts, rear top rail
    tray = box(0, d, -hw, hw, 0, z0)
    xl = bx0 + P.BATT_H - 15 - BATT_LID
    for ya in ybs:
        for yy in (ya + 48, ya + 172):
            tray = tray.cut(box(xl - 13, xl + 15, yy - 1, yy + 21, -1, z0 + 1))
    parts.append(part("bay_base_tray", g, tray, "alu", fab=True, mat="Plate 6 5052"))
    for y in (-hw, hw - s):
        parts.append(part(f"bay_rear_post_{int(y)}", g, tube_box(d - s, d, y, y + s, z0, P.BAY_H, axis="Z"), "alu", fab=True, mat=shs))
    parts.append(part("bay_rear_top", g, tube_box(d - s, d, -hw + s, hw - s, P.BAY_H - s, P.BAY_H, axis="Y"), "alu", fab=True, mat=shs))
    # ---- MultiPlus-II lying flat, passenger side, connection end toward the distribution column (+Y)
    L, D, H = P.INVERTER
    yq0, yq1 = -hw + 2, -hw + 2 + L
    xq0 = 4
    zq = z0 + 4
    multiplus(parts, xq0, yq0, zq)
    parts.append(part("inverter_standoffs", g, box(xq0 + 20, xq0 + D - 20, yq0 + 20, yq1 - 20, z0, zq), "alu_dark", fab=True, mat="Plate 4 5052"))
    fan(parts, xq0 + D / 2, yq0 + L / 2, zq + H + 40)
    # ---- charging board on the front wall above the inverter (vertical, terminals down)
    zc = P.CHARGE_BOARD_Z
    parts.append(part("charge_board", g, box(0, 6, yq0 + 5, yq1 - 5, zc, P.BAY_H), "alu", fab=True, mat="Plate 6 5052"))
    yb = yq0 + 20
    orion(parts, yb, zc + 15)
    yb += ORION[0] + CHARGE_GAP
    mppt_100_30(parts, yb, zc + 15)
    yb += MPPT_100_30[0] + CHARGE_GAP
    mppt_75_15(parts, yb, zc + 15)
    # ---- batteries on end, driver side, lids/terminals facing the rear (+X), terminals at the top end
    for i, ya in enumerate(ybs):
        n = i + 1
        xf = battery(parts, n, bx0, ya, z0, blugs)
        for zz in (z0 + 150, z0 + 420):   # cage straps (flat bar) tied to the rear posts and front-wall brackets
            parts.append(part(f"battery_{n}_strap_{zz}", g, box(bx0 - 3, xf + 3, ya - 3, ya + bw + 3, zz, zz + 40).cut(
                box(bx0, xf, ya, ya + bw, zz - 1, zz + 41)), "alu_dark", fab=True, mat="Flat 50x6 6060"))
            yc = ya + bw / 2                                   # over-centre buckle + hinge pin + 2 bolts on the lid face
            bk = [box(xf + 3, xf + 11, yc - 22, yc + 22, zz + 4, zz + 36), pcyl(3, 50, (xf + 9, yc, zz + 8), "Y", 8)]
            bk += [hexp(10, 4, (xf + 5, yy, zz + 20), "X") for yy in (ya + 30, ya + bw - 30)]
            parts.append(part(f"battery_{n}_strap_{zz}_buckle", g, grp(bk), STEEL))
    # ---- distribution column between the inverter and battery 1 (components on a board, facing +Y)
    yd0 = yq1 + 8
    # the MultiPlus cable entries (DC at z ~50, AC glands at z ~90) face the board 8 mm away: the board gets a cable
    # window in its lower edge so the 2 x 50 mm2 DC and the AC/comms cables pass straight through and bend in the
    # ~115 mm gap between the board and battery 1 (v0.9; saves re-spacing the bay)
    win = (36, 276, DIST_WINDOW_Z)
    board = box(30, d - 34, yd0, yd0 + 6, z0, P.BAY_H - 10).cut(box(win[0], win[1], yd0 - 1, yd0 + 7, z0 - 1, win[2]))
    parts.append(part("dist_board", g, board, "alu", fab=True, mat="Plate 6 5052"))
    trim = grp(box(win[0], win[1], yd0 - 2, yd0 + 8, win[2] - 3, win[2] + 3),
               box(win[0] - 3, win[0] + 3, yd0 - 2, yd0 + 8, z0, win[2]), box(win[1] - 3, win[1] + 3, yd0 - 2, yd0 + 8, z0, win[2]))
    parts.append(part("dist_board_window_trim", g, trim, CAP_BLACK))      # rubber edge grommet strip
    yf = yd0 + 6
    V = ("Z", "X", "Y")                                          # vertical parts: a = up, b = across (X), c = off the board
    # bank - busbar (stud 1: SH1 to the shunt, studs 2/3: battery negatives)
    st = powerbar(parts, Frame((37, yf, 290), V), "busbar_bank_neg", 0.6, used=(0, 1, 2))
    lugs.add(st[0], "+Y", "-Z", "-")
    lugs.add(st[1], "+Y", "+X", "-")
    lugs.add(st[2], "+Y", "+X", "-")
    anchor("bus_bank_neg", st[0])
    # bank + busbar (stud 4: battery 1, stud 3: battery 2, stud 2: RB1 to the remote switch)
    st = powerbar(parts, Frame((232, yf, 345), V), "busbar_bank_pos", 0.6, used=(1, 2, 3))
    for k in (1, 2, 3):
        lugs.add(st[k], "+Y", "-X", "+")
    anchor("bus_bank_pos", st[3])
    # system + busbar (stud 1: MIDI link strap, stud 2: spare, stud 3: Class-T feed, stud 4: from the remote switch)
    st = powerbar(parts, Frame((232, yf, 120), V), "busbar_sys_pos", 0.6, used=(2, 3))
    lugs.add(st[2], "+Y", "-X", "+")
    lugs.add(st[3], "+Y", "-X", "+")
    anchor("bus_sys_pos", st[3])
    anchor("bus_sys_pos_studs", st[1])
    sys_pos_link = st[0]
    # system - busbar lying flat on the base tray just past the board window, studs up
    # (stud 1: SH2 from the shunt, stud 2: inverter - straight through the window, stud 3: charger negatives)
    st = powerbar(parts, Frame((60, yf + 2, z0), ("X", "Y", "Z")), "busbar_sys_neg", 0.5, used=(0, 1))
    lugs.add(st[0], "+Z", "+Y", "-", ln=0.7)
    lugs.add(st[1], "+Z", "-Y", "-", ln=0.7)
    anchor("bus_sys_neg", st[1])
    anchor("bus_sys_neg_studs", st[2])
    # ML-RBS remote battery switch, studs down
    remote_switch(parts, Frame((105, yf, 385), V), lugs)
    # Class-T 400 A (inverter feed)
    class_t(parts, Frame((145, yf, 196), V), lugs)
    # SmartShunt 500 A (battery side up)
    smartshunt(parts, Frame((40, yf, 150), V), lugs)
    # MIDI / MEGA fuse holders: tent MPPT 20 A, roof MPPT 60 A, Orion 70 A, DC fuse block MEGA 100 A
    outs = fuse_holders(parts, (96, 130, 164, 198), yf, 112, sys_pos_link)
    for o, nm in zip(outs, ("midi_mppt_tent", "midi_mppt_roof", "midi_orion", "mega_dc_fuse_block")):
        lugs.add(o, "+Y", "-Z", "+", size=0.8, ln=0.5)
        anchor(nm, o)
    anchor("midi_fuses", outs[3])
    parts += lugs.parts() + blugs.parts()
    # ---- slotted guard on the bay's rear face (protects terminals from slide cargo, lets the bay breathe)
    gz0, gz1 = 160, P.BAY_H - s
    guard = box(d - 2, d, -hw + s, hw - s, gz0, gz1)
    cuts = []
    for r, zz in enumerate(range(gz0 + 20, int(gz1) - 24, 34)):          # staggered 140 x 12 slots
        off = 0 if r % 2 == 0 else 85
        for yy in range(int(-hw + s + 30 + off), int(hw - s - 170), 170):
            cuts.append(box(d - 3, d + 1, yy, yy + 140, zz, zz + 12))
    guard = guard.cut(grp(cuts))
    parts.append(part("bay_guard", "bay_cover", guard, GUARD, fab=True, mat="Sheet 1.6 5005"))
    return parts
