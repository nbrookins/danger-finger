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
import concurrent
import threading
from collections import OrderedDict
from hashlib import sha256
import tornado.options
import tornado.ioloop
import tornado.web
import solid
import boto3
from danger import *

tornado.options.define('port', type=int, default=8081, help='server port number (default: 9000)')
tornado.options.define('debug', type=bool, default=False, help='run in debug mode with autoreload (default: False)')

def set_def_headers(self):
    #print("setting headers!!!")
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With")
    self.set_header('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')

class StaticHandler(tornado.web.StaticFileHandler):
    def set_default_headers(self):
        set_def_headers(self)

    def options(self):
        self.set_status(204)
        self.finish()

    def data_received(self, chunk):
        pass

# pylint: disable=W0223
class FingerHandler(tornado.web.RequestHandler):
    ''' handle torando requests for finger api'''

    def set_default_headers(self):
        set_def_headers(self)

    async def get(self, var, var2=None):
        '''Handle a metadata request'''
        print("  HTTP Request: %s %s %s" % (self.request, self.request.path, var))
        if self.request.path.startswith(("/configs", "/profiles", "/models", "/preview", "/render", "/scad")):
            print("  Getting %s from s3 " % self.request.path[1:])
            b = s3_get(self.request.path[1:], load=False)
            if b is None:
                self.set_status(404)
                return
            self.serve_bytes(b, 'application/json')
            return

        if self.request.path.startswith("/param"):
            params = DangerFinger().params(adv=var.startswith("/adv"), allv=var.startswith("/all"), extended=True)
            pbytes = json.dumps(params, default=str, skipkeys=True).encode('utf-8')
            self.serve_bytes(pbytes, 'application/json')
            return

        self.set_status(500)

    def delete(self, userhash, cfg):
        print("  HTTP Request: %s %s %s %s" % (self.request, self.request.path, userhash, cfg))
        if self.request.path.startswith("/profile"):
            pkey = "profiles/%s" % userhash
            profile = s3_get(pkey)
            if not profile: profile = {"userhash" : userhash, "createdtime" :  time.time(), "configs" : {}}
            if "configs" not in profile: profile["configs"] = {}

            if cfg in profile["configs"]:
                del profile["configs"][cfg]
                s3_put(pkey, profile)
                self.set_status(204)
        self.set_status(500)

    def post(self, userhash, cfg):
        print("  HTTP Request: %s %s %s %s" % (self.request, self.request.path, userhash, cfg))
        if self.request.path.startswith("/profile"):
            pkey = "profiles/%s" % userhash
            profile = s3_get(pkey)
            if not profile: profile = {"userhash" : userhash, "createdtime" :  time.time(), "configs" : {}}
            if "configs" not in profile: profile["configs"] = {}

            if self.request.path.find("/config") > -1:
                _config, cfgbytes, cfghash = package_json(process_post(self.request.body_arguments))
                print("ConfigHash: %s" % cfghash)

                cfg_load = s3_get("configs/%s" % cfghash)
                if not cfg_load:
                    err = s3_put("configs/%s" % cfghash, cfgbytes)
                    if err is not None:
                        self.set_status(503)
                        return

                if not cfg in profile["configs"] or profile["configs"][cfg] != cfghash:
                    profile["configs"][cfg] = cfghash
                    profile["updatedtime"] = time.time()
                    err = s3_put("profiles/%s" % userhash, profile)
                    if err is not None:
                        self.set_status(502)
                        return
                    print("Saved config to profile")
                self.set_status(204)
                return

            if self.request.path.find("/preview") > -1 or self.request.path.find("/render") > -1:
                if not initiate_render(cfg, preview=self.request.path.find("/preview") > -1):
                    self.set_status(504)
                self.set_status(204)
                return

        self.set_status(500)

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

parts = (FingerPart.TIP | FingerPart.BASE | FingerPart.LINKAGE | FingerPart.MIDDLE)

