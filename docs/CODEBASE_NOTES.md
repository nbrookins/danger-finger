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

## Magic number audit (Pass 2, 2026-04-11)

Class-level constants in `DangerFinger` and inline literals in `part_*` methods.

### Derived (applied)

| Constant | Old value | New formula | Status |
|---|---|---|---|
| `SCALLOP_HEIGHT` | `9` | `socket_bottom_cut` (property) | Applied. Exact match at defaults. **Visual review needed at extreme socket_bottom_cut** (0–60). |

### Derivation candidates (need visual review before applying)

| Constant | Value | Candidate formula | Match at defaults | Notes |
|---|---|---|---|---|
| `PEG_SUPPORT_RADIUS` | 1.2 | `tendon_hole_radius + 0.1` | Exact (1.2) | Support sleeve around peg hole; would scale with tendon size |
| `PEG_SUPPORT_SIDE_X_OFFSET` | 1.65 | `tendon_hole_radius * 1.5` | Exact (1.65) | Side support spread; proportional to tendon path |
| `PEG_SUPPORT_TRANSLATE_Z` | 3.4 | No clean formula | N/A | Closest: `tendon_hole_width * 1.545` — not clean enough |
| `ANCHOR_OFFSET_DISTAL` | -0.485 | No clean formula | N/A | Closest: `-(knuckle_clearance * 0.5 + knuckle_side_clearance)` = -0.42 |
| `TENDON_CUT_ROTATE` | -80 | Fixed angle | N/A | Empirically tuned cut angle for tendon routing |
| `SOCKET_RIDGE_SPACING_FACTOR` | 0.0015 | Fixed factor | N/A | Controls ridge texture density; print-tolerance dependent |
| `SOCKET_BOTTOM_CUT_FACTOR` | 1.2 | Fixed factor | N/A | Scales bottom cut radius; likely print-tolerance dependent |
| `SCALLOP_RADIUS_ADJ` | 1 | Fixed offset (mm) | N/A | Scallop oversizing; may relate to wall thickness |
| `TIP_FIST_TRIM_ROTATE` | -25 | Fixed angle | N/A | Range-of-motion clearance; empirically tuned |

### Inline method literals (not yet promoted to constants)

| Location | Value | Description | Candidate |
|---|---|---|---|
| `part_base` | `breather_radius_factor=0.2` | Breather hole proportion | Could be Prop if user-meaningful |
| `part_base` | `breather_height=20` | Subtractively long | Could be `socket_depth + margin` |
| `part_base` | `breather_translate_y=-10` | Alignment offset | Likely `-(socket_interface_length + margin)` |
| `part_tipcover` | `TIP_CORE_RESIZE_INSET=2` | Flattening of tip sphere | May relate to `tip_radius` |
| `tip_interface` | `tipcover_chamfer=0.6` | Interface chamfer depth | Could relate to `tipcover_thickness` |
| `part_middle` | `-3.75` in `anchor_db` | Bottom strut Y offset | Likely `-(distal_base_length * 0.625)` at defaults |
| `part_middle` | `1.3` in bumper translate | Bumper X centering | Empirical; tracks hinge radius offset |
| `bridge_anchor` | `-.5` in `height_bottom` | Strut clearance | Small tolerance offset |
| `knuckle_inner` | `1.0` in `anchor_b` Y | Bottom anchor Y nudge | Likely related to clearance |

## Downstream consumers of part output

- `web/server.py` treats stand as a standard part in render/preview flows
- `scripts/generate_static.py`, `scripts/reference_stls.py`, `scripts/regression_check.py`, `scripts/validate_formula.py` all iterate over parts
- Stand exclusion in native SCAD means "don't port it" but keep generating it from Python pipeline

## Existing infrastructure

- `benchmark-ec2` Makefile target exists for cloud benchmarking (no local render-timing target)
- `validate-formula` target exists for parameter sweep validation
- `regression-check` target for STL comparison
- `output/` directory exists and is used for build artifacts
