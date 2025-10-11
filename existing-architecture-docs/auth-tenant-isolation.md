## **Purpose**

Enable secure, multi-tenant access to Plotly Dash applications and APIs so that each authenticated user can only access the dashboards, datasets, and features authorized for their assigned tenant(s).

This architecture enforces tenant isolation at every entry point and provides the foundation for future role-based and fine-grained access controls.

## **Core Requirements**

### **Identity Provider (IdP)**

- **Azure AD B2C** (OIDC-compliant).
    
- Issues ID & access tokens with claims:
    
    - sub (user ID)
        
    - email (user email)
        
    - roles (e.g., "admin", "viewer", "uploader")
        
    - tenant_ids (array of tenants the user has access to — replaces single tenant_id for multi-tenant users).
        
- Custom claim mapping in B2C to populate tenant data from user attributes or external identity API.
    
- **Token lifetime:** 1 hour; refresh via B2C or frontend redirect.
    

## **Architecture Overview**

**Actors and Components:**

1. **Azure AD B2C** – Authentication & token issuance.
    
2. **Shell UI (Next.js)** – Handles login flow, displays tenant selection, embeds dashboards.
    
3. **FastAPI Auth/Data Services** –
    
    - Middleware validates tokens, extracts active tenant_id & role, and attaches to request.state.
        
    - All API/data access is filtered by active tenant_id.
        
4. **Tenant Metadata DB (Postgres)** – Stores tenants, user↔tenant mappings, dashboard assignments, and feature toggles.
    
5. **Plotly Dash Apps** – Embedded visualizations that load tenant-filtered data from FastAPI endpoints.
    

## **Authentication Flow**

1. **Login**
    
    - User redirected to B2C for OIDC login.
        
    - On return, Shell UI receives **ID token** (frontend session) and **user access token** (API calls).
        
2. **Tenant Discovery**
    
    - Shell UI calls GET /api/me with the user access token.
        
    - FastAPI validates token, queries user_tenants mapping, and returns a list of authorized tenant_ids and roles.
        
3. **Tenant Selection (multi-tenant users)**
    
    - If only one tenant is assigned, set it as the active tenant.
        
    - If multiple, prompt the user to choose.
        
4. **Token Exchange**
    
    - Shell UI posts the chosen tenant to POST /api/token/exchange.
        
    - FastAPI validates the user token & tenant mapping, then issues a **short-lived tenant-scoped token** containing exactly one tenant_id.
        
5. **Embedding Dash**
    
    - Shell UI embeds Dash via a secure iframe or dynamic route.
        
    - The tenant-scoped token is passed via HTTP header (preferred) or reverse proxy header injection.
        
    - Dash app decodes token, loads config, and calls APIs with the active tenant_id from claims.
        

### Sequence Diagram
![[auth_sequence 2.png]]
Source for sequence diagram:
```
@startuml
title Kyros Plotly SaaS – Auth & Tenant Isolation (MVP, compact)

actor U as "User"
participant Shell as "Shell UI"
participant B2C as "Azure AD B2C"
participant Auth as "FastAPI Auth API"
database Meta as "Tenant DB"
participant Data as "FastAPI Data API"
participant Dash as "Dash App"
collections Store as "Azure Storage"
collections Mon as "Prometheus/Grafana"
participant Log as "Loki"

== Login ==
U -> Shell: Open /login
Shell -> B2C: OIDC auth request
B2C --> Shell: Redirect + code
Shell -> B2C: Token exchange
B2C --> Shell: ID + Access tokens

== Tenant discovery ==
Shell -> Auth: GET /me (Bearer user token)
Auth -> Auth: Validate JWT (sig/exp)
Auth -> Meta: Lookup user↔tenants
Meta --> Auth: tenant_ids, roles
Auth --> Shell: tenant_ids
alt Multi-tenant
  U -> Shell: Choose tenant
end

== Token exchange (recommended) ==
Shell -> Auth: POST /token/exchange (tenant)
Auth -> Meta: Verify mapping
Meta --> Auth: OK
Auth --> Shell: Tenant-scoped JWT (short-lived)

== Embed Dash ==
Shell -> Dash: Open /dash/{slug}\n(token via header/proxy)

== Load dashboards ==
Dash -> Data: GET /tenant/{id}/dashboards (Bearer)
Data -> Data: Validate JWT + tenant_id
Data -> Meta: Fetch dashboards/config
Meta --> Data: Config
Data --> Dash: Config

== Data query (tenant-scoped) ==
loop Callbacks / queries
  Dash -> Data: GET /dash/{slug}/data (Bearer)
  Data -> Data: Validate JWT + tenant_id
  Data -> Meta: Resolve path /processed/{id}/...
  Meta --> Data: Path
  Data -> Store: Read data
  Store --> Data: Dataset
  Data --> Dash: Filtered data
end

== Save prefs (optional) ==
Dash -> Data: POST /prefs {filters, layout}
Data -> Data: Validate JWT + tenant_id
Data -> Meta: Upsert prefs JSON
Meta --> Data: OK
Data --> Dash: 200 OK

== Audit & observability ==
Data -> Meta: INSERT audit_log {sub,email,tenant_id,action}
Data -> Mon: Emit metrics (labels: tenant_id, slug)
Data -> Log: Structured logs (tenant_id, sub, route)

== Failures ==
alt Invalid/expired token
  Auth --> Shell: 401
  Data --> Dash: 401
else Unauthorized tenant
  Auth --> Shell: 403
  Data --> Dash: 403
end

@enduml
```

## **Token Requirements**

**Access Token Claims:**

|   |   |
|---|---|
|**Claim**|**Description**|
|sub|User ID|
|email|User email|
|tenant_ids|Array of UUIDs representing authorized tenants|
|tenant_id|Active tenant ID (in tenant-scoped token)|
|roles|[“admin”, “viewer”, “uploader”]|
|exp, iat|Expiration & issued timestamps|

## **Middleware Responsibilities**

- Validate JWT signature using B2C JWKs.
    
- Verify token expiry.
    
- Extract and attach tenant_id, roles, and user to request.state.
    
- Reject requests with invalid tokens, expired tokens, missing claims, or unauthorized tenants.
    
- Apply role decorators to enforce admin/viewer/uploader capability.
    

## **Tenant Enforcement**

**At API Layer:**

- Always derive tenant_id from token claims, never from client input or URL params.
    
- All DB queries and storage lookups are scoped to tenant_id.
    

**At Dash Layer:**

- All callbacks and data fetches use tenant-scoped API calls.
    
- No Dash app accesses storage directly — all data flows through FastAPI for enforcement.
    

## **Tenant Metadata Design**

See [Tenant Metadata DB](tenant-metadata-db) .

## **Roles and Capabilities**

- **Admin** – View, upload, run jobs, manage users.
    
- **Viewer** – View dashboards only.
    

## **Auditing**

- Every API request is tagged with sub, email, and tenant_id.
    
- Store in audit_logs table for compliance and traceability.
    
- Log structured events to Loki; emit metrics to Prometheus with tenant_id label.
    

## **Provisioning & Onboarding for MVP**

- Manual creation of tenant records in metadata DB.
    
- Manual user provisioning in B2C with tenant assignments.
    
- Future: self-service onboarding, tenant-specific IdPs, automated tenant mapping pipelines.
    

## **Failure Cases**

|                                 |                  |
| ------------------------------- | ---------------- |
| **Scenario**                    | **Response**     |
| Missing/expired token           | 401 Unauthorized |
| Missing/invalid tenant_id claim | 403 Forbidden    |
| Tenant not found/inactive       | 403 Forbidden    |