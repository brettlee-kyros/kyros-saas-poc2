"""Integration tests for dashboard data API endpoint."""
import sys

import pytest
from fastapi.testclient import TestClient

# Add paths for imports
sys.path.insert(0, '/app/packages/shared-config/src')

from shared_config import (
    encode_user_token,
    encode_tenant_token,
    get_user_by_email
)

from src.main import app

# Test tenant IDs
ACME_ID = "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"
BETA_ID = "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4"


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


def create_tenant_token(email: str, tenant_id: str) -> str:
    """
    Helper to create tenant-scoped token for testing.

    Args:
        email: User email
        tenant_id: Tenant UUID

    Returns:
        Encoded JWT token
    """
    user_data = get_user_by_email(email)
    role = "admin" if "admin" in email else "viewer"

    return encode_tenant_token({
        "user_id": user_data["user_id"],
        "email": email,
        "tenant_id": tenant_id,
        "role": role
    })


class TestDashboardDataAPIAuthentication:
    """Test authentication and authorization for dashboard data endpoint."""

    def test_requires_authentication(self, client):
        """Test that endpoint requires authentication."""
        response = client.get("/api/dashboards/customer-lifetime-value/data")

        assert response.status_code == 403, "Should return 403 when no token provided"

    def test_invalid_token_rejected(self, client):
        """Test that invalid tokens are rejected."""
        response = client.get(
            "/api/dashboards/customer-lifetime-value/data",
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401, "Should return 401 for invalid token"

    def test_user_token_rejected(self, client):
        """Test that user tokens (not tenant-scoped) are rejected."""
        # User tokens have tenant_ids array, not single tenant_id
        user_data = get_user_by_email("analyst@acme.com")
        user_token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        response = client.get(
            "/api/dashboards/customer-lifetime-value/data",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Should fail because endpoint expects tenant-scoped token
        assert response.status_code == 401


class TestCLVDashboardAccess:
    """Test CLV dashboard data access (Acme only)."""

    def test_acme_can_access_clv_data(self, client):
        """Test that Acme tenant can access CLV data."""
        token = create_tenant_token("analyst@acme.com", ACME_ID)

        response = client.get(
            "/api/dashboards/customer-lifetime-value/data",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["tenant_id"] == ACME_ID
        assert data["dashboard_slug"] == "customer-lifetime-value"
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0, "Should have CLV data for Acme"

        # Verify all records belong to Acme
        for record in data["data"]:
            assert record["tenant_id"] == ACME_ID

    def test_beta_cannot_access_clv_data(self, client):
        """Test that Beta tenant cannot access CLV data (demonstrates isolation)."""
        token = create_tenant_token("viewer@beta.com", BETA_ID)

        response = client.get(
            "/api/dashboards/customer-lifetime-value/data",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Beta should get 404 because they have no CLV data
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["detail"]["error"]["code"] == "DATA_NOT_FOUND"


class TestRiskDashboardAccess:
    """Test Risk dashboard data access (Acme + Beta)."""

    def test_acme_can_access_risk_data(self, client):
        """Test that Acme tenant can access Risk data."""
        token = create_tenant_token("analyst@acme.com", ACME_ID)

        response = client.get(
            "/api/dashboards/risk-analysis/data",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["tenant_id"] == ACME_ID
        assert data["dashboard_slug"] == "risk-analysis"
        assert len(data["data"]) > 0, "Should have Risk data for Acme"

        # Verify all records belong to Acme
        for record in data["data"]:
            assert record["tenant_id"] == ACME_ID

    def test_beta_can_access_risk_data(self, client):
        """Test that Beta tenant can access Risk data."""
        token = create_tenant_token("viewer@beta.com", BETA_ID)

        response = client.get(
            "/api/dashboards/risk-analysis/data",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["tenant_id"] == BETA_ID
        assert data["dashboard_slug"] == "risk-analysis"
        assert len(data["data"]) > 0, "Should have Risk data for Beta"

        # Verify all records belong to Beta
        for record in data["data"]:
            assert record["tenant_id"] == BETA_ID


class TestTenantDataIsolation:
    """Critical security tests: verify tenant data isolation."""

    def test_acme_cannot_see_beta_risk_data(self, client):
        """Test that Acme cannot see Beta's Risk data."""
        acme_token = create_tenant_token("analyst@acme.com", ACME_ID)

        acme_response = client.get(
            "/api/dashboards/risk-analysis/data",
            headers={"Authorization": f"Bearer {acme_token}"}
        )

        assert acme_response.status_code == 200
        acme_data = acme_response.json()["data"]

        # Verify NO Beta tenant_ids in Acme's data
        tenant_ids_in_acme_data = {record["tenant_id"] for record in acme_data}
        assert BETA_ID not in tenant_ids_in_acme_data, "Acme should not see Beta data"
        assert tenant_ids_in_acme_data == {ACME_ID}, "Should only contain Acme tenant_id"

    def test_beta_cannot_see_acme_risk_data(self, client):
        """Test that Beta cannot see Acme's Risk data."""
        beta_token = create_tenant_token("viewer@beta.com", BETA_ID)

        beta_response = client.get(
            "/api/dashboards/risk-analysis/data",
            headers={"Authorization": f"Bearer {beta_token}"}
        )

        assert beta_response.status_code == 200
        beta_data = beta_response.json()["data"]

        # Verify NO Acme tenant_ids in Beta's data
        tenant_ids_in_beta_data = {record["tenant_id"] for record in beta_data}
        assert ACME_ID not in tenant_ids_in_beta_data, "Beta should not see Acme data"
        assert tenant_ids_in_beta_data == {BETA_ID}, "Should only contain Beta tenant_id"

    def test_acme_and_beta_have_different_risk_data(self, client):
        """Test that Acme and Beta receive different data sets for Risk dashboard."""
        acme_token = create_tenant_token("analyst@acme.com", ACME_ID)
        beta_token = create_tenant_token("viewer@beta.com", BETA_ID)

        acme_response = client.get(
            "/api/dashboards/risk-analysis/data",
            headers={"Authorization": f"Bearer {acme_token}"}
        )
        beta_response = client.get(
            "/api/dashboards/risk-analysis/data",
            headers={"Authorization": f"Bearer {beta_token}"}
        )

        acme_data = acme_response.json()["data"]
        beta_data = beta_response.json()["data"]

        # Both should have data
        assert len(acme_data) > 0
        assert len(beta_data) > 0

        # Record counts should be different
        assert len(acme_data) != len(beta_data), "Should have different amounts of data"

        # Approximately 60/40 split (with some tolerance)
        total_records = len(acme_data) + len(beta_data)
        acme_percentage = (len(acme_data) / total_records) * 100

        assert 55 <= acme_percentage <= 65, f"Acme should have ~60% of data, got {acme_percentage:.1f}%"


class TestInvalidDashboards:
    """Test error handling for invalid dashboard slugs."""

    def test_non_existent_dashboard_returns_404(self, client):
        """Test that requesting non-existent dashboard returns 404."""
        token = create_tenant_token("analyst@acme.com", ACME_ID)

        response = client.get(
            "/api/dashboards/non-existent-dashboard/data",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        error_data = response.json()
        assert error_data["detail"]["error"]["code"] == "DATA_NOT_FOUND"

    def test_empty_dashboard_slug(self, client):
        """Test handling of empty dashboard slug."""
        token = create_tenant_token("analyst@acme.com", ACME_ID)

        response = client.get(
            "/api/dashboards//data",  # Empty slug
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should return 404 (FastAPI path matching)
        assert response.status_code == 404


class TestResponseFormat:
    """Test API response format and structure."""

    def test_response_has_required_fields(self, client):
        """Test that response includes all required fields."""
        token = create_tenant_token("analyst@acme.com", ACME_ID)

        response = client.get(
            "/api/dashboards/customer-lifetime-value/data",
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.json()

        # Verify required top-level fields
        assert "tenant_id" in data
        assert "dashboard_slug" in data
        assert "data" in data

        # Verify field types
        assert isinstance(data["tenant_id"], str)
        assert isinstance(data["dashboard_slug"], str)
        assert isinstance(data["data"], list)

    def test_data_records_are_dictionaries(self, client):
        """Test that data array contains dictionary objects."""
        token = create_tenant_token("analyst@acme.com", ACME_ID)

        response = client.get(
            "/api/dashboards/customer-lifetime-value/data",
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.json()["data"]

        assert len(data) > 0
        for record in data:
            assert isinstance(record, dict), "Each record should be a dictionary"
            assert "tenant_id" in record, "Each record should have tenant_id"


class TestEndToEndFlow:
    """Test complete end-to-end flow: token exchange + data access."""

    def test_complete_flow_analyst_acme(self, client):
        """Test complete flow: login -> exchange -> get CLV data."""
        # Step 1: Mock login (get user token)
        user_data = get_user_by_email("analyst@acme.com")
        user_token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        # Step 2: Exchange for tenant-scoped token
        exchange_response = client.post(
            "/api/token/exchange",
            json={"tenant_id": ACME_ID},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert exchange_response.status_code == 200
        tenant_token = exchange_response.json()["access_token"]

        # Step 3: Access dashboard data with tenant token
        data_response = client.get(
            "/api/dashboards/customer-lifetime-value/data",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )

        assert data_response.status_code == 200
        data = data_response.json()

        assert data["tenant_id"] == ACME_ID
        assert len(data["data"]) > 0

    def test_complete_flow_admin_multi_tenant(self, client):
        """Test admin accessing both Acme and Beta Risk data."""
        user_data = get_user_by_email("admin@acme.com")
        user_token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        # Exchange for Acme
        acme_exchange = client.post(
            "/api/token/exchange",
            json={"tenant_id": ACME_ID},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        acme_token = acme_exchange.json()["access_token"]

        # Exchange for Beta
        beta_exchange = client.post(
            "/api/token/exchange",
            json={"tenant_id": BETA_ID},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        beta_token = beta_exchange.json()["access_token"]

        # Access Risk data for Acme
        acme_data_response = client.get(
            "/api/dashboards/risk-analysis/data",
            headers={"Authorization": f"Bearer {acme_token}"}
        )

        # Access Risk data for Beta
        beta_data_response = client.get(
            "/api/dashboards/risk-analysis/data",
            headers={"Authorization": f"Bearer {beta_token}"}
        )

        # Both should succeed
        assert acme_data_response.status_code == 200
        assert beta_data_response.status_code == 200

        # Verify different data
        acme_data = acme_data_response.json()["data"]
        beta_data = beta_data_response.json()["data"]

        assert all(r["tenant_id"] == ACME_ID for r in acme_data)
        assert all(r["tenant_id"] == BETA_ID for r in beta_data)
