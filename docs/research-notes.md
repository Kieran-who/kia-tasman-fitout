# Research notes: sourced specifications

Gathered October 2026. Confidence: **H** = manufacturer document, **M** = retailer or review, **L** = estimate or single source.
Anything marked **MEASURE** must be checked on the vehicle before cutting material.

## Vehicle: Kia Tasman X-Pro dual cab

| Item | Value | Conf. | Source |
|---|---|---|---|
| Tub length / max width / depth (SX+, X-Line, X-Pro) | **1512 / 1572 / 540 mm** | H | Kia AU spec sheet (A) |
| Tub (S / SX, no liner) | 1573 / 1600 / 543 mm | H | A |
| Between wheel arches | **1186 mm**, same figure for every grade | M | CarExpert (B, C) |
| Factory tub liner | Standard on SX+, X-Line, X-Pro | H | A |
| Tub volume VDA | 1173 L | H | A |
| Tie-downs | 4 bed hooks on the side walls | H | Owner's manual (E1) |
| Factory 240 V outlet | 400 W, engine running only, on the tub inner side wall. **Passenger side** (owner confirmed) | H | E3 |
| Tailgate | Drop-down, opens 90° | M | B |
| Overall size | 5410 L × 1930 W × 1920 H (X-Pro), wheelbase 3270 | H | A |
| Roof rails | Bridge-type raised rails (X-Line / X-Pro) | H | A |
| Roof load | **100 kg dynamic**, 400 kg static | H | A, E5 |
| Payload | about 1013 kg (GVM 3250 kg) | M | CarExpert |
| Under-rear-seat storage | 45 L | H | A |
| Alternator rating | **Not published.** Plan for a smart alternator | L | — |

**Liner note.** The liner grades are listed 61 mm shorter, 28 mm narrower and 3 mm shallower than S/SX. That suggests the 1512 × 1572 × 540 figures are measured with the liner fitted. The 1186 mm between-arch figure is the same for every grade, so it is probably bare steel. The model therefore uses **1170 mm** between the arches (`LINER_ALLOW = 8` mm per side). **MEASURE.**

**Not published (MEASURE):** wheel-arch length and height, tailgate opening width, Load-Lid height above the rail, tub-rail height from the ground, and exact tie-down positions.

## Ute Master MK2 Load-Lid (Tasman), LLX-KTA37-B-DSR

- **Rating:** 200 kg dynamic / 400 kg static (H). Material: 3 mm aluminium chequer plate, powder-coated (M).
- **Side rails:** Destroyer Side Rails, full-length T-track, rated 200 kg (H).
- **Tent mounting:** Utemaster cross bars (A$558) are the recommended mount and need the 15 kg gas stay upgrade (H).
- **Weight:** about 50–70 kg (L). **Height above the rail:** not published.

## 23Zero Panther Horizon 1600

- **Closed size:** 1550 L × 1270 W × **330 H** (55 base/rails + 250 shell + 25 roof bars) (H, user manual).
- **Weight:** **84 kg** (H).
- **Underside rails:** 2 rails along the 1550 direction, 1440 long, 800 mm c/c, M8 T-bolts (H).
- **Top bars:** 2 bars about 890 long, about 1040 mm c/c, set toward one end; the other end of the shell slopes down (L, scaled from drawing).
- **Load on top:** **20 kg max**, spread over both bars (H). Solar on the bars is supported by 23Zero (H).
- **Opening:** H-frame gas-strut lift, and the baseboard folds out on the ladder side (H).

## Roof platform

| Option | Size | Notes | A$ |
|---|---|---|---|
| **Wedgetail Adventure WT-KT-1614U** (recommended) | 1600 × 1450 | Tasman kit WTM-KT-1614 bolts to factory roof points (headlining drops). Sits about 70 mm off the roof. Has a light-bar plate and recessed solar brackets | 2,195 |
| Yakima LockNLoad + Tasman track kit | 1530 × 1495 | Mounts on the raised rails | — |
| X-Country Summit CK0081 | 1455 × 1380 | Mounts on the raised rails | 1,690 |
| ARB BASE | Tasman kit exists | Size and part number not found | — |

## Solar

| Panel | Size (mm) | W | kg |
|---|---|---|---|
| **Victron BlueSolar SPM041903903** ×2 on the roof | 1485 × 668 × 30 | 190 | 10.5 |
| **Sunman eArc 100 W** ×2 on the tent (on an ACM backing sheet) | 1093 × 552 × 2 | 100 | ~2.0 |

## Starlink Mini

