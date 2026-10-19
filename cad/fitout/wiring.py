"""
Cable routing and schedule.

Every cable is a polyline through named anchors (set by the other modules) and shared trunk
waypoints, so its modelled length is real. All cables that leave the tub pass through the factory
240 V outlet hole (passenger rear wall), run along the passenger chassis rail and branch to the
engine bay, the cabin (under the rear seat) and the cab-tub gap junction box (tent + roof).
"""
from dataclasses import dataclass

import params as P

from .core import ANCHORS, C, Part, anchor, box, part

# conductor size -> render radius (mm)
RADIUS = {"120": 10.5, "70": 9, "50": 8, "25": 6.5, "16": 5.5, "6": 4.5, "4": 4, "2.5x3": 5, "data": 2.5}


@dataclass
class Cable:
    cid: str
    circuit: str
    frm: str
    to: str
    size: str              # mm2 key in RADIUS
    spec: str              # conductor / type description
    protection: str
    colour: str            # key in C
    path: list             # anchors (str) or xyz tuples
    side: str = "vehicle"  # 'vehicle' or 'tent' (detachable tent harness)
    extra_mm: float = 0.0  # e.g. length inside the cable chain
    notes: str = ""

    def points(self, k=0):
        pts = []
        for i, p in enumerate(self.path):
            xyz = ANCHORS[p] if isinstance(p, str) else p
            if 0 < i < len(self.path) - 1:      # offset interior points so bundled cables don't overlap
                xyz = (xyz[0] + (k % 4) * 6, xyz[1] + (k % 3) * 7, xyz[2] + (k % 5) * 6)
            q = tuple(float(v) for v in xyz)
            if not pts or sum((u - v) ** 2 for u, v in zip(q, pts[-1])) > 1.0:
                pts.append(q)
        return pts

    def length_m(self):
        pts = self.points()
        run = sum(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5 for a, b in zip(pts[:-1], pts[1:]))
        return round((run * 1.10 + 300 + self.extra_mm) / 1000, 2)   # +10 % slack, +0.3 m terminations


def trunks():
    """Shared waypoints (tub frame, mm)."""
    hw = P.TUB_W / 2
    ow = hw + P.TUB_WALL_T
    fx, _, fz = P.FACTORY_OUTLET
    gx = P.CAB_REAR_X + 28                     # centre of the cab-tub gap
    w = dict(
        bay_top=(P.BAY_D - 15, -P.BAY_W / 2 + 60, P.BAY_H - 15),
        dist_top=(200, ANCHORS["bus_pos"][1], P.BAY_H - 15),
        arch_run0=(P.BAY_D - 15, -P.POCKET_Y_IN - 40, P.TOP_Z - 20),
        arch_run1=(P.POCKET_X0 + 30, -P.POCKET_Y_IN - 40, P.TOP_Z - 20),
        cab_in=(P.POCKET_X0 + 120, -P.POCKET_Y_IN - 60, P.TOP_Z - 30),
        gland_in=(fx, -hw + 20, fz),
        cab_floor=(P.POCKET_X0 + 200, -P.POCKET_Y_IN - 40, 30),
        under_slide=(P.POCKET_X0 + 120, -P.POCKET_Y_IN + 10, 12),
        wall_out=(fx, -ow - 12, fz),
        wall_low=(fx, -ow - 12, -60),
        chassis_rear=(fx, -(P.CHASSIS_RAIL_Y + 45), P.CHASSIS_Z - 20),
        chassis_gap=(gx, -(P.CHASSIS_RAIL_Y + 45), P.CHASSIS_Z - 20),
        chassis_cabin=(P.CABIN_SEAT_BOX[0], -(P.CHASSIS_RAIL_Y + 45), P.CHASSIS_Z - 20),
        cabin_grommet=(P.CABIN_SEAT_BOX[0], P.CABIN_SEAT_BOX[1], -40),
        chassis_engine=(P.ENGINE_BAY_BATT[0] + 250, -(P.CHASSIS_RAIL_Y + 45), P.CHASSIS_Z - 20),
        engine_up=(P.ENGINE_BAY_BATT[0] + 250, P.ENGINE_BAY_BATT[1], P.ENGINE_BAY_BATT[2] + 140),
        gap_low=(gx, -700, 120),
        junction_bot=(gx, -700, 360),
        junction_top=(gx, -700, 535),
        gap_high=(gx, -560, P.ROOF_Z - 80),
        lid_front=(gx, -515, P.LID_TOP_Z + 60),
    )
    for k, v in w.items():
        anchor(k, v)


