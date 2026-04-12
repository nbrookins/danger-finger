"""Playwright browser connection + dev-server discovery helper.

Connects to pre-launched Chromium via CDP if dev-server is running,
otherwise falls back to launching a local browser.
"""

import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(REPO_ROOT, ".dev-server.json")


def _read_dev_server_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def get_web_base_url():
    """Get the dev-server's web app URL, or None if not running."""
    state = _read_dev_server_state()
    if state and state.get("web_port"):
        return "http://127.0.0.1:%d" % state["web_port"]
    return None


def get_browser(playwright, headless=True):
    """Get a browser, preferring the dev-server's Chromium via CDP.

    Returns (browser, is_remote) — caller should only close if not remote.
    """
    cdp_url = os.environ.get("CDP_URL")
    if not cdp_url:
        state = _read_dev_server_state()
        if state:
            cdp_url = state.get("cdp_url")

    if cdp_url:
        try:
            browser = playwright.chromium.connect_over_cdp(cdp_url)
            return browser, True
        except Exception as e:
            print("pw_connect: dev-server Chromium unavailable (%s), launching local" % e, flush=True)

    browser = playwright.chromium.launch(headless=headless)
    return browser, False
