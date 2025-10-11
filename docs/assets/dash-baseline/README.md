# Dash Baseline Assets

**Created By:** Story 0.3 - Dash Application Startup Validation
**Date:** 2025-10-07

---

## Purpose

This directory was created to store baseline screenshots and dependency lists from the original `burn-performance` and `mixshift` Dash applications before Epic 4 modifications.

---

## Status

**❌ Baseline screenshots NOT captured**

**Reason:** Applications cannot start in the PoC development environment due to blocking dependencies:

1. **Private Package:** `kyros-plotly-common==0.5.8` (not accessible without authentication)
2. **Databricks Infrastructure:** Applications require Databricks connection for data loading
3. **Redis Server:** Caching layer requires Redis instance

---

## Alternative Baseline Documentation

Since the original applications cannot run, baseline information was captured through static analysis in Epic 0:

### Story 0.1: Repository Structure
- Entry points identified (`app.py` for both)
- Directory structure documented
- Callback patterns noted
- Dependencies catalogued

### Story 0.2: Test Data
- Data schemas documented (burn.csv: 100×56, mix.csv: 100×6)
- Sample data captured for Epic 4 visualization baseline

### Story 0.3: Dependency Analysis
- Complete dependency list analyzed
- Python 3.11 compatibility confirmed
- Dash 2.18.1 version validated
- Blocking vs. compatible dependencies identified

---

## Epic 4 Baseline Strategy

Instead of comparing against original running applications, Epic 4 will:

1. Create modified Dash applications that work in PoC environment
2. Validate visualizations against test data expectations
3. Compare structure against Story 0.1 architectural analysis
4. Ensure JWT validation and tenant isolation work correctly

**Baseline comparison:** Test data visualizations, not original app screenshots

---

## Files That Would Have Been Here

If applications could start, this directory would contain:

- `burn-performance-baseline.png` - Screenshot of CLV dashboard
- `mixshift-baseline.png` - Screenshot of Risk Analysis dashboard
- `installed-burn-performance.txt` - Pip freeze of burn-performance dependencies
- `installed-mixshift.txt` - Pip freeze of mixshift dependencies

---

## References

- Full startup validation analysis: `docs/external-dependencies.md` (Dash Application Startup Validation section)
- Story documentation: `docs/stories/0.3.dash-startup-validation.md`
