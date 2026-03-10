#!/bin/python
# pylint: disable=C0302, line-too-long, unused-wildcard-import, wildcard-import, invalid-name, broad-except
'''
The danger_finger copyright 2014-2026 Nicholas Brookins and Danger Creations, LLC
http://dangercreations.com/prosthetics :: http://www.thingiverse.com/thing:1340624
Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 https://creativecommons.org/licenses/by-nc-sa/4.0/
Source code licensed under Apache 2.0:  https://www.apache.org/licenses/LICENSE-2.0
'''
from solid2 import *
from danger.constants import *
from danger.finger_base import *

# RGB 0-1 for SCAD color(); matches web PREVIEW_PART_COLORS for comparing part_all STL to web preview
PART_COLORS = {
    "tip": [0.753, 0.224, 0.169],       # #c0392b
    "base": [0.161, 0.502, 0.725],      # #2980b9
    "linkage": [0.153, 0.682, 0.376],   # #27ae60
    "middle": [0.827, 0.329, 0.0],     # #d35400
    "tipcover": [0.557, 0.267, 0.678], # #8e44ad
    "socket": [0.086, 0.627, 0.522],   # #16a085
    "stand": [0.498, 0.549, 0.553],    # #7f8c8d
    "pins": [0.173, 0.243, 0.314],     # #2c3e50
    "plug": [0.902, 0.494, 0.133],     # #e67e22
    "peg": [0.902, 0.494, 0.133],      # same as plug
    "bumper": [0.498, 0.549, 0.553],   # same as stand (gray)
}

#TODO - make snap knucles instead of pins?
# ********************************** The danger finger *************************************
class DangerFinger(DangerFingerBase):
    ''' The actual finger model '''
    # #**************************************** finger bits ****************************************
    VERSION = 5.3

    def make_bridge(self, orient, scale_z=None, scale_x=1.0, translate_z=None, rnd1=0, rnd2=None):
        """Build a parametric bridge using rcubecyl with standard trim and cutout.

        Parameters:
        - orient: Orient.PROXIMAL or Orient.DISTAL
        - scale_z, scale_x: scale factors to apply
        - translate_z: Z translation (Y local coord after rotation)
        - rnd1, rnd2: rounding params for rcubecyl

        Returns: trimmed and cut bridge object
        """
        l = self.intermediate_distal_height + self.tunnel_height * 2
        rwid = 3
        avgk = (self.knuckle_width_[Orient.DISTAL] + self.knuckle_width_[Orient.PROXIMAL]) / 2

        # Select orient-specific dimensions and defaults
        if orient == Orient.PROXIMAL:
            trim_dim = self.intermediate_proximal_height
            trim_z = self.knuckle_width_[Orient.PROXIMAL] - self.knuckle_rounding * 4
            if scale_z is None: scale_z = 1.1
            if translate_z is None: translate_z = rwid/3 + self.strut_rounding + 0.1
        else:  # DISTAL
            trim_dim = self.intermediate_distal_height#+3
            trim_z = self.intermediate_width_[Orient.DISTAL]
            if scale_z is None: scale_z = 1.0
            if translate_z is None: translate_z = -rwid/3 - self.strut_rounding
            if scale_x == 1.0: scale_x = 0.9

        # Build core bridge
        bridge = rcubecyl(h=rwid, l=l, w=avgk/2+2, t=self.intermediate_distal_height*.5,
                          rnd1=rnd1, rnd2=rnd2, center=True)
        bridge = bridge.scaleZ(scale_z).scaleX(scale_x).translate((1, translate_z, 0))
        bridge = bridge.trim((trim_dim+3, 0, trim_z), offset=(trim_dim, 0, 0))

        # Subtract cylinder cutout
        cylinder_cut = cylinder(r=self.intermediate_width_[orient]/2, h=10, center=True)\
                       .rotate((90,0,0)).scaleZ(1.3).translate((.5,0,0))#.debug()

        return bridge - cylinder_cut

    def part_base(self):
        ''' Generate the base finger section, closest proximal to remnant '''
        tunnel_length = self.intermediate_height_[Orient.PROXIMAL] * .4
        length = (self.proximal_length + self.intermediate_height_[Orient.PROXIMAL]/2)
        trim_offset = self.knuckle_proximal_thickness + self.intermediate_width_[Orient.PROXIMAL] + self.knuckle_side_clearance-.01
        mod_core = self._mod_core(length)#.debug() #
        mod_hinge, mod_hinge_cut, mod_washers, mod_pin = self.knuckle_outer(orient=Orient.PROXIMAL, rnd=self.knuckle_inner_rounding, extend_cut=(-16, -.35))#TODO - confgi s
        mod_tunnel, _mod_bridge_cut = self.bridge(length=tunnel_length, tunnel_width=self.knuckle_inner_width_[Orient.PROXIMAL] +0, orient=Orient.PROXIMAL | Orient.OUTER)

        bridge_p = self.make_bridge(Orient.PROXIMAL, rnd1=0, rnd2=0)#.debug()
        mod_tunnel += bridge_p.translate((0, -3, 0))

        mod_socket_interface, sock_cut = self.socket_interface(Orient.INNER, ridges=True)
        #TODO 3 allow resize of width for base/socket interface, once socket is done

        mod_plugs = self.part_plugs(clearance=False, extra=True)
        mod_trim = cylinder(h=self.intermediate_proximal_width_-5, r=self.intermediate_proximal_height/2 - self.knuckle_rounding, center=True)#.debug()
        mod_side_trim = mod_trim.translate((0, 0, trim_offset)) + mod_trim.translate((0, 0, -trim_offset))#.debug()
        # local values (previously class-level Props)
        breather_radius_factor = 0.2
        breather_height = 20
        breather_translate_y = -10
        bridge_cut_translate_x = 0.2
        bridge_cut_translate_y = -2.0

        mod_breather = cylinder(r=self.knuckle_inner_width_[Orient.PROXIMAL]*breather_radius_factor, h=breather_height, center=True).rotate((90, 0, 0)).translate((0, breather_translate_y, 0))
        mod_elastic = self.elastic_hole(double=True)
        mod_extra = self._mod_extra(Orient.PROXIMAL, rnd=self.knuckle_inner_rounding)#.debug()
        mod_main = (mod_core + mod_hinge).hull() + (mod_tunnel + mod_core).hull()

    #TODO - hack hack hack
        front_cut = cube((1,1.5,self.knuckle_width_[Orient.PROXIMAL]),center=True).rotate((0,0,10)) \
             .translate((-self.intermediate_proximal_height/2 - 1.7,-self.intermediate_proximal_height/2 + .65,0))#.debug()

        if self.knuckle_tendon_offset > 0:
            mod_tendon_hole = self.tendon_hole(shift=self.knuckle_tendon_offset)
            mod_main += self._tendon_bulge(mod_core) - sock_cut
        else:
            mod_tendon_hole = self.tendon_hole()

        #TODO - hardcoded hack
        final = (mod_main - (mod_plugs[0]+mod_plugs[1]+mod_plugs[2]+mod_plugs[3]) - mod_pin - mod_side_trim + \
                    mod_socket_interface - mod_hinge_cut.translate(self.tunnel_radius/2, .001, 0) \
                    - mod_tendon_hole - mod_elastic - mod_breather - _mod_bridge_cut[0].translate(bridge_cut_translate_x, bridge_cut_translate_y, 0).resize(0, 0, self.knuckle_inner_width_[Orient.PROXIMAL])
                    ) - mod_extra + mod_washers - mod_pin    - front_cut #- mod_cut_fist.debug()+ mod_shell
        return final.color(PART_COLORS["base"])#.rotate((0, 0, 90))

    tip_bottom_trim_x_extra = -2

    def part_tip(self):
        ''' Generate the tip finger knuckle section, most distal to remnant '''
        tunnel_length = self.intermediate_height_[Orient.DISTAL]*.4
        # local defaults for tip-specific params (previously Props)
        tip_fist_trim_rotate = -25
        tip_fist_trim_y_offset = -4.05
        peg_support_radius = 1.2
        peg_support_h = 10
        peg_support_translate_y = 10
        peg_support_translate_z = 3.4
        peg_support_side_x_offset = 1.65
        #peg_support_translate_z_offset = -1.5
        plug_trans = diff(-self.knuckle_distal_width/2 + self.knuckle_plug_thickness/2 - 0.01, -self.knuckle_proximal_width/2 + self.knuckle_plug_thickness/2 - 0.01)
        mod_hinge, mod_hinge_cut, mod_washers, mod_pin = self.knuckle_outer(orient=Orient.DISTAL)
        mod_plugs = self.part_plugs(clearance=False)
        mod_plug_cut = mod_plugs[0].translate((0, 0, plug_trans)) + mod_plugs[1].translate((0, 0, -plug_trans))
        bridge, cut = self.bridge(length=tunnel_length, tunnel_width=self.knuckle_inner_width_[Orient.DISTAL] + self.knuckle_side_clearance*2, orient=Orient.DISTAL | Orient.OUTER)

        bridge_d = self.make_bridge(Orient.DISTAL, scale_z=1.0, scale_x=0.9, rnd1=0, rnd2=0)
        bridge += bridge_d.translate((0, -1, 0))

        mod_tunnel = translate((0, tunnel_length, 0))(bridge)

        mod_bottom_trim = cube((self.intermediate_distal_height, 10, self.knuckle_width_[Orient.DISTAL]), center=True).translate(
            (-self.knuckle_plug_radius -self.intermediate_distal_height/2 + self.tip_bottom_trim_x_extra, self.distal_base_length-.25, 0))#.debug()

