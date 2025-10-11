# 5. API Specification

The FastAPI monolith exposes REST endpoints for mock authentication, token exchange, tenant metadata, and dashboard data access. All endpoints except mock auth require Bearer token authentication.

## REST API Specification

```yaml
openapi: 3.0.0
info:
  title: Kyros SaaS PoC API
  version: 0.1.0
  description: |
    FastAPI monolith providing mock authentication, JWT token exchange,
    tenant metadata, and tenant-scoped dashboard data access.

    ⚠️ PoC Simplifications:
    - Mock auth endpoints return pre-generated JWTs (not production OIDC)
    - Combined auth and data services (MVP should separate these)
    - No rate limiting or advanced security headers

servers:
  - url: http://localhost:8000
    description: Local development (Docker Compose)

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        JWT token in Authorization header.
        - User Access Token: Contains tenant_ids array
        - Tenant-Scoped Token: Contains single tenant_id

  schemas:
    Error:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: object
            timestamp:
              type: string
              format: date-time
            request_id:
              type: string

paths:
  /api/auth/mock-login:
    post:
      summary: Mock login endpoint (PoC only)
      description: |
        Returns a pre-generated user access token for testing.
        ⚠️ NOT FOR PRODUCTION - Replace with Azure AD B2C OIDC flow in MVP.
      tags:
        - Mock Auth
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                  format: email
                  example: "analyst@acme.com"
      responses:
        '200':
          description: User access token issued
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  token_type:
                    type: string
                    enum: [Bearer]
                  expires_in:
                    type: integer
        '404':
          description: User not found in mock data
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /api/me:
    get:
      summary: Get current user info and accessible tenants
      description: |
        Returns user profile and list of tenants they have access to.
        Requires user access token.
      tags:
        - User
      security:
        - BearerAuth: []
      responses:
        '200':
          description: User info with tenant list
        '401':
          description: Invalid or expired token
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /api/token/exchange:
    post:
      summary: Exchange user token for tenant-scoped token
      description: |
        Validates user has access to requested tenant and issues a
        short-lived tenant-scoped JWT (15-30 min lifetime).
        This is the core architectural mechanism being validated in the PoC.
      tags:
        - Token Exchange
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - tenant_id
              properties:
                tenant_id:
                  type: string
                  format: uuid
      responses:
        '200':
          description: Tenant-scoped token issued
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                    description: Tenant-scoped JWT
                  token_type:
                    type: string
                    enum: [Bearer]
                  expires_in:
                    type: integer
                    description: Token lifetime in seconds
        '400':
          description: Invalid request (missing tenant_id)
        '401':
          description: Invalid or expired user token
        '403':
          description: User does not have access to requested tenant
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /api/tenant/{tenant_id}:
    get:
      summary: Get tenant metadata
      description: |
        Returns tenant configuration including branding and feature flags.
        Requires tenant-scoped token with matching tenant_id.
      tags:
        - Tenant
      security:
        - BearerAuth: []
      parameters:
        - name: tenant_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Tenant metadata
        '401':
          description: Invalid or expired token
        '403':
          description: Token tenant_id does not match requested tenant
        '404':
          description: Tenant not found

  /api/tenant/{tenant_id}/dashboards:
    get:
      summary: List dashboards assigned to tenant
      description: |
        Returns array of dashboards the tenant has access to.
        Requires tenant-scoped token with matching tenant_id.
      tags:
        - Dashboards
      security:
        - BearerAuth: []
      parameters:
        - name: tenant_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: List of tenant's dashboards
        '401':
          description: Invalid or expired token
        '403':
          description: Token tenant_id does not match requested tenant

  /api/dashboards/{slug}/data:
    get:
      summary: Get dashboard data for active tenant
      description: |
        Returns tenant-filtered data for the specified dashboard.
        Tenant context extracted from JWT tenant_id claim.
        Data is loaded from in-memory Pandas DataFrames (PoC) or
        queried from tenant-scoped storage (MVP).
      tags:
        - Dashboard Data
      security:
        - BearerAuth: []
      parameters:
        - name: slug
          in: path
          required: true
          schema:
            type: string
          example: "customer-lifetime-value"
        - name: filters
          in: query
          required: false
          schema:
            type: object
          description: Optional filters (JSON object)
      responses:
        '200':
          description: Tenant-scoped dashboard data
        '401':
          description: Invalid or expired token
        '403':
          description: Tenant does not have access to this dashboard
        '404':
          description: Dashboard not found or no data available

  /health:
    get:
      summary: Health check endpoint
      description: Returns service health status
      tags:
        - System
      responses:
        '200':
          description: Service is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    enum: [ok]
                  timestamp:
                    type: string
                    format: date-time
```

---
