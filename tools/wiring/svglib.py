"""Tiny SVG drawing kit for the wiring sheets (A3 landscape, 4 px per mm).

Everything is drawn in layers so wires sit under blocks and tags sit on top:
zone -> wire -> sym -> block -> tag -> text.
"""
from html import escape

W, H = 1680, 1188           # A3 landscape at 4 px/mm
M = 30                      # frame margin
FONT = "'IBM Plex Sans', 'Segoe UI', Arial, sans-serif"
MONO = "'IBM Plex Mono', Consolas, monospace"

# wire kinds: stroke colour, default width, optional dash / underlay
KIND = {
    "pos": dict(c="#c92a2a", w=3.0),
    "neg": dict(c="#212529", w=3.0),
    "pvp": dict(c="#e8590c", w=2.6),
    "pvn": dict(c="#495057", w=2.6),
    "L": dict(c="#8a4b16", w=2.4),
    "N": dict(c="#1c62c9", w=2.4),
    "PE": dict(c="#2b8a3e", w=2.4, dash="8 6", under="#f0c419"),
    "data": dict(c="#6f42c1", w=1.8),
    "ctrl": dict(c="#0b7285", w=1.8),
    "sig": dict(c="#0b7285", w=1.6, dash="5 3"),
    "fact": dict(c="#868e96", w=2.0, dash="2 4"),
    "wifi": dict(c="#6f42c1", w=1.6, dash="2 5"),
}
KIND_LABEL = {
    "pos": "DC + (red)", "neg": "DC − (black)", "pvp": "PV +", "pvn": "PV −", "L": "AC active (brown)",
    "N": "AC neutral (blue)", "PE": "Protective earth (green/yellow)", "data": "Data (VE.Bus / VE.Direct / USB)",
    "ctrl": "Control (12 V switched)", "sig": "Signal / sense", "fact": "Factory vehicle wiring", "wifi": "Wireless (Wi-Fi / BLE)",
}
# conductor size -> stroke width
SIZE_W = {"70": 5.2, "50": 4.6, "25": 3.8, "16": 3.3, "10": 3.0, "6": 2.7, "4": 2.4, "2.5": 2.2, "1.5": 1.9, "1": 1.7, "0.75": 1.5}

CAT = {   # block header colours
    "victron": "#1f5fa8", "battery": "#2f6f3e", "prot": "#b35c00", "ac": "#7c5b1e", "outlet": "#495057",
    "conn": "#5f3dc4", "gen": "#3d4650", "vehicle": "#6b7178", "pv": "#a3570c",
}


def tw(text, size=12.0):
    """Approximate rendered text width."""
    return len(str(text)) * size * 0.56


def _pts(pts):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def offset_path(pts, o):
    """Offset an orthogonal polyline sideways by o (left of travel direction = +)."""
    if len(pts) < 2:
        return pts
    segs = []
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        dx, dy = x2 - x1, y2 - y1
        L = (dx * dx + dy * dy) ** 0.5 or 1
        nx, ny = -dy / L, dx / L
        segs.append(((x1 + nx * o, y1 + ny * o), (x2 + nx * o, y2 + ny * o), (dx, dy)))
    out = [segs[0][0]]
    for a, b in zip(segs[:-1], segs[1:]):
        (p1, p2, d1), (q1, q2, d2) = a, b
        if abs(d1[0]) < 1e-6 and abs(d2[1]) < 1e-6:      # vertical then horizontal
            out.append((p2[0], q1[1]))
        elif abs(d1[1]) < 1e-6 and abs(d2[0]) < 1e-6:    # horizontal then vertical
            out.append((q1[0], p2[1]))
        else:
            out.append(p2)
    out.append(segs[-1][1])
    return out


