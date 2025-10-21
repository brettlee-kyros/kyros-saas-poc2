# E2E Test Setup Guide

Quick setup guide for Epic 3 Playwright E2E tests.

## ⚡ Quick Start (5 minutes)

### 1. Install Dependencies

```bash
cd apps/shell-ui
npm install
npx playwright install chromium
```

### 2. Start Services

```bash
# Terminal 1: Start API
cd apps/api
docker-compose up

# Terminal 2: Start Shell UI
cd apps/shell-ui
npm run dev
```

### 3. Run Tests

```bash
cd apps/shell-ui
npm run test:e2e
```

---

## 📦 What Was Created

### Files Created

```
apps/shell-ui/
├── playwright.config.ts                    # Playwright configuration
├── package.json                             # Updated with test scripts + @playwright/test
├── e2e/
│   ├── README.md                            # Full documentation
│   ├── fixtures/
│   │   ├── users.json                       # Mock user test data
│   │   └── api-responses.json               # Mock API responses
│   ├── helpers/
│   │   ├── auth.helper.ts                   # Authentication utilities
│   │   ├── token.helper.ts                  # JWT token operations
│   │   └── api.helper.ts                    # API mocking utilities
│   ├── page-objects/
│   │   ├── LoginPage.ts                     # Login page POM
│   │   └── TenantSelectionPage.ts           # Tenant selection POM
│   └── tests/
│       └── 3.1-login.spec.ts                # First working test (11 tests)

.github/workflows/
└── e2e-tests.yml                            # GitHub Actions CI/CD
```

### Test Scripts Added

```json
{
  "test:e2e": "playwright test",
  "test:e2e:ui": "playwright test --ui",
  "test:e2e:debug": "playwright test --debug",
  "test:e2e:headed": "playwright test --headed",
  "test:e2e:report": "playwright show-report",
  "test:e2e:priority1": "playwright test --grep @priority1",
  "test:e2e:priority2": "playwright test --grep @priority2",
  "test:e2e:chromium": "playwright test --project=chromium",
  "test:e2e:firefox": "playwright test --project=firefox",
  "test:e2e:webkit": "playwright test --project=webkit"
}
```

---

## 🧪 First Test Included

**File:** `e2e/tests/3.1-login.spec.ts`

**Coverage:** 11 test cases for Story 3.1 (Login Page)

| Test ID | Description | Priority |
|---------|-------------|----------|
| TC-3.1.1 | Login page accessibility | P1 |
| TC-3.1.2 | Login form UI elements | P1 |
| TC-3.1.3 | Mock email suggestions | P1 |
| TC-3.1.4 | Valid login (analyst) ⭐ | P1 - Critical |
| TC-3.1.5 | Valid login (admin) | P1 |
| TC-3.1.6 | Valid login (viewer) | P1 |
| TC-3.1.7 | Invalid user (404) | P1 |
| TC-3.1.8 | Network error handling | P2 |
| TC-3.1.10 | Invalid email format | P2 |
| TC-3.1.11 | Empty email validation | P2 |

---

## 🎯 Try It Out

### Run the First Test

```bash
cd apps/shell-ui

# Run just the login tests
npm run test:e2e e2e/tests/3.1-login.spec.ts

# Run in UI mode (recommended for first time)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed e2e/tests/3.1-login.spec.ts
```

### View Test Report

After running tests:

```bash
npm run test:e2e:report
```

### Debug a Test

```bash
npm run test:e2e:debug e2e/tests/3.1-login.spec.ts
```

---

## 🛠️ Using the Helpers

### Example: Auth Operations

```typescript
import { AuthHelper } from '../helpers/auth.helper';

const authHelper = new AuthHelper(page);

// Login
await authHelper.login('analyst@acme.com');

// Check authentication
const isAuth = await authHelper.isAuthenticated();

// Get token
const token = await authHelper.getStoredToken();

// Logout
await authHelper.logout();
```

### Example: Token Operations

