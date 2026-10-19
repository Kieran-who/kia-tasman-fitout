# Design brief and decision log

## Vehicle and fixed constraints
- 2025/26 Kia Tasman X-Pro dual cab with the factory tub liner. Tub figures: 1512 × 1572 × 540, 1186 between the arches. The **wheel arches start at the front wall** of the tub.
- Ute Master Load-Lid on the tub. No canopy is possible, so everything lives under the lid.
- 23Zero Panther Horizon 1600 rooftop tent mounted on the lid. It must stay **detachable**, including all its wiring.
- The factory 240 V outlet is on the **passenger side**. It will be removed and its wiring path used to route cables out of the tub. Its area becomes the new outlet panel.
- The owner builds everything themselves (welding and all workshop tools available). Aluminium + plywood preferred.

## Requirements
| # | Requirement | Where it lives in v0.1 |
|---|---|---|
| R1 | 2 × iTech400X Pro 400 Ah at the very front of the tub | Front bay between the arches |
| R2 | Solar + alternator charging | Charging board: Orion XS ×2, MPPT ×2 |
| R3 | Inverter about 3000 W for a kettle and microwave | MultiPlus-II 12/3000 (Quattro 12/5000 as an option) |
| R4 | 240 V mains charging, inlet under the tent, detachable | MultiPlus AC-in via the tent umbilical |
| R5 | 240 V outlet under the tent for a diesel heater, detachable with the tent | Tent services box + lid connector panel |
| R6 | Power to the tent and to the cabin under the rear seats | Tent umbilical; cabin feed through the factory outlet path |
| R7 | Two independent slides, each half the width between the arches, heavy loads fully extended | 4 runners per slide + fold-down legs |
| R8 | Power-side slide has integrated cable management and outlets | Lay-flat chain + outlet bulkhead |
| R9 | Modular slides: centre tie-down track + quick-release module mounting | L-track + 100 mm receiver grid |
| R10 | Passenger rear pocket: power management + 240 V, Anderson, USB-C outlets | Power cabinet |
| R11 | Driver side: drinking-water tank with tap + short hose, may go over the arch | L-shaped tank |
| R12 | Clever use of the space above the passenger arch | Charging board |
| R13 | Quality components; Home Assistant monitoring preferred | Victron + Cerbo GX |
| R14 | Roof platform over the full roof, mostly solar, still carries light cargo above the panels | Wedgetail 1600 × 1450 + removable cargo bars |
| R15 | Flush light bar at the front of the platform (nice to have) | Platform front plate |
| R16 | Starlink Mini permanently on the roof, powered | Rear edge of the platform, 12 V direct |
| R17 | Tent-top solar, 20 kg limit | 2 × 100 W flexible on an ACM sheet (about 10 kg) |
| R18 | Full product list + cutting list, all files kept in this repo | `bom/` (product list v0.1; cutting list after layout freeze) |

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