class Block:
    def __init__(self, sheet, ref, x, y, w, h, title, lines=(), cat="gen", terms=(), note=None):
        self.s, self.ref, self.x, self.y, self.w, self.h = sheet, ref, x, y, w, h
        self.title, self.lines, self.cat, self.note = title, lines, cat, note
        self.terms = {}
        self.term_draw = []
        for key, side, off, label in terms:
            if side == "L":
                p = (x, y + off)
            elif side == "R":
                p = (x + w, y + off)
            elif side == "T":
                p = (x + off, y)
            else:
                p = (x + off, y + h)
            self.terms[key] = p
            self.term_draw.append((p, side, label))
        sheet.layers["block"].append(self)

    def t(self, key):
        return self.terms[key]

    def render(self):
        x, y, w, h = self.x, self.y, self.w, self.h
        col = CAT.get(self.cat, CAT["gen"])
        o = [f'<g class="blk"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#ffffff" stroke="#343a40" stroke-width="1.4"/>',
             f'<rect x="{x}" y="{y}" width="{w}" height="22" rx="3" fill="{col}"/>',
             f'<rect x="{x}" y="{y + 12}" width="{w}" height="10" fill="{col}"/>',
             f'<text x="{x + 6}" y="{y + 15.5}" font-size="12" font-weight="600" fill="#fff">'
             f'<tspan font-family="{MONO}" font-weight="700">{escape(self.ref)}</tspan>  {escape(self.title)}</text>']
        ty = y + 37
        for ln in self.lines:
            o.append(f'<text x="{x + 7}" y="{ty}" font-size="11" fill="#343a40">{escape(ln)}</text>')
            ty += 14
        for (px, py), side, label in self.term_draw:
            o.append(f'<circle cx="{px}" cy="{py}" r="3.6" fill="#fff" stroke="#212529" stroke-width="1.4"/>')
            if label:   # terminal labels sit outside the block, beside the wire
                if side == "L":
                    o.append(f'<text x="{px - 6}" y="{py - 6}" font-size="10" font-family="{MONO}" fill="#212529" text-anchor="end">{escape(label)}</text>')
                elif side == "R":
                    o.append(f'<text x="{px + 6}" y="{py - 6}" font-size="10" font-family="{MONO}" fill="#212529">{escape(label)}</text>')
                elif side == "T":
                    o.append(f'<text x="{px + 6}" y="{py - 6}" font-size="10" font-family="{MONO}" fill="#212529">{escape(label)}</text>')
                else:
                    o.append(f'<text x="{px + 6}" y="{py + 15}" font-size="10" font-family="{MONO}" fill="#212529">{escape(label)}</text>')
        if self.note:
            o.append(f'<text x="{x}" y="{y + h + 14}" font-size="10" font-style="italic" fill="#495057">{escape(self.note)}</text>')
        o.append("</g>")
        return "".join(o)


