"""Integration tests for full authentication flow."""
import sys

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


class TestMockLoginIntegration:
    """Integration tests for POST /api/auth/mock-login full flow."""

    def test_full_login_flow_analyst_acme(self, client):
        """Test complete login flow with analyst@acme.com."""
        # Make login request
        response = client.post(
            "/api/auth/mock-login",
            json={"email": "analyst@acme.com"}
        )

        # Verify success
        assert response.status_code == 200
        data = response.json()

        # Decode and verify JWT
        token = data["access_token"]
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Verify user details
        assert decoded["email"] == "analyst@acme.com"
        assert isinstance(decoded["tenant_ids"], list)

        # analyst@acme.com should have Acme tenant
        assert len(decoded["tenant_ids"]) >= 1

    def test_full_login_flow_admin_acme(self, client):
        """Test complete login flow with admin@acme.com (multi-tenant)."""
        response = client.post(
            "/api/auth/mock-login",
            json={"email": "admin@acme.com"}
        )

        assert response.status_code == 200
        token = response.json()["access_token"]
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Verify multi-tenant access
        assert decoded["email"] == "admin@acme.com"
        assert len(decoded["tenant_ids"]) >= 2  # Acme + Beta

    def test_full_login_flow_viewer_beta(self, client):
        """Test complete login flow with viewer@beta.com."""
        response = client.post(
            "/api/auth/mock-login",
            json={"email": "viewer@beta.com"}
        )

        assert response.status_code == 200
        token = response.json()["access_token"]
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Verify single tenant access
        assert decoded["email"] == "viewer@beta.com"
        assert len(decoded["tenant_ids"]) == 1  # Beta only

    def test_invalid_email_returns_404(self, client):
        """Test with invalid email returns 404."""
        response = client.post(
            "/api/auth/mock-login",
            json={"email": "invalid@example.com"}
        )

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "USER_NOT_FOUND"

    def test_malformed_email_returns_error(self, client):
        """Test with malformed email format returns error."""
        response = client.post(
            "/api/auth/mock-login",
            json={"email": "not-an-email"}
        )

        # FastAPI/Pydantic should reject invalid email format
        assert response.status_code == 422  # Unprocessable Entity

    def test_token_usable_in_authorization_header(self, client):
        """Test that token can be used in Authorization header."""
        # Get token
        response = client.post(
            "/api/auth/mock-login",
            json={"email": "analyst@acme.com"}
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        # Verify token format is valid for Authorization header
        assert isinstance(token, str)
        assert len(token) > 0

        # Token should be decodable (validates it's a proper JWT)
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert decoded is not None

    def test_token_expiration_claim(self, client):
        """Test that token has proper expiration (1 hour from iat)."""
        response = client.post(
            "/api/auth/mock-login",
            json={"email": "analyst@acme.com"}
        )

        assert response.status_code == 200
        token = response.json()["access_token"]
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Verify exp is approximately 3600 seconds after iat
        iat = decoded["iat"]
        exp = decoded["exp"]
        diff = exp - iat

        # Should be 3600 seconds (1 hour)
        assert diff == 3600

    def test_all_mock_users_can_login(self, client):
        """Test all 3 mock users can successfully login."""
        mock_users = [
            "analyst@acme.com",
            "admin@acme.com",
            "viewer@beta.com"
        ]

        for email in mock_users:
            response = client.post(
                "/api/auth/mock-login",
                json={"email": email}
            )

            assert response.status_code == 200, f"Failed for {email}"
            token = response.json()["access_token"]
            decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            assert decoded["email"] == email
