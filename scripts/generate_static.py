#!/usr/bin/env python3
"""Generate static JSON files for the S3 static site.

Produces the same JSON that the live server returns for:
  GET /api/parts  ->  web/static/api/parts.json
  GET /params/all ->  web/static/params/all.json

Run from project root: python3 scripts/generate_static.py
"""
import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from danger.finger import DangerFinger, PART_COLORS
from danger.finger_params import DangerFingerParams as P, FingerPart

STATIC_DIR = os.path.join(PROJECT_ROOT, "web", "static")

PARTS = [
    FingerPart.TIP, FingerPart.BASE, FingerPart.LINKAGE, FingerPart.MIDDLE,
    FingerPart.TIPCOVER, FingerPart.SOCKET, FingerPart.PLUG, FingerPart.STAND,
]


def _preview_config():
    """Replicate the preview config logic from web/server.py without importing it."""
    return {
        "rotateOffsets": {k: list(v) for k, v in P._preview_rotate_offsets.items()},
        "positionOffsets": {k: list(v) for k, v in P._preview_position_offsets.items()},
        "plugInstances": [
            {"position": list(p["position"]), "rotation": list(p["rotation"])}
            for p in P._preview_plug_instances
        ],
        "explodeOffsets": {k: list(v) for k, v in P._preview_explode_offsets.items()},
        "partColors": {k: v for k, v in PART_COLORS.items()},
    }


def generate_parts_json():
    part_list = [{"id": str(p.name).lower(), "label": str(p.name).capitalize()} for p in PARTS]
    data = {
        "parts": part_list,
        "version": DangerFinger.VERSION,
        "build": "static",
        "previewConfig": _preview_config(),
    }
    out = os.path.join(STATIC_DIR, "api", "parts.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(data, f, default=str, separators=(",", ":"))
    print(f"  Wrote {out} ({os.path.getsize(out)} bytes)")


def generate_params_json():
    params = DangerFinger().get_params(adv=False, allv=True, extended=True)
    out = os.path.join(STATIC_DIR, "params", "all.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(params, f, default=str, skipkeys=True, separators=(",", ":"))
    print(f"  Wrote {out} ({os.path.getsize(out)} bytes)")


def main():
    print("Generating static JSON files...")
    generate_parts_json()
    generate_params_json()
    print("Done.")


if __name__ == "__main__":
    main()
