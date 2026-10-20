# Smart ute: hardware research (cameras, Frigate, Home Assistant, thermal, dashboard)

Status: **research, 2026-10-20.** Nothing here is in the model yet. **[est]** marks an estimate. Every other figure comes from the sources listed at the end. Many industrial parts are quote-only, so those AUD prices are estimates; get quotes before deciding.

## 1. Recommendation at a glance

| Part | Recommended | Why | Alternatives |
|---|---|---|---|
| Mini PC (under the rear seats) | **Neousys POC-751VTC** (i3-N305, fanless) | Built for vehicles: 8–35 V DC in, **ignition power control built in**, −40 to 70 °C, 4 × PoE+ ports | Cincoze DA-1200 (N97, 9–48 V, −40 to 70 °C, NVMe + 2.5" bay). Budget: Protectli VP2430 (N150) + Mini-Box DCDC-USB-200, but it's rated only −10 to 50 °C |
| Object detection | **OpenVINO on the Intel iGPU**, YOLOv9-t-320 at 5 fps | Mainstream Frigate path, no extra hardware. 7 cameras × 5 fps is well within an N-series iGPU (about 16 ms per frame on an N150) | Hailo-8L M.2 (about 11 ms) if a slot fits. Coral is "no longer recommended" for new installs |
| Software | **Home Assistant OS** on bare metal, **Frigate add-on**, Tailscale add-on | One box and one update path. The add-on can use the iGPU | Proxmox with HA OS in a VM and Frigate in Docker (only needed for an Intel NPU) |
| Front and rear cameras | **e-con RouteCAM_CU86_IP67** (Sony IMX678 STARVIS 2, 4K, 98.7° H) | Sensor confirmed in writing, **no illuminators**, IP67, vehicle-tested (ISO 16750-3/-4), PoE or 12 V, 3.8 W | Axis F9104-B Mk II + F2107-RE heads (vehicle-grade, premium). Hikvision ColorVu with its LED disabled (heavy, not vehicle-rated, sensor not named) |
| Side cameras (2 pairs, rear corners of the roof platform) | **4 × e-con RouteCAM_CU22_IP67** (IMX662 STARVIS 2, 1080p, 130° H) | 46 mm cube, 186 g, so two bolt back-to-back on one bracket; 2.8 W each | Axis F9104-B Mk II with 4 × F2105-RE heads (108°) |
| Thermal (forward) | **HIKMICRO HM-TD2638-15/G1** (384×288, 15 mm, about 17.5° H, 25 Hz, −40 to 70 °C, ONVIF) | Narrow lens to see far down the road, full RTSP for Frigate, wide temperature rating | Budget: Dahua TPC-BF1241 10 mm (256×192, 17.3°, 25/30 fps, only to +60 °C). Lowest latency: Hikvision DS-2TV03-10ZI analog kit (50 fps, A$7,241) + Axis M7104 encoder for Frigate |
| Thermal dash display | **Lilliput 719H/C** 7" (1000 nits, 9–36 V, IP65 frame), fed by a **dedicated Raspberry Pi 5** player | A Frigate or PC crash never blanks the driving aid. Tuned RTSP decoding gives about 150–300 ms glass-to-glass [est] | A 5" HDMI screen if 7" doesn't fit the binnacle (measure it) |
| Dashboard tablet | **Samsung Galaxy Tab S10 FE** (about 700 nits, IP68, 80% charge limit, 7 years of updates) + **Fully Kiosk Browser PLUS** | Brightest consumer option found; smooth enough for Frigate live view | Cheap: Galaxy Tab A11+ (about 500 nits, A$379). Can stay in the heat: **Galaxy Tab Active5** in "No Battery Mode" (battery removed) |
| PoE switch | **Teltonika TSW202** (8 × PoE+, managed, −40 to 75 °C) powered by a **Victron Orion-Tr 12/48-8A** | Full 240 W PoE budget, VLANs, and the Orion's remote on/off lets HA cut camera power by mode | Planet IGS-10020HPT (12–48 V in, but only 60 W PoE at 12 V) |
| Router | **Teltonika RUTX11** (4G dual-SIM, Wi-Fi 5, 9–50 V) | Owns the LAN and Wi-Fi, so everything works with Starlink off. Starlink Mini in bypass mode on WAN1, 4G on WAN2 | RUTX50 (5G); a non-cellular router if 4G backup isn't wanted |
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
     ├─ Neousys POC-751VTC (8–35 V direct, ignition input from an ACC tap)  ── 4 × PoE+: front, rear, thermal, Pi 5 player
     ├─ Orion-Tr 12/48-8A (remote on/off ← HA) ── TSW202 PoE switch ── 4 × side cams (roof), spare ports, uplinks
     ├─ Teltonika RUTX11 ── WAN1: Starlink Mini (bypass, Mini Ethernet cable) · WAN2: 4G SIM · Wi-Fi AP → tablet, phones
     └─ LAN: PC ↔ switch ↔ router; Cat6 to the tub rear cabinet → Cerbo GX (HA "Victron GX" integration, MQTT)
   dash: Lilliput 719H/C ← HDMI ← Raspberry Pi 5 (PoE HAT, low-latency player of the thermal RTSP) · tablet on a RAM X-Grip
   roof: Starlink Mini (existing DO4 feed) switched by relay K1 ← Cerbo relay 1 (HA), side camera pairs on the platform rear corners
   front: thermal + front camera on the bull bar (outside the glass, clear of the Tasman's front radar) · rear: camera on the tailgate/lid
VLANs: cameras (no internet) · management · users. Frigate records to a wide-temperature SSD in the PC.
```

- **Why it's split this way:**
  - **PC PoE ports** power the cab-end devices.
  - **The TSW202** takes the roof cameras and can be switched off to save power.
  - **The router** keeps the LAN up whatever Starlink is doing.
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
  - Front and rear: 4K at 6–8 Mbps. Sides: 1080p at 3–4 Mbps. Thermal: about 1 Mbps.
  - That's about **32 Mbps, or about 14 GB per hour** [est].
  - **A 2 TB wide-temperature SSD holds about 5 days continuous**, or 3 days continuous plus 14 days of motion clips [est].
  - Use industrial −40 to 85 °C SSDs (e.g. Transcend MTE712A-I). The WD Red SN700 has a high write endurance (TBW) but is rated only 0–70 °C.
- **Thermal:** goes into Frigate as an ordinary RTSP camera. Detection on thermal is optional; recording is the requirement.
- **Remote:** HA Companion app with the SgtBatten Frigate notification blueprint (snapshots, then clips). Cameras sit on a VLAN with no internet.

## 5. Power budget

Using measured or datasheet figures where they exist.

| Load | W | Basis |
|---|---|---|
| Neousys PC (HA + Frigate, 7 detect streams) | 15 | [est]. The i3-N305 is a 15 W TDP chip |
| 2 × CU86 + 4 × CU22 | 18.7 | e-con datasheets (3.78 / 2.78 W) |
| Thermal HM-TD2638 | 10 (12.1 max) | VIDEOR datasheet |
| TSW202 + Orion idle and losses | 7 | TSW202 <3 W idle, 8 W max; Orion idle about 2.6 W [est] |
| RUTX11 | 6 | [est] (the RUTX50 measures 5.2 W idle) |
| Pi 5 + Lilliput (driving at night only) | 13 | Lilliput ≤8.5 W; Pi [est] |
| Tablet (on) | 6 | [est] |
| Starlink Mini | 28 | 25–30 W reported |

| Mode | What's on | W | Wh/day | Share of the 10.2 kWh bank |
|---|---|---|---|---|
| Driving | Everything | about 104 | covered by the alternator and solar | – |
| Camped | PC, 6 cams, switch, router 24 h; Starlink 12 h; tablet 6 h; thermal off | about 47 + extras | about **1,500** | about 15% |
| Sentry (parked, away) | PC, 6 cams, switch, router (4G for alerts), Starlink off | about 47 | about **1,130** | about 7 days on 80% |
| Deep sentry | PC, front and rear cams, router | about 34 | about **820** | about 10 days |

The roof (570 W with the visor) and tent (200 W) solar covers the camped figure on a reasonable day.

## 6. Cost estimate (parts, AUD inc GST)

| Item | Recommended | Value build |
|---|---|---|
| Mini PC + 2 TB wide-temp SSD + RAM | 2,400–3,200 [est, Neousys quote-only] | 1,200–1,400 [est, Protectli + DCDC-USB + SSD + fan] |
| 6 × RouteCAM (US$2,074) incl. GST, shipping [est] | 3,500–3,800 | 3,500–3,800 (no cheaper STARVIS-confirmed option was found) |
| Thermal camera | 3,000–4,500 [est, no AU listing] | 800–1,400 [est, Dahua TPC-BF1241] |
| Pi 5 kit + PoE HAT + Lilliput 719H/C | about 600 [est] | about 600 [est] |
| TSW202 (A$278) + Orion-Tr 12/48 (A$288) | 566 | 566 |
| RUTX11 | 652 | 652 |
| Tablet + Fully Kiosk + RAM X-Grip + 30 W USB-C PD | about 1,050 (S10 FE) | about 650 (Tab A11+) |
| BatteryProtect, outdoor Cat6, IP67 glands, brackets, fuses | about 500 [est] | about 500 [est] |
| **Total** | **about A$12,300–14,900** | **about A$8,500–9,600** |

The cameras are the fixed cost: the RouteCAMs are the only cameras found with a STARVIS 2 sensor confirmed in writing and no illuminators. The other swings are the PC and the thermal camera.

## 7. Heat (the main risk)

- **How hot it gets:** a closed car rose from 36 °C to 67 °C in 15 minutes (Brisbane study), and the RAA reports up to 80 °C on a 40 °C day.
- **The limits:**
  - The best-rated parts here (Neousys, Cincoze, OnLogic, HIKMICRO thermal, RouteCAM) are rated to 65–70 °C.
  - Consumer tablets are rated 0–35 °C. Apple says not to leave an iPad in a car.
- **Under the seat:**
  - Mount the PC on an aluminium plate with its fins vertical.
  - Fit a 12 V thermostatic fan venting to the footwell, a temperature sensor, and reflective lining.
  - HA throttles detection or shuts down above about 75 °C in the box [est].
- **Tablet:**
  - Power it from an ACC-switched supply so it doesn't charge while heat-soaking.
  - Fully Kiosk "Sleep on power disconnect", Samsung battery protection at 80%, and an HA cut-off if the cabin goes above about 40 °C.
  - Mount it low and out of the sun. Pull it on heatwave days, or use the Active5 battery-less.
- **Cameras:** sun shields, white housings, an air gap from the roof skin.

## 8. Legal and safety

- **The thermal screen and road rule 299.** Rule 299 allows a display the driver can see if it is a "driver's aid" in a fixed mount: in a commercially designed mount (ACT) or affixed to the vehicle (NSW). The rule's examples include CCTV security cameras, rear-view screens and vehicle-monitoring devices.
  - Thermal night vision isn't named. Treating it as a driver's aid is a reasonable reading but untested, so confirm with your state's transport authority.
  - Show **only** the thermal feed on that screen.
  - Keep it low on the binnacle, out of airbag paths, and not blocking the road view (Victoria: 11 m ahead).
- **What thermal will and won't do:**
  - A WA operator on the Perth to Port Hedland run reported fewer kangaroo strikes with a FLIR dash unit, but it missed animals coming in from the side.
  - A NESP study found thermal gave about 30% more detections than spotlights at 15 °C, and little benefit above 30 °C ambient.
- **Thermal export rules:** faster than 9 Hz is export-controlled (6A003.b.4.b). Australia is covered by the EU general authorisation, so check the exact AU SKU's frame rate before paying.

## 9. To do before buying

1. **Quotes:**
   - Neousys POC-751VTC (AU distributor), with a wide-temperature 2 TB M.2 SATA SSD.
   - e-con RouteCAM ×6: ask about the sub-stream, IR-cut filter and AU shipping.
   - HIKMICRO HM-TD2638-15 or Dahua TPC-BF1241 10 mm: AU stock, and confirm the frame rate.
2. **Measure:** the binnacle space for the thermal screen (7" or 5"); the under-seat box (internal size and airflow); camera bracket points on the bull bar, tailgate and platform corners. These can be added to the measurement sheet.
3. **Check the front-radar cover zone** before placing anything on the bull bar.
4. **Decide:** 4G backup router or Wi-Fi only; Tailscale only or with Nabu Casa; the S10 FE (remove it in heat) or the Active5 (battery-less, 8").
5. **Bench-test** Frigate with OpenVINO on the chosen PC before installing. There's a GitHub report of an N100 restart-looping with OpenVINO.

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

**Road rules and field evidence**
- https://www.legislation.qld.gov.au/view/whole/html/inforce/2024-09-20/sl-2009-0194
- https://www.legislation.act.gov.au/DownloadFile/sl/2015-35/20151119-62378/PDF/2015-35.PDF
- https://ownersmanual.kia.com/full_webhelp/TK1/2026/en_GB/topics/t00417.html
- https://www.beefcentral.com/?p=128686
- https://www.nespthreatenedspecies.edu.au/publications-and-tools/effectiveness-of-thermal-cameras-compared-to-spotlights-for-counts-of-arid-zone-mammals-across-a-range-of-ambient-temperatures
