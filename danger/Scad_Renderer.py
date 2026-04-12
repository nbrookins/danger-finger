#!/bin/python
# pylint: disable=C0302, line-too-long, unused-wildcard-import, wildcard-import, invalid-name, broad-except
'''
The danger_finger copyright 2014-2020 Nicholas Brookins and Danger Creations, LLC
http://dangercreations.com/prosthetics :: http://www.thingiverse.com/thing:1340624
Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 https://creativecommons.org/licenses/by-nc-sa/4.0/
Source code licensed under Apache 2.0:  https://www.apache.org/licenses/LICENSE-2.0
'''
import os
import time
import asyncio
import platform
import subprocess
from danger.tools import *

class Borg:
    '''This is a very elegant singleton'''
    _shared_state = {}
    def __init__(self):
        self.__dict__ = self._shared_state

class AsyncSubprocess(Borg):
    '''Async and await using subprocesses - we use this to run the single-threaded openscad render processes in parallel'''

    async def run_command(self, *args):
        """Run command in subprocess.   http://asyncio.readthedocs.io/en/latest/subprocess.html"""
        print("  Starting task: %s" % str(args), flush=True) #process.pid
        start = time.time()
        # Create subprocess
        process = await asyncio.create_subprocess_exec(args[0], \
            *args[1:], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

        # Wait for the subprocess to finish
        stdout, stderr = await process.communicate()
        elapsed = time.time() - start

        result = stdout.decode().strip()
        error = stderr.decode().strip() if stderr is not None else None
        print("%s %s, pid=%s, %s sec, result: %s %s"% (("  Done:" if process.returncode == 0 else "Failed:"), args, process.pid, elapsed, result, error))

        # Return stdout
        return result, error

    async def run_command_shell(self, command):
        """Run command in subprocess (shell).
            This can be used if you wish to execute e.g. "copy"
            on Windows, which can only be executed in the shell. """
        # Create subprocess
        process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        print("  Started task:", command, "(pid = " + str(process.pid) + ")", flush=True)
        # Wait for the subprocess to finish
        stdout, stderr = await process.communicate()
        print("  Completed task:" if process.returncode == 0 else "Failed:", command, "(pid = " + str(process.pid) + ")", flush=True)

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

        #if asyncio.get_event_loop().is_closed():
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


class Scad_Renderer(Borg):
    '''This class will render an OpenSCAD object to STL
    This class needs to know the path to the openscad command-line tool.
    You can set the path with the OPENSCAD_EXEC environment variable, or with the 'openscad_exec'
    keyword in the constructor.  If these are omitted, the class makes an attempt at finding the executable itself.
    '''
    CAMERA_PRESETS = {
        "iso": "0,0,0,55,0,25,200",
        "front": "0,0,0,0,0,0,200",
        "side": "0,0,0,0,0,90,200",
        "top": "0,0,0,90,0,0,200",
    }

    def __init__(self, **kw):
        Borg.__init__(self)
        self.openscad_exec = None
        self.openscad_tmp_dir = None
        self._try_detect_openscad_exec(kw)
        if self.openscad_exec is None:
            raise Exception('openscad exec not found!')

    def scad_parallel(self, scad_filenames, png_size=None, max_concurrent_tasks=2, camera=None):
        ''' run up to max concurrent tasks to render a list of scad files in parallel '''
        start = time.time()

#'--enable', 'fast-csg', '--enable', 'manifold', '--enable', 'lazy-union', '--enable', 'vertex-object-renderers', '--enable', 'vertex-object-renderers-indexing', \
#'--enable', 'fast-csg', '--enable', 'manifold', '--enable', 'lazy-union', '--enable', 'vertex-object-renderers', '--enable', 'vertex-object-renderers-indexing',
        def _png_cmd(scad_filename):
            cmd = [self.openscad_exec, '-q', '--imgsize', png_size or '1024,768', '--preview', '-o', 
                   scad_filename.replace(".scad", ".png"), scad_filename]
            if camera:
                cmd = cmd[:2] + ['--camera', camera] + cmd[2:]
            return cmd

        commandsp = [] if not png_size or png_size == "" else [_png_cmd(sf) for sf in scad_filenames]
#TODO - param for quiet mode
        commands = [[self.openscad_exec,
                       '--enable', 'manifold', '--export-format', 'binstl', '-o', scad_filename.replace(".scad", ".stl"), scad_filename] for scad_filename in scad_filenames]
        commands += (commandsp)
        tasks = [AsyncSubprocess().run_command(*command) for command in commands]
        results = AsyncSubprocess().run_asyncio_commands(tasks, max_concurrent_tasks=max_concurrent_tasks)

        end = time.time()
        rounded_end = "{0:.4f}".format(round(end - start, 4))
        print("** Rendered in %s seconds" % (rounded_end), flush=True)
        return results

    def scad_to_stl(self, scad_filename, stl_filename, trialrun=False):#, **kw):
        '''render a scad file to stl'''
        try:
            cmd = [self.openscad_exec, '-o', stl_filename, scad_filename]
            if trialrun: return cmd
            out = subprocess.check_output(cmd)
            if out != b'': return out
        except Exception as e:
            raise e

    def scad_to_png(self, scad_filename, png_filename, camera=None, imgsize=None):
        '''render a scad file to png'''
        try:
            cmd = [self.openscad_exec, '--preview', '-o', png_filename, scad_filename]
            if camera:
                cmd = cmd[:1] + ['--camera', camera] + cmd[1:]
            if imgsize:
                cmd = cmd[:1] + ['--imgsize', imgsize] + cmd[1:]
            out = subprocess.check_output(cmd)
            if out != b'': print(out)
        except Exception as e:
            raise e

    def render_multi_view(self, scad_filename, output_dir, imgsize="1024,768"):
        '''Render a SCAD file to multiple PNG views using camera presets.
        Returns list of generated PNG paths.'''
        os.makedirs(output_dir, exist_ok=True)
        basename = os.path.splitext(os.path.basename(scad_filename))[0]
        generated = []
        for view_name, camera_str in self.CAMERA_PRESETS.items():
            png_path = os.path.join(output_dir, "%s_%s.png" % (basename, view_name))
            self.scad_to_png(scad_filename, png_path, camera=camera_str, imgsize=imgsize)
            generated.append(png_path)
        return generated

    def _try_executable(self, executable_path):
        if os.path.isfile(executable_path):
            self.openscad_exec = executable_path

    def _try_detect_openscad_exec(self, kw):
        self.openscad_exec = None
        if 'OPENSCAD_EXEC' in os.environ:
            self.openscad_exec = os.environ['OPENSCAD_EXEC']  # path or name (subprocess resolves via PATH)
        if 'OPENSCAD_TMP_DIR' in os.environ: self.openscad_tmp_dir = os.environ['OPENSCAD_TMP_DIR']
        if 'openscad_exec' in kw: self.openscad_exec = kw['openscad_exec']
        platfm = platform.system()
        if platfm == 'Linux':
            if self.openscad_exec is None:
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
            if self.openscad_exec is None:
                self._try_executable('/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD')
        elif platfm == 'Windows':
            if self.openscad_exec is None:
                self._try_executable(os.path.join(os.environ.get('Programfiles(x86)', 'C:'), 'OpenSCAD\\openscad.exe'))
            if self.openscad_exec is None:
                self._try_executable(os.path.join(os.environ.get('Programfiles', 'C:'), 'OpenSCAD\\openscad.exe'))