# CSG Modeling Patterns

This document describes the SolidPython2 idioms and custom primitives used throughout the danger-finger codebase. Read this before modifying geometry code in `finger.py` or `finger_base.py`.

---

## SolidPython2 basics

The project uses [SolidPython2](https://github.com/jeff-dh/SolidPython2), which generates OpenSCAD code from Python. CSG operations:

| Python | OpenSCAD | Meaning |
|--------|----------|---------|
| `a + b` | `union()` | Combine volumes |
| `a - b` | `difference()` | Subtract b from a |
| `a * b` | `intersection()` | Keep only overlap |
| `hull()(a, b)` | `hull()` | Convex hull of a and b |
| `a.rotate((rx, ry, rz))` | `rotate()` | Euler rotation (degrees) |
| `a.translate((x, y, z))` | `translate()` | Move |
| `a.scaleX(f)` / `.resize(...)` | `scale()`/`resize()` | Scale |
| `scad_render(obj)` | — | Generate .scad string |
| `obj.render()` | `render()` | Force evaluation (CSG cache) |

SolidPython2 builds a lazy tree. `.render()` evaluates it, which is important for complex boolean operations (avoids re-computation). The `build()` loop calls `.render()` on each model.

---

## Custom primitives (defined in `finger_base.py`)

### `rcylinder(r, h, rnd=0, center=False)`

Rounded-edge cylinder. Uses `rotate_extrude(offset(r=rnd)(offset(delta=-rnd)(square)))` to create filleted edges.

- `rnd=0`: Falls back to plain `cylinder()`
- Used extensively for hinges, struts, bumpers

### `rcube(size, rnd=0, center=True)`

Rounded-edge cube (4 edges rounded). Intersects a cube with a resized cylinder.

- `round_ratio = (1-rnd) * 1.1 + 0.5` controls how much the cylinder crops
- Used for struts, braces

### `rcubecyl(h, w, l, t, rnd=None, rnd1=None, rnd2=None, center=True)`

Hybrid cuboid-cylinder. The most complex primitive. Creates a rounded shape by hulling two scaled copies of a cylinder:

```python
anchor1 = cy.scaleX(.5).translateX(t / 2.0)
anchor2 = cy.scaleX(.5).translateX(-t / 2.0)
hub = hull()(anchor1, anchor2, cy)
return hub.rotate((90, 0, 0))
```

- `h`: height (cylinder axis), `w`: width (cylinder radius), `l`: length (resize X), `t`: hull offset
- `rnd1`/`rnd2`: Per-side rounding (left half / right half). Allows one end to be round and the other flat.
- Used for bridges and bumper shells

### `trim(x=0, y=0, z=0, center=True, offset=(0,0,0))`

Returns a transform function that intersects the object with a cutting cube. Axes set to 0 get a very large value (10000) so they don't clip.

```python
trim(x=10)(obj)            # functional style
obj.trim((10, 0, 20))      # method style (monkey-patched onto OpenSCADObject)
obj.trim((10, 0, 20), offset=(5, 0, 0))  # offset the cutting cube
```

### `flaredcyl(r, h, fr, fh)`

Flared cylinder using double-offset `rotate_extrude`. Creates a cylinder that widens at one end. Used for hinge inset flares.

### `circular_text(txt, radius, size, thickness, spacing, rot, reverse=False)`

Wraps text around a circle. Each character is positioned at an angle computed from character width heuristics (`WIDTH_ADJUSTMENTS` in `constants.py`). Used on the display stand.

---

## Key modeling patterns

### Hull pair pattern

The most common pattern. Two primitives are hulled together to create a smooth transition:

```python
mod_main = (mod_core + mod_hinge).hull() + (mod_tunnel + mod_core).hull()
```

This creates the base's body by hulling the core cylinder with the hinge, then hulling the tunnel with the core. The `+` combines both hulls into the final shape.

**Why**: Hulling two offset shapes creates a smooth, convex transition that is structurally strong and easy to print. Direct union of complex shapes often leaves internal voids or sharp transitions.

### Subtractive modeling

Most parts follow: build up material, then cut away features.

```python
final = (mod_main + mod_interface
         - mod_plug_cut      # subtract plug holes
         - mod_tip_hole       # subtract peg hole
         - mod_hinge_cut      # subtract hinge clearance
         - mod_pin            # subtract pin hole
         - cut[1].translate(...)  # subtract bridge cut
        ) - mod_extra + mod_washers - mod_pin
```

The order matters: additions first, then subtractions. Some features (like washers) are added after initial subtractions because they need to sit in the clearance zone.

### Orient dispatch pattern

Many methods take an `orient` parameter (an `Orient` IntFlag) and branch on it:

```python
if orient == Orient.PROXIMAL:
    trim_dim = self.intermediate_proximal_height
    trim_z = self.knuckle_width_[Orient.PROXIMAL] - self.knuckle_rounding * 4
else:  # DISTAL
    trim_dim = self.intermediate_distal_height
    trim_z = self.intermediate_width_[Orient.DISTAL]
```

The `orient_pair()` helper creates `{Orient.DISTAL: val, Orient.PROXIMAL: val}` dicts for computed properties that differ by orientation.

`Orient` is an `IntFlag`, so values can be combined: `Orient.PROXIMAL | Orient.OUTER` means "the proximal, outer portion" — used heavily in `bridge()` and `bridge_anchor()`.

### Computed property convention

Properties ending with `_` are computed (read-only):

```python
intermediate_width_ = property(lambda self: orient_pair(
    self.intermediate_distal_width_, self.intermediate_proximal_width_))
tip_radius = property(lambda self: self.tip_circumference / math.pi / 2)
```

These derive from user-facing `Prop` parameters. Never set them directly.

### Color coding

Each `part_*` method applies a `.color(PART_COLORS[name])` at the end:

```python
return final.color(PART_COLORS["base"])
```

`PART_COLORS` maps part names to `[r, g, b]` arrays (0-1 range) used by both OpenSCAD's `color()` command and the web viewer's material colors.

### Debug pattern

During development, `.debug()` (renders as `#` in OpenSCAD = transparent highlight) can be chained on any object:

```python
mod_hinge_cut.debug()  # show this subtraction as transparent
```

Many lines have `#.debug()` comments — these are inactive debug calls that can be re-enabled.

---

## Bridge and tunnel construction

The bridge/tunnel system is the most complex geometry in the codebase. It routes the tendon through the hinge zones.

### `bridge(length, orient, tunnel_width)`

Builds a tendon tunnel for external hinges (base and tip). Uses `bridge_anchor()` to create 8 anchor points (4 positions x 2 sides), hulls them, then subtracts a cylindrical channel.

The orient is composite: `Orient.PROXIMAL | Orient.OUTER` means "proximal end, outer part (base or tip side)".

### `bridge_anchor(orient, length, top, inside, shift, rnd)`

Calculates one anchor point for the bridge hull. Returns a small cylinder or sphere positioned at the correct height, width, and depth for the given orientation. The `shift` parameter mirrors the point across Z (left vs right side).

This method contains the most orientation-dependent branching in the codebase — it handles 8 combinations of orient, top/bottom, inside/outside, and distal/proximal.

### `make_bridge(orient, ...)`

A newer, simpler bridge method using `rcubecyl`. Used by base, tip, and middle (COVER/FULL bumper). Creates a single rounded cuboid, scales it, trims it, and subtracts a cylinder channel.

### `create_bridge(r, length, width, height, ...)`

Middle-section tunnel. Similar to `bridge()` but with different anchor geometry. Has a `sharp=True` mode for simpler variants.

---

## Monkey-patching

`finger_base.py` patches `OpenSCADObject` to add method-style `.trim()`:

```python
from solid2.core.object_base.object_base_impl import OpenSCADObject
OpenSCADObject.trim = _open_scad_trim
```

This allows `obj.trim((x, y, z))` instead of `trim(x, y, z)(obj)`.

---

## Common pitfalls

1. **Modifying a primitive affects all callers**: `rcylinder`, `rcubecyl`, `trim`, etc. are used throughout. Changes to these functions will affect every part.

2. **Hull order doesn't matter, but addition/subtraction order does**: `hull()(a, b)` is the same as `hull()(b, a)`, but `(a + b) - c` is different from `(a - c) + b`.

3. **`.debug()` in production**: Leaving `.debug()` active in a `build()` call makes the part transparent in OpenSCAD previews. The `.debug()` calls are commented out but easy to accidentally uncomment.

4. **`.render()` placement**: Calling `.render()` too early freezes the CSG tree, preventing further boolean operations. The `build()` loop calls it at the right time. Don't add extra `.render()` calls inside `part_*` methods.

5. **Scale vs resize**: `.scaleX(f)` multiplies by factor f. `.resizeX(dim)` sets absolute dimension. `.resize(0, 0, z)` only resizes Z — 0 means "keep original".
