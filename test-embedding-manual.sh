#!/bin/bash
#
# Manual test script for Story 5.2 Dashboard Embedding
# Tests that the embedding page is accessible and properly configured
#

set -e

echo "=========================================="
echo "Story 5.2: Dashboard Embedding Manual Testing"
echo "=========================================="
echo

# Colors for output
GREEN='\033[0;32m'
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
        echo "Got: $(echo "$result" | head -20)"
        ((FAILED++))
    fi
    echo
}

echo "=== AC 1: Dashboard embedding page exists ==="
test_case \
    "Page route exists and serves HTML" \
    "curl -s http://localhost:3000/tenant/acme-corporation/dashboard/customer-lifetime-value | head -50" \
    "<!DOCTYPE html>"

echo "=== AC 3: iframe src points to proxy route ==="
test_case \
    "iframe src uses reverse proxy" \
    "curl -s http://localhost:3000/tenant/acme-corporation/dashboard/customer-lifetime-value" \
    "/api/proxy/dash/"

echo "=== AC 4: iframe has proper styling classes ==="
test_case \
    "iframe has w-full h-full classes" \
    "curl -s http://localhost:3000/tenant/acme-corporation/dashboard/customer-lifetime-value" \
    "w-full h-full"

echo "=== AC 11: iframe has sandbox attribute ==="
test_case \
    "iframe has sandbox security attribute" \
    "curl -s http://localhost:3000/tenant/acme-corporation/dashboard/customer-lifetime-value" \
    "sandbox="

echo "=== Story 5.1 Integration: Proxy accepts token via query param ==="
TENANT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmOGQxZTJjMy00YjVhLTY3ODktYWJjZC1lZjEyMzQ1Njc4OTAiLCJlbWFpbCI6ImFuYWx5c3RAYWNtZS5jb20iLCJ0ZW5hbnRfaWRzIjpbIjhlMWIzZDViLTdjOWEtNGUyZi1iMWQzLWE1YzdlOWYxMjM0NSJdLCJpYXQiOjE3NjAyMzc4NzgsImV4cCI6MTc2MDI0MTQ3OCwiaXNzIjoia3lyb3MtcG9jIn0.HSUI8pR7Rz8HjcVtsRMry9enSUWKHtxl38Lp6LNIl5o"

test_case \
    "Proxy accepts token via query parameter" \
    "curl -s 'http://localhost:3000/api/proxy/dash/customer-lifetime-value/?token=$TENANT_TOKEN' | head -5" \
    "<!DOCTYPE html>"

echo
echo "==========================================="
echo "Test Summary:"
echo "  Passed: $PASSED"
echo "  Failed: $FAILED"
echo "==========================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    echo
    echo "✓ Dashboard embedding page created"
    echo "✓ iframe configured to use reverse proxy"
    echo "✓ iframe has proper styling and security attributes"
    echo "✓ Proxy route updated to accept tokens via query parameter"
    echo
    echo "Manual verification needed:"
    echo "1. Visit http://localhost:3000"
    echo "2. Login (any email/password works with mock auth)"
    echo "3. Select 'Acme Corporation' tenant"
    echo "4. Click 'Open Dashboard' on CLV or Risk dashboard"
    echo "5. Verify dashboard loads in iframe"
    echo "6. Verify header/breadcrumb visible outside iframe"
    echo "7. Verify 'Back to Dashboards' button works"
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi
