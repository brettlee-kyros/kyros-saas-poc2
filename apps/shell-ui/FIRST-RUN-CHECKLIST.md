# First Run Checklist - E2E Tests

Use this checklist to verify your E2E test automation setup is working correctly.

---

## ☑️ Prerequisites

- [ ] Node.js 20+ installed (`node --version`)
- [ ] npm 9+ installed (`npm --version`)
- [ ] Docker Desktop running
- [ ] Git repository cloned

---

## ☑️ Installation Steps

### 1. Install Dependencies

```bash
cd apps/shell-ui
npm install
```

**Expected output:** Dependencies installed successfully, no errors

- [ ] ✅ npm install completed without errors

### 2. Install Playwright Browsers

```bash
npx playwright install chromium
```

**Expected output:** Browser binaries downloaded

- [ ] ✅ Chromium browser installed

### 3. Verify Playwright Installation

```bash
npx playwright --version
```

**Expected output:** `Version 1.48.0` (or later)

- [ ] ✅ Playwright version displayed correctly

---

## ☑️ Service Startup

### 4. Start API Service

```bash
# In a separate terminal
cd apps/api
docker-compose up
```

**Wait for:** `Application startup complete` or similar message

- [ ] ✅ API service started successfully

### 5. Verify API Health

```bash
curl http://localhost:8000/health
```

**Expected output:** `{"status":"healthy"}` or similar

- [ ] ✅ API health check passed

### 6. Start Shell UI

```bash
# In another terminal
cd apps/shell-ui
npm run dev
```

**Wait for:** `Ready on http://localhost:3000`

- [ ] ✅ Shell UI started successfully

### 7. Verify Shell UI Accessibility

```bash
curl http://localhost:3000/login
```

**Expected output:** HTML content (not error)

- [ ] ✅ Shell UI accessible

---

## ☑️ Test Execution

### 8. Run First Test

```bash
cd apps/shell-ui
npm run test:e2e e2e/tests/3.1-login.spec.ts
```

**Expected output:** `11 passed` tests

- [ ] ✅ All 11 login tests passed

**If any tests fail, check:**
- Services are running (API + Shell UI)
- No port conflicts (8000, 3000)
- Browser closed before running tests

### 9. View Test Report

```bash
npm run test:e2e:report
```

**Expected:** HTML report opens in browser

- [ ] ✅ Test report viewable
- [ ] ✅ All tests show as "passed" (green)
- [ ] ✅ Screenshots available (if any failures)

---

## ☑️ Interactive Modes

### 10. Try UI Mode

```bash
npm run test:e2e:ui
```

**Expected:** Playwright UI opens with test explorer

- [ ] ✅ UI mode opens
- [ ] ✅ Can see test list
- [ ] ✅ Can run individual tests
- [ ] ✅ Can see test output

### 11. Try Headed Mode

```bash
npm run test:e2e:headed e2e/tests/3.1-login.spec.ts
```

**Expected:** Browser window opens, tests run visibly

- [ ] ✅ Browser visible during test execution
- [ ] ✅ Can see login page interactions
- [ ] ✅ Tests complete successfully

### 12. Try Debug Mode

```bash
npm run test:e2e:debug e2e/tests/3.1-login.spec.ts
```

**Expected:** Playwright Inspector opens

- [ ] ✅ Inspector opens
- [ ] ✅ Can step through test
- [ ] ✅ Can inspect page elements

---

## ☑️ Verify Test Infrastructure

### 13. Check Fixtures Load

```bash
cat e2e/fixtures/users.json
```

**Expected:** JSON with 3 user objects

- [ ] ✅ Fixture file readable
- [ ] ✅ Contains analyst, admin, viewer users

### 14. Check Helpers Exist

```bash
ls e2e/helpers/
```

**Expected:** auth.helper.ts, token.helper.ts, api.helper.ts

- [ ] ✅ All 3 helper files present

### 15. Check Page Objects Exist

```bash
ls e2e/page-objects/
```

**Expected:** LoginPage.ts, TenantSelectionPage.ts

- [ ] ✅ Both page object files present

---

## ☑️ CI/CD Verification

### 16. Check GitHub Actions Workflow

```bash
cat .github/workflows/e2e-tests.yml
```

**Expected:** Valid YAML workflow configuration

- [ ] ✅ Workflow file exists
- [ ] ✅ Contains test execution steps

---

## ☑️ Documentation Verification

### 17. Check Documentation

```bash
ls apps/shell-ui/e2e/README.md
ls apps/shell-ui/E2E-SETUP.md
ls docs/qa/epic-3-automation-strategy.md
ls docs/qa/AUTOMATION-IMPLEMENTATION-SUMMARY.md
```

**Expected:** All 4 documentation files exist

- [ ] ✅ e2e/README.md exists
- [ ] ✅ E2E-SETUP.md exists
- [ ] ✅ Automation strategy exists
- [ ] ✅ Implementation summary exists

---

## ☑️ Final Verification

### 18. Run Full Test Suite

```bash
npm run test:e2e
```

**Expected:** All tests pass

- [ ] ✅ Test suite completes
- [ ] ✅ All tests pass (11/11)
- [ ] ✅ Execution time < 2 minutes

### 19. Check Test Artifacts

```bash
ls -la playwright-report/
ls -la test-results/
```

**Expected:** Report and result directories exist

- [ ] ✅ playwright-report/ directory exists
- [ ] ✅ test-results/ directory exists
- [ ] ✅ HTML report generated

---

## 🎉 Success Criteria

All checkboxes should be checked (✅) for successful setup.

**If any step failed:**

1. **Check services** - Ensure API and Shell UI are running
2. **Check ports** - No conflicts on 3000 or 8000
3. **Reinstall** - Try `npm install` again
4. **Check logs** - Look for error messages
5. **Consult docs** - See E2E-SETUP.md for troubleshooting

---

## 📊 Summary

When all checks pass, you have:

✅ **Playwright installed and configured**
✅ **11 working tests for Story 3.1**
✅ **All helper utilities functional**
✅ **Page Object Models working**
✅ **Test fixtures loaded**
✅ **Multiple run modes working** (normal, UI, headed, debug)
✅ **CI/CD workflow configured**
✅ **Comprehensive documentation available**

---

## 🚀 What's Next?

1. **Review test code** - Study `e2e/tests/3.1-login.spec.ts`
2. **Read documentation** - See `e2e/README.md` for full guide
3. **Follow automation strategy** - See `docs/qa/epic-3-automation-strategy.md`
4. **Add more tests** - Stories 3.2, 3.3, 3.4, 3.5, Integration
5. **Run in CI/CD** - Push code to trigger GitHub Actions

---

## 📞 Support

**Troubleshooting:** See E2E-SETUP.md
**Full Documentation:** See e2e/README.md
**Strategy Guide:** See docs/qa/epic-3-automation-strategy.md

**Questions?** File an issue in the project repository.

---

**Checklist Version:** 1.0
**Last Updated:** 2025-10-18
**Author:** Quinn (Test Architect) 🧪

