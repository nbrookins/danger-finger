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
import solid
from danger import *

tornado.options.define('port', type=int, default=8081, help='server port number (default: 9000)')
tornado.options.define('debug', type=bool, default=False, help='run in debug mode with autoreload (default: False)')

# class Worker(threading.Thread):
#    def __init__(self, callback=None, *args, **kwargs):
#         super(Worker, self).__init__(*args, **kwargs)
#         self.callback = callback

#    def run(self):


# class MainHandler(tornado.web.RequestHandler):
#     @tornado.web.asynchronous
#     @tornado.gen.coroutine
#     def get(self):
#         response = yield tornado.gen.Task(sleeper)
#         self.write(response)
#         self.finish()

def main():
    '''main'''

    config = {}
    Params.parse(config)

    server = True
    if server:
        start_server()
        return

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
            filename = "output/dangerfinger_v4.2_" + model.part
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

def start_server():#http_port=8081):
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(tornado.options.options.port)
    tornado.ioloop.IOLoop.instance().start()
#     ''' start the web server to take api request for finger building '''


#     print("Listening on localhost %s" % (http_port))
#     tornado.ioloop.IOLoop.instance().start()

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
    Renderer().scad_to_stl(scad_file, stl_file)
    print("  Rendered %s in %s sec" % (stl_file, round(time.time()-start, 1)))

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

class Application(tornado.web.Application):
    def __init__(self):
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
        tornado.web.Application.__init__(self, handlers, **settings)


# def run_async(func):
#     @wraps(func)
#     def async_func(*args, **kwargs):
#         func_hl = Thread(target = func, args = args, kwargs = kwargs)
#         func_hl.start()
#         return func_hl

#     return async_func

#@run_async
@tornado.gen.coroutine
def task(scad_file, stl_file):
    write_stl(scad_file, stl_file)
    #self.serve_file(stl_file, 'model/stl')
    #callback(
    return (stl_file)
    #raise gen.Return(response


# pylint: disable=W0223
class FingerHandler(tornado.web.RequestHandler):
    '''Handle a metadata request'''
    @tornado.gen.coroutine
    def get(self, var):
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
                response = yield task(scad_file, stl_file) #tornado.gen.Task(sleeper)
                self.serve_file(response, 'model/stl')
                #self.write(response)
                #self.finish()
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

if __name__ == "__main__":
    sys.stdout = UnbufferedStdOut(sys.stdout)
    main()
