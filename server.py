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
import zipfile
import concurrent
from io import BytesIO
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
    '''send default headers to ensure cors'''
    #print("setting headers!!!")
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With")
    self.set_header('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')

class StaticHandler(tornado.web.StaticFileHandler):
    '''handle static file requests'''
    def set_default_headers(self):
        '''send default headers to ensure cors'''
        set_def_headers(self)

    def options(self):
        '''send default headers to ensure cors'''
        self.set_status(204)
        self.finish()

    def data_received(self, chunk):
        pass

# pylint: disable=W0223
class FingerHandler(tornado.web.RequestHandler):
    ''' handle torando requests for finger api'''

    def set_default_headers(self):
        '''send default headers to ensure cors'''
        set_def_headers(self)

    async def get(self, var, var2=None):
        '''Handle a metadata request'''
        print("  HTTP Request: %s %s %s" % (self.request, self.request.path, var))
        if self.request.path.startswith(("/configs", "/profiles", "/models", "/preview", "/render", "/scad", "/downloads")):
            print("  Getting %s from s3 " % self.request.path[1:])
            b = FingerServer().get(self.request.path[1:], load=False)
            if b is None:
                self.set_status(404)
                return
            mime = 'application/json' if self.request.path.startswith(("/configs", "/profiles", "/models")) else "application/txt" \
                if self.request.path.startswith(("/preview", "/render", "/scad")) else 'application/zip'
            self.serve_bytes(b, mime)
            return

        if self.request.path.startswith(("/profile")):
            if self.request.path.find("/download") > -1:
                self.serve_download(var, var2)
                return
            if self.request.path.find("/metadata") > -1:
                self.serve_download(var, var2, metadata=True)
                return

        if self.request.path.startswith("/param"):
            params = DangerFinger().params(adv=var.startswith("/adv"), allv=var.startswith("/all"), extended=True)
            pbytes = json.dumps(params, default=str, skipkeys=True).encode('utf-8')
            self.serve_bytes(pbytes, 'application/json')
            return

        self.set_status(500)

    def delete(self, userhash, cfg):
        '''override delete method to allow removing config from profile'''
        print("  HTTP Request: %s %s %s %s" % (self.request, self.request.path, userhash, cfg))
        if self.request.path.startswith("/profile"):
            pkey = "profiles/%s" % userhash
            profile = FingerServer().get(pkey, load=True)
            if not profile: profile = {"userhash" : userhash, "createdtime" :  time.time(), "configs" : {}}
            if "configs" not in profile: profile["configs"] = {}

            if cfg in profile["configs"]:
                del profile["configs"][cfg]
                FingerServer().put(pkey, profile)
                self.set_status(204)
        self.set_status(500)

    def post(self, userhash, cfg):
        '''support post for several actions'''
        print("  HTTP Request: %s %s %s %s" % (self.request, self.request.path, userhash, cfg))
        if self.request.path.startswith("/profile"):
            pkey = "profiles/%s" % userhash
            profile = FingerServer().get(pkey, load=True)
            if not profile: profile = {"userhash" : userhash, "createdtime" :  time.time(), "configs" : {}}
            if "configs" not in profile: profile["configs"] = {}

            if self.request.path.find("/config") > -1:
                _config, cfgbytes, cfghash = package_config_json(process_post(self.request.body_arguments))
                print("ConfigHash: %s" % cfghash)

                cfg_load = FingerServer().get("configs/%s" % cfghash, load=True)
                if not cfg_load:
                    err = FingerServer().put("configs/%s" % cfghash, cfgbytes)
                    if err is not None:
                        self.set_status(503)
                        return

                if not cfg in profile["configs"] or profile["configs"][cfg] != cfghash:
                    profile["configs"][cfg] = cfghash
                    profile["updatedtime"] = time.time()
                    profile["lastconfig"] = cfg
                    err = FingerServer().put("profiles/%s" % userhash, profile)
                    if err is not None:
                        self.set_status(502)
                        return
                    print("Saved config to profile")
                self.set_status(204)
                return

            if self.request.path.find("/preview") > -1 or self.request.path.find("/render") > -1:
                if not FingerServer().queue(cfg, preview=self.request.path.find("/preview") > -1):
                    self.set_status(504)
                profile["lastconfig"] = cfg
                FingerServer().put("profiles/%s" % userhash, profile)
                self.set_status(204)
                return

        self.set_status(500)

    def serve_download(self, prf, cfg, metadata=False):
        '''find all assets for a config and package into a download zip'''
        try:
            profile = FingerServer().get("profiles/" + prf, load=True)
            if profile and "configs" in profile:
                for c in profile["configs"]:
                    if not cfg in (c, profile["configs"][c]):
                        continue
                    cfghash = profile["configs"][c]
                    zipname = "danger_finger_v%s_%s%s.zip" % (DangerFinger().VERSION, cfg, "_metadata" if metadata else "")
                    dlkey = "downloads/" + zipname
                    dl = FingerServer().get(dlkey)
                    if dl is None:
                        #pull files from s3
                        config = FingerServer().get("configs/%s" % cfghash)
                        models = get_config_models(cfghash)
                        files = get_assets(models, metadata)
                        if files is None:
                            self.set_status(404)
                            return
                        files["LICENSE"] = read_file("LICENSE")
                        files["README.md"] = read_file("README.md")
                        files["metadata/config_" + cfg + ".json"] = config
                        dl = create_zip(files)
                        FingerServer().put(dlkey, dl)
                    profile["lastconfig"] = cfg
                    FingerServer().put("profiles/%s" % prf, profile)

                    self.set_header('Content-Type', 'application/zip')
                    self.set_header('Content-Length', len(dl))
                    self.set_header("Content-Disposition", "attachment; filename=%s" % zipname)
                    self.write(dl)
                    return
        except Exception as e:
            print("Failed to create download %s: %s" % (cfg, e))
        self.set_status(404)

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

