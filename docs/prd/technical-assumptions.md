# Technical Assumptions

## Repository Structure

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

## Service Architecture

**Monolith** - The PoC combines authentication, token exchange, tenant metadata, and dashboard data APIs into a single FastAPI monolith. All services run as separate Docker containers orchestrated by Docker Compose, but the FastAPI backend is a single service.

**Rationale:** Combining services reduces operational complexity for local PoC development while maintaining clear internal module boundaries (routers, services, database access). The architecture document already defines the separation points for MVP migration (auth service, data service). This trade-off is explicitly documented in NFR3.

**⚠️ MVP Migration Note:** The MVP must separate the monolith into at least two services: (1) Authentication/Token Exchange service and (2) Dashboard Data service. The current FastAPI router structure (`routers/auth.py`, `routers/token.py`, `routers/dashboard.py`) maps cleanly to this separation.

## Testing Requirements

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

## Additional Technical Assumptions and Requests

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
