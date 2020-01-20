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

def main():
    '''main'''
   
    http_port = 8081 #TODO config config.get("service_port", 8081)  # pylint: disable=invalid-name
    tornado.web.Application([
        (r"/params/([a-zA-Z0-9]+/)", FingerHandler), #, {"params":config}),
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
    def initialize(self):#, params): #pylint: disable=arguments-differ
        pass

    def get(self, part):#pylint: disable=arguments-differ
        print("part %s" % part)

        #TODO - mostly everything for these APIs

        #if params
            # loop preperties, build dict, emit json

        #else
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
