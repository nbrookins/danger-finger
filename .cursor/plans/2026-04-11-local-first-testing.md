# Local-First Testing Architecture

**Date**: 2026-04-11
**Status**: completed

## Goal
Replace Docker container orchestration in the testing pipeline with a local-first approach. OpenSCAD runs via a thin Docker CLI wrapper (`bin/openscad-docker`), but the web server, Playwright, and pytest all run natively. This eliminates sandbox permission prompts, reduces iteration time, and enables fully autonomous pipeline runs.

## Steps
1. Fix .venv (Python 3.11 + all deps + Playwright Chromium)
2. Create `bin/openscad-docker` wrapper (Docker CLI, not containers)
3. Fix `Scad_Renderer` to honor `OPENSCAD_EXEC` env var over macOS default
4. Add `make serve-local` target
5. Rewrite `scripts/parametric_report.py` — no Docker orchestration
6. Rewrite `scripts/verify_web_ui.sh` — local server mode as default
7. Fix `visual_review.py` plug visibility + camera tuning
8. Consolidate Makefile targets
9. Create `prompt.md`, rules, skill docs

## Key decisions
- `bin/openscad-docker` uses `docker run --rm` with `--mount` (not `-v`) for iCloud path safety
- `OPENSCAD_EXEC` env var takes priority over macOS OpenSCAD.app detection
- Default `VERIFY_PORT` is 8092 (avoids collision with dev server on 8081)
- `make test-parametric` now means "all tiers, locally" (was Docker-dependent)
- `make test-parametric-fast` replaces old `SKIP_DOCKER=1` mode
- macOS `/bin/bash` is v3 — wrapper avoids `declare -A` (associative arrays)

## Files affected
- `bin/openscad-docker` — new, Docker CLI wrapper
- `Makefile` — restructured testing targets, added PYTHON/OPENSCAD_EXEC vars
- `scripts/parametric_report.py` — full rewrite, no Docker orchestration
- `scripts/verify_web_ui.sh` — rewritten for local-first, Docker mode opt-in
- `scripts/visual_review.py` — plug visibility fix, camera distance tuning
- `danger/Scad_Renderer.py` — OPENSCAD_EXEC env var priority fix
- `prompt.md` — new project identity file
- `.cursor/rules/local-first-testing.mdc` — new rule
- `.cursor/rules/openscad-docker-wrapper.mdc` — new rule
- `.cursor/rules/docker-tier2-tier3-integration.mdc` — marked superseded
- `.cursor/skills/parametric-feedback-loop/SKILL.md` — new skill

## Outcome
Full 3-tier pipeline passes (`make test-parametric`) with **zero sandbox prompts**:
- Tier 1: 261 pytest cases + SCAD baseline (13 parts unchanged) + 77-case SCAD audit — 95s
- Tier 2: Full param audit with STL rendering via native OpenSCAD — 13s
- Tier 3: Visual web UI verification with Playwright (36+ screenshots, HTML report) — 222s
- Total: ~330s

Key insight: Cursor's sandbox blocks Docker socket, Qt sysctl (OpenSCAD), AND Chromium process launch. Solution was a "dev-server" pattern: user runs `make start-dev` once in a terminal (outside sandbox), which starts OpenSCAD HTTP server (port 9876) and headless Chromium with CDP (port 9222). Pipeline discovers services via `.dev-server.json` and connects via localhost.

Additional files created beyond original plan:
- `bin/dev-server` — combined OpenSCAD + Chromium service
- `bin/openscad-local` — CLI wrapper that POSTs to dev-server
- `scripts/pw_connect.py` — Playwright CDP connection helper
- `.cursor/rules/dev-server-pattern.mdc` — documents the pattern

OpenSCAD installed via `brew install --cask openscad@snapshot` (2026.04.08) — native arm64, 179ms per render vs 5s+ via Docker.
