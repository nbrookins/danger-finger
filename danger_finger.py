#!/bin/python
# pylint: disable=C0302, line-too-long, unused-wildcard-import, wildcard-import, invalid-name, broad-except
'''
The danger_finger copyright 2014-2020 Nicholas Brookins and Danger Creations, LLC
http://dangercreations.com/prosthetics :: http://www.thingiverse.com/thing:1340624
Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 https://creativecommons.org/licenses/by-nc-sa/4.0/
Source code licensed under Apache 2.0:  https://www.apache.org/licenses/LICENSE-2.0
'''
import os
import sys
from solid import *
from solid.utils import *
from solid.solidpython import OpenSCADObject
from danger_tools import *

VERSION = 4.1

# *********************************** Entry Point ****************************************
def assemble():
    ''' The entry point which loads a finger with proper parameters and outputs SCAD files as configured '''
    #create a finger object
    finger = DangerFinger()

    #sample param overrides for testing - comment out
    finger.preview = True
    finger.part = [FingerPart.BASE]
    finger.explode = True
   # finger.explode_animate = True
    finger.render_quality = RenderQuality.HIGH # FAST HIGH MEDIUM ULTRAHIGH SUBMEDIUM

    #load a configuration, with parameters from cli or env
    Params.parse(finger)

    #build some pieces
    mod_list = finger.render_models()
    for m in mod_list:
        finger.emit_scad(mod_list[m], filename=m)


