## **Purpose**

Deliver a secure, multi-tenant Plotly SaaS platform where clients log in to view dashboards filtered to their organization (tenant). Kyros actuaries/admins can view multiple tenants. MVP is read-only except for saving filters/preferences per tenant. Data ingestion and scoring remain external to this MVP.

## **High-Level Architecture**

Current:
![[current_architecture.jpg]]
 

Proposed (WIP):
![[proposed_architecture.jpg]]

Proposed Sequence View:
  ![[main_sequence.png]]

**Core Components:**

1. [**Authentication & Tenant Isolation**](auth-tenant-isolation) – Azure AD B2C (OIDC) issues JWTs with tenant_id and roles .
    
2. [**Shell UI (Next.js)**](shell-ui) – Entry point for login, dashboard selection, and embedding Dash apps .
    
3. [**FastAPI Monolith**](fast-api-monolith) – Enforces JWT validation, resolves tenant metadata, serves data/config to Dash apps .
    
4. [**Plotly Dash Apps**](plotly-dash) – Embedded visualizations scoped to tenant data.
    
5. [**Tenant Metadata DB**](tenant-metadata-db) – Stores tenant details, dashboard assignments, config JSON.
    
6. **Object Storage (Azure Storage)** – Tenant-segregated paths for processed data. _Likely to remain unchanged from current architecture._
    
