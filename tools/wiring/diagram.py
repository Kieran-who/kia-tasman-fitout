"""
Wiring diagram generator.

Reads the routed cable schedule (bom/cable-schedule-<ver>.csv) and cad/out/cables.json written by
cad/build.py, draws the electrical sheets E1-E9 as SVG, and writes:
    docs/wiring/sheets/E<n>-<key>.svg
    docs/wiring/wiring-diagram-<ver>.html   (standalone page: all sheets + schedules)
    docs/wiring/artifact.html               (same content without the html/head/body skeleton)
Every cable ID in the schedule must appear on at least one sheet; the script fails otherwise.

Usage:  python3 tools/wiring/diagram.py
"""
import csv
import json
import re
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svglib import Sheet, MONO  # noqa: E402
import routes  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cad"))
import params as P  # noqa: E402

V = P.VERSION
DATE = "2026-10-23"
META = dict(version=V, date=DATE)
TOTAL = 16

SCHED = {r["id"]: r for r in csv.DictReader(open(ROOT / f"bom/cable-schedule-{V}.csv"))}
ROUTES = json.load(open(ROOT / "cad/out/cables.json"))
USED = set()


def size_of(cid):
    spec = SCHED[cid]["cable"]
    m = re.match(r"\s*(2 x )?([\d.]+) mm2", spec)
    if not m:
        return None
    return m.group(2)


def T(cid, extra=None):
    """Cable tag text: ID · conductor."""
    USED.add(cid)
    spec = SCHED[cid]["cable"]
    m = re.match(r"\s*(2 x )?([\d.]+) mm2(?: (twin|3-core|single|red|black|green/yellow))?", spec)
    if extra:
        return f"{cid} · {extra}"
    if not m:
        short = {"RJ45 VE.Bus cable": "VE.Bus RJ45", "VE.Direct cables x3": "VE.Direct", "VE.Direct to USB interface": "VE.Direct-USB",
                 "GX Touch cable (HDMI + USB)": "HDMI+USB"}.get(spec, spec.split(" (")[0])
        return f"{cid} · {short.replace('mm2', 'mm²')}"
    n = ("2×" if m.group(1) else "") + m.group(2) + " mm²"
    core = m.group(3)
    if core in ("twin", "3-core"):
        n += f" {core}"
    return f"{cid} · {n}"


def W(size):
    """Map a schedule size to a stroke width key."""
    return {"2.5x3": "2.5", "4x3": "4", "data": "1", "1.0": "1"}.get(size, size)


# ======================================================================================= E2
def sheet_dc_main():
    s = Sheet(2, "dc-main", "DC power: battery bank and main distribution",
              "Front bay, between the wheel arches. 12.8 V LiFePO₄ bank → isolation → protection → system busbars.", TOTAL)
    yp, yn = 250, 650          # system rails
    s.zone(46, 92, 1590, 690, "Front bay", "tub front wall, between the arches (lid can't open with the tent on; everything is serviced from the rear)")
    # ---------------- batteries
    bt = []
    for i, x in enumerate((90, 330)):
        b = s.block(f"BT{i + 1}", x, 360, 190, 170, f"Battery {i + 1}",
                    ["iTechworld iTech400X Pro", "12.8 V · 400 Ah LiFePO₄", "stands on end, terminals rear", "internal BMS (Bluetooth only)"],
                    cat="battery", terms=[("p", "T", 45, "+ M8"), ("n", "B", 140, "− M8")])
        bt.append(b)
    s.bus("BB1", 110, yp, 600, yp, "pos", "Bank + busbar")
    s.bus("BB2", 110, yn, 600, yn, "neg", "Bank − busbar")
    for i, b in enumerate(bt):
        x, y = b.t("p")
        s.wire([(x, y), (x, yp)], "pos", "70", tag=T(f"B{i + 1}P"), tag_at=(x + 48, yp + 34))
        s.fuse(x, y - 34, "v", f"F{i + 1}", "MRBF 300 A", side=1 if i == 0 else 1)
        x, y = b.t("n")
        s.wire([(x, y), (x, yn)], "neg", "70", tag=T(f"B{i + 1}N"), tag_at=(x, y + 40))
    # ---------------- isolation: ML-RBS between bank + and system +
    q = s.block("QS1", 690, yp - 50, 180, 92, "Battery switch", ["Blue Sea ML-RBS 7713", "500 A latching, manual knob"],
                cat="prot", terms=[("in", "L", 50, "IN"), ("out", "R", 50, "OUT"), ("ctl", "B", 120, "CTRL")])
    s.wire([(600, yp), q.t("in")], "pos", "120", tag=T("RB1"), tag_at=(648, yp + 22))
    s.bus("BB3", 960, yp, 1440, yp, "pos", "System + busbar")
    s.wire([q.t("out"), (960, yp)], "pos", "120", tag=T("RB2"), tag_at=(915, yp + 22))
    s.dot(630, yp)
    s.wire([(630, yp), (630, 150), (700, 150)], "ctrl", "1")
    s.fuse(630, 192, "v", "F10", "2 A", side=-1)
    s.offsheet(700, 150, "r", f"{T('RBF')} → S1 +12 V feed", "always live (bank side) · sheet E6")
    x, y = q.t("ctl")
    s.wire([(x, y), (x, y + 40)], "ctrl", "1")
    s.offsheet(x, y + 40, "d", f"{T('SW1')} → S1 rear panel", "sheet E6")
    # ---------------- SmartShunt in the negative
    sh = s.block("P1", 690, yn - 45, 180, 90, "Battery monitor", ["Victron SmartShunt 500 A", "all − current passes it",
                                                                  "Aux = battery temp (TS1)"],
                 cat="victron", terms=[("b", "L", 45, "BATT"), ("s", "R", 45, "SYS"), ("v", "T", 22, "V+"), ("ax", "T", 62, "AUX"),
                                       ("vd", "T", 150, "VE.D")])
    s.wire([(600, yn), sh.t("b")], "neg", "120", tag=T("SH1"), tag_at=(645, yn + 24))
    s.bus("BB4", 960, yn, 1440, yn, "neg", "System − busbar", below=True)
    s.wire([sh.t("s"), (960, yn)], "neg", "120", tag=T("SH2"), tag_at=(915, yn + 24))
    # v0.14: Victron temperature sensor - ring lug on battery 1's + post (battery side of F1), red to V+, black to AUX
    s.dot(135, 348, "pos")
    s.wire([(135, 348), (300, 348), (300, 548), (752, 548), sh.t("ax")], "sig", "0.75", tag=T("TS1", "temp sensor 2-core"),
           tag_at=(600, 548))
    s.dot(712, 548, "pos", r=3)
    s.wire([(712, 548), sh.t("v")], "sig", "0.75")
    s.fuse(300, 450, "v", "F11", "", side=1)
    s.text(232, 343, "θ sensor", size=10, fill="#0b7285", weight="600")
    x, y = sh.t("vd")
    s.wire([(x, y), (x, y - 60)], "data")
    s.offsheet(x, y - 60, "u", f"{T('D2', 'VE.Direct')} → U5 Cerbo", "sheet E6")
    # ---------------- inverter
    xi = 1010
    u1 = s.block("U1", xi - 30, 360, 220, 200, "Inverter / charger",
                 ["Victron MultiPlus-II 12/3000/120-32", "230 V · 2400 W cont. · 120 A charge", "DC: 2 × 50 mm² per pole (0–5 m)",
                  "AC-in / AC-out → sheet E5", "VE.Bus, remote on/off → sheet E6", "lies flat beside the batteries"],
                 cat="victron", terms=[("p", "T", 30, "DC+"), ("n", "B", 30, "DC−"), ("pe", "R", 160, "CASE ⏚")])
    s.wire([(xi, yp), (xi, 285)], "pos", "50", tag=T("CT1"), tag_at=(xi + 50, 272))
    s.fuse(xi, 300, "v", "F3", "Class-T 400 A", side=-1)
    s.wire([(xi, 315), u1.t("p")], "pos", "50", tag=T("INVP"), tag_at=(xi + 60, 328))
    s.wire([u1.t("n"), (xi, yn)], "neg", "50", tag=T("INVN"), tag_at=(xi + 54, 598))
    x, y = u1.t("pe")
    s.wire([(x, y), (1226, y), (1226, yn)], "PE", "50", tag=T("PE1"), tag_at=(1226, 596))
    # ---------------- fan (thermostatic, above the inverter)
    s.wire([(1268, yp), (1268, 384)], "pos", "1.5")
    s.fuse(1268, 318, "v", "F12", "5 A", side=-1)
    s.motor(1268, 400, "M1", "fan 92 mm")
    s.wire([(1268, 416), (1268, yn)], "neg", "1.5", tag=T("FAN"), tag_at=(1268, 470))
    # ---------------- charger outputs (twin: + leg to BB3 via MIDI, − leg to BB4)
    for k, (cid, ref, rating, src) in enumerate((("ORO", "F4", "MIDI 70 A", "U2 Orion XS"), ("MPR", "F5", "MIDI 40 A", "U3 MPPT 100/30"),
                                                 ("MPT", "F6", "MIDI 40 A", "U4 MPPT 75/15"), ("MPV", "F6", "(shared)", "U13 MPPT 100/20"))):
        x = 1316 + k * 28
        sz = size_of(cid)
        tagtxt = T(cid).split(" · ")[1]
        yy = 104 + k * 34
        s.wire([(x, yp), (x, yy), (1440, yy)], "pos", sz)
        s.fuse(1415, yy, "h", ref, rating)
        s.offsheet(1440, yy, "r", f"{cid}+ ← {src}", f"{tagtxt} · sheet E4")
        yy2 = 684 + k * 26
        s.wire([(x, yn), (x, yy2), (1440, yy2)], "neg", sz)
        s.offsheet(1440, yy2, "r", f"{cid}− ← {src} (E4)")
    # ---------------- power-slide pod feed (v0.12: from the BB3 spare stud, MRBF 30 A)
    s.wire([(1100, yp), (1100, 178), (1112, 178)], "pos", "6")
    s.fuse(1100, 214, "v", "F17", "MRBF 30 A", side=-1)
    s.offsheet(1112, 178, "r", "DO2+ → power-slide pod", "6 mm² high-flex · chain · sheet E3")
    s.wire([(1090, yn), (1090, 728)], "neg", "6")
    s.offsheet(1090, 728, "l", "DO2− → power-slide pod", "sheet E3")
    USED.add("DO2")
    # ---------------- battery heater feed (v0.14, sheet E16): BB3 -> F18 10 A -> TH1; return to BB4
    s.wire([(1300, yp), (1300, 380), (1330, 380)], "pos", "2.5")
    s.fuse(1300, 330, "v", "F18", "10 A", side=1)
    s.offsheet(1330, 380, "r", "HTR+ → TH1 battery heater", "2.5 mm² twin · sheet E16")
    s.wire([(1300, yn), (1300, 560), (1330, 560)], "neg", "2.5")
    s.offsheet(1330, 560, "r", "HTR− ← TH1 battery heater", "sheet E16")
    USED.add("HTR")
    # ---------------- DC distribution feed
    s.wire([(1440, yp), (1500, yp)], "pos", "25")
    s.fuse(1472, yp, "h", "F7", "MEGA 100 A", side=-1)
    s.offsheet(1500, yp, "r", "DCF+ → FB1", f"{T('DCF').split(' · ')[1]} · E3")
    s.wire([(1440, yn), (1500, yn)], "neg", "25")
    s.offsheet(1500, yn, "r", "DCF− → FB1", "sheet E3")
    # ---------------- chassis bond (system side of the shunt, so the shunt sees all current)
    s.wire([(1150, yn), (1150, 705)], "neg", "25")
    s.earth(1150, 705)
    s.tag(1150, 684, T("CHB"))
    s.text(1170, 735, "chassis rail bond, via the gland", size=10.5)
    # ---------------- notes
    y0 = 800
    s.note(46, y0, 380, ["- B1P = B2P and B1N = B2N: cut each pair to the",
                         "  longer length (schedule) with identical lugs.",
                         "- F1/F2 MRBF 300 A sit directly on each + stud.",
                         "- RB1/RB2/SH1/SH2 120 mm² (v0.13): both MRBFs",
                         "  in parallel can deliver 600 A into them.",
                         "- Tinned fine-strand, hex-crimped, adhesive",
                         "  heat-shrink; re-torque after 500 km."], title="Battery bank")
    s.note(440, y0, 390, ["- QS1 opens bank + → system +. BB3 stays live",
                          "  from the chargers: open QP1–QP3, S2 off and",
                          "  ignition off BEFORE opening QS1, so no charger",
                          "  runs without the battery.",
                          "- Only F10 (QS1 control) and F11 (TS1 sensor",
                          "  lead) stay live on the bank side.",
                          "- S2 off before closing QS1 (MultiPlus inrush)."], title="Isolation")
    s.note(844, y0, 390, ["- DC: one bond only, BB4 → chassis (CHB 25 mm²).",
                          "- MultiPlus case → BB4 (PE1, Victron: = DC −).",
                          "- AC earth bar → chassis bond (PE2, 6 mm² G/Y),",
                          "  not via the DC negative (E5).",
                          "- Orion XS non-isolated: ALT − lands on the body",
                          "  earth, chassis side of the battery sensor (E4)."], title="Earthing")
    s.note(1248, y0, 386, ["- F3: Class-T 400 A, holder bolted beside BB3:",
                           "  CT1 link < 200 mm, so F3 is at the source.",
                           "- CT1 / INVP / INVN: 2 × 50 mm² per pole;",
                           "  INVP + CT1 ≈ 1.2 m route, through the window.",
                           "- MIDI F4–F6 and MEGA F7 on the BB3 studs;",
                           "  F6 40 A serves MPT and MPV (6 mm² each)."], title="Victron MultiPlus-II 12/3000")
    return s


