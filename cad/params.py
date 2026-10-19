"""
Single source of truth for every dimension in the fit-out model (mm, kg).

Coordinate system (tub frame):
    X  = along the vehicle, 0 at the inner face of the tub FRONT wall, +X towards the tailgate
    Y  = across the vehicle, 0 on the centreline, +Y = DRIVER side (right, RHD), -Y = PASSENGER side
    Z  = up, 0 on the tub floor (top of the factory liner ribs)

Status flags in comments:
    [PUB]      published manufacturer figure
    [EST]      estimated from photos / drawings - MUST be verified on the vehicle
    [DES]      design choice (free to change)
    [CONFIRM]  assumption the owner needs to confirm
"""

VERSION = "v0.5"

# ================================================================ vehicle / tub
TUB_L = 1512           # [PUB] floor length, front wall -> closed tailgate (liner grades)
TUB_W = 1572           # [PUB] max width wall-to-wall
TUB_D = 540            # [PUB] depth floor -> top of tub rail
ARCH_GAP_PUB = 1186    # [PUB] between wheel arches (same for liner/no-liner grades -> likely bare steel)
LINER_ALLOW = 8        # [EST] liner thickness allowance per side over the arches
ARCH_GAP = ARCH_GAP_PUB - 2 * LINER_ALLOW   # 1170 design width between the arches
ARCH_L = 860           # [EST] arch length from the front wall (arches start AT the front wall)
ARCH_H = 290           # [EST] arch top height above the floor
ARCH_IN = (TUB_W - ARCH_GAP) / 2            # ~201 arch intrusion per side
ARCH_R = 70            # [EST] radius on the arch's top inboard edge
RIB_PITCH = 100        # [EST] liner floor rib pitch (ribs run fore-aft)
RIB_W = 45             # [EST] rib top width
RIB_H = 14             # [EST] rib height (Z=0 is the rib tops)
TAIL_BULGE_L = 0       # [owner] no tail-light bulge inside the tub
TAIL_BULGE_IN = 0
TAILGATE_T = 60        # [EST]
TAILGATE_H = TUB_D - 15
TUB_WALL_T = 55        # [EST] visual thickness of the side walls incl. liner
LID_CLEAR = 8          # [EST] tub rail -> underside of the Ute Master lid
# The lid CANNOT be opened with the tent on (weight): everything in the tub is reached from the tailgate.
UNDER_LID_Z = TUB_D + LID_CLEAR             # 548: hard ceiling for everything in the tub
BED_HOOKS = [          # [EST] 4 factory bed hooks (x, side, z) - side +1 driver / -1 passenger
    (ARCH_L - 140, 1, ARCH_H - 50), (ARCH_L - 140, -1, ARCH_H - 50),
    (TUB_L - 190, 1, 330), (TUB_L - 190, -1, 330)]
FACTORY_OUTLET = (1330, -1, 400)            # [EST] passenger wall, becomes the cable gland plate

# body context (only used for the context shell)
WHEELBASE = 3270       # [PUB]
REAR_AXLE_X = ARCH_L / 2                    # [EST]
FLOOR_ABOVE_GROUND = 920                    # [EST]
ROOF_Z = 1880 - FLOOR_ABOVE_GROUND          # [EST] roof skin; X-Pro height 1920 [PUB] incl. rails
CAB_REAR_X = -110                           # [EST] cab back wall -> ~55 mm gap to the tub front wall. MEASURE
CAB_FRONT_X = -1790                         # [EST] top of windscreen
TYRE_D = 810
TYRE_W = 265
CHASSIS_RAIL_Y = 470                        # [EST] chassis rail centre lines (+/-)
CHASSIS_Z = -150                            # [EST] top of chassis rail in tub frame
ENGINE_BAY_BATT = (-3050, -520, 120)        # [EST] start battery (passenger side of engine bay)
CABIN_SEAT_BOX = (-650, -380, 20)           # [EST] under rear seat outlet box location

