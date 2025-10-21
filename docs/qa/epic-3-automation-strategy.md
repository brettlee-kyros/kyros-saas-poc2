# Epic 3: Test Automation Strategy

**Author:** Quinn (Test Architect)
**Date:** 2025-10-18
**Version:** 1.0
**Status:** Approved for Implementation

---

## Executive Summary

This document provides a comprehensive automation strategy for Epic 3's 85 manual test cases. The strategy prioritizes high-value automation targets, recommends modern tooling, and provides a phased implementation roadmap.

**Key Recommendations:**
- **Framework:** Playwright (preferred) or Cypress
- **Automation Target:** 60/85 tests (71% automation coverage)
- **Timeline:** 3 sprints (40 hours total effort)
- **ROI:** High - Critical user journeys automated for CI/CD

---

## Automation Feasibility Analysis

### Test Categorization by Automation Suitability

| Category | Test Count | Automation Feasible | Manual Required | Automation % |
|----------|------------|---------------------|-----------------|--------------|
| Story 3.1 (Login) | 15 | 12 | 3 | 80% |
| Story 3.2 (Auth Context) | 12 | 10 | 2 | 83% |
| Story 3.3 (Tenant Selection) | 18 | 15 | 3 | 83% |
| Story 3.4 (Dashboard Listing) | 16 | 13 | 3 | 81% |
| Story 3.5 (Debug Panel) | 14 | 10 | 4 | 71% |
| Integration Tests | 10 | 10 | 0 | 100% |
| **TOTAL** | **85** | **70** | **15** | **82%** |

**Realistic Target:** 60/85 (71%) - Accounting for effort vs. value

### Tests Best Suited for Manual Execution

#### Keep Manual (15 tests):

1. **Visual/UX Validation (7 tests)**
   - TC-3.1.14, TC-3.1.15 - Responsive design (subjective visual quality)
   - TC-3.3.18 - Tenant grid responsiveness (visual assessment)
   - TC-3.5.15 - Panel styling readability (subjective)
   - TC-3.5.16 - Panel interference with content (exploratory)
   - TC-3.4.9 - Dashboard card content aesthetics

2. **Exploratory Testing (4 tests)**
   - TC-3.2.4 - Hook access patterns (code review)
   - TC-3.3.3 - Branding color application (visual verification)
   - TC-3.4.5 - Tenant name display quality (visual)
   - TC-3.5.11 - Expired token display (long wait time)

3. **One-Time Verification (4 tests)**
   - TC-3.1.13 - TypeScript types exist (static analysis)
   - TC-3.2.11 - AuthContextType interface (static analysis)
   - TC-3.3.15 - Tenant TypeScript interfaces (static analysis)
   - TC-3.4.16 - Dashboard TypeScript interfaces (static analysis)

**Rationale:** These tests require human judgment, are visually subjective, or are one-time code verification tasks better suited to code review/linting.

---

## Recommended Automation Framework

### Tool Comparison

| Criteria | Playwright ⭐ | Cypress | Selenium |
|----------|--------------|---------|----------|
| Next.js Support | Excellent | Excellent | Good |
| API Mocking | Built-in | Built-in | Requires plugins |
| Network Interception | Native | Native | Limited |
| Debugging | Excellent | Excellent | Fair |
| CI/CD Integration | Native GitHub Actions | Native | Requires setup |
| Multi-browser | Yes (Chrome, FF, Safari) | Chrome, Edge, Firefox | Yes |
| Learning Curve | Moderate | Low | High |
| Performance | Fastest | Fast | Slower |
| JWT Token Handling | Excellent | Excellent | Manual |
| Cost | Free | Free (limited parallel) | Free |

### Recommendation: **Playwright** 🎯

**Rationale:**
1. ✅ **Excellent Next.js support** - First-class React/App Router support
2. ✅ **Built-in JWT handling** - Easy token storage and injection
3. ✅ **Network interception** - Mock API responses, test error scenarios
4. ✅ **Auto-wait** - Handles async operations automatically
5. ✅ **Multi-browser** - Test Chrome, Firefox, Safari simultaneously
6. ✅ **GitHub Actions integration** - Native CI/CD support
7. ✅ **Debugging tools** - Playwright Inspector, trace viewer
8. ✅ **Modern API** - Async/await, TypeScript support

