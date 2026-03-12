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
    # File extensions that should never be browser-cached (source code changes between runs)
    _NO_CACHE_EXTS = {".js", ".html", ".css"}

    def set_default_headers(self):
        '''send default headers to ensure cors'''
        set_def_headers(self)

    def get_cache_time(self, path, modified, mime_type):
        '''Return 0 for source files so Tornado never sets long-lived cache headers or sends 304s.'''
        _, ext = os.path.splitext(path)
        if ext.lower() in self._NO_CACHE_EXTS:
            return 0
        return super().get_cache_time(path, modified, mime_type)

    def set_extra_headers(self, path):
        '''Disable browser caching for source files so code changes take effect on reload.'''
        _, ext = os.path.splitext(path)
        if ext.lower() in self._NO_CACHE_EXTS:
            self.set_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.set_header("Pragma", "no-cache")

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
        '''Handle a metadata request — S3 reads go through Lambda; this handles params and S3 proxy fallback'''
        print("  HTTP Request: %s %s %s" % (self.request, self.request.path, var))
        if self.request.path.startswith(("/configs", "/profiles", "/render")):
            b = FingerServer().get(self.request.path[1:], load=False)
            if b is None:
                self.set_status(404)
                return
            mime = 'application/json' if self.request.path.startswith(("/configs", "/profiles")) else 'application/octet-stream'
            self.serve_bytes(b, mime)
            return

        if self.request.path.startswith("/param"):
            params = DangerFinger().get_params(adv=var.startswith("/adv"), allv=var.startswith("/all"), extended=True)
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

    async def post(self, userhash, cfg):
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

                # Run render in executor so the IO loop is not blocked (matches ApiPreviewHandler/ApiRenderHandler).
                loop = asyncio.get_event_loop()
                try:
                    await asyncio.wait_for(
                        loop.run_in_executor(
                            getattr(self.application, "executor", None),
                            lambda: _run_sync_preview_or_render(
                                config_dict, preview_quality=False, store_in_s3=True
                            ),
                        ),
                        timeout=PREVIEW_TIMEOUT_SEC,
                    )
                except asyncio.TimeoutError:
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
                self.set_header("Content-Type", "application/json")
                self.write(json.dumps({"cfghash": cfghash, "config_name": cfg}))
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


_position_cache = {}

def _get_build_id():
    """Return a short build identifier: git short-hash + UTC date, e.g. 'a1b2c3d 2026-03-11'.
    Falls back to process start timestamp if git is unavailable."""
    import subprocess, datetime
    try:
        short = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ).decode().strip()
        date = subprocess.check_output(
            ["git", "log", "-1", "--format=%cd", "--date=short"],
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ).decode().strip()
        return f"{short} {date}"
    except Exception:
        return datetime.datetime.utcnow().strftime("started %Y-%m-%d %H:%M")

_BUILD_ID = _get_build_id()

def _preview_config(config_dict=None):
    """Build preview layout config from DangerFingerParams for the web viewer.
    If config_dict is provided, computes dynamic positions for that config (cached by cfghash)."""
    from danger.finger_params import DangerFingerParams as P
    from danger.finger import PART_COLORS

    if config_dict:
        cache_key = sha256(json.dumps(config_dict, sort_keys=True).encode()).hexdigest()[:16]
        if cache_key not in _position_cache:
            finger = DangerFinger()
            Params.apply_config(finger, config_dict)
            _position_cache[cache_key] = {
                "positions": finger.compute_preview_positions(),
                "plugInstances": finger.compute_preview_plug_instances(),
            }
        cached = _position_cache[cache_key]
        positions = cached["positions"]
        plug_instances = cached["plugInstances"]
    else:
        positions = P._preview_position_offsets
        plug_instances = P._preview_plug_instances

    return {
        "rotateOffsets": {k: list(v) for k, v in P._preview_rotate_offsets.items()},
        "positionOffsets": {k: list(v) for k, v in positions.items()},
        "plugInstances": [{"position": list(p["position"]), "rotation": list(p["rotation"])} for p in plug_instances],
        "explodeOffsets": {k: list(v) for k, v in P._preview_explode_offsets.items()},
        "partColors": {k: v for k, v in PART_COLORS.items()},
    }


