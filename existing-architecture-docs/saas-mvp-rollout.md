## Guiding Principles

1. **Minimal downtime for existing Plotly apps** – Dash apps continue functioning while we add Shell UI, tenant isolation, and observability features.
    
2. **Visual POC first** – Deliver a working Shell UI embedding Dash apps with optional/hardcoded JWT handling before building out the full token exchange, metadata DB, and tenant scoping.
    
3. **Incremental layering** – Start with a simple integration, add tenant isolation, then expand to observability and admin features.
    
4. **Infrastructure-as-Code** – Azure resources (AKS, Postgres, Key Vault, networking) provisioned via Bicep.
    
5. **Team sizing** – Assume 40h/week engineers, but only 65% is true coding. Timelines below reflect this.
    

## Potential Epics and User Stories

See: [Potential Epics and Stories](epics-stories)

## Phase 1: Proof of Concept (3–4 weeks)

**Goal:** Demonstrate Shell UI embedding Plotly Dash apps, with optional JWT header injection (hardcoded or disabled by config).

### Tasks

- **Shell UI (Next.js)**: Base app scaffold, minimal nav, embed Plotly Dash app, optional JWT injection.
    
- **Ingress / Proxy Setup**: NGINX Ingress mapping, optional JWT header injection.
    
- **DevOps / Infra**: Isolated Azure environment for POC, Terraform modules for AKS/Ingress/Postgres (empty).
    

**Skills Needed**

- 1x JavaScript/React engineer
    
- 1x Azure DevOps engineer
    
- 1x Python engineer
    
- 1x Security Engineer/Tester
    

**Acceptance Criteria (Gherkin)**

`Feature: Shell UI embeds Dash apps   Scenario: User accesses dashboard without JWT     Given I log in to the Shell UI     When I navigate to "/tenant/acme-corp/dashboard/customer-ltv"     Then I should see the Dash app render inside the Shell frame     And the Dash app should load without tenant scoping    Scenario: User accesses dashboard with optional JWT     Given I log in to the Shell UI     When I navigate to a dashboard that has JWT injection enabled     Then the request to the Dash service should include an Authorization header     And the Dash app should parse the JWT if provided`

## Phase 2: Tenant Metadata & Token Exchange (4–6 weeks)

**Goal:** Replace optional JWT with real tenant-scoped token exchange. Introduce tenant metadata DB (Option B with tenant_datastores).

### Tasks

- Alembic migration for tenants + tenant_datastores.
    
- FastAPI: /api/me, /api/token/exchange, tenant-scoped JWT.
    
- Shell UI: tenant switcher, token exchange call.
    

**Skills Needed**

- 1x Python engineer
    
- 1x JavaScript/React engineer
    
- 1x Postgres engineer
    
- 1x Security Engineer/Tester
    

**Acceptance Criteria (Gherkin)**

`Feature: Tenant-scoped tokens   Scenario: Multi-tenant user selects tenant     Given I log in as a user with access to 2 tenants     When I select "Acme Corp" in the tenant switcher     Then a tenant-scoped JWT should be minted     And it should contain tenant_id and uc_catalog     And the Dash embed should include this token in the header`

## Phase 3: Tenant-aware Dash Apps (4-5 weeks)

**Goal:** Dash apps read tenant-scoped tokens, resolve Unity Catalog, and build tenant-specific SQL queries.

### Tasks

- Dash runtime: middleware to parse Authorization header.
    
- Safe SQL builder: regex validation for identifiers, parameterized values.
    
- Preferences API: save tenant/user filters.
    

**Skills Needed**

- 2x Python engineers
    
- 1x Security Engineer/Tester
    

**Acceptance Criteria (Gherkin)**

`Feature: Dash apps scoped by tenant   Scenario: Tenant A user queries dashboard     Given I log in and select tenant "Acme Corp"     When I open the "Customer LTV" dashboard     Then the Dash app should query using catalog "kyros_acme_prod"     And I should not see data from other tenants    Scenario: Tenant B user queries dashboard     Given I log in and select tenant "Global Retail"     When I open the "Customer LTV" dashboard     Then the Dash app should query using catalog "kyros_retail_prod"     And results should differ from Acme Corp`

## Phase 4: Observability (3 weeks)

**Goal:** Implement metrics, structured logging, and audit trails.

### Tasks

- Metrics: Prometheus middleware in FastAPI, decorators for Dash callbacks, Grafana dashboards.
    
- Logs: JSON logs with tenant_id, sub, email; Promtail → Loki.
    
- Audit: Postgres audit_logs with key actions.
    

**Skills Needed**

- 1x Python engineer
    
- 1x Azure DevOps engineer
    
- 1x Security Engineer/Tester
    

**Acceptance Criteria (Gherkin)**

`Feature: Per-tenant observability   Scenario: Tenant access logs     Given I access a dashboard as tenant "Acme Corp"     Then a JSON log entry should exist with tenant_id, sub, and email    Scenario: Audit logs     Given I view a dashboard     Then a row should be inserted into audit_logs with action "view_dashboard" and my tenant_id    Scenario: Metrics     Given Dash callback execution     Then a Prometheus metric should be emitted with labels {tenant_id, app_slug, callback}`

## Phase 5: Hardening & Production Rollout (3–4 weeks)

**Goal:** Stabilize, test, and promote MVP to production with minimal downtime.

### Tasks

- Blue/green rollout of Shell UI and Ingress changes.
    
- Canary tenant migration to new metadata DB + JWT flow.
    
- Security testing for SQL injection and auth leaks.
    
- Runbooks + alerts live.
    

**Skills Needed**

- 1x Azure DevOps engineer
    
- 1x Python engineer
    
- 1x Security Engineer/Tester
    

**Acceptance Criteria (Gherkin)**

`Feature: Production readiness   Scenario: Rollout without downtime     Given existing tenants use legacy Dash apps     When I enable Shell UI embedding for a canary tenant     Then legacy tenants should remain unaffected     And the canary tenant should see tenant-scoped dashboards`

## Overall Timeline

- **Original estimate (100% coding time):** ~12–15 weeks
    
- **Adjusted for 65% coding time:** ~18–22 weeks
    

## Summary by Role

- 1x Azure DevOps engineer – AKS, ingress, Bicep, monitoring stack.
    
- 2x Python engineers – FastAPI monolith, Dash runtime, SQL builder, observability, audit logs.
    
- 1x JavaScript/React engineer – Shell UI, tenant switcher, embedding.
    
- 1x Postgres engineer – schema migrations, queries.
    
- 1x Security Engineer/Tester
    
- Optional 0.5x UX/UI designer – tenant switcher, Shell UI branding.