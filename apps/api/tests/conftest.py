"""
Shared pytest fixtures for API tests.

Provides test database, test clients, and token fixtures.
"""
import sys
import os
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Add paths for imports (handle both Docker and local)
# In Docker: /app/packages/shared-config/src
# Locally: relative to project root
if os.path.exists('/app/packages/shared-config/src'):
    sys.path.insert(0, '/app/packages/shared-config/src')
else:
    project_root = Path(__file__).parent.parent.parent.parent
    shared_config_path = project_root / 'packages' / 'shared-config' / 'src'
    if shared_config_path.exists():
        sys.path.insert(0, str(shared_config_path))

from shared_config import encode_user_token, encode_tenant_token

# Import app
# In Docker: /app/src/main.py
sys.path.insert(0, '/app')
from src.main import app


# ============================================================================
# Test Token Fixtures
# ============================================================================

@pytest.fixture
def user_token() -> str:
    """Generate valid user access token for testing (multi-tenant)."""
    return encode_user_token({
        "user_id": "user-test-123",
        "email": "test@example.com",
        "tenant_ids": ["tenant-1", "tenant-2"]
    })


@pytest.fixture
def single_tenant_user_token() -> str:
    """Generate user token with single tenant."""
    return encode_user_token({
        "user_id": "user-single-456",
        "email": "single@example.com",
        "tenant_ids": ["tenant-1"]
    })


@pytest.fixture
def tenant_token() -> str:
    """Generate valid tenant-scoped token for testing."""
    return encode_tenant_token({
        "user_id": "user-test-123",
        "email": "test@example.com",
        "tenant_id": "tenant-1",
        "role": "viewer"
    })


@pytest.fixture
def admin_tenant_token() -> str:
    """Generate tenant-scoped token with admin role."""
    return encode_tenant_token({
        "user_id": "user-admin-789",
        "email": "admin@example.com",
        "tenant_id": "tenant-1",
        "role": "admin"
    })


# ============================================================================
# Async HTTP Client Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for testing FastAPI app.

    Uses httpx.AsyncClient with ASGITransport for direct app testing
    without requiring a running server.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ============================================================================
# Database Fixtures (for integration tests - Story 6.2)
# ============================================================================

import aiosqlite
import json
from datetime import datetime, timezone


