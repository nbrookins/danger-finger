#!/bin/python
# pylint: disable=C0302, line-too-long, unused-wildcard-import, wildcard-import, invalid-name, broad-except
'''
The danger_finger copyright 2014-2020 Nicholas Brookins and Danger Creations, LLC
http://dangercreations.com/prosthetics :: http://www.thingiverse.com/thing:1340624
Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 https://creativecommons.org/licenses/by-nc-sa/4.0/
Source code licensed under Apache 2.0:  https://www.apache.org/licenses/LICENSE-2.0'''
import math
from solid import *
from solid.utils import *
from solid.solidpython import OpenSCADObject
from danger_tools import *

VERSION = 4.2
# *********************************** Entry Point ****************************************
#@staticmethod
def assemble(finger):
    ''' The entry point which loads a finger with proper parameters and outputs SCAD files as configured '''
    #sample param overrides for quick testing - comment out

    #uncomment to render STL instead of previewing
    #finger.action = Action.RENDER | Action.EMITSCAD

    finger.part = FingerPart.HARD
    #finger.part = FingerPart.TIP
    finger.render_quality = RenderQuality.FAST #ULTRAFAST FAST SUBMEDIUM MEDIUM EXTRAMEDIUM HIGH ULTRAHIGH
    finger.render_threads = 8

    #finger.preview_explode = True
    finger.preview_quality = RenderQuality.ULTRAFAST #ULTRAFAST FAST SUBMEDIUM MEDIUM EXTRAMEDIUM HIGH ULTRAHIGH
    #finger.preview_cut = True
    #finger.preview_rotate = 40
    #finger.animate_explode = True
    #finger.animate_rotate = True

    #load a configuration, with parameters from cli or env
    Params.parse(finger)
    print("~~* Building the DangerFinger: %s, %s, %s *~~" % (finger.action, finger.quality, finger.part))

    #build some pieces
    #TODO !!! - refact these to static helper methods
    build_models(finger)

    if finger.emitscad: emit_scad(finger)

    if finger.render: render_stl(finger)

    if finger.preview: render_stl(finger)
    #finger.render_png()

