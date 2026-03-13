# Codebase Notes

Learnings discovered during SCAD optimization and customizer planning (2026-03-12).

## Geometry and rendering

- `finger.py` contains 12 `part_*` methods and ~38 helper functions (~780 lines)
- `finger_params.py` defines 93 `Prop` parameters (plus 1 in `finger.py`: `peg_hollow_radius`)
- Render quality uses `$fa`/`$fs` globally (set in SCAD header), NOT `$fn`
  - SolidPython2's `_fn=` parameter emits per-primitive `$fn=` which overrides the global setting
  - Mixed `$fn` and `$fa/$fs` can produce visual seams at primitive boundaries
  - Only use `_fn=` on cutting geometry (invisible in final output) or hull anchors (too small to see)
- `RenderQuality.EXTRAHIGH` (value 8) exists in `constants.py` but has NO mapping in the `fs_` or `fa_` dicts in `finger_params.py` -- using it will cause a `KeyError`

## Known hotspots

- `_socket_bottom()` (line 460): loop runs `socket_depth` (default 34) individual `rotate_extrude()` calls -- the #1 render-time hotspot
- `part_tipcover()` fingerprints (line 366): ~19 individual cube subtractions from a sphere
- Bridge/tunnel system (`create_bridge`, `make_bridge`): most complex CSG geometry, uses multi-sphere hulls with small anchor spheres

## Parameter system

- `Prop` class in `Params.py` supports: val, minv, maxv, doc, adv (advanced), hidden, custom (CustomType), setter
- `CustomType` enum (DROPDOWN, SLIDER, SPINNER, CHECKBOX, TEXTBOX) exists but is only used by the web UI, not for SCAD output
- `Params.open_config` does direct `params[k] = config[k]` with no migration path -- if a Prop name changes, saved configs silently fall back to defaults
- No preset/sizing infrastructure exists; must be built from scratch

## Regression testing

- `scripts/regression_check.py` uses exact SHA-256 hashes of STL files
- `scripts/reference_stls.py` generates reference STLs at default params
- Any change to tessellation (quality settings, $fn overrides) will change hashes even when geometry intent is unchanged
- For optimization work, need geometry-aware validation (bounding box, volume, visual diff)

## Downstream consumers of part output

- `web/server.py` treats stand as a standard part in render/preview flows
- `scripts/generate_static.py`, `scripts/reference_stls.py`, `scripts/regression_check.py`, `scripts/validate_formula.py` all iterate over parts
- Stand exclusion in native SCAD means "don't port it" but keep generating it from Python pipeline

## Existing infrastructure

- `benchmark-ec2` Makefile target exists for cloud benchmarking (no local render-timing target)
- `validate-formula` target exists for parameter sweep validation
- `regression-check` target for STL comparison
- `output/` directory exists and is used for build artifacts
