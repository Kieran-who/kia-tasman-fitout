"""Shared types, colours, materials and geometry helpers."""
from __future__ import annotations

from dataclasses import dataclass, field

import cadquery as cq

# ------------------------------------------------------------------ colours (sRGB 0-255, alpha)
C = dict(
    body=(201, 191, 163, 255), trim=(40, 40, 42, 255), tyre=(25, 25, 25, 255),
    liner=(44, 44, 46, 255), liner_rib=(56, 56, 58, 255), glass=(60, 70, 80, 200),
    lid=(30, 30, 32, 255), rail=(20, 20, 22, 255), rack=(15, 15, 15, 255),
    tent=(22, 22, 22, 255), tent_base=(45, 45, 45, 255), tent_rail=(55, 55, 58, 255),
    alu=(190, 194, 198, 255), alu_dark=(120, 124, 128, 255), ply=(214, 182, 134, 255),
    ply_edge=(190, 155, 110, 255), uhmw=(235, 235, 235, 255),
    runner=(150, 155, 160, 255), battery=(30, 32, 35, 255), battery_accent=(240, 120, 20, 255),
    victron=(0, 92, 170, 255), victron_dark=(20, 40, 70, 255), fuse=(200, 40, 40, 255),
    copper=(196, 120, 60, 255), outlet=(240, 240, 240, 255), anderson=(210, 30, 30, 255),
    anderson_grey=(130, 130, 130, 255), usb=(20, 20, 20, 255),
    solar=(20, 35, 75, 255), solar_frame=(170, 175, 180, 255), light=(250, 250, 240, 255),
    starlink=(235, 235, 235, 255), chain=(60, 60, 60, 255), receiver=(170, 172, 176, 255),
    hole=(25, 25, 25, 255), ltrack=(170, 175, 180, 255), cover=(90, 95, 100, 70),
    kia_outlet=(255, 90, 0, 255), marker=(255, 0, 140, 255), ghost=(80, 170, 255, 60),
    payload=(120, 160, 120, 255), payload_dark=(70, 90, 70, 255), fridge=(225, 225, 220, 255),
    strap=(230, 160, 20, 255),
    # cable colours
    w_pos=(200, 30, 30, 255), w_neg=(25, 25, 25, 255), w_ac=(245, 130, 30, 255),
    w_pv=(250, 200, 30, 255), w_data=(40, 120, 220, 255), w_12v=(220, 70, 70, 255),
    w_tent=(160, 80, 200, 255),
)

# ------------------------------------------------------------------ materials
# kind: "linear" (kg/m along the longest bbox side), "sheet" (kg/m2 over the two largest sides),
#       "solid" (kg/mm3 * volume).  stock = purchase length/size for the cutting list.
MAT = {
    "RHS 75x25x2 6060": dict(kind="linear", kgm=1.04, stock="6.5 m length"),
    "RHS 50x25x2 6060": dict(kind="linear", kgm=0.77, stock="6.5 m length"),
    "SHS 30x30x2 6060": dict(kind="linear", kgm=0.61, stock="6.5 m length"),
    "SHS 40x40x2 6060": dict(kind="linear", kgm=0.82, stock="6.5 m length"),
    "Angle 50x50x5 6060": dict(kind="linear", kgm=1.28, stock="6.5 m length"),
    "Angle 30x30x3 6060": dict(kind="linear", kgm=0.47, stock="6.5 m length"),
    "Angle 60x40x3 6060": dict(kind="linear", kgm=0.79, stock="6.5 m length"),
    "Flat 50x6 6060": dict(kind="linear", kgm=0.81, stock="6.5 m length"),
    "Flat 60x6 6060": dict(kind="linear", kgm=0.97, stock="6.5 m length"),
    "Plate 3 5052": dict(kind="sheet", kgm2=8.1, stock="2400x1200 sheet"),
    "Plate 4 5052": dict(kind="sheet", kgm2=10.8, stock="2400x1200 sheet"),
    "Plate 6 5052": dict(kind="sheet", kgm2=16.2, stock="2400x1200 sheet"),
    "Sheet 1.6 5005": dict(kind="sheet", kgm2=4.3, stock="2400x1200 sheet"),
    "Ply 18 marine": dict(kind="sheet", kgm2=10.3, stock="2400x1200 sheet"),
    "Ply 15 marine": dict(kind="sheet", kgm2=8.6, stock="2400x1200 sheet"),
    "Ply 12 marine": dict(kind="sheet", kgm2=6.9, stock="2400x1200 sheet"),
    "Ply 9 marine": dict(kind="sheet", kgm2=5.2, stock="2400x1200 sheet"),
    "ACM 3": dict(kind="sheet", kgm2=4.5, stock="2440x1220 sheet"),
    "UHMW 10": dict(kind="sheet", kgm2=9.4, stock="1000x500 sheet"),
    "L-track HD": dict(kind="linear", kgm=0.75, stock="1.2 m length"),
}


