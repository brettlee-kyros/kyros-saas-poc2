# Epic 3: Shell UI & Tenant Selection

**Epic Goal:** Build the Next.js Shell UI providing the authenticated user journey from login through tenant selection to dashboard listing, with debug panel visibility into JWT claims and token exchange.

## Story 3.1: Login Page with Mock Authentication

**As a** user,
**I want** a login page where I can enter my email to authenticate,
**so that** I can access the multi-tenant application.

**Acceptance Criteria:**

1. app/login/page.tsx created with login form containing email input field and submit button
2. Form styled with Tailwind CSS matching minimal branding guidelines
3. Email input includes placeholder text with example: "analyst@acme.com"
4. Form includes dropdown or clickable suggestions for the 3 mock user emails
5. On submit, form calls POST /api/auth/mock-login via fetch with {email} payload
6. On success, stores access_token in memory (React state or zustand store) and redirects to home page
7. On 404 error, displays error message: "User not found" below form
8. On network error, displays error message with retry option
9. Loading state shows spinner on submit button during API call
10. TypeScript interfaces defined for login request/response
11. Client-side validation ensures email format before submission
12. Page is accessible at /login route

## Story 3.2: Authentication Context and Token Management

**As a** Shell UI developer,
**I want** centralized auth state management with token storage,
**so that** authenticated state and tokens are accessible throughout the application.

**Acceptance Criteria:**

1. Auth context created with React Context API providing: {isAuthenticated, userToken, login(token), logout()}
2. Auth provider wraps root layout (app/layout.tsx)
3. User access token stored in React state (not localStorage for PoC simplicity)
4. login(token) function stores token and sets isAuthenticated = true
5. logout() function clears token and sets isAuthenticated = false
6. useAuth() hook provides access to auth context from any component
7. AuthGuard component created that redirects to /login if not authenticated
8. AuthGuard wraps protected routes (home page, tenant pages)
9. On app mount, auth context checks for existing token (future: could check /api/me)
10. TypeScript types defined for auth context interface

## Story 3.3: Tenant Selection Page

**As a** user,
**I want** to see a list of tenants I have access to and select one,
**so that** I can exchange my user token for a tenant-scoped token and proceed to dashboards.

**Acceptance Criteria:**

1. Home page (app/page.tsx) fetches GET /api/me on mount if authenticated
2. If user has multiple tenants, displays tenant selector grid/list with cards for each tenant
3. Each tenant card shows: tenant name, optional description from config_json, "Select" button
4. Tenant cards styled with Tailwind CSS, using branding colors from config_json if present
5. On "Select" button click, calls POST /api/token/exchange with {tenant_id}
6. On successful exchange, stores tenant-scoped token (replaces user token in auth context or separate tenant context)
7. Stores selected tenant metadata (id, name, slug) in zustand tenant store
8. Redirects to /tenant/[tenant_slug] route after successful exchange
9. If user has only one tenant, automatically triggers exchange and redirects (skips selection UI)
10. Loading state shown during tenant discovery and token exchange
11. Error handling for exchange failures (403, 401) with user-friendly messages
12. TypeScript interfaces for tenant data and exchange request/response

## Story 3.4: Dashboard Listing Page

**As a** user,
**I want** to view all dashboards available for my selected tenant,
**so that** I can choose which dashboard to open.

**Acceptance Criteria:**

1. app/tenant/[tenant_slug]/page.tsx created for dashboard listing
2. Page fetches GET /api/tenant/{tenant_id}/dashboards using tenant-scoped token on mount
3. Page displays tenant name in header/breadcrumb area
4. Dashboard cards displayed in grid layout (2-3 columns responsive)
5. Each card shows: dashboard title, description, thumbnail placeholder, "Open Dashboard" button
6. Cards styled with Tailwind CSS consistent with app theme
7. On "Open Dashboard" click, navigates to /tenant/[tenant_slug]/dashboard/[dashboard_slug]
8. If no dashboards assigned, displays message: "No dashboards available for this tenant"
9. Loading state shown while fetching dashboards
10. Error handling for API failures with retry option
11. Page includes tenant switcher dropdown in header (shows current tenant, allows switching back to selection)
12. TypeScript interfaces for dashboard list response

## Story 3.5: JWT Debug Panel Component

**As a** stakeholder,
**I want** a collapsible debug panel showing decoded JWT claims and expiry countdown,
**so that** I can visually verify the token exchange mechanism and tenant scoping.

**Acceptance Criteria:**

1. DebugPanel component created in components/dashboard/DebugPanel.tsx
2. Panel rendered in app header or fixed position (top-right corner)
3. Panel collapsed by default, toggle button shows "Debug" label or icon
4. When expanded, panel displays: Token Type (User/Tenant-Scoped), Decoded Claims (formatted JSON), Expiry Countdown (time remaining)
5. If tenant-scoped token active, highlights tenant_id claim and shows it's a single value (not array)
6. If user access token active, highlights tenant_ids claim showing array of UUIDs
7. Expiry countdown updates every second, shows "Expired" in red if token past expiration
8. Panel styled with Tailwind CSS, semi-transparent background, readable typography
9. Panel uses JWT decode library (e.g., jwt-decode) to parse token without validation
10. Panel handles missing/invalid tokens gracefully (shows "No token" message)
11. Panel visible on all authenticated pages (login page, tenant selection, dashboard listing, dashboard view)
12. Component re-renders when token changes (after login, after exchange)

---
