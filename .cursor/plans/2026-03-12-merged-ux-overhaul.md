# Merged UX Overhaul

**Date**: 2026-03-12
**Status**: completed

## Goal
Implement the full merged UX overhaul plan: async preview, param ordering, render button intelligence, full-page launch from iframe, profile table status, reset defaults, quality indicator, presets, and documentation updates. Phases 1A-1C (fetchParts bug, priority levels, rate limiting) already implemented.

## Steps
1. Phase 2: Async preview — convert preview to job queue, add in-memory results, frontend polling
2. Phase 3: Param ordering — add order/section to Prop, tag common params, render 3 sections
3. Phase 4: Render button intelligence — track _lastRenderedCfghash, separate render disable
4. Phase 5: Full-page launch from iframe + share link
5. Phase 6: Profile table render status column
6. Phase 7A: Reset to defaults (per-param + global)
7. Phase 7B: Quality indicator in viewer status
8. Phase 7C: Param presets dropdown
9. Phase 8: Docs and archive

## Key decisions
- Using module-level `_app_ref` to avoid threading `application` through every function signature
- Preview jobs stored in-memory only (no S3 persistence), pruned after 10 minutes
- Preview jobs share the render queue at PRIORITY_PREVIEW=-10 (always first)
- JobStatusHandler returns preview results from in-memory dict

## Files affected
- `web/server.py` — async preview queue, preview job infrastructure
- `web/api.js` — preview polling, share link support
- `web/app.js` — render button state, iframe detection, share link, profile status
- `web/params.js` — three-section rendering, reset buttons, presets, render button separation
- `web/index.html` — new buttons (full-page, share), preset dropdown
- `danger/Params.py` — add order/section to Prop
- `danger/finger_params.py` — tag common params with section/order
- `docs/PRODUCT.md` — changelog
- `docs/ARCHITECTURE.md` — endpoint updates
- `docs/PARAMETERS.md` — section/order system

## Outcome
All phases implemented successfully. Key changes:
- Phase 2: Async preview using shared job queue with PRIORITY_PREVIEW=-10, in-memory results, frontend polling
- Phase 3: Prop.order/section attributes, 6 common params tagged, get_params() sorts deterministically, params.js renders 3 sections
- Phase 4: _lastRenderedCfghash tracking, setRenderDisabled() separate from setButtonsDisabled()
- Phase 5: isInIframe() detection, launchFullPage(), copyShareLink(), restoreFromHash()
- Phase 6: Status column in profile table with _checkProfileStatus() polling
- Phase 7A: resetParam(), resetAll(), per-row × button, "Reset all" link
- Phase 7B: Quality indicator in preview status messages
- Phase 7C: _presets dict with 4 configurations, dropdown in fillParams()
- Phase 8: PRODUCT.md, ARCHITECTURE.md, PARAMETERS.md updated
