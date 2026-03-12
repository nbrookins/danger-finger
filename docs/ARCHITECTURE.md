# Architecture

This document describes the system architecture of the danger-finger project: how user measurements become printable prosthetic finger STLs, and how the code is organized.

---

## System overview

```
User (browser)
  │  measurements / parameter values
  ▼
index.html + JS modules (api.js, params.js, viewer.js, app.js)
  │  POST /api/preview  or  POST /api/render
  ▼
server.py (Tornado, port 8081)
  │  config hashing, deduplication
  ▼
build() → DangerFinger.build()
  │  SolidPython2 CSG tree → scad_render() → .scad string
  ▼
Scad_Renderer.scad_to_stl()
  │  subprocess: openscad --export-format binstl -o part.stl part.scad
  ▼
.stl files (binary STL)
  │
  ├──(preview)──→ temp dir → served as /api/preview/temp/{run_id}/{part}.stl
  │
  └──(render)───→ bundle.zip (STL + SCAD + config + LICENSE + README)
                    → S3: render/{cfghash}/bundle.zip
                    → Lambda proxy for browser reads
```

---

## Class hierarchy

```
DangerFingerParams          (finger_params.py)
  │  ~80 Prop descriptors (user-facing parameters)
  │  ~20 computed properties (intermediate_width_, tip_radius, etc.)
  │  Preview config: _preview_position_offsets, _preview_rotate_offsets, etc.
  │  compute_preview_positions(), compute_preview_plug_instances()
  │  validate_params(), get_params()
  │
  ▼
DangerFingerBase            (finger_base.py)
  │  build() — iterates FingerPart enum, calls part_xxx(), applies transforms
  │  _part_composite() — assembles multi-part views (all, explode)
  │  scad_header() — $fa/$fs quality settings
  │  Custom primitives: rcylinder, rcube, rcubecyl, trim, flaredcyl, circular_text
  │
  ▼
DangerFinger                (finger.py)
  │  VERSION = 5.3
  │  Class constants: ANCHOR_OFFSET_DISTAL, TENDON_CUT_ROTATE, etc.
  │  PART_COLORS dict
  │  part_base(), part_tip(), part_middle(), part_linkage(), part_socket(),
  │  part_tipcover(), part_plug(), part_peg(), part_pins(), part_stand(), part_bumper()
  │  Shared primitives: knuckle_outer, knuckle_inner, bridge, bridge_anchor,
  │  socket_interface, tendon_hole, elastic_hole, tip_interface, link_hook, etc.
```

Supporting classes:

| Class | File | Role |
|-------|------|------|
| `Prop` | `Params.py` | Descriptor enforcing min/max, metadata (docs, adv, hidden), getter/setter hooks |
| `Params` | `Params.py` | Static utility: CLI parsing, config open/save/apply, env var override |
| `Borg` | `Scad_Renderer.py` | Singleton pattern (shared `_shared_state` dict) |
| `Scad_Renderer(Borg)` | `Scad_Renderer.py` | OpenSCAD subprocess management, parallel rendering, multi-view PNG |
| `FingerServer(Borg)` | `server.py` | S3 client (boto3), brotli-compressed storage, config/profile/bundle CRUD |

Enums (`constants.py`):

| Enum | Type | Purpose |
|------|------|---------|
| `Orient` | IntFlag | PROXIMAL, DISTAL, INNER, OUTER, UNIVERSAL, MIDDLE — composable orientation flags |
| `FingerPart` | IntFlag | SOCKET, BASE, MIDDLE, TIP, TIPCOVER, LINKAGE, PLUG, PEG, BUMPER, STAND, PINS, ALL, EXPLODE |
| `BumperStyle` | Enum | NONE, MINIMAL, COVER, FULL |
| `RenderQuality` | Enum | INSANE through STUPIDFAST — controls OpenSCAD $fa/$fs |
| `CustomType` | IntFlag | UI widget hints (SLIDER, DROPDOWN, etc.) |

---

## The Prop descriptor system

