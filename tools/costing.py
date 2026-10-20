"""
Parts cost for the current version.

Prices every line of bom/product-list-<ver>.csv, then adds the cable (bom/cable-totals-<ver>.csv) and the raw
material for the fabricated parts (cad/out/summary.json material_need) at the rates in bom/cost-rates.csv. Writes:
    bom/cost-summary-<ver>.csv   one line per product, cable and material, with the price type and source
    bom/cost-history.csv         one total per version (the running total)
    bom/cost-by-stage-<ver>.csv  the same total split over the build stages (bom/stages.csv)
    README.md                    the block between <!-- cost:start --> and <!-- cost:end -->
    docs/build-stages.md         the block between <!-- stages:start --> and <!-- stages:end -->

Stages: each product line names its stage(s) in the `stage` column ("3", or "1:2,3:1" to split the qty). Cable is
split by cable ID and raw material by model group, both through bom/stage-map.csv; the two lump sums follow the cable
and material they belong to.

Product-list price types: actual (seen on a retailer / maker page, URL in `source`), estimate, owned (already owned,
not counted), in cables / in materials (counted in those sections instead, so not counted twice).

Usage:  python3 tools/costing.py
"""
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad"))
import params as P  # noqa: E402

V = P.VERSION
LINEAR_WASTE = 1.2      # cut-to-length offcuts
SHEET_WASTE = 1.25      # nesting losses before rounding up to whole sheets
COUNTED = ("actual", "estimate")


def money(x):
    return f"{x:,.0f}"


def stage_split(spec, qty):
    """'3' -> {3: 1.0}; '1:2,3:1' -> qty shares; '-' -> {} (not counted)."""
    if spec.strip() == "-":
        return {}
    if ":" not in spec:
        return {int(spec): 1.0}
    parts = {int(s): float(q) for s, q in (x.split(":") for x in spec.split(","))}
    assert abs(sum(parts.values()) - qty) < 1e-6, f"stage split {spec} != qty {qty}"
    return {s: q / qty for s, q in parts.items()}


def stage_map():
    m = {(r["kind"], r["key"]): int(r["stage"]) for r in csv.DictReader(open(ROOT / "bom/stage-map.csv"))}
    return m


def shares(d):
    tot = sum(d.values())
    return {k: v / tot for k, v in d.items()} if tot else {}


def lump_shares(rows):
    by = defaultdict(float)
    for r in rows:
        for s, f in r["stages"].items():
            by[s] += f * r["line_aud"]
    return shares(by)


def products():
    rows = []
    for r in csv.DictReader(open(ROOT / f"bom/product-list-{V}.csv")):
        kind = r["price"]
        qty, unit = float(r["qty"]), float(r["unit AUD inc GST"] or 0)
        line = qty * unit if kind in COUNTED else 0.0
        rows.append(dict(section="products", group=r["system"], item=r["item"], qty=qty, unit="ea", unit_aud=unit,
                         line_aud=round(line, 2), price=kind, source=r["source"], stages=stage_split(r["stage"], qty)))
    return rows


def rates():
    return {(r["kind"], r["key"]): r for r in csv.DictReader(open(ROOT / "bom/cost-rates.csv"))}


def cables(rt, sm):
    by_spec = defaultdict(lambda: defaultdict(float))
    for r in csv.DictReader(open(ROOT / f"bom/cable-schedule-{V}.csv")):
        by_spec[r["cable"]][sm[("cable", r["id"])]] += float(r["length_m (model +10%)"])
    rows = []
    for r in csv.DictReader(open(ROOT / f"bom/cable-totals-{V}.csv")):
        k = rt[("cable", r["cable"])]
        m = float(r["buy_m (+15%, rounded up)"])
        unit = float(k["aud_inc_gst"])
        rows.append(dict(section="cable", group="cable", item=r["cable"], qty=m, unit="m", unit_aud=unit,
                         line_aud=round(m * unit, 2) if k["price"] in COUNTED else 0.0, price=k["price"], source=k["source"],
                         stages=shares(by_spec[r["cable"]])))
    k = rt[("lump", "Cable terminations")]
    rows.append(dict(section="cable", group="cable", item="Cable terminations", qty=1, unit="lot", unit_aud=float(k["aud_inc_gst"]),
                     line_aud=float(k["aud_inc_gst"]), price=k["price"], source=k["source"], stages=lump_shares(rows)))
    return rows


