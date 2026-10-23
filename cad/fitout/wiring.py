"""
Cable routing and schedule (v0.13: route network).

Every cable follows a path through named route NODES. Consecutive nodes that belong to the same RUN form a segment of
that run; each run has a containment (conduit, tray, channel, chain, hollow extrusion...) and a cross-section in which
its cables are packed in rows (biggest first), so bundles render as neat parallel lanes and every run's fill can be
checked. Short connections from a run to a terminal ("tails") are drawn straight.

All cables that leave the tub pass through the factory 240 V outlet hole (passenger wall): 230 V through its own
grommet row and its own orange conduit (segregated from 12 V, AS/NZS 3000 3.9.8 / 3001.2), everything else through the
12 V row. Outside, both conduits run down the wall cavity, under the tub floor to the passenger chassis rail, and along
it to the cab-tub gap (junction box, roof), the cabin (compute box) and the engine bay.
"""
import math
from dataclasses import dataclass, field

import params as P

from .core import ANCHORS, C, Part, anchor, box, part

# ------------------------------------------------------------------ cable outer diameters (mm) [EST, typical AU stock]
OD1 = {0.75: 2.4, 1.0: 2.7, 1.5: 3.0, 2.5: 3.8, 4: 4.6, 6: 5.4, 10: 7.2, 16: 8.6, 25: 10.4, 35: 11.8, 50: 13.6, 70: 15.6,
       120: 19.8}                                                        # single core, tinned marine / automotive
SOLAR1 = {4: 5.8, 6: 6.4, 10: 7.6}                                       # single-core PV cable (double insulated)
FLEX3 = {1.5: 8.5, 2.5: 10.5, 4: 12.0}                                   # 3-core sheathed flex (TPS-flex / H07RN-F)
MULTI = {"4c1.0": 7.0, "4c0.75": 6.6, "3c0.75": 6.3, "2c0.75": 5.6, "2c1.5": 7.4, "vebus": 6.0, "vedirect": 4.5,
         "usb": 4.5, "hdmi": 9.0}


def od_of(form, s=None):
    """(core OD, cores): 'single', 'twin' (+ and - singles run side by side), 'pv2' (PV pair), 'x2' (two paralleled singles),
    'flex3' (one sheathed 3-core), or a MULTI key (s = count of identical cables, packed as one round bundle)."""
    if form == "single":
        return (OD1[s], 1)
    if form == "twin":
        return (OD1[s], 2)
    if form == "pv2":
        return (SOLAR1[s], 2)
    if form == "x2":
        return (OD1[s], 2)
    if form == "flex3":
        return (FLEX3[s], 1)
    if form in MULTI:
        return (MULTI[form] if s is None else MULTI[form] * math.sqrt(s), 1)
    raise KeyError(form)


@dataclass
class Cable:
    cid: str
    circuit: str
    frm: str
    to: str
    size: str              # conductor key for the diagram ('120', '35', '6', '2.5x3', 'data', ...)
    spec: str              # conductor / type description (schedule)
    protection: str
    colour: str            # key in C
    path: list             # node / anchor names or xyz tuples
    od: object = 6.0       # (core OD, cores) from od_of(), or a single round OD (mm)
    side: str = "vehicle"  # 'vehicle' or 'tent' (detachable tent harness)
    extra_mm: float = 0.0  # e.g. length inside a cable chain, matched-length pairs
    lv: bool = False       # 230 V (low voltage): segregated route
    notes: str = ""
    pts: list = field(default_factory=list)   # routed polyline, centre of the cable (set by route())
    core_pts: list = field(default_factory=list)  # one polyline per core for twins (+ then -)
    runs: list = field(default_factory=list)  # run codes it uses, in order

    def __post_init__(self):
        self.d1, self.cores = self.od if isinstance(self.od, tuple) else (float(self.od), 1)
        self.od = self.d1 * math.sqrt(self.cores)                 # area-equivalent round OD (fill, conduit sizing)
        self.w = self.cores * self.d1 + (self.cores - 1) * 1.0    # footprint across the lane (cores side by side)
        self.h = self.d1

    def points(self, k=0):
        return self.pts

    def run_mm(self):
        return sum(math.dist(a, b) for a, b in zip(self.pts[:-1], self.pts[1:]))

    def length_m(self):
        return round((self.run_mm() * 1.10 + 300 + self.extra_mm) / 1000, 2)   # +10 % slack, +0.3 m terminations


@dataclass
class Run:
    code: str
    name: str
    zone: str               # bay / tray / wall / cabinet / under / chassis / cabin / engine / gap / roof / tent / slide
    nodes: list
    hold: str               # containment + fixing, for the schedule and the route sheets
    wide: str = "y"         # cross-section axis the bundle spreads along (rows run along it)
    width: float = 80.0     # space along `wide` (mm) before a new row starts
    kind: str = "open"      # conduit / lv_conduit / loom / tray / channel / duct / hollow / chain / open
    clip: float = 0.0       # clip / saddle spacing (mm) drawn along the run (0 = none)
    lv: bool = False        # 230 V only
    members: list = field(default_factory=list)
    slots: dict = field(default_factory=dict)
    size_mm: float = 0.0    # chosen conduit / loom ID


NODES = {}
RUNS = []
GROMMETS = []               # (name, node a, node b, r_extra): ring where a bundle passes a panel


def N(name, xyz):
    NODES[name] = tuple(float(v) for v in xyz)
    anchor(name, xyz)
    return name


def R(code, name, zone, nodes, hold, **kw):
    RUNS.append(Run(code, name, zone, list(nodes), hold, **kw))


