#!/usr/bin/env bash
# Verify web UI: start server, run Playwright inspection + visual review, stop server.
# Default: local Python server. Set USE_DOCKER=1 + DOCKER_TAG for Docker mode.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON="${PYTHON:-.venv/bin/python3}"
VERIFY_PORT="${VERIFY_PORT:-8092}"
USE_DOCKER="${USE_DOCKER:-}"
SERVER_PID=""
CONTAINER_ID=""
USING_DEV_SERVER=""

cleanup() {
    if [[ -n "$SERVER_PID" ]]; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
    if [[ -n "$CONTAINER_ID" ]]; then
        docker stop "$CONTAINER_ID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# --- Check if dev-server's web server is already running ---
if [[ -f "$REPO_ROOT/.dev-server.json" ]]; then
    DEV_WEB_PORT=$("$PYTHON" -c "import json; d=json.load(open('$REPO_ROOT/.dev-server.json')); print(d.get('web_port',''))" 2>/dev/null)
    if [[ -n "$DEV_WEB_PORT" ]] && curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${DEV_WEB_PORT}/" 2>/dev/null | grep -q 200; then
        echo "Using dev-server's web app on port $DEV_WEB_PORT"
        VERIFY_PORT="$DEV_WEB_PORT"
        USING_DEV_SERVER=1
    fi
fi

# --- Start server if not using dev-server ---
if [[ -z "$USING_DEV_SERVER" ]]; then
    if [[ -n "$USE_DOCKER" ]]; then
        DOCKER_TAG="${DOCKER_TAG:?DOCKER_TAG required in Docker mode}"
        echo "Starting Docker container (tag=$DOCKER_TAG, port=$VERIFY_PORT)..."
        CONTAINER_ID=$(docker run -d --rm -p "${VERIFY_PORT}:8081" -e http_port=8081 "$DOCKER_TAG")
        echo "Container: $CONTAINER_ID"
    else
        echo "Starting local server (port=$VERIFY_PORT)..."
        "$PYTHON" web/server.py --http_port="$VERIFY_PORT" &
        SERVER_PID=$!
        echo "Server PID: $SERVER_PID"
    fi

    # --- Wait for healthy ---
    echo "Waiting for http://127.0.0.1:${VERIFY_PORT} (up to 120s)..."
    for i in $(seq 1 120); do
        if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${VERIFY_PORT}/" 2>/dev/null | grep -q 200; then
            echo "Server is up."
            break
        fi
        if [[ $i -eq 120 ]]; then
            echo "ERROR: Server did not become healthy within 120 seconds"
            exit 1
        fi
        sleep 1
    done
fi

# --- Run inspection ---
echo "Running UI inspection..."
set +e
BASE_URL="http://127.0.0.1:${VERIFY_PORT}" \
    SCREENSHOT_OUTPUT="output/viewer-screenshot.png" \
    UI_INSPECT_OUTPUT="output/ui-inspect.txt" \
    "$PYTHON" scripts/inspect_ui.py
INSPECT_CODE=$?
set -e

if [[ $INSPECT_CODE -ne 0 ]]; then
    echo "verify-web-ui: FAIL (inspection failed)"
    exit "$INSPECT_CODE"
fi

# --- Run visual review ---
echo "Running visual review (multi-angle)..."
set +e
BASE_URL="http://127.0.0.1:${VERIFY_PORT}" \
    VISUAL_REVIEW_DIR="output/visual-review" \
    "$PYTHON" scripts/visual_review.py
REVIEW_CODE=$?
set -e

if [[ $REVIEW_CODE -eq 0 ]]; then
    echo "verify-web-ui: OK"
else
    echo "verify-web-ui: PARTIAL (inspection OK, visual review code=$REVIEW_CODE)"
fi
echo "Artifacts: output/ui-inspect.txt, output/viewer-screenshot.png, output/visual-review/"

exit "$REVIEW_CODE"
