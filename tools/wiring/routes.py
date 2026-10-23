"""
Route sheets for the wiring diagram (v0.13), drawn to scale from the routed 3D model (cad/out/cables.json):

    E8   route map: every run on the whole vehicle (plan + side), run schedule
    E10  front bay (plan + view from the rear)
    E11  tray, wall channel, gland plate and rear cabinet (view outboard + plan)
    E12  under the vehicle: wall cavity, chassis rail, cabin and engine-bay branches (side + plan)
    E13  cab-tub gap, junction box, roof and the tent harnesses (view forward + side)
    E14  power slide: trunk and chain, stowed and extended (plans)
    E15  bundle cross-sections: every run's packing, conduit size and fill

Every cable is drawn along its routed centre line and labelled with its schedule ID; every run carries its R-code.
"""
import math
from html import escape

from svglib import MONO, Sheet

COL = {"w_pos": "#c92a2a", "w_neg": "#212529", "w_ac": "#a0522d", "w_12v": "#e03131", "w_pv": "#e8590c", "w_data": "#6f42c1",
       "w_tent": "#7048e8", "w_pe": "#2b8a3e"}
KIND_OF = {"w_pos": "pos", "w_neg": "neg", "w_ac": "L", "w_12v": "pos", "w_pv": "pvp", "w_data": "data", "w_tent": "ctrl", "w_pe": "PE"}
RUN_COL = {"lv": "#d9480f", "elv": "#343a40", "tent": "#7048e8"}
SKIP_PART = ("screw", "label", "stripe", "lugs_", "_grid", "shutline", "_text", "ply_lines", "bezel", "_ui", "lens", "rocker",
             "_studs", "_pockets", "_bores", "receivers", "_lid", "led", "glass", "_trim", "keeper", "_pull", "_hardware", "gasket",
             "lever", "_caps", "boots", "_tinned", "_metal", "window", "_spring", "_pad", "_fuses", "_cover", "_plugs", "slots",
             "optics", "_knob", "_vedirect", "_brass", "_vbatt", "_buckle", "_display", "_panel_", "strap")
NAMES = {
    "inverter_charger_multiplus2_3000": "U1 MultiPlus-II", "orion_xs_50a": "U2 Orion", "mppt_roof_100_30": "U3",
    "mppt_tent_75_15": "U4", "mppt_visor_100_20": "U13", "dc_fuse_block": "FB1", "cerbo_gx": "U5 Cerbo",
    "pc_rcbo_enclosure": "RCBO Q0–Q3", "busbar_bank_pos": "BB1", "busbar_bank_neg": "BB2", "busbar_sys_pos": "BB3",
    "busbar_sys_neg": "BB4", "battery_1": "BT1", "battery_2": "BT2", "gap_junction_box": "JB", "cabin_compute_box": "U12",
    "start_battery": "BT0", "visor_controller_box": "U11", "starlink_mini": "ST1", "remote_battery_switch_500a": "QS1",
    "smartshunt_500a": "P1", "class_t_400a": "F3", "fuse_holders_midi": "F4–F7", "mrbf_slide_30a": "F17",
    "inverter_fan": "M1", "cable_tray": "tray", "pc_gpo_double": "XS1", "pc_gx_touch_50": "U6", "pc_anderson_1": "X1",
    "pc_anderson_2": "X2", "tent_services_box": "services box", "slide_power_power_pod": "pod", "slide_power_cable_chain": "chain",
    "slide_power_chain_tray": "glide tray", "fridge": "fridge", "roof_solar_190w_jbox": "PV1 jb", "roof_solar_130w_jbox": "PV2 jb",
    "tent_solar_jbox": "PV3/4 jb", "factory_outlet_gland_plate": "gland plate", "dist_board": "board", "charge_board": "charging board",
}


class View:
    """Orthographic view: two world axes (index, sign) mapped to the sheet; world box in signed axis units."""
    n = 0

    def __init__(self, s, x, y, w, h, axes, world, title, depth=None, sc=None):
        View.n += 1
        self.s, self.x, self.y, self.w, self.h = s, x, y, w, h
        self.axes, self.world, self.title, self.depth = axes, world, title, depth
        (u0, u1, v0, v1) = world
        self.sc = sc or min(w / (u1 - u0), h / (v1 - v0))
        self.ox = x + (w - (u1 - u0) * self.sc) / 2 - u0 * self.sc
        self.oy = y + (h - (v1 - v0) * self.sc) / 2 - v0 * self.sc
        self.id = f"cv{View.n}"
        self.labels = []                       # occupied label rectangles
        s.raw("zone", f'<clipPath id="{self.id}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>'
                      f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fbfcfd" stroke="#ced4da" stroke-width="1"/>')
        s.text(x, y - 8, f"{title}  ·  1:{round(4 / self.sc)} on A3", size=11.5, weight="700", fill="#343a40")

    def uv(self, q):
        (ia, sa), (ib, sb) = self.axes
        return sa * q[ia], sb * q[ib]

    def p(self, q):
        u, v = self.uv(q)
        return self.ox + u * self.sc, self.oy + v * self.sc

    def hit3(self, q, pad=0.0):
        u, v = self.uv(q)
        u0, u1, v0, v1 = self.world
        if not (u0 - pad <= u <= u1 + pad and v0 - pad <= v <= v1 + pad):
            return False
        if self.depth:
            i, lo, hi = self.depth
            return lo <= q[i] <= hi
        return True

    def inside(self, X, Y, m=0):
        return self.x + m <= X <= self.x + self.w - m and self.y + m <= Y <= self.y + self.h - m

    def g(self, layer, body):
        self.s.raw(layer, f'<g clip-path="url(#{self.id})">{body}</g>')

    # ---------------------------------------------------------------- context outlines
    def outlines(self, outl, groups=None, names=(), fill="#e9ecef", stroke="#adb5bd", label=True, only=None):
        o, labs = [], []
        for nm, (grp, x0, x1, y0, y1, z0, z1) in outl.items():
            if only is not None and not any(nm.startswith(k) for k in only):
                continue
            if only is None and ((groups and grp not in groups) or any(k in nm for k in SKIP_PART)):
                continue
            corners = [(x0, y0, z0), (x1, y1, z1)]
            if self.depth:
                i, lo, hi = self.depth
                if (x0, y0, z0)[i] > hi or (x1, y1, z1)[i] < lo:
                    continue
            (X0, Y0), (X1, Y1) = self.p(corners[0]), self.p(corners[1])
            a, b = sorted((X0, X1)), sorted((Y0, Y1))
            if a[1] < self.x or a[0] > self.x + self.w or b[1] < self.y or b[0] > self.y + self.h:
                continue
            if a[1] - a[0] < 1.5 and b[1] - b[0] < 1.5:
                continue
            f = fill if grp != "vehicle" else "none"
            o.append(f'<rect x="{a[0]:.1f}" y="{b[0]:.1f}" width="{a[1] - a[0]:.1f}" height="{b[1] - b[0]:.1f}" fill="{f}" '
                     f'stroke="{stroke}" stroke-width="{0.8 if grp != "vehicle" else 1.0}"'
                     f'{" stroke-dasharray=\"5 4\"" if grp == "vehicle" else ""}/>')
            key = next((k for k in NAMES if nm == k), None)
            if label and key and a[1] - a[0] > 18 and b[1] - b[0] > 10:
                labs.append(f'<text x="{(a[0] + a[1]) / 2:.1f}" y="{(b[0] + b[1]) / 2 + 3:.1f}" font-size="9" text-anchor="middle" '
                            f'fill="#868e96" font-weight="600">{escape(NAMES[key])}</text>')
        self.g("zone", "".join(o) + "".join(labs))

    # ---------------------------------------------------------------- cables
    def cables(self, cabs, pts_of=None, width=1.0, keep=None):
        """Draw every cable that enters the view (only the parts where keep(point) holds); returns {cid: longest screen
        polyline} for labelling."""
        vis, o = {}, []
        for c in cabs:
            pts = pts_of(c) if pts_of else c["points"]
            if not pts or not any(self.hit3(q, 40) for q in pts):
                continue
            pieces = _split(pts, keep) if keep else [pts]
            w = max(1.3, min(c["od"] * math.sqrt(c.get("cores", 1)) * self.sc * 0.55 * width, 5.0))
            col = COL.get(c["colour"], "#495057")
            dash = ' stroke-dasharray="6 3"' if c.get("side") == "tent" else ""
            best = None
            for pc in pieces:
                if len(pc) < 2:
                    continue
                sp = [self.p(q) for q in pc]
                o.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in sp)}" fill="none" stroke="#ffffff" '
                         f'stroke-width="{w + 1.6:.1f}" stroke-linejoin="round" opacity="0.9"/>'
                         f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in sp)}" fill="none" stroke="{col}" '
                         f'stroke-width="{w:.1f}" stroke-linejoin="round" stroke-linecap="round"{dash}/>')
                L = sum(math.dist(a, b) for a, b in zip(sp[:-1], sp[1:]))
                if best is None or L > best[0]:
                    best = (L, sp)
            if best:
                vis[c["id"]] = best[1]
        self.g("wire", "".join(o))
        return vis

    def free(self, r):
        x0, y0, x1, y1 = r
        if not (self.inside(x0, y0, 2) and self.inside(x1, y1, 2)):
            return False
        return all(x1 < a or x0 > c or y1 < b or y0 > d for a, b, c, d in self.labels)

    def label_cables(self, vis, prefer_ends=True):
        """One pill per cable on its own line, at the first free spot (ends first, then along its longest segments)."""
        out = []
        order = sorted(vis.items(), key=lambda kv: sum(math.dist(a, b) for a, b in zip(kv[1][:-1], kv[1][1:])))
        for cid, sp in order:
            w, h = len(cid) * 5.7 + 8, 12
            cands = []
            if prefer_ends:
                for q, nxt in ((sp[0], sp[1] if len(sp) > 1 else sp[0]), (sp[-1], sp[-2] if len(sp) > 1 else sp[-1])):
                    if self.inside(*q, 4):
                        d = math.dist(q, nxt) or 1
                        t = min(1.0, 14 / d)
                        cands.append((q[0] + (nxt[0] - q[0]) * t, q[1] + (nxt[1] - q[1]) * t))
            segs = sorted(zip(sp[:-1], sp[1:]), key=lambda ab: -math.dist(*ab))
            for a, b in segs[:8]:
                L = math.dist(a, b)
                if L < 16:
                    continue
                for t in (0.5, 0.3, 0.7, 0.15, 0.85, 0.4, 0.6):
                    cands.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            placed = None
            for X, Y in cands:
                r = (X - w / 2, Y - h / 2, X + w / 2, Y + h / 2)
                if self.free(r):
                    placed = (X, Y)
                    break
            if placed is None:                  # leader to an offset spot
                for X, Y in cands[:6]:
                    for dx, dy in ((0, -22), (0, 22), (34, -18), (-34, -18), (34, 18), (-34, 18), (0, -40), (0, 40)):
                        r = (X + dx - w / 2, Y + dy - h / 2, X + dx + w / 2, Y + dy + h / 2)
                        if self.free(r):
                            placed = (X + dx, Y + dy)
                            out.append(f'<line x1="{X:.1f}" y1="{Y:.1f}" x2="{X + dx:.1f}" y2="{Y + dy:.1f}" stroke="#868e96" stroke-width="0.8"/>')
                            break
                    if placed:
                        break
            if placed is None:
                continue
            X, Y = placed
            self.labels.append((X - w / 2, Y - h / 2, X + w / 2, Y + h / 2))
            out.append(f'<rect x="{X - w / 2:.1f}" y="{Y - h / 2:.1f}" width="{w:.1f}" height="{h}" rx="6" fill="#fff" stroke="#495057" '
                       f'stroke-width="0.8"/><text x="{X:.1f}" y="{Y + 3.4:.1f}" font-size="8.8" text-anchor="middle" '
                       f'font-family="{MONO}" fill="#212529">{escape(cid)}</text>')
        self.s.raw("tag", "".join(out))

    # ---------------------------------------------------------------- runs
    def run_lines(self, runs, nodes, width=6.0, codes=True, clip_ticks=True):
        o, badges = [], []
        for r in runs:
            pts = [nodes[n] for n in r["nodes"]]
            if not any(self.hit3(q, 40) for q in pts):
                continue
            sp = [self.p(q) for q in pts]
            col = RUN_COL["tent"] if r["zone"] == "tent" else (RUN_COL["lv"] if r["lv"] else RUN_COL["elv"])
            dash = ' stroke-dasharray="9 5"' if r["zone"] == "tent" else ""
            ww = width * (1.4 if r["kind"] in ("conduit", "lv_conduit") else 1.0)
            o.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in sp)}" fill="none" stroke="{col}" stroke-width="{ww:.1f}" '
                     f'stroke-linejoin="round" stroke-linecap="round" opacity="0.85"{dash}/>')
            if clip_ticks and r.get("clip"):
                for a, b in zip(pts[:-1], pts[1:]):
                    L = math.dist(a, b)
                    n = int(L // r["clip"])
                    for k in range(n):
                        t = (k + 0.5) / n
                        X, Y = self.p(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))
                        o.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="{ww / 2 + 1.6:.1f}" fill="none" stroke="#000" stroke-width="1.2"/>')
            if codes:
                seg = max(zip(sp[:-1], sp[1:]), key=lambda ab: math.dist(*ab))
                badges.append((r["code"], seg))
        self.g("wire", "".join(o))
        out = []
        for code, (a, b) in badges:
            L = math.dist(a, b) or 1
            nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
            done = False
            for t in (0.5, 0.35, 0.65, 0.2, 0.8):
                for off in (16, -16, 28, -28, 0):
                    X = a[0] + (b[0] - a[0]) * t + nx * off
                    Y = a[1] + (b[1] - a[1]) * t + ny * off
                    rr = (X - 15, Y - 9, X + 15, Y + 9)
                    if self.free(rr):
                        self.labels.append(rr)
                        out.append(f'<rect x="{X - 15:.1f}" y="{Y - 8.5:.1f}" width="30" height="17" rx="3" fill="#1f5fa8"/>'
                                   f'<text x="{X:.1f}" y="{Y + 3.6:.1f}" font-size="9.5" text-anchor="middle" font-weight="700" '
                                   f'fill="#fff" font-family="{MONO}">{code}</text>')
                        done = True
                        break
                if done:
                    break
        self.s.raw("tag", "".join(out))

    def note(self, q, text, dx=0, dy=-14, size=9.5, anchor="middle", color="#495057"):
        X, Y = self.p(q)
        if self.inside(X, Y):
            self.s.text(X + dx, Y + dy, text, size=size, anchor=anchor, fill=color, italic=True)


