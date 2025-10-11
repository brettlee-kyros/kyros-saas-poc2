# Brainstorming Session Results

**Session Date:** 2025-10-05
**Facilitator:** Business Analyst Mary 📊
**Participant:** Project Lead

---

## Executive Summary

**Topic:** Kyros Multi-Tenant SaaS PoC - Architecture Validation Through Shell UI, JWT Token Exchange, and Plotly App Embedding

**Session Goals:** Validate the proposed multi-tenant architecture by implementing core mechanisms: shell-ui application with mocked authentication, JWT creation and token exchange for tenant isolation, tenant selection UI, and secure embedding of Plotly applications with tenant-scoped data access.

**Techniques Used:**
1. Morphological Analysis (15 min) - Mapped implementation options for core architectural components
2. Five Whys (15 min) - Identified root causes of potential implementation risks
3. SCAMPER Method (20 min) - Generated solutions for mocking strategy and scope decisions
4. Question Storming (15 min) - Created comprehensive validation framework

**Total Ideas Generated:** 47 distinct ideas, decisions, and validation questions

**Key Themes Identified:**
- **Architectural Fidelity with Pragmatic Mocking** - Stay true to production architecture while mocking external dependencies (auth, data sources, observability)
- **Configuration Consistency as Critical Risk** - Shared configuration module needed across FastAPI and Dash apps for JWT validation
- **PoC vs. MVP Tradeoff Documentation** - Clear documentation of simplifications made for PoC that must be separated in MVP
- **Validation Through Visibility** - Debug panel showing JWT claims provides critical demonstration of token exchange mechanism
- **Automated Setup Reduces Error** - Seed scripts and setup validation essential even without admin tooling in scope

---

## Technique Sessions

### Morphological Analysis - 15 minutes

**Description:** Systematically mapped the key architectural components of the PoC and explored implementation options for each parameter.

**Ideas Generated:**

1. **Mock Authentication Decision** - Selected simple in-memory store (Python dict/class) to simulate user lookup rather than full mock OIDC server or hardcoded config
2. **JWT Generation Decision** - Selected pre-generated tokens stored as constants to focus validation on exchange flow rather than cryptography
3. **Tenant Switcher UI Decision** - Selected dedicated tenant selection page to force explicit choice and clearly demonstrate token exchange trigger
4. **Plotly App Embedding Decision** - Selected reverse proxy with header injection as most production-like approach demonstrating token passing and isolation
5. **JWT Structure Definition** - Defined user access token with `tenant_ids` array and tenant-scoped token with single `tenant_id`
6. **Token Storage Strategy** - Identified options for frontend token storage (memory, HTTP-only cookies, SessionStorage)
7. **Token Passing Mechanism** - Confirmed Authorization header as preferred method over query params or custom headers
8. **In-Memory Data Source Options** - Explored Pandas DataFrame, Dict, and SQLite in-memory as data source implementations

**Insights Discovered:**
- The choice of pre-generated JWTs allows faster iteration on the exchange mechanism without cryptographic complexity
- Reverse proxy header injection is architecturally correct and validates the production approach
- Dedicated tenant selection page creates a clear demonstration point for stakeholders
- The in-memory store for mock auth provides flexibility to test different user/tenant mapping scenarios

**Notable Connections:**
- All four core parameters (auth, JWT, tenant switcher, embedding) align to validate the same architectural principle: hard tenant isolation through JWT claims
- The decisions balance PoC speed with architectural realism

---

### Five Whys - 15 minutes

**Description:** Deep dive into potential implementation risks and blockers using iterative "why" questioning to uncover root causes.

**Ideas Generated:**

#### Challenge 1: JWT Token Passing to Dash Apps
9. **Challenge Statement** - Embedded Plotly Dash app might not properly receive or validate tenant-scoped JWT from reverse proxy
10. **Why 1** - Header was corrupted or request failed
11. **Why 2** - Network issues (handled by retry) OR configuration/encoding errors
12. **Why 3** - Encoding problems, middleware interference persist
13. **Why 4** - Character encoding mismatches, middleware order issues, header size limits, conflicting security middleware
14. **Why 5 (Root Cause)** - Misconfigured test environments, inadequate integration tests, missing validation logging

