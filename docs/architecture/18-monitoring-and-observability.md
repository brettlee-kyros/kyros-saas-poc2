# 18. Monitoring and Observability

## 18.1 Monitoring Stack

- **Frontend Monitoring:** Console logging only (PoC); MVP should add Sentry or similar
- **Backend Monitoring:** Stdout JSON logging; MVP should add Prometheus metrics
- **Error Tracking:** None (PoC); MVP should add error tracking service
- **Performance Monitoring:** None (PoC); MVP should add APM tool

## 18.2 Key Metrics

**Frontend Metrics (MVP):**
- Page load time
- API response time (from client perspective)
- JavaScript errors
- User interactions (tenant selection, dashboard loads)

**Backend Metrics (MVP):**
- Request rate per endpoint
- P50/P95/P99 latency
- Error rate by status code
- Token exchange success/failure rate
- Database query latency

## 18.3 Logging Strategy (PoC)

**Frontend:** Console logs with structured format
**Backend:** JSON logging to stdout with tenant context

---