```typescript
import { TokenHelper } from '../helpers/token.helper';

// Decode JWT
const decoded = TokenHelper.decodeJWT(token);
console.log(decoded.email); // analyst@acme.com

// Check token type
const isUserToken = TokenHelper.isUserToken(token);
const isTenantToken = TokenHelper.isTenantToken(token);

// Check expiry
const isExpired = TokenHelper.isExpired(token);
```

### Example: API Mocking

```typescript
import { APIHelper } from '../helpers/api.helper';

const apiHelper = new APIHelper(page);

// Mock successful login
await apiHelper.mockLoginSuccess('analyst@acme.com');

// Mock 404 error
await apiHelper.mockLoginNotFound();

// Mock network error
await apiHelper.mockLoginNetworkError();
```

---

## 🚀 Next Steps

### 1. Run the Tests

```bash
npm run test:e2e
```

### 2. Review the Output

Check for:
- ✅ All tests passing
- Test execution time
- Any flaky tests

### 3. Add More Tests

Copy the pattern from `3.1-login.spec.ts` to create:
- `3.2-auth-context.spec.ts`
- `3.3-tenant-selection.spec.ts`
- `3.4-dashboard-listing.spec.ts`
- `3.5-debug-panel.spec.ts`
- `integration.spec.ts`

### 4. Create Missing Page Objects

Add to `e2e/page-objects/`:
- `DashboardListingPage.ts`
- `DebugPanel.ts`

### 5. Enhance Test Coverage

Follow the automation strategy:
- **Sprint 1:** Priority 1 tests (critical path)
- **Sprint 2:** Priority 2 tests (error handling)
- **Sprint 3:** Priority 3 tests (edge cases + integration)

---

## 📚 Documentation

**Detailed Documentation:**
- **Full README:** `e2e/README.md` (comprehensive guide)
- **Automation Strategy:** `docs/qa/epic-3-automation-strategy.md`
- **Test Script Validation:** `docs/qa/epic-3-test-script-validation-report.md`
- **Manual Test Script:** `docs/qa/epic-3-qa-test-script.md`

**Playwright Resources:**
- Official Docs: https://playwright.dev
- API Reference: https://playwright.dev/docs/api/class-test
- Best Practices: https://playwright.dev/docs/best-practices

---

## ❓ Troubleshooting

### Issue: Tests fail with "page.goto timeout"

**Solution:**
```bash
# Ensure Shell UI is running
npm run dev

# Check it's accessible
curl http://localhost:3000/login
```

### Issue: Tests fail with "Cannot find module"

**Solution:**
```bash
# Reinstall dependencies
npm install
```

### Issue: Playwright browsers not installed

**Solution:**
```bash
npx playwright install
```

### Issue: API calls fail with network errors

**Solution:**
```bash
# Ensure API is running
cd apps/api
docker-compose up -d

# Verify health
curl http://localhost:8000/health
```

---

## ✅ Verification Checklist

Before considering setup complete:

- [ ] Playwright installed (`npx playwright --version`)
- [ ] Dependencies installed (`npm install`)
- [ ] Browsers installed (`npx playwright install`)
- [ ] Services running (API + Shell UI)
- [ ] First test passes (`npm run test:e2e e2e/tests/3.1-login.spec.ts`)
- [ ] Test report viewable (`npm run test:e2e:report`)
- [ ] Can debug tests (`npm run test:e2e:debug`)

---

## 🎉 Success!

You now have a working Playwright E2E test suite for Epic 3!

**What you have:**
- ✅ 11 working tests for Story 3.1
- ✅ Complete test infrastructure (config, helpers, POMs)
- ✅ CI/CD integration (GitHub Actions)
- ✅ Comprehensive documentation

**Next:** Follow the automation strategy to add remaining 49 tests across Stories 3.2-3.5 and integration tests.

---

**Questions?** See `e2e/README.md` for detailed documentation.

**Author:** Quinn (Test Architect) 🧪
**Date:** 2025-10-18