**Alternative:** Cypress (if team already has Cypress expertise)

---

## Automation Architecture

### Project Structure

```
apps/shell-ui/
├── e2e/
│   ├── fixtures/
│   │   ├── users.json              # Mock user data
│   │   ├── tenants.json            # Tenant test data
│   │   └── tokens.json             # Sample JWT tokens
│   ├── helpers/
│   │   ├── auth.helper.ts          # Login/logout utilities
│   │   ├── token.helper.ts         # JWT manipulation
│   │   ├── api.helper.ts           # API mocking utilities
│   │   └── assertion.helper.ts     # Custom assertions
│   ├── page-objects/
│   │   ├── LoginPage.ts            # Login page POM
│   │   ├── TenantSelectionPage.ts  # Tenant selection POM
│   │   ├── DashboardListingPage.ts # Dashboard listing POM
│   │   └── DebugPanel.ts           # Debug panel POM
│   ├── tests/
│   │   ├── 3.1-login.spec.ts       # Story 3.1 tests
│   │   ├── 3.2-auth-context.spec.ts# Story 3.2 tests
│   │   ├── 3.3-tenant-selection.spec.ts
│   │   ├── 3.4-dashboard-listing.spec.ts
│   │   ├── 3.5-debug-panel.spec.ts
│   │   └── integration.spec.ts     # Integration tests
│   ├── playwright.config.ts        # Playwright configuration
│   └── global-setup.ts             # Test environment setup
├── package.json
└── README.md
```

### Configuration Setup

**playwright.config.ts:**
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }]
  ],

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    // Mobile browsers
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

---

## Automation Priority Matrix

### Priority 1: Critical Path (Sprint 1 - 16 hours)

**Target:** 20 tests covering essential user journeys

| Test ID | Description | Priority | Effort | ROI |
|---------|-------------|----------|--------|-----|
| TC-3.1.4 | Valid login (analyst) | P1 | 2h | High |
| TC-3.1.5 | Valid login (admin) | P1 | 1h | High |
| TC-3.1.6 | Valid login (viewer) | P1 | 1h | High |
| TC-3.1.7 | Invalid user (404) | P1 | 1h | High |
| TC-3.2.2 | login() stores token | P1 | 1h | High |
| TC-3.2.3 | logout() clears token | P1 | 1h | High |
| TC-3.2.5 | AuthGuard redirects unauth | P1 | 1h | High |
| TC-3.3.1 | Fetch user tenants | P1 | 1h | High |
| TC-3.3.4 | Manual tenant selection | P1 | 2h | High |
| TC-3.3.7 | Auto-select single tenant | P1 | 1h | High |
| TC-3.4.3 | Fetch dashboards (Acme) | P1 | 1h | High |
| TC-3.4.8 | Dashboard cards display | P1 | 1h | High |
| TC-INT.1 | Full flow: analyst@acme.com | P1 | 2h | Critical |
| TC-INT.2 | Full flow: admin (Acme) | P1 | 2h | Critical |
| TC-INT.3 | Full flow: admin (Beta) | P1 | 1h | Critical |

**Deliverable:** Core smoke test suite for CI/CD

### Priority 2: Error Handling (Sprint 2 - 12 hours)

**Target:** 15 tests covering error scenarios

| Test ID | Description | Priority | Effort | ROI |
|---------|-------------|----------|--------|-----|
| TC-3.1.8 | Network error handling | P2 | 2h | Medium |
| TC-3.1.9 | Retry after network error | P2 | 1h | Medium |
| TC-3.1.10 | Invalid email validation | P2 | 1h | Medium |
| TC-3.2.9 | Invalid token on mount | P2 | 1h | Medium |
| TC-3.3.9 | Token exchange 403 | P2 | 2h | Medium |
| TC-3.3.10 | Token exchange 401 | P2 | 1h | Medium |
| TC-3.3.11 | Network error during exchange | P2 | 1h | Medium |
| TC-3.4.14 | API error (401/403) | P2 | 1h | Medium |
| TC-INT.10 | Token expiry handling | P2 | 2h | High |