def material_groups(sm):
    """Share of each material's quantity by stage, from the cut list (part -> model group -> stage)."""
    grp = {r["item"]: r["group"] for r in csv.DictReader(open(ROOT / f"bom/weight-budget-{V}.csv"))}
    by = defaultdict(lambda: defaultdict(float))
    for r in csv.DictReader(open(ROOT / f"bom/cut-list-{V}.csv")):
        dims = [float(x) for x in r["cut size (mm)"].split(" x ")]
        q = dims[0] if len(dims) == 1 else dims[0] * dims[1]
        for name in r["parts"].split("; "):
            by[r["material"]][sm[("group", grp[name])]] += q
    return {m: shares(d) for m, d in by.items()}


def materials(rt, sm):
    rows = []
    split = material_groups(sm)
    need = json.load(open(ROOT / "cad/out/summary.json"))["material_need"]
    for mat, q in sorted(need.items()):
        k = rt[("material", mat)]
        unit = float(k["aud_inc_gst"])
        if k["unit"] == "sheet":
            n, u = math.ceil(q * SHEET_WASTE / float(k["sheet_m2"])), "sheet"
        else:
            n, u = round(q * LINEAR_WASTE, 1), "m"
        rows.append(dict(section="materials", group="materials", item=mat, qty=n, unit=u, unit_aud=unit,
                         line_aud=round(n * unit, 2) if k["price"] in COUNTED else 0.0, price=k["price"], source=k["source"],
                         stages=split[mat]))
    k = rt[("lump", "Fasteners and consumables")]
    rows.append(dict(section="materials", group="materials", item="Fasteners and consumables", qty=1, unit="lot",
                     unit_aud=float(k["aud_inc_gst"]), line_aud=float(k["aud_inc_gst"]), price=k["price"], source=k["source"],
                     stages=lump_shares(rows)))
    return rows


def readme_block(rows, total, actual, history):
    by = defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        key = r["group"] if r["section"] == "products" else {"cable": "cable (from the cable schedule)",
                                                             "materials": "raw material for fabricated parts"}[r["section"]]
        by[key][0] += r["line_aud"]
        if r["price"] == "actual":
            by[key][1] += r["line_aud"]
    est = total - actual
    owned = [r["item"] for r in rows if r["price"] == "owned"]
    bat = sum(r["line_aud"] for r in rows if r["group"] == "energy storage")
    lines = ["<!-- cost:start -->",
             f"**Parts total ({V}): A${money(total)}** inc GST. Of that, A${money(actual)} ({actual / total:.0%}) is real prices "
             f"from a named retailer or maker page and A${money(est)} is estimates.",
             "",
             "| Area | A$ inc GST | of which real prices |",
             "|---|---:|---:|"]
    for k, (v, a) in sorted(by.items(), key=lambda x: -x[1][0]):
        if v:
            lines.append(f"| {k[0].upper() + k[1:]} | {money(v)} | {money(a)} |")
    lines += [f"| **Total** | **{money(total)}** | **{money(actual)}** |",
              "",
              f"- Batteries are A${money(bat)} of the total (A${money(total - bat)} without them).",
              "- Real prices were checked on the date in the product list; many are current sale prices, so expect some to rise.",
              f"- Not counted (already owned): {', '.join(owned)}; also the tent, Load-Lid and Destroyer rails.",
              "- Not included: labour, the licensed electrician for the 230 V work, freight, tools, a fridge, Starlink hardware.",
              "",
              "**Running total by version**",
              "",
              "| Version | Parts total A$ | Real prices |",
              "|---|---:|---:|"]
    for h in history:
        lines.append(f"| {h['version']} | {money(float(h['total_aud']))} | {float(h['actual_share']):.0%} |")
    lines += ["",
              f"Line by line, with the source for every price: [`bom/cost-summary-{V}.csv`](bom/cost-summary-{V}.csv). "
              f"Prices are in [`bom/product-list-{V}.csv`](bom/product-list-{V}.csv) and [`bom/cost-rates.csv`](bom/cost-rates.csv). "
              "Regenerate with `python3 tools/costing.py`.",
              "<!-- cost:end -->"]
    return "\n".join(lines)


