"""Unit tests for authentication endpoints."""
import sys
from datetime import datetime

import jwt
import pytest
from fastapi.testclient import TestClient

# Add paths for imports
sys.path.insert(0, '/app/packages/shared-config/src')

from shared_config import JWT_SECRET_KEY, JWT_ALGORITHM

from apps.api.src.main import app

@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


class TestMockLogin:
    """Tests for POST /api/auth/mock-login endpoint."""

    def test_successful_login_with_valid_email(self, client):
        """Test successful authentication with valid email (analyst@acme.com)."""
        response = client.post(
            "/api/auth/mock-login",
            json={"email": "analyst@acme.com"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data

        # Verify token_type
        assert data["token_type"] == "Bearer"

        # Verify expires_in
        assert data["expires_in"] == 3600

    def test_jwt_claims_structure(self, client):
        """Test JWT claims structure (sub, email, tenant_ids, iat, exp)."""
        response = client.post(
            "/api/auth/mock-login",
            json={"email": "analyst@acme.com"}
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        # Decode and verify JWT
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Verify required claims exist
        assert "sub" in decoded
        assert "email" in decoded
        assert "tenant_ids" in decoded
        assert "iat" in decoded
        assert "exp" in decoded

        # Verify claim values
        assert decoded["email"] == "analyst@acme.com"
        assert isinstance(decoded["tenant_ids"], list)
        assert len(decoded["tenant_ids"]) > 0

    def test_jwt_signature_validation(self, client):
        """Test JWT signature can be validated with JWT_SECRET_KEY."""
        response = client.post(
            "/api/auth/mock-login",
            json={"email": "admin@acme.com"}
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        # Should not raise exception
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert decoded is not None

    def test_404_response_for_nonexistent_user(self, client):
        """Test 404 response for non-existent user email."""
        response = client.post(
            "/api/auth/mock-login",
            json={"email": "nonexistent@example.com"}
        )

        assert response.status_code == 404

    def test_error_response_format(self, client):
        """Test error response format matches standard."""
        response = client.post(
            "/api/auth/mock-login",
            json={"email": "nonexistent@example.com"}
        )

        assert response.status_code == 404
        data = response.json()

        # Verify standard error format
        assert "error" in data
        error = data["error"]

        assert "code" in error
        assert "message" in error
        assert "timestamp" in error
        assert "request_id" in error

        # Verify error code
        assert error["code"] == "USER_NOT_FOUND"

        # Verify message contains email
        assert "nonexistent@example.com" in error["message"]

        # Verify timestamp is ISO 8601
        # Should be parseable as datetime
        timestamp = datetime.fromisoformat(error["timestamp"].replace('Z', '+00:00'))
        assert timestamp is not None

    def test_multi_tenant_user_token(self, client):
        """Test admin@acme.com returns token with multiple tenant_ids."""
        response = client.post(
            "/api/auth/mock-login",
            json={"email": "admin@acme.com"}
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # admin@acme.com should have access to multiple tenants
        assert len(decoded["tenant_ids"]) >= 2

    def test_single_tenant_user_token(self, client):
        """Test viewer@beta.com returns token with single tenant_id."""
        response = client.post(
            "/api/auth/mock-login",
            json={"email": "viewer@beta.com"}
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # viewer@beta.com should have access to one tenant
        assert len(decoded["tenant_ids"]) == 1
