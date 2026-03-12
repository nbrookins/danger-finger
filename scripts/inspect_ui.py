#!/usr/bin/env python3
"""
Playwright-based UI inspection for danger-finger web app.
Captures #preview_status, #viewer_error, #loader, /api/parts, stl_viewer positions, console.
Also checks: title/h1 encoding, part toggle count vs API, plugInstances in previewConfig,
advanced-section collapse, and explode slider state.
Writes output to UI_INSPECT_OUTPUT and screenshot to SCREENSHOT_OUTPUT.
Exit 0 if preview_status does not contain "error", else 1.
"""
import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    base_url = os.environ.get("BASE_URL", "http://127.0.0.1:8081")
    ui_output = os.environ.get("UI_INSPECT_OUTPUT", "output/ui-inspect.txt")
    screenshot_output = os.environ.get("SCREENSHOT_OUTPUT", "output/viewer-screenshot.png")

    Path(screenshot_output).parent.mkdir(parents=True, exist_ok=True)

    console_logs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        def on_console(msg):
            console_logs.append(f"[{msg.type}] {msg.text}")

        page = context.new_page()
        page.on("console", on_console)

        try:
            page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            _write_output(ui_output, base_url, error=f"Navigation failed: {e}")
            browser.close()
            sys.exit(1)

        try:
            page.wait_for_function(
                """() => {
                    const el = document.getElementById('preview_status');
                    if (!el || !el.textContent) return false;
                    const t = el.textContent.toLowerCase();
                    return t.includes('ready') || t.includes('error');
                }""",
                timeout=90000,
            )
        except Exception:
            pass

        import time as _time
        _time.sleep(3)

        preview_status_text = (page.locator("#preview_status").first.text_content() or "")

        viewer_error_el = page.locator("#viewer_error").first
        viewer_error_text = "(none)"
        if viewer_error_el.count() > 0:
            t = viewer_error_el.text_content()
            viewer_error_text = (t or "").strip() or "(empty)"

        loader_el = page.locator("#loader").first
        loader_visible = "visible" if loader_el.is_visible() else "hidden"

        title_checks = _check_title_encoding(page)
        parts_checks = _check_parts_and_toggles(page, base_url)
        preview_config_checks = _check_preview_config(page, base_url)
        advanced_checks = _check_advanced_collapse(page)
        explode_checks = _check_explode_slider(page)

        viewer_positions = page.evaluate("""
            () => {
                const out = {};
                if (typeof stl_viewer === 'undefined') return out;
                for (let id = 0; id <= 15; id++) {
                    try {
                        const info = stl_viewer.get_model_info(id);
                        if (info) {
                            const pos = info.pos || info.position ||
                                (info.matrix && info.matrix.elements
                                    ? [info.matrix.elements[12], info.matrix.elements[13], info.matrix.elements[14]]
                                    : null);
                            out[String(id)] = (pos && Array.isArray(pos))
                                ? [pos[0], pos[1], pos[2]] : info;
                        }
                    } catch (e) {}
                }
                return out;
            }
        """)

        page.screenshot(path=screenshot_output)
        browser.close()

    report = _build_report(
        base_url=base_url,
        preview_status=preview_status_text,
        viewer_error=viewer_error_text,
        loader_status=loader_visible,
        title_checks=title_checks,
        parts_checks=parts_checks,
        preview_config_checks=preview_config_checks,
        advanced_checks=advanced_checks,
        explode_checks=explode_checks,
        viewer_positions=viewer_positions,
        console_logs=console_logs[-50:],
    )

    with open(ui_output, "w", encoding="utf-8") as f:
        f.write(report)

    if "error" in preview_status_text.lower():
        sys.exit(1)
    sys.exit(0)


def _check_title_encoding(page):
    checks = {}
    try:
        title_text = page.title()
        checks["title_text"] = title_text
        checks["title_has_mojibake"] = any(c in title_text for c in ["\u00e2\u20ac", "\u00c3", "\ufffd"])
        checks["title_ok"] = ("Danger" in title_text or "DangerFinger" in title_text) and not checks["title_has_mojibake"]
    except Exception as e:
        checks["title_error"] = str(e)
    try:
        h1_text = (page.locator("h1").first.text_content() or "")
        checks["h1_text"] = h1_text
        checks["h1_has_mojibake"] = any(c in h1_text for c in ["\u00e2\u20ac", "\u00c3", "\ufffd"])
        checks["h1_ok"] = ("Danger" in h1_text or "DangerFinger" in h1_text) and not checks["h1_has_mojibake"]
    except Exception as e:
        checks["h1_error"] = str(e)
    return checks


