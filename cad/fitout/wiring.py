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
    yt = -hw + 30                              # passenger cable tray / wall channel line
    zt = P.UPPER_Z1 + 14                       # tray height (above the upper drawer, under the lid)
    w = dict(
        bay_top=(P.BAY_D - 40, -P.BAY_W / 2 + 40, P.BAY_H - 15),
        dist_top=(200, ANCHORS["bus_sys_pos"][1] + 10, P.BAY_H - 15),
        tray_front=(P.BAY_D - 40, yt, zt),
        tray_rear=(fx + 30, yt, zt),
        drop_gland=(fx + 30, -hw + 11, fz + 20),
        gland_in=(fx, -hw + 8, fz),
        cab_in=(fx + 30, -hw + 11, P.LOWER_TOP_Z - 30),
        cab_floor=(P.POCKET_X0 + 200, -P.POCKET_Y_IN - 30, 25),
        under_slide=(P.POCKET_X0 + 200, -P.POCKET_Y_IN + 20, 8),
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


def _up(a, dz=0):
    """Waypoint just above a front-wall charging-board component, at bay-top height."""
    x, y, z = ANCHORS[a]
    return (x + 20, y, P.BAY_H - 25 + dz)


# shared legs
OUT = ["gland_in", "wall_out", "wall_low", "chassis_rear"]                 # tub -> chassis
IN = list(reversed(OUT))
BAY_TO_CAB = ["dist_top", "bay_top", "tray_front", "tray_rear", "drop_gland", "cab_in"]
CAB_TO_BAY = list(reversed(BAY_TO_CAB))
GLAND_TO_BAY = ["gland_in", "drop_gland", "tray_rear", "tray_front", "bay_top"]


def cables():
    trunks()
    to_gap = OUT + ["chassis_gap", "gap_low", "junction_bot"]
    from_gap = ["junction_bot", "gap_low", "chassis_gap"] + IN
    A = ANCHORS
    L = []
    # ------------------------------------------------ battery bank (equal-length pairs)
    for n in (1, 2):
        bp, bn = A[f"batt{n}_pos"], A[f"batt{n}_neg"]
        L.append(Cable(f"B{n}P", "Bank +", f"Battery {n} + (MRBF 300 A)", "Bank + busbar", "70", "70 mm2 tinned, red", "MRBF 300 A on terminal",
                       "w_pos", [f"batt{n}_pos", (bp[0] + 35, bp[1], bp[2]), (bp[0] + 35, A["bus_bank_pos"][1] + 30, A["bus_bank_pos"][2]),
                                 "bus_bank_pos"], notes="cut B1P/B2P to identical length"))
        L.append(Cable(f"B{n}N", "Bank -", f"Battery {n} -", "Bank - busbar", "70", "70 mm2 tinned, black", "-", "w_neg",
                       [f"batt{n}_neg", (bn[0] + 35, bn[1], bn[2]), (bn[0] + 35, A["bus_bank_neg"][1] + 30, bn[2]),
                        (A["bus_bank_neg"][0], A["bus_bank_neg"][1] + 30, A["bus_bank_neg"][2]), "bus_bank_neg"],
                       notes="cut B1N/B2N to identical length"))
    L.append(Cable("RB1", "Main +", "Bank + busbar", "Remote battery switch IN", "70", "70 mm2 tinned, red", "MRBF x2 upstream", "w_pos",
                   ["bus_bank_pos", "rbs_in"]))
    L.append(Cable("RB2", "Main +", "Remote battery switch OUT", "System + busbar", "70", "70 mm2 tinned, red", "-", "w_pos",
                   ["rbs_out", (A["rbs_out"][0], A["rbs_out"][1] + 25, A["bus_sys_pos"][2]), "bus_sys_pos"]))
    L.append(Cable("SH1", "Main -", "Bank - busbar", "SmartShunt (battery side)", "70", "70 mm2 tinned, black", "-", "w_neg", ["bus_bank_neg", "shunt"]))
    L.append(Cable("SH2", "Main -", "SmartShunt (system side)", "System - busbar", "70", "70 mm2 tinned, black", "-", "w_neg",
                   ["shunt_sys", (A["shunt_sys"][0], A["shunt_sys"][1] + 25, A["bus_sys_neg"][2]), "bus_sys_neg"]))
    L.append(Cable("CT1", "Inverter +", "System + busbar", "Class-T 400 A", "50", "2 x 50 mm2 tinned, red", "-", "w_pos",
                   ["bus_sys_pos", (A["bus_sys_pos"][0], A["bus_sys_pos"][1] + 25, A["classT_in"][2]), "classT_in"]))
    L.append(Cable("INVP", "Inverter +", "Class-T 400 A", "MultiPlus-II DC +", "50", "2 x 50 mm2 tinned, red", "Class-T 400 A", "w_pos",
                   ["classT_out", (A["classT_out"][0], A["inv_dc_pos"][1] + 20, A["inv_dc_pos"][2] + 30), "inv_dc_pos"],
                   notes="Victron: 2 x 50 mm2 per pole for 0-5 m, 400 A fuse"))
    L.append(Cable("INVN", "Inverter -", "System - busbar", "MultiPlus-II DC -", "50", "2 x 50 mm2 tinned, black", "-", "w_neg",
                   ["bus_sys_neg", (A["inv_dc_neg"][0], A["bus_sys_neg"][1] + 5, A["inv_dc_neg"][2]), "inv_dc_neg"]))
    # ------------------------------------------------ charging board (front wall) <-> system busbars (short, inside the bay)
    for cid, src, term, fuse, size, spec, prot in (("ORO", "orion_xs_50a", "orion_out", "midi_orion", "16", "16 mm2 twin", "MIDI 70 A"),
                                                   ("MPR", "mppt_roof_100_30", "mppt_roof_bat", "midi_mppt_roof", "16", "16 mm2 twin", "MIDI 60 A"),
                                                   ("MPT", "mppt_tent_75_15", "mppt_tent_bat", "midi_mppt_tent", "6", "6 mm2 twin", "MIDI 20 A")):
        t = A.get(term, A[src])
        f = A.get(fuse, A["midi_fuses"])
        L.append(Cable(cid, "Charging output", src.replace("_", " "), "System +/- busbars (MIDI fuse)", size, spec, prot, "w_pos",
                       [t, (t[0] + 30, t[1], 150), (f[0], f[1] + 30, 150), f]))
    # ------------------------------------------------ bay -> rear control cabinet
    L.append(Cable("DCF", "DC distribution", "System + busbar (MEGA 100 A)", "Rear DC fuse block", "25", "25 mm2 twin (red/black)", "MEGA 100 A",
                   "w_pos", ["midi_fuses"] + BAY_TO_CAB + ["dc_fuse_block"]))
    L.append(Cable("AC1", "AC out", "MultiPlus-II AC-out 1", "RCBO enclosure", "2.5x3", "2.5 mm2 3-core flex (TPS-flex)", "MultiPlus + RCBOs", "w_ac",
                   ["inv_ac"] + BAY_TO_CAB + ["rcbo"], notes="licensed electrician"))
    L.append(Cable("AC2", "Rear GPO", "RCBO 1", "Rear panel double GPO", "2.5x3", "2.5 mm2 3-core flex", "RCBO 10 A 30 mA", "w_ac",
                   ["rcbo", "pc_gpo_double"]))
    L.append(Cable("AC3", "Slide GPO", "RCBO 2", "Power-slide pod GPO", "2.5x3", "2.5 mm2 3-core high-flex (chain rated)", "RCBO 10 A 30 mA", "w_ac",
                   ["rcbo", "cab_floor", "under_slide", "chain_fixed", "chain_moving", "slide_bulkhead"], extra_mm=600,
                   notes="runs through the cable chain"))
    L.append(Cable("AC4", "Tent heater GPO", "RCBO 3", "Gap junction -> tent services box GPO", "2.5x3", "2.5 mm2 3-core flex, UV rated",
                   "RCBO 10 A 30 mA", "w_ac", ["rcbo", "cab_in", "drop_gland"] + to_gap, notes="detaches at the gap junction (IP66 inline plug)"))
    L.append(Cable("AC5", "Shore inlet", "Gap junction (from tent 15 A inlet)", "MultiPlus-II AC-in", "2.5x3", "2.5 mm2 3-core flex (15 A)",
                   "RCBO 16 A 30 mA in the services box + MultiPlus AC-in limit 15 A", "w_ac", from_gap + GLAND_TO_BAY + ["dist_top", "inv_ac"]))
    # ------------------------------------------------ DC outlets from the rear fuse block
    for cid, circ, to, size, spec, prot in (("DO1A", "Rear Anderson 1", "pc_anderson_1", "6", "6 mm2 twin", "ATC 30 A"),
                                            ("DO1B", "Rear Anderson 2", "pc_anderson_2", "6", "6 mm2 twin", "ATC 30 A"),
                                            ("DO1C", "Rear USB-C x2", "pc_usbc_1", "2.5x3", "2.5 mm2 twin", "ATC 10 A"),
                                            ("DO1D", "Rear 12 V socket", "pc_12v", "4", "4 mm2 twin", "ATC 15 A")):
        L.append(Cable(cid, circ, "DC fuse block", f"Rear panel {circ.split('Rear ')[1]}", size, spec, prot, "w_12v",
                       ["dc_fuse_block", to], notes="USB-C sockets daisy-chained at the panel" if cid == "DO1C" else ""))
    L.append(Cable("DO2", "Slide DC", "DC fuse block", "Power-slide pod Anderson / 12 V / USB-C", "6", "6 mm2 twin high-flex", "ATC 30 A (+ inline 15 A / 10 A in the pod)", "w_12v",
                   ["dc_fuse_block", "cab_floor", "under_slide", "chain_fixed", "chain_moving", "slide_bulkhead"], extra_mm=600,
                   notes="runs through the cable chain"))
    L.append(Cable("DO3", "Cabin outlets", "DC fuse block", "Under-rear-seat box (Anderson, USB-C, 12 V)", "6", "6 mm2 twin", "ATC 30 A (+ inline 15 A / 10 A in the box)", "w_12v",
                   ["dc_fuse_block", "cab_in", "drop_gland"] + OUT + ["chassis_cabin", "cabin_grommet", "cabin_outlets"]))
    L.append(Cable("DO4", "Starlink Mini", "DC fuse block", "Starlink Mini (roof)", "4", "4 mm2 twin + DC barrel lead", "ATC 10 A", "w_12v",
                   ["dc_fuse_block", "cab_in", "drop_gland"] + to_gap + ["junction_top", "gap_high", "roof_drop", "starlink"]))
    L.append(Cable("DO5", "Tent 12 V", "DC fuse block", "Gap junction -> tent (Anderson SB50)", "6", "6 mm2 twin", "ATC 30 A", "w_12v",
                   ["dc_fuse_block", "cab_in", "drop_gland"] + to_gap, notes="detaches at the gap junction"))
    # ------------------------------------------------ charging inputs (enter via the gland, run to the front-wall board)
    L.append(Cable("ALT", "Alternator charge", "Start battery (60 A MIDI)", "Orion XS input", "25", "25 mm2 twin (+/-), tinned", "60 A at start battery",
                   "w_pos", ["start_battery", "engine_up", "chassis_engine", "chassis_gap"] + IN + GLAND_TO_BAY + [_up("orion_xs_50a"), A.get("orion_in", A["orion_xs_50a"])],
                   notes="Orion XS input limit 25-30 A until the alternator rating is known"))
    L.append(Cable("PVR", "Roof PV", "Roof panels + visor (parallel, MC4 3-way branch)", "MPPT 100/50 PV in", "6", "6 mm2 solar twin (UV)", "2-pole DC PV isolator 32 A", "w_pv",
                   ["roof_pv", "roof_drop", "gap_high", "junction_top", "junction_bot", "gap_low", "chassis_gap"] + IN + GLAND_TO_BAY +
                   [_up("mppt_roof_100_30"), A.get("mppt_roof_pv", A["mppt_roof_100_30"])]))
    L.append(Cable("PVT", "Tent PV", "Gap junction (from tent panels)", "MPPT 75/15 PV in", "6", "6 mm2 solar twin (UV)", "2-pole DC PV isolator 32 A", "w_pv",
                   from_gap + GLAND_TO_BAY + [_up("mppt_tent_75_15"), A.get("mppt_tent_pv", A["mppt_tent_75_15"])], notes="detaches at the gap junction"))
    # ------------------------------------------------ control + comms (rear panel <-> bay)
    L.append(Cable("SW1", "Battery switch control", "Rear panel ML-RBS switch (Blue Sea 2155)", "ML-RBS control harness", "data",
                   "4-core 1.0 mm2 (+12 V feed, control, LED, ground)", "2 A inline at bank + (RBF)", "w_data",
                   ["pc_sw_battery", "cab_in"] + CAB_TO_BAY + [A.get("rbs_ctrl", A["rbs_in"])],
                   notes="switch feed taken from the battery side so the RBS can be closed again"))
    L.append(Cable("RBF", "Battery switch control", "Bank + busbar", "ML-RBS control feed (inline 2 A)", "data", "1.0 mm2 red", "ATC 2 A inline",
                   "w_data", ["bus_bank_pos", A.get("rbs_ctrl", A["rbs_in"])]))
    L.append(Cable("SHV", "Shunt sense", "Bank + busbar", "SmartShunt Vbatt+", "data", "0.75 mm2 red (supplied lead)", "1 A inline (supplied)",
                   "w_data", ["bus_bank_pos", A.get("shunt_vbatt", A["shunt"])]))
    L.append(Cable("FAN", "Inverter fan", "System + busbar", "92 mm thermostatic fan", "2.5x3", "1.5 mm2 twin", "ATC 5 A inline", "w_12v",
                   ["bus_sys_pos", A.get("inv_fan", (P.INVERTER[1] / 2 + 4, -P.BAY_W / 2 + 2 + P.INVERTER[0] / 2, 10 + P.INVERTER[2] + 40))]))
    L.append(Cable("CGX", "Cerbo GX power", "DC fuse block", "Cerbo GX power in", "data", "0.75 mm2 twin", "ATC 2 A", "w_12v",
                   ["dc_fuse_block", "cerbo"]))
    L.append(Cable("IGN", "Orion ignition sense", "Engine-bay fuse box (add-a-fuse, ignition)", "Orion XS remote H", "data", "1.0 mm2 single",
                   "ATC 2 A add-a-fuse", "w_data", ["start_battery", "engine_up", "chassis_engine", "chassis_gap"] + IN + GLAND_TO_BAY +
                   [_up("orion_xs_50a", 12), A.get("orion_remote", A["orion_xs_50a"])],
                   notes="engine-run signal; avoids relying on voltage detection with a smart alternator"))
    L.append(Cable("PE1", "Inverter case earth", "MultiPlus-II chassis earth stud", "System - busbar", "50", "50 mm2 green/yellow", "-", "w_pe",
                   [A.get("inv_chassis_earth", A["inv_dc_neg"]), "bus_sys_neg"], notes="Victron: same size as the DC negative"))
    L.append(Cable("CHB", "Chassis bond", "System - busbar", "Chassis rail bond point", "25", "25 mm2 black", "-", "w_neg",
                   ["bus_sys_neg", "dist_top"] + list(reversed(GLAND_TO_BAY)) + OUT, notes="single DC-negative / PE bond to the vehicle chassis"))
    L.append(Cable("SW2", "Inverter remote on/off", "Rear panel switch", "MultiPlus-II remote terminals", "data", "2-core 0.75 mm2", "-", "w_data",
                   ["pc_sw_inverter", "cab_in"] + CAB_TO_BAY + [A.get("inv_remote", A["inv_comms"])]))
    L.append(Cable("D1", "VE.Bus", "Cerbo GX", "MultiPlus-II", "data", "RJ45 VE.Bus cable", "-", "w_data", ["cerbo"] + CAB_TO_BAY + ["inv_comms"]))
    L.append(Cable("D2", "VE.Direct", "Cerbo GX VE.Direct 1-3", "SmartShunt / MPPT 100/50 / MPPT 75/15", "data", "VE.Direct cables x3", "-", "w_data",
                   ["cerbo"] + CAB_TO_BAY + [_up("mppt_roof_100_30", 8), "mppt_roof_100_30", A.get("shunt_vedirect", A["shunt"])]))
    L.append(Cable("D4", "VE.Direct", "Cerbo GX USB", "Orion XS VE.Direct", "data", "VE.Direct to USB interface", "-", "w_data",
                   ["cerbo"] + CAB_TO_BAY + [_up("orion_xs_50a", 8), "orion_xs_50a"], notes="Cerbo GX MK2 has only 3 VE.Direct ports"))
    L.append(Cable("D3", "Display", "Cerbo GX (HDMI + USB)", "GX Touch 50", "data", "GX Touch cable (HDMI + USB)", "-", "w_data", ["cerbo", "pc_gx_touch_50"]))
    # ------------------------------------------------ windscreen visor panel (v0.11)
    roof_up = to_gap + ["junction_top", "gap_high", "roof_drop"]
    L.append(Cable("PVV", "Visor PV", "Visor panel (moving)", "Roof PV branch (parallel with PV1/PV2)", "4", "4 mm2 solar twin, high-flex (chain rated)",
                   "-", "w_pv", ["visor_pv", (A["visor_pv"][0], -P.VISOR["rail_y"] + 40, A["visor_pv"][2]),
                                 (A["visor_ctrl"][0], -P.VISOR["rail_y"] + 40, A["visor_ctrl"][2]), "roof_pv"],
                   extra_mm=1600, notes="runs in a small cable chain beside the passenger guide rail"))
    L.append(Cable("VIS", "Visor drive power", "DC fuse block (way 10)", "Visor controller (roof)", "6", "6 mm2 twin", "ATC 20 A", "w_12v",
                   ["dc_fuse_block", "cab_in", "drop_gland"] + roof_up + ["visor_ctrl"], notes="gearmotor + 2 tilt drives + latches"))
    L.append(Cable("VSW", "Visor control", "Rear panel visor button (S3)", "Visor controller (roof)", "data", "3-core 0.75 mm2 (deploy, stow, LED)",
                   "-", "w_data", ["pc_sw_inverter", "cab_in", "drop_gland"] + roof_up + ["visor_ctrl"]))
    L.append(Cable("VIG", "Visor interlock", "Orion XS remote H (ignition, F9)", "Visor controller interlock input", "data", "1.0 mm2 single",
                   "F9 2 A (shared)", "w_data", [A.get("orion_remote", A["orion_xs_50a"]), _up("orion_xs_50a", 16)] + list(reversed(GLAND_TO_BAY))
                   + OUT + ["chassis_gap", "gap_low", "junction_bot"] + ["junction_top", "gap_high", "roof_drop", "visor_ctrl"],
                   notes="ignition on = deploy inhibited, warning if not stowed"))
    # ------------------------------------------------ detachable tent harness (tent side)
    L.append(Cable("T1", "Tent harness", "Tent services box", "Gap junction plugs (240 V out, 240 V in, 12 V)", "2.5x3",
                   "2 x 2.5 mm2 3-core + 6 mm2 twin, sheathed bundle", "RCBO 16 A 30 mA (AC-in, in the services box)", "w_tent",
                   ["tent_services", (P.TENT_X0 + 30, A["tent_services"][1], A["tent_services"][2]),
                    (P.TENT_X0 + 30, -515, A["tent_services"][2]), "lid_front", "junction_top"], side="tent",
                   notes="stays with the tent; check clearance at the lid hinge"))
    L.append(Cable("T2", "Tent PV harness", "Tent panels", "Gap junction (PV plug)", "6", "6 mm2 solar twin (UV)", "-", "w_tent",
                   ["tent_pv_jbox", (P.TENT_X0 + 20, A["tent_pv_jbox"][1], A["tent_pv_jbox"][2]),
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
