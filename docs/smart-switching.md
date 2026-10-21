# Smart switching: approach (proposal, 2026-10-20; reduced 2026-10-21)

Goal: switch the inverter, Starlink and the 12 V circuits from Home Assistant (HA), while every circuit keeps working from a physical switch if HA, the mini PC or the network is down. **[est]** marks an estimate. Everything else comes from the sources at the end. Not in the model or the wiring sheets yet.

## 1. The approach in one line

- **Inverter:** controlled over VE.Bus from Home Assistant (HA), not by switching its DC.
- **Starlink and the tent 12 V:** each gets a **Victron Smart BatteryProtect (SBP)**, used as a solid-state switch. An SBP draws about 1 mA, against the 100–150 mA a relay coil holds.
  - Each is driven by a **3-position rocker (ON / OFF / AUTO)** at the rear panel.
  - In AUTO the circuit follows a **Cerbo GX relay**. HA switches that relay, and the HA Victron GX integration confirms the GX relays are exposed as switches.
- **Everything else stays always on**, on plain fused circuits, by decision 2026-10-21: the cabin compute feed, the power-slide pod (fridge), and the rear USB-C / 12 V / Andersons. The tablet runs from the Tasman's own USB-C, so it isn't on this system.

Fallbacks:
- **Rocker ON / OFF** works with HA, the PC, the Cerbo and the network all down.
- **AUTO** also shows on the **GX Touch "Switch pane"** at the rear panel (Venus OS 3.70), so there's a touch fallback that doesn't need HA.

Standby for the whole switching layer is about **1 W [est]**: three SBPs at about 1 mA each, plus a Shelly Plus Uni in the compute box.

## 2. Circuit by circuit

| Circuit | Load | Switched by | AUTO contact | If HA or the PC fails | Manual control |
|---|---|---|---|---|---|
| **Inverter** (MultiPlus-II) | All 230 V, plus the charger | **VE.Bus mode** via the Cerbo: HA select with on / off / charger only / inverter only (HA "Victron GX" integration, MQTT) | – | The MultiPlus keeps its last mode | Existing rocker **S2** on the remote L–H terminal: OFF forces the unit off (charging too); ON lets HA/GX decide. **No Digital Multi Control**: it disables GX on/off control |
| **Starlink** (DO4, 10 A) | Starlink Mini | SBP-65 #1 | Cerbo relay 1 (NO) | **Off** | New 3-position rocker **S4** |
| **Tent 12 V** (DO5, 30 A) | Tent lights and fans | SBP-65 #2 | Cerbo relay 2 (NO) | Off in AUTO after a Cerbo restart. Leave the rocker on ON at camp if it must never drop | New 3-position rocker **S5** |
| **Camera PoE switch** (TSW101, in the compute box) | 2 side cameras (deep-sentry cut) | SBP-65 #3 | Shelly Plus Uni output 1 (compute box) | On | none (HA or the GX only) |
| Tablet | Dashboard tablet | **Tasman's own USB-C ports**, not our wiring | – | Follows the vehicle | – |
| Power-slide pod (DO2, 30 A) | Fridge (pod Anderson), pod 12 V (no USB-C, v0.11) | **Always on** | – | On | – |
| Rear panel outlets (DO1A–D) | 2 × Anderson, 12 V socket, 2 × USB-C (100 + 20 W each) | **Always on** | – | On | – |
| Visor (VIS) | Own controller U11 | U11 runs **ESPHome**: HA gets deploy / stow / position, but all interlocks stay in its firmware | – | Rear button S3 still works | S3 |
| **Cabin compute feed** (DO3, 15 A) | Compute box: HA PC, router, PoE switch | **Never switched by HA.** It ends at an SB50 inlet, then a Smart BatteryProtect (hard low-voltage cut-off) and per-device fuses | – | On | – |
| **ML-RBS main isolator, Cerbo, fuses** | – | **Never under HA.** HA's own power flows through them | – | – | S1 (unchanged) |
| 230 V tent heater outlet | Diesel heater | Not switched separately. Control the heater with its own controller: cutting power to a running diesel heater skips its cool-down | – | – | – |

**Rear panel switches after this change:** S1 battery isolate, S2 inverter, S3 visor, **S4 Starlink**, **S5 tent**. That's two more rockers than today.

## 3. Rocker wiring (S4, S5)

```
FB1 way ──[ATC]── SBP IN ═══ SBP OUT ── load
                   SBP H ←─┬─ rocker "ON":   +12 V (from the SBP IN side)
                           └─ rocker "AUTO": +12 V through the Cerbo relay contact
                              rocker centre = OFF (H floating)
rocker LED ← SBP OUT (shows the real output state, whoever switched it)
Cerbo digital input ← rocker AUTO leg (so HA knows the rocker is in AUTO)
```

