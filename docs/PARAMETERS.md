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

Notes
-----

These changes are intentionally conservative: defaults reproduce prior behavior. If you'd like I can continue and parameterize additional hardcoded values (nail cut offsets, tunnel helper constants, and more).