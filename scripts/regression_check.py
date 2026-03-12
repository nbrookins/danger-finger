#!/usr/bin/env python3
"""Re-build all parts at default params, compare STL checksums to reference baseline."""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from danger.finger import DangerFinger
from danger.constants import RenderQuality
from danger.Scad_Renderer import Scad_Renderer
from danger.tools import *

PARTS = ["tip", "base", "linkage", "middle", "tipcover", "socket", "plug", "stand", "pins"]
OUTPUT_DIR = "output"
REFERENCE_DIR = os.path.join(OUTPUT_DIR, "reference")
CHECKSUMS_FILE = os.path.join(OUTPUT_DIR, "reference_checksums.json")
CHECK_DIR = os.path.join(OUTPUT_DIR, "regression_check")


def build_part_scad(part_name, quality=RenderQuality.HIGH):
    """Build a single part at default params and return scad_string."""
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
    if not os.path.isfile(CHECKSUMS_FILE):
        print(f"ERROR: Reference checksums not found at {CHECKSUMS_FILE}")
        print("Run 'make reference-stls' first to create the baseline.")
        sys.exit(2)
    
    with open(CHECKSUMS_FILE) as f:
        reference = json.load(f)
    
    os.makedirs(CHECK_DIR, exist_ok=True)
    
    current = {}
    scad_files = []
    
    print("Building all parts at default params...")
    for part_name in PARTS:
        print(f"  Building {part_name}...")
        scad_str = build_part_scad(part_name)
        if scad_str is None:
            print(f"  WARNING: {part_name} returned no SCAD output")
            continue
        scad_path = os.path.join(CHECK_DIR, f"{part_name}.scad")
        with open(scad_path, "w") as f:
            f.write(scad_str)
        scad_files.append(scad_path)
    
    if not scad_files:
        print("ERROR: No SCAD files generated")
        sys.exit(1)
    
    print("Rendering STLs...")
    renderer = Scad_Renderer()
    renderer.scad_parallel(scad_files, max_concurrent_tasks=2)
    
    print("Computing checksums and comparing...")
    mismatches = []
    for part_name in PARTS:
        stl_path = os.path.join(CHECK_DIR, f"{part_name}.stl")
        if not os.path.isfile(stl_path):
            print(f"  WARNING: {stl_path} not found")
            continue
        with open(stl_path, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()
        current[part_name] = sha
        ref_sha = reference.get(part_name)
        if ref_sha is None:
            print(f"  {part_name}: NEW (no reference)")
        elif sha == ref_sha:
            print(f"  {part_name}: OK")
        else:
            print(f"  {part_name}: MISMATCH")
            print(f"    reference: {ref_sha}")
            print(f"    current:   {sha}")
            mismatches.append(part_name)
    
    if mismatches:
        print(f"\nGenerating comparison PNGs for mismatched parts...")
        for part_name in mismatches:
            scad_path = os.path.join(CHECK_DIR, f"{part_name}.scad")
            if os.path.isfile(scad_path):
                view_dir = os.path.join(CHECK_DIR, "views")
                try:
                    renderer.render_multi_view(scad_path, view_dir)
                except Exception as e:
                    print(f"  WARNING: Multi-view render failed for {part_name}: {e}")
    
    report = {
        "reference_file": CHECKSUMS_FILE,
        "current": current,
        "mismatches": mismatches,
        "passed": len(mismatches) == 0,
    }
    report_path = os.path.join(CHECK_DIR, "report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    if mismatches:
        print(f"\nREGRESSION DETECTED: {len(mismatches)} part(s) differ: {', '.join(mismatches)}")
        print(f"Report: {report_path}")
        sys.exit(1)
    else:
        print(f"\nAll {len(current)} parts match reference. No regression.")
        sys.exit(0)


if __name__ == "__main__":
    main()
