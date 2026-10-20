"""
Build the fit-out model and export:
    ../viewer/models/fitout_<state>.glb   coloured meshes for the web viewer + renders (Y-up, metres)
    out/fitout_fab.step                   fabricated parts only, stowed (travel) state
    out/summary.json                      key derived numbers
    out/cables.json                       routed cable polylines + anchors (wiring route map)
    ../bom/weight-budget-<ver>.csv        mass of every part (fixed fit-out vs payload)
    ../bom/cut-list-<ver>.csv             fabricated parts grouped by material
    ../bom/cable-schedule-<ver>.csv       every cable: from/to, size, protection, modelled length
    ../bom/cable-totals-<ver>.csv         purchase quantities per cable type

Usage:  ../.venv/bin/python build.py
"""
import csv
import json
import os
import sys
from collections import defaultdict

import cadquery as cq
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import params as P  # noqa: E402
from fitout import assembly  # noqa: E402
from fitout.core import C, MAT  # noqa: E402
from fitout.slides import slide_extent  # noqa: E402

OUT = os.path.join(HERE, "out")
VIEWER = os.path.join(HERE, "..", "viewer", "models")
BOM = os.path.join(HERE, "..", "bom")
for d in (OUT, VIEWER, BOM):
    os.makedirs(d, exist_ok=True)
V = P.VERSION

# CAD frame (Z up, mm) -> glTF frame (Y up, m)
TO_GL = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float)
TO_GL[:3, :3] *= 0.001
METAL = {"alu", "alu_dark", "runner", "ltrack", "solar_frame", "copper", "receiver"}
NOT_FITOUT = {"vehicle", "markers", "future", "payload", "well_filler", "modules"}
# alternatives modelled for comparison: not counted in the fit-out or payload totals
OPTIONS = {"well_filler": "option: well filler (no fridge)", "modules": "option: example edge modules"}


