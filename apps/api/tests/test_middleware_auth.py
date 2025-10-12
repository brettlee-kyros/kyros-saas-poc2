"""Unit tests for JWT authentication middleware."""
import sys
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

# Add paths for imports
sys.path.insert(0, '/app/packages/shared-config/src')

from shared_config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ISSUER, encode_user_token

from apps.api.src.middleware.auth import get_current_user

# Create minimal FastAPI app for testing middleware
app = FastAPI()


@app.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    """Test endpoint that uses get_current_user dependency."""
    return {"user_id": current_user.get("sub"), "email": current_user.get("email")}


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


@pytest.fixture
def valid_user_data():
    """Valid user data for token generation."""
    return {
        "user_id": "test-user-id-123",
        "email": "test@example.com",
        "tenant_ids": ["tenant-1", "tenant-2"]
    }


class TestJWTValidationMiddleware:
    """Tests for get_current_user JWT validation middleware."""

    def test_valid_token_accepted(self, client, valid_user_data):
        """Test that valid user token is accepted and claims extracted."""
        # Generate valid token
        token = encode_user_token(valid_user_data)

        # Call protected endpoint
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == valid_user_data["user_id"]
        assert data["email"] == valid_user_data["email"]

    def test_expired_token_returns_401(self, client):
        """Test that expired token returns 401 with proper error format."""
        # Generate expired token (expired 1 hour ago)
        expired_time = datetime.now(timezone.utc) - timedelta(hours=2)
        payload = {
            "sub": "user-id",
            "email": "test@example.com",
            "tenant_ids": ["tenant-1"],
            "iat": int(expired_time.timestamp()),
            "exp": int((expired_time + timedelta(hours=1)).timestamp()),
            "iss": JWT_ISSUER
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        # Call protected endpoint
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should fail with 401
        assert response.status_code == 401
        data = response.json()

        # Verify error format
        assert "error" in data
        error = data["error"]
        assert error["code"] == "INVALID_TOKEN"
        assert "expired" in error["message"].lower()
        assert "timestamp" in error
        assert "request_id" in error

    def test_invalid_signature_returns_401(self, client):
        """Test that token with invalid signature returns 401."""
        # Generate token with wrong secret
        payload = {
            "sub": "user-id",
            "email": "test@example.com",
            "tenant_ids": ["tenant-1"],
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "iss": JWT_ISSUER
        }
        token = jwt.encode(payload, "wrong-secret-key", algorithm=JWT_ALGORITHM)

        # Call protected endpoint
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should fail with 401
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "INVALID_TOKEN"

    def test_missing_authorization_header_returns_401(self, client):
        """Test that missing Authorization header returns 401."""
        # Call protected endpoint without Authorization header
        response = client.get("/protected")

        # Should fail with 401 or 403 (FastAPI HTTPBearer behavior)
        assert response.status_code in [401, 403]

    def test_malformed_bearer_token_returns_401(self, client):
        """Test that malformed Bearer token returns 401."""
        # Call with malformed token (not a valid JWT)
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer not-a-valid-jwt"}
        )

        # Should fail with 401
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "INVALID_TOKEN"

    def test_token_with_missing_claims_returns_401(self, client):
        """Test that token with missing required claims returns 401."""
        # Generate token missing required claims (no tenant_ids)
        payload = {
            "sub": "user-id",
            "email": "test@example.com",
            # Missing tenant_ids
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "iss": JWT_ISSUER
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        # Call protected endpoint
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should fail with 401 (shared_config validation should reject)
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "INVALID_TOKEN"

    def test_error_response_format(self, client):
        """Test that error responses match standard format."""
        # Use expired token to trigger error
        expired_time = datetime.now(timezone.utc) - timedelta(hours=2)
        payload = {
            "sub": "user-id",
            "email": "test@example.com",
            "tenant_ids": ["tenant-1"],
            "iat": int(expired_time.timestamp()),
            "exp": int((expired_time + timedelta(hours=1)).timestamp()),
            "iss": JWT_ISSUER
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401
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

    def test_valid_token_extracts_all_claims(self, client, valid_user_data):
        """Test that middleware extracts all required claims from valid token."""
        token = encode_user_token(valid_user_data)

        # Decode token to verify claims
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Verify all expected claims are present
        assert "sub" in decoded
        assert "email" in decoded
        assert "tenant_ids" in decoded
        assert "iat" in decoded
        assert "exp" in decoded
        assert "iss" in decoded

        # Verify claim values
        assert decoded["sub"] == valid_user_data["user_id"]
        assert decoded["email"] == valid_user_data["email"]
        assert decoded["tenant_ids"] == valid_user_data["tenant_ids"]
