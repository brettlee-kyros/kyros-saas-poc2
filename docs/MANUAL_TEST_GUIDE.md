# Kyros Multi-Tenant SaaS PoC - Manual Test Guide

**Version:** 2.0
**Date:** 2025-10-18
**Test Architect:** Quinn
**Last Updated:** 2025-10-18 (Epic 5 Integration)
**Status:** Ready for Execution

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Test Environment Setup](#test-environment-setup)
4. [Test Suite 1: Authentication & Token Exchange](#test-suite-1-authentication--token-exchange)
5. [Test Suite 2: Data API & Tenant Isolation](#test-suite-2-data-api--tenant-isolation)
6. [Test Suite 3: CLV Dashboard Integration](#test-suite-3-clv-dashboard-integration)
7. [Test Suite 4: Risk Dashboard Integration](#test-suite-4-risk-dashboard-integration)
8. [Test Suite 5: Multi-Tenant Data Isolation (CRITICAL)](#test-suite-5-multi-tenant-data-isolation-critical)
9. [Test Suite 6: Error Handling & Security](#test-suite-6-error-handling--security)
10. [Test Suite 7: End-to-End Integration](#test-suite-7-end-to-end-integration)
11. [Test Suite 8: Epic 5 - Reverse Proxy & Dashboard Embedding](#test-suite-8-epic-5---reverse-proxy--dashboard-embedding)
12. [Test Results Template](#test-results-template)
13. [Troubleshooting](#troubleshooting)

---

## Overview

This manual test guide provides comprehensive test procedures for all implemented functionality through **Stories 0.1 - 5.3**, covering:

- **Epic 0**: Project setup and shared configuration
- **Epic 1**: Authentication foundation (mock login, token exchange)
- **Epic 2**: Token exchange mechanism
- **Epic 3**: Shell UI and tenant selection
- **Epic 4**: Dash application integration (CLV and Risk dashboards)
- **Epic 5**: Reverse proxy and dashboard embedding with token expiry handling

### Testing Objectives

1. Verify hard tenant isolation across all services
2. Validate JWT token exchange mechanism
3. Confirm proper authentication and authorization flows
4. Test error handling for all failure scenarios
5. Verify multi-tenant data access patterns
6. Validate cross-dashboard pattern consistency

### Critical Success Criteria

- ✅ No cross-tenant data leakage detected
- ✅ All JWT validation paths working correctly
- ✅ Both dashboards functioning with proper tenant isolation
- ✅ Error handling graceful and user-friendly
- ✅ Concurrent multi-tenant access working correctly

---

## Prerequisites

### Required Tools

```bash
# Check versions
docker --version          # Docker 20.10+
docker-compose --version  # Docker Compose 2.0+
python3 --version        # Python 3.11+
curl --version           # Any recent version
jq --version             # JSON parsing (optional but helpful)
```

### Required Files

Verify these files exist:
```bash
cd /Users/brettlee/docker/kyros-dev/work/kyros-saas-poc

# Core files
ls -la docker-compose.yml
ls -la data/tenant_metadata.db
ls -la scripts/seed-database.py

# Application directories
ls -ld apps/api apps/shell-ui apps/dash-app-clv apps/dash-app-risk
ls -ld packages/shared-config
```

### Test Data Overview

The seeded database contains:

**Tenants:**
- **Acme Corp** (`8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345`)
  - Has access to: CLV Dashboard, Risk Analysis
- **Beta Industries** (`2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4`)
  - Has access to: Risk Analysis only

**Users:**
- `analyst@acme.com` - Acme analyst (access to Acme tenant)
- `admin@acme.com` - Acme admin (access to Acme tenant)
- `viewer@beta.com` - Beta viewer (access to Beta tenant)

---

## Test Environment Setup

### Step 1: Clean Environment

```bash
# Stop any running containers
docker-compose down -v

# Clean up old containers and networks
docker system prune -f

# Remove old database
rm -f data/tenant_metadata.db
```

### Step 2: Initialize Database

```bash
# Run seed script
python3 scripts/seed-database.py

# Expected output:
# ✓ Database seeded successfully!
# Record counts:
#   tenants: 2
#   users: 3
#   user_tenants: 3
#   dashboards: 2
#   tenant_dashboards: 3
```

### Step 3: Build and Start Services

```bash
# Build all containers
docker-compose build

# Start all services
docker-compose up -d

# Wait for services to be ready (30-60 seconds)
sleep 60

# Verify all services are running
docker-compose ps

# Expected output: All services should show "Up" status
# NAME                IMAGE                    STATUS
# kyros-api           kyros-saas-poc-api       Up (healthy)
# kyros-shell-ui      kyros-saas-poc-shell-ui  Up
# kyros-dash-clv      kyros-saas-poc-dash-app-clv  Up
# kyros-dash-risk     kyros-saas-poc-dash-app-risk Up
```

### Step 4: Verify Service Health

```bash
# Check API health
curl -s http://localhost:8000/health | jq

# Expected: {"status": "healthy"}

# Check Shell UI (should return HTML)
curl -s http://localhost:3000 | head -n 5

# Check CLV Dashboard accessibility (should return 401 without token)
curl -s http://localhost:8050 | head -n 5

# Check Risk Dashboard accessibility (should return 401 without token)
curl -s http://localhost:8051 | head -n 5
```

### Step 5: View Service Logs

```bash
# Open separate terminal windows/tabs for each service
docker-compose logs -f api        # Terminal 1
docker-compose logs -f dash-app-clv  # Terminal 2
docker-compose logs -f dash-app-risk # Terminal 3
```

**Keep these logs visible during testing to observe authentication flow.**

---

## Test Suite 1: Authentication & Token Exchange

### Test 1.1: Mock Login - Valid User

**Objective:** Verify mock authentication endpoint returns valid user access token

**Procedure:**
```bash
# Login as Acme analyst
curl -X POST http://localhost:8000/api/auth/mock-login \
  -H "Content-Type: application/json" \
  -d '{"email": "analyst@acme.com"}' \
  | jq

# Save token for later tests
export USER_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/mock-login \
  -H "Content-Type: application/json" \
  -d '{"email": "analyst@acme.com"}' \
  | jq -r '.access_token')

echo "User Token: $USER_TOKEN"
```

**Expected Result:**
```json
{
  "access_token": "<JWT_TOKEN>",
  "token_type": "bearer",
  "user": {
    "id": "<UUID>",
    "email": "analyst@acme.com",
    "tenant_ids": ["8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"]
  }
}
```

**Verification:**
- ✅ Response contains `access_token` field
- ✅ Token is a valid JWT (three parts separated by dots)
- ✅ User email matches request
- ✅ tenant_ids array contains Acme tenant ID

**Status:** [ ] PASS [ ] FAIL

---

### Test 1.2: Mock Login - Invalid User

**Objective:** Verify authentication fails for non-existent user

**Procedure:**
```bash
curl -X POST http://localhost:8000/api/auth/mock-login \
  -H "Content-Type: application/json" \
  -d '{"email": "nonexistent@example.com"}' \
  | jq
```

**Expected Result:**
```json
{
  "detail": "User not found"
}
```

**Verification:**
- ✅ HTTP status code 404
- ✅ Error message indicates user not found

**Status:** [ ] PASS [ ] FAIL

---

### Test 1.3: Token Exchange - Valid Tenant

**Objective:** Verify token exchange returns tenant-scoped JWT

**Procedure:**
```bash
# Use USER_TOKEN from Test 1.1
curl -X POST http://localhost:8000/api/auth/token-exchange \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "tenant_id=8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345" \
  | jq

# Save tenant token
export TENANT_TOKEN_ACME=$(curl -s -X POST http://localhost:8000/api/auth/token-exchange \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "tenant_id=8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345" \
  | jq -r '.tenant_token')

echo "Tenant Token (Acme): $TENANT_TOKEN_ACME"
```

**Expected Result:**
```json
{
  "tenant_token": "<TENANT_SCOPED_JWT>",
  "token_type": "bearer",
  "expires_in": 1800,
  "tenant_id": "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"
}
```

**Verification:**
- ✅ Response contains `tenant_token` field
- ✅ Token is valid JWT format
- ✅ `expires_in` is 1800 seconds (30 minutes)
- ✅ `tenant_id` matches requested tenant

**Status:** [ ] PASS [ ] FAIL

---

### Test 1.4: Token Exchange - Unauthorized Tenant

**Objective:** Verify token exchange fails for unauthorized tenant access

**Procedure:**
```bash
# Try to get token for Beta tenant using Acme user credentials
curl -X POST http://localhost:8000/api/auth/token-exchange \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "tenant_id=2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4" \
  | jq
```

**Expected Result:**
```json
{
  "detail": "User does not have access to this tenant"
}
```

**Verification:**
- ✅ HTTP status code 403 or 401
- ✅ Error message indicates unauthorized access
- ✅ No tenant token returned

**Status:** [ ] PASS [ ] FAIL

---

### Test 1.5: Decode and Verify JWT Claims

**Objective:** Verify tenant-scoped token contains correct claims

**Procedure:**
```bash
# Decode JWT (without verification - for inspection only)
echo $TENANT_TOKEN_ACME | cut -d'.' -f2 | base64 -d 2>/dev/null | jq

# Or use jwt.io website: https://jwt.io
# Paste the token and inspect the payload
```

**Expected Claims:**
```json
{
  "sub": "<USER_ID>",
  "email": "analyst@acme.com",
  "tenant_id": "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
  "tenant_ids": ["8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"],
  "iat": <TIMESTAMP>,
  "exp": <TIMESTAMP>,
  "iss": "kyros-poc"
}
```

**Verification:**
- ✅ `tenant_id` is a string (NOT an array)
- ✅ `tenant_id` matches Acme tenant ID
- ✅ `exp` timestamp is ~30 minutes in the future
- ✅ `iss` is "kyros-poc"
- ✅ `sub` contains user ID
- ✅ `email` matches user

**Status:** [ ] PASS [ ] FAIL

---

## Test Suite 2: Data API & Tenant Isolation

### Test 2.1: Fetch CLV Dashboard Data - Acme Tenant

**Objective:** Verify Data API returns tenant-filtered CLV data

**Procedure:**
```bash
# Fetch CLV data with Acme tenant token
curl -s http://localhost:8000/api/dashboards/customer-lifetime-value/data \
  -H "Authorization: Bearer $TENANT_TOKEN_ACME" \
  | jq
```

**Expected Result:**
```json
{
  "dashboard_slug": "customer-lifetime-value",
  "tenant_id": "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
  "data": [
    {...},
    {...}
  ],
  "record_count": <NUMBER>
}
```

**Verification:**
- ✅ HTTP status code 200
- ✅ `tenant_id` matches Acme tenant
- ✅ `data` array contains records
- ✅ `record_count` > 0

**Status:** [ ] PASS [ ] FAIL

---

### Test 2.2: Fetch Risk Dashboard Data - Acme Tenant

**Objective:** Verify Data API returns tenant-filtered Risk data for Acme

**Procedure:**
```bash
# Fetch Risk data with Acme tenant token
curl -s http://localhost:8000/api/dashboards/risk-analysis/data \
  -H "Authorization: Bearer $TENANT_TOKEN_ACME" \
  | jq
```

**Expected Result:**
```json
{
  "dashboard_slug": "risk-analysis",
  "tenant_id": "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
  "data": [
    {...},
    {...}
  ],
  "record_count": <NUMBER>
}
```

**Verification:**
- ✅ HTTP status code 200
- ✅ `tenant_id` matches Acme tenant
- ✅ `data` array contains Acme risk records
- ✅ `record_count` > 0

**Status:** [ ] PASS [ ] FAIL

---

### Test 2.3: Fetch Dashboard Data - No Authorization Header

**Objective:** Verify API rejects requests without authentication

**Procedure:**
```bash
# Try to fetch data without token
curl -s http://localhost:8000/api/dashboards/customer-lifetime-value/data \
  | jq
```

**Expected Result:**
```json
{
  "detail": "Not authenticated"
}
```

**Verification:**
- ✅ HTTP status code 401
- ✅ Error message indicates authentication required

**Status:** [ ] PASS [ ] FAIL

---

### Test 2.4: Fetch Dashboard Data - Invalid Token

**Objective:** Verify API rejects requests with invalid tokens

**Procedure:**
```bash
# Try to fetch data with malformed token
curl -s http://localhost:8000/api/dashboards/customer-lifetime-value/data \
  -H "Authorization: Bearer invalid-token-123" \
  | jq
```

**Expected Result:**
```json
{
  "detail": "Could not validate credentials"
}
```

**Verification:**
- ✅ HTTP status code 401
- ✅ Error message indicates invalid credentials

**Status:** [ ] PASS [ ] FAIL

---

### Test 2.5: Fetch Dashboard Data - Expired Token

**Objective:** Verify API rejects expired tokens

**Procedure:**
```bash
# Use a pre-expired token (you'll need to modify JWT_SECRET_KEY temporarily
# or wait 30 minutes for TENANT_TOKEN_ACME to expire)

# For immediate testing, use this known expired token:
EXPIRED_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjB9.invalid"

curl -s http://localhost:8000/api/dashboards/customer-lifetime-value/data \
  -H "Authorization: Bearer $EXPIRED_TOKEN" \
  | jq
```

**Expected Result:**
```json
{
  "detail": "Token has expired"
}
```

**Verification:**
- ✅ HTTP status code 401
- ✅ Error message indicates expired token

**Status:** [ ] PASS [ ] FAIL

---

### Test 2.6: Beta Tenant Authentication Setup

**Objective:** Set up Beta tenant authentication for multi-tenant tests

**Procedure:**
```bash
# Login as Beta user
export USER_TOKEN_BETA=$(curl -s -X POST http://localhost:8000/api/auth/mock-login \
  -H "Content-Type: application/json" \
  -d '{"email": "viewer@beta.com"}' \
  | jq -r '.access_token')

# Exchange for Beta tenant token
export TENANT_TOKEN_BETA=$(curl -s -X POST http://localhost:8000/api/auth/token-exchange \
  -H "Authorization: Bearer $USER_TOKEN_BETA" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "tenant_id=2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4" \
  | jq -r '.tenant_token')

echo "Beta Tenant Token: $TENANT_TOKEN_BETA"
```

**Expected Result:**
- Valid JWT token for Beta tenant

**Verification:**
- ✅ Token obtained successfully
- ✅ Token contains Beta tenant ID when decoded

**Status:** [ ] PASS [ ] FAIL

---

### Test 2.7: Fetch Risk Data - Beta Tenant

**Objective:** Verify Beta tenant can access their Risk data

**Procedure:**
```bash
# Fetch Risk data with Beta tenant token
curl -s http://localhost:8000/api/dashboards/risk-analysis/data \
  -H "Authorization: Bearer $TENANT_TOKEN_BETA" \
  | jq
```

**Expected Result:**
```json
{
  "dashboard_slug": "risk-analysis",
  "tenant_id": "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4",
  "data": [
    {...},
    {...}
  ],
  "record_count": <NUMBER>
}
```

**Verification:**
- ✅ HTTP status code 200
- ✅ `tenant_id` matches Beta tenant
- ✅ `data` array contains Beta risk records
- ✅ Data is DIFFERENT from Acme risk data (Test 2.2)

**Status:** [ ] PASS [ ] FAIL

---

### Test 2.8: Beta Tenant CLV Access (Should Fail)

**Objective:** Verify Beta tenant CANNOT access CLV dashboard (not assigned)

**Procedure:**
```bash
# Try to fetch CLV data with Beta tenant token
curl -s http://localhost:8000/api/dashboards/customer-lifetime-value/data \
  -H "Authorization: Bearer $TENANT_TOKEN_BETA" \
  | jq
```

**Expected Result:**
```json
{
  "detail": "Dashboard not found or not accessible"
}
```

**Verification:**
- ✅ HTTP status code 404 or 403
- ✅ Error message indicates no access
- ✅ No data returned

**Status:** [ ] PASS [ ] FAIL

---

## Test Suite 3: CLV Dashboard Integration

### Test 3.1: CLV Dashboard - No Authentication

**Objective:** Verify dashboard requires authentication

**Procedure:**
```bash
# Try to access dashboard without token
curl -s http://localhost:8050/ | head -n 20
```

**Expected Result:**
- HTTP 401 Unauthorized response
- JSON error response or HTML error page

**Verification:**
- ✅ HTTP status code 401
- ✅ Access denied without valid token

**Status:** [ ] PASS [ ] FAIL

---

### Test 3.2: CLV Dashboard - Valid Acme Token

**Objective:** Verify dashboard loads with valid tenant token

**Procedure:**
```bash
# Access dashboard with Acme tenant token
curl -s http://localhost:8050/ \
  -H "Authorization: Bearer $TENANT_TOKEN_ACME" \
  | head -n 50

# Check if HTML contains dashboard title
curl -s http://localhost:8050/ \
  -H "Authorization: Bearer $TENANT_TOKEN_ACME" \
  | grep -i "Customer Lifetime Value"
```

**Expected Result:**
- HTTP 200 OK
- HTML response containing dashboard content
- "Customer Lifetime Value Dashboard" title present

**Verification:**
- ✅ HTTP status code 200
- ✅ HTML content returned
- ✅ Dashboard title found in response
- ✅ Check logs show: "JWT validated successfully for tenant: <ACME_ID>"

**Status:** [ ] PASS [ ] FAIL

---

### Test 3.3: CLV Dashboard - Tenant Info Display

**Objective:** Verify dashboard displays correct tenant context

**Procedure:**
```bash
# Access dashboard and check for tenant ID display
curl -s http://localhost:8050/ \
  -H "Authorization: Bearer $TENANT_TOKEN_ACME" \
  | grep -i "8e1b3d5b"
```

**Expected Result:**
- Response contains Acme tenant ID in display

**Verification:**
- ✅ Tenant ID visible in HTML response
- ✅ Logs show correct tenant_id extracted

**Status:** [ ] PASS [ ] FAIL

---

### Test 3.4: CLV Dashboard - Data API Integration

**Objective:** Verify dashboard fetches data from API

**Procedure:**
```bash
# Monitor CLV dashboard logs while accessing
docker-compose logs dash-app-clv --tail=50 | grep -i "fetching\|received"

# In another terminal, access dashboard
curl -s http://localhost:8050/ \
  -H "Authorization: Bearer $TENANT_TOKEN_ACME" > /dev/null
```

**Expected Log Entries:**
```
INFO - Fetching data for dashboard: customer-lifetime-value, tenant: 8e1b3d5b-...
INFO - Received <N> records for customer-lifetime-value
INFO - Rendered CLV segment graph with <N> records
```

**Verification:**
- ✅ Logs show data fetch from API
- ✅ Logs show tenant_id in fetch request
- ✅ Logs show record count received
- ✅ Logs show successful visualization rendering

**Status:** [ ] PASS [ ] FAIL

---

### Test 3.5: CLV Dashboard - Invalid Token

**Objective:** Verify dashboard rejects invalid tokens

**Procedure:**
```bash
# Try to access with invalid token
curl -s http://localhost:8050/ \
  -H "Authorization: Bearer invalid-token-xyz" \
  | jq
```

**Expected Result:**
```json
{
  "error": "UNAUTHORIZED",
  "message": "Invalid or expired token: ..."
}
```

**Verification:**
- ✅ HTTP status code 401
- ✅ Error response returned
- ✅ Logs show: "JWT validation failed"

**Status:** [ ] PASS [ ] FAIL

---

### Test 3.6: CLV Dashboard - Beta Token (Should Fail)

**Objective:** Verify CLV dashboard denies Beta tenant access

**Procedure:**
```bash
# Try to access CLV with Beta tenant token
curl -s http://localhost:8050/ \
  -H "Authorization: Bearer $TENANT_TOKEN_BETA" \
  | head -n 20
```

**Expected Result:**
- HTTP 200 (JWT is valid)
- But "No Data Available" or "404" message in dashboard
- Data API returns 404 for Beta accessing CLV

**Verification:**
- ✅ Dashboard loads (JWT valid)
- ✅ No CLV data displayed (Beta has no access)
- ✅ Error message shown in UI
- ✅ Logs show data API returned 404 or empty data

**Status:** [ ] PASS [ ] FAIL

---

### Test 3.7: CLV Dashboard - Browser Test (Optional)

**Objective:** Manually verify dashboard UI in browser

**Procedure:**

**Note:** This requires the Shell UI to be functioning for proper token injection. If Shell UI is not yet complete, skip this test.

1. Open browser to http://localhost:3000
2. Login as `analyst@acme.com`
3. Select Acme Corp tenant
4. Navigate to CLV Dashboard
5. Observe visualizations

**Expected Result:**
- Dashboard displays 3 visualizations
- Tenant info shows Acme tenant ID
- Data visualizations render correctly
- Auto-refresh works (60 second interval)

**Verification:**
- ✅ All visualizations load
- ✅ Tenant context displayed
- ✅ Data appears tenant-specific
- ✅ No errors in browser console

**Status:** [ ] PASS [ ] FAIL [ ] SKIPPED

---

## Test Suite 4: Risk Dashboard Integration

### Test 4.1: Risk Dashboard - No Authentication

**Objective:** Verify Risk dashboard requires authentication

**Procedure:**
```bash
# Try to access dashboard without token
curl -s http://localhost:8051/ | head -n 20
```

**Expected Result:**
- HTTP 401 Unauthorized response

**Verification:**
- ✅ HTTP status code 401
- ✅ Access denied without valid token

**Status:** [ ] PASS [ ] FAIL

---

### Test 4.2: Risk Dashboard - Valid Acme Token

**Objective:** Verify Risk dashboard loads for Acme tenant

**Procedure:**
```bash
# Access Risk dashboard with Acme tenant token
curl -s http://localhost:8051/ \
  -H "Authorization: Bearer $TENANT_TOKEN_ACME" \
  | grep -i "Risk Analysis"
```

**Expected Result:**
- HTTP 200 OK
- "Risk Analysis Dashboard" title present

**Verification:**
- ✅ HTTP status code 200
- ✅ Dashboard title found
- ✅ Logs show: "JWT validated successfully for tenant: <ACME_ID>"

**Status:** [ ] PASS [ ] FAIL

---

### Test 4.3: Risk Dashboard - Valid Beta Token

**Objective:** Verify Risk dashboard loads for Beta tenant

**Procedure:**
```bash
# Access Risk dashboard with Beta tenant token
curl -s http://localhost:8051/ \
  -H "Authorization: Bearer $TENANT_TOKEN_BETA" \
  | grep -i "Risk Analysis"
```

**Expected Result:**
- HTTP 200 OK
- "Risk Analysis Dashboard" title present

**Verification:**
- ✅ HTTP status code 200
- ✅ Dashboard title found
- ✅ Logs show: "JWT validated successfully for tenant: <BETA_ID>"

**Status:** [ ] PASS [ ] FAIL

---

### Test 4.4: Risk Dashboard - Data API Integration (Acme)

**Objective:** Verify Risk dashboard fetches Acme data from API

**Procedure:**
```bash
# Monitor Risk dashboard logs
docker-compose logs dash-app-risk --tail=50 | grep -i "fetching\|received"

# Access dashboard
curl -s http://localhost:8051/ \
  -H "Authorization: Bearer $TENANT_TOKEN_ACME" > /dev/null
```

**Expected Log Entries:**
```
INFO - Fetching data for dashboard: risk-analysis, tenant: 8e1b3d5b-...
INFO - Received <N> records for risk-analysis
INFO - Rendered Risk distribution graph with <N> records
```

**Verification:**
- ✅ Logs show data fetch for risk-analysis
- ✅ Logs show Acme tenant_id
- ✅ Logs show records received
- ✅ Visualizations rendered successfully

**Status:** [ ] PASS [ ] FAIL

---

### Test 4.5: Risk Dashboard - Data API Integration (Beta)

**Objective:** Verify Risk dashboard fetches Beta data from API

**Procedure:**
```bash
# Monitor Risk dashboard logs
docker-compose logs dash-app-risk --tail=50 | grep -i "fetching\|received"

# Access dashboard with Beta token
curl -s http://localhost:8051/ \
  -H "Authorization: Bearer $TENANT_TOKEN_BETA" > /dev/null
```

**Expected Log Entries:**
```
INFO - Fetching data for dashboard: risk-analysis, tenant: 2450a2f8-...
INFO - Received <N> records for risk-analysis
INFO - Rendered Risk distribution graph with <N> records
```

**Verification:**
- ✅ Logs show data fetch for risk-analysis
- ✅ Logs show Beta tenant_id (DIFFERENT from Acme)
- ✅ Logs show records received
- ✅ Record count may differ from Acme

**Status:** [ ] PASS [ ] FAIL

---

### Test 4.6: Risk Dashboard - Pattern Consistency Verification

**Objective:** Verify Risk dashboard follows CLV pattern exactly

**Procedure:**

This is a code review checkpoint - verify the following files are identical between dashboards:

```bash
# Compare auth middleware
diff apps/dash-app-clv/auth_middleware.py apps/dash-app-risk/auth_middleware.py

# Compare data client
diff apps/dash-app-clv/data_client.py apps/dash-app-risk/data_client.py

# Compare error page
diff apps/dash-app-clv/error_page.py apps/dash-app-risk/error_page.py

# Compare requirements
diff apps/dash-app-clv/requirements.txt apps/dash-app-risk/requirements.txt
```

**Expected Result:**
- All diffs should be empty (no output)

**Verification:**
- ✅ auth_middleware.py: IDENTICAL
- ✅ data_client.py: IDENTICAL
- ✅ error_page.py: IDENTICAL
- ✅ requirements.txt: IDENTICAL

**Status:** [ ] PASS [ ] FAIL

---

## Test Suite 5: Multi-Tenant Data Isolation (CRITICAL)

### Test 5.1: Concurrent Access - Different Tenants

**Objective:** Verify no cross-tenant data leakage with concurrent requests

**Setup:**
Create test script `test_concurrent_access.sh`:

```bash
#!/bin/bash

# Set tokens
ACME_TOKEN="$TENANT_TOKEN_ACME"
BETA_TOKEN="$TENANT_TOKEN_BETA"

# Function to fetch Risk data and extract tenant_id
fetch_risk_data() {
    local TOKEN=$1
    local LABEL=$2
    local RESPONSE=$(curl -s http://localhost:8000/api/dashboards/risk-analysis/data \
      -H "Authorization: Bearer $TOKEN")

    local TENANT_ID=$(echo "$RESPONSE" | jq -r '.tenant_id')
    local RECORD_COUNT=$(echo "$RESPONSE" | jq -r '.record_count')

    echo "[$LABEL] Tenant ID: $TENANT_ID, Records: $RECORD_COUNT"
    echo "$RESPONSE" > "/tmp/risk_data_${LABEL}.json"
}

# Launch concurrent requests
echo "Launching concurrent requests..."
for i in {1..10}; do
    fetch_risk_data "$ACME_TOKEN" "ACME_$i" &
    fetch_risk_data "$BETA_TOKEN" "BETA_$i" &
done

# Wait for all background jobs
wait

echo "All requests completed."

# Verify all Acme requests returned Acme tenant_id
echo "Verifying Acme requests..."
for i in {1..10}; do
    TENANT=$(jq -r '.tenant_id' /tmp/risk_data_ACME_$i.json)
    if [ "$TENANT" != "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345" ]; then
        echo "ERROR: Acme request $i returned wrong tenant: $TENANT"
        exit 1
    fi
done
echo "✓ All Acme requests returned Acme data"

# Verify all Beta requests returned Beta tenant_id
echo "Verifying Beta requests..."
for i in {1..10}; do
    TENANT=$(jq -r '.tenant_id' /tmp/risk_data_BETA_$i.json)
    if [ "$TENANT" != "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4" ]; then
        echo "ERROR: Beta request $i returned wrong tenant: $TENANT"
        exit 1
    fi
done
echo "✓ All Beta requests returned Beta data"

# Clean up
rm -f /tmp/risk_data_*.json

echo "✓ PASS: No cross-tenant data leakage detected"
```

**Procedure:**
```bash
# Make script executable
chmod +x test_concurrent_access.sh

# Run test
./test_concurrent_access.sh
```

**Expected Output:**
```
Launching concurrent requests...
[ACME_1] Tenant ID: 8e1b3d5b-..., Records: X
[BETA_1] Tenant ID: 2450a2f8-..., Records: Y
...
All requests completed.
Verifying Acme requests...
✓ All Acme requests returned Acme data
Verifying Beta requests...
✓ All Beta requests returned Beta data
✓ PASS: No cross-tenant data leakage detected
```

**Verification:**
- ✅ All Acme requests return Acme tenant_id
- ✅ All Beta requests return Beta tenant_id
- ✅ No cross-contamination detected
- ✅ Record counts consistent per tenant
- ✅ Check logs for no error messages

**Status:** [ ] PASS [ ] FAIL

**CRITICAL: This test MUST PASS before production deployment.**

---

### Test 5.2: Concurrent Dashboard Access

**Objective:** Verify dashboards maintain tenant isolation under concurrent access

**Setup:**
Create test script `test_concurrent_dashboards.sh`:

```bash
#!/bin/bash

ACME_TOKEN="$TENANT_TOKEN_ACME"
BETA_TOKEN="$TENANT_TOKEN_BETA"

# Function to access dashboard and verify tenant info
access_dashboard() {
    local TOKEN=$1
    local EXPECTED_TENANT=$2
    local LABEL=$3

    local RESPONSE=$(curl -s http://localhost:8051/ \
      -H "Authorization: Bearer $TOKEN")

    if echo "$RESPONSE" | grep -q "$EXPECTED_TENANT"; then
        echo "[$LABEL] ✓ Correct tenant context"
        return 0
    else
        echo "[$LABEL] ✗ WRONG tenant context!"
        return 1
    fi
}

echo "Testing concurrent dashboard access..."

FAIL_COUNT=0

# Launch concurrent dashboard requests
for i in {1..5}; do
    access_dashboard "$ACME_TOKEN" "8e1b3d5b" "ACME_$i" || ((FAIL_COUNT++)) &
    access_dashboard "$BETA_TOKEN" "2450a2f8" "BETA_$i" || ((FAIL_COUNT++)) &
done

wait

if [ $FAIL_COUNT -eq 0 ]; then
    echo "✓ PASS: All dashboard requests returned correct tenant context"
    exit 0
else
    echo "✗ FAIL: $FAIL_COUNT requests returned wrong tenant context"
    exit 1
fi
```

**Procedure:**
```bash
# Make script executable
chmod +x test_concurrent_dashboards.sh

# Run test
./test_concurrent_dashboards.sh
```

**Expected Output:**
```
Testing concurrent dashboard access...
[ACME_1] ✓ Correct tenant context
[BETA_1] ✓ Correct tenant context
...
✓ PASS: All dashboard requests returned correct tenant context
```

**Verification:**
- ✅ All requests return correct tenant context
- ✅ No cross-tenant contamination
- ✅ Check dashboard logs for correct tenant_ids

**Status:** [ ] PASS [ ] FAIL

---

### Test 5.3: Data Comparison - Acme vs Beta Risk Data

**Objective:** Verify Acme and Beta receive DIFFERENT risk data

**Procedure:**
```bash
# Fetch Acme risk data
curl -s http://localhost:8000/api/dashboards/risk-analysis/data \
  -H "Authorization: Bearer $TENANT_TOKEN_ACME" \
  > /tmp/acme_risk.json

# Fetch Beta risk data
curl -s http://localhost:8000/api/dashboards/risk-analysis/data \
  -H "Authorization: Bearer $TENANT_TOKEN_BETA" \
  > /tmp/beta_risk.json

# Compare record counts
ACME_COUNT=$(jq '.record_count' /tmp/acme_risk.json)
BETA_COUNT=$(jq '.record_count' /tmp/beta_risk.json)

echo "Acme Risk Records: $ACME_COUNT"
echo "Beta Risk Records: $BETA_COUNT"

# Compare first record IDs (they should be different)
ACME_FIRST=$(jq '.data[0]' /tmp/acme_risk.json)
BETA_FIRST=$(jq '.data[0]' /tmp/beta_risk.json)

echo "Acme First Record:"
echo "$ACME_FIRST" | jq

echo "Beta First Record:"
echo "$BETA_FIRST" | jq

# Verify they are different
if [ "$ACME_FIRST" == "$BETA_FIRST" ]; then
    echo "✗ FAIL: Acme and Beta received IDENTICAL data!"
    exit 1
else
    echo "✓ PASS: Acme and Beta received DIFFERENT data"
fi

# Clean up
rm -f /tmp/acme_risk.json /tmp/beta_risk.json
```

**Expected Output:**
```
Acme Risk Records: <NUMBER_A>
Beta Risk Records: <NUMBER_B>
Acme First Record:
{ <DATA_A> }
Beta First Record:
{ <DATA_B> }
✓ PASS: Acme and Beta received DIFFERENT data
```

**Verification:**
- ✅ Record counts likely differ (may be same by coincidence)
- ✅ First records are DIFFERENT
- ✅ Tenant IDs in responses match requested tenant

**Status:** [ ] PASS [ ] FAIL

**CRITICAL: This test MUST PASS to confirm tenant data isolation.**

---

## Test Suite 6: Error Handling & Security

### Test 6.1: Expired Token Handling - API

**Objective:** Verify API properly rejects expired tokens

**Note:** This test requires either waiting 30 minutes for a token to expire, or using a pre-created expired token.

**Procedure:**
```bash
# Option 1: Wait for token expiration (30 minutes)
# Then retry Test 2.1

# Option 2: Use known expired token
EXPIRED_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjB9.signature"

curl -s http://localhost:8000/api/dashboards/risk-analysis/data \
  -H "Authorization: Bearer $EXPIRED_TOKEN" \
  | jq
```

**Expected Result:**
```json
{
  "detail": "Token has expired"
}
```

**Verification:**
- ✅ HTTP status code 401
- ✅ Specific error about expiration

**Status:** [ ] PASS [ ] FAIL [ ] SKIPPED

---

### Test 6.2: Malformed Authorization Header

**Objective:** Verify proper error handling for malformed headers

**Procedure:**
```bash
# Missing "Bearer" prefix
curl -s http://localhost:8050/ \
  -H "Authorization: $TENANT_TOKEN_ACME" \
  | jq

# Wrong format
curl -s http://localhost:8050/ \
  -H "Authorization: Token $TENANT_TOKEN_ACME" \
  | jq
```

**Expected Result:**
```json
{
  "error": "UNAUTHORIZED",
  "message": "Malformed Authorization header. Expected format: Bearer <token>"
}
```

**Verification:**
- ✅ HTTP status code 401
- ✅ Clear error message about header format

**Status:** [ ] PASS [ ] FAIL

---

### Test 6.3: Token Tampering Detection

**Objective:** Verify JWT signature validation prevents tampering

**Procedure:**
```bash
# Take valid token and modify payload (break signature)
TAMPERED_TOKEN=$(echo $TENANT_TOKEN_ACME | sed 's/\(.*\.\)\(.*\)\.\(.*\)/\1TAMPERED\.\3/')

echo "Tampered Token: $TAMPERED_TOKEN"

# Try to use tampered token
curl -s http://localhost:8000/api/dashboards/risk-analysis/data \
  -H "Authorization: Bearer $TAMPERED_TOKEN" \
  | jq
```

**Expected Result:**
```json
{
  "detail": "Could not validate credentials"
}
```

**Verification:**
- ✅ HTTP status code 401
- ✅ Token rejected due to invalid signature

**Status:** [ ] PASS [ ] FAIL

---

### Test 6.4: Data API Connection Failure

**Objective:** Verify dashboard handles API unavailability gracefully

**Procedure:**
```bash
# Stop API service
docker-compose stop api

# Wait a moment
sleep 5

# Try to access dashboard (it should load but show error for data)
curl -s http://localhost:8051/ \
  -H "Authorization: Bearer $TENANT_TOKEN_ACME" \
  | grep -i "error\|failed\|unavailable"

# Restart API
docker-compose start api
sleep 10
```

**Expected Result:**
- Dashboard loads (JWT validation still works in Dash app)
- Error message displayed: "Failed to load data from API"
- User-friendly error UI shown

**Verification:**
- ✅ Dashboard doesn't crash
- ✅ Error message displayed in UI
- ✅ Logs show: "Data API request failed" or "Could not connect to Data API"

**Status:** [ ] PASS [ ] FAIL

---

### Test 6.5: Missing Tenant ID in JWT

**Objective:** Verify proper error when JWT lacks tenant_id claim

**Note:** This requires creating a custom JWT without tenant_id (advanced - may skip)

**Expected Behavior:**
- Auth middleware rejects token
- Error: "Invalid token: missing tenant_id claim"
- HTTP 401

**Status:** [ ] PASS [ ] FAIL [ ] SKIPPED

---

## Test Suite 7: End-to-End Integration

### Test 7.1: Complete Flow - Acme User

**Objective:** Execute complete authentication and dashboard access flow for Acme user

**Procedure:**
```bash
echo "=== E2E Test: Acme User ==="

# Step 1: Mock Login
echo "Step 1: Mock Login"
USER_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/mock-login \
  -H "Content-Type: application/json" \
  -d '{"email": "analyst@acme.com"}' \
  | jq -r '.access_token')
echo "✓ User token obtained"

# Step 2: Token Exchange
echo "Step 2: Token Exchange"
TENANT_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token-exchange \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "tenant_id=8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345" \
  | jq -r '.tenant_token')
echo "✓ Tenant token obtained"

# Step 3: Access CLV Dashboard
echo "Step 3: Access CLV Dashboard"
CLV_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8050/ \
  -H "Authorization: Bearer $TENANT_TOKEN")
if [ "$CLV_RESPONSE" == "200" ]; then
    echo "✓ CLV Dashboard accessible"
else
    echo "✗ CLV Dashboard failed: HTTP $CLV_RESPONSE"
    exit 1
fi

# Step 4: Access Risk Dashboard
echo "Step 4: Access Risk Dashboard"
RISK_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8051/ \
  -H "Authorization: Bearer $TENANT_TOKEN")
if [ "$RISK_RESPONSE" == "200" ]; then
    echo "✓ Risk Dashboard accessible"
else
    echo "✗ Risk Dashboard failed: HTTP $RISK_RESPONSE"
    exit 1
fi

# Step 5: Fetch CLV Data
echo "Step 5: Fetch CLV Data"
CLV_DATA=$(curl -s http://localhost:8000/api/dashboards/customer-lifetime-value/data \
  -H "Authorization: Bearer $TENANT_TOKEN" \
  | jq -r '.tenant_id')
if [ "$CLV_DATA" == "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345" ]; then
    echo "✓ CLV data returned for correct tenant"
else
    echo "✗ CLV data returned for wrong tenant: $CLV_DATA"
    exit 1
fi

# Step 6: Fetch Risk Data
echo "Step 6: Fetch Risk Data"
RISK_DATA=$(curl -s http://localhost:8000/api/dashboards/risk-analysis/data \
  -H "Authorization: Bearer $TENANT_TOKEN" \
  | jq -r '.tenant_id')
if [ "$RISK_DATA" == "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345" ]; then
    echo "✓ Risk data returned for correct tenant"
else
    echo "✗ Risk data returned for wrong tenant: $RISK_DATA"
    exit 1
fi

echo ""
echo "✓✓✓ E2E Test PASSED: Acme User ✓✓✓"
```

**Expected Output:**
```
=== E2E Test: Acme User ===
Step 1: Mock Login
✓ User token obtained
Step 2: Token Exchange
✓ Tenant token obtained
Step 3: Access CLV Dashboard
✓ CLV Dashboard accessible
Step 4: Access Risk Dashboard
✓ Risk Dashboard accessible
Step 5: Fetch CLV Data
✓ CLV data returned for correct tenant
Step 6: Fetch Risk Data
✓ Risk data returned for correct tenant

✓✓✓ E2E Test PASSED: Acme User ✓✓✓
```

**Verification:**
- ✅ All steps complete successfully
- ✅ Both dashboards accessible
- ✅ Data returns correct tenant_id

**Status:** [ ] PASS [ ] FAIL

---

### Test 7.2: Complete Flow - Beta User

**Objective:** Execute complete flow for Beta user (Risk only, no CLV)

**Procedure:**
```bash
echo "=== E2E Test: Beta User ==="

# Step 1: Mock Login
echo "Step 1: Mock Login"
USER_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/mock-login \
  -H "Content-Type: application/json" \
  -d '{"email": "viewer@beta.com"}' \
  | jq -r '.access_token')
echo "✓ User token obtained"

# Step 2: Token Exchange
echo "Step 2: Token Exchange"
TENANT_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token-exchange \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "tenant_id=2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4" \
  | jq -r '.tenant_token')
echo "✓ Tenant token obtained"

# Step 3: Try CLV Dashboard (should work but return no data)
echo "Step 3: Try CLV Dashboard (should be denied)"
CLV_RESPONSE=$(curl -s http://localhost:8050/ \
  -H "Authorization: Bearer $TENANT_TOKEN")
if echo "$CLV_RESPONSE" | grep -qi "no data\|404\|not found"; then
    echo "✓ CLV Dashboard correctly denied/shows no data"
else
    echo "⚠ CLV Dashboard response unexpected (review manually)"
fi

# Step 4: Access Risk Dashboard
echo "Step 4: Access Risk Dashboard"
RISK_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8051/ \
  -H "Authorization: Bearer $TENANT_TOKEN")
if [ "$RISK_RESPONSE" == "200" ]; then
    echo "✓ Risk Dashboard accessible"
else
    echo "✗ Risk Dashboard failed: HTTP $RISK_RESPONSE"
    exit 1
fi

# Step 5: Try to fetch CLV Data (should fail)
echo "Step 5: Try to fetch CLV Data (should fail)"
CLV_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:8000/api/dashboards/customer-lifetime-value/data \
  -H "Authorization: Bearer $TENANT_TOKEN")
if [ "$CLV_STATUS" == "404" ] || [ "$CLV_STATUS" == "403" ]; then
    echo "✓ CLV data correctly denied (HTTP $CLV_STATUS)"
else
    echo "✗ CLV data should be denied but got: HTTP $CLV_STATUS"
    exit 1
fi

# Step 6: Fetch Risk Data (should succeed)
echo "Step 6: Fetch Risk Data"
RISK_DATA=$(curl -s http://localhost:8000/api/dashboards/risk-analysis/data \
  -H "Authorization: Bearer $TENANT_TOKEN" \
  | jq -r '.tenant_id')
if [ "$RISK_DATA" == "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4" ]; then
    echo "✓ Risk data returned for correct tenant"
else
    echo "✗ Risk data returned for wrong tenant: $RISK_DATA"
    exit 1
fi

echo ""
echo "✓✓✓ E2E Test PASSED: Beta User ✓✓✓"
```

**Expected Output:**
```
=== E2E Test: Beta User ===
Step 1: Mock Login
✓ User token obtained
Step 2: Token Exchange
✓ Tenant token obtained
Step 3: Try CLV Dashboard (should be denied)
✓ CLV Dashboard correctly denied/shows no data
Step 4: Access Risk Dashboard
✓ Risk Dashboard accessible
Step 5: Try to fetch CLV Data (should fail)
✓ CLV data correctly denied (HTTP 404)
Step 6: Fetch Risk Data
✓ Risk data returned for correct tenant

✓✓✓ E2E Test PASSED: Beta User ✓✓✓
```

**Verification:**
- ✅ Beta user can access Risk dashboard
- ✅ Beta user CANNOT access CLV data
- ✅ Risk data returns Beta tenant_id
- ✅ Proper authorization enforcement

**Status:** [ ] PASS [ ] FAIL

---

### Test 7.3: Logging Verification

**Objective:** Verify comprehensive logging at all handoff points

**Procedure:**
```bash
# Clear logs
docker-compose restart api dash-app-clv dash-app-risk
sleep 10

# Execute a complete flow
USER_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/mock-login \
  -H "Content-Type: application/json" \
  -d '{"email": "analyst@acme.com"}' \
  | jq -r '.access_token')

TENANT_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token-exchange \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "tenant_id=8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345" \
  | jq -r '.tenant_token')

curl -s http://localhost:8051/ \
  -H "Authorization: Bearer $TENANT_TOKEN" > /dev/null

# Check logs for expected entries
echo "Checking API logs..."
docker-compose logs api | grep -i "token exchange\|validated\|tenant"

echo "Checking Risk Dashboard logs..."
docker-compose logs dash-app-risk | grep -i "jwt validated\|fetching data\|tenant"
```

**Expected Log Patterns:**

**API Logs:**
```
INFO - Token exchange requested for tenant: 8e1b3d5b-...
INFO - User <ID> has access to tenant 8e1b3d5b-...
INFO - Token exchange successful for tenant: 8e1b3d5b-...
```

**Dashboard Logs:**
```
INFO - JWT validated successfully for tenant: 8e1b3d5b-...
INFO - Fetching data for dashboard: risk-analysis, tenant: 8e1b3d5b-...
INFO - Received <N> records for risk-analysis
```

**Verification:**
- ✅ API logs show token exchange
- ✅ Dashboard logs show JWT validation
- ✅ Dashboard logs show data fetching with tenant_id
- ✅ No error messages in logs

**Status:** [ ] PASS [ ] FAIL

---

## Test Suite 8: Epic 5 - Reverse Proxy & Dashboard Embedding

**Epic Context:** Epic 5 introduces the reverse proxy pattern and iframe-based dashboard embedding in the Shell UI. This enables:
- Server-side JWT injection (tokens never exposed to browser JavaScript)
- iframe embedding of Dash dashboards within Shell UI
- Proactive token refresh before expiry
- User-friendly error handling and notifications

### Test 8.1: Reverse Proxy - Token Injection

**Objective:** Verify reverse proxy injects Authorization header server-side

**Procedure:**
```bash
# Set up tokens from previous tests
export USER_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/mock-login \
  -H "Content-Type: application/json" \
  -d '{"email": "analyst@acme.com"}' \
  | jq -r '.access_token')

export TENANT_TOKEN_ACME=$(curl -s -X POST http://localhost:8000/api/auth/token-exchange \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "tenant_id=8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345" \
  | jq -r '.tenant_token')

# Test proxy route with token as query parameter (for iframe)
curl -s "http://localhost:3000/api/proxy/dash/customer-lifetime-value/?token=$TENANT_TOKEN_ACME" \
  | grep -i "Customer Lifetime Value"

# Test proxy route with X-Tenant-Token header (for direct fetch)
curl -s "http://localhost:3000/api/proxy/dash/customer-lifetime-value/" \
  -H "X-Tenant-Token: $TENANT_TOKEN_ACME" \
  | grep -i "Customer Lifetime Value"
```

**Expected Result:**
- Both requests return HTTP 200
- Dashboard HTML content returned
- Token stripped from query params before forwarding to Dash app
- Authorization header injected server-side

**Verification:**
- ✅ Query parameter method works (for iframes)
- ✅ Header method works (for direct requests)
- ✅ Dashboard content returned
- ✅ Check Shell UI logs: `[Proxy] Request:` and `[Proxy] Response: status: 200`

**Status:** [ ] PASS [ ] FAIL

---

### Test 8.2: Reverse Proxy - Invalid Dashboard Slug (SSRF Protection)

**Objective:** Verify proxy rejects invalid dashboard slugs

**Procedure:**
```bash
# Try to access non-existent dashboard
curl -s "http://localhost:3000/api/proxy/dash/invalid-dashboard/?token=$TENANT_TOKEN_ACME" \
  | jq

# Try to access arbitrary URL (should fail)
curl -s "http://localhost:3000/api/proxy/dash/../../../etc/passwd?token=$TENANT_TOKEN_ACME" \
  | jq
```

**Expected Result:**
```json
{
  "error": "INVALID_DASHBOARD",
  "message": "Dashboard 'invalid-dashboard' not found"
}
```

**Verification:**
- ✅ HTTP status code 404
- ✅ Error message indicates dashboard not found
- ✅ No arbitrary file access or SSRF vulnerability
- ✅ Logs show: `[Proxy] Invalid dashboard slug`

**Status:** [ ] PASS [ ] FAIL

---

### Test 8.3: Reverse Proxy - Missing Token

**Objective:** Verify proxy rejects requests without token

**Procedure:**
```bash
# Try to access dashboard without token
curl -s "http://localhost:3000/api/proxy/dash/customer-lifetime-value/" \
  | jq
```

**Expected Result:**
```json
{
  "error": "UNAUTHORIZED",
  "message": "Tenant token required"
}
```

**Verification:**
- ✅ HTTP status code 401
- ✅ Error message indicates missing token
- ✅ No dashboard content returned

**Status:** [ ] PASS [ ] FAIL

---

### Test 8.4: Reverse Proxy - Expired Token Detection

**Objective:** Verify proxy detects and returns standardized error for expired tokens

**Note:** This test requires either waiting 30 minutes for token expiry or using a pre-created expired token.

**Procedure:**
```bash
# Use an expired token (wait 30 minutes or use mock expired token)
# For testing, you can temporarily modify JWT_SECRET_KEY to invalidate tokens

EXPIRED_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjB9.invalid"

curl -s "http://localhost:3000/api/proxy/dash/customer-lifetime-value/?token=$EXPIRED_TOKEN" \
  | jq
```

**Expected Result:**
```json
{
  "error": "TOKEN_EXPIRED",
  "message": "Your session has expired. Please select your tenant again.",
  "dashboardSlug": "customer-lifetime-value"
}
```

**Verification:**
- ✅ HTTP status code 401
- ✅ Error code is TOKEN_EXPIRED
- ✅ User-friendly error message
- ✅ Logs show: `[Proxy] 401 Unauthorized from Dash app`

**Status:** [ ] PASS [ ] FAIL [ ] SKIPPED

---

### Test 8.5: Reverse Proxy - Docker Networking

**Objective:** Verify proxy uses Docker service names for inter-container communication

**Procedure:**
```bash
# Check proxy configuration
grep -A 5 "baseUrl" apps/shell-ui/app/lib/proxy-config.ts

# Verify environment variables
docker-compose exec shell-ui env | grep -i dash

# Test proxy in Docker environment
curl -s "http://localhost:3000/api/proxy/dash/risk-analysis/?token=$TENANT_TOKEN_ACME" \
  | grep -i "Risk Analysis"
```

**Expected Result:**
- Proxy config uses Docker service names (dash-app-clv, dash-app-risk) in production
- Proxy successfully reaches Dash containers
- Dashboard content returned

**Verification:**
- ✅ Proxy config shows service names for production
- ✅ Risk dashboard content returned via proxy
- ✅ No connection refused errors
- ✅ Logs show successful proxy to backend

**Status:** [ ] PASS [ ] FAIL

---

### Test 8.6: Dashboard Embedding - Browser Test (Shell UI)

**Objective:** Verify dashboard embedding works end-to-end in browser

**Procedure:**
1. Open browser to http://localhost:3000
2. Login as `analyst@acme.com` (password: any value for mock auth)
3. Select "Acme Corporation" tenant
4. Click on "Customer Lifetime Value" dashboard
5. Observe iframe-embedded dashboard

**Expected Result:**
- Dashboard loads in iframe without errors
- Tenant context displayed correctly
- Visualizations render properly
- No CORS errors in browser console
- Token never visible in browser (check Network tab)

**Verification:**
- ✅ Dashboard iframe loads successfully
- ✅ Dashboard displays correct tenant data
- ✅ No JavaScript errors in console
- ✅ Token passed via query param (not exposed to JS)
- ✅ Check Network tab: Authorization header not visible to client

**Status:** [ ] PASS [ ] FAIL

---

### Test 8.7: Dashboard Embedding - Navigation Flow

**Objective:** Verify complete navigation flow through Shell UI

**Procedure:**
1. Open http://localhost:3000
2. Login as `analyst@acme.com`
3. Verify redirect to tenant selection page (/)
4. Verify Acme tenant card displayed
5. Click on Acme tenant
6. Verify redirect to dashboard listing page
7. Verify CLV and Risk dashboards displayed
8. Click on "Customer Lifetime Value"
9. Verify redirect to `/tenant/acme-corporation/dashboard/customer-lifetime-value`
10. Verify dashboard loads in iframe
11. Click "Back to Dashboards" button
12. Verify return to dashboard listing
13. Click on "Risk Analysis"
14. Verify Risk dashboard loads

**Expected Result:**
- Smooth navigation flow with no errors
- Correct redirects at each step
- Dashboard URLs follow pattern: `/tenant/{tenant_slug}/dashboard/{dashboard_slug}`
- Breadcrumb navigation works correctly

**Verification:**
- ✅ Complete flow works without errors
- ✅ URLs follow expected pattern
- ✅ Navigation buttons work correctly
- ✅ Both dashboards accessible

**Status:** [ ] PASS [ ] FAIL

---

### Test 8.8: Dashboard Embedding - Tenant Validation

**Objective:** Verify dashboard access is validated against tenant assignments

**Procedure:**
```bash
# In browser:
# 1. Login as viewer@beta.com
# 2. Select Beta Industries tenant
# 3. Verify only Risk Analysis dashboard shown (NOT CLV)
# 4. Click on Risk Analysis
# 5. Verify dashboard loads with Beta data
# 6. Try to manually navigate to CLV dashboard:
#    http://localhost:3000/tenant/beta-industries/dashboard/customer-lifetime-value
```

**Expected Result:**
- Beta tenant sees only Risk Analysis dashboard in listing
- Attempting to access CLV dashboard shows "Dashboard Not Found" error
- Error message: "The requested dashboard is not available for this tenant"
- "Back to Dashboards" button provided

**Verification:**
- ✅ Dashboard listing shows only assigned dashboards
- ✅ Direct URL access to unassigned dashboard blocked
- ✅ User-friendly error message displayed
- ✅ No data leakage or unauthorized access

**Status:** [ ] PASS [ ] FAIL

---

### Test 8.9: Dashboard Embedding - iframe Error Handling

**Objective:** Verify iframe error states are handled gracefully

**Procedure:**
```bash
# Test 1: Dashboard service unavailable
docker-compose stop dash-app-clv

# In browser:
# 1. Navigate to CLV dashboard
# 2. Observe error state
# 3. Click "Retry" button
# 4. Observe continued error

# Restart service
docker-compose start dash-app-clv
sleep 10

# 5. Click "Retry" button again
# 6. Observe dashboard loads successfully

# Test 2: Loading state
# 1. Navigate to Risk dashboard
# 2. Observe loading skeleton/spinner while iframe loads
```

**Expected Result:**
- Loading state shows spinner and "Loading dashboard..." message
- Error state shows warning icon and clear error message
- "Retry" and "Back to Dashboards" buttons provided
- After service restart, retry successfully loads dashboard

**Verification:**
- ✅ Loading state displayed during iframe load
- ✅ Error state displayed when service unavailable
- ✅ Retry button works correctly
- ✅ Back button returns to dashboard listing
- ✅ Dashboard recovers after service restart

**Status:** [ ] PASS [ ] FAIL

---

### Test 8.10: Token Refresh - Proactive Refresh Scheduling

**Objective:** Verify proactive token refresh schedules correctly

**Procedure:**
```bash
# In browser with console open:
# 1. Login as analyst@acme.com
# 2. Select Acme tenant
# 3. Open browser console (F12)
# 4. Navigate to any dashboard
# 5. Look for console log: "[TokenRefresh] Scheduling refresh in X seconds"

# Check token expiry
echo $TENANT_TOKEN_ACME | cut -d'.' -f2 | base64 -d 2>/dev/null | jq '.exp'

# Calculate time until refresh (exp - now - 300 seconds)
```

**Expected Result:**
- Console log shows token refresh scheduled
- Refresh scheduled 5 minutes (300 seconds) before token expiry
- Token expiry set to 30 minutes from issuance

**Verification:**
- ✅ Token refresh scheduled on dashboard page load
- ✅ Refresh timing calculated correctly (25 minutes after token issue)
- ✅ Console log shows: `[TokenRefresh] Scheduling refresh in XXXs`

**Status:** [ ] PASS [ ] FAIL

---

### Test 8.11: Token Refresh - Successful Proactive Refresh

**Objective:** Verify proactive token refresh executes and updates token

**Note:** This test requires either waiting 25 minutes or temporarily modifying token expiry for faster testing.

**Procedure:**
```bash
# Option 1: Wait 25 minutes (or reduce token expiry to 6 minutes for testing)
# Option 2: Mock short-lived token by modifying token-exchange endpoint

# In browser with console open:
# 1. Wait for scheduled refresh to trigger
# 2. Observe console log: "[TokenRefresh] Refreshing token for tenant: <ID>"
# 3. Observe toast notification: "Session refreshed" (green, auto-dismiss)
# 4. Verify dashboard continues working without interruption
# 5. Check network tab for POST /api/auth/exchange request
```

**Expected Result:**
- Console log shows refresh initiated
- Toast notification appears briefly (green, success)
- New token obtained from exchange endpoint
- Dashboard continues functioning seamlessly
- No user interruption or redirect

**Verification:**
- ✅ Refresh triggered automatically
- ✅ Success notification displayed
- ✅ New token obtained and stored
- ✅ Dashboard remains functional
- ✅ No redirect or error

**Status:** [ ] PASS [ ] FAIL [ ] SKIPPED

---

### Test 8.12: Token Refresh - Failed Refresh Handling

**Objective:** Verify failed token refresh redirects user appropriately

**Procedure:**
```bash
# Simulate refresh failure by stopping API temporarily
# 1. In browser, login and navigate to dashboard
# 2. Wait for refresh trigger (or modify timing for testing)
# 3. Stop API just before refresh:
docker-compose stop api

# 4. Wait for refresh to trigger
# 5. Observe error toast notification
# 6. Observe redirect to tenant selection page

# Restart API
docker-compose start api
```

**Expected Result:**
- Toast notification: "Failed to refresh session. Please select your tenant again." (red, error)
- Console log: `[TokenRefresh] Failed to refresh token`
- Automatic redirect to home page (/)
- Tenant state cleared from store

**Verification:**
- ✅ Error notification displayed
- ✅ Console shows error log
- ✅ Redirect to tenant selection page
- ✅ User can select tenant again to resume

**Status:** [ ] PASS [ ] FAIL

---

### Test 8.13: Token Refresh - User Token Expiry

**Objective:** Verify user token expiry redirects to login

**Note:** This test requires waiting 1 hour for user token expiry, or using a mock expired user token.

**Procedure:**
```bash
# Wait for user token to expire (1 hour) or use expired token

# In browser:
# 1. Wait for token refresh to trigger (after 25 min of tenant token)
# 2. Observe refresh attempt fails due to expired user token
# 3. Observe toast notification: "Please log in again."
# 4. Observe redirect to /login page
```

**Expected Result:**
- Refresh fails with 401 from exchange endpoint
- Toast notification: "Please log in again." (red, error)
- Console log: `[TokenRefresh] User token expired during refresh`
- Redirect to /login page
- All auth state cleared

**Verification:**
- ✅ Refresh failure detected
- ✅ Error notification displayed
- ✅ Redirect to login page
- ✅ User can log in again

**Status:** [ ] PASS [ ] FAIL [ ] SKIPPED

---

### Test 8.14: Toast Notifications - Display and Dismissal

**Objective:** Verify toast notification system works correctly

**Procedure:**
```bash
# In browser console, manually trigger toasts:
# 1. Open browser console
# 2. Import toast:
#    import { toast } from '/components/ui/Toast';
# 3. Trigger different toast types:
toast.info('This is an info message');
toast.success('This is a success message');
toast.warning('This is a warning message');
toast.error('This is an error message');

# 4. Observe each toast
# 5. Click X button to manually dismiss
# 6. Wait 5 seconds for auto-dismiss
```

**Expected Result:**
- Toasts appear in top-right corner
- Each type has distinct color (blue, green, yellow, red)
- Appropriate icon shown (ℹ️, ✓, ⚠️, ✕)
- Auto-dismiss after 5 seconds
- Manual dismiss works via X button
- Multiple toasts stack vertically

**Verification:**
- ✅ All toast types display correctly
- ✅ Colors and icons appropriate
- ✅ Auto-dismiss after 5 seconds
- ✅ Manual dismiss works
- ✅ Multiple toasts visible simultaneously

**Status:** [ ] PASS [ ] FAIL

---

### Test 8.15: End-to-End Epic 5 Flow

**Objective:** Execute complete Epic 5 flow from login to dashboard with token refresh

**Procedure:**
```bash
echo "=== E2E Epic 5 Flow ==="

# Step 1: Browser - Login
# 1. Open http://localhost:3000
# 2. Login as analyst@acme.com

# Step 2: Browser - Select Tenant
# 3. Click on "Acme Corporation"
# 4. Verify redirect to /tenant/acme-corporation

# Step 3: Browser - Dashboard Listing
# 5. Verify CLV and Risk dashboards shown
# 6. Click on "Customer Lifetime Value"

# Step 4: Browser - Embedded Dashboard via Proxy
# 7. Verify URL: /tenant/acme-corporation/dashboard/customer-lifetime-value
# 8. Verify dashboard loads in iframe
# 9. Verify tenant context correct
# 10. Verify visualizations render

# Step 5: Console - Token Refresh Scheduling
# 11. Open browser console
# 12. Verify log: "[TokenRefresh] Scheduling refresh in Xs"

# Step 6: Network Tab - Verify Token Injection
# 13. Open Network tab
# 14. Refresh dashboard
# 15. Find request to /api/proxy/dash/customer-lifetime-value/
# 16. Verify query param includes token
# 17. Verify no Authorization header visible in browser

# Step 7: Backend Logs - Verify Server-Side Injection
# 18. Check Shell UI logs:
docker-compose logs shell-ui --tail=20 | grep "\[Proxy\]"

# 19. Verify logs show Authorization header injected

# Step 8: Toast - Manual Test
# 20. In console, trigger test toast:
#     (Skip if automatic refresh happens)

echo "✓✓✓ E2E Epic 5 Flow Complete ✓✓✓"
```

**Expected Result:**
- Complete flow works seamlessly
- Dashboard embedded via reverse proxy
- Token injected server-side (not exposed to client)
- Token refresh scheduled proactively
- All components integrated correctly

**Verification:**
- ✅ Login and tenant selection work
- ✅ Dashboard embedding via iframe works
- ✅ Reverse proxy injects Authorization header
- ✅ Token never exposed to client JavaScript
- ✅ Token refresh scheduling works
- ✅ Logs show complete flow execution

**Status:** [ ] PASS [ ] FAIL

---

## Test Results Template

Use this template to record your test results:

```
===============================================
KYROS POC MANUAL TEST RESULTS
===============================================

Date: ________________
Tester: ________________
Environment: Local Docker Compose
Services Version: Latest (as of test date)

===============================================
TEST SUITE 1: AUTHENTICATION & TOKEN EXCHANGE
===============================================
Test 1.1: Mock Login - Valid User             [ ] PASS [ ] FAIL
Test 1.2: Mock Login - Invalid User           [ ] PASS [ ] FAIL
Test 1.3: Token Exchange - Valid Tenant       [ ] PASS [ ] FAIL
Test 1.4: Token Exchange - Unauthorized       [ ] PASS [ ] FAIL
Test 1.5: Decode and Verify JWT Claims        [ ] PASS [ ] FAIL

Suite 1 Overall: [ ] PASS [ ] FAIL
Notes: _________________________________________

===============================================
TEST SUITE 2: DATA API & TENANT ISOLATION
===============================================
Test 2.1: Fetch CLV Data - Acme               [ ] PASS [ ] FAIL
Test 2.2: Fetch Risk Data - Acme              [ ] PASS [ ] FAIL
Test 2.3: No Authorization Header             [ ] PASS [ ] FAIL
Test 2.4: Invalid Token                       [ ] PASS [ ] FAIL
Test 2.5: Expired Token                       [ ] PASS [ ] FAIL [ ] SKIP
Test 2.6: Beta Tenant Setup                   [ ] PASS [ ] FAIL
Test 2.7: Fetch Risk Data - Beta              [ ] PASS [ ] FAIL
Test 2.8: Beta CLV Access (Should Fail)       [ ] PASS [ ] FAIL

Suite 2 Overall: [ ] PASS [ ] FAIL
Notes: _________________________________________

===============================================
TEST SUITE 3: CLV DASHBOARD INTEGRATION
===============================================
Test 3.1: No Authentication                   [ ] PASS [ ] FAIL
Test 3.2: Valid Acme Token                    [ ] PASS [ ] FAIL
Test 3.3: Tenant Info Display                 [ ] PASS [ ] FAIL
Test 3.4: Data API Integration                [ ] PASS [ ] FAIL
Test 3.5: Invalid Token                       [ ] PASS [ ] FAIL
Test 3.6: Beta Token (Should Fail)            [ ] PASS [ ] FAIL
Test 3.7: Browser Test                        [ ] PASS [ ] FAIL [ ] SKIP

Suite 3 Overall: [ ] PASS [ ] FAIL
Notes: _________________________________________

===============================================
TEST SUITE 4: RISK DASHBOARD INTEGRATION
===============================================
Test 4.1: No Authentication                   [ ] PASS [ ] FAIL
Test 4.2: Valid Acme Token                    [ ] PASS [ ] FAIL
Test 4.3: Valid Beta Token                    [ ] PASS [ ] FAIL
Test 4.4: Data API Integration (Acme)         [ ] PASS [ ] FAIL
Test 4.5: Data API Integration (Beta)         [ ] PASS [ ] FAIL
Test 4.6: Pattern Consistency                 [ ] PASS [ ] FAIL

Suite 4 Overall: [ ] PASS [ ] FAIL
Notes: _________________________________________

===============================================
TEST SUITE 5: MULTI-TENANT ISOLATION (CRITICAL)
===============================================
Test 5.1: Concurrent Access                   [ ] PASS [ ] FAIL
Test 5.2: Concurrent Dashboard Access         [ ] PASS [ ] FAIL
Test 5.3: Data Comparison                     [ ] PASS [ ] FAIL

Suite 5 Overall: [ ] PASS [ ] FAIL
**CRITICAL: Must PASS before production**
Notes: _________________________________________

===============================================
TEST SUITE 6: ERROR HANDLING & SECURITY
===============================================
Test 6.1: Expired Token                       [ ] PASS [ ] FAIL [ ] SKIP
Test 6.2: Malformed Auth Header               [ ] PASS [ ] FAIL
Test 6.3: Token Tampering                     [ ] PASS [ ] FAIL
Test 6.4: Data API Connection Failure         [ ] PASS [ ] FAIL
Test 6.5: Missing Tenant ID                   [ ] PASS [ ] FAIL [ ] SKIP

Suite 6 Overall: [ ] PASS [ ] FAIL
Notes: _________________________________________

===============================================
TEST SUITE 7: END-TO-END INTEGRATION
===============================================
Test 7.1: Complete Flow - Acme User           [ ] PASS [ ] FAIL
Test 7.2: Complete Flow - Beta User           [ ] PASS [ ] FAIL
Test 7.3: Logging Verification                [ ] PASS [ ] FAIL

Suite 7 Overall: [ ] PASS [ ] FAIL
Notes: _________________________________________

===============================================
TEST SUITE 8: EPIC 5 - REVERSE PROXY & EMBEDDING
===============================================
Test 8.1: Reverse Proxy - Token Injection     [ ] PASS [ ] FAIL
Test 8.2: Reverse Proxy - Invalid Slug        [ ] PASS [ ] FAIL
Test 8.3: Reverse Proxy - Missing Token       [ ] PASS [ ] FAIL
Test 8.4: Reverse Proxy - Expired Token       [ ] PASS [ ] FAIL [ ] SKIP
Test 8.5: Reverse Proxy - Docker Networking   [ ] PASS [ ] FAIL
Test 8.6: Dashboard Embedding - Browser Test  [ ] PASS [ ] FAIL
Test 8.7: Dashboard Embedding - Navigation    [ ] PASS [ ] FAIL
Test 8.8: Dashboard Embedding - Validation    [ ] PASS [ ] FAIL
Test 8.9: Dashboard Embedding - Error States  [ ] PASS [ ] FAIL
Test 8.10: Token Refresh - Scheduling         [ ] PASS [ ] FAIL
Test 8.11: Token Refresh - Success            [ ] PASS [ ] FAIL [ ] SKIP
Test 8.12: Token Refresh - Failure            [ ] PASS [ ] FAIL
Test 8.13: Token Refresh - User Expiry        [ ] PASS [ ] FAIL [ ] SKIP
Test 8.14: Toast Notifications                [ ] PASS [ ] FAIL
Test 8.15: E2E Epic 5 Flow                    [ ] PASS [ ] FAIL

Suite 8 Overall: [ ] PASS [ ] FAIL
Notes: _________________________________________

===============================================
OVERALL TEST RESULTS
===============================================
Total Tests: 55
Tests Passed: ___
Tests Failed: ___
Tests Skipped: ___

Critical Tests Status:
  - Test 5.1 (Concurrent Access):       [ ] PASS [ ] FAIL
  - Test 5.2 (Concurrent Dashboards):   [ ] PASS [ ] FAIL
  - Test 5.3 (Data Comparison):         [ ] PASS [ ] FAIL

OVERALL VERDICT: [ ] PASS [ ] FAIL

BLOCKING ISSUES:
_________________________________________________
_________________________________________________

PRODUCTION READINESS:
[ ] READY    [ ] NOT READY

Sign-off: ________________  Date: ________________
```

---

## Troubleshooting

### Services Won't Start

**Symptom:** `docker-compose up` fails

**Solutions:**
```bash
# Check for port conflicts
lsof -i :3000  # Shell UI
lsof -i :8000  # API
lsof -i :8050  # CLV Dashboard
lsof -i :8051  # Risk Dashboard

# Kill conflicting processes
kill -9 <PID>

# Rebuild containers
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Database Not Seeded

**Symptom:** Authentication fails, users not found

**Solution:**
```bash
# Re-run seed script
python3 scripts/seed-database.py

# Verify records
sqlite3 data/tenant_metadata.db "SELECT COUNT(*) FROM users;"
# Should return: 3

# Restart API to pick up new database
docker-compose restart api
```

### JWT Token Invalid

**Symptom:** All authentication requests fail

**Solution:**
```bash
# Check JWT_SECRET_KEY consistency
echo $JWT_SECRET_KEY

# Verify it matches in docker-compose.yml (default key)
# Restart all services with consistent key
docker-compose down
export JWT_SECRET_KEY="kyros-poc-secret-key-CHANGE-IN-PRODUCTION-12345678"
docker-compose up -d
```

### Dashboard Returns 401

**Symptom:** Dashboard access fails even with valid token

**Solutions:**
```bash
# 1. Verify token format
echo $TENANT_TOKEN_ACME

# 2. Check Authorization header format
# Must be: "Bearer <token>"

# 3. Check dashboard logs
docker-compose logs dash-app-clv --tail=50
docker-compose logs dash-app-risk --tail=50

# 4. Verify shared-config is mounted
docker-compose exec dash-app-clv ls -la /app/packages/shared-config/
```

### No Data Returned

**Symptom:** Dashboard loads but shows "No data available"

**Solutions:**
```bash
# 1. Check API health
curl http://localhost:8000/health

# 2. Verify data API endpoint directly
curl http://localhost:8000/api/dashboards/risk-analysis/data \
  -H "Authorization: Bearer $TENANT_TOKEN_ACME"

# 3. Check tenant_id in token
echo $TENANT_TOKEN_ACME | cut -d'.' -f2 | base64 -d | jq

# 4. Check data loader implementation
docker-compose logs api | grep -i "loading data\|dashboard"
```

### Cross-Tenant Data Leakage Detected

**Symptom:** Test 5.x fails - wrong tenant_id in response

**CRITICAL - DO NOT PROCEED TO PRODUCTION**

**Investigation:**
```bash
# 1. Check thread-local storage implementation
grep -n "threading.local" apps/dash-app-*/auth_middleware.py

# 2. Verify JWT validation extracts correct tenant_id
docker-compose logs dash-app-risk | grep "tenant:"

# 3. Check data loader filtering
docker-compose logs api | grep "tenant_id"

# 4. Review auth_middleware.py for context storage
```

**Contact development team immediately if leakage detected.**

---

## Test Completion Checklist

After completing all tests:

- [ ] All critical tests (Suite 5) PASSED
- [ ] No cross-tenant data leakage detected
- [ ] JWT validation working correctly
- [ ] Both dashboards functional
- [ ] Error handling verified
- [ ] Logging comprehensive and accurate
- [ ] Test results documented
- [ ] Any failures investigated and documented
- [ ] Production readiness decision made

**Next Steps:**
- Review test results with team
- Address any failures or concerns
- Document production migration requirements
- Plan additional performance/load testing if needed

---

**End of Manual Test Guide**
