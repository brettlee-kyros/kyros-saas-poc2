# Kyros Multi-Tenant SaaS PoC - Product Requirements Document (PRD)

**Version:** 0.1
**Date:** 2025-10-05
**Status:** In Progress

---

## Goals and Background Context

### Goals

- Validate the JWT token exchange mechanism for hard tenant isolation in a multi-tenant SaaS architecture
- Prove that embedded Plotly Dash applications can securely access tenant-scoped data through reverse proxy header injection
- Demonstrate consistent JWT validation across multiple services (FastAPI, Dash apps) using shared configuration
- Create a working PoC that showcases the full authentication flow: mock login → tenant selection → token exchange → dashboard embedding
- Document PoC simplifications and provide clear migration path to production MVP
- Establish foundation patterns (token exchange, reverse proxy, tenant isolation) that transition directly to MVP with infrastructure substitutions

### Background Context

The Kyros PoC addresses a critical validation need before committing to full MVP development. The existing architecture documentation (found in `existing-architecture-docs/`) proposes a sophisticated multi-tenant SaaS platform using JWT token exchange for tenant isolation. However, the core mechanisms—converting multi-tenant user tokens to single-tenant scoped tokens, passing these securely to embedded applications, and enforcing hard tenant isolation—have never been implemented or validated.

The brainstorming session identified "architectural fidelity with pragmatic mocking" as the guiding principle. This PoC will prove the architecture works by implementing production-realistic patterns (JWT exchange, reverse proxy, shared configuration) while mocking external dependencies (Azure AD B2C, cloud storage, observability). The critical validation point is demonstrating that tenant isolation works through JWT claims, preventing any cross-tenant data leakage while maintaining a seamless user experience across Shell UI and embedded Dash applications.

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-10-05 | 0.1 | Initial PRD creation from architecture and brainstorming documents | John (PM Agent) |

---

## Requirements

### Functional Requirements

**FR1:** The system shall provide a mock authentication endpoint that accepts user email and returns a pre-generated user access token containing an array of tenant_ids the user can access

**FR2:** The Shell UI shall display a tenant selection interface when a user has access to multiple tenants, requiring explicit tenant choice before proceeding

**FR3:** The system shall provide a token exchange endpoint that accepts a user access token and tenant_id, validates the user has access to that tenant, and returns a short-lived tenant-scoped JWT (30 minute expiry)

**FR4:** The tenant-scoped JWT shall contain exactly one tenant_id claim (not an array), the user's role for that tenant, and standard JWT claims (sub, iat, exp)

**FR5:** The Shell UI shall use Next.js API routes as a reverse proxy to inject the tenant-scoped JWT into Authorization headers when embedding Dash applications

**FR6:** Both Dash applications (Customer Lifetime Value and Risk Analysis) shall extract and validate the tenant-scoped JWT from the Authorization header using the shared configuration module

**FR7:** The system shall provide a shared configuration module (Python package) that defines JWT validation settings (secret key, algorithm, issuer) and is imported by all services (FastAPI, Dash apps)

**FR8:** The FastAPI data access layer shall filter all dashboard data queries by the tenant_id extracted from the validated JWT, never accepting tenant context from request parameters

**FR9:** The Shell UI shall provide a debug panel (collapsible) that displays the decoded JWT claims to demonstrate token exchange and tenant scoping

**FR10:** The system shall store tenant metadata (tenants, users, user-tenant mappings, dashboard assignments) in a SQLite database with schema compatible with PostgreSQL migration

**FR11:** The Dash applications shall load mock tenant data from in-memory Pandas DataFrames populated from CSV/Parquet files in the sample-plotly-repos directory (burn-performance and mixshift projects)

**FR12:** The system shall provide automated seed scripts to initialize the tenant metadata database with mock tenants, users, and dashboard assignments

**FR13:** When a tenant-scoped JWT expires during dashboard viewing, the system shall return a 401 Unauthorized response, and the Shell UI shall detect this and redirect to tenant selection or login

**FR14:** The system shall prevent cross-tenant data access by validating that the JWT tenant_id matches the requested resource's tenant context for all API endpoints

**FR15:** The Shell UI shall display a dashboard listing page showing all dashboards assigned to the selected tenant, retrieved via the FastAPI metadata API

