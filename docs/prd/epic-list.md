# Epic List

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