parts = [FingerPart.TIP, FingerPart.BASE, FingerPart.LINKAGE, FingerPart.MIDDLE, FingerPart.TIPCOVER, FingerPart.SOCKET, FingerPart.PLUGS]

handlers = [
        #get available parameters
        (r"/params(/?\w*)", FingerHandler),
        #handle post of config to a profile
        (r"/profile/([a-zA-Z0-9.]+)/config/([a-zA-Z0-9.]+)", FingerHandler),
        #handle initiation of preview render
        (r"/profile/([a-zA-Z0-9.]+)/preview/([a-zA-Z0-9.]+)", FingerHandler),
        #handle initiation of quality render
        (r"/profile/([a-zA-Z0-9.]+)/render/([a-zA-Z0-9.]+)", FingerHandler),
        #handle download of a config and all assets
        (r"/profile/([a-zA-Z0-9.]+)/download/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/profile/([a-zA-Z0-9.]+)/metadata/([a-zA-Z0-9.]+)", FingerHandler),
        #handle get or post of a profile
        (r"/profiles/([a-zA-Z0-9.]+)", FingerHandler),
        #handle gets from s3
        (r"/configs/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/scad/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/models/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/render/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/preview/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/downloads/([a-zA-Z0-9.]+)", FingerHandler),
        #fallback serves static files, include ones to supply preview page
        (r"/(.*)", StaticHandler, {"path": "./web/", "default_filename": "index.html"})
    ]

class FingerServer(Borg):
    '''server to handle s3 actions including queing of preview and render, and dequeue / processing of stl'''
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

    def queue(self, cfghash, preview=False):
        '''add models to queue'''
        path = "preview" if preview else "render"
        created = False
        for p in parts:
            pn = str.lower(str(p.name))
            pkey = get_key(cfghash, DangerFinger.VERSION, pn)
            modkey = "models/%s" % pkey + ".mod"

            #model file
            model = self.get(modkey, load=True)
            scadbytes = None
            if model is None:
                model, scadbytes = create_model(pn, DangerFinger.VERSION, cfghash)
                created = True
            else:
                scadbytes = self.get(model["scadkey"])
            if not scadbytes or len(scadbytes) < 16:
                scadbytes = build(pn, q=RenderQuality.NONE).encode('utf-8')
                model["scadhash"] = sha256(scadbytes).hexdigest()
                model["scadkey"] = "scad/%s" % model["scadhash"] + ".scad"
                created = True

            s3key = path + "/" + model["scadhash"]
            found = False
            for obj in self.dir(s3key):
                found = True
                print("Found file: %s" % obj.key)
            if not found:
                created = True
                print("Part not found:: %s" % cfghash)
                model[path + "queuedtime"] = time.time()
                self.put(s3key + ".mod", model)
                print("Part uploaded: %s" % s3key + ".mod")
            if created:
                self.put(modkey, model)
                self.put(model["scadkey"], scadbytes)
                print("Model uploaded: %s, %s" % (modkey, model["scadkey"]))
        if not created:
            print("Found all parts for %s " % cfghash)
        return True

    def dir(self, key):
        '''do a listing'''
        objs = []
        try:
            objs = self.bucket.objects.filter(Prefix=key)
        except Exception as e:
            print("Error: %s" % e)
        return objs

    def put(self, key, obj):
        '''put an object to s3'''
        b = obj if isinstance(obj, bytes) else json.dumps(obj, skipkeys=True).encode('utf-8') #, cls=EnumEncoder
        try:
            self.s3.Object(self.s3_bucket, key).put(Body=b)
            print("Created object %s " % (key))
        except Exception as e:
            print("Failed to save %s: %s" % (key, e))
            return e
        return None

    def get(self, key, load=False):
        '''get an object from s3 '''
        try:
            resp = self.s3.Object(self.s3_bucket, key).get()
            print("Found object: %s " % key)
            b = resp["Body"].read()
            return json.loads(b) if load else b
        except Exception as e:
            print("Object %s not found:: %s" % (key, e))
        return None

    def setup(self):
        '''setup the server - do this once to get a session'''
        self.s3session = boto3.Session(aws_access_key_id=self.aws_id, aws_secret_access_key=self.aws_key)
        self.s3 = self.s3session.resource('s3')
        self.bucket = self.s3.Bucket(self.s3_bucket)

    def __init__(self):#, **kw):
        Borg.__init__(self)

    def process_scad_loop(self, path, timeout):
        '''process a scad file in a loop'''
        time.sleep(timeout)
        while True:
            if self.lock: continue
            for obj in FingerServer().dir(path):
                try:
                    if obj.key.find(".mod") == -1:
                        continue
                    self.lock = True
                    print("Processing: %s" % obj.key)
                    scad_file = "output/" + obj.key.replace(path, "")
                    stl_file = scad_file + ".stl"
                    stl_key = obj.key.replace(".mod", ".stl")
                    pkey = path.rstrip('/')
                    #get the model
                    model = FingerServer().get(obj.key, load=True)
                    model[pkey + "starttime"] = time.time()
                    #create the scad
                    rq = RenderQuality.STUPIDFAST if path.find("preview") > -1 else RenderQuality.HIGH
                    scad = DangerFinger().scad_header(rq) + "\n" + FingerServer().get(model["scadkey"], load=False).decode('utf-8')
                    write_file(scad.encode('utf-8'), scad_file)
                    print("   Wrote SCAD file: %s" % scad_file)
                    #render it!
                    write_stl(scad_file, stl_file)
                    with open(stl_file, 'rb') as file_h:
                        FingerServer().put(stl_key, file_h.read())
                        print("   uploaded %s" % stl_key)
                        obj.delete()
                        print("   deleted %s" % obj.key)
                    model[pkey + "completedtime"] = time.time()
                    model[pkey + "key"] = stl_key
                    FingerServer().put(model["modkey"], model)
                    print("   updated %s" % model["modkey"])
                except Exception as e:
                    print("Error with %s: %s" % (obj.key, e))
            self.lock = False
            time.sleep(timeout)

def get_file_list(items):
    '''get files from a list of keys'''
    objs = {}
    for key in items:
        obj = FingerServer().get(key, load=False)
        objs[key] = obj
    return objs

def get_assets(models, metadata):
    '''get assets for a list of models'''
    files = {}
    scad = get_file_list([models[x]["scadkey"] for x in models])
    for (f, s) in models.items():
        if s is None: return None
        b = json.dumps(s, skipkeys=True)
        files["metadata/" + f] = b
    for (f, s) in scad.items():
        if s is None: return None
        bs = DangerFinger().scad_header(RenderQuality.HIGH) + "\n" + s.decode('utf-8')
        b = bs.encode('utf-8')
        files["metadata/" + f] = b
    if not metadata:
        preview = get_file_list([models[x]["previewkey"] for x in models])
        renders = get_file_list([models[x]["renderkey"] for x in models])
        for (f, b) in preview.items():
            if b is None: return None
            files[f] = b
        for (f, b) in renders.items():
            if b is None: return None
            files[f.replace("render/", "")] = b
    return files

def get_config_models(cfg):
    '''get models from a configuration'''
    models = {}
    for p in list(parts):
        pn = str.lower(str(FingerPart(p).name))
        v = DangerFinger.VERSION
        pkey = get_key(cfg, v, pn)
        modkey = "models/%s" % pkey + ".mod"
        model = FingerServer().get(modkey, load=True)
        models[modkey] = model
    return models

def check_null(obj):
    '''check dict for null members'''
    for i in obj:
        if obj[i] is None: return False
    return True

def get_key(cfg, v, pn):
    '''get a config key'''
    return "%s_%s_%s" % (cfg, pn, v)

def create_model(pn, v, cfghash):
    '''create a new model and scad'''
    pkey = get_key(cfghash, v, pn)
    modkey = "models/%s" % pkey + ".mod"
    scad = build(pn, q=RenderQuality.NONE)
    scadbytes = scad.encode('utf-8')
    scadhash = sha256(scadbytes).hexdigest()
    scadkey = "scad/%s" % scadhash + ".scad"
    return {"cdfghash": cfghash, "version": v, "part" : pn, "createdtime" : time.time(), "scadkey" : scadkey, "scadhash" : scadhash, "modkey" : modkey}, scadbytes

def process_post(args):
    '''parse a post body'''
    return {k: v[0].decode('utf-8') for (k, v) in args.items()}

def create_zip(files):
    '''create a big ol zip file'''
    bf = BytesIO()
    zf = zipfile.ZipFile(bf, "w")
    for (f, b) in files.items():
        zf.writestr(f, b)
    zf.close()
    dl = bf.getvalue()
    bf.close()
    return dl

def read_file(filename):
    '''serve a file from disk to client'''
    with open(filename, 'rb') as file_h:
        print("serving %s" % filename)
        return file_h.read()

def remove_defaults(config):
    '''ensure defaults are not cluttering the config'''
    params = DangerFinger().params()
    for k in params:
        if k in config and str(params[k]) == str(config[k]):
            config.pop(k)

def package_config_json(obj):
    '''process a config file to sort it'''
    config = OrderedDict(sorted(obj.items(), key=lambda t: t[0]))
    cfgbytes = json.dumps(config, skipkeys=True).encode('utf-8')
    cfghash = sha256(cfgbytes).hexdigest()
    return config, cfgbytes, cfghash

def write_file(data, filename):
    ''' write bytes to file '''
    print("  writing %s bytes to %s" %(len(data), filename))
    with open(filename, 'wb') as file_h:
        file_h.write(data)

def write_stl(scad_file, stl_file):
    ''' render and write stl to file '''
    start = time.time()
    print("  Beginning render of %s" %(stl_file))
    Renderer().scad_to_stl(scad_file, stl_file)#), trialrun=True)
    print("  Rendered %s in %s sec" % (stl_file, round(time.time()-start, 1)))
    return stl_file

def build(p, q=RenderQuality.HIGH):
    '''build a finger model and return scad'''
    print("Building finger")
    finger = DangerFinger()
    finger.render_quality = q#RenderQuality.STUPIDFAST #     INSANE = 2 ULTRAHIGH = 5 HIGH = 10 EXTRAMEDIUM = 13 MEDIUM = 15 SUBMEDIUM = 17 FAST = 20 ULTRAFAST = 25 STUPIDFAST = 30
    finger.build(header=(q != RenderQuality.NONE))
    for _fp, model in finger.models.items():
        if iterable(model):
            if str(model[0].part) == p:
                return flatten([x.scad for x in model])
        elif str(model.part) == p:
            return model.scad
    return None

async def make_app():
    ''' create server async'''
    settings = dict(
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        debug=tornado.options.options.debug,
    )
    app = tornado.web.Application(handlers, **settings)
    app.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    app.counter = 0
    app.listen(fs.http_port)


if __name__ == "__main__":
    sys.stdout = UnbufferedStdOut(sys.stdout)

    fs = FingerServer()
    Params.parse(fs)
    fs.setup()
    a = make_app()

    t_preview = threading.Thread(target=fs.process_scad_loop, args=['preview/', fs.preview_poll])
    t_render = threading.Thread(target=fs.process_scad_loop, args=['render/', fs.render_poll])
    t_preview.start()
    t_render.start()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(a)
    loop.run_forever()