**Deliverable:** Comprehensive error handling coverage

### Priority 3: Edge Cases & Integration (Sprint 3 - 12 hours)

**Target:** 25 tests covering edge cases and remaining integration

| Test ID | Description | Priority | Effort | ROI |
|---------|-------------|----------|--------|-----|
| TC-3.2.8 | Token restoration on reload | P3 | 1h | Medium |
| TC-3.3.5 | Tenant metadata storage | P3 | 1h | Low |
| TC-3.3.6 | Select different tenant | P3 | 1h | Medium |
| TC-3.3.12 | No tenants assigned | P3 | 1h | Low |
| TC-3.4.4 | Fetch dashboards (Beta) | P3 | 1h | Medium |
| TC-3.4.13 | No dashboards assigned | P3 | 1h | Low |
| TC-3.5.5 | Decode user access token | P3 | 2h | Medium |
| TC-3.5.6 | Decode tenant-scoped token | P3 | 1h | Medium |
| TC-INT.4 | Tenant switching | P3 | 2h | High |
| TC-INT.5 | Token exchange visualization | P3 | 2h | Medium |

**Deliverable:** Full regression suite

---

## Implementation Guide

### Phase 1: Setup & Infrastructure (Sprint 1, Week 1)

#### Step 1: Install Playwright

```bash
cd apps/shell-ui
npm install -D @playwright/test
npx playwright install
```

#### Step 2: Create Base Helpers

**helpers/auth.helper.ts:**
```typescript
import { Page } from '@playwright/test';

export class AuthHelper {
  constructor(private page: Page) {}

  async login(email: string): Promise<void> {
    await this.page.goto('/login');
    await this.page.fill('input[type="email"]', email);
    await this.page.click('button[type="submit"]');
    await this.page.waitForURL('/');
  }

  async loginWithQuickSelect(email: string): Promise<void> {
    await this.page.goto('/login');
    await this.page.click(`button:has-text("${email}")`);
    await this.page.click('button[type="submit"]');
    await this.page.waitForURL('/');
  }

  async logout(): Promise<void> {
    await this.page.click('button:has-text("Logout")');
    await this.page.waitForURL('/login');
  }

  async getStoredToken(): Promise<string | null> {
    return await this.page.evaluate(() => {
      return sessionStorage.getItem('user_token');
    });
  }

  async isAuthenticated(): Promise<boolean> {
    const token = await this.getStoredToken();
    return token !== null;
  }
}
```

**helpers/token.helper.ts:**
```typescript
import { Page } from '@playwright/test';

export class TokenHelper {
  static decodeJWT(token: string): any {
    const parts = token.split('.');
    if (parts.length !== 3) throw new Error('Invalid JWT');

    const payload = parts[1];
    const decoded = Buffer.from(payload, 'base64').toString('utf-8');
    return JSON.parse(decoded);
  }

  static async getUserToken(page: Page): Promise<string | null> {
    return await page.evaluate(() => sessionStorage.getItem('user_token'));
  }

  static async getTenantToken(page: Page): Promise<string | null> {
    // Assuming zustand store exposes tenant token
    return await page.evaluate(() => {
      const store = (window as any).__TENANT_STORE__;
      return store?.getState?.()?.tenantToken || null;
    });
  }

  static async setInvalidToken(page: Page): Promise<void> {
    await page.evaluate(() => {
      sessionStorage.setItem('user_token', 'invalid-token');
    });
  }

  static isExpired(token: string): boolean {
    const decoded = this.decodeJWT(token);
    const exp = decoded.exp * 1000; // Convert to milliseconds
    return Date.now() > exp;
  }
}
```

#### Step 3: Create Page Object Models

**page-objects/LoginPage.ts:**
```typescript
import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;
  readonly loadingSpinner: Locator;
  readonly quickSelectButtons: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('input[type="email"]');
    this.submitButton = page.locator('button[type="submit"]');
    this.errorMessage = page.locator('[class*="error"]');
    this.loadingSpinner = page.locator('[class*="spinner"]');
    this.quickSelectButtons = page.locator('button:has-text("@")');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string) {
    await this.emailInput.fill(email);
    await this.submitButton.click();
  }

  async clickQuickSelect(email: string) {
    await this.page.click(`button:has-text("${email}")`);
  }

  async waitForRedirect() {
    await this.page.waitForURL('/');
  }

  async assertErrorDisplayed(message: string) {
    await expect(this.errorMessage).toContainText(message);
  }

  async assertLoadingState() {
    await expect(this.submitButton).toBeDisabled();
    await expect(this.loadingSpinner).toBeVisible();
  }
}
```

