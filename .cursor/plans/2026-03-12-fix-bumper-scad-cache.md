# Fix Bumper, Add SCAD to Bundles, Cache Previews

**Date**: 2026-03-12
**Status**: completed

## Goal
Fix bumper disappearing on subsequent preview renders (caused by rebuilding the finger model 9 times with `.part` attribute collisions), include SCAD source files in every download bundle, and add cfghash-based preview caching so identical configs return instantly.

## Steps
1. Refactor `build()` in server.py to `build_all()` — build the finger model once and extract all parts
2. Add per-part try/except and STL size verification in `_run_sync_preview_or_render`
3. Return `scad_urls` alongside `stl_urls` in preview responses; nest SCAD under `scad/` in S3 bundles
4. Keep SCAD files in `generate_default_stls.py` and include in default bundle under `scad/`
5. Update `buildPreviewZipDownload` in app.js to fetch and include SCAD files in `scad/` folder
6. Add cfghash-based preview caching in `ApiPreviewHandler` with `preview_by_cfghash` index
7. Deploy and verify bumper, SCAD in zips, and cache hits

## Key decisions
- `build_all()` mirrors the approach used by `generate_default_stls.py` (which already works correctly) — build once, extract by name
- Preview cache uses in-memory `preview_by_cfghash` dict with disk validation before returning cached results
- SCAD files nested under `scad/` subfolder in all bundle types for consistent structure
- Per-part error handling prevents one OpenSCAD failure from killing the entire render

## Files affected
- `web/server.py` — `build_all()` replaces `build()`, `_run_sync_preview_or_render` returns 4-tuple, preview caching in handler and worker, `_find_cached_preview` helper
- `web/app.js` — `buildPreviewZipDownload` accepts `scadUrls` parameter, fetches and includes SCAD in zip
- `scripts/generate_default_stls.py` — stop deleting SCAD files, include them in default bundle zip

## Outcome
All three issues resolved and verified in production:
- **Bumper fix**: `build_all()` builds the finger model once and extracts all 9 parts. Verified: bumper.stl (1.36 MB) returned for `finger_length=55` config.
- **SCAD in bundles**: All 9 SCAD files returned in `scad_urls` alongside `stl_urls`. Client-side zip builder fetches and nests them under `scad/`. S3 bundles also nest under `scad/`. Default bundle will include SCAD files on next `make generate-default-stls`.
- **Preview caching**: Second identical request returned in 0.24s (cache hit) vs ~60s render. Cache indexed by cfghash with disk validation. Pruned alongside existing `preview_results` TTL.