- **Dish:** 298.5 × 259 × 38.5 mm, 1.10 kg.
- **Power:** 12–48 V DC input, 25–40 W average, 60 W max.
- **Wiring plan:** feed the DC barrel input directly from a fused 12 V circuit.
- **Mounts:** Front Runner RRAC352 (slides into platform T-slots), Wedgetail Starlink Mini mount.

## Batteries: iTechworld iTech400X Pro (×2)

| Item | Value |
|---|---|
| Size / weight | 525 × 240 × 220 mm (235 incl. terminals), 38 kg |
| Discharge | 250 A continuous, 500 A for 5 s (per battery) |
| Charge | 14.4 V absorption / 13.5 V float, up to 150 A per battery |
| Orientation | Any orientation except upside down |
| Comms | Bluetooth only (no CAN / RS485), so state of charge comes from a Victron shunt |
| Terminals | M8 (confirm on the 2025 model) |

## Inverter/charger

| Unit | Continuous (25 °C) | Size (H × W × D) | kg | A$ ex GST |
|---|---|---|---|---|
| **Victron MultiPlus-II 12/3000/120-32** (selected) | 2400 W (3000 VA), 5500 W peak, 120 A charger, 32 A transfer | 546 × 275 × 147 | 19–20 | 1,795 |
| Victron Quattro 12/5000/220-100/100 (option) | 4000 W, 10 kW peak, 220 A charger | 444 × 328 × 240 | 34 | 3,926 |
| Redarc RS3 3000 W | 3000 W, built-in RCD and transfer switch, no charger | 467 × 318 × 131 | 10.3 | — |

- **Mounting:** the MultiPlus-II manual says wall mount. Flat mounting is acceptable with derating, so add a fan.
- **Simultaneous loads:** a kettle and microwave together (about 3.4 kW) exceed any 12 V 3 kVA unit.

## DC-DC, MPPT, monitoring, protection

| Item | Size (mm) | Notes | A$ ex GST |
|---|---|---|---|
| Orion XS 12/12-50A ×2 | 137 × 123 × 40 | 100 A in parallel. Voltage-based engine detection suits a smart alternator. Mount vertical, terminals down | 534 each |
| SmartSolar MPPT 100/50 | 130 × 186 × 70 | Roof array | 317 |
| SmartSolar MPPT 75/15 | 100 × 113 × 40 | Tent array | 109 |
| Cerbo GX MK2 | 48 × 154 × 78 | Home Assistant via the core "Victron GX" MQTT integration or Modbus TCP | 425 |
| GX Touch 50 | 87 × 128 × 12.5 | Display | 378 |
| SmartShunt 500 A | 46 × 120 × 54 | Bank state of charge | ~167 |
| Lynx Class-T Power In | 170 × 280 × 97 | 400 A Class-T (Blue Sea 5121) | 291 |
| Lynx Distributor | 170 × 290 × 80 | 4 × MEGA fuses | 345 |
| Blue Sea 6006 isolator | — | 300 A continuous | ~53 |
| Blue Sea 5191 MRBF ×2 | — | Fuse on each battery positive | ~50 each |

**Cables:**
- Inverter: 2 × 50 mm², or 95 mm² for runs of about 1 m.
- Alternator feed: 50 mm² pair (about 5 m), fused 150 A at the start battery, then 70 A per Orion.

**Charge budget:** MultiPlus 120 A + Orions 100 A + solar about 45 A = 265 A. That is under the 300 A the two batteries accept.

## Slides

| Runner | Size | Rating per pair |
|---|---|---|
| Accuride DZ9308 (locks in and out, handed, side mount only) | 76.2 × 19.1 | 1118 mm: 218 kg · 1219 mm: 204 kg (moderate use) |
| Accuride DZ9301 (detent, disconnect) | 76.2 × 19.1 | Same |

- **In a vehicle:** Accuride's vehicle rating is about 163 kg at 559 mm, so roughly 120 kg per pair at 1.2 m.
- **Design:** the model uses **4 runners per slide**: DZ9308 on the outside, DZ9301 on a centre keel. It also has fold-down legs, and UHMW stops so road loads don't go through the runners when stowed.
- **Drag chain:** igus E2.26 family, about 75 mm bend radius, running on its side in a glide trough under the power slide.

## Modular fixing hardware

- **L-track:** about 35 × 13 mm (US heavy-duty) or 42 mm wide (KombiLife AU). Double studs cost $5–19.
- **Receivers:** stainless flanged bushes epoxied into countersunk holes in 15–18 mm ply.
- **Fasteners:** 8 mm ball-lock pins locate the modules (they take shear). Camloc D4002 quarter-turn fasteners (3.1 kN working) or L-track studs hold them down.

