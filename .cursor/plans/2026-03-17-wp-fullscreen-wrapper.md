# WordPress Fullscreen Wrapper

**Date**: 2026-03-17
**Status**: completed

## Goal
Keep the user on the dangercreations.com domain when "Open full page" is clicked, by adding a WordPress fullscreen template that renders a thin breadcrumb/back bar above a full-viewport iframe. Also add a matching site bar when visiting the CloudFront app directly.

## Steps
1. Added `configurePageUrl` to parts JSON in server.py and generate_static.py
2. Updated `launchFullPage()` in app.js to open `dangercreations.com/prosthetics/configure/?fullscreen=1` instead of the raw CloudFront URL
3. Added `#site-bar` element in index.html with back link and breadcrumb, shown by app.js when running standalone (not in iframe)
4. Added `template_redirect` handler in WordPress `functions-auth.php` for `?fullscreen=1` — renders minimal HTML with top bar + full-viewport iframe
5. Deployed container, static site, and WordPress plugin; verified all three layers

## Key decisions
- Used `WP_AUTH_URL` env var (already exists) to derive `configurePageUrl` — no new env var needed
- WordPress fullscreen template uses `is_page('configure')` to only trigger on the configure page
- Hash fragment forwarding: WP page script reads `window.location.hash` and appends it to the iframe `src` so config params carry through
- Site bar in app.js only shows when `!isInIframe() && _configurePageUrl` — avoids double bars when iframed

## Files affected
- `web/server.py` — added `configurePageUrl` to ApiPartsHandler response
- `scripts/generate_static.py` — added `configurePageUrl` to both parts.json and bootstrap JS
- `web/app.js` — added `_configurePageUrl` var, updated `launchFullPage()`, added `initSiteBar()`
- `web/index.html` — added `#site-bar` element above auth bar
- `wordpress/dangerfinger-setup/functions-auth.php` — added template_redirect for `?fullscreen=1`

## Outcome
"Open full page" now opens `dangercreations.com/prosthetics/configure/?fullscreen=1` — user stays on the WP domain with a breadcrumb bar showing "Danger Creations | Prosthetics > Configure". Direct visits to CloudFront show a matching site bar with a back link. Config params transfer via URL hash.
