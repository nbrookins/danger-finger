# Fix Preview Position Offsets & Add 3D Compass

**Date**: 2026-03-17
**Status**: completed

## Goal
Fix Y-axis part compression and plug misalignment in the 3D preview, and add an XYZ axis compass widget for spatial reference.

## Steps
1. Add 3D axis compass widget (ArrowHelper + CanvasTexture labels) to bottom-left corner of viewer
2. Download default STL files and measure bounding boxes with numpy-stl
3. Compute rotated bounding box Y extents for each part after the viewer's center→rotate→reposition pipeline
4. Identify overlaps: base-middle 11.6mm (should be ~5mm), middle-tip 9.1mm, tip-tipcover 4.1mm
5. Calculate corrected Y position offsets that align hinge axes at Y=0 (proximal) and Y=int_len (distal)
6. Remove +1.5mm Y nudge from plug instance positions (centers plugs on hinge holes)
7. Test new offsets via Playwright route interception before committing
8. Update static fallback offsets, compute formulas, and plug instance methods
9. Deploy and verify with screenshots

## Key decisions
- Used STL bounding-box measurement (numpy-stl) to get exact rotated bbox extents rather than guessing offsets
- Removed plug Y nudge entirely (was knuckle_plug_radius/2) — plugs center directly on hinge axis
- Compass uses a second WebGLRenderer + OrthographicCamera synced to main camera rotation
- Position formulas rewritten with empirical scaling factors (prox_h * 0.8, sock_depth * 0.7, etc.)

## Files affected
- `web/stl_viewer.js` — added _initCompass(), _makeLabel(), _renderCompass() methods; extended THREE destructuring
- `danger/finger_params.py` — updated _preview_position_offsets, _preview_plug_instances, compute_preview_positions(), compute_preview_plug_instances()
- `web/static/config-bootstrap.js` — regenerated with corrected offsets

## Outcome
- Y-axis overlaps reduced to natural hinge interleave levels (~5-6mm)
- Plugs centered on hinge holes instead of sitting 1.5mm above
- Compass visible in bottom-left corner with labeled red X, green Y, blue Z axes
- All changes verified with Playwright headless screenshots
