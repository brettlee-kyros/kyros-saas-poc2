# Epic 3 E2E Test Automation

End-to-end test suite for Epic 3 (Shell UI & Tenant Selection) using Playwright.

## 📋 Overview

This E2E test suite automates **60/85** test cases from the Epic 3 manual test script, providing comprehensive coverage of:

- **Story 3.1:** Login Page with Mock Authentication
- **Story 3.2:** Authentication Context and Token Management
- **Story 3.3:** Tenant Selection Page
- **Story 3.4:** Dashboard Listing Page
- **Story 3.5:** JWT Debug Panel Component
- **Integration Tests:** Full user journeys across all stories

**Coverage:** 71% of manual tests automated
**Priority:** Critical path and error scenarios

---

## 🚀 Quick Start

### Prerequisites

- Node.js 20+
- npm 9+
- Docker and Docker Compose (for running services)

### Installation

```bash
# 1. Navigate to shell-ui directory
cd apps/shell-ui

# 2. Install dependencies
npm install

# 3. Install Playwright browsers
npx playwright install

# 4. Verify installation
npx playwright --version
```

### Running Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run tests in UI mode (interactive)
npm run test:e2e:ui

# Run tests in headed mode (see browser)
npm run test:e2e:headed

# Run tests with debugger
npm run test:e2e:debug

# Run specific browser
npm run test:e2e:chromium
npm run test:e2e:firefox
npm run test:e2e:webkit

# View test report
npm run test:e2e:report
```

---

## 📁 Project Structure

```
e2e/
├── fixtures/              # Test data and API mock responses
│   ├── users.json         # Mock user accounts
│   └── api-responses.json # Mock API responses
├── helpers/               # Utility functions
│   ├── auth.helper.ts     # Authentication utilities
│   ├── token.helper.ts    # JWT token manipulation
│   └── api.helper.ts      # API mocking utilities
├── page-objects/          # Page Object Models
│   ├── LoginPage.ts       # Login page POM
│   ├── TenantSelectionPage.ts
│   └── ...
├── tests/                 # Test specifications
│   ├── 3.1-login.spec.ts  # Story 3.1 tests
│   ├── 3.2-auth-context.spec.ts
│   ├── 3.3-tenant-selection.spec.ts
│   ├── 3.4-dashboard-listing.spec.ts
│   ├── 3.5-debug-panel.spec.ts
│   └── integration.spec.ts
└── README.md
```

---

## 🧪 Test Data

### Mock Users

Three mock users are available for testing:

| Email | Tenants | Role | Use Case |
|-------|---------|------|----------|
| analyst@acme.com | 1 (Acme) | Viewer | Single-tenant auto-select |
| admin@acme.com | 2 (Acme, Beta) | Admin | Multi-tenant selection |
| viewer@beta.com | 1 (Beta) | Viewer | Single-tenant isolation |

**Fixture Location:** `e2e/fixtures/users.json`

### API Responses

Mock API responses are defined in `e2e/fixtures/api-responses.json`:

- Login success/failure
- User info with tenant list
- Token exchange
- Dashboard listings

---

## 📝 Writing Tests

### Example: Login Test

```typescript
import { test, expect } from '@playwright/test';
import { LoginPage } from '../page-objects/LoginPage';
import { AuthHelper } from '../helpers/auth.helper';
import { APIHelper } from '../helpers/api.helper';
import users from '../fixtures/users.json';

test.describe('Story 3.1: Login Page', () => {
  let loginPage: LoginPage;
  let authHelper: AuthHelper;
  let apiHelper: APIHelper;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    authHelper = new AuthHelper(page);
    apiHelper = new APIHelper(page);

    await authHelper.clearAuthState();
    await loginPage.goto();
  });

  test('TC-3.1.4 - Valid login succeeds', async ({ page }) => {
    // Mock API
    await apiHelper.mockLoginSuccess(users.analyst.email);

    // Login
    await loginPage.login(users.analyst.email);

    // Assert redirect
    await loginPage.waitForRedirect();
    expect(page.url()).toContain('/');

    // Assert token stored
    const token = await authHelper.getStoredToken();
    expect(token).toBeTruthy();
  });
});
```

---

## 🛠️ Helper Utilities

### AuthHelper

Authentication operations:

```typescript
const authHelper = new AuthHelper(page);

// Login
await authHelper.login('analyst@acme.com');
await authHelper.loginWithQuickSelect('analyst@acme.com');

// Logout
await authHelper.logout();

// Token operations
const token = await authHelper.getStoredToken();
const isAuth = await authHelper.isAuthenticated();
await authHelper.setToken('custom-token');
await authHelper.clearAuthState();
```

### TokenHelper

JWT token manipulation:

```typescript
import { TokenHelper } from '../helpers/token.helper';

// Decode token
const decoded = TokenHelper.decodeJWT(token);

// Extract claims
const email = TokenHelper.getEmail(token);
const role = TokenHelper.getRole(token);
const tenantIds = TokenHelper.getTenantIds(token);
const tenantId = TokenHelper.getTenantId(token);

// Check token type
const isUser = TokenHelper.isUserToken(token);
const isTenant = TokenHelper.isTenantToken(token);

// Check expiry
const isExpired = TokenHelper.isExpired(token);
const secondsLeft = TokenHelper.getTimeUntilExpiry(token);
```

### APIHelper

API mocking:

```typescript
const apiHelper = new APIHelper(page);

// Mock successful responses
await apiHelper.mockLoginSuccess('analyst@acme.com');
await apiHelper.mockUserInfo();
await apiHelper.mockTokenExchange();
await apiHelper.mockDashboards();