#TODO - HACK
        mod_fist_trim = cube((self.intermediate_distal_height, 10, self.knuckle_inner_width_[Orient.DISTAL]), center=True).rotate((0,0,tip_fist_trim_rotate)).translate(
            (-self.knuckle_plug_radius -self.intermediate_distal_height/2-1, self.distal_base_length + tip_fist_trim_y_offset , 0)) #.debug()

        #TODO 3 allow resize of width for tip
        mod_core = rcylinder(r=self.tip_radius, h=0.1).rotate((90, 0, 0)).translate((0, self.distal_base_length, 0)) - mod_bottom_trim
        mod_interface = self.tip_interface(chamfer_out=True, chamfer_in=False) #- mod_bottom_trim

        #mod_top_detent = self.tip_detent()
        mod_extra = self._mod_extra(Orient.DISTAL)#.debug()
        mod_extra = hull()(mod_extra +mod_extra.translate((-3,-.5,0)))#.debug()

        mod_main = (mod_core + mod_hinge).hull() + (mod_tunnel + mod_core).hull() - mod_fist_trim
        cy = cylinder(r=peg_support_radius,h=peg_support_h).rotate((90,0,0)).translate((0,peg_support_translate_y,0))
        mod_tip_hole = (self.part_peg(fs=60, hollow=False).translate((0.5,1,0))
                + cy.translate((peg_support_side_x_offset,0,-peg_support_translate_z))
                + cy.translate((peg_support_side_x_offset,0,peg_support_translate_z))
                + cy.translate((-peg_support_side_x_offset-.5,0,-peg_support_translate_z+.95))
                + cy.translate((-peg_support_side_x_offset-.5,0,peg_support_translate_z-.95)) )#.translate((0,0,peg_support_translate_z_offset))

        #TODO 1 Hacky hard coded, paired to the 10 in bridge #3rd: + mod_top_detent    //mod_bend_cut -
        final = ((mod_main  + mod_interface  - mod_plug_cut - mod_tip_hole - mod_hinge_cut -  mod_pin \
                  - cut[1].translate(0, 9.0, 0).resize(0, 0, self.knuckle_inner_width_[Orient.DISTAL])) \
                    - mod_extra + mod_washers - mod_pin) #.mod("")
        return final.translate((0,self.intermediate_length,0)).color(PART_COLORS["tip"])#.rotate((0, 0, 90))

    def part_middle(self):
        ''' Generate the middle/intermediate finger section '''
        #a hinge at each end
        mod_dist_hinge, anchor_dtl, anchor_dtr, anchor_db = self.knuckle_inner(orient=Orient.DISTAL, cutout=self.knuckle_cutouts, holes=True)
        mod_prox_hinge, anchor_ptl, anchor_ptr, anchor_pb = self.knuckle_inner(orient=Orient.PROXIMAL, cutout=self.knuckle_cutouts, holes=True)
        mod_dist_hinge = mod_dist_hinge.rotate((180, 0, 0))
        ## 3 struts and a cross brace
        mod_strut_tl = (anchor_dtl.translate(0, self.distal_offset_, 0)+ anchor_ptl).hull()
        mod_strut_tr = (anchor_dtr.translate(0, self.distal_offset_, 0)+ anchor_ptr).hull()
        mod_strut_b =  (anchor_db.rotate((0,0,self.intermediate_strut_rotate))
                        .translate(0, self.distal_offset_ - 3.75, 0)+ anchor_pb).hull() #.mod("%")
        mod_brace = self.cross_strut()#.debug() #TODO - fix hardcode
        #TODO - param for cross strut width

        #mid rounded bumper. self.intermediate_bumper_width #(self.knuckle_width_[Orient.PROXIMAL])
        rwid = 3 #(self.knuckle_proximal_thickness + self.knuckle_distal_thickness)/2 + self.intermediate_width_[Orient.DISTAL] + self.knuckle_side_clearance-.01
        mid_cut = cube(0)
        avg = (self.intermediate_width_[Orient.DISTAL] +self.intermediate_width_[Orient.PROXIMAL])/2
        avgk = (self.knuckle_width_[Orient.DISTAL] +self.knuckle_width_[Orient.PROXIMAL])/2
        if self.intermediate_bumper_style==BumperStyle.NONE:
            mod_mid_round = cube(0)
        else:
            rwid = 3
            mod_mid_round = rcylinder(r=avg/2, h=rwid, rnd=self.strut_rounding*2, center=True).hull()#.debug()

            mid_cut =      (cylinder(r=avg/2-1.7, h=rwid+.1, center=True).scale(.95,1.15,1) +\
                            cylinder(r=avg/4.0, h=rwid+.1, center=True).translate((self.tunnel_height/1.5,0,0))).hull() +\
                                (cube((10,10,10),center=True).translate((avg-1.7 ,0,0)) if not self.intermediate_bumper_style==BumperStyle.FULL else cube(0))

            #TODO - parametrics
            mod_mid_round = (mod_mid_round-mid_cut).rotate((90,0,0)) \
                .translate((1.3,self.intermediate_length/2 + .2,0))\
                .resizeX((self.intermediate_distal_height-self.knuckle_rounding)).resizeZ((self.knuckle_width_[Orient.PROXIMAL]))

        tendon = cylinder(0)
        if self.intermediate_bumper_style==BumperStyle.FULL or self.intermediate_bumper_style==BumperStyle.COVER:
            cover = self.intermediate_bumper_style==BumperStyle.COVER
            #mod_mid_round = mod_mid_round.resizeX((self.intermediate_distal_height+self.tunnel_height*2)).translate((-self.tunnel_height/2+self.tunnel_inner_rounding/2,0,0))
            l=self.intermediate_distal_height+self.tunnel_height*2
            tendon = rcylinder(h=rwid+.5, rnd=.5, r=self.tendon_hole_radius,center=True).scale((.6,1.1,1.4)).rotate((90,0,0)).translate((-avg/2 + self.tendon_hole_radius/1,self.intermediate_length/2+.2,0)).hull()#.debug()

            mod_mid_round = self._create_cover_bumper(1.8, l, avgk-1.0, avg, t=self.intermediate_distal_height*.5) if cover else \
                self._create_cover_bumper(rwid, l, avgk, avg,t=self.intermediate_distal_height*.5)
                                #- cylinder(r=avg/2, h=10, center=True).rotate((90,0,0)).scaleZ(1.1).resizeX(avg-1.5).translate((.5,0,0))#.debug()
            bridge_p = self.make_bridge(Orient.PROXIMAL, rnd1=0, rnd2=self.strut_rounding*2)
            bridge_d = self.make_bridge(Orient.DISTAL, scale_z=1.0, scale_x=0.9, rnd1=self.strut_rounding*2, rnd2=0)
            mod_mid_round = mod_mid_round.translate(1,self.intermediate_length/2,0)
        else:
            #tunnel at each end
            bridge_p, pcut = self.create_bridge(r=self.tunnel_radius, length=self.intermediate_tunnel_length, width=self.intermediate_proximal_width_-.023, rnd=self.tunnel_inner_rounding,
                        tunnel_width=self.tunnel_inner_width_[Orient.PROXIMAL], height=self.intermediate_height_[Orient.PROXIMAL] / 2 + self.tunnel_height - self.tunnel_radius,
                        tunnel_height=self.tunnel_inner_cutheight_[Orient.PROXIMAL] )

            bridge_d, dcut = self.create_bridge(r=self.tunnel_radius, length=self.intermediate_tunnel_length, width=self.intermediate_distal_width_, rnd=self.tunnel_inner_rounding,
                        tunnel_width=self.tunnel_inner_width_[Orient.DISTAL], height=self.intermediate_height_[Orient.DISTAL] / 2 + self.tunnel_height - self.tunnel_radius,
                        tunnel_height=self.tunnel_inner_cutheight_[Orient.DISTAL] )#
            bridge_d = bridge_d.rotate(180, 0, 0)

        trim_c_d = cylinder(r=self.intermediate_height_[Orient.DISTAL]/2 + self.knuckle_side_clearance*2, h=4, center=True)#.debug()
        trim_c_p = cylinder(r=self.intermediate_height_[Orient.PROXIMAL]/2 + self.knuckle_side_clearance*2, h=4, center=True).scaleX(1.3)
        mod_side_trim_d = trim_c_d.translate((0, 0, self.intermediate_width_[Orient.DISTAL]/2+1.99)) + trim_c_d.translate((0, 0, -self.intermediate_width_[Orient.DISTAL]/2-1.99))
        mod_side_trim_p = trim_c_p.translate((0, 0, self.intermediate_width_[Orient.PROXIMAL]/2+1.99)) + trim_c_p.translate((0, 0, -self.intermediate_width_[Orient.PROXIMAL]/2-1.99))

        final = ((mod_dist_hinge + bridge_d).translate((0, self.distal_offset_, 0)) + mod_prox_hinge + mod_strut_tl + mod_strut_tr + mod_strut_b \
                 + bridge_p) - (mod_side_trim_d.translate((0, self.distal_offset_, 0))+  mod_side_trim_p) + mod_brace + mod_mid_round #.debug()

        return (final - tendon).color(PART_COLORS["middle"]) #- mid_cut#.debug()#+ fc.debug()#.rotate((0, 0, 90))

    def _create_cover_bumper(self, rwid, l, avgk, avg, t):
        ''' Create the cover-style bumper geometry for the middle section '''

        # if cover:
        #     rwid = 1.8
        #     avgk -= .5
        mod_mid_round = rcubecyl(h=rwid, l=l, w=avgk/2, t=t,
                            rnd=self.strut_rounding*2, center=True) \
                            - rcubecyl(h=10, l=l-4, w=avg/2+1.5, t=t*.6,
                            rnd=self.strut_rounding*2, center=True).translate((.25,0,0))
        return mod_mid_round

    def part_linkage(self):
        ''' The wrist linakge strut for securing the finger tendon '''
        link_hole = self.linkage_length*.8
        mod_core = rcylinder(r=self.linkage_width/2, h=self.linkage_length, rnd=self.linkage_hook_rounding, center=True).resize((self.linkage_width + self.linkage_flat, self.linkage_height, 0)) * cube((self.linkage_width, self.linkage_height, self.linkage_length), center=True)
        mod_core = mod_core.rotate((90, 90, 0))
        mod_hook = self.link_hook().translate(
            ((self.linkage_hook_height - self.linkage_height)/2 +self.linkage_hook_offset,
            -self.linkage_length/2 -self.linkage_hook_length/2 + self.linkage_hook_thickness*2.25 + self.linkage_hook_inset, 0))
        mod_hook_left = mod_hook - cube((20, 20, 20), center=True).translate((0, -self.linkage_length/2 -10 + 1))
        mod_core_right = mod_core - cube((20, 200, 20), center=True).translate((0, 100 -self.linkage_length/2.5))#.debug()
        mod_core_hull = hull()(mod_core_right + mod_hook_left)#.mod("%")

        mod_hole = cylinder(r=self.tendon_hole_radius, h=link_hole).rotate((90, 90, 0)).translate((0, (self.linkage_length/3)*1.5+.01, 0)).resize((self.linkage_height/2.4, 0, 0))#.mod("%")

        cross_hole_dist = self.linkage_hole_spacing
        mod_cut = cube((0))
        mod_cross = cylinder(r=self.tendon_hole_radius, h=self.linkage_width+1, center=True).resize((self.linkage_height/2.8, 0, 0))

        for i in range (0, self.linkage_holes):
            if i == self.linkage_holes-2:
                mod_cut += hull()(mod_cross.translate((0, self.linkage_length/3 + cross_hole_dist -cross_hole_dist*i, 0))+\
                    mod_cross.translate((0, self.linkage_length/3 + cross_hole_dist -cross_hole_dist*i -.8, 0)))
            elif i == self.linkage_holes-1:
                mod_cut += mod_cross.translate((0, self.linkage_length/3 + cross_hole_dist -cross_hole_dist*i - .4, 0))
            else:
                mod_cut += mod_cross.translate((0, self.linkage_length/3 + cross_hole_dist -cross_hole_dist*i, 0))
        #slit
        mod_slit = cylinder(r=self.linkage_height/2.8/2, h=cross_hole_dist * (self.linkage_holes-1)).rotate((90, 90, 0))#.debug()
        mod_cut += mod_slit.translate((0, self.linkage_length/3 + cross_hole_dist, -self.linkage_width/1.85)) + \
             mod_slit.translate((0, self.linkage_length/3 + cross_hole_dist, self.linkage_width/1.85))#.debug()

        final = mod_core + mod_hook + mod_core_hull - mod_hole - mod_cut#.mod("%")
        return final.color(PART_COLORS["linkage"])#.rotate((0, 0, 90))

    def part_socket(self):
        ''' create the interface socket '''
        #TODO 3 Socket texture
        #mod_cut_fist = self._mod_cut_fist() #TODO - hardcoding bullshit
        mod_cut_tendon = cube((20,20,20), center=True).translate(0,0,0).rotate(0,0,-80).translate(19.2,-6.8,0)#.debug()
        length = (self.proximal_length + self.intermediate_height_[Orient.PROXIMAL]/2)
        mod_core = cylinder(r1=self.socket_interface_radius_[Orient.DISTAL] + self.socket_thickness_[Orient.DISTAL], \
            r2=self.socket_interface_radius_[Orient.PROXIMAL] + self.socket_thickness_[Orient.MIDDLE],
            h=self.socket_interface_length).rotate((90, 0, 0)).translate((0, -length - self.distal_flange_height -.01, 0))#.debug()

        #mirror of base #TODO sep config for socket cuts
        mod_socket_interface_cut, _ = self.socket_interface(Orient.OUTER, ridges=False, half=True)
        mod_bottom, c = self._socket_bottom()
        bottom_cut =self._socket_bottom_bit(shrink = True)
        bottom_cut = translate((0, -length - self.distal_flange_height -.01 - self.socket_interface_length, 0))(rotate((90, 0, 0))(bottom_cut))
        mod_bottom = translate((0, -length - self.distal_flange_height -.01 - self.socket_interface_length, 0))(rotate((90, 0, 0))(mod_bottom))
        c= translate((0, -length - self.distal_flange_height -.01 - self.socket_interface_length, 0))(rotate((90, 0, 0))(c))
        mod_bottom_cut = cylinder(r=self.socket_bottom_cut*1.2 , h = 40).translate(-self.socket_bottom_cut,-self.socket_depth-self.socket_bottom_cut*1.2,-20) #.debug()
        scallops = self._socket_scallop()
        final = color(PART_COLORS["socket"])(
            (mod_core - mod_socket_interface_cut +mod_bottom  - bottom_cut  + c - mod_cut_tendon).rotate((0,20,0)) - mod_bottom_cut  - scallops)

            #TODO - hack hack hack
        front_ct = (cube((1,1.5,self.knuckle_width_[Orient.PROXIMAL]),center=True).rotate((0,0,10)) \
             .translate((-self.intermediate_proximal_height/2 - 1.7,-self.intermediate_proximal_height/2 + .65,0))+
        sphere(r=.5).translate((-self.socket_interface_radius_distal*1.5,-self.socket_interface_radius_distal+0.9,0)) ).hull()#.debug()

        mod_basecore = self._mod_core(length)
        mod_bulge = self._tendon_bulge(mod_basecore)
        return final.rotate((0,-20,0)) - mod_bulge #- front_ct

    def part_tipcover(self):
        ''' the finger tip flexible portion '''
        sr = self.tip_radius*self.tip_print_factor
        mod_core = hull()(cylinder(r1=self.tip_radius, r2=self.tip_radius, h=self.distal_base_length).rotate((90, 90, 0)).translate((0, self.distal_base_length*2, 0)), # #self.intermediate_length
            sphere(r=self.tip_radius).resize((self.tip_radius*2-2,0,0)).translate((-.5,self.distal_length-self.tip_radius,0)))

        #Nail cuts #TODO - fix hardcoded
        mod_sphere = sphere(r=sr) \
            .translate((-sr + self.tip_radius*.8, sr/2 -self.distal_base_length*2+2.8,0))#.debug() #self.intermediate_length + self.distal_length-sr, 0))
        c = cube((self.tip_radius*3, 25, self.tip_radius*3), center=True) \
            .rotate((0,0,40)) .translate((5 +4.0, 25-0,0))#.debug()
        d = intersection()((mod_core - mod_sphere), c).translate((.1,0,0)).scale((1,1,1.1))#.debug()

        #INNER CUT
        #TODO - more top clearance from interface
        #TODO - cut through FPs
        mod_int = self.tip_interface(chamfer_in=True) + \
            hull()(cylinder(r=self.tip_interface_post_radius_, h=.1).translate((0-.25,0,-self.tip_interface_post_height - self.tip_interface_ridge_height - self.distal_base_length )).rotate((90,0,0)),
                   cylinder(r=self.tip_interface_post_radius_-1, h=.1).translate((0,0,-self.tip_interface_post_height - self.tip_interface_ridge_height - self.distal_base_length - 1)).rotate((90,0,0)),
            sphere(r=self.tip_radius-1).resize((self.tip_radius-4,0,0)).translate((-.5,self.distal_length-self.tip_radius +0.1,0)))#.debug()

        #Fingerprints
        bot_sp = sphere(r=sr).translate((+sr -  self.tip_radius*.96,
                                         sr/2 -self.distal_base_length*2+self.tip_print_offset*1.2,0))#.debug()
        bot_sp2 = sphere(r=sr+self.tip_print_depth) \
             .translate((+sr - self.tip_radius*1.0250, sr/2 -self.distal_base_length*2+2 + self.tip_print_depth,0))#.debug()
        for i in range(1, round(self.distal_length/self.tip_print_width)):
            if i % 2 == 0: continue
            bot_sp2 -= cube((20,self.tip_print_width,20), center=True).translate((0,(i+1)*self.tip_print_width -.1,0))#.debug()
        prints = intersection()(mod_core - d- mod_int, bot_sp2) \
            - cube((30,30,30), center=True).translate((15 - self.tip_radius/2+.5,15,0)).translate((0,0,0))#.debug()

        #TODO better fist bottom cut
        final = intersection()(mod_core - d- mod_int, bot_sp) + (prints)
        return final.translate((0,self.intermediate_length ,0)).color(PART_COLORS["tipcover"])#.rotate((0, 0, 90))

    def part_plug(self, clearance=True, extra=False):
        ''' plug covers for the knuckle pins'''
        return color(PART_COLORS["plug"])(self.knuckle_plug(clearance=clearance, extra=extra))

    def part_plugs(self, clearance=True, extra=False):
        ''' plug covers for the knuckle pins'''
        plug = self.part_plug(clearance=clearance, extra=extra)
        p_offset = -self.knuckle_proximal_width/2 + self.knuckle_plug_thickness/2 - 0.01
        d_offset = -self.knuckle_distal_width/2 + self.knuckle_plug_thickness/2
        mod_plug_pl = plug.translate(0, 0, p_offset)
        mod_plug_pr = mod_plug_pl.rotate(0, 180, 0)
        mod_plug_dl = plug.translate(0, 0, d_offset - 0.1).translate(0, self.distal_offset_, 0)
        mod_plug_dr = mod_plug_dl.rotate(0, 180, 0)
        return (mod_plug_pl, mod_plug_pr, mod_plug_dl, mod_plug_dr)

    def part_peg(self, fs=10, hollow=True):
        # local default for hollow peg radius
        peg_hollow_radius = 0.5
        peg = cylinder(r1=self.tendon_hole_radius*2.0,r2=self.tendon_hole_radius*1.3, h= self.distal_base_length+2, center=True, _fn=fs)
        if (hollow): peg -= cylinder(r=peg_hollow_radius, h=self.distal_base_length+.5).translate((0,0,-1.5))
        return peg.rotate((90, 0, 0)).translate((0, self.intermediate_distal_height-self.distal_base_length/2.5, 0)).color(PART_COLORS["peg"])

    def part_pins(self):
        # local translate for pins
        pins_translate_y = 10
        mod = self.knuckle_pin(length=self.knuckle_width_[Orient.DISTAL] - self.knuckle_plug_thickness*2 + .01, shrink=.1) + \
            self.knuckle_pin(length=self.knuckle_width_[Orient.PROXIMAL] - self.knuckle_plug_thickness*2 + .01, shrink=.1).translate((0, pins_translate_y, 0))
        return mod.color(PART_COLORS["pins"])

    def part_stand(self):
        ''' create a display stand for the finger socket '''
        depth = self.socket_depth*self.stand_depth_factor
        mod_inner = self._socket_bottom_bit(shrink = True) + sphere(r=self.socket_interface_radius_[Orient.PROXIMAL]).scale((1,1,.35))

        mod_base = hull()(rcylinder(r=self.socket_radius_[Orient.PROXIMAL]*2-2, h=3, rnd=1).translate((0,0,depth)),
            rcylinder(r=self.socket_radius_[Orient.PROXIMAL]*2, h=3, rnd=1).translate((0,0,depth)).translate((0,0,3)),
            cylinder(r=self.socket_radius_[Orient.PROXIMAL]*2, h=1).translate((0,0,depth)).translate((0,0,5)))

        mod_text = circular_text("DangerFinger v5.1     2014-2026", self.socket_radius_[Orient.PROXIMAL] + 3.5, 3.4, 1.0, 11, [0,180,180], reverse=True).rotate((0,0,0)).translate((0,0,depth+.5))
        cut = cylinder(r1=self.socket_radius_[Orient.DISTAL]-1.5, r2=self.socket_radius_[Orient.PROXIMAL]-1.5, h=self.socket_depth +8) + \
            cylinder(r=self.socket_radius_[Orient.PROXIMAL]*2, h=self.socket_depth).translate((0,0,depth + 5.99))#.debug()
        mod = rotate((90,0,0))((mod_inner + mod_base + mod_text) - cut)

        return mod.color(PART_COLORS["stand"])

    def part_bumper(self):
        l=self.intermediate_distal_height+self.tunnel_height*2
        t=self.intermediate_distal_height*.5
        avgk=(self.knuckle_width_[Orient.DISTAL] +self.knuckle_width_[Orient.PROXIMAL])/2 - .5
        cover = self._create_cover_bumper(rwid=3.5, l=l+.5, avgk=avgk+.3, avg=1, t=t)#(self.intermediate_width_[Orient.DISTAL] +self.intermediate_width_[Orient.PROXIMAL])/2).translate(1,self.intermediate_length/2,0)

        cut = self._create_cover_bumper(rwid=1.8, l=l, avgk=avgk-1.0, avg=1, t=t ).hull()#.debug()#.translate(1,self.intermediate_length/2,0).
        cut2 = self._create_cover_bumper(rwid=10, l=l-3, avgk=avgk-3, avg=1, t=t*.6).hull()#.debug()#.translate(1,self.intermediate_length/2,0).
        mod = cover - cut - cut2
        return mod.color(PART_COLORS["bumper"])

    def part_oldbumper(self):
        bridge_p = self.create_bridgesh(r=self.tunnel_radius, length=self.intermediate_tunnel_length,width=self.intermediate_proximal_width_-.023,
                                        rnd=self.tunnel_inner_rounding/2,
                                        height=self.intermediate_height_[Orient.PROXIMAL] / 2 + self.tunnel_height - self.tunnel_radius,
                                         ).hull().translate((0,self.tunnel_radius,0))

        bridge_d = self.create_bridgesh(r=self.tunnel_radius, length=self.intermediate_tunnel_length,width=self.intermediate_distal_width_,
                                        rnd=self.tunnel_inner_rounding/2,
                                        height=self.intermediate_height_[Orient.DISTAL] / 2 + self.tunnel_height - self.tunnel_radius,
                                       ).rotate(180, 0, 0).translate(0, self.distal_offset_ - self.tunnel_radius, 0).hull()#.debug()

        _, anchor_dtl, anchor_dtr, anchor_db = self.knuckle_inner(orient=Orient.DISTAL, cutout=self.knuckle_cutouts, holes=True)
        _, anchor_ptl, anchor_ptr, anchor_pb = self.knuckle_inner(orient=Orient.PROXIMAL, cutout=self.knuckle_cutouts, holes=True)
        #mod_dist_hinge = mod_dist_hinge.rotate((180, 0, 0))
        ## 3 struts and a cross brace
        mod_strut_tl = (anchor_dtl.translate(0, self.distal_offset_, 0)+ anchor_ptl).hull()
        mod_strut_tr = (anchor_dtr.translate(0, self.distal_offset_, 0)+ anchor_ptr).hull()
        mod_strut_b =  (anchor_db.rotate((0,0,self.intermediate_strut_rotate)).translate(0, self.distal_offset_ - 3.75, 0)+ anchor_pb).hull() #.mod("%")
        mod_brace = self.cross_strut()
        mod_cut = (mod_brace + mod_strut_tr + mod_strut_tl + mod_strut_b).hull()#.debug()

        cyllen = self.intermediate_length*.5

        c1 = hull()(rcylinder(h=self.tunnel_inner_rounding+1, r=self.tunnel_radius, rnd=self.tunnel_inner_rounding).rotate((90,0,0)).translate((self.intermediate_height_[Orient.PROXIMAL]/2,self.intermediate_length*.8 - cyllen,self.intermediate_width_[Orient.PROXIMAL]/2)),
                rcylinder(h=self.tunnel_inner_rounding+1, r=self.tunnel_radius, rnd=self.tunnel_inner_rounding).rotate((90,0,0)).translate((self.intermediate_height_[Orient.DISTAL]/2,self.intermediate_length*.75 + cyllen/12 ,self.intermediate_width_[Orient.DISTAL]/2)))
        c2 = c1.rotate((0,90,0))
        #top cut for tendons
        cc1 = hull()(rcylinder(h=self.tunnel_inner_rounding+1, r=self.tunnel_radius, rnd=self.tunnel_inner_rounding).rotate((90,0,0)).translate((self.intermediate_height_[Orient.PROXIMAL]/2.45,self.intermediate_length*.8 - cyllen -2,self.intermediate_width_[Orient.PROXIMAL]/4)),
                rcylinder(h=self.tunnel_inner_rounding+1, r=self.tunnel_radius, rnd=self.tunnel_inner_rounding).rotate((90,0,0)).translate((self.intermediate_height_[Orient.DISTAL]/2.45,self.intermediate_length*.75 + cyllen/12 +2,self.intermediate_width_[Orient.DISTAL]/4)))
        cc2 = hull()(rcylinder(h=self.tunnel_inner_rounding+1, r=self.tunnel_radius, rnd=self.tunnel_inner_rounding).rotate((90,0,0)).translate((self.intermediate_height_[Orient.PROXIMAL]/2.45,self.intermediate_length*.8 - cyllen -2,-self.intermediate_width_[Orient.PROXIMAL]/4)),
                rcylinder(h=self.tunnel_inner_rounding+1, r=self.tunnel_radius, rnd=self.tunnel_inner_rounding).rotate((90,0,0)).translate((self.intermediate_height_[Orient.DISTAL]/2.45,self.intermediate_length*.75 + cyllen/12 +2,-self.intermediate_width_[Orient.DISTAL]/4)))

        c3 = hull()(rcylinder(h=self.tunnel_inner_rounding+1, r=self.tunnel_radius, rnd=self.tunnel_inner_rounding).rotate((90,0,0)).translate((-self.intermediate_height_[Orient.PROXIMAL]/2 + self.tunnel_radius*2.25,self.intermediate_length*.8 - cyllen,2)),
                rcylinder(h=self.tunnel_inner_rounding+1, r=self.tunnel_radius, rnd=self.tunnel_inner_rounding).rotate((90,0,0)).translate((-self.intermediate_height_[Orient.DISTAL]/2 + self.tunnel_radius*2.25,self.intermediate_length*.75 + cyllen/12 ,2)))
        c4 = hull()(rcylinder(h=self.tunnel_inner_rounding+1, r=self.tunnel_radius, rnd=self.tunnel_inner_rounding).rotate((90,0,0)).translate((-self.intermediate_height_[Orient.PROXIMAL]/2 + self.tunnel_radius*2.25,self.intermediate_length*.8 - cyllen,-2)),
                rcylinder(h=self.tunnel_inner_rounding+1, r=self.tunnel_radius, rnd=self.tunnel_inner_rounding).rotate((90,0,0)).translate((-self.intermediate_height_[Orient.DISTAL]/2 + self.tunnel_radius*2.25,self.intermediate_length*.75 + cyllen/12 ,-2)))

        mod_side = hull()((c1 + c2).translate((-1,0,0)), c3, c4)#.debug()

        mod_bumper= hull()(bridge_p + bridge_d + mod_side) - mod_cut  - hull()(cc1, cc2) + hull()(c3, c4).scale((.8,1,.9)).translate((-.55,0,0)) -mod_strut_b#- bridge_p.scale(1.1, 1.1,1.01) - bridge_d.scale(1.1, 1.1,1.01)
        return mod_bumper.color(PART_COLORS["bumper"]) #.rotate((0, 0, 90))

    #**************************************** Primitives ***************************************

    def _mod_core(self, length):
        return rcylinder(r=self.socket_interface_radius_[Orient.DISTAL]+self.socket_thickness_distal, h=self.distal_flange_height).rotate((90, 0, 0)).translate((0, -length, 0))

    def _tendon_bulge(self, mod_core):
        h=self.knuckle_tendon_offset+1
        mod_core_ext = hull()(mod_core, mod_core.translate((.7,-self.knuckle_tendon_offset +.4,0)))#.debug()
        bulge = intersection()(rcylinder(h=10, rnd=.5, r=self.intermediate_width_[Orient.PROXIMAL]/4,center=True),#.debug(),
                                   rcube((self.knuckle_proximal_width/2,self.intermediate_width_[Orient.PROXIMAL]/2,10),rnd=.25, center=True)).rotate((90,0,90))\
                                    .translate((self.intermediate_height_[Orient.PROXIMAL]/2+h/2,
                                                h/2 - self.intermediate_height_[Orient.PROXIMAL]/2 - self.knuckle_tendon_offset+1.0, 0))#.debug()
        return intersection()(mod_core_ext,bulge)#.debug()

    # moved single-use props into method local variables
    # keep peg_hollow_radius available on the class for external checks
    peg_hollow_radius = Prop(val=0.5, minv=0, maxv=10, adv=True, doc='''radius to hollow out the peg''')


    def _socket_bottom(self):
        mod_bottom = self._socket_bottom_bit(False)
        bottom_cut = self._socket_bottom_bit(True).translate((0,0,-0))
        c = union()
        dd= 0
        d = (self.socket_radius_[Orient.PROXIMAL] - self.socket_radius_[Orient.DISTAL]) / self.socket_depth
        for i in range(1, self.socket_depth):
            dd += d + i*.0015
            c=c+ circle(r = 1).translate(self.socket_radius_[Orient.DISTAL]+.85+ dd, 0, 0).rotate_extrude(convexity = 10).translate(0,0,i*1.5 + self.socket_interface_depth)# .debug()
        c = intersection()(c.rotate((0, 0, 0)), bottom_cut)#.debug()
        return mod_bottom +c, c#, bottom_cut

    def _socket_bottom_bit(self, shrink=False):
        mod_bottom = cylinder(r1=self.socket_interface_radius_[Orient.PROXIMAL] + (0 if shrink else self.socket_thickness_[Orient.MIDDLE]),
                             r2=self.socket_radius_[Orient.DISTAL]+ (0 if shrink else self.socket_thickness_[Orient.DISTAL]),
                             h=4 + (.2 if shrink else 0)).translate((0,0,(-.1 if shrink else 0))) + \
                    cylinder(r1=self.socket_radius_[Orient.DISTAL]+ (0 if shrink else self.socket_thickness_[Orient.DISTAL]),
                     r2=self.socket_radius_[Orient.PROXIMAL]+ (0 if shrink else self.socket_thickness_[Orient.PROXIMAL]),
                        h=self.socket_depth - self.socket_interface_depth -4+(.2 if shrink else 0)).translate((0, 0, 4-(.1 if shrink else 0)))
        return mod_bottom#.debug()

    def _socket_scallop(self):
        cl = cylinder(r=self.socket_interface_radius_[Orient.DISTAL]+1, h=9).translate((0,0,-4.5)).rotate((0,0,180)) \
                .translate((0,-self.socket_depth-self.socket_interface_radius_[Orient.DISTAL]*2 -1+ self.socket_scallop_depth_left , self.socket_interface_radius_[Orient.DISTAL] ))
        cr = cylinder(r=self.socket_interface_radius_[Orient.DISTAL]+1, h=9).translate((0,0,-4.5)).rotate((0,0,180)) \
                .translate((0,-self.socket_depth-self.socket_interface_radius_[Orient.DISTAL]*2 - 1+self.socket_scallop_depth_right , -self.socket_interface_radius_[Orient.DISTAL]))
        return hull()(cl + cl.scale(1.5,1.35,1)) + hull()(cr + cr.scale(1.5,1.35,1))#.translate((0,0,0)))

    def link_hook(self):
        ''' create the hooke for end of linkage '''
        mod_hook = rcylinder(r=self.linkage_hook_length/2, h=self.linkage_width, rnd=self.linkage_hook_rounding, center=True).resize((self.linkage_hook_height,0,0)) - \
                    cylinder(r=self.linkage_hook_length/2 - self.linkage_hook_thickness*2+self.linkage_hook_end_inset, h=self.linkage_width+1, center=True).resize((self.linkage_hook_height- self.linkage_hook_thickness*2,0,0))

        mod_cut = cube((self.linkage_hook_height, self.linkage_hook_thickness*2+self.linkage_hook_opening*2, self.linkage_width+1), center=True).translate((-2, self.linkage_hook_thickness*1.5, 0)) \
            - sphere(r=self.linkage_width/1.9).resize((self.linkage_height*1.2, 0, self.linkage_width*1.8)).translate((-self.linkage_width/3.14, -self.linkage_width/3.4, 0))#.debug()
        #mod_cut = mod_cut.debug()
        return mod_hook - mod_cut.translate((0, -self.linkage_hook_opening, 0))#.mod("%"))

    def tip_interface(self,chamfer_out=False, chamfer_in=False):
        ''' the snap-on interface section to the soft tip cover'''
        # local tipcover chamfer (previously class-level)
        tipcover_chamfer = 0.6
        ph=self.tip_interface_post_height+self.tip_interface_clearance
        mod_post = cylinder(r=self.tip_interface_post_radius_ - self.tip_interface_clearance, h=ph, center=True)

        r = self.tip_interface_ridge_radius+self.tip_interface_post_radius_ - self.tip_interface_clearance #+ self.tip_interface_ridge_height*(2/3))) \
        mod_ridge = cylinder(r=r, h=self.tip_interface_ridge_height*.67).translate((0, 0, -self.tip_interface_post_height- self.tip_interface_ridge_height*.33 +self.tip_interface_clearance)) \
                +  cylinder(r1=r - (.5 if chamfer_out else 0), r2=r, h=self.tip_interface_ridge_height*.33).translate((0, 0, -self.tip_interface_post_height- self.tip_interface_ridge_height*.66+self.tip_interface_clearance +.01))
        if (chamfer_in):
            cinh = tipcover_chamfer/2
            mod_ridge += cylinder(r2=self.tip_interface_post_radius_ - self.tip_interface_clearance, r1= r, h=cinh).translate((0, 0, -self.tip_interface_post_height+ self.tip_interface_ridge_height/2 -.01)) \
                + cylinder(r1=self.tip_interface_post_radius_ - self.tip_interface_clearance, r2= r, h=cinh).translate((0, 0, -self.tip_interface_post_height- self.tip_interface_ridge_height/2 - cinh/2 -.085)) \
                + cylinder(r1=self.tip_interface_post_radius_ - self.tip_interface_clearance, r2= r, h=tipcover_chamfer).translate((0, 0, ph/2 - tipcover_chamfer))#.debug()
        mod_core = mod_post + mod_ridge

        mod_bottom_trim = cube((self.intermediate_distal_height, 10, self.knuckle_width_[Orient.DISTAL]), center=True).translate(
            (-self.knuckle_plug_radius -self.intermediate_distal_height/2 + self.tip_bottom_trim_x_extra, self.distal_base_length-.25, 0))#.debug()

        return mod_core.rotate((90, 0, 0)).translate((0, self.distal_base_length + self.tip_interface_post_height/2 + self.tip_interface_clearance/2 - .01, 0)) - mod_bottom_trim

    def _mod_extra(self, orient, rnd=0):
        """Return the 'extra' cylinder used in some parts based on orient."""
        radius = self.intermediate_height_[orient]/2
        # local for single-use translation
        mod_extra_hull_translate_x = -5
        if orient == Orient.DISTAL:
            return cylinder(r=radius+self.knuckle_clearance, h=self.knuckle_inner_width_[orient], center=True) + \
                   (cylinder(r=radius-self.knuckle_clearance*3, h=self.knuckle_inner_width_[orient], center=True).translate(0, 0, 0) + \
                    cylinder(r=radius-self.knuckle_clearance*3, h=self.knuckle_inner_width_[orient], center=True).translate(mod_extra_hull_translate_x, 0, 0)).hull()
        return rcylinder(r=radius+self.knuckle_clearance, h=self.knuckle_inner_width_[orient], center=True, rnd=rnd)

    def tendon_hole(self, shift=0):
        ''' return a tendon tube for cutting from the base'''
        h = self.socket_radius_[Orient.DISTAL] + self.socket_thickness_[Orient.DISTAL]
        # local default for tendon hole offset
        tendon_hole_y_offset = 0.65
        a1 = translate((h, -self.intermediate_proximal_height/2 + tendon_hole_y_offset - self.proximal_length + self.tendon_hole_radius/2 - shift, 0))( \
            resize((0, 0, self.tendon_hole_width))(rotate((0, 90, 0))(cylinder(r=self.tendon_hole_radius, h=.1, center=True))))#.debug()
        a2 = translate((-h/4, -self.intermediate_proximal_height/2 + .65+ self.tendon_hole_radius/2 +2, 0))( \
            cylinder(r=self.tendon_hole_radius, h=.1, center=True).resize((0, 0, 1)).rotate((0, 90, 0)))#.debug()
        return (a1+ a2).hull()

    def elastic_hole(self, double=False):
        ''' generate twin holes in base for elastic tendon '''
        r = self.tendon_hole_radius
        w = self.intermediate_width_[Orient.PROXIMAL]/2 - self.knuckle_inset_border -self.tendon_hole_width/2
        l = (self.proximal_length + self.socket_interface_length + self.intermediate_proximal_height/2)
        sr = self.socket_radius_[Orient.DISTAL] + r #- self.socket_interface_radius_offset + r
        anchor = translate((sr/2, 0, 0))(resize((0, 0, self.tendon_hole_width))(rotate((90, 0, 0))(cylinder(r=r, h=0.1, center=True))))
        anchor1 = anchor.translate((0,0,w))
        anchor2 = anchor.translate((0,0,-w))
        a1 = anchor.translate((0, -l, w))
        a2 = anchor.translate((0, -l, -w))
        #TODO - fix these and make configable
        if double:
            anchor3 = translate((-sr/2.6, 2.5, 0))(rotate((90, 0, 0))(cylinder(r=r*.8, h=0.1, center=True)))#.debug()
            a3 = anchor3.translate((0, -l, self.tendon_hole_width * 1.2))
            a4 = anchor3.translate((0, -l, -self.tendon_hole_width * 1.2))
            return (anchor1+ a1).hull() + (anchor2+ a2).hull() + (anchor3+ a3).hull() + (anchor3+ a4).hull()
        return (anchor1+ a1).hull() + (anchor2+ a2).hull()#.debug()

    def bridge(self, length, orient, tunnel_width):
        ''' tendon tunnel for external hinges'''
        #assemble lots of variables, changing by orientation
        # local defaults (previously class-level Props)
        bridge_cut_a_y_offset = self.tunnel_radius + 1.4
        bridge_cut_b_y_offset = -(self.distal_base_length * 2)
        orient_lat = Orient.PROXIMAL if orient & Orient.PROXIMAL else Orient.DISTAL
        #generate our anchor points
        t_top_l_in = self.bridge_anchor(orient, length, top=True, inside=True, rnd=(orient&Orient.INNER))
        t_top_r_in = self.bridge_anchor(orient, length, top=True, inside=True, shift=True, rnd=(orient&Orient.INNER))
        t_top_l_out = self.bridge_anchor(orient, length, top=True, inside=False)
        t_top_r_out = self.bridge_anchor(orient, length, top=True, inside=False, shift=True)
        t_anchor_l_in = self.bridge_anchor(orient, length, top=False, inside=True, rnd=(orient&Orient.OUTER))#.debug()
        t_anchor_r_in = self.bridge_anchor(orient, length, top=False, inside=True, shift=True, rnd=(orient&Orient.OUTER))#.debug()
        t_anchor_l_out = self.bridge_anchor(orient, length, top=False, inside=False, rnd=(orient&Orient.OUTER))
        t_anchor_r_out = self.bridge_anchor(orient, length, top=False, inside=False, shift=True, rnd=(orient&Orient.OUTER))
        #anchors = ()
        if orient != Orient.OUTER | Orient.PROXIMAL:
            anchors = (t_anchor_l_out + t_anchor_r_out + t_top_r_out + t_top_l_out)
        if orient != Orient.OUTER | Orient.DISTAL:
            anchors = (t_anchor_l_in + t_anchor_r_in + t_top_l_in + t_top_r_in)

        #hull them together, and cut the middle
        mod_tunnel = anchors.hull()

        #TODO - 2 make bridge height configurable
        mod_cut_a = rcylinder(h=tunnel_width, rnd=self.tunnel_inner_rounding, center=True, r=self.tunnel_inner_cutheight_[orient_lat] - (1.75 if orient == (Orient.DISTAL | Orient.OUTER) else 0)) \
            .translate((0, bridge_cut_a_y_offset + (length if orient == (Orient.DISTAL | Orient.INNER) else 0), 0))#TODO 2 - unhardcode this later
        mod_cut_b = rcylinder(r=self.tunnel_inner_cutheight_[orient_lat], h=tunnel_width, rnd=self.tunnel_inner_rounding, center=True) \
            .translate((0, bridge_cut_b_y_offset + (length if orient == (Orient.DISTAL | Orient.INNER) else 0), 0))#.mod("%")

        if orient != (Orient.OUTER):
            mod_tunnel = mod_tunnel - (mod_cut_a + mod_cut_b).hull()
        return mod_tunnel, (mod_cut_a , mod_cut_b)

    def bridge_anchor(self, orient, length, top=False, inside=False, shift=False, rnd=False):
        ''' calculate tunnel widths for a variety of orientations. a mess of logic, but it's gotta go somewhere '''
        orient_lat = Orient.PROXIMAL if orient & Orient.PROXIMAL else Orient.DISTAL
        orient_part = Orient.INNER if orient & Orient.INNER else Orient.OUTER
        r = self.tunnel_radius

        height_top = self.intermediate_height_[orient_lat] / 2 + self.tunnel_height
        height_bottom = self.intermediate_height_[orient_lat] / 2 -.5 #adjust to not stick out from struts
        height = (height_top -r) if top else height_bottom

        top_inner_slant = self.strut_rounding + self.tunnel_inner_slant
        width_top_in = (self.intermediate_width_[orient_lat] / 2) - (top_inner_slant if (orient_part == Orient.INNER) else 0)
        width_top_out = (self.intermediate_width_[orient_lat] / 2) - (-.01 if (orient_part == Orient.INNER) else -self.tunnel_outer_flare) \
            + (.01 if (orient_lat == Orient.DISTAL and inside) else 0)

        width_bottom_in = self.intermediate_width_[orient_lat] / 2
        width_bottom_out = self.knuckle_width_[orient_lat] / 2  + (.01 if (orient_lat == Orient.DISTAL and inside) else 0)-self.knuckle_rounding*.25

        if orient & Orient.OUTER:            #TODO 2 - unhardcode this based on tip width, when defined
            width = width_bottom_out - ((self.tunnel_outer_slant) if inside or (not inside and orient_lat == Orient.DISTAL) else 0) if not top else \
                (width_top_out -1 if orient_lat == Orient.DISTAL and inside else width_top_out)
        elif orient & Orient.INNER and inside: #inside middle
            width = (width_top_in if top else width_bottom_in - self.strut_rounding/2) #inner bottom slant inward
        else: #outside middle
            width = (width_top_out if top else width_bottom_in)
        width -= r
        if shift: width = -width

        #TODO - WTF?
        lenn = 0 if inside else -length
        dim = (height, lenn, width)
        anchor = (cylinder(r=r, h=.01)).rotate((90, 0, 0))
        if rnd:#use sphere instead of cylender
            anchor = (sphere(r=r/2)).translate((r/4 * -.5 if not top else r/4, -r/2 if inside else r/2, r/2*(-1 if shift else 1)))
        return (anchor).translate(dim)

    def knuckle_outer(self, orient, rnd=0, extend_cut=(0, 0)):
        ''' create the outer hinges for base or tip segments '''
        radius = self.intermediate_height_[orient]/2
        width = self.knuckle_width_[orient]
        mod_pin = self.knuckle_pin(length=width + .01)#.mod("%")
        mod_washers = self.knuckle_washers(orient) - mod_pin
        mod_cutcube = cube((radius, radius/2, self.knuckle_inner_width_[orient]),center=True).translate((radius, (radius/4) * (-1 if orient & Orient.DISTAL else 1), 0))#.debug()
        mod_cut = rcylinder(r=radius+self.knuckle_clearance, rnd=rnd, h=self.knuckle_inner_width_[orient], center=True)#.debug()
        if extend_cut != (0, 0):
            mod_cut = mod_cut+ (rcylinder(r=radius-self.knuckle_clearance, rnd=rnd, h=self.knuckle_inner_width_[orient], center=True) + mod_cut.translate(extend_cut + (0,))).hull()
        mod_cut += mod_cutcube

        mod_main = rcylinder(r=radius, h=width, rnd=self.knuckle_rounding, center=True)
        return ((mod_main + mod_washers) - mod_pin) - mod_cut, mod_cut, mod_washers, mod_pin

    def knuckle_washers(self, orient):
        ''' the little built-in washers to reduce hinge friction '''
        r = self.knuckle_washer_radius + self.knuckle_pin_radius
        return cylinder(r=r, h=self.knuckle_width_[orient] - self.knuckle_plug_thickness*2, center=True) \
            - cylinder(r=r+.01, h=self.knuckle_inner_width_[orient] - self.knuckle_washer_thickness, center=True) \
            -cylinder(r=(r-self.knuckle_washer_width), h=self.knuckle_width_[orient] - self.knuckle_plug_thickness*3, center=True)

    knuckle_inner_rounding = 1.35

    def knuckle_inner(self, orient, cutout=False, holes=False):
        ''' create the hinges at either end of a intermediate/middle segment '''
        width = self.intermediate_width_[orient]
        radius = self.intermediate_height_[orient]/2
        st_height = self.knuckle_inset_border*self.strut_height_ratio
        st_offset = self.knuckle_inset_border/2

