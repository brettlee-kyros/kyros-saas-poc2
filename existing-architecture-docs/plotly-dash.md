## **Purpose**

Deliver tenant-isolated dashboards that Kyros can embed inside the Shell UI. Each request is authorized for a **single tenant** and a single **Unity Catalog catalog**; all queries and assets must respect that scope.

## **Non-goals (MVP)**

- No cross-tenant views in a single page.
    
- Minimal write paths (only preferences).
    

## **Actors & components**

- **Shell UI (Next.js)** – Auth flow, tenant selection, embeds Dash via same-origin path and header-injected token.
    
- **FastAPI Monolith** – Public API for Dash/Shell, token exchange, metadata, query execution; internal Admin API.
    
- **Dash Runtime** – One or more Plotly Dash apps served behind the same ingress as the monolith (recommended: separate deployment but same origin path /dash/{slug}).
    
- **Databricks SQL Warehouse** – Executes SQL against Unity Catalog.
    
- **Tenant Metadata DB (PostgreSQL)** – Authoritative metadata
    

## **Tenancy model & claims**

- User authenticates with Azure AD B2C.
    
- Shell selects an **active tenant** and calls **token exchange**.
    
- FastAPI returns a **short-lived tenant-scoped JWT** with claims:
    
    - sub, tenant_id, roles
        
    - env
        
    - uc_catalog (resolved via tenant_datastores for (tenant_id, env) primary)
        
    - exp (~15–30 min)
        

_Dash receives this token **via HTTP header injected by the reverse proxy**; client JS never sees it._

## **Embedding & routing**

Recommended pattern: **same-origin reverse proxy**.
```
/tenant/{tenantSlug}/dashboard/{dashboardSlug}   (Shell UI page)
  └── embeds → /dash/{dashboardSlug}             (Dash upstream service)
        (ingress injects Authorization: Bearer <tenant-scoped token>)
```
Security headers on Dash responses:
- Content-Security-Policy: frame-ancestors 'self' https://shell-origin
- X-Frame-Options: SAMEORIGIN
- Cache-Control: private, no-store

## **Data access pattern**

1. Dash Decodes JWT
    
2. Dash server holds a service principal credential (from Key Vault), decodes the tenant-scoped token, takes uc_catalog claim, and executes queries directly.
    

> **Note:** this is the lightest lift approach for MVP. An alternate approach that centralizes query construction in FastAPI would likely be better for observability.

## **Catalog resolution**

- Table: tenant_datastores(tenant_id, env, uc_workspace, uc_catalog, is_primary)
    
- Rule: exactly **one primary per (tenant_id, env)**.
    
- Resolver:
    

`SELECT uc_catalog, uc_workspace FROM tenant_datastores WHERE tenant_id = $1 AND env = $2 AND is_primary = true;`

- Token exchange adds uc_catalog to the tenant-scoped JWT. Dash can read and cache it per request; the monolith may verify it on receipt of a query request.
    

## **Dash app layout**

- **App registry**: maps dashboard_slug → app factory and its **query templates** (schema/table/columns).
    
- **App factory** reads tenant context each request:
    
    - Extracts tenant_id, uc_catalog, env from Authorization header (validate).
        
    - Stashes them in a request-local context for callbacks.
        
- **Callbacks** only accept filter inputs; they never accept catalog/schema/table.
    

## **Configuration & metadata**

- Dashboard definitions (per dashboard_slug):
    
    - **Query templates** (schema/table/columns, safe identifier lists).
        
    - Default filters, time windows.
        
    - Allowed filter ranges (server enforced).
        
- Tenant-level flags in tenants.config_json:
    
    - Branding, feature toggles, thresholds.
        
- Datastore mapping in tenant_datastores (above).
    

## **Preferences (optional write path)**

- Dash POSTs preferences to POST /api/preferences with {filters, layout}.
    
- Monolith upserts (tenant_id, sub) → JSONB.
    
- No business logic in Dash regarding authorization.
    

## **Performance & scaling**

- Use **Databricks SQL Warehouse** appropriate size; enable result caching as permitted.
    
- Server-side **dataset caching** (later): cache (tenant_id, dashboard_slug, filter_hash) for short TTLs.
    

## **Observability**

- **Metrics**:
    
    - dash_callback_duration_seconds{app_slug,callback,tenant_id}
        
    - dash_callback_errors_total{app_slug,callback,tenant_id}
        
- **Logs** (JSON to Loki): include tenant_id, tenant_slug, dashboard_slug, trace_id, latency_ms.
    
- **Traces** (optional): set attributes kyros.tenant_id, kyros.tenant_slug on spans.
    
- Grafana dashboards: “Dash Apps Health” + “Tenant Drill-down” (already defined in Monitoring spec).
    

## **Security**

- Tenant-scoped token in **header only**, short TTL (15–30 min).
    
- Enforce CSP frame-ancestors, HSTS, and no tokens in URLs or client storage.
    
- Server-side identifier allowlist; strong input validation on filters.
    
- Dash service principal secrets pulled from **Key Vault** (or call monolith to execute SQL).
    
- Network policy: Dash can reach only the monolith and (if needed) Databricks; never public data endpoints.
    

## **Failure modes & UX**

- Invalid/expired token → 401 to Shell; Shell refreshes token/exchange and reloads.
    
- Tenant has no primary datastore for env → 500 with correlation id; alert raises; admin fix mapping.
    
- Query timeouts → render friendly “Data temporarily unavailable” with retry/backoff.
    
- Filter outside allowed range → 422 with guidance.
    

## **Testing & DoD**

- **Unit**: identifier validation, SQL builder uses correct catalog, query template constraints.
    
- **Integration**: for a tenant in prod, a request builds SQL with the **prod** catalog; swapping primary catalog updates within token TTL.
    
- **Security**: attempts to inject catalog/table via inputs fail; no tokens/PII in logs.
    
- **Performance**: P95 latency for data endpoints under agreed SLOs with typical filter sizes.
    

**Definition of Done**

- All Dash routes operate only with header-injected tenant-scoped tokens.
    
- Each dashboard uses the correct uc_catalog for the active (tenant_id, env).
    
- No dashboard accepts identifier inputs from the client.
    
- Metrics/logs present and per-tenant filterable in Grafana/Loki.
    

## **Open questions**

- Centralized execution (monolith) vs. direct DBSQL from Dash in MVP?
    
    Recommendation: **centralized in monolith as an MLP follow-on**; allows uniform policy, caching, and auditing.
    
- Cross-env viewing (stage/prod switcher) in the UI? If yes, pass an explicit env and resolve catalog accordingly.
    
- Result caching policy for high-cost queries (TTL, invalidation on data refresh)?
    

## **Implementation checklist (per repo)**

- **DB**: create tenant_datastores + admin CRUD; enforce one primary per (tenant, env).
    
- **Monolith**:
    
    - Token exchange includes uc_catalog and env.
        
    - /api/tenant/{id} returns datastores (or current env primary).
        
    - /api/dashboards/{slug}/data builds SQL server-side using trusted identifiers.
        
    
- **Dash**:
    
    - Request-scoped tenant context reader (decodes header JWT).
        
    - Registry of dashboards → query templates (no free-form identifiers).
        
    - Metrics decorators on callbacks; structured logs.
        
    
- **Shell UI**:
    
    - No changes beyond token exchange; ensure embed path stays same-origin to receive header.