# Render UX Improvements and Flex Preview Feature

**Date**: 2026-03-12
**Status**: in-progress

## Goal
Three UI improvements: (1) show a rendering-in-progress overlay on the viewer when a render is in flight, (2) collapse standard parameters by default so the form is less overwhelming, (3) add a "Flex" slider that curls the finger by rotating parts around the two hinge pivot points in the 3D preview.

## Steps
1. Add render progress overlay (dim + spinner) inside the viewer #wrap div
2. Wire showRenderProgress(true/false) in app.js triggerRender/onPreviewReady
3. Wrap standard params in Bootstrap collapse (initially collapsed)
4. Add set_rotation() method to stl_viewer.js
5. Add hingePivots to previewConfig pipeline (finger_params.py, server.py, generate_static.py)
6. Implement flexChange() in viewer.js with compound hinge rotation math
7. Add Flex slider to index.html, wire in app.js
8. Build, deploy, verify via Playwright screenshots

## Key decisions
- Single flex slider for both hinges (equal angles) per user request
- Flex angle range: 0-90 degrees mapped from slider 0-100
- Linkage stays fixed during flex (tendon-pull mechanism)
- Proximal plugs stay with base; distal plugs move with tip
- flexChange() recomputes both explode and flex transforms to stay in sync

## Files affected
- `web/index.html` — render progress overlay div, flex slider
- `web/app.js` — showRenderProgress(), flex_change wiring
- `web/viewer.js` — _plugBaseRots, flexChange(), _rotateXY(), updated slideChange/modLoaded
- `web/stl_viewer.js` — set_rotation() method
- `web/params.js` — standard params wrapped in collapse
- `danger/finger_params.py` — _preview_hinge_pivots, compute_hinge_pivots()
- `web/server.py` — hingePivots in _preview_config()
- `scripts/generate_static.py` — hingePivots in static fallback

## Outcome
(Fill in after completion)
