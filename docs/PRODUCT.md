# Product requirements and design decisions

This document is the running record of product requirements and design decisions for the Danger Finger project. Update it as the product and architecture evolve.

---

## Product requirements

### Goals

- **Web UI**: View and configure the finger prosthetic (STL) in the browser, change parameters with live preview, filter parts, and save/load configs (with auth where needed).
- **Backend**: Support both quick preview (ephemeral, no S3) and full render (stored in S3); keep operations synchronous with a reasonable timeout (e.g. ≤10 s) and run OpenSCAD on the server (not Lambda).
- **Profiles**: Users can save configs under a profile; profile stores config name → cfghash and history for save-in-place and history.

### User-facing features

- 3D viewer for finger parts (tip, middle, base, linkage, etc.) with part visibility toggles (e.g. checkboxes).
- Parameter form: standard parameters visible by default; advanced parameters in a separate section below when “Advanced” is selected. Parameters show descriptions (from API) and feedback for modified values.
- Explode slider: when non-exploded, parts are positioned as assembled (preview position); when exploded, parts move along explode offsets. Same STLs throughout.
- Save config: name and save under current user profile; triggers sync render and stores bundle.zip (STL + SCAD + config + LICENSE + README) in S3. Download link shown on completion.
- Load saved config: fetches bundle.zip from S3 via Lambda, extracts STLs client-side with JSZip, feeds to viewer. Download reuses cached ZIP blob.
- Remove saved configs from profile list.
- Download ZIP: available per-row in saved configs table and after save/load. Same `render/{cfghash}/bundle.zip` object used for viewer load and download — no re-fetch.
- Preview: on param change (debounced), request preview; viewer updates from temp STL URLs. No S3 for preview.

### Non-goals / later

- WordPress auth (optional later).
- Automated cleanup of dereferenced S3 objects (optional later).
- OpenSCAD WASM rendering in Lambda (blocked: openscad-wasm lacks Manifold, 100-660x slower than native).

---

## Design decisions

### Backend

| Decision | Rationale |
|----------|-----------|
| **Sync preview and render on server** | Predictable latency and simpler than queue + worker for current scale; 10 s timeout keeps UX responsive. |
| **OpenSCAD on server (not Lambda)** | Docker image already has OpenSCAD; avoids cold starts and payload limits. Container writes to S3; reads go through Lambda. |
| **Preview STLs in temp dir, not S3** | Previews are ephemeral; avoid S3 churn and cost. |
| **ZIP-only storage: `render/{cfghash}/bundle.zip`** | Single compressed object per config containing all STLs, SCAD, config JSON, LICENSE, README. Used for both viewer load (JSZip extraction in-browser) and download. 63% less storage, 33% less egress, 85% fewer requests vs individual STLs. cfghash immutability means no invalidation needed. |
| **Lambda for S3 reads (API Gateway + Lambda)** | Protects AWS credentials from client. Single Python handler with path-based routing: `/configs/{cfghash}`, `/profiles/{userhash}`, `/render/{cfghash}/bundle.zip`. Presigned URL redirect for ZIPs > 5 MB. SAM template at `template.yaml`. |
| **Profile stores `configs[name] = { cfghash, history }`** | Save-in-place and history without storing full config blob in profile. |
| **`/api/params` and `/api/params/all`** | Explicit routes for parameter definitions; frontend uses these instead of legacy `/params` regex route. |
| **`DangerFinger().params()` as a method (not property)** | Server needs to call `params(adv=..., allv=..., extended=True)`; property cannot take arguments. |
| **Print orientation vs preview display** | STLs are exported in print orientation (rotate_offsets) for slicing. Preview applies preview_rotate_offsets and preview position/explode in the viewer only; no duplicate STLs. |
| **`/api/parts` returns preview config** | Each part includes preview_position, explode_offset, preview_rotation (degrees), and hidden_in_preview so the viewer can display parts as an assembled finger and support explode without changing STL files. Plug is expanded to plug_0..plug_3 (same STL via `stl_part`); linkage uses a preview-only position override so it appears behind the finger/socket. |
| **stl_viewer centers geometry by default** | `stl_viewer.js` calls `geometry.computeBoundingBox()` + `translate(-center)` on load, moving the bbox center to the local origin (replicates old `geometry.center()` behavior). `_preview_position_offsets` must therefore specify the assembled-space bounding box center of each part. See `docs/VIEWER_ASSEMBLY.md`. |
| **stl_viewer rotates around world axis** | `add_model` uses `mesh.rotateOnWorldAxis(axis, angle)` X→Y→Z (world-space pre-multiply, equivalent to old `rotateAroundWorldAxis`). With geometry centered at origin, this rotates each part around its own center. Position from `mod_loaded` is set after rotation. |
| **preview_position_offsets fixed for v5.2+ print rotations** | Positions updated to assembled bbox centers measured from v5.1 STLs. Previously all zeros causing parts to overlap at viewer origin. See `docs/VIEWER_ASSEMBLY.md` section 3.2. |
| **SCAD all reference uses preview_rotate=False** | `preview_rotate = False` is hard-coded. `_part_composite` does NOT apply `_rotate_offsets["all"]`. The all.png is the assembled-orientation reference. |
| **OpenSCAD ARM64 workaround** | On macOS ARM64, Qt runtime check fails. Fix: prepend `arch -x86_64` in `Scad_Renderer.py` (Rosetta). `OPENSCAD_USE_ROSETTA` env var. Headless PNG needs Xvfb. |

