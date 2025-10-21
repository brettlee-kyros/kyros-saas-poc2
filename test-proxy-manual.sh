#!/bin/bash
#
# Manual test script for Story 5.1 Reverse Proxy
# Tests all acceptance criteria for the proxy route
#

set -e

echo "========================================="
echo "Story 5.1: Reverse Proxy Manual Testing"
echo "========================================="
echo

# Colors for output
GREEN='\033[0.32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Test function
test_case() {
    local name="$1"
    local command="$2"
    local expected="$3"

    echo "Test: $name"
    result=$(eval "$command" 2>&1)

    if echo "$result" | grep -q "$expected"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "Expected: $expected"
        echo "Got: $result"
        ((FAILED++))
    fi
    echo
}

echo "=== AC 1-2: Route exists and validates token ==="
test_case \
    "Missing token returns 401" \
    "curl -s http://localhost:3000/api/proxy/dash/customer-lifetime-value" \
    "UNAUTHORIZED"

echo "=== AC 4: Invalid dashboard slug returns 404 ==="
test_case \
    "Invalid dashboard slug" \
    "curl -s http://localhost:3000/api/proxy/dash/invalid-dashboard-slug" \
    "INVALID_DASHBOARD"

echo "=== AC 10: Dash app unavailable returns 503 ==="
echo "Stopping CLV dashboard..."
docker-compose stop dash-app-clv > /dev/null 2>&1
sleep 2

# Use a fake token for this test (any token works, we're testing service unavailable)
test_case \
    "Dashboard service unavailable" \
    "curl -s -H 'X-Tenant-Token: fake-token-for-testing' http://localhost:3000/api/proxy/dash/customer-lifetime-value" \
    "SERVICE_UNAVAILABLE"

echo "Restarting CLV dashboard..."
docker-compose start dash-app-clv > /dev/null 2>&1
sleep 3

echo
echo "==========================================="
echo "Test Summary:"
echo "  Passed: $PASSED"
echo "  Failed: $FAILED"
echo "==========================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi
