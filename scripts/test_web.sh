#!/usr/bin/env bash
# Run the web server, hit key endpoints, print responses. Kills server on exit.
# Usage: from repo root, ./scripts/test_web.sh
# Env: USE_EXISTING_SERVER=1  — skip starting a server (use existing, e.g. Docker on kbr-test)
#      TEST_PORT               — port to hit (default 8091 for fresh server, 8081 for kbr-test)
# Needs: OpenSCAD on PATH (or OPENSCAD_EXEC) for POST /api/preview to return 200.
set -e
cd "$(dirname "$0")/.."
PORT=${TEST_PORT:-8091}
BASE="http://127.0.0.1:$PORT"
PYTHON=${PYTHON:-python3}

if [ -z "$USE_EXISTING_SERVER" ]; then
  # Start a fresh server on the designated port; killed on exit.
  http_port=$PORT $PYTHON web/server.py &
  PID=$!
  trap "kill $PID 2>/dev/null || true" EXIT
fi

echo "Waiting for server on $BASE ..."
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -s -o /dev/null -w "%{http_code}" "$BASE/" 2>/dev/null | grep -q 200; then
    break
  fi
  sleep 1
done

echo "--- GET / (index) ---"
curl -s -o /dev/null -w "HTTP %{http_code}, size %{size_download}\n" "$BASE/"

echo "--- GET /api/parts ---"
curl -s "$BASE/api/parts" | head -c 500
echo ""

echo "--- POST /api/preview (minimal config) ---"
RES=$(curl -s -w "\n%{http_code}" -X POST "$BASE/api/preview" \
  -H "Content-Type: application/json" \
  -d '{"intermediate_length":24,"distal_length":24}')
CODE=$(echo "$RES" | tail -n1)
BODY=$(echo "$RES" | sed '$d')
echo "HTTP $CODE"
echo "$BODY" | head -c 600
echo ""

echo "--- Done ---"
