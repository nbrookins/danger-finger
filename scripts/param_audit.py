#!/usr/bin/env python3
"""Run a curated multi-profile audit across key finger parts."""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from danger.Params import Params
from danger.Scad_Renderer import Scad_Renderer
from danger.constants import RenderQuality
from danger.finger import DangerFinger
from danger.geometry_checks import (
    bbox_dimensions,
    bbox_from_stl,
    check_no_degenerate,
    check_reasonable_size,
    check_zero_dimension,
)
from danger.tools import iterable
from tests.profiles import PROFILE_LABELS, PROFILE_ORDER, PROFILES

PARTS = (
    "socket",
    "base",
    "middle",
    "tip",
    "tipcover",
    "linkage",
    "plug",
    "peg",
    "bumper",
    "stand",
    "pins",
)
OUTPUT_BASE = "output/param_audit"


def parse_selection(raw, available):
    if raw == "all":
        return list(available)
    values = [item.strip() for item in raw.split(",") if item.strip()]
    unknown = [item for item in values if item not in available]
    if unknown:
        raise ValueError("Unknown selection(s): %s" % ", ".join(sorted(unknown)))
    return values


def parse_quality(name):
    try:
        return RenderQuality[name.upper()]
    except KeyError as exc:
        raise ValueError("Unknown render quality: %s" % name) from exc


def build_finger(config, quality):
    finger = DangerFinger()
    Params.apply_config(finger, config)
    finger.render_quality = quality
    warnings = finger.validate_params()
    finger.build()
    return finger, warnings


def extract_scad(finger, part_name):
    for _fp, model in finger.models.items():
        if iterable(model):
            if str(model[0].part) == part_name:
                return model[0].scad
        elif str(model.part) == part_name:
            return model.scad
    return None


def stl_checks(stl_path):
    bbox = bbox_from_stl(stl_path)
    dims = bbox_dimensions(bbox)
    zero_ok, zero_msg = check_zero_dimension(dims)
    size_ok, size_msg = check_reasonable_size(dims)
    passed = bbox is not None and zero_ok and size_ok
    return {
        "bbox": bbox,
        "dimensions": dims,
        "checks": {
            "zero_dimension": {"passed": zero_ok, "message": zero_msg},
            "reasonable_size": {"passed": size_ok, "message": size_msg},
        },
        "passed": passed,
    }