# ================================================================ load lid + rack + tent
LID_L = 1600           # [EST]
LID_W = 1720           # [EST]
LID_T = 45             # [EST]
LID_X0 = -25           # [EST] lid front edge
LID_TOP_Z = UNDER_LID_Z + LID_T
LID_RAIL_H = 55        # [EST] Destroyer side rails
LID_RAIL_W = 45        # [EST]
LID_RAIL_Y = LID_W / 2 - 30                 # rail centre lines
TENT_GAP = 163.4       # [owner] lid top -> underside of tent = iPhone 17 Pro Max height (163.4 mm, Apple)
RACK_BAR = (79, 30)    # [PUB-ish] Rhino-Rack Vortex bar section (79 x 30), ~1.5 kg/m
RACK_BAR_X = (180, 1080)                    # [EST] crossbar centre lines (X)
RACK_BAR_L = 1500      # [EST] bar length
TENT_L = 1550          # [PUB] along vehicle
TENT_W = 1270          # [PUB] across vehicle
TENT_H = 330           # [PUB] 55 base/rails + 250 shell + 25 roof bars
TENT_BASE_H = 55
TENT_KG = 84           # [PUB]
TENT_X0 = -10          # [EST]
TENT_Z0 = LID_TOP_Z + TENT_GAP
TENT_FOLDOUT_SIDE = 1  # [CONFIRM] +1 = folds out to the DRIVER side, -1 = passenger side
TENT_SLOPE_L = 380     # [EST] the shell slopes down over this length at the front end [CONFIRM]
TENT_BAR_CC = 1040     # [EST] top bars c/c
TENT_BAR_L = 890       # [EST]
TENT_UNDER_RAILS_CC = 800    # [PUB] underside mounting rails c/c (run along X, 1440 long)
TENT_SERVICES = dict(x=240, inset=170, w=260, d=150, h=95)   # [DES] under-tent box near the front, inset

# ================================================================ batteries + electrical bay
BATT_L, BATT_W, BATT_H = 525, 240, 235      # [PUB] iTech400X Pro incl. terminals; any orientation except upside down
BATT_KG = 38
# Batteries stand ON END (525 tall), terminals facing the rear: footprint 240 (Y) x 235 (X).
# The inverter lies flat BESIDE them (Victron: not directly above batteries) - this keeps the bay shallow.
BAY_D = 320            # [DES] 235 battery + ~85 for terminal cable bends; inverter is 275 deep
BAY_W = ARCH_GAP - 6
BAY_H = 535            # [DES] rear posts / top rail (batteries on end are 525 + base)
INVERTER = (546, 275, 147)    # [PUB] Victron MultiPlus-II 12/3000/120-32 laid flat: along Y, along X, height
INVERTER_KG = 20              # [PUB] 2400 W @25 C / 2200 W @40 C, 5500 W peak, 120 A charger, 32 A transfer
SHUNT = (120, 46, 54)         # [PUB] SmartShunt 500 A
CLASS_T = (115, 70, 75)       # [EST] Blue Sea 5502 holder + 400 A Class-T (inverter feed, per Victron)
MRBF = (40, 35, 14)           # [EST] Blue Sea 5191 MRBF 300 A on each battery + terminal
BUSBAR = (200, 50, 45)        # [EST] Blue Sea PowerBar 600 A (bank +, system +, bank -, system -)
RBS = (110, 95, 100)          # [EST] Blue Sea ML-RBS 7713 remote battery switch 500 A (switched from the rear panel)
# charging board on the FRONT WALL above the inverter (vertical, terminals down): (along Y, thickness, height)
DCDC = (123, 40, 137)         # [PUB] Orion XS 12/12-50A x1, input current limit 1-50 A: start at 25-30 A
MPPT_ROOF = (130, 70, 186)    # [PUB] SmartSolar 100/30 (320 W roof array ~23 A; same case as 100/50)
MPPT_TENT = (113, 40, 100)    # [PUB] SmartSolar 75/15
CHARGE_BOARD_Z = 290          # [DES] bottom of the board: ~140 mm air gap above the inverter
# rear control cabinet (passenger, behind the arch): reached by opening the tailgate only
CERBO = (154, 48, 78)         # [PUB] Cerbo GX MK2
FUSE_BLOCK = (211, 45, 140)   # [EST] Blue Sea 5026 12-way with negative bus
GX_TOUCH = (128, 13, 87)      # [PUB] GX Touch 50

