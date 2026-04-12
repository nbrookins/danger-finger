import argparse
from enum import Enum
import inspect
import json
import os
import re
import sys

class Params():
    ''' handy class for parsing/loading/saving dynamic configs'''
    @staticmethod
    def open_config(fname, params, args):
        '''open a config file'''
        with open(fname, "r") as file_h:
            config = dict(json.load(file_h))
            print("** Loaded config from %s " % fname)
            for k in config:
                if config[k] and k not in args:
                    params[k] = config[k]

    @staticmethod
    def apply_config(obj, params):
        '''apply a config file'''
        for k in params:
            try:
                setattr(obj, k, params[k])
            except Exception:
                print("param not found: %s" % k)

    @staticmethod
    def save_config(params, config_obj):
        '''save a config file'''
        try:
            config_file = params["save_config"]
            print("** Saving config file to: %s " % config_file)
            del params["save_config"]
            del params["help"]
            del params["open_config"]
            if (params["force"]):
                print ("force")
                dct = {}
                for prop in dir(config_obj):#vars(config_obj).items(): ###
                    if prop.startswith("_") or prop.endswith("_"): continue
                    val = getattr(config_obj, prop)
                    if str(type(val))=="<class 'method'>": continue
                    if str(type(val)).startswith("<class 'dict"):
                        dct[prop] = val
                        continue
                    print (prop + ", " + str(type(val)))
                    if prop in params: continue
                    params[prop] = val
                params.update(dct)
            with open(config_file, "w+") as file_h:
                j = json.dumps(params, cls=MyEncoder, separators=(',', ':'))
                #repl = {r'([\[\]])\s+': r'\1',  r'([\[\]]){1},\n+': r'\1,',  r'^\s*(\d)\n+' : r'\1',  r':\{\n+' : r':{',  r'^\s*(\d)*,\n+': r'\1, ', r'^\s*([^"]){1}(.*),\n+': r'\1\2, '  } #
                repl = {r',"': r',\n"'}
                for p,r in repl.items(): j = re.sub(p, r, j, flags=re.M)
                file_h.write(j)#data)
        except Exception as err:
            print("* Failed saving config file: %s " % err)

    @staticmethod
    def parse(config_obj, parser=None):
        """parse command line args"""
        #lay down all of our potential options
        if (not parser): parser = argparse.ArgumentParser(prog="", description="", epilog='''''', add_help=False)

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
        parser.add_argument("-f", "--force", help="force all configs to dump", action="store_true")

        # loop through config class and add a parameter option for each attribute
        for param in vars(type(config_obj)).items(): ###
            #print (param)
            if param[0].startswith("_"): continue
            val = getattr(config_obj, param[0])
            if str(val).startswith(("<f", "<b")): continue
            doc = inspect.getdoc(param[1])
            if doc is None: doc = ""
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
            cfg = params.pop("open_config", None)
            Params.open_config(cfg, params, arg_list)
        if params["save_config"]:
            Params.save_config(params, config_obj)
            sys.exit()#"Exiting.  Remove 'save' param in order to run tool normally"

        #set the params back to the object
        #print(arg_list)
        for param in params:
            #print("%s %s " % (param, params[param]))
#            if param in arg_list:
            print("Setting %s %s " % (param, params[param]))
            try:
                setattr(config_obj, param, params[param])
            except Exception as ex:
                print(ex)

#********************************* Parameterization system **********************************
class Prop(object):
    ''' a simple property replacement that enforces min and max values'''
    def __init__(self, val=None, minv=None, maxv=None, doc=None, getter=None, setter=None, adv=False, hidden=False, custom=None, name=None, order=100, section=None):
        self._value = val
        self._hidden = hidden
        self._min = minv
        self._max = maxv
        self.__doc__ = doc
        self._getter = getter
        # In Python <3.10 staticmethod descriptors aren't callable; unwrap to raw function
        if setter is not None and isinstance(setter, staticmethod):
            setter = setter.__func__
        self._setter = setter
        self._adv = adv
        self._default = val
        self.name = name
        self._order = order
        self._section = section

    advanced = property(lambda self: self._adv)
    value = property(lambda self: self._value)
    minimum = property(lambda self: self._min)
    maximum = property(lambda self: self._max)
    docs = property(lambda self: self.__doc__)
    default = property(lambda self: self._default)
    hidden = property(lambda self: self._hidden)
    order = property(lambda self: self._order)
    section = property(lambda self: self._section)

    @staticmethod
    def minmax(value, minv=None, maxv=None):
        '''return the value constrained by a min and max, skipped if None/not provided'''
        try:
            value = value if not minv else max(value, minv)
            value = value if not maxv else min(value, maxv)
        except Exception as _e:
            pass
        return value

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, obj, value):
        if self._setter is not None:
            value = self._setter(self, obj, value)
        setattr(obj, "__" + self.name, self.minmax(value, self._min, self._max))

    def __get__(self, obj, objtype=None):
        if obj is None: return self
        if self._getter is not None:
            return self._getter(self, obj, objtype)
        val = getattr(obj, "__" + self.name, None)
        return val if val is not None else self._value

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.name
        return super().default(obj)
