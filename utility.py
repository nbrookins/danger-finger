#!/bin/python
# pylint: disable=C0302, line-too-long, unused-wildcard-import, wildcard-import, invalid-name, broad-except
'''
The danger_finger copyright 2014-2026 Nicholas Brookins and Danger Creations, LLC
http://dangercreations.com/prosthetics :: http://www.thingiverse.com/thing:1340624
Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 https://creativecommons.org/licenses/by-nc-sa/4.0/
Source code licensed under Apache 2.0:  https://www.apache.org/licenses/LICENSE-2.0
'''
import sys
import os
from danger import *
from danger.Scad_Renderer import *

def main():
    '''main'''
    print("running CLI")

    finger = DangerFinger()
    parser = argparse.ArgumentParser(prog="danger_finger.py",
        description='''danger-finger.py v%s (c) 2015-2020 DangerCreations, Inc.
        code: knick@dangercreations.com''' % finger.VERSION, add_help=False)
    parser.add_argument("-r", "--render", help="render STL", action="store_true")
    Params.parse(finger, parser=parser)

    cores = os.cpu_count()
    render_stl = FingerPart.NONE if not finger.render else FingerPart.ALL | FingerPart.EXPLODE#.HARD | FingerPart.SOFT | FingerPart.STAND | FingerPart.PINS#FingerPart.ALL# HARD PREVIEW ALL
    print ("Found cores: ", cores, render_stl)
    finger.render_quality = RenderQuality.HIGH #  INSANE = 2 ULTRAHIGH = 5 HIGH = 10 EXTRAMEDIUM = 13 MEDIUM = 15 SUBMEDIUM = 17 FAST = 20 ULTRAFAST = 25 STUPIDFAST = 30
    #finger.preview_cut = True

    finger.build()#header=True)
    files = []

    for name, model in finger.models.items():
        if model == None: continue
        fp = FingerPart.from_str(name)
        if not iterable(model):
            print ("Processing ", fp)
            #write SCAD files
            filename = "output/dangerfinger_v" + str(finger.VERSION) + "_" + model.part
            model.scad_filename = filename + ".scad"
            write_file(model.scad.encode('utf-8'), model.scad_filename)

            if render_stl == fp or ((fp & render_stl == fp)):# and (fp & FingerPart.PREVIEW == 0)): #TODO - make expanded one for non unioned plugs
                print ("** queing for render ", fp)
                files.append(model.scad_filename)
            else:
                print ("skipping ", fp)

    if files and render_stl:
        Scad_Renderer().scad_parallel(files, max_concurrent_tasks=cores)

    print("-- Complete, exiting --")

if __name__ == "__main__":
    sys.stdout = UnbufferedStdOut(sys.stdout)
    main()
