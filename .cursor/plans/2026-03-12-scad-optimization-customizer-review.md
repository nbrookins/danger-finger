# SCAD Optimization + Customizer: Consolidated Review

**Date**: 2026-03-12
**Status**: in-progress
**Source**: 4 independent agent reviews of Plans 1-3

## Review sources

- [Plan review](3088e612-bf5a-47c4-b2e6-38df0def1f59) -- deep codebase analysis with subagents
- [Contract-focused review](8e4d0cc5-a590-450e-80d5-b5b008f20197) -- interface contracts and sequencing
- [Skip-stand review](a26e8b4f-1d5a-40bb-9aeb-55eafe542d4d) -- downstream impact analysis
- [Schema stability review](a33918ea-25bb-4155-af60-be852e1ce13b) -- preset versioning and parameter schema

## User decisions (from review feedback)

| Question | Decision |
|----------|----------|
| "Skip stand" meaning | Don't port stand to native OpenSCAD; keep it in the Python pipeline |
| Split Plan 2 | Yes -- presets.py first (low risk), then socket SCAD + bundles separately |
| Web UI presets | Add a preset dropdown to the web UI (in scope) |
| STL generation compute | Run on EC2 |

---

## Unanimous findings (all 4 reviewers)

### 1. Plan 3 is NOT independent of Plan 2

Plan 3 claims independence but reuses socket modules from Plan 2 and could silently break Plan 2's preset schema if it renames params or restructures data.

**Resolution**: Acknowledge the dependency explicitly. Freeze the socket module API and preset schema before Plan 3 starts. Add a contract doc (`docs/SOCKET_PRESET_CONTRACT.md`).

### 2. Regression testing is too strict for optimization work

`scripts/regression_check.py` uses exact SHA-256 hashes of STL files. Any change to tessellation ($fn, $fs, $fa) changes hashes even when design intent is unchanged.

**Resolution**: For Plan 1, use geometry-aware validation:
- Bounding box comparison
- Volume comparison (OpenSCAD can report this)
- Multi-angle visual diff (render to PNG, compare)
- Reserve exact hash checks for non-optimization changes

### 3. Missing exit criteria

No plan defines measurable "done" conditions.

**Resolution**: Add per-plan KPIs:
- Plan 1: Render time reduction % at MEDIUM/EXTRAMEDIUM; regression-check pass (geometry-aware)
- Plan 2A (presets): `get_preset_params()` covers all 20 configs; preset dropdown works in web UI
- Plan 2B (socket SCAD): Socket renders <10s at MEDIUM; validate-socket-scad passes (bbox + volume + visual)
- Plan 2C (bundles): All 160 STLs render successfully at HIGH on EC2
- Plan 3: Each part <30s at MEDIUM; full customizer <30s; Python pipeline unchanged

### 4. Interface contract needed before Plan 3

**Resolution**: At the end of Plan 2, freeze:
- Parameter names (no renames after this point)
- Preset JSON format: `{"version": 1, "size": "M", "finger": "index", "params": {...}}`
- Socket module API: inputs/outputs documented

### 5. Bounding-box validation alone is insufficient

**Resolution**: Strengthen validation in Plans 2 and 3:
- Bounding box (planned)
- Volume comparison (add)
- Multi-angle PNG visual diff (add)
- For socket: interface mating test (render socket + base, verify assembly)

### 6. Effort estimates are optimistic

| Plan | Original | Reviewer consensus |
|------|----------|-------------------|
| 1 (Optimizations) | ~1 day | ~1-2 days (reasonable with benchmark) |
| 2 (Socket + Presets) | ~2 days | ~3-4 days (now split into 3 sub-PRs + web UI) |
| 3 (Full Customizer) | ~3-5 days | ~5-8 days (bridge/tunnel system is complex) |

---

## Majority findings (3/4 reviewers)

### 7. Mixed $fn/$fa/$fs strategy needs documenting

Plan 1B/1C introduces per-primitive `$fn` alongside global `$fa/$fs`. SolidPython2's `_fn=` emits `$fn=` which overrides the global quality. This can produce visual seams where adjacent primitives have different tessellation.

**Resolution**: Document in the plan that `_fn` is only applied to:
- Cutting geometry (invisible in final output)
- Hull anchor spheres (too small to see tessellation)
- Never on visible surface geometry

### 8. Part count error

Plan says "iterate over 8 parts (skip STAND)" but there are 12 `part_*` methods: socket, base, middle, tip, tipcover, linkage, plug, plugs, peg, pins, stand, bumper.

**Resolution**: Benchmark all parts except stand. Note that `part_plugs()` calls `part_plug()` 4x.

### 9. 94 params is too many for MakerWorld customizer

MakerWorld's customizer UI becomes unusable above ~20-30 parameters.

**Resolution**: Plan 3 should expose ~15-20 user-facing params in `/* [Sizing] */` and `/* [Options] */`. The rest go in `/* [Advanced] */` (hidden by default) or `/* [Hidden] */`.

---

## Notable individual findings

### 10. EXTRAHIGH quality has no $fa/$fs mapping

`RenderQuality.EXTRAHIGH` (value 8) exists in `constants.py` but is missing from the `fs_` and `fa_` property dicts in `finger_params.py`. Using it would cause a `KeyError`. Not blocking for these plans, but should be fixed as tech debt.

### 11. 1A is a hard prerequisite for Plan 2

The socket customizer SCAD would need to replicate either the old N-rotate_extrude loop or the new single composite approach. Doing 1A first means the socket SCAD is simpler and faster.

### 12. Preset schema versioning

`Params.open_config` does `params[k] = config[k]` with no migration path. If a Prop name changes, saved presets silently fall back to defaults. Add schema versioning from the start.

### 13. STL compute cost

160 renders at HIGH quality, estimated 3-6 hours. Will run on EC2 per user decision.

### 14. Maintenance workflow for generated SCAD

Plan 3's `generate_customizer_scad.py` needs a maintenance story: CI check that generated SCAD matches Python output, `make regenerate-customizer` target, workflow docs for adding new Prop.

---

## Updated plan structure (post-review)

Based on review feedback and user decisions:

```
Plan 1:   Render Optimizations (benchmark + 1A-1D)
Plan 2A:  Size Presets (presets.py + web UI dropdown)           -- low risk
Plan 2B:  Socket Customizer SCAD (native OpenSCAD socket)       -- medium risk
Plan 2C:  Preset STL Bundles (EC2 generation + packaging)       -- depends on 2A + 2B
Plan 3:   Full Native OpenSCAD Customizer                       -- depends on 1, 2B
```

---

## Codebase learnings saved from reviews

See: `docs/CODEBASE_NOTES.md` (to be created with these findings)
