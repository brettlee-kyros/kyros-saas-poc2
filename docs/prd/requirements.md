# Requirements

## Functional Requirements

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

## Non-Functional Requirements

**NFR1:** The system shall use a monorepo structure with npm workspaces to enable sharing the configuration module between Next.js, FastAPI, and Dash applications

**NFR2:** All services shall run locally via Docker Compose without requiring cloud infrastructure or external dependencies

**NFR3:** The PoC shall document all architectural simplifications (mock auth, pre-generated JWTs, SQLite, in-memory data) with explicit notes on what must change for MVP

**NFR4:** JWT signature validation shall prevent token tampering - modified tokens must be rejected with clear error messages

**NFR5:** The token exchange endpoint response time shall be under 500ms at the 95th percentile for local deployment

**NFR6:** The system shall provide logging at key handoff points (token exchange, header injection, JWT validation) to enable debugging and demonstration of the flow

**NFR7:** The PoC codebase shall use TypeScript for frontend code and Python 3.11+ for backend/Dash code with type hints to reduce runtime errors

**NFR8:** The system shall be resettable to a known clean state via seed scripts to enable repeated demonstrations

---
