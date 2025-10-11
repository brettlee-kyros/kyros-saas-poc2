## Epic 0: Foundations & Infrastructure

### Story 0.1 – Create Git repos and app skeletons for Shell UI, FastAPI, Dash, IaC

**Skills Needed:** Azure DevOps engineer, JavaScript dev, Python dev  
**AC (Gherkin):**

`Scenario: Repositories and skeleton apps exist   Given I visit the org's source control   Then I should see repos "kyros-shell-ui", "kyros-api", "kyros-dash", and "kyros-iac"   And "kyros-shell-ui" builds a Next.js app locally   And "kyros-api" runs a FastAPI "hello" endpoint   And "kyros-dash" serves a basic Plotly Dash app`

**DoD:**

- Repos created with READMEs, MIT/Apache-2.0 license, CODEOWNERS.
    
- Basic app scaffolds committed; local dev instructions validated on fresh machine.
    
- Common PR template and branch protection rules enabled.
    

### Story 0.2 – CI/CD pipelines (build/test) for Shell UI, FastAPI, Dash

**Skills Needed:** Azure DevOps engineer  
**AC:**

`Scenario: PRs trigger CI   Given I open a PR in any app repo   Then CI runs install, lint, unit tests, and produces an artifact`

**DoD:**

- Azure Pipelines/GitHub Actions workflows added per repo.
    
- Cache dependencies; produce versioned artifacts (Docker images or tarballs).
    
- Status checks required before merge.
    

### Story 0.3 – IaC: AKS cluster, ACR, Key Vault, Log Analytics workspace

**Skills Needed:** Azure DevOps engineer  
**AC:**

`Scenario: Infra is provisioned by code   Given I apply the kyros-iac Terraform   Then an AKS cluster, ACR, Key Vault, and Log Analytics exist in the subscription   And outputs provide kubeconfig and resource IDs`

**DoD:**

- Terraform/Bicep modules with remote state and env vars.
    
- Private clusters/endpoints where applicable.
    
- Documentation to create dev/stage/prod workspaces.
    

### Story 0.4 – Azure AD B2C tenant & app registrations (OIDC)

**Skills Needed:** Azure DevOps engineer  
**AC:**

`Scenario: B2C app registrations created   Given I view Azure AD B2C   Then I see "kyros-shell-ui" and "kyros-api" app registrations   And user flow/policy exists for sign-in`

**DoD:**

- B2C tenant set up; test user created.
    
- Client IDs/secrets stored in Key Vault.
    
- OIDC metadata documented.
    

### Story 0.5 – Base networking & ingress (NGINX Ingress Controller + certs)

**Skills Needed:** Azure DevOps engineer  
**AC:**

`Scenario: Ingress routes apps   Given I deploy the Ingress chart   Then requests to "/api" reach kyros-api   And requests to "/dash" reach kyros-dash   And TLS certs terminate at the ingress`

**DoD:**

- NGINX Ingress installed via Helm; DNS + TLS configured.
    
- Blue/green annotations supported.
    
- Security headers baseline (HSTS, frame-ancestors) applied.
    

### Story 0.6 – Observability stack bootstrap (Grafana, Prometheus, Loki)

**Skills Needed:** Azure DevOps engineer  
**AC:**

`Scenario: Observability is reachable internally   Given the Helm values are applied   Then Grafana is accessible on a private endpoint   And Prometheus scrapes the cluster   And Loki ingests basic app logs`

**DoD:**

- Helm releases for Grafana/Prometheus/Loki in a monitoring namespace.
    
- SSO to Grafana via Azure AD.
    
- Starter dashboards imported.
    

### Story 0.7 – Security baseline: CSP, HSTS, secure headers at ingress

**Skills Needed:** Security engineer/tester, Azure DevOps engineer  
**AC:**

`Scenario: Security headers set   Given I inspect response headers   Then I see CSP with frame-ancestors   And I see HSTS`

**DoD:**

- Ingress annotations apply secure headers.
    
- Tested with OWASP ZAP.
    

### Story 0.8 – Static code analysis & secret scanning in CI