# ================================================================ slides (v0.5: side-mount runners, COVERED deck)
# Accuride DZ9308 runners on the cassette sides (as v0.3). Aluminium L-angles on top of the moving side
# members reach out over the runners, so the 15 mm ply deck covers the whole slide. The two decks meet in
# the middle (6 mm gap) - one continuous surface except the fridge well. The cable chain moves to a lane
# on the outboard side of the power slide.
SLIDE_X0 = BAY_D + 10
SLIDE_L = TUB_L - SLIDE_X0 - 8              # 1174
SLIDE_GAP_MID = 6                           # [DES] decks almost touch
CHAIN_LANE = 50                             # [DES] power slide outboard lane for the upright cable chain
RUNNER_T, RUNNER_H = 19.1, 76.2             # [PUB] Accuride DZ9308 (lock in + lock out)
RUNNER_LEN = 1168.4                         # [PUB] 46"
BASE_T = 6                                  # [DES] 6 mm base plates under the runners
SIDE_PLATE_T = 5
DECK_CLEAR = 2                              # [DES] deck lip clears the fixed runner plates by this much
LIP_T = 3                                   # [DES] L-angle horizontal leg (60 x 40 x 3) carrying the deck edges
DECK_T = 15                                 # [DES] 15 mm marine ply on top
DECK_BOT_Z = BASE_T + RUNNER_H + DECK_CLEAR + LIP_T   # 87.2
DECK_TOP_Z = DECK_BOT_Z + DECK_T                      # ~102
SLIDE_EXT = RUNNER_LEN
LTRACK_W, LTRACK_H = 35, 13                 # [PUB] heavy-duty airline track
RECEIVER_PITCH = 100                        # [DES] ball-lock receiver grid
RECEIVER_D = 22                             # [DES] flanged stainless bush OD (8 mm ball-lock pin)
LEG_INSET = 45                              # removable pin-in legs (stored in the lower utility drawer)
MICROWAVE_D = 332                           # [PUB] NCE 20 L depth (largest allowed)
BULKHEAD_D = 70                             # [DES] power pod: sockets face UP so plugs never foul the fridge
FRIDGE_WELL_L = SLIDE_L - BULKHEAD_D - MICROWAVE_D - 6   # 766 -> fridge <= ~756 long
FRIDGE_WELL_Z = 12                          # [DES] pan top surface -> ~536 under the lid
CHAIN_R, CHAIN_H, CHAIN_W = 63, 32, 40      # [EST] igus E2.26-class, R63 suits chain-rated 2.5 / 6 mm2 cable

# ================================================================ side bays
# Each side: LOWER cabinet/drawer behind the arch (floor -> arch height) + UPPER long drawer over the arch that
# runs the full tub length and pulls out of the back. Nothing needs the lid opened.
POCKET_X0 = ARCH_L + 5
POCKET_X1 = TUB_L - 6
POCKET_Y_IN = ARCH_GAP / 2 + 4              # inboard face of the side pockets
POCKET_Y_OUT = TUB_W / 2 - 4
TOP_Z = UNDER_LID_Z - 40                    # top of fixed furniture (40 mm clear under the lid)
LOWER_TOP_Z = ARCH_H                        # lower cabinets end level with the arch top
UPPER_Z0 = ARCH_H + 2                       # upper drawer carcass floor
UPPER_Z1 = UNDER_LID_Z - 38                 # 510: leaves a 28 mm cable tray band under the lid (passenger)
REAR_PANEL_X = TUB_L - 105                  # [DES] control/outlet panel recessed 105 mm so plugs clear the tailgate
CABLE_GAP = 22                              # [DES] passenger wall channel behind the upper drawer (gland drop)
UPPER_DRAWER_TRAVEL = 1000                  # [DES] 48" light-duty runners

# ================================================================ roof platform
PLAT_L = 1600          # [PUB] Wedgetail Adventure WT-KT-1614U
PLAT_W = 1450          # [PUB]
PLAT_Z = ROOF_Z + 70   # [PUB]
PLAT_T = 40
PLAT_X0 = CAB_REAR_X - 40 - PLAT_L
ROOF_PANEL_A = (1485, 668, 30)   # [PUB] Victron BlueSolar 190 W (driver half)
ROOF_PANEL_B = (1020, 668, 30)   # [PUB] Victron BlueSolar 130 W, 7.1 kg (no quality ~1200 mm panel exists)
PANEL_T = 30
CARGO_BAR_Z = 130
STARLINK_MINI = (298.5, 259, 38.5)    # [PUB]
TENT_PANEL = (1093, 552, 2)           # [PUB] Sunman eArc 100 W (x2 on ACM sheet)
