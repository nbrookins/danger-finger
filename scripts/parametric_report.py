#!/usr/bin/env python3
"""Tiered parametric validation pipeline — local-first.

Tier 1 (always): pytest + SCAD baseline hash comparison + SCAD-only param audit
Tier 2 (needs OpenSCAD): full param audit with STL render + bbox checks
Tier 3 (needs OpenSCAD + Playwright): visual web UI verification + multi-angle review

All tiers run locally. OpenSCAD is accessed via OPENSCAD_EXEC (typically
bin/openscad-docker which runs the CLI through Docker transparently).

Set SKIP_OPENSCAD=1 to run Tier 1 only (fast, no OpenSCAD needed).

Writes output/parametric-report.md and output/parametric-report.json.
Exit code 0 = all tiers that ran passed; 1 = at least one failure.
"""

import hashlib
import json
import os
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

OUTPUT_DIR = os.path.join(REPO_ROOT, "output")
BASELINE_PATH = os.path.join(OUTPUT_DIR, "scad_baseline.json")
REPORT_JSON = os.path.join(OUTPUT_DIR, "parametric-report.json")
REPORT_MD = os.path.join(OUTPUT_DIR, "parametric-report.md")
PYTHON = os.environ.get("PYTHON", sys.executable)


def openscad_available():
    """Check if OPENSCAD_EXEC is set and can actually run (not blocked by sandbox)."""
    if os.environ.get("SKIP_OPENSCAD", "").strip() in ("1", "true", "yes"):
        return False
    exec_path = os.environ.get("OPENSCAD_EXEC", "")
    if not exec_path:
        return False
    try:
        test_scad = os.path.join(OUTPUT_DIR, "_probe.scad")
        test_stl = os.path.join(OUTPUT_DIR, "_probe.stl")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(test_scad, "w") as f:
            f.write("cube(1);")
        r = subprocess.run(
            [exec_path, "-o", test_stl, test_scad],
            capture_output=True, timeout=30,
        )
        ok = r.returncode == 0 and os.path.exists(test_stl) and os.path.getsize(test_stl) > 0
        for p in (test_scad, test_stl):
            try:
                os.remove(p)
            except OSError:
                pass
        return ok
    except Exception:
        return False


def run_cmd(args, label, cwd=None, timeout=600, env=None):
    """Run a command, capture output, return (ok, stdout, stderr, elapsed)."""
    start = time.time()
    try:
        r = subprocess.run(
            args, capture_output=True, text=True,
            cwd=cwd or REPO_ROOT, timeout=timeout, env=env,
        )
        elapsed = time.time() - start
        return r.returncode == 0, r.stdout, r.stderr, elapsed
    except subprocess.TimeoutExpired:
        return False, "", "TIMEOUT after %ds" % timeout, time.time() - start
    except Exception as e:
        return False, "", str(e), time.time() - start


# ---------------------------------------------------------------------------
# Tier 1: fast checks (no OpenSCAD)
# ---------------------------------------------------------------------------

def tier1_pytest():
    ok, stdout, stderr, elapsed = run_cmd(
        [PYTHON, "-m", "pytest", "tests/", "-x", "-v", "--tb=short", "-q"],
        "pytest",
    )
    lines = (stdout + stderr).strip().splitlines()
    summary = lines[-1] if lines else "(no output)"
    return ok, summary, elapsed


def tier1_scad_baseline():
    from danger.finger import DangerFinger
    from danger.constants import RenderQuality
    from danger.tools import iterable

    if not os.path.exists(BASELINE_PATH):
        return False, {"error": "no baseline file at %s" % BASELINE_PATH}, 0

    with open(BASELINE_PATH) as f:
        baseline = json.load(f)

    start = time.time()
    finger = DangerFinger()
    finger.render_quality = RenderQuality.STUPIDFAST
    _stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")
    try:
        finger.build()
    finally:
        sys.stdout.close()
        sys.stdout = _stdout

    results = {}
    for name, model in finger.models.items():
        if iterable(model):
            scad = model[0].scad if hasattr(model[0], "scad") else None
        else:
            scad = model.scad if hasattr(model, "scad") else None
        if not scad:
            results[name] = {"status": "no_scad"}
            continue
        sha = hashlib.sha256(scad.encode()).hexdigest()
        expected = baseline.get(name, {}).get("sha256")
        if expected is None:
            results[name] = {"status": "new_part", "sha256": sha}
        elif sha == expected:
            results[name] = {"status": "unchanged"}
        else:
            results[name] = {"status": "CHANGED", "sha256": sha, "expected": expected, "length": len(scad)}

    elapsed = time.time() - start
    all_ok = all(r["status"] in ("unchanged", "new_part") for r in results.values())
    return all_ok, results, elapsed