### Frontend

| Decision | Rationale |
|----------|-----------|
| **JSZip for viewer load from bundle.zip** | Load config fetches single ZIP via Lambda, extracts STLs in-browser (~30-50 ms), creates blob URLs for Three.js viewer. Same blob reused for download — zero re-fetch. |
| **Dual base URLs (`baseurl` / `readUrl`)** | Write operations (preview, save) go to Tornado container. Read operations (configs, profiles, render bundles) go to Lambda via API Gateway. Fallback: `readUrl` defaults to `baseurl` when Lambda is not deployed. |
| **Part visibility via checkboxes** | Clearer than toggle buttons; re-show part using `last_stl_urls` so toggling back on uses current preview URL. |
| **Parameters: Standard first, Advanced section below** | Matches typical config UIs; Advanced hidden until selected. |
| **Parameter descriptions from API** | API returns `Documentation` (from param docs); shown as tooltip and optional short description under label. |
| **Modified feedback (badge + row highlight)** | Users can see which params differ from default. |
| **Viewer errors surfaced in UI** | `#viewer_error` and `set_viewer_error()`; try/catch and `stl_viewer.error` reported in status so failures are visible. |
| **Request preview from viewer `ready_callback`** | First preview runs after viewer is ready so models load correctly. |

### DevOps / testing

| Decision | Rationale |
|----------|-----------|
| **`make kbr-test`** | Build, run container in background, then run e2e test against it so we test the real Docker stack. |
| **`USE_EXISTING_SERVER=1` in test script** | Allows hitting an already-running server (e.g. Docker on 8081) without starting a second process. |
| **Test port 8091 when starting server in script** | Avoids clashing with Docker on 8081. |
| **`make inspect-ui` (Playwright)** | Headless browser loads the live UI, captures `#preview_status`, `#viewer_error`, and console; writes `output/ui-inspect.txt`. Exit 1 if the UI shows an error. Use when debugging “error and no preview” or to capture exactly what the page shows. Requires `pip install -r requirements-dev.txt` and `python -m playwright install chromium`. |

---

## Infrastructure & Deployment

The application deploys to AWS using Terraform-managed infrastructure. See [DEPLOY.md](DEPLOY.md) for full details.

**Components**: EC2 (Docker + OpenSCAD, handles writes), Lambda + API Gateway (read-only S3 API), S3 (persistent storage), ECR (image registry).

**Key files**: `infra/*.tf` (Terraform), `.github/workflows/deploy.yml` (CI/CD), `scripts/verify_aws_deploy.sh` (smoke tests), `scripts/aws_audit.py` (account audit), `scripts/benchmark_ec2.py` (instance benchmarking).

**Cursor rules**: `.cursor/rules/aws-deploy.mdc` (deployment safety), `.cursor/rules/terraform-conventions.mdc` (Terraform style). **Skill**: `.cursor/skills/deploy-to-aws/SKILL.md`.

---

## Changelog

