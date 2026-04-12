# DangerFinger

Parametric prosthetic finger — a customizable, 3D-printable mechanical finger prosthesis. Users configure parameters through a web UI, preview the assembled model in a Three.js viewer, and download STL files for printing.

## Stack

- **Geometry**: Python + SolidPython2 → OpenSCAD SCAD → STL
- **Web**: Tornado server, Three.js viewer, Playwright for automated visual testing
- **Deploy**: Docker image on EC2 (via ECR), static assets on S3 + CloudFront
- **Testing**: pytest, SCAD hash baselines, parameter sweep audits, multi-angle Playwright screenshots

## Key Entry Points

| Task | Command |
|------|---------|
| Start dev services | `make start-dev` (run once in terminal) |
| Run all tests (local) | `make test-parametric` |
| Run fast tests only | `make test-parametric-fast` |
| Start local server | `make serve-local` |
| Visual review only | `make visual-review` (needs running server) |
| Build Docker image | `make build` |
| Deploy to AWS | `make deploy` |

## Testing Philosophy

- **Local-first**: All testing runs natively. Docker is only for deploy.
- **Dev-server pattern**: Run `make start-dev` once in a terminal — this starts an OpenSCAD render server and headless Chromium outside the Cursor sandbox. The pipeline connects via localhost, so all 3 tiers run with zero sandbox prompts.
- **OPENSCAD_EXEC**: Set to `bin/openscad-local` which POSTs to the dev-server's OpenSCAD endpoint. Fallback: `bin/openscad-docker`.
- **Tiered validation**: Tier 1 (fast, no OpenSCAD), Tier 2 (STL render + bbox), Tier 3 (visual web UI via CDP).
- **Artifacts**: `output/parametric-report.md`, `output/visual-review/report.html`, `output/viewer-screenshot.png`.

## Project Structure

- `danger/` — parametric model (finger_params.py, finger.py, finger_base.py, Scad_Renderer.py)
- `web/` — Tornado server + Three.js viewer (server.py, viewer.js, stl_viewer.js)
- `scripts/` — automation (parametric_report.py, visual_review.py, param_audit.py, verify_web_ui.sh)
- `tests/` — pytest suite (param sweeps, profile tests, geometry checks)
- `bin/` — CLI wrappers (openscad-docker)
- `docker/` — Dockerfile + entrypoint for production image
- `infra/` — Terraform for AWS infrastructure
- `docs/` — architecture, deploy, parameters, viewer assembly docs