### Non-Functional Requirements

**NFR1:** The system shall use a monorepo structure with npm workspaces to enable sharing the configuration module between Next.js, FastAPI, and Dash applications

**NFR2:** All services shall run locally via Docker Compose without requiring cloud infrastructure or external dependencies

**NFR3:** The PoC shall document all architectural simplifications (mock auth, pre-generated JWTs, SQLite, in-memory data) with explicit notes on what must change for MVP

**NFR4:** JWT signature validation shall prevent token tampering - modified tokens must be rejected with clear error messages

**NFR5:** The token exchange endpoint response time shall be under 500ms at the 95th percentile for local deployment

**NFR6:** The system shall provide logging at key handoff points (token exchange, header injection, JWT validation) to enable debugging and demonstration of the flow

**NFR7:** The PoC codebase shall use TypeScript for frontend code and Python 3.11+ for backend/Dash code with type hints to reduce runtime errors

**NFR8:** The system shall be resettable to a known clean state via seed scripts to enable repeated demonstrations

---

## User Interface Design Goals

### Overall UX Vision

The PoC UI prioritizes **architectural demonstration** over polished user experience. The interface should make the token exchange mechanism **visible and comprehensible** to technical stakeholders while maintaining a functional user journey. Clean, minimal design with clear visual feedback at each step (login → tenant selection → dashboard viewing) helps non-technical stakeholders understand the multi-tenant architecture. The debug panel showing JWT claims serves as both a validation tool and a teaching aid, making the abstract concept of tenant-scoped tokens tangible.

### Key Interaction Paradigms

- **Explicit Tenant Selection**: Unlike production systems that might auto-select single-tenant users, the PoC forces explicit tenant choice via a dedicated selection page, creating a clear demonstration point for the token exchange trigger
- **Server-Side Token Handling**: All JWT operations happen server-side (Next.js API routes, FastAPI), never exposing tokens to browser JavaScript - validates the production security pattern
- **Embedded Dashboard Pattern**: Dash applications render within the Shell UI through reverse proxy, demonstrating header injection without iframe complexity
- **Debug-Driven Transparency**: Collapsible debug panel reveals internal state (decoded JWT claims, token expiry) for stakeholder education and validation

### Core Screens and Views

**Login Screen** - Simple email input form with hardcoded email suggestions for mock users, demonstrating authentication entry point

**Tenant Selection Page** - Grid or list of available tenants with visual cards showing tenant name and metadata, primary CTA button for each tenant triggers token exchange

**Dashboard Listing Page** - Shows all dashboards assigned to selected tenant in card/tile layout, includes tenant context indicator in header, displays debug panel toggle

**Dashboard View Page** - Full-screen embedded Dash application, header shows active tenant and provides tenant switcher dropdown, debug panel displays current JWT claims and expiry countdown

**Error States** - Simple inline error messages for token expiry (401) and unauthorized access (403), redirect to login or tenant selection as appropriate

### Accessibility

**None** - Accessibility features are out of scope for PoC. MVP should target WCAG AA compliance.

### Branding

**Minimal Generic Branding** - Simple color scheme (neutral grays with one accent color), basic logo placeholder, no custom fonts or sophisticated styling. The PoC validates architecture, not design. The tenant `config_json` includes branding fields (logo_url, primary_color) to demonstrate the data model, but applying tenant-specific branding to the Shell UI is out of PoC scope.

### Target Devices and Platforms

**Web Responsive (Desktop-First)** - Primary target is desktop browsers (Chrome, Firefox, Safari latest versions) at 1920x1080 resolution for stakeholder demonstrations. Basic responsive behavior for laptop screens (1366x768+) but mobile/tablet views are not optimized. The embedded Dash applications will inherit responsive behavior from the source repos (burn-performance and mixshift).

---

## Technical Assumptions

### Repository Structure

**Monorepo** - The project uses a monorepo structure managed by npm workspaces (lightweight, no Nx/Turborepo tooling required). This enables the critical shared configuration module to be co-located with the services that consume it (FastAPI, Dash apps), solving the configuration consistency root cause identified in brainstorming.

