## Purpose

Serve Plotly Dash dashboards to external clients and Kyros staff while guaranteeing strong tenant isolation. The FastAPI monolith is the single gatekeeper for data and configuration consumed by Dash apps and the Shell UI.

## Design Tenets

1. Deny‑by‑default tenancy: every request is evaluated against an active tenant derived from a validated JWT; the client never chooses the tenant id directly.
    
2. Metadata‑driven behavior: dashboards, features, and data locations come from tenant metadata.
    
3. Safe multi‑tenant users: a user may belong to many tenants, but any one runtime token is scoped to exactly one tenant.
    

## High‑Level Architecture

- Shell UI (Next.js): login, dashboard list, embed Dash with a bearer token.
    
- FastAPI Monolith:
    
    - Auth middleware: validates JWTs, resolves active tenant, injects request.state.
        
    - Public API surface for Shell and Dash.
        
    - Internal admin surface (private ingress) for TC3/automation.
        
    - Data Access Layer (DAL) that maps (tenant_id, dashboard_slug) to storage/queries.
        
- Tenant Metadata DB (Postgres): tenants, dashboards, user↔tenant mapping, feature flags, preferences, audit logs.
    
- Object Storage (Azure Storage): tenant‑scoped prefixes, e.g., /processed/<tenant_id>/....
    

## Request Lifecycle

1. Ingress receives HTTPS request.
    
2. Auth middleware:
    
    - Validates signature/expiry against Azure AD B2C JWKs.
        
    - Extracts sub, email, roles, and either tenant_id (tenant‑scoped token) or tenant_ids (user token).
        
    - If request targets tenant resources:
        
        - Determine active tenant (tenant_id). For user tokens, require the selected tenant via /api/token/exchange or a server‑side session.
            
        - Load and cache tenant metadata (see caching).
            
    - Attach request.state.user, request.state.tenant_id, request.state.roles, request.state.meta.
        
3. Route handler executes business logic using the DAL; all reads/writes are implicitly tenant‑scoped.
    
4. Structured logging and audit recording include {sub,email,tenant_id,route,action}.
    

## Data Access Layer

A narrow module responsible for turning tenant context and a logical request into concrete reads:

- Input: tenant_id, dashboard_slug, optional filters.
    
- Resolves:
    
    - Storage path prefix: /processed/<tenant_id>/...
        
    - Dataset names or table pointers (if using external tables).
        
    - Tenant feature toggles and display constraints.
        
- Executes read operations via approved connectors or precomputed artifacts.
    
- Returns sanitized, tenant‑filtered frames or JSON.
    

Guardrails:

- DAL never accepts tenant_id from the caller; it only reads request.state.tenant_id.
    
- DAL implements safe defaults (no tenant_id → fail closed).
    
- Single entrypoint functions per dashboard/data domain to avoid ad‑hoc file access in routes.
    

## Metadata Model

See [Tenant Metadata DB](tenant-metadata-db) .

## API Surface (MVP)

Public (requires bearer token; CORS restricted to Shell origin)

- GET /api/me
    
- POST /api/token/exchange → include uc_catalog in the tenant-scoped token claims (short-lived). Example claim: "uc_catalog": "kyros_acme_prod".
    
- GET /api/tenant/{tenant_id} → include uc_catalog, uc_workspace.
    
- GET /api/tenant/{tenant_id}/dashboards → include uc_catalog at the top level 
    
- GET /api/dashboards/{slug}/data
    
- POST /api/preferences
    

Internal (private ingress; client‑credentials or mTLS)

- POST /admin/tenants / PUT /admin/tenants/{id}
    
- POST /admin/tenants/{id}/dashboards
    
- POST /admin/rotate-secret
    
- POST /admin/reload-cache
    

## Multi‑Tenant Behavior in Dash

- Shell embeds Dash with a tenant‑scoped token.
    
- Every Dash callback calls FastAPI endpoints with that token; no direct storage reads.
    
- Dash respects feature toggles in config_json.
    

## Caching Strategy

- **Metadata cache** in the monolith (e.g., Redis or in‑process).
    
- **Dataset cache (optional, later)**.
    

## Object Storage Conventions

- Read paths: /processed/<tenant_id>/<dashboard_slug>/...
    
- Optional uploads: /uploads/<tenant_id>/...
    

## Security Model

- Only accept tenant_id from validated tokens.
    
- Short‑lived access tokens; short‑lived tenant‑scoped tokens for Dash.
    
- Strict HTTP headers on embedded dashboards.
    

## Observability and Audit

- Structured logs with tenant context.
    
- Prometheus metrics labeled with tenant_id.
    

## Performance and Scaling

- Stateless app instances; horizontal scale.
    
- DAL optimizes for partitioned artifacts and server‑side filtering.
    

## Error Model

- 401 Unauthorized
    
- 403 Forbidden
    
- 404 Not Found
    
- 422 Unprocessable
    

## Testing Strategy

- Unit tests for middleware, DAL.
    
- Contract tests for public/admin endpoints.
    
- Multi‑tenant scenarios and negative tests.
    

## MVP Rollout Plan

1. Deploy FastAPI monolith with read‑only endpoints.
    
2. Onboard pilot tenant.
    
3. Enable metrics dashboards.
    
4. Deploy admin private ingress.
    
5. Add preferences write‑path.
    

## Configuration and Secrets

- Environment variables for IdP, DB, cache.
    
- Secrets in Azure Key Vault.