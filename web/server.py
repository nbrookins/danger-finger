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
import traceback
from threading import Event, Lock, Thread
from io import BytesIO
from collections import OrderedDict
from hashlib import sha256
import brotli
import tornado.options
import tornado.web
import boto3
from auth import validate_jwt, get_nicename

# Add parent directory to path so we can import danger module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from danger import *
#from danger.Borg import Borg
from danger.Params import Params
from danger.tools import *
from danger.Scad_Renderer import *

tornado.options.define('port', type=int, default=8081, help='server port number (default: 9000)')
tornado.options.define('debug', type=bool, default=False, help='run in debug mode with autoreload (default: False)')

# Origins allowed for CORS. When configured, only these origins receive
# Access-Control-Allow-Origin. Defaults to '*' for local dev.
WP_AUTH_URL = os.environ.get("wp_auth_url", "").rstrip("/")
APP_BASE_URL = os.environ.get("app_base_url", "").rstrip("/")
STATIC_SITE_URL = os.environ.get("static_site_url", "").rstrip("/")


def _normalize_origin(url: str) -> str:
    """Ensure origin has a protocol prefix so it matches browser Origin headers."""
    url = url.strip().rstrip("/")
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


_CORS_ALLOWED = set(filter(None, [_normalize_origin(u) for u in [WP_AUTH_URL, APP_BASE_URL, STATIC_SITE_URL]]))


def _cors_origin(request_origin: str) -> str:
    if not _CORS_ALLOWED:
        return "*"
    if request_origin and request_origin in _CORS_ALLOWED:
        return request_origin
    return next(iter(_CORS_ALLOWED))  # default to the first configured origin


def set_def_headers(self):
    '''Send CORS headers. Reflects exact requesting origin when it is in the allow-list.'''
    origin = self.request.headers.get("Origin", "")
    allowed = _cors_origin(origin)
    self.set_header("Access-Control-Allow-Origin", allowed)
    if allowed != "*":
        self.set_header("Vary", "Origin")
    self.set_header("Access-Control-Allow-Headers",
                    "Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With")
    self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")


class CorsMixin:
    """Respond 204 to CORS preflight OPTIONS requests so browsers allow cross-origin POSTs."""
    def options(self, *args, **kwargs):
        self.set_default_headers()
        self.set_status(204)
        self.finish()


class WpAuthMixin:
    """Mixin for Tornado handlers that require or optionally use a valid WordPress JWT."""

    def _payload_from_header(self, strict=False):
        auth_header = self.request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            if strict:
                self._auth_error("Bearer token required")
            return None
        token = auth_header[7:].strip()
        payload = validate_jwt(token)
        if payload is None and strict:
            self._auth_error("Invalid or expired token")
        return payload

    def require_auth(self):
        """Validate Bearer JWT. Returns user_nicename str or None (with 401 written)."""
        payload = self._payload_from_header(strict=True)
        if payload is None:
            return None
        return get_nicename(payload)

    def optional_auth(self):
        payload = self._payload_from_header(strict=False)
        if payload is None:
            return None
        return get_nicename(payload)

    def _auth_error(self, msg: str):
        self.set_status(401)
        self.set_header("Content-Type", "application/json")
        wp_login = WP_AUTH_URL or "https://dangercreations.com"
        self.write(json.dumps({
            "error": msg,
            "auth_required": True,
            "wp_auth_url": wp_login,
        }))