**Package Organization:**
```
kyros-saas-poc/
├── apps/
│   ├── shell-ui/          # Next.js frontend
│   ├── api/               # FastAPI monolith
│   ├── dash-app-clv/      # Customer Lifetime Value dashboard (from burn-performance)
│   └── dash-app-risk/     # Risk Analysis dashboard (from mixshift)
├── packages/
│   └── shared-config/     # Python package: JWT config, constants, validation
├── data/
│   ├── tenant_metadata.db # SQLite database (generated)
│   └── mock-data/         # CSV/Parquet from sample-plotly-repos
└── scripts/               # Seed/setup scripts
```

**Rationale:** Monorepo ensures the shared configuration module is versioned atomically with consuming services, preventing configuration drift. Separate Dash app directories allow independent modification of burn-performance and mixshift sources while maintaining shared JWT validation logic.

### Service Architecture

**Monolith** - The PoC combines authentication, token exchange, tenant metadata, and dashboard data APIs into a single FastAPI monolith. All services run as separate Docker containers orchestrated by Docker Compose, but the FastAPI backend is a single service.

**Rationale:** Combining services reduces operational complexity for local PoC development while maintaining clear internal module boundaries (routers, services, database access). The architecture document already defines the separation points for MVP migration (auth service, data service). This trade-off is explicitly documented in NFR3.

**⚠️ MVP Migration Note:** The MVP must separate the monolith into at least two services: (1) Authentication/Token Exchange service and (2) Dashboard Data service. The current FastAPI router structure (`routers/auth.py`, `routers/token.py`, `routers/dashboard.py`) maps cleanly to this separation.

### Testing Requirements

**Unit + Integration Testing** - The PoC implements a focused testing strategy:

**Frontend (Shell UI):**
- Vitest + React Testing Library for component tests (TenantSelector, DashboardEmbed, debug panel)
- Hook tests for useAuth, useTenantContext, useTokenRefresh
- Target: 60%+ coverage on business logic components

**Backend (FastAPI):**
- pytest with async test client (httpx)
- Unit tests for JWT validation, token exchange, tenant isolation logic
- Integration tests for full endpoint flows (mock DB)
- Target: 70%+ coverage on authentication and data access layers

**E2E (Playwright):**
- Critical path: login → tenant selection → dashboard load
- Token expiry and refresh flow
- Cross-tenant isolation validation (attack scenarios from brainstorming)
- Target: 3-5 key scenarios

**Out of Scope:**
- Performance/load testing (PoC runs locally with no scale requirements)
- Security penetration testing (beyond basic isolation validation)
- Browser compatibility testing (Chrome/Firefox latest only)

**Rationale:** This testing pyramid focuses validation effort on the architectural mechanisms (JWT exchange, tenant isolation) rather than comprehensive test coverage. E2E tests directly map to the validation questions from the brainstorming session.

### Additional Technical Assumptions and Requests

**Languages and Frameworks:**
- **Frontend:** TypeScript 5.3+, Next.js 14.2+ (App Router), React 18+
- **Backend:** Python 3.11+, FastAPI 0.115+
- **Dash Apps:** Python 3.11+, Plotly Dash 2.18+
- **Rationale:** TypeScript prevents runtime errors in token handling. Next.js App Router provides server components and API routes for reverse proxy. Python 3.11+ unified across backend enables shared config module.

**Database and Storage:**
- **Tenant Metadata:** SQLite 3.45+ with PostgreSQL-compatible schema (standard SQL, no SQLite-specific features)
- **Dashboard Data:** In-memory Pandas DataFrames loaded from CSV/Parquet files in `sample-plotly-repos/` directories
- **Rationale:** SQLite requires zero configuration. Schema designed for DROP-IN replacement with PostgreSQL (UUID → TEXT, BOOLEAN → INTEGER, JSONB → TEXT). In-memory data simulates Azure Storage without infrastructure while maintaining realistic data access patterns.

**Authentication and Security:**
- **Mock Auth:** FastAPI endpoint returning pre-generated JWTs (stored as constants in shared-config)
- **JWT Library:** PyJWT or python-jose for encoding/decoding/validation
- **Token Storage:** HTTP-only cookies for tenant-scoped tokens (never localStorage)
- **Rationale:** Mock auth eliminates Azure AD B2C dependency while keeping token exchange flow architecturally accurate. Pre-generated JWTs allow testing multiple user/tenant scenarios without cryptographic complexity.

