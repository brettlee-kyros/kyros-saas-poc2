# Epic 3: Shell UI & Tenant Selection - QA Test Script

**Epic Goal:** Build the Next.js Shell UI providing the authenticated user journey from login through tenant selection to dashboard listing, with debug panel visibility into JWT claims and token exchange.

**Test Date:** _____________
**Tester:** _____________
**Environment:** Local Docker Compose
**Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Complete | ⬜ Blocked

---

## Prerequisites

### Environment Setup
- [ ] Docker Desktop running
- [ ] All services started: `docker-compose up`
- [ ] API service healthy: `curl http://localhost:8000/health`
- [ ] Shell UI accessible: http://localhost:3000
- [ ] Browser DevTools open (Network + Console tabs)

### Test Data Verification
- [ ] Database seeded with 3 mock users
- [ ] Database seeded with 2 tenants (Acme, Beta)
- [ ] Database seeded with 2 dashboards (CLV, Risk Analysis)
- [ ] Dashboard assignments verified (Acme: 2, Beta: 1)

### Mock User Accounts
| Email | Tenants | Role | Use Case |
|-------|---------|------|----------|
| analyst@acme.com | 1 (Acme) | Viewer | Single-tenant auto-select |
| admin@acme.com | 2 (Acme, Beta) | Admin | Multi-tenant selection |
| viewer@beta.com | 1 (Beta) | Viewer | Single-tenant isolation |

---

## Test Execution Summary

| Story | Total Tests | Passed | Failed | Blocked | Notes |
|-------|-------------|--------|--------|---------|-------|
| 3.1 Login Page | 15 | | | | |
| 3.2 Auth Context | 12 | | | | |
| 3.3 Tenant Selection | 18 | | | | |
| 3.4 Dashboard Listing | 16 | | | | |
| 3.5 Debug Panel | 14 | | | | |
| Integration Tests | 10 | | | | |
| **TOTAL** | **85** | | | | |

---

# Story 3.1: Login Page with Mock Authentication

**Acceptance Criteria:** 12
**File:** apps/shell-ui/app/login/page.tsx:1

## Test Suite 3.1.1: Page Load and UI Elements

### TC-3.1.1 - Login Page Accessibility
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Navigate to http://localhost:3000/login
  2. Verify page loads successfully
- **Expected:**
  - Page accessible at /login route
  - No console errors
  - Page title: "Kyros PoC" or similar
- **Actual:** _____________________________________________
- **AC Covered:** AC 12

### TC-3.1.2 - Login Form UI Elements
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Inspect login page layout
  2. Verify all form elements present
- **Expected:**
  - Email input field visible
  - Placeholder text: "analyst@acme.com"
  - Submit button labeled "Log In"
  - 3 mock email suggestion buttons visible
  - Tailwind CSS styling applied (centered card, shadow)
- **Actual:** _____________________________________________
- **AC Covered:** AC 1, 2, 3, 4

### TC-3.1.3 - Mock Email Suggestions
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Click "analyst@acme.com" suggestion
  2. Verify email input populated
  3. Click "admin@acme.com" suggestion
  4. Verify email input updated
  5. Click "viewer@beta.com" suggestion
- **Expected:**
  - Each click populates email input with clicked email
  - Input value changes on each click
  - No form submission occurs
- **Actual:** _____________________________________________
- **AC Covered:** AC 4

## Test Suite 3.1.2: Successful Login Flow

### TC-3.1.4 - Valid Login (analyst@acme.com)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Enter email: analyst@acme.com
  2. Click "Log In"
  3. Observe network tab for API call
  4. Observe redirect behavior
- **Expected:**
  - POST /api/auth/mock-login called with {email: "analyst@acme.com"}
  - Response 200 with {access_token, token_type, expires_in}
  - Loading spinner shows during API call
  - Redirect to "/" (home page) after success
  - Token stored (check sessionStorage or React state)
- **Actual:** _____________________________________________
- **AC Covered:** AC 5, 6, 9

### TC-3.1.5 - Valid Login (admin@acme.com)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Return to /login (logout if needed)
  2. Enter email: admin@acme.com
  3. Click "Log In"
- **Expected:**
  - POST /api/auth/mock-login returns 200
  - Redirect to home page
  - Token stored
- **Actual:** _____________________________________________
- **AC Covered:** AC 5, 6

### TC-3.1.6 - Valid Login (viewer@beta.com)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Return to /login
  2. Enter email: viewer@beta.com
  3. Click "Log In"
- **Expected:**
  - POST /api/auth/mock-login returns 200
  - Redirect to home page
  - Token stored
- **Actual:** _____________________________________________
- **AC Covered:** AC 5, 6

## Test Suite 3.1.3: Error Handling

### TC-3.1.7 - Invalid User (404 Error)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Navigate to /login
  2. Enter email: invalid@test.com
  3. Click "Log In"
  4. Observe error display
- **Expected:**
  - POST /api/auth/mock-login returns 404
  - Error message displayed: "User not found"
  - Error appears below form with red styling
  - Form remains visible (no redirect)
  - Loading state clears
- **Actual:** _____________________________________________
- **AC Covered:** AC 7

### TC-3.1.8 - Network Error Handling
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Stop API service: `docker-compose stop api`
  2. Enter valid email
  3. Click "Log In"
  4. Observe error handling
