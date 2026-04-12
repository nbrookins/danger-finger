#!/usr/bin/env python3
"""Direct STL geometry inspection using trimesh.

Loads STL files from a preview run and validates geometry properties
without requiring a browser, web server, or WebGL. Produces a JSON
report with per-part metrics and pass/fail status.

Usage:
    python scripts/stl_inspect.py [--run-dir output/preview_temp/xxx]
    python scripts/stl_inspect.py --trigger  # trigger preview first, then inspect

If --run-dir is omitted, uses the most recent preview_temp subdirectory.
"""
import argparse
import json
import os
import sys
import time
import urllib.request

import numpy as np
import trimesh

PREVIEW_TEMP = "output/preview_temp"
OUTPUT_DIR = "output"
REPORT_NAME = "stl-inspection.json"

EXPECTED_PARTS = ["tip", "base", "linkage", "middle", "tipcover", "socket", "plug", "stand", "bumper"]

# Per-part expected ranges. Derived from default params; generous enough
# to accommodate parameter sweeps without false positives.
PART_EXPECTATIONS = {
    "tip":      {"min_vol": 200, "max_vol": 3000, "min_faces": 2000, "max_faces": 50000, "max_extent": 40},
    "base":     {"min_vol": 400, "max_vol": 5000, "min_faces": 4000, "max_faces": 80000, "max_extent": 50},
    "linkage":  {"min_vol": 200, "max_vol": 5000, "min_faces": 2000, "max_faces": 50000, "max_extent": 120},
    "middle":   {"min_vol": 400, "max_vol": 5000, "min_faces": 4000, "max_faces": 80000, "max_extent": 60},
    "tipcover": {"min_vol": 200, "max_vol": 4000, "min_faces": 2000, "max_faces": 60000, "max_extent": 50},
    "socket":   {"min_vol": 500, "max_vol": 10000, "min_faces": 5000, "max_faces": 200000, "max_extent": 80},
    "plug":     {"min_vol": 5, "max_vol": 500, "min_faces": 100, "max_faces": 10000, "max_extent": 20},
    "stand":    {"min_vol": 1000, "max_vol": 30000, "min_faces": 5000, "max_faces": 100000, "max_extent": 80},
    "bumper":   {"min_vol": 30, "max_vol": 2000, "min_faces": 500, "max_faces": 30000, "max_extent": 40},
}


def find_latest_run():
    if not os.path.isdir(PREVIEW_TEMP):
        return None
    runs = sorted(os.listdir(PREVIEW_TEMP), key=lambda d: os.path.getmtime(os.path.join(PREVIEW_TEMP, d)))
    return os.path.join(PREVIEW_TEMP, runs[-1]) if runs else None


def trigger_preview(base_url="http://127.0.0.1:8092"):
    """POST /api/preview and wait for completion. Returns run_dir path."""
    print("Triggering preview at %s ..." % base_url, flush=True)
    req = urllib.request.Request(
        base_url + "/api/preview",
        data=json.dumps({"params": {}}).encode(),
        headers={"Content-Type": "application/json"},
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())

    if resp.get("stl_urls"):
        # Cached result — extract run_id from first URL
        first_url = next(iter(resp["stl_urls"].values()))
        run_id = first_url.split("/api/preview/temp/")[1].split("/")[0]
        return os.path.join(PREVIEW_TEMP, run_id)

    job_id = resp.get("job_id")
    if not job_id:
        print("ERROR: No job_id or stl_urls in response", flush=True)
        return None

    for _ in range(120):
        jr = json.loads(urllib.request.urlopen(
            base_url + "/api/jobs/" + job_id, timeout=10
        ).read())
        if jr.get("status") == "complete":
            first_url = next(iter(jr["result"]["stl_urls"].values()))
            run_id = first_url.split("/api/preview/temp/")[1].split("/")[0]
            return os.path.join(PREVIEW_TEMP, run_id)
        if jr.get("status") == "failed":
            print("ERROR: Preview job failed", flush=True)
            return None
        time.sleep(2)
    return None


def inspect_part(stl_path, part_name):
    """Inspect a single STL file. Returns a dict of metrics and checks."""
    result = {"part": part_name, "file": stl_path, "checks": {}, "passed": True}

    try:
        mesh = trimesh.load(stl_path)
    except Exception as e:
        result["error"] = "Failed to load: %s" % e
        result["passed"] = False
        return result

    result["vertices"] = int(mesh.vertices.shape[0])
    result["faces"] = int(mesh.faces.shape[0])
    result["is_watertight"] = bool(mesh.is_watertight)
    result["volume_mm3"] = round(float(mesh.volume), 2)
    result["surface_area_mm2"] = round(float(mesh.area), 2)
    result["extents_mm"] = mesh.bounding_box.extents.round(2).tolist()
    result["center_mm"] = mesh.centroid.round(2).tolist()
    result["euler_number"] = int(mesh.euler_number)

    # Bbox in min/max form for compatibility with existing geometry_checks
    bb = mesh.bounds
    result["bbox"] = {"min": bb[0].round(3).tolist(), "max": bb[1].round(3).tolist()}

    exp = PART_EXPECTATIONS.get(part_name, {})
    checks = result["checks"]

    # Loadable
    checks["loadable"] = {"passed": True, "detail": "OK"}

    # Watertight (warn, don't fail — some OpenSCAD exports have edge cases)
    checks["watertight"] = {
        "passed": mesh.is_watertight,
        "detail": "watertight" if mesh.is_watertight else "NOT watertight (euler=%d)" % mesh.euler_number,
        "severity": "warn",
    }

    # Volume in expected range
    vol = mesh.volume
    if exp.get("min_vol") and vol < exp["min_vol"]:
        checks["volume"] = {"passed": False, "detail": "%.1f < min %.1f mm³" % (vol, exp["min_vol"])}
        result["passed"] = False
    elif exp.get("max_vol") and vol > exp["max_vol"]:
        checks["volume"] = {"passed": False, "detail": "%.1f > max %.1f mm³" % (vol, exp["max_vol"])}
        result["passed"] = False
    else:
        checks["volume"] = {"passed": True, "detail": "%.1f mm³" % vol}

    # Face count in expected range
    nf = mesh.faces.shape[0]
    if exp.get("min_faces") and nf < exp["min_faces"]:
        checks["face_count"] = {"passed": False, "detail": "%d < min %d" % (nf, exp["min_faces"])}
        result["passed"] = False
    elif exp.get("max_faces") and nf > exp["max_faces"]:
        checks["face_count"] = {"passed": False, "detail": "%d > max %d" % (nf, exp["max_faces"])}
        result["passed"] = False
    else:
        checks["face_count"] = {"passed": True, "detail": "%d faces" % nf}

    # No axis too large (catches exploded/transformed geometry bugs)
    max_ext = max(mesh.bounding_box.extents)
    limit = exp.get("max_extent", 200)
    if max_ext > limit:
        checks["max_extent"] = {"passed": False, "detail": "%.1f > limit %.1f mm" % (max_ext, limit)}
        result["passed"] = False
    else:
        checks["max_extent"] = {"passed": True, "detail": "max %.1f mm" % max_ext}

    # No degenerate (collapsed) axis
    min_ext = min(mesh.bounding_box.extents)
    if min_ext < 0.1:
        checks["min_extent"] = {"passed": False, "detail": "%.3f mm — collapsed axis" % min_ext}
        result["passed"] = False
    else:
        checks["min_extent"] = {"passed": True, "detail": "min %.1f mm" % min_ext}

    # Volume should be positive
    if vol <= 0:
        checks["positive_volume"] = {"passed": False, "detail": "volume=%.3f — inverted normals?" % vol}
        result["passed"] = False
    else:
        checks["positive_volume"] = {"passed": True, "detail": "OK"}

    return result


