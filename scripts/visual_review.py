#!/usr/bin/env python3
"""Multi-angle visual review of the parametric finger model.

Captures:
  - Assembled model from 6 angles (front, back, left, right, top, isometric)
  - Exploded view from 2 angles
  - Each individual part isolated from 4 angles (front, side, top, isometric)
  - Generates an HTML gallery report

Requires: playwright, a running danger-finger server (set BASE_URL env).
"""
import json
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8092")
OUTPUT_DIR = os.environ.get("VISUAL_REVIEW_DIR", "output/visual-review")

# Camera presets: (cam_x, cam_y, cam_z, target_x, target_y, target_z)
# The assembled finger is ~100mm tall along Y, centered roughly at (0, 20, 0)
ASSEMBLED_TARGET = (0, 20, 0)
ASSEMBLED_VIEWS = {
    "front":  (0, 30, 160),
    "back":   (0, 30, -160),
    "left":   (-160, 30, 0),
    "right":  (160, 30, 0),
    "top":    (0, 200, 1),
    "iso":    (100, 80, 120),
}

EXPLODE_VIEWS = {
    "iso":    (120, 100, 140),
    "front":  (0, 40, 200),
}

# Per-part views: camera distance is scaled to the part's bounding sphere
PART_VIEWS = {
    "front": (0, 0, 1),
    "side":  (1, 0, 0),
    "top":   (0, 1, 0.01),
    "iso":   (0.7, 0.5, 0.8),
}

JS_HELPERS = """
window._vr = window._vr || {};
window._vr.getViewer = function() { return Viewer.getStlViewer(); };

window._vr.setCamera = function(cx, cy, cz, tx, ty, tz) {
    var v = window._vr.getViewer();
    v._camera.position.set(cx, cy, cz);
    v._controls.target.set(tx, ty, tz);
    v._controls.update();
    v._renderer.render(v._scene, v._camera);
};

window._vr.waitFrame = function() {
    return new Promise(resolve => requestAnimationFrame(() => {
        requestAnimationFrame(resolve);
    }));
};

window._vr.getPartNames = function() {
    var map = Viewer.getPartNameToId();
    return Object.keys(map);
};

window._vr.getPartIds = function() {
    return Viewer.getPartNameToId();
};

window._vr.showOnly = function(partName) {
    var v = window._vr.getViewer();
    var nameToId = Viewer.getPartNameToId();
    for (var name in nameToId) {
        var id = nameToId[name];
        var entry = v._models[id];
        if (entry) entry.mesh.visible = (name === partName);
    }
    // Hide/show plug instances (ids 100-103)
    for (var i = 100; i < 104; i++) {
        var e = v._models[i];
        if (e) e.mesh.visible = (partName === 'plug');
    }
};

window._vr.showAll = function() {
    var v = window._vr.getViewer();
    for (var id in v._models) {
        if (v._models[id] && v._models[id].mesh) {
            v._models[id].mesh.visible = true;
        }
    }
};

window._vr.getPartBounds = function(partName) {
    var v = window._vr.getViewer();
    var entry = null;
    if (partName === 'plug') {
        // Plug is only loaded as instances (ids 100-103)
        entry = v._models[100];
    } else {
        var nameToId = Viewer.getPartNameToId();
        var id = nameToId[partName];
        if (id === undefined) return null;
        entry = v._models[id];
    }
    if (!entry) return null;
    var mesh = entry.mesh;
    mesh.geometry.computeBoundingBox();
    var bb = mesh.geometry.boundingBox;
    var pos = mesh.position;
    return {
        min: [bb.min.x + pos.x, bb.min.y + pos.y, bb.min.z + pos.z],
        max: [bb.max.x + pos.x, bb.max.y + pos.y, bb.max.z + pos.z],
        center: [(bb.min.x + bb.max.x)/2 + pos.x,
                 (bb.min.y + bb.max.y)/2 + pos.y,
                 (bb.min.z + bb.max.z)/2 + pos.z],
        size: [bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z]
    };
};

window._vr.setExplode = function(pct) {
    var slider = document.getElementById('explode');
    if (!slider) return false;
    var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value').set;
    nativeInputValueSetter.call(slider, pct);
    slider.dispatchEvent(new Event('input', { bubbles: true }));
    return true;
};
"""


