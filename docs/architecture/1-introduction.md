# 1. Introduction

This document outlines the complete fullstack architecture for **Kyros Multi-Tenant SaaS PoC**, including backend systems, frontend implementation, and their integration. It serves as the single source of truth for AI-driven development, ensuring consistency across the entire technology stack.

This unified approach combines what would traditionally be separate backend and frontend architecture documents, streamlining the development process for modern fullstack applications where these concerns are increasingly intertwined.

**Purpose of this PoC:**
Validate the proposed multi-tenant architecture by implementing core mechanisms: shell-ui application with mocked authentication, JWT creation and token exchange for tenant isolation, tenant selection UI, and secure embedding of Plotly applications with tenant-scoped data access.

## 1.1 Starter Template or Existing Project

**Status:** Existing Architecture + PoC Simplifications

This PoC is based on **existing architecture documentation** found in `existing-architecture-docs/`, which defines a production-ready multi-tenant SaaS platform. The PoC will validate core architectural patterns while making strategic simplifications:

**Architectural Fidelity Maintained:**
- JWT token exchange mechanism for tenant isolation
- FastAPI monolith as API gateway and data access layer
- Next.js Shell UI with reverse proxy for Dash embedding
- Tenant metadata database for configuration
- Hard tenant isolation (non-negotiable)

**PoC Simplifications (documented for MVP separation):**
- Mock authentication instead of Azure AD B2C
- Pre-generated JWTs instead of cryptographic signing
- SQLite instead of PostgreSQL
- In-memory data sources (Pandas) instead of Azure Storage/Databricks
- Combined FastAPI service (auth + data) instead of separation
- No observability stack (Prometheus/Grafana/Loki)

**Constraints from Existing Architecture:**
- Must demonstrate token exchange flow (user token → tenant-scoped token)
- Must use reverse proxy with header injection for Dash embedding
- Must validate tenant isolation through JWT claims
- Must provide shared configuration module for JWT validation consistency

## 1.2 Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-10-05 | 0.1 | Initial PoC architecture based on brainstorming session | Winston (Architect Agent) |

---
