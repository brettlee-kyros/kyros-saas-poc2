# Epic 5: Reverse Proxy & Dashboard Embedding

**Epic Goal:** Implement Next.js API routes as reverse proxy to inject Authorization headers when embedding Dash applications in Shell UI, complete the end-to-end flow, and handle token expiry gracefully.

## Story 5.1: Next.js Reverse Proxy API Route with Header Injection

**As a** Shell UI developer,
**I want** Next.js API routes that proxy requests to Dash apps while injecting Authorization headers,
**so that** tenant-scoped JWTs are passed securely to Dash apps without client-side exposure.

**Acceptance Criteria:**

1. app/api/proxy/dash/[...path]/route.ts created as catch-all API route
2. Route extracts tenant-scoped token from auth context or HTTP-only cookie (if implemented)
3. Route reconstructs target URL: http://dash-app-{dashboard_slug}:{port}/[...path]
4. Route maps dashboard slugs to ports: customer-lifetime-value → 8050, risk-analysis → 8051
5. Route creates proxied request to Dash app with all query params and request body preserved
6. Route injects Authorization: Bearer {tenant_token} header into proxied request
7. Route forwards response from Dash app back to client (status, headers, body)
8. If tenant token missing or invalid, returns 401 error without proxying
9. Route logs proxied requests: dashboard_slug, path, response status
10. Route handles Dash app unavailable errors (connection refused) with 503 error
11. TypeScript types defined for proxy route parameters
12. Manual testing verifies headers injected correctly using Dash app logging

## Story 5.2: Dashboard Embedding Page with iframe or Direct Embed

**As a** user,
**I want** to view embedded Dash dashboards within the Shell UI,
**so that** I have a seamless experience without leaving the application.

**Acceptance Criteria:**

1. app/tenant/[tenant_slug]/dashboard/[dashboard_slug]/page.tsx created
2. Page displays tenant name and dashboard title in header
3. Page embeds Dash app using iframe pointing to /api/proxy/dash/[dashboard_slug]/
4. iframe styled to fill available viewport area (full-height, responsive width)
5. iframe src includes all necessary Dash routing (e.g., /api/proxy/dash/customer-lifetime-value/)
6. Page shows loading skeleton while Dash app initializes
7. If dashboard_slug not found in tenant's assigned dashboards, shows 404 message
8. Debug panel remains visible in Shell UI header (outside iframe)
9. Tenant switcher dropdown remains functional in Shell UI header
10. Back navigation returns to dashboard listing page
11. Page handles iframe load errors with user-friendly error message
12. TypeScript interfaces for dashboard embed page props

## Story 5.3: Token Expiry Handling and Redirect

**As a** user,
**I want** to be redirected to login or tenant selection when my token expires,
**so that** I can re-authenticate and continue using the application.

**Acceptance Criteria:**

1. Reverse proxy detects 401 responses from Dash apps (indicating expired/invalid token)
2. Proxy returns 401 status to client with error code "TOKEN_EXPIRED"
3. Client-side error boundary or interceptor detects 401 responses
4. On 401 from embedded dashboard, Shell UI redirects user to tenant selection page
5. User sees notification message: "Your session has expired. Please select your tenant again."
6. If user token also expired, redirect to /login with message: "Please log in again."
7. useTokenRefresh hook created (optional) to proactively refresh tenant token before expiry
8. Hook checks token expiry from debug panel or decoded JWT, triggers exchange 5 minutes before expiration
9. Successful proactive refresh shows subtle notification: "Session refreshed"
10. Failed refresh redirects to tenant selection or login as appropriate
11. E2E test verifies token expiry flow: wait for expiry, interact with dashboard, verify redirect

---