class IndexHandler(tornado.web.RequestHandler):
    '''Serve index.html with build-ID-stamped script URLs to bust browser caches on every restart.'''
    def set_default_headers(self):
        set_def_headers(self)

    def get(self):
        html_path = os.path.join(os.path.dirname(__file__), "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        import re
        html = re.sub(r'\?v=[^"\']*', f'?v={_BUILD_ID}', html)
        read_url = os.environ.get("READ_URL", "")
        if read_url:
            inject = f'<script>window.__READ_URL__="{read_url}";</script>'
            html = html.replace("</head>", f"{inject}</head>", 1)
        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.set_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.set_header("Pragma", "no-cache")
        self.write(html)


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
class FingerHandler(CorsMixin, WpAuthMixin, tornado.web.RequestHandler):
    ''' handle tornado requests for finger api'''

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
            auth_user = self.require_auth()
            if auth_user is None:
                return
            if auth_user != userhash:
                self.set_status(403)
                self.write(json.dumps({"error": "Cannot modify another user's profile"}))
                return
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
            auth_user = self.require_auth()
            if auth_user is None:
                return
            if auth_user != userhash:
                self.set_status(403)
                self.write(json.dumps({"error": "Cannot write to another user's profile"}))
                return
            pkey = "profiles/%s" % userhash
            profile = FingerServer().get(pkey, load=True)
            if not profile:
                profile = {"userhash": userhash, "createdtime": time.time(), "configs": {}}
            if "configs" not in profile:
                profile["configs"] = {}

            if self.request.path.find("/config") > -1:
                if self.request.headers.get("Content-Type", "").startswith("application/json"):
                    try:
                        config_dict = json.loads(self.request.body or b'{}')
                    except json.JSONDecodeError:
                        self.set_status(400)
                        self.write(json.dumps({"error": "Invalid JSON"}))
                        return
                else:
                    config_dict = process_post(self.request.body_arguments)
                _config, cfgbytes, cfghash = package_config_json(config_dict)
                print("ConfigHash: %s" % cfghash)

                err = _ensure_config_exists(cfghash, cfgbytes)
                if err is not None:
                    self.set_status(503)
                    self.write(json.dumps({"error": str(err)}))
                    return

                prev_entry = profile["configs"].get(cfg)
                profile["configs"][cfg] = _config_entry_with_history(prev_entry, cfghash)
                profile["updatedtime"] = time.time()
                profile["lastconfig"] = cfg
                err = FingerServer().put("profiles/%s" % userhash, profile)
                if err is not None:
                    self.set_status(502)
                    self.write(json.dumps({"error": str(err)}))
                    return
                job = _find_active_job(self.application, cfghash)
                if job is not None:
                    job = _promote_job_if_needed(self.application, job, auth_user)
                print("Saved config to profile")
                self.set_header("Content-Type", "application/json")
                self.write(json.dumps({
                    "cfghash": cfghash,
                    "config_name": cfg,
                    "render_status": _load_render_status(cfghash) or _status_payload(cfghash, job),
                }))
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
        return datetime.datetime.now(datetime.timezone.utc).strftime("started %Y-%m-%d %H:%M")

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
                "hingePivots": finger.compute_hinge_pivots(),
            }
        cached = _position_cache[cache_key]
        positions = cached["positions"]
        plug_instances = cached["plugInstances"]
        hinge_pivots = cached["hingePivots"]
    else:
        positions = P._preview_position_offsets
        plug_instances = P._preview_plug_instances
        hinge_pivots = P._preview_hinge_pivots

    return {
        "rotateOffsets": {k: list(v) for k, v in P._preview_rotate_offsets.items()},
        "positionOffsets": {k: list(v) for k, v in positions.items()},
        "plugInstances": [{"position": list(p["position"]), "rotation": list(p["rotation"])} for p in plug_instances],
        "explodeOffsets": {k: list(v) for k, v in P._preview_explode_offsets.items()},
        "partColors": {k: v for k, v in PART_COLORS.items()},
        "hingePivots": {k: list(v) for k, v in hinge_pivots.items()},
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
            "wpAuthUrl": WP_AUTH_URL or "",
            "appBaseUrl": APP_BASE_URL or "",
            "staticSiteUrl": STATIC_SITE_URL or "",
            "configurePageUrl": (WP_AUTH_URL + "/prosthetics/configure/") if WP_AUTH_URL else "",
        }))


PREVIEW_TIMEOUT_SEC = 10
PREVIEW_TEMP_DIR = "output/preview_temp"
JOB_PREFIX = "jobs/"
JOB_HEARTBEAT_SEC = 5
PRIORITY_AUTHENTICATED = 10
PRIORITY_GUEST = 20
QUEUE_AGING_SEC = 300
QUEUE_AGING_STEP = 5
GUEST_RATE_LIMIT_COUNT = 3
GUEST_RATE_LIMIT_WINDOW_SEC = 15 * 60
PRIORITY_PREVIEW = -10
PREVIEW_RESULT_TTL_SEC = 600

_app_ref = None


