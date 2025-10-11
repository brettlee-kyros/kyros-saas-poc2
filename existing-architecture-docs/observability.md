## **Purpose**

The purpose of Observability in the Kyros Plotly SaaS platform is to ensure that system behavior, performance, and user interactions can be continuously monitored, audited, and improved. Since the platform is multi-tenant and handles sensitive financial and actuarial data, observability must serve three key goals:

1. **Operational Monitoring** – Provide real-time insight into the health of FastAPI services, Plotly Dash applications, and supporting infrastructure. Metrics must capture tenant-specific activity to enable proactive detection of performance bottlenecks or anomalies.
    
2. **Security & Compliance** – Guarantee accountability through structured logs and auditable trails. Every action that touches tenant data must be attributable to a specific user (sub and email) and a specific tenant (tenant_id). This is critical for compliance, incident response, and client trust.
    
3. **Product Insights** – Allow the engineering and actuary teams to analyze how tenants use dashboards and features. This feedback loop supports iterative improvements, helps prioritize feature development, and ensures that system resources align with actual usage patterns.
    

By combining **Prometheus/Grafana for metrics**, **Loki for logs**, and **Postgres audit trails**, the observability layer creates a comprehensive view of the system, balancing **operational excellence**, **security posture**, and **business intelligence**.

## **Scope**

Unified metrics, logs, and audit trails for Kyros SaaS (Shell UI, FastAPI monolith, Dash apps, ingress).

- **Metrics:** Prometheus → Grafana, with tenant_id labels.
    
- **Logs:** Loki with structured JSON, including sub, email, tenant_id.
    
- **Audit trails:** Postgres audit_logs table for dashboard access and metadata changes.
    

## **Objectives**

1. Detect user‑facing issues fast (per service and per tenant).
    
2. Trace dashboard usage and admin changes for compliance.
    
3. Keep noise, cost, and PII risk under control.
    

## **Metrics (Prometheus → Grafana)**

### **Required metrics**

Instrument FastAPI and Dash to expose /metrics with:

- Request rate:
    
    - http_requests_total{service,endpoint,method,code,tenant_id}
        
- Latency:
    
    - http_request_duration_seconds_bucket{service,endpoint,method,tenant_id}
        
- Response size:
    
    - http_response_size_bytes_sum{service,endpoint,tenant_id}
        
- Dash callbacks:
    
    - dash_callback_duration_seconds_bucket{app_slug,callback,tenant_id}
        
    - dash_callback_errors_total{app_slug,callback,tenant_id}
        

Platform exporters:

- Ingress Controller, kube‑state‑metrics?, node/cAdvisor, Postgres exporter.
    

Label policy:

- Always label by service, endpoint (route name), and tenant_id.
    
- Avoid high‑cardinality labels (do not label by sub or email).
    

### **SLOs**

- Monolith availability: 99.9% (probe /healthz).
    
- P95 latency:
    
    - Public GET endpoints _TBD_
        
    - Dash data endpoints _TBD_.
        
- 5xx error ratio _TBD_ per service.
    

### **Example alert rules (Prometheus/Alertmanager)**

- High error ratio:
    

`sum(rate(http_requests_total{code=~"5.."}[10m]))  / sum(rate(http_requests_total[10m])) > 0.02 for: 10m labels: {severity="page"}`

- P95 latency breach:
    

`histogram_quantile(   0.95,    sum by (le, service) (rate(http_request_duration_seconds_bucket[5m])) ) > 0.7 for: 15m labels: {severity="page"}`

- DB pressure: connections > 80% of max for 10m (postgres_exporter).
    

### **Grafana dashboards (minimum)**

- **SaaS Overview:** RPS, 5xx ratio, P50/P95 latency (tenant filter).
    
- **Tenant Drill‑Down:** per‑tenant request rate, errors, top slow endpoints.
    
- **Dash Apps Health:** callback duration/errs per app_slug and tenant.
    
- **Platform & DB:** ingress saturation, pod restarts, Postgres connections/locks.
    

## **Logs (Loki with structured JSON)**

### **Log schema (application)**

All app logs must be **structured JSON**. Required fields:

- Core: ts, level, service, route, method, status, latency_ms, bytes
    
- Identity: sub, email, tenant_id
    
    - Note: email is PII—log only what you need. If possible, store email_hash and email_domain instead of full email. If you must log email, limit to access logs and redact in error logs.
        
