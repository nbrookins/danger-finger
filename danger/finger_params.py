#!/bin/python
# pylint: disable=C0302, line-too-long, unused-wildcard-import, wildcard-import, invalid-name, broad-except
'''
The danger_finger copyright 2014-2026 Nicholas Brookins and Danger Creations, LLC
http://dangercreations.com/prosthetics :: http://www.thingiverse.com/thing:1340624
Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 https://creativecommons.org/licenses/by-nc-sa/4.0/
Source code licensed under Apache 2.0:  https://www.apache.org/licenses/LICENSE-2.0'''
import math
import inspect
from solid2 import *
from danger.constants import *
from danger.Params import *
from danger.tools import *


def orient_pair(distal_val, proximal_val):
    """Shorthand for {Orient.DISTAL: distal_val, Orient.PROXIMAL: proximal_val}."""
    return {Orient.DISTAL: distal_val, Orient.PROXIMAL: proximal_val}


# ********************************** The danger finger *************************************
class DangerFingerParams:
    ''' The available config options'''
    # ************************************* control params *****************************************
    preview_cut = Prop(val=False, doc=''' cut the preview for inset view ''', hidden=True)
    preview_rotate = False
    scad_render = True

    @staticmethod
    def _render_quality_setter(prop, obj, value):
        '''convert string to RenderQuality enum if needed'''
        return RenderQuality[value] if isinstance(value, str) else value

    @staticmethod
    def _bumper_style_setter(prop, obj, value):
        '''convert string to BumperStyle enum if needed'''
        return BumperStyle[value] if isinstance(value, str) else value

    render_quality = Prop(val=RenderQuality.EXTRAMEDIUM, doc='''- auto to use fast for preview.  higher quality take much longer for scad rendering''', adv=True, setter=_render_quality_setter, hidden=True)

    # **************************************** parameters ****************************************
    intermediate_length = Prop(val=24, minv=8, maxv=30, custom=CustomType.SLIDER, name="intermediate_length", doc=''' length of the intermediate finger segment ''')
    intermediate_distal_height = Prop(val=9.5, minv=4, maxv=16, custom=CustomType.SLIDER, name="intermediate_distal_height", doc=''' height of the middle section at the distal end.  roughly the height of the hinge circle ''')
    intermediate_proximal_height = Prop(val=11.0, minv=4, maxv=16, custom=CustomType.SLIDER, name="intermediate_proximal_height", doc=''' height of the middle section at the proximal end.  roughly the height of the hinge circle ''')
    intermediate_bumper_width = Prop(val=3.6, minv=0, maxv=20, custom=CustomType.SLIDER, name="intermediate_bumper_width", doc=''' width of optional bumper around middle section ''')
    intermediate_bumper_style= Prop(val=BumperStyle.COVER, setter=_bumper_style_setter, doc='''style of bumper around middle section: NONE, MINIMAL, COVER, or FULL''')
    knuckle_tendon_offset = Prop(val=3.0, minv=0, maxv=10, custom=CustomType.SLIDER, name="knuckle_tendon_offset", doc='''vertical offset of tendon anchor on base; 0 disables the bulge''')

    proximal_length = Prop(val=-.5, minv=-2, maxv=30, custom=CustomType.SLIDER, name="proximal_length", doc=''' length of the proximal/base finger segment ''') #TODO 3 - dynamic min auto of knuckle radius
    distal_length = Prop(val=24.0, minv=8, maxv=30, custom=CustomType.SLIDER, name="distal_length", doc=''' length of the distal/tip finger segment ''')
    distal_base_length = Prop(val=6.0, minv=0, maxv=20, custom=CustomType.SLIDER, name="distal_base_length", doc=''' length of the base of the distal/tip finger segment ''')

    knuckle_proximal_width = Prop(val=18.5, minv=10, maxv=28, custom=CustomType.SLIDER, name="knuckle_proximal_width", doc=''' width of the proximal knuckle hinge''')
    knuckle_distal_width = Prop(val=16.0, minv=10, maxv=28, custom=CustomType.SLIDER, name="knuckle_distal_width", doc=''' width of the distal knuckle hinge ''')
    tip_circumference = Prop(val=47, minv=4, maxv=100, custom=CustomType.SLIDER, name="tip_circumference", doc=''' circumference of tip ''')

    socket_depth = Prop(val=34, minv=5, maxv=60, doc=''' length of the portion that interfaces socket and base ''')
    socket_bottom_cut = Prop(val=9, minv=0, maxv=60, doc='''radius of the bottom cutout on the socket; larger values remove more material from the palm side''')

    socket_circumference_distal = Prop(val=57.3, minv=20, maxv=160, doc='''circumference of the socket closest to the base''')
    socket_circumference_proximal = Prop(val=63.4, minv=20, maxv=160, doc='''circumference of the socket closest to the hand''')
    #1.6
    socket_thickness_distal = Prop(val=1.9, minv=.5, maxv=4, doc='''thickness of the socket closest to the base''') #from 1.2
    socket_thickness_middle = Prop(val=1.6, minv=.5, maxv=4, doc='''thickness of the socket at interface''') #from .42
    socket_thickness_proximal = Prop(val=.85, minv=.5, maxv=4, doc='''thickness of the socket at flare''') #from .42

    linkage_length = Prop(val=70, minv=10, maxv=120, doc=''' length of the wrist linkage ''')

    socket_scallop_depth_left = Prop(val=10, minv=-10, maxv=20, adv=True, doc='''depth of the left scallop cutout on the socket; negative values disable''')
    socket_scallop_depth_right = Prop(val=0, minv=-10, maxv=20, adv=True, doc='''depth of the right scallop cutout on the socket; 0 for symmetric with left''')

    # Advanced
    stand_depth_factor = Prop(val=.8, minv=0, maxv=2, adv=True, doc='''ratio of stand depth to socket_depth; 0 for minimal stand, >1 extends past socket''')
    linkage_width = Prop(val=7.0, minv=4, maxv=12, adv=True, doc=''' width of the wrist linkage ''')
    linkage_height = Prop(val=4.3, minv=3, maxv=8, adv=True, doc=''' thickness of the wrist linkage ''')

    tip_print_depth = Prop(val=.4, minv=-2, maxv=2, adv=True, doc='''depth of fingerprint ridges on the tipcover; negative inverts the pattern''')
    tip_print_width = Prop(val=.61, minv=0, maxv=2, adv=True, doc='''width of each fingerprint ridge stripe on the tipcover''')

    linkage_hook_length = Prop(val=9.0, minv=4, maxv=12, adv=True, doc='''overall length of the wrist hook at the end of the linkage''')
    linkage_hook_height = Prop(val=4.5, minv=4, maxv=12, adv=True, doc='''height (vertical extent) of the wrist hook''')
    linkage_hook_thickness = Prop(val=1.5, minv=0, maxv=12, adv=True, doc='''wall thickness of the wrist hook loop''')
    linkage_hook_opening = Prop(val=.3, minv=0, maxv=12, adv=True, doc='''gap opening of the wrist hook for the elastic band''')
    linkage_hook_offset = Prop(val=.05, minv=0, maxv=12, adv=True, doc='''vertical offset of the hook relative to the linkage center''')
    linkage_hook_inset = Prop(val=-.5, minv=-1, maxv=12, adv=True, doc='''how far the hook is inset into the linkage body; negative extends outward''')
    linkage_hook_rounding = Prop(val=.9, minv=0, maxv=12, adv=True, doc='''rounding radius applied to the hook and linkage ends''')
    linkage_hook_end_inset = Prop(val=.7, minv=0, maxv=12, adv=True, doc='''inset at the inner tip of the hook opening''')
    linkage_flat = Prop(val=.5, minv=0, maxv=12, adv=True, doc='''flat extension added to the linkage width (flattens the oval cross-section)''')
    linkage_hole_spacing = Prop(val=4, minv=0, maxv=12, adv=True, doc='''spacing between cross-holes along the linkage for tension adjustment''')
    linkage_holes = Prop(val=5, minv=0, maxv=24, adv=True, doc='''number of cross-holes in the linkage; 0 disables holes''')

    tunnel_height = Prop(val=2.0, minv=0, maxv=5, adv=True, doc=''' height of tendon tunnel ''')
    tunnel_inner_height = Prop(val=.75, minv=0, maxv=4.5, adv=True, doc=''' additional height of the inner (middle section) tendon tunnel above the hinge center ''')
    tunnel_radius = Prop(val=1.6, minv=0, maxv=4, adv=True, doc=''' radius of tendon tunnel rounding ''')
    tunnel_inner_slant = Prop(val=0.0035, minv=0, maxv=4, adv=True, doc=''' inward slant of middle tunnels ''')
    tunnel_outer_slant = Prop(val=0.0085, minv=0, maxv=4, adv=True, doc=''' inward slant of outer tunnels ''')
    tunnel_outer_flare = Prop(val=0.7, minv=0, maxv=5, adv=True, doc=''' outward slant of outer tunnels back ''')

    knuckle_proximal_thickness = Prop(val=3.5, minv=1, maxv=5, adv=True, doc=''' thickness of the hinge tab portion on proximal side  ''')
    knuckle_distal_thickness = Prop(val=3.0, minv=1, maxv=5, adv=True, doc=''' thickness of the hinge tab portion on distal side ''')
    knuckle_inset_border = Prop(val=2.0, minv=0, maxv=5, adv=True, doc=''' width of the hinge inset, same as top strut width ''')
    knuckle_inset_depth = Prop(val=1.0, minv=0, maxv=3, adv=True, doc=''' depth of the inset to clear room for tendons ''')

    knuckle_pin_radius = Prop(val=1.12, minv=0, maxv=3, adv=True, doc=''' radius of the hinge pin/hole ''')
    knuckle_plug_radius = Prop(val=3.0, minv=2, maxv=5, adv=True, doc=''' radius of the hinge pin cover plug ''') #TO-DO dynamic contraints?, must be less than hinge radius
    knuckle_plug_thickness = Prop(val=1.3, minv=0.5, maxv=4, adv=True, doc=''' thickness of the hinge pin cover plug ''')
    knuckle_plug_ridge = Prop(val=.3, minv=0, maxv=1.5, adv=True, doc=''' width of the plug holding ridge ''')
    knuckle_plug_clearance = Prop(val=.1, minv=-.5, maxv=1, adv=True, doc=''' clearance of the plug ''')

    knuckle_clearance = Prop(val=.6, minv=-.25, maxv=1, adv=True, doc=''' clearance of the rounded inner part of the hinges ''')
    knuckle_side_clearance = Prop(val=.12, minv=-.25, maxv=1, adv=True, doc=''' clearance of the flat circle side of the hinges ''')

    knuckle_rounding = Prop(val=0.9, minv=0, maxv=4, adv=True, doc=''' amount of rounding for the outer hinges ''')
    knuckle_cutouts = Prop(val=True, adv=True, doc=''' True for extra cutouts on internals of intermediate section ''', hidden=True)
    knuckle_washer_radius = Prop(val=1.75, minv=0, maxv=4, adv=True, doc=''' radius of the washers for lowering hinge friction ''')
    knuckle_washer_thickness = Prop(val=.38, minv=0, maxv=4, adv=True, doc=''' thickness of the washers for lowering hinge friction ''')
    knuckle_washer_width = Prop(val=.4, minv=0, maxv=4, adv=True, doc=''' width of the washers for lowering hinge friction ''')
    knuckle_brace_height_factor = Prop(val=.3, minv=0, maxv=2, adv=True, doc='''ratio of brace height vs regular struts, e.g. .5 for half the height''')

    socket_interface_length = Prop(val=7.8, minv=3, maxv=8, adv=True, doc=''' length of the portion that interfaces socket and base ''')
    socket_interface_radius_distal = Prop(val=7.20, minv=5, maxv=10, adv=True, doc='''radius of the socket-to-base interface at the distal (finger) end''')
    socket_interface_radius_proximal = Prop(val=8.75, minv=5, maxv=10, adv=True, doc='''radius of the socket-to-base interface at the proximal (hand) end''')
    socket_interface_clearance = Prop(val=.03, minv=-2, maxv=2, adv=True, doc='''gap between base and socket interface surfaces; negative for interference fit''')
    socket_interface_thickness = Prop(val=.65, minv=.25, maxv=4, adv=True, doc='''wall thickness of the socket interface cylinder''')
    socket_interface_depth = Prop(val=1.0, minv=-2, maxv=4, adv=True, doc='''depth of the inner cutout sphere in the socket interface''')

    socket_interface_ridges = Prop(val=9, minv=0, maxv=32, adv=True, doc='''number of vertical ridges on the socket interface for grip; 0 disables''')
    socket_interface_cuts = Prop(val=True, adv=True, doc='''enable radial cuts on the socket interface for flex/grip''')
    socket_interface_ridge_width = Prop(val=.6, minv=0, maxv=4, adv=True, doc='''width of each ridge on the socket interface''')
    socket_interface_ridge_inner = Prop(val=-.016, minv=-.5, maxv=0, adv=True, doc='''inward scale factor for inner ridge layer; negative shrinks slightly''')
    socket_interface_ridge_outer = Prop(val=.02, minv=0, maxv=.5, adv=True, doc='''outward scale factor for outer ridge layer''')

    intermediate_bottom_width_factor = Prop(val=.5, minv=0, maxv=2, adv=True, doc='''ratio of bottom strut width to intermediate inner width; 0 removes bottom strut''')
    intermediate_tunnel_length = Prop(val=2, minv=-.25, maxv=2, adv=True, doc='''0-2 for the length of tunnels toward middle''')
    distal_flange_height = Prop(val=.5, minv=0, maxv=10, adv=True, doc='''height of the flange between base core and socket interface''')
    tunnel_inner_rounding = Prop(val=0.5, minv=0, maxv=4, adv=True, doc=''' amount of rounding for the inner tunnel ''')
    tendon_hole_radius = Prop(val=1.1, minv=0, maxv=5, adv=True, doc='''radius of the tendon routing holes through the base''')
    tendon_hole_width = Prop(val=2.2, minv=0, maxv=5, adv=True, doc='''width (Z extent) of the tendon routing holes''')

    tipcover_thickness = Prop(val=.95, minv=0, maxv=5, adv=True, doc='''wall thickness of the flexible tipcover shell; depends_on: tip_circumference''')
    tip_interface_clearance = Prop(val=.3, minv=0, maxv=5, adv=True, doc='''clearance gap between tip and tipcover snap-fit interface''')
    tip_interface_ridge_radius = Prop(val=.875, minv=0, maxv=5, adv=True, doc='''radius of the snap-fit ridge on the tip interface; depends_on: tipcover_thickness''')
    tip_interface_ridge_height = Prop(val=1.55, minv=0, maxv=5, adv=True, doc='''height of the snap-fit ridge that locks the tipcover to the tip''')
    tip_interface_post_height = Prop(val=1.7, minv=0, maxv=5, adv=True, doc='''height of the central post on the tip that the tipcover snaps onto''')

    strut_height_ratio = Prop(val=1.15, minv=.1, maxv=3, adv=True, doc=''' ratio of strut height to width (auto-controlled).  fractions make the strut thinner ''')
    strut_rounding = Prop(val=.3, minv=0, maxv=2, adv=True, doc=''' 0 for no rounding, 1 for fully round ''')
    strut_inset_distal = Prop(val=0.2, minv=0, maxv=5, adv=True, doc='''inward inset of the distal strut anchors; moves struts away from the edge''')
    strut_inset_proximal = Prop(val=-.2, minv=-1, maxv=5, adv=True, doc='''inward inset of the proximal strut anchors; negative extends outward''')
    tip_print_factor = Prop(val=4.3, minv=0, maxv=10, adv=True, doc='''sphere radius multiplier for the fingerprint pattern on the tipcover; depends_on: tip_circumference''')
    tip_print_offset = Prop(val=3, minv=0, maxv=10, adv=True, doc='''Y offset for the fingerprint pattern sphere positioning''')

    # super advanced
    render = Prop(val=False, doc=''' render STL ''', hidden=False)
    intermediate_strut_rotate = Prop(val=-25, minv=-50, maxv=20, adv=True, doc='''rotation angle of the bottom strut on the middle section; affects fist clearance''')

    _translate_offsets = {"all":{"middle":((0, 0, 0),), "base" : ((0, 0, 0),), "tip":((0, 0, 0),), "socket":((0, 0, 0),),"peg":((0, 45, 20),), "linkage" : ((0, 0, 20),), "bumper": ((0, 0, 0),),"tipcover" : ((0, 0, 0),), "stand" : ((0, -30, 0),), "plug":((0, 0, -18),), "plugs":((0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0))},
                            "explode":{"middle":((0, 12, 0),), "base" : ((0, 0, 0),), "tip":((0, 23, 0),), "socket":((0, -12, 0),),"peg":((0, 52, 0),), "linkage" : ((0, 0, 26),), "bumper": ((15, 0, 0),), "tipcover" : ((0, 38, 0),), "stand" : ((0, -60, 0),), "plug":((0, 0, -18),), "pins":((0, 12, -30), (0, 0, -30))}}
    _rotate_offsets = {
        "socket":(-90, 0, 0),"base":(90, 0, 0), "tip":(-90, 0, 0), "tipcover":(90, 0, 0), "linkage":(0, -180, 0), "stand":(90, 0, 0), "peg":(-90, 0, 0), "middle":(90, -50, 90),

        "all":{"middle":((0, 0, 35),), "base" : ((0, 0, 0),), "bumper":((0, 0, 35),), "tip":((0, 0, 35),), "socket":((0, 0, 0),),
            "linkage" : ((0, 0, 0),), "tipcover" : ((0, 0, 35),)}}

    # Web viewer preview: inverse print rotations to show parts in assembled orientation
    # middle: true matrix inverse of Rx(90)*Ry(-50)*Rz(90) gives py=-90, pz+px=-140; start (0,-90,-140)
    _preview_rotate_offsets = {
        "socket": (90, 0, 0), "base": (-90, 0, 0), "tip": (90, 0, 0), "tipcover": (-90, 0, 0),
        "linkage": (0, 180, 0), "stand": (-90, 0, 0), "peg": (90, 0, 0), "middle": (0, -90, -140),
        "bumper": (0, 0, 0), "plug": (0, 0, 0), "pins": (0, 0, 0),
    }

    # Fallback preview positions (mm) from v5.1 STL bounding-box centers (used when no config is applied)
    _preview_position_offsets = {
        "socket":   (0, -25, 0),
        "base":     (0, -3, 0),
        "middle":   (1, 12, 0),
        "tip":      (1, 26, 0),
        "tipcover": (0, 39, 0),
        "linkage":  (0, 0, 20),
        "stand":    (0, -30, 0),
        "pins":     (0, 0, 0),
    }

    def compute_preview_positions(self):
        """Compute dynamic preview positions from current params.

        Estimates bounding-box centers for each part in assembled orientation
        based on parametric dimensions, without requiring STL rendering.
        Returns dict of part_name -> (x, y, z) tuples.
        """
        prox_h = self.intermediate_proximal_height
        dist_h = self.intermediate_distal_height
        int_len = self.intermediate_length
        dist_len = self.distal_length
        prox_len = self.proximal_length
        sock_depth = self.socket_depth
        sock_iface_len = self.socket_interface_length

        base_y = -(prox_len + prox_h / 2) / 2
        middle_y = int_len / 2
        tip_y = int_len + dist_len / 2
        tipcover_y = int_len + dist_len * 0.75
        socket_y = -(prox_len + prox_h / 2 + sock_iface_len + sock_depth / 2)
        stand_y = socket_y - sock_depth * 0.3
        linkage_z = 20

        return {
            "socket":   (0, round(socket_y, 1), 0),
            "base":     (0, round(base_y, 1), 0),
            "middle":   (1, round(middle_y, 1), 0),
            "tip":      (1, round(tip_y, 1), 0),
            "tipcover": (0, round(tipcover_y, 1), 0),
            "linkage":  (0, 0, linkage_z),
            "stand":    (0, round(stand_y, 1), 0),
            "pins":     (0, 0, 0),
        }

    # Multiple plug placements for the web preview
    # Y=0 = proximal hinge, Y=intermediate_length(24) = distal hinge
    # Z offsets = hinge half-width (~knuckle_proximal_width/2 and knuckle_distal_width/2)
    _preview_plug_instances = [
        {"position": (0,  0, -8.6), "rotation": (0,   0, 0)},   # proximal left
        {"position": (0,  0,  8.6), "rotation": (0, 180, 0)},   # proximal right
        {"position": (0, 24, -7.5), "rotation": (0,   0, 0)},   # distal left
        {"position": (0, 24,  7.5), "rotation": (0, 180, 0)},   # distal right
    ]

    # Explode offsets: unit direction vectors away from middle (Y≈12) in assembled space
    _preview_explode_offsets = {
        "middle":   (0,    0, 0),
        "socket":   (0,   -1, 0),
        "base":     (0, -0.5, 0),
        "tip":      (0,    1, 0),
        "tipcover": (0,  1.5, 0),
        "linkage":  (0,    0, 1),
        "stand":    (0, -1.5, 0),
        "plug":     (0,    0, 0),
        "pins":     (0,    0, 0),
    }

    #**************************************** dynamic properties ******************************

    intermediate_proximal_width_ = property(lambda self: (self.knuckle_proximal_width - self.knuckle_proximal_thickness*2 - self.knuckle_side_clearance*2) )
    intermediate_distal_width_ = property(lambda self: (self.knuckle_distal_width - self.knuckle_distal_thickness*2 - self.knuckle_side_clearance*2))
    intermediate_width_ = property(lambda self: orient_pair(self.intermediate_distal_width_, self.intermediate_proximal_width_))
    tip_interface_post_radius_ = property(lambda self: (self.tip_radius - self.tipcover_thickness- self.tip_interface_ridge_radius))# - self.tip_interface_ridge_radius - self.tipcover_thickness))
    tunnel_inner_width_ = property(lambda self: ({Orient.DISTAL: self.intermediate_width_[Orient.DISTAL]- self.knuckle_inset_border*2 + self.tunnel_radius/2, \
        Orient.PROXIMAL: self.intermediate_width_[Orient.PROXIMAL]- self.knuckle_inset_border*2 + self.tunnel_radius/2}))
    tunnel_inner_cutheight_ = property(lambda self: ({Orient.DISTAL: self.intermediate_height_[Orient.DISTAL] / 2 + self.tunnel_inner_height, \
        Orient.PROXIMAL: self.intermediate_height_[Orient.PROXIMAL] / 2 + self.tunnel_inner_height}))
    knuckle_inner_width_ = property(lambda self: ({Orient.PROXIMAL: self.intermediate_width_[Orient.PROXIMAL] + self.knuckle_side_clearance*2, \
         Orient.DISTAL: self.intermediate_width_[Orient.DISTAL] + self.knuckle_side_clearance*2}))
    intermediate_height_ = property(lambda self: orient_pair(self.intermediate_distal_height, self.intermediate_proximal_height))
    length_ = property(lambda self: orient_pair(self.distal_length, self.proximal_length))
    knuckle_width_ = property(lambda self: orient_pair(self.knuckle_distal_width, self.knuckle_proximal_width))
    knuckle_thickness_ = property(lambda self: orient_pair(self.knuckle_distal_thickness, self.knuckle_proximal_thickness))
    #TODO - this
    tip_radius = property(lambda self: self.tip_circumference/math.pi/2)
    socket_radius_ = property(lambda self: ({Orient.DISTAL: self.socket_circumference_distal / math.pi / 2, Orient.PROXIMAL: self.socket_circumference_proximal / math.pi / 2}))
    socket_thickness_ = property(lambda self: ({Orient.DISTAL: self.socket_thickness_distal, Orient.PROXIMAL: self.socket_thickness_proximal, Orient.MIDDLE: self.socket_thickness_middle}))
    strut_inset_ = property(lambda self: orient_pair(self.strut_inset_distal, self.strut_inset_proximal))
    distal_offset_ = property(lambda self: (self.intermediate_length))
    socket_interface_radius_ = property(lambda self: {Orient.DISTAL: self.socket_interface_radius_distal, # - self.socket_interface_radius_offset,
                                Orient.PROXIMAL: self.socket_interface_radius_proximal}) # - self.socket_interface_radius_offset + self.socket_interface_flare_radius})
    bottom_strut_width_ = property(lambda self: {Orient.DISTAL: self.intermediate_bottom_width_factor * (self.intermediate_width_[Orient.DISTAL]-(self.knuckle_inset_border*2)), \
        Orient.PROXIMAL: self.intermediate_bottom_width_factor * (self.intermediate_width_[Orient.PROXIMAL]-(self.knuckle_inset_border*2))})

    def __init__(self):
        self._models = {}
        self._parts = {}
    models = property(lambda self: self._models)
    parts = property(lambda self: self._parts)


    #The minimum circumferential length of a polygon segment.  higher is faster
    fs_ = property(lambda self: ({RenderQuality.INSANE : .05, RenderQuality.ULTRAHIGH : .1, RenderQuality.HIGH : .18, RenderQuality.EXTRAMEDIUM : .2, RenderQuality.MEDIUM : .4, RenderQuality.SUBMEDIUM : .6,RenderQuality.FAST : 1, RenderQuality.ULTRAFAST : 1.5, RenderQuality.STUPIDFAST : 2}))#, RenderQuality.AUTO : 1 if self.preview else .2}))
    #the minimum dgrees of each polygon framgment , higher is faster
    @property
    def fa_ (self): return{RenderQuality.INSANE : 1, RenderQuality.ULTRAHIGH : 1.5, RenderQuality.HIGH : 2, RenderQuality.EXTRAMEDIUM : 3.8, RenderQuality.MEDIUM : 4, RenderQuality.SUBMEDIUM : 5, RenderQuality.FAST : 6, RenderQuality.ULTRAFAST : 10, RenderQuality.STUPIDFAST : 15}#, RenderQuality.AUTO : 6 if self.preview else 2}))#[self.render_quality if not self.preview else self.preview_quality]))

    @property
    def scad_header(self, rq):
        ''' calculate header for top of scad file'''
        return "" if rq == RenderQuality.NONE else "$fa = %s; \n$fs = %s;\n" % (self.fa_[rq], self.fs_[rq])

    @property
    def translate_offsets(self):
         ''' amount to expand during explode'''
         return self._translate_offsets #self._prop_offset(self._offsets, self._animate_factor)#pass through ;amda to apply animate offsets

    @property
    def rotate_offsets(self):
        ''' amount rotate in print mode'''
        return self._rotate_offsets#self._prop_offset(self._print_rotate_offsets, self.distal_offset_)

    def validate_params(self):
        """Check cross-parameter constraints. Returns list of warning strings (empty = all OK)."""
        warnings = []
        # knuckle_plug_radius must be < hinge radius (intermediate_height/2)
        for orient_name, height in [("distal", self.intermediate_distal_height), ("proximal", self.intermediate_proximal_height)]:
            hinge_radius = height / 2
            if self.knuckle_plug_radius >= hinge_radius:
                warnings.append(f"knuckle_plug_radius ({self.knuckle_plug_radius}) >= {orient_name} hinge radius ({hinge_radius})")
        # proximal_length min should be >= -knuckle_radius
        prox_hinge_r = self.intermediate_proximal_height / 2
        if self.proximal_length < -prox_hinge_r:
            warnings.append(f"proximal_length ({self.proximal_length}) < -proximal hinge radius ({-prox_hinge_r})")
        # socket_interface_length max should be <= socket_depth
        if self.socket_interface_length > self.socket_depth:
            warnings.append(f"socket_interface_length ({self.socket_interface_length}) > socket_depth ({self.socket_depth})")
        # intermediate_tunnel_length should be <= maxv (already bounded by Prop, but check)
        # knuckle_washer_radius + knuckle_pin_radius should fit within hinge
        for orient_name, height in [("distal", self.intermediate_distal_height), ("proximal", self.intermediate_proximal_height)]:
            hinge_r = height / 2
            washer_total = self.knuckle_washer_radius + self.knuckle_pin_radius
            if washer_total > hinge_r:
                warnings.append(f"knuckle_washer_radius + knuckle_pin_radius ({washer_total}) > {orient_name} hinge radius ({hinge_r})")
        # tip_interface_post_radius_ should be positive
        tip_post_r = self.tip_radius - self.tipcover_thickness - self.tip_interface_ridge_radius
        if tip_post_r <= 0:
            warnings.append(f"tip_interface_post_radius_ ({tip_post_r:.2f}) <= 0: tip too small for interface (depends_on: tip_circumference, tipcover_thickness, tip_interface_ridge_radius)")
        return warnings

    def get_params(self, adv=False, allv=True, extended=False):
        ''' return all parameters for this finger model '''
        from enum import Enum as _Enum
        params = {}
        for name, prop in inspect.getmembers(DangerFingerParams):
            if name.startswith("_"): continue
            if isinstance(prop, Prop):
                inst_val = getattr(self, name)
                if (prop.advanced and (adv or allv)) or (not prop.advanced and not adv):
                    if not extended:
                        params[name] = inst_val
                    else:
                        row = {"Value": inst_val, "Default": prop.default, "Minimum": prop.minimum, "Maximum": prop.maximum, "Advanced": prop.advanced, "Documentation": prop.docs, "Hidden": prop.hidden}
                        if isinstance(inst_val, _Enum):
                            row["EnumOptions"] = list(type(inst_val).__members__.keys())
                            row["Value"] = inst_val.name
                            row["Default"] = prop.default.name if isinstance(prop.default, _Enum) else prop.default
                        params[name] = row
        return params

    @property
    def params(self):
        ''' return all parameters (shortcut for get_params with defaults) '''
        return self.get_params()
