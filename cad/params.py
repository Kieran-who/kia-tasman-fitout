"""
Single source of truth for every dimension in the fit-out model (mm, kg).

Coordinate system (tub frame):
    X  = along the vehicle, 0 at the inner face of the tub FRONT wall, +X towards the tailgate
    Y  = across the vehicle, 0 on the centreline, +Y = DRIVER side (right, RHD), -Y = PASSENGER side
    Z  = up, 0 on the tub floor (top of factory liner ribs)

Status flags in comments:
    [PUB]  published manufacturer figure
    [EST]  estimated from photos / drawings - MUST be verified on the vehicle
    [DES]  design choice (free to change)
"""

# ---------------------------------------------------------------- vehicle / tub
TUB_L = 1512           # [PUB] floor length, front wall -> closed tailgate
TUB_W = 1572           # [PUB] max width wall-to-wall
TUB_D = 540            # [PUB] depth floor -> top of tub rail
ARCH_GAP_PUB = 1186    # [PUB] width between wheel arches (same figure for liner/no-liner grades -> likely bare steel)
LINER_ALLOW = 8        # [EST] factory liner thickness allowance per side over the arches
ARCH_GAP = ARCH_GAP_PUB - 2 * LINER_ALLOW   # 1170 design width used for everything between the arches
ARCH_L = 860           # [EST] arch length from front wall (arches start AT the front wall)
ARCH_H = 290           # [EST] arch top height above floor
ARCH_IN = (TUB_W - ARCH_GAP) / 2   # ~201 - arch intrusion per side (incl. liner allowance)
TAILGATE_T = 60        # [EST]
TUB_WALL_T = 55        # [EST] visual thickness of side walls incl. liner
LID_CLEAR = 8          # [EST] gap between tub rail and underside of Ute Master lid

# body context (only used for the context shell, not for fabrication)
WHEELBASE = 3270       # [PUB]
REAR_AXLE_X = ARCH_L / 2          # [EST] axle roughly central under the arch
FLOOR_ABOVE_GROUND = 920          # [EST]
ROOF_Z = 1880 - FLOOR_ABOVE_GROUND  # [EST] roof skin; X-Pro height 1920 [PUB] incl. bridge rails
CAB_REAR_X = -110                 # [EST] cab back wall relative to tub front wall
CAB_FRONT_X = -1790               # [EST] top of windscreen
TYRE_D = 810                      # [EST] X-Pro all-terrains
TYRE_W = 265

# ---------------------------------------------------------------- load lid + tent
LID_L = 1600           # [EST]
LID_W = 1720           # [EST]
LID_T = 45             # [EST]
LID_X0 = -25           # [EST] lid front edge
LID_RAIL_H = 55        # [EST] black ladder side rails on lid
TENT_L = 1550          # [PUB 23Zero drawing] along vehicle
TENT_W = 1270          # [PUB 23Zero drawing] across vehicle
TENT_H = 330           # [PUB 23Zero manual] 55 base/rails + 250 shell + 25 roof bars
TENT_KG = 84           # [PUB]
TENT_BAR_CC = 1040     # [EST from drawing] top bars c/c
TENT_BAR_L = 890       # [EST from drawing]
TENT_X0 = -10          # [EST]
TENT_TOP_SOLAR_MAX_KG = 20  # [user]

# ---------------------------------------------------------------- batteries + electrical bay
BATT_L, BATT_W, BATT_H = 525, 240, 235   # [PUB] iTech400X Pro incl. terminals, 38 kg each
BATT_KG = 38
BAY_D = 300            # [DES] depth of front electrical bay (X)
BAY_W = ARCH_GAP - 6   # [DES] fits between arches with 3 mm each side
BAY_H = 470            # [DES] height of bay frame (below lid)
BAY_DECK_Z = 255       # [DES] component deck above batteries