def wait_for_preview(page, timeout_ms=90000):
    """Wait until preview is ready or errored. Triggers preview if page doesn't auto-trigger."""
    # Wait briefly for JS to auto-trigger the preview
    try:
        page.wait_for_function(
            """() => {
                const el = document.getElementById('preview_status');
                if (!el || !el.textContent) return false;
                const t = el.textContent.toLowerCase();
                return t.includes('queued') || t.includes('running') || t.includes('ready') || t.includes('error');
            }""",
            timeout=10000,
        )
    except Exception:
        pass  # Will handle below

    # Check if models loaded (preview might have auto-completed)
    mc = page.evaluate("Object.keys(Viewer.getStlViewer()._models).length")
    if mc >= 7:
        print("  Preview auto-completed, %d models loaded" % mc, flush=True)
        return

    # Trigger preview manually via synchronous fetch from browser
    print("  Triggering preview manually...", flush=True)
    preview_resp = page.evaluate("""
        fetch('/api/preview', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({params: {}})
        }).then(r => r.json())
    """)

    if not isinstance(preview_resp, dict):
        print("  Warning: unexpected preview response", flush=True)
        return

    # Handle cached/immediate response (has stl_urls directly)
    result = None
    if preview_resp.get("stl_urls"):
        result = preview_resp
    elif preview_resp.get("job_id"):
        # Async job — poll for completion
        job_id = preview_resp["job_id"]
        print("  Job: %s — polling..." % job_id, flush=True)
        base = page.url.rstrip("/")
        for _ in range(90):
            resp = page.evaluate(
                "fetch('%s/api/jobs/%s').then(r=>r.json())" % (base, job_id)
            )
            status = resp.get("status", "unknown")
            if status == "complete":
                result = resp.get("result")
                break
            elif status == "failed":
                print("  Preview job failed", flush=True)
                return
            time.sleep(2)

    if result and result.get("stl_urls"):
        print("  Loading %d STLs into viewer..." % len(result["stl_urls"]), flush=True)
        page.evaluate("""(res) => {
            Viewer.applyPreviewConfig(res, null);
            Viewer.updateFromStlUrls(res.stl_urls, null);
        }""", result)
        n_expected = len(result["stl_urls"])
        for _wi in range(30):
            mc = page.evaluate(
                "Object.keys(Viewer.getStlViewer()._models).length"
            )
            if mc >= n_expected:
                print("  %d models loaded" % mc, flush=True)
                break
            time.sleep(1)
        time.sleep(2)
    else:
        print("  Warning: no STL URLs in preview result", flush=True)


def inject_helpers(page):
    page.evaluate(JS_HELPERS)


def set_camera(page, cam_pos, target):
    page.evaluate(
        "window._vr.setCamera(%f,%f,%f,%f,%f,%f)" % (*cam_pos, *target)
    )
    page.evaluate("window._vr.waitFrame()")
    time.sleep(0.4)


def capture_viewer(page, path):
    """Screenshot just the 3D viewer element."""
    el = page.locator("#stl_cont, #stl_viewer_container, canvas").first
    if el.count() > 0 and el.is_visible():
        el.screenshot(path=path)
    else:
        page.screenshot(path=path)


def capture_assembled(page, out_dir):
    """Capture assembled model from all angles."""
    page.evaluate("window._vr.showAll()")
    page.evaluate("window._vr.setExplode(0)")
    page.evaluate("window._vr.waitFrame()")
    time.sleep(0.5)
    results = {}
    for name, cam_pos in ASSEMBLED_VIEWS.items():
        path = os.path.join(out_dir, "assembled-%s.png" % name)
        set_camera(page, cam_pos, ASSEMBLED_TARGET)
        capture_viewer(page, path)
        results[name] = path
    return results


def capture_exploded(page, out_dir):
    """Capture exploded view."""
    page.evaluate("window._vr.showAll()")
    page.evaluate("window._vr.setExplode(80)")
    page.evaluate("window._vr.waitFrame()")
    time.sleep(0.8)
    results = {}
    for name, cam_pos in EXPLODE_VIEWS.items():
        path = os.path.join(out_dir, "exploded-%s.png" % name)
        set_camera(page, cam_pos, ASSEMBLED_TARGET)
        capture_viewer(page, path)
        results[name] = path
    page.evaluate("window._vr.setExplode(0)")
    return results


