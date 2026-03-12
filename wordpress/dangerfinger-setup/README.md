# DangerFinger WordPress Setup

> **Status (2026-03-12)**: All steps below have been applied to dangercreations.com
> via SSH. This README is kept as reference for future re-installs, theme changes,
> or migrations. See `.cursor/rules/wordpress-integration.mdc` for the live
> connection details and gotchas.

This directory contains everything needed to integrate the DangerFinger app
(hosted on AWS) with the WordPress site on SiteGround.

## Auth flow overview

```
User (browser)
  │  1. Click "Login" in the app
  ▼
WordPress /wp-admin/authorize-application.php
  │  2. User logs in (if not already), approves the app
  ▼
App URL?jwt_auth=1&user_login=...&password=...
  │  3. App POSTs to /wp-json/jwt-auth/v1/token with Application Password
  ▼
JWT token returned → stored in sessionStorage
  │  4. App sends Authorization: Bearer <JWT> on protected requests
  ▼
Tornado server validates JWT locally (no WP round-trip per request)
```

## Setup steps

### 1. Install the JWT plugin

In WP Admin → Plugins → Add New, search for and install:
**"JWT Authentication for WP REST API"** by Enrique Chavez

### 2. Update wp-config.php

Add the lines from `wp-config-additions.txt` to `/public_html/wp-config.php`
before the "That's all, stop editing!" line.

**Important**: Set `JWT_AUTH_SECRET_KEY` to a random 32+ character string,
and use the **same secret** as the `jwt_secret` env var in the Tornado server
(see `docker/env-example.txt`).

### 3. Update .htaccess

Add the rules from `htaccess-additions.txt` to `/public_html/.htaccess`,
**after** the `# END WordPress` block (not inside it — WordPress overwrites
that section on permalink save).

> **Note**: SiteGround's default WordPress `.htaccess` already includes
> `RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]` inside the
> WordPress block, so the Authorization header passthrough works out of the box.
> The additions in `htaccess-additions.txt` are for security blocks only
> (user enumeration, XML-RPC, version disclosure).

> **Caveat**: SiteGround uses nginx in front of Apache. nginx serves static
> files directly, bypassing `.htaccess`. To block a static file like
> `readme.html`, **delete it** rather than relying on `FilesMatch`.

### 4. Add PHP code to functions.php

Add the contents of both PHP files to your active theme's `functions.php`
(or create a custom must-use plugin under `wp-content/mu-plugins/`):

- `functions-security.php` — security hardening (user enumeration, EXIF, etc.)
- `functions-auth.php` — JWT payload filter + `[dangerfinger_configurator]` shortcode

### 5. WordPress admin changes

- **Disable open registration**: Settings → General → uncheck "Anyone can register"
- **Fix HTTPS**: Settings → General → ensure WordPress Address and Site Address both use `https://`
- **Consolidate form plugins**: keep only one of Ninja Forms / Pirate Forms / WPForms;
  deactivate and delete the others from Plugins → Installed Plugins

### 6. Create the configurator page

Create a new WordPress Page at permalink `/prosthetics/configure` with this shortcode:

```
[dangerfinger_configurator url="https://YOUR_AWS_APP_URL"]
```

### 7. Verify the JWT endpoint

```bash
curl -X POST https://dangercreations.com/wp-json/jwt-auth/v1/token \
     -H "Content-Type: application/json" \
     -d '{"username":"YOUR_USERNAME","password":"YOUR_APP_PASSWORD"}'
```

Expected response:
```json
{
  "token": "eyJ...",
  "user_email": "you@example.com",
  "user_nicename": "your-username",
  "user_display_name": "Your Name"
}
```

### 8. Configure the Tornado server

Set these environment variables (see `docker/env-example.txt`):

```
jwt_secret=SAME_KEY_AS_JWT_AUTH_SECRET_KEY_IN_WP_CONFIG
wp_auth_url=https://dangercreations.com
app_base_url=https://YOUR_AWS_APP_URL
```

## Files in this directory

| File | Purpose |
|------|---------|
| `README.md` | This file |
| `functions-security.php` | WP security hardening |
| `functions-auth.php` | JWT filter + shortcode |
| `htaccess-additions.txt` | Security blocks (user enum, XML-RPC, version disclosure) |
| `wp-config-additions.txt` | JWT plugin config + HTTPS + app URL |

## Live configuration reference

These values are currently set on dangercreations.com:

- **JWT plugin**: JWT Authentication for WP REST API v1.5.0 (active)
- **Active theme**: kale (functions.php has all filters + shortcode)
- **Configure page**: `/prosthetics/configure` (page ID 1227, child of Prosthetics ID 9)
- **siteurl / home**: `https://dangercreations.com`
- **users_can_register**: `0` (disabled)
- **Deactivated plugins**: `pirate-forms`, `wpforms-lite` (kept `ninja-forms`)
- **Deleted files**: `readme.html`, `license.txt` (version disclosure)
- **Blocked via .htaccess**: `?author=N` enumeration, `xmlrpc.php`
- **Blocked via PHP filter**: `/wp-json/wp/v2/users` (REST user enumeration)

SSH access and gotchas are documented in `.cursor/rules/wordpress-integration.mdc`.
