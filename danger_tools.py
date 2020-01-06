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
import json
import inspect
from enum import IntFlag, Flag
import argparse
#from solid import *
import solid
#import solid.utils# import *

VERSION = 4.2

# ********************************* Custom SCAD Primitives *****************************

class Orient(IntFlag):
    ''' Enum for passing an orientation '''
    PROXIMAL = 1
    DISTAL = 2
    INNER = 4
    OUTER = 8
    UNIVERSAL = 16

class RenderQuality(Flag):
    ''' Enum for passing an orientation '''
    AUTO = 0
    ULTRAHIGH = 5
    HIGH = 10
    EXTRAMEDIUM = 13
    MEDIUM = 15
    SUBMEDIUM = 17
    FAST = 20
    ULTRAFAST = 25

class FingerPart(IntFlag):
    ''' Enum for passing an orientation '''
    ALL = 0
    SOCKET = 2
    BASE = 4
    MIDDLE = 8
    TIP = 16
    TIPCOVER = 32
    LINKAGE = 64
    PLUGS = 128
    BUMPER = 256
    SOFT = BUMPER | PLUGS | SOCKET | TIPCOVER
    HARD = BASE | TIP | MIDDLE | LINKAGE

def rcylinder(r, h, rnd=0, center=False, rotate=(), translate=(), resize=()):
    ''' primitive for a cylinder with rounded edges'''
    if rnd == 0: return cylinder(r=r, h=h, rotate=rotate, translate=translate, center=center)
    mod_cyl = solid.translate((0, 0, -h/2 if center else 0))( \
        solid.rotate_extrude(convexity=1)(solid.offset(r=rnd)(solid.offset(delta=-rnd)(solid.square((r, h)) + solid.square((rnd, h))))))
    if resize != (): mod_cyl = solid.resize(resize)(mod_cyl)
    return mod_cyl

def rcube(size, rnd=0, center=True, rotate=(), translate=(), resize=()):
    ''' primitive for a cube with rounded edges on 4 sides '''
    if rnd == 0: return solid.cube(size, center=center)
    round_ratio = (1-rnd) * 1.1 + 0.5
    c = cube(size, center=center, rotate=rotate, translate=translate) * cylinder(h=size[2], r=size[1]*round_ratio*2, center=center, rotate=rotate, translate=translate, resize=(size[0]*round_ratio, 0, 0))
    if resize != (): c = solid.resize(resize)(c)
    return c

def cylinder(r=0, h=0, r1=0, r2=0, center=False, rotate=(), translate=(), resize=()):
    ''' cylender with built-in translate and rotate '''
    cyl = solid.cylinder(r1=r1, r2=r2, h=h, center=center) if r1 > 0 and r2 > 0 else solid.cylinder(r=r, h=h, center=center)
    if rotate != (): cyl = solid.rotate(rotate)(cyl)
    if translate != (): cyl = solid.translate(translate)(cyl)

    if resize != (): cyl = solid.resize(resize)(cyl)
    return cyl

def cube(size, center=False, rotate=(), translate=(), resize=()):
    ''' cylender with built-in translate and rotate '''
    c = solid.cube(size=size, center=center)
    if rotate != (): c = solid.rotate(rotate)(c)
    if translate != (): c = solid.translate(translate)(c)
    if resize != (): c = solid.resize(resize)(c)
    return c

def _rotate(self, rotate):
    ''' built-in rotate '''
    return solid.rotate(rotate)(self)

def _resize(self, resize):
    ''' built-in resize '''
    return solid.resize(resize)(self)

def _translate(self, translate):
    ''' built-in translate '''
    return solid.translate(translate)(self)
solid.OpenSCADObject.translate = _translate
solid.OpenSCADObject.rotate = _rotate
solid.OpenSCADObject.resize = _resize


#********************************* Parameterization system **********************************
class Prop(object):
    ''' a simple property replacement that enforces min and max values'''
    def __init__(self, val=None, minv=None, maxv=None, doc=None, getter=None, setter=None, adv=False):
        self._value = val
        self._min = minv
        self._max = maxv
        self.__doc__ = doc
        self._getter = getter
        self._setter = setter
        self._adv = adv

    @staticmethod
    def minmax(value, minv=None, maxv=None):
        '''return the value constrained by a min and max, skipped if None/not provided'''
        try:
            #print(value, minv, maxv)
            value = value if not minv else max(value, minv)
            value = value if not maxv else min(value, maxv)
            #print(value)
        except Exception as _e:
            pass
        return value

    def __get__(self, obj, objtype):
        if self._getter is not None:
            return self._getter(self)
        return self._value

    def __set__(self, obj, value):
        if self._setter is not None:
            self._value = self._setter(self, value)
        self._value = self.minmax(value, self._min, self._max)

class Params():
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
    def parse(config_obj):
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
        #print("args %s" % str(args))
        for arg in args[1]:
            print("arg %s" % arg)
            if arg.startswith("-"): arg_list.append(arg.replace("-", ""))

        parser.add_argument("-h", "--help", help="Display this help message and exit.", action="store_true")
        parser.add_argument("-s", "--save_config", help="save config to json file")
        parser.add_argument("-o", "--open_config", help="open config or checkpoint from json file")
        parser.add_argument("-v", "--verbose", help="verbose mode", action="store_true")

        # loop through config class and add a parameter option for each attribute, using _ prepended ones for simu-docstrings
        for param in vars(type(config_obj)).items(): ###
            #print (param)
            if param[0].startswith("_"): continue
            val = getattr(config_obj, param[0])
            if str(val).startswith(("<f", "<b")): continue
            doc = inspect.getdoc(param[1])
            if doc is None: doc = "" #getattr(config, "_" + param[0], None) if hasattr(config, "_" + param[0]) else inspect.getdoc(param[1])
            parser.add_argument("--%s" % param[0], default=val, help=doc)
            #print("added param %s, %s, \"%s\"" % (param[0], val, doc))

        params = vars(parser.parse_args())
        #print("params: %s" % params)
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
            Params.open_config(params, arg_list)
        if params["save_config"]:
            Params.save_config(params)
            sys.exit("Exiting.  Remove 'save' param in order to run tool normally")

        #set the params back to the object
        #print(arg_list)
        for param in params:
            #print("%s %s " % (param, params[param]))
            if param in arg_list:
                print("Setting %s %s " % (param, params[param]))
                setattr(config_obj, param, params[param])

def iterable(obj):
    ''' test if object is iterable '''
    try:
        if isinstance(obj, str): return False
        iter(obj)
        return True
    except TypeError:
        return False

def diff(val1, val2):
    ''' get difference between numbers '''
    return max(val1, val2)- min(val1, val2)
