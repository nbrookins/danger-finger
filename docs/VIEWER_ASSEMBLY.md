# Viewer assembly system — coordinate reference and known behaviours

This document captures how the web viewer assembles the finger from individual print-oriented STL files, and how `stl_viewer.min.js` actually transforms each mesh. It is the authoritative reference for setting `_preview_position_offsets`, `_preview_rotate_offsets`, and `_preview_plug_instances` in `danger/finger_params.py`.

---

## 1. The pipeline from SCAD to viewer

```
part_xxx()          -> natural/assembled geometry (SCAD coordinate space)
  |  build()
rotate(rotate_offsets[name])   -> print orientation (optimal for FDM slicing)
  |  write_file -> output/{name}.stl

HTTP: /render/{name}.stl -> browser -> stl_viewer.add_model(...)
  -> center_models (bbox center -> local origin 0,0,0)
  -> rotate (rotateAroundWorldAxis by preview_rotate_offsets[name])
  -> set_position from mod_loaded (preview_position_offsets[name])
```

The viewer reconstructs the assembled finger from print-oriented STLs. Positions and rotations are viewer-only.

---

## 2. stl_viewer.min.js — actual behaviour (confirmed from source)

### 2.1 Geometry centering

`center_models` defaults to `true`. After loading the STL, the library calls `geometry.center()` which translates all vertices so the **bounding box center becomes the geometry local origin (0,0,0)**. The original SCAD/STL coordinate system is discarded.

**Consequence**: `_preview_position_offsets` values must be the world-space position of each part's bounding box center in assembled finger space — not SCAD translate offsets.

### 2.2 Rotation

Rotation is applied via `rotateAroundWorldAxis(mesh, worldAxis, angle)` which pre-multiplies the mesh matrix by a world-space rotation. Because geometry was centered first, this effectively **rotates around the part's own center**. Values are applied as successive X -> Y -> Z world-axis rotations (in degrees; `index.html` calls `degtorad`).

### 2.3 Position ordering — the mod_loaded override

`set_model_custom_props` (synchronous in `add_model`):
1. Sets `mesh.position` from `add_model` params.
2. Calls `rotate(...)`.

`mod_loaded` (async callback when STL loads):
3. Calls `set_position(id, pos[0], pos[1], pos[2])` — **overrides** position with `preview_position_offsets`.

Net effect: geometry is centered, rotated around its own center, then translated to `preview_position_offsets`.

### 2.4 DEBUG_PREVIEW_SCALE is a no-op

`add_model` multiplies position by `DEBUG_PREVIEW_SCALE`, but `mod_loaded` always overrides with the unscaled value. Has no visual effect.

---

## 3. How assembled positions are derived

The correct `_preview_position_offsets[name]` is the **world-space location of the bounding box center of `name` in assembled (natural/pre-print-rotation) orientation**.

### 3.1 Natural assembled coordinate system

The finger's natural coordinate space (pre-print-rotation, default params):

| Part     | Y span (approx)  | Bbox center Y |
|----------|-----------------|---------------|
| socket   | -46 to -5        | approx -25    |
| base     | -11 to +5        | approx -3     |
| middle   | -5  to +29       | approx +12    |
| tip      | +19 to +33       | approx +26    |
| tipcover | +30 to +48       | approx +39    |
| linkage  | centered Y=0, Z offset=+20 | approx (0,-3,20) |

Y=0 is the **proximal hinge** (where base meets middle).

`part_tip()` returns `final.translate((0, intermediate_length, 0))` — this translation is **baked into the geometry** before print rotation, so the tip's natural bounding box starts at Y approx `intermediate_length`.

### 3.2 Correct values from v5.1 STL measurements

v5.1 STLs were in natural/assembled orientation (no print rotations) and serve as ground-truth:

```
socket:   center approx (0.1, -24.8, -0.1)
base:     center approx (0.0,  -2.7,  0.0)
middle:   center approx (1.0,  11.6,  0.0)
tip:      center approx (1.2,  26.3,  0.0)
tipcover: center approx (0.0,  39.0,  0.0)
```

These scale with `intermediate_length` and other params. Ideally derived dynamically from built geometry.

---

## 4. Preview positions — fix applied (v5.3)

`_preview_position_offsets` updated to assembled bbox centers from section 3.2. The legacy 35 degree Z rotation was removed from tip and tipcover in `_preview_rotate_offsets` (it matched `preview_rotate=True` SCAD behaviour, not the current `preview_rotate=False` reference).

Long-term: derive positions dynamically from built geometry so they stay correct as parameters change.

---

## 5. SCAD all view vs viewer

### The preview_rotate flag

`preview_rotate = False` is hard-coded in `finger_params.py`. With this flag:
- `_part_composite` skips `_rotate_offsets["all"]` per-part rotations and the tip special transform.
- Parts appear in natural/assembled orientation at `translate_offsets["all"]` (mostly zeros).
- The output PNG (`dangerfinger_v*_all.png`) is the canonical visual reference.
- The diagonal appearance is OpenSCAD's default camera angle, not a physical rotation.

---

## 6. How preview_rotate_offsets is derived

Each part's print rotation is in `_rotate_offsets[name]` (single tuple). The preview rotation is the approximate inverse.

| Part     | Print rotation   | Preview rotation   | Notes                                      |
|----------|-----------------|-------------------|--------------------------------------------|
| socket   | (-90, 0, 0)      | (+90, 0, 0)       |                                            |
| base     | (+90, 0, 0)      | (-90, 0, 0)       |                                            |
| tip      | (-90, 0, 0)      | (+90, 0, 0)       | legacy 35 deg Z removed                   |
| tipcover | (+90, 0, 0)      | (-90, 0, 0)       | legacy 35 deg Z removed                   |
| linkage  | (0, -180, 0)     | (0, +180, 0)      |                                            |
| middle   | (90, -50, 90)    | (-90, +50, -90)   | multi-axis; true inverse is non-trivial    |

For multi-axis Euler rotations, negating each component is approximate. Verify visually.

---

## 7. OpenSCAD on macOS ARM64

Qt runtime check fails on native ARM64. Fix in `danger/Scad_Renderer.py`: prepend `arch -x86_64` on `darwin/arm64` (Rosetta 2). Disable with `OPENSCAD_USE_ROSETTA=0`. Headless PNG needs Xvfb (`DISPLAY=:99`).

---

## 8. Plug instances

Single STL (`plug.stl`) displayed four times via `_preview_plug_instances`:

```python
_preview_plug_instances = [
    {"position": (0,  0, -8.6), "rotation": (0,   0, 0)},   # proximal left
    {"position": (0,  0,  8.6), "rotation": (0, 180, 0)},   # proximal right
    {"position": (0, 24, -7.5), "rotation": (0,   0, 0)},   # distal left
    {"position": (0, 24,  7.5), "rotation": (0, 180, 0)},   # distal right
]
```

Y=0 is the proximal hinge; Y=24 (= `intermediate_length`) is the distal hinge.
