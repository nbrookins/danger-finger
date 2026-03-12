#!/bin/bash
# Post-deployment smoke tests for AWS environment.
# Usage: ./scripts/verify_aws_deploy.sh [ec2_url] [api_gw_url]
set -euo pipefail

EC2_URL="${1:-$(cd infra && terraform output -raw app_url 2>/dev/null || echo "")}"
API_GW_URL="${2:-$(cd infra && terraform output -raw api_gateway_url 2>/dev/null || echo "")}"

if [ -z "$EC2_URL" ]; then
    echo "ERROR: No EC2 URL provided and terraform output unavailable"
    exit 1
fi

PASS=0
FAIL=0

check() {
    local desc="$1" url="$2" expect="$3"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "$expect" ]; then
        echo "  PASS: $desc (HTTP $HTTP_CODE)"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $desc (expected $expect, got $HTTP_CODE)"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== AWS Deployment Verification ==="
echo ""

echo "EC2 Server: $EC2_URL"
check "Homepage loads" "$EC2_URL/" "200"
check "Parts API" "$EC2_URL/api/parts" "200"
check "Preview endpoint" "$EC2_URL/api/preview" "200"

echo ""
echo "API Gateway (Lambda): $API_GW_URL"
if [ -n "$API_GW_URL" ]; then
    check "Configs 404 (nonexistent)" "${API_GW_URL}configs/deadbeef" "404"
    check "Profiles 404 (nonexistent)" "${API_GW_URL}profiles/nobody" "404"
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && echo "ALL CHECKS PASSED" || { echo "SOME CHECKS FAILED"; exit 1; }
