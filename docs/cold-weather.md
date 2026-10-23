# Cold-weather protection: batteries and water (proposal, 2026-10-23)

The goal is snow camping in the Snowy Mountains: nights of −5 to −15 °C. Two things need protecting:
- **The house batteries.** LiFePO4 discharges fine down to −20 °C, but **charging below 0 °C damages the cells** (lithium plating).
- **The 30 L water can on the load lid**, so it doesn't freeze.

Not modelled yet; this is the proposal. **[est]** marks an estimate.

## 1. What the iTech400X Pro does on its own

- iTechworld publishes only an "optimum temperature range 5–60 °C" and a "BMS operational temperature range". The product page says −5 to 80 °C; the X-range user guide says −40 to 80 °C.
- The guide says the BMS has "high and low temperature" protection (safe mode), but gives **no low-temperature charging cut-off**. There is **no self-heating**.
- So the build has to stop charging below 0 °C itself, and keep the bank warm enough that charging is allowed.
- **Before stage 1:** ask iTechworld whether the BMS blocks charging below 0 °C, and at what temperature.

(The same page now gives **200 A continuous** per battery, not 250 A, and 150 A maximum charge. That's still enough: the MultiPlus draws about 230 A from the 400 A bank, and the most all chargers together can push is about 235 A into a 300 A charge limit. The BOM is corrected.)

## 2. Batteries: insulate, heat from the middle, and a charger backstop

| Part | What | Why |
|---|---|---|
| **Insulation** | Closed-cell foil-faced foam around the two batteries: 20 mm behind them (below the terminals), 15 mm on the busbar side, and 6 mm on the front wall, the top (under the lid) and the outer side, where the bay leaves only 4–9 mm | Halves the heat loss, about 8 → 4 W/K **[est]** |
| **Heater** | One 12 V **100 W** silicone heater pad on a 3 mm aluminium plate, slid into the 10 mm gap between the two batteries (it heats both inner faces) | No room above or below the batteries (they stand 539 mm tall under a 548 mm lid) |
| **Control** | A 12 V digital thermostat (on below **+3 °C**, off above **+8 °C**). Its probe goes on the outer battery at mid-height. It switches a 15 A relay. A **50 °C normally-closed thermal cut-out** sits on the plate in series. | Works without the Cerbo, Home Assistant or the network |
| **Feed** | **F18:** a 10 A inline fuse on BB3 in the bay (2.5 mm², under 1 m). After QS1, so it's off when the bank is isolated for storage. | Short cable, no new run to the cabinet |
| **Charger backstop** | A Victron temperature sensor on the SmartShunt (battery 1). DVCC shared temperature sense goes to the MPPTs, the Orion and the MultiPlus. Each charger's **low-temperature cut-off is set to +3 °C** (Victron's default is 5 °C). | If the heater fails, nothing charges a cold battery. Test it once by chilling the sensor: forum reports of this path are mixed. |
| **Home Assistant** | Battery temperature from the Cerbo, a warning below +2 °C, and heater-on time | Monitoring only. The thermostat does the control. |

**Energy, from the bay and battery figures:**
- **Heat stored in the bank:** 77 kg at about 1 kJ/kg·K is about 21.5 Wh per °C. Insulated, the bank takes about 5 h to cool from +15 °C to +3 °C on a −10 °C night. Uninsulated, it takes under 2 h.
- **Holding at +3 °C through a −10 °C night:** about **43 Ah** insulated, about 99 Ah without insulation. At −5 °C it's about **23 Ah** **[est]**.
- **Warm-up power:** 100 W brings a cold bank from −10 °C to +5 °C in about 3–4 h, and holds it down to about −20 °C.
- **Why not just warm up before charging?** Letting the bank go cold overnight and heating only before morning charging saves only about 13 Ah. It also delays morning charging by about 3 h. Holding +3 °C is simpler and the cells stay ready.

## 3. Water: jacket plus a small pad, powered from the tent side

The OnTrack 30 L can (340 × 860 × 150) lies on the load lid under the tent. Bare, on a −10 °C night, it drops to 0 °C in about 3–4 h and has about 5 L of ice by morning; the hose and outlet freeze solid **[est]**.

| Part | What |
|---|---|
| **Jacket** | A 20 mm closed-cell foam cover (top, sides and ends), with the cap end opening. Plus a 10 mm foam sheet under the pad, so the pad heats the water and not the lid. On its own, it keeps the water above 0 °C through one −10 °C night (about +2 °C by morning) **[est]**. |
| **Pad** | A 12 V **30 W** silicone pad under the can, with a thermostat set to on below +3 °C, off above +6 °C, and a 45 °C cut-out. Holding +4 °C through a −10 °C night uses about **17 Ah** **[est]**. |
| **Feed** | From the **tent services box** (12 V via T1D / DO5): a 5 A fused output and thermostat in the box, then a 1 m lead with a small connector to the pad. The box is 130 mm from the can. **Nothing passes through the load lid** (R6), and the lead unplugs with the tent. |
| **Hose** | Drain the draw hose after use, or keep it inside the jacket. It freezes long before the can. |

## 4. Why not one heater warming both through the load lid

- **The lid is in the way, and probably insulated.** The batteries are inside the tub (x 8–228) and the water can is on top of the lid (x 240–580). They don't overlap. Heat would have to cross the lid and travel about 300 mm sideways, and most of it would warm the lid and the air.
- **Only uninsulated batteries could pass heat up,** and that doubles their heat loss: the opposite of what saves energy.
- **It breaks the rule** that nothing goes through the load lid (R6).
- **A diesel heater could duct warm air to both,** but it would burn fuel all night to save about 40 W of electric heat. It would also bring combustion into the tub, and it's already meant for the tent.

Two small thermostatic heaters, each on its own insulated item, use the least energy and keep working if one fails.

## 5. Totals

| | Typical night (−5 °C) | Hard night (−10 to −15 °C) |
|---|---|---|
| Battery heater (insulated) | ~23 Ah | ~43–60 Ah |
| Water pad (jacketed) | ~5–10 Ah | ~17–25 Ah |
| **Total** | **~30 Ah** | **~60–85 Ah** |

That's on top of about 210 Ah of winter daily use (docs/weight-options.md), out of 800 Ah. Snow-country solar is weak, so expect to need driving or shore power every 2–3 days.

**Parts [est]:**
- Batteries: foam about A$60, heater pad and plate about A$90, thermostat, relay, cut-out and fuse about A$70, Victron temperature sensor about A$45. Subtotal about **A$265**.
- Water: jacket about A$80, pad about A$40, thermostat, fuse and lead about A$40. Subtotal about **A$160**.
- **Total about A$425.**

## Sources

- iTechworld product page, iTech400X Pro specifications: https://itechworld.com.au/products/12v-400ah-lithium-battery-with-bluetooth-itech400x-pro
- iTechworld X-range user guide: https://itechworld.com.au/cdn/shop/files/X_Range_Batteries_User_Guide.pdf
- Victron community, low-temperature cut-off through shared temperature sense / DVCC (mixed results, test it): https://communityarchive.victronenergy.com/questions/185081/multiplus-ii-and-mppt-chargers-low-temperature-cut.html
- Victron community, GX relay on temperature is unreliable (so use a standalone thermostat): https://community.victronenergy.com/t/cerbo-gx-relay-for-temperature-control-only-activates-at-exact-temperature-ruuvi-tag/22263
- Battery heater pad practice (thermostat plus over-temperature cut-out on an aluminium plate): https://motorhomefun.co.uk/forum/threads/lithium-lifepo4-and-keeping-warm-in-winter-diy-heater.313779
