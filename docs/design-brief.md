# Design brief and decision log

## Vehicle and fixed constraints
- 2025/26 Kia Tasman X-Pro dual cab with the factory tub liner. Tub figures: 1512 × 1572 × 540, 1186 between the arches. The **wheel arches start at the front wall** of the tub.
- Ute Master Load-Lid on the tub. No canopy is possible, so everything lives under the lid.
- 23Zero Panther Horizon 1600 rooftop tent mounted on the lid. It must stay **detachable**, including all its wiring.
- The factory 240 V outlet is on the **passenger side**. It will be removed and its wiring path used to route cables out of the tub. Its area becomes the new outlet panel.
- The owner builds everything themselves (welding and all workshop tools available). Aluminium + plywood preferred.

## Requirements
| # | Requirement | Where it lives (v0.3) |
|---|---|---|
| R1 | 2 × iTech400X Pro 400 Ah at the very front of the tub | Front bay between the arches |
| R2 | Solar + alternator charging | Charging board: 1 × Orion XS (25–30 A limit), MPPT 100/50 + 75/15 |
| R3 | Inverter ~2400 W (kettle or microwave, one at a time) | MultiPlus-II 12/3000 (v0.3) |
| R4 | 240 V mains charging, inlet under the tent, detachable | Tent services box inlet → gap junction → Quattro AC-in 1 |
| R5 | 240 V outlet under the tent for a diesel heater, detachable with the tent | Tent services box (under the tent, front, inset) → gap junction plug |
| R6 | Power to the tent and to the cabin under the rear seats. **Nothing through the load lid**: all wiring leaves via the factory outlet; tent circuits detach between cab and tub | Gap junction box at the passenger front corner (v0.2) |
| R7 | Two independent slides, each half the width between the arches, heavy loads fully extended | 2 × DZ9308 per slide, UHMW stowed stops, pin-in legs |
| R8 | Power-side slide has integrated cable management and outlets | Upright chain in the centre gap + up-facing power pod + fridge well |
| R9 | Modular slides: centre tie-down track + quick-release module mounting | L-track + 100 mm receiver grid |
| R10 | Passenger rear pocket: power management + 240 V, Anderson, USB-C outlets; **all switches (incl. battery isolation) at the back of the tub** | Lower control cabinet with hinged rear control panel (v0.3) |
| R11 | ~~Driver side: drinking-water tank~~ → always-in-the-car utility storage (straps, odd gear) | Utility drawer + over-arch tray (v0.2) |
| R12 | Clever use of the space above the arches; **lid can't open with the tent on, so all storage slides out the back** | Full-length upper drawers both sides (v0.3) |
| R13 | Quality components; Home Assistant monitoring preferred | Victron + Cerbo GX |
| R14 | Roof platform over the full roof, mostly solar, still carries light cargo above the panels | Wedgetail 1600 × 1450 + removable cargo bars |
| R15 | Flush light bar at the front of the platform (nice to have) | Platform front plate |
| R16 | Starlink Mini permanently on the roof, powered, never over the tent (it opens sideways) | Inside the platform frame (v0.2) |
| R17 | Tent-top solar, 20 kg limit | 2 × 100 W flexible on an ACM sheet (about 10 kg) |
| R18 | Full product list + cutting list, all files kept in this repo | `bom/` (product list, generated cut list, cable schedule, weight budget) |

## Decisions log
| Date | Version | Decision | Why |
|---|---|---|---|
| 2026-10-19 | v0.1 | CadQuery (Python) parametric model; STEP for CAD, GLB for the web viewer | Free, scriptable, every dimension in one file; STEP opens in Fusion/FreeCAD/Onshape |
| 2026-10-19 | v0.1 | Design width between the arches = 1170 (1186 published − 2 × 8 liner allowance) | The 1186 figure is the same for liner and no-liner grades, so it's probably bare steel |
| 2026-10-19 | v0.1 | Victron ecosystem (MultiPlus-II, Orion XS, SmartSolar, Cerbo GX) | Best Home Assistant integration; one configuration tool |
| 2026-10-19 | v0.1 | Inverter mounted flat with a fan | 546 mm tall upright doesn't fit under the lid |
| 2026-10-19 | v0.1 | DC-DC/MPPT/Cerbo on a vertical board above the passenger arch | Must mount vertically; frees the bay deck |
| 2026-10-19 | v0.1 | 4 runners per slide + legs + UHMW stowed stops | One 1.1 m pair is only rated about 120 kg in vehicle use |
| 2026-10-19 | v0.1 | Tent wiring through a lid gland to connectors on the lid underside | Weather-protected, nothing exposed, tent detaches in minutes |
| 2026-10-19 | v0.2 | Water tank removed; driver side becomes utility storage | Freezing in winter; weight |
| 2026-10-19 | v0.2 | Quattro 12/5000 lying flat beside the batteries; batteries stand on end | ≥ 3000 W needs the 5 kVA model; Victron forbids mounting above batteries |
| 2026-10-19 | v0.2 | 2 × Class-T 400 A (one per battery), 2 × 120 mm² per pole, ≥ 600 A isolator, SmartShunt 1000 A | Victron spec for the Quattro 12/5000 |
| 2026-10-19 | v0.2 | 1 × Orion XS, input limit 25–30 A | Alternator rating unknown; Orion caps alternator draw |
| 2026-10-19 | v0.2 | All external wiring through the factory outlet hole → chassis → cab–tub gap junction; tent harness unplugs there | Nothing through the lid (owner) |
| 2026-10-19 | v0.2 | Tent on Rhino-Rack bars, 163.4 mm above the lid; services box under the tent near the front, inset | Matches vehicle; sheltered |
| 2026-10-19 | v0.2 | Slides: 2 × DZ9308 each, deck at 84 mm, fridge well on the power slide, upright chain in a 50 mm centre gap, pin-in legs, no reliance on the tailgate | Deck height is set by runner height; tailgate rating unpublished |
| 2026-10-19 | v0.2 | Push-button 8 mm ball-lock pins on a 100 mm receiver grid | Owner choice |
| 2026-10-19 | v0.2 | Model gains materials, masses, routed cables, generated BOM/cut/cable lists, axle loads and an interference check | Fidelity toward a fully mapped build |
| 2026-10-19 | v0.3 | MultiPlus-II 12/3000 (2400 W) instead of the Quattro | Owner: 2400 W is sufficient; -14 kg, shallower bay |
| 2026-10-19 | v0.3 | MRBF per battery, equal-length 70 mm² bank cables, Class-T 400 A inverter feed, 2 × 50 mm² | Victron MultiPlus-II 12/3000 spec; even sharing between batteries |
| 2026-10-19 | v0.3 | ML-RBS remote battery switch, controlled from the rear panel | Lid can't open; isolation must be reachable from the tailgate |
| 2026-10-19 | v0.3 | Charging board moved to the front wall above the inverter | Frees the over-arch space for slide-out storage |
| 2026-10-19 | v0.3 | Full-length upper drawers over both arches + lower control cabinet / utility drawer behind the arches | All storage slides out the back |
| 2026-10-19 | v0.3 | No tail-light bulge; tent folds out to the driver side | Owner confirmation |
| 2026-10-19 | v0.3 | Bay 320 deep, slides 1174 mm on 46" DZ9308 | Smaller inverter |
