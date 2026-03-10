#!/usr/bin/env python3
"""
Param-sweep validation for derived formulas.
Usage: python scripts/validate_formula.py --part tip --params tip_circumference --steps 5
"""
import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from danger.finger import DangerFinger
from danger.constants import RenderQuality
from danger.Scad_Renderer import Scad_Renderer
from danger.geometry_checks import (
    bbox_from_stl, bbox_dimensions, check_no_degenerate, check_proportional_scaling
)
from danger.Params import Params
from danger.tools import *
from solid2 import scad_render

PARTS_LIST = ["tip", "base", "linkage", "middle", "tipcover", "socket", "plug", "stand", "pins"]
OUTPUT_BASE = "output/formula_validation"


def get_param_range(param_name, steps=5):
    """Get min/max from DangerFingerParams Prop definition and generate sweep values."""
    import inspect
    from danger.finger_params import DangerFingerParams
    from danger.Params import Prop
    for name, prop in inspect.getmembers(DangerFingerParams):
        if name == param_name and isinstance(prop, Prop):
            minv = prop.minimum
            maxv = prop.maximum
            default = prop.default
            if minv is not None and maxv is not None:
                step_size = (maxv - minv) / max(steps - 1, 1)
                return [round(minv + i * step_size, 4) for i in range(steps)]
            return [default]
    return None


def build_part_scad_with_config(part_name, config, quality=RenderQuality.STUPIDFAST):
    """Build a single part with given config and return scad_string."""
    finger = DangerFinger()
    Params.apply_config(finger, config)
    finger.render_quality = quality
    finger.build()
    for _fp, model in finger.models.items():
        from danger.tools import iterable, flatten
        if iterable(model):
            if str(model[0].part) == part_name:
                scad_parts = flatten([x.scad for x in model])
                return scad_render(union()(*scad_parts)) if len(scad_parts) > 1 else scad_render(scad_parts[0])
        elif str(model.part) == part_name:
            return scad_render(model.scad)
    return None


def main():
    parser = argparse.ArgumentParser(description="Validate parametric formula by sweeping params")
    parser.add_argument("--part", required=True, help="Part name (e.g. tip, base, middle)")
    parser.add_argument("--params", required=True, help="Comma-separated param names to sweep")
    parser.add_argument("--steps", type=int, default=5, help="Number of sweep steps per param")
    parser.add_argument("--render-png", action="store_true", help="Render multi-view PNGs at each sweep point")
    args = parser.parse_args()

    part_name = args.part
    param_names = [p.strip() for p in args.params.split(",")]
    
    output_dir = os.path.join(OUTPUT_BASE, f"{part_name}_{'_'.join(param_names)}")
    os.makedirs(output_dir, exist_ok=True)
    
    renderer = Scad_Renderer()
    report = {"part": part_name, "params": param_names, "steps": args.steps, "results": []}
    all_passed = True
    
    for param_name in param_names:
        values = get_param_range(param_name, args.steps)
        if values is None:
            print(f"WARNING: param '{param_name}' not found in DangerFingerParams")
            continue
        
        print(f"\nSweeping {param_name}: {values}")
        prev_dims = None
        
        for val in values:
            config = {param_name: float(val)}
            step_id = f"{param_name}_{val}".replace(".", "_").replace("-", "neg")
            
            print(f"  {param_name}={val}...")
            scad_str = build_part_scad_with_config(part_name, config)
            
            if scad_str is None:
                entry = {"param": param_name, "value": val, "passed": False, "error": "No SCAD output"}
                report["results"].append(entry)
                all_passed = False
                continue
            
            degen_ok, degen_msg = check_no_degenerate(scad_str)
            
            scad_path = os.path.join(output_dir, f"{step_id}.scad")
            stl_path = os.path.join(output_dir, f"{step_id}.stl")
            with open(scad_path, "w") as f:
                f.write(scad_str)
            
            try:
                renderer.scad_to_stl(scad_path, stl_path)
            except Exception as e:
                entry = {"param": param_name, "value": val, "passed": False, "error": f"STL render failed: {e}"}
                report["results"].append(entry)
                all_passed = False
                continue
            
            bbox = bbox_from_stl(stl_path)
            dims = bbox_dimensions(bbox) if bbox else None
            
            entry = {
                "param": param_name,
                "value": val,
                "passed": degen_ok and bbox is not None,
                "degenerate_check": degen_msg,
                "bbox": bbox,
                "dimensions": dims,
            }
            
            if not degen_ok or bbox is None:
                all_passed = False
            
            report["results"].append(entry)
            
            if args.render_png:
                try:
                    view_dir = os.path.join(output_dir, "views")
                    renderer.render_multi_view(scad_path, view_dir)
                except Exception as e:
                    print(f"    PNG render warning: {e}")
            
            print(f"    {'PASS' if entry['passed'] else 'FAIL'} dims={dims} {degen_msg}")
    
    report["all_passed"] = all_passed
    report_path = os.path.join(output_dir, "report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nReport: {report_path}")
    if all_passed:
        print("ALL CHECKS PASSED")
        sys.exit(0)
    else:
        print("SOME CHECKS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
