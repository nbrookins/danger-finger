# Direct STL Inspection Tier

**Date**: 2026-04-12
**Status**: completed

## Goal
Replace the fragile browser-based visual pipeline (Tier 3) as the primary geometry validation with direct STL inspection using trimesh. The browser pipeline becomes optional/supplementary for UI regression only. The agent can now validate geometry without a web server, browser, WebGL, or timing-sensitive async flows.

## What trimesh gives us over hand-rolled STL parsing
- Manifold/watertight checks (is_watertight)
- Volume and surface area
- Triangle count, vertex count
- Euler number / genus
- Convex hull comparison
- Cross-sections at arbitrary planes
- Assembly collision detection (mesh-mesh, not just bbox)
- All pure Python, no external processes, sandbox-friendly

## New Tier structure

| Tier | Name | What | Speed |
|------|------|------|-------|
| 1 | Unit tests | pytest + SCAD baseline + SCAD audit | ~100s |
| 2 | STL render + bbox | param_audit.py (existing) | ~15s |
| 2b | **STL inspection** (NEW) | trimesh-based deep geometry checks | ~5s |
| 3 | Visual UI (optional) | Browser screenshots via Playwright | ~150s |

## Tier 2b checks (scripts/stl_inspect.py)

For each STL produced by preview:

1. **Load**: trimesh.load(stl_path) — validates parseable
2. **Manifold**: mesh.is_watertight — critical for 3D printing
3. **Volume**: mesh.volume > 0 and within expected range per part
4. **Dimensions**: mesh.bounding_box.extents — cross-check with existing bbox
5. **Triangle count**: mesh.faces.shape[0] — sanity range per part
6. **Assembly fit**: load all parts with position/rotation offsets from previewConfig, check for excessive overlap via mesh bounding box overlap (fast) or convex hull intersection (thorough)

Output: JSON report with per-part metrics + pass/fail + an ASCII summary the agent can read without screenshots.

## Steps
1. Add trimesh to requirements-dev.txt
2. Create scripts/stl_inspect.py with the checks above
3. Integrate into parametric_report.py as Tier 2b
4. Update Makefile targets
5. Create baseline expectations JSON (expected ranges per part)
6. Update docs and rules

## Key decisions
- trimesh over numpy-stl: trimesh has manifold checks and assembly tools; numpy-stl is bbox-only
- Tier 2b not Tier 3: geometry validation should run before and independently of the browser
- Keep visual pipeline: it validates the UI, not geometry — different purpose
- No new external processes: trimesh is pure Python (with optional numpy acceleration)

## Files affected
- `requirements-dev.txt` — add trimesh
- `scripts/stl_inspect.py` — new: main inspection script
- `scripts/parametric_report.py` — add Tier 2b
- `danger/geometry_checks.py` — add trimesh-based checks alongside existing
- `Makefile` — update test-parametric target
- `.cursor/rules/` — new rule for STL inspection
- `docs/` — update architecture docs

## Outcome
- Tier 2b runs in 0.8s, produces per-part metrics table in the markdown report
- 9/9 parts pass; 3 watertight warnings (tip, tipcover, socket — known OpenSCAD edge cases)
- Full pipeline now: Tier 1 (99s) → Tier 2 (13s) → Tier 2b (0.8s) → Tier 3 (147s) = ~260s total
- Agent can now validate geometry by reading `output/stl-inspection.json` — no screenshots needed
- Visual pipeline (Tier 3) remains for UI regression testing