handlers = [
        #get available parameters
        (r"/params(/?\w*)", FingerHandler),
        #handle post of config to a profile
        (r"/profile/([a-zA-Z0-9.]+)/config/([a-zA-Z0-9.]+)", FingerHandler),
        #handle initiation of preview render
        (r"/profile/([a-zA-Z0-9.]+)/preview/([a-zA-Z0-9.]+)", FingerHandler),
        #handle initiation of quality render
        (r"/profile/([a-zA-Z0-9.]+)/render/([a-zA-Z0-9.]+)", FingerHandler),
        #handle get or post of a profile
        (r"/profiles/([a-zA-Z0-9.]+)", FingerHandler),
        #handle gets from s3
        (r"/configs/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/scad/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/models/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/render/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/preview/([a-zA-Z0-9.]+)", FingerHandler),
        #fallback serves static files, include ones to supply preview page
        (r"/(.*)", StaticHandler, {"path": "./web/", "default_filename": "index.html"})
    ]

def get_key(cfg, v, pn):
    return "%s_%s_%s" % (cfg, pn, v)

def initiate_render(cfghash, preview=False):
    path = "preview" if preview else "render"
    created = False
    for p in FingerPart:
        if parts & p == 0 or parts & p == FingerPart.HARD or parts & p == FingerPart.ALL: continue
        pn = str.lower(str(p.name))
        v = DangerFinger.VERSION
        pkey = get_key(cfghash, v, pn)
        modkey = "models/%s" % pkey + ".mod"

        #model file
        model = s3_get(modkey)
        if model is None:
            model, scadbytes = create_model(pn, v, cfghash)
            created = True

        s3key = path + "/" + model["scadhash"]
        tqkey = path + "queuedtime"
        objs = s3_list(s3key)
        found = False
        for obj in objs:
            found = True
            print("Found file: %s" % obj.key)
        if not found:
            created = True
            print("Part not found:: %s" % cfghash)
            model[tqkey] = time.time()
            s3_put(s3key + ".mod", model)
            print("Part uploaded: %s" % s3key + ".mod")
        if created:
            s3_put(modkey, model)
            s3_put(model["scadkey"], scadbytes)
            print("Model uploaded: %s, %s" % (modkey, model["scadkey"]))
    if not created:
        print("Found all parts for %s " % cfghash)
    return True

def create_model(pn, v, cfghash):
    pkey = get_key(cfghash, v, pn)
    modkey = "models/%s" % pkey + ".mod"
    scad = build(pn, q=RenderQuality.NONE)
    scadbytes = scad.encode('utf-8')
    scadhash = sha256(scadbytes).hexdigest()
    scadkey = "scad/%s" % scadhash + ".scad"
    return {"cdfghash": cfghash, "version": v, "part" : pn, "createdtime" : time.time(), "scadkey" : scadkey, "scadhash" : scadhash, "modkey" : modkey}, scadbytes

def process_post(args):
    return {k: v[0].decode('utf-8') for (k, v) in args.items()}

def remove_defaults(config):
    params = DangerFinger().params()
    for k in params:
        if k in config and str(params[k]) == str(config[k]):
            config.pop(k)

def package_json(obj):
    config = OrderedDict(sorted(obj.items(), key=lambda t: t[0]))
    cfgbytes = json.dumps(config, skipkeys=True).encode('utf-8')
    cfghash = sha256(cfgbytes).hexdigest()
    return config, cfgbytes, cfghash

def s3_get(key, load=True):
    try:
        resp = FingerServer().s3.Object("danger-finger", key).get()
        print("Found object: %s " % key)
        b = resp["Body"].read()
        return json.loads(b) if load else b
    except Exception as e:
        print("Object %s not found:: %s" % (key, e))
    return None

def s3_list(key):
    objs = []
    try:
        objs = FingerServer().bucket.objects.filter(Prefix=key)
    except Exception as e:
        print("Error: %s" % e)
    return objs

def s3_put(key, obj):
    b = obj if isinstance(obj, bytes) else json.dumps(obj, skipkeys=True).encode('utf-8') #, cls=EnumEncoder
    try:
        FingerServer().s3.Object("danger-finger", key).put(Body=b)
        print("Created object %s " % (key))
    except Exception as e:
        print("Failed to save %s: %s" % (key, e))
        return e
    return None

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
    print("  Rendered %s in %s sec" % (stl_file, round(time.time()-start, 1)))
    return stl_file