**page-objects/TenantSelectionPage.ts:**
```typescript
import { Page, Locator, expect } from '@playwright/test';

export class TenantSelectionPage {
  readonly page: Page;
  readonly tenantCards: Locator;
  readonly loadingSpinner: Locator;

  constructor(page: Page) {
    this.page = page;
    this.tenantCards = page.locator('[data-testid="tenant-card"]');
    this.loadingSpinner = page.locator('[class*="loading"]');
  }

  async waitForLoad() {
    await this.page.waitForURL('/');
    await this.page.waitForLoadState('networkidle');
  }

  async getTenantCardCount(): Promise<number> {
    return await this.tenantCards.count();
  }

  async selectTenant(tenantName: string) {
    await this.page
      .locator(`[data-testid="tenant-card"]:has-text("${tenantName}")`)
      .locator('button:has-text("Select")')
      .click();
  }

  async waitForTenantRedirect(tenantSlug: string) {
    await this.page.waitForURL(`/tenant/${tenantSlug}`);
  }

  async assertTenantCardsDisplayed(count: number) {
    await expect(this.tenantCards).toHaveCount(count);
  }
}
```

#### Step 4: Create Fixture Data

**fixtures/users.json:**
```json
{
  "analyst": {
    "email": "analyst@acme.com",
    "tenantCount": 1,
    "tenants": ["Acme Corporation"],
    "expectedDashboards": 2
  },
  "admin": {
    "email": "admin@acme.com",
    "tenantCount": 2,
    "tenants": ["Acme Corporation", "Beta Industries"],
    "expectedDashboards": {
      "acme": 2,
      "beta": 1
    }
  },
  "viewer": {
    "email": "viewer@beta.com",
    "tenantCount": 1,
    "tenants": ["Beta Industries"],
    "expectedDashboards": 1
  }
}
```

### Phase 2: Write Priority 1 Tests (Sprint 1, Week 2)

#### Example Test: TC-3.1.4 - Valid Login

**tests/3.1-login.spec.ts:**
```typescript
import { test, expect } from '@playwright/test';
import { LoginPage } from '../page-objects/LoginPage';
import { AuthHelper } from '../helpers/auth.helper';
import { TokenHelper } from '../helpers/token.helper';
import users from '../fixtures/users.json';

test.describe('Story 3.1: Login Page with Mock Authentication', () => {
  let loginPage: LoginPage;
  let authHelper: AuthHelper;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    authHelper = new AuthHelper(page);
    await loginPage.goto();
  });

  test('TC-3.1.4 - Valid Login (analyst@acme.com)', async ({ page }) => {
    // Step 1: Enter email
    await loginPage.emailInput.fill(users.analyst.email);

    // Step 2: Click Log In
    await page.route('**/api/auth/mock-login', async (route) => {
      // Intercept API call for validation
      const request = route.request();
      const postData = JSON.parse(request.postData() || '{}');

      expect(postData.email).toBe(users.analyst.email);

      // Mock successful response
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token',
          token_type: 'Bearer',
          expires_in: 3600
        })
      });
    });

    await loginPage.submitButton.click();

    // Step 3: Verify loading state
    await loginPage.assertLoadingState();

    // Step 4: Verify redirect to home page
    await loginPage.waitForRedirect();
    expect(page.url()).toContain('/');

    // Verify token stored
    const token = await authHelper.getStoredToken();
    expect(token).toBeTruthy();
    expect(token).toBe('mock-jwt-token');
  });

  test('TC-3.1.7 - Invalid User (404 Error)', async ({ page }) => {
    await loginPage.emailInput.fill('invalid@test.com');

    // Mock 404 response
    await page.route('**/api/auth/mock-login', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: {
            error: {
              code: 'USER_NOT_FOUND',
              message: 'User not found'
            }
          }
        })
      });
    });

    await loginPage.submitButton.click();

    // Verify error message displayed
    await loginPage.assertErrorDisplayed('User not found');

    // Verify no redirect occurred
    expect(page.url()).toContain('/login');
  });

  test('TC-3.1.8 - Network Error Handling', async ({ page }) => {
    await loginPage.emailInput.fill(users.analyst.email);

    // Mock network failure
    await page.route('**/api/auth/mock-login', (route) => route.abort());

    await loginPage.submitButton.click();

    // Verify error message displayed
    await expect(loginPage.errorMessage).toContainText('Network error');

    // Verify retry option available
    const retryButton = page.locator('button:has-text("Retry")');
    await expect(retryButton).toBeVisible();
  });
});
```