def _run_sync_preview_or_render(config_dict, preview_quality=True, store_in_s3=False, heartbeat_cb=None):
    '''
    Run OpenSCAD for all parts synchronously.
    Returns (cfghash, config, stl_urls, scad_urls).
    stl_urls/scad_urls map part names to /api/preview/temp/{run_id}/{part}.{ext}.
    For render with store_in_s3: builds a bundle.zip and uploads once.
    '''
    config, cfgbytes, cfghash = package_config_json(config_dict)
    quality = RenderQuality.EXTRAMEDIUM if preview_quality else RenderQuality.HIGH
    os.makedirs(PREVIEW_TEMP_DIR, exist_ok=True)
    run_id = str(uuid.uuid4())[:12]
    run_dir = os.path.join(PREVIEW_TEMP_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)
    stl_urls = {}
    scad_urls = {}

    if heartbeat_cb is not None:
        heartbeat_cb("building")
    all_scad = build_all(dict(config), quality)

    for pn in [str(p.name).lower() for p in parts]:
        if heartbeat_cb is not None:
            heartbeat_cb(pn)
        scad_str = all_scad.get(pn)
        if scad_str is None:
            print("  Skipping %s (no geometry from build)" % pn)
            continue
        scad_out = os.path.join(run_dir, pn + ".scad")
        stl_out = os.path.join(run_dir, pn + ".stl")
        try:
            write_file(scad_str.encode('utf-8'), scad_out)
            write_stl(scad_out, stl_out)
            if os.path.isfile(stl_out) and os.path.getsize(stl_out) > 0:
                stl_urls[pn] = "/api/preview/temp/%s/%s.stl" % (run_id, pn)
                scad_urls[pn] = "/api/preview/temp/%s/%s.scad" % (run_id, pn)
            else:
                print("  WARNING: %s.stl empty or missing after OpenSCAD" % pn)
        except Exception as e:
            print("  ERROR rendering %s: %s" % (pn, e))

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
                    zip_files["scad/" + pn + ".scad"] = f.read()
        zip_files["config.json"] = json.dumps(dict(config), indent=2)
        zip_files["LICENSE"] = read_file("LICENSE")
        zip_files["README.md"] = read_file("README.md")
        bundle = create_zip(zip_files)
        bundle_key = _bundle_key(cfghash)
        FingerServer().put(bundle_key, bundle, compress=False)
        stl_urls["bundle"] = "/" + bundle_key
    return cfghash, config, stl_urls, scad_urls


class ApiPreviewHandler(CorsMixin, tornado.web.RequestHandler):
    '''POST /api/preview - enqueue a render job and return 202 with job_id.
    Accepts optional "quality" field: "default" (EXTRAMEDIUM) or "high" (HIGH).
    Both save to S3; high produces a downloadable bundle.'''
    def set_default_headers(self):
        set_def_headers(self)

    async def post(self):
        try:
            body = json.loads(self.request.body or b'{}')
        except json.JSONDecodeError:
            self.set_status(400)
            self.write(json.dumps({"error": "Invalid JSON"}))
            return
        quality = body.pop("quality", "default")
        high_quality = (quality == "high")

        _config, _cfgbytes, cfghash = package_config_json(dict(body))
        cached = _find_cached_preview(self.application, cfghash)
        if cached and not high_quality:
            print("Preview cache hit for cfghash=%s" % cfghash[:8])
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(cached))
            return

        warnings = []
        try:
            from danger.finger import DangerFinger
            from danger.Params import Params
            check = DangerFinger()
            Params.apply_config(check, dict(body))
            warnings = check.validate_params()
            if warnings:
                print(f"Preview param warnings: {warnings}")
        except Exception as e:
            print(f"Preview validation error (non-fatal): {e}")
        job = _create_preview_job(body, high_quality=high_quality)
        job["cfghash"] = cfghash
        _queue_job(self.application, job)
        self.set_status(202)
        self.set_header("Content-Type", "application/json")
        resp = {"job_id": job["job_id"], "status": "queued", "quality": quality}
        if warnings:
            resp["warnings"] = warnings
        self.write(json.dumps(resp))


