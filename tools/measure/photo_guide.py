"""
Photo guide for the measurement sheet: the owner's own photos of the tub, marked up with the reference lines and with
where each measurement starts and ends. Imported by measure_sheet.py (pages go in after the intro).

Coordinates are in the ORIGINAL photo pixels (the photos sent on 2026-11-01); the copies in docs/measurements/photos/ are
scaled by SCALE. Each mark: (kind, item id, geometry, label offset). Kinds:
    datum  - blue dashed reference line          ("datum", id, (x1, y1, x2, y2), (dx, dy))
    dim    - yellow dimension arrow, both ends    ("dim", id, (x1, y1, x2, y2), (dx, dy))
    pt     - red point (a start or end point)     ("pt", id, (x, y), (dx, dy))
    box    - dashed outline round a feature       ("box", id, (x1, y1, x2, y2), (dx, dy))
    line   - solid red edge to measure to         ("line", id, (x1, y1, x2, y2), (dx, dy))
"""
from html import escape

SCALE = 0.6        # original photo px -> stored copy px (2000 -> 1200)

# key: (file, title, where it was taken from, original size, marks, legend)
# legend rows: (id, what it is, FROM, TO, how)
PHOTOS = {
    "P1": ("p1-tub-from-tailgate.jpg", "Whole tub from the tailgate",
           "Standing at the open tailgate, looking forward. Driver side (D) is on the RIGHT, passenger (P) on the left.", (2000, 1500),
           [("datum", "X0", (507, 600, 1467, 600), (0, -36)),
            ("datum", "Z0", (560, 1110, 1450, 1110), (330, -22)),
            ("datum", "Y0", (987, 600, 1083, 1350), (40, 120)),
            ("dim", "T1", (800, 1180, 800, 610), (-70, 0)),
            ("dim", "W4", (488, 680, 1505, 680), (-360, -30)),
            ("pt", "C13", (300, 533), (-40, -50)), ("pt", "C13", (1620, 540), (40, -50)),
            ("pt", "L16", (327, 360), (40, 40)), ("pt", "L16", (1580, 387), (-40, 40)),
            ("pt", "T17", (567, 1353), (-80, 0)), ("pt", "T17", (1600, 1347), (80, 0)),
            ("pt", "L8", (133, 147), (60, 50)), ("pt", "L8", (1907, 120), (-60, 50)),
            ("pt", "L5", (967, 205), (0, -40))],
           [("X0", "Reference X = 0: the front wall", "–", "–",
             "Hold a straight edge (level) flat across the RAISED panels of the front wall, about 100 mm above the floor. Every X is "
             "measured from that edge, not from the bottom of the vertical grooves."),
            ("Z0", "Reference Z = 0: the floor", "–", "–",
             "Lay the straight edge across the floor ribs. Every height is measured from the TOPS of the ribs (the ridges), never the valleys."),
            ("Y0", "Reference Y = 0: the centreline", "–", "–",
             "Mark halfway between the two round floor plugs at the tailgate end, and halfway wall-to-wall at the front wall. "
             "Run masking tape between the two marks; Y is measured square off this line."),
            ("T1", "Floor length", "inside face of the CLOSED tailgate", "the X0 straight edge",
             "On the centreline, at rib-top height. Laser: back of the laser flat on the closed tailgate, aim at a card held on the "
             "straight edge. Your photo reads 1.508 m: note where the back of the laser was."),
            ("W4", "Width between the arches", "inner face of the P arch", "inner face of the D arch",
             "Just above the floor, square across, at X ≈ 100, 430 and 760 (three readings)."),
            ("C13", "Notch in each arch top (near the front wall)", "X0 / Z0", "centre of the notch",
             "X and Z of the notch centre, its width and how deep it goes."),
            ("L16", "Lid front-corner bracket", "–", "–", "See photo P4 (driver front corner)."),
            ("T17", "Round floor plugs", "X0 and Y0", "centre of each plug", "X, Y of each centre and the diameter."),
            ("L8", "Lid gas struts", "–", "–", "See photos P4 and P5."),
            ("L5", "Lid front member", "top of the tub rail", "underside of the lid", "Gap at each corner with the lid closed (L5).")]),
    "P2": ("p2-passenger-rear-corner.jpg", "Passenger rear corner (square on)",
           "Standing at the centreline, facing the passenger wall. The tailgate is to the LEFT, the cab to the right.", (1500, 2000),
           [("line", "C2", (290, 620, 290, 1700), (-120, -380)),
            ("box", "C2", (0, 560, 270, 1720), (-1, -1)),
            ("pt", "L15", (349, 1183), (-150, 120)), ("pt", "L15", (349, 1256), (-150, 120)),
            ("line", "L15", (470, 430, 350, 1130), (130, -120)),
            ("box", "F1", (553, 1060, 933, 1520), (0, 260)),
            ("box", "C8", (520, 1013, 993, 1573), (0, 0)),
            ("box", "C7", (1173, 907, 1253, 1667), (0, 0)),
            ("line", "C12", (507, 867, 1467, 867), (-330, -40)),
            ("pt", "L9", (587, 360), (-30, -90)), ("pt", "L9", (933, 427), (30, -90)),
            ("line", "L6", (600, 600, 1500, 600), (250, 30)),
            ("pt", "L6", (1200, 330), (60, 60)),
            ("pt", "L7", (400, 133), (120, 30)),
            ("datum", "Z0", (380, 1690, 1480, 1690), (300, 28))],
           [("C2", "Tail-light housing (P)", "X0 (front wall)", "the housing's front face, where it leaves the side wall (red line)",
             "At the floor, 270 high and just under the rail. Then how far it comes in: straight edge flat on the side wall FORWARD of "
             "the housing, measure square to it to the housing face, same three heights. Then Z of its bottom and top."),
            ("L15", "Lid rear stay", "Z0 / X0", "centre of each of the 2 bolts",
             "X and Z of both bolts; how far the bar stands off the wall at the bolts and at the top; bar width."),
            ("F1", "Factory 240 V outlet bezel", "X0 / Z0", "bezel edges", "X of the bezel's front and rear edges, Z of its top and bottom."),
            ("C8", "Outlet recess", "X0 / Z0", "edges of the recessed panel", "X front and rear, Z bottom and top, and how deep it is behind the wall face."),
            ("C7", "Vertical rib", "X0 / Z0", "rib centre", "X of the centre, width, how far it stands proud, Z where it stops."),
            ("C12", "Wall step (ledge line)", "Z0", "the step line", "Height of the step; then straight edge on the upper wall, measure in to the lower wall (step depth)."),
            ("L9", "Star-knob clamps", "X0, side wall, Z0", "each knob", "X of each; how far its tip is from the side wall; Z of its lowest point."),
            ("L6", "Lid side skirt (UTE MASTER plate) and the rail below it", "Z0 and the side wall", "lowest edge of each",
             "Z of the lowest edge of the skirt and of the aluminium rail; how far each stands in from the side wall."),
            ("L7", "Shackle / catch at the lid corner", "lid underside", "lowest point", "How far it hangs below the lid, X of its centre."),
            ("Z0", "Floor reference", "–", "–", "Heights from the rib tops (P1).")]),
    "P3": ("p3-passenger-rear-corner-up.jpg", "Passenger rear corner, looking up at the lid hardware",
           "Close to the passenger wall, looking up and back. Tailgate to the LEFT.", (1500, 2000),
           [("pt", "L7", (400, 400), (130, -40)),
            ("pt", "L9", (573, 813), (-60, -120)), ("pt", "L9", (893, 827), (40, -120)),
            ("line", "L15", (300, 820, 330, 1780), (-110, -200)),
            ("pt", "L15", (327, 1827), (130, 20)), ("pt", "L15", (327, 1920), (130, 20)),
            ("line", "L6", (733, 933, 1500, 920), (150, 50)),
            ("box", "C2", (0, 980, 130, 2000), (-1, -1)),
            ("line", "C12", (507, 1333, 960, 1307), (100, -40)),
            ("box", "C7", (920, 1400, 990, 2000), (0, 0))],
           [("L7", "Shackle / catch", "lid underside", "lowest point", "Hang depth and X."),
            ("L9", "Star knobs", "side wall", "knob tip", "As P2."),
            ("L15", "Rear stay", "lid corner (top) / bolts (bottom)", "–", "Top: X where it leaves the lid. Bottom: the 2 bolts (P2)."),
            ("L6", "Aluminium lid rail along the wall top", "side wall", "inner face of the rail", "How far in, and Z of its bottom edge."),
            ("C2", "Tail-light housing face", "–", "–", "As P2."),
            ("C12", "Wall step", "–", "–", "As P2."),
            ("C7", "Vertical rib", "–", "–", "As P2.")]),
    "P4": ("p4-driver-front-corner.jpg", "Driver front corner",
           "Inside the tub near the driver arch, looking forward and right. Front wall on the LEFT, driver side wall on the right.", (1500, 2000),
           [("line", "L16", (800, 590, 853, 990), (-170, -60)),
            ("pt", "L16", (853, 995), (-150, 60)),
            ("line", "C12", (1160, 990, 1500, 960), (-40, -50)),
            ("pt", "C13", (573, 1627), (130, 60)),
            ("pt", "W3", (900, 1300), (150, 0)),
            ("pt", "X0", (400, 1333), (-60, 60)),
            ("pt", "L8", (1267, 333), (-140, 40)),
            ("line", "L6", (1067, 600, 1500, 507), (0, 70))],
           [("L16", "Lid front-corner bracket (angle with a plastic hook)", "X0 / the side wall / Z0", "bracket edges and the hook's bottom",
             "How far it stands off the front wall, how far its outer edge is from the side wall, its width, and Z of the BOTTOM of the hook."),
            ("C12", "Wall step over the arch", "Z0", "step line", "Height at the front and at the back of the arch."),
            ("C13", "Arch notch", "X0 / Z0", "notch centre", "As P1."),
            ("W3", "Arch top", "Z0", "top of the arch", "Height at the front, middle and rear of its top (W3); note where the top steps."),
            ("X0", "Front wall raised panel", "–", "–", "The X = 0 face (P1)."),
            ("L8", "Gas strut, lower end", "X0 / Z0 / side wall", "the strut's lower pivot",
             "X, Z and distance from the side wall of BOTH strut ends (lid closed); strut diameter."),
            ("L6", "Lid rail along the wall top", "side wall", "inner face", "As P2.")]),
    "P5": ("p5-passenger-front-corner.jpg", "Passenger front corner",
           "Inside the tub near the passenger arch, looking forward and left. Front wall on the RIGHT.", (1500, 2000),
           [("line", "L16", (867, 440, 813, 933), (140, 60)),
            ("pt", "L16", (813, 945), (150, 80)),
            ("line", "C12", (0, 720, 667, 907), (60, -70)),
            ("pt", "C13", (590, 1700), (150, 40)),
            ("pt", "L8", (533, 400), (-120, 60)),
            ("line", "L6", (0, 320, 693, 507), (60, -70))],
           [("L16", "Lid front-corner bracket", "–", "–", "As P4."),
            ("C12", "Wall step", "–", "–", "As P2, passenger side."),
            ("C13", "Arch notch", "–", "–", "As P1."),
            ("L8", "Gas strut", "–", "–", "As P4, passenger side."),
            ("L6", "Lid rail", "–", "–", "As P2.")]),
}