# ====================================================================== helpers
def _split(pts, keep):
    """Pieces of a polyline where keep(point) holds; segments crossing the boundary are cut at it (bisection)."""
    out, cur = [], []
    for a, b in zip(pts[:-1], pts[1:]):
        ka, kb = keep(a), keep(b)
        if ka and kb:
            if not cur:
                cur = [a]
            cur.append(b)
        elif ka or kb:
            lo, hi = (0.0, 1.0)
            for _ in range(24):
                m = (lo + hi) / 2
                q = tuple(a[i] + (b[i] - a[i]) * m for i in range(3))
                if keep(q) == ka:
                    lo = m
                else:
                    hi = m
            q = tuple(a[i] + (b[i] - a[i]) * lo for i in range(3))
            if ka:
                if not cur:
                    cur = [a]
                cur.append(q)
                out.append(cur)
                cur = []
            else:
                cur = [q, b]
        else:
            if cur:
                out.append(cur)
                cur = []
    if cur:
        out.append(cur)
    return out


def outside_tub(q):
    return q[0] < -55 or q[1] < -841 or q[2] < -25


def outside_tub_front(q):
    return q[0] < -10 or q[2] > 548
def cable_list(s, x, y, cabs, runs_of, width=540, title="Cables in this view", max_rows=40, size=9.5):
    rows = []
    cw = min(178, (width - 46 - 70) / 2)                  # From / To columns (narrow tables keep 70 for the runs)
    n = int((cw - 8) / (size * 0.56))                     # characters that fit
    for c in cabs[:max_rows]:
        rr = [r for r in c["runs"] if r in runs_of] if runs_of else c["runs"]
        rows.append((c["id"], (c["frm"][:n - 1] + "…") if len(c["frm"]) > n else c["frm"],
                     (c["to"][:n - 1] + "…") if len(c["to"]) > n else c["to"], " ".join(rr) or "local"))
    return s.table(x, y, ["ID", "From", "To", "Runs here"], rows, [46, cw, cw, width - 46 - 2 * cw], size=size, rh=15, title=title)


