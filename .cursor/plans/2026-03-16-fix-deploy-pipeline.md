# Fix Deploy Pipeline

**Date**: 2026-03-16  
**Status**: completed

## Goal
Fix 8 distinct failure modes in the deploy pipeline that cause most deploys to break. The root causes span architecture mismatches, missing ECR auth, empty env vars, CORS protocol mismatches, mixed content, an incomplete `make deploy` target, no health checks, and duplicate Makefile variable definitions.

## Steps
1. Fix Makefile variable resolution — remove duplicate `STATIC_SITE_URL ?=` on line 137 (conflicts with terraform output on line 181); source JWT_SECRET, WP_AUTH_URL, APP_BASE_URL, STATIC_SITE_URL from terraform outputs instead of empty dev.env vars
2. Add `--platform linux/amd64` to `build` target so builds always produce amd64 images
3. Include ECR re-auth (`aws ecr get-login-password | docker login`) inside the SSM command for `deploy-ec2`
4. Fix `server.py` CORS to normalize origin URLs — ensure values in `_CORS_ALLOWED` always include protocol prefix
5. Create a unified `deploy-all` target that chains: build → push-ecr → deploy-ec2 → deploy-static → health check
6. Add a post-deploy health check that waits for SSM command completion and verifies `/api/parts` returns healthy
7. Redeploy with fixes and verify live site works

## Key decisions
- Keep `make build` cross-compiling to amd64 by default since the only deploy target is EC2 amd64. Add a `build-native` target for local dev testing.
- Source deploy env vars exclusively from terraform outputs (remove the intermediate Make vars that shadow them)
- Fix CORS normalization in server.py rather than relying on callers to always include protocol

## Files affected
- `Makefile` — variable resolution, build target, deploy targets, health check
- `web/server.py` — CORS origin normalization

## Outcome
All 8 failure modes fixed and verified:

1. **Build**: `make build` now cross-compiles to amd64 by default (`DOCKER_PLATFORM=linux/amd64`). `make build-native` available for local dev.
2. **ECR auth**: `deploy-ec2` SSM command now runs `aws ecr get-login-password | docker login` before `docker pull`.
3. **Env vars**: `STATIC_SITE_URL` and `APP_BASE_URL` sourced from terraform outputs via `$(or ...)` pattern; `WP_AUTH_URL` defaults to `https://dangercreations.com`.
4. **CORS**: `server.py` normalizes origin URLs via `_normalize_origin()` — adds `https://` prefix if missing.
5. **Mixed content**: `RENDER_URL` changed from raw EC2 HTTP to CloudFront HTTPS URL. CloudFront already proxies `/api/*`, `/render/*` etc. to EC2.
6. **`make deploy`**: Now chains `build → push-ecr → deploy-ec2 → deploy-static → check-health`.
7. **SSM wait**: `deploy-ec2` polls SSM command status (up to 75s), reports success/failure and stderr on error.
8. **Duplicate var**: Removed second `STATIC_SITE_URL ?=` that was dead code.

Also fixed: `check-health` missing `$(or $(PYTHON),python3)` fallback; CI workflow `RENDER_URL` confirmed to use CloudFront URL (was correct, briefly broken then restored).

Follow-up: `JWT_SECRET` must still be passed explicitly for local deploys (`make deploy JWT_SECRET=xxx`). Consider storing in SSM Parameter Store for fully automated local deploys.

### Additional fixes discovered during verification
9. **`/jobs/*` route not covered by CloudFront** — Preview status polling hit `/jobs/{id}` which fell through to S3 default behavior (SPA fallback → index.html). Moved route to `/api/jobs/{id}` which is covered by existing `/api/*` behavior.
10. **RENDER_URL pointed to raw EC2 HTTP** — Despite CloudFront already proxying render paths to EC2, the RENDER_URL was set to the EC2 IP. This caused mixed-content blocking when embedded in HTTPS WordPress. Fixed to point to CloudFront URL.
11. **CloudFront not invalidated after static deploys** — Added automatic CloudFront invalidation to `deploy-static` target. Added `cloudfront_distribution_id` terraform output.
12. **Created two new cursor rules**: `cloudfront-route-coverage.mdc` (ensure all server routes are covered by CF behaviors) and `verify-deploy-e2e.mdc` (end-to-end deploy verification checklist). Updated deploy skill with corrected workflow.
