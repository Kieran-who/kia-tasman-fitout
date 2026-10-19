# Weight reduction options (after v0.1)

v0.1 fit-out is about **535 kg**, or about **605 kg** with a loaded fridge and microwave. Payload is about **1013 kg**. With a bull bar (~75 kg est), tow bar (~30 kg est) and four adults (~320 kg), about 590 kg is left for the fit-out *and* all camping gear, so v0.1 does not fit.

## Where the weight is (v0.1)

| Item | kg | Carried 24/7? | Lever |
|---|---|---|---|
| Water tank + 80 L | 92 | yes | **Remove**, or drive with it empty |
| Rooftop tent | 84 | yes | Detachable already. Take it off between trips (needs 2–4 people or a garage hoist) |
| Slides (4 runners each) | 80 | yes | 2 runners each + legs saves about 25 kg (capacity falls to ~120 kg per slide in transit) |
| Batteries 2 × 38 | 76 | yes | **One battery** saves 38 kg |
| Roof platform, panels, light bar, Starlink, bars | 61 | yes | Biggest fuel lever (drag). Could drop the platform and rely on tent-top + portable solar |
| Load-Lid | 60 | yes | Fixed |
| Electrical (inverter, Lynx, charging board, cable, bay frame) | 62 | yes | Lighter with one battery (smaller bay, shorter cable) |
| Power cabinet, tent solar | 20 | yes | — |

## Fuel

- Weight matters less than you'd expect. US DOE guidance is roughly **1% fuel per extra 45 kg** for passenger cars, and less for a 2.3 t ute. Removing about 130 kg is worth roughly 2–3%, mostly in stop-start and hilly driving.
- **Drag matters more at highway speed.** The same guidance puts a roof cargo box at 6–17% on the highway.
- A slimline platform with a front fairing, with the cargo bars and light bar off when not needed, is the cheaper option. The tent sits below the roofline behind the cab and is partly shielded.
- If fuel is the main concern, the roof platform is the first thing to question, ahead of the water.

## Option A: remove the water tank

Freed space on the driver side:

- Behind the arch: **637 L × 201 W × ~530 H** (≈ 65 L)
- Above the arch: **850 L × 200 W × ~250 H** (≈ 40 L)

Proposed uses:

1. **Rear pull-out pantry** behind the arch. A tall, narrow drawer (≈ 180 W × 480 H × 600 D) on side-mount runners pulls out rearward, with adjustable shelves for oil, spices, utensils, paper towel and coffee kit. It mirrors the power cabinet on the other side. About 7 kg.
2. **Over-arch gear tray** with lid access: snow chains, shovel, recovery straps and shackles, tyre repair kit, awning poles. About 3 kg.
3. **Water as a module, only on trips.** A 20 L flat tank or jerry with a tap clips into the slide receiver grid. A 12 V pump plugs into the slide outlets. That's 20 kg when needed and 0 kg day to day.
4. Alternatives: a hard-mounted air compressor with a rear quick-coupler, or a **slim battery bay** (see Option C).

Net: about **−84 kg** (−92 tank and water, +8 pantry and tray).

## Option B: one iTech400X Pro

- Saves **38 kg** plus about 5 kg of cable and frame.
- **Energy:** 400 Ah (≈ 4.6 kWh usable). A typical day with fridge, Starlink Mini, kettle ×2, microwave, lights and devices uses about 150 Ah. Add about 50 Ah for a winter night of diesel heater plus inverter idle.

| Daily load | Ah/day (est) |
|---|---|
| 60 L compressor fridge | 35–50 |
| Starlink Mini 24/7 (25–40 W) | 50–75 |
| Kettle ×2 (via inverter) | ~28 |
| Microwave 10 min | ~22 |
| Lights, phones, laptop | ~15 |
| Winter: heater overnight + inverter idle | ~40–60 |
| **Total** | **≈ 150 summer / ≈ 210 winter** |

