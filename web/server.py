#!/bin/python
# pylint: disable=C0302, line-too-long, unused-wildcard-import, wildcard-import, invalid-name, broad-except
'''
The danger_finger copyright 2014-2020 Nicholas Brookins and Danger Creations, LLC
http://dangercreations.com/prosthetics :: http://www.thingiverse.com/thing:1340624
Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 https://creativecommons.org/licenses/by-nc-sa/4.0/
Source code licensed under Apache 2.0:  https://www.apache.org/licenses/LICENSE-2.0
'''
import asyncio
import os
import shutil
import sys
import json
import time
import uuid
import zipfile
import concurrent
from io import BytesIO
import threading
from collections import OrderedDict
from hashlib import sha256
import brotli
import tornado.options
import tornado.web
import boto3

# Add parent directory to path so we can import danger module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from danger import *
#from danger.Borg import Borg
from danger.Params import Params
from danger.tools import *
from danger.Scad_Renderer import *

#TODO 1 - get new image running with auth variables
#TODO 1 - implement API in index.html

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
            b = None
            if self.request.path.startswith(("/models", "/preview", "/render", "/scad")) and self.request.path.find(".") == -1:
                l = []
                for obj in FingerServer().dir(self.request.path[1:]):
                    l.append(FingerServer().get(obj.key, load=True))
                b = json.dumps(l).encode('utf-8')
            else:
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
                if self.request.headers.get("Content-Type", "").startswith("application/json"):
                    try:
                        config_dict = json.loads(self.request.body or b'{}')
                    except json.JSONDecodeError:
                        self.set_status(400)
                        return
                else:
                    config_dict = process_post(self.request.body_arguments)
                _config, cfgbytes, cfghash = package_config_json(config_dict)
                print("ConfigHash: %s" % cfghash)

                if not FingerServer().get("configs/%s" % cfghash, load=True):
                    err = FingerServer().put("configs/%s" % cfghash, cfgbytes)
                    if err is not None:
                        self.set_status(503)
                        return

                # Sync render and store STLs in S3 (10s timeout)
                try:
                    executor = getattr(self.application, "executor", None)
                    if executor:
                        future = executor.submit(
                            _run_sync_preview_or_render,
                            config_dict,
                            preview_quality=False,
                            store_in_s3=True,
                        )
                        future.result(timeout=PREVIEW_TIMEOUT_SEC)
                    else:
                        _run_sync_preview_or_render(config_dict, preview_quality=False, store_in_s3=True)
                except concurrent.futures.TimeoutError:
                    self.set_status(504)
                    self.write(json.dumps({"error": "Render timed out (max %s s)" % PREVIEW_TIMEOUT_SEC}))
                    return
                except Exception as e:
                    print("Save render failed: %s" % e)
                    self.set_status(500)
                    self.write(json.dumps({"error": str(e)}))
                    return

                prev_entry = profile["configs"].get(cfg)
                profile["configs"][cfg] = _config_entry_with_history(prev_entry, cfghash)
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
                    if c != cfg:
                        continue
                    cfghash = _resolve_cfghash(profile["configs"][c])
                    if not cfghash:
                        continue
                    zipname = "danger_finger_v%s_%s%s.zip" % (DangerFinger().VERSION, cfg, "_metadata" if metadata else "")
                    dlkey = "downloads/" + zipname
                    dl = FingerServer().get(dlkey)
                    if dl is None:
                        #pull files from s3
                        config = FingerServer().get("configs/%s" % cfghash, load=True)
                        if not config:
                            self.set_status(404)
                            return
                        models = get_config_models(cfghash)
                        files = get_assets(models, metadata) if models and any(models.get(k) for k in models) else None
                        if files is None:
                            # New layout: render/cfghash/part.stl (no .mod); build zip from listing
                            files = {"metadata/config_%s.json" % cfg: json.dumps(config, indent=2)}
                            prefix = "render/%s/" % cfghash
                            for obj in FingerServer().dir(prefix):
                                if obj.key.endswith(".stl"):
                                    stl = FingerServer().get(obj.key, load=False)
                                    if stl:
                                        name = obj.key.replace(prefix, "")
                                        files[name] = stl
                            if len(files) <= 1:
                                self.set_status(404)
                                return
                        else:
                            files["metadata/config_" + cfg + ".json"] = json.dumps(config) if isinstance(config, dict) else config
                        files["LICENSE"] = read_file("LICENSE")
                        files["README.md"] = read_file("README.md")
                        dl = create_zip(files)
                        FingerServer().put(dlkey, dl, compress=False)
                    profile["lastconfig"] = cfg
                    FingerServer().put("profiles/%s" % prf, profile)
                    self.serve_bytes(dl, 'application/zip', filename=zipname)
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