# ================================================================== route network
def network():
    NODES.clear()
    RUNS.clear()
    GROMMETS.clear()
    junction_anchors()
    hw = P.TUB_W / 2                       # 786: tub inner wall
    cav = -(hw + P.TUB_WALL_T + 24.5)      # -865.5: middle of the wall cavity (inner wall -841 .. outer skin -890)
    fx = P.FACTORY_OUTLET[0]               # 1330
    xg = P.CAB_REAR_X + 28                 # -82: centre of the cab-tub gap
    rch = P.BAY_D - 20                     # 300: rear channel behind the inverter / busbars (board ends at x 286, guard 318)
    zt = P.UPPER_Z1 + 21                   # 531: cable tray band (tray floor 515, lid underside 548)
    yr = -(P.CHASSIS_RAIL_Y + 52)          # -522: outer face of the passenger chassis rail (web at -500)
    zr, zrl = P.CHASSIS_Z - 35, P.CHASSIS_Z - 105     # -185 / -255: 12 V conduit high on the rail web, 230 V below it
    zu = -100                              # under the tub floor, between the bearers
    zroof = P.PLAT_Z - 15                  # 1015: under the platform rear end member
    xem = P.PLAT_X0 + P.PLAT_L - 20        # -170: platform rear end member (hollow extrusion) centre line
    zem = P.PLAT_Z + P.PLAT_T / 2          # 1050: inside the end member

    # ---------------- front bay: rear channel (x 286-318) links the busbar side, the inverter side and the exits
    for z in (30, 90, 190, 270, 360, 410):
        N(f"b_bus{z}", (rch, 62, z))                                   # riser in the gap between the busbars and battery 1
    N("b_rh_c", (rch, -45, 410))
    N("b_rh_s", (rch, -412, 410))
    N("b_rh_p", (rch, -520, 410))
    N("b_rm_c", (rch, -45, 360))
    N("b_rl_s", (rch, -412, 30))
    N("b_x1", (185, -520, 410))                                        # into the open space above the inverter
    N("b_x2", (185, -520, zt))
    N("b_x3", (185, -610, zt))                                         # over the drawer carcass, into the tray band
    N("b_cb_hi", (95, -520, 410))                                      # charging board: down in front of the fan bracket
    N("b_cb_520", (95, -520, 288))
    N("b_cb_310", (95, -310, 288))
    N("b_cb_145", (95, -145, 288))
    N("b_cb_60", (95, -60, 288))
    N("f_p", (18, -60, 288))                                           # front channel: between the front wall and the board edge
    N("f_c", (18, 40, 288))
    N("f_lo", (18, 40, 110))
    R("R01", "Bay riser, busbar side", "bay", ["b_bus30", "b_bus90", "b_bus190", "b_bus270", "b_bus360", "b_bus410"],
      "rear channel behind the busbars (gap to battery 1); cable ties to the rear posts' saddle bar every 150 mm", wide="y", width=46)
    R("R02", "Bay rear channel, high", "bay", ["b_bus410", "b_rh_c", "b_rh_s", "b_rh_p"],
      "behind the distribution board edge and the inverter, under the top rail; adhesive tie mounts on the guard frame",
      wide="x", width=26)
    R("R03", "Bay rear channel, cross link", "bay", ["b_rm_c", "b_bus360"], "behind the board edge, visor MPPT output",
      wide="x", width=26)
    R("R04", "Bay rear channel, low (to the slide)", "bay", ["b_bus30", "b_rl_s", "b_rh_s"],
      "along the base tray behind the inverter, then down from the high channel; P-clips to the base tray", wide="x", width=26)
    R("R05", "Bay exit over the inverter", "bay", ["b_rh_p", "b_x1", "b_x2", "b_x3"],
      "across the top of the inverter compartment and over the passenger drawer carcass; grommet strip on the carcass edge",
      wide="xz", width={"x": 176, "z": 60})
    R("R31", "Bay front channel (chargers to the MIDI fuses)", "bay", ["b_cb_60", "f_p", "f_c", "f_lo"],
      "between the front wall and the distribution board's front edge, under the charging board; tie mounts on the board edge",
      wide="x", width=22)
    R("R06", "Charging-board loom", "bay", ["b_x1", "b_cb_hi", "b_cb_520", "b_cb_310", "b_cb_145", "b_cb_60"],
      "down the front of the inverter compartment and along under the chargers' terminal faces; tie mounts on the board",
      wide="x", width=30)
    # ---------------- tub: lid-height cable tray over the passenger drawer (v0.13: 120 mm wide, divided)
    yl, ye = -768, -706                    # 230 V compartment (outboard, against the wall) / 12 V compartment
    N("t_lf0", (70, -610, zt))
    N("t_lf", (70, yl, zt))
    N("t_lr", (1215, yl, zt))
    N("t_ef", (185, ye, zt))
    N("t_er", (1350, ye, zt))
    R("R07", "Tray, 230 V compartment", "tray", ["b_x3", "t_lf0", "t_lf", "t_lr"], "aluminium tray, 230 V side of the divider; ties through the tray slots every 120 mm",
      wide="y", width=28, kind="tray", lv=True)
    R("R08", "Tray, 12 V compartment", "tray", ["b_x3", "t_ef", "t_er"], "aluminium tray, 12 V side of the divider; ties through the tray slots every 120 mm",
      wide="y", width={"y": 80, "x": 176}, kind="tray")
    # ---------------- wall channel behind the upper drawer (y -784..-761) down to the gland plate and the cabinet
    yw = -772
    zg = P.FACTORY_OUTLET[2] + 20          # 420: gland rows in the old outlet hole (plate z 355-445)
    N("w_l1", (1215, yw, zt))
    N("w_l2", (1215, yw, zg))
    N("w_l3", (1215, yw, 310))
    N("w_l4", (1285, yw, zg))
    N("w_e1", (1350, yw, zt))
    N("w_e2", (1350, yw, zg))
    N("w_e3", (1350, yw, 330))
    N("w_e4", (1320, yw, 330))
    N("g_l1", (1285, -(hw + 4), zg))
    N("g_e1", (1350, -(hw + 4), zg))
    R("R09", "Wall channel, 230 V drop", "wall", ["t_lr", "w_l1", "w_l2", "w_l4", "g_l1"],
      "22 mm channel behind the drawer runner panel, then out through the 230 V grommet row of the gland plate; ties to adhesive mounts",
      wide="xz", width=26, kind="channel", lv=True)
    R("R10", "Wall channel, 12 V drop", "wall", ["t_er", "w_e1", "w_e2"],
      "22 mm channel behind the drawer runner panel (two layers); ties to adhesive mounts on the tub wall",
      wide="x", width=112, kind="channel")
    R("R32", "Gland plate, 12 V rows", "wall", ["w_e2", "g_e1"], "12 V grommet rows of the gland plate in the old outlet hole",
      wide="x", width=62)
    # ---------------- rear control cabinet (glands in its top, outboard corridor y -782..-722 beside the RCBO enclosure)
    N("c_lin", (1215, yw, 262))
    N("c_l2", (1215, yw, 200))
    N("c_in", (1320, yw, 262))
    N("c_r", (1320, -754, 240))
    N("c_fb", (1140, -754, 240))
    N("c_cg", (955, -754, 240))
    N("c_pl", (1338, -754, 240))
    N("c_pl2", (1338, -700, 240))
    for z in (215, 160, 115, 50):
        N(f"c_pl{z}", (1338, -700, z))
    R("R11", "Cabinet, 230 V entry", "cabinet", ["w_l2", "w_l3", "c_lin", "c_l2"], "LV gland in the cabinet top, down the outboard corridor to the RCBO side gland",
      wide="x", width=26, lv=True)
    R("R12", "Cabinet entry (12 V slot)", "cabinet", ["w_e2", "w_e3", "w_e4", "c_in", "c_r"],
      "down the wall channel and through the 12 V slot (split grommet) in the drawer floor and cabinet top", wide="xz", width=98)
    R("R33", "Cabinet top loom", "cabinet", ["c_r", "c_fb", "c_cg"],
      "forward along the outboard corridor beside the RCBO enclosure, under the cabinet top; tie mounts", wide="y", width=52)
    R("R13", "Rear-panel loom", "cabinet", ["c_r", "c_pl", "c_pl2", "c_pl215", "c_pl160", "c_pl115", "c_pl50"],
      "vertical loom between the RCBO enclosure lid and the rear-panel devices; spiral wrap, ties to the door stile", wide="yz", width=60)
    # ---------------- out through the factory-outlet hole: gland plate (two rows), wall cavity, under the floor
    N("g_l2", (1285, cav, zg))
    N("g_l3", (1285, cav, zu))
    N("g_l4", (1285, yr, zu))
    N("g_l5", (1285, yr, zrl))
    N("g_e2", (1350, cav, zg))
    N("g_e3", (1350, cav, zu))
    N("g_e4", (1350, yr, zu))
    N("g_e5", (1350, yr, zr))
    R("R14", "Wall cavity + under floor, 230 V", "under", ["g_l1", "g_l2", "g_l3", "g_l4", "g_l5"],
      "LV grommet row in the gland plate; orange corrugated conduit down the wall cavity and under the floor to the rail",
      wide="x", width=26, kind="lv_conduit", clip=300, lv=True)
    R("R15", "Wall cavity + under floor, 12 V", "under", ["g_e1", "g_e2", "g_e3", "g_e4", "g_e5"],
      "12 V grommet row in the gland plate; black split corrugated conduit down the wall cavity and under the floor to the rail",
      wide="x", width=44, kind="conduit", clip=300)
    # ---------------- along the passenger chassis rail (outer face of the web), P-clips into rivnuts every 300 mm
    N("ch_l_gap", (xg, yr, zrl))
    N("ch_gap", (xg, yr, zr))
    N("ch_cab", (-760, yr, zr))
    N("ch_eng", (-2880, yr, zr))
    R("R16", "Chassis rail, 230 V, tub to the gap", "chassis", ["g_l5", "ch_l_gap"],
      "orange corrugated conduit on the rail web, below the 12 V conduit; rubber-lined P-clips every 300 mm", wide="z", width=26,
      kind="lv_conduit", clip=300, lv=True)
    R("R17", "Chassis rail, 12 V, tub to the gap", "chassis", ["g_e5", "ch_gap"],
      "black split conduit on the rail web; rubber-lined P-clips into M6 rivnuts every 300 mm (no welding or drilling the flanges)",
      wide="z", width=44, kind="conduit", clip=300)
    R("R18", "Chassis rail, 12 V, gap to the cabin", "chassis", ["ch_gap", "ch_cab"], "black split conduit; P-clips every 300 mm",
      wide="z", width=44, kind="conduit", clip=300)
    R("R19", "Chassis rail, 12 V, cabin to the engine bay", "chassis", ["ch_cab", "ch_eng"],
      "black split conduit (heat-rated near the exhaust); P-clips every 300 mm", wide="z", width=44, kind="conduit", clip=300)
    # ---------------- branches: cabin floor grommet, engine bay riser
    N("cb_1", (-760, yr, -60))
    N("cb_2", (-760, yr, -15))
    N("cb_3", (-760, -440, -15))
    R("R20", "Cabin branch", "cabin", ["ch_cab", "cb_1", "cb_2", "cb_3"],
      "up to a sealed grommet in the floor under the rear seat (sealant + rubber grommet), then to the compute box SB50 inlet",
      wide="x", width=20, kind="conduit", clip=250)
    N("en_1", (-2880, yr, 250))
    N("en_2", (-2955, yr, 250))
    R("R21", "Engine-bay riser", "engine", ["ch_eng", "en_1", "en_2"],
      "heat-rated split conduit up the inner guard behind the start battery; P-clips to existing guard holes", wide="x", width=30,
      kind="conduit", clip=250)
    # ---------------- cab-tub gap: risers to the junction box (12 V inboard, 230 V outboard) and on to the roof
    ye_g, yl_g = -650, -745
    N("gp_e1", (xg, ye_g, zr))
    N("gp_e2", (xg, ye_g, 360))
    N("gp_e3", (xg, ye_g, 535))
    N("gp_l1", (xg, yl_g, zrl))
    N("gp_l2", (xg, yl_g, 360))
    R("R22", "Gap riser, 230 V", "gap", ["ch_l_gap", "gp_l1", "gp_l2"], "orange conduit up the cab-tub gap to the LV gland in the junction box base",
      wide="y", width=24, kind="lv_conduit", clip=300, lv=True)
    R("R23", "Gap riser, 12 V", "gap", ["ch_gap", "gp_e1", "gp_e2"], "black conduit up the cab-tub gap to the ELV gland in the junction box base",
      wide="y", width=36, kind="conduit", clip=300)
    R("R24", "Junction box pass-through", "gap", ["gp_e2", "gp_e3"], "through the junction box on the 12 V side of its barrier (roof cables are not detachable)",
      wide="y", width=36)
    N("rf_1", (xg, ye_g, zroof))
    N("rf_2", (xem, ye_g, zroof))
    N("rf_3", (xem, ye_g, zem))
    N("rf_4", (xem, -350, zem))
    N("rf_5", (xem, 30, zem))
    R("R25", "Cab back riser to the roof", "roof", ["gp_e3", "rf_1", "rf_2"],
      "black conduit up the back of the cab (C-pillar corner), stick-on cable clamps every 250 mm, over the roof edge under the platform",
      wide="y", width=36, kind="conduit", clip=250)
    R("R26", "Platform rear end member", "roof", ["rf_2", "rf_3", "rf_4", "rf_5"],
      "inside the hollow rear end member (34 x 34 mm), in through a grommeted hole in its underside, out through grommets on its inner face",
      wide="z", width=26, kind="hollow")
    # ---------------- tent harnesses (stay with the tent): from the services box forward, across the front, down to J1-J4
    zh_a, zh_d = 685, 715
    N("tn_a1", (230, 260, zh_a))
    N("tn_a2", (-40, 260, zh_a))
    N("tn_a3", (-40, yl_g, zh_a))
    N("tn_a4", (-40, yl_g, 548))
    N("tn_a5", (xg, yl_g, 548))
    N("tn_d1", (230, 330, zh_d))
    N("tn_d2", (-55, 330, zh_d))
    N("tn_d3", (-55, ye_g, zh_d))
    N("tn_d4", (-55, ye_g, 548))
    N("tn_d5", (xg, ye_g, 548))
    R("R27", "Tent harness, 230 V", "tent", ["tn_a1", "tn_a2", "tn_a3", "tn_a4", "tn_a5"],
      "orange sheathed harness in UV-stable spiral wrap, saddles under the tent base and on the lid front", wide="z", width=24,
      kind="loom", clip=300, lv=True)
    R("R28", "Tent harness, 12 V + PV", "tent", ["tn_d1", "tn_d2", "tn_d3", "tn_d4", "tn_d5"],
      "black sheathed harness in spiral wrap, saddles under the tent base and on the lid front", wide="z", width=24,
      kind="loom", clip=300)
    # ---------------- power slide: trunk on the glide tray, then the chain (lying on its side)
    for n_ in ("slide_entry", "chain_trunk_end", "chain_fixed", "chain_bend_fixed", "chain_bend_tip", "chain_moving", "pod_cable_in"):
        NODES[n_] = ANCHORS[n_]
    N("s_drop", (rch, ANCHORS["slide_entry"][1], ANCHORS["slide_entry"][2]))
    R("R29", "Slide trunk (fixed, on the glide tray)", "slide", ["b_rl_s", "s_drop", "slide_entry", "chain_trunk_end"],
      "under the bay guard into the front of the cassette, along the glide tray outboard of the fixed run; ties to the tray lip",
      wide="y", width=30)
    R("R30", "Power-slide cable chain", "slide", ["chain_fixed", "chain_bend_fixed", "chain_bend_tip", "chain_moving", "pod_cable_in"],
      "igus E2.15 (R75) lying on its side, with a separator between the 230 V and 12 V cables; strain-relief at both ends",
      wide="z", width=30, kind="chain")
    # ---------------- grommets where bundles pass a panel
    GROMMETS.extend([("gland_plate_lv", "w_l4", "g_l1", 4), ("gland_plate_elv", "w_e2", "g_e1", 4),
                     ("cab_gland_lv", "w_l3", "c_lin", 3),
                     ("cabin_floor_grommet", "cb_1", "cb_2", 4), ("jb_gland_lv", "gp_l1", "gp_l2", 3),
                     ("jb_gland_elv", "gp_e1", "gp_e2", 3), ("jb_gland_roof", "gp_e2", "gp_e3", 3),
                     ("end_member_grommet", "rf_2", "rf_3", 3)])


