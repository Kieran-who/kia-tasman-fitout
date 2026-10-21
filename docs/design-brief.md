# Design brief and decision log

## Vehicle and fixed constraints
- 2025/26 Kia Tasman X-Pro dual cab with the factory tub liner. Tub figures: 1512 × 1572 × 540, 1186 between the arches. The **wheel arches start at the front wall** of the tub.
- Ute Master Load-Lid on the tub. No canopy is possible, so everything lives under the lid.
- 23Zero Panther Horizon 1600 rooftop tent mounted on the lid. It must stay **detachable**, including all its wiring.
- The factory 240 V outlet is on the **passenger side**. It will be removed and its wiring path used to route cables out of the tub. Its area becomes the new outlet panel.
- The owner builds everything themselves (welding and all workshop tools available). Aluminium + plywood preferred.

## Requirements
| # | Requirement | Where it lives (v0.12) |
|---|---|---|
| R1 | 2 × iTech400X Pro 400 Ah at the very front of the tub | Front bay between the arches |
| R2 | Solar + alternator charging | Charging board: 1 × Orion XS (25–30 A limit), MPPT 100/50 (roof + visor) + 75/15 (tent) |
| R3 | Inverter ~2400 W (kettle or microwave, one at a time) | MultiPlus-II 12/3000 (v0.3) |
| R4 | 240 V mains charging, inlet under the tent, detachable | Tent services box inlet → gap junction → Quattro AC-in 1 |
| R5 | 240 V outlet under the tent for a diesel heater, detachable with the tent | Tent services box (under the tent, front, inset) → gap junction plug |
| R6 | Power to the tent and to the cabin under the rear seats. **Nothing through the load lid**: all wiring leaves via the factory outlet; tent circuits detach between cab and tub | Gap junction box at the passenger front corner (v0.2) |
| R7 | Two independent slides, each half the width between the arches, heavy loads fully extended | 2 × DZ9308 side-mount per slide under a covered ply deck (L-angles over the runners), UHMW stops, fold-out telescopic legs stowed under each deck (v0.7); both decks 579 mm wide (v0.12) |
| R8 | Power-side slide has integrated cable management and outlets | Cable chain lying flat under the power deck on a glide tray (v0.12) + up-facing power pod (Anderson, 12 V, 230 V; fed from the battery bay) + raised fridge well with a removable flush filler |
| R9 | Modular slides: centre tie-down track + quick-release module mounting | L-track + 100 mm receiver grid running to 37.6 mm from each deck edge; flush edge fences pin into the edge rows (v0.6) |
| R10 | Passenger rear pocket: power management + 240 V, Anderson, USB-C outlets; **all switches (incl. battery isolation) at the back of the tub** | Lower control cabinet with hinged rear control panel (v0.3) |
| R11 | ~~Driver side: drinking-water tank~~ → always-in-the-car utility storage (straps, odd gear) | Utility drawer + over-arch tray (v0.2) |
| R12 | Clever use of the space above the arches; **lid can't open with the tent on, so all storage slides out the back** | Full-length upper drawers both sides (v0.3) |
| R13 | Quality components; Home Assistant monitoring preferred | Victron + Cerbo GX |
| R14 | Roof platform over the full roof, mostly solar, still carries light cargo above the panels | Wedgetail 1600 × 1450 + removable cargo bars; motorised slide-out windscreen visor panel underneath (v0.11) |
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
| 2026-10-19 | v0.4 | Under-mount slides on Rollon DE43 (flat-rated), deck at 62 mm, decks 6 mm apart, fridge well removed | Owner: lower decks + modules butting together; only DE-series rails keep their rating flat |
| 2026-10-19 | v0.4 | Rear roller supports on the cassette + spring-plunger lock | Unload the rails at the tub edge; DE rails have no lock |
| 2026-10-19 | v0.4 | Keep separate Orion XS + two SmartSolar MPPTs (roof 100/30, tent 75/15) | Combined DC-DC/MPPT units cap total output (~50 A) and need matched arrays |
| 2026-10-19 | v0.4 | Rear panel 4 × USB-C (2 dual sockets); upper drawers get removable slot dividers | Owner request |
| 2026-10-19 | v0.5 | Back to DZ9308 side-mount runners; ply deck carried on L-angles over the runners so both decks form one continuous surface (6 mm gap) except the fridge well; chain in an outboard lane | Rollon cost prohibitive; owner wants a continuous covered surface |
| 2026-10-19 | v0.6 | Receiver grid runs edge to edge: edge rows 37.6 mm in (over the RHS side members, pins lock under the RHS top wall), front/rear rows 35 mm in, interior rows shared by both slides | Owner: dividers flush with the slide sides |
| 2026-10-19 | v0.6 | Flush fences/dividers use a 12 mm ply wall on a 60 × 6 foot that reaches the edge receiver row | A pin can't sit under a wall that's flush with the edge (the runner is 2 mm below) |
| 2026-10-19 | v0.6 | Removable fridge-well filler: 15 mm ply on 18 mm ply risers studded into the well L-tracks, flush with the deck, same grid | Owner: use the well as deck when no fridge is fitted |
| 2026-10-19 | v0.7 | Loose pin-in legs → 2 fold-out telescopic legs per slide (32/25/19 SHS, clevis pivot on the side members, fold across the rear bay, clipped under the deck) | Owner: legs should fold out and clip under the slides; the fridge well leaves no room for lengthwise folding |
| 2026-10-19 | v0.7 | Placeholder bed hooks removed; recessed well modelled in each arch face; edge fences back to 150 mm | Owner photo: no hooks on the arches |
| 2026-10-19 | v0.8 | Detail pass on every component from published drawings; real sizes where they differ (iTech terminals both at the top, MultiPlus DC toward the front wall, ML-RBS, PowerBar, Class-T, fuse block, SmartSolar 100/30); power pod deepened to 85 mm for a real Iconic double GPO | Owner: increase detail in all components |
| 2026-10-19 | v0.8 | Full wiring diagram E1–E8 generated from the cable model; VE.Direct-USB for the Orion (Cerbo has 3 VE.Direct ports), bank-side 2 A feed for the ML-RBS control, ignition sense for the Orion, separate fuses per rear outlet, roof panels in parallel, PV isolators, keyed tent connectors (J1 10 A socket / J2 15 A inlet, SB50 red 12 V / grey PV), shore RCBO in the tent box | Owner: full wiring diagram |
| 2026-10-19 | v0.8 | Cable chain re-anchored at mid-travel (was 69 mm short at full extension); rear control panel hinges on its inboard edge | Found during the detail pass |
| 2026-10-19 | v0.9 | Cable window in the distribution board + system − busbar flat on the base tray (MultiPlus cables pass straight through); flush Iconic double GPO under a clear cover on the rear panel; igus E2.15.30 chain (37.8 mm wide) in the 50 mm lane | Owner: "whatever saves the most space" |
| 2026-10-19 | v0.9 | Tent folds open on the driver side (confirmed); Load-Lid struts outside the tub (lid removable with bolts) | Owner confirmation |
| 2026-10-20 | v0.10 | Under-tent storage: rivnut cross-bars clamped to the Destroyer rails, captive 30 L water (fill in place), rear-loading drawer between the tent-bolt lines holding the folding table, RotopaX 1 gal diesel (heater), 2 kg extinguisher on a quick release at the rear edge; lid load 171 of 200 kg | Owner: jerry cans + platform/closed storage under the tent; drawer preferred; small diesel; extinguisher access; table |
| 2026-10-20 | v0.11 | Windscreen solar visor: ~250 W panel stowed under the platform, slides out on two rails (one worm gearmotor, cross shaft + belts), tilts to 20° on two self-locking worm drives, hard stop 22°, spring-locked latches (fail locked), limit switches, ignition interlock, dead-man button S3; MPPT 100/30 → 100/50; roof load 85 of ~100 kg | Owner: slide out a large panel in front of the windscreen when parked; strong, locked for travel, motorised one-button |
| 2026-10-21 | v0.11 | Rear USB-C = 2 × Treklo dual 120 W (100 W PD + 20 W) on 4 mm² / 25 A; pod loses its USB-C; cabin outlets replaced by a 15 A compute feed (SB50 inlet, under-seat compute box); tablet on the Tasman's own USB-C; S6–S8 stay always on | Owner |
| 2026-10-21 | v0.12 | igus chain laid on its side under the power deck on a 3 mm glide tray (bends in plan); outboard lane removed so the power deck widens 529 → 579 mm; fridge-well pan raised to 54 mm (tallest fridge ~490 mm), L-tracks → flush tie-down rings; pod fed from the bay through an MRBF 30 A (F17) on the system + busbar, down behind the inverter into the slide front; FB1 way 5 spare | Owner: run the cable under the slide so the deck can be wider |