- **Expected:**
  - Network error caught
  - Error message: "Network error. Please retry." or similar
  - Retry button or dismiss option shown
  - Form remains functional
- **Actual:** _____________________________________________
- **Notes:** Remember to restart API: `docker-compose start api`
- **AC Covered:** AC 8

### TC-3.1.9 - Retry After Network Error
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. After TC-3.1.8, restart API service
  2. Click retry button or re-submit form
  3. Observe success behavior
- **Expected:**
  - Error message clears
  - New API call succeeds
  - Login completes successfully
- **Actual:** _____________________________________________
- **AC Covered:** AC 8

## Test Suite 3.1.4: Form Validation

### TC-3.1.10 - Client-Side Email Validation (Invalid Format)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Navigate to /login
  2. Enter invalid email: "notanemail"
  3. Attempt to submit
- **Expected:**
  - HTML5 validation prevents submission OR
  - Custom validation shows error message
  - Submit button disabled or validation error shown
  - Red border or error text on input
- **Actual:** _____________________________________________
- **AC Covered:** AC 11

### TC-3.1.11 - Empty Email Validation
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Leave email field empty
  2. Attempt to submit
- **Expected:**
  - Submit button disabled OR
  - Required field validation prevents submission
  - Validation message shown
- **Actual:** _____________________________________________
- **AC Covered:** AC 11

## Test Suite 3.1.5: Loading States

### TC-3.1.12 - Loading Spinner Display
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Enter valid email
  2. Click "Log In"
  3. Observe button during API call (use Network throttling if needed)
- **Expected:**
  - Button text changes to "Logging in..." or similar
  - Spinner icon visible on button
  - Form inputs disabled during loading
  - Submit button disabled during loading
- **Actual:** _____________________________________________
- **AC Covered:** AC 9

## Test Suite 3.1.6: TypeScript Interfaces

### TC-3.1.13 - TypeScript Types Exist
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Check file exists: apps/shell-ui/types/auth.ts
  2. Verify interfaces defined
- **Expected:**
  - LoginRequest interface: {email: string}
  - LoginResponse interface: {access_token, token_type, expires_in}
  - ErrorResponse interface matches API error format
- **Actual:** _____________________________________________
- **AC Covered:** AC 10

## Test Suite 3.1.7: Responsive Design

### TC-3.1.14 - Mobile Responsiveness
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Resize browser to mobile width (375px)
  2. Verify layout adapts
- **Expected:**
  - Form remains usable
  - No horizontal scroll
  - Mock email suggestions wrap properly
  - Centered layout maintained
- **Actual:** _____________________________________________
- **AC Covered:** AC 2

### TC-3.1.15 - Tablet/Desktop Responsiveness
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Test at tablet (768px) and desktop (1024px+) widths
  2. Verify layout quality
- **Expected:**
  - Card maintains max-width constraint
  - Centered on screen
  - Proper spacing and typography
- **Actual:** _____________________________________________
- **AC Covered:** AC 2

---

# Story 3.2: Authentication Context and Token Management

**Acceptance Criteria:** 10
**File:** contexts/AuthContext.tsx:1

## Test Suite 3.2.1: Auth Context Functionality

### TC-3.2.1 - Auth Context Initialization
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Open DevTools Console
  2. Navigate to http://localhost:3000
  3. Check React DevTools for AuthProvider
- **Expected:**
  - AuthProvider wraps root layout
  - Initial state: isAuthenticated = false, userToken = null
  - No errors in console
- **Actual:** _____________________________________________
- **AC Covered:** AC 1, 2, 3

### TC-3.2.2 - login() Function Stores Token
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login with analyst@acme.com via /login page
  2. Check sessionStorage: `sessionStorage.getItem('user_token')`
  3. Check React state via DevTools
- **Expected:**
  - login(token) function called
  - userToken stored in React state
  - isAuthenticated = true
  - Token persisted to sessionStorage
- **Actual:** _____________________________________________
- **AC Covered:** AC 4

### TC-3.2.3 - logout() Function Clears Token
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. After successful login, click logout button
  2. Check sessionStorage and React state
- **Expected:**
  - logout() function called
  - userToken cleared (null)
  - isAuthenticated = false
  - Token removed from sessionStorage
  - Redirect to /login
- **Actual:** _____________________________________________
- **AC Covered:** AC 5

### TC-3.2.4 - useAuth() Hook Access
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Inspect home page component
  2. Verify useAuth() hook usage
- **Expected:**
  - useAuth() provides: {isAuthenticated, userToken, login, logout}
  - Hook accessible from any component
  - No errors when used within provider
- **Actual:** _____________________________________________
- **AC Covered:** AC 6

## Test Suite 3.2.2: AuthGuard Component

### TC-3.2.5 - AuthGuard Redirects Unauthenticated Users
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Ensure logged out (clear sessionStorage)
  2. Navigate directly to http://localhost:3000/
  3. Observe redirect behavior
- **Expected:**
  - AuthGuard detects isAuthenticated = false
  - Automatic redirect to /login
  - No flash of protected content
  - Login page displays
- **Actual:** _____________________________________________
- **AC Covered:** AC 7, 8

### TC-3.2.6 - AuthGuard Allows Authenticated Users
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login with valid user
  2. Verify home page access
  3. Try accessing protected routes
- **Expected:**
  - AuthGuard allows access
  - Home page content visible
  - No redirect to login
  - Protected content renders