# ======================================================================================= E3
FB1_WAYS = [  # way, circuit, fuse, cable, destination
    (1, "Rear Anderson 1", "30 A", "DO1A"), (2, "Rear Anderson 2", "30 A", "DO1B"), (3, "Rear USB-C ×2", "25 A", "DO1C"),
    (4, "Rear 12 V socket", "15 A", "DO1D"), (5, "spare (pod moved to the bay)", "–", ""), (6, "Cabin compute feed", "15 A", "DO3"),
    (7, "Starlink Mini", "7.5 A", "DO4"), (8, "Tent 12 V", "20 A", "DO5"), (9, "Cerbo GX", "2 A", "CGX"),
    (10, "Visor drive", "20 A", "VIS"), (11, "spare", "–", ""), (12, "spare", "–", "")]


def _twin_lr(s, x0, y, x1, size, tag=None, tag_x=None):
    """Left-to-right twin with + exactly on y (− drawn just below)."""
    s.twin([(x0, y + 3.5), (x1, y + 3.5)], kinds=("neg", "pos"), size=size, tag=tag,
           tag_at=(tag_x, y + 3.5) if tag_x else None)


def sheet_dc_dist():
    s = Sheet(3, "dc-dist", "DC distribution: fuse block and 12 V outlets",
              "FB1 in the rear control cabinet feeds every 12 V outlet. Twin cables: + from the numbered way, − to the FB1 negative bus.", TOTAL)
    s.zone(285, 92, 860, 860, "Rear control cabinet", "passenger side, behind the arch", bottom=True)
    s.zone(600, 116, 530, 200, "Rear panel", "hinged door, faces the tailgate", bottom=True)
    s.zone(1160, 318, 470, 172, "Power slide pod", "sockets face up", bottom=True, lx=180)
    s.zone(1160, 500, 470, 165, "Cabin", "compute box under the rear seat", bottom=True, lx=180)
    s.zone(1160, 672, 130, 280, "Gap junction", "cab–tub gap", bottom=True)
    s.zone(1310, 866, 320, 86, "Roof platform", "visor drive", bottom=True, lx=12)
    s.zone(1310, 672, 320, 54, "Roof platform", bottom=True)
    s.zone(1310, 740, 320, 118, "Tent services box", "detaches with the tent", bottom=True, lx=110)
    ways = {1: 150, 2: 190, 3: 230, 4: 270, 5: 360, 6: 520, 7: 690, 8: 780, 9: 840, 10: 885}
    terms = [("in", "L", 60, "+IN"), ("neg", "L", 795, "−BUS")]
    for w, circ, fuse, cid in FB1_WAYS:
        if w in ways:
            terms.append((f"w{w}", "R", ways[w] - 110, f"{w}·{fuse}"))
    fb = s.block("FB1", 330, 110, 190, 800, "Fuse block",
                 ["Blue Sea 5026 (12-way ATC)", "with negative bus", "", "ways 5, 11, 12 spare", "", "feed: DCF 35 mm² twin",
                  "from F7 MEGA 100 A"], cat="prot", terms=terms)
    s.wire([(250, 170), fb.t("in")], "pos", "25")
    s.offsheet(250, 170, "l", "DCF+ ← F7", "BB3 · sheet E2")
    USED.add("DCF")
    s.wire([(250, 905), fb.t("neg")], "neg", "25")
    s.offsheet(250, 905, "l", "DCF− ← BB4", "sheet E2")
    xo = fb.x + fb.w
    # ---- rear panel (ways 1-4)
    blk = {}
    for w, ref, title in ((1, "X1", "Anderson SB50 (rear 1)"), (2, "X2", "Anderson SB50 (rear 2)"), (3, "U7", "USB-C 100 W + 20 W (rear 1)"),
                          (4, "X6", "12 V socket (rear)")):
        y = ways[w]
        blk[w] = s.block(ref, 660, y - 15, 220, 30, title, cat="outlet", terms=[("i", "L", 15, "")])
        cid = FB1_WAYS[w - 1][3]
        _twin_lr(s, xo, y, 660, size_of(cid), tag=T(cid), tag_x=590)
    u8 = s.block("U8", 920, ways[3] - 15, 200, 30, "USB-C 100 W + 20 W (rear 2)", cat="outlet", terms=[("i", "L", 15, "")])
    _twin_lr(s, 880, ways[3], 920, "4")
    s.text(900, ways[3] + 22, T("DO1E"), size=9.5, anchor="middle", family=MONO, fill="#495057")
    # ---- power slide pod (way 5): twin trunk → local fuse block → outlets
    for w, cid, fbref, zone_txt, outs in (
            (5, "DO2", "FB2", "not on FB1 · bay → slide front → chain", (("X3", "Anderson SB50 (pod)", "F14 20 A"), ("X7", "12 V socket (pod)", "F13 15 A"))),):
        y = ways[w]
        lf = s.block(fbref, 1180, y - 20, 140, 130, "Local fuses", ["ATC holder ×2", "+ / − studs"], cat="prot",
                     terms=[("i", "L", 20, "")] + [(f"o{k + 1}", "R", off, "") for k, off in enumerate((20, 65, 105)[:len(outs)])])
        _twin_lr(s, 820, y, 1180, "6", tag=T(cid), tag_x=960)
        s.offsheet(820, y + 3.5, "l", "DO2 ← BB3 MRBF 30 A (F17)", "front bay · sheet E2")
        s.text(1000, y - 10, zone_txt, size=10, italic=True, anchor="middle", fill="#495057")
        for k, (ref, title, fz) in enumerate(outs):
            oy = lf.t(f"o{k + 1}")[1]
            s.block(ref, 1420, oy - 15, 200, 30, title, cat="outlet", terms=[("i", "L", 15, "")])
            _twin_lr(s, 1320, oy, 1420, "6" if k == 0 else "2.5")
            s.text(1370, oy - 9, fz, size=9.5, anchor="middle", weight="600", fill="#8a4500")
    # ---- cabin compute feed (way 6): SB50 inlet → compute box (BatteryProtect + per-device fuses)
    y = ways[6]
    _twin_lr(s, xo, y, 1340, "6", tag=T("DO3"), tag_x=760)
    s.text(980, y - 10, "via gland → chassis rail → cabin grommet", size=10, italic=True, anchor="middle", fill="#495057")
    s.conn(1225, y + 3.5, "h", "X4", "SB50 inlet", side=1)
    s.block("U12", 1340, y - 15, 270, 110, "Compute box (under the seat)",
            ["Smart BatteryProtect (low-V cut)", "FB3: PC · router · PoE switch · fan", "smart-ute system: see", "docs/smart-ute-research.md"],
            cat="gen", terms=[("i", "L", 15, "")])
    # ---- Starlink (way 7) and tent 12 V (way 8)
    y = ways[7]
    _twin_lr(s, xo, y, 1340, "4", tag=T("DO4"), tag_x=760)
    s.gland(1225, y + 3.5, "")
    s.block("ST1", 1340, y - 15, 270, 30, "Starlink Mini (roof, inside frame)", cat="outlet", terms=[("i", "L", 15, "")])
    y = ways[8]
    _twin_lr(s, xo, y, 1225, "10", tag=T("DO5"), tag_x=760)
    s.twin([(1225, y + 3.5), (1356.5, y + 3.5), (1356.5, y + 30)], kinds=("neg", "pos"), size="10")
    s.conn(1225, y + 3.5, "h", "J3", "SB50 red", side=1)
    s.tag(1440, y + 3.5, T("T1D", "tent 12 V + PV"))
    s.block("X5", 1340, y + 30, 270, 30, "Anderson SB50 (tent 12 V)", cat="outlet", terms=[("i", "T", 20, "")])
    # ---- Cerbo power (way 9)
    y = ways[9]
    s.block("U5", 660, y - 15, 220, 30, "Cerbo GX power in", cat="victron", terms=[("i", "L", 15, "")])
    _twin_lr(s, xo, y, 660, "0.75", tag=T("CGX"), tag_x=590)
    # ---- visor drive (way 10, v0.11)
    y = ways[10]
    _twin_lr(s, xo, y, 1340, "10", tag=T("VIS"), tag_x=760)
    s.gland(1225, y + 3.5, "")
    s.block("U11", 1340, y - 15, 270, 30, "Visor controller (detail E9)", cat="gen", terms=[("i", "L", 15, "")])
    # ---- way table + notes (left column)
    rows = [(w, c, f, cid or "–") for w, c, f, cid in FB1_WAYS]
    s.table(46, 330, ["Way", "Circuit", "ATC", "Cable"], rows, [34, 112, 40, 46], size=10, rh=17, title="FB1 ways")
    s.note(46, 600, 232, ["- ATC blade fuses, rating on the",
                          "  way label and in the lid.",
                          "- Size each fuse to protect its",
                          "  cable, not the device.",
                          "- Pod: one 30 A feed (F17, bay);",
                          "  FB2: X3 20 A, X7 15 A.",
                          "- Cabin: SB50 inlet to the",
                          "  compute box (PC + network).",
                          "- USB-C sockets: 100 W PD +",
                          "  20 W each (Treklo, 120 W);",
                          "  rear pair ~22 A at 12 V."], title="Notes", size=10, lh=14)
    return s


# ======================================================================================= E4
def _panel(s, ref, x, y, title, model, w=130, h=78):
    return s.block(ref, x, y, w, h, title, [model], cat="pv", terms=[("p", "T", 30, "+"), ("n", "B", w - 30, "−")])


