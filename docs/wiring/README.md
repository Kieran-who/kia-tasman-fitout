# Wiring diagram

| File | What |
|---|---|
| `wiring-diagram-v0.12.html` | All nine sheets plus the cable, protection, fuse-way and component schedules. Open it in a browser. |
| `wiring-diagram-v0.12.pdf` | The same, printed: A3 landscape, one sheet per page, then the schedules. |
| `sheets/E1…E9-*.svg` | The individual sheets as SVG. |
| `artifact.html` | The page body used for the published claude.ai artifact. |

| Sheet | Content |
|---|---|
| E1 | Overview: locations, and which cables share each run (worked out from the routed model) |
| E2 | DC power: battery bank, MRBFs, busbars, ML-RBS isolation, SmartShunt, Class-T, MultiPlus DC, earthing |
| E3 | DC distribution: FB1 fuse block ways and every 12 V outlet (rear panel, power-slide pod, cabin, Starlink, tent) |
| E4 | Charging: alternator → Orion XS (ignition sense), roof + visor arrays (parallel) → MPPT 100/50, tent array (series) → MPPT 75/15 |
| E5 | 230 V AC: shore inlet + RCBO → MultiPlus AC-in, AC-out → RCBO enclosure → GPOs and the tent heater outlet |
| E6 | Control and comms: Cerbo GX ports, GX Touch 50, Home Assistant, ML-RBS switch wiring, inverter remote on/off, Orion remote, visor button S3 |
| E7 | Detachable tent harness: gap junction connectors J1–J4, pinouts, detach procedure |
| E8 | Cable routes in plan and side view, bundle lists, and cable to buy |
| E9 | Visor drive: controller U11, slide gearmotor, tilt drives, latches, limit switches, interlocks and the deploy/stow sequence |

## Regenerate

```bash
cd cad && ../.venv/bin/python build.py          # writes bom/cable-schedule-<ver>.csv and cad/out/cables.json
cd .. && python3 tools/wiring/diagram.py         # writes the sheets and the HTML page
cd tools/render && node wiring_pdf.mjs ../../docs/wiring/wiring-diagram-v0.12.html ../../docs/wiring/wiring-diagram-v0.12.pdf
```

The generator stops with an error if any cable in the schedule isn't drawn on a sheet, so new circuits added in `cad/fitout/wiring.py` can't be left out of the drawings.

**230 V work must be done and certified by a licensed electrician (AS/NZS 3000, AS/NZS 3001.2).** These drawings are a design for review.