def tier1_param_audit_scad():
    ok, stdout, stderr, elapsed = run_cmd(
        [PYTHON, "scripts/param_audit.py", "--profiles", "all", "--parts", "all",
         "--quality", "STUPIDFAST", "--skip-stl"],
        "param-audit-scad",
    )
    lines = (stdout + stderr).strip().splitlines()
    summary = lines[-1] if lines else "(no output)"
    return ok, summary, elapsed


# ---------------------------------------------------------------------------
# Tier 2: STL render + bbox checks (needs OPENSCAD_EXEC)
# ---------------------------------------------------------------------------

def tier2_param_audit_full():
    """Run param_audit.py locally with STL rendering via OPENSCAD_EXEC."""
    ok, stdout, stderr, elapsed = run_cmd(
        [PYTHON, "scripts/param_audit.py", "--profiles", "all", "--parts", "all",
         "--quality", "STUPIDFAST"],
        "param-audit-full", timeout=300,
    )
    lines = (stdout + stderr).strip().splitlines()
    summary = lines[-1] if lines else "(no output)"
    return ok, summary, elapsed


# ---------------------------------------------------------------------------
# Tier 2b: direct STL inspection (trimesh, no browser needed)
# ---------------------------------------------------------------------------

def tier2b_stl_inspect():
    """Run stl_inspect.py on the latest preview run (or trigger one)."""
    ok, stdout, stderr, elapsed = run_cmd(
        [PYTHON, "scripts/stl_inspect.py"],
        "stl-inspect", timeout=60,
    )
    combined = (stdout + stderr).strip()
    lines = combined.splitlines()
    summary_line = ""
    for ln in reversed(lines):
        if ln.startswith("Total:") or ln.startswith("Result:"):
            summary_line = ln
            break
    if not summary_line:
        summary_line = lines[-1] if lines else "(no output)"

    # Parse the JSON report for structured data
    report_path = os.path.join(OUTPUT_DIR, "stl-inspection.json")
    inspection = None
    if os.path.exists(report_path):
        with open(report_path) as f:
            inspection = json.load(f)

    return ok, summary_line, inspection, elapsed


# ---------------------------------------------------------------------------
# Tier 3: visual verification (local server + Playwright)
# ---------------------------------------------------------------------------

def _find_playwright_python():
    candidates = [PYTHON, "python3", sys.executable]
    for py in candidates:
        try:
            r = subprocess.run([py, "-c", "import playwright"], capture_output=True, timeout=5)
            if r.returncode == 0:
                return py
        except Exception:
            continue
    return PYTHON