def sheet_charging():
    s = Sheet(4, "charging", "Charging: alternator (DC-DC) and solar",
              "Four independent chargers in the front bay, each output fused at the system busbars (sheet E2).", TOTAL)
    s.zone(46, 92, 420, 250, "Engine bay")
    s.zone(46, 358, 420, 250, "Roof platform", "fixed array")
    s.zone(46, 624, 420, 300, "Tent roof", "detachable array")
    s.zone(500, 358, 150, 566, "Gap junction")
    s.zone(690, 92, 610, 832, "Front bay: charging board", "front wall, above the inverter")
    # ---------------- alternator path
    s.block("G1", 70, 140, 150, 50, "Alternator", ["smart / variable"], cat="vehicle", terms=[("o", "B", 75, "")])
    bt0 = s.block("BT0", 70, 230, 170, 90, "Start battery", ["factory 12 V AGM/EFB"], cat="vehicle",
                  terms=[("i", "T", 75, ""), ("p", "R", 30, "+"), ("n", "R", 70, "−")])
    s.wire([(145, 190), (145, 230)], "fact")
    fbx = s.block("FBX", 280, 118, 150, 52, "Engine fuse box", ["ignition add-a-fuse"], cat="vehicle", terms=[("o", "R", 36, "IGN")])
    u2 = s.block("U2", 760, 150, 260, 170, "DC-DC charger",
                 ["Victron Orion XS 12/12-50A", "non-isolated, 50 A out", "input limit 25–30 A (alternator", "rating unknown)", "VE.Direct → Cerbo USB (E6)"],
                 cat="victron", terms=[("ip", "L", 50, "IN+"), ("in", "L", 90, "IN−"), ("h", "L", 140, "H"), ("op", "R", 50, "OUT+"), ("on", "R", 90, "OUT−")])
    x, y = bt0.t("p")
    s.wire([(x, y), (700, y), (700, u2.t("ip")[1]), u2.t("ip")], "pos", "25")
    s.fuse(275, y, "h", "F8", "MIDI 60 A")
    x, y = bt0.t("n")
    s.wire([(x, y), (720, y), (720, u2.t("in")[1]), u2.t("in")], "neg", "25")
    s.text(300, 312, "ALT − on the body earth (chassis side of the battery sensor)", size=9.5, italic=True, fill="#495057")
    s.tag(560, 260, T("ALT"))
    s.text(560, 330, "via chassis rail → factory-outlet gland", size=10, italic=True, anchor="middle", fill="#495057")
    x, y = fbx.t("o")
    s.wire([(x, y), (660, y), (660, u2.t("h")[1]), u2.t("h")], "sig", "1")
    s.fuse(500, y, "h", "F9", "2 A")
    s.tag(560, y, T("IGN"))
    # ---------------- roof array: two fixed panels in parallel (v0.13: the visor panel has its own MPPT, U13)
    pv1 = _panel(s, "PV1", 62, 402, "190 W", "BlueSolar", w=112)
    pv2 = _panel(s, "PV2", 192, 402, "130 W", "BlueSolar", w=112)
    yp_, yn_ = 392, 490
    for pv in (pv1, pv2):
        x, y = pv.t("p")
        s.wire([(x, y), (x, yp_)], "pvp", "10")
        x, y = pv.t("n")
        s.wire([(x, y), (x, yn_)], "pvn", "10")
    s.dot(pv2.t("p")[0], yp_, "pvp")
    s.dot(pv2.t("n")[0], yn_, "pvn")
    s.text(183, 504, "parallel via MC4 Y-branch", size=10, italic=True, anchor="middle", fill="#495057")
    u3 = s.block("U3", 760, 372, 260, 120, "MPPT roof",
                 ["Victron SmartSolar MPPT 100/30", "PV1 + PV2 = 320 W, 30 A out", "VE.Direct 2 → Cerbo (E6)"],
                 cat="victron", terms=[("pp", "L", 30, "PV+"), ("pn", "L", 80, "PV−"), ("op", "R", 30, "BAT+"), ("on", "R", 70, "BAT−")])
    s.wire([(pv1.t("p")[0], yp_), (600, yp_), (600, u3.t("pp")[1]), u3.t("pp")], "pvp", "10")
    s.wire([(pv1.t("n")[0], yn_), (620, yn_), (620, u3.t("pn")[1]), u3.t("pn")], "pvn", "10")
    s.gland(560, yp_, "", side=1)
    s.switch(700, u3.t("pp")[1], "h", "QP1", "PV isolator", side=1)
    s.switch(700, u3.t("pn")[1], "h", "", "", side=-1)
    s.tag(480, yp_, T("PVR"))
    # ---------------- visor panel: PVV in its chain to the couplers at U11, PVS down to its own MPPT
    pv5 = _panel(s, "PV5", 322, 516, "250 W visor", "E9", w=112)
    u13 = s.block("U13", 760, 520, 260, 110, "MPPT visor",
                  ["Victron SmartSolar MPPT 100/20", "own charger: panel voltage free", "VE.Direct-USB → Cerbo USB 2 (E6)"],
                  cat="victron", terms=[("pp", "L", 30, "PV+"), ("pn", "L", 70, "PV−"), ("op", "R", 30, "BAT+"), ("on", "R", 64, "BAT−")])
    x, y = pv5.t("p")
    s.wire([(x, y), (x, 507), (640, 507), (640, u13.t("pp")[1]), u13.t("pp")], "pvp", "6")
    x, y = pv5.t("n")
    s.wire([(x, y), (x, 600), (660, 600), (660, u13.t("pn")[1]), u13.t("pn")], "pvn", "6")
    s.conn(470, 507, "h", "", "", side=1)
    s.conn(470, 600, "h", "", "", side=-1)
    s.text(470, 537, "MC4 at U11", size=9.5, anchor="middle", fill="#495057")
    s.tag(540, 507, T("PVV", "4 mm² chain"))
    s.tag(560, 600, T("PVS"))
    s.switch(700, u13.t("pp")[1], "h", "QP3", "PV isolator", side=1)
    s.switch(700, u13.t("pn")[1], "h", "", "", side=-1)
    # ---------------- tent array: two flexible panels in series
    pv3 = _panel(s, "PV3", 80, 720, "100 W flex", "Sunman eArc")
    pv4 = _panel(s, "PV4", 260, 720, "100 W flex", "Sunman eArc")
    x3p, y3p = pv3.t("p")
    x3n, y3n = pv3.t("n")
    x4p, y4p = pv4.t("p")
    x4n, y4n = pv4.t("n")
    s.wire([(x3n, y3n), (x3n, y3n + 22), (235, y3n + 22), (235, 690), (x4p, 690), (x4p, y4p)], "pvp", "6")
    s.text(240, 680, "series link", size=9.5, fill="#495057")
    u4 = s.block("U4", 760, 700, 260, 170, "MPPT tent",
                 ["Victron SmartSolar MPPT 75/15", "PV ≤ 75 V Voc, 15 A out", "2 × 100 W in series", "VE.Direct 3 → Cerbo (E6)"],
                 cat="victron", terms=[("pp", "L", 50, "PV+"), ("pn", "L", 120, "PV−"), ("op", "R", 50, "BAT+"), ("on", "R", 90, "BAT−")])
    s.wire([(x3p, y3p), (x3p, 660), (620, 660), (620, u4.t("pp")[1]), u4.t("pp")], "pvp", "6")
    s.wire([(x4n, y4n), (x4n, 900), (620, 900), (620, u4.t("pn")[1]), u4.t("pn")], "pvn", "6")
    s.conn(560, 660, "h", "J4", "SB50 grey", side=1)
    s.conn(560, 900, "h", "", "", side=-1)
    s.tag(440, 660, T("T2", "tent PV"))
    s.tag(660, 900, T("PVT"))
    s.switch(690, u4.t("pp")[1], "h", "QP2", "PV isolator", side=1)
    s.switch(690, u4.t("pn")[1], "h", "", "", side=-1)
    # ---------------- outputs to the system busbars
    for u, cid, ref, rating in ((u2, "ORO", "F4", "MIDI 70 A"), (u3, "MPR", "F5", "MIDI 40 A"), (u4, "MPT", "F6", "MIDI 40 A"),
                                (u13, "MPV", "F6", "shared")):
        sz = size_of(cid)
        x, y = u.t("op")
        s.wire([(x, y), (1320, y)], "pos", sz)
        s.fuse(1120, y, "h", ref, rating)
        s.offsheet(1320, y, "r", f"{cid}+ → BB3", "sheet E2")
        x, y = u.t("on")
        s.wire([(x, y), (1320, y)], "neg", sz)
        s.offsheet(1320, y, "r", f"{cid}− → BB4", "sheet E2")
        s.tag(1220, y - 20, T(cid))
    # ---------------- settings
    s.note(46, 936, 1030, ["- Absorption / float / no temperature compensation set to iTechworld's LiFePO₄ figures in all four chargers (the BMS has no Victron link).",
                           "- Orion XS: charger mode, input limit 25–30 A until the alternator rating is known; IGN on H. Two panels in parallel need no string fuses.",
                           "- DVCC on, SmartShunt as the battery monitor (Venus OS ≥ 3.20). QP1–QP3: 2-pole DC isolators; open them before QS1 (sheet E2)."],
           title="Charger settings", size=10.5, lh=15)
    return s


# ======================================================================================= E5
AC_GAP = 10


def _ac_terms(prefix, side, off, labels=True, flip=False):
    """Three AC terminals (L, N, PE) 10 px apart; one group label. flip puts PE on top."""
    lab = "L N PE" if not flip else "PE N L"
    o = (-AC_GAP, 0, AC_GAP) if not flip else (AC_GAP, 0, -AC_GAP)
    first = min(o)
    return [(f"{prefix}{k}", side, off + d, (lab if (labels and d == first) else "")) for k, d in zip("LNE", o)]


def _ac(s, a, b, pts_mid=None, size="2.5", tag=None, tag_at=None):
    """3-core run between two (L, N, E) terminal triples; pts_mid(k, p0, p1) gives the bends for conductor k."""
    for k, kind in ((0, "L"), (1, "N"), (2, "PE")):
        p0, p1 = a[k], b[k]
        if pts_mid is None:
            pts = [p0, (p1[0], p0[1])] if abs(p0[1] - p1[1]) < 0.5 else [p0, ((p0[0] + p1[0]) / 2, p0[1]), ((p0[0] + p1[0]) / 2, p1[1]), p1]
        else:
            pts = [p0] + pts_mid(k, p0, p1) + [p1]
        s.wire(pts, kind, size)
    if tag:
        s.tag(*(tag_at or ((a[1][0] + b[1][0]) / 2, a[1][1])), tag)


def _tr(b, p):
    return (b.t(p + "L"), b.t(p + "N"), b.t(p + "E"))


def sheet_ac():
    s = Sheet(5, "ac", "230 V AC: shore inlet, inverter output, RCBOs and outlets",
              "Licensed electrician to install and certify (AS/NZS 3000, AS/NZS 3001.2). Active brown · neutral blue · earth green/yellow.", TOTAL)
    s.zone(46, 92, 360, 930, "Tent services box", "under the tent, front, inset", bottom=True)
    s.zone(436, 92, 160, 930, "Gap junction", "cab–tub gap", bottom=True)
    s.zone(626, 92, 340, 450, "Front bay", "", bottom=True)
    s.zone(996, 92, 638, 516, "Rear control cabinet", "", bottom=True)
    s.zone(1330, 626, 304, 170, "Power slide pod", "", bottom=True)
    yin = 190                                   # AC-in run (N conductor)
    yout = 330                                  # AC-out run
    # ---- shore inlet → Q4 → T1 → J2 → AC5 → U1 AC-in (all straight)
    xi1 = s.block("XI1", 70, yin - 50, 140, 100, "Shore inlet", ["Clipsal 56AI315", "IP66, 15 A"], cat="ac", terms=_ac_terms("o", "R", 50))
    q4 = s.block("Q4", 260, yin - 25, 100, 50, "RCBO 2-pole", ["16 A 30 mA"], cat="prot",
                 terms=_ac_terms("i", "L", 25, False) + _ac_terms("o", "R", 25, False))
    _ac(s, _tr(xi1, "o"), _tr(q4, "i"))
    u1 = s.block("U1", 680, yin - 60, 260, 300, "MultiPlus-II 12/3000",
                 ["AC-in → transfer switch (32 A)", "  → AC-out 1", "AC-in current limit: 15 A", "Ground relay bonds N–PE while",
                  "inverting, so the RCBOs work", "off-grid (check the AU setting).", "AC-out 2 not used.", "", "Case / PE → BB4 (PE1, E2)"],
                 cat="victron", terms=_ac_terms("i", "L", 60) + _ac_terms("o", "R", yout - (yin - 60)) + [("pe", "B", 130, "CASE")])
    _ac(s, _tr(q4, "o"), _tr(u1, "i"))
    s.conn(516, yin, "h", "J2", "IP66 15 A", side=1)
    s.text(516, yin + 30, "tent: socket", size=9.5, anchor="middle", fill="#5f3dc4")
    s.text(516, yin + 42, "vehicle: inlet", size=9.5, anchor="middle", fill="#5f3dc4")
    s.tag(400, yin + 26, T("T1A", "AC-in cores"))
    s.tag(600, yin - 24, T("AC5"))
    # ---- U1 AC-out → RCBO enclosure (straight) → Q1 / Q2 / Q3
    enc = s.block("RCBO", 1030, yout - 70, 230, 330, "RCBO enclosure", ["IP66, DIN rail, N bar + PE bar", "Q0  main switch 2P 32 A", "",
                                                                         "Q1  10 A 30 mA  → rear GPO"] + [""] * 6 +
                  ["Q2  10 A 30 mA  → pod GPO"] + [""] * 6 + ["Q3  10 A 30 mA  → tent outlet"],
                  cat="prot", terms=_ac_terms("i", "L", 70) + _ac_terms("q1", "R", 70, False) + _ac_terms("q2", "R", 170, False)
                  + _ac_terms("q3", "R", 270, False) + [("pe", "B", 200, "PE bar")])
    _ac(s, _tr(u1, "o"), _tr(enc, "i"), size="4", tag=T("AC1"), tag_at=(985, yout + 34))
    x, y = enc.t("pe")
    s.wire([(x, y), (x, 640)], "PE", "6")
    s.earth(x, 640, "chassis bond")
    s.tag(x, 614, T("PE2"))
    xs1 = s.block("XS1", 1420, yout - 40, 200, 80, "Rear double GPO", ["IP66, 10 A, rear panel"], cat="ac", terms=_ac_terms("i", "L", 40))
    _ac(s, _tr(enc, "q1"), _tr(xs1, "i"), tag=T("AC2"), tag_at=(1340, yout + 34))
    xs2 = s.block("XS2", 1420, 660, 200, 80, "Pod GPO", ["flush, faces up, 10 A"], cat="ac", terms=_ac_terms("i", "L", 40))
    _ac(s, _tr(enc, "q2"), _tr(xs2, "i"), pts_mid=lambda k, p0, p1: [(1380 - k * AC_GAP, p0[1]), (1380 - k * AC_GAP, p1[1])])
    s.tag(1300, yout + 76, T("AC3"))
    s.text(1340, 760, "AC3: through the cable chain, high-flex 3-core", size=9.5, italic=True, fill="#495057")
    # ---- Q3 → AC4 → J1 → T1 → XS3 (heater outlet in the tent box), PE on top so the run never crosses itself
    ybot = 930
    xs3 = s.block("XS3", 70, ybot - 50, 190, 100, "Tent heater outlet", ["Clipsal 56SO310A", "IP66, 10 A"], cat="ac",
                  terms=_ac_terms("i", "R", 50, flip=True))
    q3 = _tr(enc, "q3")
    b = _tr(xs3, "i")
    _ac(s, q3, b, pts_mid=lambda k, p0, p1: [(1300 + k * 0 + (2 - k) * AC_GAP, p0[1]), (1300 + (2 - k) * AC_GAP, p1[1])])
    s.conn(516, ybot, "h", "J1", "IP66 10 A", side=-1)
    s.text(516, ybot - 30, "vehicle: socket", size=9.5, anchor="middle", fill="#5f3dc4")
    s.text(516, ybot - 18, "tent: plug", size=9.5, anchor="middle", fill="#5f3dc4")
    s.tag(820, ybot, T("AC4"))
    s.tag(380, ybot - 26, T("T1A", "AC-out cores"))
    # ---- earth path
    x, y = u1.t("pe")
    s.wire([(x, y), (x, 500)], "PE", "50")
    s.offsheet(x, 500, "d", "PE1 → BB4 (case to DC −)", "sheet E2")
    USED.add("PE1")
    s.note(640, 680, 640, ["- Every 230 V circuit is RCD-protected (30 mA): Q4 (2-pole) on the inlet, Q1–Q3 on AC-out.",
                           "- Q0: 2-pole main switch for the inverter supply (AS/NZS 3001.2). AC1 is 4 mm²: with",
                           "  PowerAssist AC-out can carry ~25 A (15 A shore + inverter).",
                           "- 230 V runs apart from 12 V: own tray compartment, own grommet row, orange conduit",
                           "  outside, separator in the slide chain, own sheath to the tent (T1A).",
                           "- The tent has only two 230 V connections (J1 out, J2 in). They differ in rating and",
                           "  gender, so the tent's outlet can't be plugged into its own inlet.",
                           "- MultiPlus-II: AC-in limit 15 A; enable the ground relay for AU; test every RCD in",
                           "  inverter mode and on shore power before first use.",
                           "- Earth continuity: every metal enclosure and outlet earth back to U1 PE and BB4.",
                           "- Compliance plate and RCD test record inside the rear cabinet door."],
           title="Electrician notes", size=10.5, lh=15)
    return s


