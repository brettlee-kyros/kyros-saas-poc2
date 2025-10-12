-- ============================================================================
-- Kyros SaaS PoC - Tenant Metadata Database Schema
-- SQLite implementation with PostgreSQL migration path
-- ============================================================================

-- Enable foreign key constraints (SQLite requires explicit enable)
PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- TENANTS
-- Core tenant records with configuration
-- ----------------------------------------------------------------------------
CREATE TABLE tenants (
    id TEXT PRIMARY KEY,                    -- UUID stored as TEXT (PostgreSQL: UUID type)
    name TEXT NOT NULL,                     -- Display name
    slug TEXT NOT NULL UNIQUE,              -- ⚠️ PoC: Used in URLs (MVP: add opaque token layer)
    is_active INTEGER NOT NULL DEFAULT 1,   -- Boolean (SQLite uses INTEGER 0/1)
    config_json TEXT,                       -- JSONB in PostgreSQL, TEXT in SQLite
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))  -- ISO 8601 timestamp
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_active ON tenants(is_active);

-- ----------------------------------------------------------------------------
-- USERS
-- Authenticated users (sub from JWT)
-- ----------------------------------------------------------------------------
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,               -- UUID from JWT 'sub' claim
    email TEXT NOT NULL UNIQUE,             -- User email
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX idx_users_email ON users(email);

-- ----------------------------------------------------------------------------
-- USER_TENANTS
-- Junction table: which users can access which tenants and their roles
-- ----------------------------------------------------------------------------
CREATE TABLE user_tenants (
    user_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'viewer')),  -- Enum constraint
    PRIMARY KEY (user_id, tenant_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX idx_user_tenants_user ON user_tenants(user_id);
CREATE INDEX idx_user_tenants_tenant ON user_tenants(tenant_id);

-- ----------------------------------------------------------------------------
-- DASHBOARDS
-- Reusable dashboard definitions
-- ----------------------------------------------------------------------------
CREATE TABLE dashboards (
    slug TEXT PRIMARY KEY,                  -- ⚠️ PoC: PK for simplicity (MVP: add UUID id)
    title TEXT NOT NULL,
    description TEXT,
    config_json TEXT,                       -- Dashboard configuration
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

-- ----------------------------------------------------------------------------
-- TENANT_DASHBOARDS
-- Junction table: which dashboards are assigned to which tenants
-- ----------------------------------------------------------------------------
CREATE TABLE tenant_dashboards (
    tenant_id TEXT NOT NULL,
    slug TEXT NOT NULL,                     -- Dashboard slug
    PRIMARY KEY (tenant_id, slug),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (slug) REFERENCES dashboards(slug) ON DELETE CASCADE
);

CREATE INDEX idx_tenant_dashboards_tenant ON tenant_dashboards(tenant_id);
CREATE INDEX idx_tenant_dashboards_slug ON tenant_dashboards(slug);

-- ============================================================================
-- PoC SEED DATA
-- Mock tenants, users, and mappings for testing
-- ============================================================================

-- Two mock tenants
INSERT INTO tenants (id, name, slug, is_active, config_json) VALUES
(
    '8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345',
    'Acme Corporation',
    'acme-corp',
    1,
    '{"branding": {"logo_url": "/logos/acme.svg", "primary_color": "#0052cc"}, "features": {"show_experimental": false}}'
),
(
    '2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4',
    'Beta Industries',
    'beta-ind',
    1,
    '{"branding": {"logo_url": "/logos/beta.svg", "primary_color": "#ff5722"}, "features": {"show_experimental": true}}'
);

-- Three mock users
INSERT INTO users (user_id, email) VALUES
('f8d1e2c3-4b5a-6789-abcd-ef1234567890', 'analyst@acme.com'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'admin@acme.com'),
('b2c3d4e5-f6a7-8901-bcde-f12345678901', 'viewer@beta.com');

-- User-tenant mappings
-- User 1: Viewer access to Acme only
INSERT INTO user_tenants (user_id, tenant_id, role) VALUES
('f8d1e2c3-4b5a-6789-abcd-ef1234567890', '8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345', 'viewer');

-- User 2: Admin access to both Acme and Beta
INSERT INTO user_tenants (user_id, tenant_id, role) VALUES
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', '8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345', 'admin'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', '2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4', 'admin');

-- User 3: Viewer access to Beta only
INSERT INTO user_tenants (user_id, tenant_id, role) VALUES
('b2c3d4e5-f6a7-8901-bcde-f12345678901', '2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4', 'viewer');

-- Two dashboard definitions
INSERT INTO dashboards (slug, title, description, config_json) VALUES
(
    'customer-lifetime-value',
    'Customer Lifetime Value',
    'Analyze customer lifetime value metrics and segmentation',
    '{"layout": "grid", "thresholds": {"high": 15000, "medium": 8000}, "labels": {"currency": "USD"}}'
),
(
    'risk-analysis',
    'Risk Analysis',
    'Risk scoring and exposure analysis dashboards',
    '{"layout": "single", "thresholds": {"critical": 0.8, "warning": 0.5}, "labels": {"unit": "probability"}}'
);

-- Dashboard assignments
-- Acme has both dashboards
INSERT INTO tenant_dashboards (tenant_id, slug) VALUES
('8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345', 'customer-lifetime-value'),
('8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345', 'risk-analysis');

-- Beta has only risk-analysis
INSERT INTO tenant_dashboards (tenant_id, slug) VALUES
('2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4', 'risk-analysis');

-- ============================================================================
-- PostgreSQL Migration Notes (MVP)
-- ============================================================================
-- 1. Change TEXT UUIDs to native UUID type
-- 2. Change INTEGER booleans to BOOLEAN type
-- 3. Change TEXT timestamps to TIMESTAMPTZ
-- 4. Change TEXT JSON to JSONB
-- 5. Add GIN indexes on JSONB columns
-- 6. Enable Row-Level Security (RLS)
-- 7. Create RLS policies for multi-tenant isolation
-- See: docs/architecture/8-database-schema.md#8.2 for migration SQL