#### Challenge 2: Token Exchange Scoping
15. **Challenge Statement** - Token exchange might not correctly scope JWT to single tenant after selection
16. **Why 1** - Data issues in tenant metadata DB
17. **Why 2** - Tenant metadata DB misconfigured
18. **Why 3** - Manual setup errors
19. **Why 4** - Lack of setup scripts, unclear documentation, no validation checks, complex manual steps
20. **Why 5 (Root Cause)** - No automated seed scripts, difficult to reset test state, hard to verify tenant mappings, requires manual SQL

#### Challenge 3: Tenant Data Filtering
21. **Challenge Statement** - In-memory data source might not correctly filter data by tenant
22. **Why 1** - JWT not validated correctly in Dash app
23. **Why 2** - Wrong secret key, signature validation issues, expired tokens not handled, missing libraries
24. **Why 3** - Configuration mismatch between Shell UI/FastAPI and Dash apps
25. **Why 4** - Separate config files, no shared config management, environment variables not propagated, hardcoded values
26. **Why 5 (Root Cause)** - No shared config module to ensure consistency

**Insights Discovered:**
- Robust validation and logging at each handoff point critical to catch token passing issues early
- Even without admin tooling in scope, automated seed scripts are essential for PoC reliability
- Shared configuration module is non-negotiable for JWT validation consistency across services
- Integration testing must cover the full flow: tenant selection → token exchange → header injection → Dash validation

**Notable Connections:**
- All three challenges share a common theme: configuration consistency and validation across service boundaries
- The root causes point to specific technical requirements: shared config module, seed scripts, integration tests, validation logging

---

### SCAMPER Method - 20 minutes

**Description:** Systematically explored solutions for mocking strategy and scope decisions using Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse framework.

**Ideas Generated:**

#### Substitute - Mocking Strategy
27. **Mock Auth Implementation** - Simple FastAPI endpoint returning pre-signed JWTs instead of full OIDC server
28. **Mock Data Sources** - Local Parquet/CSV files loaded into Pandas DataFrames instead of Azure Storage
29. **Mock Tenant Metadata DB** - SQLite for PoC instead of full PostgreSQL instance

#### Combine - Simplifications
30. **Combined Auth Service** - FastAPI service handles both token exchange AND mock auth endpoints (⚠️ PoC tradeoff)
31. **Combined Configuration** - Tenant metadata and mock user data in single config file (⚠️ PoC tradeoff)
32. **Shared Validation Module** - JWT validation and data loading module shared across both Plotly apps (⚠️ may remain in MVP)

#### Adapt - Leverage Existing Patterns
33. **Next.js API Routes** - Adapt for reverse proxy with header injection functionality
34. **Plotly Dash Auth Examples** - Adapt existing JWT validation patterns for tenant-scoped tokens
35. **Sample Data Schema Adaptation** - Adapt provided schemas to work with Pandas DataFrames

#### Modify - Strategic Adjustments
36. **Token Lifetime** - Keep realistic (15-30 min) rather than extending for demo convenience
37. **Mock Tenant Count** - Two tenants sufficient for validating switcher mechanism
38. **Tenant Isolation** - Hard tenant isolation is non-negotiable requirement, no simplification

#### Put to Other Uses - Repurposing for Validation
39. **JWT Claims Debug Panel** - Collapsible panel in header displays active JWT claims after tenant switch to demonstrate token exchange
40. **Tenant Selection as Demo Point** - Selection page serves as visual demonstration of architecture mechanism

#### Eliminate - Scope Reductions
41. **User Preferences/Saved Filters** - Out of scope for PoC
42. **Logout Flow** - Out of scope (refresh to reset)
43. **Error Pages** - 401, 403, 404 pages out of scope (simple error messages instead)
44. **HTTPS/CSP Headers** - Out of scope for local development
45. **Logging and Monitoring** - Observability out of scope per original requirements

#### Reverse - Flow Rearrangements
46. **No Reversals Needed** - Standard flow (login → tenant selection → dashboard) optimal for demonstration

**Insights Discovered:**
- Mocking strategy allows focus on architectural mechanisms (JWT exchange, tenant isolation) rather than infrastructure
- Combining services in PoC requires explicit documentation of what must be separated in MVP
- Debug panel serves dual purpose: validation tool during development and demonstration aid for stakeholders
- Scope eliminations are strategic - they remove UI polish and production concerns while keeping core validation intact

**Notable Connections:**
- The substitutions (mock auth, mock data, SQLite) all share goal of removing external dependencies
- The eliminations align with PoC purpose: prove the architecture, not build production-ready features
- Documentation of PoC tradeoffs ensures future teams understand what needs to change for MVP

---

### Question Storming - 15 minutes

**Description:** Generated critical questions for testing and validation rather than jumping to solutions.

**Ideas Generated:**

#### Architecture Validation Questions
1. Does the tenant-scoped JWT contain exactly one `tenant_id` after exchange?
2. Can a user with access to Tenant A see any data from Tenant B?
3. What happens if someone tries to manually edit the JWT in browser dev tools?
4. Does the reverse proxy correctly inject the Authorization header into Dash app requests?

#### Implementation Questions
5. How do we verify the Dash apps are using the in-memory data source and not calling external APIs?
6. What's the end-to-end latency from tenant selection to dashboard render?
7. How do we reset the PoC to a known state for repeated demos?

#### Integration Questions
8. Do both Plotly apps successfully validate JWTs using the shared config module?
9. Does the debug panel correctly show JWT claims after every tenant switch?

#### Data Isolation Questions
10. How do we verify that each Plotly app only loads data for the active tenant from the in-memory source?
11. What happens when the JWT expires while viewing a dashboard?

#### Developer Experience Questions
12. How easy is it for a new developer to set up and run the PoC locally?
13. What documentation artifacts prove the architecture concepts to stakeholders?

#### Edge Case Questions
14. What happens if a user tries to access a tenant they previously had access to but was removed?
15. How does the system behave if the tenant metadata DB is empty or misconfigured?

**Insights Discovered:**
- Security validation (questions 1-4) must prove tenant isolation works as designed
- Developer experience (questions 7, 12) critical for PoC to be repeatable and maintainable
- Edge cases (questions 11, 14, 15) reveal how robust the implementation is
- Documentation artifacts (question 13) serve dual purpose: stakeholder proof and future team guidance

**Notable Connections:**
- Questions map directly to the three challenges identified in Five Whys analysis
- Many questions can be answered through automated tests, forming basis for acceptance criteria
- The validation framework created here will guide epic and story creation in next phase

---

## Idea Categorization

### Immediate Opportunities
*Ideas ready to implement now*

1. **Shared Configuration Module**
   - Description: Create Python module with JWT validation settings (secret key, algorithm, issuer) imported by both FastAPI and Dash apps
   - Why immediate: Solves root cause from Five Whys (config consistency), prevents integration failures
   - Resources needed: Python module file, documentation of config structure, import in all services

2. **Automated Seed Scripts**
   - Description: Scripts to initialize SQLite tenant metadata DB with mock tenants, users, and user-tenant mappings
   - Why immediate: Solves root cause from Five Whys (manual setup errors), enables repeatable demos
   - Resources needed: SQL seed data, Python script, reset mechanism, validation checks

3. **JWT Claims Debug Panel**
   - Description: Collapsible panel in Shell UI header showing decoded JWT claims after tenant selection
   - Why immediate: Critical validation and demonstration tool, low implementation complexity
   - Resources needed: React component, JWT decode logic (frontend), toggle state management

4. **Mock Auth FastAPI Endpoints**
   - Description: Simple endpoints returning pre-generated JWTs for different user/tenant scenarios
   - Why immediate: Foundation for all other PoC work, straightforward implementation
   - Resources needed: FastAPI routes, pre-generated JWT constants, mock user/tenant data structure

5. **Reverse Proxy Header Injection**
   - Description: Next.js API routes that proxy requests to Dash apps with Authorization header injected
   - Why immediate: Core architectural mechanism validation, proven Next.js pattern
   - Resources needed: Next.js rewrites/middleware, Dash app URL configuration, header injection logic

### Future Innovations
*Ideas requiring development/research*

1. **Integration Test Suite**
   - Description: End-to-end tests covering login → tenant selection → token exchange → dashboard load → data filtering
   - Development needed: Test framework selection (Playwright/Cypress), mock data setup, assertion strategies
   - Timeline estimate: Post-PoC implementation, during MVP planning

2. **PoC vs MVP Tradeoff Documentation**
   - Description: Comprehensive document detailing what was combined/simplified in PoC and must be separated in MVP
   - Development needed: Template structure, stakeholder review process, integration with architecture docs
   - Timeline estimate: Created during PoC development, refined for handoff to MVP team