- That's about 2 days with no input in winter and 3 in summer, extended by ~580 W of solar and 50 A while driving.
- **Two batteries only pay off** for multi-day static snow camps with no powered site.
- **Charging:** one battery accepts 150 A max. Drop to **one Orion XS 50 A** and cap the MultiPlus charger at 100 A.

### Does one battery let the slides reach the front wall?

**Not on its own.** The depth of the front bay is set by the **inverter** (MultiPlus-II footprint 275 deep, 546 tall) and the battery's narrowest side (240), not by the battery count.

Neither unit fits the 200 mm side pockets or the arch tops, so a one-battery bay is still about **280 mm deep**. It can be **half height** though: the battery and inverter fit side by side on the floor (525 + 546 = 1071 of 1170). That frees a **1170 × 280 × ~270 mm top-access shelf** above it, which could hold the charging board and free the passenger arch top.

## Option C: full-length slides (front wall clear)

To clear the front, both the battery *and* the inverter have to move into the rear side pockets:

| Change | Detail |
|---|---|
| Batteries | **2 × slim 200 Ah** (~70–120 mm thick) standing on edge in the driver pocket instead of the iTech400X. Examples: Custom Lithium Ultra Slim 200 Ah 610 × 405 × 71, 22 kg; PowerCell 200 Ah 460 × 290 × 120, 21 kg. Two side by side ≈ 142 mm thick in the 201 mm pocket. 400 Ah total, ~44 kg |
| Inverter | Must stand upright in the passenger pocket (≤ 201 wide, ≤ ~520 tall). **Redarc RS3 3000 W** (467 × 318 × 131, 10.3 kg, built-in RCD and transfer switch) fits. The MultiPlus-II (546 tall) and classic MultiPlus 12/3000 (218 thick) do not |
| Shore charging | The RS3 has no charger, so add a small 240 V charger (e.g. Victron Blue Smart IP22 12/30). Charging drops from 120 A to 30 A, and you lose Victron inverter control in Home Assistant (state of charge still comes from the SmartShunt) |
| Slides | Deck ~1490 long. With 48" runners (1219 travel), ~270 mm of deck stays in the tub when fully out. That bit is lid-access only. 60" runners give near-full extension but a 1.5 m cantilever (legs essential) |
| Water | Must go (the driver pocket now holds the batteries) |

Net: about **−110 kg** vs v0.1, but the power cabinet becomes mostly inverter, and the extra ~300 mm of slide is the hardest part to reach.

## Comparison

| | v0.1 | **A + B "Lite" (recommended)** | C "Full-length" |
|---|---|---|---|
| Fit-out kg | ~535 | **~405** | ~410–425 |
| + fridge/microwave | ~605 | **~475** | ~480–495 |
| Margin with 4 adults + bull bar + tow bar (≈ 590 available) | −15 before gear | **≈ +115 for food, clothes, gear** | ≈ +100 |
| Battery | 800 Ah | 400 Ah | 400 Ah |
| Inverter | MultiPlus-II 3000 | MultiPlus-II 3000 | Redarc RS3 + 30 A charger |
| Slide deck length | 1194 | 1194 | ~1490 |
| Water | 80 L fixed | 20 L module on trips | 20 L module on trips |

**Further optional savings:**
- 2-runner slides: −25 kg
- No roof platform (tent-top + portable solar): −61 kg, plus the biggest fuel saving
- Tent off between trips: −84 kg day to day

**Before finalising:** weigh the finished vehicle at a public weighbridge, per axle. The Tasman's rear-axle rating isn't published in the sources found, and nearly all of this load sits over or behind the rear axle.

Sources:
- fueleconomy.gov driving tips: https://www.fueleconomy.gov/feg/drivehabits.jsp
- Custom Lithium Ultra Slim 200 Ah review: https://www.4x4australia.com.au/gear/custom-lithium-ultra-slim-200ah-battery-review
- PowerCell 200 Ah Slimline: https://saltycaptain.com.au/products/200a-battery-with-bluetooth
- Redarc RS3: https://www.redarcelectronics.com/nz/12v-rs3-inverter-3000w
