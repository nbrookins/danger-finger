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

VERSION = 4.1

# *********************************** Entry Point ****************************************
def assemble():
    ''' The entry point which loads a finger with proper parameters and outputs SCAD files as configured '''
    #create a finger object
    finger = danger_finger()

    #sample param overrides for testing - comment out
    finger.preview = True
    finger.segments = 72
    #finger.explode = True

    #load a configuration, with parameters from cli or env
    ParamParser.parse(finger)

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

# *********************************** Helper class ****************************************
class ConstrainedProperty(object):
    ''' a simple property replacement that enforces min and max values'''
    def __init__(self, default, minv, maxv, doc, getter=None):
        self._value = default
        self._min = minv
        self._max = maxv
        self.__doc__ = doc
        self._getter = getter

    @staticmethod
    def minmax(value, minv=None, maxv=None):
        '''return the value constrained by a min and max, skipped if None/not provided'''
        value = value if not minv else min(value, minv)
        value = value if not maxv else max(value, maxv)
        return value

    def __get__(self, obj, objtype):
        if self._getter:
            return self._getter(self)
        return self._value

    def __set__(self, obj, value):
        self._value = self.minmax(value, self._min, self._max)

# ********************************** The danger finger *************************************
class danger_finger:
    ''' The actual finger model '''
    manifest = ["middle", "base", "tip", "plugs"]
    explode_offsets = {"middle":(0, 15, 0), "base" : (0, 0, 0), "tip":(0, 30, 0), "plugs":(15, 0, 0)}
    # ************************************* control params *****************************************

    preview = ConstrainedProperty(False, None, None, ''' Enable preview mode, emits all segments ''')
    explode = ConstrainedProperty(False, None, None, ''' Enable explode mode, only for preview ''')
    output_directory = ConstrainedProperty(os.getcwd(), None, None, ''' output_directory for scad code, otherwise current''')

    # **************************************** parameters ****************************************
    intermediate_length = ConstrainedProperty(25, 8, 30, ''' length of the intermediate finger segment ''')
    intermediate_distal_height = ConstrainedProperty(11.0, 4, 8, ''' height of the middle section at the distal end.  roughly the height of the hinge circle ''')
    intermediate_proximal_height = ConstrainedProperty(12.0, 4, 8, ''' height of the middle section at the proximal end.  roughly the height of the hinge circle ''')

    proximal_length = ConstrainedProperty(16, 8, 30, ''' length of the proximal/tip finger segment ''')
    distal_length = ConstrainedProperty(16, 8, 30, ''' length of the distal/base finger segment ''')

    knuckle_proximal_width = ConstrainedProperty(16.0, 4, 20, ''' width of the proximal knuckle hinge''')
    knuckle_distal_width = ConstrainedProperty(14.5, 4, 20, ''' width of the distal knuckle hinge ''')

    socket_circumference_distal = ConstrainedProperty(55, 20, 160, '''circumference of the socket closest to the base''')
    socket_circumference_proximal = ConstrainedProperty(62, 20, 160, '''circumference of the socket closest to the hand''')
    socket_thickness_distal = ConstrainedProperty(2, .5, 4, '''thickness of the socket closest to the base''')
    socket_thickness_proximal = ConstrainedProperty(1.6, .5, 4, '''thickness of the socket at flare''')
    socket_clearance = ConstrainedProperty(-.25, -2, 2, '''Clearance between socket and base.  -.5 for Ninja flex and sloopy printing to +.5 for firm tpu and accurate''')

    knuckle_proximal_thickness = ConstrainedProperty(3.8, 1, 5, ''' thickness of the hinge tab portion on proximal side  ''')
    knuckle_distal_thickness = ConstrainedProperty(3.4, 1, 5, ''' thickness of the hinge tab portion on distal side ''')

    linkage_length = ConstrainedProperty(70, 10, 120, ''' length of the wrist linkage ''')
    linkage_width = ConstrainedProperty(6.8, 4, 12, ''' width of the wrist linkage ''')
    linkage_height = ConstrainedProperty(4.4, 3, 8, ''' thickness of the wrist linkage ''')

    # ************************************* rare or non-recommended to muss with *************
    #TODO - find a way to markup advanced properties

    knuckle_inset_border = ConstrainedProperty(2.2, 0, 5, ''' width of teh hinge inset, same as top strut width ''')
    knuckle_inset_depth = ConstrainedProperty(.65, 0, 3, ''' depth of the inset to clear room for tendons ''')
    knuckle_pin_radius = ConstrainedProperty(1.07, 0, 3, ''' radius of the hinge pin/hole ''')
    knuckle_plug_radius = ConstrainedProperty(3.0, 2, 5, ''' radius of the hinge pin cover plug ''') #TO-DO dynamic contraints?, must be less than hinge radius
    knuckle_plug_thickness = ConstrainedProperty(1.1, 0.5, 4, ''' thickness of the hinge pin cover plug ''')
    knuckle_plug_ridge = ConstrainedProperty(.3, 0, 1.5, ''' width of the plug holding ridge ''')
    knuckle_plug_clearance = ConstrainedProperty(.1, -.5, 1, ''' clearance of the plug ''')

    knuckle_rounding = ConstrainedProperty(.7, 0, 4, ''' amount of rounding for the outer hinges ''')
    knuckle_side_clearance = ConstrainedProperty(.1, -.25, 1, ''' clearance of the flat round side of the hinges ''')

    strut_height_ratio = ConstrainedProperty(.8, .1, 3, ''' ratio of strut height to width (auto-controlled).  fractions make the strut thinner ''')
    strut_rounding = ConstrainedProperty(.3, .5, 2, ''' 0 for no rounding, 1 for fullly round ''')

    socket_interface_length = ConstrainedProperty(5, 3, 8, ''' length of the portion that interfaces socket and base ''')

    knuckle_cutouts = ConstrainedProperty(False, None, None, ''' True for extra cutouts on internals of intermediate section ''')

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

