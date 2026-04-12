# Parametric Feedback Loop

Automated validation and visual review of the parametric finger model. Run the full pipeline, interpret artifacts, and iterate on model changes.

## When to use

- After any change to `danger/` model code (finger.py, finger_params.py, finger_base.py)
- After parameter range or profile changes
- Before deploying geometry changes
- When the user asks to "test", "validate", or "review" the model

## Quick start

### Fast check (Tier 1 only, ~2 min, no OpenSCAD needed)
```bash
make test-parametric-fast
```
Runs: 261 pytest cases, SCAD hash baseline comparison, 77-case SCAD-only param audit.

### Full check (all 3 tiers, ~3-4 min, needs Docker for OpenSCAD)
```bash
make test-parametric
```
Adds: STL rendering + bounding box checks, visual web UI verification with 36+ multi-angle screenshots.

### Visual review only (needs running server)
```bash
make serve-local &   # start server on port 8092
make visual-review   # capture multi-angle screenshots
```

## Artifacts

All artifacts are in `output/`:

| Artifact | Purpose |
|----------|---------|
| `parametric-report.md` | Human-readable summary of all tiers |
| `parametric-report.json` | Machine-readable for agent consumption |
| `visual-review/report.html` | HTML gallery with all 36+ screenshots |
| `visual-review/summary.json` | Image count, part list, console errors |
| `visual-review/assembled-*.png` | Assembled model from 6 angles |
| `visual-review/exploded-*.png` | Exploded view from 2 angles |
| `visual-review/part-*-*.png` | Each part isolated from 4 angles |
| `viewer-screenshot.png` | Quick 3D viewer screenshot |
| `ui-inspect.txt` | Detailed UI state inspection |

## Interpreting results

### Tier 1 failures
- **pytest fail**: Read the test output — usually a parameter validation or build error
- **SCAD baseline CHANGED**: Geometry changed. If intentional, run `make update-scad-baseline`
- **SCAD audit fail**: A parameter combination crashes or produces degenerate geometry

### Tier 2 failures
- **bbox check fail**: STL has collapsed dimension or unreasonable size
- **STL render fail**: OpenSCAD couldn't render the SCAD (usually invalid geometry)

### Tier 3 failures
- **Server startup fail**: Check if port 8092 is in use, or OpenSCAD wrapper isn't working
- **Preview error**: The web UI reported an error in preview_status
- **Visual review**: Open `output/visual-review/report.html` to inspect individual parts

## Iteration workflow

1. Make a model change in `danger/`
2. Run `make test-parametric-fast` for quick validation
3. If Tier 1 passes, run `make test-parametric` for full visual review
4. Read the report: `cat output/parametric-report.md`
5. Open visual review: `open output/visual-review/report.html`
6. If SCAD baseline changed intentionally: `make update-scad-baseline`
7. Show the user key screenshots from `output/visual-review/` for approval

## Architecture

```
Tier 1 (no OpenSCAD)     Tier 2 (OpenSCAD)        Tier 3 (OpenSCAD + Playwright)
├─ pytest                 ├─ param_audit.py         ├─ local web server
├─ SCAD baseline hash     │  (STL render + bbox)    ├─ inspect_ui.py
└─ param_audit --skip-stl └─ geometry_checks.py     └─ visual_review.py (36+ screenshots)
                                   │                          │
                                   └── OPENSCAD_EXEC ─────────┘
                                       (bin/openscad-docker)
```

## Key files

- `scripts/parametric_report.py` — orchestrator, runs all tiers
- `scripts/visual_review.py` — multi-angle Playwright screenshot capture
- `scripts/param_audit.py` — parameter sweep with optional STL rendering
- `scripts/verify_web_ui.sh` — server lifecycle + inspection + visual review
- `bin/openscad-docker` — OpenSCAD CLI via Docker (transparent wrapper)
- `danger/geometry_checks.py` — bbox extraction, degenerate checks
