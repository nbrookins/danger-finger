# S3 Static Frontend — EC2 Downtime Resilience

**Date**: 2026-03-12
**Status**: completed

## Goal
Host the frontend as a static site on S3 so the UI loads even when EC2 is down. EC2 is demoted to render-only API. Lambda handles reads. No CloudFront or new services.

## Steps
1. Create `infra/static.tf` — S3 bucket with website hosting + public read policy + CORS
2. Create `scripts/generate_static.py` — produces parts.json and params.json at deploy time
3. Update `web/api.js` — add `_renderUrl` for POST calls, graceful offline error handling
4. Update `web/app.js` — read `window.__RENDER_URL__`, pass to `Api.init()`
5. Add `generate-static` and `deploy-static` Makefile targets
6. Add deploy-static step to `.github/workflows/deploy.yml`
7. Apply Terraform, deploy, verify

## Key decisions
- S3 static website over CloudFront: simpler, effectively free at this traffic level, CloudFront can be added later as a CDN layer if needed
- Separate static bucket (`danger-finger-static`) rather than a prefix in the data bucket: keeps public/private cleanly separated
- Extensionless JSON files (`/api/parts`, `/params/all`) uploaded alongside `.json` versions: matches the live server's URL pattern so the JS works unchanged
- `_renderUrl` / `_readBase()` / `_renderBase()` pattern: clean separation of which calls go where, with graceful offline messaging
- Did NOT import from `web/server.py` for static generation: server has too many transitive dependencies (auth, tornado). Replicated the logic directly.

## Files affected
- `infra/static.tf` — new: S3 static website bucket
- `infra/outputs.tf` — added static_site_url and static_bucket outputs
- `scripts/generate_static.py` — new: generates static JSON
- `web/api.js` — added _renderUrl, _renderBase(), offline error handling
- `web/app.js` — reads window.__RENDER_URL__
- `Makefile` — added generate-static, deploy-static targets
- `.github/workflows/deploy.yml` — added deploy-static step

## Outcome
- Static site live at: http://danger-finger-static.s3-website-us-east-1.amazonaws.com
- All endpoints verified: HTML, JS, CSS, api/parts, params/all
- READ_URL and RENDER_URL injected into static index.html
- When EC2 is down: UI loads, parameter controls work, saved configs load (via Lambda), only preview/render shows "server offline" message
