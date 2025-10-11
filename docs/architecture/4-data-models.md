# 4. Data Models

Based on the existing architecture documentation and brainstorming session, the PoC requires data models for tenant metadata, user-tenant relationships, dashboard assignments, and mock tenant data. These models are shared between TypeScript (Shell UI) and Python (FastAPI/Dash) via the shared-config package.

## 4.1 Tenant

**Purpose:** Represents a client organization with isolated data access, configuration, and dashboard assignments.

**Key Attributes:**
- `id`: string (UUID) - **Internal identifier, never exposed in URLs**
- `name`: string - Display name (e.g., "Acme Corporation")
- `slug`: string - **⚠️ PoC ONLY: Used in URLs for routing** - URL-safe identifier (e.g., "acme-corp")
- `is_active`: boolean - Soft disable flag for tenant
- `config_json`: object - Flexible JSONB for branding, feature flags, display settings
- `created_at`: datetime - Timestamp of tenant creation

**⚠️ MVP MIGRATION REQUIREMENT:**
The `slug` is currently exposed in URLs (`/tenant/{tenant_slug}/dashboard/{dashboard_slug}`). In MVP, implement one of these patterns:
1. **Opaque Tokens:** Generate short-lived encrypted tokens that map to tenant IDs server-side
2. **Signed References:** Use HMAC-signed slugs that can be verified but not forged
3. **Session-Based Routing:** Store active tenant in server session, use routes without tenant identifiers

The PoC uses slugs in URLs for demo clarity, but production should never expose predictable identifiers that could enable enumeration or information disclosure.

**TypeScript Interface:**

```typescript
interface Tenant {
  id: string; // UUID - INTERNAL ONLY, never in URLs/responses
  name: string;
  slug: string; // ⚠️ PoC: Exposed in URLs - MVP must use opaque references
  is_active: boolean;
  config_json: {
    branding?: {
      logo_url?: string;
      primary_color?: string;
    };
    features?: {
      show_experimental?: boolean;
    };
  };
  created_at: string; // ISO 8601
}
```

**Relationships:**
- One tenant has many `UserTenant` mappings (users with access)
- One tenant has many `TenantDashboard` assignments (available dashboards)
- One tenant has zero or one `TenantDatastore` (mock data source mapping)

## 4.2 User

**Purpose:** Represents an authenticated user who may have access to one or more tenants.

**Key Attributes:**
- `user_id`: string (UUID) - Subject identifier from JWT (`sub`)
- `email`: string - User email address
- `created_at`: datetime - Timestamp of user creation

**TypeScript Interface:**

```typescript
interface User {
  user_id: string; // UUID, matches JWT 'sub'
  email: string;
  created_at: string; // ISO 8601
}
```

**Relationships:**
- One user has many `UserTenant` mappings (tenants they can access)

## 4.3 UserTenant

**Purpose:** Junction table establishing user access to specific tenants with role assignments.

**Key Attributes:**
- `user_id`: string (UUID) - Foreign key to User
- `tenant_id`: string (UUID) - Foreign key to Tenant
- `role`: string - Access level: "admin" or "viewer"

**TypeScript Interface:**

```typescript
interface UserTenant {
  user_id: string; // UUID
  tenant_id: string; // UUID
  role: 'admin' | 'viewer';
}
```

**Relationships:**
- Belongs to one User
- Belongs to one Tenant
- Composite primary key: (user_id, tenant_id)

## 4.4 Dashboard

**Purpose:** Defines a reusable dashboard template that can be assigned to tenants.

**Key Attributes:**
- `slug`: string - **⚠️ PoC ONLY: Used as primary key for simplicity**
- `title`: string - Display name (e.g., "Customer Lifetime Value")
- `description`: string - Optional description for dashboard listing
- `config_json`: object - Dashboard-specific configuration (layout, thresholds, labels)

**⚠️ MVP MIGRATION REQUIREMENT:**
In production architecture, add a separate `id: UUID` primary key. Never expose database primary keys (whether integer IDs or UUIDs) in URLs or API responses. The `slug` field should remain as a unique indexed column for lookups, but routing should use opaque tokens or encrypted references that map to internal IDs. This prevents enumeration attacks and decouples URLs from database structure.

**PoC Rationale:** Using slug as PK simplifies routing for demonstration purposes (`/tenant/{tenant_slug}/dashboard/{dashboard_slug}`), but this pattern must not continue to MVP.

**TypeScript Interface:**

