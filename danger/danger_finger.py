#!/bin/python
# pylint: disable=C0302, line-too-long, unused-wildcard-import, wildcard-import, invalid-name, broad-except
'''
The danger_finger copyright 2014-2020 Nicholas Brookins and Danger Creations, LLC
http://dangercreations.com/prosthetics :: http://www.thingiverse.com/thing:1340624
Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 https://creativecommons.org/licenses/by-nc-sa/4.0/
Source code licensed under Apache 2.0:  https://www.apache.org/licenses/LICENSE-2.0
'''
import math
from solid import *
from solid.utils import *
from solid.solidpython import OpenSCADObject
from .danger_finger_base import *

# ********************************** The danger finger *************************************
class DangerFinger(DangerFingerBase):
    ''' The actual finger model '''
    # #**************************************** finger bits ****************************************
    VERSION = 4.2

    def part_base(self):
        ''' Generate the base finger section, closest proximal to remnant '''
        tunnel_length = self.intermediate_height[Orient.PROXIMAL] * .4
       # tunnel_width = self.intermediate_width[Orient.PROXIMAL] + self.knuckle_side_clearance*2
        length = (self.proximal_length + self.intermediate_height[Orient.PROXIMAL]/2)
        trim_offset = self.knuckle_proximal_thickness +self.intermediate_proximal_width + self.knuckle_side_clearance-.01

        mod_core = translate((0, -length, 0))(rotate((90, 0, 0))(rcylinder(r=self.socket_interface_radius[Orient.DISTAL]+self.socket_thickness_distal, h=self.distal_flange_height))) #
        mod_hinge, mod_hinge_cut, mod_washers, mod_pin = self.knuckle_outer(orient=Orient.PROXIMAL, extend_cut=(-10, .5))
        mod_tunnel, _mod_bridge_cut = self.bridge(length=tunnel_length, tunnel_width=self.knuckle_inner_width[Orient.PROXIMAL] +0, orient=Orient.PROXIMAL | Orient.OUTER)
        mod_socket_interface = self.socket_interface(Orient.INNER)
        #TODO 3 allow resize of width for base/socket interface, once socket is done

        mod_plugs = self.part_plugs(clearance=False)
        mod_trim = cylinder(h=self.intermediate_proximal_width, r=self.intermediate_proximal_height/2 - self.knuckle_rounding, center=True)
        mod_side_trim = mod_trim.translate((0, 0, trim_offset)) + translate((0, 0, -trim_offset))(mod_trim)
        mod_tendon_hole = self.tendon_hole()
        mod_breather = cylinder(r=self.knuckle_inner_width[Orient.PROXIMAL]/5, h=20, center=True).rotate((90, 0, 0)).translate((0, -10, 0))
        mod_elastic = self.elastic_hole()
        #TODO 1 FIX BASE CUTOUT / depth

        radius = self.intermediate_height[Orient.PROXIMAL]/2
        mod_extra = cylinder(r=radius+self.knuckle_clearance, h=self.knuckle_inner_width[Orient.PROXIMAL], center=True)#.mod("*")
        mod_main = hull()(mod_core + mod_hinge) + hull()(mod_tunnel + mod_core)

        #TODO - hardcoded hack
        final = (mod_main - mod_plugs - mod_pin - mod_side_trim + mod_socket_interface - mod_hinge_cut.translate((self.tunnel_radius/2, 0, 0)) - mod_tendon_hole - mod_elastic - mod_breather- _mod_bridge_cut[0].translate((0.2, -2, 0)).resize((0, 0, self.knuckle_inner_width[Orient.PROXIMAL]))) - mod_extra + mod_washers - mod_pin
        return final.rotate((0, 0, 90))

    def part_tip(self):
        ''' Generate the tip finger knuckle section, most distal to remnant '''
        tunnel_length = self.intermediate_height[Orient.DISTAL]*.4
        plug_trans = diff(-self.knuckle_distal_width/2 + self.knuckle_plug_thickness/2 - 0.01, -self.knuckle_proximal_width/2 + self.knuckle_plug_thickness/2 - 0.01)

        mod_hinge, mod_hinge_cut, mod_washers, mod_pin = self.knuckle_outer(orient=Orient.DISTAL)
        mod_plugs = self.part_plugs(clearance=False)
        mod_plug_cut = mod_plugs[0].translate((0, 0, plug_trans)) + mod_plugs[1].translate((0, 0, -plug_trans))

        bridge = self.bridge(length=tunnel_length, tunnel_width=self.knuckle_inner_width[Orient.DISTAL] + self.knuckle_side_clearance*2, orient=Orient.DISTAL | Orient.OUTER)
        mod_tunnel = translate((0, tunnel_length, 0))(bridge[0])
        mod_bottom_trim = cube((self.intermediate_distal_height, 1, self.knuckle_width[Orient.DISTAL]), center=True).translate((-self.knuckle_plug_radius -self.intermediate_distal_height/2, self.distal_base_length-.25, 0))
        #TODO 3 allow resize of width for tip
        mod_core = rcylinder(r=self.tip_radius, h=0.1).rotate((90, 0, 0)).translate((0, self.distal_base_length, 0)) - mod_bottom_trim
        mod_interface = self.tip_interface()

        mod_top_detent = self.tip_detent()
        radius = self.intermediate_height[Orient.DISTAL]/2
        mod_extra = cylinder(r=radius+self.knuckle_clearance, h=self.knuckle_inner_width[Orient.DISTAL], center=True)
        mod_main = hull()(mod_core + mod_hinge) + hull()(mod_tunnel + mod_core)

        rc = self.bottom_strut_width[Orient.DISTAL] *2
        mod_bend_cut = rcube((rc, rc, self.tip_interface_post_radius), rnd=.3, center=True).rotate((0, 90, 0)).translate((-self.tip_interface_post_radius/2, self.distal_base_length-rc/2-.0101, 0)) #rcylinder(r=self.knuckle_inner_width[Orient.DISTAL]/1.9, h=self.tip_interface_post_radius, rnd=.5)
        mod_tip_hole = cylinder(r=self.tendon_hole_radius*1.5, h=20, center=True).rotate((90, 0, 0)).translate((0, self.intermediate_distal_height, 0))

        #TODO 1 Hacky hard coded, paired to the 10 in bridge
        final = ((mod_main + mod_interface + mod_top_detent - mod_plug_cut - mod_tip_hole - mod_hinge_cut - mod_bend_cut - mod_pin - bridge[1][1].translate((0, 9.0, 0)).resize((0, 0, self.knuckle_inner_width[Orient.DISTAL]))) - mod_extra.translate((-1, 0, 0)).mod("") + mod_washers - mod_pin)
        return final.rotate((0, 0, 90))

    def part_middle(self):
        ''' Generate the middle/intermediate finger section '''
        #a hinge at each end
        mod_dist_hinge, anchor_dtl, anchor_dtr, anchor_db = self.knuckle_inner(orient=Orient.DISTAL, cutout=self.knuckle_cutouts)
        mod_prox_hinge, anchor_ptl, anchor_ptr, anchor_pb = self.knuckle_inner(orient=Orient.PROXIMAL, cutout=self.knuckle_cutouts)
        mod_dist_hinge = mod_dist_hinge.rotate((180, 0, 0))
        # 3 struts and a cross brace
        mod_strut_tl = hull()(self.shift_distal()(anchor_dtl), anchor_ptl)
        mod_strut_tr = hull()(self.shift_distal()(anchor_dtr), anchor_ptr)
        mod_strut_b = hull()(self.shift_distal()(anchor_db), anchor_pb) #.mod("%")
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
        #TODO 2 Consider compressed hinge mode

        trim_c_d = cylinder(r=self.intermediate_height[Orient.DISTAL]/2 + self.knuckle_side_clearance*1, h=4, center=True)
        trim_c_p = cylinder(r=self.intermediate_height[Orient.PROXIMAL]/2 + self.knuckle_side_clearance*1, h=4, center=True)
        mod_side_trim_d = trim_c_d.translate((0, 0, self.intermediate_width[Orient.DISTAL]/2+1.99)) + trim_c_d.translate((0, 0, -self.intermediate_width[Orient.DISTAL]/2-1.99))
        mod_side_trim_p = trim_c_p.translate((0, 0, self.intermediate_width[Orient.PROXIMAL]/2+1.99)) + trim_c_p.translate((0, 0, -self.intermediate_width[Orient.PROXIMAL]/2-1.99))

        final = (self.shift_distal()(mod_dist_hinge + mod_tunnel_d) + mod_prox_hinge + mod_strut_tl + mod_strut_tr + mod_strut_b + mod_brace + mod_tunnel_p) - (self.shift_distal()(mod_side_trim_d), mod_side_trim_p)
        return final.rotate((0, 0, 90))

    def part_plugs(self, clearance=True):
        ''' plug covers for the knuckle pins'''
        plug = color(Blue)(self.knuckle_plug(clearance=clearance))
        p_offset = -self.knuckle_proximal_width/2 + self.knuckle_plug_thickness/2 - 0.01
        d_offset = -self.knuckle_distal_width/2 + self.knuckle_plug_thickness/2
        mod_plug_pl = translate((0, 0, p_offset))(plug)
        mod_plug_pr = rotate((0, 180, 0))(translate((0, 0, p_offset))(plug))
        mod_plug_dl = self.shift_distal()(plug.translate((0, 0, -d_offset- 0.1)))
        mod_plug_dr = self.shift_distal()(plug.rotate((0, 180, 0)).translate((0, 0, d_offset+.01)))
        return mod_plug_pl, mod_plug_pr, mod_plug_dl, mod_plug_dr

    def part_linkage(self):
        ''' The wrist linakge strut for securing the finger tendon '''
        mod_core = rcylinder(r=self.linkage_width/2, h=self.linkage_length, rnd=1.5, center=True).resize((self.linkage_width + .25, self.linkage_height, 0)) * cube((self.linkage_width, self.linkage_height, self.linkage_length), center=True)
        mod_core = mod_core.rotate((90, 90, 0))

        mod_hook = self.link_hook().translate(((self.linkage_hook_height - self.linkage_height)/2, -self.linkage_length/2 -self.linkage_hook_length/2 + self.linkage_hook_thickness*2.4, 0))
        mod_hook_left = mod_hook - cube((20, 20, 20), center=True).translate((0, -self.linkage_length/2 -10 + 1))
        mod_core_right = mod_core - cube((20, 200, 20), center=True).translate((0, 100 -self.linkage_length/2.5))
        mod_core_hull = hull()(mod_core_right + mod_hook_left)#.mod("%")

        mod_hole = cylinder(r=self.tendon_hole_radius, h=self.linkage_length/3).rotate((90, 90, 0)).translate((0, (self.linkage_length/3)*1.5+.01, 0)).resize((self.linkage_height/2.6, 0, 0))#.mod("%")
        mod_cross = cylinder(r=self.tendon_hole_radius, h=self.linkage_width+1, center=True).resize((self.linkage_height/3.2, 0, 0))
        mod_slit = cylinder(r=self.linkage_height/3.2/2, h=3).rotate((90, 90, 0))
        mod_cut = mod_cross.translate((0, self.linkage_length/3, 0)) + mod_cross.translate((0, self.linkage_length/3 + 3, 0)) + \
            mod_slit.translate((0, self.linkage_length/3 + 3, -self.linkage_width/1.9)) + \
            mod_slit.translate((0, self.linkage_length/3 + 3, self.linkage_width/1.9))
        final = mod_core + mod_hook + mod_core_hull - mod_hole - mod_cut#.mod("%")
        return final.rotate((0, 0, 90))

    def part_socket(self):
        ''' create the interface socket '''
        #r = self.socket_interface_radius[Orient.DISTAL] #- self.socket_interface_thickness
        #h = self.socket_interface_length-socket_interface_base - self.socket_interface_thickness

        #mod_core = cylinder(r2=self.socket_interface_radius[Orient.PROXIMAL]-c, r1=self.socket_interface_radius[Orient.DISTAL]-c, h=self.socket_interface_length-socket_interface_base) + \

        #TODO 3 Socket
        #TODO 3 Socket scallops
        #TODO 3 Socket texture
        length = (self.proximal_length + self.intermediate_height[Orient.PROXIMAL]/2)
        mod_core = cylinder(r1=self.socket_interface_radius[Orient.DISTAL] + self.socket_thickness[Orient.DISTAL], \
            r2=self.socket_interface_radius[Orient.PROXIMAL] + self.socket_thickness[Orient.PROXIMAL], h=self.socket_interface_length)
        mod_core = translate((0, -length - self.distal_flange_height -.01, 0))(rotate((90, 0, 0))(mod_core))
        mod_socket_interface = self.socket_interface(Orient.OUTER)
        mod_bottom = cylinder(r1=self.socket_interface_radius[Orient.PROXIMAL] + self.socket_thickness[Orient.PROXIMAL], r2=self.socket_radius[Orient.DISTAL]+ self.socket_thickness[Orient.DISTAL], h=4) + \
            cylinder(r1=self.socket_radius[Orient.DISTAL]+ self.socket_thickness[Orient.DISTAL], r2=self.socket_radius[Orient.PROXIMAL]+ self.socket_thickness[Orient.PROXIMAL], h=self.socket_depth - self.socket_interface_depth -4).translate((0, 0, 4))
        mod_bottom = translate((0, -length - self.distal_flange_height -.01 - self.socket_interface_length, 0))(rotate((90, 0, 0))(mod_bottom))
        final = color("blue")(mod_core - mod_socket_interface +mod_bottom)
        return final.rotate((0, 0, 90))

    def part_tipcover(self):
        ''' the finger tip flexible portion '''

        #TODO 3 Tip Cover
        #TODO 3 Tip Cover fingernail (ugh..)
        #TODO 3 Tip Cover fingerprints

        #h = self.distal_length-self.distal_base_length
        sr = self.tip_radius/1.5
        mod_core = cylinder(r=self.tip_radius, h=self.distal_base_length).rotate((90, 90, 0)).translate((0, self.intermediate_length + self.distal_base_length*2, 0))
        mod_sphere = sphere(r=sr).resize((self.tip_radius*1.2, 0, self.tip_radius*1.8)).translate((-self.tip_radius/3, self.intermediate_length + self.distal_length-sr, 0))
        final = color("blue")(hull()(mod_core + mod_sphere))
        return final.rotate((0, 0, 90))
    #**************************************** Primitives ***************************************

    def link_hook(self):
        ''' create the hooke for end of linkage '''
        linkage_loop_extrusion = 1.5
        #opening = 40
        mod_hook = resize((self.linkage_hook_height, self.linkage_hook_length, self.linkage_width))( \
                    rotate_extrude(convexity=3, angle=300)(
                        hull()(circle(d=self.linkage_hook_thickness).translate((linkage_loop_extrusion, -self.linkage_width/2, 0)), \
                            circle(d=self.linkage_hook_thickness).translate((linkage_loop_extrusion, self.linkage_width/2, 0))) \
                                ).rotate((0, 0, 160))).translate((0, self.linkage_hook_thickness/2, 0))

        mod_cut = cube((self.linkage_hook_thickness*2, self.linkage_hook_thickness*2, self.linkage_width+.01), center=True).translate((-2, self.linkage_hook_thickness*1.5, 0)) \
            - sphere(r=self.linkage_width/1.9).resize((self.linkage_height*1.2, 0, self.linkage_width*1.5)).translate((-self.linkage_width/3.14, -self.linkage_width/3.4, 0))#.mod("%")
        return difference()(mod_hook, mod_cut.translate((0, -self.linkage_hook_opening, 0)))#.mod("%"))

    def tip_detent(self):
        ''' create tendon detents '''
        # detent_thickness = 2.5
        # detent_width = 4
        detent_cut_width = .5
        # detent_narrow = 1.9
        # hole_offset = self.tip_interface_post_radius-2.5 + .3
        shift = self.distal_base_length + self.tip_detent_height/2 + self.tip_interface_post_height *2 - .1+ self.tip_interface_ridge_height -1 + self.tip_interface_clearance

        c1r = self.tip_interface_post_radius *.7
        h1r = self.tip_interface_post_radius *.45
        c1r2 = c1r + .2
        sl = self.tip_interface_post_radius *2

        c1 = cylinder(r=c1r, h=self.tip_detent_height*.8).rotate((90, 0, 0))
        c2 = cylinder(r=c1r2, h=self.tip_detent_height*.2).rotate((90, 0, 0)).translate((0, 0, 0))
        h1 = cylinder(r=h1r, h=self.tip_detent_height*1.01).rotate((90, 0, 0)).translate((0, self.tip_detent_height*.11, 0))
        b1 = cube((c1r*1.5, self.tip_detent_height, c1r*2.2), center=True).translate((c1r*1.1, -self.tip_detent_height*.36, 0))

        slit = hull()(cylinder(d=detent_cut_width*.65, h=sl), \
            cylinder(d=detent_cut_width, h=sl).translate((0, self.tip_detent_height*.6, 0))).translate((0, -self.tip_detent_height*.6, -sl/2))#.mod("%")
        return ((c1 + c2) - h1 - b1 \
            - slit - slit.rotate((0, -30, 0)) - slit.rotate((0, -60, 0)) - slit.rotate((0, 30, 0)) - slit.rotate((0, 60, 0)) - slit.rotate((0, 90, 0)) \
            ).translate((0, shift, 0))

        # mod = rcylinder(r=detent_width/2, h=self.tip_detent_height-1.5, rnd=.2).rotate((90, 0, 0)).resize((detent_thickness, 0, 0)).translate((0, detent_narrow/2-.1, 0)) \
        #     + rcylinder(r=detent_width/2, h=detent_narrow, rnd=0).rotate((90, 0, 0)).resize((detent_thickness, 0, detent_width/1.5)).translate((0, -self.tip_detent_height/2+detent_narrow/2, 0)) \
        #     - cube(size=(detent_thickness+.1, self.tip_detent_height, detent_cut_width), center=True).translate((0, -self.tip_detent_height/2 + detent_narrow+.3, 0))
        #     #cube(size=(detent_thickness, self.tip_detent_height, detent_width), center=True) \
        # return mod.rotate((0, 20, 0)).translate((-hole_offset + .75, shift, 1.6)) \
        #      + mod.rotate((0, -20, 0)).translate((-hole_offset+.75, shift, -1.6)) \
        #      + mod.rotate((0, 75, 0)).translate((-hole_offset+3.4, shift, 3.0)) \
        #      + mod.rotate((0, -75, 0)).translate((-hole_offset+3.4, shift, -3.0))



    def tip_interface(self):
        ''' the snap-on interface section to the soft tip cover'''
        mod_post = cylinder(r=self.tip_interface_post_radius - self.tip_interface_clearance, h=self.tip_interface_post_height+self.tip_interface_clearance, center=True)
        mod_ridge = cylinder(r=self.tip_interface_ridge_radius+self.tip_interface_post_radius - self.tip_interface_clearance, h=self.tip_interface_ridge_height, center=True).translate((0, 0, -self.tip_interface_post_height+.01))
        mod_core = mod_post + mod_ridge
        return mod_core.rotate((90, 0, 0)).translate((0, self.distal_base_length + self.tip_interface_post_height/2 + self.tip_interface_clearance/2 - .01, 0))

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
        l = (self.proximal_length + self.socket_interface_length + self.intermediate_proximal_height/2)
        sr = self.socket_radius[Orient.DISTAL] - self.socket_interface_radius_offset + r
        anchor = translate((sr/2, 0, 0))(resize((0, 0, self.tendon_hole_width))(rotate((90, 0, 0))(cylinder(r=r, h=0.1, center=True))))
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

        #TODO - 2 make bridge height configurable
        mod_cut_a = translate((0, 2 + (length if orient == (Orient.DISTAL | Orient.INNER) else -0), 0))( \
                rcylinder(h=tunnel_width, rnd=self.tunnel_inner_rounding, center=True, \
                    r=self.tunnel_inner_cutheight[orient_lat] - (1.75 if orient == (Orient.DISTAL | Orient.OUTER) else 0)))#TODO 2 - unhardcode this later
        mod_cut_b = translate((0, -10 + (length if orient == (Orient.DISTAL | Orient.INNER) else 0), 0))( \
                rcylinder(r=self.tunnel_inner_cutheight[orient_lat], h=tunnel_width, rnd=self.tunnel_inner_rounding, center=True))#.mod("%")

        if orient != (Orient.OUTER):
            mod_tunnel = mod_tunnel - hull()(mod_cut_a, mod_cut_b)
        return mod_tunnel, (mod_cut_a, mod_cut_b)

    def bridge_anchor(self, orient, length, top=False, inside=False, shift=False, rnd=False):
        ''' calculate tunnel widths for a variety of orientations. a mess of logic, but it's gotta go somewhere '''
        orient_lat = Orient.PROXIMAL if orient & Orient.PROXIMAL else Orient.DISTAL
        orient_part = Orient.INNER if orient & Orient.INNER else Orient.OUTER
        r = self.tunnel_radius

        height_top = self.intermediate_height[orient_lat] / 2 + self.tunnel_height
        height_bottom = self.intermediate_height[orient_lat] / 2 -.5 #adjust to not stick out from struts
        height = (height_top -r) if top else height_bottom

        top_inner_slant = self.strut_rounding + self.tunnel_inner_slant
        width_top_in = (self.intermediate_width[orient_lat] / 2) - (top_inner_slant if (orient_part == Orient.INNER) else 0)
        width_top_out = (self.intermediate_width[orient_lat] / 2) - (-.01 if (orient_part == Orient.INNER) else -self.tunnel_outer_flare) \
            + (.01 if (orient_lat == Orient.DISTAL and inside) else 0)

        width_bottom_in = self.intermediate_width[orient_lat] / 2
        width_bottom_out = self.knuckle_width[orient_lat] / 2  + (.01 if (orient_lat == Orient.DISTAL and inside) else -.5)

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
            anchor = translate((r/4 * -.5 if not top else r/4, -r/3, r/2*(-1 if shift else 1)))(sphere(r=r/2))
        return translate(dim)(anchor)

    def knuckle_outer(self, orient, extend_cut=(0, 0)):
        ''' create the outer hinges for base or tip segments '''
        radius = self.intermediate_height[orient]/2
        width = self.knuckle_width[orient]
        mod_pin = self.knuckle_pin(length=width + .01)#.mod("%")
        mod_washers = self.knuckle_washers(orient) - mod_pin
        mod_cut = cylinder(r=radius+self.knuckle_clearance, h=self.knuckle_inner_width[orient], center=True)
        if extend_cut != (0, 0):
            mod_cut = hull()(mod_cut, translate(extend_cut + (0,))(mod_cut))
        mod_main = rcylinder(r=radius, h=width, rnd=self.knuckle_rounding, center=True)
        return ((mod_main + mod_washers) - mod_pin) - mod_cut, mod_cut, mod_washers, mod_pin

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
        anchor_tl = translate((radius -st_offset * self.strut_height_ratio, 0, width/2 - st_offset))(rotate((90, 0, 0))(self.strut(height=st_height)))
        anchor_tr = translate((radius -st_offset * self.strut_height_ratio, 0, -width/2 + st_offset))(rotate((90, 0, 0))(self.strut(height=st_height)))
        #bottom anchor
        anchor_b = translate((-radius +st_offset * self.strut_height_ratio + self.knuckle_inset_depth, 0, 0))(
            rotate((90, 0, 0))(
                self.strut(height=st_height, width=self.bottom_strut_width[orient]))) #+width*.05

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

    def socket_interface(self, orient):
        ''' build an interface for the socket.  orient determines whether is for base or socket(cutout) with clearance'''
        socket_interface_base = .5
        length = (self.proximal_length + self.intermediate_height[Orient.PROXIMAL]/2)
        c = self.socket_interface_clearance if orient == Orient.INNER else 0
        r = self.socket_interface_radius[Orient.PROXIMAL]-c - self.socket_interface_thickness
        h = self.socket_interface_length-socket_interface_base - self.socket_interface_thickness

        mod_core = cylinder(r2=self.socket_interface_radius[Orient.PROXIMAL]-c, r1=self.socket_interface_radius[Orient.DISTAL]-c, h=self.socket_interface_length-socket_interface_base + (self.socket_interface_clearance*2 if orient == Orient.OUTER else 0)) + \
            translate((0, 0, self.socket_interface_length-socket_interface_base- .01))(cylinder(r=self.socket_interface_radius[Orient.PROXIMAL]-c, h=socket_interface_base))            #small base section
        mod_cut = sphere(r).resize((0, 0, h*2)) + cylinder(r=r, h=h).translate((0, 0, 0.01))
        mod_cut = mod_cut.translate((0, 0, h + self.socket_interface_depth))

        if orient == Orient.INNER:
            return translate((0, -length - self.distal_flange_height + .01, 0))(rotate((90, 0, 0))(mod_core - translate((0, 0, .01))(mod_cut)))
        return translate((0, -length - self.distal_flange_height + .01, 0))(rotate((90, 0, 0))(mod_core))

    def knuckle_plug(self, clearance):
        ''' plug cover for the knuckle pins'''
        clearance_val = self.knuckle_plug_clearance if clearance else 0
        r = self.knuckle_plug_radius - clearance_val
        h = self.knuckle_plug_thickness*.25 - clearance_val
        h2 = self.knuckle_plug_thickness*.75
        mod_plug = translate((0, 0, -h/2))( \
            cylinder(r1=r, r2=r+self.knuckle_plug_ridge, h=h2, center=True)) + \
            translate((0, 0, h2/2-0.01))(cylinder(r=r+self.knuckle_plug_ridge, h=h, center=True))
        return rotate((0, 0, 90))(mod_plug) #TODO - reverse rotate for left

    def cross_strut(self):
        ''' center cross strut'''
        brace_length = min(self.intermediate_distal_width, self.intermediate_proximal_width) - self.knuckle_inset_border
        x_shift = self.intermediate_distal_height/2 -self.knuckle_inset_border/2
        h = self.knuckle_inset_border*self.knuckle_brace_height_factor
        mod_brace = translate((.5, self.distal_offset/2, 0))(
            hull()(translate((x_shift, 0, 0))(self.strut(height=h, length=brace_length)) + \
            translate((x_shift, 0, 0))(self.strut(height=h, length=brace_length+ self.knuckle_inset_border*.8))))
        return mod_brace

    #TODO 4 Bumper
