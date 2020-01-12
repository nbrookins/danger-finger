#!/bin/python
# pylint: disable=C0302, line-too-long, unused-wildcard-import, wildcard-import, invalid-name, broad-except
'''
The danger_finger copyright 2014-2020 Nicholas Brookins and Danger Creations, LLC
http://dangercreations.com/prosthetics :: http://www.thingiverse.com/thing:1340624
Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 https://creativecommons.org/licenses/by-nc-sa/4.0/
Source code licensed under Apache 2.0:  https://www.apache.org/licenses/LICENSE-2.0'''
import os
import sys
import math
import time
from solid import *
from solid.utils import *
from solid.solidpython import OpenSCADObject
from danger_tools import *

VERSION = 4.2

# *********************************** Entry Point ****************************************
def assemble():
    ''' The entry point which loads a finger with proper parameters and outputs SCAD files as configured '''
    #create a finger object
    finger = DangerFinger()

    #sample param overrides for quick testing - comment out
    # finger.preview = True
    finger.render = True
    finger.part = FingerPart.BASE | FingerPart.MIDDLE | FingerPart.TIP
    #finger.render_quality = RenderQuality.EXTRAMEDIUM # EXTRAMEDIUM FAST HIGH MEDIUM ULTRAHIGH SUBMEDIUM
    finger.render_quality = RenderQuality.ULTRAHIGH # FAST EXTRAMEDIUM HIGH MEDIUM ULTRAHIGH SUBMEDIUM
    finger.preview_explode = True
    #finger.preview_cut = True

    finger.render_threads = 8
   # finger.rotate = 30
    #finger.explode_animate = True
    #finger.rotate_animate = True

    #load a configuration, with parameters from cli or env
    Params.parse(finger)

    #build some pieces
    finger.build_models()
    if finger.emit: finger.emit_scad()
    if finger.render: finger.render_stl()