```typescript
interface Dashboard {
  slug: string; // ⚠️ PoC: Primary key - DO NOT use in MVP
  // MVP TODO: Add id: string (UUID) as PK, make slug a unique indexed field
  title: string;
  description?: string;
  config_json: {
    layout?: 'single' | 'grid';
    thresholds?: Record<string, number>;
    labels?: Record<string, string>;
  };
}
```

**Relationships:**
- One dashboard has many `TenantDashboard` assignments (which tenants can view it)

## 4.5 TenantDashboard

**Purpose:** Junction table assigning dashboards to specific tenants.

**Key Attributes:**
- `tenant_id`: string (UUID) - Foreign key to Tenant
- `slug`: string - Foreign key to Dashboard

**TypeScript Interface:**

```typescript
interface TenantDashboard {
  tenant_id: string; // UUID
  slug: string; // Dashboard slug
}
```

**Relationships:**
- Belongs to one Tenant
- Belongs to one Dashboard
- Composite primary key: (tenant_id, slug)

## 4.6 JWT Token Claims

**Purpose:** Defines the structure of JWTs used in token exchange and validation.

**Key Attributes:**

**User Access Token (multi-tenant):**
- `sub`: string (UUID) - User identifier
- `email`: string - User email
- `tenant_ids`: string[] - Array of tenant UUIDs the user can access
- `iat`: number - Issued at timestamp
- `exp`: number - Expiration timestamp

**Tenant-Scoped Token (single tenant):**
- `sub`: string (UUID) - User identifier
- `email`: string - User email
- `tenant_id`: string (UUID) - Single active tenant
- `role`: string - User's role for this tenant ("admin" or "viewer")
- `iat`: number - Issued at timestamp
- `exp`: number - Expiration timestamp (short-lived: 15-30 min)

**TypeScript Interfaces:**

```typescript
interface UserAccessToken {
  sub: string; // UUID
  email: string;
  tenant_ids: string[]; // Array of tenant UUIDs
  iat: number; // Unix timestamp
  exp: number; // Unix timestamp
}

interface TenantScopedToken {
  sub: string; // UUID
  email: string;
  tenant_id: string; // Single tenant UUID
  role: 'admin' | 'viewer';
  iat: number; // Unix timestamp
  exp: number; // Unix timestamp (short-lived)
}
```

**Relationships:**
- User Access Token is issued by mock auth endpoint
- Tenant-Scoped Token is issued by token exchange endpoint after validating UserTenant mapping

## 4.7 Mock Tenant Data

**Purpose:** In-memory data structures representing tenant-specific datasets for dashboard visualization.

**Key Attributes:**
- `tenant_id`: string (UUID) - Tenant this data belongs to
- `dashboard_slug`: string - Which dashboard uses this data
- `data`: object - Pandas DataFrame serialized to JSON (records format)

**TypeScript Interface:**

```typescript
interface TenantDataRecord {
  [key: string]: string | number | boolean | null; // Flexible schema per dashboard
}

interface TenantData {
  tenant_id: string; // UUID
  dashboard_slug: string;
  data: TenantDataRecord[];
}
```

**Relationships:**
- Associated with one Tenant (but not a DB foreign key; matched in-memory)
- Associated with one Dashboard (by slug)

## 4.8 PoC vs MVP Data Model Tradeoffs

**⚠️ CRITICAL SECURITY MIGRATION NOTES:**

| PoC Pattern | MVP Requirement | Security Risk if Not Changed |
|-------------|-----------------|------------------------------|
| Slug used as Dashboard PK | Add UUID `id` field as PK; slug becomes unique indexed column | Exposes database structure; enables enumeration; couples URLs to DB schema |
| Tenant slug in URLs (`/tenant/acme-corp/dashboard/...`) | Use opaque tokens, signed references, or session-based routing | Predictable URLs enable tenant enumeration; leaks business relationships |
| User IDs (UUIDs) in JWT claims exposed to client | Keep UUIDs internal; use opaque session tokens client-side | UUIDs are predictable and may leak system information |

**PoC Justification:**
These patterns simplify demonstration and reduce complexity for validating the token exchange mechanism. However, **all URL-exposed identifiers represent security risks in production** and must be replaced with non-enumerable, non-predictable references.

**MVP Implementation Guidance:**
1. Add surrogate UUID primary keys to all tables where slug is currently PK
2. Create unique indexes on slug fields for fast lookups
3. Implement URL token generation service (encrypt/sign tenant+dashboard references)
4. Update all routing to use opaque tokens instead of slugs
5. Add security tests that verify primary keys never appear in HTTP responses or URLs

---
