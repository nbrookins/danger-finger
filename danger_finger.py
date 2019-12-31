#!/bin/python
# pylint: disable=C0302, line-too-long, unused-wildcard-import, wildcard-import, invalid-name, broad-except
'''
The danger_finger copyright 2014-2019 Nicholas Brookins and Danger Creations, LLC
http://dangercreations.com/prosthetics :: http://www.thingiverse.com/thing:1340624
Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 https://creativecommons.org/licenses/by-nc-sa/4.0/
Source code licensed under Apache 2.0:  https://www.apache.org/licenses/LICENSE-2.0
'''
import os
import sys
from solid import *
from solid.utils import *
from danger_tools import *

VERSION = 4.1

# *********************************** Entry Point ****************************************
def assemble():
    ''' The entry point which loads a finger with proper parameters and outputs SCAD files as configured '''
    #create a finger object
    finger = DangerFinger()

    #sample param overrides for testing - comment out
    finger.preview = True
    finger.segments = 72
    finger.part = ["middle"]
   # finger.explode = True

    #load a configuration, with parameters from cli or env
    Params.parse(finger)

    #build some pieces
    mod_preview = None
    for p in finger.part:
        mod_segment = getattr(finger, "part_" + p)()
        if finger.explode:
            if isinstance(mod_segment, (dict, tuple, list)):
                new_mod = []
                for s in mod_segment:
                    new_mod.append(translate(finger.explode_offsets[p][len(new_mod)])(s))
                mod_segment = new_mod
            else:
                mod_segment = translate(finger.explode_offsets[p])(mod_segment)
        mod_preview = mod_segment if not mod_preview else mod_preview + mod_segment
        #write it to a scad file (still needs to be rendered by openscad)
        if not finger.preview:
            finger.emit(mod_segment, filename="dangerfinger_%s_%s_gen.scad" %(VERSION, p))
    if finger.preview:
        finger.emit(mod_preview, filename="dangerfinger_%s_preview_gen.scad" % VERSION)