#TODO - config, and diff distal/prox angles                   #rounding on proximal for strength
        mod_hinge = cylinder(h=width, r=radius, center=True) if orient == Orient.DISTAL else \
            (rcylinder(h=width, r=radius, rnd=self.knuckle_inner_rounding, center=True) + \
            (cylinder(h=width, r=radius, center=True) \
             - cube((radius*5,radius*2,width+1),center=True).rotate((0,0,-45)).translate((0,-self.knuckle_pin_radius-radius,0)))).hull()

        mod_flare= flaredcyl(h=width/2, r=radius- self.knuckle_inset_depth-.01, fr=self.knuckle_inset_depth, fh=.1)
        mod_flare = mod_flare.rotate((0,180,0)).translate((0,0,width/2-self.knuckle_inset_border+.1)) +\
                        mod_flare.translate((0,0,-width/2+self.knuckle_inset_border-.1))#.debug()
        mod_inset = self.knuckle_inset(radius, width)
        mod_cutin = cylinder(h=width-3, r=radius-2.15, center=True)
        mod_pin = self.knuckle_pin(length=width + .01)

        #create anchor points for the struts
        anchor_tl = self.strut(height=st_height).rotate(90, 0, 0).translate(radius -st_offset * self.strut_height_ratio, 0, width/2 - st_offset - self.strut_inset_[orient])
        anchor_tr = self.strut(height=st_height).rotate(90, 0, 0).translate(radius -st_offset * self.strut_height_ratio, 0, -width/2 + st_offset + self.strut_inset_[orient])
        #bottom anchor
        anchor_b = self.strut(height=st_height, width=self.bottom_strut_width_[orient]).rotate(90, 0, 0) \
            .translate(-radius +st_offset * self.strut_height_ratio + self.knuckle_inset_depth + \
                       (.12 if orient==Orient.PROXIMAL else -.485), 1.0, 0)#.debug() #+width*.05
                        #TODO ^set these as params

        return ((mod_hinge - mod_inset + mod_flare - mod_pin - mod_cutin),#.debug(),
                 anchor_tl, anchor_tr, anchor_b)

    def knuckle_inset(self, radius, width):
        ''' create negative space for cutting the hinge inset to make room for tendons '''
        return cylinder(h=width - self.knuckle_inset_border * 2, r=radius + .01, center=True) \
            - cylinder(h=width - self.knuckle_inset_border * 2 + .01, r=radius - self.knuckle_inset_depth, center=True)

    def knuckle_pin(self, length=10, shrink=0):
        ''' create a pin for the hinge hole '''
        return cylinder(h=length, r=self.knuckle_pin_radius - shrink, center=True)

    def strut(self, width=0, height=0, length=.01):
        ''' create a strut that connects the two middle hinges  '''
        if width == 0: width = self.knuckle_inset_border
        if height == 0: height = self.knuckle_inset_border
        return rcube((height, width, length), rnd=self.strut_rounding, center=True)

    def socket_interface(self, orient, ridges=False, half=False):
        ''' build an interface for the socket.  orient determines whether is for base or socket(cutout) with clearance'''
        socket_interface_base = .5
        length = (self.proximal_length + self.intermediate_height_[Orient.PROXIMAL]/2)
        c = self.socket_interface_clearance if orient == Orient.INNER else 0
        r = self.socket_interface_radius_[Orient.PROXIMAL]-c - self.socket_interface_thickness
        h = self.socket_interface_length-socket_interface_base - self.socket_interface_thickness
        dr = self.socket_interface_radius_[Orient.DISTAL]-c
        tol = self.knuckle_width_[Orient.PROXIMAL] - dr*2

        #TODO - make this oblong configurable
        mod_core = (cylinder(r=dr, h=.5).resizeY(dr*2+tol*.35) + \
            cylinder(r=self.socket_interface_radius_[Orient.PROXIMAL]-c,
                     h=socket_interface_base).translate(0, 0, self.socket_interface_length-socket_interface_base- .01)).hull()            #small base section
        mod_cut = sphere(r).resize((0, 0, h*2)) + cylinder(r=r, h=h).translate((0, 0, 0.01))
        mod_cut = mod_cut.translate((0, 0, h + self.socket_interface_depth))
        core_temp = mod_core - mod_cut.translate(0, 0, .01) if orient == Orient.INNER else mod_core
        final = core_temp.rotate(90, 0, 0).translate(0, -length - self.distal_flange_height + .01, 0)
        mod_cut = mod_cut.rotate(90, 0, 0).translate(0, -length - self.distal_flange_height + .01, 0)

        if ridges and self.socket_interface_ridges > 0:
            o = self.socket_interface_ridge_outer / (2 if half else 1)
            i = self.socket_interface_ridge_inner / (2 if half else 1)
            cub = union()([cube((self.socket_interface_ridge_width,30,30), center=True).rotate((0, 360/(self.socket_interface_ridges-1)*i, 0)) for i in range(1, self.socket_interface_ridges)])
            final += intersection()(final.scale((1+o,1,1+o)), cub)#.debug())
            final += intersection()(final.scale((1+i,1,1+i)), cub)

        return final, mod_cut

    def knuckle_plug(self, clearance, extra=False):
        ''' plug cover for the knuckle pins'''
        clearance_val = self.knuckle_plug_clearance if clearance else 0
        r = self.knuckle_plug_radius - clearance_val
        h = self.knuckle_plug_thickness*.25 - clearance_val
        h2 = self.knuckle_plug_thickness*.75
        mod_plug = cylinder(r1=r, r2=r+self.knuckle_plug_ridge, h=h2, center=True).translate(0, 0, -h/2) + \
                    cylinder(r=r+self.knuckle_plug_ridge + (.25 if extra else 0), h=h, center=True).translate(0, 0, h2/2-0.01)
        return mod_plug.rotate(0, 0, 90) #TODO - reverse rotate for left

    def create_bridge(self, r, length, width, height, tunnel_width, tunnel_height, rnd=0, ledge=None, sharp=False):
        ''' create a tendon tunnel for middle section; set `sharp=True` for a smaller/sharp variant (used by create_bridgesh)'''
        #TODO - hardcoding, make rounding config
        if ledge is None:
            ledge = max(0.5, self.tunnel_radius * .9)
        if sharp:
            # reduced anchors for a sharper/simpler bridge (similar to previous create_bridgesh)
            anchors = [
                sphere(r=r/2).translate(r/5 ,length-r/2, width/2-r/2-self.strut_rounding*1.8),
                sphere(r=r/2).translate(r/5 ,length-r/2, -(width/2-r/2-self.strut_rounding*1.)),
                cube((.1, .1,width),center=True).translate(-r,length-r/2-.5,0),
                cube((.1, .1,width-.1),center=True).translate(-r,length,0)
            ]
            mod_tunnel = reduce(add, anchors).hull().translate(height,0,0)
            return mod_tunnel

        anchors =   [cylinder(r=r, h=.01).translate(0,width/2-r,0).rotate((90, 0, 0)),
                    cylinder(r=r, h=.01).rotate((90, 0, 0)).translate(0,0,-width/2+r),
                 #   rcylinder(r=r, h=ledge, rnd=.5).rotate((90, 0, 0)).translate(-.1,ledge,width/2-r*1.25),
                 #   rcylinder(r=r, h=ledge, rnd=.5).rotate((90, 0, 0)).translate(-.1,ledge,-width/2+r*1.25).debug(),
                    sphere(r=r/2).translate(r/5 ,length-r/2, width/2-r/2-self.strut_rounding*1.8),
                    sphere(r=r/2).translate(r/5 ,length-r/2, -(width/2-r/2-self.strut_rounding*1.)),
                 #   cube((.1, length-1,width),center=True).translate(-r,length-1/2-2,0),#.debug(),
                    cube((.1, 1,width-.1),center=True).translate(-r,length-1/2,0)]

        #TODO -hack of height r/8
        mod_cut = (rcylinder(r=tunnel_height, h=tunnel_width, rnd=rnd, center=True).translate(.0,length*1.5,0) +\
                rcylinder(r=tunnel_height, h=tunnel_width, rnd=rnd, center=True).translate(.25,-length*.5,0)).hull()
        mod_tunnel = reduce(add, anchors).hull().translate(height,0,0)

        return mod_tunnel - mod_cut, mod_cut

    def create_bridgesh(self, r, length, width, height, rnd=0, ledge = 1.5):
        ''' legacy thin/sharp bridge wrapper - delegates to create_bridge with sharp=True '''
        return self.create_bridge(r, length, width, height, 0, 0, rnd=rnd, ledge=ledge, sharp=True)

    def cross_strut(self):
        ''' center cross strut'''
        brace_length = min(self.intermediate_distal_width_, self.intermediate_proximal_width_) - self.knuckle_inset_border
        x_shift = self.intermediate_distal_height/2 -self.knuckle_inset_border/2
        h = self.knuckle_inset_border*self.knuckle_brace_height_factor+.4
        return rcube((h, h*2,brace_length), rnd=self.strut_rounding).translate((x_shift-.2, self.distal_offset_/2+h/4, 0))