**Deployment and Orchestration:**
- **Local Deployment Only:** Docker Compose orchestrates Shell UI (Next.js), API (FastAPI), and Dash apps
- **No Cloud Infrastructure:** No Azure, AWS, or GCP resources required for PoC
- **Port Mapping:** Shell UI (3000), FastAPI (8000), Dash CLV (8050), Dash Risk (8051)
- **Rationale:** Docker Compose provides consistent local execution across development machines. Avoids cloud costs and complexity for architectural validation.

**Data Sources for Dash Apps:**
- **Source:** Existing Plotly repos in `sample-plotly-repos/burn-performance` and `sample-plotly-repos/mixshift`
- **Modification Required:** Dash apps must be modified to:
  1. Import shared-config module for JWT validation
  2. Extract tenant_id from Authorization header
  3. Query FastAPI data API (instead of direct data access)
  4. Accept tenant-scoped data from API response
- **Test Data:** Use existing test data from `burn-performance-test-data/` and `mixshift-test-data/` directories, augmented with tenant_id column for multi-tenant filtering
- **Rationale:** Reusing existing Dash apps demonstrates realistic integration scenario. Modifications validate the architectural pattern (JWT validation, API-based data access) without building dashboards from scratch.

**Libraries and Dependencies:**
- **UI Components:** Tailwind CSS 3.4+ for styling, Headless UI 2.1+ for accessible primitives (dropdowns, modals)
- **State Management:** Zustand 4.5+ for tenant context, React Context for auth state
- **API Client:** Native fetch with wrapper for auth headers
- **Async DB Access:** aiosqlite for FastAPI database queries
- **Rationale:** Lightweight modern libraries appropriate for PoC scale. Tailwind enables rapid UI prototyping. Zustand simpler than Redux for limited state management needs.

**Build and Development Tools:**
- **Frontend Build:** Next.js built-in (Turbopack/Webpack)
- **Backend:** No build step (Python interpreted)
- **Package Management:** npm for frontend, pip for Python
- **Linting:** ESLint for TypeScript, Ruff for Python
- **Rationale:** Standard tooling, minimal configuration overhead.

**Logging and Monitoring:**
- **Logging:** JSON structured logs to stdout (Docker Compose captures)
- **Log Points:** Token exchange, header injection, JWT validation, data access with tenant_id
- **Monitoring:** None (no Prometheus/Grafana/Loki in PoC)
- **Rationale:** Stdout logging sufficient for local debugging and demonstration. Monitoring eliminated per brainstorming SCAMPER analysis.

**Documentation Requirements:**
- **README:** Setup instructions, Docker Compose commands, seed script usage
- **Architecture Tradeoffs Doc:** Explicit list of PoC simplifications and MVP migration tasks
- **API Documentation:** FastAPI auto-generated OpenAPI docs (Swagger UI)
- **Rationale:** Documentation ensures PoC creates organizational value beyond code, enabling future team to understand migration requirements.

---

## Epic List

**Epic 0: Prerequisites & External Dependency Validation**

Validate all external dependencies, verify sample Plotly repositories accessibility and compatibility, and establish baseline prerequisites before beginning foundation work - ensuring Epic 4 Dash integration is not blocked by missing or incompatible external resources.

**Epic 1: Foundation & Shared Configuration**

Establish project infrastructure, monorepo setup, shared JWT configuration module, and automated database seeding - creating the foundation for all subsequent work while delivering basic health checks and validation utilities.

**Epic 2: Mock Authentication & Token Exchange**

Implement mock authentication endpoint, user access token generation, token exchange mechanism for tenant scoping, and tenant metadata API - delivering the core architectural validation target (JWT token exchange with hard tenant isolation).

**Epic 3: Shell UI & Tenant Selection**

Build Next.js Shell UI with login page, tenant selection interface, dashboard listing page, and debug panel - delivering a functional user journey from authentication through tenant selection with full visibility into JWT claims.

**Epic 4: Dash Application Integration**