COL = {"datum": "#1c7ed6", "dim": "#f59f00", "pt": "#e03131", "box": "#e03131", "line": "#e03131"}


def refs():
    """item id -> list of photo keys it is marked on (for the measurement tables)."""
    out = {}
    for k, (_, _, _, _, marks, _) in PHOTOS.items():
        for m in marks:
            out.setdefault(m[1], [])
            if k not in out[m[1]]:
                out[m[1]].append(k)
    return out


def _label(x, y, text, col):
    w = 18 + 13.5 * len(text)
    return (f'<rect x="{x - w / 2:.0f}" y="{y - 17:.0f}" width="{w:.0f}" height="34" rx="17" fill="{col}" stroke="#fff" stroke-width="2.5"/>'
            f'<text x="{x:.0f}" y="{y + 8:.0f}" font-size="23" font-weight="800" text-anchor="middle" fill="#fff">{escape(text)}</text>')


def svg(key):
    fn, title, where, (W, H), marks, _ = PHOTOS[key]
    w, h = round(W * SCALE), round(H * SCALE)
    s = SCALE
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%">',
         '<defs><marker id="pa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
         '<path d="M0,0 L10,5 L0,10 z" fill="#f59f00"/></marker></defs>',
         f'<image href="photos/{fn}" x="0" y="0" width="{w}" height="{h}"/>']
    for kind, iid, g, (dx, dy) in marks:
        c = COL[kind]
        if kind in ("datum", "dim", "line"):
            x1, y1, x2, y2 = (v * s for v in g)
            dash = ' stroke-dasharray="12 7"' if kind == "datum" else ""
            mk = ' marker-start="url(#pa)" marker-end="url(#pa)"' if kind == "dim" else ""
            o.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#000" stroke-opacity="0.55" stroke-width="7"/>'
                     f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{c}" stroke-width="4"{dash}{mk}/>')
            lx, ly = (x1 + x2) / 2 + dx * s, (y1 + y2) / 2 + dy * s
            if (dx, dy) != (0, 0):
                o.append(f'<line x1="{(x1 + x2) / 2:.0f}" y1="{(y1 + y2) / 2:.0f}" x2="{lx:.0f}" y2="{ly:.0f}" stroke="{c}" stroke-width="2"/>')
            o.append(_label(lx, ly, iid, c))
        elif kind == "box":
            x1, y1, x2, y2 = (v * s for v in g)
            o.append(f'<rect x="{x1:.0f}" y="{y1:.0f}" width="{x2 - x1:.0f}" height="{y2 - y1:.0f}" fill="none" stroke="#000" '
                     f'stroke-opacity="0.5" stroke-width="6"/><rect x="{x1:.0f}" y="{y1:.0f}" width="{x2 - x1:.0f}" height="{y2 - y1:.0f}" '
                     f'fill="none" stroke="{c}" stroke-width="3" stroke-dasharray="10 6"/>')
            if (dx, dy) != (-1, -1):
                o.append(_label((x1 + x2) / 2 + dx * s, y1 - 22 + dy * s, iid, c))
        else:
            x, y = g[0] * s, g[1] * s
            lx, ly = x + dx * s, y + dy * s
            o.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{lx:.0f}" y2="{ly:.0f}" stroke="#000" stroke-opacity="0.5" stroke-width="5"/>'
                     f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{lx:.0f}" y2="{ly:.0f}" stroke="{c}" stroke-width="2.5"/>'
                     f'<circle cx="{x:.0f}" cy="{y:.0f}" r="11" fill="{c}" stroke="#fff" stroke-width="3"/>')
            o.append(_label(lx, ly, iid, c))
    o.append("</svg>")
    return "".join(o)