def _preview_config():
    """Build preview layout config from DangerFingerParams for the web viewer."""
    from danger.finger_params import DangerFingerParams as P
    from danger.finger import PART_COLORS
    return {
        "rotateOffsets": {k: list(v) for k, v in P._preview_rotate_offsets.items()},
        "positionOffsets": {k: list(v) for k, v in P._preview_position_offsets.items()},
        "plugInstances": [{"position": list(p["position"]), "rotation": list(p["rotation"])} for p in P._preview_plug_instances],
        "partColors": {k: v for k, v in PART_COLORS.items()},
    }


class ApiPartsHandler(tornado.web.RequestHandler):
    '''GET /api/parts - list part ids and labels for viewer filter'''
    def set_default_headers(self):
        set_def_headers(self)

    def get(self):
        part_list = [{"id": str(p.name).lower(), "label": str(p.name).capitalize()} for p in parts]
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({"parts": part_list, "previewConfig": _preview_config()}))


PREVIEW_TIMEOUT_SEC = 10
PREVIEW_TEMP_DIR = "output/preview_temp"


def _run_sync_preview_or_render(config_dict, preview_quality=True, store_in_s3=False):
    '''
    Run OpenSCAD for all parts synchronously. Returns (cfghash, config, stl_urls_or_run_id).
    For preview: writes STLs to temp dir, returns run_id and stl_urls point at /api/preview/temp/{run_id}/{part}.stl.
    For render with store_in_s3: writes STLs to S3 (existing queue/pipeline or direct), returns stl_urls from S3.
    Raises TimeoutError if over PREVIEW_TIMEOUT_SEC; other exceptions on build/render failure.
    '''
    config, cfgbytes, cfghash = package_config_json(config_dict)
    quality = RenderQuality.STUPIDFAST if preview_quality else RenderQuality.HIGH
    os.makedirs(PREVIEW_TEMP_DIR, exist_ok=True)
    run_id = str(uuid.uuid4())[:12]
    run_dir = os.path.join(PREVIEW_TEMP_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)
    stl_urls = {}
    try:
        for p in parts:
            pn = str(p.name).lower()
            scad_out = os.path.join(run_dir, pn + ".scad")
            stl_out = os.path.join(run_dir, pn + ".stl")
            scad_result = build(pn, dict(config), quality)
            if scad_result is None:
                continue
            scad_str = scad_result if isinstance(scad_result, str) else "\n".join(scad_result)
            write_file(scad_str.encode('utf-8'), scad_out)
            write_stl(scad_out, stl_out)
            if store_in_s3:
                s3_prefix = "preview" if preview_quality else "render"
                stl_key = "%s/%s/%s.stl" % (s3_prefix, cfghash, pn)
                with open(stl_out, 'rb') as f:
                    FingerServer().put(stl_key, f.read(), compress=False)
                stl_urls[pn] = "/" + stl_key
            else:
                stl_urls[pn] = "/api/preview/temp/%s/%s.stl" % (run_id, pn)
        return cfghash, config, stl_urls
    finally:
        if store_in_s3:
            try:
                shutil.rmtree(run_dir, ignore_errors=True)
            except Exception:
                pass


class ApiPreviewHandler(tornado.web.RequestHandler):
    '''POST /api/preview - sync preview from JSON config; STLs in temp, no S3. 10s timeout.'''
    def set_default_headers(self):
        set_def_headers(self)

    async def post(self):
        try:
            config_dict = json.loads(self.request.body or b'{}')
        except json.JSONDecodeError:
            self.set_status(400)
            self.write(json.dumps({"error": "Invalid JSON"}))
            return
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: _run_sync_preview_or_render(config_dict, preview_quality=True, store_in_s3=False),
                ),
                timeout=PREVIEW_TIMEOUT_SEC,
            )
        except asyncio.TimeoutError:
            self.set_status(504)
            self.write(json.dumps({"error": "Preview timed out (max %s s)" % PREVIEW_TIMEOUT_SEC}))
            return
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print("Preview failed: %s\n%s" % (e, tb))
            self.set_status(500)
            err_msg = str(e)
            self.write(json.dumps({"error": err_msg, "detail": tb}))
            return
        cfghash, config, stl_urls = result
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({
            "cfghash": cfghash,
            "config": dict(config),
            "stl_urls": stl_urls,
        }))


