"""Unit and integration tests for token exchange endpoint."""
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from fastapi.testclient import TestClient

# Add paths for imports
sys.path.insert(0, '/app/packages/shared-config/src')
sys.path.insert(0, '/app')

from shared_config import (
    encode_user_token,
    encode_tenant_token,
    validate_tenant_token,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    TENANT_TOKEN_EXPIRY,
    get_user_by_email
)

from src.main import app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


class TestTokenExchangeAccessValidation:
    """Unit tests for tenant access validation logic."""

    @patch("src.routers.token.get_user_tenant_role")
    def test_exchange_with_authorized_tenant(self, mock_get_role, client):
        """Test token exchange when tenant_id IS in user's tenant_ids array."""
        # Mock role query
        mock_get_role.return_value = AsyncMock(return_value="viewer")()

        # Generate user token with Acme tenant
        user_token = encode_user_token({
            "user_id": "user-123",
            "email": "analyst@acme.com",
            "tenant_ids": ["acme-uuid"]
        })

        # Exchange for authorized tenant
        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": "acme-uuid"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] == 1800

    def test_exchange_with_unauthorized_tenant(self, client):
        """Test token exchange when tenant_id NOT in user's tenant_ids array."""
        # Generate user token with only Acme tenant
        user_token = encode_user_token({
            "user_id": "user-123",
            "email": "analyst@acme.com",
            "tenant_ids": ["acme-uuid"]
        })

        # Attempt exchange for unauthorized Beta tenant
        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": "beta-uuid"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Should return 403
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "TENANT_ACCESS_DENIED"
        assert "beta-uuid" in data["error"]["message"]

    def test_exchange_with_empty_tenant_ids(self, client):
        """Test token exchange with empty tenant_ids array."""
        # Generate user token with no tenants
        user_token = encode_user_token({
            "user_id": "user-123",
            "email": "test@example.com",
            "tenant_ids": []
        })

        # Attempt exchange
        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": "acme-uuid"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Should return 403
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "TENANT_ACCESS_DENIED"

    def test_exchange_with_missing_tenant_id(self, client):
        """Test token exchange with missing tenant_id in request."""
        # Generate valid user token
        user_token = encode_user_token({
            "user_id": "user-123",
            "email": "analyst@acme.com",
            "tenant_ids": ["acme-uuid"]
        })

        # Attempt exchange without tenant_id
        response = client.post(
            "/api/token/exchange",
            json={},  # Empty request
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Should return 422 (FastAPI validation error)
        assert response.status_code == 422

    def test_error_response_format(self, client):
        """Test that error responses match standard format."""
        user_token = encode_user_token({
            "user_id": "user-123",
            "email": "analyst@acme.com",
            "tenant_ids": ["acme-uuid"]
        })

        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": "unauthorized-uuid"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 403
        data = response.json()

        # Verify standard error structure
        assert "error" in data
        error = data["error"]
        assert "code" in error
        assert "message" in error
        assert "timestamp" in error
        assert "request_id" in error

        # Verify timestamp is ISO 8601
        timestamp = datetime.fromisoformat(error["timestamp"].replace('Z', '+00:00'))
        assert timestamp is not None

    def test_tenant_access_denied_error_code(self, client):
        """Verify specific TENANT_ACCESS_DENIED error code."""
        user_token = encode_user_token({
            "user_id": "user-123",
            "email": "viewer@beta.com",
            "tenant_ids": ["beta-uuid"]
        })

        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": "acme-uuid"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "TENANT_ACCESS_DENIED"


class TestTokenExchangeJWTGeneration:
    """Unit tests for JWT generation and structure."""

    @patch("apps.api.src.routers.token.get_user_tenant_role")
    def test_tenant_scoped_jwt_claims_structure(self, mock_get_role, client):
        """Test that tenant-scoped JWT has correct claims structure."""
        # Mock role
        mock_get_role.return_value = AsyncMock(return_value="admin")()

        user_token = encode_user_token({
            "user_id": "admin-uuid",
            "email": "admin@acme.com",
            "tenant_ids": ["acme-uuid", "beta-uuid"]
        })

        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": "acme-uuid"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        tenant_token = response.json()["access_token"]

        # Decode and verify claims
        decoded = jwt.decode(tenant_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Required claims
        assert "sub" in decoded
        assert "email" in decoded
        assert "tenant_id" in decoded
        assert "role" in decoded
        assert "iat" in decoded
        assert "exp" in decoded
        assert "iss" in decoded

    @patch("apps.api.src.routers.token.get_user_tenant_role")
    def test_tenant_id_is_single_value(self, mock_get_role, client):
        """Verify tenant_id is single UUID, not array."""
        mock_get_role.return_value = AsyncMock(return_value="viewer")()

        user_token = encode_user_token({
            "user_id": "user-123",
            "email": "analyst@acme.com",
            "tenant_ids": ["acme-uuid"]
        })

        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": "acme-uuid"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        tenant_token = response.json()["access_token"]
        decoded = jwt.decode(tenant_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # tenant_id should be string, not list
        assert isinstance(decoded["tenant_id"], str)
        assert decoded["tenant_id"] == "acme-uuid"

    @patch("apps.api.src.routers.token.get_user_tenant_role")
    def test_role_included_in_claims(self, mock_get_role, client):
        """Verify role is included in JWT claims."""
        mock_get_role.return_value = AsyncMock(return_value="admin")()

        user_token = encode_user_token({
            "user_id": "admin-uuid",
            "email": "admin@acme.com",
            "tenant_ids": ["acme-uuid"]
        })

        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": "acme-uuid"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        tenant_token = response.json()["access_token"]
        decoded = jwt.decode(tenant_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        assert decoded["role"] == "admin"

    @patch("apps.api.src.routers.token.get_user_tenant_role")
    def test_token_expiry_is_30_minutes(self, mock_get_role, client):
        """Verify exp is 1800 seconds (30 min) from iat."""
        mock_get_role.return_value = AsyncMock(return_value="viewer")()

        user_token = encode_user_token({
            "user_id": "user-123",
            "email": "analyst@acme.com",
            "tenant_ids": ["acme-uuid"]
        })

        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": "acme-uuid"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        tenant_token = response.json()["access_token"]
        decoded = jwt.decode(tenant_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Verify exp is 1800 seconds after iat
        iat = decoded["iat"]
        exp = decoded["exp"]
        diff = exp - iat

        assert diff == 1800  # 30 minutes

    @patch("apps.api.src.routers.token.get_user_tenant_role")
    def test_jwt_signature_validation(self, mock_get_role, client):
        """Verify JWT signature with JWT_SECRET_KEY."""
        mock_get_role.return_value = AsyncMock(return_value="viewer")()

        user_token = encode_user_token({
            "user_id": "user-123",
            "email": "analyst@acme.com",
            "tenant_ids": ["acme-uuid"]
        })

        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": "acme-uuid"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        tenant_token = response.json()["access_token"]

        # Should decode without exception
        decoded = jwt.decode(tenant_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert decoded is not None

    @patch("apps.api.src.routers.token.get_user_tenant_role")
    def test_response_token_type(self, mock_get_role, client):
        """Test token_type is 'Bearer'."""
        mock_get_role.return_value = AsyncMock(return_value="viewer")()

        user_token = encode_user_token({
            "user_id": "user-123",
            "email": "analyst@acme.com",
            "tenant_ids": ["acme-uuid"]
        })

        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": "acme-uuid"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        data = response.json()
        assert data["token_type"] == "Bearer"

    @patch("apps.api.src.routers.token.get_user_tenant_role")
    def test_response_expires_in(self, mock_get_role, client):
        """Test expires_in is 1800 (30 minutes)."""
        mock_get_role.return_value = AsyncMock(return_value="viewer")()

        user_token = encode_user_token({
            "user_id": "user-123",
            "email": "analyst@acme.com",
            "tenant_ids": ["acme-uuid"]
        })

        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": "acme-uuid"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        data = response.json()
        assert data["expires_in"] == 1800