`Prop` is a Python descriptor that replaces `@property` for configurable parameters. It stores a default value and enforces min/max bounds on every `__set__`.

```python
class Prop:
    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, obj, value):
        if self._setter: value = self._setter(self, obj, value)
        setattr(obj, "__" + self.name, self.minmax(value, self._min, self._max))

    def __get__(self, obj, objtype=None):
        if obj is None: return self       # class-level access returns Prop itself
        if self._getter: return self._getter(self, obj, objtype)
        val = getattr(obj, "__" + self.name, None)
        return val if val is not None else self._value  # fall back to default
```

Key behaviors:
- Instance values stored as `obj.__paramname` (name-mangled to avoid collision)
- Class-level access (`DangerFingerParams.intermediate_length`) returns the `Prop` object (used by `get_params()` introspection)
- `get_params(adv=False, allv=True, extended=True)` iterates `Prop` descriptors via `inspect.getmembers` and returns metadata dicts for the frontend
- Custom setters handle enum conversion (e.g., `_bumper_style_setter` converts string to `BumperStyle`)

---

## Build pipeline

### 1. `DangerFingerBase.build()`

```python
for _, pv in FingerPart.__members__.items():
    name = str.lower(pv.name)
    self._parts[name] = self.part(pv)       # calls part_xxx() or _part_composite()
    # Apply print-orientation transforms
    if rotates and not isinstance(rotates, dict):
        temp = rotate(rotates)(temp)         # _rotate_offsets[name]
    if offsets and not isinstance(offsets, dict):
        temp = translate(offsets)(temp)       # _translate_offsets[name]
    temp = flatten(temp)
    self._models[name] = temp.render() if self.scad_render else temp
```

After the loop, a second pass renders each model to SCAD strings via `scad_render()` with quality header ($fa, $fs).

### 2. Per-part methods

Each `part_xxx()` method:
1. Constructs CSG primitives (cylinders, cubes, hulls)
2. Combines them additively and subtractively
3. Returns the final SolidPython2 object (not yet SCAD text)
4. The `build()` loop applies `.render()` which evaluates lazy CSG into a concrete tree

### 3. Print orientation

`_rotate_offsets` (dict of part name -> `(rx, ry, rz)`) rotate each part from its natural assembled orientation into optimal FDM print orientation. This happens in `build()` and affects the exported STL files.

The web viewer reverses this with `_preview_rotate_offsets` (approximate inverse rotations applied in the browser). See `docs/VIEWER_ASSEMBLY.md`.

### 4. SCAD rendering to STL

`Scad_Renderer.scad_to_stl()` calls OpenSCAD via subprocess:
```
openscad --enable manifold --export-format binstl -o part.stl part.scad
```

`scad_parallel()` runs multiple parts concurrently using `asyncio` with configurable `max_concurrent_tasks`. PNG previews can be generated simultaneously using `--preview --imgsize`.

---

## Server architecture

### Tornado handlers

| Route | Handler | Method | Purpose |
|-------|---------|--------|---------|
| `/` | `IndexHandler` | GET | Serves `index.html` with build-ID-stamped `?v=` cache busters |
| `/api/parts` | `ApiPartsHandler` | GET | Part list, version, build ID, preview config |
| `/api/preview` | `ApiPreviewHandler` | POST | Sync preview: build all parts, serve temp STLs |
| `/api/render` | `ApiRenderHandler` | POST | Sync render: build + bundle.zip to S3 |
| `/api/preview/temp/...` | `ApiPreviewTempHandler` | GET | Serve temp STL files from disk |
| `/params/...` | `FingerHandler` | GET | Parameter metadata (extended JSON) |
| `/profile/.../config/...` | `FingerHandler` | POST/DELETE | Save/remove config in S3 profile |
| `/profiles/...`, `/configs/...`, `/render/...` | `FingerHandler` | GET | S3 read fallback (primary is Lambda) |
| `/(*)` | `StaticHandler` | GET | Static files from `web/` |

### Preview vs render

