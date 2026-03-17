#!/usr/bin/env python3
"""Generate pre-rendered STLs for the default parameter configuration.

These are deployed as static files so the web viewer can display the finger
instantly on first load without hitting the render server.

Run from project root:
  python3 scripts/generate_default_stls.py          # inside Docker (has OpenSCAD)
  make generate-default-stls                         # via Docker from host

Output: web/static/render/default/{part}.stl
"""
import json
import os
import sys
import subprocess
import time
import zipfile
from io import BytesIO

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from danger.finger import DangerFinger
from danger.finger_params import DangerFingerParams, FingerPart
from danger.Params import Params
from danger.constants import RenderQuality

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "web", "static", "defaults")

PARTS = [
    FingerPart.TIP, FingerPart.BASE, FingerPart.LINKAGE, FingerPart.MIDDLE,
    FingerPart.TIPCOVER, FingerPart.SOCKET, FingerPart.PLUG, FingerPart.BUMPER,
    FingerPart.STAND,
]


def build_scad(part_name, finger):
    """Build SCAD string for a single part using the configured finger."""
    for _fp, model in finger.models.items():
        if hasattr(model, '__iter__') and not isinstance(model, str):
            for m in model:
                if str(m.part) == part_name:
                    return m.scad if isinstance(m.scad, str) else "\n".join(m.scad)
        elif str(model.part) == part_name:
            return model.scad if isinstance(model.scad, str) else "\n".join(model.scad)
    return None


def _find_openscad():
    import shutil
    path = shutil.which("openscad")
    if path:
        return path
    mac_path = "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
    if os.path.isfile(mac_path):
        return mac_path
    return "openscad"


def render_stl(scad_path, stl_path):
    """Invoke OpenSCAD to render a .scad file to binary .stl."""
    cmd = [_find_openscad(), "--export-format", "binstl", "-o", stl_path, scad_path]
    print(f"  Rendering {os.path.basename(stl_path)}...", end=" ", flush=True)
    t0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - t0
    if result.returncode != 0:
        print(f"FAILED ({elapsed:.1f}s)")
        print(f"    stderr: {result.stderr[:200]}")
        return False
    print(f"OK ({elapsed:.1f}s, {os.path.getsize(stl_path)} bytes)")
    return True


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating default STLs to {OUTPUT_DIR}")

    finger = DangerFinger()
    finger.render_quality = RenderQuality.EXTRAMEDIUM
    finger.build()

    ok = 0
    fail = 0
    for part_enum in PARTS:
        part_name = str(part_enum.name).lower()
        scad_str = build_scad(part_name, finger)
        if scad_str is None:
            print(f"  Skipping {part_name} (no geometry)")
            continue

        scad_path = os.path.join(OUTPUT_DIR, part_name + ".scad")
        stl_path = os.path.join(OUTPUT_DIR, part_name + ".stl")

        with open(scad_path, "w") as f:
            f.write(scad_str if isinstance(scad_str, str) else "\n".join(scad_str))

        if render_stl(scad_path, stl_path):
            os.remove(scad_path)
            ok += 1
        else:
            fail += 1

    print(f"\nDone: {ok} rendered, {fail} failed")
    if fail:
        sys.exit(1)

    stl_files = {f: open(os.path.join(OUTPUT_DIR, f), "rb").read()
                 for f in os.listdir(OUTPUT_DIR) if f.endswith(".stl")}
    if stl_files:
        config = {p.name: p.val for p in finger.params() if hasattr(p, "val")}
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, data in stl_files.items():
                zf.writestr(name, data)
            zf.writestr("config.json", json.dumps(config, indent=2, default=str))
            for extra in ("LICENSE", "README.md"):
                path = os.path.join(PROJECT_ROOT, extra)
                if os.path.isfile(path):
                    zf.write(path, extra)
        bundle_path = os.path.join(OUTPUT_DIR, "bundle.zip")
        with open(bundle_path, "wb") as f:
            f.write(buf.getvalue())
        print(f"  Wrote {bundle_path} ({os.path.getsize(bundle_path)} bytes)")


if __name__ == "__main__":
    main()