# ********************************* Custom SCAD Primitives *****************************

def rcylinder(r, h, rnd=0, center=False):
    ''' primitive for a cylinder with rounded edges'''
    if rnd == 0: return cylinder(r=r, h=h, center=center)
    mod_cyl = translate((0, 0, -h/2 if center else 0))( \
        rotate_extrude(convexity=1)(offset(r=rnd)(offset(delta=-rnd)(square((r, h)) + square((rnd, h))))))
    return mod_cyl

def rcube(size, rnd=0, center=True):
    ''' primitive for a cube with rounded edges on 4 sides '''
    if rnd == 0: return cube(size, center=center)
    round_ratio = (1-rnd) * 1.1 + 0.5
    return cube(size, center=center) * resize((size[0]*round_ratio, 0, 0))(cylinder(h=size[2], d=size[1]*round_ratio, center=center))

#********************************* Parameterization system **********************************
class ParamParser():
    ''' handy class for parsing/loading/saving dynamic configs'''
    @staticmethod
    def open_config(params, args):
        '''open a config file'''
        with open(params["open_config"], "r") as file_h:
            config = dict(json.load(file_h))
            print("-Loaded config from %s " % params["open_config"])
            for k in config:
                if config[k] and k not in args:
                    params[k] = config[k]

    @staticmethod
    def save_config(params):
        '''save a config file'''
        try:
            config_file = params["save_config"]
            print("-Saving config file to: %s " % config_file)
            del params["save_config"]
            with open(config_file, "w+") as file_h:
                json.dump(params, file_h, indent=2)
        except Exception as err:
            print("Failed saving config file: %s " % err)

    @staticmethod
    def parse(finger):
        """parse command line args"""
        #lay down all of our potential options
        parser = argparse.ArgumentParser(
            prog="danger_finger.py",
            description='''danger-finger.py v%s (c) 2015-2020 DangerCreations, Inself.
                code: knick@dangercreations.com''' % VERSION,
            epilog='''''', add_help=False)

        #do this to distinguish set vs default args
        args = parser.parse_known_args()
        arg_list = []
        for arg in args[1]:
            if arg.startswith("-"): arg_list.append(arg.replace("-", ""))

        parser.add_argument("-h", "--help", help="Display this help message and exit.", action="store_true")
        parser.add_argument("-s", "--save_config", help="save config to json file")
        parser.add_argument("-o", "--open_config", help="open config or checkpoint from json file")
        parser.add_argument("-v", "--verbose", help="verbose mode", action="store_true")

        # loop through config class and add a parameter option for each attribute, using _ prepended ones for simu-docstrings
        for param in vars(danger_finger).items():
            if param[0].startswith("_"): continue
            val = getattr(finger, param[0])
            if str(val).startswith(("<f", "<b")): continue
            doc = inspect.getdoc(param[1]) #getattr(config, "_" + param[0], None) if hasattr(config, "_" + param[0]) else inspect.getdoc(param[1])
            parser.add_argument("--%s" % param[0], default=val, help=doc)
            #print("added param %s, %s, \"%s\"" % (param[0], val, doc))

        params = vars(parser.parse_args())
        for param in params:
            env = os.environ.get(param)
            if env:
                #print("Found matching env var %s, value: %s " % (param, env))
                if env.startswith("'") and env.endswith("'"):
                    env = env[1:-1]
                if isinstance(env, str) and ("false" in env.lower() or "true" in env.lower()):
                    params[param] = (env.lower() == "true")
                else:
                    params[param] = env

        if params["help"]:
            parser.print_help()
            sys.exit()
        if params["open_config"]:
            params.pop("open_config", None)
            ParamParser.open_config(params, arg_list)
        if params["save_config"]:
            ParamParser.save_config(params)
            sys.exit("Exiting.  Remove 'save' param in order to run tool normally")

        #set the params back to the finger
        for param in params:
            setattr(finger, param[0], param[1])

if __name__ == '__main__':
    assemble()
