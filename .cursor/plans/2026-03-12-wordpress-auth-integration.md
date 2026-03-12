# WordPress JWT Auth Integration

**Date**: 2026-03-12  
**Status**: completed

## Goal

Integrate WordPress (dangercreations.com on SiteGround) as the identity provider for the
Danger Finger app deployed on AWS. Users log in via WordPress; the app receives a JWT that
Tornado validates locally. Expensive operations (full render, profile writes) require a
valid JWT. Anonymous users can still preview and download. Also includes a comprehensive
WordPress site audit and cleanup to improve security before exposing the auth endpoint.

## Steps

1. Create `wordpress/dangerfinger-setup/` with PHP code, .htaccess rules, and setup instructions.
2. `functions-security.php`: disable user enumeration REST endpoint and `?author=N` redirect; strip EXIF from media REST responses; remove WP version from output.
3. `functions-auth.php`: add `user_nicename` to JWT payload via `jwt_auth_token_before_sign` filter; `[dangerfinger_configurator]` shortcode for WP embed page.
4. `htaccess-additions.txt`: Authorization header passthrough (SiteGround strips it by default); block `readme.html`, `license.txt`, `wp-config.php`.
5. `wp-config-additions.txt`: `JWT_AUTH_SECRET_KEY`, `JWT_AUTH_CORS_ENABLE`, `DANGERFINGER_APP_URL`, HTTPS siteurl/home.
6. `README.md`: step-by-step setup guide (plugin install, wp-config, .htaccess, functions.php, page creation, verification commands).
7. Create `web/auth.py`: `validate_jwt()` (PyJWT decode, in-memory LRU cache, dev-mode bypass); `get_nicename()` to extract `user_nicename` from payload.
8. Update `web/server.py`: add `WP_AUTH_URL`/`APP_BASE_URL` env vars; update `set_def_headers` to reflect specific CORS origin when configured; add `WpAuthMixin` class with `require_auth()` / `_auth_error()`; apply mixin to `ApiRenderHandler` and `FingerHandler`; add profile ownership check (jwt nicename == URL userhash); expose `wpAuthUrl` and `appBaseUrl` in `/api/parts` response.
9. Update `web/api.js`: add `_authToken`, `setAuthToken()`, `getAuthToken()`; always send `Authorization: Bearer` header when token is set; add `fetchWpJwt()` to exchange Application Password for JWT.
10. Update `web/app.js`: remove forced `http://` redirect; add full auth state (`_authToken`, `_authUser`, `_authDisplay`, `_wpAuthUrl`); `setAuthState()`, `clearAuthState()`, `loadStoredAuth()` (sessionStorage), `updateAuthUI()`, `buildLoginUrl()`, `initLoginLogout()`, `handleAuthCallback()` (cleans URL, exchanges app password for JWT); replace hardcoded `"nick"` username with `getUsername()`; only fetch profiles when authenticated.
11. Update `web/params.js`: add `setUsername()` public method; auth gate in `submit()` (shows "please log in" when username empty).
12. Update `web/index.html`: add `#auth-bar` with login/logout buttons and user display; remove forced HTTP redirect.
13. Update `requirements.txt`: add `PyJWT>=2.0`.
14. Update `docker/env-example.txt`: add `jwt_secret`, `wp_auth_url`, `app_base_url`.
15. Update `template.yaml`: add `WpAuthOrigin` CloudFormation parameter; use it in Lambda CORS `AllowOrigins`.
16. Update `docs/PRODUCT.md`: add Authentication section (product requirements + design decisions + changelog entry).

## Key decisions

