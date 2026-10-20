# Smart switching: approach (proposal, 2026-10-20)

Goal: switch the inverter, Starlink and the 12 V circuits from Home Assistant (HA), while every circuit keeps working from a physical switch if HA, the mini PC or the network is down. **[est]** marks an estimate. Everything else comes from the sources at the end. Not in the model or the wiring sheets yet.

## 1. The approach in one line

Each circuit's 12 V feed passes through its own **Victron Smart BatteryProtect (SBP)**, used as a solid-state switch. SBPs draw about 1 mA, not the 100–150 mA a relay coil holds. Each SBP is driven by a **3-position rocker (ON / OFF / AUTO)** at the rear panel. In AUTO the circuit follows a contact controlled by the **Cerbo GX**: its relays, plus a **GX IO-Extender 150**. HA controls those contacts. The **inverter** is controlled over VE.Bus, not by switching its DC.

- **ON / OFF:** the rocker sets the circuit directly. It works with HA, the PC, the Cerbo and the network all down.
- **AUTO:** HA or the GX decides. The same contacts also appear on the **GX Touch "Switch pane"** at the rear panel (Venus OS 3.70), so there's a touchscreen fallback that doesn't need HA.
- **Standby:** about 1 mA per SBP and under 0.1 W for the IO-Extender, so the whole layer is about **1–2 W [est]**. Eight automotive relays held on would draw about 1 A (12 W, about 290 Wh/day).

## 2. Circuit by circuit

| Circuit | Load | Switched by | AUTO contact | If HA or the PC fails | Manual control |
|---|---|---|---|---|---|
| **Inverter** (MultiPlus-II) | All 230 V, plus the charger | **VE.Bus mode** via the Cerbo: HA select with on / off / charger only / inverter only (HA "Victron GX" integration, MQTT) | – | The MultiPlus keeps its last mode | Existing rocker **S2** on the remote L–H terminal: OFF forces the unit off (charging too); ON lets HA/GX decide. **No Digital Multi Control**: it disables GX on/off control |
| **Starlink** (DO4, 10 A) | Starlink Mini | SBP-65 #1 | Cerbo relay 1 (NO) | **Off** | New 3-position rocker S4 |
| **Tent 12 V** (DO5, 30 A) | Tent lights and fans | SBP-65 #2 | IO-Extender latching relay 1 | Stays as it was | S5 |
| **Cabin box** (DO3, 30 A) | Rear-seat Anderson, 12 V, USB-C | SBP-65 #3 | IO-Extender latching relay 2 | Stays as it was | S6 |
| **Power-slide pod** (DO2, 30 A) | **Fridge** (pod Anderson), pod 12 V and USB-C | SBP-65 #4 | Cerbo relay 2 **NC** contact | **On** (the fridge never fails off) | S7 |
| **Rear USB-C + 12 V socket** (DO1C + DO1D) | Phone chargers, small loads | SBP-65 #5. FB1 way 3 (20 A) feeds the SBP, then a local 2-way holder: 10 A USB-C, 15 A socket. That frees way 4 | IO-Extender solid-state output | Off (low priority) | S8 |
| **Camera PoE switch** (TSW101, under the seat) | 2 side cameras (deep-sentry cut) | SBP-65 #6 | Shelly Plus Uni output 1 (under-seat box) | On | none (HA or the GX only) |
| **Tablet supply** (cab) | 30 W USB-C PD | Ignition-switched relay | Shelly Plus Uni output 2 breaks the relay coil to cut the tablet in heat | Follows the ignition | none |
| Rear Andersons ×2 (DO1A/B) | Fridge or compressor at the tailgate | **Not switched**: always available | – | On | – |
| Visor (VIS) | Own controller U11 | U11 runs **ESPHome**: HA gets deploy / stow / position, but all interlocks stay in its firmware | – | Rear button S3 still works | S3 |
| Smart system feed (PC, router, PoE) | HA's own hardware | **Never switched by HA.** Hard low-voltage cut-off (BatteryProtect) only | – | – | – |
| **ML-RBS main isolator, Cerbo, fuses** | – | **Never under HA.** HA's own power flows through them | – | – | S1 (unchanged) |
| 230 V tent heater outlet | Diesel heater | Not switched separately. Control the heater with its own controller: cutting power to a running diesel heater skips its cool-down | – | – | – |

## 3. Rocker wiring (one per SBP)

```
FB1 way ──[ATC]── SBP IN ═══ SBP OUT ── load
                   SBP H ←─┬─ rocker "ON":   +12 V (from the SBP IN side)
                           └─ rocker "AUTO": +12 V through the GX/HA contact
                              rocker centre = OFF (H floating)
rocker LED ← SBP OUT (shows the real output state, whoever switched it)
GX digital input ← rocker AUTO leg (so HA knows the rocker is in AUTO)
```

- Use Contura **ON-OFF-ON** 3-position rockers with an LED (same family as S1 and S2).
- **SBP settings:**
  - **Normal mode, not Li-ion mode.** Li-ion mode adds a 30 s dead time after the input opens.
  - Set its own low-voltage cut-off to the LiFePO4 values. Each circuit then also gets a second, per-circuit low-voltage disconnect.