Modify existing Dash applications (burn-performance, mixshift) to validate JWTs, integrate with FastAPI data API, and load tenant-scoped data - proving the architecture can embed real-world Plotly applications with secure tenant isolation.

**Epic 5: Reverse Proxy & Dashboard Embedding**

Implement Next.js API routes as reverse proxy with Authorization header injection, integrate Dash apps into Shell UI dashboard view, and handle token expiry - completing the end-to-end flow with secure embedding pattern.

**Epic 6: Testing & Validation**

Implement unit tests for JWT validation and token exchange, integration tests for API endpoints, and E2E tests for critical paths including cross-tenant isolation attacks - validating that tenant isolation works as designed.

---

## Epic 1: Foundation & Shared Configuration

**Epic Goal:** Establish the foundational project infrastructure including monorepo setup, shared JWT configuration module, tenant metadata database with seeding, and Docker Compose orchestration - while delivering working health check endpoints and validation utilities that enable all subsequent development work.

### Story 1.1: Monorepo Project Structure and Build Configuration

**As a** developer,
**I want** the monorepo structure with npm workspaces configured and basic build scripts,
**so that** I can develop and build all services (Shell UI, FastAPI, Dash apps) from a single repository with shared dependencies.

**Acceptance Criteria:**

1. Repository structure matches the Technical Assumptions layout with apps/, packages/, data/, docs/, and scripts/ directories
2. package.json at root level configures npm workspaces for apps/shell-ui and other npm-based packages
3. Each Python app (api, dash-app-clv, dash-app-risk) has requirements.txt with dependency specifications
4. Root-level README.md documents project structure, technology stack, and setup prerequisites
5. .gitignore configured to exclude node_modules/, __pycache__/, *.pyc, .env, data/*.db, and build artifacts
6. Basic npm scripts defined: install, build, lint (runs ESLint on TypeScript code)
7. Python linting configured with Ruff for all Python applications

### Story 1.2: Shared Configuration Module for JWT Validation

**As a** developer,
**I want** a shared Python package containing JWT configuration settings, validation functions, and data models,
**so that** all services (FastAPI, Dash apps) use identical JWT validation logic, preventing configuration drift.

**Acceptance Criteria:**

1. packages/shared-config/ created as installable Python package with setup.py or pyproject.toml
2. Shared config module exports JWT_SECRET_KEY, JWT_ALGORITHM ("HS256"), JWT_ISSUER ("kyros-poc")
3. Shared config defines USER_TOKEN_EXPIRY (3600 seconds) and TENANT_TOKEN_EXPIRY (1800 seconds)
4. Pydantic models defined for UserAccessToken (with tenant_ids array) and TenantScopedToken (with single tenant_id)
5. Validation functions provided: validate_user_token(token) and validate_tenant_token(token) that decode JWT and return typed objects
6. Mock user data structure defined with pre-configured users and their tenant mappings
7. All Python apps can import from shared_config module: `from shared_config import JWT_SECRET_KEY, validate_tenant_token`
8. Unit tests verify JWT encoding and decoding work correctly with shared configuration

### Story 1.3: Tenant Metadata Database Schema and Seed Scripts

**As a** developer,
**I want** a SQLite database with PostgreSQL-compatible schema and automated seed scripts,
**so that** the PoC has consistent tenant metadata for testing without manual SQL entry, and the schema can migrate to PostgreSQL for MVP.

**Acceptance Criteria:**

1. database/schema.sql contains CREATE TABLE statements for: tenants, users, user_tenants, dashboards, tenant_dashboards
2. Schema uses PostgreSQL-compatible types: TEXT for UUIDs, INTEGER for booleans, TEXT for JSONB, TEXT for timestamps (ISO 8601)
3. Foreign key constraints defined with ON DELETE CASCADE for referential integrity
4. Indexes created on: tenants.slug, users.email, user_tenants(user_id), user_tenants(tenant_id), tenant_dashboards(tenant_id)
5. scripts/seed-database.py script creates data/tenant_metadata.db and executes schema.sql
6. Seed script inserts 2 mock tenants (Acme Corporation, Beta Industries) with config_json including branding fields
7. Seed script inserts 3 mock users with different tenant access patterns (single tenant, multi-tenant, different tenant)
8. Seed script inserts 2 dashboard definitions (customer-lifetime-value, risk-analysis) with config_json
9. Seed script creates tenant_dashboards assignments (Acme has both dashboards, Beta has only risk-analysis)
10. scripts/validate-database.py script queries database and verifies expected records exist, printing validation report
11. Seed script is idempotent - running multiple times drops and recreates database cleanly

### Story 1.4: Docker Compose Orchestration Setup

**As a** developer,
**I want** Docker Compose configuration that orchestrates all services with proper networking and volume mounts,
**so that** I can start the entire PoC with a single command and services can communicate.

**Acceptance Criteria:**

1. docker-compose.yml defines services: shell-ui, api, dash-app-clv, dash-app-risk
2. shell-ui service: builds from apps/shell-ui/Dockerfile, exposes port 3000, depends on api service
3. api service: builds from apps/api/Dockerfile, exposes port 8000, mounts data/ volume for SQLite access
4. dash-app-clv service: builds from apps/dash-app-clv/Dockerfile, exposes port 8050, depends on api service
5. dash-app-risk service: builds from apps/dash-app-risk/Dockerfile, exposes port 8051, depends on api service
6. All services connected via Docker network named kyros-net for inter-service communication
7. Environment variables configured for each service (database path, API URLs, JWT secret)
8. Volume mounts configured for: data/ (database and mock data), shared-config/ (Python package)
9. Each service Dockerfile created with appropriate base image (node:20 for Shell UI, python:3.11 for others)
10. Dockerfiles install dependencies and set up working directories correctly
11. `docker-compose up --build` successfully starts all services without errors

### Story 1.5: FastAPI Health Check and Basic Setup

**As a** developer,
**I want** a basic FastAPI application with health check endpoint and database connectivity,
**so that** I can verify the API service is running and can access the tenant metadata database.

**Acceptance Criteria:**

1. apps/api/src/main.py created with FastAPI app initialization
2. GET /health endpoint returns {"status": "ok", "timestamp": "<ISO 8601>"} with 200 status
3. FastAPI app configured with CORS middleware allowing requests from localhost:3000 (Shell UI origin)
4. apps/api/src/database/connection.py provides async SQLite connection function using aiosqlite
5. GET /health/db endpoint queries database (SELECT COUNT(*) FROM tenants) and returns database health status
6. FastAPI application loads shared_config module successfully and logs JWT configuration on startup
7. Startup logging confirms: database path, shared config loaded, listening port
8. All endpoints use consistent JSON error response format matching architecture document (error.code, error.message, error.timestamp, error.request_id)
9. FastAPI auto-generated docs available at http://localhost:8000/docs (Swagger UI)
10. Health check endpoints accessible via curl from host machine and from other Docker containers

### Story 1.6: Next.js Shell UI Basic Setup and Health Check

**As a** developer,
**I want** a basic Next.js application with TypeScript and Tailwind CSS configured,
**so that** I have the foundation for building the Shell UI interface.

**Acceptance Criteria:**

1. apps/shell-ui/ initialized with Next.js 14+ using App Router and TypeScript
2. Tailwind CSS 3.4+ configured with tailwind.config.js and globals.css
3. Root layout (app/layout.tsx) created with basic HTML structure and metadata
4. Home page (app/page.tsx) displays "Kyros PoC" heading and link to health check status
5. TypeScript configured with strict mode enabled in tsconfig.json
6. ESLint configured for Next.js and React best practices
7. app/api/health/route.ts API route created that proxies FastAPI /health endpoint
8. Client-side fetch on home page displays API health status (fetches from /api/health)
9. Next.js app successfully builds (`npm run build`) without TypeScript errors
10. Next.js app accessible at http://localhost:3000 with health status visible on home page
11. Environment variables configured in .env.local for API_BASE_URL (http://api:8000)

---

## Epic 2: Mock Authentication & Token Exchange

**Epic Goal:** Implement the core JWT token exchange mechanism that validates the multi-tenant architecture - converting user access tokens (with multiple tenant_ids) into tenant-scoped tokens (with single tenant_id) while enforcing access control and providing tenant metadata APIs.

### Story 2.1: Mock Authentication Endpoint with Pre-Generated JWTs

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

### Story 2.2: User Info Endpoint with Tenant Discovery

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

### Story 2.3: Token Exchange Endpoint for Tenant Scoping

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

### Story 2.4: Tenant Metadata API Endpoints

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

## Epic 3: Shell UI & Tenant Selection

**Epic Goal:** Build the Next.js Shell UI providing the authenticated user journey from login through tenant selection to dashboard listing, with debug panel visibility into JWT claims and token exchange.

### Story 3.1: Login Page with Mock Authentication

**As a** user,
**I want** a login page where I can enter my email to authenticate,
**so that** I can access the multi-tenant application.

**Acceptance Criteria:**

1. app/login/page.tsx created with login form containing email input field and submit button
2. Form styled with Tailwind CSS matching minimal branding guidelines
3. Email input includes placeholder text with example: "analyst@acme.com"
4. Form includes dropdown or clickable suggestions for the 3 mock user emails
5. On submit, form calls POST /api/auth/mock-login via fetch with {email} payload
6. On success, stores access_token in memory (React state or zustand store) and redirects to home page
7. On 404 error, displays error message: "User not found" below form
8. On network error, displays error message with retry option
9. Loading state shows spinner on submit button during API call
10. TypeScript interfaces defined for login request/response
11. Client-side validation ensures email format before submission
12. Page is accessible at /login route

### Story 3.2: Authentication Context and Token Management

**As a** Shell UI developer,
**I want** centralized auth state management with token storage,
**so that** authenticated state and tokens are accessible throughout the application.

**Acceptance Criteria:**

1. Auth context created with React Context API providing: {isAuthenticated, userToken, login(token), logout()}
2. Auth provider wraps root layout (app/layout.tsx)
3. User access token stored in React state (not localStorage for PoC simplicity)
4. login(token) function stores token and sets isAuthenticated = true
5. logout() function clears token and sets isAuthenticated = false
6. useAuth() hook provides access to auth context from any component
7. AuthGuard component created that redirects to /login if not authenticated
8. AuthGuard wraps protected routes (home page, tenant pages)
9. On app mount, auth context checks for existing token (future: could check /api/me)
10. TypeScript types defined for auth context interface

### Story 3.3: Tenant Selection Page

**As a** user,
**I want** to see a list of tenants I have access to and select one,
**so that** I can exchange my user token for a tenant-scoped token and proceed to dashboards.

**Acceptance Criteria:**

1. Home page (app/page.tsx) fetches GET /api/me on mount if authenticated
2. If user has multiple tenants, displays tenant selector grid/list with cards for each tenant
3. Each tenant card shows: tenant name, optional description from config_json, "Select" button
4. Tenant cards styled with Tailwind CSS, using branding colors from config_json if present
5. On "Select" button click, calls POST /api/token/exchange with {tenant_id}
6. On successful exchange, stores tenant-scoped token (replaces user token in auth context or separate tenant context)
7. Stores selected tenant metadata (id, name, slug) in zustand tenant store
8. Redirects to /tenant/[tenant_slug] route after successful exchange
9. If user has only one tenant, automatically triggers exchange and redirects (skips selection UI)
10. Loading state shown during tenant discovery and token exchange
11. Error handling for exchange failures (403, 401) with user-friendly messages
12. TypeScript interfaces for tenant data and exchange request/response

### Story 3.4: Dashboard Listing Page

**As a** user,
**I want** to view all dashboards available for my selected tenant,
**so that** I can choose which dashboard to open.

**Acceptance Criteria:**

1. app/tenant/[tenant_slug]/page.tsx created for dashboard listing
2. Page fetches GET /api/tenant/{tenant_id}/dashboards using tenant-scoped token on mount
3. Page displays tenant name in header/breadcrumb area
4. Dashboard cards displayed in grid layout (2-3 columns responsive)
5. Each card shows: dashboard title, description, thumbnail placeholder, "Open Dashboard" button
6. Cards styled with Tailwind CSS consistent with app theme
7. On "Open Dashboard" click, navigates to /tenant/[tenant_slug]/dashboard/[dashboard_slug]
8. If no dashboards assigned, displays message: "No dashboards available for this tenant"
9. Loading state shown while fetching dashboards
10. Error handling for API failures with retry option
11. Page includes tenant switcher dropdown in header (shows current tenant, allows switching back to selection)
12. TypeScript interfaces for dashboard list response

### Story 3.5: JWT Debug Panel Component

**As a** stakeholder,
**I want** a collapsible debug panel showing decoded JWT claims and expiry countdown,
**so that** I can visually verify the token exchange mechanism and tenant scoping.

**Acceptance Criteria:**

1. DebugPanel component created in components/dashboard/DebugPanel.tsx
2. Panel rendered in app header or fixed position (top-right corner)
3. Panel collapsed by default, toggle button shows "Debug" label or icon
4. When expanded, panel displays: Token Type (User/Tenant-Scoped), Decoded Claims (formatted JSON), Expiry Countdown (time remaining)
5. If tenant-scoped token active, highlights tenant_id claim and shows it's a single value (not array)
6. If user access token active, highlights tenant_ids claim showing array of UUIDs
7. Expiry countdown updates every second, shows "Expired" in red if token past expiration
8. Panel styled with Tailwind CSS, semi-transparent background, readable typography
9. Panel uses JWT decode library (e.g., jwt-decode) to parse token without validation
10. Panel handles missing/invalid tokens gracefully (shows "No token" message)
11. Panel visible on all authenticated pages (login page, tenant selection, dashboard listing, dashboard view)
12. Component re-renders when token changes (after login, after exchange)

---

## Epic 4: Dash Application Integration

**Epic Goal:** Modify the existing Dash applications from sample-plotly-repos (burn-performance → CLV, mixshift → Risk) to validate JWTs from Authorization headers, query FastAPI data API with tenant context, and render tenant-scoped visualizations.

### Story 4.1: Tenant Data Preparation and FastAPI Data Access Layer

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

### Story 4.2: Customer Lifetime Value Dashboard Integration

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

### Story 4.3: Risk Analysis Dashboard Integration

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

## Epic 5: Reverse Proxy & Dashboard Embedding

**Epic Goal:** Implement Next.js API routes as reverse proxy to inject Authorization headers when embedding Dash applications in Shell UI, complete the end-to-end flow, and handle token expiry gracefully.

### Story 5.1: Next.js Reverse Proxy API Route with Header Injection

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

### Story 5.2: Dashboard Embedding Page with iframe or Direct Embed

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

### Story 5.3: Token Expiry Handling and Redirect

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

## Epic 6: Testing & Validation

**Epic Goal:** Implement comprehensive testing to validate the JWT token exchange mechanism, tenant isolation, and end-to-end user flows - proving the architecture works as designed.

### Story 6.1: Backend Unit Tests for JWT and Token Exchange

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

### Story 6.2: Backend Integration Tests for API Endpoints

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

### Story 6.3: Frontend Unit Tests for Components and Hooks

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

### Story 6.4: End-to-End Tests for Critical Paths

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

---

## Checklist Results Report

_This section will be populated after running the pm-checklist to validate PRD completeness and quality._

**Status:** Pending execution

---

## Next Steps

### UX Expert Prompt

The UI/UX design goals have been documented in this PRD. If detailed wireframes, user flows, or design system specifications are needed, engage the UX Expert with:

"Review the PRD at docs/prd.md and create wireframes for the Shell UI focusing on: (1) tenant selection interface, (2) dashboard listing page, and (3) JWT debug panel. Prioritize architectural demonstration over polished aesthetics, ensuring the token exchange flow is visually clear to technical stakeholders."

### Architect Prompt

The architecture document at docs/architecture.md provides comprehensive technical specifications. With the PRD now complete, you can begin implementation:

"The PRD is complete at docs/prd.md. Begin implementation starting with Epic 1 (Foundation & Shared Configuration). Focus on:
1. Setting up the monorepo structure with shared-config module
2. Creating the database schema and seed scripts
3. Establishing Docker Compose orchestration
4. Implementing health check endpoints

Reference the architecture document at docs/architecture.md for detailed technical specifications. All requirements, epics, and acceptance criteria are defined in the PRD."

---

**End of PRD Document**

