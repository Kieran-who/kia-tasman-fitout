# Kia Tasman X-Pro fit-out

DIY tub, electrical and roof fit-out for a Kia Tasman X-Pro dual cab with a Ute Master Load-Lid and a 23Zero Panther Horizon 1600 rooftop tent (on Rhino-Rack bars).

**Current version: v0.12.** See [`docs/v0.12-concept.md`](docs/v0.12-concept.md) (power-slide cable chain lying flat under the deck, so both decks are 579 mm wide; raised fridge well; pod fed from the battery bay; pod outlets cut to Anderson, 12 V and 230 V; 100 W + 20 W rear USB-C; cabin compute feed). [`v0.11`](docs/v0.11-concept.md): motorised slide-out windscreen solar visor: one-button deploy/stow, self-locking drives, fail-locked latches, 22° hard stop, ignition interlock; MPPT 100/50). [`v0.10`](docs/v0.10-concept.md): storage under the tent (30 L water, rear-loading drawer with the table, diesel pack, extinguisher, rivnut cross-bars). [`v0.9`](docs/v0.9-concept.md): v0.8 layout decisions resolved for minimum space. v0.8 ([`docs/v0.8-concept.md`](docs/v0.8-concept.md)) added detail to every component and the full wiring diagram. **Wiring diagram: [`docs/wiring/`](docs/wiring)** (9 A3 sheets as HTML/PDF/SVG + schedules). Earlier versions: [`v0.7`](docs/v0.7-concept.md) (fold-out legs), [`v0.6`](docs/v0.6-concept.md) (edge-to-edge receiver grid, fridge-well filler, flush edge fences), [`v0.5`](docs/v0.5-concept.md) (covered deck), [`v0.4`](docs/v0.4-concept.md) (charging rationale, USB-C, dividers), [`v0.3`](docs/v0.3-concept.md), [`v0.2`](docs/v0.2-concept.md), [`v0.1`](docs/v0.1-concept.md). [`docs/weight-options.md`](docs/weight-options.md) covers weight trade-offs.

![Chain under the power deck](renders/v0.12/02_power_slide_out_chain.png)

| | |
|---|---|
| ![Section through the chain and fridge well](renders/v0.12/01_section_chain_fridge.png) | ![Decks plan](renders/v0.12/03_decks_plan.png) |
| ![Visor deployed](renders/v0.11/01_visor_deployed.png) | ![Wiring sheet E3](docs/wiring/sheets/E3-dc-dist.svg) |

| | |
|---|---|
| ![Visor side view](renders/v0.11/03_visor_side.png) | ![Visor mechanism](renders/v0.11/04_visor_mechanism.png) |
| ![Wiring sheet E9](docs/wiring/sheets/E9-visor.svg) | ![Camp mode](renders/v0.10/06_hero_camp.png) |

| | |
|---|---|
| ![Under-tent storage](renders/v0.10/01_under_tent_travel.png) | ![Lid plan](renders/v0.10/03_lid_plan.png) |

| | |
|---|---|
| ![Battery bay](renders/v0.9/bay_01_overview.png) | ![Rear control panel](renders/v0.9/cabinets_01_panel_shut.png) |
| ![Power pod](renders/v0.9/slides_02_power_pod.png) | ![Fold-out legs](renders/v0.9/slides_04_legs.png) |
| ![Wiring sheet E2](docs/wiring/sheets/E2-dc-main.svg) | ![Wiring sheet E1](docs/wiring/sheets/E1-overview.svg) |
| ![Receiver grid to the edges](renders/v0.6/02_tub_iso_empty.png) | ![Well filler fitted](renders/v0.6/03_tub_iso_filler.png) |
| ![Flush edge fences](renders/v0.6/04_tub_iso_fences.png) | ![Edge pin section](renders/v0.6/08b_section_edge.png) |
| ![Rear control panel](renders/v0.5/08_rear_panel.png) | ![Drawers with removable dividers](renders/v0.5/09_drawers.png) |

## Cost (parts only)

<!-- cost:start -->
**Parts total (v0.12): A$27,350** inc GST. Of that, A$14,369 (53%) is real prices from a named retailer or maker page and A$12,982 is estimates.

| Area | A$ inc GST | of which real prices |
|---|---:|---:|
| Energy storage | 4,198 | 4,198 |
| Slides | 3,672 | 0 |
| Raw material for fabricated parts | 3,324 | 0 |
| Roof | 3,183 | 2,564 |
| Visor | 1,973 | 428 |
| Cable (from the cable schedule) | 1,853 | 0 |
| Inverter/charger | 1,687 | 1,687 |
| Protection | 1,318 | 831 |
| Solar | 1,117 | 1,117 |
| Under-tent | 940 | 370 |
| Distribution | 938 | 930 |
| Monitoring | 902 | 902 |
| AC | 667 | 637 |
| DC | 536 | 240 |
| DC charging | 465 | 465 |
| Storage | 436 | 0 |
| Wiring | 140 | 0 |
| **Total** | **27,350** | **14,369** |

