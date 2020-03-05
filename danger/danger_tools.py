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
import time
import asyncio
import inspect
import subprocess
import platform
from enum import IntFlag, Flag
import argparse
import solid
from solid import *
from solid.utils import *
from solid.solidpython import OpenSCADObject

VERSION = 4.2

# ********************************* Custom SCAD Primitives *****************************

#additional custom OpenScad primitive types
def rcylinder(r, h, rnd=0, center=False):
    ''' primitive for a cylinder with rounded edges'''
    if rnd == 0: return solid.cylinder(r=r, h=h, center=center)
    mod_cyl = solid.translate((0, 0, -h/2 if center else 0))( \
        solid.rotate_extrude(convexity=1)(solid.offset(r=rnd)(solid.offset(delta=-rnd)(solid.square((r, h)) + solid.square((rnd, h))))))
    return mod_cyl

def rcube(size, rnd=0, center=True):
    ''' primitive for a cube with rounded edges on 4 sides '''
    if rnd == 0: return solid.cube(size, center=center)
    round_ratio = (1-rnd) * 1.1 + 0.5
    #TODO fix rounded cube for detent use-case
    c = solid.cube(size, center=center) * solid.resize((size[0]*round_ratio, 0, 0))(solid.cylinder(h=size[2], d=size[1]*round_ratio, center=center))
    return c

#SolidTools hacks to make functions easily done inline
solid.OpenSCADObject.mod = (lambda self, t: self.set_modifier(t))
solid.OpenSCADObject.translate = (lambda self, t: solid.translate(t)(self))
solid.OpenSCADObject.rotate = (lambda self, t: solid.rotate(t)(self))
solid.OpenSCADObject.resize = (lambda self, t: solid.resize(t)(self))

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

def set_list_attr(l, name, val):
    ''' set an attribute on an object or list of objects'''
    if not iterable(l):
        setattr(l, name, val)
    else:
        for i in l: setattr(i, name, val)

def flatten(l):
    '''flatten a list by adding all items'''
    if not iterable(l): return l
    flat = l[0]
    for i in l[1:]:
        flat += i
    return flat

#********************************* Parameterization system **********************************
class Prop(object):
    ''' a simple property replacement that enforces min and max values'''
    def __init__(self, val=None, minv=None, maxv=None, doc=None, getter=None, setter=None, adv=False, hidden=False):
        self._value = val
        self._hidden = hidden
        self._min = minv
        self._max = maxv
        self.__doc__ = doc
        self._getter = getter
        self._setter = setter
        self._adv = adv
        self._default = val
        self.name = None

    advanced = property(lambda self: self._adv)
    value = property(lambda self: self._value)
    minimum = property(lambda self: self._min)
    maximum = property(lambda self: self._max)
    docs = property(lambda self: self.__doc__)
    default = property(lambda self: self._default)
    hidden = property(lambda self: self._hidden)

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
            self._value = self._setter(self, obj, value)
        setattr(obj, "__" + self.name, self.minmax(value, self._min, self._max))

    def __get__(self, obj, objtype=None):
        if obj is None: return self
        if self._getter is not None:
            return self._getter(self, obj, objtype)
        val = getattr(obj, "__" + self.name, None)
        return val if val is not None else self._value

class Borg:
    '''This is a very elegant singleton'''
    _shared_state = {}
    def __init__(self):
        self.__dict__ = self._shared_state

