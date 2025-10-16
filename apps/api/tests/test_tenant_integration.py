"""Integration tests for tenant metadata endpoints with real database."""
import pytest
import sys
from fastapi.testclient import TestClient

# Add shared_config to path
sys.path.insert(0, '/app/packages/shared-config/src')

try:
    from shared_config import encode_tenant_token
    SHARED_CONFIG_AVAILABLE = True
except ImportError:
    SHARED_CONFIG_AVAILABLE = False
    pytest.skip("shared_config not available", allow_module_level=True)

from src.main import app

client = TestClient(app)


@pytest.fixture
def acme_tenant_token():
    """Generate tenant-scoped token for Acme Corporation."""
    return encode_tenant_token({
        "user_id": "f8d1e2c3-4b5a-6789-abcd-ef1234567890",
        "email": "analyst@acme.com",
        "tenant_id": "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
        "role": "viewer"
    })


@pytest.fixture
def beta_tenant_token():
    """Generate tenant-scoped token for Beta Industries."""
    return encode_tenant_token({
        "user_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "email": "viewer@beta.com",
        "tenant_id": "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4",
        "role": "viewer"
    })


@pytest.fixture
def admin_acme_token():
    """Generate tenant-scoped token for admin accessing Acme."""
    return encode_tenant_token({
        "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "email": "admin@acme.com",
        "tenant_id": "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
        "role": "admin"
    })


def test_get_acme_tenant_metadata(acme_tenant_token):
    """Test GET /api/tenant/{tenant_id} with Acme token returns Acme metadata."""
    response = client.get(
        "/api/tenant/8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
        headers={"Authorization": f"Bearer {acme_tenant_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Acme Corporation"
    assert data["slug"] == "acme-corp"
    assert data["is_active"] == 1
    assert isinstance(data["config_json"], dict)
    assert "id" in data
    assert "created_at" in data


def test_get_beta_tenant_metadata(beta_tenant_token):
    """Test GET /api/tenant/{tenant_id} with Beta token returns Beta metadata."""
    response = client.get(
        "/api/tenant/2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4",
        headers={"Authorization": f"Bearer {beta_tenant_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Beta Industries"
    assert data["slug"] == "beta-ind"
    assert data["is_active"] == 1


def test_get_acme_dashboards(acme_tenant_token):
    """Test GET /api/tenant/{tenant_id}/dashboards with Acme token returns 2 dashboards."""
    response = client.get(
        "/api/tenant/8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345/dashboards",
        headers={"Authorization": f"Bearer {acme_tenant_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Acme has both CLV and Risk dashboards
    assert len(data) == 2

    # Verify alphabetical sorting (Customer Lifetime Value before Risk Analysis)
    assert data[0]["title"] == "Customer Lifetime Value"
    assert data[0]["slug"] == "customer-lifetime-value"
    assert data[1]["title"] == "Risk Analysis"
    assert data[1]["slug"] == "risk-analysis"

    # Verify structure
    for dashboard in data:
        assert "slug" in dashboard
        assert "title" in dashboard
        assert "description" in dashboard
        assert "config_json" in dashboard
        assert isinstance(dashboard["config_json"], dict)


def test_get_beta_dashboards(beta_tenant_token):
    """Test GET /api/tenant/{tenant_id}/dashboards with Beta token returns 1 dashboard."""
    response = client.get(
        "/api/tenant/2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4/dashboards",
        headers={"Authorization": f"Bearer {beta_tenant_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Beta has only Risk Analysis dashboard
    assert len(data) == 1
    assert data[0]["title"] == "Risk Analysis"
    assert data[0]["slug"] == "risk-analysis"


def test_cross_tenant_access_acme_to_beta(acme_tenant_token):
    """Test that Acme token cannot access Beta tenant metadata (403)."""
    response = client.get(
        "/api/tenant/2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4",  # Beta tenant
        headers={"Authorization": f"Bearer {acme_tenant_token}"}  # Acme token
    )

    assert response.status_code == 403
    error = response.json()["detail"]["error"]
    assert error["code"] == "TENANT_MISMATCH"
    assert "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345" in error["message"]  # Acme UUID
    assert "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4" in error["message"]  # Beta UUID


def test_cross_tenant_access_beta_to_acme(beta_tenant_token):
    """Test that Beta token cannot access Acme tenant metadata (403)."""
    response = client.get(
        "/api/tenant/8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",  # Acme tenant
        headers={"Authorization": f"Bearer {beta_tenant_token}"}  # Beta token
    )

    assert response.status_code == 403
    error = response.json()["detail"]["error"]
    assert error["code"] == "TENANT_MISMATCH"


def test_cross_tenant_access_dashboards(acme_tenant_token):
    """Test that Acme token cannot access Beta dashboards (403)."""
    response = client.get(
        "/api/tenant/2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4/dashboards",
        headers={"Authorization": f"Bearer {acme_tenant_token}"}
    )

    assert response.status_code == 403
    error = response.json()["detail"]["error"]
    assert error["code"] == "TENANT_MISMATCH"


def test_invalid_tenant_token():
    """Test that invalid token returns 401."""
    response = client.get(
        "/api/tenant/8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
        headers={"Authorization": "Bearer invalid-token-xyz"}
    )

    assert response.status_code == 401
    error = response.json()["detail"]["error"]
    assert error["code"] == "INVALID_TENANT_TOKEN"


def test_missing_authorization_header():
    """Test that missing Authorization header returns 401."""
    response = client.get(
        "/api/tenant/8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"
    )

    assert response.status_code == 403  # FastAPI HTTPBearer returns 403 for missing credentials


def test_role_preserved_in_context(admin_acme_token):
    """Test that admin role is preserved in tenant context."""
    # Admin can still access (same as viewer, no RBAC yet in PoC)
    response = client.get(
        "/api/tenant/8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
        headers={"Authorization": f"Bearer {admin_acme_token}"}
    )

    assert response.status_code == 200
    # Role-based access control not implemented in PoC
    # This test just verifies admin tokens work
