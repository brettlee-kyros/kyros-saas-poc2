## Purpose

The Tenant Metadata DB stores configuration, mapping, and access control information for tenants, users, and dashboards. It is the system of record for multi-tenant behavior in the Kyros SaaS platform, powering the FastAPI monolith’s access control and configuration APIs.

Scope and Objectives

- Provide **authoritative metadata** for tenants, dashboards, user-to-tenant mappings, feature flags, and preferences.
    
- Serve **low-latency lookups** to the FastAPI monolith with strict tenant scoping.
    
- Support **JSON-based dynamic configuration** without requiring frequent schema changes.
    
- Provide **audit logs** for tenant-level operations.
    
- Allow for future scaling to handle more tenants and richer metadata without full redesign.
    

## Design Tenets

1. **Tenant isolation first** – All queries are tenant-scoped, keyed by tenant_id, and reject cross-tenant access by default.
    
2. **Source of truth** – Metadata in this DB is authoritative; no duplication of tenant config elsewhere.
    
3. **JSON for flexibility** – Use JSONB fields for dynamic dashboard config and feature toggles.
    
4. **Extensible without downtime** – Prefer additive schema changes and feature flags over destructive changes.
    
5. **Performance** – Index all tenant- and dashboard-scoped queries to keep lookups sub-50ms.
    

## Suggested Technology Choice

**Azure Database for PostgreSQL – Flexible Server**  
Chosen for:

- Native **JSONB** for flexible per-tenant config.
    
- **Row-Level Security (RLS)** for optional in-database enforcement.
    
- Mature ecosystem and Python/FastAPI integration via async drivers.
    
- Good operational balance of cost, HA, and managed features.
    

## Open Design Question: RDBMS Decision Guide

We will default to PostgreSQL for MVP, but leave the door open for alternatives based on long-term needs.

|   |   |   |
|---|---|---|
|Option|Pros|Cons|
|**Azure Database for PostgreSQL – Flexible Server**|JSONB, RLS, extensions, developer-friendly, async driver support|Fewer built-in analytics/reporting than Azure SQL|
|**Azure SQL Database**|Native HA, mature tooling, security predicates, serverless tier|JSON is less ergonomic, no native JSON type, T-SQL only|
|**Azure Cosmos DB for PostgreSQL (Citus)**|Horizontal scale, sharding by tenant_id, distributed queries|More ops complexity, cost, overkill for MVP|
|**Azure Database for MySQL – Flexible Server**|Managed, HA, familiar to MySQL teams|Weaker JSON features, no native RLS|

## Proposed Schema

### tenants

|   |   |   |
|---|---|---|
|Column|Type|Notes|
|id|UUID PK|Internal identifier|
|name|TEXT|Display name|
|slug|TEXT|Unique, URL-safe identifier|
|is_active|BOOLEAN|Soft disable for tenant|
|config_json|JSONB|Branding, feature flags, limits|
|created_at|TIMESTAMP|Defaults to now()|

tenant_datastores

|   |   |   |
|---|---|---|
|**Column**|**Type**|**Notes**|
|tenant_id|UUID FK|To tenants|
|env|TEXT|dev/uat/prod|
|uc_catalog|TEXT|Catalog name|
|uc_workspace|TEXT|Workspace name|
|is_primary|BOOLEAN|Default TRUE|
|PRIMARY KEY|UNIQUE (tenant_id, env, uc_catalog)||

### users

|   |   |   |
|---|---|---|
|Column|Type|Notes|
|user_id|UUID PK|sub from JWT|
|email|TEXT|User email|
|created_at|TIMESTAMP|Defaults to now()|

### user_tenants

|   |   |   |
|---|---|---|
|Column|Type|Notes|
|user_id|UUID FK|To users|
|tenant_id|UUID FK|To tenants|
|role|TEXT|admin/viewer/uploader|
|PRIMARY KEY|(user_id, tenant_id)||

### dashboards

|   |   |   |
|---|---|---|
|Column|Type|Notes|
|slug|TEXT PK|URL-safe dashboard identifier|
|title|TEXT|Display name|
|description|TEXT|Optional|
|config_json|JSONB|Layout, thresholds, labels|

### tenant_dashboards

|   |   |   |
|---|---|---|
|Column|Type|Notes|
|tenant_id|UUID FK|To tenants|
|slug|TEXT FK|To dashboards|
|PRIMARY KEY|(tenant_id, slug)||

### preferences

|   |   |   |
|---|---|---|
|Column|Type|Notes|
|tenant_id|UUID||
|user_id|UUID||
|prefs|JSONB|Saved filters, layout|
|PRIMARY KEY|(tenant_id, user_id)||

### audit_logs

|   |   |   |
|---|---|---|
|Column|Type|Notes|
|id|BIGSERIAL PK||
|ts|TIMESTAMP|Event time|
|sub|UUID|User ID from token|
|email|TEXT|User email|
|tenant_id|UUID|Related tenant|
|action|TEXT|e.g., "view_dashboard"|
|resource|TEXT|Slug or path|
|meta|JSONB|Context data|

## Access Patterns

### Common Reads

- GET /api/me → user_tenants join tenants for active list
    
- GET /api/tenant/{tenant_id} → single-row tenants lookup
    
- GET /api/tenant/{tenant_id}/dashboards → join on tenant_dashboards + dashboards
    
- GET /api/dashboards/{slug}/data → resolve dashboard config from metadata
    

### Common Writes

- Preferences save/update
    
- Admin adding tenant or dashboard mapping
    
- Audit log insert
    

## Security

- **App-level**: Always scope queries to tenant_id from validated JWT.
    
- **Optional DB-level**: Enable Postgres RLS policies to enforce tenant scoping inside the DB as defense-in-depth.
    
- **Connection security**: Private Link to VNet, AAD auth for human users, managed identity for app.
    

## Performance Considerations

- Index all (tenant_id, slug) lookups.
    
- Use connection pooling (PgBouncer).
    
- Cache metadata in FastAPI (Redis or in-memory) with short TTL for hot paths.
    

## Observability

- Monitor query latency and connection counts.
    
- Emit DB metrics to Azure Monitor; set alerts for slow queries and replication lag.
    
- Include correlation IDs in audit logs to tie DB actions to API requests.