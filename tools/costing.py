"""
Parts cost for the current version.

Prices every line of bom/product-list-<ver>.csv, then adds the cable (bom/cable-totals-<ver>.csv) and the raw
material for the fabricated parts (cad/out/summary.json material_need) at the rates in bom/cost-rates.csv. Writes:
    bom/cost-summary-<ver>.csv   one line per product, cable and material, with the price type and source
    bom/cost-history.csv         one total per version (the running total)
    README.md                    the block between <!-- cost:start --> and <!-- cost:end -->

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


def products():
    rows = []
    for r in csv.DictReader(open(ROOT / f"bom/product-list-{V}.csv")):
        kind = r["price"]
        qty, unit = float(r["qty"]), float(r["unit AUD inc GST"] or 0)
        line = qty * unit if kind in COUNTED else 0.0
        rows.append(dict(section="products", group=r["system"], item=r["item"], qty=qty, unit="ea", unit_aud=unit,
                         line_aud=round(line, 2), price=kind, source=r["source"]))
    return rows


def rates():
    return {(r["kind"], r["key"]): r for r in csv.DictReader(open(ROOT / "bom/cost-rates.csv"))}


def cables(rt):
    rows = []
    for r in csv.DictReader(open(ROOT / f"bom/cable-totals-{V}.csv")):
        k = rt[("cable", r["cable"])]
        m = float(r["buy_m (+15%, rounded up)"])
        unit = float(k["aud_inc_gst"])
        rows.append(dict(section="cable", group="cable", item=r["cable"], qty=m, unit="m", unit_aud=unit,
                         line_aud=round(m * unit, 2) if k["price"] in COUNTED else 0.0, price=k["price"], source=k["source"]))
    k = rt[("lump", "Cable terminations")]
    rows.append(dict(section="cable", group="cable", item="Cable terminations", qty=1, unit="lot", unit_aud=float(k["aud_inc_gst"]),
                     line_aud=float(k["aud_inc_gst"]), price=k["price"], source=k["source"]))
    return rows


def materials(rt):
    rows = []
    need = json.load(open(ROOT / "cad/out/summary.json"))["material_need"]
    for mat, q in sorted(need.items()):
        k = rt[("material", mat)]
        unit = float(k["aud_inc_gst"])
        if k["unit"] == "sheet":
            n, u = math.ceil(q * SHEET_WASTE / float(k["sheet_m2"])), "sheet"
        else:
            n, u = round(q * LINEAR_WASTE, 1), "m"
        rows.append(dict(section="materials", group="materials", item=mat, qty=n, unit=u, unit_aud=unit,
                         line_aud=round(n * unit, 2) if k["price"] in COUNTED else 0.0, price=k["price"], source=k["source"]))
    k = rt[("lump", "Fasteners and consumables")]
    rows.append(dict(section="materials", group="materials", item="Fasteners and consumables", qty=1, unit="lot",
                     unit_aud=float(k["aud_inc_gst"]), line_aud=float(k["aud_inc_gst"]), price=k["price"], source=k["source"]))
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


def main():
    rt = rates()
    rows = products() + cables(rt) + materials(rt)
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
    readme = ROOT / "README.md"
    t = readme.read_text()
    a, b = t.index("<!-- cost:start -->"), t.index("<!-- cost:end -->") + len("<!-- cost:end -->")
    readme.write_text(t[:a] + readme_block(rows, total, actual, hist) + t[b:])
    print(f"{V}: A${total:,.0f} (actual {actual:,.0f}, estimate {total - actual:,.0f}); wrote {out.relative_to(ROOT)}, README.md")


if __name__ == "__main__":
    main()