- **Actual:** _____________________________________________
- **AC Covered:** AC 7, 8

### TC-3.2.7 - AuthGuard Wraps Protected Routes
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Verify home page uses AuthGuard
  2. Verify tenant routes use AuthGuard (after Story 3.3/3.4)
- **Expected:**
  - AuthGuard wraps: home page, tenant selection, dashboard listing
  - Login page NOT wrapped (publicly accessible)
- **Actual:** _____________________________________________
- **AC Covered:** AC 8

## Test Suite 3.2.3: Token Persistence

### TC-3.2.8 - Token Restoration on Page Reload
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login with valid user
  2. Refresh page (F5 or Cmd+R)
  3. Observe authentication state
- **Expected:**
  - On mount, AuthProvider checks sessionStorage
  - Token found and restored to React state
  - isAuthenticated = true
  - User remains logged in (no redirect to login)
- **Actual:** _____________________________________________
- **AC Covered:** AC 9

### TC-3.2.9 - Invalid Token Handling on Mount
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Manually set invalid token: `sessionStorage.setItem('user_token', 'invalid-token')`
  2. Refresh page
  3. Observe handling
- **Expected:**
  - Invalid token cleared from storage
  - isAuthenticated = false
  - Redirect to /login
  - Error logged to console (optional)
- **Actual:** _____________________________________________
- **AC Covered:** AC 9

### TC-3.2.10 - No Token on First Visit
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Clear all storage: `sessionStorage.clear()`
  2. Navigate to http://localhost:3000
- **Expected:**
  - No token found
  - isAuthenticated = false
  - Redirect to /login
  - No errors
- **Actual:** _____________________________________________
- **AC Covered:** AC 9

## Test Suite 3.2.4: TypeScript Types

### TC-3.2.11 - AuthContextType Interface Defined
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Check contexts/AuthContext.tsx
  2. Verify interface exports
- **Expected:**
  - AuthContextType interface: {isAuthenticated, userToken, login(), logout()}
  - Types exported for component use
  - No TypeScript errors in IDE
- **Actual:** _____________________________________________
- **AC Covered:** AC 10

## Test Suite 3.2.5: Integration with Story 3.1

### TC-3.2.12 - Login Page Uses Auth Context
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Review app/login/page.tsx
  2. Verify useAuth() import and usage
  3. Test login flow end-to-end
- **Expected:**
  - Login page imports useAuth()
  - On success, calls login(token) instead of sessionStorage.setItem()
  - Token properly stored via context
  - Redirect works via auth state
- **Actual:** _____________________________________________
- **AC Covered:** AC 4, 6

---

# Story 3.3: Tenant Selection Page

**Acceptance Criteria:** 12
**File:** app/page.tsx:1

## Test Suite 3.3.1: Tenant Discovery

### TC-3.3.1 - Fetch User Tenants on Mount
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login as admin@acme.com (2 tenants)
  2. Observe Network tab
  3. Check home page content
- **Expected:**
  - GET /api/me called on mount
  - Bearer token from auth context sent
  - Response: {user_id, email, tenants[]}
  - Loading state shown during fetch
- **Actual:** _____________________________________________
- **AC Covered:** AC 1, 10

### TC-3.3.2 - Display Multiple Tenant Cards
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. After successful /api/me fetch
  2. Inspect tenant selection UI
- **Expected:**
  - Tenant cards displayed in grid layout
  - 2 cards shown (Acme Corporation, Beta Industries)
  - Each card shows: tenant name, description, "Select" button
  - Grid is responsive (2-3 columns on desktop)
- **Actual:** _____________________________________________
- **AC Covered:** AC 2, 3, 4

### TC-3.3.3 - Tenant Branding Colors Applied
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Inspect tenant cards
  2. Check for branding color application
- **Expected:**
  - Branding colors from config_json.branding.primary_color applied
  - Visual differentiation between tenants
  - Colors applied as border, accent, or background
- **Actual:** _____________________________________________
- **AC Covered:** AC 4

## Test Suite 3.3.2: Token Exchange

### TC-3.3.4 - Manual Tenant Selection (Multi-Tenant User)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. As admin@acme.com, click "Select" on Acme Corporation
  2. Observe Network tab
  3. Check redirect
- **Expected:**
  - POST /api/token/exchange called with {tenant_id: "acme-uuid"}
  - Bearer token (user token) sent in Authorization header
  - Response 200: {access_token, token_type, expires_in}
  - Tenant-scoped token stored separately from user token
  - Redirect to /tenant/acme
- **Actual:** _____________________________________________
- **AC Covered:** AC 5, 6, 8

### TC-3.3.5 - Tenant Metadata Storage
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. After tenant selection
  2. Check zustand store (React DevTools)
- **Expected:**
  - selectedTenant stored: {id, name, slug}
  - tenantToken stored (tenant-scoped JWT)
  - Store accessible from other components
- **Actual:** _____________________________________________
- **AC Covered:** AC 7

### TC-3.3.6 - Select Different Tenant
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Navigate back to home (/) or click tenant switcher
  2. Select Beta Industries
  3. Observe token exchange and redirect
- **Expected:**
  - POST /api/token/exchange with Beta tenant_id
  - New tenant-scoped token returned
  - Zustand store updated with Beta tenant metadata
  - Redirect to /tenant/beta
- **Actual:** _____________________________________________
- **AC Covered:** AC 5, 6, 7, 8

## Test Suite 3.3.3: Auto-Select for Single Tenant

### TC-3.3.7 - Auto-Select Single Tenant (analyst@acme.com)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Logout and login as analyst@acme.com
  2. Observe home page behavior
- **Expected:**
  - GET /api/me returns 1 tenant (Acme)
  - Tenant selection UI NOT shown
  - POST /api/token/exchange automatically called
  - Immediate redirect to /tenant/acme
  - No manual selection required
- **Actual:** _____________________________________________
- **AC Covered:** AC 9, 10

### TC-3.3.8 - Auto-Select Single Tenant (viewer@beta.com)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Logout and login as viewer@beta.com
  2. Observe auto-select behavior
- **Expected:**
  - GET /api/me returns 1 tenant (Beta)
  - Automatic token exchange
  - Redirect to /tenant/beta
- **Actual:** _____________________________________________
- **AC Covered:** AC 9

## Test Suite 3.3.4: Error Handling

### TC-3.3.9 - Token Exchange 403 (Access Denied)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. (Requires API modification or expired token)
  2. Trigger 403 response from /api/token/exchange
  3. Observe error handling
- **Expected:**
  - Error message displayed: "Access denied" or similar
  - User-friendly message shown
  - Tenant selection UI remains visible
  - Logout option provided
- **Actual:** _____________________________________________
- **AC Covered:** AC 11

### TC-3.3.10 - Token Exchange 401 (Invalid Token)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Manually corrupt user token in sessionStorage
  2. Attempt tenant selection
  3. Observe error handling
- **Expected:**
  - 401 response from API
  - Error message: "Invalid token" or "Please log in again"
  - Redirect to login page or logout prompt
- **Actual:** _____________________________________________
- **AC Covered:** AC 11

### TC-3.3.11 - Network Error During Exchange
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Stop API service during tenant selection
  2. Click "Select" button
  3. Observe error handling
- **Expected:**
  - Network error caught
  - User-friendly error message
  - Retry option provided
  - Tenant selection UI remains functional
- **Actual:** _____________________________________________
- **AC Covered:** AC 11

### TC-3.3.12 - No Tenants Assigned (Edge Case)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. (Requires test user with no tenants - may need DB modification)
  2. Login with zero-tenant user
  3. Observe handling
- **Expected:**
  - GET /api/me returns empty tenants array
  - Message: "No tenants available" or similar
  - Logout option provided
  - No errors thrown
- **Actual:** _____________________________________________
- **AC Covered:** AC 11

## Test Suite 3.3.5: Loading States

### TC-3.3.13 - Loading State During Tenant Discovery
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login and observe home page load
  2. Use Network throttling to slow request
- **Expected:**
  - Loading spinner shown during GET /api/me
  - Loading message: "Loading tenants..." or similar
  - No content flash before loading
- **Actual:** _____________________________________________
- **AC Covered:** AC 10

### TC-3.3.14 - Loading State During Token Exchange
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. As admin@acme.com, click "Select" button
  2. Observe button state during exchange
- **Expected:**
  - "Select" button shows loading spinner
  - Button disabled during exchange
  - Other tenant cards remain interactive (or all disabled)
  - Loading clears on success/error
- **Actual:** _____________________________________________
- **AC Covered:** AC 10

## Test Suite 3.3.6: TypeScript Interfaces

### TC-3.3.15 - Tenant TypeScript Interfaces
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Check types/tenant.ts file
  2. Verify interface definitions
- **Expected:**
  - Tenant interface: {tenant_id, name, slug, config_json}
  - TokenExchangeRequest: {tenant_id}
  - TokenExchangeResponse: {access_token, token_type, expires_in}
  - Types exported for component use
- **Actual:** _____________________________________________
- **AC Covered:** AC 12

## Test Suite 3.3.7: Zustand Store

### TC-3.3.16 - Tenant Store Creation
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Check stores/useTenantStore.ts file
  2. Verify store structure
- **Expected:**
  - Zustand store created
  - State: selectedTenant, tenantToken
  - Actions: setSelectedTenant(), setTenantToken(), clearTenant()
  - useTenantStore hook exported
- **Actual:** _____________________________________________
- **AC Covered:** AC 7

### TC-3.3.17 - Zustand Package Installed
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Check apps/shell-ui/package.json
  2. Verify zustand dependency
- **Expected:**
  - zustand@^4.5.0 in dependencies
  - Package installed in node_modules
- **Actual:** _____________________________________________
- **AC Covered:** AC 7

## Test Suite 3.3.8: Responsive Design

### TC-3.3.18 - Tenant Grid Responsiveness
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. As admin@acme.com, view tenant selection
  2. Resize browser: mobile (375px), tablet (768px), desktop (1024px+)
- **Expected:**
  - Mobile: 1 column grid
  - Tablet: 2 column grid
  - Desktop: 2-3 column grid
  - Cards scale appropriately
  - No horizontal scroll
- **Actual:** _____________________________________________
- **AC Covered:** AC 2, 4

---

# Story 3.4: Dashboard Listing Page

**Acceptance Criteria:** 12
**File:** app/tenant/[tenant_slug]/page.tsx:1

## Test Suite 3.4.1: Page Access and Setup

### TC-3.4.1 - Dynamic Route Accessibility
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Complete tenant selection (any user)
  2. Verify redirect to /tenant/[slug]
  3. Check URL matches tenant slug
- **Expected:**
  - Dynamic route created: /tenant/[tenant_slug]/page.tsx
  - URL: http://localhost:3000/tenant/acme OR /tenant/beta
  - Page loads successfully
  - No 404 errors
- **Actual:** _____________________________________________
- **AC Covered:** AC 1

### TC-3.4.2 - AuthGuard Protection
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Logout
  2. Navigate directly to http://localhost:3000/tenant/acme
- **Expected:**
  - AuthGuard redirects to /login
  - Protected route not accessible when unauthenticated
- **Actual:** _____________________________________________
- **AC Covered:** AC 1, 8

## Test Suite 3.4.2: Dashboard Fetch

### TC-3.4.3 - Fetch Dashboards with Tenant Token (Acme)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login as analyst@acme.com
  2. Complete tenant selection (auto-select to Acme)
  3. Observe Network tab on dashboard listing page
- **Expected:**
  - GET /api/tenant/{acme-uuid}/dashboards called
  - Bearer token: tenant-scoped token (NOT user token)
  - Response 200: {tenant_id, tenant_name, dashboards[]}
  - 2 dashboards returned: Customer Lifetime Value, Risk Analysis
  - Loading state shown during fetch
- **Actual:** _____________________________________________
- **AC Covered:** AC 2, 9

### TC-3.4.4 - Fetch Dashboards (Beta)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login as viewer@beta.com
  2. View dashboard listing
- **Expected:**
  - GET /api/tenant/{beta-uuid}/dashboards called
  - 1 dashboard returned: Risk Analysis
  - Demonstrates tenant isolation (Beta doesn't see Acme's CLV dashboard)
- **Actual:** _____________________________________________
- **AC Covered:** AC 2

## Test Suite 3.4.3: Tenant Header

### TC-3.4.5 - Display Tenant Name
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. View dashboard listing page
  2. Inspect header/breadcrumb area
- **Expected:**
  - Tenant name displayed: "Acme Corporation" or "Beta Industries"
  - Breadcrumb navigation visible
  - Clear visual hierarchy
- **Actual:** _____________________________________________
- **AC Covered:** AC 3

### TC-3.4.6 - Tenant Switcher Dropdown
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login as admin@acme.com (multi-tenant user)
  2. Select Acme tenant
  3. View dashboard listing
  4. Locate tenant switcher in header
- **Expected:**
  - Tenant switcher dropdown visible
  - Current tenant highlighted
  - "Switch Tenant" button or link present
  - Click redirects back to home (/) for tenant selection
- **Actual:** _____________________________________________
- **AC Covered:** AC 11

### TC-3.4.7 - Tenant Switcher Navigation
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Click "Switch Tenant" button
  2. Observe navigation
- **Expected:**
  - Redirect to home page (/)
  - Tenant selection UI displayed
  - Can select different tenant
- **Actual:** _____________________________________________
- **AC Covered:** AC 11

## Test Suite 3.4.4: Dashboard Grid Layout

### TC-3.4.8 - Dashboard Cards Display (Acme - 2 Dashboards)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. As analyst@acme.com, view dashboard listing
  2. Inspect dashboard cards
- **Expected:**
  - 2 dashboard cards displayed in grid
  - Grid layout: 2-3 columns (responsive)
  - Each card shows: title, description, thumbnail/icon, button
  - Tailwind CSS styling applied
  - Consistent with app theme
- **Actual:** _____________________________________________
- **AC Covered:** AC 4, 5, 6

### TC-3.4.9 - Dashboard Card Content
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Inspect individual dashboard card
  2. Verify all required elements
- **Expected:**
  - Dashboard title: "Customer Lifetime Value" / "Risk Analysis"
  - Description text visible
  - Thumbnail placeholder (icon, gradient, or image)
  - "Open Dashboard" button present
  - Framework indicator (Dash/Streamlit emoji or text)
- **Actual:** _____________________________________________
- **AC Covered:** AC 5

### TC-3.4.10 - Dashboard Cards Display (Beta - 1 Dashboard)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login as viewer@beta.com
  2. View dashboard listing
- **Expected:**
  - 1 dashboard card displayed: "Risk Analysis"
  - Same card styling as Acme
  - Demonstrates tenant-specific dashboard assignments
- **Actual:** _____________________________________________
- **AC Covered:** AC 4, 5, 6

## Test Suite 3.4.5: Dashboard Navigation

### TC-3.4.11 - Navigate to Dashboard View
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Click "Open Dashboard" on any card
  2. Observe navigation
- **Expected:**
  - Navigate to /tenant/[tenant_slug]/dashboard/[dashboard_slug]
  - Example: /tenant/acme/dashboard/customer-lifetime-value
  - Dashboard slug from card data
  - Next.js router.push() used
- **Actual:** _____________________________________________
- **Notes:** Dashboard view page may not exist yet (Epic 5)
- **AC Covered:** AC 7

### TC-3.4.12 - Dashboard Navigation for All Cards
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. As admin@acme.com, test both Acme dashboards
  2. Return and test Beta dashboard
- **Expected:**
  - "Open Dashboard" button works for all cards
  - Correct slug used in URL for each
  - Navigation consistent across tenants
- **Actual:** _____________________________________________
- **AC Covered:** AC 7

## Test Suite 3.4.6: Empty State

### TC-3.4.13 - No Dashboards Assigned (Edge Case)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. (Requires test tenant with no dashboards - may need DB modification)
  2. Select tenant with zero dashboards
  3. View dashboard listing
- **Expected:**
  - Message displayed: "No dashboards available for this tenant"
  - Centered message with icon
  - "Switch Tenant" or "Contact Admin" option
  - No empty grid or errors
- **Actual:** _____________________________________________
- **AC Covered:** AC 8

## Test Suite 3.4.7: Error Handling

### TC-3.4.14 - API Error (401/403)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. (Manually corrupt tenant token OR wait for expiry)
  2. Navigate to dashboard listing
  3. Observe error handling
- **Expected:**
  - API returns 401 or 403
  - Error message displayed with icon
  - Retry button provided
  - "Switch Tenant" or "Logout" option
  - User-friendly error text
- **Actual:** _____________________________________________
- **AC Covered:** AC 10

### TC-3.4.15 - Retry After Error
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. After error state (TC-3.4.14)
  2. Fix issue (refresh token, restart API)
  3. Click retry button
- **Expected:**
  - Page reloads or re-fetches dashboards
  - Error clears on success
  - Dashboard grid displays correctly
- **Actual:** _____________________________________________
- **AC Covered:** AC 10

## Test Suite 3.4.8: TypeScript Interfaces

### TC-3.4.16 - Dashboard TypeScript Interfaces
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Check types/dashboard.ts file
  2. Verify interface definitions
- **Expected:**
  - Dashboard interface: {dashboard_id, name, slug, description, framework, entry_point, config_json}
  - DashboardListResponse: {tenant_id, tenant_name, dashboards[]}
  - Types exported and used in component
- **Actual:** _____________________________________________
- **AC Covered:** AC 12

---

# Story 3.5: JWT Debug Panel Component

**Acceptance Criteria:** 12
**File:** components/dashboard/DebugPanel.tsx:1

## Test Suite 3.5.1: Debug Panel Visibility

### TC-3.5.1 - Debug Panel Present on All Auth Pages
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login and navigate through: home (/), tenant listing (/tenant/acme)
  2. Check for debug panel on each page
- **Expected:**
  - Debug panel visible on all authenticated pages
  - Fixed position (top-right corner)
  - NOT visible on login page
  - Z-index keeps panel on top
- **Actual:** _____________________________________________
- **AC Covered:** AC 2, 11

### TC-3.5.2 - Debug Panel Toggle Button
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Locate debug panel toggle button
  2. Verify initial state
- **Expected:**
  - Toggle button shows "Debug" label or icon
  - Panel collapsed by default
  - Button visible and clickable
  - Clear visual indicator
- **Actual:** _____________________________________________
- **AC Covered:** AC 3

### TC-3.5.3 - Expand/Collapse Functionality
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Click debug panel toggle
  2. Verify expansion
  3. Click again to collapse
- **Expected:**
  - Panel expands smoothly (animation)
  - Panel content visible when expanded
  - Panel collapses to button when closed
  - Toggle state persists during navigation (optional)
- **Actual:** _____________________________________________
- **AC Covered:** AC 3

## Test Suite 3.5.2: JWT Decoding

### TC-3.5.4 - JWT Decode Library Installed
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Check apps/shell-ui/package.json
  2. Check component imports
- **Expected:**
  - jwt-decode@^4.0.0 in dependencies
  - Library imported in DebugPanel component
  - No TypeScript errors
- **Actual:** _____________________________________________
- **AC Covered:** AC 9

### TC-3.5.5 - Decode User Access Token
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login as admin@acme.com
  2. On home page (before tenant selection), open debug panel
  3. Inspect decoded claims