def tier3_verify_web_ui():
    """Start local server, run inspection + visual review, stop server."""
    pw_python = _find_playwright_python()
    env = os.environ.copy()
    env["PYTHON"] = pw_python
    env.setdefault("VERIFY_PORT", "8092")
    start = time.time()
    try:
        r = subprocess.run(
            ["bash", "scripts/verify_web_ui.sh"],
            capture_output=True, text=True,
            cwd=REPO_ROOT, timeout=360, env=env,
        )
        elapsed = time.time() - start
        combined = r.stdout + r.stderr
        lines = combined.strip().splitlines()
        summary = lines[-1] if lines else "(no output)"
        ok = r.returncode == 0
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        ok, summary = False, "TIMEOUT after 360s"
    except Exception as e:
        elapsed = time.time() - start
        ok, summary = False, str(e)
    screenshot = os.path.join(OUTPUT_DIR, "viewer-screenshot.png")
    has_screenshot = os.path.exists(screenshot)
    review_report = os.path.join(OUTPUT_DIR, "visual-review", "report.html")
    has_review = os.path.exists(review_report)
    return ok, summary, has_screenshot, has_review, elapsed


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def write_report(report):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(REPORT_JSON, "w") as f:
        json.dump(report, f, indent=2, default=str)

    lines = []
    lines.append("# Parametric Validation Report")
    lines.append("")
    overall = "PASS" if report["passed"] else "FAIL"
    lines.append("**Overall: %s** | Tiers run: %s" % (overall, ", ".join(report["tiers_run"])))
    lines.append("")

    t1 = report.get("tier1", {})
    lines.append("## Tier 1: Fast checks (no OpenSCAD)")
    lines.append("")
    if "pytest" in t1:
        p = t1["pytest"]
        lines.append("- **pytest**: %s (%.1fs) — %s" % ("PASS" if p["passed"] else "FAIL", p["elapsed"], p["summary"]))
    if "scad_baseline" in t1:
        b = t1["scad_baseline"]
        lines.append("- **SCAD baseline**: %s (%.1fs)" % ("PASS" if b["passed"] else "FAIL", b["elapsed"]))
        if isinstance(b.get("details"), dict):
            changed = [k for k, v in b["details"].items() if v.get("status") == "CHANGED"]
            unchanged = [k for k, v in b["details"].items() if v.get("status") == "unchanged"]
            lines.append("  - Unchanged: %d parts" % len(unchanged))
            if changed:
                lines.append("  - **Changed**: %s" % ", ".join(sorted(changed)))
    if "param_audit_scad" in t1:
        a = t1["param_audit_scad"]
        lines.append("- **SCAD audit**: %s (%.1fs) — %s" % ("PASS" if a["passed"] else "FAIL", a["elapsed"], a["summary"]))
    lines.append("")

    t2 = report.get("tier2", {})
    if t2:
        lines.append("## Tier 2: STL render + bbox (local OpenSCAD)")
        lines.append("")
        if "param_audit_full" in t2:
            a = t2["param_audit_full"]
            lines.append("- **Full audit**: %s (%.1fs) — %s" % ("PASS" if a["passed"] else "FAIL", a["elapsed"], a["summary"]))
        lines.append("")

    t2b = report.get("tier2b", {})
    if t2b:
        lines.append("## Tier 2b: STL Inspection (trimesh)")
        lines.append("")
        lines.append("- **Result**: %s (%.1fs) — %s" % (
            "PASS" if t2b.get("passed") else "FAIL",
            t2b.get("elapsed", 0),
            t2b.get("summary", ""),
        ))
        insp = t2b.get("inspection")
        if insp:
            s = insp.get("summary", {})
            lines.append("- Parts: %d | Passed: %d | Failed: %d | Warnings: %d" % (
                s.get("total", 0), s.get("passed", 0), s.get("failed", 0), s.get("warnings", 0),
            ))
            lines.append("")
            lines.append("| Part | Verts | Faces | Watertight | Volume mm³ | Extents mm |")
            lines.append("|------|-------|-------|------------|------------|------------|")
            for p in insp.get("parts", []):
                if p.get("error"):
                    lines.append("| %s | — | — | — | — | %s |" % (p["part"], p["error"]))
                else:
                    wt = "yes" if p.get("is_watertight") else "no"
                    ext = "×".join("%.1f" % e for e in p.get("extents_mm", []))
                    lines.append("| %s | %d | %d | %s | %.1f | %s |" % (
                        p["part"], p.get("vertices", 0), p.get("faces", 0),
                        wt, p.get("volume_mm3", 0), ext,
                    ))
        lines.append("")

    t3 = report.get("tier3", {})
    if t3:
        lines.append("## Tier 3: Visual verification (local server + Playwright)")
        lines.append("")
        if "verify_web_ui" in t3:
            v = t3["verify_web_ui"]
            lines.append("- **verify-web-ui**: %s (%.1fs) — %s" % ("PASS" if v["passed"] else "FAIL", v["elapsed"], v["summary"]))
            if v.get("has_screenshot"):
                lines.append("- Screenshot: `output/viewer-screenshot.png`")
            if v.get("has_review"):
                lines.append("- Visual review: `output/visual-review/report.html`")
        lines.append("")

    if report.get("skipped"):
        lines.append("## Skipped")
        lines.append("")
        for s in report["skipped"]:
            lines.append("- %s" % s)
        lines.append("")

    with open(REPORT_MD, "w") as f:
        f.write("\n".join(lines))


