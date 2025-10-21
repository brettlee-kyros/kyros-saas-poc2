#!/bin/bash
# Manual test script for reverse proxy API route

echo "=== Reverse Proxy Manual Testing ==="
echo

# Test tenant token (generated from Epic 3)
# This is a sample token for Acme Corporation tenant
TENANT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmOGQxZTJjMy00YjVhLTY3ODktYWJjZC1lZjEyMzQ1Njc4OTAiLCJlbWFpbCI6ImFuYWx5c3RAYWNtZS5jb20iLCJ0ZW5hbnRfaWRzIjpbIjhlMWIzZDViLTdjOWEtNGUyZi1iMWQzLWE1YzdlOWYxMjM0NSJdLCJpYXQiOjE3NjAyMzc4NzgsImV4cCI6MTc2MDI0MTQ3OCwiaXNzIjoia3lyb3MtcG9jIn0.HSUI8pR7Rz8HjcVtsRMry9enSUWKHtxl38Lp6LNIl5o"

echo "Test 1: Missing token (should return 401)"
curl -s http://localhost:3000/api/proxy/dash/customer-lifetime-value/ | python3 -m json.tool
echo

echo "Test 2: Invalid dashboard slug (should return 404)"
curl -s -H "X-Tenant-Token: $TENANT_TOKEN" \
  http://localhost:3000/api/proxy/dash/invalid-dashboard/ | python3 -m json.tool
echo

echo "Test 3: Valid request to CLV dashboard (should proxy successfully)"
curl -s -H "X-Tenant-Token: $TENANT_TOKEN" \
  -H "Accept: text/html" \
  http://localhost:3000/api/proxy/dash/customer-lifetime-value/ | head -20
echo

echo "Test 4: Valid request to Risk dashboard (should proxy successfully)"
curl -s -H "X-Tenant-Token: $TENANT_TOKEN" \
  -H "Accept: text/html" \
  http://localhost:3000/api/proxy/dash/risk-analysis/ | head -20
echo

echo "=== Testing Complete ==="