- Context: dashboard_slug?, trace_id?, span_id?, env
    

Example access log:

`{   "ts":"2025-08-16T15:22:10Z",   "level":"info",   "service":"kyros-api",   "route":"/api/dashboards/{slug}/data",   "method":"GET",   "status":200,   "latency_ms":142,   "bytes":32768,   "sub":"f8d1…",   "email":"analyst@client.com",   "tenant_id":"8e1b3d5b-…",   "dashboard_slug":"customer-lifetime-value",   "trace_id":"6a5e…",   "env":"prod" }`

### **What to log**

- Access logs for every request (info).
    
- Business events: login, token exchange, tenant switch, preferences saved (info).
    
- Errors: stack traces plus context (error).
    
- Security events: auth failures, forbidden access, rate limit (warn/error).
    

### **What not  to log**

- Tokens, cookies, raw request bodies with sensitive content.
    
- Full datasets or query results.
    
- If keeping email, never log in debug payloads or stack traces.
    

### **Ingestion**

- Promtail/Fluent Bit daemonset scrapes container stdout/stderr.
    
- Keep Loki **labels** minimal (service, namespace, container, level) to avoid cardinality explosions; retain sub, email, tenant_id inside JSON fields.
    

Retention (initial):

- Loki logs: 7–14 days (Blob storage backend). _TBD_
    
- Error/critical logs can be mirrored to longer‑term storage if needed.
    

## **Audit Trails (Postgres audit_logs)**

### **Purpose**

Authoritative record of user actions and metadata changes for compliance and investigations.

### **Table**

audit_logs (append‑only). Refer to [DB Model](https://kyros.atlassian.net/wiki/spaces/PSD/pages/71434299/Tenant+Metadata+DB#audit_logs).

### **Access & retention**

- Application writes only; no direct DML by users.
    
- Retain per policy (e.g., 365 days+).
    
- Provide read‑only reporting views for analysts.
    

## **Correlation (metrics ↔ logs ↔ traces)**

- Generate a trace_id for each request (OpenTelemetry or custom).
    
- Include trace_id in access logs and propagate as a metric **exemplar** (optional).
    
- Grafana panel links should jump from a red time series to matching Loki logs filtered by trace_id and tenant_id.
    

## **Security & Privacy**

- Transport: TLS for Prometheus/Grafana/Loki; restrict endpoints to private networks; SSO Grafana via Azure AD.
    
- Secrets: access via Azure Key Vault; use managed identities where possible.
    
- PII hygiene:
    
    - Limit email usage to what’s necessary; prefer email_domain and email_hash.
        
    - Never log tokens; add automated redaction/linting in CI.
        
- Multi‑tenant:
    
    - Always include tenant_id in access logs and metrics labels.
        
    - Avoid sub/email as metric labels (logs only).
        

## **Runbooks (initial)**

- **5xx spike:**
    
    Check Grafana Overview → filter by tenant_id → open Loki logs with trace_id → verify last deploy → rollback or hotfix.
    
- **High latency P95:**
    
    Compare ingress vs app vs DB panels → check cache hit rate → profile slow endpoints/callbacks → inspect DB slow query log.
    
- **Tenant complaint (“my dashboard is blank/slow”):**
    
    Use Tenant Drill‑Down dashboard with that tenant_id → open Dash Apps Health → correlate errors → inspect audit entries for recent metadata changes.
    

## **Acceptance (DoD)**

- Prometheus scraping app and platform metrics; panels show per‑tenant information.
    
- Loki receiving structured JSON logs; sample queries by tenant_id return results.
    
- audit_logs table populated for token exchange, dashboard view, preferences, and admin changes.
    
- Two paging alerts live (5xx ratio, latency P95) and routing to the team channel.
    
- No tokens/PII leakage verified via redaction tests.
    

## **Implementation checklist**

- Add metrics middleware to FastAPI and Dash callback decorators (with tenant_id label).
    
- Emit JSON logs with required fields; configure Promtail to ship to Loki.
    
- Create audit_logs DDL, indices, and write hooks in the monolith.
    
- Provision Prometheus, Loki, Grafana; import starter dashboards and alerts.
    
- Add SSO to Grafana (Azure AD) and restrict endpoints to private networks.
    
- Document runbooks and on‑call notifications.