class ApiPartsHandler(tornado.web.RequestHandler):
    '''GET /api/parts - list part ids and labels for viewer filter'''
    def set_default_headers(self):
        set_def_headers(self)

    def get(self):
        part_list = [{"id": str(p.name).lower(), "label": str(p.name).capitalize()} for p in parts]
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({
            "parts": part_list,
            "version": DangerFinger.VERSION,
            "build": _BUILD_ID,
            "previewConfig": _preview_config(),
        }))


PREVIEW_TIMEOUT_SEC = 10
PREVIEW_TEMP_DIR = "output/preview_temp"


def _run_sync_preview_or_render(config_dict, preview_quality=True, store_in_s3=False):
    '''
    Run OpenSCAD for all parts synchronously. Returns (cfghash, config, stl_urls_or_run_id).
    For preview: writes STLs to temp dir, returns run_id and stl_urls point at /api/preview/temp/{run_id}/{part}.stl.
    For render with store_in_s3: builds a bundle.zip (STL + SCAD + config + LICENSE + README) and uploads once.
    '''
    config, cfgbytes, cfghash = package_config_json(config_dict)
    quality = RenderQuality.EXTRAMEDIUM if preview_quality else RenderQuality.HIGH
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
            if not store_in_s3:
                stl_urls[pn] = "/api/preview/temp/%s/%s.stl" % (run_id, pn)
        if store_in_s3:
            zip_files = {}
            for p in parts:
                pn = str(p.name).lower()
                stl_path = os.path.join(run_dir, pn + ".stl")
                scad_path = os.path.join(run_dir, pn + ".scad")
                if os.path.isfile(stl_path):
                    with open(stl_path, 'rb') as f:
                        zip_files[pn + ".stl"] = f.read()
                if os.path.isfile(scad_path):
                    with open(scad_path, 'rb') as f:
                        zip_files[pn + ".scad"] = f.read()
            zip_files["config.json"] = json.dumps(dict(config), indent=2)
            zip_files["LICENSE"] = read_file("LICENSE")
            zip_files["README.md"] = read_file("README.md")
            bundle = create_zip(zip_files)
            bundle_key = "render/%s/bundle.zip" % cfghash
            FingerServer().put(bundle_key, bundle, compress=False)
            stl_urls["bundle"] = "/" + bundle_key
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
        finger_check = DangerFinger()
        Params.apply_config(finger_check, dict(config))
        param_warnings = finger_check.validate_params()
        preview_cfg = _preview_config(dict(config))
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({
            "cfghash": cfghash,
            "config": dict(config),
            "stl_urls": stl_urls,
            "warnings": param_warnings,
            "previewConfig": preview_cfg,
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
        (r"/params(/?\w*)", FingerHandler),
        (r"/profile/([a-zA-Z0-9.]+)/config/([a-zA-Z0-9.]+)", FingerHandler),
        # S3 read fallback (primary reads go through Lambda)
        (r"/profiles/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/configs/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/render/(.+)", FingerHandler),
        (r"/(.*)", StaticHandler, {"path": "./web/", "default_filename": "index.html"})
    ]

class FingerServer(Borg):
    '''server to handle s3 actions — writes configs/profiles/bundles; reads are fallback (Lambda is primary)'''
    http_port = Prop(val=8081, minv=80, maxv=65500, doc='''  ''', hidden=True)
    s3_bucket = Prop(val='danger-finger', doc='''  ''', hidden=True)
    aws_id = Prop(val="", doc=''' ''', hidden=True)
    aws_key = Prop(val="", doc=''' ''', hidden=True)
    s3session = None
    s3 = None
    bucket = None

    def __init__(self):#, **kw):
        Borg.__init__(self)

    def setup(self):
        '''setup the server - do this once to get a session'''
        self.s3session = boto3.Session(aws_access_key_id=self.aws_id, aws_secret_access_key=self.aws_key)
        self.s3 = self.s3session.resource('s3')
        self.bucket = self.s3.Bucket(self.s3_bucket)

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
        try:
            if k in config and float(pv) == float(config[k]):
                config.pop(k)
        except (TypeError, ValueError):
            if k in config and str(pv) == str(config[k]):
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
def floatify(config):
    """Convert numeric config values to float; leave strings/enums unchanged."""
    out = {}
    for k, v in config.items():
        try:
            out[k] = float(v)
        except (TypeError, ValueError):
            out[k] = v
    return out

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

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(a)
    loop.run_forever()
