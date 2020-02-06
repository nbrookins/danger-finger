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
import threading
from functools import wraps
import tornado.options
import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.concurrent
from tornado.concurrent import run_on_executor
import concurrent
from concurrent.futures import ThreadPoolExecutor
import solid
from danger import *

tornado.options.define('port', type=int, default=8081, help='server port number (default: 9000)')
tornado.options.define('debug', type=bool, default=False, help='run in debug mode with autoreload (default: False)')


def main():
    '''main'''

    config = {}
    Params.parse(config)

    # server = True
    # if server:
    #     start_server()
    #     return

    print("running CLI")
    finger = DangerFinger()

    render_stl = FingerPart.NONE
    render_stl = FingerPart.HARD # HARD PREVIEW ALL
    cores = 6

    Params.parse(finger)
    finger.render_quality = RenderQuality.HIGH #  INSANE = 2 ULTRAHIGH = 5 HIGH = 10 EXTRAMEDIUM = 13 MEDIUM = 15 SUBMEDIUM = 17 FAST = 20 ULTRAFAST = 25 STUPIDFAST = 30
    finger.preview_quality = RenderQuality.FAST #     INSANE = 2 ULTRAHIGH = 5 HIGH = 10 EXTRAMEDIUM = 13 MEDIUM = 15 SUBMEDIUM = 17 FAST = 20 ULTRAFAST = 25 STUPIDFAST = 30
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
            write_file(model.scad.encode('utf-8'), model.scad_filename)

    if render_stl:
        files = []
        for fp, model in finger.models.items():
            if fp & render_stl == fp and not iterable(model): #TODO - make expanded one for non unioned plugs
                files.append(model.scad_filename)
        if files:
            Renderer().scad_parallel_to_stl(files, max_concurrent_tasks=cores)
    print("Complete")

# def start_server():#http_port=8081):
#     http_server = tornado.httpserver.HTTPServer(Application())
#     http_server.listen(tornado.options.options.port)
#     tornado.ioloop.IOLoop.instance().start()
#     ''' start the web server to take api request for finger building '''

def write_file(data, filename):
    ''' write bytes to file '''
    print("  writing %s bytes to %s" %(len(data), filename))
    with open(filename, 'wb') as file_h:
        file_h.write(data)

def write_stl(scad_file, stl_file):
    ''' render and write stl to file '''
    #TODO - cache these with hash of config...
    start = time.time()
    print("  Beginning render of %s" %(stl_file))
    Renderer().scad_to_stl(scad_file, stl_file)#), trialrun=True)
    #sp = Subprocess(print_res, timeout=30, args=cmd)
    #sp.start()
    print("  Rendered %s in %s sec" % (stl_file, round(time.time()-start, 1)))
    return stl_file

def get_params(self, finger, var):
    '''walk finger to discover parameters'''
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
    # executor = ThreadPoolExecutor(max_workers=4)

    '''Handle a metadata request'''
    #@tornado.gen.coroutine
    async def get(self, var):
        '''Handle a metadata request'''
        print("  HTTP Request: %s %s %s" % (self.request, self.request.path, var))
        #TODO - get config here from query string or post
        if self.request.path.startswith("/param"):
            params = DangerFinger().params(adv=var.startswith("/adv"), allv=var.startswith("/all"), extended=True)
            pbytes = json.dumps(params, skipkeys=True, cls=EnumEncoder).encode('utf-8')
            self.serve_bytes(pbytes, 'application/json')
            return

        if self.request.path.startswith(("/scad", "/render")):
            finger = DangerFinger()
            finger.render_quality = RenderQuality.ULTRAFAST
            finger.build()
            p = var.split('.')[0]
            model = finger.models[FingerPart.from_str(p)]
            scad_file = "output/dangerfinger_v4.2_" + p + ".scad"
            stl_file = "output/dangerfinger_v4.2_" + p + ".stl"
            write_file(model.scad.encode('utf-8'), scad_file)
            if self.request.path.startswith("/scad"):
                self.serve_file(scad_file, 'text/scad')
            else:
                #response = yield task(scad_file, stl_file) #tornado.gen.Task(sleeper)
                #yield self.task(scad_file, stl_file)
                #print(response.)
                # self.serve_file(stl_file, 'model/stl')
                #self.write(response)
                #self.finish()

                l = asyncio.get_event_loop()
                f = l.run_in_executor(self.application.executor, write_stl, scad_file, stl_file)
                await f
                #print(r)
                self.serve_file(stl_file, 'model/stl')
            return

        self.write_error(500)

    #         Worker(self.worker_done).start()


    # def worker_done(self, value):
    #     self.finish(value)
    def serve_file(self, filename, mimetype, download=False):
        '''serve a file from disk to client'''
        with open(filename, 'rb') as file_h:
            print("serving %s" % filename)
            data = file_h.read()
            self.serve_bytes(data, mimetype, filename=filename if download else None)

    def serve_bytes(self, data, mimetype, filename=None):
        '''serve bytes to our client'''
        self.set_header('Content-Length', len(data))
        self.set_header('Content-Type', mimetype)
        if filename:
            self.set_header('Content-Disposition', 'filename="%s"' % filename)
        #now send response body
        self.write(data)
        print("200 OK response to: %s, %sb" %(self.request.uri, len(data)))

class EnumEncoder(json.JSONEncoder):
    '''simple encoder to support emuns generically'''
    def default(self, obj): #pylint: disable=method-hidden, arguments-differ
        ''' test enum encoder'''
        return {"__enum__": str(obj)}

async def make_app():
    ''' create server async'''
    handlers = [
        (r"/params(/?\w*)", FingerHandler), #, {"params":config}),
        (r"/render/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/scad/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/preview", FingerHandler),
        #fallback serves static files, include ones to supply preview page
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": "./web/", "default_filename": "index.html"})
        # ]).listen(http_port)
        #     (r"/", IndexHandler),
        #     (r"/thread", ThreadHandler),
    ]
    settings = dict(
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        debug=tornado.options.options.debug,
    )
    app = tornado.web.Application(handlers, **settings)
    #app = tornado.web.Application(handlers, debug=True)
    app.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    app.counter = 0
    app.listen(8081)

if __name__ == "__main__":
    sys.stdout = UnbufferedStdOut(sys.stdout)
    server = True

    if server:
        #tornado.platform.asyncio.AsyncIOMainLoop().install()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(make_app())
        loop.run_forever()
    else:
        main()