def inspect_run(run_dir):
    """Inspect all STL files in a preview run directory."""
    report = {
        "run_dir": run_dir,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "parts": [],
        "summary": {"total": 0, "passed": 0, "failed": 0, "warnings": 0},
    }

    stl_files = {f.replace(".stl", ""): os.path.join(run_dir, f)
                 for f in os.listdir(run_dir) if f.endswith(".stl")}

    # Check all expected parts are present
    missing = [p for p in EXPECTED_PARTS if p not in stl_files]
    if missing:
        report["missing_parts"] = missing

    for part_name in EXPECTED_PARTS:
        if part_name not in stl_files:
            report["parts"].append({
                "part": part_name, "error": "STL not found", "passed": False, "checks": {}
            })
            report["summary"]["total"] += 1
            report["summary"]["failed"] += 1
            continue

        result = inspect_part(stl_files[part_name], part_name)
        report["parts"].append(result)
        report["summary"]["total"] += 1
        if result["passed"]:
            report["summary"]["passed"] += 1
        else:
            report["summary"]["failed"] += 1

        # Count warnings (watertight failures are warnings, not errors)
        for check in result.get("checks", {}).values():
            if not check.get("passed") and check.get("severity") == "warn":
                report["summary"]["warnings"] += 1

    report["all_passed"] = report["summary"]["failed"] == 0
    return report


def print_summary(report):
    """Print a human-readable summary table."""
    print("", flush=True)
    print("=" * 72, flush=True)
    print("STL Inspection: %s" % report["run_dir"], flush=True)
    print("=" * 72, flush=True)
    print("", flush=True)

    fmt = "%-12s %6s %6s %5s %9s %8s  %s"
    print(fmt % ("Part", "Verts", "Faces", "H2O", "Vol mm³", "MaxExt", "Status"), flush=True)
    print("-" * 72, flush=True)

    for p in report["parts"]:
        if p.get("error"):
            print("%-12s  %-58s  FAIL" % (p["part"], p["error"]), flush=True)
            continue

        wt = "yes" if p["is_watertight"] else "NO"
        status = "PASS" if p["passed"] else "FAIL"
        fails = [k for k, v in p["checks"].items()
                 if not v["passed"] and v.get("severity") != "warn"]
        detail = ", ".join(fails) if fails else ""

        print(fmt % (
            p["part"],
            p["vertices"],
            p["faces"],
            wt,
            "%.1f" % p["volume_mm3"],
            "%.1f" % max(p["extents_mm"]),
            "%s  %s" % (status, detail),
        ), flush=True)

    s = report["summary"]
    print("", flush=True)
    print("Total: %d | Passed: %d | Failed: %d | Warnings: %d" % (
        s["total"], s["passed"], s["failed"], s["warnings"]
    ), flush=True)
    print("Result: %s" % ("PASS" if report["all_passed"] else "FAIL"), flush=True)
    print("", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Direct STL geometry inspection")
    parser.add_argument("--run-dir", help="Preview run directory (default: latest)")
    parser.add_argument("--trigger", action="store_true", help="Trigger preview first")
    parser.add_argument("--base-url", default="http://127.0.0.1:8092", help="Web server URL for --trigger")
    parser.add_argument("--output", default=os.path.join(OUTPUT_DIR, REPORT_NAME), help="JSON report path")
    parser.add_argument("--quiet", action="store_true", help="JSON only, no table")
    args = parser.parse_args()

    run_dir = args.run_dir
    if args.trigger:
        run_dir = trigger_preview(args.base_url)
    if not run_dir:
        run_dir = find_latest_run()
    if not run_dir or not os.path.isdir(run_dir):
        print("ERROR: No preview run found. Use --trigger or --run-dir.", file=sys.stderr)
        sys.exit(1)

    report = inspect_run(run_dir)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    if not args.quiet:
        print_summary(report)
        print("Report: %s" % args.output, flush=True)

    sys.exit(0 if report["all_passed"] else 1)


if __name__ == "__main__":
    main()
