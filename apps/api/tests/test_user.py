"""Unit tests for user info endpoint."""
import sys
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# Add paths for imports
sys.path.insert(0, '/app/packages/shared-config/src')

from shared_config import encode_user_token

from apps.api.src.main import app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_user_data():
    """Mock user data for testing."""
    return {
        "id": "user-123",
        "email": "analyst@acme.com",
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def mock_single_tenant():
    """Mock single tenant data."""
    return [{
        "id": "tenant-123",
        "name": "Acme Corporation",
        "slug": "acme-corp",
        "role": "viewer",
        "config_json": {"branding": {"logo_url": "https://acme.com/logo.png"}}
    }]


@pytest.fixture
def mock_multi_tenants():
    """Mock multi-tenant data (sorted alphabetically)."""
    return [
        {
            "id": "tenant-123",
            "name": "Acme Corporation",
            "slug": "acme-corp",
            "role": "admin",
            "config_json": {"branding": {"logo_url": "https://acme.com/logo.png"}}
        },
        {
            "id": "tenant-456",
            "name": "Beta Industries",
            "slug": "beta-industries",
            "role": "admin",
            "config_json": {"branding": {"logo_url": "https://beta.com/logo.png"}}
        }
    ]


class TestUserInfoEndpoint:
    """Tests for GET /api/me endpoint."""

    @patch("apps.api.src.routers.user.get_user_tenants")
    @patch("apps.api.src.routers.user.get_user_by_id")
    def test_successful_retrieval_single_tenant(
        self,
        mock_get_user,
        mock_get_tenants,
        client,
        mock_user_data,
        mock_single_tenant
    ):
        """Test successful user info retrieval with single tenant."""
        # Setup mocks
        mock_get_user.return_value = AsyncMock(return_value=mock_user_data)()
        mock_get_tenants.return_value = AsyncMock(return_value=mock_single_tenant)()

        # Generate token
        token = encode_user_token({
            "user_id": "user-123",
            "email": "analyst@acme.com",
            "tenant_ids": ["tenant-123"]
        })

        # Call endpoint
        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == "user-123"
        assert data["email"] == "analyst@acme.com"
        assert len(data["tenants"]) == 1

        tenant = data["tenants"][0]
        assert tenant["id"] == "tenant-123"
        assert tenant["name"] == "Acme Corporation"
        assert tenant["slug"] == "acme-corp"
        assert tenant["role"] == "viewer"
        assert "config_json" in tenant

    @patch("apps.api.src.routers.user.get_user_tenants")
    @patch("apps.api.src.routers.user.get_user_by_id")
    def test_successful_retrieval_multi_tenant(
        self,
        mock_get_user,
        mock_get_tenants,
        client,
        mock_user_data,
        mock_multi_tenants
    ):
        """Test successful retrieval with multi-tenant user (admin@acme.com)."""
        # Setup mocks
        mock_user_data["email"] = "admin@acme.com"
        mock_get_user.return_value = AsyncMock(return_value=mock_user_data)()
        mock_get_tenants.return_value = AsyncMock(return_value=mock_multi_tenants)()

        # Generate token
        token = encode_user_token({
            "user_id": "user-123",
            "email": "admin@acme.com",
            "tenant_ids": ["tenant-123", "tenant-456"]
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
        assert len(data["tenants"]) == 2

        # Verify tenants are sorted alphabetically
        assert data["tenants"][0]["name"] == "Acme Corporation"
        assert data["tenants"][1]["name"] == "Beta Industries"

    @patch("apps.api.src.routers.user.get_user_tenants")
    @patch("apps.api.src.routers.user.get_user_by_id")
    def test_tenant_filtering_only_active(
        self,
        mock_get_user,
        mock_get_tenants,
        client,
        mock_user_data
    ):
        """Test that only active tenants are returned (is_active = 1)."""
        # Mock returns only active tenants (database query already filters)
        active_tenants = [{
            "id": "tenant-123",
            "name": "Acme Corporation",
            "slug": "acme-corp",
            "role": "viewer",
            "config_json": {}
        }]

        mock_get_user.return_value = AsyncMock(return_value=mock_user_data)()
        mock_get_tenants.return_value = AsyncMock(return_value=active_tenants)()

        # Generate token with multiple tenants (but only one is active)
        token = encode_user_token({
            "user_id": "user-123",
            "email": "analyst@acme.com",
            "tenant_ids": ["tenant-123", "tenant-inactive"]
        })

        # Call endpoint
        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should only return active tenant
        assert response.status_code == 200
        data = response.json()
        assert len(data["tenants"]) == 1
        assert data["tenants"][0]["id"] == "tenant-123"

    @patch("apps.api.src.routers.user.get_user_tenants")
    @patch("apps.api.src.routers.user.get_user_by_id")
    def test_role_mapping_from_user_tenants(
        self,
        mock_get_user,
        mock_get_tenants,
        client,
        mock_user_data
    ):
        """Test that role is correctly mapped from user_tenants table."""
        # Mock tenant with admin role
        tenant_with_admin = [{
            "id": "tenant-123",
            "name": "Acme Corporation",
            "slug": "acme-corp",
            "role": "admin",  # Role from user_tenants table
            "config_json": {}
        }]

        mock_get_user.return_value = AsyncMock(return_value=mock_user_data)()
        mock_get_tenants.return_value = AsyncMock(return_value=tenant_with_admin)()

        token = encode_user_token({
            "user_id": "user-123",
            "email": "admin@acme.com",
            "tenant_ids": ["tenant-123"]
        })

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tenants"][0]["role"] == "admin"

    @patch("apps.api.src.routers.user.get_user_tenants")
    @patch("apps.api.src.routers.user.get_user_by_id")
    def test_alphabetical_sorting_of_tenants(
        self,
        mock_get_user,
        mock_get_tenants,
        client,
        mock_user_data
    ):
        """Test that tenants are sorted alphabetically by name."""
        # Unsorted tenants
        unsorted_tenants = [
            {
                "id": "tenant-3",
                "name": "Zeta Corp",
                "slug": "zeta-corp",
                "role": "viewer",
                "config_json": {}
            },
            {
                "id": "tenant-1",
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "role": "viewer",
                "config_json": {}
            },
            {
                "id": "tenant-2",
                "name": "Beta Industries",
                "slug": "beta-industries",
                "role": "viewer",
                "config_json": {}
            }
        ]

        # Mock should return sorted (query already sorts)
        sorted_tenants = sorted(unsorted_tenants, key=lambda t: t["name"])

        mock_get_user.return_value = AsyncMock(return_value=mock_user_data)()
        mock_get_tenants.return_value = AsyncMock(return_value=sorted_tenants)()

        token = encode_user_token({
            "user_id": "user-123",
            "email": "analyst@acme.com",
            "tenant_ids": ["tenant-1", "tenant-2", "tenant-3"]
        })

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify alphabetical order
        assert data["tenants"][0]["name"] == "Acme Corporation"
        assert data["tenants"][1]["name"] == "Beta Industries"
        assert data["tenants"][2]["name"] == "Zeta Corp"

    @patch("apps.api.src.routers.user.get_user_by_id")
    def test_404_when_user_not_in_database(self, mock_get_user, client):
        """Test 404 response when user_id from JWT not found in database."""
        # Mock user not found
        mock_get_user.return_value = AsyncMock(return_value=None)()

        token = encode_user_token({
            "user_id": "nonexistent-user",
            "email": "nonexistent@example.com",
            "tenant_ids": []
        })

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should return 404
        assert response.status_code == 404
        data = response.json()

        # Verify error format
        assert "error" in data
        error = data["error"]
        assert error["code"] == "USER_NOT_FOUND"
        assert "nonexistent-user" in error["message"]
        assert "timestamp" in error
        assert "request_id" in error

    @patch("apps.api.src.routers.user.get_user_tenants")
    @patch("apps.api.src.routers.user.get_user_by_id")
    def test_empty_tenants_array_when_no_active_tenants(
        self,
        mock_get_user,
        mock_get_tenants,
        client,
        mock_user_data
    ):
        """Test that empty tenants array is returned when no active tenants (not error)."""
        # User exists but has no active tenants
        mock_get_user.return_value = AsyncMock(return_value=mock_user_data)()
        mock_get_tenants.return_value = AsyncMock(return_value=[])()  # Empty list

        token = encode_user_token({
            "user_id": "user-123",
            "email": "analyst@acme.com",
            "tenant_ids": []
        })

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should succeed with empty tenants array
        assert response.status_code == 200
        data = response.json()
        assert data["tenants"] == []
        assert len(data["tenants"]) == 0
