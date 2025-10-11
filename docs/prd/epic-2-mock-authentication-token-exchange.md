# Epic 2: Mock Authentication & Token Exchange

**Epic Goal:** Implement the core JWT token exchange mechanism that validates the multi-tenant architecture - converting user access tokens (with multiple tenant_ids) into tenant-scoped tokens (with single tenant_id) while enforcing access control and providing tenant metadata APIs.

## Story 2.1: Mock Authentication Endpoint with Pre-Generated JWTs

**As a** user,
**I want** to log in with my email address and receive a user access token,
**so that** I can proceed to select a tenant from those I have access to.

**Acceptance Criteria:**

1. POST /api/auth/mock-login endpoint accepts {email: string} request body
2. Endpoint looks up user in mock data from shared_config module
3. If user found, endpoint generates user access token JWT with claims: sub (user_id), email, tenant_ids (array of UUIDs), iat, exp (1 hour)
4. JWT signed with shared JWT_SECRET_KEY using HS256 algorithm
5. Response returns {access_token: string, token_type: "Bearer", expires_in: 3600}
6. If user not found, returns 404 with error: {error: {code: "USER_NOT_FOUND", message: "User with email ... not found"}}
7. Mock users defined in shared-config: analyst@acme.com (Acme only), admin@acme.com (Acme + Beta), viewer@beta.com (Beta only)
8. Endpoint logs authentication attempt with email and success/failure
9. Unit tests verify JWT claims structure and signature validation
10. Integration test verifies full login flow with valid and invalid emails

## Story 2.2: User Info Endpoint with Tenant Discovery

**As a** user,
**I want** to retrieve my profile and list of tenants I can access,
**so that** the Shell UI can display available tenants for selection.

**Acceptance Criteria:**

1. GET /api/me endpoint requires Bearer token authentication (user access token)
2. JWT validation middleware extracts and validates user token, rejecting invalid/expired tokens with 401
3. Endpoint extracts user_id (sub) and tenant_ids from validated JWT claims
4. Endpoint queries database for user record matching user_id
5. Endpoint queries database for tenant records WHERE id IN tenant_ids AND is_active = 1
6. Endpoint queries user_tenants table to get role for each tenant
7. Response returns: {user_id, email, tenants: [{id, name, slug, role, config_json}, ...]}
8. Tenants array sorted alphabetically by name
9. If user_id from JWT not found in database, returns 404 with "USER_NOT_FOUND" error
10. If no active tenants found, returns empty tenants array (not an error)
11. Endpoint logs request with user_id and number of tenants returned
12. Unit tests verify tenant filtering and role mapping
13. Integration test verifies end-to-end flow with mock JWT

## Story 2.3: Token Exchange Endpoint for Tenant Scoping

**As a** user,
**I want** to exchange my user access token for a tenant-scoped token after selecting a tenant,
**so that** I can access dashboards and data specific to that tenant with hard isolation.

**Acceptance Criteria:**

1. POST /api/token/exchange endpoint requires Bearer token (user access token) and accepts {tenant_id: string} in request body
2. Endpoint validates user access token and extracts tenant_ids array from claims
3. Endpoint verifies requested tenant_id is in the user's tenant_ids array, returns 403 "ACCESS_DENIED" if not
4. Endpoint queries user_tenants table to get user's role for the requested tenant
5. Endpoint generates tenant-scoped JWT with claims: sub (user_id), email, tenant_id (single UUID), role, iat, exp (30 minutes)
6. Tenant-scoped JWT signed with shared JWT_SECRET_KEY using HS256 algorithm
7. Response returns {access_token: string, token_type: "Bearer", expires_in: 1800}
8. If tenant_id missing from request, returns 400 "INVALID_REQUEST"
9. If user does not have access to tenant, returns 403 with error: {error: {code: "TENANT_ACCESS_DENIED", message: "User does not have access to tenant ..."}}
10. Endpoint logs token exchange: user_id, tenant_id, role, token expiry
11. Unit tests verify tenant_id validation and JWT claims structure
12. Integration test verifies complete exchange flow and validates resulting tenant-scoped token
13. Security test verifies user cannot exchange token for unauthorized tenant

## Story 2.4: Tenant Metadata API Endpoints

**As a** Shell UI,
**I want** to retrieve tenant configuration and dashboard assignments,
**so that** I can display branding, feature flags, and available dashboards for the selected tenant.

**Acceptance Criteria:**

1. GET /api/tenant/{tenant_id} endpoint requires Bearer token (tenant-scoped token)
2. JWT validation middleware extracts tenant_id claim from token and compares to {tenant_id} path parameter, returns 403 if mismatch
3. Endpoint queries database for tenant record WHERE id = tenant_id
4. Response returns: {id, name, slug, is_active, config_json, created_at}
5. If tenant not found, returns 404 "TENANT_NOT_FOUND"
6. GET /api/tenant/{tenant_id}/dashboards endpoint requires tenant-scoped token with matching tenant_id
7. Endpoint queries tenant_dashboards JOIN dashboards to get assigned dashboards for tenant
8. Response returns array: [{slug, title, description, config_json}, ...]
9. Dashboards sorted alphabetically by title
10. If tenant has no dashboards assigned, returns empty array (not error)
11. Both endpoints use consistent tenant_id validation middleware
12. Endpoints log requests with tenant_id and response status
13. Unit tests verify tenant_id claim validation and mismatch detection
14. Integration tests verify full flow with valid tenant-scoped tokens

---