- **SBP rules (Victron manual):**
  - Never put the **inverter** on an SBP: its capacitive inrush trips the SBP's short-circuit protection ("E1").
  - Never put a **charging source** through one: reverse current damages it.
  - The SBP connects the load 1 s after the input closes and disconnects immediately when it opens.

## 4. HA automations this enables (examples)

- **Inverter:**
  - Set to *off* when no 230 V load is seen for 10 min.
  - *Charger only* on shore power.
  - *On* when the tablet or a button asks for it.
  - A 12/3000 idling uses 13 W (9 W in its energy-saving AES mode, 3 W in Search mode), about **0.3 kWh/day**.
- **Starlink:**
  - Off below 40% charge or when parked away (sentry).
  - On for 15 min when Frigate sees a person, so the alert reaches your phone.
  - The HA Starlink integration also gives stow, restart and power readings.
- **Leaving camp:** one "Leave" button turns the tent, cabin and rear USB off, and Starlink off or on schedule. The fridge stays on.
- **Low battery tiers:**
  - At 30%: Starlink, cabin and tent off.
  - At 15%: camera switch off, inverter off.
  - The PC's own BatteryProtect cut is the last backstop.
- **Heat:** tablet cut above 40 °C in the cabin; under-seat fan on above 45 °C.

## 5. Parts and cost (AUD inc GST)

| Item | Qty | Each | Total |
|---|---|---|---|
| Victron Smart BatteryProtect 12/24V-65A | 6 | about 70–97 (Jaycar MS6198 / Frankie's) | 420–582 |
| Victron GX IO-Extender 150 (2 latching relays 3 A, 1 solid-state output 4 A, 8 digital I/O) | 1 | 188.90 (Solar4RVs) | 189 |
| Shelly Plus Uni (9–28 VDC, 2 × 300 mA solid-state outputs, 2 inputs) | 1 | about 30–40 [est] | 35 |
| Contura ON-OFF-ON rockers with LED + actuators | 5 | about 40–50 [est] | 200–250 |
| 2-way ATC holder (rear USB/12 V), tablet relay, wire, ferrules | – | – | about 60 [est] |
| **Total** | | | **about A$900–1,100** |

**All-in-one alternative: Safiery STAR-Power** (A$1,009) + STAR-Switch Custom (A$272), about **A$1,280**.
- **What you get:** 6 × 30 A + 6 × 10 A dimmable channels, 12 backup buttons on the unit, and VE.Can into the Cerbo. It shows in the GX Switch pane, and Safiery says it works with HA.
- **Downsides:** standby draw isn't published, and it's one box: a failure takes out every circuit.
- **When it wins:** if you later want dimmable lighting circuits.

Other systems found and why they weren't chosen:
- **CZone Contact 6 Plus** (A$508, 0.3 mA standby): needs an NMEA 2000 network and Signal K for HA.
- **Garmin EmpirBus:** Switch pane only, no HA.
- **Redarc RedVision / Projecta:** no HA or open API.
- **Plain relay boards** (Waveshare, LILYGO, KinCony): cheap, but relay coils or ESP32s draw standby, and there's no per-circuit protection.

## 6. Things to check or decide

1. **Does HA's Victron GX integration expose the IO-Extender outputs?** The docs confirm the GX relays only. If it doesn't:
   - drive those contacts through Node-RED on the Cerbo, or define them as MQTT switches;
   - or use 2 more Shelly Plus Unis (HA-native) in place of the IO-Extender, which adds about 1 W standby each.
2. **Rear panel space.** Five more rockers is about 135 mm in a row [est] on a door that's 183.5 mm wide. It needs a layout pass, and possibly a second small switch panel inside the cabinet door.
3. **Starlink Mini and the fridge through an SBP-65.** Both are below its 65 A rating (250 A peak). Confirm that the startup surge doesn't trip it.
4. **Pick the defaults:** which circuits come back on after a power cut (latching vs NC vs NO) is set per circuit in the table above. Change it to suit.

## Sources

**Victron**
- https://www.home-assistant.io/integrations/victron_gx/ (inverter mode select, GX relay switches)
- https://www.victronenergy.com/upload/documents/MultiPlus-II_230V/32424-MultiPlus-II___Quattro-II-pdf-en.pdf (remote on/off, zero-load power)
- https://www.victronenergy.com/media/pg/Cerbo_GX/en/connecting-victron-products.html (DMC disables GX on/off)
- https://www.victronenergy.com/media/pg/Cerbo_GX/en/technical-specifications.html (relays 6 A at 30 VDC)
- https://www.victronenergy.com/blog/2026/02/25/introducing-venus-os-3-70/ (Switch pane)
- https://community.victronenergy.com/t/venus-os-v3-70-shelly-support/54232
- https://www.victronenergy.com/media/pg/GX_IO-Extender_150/en/technical-specifications.html
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