## Water

- **Tanks:** off-the-shelf (Dunn & Watson) 60 L $235, 80 L $300, 48 L wheel-arch $315–370. A custom welded PE tank to fit the L-shape costs about $500–1000 (estimate, get quotes).
- **Pumps:** Shurflo 4008 (206 × 125 × 110, 3.0 GPM, 7.5 A) or Seaflo 42-series.
- **Tap:** Suprema XCEL pull-out tap, needs at least 300 kPa.

## 240 V compliance (Australia)

- **AS/NZS 3001.2:** each inverter circuit needs its own labelled RCD. Fixed 240 V wiring in vehicles must be done by a licensed electrician (check your state regulator).
- **MultiPlus-II:** its ground relay provides the neutral–earth bond in inverter mode.
- **Outlets:** the Clipsal 56C310RC is an IP66 outlet with a built-in 30 mA RCD.

## Sources

- A: https://media.adtorqueedge.com/new-cars/kia/tasman/tasman-brochure.pdf
- B: https://www.carexpert.com.au/kia/tasman/2026/x-pro/exterior-and-dimensions
- C: https://www.carexpert.com.au/kia/tasman/2026-s-2-2l-utility-rwd-diesel-automatic-jsgsokmk20250516
- E1 / E3 / E5: https://ownersmanual.kia.com/full_webhelp/TK1/2026/en_GB/topics/t00276.html, t00285.html, t00288.html
- Ute Master: https://www.utemaster.com.au/products/kia-tasman-hard-lid · https://www.utemaster.com.au/products/hard-lid-destroyer-side-rails · https://www.utemaster.com.au/products/hard-lid-cross-bars
- 23Zero: https://23zero.com.au/product/panther-horizon-1600/ · https://23zero.com.au/wp-content/uploads/2025/07/PANTHER-HORIZON-USER-MANUAL.pdf
- Wedgetail: https://roofrack.com.au/?p=211265 · https://www.roofracksgalore.com.au/platforms-trays/roof-tray-platform-accessories/wedgetail-accessories
- Yakima: https://www.roofracksgalore.com.au/yakima-locknload-platform-1530-x-1495mm-with-ruggedline-hd-for-kia-tasman-4dr-ute-with-raised-roof-rail-2025-onwards-roof-factory-point-mount
- X-Country: https://roofrack.com.au/product/summit-platform-kit-kia-tasman-2025-on-ck0081/
- Victron panels: https://www.victronenergy.com/upload/documents/Datasheet-BlueSolar-Monocrystalline-Panels-current-models-EN.pdf
- Sunman eArc: https://www.mygenerator.com.au/earc-175w-flexible-solar-panel · https://www.solar4rvs.com.au/100w-frameless-earche
- Starlink Mini: https://www.networkinnovations.com/hubfs/docs/product/starlink/NI-Starlink-Mini.pdf · https://www.dometic.com/en-ae/product/starlink-mini-quick-release-mount-rrac352
- iTech: https://itechworld.com.au/cdn/shop/files/X_Range_User_Guide_No_BT.pdf · https://help.itechworld.com.au/en-GB/can-i-mount-my-itechworld-battery-on-its-side-863495
- Victron price list (ex GST): https://www.victronenergy.com/media/pricelist/Pricelist_Victron_AUSD_2026-Q4_Web.pdf
- MultiPlus-II: https://www.victronenergy.com/media/pg/MultiPlus-II_230V/en/technical-specifications-mp-ii-230v.html
- Orion XS: https://www.victronenergy.com/media/pg/Orion_XS_12-12-50A_DC-DC_battery_charger/en/installation.html
- Home Assistant: https://www.home-assistant.io/integrations/victron_gx/ · https://www.home-assistant.io/integrations/victron_ble · https://github.com/sfstar/hass-victron
- Accuride: https://www.metrol.com/online-shop/accuride-dz9301.html · https://albeco.com.pl/pl/katalog/preview/prowadnice-liniowe-accuride-9308.pdf
- igus: https://www.igus.co.uk/product/series-E2-26 · https://igus.co.uk/info/energy-chains-side-mounted
- AS/NZS 3001.2 summary: https://teambmpro.com/12v-guru-as-nzs-3001-2-electrical-installations-what-does-it-all-mean/
- Clipsal 56 series: https://www.clipsal.com/products/industrial/56-series/appliance-inlet-ip66-250v-15a-3-flat-pins-56ai315
- Water: https://dunnandwatson.com.au/?p=2444 · https://defender.com/assets/pdf/shurflo/pds-4008-101-x65.pdf
