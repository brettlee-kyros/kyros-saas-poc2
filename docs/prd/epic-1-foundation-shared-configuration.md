# Epic 1: Foundation & Shared Configuration

**Epic Goal:** Establish the foundational project infrastructure including monorepo setup, shared JWT configuration module, tenant metadata database with seeding, and Docker Compose orchestration - while delivering working health check endpoints and validation utilities that enable all subsequent development work.

## Story 1.1: Monorepo Project Structure and Build Configuration

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

## Story 1.2: Shared Configuration Module for JWT Validation

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
9. **[BLOCKER RESOLUTION #1]** Dependency resolution strategy documented in `docs/dependency-resolution.md`
10. **[BLOCKER RESOLUTION #1]** JWT library chosen: PyJWT 2.8+ (rationale: lightweight, widely used, simpler API than python-jose)
11. **[BLOCKER RESOLUTION #1]** All Python requirements.txt files use pinned versions (e.g., `PyJWT==2.8.0`, `pydantic==2.5.0`)
12. **[BLOCKER RESOLUTION #1]** Compatibility validated: Dash 2.18+ tested with Python 3.11+ in clean virtual environment
13. **[BLOCKER RESOLUTION #1]** Compatibility validated: aiosqlite async patterns tested with FastAPI 0.115+
14. **[BLOCKER RESOLUTION #1]** Known dependency conflicts or workarounds documented in README troubleshooting section
15. **[BLOCKER RESOLUTION #1]** `scripts/test-dependencies.sh` script created to install and test all requirements in clean environment

## Story 1.3: Tenant Metadata Database Schema and Seed Scripts

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

## Story 1.4: Docker Compose Orchestration Setup

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

## Story 1.5: FastAPI Health Check and Basic Setup

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

## Story 1.6: Next.js Shell UI Basic Setup and Health Check

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
