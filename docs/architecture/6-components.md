# 6. Components

This section defines the major logical components across the fullstack PoC, their responsibilities, interfaces, dependencies, and technology implementation.

## 6.1 Shell UI (Next.js Application)

**Responsibility:** Authenticated entry point providing login, tenant selection, dashboard listing, and secure embedding of Dash applications via reverse proxy.

**Key Interfaces:**
- **Pages:**
  - `/login` - Mock authentication interface
  - `/` - Tenant selector (if multi-tenant user) or redirect to dashboard list
  - `/tenant/[tenant_slug]` - Dashboard listing page
  - `/tenant/[tenant_slug]/dashboard/[dashboard_slug]` - Dashboard embedding page

- **API Routes (BFF Pattern):**
  - `/api/proxy/dash/[...path]` - Reverse proxy with Authorization header injection

**Dependencies:**
- FastAPI Mock Auth endpoints (`/api/auth/mock-login`, `/api/me`)
- FastAPI Token Exchange endpoint (`/api/token/exchange`)
- FastAPI Metadata endpoints (`/api/tenant/{id}`, `/api/tenant/{id}/dashboards`)
- Shared Config Module (for JWT secret to verify tokens client-side if needed)

**Technology Stack:**
- Next.js 14.2+ (App Router)
- TypeScript 5.3+
- Tailwind CSS + Headless UI (components)
- zustand (tenant context state)
- React Context (auth state)

**Key Design Patterns:**
- **Server Components** for initial page loads (fetch tenant list server-side)
- **Client Components** for interactive tenant selector and token refresh logic
- **API Routes as Reverse Proxy** to inject tenant-scoped JWT into Dash requests
- **HTTP-Only Cookies** for storing tenant-scoped token (never in localStorage)

## 6.2 FastAPI Monolith

**Responsibility:** Central API gateway handling mock authentication, JWT token exchange, tenant metadata resolution, and tenant-scoped data access for Dash applications.

**Key Interfaces:**
- **Mock Auth API:**
  - `POST /api/auth/mock-login` - Returns user access token

- **User API:**
  - `GET /api/me` - Returns user info and accessible tenants

- **Token Exchange API:**
  - `POST /api/token/exchange` - Issues tenant-scoped token

- **Tenant Metadata API:**
  - `GET /api/tenant/{tenant_id}` - Returns tenant config
  - `GET /api/tenant/{tenant_id}/dashboards` - Returns dashboard assignments

- **Dashboard Data API:**
  - `GET /api/dashboards/{slug}/data` - Returns tenant-filtered dashboard data

**Dependencies:**
- SQLite Tenant Metadata DB (via `aiosqlite`)
- In-Memory Data Store (Pandas DataFrames loaded at startup)
- Shared Config Module (JWT validation settings)

**Technology Stack:**
- Python 3.11+
- FastAPI 0.115+
- Pydantic v2 (request/response validation)
- PyJWT or python-jose (JWT encoding/decoding)
- aiosqlite (async SQLite access)
- Pandas (in-memory data loading)

**Key Design Patterns:**
- **Dependency Injection** for database connections and JWT validator
- **Middleware** for JWT validation and tenant context extraction
- **Repository Pattern** (Data Access Layer) for tenant-scoped queries
- **Deny-by-Default Tenancy** - All endpoints validate tenant_id from JWT claims

## 6.3 Dash App: Customer Lifetime Value (CLV)

**Responsibility:** Embedded Plotly Dash application visualizing customer lifetime value metrics for the active tenant.

**Key Interfaces:**
- **Entry Point:** `/dash/customer-lifetime-value/`
- **Callbacks:** Interactive filters triggering data refresh via FastAPI data API
- **Token Handling:** Extracts and validates tenant-scoped JWT from Authorization header

**Dependencies:**
- FastAPI Dashboard Data API (`/api/dashboards/customer-lifetime-value/data`)
- Shared Config Module (JWT validation)

**Technology Stack:**
- Python 3.11+
- Plotly Dash 2.18+
- Dash Bootstrap Components (UI)
- Pandas (data manipulation)
- PyJWT or python-jose (JWT validation)