# ======================================================================================= E6
def sheet_control():
    s = Sheet(6, "control", "Control and communications",
              "Cerbo GX gathers every Victron device for the GX Touch, Home Assistant and VRM. Hard-wired switches at the rear panel.", TOTAL)
    s.zone(46, 92, 1588, 520, "Monitoring", "Cerbo GX in the rear cabinet")
    s.zone(46, 628, 1588, 400, "Control circuits", "switches on the rear panel", bottom=True, lx=700)
    u5 = s.block("U5", 600, 170, 300, 400, "Cerbo GX MK2",
                 ["Victron GX device, Venus OS ≥ 3.20", "3 × VE.Direct, 2 × VE.Bus (RJ45)", "3 × USB, HDMI, Ethernet, Wi-Fi, BLE",
                  "VE.Can 1/2, relays, tank / temp /", "digital inputs: unused", "", "power: FB1 way 9, 2 A (CGX)"],
                 cat="victron", terms=[("pwr", "L", 300, "PWR"), ("hdmi", "L", 120, "HDMI"), ("usb3", "L", 150, "USB 3"),
                                       ("vb", "R", 40, "VE.Bus"), ("vd1", "R", 100, "VE.Direct 1"), ("vd2", "R", 150, "VE.Direct 2"),
                                       ("vd3", "R", 200, "VE.Direct 3"), ("usb1", "R", 260, "USB 1"), ("usb2", "R", 320, "USB 2"),
                                       ("wifi", "T", 150, "Wi-Fi")])
    u6 = s.block("U6", 90, 250, 230, 80, "GX Touch 50", ["5\" touch display, rear panel"], cat="victron",
                 terms=[("hdmi", "R", 40, ""), ("usb", "R", 70, "")])
    for k in (("hdmi", "hdmi"), ("usb", "usb3")):
        a, b = u6.t(k[0]), u5.t(k[1])
        s.wire([a, ((a[0] + b[0]) / 2 + (0 if k[0] == "hdmi" else 10), a[1]), ((a[0] + b[0]) / 2 + (0 if k[0] == "hdmi" else 10), b[1]), b], "data")
    s.tag(420, 310, T("D3"))
    x, y = u5.t("pwr")
    s.wire([(400, y), (x, y)], "pos", "0.75")
    s.offsheet(400, y, "l", "CGX ← FB1 way 9 (2 A)", "sheet E3")
    devs = [("vb", "U1", "MultiPlus-II", "VE.Bus", "D1"), ("vd1", "P1", "SmartShunt 500 A", "VE.Direct", "D2"),
            ("vd2", "U3", "MPPT 100/30 (roof)", "VE.Direct", "D2"), ("vd3", "U4", "MPPT 75/15 (tent)", "VE.Direct", "D2"),
            ("usb1", "U2", "Orion XS 12/12-50A", "VE.Direct", "D4"), ("usb2", "U13", "MPPT 100/20 (visor)", "VE.Direct", "D5")]
    for port, ref, name, dport, cid in devs:
        a = u5.t(port)
        d = s.block(ref, 1180, a[1] - 22, 260, 44, name, [], cat="victron", terms=[("p", "L", 22, dport)])
        s.wire([a, d.t("p")], "data")
        s.tag(1040, a[1], T(cid))
    s.text(1450, 172, "front bay / charging board", size=10, italic=True, fill="#495057")
    # ---- network
    ha = s.block("HA", 1180, 110, 260, 44, "Home Assistant", [], cat="gen", terms=[("n", "L", 22, "")])
    st = s.block("ST1", 90, 140, 230, 60, "Starlink Mini", ["Wi-Fi router / uplink"], cat="outlet", terms=[("n", "R", 30, "")])
    x, y = u5.t("wifi")
    s.wire([(x, y), (x, 132), ha.t("n")], "wifi")
    s.wire([(x, 132), (x, 170), st.t("n")], "wifi")
    s.text(950, 126, "Victron integration · Modbus-TCP / MQTT", size=10, italic=True, fill="#6f42c1")
    s.text(360, 164, "Wi-Fi (VRM uplink, optional)", size=10, italic=True, fill="#6f42c1")
    # ---- battery switch S1 ↔ ML-RBS (4-core SW1)
    s1 = s.block("S1", 90, 680, 240, 150, "Battery isolate switch", ["Blue Sea 2155 Contura", "SPDT ON-ON with LED", "rear panel"],
                 cat="prot", terms=[("v", "R", 30, "+12V"), ("c", "R", 60, "CTRL"), ("l", "R", 90, "LED"), ("g", "R", 120, "GND")])
    qs = s.block("QS1", 700, 680, 260, 150, "ML-RBS 7713 control harness", ["red: CONTROL (high = close)", "yellow: LED OUTPUT",
                                                                              "black: GROUND", "verify colours vs Blue Sea doc"],
                 cat="prot", terms=[("c", "L", 60, "red"), ("l", "L", 90, "yel"), ("g", "L", 120, "blk"), ("g2", "R", 120, "")])
    x, y = s1.t("v")
    s.wire([(x, y), (380, y), (380, 662), (1000, 662)], "pos", "1")
    s.offsheet(1000, 662, "r", "RBF ← BB1 via F10 2 A", "bank side, always live · E2")
    USED.add("RBF")
    s.wire([s1.t("c"), qs.t("c")], "ctrl", "1")
    s.wire([qs.t("l"), s1.t("l")], "sig", "1")
    s.wire([s1.t("g"), qs.t("g")], "neg", "1")
    x, y = qs.t("g2")
    s.wire([(x, y), (1000, y)], "neg", "1")
    s.offsheet(1000, y, "r", "→ BB4 system −", "sheet E2")
    s.tag(520, 740, T("SW1"))
    # ---- inverter remote S2 ↔ MultiPlus remote L/H (SW2)
    s2 = s.block("S2", 90, 850, 240, 64, "Inverter on/off", ["SPST rocker, rear panel"], cat="prot",
                 terms=[("a", "R", 25, "1"), ("b", "R", 48, "2")])
    rm = s.block("U1", 700, 850, 260, 64, "MultiPlus-II remote on/off", ["remove the factory L–H bridge"], cat="victron",
                 terms=[("L", "L", 25, "L"), ("H", "L", 48, "H")])
    s.wire([s2.t("a"), rm.t("L")], "ctrl", "1")
    s.wire([s2.t("b"), rm.t("H")], "ctrl", "1")
    s.tag(520, 875, T("SW2"))
    # ---- visor button S3 (v0.11) -> visor controller (E9)
    s3 = s.block("S3", 90, 934, 240, 80, "Visor deploy / stow", ["momentary rocker + LED, rear panel"], cat="prot",
                 terms=[("d", "R", 20, "DEP"), ("s", "R", 36, "STOW"), ("l", "R", 52, "LED"), ("c", "R", 68, "COM")])
    for k, kind in (("d", "ctrl"), ("s", "ctrl"), ("l", "sig"), ("c", "neg")):
        x, y = s3.t(k)
        s.wire([(x, y), (640, y)], kind, "1")
    s.offsheet(640, 978, "r", "VSW (4-core) → U11 visor controller", "roof · sheet E9")
    s.tag(500, 960, T("VSW"))
    # ---- Orion ignition sense
    ig = s.block("U2", 1340, 700, 260, 64, "Orion XS remote on/off", ["H ← ignition 12 V (IGN)", "remove the L–H bridge"], cat="victron",
                 terms=[("H", "L", 25, "H")])
    s.wire([(1300, 725), ig.t("H")], "sig", "1")
    s.offsheet(1300, 725, "l", "IGN ← F9 2 A (E4)")
    USED.add("IGN")
    s.wire([(1315, 725), (1315, 790), (1340, 790)], "sig", "0.75")
    s.dot(1315, 725, "sig", r=3.2)
    s.offsheet(1340, 790, "r", "VIG: ignition → U11 visor interlock", "sheet E9")
    USED.add("VIG")
    s.note(1180, 840, 450, ["- S1 drives QS1 open/closed; QS1 latches, so S1 position is",
                            "  the command and the LED confirms the contacts.",
                            "- S2 open = MultiPlus fully off (inverter and charger).",
                            "  Modes (on / charger only) are also on the GX Touch."], size=10, lh=14)
    return s


# ======================================================================================= E7
def sheet_tent():
    s = Sheet(7, "tent", "Detachable tent harness and gap junction",
              "Four keyed connectors at the cab–tub gap. Unplug J1–J4, cap them, and the tent lifts off with its harness and services box.", TOTAL)
    s.zone(46, 92, 520, 540, "Tent services box", "under the tent, front, inset · stays with the tent", bottom=True)
    s.zone(640, 92, 300, 540, "Gap junction box", "IP66, barrier: 230 V side | 12 V side", bottom=True)
    s.zone(1000, 92, 634, 540, "Vehicle", bottom=True)
    tr = lambda b, p: (b.t(p + "L"), b.t(p + "N"), b.t(p + "E"))   # noqa: E731
    xs3 = s.block("XS3", 80, 128, 180, 70, "Heater outlet", ["IP66 10 A"], cat="ac", terms=_ac_terms("o", "R", 36))
    xi1 = s.block("XI1", 80, 220, 120, 70, "Shore inlet", ["IP66 15 A"], cat="ac", terms=_ac_terms("o", "R", 36))
    q4 = s.block("Q4", 240, 235, 110, 50, "RCBO 2-pole", ["16 A 30 mA"], cat="prot", terms=_ac_terms("i", "L", 21, False) + _ac_terms("o", "R", 21, False))
    _ac(s, tr(xi1, "o"), tr(q4, "i"))
    x5 = s.block("X5", 80, 330, 180, 56, "Anderson SB50", ["tent 12 V (lights, fans)"], cat="outlet", terms=[("p", "R", 24, "+"), ("n", "R", 36, "−")])
    pvj = s.block("PVJ", 80, 420, 180, 70, "PV bulkhead (MC4)", ["T2 ← tent-top junction box", "PV3 + PV4 in series (E4)"], cat="pv",
                  terms=[("p", "R", 30, "+"), ("n", "R", 42, "−")])
    xc = 790
    ys = dict(J1=160, J2=260, J3=360, J4=460)
    # J1: 230 V to the tent (vehicle socket, tent plug)
    a = tr(xs3, "o")
    for k, kind in enumerate(("L", "N", "PE")):
        y = ys["J1"] - AC_GAP + AC_GAP * k
        s.wire([a[k], (500, a[k][1]), (500, y), (1060, y)], kind, "2.5")
    s.conn(xc, ys["J1"], "h", "J1", "230 V OUT · IP66 10 A")
    s.offsheet(1060, ys["J1"], "r", "AC4 ← Q3 RCBO", "sheet E5")
    USED.add("AC4")
    # J2: shore power from the tent (tent socket, vehicle inlet)
    a = tr(q4, "o")
    for k, kind in enumerate(("L", "N", "PE")):
        y = ys["J2"] - AC_GAP + AC_GAP * k
        s.wire([a[k], (470, a[k][1]), (470, y), (1060, y)], kind, "2.5")
    s.conn(xc, ys["J2"], "h", "J2", "230 V IN · IP66 15 A")
    s.offsheet(1060, ys["J2"], "r", "AC5 → U1 AC-in", "sheet E5")
    USED.add("AC5")
    # J3: tent 12 V
    for (pt, kind, dy) in ((x5.t("p"), "pos", -4), (x5.t("n"), "neg", 4)):
        y = ys["J3"] + dy
        s.wire([pt, (440, pt[1]), (440, y), (1060, y)], kind, "10")
    s.conn(xc, ys["J3"], "h", "J3", "12 V · Anderson SB50 red")
    # v0.14: water-can heater tapped off the box's 12 V (sheet E16)
    for (pt, kind, xx) in ((x5.t("p"), "pos", 350), (x5.t("n"), "neg", 364)):
        s.dot(xx, pt[1], kind, r=3.2)
        s.wire([(xx, pt[1]), (xx, 570), (380, 570)] if kind == "pos" else [(xx, pt[1]), (xx, 586), (380, 586)], kind, "1.5")
    s.offsheet(380, 578, "r", "WHT → F19 → TH2 → HP3 water pad", "1.5 mm² twin · sheet E16")
    s.offsheet(1060, ys["J3"], "r", "DO5 ← FB1 way 8 (20 A)", "sheet E3")
    USED.add("DO5")
    # J4: tent PV
    for (pt, kind, dy) in ((pvj.t("p"), "pvp", -4), (pvj.t("n"), "pvn", 4)):
        y = ys["J4"] + dy
        s.wire([pt, (420, pt[1]), (420, y), (1060, y)], kind, "6")
    s.conn(xc, ys["J4"], "h", "J4", "PV · Anderson SB50 grey")
    s.offsheet(1060, ys["J4"], "r", "PVT → QP2 → U4 MPPT 75/15", "sheet E4")
    USED.add("PVT")
    s.tag(600, 212, T("T1A", "230 V: 2 × 2.5 mm² 3-core"))
    s.tag(600, 412, T("T1D", "12 V 10 mm² + PV 6 mm²"))
    s.tag(200, 508, T("T2", "tent top → box, via the front hinge"))
    # pass-throughs
    for k, (cid, txt, kind) in enumerate((("DO4", "Starlink 4 mm² twin", "pos"), ("PVR", "roof PV 10 mm² pair", "pvp"),
                                          ("PVS", "visor PV 6 mm² pair", "pvp"), ("VIS", "visor drive 10 mm² twin", "pos"),
                                          ("VSW", "visor button 4-core", "ctrl"), ("VIG", "visor interlock 1 mm²", "sig"))):
        y = 500 + k * 16
        s.wire([(660, y), (1060, y)], kind, "1")
        s.text(670, y - 4, f"{cid} {txt} · pass-through (not detachable)", size=9, fill="#495057")
    s.gland(xc, 540, "")
    USED.update(["DO4", "PVR", "PVS", "VIS", "VSW", "VIG"])
    # pinout tables
    hdr = ["Pin", "Function", "Conductor", "Vehicle side", "Tent side"]
    wd = [42, 120, 150, 150, 150]
    y = 660
    y = s.table(46, y, hdr, [("A", "Active", "2.5 mm² brown", "socket (live)", "plug"), ("N", "Neutral", "2.5 mm² blue", "", ""),
                             ("E", "Earth", "2.5 mm² green/yellow", "", "")], wd, title="J1 · 230 V out to tent · IP66 10 A (Clipsal 56 series)")
    y = s.table(46, y + 28, hdr, [("A", "Active (shore)", "2.5 mm² brown", "appliance inlet", "socket (live)"), ("N", "Neutral", "2.5 mm² blue", "", ""),
                                  ("E", "Earth", "2.5 mm² green/yellow", "", "")], wd, title="J2 · 230 V shore in · IP66 15 A inlet + extension socket")
    y2 = s.table(700, 660, ["Pin", "Function", "Conductor"], [("+", "12 V +", "10 mm² red"), ("−", "12 V −", "10 mm² black")],
                 [42, 100, 120], title="J3 · 12 V · Anderson SB50 red")
    s.table(700, y2 + 28, ["Pin", "Function", "Conductor"], [("+", "PV +", "6 mm² solar"), ("−", "PV −", "6 mm² solar")],
            [42, 100, 120], title="J4 · PV · Anderson SB50 grey")
    s.note(1000, 650, 634, ["1. Switch the inverter off (S2) and isolate shore power at the source.",
                            "2. Unplug J2 (shore in) first, then J1, J3, J4.",
                            "3. Fit the caps to all eight halves (IP66 caps / SB50 dust covers).",
                            "4. Unclip T1A and T1D from the lid-front saddles, then lift the tent.",
                            "Refit in reverse. SB50 colours are keyed: red and grey won't mate,",
                            "and J1/J2 differ in rating and gender, so nothing can cross-connect."],
           title="Detach / refit", size=10.5, lh=15)
    return s