class ApiRenderHandler(CorsMixin, WpAuthMixin, tornado.web.RequestHandler):
    '''POST /api/render - enqueue a full-quality render and return durable job status.'''
    def set_default_headers(self):
        set_def_headers(self)

    async def post(self):
        try:
            config_dict = json.loads(self.request.body or b'{}')
        except json.JSONDecodeError:
            self.set_status(400)
            self.write(json.dumps({"error": "Invalid JSON"}))
            return

        auth_user = self.optional_auth()
        if auth_user is None:
            retry_after = _check_guest_rate_limit(self.application, _request_ip(self.request))
            if retry_after is not None:
                self.set_status(429)
                self.write(json.dumps({
                    "error": "Too many anonymous render requests. Please wait a few minutes or log in.",
                    "retry_after_sec": retry_after,
                }))
                return

        config, cfgbytes, cfghash = package_config_json(dict(config_dict))
        err = _ensure_config_exists(cfghash, cfgbytes)
        if err is not None:
            self.set_status(503)
            self.write(json.dumps({"error": str(err)}))
            return

        if _bundle_exists(cfghash):
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(_status_payload(cfghash)))
            return

        job = _find_active_job(self.application, cfghash)
        if job is not None:
            job = _promote_job_if_needed(self.application, job, auth_user)
        else:
            job = _create_render_job(config, cfghash, requested_by=auth_user)
            _persist_job(job)
            _queue_job(self.application, job)

        self.set_status(202)
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(_job_response(job)))


class RenderStatusHandler(tornado.web.RequestHandler):
    'GET /render/{cfghash}/status - return durable render status.'
    def set_default_headers(self):
        set_def_headers(self)

    def get(self, cfghash):
        payload = _load_render_status(cfghash)
        if payload is None:
            self.set_status(404)
            self.write(json.dumps({"error": "Not found"}))
            return
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(payload))


class JobStatusHandler(tornado.web.RequestHandler):
    'GET /jobs/{job_id} - return durable job state; preview results served from memory.'
    def set_default_headers(self):
        set_def_headers(self)

    def get(self, job_id):
        with self.application.queue_lock:
            preview_result = self.application.preview_results.get(job_id)
        if preview_result is not None:
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({
                "job_id": job_id,
                "status": "complete",
                "result": preview_result,
            }))
            return

        job = _load_job(job_id)
        if job is None:
            self.set_status(404)
            self.write(json.dumps({"error": "Not found"}))
            return

        if job.get("job_type") == "preview":
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({
                "job_id": job_id,
                "status": job.get("status", "queued"),
                "queue_position": job.get("queue_position"),
                "error": job.get("error"),
            }))
            return

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(_job_response(job)))


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


parts = [FingerPart.TIP, FingerPart.BASE, FingerPart.LINKAGE, FingerPart.MIDDLE, FingerPart.TIPCOVER, FingerPart.SOCKET, FingerPart.PLUG, FingerPart.STAND, FingerPart.BUMPER]