# ********************************** The danger finger *************************************
class DangerFingerBase:
    ''' The actual finger model '''
    # ************************************* control params *****************************************

    action = Prop(val=Action.PREVIEW | Action.EMITSCAD, doc=''' ''')
    preview_cut = Prop(val=False, doc=''' cut the preview for inset view ''')
    preview_explode = Prop(val=False, doc=''' Enable explode mode, only for preview ''')
    preview_rotate = Prop(val=0, minv=0, maxv=120, doc=''' rotate the finger ''')
    animate_explode = Prop(val=False, doc=''' Enable explode animation, only for preview ''')
    animate_rotate = Prop(val=False, doc=''' Enable rotate animation, only for preview ''')

    emit = Prop(val=True, doc=''' emit SCAD ''')
    render_quality = Prop(val=RenderQuality.AUTO, doc='''- auto to use fast for preview.  higher quality take much longer for scad rendering''', adv=True, setter=lambda self, value: (value))
    preview_quality = Prop(val=RenderQuality.AUTO, doc='''- auto to use fast for preview.  higher quality take much longer for scad rendering''', adv=True, setter=lambda self, value: (value))
    render_threads = Prop(val=2, minv=1, maxv=64, doc=''' render to STL ''')
    output_directory = Prop(val=os.getcwd(), doc=''' output_directory for scad code, otherwise current''')

    # **************************************** parameters ****************************************
    #TODO 3 - make a first class "AUTO" value
    intermediate_length = Prop(val=24, minv=8, maxv=30, doc=''' length of the intermediate finger segment ''')
    intermediate_distal_height = Prop(val=9.0, minv=4, maxv=16, doc=''' height of the middle section at the distal end.  roughly the height of the hinge circle ''')
    intermediate_proximal_height = Prop(val=10.0, minv=4, maxv=16, doc=''' height of the middle section at the proximal end.  roughly the height of the hinge circle ''')

    proximal_length = Prop(val=-1, minv=8, maxv=30, doc=''' length of the proximal/base finger segment ''') #TODO 2 - min auto of knuckle radius
    distal_length = Prop(val=18, minv=8, maxv=30, doc=''' length of the distal/tip finger segment ''')
    distal_base_length = Prop(val=5.5, minv=0, maxv=20, doc=''' length of the base of the distal/tip finger segment ''')

    knuckle_proximal_width = Prop(val=18.0, minv=4, maxv=20, doc=''' width of the proximal knuckle hinge''')
    knuckle_distal_width = Prop(val=16.0, minv=4, maxv=20, doc=''' width of the distal knuckle hinge ''')
    tip_circumference = 47.0
    tip_radius = property(lambda self: self.tip_circumference/math.pi/2)

    socket_depth = Prop(val=27, minv=5, maxv=60, doc=''' length of the portion that interfaces socket and base ''')
    socket_circumference_distal = Prop(val=57, minv=20, maxv=160, doc='''circumference of the socket closest to the base''')
    socket_circumference_proximal = Prop(val=62, minv=20, maxv=160, doc='''circumference of the socket closest to the hand''')
    socket_flare_top = Prop(val=5, minv=0, maxv=20, doc=''' length of the portion that interfaces socket and base ''')
    socket_thickness_distal = Prop(val=1.8, minv=.5, maxv=4, doc='''thickness of the socket closest to the base''')
    socket_thickness_proximal = Prop(val=1.5, minv=.5, maxv=4, doc='''thickness of the socket at flare''')

    linkage_length = Prop(val=70, minv=10, maxv=120, doc=''' length of the wrist linkage ''')
    linkage_width = Prop(val=6.8, minv=4, maxv=12, doc=''' width of the wrist linkage ''')
    linkage_height = Prop(val=4.4, minv=3, maxv=8, doc=''' thickness of the wrist linkage ''')
    linkage_hook_length = Prop(val=11.0, minv=4, maxv=12, doc='''  ''')
    linkage_hook_height = Prop(val=6.0, minv=4, maxv=12, doc='''  ''')
    linkage_hook_thickness = Prop(val=1.25, minv=0, maxv=12, doc='''  ''')
    linkage_hook_opening = Prop(val=.2, minv=0, maxv=12, doc='''  ''')

    # ************************************* rare or non-recommended to muss with *************
    tunnel_height = Prop(val=2.0, minv=0, maxv=5, adv=True, doc=''' height of tendon tunnel ''')
    tunnel_inner_height = Prop(val=.75, minv=0, maxv=4.5, adv=True, doc=''' height of tendon tunnel ''')
    tunnel_radius = Prop(val=1.6, minv=0, maxv=4, adv=True, doc=''' radius of tendon tunnel rounding ''')
    tunnel_inner_slant = Prop(val=0.35, minv=0, maxv=4, adv=True, doc=''' inward slant of middle tunnels ''')
    tunnel_outer_slant = Prop(val=0.85, minv=0, maxv=4, adv=True, doc=''' inward slant of outer tunnels ''')
    tunnel_outer_flare = Prop(val=0.0, minv=0, maxv=5, adv=True, doc=''' outward slant of outer tunnels back ''')

    knuckle_proximal_thickness = Prop(val=3.8, minv=1, maxv=5, adv=True, doc=''' thickness of the hinge tab portion on proximal side  ''')
    knuckle_distal_thickness = Prop(val=3.2, minv=1, maxv=5, adv=True, doc=''' thickness of the hinge tab portion on distal side ''')
    knuckle_inset_border = Prop(val=2.0, minv=0, maxv=5, adv=True, doc=''' width of teh hinge inset, same as top strut width ''')
    knuckle_inset_depth = Prop(val=0.9, minv=0, maxv=3, adv=True, doc=''' depth of the inset to clear room for tendons ''')

    knuckle_pin_radius = Prop(val=1.07, minv=0, maxv=3, adv=True, doc=''' radius of the hinge pin/hole ''')
    knuckle_plug_radius = Prop(val=3.0, minv=2, maxv=5, adv=True, doc=''' radius of the hinge pin cover plug ''') #TO-DO dynamic contraints?, must be less than hinge radius
    knuckle_plug_thickness = Prop(val=1.3, minv=0.5, maxv=4, adv=True, doc=''' thickness of the hinge pin cover plug ''')
    knuckle_plug_ridge = Prop(val=.3, minv=0, maxv=1.5, adv=True, doc=''' width of the plug holding ridge ''')
    knuckle_plug_clearance = Prop(val=.1, minv=-.5, maxv=1, adv=True, doc=''' clearance of the plug ''')

    knuckle_clearance = Prop(val=.4, minv=-.25, maxv=1, adv=True, doc=''' clearance of the rounded inner part of the hinges ''')
    knuckle_side_clearance = Prop(val=.2, minv=-.25, maxv=1, adv=True, doc=''' clearance of the flat circle side of the hinges ''')

    knuckle_rounding = Prop(val=1.5, minv=0, maxv=4, adv=True, doc=''' amount of rounding for the outer hinges ''')
    knuckle_cutouts = Prop(val=False, adv=True, doc=''' True for extra cutouts on internals of intermediate section ''')
    knuckle_washer_radius = Prop(val=.75, minv=0, maxv=4, adv=True, doc=''' radius of the washers for lowering hinge friction ''')
    knuckle_washer_thickness = Prop(val=.5, minv=0, maxv=4, adv=True, doc=''' thickness of the washers for lowering hinge friction ''')
    knuckle_brace_height_factor = Prop(val=.3, minv=0, maxv=2, adv=True, doc='''ratio of brace height vs regular struts, e.g. .5 for half the height''')

    socket_scallop_ratio_left = Prop(val=.2, minv=0, maxv=.8, adv=True, doc='''''')
    socket_scallop_ratio_right = Prop(val=.2, minv=0, maxv=.8, adv=True, doc=''' ''')
    socket_vertical_clearance = Prop(val=1, minv=-4, maxv=4, adv=True, doc='''Clearance between socket and base. extra is ok, as it gets hidden inside the socket, and the taper ensures a firm fit''')
    socket_interface_length = Prop(val=5.2, minv=3, maxv=8, adv=True, doc=''' length of the portion that interfaces socket and base ''')
    socket_interface_flare_radius = Prop(val=1.1, minv=3, maxv=8, adv=True, doc='''  ''')
    socket_interface_clearance = Prop(val=.3, minv=-2, maxv=2, adv=True, doc='''  ''')
    socket_interface_thickness = Prop(val=.75, minv=.25, maxv=4, adv=True, doc='''  ''')
    socket_interface_depth = Prop(val=1.0, minv=-2, maxv=4, adv=True, doc='''  ''')
    socket_interface_radius_offset = Prop(val=1.5, minv=-10, maxv=10, adv=True, doc='''  ''')

    intermediate_bottom_width_factor = Prop(val=.5, minv=0, maxv=2, adv=True, doc='''''')
    intermediate_tunnel_length = Prop(val=.4, minv=-.25, maxv=2, adv=True, doc='''0-2 for the length of tunnels toward middle''')
    distal_flange_height = Prop(val=.5, minv=0, maxv=10, adv=True, doc='''  ''')
    tunnel_inner_rounding = Prop(val=1.2, minv=0, maxv=4, adv=True, doc=''' amount of rounding for the inner tunnel ''')
    tendon_hole_radius = Prop(val=1.1, minv=0, maxv=5, adv=True, doc=''' ''')
    tendon_hole_width = Prop(val=2.2, minv=0, maxv=5, adv=True, doc=''' ''')

    tipcover_thickness = Prop(val=.95, minv=0, maxv=5, adv=True, doc=''' ''')
    tip_interface_clearance = Prop(val=.3, minv=0, maxv=5, adv=True, doc=''' ''')
    tip_interface_ridge_radius = Prop(val=.875, minv=0, maxv=5, adv=True, doc=''' ''')
    tip_interface_ridge_height = Prop(val=1.55, minv=0, maxv=5, adv=True, doc=''' ''')
    tip_interface_post_height = Prop(val=1.7, minv=0, maxv=5, adv=True, doc=''' ''')
    tip_detent_height = 3.3

    strut_height_ratio = Prop(val=.85, minv=.1, maxv=3, adv=True, doc=''' ratio of strut height to width (auto-controlled).  fractions make the strut thinner ''')
    strut_rounding = Prop(val=.4, minv=.5, maxv=2, adv=True, doc=''' 0 for no rounding, 1 for fullly round ''')

    #**************************************** dynamic properties ******************************

    intermediate_proximal_width = property(lambda self: (self.knuckle_proximal_width - self.knuckle_proximal_thickness*2 - self.knuckle_side_clearance*2))
    intermediate_distal_width = property(lambda self: (self.knuckle_distal_width - self.knuckle_distal_thickness*2 - self.knuckle_side_clearance*2))
    intermediate_width = property(lambda self: ({Orient.DISTAL: self.intermediate_distal_width, Orient.PROXIMAL: self.intermediate_proximal_width}))
    tip_interface_post_radius = property(lambda self: (self.tip_radius - self.tipcover_thickness- self.tip_interface_ridge_radius))# - self.tip_interface_ridge_radius - self.tipcover_thickness))
    tunnel_inner_width = property(lambda self: ({Orient.DISTAL: self.intermediate_width[Orient.DISTAL]- self.knuckle_inset_border*2 + self.tunnel_radius/2, \
        Orient.PROXIMAL: self.intermediate_width[Orient.PROXIMAL]- self.knuckle_inset_border*2 + self.tunnel_radius/2}))
    tunnel_inner_cutheight = property(lambda self: ({Orient.DISTAL: self.intermediate_height[Orient.DISTAL] / 2 + self.tunnel_inner_height, \
        Orient.PROXIMAL: self.intermediate_height[Orient.PROXIMAL] / 2 + self.tunnel_inner_height}))
    knuckle_inner_width = property(lambda self: ({Orient.PROXIMAL: self.intermediate_width[Orient.PROXIMAL] + self.knuckle_side_clearance*2, \
         Orient.DISTAL: self.intermediate_width[Orient.DISTAL] + self.knuckle_side_clearance*2}))
    intermediate_height = property(lambda self: ({Orient.DISTAL: self.intermediate_distal_height, Orient.PROXIMAL: self.intermediate_proximal_height}))
    length = property(lambda self: ({Orient.DISTAL: self.distal_length, Orient.PROXIMAL: self.proximal_length}))
    knuckle_width = property(lambda self: ({Orient.DISTAL: self.knuckle_distal_width, Orient.PROXIMAL: self.knuckle_proximal_width}))
    knuckle_thickness = property(lambda self: ({Orient.DISTAL: self.knuckle_distal_thickness, Orient.PROXIMAL: self.knuckle_proximal_thickness}))
    socket_radius = property(lambda self: ({Orient.DISTAL: self.socket_circumference_distal / math.pi / 2, Orient.PROXIMAL: self.socket_circumference_proximal / math.pi / 2}))
    socket_thickness = property(lambda self: ({Orient.DISTAL: self.socket_thickness_distal, Orient.PROXIMAL: self.socket_thickness_proximal}))
    distal_offset = property(lambda self: (self.intermediate_length))
    socket_interface_radius = property(lambda self: {Orient.DISTAL: self.socket_radius[Orient.DISTAL] - self.socket_interface_radius_offset, Orient.PROXIMAL: self.socket_radius[Orient.DISTAL] - self.socket_interface_radius_offset + self.socket_interface_flare_radius})
    shift_distal = property(lambda self: translate((0, self.distal_offset, 0)))
    render = property(lambda self: (Action.RENDER in self.action))
    preview = property(lambda self: (Action.PREVIEW in self.action))
    emitscad = property(lambda self: (Action.EMITSCAD in self.action))
    quality = property(lambda self: (self.render_quality if not self.preview else self.preview_quality))
    bottom_strut_width = property(lambda self: {Orient.DISTAL: self.intermediate_bottom_width_factor * (self.intermediate_width[Orient.DISTAL]-(self.knuckle_inset_border*2)),
                                 Orient.PROXIMAL: self.intermediate_bottom_width_factor * (self.intermediate_width[Orient.PROXIMAL]-(self.knuckle_inset_border*2))})
    animate_factor = 1
    #*************************************** special properties **********************************
    mod = {}
    @property
    def explode_offsets(self):
        ''' amount to expand during explode'''
        return self._prop_offset(self._explode_offsets, self.animate_factor)
    _explode_offsets = {"middle":(0, 20, 0), "base" : (0, 0, 0), "tip":(0, 40, 0), "socket":(0, -20, 0), \
        "linkage" : (10, -30, 0), "tipcover" : (0, 60, 0), "plugs":((0, 0, -8), (0, 0, 8), (0, 40, -8), (0, 40, 20))}

    @property
    def translate_offsets(self):
        ''' amount to expand during explode'''
        return self._prop_offset(self._translate_offsets, self.distal_offset)
    _translate_offsets = {"middle":(0, 0, 0), "base" : (0, 0, 0), "tip":(0, 1, 0), "socket":(0, 0, 0), \
        "linkage" : (.5, 0, 0), "tipcover" : (0, 0, 0), "plugs":((0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0))}

    @property
    def print_rotate_offsets(self):
        ''' amount rotate in print mode'''
        return self._prop_offset(self._print_rotate_offsets, self.distal_offset)
    _print_rotate_offsets = {"middle":(0, -90, 0), "base" : (90, 0, 0), "tip":(-90, 0, 0), "socket":(0, 0, 0), \
        "linkage" : (0, -90, 0), "tipcover" : (0, 0, 0), "plugs":((0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0))}

    @property
    def rotate_offsets(self):
        ''' amount to rotate'''
        return self._prop_offset(self.rotate_offset_factors, self.animate_factor * self.preview_rotate, func=lambda v: min(v, 1))
    rotate_offset_factors = {"middle":(0, 0, 1), "base" : (0, 0, 0), "tip":(0, 0, 2), "socket":(0, 0, 0), \
        "linkage" : (0, 0, 0), "tipcover" : (0, 0, 0), "plugs":((0, 0, 0), (0, 0, 0), (0, 0, 2), (0, 0, 2))}

    def _prop_offset(self, offs, f, func=lambda v: v):
        ''' calculate offsets by facot for animation, etc '''
        new_offs = {o: (func(offs[o][0]) * f, func(offs[o][1]) * f, func(offs[o][2]) * f) if isinstance(offs[o][0], (int, float)) else \
            [(func(v[0]) * f, func(v[1]) * f, func(v[2]) * f) for v in offs[o]] for o in offs}
        return new_offs

    _part = FingerPart.MIDDLE
    @property
    def part(self):
        ''' select which part to print. list of FingerPart enums'''
        return FingerPart.ALL if self.preview else self._part
    @part.setter
    def part(self, val):
        self._part = val

    #The minimum circumferential length of a polygon segment.  higher is faster
    fs = property(lambda self: ({
        RenderQuality.ULTRAHIGH : .1, RenderQuality.HIGH : .2, RenderQuality.EXTRAMEDIUM : .3, RenderQuality.MEDIUM : .4, RenderQuality.SUBMEDIUM : .6,
        RenderQuality.FAST : 1, RenderQuality.ULTRAFAST : 1.5, RenderQuality.AUTO : 1 if self.preview else .2}[self.render_quality if not self.preview else self.preview_quality]))

    #the minimum dgrees of each polygon framgment , higher is faster
    fa = property(lambda self: ({
        RenderQuality.ULTRAHIGH : 1.5, RenderQuality.HIGH : 2, RenderQuality.EXTRAMEDIUM : 3, RenderQuality.MEDIUM : 4, RenderQuality.SUBMEDIUM : 5,
        RenderQuality.FAST : 6, RenderQuality.ULTRAFAST : 10, RenderQuality.AUTO : 6 if self.preview else 2}[self.render_quality if not self.preview else self.preview_quality]))

    scad_header = property(lambda self: ("$fa = %s; \n$fs = %s;\n" % (self.fa, self.fs)))