def material(rgba, metal=False):
    r, g, b, a = rgba
    lin = [((c / 255 + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]   # sRGB -> linear (glTF)
    return trimesh.visual.material.PBRMaterial(
        baseColorFactor=lin + [a / 255], metallicFactor=0.6 if metal else 0.0,
        roughnessFactor=0.45 if metal else 0.75, alphaMode="BLEND" if a < 255 else "OPAQUE", doubleSided=a < 255)


def mesh_of(p):
    if p.tube:
        meshes = []
        pts = [np.array(q, dtype=float) for q in p.tube]
        for a, b in zip(pts[:-1], pts[1:]):
            meshes.append(trimesh.creation.cylinder(radius=p.tube_r, segment=[a, b], sections=10))
        for q in pts:
            s = trimesh.creation.icosphere(subdivisions=1, radius=p.tube_r)
            s.apply_translation(q)
            meshes.append(s)
        m = trimesh.util.concatenate(meshes)
    else:
        verts, tris = p.shape.tessellate(0.6, 0.35)
        m = trimesh.Trimesh(np.array([v.toTuple() for v in verts]), np.array(tris), process=False)
    key = next((k for k, v in C.items() if v == p.color), "")
    m.visual = trimesh.visual.TextureVisuals(material=material(p.color, key in METAL))
    return m


def export_glb(state):
    parts, cables = assembly.build(state)
    scene = trimesh.Scene()
    for p in parts:
        scene.add_geometry(mesh_of(p), node_name=f"{p.group}__{p.name}", geom_name=f"{p.group}__{p.name}")
    scene.apply_transform(TO_GL)
    path = os.path.join(VIEWER, f"fitout_{state}.glb")
    scene.export(path, include_normals=True)
    print(f"wrote {path} ({os.path.getsize(path)/1e6:.1f} MB, {len(parts)} parts)")
    return parts, cables


def export_step(parts):
    asm = cq.Assembly(name="tasman_fitout_fab")
    for p in parts:
        if p.fab and p.shape is not None:
            r, g, b, a = p.color
            asm.add(p.shape, name=p.name, color=cq.Color(r / 255, g / 255, b / 255, a / 255))
    path = os.path.join(OUT, "fitout_fab.step")
    asm.export(path)
    print(f"wrote {path}")


def write_csv(name, header, rows):
    path = os.path.join(BOM, name)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {path} ({len(rows)} rows)")


def weight_budget(parts):
    rows, by_group = [], defaultdict(float)
    for p in parts:
        if p.group in ("vehicle", "markers", "future") or p.tube:
            continue
        m = p.mass
        if m <= 0:
            continue
        cls = OPTIONS.get(p.group) or ("payload (example)" if p.group in ("payload", "lid_cargo") else "fit-out")
        rows.append([cls, p.group, p.name, p.mat or "purchased", round(m, 2)])
        by_group[(cls, p.group)] += m
    # cable mass from the schedule (approx kg/m by size)
    return rows, by_group


CABLE_KGM = {"120": 1.2, "70": 0.70, "50": 0.50, "25": 0.27 * 2, "16": 0.18 * 2, "6": 0.07 * 2, "4": 0.05 * 2, "2.5x3": 0.12, "data": 0.04}


def cable_outputs(cables):
    rows, totals = [], defaultdict(float)
    kg = 0.0
    for c in cables:
        L = c.length_m()
        mult = 2 if c.spec.startswith("2 x") else 1
        rows.append([c.cid, c.circuit, c.side, c.frm, c.to, c.spec, c.protection, L * mult, c.notes])
        totals[c.spec] += L * mult
        kg += CABLE_KGM[c.size] * L * mult
    write_csv(f"cable-schedule-{V}.csv", ["id", "circuit", "harness", "from", "to", "cable", "protection", "length_m (model +10%)", "notes"], rows)
    write_csv(f"cable-totals-{V}.csv", ["cable", "total_m (model)", "buy_m (+15%, rounded up)"],
              [[k, round(v, 1), int(np.ceil(v * 1.15))] for k, v in sorted(totals.items())])
    return kg


def cut_list(parts):
    groups = defaultdict(list)
    for p in parts:
        if not (p.fab and p.mat and p.shape is not None):
            continue
        m = MAT[p.mat]
        d = p.bbox_dims
        size = f"{d[0]:.0f}" if m["kind"] == "linear" else f"{d[0]:.0f} x {d[1]:.0f}"
        groups[(p.mat, size)].append(p.name)
    rows = []
    for (mat, size), names in sorted(groups.items()):
        rows.append([mat, size, len(names), MAT[mat]["stock"], "; ".join(sorted(names))])
    write_csv(f"cut-list-{V}.csv", ["material", "cut size (mm)", "qty", "stock", "parts"], rows)
    # stock estimate per material
    need = defaultdict(float)
    for (mat, size), names in groups.items():
        dims = [float(v) for v in size.split(" x ")]
        need[mat] += (dims[0] / 1000 if len(dims) == 1 else dims[0] * dims[1] / 1e6) * len(names)
    return {k: round(v, 2) for k, v in need.items()}


def axle_loads(parts):
    """Split every mass between the axles by its X position (simple beam). Returns kg added per axle."""
    xr = P.REAR_AXLE_X
    xf = xr - P.WHEELBASE

    def split(m, x):
        r = (x - xf) / P.WHEELBASE
        return m * (1 - r), m * r
    out = defaultdict(lambda: [0.0, 0.0])
    for p in parts:
        if p.group in ("vehicle", "markers", "future") or p.group in OPTIONS or p.tube or p.mass <= 0:
            continue
        bb = p.shape.BoundingBox()
        f, r = split(p.mass, (bb.xmin + bb.xmax) / 2)
        key = "payload (example)" if p.group in ("payload", "lid_cargo") else "fit-out"
        out[key][0] += f
        out[key][1] += r
    # occupants + accessories (estimates, for the GVM / axle check)
    for name, m, x in (("4 adults (2 front, 2 rear)", 320, None), ("bull bar (est)", 75, -3900), ("tow bar (est)", 30, P.TUB_L + 250)):
        if x is None:
            f1, r1 = split(160, -2050)
            f2, r2 = split(160, -1150)
            out[name] = [f1 + f2, r1 + r2]
        else:
            out[name] = list(split(m, x))
    return {k: [round(v[0], 1), round(v[1], 1)] for k, v in out.items()}


if __name__ == "__main__":
    travel, cables = export_glb("travel")
    camp, _ = export_glb("camp")
    export_step(travel)
    rows, by_group = weight_budget(travel)
    cable_kg = cable_outputs(cables)
    # routed cable polylines (travel state) for the wiring route map in docs/wiring
    from fitout.core import ANCHORS
    open(os.path.join(OUT, "cables.json"), "w").write(json.dumps(dict(
        version=V, cables=[dict(id=c.cid, circuit=c.circuit, frm=c.frm, to=c.to, size=c.size, spec=c.spec, protection=c.protection,
                                side=c.side, colour=c.colour, length_m=c.length_m(), notes=c.notes,
                                via=[q if isinstance(q, str) else None for q in c.path],
                                points=[[round(v, 1) for v in q] for q in c.points(k)]) for k, c in enumerate(cables)],
        anchors={k: [round(float(v), 1) for v in xyz] for k, xyz in ANCHORS.items()}), indent=0))
    rows.append(["fit-out", "wiring", "all cables (from schedule)", "cable", round(cable_kg, 1)])
    by_group[("fit-out", "wiring")] += cable_kg
    write_csv(f"weight-budget-{V}.csv", ["class", "group", "item", "material", "kg"], rows)
    stock = cut_list(travel)
    fit = sum(v for (c, g), v in by_group.items() if c == "fit-out")
    pay = sum(v for (c, g), v in by_group.items() if c == "payload (example)")
    opts = {c: round(sum(v for (c2, g), v in by_group.items() if c2 == c), 1) for c in OPTIONS.values()}
    summary = dict(
        version=V,
        fitout_kg=round(fit, 1), example_payload_kg=round(pay, 1), options_kg=opts,
        by_group_kg={g: round(v, 1) for (c, g), v in sorted(by_group.items())},
        slide_deck_top_z=round(P.DECK_TOP_Z, 1), clear_above_deck=round(P.UNDER_LID_Z - P.DECK_TOP_Z, 1),
        deck_widths=[round(abs(b - a), 1) for a, b in (slide_extent('p'), slide_extent('d'))], slide_length=P.SLIDE_L, slide_travel=P.SLIDE_EXT,
        tent_gap=P.TENT_GAP, solar_w=sum(p.meta.get("watts", 0) for p in travel),
        cable_count=len(cables), cable_total_m=round(sum(c.length_m() for c in cables), 1),
        material_need=stock,
        lid_load_kg=round(sum(p.mass for p in travel if p.group in ("tent", "rack", "tent_services", "lid_storage", "lid_cargo")
                              or p.name.startswith("tent_solar")), 1),
        lid_dynamic_rating_kg=P.LID_DYNAMIC_KG,
        roof_load_kg=round(sum(p.mass for p in travel if p.group in ("roof", "cargo", "visor")
                               or (p.group == "solar" and not p.name.startswith("tent_solar"))), 1),
        roof_dynamic_rating_kg=P.ROOF_DYNAMIC_KG,
        axle_added_kg_front_rear=axle_loads(travel),   # driving: slides stowed
    )
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