3. **Validation Logging Framework**
   - Description: Structured logging at key handoff points (token exchange, header injection, JWT validation in Dash)
   - Development needed: Logging library selection, log format standardization, log viewing during demos
   - Timeline estimate: Could be added to PoC if time permits, otherwise MVP concern

4. **Multi-User Test Scenarios**
   - Description: Expanded mock user base covering edge cases (single-tenant users, admin roles, removed access)
   - Development needed: Additional mock user data, scenario documentation, test case mapping
   - Timeline estimate: Incremental addition during PoC testing phase

5. **Dashboard Performance Baselines**
   - Description: Measure and document end-to-end latency for tenant switching and dashboard rendering
   - Development needed: Performance measurement tooling, baseline establishment, comparison framework
   - Timeline estimate: Post-PoC, useful for MVP planning

### Moonshots
*Ambitious, transformative concepts*

1. **Interactive Architecture Validation Dashboard**
   - Description: Meta-dashboard showing real-time flow of JWT tokens, tenant context, data scoping across all services
   - Transformative potential: Makes the architecture tangibly visible for stakeholders, becomes a teaching tool for new developers
   - Challenges to overcome: Significant development effort, requires instrumentation across all services, out of PoC scope but powerful for organizational understanding

2. **PoC-to-MVP Migration Automation**
   - Description: Tooling that analyzes the PoC codebase and generates MVP implementation checklist with code references
   - Transformative potential: Bridges PoC learning to production implementation, reduces knowledge loss between phases
   - Challenges to overcome: Requires deep understanding of both architectures, maintenance burden, unclear ROI

3. **Tenant Isolation Chaos Testing**
   - Description: Automated testing framework that attempts to break tenant isolation through various attack vectors
   - Transformative potential: Proves security model robustness, builds confidence in multi-tenant approach, becomes part of CI/CD
   - Challenges to overcome: Security expertise required, test design complexity, may be overkill for PoC but valuable for production

### Insights & Learnings
*Key realizations from the session*

- **PoC Purpose Clarity**: The PoC exists to validate specific architectural mechanisms (JWT exchange, tenant isolation, embedding), not to build a feature-complete application. Scope discipline is critical.

- **Configuration Consistency is Underestimated**: Initial architecture discussion didn't emphasize shared configuration, but Five Whys revealed it as a root cause of multiple failure modes. This is now a first-class requirement.

- **Visibility Drives Confidence**: The JWT claims debug panel emerged as more than a debugging tool—it's a stakeholder confidence builder that makes the abstract architecture concrete and observable.

- **Documentation as Deliverable**: For a PoC, documentation of tradeoffs and learnings may be more valuable than the code itself, since the code may be discarded but the insights inform MVP development.

- **Automation Pays Off Early**: Even in a PoC, automated seed scripts and validation checks reduce friction and enable the iterative testing needed to validate the architecture.

- **Architecture Fidelity Matters**: The decision to stay true to the proposed architecture (reverse proxy, JWT exchange, tenant-scoped tokens) rather than taking shortcuts ensures the PoC actually validates what will be built in MVP.

---

## Action Planning

### Top 3 Priority Ideas

#### #1 Priority: Shared Configuration Module

- **Rationale**: Solves the most critical root cause identified (configuration inconsistency across FastAPI and Dash apps). Without this, JWT validation will fail unpredictably, blocking all other validation work. Low complexity, high impact.

- **Next steps**:
  1. Create `shared_config.py` module with JWT settings (secret key, algorithm, issuer, expiry)
  2. Define mock user and tenant data structures in same module
  3. Import in FastAPI auth service, FastAPI data service, and both Dash apps
  4. Add validation that config is loaded correctly on startup

- **Resources needed**:
  - Python module file in shared location accessible to all services
  - Documentation of config structure and import pattern
  - Startup validation logic

- **Timeline**: Day 1 of PoC implementation (prerequisite for other work)

#### #2 Priority: Automated Seed Scripts with Validation

- **Rationale**: Enables repeatable demos and reduces manual setup errors identified as root cause. Creates foundation for testing tenant isolation. Essential for iterative PoC development.

- **Next steps**:
  1. Create SQL schema for tenant metadata (tenants, users, user_tenants tables)
  2. Write seed data for 2 mock tenants with different user access patterns
  3. Create Python script to initialize SQLite DB from seed data
  4. Add validation script that checks DB state matches expected configuration
  5. Document reset procedure for repeated demos

