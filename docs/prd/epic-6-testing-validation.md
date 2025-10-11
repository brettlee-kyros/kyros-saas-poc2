# Epic 6: Testing & Validation

**Epic Goal:** Implement comprehensive testing to validate the JWT token exchange mechanism, tenant isolation, and end-to-end user flows - proving the architecture works as designed.

## Story 6.1: Backend Unit Tests for JWT and Token Exchange

**As a** developer,
**I want** unit tests for JWT validation and token exchange logic,
**so that** I can verify the core authentication mechanisms work correctly in isolation.

**Acceptance Criteria:**

1. apps/api/tests/test_jwt.py created with unit tests for shared_config JWT functions
2. Tests verify: JWT encoding with correct claims, JWT decoding and validation, expired token rejection, tampered token rejection (signature validation)
3. apps/api/tests/test_token_exchange.py created with tests for token exchange endpoint
4. Tests verify: valid exchange succeeds, unauthorized tenant access returns 403, missing tenant_id returns 400, invalid user token returns 401
5. Tests verify tenant-scoped token contains exactly one tenant_id (not array)
6. Tests verify tenant-scoped token includes correct role from user_tenants table
7. All tests use pytest with async test client (httpx.AsyncClient)
8. Tests use in-memory SQLite database fixture (not production database)
9. Test coverage for JWT and token exchange modules exceeds 80%
10. Tests run successfully: pytest apps/api/tests/

## Story 6.2: Backend Integration Tests for API Endpoints

**As a** developer,
**I want** integration tests for complete API workflows,
**so that** I can verify endpoints work together correctly with database interactions.

**Acceptance Criteria:**

1. apps/api/tests/test_integration.py created with full flow tests
2. Test: login → /api/auth/mock-login → /api/me → verify tenant list
3. Test: login → tenant selection → /api/token/exchange → verify tenant-scoped token claims
4. Test: tenant-scoped token → /api/tenant/{id} → verify tenant metadata returned
5. Test: tenant-scoped token → /api/tenant/{id}/dashboards → verify dashboard list filtered by tenant
6. Test: tenant-scoped token → /api/dashboards/{slug}/data → verify data filtered by tenant_id
7. Test: mismatched tenant_id in token vs path parameter → verify 403 error
8. Tests use seeded test database with known fixtures (2 tenants, 3 users, 2 dashboards)
9. Tests verify logging output contains expected tenant_id and request details
10. Integration test coverage exceeds 70%
11. All integration tests pass: pytest apps/api/tests/test_integration.py

## Story 6.3: Frontend Unit Tests for Components and Hooks

**As a** developer,
**I want** unit tests for Shell UI components and hooks,
**so that** I can verify UI logic works correctly in isolation.

**Acceptance Criteria:**

1. apps/shell-ui/tests/components/TenantSelector.test.tsx created
2. Tests verify: tenant cards render correctly, "Select" button triggers token exchange, loading state shown during exchange, error handling for exchange failures
3. apps/shell-ui/tests/components/DebugPanel.test.tsx created
4. Tests verify: panel toggles open/closed, decoded JWT claims displayed correctly, expiry countdown updates, tenant_id vs tenant_ids array distinguished
5. apps/shell-ui/tests/hooks/useAuth.test.ts created
6. Tests verify: login stores token, logout clears token, isAuthenticated reflects token state
7. Tests use Vitest + React Testing Library
8. Tests mock API calls using vi.fn() or MSW (Mock Service Worker)
9. Component tests verify UI renders without TypeScript errors
10. Hook tests verify state management logic
11. Test coverage for components and hooks exceeds 60%
12. Tests run successfully: npm run test

## Story 6.4: End-to-End Tests for Critical Paths

**As a** stakeholder,
**I want** E2E tests that validate complete user journeys including tenant isolation,
**so that** I can verify the PoC architecture works end-to-end as designed.

**Acceptance Criteria:**