# ********************************** The danger finger *************************************
class DangerFinger:
    ''' The actual finger model '''
    # ************************************* control params *****************************************

    preview = Prop(val=False, doc=''' Enable preview mode, emits all segments ''')
    render_quality = Prop(val=RenderQuality.AUTO, minv=RenderQuality.AUTO, maxv=RenderQuality.ULTRAFAST, doc='''- auto to use fast for preview.  higher quality take much longer for scad rendering''', adv=True, setter=lambda self, value: (value))
    explode = Prop(val=False, doc=''' Enable explode mode, only for preview ''')
    explode_animate = Prop(val=False, doc=''' Enable explode mode, only for preview ''')
    rotate_animate = Prop(val=False, doc=''' Enable explode mode, only for preview ''')
    rotate = Prop(val=0, minv=0, maxv=120, doc=''' rotate the finger ''') #TODO - implement finger:Rotate
    output_directory = Prop(val=os.getcwd(), doc=''' output_directory for scad code, otherwise current''')

    # **************************************** parameters ****************************************
    #TODO - make a first class "AUTO"
    intermediate_length = Prop(val=25, minv=8, maxv=30, doc=''' length of the intermediate finger segment ''')
    intermediate_distal_height = Prop(val=11.0, minv=4, maxv=8, doc=''' height of the middle section at the distal end.  roughly the height of the hinge circle ''')
    intermediate_proximal_height = Prop(val=13.0, minv=4, maxv=8, doc=''' height of the middle section at the proximal end.  roughly the height of the hinge circle ''')
    intermediate_height = property(lambda self: ({Orient.DISTAL: self.intermediate_distal_height, Orient.PROXIMAL: self.intermediate_proximal_height}))

    proximal_length = Prop(val=7, minv=8, maxv=30, doc=''' length of the proximal/base finger segment ''') #TODO - min auto of knuckle radius
    distal_length = Prop(val=24, minv=8, maxv=30, doc=''' length of the distal/tip finger segment ''')
    distal_base_length = Prop(val=6, minv=0, maxv=20, doc=''' length of the base of the distal/tip finger segment ''')
    length = property(lambda self: ({Orient.DISTAL: self.distal_length, Orient.PROXIMAL: self.proximal_length}))

    knuckle_proximal_width = Prop(val=16.5, minv=4, maxv=20, doc=''' width of the proximal knuckle hinge''')
    knuckle_distal_width = Prop(val=14.5, minv=4, maxv=20, doc=''' width of the distal knuckle hinge ''')
    knuckle_width = property(lambda self: ({Orient.DISTAL: self.knuckle_distal_width, Orient.PROXIMAL: self.knuckle_proximal_width}))

    socket_circumference_distal = Prop(val=55, minv=20, maxv=160, doc='''circumference of the socket closest to the base''')
    socket_circumference_proximal = Prop(val=62, minv=20, maxv=160, doc='''circumference of the socket closest to the hand''')
    socket_thickness_distal = Prop(val=2, minv=.5, maxv=4, doc='''thickness of the socket closest to the base''')
    socket_thickness_proximal = Prop(val=1.6, minv=.5, maxv=4, doc='''thickness of the socket at flare''')
    socket_clearance = Prop(val=-.25, minv=-2, maxv=2, doc='''Clearance between socket and base.  -.5 for Ninja flex and sloopy printing to +.5 for firm tpu and accurate''')

    knuckle_proximal_thickness = Prop(val=3.8, minv=1, maxv=5, doc=''' thickness of the hinge tab portion on proximal side  ''')
    knuckle_distal_thickness = Prop(val=3.4, minv=1, maxv=5, doc=''' thickness of the hinge tab portion on distal side ''')
    knuckle_thickness = property(lambda self: ({Orient.DISTAL: self.knuckle_distal_thickness, Orient.PROXIMAL: self.knuckle_proximal_thickness}))

    linkage_length = Prop(val=70, minv=10, maxv=120, doc=''' length of the wrist linkage ''')
    linkage_width = Prop(val=6.8, minv=4, maxv=12, doc=''' width of the wrist linkage ''')
    linkage_height = Prop(val=4.4, minv=3, maxv=8, doc=''' thickness of the wrist linkage ''')

    # ************************************* rare or non-recommended to muss with *************
    tunnel_height = Prop(val=1.7, minv=0, maxv=5, adv=True, doc=''' height of tendon tunnel ''')
    tunnel_inner_height = Prop(val=.65, minv=0, maxv=4.5, adv=True, doc=''' height of tendon tunnel ''')
    tunnel_radius = Prop(val=1.2, minv=0, maxv=4, adv=True, doc=''' radius of tendon tunnel rounding ''')
    tunnel_inner_slant = Prop(val=0.5, minv=0, maxv=4, adv=True, doc=''' inward slant of middle tunnels ''')
    tunnel_outer_flare = Prop(val=0.0, minv=0, maxv=5, adv=True, doc=''' outward slant of outer tunnels ''')

    knuckle_inset_border = Prop(val=2.2, minv=0, maxv=5, adv=True, doc=''' width of teh hinge inset, same as top strut width ''')
    knuckle_inset_depth = Prop(val=.75, minv=0, maxv=3, adv=True, doc=''' depth of the inset to clear room for tendons ''')
    knuckle_pin_radius = Prop(val=1.07, minv=0, maxv=3, adv=True, doc=''' radius of the hinge pin/hole ''')
    knuckle_plug_radius = Prop(val=3.0, minv=2, maxv=5, adv=True, doc=''' radius of the hinge pin cover plug ''') #TO-DO dynamic contraints?, must be less than hinge radius
    knuckle_plug_thickness = Prop(val=1.1, minv=0.5, maxv=4, adv=True, doc=''' thickness of the hinge pin cover plug ''')
    knuckle_plug_ridge = Prop(val=.3, minv=0, maxv=1.5, adv=True, doc=''' width of the plug holding ridge ''')
    knuckle_plug_clearance = Prop(val=.1, minv=-.5, maxv=1, adv=True, doc=''' clearance of the plug ''')
    knuckle_clearance = Prop(val=.4, minv=-.25, maxv=1, adv=True, doc=''' clearance of the rounded inner part of the hinges ''')

    intermediate_tunnel_length = Prop(val=.4, minv=-.25, maxv=2, adv=True, doc='''0-2 for the length of tunnels toward middle''')
    knuckle_rounding = Prop(val=.7, minv=0, maxv=4, adv=True, doc=''' amount of rounding for the outer hinges ''')
    tunnel_inner_rounding = Prop(val=1.2, minv=0, maxv=4, adv=True, doc=''' amount of rounding for the inner tunnel ''')
    knuckle_side_clearance = Prop(val=.2, minv=-.25, maxv=1, adv=True, doc=''' clearance of the flat circle side of the hinges ''')

    strut_height_ratio = Prop(val=.8, minv=.1, maxv=3, adv=True, doc=''' ratio of strut height to width (auto-controlled).  fractions make the strut thinner ''')
    strut_rounding = Prop(val=.4, minv=.5, maxv=2, adv=True, doc=''' 0 for no rounding, 1 for fullly round ''')

    socket_interface_length = Prop(val=5, minv=3, maxv=8, adv=True, doc=''' length of the portion that interfaces socket and base ''')

    knuckle_cutouts = Prop(val=False, adv=True, doc=''' True for extra cutouts on internals of intermediate section ''')

    knuckle_washer_radius = Prop(val=.6, minv=0, maxv=4, adv=True, doc=''' radius of the washers for lowering hinge friction ''')
    knuckle_washer_thickness = Prop(val=.5, minv=0, maxv=4, adv=True, doc=''' thickness of the washers for lowering hinge friction ''')



    #**************************************** dynamic properties ******************************

    intermediate_proximal_width = property(lambda self: (self.knuckle_proximal_width - self.knuckle_proximal_thickness*2 - self.knuckle_side_clearance*2))
    intermediate_distal_width = property(lambda self: (self.knuckle_distal_width - self.knuckle_distal_thickness*2 - self.knuckle_side_clearance*2))
    intermediate_width = property(lambda self: ({Orient.DISTAL: self.intermediate_distal_width, Orient.PROXIMAL: self.intermediate_proximal_width}))
    tunnel_inner_width = property(lambda self: ({Orient.DISTAL: self.intermediate_width[Orient.DISTAL]- self.knuckle_inset_border*2 + self.tunnel_radius/2, \
        Orient.PROXIMAL: self.intermediate_width[Orient.PROXIMAL]- self.knuckle_inset_border*2 + self.tunnel_radius/2}))
    tunnel_inner_cutheight = property(lambda self: ({Orient.DISTAL: self.intermediate_height[Orient.DISTAL] / 2 + self.tunnel_inner_height, \
        Orient.PROXIMAL: self.intermediate_height[Orient.PROXIMAL] / 2 + self.tunnel_inner_height}))
    knuckle_inner_width = property(lambda self: ({Orient.PROXIMAL: self.intermediate_width[Orient.PROXIMAL] + self.knuckle_side_clearance*2, \
         Orient.DISTAL: self.intermediate_width[Orient.DISTAL] + self.knuckle_side_clearance*2}))

    distal_offset = property(lambda self: (self.intermediate_length))#+ self.intermediate_distal_height / 2))
    shift_distal = lambda self: translate((0, self.distal_offset, 0))

    #**************************************** finger bits ****************************************

    def part_base(self):
        ''' Generate the base finger section, closest proximal to remant '''
        mod_hinge, mod_hinge_cut, mod_washers = self.knuckle_outer(orient=Orient.PROXIMAL)
        mod_plugs = self.part_plugs(clearance=False)
        tunnel_length = self.intermediate_height[Orient.PROXIMAL]*.4
        tunnel_width = self.intermediate_width[Orient.PROXIMAL]+ self.knuckle_side_clearance*2
        mod_tunnel, mod_bridge_cut = self.bridge(length=tunnel_length, tunnel_width=tunnel_width, orient=Orient.PROXIMAL | Orient.OUTER)

        mod_core = translate((0, -self.proximal_length, 0))(rotate((90, 0, 0))(rcylinder(r=self.knuckle_proximal_width/2 + 1, h=0.1)))
        trim_offset = tunnel_width + self.knuckle_proximal_thickness -.01
        mod_side_trim = hull()(translate((0, 0, trim_offset))(mod_hinge_cut), translate((0, -self.proximal_length, trim_offset))(mod_hinge_cut)) \
            + hull()(translate((0, 0, -trim_offset))(mod_hinge_cut), translate((0, -self.proximal_length, -trim_offset))(mod_hinge_cut))

        #TODO base socket interface
        #TODO base tendon tunnel

        return mod_hinge + hull()(mod_tunnel + mod_core) - mod_bridge_cut - mod_plugs - mod_hinge_cut + mod_washers - mod_side_trim

    def part_tip(self):
        ''' Generate the base finger section, closest proximal to remant '''
        mod_hinge, mod_hinge_cut, mod_washers = self.knuckle_outer(orient=Orient.DISTAL)
        mod_plugs = self.part_plugs(clearance=False)

        tunnel_length = self.intermediate_height[Orient.DISTAL]*.4
        bridge = self.bridge(length=tunnel_length, tunnel_width=self.knuckle_inner_width[Orient.DISTAL], orient=Orient.DISTAL | Orient.OUTER)
        mod_tunnel = translate((0, tunnel_length, 0))(bridge[0])
        mod_cut = translate((0, tunnel_length, 0))(bridge[1])
        mod_bottom_trim = translate((-self.knuckle_plug_radius -self.intermediate_distal_height/2, self.distal_base_length-.25, 0))(cube((self.intermediate_distal_height, 1, self.knuckle_width[Orient.DISTAL]), center=True))
        mod_core = translate((0, self.distal_base_length, 0))(rotate((90, 0, 0))(rcylinder(r=self.knuckle_distal_width/2 -.5, h=0.1))) - mod_bottom_trim
        #TODO Tip interface
        #TODO tip tendon detents

        return self.shift_distal()(mod_hinge + hull()(mod_tunnel+ mod_core) -mod_cut - mod_hinge_cut) - mod_plugs[2]- mod_plugs[3] + self.shift_distal()(mod_washers) #+ self.shift_distal()(mod_bottom_trim)

    def part_middle(self):
        ''' Generate the middle/intermediate finger section '''
        #a hinge at each end
        mod_dist_hinge, anchor_dtl, anchor_dtr, anchor_db = self.knuckle_inner(orient=Orient.DISTAL, cutout=self.knuckle_cutouts)
        mod_prox_hinge, anchor_ptl, anchor_ptr, anchor_pb = self.knuckle_inner(orient=Orient.PROXIMAL, cutout=self.knuckle_cutouts)
        mod_dist_hinge = rotate((180, 0, 0))(mod_dist_hinge)
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
        _mod_cut_d = rotate((180, 0, 0))(shift_tun(self, Orient.DISTAL)(bridge_d[1])) #translate((0, self.intermediate_height[Orient.DISTAL]*self.intermediate_tunnel_length, 0))(bridge_d[1])#rotate((180, 0, 0))(

        #trim_offset = self.tunnel_inner_width[Orient.DISTAL]
        trim_c_d = cylinder(r=self.intermediate_height[Orient.DISTAL]/2 + self.knuckle_side_clearance*1, h=4, center=True)
        trim_c_p = cylinder(r=self.intermediate_height[Orient.PROXIMAL]/2 + self.knuckle_side_clearance*1, h=4, center=True)
        mod_side_trim_d = translate((0, 0, self.intermediate_width[Orient.DISTAL]/2+1.99))(trim_c_d) + translate((0, 0, -self.intermediate_width[Orient.DISTAL]/2-1.99))(trim_c_d) #\
        mod_side_trim_p = translate((0, 0, self.intermediate_width[Orient.PROXIMAL]/2+1.99))(trim_c_p) + translate((0, 0, -self.intermediate_width[Orient.PROXIMAL]/2-1.99))(trim_c_p) #\
            #+ hull()(translate((0, 0, -trim_offset))(mod_hinge_cut), translate((0, -self.proximal_length, -trim_offset))(mod_hinge_cut))

        return self.shift_distal()(mod_dist_hinge + mod_tunnel_d) + mod_prox_hinge + mod_strut_tl + mod_strut_tr + mod_strut_b + mod_brace + mod_tunnel_p - self.shift_distal()(mod_side_trim_d) - mod_side_trim_p#+ self.shift_distal()(color(Red)(_mod_cut_d))  + _mod_cut_p

    def part_plugs(self, clearance=True):
        ''' plug covers for the knuckle pins'''
        plug = color(Blue)(self.knuckle_plug(clearance=clearance))
        p_offset = -self.knuckle_proximal_width/2 + self.knuckle_plug_thickness/2 - 0.01
        d_offset = -self.knuckle_distal_width/2 + self.knuckle_plug_thickness/2 - 0.01
        mod_plug_pl = translate((0, 0, p_offset))(plug)
        mod_plug_pr = rotate((0, 180, 0))(translate((0, 0, p_offset))(plug))
        mod_plug_dl = self.shift_distal()(translate((0, 0, d_offset))(plug))
        mod_plug_dr = self.shift_distal()(rotate((0, 180, 0))(translate((0, 0, d_offset))(plug)))
        return mod_plug_pl, mod_plug_pr, mod_plug_dl, mod_plug_dr

    #**************************************** Primitives ***************************************

    def bridge(self, length, orient, tunnel_width):
        ''' tendon tunnel for external hinges'''
        #assemble lots of variables, changing by orientation
        orient_lat = Orient.PROXIMAL if orient & Orient.PROXIMAL else Orient.DISTAL
        #generate our anchor points
        t_top_l_in = self.round_bridge_anchor(orient, length, top=True, inside=True, rnd=(orient&Orient.INNER))
        t_top_r_in = self.round_bridge_anchor(orient, length, top=True, inside=True, shift=True, rnd=(orient&Orient.INNER))
        t_top_l_out = self.round_bridge_anchor(orient, length, top=True, inside=False)
        t_top_r_out = self.round_bridge_anchor(orient, length, top=True, inside=False, shift=True)
        t_anchor_l_in = self.round_bridge_anchor(orient, length, top=False, inside=True, rnd=True)
        t_anchor_r_in = self.round_bridge_anchor(orient, length, top=False, inside=True, shift=True, rnd=True)
        t_anchor_l_out = self.round_bridge_anchor(orient, length, top=False, inside=False, rnd=(orient&Orient.OUTER))
        t_anchor_r_out = self.round_bridge_anchor(orient, length, top=False, inside=False, shift=True, rnd=(orient&Orient.OUTER))

        #hull them together, and cut the middle
        mod_tunnel = hull()(t_top_l_in, t_top_l_out, t_top_r_in, t_top_r_out, t_anchor_l_in, t_anchor_l_out, t_anchor_r_in, t_anchor_r_out)

        mod_cut = hull()(
            translate((0, 2 + (length if orient == (Orient.DISTAL | Orient.INNER) else 0), 0))(
                rcylinder(h=tunnel_width, rnd=self.tunnel_inner_rounding, center=True, r=self.tunnel_inner_cutheight[orient_lat] - (1.75 if orient == (Orient.DISTAL | Orient.OUTER) else 0))), #TODO - unhardcode this later
            translate((0, -10 + (length if orient == (Orient.DISTAL | Orient.INNER) else 0), 0))(
                rcylinder(r=self.tunnel_inner_cutheight[orient_lat], h=tunnel_width, rnd=self.tunnel_inner_rounding, center=True)))

        return mod_tunnel - mod_cut, mod_cut

    def round_bridge_anchor(self, orient, length, top=False, inside=False, shift=False, rnd=False):
        ''' calculate tunnel widths for a variety of orientations. a mess of logic, but it's gotta go somewhere '''
        orient_lat = Orient.PROXIMAL if orient & Orient.PROXIMAL else Orient.DISTAL
        orient_part = Orient.INNER if orient & Orient.INNER else Orient.OUTER

        r = self.tunnel_radius

        top_inner_slant = self.strut_rounding + self.tunnel_inner_slant
        width_top_in = (self.intermediate_width[orient_lat] / 2) - (top_inner_slant if (orient_part == Orient.INNER) else 0)
        width_top_out = (self.intermediate_width[orient_lat] / 2) - (-.01 if (orient_part == Orient.INNER) else -self.tunnel_outer_flare) \
            + (.01 if (orient_lat == Orient.DISTAL and inside) else 0)

        width_bottom_in = self.intermediate_width[orient_lat] / 2 #self.knuckle_width[orient_lat] / 4
        if orient_part == Orient.OUTER:
            width_bottom_out = self.knuckle_width[orient_lat] / 2  + (.01 if (orient_lat == Orient.DISTAL and inside) else 0)
        else: #INNER
            width_bottom_out = self.intermediate_width[orient_lat] / 2  + (1 if (inside) else 0)

        if orient & Orient.OUTER:
            #TODO - unhardcode this based on tip width, when defined
            width = width_bottom_out if not top else width_top_out -1 if orient_lat == Orient.DISTAL and inside else width_top_out
        else:
            if inside: #inside middle
                width = (width_top_in if top else width_bottom_in - self.strut_rounding) #inner bottom slant inward
            else: #outside middle
                width = (width_top_out if top else width_bottom_in)
        width -= r
        if shift: width = -width

        height_top = self.intermediate_height[orient_lat] / 2 + self.tunnel_height
        height_bottom = self.intermediate_height[orient_lat] / 2
        if orient_part == Orient.INNER and inside:
            height_bottom += r #adjust to not stick uot from struts
        #TODO - unhard code this based on tip height, not yet defined
        height = (height_top + (-.5 if inside and orient == (Orient.DISTAL | Orient.OUTER) else 0)) if top else height_bottom
        height -= r

        length = 0 if inside else -length

        dim = (height, length, width)
        anchor = rotate((90, 0, 0))(cylinder(r=r, h=.01))
        if rnd:
            sr = r/2
            anchor = translate((sr/2 * -.5 if not top else 0, -sr/2, 0))(sphere(r=sr)) #sr/4 * (1*1.5  if not shift and inside else -.5)
        return translate(dim)(anchor)

    def knuckle_outer(self, orient):#, cut_width=-1):#, radius, width):
        ''' create the outer hinges for base or tip segments '''
        radius = self.intermediate_height[orient]/2
        width = self.knuckle_width[orient]
        mod_pin = self.knuckle_pin(length=width + .01)
        mod_washers = self.knuckle_washers(orient) - mod_pin
        mod_cut = cylinder(r=radius+self.knuckle_clearance, h=self.knuckle_inner_width[orient], center=True)
        mod_main = rcylinder(r=radius, h=width, rnd=self.knuckle_rounding, center=True)
        return (mod_main + mod_washers) - mod_pin - mod_cut, mod_cut, mod_washers

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
        #TODO - make this more useful, cut only inset portion, all the way in past pin to reduce weight
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

    knuckle_brace_factor = .3
    def cross_strut(self):
        ''' center cross strut'''
        brace_length = min(self.intermediate_distal_width, self.intermediate_proximal_width) - self.knuckle_inset_border
        x_shift = self.intermediate_distal_height/2 -self.knuckle_inset_border/2
        h = self.knuckle_inset_border*self.knuckle_brace_factor
        mod_brace = translate((.5, self.distal_offset/2, 0))(
            hull()(translate((x_shift, 0, 0))(self.strut(height=h, length=brace_length)) + \
            translate((x_shift, 0, 0))(self.strut(height=h, length=brace_length+ self.knuckle_inset_border*.8))))
        return mod_brace

    #TODO Socket
    #TODO Socket scallops
    #TODO Socket texture

    #TODO Tip Cover
    #TODO Tip Cover fingernail (ugh..
    #TODO Tip Cover fingerprints

    #TODO Linkage
    #TODO Linkage Hook

    #TODO Bumper?
    #************************************* utilities ****************************************

    def emit_scad(self, val, filename=None):
        ''' emit the provided model to SCAD code '''
        if not filename:
            return scad_render(val, file_header=self.scad_header)
        elif self.explode_animate:
            print("Writing SCAD animation to %s/%s" % (self.output_directory, filename))
            return scad_render_animated_file(self._animate_explosion, steps=20, back_and_forth=True, out_dir=self.output_directory, file_header=self.scad_header, include_orig_code=True, filepath=filename)
        else:
            print("Writing SCAD output to %s/%s" % (self.output_directory, filename))
            return scad_render_to_file(val, out_dir=self.output_directory, file_header=self.scad_header, include_orig_code=True, filepath=filename)

    def render_models(self):
        ''' determine which models to emit, and organize by output filename '''
        file_template = "dangerfinger_%s_%s_gen.scad"
        mod = {}
        mod_preview = None
        for pv in self.part:
            p = str.lower(str(pv.name) if isinstance(pv, FingerPart) else str(pv))
            if not hasattr(self, "part_%s" % p): continue
            mod_segment = getattr(self, "part_%s" % p)()
            mod_file = file_template % (VERSION, p)
            if self.explode:
                if iterable(mod_segment):
                    new_mod = []
                    for s in mod_segment:
                        offs = self.explode_offsets[p][len(new_mod)]
                        new_mod.append(translate(offs)(s))
                    mod_segment = new_mod
                else:
                    offs = self.explode_offsets[p]
                    #print("offset %s" % str(offs))
                    mod_segment = translate(offs)(mod_segment)
            mod_preview = mod_segment if not mod_preview else mod_preview + mod_segment
            mod[mod_file] = mod_segment
            #write it to a scad file (still needs to be rendered by openscad)
        return mod if not self.preview else {file_template % (VERSION, "preview"): mod_preview} #TODO - implement FingerPart.ALL for preview

    _explode_factor = 1
    def _animate_explosion(self, _time: Optional[float] = 0) -> OpenSCADObject:
        ''' test'''
        self._explode_factor = max(_time -.3, 0)
        #print(self._explode_factor)
        mod = self.render_models()
        return mod[list(mod.keys())[0]]

    #*************************************** special properties **********************************

    @property
    def explode_offsets(self):
        ''' amount to expand during explode'''
        offs = self._explode_offsets
        new_offs = {}
        for o in offs:
            if isinstance(offs[o][0], (int, float)):
                new_offs[o] = (offs[o][0] * self._explode_factor, offs[o][1] * self._explode_factor, offs[o][2] * self._explode_factor)
            else:
                new_sub = []
                for v in offs[o]:
                    new_sub.append((v[0] * self._explode_factor, v[1] * self._explode_factor, v[2] * self._explode_factor))
                new_offs[o] = new_sub
        return new_offs

    _explode_offsets = {
        "middle":(0, 20, 0),
        "base" : (0, 0, 0),
        "tip":(0, 40, 0),
        "plugs":((0, 0, -8), (0, 0, 8), (0, 40, -8), (0, 40, 8))}

    _part = []
    @property
    def part(self):
        ''' select which part to print. list of FingerPart enums'''
        return [e for e in FingerPart] if self.preview else self._part
    @part.setter
    def part(self, val):
        self._part = val

    #The minimum circumferential length of a polygon segment.  higher is faster
    fs = property(lambda self: ({
        RenderQuality.ULTRAHIGH : .1,
        RenderQuality.HIGH : .2,
        RenderQuality.EXTRAMEDIUM : .3,
        RenderQuality.MEDIUM : .4,
        RenderQuality.SUBMEDIUM : .6,
        RenderQuality.FAST : 1,
        RenderQuality.ULTRAFAST : 1.5,
        RenderQuality.AUTO : 1 if self.preview else .2
        }[self.render_quality]))

    #the minimum dgrees of each polygon framgment , higher is faster
    fa = property(lambda self: ({
        RenderQuality.ULTRAHIGH : 1.5,
        RenderQuality.HIGH : 2,
        RenderQuality.EXTRAMEDIUM : 3,
        RenderQuality.MEDIUM : 4,
        RenderQuality.SUBMEDIUM : 5,
        RenderQuality.FAST : 6,
        RenderQuality.ULTRAFAST : 10,
        RenderQuality.AUTO : 6 if self.preview else 2
        }[self.render_quality]))

    scad_header = property(lambda self: ("$fa = %s; \n$fs = %s;\n" % (self.fa, self.fs)))

if __name__ == '__main__':
    assemble()