def main():
    report = {
        "passed": True,
        "tiers_run": [],
        "skipped": [],
        "tier1": {},
        "tier2": {},
        "tier2b": {},
        "tier3": {},
    }

    # --- Tier 1: always ---
    report["tiers_run"].append("tier1")
    print("=== Tier 1: pytest ===", flush=True)
    ok, summary, elapsed = tier1_pytest()
    report["tier1"]["pytest"] = {"passed": ok, "summary": summary, "elapsed": elapsed}
    if not ok:
        report["passed"] = False
    print("  %s (%.1fs)" % ("PASS" if ok else "FAIL", elapsed), flush=True)

    print("=== Tier 1: SCAD baseline ===", flush=True)
    ok, details, elapsed = tier1_scad_baseline()
    report["tier1"]["scad_baseline"] = {"passed": ok, "details": details, "elapsed": elapsed}
    if not ok:
        report["passed"] = False
    print("  %s (%.1fs)" % ("PASS" if ok else "FAIL/CHANGED", elapsed), flush=True)

    print("=== Tier 1: SCAD audit ===", flush=True)
    ok, summary, elapsed = tier1_param_audit_scad()
    report["tier1"]["param_audit_scad"] = {"passed": ok, "summary": summary, "elapsed": elapsed}
    if not ok:
        report["passed"] = False
    print("  %s (%.1fs)" % ("PASS" if ok else "FAIL", elapsed), flush=True)

    # --- Tier 2/3: need OpenSCAD ---
    has_openscad = openscad_available()
    if has_openscad:
        report["tiers_run"].append("tier2")
        print("=== Tier 2: full param audit (STL) ===", flush=True)
        ok, summary, elapsed = tier2_param_audit_full()
        report["tier2"]["param_audit_full"] = {"passed": ok, "summary": summary, "elapsed": elapsed}
        if not ok:
            report["passed"] = False
        print("  %s (%.1fs)" % ("PASS" if ok else "FAIL", elapsed), flush=True)

        report["tiers_run"].append("tier2b")
        print("=== Tier 2b: STL inspection (trimesh) ===", flush=True)
        ok, summary, inspection, elapsed = tier2b_stl_inspect()
        report["tier2b"] = {
            "passed": ok, "summary": summary, "elapsed": elapsed,
            "inspection": inspection,
        }
        if not ok:
            report["passed"] = False
        print("  %s (%.1fs)" % ("PASS" if ok else "FAIL", elapsed), flush=True)

        report["tiers_run"].append("tier3")
        print("=== Tier 3: visual verification ===", flush=True)
        ok, summary, has_ss, has_rev, elapsed = tier3_verify_web_ui()
        report["tier3"]["verify_web_ui"] = {
            "passed": ok, "summary": summary,
            "has_screenshot": has_ss, "has_review": has_rev, "elapsed": elapsed,
        }
        if not ok:
            report["passed"] = False
        print("  %s (%.1fs)" % ("PASS" if ok else "FAIL", elapsed), flush=True)
    else:
        report["skipped"].append("Tier 2 (STL render): OPENSCAD_EXEC not available or SKIP_OPENSCAD=1")
        report["skipped"].append("Tier 3 (visual): requires OpenSCAD for server preview")
        print("=== Tiers 2-3: SKIPPED (no OpenSCAD) ===", flush=True)

    # --- Write report ---
    write_report(report)
    print("", flush=True)
    print("Report: %s" % REPORT_MD, flush=True)
    print("JSON:   %s" % REPORT_JSON, flush=True)
    print("", flush=True)
    if report["passed"]:
        print("PARAMETRIC VALIDATION PASSED", flush=True)
    else:
        print("PARAMETRIC VALIDATION FAILED", flush=True)
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
