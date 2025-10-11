# Kyros Multi-Tenant SaaS PoC - Test Architecture

**Version:** 0.1
**Date:** 2025-10-07
**Author:** Quinn (Test Architect & Quality Advisor)
**Status:** Early Architecture - Pre-Implementation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Risk-Based Test Strategy](#2-risk-based-test-strategy)
3. [Requirements Traceability Matrix](#3-requirements-traceability-matrix)
4. [Test Architecture by Epic](#4-test-architecture-by-epic)
5. [Non-Functional Requirements Assessment](#5-non-functional-requirements-assessment)
6. [Quality Gates & Decision Framework](#6-quality-gates--decision-framework)
7. [Test Infrastructure](#7-test-infrastructure)
8. [Test Data Strategy](#8-test-data-strategy)
9. [Test Execution Plan](#9-test-execution-plan)
10. [Technical Debt & Improvement Opportunities](#10-technical-debt--improvement-opportunities)

---

## 1. Executive Summary

### 1.1 Purpose

This test architecture document provides comprehensive quality assurance guidance for the Kyros Multi-Tenant SaaS PoC. The primary validation target is **hard tenant isolation through JWT token exchange**, with security testing as the critical success factor.

### 1.2 Critical Quality Attributes

| Quality Attribute | Priority | Rationale |
|-------------------|----------|-----------|
| **Security (Tenant Isolation)** | CRITICAL | Core architectural validation - tenant data leakage is catastrophic failure |
| **Testability** | HIGH | PoC success depends on demonstrating verifiable tenant isolation |
| **Functional Correctness** | HIGH | Token exchange and authentication flows must work reliably |
| **Performance** | MEDIUM | In-memory data and local deployment make performance less critical for PoC |
| **Usability** | MEDIUM | Demo clarity important, but not production-critical |
| **Maintainability** | LOW | PoC code is disposable; focus on validating patterns, not code quality |

### 1.3 Test Strategy Summary

- **Testing Pyramid:** 40% Frontend Unit, 40% Backend Unit, 15% Integration, 5% E2E
- **Risk-Based Approach:** Heavy investment in security testing (cross-tenant isolation attacks)
- **Epic-Aligned Testing:** Each epic has dedicated test scenarios and quality gates
- **Advisory Quality Gates:** PASS/CONCERNS/FAIL/WAIVED decisions guide progress without blocking
- **LLM-Accelerated Analysis:** Use AI for thorough yet focused test case generation and risk assessment

### 1.4 Key Success Metrics

- **Zero cross-tenant data leakage** in isolation attack scenarios
- **100% JWT validation coverage** across all services
- **All critical path E2E tests pass** (login → tenant select → dashboard view)
- **Token exchange success rate >99%** in integration tests
- **Shared config module correctly loaded** in all Python services

---

## 2. Risk-Based Test Strategy

### 2.1 Risk Assessment Matrix

| Risk Area | Probability | Impact | Overall Risk | Test Investment |
|-----------|-------------|--------|--------------|-----------------|
| **Cross-Tenant Data Leakage** | Medium | CRITICAL | **HIGH** | 🔴 Heavy (30% of effort) |
| **JWT Validation Inconsistency** | High | CRITICAL | **HIGH** | 🔴 Heavy (25% of effort) |
| **Token Exchange Logic Errors** | Medium | High | **MEDIUM-HIGH** | 🟡 Moderate (20% of effort) |
| **Reverse Proxy Header Injection Failure** | Low | High | **MEDIUM** | 🟡 Moderate (10% of effort) |
| **Mock Auth Misalignment with Real OIDC** | Low | Medium | **LOW-MEDIUM** | 🟢 Light (5% of effort) |
| **UI State Management Bugs** | Medium | Low | **LOW** | 🟢 Light (5% of effort) |
| **Database Seed Data Inconsistency** | Low | Low | **LOW** | 🟢 Light (5% of effort) |

### 2.2 Test Coverage Prioritization

#### Critical (Must Test)
- JWT signature validation in all services (FastAPI, Dash apps)
- Token exchange validation (user must have access to requested tenant)
- Tenant ID extracted from JWT claims (never from request params)
- Cross-tenant API call rejection (403 Forbidden)
- Shared config module loaded correctly in all Python services

#### High (Should Test)
- Mock login flow (email → user access token)
- Tenant selector UI (multi-tenant users see correct list)
- Dashboard listing filtered by tenant_dashboards table
- Reverse proxy Authorization header injection
- Token expiry handling (401 triggers refresh)

#### Medium (Could Test)
- Error response format consistency
- Database connection pooling (minimal for SQLite)
- Frontend component rendering edge cases
- API pagination (if implemented)

#### Low (Won't Test for PoC)
- Performance benchmarks (not critical for local demo)
- Accessibility compliance (out of PoC scope)
- Browser compatibility matrix (modern browsers only)
- Observability instrumentation (logging only in PoC)

---

## 3. Requirements Traceability Matrix

### 3.1 Epic 1: Foundation & Shared Configuration

| Requirement | Test Scenario | Given-When-Then | Test Type | Priority |
|-------------|---------------|-----------------|-----------|----------|
| Shared JWT config module exists | Verify shared-config package installable | **Given** shared-config package defined<br>**When** `pip install -e packages/shared-config` runs<br>**Then** package imports successfully in FastAPI and Dash | Unit | CRITICAL |
| JWT settings consistent across services | Import JWT_SECRET_KEY in all services | **Given** shared-config module installed<br>**When** FastAPI and Dash apps import JWT_SECRET_KEY<br>**Then** all services use identical secret value | Integration | CRITICAL |
| Database seed script creates valid data | Run seed script and verify tables | **Given** schema.sql seed data<br>**When** `python scripts/seed-database.py` executes<br>**Then** tenants, users, user_tenants, dashboards tables populated with valid UUIDs | Unit | HIGH |
| Health check endpoint returns 200 OK | GET /health | **Given** FastAPI running<br>**When** GET /health<br>**Then** 200 OK with `{"status": "ok"}` | Integration | MEDIUM |

### 3.2 Epic 2: Mock Authentication & Token Exchange

| Requirement | Test Scenario | Given-When-Then | Test Type | Priority |
|-------------|---------------|-----------------|-----------|----------|
| Mock login returns user access token | POST /api/auth/mock-login | **Given** user "analyst@acme.com" in mock data<br>**When** POST /api/auth/mock-login with email<br>**Then** 200 OK with access_token containing tenant_ids array | Integration | CRITICAL |
| User token validation extracts tenant_ids | Decode user access token | **Given** valid user access token<br>**When** JWT decoded with shared secret<br>**Then** claims contain tenant_ids: [UUID, UUID, ...] | Unit | CRITICAL |
| Token exchange validates tenant access | POST /api/token/exchange with unauthorized tenant | **Given** user with access to T1 only<br>**When** POST /api/token/exchange with tenant_id=T2<br>**Then** 403 Forbidden with error code TENANT_ACCESS_DENIED | Integration | CRITICAL |
| Token exchange issues tenant-scoped token | POST /api/token/exchange with valid tenant | **Given** user with access to T1<br>**When** POST /api/token/exchange with tenant_id=T1<br>**Then** 200 OK with token containing single tenant_id=T1 and role | Integration | CRITICAL |
| Tenant-scoped token expires in 30 min | Verify token exp claim | **Given** newly issued tenant-scoped token<br>**When** JWT decoded<br>**Then** exp claim is iat + 1800 seconds | Unit | HIGH |
| Tenant metadata API validates token tenant_id | GET /api/tenant/{T1} with T2 token | **Given** tenant-scoped token for T2<br>**When** GET /api/tenant/T1<br>**Then** 403 Forbidden with error TENANT_MISMATCH | Integration | CRITICAL |

### 3.3 Epic 3: Shell UI & Tenant Selection

| Requirement | Test Scenario | Given-When-Then | Test Type | Priority |
|-------------|---------------|-----------------|-----------|----------|
| Login form accepts email and calls API | Submit login form | **Given** user on /login page<br>**When** enter "analyst@acme.com" and submit<br>**Then** POST /api/auth/mock-login called with email | Unit (React) | HIGH |
| Tenant selector shows only user's tenants | Render TenantSelector with multi-tenant user | **Given** user access token with tenant_ids=[T1, T2]<br>**When** TenantSelector renders after GET /api/me<br>**Then** displays "Acme Corporation" and "Beta Industries" only | Unit (React) | HIGH |
| Tenant selection triggers token exchange | Click tenant in selector | **Given** user viewing tenant list<br>**When** click "Acme Corporation"<br>**Then** POST /api/token/exchange called with tenant_id=T1 | E2E | CRITICAL |
| Dashboard listing filtered by tenant | GET /api/tenant/{id}/dashboards | **Given** tenant T2 assigned only "risk-analysis"<br>**When** GET /api/tenant/T2/dashboards with T2 token<br>**Then** returns only "risk-analysis", not "customer-lifetime-value" | Integration | HIGH |

### 3.4 Epic 4: Dash Application Integration

| Requirement | Test Scenario | Given-When-Then | Test Type | Priority |
|-------------|---------------|-----------------|-----------|----------|
| Dash app validates JWT from Authorization header | Dash app receives request with invalid token | **Given** Dash app running<br>**When** GET /dash/clv/ with invalid Authorization header<br>**Then** 401 Unauthorized returned | Integration | CRITICAL |
| Dash app extracts tenant_id from JWT | Dash app parses valid tenant-scoped token | **Given** Dash app receives valid token with tenant_id=T1<br>**When** Dash app decodes JWT<br>**Then** tenant_id=T1 extracted and stored in request context | Unit | CRITICAL |
| Dash app fetches data via FastAPI API | Dash callback queries data | **Given** Dash app initialized for T1<br>**When** user triggers filter callback<br>**Then** GET /api/dashboards/clv/data called with tenant token | Integration | HIGH |
| Dash app renders only tenant-scoped data | Data filtering validation | **Given** T1 data contains 100 rows, T2 data contains 50 rows<br>**When** Dash app renders with T1 token<br>**Then** visualizations show exactly 100 rows | E2E | CRITICAL |

### 3.5 Epic 5: Reverse Proxy & Dashboard Embedding

| Requirement | Test Scenario | Given-When-Then | Test Type | Priority |
|-------------|---------------|-----------------|-----------|----------|
| Reverse proxy injects Authorization header | API route proxies request to Dash | **Given** Next.js API route receives request with tenant token in HTTP-only cookie<br>**When** /api/proxy/dash/clv/[path] proxies to Dash<br>**Then** Authorization: Bearer {token} header added to upstream request | Integration | CRITICAL |
| Embedded Dash app loads successfully | Dashboard embed page renders | **Given** user navigates to /tenant/acme-corp/dashboard/clv<br>**When** page loads with iframe/embed<br>**Then** Dash app renders via reverse proxy without exposing token to client | E2E | CRITICAL |
| Token expiry triggers refresh | Expired token handling | **Given** tenant-scoped token expired (>30 min old)<br>**When** Dash app makes API call<br>**Then** 401 returned, Shell UI calls /api/token/exchange, new token issued, embed reloaded | E2E | HIGH |

### 3.6 Epic 6: Testing & Validation

| Requirement | Test Scenario | Given-When-Then | Test Type | Priority |
|-------------|---------------|-----------------|-----------|----------|
| JWT validation unit tests pass | Run pytest on jwt_service | **Given** jwt_service with validation functions<br>**When** pytest runs test_jwt_service.py<br>**Then** all token validation tests pass (valid, expired, invalid signature) | Unit | CRITICAL |
| Cross-tenant isolation attack tests fail gracefully | Penetration test scenarios | **Given** attacker with valid T1 token<br>**When** attempts to access T2 data via API manipulation<br>**Then** all attacks return 403 Forbidden with no data leakage | Integration | CRITICAL |
| E2E critical path test passes | Full user journey | **Given** clean database state<br>**When** login → select tenant → view dashboard → interact with filters<br>**Then** user sees correct tenant data, no errors, token refresh works | E2E | CRITICAL |

---

## 4. Test Architecture by Epic

### 4.1 Epic 1: Foundation & Shared Configuration

#### Test Objectives
- Verify shared-config package correctly exposes JWT settings
- Validate database seed script creates consistent, valid data
- Ensure FastAPI and Dash apps can import shared configuration

#### Test Scenarios

##### Scenario 1.1: Shared Config Module Availability
```python
# Test: packages/shared-config/tests/test_config.py
def test_jwt_config_exports():
    """Verify shared config exposes required JWT settings"""
    from shared_config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ISSUER

    assert JWT_SECRET_KEY is not None
    assert JWT_ALGORITHM == "HS256"
    assert JWT_ISSUER == "kyros-poc"
```

##### Scenario 1.2: Config Consistency Across Services
```python
# Test: tests/integration/test_config_consistency.py
def test_all_services_use_same_jwt_secret():
    """Verify FastAPI and Dash apps import identical JWT secret"""
    from apps.api.src.services.jwt_service import JWT_SECRET_KEY as api_secret
    from apps.dash_app_clv.auth import JWT_SECRET_KEY as dash_clv_secret
    from apps.dash_app_risk.auth import JWT_SECRET_KEY as dash_risk_secret

    assert api_secret == dash_clv_secret == dash_risk_secret
```

##### Scenario 1.3: Database Seed Data Validity
```python
# Test: scripts/tests/test_seed_database.py
def test_seed_creates_valid_tenants():
    """Verify seed script creates tenants with valid UUIDs and relationships"""
    # Run seed script
    subprocess.run(["python", "scripts/seed-database.py"], check=True)

    # Verify tenants
    conn = sqlite3.connect("data/tenant_metadata.db")
    tenants = pd.read_sql("SELECT id, name, slug FROM tenants", conn)

    assert len(tenants) == 2
    assert all(is_valid_uuid(t) for t in tenants['id'])
    assert 'acme-corp' in tenants['slug'].values
```

#### Quality Gate: Epic 1
- **PASS Criteria:**
  - All shared-config unit tests pass
  - Config consistency test passes across all services
  - Seed script creates valid data matching schema
- **CONCERNS Criteria:**
  - Config imports work but lack type validation
  - Seed data valid but UUIDs not properly formatted
- **FAIL Criteria:**
  - Services import different JWT secrets (configuration drift)
  - Seed script fails or creates invalid foreign key relationships

---

### 4.2 Epic 2: Mock Authentication & Token Exchange

#### Test Objectives
- Validate mock login returns correctly formatted user access tokens
- Ensure token exchange enforces tenant access authorization
- Verify tenant-scoped tokens contain single tenant_id and role
- Test JWT signature validation rejects tampered tokens

#### Test Scenarios

##### Scenario 2.1: Mock Login Flow
```python
# Test: apps/api/tests/test_auth.py
@pytest.mark.asyncio
async def test_mock_login_returns_user_access_token(async_client):
    """Mock login issues token with tenant_ids array"""
    response = await async_client.post(
        "/api/auth/mock-login",
        json={"email": "admin@acme.com"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    # Decode and validate
    payload = jwt.decode(data["access_token"], JWT_SECRET_KEY, algorithms=["HS256"])
    assert payload["email"] == "admin@acme.com"
    assert "tenant_ids" in payload
    assert len(payload["tenant_ids"]) == 2  # Admin has access to T1 and T2
```

##### Scenario 2.2: Token Exchange Authorization Check
```python
# Test: apps/api/tests/test_token_exchange.py
@pytest.mark.asyncio
async def test_token_exchange_rejects_unauthorized_tenant(async_client, user_token_t1_only):
    """User with access to T1 cannot get token for T2"""
    response = await async_client.post(
        "/api/token/exchange",
        headers={"Authorization": f"Bearer {user_token_t1_only}"},
        json={"tenant_id": "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4"}  # T2
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "TENANT_ACCESS_DENIED"
```

##### Scenario 2.3: Tenant-Scoped Token Structure
```python
# Test: apps/api/tests/test_token_exchange.py
@pytest.mark.asyncio
async def test_tenant_scoped_token_structure(async_client, user_token_multi_tenant):
    """Tenant-scoped token contains single tenant_id and role"""
    response = await async_client.post(
        "/api/token/exchange",
        headers={"Authorization": f"Bearer {user_token_multi_tenant}"},
        json={"tenant_id": "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"}  # T1
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    assert payload["tenant_id"] == "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"
    assert "tenant_ids" not in payload  # Should be single tenant_id, not array
    assert payload["role"] in ["admin", "viewer"]
    assert payload["exp"] - payload["iat"] == 1800  # 30 minutes
```

##### Scenario 2.4: JWT Signature Validation
```python
# Test: apps/api/tests/test_jwt_validation.py
def test_jwt_validation_rejects_tampered_token():
    """Modified JWT claims are detected via signature validation"""
    # Create valid token
    valid_token = jwt.encode(
        {"sub": "user123", "tenant_id": "T1", "exp": time.time() + 3600},
        JWT_SECRET_KEY,
        algorithm="HS256"
    )

    # Tamper with token (change tenant_id in payload without re-signing)
    header, payload, signature = valid_token.split(".")
    tampered_payload = base64.b64decode(payload + "==")
    tampered_payload = tampered_payload.replace(b'"T1"', b'"T2"')
    tampered_token = f"{header}.{base64.b64encode(tampered_payload).decode().rstrip('=')}.{signature}"

    # Validation should fail
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(tampered_token, JWT_SECRET_KEY, algorithms=["HS256"])
```

#### Quality Gate: Epic 2
- **PASS Criteria:**
  - All mock auth tests pass
  - Token exchange correctly validates tenant access (403 for unauthorized)
  - JWT signature tampering always detected
  - Tenant-scoped tokens have correct structure and expiry
- **CONCERNS Criteria:**
  - Token exchange works but error messages not standardized
  - Expiry times slightly off (±5 seconds) due to clock skew
- **FAIL Criteria:**
  - Token exchange allows access to unauthorized tenants
  - JWT signature validation not working (services use different secrets)
  - Tenant-scoped tokens missing required claims

---

### 4.3 Epic 3: Shell UI & Tenant Selection

#### Test Objectives
- Verify login form correctly calls mock auth API
- Ensure tenant selector displays only authorized tenants
- Test tenant selection triggers token exchange
- Validate dashboard listing filtered by tenant

#### Test Scenarios

##### Scenario 3.1: Login Form Component
```typescript
// Test: apps/shell-ui/tests/components/LoginForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LoginForm } from '@/components/auth/LoginForm';

test('login form submits email to mock auth endpoint', async () => {
  const mockLogin = jest.fn().mockResolvedValue({ access_token: 'token123' });

  render(<LoginForm onLogin={mockLogin} />);

  const emailInput = screen.getByLabelText(/email/i);
  const submitButton = screen.getByRole('button', { name: /login/i });

  fireEvent.change(emailInput, { target: { value: 'analyst@acme.com' } });
  fireEvent.click(submitButton);

  await waitFor(() => {
    expect(mockLogin).toHaveBeenCalledWith('analyst@acme.com');
  });
});
```

##### Scenario 3.2: Tenant Selector Filtering
```typescript
// Test: apps/shell-ui/tests/components/TenantSelector.test.tsx
test('tenant selector shows only accessible tenants', async () => {
  const mockTenants = [
    { id: 'T1', name: 'Acme Corporation', slug: 'acme-corp' },
    { id: 'T2', name: 'Beta Industries', slug: 'beta-ind' }
  ];

  render(<TenantSelector tenants={mockTenants} onSelect={jest.fn()} />);

  expect(screen.getByText('Acme Corporation')).toBeInTheDocument();
  expect(screen.getByText('Beta Industries')).toBeInTheDocument();
  expect(screen.queryByText('Unauthorized Tenant')).not.toBeInTheDocument();
});
```

##### Scenario 3.3: Tenant Selection E2E
```typescript
// Test: tests/e2e/auth-and-tenant-selection.spec.ts
import { test, expect } from '@playwright/test';

test('user can login and select tenant', async ({ page }) => {
  // Navigate to login
  await page.goto('http://localhost:3000/login');

  // Login as multi-tenant user
  await page.fill('input[type="email"]', 'admin@acme.com');
  await page.click('button:has-text("Login")');

  // Should see tenant selector
  await expect(page.locator('h1')).toContainText('Select Tenant');
  await expect(page.locator('text=Acme Corporation')).toBeVisible();
  await expect(page.locator('text=Beta Industries')).toBeVisible();

  // Select Acme
  await page.click('text=Acme Corporation');

  // Should redirect to dashboard listing
  await expect(page).toHaveURL(/\/tenant\/acme-corp/);
  await expect(page.locator('h1')).toContainText('Dashboards');
});
```

#### Quality Gate: Epic 3
- **PASS Criteria:**
  - Login form tests pass
  - Tenant selector correctly filters by user access
  - E2E test completes full login → tenant select flow
  - Dashboard listing shows only assigned dashboards
- **CONCERNS Criteria:**
  - UI tests pass but accessibility concerns (missing labels)
  - Navigation works but URL slugs exposed (documented PoC tradeoff)
- **FAIL Criteria:**
  - Tenant selector shows unauthorized tenants
  - Token exchange not triggered on tenant selection
  - E2E test fails at any step

---

### 4.4 Epic 4: Dash Application Integration

#### Test Objectives
- Verify Dash apps validate JWT from Authorization header
- Ensure Dash apps extract tenant_id from JWT claims
- Test Dash apps fetch data via FastAPI with tenant-scoped tokens
- Validate data filtering based on tenant context

#### Test Scenarios

##### Scenario 4.1: Dash JWT Validation
```python
# Test: apps/dash-app-clv/tests/test_auth.py
def test_dash_app_validates_jwt_header():
    """Dash app extracts and validates JWT from Authorization header"""
    from apps.dash_app_clv.auth import validate_request_token

    # Create mock request with valid token
    valid_token = create_tenant_scoped_token(tenant_id="T1", role="viewer")
    mock_request = Mock()
    mock_request.headers = {"Authorization": f"Bearer {valid_token}"}

    tenant_id, role = validate_request_token(mock_request)

    assert tenant_id == "T1"
    assert role == "viewer"

def test_dash_app_rejects_invalid_token():
    """Dash app returns 401 for invalid Authorization header"""
    from apps.dash_app_clv.auth import validate_request_token

    mock_request = Mock()
    mock_request.headers = {"Authorization": "Bearer invalid_token"}

    with pytest.raises(UnauthorizedException):
        validate_request_token(mock_request)
```

##### Scenario 4.2: Tenant-Scoped Data Loading
```python
# Test: apps/dash-app-clv/tests/test_data_loading.py
@pytest.mark.asyncio
async def test_dash_loads_tenant_specific_data():
    """Dash app fetches data for correct tenant via FastAPI"""
    # Mock FastAPI data endpoint
    with aioresponses() as mocked:
        mocked.get(
            "http://localhost:8000/api/dashboards/customer-lifetime-value/data",
            payload={"tenant_id": "T1", "data": [{"customer_id": "C1", "clv": 15000}]}
        )

        # Simulate Dash callback with T1 token
        data = await load_dashboard_data(
            dashboard_slug="customer-lifetime-value",
            tenant_token=create_tenant_scoped_token("T1", "viewer")
        )

        assert data["tenant_id"] == "T1"
        assert len(data["data"]) == 1
```

#### Quality Gate: Epic 4
- **PASS Criteria:**
  - Dash apps correctly validate JWT from Authorization header
  - Dash apps extract tenant_id and use it for data queries
  - Dash apps reject requests with invalid/missing tokens (401)
  - Data loaded matches tenant context
- **CONCERNS Criteria:**
  - JWT validation works but error handling inconsistent
  - Dash apps load data but don't filter correctly (returns all tenants)
- **FAIL Criteria:**
  - Dash apps don't validate tokens (security vulnerability)
  - Dash apps use tenant_id from query params instead of JWT (insecure)
  - Cross-tenant data visible in Dash visualizations

---

### 4.5 Epic 5: Reverse Proxy & Dashboard Embedding

#### Test Objectives
- Verify Next.js API route injects Authorization header from HTTP-only cookie
- Ensure embedded Dash apps load without client-side token exposure
- Test token expiry detection and refresh mechanism
- Validate end-to-end flow including reverse proxy

#### Test Scenarios

##### Scenario 5.1: Reverse Proxy Header Injection
```typescript
// Test: apps/shell-ui/tests/api/proxy.test.ts
import { NextRequest } from 'next/server';
import { GET } from '@/app/api/proxy/dash/[...path]/route';

test('reverse proxy injects Authorization header from cookie', async () => {
  // Create mock request with tenant token in cookie
  const mockRequest = new NextRequest('http://localhost:3000/api/proxy/dash/clv/', {
    headers: {
      cookie: 'tenant_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    }
  });

  // Mock fetch to Dash app
  global.fetch = jest.fn().mockResolvedValue(new Response('Dash HTML', { status: 200 }));

  await GET(mockRequest, { params: { path: ['clv', ''] } });

  // Verify fetch called with Authorization header
  expect(global.fetch).toHaveBeenCalledWith(
    'http://dash-clv:8050/dash/clv/',
    expect.objectContaining({
      headers: expect.objectContaining({
        Authorization: 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
      })
    })
  );
});
```

##### Scenario 5.2: Token Expiry Handling E2E
```typescript
// Test: tests/e2e/token-expiry-and-refresh.spec.ts
import { test, expect } from '@playwright/test';

test('expired token triggers refresh and embed reload', async ({ page }) => {
  // Login and select tenant
  await page.goto('http://localhost:3000/login');
  await page.fill('input[type="email"]', 'analyst@acme.com');
  await page.click('button:has-text("Login")');
  await page.click('text=Acme Corporation');

  // Navigate to dashboard
  await page.click('text=Customer Lifetime Value');
  await expect(page.locator('iframe')).toBeVisible();

  // Simulate token expiry by waiting 31 minutes (mock or time travel)
  await page.evaluate(() => {
    // Manipulate cookie to set expired token
    document.cookie = 'tenant_token=expired_token; path=/';
  });

  // Trigger interaction that requires API call
  await page.frameLocator('iframe').locator('button:has-text("Apply Filter")').click();

  // Should see notification about session refresh
  await expect(page.locator('text=Session refreshed')).toBeVisible();

  // Dashboard should reload successfully
  await expect(page.frameLocator('iframe').locator('.dash-graph')).toBeVisible();
});
```

#### Quality Gate: Epic 5
- **PASS Criteria:**
  - Reverse proxy correctly injects Authorization header
  - Tokens stored in HTTP-only cookies (not accessible to client JS)
  - Token expiry detected and triggers refresh
  - Embedded Dash apps load successfully via proxy
- **CONCERNS Criteria:**
  - Proxy works but doesn't handle all HTTP methods (only GET)
  - Token refresh works but requires manual page reload
- **FAIL Criteria:**
  - Tokens exposed to client-side JavaScript (security vulnerability)
  - Reverse proxy doesn't inject Authorization header
  - Expired tokens not refreshed (user stuck in error state)

---

### 4.6 Epic 6: Testing & Validation

#### Test Objectives
- Implement comprehensive security testing (cross-tenant isolation attacks)
- Create full E2E test suite covering critical paths
- Validate test infrastructure and CI/CD readiness
- Document test coverage gaps and MVP requirements

#### Test Scenarios

##### Scenario 6.1: Cross-Tenant Isolation Attack Tests
```python
# Test: apps/api/tests/test_tenant_isolation.py
@pytest.mark.security
@pytest.mark.asyncio
async def test_attack_token_manipulation(async_client):
    """Attacker cannot modify tenant_id in JWT to access other tenant data"""
    # Get valid token for T1
    t1_token = create_tenant_scoped_token(tenant_id="T1", role="viewer")

    # Attempt to manually change tenant_id to T2 (should fail signature validation)
    header, payload, signature = t1_token.split(".")
    modified_payload = base64.b64decode(payload + "==")
    modified_payload = modified_payload.replace(b'"T1"', b'"T2"')
    tampered_token = f"{header}.{base64.b64encode(modified_payload).decode().rstrip('=')}.{signature}"

    # Try to access T2 data with tampered token
    response = await async_client.get(
        "/api/tenant/2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4",  # T2
        headers={"Authorization": f"Bearer {tampered_token}"}
    )

    assert response.status_code == 401
    assert "Invalid token signature" in response.json()["error"]["message"]

@pytest.mark.security
@pytest.mark.asyncio
async def test_attack_direct_tenant_enumeration(async_client):
    """Attacker with T1 token cannot enumerate T2 data via API calls"""
    # Get valid T1 token
    t1_token = create_tenant_scoped_token(tenant_id="8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345", role="viewer")

    # Try to access T2 tenant metadata
    response = await async_client.get(
        "/api/tenant/2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4",  # T2
        headers={"Authorization": f"Bearer {t1_token}"}
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "TENANT_MISMATCH"

@pytest.mark.security
@pytest.mark.asyncio
async def test_attack_dashboard_data_cross_tenant_access(async_client):
    """Attacker cannot access other tenant's dashboard data"""
    # T1 viewer token
    t1_token = create_tenant_scoped_token(tenant_id="8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345", role="viewer")

    # Load T1 data
    response = await async_client.get(
        "/api/dashboards/customer-lifetime-value/data",
        headers={"Authorization": f"Bearer {t1_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify no T2 data leaked into response
    t2_tenant_id = "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4"
    assert all(record.get("tenant_id") != t2_tenant_id for record in data["data"])
```

##### Scenario 6.2: Critical Path E2E Test
```typescript
// Test: tests/e2e/full-user-journey.spec.ts
test('complete user journey: login → tenant select → dashboard view → filter interaction', async ({ page }) => {
  // Step 1: Login
  await page.goto('http://localhost:3000/login');
  await page.fill('input[type="email"]', 'admin@acme.com');
  await page.click('button:has-text("Login")');

  // Step 2: Tenant Selection
  await expect(page.locator('h1')).toContainText('Select Tenant');
  await page.click('text=Acme Corporation');

  // Step 3: Dashboard Listing
  await expect(page).toHaveURL(/\/tenant\/acme-corp/);
  await expect(page.locator('text=Customer Lifetime Value')).toBeVisible();
  await expect(page.locator('text=Risk Analysis')).toBeVisible();

  // Step 4: Dashboard View
  await page.click('text=Customer Lifetime Value');
  await expect(page).toHaveURL(/\/dashboard\/customer-lifetime-value/);
  await expect(page.frameLocator('iframe').locator('.dash-graph')).toBeVisible();

  // Step 5: Filter Interaction
  await page.frameLocator('iframe').locator('select[id="date-range"]').selectOption('last-30-days');
  await page.frameLocator('iframe').locator('button:has-text("Apply")').click();

  // Verify updated visualization
  await expect(page.frameLocator('iframe').locator('.dash-graph')).toBeVisible();

  // Step 6: Verify no errors in console
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });

  expect(consoleErrors).toHaveLength(0);
});
```

#### Quality Gate: Epic 6
- **PASS Criteria:**
  - All cross-tenant isolation attack tests pass (no data leakage)
  - Critical path E2E test passes end-to-end
  - Test coverage >80% for security-critical code paths
  - All quality gates from previous epics remain PASS
- **CONCERNS Criteria:**
  - Security tests pass but edge cases not fully covered
  - E2E test passes but requires multiple retries due to timing issues
- **FAIL Criteria:**
  - Any cross-tenant isolation attack succeeds (data leakage detected)
  - Critical path E2E test fails at any step
  - JWT signature validation not working consistently

---

## 5. Non-Functional Requirements Assessment

### 5.1 Security NFRs

| NFR | Scenario | Validation Method | Pass Criteria |
|-----|----------|-------------------|---------------|
| **Hard Tenant Isolation** | User with T1 token attempts to access T2 data via API manipulation | Security test suite (test_tenant_isolation.py) | All attacks return 403 Forbidden; no T2 data in any response |
| **JWT Signature Validation** | Modified JWT token used in API request | Unit test + E2E attempt | 401 Unauthorized; "Invalid token signature" error |
| **Token Storage Security** | Client-side JavaScript attempts to access tenant token | Browser DevTools inspection + E2E test | Token stored in HTTP-only cookie; not accessible via document.cookie or localStorage |
| **No Identifiable Enumeration** | Attacker attempts to enumerate tenants via URL guessing | Manual testing + security scan | 403 for unauthorized access (not 404); no tenant list exposed to unauthorized users |

### 5.2 Performance NFRs

| NFR | Scenario | Validation Method | Pass Criteria |
|-----|----------|-------------------|---------------|
| **API Response Time** | GET /api/tenant/{id}/dashboards under normal load | Load test with 10 concurrent users | P95 latency <500ms |
| **Dashboard Load Time** | Time to render Dash app in iframe | E2E test with performance timing | Initial render <3 seconds |
| **Token Exchange Latency** | POST /api/token/exchange performance | Integration test with timing | P99 latency <200ms |

**Note:** Performance is LOW priority for PoC (local deployment, small datasets). These metrics are guidance for MVP.

### 5.3 Testability NFRs

| NFR | Scenario | Validation Method | Pass Criteria |
|-----|----------|-------------------|---------------|
| **Observable JWT Claims** | Developer needs to debug token exchange issue | Debug panel in Shell UI shows decoded JWT claims | JWT payload visible without manual decoding; includes tenant_id, role, exp |
| **Seedable Test Data** | Reset database to clean state for E2E tests | Database seed script execution time | Seed completes in <5 seconds; idempotent (can run multiple times) |
| **API Error Clarity** | API returns error due to tenant mismatch | Error response inspection | Error includes code (TENANT_MISMATCH), message, details, and request_id for log correlation |

---

## 6. Quality Gates & Decision Framework

### 6.1 Advisory Gate Model

Quinn provides **advisory quality decisions** using a four-tier gate system:

- **PASS:** All critical criteria met; ready to proceed
- **CONCERNS:** Core functionality works but has non-blocking issues; document concerns and proceed
- **FAIL:** Critical defects present; must fix before proceeding
- **WAIVED:** Documented tradeoff or PoC simplification; accepted risk

### 6.2 Epic-Level Quality Gates

| Epic | Gate Criteria | Decision | Notes |
|------|---------------|----------|-------|
| **Epic 1** | Shared config module imported consistently across all services | 🟢 PASS / 🟡 CONCERNS / 🔴 FAIL | Gate opens Epic 2 |
| **Epic 2** | Token exchange validates tenant access; JWT signature validation works | 🟢 PASS / 🔴 FAIL | CRITICAL: Security foundation |
| **Epic 3** | Tenant selector shows only authorized tenants; token exchange triggered on selection | 🟢 PASS / 🟡 CONCERNS | UI bugs can be CONCERNS |
| **Epic 4** | Dash apps validate JWT and load tenant-scoped data only | 🟢 PASS / 🔴 FAIL | CRITICAL: Data isolation |
| **Epic 5** | Reverse proxy injects Authorization header; tokens in HTTP-only cookies | 🟢 PASS / 🔴 FAIL | CRITICAL: Token security |
| **Epic 6** | All cross-tenant isolation attacks fail; critical path E2E passes | 🟢 PASS / 🔴 FAIL | CRITICAL: PoC validation |

### 6.3 Gate Decision Process

1. **Run Test Suite** for completed epic
2. **Analyze Results** against gate criteria
3. **Assess Risk** using probability × impact matrix
4. **Make Decision:**
   - **PASS:** All critical tests pass, no high-risk failures
   - **CONCERNS:** Non-critical issues documented, workarounds available
   - **FAIL:** Critical tests fail or high-risk security issues present
   - **WAIVED:** Known PoC limitation, explicitly documented in architecture
5. **Document Rationale** in gate decision file (see Section 6.4)
6. **Communicate to Team** with recommended actions

### 6.4 Gate Decision File Format

```yaml
# Example: docs/qa/gates/epic-2-token-exchange.yml
epic: Epic 2 - Mock Authentication & Token Exchange
decision: PASS
timestamp: 2025-10-07T14:30:00Z
reviewer: Quinn (Test Architect)

criteria:
  critical:
    - id: JWT_VALIDATION
      description: JWT signature validation rejects tampered tokens
      status: PASS
      evidence: test_jwt_validation.py::test_jwt_validation_rejects_tampered_token PASSED
    - id: TENANT_ACCESS_CHECK
      description: Token exchange validates user has access to requested tenant
      status: PASS
      evidence: test_token_exchange.py::test_token_exchange_rejects_unauthorized_tenant PASSED
    - id: SCOPED_TOKEN_STRUCTURE
      description: Tenant-scoped token contains single tenant_id and role
      status: PASS
      evidence: test_token_exchange.py::test_tenant_scoped_token_structure PASSED

  non_critical:
    - id: ERROR_FORMAT_CONSISTENCY
      description: Error responses follow standard format
      status: CONCERNS
      evidence: Some endpoints return different error structures
      mitigation: Document standard format; update in Epic 6 if time permits

rationale: |
  All critical security criteria met. Token exchange correctly validates tenant access
  and issues properly structured tenant-scoped tokens. JWT signature validation works
  consistently across all services (shared config module validated).

  Minor concerns about error response consistency, but this does not block progression
  as core security mechanisms are sound.

recommendations:
  - Proceed to Epic 3 (Shell UI & Tenant Selection)
  - Create ticket to standardize error responses in Epic 6
  - Add integration test for error format consistency

risk_assessment:
  residual_risk: LOW
  confidence: HIGH
```

---

## 7. Test Infrastructure

### 7.1 Test Environments

| Environment | Purpose | Configuration | Data State |
|-------------|---------|---------------|------------|
| **Local Dev** | Developer testing during implementation | Docker Compose with hot reload | Seed data from schema.sql |
| **CI/CD (Future)** | Automated test execution on PR | GitHub Actions with Docker Compose | Fresh seed data per run |
| **E2E Test** | Playwright E2E tests | Docker Compose with all services | Seed data + test-specific fixtures |

### 7.2 Test Data Management

#### Seed Data Strategy
- **Source:** `database/schema.sql` with inline INSERT statements
- **Tenants:** 2 mock tenants (Acme Corporation, Beta Industries)
- **Users:** 3 mock users with different access patterns
- **Dashboards:** 2 dashboard definitions (CLV, Risk Analysis)
- **Reset:** Run `python scripts/seed-database.py` to reset to clean state

#### Test Fixtures
```python
# pytest fixtures for common test data
@pytest.fixture
def tenant_t1_id():
    return "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"

@pytest.fixture
def tenant_t2_id():
    return "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4"

@pytest.fixture
def user_token_t1_only():
    """User access token for analyst@acme.com (T1 access only)"""
    return create_user_access_token(
        user_id="f8d1e2c3-4b5a-6789-abcd-ef1234567890",
        email="analyst@acme.com",
        tenant_ids=["8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"]
    )

@pytest.fixture
def user_token_multi_tenant():
    """User access token for admin@acme.com (T1 and T2 access)"""
    return create_user_access_token(
        user_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        email="admin@acme.com",
        tenant_ids=["8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345", "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4"]
    )
```

### 7.3 Test Execution Commands

```bash
# Backend unit tests
cd apps/api && pytest

# Frontend unit tests
cd apps/shell-ui && npm run test

# Integration tests
cd tests && pytest integration/

# E2E tests
npm run test:e2e

# Security-specific tests
pytest -m security

# Run all tests with coverage
pytest --cov=apps/api --cov-report=html
npm run test:coverage
```

---

## 8. Test Data Strategy

### 8.1 Mock Data Requirements

#### Tenant Data
- **Tenant T1 (Acme):** 100 customer records for CLV dashboard; 50 risk records
- **Tenant T2 (Beta):** 75 customer records for CLV dashboard (if assigned); 40 risk records
- **Format:** CSV files in `data/mock-data/` loaded into Pandas DataFrames at startup
- **Schema:** Each CSV has `tenant_id` column for filtering

#### JWT Test Tokens
```python
# Pre-generated tokens for consistent testing
TEST_TOKENS = {
    "user_t1_viewer": create_user_access_token(
        user_id="f8d1e2c3-4b5a-6789-abcd-ef1234567890",
        email="analyst@acme.com",
        tenant_ids=["8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"]
    ),
    "user_multi_admin": create_user_access_token(
        user_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        email="admin@acme.com",
        tenant_ids=["8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345", "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4"]
    ),
    "tenant_t1_viewer": create_tenant_scoped_token(
        tenant_id="8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
        role="viewer",
        user_id="f8d1e2c3-4b5a-6789-abcd-ef1234567890",
        email="analyst@acme.com"
    ),
    "expired_token": create_tenant_scoped_token(
        tenant_id="8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
        role="viewer",
        user_id="f8d1e2c3-4b5a-6789-abcd-ef1234567890",
        email="analyst@acme.com",
        exp=int(time.time()) - 3600  # Expired 1 hour ago
    )
}
```

---

## 9. Test Execution Plan

### 9.1 Pre-Epic Testing (Continuous)

**Objective:** Validate foundation as it's built

**Activities:**
- Run unit tests locally during development
- Validate shared-config module imports before committing
- Test database seed script after schema changes

### 9.2 Epic Completion Testing

**Objective:** Quality gate decision for each epic

**Process:**
1. Developer completes epic implementation
2. Developer runs relevant test suite locally (unit + integration)
3. Developer requests Quinn review via `*review {epic}` command
4. Quinn executes comprehensive test suite:
   - Unit tests for epic scope
   - Integration tests for API endpoints
   - Security tests (if applicable)
   - E2E tests for user-facing flows
5. Quinn analyzes results and makes gate decision (PASS/CONCERNS/FAIL/WAIVED)
6. Quinn updates gate decision file in `docs/qa/gates/{epic}.yml`
7. Quinn communicates decision and recommendations to team

### 9.3 Final PoC Validation (Epic 6 Completion)

**Objective:** Comprehensive validation of PoC goals

**Activities:**
1. **Security Validation:**
   - Run full cross-tenant isolation attack test suite
   - Manual penetration testing (token manipulation, enumeration attempts)
   - JWT signature validation tests

2. **E2E Validation:**
   - Critical path E2E test (login → tenant select → dashboard → filters)
   - Token expiry and refresh flow
   - Multi-tenant user switching between tenants

3. **Requirements Validation:**
   - Verify all acceptance criteria from PRD epics met
   - Trace requirements to tests (traceability matrix complete)

4. **Architecture Validation:**
   - Confirm shared config module used consistently
   - Validate reverse proxy pattern working
   - Verify Dash apps integrated with JWT validation

5. **Final Gate Decision:**
   - **PASS:** PoC demonstrates hard tenant isolation; ready for demo
   - **FAIL:** Critical security issues present; must fix before demo

---

## 10. Technical Debt & Improvement Opportunities

### 10.1 Known PoC Limitations (Documented Tradeoffs)

| Limitation | Impact | MVP Migration Required |
|------------|--------|------------------------|
| **Mock Authentication** | No real OIDC flow tested | Replace with Azure AD B2C; test OIDC redirect flow |
| **Tenant Slugs in URLs** | Enables enumeration attacks | Implement opaque token layer; test with non-guessable IDs |
| **Pre-generated JWTs** | No cryptographic signing tested | Implement proper JWT signing; test key rotation |
| **SQLite Database** | No connection pooling/transactions tested | Migrate to PostgreSQL; test connection pooling, RLS |
| **No Observability** | Can't detect runtime issues in demo | Add Prometheus/Grafana; test metric collection |

### 10.2 Test Coverage Gaps (MVP Recommendations)

| Gap | Risk | Recommended Action |
|-----|------|--------------------|
| **Load Testing** | Unknown performance under realistic load | Add locust/k6 tests for 100+ concurrent users |
| **Token Refresh Mechanism** | Refresh logic not fully tested | Add E2E tests for token refresh without page reload |
| **API Pagination** | Large datasets may cause performance issues | Add pagination tests if implemented in MVP |
| **Error Recovery** | Network failures not tested | Add resilience tests (retry logic, timeout handling) |
| **Admin API Security** | No mTLS or admin authentication tested | Add admin API security tests with certificate validation |

### 10.3 Test Infrastructure Improvements (Future)

- **CI/CD Pipeline:** GitHub Actions workflow to run tests on every PR
- **Test Parallelization:** Run unit tests in parallel for faster feedback
- **Visual Regression Testing:** Playwright screenshots for UI consistency
- **Contract Testing:** Pact tests for Frontend ↔ Backend API contracts
- **Mutation Testing:** Verify test suite quality by introducing bugs

---

## Appendix A: Test Case Catalog

### A.1 Unit Tests (Backend)

| Test ID | Test Name | Epic | Priority |
|---------|-----------|------|----------|
| UT-API-001 | test_jwt_config_exports | Epic 1 | CRITICAL |
| UT-API-002 | test_all_services_use_same_jwt_secret | Epic 1 | CRITICAL |
| UT-API-003 | test_mock_login_returns_user_access_token | Epic 2 | CRITICAL |
| UT-API-004 | test_token_exchange_rejects_unauthorized_tenant | Epic 2 | CRITICAL |
| UT-API-005 | test_tenant_scoped_token_structure | Epic 2 | CRITICAL |
| UT-API-006 | test_jwt_validation_rejects_tampered_token | Epic 2 | CRITICAL |
| UT-API-007 | test_tenant_metadata_api_validates_token_tenant_id | Epic 2 | CRITICAL |
| UT-DASH-001 | test_dash_app_validates_jwt_header | Epic 4 | CRITICAL |
| UT-DASH-002 | test_dash_app_rejects_invalid_token | Epic 4 | CRITICAL |
| UT-DASH-003 | test_dash_loads_tenant_specific_data | Epic 4 | HIGH |

### A.2 Unit Tests (Frontend)

| Test ID | Test Name | Epic | Priority |
|---------|-----------|------|----------|
| UT-UI-001 | test_login_form_submits_email | Epic 3 | HIGH |
| UT-UI-002 | test_tenant_selector_shows_only_accessible_tenants | Epic 3 | HIGH |
| UT-UI-003 | test_tenant_selection_triggers_token_exchange | Epic 3 | CRITICAL |
| UT-UI-004 | test_reverse_proxy_injects_authorization_header | Epic 5 | CRITICAL |

### A.3 Integration Tests

| Test ID | Test Name | Epic | Priority |
|---------|-----------|------|----------|
| IT-001 | test_full_token_exchange_flow | Epic 2 | CRITICAL |
| IT-002 | test_dashboard_data_filtered_by_tenant | Epic 4 | CRITICAL |
| IT-003 | test_attack_token_manipulation | Epic 6 | CRITICAL |
| IT-004 | test_attack_direct_tenant_enumeration | Epic 6 | CRITICAL |
| IT-005 | test_attack_dashboard_data_cross_tenant_access | Epic 6 | CRITICAL |

### A.4 E2E Tests

| Test ID | Test Name | Epic | Priority |
|---------|-----------|------|----------|
| E2E-001 | test_user_can_login_and_select_tenant | Epic 3 | CRITICAL |
| E2E-002 | test_embedded_dash_app_loads_successfully | Epic 5 | CRITICAL |
| E2E-003 | test_expired_token_triggers_refresh_and_reload | Epic 5 | HIGH |
| E2E-004 | test_complete_user_journey | Epic 6 | CRITICAL |

---

## Appendix B: Security Test Scenarios

### B.1 Attack Scenario: JWT Token Manipulation

**Attacker Goal:** Modify tenant_id in JWT to access unauthorized tenant data

**Attack Steps:**
1. Attacker authenticates as legitimate user with access to Tenant T1
2. Attacker intercepts valid tenant-scoped token for T1
3. Attacker decodes JWT (public information, not encrypted)
4. Attacker modifies `tenant_id` claim from T1 to T2 in payload
5. Attacker re-encodes payload without re-signing (signature remains from original T1 token)
6. Attacker sends modified token in API request to access T2 data

**Expected System Response:**
- API validates JWT signature using shared JWT_SECRET_KEY
- Signature validation fails (payload changed but signature didn't)
- API returns 401 Unauthorized with error code `INVALID_TOKEN_SIGNATURE`
- No T2 data exposed

**Test Validation:** `test_attack_token_manipulation()` in `test_tenant_isolation.py`

---

### B.2 Attack Scenario: Direct Tenant Enumeration

**Attacker Goal:** Enumerate other tenants' data by guessing tenant IDs in API calls

**Attack Steps:**
1. Attacker authenticates and obtains valid tenant-scoped token for T1
2. Attacker observes T1's UUID in URLs or responses: `8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345`
3. Attacker guesses or brute-forces other tenant UUIDs (e.g., incrementing last digits)
4. Attacker makes API call: `GET /api/tenant/{guessed_T2_uuid}` with valid T1 token
5. Attacker attempts to access T2 metadata or dashboards

**Expected System Response:**
- API extracts `tenant_id` from JWT claims (T1)
- API compares token tenant_id (T1) vs requested tenant ID (T2)
- Mismatch detected
- API returns 403 Forbidden with error code `TENANT_MISMATCH`
- No T2 metadata exposed

**Test Validation:** `test_attack_direct_tenant_enumeration()` in `test_tenant_isolation.py`

---

### B.3 Attack Scenario: Cross-Tenant Dashboard Data Access

**Attacker Goal:** Access dashboard data belonging to another tenant

**Attack Steps:**
1. Attacker authenticates with access to T1
2. Attacker navigates to legitimate T1 dashboard
3. Attacker observes API calls to `/api/dashboards/{slug}/data`
4. Attacker attempts to query data with T1 token, hoping to see T2 data mixed in response
5. Attacker inspects response JSON for records with `tenant_id != T1`

**Expected System Response:**
- FastAPI data API extracts `tenant_id` from JWT claims (T1)
- Data Access Layer queries in-memory DataFrames filtered by `tenant_id == T1`
- Only T1 records returned in response
- No T2 records present in any field

**Test Validation:** `test_attack_dashboard_data_cross_tenant_access()` in `test_tenant_isolation.py`

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **User Access Token** | JWT issued by mock auth containing `tenant_ids` array (multi-tenant access) |
| **Tenant-Scoped Token** | JWT issued by token exchange with single `tenant_id` and `role` (hard isolation) |
| **Token Exchange** | API endpoint that converts user access token → tenant-scoped token after authorization check |
| **Hard Tenant Isolation** | Security pattern where tenant context comes only from JWT claims, never from client input |
| **Shared Config Module** | Python package (`packages/shared-config`) providing consistent JWT validation settings |
| **Reverse Proxy Pattern** | Next.js API routes inject Authorization header from HTTP-only cookie before forwarding to Dash |
| **Quality Gate** | Advisory decision point (PASS/CONCERNS/FAIL/WAIVED) after epic completion |
| **Cross-Tenant Isolation Attack** | Security test where attacker with valid token attempts unauthorized tenant access |
| **Deny-by-Default Tenancy** | Security principle: all API requests validate tenant_id from JWT, never from query params |

---

**End of Test Architecture Document**
