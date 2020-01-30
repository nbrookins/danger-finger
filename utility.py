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
import solid
from danger import *
#from danger_tools import *

def main():
    '''main'''

    config = {}
    Params.parse(config)

    server = True
    if server:
        start_server()
    else:
        finger = DangerFinger()
        Params.parse(finger)
        #write_scad(model.code, scad_file)
        #write_stl(scad_file, stl_file)

def start_server(http_port=8081):
    ''' start the web server to take api request for finger building '''
    tornado.web.Application([
        (r"/params(/?\w*)", FingerHandler), #, {"params":config}),
        (r"/render/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/scad/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/preview", FingerHandler),
        #fallback serves static files, include ones to supply preview page
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": "./web/", "default_filename": "index.html"})
        ]).listen(http_port)

    print("Listening on localhost %s" % (http_port))
    tornado.ioloop.IOLoop.instance().start()

def write_scad(code, filename):
    with open(filename, 'wb') as file_h:
        file_h.write(code)

def write_stl(scad_file, stl_file):
    #TODO - cache these with hash of config...
    start = time.time()
    Renderer().scad_to_stl(scad_file, stl_file)
    print(" Rendered %s in %s sec" % (stl_file, round(time.time()-start, 1)))

def get_params(self, finger, var):
    params = finger.params(adv=var.startswith("/adv"), allv=var.startswith("/all"), extended=True)
    pbytes = json.dumps(params, skipkeys=True, cls=EnumEncoder).encode('utf-8')
    self.set_header('Content-Length', len(pbytes))
    self.set_header('Content-Type', 'application/json')
    self.write(pbytes)
    self.finish()
    print("200 OK JSON response to: %s, %sb" %(self.request.uri, len(pbytes)))
    return

# pylint: disable=W0223
class FingerHandler(tornado.web.RequestHandler):
    '''Handle a metadata request'''
    def get(self, var):
        '''Handle a metadata request'''
        print("  HTTP Request: %s %s %s" % (self.request, self.request.path, var))
        #TODO - get config here

        if self.request.path.startswith("/param"):
            params = DangerFinger().params(adv=var.startswith("/adv"), allv=var.startswith("/all"), extended=True)
            pbytes = json.dumps(params, skipkeys=True, cls=EnumEncoder).encode('utf-8')
            self.serve_bytes(pbytes, 'application/json')
            return

        if self.request.path.startswith(("/scad", "/render")):
            finger = DangerFinger()
            finger.build()
            p = var.split('.')[0]
            model = finger.models[FingerPart.from_str(p)] #TODO - fix PREVIEW enum
            scad_file = "output/dangerfinger_v4.2_" + p + ".scad"
            stl_file = "output/dangerfinger_v4.2_" + p + ".stl"
            write_scad(model.scad.encode('utf-8'), scad_file)
            if self.request.path.startswith("/scad"):
               self.serve_file(scad_file, 'text/scad')
            else:
                write_stl(scad_file, stl_file)
                self.serve_file(stl_file, 'model/stl')
            return

        self.write_error(500)

    def serve_file(self, filename, mimetype, download=False):
        with open(filename, 'rb') as file_h:
            print("serving %s" % filename)
            data = file_h.read()
            self.serve_bytes(data, mimetype, filename=filename if download else None)

    def serve_bytes(self, data, mimetype, filename=None):
        self.set_header('Content-Length', len(data))
        self.set_header('Content-Type', mimetype)
        if filename:
            self.set_header('Content-Disposition', 'filename="%s"' % filename)
        #now send response body
        self.write(data)
        print("200 OK response to: %s, %sb" %(self.request.uri, len(data)))

class EnumEncoder(json.JSONEncoder):
    def default(self, obj): #pylint: disable=method-hidden
        ''' test enum encoder'''
        return {"__enum__": str(obj)}

if __name__ == "__main__":
    sys.stdout = UnbufferedStdOut(sys.stdout)
    main()


# *********************************** Entry Point ****************************************
#@staticmethod
#def assemble(finger):
    #''' The entry point which loads a finger with proper parameters and outputs SCAD files as configured '''
    #sample param overrides for quick testing - comment out

    #uncomment to render STL instead of previewing
    #finger.action = Action.RENDER | Action.EMITSCAD

#    finger.part = FingerPart.HARD
    #finger.part = FingerPart.TIP
    #finger.render_quality = RenderQuality.FAST #ULTRAFAST FAST SUBMEDIUM MEDIUM EXTRAMEDIUM HIGH ULTRAHIGH
    #finger.render_threads = 8
    #finger.preview_explode = True
    #finger.preview_quality = RenderQuality.ULTRAFAST #ULTRAFAST FAST SUBMEDIUM MEDIUM EXTRAMEDIUM HIGH ULTRAHIGH
    #finger.preview_cut = True
    #finger.preview_rotate = 40
    #finger.animate_explode = True
    #finger.animate_rotate = True

    #load a configuration, with parameters from cli or env


    #build some pieces
 #   finger.build()

    #if finger.emitscad: finger.emit_scad()
    #if finger.render: finger.render_stl()

    #if finger.preview: finger.render_stl()
    #finger.render_png()