7. [**Observability**](https://kyros.atlassian.net/wiki/spaces/PSD/pages/40861707) – Prometheus + Grafana for metrics, Loki for logs.
    

## **MVP Features**

### **1. User Authentication & Tenant Isolation**

- **IdP:** Azure AD B2C with OIDC.
    
- **JWT Claims:** tenant_id, role, email, sub.
    
- **Token Lifetime:** 1 hour; refresh via B2C flow.
    
- **FastAPI Middleware:** Validates JWT, extracts tenant_id & role, attaches to request context .
    
- **Access Enforcement:** Always resolve tenant_id from validated claims; never accept from client input .
    

### **2. Multi-Tenant Application Behavior**

- **Tenant Metadata:** Maps tenant_id to dashboards, storage paths, display config .
    
- **Dash Apps:** Load only tenant-filtered data; no global dataset access.
    
- **Dynamic Config:** Branding, filters, and component visibility driven by metadata.
    
- **Storage Layout:** /processed/<tenant_id>/... for results; /uploads/<tenant_id>/... for incoming data.
    

### **3. Shell UI**

- **Login:** OIDC redirect; store tokens securely (HTTP-only cookie or memory).
    
- **Dashboard Listing:** Fetched from FastAPI for logged-in tenant.
    
- **Embedding:** JWT-secured iframe or dynamic route for Dash apps .
    
- **Routing:** /login, /dashboard/:slug, /logout.
    
- **Security:** HTTPS, CSP headers, clickjacking/XSS protection.
    

### **4. Internal Admin API (for TC3 Pipeline Integration)**

- **Endpoints (Private Ingress Only):**
    
    - POST /admin/tenants/{id}/metadata
        
    - POST /admin/tenants/{id}/dashboards
        
    - POST /admin/rotate-secret
        
- **Auth:** Client credentials (AAD confidential client) or mTLS.
    
- **Purpose:** Update tenant metadata, assign dashboards, rotate secrets.
    

### **5. Monitoring & Logging**

- **Metrics:** Prometheus/Grafana with tenant_id labels.
    
- **Logs:** Loki with structured logging; include sub, email, tenant_id.
    
- **Audit Trails:** Postgres audit_logs table for dashboard access & metadata changes.
    

## **MVP Scope**

**Included:**

- Tenant-based auth & data filtering.
    
- Config-driven dashboard rendering.
    
- Read-only dashboards with saved preferences.
    
- Observability with per-tenant metrics/logging.
    
- Private admin API for metadata updates.
    

**Excluded (Post-MVP):**

- Self-service onboarding.
    
- Tenant-level RBAC beyond admin/viewer.
    
- File uploads/downloads via UI.
    
- Per-tenant custom Dash code.
    

## **Deployment Sequence**

See: [SaaS MVP Rollout Work Plan](saas-mvp-rollout)

## **Security Considerations**

- Never trust client-supplied tenant_id; always from JWT.
    
- Short-lived access tokens; refresh via secure flow.
    
- Apply least privilege to storage and DB access.
    
- Enforce HTTPS everywhere; apply CSP & frameguard headers.
    

# Glossary of Terms/Acronyms

## **Authentication & Identity**

- **OIDC** – _OpenID Connect_
    
    An identity layer on top of OAuth 2.0 used for secure authentication and user identity claims (sub, email, roles).
    
- **OIDC + PKCE** – _Proof Key for Code Exchange_
    
    An extension of OAuth/OIDC for public clients (like browsers), prevents token interception attacks.
    
- **IdP** – _Identity Provider_
    
    Service that authenticates users and issues tokens (Azure AD B2C in this design).
    
- **Azure AD B2C** – _Azure Active Directory Business-to-Consumer_
    
    Microsoft’s cloud identity platform; handles user login, MFA, token issuance.
    
- **JWT** – _JSON Web Token_
    
    Compact signed token containing user and tenant claims (tenant_id, roles, sub).
    
- **sub** – _Subject Identifier_
    
    Unique, immutable user identifier inside a JWT.
    
- **RBAC** – _Role-Based Access Control_
    
    Authorization scheme controlling what roles (admin, viewer) can do.
    
- **SSO** – _Single Sign-On_
    
    Ability to log in once and access multiple services using the same identity provider session.
    

## **Backend & APIs**

- **API** – _Application Programming Interface_
    
    Interface exposed by FastAPI monolith for Shell UI, Dash apps, and Admin functions.
    
- **DAL** – _Data Access Layer_
    
    Module in the monolith that maps tenant_id + dashboard_slug to safe queries and storage paths.
    
- **RLS** – _Row-Level Security_
    
    PostgreSQL feature to enforce per-tenant data isolation at the database row level.
    
- **CRUD** – _Create, Read, Update, Delete_
    
    Standard database operations (Admin API covers tenant/dashboard CRUD).
    
- **mTLS** – _Mutual TLS_
    
    Strong authentication using TLS client certificates (used for Admin API security).
    

## **Frontend & Visualization**

- **UI** – _User Interface_
    
    The front-end interface (Next.js Shell UI).
    
- **UX** – _User Experience_
    
    The holistic design of the UI flow (login, tenant chooser, dashboard embed).
    
- **SSR** – _Server-Side Rendering_
    
    Next.js feature to render pages server-side for performance and SEO.
    
- **SSG** – _Static Site Generation_
    
    Next.js feature for pre-rendering static content.
    
- **CSP** – _Content Security Policy_
    
    Browser header restricting what resources/scripts can load (prevents XSS).
    
- **HSTS** – _HTTP Strict Transport Security_
    
    Security header forcing all traffic to use HTTPS.
    
- **Slug** –
    
    A stable, URL-safe identifier for tenants and dashboards (acme-corp, customer-lifetime-value).
    

## **Data & Storage**

- **DB** – _Database_
    
    Stores metadata (PostgreSQL) or data (Databricks, Azure Storage).
    
- **JSONB** – _JSON Binary_
    
    PostgreSQL’s binary JSON storage type, allows indexing and querying of JSON efficiently.
    
- **TTL** – _Time To Live_
    
    Expiry time for caches or tokens (15–30 min for tenant-scoped tokens).
    
- **UC** – _Unity Catalog_
    
    Databricks’ data governance layer for managing databases/tables/catalogs per tenant.
    

## **Observability & Ops**

- **SLO** – _Service Level Objective_
    
    Target performance/availability thresholds (99.9% uptime, P95 latency).
    
- **P95 / P50** – _95th Percentile / Median_
    
    Latency distribution metrics; “95% of requests must be faster than X ms.”
    
- **RPS** – _Requests Per Second_
    
    Metric for service throughput.
    
- **PII** – _Personally Identifiable Information_
    
    Sensitive user data (emails, tokens) requiring special handling.
    
- **Prometheus** – (no acronym, open-source project)
    
    Metrics collection system, scrapes /metrics endpoints.
    
- **Grafana** – (no acronym, open-source project)
    
    Visualization tool for Prometheus metrics, logs, dashboards.
    
- **Loki** – (no acronym, open-source project)
    
    Log aggregation system, paired with Promtail for scraping.
    
- **Promtail** – (no acronym, part of Loki stack)
    
    Agent that scrapes logs from containers and ships to Loki.
    
- **OpenTelemetry (OTel)** – _Open Telemetry_
    
    Standard for distributed tracing and correlation across services.
    
- **PgBouncer** – (no acronym, project name)
    
    PostgreSQL connection pooler to improve performance.
    
- **HA** – _High Availability_
    
    Ensures uptime with redundant/replicated infrastructure.
    

## **Deployment & Environment**

- **MVP** – _Minimum Viable Product_
    
    The simplest functional version of the SaaS that meets core goals.
    
- **MLP** – _Minimum Lovable Product_
    
    Post-MVP refinement that improves user experience
    
- **CI/CD** – _Continuous Integration / Continuous Deployment_
    
    Automation for testing and deploying software changes.
    
- **VNet** – _Virtual Network_
    
    Azure’s private network boundary for isolating services.
    
- **Key Vault** – (Azure service)
    
    Manages and secures application secrets/keys.
    
- **Ingress** – (Kubernetes/Cloud term)
    
    Network entry point routing external requests to services.