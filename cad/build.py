"""
Build the fit-out model and export:
    ../viewer/models/fitout_<state>.glb - coloured meshes for the web viewer + renders (Y-up, metres)
    out/fitout_fab.step      - fabricated parts only (for CAD / CNC hand-off)
    out/summary.json         - derived numbers (volumes, clearances) used by the docs

Usage:  ../.venv/bin/python build.py
"""
import json
import os
import sys

import cadquery as cq
import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(__file__))
import model  # noqa: E402
import params as P  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "out")
VIEWER = os.path.join(os.path.dirname(__file__), "..", "viewer", "models")
os.makedirs(OUT, exist_ok=True)
os.makedirs(VIEWER, exist_ok=True)

# CAD frame (Z up, mm) -> glTF frame (Y up, m)
TO_GL = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float)
TO_GL[:3, :3] *= 0.001


def material(rgba, metal=False):
    r, g, b, a = rgba
    lin = [((c / 255 + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]   # sRGB -> linear (glTF spec)
    return trimesh.visual.material.PBRMaterial(
        baseColorFactor=lin + [a / 255],
        metallicFactor=0.6 if metal else 0.0,
        roughnessFactor=0.45 if metal else 0.75,
        alphaMode="BLEND" if a < 255 else "OPAQUE",
        doubleSided=a < 255,
    )


METAL = {"alu", "alu_dark", "runner", "ltrack", "solar_frame", "copper"}


def mesh_of(p: model.Part):
    if p.tube:
        meshes = []
        pts = [np.array(q, dtype=float) for q in p.tube]
        for a, b in zip(pts[:-1], pts[1:]):
            meshes.append(trimesh.creation.cylinder(radius=p.tube_r, segment=[a, b], sections=12))
        for q in pts:
            s = trimesh.creation.icosphere(subdivisions=1, radius=p.tube_r)
            s.apply_translation(q)
            meshes.append(s)
        m = trimesh.util.concatenate(meshes)
    else:
        verts, tris = p.shape.tessellate(0.8, 0.4)
        m = trimesh.Trimesh(np.array([v.toTuple() for v in verts]), np.array(tris), process=False)
    colour_key = next((k for k, v in model.C.items() if v == p.color), "")
    m.visual = trimesh.visual.TextureVisuals(material=material(p.color, colour_key in METAL))
    return m


def export_glb(state):
    parts = model.build(state)
    scene = trimesh.Scene()
    for p in parts:
        scene.add_geometry(mesh_of(p), node_name=f"{p.group}__{p.name}", geom_name=f"{p.group}__{p.name}")
    scene.apply_transform(TO_GL)
    path = os.path.join(VIEWER, f"fitout_{state}.glb")
    scene.export(path, include_normals=True)
    print(f"wrote {path} ({os.path.getsize(path)/1e6:.1f} MB, {len(parts)} parts)")
    return parts


def export_step(parts):
    asm = cq.Assembly(name="tasman_fitout_fab")
    for p in parts:
        if p.fab and p.shape is not None:
            r, g, b, a = p.color
            asm.add(p.shape, name=p.name, color=cq.Color(r / 255, g / 255, b / 255, a / 255))
    path = os.path.join(OUT, "fitout_fab.step")
    asm.export(path)
    print(f"wrote {path}")


def summary(parts):
    d = {}
    for p in parts:
        if "gross_litres" in p.meta:
            d["water_tank_gross_litres"] = p.meta["gross_litres"]
    d["slide_deck_top_z"] = P.DECK_TOP_Z
    d["clear_height_above_slide_deck"] = P.TUB_D + P.LID_CLEAR - P.DECK_TOP_Z
    d["carriage_width"] = round(P.CARRIAGE_W, 1)
    d["cassette_width"] = round(P.CASSETTE_W, 1)
    d["slide_length"] = P.SLIDE_L
    d["slide_extension"] = P.SLIDE_EXT
    d["side_pocket_width"] = P.POCKET_W
    d["side_pocket_length"] = P.POCKET_X1 - P.POCKET_X0
    d["solar_watts_placeholder"] = sum(p.meta.get("watts", 0) for p in parts)
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(d, f, indent=2)
    print(json.dumps(d, indent=2))


if __name__ == "__main__":
    export_glb("travel")
    parts = export_glb("camp")
    export_step(parts)
    summary(parts)