def write_markdown_report(report, path):
    lines = []
    lines.append("# Param Audit Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("- Quality: `%s`" % report["quality"])
    lines.append("- Profiles: %d" % len(report["profiles"]))
    lines.append("- Parts per profile: %d" % len(report["parts"]))
    lines.append("- Total cases: %d" % report["summary"]["total_cases"])
    lines.append("- Passed: %d" % report["summary"]["passed_cases"])
    lines.append("- Failed: %d" % report["summary"]["failed_cases"])
    lines.append("- Skip STL: `%s`" % report["skip_stl"])
    lines.append("- Render PNG: `%s`" % report["render_png"])
    lines.append("")
    lines.append("| Profile | Part | Status | Warnings | Dimensions | Notes |")
    lines.append("|---|---|---|---|---|---|")
    for profile in report["profiles"]:
        profile_name = profile["name"]
        warning_count = len(profile["warnings"])
        for part in profile["parts"]:
            dims = part.get("dimensions")
            dims_str = "x".join("%.2f" % value for value in dims) if dims else "n/a"
            notes = "; ".join(part["notes"]) if part["notes"] else ""
            status = "PASS" if part["passed"] else "FAIL"
            lines.append(
                "| %s | %s | %s | %d | %s | %s |"
                % (profile_name, part["part"], status, warning_count, dims_str, notes.replace("|", "/"))
            )
    lines.append("")
    lines.append("## Profile Warnings")
    lines.append("")
    for profile in report["profiles"]:
        lines.append("### %s" % profile["name"])
        if profile["warnings"]:
            for warning in profile["warnings"]:
                lines.append("- %s" % warning)
        else:
            lines.append("- none")
        lines.append("")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Run curated profile x part param audit")
    parser.add_argument("--profiles", default="all", help="Comma-separated profile names or 'all'")
    parser.add_argument("--parts", default="all", help="Comma-separated part names or 'all'")
    parser.add_argument("--quality", default="STUPIDFAST", help="RenderQuality enum name")
    parser.add_argument("--output-dir", default=OUTPUT_BASE, help="Output directory")
    parser.add_argument("--render-png", action="store_true", help="Render multi-view PNGs")
    parser.add_argument("--skip-stl", action="store_true", help="Skip STL and bbox checks")
    args = parser.parse_args()

    selected_profiles = parse_selection(args.profiles, PROFILE_ORDER)
    selected_parts = parse_selection(args.parts, PARTS)
    quality = parse_quality(args.quality)

    os.makedirs(args.output_dir, exist_ok=True)

    renderer = None
    if not args.skip_stl:
        renderer = Scad_Renderer()

    report = {
        "quality": quality.name,
        "skip_stl": args.skip_stl,
        "render_png": args.render_png,
        "parts": selected_parts,
        "profiles": [],
        "summary": {"total_cases": 0, "passed_cases": 0, "failed_cases": 0},
    }

    for profile_name in selected_profiles:
        config = PROFILES[profile_name]
        profile_dir = os.path.join(args.output_dir, profile_name)
        os.makedirs(profile_dir, exist_ok=True)

        profile_entry = {
            "name": profile_name,
            "label": PROFILE_LABELS.get(profile_name, profile_name),
            "config": config,
            "warnings": [],
            "parts": [],
        }

        try:
            finger, warnings = build_finger(config, quality)
            profile_entry["warnings"] = warnings
        except Exception as exc:
            for part_name in selected_parts:
                profile_entry["parts"].append(
                    {
                        "part": part_name,
                        "passed": False,
                        "notes": ["build failed: %s" % exc],
                        "dimensions": None,
                    }
                )
                report["summary"]["total_cases"] += 1
                report["summary"]["failed_cases"] += 1
            report["profiles"].append(profile_entry)
            continue

        for part_name in selected_parts:
            report["summary"]["total_cases"] += 1
            part_entry = {
                "part": part_name,
                "passed": True,
                "notes": [],
                "scad": None,
                "stl": None,
                "dimensions": None,
            }

            scad = extract_scad(finger, part_name)
            if scad is None:
                part_entry["passed"] = False
                part_entry["notes"].append("no scad output")
                report["summary"]["failed_cases"] += 1
                profile_entry["parts"].append(part_entry)
                continue

            scad_ok, scad_msg = check_no_degenerate(scad)
            if not scad_ok:
                part_entry["passed"] = False
                part_entry["notes"].append(scad_msg)

            scad_path = os.path.join(profile_dir, "%s.scad" % part_name)
            with open(scad_path, "w", encoding="utf-8") as handle:
                handle.write(scad)
            part_entry["scad"] = scad_path

            if not args.skip_stl:
                stl_path = os.path.join(profile_dir, "%s.stl" % part_name)
                try:
                    renderer.scad_to_stl(scad_path, stl_path)
                    part_entry["stl"] = stl_path
                    stl_result = stl_checks(stl_path)
                    part_entry["dimensions"] = stl_result["dimensions"]
                    if not stl_result["passed"]:
                        part_entry["passed"] = False
                        for check in stl_result["checks"].values():
                            if not check["passed"]:
                                part_entry["notes"].append(check["message"])
                except Exception as exc:
                    part_entry["passed"] = False
                    part_entry["notes"].append("stl render failed: %s" % exc)

                if args.render_png and part_entry["stl"] is not None:
                    try:
                        view_dir = os.path.join(profile_dir, "views")
                        part_entry["views"] = renderer.render_multi_view(scad_path, view_dir)
                    except Exception as exc:
                        part_entry["notes"].append("png render failed: %s" % exc)
            else:
                part_entry["notes"].append("stl skipped")

            if part_entry["passed"]:
                report["summary"]["passed_cases"] += 1
            else:
                report["summary"]["failed_cases"] += 1
            profile_entry["parts"].append(part_entry)

        report["profiles"].append(profile_entry)

    report_path = os.path.join(args.output_dir, "report.json")
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, default=str)

    md_path = os.path.join(args.output_dir, "report.md")
    write_markdown_report(report, md_path)

    print("Wrote %s" % report_path)
    print("Wrote %s" % md_path)
    if report["summary"]["failed_cases"] > 0:
        print(
            "PARAM AUDIT FAILED: %d/%d case(s) failed"
            % (report["summary"]["failed_cases"], report["summary"]["total_cases"])
        )
        sys.exit(1)

    print(
        "PARAM AUDIT PASSED: %d case(s)"
        % report["summary"]["passed_cases"]
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
