"""Cable route check: reports where a routed cable passes through a solid part (sampled every 5 mm).

The first and last 40 mm of each cable are ignored (that is where it lands on its terminal). Vehicle body solids that are
only rough envelopes (tub underside, cab shell, chassis) are skipped, as in clash.py.
Usage:  ../.venv/bin/python cable_check.py [travel|camp]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from OCP.BRepClass3d import BRepClass3d_SolidClassifier  # noqa: E402
from OCP.gp import gp_Pnt  # noqa: E402
from OCP.TopAbs import TopAbs_IN  # noqa: E402

from clash import SKIP_GROUPS, SKIP_NAMES  # noqa: E402
from fitout import assembly  # noqa: E402

STEP = 2.5
END = 40.0
# parts cables are meant to pass through or lie in (glands, grommets, ducts, the chain itself, conduits)
PASS = ("gland", "grommet", "_duct", "cable_chain", "conduit", "chain_tray", "cable_tray", "bulkhead", "power_pod", "window",
        "clip", "gap_junction_box", "compute_box", "compute_inlet", "lugs", "terminals", "_studs", "label", "boot", "chain_bracket",
        "factory_outlet", "visor_controller_box", "mppt_visor")
# openings that exist on the vehicle but aren't cut in the model: (part, x0, x1, y0, y1, z0, z1)
WINDOWS = [("tub_wall_passenger", 1265, 1395, -900, -780, 350, 450),          # factory 240 V outlet hole -> gland plate
           ("plat_end_", -195, -145, -700, 40, 1025, 1075)]                    # grommeted holes into the end member


def samples(pts):
    out = []
    total = 0.0
    segs = []
    for a, b in zip(pts[:-1], pts[1:]):
        L = sum((u - v) ** 2 for u, v in zip(a, b)) ** 0.5
        segs.append((a, b, L))
        total += L
    s = 0.0
    for a, b, L in segs:
        n = max(1, int(L / STEP))
        for i in range(n):
            t = i / n
            d = s + t * L
            if END < d < total - END:
                out.append(tuple(u + (v - u) * t for u, v in zip(a, b)))
        s += L
    return out


def run(state="travel"):
    parts, cables = assembly.build(state)
    solids = [p for p in parts if p.shape is not None and not p.tube and p.group not in SKIP_GROUPS
              and not any(s in p.name for s in SKIP_NAMES) and not any(s in p.name for s in PASS)]
    shp = [(p, p.shape.val() if hasattr(p.shape, "val") else p.shape) for p in solids]
    bbs = [(p, s, s.BoundingBox()) for p, s in shp]
    hits = {}
    tubes = [p for p in parts if p.tube and p.name.startswith("cable_")]
    for t in tubes:
        for q in samples(t.tube):
            for p, s, bb in bbs:
                if not (bb.xmin - 1 <= q[0] <= bb.xmax + 1 and bb.ymin - 1 <= q[1] <= bb.ymax + 1 and bb.zmin - 1 <= q[2] <= bb.zmax + 1):
                    continue
                if any(w[0] in p.name and w[1] <= q[0] <= w[2] and w[3] <= q[1] <= w[4] and w[5] <= q[2] <= w[6] for w in WINDOWS):
                    continue
                c = BRepClass3d_SolidClassifier(s.wrapped, gp_Pnt(*q), 0.5)
                if c.State() == TopAbs_IN:
                    hits.setdefault((t.name[6:], p.name), []).append(q)
    print(f"[{state}] {len(hits)} cable/part intersections")
    for (cid, pn), qs in sorted(hits.items(), key=lambda kv: -len(kv[1])):
        q = qs[len(qs) // 2]
        print(f"  {cid:5s} x {pn:38s} {len(qs) * STEP:6.0f} mm  e.g. ({q[0]:.0f}, {q[1]:.0f}, {q[2]:.0f})")
    return hits


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "travel")
