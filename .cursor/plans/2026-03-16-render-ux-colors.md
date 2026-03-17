# Render UX + Part Colors Overhaul

**Date**: 2026-03-16  
**Status**: completed

## Goal
Replace auto-preview with a manual "Render" button on the viewer card. Default render quality = preview quality (EXTRAMEDIUM). Add a quality selector (Default / High). Update part colors to warm browns for hard parts and blues for soft parts.

## Steps
1. Update `PART_COLORS` in `danger/finger.py` — hard parts (tip+base, middle+linkage) warm browns, soft parts (tipcover, socket, plug) blue shades, stand neutral gray
2. Remove auto-preview trigger from `params.js` `onChange()` — no server request on param change
3. Add Render button + quality dropdown to the viewer card in `index.html` — show when params are dirty
4. Add `quality` parameter to `/api/preview` endpoint in `server.py` — "default" = EXTRAMEDIUM, "high" = HIGH; both save to S3
5. Wire frontend: `app.js` tracks dirty state, shows/hides render overlay, handles render click; `api.js` sends quality param
6. Remove old Render button from params form (keep Save button)
7. Build, deploy, verify end-to-end through CloudFront

## Key decisions
- Plug is a soft part (blue) per user instruction
- Stand stays neutral gray
- Both quality levels save to S3; High replaces Default bundle for download
- No auto-preview at all — user must click Render to see any changes
- Render button overlaid on viewer when params are dirty
- Save button stays in params form (saves config to profile, requires auth)

## Files affected
- `danger/finger.py` — PART_COLORS
- `web/index.html` — render overlay UI in viewer card
- `web/params.js` — remove auto-preview trigger, remove render button from form
- `web/app.js` — dirty state tracking, render overlay logic, quality handling
- `web/api.js` — send quality param, remove debounce/auto-preview
- `web/server.py` — quality param in preview endpoint, S3 storage for both

## Outcome
All changes implemented and verified live on CloudFront.

- **Colors**: Hard parts (tip+base) in dark warm brown (#7A6555), middle+linkage in sandy tan (#B8A089). Soft parts (tipcover, socket, plug) in blue shades (#89BCD6, #6A9DB8, #7BB0CC). Stand stays neutral gray.
- **No auto-preview**: Parameter changes no longer trigger server requests. The viewer shows the last render until user clicks Render.
- **Render overlay**: Quality dropdown (Default/High) + green Render button appear at the bottom of the viewer when params are dirty. Hidden after render completes.
- **Quality**: Default = EXTRAMEDIUM (fast, ephemeral STLs). High = HIGH (slower, saves bundle.zip to S3 for download). Both produce 8 STL parts for the viewer.
- **Save button** remains in params form for saving config to profile.
- Verified with Playwright screenshots: initial load renders at default quality, param change shows overlay, Render button works.