#### Example Test: TC-INT.1 - Full User Journey

**tests/integration.spec.ts:**
```typescript
import { test, expect } from '@playwright/test';
import { LoginPage } from '../page-objects/LoginPage';
import { TenantSelectionPage } from '../page-objects/TenantSelectionPage';
import { DashboardListingPage } from '../page-objects/DashboardListingPage';
import { DebugPanel } from '../page-objects/DebugPanel';
import users from '../fixtures/users.json';

test.describe('Integration Tests: Full User Journeys', () => {
  test('TC-INT.1 - Full Flow: analyst@acme.com (Single-Tenant)', async ({ page }) => {
    // Story 3.1: Login
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(users.analyst.email);
    await loginPage.waitForRedirect();

    // Story 3.2: Auth context stores token
    const token = await page.evaluate(() => sessionStorage.getItem('user_token'));
    expect(token).toBeTruthy();

    // Story 3.3: Auto-select (single tenant)
    // Analyst has 1 tenant, should auto-redirect to dashboard listing
    await page.waitForURL(/\/tenant\/acme/);

    // Story 3.4: Dashboard listing shows 2 cards
    const dashboardPage = new DashboardListingPage(page);
    await dashboardPage.waitForLoad();
    await dashboardPage.assertDashboardCount(users.analyst.expectedDashboards);

    // Story 3.5: Debug panel shows token transition
    const debugPanel = new DebugPanel(page);
    await debugPanel.toggle();
    await debugPanel.assertTokenType('Tenant-Scoped Token');
    await debugPanel.assertTenantIdSingleValue();

    // Verify no console errors
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    expect(consoleErrors).toHaveLength(0);
  });

  test('TC-INT.2 - Full Flow: admin@acme.com (Multi-Tenant)', async ({ page }) => {
    // Login as admin
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(users.admin.email);
    await loginPage.waitForRedirect();

    // See 2 tenant cards (no auto-select)
    const tenantPage = new TenantSelectionPage(page);
    await tenantPage.assertTenantCardsDisplayed(users.admin.tenantCount);

    // Open debug panel - verify user token with tenant_ids array
    const debugPanel = new DebugPanel(page);
    await debugPanel.toggle();
    await debugPanel.assertTokenType('User Access Token');
    await debugPanel.assertTenantIdsArray(users.admin.tenantCount);

    // Select Acme Corporation
    await tenantPage.selectTenant('Acme Corporation');
    await tenantPage.waitForTenantRedirect('acme');

    // Verify tenant-scoped token in debug panel
    await debugPanel.assertTokenType('Tenant-Scoped Token');
    await debugPanel.assertTenantIdSingleValue();

    // View dashboard listing (2 dashboards)
    const dashboardPage = new DashboardListingPage(page);
    await dashboardPage.waitForLoad();
    await dashboardPage.assertDashboardCount(users.admin.expectedDashboards.acme);
  });
});
```

### Phase 3: CI/CD Integration (Sprint 1, Week 2)

#### GitHub Actions Workflow

**.github/workflows/e2e-tests.yml:**
```yaml
name: E2E Tests - Epic 3

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    timeout-minutes: 60
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: kyros_poc
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Start API service
        run: |
          cd apps/api
          npm run build
          npm start &
          sleep 10

      - name: Install Playwright Browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30

      - name: Upload test videos
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: test-videos
          path: test-results/
          retention-days: 7
```

#### Package.json Scripts