handlers = [
        (r"/api/parts", ApiPartsHandler),
        (r"/api/preview", ApiPreviewHandler),
        (r"/api/render", ApiRenderHandler),
        (r"/api/preview/temp/([a-zA-Z0-9\-]+)/([a-zA-Z0-9_.]+)", ApiPreviewTempHandler),
        (r"/api/jobs/([a-zA-Z0-9\-]+)", JobStatusHandler),
        (r"/render/([a-fA-F0-9]+)/status", RenderStatusHandler),
        (r"/params(/?\w*)", FingerHandler),
        (r"/profile/([a-zA-Z0-9.]+)/config/([a-zA-Z0-9.]+)", FingerHandler),
        # S3 read fallback (primary reads go through Lambda)
        (r"/profiles/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/configs/([a-zA-Z0-9.]+)", FingerHandler),
        (r"/render/(.+)", FingerHandler),
        # index.html served via IndexHandler to inject build-ID cache-busting into script URLs
        (r"/(?:index\.html)?$", IndexHandler),
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
        '''Setup S3 session. Uses explicit keys if provided (local dev), otherwise falls back
        to the default credential chain (IAM instance profile on EC2, env vars, ~/.aws/credentials).'''
        if self.aws_id and self.aws_key:
            self.s3session = boto3.Session(aws_access_key_id=self.aws_id, aws_secret_access_key=self.aws_key)
        else:
            self.s3session = boto3.Session()
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

    def exists(self, key):
        try:
            self.s3.Object(self.s3_bucket, key).load()
            return True
        except Exception:
            return False

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


def _bundle_key(cfghash):
    return "render/%s/bundle.zip" % cfghash


def _job_key(job_id):
    return JOB_PREFIX + job_id


def _render_status_key(cfghash):
    return "render/%s/status" % cfghash


def _bundle_exists(cfghash):
    return FingerServer().exists(_bundle_key(cfghash))


def _ensure_config_exists(cfghash, cfgbytes):
    key = "configs/%s" % cfghash
    if FingerServer().exists(key):
        return None
    return FingerServer().put(key, cfgbytes)


def _request_ip(request):
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_ip or "unknown"


def _check_guest_rate_limit(application, ip_addr):
    now = time.time()
    with application.queue_lock:
        hits = [ts for ts in application.guest_render_hits.get(ip_addr, []) if now - ts < GUEST_RATE_LIMIT_WINDOW_SEC]
        if len(hits) >= GUEST_RATE_LIMIT_COUNT:
            application.guest_render_hits[ip_addr] = hits
            return max(1, int(GUEST_RATE_LIMIT_WINDOW_SEC - (now - hits[0])))
        hits.append(now)
        application.guest_render_hits[ip_addr] = hits
    return None


def _job_priority(auth_user):
    return PRIORITY_AUTHENTICATED if auth_user else PRIORITY_GUEST


def _job_auth_tier(auth_user):
    return "authenticated" if auth_user else "guest"


def _status_message(job):
    status = job.get("status")
    if status == "complete":
        return "Ready to download"
    if status == "failed":
        return "Render failed"
    if status == "running":
        return "Recovered after restart" if job.get("retrying_after_restart") else "Rendering now"
    if status == "queued":
        if job.get("retrying_after_restart"):
            return "Recovered after restart"
        return "Queued behind signed-in users" if job.get("auth_tier") == "guest" else "Queued"
    return "Not rendered yet"


def _status_payload(cfghash, job=None):
    bundle_ready = _bundle_exists(cfghash)
    payload = {
        "cfghash": cfghash,
        "bundle_url": "/" + _bundle_key(cfghash) if bundle_ready else None,
        "status": "complete" if bundle_ready else "not_rendered",
        "status_message": "Ready to download" if bundle_ready else "Not rendered yet",
        "auth_tier": None,
        "job_id": None,
        "queue_position": None,
        "retrying_after_restart": False,
        "error": None,
    }
    if job is not None:
        payload.update({
            "job_id": job.get("job_id"),
            "auth_tier": job.get("auth_tier"),
            "queue_position": job.get("queue_position"),
            "retrying_after_restart": bool(job.get("retrying_after_restart")),
            "error": job.get("error"),
        })
        if not bundle_ready:
            payload["status"] = job.get("status", "not_rendered")
        payload["status_message"] = _status_message(job)
    return payload


def _job_response(job):
    return {
        "job_id": job.get("job_id"),
        "cfghash": job.get("cfghash"),
        "status": job.get("status"),
        "auth_tier": job.get("auth_tier"),
        "queue_position": job.get("queue_position"),
        "requested_by": job.get("requested_by"),
        "bundle_url": "/" + _bundle_key(job["cfghash"]) if _bundle_exists(job["cfghash"]) else None,
        "status_message": _status_message(job),
        "retrying_after_restart": bool(job.get("retrying_after_restart")),
        "error": job.get("error"),
    }


def _persist_job(job):
    if _app_ref is not None:
        with _app_ref.queue_lock:
            _app_ref.in_memory_jobs[job["job_id"]] = dict(job)
    if job.get("job_type") == "preview":
        return
    err = FingerServer().put(_job_key(job["job_id"]), job)
    if err is not None:
        raise RuntimeError(str(err))


def _load_job(job_id):
    if _app_ref is not None:
        with _app_ref.queue_lock:
            mem_job = _app_ref.in_memory_jobs.get(job_id)
        if mem_job is not None:
            return mem_job
    return FingerServer().get(_job_key(job_id), load=True)


def _write_render_status(job):
    if job.get("job_type") == "preview":
        return
    FingerServer().put(_render_status_key(job["cfghash"]), _status_payload(job["cfghash"], job))


def _load_render_status(cfghash):
    payload = FingerServer().get(_render_status_key(cfghash), load=True)
    if payload is not None:
        if payload.get("status") != "complete" and _bundle_exists(cfghash):
            return _status_payload(cfghash)
        return payload
    if _bundle_exists(cfghash):
        return _status_payload(cfghash)
    return None


def _create_render_job(config, cfghash, requested_by=None):
    now = time.time()
    return {
        "job_id": str(uuid.uuid4()),
        "cfghash": cfghash,
        "config": dict(config),
        "requested_by": requested_by,
        "auth_tier": _job_auth_tier(requested_by),
        "priority_rank": _job_priority(requested_by),
        "status": "queued",
        "created_at": now,
        "started_at": None,
        "finished_at": None,
        "last_heartbeat": now,
        "queue_position": None,
        "retrying_after_restart": False,
        "recovery_count": 0,
        "error": None,
        "current_part": None,
    }


def _create_preview_job(config_dict, high_quality=False):
    now = time.time()
    return {
        "job_id": str(uuid.uuid4()),
        "job_type": "preview",
        "high_quality": high_quality,
        "cfghash": None,
        "config": dict(config_dict),
        "requested_by": None,
        "auth_tier": None,
        "priority_rank": PRIORITY_PREVIEW,
        "status": "queued",
        "created_at": now,
        "started_at": None,
        "finished_at": None,
        "last_heartbeat": now,
        "queue_position": None,
        "retrying_after_restart": False,
        "recovery_count": 0,
        "error": None,
        "current_part": None,
    }


def _prune_stale_previews(application):
    now = time.time()
    with application.queue_lock:
        stale_results = [jid for jid, res in application.preview_results.items()
                         if now - res.get("completed_at", 0) > PREVIEW_RESULT_TTL_SEC]
        for jid in stale_results:
            res = application.preview_results.pop(jid, None)
            if res and hasattr(application, 'preview_by_cfghash'):
                ch = res.get("cfghash")
                if ch and application.preview_by_cfghash.get(ch) == jid:
                    del application.preview_by_cfghash[ch]
        stale_jobs = [jid for jid, job in application.in_memory_jobs.items()
                      if job.get("job_type") == "preview"
                      and job.get("status") in ("complete", "failed")
                      and now - job.get("finished_at", job.get("created_at", 0)) > PREVIEW_RESULT_TTL_SEC]
        for jid in stale_jobs:
            del application.in_memory_jobs[jid]


def _find_cached_preview(application, cfghash):
    """Return a cached preview result dict if one exists with valid temp files on disk."""
    if not cfghash:
        return None
    with application.queue_lock:
        jid = application.preview_by_cfghash.get(cfghash)
        if not jid:
            return None
        cached = application.preview_results.get(jid)
        if not cached:
            return None
    stl_urls = cached.get("stl_urls", {})
    for pn, url in stl_urls.items():
        if pn == "bundle":
            continue
        if "/api/preview/temp/" in url:
            parts = url.split("/api/preview/temp/")[1]
            disk_path = os.path.join(PREVIEW_TEMP_DIR, parts)
            if not os.path.isfile(disk_path):
                return None
    return cached


def _find_active_job(application, cfghash):
    with application.queue_lock:
        job_id = application.active_jobs.get(cfghash)
    if not job_id:
        return None
    job = _load_job(job_id)
    if job is None or job.get("status") in ("complete", "failed"):
        with application.queue_lock:
            if application.active_jobs.get(cfghash) == job_id:
                application.active_jobs.pop(cfghash, None)
            if job_id in application.pending_job_ids:
                application.pending_job_ids.remove(job_id)
        return None
    return job


def _promote_job_if_needed(application, job, auth_user):
    if auth_user and job.get("auth_tier") != "authenticated":
        job["auth_tier"] = "authenticated"
        job["priority_rank"] = PRIORITY_AUTHENTICATED
        job["requested_by"] = auth_user
        if job.get("status") == "queued":
            _queue_job(application, job)
        else:
            _persist_job(job)
            _write_render_status(job)
    return job


def _effective_priority(job, now):
    rank = job.get("priority_rank", PRIORITY_GUEST)
    if job.get("auth_tier") == "guest":
        promotions = int(max(0, now - job.get("created_at", now)) // QUEUE_AGING_SEC)
        rank = max(PRIORITY_AUTHENTICATED, rank - (promotions * QUEUE_AGING_STEP))
    return rank


def _queued_jobs(application):
    with application.queue_lock:
        job_ids = list(application.pending_job_ids)
    jobs = []
    seen = set()
    for job_id in job_ids:
        if job_id in seen:
            continue
        seen.add(job_id)
        job = _load_job(job_id)
        if job and job.get("status") == "queued":
            jobs.append(job)
    return jobs


def _refresh_queue_positions(application):
    jobs = _queued_jobs(application)
    now = time.time()
    jobs.sort(key=lambda job: (_effective_priority(job, now), job.get("created_at", now), job.get("job_id")))
    with application.queue_lock:
        application.pending_job_ids = [job["job_id"] for job in jobs]
    for idx, job in enumerate(jobs, start=1):
        if job.get("queue_position") != idx:
            job["queue_position"] = idx
            _persist_job(job)
            _write_render_status(job)


def _queue_job(application, job):
    job["status"] = "queued"
    job["error"] = None
    job["last_heartbeat"] = time.time()
    with application.queue_lock:
        if job["job_id"] not in application.pending_job_ids:
            application.pending_job_ids.append(job["job_id"])
        if job.get("job_type") != "preview" and job.get("cfghash"):
            application.active_jobs[job["cfghash"]] = job["job_id"]
    _persist_job(job)
    _write_render_status(job)
    _refresh_queue_positions(application)
    application.queue_event.set()


def _dequeue_next_job(application):
    jobs = _queued_jobs(application)
    if not jobs:
        with application.queue_lock:
            application.pending_job_ids = []
        return None
    now = time.time()
    jobs.sort(key=lambda job: (_effective_priority(job, now), job.get("created_at", now), job.get("job_id")))
    job = jobs[0]
    with application.queue_lock:
        if job["job_id"] in application.pending_job_ids:
            application.pending_job_ids.remove(job["job_id"])
    _refresh_queue_positions(application)
    return job


def _mark_job_complete(application, job):
    job["status"] = "complete"
    job["finished_at"] = time.time()
    job["last_heartbeat"] = job["finished_at"]
    job["queue_position"] = None
    job["retrying_after_restart"] = False
    _persist_job(job)
    _write_render_status(job)
    if job.get("job_type") != "preview" and job.get("cfghash"):
        with application.queue_lock:
            if application.active_jobs.get(job["cfghash"]) == job["job_id"]:
                application.active_jobs.pop(job["cfghash"], None)


def _mark_job_failed(application, job, exc):
    job["status"] = "failed"
    job["finished_at"] = time.time()
    job["last_heartbeat"] = job["finished_at"]
    job["queue_position"] = None
    job["error"] = str(exc)
    try:
        _persist_job(job)
    except Exception as persist_exc:
        print("Secondary S3 failure in _mark_job_failed: %s" % persist_exc)
    _write_render_status(job)
    if job.get("job_type") != "preview" and job.get("cfghash"):
        with application.queue_lock:
            if application.active_jobs.get(job["cfghash"]) == job["job_id"]:
                application.active_jobs.pop(job["cfghash"], None)


def _recover_jobs(application):
    recovered_any = False
    try:
        objs = list(FingerServer().dir(JOB_PREFIX))
    except Exception as exc:
        print("Job recovery skipped: %s" % exc)
        return
    for obj in objs:
        try:
            job = FingerServer().get(obj.key, load=True)
            if not job:
                continue
            if _bundle_exists(job["cfghash"]):
                if job.get("status") != "complete":
                    job["status"] = "complete"
                    job["finished_at"] = time.time()
                    job["queue_position"] = None
                    _persist_job(job)
                    _write_render_status(job)
                continue
            if job.get("status") not in ("queued", "running"):
                continue
            job["status"] = "queued"
            job["retrying_after_restart"] = True
            job["recovery_count"] = int(job.get("recovery_count") or 0) + 1
            job["last_heartbeat"] = time.time()
            _queue_job(application, job)
            recovered_any = True
        except Exception as exc:
            print("Job recovery entry skipped: %s" % exc)
    if recovered_any:
        application.queue_event.set()

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

def build_all(config_dict, q=RenderQuality.NONE):
    '''Build the finger model once and return {part_name: scad_string} for all requested parts.'''
    print("Building finger (all parts)")
    finger = DangerFinger()
    config_dict = floatify(config_dict)
    Params.apply_config(finger, config_dict)
    finger.render_quality = q
    finger.build()
    result = {}
    for part_enum in parts:
        pn = str(part_enum.name).lower()
        for _fp, model in finger.models.items():
            found = False
            if hasattr(model, '__iter__') and not isinstance(model, str):
                for m in model:
                    if str(m.part) == pn:
                        scad = m.scad if isinstance(m.scad, str) else "\n".join(m.scad)
                        result[pn] = scad
                        found = True
                        break
            elif str(getattr(model, 'part', '')) == pn:
                result[pn] = model.scad if isinstance(model.scad, str) else "\n".join(model.scad)
                found = True
            if found:
                break
    return result


def _render_worker(application):
    while True:
      try:
        _prune_stale_previews(application)
        job = _dequeue_next_job(application)
        if job is None:
            application.queue_event.wait(1)
            application.queue_event.clear()
            continue

        is_preview = job.get("job_type") == "preview"

        if not is_preview and _bundle_exists(job["cfghash"]):
            _mark_job_complete(application, job)
            continue

        job["status"] = "running"
        if job.get("started_at") is None:
            job["started_at"] = time.time()
        job["last_heartbeat"] = time.time()
        job["queue_position"] = None
        _persist_job(job)
        _write_render_status(job)

        last_beat = {"at": 0}

        def heartbeat(part_name=None):
            now = time.time()
            if part_name is not None:
                job["current_part"] = part_name
            if part_name is None and now - last_beat["at"] < JOB_HEARTBEAT_SEC:
                return
            last_beat["at"] = now
            job["last_heartbeat"] = now
            _persist_job(job)
            _write_render_status(job)

        try:
            heartbeat()
            if is_preview:
                high_q = job.get("high_quality", False)
                use_preview_quality = not high_q
                cfghash, config, stl_urls, scad_urls = _run_sync_preview_or_render(
                    job["config"], preview_quality=use_preview_quality,
                    store_in_s3=high_q, heartbeat_cb=heartbeat)
                finger_check = DangerFinger()
                Params.apply_config(finger_check, dict(config))
                param_warnings = finger_check.validate_params()
                preview_cfg = _preview_config(dict(config))
                with application.queue_lock:
                    application.preview_results[job["job_id"]] = {
                        "cfghash": cfghash,
                        "config": dict(config),
                        "stl_urls": stl_urls,
                        "scad_urls": scad_urls,
                        "warnings": param_warnings,
                        "previewConfig": preview_cfg,
                        "quality": "high" if high_q else "default",
                        "completed_at": time.time(),
                    }
                    if hasattr(application, 'preview_by_cfghash'):
                        application.preview_by_cfghash[cfghash] = job["job_id"]
                job["cfghash"] = cfghash
                if high_q:
                    _write_render_status(job)
            else:
                _cfghash, _cfg, _stl, _scad = _run_sync_preview_or_render(
                    job["config"], preview_quality=False, store_in_s3=True, heartbeat_cb=heartbeat)
            _mark_job_complete(application, job)
        except Exception as exc:
            print("Job failed: %s\n%s" % (exc, traceback.format_exc()))
            _mark_job_failed(application, job, exc)
      except Exception as outer_exc:
        print("Render worker error (will retry): %s\n%s" % (outer_exc, traceback.format_exc()))
        time.sleep(2)


def _init_application_state(application):
    global _app_ref
    _app_ref = application
    application.queue_lock = Lock()
    application.queue_event = Event()
    application.pending_job_ids = []
    application.active_jobs = {}
    application.guest_render_hits = {}
    application.in_memory_jobs = {}
    application.preview_results = {}
    application.preview_by_cfghash = {}


def _start_render_worker(application):
    worker = Thread(target=_render_worker, args=(application,), daemon=True, name="danger-finger-render-worker")
    worker.start()
    application.render_worker = worker


async def make_app(fs):
    ''' create server async'''
    settings = dict(
        #debug=tornado.options.options.debug,
        compress_response=True
    )
    app = tornado.web.Application(handlers, **settings)
    app.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    app.counter = 0
    _init_application_state(app)
    _recover_jobs(app)
    _start_render_worker(app)
    app.listen(fs.http_port)
    return app

if __name__ == "__main__":
    sys.stdout = UnbufferedStdOut(sys.stdout)

    fs = FingerServer()
    Params.parse(fs)
    fs.setup()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(make_app(fs))
    loop.run_forever()
