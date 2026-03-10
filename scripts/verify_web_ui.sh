#!/usr/bin/env bash
# Verify web UI by starting Docker container, running Playwright inspect, then stopping.
# Requires: DOCKER_TAG (env), make build, pip install playwright, playwright install chromium

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DOCKER_TAG="${DOCKER_TAG:?DOCKER_TAG is required (e.g. from make: \$(DOCKER_TAG))}"
PYTHON="${PYTHON:-python3}"
VERIFY_PORT="${VERIFY_PORT:-8092}"

CONTAINER_ID=""

cleanup() {
    if [[ -n "$CONTAINER_ID" ]]; then
        echo "Stopping container $CONTAINER_ID..."
        docker stop "$CONTAINER_ID" 2>/dev/null || true
        CONTAINER_ID=""
    fi
}

trap cleanup EXIT

echo "Starting container (DOCKER_TAG=$DOCKER_TAG, port $VERIFY_PORT)..."
CONTAINER_ID=$(docker run -d --rm -p "${VERIFY_PORT}:8081" -e http_port=8081 "$DOCKER_TAG") || {
    echo "ERROR: Failed to start container"
    exit 1
}

echo "Container ID: $CONTAINER_ID"
echo "Waiting for server on http://127.0.0.1:${VERIFY_PORT} (up to 60s)..."

for i in $(seq 1 60); do
    if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${VERIFY_PORT}/" 2>/dev/null | grep -q 200; then
        echo "Server is up."
        break
    fi
    if [[ $i -eq 60 ]]; then
        echo "ERROR: Server did not become healthy within 60 seconds"
        exit 1
    fi
    sleep 1
done

echo "Running UI inspection..."
set +e
BASE_URL="http://127.0.0.1:${VERIFY_PORT}" \
    SCREENSHOT_OUTPUT="output/viewer-screenshot.png" \
    UI_INSPECT_OUTPUT="output/ui-inspect.txt" \
    "$PYTHON" scripts/inspect_ui.py
EXIT_CODE=$?
set -e

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "verify-web-ui: OK (preview_status has no error)"
else
    echo "verify-web-ui: FAIL (preview_status contains error, or inspect failed)"
fi
echo "Output: output/ui-inspect.txt, output/viewer-screenshot.png"

exit "$EXIT_CODE"