- **Expected:**
  - Panel displays: "User Access Token" label
  - Decoded claims shown as formatted JSON
  - Claims include: sub, email, tenant_ids (array), iat, exp, iss
  - tenant_ids highlighted with "← Multi-tenant" annotation
  - No validation errors (library doesn't validate, just decodes)
- **Actual:** _____________________________________________
- **AC Covered:** AC 4, 6, 9

### TC-3.5.6 - Decode Tenant-Scoped Token
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Complete tenant selection (select Acme)
  2. On dashboard listing page, open debug panel
  3. Inspect decoded claims
- **Expected:**
  - Panel displays: "Tenant-Scoped Token" label
  - Decoded claims shown
  - Claims include: sub, email, tenant_id (single value), role, iat, exp, iss
  - tenant_id highlighted with "← Single tenant" annotation
  - Shows it's NOT an array
- **Actual:** _____________________________________________
- **AC Covered:** AC 4, 5, 9

## Test Suite 3.5.3: Token Type Detection

### TC-3.5.7 - Identify User Token vs Tenant Token
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Open debug panel on home page (user token)
  2. Note token type label
  3. Select tenant and navigate to dashboard listing
  4. Open debug panel (tenant token)
  5. Note token type label change
- **Expected:**
  - Before exchange: "User Access Token" (Blue badge/label)
  - After exchange: "Tenant-Scoped Token" (Green badge/label)
  - Clear visual differentiation
  - Token type detection logic: checks for tenant_ids vs tenant_id
- **Actual:** _____________________________________________
- **AC Covered:** AC 5, 6

### TC-3.5.8 - Highlight tenant_ids Array
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. View user token claims (admin@acme.com before tenant selection)
  2. Inspect tenant_ids claim rendering
- **Expected:**
  - tenant_ids displayed as array with UUIDs
  - Array format: ["uuid1", "uuid2"]
  - Highlighted with blue border or background
  - Annotation: "← Multi-tenant" or similar
- **Actual:** _____________________________________________
- **AC Covered:** AC 6

### TC-3.5.9 - Highlight tenant_id Single Value
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. View tenant-scoped token claims (after tenant selection)
  2. Inspect tenant_id claim rendering
- **Expected:**
  - tenant_id displayed as single string UUID
  - NOT an array
  - Highlighted with green border or background
  - Annotation: "← Single tenant" or similar
- **Actual:** _____________________________________________
- **AC Covered:** AC 5

## Test Suite 3.5.4: Expiry Countdown

### TC-3.5.10 - Display Token Expiry Countdown
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login and open debug panel
  2. Observe expiry countdown
  3. Wait for countdown to update
- **Expected:**
  - Expiry countdown displayed: "Expires in: 59m 23s" or similar
  - Countdown updates every second
  - Format: minutes and seconds OR seconds only if < 1 minute
  - Countdown reflects exp claim from token (1 hour = 3600s)
- **Actual:** _____________________________________________
- **AC Covered:** AC 4, 7

### TC-3.5.11 - Expired Token Display
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. (Wait for token to expire OR manually set exp to past timestamp)
  2. Open debug panel
  3. Check expiry display
- **Expected:**
  - Expiry text: "Expired" in red
  - Clear visual indicator (red color, icon)
  - Countdown stopped
  - Suggests logout or token refresh
- **Actual:** _____________________________________________
- **AC Covered:** AC 7

### TC-3.5.12 - Countdown Updates on Token Change
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Open debug panel with user token
  2. Note expiry time
  3. Select tenant (triggers new token)
  4. Observe countdown reset
- **Expected:**
  - Countdown timer resets for new token
  - New exp claim from tenant-scoped token
  - Timer continues updating
  - No stale countdown data
- **Actual:** _____________________________________________
- **AC Covered:** AC 12

## Test Suite 3.5.5: Error Handling

### TC-3.5.13 - No Token Available
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Logout (clear tokens)
  2. Navigate to login page (if debug panel visible there)
  3. Open debug panel
- **Expected:**
  - Message: "No token available" or similar
  - Gray/muted styling
  - No errors thrown
  - Helpful text (e.g., "Please log in")
- **Actual:** _____________________________________________
- **AC Covered:** AC 10

### TC-3.5.14 - Invalid Token Format
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Manually set invalid token: `sessionStorage.setItem('user_token', 'not-a-jwt')`
  2. Refresh page
  3. Open debug panel
- **Expected:**
  - Message: "Invalid token format" or similar
  - Red/warning styling
  - No app crash
  - Error logged to console
- **Actual:** _____________________________________________
- **AC Covered:** AC 10

## Test Suite 3.5.6: Styling

### TC-3.5.15 - Panel Styling and Readability
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Open debug panel
  2. Inspect visual design
- **Expected:**
  - Semi-transparent dark background (bg-gray-900 opacity-95)
  - White text for readability
  - Monospace font for JSON claims
  - Proper spacing and padding
  - Responsive sizing (max-width, max-height)
  - Scrollable if content overflows
- **Actual:** _____________________________________________
- **AC Covered:** AC 8

### TC-3.5.16 - Panel Does Not Interfere with Content
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Open debug panel on various pages
  2. Interact with page content
- **Expected:**
  - Fixed position doesn't block important UI
  - Collapsible to minimize space
  - High z-index keeps panel on top
  - Doesn't break page layout
- **Actual:** _____________________________________________
- **AC Covered:** AC 2

---

# Integration Tests

**Purpose:** Test cross-story functionality and full user journeys

## Test Suite INT.1: Complete User Journey (Single-Tenant)

### TC-INT.1 - Full Flow: analyst@acme.com
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Navigate to http://localhost:3000
  2. Redirected to /login
  3. Login with analyst@acme.com
  4. Auto-select to Acme tenant
  5. View 2 dashboards
  6. Open debug panel at each step
- **Expected:**
  - Story 3.1: Successful login
  - Story 3.2: Auth context stores token
  - Story 3.3: Auto-select (single tenant)
  - Story 3.4: Dashboard listing shows 2 cards
  - Story 3.5: Debug panel shows user token → tenant token transition
  - No errors in console
  - All pages render correctly
- **Actual:** _____________________________________________
- **Stories:** 3.1, 3.2, 3.3, 3.4, 3.5

## Test Suite INT.2: Complete User Journey (Multi-Tenant)

### TC-INT.2 - Full Flow: admin@acme.com (Select Acme)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login as admin@acme.com
  2. See 2 tenant cards
  3. Select Acme Corporation
  4. View dashboard listing (2 dashboards)
  5. Monitor debug panel throughout
- **Expected:**
  - Tenant selection UI shown (not auto-select)
  - Manual tenant selection works
  - Token exchange completes
  - Debug panel shows tenant_ids array → tenant_id single value
  - Dashboard listing specific to Acme
- **Actual:** _____________________________________________
- **Stories:** 3.1, 3.2, 3.3, 3.4, 3.5

### TC-INT.3 - Full Flow: admin@acme.com (Select Beta)
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login as admin@acme.com
  2. Select Beta Industries
  3. View dashboard listing (1 dashboard)
- **Expected:**
  - Token exchange for Beta tenant
  - Dashboard listing shows only 1 dashboard (Risk Analysis)
  - Demonstrates tenant isolation
  - Acme's CLV dashboard NOT visible
- **Actual:** _____________________________________________
- **Stories:** 3.3, 3.4

### TC-INT.4 - Tenant Switching
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. As admin@acme.com, select Acme
  2. View dashboards (2 cards)
  3. Click "Switch Tenant"
  4. Select Beta Industries
  5. View dashboards (1 card)
- **Expected:**
  - Can switch between tenants
  - Each tenant shows correct dashboards
  - Token exchange occurs for each switch
  - Debug panel updates with new token
- **Actual:** _____________________________________________
- **Stories:** 3.3, 3.4, 3.5

## Test Suite INT.3: Debug Panel Token Visualization

### TC-INT.5 - Token Exchange Visualization
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login as admin@acme.com
  2. Open debug panel on home (tenant selection)
  3. Note token type and tenant_ids
  4. Select Acme tenant
  5. Open debug panel on dashboard listing
  6. Compare token claims
- **Expected:**
  - **Before exchange:**
    - Token type: "User Access Token"
    - Claims show tenant_ids: ["acme-uuid", "beta-uuid"]
  - **After exchange:**
    - Token type: "Tenant-Scoped Token"
    - Claims show tenant_id: "acme-uuid" (single value)
    - Claims show role: "admin"
  - **Visual proof** of token scoping mechanism
- **Actual:** _____________________________________________
- **Stories:** 3.3, 3.5

### TC-INT.6 - Expiry Countdown Through Flow
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login and immediately check expiry countdown
  2. Complete tenant selection
  3. Check expiry countdown on dashboard listing
- **Expected:**
  - User token expiry: ~1 hour from login
  - Tenant token expiry: ~30 minutes from exchange (or 1 hour - verify API)
  - Countdown updates continuously
  - New countdown after token exchange
- **Actual:** _____________________________________________
- **Stories:** 3.5

## Test Suite INT.4: AuthGuard Protection

### TC-INT.7 - Protected Routes Redirect Unauthenticated
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Ensure logged out
  2. Navigate to: /, /tenant/acme, /tenant/beta
  3. Verify redirects
- **Expected:**
  - All protected routes redirect to /login
  - Login page publicly accessible
  - No flash of protected content
- **Actual:** _____________________________________________
- **Stories:** 3.2

### TC-INT.8 - Logout and Re-login
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Complete full login flow
  2. Click logout button
  3. Verify logout behavior
  4. Login again
- **Expected:**
  - Logout clears all tokens (user + tenant)
  - Redirect to login
  - sessionStorage cleared
  - Re-login works as expected
  - No stale data from previous session
- **Actual:** _____________________________________________
- **Stories:** 3.1, 3.2, 3.3

## Test Suite INT.5: Token Persistence

### TC-INT.9 - Page Reload Maintains Auth State
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. Login and complete tenant selection
  2. On dashboard listing page, refresh (F5)
  3. Observe state restoration
- **Expected:**
  - Auth state restored from sessionStorage
  - Tenant selection restored from zustand (if persisted)
  - User remains on dashboard listing page OR redirected to home
  - No forced logout
  - Tokens available
- **Actual:** _____________________________________________
- **Stories:** 3.2, 3.3

### TC-INT.10 - Token Expiry Handling
- [ ] **PASS** | [ ] **FAIL** | [ ] **BLOCKED**
- **Steps:**
  1. (Wait for token expiry OR manually set exp to past)
  2. Attempt to fetch dashboards with expired token
  3. Observe API error handling
- **Expected:**
  - API returns 401 (Unauthorized)
  - Error message displayed
  - User prompted to re-login
  - Debug panel shows "Expired" in red
  - Graceful degradation (no app crash)
- **Actual:** _____________________________________________
- **Stories:** 3.2, 3.4, 3.5

---

# Environment Cleanup

## Post-Test Cleanup
- [ ] Stop Docker services: `docker-compose down`
- [ ] Clear browser storage: sessionStorage, localStorage
- [ ] Clear browser cache and cookies
- [ ] Close all test browser tabs
- [ ] Archive test results and screenshots

---

# Test Results Summary

**Total Tests Executed:** ____ / 85
**Passed:** ____
**Failed:** ____
**Blocked:** ____
**Pass Rate:** ____%

## Critical Issues Found
_(List P0/P1 issues that block release)_

1.
2.
3.

## Non-Critical Issues Found
_(List P2/P3 issues for future fixes)_

1.
2.
3.

## Test Environment Issues
_(Issues with test setup, not application bugs)_

1.
2.

## Recommendations

### Immediate Actions Required
- [ ]
- [ ]
- [ ]

### Follow-Up Testing Needed
- [ ]
- [ ]

### Documentation Updates
- [ ] Update story QA Results sections
- [ ] File GitHub issues for bugs found
- [ ] Update test data if needed

---

## Sign-Off

**Tester Name:** _____________
**Date Completed:** _____________
**Signature:** _____________

**PO Review:** _____________
**Date:** _____________

**Notes:**