def capture_individual_parts(page, out_dir):
    """Isolate and capture each part from multiple angles."""
    part_names = page.evaluate("window._vr.getPartNames()")
    all_results = {}

    for part_name in part_names:
        page.evaluate("window._vr.showOnly('%s')" % part_name)
        page.evaluate("window._vr.waitFrame()")
        time.sleep(0.3)

        bounds = page.evaluate("window._vr.getPartBounds('%s')" % part_name)
        if not bounds:
            all_results[part_name] = {"error": "no bounds"}
            page.evaluate("window._vr.showAll()")
            continue

        center = bounds["center"]
        size = bounds["size"]
        max_dim = max(size) if size else 30
        cam_dist = max(max_dim * 2.5, 60)

        part_results = {"bounds": bounds}
        for view_name, direction in PART_VIEWS.items():
            cam_pos = (
                center[0] + direction[0] * cam_dist,
                center[1] + direction[1] * cam_dist,
                center[2] + direction[2] * cam_dist,
            )
            target = tuple(center)
            path = os.path.join(out_dir, "part-%s-%s.png" % (part_name, view_name))
            set_camera(page, cam_pos, target)
            capture_viewer(page, path)
            part_results[view_name] = path

        all_results[part_name] = part_results

    page.evaluate("window._vr.showAll()")
    return all_results


def _copy_stls_to_report(out_dir):
    """Copy STL files from the latest preview run into the report directory."""
    import shutil
    stl_dir = os.path.join(out_dir, "stls")
    os.makedirs(stl_dir, exist_ok=True)
    preview_temp = os.path.join("output", "preview_temp")
    if not os.path.isdir(preview_temp):
        return {}
    runs = sorted(os.listdir(preview_temp),
                  key=lambda d: os.path.getmtime(os.path.join(preview_temp, d)))
    if not runs:
        return {}
    run_dir = os.path.join(preview_temp, runs[-1])
    stl_map = {}
    for f in os.listdir(run_dir):
        if f.endswith(".stl"):
            src = os.path.join(run_dir, f)
            dst = os.path.join(stl_dir, f)
            shutil.copy2(src, dst)
            stl_map[f.replace(".stl", "")] = "stls/" + f
    return stl_map


def _load_inspection_data():
    """Load trimesh inspection data if available."""
    path = os.path.join("output", "stl-inspection.json")
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        return {p["part"]: p for p in data.get("parts", []) if "part" in p}
    return {}


_THREEJS_VIEWER = """
<script type="importmap">
{ "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.164.1/examples/jsm/"
} }
</script>
<script type="module">
import * as THREE from 'three';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
window._initViewer = function(canvasId, stlUrl, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const w = canvas.clientWidth || 400, h = canvas.clientHeight || 300;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x16213e);
    const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 2000);
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(window.devicePixelRatio);
    const controls = new OrbitControls(camera, canvas);
    controls.enableDamping = true;
    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const dLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dLight.position.set(50, 80, 60);
    scene.add(dLight);
    scene.add(new THREE.DirectionalLight(0xffffff, 0.3).position.set(-30, -20, -40));
    const loader = new STLLoader();
    loader.load(stlUrl, function(geometry) {
        geometry.computeVertexNormals();
        const mat = new THREE.MeshPhongMaterial({
            color: new THREE.Color(color || '#8fb5c4'),
            specular: 0x222222, shininess: 40
        });
        const mesh = new THREE.Mesh(geometry, mat);
        scene.add(mesh);
        geometry.computeBoundingBox();
        const bb = geometry.boundingBox;
        const center = new THREE.Vector3();
        bb.getCenter(center);
        const size = new THREE.Vector3();
        bb.getSize(size);
        const maxDim = Math.max(size.x, size.y, size.z);
        camera.position.set(center.x + maxDim, center.y + maxDim * 0.6, center.z + maxDim);
        controls.target.copy(center);
        controls.update();
    });
    function animate() { requestAnimationFrame(animate); controls.update(); renderer.render(scene, camera); }
    animate();
};
</script>
"""


