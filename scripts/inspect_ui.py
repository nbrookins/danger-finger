#!/usr/bin/env python3
"""
Playwright-based UI inspection for danger-finger web app.
Captures #preview_status, #viewer_error, #loader, /api/parts, stl_viewer positions, console.
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
            kind = msg.type
            text = msg.text
            console_logs.append(f"[{kind}] {text}")

        page = context.new_page()
        page.on("console", on_console)

        try:
            page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            _write_output(ui_output, base_url, error=f"Navigation failed: {e}")
            browser.close()
            sys.exit(1)

        # Wait up to 30 seconds for #preview_status to contain text
        try:
            page.wait_for_function(
                """() => {
                    const el = document.getElementById('preview_status');
                    return el && el.textContent && el.textContent.trim().length > 0;
                }""",
                timeout=30000,
            )
        except Exception:
            pass  # Proceed even if timeout; we'll capture current state

        # Capture DOM elements
        preview_status = page.locator("#preview_status").first
        preview_status_text = preview_status.text_content() or ""

        viewer_error_el = page.locator("#viewer_error").first
        viewer_error_text = "(none)"
        if viewer_error_el.count() > 0:
            t = viewer_error_el.text_content()
            viewer_error_text = (t or "").strip() or "(empty)"

        loader_el = page.locator("#loader").first
        loader_visible = "visible" if loader_el.is_visible() else "hidden"

        # Fetch /api/parts and summarize
        parts_summary = _fetch_parts_summary(page, base_url)

        # Get viewer positions from stl_viewer.get_model_info()
        viewer_positions = page.evaluate("""
            () => {
                const out = {};
                if (typeof stl_viewer === 'undefined') return out;
                for (let id = 0; id <= 15; id++) {
                    try {
                        const info = stl_viewer.get_model_info(id);
                        if (info) {
                            const pos = info.pos || info.position || (info.matrix && info.matrix.elements ? [info.matrix.elements[12], info.matrix.elements[13], info.matrix.elements[14]] : null);
                            if (pos && Array.isArray(pos)) {
                                out[String(id)] = [pos[0], pos[1], pos[2]];
                            } else {
                                out[String(id)] = info;
                            }
                        }
                    } catch (e) {}
                }
                return out;
            }
        """)

        # Take screenshot
        page.screenshot(path=screenshot_output)

        browser.close()

    # Build output
    report = _build_report(
        base_url=base_url,
        preview_status=preview_status_text,
        viewer_error=viewer_error_text,
        loader_status=loader_visible,
        parts_summary=parts_summary,
        viewer_positions=viewer_positions,
        console_logs=console_logs[-50:],
    )

    with open(ui_output, "w", encoding="utf-8") as f:
        f.write(report)

    # Exit 1 if preview_status contains "error" (case-insensitive)
    if "error" in preview_status_text.lower():
        sys.exit(1)
    sys.exit(0)


def _fetch_parts_summary(page, base_url):
    """Fetch /api/parts and return count, sample part, tip position."""
    try:
        resp = page.request.get(f"{base_url.rstrip('/')}/api/parts")
        if resp.status != 200:
            return {"error": f"HTTP {resp.status}"}
        data = resp.json()
        parts = data.get("parts", [])
        cfg = data.get("previewConfig", {})
        pos_offsets = cfg.get("positionOffsets", {})

        sample = None
        if parts:
            first = parts[0]
            name = first.get("id") or first.get("label", "").lower()
            pos = pos_offsets.get(name) if name else None
            sample = {"name": name, "pos": pos}

        tip_pos = pos_offsets.get("tip")
        return {
            "count": len(parts),
            "sample": sample,
            "tipPos": {"pos": tip_pos} if tip_pos is not None else None,
        }
    except Exception as e:
        return {"error": str(e)}


def _build_report(
    base_url,
    preview_status,
    viewer_error,
    loader_status,
    parts_summary,
    viewer_positions,
    console_logs,
    error=None,
):
    if error:
        return f"=== UI inspect: {base_url} ===\n\nError: {error}\n"

    parts_str = json.dumps(parts_summary, indent=2) if isinstance(parts_summary, dict) else str(parts_summary)
    positions_str = json.dumps(viewer_positions, indent=2) if isinstance(viewer_positions, dict) else str(viewer_positions)
    console_str = "\n".join(console_logs) if console_logs else "(none)"

    return f"""=== UI inspect: {base_url} ===

#preview_status:
{preview_status.strip() or '(empty)'}

#viewer_error:
{viewer_error}

#loader (Loading...):
{loader_status}

#parts_debug (frontend parts from /api/parts):
{parts_str}

#viewer_positions (mesh positions from stl_viewer.get_model_info):
{positions_str}

--- console (last 50) ---
{console_str}
"""


def _write_output(path, base_url, error):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(_build_report(base_url, "", "(none)", "unknown", {}, {}, [], error=error))


if __name__ == "__main__":
    main()
