# House battery options: KickAss vs the iTech400X Pro (research, 2026-10-23)

The design currently uses 2 × iTechworld iTech400X Pro: 800 Ah in total, 2 × 38 kg, A$2,099 each on sale.

Each battery stands on end in the driver half of the front bay. That space is about **496 mm wide (Y) × 286 mm deep (X) × 535 mm tall**:
- Y is limited by the riser channel behind the busbars on one side and the bay side on the other.
- X is limited by the rear cable channel.
- Height is limited by the bay frame; the lid underside is at 548.

KickAss prices and specs below are from kickassproducts.com.au product pages and manuals, checked 2026-10-23.

## KickAss models that could replace the bank

| Bank | Capacity | Each: size (mm), weight | Continuous / peak (each) | Price for the bank | A$/Ah | Fits the bay? |
|---|---|---|---|---|---|---|
| **2 × Ultra-X 300 Ah Series 2** (KA12300UXG2-LION) | 600 Ah (7.7 kWh) | 242 × 180 × 460 (500 with brackets), 30 kg | 300 A / 660 A for 30 s | A$4,390 list; **A$3,390** at Club price (A$1,695 each; Club signup is free) | 7.3 list / 5.7 Club | **Yes**, standing on end, with ~136 mm of bay width to spare |
| 2 × Ultra-X 460 Ah (KA12460X-LION-C1) | 920 Ah (11.8 kWh) | 550 × 460 × 126, 48 kg | 300 A / 660 A for 30 s | A$4,590 | 5.0 | **No.** Standing upright it needs 550 mm of width (the bay has 496), and it must sit on the floor (only the newer revision allows upright mounting) |
| 2 × Ultra-X 230 Ah Compact | 460 Ah | 360 × 215 × 265 (with housing), 23.5 kg | 230 A / 430 A for 30 s | A$2,735 (twin bundle) | 5.9 | Yes, but only two fit, so a third (690 Ah) won't |
| 2 × 200 Ah standard | 400 Ah | 522 × 244 × 241, 20.4 kg | 200 A | A$1,677 (twin bundle) | 4.2 | Yes: same footprint as the iTech |
| 4 × Ultra-X 230 Ah Slimline | 920 Ah | 510 × 70 × 540 (with housing), 26.9 kg | 230 A | A$5,587 | 6.1 | **No:** 540 mm tall (the bay is 535) |
| *Current: 2 × iTech400X Pro* | *800 Ah (10.2 kWh)* | *525 × 240 × 235, 38 kg* | *200 A (640 A for 5 s)* | *A$3,992 (sale, 2026-10-23)* | *5.0* | *as designed* |

Sources:
- [Ultra-X 300 Ah Series 2](https://kickassproducts.com.au/products/kickass-smart-12v-300ah-ultra-x-lithium-compact-deep-cycle-battery-lifepo4) and its [manual](https://cdn.shopify.com/s/files/1/0845/2341/7879/files/KA12300UXG2-LION-USERMANUAL.pdf)
- [Ultra-X 460 Ah](https://kickassproducts.com.au/products/kickass-ultra-x-460ah-12v-deep-cycle-lithium-battery) and its [manual](https://cdn.shopify.com/s/files/1/0845/2341/7879/files/KA12460X-LION-C1-USERMANUAL.pdf)
- [Ultra-X 230 Ah Compact](https://kickassproducts.com.au/products/kickass-ultra-x-230ah-12v-deep-cycle-lithium-battery)
- [Ultra-X 230 Ah Slimline](https://kickassproducts.com.au/products/kickass-ultra-x-230ah-12v-deep-cycle-lithium-battery-slimline)
- [12V 200 Ah](https://kickassproducts.com.au/products/kickass-12v-200ah-deep-cycle-lithium-battery)
- [KickAss lithium range](https://kickassproducts.com.au/collections/lithium-batteries)

## The one worth considering: 2 × Ultra-X 300 Ah Series 2

**Better than the iTechs on:**
- **Size and weight:** 16 kg lighter, and it frees about 136 mm of bay width.
- **Case:** IP65 metal case with a 19 mm vent port. The manual lists AS/NZS 3001.2 among its certifications.
- **Mounting:** wall, floor or ceiling, as long as the label text isn't upside down. Standing on end like the iTechs is fine.
- **Monitoring:** Bluetooth, plus whole-bank monitoring over RJ45. The SmartShunt still feeds the Cerbo either way.
- **Warranty:** 7 years.
- **Cables:** M8 terminals, the same as now, so the bank cables carry over.

**Worse:**
- **Capacity: 600 Ah instead of 800 Ah**, which is 2.6 kWh less. The estimated daily use is about 150 Ah in summer and 210 Ah in winter (docs/weight-options.md), plus about 100 Ah for the smart-ute system when camped. Without solar, that's about 2 days instead of about 2.5–3.
- **Cost:** about A$400 more than the iTech sale price (A$1,996 each on 2026-10-23) at list. At Club price it's about A$600 cheaper.

**Same as the iTechs:**
- **Inverter:** the MultiPlus-II 12/3000 draws about 230 A at 2400 W and more on a short surge. Either bank covers that: 2 × 200 A for the iTechs, 2 × 300 A for the KickAss.
- **Cold charging:** neither can charge below 0 °C, and neither has self-heating.
- **Victron link:** neither BMS talks to Victron.

## Other rules to know (KickAss manuals)

- **Batteries in parallel must be the same model and the same production batch.** Buy both together. The build-stages tip to "buy one battery now and the second later" would not work with KickAss.
- **Before paralleling,** charge each battery to full on its own and let it rest 30 minutes. Use equal-length link cables.
- **Banks:** up to four in parallel or series, but not both at once.

## Recommendation

**Keep the iTechs if capacity matters most.** The 460 Ah Ultra-X is the only KickAss option with more capacity and a lower price per Ah, and it doesn't fit the bay without re-laying the distribution column.

**Switch to 2 × Ultra-X 300 Ah Series 2 at the Club price** if 600 Ah is enough. You'd get a lighter, smaller, better-sealed bank with a longer warranty, about A$600 cheaper. The model change is small: new battery dimensions, cable lengths and bay positions.