@pytest_asyncio.fixture(scope="module")
async def test_db_integration():
    """
    Create persistent SQLite database for integration tests with seeded fixtures.

    Seeds database with:
    - 2 tenants: Acme Corp, Beta Industries
    - 3 users: analyst@acme.com (single-tenant), admin@acme.com (multi-tenant), viewer@beta.com
    - User-tenant relationships with roles
    - 2 dashboards (one per tenant)

    Database persists for entire test module, then is cleaned up.
    """
    db_path = "/tmp/test_integration.db"

    # Remove existing test database if present
    if os.path.exists(db_path):
        os.remove(db_path)

    # Create connection and schema
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row

    # Create schema
    await conn.execute("""
        CREATE TABLE tenants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            config_json TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
        )
    """)

    await conn.execute("""
        CREATE TABLE users (
            user_id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
        )
    """)

    await conn.execute("""
        CREATE TABLE user_tenants (
            user_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'viewer')),
            PRIMARY KEY (user_id, tenant_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
        )
    """)

    await conn.execute("""
        CREATE TABLE dashboards (
            slug TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            config_json TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
        )
    """)

    await conn.execute("""
        CREATE TABLE tenant_dashboards (
            tenant_id TEXT NOT NULL,
            slug TEXT NOT NULL,
            PRIMARY KEY (tenant_id, slug),
            FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
            FOREIGN KEY (slug) REFERENCES dashboards(slug) ON DELETE CASCADE
        )
    """)

    # Seed test data
    # Tenant 1: Acme Corporation (matches production database)
    await conn.execute(
        "INSERT INTO tenants (id, name, slug, is_active, config_json) VALUES (?, ?, ?, ?, ?)",
        ("8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345", "Acme Corporation", "acme-corp", 1, json.dumps({"theme": "blue"}))
    )

    # Tenant 2: Beta Industries (matches production database)
    await conn.execute(
        "INSERT INTO tenants (id, name, slug, is_active, config_json) VALUES (?, ?, ?, ?, ?)",
        ("2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4", "Beta Industries", "beta-ind", 1, json.dumps({"theme": "green"}))
    )

    # User 1: analyst@acme.com (single tenant)
    await conn.execute(
        "INSERT INTO users (user_id, email) VALUES (?, ?)",
        ("f8d1e2c3-4b5a-6789-abcd-ef1234567890", "analyst@acme.com")
    )

    # User 2: admin@acme.com (multi-tenant)
    await conn.execute(
        "INSERT INTO users (user_id, email) VALUES (?, ?)",
        ("a1b2c3d4-e5f6-7890-abcd-ef1234567891", "admin@acme.com")
    )

    # User 3: viewer@beta.com (single tenant)
    await conn.execute(
        "INSERT INTO users (user_id, email) VALUES (?, ?)",
        ("c3d4e5f6-a7b8-9012-cdef-ab1234567892", "viewer@beta.com")
    )

    # User-Tenant relationships
    await conn.execute(
        "INSERT INTO user_tenants (user_id, tenant_id, role) VALUES (?, ?, ?)",
        ("f8d1e2c3-4b5a-6789-abcd-ef1234567890", "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345", "viewer")
    )
    await conn.execute(
        "INSERT INTO user_tenants (user_id, tenant_id, role) VALUES (?, ?, ?)",
        ("a1b2c3d4-e5f6-7890-abcd-ef1234567891", "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345", "admin")
    )
    await conn.execute(
        "INSERT INTO user_tenants (user_id, tenant_id, role) VALUES (?, ?, ?)",
        ("a1b2c3d4-e5f6-7890-abcd-ef1234567891", "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4", "admin")
    )
    await conn.execute(
        "INSERT INTO user_tenants (user_id, tenant_id, role) VALUES (?, ?, ?)",
        ("c3d4e5f6-a7b8-9012-cdef-ab1234567892", "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4", "viewer")
    )

    # Dashboards
    await conn.execute(
        "INSERT INTO dashboards (slug, title, description, config_json) VALUES (?, ?, ?, ?)",
        ("customer-lifetime-value", "Customer Lifetime Value", "CLV analysis dashboard", json.dumps({"port": 8051}))
    )
    await conn.execute(
        "INSERT INTO dashboards (slug, title, description, config_json) VALUES (?, ?, ?, ?)",
        ("risk-analysis", "Risk Analysis", "Risk assessment dashboard", json.dumps({"port": 8052}))
    )

    # Tenant-Dashboard relationships (matching production)
    # Acme has both dashboards
    await conn.execute(
        "INSERT INTO tenant_dashboards (tenant_id, slug) VALUES (?, ?)",
        ("8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345", "customer-lifetime-value")
    )
    await conn.execute(
        "INSERT INTO tenant_dashboards (tenant_id, slug) VALUES (?, ?)",
        ("8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345", "risk-analysis")
    )
    # Beta has risk-analysis dashboard
    await conn.execute(
        "INSERT INTO tenant_dashboards (tenant_id, slug) VALUES (?, ?)",
        ("2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4", "risk-analysis")
    )

    await conn.commit()

    # Override DATABASE_PATH for integration tests
    original_db_path = os.environ.get("DATABASE_PATH")
    os.environ["DATABASE_PATH"] = db_path

    yield conn

    # Cleanup
    await conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)

    # Restore original DATABASE_PATH
    if original_db_path:
        os.environ["DATABASE_PATH"] = original_db_path
    else:
        os.environ.pop("DATABASE_PATH", None)


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