class ApiRenderHandler(tornado.web.RequestHandler):
    '''POST /api/render - sync full-quality render from JSON config; store STLs in S3. 10s timeout.'''
    def set_default_headers(self):
        set_def_headers(self)

    async def post(self):
        try:
            config_dict = json.loads(self.request.body or b'{}')
        except json.JSONDecodeError:
            self.set_status(400)
            self.write(json.dumps({"error": "Invalid JSON"}))
            return
        # Ensure config exists in S3 for later load
        config, cfgbytes, cfghash = package_config_json(config_dict)
        existing = FingerServer().get("configs/%s" % cfghash, load=True)
        if not existing:
            FingerServer().put("configs/%s" % cfghash, cfgbytes)
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: _run_sync_preview_or_render(config_dict, preview_quality=False, store_in_s3=True),
                ),
                timeout=PREVIEW_TIMEOUT_SEC,
            )
        except asyncio.TimeoutError:
            self.set_status(504)
            self.write(json.dumps({"error": "Render timed out (max %s s)" % PREVIEW_TIMEOUT_SEC}))
            return
        except Exception as e:
            print("Render failed: %s" % e)
            self.set_status(500)
            self.write(json.dumps({"error": str(e)}))
            return
        cfghash, config, stl_urls = result
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({
            "cfghash": cfghash,
            "config": dict(config),
            "stl_urls": stl_urls,
        }))


class ApiPreviewTempHandler(tornado.web.RequestHandler):
    '''GET /api/preview/temp/(run_id)/(filename) - serve temp preview STL from disk'''
    def set_default_headers(self):
        set_def_headers(self)

    def get(self, run_id, filename):
        if ".." in run_id or ".." in filename or "/" in filename:
            self.set_status(400)
            return
        path = os.path.join(PREVIEW_TEMP_DIR, run_id, filename)
        if not os.path.isfile(path):
            self.set_status(404)
            return
        self.set_header("Content-Type", "application/octet-stream")
        with open(path, 'rb') as f:
            self.write(f.read())


parts = [FingerPart.TIP, FingerPart.BASE, FingerPart.LINKAGE, FingerPart.MIDDLE, FingerPart.TIPCOVER, FingerPart.SOCKET, FingerPart.PLUG, FingerPart.STAND, FingerPart.PINS]

handlers = [
        (r"/api/parts", ApiPartsHandler),
        (r"/api/preview", ApiPreviewHandler),
        (r"/api/render", ApiRenderHandler),
        (r"/api/preview/temp/([a-zA-Z0-9\-]+)/([a-zA-Z0-9_.]+)", ApiPreviewTempHandler),
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
        (r"/render/(.+)", FingerHandler),  # e.g. /render/cfghash/tip.stl for sync render
        (r"/preview/(.+)", FingerHandler),
        (r"/downloads/([a-zA-Z0-9.]+)", FingerHandler),
        #fallback serves static files, include ones to supply preview page
        (r"/(.*)", StaticHandler, {"path": "./web/", "default_filename": "index.html"})
    ]

class FingerServer(Borg):
    '''server to handle s3 actions including queing of preview and render, and dequeue / processing of stl'''
    preview_poll = Prop(val=10, minv=0, maxv=120, doc='''  ''', hidden=True)
    render_poll = Prop(val=30, minv=0, maxv=120, doc='''  ''', hidden=True)
    http_port = Prop(val=8081, minv=80, maxv=65500, doc='''  ''', hidden=True)
    s3_bucket = Prop(val='danger-finger', doc='''  ''', hidden=True)
    aws_id = Prop(val="", doc=''' ''', hidden=True)
    aws_key = Prop(val="", doc=''' ''', hidden=True)
    s3session = None
    s3 = None
    bucket = None
    lock = {}

    def __init__(self):#, **kw):
        Borg.__init__(self)

    def setup(self):
        '''setup the server - do this once to get a session'''
        self.s3session = boto3.Session(aws_access_key_id=self.aws_id, aws_secret_access_key=self.aws_key)
        self.s3 = self.s3session.resource('s3')
        self.bucket = self.s3.Bucket(self.s3_bucket)

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
                print("Wanring, missing scad")
                scadbytes = compile_scad(pn, cfghash)
                created = True

            s3key = path + "/" + model["scadhash"]
            found = False
            for obj in self.dir(s3key):
                found = True
                print("Found file: %s" % obj.key)
                if obj.key.endswith(".stl") and model.get(path + "key", "") != obj.key:
                    model[path + "key"] = obj.key
                    created = True
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

    def put(self, key, obj, compress=True):
        '''put an object to s3'''
        b = obj if isinstance(obj, bytes) else json.dumps(obj, skipkeys=True).encode('utf-8') #, cls=EnumEncoder
        try:
            d = b'42' + brotli.compress(b) if compress else b
            self.s3.Object(self.s3_bucket, key).put(Body=d)
            print("Created object %s, %sb %s " % (key, len(b), "(%sb comp)"%len(d) if compress else ""))
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
            if b.startswith(b'42'):
                b = brotli.decompress(b[2:])
            return json.loads(b) if load else b
        except Exception as e:
            print("Object %s not found:: %s" % (key, e))
        return None

    def process_scad_loop(self, path, timeout):
        '''process a scad file in a loop'''
        if not path in self.lock: self.lock[path] = False
        time.sleep(timeout)
        while True:
            if self.lock[path]:
                time.sleep(timeout)
                continue
            try:
                for obj in FingerServer().dir(path):
                    try:
                        if obj.key.find(".mod") == -1: continue
                        #start processing
                        self.lock[path] = True
                        print("Processing: %s" % obj.key)
                        scad_file = "output/" + obj.key.replace(path, "")
                        stl_file = scad_file + ".stl"
                        stl_key = obj.key.replace(".mod", ".stl")
                        pkey = path.rstrip('/')
                        #get the model
                        model = FingerServer().get(obj.key, load=True)
                        model[pkey + "starttime"] = time.time()
                        #create the scad, insert a custom quality header (defrags cache)
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
            except Exception as e:
                print("Error listing %s: %s" % (path, e))
            if self.lock[path]:
                print("Completed process loop~")
                self.lock[path] = False
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

