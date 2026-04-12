# Parametric QA Stabilization Plan

**Date**: 2026-04-11  
**Status**: in-progress

## Goal
Make the first serious pass on parametric robustness for the model by focusing on common sizing plus closely related fit and clearance parameters, using a repeatable audit loop instead of one-off visual tweaks. The work builds on the existing validation, regression, and viewer tooling instead of replacing it.

## Steps
1. Repair the baseline test drift around stale parameter expectations and lock a trustworthy default baseline.
2. Define a reusable common-plus-fit human-range profile matrix for the first wave.
3. Build a multi-profile param audit harness with geometry metrics, rendered artifacts, and Make targets.
4. Trace failures through the full parameter-to-geometry path and rank hotspots.
5. Fix one failure family at a time, rerunning targeted audits and default regressions after each change.
6. Add targeted assembly and preview validation for the first-wave profiles.
7. Document the workflow and formalize only the minimum rules and skills that prove useful.

## Key decisions
- Start with common sizing plus nearby fit and clearance parameters, not the entire parameter surface.
- Prefer deriving formulas from existing physical dimensions over adding new independent `Prop`s unless the value is truly user-meaningful.
- Keep exact STL hash checks for unchanged defaults, but use geometry-aware validation for profile sweeps.
- Keep preview verification separate from print-geometry validity, while still including it in the first-wave loop.

## Files affected
- `danger/finger.py` — main geometry formulas and hardcoded literals
- `danger/finger_base.py` — build orchestration and preview-related transforms
- `danger/finger_params.py` — parameter metadata, warnings, and first-wave scope
- `tests/test_params.py` — stale parameter expectations
- `tests/test_more_params.py` — stale parameter expectations
- `tests/test_param_sweep.py` — sweep coverage expansion
- `tests/profiles.py` — first-wave profile matrix
- `scripts/validate_formula.py` — current sweep foundation
- `scripts/param_audit.py` — new multi-profile audit harness
- `danger/geometry_checks.py` — metric and assembly primitives
- `scripts/regression_check.py` — exact-hash defaults plus geometry-aware complements
- `scripts/inspect_ui.py` — viewer screenshot and report path
- `Makefile` — one-command local verification loop
- `docs/PARAMETERS.md` — scope and parameter semantics
- `docs/CODEBASE_NOTES.md` — validation learnings and known hotspots

## Outcome
Progress so far:
- Repaired the Phase 0 baseline by replacing stale test expectations with assertions against live derived behavior and by fixing model robustness for `peg_hollow_radius`, float-valued `linkage_holes`, and `tip_print_width=0`.
- Added `tests/profiles.py` and `tests/test_profiles.py` for the first-wave common-plus-fit profile matrix; local param/profile suites now pass in a workspace `.venv`.
- Added `scripts/param_audit.py` plus `make param-audit-scad`, `make param-audit`, and `make param-audit-visual`. Verified the SCAD-only audit path and report generation locally.
- Render-backed audit remains blocked on this machine until either Docker Desktop is running or a working local OpenSCAD path is available; local native OpenSCAD still fails with the documented macOS Qt incompatibility.

**Pass 2 (2026-04-11):**
- 261 tests pass (Python 3.9), covering all 8 geometry parts, 10 param interaction pairs, and 7 profiles with full validation.
- `validate_params()` expanded with 10 new constraints (tunnel, linkage, bumper, socket interface, bottom strut, tip print).
- `SCALLOP_HEIGHT` derived as `socket_bottom_cut` property — needs visual review at socket_bottom_cut extremes.
- 9 remaining constants + 9 inline literals documented with candidate formulas in `docs/CODEBASE_NOTES.md`.
- Fixed `Prop` Python 3.9 `staticmethod` descriptor compatibility.
- See `2026-04-11-parametric-pass2-automated.md` for full details.