- **Resources needed**:
  - SQLite database file location
  - SQL schema matching architecture docs
  - Python script using shared config module
  - Validation queries to verify setup

- **Timeline**: Day 1-2 of PoC implementation (parallel with #1)

#### #3 Priority: Mock Auth + Token Exchange Endpoints

- **Rationale**: Core mechanism that everything else depends on. Implements the architectural pattern being validated. Includes both the simplified mock auth and the architecturally-correct token exchange flow.

- **Next steps**:
  1. Implement GET `/api/me` endpoint returning user's tenant_ids from mock data
  2. Implement POST `/api/token/exchange` endpoint validating tenant access and returning tenant-scoped JWT
  3. Create pre-generated JWT constants for different user scenarios
  4. Add JWT validation middleware for protected endpoints
  5. Test token exchange flow with different user/tenant combinations

- **Resources needed**:
  - FastAPI route definitions
  - JWT encoding/decoding library (PyJWT or python-jose)
  - Pre-generated JWT tokens stored in shared config
  - Mock user lookup logic

- **Timeline**: Day 2-3 of PoC implementation (depends on #1)

---

## Reflection & Follow-up

### What Worked Well

- **Morphological Analysis provided clear decision framework** - Breaking down implementation options into discrete parameters helped make concrete choices quickly
- **Five Whys uncovered non-obvious root causes** - Without this technique, configuration consistency might not have been identified as a critical requirement
- **SCAMPER balanced scope and fidelity** - The framework helped distinguish between acceptable PoC shortcuts and non-negotiable architectural requirements
- **Question Storming created validation framework** - The questions generated will directly translate to acceptance criteria for epics and stories
- **Focus on PoC vs MVP tradeoffs** - Explicit discussion of what must be documented for future teams ensures PoC creates organizational value beyond code

### Areas for Further Exploration

- **Plotly Dash In-Memory Data Implementation**: How exactly will the sample data be loaded and filtered in each Dash app? Need to explore Dash callback patterns with JWT-scoped queries.
- **Next.js Reverse Proxy Configuration**: Specific implementation details of header injection via Next.js rewrites or middleware need technical spike.
- **Token Expiry Handling**: What's the UX when JWT expires during dashboard viewing? Does Dash callback fail gracefully? Is there automatic refresh?
- **Sample Data Structure**: Need to examine the provided sample data and schemas to understand transformation requirements for Pandas DataFrame format.
- **Multi-Tenant User Test Scenarios**: What specific user/tenant access combinations should be mocked to validate isolation? (e.g., User A → Tenant 1 only, User B → Tenant 1 & 2, User C → Tenant 2 only)

### Recommended Follow-up Techniques

- **User Story Mapping**: Map out the PoC user journeys (login → tenant selection → dashboard view) with acceptance criteria derived from Question Storming
- **Technical Spike Planning**: Identify which implementation details need research before story estimation (Next.js proxy, Dash JWT validation)
- **Risk Matrix Creation**: Plot the Five Whys challenges against likelihood/impact to prioritize mitigation strategies

### Questions That Emerged

- Should the PoC include any form of token refresh mechanism, or is manual re-login acceptable when JWT expires?
- What level of error handling is expected in the PoC? (Simple error messages vs. error pages vs. none)
- Who are the primary audiences for PoC demonstrations? (Technical stakeholders, business stakeholders, future development team?)
- Are there existing Plotly Dash apps in the organization that could provide JWT validation patterns to adapt?
- Should the PoC repository structure mirror the expected MVP structure (separate repos/folders for Shell UI, FastAPI, Dash apps)?
- What deployment target for the PoC? (Local docker-compose, single cloud VM, separate services?)

### Next Session Planning

- **Suggested topics**:
  1. Architecture review session - Walk through existing architecture docs with Product/Dev leads to create epic structure
  2. Technical spike planning - Identify unknowns that need research before story creation
  3. Story writing workshop - Transform brainstorming insights and questions into concrete user stories with acceptance criteria

- **Recommended timeframe**: Within 1-2 days to maintain momentum and context from this brainstorming session

- **Preparation needed**:
  - Review sample Plotly apps in `sample-plotly-repos/` directory
  - Examine sample data and schemas provided
  - Read full architecture documentation in `existing-architecture-docs/`
  - Identify which BMAD agent should lead next phase (likely Product Manager for epic/story creation)

---

*Session facilitated using the BMAD-METHOD™ brainstorming framework*
