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
    ''' 3 '''
    #create a finger object
    finger = danger_finger()
    #load a configuration, with parameters from cli or env
    ParamParser.parse(finger)

    finger.preview = False
    finger.part = ["middle"]

    #build some pieces
    for p in finger.part:
        seg = getattr(finger, p)()#finger.middle()
        #write it to a scad file (still needs to be rendered by openscad)
        file_out = finger.emit(seg, filename=p)
        print("OpenSCAD file written to: %s" % file_out)


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
    ALL_PARTS = ["middle"]
    # **************************************** parameters ****************************************
    intermediate_length = ConstrainedProperty(16, 8, 30, ''' length of the intermediate finger segment ''')

    hinge_side_clearance = ConstrainedProperty(.1, -.25, 1, ''' clearance of the flat round side of the hinges ''')

    hinge_proximal_thickness = ConstrainedProperty(2.25, 1, 5, ''' thickness of the hinge tab portion on proximal side  ''')
    hinge_distal_thickness = ConstrainedProperty(2.25, 1, 5, ''' thickness of the hinge tab portion on distal side ''')

    hinge_proximal_width = ConstrainedProperty(10.75, 4, 20, ''' width of the proximal knuckle hinge''')
    hinge_distal_width = ConstrainedProperty(10.25, 4, 20, ''' width of the distal knuckle hinge ''')

    hinge_inset_border = ConstrainedProperty(1.5, 0, 5, ''' width of teh hinge inset, same as top strut width ''')
    hinge_inset_depth = ConstrainedProperty(.8, 0, 3, ''' depth of the inset to clear room for tendons ''')
    hinge_pin_radius = ConstrainedProperty(1.01, 0, 3, ''' radius of the hinge pin/hole ''')

    strut_height_ratio = ConstrainedProperty(.75, .1, 3, ''' ratio of strut height to width (auto-controlled).  fractions make the strut thinner ''')
    strut_round_ratio = ConstrainedProperty(1.2, .5, 2, ''' 2 for no rounding, lower numbers give more. ''')

    intermediate_distal_height = ConstrainedProperty(8, 4, 8, ''' height of the middle section at the distal end.  roughly the height of the hinge circle ''')
    intermediate_proximal_height = ConstrainedProperty(8, 4, 8, ''' height of the middle section at the proximal end.  roughly the height of the hinge circle ''')

    #**************************************** dynamic properties ******************************
    intermediate_proximal_width = property(lambda self: (self.hinge_proximal_width - self.hinge_proximal_thickness*2 - self.hinge_side_clearance*2))
    intermediate_distal_width = property(lambda self: (self.hinge_distal_width - self.hinge_distal_thickness*2 - self.hinge_side_clearance*2))

    #*************************************** special properties **********************************

    output_directory = ConstrainedProperty(os.getcwd(), None, None, ''' output_directory for scad code, otherwise current''')
    preview = ConstrainedProperty(True, None, None, ''' Enable preview mode, emits all segments ''')

    _part = []
    @property
    def part(self):
        ''' select which part to print'''
        return self.ALL_PARTS if self.preview else self._part
    @part.setter
    def part(self, val):
        self._part = val

    _segments = 0
    @property
    def segments(self):
        '''number of radii segments, higher is better for detail but slower.  auto sets low (36) for preview and high (108) for print '''
        return self._segments if self._segments != 0 else 36 if self.preview else 36*3
    @segments.setter
    def segments(self, val):
        self._segments = val

    #**************************************** finger bits ****************************************

    def middle(self):
        ''' Generate the middle/intermediate finger section '''
        distal_offset = self.intermediate_length + self.intermediate_distal_height / 2
        shift_distal = lambda: translate((0, distal_offset, 0))
        mod_dist_hinge, anchor_dtl, anchor_dtr, anchor_db = self.intermediate_hinge(width=self.intermediate_distal_width, radius=self.intermediate_distal_height/2)
        mod_prox_hinge, anchor_ptl, anchor_ptr, anchor_pb = self.intermediate_hinge(width=self.intermediate_proximal_width, radius=self.intermediate_proximal_height/2)

        mod_strut_tl = hull()(shift_distal()(anchor_dtl), anchor_ptl)
        mod_strut_tr = hull()(shift_distal()(anchor_dtr), anchor_ptr)
        mod_strut_b = hull()(shift_distal()(anchor_db), anchor_pb)
        mod_brace = translate((self.intermediate_distal_height/2 -self.hinge_inset_border*self.strut_height_ratio/2, distal_offset/2, 0))(self.strut(height=self.hinge_inset_border*.5, length=min(self.intermediate_distal_width, self.intermediate_proximal_width)))

        return translate((0, self.intermediate_length + self.intermediate_distal_height / 2, 0))(mod_dist_hinge) + mod_prox_hinge + mod_strut_tl + mod_strut_tr + mod_strut_b + mod_brace

    #**************************************** Primitives ***************************************

    def intermediate_hinge(self, radius, width):
        ''' create the hinges at either end of a intermediate/middle segment '''
        st_height = self.hinge_inset_border*self.strut_height_ratio
        st_offset = self.hinge_inset_border/2

        mod_hinge = cylinder(h=width, r=radius, center=True)
        mod_inset = self.hinge_inset(radius, width)
        mod_pin = self.hinge_pin(length=width + .01)

        #create anchor points for the struts
        anchor_tl = translate((radius -st_offset*self.strut_height_ratio, 0, width/2 - st_offset))(rotate((90, 0, 0))(self.strut(height=st_height)))
        anchor_tr = translate((radius -st_offset*self.strut_height_ratio, 0, -width/2 + st_offset))(rotate((90, 0, 0))(self.strut(height=st_height)))
        anchor_b = translate((-radius +st_offset*self.strut_height_ratio + self.hinge_inset_depth, 0, 0))(rotate((90, 0, 0))(self.strut(height=st_height, width=width-(self.hinge_inset_border*2)+width*.05)))

        return (mod_hinge - mod_inset - mod_pin, anchor_tl, anchor_tr, anchor_b)

    def hinge_inset(self, radius, width):
        ''' create negative space for cutting the hinge inset to make room for tendons '''
        return cylinder(h=width - self.hinge_inset_border * 2, r=radius + .01, center=True) \
            - cylinder(h=width - self.hinge_inset_border * 2 + .01, r=radius - self.hinge_inset_depth, center=True)

    def hinge_pin(self, length=10):
        ''' create a pin for the hinge hole '''
        return cylinder(h=length, r=self.hinge_pin_radius, center=True)

    def strut(self, width=0, height=0, length=.01):
        ''' create a strut that connects the two middle hinges  '''
        if width == 0: width = self.hinge_inset_border
        if height == 0: height = self.hinge_inset_border
        return cube((height, width, length), center=True) * resize((height*self.strut_round_ratio, 0, 0))(cylinder(h=length, d=width*1.3, center=True))

    #************************************* utilities ****************************************

    def emit(self, val, filename=None):
        ''' emit the provided model to SCAD code '''
        print("wirintg to %s" % self.output_directory)
        return scad_render_to_file(val, out_dir=self.output_directory, file_header=f'$fn = {self.segments};', include_orig_code=True, filepath=(filename + "_gen.scad" if filename else "test.scad"))


# boilerplate stuff
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
            print("added param %s, %s, \"%s\"" % (param[0], val, doc))

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