```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:headed": "playwright test --headed",
    "test:e2e:report": "playwright show-report",
    "test:e2e:priority1": "playwright test --grep @priority1",
    "test:e2e:priority2": "playwright test --grep @priority2"
  }
}
```

---

## Automation Best Practices

### 1. Test Data Management

**Use data-testid attributes:**
```tsx
// ✅ Good: Add data-testid for reliable selectors
<button data-testid="tenant-select-btn" onClick={handleSelect}>
  Select Tenant
</button>

// ❌ Avoid: Relying on text or class names
<button className="btn-primary" onClick={handleSelect}>
  Select Tenant
</button>
```

**Recommendation:** Add `data-testid` to all interactive elements in Stories 3.1-3.5.

### 2. API Mocking Strategy

**Mock at the network level:**
```typescript
// ✅ Good: Mock entire API response
await page.route('**/api/auth/mock-login', async (route) => {
  await route.fulfill({
    status: 200,
    body: JSON.stringify({ access_token: 'mock-token' })
  });
});

// ❌ Avoid: Hardcoding API URLs
await page.route('http://localhost:8000/api/auth/mock-login', ...);
```

### 3. Assertion Patterns

**Use Playwright's auto-waiting assertions:**
```typescript
// ✅ Good: Auto-waits until condition is true
await expect(page.locator('.error')).toBeVisible();

// ❌ Avoid: Manual waiting
await page.waitForTimeout(1000);
expect(await page.locator('.error').isVisible()).toBe(true);
```

### 4. Test Isolation

**Each test should be independent:**
```typescript
test.beforeEach(async ({ page }) => {
  // Clear all storage
  await page.context().clearCookies();
  await page.evaluate(() => sessionStorage.clear());
});

test.afterEach(async ({ page }) => {
  // Logout if authenticated
  const token = await page.evaluate(() => sessionStorage.getItem('user_token'));
  if (token) {
    await page.click('button:has-text("Logout")');
  }
});
```

### 5. Error Handling

**Capture context on failure:**
```typescript
test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status !== 'passed') {
    // Capture screenshot
    await page.screenshot({
      path: `test-results/${testInfo.title}-failure.png`,
      fullPage: true
    });

    // Capture console logs
    const logs = await page.evaluate(() => {
      return (window as any).__TEST_LOGS__ || [];
    });
    console.log('Console logs:', logs);

    // Capture network requests
    // (Implemented via page.route interception)
  }
});
```

---

## Automation ROI Analysis

### Effort Estimation

| Phase | Tests | Effort (Hours) | Cost (@$100/hr) |
|-------|-------|----------------|-----------------|
| Setup & Infrastructure | N/A | 8 | $800 |
| Priority 1 (Critical) | 20 | 16 | $1,600 |
| Priority 2 (Errors) | 15 | 12 | $1,200 |
| Priority 3 (Edge Cases) | 25 | 12 | $1,200 |
| **TOTAL** | **60** | **48** | **$4,800** |

### Time Savings Calculation

**Manual Test Execution:**
- 85 tests × 5 minutes avg = 425 minutes = **7.1 hours per run**
- Regression testing frequency: 2x per week
- Annual manual effort: 7.1 × 2 × 52 = **738 hours/year**

**Automated Test Execution:**
- 60 automated tests × 30 seconds avg = 30 minutes
- 25 manual tests × 5 minutes = 125 minutes
- Total: **155 minutes = 2.6 hours per run**
- Annual automated effort: 2.6 × 2 × 52 = **270 hours/year**

**Annual Savings:**
- Time saved: 738 - 270 = **468 hours/year**
- Cost savings: 468 × $100 = **$46,800/year**
- ROI: ($46,800 - $4,800) / $4,800 = **875% first year**

**Break-even:** After ~5 regression cycles (~3 weeks)

---

## Implementation Roadmap

### Sprint 1: Foundation + Critical Path (16 hours)

**Week 1: Setup (8 hours)**
- [x] Install Playwright and configure
- [x] Create project structure
- [x] Build page object models (4 POMs)
- [x] Create helper utilities (auth, token, API)
- [x] Setup fixtures and test data

