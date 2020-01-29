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
import tornado.web
#from enum import IntFlag, Flag
import solid
from danger_finger import *
from danger_tools import *


def main():
    '''main'''

    http_port = 8081 #TODO config config.get("service_port", 8081)  # pylint: disable=invalid-name
    tornado.web.Application([
        (r"/param([a-zA-Z0-9.]+)", FingerHandler), #, {"params":config}),
        (r"/render/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/scad/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/preview", FingerHandler),
        #fallback serves static files, include ones to supply preview page
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": "./web/"})
        ]).listen(http_port)

    print("Listening on localhost %s" % (http_port))
    tornado.ioloop.IOLoop.instance().start()

# pylint: disable=W0223
class FingerHandler(tornado.web.RequestHandler):
    '''Handle a metadata request'''
    def get(self, part_name):
        '''Handle a metadata request'''
        #TODO - mostly everything for these APIs
        print(" %s %s %s" % (self.request, self.request.path, part_name))
        finger = DangerFinger()

        if self.request.path.startswith("/param"):
            return self.get_params(finger)

        if self.request.path.startswith("/scad"):
            return self.get_scad(finger, part_name)

        if self.request.path.startswith("/render"):
            return self.get_stl(finger, part_name)

        self.write_error(500)

    def build_finger(self, p, finger):
        if p=="preview":
            finger.action = Action.PREVIEW | Action.RENDER | Action.EMITSCAD
            finger.part = FingerPart.HARD
        else:
            finger.action = Action.RENDER | Action.EMITSCAD
            finger.part = FingerPart.from_str(p)

        finger.render_quality = RenderQuality.ULTRAFAST #ULTRAFAST FAST SUBMEDIUM MEDIUM EXTRAMEDIUM HIGH ULTRAHIGH
        finger.render_threads = 8
        finger.preview_quality = RenderQuality.ULTRAFAST #ULTRAFAST FAST SUBMEDIUM MEDIUM EXTRAMEDIUM HIGH ULTRAHIGH
        finger.preview_explode = True
        build_models(finger)
        emit_scad(finger)

    def get_scad(self, finger, part_name):
        p = part_name.split('.')[0]
        self.build_finger(p, finger)

        for key in finger.mod.keys():
            if not p + "_" in key: continue
            self.serve_file(key, 'text/scad')

    def serve_file(self, filename, mimetype):
        with open(filename, 'rb') as file_h:
            print("serving %s" % filename)
            #the whole pie
            file_h.seek(0, os.SEEK_END)
            self.set_header('Content-Length', file_h.tell())
            self.set_header('Content-Type', mimetype)
            self.set_header('Content-Disposition', 'filename="%s"' % filename)
            file_h.seek(0, 0)
            data = file_h.read()
            #now send response body
            self.write(data)
            self.flush()
            self.finish()
            print("200 OK response to: %s, %sb" %(self.request.uri, len(data)))
            return

    def get_stl(self, finger, part_name):
        p = part_name.split('.')[0]
        self.build_finger(p, finger)

        for key in finger.mod.keys():
            if not p + "_" in key: continue
            stl = key + ".stl"
            start = time.time()
            Renderer().scad_to_stl(key, stl)
            print(" Rendered %s in %s sec" % (stl, round(time.time()-start, 1)))
            self.serve_file(stl, 'model/stl')

    def get_params(self, finger):
        params = {}

        for param in dir(DangerFinger):#vars( #type(finger)).items(): ###
            print (param)
            if param.startswith("_"): continue
            val = getattr(finger, param)
            if str(val).startswith(("{", "__", "<f", "<b")): continue
            params[param] = val
            print(param, val)

        pbytes = json.dumps(params, skipkeys=True, cls=EnumEncoder).encode('utf-8')
        self.set_header('Content-Length', len(pbytes))
        self.write(pbytes)
        self.finish()
        print("200 OK JSON response to: %s, %sb" %(self.request.uri, len(pbytes)))
        return

    # def write_error(self, status_code, **kwargs): #pylint: disable=arguments-differ
    #     super().write_error(status_code, **kwargs)

class EnumEncoder(json.JSONEncoder):
    def default(self, obj): #pylint: disable=method-hidden
        ''' test enum encoder'''
        #if type(obj) in PUBLIC_ENUMS.values():
        return {"__enum__": str(obj)}
        #return json.JSONEncoder.default(self, obj)

# def as_enum(d):
#     if "__enum__" in d:
#         name, member = d["__enum__"].split(".")
#         return getattr(PUBLIC_ENUMS[name], member)
#     else:
#         return d

if __name__ == "__main__":
    sys.stdout = UnbufferedStdOut(sys.stdout)
    main()
