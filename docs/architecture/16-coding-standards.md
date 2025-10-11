# 16. Coding Standards

## 16.1 Critical Fullstack Rules

- **Type Sharing:** Always define shared types in `packages/shared-config` (Python) and import from there. Never duplicate type definitions.
- **JWT Configuration:** ALL JWT settings (secret, algorithm, expiry) MUST be imported from shared-config module. Never hardcode these values.
- **Tenant Context from JWT Only:** Never accept tenant_id as a request parameter. Always extract from validated JWT claims via `request.state.tenant_id`.
- **Token Storage:** Frontend must store tokens in HTTP-only cookies (set by API routes). Never use localStorage or sessionStorage for tokens.
- **Error Handling:** All API routes must use standard error response format (see Section 17). Include request_id for correlation.
- **No Primary Keys in URLs:** Never expose database primary keys (UUIDs or integers) in URLs or API responses without opaque token layer (documented as PoC tradeoff).

## 16.2 Naming Conventions

| Element | Frontend | Backend | Example |
|---------|----------|---------|---------|
| **Components** | PascalCase | - | `TenantSelector.tsx` |
| **Hooks** | camelCase with 'use' | - | `useAuth.ts`, `useTenantContext.ts` |
| **API Routes** | - | kebab-case | `/api/token-exchange`, `/api/tenant/{id}` |
| **Database Tables** | - | snake_case | `user_tenants`, `tenant_dashboards` |
| **TypeScript Interfaces** | PascalCase | - | `UserAccessToken`, `TenantScopedToken` |
| **Python Classes** | PascalCase | PascalCase | `JWTService`, `DataAccessLayer` |
| **Functions/Methods** | camelCase | snake_case | TS: `handleSelectTenant`, Python: `validate_user_token` |

---