- **Preview** (`/api/preview`): EXTRAMEDIUM quality, temp directory, no S3. Files served via `/api/preview/temp/{run_id}/`. Run directory cleaned on next request.
- **Render** (`/api/render` or via `/profile/.../config/...`): HIGH quality, creates `bundle.zip` in S3. Config and profile updated atomically.

Both use `_run_sync_preview_or_render()` in a `ThreadPoolExecutor` with a 10-second timeout.

### Config hashing

`package_config_json()` removes default-value params, sorts keys, SHA-256 hashes the JSON. Identical configs always produce the same `cfghash`, enabling deduplication.

### S3 layout

```
configs/{cfghash}          — JSON config (brotli-compressed with "42" prefix)
profiles/{userhash}        — JSON profile with configs map (brotli)
render/{cfghash}/bundle.zip — ZIP containing STLs, SCADs, config.json, LICENSE, README
```

---

## Frontend architecture

Four vanilla JS modules loaded as global IIFEs (no bundler):

### `api.js` — HTTP client
- XHR-based, three base URLs: `baseurl` (default/relative), `readUrl` (Lambda reads), `renderUrl` (EC2 render API)
- `requestPreview()` debounced at 500ms, uses `renderUrl` with graceful offline detection
- `saveConfig()`/`deleteConfig()` also route through `renderUrl`
- `fetchBundleZip()` uses `arraybuffer` responseType for JSZip extraction
- Network errors (status 0) on render endpoints show "server offline" message

### `params.js` — Parameter form
- Renders parameter table from `/params/all` metadata
- Standard params visible by default; advanced in collapsible section
- Tracks dirty (unsaved) and changed (differs from default) states per param
- `getCurrentParams()` returns current form values as `{name: numericValue}` dict

### `viewer.js` — 3D viewer manager
- Wraps `StlViewer` (Three.js r160 compatibility wrapper)
- Manages part ID -> mesh mapping, plug instances (IDs 100-103), explode slider
- `applyPreviewConfig()` sets positions/rotations/explode offsets from server
- `updateFromStlUrls()` removes all models and re-adds from new URL map
- `PREVIEW_SKIP_PARTS = { "pins": true }` — pins excluded because composite STL cannot be correctly positioned

### `app.js` — Orchestrator
- Initializes all modules, wires callbacks
- Manages profile table, save/load/download workflow
- `loadBundleZip()` — fetches ZIP via Lambda, extracts STLs with JSZip, creates blob URLs

### `stl_viewer.js` — Three.js wrapper
- Compatibility wrapper over Three.js r160 + STLLoader r170 + OrbitControls r170
- Replicates the exact `StlViewer` API used by `viewer.js`
- Transform pipeline: load STL -> bbox center -> rotate (world-axis X/Y/Z) -> set position
- See `docs/VIEWER_ASSEMBLY.md` for transform semantics

---

## Docker

`docker/Dockerfile` is based on `openscad/openscad:trixie.2025-12-15` (Debian with OpenSCAD pre-installed). Python 3 venv with solidpython2, tornado, boto3, brotli. Entry point runs `server.py`.

The container serves both the web UI and performs OpenSCAD rendering. No separate worker process.

---

## Testing infrastructure

| Target | Script | What it tests |
|--------|--------|---------------|
| `make test-web` | `scripts/test_web.sh` | Fresh local server, hits /, /api/parts, POST /api/preview |
| `make kbr-test` | Makefile inline | Docker build + run + test |
| `make verify-web-ui` | `scripts/verify_web_ui.sh` | Docker container + Playwright screenshot |
| `make inspect-ui` | `scripts/inspect_ui.py` | Playwright against running server |
| `make reference-stls` | `scripts/reference_stls.py` | Build baseline STL checksums |
| `make regression-check` | `scripts/regression_check.py` | Compare current STLs to baseline |
| `make validate-formula` | `scripts/validate_formula.py` | Sweep params, check geometry |
| `pytest` | `tests/test_*.py` | Unit tests: param sweep, boundary, smoke |