def _up(a, dz=0):
    """Point straight below a charging-board terminal at the loom height (terminals face down)."""
    x, y, z = ANCHORS[a]
    return (x, y, 288 + dz)


def _drop(a, z):
    x, y, _ = ANCHORS[a]
    return (x, y, z)


# ================================================================== cables
def cables():
    network()
    A = ANCHORS
    L = []
    yr, zr, rch = -(P.CHASSIS_RAIL_Y + 52), P.CHASSIS_Z - 35, P.BAY_D - 20

    def add(cid, circuit, frm, to, size, spec, prot, colour, path, od, **kw):
        L.append(Cable(cid, circuit, frm, to, size, spec, prot, colour, path, od, **kw))

    # ---- shared legs
    BUS_UP = ["b_bus410", "b_rh_c", "b_rh_s", "b_rh_p", "b_x1", "b_x2", "b_x3"]        # busbar side -> tray front
    TO_CAB = ["t_ef", "t_er", "w_e1", "w_e2", "w_e3", "w_e4", "c_in"]                 # 12 V tray -> cabinet
    TO_CAB_LV = ["t_lf0", "t_lf", "t_lr", "w_l1", "w_l2", "w_l3", "c_lin", "c_l2"]    # 230 V tray -> RCBO side
    OUT_E = ["w_e2", "g_e1", "g_e2", "g_e3", "g_e4", "g_e5"]                          # 12 V wall channel -> rail
    OUT_L = ["w_l2", "w_l4", "g_l1", "g_l2", "g_l3", "g_l4", "g_l5"]
    CAB_UP = ["c_in", "w_e4", "w_e3", "w_e2"]                                         # cabinet -> wall channel (12 V)
    TO_GAP = ["ch_gap", "gp_e1", "gp_e2"]
    TO_ROOF = TO_GAP + ["gp_e3", "rf_1", "rf_2"]
    CB_IN = ["b_x1", "b_cb_hi", "b_cb_520"]
    # ---- battery bank (equal-length pairs, set after routing)
    for n in (1, 2):
        bp, bn = A[f"batt{n}_pos"], A[f"batt{n}_neg"]
        add(f"B{n}P", "Bank +", f"Battery {n} + (MRBF 300 A)", "Bank + busbar", "70", "70 mm2 tinned, red", "MRBF 300 A on terminal",
            "w_pos", [f"batt{n}_pos", (bp[0] + 35, bp[1], bp[2] + 6), (bp[0] + 35, 51, bp[2] + 6), (A["bus_bank_pos"][0], 51, bp[2] + 6),
                      (A["bus_bank_pos"][0], 30, A["bus_bank_pos"][2]), "bus_bank_pos"],
            od_of("single", 70), notes="cut B1P and B2P to the same length")
        add(f"B{n}N", "Bank -", f"Battery {n} -", "Bank - busbar", "70", "70 mm2 tinned, black", "-", "w_neg",
            [f"batt{n}_neg", (bn[0], bn[1], bn[2] + 25), (bn[0] + 50, bn[1], bn[2] + 25), (bn[0] + 50, 51, bn[2] - 30),
             (A["bus_bank_neg"][0], 51, bn[2] - 30), (A["bus_bank_neg"][0], 51, A["bus_bank_neg"][2]), (A["bus_bank_neg"][0], 30, A["bus_bank_neg"][2]),
             "bus_bank_neg"],
            od_of("single", 70), notes="cut B1N and B2N to the same length")
    # v0.13: main path 120 mm2 - the two 300 A MRBFs in parallel can deliver 600 A into it
    add("RB1", "Main +", "Bank + busbar", "Remote battery switch IN", "120", "120 mm2 tinned, red", "2 x MRBF 300 A upstream (parallel)",
        "w_pos", ["bus_bank_pos", (A["bus_bank_pos"][0], 45, A["bus_bank_pos"][2]), (A["bus_bank_pos"][0], 45, A["rbs_in"][2]),
                  (A["rbs_in"][0], 45, A["rbs_in"][2]), (A["rbs_in"][0], 30, A["rbs_in"][2]), "rbs_in"], od_of("single", 120))
    add("RB2", "Main +", "Remote battery switch OUT", "System + busbar", "120", "120 mm2 tinned, red", "-", "w_pos",
        ["rbs_out", (A["rbs_out"][0], A["rbs_out"][1] + 30, A["rbs_out"][2]), (A["rbs_out"][0], A["rbs_out"][1] + 30, A["bus_sys_pos"][2]),
         (A["bus_sys_pos"][0], A["rbs_out"][1] + 30, A["bus_sys_pos"][2]), "bus_sys_pos"], od_of("single", 120))
    add("SH1", "Main -", "Bank - busbar", "SmartShunt (battery side)", "120", "120 mm2 tinned, black", "-", "w_neg",
        ["bus_bank_neg", (A["bus_bank_neg"][0], A["bus_bank_neg"][1] + 30, A["bus_bank_neg"][2]),
         (A["bus_bank_neg"][0], A["bus_bank_neg"][1] + 30, A["shunt"][2]), "shunt"], od_of("single", 120))
    add("SH2", "Main -", "SmartShunt (system side)", "System - busbar", "120", "120 mm2 tinned, black", "-", "w_neg",
        ["shunt_sys", (A["shunt_sys"][0], A["shunt_sys"][1] + 30, A["shunt_sys"][2]), (A["shunt_sys"][0], A["shunt_sys"][1] + 30, A["bus_sys_neg"][2] + 30),
         (A["bus_sys_neg"][0], A["shunt_sys"][1] + 30, A["bus_sys_neg"][2] + 30), "bus_sys_neg"], od_of("single", 120))
    add("CT1", "Inverter +", "System + busbar", "Class-T 400 A", "50", "2 x 50 mm2 tinned, red", "-", "w_pos",
        ["bus_sys_pos", (A["bus_sys_pos"][0], A["bus_sys_pos"][1] + 30, A["bus_sys_pos"][2]),
         (A["bus_sys_pos"][0], A["bus_sys_pos"][1] + 30, A["classT_in"][2]), (A["classT_in"][0], A["bus_sys_pos"][1] + 30, A["classT_in"][2]), "classT_in"],
        od_of("x2", 50), notes="Class-T holder on the board next to BB3: link under 200 mm, so it counts as at the source")
    add("INVP", "Inverter +", "Class-T 400 A", "MultiPlus-II DC +", "50", "2 x 50 mm2 tinned, red", "Class-T 400 A", "w_pos",
        ["classT_out", (A["classT_out"][0], 40, A["classT_out"][2]), (A["classT_out"][0], 40, 80), (A["inv_dc_pos"][0], 40, 80),
         (A["inv_dc_pos"][0], -20, 80), (A["inv_dc_pos"][0], -20, A["inv_dc_pos"][2]), "inv_dc_pos"],
        od_of("x2", 50), notes="through the board window; Victron: 2 x 50 mm2 per pole for 0-5 m")
    add("INVN", "Inverter -", "System - busbar", "MultiPlus-II DC -", "50", "2 x 50 mm2 tinned, black", "-", "w_neg",
        ["bus_sys_neg", (A["bus_sys_neg"][0], A["bus_sys_neg"][1], 72), (A["inv_dc_neg"][0], A["bus_sys_neg"][1], 72),
         (A["inv_dc_neg"][0], -20, 72), (A["inv_dc_neg"][0], -20, A["inv_dc_neg"][2]), "inv_dc_neg"], od_of("x2", 50))
    # ---- charger outputs (short, inside the bay): + to its MIDI on BB3, - to BB4
    for cid, src, term, fuse, size, spec, prot in (("ORO", "Orion XS 12/12-50A", "orion_out", "midi_orion", 16, "16 mm2 twin", "MIDI 70 A"),
                                                   ("MPR", "MPPT 100/30 (roof)", "mppt_roof_bat", "midi_mppt_roof", 16, "16 mm2 twin", "MIDI 40 A"),
                                                   ("MPT", "MPPT 75/15 (tent)", "mppt_tent_bat", "midi_mppt_tent", 6, "6 mm2 twin", "MIDI 40 A (shared with MPV)")):
        t, f = A[term], A[fuse]
        loom = ["b_cb_520", "b_cb_310", "b_cb_145", "b_cb_60"]
        node = "b_cb_520" if t[1] < -400 else ("b_cb_310" if t[1] < -220 else "b_cb_145")
        add(cid, "Charging output", src, "System +/- busbars (MIDI fuse)", str(size), spec, prot, "w_pos",
            [term, _up(term), (95, t[1], 288)] + loom[loom.index(node) + 1:] + ["f_p", "f_c", "f_lo", (f[0], 40, 110),
                                                                                (f[0], f[1] + 25, f[2]), fuse], od_of("twin", size))
    # v0.13: visor panel on its own MPPT 100/20 (U13), on the passenger face of the distribution board
    f = A["midi_mppt_tent"]
    add("MPV", "Charging output", "MPPT 100/20 (visor)", "System +/- busbars (MIDI fuse)", "6", "6 mm2 twin", "MIDI 40 A (shared with MPT)",
        "w_pos", ["mppt_visor_bat", _drop("mppt_visor_bat", 360), "b_rm_c", "b_bus360", "b_bus270", "b_bus190", "b_bus90",
                  (f[0] + 8, 62, 90), (f[0] + 8, f[1] + 30, f[2] - 20), "midi_mppt_tent"], od_of("twin", 6))
    # ---- bay -> rear control cabinet
    f = A["midi_fuses"]
    add("DCF", "DC distribution", "System + busbar (MEGA 100 A)", "Rear DC fuse block", "35", "35 mm2 twin (red/black)", "MEGA 100 A",
        "w_pos", ["midi_fuses", (f[0], f[1] + 30, f[2]), (f[0], 62, 90), "b_bus90", "b_bus190", "b_bus270", "b_bus360"] + BUS_UP + TO_CAB
        + ["c_r", "c_fb", (1140, -660, 240), "dc_fuse_block"], od_of("twin", 35), notes="v0.13: 35 mm2 (25 mm2 dropped 3.9 % at 100 A)")
    ia = A["inv_ac"]
    add("AC1", "AC out", "MultiPlus-II AC-out 1", "RCBO enclosure (Q0 main switch)", "4x3", "4 mm2 3-core flex (TPS-flex)",
        "MultiPlus internal limit + 15 A AC-in limit; Q0 2-pole main switch", "w_ac",
        ["inv_ac", (ia[0], ia[1] + 20, ia[2]), (ia[0], 62, ia[2]), "b_bus90", "b_bus190", "b_bus270", "b_bus360"] + BUS_UP[:-1]
        + ["b_x3"] + TO_CAB_LV + ["rcbo"], FLEX3[4], lv=True,
        notes="v0.13: 4 mm2 - with PowerAssist AC-out carries ~25 A (15 A shore + inverter); licensed electrician")
    add("AC2", "Rear GPO", "RCBO Q1", "Rear panel double GPO", "2.5x3", "2.5 mm2 3-core flex", "RCBO 10 A 30 mA", "w_ac",
        ["rcbo", (1330, -728, 200), (1330, -728, 127), "pc_gpo_double"], FLEX3[2.5], lv=True)
    add("AC3", "Slide GPO", "RCBO Q2", "Power-slide pod GPO", "2.5x3", "2.5 mm2 3-core high-flex (chain rated)", "RCBO 10 A 30 mA", "w_ac",
        ["rcbo", "c_l2", "c_lin", "w_l3", "w_l2", "w_l1", "t_lr", "t_lf", "t_lf0", "b_x3", "b_x2", "b_x1", "b_rh_p", "b_rh_s", "b_rl_s",
         "s_drop", "slide_entry", "chain_trunk_end", "chain_fixed", "chain_bend_fixed", "chain_bend_tip", "chain_moving", "pod_cable_in",
         "slide_bulkhead"], FLEX3[2.5], extra_mm=600, lv=True,
        notes="back to the bay in the tray's 230 V side, down behind the inverter, into the slide front; separator in the chain")
    add("AC4", "Tent heater GPO", "RCBO Q3", "Gap junction J1 -> tent services box outlet", "2.5x3", "2.5 mm2 3-core flex, UV rated",
        "RCBO 10 A 30 mA", "w_ac", ["rcbo", "c_l2", "c_lin", "w_l3", "w_l2"] + OUT_L[1:] + ["ch_l_gap", "gp_l1", "gp_l2", "gap_junction_lv"],
        FLEX3[2.5], lv=True, notes="orange conduit; detaches at J1 (IP66)")
    add("AC5", "Shore inlet", "Gap junction J2 (from the tent's 15 A inlet)", "MultiPlus-II AC-in", "2.5x3", "2.5 mm2 3-core flex (15 A)",
        "RCBO 16 A 30 mA 2-pole in the services box + MultiPlus AC-in limit 15 A", "w_ac",
        ["gap_junction_lv", "gp_l2", "gp_l1", "ch_l_gap"] + list(reversed(OUT_L)) + ["w_l1", "t_lr", "t_lf", "t_lf0", "b_x3", "b_x2", "b_x1",
                                                                                     "b_rh_p", "b_rh_s", "b_rh_c", "b_bus410", "b_bus360", "b_bus270", "b_bus190", "b_bus90",
                                                                                     (ia[0] + 12, 62, ia[2]), (ia[0] + 12, ia[1] + 20, ia[2]), "inv_ac"],
        FLEX3[2.5], lv=True)
    # PE2 (v0.13): dedicated earth from the RCBO enclosure earth bar to the chassis bond point (not via the DC negative)
    add("PE2", "AC earth to chassis", "RCBO enclosure earth bar", "Chassis bond point (passenger rail, near the gland)", "6",
        "6 mm2 green/yellow", "-", "w_pe", ["rcbo", (1300, -735, 240), "c_r", "c_in", "w_e4", "w_e3", "w_e2"] + OUT_E[1:] + [(1350, yr - 0, zr - 60)],
        od_of("single", 6), notes="electrician to confirm against AS/NZS 3001.2; bond point shared with CHB")
    # ---- 12 V outlets from FB1 (rear cabinet)
    pl = {"pc_anderson_1": "c_pl50", "pc_anderson_2": "c_pl50", "pc_usbc_1": "c_pl160", "pc_12v": "c_pl50"}
    for cid, circ, to, size, spec, prot in (("DO1A", "Rear Anderson 1", "pc_anderson_1", 6, "6 mm2 twin", "ATC 30 A"),
                                            ("DO1B", "Rear Anderson 2", "pc_anderson_2", 6, "6 mm2 twin", "ATC 30 A"),
                                            ("DO1C", "Rear USB-C x2", "pc_usbc_1", 4, "4 mm2 twin", "ATC 25 A"),
                                            ("DO1D", "Rear 12 V socket", "pc_12v", 4, "4 mm2 twin", "ATC 15 A")):
        seq = ["c_pl", "c_pl2", "c_pl215", "c_pl160", "c_pl115", "c_pl50"]
        seq = seq[:seq.index(pl[to]) + 1]
        t = A[to]
        add(cid, circ, "DC fuse block", f"Rear panel {circ.split('Rear ')[1]}", str(size), spec, prot, "w_12v",
            ["dc_fuse_block", (1140, -660, 240), "c_fb", "c_r"] + seq + [(1338, t[1], t[2]), (1352, t[1], t[2]), to], od_of("twin", size),
            notes="2 x Treklo dual USB-C 120 W (100 W PD + 20 W), U8 linked from U7 (DO1E)" if cid == "DO1C" else "")
    t1, t2 = A["pc_usbc_1"], A["pc_usbc_2"]
    add("DO1E", "Rear USB-C link", "USB-C U7 terminals", "USB-C U8 terminals", "4", "4 mm2 twin", "ATC 25 A (DO1C)", "w_12v",
        ["pc_usbc_1", (1350, t1[1] - 20, t1[2]), (1350, t2[1] - 20, t2[2]), "pc_usbc_2"], od_of("twin", 4),
        notes="v0.13: short link behind the panel, same size as DO1C")
    sp = A["bus_sys_pos_studs"]
    add("DO2", "Slide DC", "System + busbar spare stud (MRBF 30 A); - to the system - busbar", "Power-slide pod (FB2)", "6",
        "6 mm2 twin high-flex", "MRBF 30 A (F17); FB2: X3 20 A, X7 15 A", "w_12v",
        ["bus_sys_pos_studs", (sp[0], 62, sp[2]), "b_bus190", "b_bus90", "b_bus30", "b_rl_s", "s_drop", "slide_entry", "chain_trunk_end",
         "chain_fixed", "chain_bend_fixed", "chain_bend_tip", "chain_moving", "pod_cable_in", "slide_bulkhead"], od_of("twin", 6), extra_mm=600,
        notes="fed in the bay; down the riser and the low rear channel into the slide front; chain under the deck")
    add("DO3", "Cabin compute feed", "DC fuse block", "Compute box SB50 inlet (under the rear seat)", "6", "6 mm2 twin",
        "ATC 15 A (+ BatteryProtect and per-device fuses in the box)", "w_12v",
        ["dc_fuse_block", (1140, -660, 240), "c_fb", "c_r", "c_in", "w_e4", "w_e3", "w_e2"] + OUT_E[1:] + ["ch_gap", "ch_cab", "cb_1", "cb_2", "cb_3",
                                                                                                    (-760, -440, 20), "cabin_compute_in"],
        od_of("twin", 6), notes="HA PC, router, PoE switch (docs/smart-ute-research.md); no outlets in the cabin")
    add("DO4", "Starlink Mini", "DC fuse block", "Starlink Mini (roof)", "4", "4 mm2 twin + DC barrel lead", "ATC 7.5 A", "w_12v",
        ["dc_fuse_block", (1140, -660, 240), "c_fb", "c_r", "c_in", "w_e4", "w_e3", "w_e2"] + OUT_E[1:] + TO_ROOF + ["rf_3", "rf_4",
                                                                                                             (xem_ := P.PLAT_X0 + P.PLAT_L - 40, -350, P.PLAT_Z + P.PLAT_T / 2), "starlink"],
        od_of("twin", 4), notes="v0.13: 7.5 A protects the barrel lead (was 10 A)")
    add("DO5", "Tent 12 V", "DC fuse block", "Gap junction J3 -> tent (SB50 red)", "10", "10 mm2 twin", "ATC 20 A", "w_12v",
        ["dc_fuse_block", (1140, -660, 240), "c_fb", "c_r", "c_in", "w_e4", "w_e3", "w_e2"] + OUT_E[1:] + TO_GAP + ["gap_junction_elv"],
        od_of("twin", 10), notes="v0.13: 10 mm2 / 20 A (6 mm2 at 30 A dropped 11 % over DO5 + T1D); detaches at J3")
    # ---- charging inputs: in through the gland, forward along the tray, down the charging-board loom
    TRAY_TO_CB = ["c_in", "w_e4", "w_e3", "w_e2", "w_e1", "t_er", "t_ef", "b_x3", "b_x2", "b_x1", "b_cb_hi", "b_cb_520"]
    IN_E = ["g_e5", "g_e4", "g_e3", "g_e2", "g_e1", "w_e2", "w_e1", "t_er", "t_ef", "b_x3", "b_x2", "b_x1", "b_cb_hi", "b_cb_520"]
    add("ALT", "Alternator charge", "Start battery + (F8 MIDI 60 A); - to the body earth", "Orion XS input", "25", "25 mm2 twin (+/-), tinned",
        "MIDI 60 A at the start battery", "w_pos", ["start_battery_pos", (A["start_battery_pos"][0], yr, 250), "en_2", "en_1", "ch_eng", "ch_cab", "ch_gap"]
        + IN_E + [_up("orion_in"), "orion_in"], od_of("twin", 25),
        notes="Orion input limit 25-30 A until the alternator rating is known; land the - on the body earth (chassis side of the battery sensor)")
    add("IGN", "Orion ignition sense", "Engine-bay fuse box (add-a-fuse, ignition)", "Orion XS remote H", "1.0", "1.0 mm2 single",
        "ATC 2 A add-a-fuse", "w_data", ["engine_fusebox", (A["engine_fusebox"][0], yr, 250), "en_2", "en_1", "ch_eng", "ch_cab", "ch_gap"]
        + IN_E + [_up("orion_remote", 0), "orion_remote"], od_of("single", 1.0),
        notes="engine-run signal; also feeds the visor interlock (VIG)")
    add("PVR", "Roof PV", "Roof panels PV1 + PV2 (parallel, MC4 Y-branch)", "QP1 -> MPPT 100/30 PV in", "10", "10 mm2 solar pair (UV)",
        "2-pole DC PV isolator QP1 32 A", "w_pv",
        ["roof_pv", (xem_, 30, P.PLAT_Z + P.PLAT_T / 2), "rf_5", "rf_4", "rf_3", "rf_2", "rf_1", "gp_e3", "gp_e2", "gp_e1", "ch_gap"] + IN_E
        + ["b_cb_310", _up("mppt_roof_pv"), "mppt_roof_pv"], od_of("pv2", 10),
        notes="v0.13: two panels only (visor has its own MPPT), 10 mm2 for the ~7 m run")
    add("PVT", "Tent PV", "Gap junction J4 (from the tent panels)", "QP2 -> MPPT 75/15 PV in", "6", "6 mm2 solar pair (UV)",
        "2-pole DC PV isolator QP2 32 A", "w_pv", ["gap_junction_elv", "gp_e2", "gp_e1", "ch_gap"] + IN_E + ["b_cb_310", "b_cb_145",
                                                                                                         _up("mppt_tent_pv"), "mppt_tent_pv"],
        od_of("pv2", 6), notes="detaches at J4")
    add("PVS", "Visor PV", "U11 box (MC4 couplers at the visor chain end)", "QP3 -> MPPT 100/20 (visor) PV in", "6", "6 mm2 solar pair (UV)",
        "2-pole DC PV isolator QP3 32 A", "w_pv",
        ["visor_ctrl", (P.PLAT_X0 + P.PLAT_L - 20, -640, P.PLAT_Z - 15), "rf_2", "rf_1", "gp_e3", "gp_e2", "gp_e1", "ch_gap"] + IN_E[:-2] + [(185, -80, 410), (A["mppt_visor_pv"][0], -80, 410), (A["mppt_visor_pv"][0], -80, 370), _drop("mppt_visor_pv", 370),
                 "mppt_visor_pv"],
        od_of("pv2", 6), notes="v0.13: visor on its own MPPT (panel voltage independent of PV1/PV2)")
    # ---- control + comms
    S1 = ["b_bus410", "b_rh_c", "b_rh_s", "b_rh_p", "b_x1", "b_x2", "b_x3"]
    add("SW1", "Battery switch control", "Rear panel ML-RBS switch (Blue Sea 2155)", "ML-RBS control harness", "data",
        "4-core 1.0 mm2 (+12 V feed, control, LED, ground)", "2 A inline at bank + (RBF)", "w_data",
        ["pc_sw_battery", (1352, A["pc_sw_battery"][1], A["pc_sw_battery"][2]), "c_pl215", "c_pl2", "c_pl", "c_r", "c_in"] + TRAY_TO_CB[1:8]
        + list(reversed(S1)) + ["b_bus360", (A["rbs_ctrl"][0], 45, 360), (A["rbs_ctrl"][0], 45, A["rbs_ctrl"][2]), "rbs_ctrl"],
        od_of("4c1.0"), notes="switch feed taken from the battery side so the RBS can be closed again")
    add("RBF", "Battery switch control", "Bank + busbar", "ML-RBS control feed (inline 2 A)", "data", "1.0 mm2 red", "ATC 2 A inline",
        "w_data", ["bus_bank_pos", (A["bus_bank_pos"][0] - 20, 45, A["bus_bank_pos"][2]), (A["rbs_ctrl"][0], 45, A["rbs_ctrl"][2]), "rbs_ctrl"],
        od_of("single", 1.0))
    # v0.14: the Victron temperature sensor replaces the plain Vbatt+ lead - its lug (sensor inside) goes on battery 1's +
    # post under the MRBF, red to Vbatt+ (fused in the lead), black to Aux (set to 'temperature'); DVCC shares it
    sv = A["shunt_vbatt"]
    add("TS1", "Shunt sense + battery temperature", "Battery 1 + post (lug with sensor, under the MRBF)", "SmartShunt Vbatt+ and Aux",
        "data", "Victron temperature sensor lead (2-core, supplied)", "fuse in the lead (supplied)", "w_data",
        ["batt1_pos_post", (240, A["batt1_pos_post"][1] - 4, 500), (240, 45, 500), (sv[0], 45, 500), (sv[0], 45, sv[2]), "shunt_vbatt"],
        od_of("2c0.75"), notes="v0.14: replaces the Vbatt+ lead; chargers' low-temperature cut-off +3 C via DVCC")
    # v0.14 battery heater: BB3 -> F18 10 A inline -> TH1 (thermostat + relay, behind the batteries) -> HP1/HP2
    bs, hc = A["bus_sys_pos"], A["bay_heater_ctrl"]
    add("HTR", "Battery heater feed", "System + busbar (F18 10 A inline); - to the system - busbar", "Heater controller TH1",
        "2.5", "2.5 mm2 twin", "ATC 10 A inline (F18)", "w_12v",
        ["bus_sys_pos", (bs[0], 62, bs[2]), "b_bus270", "b_bus360", "b_bus410", (rch, 62, 450), (hc[0], 62, 450), (hc[0], hc[1], 450),
         "bay_heater_ctrl"], od_of("twin", 2.5), notes="v0.14: after the remote switch, so it is off when the bank is isolated")
    ho, hp = A["bay_heater_out"], A["bay_heater_pads"]
    add("HTP", "Battery heater pads", "Heater controller TH1 (relay out)", "Heater pads HP1 + HP2 (between the batteries)", "1.5",
        "1.5 mm2 twin (silicone)", "F18 (upstream); 50 C cut-out on each pad", "w_12v",
        ["bay_heater_out", (ho[0], ho[1], 415), (hp[0], hp[1], 415), "bay_heater_pads"], od_of("twin", 1.5),
        notes="v0.14: through the notch in the rear foam, down the gap between the batteries' lids")
    hq, pr = A["bay_heater_probe_out"], A["bay_heater_probe"]
    add("HTS", "Battery heater probe", "Heater controller TH1 (sensor in)", "NTC probe on battery 2 (lid face, mid-height)", "data",
        "NTC probe lead (supplied, 2-core)", "-", "w_data",
        ["bay_heater_probe_out", (hq[0], hq[1], 415), (pr[0] + 6, hq[1], 415), (pr[0] + 6, hq[1], pr[2]), (pr[0] + 6, pr[1], pr[2]),
         "bay_heater_probe"], od_of("2c0.75"), notes="v0.14: the outer (colder) battery; behind the rear foam, clear of the pads")
    fan = A["inv_fan"]
    add("FAN", "Inverter fan", "System + busbar (inline 5 A)", "92 mm thermostatic fan", "1.5", "1.5 mm2 twin", "ATC 5 A inline", "w_12v",
        ["bus_sys_pos", (A["bus_sys_pos"][0], 62, A["bus_sys_pos"][2]), "b_bus270", "b_bus360", "b_bus410", "b_rh_c",
         (rch, fan[1], 410), (fan[0], fan[1], 410), "inv_fan"], od_of("twin", 1.5))
    add("CGX", "Cerbo GX power", "DC fuse block", "Cerbo GX power in", "0.75", "0.75 mm2 twin", "ATC 2 A", "w_12v",
        ["dc_fuse_block", (1140, -660, 240), "c_fb", "c_cg", (955, -660, 240), "cerbo"], od_of("twin", 0.75))
    add("PE1", "Inverter case earth", "MultiPlus-II chassis earth stud", "System - busbar", "50", "50 mm2 green/yellow", "-", "w_pe",
        ["inv_chassis_earth", (45, -24, A["inv_chassis_earth"][2]), (45, -24, 92), (45, 45, 92), (A["bus_sys_neg"][0] + 20, 45, 92),
         (A["bus_sys_neg"][0] + 20, A["bus_sys_neg"][1], 92), "bus_sys_neg"], od_of("single", 50),
        notes="Victron: case to the DC negative, same size as the DC negative; AC earth bar bonds the chassis separately (PE2)")
    add("CHB", "Chassis bond", "System - busbar", "Chassis bond point (passenger rail, near the gland)", "25", "25 mm2 black", "-", "w_neg",
        ["bus_sys_neg_studs", (A["bus_sys_neg_studs"][0], 62, 60), "b_bus90", "b_bus190", "b_bus270", "b_bus360"] + BUS_UP
        + ["t_ef", "t_er", "w_e1", "w_e2"] + OUT_E[1:] + [(1350, yr, zr - 60)], od_of("single", 25),
        notes="single DC-negative bond to the vehicle chassis, shared stud with PE2")
    add("SW2", "Inverter remote on/off", "Rear panel switch S2", "MultiPlus-II remote terminals", "data", "2-core 0.75 mm2", "-", "w_data",
        ["pc_sw_inverter", (1352, A["pc_sw_inverter"][1], A["pc_sw_inverter"][2]), "c_pl215", "c_pl2", "c_pl", "c_r", "c_in"] + TRAY_TO_CB[1:8]
        + list(reversed(S1)) + ["b_bus360", "b_bus270", "b_bus190", "b_bus90", (rch - 20, 62, 100), (A["inv_remote"][0], 62, 100),
                                (A["inv_remote"][0], A["inv_remote"][1] + 20, 100), "inv_remote"], od_of("2c0.75"))
    COMMS = ["cerbo", (955, -660, 240), "c_cg", "c_fb", "c_r", "c_in"] + TRAY_TO_CB[1:8] + list(reversed(S1))
    add("D1", "VE.Bus", "Cerbo GX", "MultiPlus-II", "data", "RJ45 VE.Bus cable", "-", "w_data",
        COMMS + ["b_bus360", "b_bus270", "b_bus190", "b_bus90", (rch - 20, 62, 100), (A["inv_comms"][0], 62, 100), (A["inv_comms"][0], A["inv_comms"][1] + 20, 100),
                 "inv_comms"], od_of("vebus"))
    add("D2", "VE.Direct", "Cerbo GX VE.Direct 1-3", "SmartShunt / MPPT 100/30 / MPPT 75/15", "data", "VE.Direct cables x3", "-", "w_data",
        COMMS[:-4] + ["b_cb_hi", "b_cb_520", "b_cb_310", (95, A["mppt_roof_100_30"][1], 282), _up("mppt_roof_100_30", -6),
                      "mppt_roof_100_30"], od_of("vedirect", 3),
        notes="three cables: shunt (branches at the riser), roof MPPT, tent MPPT")
    add("D4", "VE.Direct", "Cerbo GX USB 1", "Orion XS VE.Direct", "data", "VE.Direct to USB interface", "-", "w_data",
        COMMS[:-4] + CB_IN[1:] + [(95, A["orion_xs_50a"][1], 282), _up("orion_xs_50a", -6), "orion_xs_50a"], od_of("usb"), notes="Cerbo GX MK2 has only 3 VE.Direct ports")
    add("D5", "VE.Direct", "Cerbo GX USB 2", "MPPT 100/20 (visor) VE.Direct", "data", "VE.Direct to USB interface", "-", "w_data",
        COMMS[:-4] + [(185, -80, 410), (A["mppt_visor"][0] + 20, -80, 410), (A["mppt_visor"][0] + 20, -80, 370),
                      (A["mppt_visor"][0] + 20, -45, 370), "mppt_visor"], od_of("usb"),
        notes="v0.13: fourth Victron charger")
    add("D3", "Display", "Cerbo GX (HDMI + USB)", "GX Touch 50", "data", "GX Touch cable (HDMI + USB)", "-", "w_data",
        ["cerbo", (955, -660, 240), "c_cg", "c_fb", "c_r", "c_pl", "c_pl2", "c_pl215", (1338, A["pc_gx_touch_50"][1], A["pc_gx_touch_50"][2]),
         "pc_gx_touch_50"], od_of("hdmi"))
    # ---- windscreen visor (v0.11): feeds up to U11 on the roof
    add("PVV", "Visor PV (moving)", "Visor panel junction box", "U11 box (MC4 couplers)", "4", "4 mm2 solar pair, high-flex (chain rated)",
        "-", "w_pv", ["visor_pv_rear", (A["visor_pv_rear"][0], -532, 968), (-370, -532, 968), (-370, -590, 968),
                      (A["visor_ctrl_side"][0], -590, 968), "visor_ctrl_side"], od_of("pv2", 4), extra_mm=1600,
        notes="runs in the small igus chain beside the passenger guide rail (1.6 m extra in the chain)")
    add("VIS", "Visor drive power", "DC fuse block (way 10)", "Visor controller U11 (roof)", "10", "10 mm2 twin", "ATC 20 A", "w_12v",
        ["dc_fuse_block", (1140, -660, 240), "c_fb", "c_r", "c_in", "w_e4", "w_e3", "w_e2"] + OUT_E[1:] + TO_ROOF + ["visor_ctrl"],
        od_of("twin", 10), notes="v0.13: 10 mm2 (6 mm2 dropped 4.6 %); per-channel fuses inside U11")
    add("VSW", "Visor control", "Rear panel visor button (S3)", "Visor controller U11 (roof)", "data", "4-core 0.75 mm2 (deploy, stow, LED, common)",
        "-", "w_data", ["pc_sw_inverter", (1352, A["pc_sw_inverter"][1] + 12, A["pc_sw_inverter"][2]), "c_pl215", "c_pl2", "c_pl", "c_r", "c_in",
                        "w_e4", "w_e3", "w_e2"] + OUT_E[1:] + TO_ROOF + ["visor_ctrl"], od_of("4c0.75"),
        notes="v0.13: 4-core (the switch and LED need a common)")
    add("VIG", "Visor interlock", "Orion XS remote H (ignition, F9)", "Visor controller interlock input", "data", "1.0 mm2 single",
        "F9 2 A (shared)", "w_data", ["orion_remote", _up("orion_remote", 4), "b_cb_520", "b_cb_hi", "b_x1", "b_x2", "b_x3", "t_ef", "t_er", "w_e1", "w_e2"]
        + OUT_E[1:] + TO_ROOF + ["visor_ctrl"], od_of("single", 1.0), notes="ignition on = deploy inhibited, warning if not stowed")
    # ---- detachable tent harnesses (tent side) - v0.13: 230 V and 12 V in separate sheaths
    add("T1A", "Tent harness 230 V", "Tent services box (heater outlet + shore inlet)", "Gap junction J1 + J2", "2.5x3",
        "2 x 2.5 mm2 3-core flex, sheathed together, UV rated", "Q4 2-pole RCBO 16 A (AC-in); Q3 (AC-out)", "w_tent",
        ["tent_services_a", "tn_a1", "tn_a2", "tn_a3", "tn_a4", "tn_a5", "gap_junction_top_lv"], (FLEX3[2.5], 2), side="tent", lv=True,
        notes="stays with the tent; 230 V only")
    add("T1D", "Tent harness 12 V + PV", "Tent services box (SB50 + PV bulkhead)", "Gap junction J3 + J4", "10",
        "10 mm2 twin (12 V) + 6 mm2 solar pair (PV), sheathed together", "DO5 20 A (12 V)", "w_tent",
        ["tent_services_d", "tn_d1", "tn_d2", "tn_d3", "tn_d4", "tn_d5", "gap_junction_top_elv"],
        16.5, side="tent", notes="stays with the tent; 12 V and PV only")
    hf = A["tent_hinge_front"]
    jb = A["tent_pv_jbox"]
    add("T2", "Tent PV harness", "Tent-top junction box (PV3 + PV4 in series)", "Services box PV bulkhead", "6", "6 mm2 solar pair (UV)", "-",
        "w_tent", ["tent_pv_jbox", (jb[0], hf[1] + 8, jb[2]), (hf[0], hf[1] + 8, jb[2]), (hf[0], hf[1] + 8, hf[2] + 20),
                   (hf[0], hf[1] + 8, 770), (A["tent_services_pv"][0], hf[1] + 8, 770),
                   (A["tent_services_pv"][0], hf[1] + 8, A["tent_services_pv"][2]), "tent_services_pv"], od_of("pv2", 6), side="tent",
        notes="v0.13: crosses to the base at the front hinge with a service loop, so opening the shell never pulls on it")
    # v0.14: water-can pad, fed from the tent services box (T1D / DO5 12 V): F19 5 A + thermostat TH2 inside the box
    sw_, wp = A["tent_services_w"], A["water_heat_pad"]
    add("WHT", "Water can heater", "Tent services box (F19 5 A + thermostat TH2)", "Water can pad HP3 (under the can)", "1.5",
        "1.5 mm2 twin (silicone), plug-in", "ATC 5 A (F19) in the services box; 45 C cut-out on the pad", "w_tent",
        ["tent_services_w", (sw_[0], 110, sw_[2]), (wp[0], 110, wp[2] + 1), (wp[0], wp[1], wp[2] + 1), "water_heat_pad"],
        od_of("twin", 1.5), side="tent", notes="v0.14: on the lid top under the jacket's end; nothing passes through the lid")
    _match(L, ("B1P", "B2P"), ("B1N", "B2N"))
    return L


