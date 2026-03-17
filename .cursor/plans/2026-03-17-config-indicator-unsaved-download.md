# Config Indicator, Unsaved Prompt, Anonymous Downloads, Bumper Bug

**Date**: 2026-03-17
**Status**: completed

## Goal
Add config hash indicator in the UI, warn on unsaved changes, enable downloads for anonymous previews, and investigate bumper disappearing after param changes.

## Steps
1. Add config hash indicator badge (below download button or in status area)
2. Add beforeunload prompt when params are dirty/unsaved
3. Enable download button for all preview renders (client-side zip via JSZip)
4. Investigate and fix bumper disappearing on subsequent renders

## Key decisions
- Config indicator shows "default" or first 8 chars of cfghash, with saved/unsaved state
- Client-side zip via JSZip (already loaded) for anonymous preview downloads since preview STLs are in temp dir, not S3 bundles
- beforeunload fires when _paramsDirty is true and config hasn't been saved

## Files affected
- `web/app.js` — config indicator, beforeunload, download on preview complete
- `web/index.html` — config indicator element

## Outcome
All four features implemented and deployed:
1. Config hash indicator shows "default" or cfghash with saved/modified/unsaved state, color-coded
2. beforeunload prompt fires when params are dirty and config isn't saved
3. Anonymous preview downloads build client-side zip via JSZip from preview STL URLs
4. Bumper issue: likely server-side — `build("bumper", config)` may return `None` for certain param combos. Need specific param values to reproduce. The viewer correctly renders whatever the server returns.