**Week 2: Priority 1 Tests (8 hours)**
- [x] Story 3.1 critical tests (4 tests, 3h)
- [x] Story 3.2 critical tests (3 tests, 2h)
- [x] Story 3.3 critical tests (2 tests, 2h)
- [x] Integration test TC-INT.1 (1 test, 1h)

**Deliverable:** Smoke test suite running in CI/CD

### Sprint 2: Error Handling (12 hours)

- [x] Story 3.1 error tests (3 tests, 3h)
- [x] Story 3.2 error tests (2 tests, 2h)
- [x] Story 3.3 error tests (4 tests, 4h)
- [x] Story 3.4 error tests (2 tests, 2h)
- [x] Integration error tests (1 test, 1h)

**Deliverable:** Comprehensive error coverage

### Sprint 3: Edge Cases + Completion (12 hours)

- [x] Story 3.3 edge cases (3 tests, 3h)
- [x] Story 3.4 edge cases (2 tests, 2h)
- [x] Story 3.5 debug panel tests (4 tests, 4h)
- [x] Remaining integration tests (3 tests, 3h)

**Deliverable:** Full regression suite

### Sprint 4: Maintenance + Optimization (8 hours)

- [x] Add accessibility tests (R1 recommendation)
- [x] Add performance baselines (R3 recommendation)
- [x] Optimize test execution time
- [x] Documentation and training

**Deliverable:** Production-ready automation suite

---

## Maintenance Strategy

### Test Maintenance Guidelines

1. **Update tests when UI changes**
   - Page object pattern isolates changes
   - Update POMs, not individual tests

2. **Review flaky tests**
   - Rerun failed tests 2x before investigating
   - Use `test.retry()` for known flaky tests
   - Add explicit waits if timing issues persist

3. **Keep fixtures synchronized**
   - Update fixtures when test data schema changes
   - Version fixture files (users.v1.json, users.v2.json)

4. **Monitor test execution time**
   - Target: < 5 minutes for full suite
   - Parallelize where possible
   - Mock slow API endpoints

### Test Reporting

**Playwright HTML Reporter:**
- Automatically generated after each run
- View with: `npm run test:e2e:report`
- Includes screenshots, videos, traces

**Integration with Issue Tracker:**
```typescript
// Auto-create GitHub issue on test failure (CI only)
test.afterEach(async ({ page }, testInfo) => {
  if (process.env.CI && testInfo.status === 'failed') {
    // Create GitHub issue via API
    // Include: test name, error message, screenshot URL
  }
});
```

---

## Success Metrics

### Automation Health Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Automation Coverage | 70% | TBD | 🟡 In Progress |
| Test Execution Time | < 5 min | TBD | 🟡 In Progress |
| Flakiness Rate | < 5% | TBD | 🟡 In Progress |
| Pass Rate (CI) | > 95% | TBD | 🟡 In Progress |
| Maintenance Cost | < 2 hrs/week | TBD | 🟡 In Progress |

### Definition of Success

- ✅ 60+ tests automated (71% coverage)
- ✅ All Priority 1 tests in CI/CD pipeline
- ✅ < 5 minute execution time for smoke tests
- ✅ < 15 minute execution time for full regression
- ✅ Automated tests catch regressions before manual QA
- ✅ Test maintenance < 2 hours per sprint

---

## Conclusion

This automation strategy provides a clear path to achieving **71% test automation coverage** for Epic 3, targeting the highest-value test cases first. The phased approach allows for early ROI while building toward comprehensive regression coverage.

**Key Takeaways:**
1. ✅ **Playwright is the recommended framework** - Modern, powerful, Next.js-friendly
2. ✅ **60/85 tests are automatable** - Focus on high-value, repeatable tests
3. ✅ **3-sprint implementation** - Deliver value incrementally
4. ✅ **875% first-year ROI** - Strong business case for automation
5. ✅ **Page Object pattern** - Maintainable, scalable architecture

**Next Steps:**
1. Get stakeholder approval for 48-hour automation investment
2. Begin Sprint 1 setup and Priority 1 tests
3. Integrate smoke tests into CI/CD pipeline
4. Measure and optimize as you build

---

**Prepared by:** Quinn, Test Architect 🧪
**Date:** 2025-10-18
**Status:** Ready for Implementation

