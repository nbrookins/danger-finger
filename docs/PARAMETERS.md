Parametrized magic numbers
==========================

Several hardcoded numbers in `danger/finger.py` were made configurable via `DangerFingerParams` so you can tune behavior without editing source.

Added parameters (defaults chosen to preserve current behavior):

- `proto_shell_sphere_radius` (default 5)
- `proto_shell_sphere_y_factor_a` (default 3.5)
- `proto_shell_sphere_y_factor_b` (default 10.0)
- `proto_shell_sphere_z` (default 9)
- `proto_shell_cut_cube_x`, `proto_shell_cut_cube_y`, `proto_shell_cut_cube_z` (defaults 30,20,30)
- `proto_shell_cut_translate_y` (default -35)
- `tip_proto_cube_x`, `tip_proto_cube_y`, `tip_proto_cube_z` (8,20,20)
- `tip_proto_translate_x_offset` (default 7)
- `tip_proto_bottom_cut_*` (defaults 10,50,30 and translate_x_offset -0.5)
- `cut_fist_radius_offset`, `cut_fist_h`, `cut_fist_scale_y`, `cut_fist_translate_y1`, `cut_fist_translate_y2`, `cut_fist_translate_z`, `cut_fist_rotate` (control the fist cut geometry)
- `bridge_cut_a_y_offset`, `bridge_cut_b_y_offset`, `bridge_ledge` (control bridge cut translations and ledge)

Usage
-----

Adjust parameters either programmatically (e.g. `finger.proto_shell_sphere_radius = 8`) or through any provided GUI/parameter interface before rendering to experiment with variants.

Preview vs print orientation
----------------------------

- **`_rotate_offsets`** (in `danger/finger_params.py`): Applied at export so STLs are in print orientation for slicing. Do not change for preview display.
- **`_translate_offsets["all"]`**: Used by part_all and assembly; do **not** use for viewer layout or you will break the all.stl output.
- **`_preview_position_offsets`**: Viewer-only positions (part name → (x,y,z)). Used only by the web API for preview; part_all and STL export are unchanged. Proximal→distal along +Y; linkage behind finger (-Z). Tune here to fix stacked preview without touching `_translate_offsets`.
- **`_preview_rotate_offsets`**: Per-part (rx, ry, rz) in degrees applied only in the web viewer so the same STLs appear as an assembled finger. Tune these if preview alignment looks wrong. `middle` is set to `(-90, 50, -90)` (approximate inverse of its print rotation `(90, -50, 90)`; see `docs/VIEWER_ASSEMBLY.md` section 6).
- **`_preview_hidden`** *(planned)*: Set of part names (e.g. `{"stand"}`) hidden by default in the preview UI.
- **`_preview_plug_instances`**: List of four `{ "position": (x,y,z), "rotation": (rx,ry,rz) }` entries for the four plug instances (proximal L/R, distal L/R). Same plug STL is shown four times in the viewer at these positions/rotations so plugs appear in their tip holes.
- **`_preview_position_override`** *(planned)*: Optional overrides on top of `_preview_position_offsets` for a single part (viewer only).

Notes
-----

These changes are intentionally conservative: defaults reproduce prior behavior. If you'd like I can continue and parameterize additional hardcoded values (nail cut offsets, tunnel helper constants, and more).

---

See also
--------

- [Architecture](ARCHITECTURE.md) — system pipeline, class hierarchy, build flow
- [Parts Anatomy](PARTS_ANATOMY.md) — physical design of each part and known TODOs
- [CSG Patterns](CSG_PATTERNS.md) — SolidPython2 idioms and custom primitives
- [Viewer Assembly](VIEWER_ASSEMBLY.md) — how the web viewer positions and rotates parts
- [Product](PRODUCT.md) — product requirements and design decisions