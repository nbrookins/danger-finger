# Product requirements and design decisions

This document is the running record of product requirements and design decisions for the Danger Finger project. Update it as the product and architecture evolve.

---

## Product requirements

### Goals

- **Web UI**: View and configure the finger prosthetic (STL) in the browser, change parameters with live preview, filter parts, and save/load configs (with auth where needed).
- **Backend**: Support both quick preview (ephemeral, no S3) and full render (stored in S3); keep operations synchronous with a reasonable timeout (e.g. ≤10 s) and run OpenSCAD on the server (not Lambda).
- **Profiles**: Users can save configs under a profile; profile stores config name → cfghash and history for save-in-place and history.

### User-facing features

- 3D viewer for finger parts (tip, middle, base, linkage, etc.) with part visibility toggles (e.g. checkboxes).
- Parameter form: standard parameters visible by default; advanced parameters in a separate section below when “Advanced” is selected. Parameters show descriptions (from API) and feedback for modified values.
- Explode slider: when non-exploded, parts are positioned as assembled (preview position); when exploded, parts move along explode offsets. Same STLs throughout.
- Save config: name and save under current user profile; triggers sync render and stores STLs in S3.
- Load/remove saved configs from profile list; load populates params and viewer from stored render STLs.
- Preview: on param change (debounced), request preview; viewer updates from temp STL URLs. No S3 for preview.

### Non-goals / later

- WordPress auth (optional later).
- Lambda for load/profile (optional later).
- Automated cleanup of dereferenced STLs (optional later).

---

## Design decisions

### Backend

| Decision | Rationale |
|----------|-----------|
| **Sync preview and render on server** | Predictable latency and simpler than queue + worker for current scale; 10 s timeout keeps UX responsive. |
| **OpenSCAD on server (not Lambda)** | Docker image already has OpenSCAD; avoids cold starts and payload limits. |
| **Preview STLs in temp dir, not S3** | Previews are ephemeral; avoid S3 churn and cost. |
| **Render STLs in S3 at `render/{cfghash}/{part}.stl`** | Stable URLs for saved configs; cfghash dedupes identical configs. |
| **Profile stores `configs[name] = { cfghash, history }`** | Save-in-place and history without storing full config blob in profile. |
| **`/api/params` and `/api/params/all`** | Explicit routes for parameter definitions; frontend uses these instead of legacy `/params` regex route. |
| **`DangerFinger().params()` as a method (not property)** | Server needs to call `params(adv=..., allv=..., extended=True)`; property cannot take arguments. |
| **Print orientation vs preview display** | STLs are exported in print orientation (rotate_offsets) for slicing. Preview applies preview_rotate_offsets and preview position/explode in the viewer only; no duplicate STLs. |
| **`/api/parts` returns preview config** | Each part includes preview_position, explode_offset, preview_rotation (degrees), and hidden_in_preview so the viewer can display parts as an assembled finger and support explode without changing STL files. Plug is expanded to plug_0..plug_3 (same STL via `stl_part`); linkage uses a preview-only position override so it appears behind the finger/socket. |
| **stl_viewer centers geometry by default** | `stl_viewer.min.js` calls `geometry.center()` on load (`center_models=true`), moving the bbox center to the local origin. `_preview_position_offsets` must therefore specify the assembled-space bounding box center of each part. See `docs/VIEWER_ASSEMBLY.md`. |
| **stl_viewer rotates around world axis** | `rotate()` uses `rotateAroundWorldAxis` (world-space pre-multiply). With geometry centered at origin, this rotates each part around its own center. Position from `mod_loaded` is set after rotation. |
| **preview_position_offsets fixed for v5.2+ print rotations** | Positions updated to assembled bbox centers measured from v5.1 STLs. Previously all zeros causing parts to overlap at viewer origin. See `docs/VIEWER_ASSEMBLY.md` section 3.2. |
| **SCAD all reference uses preview_rotate=False** | `preview_rotate = False` is hard-coded. `_part_composite` does NOT apply `_rotate_offsets["all"]`. The all.png is the assembled-orientation reference. |
| **OpenSCAD ARM64 workaround** | On macOS ARM64, Qt runtime check fails. Fix: prepend `arch -x86_64` in `Scad_Renderer.py` (Rosetta). `OPENSCAD_USE_ROSETTA` env var. Headless PNG needs Xvfb. |

### Frontend

| Decision | Rationale |
|----------|-----------|
| **Part visibility via checkboxes** | Clearer than toggle buttons; re-show part using `last_stl_urls` so toggling back on uses current preview URL. |
| **Parameters: Standard first, Advanced section below** | Matches typical config UIs; Advanced hidden until selected. |
| **Parameter descriptions from API** | API returns `Documentation` (from param docs); shown as tooltip and optional short description under label. |
| **Modified feedback (badge + row highlight)** | Users can see which params differ from default. |
| **Viewer errors surfaced in UI** | `#viewer_error` and `set_viewer_error()`; try/catch and `stl_viewer.error` reported in status so failures are visible. |
| **Request preview from viewer `ready_callback`** | First preview runs after viewer is ready so models load correctly. |

### DevOps / testing

| Decision | Rationale |
|----------|-----------|
| **`make kbr-test`** | Build, run container in background, then run e2e test against it so we test the real Docker stack. |
| **`USE_EXISTING_SERVER=1` in test script** | Allows hitting an already-running server (e.g. Docker on 8081) without starting a second process. |
| **Test port 8091 when starting server in script** | Avoids clashing with Docker on 8081. |
| **`make inspect-ui` (Playwright)** | Headless browser loads the live UI, captures `#preview_status`, `#viewer_error`, and console; writes `output/ui-inspect.txt`. Exit 1 if the UI shows an error. Use when debugging “error and no preview” or to capture exactly what the page shows. Requires `pip install -r requirements-dev.txt` and `python -m playwright install chromium`. |

---

## Changelog

- **2026-03** – Fixed viewer assembly: `_preview_position_offsets` set to assembled bbox centers from v5.1 STLs; removed legacy 35° Z from tip/tipcover `_preview_rotate_offsets`. Created `docs/VIEWER_ASSEMBLY.md` documenting stl_viewer behaviour, coordinate system, and OpenSCAD ARM64 workaround. Added `.cursor/rules/fix-preview-positions.mdc`.
- **2026-03** – Four plug instances in preview: one plug STL shown four times (plug_0..plug_3) with per-instance position/rotation so plugs appear in tip holes; linkage preview position override so it displays behind the finger/socket. `/api/parts` expands plug and returns `stl_part` for URL lookup; frontend iterates part list and uses `stl_part` when resolving STL URLs.
- **2026-03** – Preview rotate offsets and preview config: STLs stay print-oriented; viewer applies preview_rotate_offsets, preview_position, and explode_offset from `/api/parts` so preview looks like an assembled finger and explode works without duplicating STLs. Stand hidden in preview by default. Cursor rule to keep docs updated.
- **2026-03** – Initial product/design doc; viewer error surfacing; parameter descriptions; part visibility checkboxes; Standard/Advanced layout; PRD + design decisions captured.