- Use Contura **ON-OFF-ON** 3-position rockers with an LED (same family as S1 and S2).
- **SBP settings:**
  - **Normal mode, not Li-ion mode.** Li-ion mode adds a 30 s dead time after the input opens.
  - Set its own low-voltage cut-off to the LiFePO4 values.
- **SBP rules (Victron manual):**
  - Never put the **inverter** on an SBP: its capacitive inrush trips the SBP's short-circuit protection ("E1").
  - Never put a **charging source** through one: reverse current damages it.

## 4. HA automations this enables (examples)

- **Inverter:**
  - Set to *off* when no 230 V load is seen for 10 min.
  - *Charger only* on shore power.
  - *On* when the tablet or a button asks for it.
  - A 12/3000 idling uses 13 W (9 W in AES mode, 3 W in Search mode), about **0.3 kWh/day**.
- **Starlink:**
  - Off below 40% charge or when parked away.
  - On for 15 min when Frigate sees a person, so the alert reaches your phone.
  - The HA Starlink integration also gives stow, restart and power readings.
- **Leaving camp:** tent off, and Starlink off or on schedule.
- **Low battery tiers:**
  - At 30%: Starlink and tent off.
  - At 15%: camera switch off, inverter off.
  - The PC's own BatteryProtect cut is the last backstop.
- **Heat:** compute-box fan on above 45 °C; throttle Frigate or shut down above about 75 °C in the box.

## 5. Parts and cost (AUD inc GST)

| Item | Qty | Each | Total |
|---|---|---|---|
| Victron Smart BatteryProtect 12/24V-65A (Starlink, tent, camera switch) | 3 | about 70–97 (Jaycar MS6198 / Frankie's) | 210–291 |
| Shelly Plus Uni (9–28 VDC, 2 × 300 mA solid-state outputs, 2 inputs) | 1 | about 30–40 [est] | 35 |
| Contura ON-OFF-ON rockers with LED + actuators (S4, S5) | 2 | about 40–50 [est] | 80–100 |
| Wire, ferrules | – | – | about 20 [est] |
| **Total** | | | **about A$345–450** |

The **GX IO-Extender 150 is no longer needed**: the Cerbo's two relays cover Starlink and the tent. It's still the add-on if more HA-switched circuits come later. Its HA exposure isn't confirmed, so check that before relying on it.

**All-in-one alternative: Safiery STAR-Power** (about A$1,280 with its wired-switch module). It's 12 channels, including dimmable ones, and only worth it if dimmable lighting circuits come later.

## 6. Things to check or decide

1. **Rear panel space.** Two more rockers is about 55 mm in a row [est]; it needs a layout pass on the 183.5 mm-wide door.
2. **Starlink Mini through an SBP-65:** confirm its startup surge (60–100 W reported) doesn't trip the SBP. It's well under the 65 A rating.
3. **Tent AUTO default:** the Cerbo relays aren't latching, so in AUTO the tent drops out if the Cerbo restarts. Use ON at camp, or add the IO-Extender (latching) later.

## Sources

**Victron**
- https://www.home-assistant.io/integrations/victron_gx/ (inverter mode select, GX relay switches)
- https://www.victronenergy.com/upload/documents/MultiPlus-II_230V/32424-MultiPlus-II___Quattro-II-pdf-en.pdf (remote on/off, zero-load power)
- https://www.victronenergy.com/media/pg/Cerbo_GX/en/connecting-victron-products.html (DMC disables GX on/off)
- https://www.victronenergy.com/media/pg/Cerbo_GX/en/technical-specifications.html (relays 6 A at 30 VDC)
- https://www.victronenergy.com/blog/2026/02/25/introducing-venus-os-3-70/ (Switch pane)
- https://community.victronenergy.com/t/venus-os-v3-70-shelly-support/54232
- https://www.victronenergy.com/media/pg/GX_IO-Extender_150/en/technical-specifications.html (optional add-on)
- https://www.solar4rvs.com.au/products/victron-gx-io-extender-150-input-output-expansion-module
- https://www.victronenergy.com/upload/documents/Smart_BatteryProtect_12V_24V/114439-Smart_BatteryProtect-pdf-en.pdf
- https://www.victronenergy.com/upload/documents/Datasheet-Smart-Battery-Protect-65-A--100-A--220-A-EN.pdf
- https://frankiesautoelectrics.com.au/products/victron-energy-bpr065022000

**Shelly, Safiery and others**
- https://kb.shelly.cloud/knowledge-base/shelly-plus-uni
- https://safiery.com/product/star-control-can-plus-wireless-controller/
- https://www.bluebottlemarine.com/products/c-zone-contact-6-interface.html

**Home Assistant and relay data**
- https://www.home-assistant.io/integrations/starlink/
- https://uk.rs-online.com/web/p/automotive-relays/2777226 (relay coil current)