class Renderer(Borg):
    '''This class will render an OpenSCAD object to STL
    This class needs to know the path to the openscad command-line tool.
    You can set the path with the OPENSCAD_EXEC environment variable, or with the 'openscad_exec'
    keyword in the constructor.  If these are omitted, the class makes an attempt at finding the executable itself.
    '''
    def __init__(self, **kw):
        Borg.__init__(self)
        self.openscad_exec = None
        self.openscad_tmp_dir = None
        if 'OPENSCAD_EXEC' in os.environ: self.openscad_exec = os.environ['OPENSCAD_EXEC']
        if 'OPENSCAD_TMP_DIR' in os.environ: self.openscad_tmp_dir = os.environ['OPENSCAD_TMP_DIR']
        if 'openscad_exec' in kw: self.openscad_exec = kw['openscad_exec']
        if self.openscad_exec is None:
            self._try_detect_openscad_exec()
        if self.openscad_exec is None:
            raise Exception('openscad exec not found!')

    def _try_executable(self, executable_path):
        if os.path.isfile(executable_path):
            self.openscad_exec = executable_path

    def _try_detect_openscad_exec(self):
        self.openscad_exec = None
        platfm = platform.system()
        if platfm == 'Linux':
            self._try_executable('/usr/bin/openscad')
            if self.openscad_exec is None:
                self._try_executable('/usr/local/bin/openscad')
            if self.openscad_exec is None:
                self._try_executable('openscad')
            if self.openscad_exec is None:
                self._try_executable('/usr/bin/openscad-nightly')
            if self.openscad_exec is None:
                self._try_executable('/usr/local/bin/openscad-nightly')
            if self.openscad_exec is None:
                self._try_executable('openscad-nightly')
        elif platfm == 'Darwin':
            self._try_executable('/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD')
        elif platfm == 'Windows':
            self._try_executable(os.path.join(os.environ.get('Programfiles(x86)', 'C:'), 'OpenSCAD\\openscad.exe'))
            self._try_executable(os.path.join(os.environ.get('Programfiles', 'C:'), 'OpenSCAD\\openscad.exe'))

    def scad_to_stl(self, scad_filename, stl_filename, trialrun=False):#, **kw):
        '''render a scad file to stl'''
        try:
            # now run openscad to generate stl:
            cmd = [self.openscad_exec, '-o', stl_filename, scad_filename]
            if trialrun: return cmd
            out = subprocess.check_output(cmd)
            if out != b'': return out
            #if return_code < 0:
            #    raise Exception('openscad command line returned code {}'.format(return_code))
        except Exception as e:
            raise e

    def scad_to_png(self, scad_filename, png_filename):#, **kw):
        '''render a scad file to png'''
        try:
            # now run openscad to generate stl:
            cmd = [self.openscad_exec, '--preview', '-o', png_filename, scad_filename]
            out = subprocess.check_output(cmd)
            if out != b'': print(out)
            #if return_code < 0:
            #    raise Exception('openscad command line returned code {}'.format(return_code))
        except Exception as e:
            raise e

    def scad_parallel_to_stl(self, scad_filenames, max_concurrent_tasks=4):
        ''' run up to max concurrent tasks to render a list of scad files in parallel '''
        start = time.time()

        commands = [[self.openscad_exec, '-o', scad_filename.replace(".scad", ".stl"), scad_filename] for scad_filename in scad_filenames]
        tasks = [AsyncSubprocess().run_command(*command) for command in commands]
        results = AsyncSubprocess().run_asyncio_commands(tasks, max_concurrent_tasks=max_concurrent_tasks)

        end = time.time()
        rounded_end = "{0:.4f}".format(round(end - start, 4))
        print("Rendered STL in %s seconds" % (rounded_end), flush=True)
        return results

    def scad_parallel_to_png(self, scad_filenames, max_concurrent_tasks=4):
        ''' run up to max concurrent tasks to render a list of scad files in parallel '''
        start = time.time()

        commands = [[self.openscad_exec, '--preview', '-o', scad_filename + ".png", scad_filename] for scad_filename in scad_filenames]
        tasks = [AsyncSubprocess().run_command(*command) for command in commands]
        results = AsyncSubprocess().run_asyncio_commands(tasks, max_concurrent_tasks=max_concurrent_tasks)

        end = time.time()
        rounded_end = "{0:.4f}".format(round(end - start, 4))
        print("Rendered PNG in %s seconds" % (rounded_end), flush=True)
        return results


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
            params.pop("open_config", None)
            Params.open_config(params, arg_list)
        if params["save_config"]:
            Params.save_config(params)
            sys.exit("Exiting.  Remove 'save' param in order to run tool normally")

        #set the params back to the object
        #print(arg_list)
        for param in params:
            #print("%s %s " % (param, params[param]))
#            if param in arg_list:
            print("Setting %s %s " % (param, params[param]))
            setattr(config_obj, param, params[param])

class UnbufferedStdOut(object):
    '''Override to allow unbufferred std out to work with | tee'''
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        '''override'''
        self.stream.write(data)
        self.stream.flush()
    def writelines(self, datas):
        '''override'''
        self.stream.writelines(datas)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

class AsyncSubprocess(Borg):
    '''Async and await using subprocesses - we use this to run the single-threaded openscad render processes in parallel'''

    async def run_command(self, *args):
        """Run command in subprocess.   http://asyncio.readthedocs.io/en/latest/subprocess.html"""
        print("Starting task: %s" % str(args), flush=True) #process.pid
        start = time.time()
        # Create subprocess
        process = await asyncio.create_subprocess_exec(args[0], \
            *args[1:], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

        # Wait for the subprocess to finish
        stdout, stderr = await process.communicate()
        elapsed = time.time() - start

        result = stdout.decode().strip()
        error = stderr.decode().strip() if stderr is not None else None
        print("%s %s, pid=%s, %s sec, result: %s %s"% (("Done:" if process.returncode == 0 else "Failed:"), args, process.pid, elapsed, result, error))

        # Return stdout
        return result, error

    async def run_command_shell(self, command):
        """Run command in subprocess (shell).
            This can be used if you wish to execute e.g. "copy"
            on Windows, which can only be executed in the shell. """
        # Create subprocess
        process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        print("Started task:", command, "(pid = " + str(process.pid) + ")", flush=True)
        # Wait for the subprocess to finish
        stdout, stderr = await process.communicate()
        print("Completed task:" if process.returncode == 0 else "Failed:", command, "(pid = " + str(process.pid) + ")", flush=True)

        result = stdout.decode().strip()
        error = stderr.decode().strip() if stderr is not None else None
        return result, error

    @staticmethod
    def make_chunks(l, n):
        """Yield successive n-sized chunks from l.   Taken from https://stackoverflow.com/a/312464"""
        for i in range(0, len(l), n):
            yield l[i : i + n]

    def run_asyncio_commands(self, tasks, max_concurrent_tasks=4):
        """Run tasks asynchronously using asyncio and return results.
        If max_concurrent_tasks are set to 0, no limit is applied.
            https://docs.python.org/3/library/asyncio-eventloops.html#windows"""
        all_results = []
        chunks = [tasks] if max_concurrent_tasks == 0 else self.make_chunks(l=tasks, n=int(max_concurrent_tasks))

        if asyncio.get_event_loop().is_closed():
            asyncio.set_event_loop(asyncio.new_event_loop())
        if platform.system() == "Windows":
            asyncio.set_event_loop(asyncio.ProactorEventLoop())
        loop = asyncio.get_event_loop()

        for tasks_in_chunk in chunks:
            commands = asyncio.gather(*tasks_in_chunk)  # Unpack list using *
            results = loop.run_until_complete(commands)
            all_results += results

        loop.close()
        return all_results