def _check_parts_and_toggles(page, base_url):
    try:
        resp = page.request.get(f"{base_url.rstrip('/')}/api/parts")
        if resp.status != 200:
            return {"error": f"HTTP {resp.status}"}
        data = resp.json()
        parts = data.get("parts", [])
        api_part_ids = [p.get("id") for p in parts]

        toggle_results = {}
        for part_id in api_part_ids:
            # New: checkbox with id="toggle_{part_id}"; Old: button with id="b_{part_id}"
            cb_el = page.locator(f"#toggle_{part_id}").first
            btn_el = page.locator(f"#b_{part_id}").first
            toggle_results[part_id] = "present" if (cb_el.count() > 0 or btn_el.count() > 0) else "MISSING"

        cfg = data.get("previewConfig", {})
        pos_offsets = cfg.get("positionOffsets", {})
        sample_name = api_part_ids[0] if api_part_ids else None

        return {
            "api_part_count": len(parts),
            "api_part_ids": api_part_ids,
            "toggle_buttons": toggle_results,
            "missing_toggles": [k for k, v in toggle_results.items() if v == "MISSING"],
            "sample": {"name": sample_name, "pos": pos_offsets.get(sample_name)},
        }
    except Exception as e:
        return {"error": str(e)}


def _check_preview_config(page, base_url):
    try:
        resp = page.request.get(f"{base_url.rstrip('/')}/api/parts")
        if resp.status != 200:
            return {"error": f"HTTP {resp.status}"}
        cfg = resp.json().get("previewConfig", {})
        plug_instances = cfg.get("plugInstances", [])
        return {
            "previewConfig_keys": list(cfg.keys()),
            "plugInstances_count": len(plug_instances),
            "plugInstances_ok": len(plug_instances) == 4,
            "has_rotateOffsets": "rotateOffsets" in cfg,
            "has_positionOffsets": "positionOffsets" in cfg,
            "has_partColors": "partColors" in cfg,
            "middle_rotate": cfg.get("rotateOffsets", {}).get("middle"),
        }
    except Exception as e:
        return {"error": str(e)}


def _check_advanced_collapse(page):
    checks = {}
    try:
        # New layout: Bootstrap collapse link href="#advancedParams"
        adv_link = page.locator("[href='#advancedParams'], [data-toggle='collapse']").first
        # Old layout: button #b_pa
        adv_btn_old = page.locator("#b_pa").first
        adv_present = adv_link.count() > 0 or adv_btn_old.count() > 0
        checks["adv_btn_present"] = adv_present
        if not adv_present:
            return checks

        adv_data = page.locator("#advancedParams, #advData").first
        std_data = page.locator("#showData").first
        checks["advData_present"] = adv_data.count() > 0
        checks["showData_present"] = std_data.count() > 0

        # Click the collapse toggle
        toggle = adv_link if adv_link.count() > 0 else adv_btn_old
        toggle.click()
        page.wait_for_timeout(500)
        checks["after_adv_click_advData_visible"] = adv_data.is_visible()
        checks["adv_toggle_ok"] = bool(checks.get("after_adv_click_advData_visible"))
    except Exception as e:
        checks["error"] = str(e)
    return checks


def _check_explode_slider(page):
    checks = {}
    try:
        slider = page.locator("#explode").first
        checks["slider_present"] = slider.count() > 0
        if slider.count() > 0:
            val = slider.input_value()
            checks["slider_value"] = val
            checks["slider_at_zero"] = val == "0"
    except Exception as e:
        checks["error"] = str(e)
    return checks


def _build_report(base_url, preview_status, viewer_error, loader_status,
                  title_checks, parts_checks, preview_config_checks,
                  advanced_checks, explode_checks, viewer_positions,
                  console_logs, error=None):
    if error:
        return f"=== UI inspect: {base_url} ===\n\nError: {error}\n"

    def js(obj):
        return json.dumps(obj, indent=2) if isinstance(obj, (dict, list)) else str(obj)

    return f"""=== UI inspect: {base_url} ===

#preview_status:
{preview_status.strip() or '(empty)'}

#viewer_error:
{viewer_error}

#loader (Loading...):
{loader_status}

#title_encoding:
{js(title_checks)}

#parts_and_toggles:
{js(parts_checks)}

#preview_config:
{js(preview_config_checks)}

#advanced_collapse:
{js(advanced_checks)}

#explode_slider:
{js(explode_checks)}

#viewer_positions (mesh positions from stl_viewer.get_model_info):
{js(viewer_positions)}

--- console (last 50) ---
{chr(10).join(console_logs) if console_logs else '(none)'}
"""


def _write_output(path, base_url, error):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(_build_report(base_url, "", "(none)", "unknown",
                              {}, {}, {}, {}, {}, {}, [], error=error))


if __name__ == "__main__":
    main()