- Batteries are A$4,198 of the total (A$23,152 without them).
- Real prices were checked on the date in the product list; many are current sale prices, so expect some to rise.
- Not counted (already owned): Rhino-Rack Vortex bars + raised brackets, Folding table; also the tent, Load-Lid and Destroyer rails.
- Not included: labour, the licensed electrician for the 230 V work, freight, tools, a fridge, Starlink hardware.

**Running total by version**

| Version | Parts total A$ | Real prices |
|---|---:|---:|
| v0.11 | 27,256 | 53% |
| v0.12 | 27,350 | 52% |

Line by line, with the source for every price: [`bom/cost-summary-v0.12.csv`](bom/cost-summary-v0.12.csv). Prices are in [`bom/product-list-v0.12.csv`](bom/product-list-v0.12.csv) and [`bom/cost-rates.csv`](bom/cost-rates.csv). Regenerate with `python3 tools/costing.py`.
<!-- cost:end -->

**Build in stages** ([`docs/build-stages.md`](docs/build-stages.md)): the order, what each stage gives you, and what to prepare for the next one.

<!-- stages:start -->
| Stage | What you get | Parts A$ | Running total A$ | Real prices |
|---|---|---:|---:|---:|
| **1. Power core** | Dual-battery system charged from the alternator; fridge and 12 V / USB-C outlets at the rear panel; battery isolation, monitoring by Bluetooth | 8,644 | 8,644 | 75% |
| **2. Roof platform and solar** | Wedgetail platform, 320 W roof solar on the MPPT 100/50, Starlink Mini mount and power: stays charged when parked | 3,574 | 12,218 | 82% |
| **3. Slides and storage** | Both slides with receiver grid and legs, power pod (12 V side), over-arch and utility drawers | 6,197 | 18,415 | 1% |
| **4. 230 V and monitoring** | MultiPlus-II inverter/charger, all 230 V outlets, shore power, gap junction and tent harness (one electrician visit), Cerbo GX + GX Touch | 3,952 | 22,367 | 79% |
| **5. Tent solar and cabin compute feed** | 200 W tent-top solar on its own MPPT, and the 15 A feed to the under-seat compute box (SB50 inlet) ready for the smart-ute system | 984 | 23,351 | 65% |
| **6. Under-tent storage** | Cross-bars, rear drawer, 30 L water, diesel pack | 1,197 | 24,547 | 31% |
| **7. Visor and roof extras** | Motorised windscreen visor, light bar, cargo bars | 2,803 | 27,350 | 26% |

Parts only, inc GST: products, plus the cable and raw material each stage uses. Generated by `python3 tools/costing.py`.
<!-- stages:end -->

## Repository layout

