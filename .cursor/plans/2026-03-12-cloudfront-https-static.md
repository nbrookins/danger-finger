# Add CloudFront HTTPS for Static Site (WP iframe fix)

**Date**: 2026-03-12  
**Status**: completed

## Goal
The WordPress iframe embedding the configurator is blank because `DANGERFINGER_APP_URL` points to an HTTP URL (`http://34.207.226.194:8081` or `http://danger-finger-static.s3-website-...`) while the WP site is HTTPS. Browsers block HTTP iframes in HTTPS pages (mixed content). Adding a CloudFront distribution gives the static site an HTTPS URL which can be embedded in the WP iframe.

## Steps
1. Add `aws_cloudfront_distribution` resource to `infra/static.tf`
2. Add `static_site_https_url` output to `infra/outputs.tf`
3. Update Makefile: `STATIC_SITE_URL` and `RENDER_URL` default to CloudFront URL
4. Run `terraform apply` to create CloudFront distribution (~5–10 min propagation)
5. Restart EC2 container with updated `STATIC_SITE_URL` env var (allows CloudFront origin for CORS)
6. Update `wp-config-additions.txt` to document using CloudFront HTTPS URL for `DANGERFINGER_APP_URL`
7. Update WP wp-config.php `DANGERFINGER_APP_URL` to CloudFront URL

## Key decisions
- CloudFront origin: S3 website endpoint (HTTP) — CloudFront handles HTTPS termination
- Price class: PriceClass_100 (US + Europe, cheapest ~$0.01/month)
- No custom domain cert needed: uses `*.cloudfront.net` default cert
- HTML TTL: 0s so deploys are immediately visible; JS/CSS: 300s default
- S3 bucket stays public (CloudFront just proxies; no OAI needed since bucket is public)

## Files affected
- `infra/static.tf` — Add CloudFront distribution
- `infra/outputs.tf` — Add `static_site_https_url` output
- `Makefile` — Use `static_site_https_url` for `STATIC_SITE_URL` default
- `wordpress/dangerfinger-setup/wp-config-additions.txt` — Update URL example

## Outcome
CloudFront distribution created: `https://d1n87lopz9qnnf.cloudfront.net`  
Static site redeployed with `staticSiteUrl` injected as CloudFront URL.  
EC2 restarted with `static_site_url=https://d1n87lopz9qnnf.cloudfront.net` for CORS.  
**Remaining manual step**: update `DANGERFINGER_APP_URL` in WP wp-config.php to `https://d1n87lopz9qnnf.cloudfront.net`.
