# 3. Tech Stack

| Category | Technology | Version | Purpose | Rationale |
|----------|-----------|---------|---------|-----------|
| **Frontend Language** | TypeScript | 5.3+ | Type-safe Shell UI development | Prevents runtime errors in token handling; enables shared types with backend via shared-config package |
| **Frontend Framework** | Next.js | 14.2+ | Shell UI with SSR, API routes | Built-in API routes enable reverse proxy pattern; App Router provides modern routing; server components reduce client JS |
| **UI Component Library** | Tailwind CSS + Headless UI | Tailwind 3.4+, Headless UI 2.1+ | Styling and accessible components | Rapid UI development with utility-first CSS; Headless UI provides accessible primitives for tenant selector and modals |
| **State Management** | React Context + zustand | zustand 4.5+ | Client-side state (active tenant, user) | Lightweight for PoC scale; zustand handles tenant context persistence across navigation; Context for auth state |
| **Backend Language** | Python | 3.11+ | FastAPI and Dash applications | Unified language across API and Dash apps; strong data science ecosystem (Pandas) for mock data handling |
| **Backend Framework** | FastAPI | 0.115+ | API monolith (auth, token exchange, data) | Async performance; automatic OpenAPI docs; Pydantic validation; native async DB drivers for future PostgreSQL migration |
| **API Style** | REST | OpenAPI 3.0 | HTTP JSON APIs consumed by Shell UI and Dash | Simplest for PoC; well-understood; easy to test; matches existing architecture documentation |
| **Database** | SQLite | 3.45+ | Tenant metadata storage | Zero-config for PoC; schema designed for PostgreSQL compatibility (standard SQL, UUIDs as TEXT, JSONB as TEXT) |
| **Cache** | In-Memory (Python dict) | - | Tenant metadata caching in FastAPI | Simplest solution for PoC; no external cache server needed; sufficient for local single-instance deployment |
| **File Storage** | Local Filesystem (Pandas) | - | Mock tenant data (CSV/Parquet → DataFrames) | In-memory DataFrames loaded at startup; simulates Azure Storage without infrastructure; easy to inspect/modify test data |
| **Authentication** | Mock FastAPI Endpoints | - | Simulated user login and JWT issuance | Pre-generated JWTs stored as constants; validates token exchange flow without OIDC complexity; documented as PoC-only |
| **Frontend Testing** | Vitest + React Testing Library | Vitest 1.6+, RTL 16+ | Shell UI component and hook tests | Fast Vite-native test runner; RTL for user-centric testing; tests tenant selector and token refresh logic |
| **Backend Testing** | pytest + httpx | pytest 8.3+, httpx 0.27+ | FastAPI endpoint and token exchange tests | Async test client; validates JWT generation, tenant mapping, and data filtering logic |
| **E2E Testing** | Playwright | 1.47+ | Full flow: login → tenant select → dashboard embed | Tests the critical path identified in brainstorming; validates reverse proxy header injection and Dash rendering |
| **Build Tool** | npm/pip | npm 10+, pip 24+ | Package management | Standard tools; npm for frontend monorepo, pip for Python dependencies |
| **Bundler** | Vite (via Next.js) | - | Next.js handles bundling | Modern fast bundler built into Next.js 14; Turbopack available for faster dev builds |
| **IaC Tool** | Docker Compose | 2.29+ | Local orchestration | Defines Shell UI, FastAPI, and Dash services with networking; enables one-command startup and reset |
| **CI/CD** | None (PoC) | - | Manual testing locally | PoC does not require CI/CD; GitHub Actions can be added in MVP for automated testing and deployment |
| **Monitoring** | None (PoC) | - | Out of scope per brainstorming | Observability eliminated in SCAMPER analysis; logging to stdout only; MVP will add Prometheus/Grafana/Loki |
| **Logging** | Python logging + console | - | Stdout logging for debugging | Structured JSON logs in FastAPI/Dash; visible in Docker Compose logs; sufficient for PoC validation |
| **CSS Framework** | Tailwind CSS | 3.4+ | Utility-first styling | Rapid prototyping; small bundle size; consistent design system; integrates well with Next.js and Headless UI |

---
