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
import json
import inspect
import argparse
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
    #finger.explode = True

    #load a configuration, with parameters from cli or env
    Params.parse(finger)

    #build some pieces
    mod_preview = None
    for p in finger.part:
        mod_segment = getattr(finger, "part_" + p)()
        if finger.explode:
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
    explode_offsets = {"middle":(0, 15, 0), "base" : (0, 0, 0), "tip":(0, 30, 0), "plugs":(15, 0, 0)}
    # ************************************* control params *****************************************

    preview = Prop(False, doc=''' Enable preview mode, emits all segments ''')
    explode = Prop(False, doc=''' Enable explode mode, only for preview ''')
    output_directory = Prop(os.getcwd(), doc=''' output_directory for scad code, otherwise current''')

    # **************************************** parameters ****************************************
    intermediate_length = Prop(25, minv=8, maxv=30, doc=''' length of the intermediate finger segment ''')
    intermediate_distal_height = Prop(11.0, minv=4, maxv=8, doc=''' height of the middle section at the distal end.  roughly the height of the hinge circle ''')
    intermediate_proximal_height = Prop(12.0, minv=4, maxv=8, doc=''' height of the middle section at the proximal end.  roughly the height of the hinge circle ''')

    proximal_length = Prop(16, minv=8, maxv=30, doc=''' length of the proximal/tip finger segment ''')
    distal_length = Prop(16, minv=8, maxv=30, doc=''' length of the distal/base finger segment ''')

    knuckle_proximal_width = Prop(16.0, minv=4, maxv=20, doc=''' width of the proximal knuckle hinge''')
    knuckle_distal_width = Prop(14.5, minv=4, maxv=20, doc=''' width of the distal knuckle hinge ''')

    socket_circumference_distal = Prop(55, minv=20, maxv=160, doc='''circumference of the socket closest to the base''')
    socket_circumference_proximal = Prop(62, minv=20, maxv=160, doc='''circumference of the socket closest to the hand''')
    socket_thickness_distal = Prop(2, minv=.5, maxv=4, doc='''thickness of the socket closest to the base''')
    socket_thickness_proximal = Prop(1.6, minv=.5, maxv=4, doc='''thickness of the socket at flare''')
    socket_clearance = Prop(-.25, minv=-2, maxv=2, doc='''Clearance between socket and base.  -.5 for Ninja flex and sloopy printing to +.5 for firm tpu and accurate''')

    knuckle_proximal_thickness = Prop(3.8, minv=1, maxv=5, doc=''' thickness of the hinge tab portion on proximal side  ''')
    knuckle_distal_thickness = Prop(3.4, minv=1, maxv=5, doc=''' thickness of the hinge tab portion on distal side ''')

    linkage_length = Prop(70, minv=10, maxv=120, doc=''' length of the wrist linkage ''')
    linkage_width = Prop(6.8, minv=4, maxv=12, doc=''' width of the wrist linkage ''')
    linkage_height = Prop(4.4, minv=3, maxv=8, doc=''' thickness of the wrist linkage ''')

    # ************************************* rare or non-recommended to muss with *************
    #TODO - find a way to markup advanced properties

    knuckle_inset_border = Prop(2.2, minv=0, maxv=5, doc=''' width of teh hinge inset, same as top strut width ''')
    knuckle_inset_depth = Prop(.65, minv=0, maxv=3, doc=''' depth of the inset to clear room for tendons ''')
    knuckle_pin_radius = Prop(1.07, minv=0, maxv=3, doc=''' radius of the hinge pin/hole ''')
    knuckle_plug_radius = Prop(3.0, minv=2, maxv=5, doc=''' radius of the hinge pin cover plug ''') #TO-DO dynamic contraints?, must be less than hinge radius
    knuckle_plug_thickness = Prop(1.1, minv=0.5, maxv=4, doc=''' thickness of the hinge pin cover plug ''')
    knuckle_plug_ridge = Prop(.3, minv=0, maxv=1.5, doc=''' width of the plug holding ridge ''')
    knuckle_plug_clearance = Prop(.1, minv=-.5, maxv=1, doc=''' clearance of the plug ''')

    knuckle_rounding = Prop(.7, minv=0, maxv=4, doc=''' amount of rounding for the outer hinges ''')
    knuckle_side_clearance = Prop(.1, minv=-.25, maxv=1, doc=''' clearance of the flat round side of the hinges ''')

    strut_height_ratio = Prop(.8, minv=.1, maxv=3, doc=''' ratio of strut height to width (auto-controlled).  fractions make the strut thinner ''')
    strut_rounding = Prop(.3, minv=.5, maxv=2, doc=''' 0 for no rounding, 1 for fullly round ''')

    socket_interface_length = Prop(5, minv=3, maxv=8, doc=''' length of the portion that interfaces socket and base ''')

    knuckle_cutouts = Prop(False, doc=''' True for extra cutouts on internals of intermediate section ''')

    #**************************************** dynamic properties ******************************

    intermediate_proximal_width = property(lambda self: (self.knuckle_proximal_width - self.knuckle_proximal_thickness*2 - self.knuckle_side_clearance*2))
    intermediate_distal_width = property(lambda self: (self.knuckle_distal_width - self.knuckle_distal_thickness*2 - self.knuckle_side_clearance*2))
    distal_offset = property(lambda self: (self.intermediate_length))#+ self.intermediate_distal_height / 2))
    shift_distal = lambda self: translate((0, self.distal_offset, 0))

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

    #**************************************** finger bits ****************************************

    def part_base(self):
        ''' Generate the base finger section, closest proximal to remant '''
        mod_hinge = self.knuckle_outer(radius=self.intermediate_proximal_height/2, width=self.knuckle_proximal_width, cut_width=self.intermediate_proximal_width + self.knuckle_side_clearance*2)
        mod_plugs = self.part_plugs(clearance=False)

        #TODO base tunnel section
        #TODO base socket interface

        return mod_hinge - mod_plugs

    def part_tip(self):
        ''' Generate the base finger section, closest proximal to remant '''
        mod_hinge = self.knuckle_outer(radius=self.intermediate_distal_height/2, width=self.knuckle_distal_width, cut_width=self.intermediate_distal_width + self.knuckle_side_clearance*2)
        mod_plugs = self.part_plugs(clearance=False)

        #TODO tip tunnel section
        #TODO Tip interface
        #TODO tip tendon detents

        return self.shift_distal()(mod_hinge) - mod_plugs

    def part_middle(self):
        ''' Generate the middle/intermediate finger section '''
        #a hinge at each end
        mod_dist_hinge, anchor_dtl, anchor_dtr, anchor_db = self.knuckle_inner(width=self.intermediate_distal_width, radius=self.intermediate_distal_height/2, cutout=self.knuckle_cutouts)
        mod_prox_hinge, anchor_ptl, anchor_ptr, anchor_pb = self.knuckle_inner(width=self.intermediate_proximal_width, radius=self.intermediate_proximal_height/2, cutout=self.knuckle_cutouts)
        # 3 struts and a cross brace
        mod_strut_tl = hull()(self.shift_distal()(anchor_dtl), anchor_ptl)
        mod_strut_tr = hull()(self.shift_distal()(anchor_dtr), anchor_ptr)
        mod_strut_b = hull()(self.shift_distal()(anchor_db), anchor_pb)
        mod_brace = self.cross_strut()

        #TODO middle tunnel sections

        return self.shift_distal()(rotate((180, 0, 0))(mod_dist_hinge)) + mod_prox_hinge + mod_strut_tl + mod_strut_tr + mod_strut_b + mod_brace

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

    def knuckle_outer(self, radius, width, cut_width=0):#, radius, width):
        ''' create the outer hinges for base or tip segments '''
        mod_pin = self.knuckle_pin(length=width + .01)
        return rcylinder(r=radius, h=width, rnd=self.knuckle_rounding, center=True) - cylinder(r=radius+.01, h=cut_width, center=True) - mod_pin

    def knuckle_inner(self, radius, width, cutout=False):
        ''' create the hinges at either end of a intermediate/middle segment '''
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
        mod_plug = translate((0, 0, -self.knuckle_plug_thickness*.25/2))( \
            cylinder(r1=r, r2=r+self.knuckle_plug_ridge, h=self.knuckle_plug_thickness*.75, center=True)) + \
            translate((0, 0, self.knuckle_plug_thickness*.375 - 0.01))(cylinder(r=r+self.knuckle_plug_ridge, h=self.knuckle_plug_thickness*.25 - clearance_val, center=True))
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


if __name__ == '__main__':
    assemble()
