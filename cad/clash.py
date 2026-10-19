"""Interference check: reports solid parts that intersect each other (or the tub) by more than 1 cm3."""
import sys
import os
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fitout import assembly  # noqa: E402

SKIP_GROUPS = {"markers", "future"}
SKIP_NAMES = ("_pin_", "receiver", "ltrack_pockets", "_band", "strap", "cab_body", "cab_glass", "wheel_", "chassis_rail",
              "tub_underside", "tub_skin", "rear_bumper", "roof_rail", "tub_rail", "tub_floor")
# intentional contacts (mounted to / sitting in each other)
ALLOW = [("_deck", "_ltrack"), ("_deck", "_receiver"), ("bulkhead", "_gpo"), ("bulkhead", "_anderson"), ("bulkhead", "_12v"),
         ("bulkhead", "_usbc"), ("_runner_", "_runner_"), ("battery_", "battery_"), ("tent_", "tent_"), ("rack_", "rack_"),
         ("ut_drawer", "ut_drawer"), ("lid", "lid_"), ("plat_", "plat_"), ("cargo_", "cargo_"), ("pc_", "pc_"),
         ("_fridge_well_pan", "_well_track"), ("chain_bracket", "cable_chain"), ("bay_", "bay_"), ("_carr_", "_carr_"),
         ("_side_angle", "_base_"), ("_carr_cross", "_deck"), ("isolator", "isolator"), ("quattro", "inverter"),
         ("charge_board", "charge_board"), ("ut_", "ut_"), ("_leg_", "_leg_"), ("plat_fairing", "light_bar"),
         ("_rear_plate", "_carr_side"), ("_rear_plate", "_handle"), ("_deck", "_handle"), ("cable_chain", "chain_trough"),
         ("_runner_plate", "_base_plate"), ("_base_cross", "_base_plate"), ("pc_outlet_panel", "pc_"), ("_well_track", "fridge"), ("power_pod", "_gpo"), ("power_pod", "_anderson"), ("power_pod", "_12v"), ("power_pod", "_usbc"), ("microwave", "microwave_door"), ("_front", "_pull"), ("bed_hook", "ud_")]


def allowed(a, b):
    return any((x in a and y in b) or (x in b and y in a) for x, y in ALLOW)


def run(state):
    parts, _ = assembly.build(state)
    solids = [p for p in parts if p.shape is not None and not p.tube and p.group not in SKIP_GROUPS
              and not any(s in p.name for s in SKIP_NAMES)]
    boxes = [p.shape.BoundingBox() for p in solids]
    hits = []
    for (i, a), (j, b) in combinations(enumerate(solids), 2):
        ba, bb = boxes[i], boxes[j]
        if ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin or bb.ymax < ba.ymin or ba.zmax < bb.zmin or bb.zmax < ba.zmin:
            continue
        if allowed(a.name, b.name):
            continue
        try:
            v = a.shape.intersect(b.shape).Volume()
        except Exception:
            continue
        if v > 1000:
            hits.append((v / 1000, a.name, b.name))
    hits.sort(reverse=True)
    print(f"[{state}] {len(hits)} clashes > 1 cm3")
    for v, a, b in hits[:60]:
        print(f"  {v:9.1f} cm3  {a}  x  {b}")
    return hits


if __name__ == "__main__":
    for st in sys.argv[1:] or ["travel", "camp"]:
        run(st)