# placeholder envelopes for components (L(Y) x D(X) x H(Z)) - refined after datasheet research
# envelopes as (along Y, along X, height Z) for flat-mounted parts, (along X, thickness, height) for board-mounted
INVERTER = (546, 275, 147)       # [PUB] Victron MultiPlus-II 12/3000/120-32, 19 kg - mounted FLAT + forced-air fan
LYNX_CT = (170, 280, 97)         # [PUB] Lynx Class-T Power In (400 A Class-T)
LYNX_DIST = (170, 290, 80)       # [PUB] Lynx Distributor (4 x MEGA fuses)
SHUNT = (120, 46, 54)            # [PUB] SmartShunt 500 A (on the bank negative)
# charging board (vertical, above the passenger wheel arch) - all must mount vertically, terminals down
DCDC = (123, 40, 137)            # [PUB] Orion XS 12/12-50A  x2 in parallel = 100 A
MPPT_ROOF = (130, 70, 186)       # [PUB] SmartSolar 100/50
MPPT_TENT = (113, 40, 100)       # [PUB] SmartSolar 75/15
CERBO = (154, 48, 78)            # [PUB] Cerbo GX MK2
GX_TOUCH = (128, 13, 87)         # [PUB] GX Touch 50 (on the rear power panel)

# ---------------------------------------------------------------- slides
SLIDE_X0 = BAY_D + 10            # [DES] slides start behind the bay
SLIDE_L = TUB_L - SLIDE_X0 - 8   # cassette length (~1194)
SLIDE_GAP_MID = 6                # [DES]
CASSETTE_W = (ARCH_GAP - 2 * 3 - SLIDE_GAP_MID) / 2   # ~587 per slide
RUNNER_T, RUNNER_H = 19.1, 76.2  # [PUB] Accuride DZ9308 (lock in+out, outer) + DZ9301 (centre keel)
RUNNER_LEN = 1117.6              # [PUB] 44" - 218 kg/pair moderate use; 2 pairs per slide
KEEL_T = 6                       # [DES] centre keel plate carrying the second runner pair
BASE_RAIL_H = 12                 # [DES] base plate/rail under runners (sits on liner ribs)
SIDE_PLATE_T = 5                 # [DES] fixed runner mounting angle
CARRIAGE_W = CASSETTE_W - 2 * (SIDE_PLATE_T + RUNNER_T + 1)
DECK_T = 15                      # [DES] 15 mm marine/hoop-pine ply
DECK_TOP_Z = BASE_RAIL_H + RUNNER_H + DECK_T - 5   # ~98
SLIDE_EXT = RUNNER_LEN           # 100% extension
LTRACK_W = 30                    # [EST] L-track width (flush, recessed)
RECEIVER_PITCH = 100             # [DES] module receiver grid pitch
RECEIVER_D = 22                  # [DES] countersunk receiver diameter

# ---------------------------------------------------------------- side bays
POCKET_X0 = ARCH_L + 5           # behind the arch
POCKET_X1 = TUB_L - 10
POCKET_W = ARCH_IN - 8           # ~185
WATER_TOP_Z = 505                # [DES] top of water tank below lid
WATER_REAR_GAP = 95              # [DES] space at tank rear for pump + tap + hose
WALL_T_POLY = 8                  # [DES] tank wall thickness (welded PE)

# ---------------------------------------------------------------- roof platform
PLAT_L = 1600          # [PUB] Wedgetail Adventure WT-KT-1614U (Tasman fit kit WTM-KT-1614)
PLAT_W = 1450          # [PUB]
PLAT_Z = ROOF_Z + 70   # [PUB] sits ~70 mm off the roof
PLAT_T = 40            # [EST] typical slimline profile
PLAT_X0 = CAB_REAR_X - 40 - PLAT_L
ROOF_PANEL = (1485, 668, 30)   # [PUB] Victron BlueSolar 190 W, 10.5 kg - two side by side
TENT_PANEL = (1093, 552, 2)    # [PUB] Sunman eArc 100 W flexible, ~2 kg - two on an ACM backing sheet
PANEL_T = 35
CARGO_BAR_Z = 130      # [DES] removable cargo bars sit this far above the platform
STARLINK_MINI = (298.5, 259, 38.5)   # [PUB]