def generate_html_report(assembled, exploded, parts, out_dir):
    """Generate an HTML gallery with screenshots and interactive 3D STL viewers."""
    stl_map = _copy_stls_to_report(out_dir)
    inspection = _load_inspection_data()

    # Part colors from the default previewConfig
    part_colors = {
        "tip": "#c7b7a2", "base": "#b9a994", "middle": "#c7b7a2",
        "linkage": "#b9a994", "tipcover": "#2e8e9b", "socket": "#387f8e",
        "plug": "#4296a4", "bumper": "#2e8e9b", "stand": "#9ea2a3",
    }

    html = [
        "<!DOCTYPE html><html><head>",
        "<meta charset='utf-8'>",
        "<title>Visual Review — DangerFinger</title>",
        "<style>",
        "body { font-family: system-ui, sans-serif; margin: 20px; background: #1a1a2e; color: #eee; }",
        "h1, h2, h3 { color: #e94560; }",
        ".gallery { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 24px; }",
        ".gallery figure { margin: 0; background: #16213e; border-radius: 8px; overflow: hidden; }",
        ".gallery img { width: 320px; height: auto; display: block; cursor: pointer; }",
        ".gallery img:hover { opacity: 0.85; }",
        ".gallery figcaption { padding: 6px 10px; font-size: 13px; color: #a0a0c0; }",
        ".part-section { border-left: 3px solid #e94560; padding-left: 16px; margin-bottom: 32px; }",
        ".part-row { display: flex; gap: 20px; align-items: flex-start; flex-wrap: wrap; }",
        ".viewer-wrap { flex: 0 0 400px; }",
        ".viewer-canvas { width: 400px; height: 300px; border-radius: 8px; display: block; }",
        ".viewer-label { font-size: 12px; color: #7a7a9a; margin-top: 4px; }",
        ".metrics { font-family: monospace; font-size: 12px; color: #a0a0c0; margin: 8px 0; }",
        ".metrics td { padding: 2px 10px 2px 0; }",
        ".metrics .warn { color: #fbbf24; }",
        ".bounds { font-family: monospace; font-size: 12px; color: #7a7a9a; }",
        ".pass { color: #4ade80; } .fail { color: #f87171; }",
        "summary { cursor: pointer; font-weight: bold; font-size: 16px; margin: 8px 0; }",
        "</style>",
        _THREEJS_VIEWER,
        "</head><body>",
        "<h1>DangerFinger Visual Review</h1>",
    ]

    def img_tag(path, caption):
        rel = os.path.basename(path)
        return (
            "<figure><img src='%s' alt='%s' loading='lazy'>"
            "<figcaption>%s</figcaption></figure>" % (rel, caption, caption)
        )

    html.append("<h2>Assembled Views</h2><div class='gallery'>")
    for name, path in assembled.items():
        html.append(img_tag(path, name))
    html.append("</div>")

    html.append("<h2>Exploded Views</h2><div class='gallery'>")
    for name, path in exploded.items():
        html.append(img_tag(path, "exploded " + name))
    html.append("</div>")

    html.append("<h2>Individual Parts</h2>")
    viewer_inits = []
    for part_name, data in sorted(parts.items()):
        html.append("<details open class='part-section'><summary>%s</summary>" % part_name)
        if "error" in data:
            html.append("<p class='fail'>Error: %s</p>" % data["error"])
        else:
            html.append("<div class='part-row'>")

            # Interactive 3D viewer
            stl_rel = stl_map.get(part_name)
            if stl_rel:
                canvas_id = "viewer_%s" % part_name
                color = part_colors.get(part_name, "#8fb5c4")
                html.append("<div class='viewer-wrap'>")
                html.append("<canvas id='%s' class='viewer-canvas'></canvas>" % canvas_id)
                html.append("<p class='viewer-label'>drag to rotate &middot; scroll to zoom</p>")
                html.append("</div>")
                viewer_inits.append((canvas_id, stl_rel, color))

            # Metrics from trimesh inspection
            insp = inspection.get(part_name)
            if insp and not insp.get("error"):
                wt_class = "" if insp.get("is_watertight") else " class='warn'"
                wt_text = "yes" if insp.get("is_watertight") else "no"
                ext = insp.get("extents_mm", [0, 0, 0])
                html.append("<table class='metrics'>")
                html.append("<tr><td>Vertices</td><td>%d</td></tr>" % insp.get("vertices", 0))
                html.append("<tr><td>Faces</td><td>%d</td></tr>" % insp.get("faces", 0))
                html.append("<tr><td>Watertight</td><td%s>%s</td></tr>" % (wt_class, wt_text))
                html.append("<tr><td>Volume</td><td>%.1f mm³</td></tr>" % insp.get("volume_mm3", 0))
                html.append("<tr><td>Surface</td><td>%.1f mm²</td></tr>" % insp.get("surface_area_mm2", 0))
                html.append("<tr><td>Extents</td><td>%.1f × %.1f × %.1f mm</td></tr>" % tuple(ext))
                html.append("</table>")
            elif "bounds" in data:
                b = data["bounds"]
                html.append(
                    "<p class='bounds'>size: %.1f × %.1f × %.1f mm | "
                    "center: (%.1f, %.1f, %.1f)</p>"
                    % (*b["size"], *b["center"])
                )

            html.append("</div>")  # .part-row

            # Screenshot gallery
            html.append("<div class='gallery'>")
            for view_name in PART_VIEWS:
                if view_name in data:
                    html.append(img_tag(data[view_name], "%s — %s" % (part_name, view_name)))
            html.append("</div>")
        html.append("</details>")

    # Init all viewers after page loads
    if viewer_inits:
        html.append("<script type='module'>")
        html.append("window.addEventListener('load', () => {")
        for canvas_id, stl_rel, color in viewer_inits:
            html.append("  window._initViewer('%s', '%s', '%s');" % (canvas_id, stl_rel, color))
        html.append("});")
        html.append("</script>")

    html.append("</body></html>")

    report_path = os.path.join(out_dir, "report.html")
    with open(report_path, "w") as f:
        f.write("\n".join(html))
    return report_path


