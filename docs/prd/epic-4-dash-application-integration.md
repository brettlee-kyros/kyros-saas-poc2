# Epic 4: Dash Application Integration

**Epic Goal:** Modify the existing Dash applications from sample-plotly-repos (burn-performance → CLV, mixshift → Risk) to validate JWTs from Authorization headers, query FastAPI data API with tenant context, and render tenant-scoped visualizations.

## Story 4.1: Tenant Data Preparation and FastAPI Data Access Layer

**As a** developer,
**I want** tenant-scoped mock data prepared and a FastAPI data API endpoint,
**so that** Dash apps can query tenant-filtered data via API rather than direct storage access.

**Acceptance Criteria:**

1. Existing test data from sample-plotly-repos/burn-performance-test-data/ and mixshift-test-data/ copied to data/mock-data/
2. Data files augmented with tenant_id column (UUIDs matching seeded tenants: Acme, Beta)
3. Data distributed across tenants: Acme gets both CLV and Risk data, Beta gets only Risk data
4. apps/api/src/data/data_loader.py created with function: load_tenant_data(tenant_id: str, dashboard_slug: str) -> pd.DataFrame
5. Data loader loads CSV/Parquet files into Pandas DataFrames on first request, caches in memory
6. Data loader filters DataFrame by tenant_id column before returning
7. GET /api/dashboards/{slug}/data endpoint created requiring tenant-scoped token
8. Endpoint extracts tenant_id from JWT claims, calls data_loader.load_tenant_data(tenant_id, slug)
9. Endpoint returns JSON: {tenant_id, dashboard_slug, data: [records array]}
10. If dashboard_slug not found or no data for tenant, returns 404 "DATA_NOT_FOUND"
11. Endpoint logs data access: tenant_id, dashboard_slug, record count returned
12. Unit tests verify tenant_id filtering works correctly
13. Integration test verifies end-to-end data access with tenant-scoped token

## Story 4.2: Customer Lifetime Value Dashboard Integration

**As a** user,
**I want** the CLV dashboard to display tenant-specific customer lifetime value data,
**so that** I can analyze CLV metrics for my selected tenant only.

**Acceptance Criteria:**

1. Source code from sample-plotly-repos/burn-performance/ copied to apps/dash-app-clv/
2. app.py (Dash app entry point) modified to import shared_config module
3. Custom middleware or decorator created to extract Authorization header from requests
4. JWT validation added using shared_config.validate_tenant_token() on every request
5. Extracted tenant_id from JWT stored in request context or global state (thread-local)
6. All data loading callbacks modified to call GET /api/dashboards/customer-lifetime-value/data with tenant-scoped token
7. Data API calls include Authorization header with the token from the incoming request
8. Dash app renders visualizations using tenant-filtered data from API response
9. If JWT invalid or expired, Dash app returns 401 error page
10. If data API call fails, Dash app shows error message with details
11. Dash app accessible at http://localhost:8050/ (direct access for testing)
12. Dash app includes logging for: JWT validation, tenant_id extraction, data API calls
13. Requirements.txt updated with dependencies: dash, plotly, pandas, requests, shared-config
14. Dash app successfully starts in Docker container

## Story 4.3: Risk Analysis Dashboard Integration

**As a** user,
**I want** the Risk Analysis dashboard to display tenant-specific risk metrics,
**so that** I can analyze risk exposure for my selected tenant only.

**Acceptance Criteria:**

1. Source code from sample-plotly-repos/mixshift/ copied to apps/dash-app-risk/
2. app.py modified to import shared_config module for JWT validation
3. Custom middleware/decorator extracts Authorization header and validates tenant-scoped JWT
4. Extracted tenant_id stored in request context for use in callbacks
5. All data loading callbacks modified to call GET /api/dashboards/risk-analysis/data with tenant token
6. Data API calls include Authorization header forwarded from incoming request
7. Dash app renders visualizations using tenant-scoped data from API
8. JWT validation failures return 401 error page
9. Data API failures display error messages to user
10. Dash app accessible at http://localhost:8051/ (direct access for testing)
11. Logging added for JWT validation, tenant_id, and data API requests
12. Requirements.txt updated with all dependencies including shared-config
13. Dash app successfully starts in Docker container
14. Both Dash apps (CLV and Risk) follow identical JWT validation and data access patterns

---