| Path | What |
|---|---|
| `docs/design-brief.md` | Requirements and decision log |
| `docs/build-stages.md` | Build sequence in seven stages to spread the cost |
| `docs/smart-ute-research.md` | Smart ute hardware research: mini PC (HA + Frigate), STARVIS cameras, thermal + dash screen, tablet, network, power budget, costs |
| `docs/smart-switching.md` | Smart switching proposal: inverter via VE.Bus, Smart BatteryProtect on Starlink and tent 12 V with ON/OFF/AUTO rockers driven by the Cerbo relays; everything else always on |
| `docs/measurements/` | **Measurement sheet** to print and fill in (PDF/HTML, diagrams, CSV): every dimension the model still estimates |
| `tools/measure/` | Generator for the measurement sheet (reads `cad/params.py`) |
| `docs/v0.12-concept.md` | Current: cable chain flat under the power deck, full-width decks, raised fridge well, pod fed from the bay (F17), outlet changes |
| `docs/v0.11-concept.md` | Motorised windscreen solar visor (mechanism, clearances, controls and safety, roof load) |
| `docs/v0.10-concept.md` | Storage under the tent (drawer, water, diesel, extinguisher, cross-bars), lid load check |
| `docs/v0.9-concept.md` | cable window in the distribution board, flush rear GPO, narrower chain, owner confirmations |
| `docs/v0.8-concept.md` | Detail pass on every component, real-product corrections, layout issues to decide, wiring changes |
| `docs/wiring/` | **Wiring diagram** E1–E9 (HTML, PDF, SVG) with cable / protection / fuse-way / component schedules |
| `docs/v0.7-concept.md` | Fold-out telescopic legs under the slides; arch hooks removed (still current) |
| `docs/v0.6-concept.md` | Receiver grid to the deck edges, removable fridge-well filler, flush edge fences (still current) |
| `docs/v0.5-concept.md` | Slides: side-mount runners under a covered continuous deck (still current) |
| `docs/v0.4-concept.md` | Charging rationale, rear panel, dividers (still current); under-mount slides (dropped) |
| `docs/v0.3-concept.md` | Battery configuration and tailgate-only access (still current) |
| `docs/research-notes.md` | Sourced dimensions and specs |
| `cad/params.py` | **Every dimension in one place.** Each is flagged `[PUB]` (published), `[EST]` (estimate, measure it), `[DES]` (design choice) or `[CONFIRM]` |
| `tools/wiring/` | Wiring diagram generator (reads the cable schedule + routed cables) |
| `tools/costing.py` | Parts cost: prices the product list, cable and raw material, updates the cost section above |
| `cad/fitout/` | Parametric CadQuery model, one module per subsystem: `vehicle`, `lid_tent`, `bay`, `slides`, `side_bays`, `roof`, `lid_storage` (under-tent storage), `modules` (example payload + example edge fences), `wiring` (routed cables + schedule) |
| `cad/build.py` | Builds both states. Exports the GLB viewer models, `cad/out/fitout_fab.step` and `cad/out/summary.json`, and generates the BOM CSVs |
| `cad/clash.py` | Interference check between all solid parts (travel + camp states) |
| `bom/weight-budget-<ver>.csv` | Mass of every part (fit-out vs example payload) |
| `bom/cut-list-<ver>.csv` | Fabricated parts grouped by material and cut size (preliminary) |
| `bom/cable-schedule-<ver>.csv` | Every cable: from/to, size, protection, **length measured along its modelled route** |
| `bom/cable-totals-<ver>.csv` | Cable purchase quantities |
| `bom/product-list-<ver>.csv` | Purchased components, with unit price, real price or estimate, and source (from v0.11) |
| `bom/cost-rates.csv` | Estimated per-metre / per-sheet rates for cable and raw material |
| `bom/cost-summary-<ver>.csv` | Every cost line (products, cable, material) with its source |
| `bom/cost-history.csv` | Parts total per version |
| `bom/stages.csv`, `bom/stage-map.csv` | Build stages, and which cables and fabricated parts belong to each |
| `bom/cost-by-stage-<ver>.csv` | Parts cost per build stage, with the running total |
| `viewer/index.html` | Interactive 3D viewer (three.js): orbit, toggle layers, camp/travel states, preset views |
| `renders/<version>/` | Rendered images per version |
| `reference/` | Owner photos and the 23Zero tent drawing |

## Viewing the model

- **STEP:** open `cad/out/fitout_fab.step` in [Onshape](https://www.onshape.com) or [FreeCAD](https://www.freecad.org) (both free).
- **Interactive viewer (artifact):** `python3 tools/make_artifact.py <dir>` packages the viewer as a self-contained page.
- **Interactive viewer (local):** run `npx serve viewer` (or `python3 -m http.server -d viewer`) and open the URL it prints.

## Rebuilding

```bash
python3 -m venv .venv && .venv/bin/pip install -r cad/requirements.txt
cd cad && ../.venv/bin/python build.py      # model -> GLB + STEP + summary + BOM CSVs
../.venv/bin/python clash.py                 # interference check
cd ../tools/render && npm install && node render.mjs shots_v0.9.json ../../renders/v0.9
cd ../.. && python3 tools/wiring/diagram.py   # wiring sheets + page (after build.py)
```

Change a number in `cad/params.py`, rebuild, re-check and re-render. Every part, cable length and weight follows.

## Coordinate system (tub frame)

`X` runs rearward from the inner face of the tub front wall. `Y` is across the tub (+ = driver/right, − = passenger/left). `Z` is up from the tops of the floor liner ribs. Units are mm.

## Safety notes

- Fixed 240 V wiring in a vehicle must be installed or certified by a licensed electrician (AS/NZS 3001.2), with an RCD/RCBO on every inverter circuit.
- Check the limits: GVM 3250 kg (payload 1013), **rear axle 2002 kg**, roof 100 kg dynamic, Load-Lid 200 kg dynamic. The open tailgate has no published rating. See the weight and axle tables in the v0.3 concept.
- The load lid can't be opened with the tent fitted, so every control, fuse and storage space is reached from the tailgate.