def legend(s, x, y):
    items = [("#c92a2a", "12 V +  / DC"), ("#212529", "DC −"), ("#a0522d", "230 V (sheathed flex)"), ("#e8590c", "PV"),
             ("#6f42c1", "data / control"), ("#2b8a3e", "earth"), ("#7048e8", "tent harness (detachable)")]
    cx = x
    for col, lab in items:
        s.raw("text", f'<line x1="{cx}" y1="{y}" x2="{cx + 22}" y2="{y}" stroke="{col}" stroke-width="3"/>'
                      f'<text x="{cx + 27}" y="{y + 3.5}" font-size="9.5" fill="#343a40">{escape(lab)}</text>')
        cx += 32 + len(lab) * 5.4 + 12
    s.raw("text", f'<rect x="{cx}" y="{y - 8.5}" width="30" height="17" rx="3" fill="#1f5fa8"/><text x="{cx + 15}" y="{y + 3.6}" '
                  f'font-size="9.5" text-anchor="middle" font-weight="700" fill="#fff" font-family="{MONO}">R07</text>'
                  f'<text x="{cx + 36}" y="{y + 3.5}" font-size="9.5" fill="#343a40">run code (schedule on E8)</text>')
    cx += 200
    s.raw("text", f'<circle cx="{cx + 6}" cy="{y}" r="4.5" fill="none" stroke="#000" stroke-width="1.2"/>'
                  f'<text x="{cx + 16}" y="{y + 3.5}" font-size="9.5" fill="#343a40">P-clip / saddle</text>')


def in_view(c, view, pts_of=None):
    pts = pts_of(c) if pts_of else c["points"]
    return any(view.hit3(q, 0) for q in pts)


