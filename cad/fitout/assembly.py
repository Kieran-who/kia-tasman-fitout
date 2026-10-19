"""Assemble the whole vehicle for a given state."""
import params as P

from . import bay, lid_tent, modules, roof, side_bays, slides, vehicle, wiring
from .core import ANCHORS


def build(state="camp"):
    """state: 'travel' (slides stowed, tailgate shut) or 'camp' (slides out, tailgate down)."""
    ANCHORS.clear()
    camp = state == "camp"
    ext_p = P.SLIDE_EXT if camp else 0
    ext_d = P.SLIDE_EXT * 0.65 if camp else 0
    parts = []
    parts += vehicle.tub(tailgate_open=camp)
    parts += vehicle.body_context()
    parts += lid_tent.lid()
    parts += lid_tent.rack_and_tent()
    parts += bay.bay()
    parts += slides.slides(ext_p, ext_d)
    parts += side_bays.passenger(drawer_out=P.UPPER_DRAWER_TRAVEL * 0.9 if camp else 0)
    parts += side_bays.driver(drawer_out=420 if camp else 0, upper_out=P.UPPER_DRAWER_TRAVEL * 0.6 if camp else 0)
    parts += roof.roof()
    parts += modules.payload(ext_p, ext_d)
    parts += modules.edge_modules(ext_p, ext_d)
    wparts, cables = wiring.build()
    parts += wparts
    return parts, cables