# ======================================================================================= E1 bundles
EDGE_RUNS = {("CH_ENGINE", "CH_CABIN"): ["R19"], ("CH_CABIN", "CH_GAP"): ["R18"], ("CH_GAP", "CH_REAR"): ["R16", "R17"],
             ("ENGINE", "CH_ENGINE"): ["R21"], ("CABIN", "CH_CABIN"): ["R20"], ("CH_GAP", "JUNCTION"): ["R22", "R23"],
             ("JUNCTION", "ROOF"): ["R25"], ("JUNCTION", "TENT"): ["R27", "R28"], ("CH_REAR", "GLAND"): ["R14", "R15"],
             ("GLAND", "TRAY"): ["R09", "R10"], ("TRAY", "BAY"): ["R07", "R08"], ("TRAY", "CABINET"): ["R11", "R12"],
             ("BAY", "POD"): ["R29", "R30"]}


def bundles():
    """Which cables share each physical run on the overview, from the model's runs (R-codes)."""
    runs = {r["code"]: r for r in ROUTES["runs"]}
    edges, on_edge = {}, set()
    for e, codes in EDGE_RUNS.items():
        ids = []
        for code in codes:
            for m in runs[code]["members"]:
                if m not in ids:
                    ids.append(m)
        if ids:
            edges[e] = ids
            on_edge.update(ids)
    internal = {"BAY": [], "CABINET": [], "ROOF": [], "TENT": []}
    for c in ROUTES["cables"]:
        if c["id"] not in on_edge:
            p0 = c["points"][0]
            key = "TENT" if c["side"] == "tent" else \
                ("ROOF" if p0[2] > P.ROOF_Z - 100 else ("BAY" if p0[0] < P.BAY_D + 120 else "CABINET"))
            internal[key].append(c["id"])
    return edges, internal


def sheet_overview():
    s = Sheet(1, "overview", "System overview: locations and cable bundles",
              "Where each part lives and which cables share each run (from the model's runs, E8). Circuits on E2–E7, E9 and E16; routes to scale on E8, E10–E15.", TOTAL)
    edges, internal = bundles()
    N = {   # node: (x, y, w, h, title, lines, cat)
        "ROOF": (430, 112, 300, 86, "Roof platform", ["PV1 190 W + PV2 130 W, PV5 visor 250 W", "ST1 Starlink, U11 visor controller (E9)"], "pv"),
        "TENT": (950, 112, 360, 86, "Tent (detachable)", ["services box: XI1 inlet, Q4 RCBO, XS3 outlet, X5", "PV3 + PV4 2 × 100 W flexible (series)"], "ac"),
        "JUNCTION": (640, 270, 300, 86, "Gap junction box", ["J1–J4 keyed connectors (tent)", "barrier 230 V | 12 V, roof pass-through"], "conn"),
        "ENGINE": (60, 270, 270, 86, "Engine bay", ["BT0 start battery + F8 60 A MIDI", "FBX fuse box: F9 2 A add-a-fuse (IGN)"], "vehicle"),
        "CABIN": (300, 600, 270, 86, "Cabin, under the rear seat", ["X4 SB50 inlet → U12 compute box", "HA PC, router, PoE switch"], "outlet"),
        "GLAND": (1180, 500, 240, 72, "Factory-outlet gland", ["passenger rear tub wall"], "gen"),
        "TRAY": (1180, 640, 240, 72, "Wall drop + tray", ["drop beside the gland; tray under the lid"], "gen"),
        "BAY": (690, 800, 380, 100, "Front bay", ["BT1/BT2, F1/F2, BB1–BB4, QS1, P1, F3", "U1 MultiPlus-II, U2 Orion, U3/U4/U13 MPPTs", "F4–F7 MIDI/MEGA, F17 MRBF (pod), M1 fan", "TH1 + HP1/HP2 heaters, F18, foam (E16)"], "battery"),
        "CABINET": (1250, 800, 370, 100, "Rear control cabinet", ["FB1 fuse block, RCBO enclosure (Q0–Q3)", "U5 Cerbo GX, rear panel: U6, S1–S3,", "XS1 GPO, X1/X2, U7/U8, X6"], "prot"),
        "POD": (1250, 950, 370, 72, "Power slide pod", ["FB2, XS2 GPO, X3 Anderson, X7 12 V"], "outlet"),
    }
    spine_y = 470
    A = ROUTES["anchors"]
    spine_x = {"CH_ENGINE": 195, "CH_CABIN": 435, "CH_GAP": 790, "CH_REAR": 1300}
    # chassis rail as a thick band with the junction nodes on it
    s.raw("zone", f'<rect x="150" y="{spine_y - 9}" width="1200" height="18" rx="9" fill="#dee2e6" stroke="#adb5bd"/>')
    s.text(160, spine_y - 16, "PASSENGER CHASSIS RAIL", size=11, weight="700", fill="#5c636a", layer="zone")
    s.zone(640, 600 + 140, 1000, 300, "Tub", "")
    blocks = {}
    for k, (x, y, w, h, title, lines, cat) in N.items():
        blocks[k] = s.block("", x, y, w, h, title, lines, cat=cat)
    def ctr(k):  # noqa: E306
        b = blocks[k]
        return b.x + b.w / 2, b.y + b.h / 2
    def edge_pts(a, b):  # noqa: E306
        if b in spine_x and a not in spine_x:
            a, b = b, a
        if a in spine_x and b in spine_x:
            return [(spine_x[a], spine_y), (spine_x[b], spine_y)]
        if a in spine_x:
            bx, by = ctr(b)
            if b == "ENGINE":
                return [(spine_x[a], spine_y), (spine_x[a], blocks[b].y + blocks[b].h)]
            if b == "CABIN":
                return [(spine_x[a], spine_y), (spine_x[a], blocks[b].y)]
            if b == "JUNCTION":
                return [(spine_x[a], spine_y), (spine_x[a], blocks[b].y + blocks[b].h)]
            if b == "GLAND":
                return [(spine_x[a], spine_y), (spine_x[a], blocks[b].y)]
        pa, pb = ctr(a), ctr(b)
        if a == "JUNCTION" and b == "ROOF":
            return [(blocks[a].x + 60, blocks[a].y), (blocks[a].x + 60, blocks[b].y + blocks[b].h)]
        if a == "JUNCTION" and b == "TENT":
            return [(blocks[a].x + blocks[a].w, blocks[a].y + 30), (blocks[b].x + 60, blocks[a].y + 30), (blocks[b].x + 60, blocks[b].y + blocks[b].h)]
        if a == "GLAND" and b == "TRAY":
            return [(pa[0], blocks[a].y + blocks[a].h), (pa[0], blocks[b].y)]
        if a == "TRAY" and b == "BAY":
            return [(blocks[a].x, blocks[a].y + 36), (880, blocks[a].y + 36), (880, blocks[b].y)]
        if a == "TRAY" and b == "CABINET":
            return [(1380, blocks[a].y + blocks[a].h), (1380, blocks[b].y)]
        if a == "BAY" and b == "POD":
            return [(1000, blocks[a].y + blocks[a].h), (1000, 986), (blocks[b].x, 986)]
        return [pa, pb]
    tag_pos = {("CH_ENGINE", "CH_CABIN"): (315, 510), ("CH_CABIN", "CH_GAP"): (612, 505), ("CH_GAP", "CH_REAR"): (1045, 520),
               ("ENGINE", "CH_ENGINE"): (100, 410), ("CABIN", "CH_CABIN"): (482, 560), ("CH_GAP", "JUNCTION"): (690, 400),
               ("JUNCTION", "ROOF"): (560, 236), ("JUNCTION", "TENT"): (1000, 255), ("CH_REAR", "GLAND"): (1440, 470),
               ("GLAND", "TRAY"): (1440, 610), ("TRAY", "BAY"): (880, 700), ("TRAY", "CABINET"): (1440, 760),
               ("BAY", "POD"): (1125, 986)}
    for (a, b), ids in sorted(edges.items()):
        a2, b2 = (b, a) if (b, a) in tag_pos else (a, b)
        pts = edge_pts(a2, b2) if (a2, b2) in tag_pos else edge_pts(a, b)
        w = min(10, 3 + len(ids) * 0.6)
        tent = a2 == "JUNCTION" and b2 == "TENT"
        s.raw("wire", f'<polyline points="{" ".join(f"{x:.0f},{y:.0f}" for x, y in pts)}" fill="none" '
                      f'stroke="{"#5f3dc4" if tent else "#495057"}" stroke-width="{w:.1f}" stroke-linecap="round" stroke-linejoin="round"'
                      f'{" stroke-dasharray=\"10 6\"" if tent else ""}/>')
        tp = tag_pos.get((a2, b2))
        if tp:
            lines, cur = [], ""
            for cid in ids:
                if len(cur) + len(cid) + 2 > 28:
                    lines.append(cur)
                    cur = ""
                cur += (", " if cur else "") + cid
            lines.append(cur)
            wbox = max(len(l) for l in lines) * 6.4 + 16
            hbox = 16 * len(lines) + 20
            x0, y0 = tp[0] - wbox / 2, tp[1] - hbox / 2
            o = [f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{wbox:.0f}" height="{hbox:.0f}" rx="5" fill="#fff" stroke="#495057"/>',
                 f'<text x="{x0 + 8:.0f}" y="{y0 + 14:.0f}" font-size="9.5" font-weight="700" fill="#5c636a">{len(ids)} CABLE{"S" if len(ids) > 1 else ""}</text>']
            for i, l in enumerate(lines):
                o.append(f'<text x="{x0 + 8:.0f}" y="{y0 + 30 + 16 * i:.0f}" font-size="10.5" font-family="{MONO}" fill="#212529">{escape(l)}</text>')
            s.raw("tag", "".join(o))
        USED.update(ids)
    for k, ids in internal.items():
        b = blocks[k]
        lines, cur = [], "internal: "
        for cid in ids:
            if len(cur) + len(cid) + 2 > b.w / 6.0:
                lines.append(cur)
                cur = ""
            cur += cid + ", "
        lines.append(cur.rstrip(", "))
        for i, l in enumerate(lines):
            s.text(b.x + (80 if k == "TENT" else 0), b.y + b.h + 16 + 13 * i, l, size=9.5, fill="#495057", family=MONO)
        USED.update(ids)
    s.note(46, 740, 560, ["- Every cable that leaves the tub goes out through the factory 240 V",
                          "  outlet hole (passenger rear wall) and along the passenger chassis rail.",
                          "- Nothing passes through the load lid.",
                          "- The tent harness (dashed) unplugs at the gap junction, so the tent",
                          "  lifts off with its services box and solar.",
                          "- All switching is at the rear panel: battery isolate (S1 → QS1),",
                          "  inverter on/off (S2), visor (S3), GX Touch 50.",
                          "- 230 V never shares a conduit or gland row with 12 V.",
                          "- Line weight ∝ number of cables in the run."], title="Routing rules", size=10.5, lh=15)
    return s