def stage_table(rows):
    names = {int(r["stage"]): (r["name"], r["you get"]) for r in csv.DictReader(open(ROOT / "bom/stages.csv"))}
    by = defaultdict(lambda: defaultdict(float))
    for r in rows:
        if r["line_aud"] and not r["stages"]:
            raise SystemExit(f"{r['item']} is counted but has no stage")
        for s, f in r["stages"].items():
            by[s][r["section"]] += f * r["line_aud"]
            if r["price"] == "actual":
                by[s]["actual"] += f * r["line_aud"]
    out, run = [], 0.0
    for s in sorted(names):
        d = by[s]
        tot = d["products"] + d["cable"] + d["materials"]
        run += tot
        out.append(dict(stage=s, name=names[s][0], you_get=names[s][1], products=d["products"], cable=d["cable"],
                        materials=d["materials"], total=tot, actual=d["actual"], cumulative=run))
    return out


def stages_block(st):
    lines = ["<!-- stages:start -->",
             "| Stage | What you get | Parts A$ | Running total A$ | Real prices |",
             "|---|---|---:|---:|---:|"]
    for s in st:
        lines.append(f"| **{s['stage']}. {s['name']}** | {s['you_get']} | {money(s['total'])} | {money(s['cumulative'])} | "
                     f"{s['actual'] / s['total']:.0%} |")
    lines += ["",
              "Parts only, inc GST: products, plus the cable and raw material each stage uses. "
              "Generated by `python3 tools/costing.py`.",
              "<!-- stages:end -->"]
    return "\n".join(lines)


def replace_block(path, tag, text):
    t = path.read_text()
    a, b = t.index(f"<!-- {tag}:start -->"), t.index(f"<!-- {tag}:end -->") + len(f"<!-- {tag}:end -->")
    path.write_text(t[:a] + text + t[b:])


def main():
    rt, sm = rates(), stage_map()
    rows = products() + cables(rt, sm) + materials(rt, sm)
    total = sum(r["line_aud"] for r in rows)
    actual = sum(r["line_aud"] for r in rows if r["price"] == "actual")
    out = ROOT / f"bom/cost-summary-{V}.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["section", "group", "item", "qty", "unit", "unit AUD inc GST", "line AUD inc GST", "price", "source"])
        for r in rows:
            w.writerow([r["section"], r["group"], r["item"], r["qty"], r["unit"], r["unit_aud"], r["line_aud"], r["price"], r["source"]])
        w.writerow(["total", "", "", "", "", "", round(total, 2), "", f"actual {actual:.0f} / estimate {total - actual:.0f}"])
    hist_path = ROOT / "bom/cost-history.csv"
    hist = list(csv.DictReader(open(hist_path))) if hist_path.exists() else []
    hist = [h for h in hist if h["version"] != V] + [dict(version=V, total_aud=f"{total:.0f}", actual_share=f"{actual / total:.3f}")]
    hist.sort(key=lambda h: [int(x) for x in h["version"].lstrip("v").split(".")])
    with open(hist_path, "w", newline="") as f:
        w = csv.DictWriter(f, ["version", "total_aud", "actual_share"])
        w.writeheader()
        w.writerows(hist)
    st = stage_table(rows)
    assert abs(st[-1]["cumulative"] - total) < 1, (st[-1]["cumulative"], total)
    with open(ROOT / f"bom/cost-by-stage-{V}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["stage", "name", "products AUD", "cable AUD", "materials AUD", "stage total AUD", "real prices AUD", "running total AUD"])
        for s in st:
            w.writerow([s["stage"], s["name"], round(s["products"]), round(s["cable"]), round(s["materials"]), round(s["total"]),
                        round(s["actual"]), round(s["cumulative"])])
    replace_block(ROOT / "README.md", "cost", readme_block(rows, total, actual, hist))
    replace_block(ROOT / "README.md", "stages", stages_block(st))
    replace_block(ROOT / "docs/build-stages.md", "stages", stages_block(st))
    print(f"{V}: A${total:,.0f} (actual {actual:,.0f}, estimate {total - actual:,.0f}); wrote {out.relative_to(ROOT)}, README.md")


if __name__ == "__main__":
    main()
