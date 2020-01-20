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
from enum import IntFlag, Flag
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

            # for param in vars(type(config_obj)).items(): ###
            # #print (param)
            # if param[0].startswith("_"): continue
            # val = getattr(config_obj, param[0])
            # if str(val).startswith(("<f", "<b")): continue

            for p in [a for a in dir(finger) if not a.startswith('_')]:
                v = getattr(finger, p)
                print(p, v)
                params[p] = v
                # loop preperties, build dict, emit json
                #send our http response
            pbytes = json.dumps(params, skipkeys=True).encode('utf-8')
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

        # exmple stuff from elsewhere
        #         for header in self.request.headers:
        #         self.set_header('Content-Type', 'text/html; charset=UTF-8')
        #         try:
        #             md_bytes = json.dumps(md_list, skipkeys=True, cls=sdsi_eventsvc_config.DatetimeEncoder).encode('utf-8')
        #         except Exception as ex:
        #             print("Error: %s " % ex)
        #             raise tornado.web.HTTPError(404)

        #     #send our http response
        #     self.set_header('Content-Length', len(md_bytes))
        #     self.write(md_bytes)
        #     self.finish()
        #     print("200 OK response to: %s, %sb" %(self.request.uri, len(md_bytes)))
        #     return
        self.write_error(500)

    def write_error(self, status_code, **kwargs): #pylint: disable=arguments-differ
        super().write_error(status_code, **kwargs)

if __name__ == "__main__":
    main()
