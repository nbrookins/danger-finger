#!/usr/bin/env python3
"""Build all parts at default params, store STL SHA256 checksums and multi-view PNGs as regression baseline."""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from danger.finger import DangerFinger
from danger.finger_params import DangerFingerParams
from danger.constants import RenderQuality, FingerPart
from danger.Scad_Renderer import Scad_Renderer
from danger.tools import *

PARTS = ["tip", "base", "linkage", "middle", "tipcover", "socket", "plug", "stand", "pins"]
OUTPUT_DIR = "output"
REFERENCE_DIR = os.path.join(OUTPUT_DIR, "reference")
CHECKSUMS_FILE = os.path.join(OUTPUT_DIR, "reference_checksums.json")


def build_part_scad(part_name, quality=RenderQuality.HIGH):
    """Build a single part at default params and return (scad_string, part_name)."""
    finger = DangerFinger()
    finger.render_quality = quality
    finger.build()
    for _fp, model in finger.models.items():
        from danger.tools import iterable, flatten
        if iterable(model):
            if str(model[0].part) == part_name:
                return model[0].scad
        elif str(model.part) == part_name:
            return model.scad
    return None


def main():
    os.makedirs(REFERENCE_DIR, exist_ok=True)
    
    checksums = {}
    scad_files = []
    
    print("Building all parts at default params with HIGH quality...")
    for part_name in PARTS:
        print(f"  Building {part_name}...")
        scad_str = build_part_scad(part_name)
        if scad_str is None:
            print(f"  WARNING: {part_name} returned no SCAD output")
            continue
        
        scad_path = os.path.join(REFERENCE_DIR, f"{part_name}.scad")
        with open(scad_path, "w") as f:
            f.write(scad_str)
        scad_files.append(scad_path)
    
    if not scad_files:
        print("ERROR: No SCAD files generated")
        sys.exit(1)
    
    print("Rendering STLs in parallel...")
    renderer = Scad_Renderer()
    renderer.scad_parallel(scad_files, png_size="1024,768", max_concurrent_tasks=2)
    
    print("Computing checksums...")
    for part_name in PARTS:
        stl_path = os.path.join(REFERENCE_DIR, f"{part_name}.stl")
        if not os.path.isfile(stl_path):
            print(f"  WARNING: {stl_path} not found after render")
            continue
        with open(stl_path, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()
        checksums[part_name] = sha
        print(f"  {part_name}: {sha}")
    
    print("Rendering multi-view PNGs...")
    for part_name in PARTS:
        scad_path = os.path.join(REFERENCE_DIR, f"{part_name}.scad")
        if os.path.isfile(scad_path):
            view_dir = os.path.join(REFERENCE_DIR, "views")
            try:
                renderer.render_multi_view(scad_path, view_dir)
            except Exception as e:
                print(f"  WARNING: Multi-view render failed for {part_name}: {e}")
    
    with open(CHECKSUMS_FILE, "w") as f:
        json.dump(checksums, f, indent=2)
    print(f"\nWrote {len(checksums)} checksums to {CHECKSUMS_FILE}")
    print("Reference baseline complete.")


if __name__ == "__main__":
    main()
