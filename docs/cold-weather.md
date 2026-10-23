# Cold-weather protection: batteries and water (in the model from v0.14)

The goal is snow camping in the Snowy Mountains, with nights of −5 to −15 °C. Two things need protecting:
- **The house batteries.** LiFePO4 can discharge down to −20 °C, but **charging below 0 °C damages the cells** (lithium plating).
- **The 30 L water can on the load lid**, so it doesn't freeze.

This was a proposal on 2026-10-23. **It is now in the 3D model, the wiring diagram (new sheet E16) and the BOM, as v0.14** ([`v0.14-concept.md`](v0.14-concept.md)). **[est]** marks an estimate.

## 1. What the iTech400X Pro does on its own

- iTechworld publishes only an "optimum temperature range 5–60 °C" and a "BMS operational temperature range". The product page says −5 to 80 °C; the X-range user guide says −40 to 80 °C.
- The guide says the BMS has "high and low temperature" protection (safe mode). It gives **no low-temperature charging cut-off**, and there is **no self-heating**.
- So the build has to stop charging below 0 °C itself, and keep the bank warm enough that charging is allowed.
- **Before stage 1, ask iTechworld two things:**
  - Does the BMS block charging below 0 °C, and at what temperature?
  - Is the case fine with a 50 °C heater pad bonded to its side?