def _drop(a, z=None, dy=0):
    """Waypoint on the arch run directly above/below an anchor."""
    x, y, zz = ANCHORS[a]
    return (x, -P.POCKET_Y_IN - 40 + dy, P.TOP_Z - 20 if z is None else z)


# outside-the-tub legs
OUT = ["gland_in", "wall_out", "wall_low", "chassis_rear"]
INSIDE_TO_BOARD = ["bay_top", "arch_run0"]


def cables():
    trunks()
    to_gap = OUT + ["chassis_gap", "gap_low", "junction_bot"]
    cab_to_gland = ["cab_in", "gland_in"]
    L = []
    # ------------------------------------------------ battery bank (inside the bay)
    for n in (1, 2):
        bp, bn = ANCHORS[f"batt{n}_pos"], ANCHORS[f"batt{n}_neg"]
        L.append(Cable(f"B{n}P", "Battery bank +", f"Battery {n} +", f"Class-T 400 A #{n}", "120", "120 mm2 tinned, red", "Class-T 400 A (Blue Sea 5502)",
                       "w_pos", [f"batt{n}_pos", (bp[0] + 40, bp[1], bp[2]), (bp[0] + 40, ANCHORS[f"classT_{n}_in"][1] + 40, bp[2]), f"classT_{n}_in"],
                       notes="keep both battery cables equal length"))
        L.append(Cable(f"F{n}", "Battery bank +", f"Class-T 400 A #{n}", "Isolator (common stud)", "120", "120 mm2 tinned, red", "-", "w_pos",
                       [f"classT_{n}_out", (ANCHORS[f"classT_{n}_out"][0] + 30, ANCHORS["isolator"][1], ANCHORS[f"classT_{n}_out"][2]), "isolator"]))
        L.append(Cable(f"B{n}N", "Battery bank -", f"Battery {n} -", "SmartShunt (battery side)", "120", "120 mm2 tinned, black", "-", "w_neg",
                       [f"batt{n}_neg", (bn[0] + 40, bn[1], bn[2]), (bn[0] + 40, ANCHORS["shunt"][1] + 30, bn[2]),
                        (ANCHORS["shunt"][0] - 10, ANCHORS["shunt"][1] + 30, ANCHORS["shunt"][2] + 20), "shunt"],
                       notes="keep both battery cables equal length"))
    L.append(Cable("M1P", "Main +", "Isolator", "+ busbar (1000 A)", "120", "2 x 120 mm2 tinned, red", "2 x 400 A Class-T upstream", "w_pos",
                   ["isolator", (ANCHORS["isolator"][0] - 20, ANCHORS["isolator"][1], ANCHORS["bus_pos"][2] + 20), "bus_pos"]))
    L.append(Cable("M1N", "Main -", "SmartShunt (system side)", "- busbar (1000 A)", "120", "2 x 120 mm2 tinned, black", "-", "w_neg",
                   ["shunt_sys", (ANCHORS["shunt_sys"][0], ANCHORS["shunt_sys"][1], ANCHORS["bus_neg"][2] + 60), "bus_neg"]))
    L.append(Cable("INVP", "Inverter DC +", "+ busbar", "Quattro DC +", "120", "2 x 120 mm2 tinned, red", "2 x 400 A Class-T (= 800 A per Victron)", "w_pos",
                   ["bus_pos", (ANCHORS["inv_dc_pos"][0], ANCHORS["bus_pos"][1], ANCHORS["inv_dc_pos"][2] + 30), "inv_dc_pos"],
                   notes="Victron: 2 x 120 mm2 per pole for 0-5 m"))
    L.append(Cable("INVN", "Inverter DC -", "- busbar", "Quattro DC -", "120", "2 x 120 mm2 tinned, black", "-", "w_neg",
                   ["bus_neg", (ANCHORS["inv_dc_neg"][0], ANCHORS["bus_neg"][1], ANCHORS["inv_dc_neg"][2] + 15), "inv_dc_neg"]))
    # ------------------------------------------------ bay -> charging board (over the passenger arch)
    for cid, to, size, spec, prot in (("DCF", "dc_fuse_block", "25", "25 mm2 twin (red/black)", "MEGA 100 A"),
                                      ("ORO", "orion_xs_50a", "16", "16 mm2 twin", "MIDI 70 A"),
                                      ("MPR", "mppt_roof_100_50", "16", "16 mm2 twin", "MIDI 60 A"),
                                      ("MPT", "mppt_tent_75_15", "6", "6 mm2 twin", "MIDI 20 A")):
        L.append(Cable(cid, "DC distribution", "+ busbar MIDI/MEGA fuse", to.replace("_", " "), size, spec, prot, "w_pos",
                       ["midi_fuses", "dist_top"] + INSIDE_TO_BOARD + [_drop(to), to]))
    # ------------------------------------------------ AC (inside)
    L.append(Cable("AC1", "AC out", "Quattro AC-out 1", "RCBO enclosure", "2.5x3", "2.5 mm2 3-core flex (TPS-flex)", "Quattro internal + RCBOs", "w_ac",
                   ["inv_ac", "dist_top", "bay_top", "arch_run0", "arch_run1", "cab_in", "rcbo"], notes="licensed electrician"))
    L.append(Cable("AC2", "Rear GPOs", "RCBO 1", "Rear panel GPO x2", "2.5x3", "2.5 mm2 3-core flex", "RCBO 10 A 30 mA", "w_ac",
                   ["rcbo", "pc_gpo_1"]))
    L.append(Cable("AC3", "Slide GPO", "RCBO 2", "Power-slide bulkhead GPO", "2.5x3", "2.5 mm2 3-core high-flex (chain rated)", "RCBO 10 A 30 mA", "w_ac",
                   ["rcbo", "cab_floor", "under_slide", "chain_fixed", "chain_moving", "slide_bulkhead"], extra_mm=600,
                   notes="runs through the cable chain"))
    L.append(Cable("AC4", "Tent heater GPO", "RCBO 3", "Tent services box GPO (via junction)", "2.5x3", "2.5 mm2 3-core flex, UV rated", "RCBO 10 A 30 mA",
                   "w_ac", ["rcbo"] + cab_to_gland + to_gap, notes="detaches at the gap junction (IP66 inline plug/socket)"))
    L.append(Cable("AC5", "Shore inlet", "Gap junction (from tent inlet)", "Quattro AC-in 1", "2.5x3", "2.5 mm2 3-core flex (15 A)", "Inlet + Quattro input limit",
                   "w_ac", ["junction_bot", "gap_low", "chassis_gap", "chassis_rear", "wall_low", "wall_out", "gland_in", "cab_in",
                            "arch_run1", "arch_run0", "bay_top", "dist_top", "inv_ac"]))
    # ------------------------------------------------ DC outlets
    L.append(Cable("DO1", "Rear panel DC", "DC fuse block", "Rear panel Anderson x2 / USB-C / 12 V", "6", "6 mm2 twin", "30 A + 15 A + 10 A", "w_12v",
                   ["dc_fuse_block", _drop("dc_fuse_block"), "arch_run1", "cab_in", "pc_anderson_1"]))
    L.append(Cable("DO2", "Slide DC", "DC fuse block", "Power-slide Anderson / 12 V / USB-C", "6", "6 mm2 twin high-flex", "30 A", "w_12v",
                   ["dc_fuse_block", _drop("dc_fuse_block"), "arch_run1", "cab_in", "cab_floor", "under_slide", "chain_fixed", "chain_moving",
                    "slide_bulkhead"], extra_mm=600, notes="runs through the cable chain"))
    L.append(Cable("DO3", "Cabin outlets", "DC fuse block", "Under-rear-seat box (Anderson, USB-C, 12 V)", "6", "6 mm2 twin", "30 A", "w_12v",
                   ["dc_fuse_block", _drop("dc_fuse_block"), "arch_run1"] + cab_to_gland + OUT + ["chassis_cabin", "cabin_grommet", "cabin_outlets"]))
    L.append(Cable("DO4", "Starlink Mini", "DC fuse block", "Starlink Mini (roof)", "4", "4 mm2 twin + DC barrel lead", "10 A", "w_12v",
                   ["dc_fuse_block", _drop("dc_fuse_block"), "arch_run1"] + cab_to_gland + to_gap + ["junction_top", "gap_high", "roof_drop",
                                                                                                       "starlink"]))
    L.append(Cable("DO5", "Tent 12 V", "DC fuse block", "Gap junction -> tent (Anderson SB50)", "6", "6 mm2 twin", "30 A", "w_12v",
                   ["dc_fuse_block", _drop("dc_fuse_block"), "arch_run1"] + cab_to_gland + to_gap, notes="detaches at the gap junction"))
    # ------------------------------------------------ charging inputs
    L.append(Cable("ALT", "Alternator charge", "Start battery (60 A fuse)", "Orion XS input", "25", "25 mm2 twin (+/-), tinned", "60 A MIDI at start battery",
                   "w_pos", ["start_battery", "engine_up", "chassis_engine", "chassis_gap"] + list(reversed(OUT)) + ["cab_in", "arch_run1",
                                                                                                                 _drop("orion_xs_50a"), "orion_xs_50a"],
                   notes="Orion XS current limit set conservatively until alternator rating known"))
    L.append(Cable("PVR", "Roof PV", "Roof panels (series)", "MPPT 100/50 PV in", "6", "6 mm2 solar twin (UV)", "PV breaker 20 A", "w_pv",
                   ["roof_pv", "roof_drop", "gap_high", "junction_top", "junction_bot", "gap_low", "chassis_gap"] + list(reversed(OUT)) +
                   ["cab_in", "arch_run1", _drop("mppt_roof_100_50"), "mppt_roof_100_50"]))
    L.append(Cable("PVT", "Tent PV", "Gap junction (from tent panels)", "MPPT 75/15 PV in", "6", "6 mm2 solar twin (UV)", "PV breaker 15 A", "w_pv",
                   ["junction_bot", "gap_low", "chassis_gap"] + list(reversed(OUT)) + ["cab_in", "arch_run1", _drop("mppt_tent_75_15"),
                                                                                       "mppt_tent_75_15"], notes="detaches at the gap junction"))
    # ------------------------------------------------ comms
    L.append(Cable("D1", "VE.Bus", "Cerbo GX", "Quattro", "data", "RJ45 VE.Bus cable", "-", "w_data",
                   ["cerbo", "cab_in", "arch_run1", "arch_run0", "bay_top", "dist_top", "inv_comms"]))
    L.append(Cable("D2", "VE.Direct", "Cerbo GX", "SmartShunt / MPPTs / Orion XS", "data", "VE.Direct cables x4", "-", "w_data",
                   ["cerbo", "cab_in", "arch_run1", _drop("mppt_roof_100_50", dy=8), "mppt_roof_100_50"]))
    L.append(Cable("D3", "Display", "Cerbo GX", "GX Touch 50", "data", "GX Touch cable", "-", "w_data", ["cerbo", "pc_gx_touch_50"]))
    # ------------------------------------------------ detachable tent harness (tent side)
    L.append(Cable("T1", "Tent harness", "Tent services box", "Gap junction plugs (240 V out, 240 V in, 12 V)", "2.5x3",
                   "2 x 2.5 mm2 3-core + 6 mm2 twin, sheathed bundle", "-", "w_tent",
                   ["tent_services", (P.TENT_X0 + 30, ANCHORS["tent_services"][1], ANCHORS["tent_services"][2]),
                    (P.TENT_X0 + 30, -515, ANCHORS["tent_services"][2]), "lid_front", "junction_top"], side="tent",
                   notes="stays with the tent; check clearance at the lid hinge"))
    L.append(Cable("T2", "Tent PV harness", "Tent panels", "Gap junction (PV plug)", "6", "6 mm2 solar twin (UV)", "-", "w_tent",
                   ["tent_pv_jbox", (P.TENT_X0 + 20, ANCHORS["tent_pv_jbox"][1], ANCHORS["tent_pv_jbox"][2]),
                    (P.TENT_X0 + 20, -515, P.TENT_Z0 + 40), "lid_front", "junction_top"], side="tent"))
    return L


def build():
    parts = []
    cl = cables()
    for k, c in enumerate(cl):
        grp = "tent_harness" if c.side == "tent" else "wiring"
        parts.append(Part(f"cable_{c.cid}", grp, color=C[c.colour], tube=c.points(k), tube_r=RADIUS[c.size],
                          meta=dict(cable=c)))
    # gap junction box (vehicle side) between cab and tub, passenger front corner
    gx = P.CAB_REAR_X + 28
    parts.append(part("gap_junction_box", "electrical", box(gx - 20, gx + 20, -790, -610, 360, 535), "victron_dark", kg=1.8,
                      note="IP66; inline plugs: 240 V out, 240 V in, 12 V SB50, PV"))
    return parts, cl