- **Application Passwords → JWT**: Use WP's built-in `authorize-application.php` for the OAuth-like step (no custom plugin). The returned Application Password is used once to call the JWT plugin endpoint, then discarded. JWT lives in sessionStorage.
- **JWT validated locally**: `JWT_AUTH_SECRET_KEY` shared between WP and Tornado via env var. No WP round-trip per request. Token cache (5 min TTL) for hot paths.
- **user_nicename as profile key**: Added to JWT payload via WP filter. Stable, URL-safe, already used as the S3 key prefix.
- **Dev mode**: when `jwt_secret` is empty, `auth.py` accepts any Bearer token. Allows local dev without a live WP site.
- **Anonymous preview allowed**: only write operations (render, save, delete) are protected. Read operations and preview remain public to support the "try before you log in" UX.
- **Profile ownership enforced in Tornado**: `userhash` in URL must match `jwt.user_nicename`; returns 403 otherwise.
- **WP embed shortcode**: `[dangerfinger_configurator url="..."]` — shows login prompt for guests, iframe for logged-in users.

## Files affected

- `wordpress/dangerfinger-setup/README.md` — NEW: setup guide
- `wordpress/dangerfinger-setup/functions-security.php` — NEW: WP security hardening
- `wordpress/dangerfinger-setup/functions-auth.php` — NEW: JWT filter + shortcode
- `wordpress/dangerfinger-setup/htaccess-additions.txt` — NEW: .htaccess rules
- `wordpress/dangerfinger-setup/wp-config-additions.txt` — NEW: wp-config.php additions
- `web/auth.py` — NEW: JWT validation and nicename extraction
- `web/server.py` — CORS update, WpAuthMixin, protect render/profile handlers, wpAuthUrl in /api/parts
- `web/api.js` — auth token state, setAuthToken, fetchWpJwt, Bearer header on all requests
- `web/app.js` — full auth flow, removed http:// redirect, dynamic username
- `web/params.js` — setUsername(), auth gate in submit()
- `web/index.html` — auth bar with login/logout/user display
- `requirements.txt` — added PyJWT>=2.0
- `docker/env-example.txt` — added jwt_secret, wp_auth_url, app_base_url
- `template.yaml` — WpAuthOrigin parameter, CORS AllowOrigins updated
- `docs/PRODUCT.md` — Authentication section (requirements, decisions, changelog)

## Outcome

**Completed 2026-03-12 (WordPress side applied via SSH)**

### WordPress changes applied directly to dangercreations.com (SiteGround)
- `jwt-authentication-for-wp-rest-api` plugin installed and activated (v1.5.0)
- `pirate-forms` and `wpforms-lite` deactivated (kept `ninja-forms`)
- `siteurl` and `home` updated to `https://dangercreations.com`
- Open user registration disabled (`users_can_register=0`)
- `wp-config.php` updated with `JWT_AUTH_SECRET_KEY`, `JWT_AUTH_CORS_ENABLE`, `DANGERFINGER_APP_URL`, `WP_SITEURL`, `WP_HOME`
- `.htaccess` updated with user-enumeration block, XML-RPC block, and version-disclosure file blocks (readme.html, license.txt deleted directly since nginx serves static files before .htaccess)
- `kale/functions.php` updated with REST user-enumeration filter, EXIF strip filter, JWT payload filter (`user_nicename`, `display_name`), and `[dangerfinger_configurator]` shortcode
- `/prosthetics/configure` page created (ID 1227, child of Prosthetics page ID 9), publishes the shortcode

### Backend changes
- `docker/env-example.txt` updated with actual values (`jwt_secret`, `wp_auth_url`, `app_base_url`)
- EC2 Docker container restarted with the three new env vars

### JWT secret
`cPxTbNhzKqHXJ11NTEdRvwbels8XYulCcher57ZPLPH3RBecHgaahM6GWVrIPOG` (set in both WordPress and container)

### Verification
- JWT endpoint `/wp-json/jwt-auth/v1/token` → 403 with `[jwt_auth] invalid_username` (correct)
- `/wp-json/wp/v2/users` → 404 (blocked, correct)
- `/readme.html` → 403 (blocked, correct)
- `/prosthetics/configure` → 200 (live, correct)

### Follow-ups
- Test full auth flow end-to-end with a real WordPress user.
- Decide whether to disable the dev-mode bypass (`jwt_secret` must always be set in prod).
- Token expiry UX: when JWT expires (default 7 days), add a login redirect rather than just a status message.
- Consider adding the JWT secret to AWS Secrets Manager rather than injecting as a container env var.