1. tests/e2e/auth-flow.spec.ts created with Playwright
2. Test: Login with analyst@acme.com → verify tenant selection page → select Acme → verify dashboard listing → open CLV dashboard → verify Dash app loads
3. Test: Login with admin@acme.com → select Acme → verify 2 dashboards shown → select Beta → verify 1 dashboard shown (tenant isolation)
4. tests/e2e/token-expiry.spec.ts created
5. Test: Login → select tenant → wait for token expiry (or mock expiry) → interact with dashboard → verify redirect to tenant selection
6. tests/e2e/security-isolation.spec.ts created
7. Test: Login as user with Acme access → attempt to exchange token for Beta tenant_id → verify 403 error
8. Test: Manually modify JWT in browser dev tools → attempt API call → verify 401 error
9. Test: Valid tenant-scoped token for Acme → call /api/dashboards/risk-analysis/data → verify only Acme data returned (check tenant_id in response)
10. All E2E tests run in headless mode against Docker Compose environment
11. Tests verify debug panel shows correct JWT claims after each step
12. Playwright screenshots captured on test failures for debugging
13. E2E tests pass: npm run test:e2e

## Story 6.5: PoC Demonstration Documentation

**As a** stakeholder,
**I want** clear documentation explaining what the PoC demonstrates and how to interpret results,
**So that** I can understand the architectural validation and make informed MVP decisions.

**Acceptance Criteria:**

1. **[BLOCKER RESOLUTION #4]** `docs/demo-script.md` created with step-by-step demonstration walkthrough
2. **[BLOCKER RESOLUTION #4]** Demo script includes sections:
   - Prerequisites check (Docker running, database seeded)
   - Step 1: Login flow (which test users to use)
   - Step 2: Tenant selection (multi-tenant user workflow)
   - Step 3: Dashboard listing (tenant-specific dashboards)
   - Step 4: Dashboard viewing (embedded Dash app)
   - Step 5: Debug panel usage (JWT claims inspection)
   - Step 6: Token expiry handling (optional advanced demo)
3. **[BLOCKER RESOLUTION #4]** Demo script explains what's proven vs. what's mocked:
   - PROVEN: JWT token exchange mechanism works
   - PROVEN: Tenant isolation via JWT claims (no cross-tenant data leakage)
   - PROVEN: Reverse proxy header injection securely passes tokens
   - PROVEN: Shared config prevents configuration drift
   - MOCKED: Authentication (no real Azure AD B2C)
   - MOCKED: Data storage (in-memory vs. Azure Storage)
   - MOCKED: Infrastructure (local Docker vs. Azure)
4. **[BLOCKER RESOLUTION #4]** Troubleshooting guide for common demo issues:
   - Docker Compose fails to start
   - Database not seeded (empty tenant list)
   - Dash apps return 401 (JWT validation failure)
   - Token expired during demo
   - Network connectivity issues between containers
5. **[BLOCKER RESOLUTION #4]** Architecture validation checklist:
   - [ ] JWT token exchange converts multi-tenant token to single-tenant token
   - [ ] Tenant-scoped token contains single tenant_id (not array)
   - [ ] Reverse proxy injects Authorization header (verified via Dash logs)
   - [ ] Dash apps validate JWT using shared config
   - [ ] Cross-tenant API calls return 403 Forbidden
   - [ ] Dashboard data filtered by tenant_id from JWT
6. **[BLOCKER RESOLUTION #4]** Screenshots or GIFs showing key validation points:
   - Debug panel with decoded user access token (tenant_ids array)
   - Debug panel with decoded tenant-scoped token (single tenant_id)
   - Dashboard listing showing tenant-specific dashboards
   - Embedded Dash app with tenant data
   - Error state: 403 when attempting unauthorized tenant access
7. **[BLOCKER RESOLUTION #4]** FAQ section answering:
   - Why use mock authentication instead of real Azure AD B2C?
   - How does this PoC relate to MVP requirements?
   - What changes are needed to transition from PoC to MVP?
   - Can this architecture scale to production?
   - What security validations does this PoC prove?
8. **[BLOCKER RESOLUTION #4]** `docs/architectural-validation-summary.md` created listing:
   - Core hypothesis: "JWT token exchange can enforce hard tenant isolation"
   - Validation evidence: Test results, logs, screenshots
   - Risk areas identified during PoC
   - Recommendations for MVP (from Architecture Appendix)
9. **[BLOCKER RESOLUTION #4]** Demo script formatted for easy reading (numbered steps, clear headings, copy-pasteable commands)
10. **[BLOCKER RESOLUTION #4]** Product Owner review and approval of demo documentation

**Definition of Done:**
- Demo script comprehensive and tested with at least one practice run
- Troubleshooting guide covers all issues encountered during development
- Architectural validation checklist maps to PRD goals
- Screenshots/GIFs captured and saved to `docs/assets/demo/`
- FAQ addresses stakeholder concerns
- Product Owner approves documentation

---
