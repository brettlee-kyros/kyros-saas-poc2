# 14. Security and Performance

## 14.1 Security Requirements

**Frontend Security:**
- **CSP Headers:** `Content-Security-Policy: default-src 'self'; frame-ancestors 'self'`
- **XSS Prevention:** React's built-in escaping; no `dangerouslySetInnerHTML`
- **Secure Storage:** Tokens in HTTP-only cookies; never in localStorage

**Backend Security:**
- **Input Validation:** Pydantic models validate all request bodies
- **Rate Limiting:** None (PoC); MVP should add rate limiting middleware
- **CORS Policy:** Restrict to Shell UI origin (`http://localhost:3000`)

**Authentication Security:**
- **Token Storage:** HTTP-only cookies (tenant-scoped tokens)
- **Session Management:** Short-lived tokens (30 min); automatic refresh
- **Password Policy:** N/A (mock auth); MVP will use Azure AD B2C

**⚠️ PoC Security Tradeoffs:**
- Mock authentication with pre-generated JWTs (INSECURE for production)
- Slugs exposed in URLs (enables enumeration; MVP must use opaque tokens)
- No HTTPS (local only; MVP requires HTTPS everywhere)
- No rate limiting or WAF (MVP must add)

## 14.2 Performance Optimization

**Frontend Performance:**
- **Bundle Size Target:** <300KB initial JS bundle
- **Loading Strategy:** React Server Components for initial loads; lazy load dashboard embed
- **Caching Strategy:** Service layer caches tenant metadata for 60 seconds

**Backend Performance:**
- **Response Time Target:** P95 <500ms for metadata endpoints; <2s for data endpoints
- **Database Optimization:** Indexes on (tenant_id, slug) lookups
- **Caching Strategy:** In-memory DataFrame cache per (tenant_id, dashboard_slug)

---
