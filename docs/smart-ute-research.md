# Smart ute: hardware research (cameras, Frigate, Home Assistant, dashboard; thermal deferred)

Status: **research, 2026-10-20 (updated the same day: thermal camera and dash screen deferred, no 4G, cheaper tablet and network).** Nothing here is in the model yet. **[est]** marks an estimate. Every other figure comes from the sources listed at the end. Many industrial parts are quote-only, so those AUD prices are estimates; get quotes before deciding.

## 1. Recommendation at a glance

| Part | Recommended | Why | Alternatives |
|---|---|---|---|
| Mini PC (under the rear seats) | **Neousys POC-751VTC** (i3-N305, fanless) | Built for vehicles: 8–35 V DC in, **ignition power control built in**, −40 to 70 °C, 4 × PoE+ ports (it powers four of the cameras itself) | Cincoze DA-1200 (N97, 9–48 V, −40 to 70 °C, NVMe + 2.5" bay). Budget: Protectli VP2430 (N150) + Mini-Box DCDC-USB-200, but it's rated only −10 to 50 °C |
| Object detection | **OpenVINO on the Intel iGPU**, YOLOv9-t-320 at 5 fps | Mainstream Frigate path, no extra hardware. 7 cameras × 5 fps is well within an N-series iGPU (about 16 ms per frame on an N150) | Hailo-8L M.2 (about 11 ms) if a slot fits. Coral is "no longer recommended" for new installs |
| Software | **Home Assistant OS** on bare metal, **Frigate add-on**, Tailscale add-on | One box and one update path. The add-on can use the iGPU | Proxmox with HA OS in a VM and Frigate in Docker (only needed for an Intel NPU) |
| Front and rear cameras | **e-con RouteCAM_CU86_IP67** (Sony IMX678 STARVIS 2, 4K, 98.7° H) | Sensor confirmed in writing, **no illuminators**, IP67, vehicle-tested (ISO 16750-3/-4), PoE or 12 V, 3.8 W | Axis F9104-B Mk II + F2107-RE heads (vehicle-grade, premium). Hikvision ColorVu with its LED disabled (heavy, not vehicle-rated, sensor not named) |
| Side cameras (2 pairs, rear corners of the roof platform) | **4 × e-con RouteCAM_CU22_IP67** (IMX662 STARVIS 2, 1080p, 130° H) | 46 mm cube, 186 g, so two bolt back-to-back on one bracket; 2.8 W each | Axis F9104-B Mk II with 4 × F2105-RE heads (108°) |
| Thermal + dash display | **Deferred (phase 2)**, on cost | Options are kept in §10 | – |
| Dashboard tablet | **Xiaomi Redmi Pad 2 Pro** (12.1", about 550–580 nits, 12,000 mAh, 80% charge limit, updates to 2032) + **Fully Kiosk Browser PLUS** | Best value: confirmed charge limit, the fastest budget chip (Snapdragon 7s Gen 4), and about 17.5 h on a Wi-Fi browsing test, so it keeps the dashboard up for an evening without charging (§4b) | Brightest: Lenovo Idea Tab Plus (633–762 nits, A$399). Longest runtime, matte, 11": OPPO Pad SE (23 h, A$399). Premium: Galaxy Tab S10 FE. Can stay in the heat: Galaxy Tab Active5 (battery removed) |
| PoE switch | **Teltonika TSW101** (automotive, 9–30 V in, 4 × PoE, 60 W, −40 to 75 °C, A$125–147) for the 2 cameras the PC can't power | The PC's 4 PoE ports take the other 4. Cameras stay on the PC's own ports, so they're off the internet without needing VLANs. HA cuts the TSW101's 12 V feed by relay in deep sentry | With the budget PC (no PoE): 2 × TSW101. Managed with VLANs: Linovision POE-SWR612GM-SOLAR (70 W at 12 V, US$239). The previous TSW202 + Orion-Tr 12/48 (A$566) is no longer needed |
| Router (no 4G) | **Teltonika RUTM10** (Wi-Fi 5, 1 WAN + 3 LAN, 9–50 V, about 3–8 W, −40 to 75 °C, A$214–250) | Owns the LAN and Wi-Fi, so the tablet, HA and Frigate keep working with Starlink off. Starlink Mini in bypass mode on WAN | MikroTik hAP ax2 (Wi-Fi 6, about A$185, but 12–28 V in and only rated to 50 °C). The RUTX10 is end-of-life |
| Remote access | **Tailscale** (HA add-on as a subnet router) | Works behind Starlink's CGNAT; reaches HA, Frigate (port 8971), the router, the switch and the Cerbo | Nabu Casa (US$6.50/mo) for zero-config phone access. Cloudflare Tunnel's free-plan terms are a risk for video |

## 2. The "STARVIS 3" requirement

- **STARVIS 3 exists but you can't buy it in a camera yet.**
  - Sony announced the first STARVIS 3 sensor, the **IMX908**, on 17 March 2026: 1/2.8-type, 8.4 MP, 1.45 µm LOFIC pixels, 96 dB HDR from a single exposure, about 27% better low light than the IMX778. Samples were due at the end of March 2026.
  - So far it only exists as sample modules: Leopard Imaging (MIPI, backordered), Commonlands (minimum order 1,000) and a Linux driver patch from July 2026. **No IP camera with the IMX908 was found.**
- **STARVIS 2 is what can be bought now:** IMX585, IMX678, IMX662, IMX675, IMX664, IMX676.
- **Very few brands name their sensor.** Hikvision, Annke, Reolink and Axis don't publish the Sony part number. e-con (RouteCAM) and Videology do.
- **The plan:** fit STARVIS 2 RouteCAMs now. They take M12 lenses and are PoE, so a STARVIS 3 model can replace one camera at a time later on the same cable and bracket.
- **Ask e-con before ordering** (their pages don't answer these):
  1. Is there a **sub-stream**? If not, Frigate decodes the main stream with hardware acceleration and scales it for detection. That costs more decode [est] but is feasible for 2 × 4K + 4 × 1080p on an N305.
  2. Is there an **IR-cut filter**? Without one, daytime colour can shift.
  3. AU shipping, and a price for 6 units.

**"No IR" is often untrue.** Many "full colour" cameras have white or warm LEDs (ColorVu, Reolink, Dahua, Annke's automatic "soft light"). The RouteCAMs have no illuminators.

## 3. System architecture

```
House bank 12.8 V ── FB1 way 11 (new "SMT" feed, 15 A, via chassis route) ── BatteryProtect 65 A (hard LVD) ── under-seat box
   under-seat box (vented, thermostatic fan, temp sensor):
     ├─ Neousys POC-751VTC (8–35 V direct, ignition input from an ACC tap) ── 4 × PoE+: front, rear, 2 side cams
     │     ├─ LAN 1 → TSW101 uplink   (camera network: no internet, the PC is the only host)
     │     └─ LAN 2 → RUTM10 LAN      (home network: HA, Frigate UI, tablet, phones)
     ├─ TSW101 PoE switch (12 V via a relay ← HA, off in deep sentry) ── 2 side cams, 2 spare PoE ports
     ├─ Teltonika RUTM10 ── WAN: Starlink Mini (bypass, Mini Ethernet cable) · Wi-Fi AP → tablet, phones
     └─ Cat6 from the RUTM10 to the tub rear cabinet → Cerbo GX (HA "Victron GX" integration, MQTT)
   dash/console: tablet on a RAM X-Grip (12" cradle for 12.1" tablets), 30 W USB-C PD supply on an ACC-switched feed
   roof: Starlink Mini (existing DO4 feed) switched by relay K1 ← Cerbo relay 1 (HA), side camera pairs on the platform rear corners
   front: camera on the bull bar (outside the glass, clear of the Tasman's front radar) · rear: camera on the tailgate/lid
Frigate records to a wide-temperature SSD in the PC.
Spare for phase 2: a thermal camera on a TSW101 spare port.
```

- **Why it's split this way:**
  - **The PC's own PoE ports** run four cameras, and the small TSW101 takes the other two, so there's no 48 V boost converter.
  - **The cameras** sit on a network only the PC sees, so they can't reach the internet.
  - **The router** keeps the LAN up whatever Starlink is doing.
- **No 4G:** remote access and phone alerts only work while Starlink is on. Locally, everything works with Starlink off. HA can switch Starlink on for a while on a schedule, or when Frigate sees something and you want the alert out (see the sentry modes in §5).
- **Ignition sense:**
  - **PC:** uses its own input, wired from an ACC tap at the cab fuse box.
  - **Cerbo:** needs a relay contact or optocoupler. It must not get 12 V directly, because its inputs have 3.3 V pull-ups.
- **Starlink Mini:** sleep mode saves little (one review measured 25 W on a dish in "sleep"), so HA cuts it with a hard relay. Its startup peak is about 60–100 W.

## 4. Frigate configuration outline

- **Detect stream:** about 1280×720 or 640×360 at 5 fps. Record at full resolution, about 15 fps.
- **Codec:** H.264 for anything viewed in a browser through go2rtc, because WebRTC doesn't support H.265.
- **Hardware decode:** `preset-vaapi` / QSV.
- **Detector:**
  ```yaml
  detectors: {ov: {type: openvino, device: GPU}}
  model: {model_type: yolo-generic, width: 320, height: 320, input_tensor: nchw, input_dtype: float,
          path: /config/model_cache/yolo.onnx, labelmap_path: /labelmap/coco-80.txt}
  record: {enabled: true, continuous: {days: 3}, motion: {days: 14}}   # Frigate 0.17+ retention keys
  ```
- **Bitrates and storage:**
  - Front and rear: 4K at 6–8 Mbps. Sides: 1080p at 3–4 Mbps.
  - That's about **31 Mbps, or about 14 GB per hour** [est].
  - **A 2 TB wide-temperature SSD holds about 5 days continuous**, or 3 days continuous plus 14 days of motion clips [est].
  - Use industrial −40 to 85 °C SSDs (e.g. Transcend MTE712A-I). The WD Red SN700 has a high write endurance (TBW) but is rated only 0–70 °C.
- **Remote:** HA Companion app with the SgtBatten Frigate notification blueprint (snapshots, then clips). It works whenever Starlink is up.

## 4b. Dashboard tablet: budget options

All IPS LCD.
- **NBC** = Notebookcheck measurements. Its Wi-Fi runtime test runs at 150 nits, so expect less at full daylight brightness.
- **GSMA** = GSMArena's Active Use score.

| Tablet | AU price | Screen | Measured brightness | Battery / runtime | Chip | Updates | 80% charge limit |
|---|---|---|---|---|---|---|---|
| **Redmi Pad 2 Pro** (pick) | A$391 (Amazon AU, 6/128); A$479 Kogan (8/256) | 12.1" 2560×1600, 120 Hz | 547 (GSMA auto), 582 (NBC) | 12,000 mAh; NBC Wi-Fi 17:31; GSMA 12:55 | Snapdragon 7s Gen 4 | 5 OS upgrades, security to Oct 2032 | **Yes (GSMArena)** |
| Lenovo Idea Tab Plus | A$399 with pen (JB, was A$599); matte "Paper Like" A$549 | 12.1" 2560×1600, 90 Hz, glossy | **633 full white, 762 small areas (NBC)** | 10,200 mAh; NBC 14:51 | Dimensity 6400 | 2 OS, security to 2029 | not confirmed |
| OPPO Pad SE | A$399 (JB; JB lists a matte anti-reflective screen) | 11" 1920×1200, 90 Hz | 518 (NBC, glossy unit) | 9,340 mAh; **NBC 23:23** | Helio G100 | no policy published | not confirmed |
| Galaxy Tab A11+ (previous budget pick) | A$379 (JB) | 11" 1920×1200, 90 Hz | 537 (NBC) | 7,040 mAh; NBC 14:54 | Dimensity 7300 | security to Nov 2032 | Samsung "Maximum" protection (One UI 6.1+) |
| Redmi Pad 2 | A$287–297 (Amazon AU) | 11" 2560×1600, 90 Hz | 398 (NBC), 461 (GSMA) | 9,000 mAh; NBC 16:04 | Helio G100 Ultra | to Jun 2032 | not confirmed |
| TCL NXTPAPER 11 Plus | A$449 (JB) | 11.5" matte NXTPAPER | claimed 450–550 only; one review calls it "rather dark" | 8,000 mAh | Helio G100 | not found | not confirmed |

**Not recommended:**
- **Fire tablets:** Fully Kiosk has to be side-loaded, and there are forum reports of HA custom cards breaking on Fire's old web engine.
- **Not sold in AU:** Honor Pad X9a/X8a and OnePlus Pad Lite/Go 2.

**Why the Redmi Pad 2 Pro:**
- It's the only budget tablet with a confirmed 80% charge limit, which matters in a hot cab.
- It has the fastest chip in the group and updates to 2032.
- Its big battery keeps the dashboard up through an evening at camp without charging. The tablet only charges while the ignition is on.

**Things to check:**
- **Size:** it's 12.1", so it needs RAM's larger X-Grip cradle; the 10" kit takes up to 10.25" long. Check that it fits the dash or console spot.
- **Matte screen:** the matte version is 8/256 only, and an AU listing wasn't confirmed.
- **If 11" fits better:** the **OPPO Pad SE** has the longest runtime and a matte screen. The **Tab A11+** has the best update support.
- **If daylight glare is the biggest worry:** the **Lenovo Idea Tab Plus** is the brightest.

## 5. Power budget

Using measured or datasheet figures where they exist.

| Load | W | Basis |
|---|---|---|
| Neousys PC (HA + Frigate, 6 detect streams) | 15 | [est]. The i3-N305 is a 15 W TDP chip |
| 2 × CU86 + 4 × CU22 | 18.7 | e-con datasheets (3.78 / 2.78 W). 13.1 W on the PC's ports, 5.6 W on the TSW101 |
| TSW101 own draw | 3 | [est] |
| RUTM10 | 4 | 3.2 W idle, 7.6 W load at 12 V (Teltonika wiki) |
| Tablet (screen on, charging) | 6 | [est] |
| Starlink Mini | 28 | 25–30 W reported |

| Mode | What's on | W | Wh/day | Bank (10.2 kWh) |
|---|---|---|---|---|
| Driving | Everything | about 75 | covered by the alternator and solar | – |
| Camped | PC, 6 cams, switch, router 24 h; Starlink 12 h; tablet 6 h | about 41 + extras | about **1,350** | about 13% |
| Sentry, offline | PC, 6 cams, switch. Router and Starlink off; records locally, no phone alerts | about 37 | about **880** | about 9 days on 80% |
| Sentry with alerts | Same, plus router and Starlink so alerts reach your phone | about 69 | about **1,650** | about 5 days |
| Deep sentry | PC + its 4 cameras; TSW101 off | about 28 | about **675** | about 12 days |

The roof (570 W with the visor) and tent (200 W) solar covers the camped figure on a reasonable day.

## 6. Cost estimate (parts, AUD inc GST)

| Item | Recommended | Value build |
|---|---|---|
| Mini PC + 2 TB wide-temp SSD + RAM | 2,400–3,200 [est, Neousys quote-only] | 1,200–1,400 [est, Protectli VP2430 + DCDC-USB-200 + SSD + fan; rated only to 50 °C] |
| 6 × RouteCAM (US$2,074) incl. GST, shipping [est] | 3,500–3,800 | 3,500–3,800 (no cheaper STARVIS-confirmed option was found) |
| PoE: TSW101 (A$125–147) | 125–147 | 250–294 (2 × TSW101: the Protectli has no PoE) |
| Router: RUTM10 | 214–250 | 214–250 |
| Tablet: Redmi Pad 2 Pro + Fully Kiosk PLUS + RAM X-Grip (12") + 30 W USB-C PD | about 690–820 [mount est] | about 690–820 |
| BatteryProtect, relays, outdoor Cat6, IP67 glands, brackets, fuses | about 500 [est] | about 500 [est] |
| **Total** | **about A$7,400–8,700** | **about A$6,350–7,050** |

**Compared with the first version:**
- **Removed:** the thermal camera and its screen (A$3,600–5,100 before), and the 4G router.
- **Replaced:** the TSW202 + Orion-Tr with the PC's own PoE ports plus one TSW101.
- **Cheaper:** the tablet.
- **The cameras are now about half the total.** They're the only cameras found with a STARVIS 2 sensor confirmed in writing and no illuminators.

## 7. Heat (the main risk)

- **How hot it gets:** a closed car rose from 36 °C to 67 °C in 15 minutes (Brisbane study), and the RAA reports up to 80 °C on a 40 °C day.
- **The limits:**
  - The best-rated parts here are rated to 65–75 °C: Neousys, Cincoze and OnLogic PCs, RouteCAM, Teltonika TSW101 and RUTM10.
  - Consumer tablets are rated 0–35 °C. No review tested one in a hot car.
- **Under the seat:**
  - Mount the PC on an aluminium plate with its fins vertical.
  - Fit a 12 V thermostatic fan venting to the footwell, a temperature sensor, and reflective lining.
  - HA throttles detection or shuts down above about 75 °C in the box [est].
- **Tablet:**
  - Power it from an ACC-switched supply so it doesn't charge while heat-soaking.
  - Turn on the 80% charge limit, and use Fully Kiosk "Sleep on power disconnect".
  - Add an HA cut-off if the cabin goes above about 40 °C.
  - Mount it low and out of the sun, and pull it on heatwave days.
- **Cameras:** sun shields, white housings, an air gap from the roof skin.

## 8. Legal and safety

- **The tablet and road rule 299:** keep what the driver sees while moving to vehicle and power data. A reversing view counts as a driver's aid. Use a commercially designed mount, out of airbag zones.
- **Recording in public:** check your state's surveillance-devices rules for audio. These cameras are video-only.

## 9. To do before buying

1. **Quotes:**
   - Neousys POC-751VTC (AU distributor), with a wide-temperature 2 TB M.2 SATA SSD.
   - e-con RouteCAM ×6: ask about the sub-stream, IR-cut filter, **PoE class** (it decides how many cameras one 60 W TSW101 can power) and AU shipping.
2. **Measure:** the under-seat box (internal size and airflow); the tablet spot (12.1" or 11"); camera bracket points on the bull bar, tailgate and platform corners. These can be added to the measurement sheet.
3. **Check the front-radar cover zone** before placing anything on the bull bar.
4. **Decide:**
   - Tailscale only, or with Nabu Casa.
   - Tablet size.
   - Sentry with phone alerts (Starlink on, about 5 days) or offline (about 9 days).
5. **Bench-test** Frigate with OpenVINO on the chosen PC before installing. There's a GitHub report of an N100 restart-looping with OpenVINO.

## 10. Deferred: thermal camera and dash screen (phase 2)

Kept for later. The current design leaves a spare PoE port and a cable path at the bull bar for it.

- **Picks found:**
  - **HIKMICRO HM-TD2638-15/G1:** 384×288, 15 mm lens, 25 Hz, −40 to 70 °C, ONVIF. No AU listing; about A$3,000–4,500 [est].
  - **Budget: Dahua TPC-BF1241, 10 mm lens:** 256×192, 17.3°, 25/30 fps, rated only to 60 °C. About A$800–1,400 [est].
  - **Lowest latency: Hikvision DS-2TV03-10ZI analog kit:** 50 fps, A$7,241, plus an Axis M7104 encoder for Frigate.
- **Display path:** a dedicated Raspberry Pi 5 player into a Lilliput 719H/C 7" (1000 nits), about A$600. A crash in Frigate then never blanks the driving view. Expect about 150–300 ms delay [est].
- **Mounting:** outside the glass (glass blocks thermal), clear of the front radar.
- **Rule 299:** thermal isn't named in the rule. Treating it as a driver's aid is a reasonable reading but untested, so confirm with your state's transport authority. Show only the thermal feed on that screen.
- **What thermal will and won't do:**
  - A WA operator reported fewer kangaroo strikes with a FLIR dash unit, but it missed animals coming in from the side.
  - A NESP study found thermal gave about 30% more detections than spotlights at 15 °C, and little benefit above 30 °C ambient.
- **Export rules:** thermal faster than 9 Hz is export-controlled, so check the AU SKU's frame rate.

## Sources

**Frigate and HA**
- https://docs.frigate.video/configuration/object_detectors/
- https://docs.frigate.video/frigate/hardware
- https://docs.frigate.video/frigate/camera_setup
- https://docs.frigate.video/configuration/live
- https://docs.frigate.video/configuration/record
- https://docs.frigate.video/configuration/authentication
- https://www.home-assistant.io/integrations/victron_gx/
- https://www.home-assistant.io/integrations/starlink/
- https://www.home-assistant.io/integrations/fully_kiosk/
- https://github.com/lmagyar/homeassistant-addon-tailscale/blob/main/tailscale/DOCS.md
- https://www.nabucasa.com/pricing/
- https://community.home-assistant.io/t/frigate-mobile-app-notifications/311091

**Sensors**
- https://sony.mediaroom.com/2026-03-17-Sony-Semiconductor-Solutions-to-Release-4K-Image-Sensor-for-Security-Cameras-with-the-Industrys-Smallest-1-45-um-LOFIC-Pixels
- https://www.notebookcheck.net/Sony-launches-IMX908-4K-security-camera-sensor-with-single-exposure-HDR.1253498.0.html
- https://commonlands.com/pages/image-sensors/imx908
- https://framos.com/products/sensors/area-sensors/sony-starvis-2-imx585aamj1-c-27458/
- https://framos.com/en/products/sony-starvis-2-imx662aaqr-c-25935

**Cameras**
- https://www.e-consystems.com/gige-cameras/4k-sony-imx678-low-light-hdr-camera.asp
- https://www.e-consystems.com/gige-cameras/faq/4k-sony-imx678-low-light-hdr-camera-faq.asp
- https://www.e-consystems.com/gige-cameras/sony-starvis-imx662-2mp-ip67-camera.asp
- https://www.axis.com/en-nz/products/axis-f9104-b-mk-ii-main-unit
- https://www.axis.com/en-gb/products/axis-f2105-re-standard-sensor
- https://supportusa.hikvision.com/support/solutions/articles/17000129674-where-can-i-disable-the-supplemental-light-on-my-colorvu-camera-
- https://www.securitywholesalers.com.au/?p=51038

**Mini PC and power**
- https://www.bvm.co.uk/products/neousys-poc-751vtc-i3-n305-ultra-compact-in-vehicle-computer-with-4x-poe/
- https://www.elvac.eu/ipc/download/NEOUSYS/datasheet/poc-751vtc.pdf
- https://www.cnx-software.com/2024/04/01/cincoze-da-1200-fanless-industrial-embedded-computer-intel-n97-cpu-40-to-70c-temperature-range/
- https://protectli.com/product/vp2430/
- https://www.mini-box.com/DCDC-USB-200
- https://hailo.ai/products/hailo-8-m2-module
- https://outbackmarine.com.au/victron-batteryprotect-12-24v-65a
- https://uk.rs-online.com/web/p/hard-drives/2629734

**Thermal and display**
- https://www.videor.com/de/generate/datasheet/render/product_sku/245108/
- https://materialfile.dahuasecurity.com/uploads/soft/20250829/DHI-TPC-BF1241-S2-Project_datasheet_202508271.pdf
- https://www.securitywholesalers.com.au/product/hikvision-ds-2tv03-10zi-thermal-driving-assistance-system/
- https://www.axis.com/dam/public/4f/8e/39/datasheet-axis-m7104-video-encoder-de-DE-355638.pdf
- https://www.markertek.com/product/lil-719-c/lilliput-719-c-7-inch-1000-nit-highbright-4k-monitor-1280x800-hdmi-vga-usb-c
- https://www.axis.com/dam/public/2a/f4/90/eu-export-fact-sheet-–-eu-sensors-en-US-110634.pdf

**Network**
- https://www.farnell.com/datasheets/4785170.pdf (TSW202)
- https://www.solar4rvs.com.au/victron-orion-tr-12v-to-48v-8a-isolated-dc-dc-converter
- https://planet.spectra.de/media/7d/69/52/1627300657/Datasheet-IGS-10020HPT.pdf
- https://www.pbtech.com/au/product/NETTTK1011/Teltonika-RUTX11-4G-LET-CAT6-AC867-Dual-Band-WiFi
- https://wiki.teltonika-networks.com/view/RUTM10_Power_Consumption
- https://icit.net.au/product/rutm10000000-teltonika-rutm10-wired-with-4x-gigabit-ethernet-ports-dual-band-wi-fi-128-tag-port-based-vlans-psu-included/
- https://wiki.teltonika-networks.com/view/RUTX10 (end of life)
- https://wiki.teltonika-networks.com/view/TSW101_Power_Consumption
- https://www.pbtech.com/au/product/SWHTTK1101/Teltonika-TSW101-Unmanaged-Industrial-Ethernet-PoE
- https://linovision.com/products/12-ports-l2-cloud-managed-poe-switch-with-dc12v-to-dc48v-voltage-booster
- https://mikrotik.com/product/hap_ax2
- https://wiki.teltonika-networks.com/view/RUTX50_Power_Consumption
- https://teltonika-networks.com/resources/blogs/how-to-set-up-failover-for-starlink
- https://www.dishytech.com/how-to-bypass-the-starlink-router/
- https://www.victronenergy.com/media/pg/Cerbo_GX/en/technical-specifications.html

**Tablet**
- https://www.phonearena.com/reviews/samsung-galaxy-tab-s10-fe-review_id7116
- https://news.samsung.com/au/samsung-galaxy-tab-a11-now-available-delivering-powerful-entertainment-and-performance
- https://www.pbtech.com/au/product/TABSAM30611/Samsung-Galaxy-Active5-8-5G--WiFi-Rugged-IP68-Rate
- https://www.flightstore.com.au/ram-universal-x-grip-mount-kit-for-10-tablets
- https://samove.raa.com.au/can-you-cook-in-your-car/
- https://www.gsmarena.com/xiaomi_redmi_pad_2_pro-review-2891p3.php
- https://www.notebookcheck.com/Guenstiges-und-grosses-Tablet-mit-Android-20-Garantie-Test-Xiaomi-Redmi-Pad-2-Pro.1140069.0.html
- https://www.getprice.com.au/product/xiaomi-redmi-pad-2-pro-12.1-inch-tablet
- https://www.notebookcheck.com/Guenstiger-12-Zoll-Allrounder-mit-Stift-Schnellladen-Test-Lenovo-Idea-Tab-Plus-Tablet.1121650.0.html
- https://www.jbhifi.com.au/products/lenovo-idea-tab-plus-12-1-2-5k-256gb-tablet-pen
- https://www.notebookcheck.net/Battery-runtime-monster-with-bright-11-inch-display-outclasses-the-competition-Oppo-Pad-SE-tablet-in-review.1040657.0.html
- https://www.jbhifi.com.au/products/oppo-pad-se
- https://www.notebookcheck.net/Samsung-Galaxy-Tab-A11-5G-Review-High-performance-makes-this-Android-tablet-the-first-choice.1204979.0.html
- https://www.gsmarena.com/redmi_pad_2-review-2839p3.php
- https://www.jbhifi.com.au/products/tcl-nxtpaper-11-plus-11-2-2k-256gb-tablet
- https://community.home-assistant.io/t/fully-kiosk-browser/41675/165

**Road rules and field evidence**
- https://www.legislation.qld.gov.au/view/whole/html/inforce/2024-09-20/sl-2009-0194
- https://www.legislation.act.gov.au/DownloadFile/sl/2015-35/20151119-62378/PDF/2015-35.PDF
- https://ownersmanual.kia.com/full_webhelp/TK1/2026/en_GB/topics/t00417.html
- https://www.beefcentral.com/?p=128686
- https://www.nespthreatenedspecies.edu.au/publications-and-tools/effectiveness-of-thermal-cameras-compared-to-spotlights-for-counts-of-arid-zone-mammals-across-a-range-of-ambient-temperatures
