# Appendix: PoC vs MVP Migration Checklist

## Security Migration (CRITICAL)

- [ ] Replace mock auth with Azure AD B2C OIDC flow
- [ ] Replace pre-generated JWTs with cryptographic signing
- [ ] Add opaque token layer for all URL identifiers
- [ ] Remove tenant slugs from URLs; implement session-based or signed routing
- [ ] Add HTTPS everywhere with HSTS headers
- [ ] Implement rate limiting and WAF
- [ ] Add Row-Level Security (RLS) to PostgreSQL

## Infrastructure Migration

- [ ] Migrate SQLite to Azure Database for PostgreSQL
- [ ] Migrate in-memory Pandas to Azure Storage/Databricks queries
- [ ] Separate FastAPI monolith into auth service + data service
- [ ] Add Redis for distributed caching
- [ ] Implement Prometheus + Grafana + Loki observability stack
- [ ] Set up CI/CD pipelines (GitHub Actions or Azure DevOps)

## Architecture Enhancements

- [ ] Add audit_logs table for compliance tracking
- [ ] Implement token refresh mechanism
- [ ] Add pagination to all list endpoints
- [ ] Create admin API with mTLS authentication
- [ ] Implement proper error pages (401, 403, 404)
- [ ] Add preferences table for saved filters/layouts

## Testing & Quality

- [ ] Expand E2E test coverage to all critical paths
- [ ] Add integration tests for Azure services
- [ ] Implement contract tests for API endpoints
- [ ] Add security penetration testing
- [ ] Performance load testing with realistic data volumes

---

**End of Architecture Document**