- **2026-03** – AWS deployment infrastructure: audited and cleaned stale ECS/CloudFormation resources (~$20-26/mo savings), created Terraform configs (VPC, ECR, EC2, Lambda, API Gateway, S3, IAM, optional Route53/ACM), Makefile deploy targets, GitHub Actions CI/CD with OIDC, deployment verification scripts, and Cursor rules/skills. EC2 uses IAM instance profile (no static keys); server.py falls back to default credential chain; app.js reads `window.__READ_URL__` injected at serve time.
- **2026-03** – Save/load/download workflow and Lambda S3 access. Render now produces a single `render/{cfghash}/bundle.zip` containing all STLs, SCAD files, config JSON, LICENSE, and README — no individual STL files in S3. Frontend uses JSZip to extract STLs in-browser for viewer load; same cached blob serves as download (zero re-fetch). Save endpoint returns cfghash so frontend can show immediate download link. Added Lambda function + SAM template (`template.yaml`, `lambda/handler.py`) for S3 read operations (configs, profiles, bundles) via API Gateway — protects AWS credentials from client. Frontend dual base URL (`baseurl` for writes, `readUrl` for reads). Removed legacy S3 queue system (`process_scad_loop`, `queue()`, `.mod` files), `serve_download`, `downloads/` prefix, and individual STL upload code. Saved configs table now has Load/Download/Remove columns. Render status indicator shown during save with Save button disabled.
- **2026-03** – Replaced `stl_viewer.min.js` (StlViewer v1.08 / Three.js r86) with `web/stl_viewer.js`: thin wrapper over Three.js r160 (last UMD build) + STLLoader r170 + OrbitControls r170 (adapted to global scripts). Vendored under `web/vendor/three/`. Transform semantics (centering, world-axis rotation) preserved exactly. `get_model_info` returns `{ pos: [x,y,z] }` array for `inspect_ui.py` compatibility.
- **2026-03** – Fixed viewer assembly: `_preview_position_offsets` set to assembled bbox centers from v5.1 STLs; removed legacy 35° Z from tip/tipcover `_preview_rotate_offsets`. Created `docs/VIEWER_ASSEMBLY.md` documenting stl_viewer behaviour, coordinate system, and OpenSCAD ARM64 workaround. Added `.cursor/rules/fix-preview-positions.mdc`.
- **2026-03** – Four plug instances in preview: one plug STL shown four times (plug_0..plug_3) with per-instance position/rotation so plugs appear in tip holes; linkage preview position override so it displays behind the finger/socket. `/api/parts` expands plug and returns `stl_part` for URL lookup; frontend iterates part list and uses `stl_part` when resolving STL URLs.
- **2026-03** – Preview rotate offsets and preview config: STLs stay print-oriented; viewer applies preview_rotate_offsets, preview_position, and explode_offset from `/api/parts` so preview looks like an assembled finger and explode works without duplicating STLs. Stand hidden in preview by default. Cursor rule to keep docs updated.
- **2026-03** – Initial product/design doc; viewer error surfacing; parameter descriptions; part visibility checkboxes; Standard/Advanced layout; PRD + design decisions captured.

---

## Related documentation

- [Architecture](ARCHITECTURE.md) — system pipeline, class hierarchy, build flow, server, frontend
- [Parts Anatomy](PARTS_ANATOMY.md) — physical design of each part, mechanical connections, materials, known TODOs
- [CSG Patterns](CSG_PATTERNS.md) — SolidPython2 idioms, custom primitives, modeling patterns
- [Parameters](PARAMETERS.md) — parameter definitions, preview vs print orientation
- [Viewer Assembly](VIEWER_ASSEMBLY.md) — how the web viewer positions and rotates parts

## Cursor rules index

| Rule | Scope | Purpose |
|------|-------|---------|
| `parametric-consistency.mdc` | `finger_params.py`, `finger.py`, `finger_base.py` | Cascade checking, fewer-params principle |
| `csg-modeling-guide.mdc` | `finger.py`, `finger_base.py` | Primitive reference, geometry rules |
| `part-physical-context.mdc` | `finger.py` | Read physical context before modifying geometry |
| `coordinate-systems.mdc` | `finger_params.py`, `finger.py`, `viewer.js`, `stl_viewer.js` | Three coordinate spaces |
| `prop-system.mdc` | `Params.py`, `finger_params.py` | How the Prop descriptor works |
| `fix-preview-positions.mdc` | `finger_params.py`, `server.py`, `index.html` | Empirical fix for viewer preview positions |
| `web-ui-inspection.mdc` | `web/**`, `finger_params.py`, `scripts/*` | Never trust a running server; screenshot verification |
| `scad-preview.mdc` | `finger.py`, `server.py`, `scripts/*` | SCAD preview PNG verification |
| `testing-and-make.mdc` | `scripts/*`, `Makefile`, `tests/**` | Use project make targets |
| `keep-docs-updated.mdc` | `danger/**`, `web/**`, `scripts/*`, `Makefile` | Keep docs updated on changes |
| `archive-execution-plans.mdc` | Always | Archive plans to `.cursor/plans/` |