**Key Design Patterns:**
- **Request-Scoped Context** - JWT decoded per request, tenant_id stored in thread-local or request context
- **Server-Side Callbacks** - All data fetching happens server-side with tenant context
- **No Direct Storage Access** - All data retrieved via FastAPI API (validates token exchange pattern)

## 6.4 Dash App: Risk Analysis

**Responsibility:** Embedded Plotly Dash application visualizing risk analysis metrics for the active tenant.

**Key Interfaces:**
- **Entry Point:** `/dash/risk-analysis/`
- **Callbacks:** Interactive filters triggering data refresh via FastAPI data API
- **Token Handling:** Extracts and validates tenant-scoped JWT from Authorization header

**Dependencies:**
- FastAPI Dashboard Data API (`/api/dashboards/risk-analysis/data`)
- Shared Config Module (JWT validation)

**Technology Stack:**
- Python 3.11+
- Plotly Dash 2.18+
- Dash Bootstrap Components (UI)
- Pandas (data manipulation)
- PyJWT or python-jose (JWT validation)

**Key Design Patterns:**
- Same as CLV Dash App (shared architecture pattern)

## 6.5 Shared Config Module

**Responsibility:** Provides consistent JWT validation settings, constants, and type definitions across all services (FastAPI and Dash apps).

**Key Interfaces:**
- **JWT Configuration:**
  - `JWT_SECRET_KEY` - Shared secret for HMAC signing
  - `JWT_ALGORITHM` - "HS256"
  - `JWT_ISSUER` - "kyros-poc"
  - `USER_TOKEN_EXPIRY` - 3600 seconds (1 hour)
  - `TENANT_TOKEN_EXPIRY` - 1800 seconds (30 minutes)

- **Validation Functions:**
  - `validate_user_token(token: str) -> UserAccessToken`
  - `validate_tenant_token(token: str) -> TenantScopedToken`

- **Mock Data:**
  - `MOCK_USERS` - Pre-defined user records
  - `PRE_GENERATED_TOKENS` - Mock JWTs for testing

**Dependencies:**
- None (pure configuration and utility functions)

**Technology Stack:**
- Python 3.11+ (shared package)
- PyJWT or python-jose (JWT operations)
- Pydantic (data models for token claims)

**Key Design Patterns:**
- **Single Source of Truth** for JWT configuration (solves root cause from brainstorming)
- **Immutable Configuration** - Settings loaded once at startup, never modified
- **Type-Safe Exports** - Pydantic models for all token claim structures

## 6.6 Tenant Metadata Database (SQLite)

**Responsibility:** Stores tenant configuration, user-tenant mappings, dashboard assignments, and provides fast lookups for authorization and metadata resolution.

**Key Interfaces:**
- **Tables:**
  - `tenants` - Tenant records
  - `users` - User records
  - `user_tenants` - User-tenant access mappings
  - `dashboards` - Dashboard definitions
  - `tenant_dashboards` - Dashboard assignments

**Dependencies:**
- None (standalone SQLite file)

**Technology Stack:**
- SQLite 3.45+
- Schema designed for PostgreSQL compatibility (standard SQL)

**Key Design Patterns:**
- **Seed Scripts** for initial data population (automated setup)
- **Validation Scripts** to verify data integrity before demos
- **Transaction Isolation** for consistent reads

## 6.7 In-Memory Data Store (Pandas)

**Responsibility:** Loads mock tenant data from CSV/Parquet files into Pandas DataFrames at FastAPI startup, providing fast tenant-filtered queries.

**Key Interfaces:**
- **Data Loading:**
  - `load_tenant_data(tenant_id: str, dashboard_slug: str) -> pd.DataFrame`
  - `filter_data(df: pd.DataFrame, filters: dict) -> pd.DataFrame`

**Dependencies:**
- Local filesystem (`data/mock-data/` directory)

**Technology Stack:**
- Python Pandas
- CSV/Parquet file formats

**Key Design Patterns:**
- **Lazy Loading** - DataFrames loaded on first request per (tenant_id, dashboard_slug)
- **In-Memory Cache** - DataFrames kept in memory for duration of FastAPI process
- **Immutable Data** - Mock data never modified at runtime

---