(The same page gives **200 A continuous** per battery, not 250 A, and 150 A maximum charge. That's still enough: the MultiPlus draws about 230 A from the 400 A bank, and all chargers together can push at most about 235 A into a 300 A charge limit.)

## 2. Batteries: insulate, heat from the middle, and a charger backstop

| Part | As modelled (v0.14) | Why |
|---|---|---|
| **Insulation** | Closed-cell, foil-faced foam: **20 mm** behind the batteries (below the terminals, notched for the pad leads), **15 mm** on the busbar side, **6 mm** on top (glued under the lid; the handle lugs stand 539 mm, the lid is at 548), **4 mm** on the front wall, and **4 mm** on the outer side above the wheel arch. There's no room underneath the batteries or on the lower outer side (2 mm to the arch). | Halves the heat loss, from about 8 to about 4 W/K **[est]** |
| **Heaters** | **Two 12 V 50 W silicone pads (HP1, HP2)**, 175 × 215 mm, self-adhesive, one on each battery's **facing side**. They sit in the 14 mm gap between the batteries and between the cage straps (z 200–416). Each has a bonded **50 °C normally-closed cut-out** in series. | There's no room above or below the batteries. One pad per face heats both batteries directly, at only 0.13 W/cm². |
| **Control** | **TH1**: a 12 V digital thermostat with a 30 A relay, in a small IP65 box on the rear foam behind the gap. It turns **on below +3 °C and off above +8 °C**. Its probe (HTS) sits on **battery 2's lid face** at mid-height: that's the outer, colder battery. | Works without the Cerbo, Home Assistant or the network |
| **Feed** | **HTR**: 2.5 mm² twin from BB3 stud 4 through **F18 10 A inline**, up the bay riser (R01) and across behind the batteries, 0.9 m. **HTP**: 1.5 mm² silicone twin from TH1 down through the foam notch to the pads. The feed is after QS1, so opening QS1 for storage also turns the heater off. | Short; no new run to the cabinet |
| **Charger backstop** | **TS1**: a Victron temperature sensor whose lug goes on **battery 1's + post** (under the MRBF). Its red wire goes to SmartShunt V+ and its black wire to Aux (set to temperature). It **replaces the plain Vbatt+ lead (SHV)**. DVCC shared temperature sense passes the reading to the MPPTs and the MultiPlus. Each charger's **low-temperature cut-off is set to +3 °C** (Victron's default is 5 °C). | If the heater fails, nothing charges a cold battery. Test it once by chilling the sensor: forum reports of this path are mixed. |
| **Orion XS** | Check in VictronConnect that it shows the shared battery temperature. If it doesn't, rely on its own low-temperature setting and confirm it in the chill test. | The Orion XS is on USB to the Cerbo, not VE.Direct |
| **Home Assistant** | Battery temperature from the Cerbo, a warning below +2 °C, and heater-on time | Monitoring only; the thermostat does the control |

**Energy, from the bay and battery figures:**
- **Heat stored in the bank:** 77 kg at about 1 kJ/kg·K is about 21.5 Wh per °C. Insulated, the bank takes about 5 h to cool from +15 °C to +3 °C on a −10 °C night. Uninsulated, it takes under 2 h.
- **Holding +3 °C through the night:** about **23 Ah at −5 °C**, and about **43 Ah at −10 °C** (about 99 Ah if uninsulated) **[est]**.
- **Warm-up power:** 2 × 50 W brings a cold bank from −10 °C to +5 °C in about 3–4 h, and can hold it down to about −20 °C.
- **Why hold +3 °C rather than warm up only before charging?** Letting the bank go cold overnight and heating it before morning saves only about 13 Ah, and it delays morning charging by about 3 h. Holding +3 °C is simpler, and the cells stay ready.

## 3. Water: jacket plus a pad, powered from the tent side

The OnTrack 30 L can (340 × 860 × 150) lies on the load lid under the tent. Bare, on a −10 °C night, it drops to 0 °C in about 3–4 h and has about 5 L of ice by morning; the hose and outlet freeze solid **[est]**.

| Part | As modelled (v0.14) |
|---|---|
| **Jacket** | Closed-cell foam with a fabric cover, over the can and its straps. **30 mm on top**: it fills the gap to the tent base (3 mm clear), with a groove where the tent's under-rail passes. **18–20 mm** on the sides and the closed end. The front side is thinned to 8 mm at one tent mount clamp. The **cap end stays open** for filling and the tap. |
| **Pad (HP3)** | A 12 V **50 W** silicone pad, 160 × 735, lying on a 3 mm foam strip **between the first two cross-bars under the can**. It has a bonded **45 °C cut-out**. |
| **Control (TH2)** | A thermostat with a relay inside the **tent services box**: on below +3 °C, off above +6 °C. Its probe is taped to the can, under the jacket. **F19 5 A** is on the box's 12 V (X5, fed by T1D and DO5). |
| **Lead (WHT)** | 1.5 mm² silicone twin, 0.5 m. It leaves the box's inner face, drops to the lid and runs under the jacket's closed end (through a notch) to the pad. It unplugs at a **Deutsch DT 4-pin plug (XW)**, which carries both the pad and the probe, so the tent still lifts off with its box. **Nothing passes through the load lid** (R6). |
| **Hose** | Drain the draw hose after use, or keep it inside the jacket. It freezes long before the can. |

**Energy:** the jacket brings the can's heat loss to about **2.5 W/K** **[est]**. The thin bottom (a 5 mm gap over the lid) and the open cap end lose the most. The water itself stores about 35 Wh per °C. Starting a −10 °C night at +15 °C, the can reaches +3 °C after about 9 h. The pad then holds it for the rest of the night: about **15–20 Ah** on a hard night and about 5 Ah at −5 °C. 50 W holds +3 °C down to about −15 °C.

## 4. Why not one heater warming both through the load lid

- **The lid is in the way, and it's probably insulated.** The batteries are inside the tub (x 8–228) and the water can is on top of the lid (x 240–580). They don't overlap. Heat would have to cross the lid and travel about 300 mm sideways, and most of it would warm the lid and the air.
- **Only uninsulated batteries could pass heat upward,** and that doubles their heat loss: the opposite of what saves energy.
- **It breaks the rule** that nothing goes through the load lid (R6).
- **A diesel heater could duct warm air to both,** but it would burn fuel all night to save about 40 W of electric heat. It would also bring combustion into the tub, and it's already meant for the tent.

Two small thermostatic heaters, each on its own insulated item, use the least energy and keep working if one fails.

## 5. Totals

| | Typical night (−5 °C) | Hard night (−10 to −15 °C) |
|---|---|---|
| Battery heaters (insulated) | ~23 Ah | ~43–60 Ah |
| Water pad (jacketed) | ~5 Ah | ~15–20 Ah |
| **Total** | **~28 Ah** | **~60–80 Ah** |

That's on top of about 210 Ah of winter daily use (docs/weight-options.md), out of 800 Ah. Snow-country solar is weak, so expect to need driving or shore power every 2–3 days.

**Parts (in `bom/product-list-v0.14.csv`):**
- **Stage 1, batteries: about A$242.**
  - Foam set A$60 [est].
  - Two pads A$70 [est].
  - TH1 thermostat, relay and box A$55 [est].
  - Victron temperature sensor A$45.20 (actual, Solar4RVs).
  - F18 holder A$11.50.
- **Stage 6, water: about A$170.**
  - Jacket A$80 [est].
  - Pad A$45 [est].
  - TH2, F19 and the XW plug A$45 [est].
- **Cable:** a few metres of 2.5 / 1.5 mm². The sensor and probe leads come with their parts.

## Test once, before the first cold trip (sheet E16)

1. Chill the TS1 lug (an ice pack in a bag) below +3 °C. Every charger must stop, or show "low temperature".
2. Chill each thermostat probe. The relay must click on, and each pad should draw about 4.2 A (use a clamp meter).
3. Warm each pad's cut-out with a heat gun. The pad must switch off.

## Sources

- iTechworld product page, iTech400X Pro specifications: https://itechworld.com.au/products/12v-400ah-lithium-battery-with-bluetooth-itech400x-pro
- iTechworld X-range user guide: https://itechworld.com.au/cdn/shop/files/X_Range_Batteries_User_Guide.pdf
- Victron temperature sensor for BMV-712 / SmartShunt (M10 lug), Solar4RVs: https://www.solar4rvs.com.au/products/victron-temperature-sensor-smart-shunt-bmv-712
- Victron community, low-temperature cut-off through shared temperature sense / DVCC (mixed results, so test it): https://communityarchive.victronenergy.com/questions/185081/multiplus-ii-and-mppt-chargers-low-temperature-cut.html
- Victron community, the GX relay on temperature is unreliable (so use a standalone thermostat): https://community.victronenergy.com/t/cerbo-gx-relay-for-temperature-control-only-activates-at-exact-temperature-ruuvi-tag/22263
- Battery heater pad practice (thermostat plus over-temperature cut-out): https://motorhomefun.co.uk/forum/threads/lithium-lifepo4-and-keeping-warm-in-winter-diy-heater.313779
- 12 V 50 W silicone pad, 4.2 A (Phillips & Temro Wolverine 3400051, for the current figure): https://newbuild-2025.t7design.co.uk/3400051.html
