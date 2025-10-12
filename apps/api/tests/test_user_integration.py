"""Integration tests for full user info flow."""
import sys

import pytest
from fastapi.testclient import TestClient

# Add paths for imports
sys.path.insert(0, '/app/packages/shared-config/src')

from shared_config import encode_user_token, get_user_by_email, MOCK_USERS

from apps.api.src.main import app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


class TestUserInfoIntegration:
    """Integration tests for GET /api/me full flow with real database."""

    def test_full_flow_analyst_acme_single_tenant(self, client):
        """Test complete user info flow with analyst@acme.com (single tenant)."""
        # Get mock user data
        user_data = get_user_by_email("analyst@acme.com")
        assert user_data is not None, "Mock user analyst@acme.com not found"

        # Generate user token
        token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        # Call GET /api/me with Authorization header
        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        # Verify user data
        assert data["user_id"] == user_data["user_id"]
        assert data["email"] == "analyst@acme.com"

        # Verify tenants array
        assert "tenants" in data
        assert isinstance(data["tenants"], list)
        assert len(data["tenants"]) >= 1  # Should have at least Acme tenant

        # Verify tenant structure
        tenant = data["tenants"][0]
        assert "id" in tenant
        assert "name" in tenant
        assert "slug" in tenant
        assert "role" in tenant
        assert "config_json" in tenant

        # analyst@acme.com should have viewer role
        assert tenant["role"] == "viewer"

    def test_full_flow_admin_acme_multi_tenant(self, client):
        """Test complete flow with admin@acme.com (multi-tenant)."""
        # Get mock user data
        user_data = get_user_by_email("admin@acme.com")
        assert user_data is not None, "Mock user admin@acme.com not found"

        # Generate user token
        token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        # Call endpoint
        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["email"] == "admin@acme.com"

        # admin@acme.com should have access to 2 tenants (Acme + Beta)
        assert len(data["tenants"]) >= 2

        # Verify tenants are sorted alphabetically
        tenant_names = [t["name"] for t in data["tenants"]]
        assert tenant_names == sorted(tenant_names)

        # Verify admin role
        for tenant in data["tenants"]:
            assert tenant["role"] == "admin"

    def test_full_flow_viewer_beta_single_tenant(self, client):
        """Test complete flow with viewer@beta.com (single tenant)."""
        # Get mock user data
        user_data = get_user_by_email("viewer@beta.com")
        assert user_data is not None, "Mock user viewer@beta.com not found"

        # Generate user token
        token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        # Call endpoint
        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["email"] == "viewer@beta.com"

        # viewer@beta.com should have 1 tenant (Beta only)
        assert len(data["tenants"]) == 1

        tenant = data["tenants"][0]
        assert "beta" in tenant["slug"].lower() or "beta" in tenant["name"].lower()
        assert tenant["role"] == "viewer"

    def test_invalid_token_returns_401(self, client):
        """Test with invalid token returns 401."""
        # Call with invalid token
        response = client.get(
            "/api/me",
            headers={"Authorization": "Bearer invalid-token-xyz"}
        )

        # Should fail with 401
        assert response.status_code == 401
        data = response.json()

        # Verify error format
        assert "error" in data
        error = data["error"]
        assert error["code"] == "INVALID_TOKEN"
        assert "timestamp" in error
        assert "request_id" in error

    def test_missing_authorization_header_returns_401(self, client):
        """Test with missing Authorization header returns 401 or 403."""
        # Call without Authorization header
        response = client.get("/api/me")

        # FastAPI HTTPBearer may return 401 or 403
        assert response.status_code in [401, 403]

    def test_response_structure_matches_specification(self, client):
        """Test that response structure matches UserInfoResponse specification."""
        # Use analyst@acme.com for testing
        user_data = get_user_by_email("analyst@acme.com")
        token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify top-level structure
        assert "user_id" in data
        assert "email" in data
        assert "tenants" in data

        # Verify user_id and email are strings
        assert isinstance(data["user_id"], str)
        assert isinstance(data["email"], str)

        # Verify tenants is an array
        assert isinstance(data["tenants"], list)

        # If tenants exist, verify tenant structure
        if len(data["tenants"]) > 0:
            tenant = data["tenants"][0]
            assert isinstance(tenant["id"], str)
            assert isinstance(tenant["name"], str)
            assert isinstance(tenant["slug"], str)
            assert isinstance(tenant["role"], str)
            assert isinstance(tenant["config_json"], dict)

    def test_all_mock_users_can_get_info(self, client):
        """Test that all 3 mock users can successfully retrieve their info."""
        mock_emails = ["analyst@acme.com", "admin@acme.com", "viewer@beta.com"]

        for email in mock_emails:
            user_data = get_user_by_email(email)
            assert user_data is not None, f"Mock user {email} not found"

            token = encode_user_token({
                "user_id": user_data["user_id"],
                "email": user_data["email"],
                "tenant_ids": user_data["tenant_ids"]
            })

            response = client.get(
                "/api/me",
                headers={"Authorization": f"Bearer {token}"}
            )

            # All should succeed
            assert response.status_code == 200, f"Failed for {email}"
            data = response.json()
            assert data["email"] == email

    def test_tenant_data_includes_all_fields(self, client):
        """Test that tenant data includes all required fields (id, name, slug, role, config_json)."""
        user_data = get_user_by_email("analyst@acme.com")
        token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify each tenant has all required fields
        for tenant in data["tenants"]:
            assert "id" in tenant
            assert "name" in tenant
            assert "slug" in tenant
            assert "role" in tenant
            assert "config_json" in tenant

            # Verify types
            assert isinstance(tenant["id"], str)
            assert isinstance(tenant["name"], str)
            assert isinstance(tenant["slug"], str)
            assert isinstance(tenant["role"], str)
            assert isinstance(tenant["config_json"], dict)

    def test_config_json_is_dict_not_string(self, client):
        """Test that config_json is parsed as dict, not returned as string."""
        user_data = get_user_by_email("analyst@acme.com")
        token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # config_json should be dict, not string
        if len(data["tenants"]) > 0:
            config_json = data["tenants"][0]["config_json"]
            assert isinstance(config_json, dict)
            # Should not be a JSON string
            assert not isinstance(config_json, str)
