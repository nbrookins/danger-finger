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
import solid
from danger import *

def main():
    '''main'''

    config = {}
    Params.parse(config)

    print("running CLI")
    finger = DangerFinger()

    render_stl = FingerPart.NONE
   # render_stl = FingerPart.TIP #HARD # HARD PREVIEW ALL
    cores = 6

    Params.parse(finger)
    finger.render_quality = RenderQuality.HIGH #  INSANE = 2 ULTRAHIGH = 5 HIGH = 10 EXTRAMEDIUM = 13 MEDIUM = 15 SUBMEDIUM = 17 FAST = 20 ULTRAFAST = 25 STUPIDFAST = 30
    finger.preview_quality = RenderQuality.MEDIUM #     INSANE = 2 ULTRAHIGH = 5 HIGH = 10 EXTRAMEDIUM = 13 MEDIUM = 15 SUBMEDIUM = 17 FAST = 20 ULTRAFAST = 25 STUPIDFAST = 30
   # finger.preview_explode = True
    #finger.preview_cut = True
    #finger.preview_rotate = 40
    #finger.animate_explode = True
    #finger.animate_rotate = True
    finger.build()

    for _fp, model in finger.models.items():
        #flat = flatten(model)
        if not iterable(model):
            filename = "output/dangerfinger_v4.2_" + model.part #TODO - fix template
            model.scad_filename = filename + ".scad"
            scad = DangerFinger().scad_header(finger.render_quality) + "\n" + model.scad
            write_file(scad.encode('utf-8'), model.scad_filename)

    if render_stl:
        files = []
        for fp, model in finger.models.items():
            if fp & render_stl == fp and not iterable(model): #TODO - make expanded one for non unioned plugs
                files.append(model.scad_filename)
        if files:
            Renderer().scad_parallel_to_stl(files, max_concurrent_tasks=cores)
    print("Complete")

def write_file(data, filename):
    ''' write bytes to file '''
    print("  writing %s bytes to %s" %(len(data), filename))
    with open(filename, 'wb') as file_h:
        file_h.write(data)

if __name__ == "__main__":
    sys.stdout = UnbufferedStdOut(sys.stdout)
    main()