**Skills Needed:** Security engineer/tester, Azure DevOps engineer  
**AC:**

`Scenario: Secrets blocked in PR   Given I commit a .pem file   When CI runs   Then the pipeline fails with a secret scanning error`

**DoD:**

- Linters + trufflehog/gitleaks integrated in CI.
    

## Epic 1: Proof of Concept – Shell UI Embeds Dash Apps

### Story 1.1 – Shell UI scaffold & tenant/dash routes

**Skills Needed:** JavaScript dev  
**AC:**

`Scenario: Tenant dashboard route renders   Given I run kyros-shell-ui locally   When I visit "/tenant/acme-corp/dashboard/customer-ltv"   Then I see the Shell frame with placeholder content`

**DoD:**

- Next.js app with dynamic routes and basic layout.
    
- ESLint/Prettier configured; unit test scaffold.
    

### Story 1.2 – Embed static Dash app via iframe/proxy

**Skills Needed:** JavaScript dev, Azure DevOps engineer  
**AC:**

`Scenario: Dash renders inside Shell   Given kyros-dash is deployed   When Shell UI loads the dashboard route   Then Dash UI is visible in the frame and interactive`

**DoD:**

- Reverse proxy path /dash/{slug} configured.
    
- CSP updated to allow same-origin frame.
    

### Story 1.3 – Optional JWT header injection (config flag)

**Skills Needed:** Azure DevOps engineer  
**AC:**

`Scenario: Toggle JWT injection   Given a config flag "JWT_INJECTION=true"   When a dashboard request is proxied   Then the Authorization header with a hardcoded JWT is attached   And setting "JWT_INJECTION=false" removes the header`

**DoD:**

- Ingress annotation or sidecar to inject header conditionally.
    
- Config managed via Helm values/Secrets.
    

### Story 1.4 – Security review of embedding approach

**Skills Needed:** Security engineer/tester  
**AC:**

`Scenario: Embed security validated   Given I embed Dash apps via Shell UI   When I run OWASP checks   Then no cross-frame scripting is possible`

**DoD:**

- Review CSP, iframe isolation.
    
- Report filed with mitigations if needed.
    

## Epic 2: Tenant Metadata & Token Exchange

### Story 2.1 – Create tenants table

**Skills Needed:** Postgres engineer, Python dev  
**AC:**

`Scenario: Tenants exist   Given I apply the migration   Then I can insert a tenant with id, slug, and name`

**DoD:**

- Alembic migration; SQL reviewed and tested.
    
- Basic ORM model and seed script.
    

### Story 2.2 – Create tenant_datastores table (Option B) with one primary per env

**Skills Needed:** Postgres engineer  
**AC:**

`Scenario: Primary datastore enforced   Given a tenant has two datastores in "prod"   When I set one to primary   Then the other cannot also be primary`

**DoD:**

- Partial unique index on (tenant_id, env) where is_primary=true.
    
- Regex validation on uc_catalog and uc_workspace documented.
    

### Story 2.3 – Admin API for tenant CRUD

**Skills Needed:** Python dev  
**AC:**

`Scenario: Create tenant via API   Given I call "POST /admin/tenants"   Then a tenant row is created with slug and name`

**DoD:**

- FastAPI endpoints with AAD auth (admin only).
    
- OpenAPI documented; unit tests green.
    

### Story 2.4 – Admin API for datastore CRUD

**Skills Needed:** Python dev, Postgres engineer  
**AC:**

`Scenario: Create datastore mapping via API   Given I call "POST /admin/tenants/{id}/datastores"   Then a datastore row is created with env and uc_catalog`

**DoD:**

- CRUD with validation; enforces single primary per env.
    
- 4xx errors for invalid identifiers.
    

### Story 2.5 – /api/me returns user’s tenant list

**Skills Needed:** Python dev  
**AC:**

`Scenario: User sees tenant list   Given I am authenticated   When I call "/api/me"   Then I see an array of tenants I can access`

**DoD:**

- Endpoint implemented; mocked directory mapping for MVP (or static).
    

### Story 2.6 – Token exchange endpoint returns tenant-scoped JWT