@dataclass
class Part:
    name: str
    group: str
    shape: cq.Shape | None = None
    color: tuple = (200, 200, 200, 255)
    tube: list | None = None          # polyline (cables) - GLB only
    tube_r: float = 6.0
    fab: bool = False                 # fabricated by the builder -> STEP + cut list
    mat: str | None = None            # key into MAT for fabricated parts
    kg: float | None = None           # purchased component mass
    meta: dict = field(default_factory=dict)

    @property
    def bbox_dims(self):
        bb = self.shape.BoundingBox()
        return sorted((bb.xlen, bb.ylen, bb.zlen), reverse=True)

    @property
    def mass(self) -> float:
        if self.kg is not None:
            return self.kg
        if self.mat and self.shape is not None:
            m = MAT[self.mat]
            d = self.bbox_dims
            if m["kind"] == "linear":
                return m["kgm"] * d[0] / 1000
            if m["kind"] == "sheet":
                # use the true face area (volume / thickness) so cut-outs count
                return m["kgm2"] * (self.shape.Volume() / max(d[2], 0.1)) / 1e6
            return m["kgmm3"] * self.shape.Volume()
        return 0.0


# ------------------------------------------------------------------ geometry helpers
def box(x0, x1, y0, y1, z0, z1) -> cq.Workplane:
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def tube_box(x0, x1, y0, y1, z0, z1, wall=2.0, axis="X") -> cq.Workplane:
    """Hollow rectangular section running along `axis` (RHS / SHS)."""
    outer = box(x0, x1, y0, y1, z0, z1)
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    w = wall
    if axis == "X":
        inner = box(x0 - 1, x1 + 1, y0 + w, y1 - w, z0 + w, z1 - w)
    elif axis == "Y":
        inner = box(x0 + w, x1 - w, y0 - 1, y1 + 1, z0 + w, z1 - w)
    else:
        inner = box(x0 + w, x1 - w, y0 + w, y1 - w, z0 - 1, z1 + 1)
    return outer.cut(inner)


def angle_x(x0, x1, y_corner, z_corner, leg=50, t=5, ydir=1, zdir=1) -> cq.Workplane:
    """Equal angle running along X with its corner at (y_corner, z_corner)."""
    a = box(x0, x1, y_corner, y_corner + ydir * leg, z_corner, z_corner + zdir * t)
    b = box(x0, x1, y_corner, y_corner + ydir * t, z_corner, z_corner + zdir * leg)
    return a.union(b)


def cyl(r, h, centre, axis="Z") -> cq.Workplane:
    w = cq.Workplane("XY").circle(r).extrude(h).translate((0, 0, -h / 2))
    if axis == "X":
        w = w.rotate((0, 0, 0), (0, 1, 0), 90)
    elif axis == "Y":
        w = w.rotate((0, 0, 0), (1, 0, 0), 90)
    return w.translate(centre)


def ring(r_out, r_in, h, centre, axis="Z"):
    return cyl(r_out, h, centre, axis).cut(cyl(r_in, h + 2, centre, axis))


def prof_xz(points, y0, y1) -> cq.Workplane:
    return cq.Workplane("XZ", origin=(0, y1, 0)).polyline(points).close().extrude(y1 - y0)


def prof_yz(points, x0, x1) -> cq.Workplane:
    return cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(points).close().extrude(x1 - x0)


def S(w) -> cq.Shape:
    if isinstance(w, cq.Shape):
        return w
    vals = w.vals()
    return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)


def part(name, group, w, color, fab=False, mat=None, kg=None, **meta) -> Part:
    col = C[color] if isinstance(color, str) else color
    return Part(name, group, S(w), col, fab=fab, mat=mat, kg=kg, meta=meta)


def union_all(ws):
    out = None
    for w in ws:
        out = w if out is None else out.union(w)
    return out


# anchors other modules (wiring) can look up: name -> (x, y, z)
ANCHORS: dict[str, tuple] = {}


def anchor(name, xyz):
    ANCHORS[name] = tuple(float(v) for v in xyz)
    return ANCHORS[name]
