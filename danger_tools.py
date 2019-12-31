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
from enum import IntFlag
import argparse
from solid import *
from solid.utils import *

VERSION = 4.1

# ********************************* Custom SCAD Primitives *****************************

class Orient(IntFlag):
    ''' Enum for passing an orientation '''
    PROXIMAL = 1
    DISTAL = 2
    INNER = 4
    OUTER = 8
    UNIVERSAL = 16

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
        value = value if not minv else min(value, minv)
        value = value if not maxv else max(value, maxv)
        return value

    def __get__(self, obj, objtype):
        if self._getter:
            return self._getter(self)
        return self._value

    def __set__(self, obj, value):
        if self._setter:
            self._value = self._getter(self, value)
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
        for arg in args[1]:
            if arg.startswith("-"): arg_list.append(arg.replace("-", ""))

        parser.add_argument("-h", "--help", help="Display this help message and exit.", action="store_true")
        parser.add_argument("-s", "--save_config", help="save config to json file")
        parser.add_argument("-o", "--open_config", help="open config or checkpoint from json file")
        parser.add_argument("-v", "--verbose", help="verbose mode", action="store_true")

        # loop through config class and add a parameter option for each attribute, using _ prepended ones for simu-docstrings
        for param in vars(config_obj).items(): ###
            if param[0].startswith("_"): continue
            val = getattr(config_obj, param[0])
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
            Params.open_config(params, arg_list)
        if params["save_config"]:
            Params.save_config(params)
            sys.exit("Exiting.  Remove 'save' param in order to run tool normally")

        #set the params back to the object
        for param in params:
            setattr(config_obj, param[0], param[1])

def iterable(obj):
    ''' test if object is iterable '''
    try:
        iter(obj)
        return True
    except TypeError:
        return False