# ********************************** The danger finger *************************************
class DangerFinger:
    ''' The actual finger model '''
    manifest = ["middle", "base", "tip", "plugs"]
    explode_offsets = property(lambda self: ({"middle":(0, 15, 0), "base" : (0, 0, 0), "tip":(0, 30, 0), "plugs":((0, 0, -5), (0, 0, 5), (0, 30, -5), (0, 30, 5))}))
    # ************************************* control params *****************************************

    preview = Prop(val=False, doc=''' Enable preview mode, emits all segments ''')
    explode = Prop(val=False, doc=''' Enable explode mode, only for preview ''')
    output_directory = Prop(val=os.getcwd(), doc=''' output_directory for scad code, otherwise current''')

    # **************************************** parameters ****************************************
    intermediate_length = Prop(val=25, minv=8, maxv=30, doc=''' length of the intermediate finger segment ''')
    intermediate_distal_height = Prop(val=11.0, minv=4, maxv=8, doc=''' height of the middle section at the distal end.  roughly the height of the hinge circle ''')
    intermediate_proximal_height = Prop(val=12.0, minv=4, maxv=8, doc=''' height of the middle section at the proximal end.  roughly the height of the hinge circle ''')
    intermediate_height = property(lambda self: ({Orient.DISTAL: self.intermediate_distal_height, Orient.PROXIMAL: self.intermediate_proximal_height}))

    proximal_length = Prop(val=6, minv=8, maxv=30, doc=''' length of the proximal/base finger segment ''')
    distal_length = Prop(val=24, minv=8, maxv=30, doc=''' length of the distal/tip finger segment ''')
    distal_base_length = Prop(val=6, minv=0, maxv=20, doc=''' length of the base of the distal/tip finger segment ''')
    length = property(lambda self: ({Orient.DISTAL: self.distal_length, Orient.PROXIMAL: self.proximal_length}))

    knuckle_proximal_width = Prop(val=16.0, minv=4, maxv=20, doc=''' width of the proximal knuckle hinge''')
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
    tunnel_height = Prop(val=2, minv=0, maxv=5, adv=True, doc=''' height of tendon tunnel ''')
    tunnel_radius = Prop(val=1, minv=0, maxv=4, adv=True, doc=''' radius of tendon tunnel rounding ''')

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
    knuckle_side_clearance = Prop(val=.2, minv=-.25, maxv=1, adv=True, doc=''' clearance of the flat circle side of the hinges ''')

    strut_height_ratio = Prop(val=.8, minv=.1, maxv=3, adv=True, doc=''' ratio of strut height to width (auto-controlled).  fractions make the strut thinner ''')
    strut_rounding = Prop(val=.3, minv=.5, maxv=2, adv=True, doc=''' 0 for no rounding, 1 for fullly round ''')

    socket_interface_length = Prop(val=5, minv=3, maxv=8, adv=True, doc=''' length of the portion that interfaces socket and base ''')

    knuckle_cutouts = Prop(val=False, adv=True, doc=''' True for extra cutouts on internals of intermediate section ''')

    #**************************************** dynamic properties ******************************

    intermediate_proximal_width = property(lambda self: (self.knuckle_proximal_width - self.knuckle_proximal_thickness*2 - self.knuckle_side_clearance*2))
    intermediate_distal_width = property(lambda self: (self.knuckle_distal_width - self.knuckle_distal_thickness*2 - self.knuckle_side_clearance*2))
    intermediate_width = property(lambda self: ({Orient.DISTAL: self.intermediate_distal_width, Orient.PROXIMAL: self.intermediate_proximal_width}))

    distal_offset = property(lambda self: (self.intermediate_length))#+ self.intermediate_distal_height / 2))
    shift_distal = lambda self: translate((0, self.distal_offset, 0))

    #**************************************** finger bits ****************************************

    def part_base(self):
        ''' Generate the base finger section, closest proximal to remant '''
        mod_hinge, mod_hinge_cut = self.knuckle_outer(orient=Orient.PROXIMAL)
        mod_plugs = self.part_plugs(clearance=False)
        tunnel_length = self.intermediate_height[Orient.PROXIMAL]*.4
        mod_tunnel, mod_cut = self.bridge(length=tunnel_length, width_factor=self.knuckle_inset_border, tunnel_width=self.intermediate_width[Orient.PROXIMAL]+ self.knuckle_side_clearance*2, orient=Orient.PROXIMAL | Orient.OUTER)
        mod_core = translate((0, -self.proximal_length, 0))(rotate((90, 0, 0))(rcylinder(r=self.knuckle_proximal_width/2 + 1, h=0.1)))
        #TODO trim hinge sides more better
        #TODO base socket interface
        #TODO base tendon tunnel

        return mod_hinge + hull()(mod_tunnel + mod_core) -mod_cut - mod_hinge_cut - mod_plugs

    def part_tip(self):
        ''' Generate the base finger section, closest proximal to remant '''
        mod_hinge, mod_hinge_cut = self.knuckle_outer(orient=Orient.DISTAL)
        mod_plugs = self.part_plugs(clearance=False)

        tunnel_length = self.intermediate_height[Orient.DISTAL]*.4
        bridge = self.bridge(length=tunnel_length, width_factor=self.knuckle_inset_border, tunnel_width=self.intermediate_width[Orient.DISTAL] + self.knuckle_side_clearance*2, orient=Orient.DISTAL | Orient.OUTER)
        mod_tunnel = translate((0, tunnel_length, 0))(bridge[0])
        mod_cut = translate((0, tunnel_length, 0))(bridge[1])
        mod_core = translate((0, self.distal_base_length, 0))(rotate((90, 0, 0))(rcylinder(r=self.knuckle_distal_width/2 -.5, h=0.1)))
        #TODO Tip interface
        #TODO tip tendon detents

        return self.shift_distal()(mod_hinge + hull()(mod_tunnel+ mod_core) -mod_cut - mod_hinge_cut) - mod_plugs[2]- mod_plugs[3]

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
        bridge_p = self.bridge(length=self.intermediate_height[Orient.PROXIMAL]*self.intermediate_tunnel_length, width_factor=self.knuckle_inset_border, \
            tunnel_width=self.intermediate_width[Orient.PROXIMAL]*.75, orient=Orient.PROXIMAL | Orient.INNER)
        mod_tunnel_p = shift_tun(self, Orient.PROXIMAL)(bridge_p[0])
        #mod_cut_p = shift_tun(self, Orient.PROXIMAL)(bridge_p[1])

        bridge_d = self.bridge(length=self.intermediate_height[Orient.DISTAL]*self.intermediate_tunnel_length, width_factor=self.knuckle_inset_border, \
            tunnel_width=self.intermediate_width[Orient.DISTAL]*.75, orient=Orient.DISTAL | Orient.INNER)
        mod_tunnel_d = rotate((180, 0, 0))(shift_tun(self, Orient.DISTAL)(bridge_d[0]))
        #mod_cut_d = rotate((180, 0, 0))(shift_tun(self, Orient.DISTAL)(bridge_d[1]))

        return self.shift_distal()(mod_dist_hinge + mod_tunnel_d) + mod_prox_hinge + mod_strut_tl + mod_strut_tr + mod_strut_b + mod_brace + mod_tunnel_p

    #TODO Socket
    #TODO Socket scallops
    #TODO Socket texture

    #TODO Tip Cover
    #TODO Tip Cover fingernail (ugh..
    #TODO Tip Cover fingerprints

    #TODO Linkage
    #TODO Linkage Hook

    #TODO Bumper?

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

    def bridge(self, length, orient, tunnel_width, width_factor):
        ''' tendon tunnel for external hinges'''
        #assemble lots of variables, changing by orientation
        orient_lat = Orient.PROXIMAL if orient & Orient.PROXIMAL else Orient.DISTAL
        h_factor = self.intermediate_height[orient_lat] / 2

        height_bottom = h_factor - self.tunnel_height
        height_top = h_factor + self.tunnel_height/2 -.2
        tunnel_height = h_factor + self.tunnel_height*.4 #hokey

        #generate our anchor points
        t_anchor_end = rotate((90, 0, 0))(cylinder(r=self.tunnel_radius, h=.01))

        t_top_l_in = translate((height_top, 0, self.get_tunnel_width(orient, width_factor, top=True, inside=True)))(t_anchor_end)
        t_top_r_in = translate((height_top, 0, -self.get_tunnel_width(orient, width_factor, top=True, inside=True)))(t_anchor_end)
        t_top_l_out = translate((height_top, -length, self.get_tunnel_width(orient, width_factor, top=True, inside=False)))(t_anchor_end)
        t_top_r_out = translate((height_top, -length, -self.get_tunnel_width(orient, width_factor, top=True, inside=False)))(t_anchor_end)

        t_anchor_l_in = translate((height_bottom, 0, self.get_tunnel_width(orient, width_factor, top=False, inside=True)))(t_anchor_end)
        t_anchor_r_in = translate((height_bottom, 0, -self.get_tunnel_width(orient, width_factor, top=False, inside=True)))(t_anchor_end)
        t_anchor_l_out = translate((height_bottom, -length, self.get_tunnel_width(orient, width_factor, top=False, inside=False)))(t_anchor_end)
        t_anchor_r_out = translate((height_bottom, -length, -self.get_tunnel_width(orient, width_factor, top=False, inside=False)))(t_anchor_end)

        #hull them together, and cut the middle
        mod_tunnel = hull()(t_top_l_in, t_top_l_out, t_top_r_in, t_top_r_out, t_anchor_l_in, t_anchor_l_out, t_anchor_r_in, t_anchor_r_out)
        mod_cut = hull()(
            translate((0, 2, 0))(rcylinder(r=tunnel_height-self.tunnel_radius/4, h=tunnel_width, rnd=1.2, center=True)),
            translate((0, -6, 0))(rcylinder(r=tunnel_height-self.tunnel_radius/4, h=tunnel_width, rnd=1.2, center=True)))

        return mod_tunnel - mod_cut, mod_cut

    def get_tunnel_width(self, orient, width_factor, top=False, inside=False):
        ''' calculate tunnel widths for a variety of orientations '''
        orient_lat = Orient.PROXIMAL if orient & Orient.PROXIMAL else Orient.DISTAL
        orient_part = Orient.INNER if orient & Orient.INNER else Orient.OUTER

        width_top_in = (self.intermediate_width[orient_lat] / 2) - (self.tunnel_radius + 0.5 if (orient_part == Orient.INNER) else 0)
        width_top_out = (self.intermediate_width[orient_lat] / 2) - (self.tunnel_radius -.01 if (orient_part == Orient.INNER) else 0) - (self.tunnel_radius -.01 if (orient_lat == Orient.DISTAL and inside) else 0)
        width_bottom_in = self.knuckle_width[orient_lat] / 4 - self.tunnel_radius
        width_bottom_out = self.knuckle_width[orient_lat] / 2 - width_factor/2 - (self.tunnel_radius -.01 if (orient_lat == Orient.DISTAL and inside) else 0)

        if orient & Orient.OUTER: return width_top_out if top else width_bottom_out
        return (width_top_in if top else width_bottom_in) if inside else (width_top_out if top else width_bottom_out if orient & Orient.OUTER else width_bottom_in)

    def knuckle_outer(self, orient, cut_width=-1):#, radius, width):
        ''' create the outer hinges for base or tip segments '''
        radius = self.intermediate_height[orient]/2
        width = self.knuckle_width[orient]
        cut_width = self.intermediate_width[orient] + self.knuckle_side_clearance*2 if cut_width == -1 else cut_width
        mod_pin = self.knuckle_pin(length=width + .01)
        mod_cut = cylinder(r=radius+self.knuckle_clearance, h=cut_width, center=True)
        return rcylinder(r=radius, h=width, rnd=self.knuckle_rounding, center=True) - mod_cut - mod_pin, mod_cut

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

    def cross_strut(self):
        ''' center cross strut'''
        brace_length = min(self.intermediate_distal_width, self.intermediate_proximal_width) - self.knuckle_inset_border
        x_shift = self.intermediate_distal_height/2 -self.knuckle_inset_border/2
        mod_brace = translate((0, self.distal_offset/2, 0))(
            hull()(translate((x_shift, 0, 0))(self.strut(height=self.knuckle_inset_border*.5, length=brace_length)) + \
            translate((x_shift, 0, 0))(self.strut(height=self.knuckle_inset_border*.25, length=brace_length+ self.knuckle_inset_border*.8))))
        return mod_brace

    #************************************* utilities ****************************************

    def emit(self, val, filename=None):
        ''' emit the provided model to SCAD code '''
        if not filename:
            return scad_render(val, file_header=f'$fn = {self.segments};')
        else:
            print("Writing SCAD output to %s/%s" % (self.output_directory, filename))
            return scad_render_to_file(val, out_dir=self.output_directory, file_header=f'$fn = {self.segments};', include_orig_code=True, filepath=filename)

    #*************************************** special properties **********************************

    _part = []
    @property
    def part(self):
        ''' select which part to print'''
        return self.manifest if self.preview else self._part
    @part.setter
    def part(self, val):
        self._part = val

    _segments = 0
    @property
    def segments(self):
        '''number of radii segments, higher is better for detail but slower.  auto sets low (36) for preview and high (108) for print '''
        return self._segments if self._segments != 0 else 36 * 2 if self.preview else 36 * 3
    @segments.setter
    def segments(self, val):
        self._segments = val

if __name__ == '__main__':
    assemble()