**Skills Needed:** Python dev, Azure DevOps engineer  
**AC:**

`Scenario: Tenant token minted   Given I select a tenant   When I call "/api/token/exchange" with that tenant_id   Then a short-lived JWT is returned   And it includes tenant_id, env, and uc_catalog`

**DoD:**

- JWT signing key in Key Vault.
    
- TTL 15–30 minutes; RS256 signing; unit tests for claims.
    

### Story 2.7 – Shell UI tenant switcher integrates with exchange

**Skills Needed:** JavaScript dev  
**AC:**

`Scenario: Switch tenant updates token   Given I open the tenant chooser   When I select a different tenant   Then Shell UI fetches a new token   And embeds Dash with the new header`

**DoD:**

- UX implemented; loading/error states covered.
    
- No tokens in localStorage or URLs.
    

### Story 2.8 – JWT validation (signature, expiry, audience)

**Skills Needed:** Security engineer/tester, Python dev  
**AC:**

`Scenario: Expired token rejected   Given I present an expired JWT   When I call an API   Then I receive 401 Unauthorized`

**DoD:**

- JWTs validated on every request.
    
- Tests for expired, invalid, wrong audience.
    

### Story 2.9 – Tenant escalation prevention tests

**Skills Needed:** Security engineer/tester  
**AC:**

`Scenario: Cross-tenant access blocked   Given I mint a token for tenant A   When I attempt to call tenant B’s dashboard   Then I get 403 Forbidden`

**DoD:**

- Integration tests simulate cross-tenant misuse.
    

## Epic 3: Tenant-aware Dash Apps

### Story 3.1 – Dash middleware parses Authorization header

**Skills Needed:** Python dev  
**AC:**

`Scenario: Claims available to callbacks   Given a request includes an Authorization header   When Dash handles the request   Then tenant_id and uc_catalog are available in the request context`

**DoD:**

- Middleware validates token and exposes claims to callbacks.
    
- Errors result in 401 with correlation id.
    

### Story 3.2 – Safe SQL builder for identifiers + parameterized values

**Skills Needed:** Python dev  
**AC:**

`Scenario: Invalid identifier rejected   Given I provide an identifier with spaces   When SQL is built   Then the system raises a 400 error`

**DoD:**

- Regex whitelist on identifiers; parameterized values.
    
- Unit tests for positive/negative cases.
    

### Story 3.3 – Replace hardcoded catalog with uc_catalog in queries

**Skills Needed:** Python dev  
**AC:**

`Scenario: Catalog comes from token   Given I open a dashboard   Then the executed SQL uses the uc_catalog from the token claim`

**DoD:**

- Visual confirmation with two tenants hitting different catalogs.
    
- Integration tests for catalog resolution.
    

### Story 3.4 – Preferences table and API

**Skills Needed:** Python dev, Postgres engineer  
**AC:**

`Scenario: Save and load preferences   Given I set dashboard filters   When I save preferences   Then they persist per (tenant_id, user_id)   And load on next visit`

**DoD:**

- Table: preferences(tenant_id, user_id, prefs JSONB).
    
- Endpoints: GET/POST; input validation; unit tests.
    

### Story 3.5 – SQL builder injection test suite

**Skills Needed:** Security engineer/tester, Python dev  
**AC:**

`Scenario: Injection attempt blocked   Given I pass "acme; DROP TABLE" as identifier   Then SQL builder rejects with 400`

**DoD:**

- Negative tests for SQL injection.
    
- Fuzzing harness included in CI.
    

### Story 3.6 – Token claim validation inside Dash middleware

**Skills Needed:** Security engineer/tester, Python dev  
**AC:**

`Scenario: Mismatched tenant_id claim rejected   Given a token contains a tenant_id not in DB   Then Dash rejects the request`

**DoD:**

- Middleware validates token claims against DB metadata.
    

## Epic 4: Observability

### Story 4.1 – FastAPI Prometheus metrics middleware

**Skills Needed:** Python dev  
**AC:**

`Scenario: Metrics available   Given I call "/metrics"   Then I see http_requests_total and http_request_duration_seconds   And labels include tenant_id and service`

**DoD:**

- Middleware wired; whitelist metrics route from auth.
    
- Basic SLO panels in Grafana.
    

### Story 4.2 – Dash callback metrics decorator

**Skills Needed:** Python dev  
**AC:**

`Scenario: Callback metrics emitted   Given a Dash callback runs   Then a metric is recorded for duration and error count   And labels include tenant_id and app_slug`

**DoD:**

- Decorator applied to key callbacks.
    
- Grafana panel shows error rates per app_slug.
    

### Story 4.3 – Structured JSON logs and Promtail pipeline

**Skills Needed:** Azure DevOps engineer, Python dev  
**AC:**

`Scenario: Logs visible in Loki   Given services emit JSON logs   When Promtail ships logs to Loki   Then I can query by {service} and filter for "tenant_id"`

**DoD:**

- Common log format fields: ts, level, service, route, status, latency_ms, sub, email, tenant_id.
    
- Loki retention set to 7–14 days; dashboards link to logs.
    

### Story 4.4 – Audit logs table and write hooks

**Skills Needed:** Python dev, Postgres engineer  
**AC:**

`Scenario: Audit row on dashboard view   Given I open a dashboard   Then an audit_logs row is inserted with action "view_dashboard" and my tenant_id`

**DoD:**

- DDL with indices; append-only enforcement.
    
- Hooks for token exchange, view, metadata change.
    

### Story 4.5 – PII redaction in logs

**Skills Needed:** Security engineer/tester, Python dev  
**AC:**

`Scenario: PII not logged   Given I trigger an error with email content   Then logs redact sensitive info`

**DoD:**

- Logger config with redaction filters.
    

### Story 4.6 – Alerts on suspicious audit events

**Skills Needed:** Security engineer/tester, Azure DevOps engineer  
**AC:**

`Scenario: Alert on failed logins   Given >10 failed logins in 5 minutes   Then an alert fires to the ops channel`

**DoD:**

- Prometheus/Loki alert rules configured.
    

## Epic 5: Hardening & Production Rollout

### Story 5.1 – Blue/green deployment pipeline and canary routing

**Skills Needed:** Azure DevOps engineer  
**AC:**

`Scenario: Canary tenant on new flow   Given legacy tenants are unaffected   When I enable the canary routing for "Acme Corp"   Then Acme uses Shell UI + JWT flow   And other tenants remain on legacy`

**DoD:**

- Pipelines switch traffic per tenant/host header.
    
- Rollback documented and tested.
    

### Story 5.2 – Security validation for identifier injection & auth leaks

**Skills Needed:** Python dev, Azure DevOps engineer  
**AC:**

`Scenario: Identifier injection blocked   Given I attempt to pass "acme; DROP TABLE tenants" as a catalog   When the system validates identifiers   Then the request is rejected with 400 and is logged`

**DoD:**

- Negative tests for SQL builder; ZAP/OWASP scan baseline.
    
- No secrets/tokens in logs; CSP/HSTS headers verified.
    

### Story 5.3 – Penetration test before production

**Skills Needed:** Security engineer/tester  
**AC:**

`Scenario: Pen test executed   Given staging environment is live   When security engineer runs pen test suite   Then findings are documented and prioritized`

**DoD:**

- External pen test report complete; P1/P2 issues remediated.
    

### Story 5.4 – Blue/green rollout security validation checklist

**Skills Needed:** Security engineer/tester, Azure DevOps engineer  
**AC:**

`Scenario: Rollout validated   Given blue/green switch is planned   When pre-flight checklist is run   Then all security checks pass before routing users`

**DoD:**

- Checklist documented; signed off before cutover.
    

# Roles & Capacity

- **Azure DevOps engineer:** AKS, Ingress, IaC, CI/CD, Observability.
    
- **JavaScript dev:** Next.js Shell UI, tenant switcher, embedding.
    
- **Python dev:** FastAPI, Dash, SQL builder, preferences, metrics, audit logging.
    
- **Postgres engineer:** schema, migrations, indices.
    
- **Security engineer/tester:** JWT validation, secure headers, injection testing, pen testing, CI security gates.