# ====================================================================== sheets
def build(ctx):
    R, USED, TOTAL = ctx["ROUTES"], ctx["USED"], ctx["TOTAL"]
    cabs = R["cables"]
    runs = R["runs"]
    nodes = {k: tuple(v) for k, v in R["nodes"].items()}
    outl = R["outlines"]
    by_run = {r["code"]: r for r in runs}
    XY_TOP = ((1, 1), (0, 1))        # plan, front at the top, driver (+Y) to the right
    YZ_REAR = ((1, 1), (2, -1))      # from behind, looking forward: driver to the right
    XZ_PASS = ((0, 1), (2, -1))      # from the passenger side: front to the left
    XY_LONG = ((0, 1), (1, -1))      # plan, front to the left, driver side up

    def mark(vis):
        USED.update(vis)

    # ------------------------------------------------------------------ E8 route map
    def sheet_map():
        s = Sheet(8, "routes", "Cable routes: route map and run schedule",
                  "Every physical run (R-code) from the routed 3D model. Detail by zone on E10–E14; bundle sections and fill on E15.", TOTAL)
        world_p = (-3450, 1650, -1000, 1000)
        sc = min(1010 / 5100, 380 / 2000)
        vp = View(s, 46, 112, 1010, 380, XY_LONG, world_p, "PLAN — front to the left, driver side up", sc=sc)
        vs = View(s, 46, 530, 1010, 430, XZ_PASS, (-3450, 1650, -1160, 700), "SIDE — from the passenger side", sc=sc)
        for v in (vp, vs):
            v.outlines(outl, only=("tub_floor", "tub_wall_", "tub_front_wall", "cab_body", "chassis_rail_-1", "chassis_rail_1",
                                   "wheel_430_-1", "wheel_-2840_-1", "plat_side", "plat_end", "tent_shell", "load_lid", "start_battery",
                                   "cabin_compute_box", "gap_junction_box", "bay_base_tray", "pc_top", "cable_tray", "visor_controller_box"),
                       fill="#f1f3f5", label=False)
            v.run_lines(runs, nodes, width=4.0, clip_ticks=False)
        for txt, q in (("ENGINE BAY", (-3000, -800, 600)), ("CAB", (-1300, -800, 600)), ("TUB", (800, -800, 600))):
            vp.note(q, txt, size=11, color="#868e96")
        for txt, q in (("ENGINE BAY", (-3000, 0, 450)), ("CAB", (-1300, 0, 900)), ("TUB", (800, 0, 520)), ("TENT", (800, 0, 1120))):
            vs.note(q, txt, size=11, color="#868e96")
        rows = []
        for r in runs:
            L = sum(math.dist(nodes[a], nodes[b]) for a, b in zip(r["nodes"][:-1], r["nodes"][1:])) / 1000
            cont = {"conduit": f"split conduit {r['conduit_id']}", "lv_conduit": f"orange conduit {r['conduit_id']}",
                    "loom": f"spiral wrap {r['conduit_id']}", "tray": "tray", "channel": "wall channel", "hollow": "in extrusion",
                    "chain": "drag chain"}.get(r["kind"], "ties / mounts")
            fill = f"{r['fill']:.0%}" if r["kind"] in ("conduit", "lv_conduit", "loom") else ""
            rows.append((r["code"], r["name"][:34], f"{L:.2f}", len(r["members"]), cont, fill, "230 V" if r["lv"] else (
                "mixed" if any(next(c for c in cabs if c["id"] == m)["lv"] for m in r["members"]) else "12 V")))
        y = s.table(1076, 128, ["Run", "Name", "m", "n", "Containment", "Fill", "V"], rows, [40, 222, 38, 24, 120, 36, 48],
                    size=9.2, rh=15.2, title="Run schedule")
        s.note(1076, y + 14, 574, ["- 230 V cables (orange runs) never share a conduit, gland row or tray compartment",
                                   "  with 12 V: own grommet row, own orange conduit, separator in the slide chain.",
                                   "- Outside the tub every run is in split conduit on rubber-lined P-clips every",
                                   "  300 mm (circles on E12), into M6 rivnuts - no welding or drilling the rail flanges.",
                                   "- Fill = cable area / conduit area (≤ 50 % for split conduit laid in).",
                                   "- Lengths: routed in the model; schedule adds 10 % + 0.3 m per cable."],
               title="Routing rules", size=10, lh=14)
        legend(s, 46, 1000)
        mark([m for r in runs for m in r["members"]])
        return s

    # ------------------------------------------------------------------ E10 front bay
    def sheet_bay():
        s = Sheet(10, "routes-bay", "Cable routes: front bay",
                  "Busbar side, rear channel (behind the board edge and the inverter), front channel, charging-board loom and the exits to the tray and the slide.", TOTAL)
        sc = min(1010 / 1240, 300 / 380)
        vp = View(s, 46, 112, 1010, 330, XY_TOP, (-620, 620, -20, 360), "PLAN — front wall at the top, driver side to the right",
                  depth=(2, -10, 560), sc=sc)
        ve = View(s, 46, 478, 1010, 480, YZ_REAR, (-620, 620, -560, 10), "VIEW FROM THE REAR — looking forward (guard removed)",
                  depth=(0, -60, 420), sc=sc)
        for v in (vp, ve):
            v.outlines(outl, groups=("bay", "electrical", "batteries", "battery_heat", "battery_insul", "power_cabinet"))
            v.run_lines([r for r in runs if r["zone"] in ("bay", "tray", "slide")], nodes, width=3.0, codes=True, clip_ticks=False)
        sel = [c for c in cabs if any(r in by_run and by_run[r]["zone"] == "bay" for r in c["runs"]) or
               (not c["runs"] and c["points"][0][0] < 420 and c["points"][0][2] < 560)]
        for v in (vp, ve):
            vis = v.cables(sel)
            v.label_cables(vis)
            mark(vis)
        bay_runs = {r["code"] for r in runs if r["zone"] == "bay"}
        cable_list(s, 1076, 128, sorted(sel, key=lambda c: c["id"]), bay_runs, width=574, title="Cables in the bay", max_rows=46, size=8.8)
        legend(s, 46, 1000)
        return s

    # ------------------------------------------------------------------ E11 tray, wall channel, cabinet
    def sheet_tub():
        s = Sheet(11, "routes-tub", "Cable routes: tray, wall channel, gland plate and rear cabinet",
                  "Passenger side of the tub. 230 V (orange) on the wall side of the tray divider, its own drop, gland row and cabinet gland.", TOTAL)
        sc = min(1010 / 1600, 450 / 640)
        ve = View(s, 46, 112, 1010, 460, XZ_PASS, (-30, 1570, -560, 80), "VIEW OUTBOARD — from inside the tub toward the passenger wall",
                  depth=(1, -830, -560), sc=sc)
        vp = View(s, 46, 612, 1010, 200, XY_LONG, (-30, 1570, 540, 830), "PLAN — passenger strip (tray, channel, cabinet)", sc=sc)
        for v in (ve, vp):
            v.outlines(outl, groups=("power_cabinet", "electrical", "bay"))
            v.outlines(outl, only=("tub_wall_passenger", "factory_outlet_gland_plate", "wheel_arch_passenger"), fill="#f8f9fa", label=False)
            v.run_lines([r for r in runs if r["zone"] in ("tray", "wall", "cabinet", "under", "bay")], nodes, width=3.0, clip_ticks=False)
        sel = [c for c in cabs if any(r in by_run and by_run[r]["zone"] in ("tray", "wall", "cabinet") for r in c["runs"]) or
               (not c["runs"] and c["points"][0][0] > 800 and c["points"][0][1] < -560)]
        for v in (ve, vp):
            vis = v.cables(sel)
            v.label_cables(vis)
            mark(vis)
        tub_runs = {r["code"] for r in runs if r["zone"] in ("tray", "wall", "cabinet")}
        cable_list(s, 1076, 128, sorted(sel, key=lambda c: c["id"]), tub_runs, width=574, title="Cables in the tray, channel and cabinet",
                   max_rows=40, size=8.8)
        s.note(46, 840, 1010, ["- Tray (R07/R08): 120 mm aluminium over the drawer carcass; 230 V outboard of the divider, 12 V inboard; ties through the slots every 120 mm.",
                               "- Wall channel (R09/R10): 22 mm behind the drawer runner panel; two layers of 12 V cables, 230 V in its own drop 135 mm further forward.",
                               "- Gland plate (old 240 V outlet hole, 120 × 90): one grommet row for 230 V (R09), two rows for 12 V (R32); cut the plate from 3 mm aluminium.",
                               "- Cabinet: 12 V through a 100 × 22 slot with a split grommet (R12), 230 V through its own 28 mm gland (R11) beside the RCBO enclosure."],
               title="Fixing", size=10, lh=14)
        legend(s, 46, 1000)
        return s

    # ------------------------------------------------------------------ E12 under the vehicle
    def sheet_under():
        s = Sheet(12, "routes-under", "Cable routes: wall cavity, chassis rail, cabin and engine bay",
                  "Outside the tub: 12 V in black split conduit, 230 V in orange conduit below it on the rail web; P-clips every 300 mm.", TOTAL)
        sc = min(1580 / 5000, 330 / 900)
        ve = View(s, 46, 112, 1580, 380, XZ_PASS, (-3450, 1600, -560, 360), "SIDE — from the passenger side", depth=(1, -1000, -300), sc=sc)
        vp = View(s, 46, 530, 1580, 300, XY_LONG, (-3450, 1600, 0, 960), "PLAN — passenger half, from above", sc=sc)
        for v in (ve, vp):
            v.outlines(outl, only=("chassis_rail_-1", "tub_floor", "tub_wall_passenger", "cab_body", "wheel_430_-1", "wheel_-2840_-1",
                                   "start_battery", "cabin_compute_box", "gap_junction_box", "factory_outlet_gland_plate", "tub_skin_passenger"),
                       fill="#f1f3f5")
            v.run_lines([r for r in runs if r["zone"] in ("under", "chassis", "cabin", "engine", "gap")], nodes, width=4.0)
        sel = [c for c in cabs if any(r in by_run and by_run[r]["zone"] in ("under", "chassis", "cabin", "engine") for r in c["runs"])]
        for v in (ve, vp):
            vis = v.cables(sel, width=0.6, keep=outside_tub)
            v.label_cables(vis, prefer_ends=True)
            mark(vis)
        ve.note((1320, -900, 430), "gland plate", dy=-12)
        ve.note((-760, -900, -60), "floor grommet", dy=-10)
        ve.note((-2900, -900, 260), "start battery F8", dy=-12)
        rows = []
        for code in ("R14", "R15", "R16", "R17", "R18", "R19", "R20", "R21", "R22", "R23"):
            r = by_run[code]
            L = sum(math.dist(nodes[a], nodes[b]) for a, b in zip(r["nodes"][:-1], r["nodes"][1:])) / 1000
            n_clip = int(sum(math.dist(nodes[a], nodes[b]) // (r.get("clip") or 1e9) for a, b in zip(r["nodes"][:-1], r["nodes"][1:])))
            rows.append((code, r["name"][:40], f"{L:.2f}", f"{r['conduit_id']} mm", f"{r['fill']:.0%}", n_clip, " ".join(r["members"])[:62]))
        s.table(46, 866, ["Run", "Name", "m", "Conduit", "Fill", "Clips", "Cables"], rows, [40, 260, 42, 64, 40, 40, 420], size=9.2, rh=14.5,
                title="Outside runs")
        s.note(1000, 866, 626, ["- Wall cavity (between the tub liner and the outer skin): both conduits",
                                "  drop from the gland plate and leave through the cavity's bottom drain",
                                "  opening - check on the vehicle (measurement sheet).",
                                "- Rail: conduits on the outer face of the web, 12 V above 230 V;",
                                "  keep 150 mm from the exhaust and use heat-rated conduit near it.",
                                "- Cabin: one sealed grommet in the floor under the rear seat.",
                                "- Engine bay: up the inner guard to the start battery (F8 within 150 mm)."],
               title="Fixing", size=10, lh=14)
        legend(s, 46, 1040)
        return s

    # ------------------------------------------------------------------ E13 gap, roof, tent
    def sheet_gap():
        s = Sheet(13, "routes-gap", "Cable routes: cab–tub gap, junction box, roof and tent harnesses",
                  "Risers up the gap to the junction box (230 V and 12 V sides), on up the cab back to the platform's hollow rear end member; tent harnesses across the lid front.", TOTAL)
        sc = min(720 / 1600, 700 / 1500)
        va = View(s, 46, 112, 720, 720, YZ_REAR, (-1000, 700, -1130, 340), "VIEW FORWARD — at the cab back (tent and lid shown dashed)",
                  depth=(0, -400, 700), sc=sc)
        vb = View(s, 790, 112, 520, 720, XZ_PASS, (-500, 650, -1130, 340), "SIDE — from the passenger side", depth=(1, -1000, 0), sc=sc)
        for v in (va, vb):
            v.outlines(outl, only=("cab_body", "tub_front_wall", "gap_junction_box", "plat_end_-190", "plat_side_-725", "visor_controller_box",
                                   "starlink_mini", "tent_services_box", "tent_shell", "tent_base", "load_lid", "lid_hinge_-1", "roof_rail_-1",
                                   "visor_rail_-1", "visor_drive_motor", "tent_solar_jbox", "tent_hinge_1", "chassis_rail_-1",
                                   "uts_water_jacket"), fill="#f1f3f5")
            v.run_lines([r for r in runs if r["zone"] in ("gap", "roof", "tent", "chassis")], nodes, width=4.0)
        sel = [c for c in cabs if any(r in by_run and by_run[r]["zone"] in ("gap", "roof", "tent") for r in c["runs"]) or c["id"] in ("T2", "PVV", "WHT")]
        for v in (va, vb):
            vis = v.cables(sel, width=0.7, keep=outside_tub_front)
            v.label_cables(vis)
            mark(vis)
        cable_list(s, 1330, 128, sorted(sel, key=lambda c: c["id"]), {r["code"] for r in runs if r["zone"] in ("gap", "roof", "tent")},
                   width=320, title="Cables here", max_rows=20, size=8.4)
        s.note(46, 860, 1264, ["- Junction box (JB): internal barrier; J1/J2 and the 230 V conduit (R22) on the outboard side, J3/J4 and the 12 V conduit (R23) inboard.",
                               "  Roof cables pass straight through on the 12 V side (R24) and are not detachable.",
                               "- Cab back (R25): 32 mm conduit on stick-on clamps up the C-pillar corner, over the roof edge under the platform, into the end member.",
                               "- End member (R26): hollow 34 × 34 extrusion; grommets where cables enter (underside, outboard end) and leave (inner face at Starlink / PV1-2).",
                               "- Tent (R27/R28): T1A (230 V) and T1D (12 V + PV) in separate spiral wraps, saddled under the tent base and down the lid front.",
                               "- T2 crosses from the tent top to the base at the FRONT HINGE with a 150 mm service loop: the shell opens about that hinge."],
               title="Fixing", size=10, lh=14)
        legend(s, 46, 1000)
        return s

    # ------------------------------------------------------------------ E14 power slide
    def sheet_slide():
        s = Sheet(14, "routes-slide", "Cable routes: power slide (trunk and chain)",
                  "AC3 (230 V) and DO2 (12 V) leave the bay under the guard, run on the glide tray, then through the chain (separator between them) to the pod.", TOTAL)
        camp = R["camp"]
        sc = min(1580 / 2650, 320 / 640)
        vt = View(s, 46, 112, 1580, 340, XY_LONG, (200, 2850, -40, 640), "PLAN — stowed (travel)", depth=(2, -10, 130), sc=sc)
        vc = View(s, 46, 500, 1580, 340, XY_LONG, (200, 2850, -40, 640), "PLAN — fully out (camp)", depth=(2, -10, 130), sc=sc)
        sel = [c for c in cabs if {"R29", "R30"} & set(c["runs"])]
        vt.outlines(outl, groups=("slide_p", "bay"), only=None)
        vc.outlines(camp["outlines"], groups=("slide_p",), only=None)
        vc.outlines(outl, groups=("bay",))
        vt.run_lines([r for r in runs if r["zone"] in ("slide", "bay")], nodes, width=3.0, clip_ticks=False)
        for v, f in ((vt, None), (vc, lambda c: camp["cables"].get(c["id"], c["points"]))):
            vis = v.cables(sel, pts_of=f, width=1.0)
            v.label_cables(vis)
            mark(vis)
        cr = by_run["R30"]
        s.note(46, 870, 1580, [f"- Chain: igus E2.15 R75 lying on its side on the glide tray; fixed end at mid-travel, moving end 115 mm behind the carriage front; length = travel/2 + πR.",
                               "- Cables in the chain: AC3 2.5 mm² 3-core high-flex (chain rated) and DO2 6 mm² twin high-flex, with an igus separator between them.",
                               "- Strain relief (tie plates) at both chain ends; 600 mm of each cable is in the chain (included in the schedule lengths).",
                               "- Inspect with the slide fully out: tray, fixed run, loop and both brackets are open from above."],
               title="Chain", size=10, lh=14)
        legend(s, 46, 1000)
        return s

    # ------------------------------------------------------------------ E15 sections
    def sheet_sections():
        s = Sheet(15, "sections", "Bundle cross-sections and fill",
                  "Every run's cross-section as packed in the model (biggest cables first; twins as two cores). Dashed circle = conduit inside diameter.", TOTAL)
        secs = R["sections"]
        codes = [r["code"] for r in runs if r["code"] in secs]
        cols, cw, chh = 7, 228, 152
        cmap = {c["id"]: c for c in cabs}
        for i, code in enumerate(codes):
            r = by_run[code]
            cx0, cy0 = 46 + (i % cols) * cw, 104 + (i // cols) * (chh + 34)
            sec = secs[code]
            slots = sec["slots"]
            ext = max([abs(a) + cmap[k]["od"] * cmap[k].get("cores", 1) / 2 + 2 for k, (a, b) in slots.items()] +
                      [abs(b) + cmap[k]["od"] / 2 + 2 for k, (a, b) in slots.items()] + [(r["conduit_id"] or 0) / 2 + 2])
            scc = min(2.6, (chh / 2 - 14) / ext)
            ox, oy = cx0 + cw / 2 - 6, cy0 + chh / 2 + 8
            o = [f'<rect x="{cx0}" y="{cy0}" width="{cw - 12}" height="{chh + 22}" rx="4" fill="#fff" stroke="#ced4da"/>',
                 f'<text x="{cx0 + 8}" y="{cy0 + 15}" font-size="10.5" font-weight="700" fill="#1f5fa8" font-family="{MONO}">{code}</text>'
                 f'<text x="{cx0 + 40}" y="{cy0 + 15}" font-size="9.5" fill="#343a40">{escape(r["name"][:34])}</text>']
            if r["kind"] in ("conduit", "lv_conduit", "loom") and r["conduit_id"]:
                rr = r["conduit_id"] / 2 * scc
                o.append(f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="{rr:.1f}" fill="none" stroke="{"#d9480f" if r["lv"] else "#343a40"}" '
                         f'stroke-width="1.4" stroke-dasharray="4 3"/>')
            for cid, (a, b) in slots.items():
                c = cmap[cid]
                d1, n = c["od"], c.get("cores", 1)
                col = COL.get(c["colour"], "#495057")
                for k in range(n):
                    aa = a + (k - (n - 1) / 2) * (d1 + 1)
                    kcol = "#212529" if (n == 2 and k == 1 and c["colour"] in ("w_pos", "w_12v", "w_pv") and cid not in ("CT1", "INVP")) else col
                    o.append(f'<circle cx="{ox + aa * scc:.1f}" cy="{oy - b * scc:.1f}" r="{d1 / 2 * scc:.1f}" fill="{kcol}" '
                             f'fill-opacity="0.85" stroke="#fff" stroke-width="0.6"/>')
                if d1 * scc * n > len(cid) * 5:
                    o.append(f'<text x="{ox + a * scc:.1f}" y="{oy - b * scc + 3:.1f}" font-size="7.5" text-anchor="middle" fill="#fff" '
                             f'font-family="{MONO}" font-weight="700">{escape(cid)}</text>')
            ids = " ".join(slots)
            fill = f" · fill {r['fill']:.0%} of {r['conduit_id']} mm" if r["kind"] in ("conduit", "lv_conduit", "loom") else ""
            o.append(f'<text x="{cx0 + 8}" y="{cy0 + chh + 12}" font-size="8.6" fill="#495057">{len(slots)} cables · {r["area"]} mm²{fill}</text>')
            o.append(f'<text x="{cx0 + 8}" y="{cy0 + chh + 24}" font-size="7.6" fill="#868e96" font-family="{MONO}">{escape(ids[:52])}</text>')
            s.raw("text", "".join(o))
        return s

    return [sheet_map, sheet_bay, sheet_tub, sheet_under, sheet_gap, sheet_slide, sheet_sections]