def _match(L, *pairs):
    by = {c.cid: c for c in L}
    route(L)
    for pair in pairs:
        cs = [by[c] for c in pair]
        m = max(c.run_mm() for c in cs)
        for c in cs:
            c.extra_mm += (m - c.run_mm()) * 1.10


# ================================================================== routing: lanes + polylines
def _edge_index():
    idx = {}
    for r in RUNS:
        for a, b in zip(r.nodes[:-1], r.nodes[1:]):
            idx[(a, b)] = idx[(b, a)] = r
    return idx


def _unit(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def _mul(a, k):
    return tuple(x * k for x in a)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


AX = {"x": (1.0, 0.0, 0.0), "y": (0.0, 1.0, 0.0), "z": (0.0, 0.0, 1.0)}


def _frame(run, d):
    """Cross-section axes for a segment direction d: u along the first of the run's `wide` axes that is not the segment
    direction (then z, y, x), v = d x u. Returns (u, v, axis letter of u)."""
    for k in run.wide + "xyz":
        w = AX[k]
        u = _sub(w, _mul(d, _dot(w, d)))
        if math.sqrt(_dot(u, u)) > 0.7:
            break
    u = _unit(u)
    v = _unit(_cross(d, u))
    return u, v, k


def _width(run, k):
    return run.width.get(k, max(run.width.values())) if isinstance(run.width, dict) else run.width


def _pack(run, cabs, width):
    """Shelf-pack the run's cables (biggest first) across `width`; returns {cid: (a, b)} centred on the run line."""
    order = sorted(cabs, key=lambda c: (-c.h, -c.w, c.cid))
    rows, cur, wcur = [], [], 0.0
    for c in order:
        if cur and wcur + c.w > width:
            rows.append(cur)
            cur, wcur = [], 0.0
        cur.append(c)
        wcur += c.w + 1.0
    if cur:
        rows.append(cur)
    hts = [max(c.h for c in r) + 1.0 for r in rows]
    tot_h = sum(hts)
    out, b0 = {}, -tot_h / 2
    for r, h in zip(rows, hts):
        wrow = sum(c.w + 1.0 for c in r) - 1.0
        a = -wrow / 2
        for c in r:
            out[c.cid] = (a + c.w / 2, b0 + h / 2)
            a += c.w + 1.0
        b0 += h
    size = max(max(sum(c.w + 1.0 for c in r) - 1.0 for r in rows), tot_h) if rows else 0.0
    run.size_mm = max(run.size_mm, size)
    return out


def _xyz(p):
    if isinstance(p, str):
        return NODES.get(p) or ANCHORS[p]
    return tuple(float(v) for v in p)


def route(L):
    idx = _edge_index()
    for r in RUNS:
        r.members = []
    for c in L:
        c.path = [p for k, p in enumerate(c.path) if k == 0 or p != c.path[k - 1]]
        c.runs = []
        for a, b in zip(c.path[:-1], c.path[1:]):
            if isinstance(a, str) and isinstance(b, str) and (a, b) in idx:
                r = idx[(a, b)]
                if c not in r.members:
                    r.members.append(c)
                if not c.runs or c.runs[-1] != r.code:
                    c.runs.append(r.code)
    for r in RUNS:
        r.size_mm = 0.0
        ks = set(r.wide) | set("xyz")
        r.slots = {k: _pack(r, r.members, _width(r, k)) for k in ks}
    for c in L:
        c.pts = _polyline(c, idx, 0.0)
        c.core_pts = [_polyline(c, idx, s * (c.d1 + 1.0) / 2) for s in (-1, 1)] if c.cores == 2 else []


def _polyline(c, idx, da):
    """Polyline of cable c with its lane slot shifted by da across the lane (for the cores of a twin)."""
    if True:
        base = [_xyz(p) for p in c.path]
        offs = []
        for j, (a, b) in enumerate(zip(c.path[:-1], c.path[1:])):
            r = idx.get((a, b)) if isinstance(a, str) and isinstance(b, str) else None
            if r is None:
                offs.append(None)
                continue
            d = _unit(_sub(base[j + 1], base[j]))
            u, v, k = _frame(r, d)
            sa, sb = r.slots[k][c.cid]
            offs.append((_add(_mul(u, sa + da), _mul(v, sb)), d))
        pts = [_add(base[0], offs[0][0]) if offs[0] else base[0]]
        for j in range(1, len(base) - 1):
            oi, oo = offs[j - 1], offs[j]
            n = base[j]
            if oi is None and oo is None:
                pts.append(n)
            elif oi is None:
                pts.append(_add(n, oo[0]))
            elif oo is None:
                pts.append(_add(n, oi[0]))
            else:
                (o1, d1), (o2, d2) = oi, oo
                p1 = _add(_add(n, o1), _mul(d1, _dot(o2, d1)))
                p2 = _add(_add(n, o2), _mul(d2, _dot(o1, d2)))
                pts.append(p1)
                if math.dist(p1, p2) > 0.5:
                    pts.append(p2)
        last = offs[-1]
        pts.append(_add(base[-1], last[0]) if last else base[-1])
        clean = []
        for q in pts:
            if not clean or math.dist(q, clean[-1]) > 1.0:
                clean.append(q)
        return clean


# ================================================================== fill / conduit sizing
CONDUIT_IDS = (10, 13, 16, 20, 25, 32, 40, 50)


def run_fill(r):
    """Cable cross-section area, chosen conduit ID (split corrugated, <= 50 % fill when laid in) and the fill."""
    area = sum(math.pi / 4 * c.od ** 2 for c in r.members)
    need = math.sqrt(area / 0.50 * 4 / math.pi)
    cid = next((d for d in CONDUIT_IDS if d >= need), None)
    fill = area / (math.pi / 4 * cid ** 2) if cid else None
    return area, cid, fill


# ================================================================== build
CONDUIT_ELV = (35, 35, 38, 120)
CONDUIT_LV = (235, 120, 30, 140)
LOOM = (40, 40, 45, 150)
CLIP = (25, 25, 28, 255)
GROMMET = (20, 20, 22, 255)


def _seg_points(a, b, step):
    L_ = math.dist(a, b)
    n = int(L_ // step)
    return [tuple(a[i] + (b[i] - a[i]) * (k + 0.5) / max(n, 1) for i in range(3)) for k in range(max(n, 1))] if n else []


def build():
    parts = []
    cl = cables()
    for c in cl:
        grp = "tent_harness" if c.side == "tent" else "wiring"
        if c.cores == 2:
            neg = "w_neg" if c.colour in ("w_pos", "w_12v", "w_pv") and c.cid not in ("CT1", "INVP", "INVN") else c.colour
            for k, (pts, col) in enumerate(zip(c.core_pts, (c.colour, neg))):
                parts.append(Part(f"cable_{c.cid}" + ("" if k == 0 else "_2"), grp, color=C[col], tube=pts, tube_r=c.d1 / 2,
                                  meta=dict(cable=c) if k == 0 else {}))
        else:
            parts.append(Part(f"cable_{c.cid}", grp, color=C[c.colour], tube=c.pts, tube_r=min(c.d1 / 2, 11.0), meta=dict(cable=c)))
    # containment: conduits / looms (see-through) with P-clips, and grommets where bundles pass a panel
    for r in RUNS:
        if r.kind not in ("conduit", "lv_conduit", "loom") or not r.members:
            continue
        _, cid, _ = run_fill(r)
        rad = max((cid or 50) / 2 + 2, r.size_mm / 2 + 2)
        col = CONDUIT_LV if r.kind == "lv_conduit" else (LOOM if r.kind == "loom" else CONDUIT_ELV)
        pts = [NODES[n] for n in r.nodes]
        parts.append(Part(f"route_{r.code}_{r.kind}", "routing", color=col, tube=pts, tube_r=rad,
                          meta=dict(run=r.code, conduit_id=cid)))
        if r.clip:
            for k, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
                d = _unit(_sub(b, a))
                for m, q in enumerate(_seg_points(a, b, r.clip)):
                    parts.append(Part(f"route_{r.code}_clip_{k}_{m}", "routing", color=CLIP,
                                      tube=[_sub(q, _mul(d, 7)), _add(q, _mul(d, 7))], tube_r=rad + 2.5))
    rmap = {r.code: r for r in RUNS}
    idx = _edge_index()
    for name, a, b, extra in GROMMETS:
        r = idx[(a, b)]
        pa, pb = NODES[a], NODES[b]
        d = _unit(_sub(pb, pa))
        q = _add(pb, _mul(d, -min(20.0, math.dist(pa, pb) / 2)))
        parts.append(Part(f"route_grommet_{name}", "routing", color=GROMMET, tube=[_sub(q, _mul(d, 5)), _add(q, _mul(d, 5))],
                          tube_r=rmap[r.code].size_mm / 2 + extra + 3))
    # gap junction box (vehicle side) between cab and tub, passenger front corner; v0.13: internal barrier 230 V | 12 V
    gx = P.CAB_REAR_X + 28
    parts.append(part("gap_junction_box", "electrical", box(gx - 20, gx + 20, -790, -610, 360, 535), "victron_dark", kg=1.8,
                      note="IP66, barrier between the 230 V side (J1, J2) and the 12 V side (J3, J4, roof pass-throughs)"))
    return parts, cl


def junction_anchors():
    """Connector faces on the junction box (called before cables())."""
    gx = P.CAB_REAR_X + 28
    anchor("gap_junction_lv", (gx, -745, 380))
    anchor("gap_junction_elv", (gx, -650, 380))
    anchor("gap_junction_top_lv", (gx, -745, 535))
    anchor("gap_junction_top_elv", (gx, -650, 535))
