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
#from danger_finger import *


def main():
    '''main'''

    http_port = 8081 #TODO config config.get("service_port", 8081)  # pylint: disable=invalid-name
    tornado.web.Application([
        (r"/params/", FingerHandler), #, {"params":config}),
        (r"/render/([a-zA-Z0-9]+/)", FingerHandler),
        (r"/scad/([a-zA-Z0-9]+/)", FingerHandler),
        (r"/preview", FingerHandler),
        #fallback serves static files, include ones to supply preview page
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": "./"})
        ]).listen(http_port)

    print("Listening on localhost %s" % (http_port))
    tornado.ioloop.IOLoop.instance().start()

# pylint: disable=W0223
class FingerHandler(tornado.web.RequestHandler):
    '''Handle a metadata request'''
    def get(self):

        print(" %s " % self.request)
        #print("part %s" % part)

        #TODO - mostly everything for these APIs

        finger = DangerFinger()

        #if params
        if self.request.path.startswith("/params"):
            params = {}

            for param in vars(type(finger)).items(): ###
            # #print (param)
                if param[0].startswith("_"): continue
                val = getattr(finger, param[0])
                if str(val).startswith(("<f", "<b")): continue
                params[param[0]] = val
                print(param, val)
            # for p in [a for a in dir(finger) if not a.startswith('_')]:
            #     v = getattr(finger, p)
            #     print(p, v)
            #     params[p] = v
                # loop preperties, build dict, emit json
                #send our http response
            pbytes = json.dumps(params, skipkeys=True, cls=EnumEncoder).encode('utf-8')
            self.set_header('Content-Length', len(pbytes))
            self.write(pbytes)
            self.finish()
            print("200 OK response to: %s, %sb" %(self.request.uri, len(pbytes)))
            return

        else:
            print("nothing to see here!")
            return
            #loop quert=y params
            # set them to a new finger
            # emit scad

            #if emit scad,set dl headers and send

            #if preview, also send to openscad to create png

            #if render, also send to open scad for STL to DL
        self.write_error(500)

    # def write_error(self, status_code, **kwargs): #pylint: disable=arguments-differ
    #     super().write_error(status_code, **kwargs)

class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
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
    main()
