# Fix Auth Callback Race & Worker Thread Resilience

**Date**: 2026-03-17
**Status**: completed

## Goal
Fix two bugs: (1) a race condition in `app.js` where the JWT auth callback clears the URL before the exchange completes, causing the auth-settled fast path to fire prematurely and silently drop the guest draft's pending save action; (2) uncaught `RuntimeError` from S3 failures in `server.py`'s render worker that permanently kill the single daemon thread.

## Steps
1. Verify Bug 1 in `web/app.js`: `handleAuthCallback` calls `history.replaceState` (line 164) before XHR completes; the post-callback check (line 671) re-reads the now-clean URL and prematurely sets `_authSettled = true`.
2. Fix Bug 1: Capture `jwt_auth` param into a local variable before calling `handleAuthCallback`, use that for the fast-path non-auth check.
3. Verify Bug 2 in `web/server.py`: `_persist_job` raises `RuntimeError` on S3 failure; calls at lines 1168, 1176 are outside try/except; `_mark_job_failed` (line 1036) also calls `_persist_job` creating a secondary failure path.
4. Fix Bug 2: Wrap entire job-processing body in outer try/except with sleep-and-retry; make `_mark_job_failed`'s `_persist_job` call resilient with its own try/except.
5. Verify no lint errors introduced.

## Key decisions
- Bug 1: Chose to capture the URL param before the call rather than deferring `replaceState`, since deferring would leave credentials visible in the URL bar during the XHR.
- Bug 2: Used a two-layer approach — outer try/except on the worker loop prevents thread death; inner try/except on `_mark_job_failed`'s persist call prevents secondary failure cascades. Added a 2-second sleep on outer catch to avoid tight retry loops on transient S3 outages.

## Files affected
- `web/app.js` — Captured `jwt_auth` into `isAuthRedirect` before `handleAuthCallback`; used it for the fast-path check instead of re-reading the URL.
- `web/server.py` — Wrapped `_render_worker`'s `while True` body in outer try/except; wrapped `_persist_job` in `_mark_job_failed` with try/except.

## Outcome
Both bugs verified and fixed. No lint errors. The auth callback race can no longer cause premature settling, and the render worker survives transient S3 failures.