# ======================================================================================= E9
def sheet_visor():
    s = Sheet(9, "visor", "Visor drive: slide, tilt and locking",
              "The windscreen visor panel (PV5) slides out on two rails and tilts to 20°. One button at the rear panel; every motion is interlocked.", TOTAL)
    s.zone(46, 92, 300, 610, "Feeds", "rear cabinet · E3, E6")
    s.zone(380, 92, 560, 610, "Roof platform", "visor controller, front cross-member", bottom=True)
    s.zone(980, 92, 654, 610, "Visor mechanism", "rails, carriages, hinge beam", bottom=True)
    u11 = s.block("U11", 520, 140, 300, 520, "Visor controller",
                  ["IP66 box, platform rear corner", "12 V logic (PLC / µC) + 2 × dual", "H-bridge drivers, current sense",
                   "3 motor channels: M2, M3, M4", "latch driver: Y1 + Y2", "4 limit inputs: B1–B4",
                   "BZ1 buzzer on the lid", "", "motion only while the button", "is held (dead-man), 1 s to start",
                   "timeout 25 s per step → fault", "fuses: M2 15 A, M3/M4 7.5 A each,", "Y 3 A, logic 2 A (v0.13)",
                   "manual override: 8 mm hex on", "M2 shaft end and both tilt drives"],
                  cat="gen", terms=[("p", "L", 40, "+12V"), ("n", "L", 80, "GND"), ("dep", "L", 160, "DEP"), ("stow", "L", 190, "STOW"),
                                    ("led", "L", 220, "LED"), ("ign", "L", 300, "IGN"),
                                    ("m2p", "R", 40, "M2+"), ("m2n", "R", 64, "M2−"), ("m3p", "R", 130, "M3+"), ("m3n", "R", 154, "M3−"),
                                    ("m4p", "R", 210, "M4+"), ("m4n", "R", 234, "M4−"), ("yp", "R", 300, "Y+"), ("yn", "R", 324, "Y−"),
                                    ("b1", "R", 380, "IN1"), ("b2", "R", 410, "IN2"), ("b3", "R", 440, "IN3"), ("b4", "R", 470, "IN4"),
                                    ("com", "B", 250, "COM")])
    # ---- feeds from the rear cabinet
    for key, kind, txt, sub in (("p", "pos", "VIS+ ← FB1 way 10, ATC 20 A", "sheet E3"), ("n", "neg", "VIS− ← FB1 neg bus", "sheet E3")):
        x, y = u11.t(key)
        s.wire([(330, y), (x, y)], kind, "10")
        s.offsheet(330, y, "l", txt, sub)
    s.tag(430, 101 + 59, T("VIS"))
    for key, kind, txt in (("dep", "ctrl", "DEP ← S3"), ("stow", "ctrl", "STOW ← S3"), ("led", "sig", "LED → S3 (COM = 4th core)")):
        x, y = u11.t(key)
        s.wire([(330, y), (x, y)], kind, "0.75")
        s.offsheet(330, y, "l", txt)
    s.text(84, 395, "S3 at the rear panel, sheet E6", size=10, italic=True, fill="#495057")
    s.tag(430, 390, T("VSW"))
    x, y = u11.t("ign")
    s.wire([(330, y), (x, y)], "sig", "0.75")
    s.offsheet(330, y, "l", "VIG ← Orion H (ignition)", "sheet E6")
    s.tag(430, 470, T("VIG"))
    s.note(60, 520, 272, ["S3 switches DEP / STOW to ground;", "U11 pulls the inputs up.", "LED: flashing = moving,",
                          "solid = not stowed, off = locked.", "IGN high = engine on."], title="Inputs", size=10, lh=14)
    # ---- motors, latches, limit switches
    def drive(ref, y, title, lines, kp, kn, size, tag):
        b = s.block(ref, 1120, y, 330, 76, title, lines, cat="gen", terms=[("p", "L", 26, "+"), ("n", "L", 50, "−")])
        for k, kind in ((kp, "pos"), (kn, "neg")):
            a = u11.t(k)
            yy = b.t("p" if kind == "pos" else "n")[1]
            s.wire([a, (960, a[1]), (960, yy), (1120, yy)], kind, size)
        s.tag(1040, y + 64, tag)
        return b
    drive("M2", 110, "Slide gearmotor", ["12 V worm gearmotor, self-locking", "cross shaft → 2 × HTD belts"], "m2p", "m2n", "2.5", "local · 2.5 mm²")
    drive("M3", 216, "Tilt drive, driver side", ["12 V worm rotary actuator", "at the hinge beam end"], "m3p", "m3n", "1.5", "1.5 mm² in chain")
    drive("M4", 322, "Tilt drive, passenger side", ["12 V worm rotary actuator", "runs in step with M3"], "m4p", "m4n", "1.5", "1.5 mm² in chain")
    y1 = s.block("Y1/Y2", 1120, 418, 330, 76, "Front latches (×2, parallel)", ["spring-locked, 12 V to release", "power lost = locked"],
                 cat="prot", terms=[("p", "L", 26, "+"), ("n", "L", 50, "−")])
    for k, t_, kind in (("yp", "p", "pos"), ("yn", "n", "neg")):
        a, b = u11.t(k), y1.t(t_)
        s.wire([a, (940 + (t_ == "n") * 6, a[1]), (940 + (t_ == "n") * 6, b[1]), b], kind, "1")
    lim = (("b1", "B1", "carriages home (stowed)"), ("b2", "B2", "carriages out (deployed)"),
           ("b3", "B3", "tilt at 0° (flat)"), ("b4", "B4", "tilt at 21° (stop at 22°)"))
    for i, (k, ref, txt) in enumerate(lim):
        yb = 520 + i * 36
        b = s.block(ref, 1120, yb, 330, 28, f"limit · {txt}", cat="vehicle", terms=[("i", "L", 14, ""), ("c", "R", 14, "")])
        a = u11.t(k)
        s.wire([a, (900 + i * 12, a[1]), (900 + i * 12, yb + 14), b.t("i")], "sig", "0.75")
        x, y = b.t("c")
        s.wire([(x, y), (1490, y)], "sig", "0.75")
    s.wire([(1490, 534), (1490, 680), (770, 680), u11.t("com")], "sig", "0.75")
    s.text(1500, 610, "COM", size=10, family=MONO, fill="#0b7285")
    s.text(1132, 513, "IP67 roller-lever switches, NO; B4 is set 1° before the hard stop", size=9.5, italic=True, fill="#495057")
    # ---- panel PV (energy chain to the roof branch)
    s.zone(46, 724, 400, 200, "Visor panel", "moves with the carriages", bottom=True)
    pv5 = _panel(s, "PV5", 80, 760, "250 W visor", "semi-flex on honeycomb", w=170)
    x, y = pv5.t("p")
    s.wire([(x, y), (x, 744), (330, 744), (330, 800), (520, 800)], "pvp", "4")
    x, y = pv5.t("n")
    s.wire([(x, y), (x, 868), (330, 868), (330, 812), (520, 812)], "pvn", "4")
    s.offsheet(520, 806, "r", "PVV → MC4 at U11 → PVS → QP3 → U13", "MPPT 100/20 · sheet E4")
    s.tag(400, 846, T("PVV"))
    s.text(530, 840, "high-flex, runs in an igus chain beside the left rail", size=9.5, italic=True, fill="#495057")
    # ---- sequence
    rows = [("1", "check IGN off, B1 + B3 closed", "allowed any time (IGN on too)"),
            ("2", "Y1/Y2 on, M2 starts; Y1/Y2 off once B1 opens", "M3 + M4 tilt down until B3"),
            ("3", "M2 extends until B2", "M2 retracts to B1; pins spring into ramped strikers"),
            ("4", "M3 + M4 tilt up to 20°, B4 = limit", "latches need no power to lock"),
            ("5", "worms hold the panel, nothing powered", "LED off = locked for travel")]
    s.table(470, 880, ["Step", "Deploy (hold DEP)", "Stow (hold STOW)"], rows, [40, 260, 260], title="Sequence")
    s.note(1090, 724, 544, ["- No deploy with the ignition on. Engine on while not stowed →",
                            "  BZ1 sounds, LED flashes; nothing moves without the button.",
                            "- M2 runs only with B3 closed: the panel slides flat, then tilts.",
                            "- Over-current on any channel → stop and back off 2 mm (pinch).",
                            "- Mechanical stop at 22° keeps ≥ 87 mm to the glass even if",
                            "  B4 fails; worm drives cannot be back-driven by wind or load.",
                            "- Latches fail locked. Stow when gusts exceed ~40 km/h.",
                            "- Y1/Y2 are short-duty (≈5 s): energised < 3 s per deploy.",
                            "- U11 draws < 20 mA idle; isolate with FB1 way 10."],
           title="Interlocks and safety", size=10.5, lh=15)
    return s


# ======================================================================================= E16
def sheet_heat():
    s = Sheet(16, "heating", "Cold-weather heating: battery bank and water can",
              "Snow camping (−5 to −15 °C nights): keep the LiFePO₄ bank above 0 °C so it may charge, stop every charger below +3 °C, "
              "and keep the 30 L can from freezing.", TOTAL)
    # ---------------- battery heater (front bay)
    s.zone(46, 92, 800, 480, "Front bay: battery heater", "foam on 5 faces; 2 × 50 W pads between the batteries")
    s.bus("BB3", 90, 160, 330, 160, "pos", "System + busbar", sub="after QS1 (E2)")
    s.bus("BB4", 90, 520, 830, 520, "neg", "System − busbar", below=True)
    th = s.block("TH1", 330, 225, 220, 150, "Battery heater control",
                 ["12 V digital thermostat", "+ 30 A relay, IP65 box", "ON < +3 °C · OFF > +8 °C", "behind the batteries"],
                 cat="prot", terms=[("p", "L", 35, "+12"), ("n", "L", 115, "0 V"), ("o", "R", 35, "OUT"), ("r", "R", 115, "0 V"),
                                    ("s", "B", 110, "PROBE")])
    s.wire([(150, 160), (150, 260), th.t("p")], "pos", "2.5", tag=T("HTR"), tag_at=(245, 260))
    s.fuse(150, 210, "v", "F18", "10 A", side=1)
    s.wire([th.t("n"), (300, 340), (300, 520)], "neg", "2.5")
    pads = []
    for k, (ref, yy, txt) in enumerate((("HP1", 170, "battery 1 inner face"), ("HP2", 290, "battery 2 inner face"))):
        b = s.block(ref, 690, yy, 120, 64, "Pad 50 W", ["silicone, 175 × 215", txt], cat="gen",
                    terms=[("p", "L", 30, ""), ("n", "R", 30, "")])
        pads.append(b)
        y = yy + 30
        s.wire([(590, 260), (590, y), b.t("p")], "pos", "1.5")
        s.switch(645, y, "h", f"CO{k + 1}", "50 °C NC")
        s.wire([b.t("n"), (826, y)], "neg", "1.5")
    s.wire([th.t("o"), (590, 260)], "pos", "1.5")
    s.dot(590, 260)
    s.dot(826, 320, "neg")
    s.wire([(826, 200), (826, 430), (570, 430), (570, 340), th.t("r")], "neg", "1.5")
    s.tag(700, 430, T("HTP"))
    bt2 = s.block("BT2", 380, 450, 210, 46, "Battery 2 (outer)", [], cat="battery", terms=[("t", "T", 60, "")])
    s.text(386, 488, "NTC probe on the lid face, mid-height", size=10)
    s.wire([th.t("s"), bt2.t("t")], "sig", "0.75", tag=T("HTS", "probe lead"), tag_at=(500, 412))
    s.text(60, 404, "Feed after QS1: opening QS1 for", size=10, fill="#495057")
    s.text(60, 418, "storage also switches the heater off.", size=10, fill="#495057")
    # ---------------- water can heater (tent services box -> lid storage)
    s.zone(880, 92, 390, 480, "Tent services box", "stays with the tent · 12 V from J3 (T1D, E7)", bottom=True)
    s.zone(1300, 92, 334, 480, "Load lid, under the tent", "vehicle side", bottom=True)
    x5 = s.block("X5", 900, 120, 130, 60, "SB50 12 V", ["from J3 / T1D"], cat="outlet", terms=[("p", "B", 40, "+"), ("n", "B", 110, "−")])
    t2 = s.block("TH2", 1040, 230, 200, 150, "Water thermostat",
                 ["12 V thermostat + relay", "ON < +3 °C · OFF > +6 °C", "probe on the can,", "under the jacket"],
                 cat="prot", terms=[("p", "L", 30, "+12"), ("n", "L", 110, "0 V"), ("o", "R", 60, "OUT"), ("r", "R", 80, ""),
                                    ("s", "B", 100, "PROBE")])
    s.wire([x5.t("p"), (940, 260), t2.t("p")], "pos", "1.5")
    s.fuse(940, 222, "v", "F19", "5 A", side=1)
    s.wire([x5.t("n"), (1010, 340), t2.t("n")], "neg", "1.5")
    hp3 = s.block("HP3", 1380, 260, 230, 100, "Water pad 50 W",
                  ["silicone, 160 × 735", "on 3 mm foam between the", "cross-bars, under the can"], cat="gen",
                  terms=[("p", "L", 30, ""), ("n", "L", 50, "")])
    s.wire([t2.t("o"), hp3.t("p")], "pos", "1.5")
    s.wire([t2.t("r"), hp3.t("n")], "neg", "1.5", tag=T("WHT"), tag_at=(1312, 384))
    s.switch(1335, 290, "h", "CO3", "45 °C NC")
    s.conn(1285, 300, "h", "XW", "DT 4-pin", side=-1)
    can = s.block("CAN", 1380, 420, 230, 70, "Water can 30 L", ["jacket: 30 mm top, 18–20 mm sides", "and end; cap end open"],
                  cat="gen", terms=[("t", "L", 30, "")])
    s.wire([t2.t("s"), (1140, 450), can.t("t")], "sig", "0.75")
    s.conn(1285, 450, "h", "", "", side=-1)
    s.text(1150, 470, "probe lead (supplied)", size=10, fill="#495057")
    # ---------------- charge protection (temperature sensing to every charger)
    s.zone(46, 600, 1588, 200, "Charge protection: no charging below +3 °C", "backstop if a heater fails or the bank is cold at start-up",
           bottom=True)
    bt1 = s.block("BT1", 80, 640, 170, 80, "Battery 1", ["+ post: ring lug with", "the temperature sensor"], cat="battery",
                  terms=[("p", "R", 45, "")])
    p1 = s.block("P1", 430, 640, 210, 80, "SmartShunt 500 A", ["V+ (red) · AUX (black)", "Aux mode: temperature"], cat="victron",
                 terms=[("v", "L", 45, ""), ("d", "R", 45, "")])
    s.wire([bt1.t("p"), p1.t("v")], "sig", "0.75", tag=T("TS1", "temp sensor"), tag_at=(362, 685))
    s.fuse(275, 685, "h", "F11", "in lead", side=-1)
    u5 = s.block("U5", 760, 640, 230, 80, "Cerbo GX (DVCC)", ["shared temperature sense: ON", "source: SmartShunt (P1)"], cat="victron",
                 terms=[("i", "L", 45, ""), ("o", "R", 45, "")])
    s.wire([p1.t("d"), u5.t("i")], "data", tag=T("D2", "VE.Direct"), tag_at=(700, 685))
    ch = s.block("U1–U4, U13", 1080, 625, 520, 110, "All chargers",
                 ["MultiPlus-II · Orion XS · MPPT 100/30 · MPPT 75/15 · MPPT 100/20",
                  "low-temperature charge cut-off: +3 °C (Victron default 5 °C)",
                  "each must show the shared battery temperature in VictronConnect;",
                  "if one doesn't, set its own cut-off and test it (see notes)"], cat="victron", terms=[("i", "L", 60, "")])
    s.wire([u5.t("o"), ch.t("i")], "data")
    s.text(994, 678, "VE.Bus / VE.Direct", size=10, fill="#6f42c1")
    # ---------------- notes
    y0 = 826
    s.note(46, y0, 392, ["- TH1: ON below +3 °C, OFF above +8 °C (probe on BT2,",
                         "  the outer, colder battery).",
                         "- TH2: ON below +3 °C, OFF above +6 °C.",
                         "- Victron: DVCC on, shared temperature sense from",
                         "  P1, every charger's low-temp cut-off +3 °C.",
                         "- Ask iTechworld whether the BMS blocks charging",
                         "  below 0 °C; the build doesn't rely on it."], title="Settings")
    s.note(452, y0, 392, ["- Bank (insulated, 4 W/K): holding +3 °C uses",
                          "  ~23 Ah on a −5 °C night, ~43–60 Ah at −10 to −15.",
                          "- Water can (jacketed, ~2.5 W/K): ~5 Ah at −5 °C,",
                          "  ~15–20 Ah on a hard night.",
                          "- 2 × 50 W warms a cold bank −10 → +5 °C in ~3–4 h.",
                          "- Daily winter use is ~210 Ah of 800 Ah: plan",
                          "  driving or shore power every 2–3 days."], title="Energy per night [est]")
    s.note(858, y0, 380, ["- Each pad has a normally-closed cut-out bonded",
                          "  to it, in series: a stuck relay can't overheat",
                          "  a battery case (50 °C) or the can (45 °C).",
                          "- Pads only on the batteries' sides, between the",
                          "  cage straps; never under a battery.",
                          "- 0.13 W/cm² on the case: confirm with iTechworld",
                          "  that the case is fine at 50 °C locally."], title="Safety")
    s.note(1252, y0, 382, ["1. Chill the TS1 lug (ice pack in a bag) below",
                           "   +3 °C: every charger must stop or show 'low",
                           "   temperature' (forum reports are mixed).",
                           "2. Chill each probe: the relay must click on;",
                           "   each pad draws ~4.2 A (clamp meter).",
                           "3. Warm each pad's cut-out with a heat gun:",
                           "   the pad must switch off."], title="Test once, before winter")
    USED.update(["TS1", "HTR", "HTP", "HTS", "WHT", "D2"])
    return s


