# Wiring diagram

| File | What |
|---|---|
| `wiring-diagram-v0.13.html` | All fifteen sheets, plus the cable, route, protection, fuse-way, component and cable-to-buy schedules. Open it in a browser. |
| `wiring-diagram-v0.13.pdf` | The same, printed: A3 landscape, one sheet per page, then the schedules. |
| `sheets/E1…E15-*.svg` | The individual sheets as SVG. |
| `artifact.html` | The page body used for the published claude.ai artifact. |

## Circuits

| Sheet | Content |
|---|---|
| E1 | Overview: where everything is, and which cables share each run (taken from the model's runs) |
| E2 | DC power: battery bank, MRBFs, 120 mm² main path, ML-RBS isolation, SmartShunt, Class-T, MultiPlus DC, earthing |
| E3 | DC distribution: FB1 fuse block ways and every 12 V outlet (rear panel, power-slide pod, cabin compute feed, Starlink, tent, visor) |
| E4 | Charging: alternator → Orion XS, roof PV1 + PV2 → MPPT 100/30, visor PV5 → MPPT 100/20, tent array → MPPT 75/15 |
| E5 | 230 V AC: shore inlet + 2-pole RCBO → MultiPlus AC-in; AC-out → Q0 main switch and RCBOs → GPOs and the tent heater outlet; AC earth to chassis |
| E6 | Control and comms: Cerbo GX ports, GX Touch 50, Home Assistant, ML-RBS switch, inverter remote, Orion remote, visor button S3 |
| E7 | Detachable tent harnesses (T1A 230 V, T1D 12 V + PV, T2): junction connectors J1–J4, pinouts, detach procedure |
| E9 | Visor drive: controller U11 (per-channel fuses), slide gearmotor, tilt drives, latches, limit switches, interlocks, sequence |

## Routes (drawn to scale from the routed 3D model)

| Sheet | Content |
|---|---|
| E8 | Route map: every run (R-code) on the whole vehicle in plan and side view, with the run schedule |
| E10 | Front bay: busbar-side riser, rear channel, front channel, charging-board loom, exits to the tray and the slide |
| E11 | Tub: divided cable tray, wall channel, gland plate, rear cabinet and rear-panel loom |
| E12 | Outside: wall cavity, chassis rail, cabin and engine-bay branches, with conduit sizes, fill and P-clips |
| E13 | Cab–tub gap risers, junction box, cab-back riser, platform end member, tent harnesses |
| E14 | Power slide: trunk on the glide tray and the chain, stowed and fully out |
| E15 | Cross-section of every run: cable packing, conduit inside diameter and fill |

## Regenerate

```bash
cd cad && ../.venv/bin/python build.py          # writes the schedules and cad/out/cables.json (routes, runs, sections)
../.venv/bin/python cable_check.py               # every routed cable against every solid part: should report 0
cd .. && python3 tools/wiring/diagram.py         # writes the sheets and the HTML page
cd tools/render && node wiring_pdf.mjs ../../docs/wiring/wiring-diagram-v0.13.html ../../docs/wiring/wiring-diagram-v0.13.pdf
```

The generator stops with an error if any cable in the schedule isn't drawn on a sheet. That way a new circuit added in `cad/fitout/wiring.py` can't be left out of the drawings.

**230 V work must be done and certified by a licensed electrician (AS/NZS 3000, AS/NZS 3001.2).** These drawings are a design for review.
