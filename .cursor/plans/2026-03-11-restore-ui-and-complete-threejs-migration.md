# Restore UI and Complete Three.js Migration

**Date**: 2026-03-11  
**Status**: completed

## Goal

Fix a regression where the 3D viewer and parameter UI stopped working, then complete the previously-incomplete migration from `stl_viewer.min.js` (StlViewer v1.08 / Three.js r86) to a modern Three.js r160 wrapper. Also re-apply Lambda/ZIP/download features that had been built on top of a broken base.

## Root cause

Commit `cec17eb` ("deprecate stlviewer for threejs") rewrote `index.html` to reference `stl_viewer.js` and `vendor/three/` files that were never committed. This left the page broken. A subsequent session built Lambda/ZIP features on top of the broken commit, compounding the regression.

## Steps

1. Diagnose: confirmed `stl_viewer.js` and `vendor/three/` didn't exist on disk or in HEAD
2. Restore `index.html` from `68701bf` (last working commit before the broken migration)
3. Re-apply Lambda/bundle ZIP/JSZip/download features into the modular JS architecture (`api.js`, `app.js`, `params.js`, `viewer.js`) rather than inline
4. Fix temp file cleanup bug in `server.py` (`finally` block was deleting preview STLs before the browser could fetch them)
5. Retrieve the complete `stl_viewer.js` wrapper and `vendor/three/` files from the Cursor worktree where the earlier session had created them but failed to sync
6. Swap `index.html` from `stl_viewer.min.js` to the three new script tags
7. Update `viewer.js` comment; no API changes needed (wrapper is fully compatible)
8. Delete 9 legacy files: `stl_viewer.min.js`, `three.min.js` (r86), `OrbitControls.js` (old), `TrackballControls.js`, `CanvasRenderer.js`, `Projector.js`, `load_stl.min.js`, `parser.min.js`, `webgl_detector.js`
9. Create this rule and backfill plan archives

## Key decisions

- Restored to `68701bf` rather than trying to fix the broken `cec17eb` — the modular architecture at `68701bf` is correct; the broken commit was purely additive mess
- Lambda/ZIP features re-applied into the existing modules (`api.js`, `app.js`) rather than inline script — keeps separation of concerns intact
- Used Three.js r160 UMD (last version with `window.THREE` global export before ESM-only pivot) — avoids needing a bundler
- `stl_viewer.js` inlines r170 STLLoader source directly — avoids separate file dependency

## Files affected

- `web/index.html` — restored to 68701bf + three new `<script>` tags + JSZip CDN + download button
- `web/stl_viewer.js` — NEW: compatibility wrapper (624 lines), Three.js r160 + r170 STLLoader + r170 OrbitControls
- `web/vendor/three/three.min.js` — NEW: Three.js r160 UMD (670KB)
- `web/vendor/three/OrbitControls.js` — NEW: r170 OrbitControls adapted as IIFE global (32KB)
- `web/api.js` — dual base URL, `fetchBundleZip()`, `getBundleUrl()`, improved save response handling
- `web/app.js` — `loadBundleZip()`, download button management, profiles Download column
- `web/params.js` — status callbacks during save, save button disable/enable
- `web/viewer.js` — `absolute` URL flag in `updateFromStlUrls()`, comment update
- `web/server.py` — fixed temp dir cleanup bug (only delete on `store_in_s3=True`)
- Deleted: `stl_viewer.min.js`, `three.min.js`, `OrbitControls.js`, `TrackballControls.js`, `CanvasRenderer.js`, `Projector.js`, `load_stl.min.js`, `parser.min.js`, `webgl_detector.js`

## Outcome

All UI improvements from earlier today are preserved and working:
- Dynamic part visibility checkboxes
- Clean parameter table with descriptions, defaults, value range
- Modified/unsaved badges on changed params
- Advanced params collapsible with warning
- Version shown in page title
- Download ZIP button after save/load
- Render status messages

Three.js migration complete:
- MeshStandardMaterial (better shading)
- Modern OrbitControls with damping
- ResizeObserver auto-resize
- Proper GPU memory cleanup on `remove_model`
- No deprecated Three.js API warnings