_RS = routes.build(dict(ROUTES=ROUTES, USED=USED, TOTAL=TOTAL))
SHEETS = [sheet_overview, sheet_dc_main, sheet_dc_dist, sheet_charging, sheet_ac, sheet_control, sheet_tent, _RS[0], sheet_visor] + _RS[1:] \
    + [sheet_heat]


# ======================================================================================= schedules
PROTECTION = [  # ref, device, rating, location, protects
    ("F1", "MRBF terminal fuse (Blue Sea 5191)", "300 A", "Battery 1 + stud", "B1P"),
    ("F2", "MRBF terminal fuse (Blue Sea 5191)", "300 A", "Battery 2 + stud", "B2P"),
    ("F3", "Class-T fuse + holder (Blue Sea 5502)", "400 A", "BB3 system + bus", "CT1, INVP (MultiPlus DC)"),
    ("F4", "MIDI fuse", "70 A", "BB3 stud", "ORO (Orion XS output)"),
    ("F5", "MIDI fuse", "40 A", "BB3 stud", "MPR (MPPT 100/30 output)"),
    ("F6", "MIDI fuse", "40 A", "BB3 stud", "MPT (MPPT 75/15) and MPV (MPPT 100/20) outputs, 6 mm² each"),
    ("F7", "MEGA fuse", "100 A", "BB3 stud", "DCF (feed to FB1)"),
    ("F8", "MIDI fuse + holder", "60 A", "Start battery +, engine bay", "ALT"),
    ("F9", "Add-a-fuse, ignition circuit", "2 A", "Engine-bay fuse box", "IGN"),
    ("F10", "Inline ATC holder", "2 A", "BB1 bank + bus", "RBF, SW1 (ML-RBS control)"),
    ("F11", "Fuse in the Victron temperature sensor lead (supplied)", "–", "Battery 1 + post (lug)", "TS1 (P1 V+ and AUX)"),
    ("F12", "Inline ATC holder", "5 A", "BB3 stud", "FAN"),
    ("FB1 1–10", "ATC blade fuses in FB1 (Blue Sea 5026)", "see E3", "Rear control cabinet", "DO1A–D, DO3–DO5, CGX, VIS (not DO2)"),
    ("F13", "ATC in FB2", "15 A", "Power slide pod", "pod 12 V socket X7"),
    ("F14", "ATC in FB2", "20 A", "Power slide pod", "pod Anderson X3"),
    ("F17", "MRBF terminal fuse (Blue Sea 5191)", "30 A", "BB3 system + busbar, spare stud", "DO2 (power-slide pod)"),
    ("F18", "Inline ATC holder", "10 A", "BB3 stud 4, front bay", "HTR, HTP (battery heater, 2 × 50 W)"),
    ("F19", "Inline ATC holder", "5 A", "Tent services box (12 V from X5)", "WHT (water-can pad, 50 W)"),
    ("CO1–CO3", "Thermal cut-out, normally closed, bonded to each pad", "50 / 50 / 45 °C", "On HP1, HP2, HP3", "pad over-temperature"),
    ("FB3", "ATC fuse block behind a Smart BatteryProtect", "per device", "Compute box, under the rear seat", "HA PC, router, PoE switch, fan"),
    ("Q0", "Main switch, 2-pole isolator (AS/NZS 3001.2)", "32 A", "RCBO enclosure, rear cabinet", "inverter supply AC1"),
    ("Q1–Q3", "RCBO 1P+N, 30 mA", "10 A", "RCBO enclosure, rear cabinet", "AC2, AC3, AC4"),
    ("Q4", "RCBO 2-pole, 30 mA", "16 A", "Tent services box", "shore inlet → AC-in (T1A, AC5)"),
    ("QS1", "ML-RBS remote battery switch (Blue Sea 7713)", "500 A", "Front bay", "isolation, bank + → system +"),
    ("QP1–QP3", "2-pole DC PV isolator", "32 A", "Front bay, beside the MPPTs", "PVR / PVT / PVS (servicing)"),
    ("U11 F1–F4", "Fuses inside the visor controller", "15 / 7.5 / 7.5 / 3 A", "U11 box, roof", "M2, M3, M4, Y1/Y2 (+ 2 A logic)"),
]

COMPONENTS = [  # ref, item, model, location, sheets
    ("BT1, BT2", "House batteries 12.8 V 400 Ah", "iTechworld iTech400X Pro", "Front bay, on end", "E2"),
    ("BB1–BB4", "Busbars (bank ±, system ±)", "Blue Sea PowerBar 600 A", "Front bay distribution column", "E2"),
    ("QS1", "Remote battery switch", "Blue Sea ML-RBS 7713 (12 V)", "Front bay", "E2, E6"),
    ("P1", "Battery monitor", "Victron SmartShunt 500 A", "Front bay", "E2, E6"),
    ("U1", "Inverter/charger", "Victron MultiPlus-II 12/3000/120-32 230 V", "Front bay, lying flat", "E2, E5, E6"),
    ("U2", "DC-DC charger", "Victron Orion XS 12/12-50A", "Charging board", "E4, E6"),
    ("U3", "Solar charger, roof", "Victron SmartSolar MPPT 100/30", "Charging board", "E4, E6"),
    ("U13", "Solar charger, visor", "Victron SmartSolar MPPT 100/20", "Front bay, passenger face of the distribution board", "E4, E6"),
    ("U4", "Solar charger, tent", "Victron SmartSolar MPPT 75/15", "Charging board", "E4, E6"),
    ("M1", "Inverter fan", "92 mm 12 V thermostatic", "Above the inverter", "E2"),
    ("TH1", "Battery heater control", "12 V digital thermostat (NTC probe) + 30 A relay, IP65 box", "Behind the batteries, on the rear foam", "E16"),
    ("HP1, HP2", "Battery heater pads 50 W", "12 V silicone pad 175 × 215, self-adhesive, CO1/CO2 50 °C", "Facing sides of BT1 / BT2", "E16"),
    ("TT1", "Battery temperature sensor", "Victron temperature sensor (BMV / SmartShunt), lug on BT1 +", "Battery 1 + post", "E2, E16"),
    ("TH2, HP3", "Water-can thermostat + pad 50 W", "12 V thermostat + relay; silicone pad 160 × 735, CO3 45 °C", "Services box / under the can", "E16"),
    ("XW", "Water-pad plug", "Deutsch DT 4-pin (pad + probe)", "Beside the tent services box", "E16"),
    ("FB1", "Fuse block 12-way + neg bus", "Blue Sea 5026", "Rear control cabinet", "E3"),
    ("FB2", "Local fuse holder + studs", "2-way ATC", "Power slide pod", "E3"),
    ("U12, FB3", "Compute box: BatteryProtect + 6-way ATC block", "Victron SBP-65, Blue Sea 5025-class", "Under the rear seat", "E3"),
    ("U5", "GX device", "Victron Cerbo GX MK2", "Rear control cabinet", "E3, E6"),
    ("U6", "Display", "Victron GX Touch 50", "Rear panel", "E6"),
    ("S1", "Battery isolate switch", "Blue Sea 2155 Contura SPDT with LED", "Rear panel", "E6"),
    ("S2", "Inverter on/off switch", "SPST rocker", "Rear panel", "E6"),
    ("S3", "Visor deploy / stow button", "momentary ON-OFF-ON rocker with LED", "Rear panel", "E6, E9"),
    ("RCBO", "RCBO enclosure, Q0–Q3", "IP66 DIN enclosure, 2-pole main switch + 3 × RCBO 10 A 30 mA", "Rear control cabinet", "E5"),
    ("XS1", "Rear double GPO", "IP66 10 A (Clipsal 56 series)", "Rear panel", "E5"),
    ("XS2", "Pod GPO", "Flush 10 A, faces up", "Power slide pod", "E5"),
    ("XS3", "Tent heater outlet", "Clipsal 56SO310A IP66 10 A", "Tent services box", "E5, E7"),
    ("XI1, Q4", "Shore inlet + RCBO", "Clipsal 56AI315 15 A + 2-pole RCBO 16 A 30 mA", "Tent services box", "E5, E7"),
    ("X1–X5", "Anderson SB50 sockets", "Anderson SB50 red + flush housing", "Rear panel ×2, pod, compute-box inlet, tent box", "E3"),
    ("X6, X7", "12 V sockets", "Narva / Blue Sea", "Rear panel, pod", "E3"),
    ("U7, U8", "Dual USB-C sockets, 100 W PD + 20 W each", "Treklo dual USB-C 120 W, 12–24 V", "Rear panel ×2", "E3"),
    ("JB", "Gap junction box", "IP66 polycarbonate with an internal barrier (230 V | 12 V)", "Cab–tub gap, passenger corner", "E7, E13"),
    ("J1", "230 V out connector", "IP66 10 A socket (vehicle) / plug (tent)", "Gap junction box", "E5, E7"),
    ("J2", "230 V in connector", "IP66 15 A inlet (vehicle) / extension socket (tent)", "Gap junction box", "E5, E7"),
    ("J3", "12 V tent connector", "Anderson SB50 red", "Gap junction box", "E3, E7"),
    ("J4", "Tent PV connector", "Anderson SB50 grey", "Gap junction box", "E4, E7"),
    ("PV1, PV2", "Roof panels 190 W + 130 W", "Victron BlueSolar (parallel)", "Roof platform", "E4"),
    ("PV5", "Visor panel ~250 W", "semi-flexible on honeycomb backing (own MPPT, U13)", "Slide-out visor", "E4, E9"),
    ("U11", "Visor controller", "12 V PLC / µC + 2 × dual H-bridge, per-channel fuses, IP66 box", "Under the platform, rear passenger corner", "E3, E9"),
    ("M2", "Slide gearmotor", "12 V worm gearmotor, self-locking", "Roof platform, rear cross-member", "E9"),
    ("M3, M4", "Tilt drives", "12 V worm rotary actuators", "Hinge beam ends", "E9"),
    ("Y1, Y2", "Front latches", "12 V solenoid, spring-locked (fail-locked)", "Platform front", "E9"),
    ("B1–B4", "Limit switches", "IP67 roller-lever, NO", "Rails and hinge beam", "E9"),
    ("BZ1", "Not-stowed buzzer", "12 V piezo", "Visor controller lid", "E9"),
    ("PV3, PV4", "Tent panels 2 × 100 W", "Sunman eArc flexible (series)", "Tent roof", "E4"),
    ("ST1", "Satellite internet", "Starlink Mini", "Roof platform, inside the frame", "E3, E6"),
    ("BT0, G1, FBX", "Vehicle start battery, alternator, fuse box", "factory", "Engine bay", "E4"),
]