class Sheet:
    def __init__(self, num, key, title, subtitle="", total=8, kinds=()):
        self.num, self.key, self.title, self.subtitle, self.total = num, key, title, subtitle, total
        self.kinds = list(kinds)
        self.layers = {k: [] for k in ("zone", "wire", "sym", "block", "tag", "text")}

    # ------------------------------------------------------------------ primitives
    def raw(self, layer, s):
        self.layers[layer].append(s)

    def text(self, x, y, s, size=11, anchor="start", weight="400", fill="#343a40", family=None, italic=False, layer="text"):
        fam = f' font-family="{family}"' if family else ""
        it = ' font-style="italic"' if italic else ""
        self.raw(layer, f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
                        f'fill="{fill}"{fam}{it}>{escape(str(s))}</text>')

    def zone(self, x, y, w, h, label, sub="", bottom=False, lx=10):
        self.raw("zone", f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#f4f6f8" stroke="#adb5bd" '
                         f'stroke-width="1.2" stroke-dasharray="7 5"/>')
        ly = y + h - (24 if sub else 10) if bottom else y + 17
        self.raw("zone", f'<text x="{x + lx}" y="{ly}" font-size="11.5" font-weight="700" letter-spacing="0.06em" '
                         f'fill="#5c636a">{escape(label.upper())}</text>')
        if sub:
            self.raw("zone", f'<text x="{x + lx}" y="{ly + 14}" font-size="10" fill="#6c757d">{escape(sub)}</text>')

    def wire(self, pts, kind, size=None, tag=None, tag_at=None, layer="wire"):
        k = KIND[kind]
        wdt = SIZE_W.get(size, k["w"]) if size else k["w"]
        if "under" in k:
            self.raw(layer, f'<polyline points="{_pts(pts)}" fill="none" stroke="{k["under"]}" stroke-width="{wdt}" '
                            f'stroke-linejoin="round" stroke-linecap="round"/>')
        dash = f' stroke-dasharray="{k["dash"]}"' if "dash" in k else ""
        self.raw(layer, f'<polyline points="{_pts(pts)}" fill="none" stroke="{k["c"]}" stroke-width="{wdt}"{dash} '
                        f'stroke-linejoin="round" stroke-linecap="round"/>')
        if kind not in self.kinds:
            self.kinds.append(kind)
        if tag:
            self.tag(*(tag_at or self._mid(pts)), tag)

    def twin(self, pts, kinds=("pos", "neg"), size=None, gap=7, tag=None, tag_at=None):
        """Two-core cable drawn as a pair of parallel conductors."""
        self.wire(offset_path(pts, gap / 2), kinds[0], size)
        self.wire(offset_path(pts, -gap / 2), kinds[1], size)
        if tag:
            self.tag(*(tag_at or self._mid(pts)), tag)

    def triple(self, pts, size="2.5", gap=6, tag=None, tag_at=None):
        """3-core AC flex: active, neutral, earth."""
        self.wire(offset_path(pts, gap), "L", size)
        self.wire(pts, "N", size)
        self.wire(offset_path(pts, -gap), "PE", size)
        if tag:
            self.tag(*(tag_at or self._mid(pts)), tag)

    @staticmethod
    def _mid(pts):
        best, bl = None, -1
        for a, b in zip(pts[:-1], pts[1:]):
            L = abs(a[0] - b[0]) + abs(a[1] - b[1])
            if L > bl:
                best, bl = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), L
        return best

    def dot(self, x, y, kind="pos", r=4.2):
        self.raw("sym", f'<circle cx="{x}" cy="{y}" r="{r}" fill="{KIND[kind]["c"]}"/>')

    def tag(self, x, y, text, size=10.5):
        w = tw(text, size) + 12
        self.raw("tag", f'<g><rect x="{x - w / 2:.1f}" y="{y - 9:.1f}" width="{w:.1f}" height="18" rx="9" fill="#ffffff" '
                        f'stroke="#495057" stroke-width="1"/><text x="{x:.1f}" y="{y + 3.8:.1f}" font-size="{size}" '
                        f'font-family="{MONO}" text-anchor="middle" fill="#212529">{escape(text)}</text></g>')

    def block(self, *a, **k):
        return Block(self, *a, **k)

    def bus(self, ref, x1, y1, x2, y2, kind, label, sub="", below=False):
        """Busbar: thick bar; returns nothing (attach wires anywhere along it)."""
        col = "#b08d57" if kind == "pos" else "#868e96"
        stroke = "#c92a2a" if kind == "pos" else "#212529"
        if y1 == y2:
            self.raw("sym", f'<rect x="{x1}" y="{y1 - 6}" width="{x2 - x1}" height="12" rx="2" fill="{col}" stroke="{stroke}" stroke-width="1.6"/>')
            self.text(x1, y1 + 24 if below else y1 - 12, f"{ref}  {label}", size=11, weight="600", fill="#212529", layer="sym")
            if sub:
                self.text(x1, y1 + 22, sub, size=10, fill="#495057", layer="sym")
        else:
            self.raw("sym", f'<rect x="{x1 - 6}" y="{y1}" width="12" height="{y2 - y1}" rx="2" fill="{col}" stroke="{stroke}" stroke-width="1.6"/>')
            self.text(x1 + 12, y1 + 10, f"{ref}  {label}", size=11, weight="600", fill="#212529", layer="sym")
            if sub:
                self.text(x1 + 12, y1 + 24, sub, size=10, fill="#495057", layer="sym")

    def fuse(self, x, y, orient, ref, rating, side=1):
        """Fuse on a wire at (x, y); orient 'h' or 'v'. Label on the +side (1) or -side (-1)."""
        if orient == "h":
            self.raw("sym", f'<rect x="{x - 15}" y="{y - 7}" width="30" height="14" rx="2" fill="#fff4e6" stroke="#b35c00" stroke-width="1.5"/>'
                            f'<line x1="{x - 15}" y1="{y}" x2="{x + 15}" y2="{y}" stroke="#b35c00" stroke-width="1.3"/>')
            ty = y - 12 if side > 0 else y + 22
            self.text(x, ty, f"{ref} {rating}", size=10.5, anchor="middle", weight="600", fill="#8a4500", layer="sym")
        else:
            self.raw("sym", f'<rect x="{x - 7}" y="{y - 15}" width="14" height="30" rx="2" fill="#fff4e6" stroke="#b35c00" stroke-width="1.5"/>'
                            f'<line x1="{x}" y1="{y - 15}" x2="{x}" y2="{y + 15}" stroke="#b35c00" stroke-width="1.3"/>')
            tx, an = (x + 12, "start") if side > 0 else (x - 12, "end")
            self.text(tx, y + 4, f"{ref} {rating}", size=10.5, anchor=an, weight="600", fill="#8a4500", layer="sym")

    def switch(self, x, y, orient, ref, label, side=1, poles=1):
        """Open switch symbol centred on (x, y) of a wire running orient 'h'/'v'."""
        if orient == "h":
            g = (f'<rect x="{x - 16}" y="{y - 4}" width="32" height="8" fill="#f8f9fa"/>'
                 f'<circle cx="{x - 12}" cy="{y}" r="2.6" fill="#212529"/><circle cx="{x + 12}" cy="{y}" r="2.6" fill="#212529"/>'
                 f'<line x1="{x - 12}" y1="{y}" x2="{x + 10}" y2="{y - 11}" stroke="#212529" stroke-width="2"/>')
            self.raw("sym", g)
            self.text(x, y - 16 if side > 0 else y + 20, f"{ref} {label}", size=10.5, anchor="middle", weight="600", fill="#212529", layer="sym")
        else:
            g = (f'<rect x="{x - 4}" y="{y - 16}" width="8" height="32" fill="#f8f9fa"/>'
                 f'<circle cx="{x}" cy="{y - 12}" r="2.6" fill="#212529"/><circle cx="{x}" cy="{y + 12}" r="2.6" fill="#212529"/>'
                 f'<line x1="{x}" y1="{y + 12}" x2="{x - 11}" y2="{y - 10}" stroke="#212529" stroke-width="2"/>')
            self.raw("sym", g)
            tx, an = (x + 12, "start") if side > 0 else (x - 16, "end")
            self.text(tx, y + 4, f"{ref} {label}", size=10.5, anchor=an, weight="600", fill="#212529", layer="sym")

    def conn(self, x, y, orient, ref, label, side=1):
        """Detachable connector (plug/socket pair) centred on (x, y)."""
        if orient == "h":
            g = (f'<path d="M{x - 14},{y - 11} L{x - 2},{y - 11} L{x - 2},{y + 11} L{x - 14},{y + 11} Z" fill="#e5dbff" stroke="#5f3dc4" stroke-width="1.5"/>'
                 f'<path d="M{x + 2},{y - 11} Q{x + 14},{y} {x + 2},{y + 11} Z" fill="#d0bfff" stroke="#5f3dc4" stroke-width="1.5"/>')
            self.raw("sym", g)
            self.text(x, y - 16 if side > 0 else y + 26, f"{ref}", size=11, anchor="middle", weight="700", fill="#5f3dc4", family=MONO, layer="sym")
            if label:
                self.text(x, y - 29 if side > 0 else y + 39, label, size=10, anchor="middle", fill="#5f3dc4", layer="sym")
        else:
            g = (f'<path d="M{x - 11},{y - 14} L{x + 11},{y - 14} L{x + 11},{y - 2} L{x - 11},{y - 2} Z" fill="#e5dbff" stroke="#5f3dc4" stroke-width="1.5"/>'
                 f'<path d="M{x - 11},{y + 2} Q{x},{y + 14} {x + 11},{y + 2} Z" fill="#d0bfff" stroke="#5f3dc4" stroke-width="1.5"/>')
            self.raw("sym", g)
            tx, an = (x + 16, "start") if side > 0 else (x - 16, "end")
            self.text(tx, y + 4, ref, size=11, anchor=an, weight="700", fill="#5f3dc4", family=MONO, layer="sym")
            if label:
                self.text(tx, y + 17, label, size=10, anchor=an, fill="#5f3dc4", layer="sym")

    def motor(self, x, y, ref, label=""):
        self.raw("sym", f'<circle cx="{x}" cy="{y}" r="16" fill="#fff" stroke="#212529" stroke-width="1.6"/>'
                        f'<text x="{x}" y="{y + 4.5}" font-size="13" font-weight="700" text-anchor="middle" fill="#212529">M</text>')
        self.text(x, y + 32, ref, size=10.5, anchor="middle", weight="700", family=MONO, layer="sym")
        if label:
            self.text(x, y + 45, label, size=10, anchor="middle", layer="sym")

    def gland(self, x, y, label="gland", side=1):
        """Pass-through cable gland (not a connector) on a horizontal run at (x, y)."""
        self.raw("sym", f'<rect x="{x - 5}" y="{y - 13}" width="10" height="26" rx="2" fill="#dee2e6" stroke="#495057" stroke-width="1.3"/>')
        if label:
            self.text(x, y - 18 if side > 0 else y + 26, label, size=9.5, anchor="middle", fill="#495057", layer="sym")

    def earth(self, x, y, label="", chassis=True):
        """Chassis-earth symbol hanging below (x, y)."""
        g = [f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + 10}" stroke="#212529" stroke-width="2"/>',
             f'<line x1="{x - 13}" y1="{y + 10}" x2="{x + 13}" y2="{y + 10}" stroke="#212529" stroke-width="2.2"/>']
        if chassis:
            for i in range(4):
                xx = x - 12 + i * 8
                g.append(f'<line x1="{xx}" y1="{y + 10}" x2="{xx - 6}" y2="{y + 18}" stroke="#212529" stroke-width="1.6"/>')
        else:
            g.append(f'<line x1="{x - 8}" y1="{y + 15}" x2="{x + 8}" y2="{y + 15}" stroke="#212529" stroke-width="2"/>'
                     f'<line x1="{x - 3}" y1="{y + 20}" x2="{x + 3}" y2="{y + 20}" stroke="#212529" stroke-width="2"/>')
        self.raw("sym", "".join(g))
        if label:
            self.text(x + 18, y + 16, label, size=10.5, fill="#212529", layer="sym")

    def offsheet(self, x, y, direction, text, sub=""):
        """Off-sheet reference flag. direction: 'r' (points right), 'l', 'u', 'd'. (x, y) = the wire end."""
        w = max(tw(text, 10.5), tw(sub, 9.5)) + 22
        h = 30 if sub else 20
        if direction == "r":
            x0 = x
            pts = [(x0, y - h / 2), (x0 + w - 10, y - h / 2), (x0 + w, y), (x0 + w - 10, y + h / 2), (x0, y + h / 2)]
            tx = x0 + 6
        elif direction == "l":
            x0 = x - w
            pts = [(x0 + 10, y - h / 2), (x0 + w, y - h / 2), (x0 + w, y + h / 2), (x0 + 10, y + h / 2), (x0, y)]
            tx = x0 + 14
        elif direction == "u":
            x0 = x - w / 2
            y0 = y - h - 10
            pts = [(x0, y0 + 10), (x0 + w / 2, y0), (x0 + w, y0 + 10), (x0 + w, y0 + 10 + h), (x0, y0 + 10 + h)]
            tx, y = x0 + 8, y0 + 10 + h / 2
        else:
            x0 = x - w / 2
            y0 = y
            pts = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0 + w / 2, y0 + h + 10), (x0, y0 + h)]
            tx, y = x0 + 8, y0 + h / 2
        self.raw("tag", f'<polygon points="{_pts(pts)}" fill="#fff9db" stroke="#a07c00" stroke-width="1.2"/>')
        if sub:
            self.raw("tag", f'<text x="{tx:.1f}" y="{y - 2:.1f}" font-size="10.5" font-weight="600" fill="#212529">{escape(text)}</text>'
                            f'<text x="{tx:.1f}" y="{y + 10:.1f}" font-size="9.5" fill="#495057">{escape(sub)}</text>')
        else:
            self.raw("tag", f'<text x="{tx:.1f}" y="{y + 4:.1f}" font-size="10.5" font-weight="600" fill="#212529">{escape(text)}</text>')

    def note(self, x, y, w, lines, title=None, size=10.5, lh=15):
        h = len(lines) * lh + (24 if title else 10) + 6
        o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#ffffff" stroke="#ced4da" stroke-width="1"/>']
        ty = y + 16
        if title:
            o.append(f'<text x="{x + 10}" y="{ty}" font-size="11" font-weight="700" letter-spacing="0.05em" fill="#343a40">{escape(title.upper())}</text>')
            ty += 18
        for ln in lines:
            bullet = ln.startswith("- ")
            t = ln[2:] if bullet else ln
            if bullet:
                o.append(f'<circle cx="{x + 13}" cy="{ty - 4}" r="1.8" fill="#495057"/>')
            o.append(f'<text x="{x + (20 if bullet else 10)}" y="{ty}" font-size="{size}" fill="#343a40">{escape(t)}</text>')
            ty += lh
        self.raw("text", "".join(o))
        return y + h

    def table(self, x, y, headers, rows, widths, size=10.5, rh=17, title=None):
        o = []
        if title:
            o.append(f'<text x="{x}" y="{y - 8}" font-size="11.5" font-weight="700" letter-spacing="0.05em" fill="#343a40">{escape(title.upper())}</text>')
        tot = sum(widths)
        o.append(f'<rect x="{x}" y="{y}" width="{tot}" height="{rh + 2}" fill="#343a40"/>')
        cx = x
        for hd, wd in zip(headers, widths):
            o.append(f'<text x="{cx + 6}" y="{y + 13}" font-size="{size}" font-weight="600" fill="#fff">{escape(hd)}</text>')
            cx += wd
        yy = y + rh + 2
        for i, r in enumerate(rows):
            if i % 2:
                o.append(f'<rect x="{x}" y="{yy}" width="{tot}" height="{rh}" fill="#f1f3f5"/>')
            cx = x
            for v, wd in zip(r, widths):
                o.append(f'<text x="{cx + 6}" y="{yy + 12.5}" font-size="{size}" fill="#212529">{escape(str(v))}</text>')
                cx += wd
            yy += rh
        o.append(f'<rect x="{x}" y="{y}" width="{tot}" height="{yy - y}" fill="none" stroke="#adb5bd" stroke-width="1"/>')
        self.raw("text", "".join(o))
        return yy

    # ------------------------------------------------------------------ frame
    def frame(self, meta):
        o = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>',
             f'<rect x="{M - 12}" y="{M - 12}" width="{W - 2 * M + 24}" height="{H - 2 * M + 24}" fill="none" stroke="#212529" stroke-width="1"/>',
             f'<rect x="{M}" y="{M}" width="{W - 2 * M}" height="{H - 2 * M}" fill="none" stroke="#212529" stroke-width="2"/>']
        # grid references
        cols, rows = 12, 8
        cw, rh_ = (W - 2 * M) / cols, (H - 2 * M) / rows
        for i in range(cols):
            cx = M + (i + 0.5) * cw
            o.append(f'<text x="{cx:.0f}" y="{M - 2}" font-size="9" text-anchor="middle" fill="#495057">{i + 1}</text>')
            o.append(f'<text x="{cx:.0f}" y="{H - M + 10}" font-size="9" text-anchor="middle" fill="#495057">{i + 1}</text>')
            if i:
                xx = M + i * cw
                o.append(f'<line x1="{xx:.0f}" y1="{M - 12}" x2="{xx:.0f}" y2="{M}" stroke="#212529"/><line x1="{xx:.0f}" y1="{H - M}" x2="{xx:.0f}" y2="{H - M + 12}" stroke="#212529"/>')
        for j in range(rows):
            cy = M + (j + 0.5) * rh_
            ch = "ABCDEFGH"[j]
            o.append(f'<text x="{M - 6}" y="{cy + 3:.0f}" font-size="9" text-anchor="middle" fill="#495057">{ch}</text>')
            o.append(f'<text x="{W - M + 6}" y="{cy + 3:.0f}" font-size="9" text-anchor="middle" fill="#495057">{ch}</text>')
            if j:
                yy = M + j * rh_
                o.append(f'<line x1="{M - 12}" y1="{yy:.0f}" x2="{M}" y2="{yy:.0f}" stroke="#212529"/><line x1="{W - M}" y1="{yy:.0f}" x2="{W - M + 12}" y2="{yy:.0f}" stroke="#212529"/>')
        # sheet heading
        o.append(f'<text x="{M + 16}" y="{M + 30}" font-size="22" font-weight="700" fill="#212529">{escape(self.title)}</text>')
        if self.subtitle:
            o.append(f'<text x="{M + 16}" y="{M + 50}" font-size="12" fill="#495057">{escape(self.subtitle)}</text>')
        # title block
        bw, bh = 560, 112
        bx, by = W - M - bw, H - M - bh
        o.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="#ffffff" stroke="#212529" stroke-width="1.6"/>')
        o.append(f'<line x1="{bx}" y1="{by + 34}" x2="{bx + bw}" y2="{by + 34}" stroke="#212529"/>'
                 f'<line x1="{bx}" y1="{by + 62}" x2="{bx + bw}" y2="{by + 62}" stroke="#212529"/>'
                 f'<line x1="{bx + 400}" y1="{by + 34}" x2="{bx + 400}" y2="{by + 62}" stroke="#212529"/>'
                 f'<line x1="{bx + 400}" y1="{by}" x2="{bx + 400}" y2="{by + 34}" stroke="#212529"/>')
        o.append(f'<text x="{bx + 10}" y="{by + 15}" font-size="9.5" fill="#6c757d">PROJECT</text>'
                 f'<text x="{bx + 10}" y="{by + 29}" font-size="13" font-weight="700" fill="#212529">Kia Tasman X-Pro fit-out · electrical</text>'
                 f'<text x="{bx + 410}" y="{by + 15}" font-size="9.5" fill="#6c757d">SHEET</text>'
                 f'<text x="{bx + 410}" y="{by + 30}" font-size="15" font-weight="700" fill="#212529">E{self.num} of E{self.total}</text>'
                 f'<text x="{bx + 10}" y="{by + 45}" font-size="9.5" fill="#6c757d">TITLE</text>'
                 f'<text x="{bx + 10}" y="{by + 58}" font-size="12.5" font-weight="600" fill="#212529">{escape(self.title)}</text>'
                 f'<text x="{bx + 410}" y="{by + 45}" font-size="9.5" fill="#6c757d">REV / DATE</text>'
                 f'<text x="{bx + 410}" y="{by + 58}" font-size="12" font-weight="600" fill="#212529">{escape(meta["version"])} · {escape(meta["date"])}</text>'
                 f'<text x="{bx + 10}" y="{by + 78}" font-size="10" fill="#495057">Generated by tools/wiring/diagram.py from cad/fitout/wiring.py — cable IDs and lengths</text>'
                 f'<text x="{bx + 10}" y="{by + 91}" font-size="10" fill="#495057">match bom/cable-schedule-{escape(meta["version"])}.csv. Measurements still [EST] until confirmed on the vehicle.</text>'
                 f'<text x="{bx + 10}" y="{by + 105}" font-size="10" font-weight="700" fill="#c92a2a">230 V work: licensed electrician only (AS/NZS 3000 · AS/NZS 3001.2). Not certified.</text>')
        # legend
        if self.kinds:
            lx, ly = M + 16, H - M - 30
            items = [k for k in KIND if k in self.kinds]
            cx, row = lx, 0
            for k in items:
                kk = KIND[k]
                lab = KIND_LABEL[k]
                if cx + 34 + tw(lab, 10.5) > 1070:
                    cx, row = lx, row + 1
                yy = ly + 15 * row
                if "under" in kk:
                    o.append(f'<line x1="{cx}" y1="{yy}" x2="{cx + 28}" y2="{yy}" stroke="{kk["under"]}" stroke-width="3"/>')
                dash = f' stroke-dasharray="{kk["dash"]}"' if "dash" in kk else ""
                o.append(f'<line x1="{cx}" y1="{yy}" x2="{cx + 28}" y2="{yy}" stroke="{kk["c"]}" stroke-width="3"{dash}/>')
                o.append(f'<text x="{cx + 34}" y="{yy + 4}" font-size="10.5" fill="#343a40">{escape(lab)}</text>')
                cx += 34 + tw(lab, 10.5) + 22
            o.append(f'<text x="{lx}" y="{ly - 14}" font-size="9.5" fill="#6c757d">LEGEND · line weight ∝ conductor size · '
                     f'<tspan font-family="{MONO}">ID · size</tspan> tags = cable schedule IDs · purple ▶◀ = detachable connector · yellow flags = continues on another sheet</text>')
        return "".join(o)

    def svg(self, meta):
        body = [self.frame(meta)]
        for k in ("zone", "wire", "sym"):
            body += self.layers[k]
        body += [b.render() for b in self.layers["block"]]
        body += self.layers["tag"] + self.layers["text"]
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
                f'font-family="{FONT}" role="img" aria-label="{escape(self.title)}">' + "".join(body) + "</svg>")
