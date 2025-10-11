## Purpose

The Shell UI is the authenticated entry point to Kyros analytics. It handles OIDC login with Azure AD B2C, lets a user pick an active tenant when they belong to multiple, fetches per‑tenant metadata and dashboard lists, and embeds Plotly Dash apps using a short‑lived, tenant‑scoped token. It enforces a secure, consistent frame and navigation experience for all dashboards.

## Scope and Objectives

- Provide a secure login flow using Azure AD B2C (OIDC + PKCE).
    
- Show the user’s authorized tenants; support tenant selection and switching.
    
- List dashboards available to the active tenant and embed them safely.
    
- Pass only a tenant‑scoped token to embedded Dash; never expose long‑lived tokens.
    
- Apply tenant‑specific branding and feature flags.
    
- Offer a minimal preferences UX (optional) for saving filters/layout via the API.
    

**Out of scope (MVP):** self‑service onboarding, in‑app role administration, file uploads.

## Key Design Principles

1. **Claims are the source of truth**: authorization is based on validated tokens; the client never supplies tenant_id for enforcement.
    
2. **One active tenant at a time**: multi‑tenant users select which tenant they are viewing; embedded apps receive a token for that tenant only.
    
3. **Dash is view‑only**: Dash apps never talk to storage directly; all reads go through FastAPI.
    
4. **Least privilege, short lifetimes**: tokens are short‑lived and scoped; headers and CSP prevent embedding and script abuse.
    
5. **Use Next.js for the Shell UI**: [Next.js](https://nextjs.org/) offers built-in server-side rendering (SSR), static site generation (SSG), and API routes; allowing fast initial loads, secure integration with Azure AD B2C, and consistent branding for all tenants.
    

## Slug: Definition and Purpose

A **slug** is a URL‑safe identifier used in routing and lookups.

- **Tenant slug**: a unique, stable string representing a tenant; e.g.,  
    Tenant name: “Acme Corporation” → acme-corp
    
- **Dashboard slug**: a unique, stable string for a dashboard; e.g.,  
    Dashboard title: “Customer Lifetime Value” → customer-lifetime-value
    

Usage:

- **Routing**:
    

  `/tenant/acme-corp   /tenant/acme-corp/dashboard/customer-lifetime-value`

- **Lookup** in the Shell UI to map route → metadata entry.
    
- **Branding and display**: the Shell UI can show the tenant name based on slug‑resolved metadata.
    

Rules:

- Slugs are **unique** in their domains (tenants.slug, dashboards.slug).
    
- Slugs should be treated as **immutable** once published.
    
- **Authorization never relies on slug**; slug is cosmetic.
    

## User Journeys

### Login and Tenant Selection

1. User opens Shell UI → redirect to Azure AD B2C if unauthenticated.
    
2. After login, Shell receives ID and access tokens.
    
3. Shell calls GET /api/me to retrieve tenant_ids and roles.
    
4. If multiple tenants, user selects active tenant.
    
5. Shell calls POST /api/token/exchange to obtain tenant‑scoped token.
    

### Dashboard Discovery and Embed

1. Shell calls GET /api/tenant/{tenant_id}/dashboards.
    
2. Renders tiles linking to /tenant/{tenantSlug}/dashboard/{dashboardSlug}.
    
3. Embeds Dash app with tenant‑scoped token via header.
    

### Tenant Switching

- Switch triggers new token exchange and metadata reload.
    

## Authentication and Token Handling

- **OIDC Client**: MSAL or NextAuth with PKCE.
    
- **Storage**: Access token in HTTP‑only cookie or memory.
    
- **Tenant‑scoped token**: memory only; 15–30 min lifetime; refresh on 401.
    
- **No tokens in query strings**; use headers.
    

## Routes and Navigation

- /login – start auth
    
- /logout – clear session
    
- / – chooser or dashboard list
    
- /tenant/{tenantSlug} – dashboard list
    
- /tenant/{tenantSlug}/dashboard/{dashboardSlug} – embedded Dash
    
- /401, /403, /404 – error pages
    

## Embedding Dash

Preferred: header‑based token pass‑through via ingress/proxy.  
If iframe used:

- Content-Security-Policy with frame-ancestors set to Shell origin.
    
- X-Frame-Options: SAMEORIGIN.
    

## Shell UI Responsibilities

- Fetch identity and metadata from API.
    
- Maintain active tenant state.
    
- Apply tenant branding.
    
- Save preferences via POST /api/preferences.
    
- Handle errors with redirects or messages.
    

## API Contracts

`GET  /api/me POST /api/token/exchange GET  /api/tenant/{tenant_id} GET  /api/tenant/{tenant_id}/dashboards POST /api/preferences`

## Security Controls

- HTTPS + [HSTS](https://en.wikipedia.org/wiki/HTTP_Strict_Transport_Security).
    
- Strict CSP ([Content-Security-Policy](https://content-security-policy.com/)).
    
- No tokens in localStorage or URL.
    
- CSRF protection for POSTs.
    
- Avoid PII in logs.
    

## State Management and Caching

- Use React Query/SWR.
    
- Cache keys include active tenant.
    
- Short TTLs (30–120s).
    

## Performance and UX

- Preload chooser and dashboard list.
    
- Lazy‑load tiles.
    
- Skeleton loaders for slow calls.
    

## Observability

- Front‑end error reporting (Sentry?).
    
- Correlation IDs from API responses.
    
- Tenant slug in analytics.
    

## Configuration

- OIDC client settings.
    
- Allowed embed origins.
    
- Feature flags: ENABLE_TOKEN_EXCHANGE, SHOW_TENANT_SWITCHER, ENFORCE_HEADER_EMBED.
    

## Testing and Acceptance

- Test auth flows, routing, embedding, tenant switching, and security headers.
    
- Definition of Done:
    
    - **All routes are behind authentication** (no public dashboard access).
        
    - **Tenant chooser and token exchange work end-to-end** for both single- and multi-tenant users.
        
    - **Dashboards embed successfully** using header-injected, tenant-scoped tokens.
        
    - **Error pages** for 401, 403, and 404 are implemented and reachable.
        
    - **Security and UX requirements** (no tokens in URLs, CSP headers set) are satisfied.
        
    - **Basic accessibility** is confirmed.
        
    

## Risks and Mitigations

- **Token leak** → header injection; memory storage only.
    
- **Stale tenant selection** → refresh /api/me at start.
    
- **CSP breakage** → staging allowlist.
    

## Examples

Example URLs:

`/tenant/acme-corp /tenant/acme-corp/dashboard/customer-lifetime-value`

Example tenant metadata:

`{   "id": "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4",   "name": "Acme Corporation",   "slug": "acme-corp",   "is_active": true,   "config_json": {     "branding": { "logoUrl": "/logos/acme.svg", "primary": "#0052cc" },     "features": { "showExperimental": false }   } }`