def html_page(built):
    sheets = []
    for sh, path in built:
        svg = path.read_text()
        sheets.append((sh, svg))
    cab_rows = "".join(
        f"<tr><td class=mono>{escape(r['id'])}</td><td>{escape(r['circuit'])}</td><td>{escape(r['from'])}</td><td>{escape(r['to'])}</td>"
        f"<td>{escape(r['cable'].replace('mm2', 'mm²'))}</td><td>{escape(r['protection'])}</td><td class=num>{escape(r['length_m (model +10%)'])}</td>"
        f"<td class=mono>{escape(r.get('route (runs)', '') or 'local')}</td><td>{escape(r['harness'])}</td></tr>" for r in SCHED.values())
    rsched = list(csv.DictReader(open(ROOT / f"bom/route-schedule-{V}.csv")))
    buy_rows = "".join(f"<tr><td>{escape(r['cable'].replace('mm2', 'mm²'))}</td><td class=num>{escape(r['total_m (model)'])}</td>"
                       f"<td class=num>{escape(r['buy_m (+15%, rounded up)'])}</td></tr>"
                       for r in csv.DictReader(open(ROOT / f"bom/cable-totals-{V}.csv")))
    run_rows = "".join(
        f"<tr><td class=mono>{escape(r['run'])}</td><td>{escape(r['name'])}</td><td class=num>{escape(r['length_m'])}</td>"
        f"<td class=num>{escape(r['cables'])}</td><td>{escape(r['containment'])}</td><td class=num>{escape(r['fill'])}</td>"
        f"<td>{escape(r['voltage'])}</td><td>{escape(r['fixing'])}</td><td class=mono>{escape(r['cable ids'])}</td></tr>" for r in rsched)
    prot_rows = "".join(f"<tr><td class=mono>{escape(a)}</td><td>{escape(b)}</td><td class=num>{escape(c)}</td><td>{escape(d)}</td><td>{escape(e)}</td></tr>"
                        for a, b, c, d, e in PROTECTION)
    comp_rows = "".join(f"<tr><td class=mono>{escape(a)}</td><td>{escape(b)}</td><td>{escape(c)}</td><td>{escape(d)}</td><td class=mono>{escape(e)}</td></tr>"
                        for a, b, c, d, e in COMPONENTS)
    fb_rows = "".join(f"<tr><td class=num>{w}</td><td>{escape(c)}</td><td class=num>{escape(f)}</td><td class=mono>{escape(cid or '–')}</td></tr>"
                      for w, c, f, cid in FB1_WAYS)
    nav = "".join(f'<a href="#e{sh.num}"><span class=mono>E{sh.num}</span> {escape(sh.title.split(":")[0])}</a>' for sh, _ in sheets)
    secs = "".join(
        f'<section class="sheet" id="e{sh.num}"><header><span class="code mono">E{sh.num}</span><div><h2>{escape(sh.title)}</h2>'
        f'<p>{escape(sh.subtitle)}</p></div></header><div class="paper">{svg}</div></section>' for sh, svg in sheets)
    total_m = sum(float(r["length_m (model +10%)"]) for r in SCHED.values())
    body = f"""<title>Tasman Fit-out Wiring</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap">
<style>
/* Layout: a drawing-set binder. Sticky sheet index on top, each sheet on white "paper", schedules as tables at the end. */
:root {{
  --bg: #e9edf1; --surface: #ffffff; --ink: #1d232a; --muted: #5a6470; --line: #c9d1d9;
  --accent: #1f5fa8; --warn: #b42318; --chip: #f1f4f7;
  --font-display: 'IBM Plex Sans Condensed', 'Arial Narrow', 'Segoe UI', sans-serif;
  --font-body: 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif;
  --font-mono: 'IBM Plex Mono', Consolas, 'Courier New', monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #12161b; --surface: #1b2129; --ink: #e6ebf0; --muted: #9aa6b2; --line: #2e3842; --accent: #7fb0ec; --warn: #ff8a7a; --chip: #232b34; color-scheme: dark }} }}
:root[data-theme="dark"] {{ --bg: #12161b; --surface: #1b2129; --ink: #e6ebf0; --muted: #9aa6b2; --line: #2e3842; --accent: #7fb0ec; --warn: #ff8a7a; --chip: #232b34; color-scheme: dark }}
body {{ background: var(--bg); color: var(--ink); font-family: var(--font-body); font-size: 15px; line-height: 1.5; }}
.wrap {{ max-width: 1320px; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 28px 64px; }}
.mono {{ font-family: var(--font-mono); }}
h1, h2, h3 {{ font-family: var(--font-display); text-wrap: balance; margin: 0; }}
h1 {{ font-size: clamp(28px, 4vw, 40px); letter-spacing: 0.01em; }}
h2 {{ font-size: 21px; }}
h3 {{ font-size: 17px; margin-bottom: 8px; }}
.lede {{ color: var(--muted); max-width: 70ch; margin: 8px 0 0; }}
.meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }}
.chip {{ background: var(--chip); border: 1px solid var(--line); border-radius: 999px; padding: 2px 10px; font-size: 12.5px; font-variant-numeric: tabular-nums; }}
.warn {{ border-left: 4px solid var(--warn); background: var(--surface); padding: 10px 14px; margin-top: 18px; border-radius: 4px; max-width: 80ch; }}
.warn strong {{ color: var(--warn); }}
nav.index {{ position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5; background: var(--bg); border-bottom: 1px solid var(--line);
  margin-top: 22px; padding-block: 10px; display: flex; gap: 6px; overflow-x: auto; scrollbar-width: thin; }}
body::before {{ content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 10; background: var(--bg); }}
nav.index a {{ flex: none; text-decoration: none; color: var(--ink); background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: 5px 10px; font-size: 13px; white-space: nowrap; }}
nav.index a:hover, nav.index a:focus-visible {{ border-color: var(--accent); outline: none; }}
nav.index a .mono {{ color: var(--accent); font-weight: 600; margin-right: 4px; }}
section {{ margin-top: 36px; scroll-margin-top: 70px; }}
.sheet header {{ display: flex; gap: 14px; align-items: flex-start; margin-bottom: 12px; }}
.sheet header p {{ margin: 4px 0 0; color: var(--muted); max-width: 80ch; }}
.code {{ flex: none; background: var(--accent); color: var(--surface); border-radius: 6px; padding: 4px 9px; font-weight: 600; font-size: 14px; }}
.paper {{ background: #ffffff; border: 1px solid var(--line); border-radius: 6px; overflow-x: auto; box-shadow: 0 1px 2px rgba(0,0,0,.06); }}
.paper svg {{ display: block; width: 100%; height: auto; min-width: 1100px; }}
.tbl {{ overflow-x: auto; background: var(--surface); border: 1px solid var(--line); border-radius: 6px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13.5px; }}
th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }}
th {{ font-family: var(--font-display); font-size: 13px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--muted); background: var(--chip); position: sticky; top: 0; }}
td.num {{ font-variant-numeric: tabular-nums; text-align: right; white-space: nowrap; }}
td.mono {{ white-space: nowrap; font-size: 12.5px; }}
.cols {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 420px), 1fr)); gap: 20px; }}
.cols > * {{ min-width: 0; }}
ul.notes {{ margin: 0; padding-left: 20px; }}
ul.notes li {{ margin-bottom: 6px; }}
footer {{ margin-top: 40px; color: var(--muted); font-size: 13px; }}
@media print {{
  @page {{ size: A3 landscape; margin: 0; }}
  body {{ background: #fff; }}
  nav.index, .warn, .intro {{ display: none; }}
  .wrap {{ max-width: none; padding: 0; }}
  .sheet {{ margin: 0; break-after: page; }}
  .sheet header {{ display: none; }}
  .paper {{ border: 0; border-radius: 0; box-shadow: none; overflow: visible; }}
  .paper svg {{ width: 420mm; height: 297mm; min-width: 0; }}
  section.sched {{ break-before: page; padding: 14mm; }}
}}
</style>
<div class="wrap">
  <div class="intro">
    <p class="mono" style="color:var(--accent);margin:0 0 6px;font-weight:600">KIA TASMAN X-PRO · ELECTRICAL · {escape(V)}</p>
    <h1>Fit-out wiring diagram</h1>
    <p class="lede">Sixteen drawing sheets and the full schedules for the 12 V and 230 V systems. E1–E7, E9 and E16 are the circuits: battery bank,
    isolation and protection, DC distribution, charging, the inverter's AC side, control, the detachable tent harnesses, the visor drive
    and the cold-weather heating (battery and water heaters, charge cut-off below +3 °C).
    E8 and E10–E15 are the cable routes, drawn to scale from the routed 3D model: every run (R-code) with its containment and fixing,
    every cable labelled in every zone, and every bundle's cross-section and conduit fill.
    Cable IDs match <span class="mono">bom/cable-schedule-{escape(V)}.csv</span>; runs match <span class="mono">bom/route-schedule-{escape(V)}.csv</span>.</p>
    <div class="meta"><span class="chip">{len(SCHED)} cables</span><span class="chip">{total_m:.1f} m routed</span><span class="chip">{len(rsched)} runs</span><span class="chip">{TOTAL} sheets, A3</span>
      <span class="chip">rev {escape(V)} · {escape(DATE)}</span></div>
    <div class="warn"><strong>230 V:</strong> the inverter output, shore inlet, RCBOs and outlets must be installed and certified by a licensed
    electrician (AS/NZS 3000, AS/NZS 3001.2). These drawings are a design for review, not a certified installation. Check every
    terminal size, torque and setting against the maker's manual.</div>
  </div>
  <nav class="index" aria-label="Sheets">{nav}<a href="#schedules"><span class=mono>S</span> Schedules</a></nav>
  {secs}
  <section class="sched" id="schedules">
    <h2>Schedules</h2>
    <h3 style="margin-top:18px">Cable schedule</h3>
    <p class="lede" style="margin-bottom:10px">Lengths are measured along each cable's routed path in the 3D model, plus 10 % slack and 0.3 m for terminations.</p>
    <div class="tbl"><table><thead><tr><th>ID</th><th>Circuit</th><th>From</th><th>To</th><th>Cable</th><th>Protection</th><th>m</th><th>Route (runs, in order)</th><th>Harness</th></tr></thead>
    <tbody>{cab_rows}</tbody></table></div>
    <h3 style="margin-top:28px">Cable to buy</h3>
    <div class="tbl" style="max-width:760px"><table><thead><tr><th>Cable</th><th>Model m</th><th>Buy m (+15 %)</th></tr></thead><tbody>{buy_rows}</tbody></table></div>
    <h3 style="margin-top:28px">Route schedule</h3>
    <p class="lede" style="margin-bottom:10px">Each physical run: where it goes, how the cables are held, and which cables share it. Fill is the cables' cross-section over the conduit's (≤ 50 % for split conduit that the cables are laid into).</p>
    <div class="tbl"><table><thead><tr><th>Run</th><th>Name</th><th>m</th><th>n</th><th>Containment</th><th>Fill</th><th>V</th><th>Fixing</th><th>Cables</th></tr></thead>
    <tbody>{run_rows}</tbody></table></div>
    <div class="cols" style="margin-top:28px">
      <div><h3>Protection</h3><div class="tbl"><table><thead><tr><th>Ref</th><th>Device</th><th>Rating</th><th>Location</th><th>Protects</th></tr></thead><tbody>{prot_rows}</tbody></table></div></div>
      <div><h3>FB1 fuse block ways</h3><div class="tbl"><table><thead><tr><th>Way</th><th>Circuit</th><th>ATC</th><th>Cable</th></tr></thead><tbody>{fb_rows}</tbody></table></div>
        <h3 style="margin-top:22px">Before power-up</h3>
        <ul class="notes">
          <li>Measure the real cable runs: these lengths come from <span class="mono">[EST]</span> positions in the model.</li>
          <li>Confirm the ML-RBS control-wire colours and switch wiring against the Blue Sea 7713 instructions.</li>
          <li>Set every charger to iTechworld's LiFePO₄ voltages; set the Orion XS input limit to 25–30 A.</li>
          <li>Torque every stud, then re-check after the first corrugated road.</li>
          <li>Electrician: earth continuity, polarity, RCD trip tests on shore power and in inverter mode.</li>
        </ul></div>
    </div>
    <h3 style="margin-top:28px">Component register</h3>
    <div class="tbl"><table><thead><tr><th>Ref</th><th>Item</th><th>Model</th><th>Location</th><th>Sheets</th></tr></thead><tbody>{comp_rows}</tbody></table></div>
  </section>
  <footer>Generated by <span class="mono">tools/wiring/diagram.py</span> from <span class="mono">cad/fitout/wiring.py</span> and the routed 3D model.
  Rebuild: <span class="mono">cd cad &amp;&amp; ../.venv/bin/python build.py &amp;&amp; cd .. &amp;&amp; python3 tools/wiring/diagram.py</span>.</footer>
</div>
"""
    out = ROOT / "docs/wiring"
    (out / "artifact.html").write_text(body)
    (out / f"wiring-diagram-{V}.html").write_text('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
                                                   '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
                                                   '<style>[hidden]{display:none!important} body{margin:0}</style>\n'
                                                   + body + "\n</html>\n")
    print("wrote", (out / f"wiring-diagram-{V}.html").relative_to(ROOT), "and docs/wiring/artifact.html")


def main():
    out = ROOT / "docs/wiring/sheets"
    out.mkdir(parents=True, exist_ok=True)
    built = []
    for fn in SHEETS:
        sh = fn()
        p = out / f"E{sh.num}-{sh.key}.svg"
        p.write_text(sh.svg(META))
        built.append((sh, p))
        print("wrote", p.relative_to(ROOT))
    missing = sorted(set(SCHED) - USED)
    if missing:
        sys.exit(f"cables not drawn on any sheet: {missing}")
    html_page(built)
    return built


if __name__ == "__main__":
    main()