# Utility lambdas
check_null = lambda obj: all(obj[i] is not None for i in obj)
get_key = lambda cfg, v, pn: "%s_%s_%s" % (cfg, v, pn)
process_post = lambda args: {k: v[0].decode('utf-8') for (k, v) in args.items()}


def _resolve_cfghash(profile_config_entry):
    '''Profile configs can be cfghash (str) or { cfghash, history } (dict). Return current cfghash.'''
    if profile_config_entry is None:
        return None
    if isinstance(profile_config_entry, str):
        return profile_config_entry
    return profile_config_entry.get("cfghash")


def _config_entry_with_history(previous_entry, new_cfghash):
    '''Build configs[name] value: { cfghash, history }. Preserve previous in history.'''
    history = []
    if previous_entry is not None:
        prev_hash = _resolve_cfghash(previous_entry)
        if prev_hash and prev_hash != new_cfghash:
            history = [{"cfghash": prev_hash, "at": time.time()}]
        if isinstance(previous_entry, dict) and previous_entry.get("history"):
            history = (previous_entry["history"][-9:]) + history  # keep last 10
    return {"cfghash": new_cfghash, "history": history}

def create_model(pn, v, cfghash):
    '''create a new model and scad'''
    pkey = get_key(cfghash, v, pn)
    modkey = "models/%s" % pkey + ".mod"
    scadbytes, scadhash = compile_scad(pn, cfghash)
    scadkey = "scad/%s" % scadhash + ".scad"
    return {"cfghash": cfghash, "version": v, "part" : pn, "createdtime" : time.time(), "scadkey" : scadkey, "scadhash" : scadhash, "modkey" : modkey}, scadbytes

def compile_scad(pn, cfghash):
    '''pull a config and properly create the scad'''
    config = FingerServer().get("configs/" + cfghash, load=True)
    scadbytes = build(pn, config).encode('utf-8')
    hsh = sha256(scadbytes).hexdigest()
    return scadbytes, hsh

def create_zip(files):
    '''create a big ol zip file'''
    with BytesIO() as bf:
        with zipfile.ZipFile(bf, "w") as zf:
            for (f, b) in files.items():
                zf.writestr(f, b)
            return bf.getvalue()

def read_file(filename):
    '''serve a file from disk to client'''
    with open(filename, 'rb') as file_h:
        print("serving %s" % filename)
        return file_h.read()

def remove_defaults(config):
    '''ensure defaults are not cluttering the config'''
    params = DangerFinger().params
    if callable(params):
        params = params()
    # params can be dict of name -> value or name -> {Value, ...}
    for k in params:
        pv = params[k] if not isinstance(params[k], dict) else params[k].get("Value", params[k])
        if k in config and float(pv) == float(config[k]):
            config.pop(k)

def package_config_json(obj):
    '''process a config file to sort it'''
    remove_defaults(obj)
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
    Scad_Renderer().scad_to_stl(scad_file, stl_file)#), trialrun=True)
    print("  Rendered %s in %s sec" % (stl_file, round(time.time()-start, 1)))
    return stl_file

# Convert config values to floats
floatify = lambda config: {k: float(v) for k, v in config.items()}

def build(p, config, q=RenderQuality.NONE):
    '''build a finger model and return scad'''
    print("Building finger")
    finger = DangerFinger()
    config = floatify(config)
    Params.apply_config(finger, config)
    finger.render_quality = q  #     INSANE = 2 ULTRAHIGH = 5 HIGH = 10 EXTRAMEDIUM = 13 MEDIUM = 15 SUBMEDIUM = 17 FAST = 20 ULTRAFAST = 25 STUPIDFAST = 30
    finger.build()
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
        #debug=tornado.options.options.debug,
        compress_response=True
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

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(a)
    loop.run_forever()