// Mock error responses
await apiHelper.mockLoginNotFound();
await apiHelper.mockLoginNetworkError();
await apiHelper.mockTokenExchange403();
await apiHelper.mockTokenExchange401();
await apiHelper.mockDashboards401();

// Utilities
await apiHelper.waitForAPICall('/api/auth/mock-login');
const payload = await apiHelper.captureAPIPayload('/api/auth/mock-login');
await apiHelper.clearMocks();
```

---

## 📊 Test Reports

### HTML Report

After running tests, view the HTML report:

```bash
npm run test:e2e:report
```

The report includes:
- Test results (pass/fail)
- Screenshots of failures
- Videos of failed tests
- Execution traces
- Performance metrics

### CI/CD Integration

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**GitHub Actions:** `.github/workflows/e2e-tests.yml`

**Artifacts:**
- Test reports (retained 30 days)
- Failure videos (retained 7 days)

---

## 🐛 Debugging

### Debug Mode

Run tests with Playwright Inspector:

```bash
npm run test:e2e:debug
```

**Features:**
- Step through tests
- Inspect DOM
- View console logs
- Network requests
- Screenshots at each step

### UI Mode

Run tests in interactive UI mode:

```bash
npm run test:e2e:ui
```

**Features:**
- Visual test explorer
- Watch mode
- Time travel debugging
- Filter by status/browser

### Headed Mode

See browser during test execution:

```bash
npm run test:e2e:headed
```

### Troubleshooting

**Tests failing locally?**

1. Ensure Docker services are running:
   ```bash
   docker-compose up -d
   ```

2. Verify API is healthy:
   ```bash
   curl http://localhost:8000/health
   ```

3. Check Shell UI is running:
   ```bash
   curl http://localhost:3000/login
   ```

4. Clear browser state:
   ```bash
   # Tests automatically clear state in beforeEach
   ```

---

## 🎯 Test Coverage

### Automated Tests

| Story | Manual Tests | Automated | Coverage |
|-------|--------------|-----------|----------|
| 3.1 Login | 15 | 12 | 80% |
| 3.2 Auth Context | 12 | 10 | 83% |
| 3.3 Tenant Selection | 18 | 15 | 83% |
| 3.4 Dashboard Listing | 16 | 13 | 81% |
| 3.5 Debug Panel | 14 | 10 | 71% |
| Integration | 10 | 10 | 100% |
| **TOTAL** | **85** | **70** | **82%** |

**Realistic target:** 60/85 (71%) accounting for effort vs. value

### Manual Tests

15 tests remain manual:
- Visual/UX validation (7 tests)
- Exploratory testing (4 tests)
- One-time verification (4 tests - TypeScript types via linting)

---

## 📚 Best Practices

### Test Organization

1. **One story per file** - Keep tests organized by story
2. **Clear test names** - Include test case ID and description
3. **Use Page Objects** - Abstract UI interactions
4. **Mock at network level** - Use APIHelper for consistent mocking
5. **Independent tests** - Each test should be runnable in isolation

### Test Data

1. **Use fixtures** - Define test data in `fixtures/` directory
2. **Don't hardcode** - Reference fixture data in tests
3. **Clean up** - Clear state in `beforeEach` and `afterEach`

### Assertions

1. **Use Playwright assertions** - Auto-waiting built-in
2. **Descriptive messages** - Make failures easy to debug
3. **Assert critical paths** - Token storage, redirects, API calls

### Error Handling

1. **Screenshot on failure** - Configured automatically
2. **Video on failure** - Configured automatically
3. **Trace on retry** - Playwright traces capture full context

---

## 🔄 CI/CD Workflow

### GitHub Actions

**Trigger:** Push to `main`/`develop`, Pull Requests

**Steps:**
1. Checkout code
2. Setup Node.js 20
3. Start Postgres service
4. Install dependencies
5. Start API service
6. Seed database
7. Install Playwright
8. Run E2E tests (Chromium only for speed)
9. Upload artifacts

**Runtime:** ~10 minutes

**Artifacts:**
- HTML test report (30 days)
- Failure videos (7 days)

---

## 📈 Metrics & Monitoring

### Success Criteria

| Metric | Target | Current |
|--------|--------|---------|
| Automation Coverage | 70% | 71% ✅ |
| Test Execution Time | < 5 min | TBD |
| Flakiness Rate | < 5% | TBD |
| Pass Rate (CI) | > 95% | TBD |
| Maintenance Cost | < 2 hrs/week | TBD |

---

## 🤝 Contributing

### Adding New Tests

1. Create test file in `e2e/tests/` directory
2. Follow naming convention: `{story}-{name}.spec.ts`
3. Use Page Objects for UI interactions
4. Use helpers for common operations
5. Add test to appropriate test suite

### Adding Page Objects

1. Create POM in `e2e/page-objects/` directory
2. Extend from base page object pattern
3. Encapsulate all page interactions
4. Export for use in tests

### Adding Helpers

1. Create helper in `e2e/helpers/` directory
2. Follow single responsibility principle
3. Document all public methods
4. Export for use in tests

---

## 📞 Support

**Documentation:**
- Test Automation Strategy: `docs/qa/epic-3-automation-strategy.md`
- Test Script Validation: `docs/qa/epic-3-test-script-validation-report.md`
- Manual Test Script: `docs/qa/epic-3-qa-test-script.md`

**Playwright Documentation:**
- Official Docs: https://playwright.dev
- API Reference: https://playwright.dev/docs/api/class-test
- Best Practices: https://playwright.dev/docs/best-practices

**Questions?**
- File an issue in the project repository
- Consult Quinn (Test Architect) via `*help` command

---

**Last Updated:** 2025-10-18
**Version:** 1.0
**Author:** Quinn (Test Architect) 🧪

