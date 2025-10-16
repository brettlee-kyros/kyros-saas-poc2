# Epic 3: Manual Test Plan
## Shell UI & Tenant Selection Flow

**Epic 3 Stories:**
- 3.1: Login Page with Mock Authentication
- 3.2: Authentication Context and Token Management
- 3.3: Tenant Selection Page
- 3.4: Dashboard Listing Page
- 3.5: JWT Debug Panel Component

---

## Prerequisites

### 1. Start Docker Services

```bash
cd /Users/brettlee/docker/kyros-dev/work/kyros-saas-poc

# Start all services
docker-compose up --build

# Verify services are running
docker-compose ps

# Expected output:
# - kyros-api (port 8000) - Running
# - kyros-shell-ui (port 3000) - Running
# - kyros-dash-clv (port 8050) - Running
# - kyros-dash-risk (port 8051) - Running
```

### 2. Verify API Health

```bash
# Check API health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"2025-10-15T..."}
```

### 3. Browser Setup

- **Browser**: Chrome, Firefox, or Safari (latest version)
- **Developer Tools**: Open (F12 or Cmd+Option+I)
- **Console Tab**: Monitor for errors
- **Network Tab**: Monitor API requests

---

## Test Scenario 1: Single-Tenant User (analyst@acme.com)

**Expected Flow:** Login → Auto-select Acme → Dashboard Listing

### Step 1.1: Access Login Page

1. Open browser: `http://localhost:3000`
2. **Expected**: Redirect to `http://localhost:3000/login`
3. **Expected**: Login page displays with:
   - "Welcome to Kyros" heading
   - Email input field with placeholder "analyst@acme.com"
   - "Log In" button
   - Blue suggestions box with 3 mock emails

**✓ Story 3.1 AC 1, 2, 3**

### Step 1.2: View Mock Email Suggestions

1. Click in email input field
2. **Expected**: Blue box shows:
   - analyst@acme.com
   - admin@acme.com
   - viewer@beta.com
3. Hover over emails
4. **Expected**: Background changes to lighter blue on hover

**✓ Story 3.1 AC 4**

### Step 1.3: Select Mock Email

1. Click "analyst@acme.com" button
2. **Expected**: Email populates in input field
3. **Expected**: Suggestions box closes

**✓ Story 3.1 AC 4**

### Step 1.4: Submit Login

1. Click "Log In" button
2. **Expected**: Button changes to "Authenticating..." with spinner
3. **Expected**: Form disabled during submission
4. **Network Tab**: POST request to `/api/auth/mock-login`
5. **Expected**: Response 200 with `access_token`
6. **Expected**: Redirect to `http://localhost:3000/`

**✓ Story 3.1 AC 5, 6, 9**

### Step 1.5: Verify Auth Context

1. **Console**: Check for no authentication errors
2. **Expected**: No redirect back to /login
3. **Expected**: User is authenticated

**✓ Story 3.2 AC 1, 4**

### Step 1.6: Auto-Select Single Tenant

1. **Expected**: Brief loading spinner "Loading your tenants..."
2. **Expected**: Automatic token exchange (no tenant selection UI shown)
3. **Network Tab**: GET request to `/api/me`
4. **Network Tab**: POST request to `/api/token/exchange`
5. **Expected**: Redirect to `http://localhost:3000/tenant/acme-corp`

**✓ Story 3.3 AC 1, 9**

### Step 1.7: View Dashboard Listing

1. **Expected**: Dashboard listing page displays
2. **Expected**: Breadcrumb shows: "Tenants / Acme Corporation"
3. **Expected**: Header shows "Dashboards"
4. **Expected**: Tenant switcher button shows "Acme Corporation"
5. **Expected**: 2 dashboard cards visible:
   - Customer Lifetime Value
   - Risk Analysis
6. **Expected**: Each card has:
   - Title
   - Description
   - Framework badge
   - "Open Dashboard" button

**✓ Story 3.4 AC 1, 2, 3, 4, 5**

### Step 1.8: View Debug Panel (Collapsed)

1. **Expected**: Top-right corner shows "🔍 Debug" button
2. **Expected**: Mini badge shows "Tenant"
3. Click "🔍 Debug" button
4. **Expected**: Panel expands smoothly

**✓ Story 3.5 AC 2, 3**

### Step 1.9: View Debug Panel (Expanded)

1. **Expected**: Panel shows:
   - "Token Type: Tenant-Scoped Token" (green badge)
   - "Token Expiry: ⏱️ 59m 45s" (countdown)
   - Decoded Claims (JSON format)
2. **Expected**: `tenant_id` line highlighted in green with "← Single tenant"
3. **Expected**: No `tenant_ids` array present
4. **Expected**: Claims show:
   - sub: (user ID)
   - email: analyst@acme.com
   - tenant_id: (single UUID)
   - role: viewer
   - exp, iat, iss

**✓ Story 3.5 AC 4, 5, 7, 9**

### Step 1.10: Verify Countdown Timer

1. Wait 5 seconds
2. **Expected**: Countdown decrements (e.g., 59m 45s → 59m 40s)
3. **Expected**: Updates every second

**✓ Story 3.5 AC 7**

### Step 1.11: Tenant Switcher

1. Click "Acme Corporation" tenant switcher button
2. **Expected**: Dropdown shows:
   - "Current Tenant" label
   - Acme Corporation (highlighted with blue border)
   - "Switch Tenant" button
3. Click "Switch Tenant"
4. **Expected**: Redirect to `http://localhost:3000/`
5. **Expected**: Tenant selection page shows Acme card

**✓ Story 3.4 AC 11**

### Step 1.12: Logout

1. Click "Logout" button (top-right, if visible on tenant selection)
2. **Expected**: Redirect to `http://localhost:3000/login`
3. **Expected**: Debug panel shows "🔒 No token available"

**✓ Story 3.2 AC 5**

---

## Test Scenario 2: Multi-Tenant User (admin@acme.com)

**Expected Flow:** Login → Tenant Selection UI → Manual Select → Dashboard Listing

### Step 2.1: Login as Multi-Tenant User

1. Navigate to `http://localhost:3000/login`
2. Click "admin@acme.com" suggestion
3. Click "Log In"
4. **Expected**: Redirect to `http://localhost:3000/`

**✓ Story 3.1 AC 4, 5, 6**

### Step 2.2: View Tenant Selection Page

1. **Expected**: Tenant selection page displays
2. **Expected**: Header shows "Select Your Tenant"
3. **Expected**: 2 tenant cards visible:
   - Acme Corporation
   - Beta Industries
4. **Expected**: Each card shows:
   - Tenant name
   - Description (if configured)
   - Slug
   - "Select Tenant" button
5. **Expected**: Branding color strip at top of each card

**✓ Story 3.3 AC 2, 3, 4**

### Step 2.3: View User Token in Debug Panel

1. Click "🔍 Debug" button
2. **Expected**: Panel shows:
   - "Token Type: User Access Token" (blue badge)
   - Countdown timer
3. **Expected**: `tenant_ids` line highlighted in blue with "← Multi-tenant"
4. **Expected**: `tenant_ids` shows array with 2 UUIDs:
   ```json
   "tenant_ids": [
     "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
     "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4"
   ]
   ```
5. **Expected**: No `tenant_id` (single value) present

**✓ Story 3.5 AC 6**

### Step 2.4: Select Acme Tenant

1. Click "Select Tenant" on Acme Corporation card
2. **Expected**: Button shows "Exchanging Token..." with spinner
3. **Network Tab**: POST request to `/api/token/exchange` with payload:
   ```json
   {"tenant_id": "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"}
   ```
4. **Expected**: Response 200 with new `access_token`
5. **Expected**: Redirect to `http://localhost:3000/tenant/acme-corp`

**✓ Story 3.3 AC 5, 6, 8**

### Step 2.5: Verify Token Exchange in Debug Panel

1. Click "🔍 Debug" button
2. **Expected**: Panel now shows:
   - "Token Type: Tenant-Scoped Token" (green badge - changed from blue!)
   - New countdown timer (reset)
3. **Expected**: `tenant_id` line highlighted (changed from `tenant_ids`)
4. **Expected**: Single `tenant_id` value (not array)
5. **Expected**: `role` claim now present

**✓ Story 3.5 AC 12 (token change reactivity)**

### Step 2.6: View Acme Dashboards

1. **Expected**: 2 dashboard cards:
   - Customer Lifetime Value
   - Risk Analysis

**✓ Story 3.4 AC 2, 4**

### Step 2.7: Switch to Beta Tenant

1. Click tenant switcher "Acme Corporation"
2. Click "Switch Tenant"
3. **Expected**: Return to tenant selection page
4. Click "Select Tenant" on Beta Industries card
5. **Expected**: Token exchange
6. **Expected**: Redirect to `http://localhost:3000/tenant/beta-industries`

**✓ Story 3.3 AC 8**

### Step 2.8: View Beta Dashboards

1. **Expected**: 1 dashboard card:
   - Risk Analysis (only)
2. **Expected**: NO Customer Lifetime Value card
3. **Expected**: Demonstrates tenant isolation

**✓ Story 3.4 AC 2 (tenant-filtered dashboards)**

---

## Test Scenario 3: Error Handling

### Step 3.1: Invalid Email Login

1. Navigate to `http://localhost:3000/login`
2. Type "invalid@test.com" in email field
3. Click "Log In"
4. **Expected**: Error message: "User not found. Try one of the suggested emails."
5. **Expected**: Red error box displayed

**✓ Story 3.1 AC 7**

### Step 3.2: Network Error Simulation

1. Stop Docker API service: `docker-compose stop api`
2. Refresh page or try to login
3. **Expected**: Error message: "Network error. Please check your connection and retry."
4. **Expected**: Red error box with retry option
5. Restart API: `docker-compose start api`

**✓ Story 3.1 AC 8**

### Step 3.3: Empty Email Validation

1. Navigate to `http://localhost:3000/login`
2. Leave email field empty
3. Click "Log In"
4. **Expected**: Error message: "Email is required"

**✓ Story 3.1 AC 11**

### Step 3.4: Invalid Email Format

1. Type "notanemail" in email field
2. Click "Log In"
3. **Expected**: Error message: "Invalid email format"

**✓ Story 3.1 AC 11**

### Step 3.5: No Dashboards (Simulated)

_This requires modifying database to remove dashboard assignments_

1. **Expected**: "No dashboards available for this tenant" message
2. **Expected**: Dashboard icon illustration
3. **Expected**: "Switch Tenant" button

**✓ Story 3.4 AC 8**

---

## Test Scenario 4: Navigation & Protected Routes

### Step 4.1: AuthGuard - Unauthenticated Access

1. Open new incognito/private window
2. Navigate to `http://localhost:3000/tenant/acme-corp`
3. **Expected**: Redirect to `http://localhost:3000/login`
4. **Expected**: Cannot access protected route without login

**✓ Story 3.2 AC 7, 8**

### Step 4.2: Token Persistence

1. Login as admin@acme.com
2. Select Acme tenant
3. Refresh page (F5)
4. **Expected**: Still on dashboard listing page (no redirect to login)
5. **Expected**: Token persisted in sessionStorage
6. **Expected**: Debug panel still shows tenant-scoped token

**✓ Story 3.2 AC 9**

### Step 4.3: Dashboard Navigation (Future)

1. Click "Open Dashboard" on any dashboard card
2. **Expected**: Navigate to `/tenant/[slug]/dashboard/[dashboard_slug]`
3. **Expected**: URL changes (page will be implemented in Epic 5)

**✓ Story 3.4 AC 7**

---

## Test Scenario 5: Debug Panel Visibility

### Step 5.1: Login Page (Hidden)

1. Navigate to `http://localhost:3000/login`
2. **Expected**: Debug panel NOT visible
3. **Expected**: No "🔍 Debug" button

**✓ Story 3.5 AC 11**

### Step 5.2: Tenant Selection (Visible)

1. Login and navigate to tenant selection
2. **Expected**: Debug panel visible with User Access Token
3. **Expected**: Shows tenant_ids array

**✓ Story 3.5 AC 11**

### Step 5.3: Dashboard Listing (Visible)

1. Select tenant and navigate to dashboard listing
2. **Expected**: Debug panel visible with Tenant-Scoped Token
3. **Expected**: Shows single tenant_id

**✓ Story 3.5 AC 11**

---

## Test Scenario 6: Expiry Testing

### Step 6.1: Token Expiry Countdown

1. Login and view debug panel
2. **Expected**: Countdown shows "59m XX s" (1 hour expiry)
3. Wait and observe countdown
4. **Expected**: Timer decrements every second
5. **Expected**: Format changes to "XXs" when under 1 minute

**✓ Story 3.5 AC 7**

### Step 6.2: Expired Token (Simulated)

_This requires waiting for token to expire or using a short expiry in backend_

1. Wait for token to expire (1 hour)
2. **Expected**: Debug panel shows "🔴 Expired" in red
3. Try to access protected resources
4. **Expected**: 401 errors in API calls

**✓ Story 3.5 AC 7**

---

## Acceptance Criteria Checklist

### Story 3.1: Login Page
- [x] AC 1: Login form with email and submit button
- [x] AC 2: Tailwind CSS styling
- [x] AC 3: Placeholder text "analyst@acme.com"
- [x] AC 4: Mock email suggestions (3 emails)
- [x] AC 5: POST /api/auth/mock-login
- [x] AC 6: Store token and redirect to home
- [x] AC 7: 404 error handling
- [x] AC 8: Network error handling
- [x] AC 9: Loading state with spinner
- [x] AC 10: TypeScript interfaces
- [x] AC 11: Client-side email validation
- [x] AC 12: Accessible at /login