def build(p, q=RenderQuality.HIGH):
    print("Building finger")
    finger = DangerFinger()
    finger.render_quality = q#RenderQuality.STUPIDFAST #     INSANE = 2 ULTRAHIGH = 5 HIGH = 10 EXTRAMEDIUM = 13 MEDIUM = 15 SUBMEDIUM = 17 FAST = 20 ULTRAFAST = 25 STUPIDFAST = 30
    finger.build(header=(q != RenderQuality.NONE))
    for _fp, model in finger.models.items():
        if not iterable(model) and str(model.part) == p:
            return model.scad

async def make_app():
    ''' create server async'''
    settings = dict(
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        debug=tornado.options.options.debug,
    )
    app = tornado.web.Application(handlers, **settings)
    #app = tornado.web.Application(handlers, debug=True)
    app.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    app.counter = 0
    app.listen(fs.http_port)

class FingerServer(Borg):
    preview_poll = Prop(val=10, minv=0, maxv=120, doc=''' Enable explode mode, only for preview ''', hidden=True)
    render_poll = Prop(val=30, minv=0, maxv=120, doc=''' rotate the finger ''', hidden=True)
    http_port = Prop(val=8081, minv=80, maxv=65500, doc=''' Enable explode animation, only for preview ''', hidden=True)
    s3_bucket = Prop(val='danger-finger', doc=''' Enable rotate animation, only for preview ''', hidden=True)
    aws_id = Prop(val="", doc=''' Enable rotate animation, only for preview ''', hidden=True)
    aws_key = Prop(val="", doc=''' Enable rotate animation, only for preview ''', hidden=True)
    s3session = None
    s3 = None
    bucket = None
    lock = False

    def setup(self):
        self.s3session = boto3.Session(aws_access_key_id=self.aws_id, aws_secret_access_key=self.aws_key)
        self.s3 = self.s3session.resource('s3')
        self.bucket = self.s3.Bucket(self.s3_bucket)

    def __init__(self):#, **kw):
        Borg.__init__(self)

    def process_scad(self, path, timeout):
        time.sleep(timeout)
        while True:
            try:
                if self.lock: continue
                for obj in s3_list(path):
                    try:
                        if obj.key.find(".mod") > -1:
                            self.lock = True
                            print("Processing: %s" % obj.key)
                            scad_file = "output/" + obj.key.replace(path, "")
                            stl_file = scad_file + ".stl"
                            stl_key = obj.key.replace(".mod", ".stl")
                            pkey = path.rstrip('/')
                            tskey = pkey + "starttime"
                            tfkey = pkey + "completedtime"
                            #get the model
                            model = s3_get(obj.key)
                            model[tskey] = time.time()
                            #create the scad
                            rq = RenderQuality.STUPIDFAST if path.find("preview") > -1 else RenderQuality.HIGH
                            scad = DangerFinger().scad_header(rq) + "\n" + s3_get(model["scadkey"], load=False).decode('utf-8')
                            scadbytes = scad.encode('utf-8')
                            write_file(scadbytes, scad_file)
                            print("   Wrote SCAD file: %s" % scad_file)
                            #render it!
                            write_stl(scad_file, stl_file)
                            with open(stl_file, 'rb') as file_h:
                                data = file_h.read()
                                s3_put(stl_key, data)
                                print("   uploaded %s" % stl_key)
                                obj.delete()
                                print("   deleted %s" % obj.key)
                            model[tfkey] = time.time()
                            model[pkey + "key"] = stl_key
                            s3_put(model["modkey"], model)
                            print("   updated %s" % model["modkey"])
                    except Exception as e:
                        print("Error with %s: %s" % (obj.key, e))
            except Exception as e:
                print("Error: %s" % e)
            finally:
                self.lock = False
                time.sleep(timeout)

if __name__ == "__main__":
    sys.stdout = UnbufferedStdOut(sys.stdout)

    fs = FingerServer()
    Params.parse(fs)
    fs.setup()
    a = make_app()

    t_preview = threading.Thread(target=fs.process_scad, args=['preview/', fs.preview_poll])
    t_render = threading.Thread(target=fs.process_scad, args=['render/', fs.render_poll])
    t_preview.start()
    t_render.start()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(a)
    loop.run_forever()