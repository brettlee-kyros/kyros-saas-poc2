# 9. Frontend Architecture

This section defines Next.js Shell UI implementation patterns, component organization, state management, and routing structure.

## 9.1 Component Architecture

### Component Organization

```
apps/shell-ui/src/
├── app/                          # Next.js 14 App Router
│   ├── layout.tsx                # Root layout with providers
│   ├── page.tsx                  # Home (tenant selector or redirect)
│   ├── login/
│   │   └── page.tsx              # Mock login page
│   ├── tenant/
│   │   └── [tenant_slug]/
│   │       ├── page.tsx          # Dashboard listing
│   │       └── dashboard/
│   │           └── [dashboard_slug]/
│   │               └── page.tsx  # Dashboard embed view
│   └── api/
│       └── proxy/
│           └── dash/
│               └── [...path]/
│                   └── route.ts  # Reverse proxy API route
├── components/
│   ├── auth/
│   │   ├── LoginForm.tsx         # Mock login form
│   │   └── AuthGuard.tsx         # Protected route wrapper
│   ├── tenant/
│   │   ├── TenantSelector.tsx    # Tenant chooser component
│   │   └── TenantSwitcher.tsx    # Header tenant switch dropdown
│   ├── dashboard/
│   │   ├── DashboardCard.tsx     # Dashboard tile in listing
│   │   ├── DashboardEmbed.tsx    # Iframe/embed container
│   │   └── DashboardLoading.tsx  # Loading skeleton
│   ├── layout/
│   │   ├── Header.tsx            # App header with nav
│   │   ├── Footer.tsx            # App footer
│   │   └── ErrorBoundary.tsx     # Error boundary wrapper
│   └── ui/                       # Shared UI primitives (Headless UI wrappers)
│       ├── Button.tsx
│       ├── Card.tsx
│       └── Modal.tsx
├── hooks/
│   ├── useAuth.ts                # Auth state and login/logout
│   ├── useTenantContext.ts       # Active tenant state
│   ├── useTokenRefresh.ts        # Auto-refresh tenant token
│   └── useApi.ts                 # API client hook
├── lib/
│   ├── api-client.ts             # Fetch wrapper with auth
│   ├── token-storage.ts          # Token cookie helpers
│   └── types.ts                  # Shared TypeScript types
└── store/
    └── tenant-store.ts           # Zustand store for tenant context
```

## 9.2 State Management Architecture

### State Structure

**Tenant Context (Zustand):** Persisted in localStorage; survives page refresh

**Auth State (React Context):** In-memory only; checked on app mount via `/api/me`

---