### Story 3.2: Authentication Context
- [x] AC 1: Auth context with isAuthenticated, userToken, login(), logout()
- [x] AC 2: AuthProvider wraps root layout
- [x] AC 3: Token stored in React state
- [x] AC 4: login() stores token
- [x] AC 5: logout() clears token
- [x] AC 6: useAuth() hook
- [x] AC 7: AuthGuard component
- [x] AC 8: AuthGuard wraps protected routes
- [x] AC 9: Token persistence check on mount
- [x] AC 10: TypeScript types

### Story 3.3: Tenant Selection
- [x] AC 1: Fetches GET /api/me
- [x] AC 2: Multiple tenants display in grid
- [x] AC 3: Cards show name, description, button
- [x] AC 4: Branding colors from config_json
- [x] AC 5: POST /api/token/exchange on select
- [x] AC 6: Stores tenant-scoped token
- [x] AC 7: Zustand tenant store
- [x] AC 8: Redirects to /tenant/[slug]
- [x] AC 9: Auto-select for single tenant
- [x] AC 10: Loading states
- [x] AC 11: Error handling (403, 401)
- [x] AC 12: TypeScript interfaces

### Story 3.4: Dashboard Listing
- [x] AC 1: Dynamic route created
- [x] AC 2: Fetches dashboards with tenant token
- [x] AC 3: Tenant name in header
- [x] AC 4: Grid layout (2-3 columns)
- [x] AC 5: Cards show title, description, button
- [x] AC 6: Tailwind CSS styling
- [x] AC 7: Navigation to dashboard view
- [x] AC 8: Empty state message
- [x] AC 9: Loading state
- [x] AC 10: Error handling with retry
- [x] AC 11: Tenant switcher dropdown
- [x] AC 12: TypeScript interfaces

### Story 3.5: Debug Panel
- [x] AC 1: Component created
- [x] AC 2: Fixed top-right position
- [x] AC 3: Collapsed by default
- [x] AC 4: Shows token type, claims, countdown
- [x] AC 5: Highlights tenant_id (single)
- [x] AC 6: Highlights tenant_ids (array)
- [x] AC 7: Live countdown with expiry warning
- [x] AC 8: Tailwind CSS styling
- [x] AC 9: Uses jwt-decode library
- [x] AC 10: Handles missing/invalid tokens
- [x] AC 11: Visible on all authenticated pages
- [x] AC 12: Re-renders on token changes

---

## Test Results Template

```
Date: _____________
Tester: _____________
Environment: Docker (local)

Test Scenario 1 (analyst@acme.com): ☐ PASS ☐ FAIL
Test Scenario 2 (admin@acme.com): ☐ PASS ☐ FAIL
Test Scenario 3 (Error Handling): ☐ PASS ☐ FAIL
Test Scenario 4 (Navigation): ☐ PASS ☐ FAIL
Test Scenario 5 (Debug Panel): ☐ PASS ☐ FAIL
Test Scenario 6 (Expiry): ☐ PASS ☐ FAIL

Issues Found:
-
-

Notes:
-
-
```

---

## Troubleshooting

### Issue: Services won't start
**Solution:**
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Issue: API returns 500 errors
**Solution:** Check API logs:
```bash
docker-compose logs api
```

### Issue: Frontend shows blank page
**Solution:** Check browser console for errors and shell-ui logs:
```bash
docker-compose logs shell-ui
```

### Issue: Token not persisting
**Solution:** Check sessionStorage in browser dev tools:
- Application tab → Storage → Session Storage
- Should see `user_token` key

### Issue: Debug panel not showing
**Solution:**
- Check if on login page (intentionally hidden)
- Check browser console for errors
- Verify component imported in layout.tsx

---

## Success Criteria

Epic 3 is considered successfully tested when:

✅ All 6 test scenarios pass
✅ All 60 acceptance criteria validated
✅ No console errors during normal flow
✅ Token exchange visibly demonstrated in debug panel
✅ Single-tenant auto-select works
✅ Multi-tenant manual select works
✅ Dashboard isolation confirmed (Acme: 2, Beta: 1)
✅ Navigation flows smoothly
✅ Error states display appropriately
✅ Debug panel provides clear stakeholder visibility

**🎉 Epic 3 Complete!**
