# Immutable, Versioned Download Naming

**Date**: 2026-03-17
**Status**: completed

## Goal
Make all download filenames content-addressed and version-prefixed (`DangerFinger_v5.3_{cfghash8}.zip`) so they are recognizable, cache-safe, and immutable. Previously, the default bundle used a generic `bundle.zip` name and rendered bundles used `danger_finger_{hash8}.zip` without version info.

## Steps
1. Add cfghash computation to `generate_default_stls.py` using the same logic as `server.py`'s `package_config_json` (sha256 of sorted empty JSON config)
2. Name the default bundle `DangerFinger_v{VERSION}_{hash8}.zip` instead of `bundle.zip`; clean up old zips on regeneration
3. Add `defaultCfghash` to `generate_static.py` bootstrap data (both `parts.json` and `config-bootstrap.js`)
4. Add `_appVersion` and `_defaultCfghash` globals in `app.js`, populated from `onPartsLoaded`
5. Add `_downloadName(suffix)` helper returning `DangerFinger_v{version}_{suffix}.zip`
6. Update all 3 download naming sites to use the helper
7. Deploy and verify via Playwright

## Key decisions
- Used `sha256('{}')` for default cfghash since `remove_defaults` strips all default values, leaving an empty config — deterministic and matches the server's hashing
- Version comes from `DangerFinger.VERSION` (currently 5.3), embedded in both bootstrap JS and the S3 filename
- Old zip files are cleaned from the defaults directory before writing the new one, preventing stale files from accumulating

## Files affected
- `scripts/generate_default_stls.py` — content-addressed zip naming, old zip cleanup
- `scripts/generate_static.py` — `_default_cfghash()` helper, `defaultCfghash` in both bootstrap and parts.json
- `web/app.js` — `_appVersion`, `_defaultCfghash`, `_downloadName()`, updated all 3 download sites

## Outcome
All downloads now named `DangerFinger_v5.3_{hash8}.zip`. Verified via Playwright: button href points to `DangerFinger_v5.3_44136fa3.zip`, CDN returns 200 with correct size. Old `bundle.zip` removed from S3.