def pages():
    """HTML pages (one per photo) for the measurement sheet."""
    out = []
    for key, (fn, title, where, (W, H), marks, legend) in PHOTOS.items():
        rows = "".join(f'<tr><td class="id">{escape(i)}</td><td><b>{escape(wh)}</b>'
                       + (f'<br><span class="ft">FROM</span> {escape(fr)} <span class="ft">TO</span> {escape(to)}' if fr != "–" else "")
                       + f'<br><span class="hw">{escape(how)}</span></td></tr>' for i, wh, fr, to, how in legend)
        land = W > H
        photo = f'<div class="pg-photo{" land" if land else ""}">{svg(key)}</div>'
        leg = f'<table class="pg-leg">{rows}</table>'
        if land:
            rl = [f'<tr><td class="id">{escape(i)}</td><td><b>{escape(wh)}</b>'
                  + (f'<br><span class="ft">FROM</span> {escape(fr)} <span class="ft">TO</span> {escape(to)}' if fr != "–" else "")
                  + f'<br><span class="hw">{escape(how)}</span></td></tr>' for i, wh, fr, to, how in legend]
            h = (len(rl) + 1) // 2
            leg = f'<div class="pg-two"><table class="pg-leg">{"".join(rl[:h])}</table><table class="pg-leg">{"".join(rl[h:])}</table></div>'
        body = photo + leg if land else f'<div class="pg-cols">{photo}<div>{leg}</div></div>'
        out.append(f'<div class="page"><h2>Photo {key} · {escape(title)}</h2><p class="where">{escape(where)}</p>{body}</div>')
    return out


