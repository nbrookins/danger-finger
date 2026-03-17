# Anonymous Access, Authenticated Save, Priority Queue, Restart Recovery Implementation

**Date**: 2026-03-12
**Status**: completed

## Goal
Implement guest-accessible configuration and preview, authenticated profile saving, guest-capable render/download, authenticated-first render dispatch, and restart-safe job recovery so the configurator remains easy to use while protecting saved profiles and keeping the queue reliable after crashes.

## Steps
1. Open the WordPress embed to guests while preserving the existing login flow.
2. Refactor the backend to decouple profile save from render submission.
3. Add durable render job records, a priority scheduler, guest throttling, and restart recovery.
4. Update the frontend for separate Save, Render, and Download actions plus login-resume draft restoration.
5. Expose render status through the read API and update docs.
6. Run validation and end-to-end verification for guest access, queue behavior, and restart recovery semantics.

## Key decisions
- Resume means safe whole-job requeue after restart, not partial OpenSCAD checkpointing.
- Bundle existence by `cfghash` remains the dedupe and completion source of truth.
- Save and render are separated so profile persistence is fast and reliable.
- Guest rendering stays available but rate-limited and lower priority than authenticated jobs.

## Files affected
- `wordpress/dangerfinger-setup/functions-auth.php` — allow guest iframe access with CTA
- `web/server.py` — durable jobs, queueing, save/render split, recovery, throttling
- `lambda/handler.py` — render status/job read support
- `web/api.js` — render/save/status client changes
- `web/app.js` — login resume, queue status, guest/auth UX
- `web/params.js` — separate Save, Render, Download controls
- `web/index.html` — status/UI controls for render flow
- `docs/ARCHITECTURE.md` — endpoint and queue architecture updates
- `docs/PRODUCT.md` — behavior and changelog updates
- `docs/DEPLOY.md` — operator notes for restart recovery and queue behavior

## Outcome
Implemented guest WordPress embed access, decoupled authenticated save from full render, added S3-backed durable render jobs with queue status endpoints, authenticated-first scheduling, guest throttling, and startup recovery. Updated the frontend to preserve guest draft state across login, auto-resume save after JWT callback, and split Save/Render/Download UX. Verified Python modules compile, verified the app boots in Docker on an isolated port even without local AWS credentials by making recovery best-effort, and captured a fresh headless screenshot showing the guest UI with separate Save and Render controls plus a successful preview. Remaining gap: the full WordPress round-trip and authenticated queue promotion were implemented but not exercised against a live WordPress auth environment in this session.
