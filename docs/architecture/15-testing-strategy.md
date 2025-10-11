# 15. Testing Strategy

## 15.1 Testing Pyramid

```
        E2E Tests (5%)
       /              \
    Integration Tests (15%)
   /                      \
Frontend Unit (40%)  Backend Unit (40%)
```

## 15.2 Test Organization

**Frontend Tests:**
```
apps/shell-ui/tests/
├── components/
│   ├── TenantSelector.test.tsx
│   └── DashboardEmbed.test.tsx
├── hooks/
│   ├── useAuth.test.ts
│   └── useTenantContext.test.ts
└── lib/
    └── api-client.test.ts
```

**Backend Tests:**
```
apps/api/tests/
├── test_auth.py                # Mock auth endpoints
├── test_token_exchange.py      # Token exchange validation
├── test_tenant_isolation.py    # Cross-tenant security tests
└── test_data_access.py         # DAL and data filtering
```

**E2E Tests:**
```
tests/e2e/
├── auth-and-tenant-selection.spec.ts
├── dashboard-embed-and-isolation.spec.ts
└── token-expiry-and-refresh.spec.ts
```

---