def main():
    out_dir = OUTPUT_DIR
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    console_errors = []

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from pw_connect import get_browser

    with sync_playwright() as p:
        browser, is_remote = get_browser(p)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.on("console", lambda msg: (
            console_errors.append(msg.text) if msg.type == "error" else None
        ))

        print("Navigating to %s ..." % BASE_URL, flush=True)
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)

        print("Waiting for preview ...", flush=True)
        wait_for_preview(page)
        inject_helpers(page)

        status = page.locator("#preview_status").first.text_content() or ""
        if "error" in status.lower():
            print("FAIL: preview_status = %s" % status.strip(), flush=True)
            browser.close()
            sys.exit(1)

        # Wait for STL models to finish loading (async after preview completes)
        print("Waiting for models to load ...", flush=True)
        for _wi in range(30):
            mc = page.evaluate(
                "Object.keys(Viewer.getStlViewer()._models).length"
            )
            if mc >= 7:
                print("  %d models loaded" % mc, flush=True)
                break
            time.sleep(1)
        else:
            mc = page.evaluate(
                "Object.keys(Viewer.getStlViewer()._models).length"
            )
            print("  Warning: only %d models loaded after 30s" % mc, flush=True)

        print("Capturing assembled views ...", flush=True)
        assembled = capture_assembled(page, out_dir)

        print("Capturing exploded views ...", flush=True)
        exploded = capture_exploded(page, out_dir)

        print("Capturing individual parts ...", flush=True)
        parts = capture_individual_parts(page, out_dir)

        browser.close()

    print("Generating HTML report ...", flush=True)
    report_path = generate_html_report(assembled, exploded, parts, out_dir)

    # Summary
    total_images = len(assembled) + len(exploded)
    for d in parts.values():
        total_images += sum(1 for k in PART_VIEWS if k in d)

    print("", flush=True)
    print("Visual review complete:", flush=True)
    print("  Images: %d" % total_images, flush=True)
    print("  Parts:  %d" % len(parts), flush=True)
    print("  Report: %s" % report_path, flush=True)
    if console_errors:
        print("  Console errors: %d" % len(console_errors), flush=True)
    print("", flush=True)

    # Write summary JSON
    summary = {
        "total_images": total_images,
        "parts": list(parts.keys()),
        "assembled_views": list(assembled.keys()),
        "exploded_views": list(exploded.keys()),
        "console_errors": console_errors[:20],
        "report": report_path,
    }
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    sys.exit(0)


if __name__ == "__main__":
    main()