def key_page():
    return """<div class="page"><h2>How to read the photo pages</h2>
<p>These are your photos (sent 2026-11-01), marked up. Each mark carries the item ID used in the tables later in this pack.</p>
<table class="pg-leg">
<tr><td><svg width="70" height="16"><line x1="2" y1="8" x2="68" y2="8" stroke="#1c7ed6" stroke-width="4" stroke-dasharray="12 7"/></svg></td>
<td><b>Blue dashed line: a reference (X0, Y0, Z0).</b> Every measurement starts from one of these three. Set them up first (photo P1).</td></tr>
<tr><td><svg width="70" height="16"><defs><marker id="pk" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#f59f00"/></marker></defs><line x1="6" y1="8" x2="64" y2="8" stroke="#f59f00" stroke-width="4" marker-start="url(#pk)" marker-end="url(#pk)"/></svg></td>
<td><b>Yellow arrow: measure from one end to the other</b>, exactly between the two points shown.</td></tr>
<tr><td><svg width="70" height="20"><circle cx="35" cy="10" r="8" fill="#e03131" stroke="#fff" stroke-width="2"/></svg></td>
<td><b>Red dot: a point to locate.</b> Give its X (from the front wall), Z (from the rib tops) and, where asked, how far it is from the side wall.</td></tr>
<tr><td><svg width="70" height="16"><line x1="2" y1="8" x2="68" y2="8" stroke="#e03131" stroke-width="4"/></svg></td>
<td><b>Red line: an edge to measure to</b> (a face, step or bar).</td></tr>
<tr><td><svg width="70" height="22"><rect x="4" y="3" width="62" height="16" fill="none" stroke="#e03131" stroke-width="3" stroke-dasharray="10 6"/></svg></td>
<td><b>Red dashed box: a feature to size</b>: its edges in X and Z, and how far it stands proud of (or recessed into) the wall.</td></tr>
</table>
<h3>Three rules that make the numbers usable</h3>
<ol><li><b>X</b> always from the front-wall straight edge (X0), along the tub. A laser is easiest: back of the laser on the straight edge,
aim at a card held on the point. <b>Y</b> always square off the centreline tape (Y0), or "from the side wall" where an item says so.
<b>Z</b> always up from the straight edge lying across the rib tops (Z0).</li>
<li>For "how far it stands in from the side wall": hold a straight edge flat on the side wall where it is flat (forward of the thing), and
measure square from the straight edge to the thing. Not from the bodywork outside, not from the liner's textured high spots.</li>
<li>Take a photo of the tape at each reading with the item ID written on masking tape in the shot. A photo of a reading beats a number.</li></ol>
<h3>Still to photograph</h3>
<ul><li>Driver rear corner, square on (as P2). Your photo of it came through in the chat but not as a file; please re-attach it as a file
so it can be marked up. It shows the C-shaped tie-down pocket (C11) and no outlet.</li>
<li>Each tail-light housing from the tailgate, looking forward along the side wall, with a straight edge on the wall: shows C1/C2 "in".</li>
<li>The outside shots you sent (rails, bars, tent latches, tail lights) are noted on the lid and tent items; re-send as files to mark up.</li></ul>
</div>"""


CSS = """
.where { color: #495057; margin: 0 0 2mm; font-size: 9pt; }
.pg-photo svg { display: block; border-radius: 1.5mm; }
.pg-photo.land svg { width: 100%; }
.pg-cols { display: grid; grid-template-columns: 108mm 1fr; gap: 4mm; align-items: start; }
table.pg-leg { width: 100%; border-collapse: collapse; margin-top: 2mm; font-size: 8.5pt; }
table.pg-leg td { border-bottom: 1px solid #dee2e6; padding: 1.3mm 1.2mm; vertical-align: top; }
table.pg-leg td.id { font-weight: 800; color: #c92a2a; white-space: nowrap; width: 10mm; }
.ft { font-size: 7pt; font-weight: 700; color: #fff; background: #495057; border-radius: 1mm; padding: 0 1mm; }
.hw { color: #343a40; }
.pg-two { display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; }
"""
