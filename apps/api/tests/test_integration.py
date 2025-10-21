"""
Integration tests for complete API workflows.

Tests multi-endpoint flows with real database interactions to verify
that authentication, token exchange, tenant isolation, and data filtering
all work together correctly.

Test Categories:
1. Authentication flow tests (login → user info → tenant list)
2. Token exchange tests (user token → tenant-scoped token)
3. Tenant metadata and dashboard tests (tenant info, dashboard list)
4. Security and isolation tests (cross-tenant access denial, logging)
"""
import sys
import logging
from typing import Dict, Any

import pytest
from httpx import AsyncClient
import jwt

# Add paths for imports
sys.path.insert(0, '/app/packages/shared-config/src')
sys.path.insert(0, '/app')

from shared_config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    validate_tenant_token,
)


# ============================================================================
# Helper Functions
# ============================================================================

async def get_user_token(async_client: AsyncClient, email: str) -> str:
    """
    Helper: Login and return user access token.

    Args:
        async_client: httpx AsyncClient
        email: User email for mock login

    Returns:
        User access token string
    """
    response = await async_client.post(
        "/api/auth/mock-login",
        json={"email": email}
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    return response.json()["access_token"]


async def exchange_token(async_client: AsyncClient, user_token: str, tenant_id: str) -> str:
    """
    Helper: Exchange user token for tenant-scoped token.

    Args:
        async_client: httpx AsyncClient
        user_token: User access token
        tenant_id: Tenant ID to exchange for

    Returns:
        Tenant-scoped access token string
    """
    response = await async_client.post(
        "/api/token/exchange",
        json={"tenant_id": tenant_id},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200, f"Token exchange failed: {response.json()}"
    return response.json()["access_token"]


# ============================================================================
# Test 1: Authentication Flow Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_and_fetch_tenants_single_tenant_user(async_client, test_db_integration):
    """
    Test: Login → /api/auth/mock-login → /api/me → verify tenant list (single-tenant user).

    AC 2: Test login → /api/auth/mock-login → /api/me → verify tenant list
    """
    # Step 1: Login as single-tenant user
    login_response = await async_client.post(
        "/api/auth/mock-login",
        json={"email": "analyst@acme.com"}
    )
    assert login_response.status_code == 200
    user_token = login_response.json()["access_token"]
    assert user_token is not None

    # Step 2: Fetch user info with tenants
    me_response = await async_client.get(
        "/api/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert me_response.status_code == 200

    data = me_response.json()
    assert data["email"] == "analyst@acme.com"
    assert len(data["tenants"]) == 1  # Single tenant

    # Verify tenant structure
    tenant = data["tenants"][0]
    assert tenant["id"] == "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"  # Acme
    assert tenant["name"] == "Acme Corporation"
    assert tenant["role"] == "viewer"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_and_fetch_tenants_multi_tenant_user(async_client, test_db_integration):
    """
    Test: Login → /api/auth/mock-login → /api/me → verify tenant list (multi-tenant user).

    AC 2: Test login → /api/auth/mock-login → /api/me → verify tenant list
    """
    # Step 1: Login as multi-tenant admin
    login_response = await async_client.post(
        "/api/auth/mock-login",
        json={"email": "admin@acme.com"}
    )
    assert login_response.status_code == 200
    user_token = login_response.json()["access_token"]

    # Step 2: Fetch user info
    me_response = await async_client.get(
        "/api/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert me_response.status_code == 200

    data = me_response.json()
    assert data["email"] == "admin@acme.com"
    assert len(data["tenants"]) == 2  # Multi-tenant user

    # Verify both tenants are present
    tenant_ids = [t["id"] for t in data["tenants"]]
    assert "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345" in tenant_ids  # Acme
    assert "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4" in tenant_ids  # Beta

    # Verify roles
    for tenant in data["tenants"]:
        assert tenant["role"] == "admin"


# ============================================================================
# Test 2: Token Exchange Flow Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_token_exchange_flow_single_tenant(async_client, test_db_integration):
    """
    Test: Login → tenant selection → /api/token/exchange → verify tenant-scoped token claims.

    AC 3: Test login → tenant selection → /api/token/exchange → verify tenant-scoped token
    AC 5: Tests verify tenant-scoped token contains exactly one tenant_id (not array)
    AC 6: Tests verify tenant-scoped token includes correct role from user_tenants table
    """
    # Step 1: Login
    login_response = await async_client.post(
        "/api/auth/mock-login",
        json={"email": "analyst@acme.com"}
    )
    user_token = login_response.json()["access_token"]

    # Step 2: Exchange for tenant-scoped token
    exchange_response = await async_client.post(
        "/api/token/exchange",
        json={"tenant_id": "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert exchange_response.status_code == 200

    response_data = exchange_response.json()
    tenant_token = response_data["access_token"]
    assert response_data["token_type"] == "Bearer"
    assert response_data["expires_in"] == 1800  # 30 minutes

    # Step 3: Decode and verify claims
    decoded = jwt.decode(tenant_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

    assert decoded["sub"] == "f8d1e2c3-4b5a-6789-abcd-ef1234567890"
    assert decoded["email"] == "analyst@acme.com"
    assert decoded["tenant_id"] == "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"  # Single value (not array)
    assert decoded["role"] == "viewer"  # Role from database
    assert "tenant_ids" not in decoded  # Should NOT have array


@pytest.mark.asyncio
@pytest.mark.integration
async def test_token_exchange_flow_multi_tenant_admin(async_client, test_db_integration):
    """
    Test: Multi-tenant admin exchanges for both tenants separately.

    AC 3: Test login → tenant selection → /api/token/exchange → verify tenant-scoped token
    """
    # Login as multi-tenant admin
    user_token = await get_user_token(async_client, "admin@acme.com")

    # Exchange for Acme tenant
    acme_token = await exchange_token(async_client, user_token, "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345")
    decoded_acme = jwt.decode(acme_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert decoded_acme["tenant_id"] == "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"
    assert decoded_acme["role"] == "admin"

    # Exchange for Beta tenant
    beta_token = await exchange_token(async_client, user_token, "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4")
    decoded_beta = jwt.decode(beta_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert decoded_beta["tenant_id"] == "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4"
    assert decoded_beta["role"] == "admin"


# ============================================================================
# Test 3: Tenant Metadata and Dashboard Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_tenant_metadata_retrieval(async_client, test_db_integration):
    """
    Test: Tenant-scoped token → /api/tenant/{id} → verify tenant metadata returned.

    AC 4: Test tenant-scoped token → /api/tenant/{id} → verify tenant metadata returned
    """
    # Get tenant-scoped token for Acme
    user_token = await get_user_token(async_client, "analyst@acme.com")
    tenant_token = await exchange_token(async_client, user_token, "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345")

    # Fetch tenant metadata
    response = await async_client.get(
        "/api/tenant/8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
        headers={"Authorization": f"Bearer {tenant_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"
    assert data["name"] == "Acme Corporation"
    assert data["slug"] == "acme-corp"
    assert data["is_active"] == 1
    # config_json is environment-specific, so just verify it exists
    assert "config_json" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dashboard_list_filtered_by_tenant(async_client, test_db_integration):
    """
    Test: Tenant-scoped token → /api/tenant/{id}/dashboards → verify dashboard list filtered by tenant.

    AC 5: Test tenant-scoped token → /api/tenant/{id}/dashboards → verify dashboard list filtered
    """
    # Get tenant-scoped token for Acme
    user_token = await get_user_token(async_client, "analyst@acme.com")
    acme_token = await exchange_token(async_client, user_token, "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345")

    # Fetch dashboards for Acme
    response = await async_client.get(
        "/api/tenant/8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345/dashboards",
        headers={"Authorization": f"Bearer {acme_token}"}
    )

    assert response.status_code == 200
    dashboards = response.json()

    # Acme has both dashboards in production
    assert len(dashboards) == 2
    dashboard_slugs = [d["slug"] for d in dashboards]
    assert "customer-lifetime-value" in dashboard_slugs
    assert "risk-analysis" in dashboard_slugs


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dashboard_list_beta_tenant(async_client, test_db_integration):
    """
    Test: Beta tenant sees only Beta dashboards.

    AC 5: Test tenant-scoped token → /api/tenant/{id}/dashboards → verify dashboard list filtered
    """
    # Get tenant-scoped token for Beta
    user_token = await get_user_token(async_client, "viewer@beta.com")
    beta_token = await exchange_token(async_client, user_token, "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4")

    # Fetch dashboards for Beta
    response = await async_client.get(
        "/api/tenant/2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4/dashboards",
        headers={"Authorization": f"Bearer {beta_token}"}
    )

    assert response.status_code == 200
    dashboards = response.json()

    # Beta has only risk-analysis dashboard (filtered correctly)
    assert len(dashboards) == 1
    assert dashboards[0]["slug"] == "risk-analysis"
    assert dashboards[0]["title"] == "Risk Analysis"


# ============================================================================
# Test 4: Security and Tenant Isolation Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_cross_tenant_access_denied_tenant_metadata(async_client, test_db_integration):
    """
    Test: Mismatched tenant_id in token vs path parameter → verify 403 error.

    AC 7: Test mismatched tenant_id in token vs path parameter → verify 403 error
    """
    # Get tenant-scoped token for Acme
    user_token = await get_user_token(async_client, "analyst@acme.com")
    acme_token = await exchange_token(async_client, user_token, "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345")

    # Attempt to access Beta's tenant metadata with Acme token
    response = await async_client.get(
        "/api/tenant/2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4",  # Beta tenant
        headers={"Authorization": f"Bearer {acme_token}"}  # Acme token
    )

    assert response.status_code == 403
    error = response.json()
    assert "detail" in error
    assert error["detail"]["error"]["code"] == "TENANT_MISMATCH"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cross_tenant_access_denied_dashboards(async_client, test_db_integration):
    """
    Test: Attempt to access another tenant's dashboards → verify 403 error.

    AC 7: Test mismatched tenant_id in token vs path parameter → verify 403 error
    """
    # Get tenant-scoped token for Acme
    user_token = await get_user_token(async_client, "analyst@acme.com")
    acme_token = await exchange_token(async_client, user_token, "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345")

    # Attempt to access Beta's dashboards with Acme token
    response = await async_client.get(
        "/api/tenant/2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4/dashboards",
        headers={"Authorization": f"Bearer {acme_token}"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unauthorized_tenant_exchange(async_client, test_db_integration):
    """
    Test: Attempt token exchange for unauthorized tenant → verify 403 error.

    AC 7: Test mismatched tenant_id in token vs path parameter → verify 403 error
    """
    # Get user token for single-tenant user (Acme only)
    user_token = await get_user_token(async_client, "analyst@acme.com")

    # Attempt to exchange for Beta tenant (unauthorized)
    response = await async_client.post(
        "/api/token/exchange",
        json={"tenant_id": "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4"},  # Beta
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 403
    error = response.json()
    assert error["detail"]["error"]["code"] == "TENANT_ACCESS_DENIED"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_user_token(async_client, test_db_integration):
    """
    Test: Invalid/malformed user token → verify 401 error.

    AC 4 (Story 6.1): Tests verify invalid user token returns 401
    """
    response = await async_client.post(
        "/api/token/exchange",
        json={"tenant_id": "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"},
        headers={"Authorization": "Bearer invalid-token-12345"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_missing_tenant_id_in_exchange(async_client, test_db_integration):
    """
    Test: Missing tenant_id in token exchange request → verify 400 error.

    AC 4 (Story 6.1): Tests verify missing tenant_id returns 400
    """
    user_token = await get_user_token(async_client, "analyst@acme.com")

    response = await async_client.post(
        "/api/token/exchange",
        json={},  # Missing tenant_id
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 422  # FastAPI validation error


# ============================================================================
# Test 5: Logging Verification Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_logging_output_contains_tenant_info(async_client, test_db_integration, caplog):
    """
    Test: Verify logging output contains expected tenant_id and request details.

    AC 9: Tests verify logging output contains expected tenant_id and request details
    """
    caplog.set_level(logging.INFO)

    # Make authenticated request
    user_token = await get_user_token(async_client, "analyst@acme.com")
    tenant_token = await exchange_token(async_client, user_token, "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345")

    response = await async_client.get(
        "/api/tenant/8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
        headers={"Authorization": f"Bearer {tenant_token}"}
    )

    assert response.status_code == 200

    # Verify log output contains tenant information
    log_messages = [record.message for record in caplog.records]

    # Should contain tenant_id in token exchange logs
    tenant_id_found = any("8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345" in msg for msg in log_messages)
    assert tenant_id_found, "tenant_id not found in logs"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_authentication_success_logging(async_client, test_db_integration, caplog):
    """
    Test: Verify successful authentication is logged.

    AC 9: Tests verify logging output contains expected tenant_id and request details
    """
    caplog.set_level(logging.INFO)

    # Login
    response = await async_client.post(
        "/api/auth/mock-login",
        json={"email": "analyst@acme.com"}
    )

    assert response.status_code == 200

    # Verify authentication success in logs
    log_messages = [record.message for record in caplog.records]
    auth_success = any("Authentication successful" in msg for msg in log_messages)
    assert auth_success, "Authentication success not logged"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_token_exchange_success_logging(async_client, test_db_integration, caplog):
    """
    Test: Verify successful token exchange is logged with details.

    AC 9: Tests verify logging output contains expected tenant_id and request details
    """
    caplog.set_level(logging.INFO)

    # Get user token and exchange
    user_token = await get_user_token(async_client, "analyst@acme.com")

    response = await async_client.post(
        "/api/token/exchange",
        json={"tenant_id": "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200

    # Verify exchange success in logs
    log_messages = [record.message for record in caplog.records]
    exchange_success = any("Token exchange successful" in msg for msg in log_messages)
    assert exchange_success, "Token exchange success not logged"