# ********************************** The danger finger *************************************
class DangerFinger:
    ''' The actual finger model '''
    # ************************************* control params *****************************************

    preview = Prop(val=False, doc=''' Enable preview mode, emits all segments ''')
    render_quality = Prop(val=RenderQuality.AUTO, doc='''- auto to use fast for preview.  higher quality take much longer for scad rendering''', adv=True, setter=lambda self, value: (value))
    preview_explode = Prop(val=False, doc=''' Enable explode mode, only for preview ''')
    emit = Prop(val=True, doc=''' emit SCAD ''')
    render = Prop(val=False, doc=''' render to STL ''')
    preview_cut = Prop(val=False, doc=''' cut the preview for inset view ''')
    render_threads = Prop(val=2, minv=1, maxv=64, doc=''' render to STL ''')
    animate_explode = Prop(val=False, doc=''' Enable explode animation, only for preview ''')
    animate_rotate = Prop(val=False, doc=''' Enable rotate animation, only for preview ''')
    preview_rotate = Prop(val=0, minv=0, maxv=120, doc=''' rotate the finger ''')
    output_directory = Prop(val=os.getcwd(), doc=''' output_directory for scad code, otherwise current''')

    # **************************************** parameters ****************************************
    #TODO 3 - make a first class "AUTO" value
    intermediate_length = Prop(val=25, minv=8, maxv=30, doc=''' length of the intermediate finger segment ''')
    intermediate_distal_height = Prop(val=10.0, minv=4, maxv=16, doc=''' height of the middle section at the distal end.  roughly the height of the hinge circle ''')
    intermediate_proximal_height = Prop(val=11.5, minv=4, maxv=16, doc=''' height of the middle section at the proximal end.  roughly the height of the hinge circle ''')

    proximal_length = Prop(val=0, minv=8, maxv=30, doc=''' length of the proximal/base finger segment ''') #TODO 2 - min auto of knuckle radius
    distal_length = Prop(val=24, minv=8, maxv=30, doc=''' length of the distal/tip finger segment ''')
    distal_base_length = Prop(val=7, minv=0, maxv=20, doc=''' length of the base of the distal/tip finger segment ''')

    knuckle_proximal_width = Prop(val=16.5, minv=4, maxv=20, doc=''' width of the proximal knuckle hinge''')
    knuckle_distal_width = Prop(val=14.5, minv=4, maxv=20, doc=''' width of the distal knuckle hinge ''')
    tip_circumference = 34
    tip_radius = property(lambda self: self.tip_circumference/math.pi/2)

    socket_depth = Prop(val=27, minv=5, maxv=60, doc=''' length of the portion that interfaces socket and base ''')
    socket_circumference_distal = Prop(val=55, minv=20, maxv=160, doc='''circumference of the socket closest to the base''')
    socket_circumference_proximal = Prop(val=62, minv=20, maxv=160, doc='''circumference of the socket closest to the hand''')
    socket_flare_top = Prop(val=5, minv=0, maxv=20, doc=''' length of the portion that interfaces socket and base ''')
    socket_thickness_distal = Prop(val=1.8, minv=.5, maxv=4, doc='''thickness of the socket closest to the base''')
    socket_thickness_proximal = Prop(val=1.5, minv=.5, maxv=4, doc='''thickness of the socket at flare''')

    linkage_length = Prop(val=70, minv=10, maxv=120, doc=''' length of the wrist linkage ''')
    linkage_width = Prop(val=6.8, minv=4, maxv=12, doc=''' width of the wrist linkage ''')
    linkage_height = Prop(val=4.4, minv=3, maxv=8, doc=''' thickness of the wrist linkage ''')

    # ************************************* rare or non-recommended to muss with *************
    tunnel_height = Prop(val=1.8, minv=0, maxv=5, adv=True, doc=''' height of tendon tunnel ''')
    tunnel_inner_height = Prop(val=.75, minv=0, maxv=4.5, adv=True, doc=''' height of tendon tunnel ''')
    tunnel_radius = Prop(val=1.6, minv=0, maxv=4, adv=True, doc=''' radius of tendon tunnel rounding ''')
    tunnel_inner_slant = Prop(val=0.35, minv=0, maxv=4, adv=True, doc=''' inward slant of middle tunnels ''')
    tunnel_outer_slant = Prop(val=0.85, minv=0, maxv=4, adv=True, doc=''' inward slant of outer tunnels ''')
    tunnel_outer_flare = Prop(val=0.0, minv=0, maxv=5, adv=True, doc=''' outward slant of outer tunnels back ''')

    knuckle_proximal_thickness = Prop(val=3.6, minv=1, maxv=5, adv=True, doc=''' thickness of the hinge tab portion on proximal side  ''')
    knuckle_distal_thickness = Prop(val=3.4, minv=1, maxv=5, adv=True, doc=''' thickness of the hinge tab portion on distal side ''')
    knuckle_inset_border = Prop(val=2.2, minv=0, maxv=5, adv=True, doc=''' width of teh hinge inset, same as top strut width ''')
    knuckle_inset_depth = Prop(val=.8, minv=0, maxv=3, adv=True, doc=''' depth of the inset to clear room for tendons ''')
    knuckle_pin_radius = Prop(val=1.07, minv=0, maxv=3, adv=True, doc=''' radius of the hinge pin/hole ''')
    knuckle_plug_radius = Prop(val=3.0, minv=2, maxv=5, adv=True, doc=''' radius of the hinge pin cover plug ''') #TO-DO dynamic contraints?, must be less than hinge radius
    knuckle_plug_thickness = Prop(val=1.1, minv=0.5, maxv=4, adv=True, doc=''' thickness of the hinge pin cover plug ''')
    knuckle_plug_ridge = Prop(val=.3, minv=0, maxv=1.5, adv=True, doc=''' width of the plug holding ridge ''')
    knuckle_plug_clearance = Prop(val=.1, minv=-.5, maxv=1, adv=True, doc=''' clearance of the plug ''')
    knuckle_clearance = Prop(val=.4, minv=-.25, maxv=1, adv=True, doc=''' clearance of the rounded inner part of the hinges ''')
    knuckle_side_clearance = Prop(val=.2, minv=-.25, maxv=1, adv=True, doc=''' clearance of the flat circle side of the hinges ''')
    knuckle_rounding = Prop(val=.9, minv=0, maxv=4, adv=True, doc=''' amount of rounding for the outer hinges ''')
    knuckle_cutouts = Prop(val=False, adv=True, doc=''' True for extra cutouts on internals of intermediate section ''')
    knuckle_washer_radius = Prop(val=.6, minv=0, maxv=4, adv=True, doc=''' radius of the washers for lowering hinge friction ''')
    knuckle_washer_thickness = Prop(val=.5, minv=0, maxv=4, adv=True, doc=''' thickness of the washers for lowering hinge friction ''')
    knuckle_brace_height_factor = Prop(val=.3, minv=0, maxv=2, adv=True, doc='''ratio of brace height vs regular struts, e.g. .5 for half the height''')

    socket_scallop_ratio_left = Prop(val=.2, minv=0, maxv=.8, adv=True, doc='''''')
    socket_scallop_ratio_right = Prop(val=.2, minv=0, maxv=.8, adv=True, doc=''' ''')
    socket_vertical_clearance = Prop(val=1, minv=-4, maxv=4, adv=True, doc='''Clearance between socket and base. extra is ok, as it gets hidden inside the socket, and the taper ensures a firm fit''')
    socket_interface_length = Prop(val=5, minv=3, maxv=8, adv=True, doc=''' length of the portion that interfaces socket and base ''')
    socket_interface_flare_radius = Prop(val=1, minv=3, maxv=8, adv=True, doc='''  ''')
    socket_interface_clearance = Prop(val=.25, minv=-2, maxv=2, adv=True, doc='''  ''')
    socket_interface_thickness = Prop(val=.75, minv=.25, maxv=4, adv=True, doc='''  ''')
    socket_interface_radius_offset = Prop(val=1.5, minv=-10, maxv=10, adv=True, doc='''  ''')

    intermediate_tunnel_length = Prop(val=.4, minv=-.25, maxv=2, adv=True, doc='''0-2 for the length of tunnels toward middle''')
    distal_flange_height = Prop(val=.5, minv=0, maxv=10, adv=True, doc='''  ''')
    tunnel_inner_rounding = Prop(val=1.2, minv=0, maxv=4, adv=True, doc=''' amount of rounding for the inner tunnel ''')
    tendon_hole_radius = Prop(val=1.1, minv=0, maxv=5, adv=True, doc=''' ''')
    tendon_hole_width = Prop(val=2.2, minv=0, maxv=5, adv=True, doc=''' ''')

    tipcover_thickness = Prop(val=.75, minv=0, maxv=5, adv=True, doc=''' ''')
    tip_interface_clearance = Prop(val=.15, minv=0, maxv=5, adv=True, doc=''' ''')
    tip_interface_ridge_radius = Prop(val=.875, minv=0, maxv=5, adv=True, doc=''' ''')
    tip_interface_ridge_height = Prop(val=1.5, minv=0, maxv=5, adv=True, doc=''' ''')
    tip_interface_post_height = Prop(val=1.5, minv=0, maxv=5, adv=True, doc=''' ''')

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
    shift_distal = lambda self: translate((0, self.distal_offset, 0))

    #**************************************** finger bits ****************************************

    def part_base(self):
        ''' Generate the base finger section, closest proximal to remnant '''
        tunnel_length = self.intermediate_height[Orient.PROXIMAL] * .4
        tunnel_width = self.intermediate_width[Orient.PROXIMAL] + self.knuckle_side_clearance*2
        length = (self.proximal_length + self.intermediate_height[Orient.PROXIMAL]/2)
        trim_offset = self.knuckle_proximal_thickness +self.intermediate_proximal_width + self.knuckle_side_clearance-.01

        mod_core = translate((0, -length, 0))(rotate((90, 0, 0))(rcylinder(r=self.socket_interface_radius[Orient.DISTAL]+self.socket_thickness_distal, h=self.distal_flange_height))) #
        mod_hinge, mod_hinge_cut, mod_washers = self.knuckle_outer(orient=Orient.PROXIMAL, extend_cut=(-10, -10))
        mod_tunnel, _mod_bridge_cut = self.bridge(length=tunnel_length, tunnel_width=tunnel_width+ self.knuckle_side_clearance*2, orient=Orient.PROXIMAL | Orient.OUTER)
        mod_socket_interface = self.socket_interface(Orient.INNER)
        #TODO 3 allow resize of width for base/socket interface, once socket is done

        mod_plugs = self.part_plugs(clearance=False)
        mod_trim = cylinder(h=self.intermediate_proximal_width, r=self.intermediate_proximal_height/2 - self.knuckle_rounding, center=True)
        mod_side_trim = mod_trim.translate((0, 0, trim_offset)) + translate((0, 0, -trim_offset))(mod_trim)
        mod_tendon_hole = self.tendon_hole()
        mod_breather = cylinder(r=self.knuckle_inner_width[Orient.PROXIMAL]/4, h=20, center=True).rotate((90, 0, 0)).translate((0, -10, 0))
        mod_elastic = self.elastic_hole()

        radius = self.intermediate_height[Orient.PROXIMAL]/2
        mod_extra = cylinder(r=radius+self.knuckle_clearance, h=self.knuckle_inner_width[Orient.PROXIMAL], center=True)
        mod_main = hull()(mod_core + mod_hinge) + hull()(mod_tunnel + mod_core)

        return  (mod_main - mod_plugs - mod_hinge_cut - mod_side_trim + mod_socket_interface - mod_tendon_hole - mod_elastic - mod_breather - _mod_bridge_cut[0].translate((0.2, -2, 0)).resize((0, 0, 0))) - mod_extra + mod_washers

    def part_tip(self):
        ''' Generate the tip finger knuckle section, most distal to remnant '''
        tunnel_length = self.intermediate_height[Orient.DISTAL]*.4
        plug_trans = diff(-self.knuckle_distal_width/2 + self.knuckle_plug_thickness/2 - 0.01, -self.knuckle_proximal_width/2 + self.knuckle_plug_thickness/2 - 0.01)

        mod_hinge, mod_hinge_cut, mod_washers = self.knuckle_outer(orient=Orient.DISTAL)
        mod_plugs = self.part_plugs(clearance=False)
        mod_plug_cut = mod_plugs[0].translate((0, 0, plug_trans)) + mod_plugs[1].translate((0, 0, -plug_trans))

        bridge = self.bridge(length=tunnel_length, tunnel_width=self.knuckle_inner_width[Orient.DISTAL] + self.knuckle_side_clearance*2, orient=Orient.DISTAL | Orient.OUTER)
        mod_tunnel = translate((0, tunnel_length, 0))(bridge[0])
        mod_bottom_trim = cube((self.intermediate_distal_height, 1, self.knuckle_width[Orient.DISTAL]), center=True).translate((-self.knuckle_plug_radius -self.intermediate_distal_height/2, self.distal_base_length-.25, 0))
        #TODO 3 allow resize of width for tip
        mod_core = rcylinder(r=self.tip_radius, h=0.1).rotate((90, 0, 0)).translate((0, self.distal_base_length, 0)) - mod_bottom_trim
        mod_interface = self.tip_interface()

        mod_tip_hole = cylinder(r=self.tip_interface_post_radius-2, h=20, center=True).rotate((90, 0, 0)).translate((0, self.intermediate_distal_height, 0))
        mod_top_detent = self.tip_detent()
        radius = self.intermediate_height[Orient.DISTAL]/2
        mod_extra = cylinder(r=radius+self.knuckle_clearance, h=self.knuckle_inner_width[Orient.DISTAL], center=True)
        mod_main = hull()(mod_core + mod_hinge) + hull()(mod_tunnel + mod_core)

        #TODO 1 Hacky hard coded!
        return (mod_main + mod_interface + mod_top_detent - mod_plug_cut - mod_tip_hole - mod_hinge_cut - bridge[1][1].translate((0, 9.0, 0))) - mod_extra.translate((-1, 0, 0)) + mod_washers

    def part_middle(self):
        ''' Generate the middle/intermediate finger section '''
        #a hinge at each end
        mod_dist_hinge, anchor_dtl, anchor_dtr, anchor_db = self.knuckle_inner(orient=Orient.DISTAL, cutout=self.knuckle_cutouts)
        mod_prox_hinge, anchor_ptl, anchor_ptr, anchor_pb = self.knuckle_inner(orient=Orient.PROXIMAL, cutout=self.knuckle_cutouts)
        mod_dist_hinge = mod_dist_hinge.rotate((180, 0, 0))
        # 3 struts and a cross brace
        mod_strut_tl = hull()(self.shift_distal()(anchor_dtl), anchor_ptl)
        mod_strut_tr = hull()(self.shift_distal()(anchor_dtr), anchor_ptr)
        mod_strut_b = hull()(self.shift_distal()(anchor_db), anchor_pb)
        mod_brace = self.cross_strut()

        #tunnel at each end
        shift_tun = lambda self, orient: (translate((0, self.intermediate_height[orient]*self.intermediate_tunnel_length, 0)))
        bridge_p = self.bridge(length=self.intermediate_height[Orient.PROXIMAL]*self.intermediate_tunnel_length, \
            tunnel_width=self.tunnel_inner_width[Orient.PROXIMAL], orient=Orient.PROXIMAL | Orient.INNER)
        mod_tunnel_p = shift_tun(self, Orient.PROXIMAL)(bridge_p[0])
        _mod_cut_p = shift_tun(self, Orient.PROXIMAL)(bridge_p[1])

        bridge_d = self.bridge(length=self.intermediate_height[Orient.DISTAL]*self.intermediate_tunnel_length, \
            tunnel_width=self.tunnel_inner_width[Orient.DISTAL], orient=Orient.DISTAL | Orient.INNER)
        mod_tunnel_d = rotate((180, 0, 0))(shift_tun(self, Orient.DISTAL)(bridge_d[0]))
        _mod_cut_d = rotate((180, 0, 0))(shift_tun(self, Orient.DISTAL)(bridge_d[1]))

        trim_c_d = cylinder(r=self.intermediate_height[Orient.DISTAL]/2 + self.knuckle_side_clearance*1, h=4, center=True)
        trim_c_p = cylinder(r=self.intermediate_height[Orient.PROXIMAL]/2 + self.knuckle_side_clearance*1, h=4, center=True)
        mod_side_trim_d = trim_c_d.translate((0, 0, self.intermediate_width[Orient.DISTAL]/2+1.99)) + trim_c_d.translate((0, 0, -self.intermediate_width[Orient.DISTAL]/2-1.99))
        mod_side_trim_p = trim_c_p.translate((0, 0, self.intermediate_width[Orient.PROXIMAL]/2+1.99)) + trim_c_p.translate((0, 0, -self.intermediate_width[Orient.PROXIMAL]/2-1.99))

        return (self.shift_distal()(mod_dist_hinge + mod_tunnel_d) + mod_prox_hinge + mod_strut_tl + mod_strut_tr + mod_strut_b + mod_brace + mod_tunnel_p) - (self.shift_distal()(mod_side_trim_d), mod_side_trim_p)

    def part_plugs(self, clearance=True):
        ''' plug covers for the knuckle pins'''
        plug = color(Blue)(self.knuckle_plug(clearance=clearance))
        p_offset = -self.knuckle_proximal_width/2 + self.knuckle_plug_thickness/2 - 0.01
        d_offset = -self.knuckle_distal_width/2 + self.knuckle_plug_thickness/2 - 0.01
        mod_plug_pl = translate((0, 0, p_offset))(plug)
        mod_plug_pr = rotate((0, 180, 0))(translate((0, 0, p_offset))(plug))
        mod_plug_dl = self.shift_distal()(plug.translate((0, 0, d_offset)))
        mod_plug_dr = self.shift_distal()(plug.rotate((0, 180, 0)).translate((0, 0, d_offset)))
        return mod_plug_pl, mod_plug_pr, mod_plug_dl, mod_plug_dr

    #**************************************** Primitives ***************************************

    tip_detent_height = 3.2
    def tip_detent(self):
        ''' create tendon detents '''
        hole_offset = self.tip_interface_post_radius-2 + .75
        shift = self.distal_base_length + self.tip_detent_height/2 - .1 + self.tip_interface_post_height + self.tip_interface_ridge_height
        mod = cube(size=(1.4, self.tip_detent_height, 2.4), center=True) - cube(size=(1.5, self.tip_detent_height, .4), center=True).translate((0, .5, 0))
        return mod.translate((-hole_offset, shift, 0)) + mod.translate((hole_offset, shift, 0))

    def tip_interface(self):
        ''' the snap-on interface section to the soft tip cover'''
        mod_core = cylinder(r=self.tip_interface_post_radius, h=self.tip_interface_post_height) + \
            cylinder(r=self.tip_interface_ridge_radius+self.tip_interface_post_radius, h=self.tip_interface_ridge_height).translate((0, 0, -self.tip_interface_post_height+.01))
        return mod_core.rotate((90, 0, 0)).translate((0, self.distal_base_length + self.tip_interface_post_height - .01, 0))

    def tendon_hole(self):
        ''' return a tendon tube for cutting from the base'''
        h = self.socket_radius[Orient.DISTAL] + self.socket_thickness[Orient.DISTAL]
        a1 = translate((h, -self.intermediate_proximal_height/2 + .65 - self.proximal_length + self.tendon_hole_radius/2, 0))( \
            resize((0, 0, self.tendon_hole_width))(rotate((0, 90, 0))(cylinder(r=self.tendon_hole_radius, h=.1, center=True))))
        a2 = translate((-h/4, -self.intermediate_proximal_height/2 + .65+ self.tendon_hole_radius/2, 0))( \
            cylinder(r=self.tendon_hole_radius, h=.1, center=True).resize((0, 0, 1)).rotate((0, 90, 0)))
        return hull()(a1, a2)

    def elastic_hole(self):
        ''' generate twin holes in base for elastic tendon '''
        r = self.tendon_hole_radius
        l = (self.proximal_length + 3 + self.intermediate_proximal_height/2) #TODO 1 - add base length (3)?
        sr = self.socket_radius[Orient.DISTAL] - self.socket_interface_radius_offset + r
        anchor = translate((sr/2, 0, 0))( \
                resize((0, 0, self.tendon_hole_width))(rotate((90, 0, 0))(cylinder(r=r, h=0.1, center=True))))
        a1 = anchor.translate((0, -l, self.tendon_hole_width * 1.2))
        a2 = anchor.translate((0, -l, -self.tendon_hole_width * 1.2))
        return hull()(anchor, a1), hull()(anchor, a2)

    def bridge(self, length, orient, tunnel_width):
        ''' tendon tunnel for external hinges'''
        #assemble lots of variables, changing by orientation
        orient_lat = Orient.PROXIMAL if orient & Orient.PROXIMAL else Orient.DISTAL
        #generate our anchor points
        t_top_l_in = self.bridge_anchor(orient, length, top=True, inside=True, rnd=(orient&Orient.INNER))
        t_top_r_in = self.bridge_anchor(orient, length, top=True, inside=True, shift=True, rnd=(orient&Orient.INNER))
        t_top_l_out = self.bridge_anchor(orient, length, top=True, inside=False)
        t_top_r_out = self.bridge_anchor(orient, length, top=True, inside=False, shift=True)
        t_anchor_l_in = self.bridge_anchor(orient, length, top=False, inside=True, rnd=True)
        t_anchor_r_in = self.bridge_anchor(orient, length, top=False, inside=True, shift=True, rnd=True)
        t_anchor_l_out = self.bridge_anchor(orient, length, top=False, inside=False, rnd=(orient&Orient.OUTER))
        t_anchor_r_out = self.bridge_anchor(orient, length, top=False, inside=False, shift=True, rnd=(orient&Orient.OUTER))
        anchors = ()
        if orient != Orient.OUTER | Orient.PROXIMAL:
            anchors += (t_anchor_l_out, t_anchor_r_out, t_top_r_out, t_top_l_out)
        if orient != Orient.OUTER | Orient.DISTAL:
            anchors += (t_anchor_l_in, t_anchor_r_in, t_top_l_in, t_top_r_in)
        #hull them together, and cut the middle
        mod_tunnel = hull()(anchors)
        #hull()(
        mod_cut_a = translate((0, 2 + (length if orient == (Orient.DISTAL | Orient.INNER) else -0), 0))( \
                rcylinder(h=tunnel_width, rnd=self.tunnel_inner_rounding, center=True, \
                    r=self.tunnel_inner_cutheight[orient_lat] - (1.75 if orient == (Orient.DISTAL | Orient.OUTER) else 0)))#TODO 2 - unhardcode this later
        mod_cut_b = translate((0, -10 + (length if orient == (Orient.DISTAL | Orient.INNER) else 0), 0))( \
                rcylinder(r=self.tunnel_inner_cutheight[orient_lat], h=tunnel_width, rnd=self.tunnel_inner_rounding, center=True))

        if orient != (Orient.OUTER):
            mod_tunnel = mod_tunnel - hull()(mod_cut_a, mod_cut_b)
        return mod_tunnel, (mod_cut_a, mod_cut_b)

    def bridge_anchor(self, orient, length, top=False, inside=False, shift=False, rnd=False):
        ''' calculate tunnel widths for a variety of orientations. a mess of logic, but it's gotta go somewhere '''
        orient_lat = Orient.PROXIMAL if orient & Orient.PROXIMAL else Orient.DISTAL
        orient_part = Orient.INNER if orient & Orient.INNER else Orient.OUTER
        r = self.tunnel_radius

        top_inner_slant = self.strut_rounding + self.tunnel_inner_slant
        width_top_in = (self.intermediate_width[orient_lat] / 2) - (top_inner_slant if (orient_part == Orient.INNER) else 0)
        width_top_out = (self.intermediate_width[orient_lat] / 2) - (-.01 if (orient_part == Orient.INNER) else -self.tunnel_outer_flare) \
            + (.01 if (orient_lat == Orient.DISTAL and inside) else 0)

        width_bottom_in = self.intermediate_width[orient_lat] / 2
        width_bottom_out = self.knuckle_width[orient_lat] / 2  + (.01 if (orient_lat == Orient.DISTAL and inside) else 0)

        height_top = self.intermediate_height[orient_lat] / 2 + self.tunnel_height
        height_bottom = self.intermediate_height[orient_lat] / 2 + (0 if orient_part == Orient.INNER and inside else 0)#adjust to not stick out from struts
        #TODO 2 - slant down for bridge at end of tip.  unhard code this based on tip height, not yet defined
        height = (height_top -r) if top else height_bottom

        if orient & Orient.OUTER:            #TODO 2 - unhardcode this based on tip width, when defined
            width = width_bottom_out - ((self.tunnel_outer_slant) if inside or (not inside and orient_lat == Orient.DISTAL) else 0) if not top else \
                (width_top_out -1 if orient_lat == Orient.DISTAL and inside else width_top_out)
        elif orient & Orient.INNER and inside: #inside middle
            width = (width_top_in if top else width_bottom_in - self.strut_rounding/2) #inner bottom slant inward
        else: #outside middle
            width = (width_top_out if top else width_bottom_in)
        width -= r
        if shift: width = -width

        length = 0 if inside else -length

        dim = (height, length, width)
        anchor = rotate((90, 0, 0))(cylinder(r=r, h=.01))
        if rnd:
            anchor = translate((r/4 * -.5 if not top else r/8, -r/3, r/2*(-1 if shift else 1)))(sphere(r=r/2))
        return translate(dim)(anchor)

    def knuckle_outer(self, orient, extend_cut=(0, 0)):
        ''' create the outer hinges for base or tip segments '''
        radius = self.intermediate_height[orient]/2
        width = self.knuckle_width[orient]
        mod_pin = self.knuckle_pin(length=width + .01)
        mod_washers = self.knuckle_washers(orient) - mod_pin
        mod_cut = cylinder(r=radius+self.knuckle_clearance, h=self.knuckle_inner_width[orient], center=True)
        if extend_cut != (0, 0):
            mod_cut = hull()(mod_cut, translate(extend_cut + (0,))(mod_cut))
        mod_main = rcylinder(r=radius, h=width, rnd=self.knuckle_rounding, center=True)
        return (mod_main + mod_washers) - mod_pin - mod_cut, mod_cut + mod_pin, mod_washers

    def knuckle_washers(self, orient):
        ''' the little built-in washers to reduce hinge friction '''
        r = self.knuckle_washer_radius + self.knuckle_pin_radius
        return cylinder(r=r, h=self.knuckle_width[orient] - self.knuckle_plug_thickness*2, center=True) - cylinder(r=r+1, h=self.knuckle_inner_width[orient] - self.knuckle_washer_thickness, center=True)

    def knuckle_inner(self, orient, cutout=False):
        ''' create the hinges at either end of a intermediate/middle segment '''
        width = self.intermediate_width[orient]
        radius = self.intermediate_height[orient]/2
        st_height = self.knuckle_inset_border*self.strut_height_ratio
        st_offset = self.knuckle_inset_border/2

        mod_hinge = cylinder(h=width, r=radius, center=True)
        #TODO 3 - make this more useful, cut only inset portion, all the way in past pin to reduce weight
        if cutout: mod_hinge -= translate((0, radius, 0))(cube((radius*2, radius, width+.1), center=True))
        mod_inset = self.knuckle_inset(radius, width)
        mod_pin = self.knuckle_pin(length=width + .01)

        #create anchor points for the struts
        anchor_tl = translate((radius -st_offset*self.strut_height_ratio, 0, width/2 - st_offset))(rotate((90, 0, 0))(self.strut(height=st_height)))
        anchor_tr = translate((radius -st_offset*self.strut_height_ratio, 0, -width/2 + st_offset))(rotate((90, 0, 0))(self.strut(height=st_height)))
        anchor_b = translate((-radius +st_offset*self.strut_height_ratio + self.knuckle_inset_depth, 0, 0))(rotate((90, 0, 0))(self.strut(height=st_height, width=width-(self.knuckle_inset_border*2)+width*.05)))

        return (mod_hinge - mod_inset - mod_pin, anchor_tl, anchor_tr, anchor_b)

    def knuckle_inset(self, radius, width):
        ''' create negative space for cutting the hinge inset to make room for tendons '''
        return cylinder(h=width - self.knuckle_inset_border * 2, r=radius + .01, center=True) \
            - cylinder(h=width - self.knuckle_inset_border * 2 + .01, r=radius - self.knuckle_inset_depth, center=True)

    def knuckle_pin(self, length=10):
        ''' create a pin for the hinge hole '''
        return cylinder(h=length, r=self.knuckle_pin_radius, center=True)

    def strut(self, width=0, height=0, length=.01):
        ''' create a strut that connects the two middle hinges  '''
        if width == 0: width = self.knuckle_inset_border
        if height == 0: height = self.knuckle_inset_border
        return rcube((height, width, length), rnd=self.strut_rounding, center=True)

    socket_interface_radius = property(lambda self: {Orient.DISTAL: self.socket_radius[Orient.DISTAL] - self.socket_interface_radius_offset, Orient.PROXIMAL: self.socket_radius[Orient.DISTAL] - self.socket_interface_radius_offset + self.socket_interface_flare_radius})

    def socket_interface(self, orient):
        ''' build an interface for the socket.  orient determines whether is for base or socket(cutout) with clearance'''
        socket_interface_base = .5
        length = (self.proximal_length + self.intermediate_height[Orient.PROXIMAL]/2)
        c = self.socket_interface_clearance if orient == Orient.OUTER else 0
        r = self.socket_interface_radius[Orient.PROXIMAL]-c - self.socket_interface_thickness
        h = self.socket_interface_length-socket_interface_base - self.socket_interface_thickness

        mod_core = cylinder(r2=self.socket_interface_radius[Orient.PROXIMAL]-c, r1=self.socket_interface_radius[Orient.DISTAL]-c, h=self.socket_interface_length-socket_interface_base) + \
            translate((0, 0, self.socket_interface_length-socket_interface_base- .01))(cylinder(r=self.socket_interface_radius[Orient.PROXIMAL]-c, h=socket_interface_base))
        mod_cut = sphere(r).resize((0, 0, h*2)).translate((0, 0, h+0.75))

        return translate((0, -length - self.distal_flange_height + .01, 0))(rotate((90, 0, 0))(mod_core - translate((0, 0, .01))(mod_cut)))

    def knuckle_plug(self, clearance):
        ''' plug cover for the knuckle pins'''
        clearance_val = self.knuckle_plug_clearance if clearance else 0
        r = self.knuckle_plug_radius - clearance_val
        h = self.knuckle_plug_thickness*.25 - clearance_val
        h2 = self.knuckle_plug_thickness*.75
        mod_plug = translate((0, 0, -h/2))( \
            cylinder(r1=r, r2=r+self.knuckle_plug_ridge, h=h2, center=True)) + \
            translate((0, 0, h2/2-0.01))(cylinder(r=r+self.knuckle_plug_ridge, h=h, center=True))
        return rotate((0, 0, 90))(mod_plug)

    def cross_strut(self):
        ''' center cross strut'''
        brace_length = min(self.intermediate_distal_width, self.intermediate_proximal_width) - self.knuckle_inset_border
        x_shift = self.intermediate_distal_height/2 -self.knuckle_inset_border/2
        h = self.knuckle_inset_border*self.knuckle_brace_height_factor
        mod_brace = translate((.5, self.distal_offset/2, 0))(
            hull()(translate((x_shift, 0, 0))(self.strut(height=h, length=brace_length)) + \
            translate((x_shift, 0, 0))(self.strut(height=h, length=brace_length+ self.knuckle_inset_border*.8))))
        return mod_brace

    def cut_model(self):
        ''' model to cut from preview for cutaway previwe'''
        return cube((30, 200, 30)).translate((0, -75, 0))

    #TODO 3 Socket
    #TODO 3 Socket scallops
    #TODO 3 Socket texture

    #TODO 3 Tip Cover
    #TODO 3 Tip Cover fingernail (ugh..)
    #TODO 3 Tip Cover fingerprints

    #TODO 2 Linkage
    #TODO 2 Linkage Hook

    #TODO 4 Bumper
    #************************************* utilities ****************************************

    def emit_scad(self):#, val, filename=None):
        ''' emit all models to SCAD code '''
        #print(self._mod)
        code = {}
        for filename in self._mod:
            val = self._mod[filename]
            tempval = None
            if iterable(val):
                for v in val:
                    tempval = v if not tempval else tempval + v
            if tempval: val = tempval
            if not filename:
                print("No filename, emitting to console")
                code[filename] = scad_render(val, file_header=self.scad_header)
            elif self.animate_explode or self.animate_rotate:
                print("Writing SCAD animation to %s/%s" % (self.output_directory, filename))
                scad_render_animated_file(self._animate_explosion, steps=20, back_and_forth=True, out_dir=self.output_directory, file_header=self.scad_header, include_orig_code=True, filepath=filename)
            else:
                print("Writing SCAD output to %s/%s" % (self.output_directory, filename))
                scad_render_to_file(val, out_dir=self.output_directory, file_header=self.scad_header, include_orig_code=True, filepath=filename)
        return code

    def render_stl(self):
        ''' render all modela to STL '''
        Renderer().scad_parallel_to_stl(self._mod.keys(), max_concurrent_tasks=4)
        return

    _mod = {}
    def build_models(self):
        ''' determine which models to emit, and organize by output filename '''
        file_template = "dangerfinger_%s_%s_gen.scad"
        mod = {}
        mod_preview = None
        for pv in FingerPart:#.self.part:
            #print(pv)
            if not self.part & pv: continue
            p = str.lower(str(pv.name) if isinstance(pv, FingerPart) else str(pv))
            part_name = "part_%s" % p
            #print(part_name)
            if not hasattr(self, part_name): continue
            mod_file = file_template % (VERSION, p)
            mod_segment = getattr(self, part_name)()
            if iterable(mod_segment):
                if self.preview_cut: mod_segment = [x - self.cut_model() for i, x in enumerate(mod_segment, 0)]
                if self.preview_rotate != 0: mod_segment = [rotate(self.rotate_offsets[p][i])(x) for i, x in enumerate(mod_segment, 0)]
                if self.preview_explode: mod_segment = [translate(self.explode_offsets[p][i])(x) for i, x in enumerate(mod_segment, 0)]
                mod_segment = [translate(self.translate_offsets[p][i])(x) for i, x in enumerate(mod_segment, 0)]
            else:
                if self.preview_cut: mod_segment = mod_segment - self.cut_model()
                if self.preview_explode: mod_segment = mod_segment.translate(self.explode_offsets[p])
                r = max(self._rotate_offsets[p], key=lambda v: v)
                if r != 0: mod_segment = mod_segment.rotate(self.rotate_offsets[p])
                if r > 2: mod_segment = mod_segment.rotate(self.rotate_offsets[p])
                mod_segment = mod_segment.translate(self.translate_offsets[p])
                if r > 1: mod_segment = mod_segment.rotate(self.rotate_offsets[p])

            mod_preview = mod_segment if not mod_preview else mod_preview + mod_segment
            mod[mod_file] = mod_segment
        self._mod.update(mod if not self.preview else {file_template % (VERSION, "preview"): mod_preview})
        return self._mod

    _animate_factor = 1
    def _animate_explosion(self, _time: Optional[float] = 0) -> OpenSCADObject:
        ''' special callback function for openscad animation'''
        self._animate_factor = max(_time -.3, 0)
        mod = self.build_models()
        return mod[list(mod.keys())[0]]

    #*************************************** special properties **********************************

    @property
    def explode_offsets(self):
        ''' amount to expand during explode'''
        return self._prop_offset(self._explode_offsets, self._animate_factor)
    _explode_offsets = { #TODO 1 - make these parametric
        "middle":(0, 20, 0), "base" : (0, 0, 0), "tip":(0, 40, 0), "socket":(0, -20, 0),
        "linkage" : (10, -30, 0), "tipcover" : (0, 50, 0), "plugs":((0, 0, -8), (0, 0, 8), (0, 40, -8), (0, 40, 20))}

    @property
    def translate_offsets(self):
        ''' amount to expand during explode'''
        return self._prop_offset(self._translate_offsets, self.distal_offset)
    _translate_offsets = {
        "middle":(0, 0, 0), "base" : (0, 0, 0), "tip":(0, 1, 0), "socket":(0, 0, 0),
        "linkage" : (0, 0, 0), "tipcover" : (0, 0, 0), "plugs":((0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0))}

    @property
    def rotate_offsets(self):
        ''' amount to expand during rotate'''
        return self._prop_offset(self._rotate_offsets, self._animate_factor * self.preview_rotate, func=lambda v: min(v, 1))
    _rotate_offsets = {
        "middle":(0, 0, 1), "base" : (0, 0, 0), "tip":(0, 0, 3), "socket":(0, 0, 0),
        "linkage" : (0, 0, 0), "tipcover" : (0, 0, 0), "plugs":((0, 0, 0), (0, 0, 0), (0, 0, 3), (0, 0, 3))}

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
        RenderQuality.FAST : 1, RenderQuality.ULTRAFAST : 1.5, RenderQuality.AUTO : 1 if self.preview else .2}[self.render_quality]))

    #the minimum dgrees of each polygon framgment , higher is faster
    fa = property(lambda self: ({
        RenderQuality.ULTRAHIGH : 1.5, RenderQuality.HIGH : 2, RenderQuality.EXTRAMEDIUM : 3, RenderQuality.MEDIUM : 4, RenderQuality.SUBMEDIUM : 5,
        RenderQuality.FAST : 6, RenderQuality.ULTRAFAST : 10, RenderQuality.AUTO : 6 if self.preview else 2}[self.render_quality]))

    scad_header = property(lambda self: ("$fa = %s; \n$fs = %s;\n" % (self.fa, self.fs)))

if __name__ == '__main__':
    sys.stdout = UnbufferedStdOut(sys.stdout)
    assemble()
