"""
Unit tests for JWT encoding, decoding, and validation.

Tests the shared_config jwt_utils functions in isolation.
"""
import sys
import os
import time
from datetime import datetime, timedelta, UTC
from pathlib import Path

import jwt
import pytest

# Add paths for imports - Docker environment
sys.path.insert(0, '/app/packages/shared-config/src')

from shared_config import (
    encode_user_token,
    encode_tenant_token,
    validate_user_token,
    validate_tenant_token,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_ISSUER,
)


class TestUserTokenEncoding:
    """Test user access token (multi-tenant) encoding."""

    def test_encode_user_token_with_correct_claims(self):
        """Test JWT encoding with correct claims (user_id, email, tenant_ids)."""
        # Arrange
        user_data = {
            "user_id": "user-123",
            "email": "test@example.com",
            "tenant_ids": ["tenant-1", "tenant-2"]
        }

        # Act
        token = encode_user_token(user_data)

        # Assert - decode without validation to inspect claims
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        assert decoded["sub"] == "user-123"
        assert decoded["email"] == "test@example.com"
        assert decoded["tenant_ids"] == ["tenant-1", "tenant-2"]
        assert decoded["iss"] == JWT_ISSUER
        assert "iat" in decoded
        assert "exp" in decoded

    def test_encode_user_token_expiry_time(self):
        """Test that user token has correct expiry time."""
        user_data = {
            "user_id": "user-123",
            "email": "test@example.com",
            "tenant_ids": ["tenant-1"]
        }

        before = int(datetime.now(UTC).timestamp())
        token = encode_user_token(user_data)
        after = int(datetime.now(UTC).timestamp())

        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Token should be issued between before and after (within 1 second window)
        assert before <= decoded["iat"] <= after + 1

        # Token should expire around 1 hour from issuance (default USER_TOKEN_EXPIRY)
        expected_exp = decoded["iat"] + 3600  # 1 hour default
        assert abs(decoded["exp"] - expected_exp) < 5  # Allow 5 second tolerance

    def test_encode_user_token_with_single_tenant(self):
        """Test encoding user token with single tenant (still array)."""
        user_data = {
            "user_id": "user-456",
            "email": "single@example.com",
            "tenant_ids": ["tenant-1"]
        }

        token = encode_user_token(user_data)
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        assert decoded["tenant_ids"] == ["tenant-1"]
        assert isinstance(decoded["tenant_ids"], list)


class TestTenantTokenEncoding:
    """Test tenant-scoped token (single tenant) encoding."""

    def test_encode_tenant_token_with_correct_claims(self):
        """Test tenant-scoped token encoding with single tenant_id and role."""
        # Arrange
        tenant_data = {
            "user_id": "user-123",
            "email": "test@example.com",
            "tenant_id": "tenant-1",
            "role": "viewer"
        }

        # Act
        token = encode_tenant_token(tenant_data)

        # Assert
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        assert decoded["sub"] == "user-123"
        assert decoded["email"] == "test@example.com"
        assert decoded["tenant_id"] == "tenant-1"  # Single value, not array
        assert decoded["role"] == "viewer"
        assert decoded["iss"] == JWT_ISSUER
        assert "iat" in decoded
        assert "exp" in decoded
        assert "tenant_ids" not in decoded  # Should NOT have array

    def test_encode_tenant_token_with_admin_role(self):
        """Test tenant-scoped token with admin role."""
        tenant_data = {
            "user_id": "user-456",
            "email": "admin@example.com",
            "tenant_id": "tenant-2",
            "role": "admin"
        }

        token = encode_tenant_token(tenant_data)
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        assert decoded["role"] == "admin"
        assert decoded["tenant_id"] == "tenant-2"

    def test_tenant_token_has_single_tenant_id(self):
        """Verify tenant-scoped token contains single tenant_id (not array)."""
        tenant_data = {
            "user_id": "user-789",
            "email": "test@example.com",
            "tenant_id": "tenant-3",
            "role": "viewer"
        }

        token = encode_tenant_token(tenant_data)
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Verify single tenant_id (string, not list)
        assert isinstance(decoded["tenant_id"], str)
        assert decoded["tenant_id"] == "tenant-3"

        # Verify no tenant_ids array
        assert "tenant_ids" not in decoded


class TestTokenDecoding:
    """Test JWT decoding and validation."""

    def test_decode_valid_user_token(self):
        """Test decoding and validating a valid user token."""
        user_data = {
            "user_id": "user-123",
            "email": "test@example.com",
            "tenant_ids": ["tenant-1", "tenant-2"]
        }

        token = encode_user_token(user_data)

        # Validate using the validation function
        validated = validate_user_token(token)

        assert validated.sub == "user-123"
        assert validated.email == "test@example.com"
        assert validated.tenant_ids == ["tenant-1", "tenant-2"]

    def test_decode_valid_tenant_token(self):
        """Test decoding and validating a valid tenant-scoped token."""
        tenant_data = {
            "user_id": "user-123",
            "email": "test@example.com",
            "tenant_id": "tenant-1",
            "role": "viewer"
        }

        token = encode_tenant_token(tenant_data)

        # Validate using the validation function
        validated = validate_tenant_token(token)

        assert validated.sub == "user-123"
        assert validated.email == "test@example.com"
        assert validated.tenant_id == "tenant-1"
        assert validated.role == "viewer"

    def test_expired_token_rejected(self):
        """Test that expired tokens are rejected."""
        # Create token with past expiry
        now = datetime.now(UTC)
        past_time = now - timedelta(hours=2)

        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "tenant_ids": ["tenant-1"],
            "iat": int(past_time.timestamp()),
            "exp": int((past_time + timedelta(hours=1)).timestamp()),  # Expired 1 hour ago
            "iss": JWT_ISSUER
        }

        expired_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        # Attempt to validate expired token
        with pytest.raises(ValueError) as exc_info:
            validate_user_token(expired_token)

        assert "expired" in str(exc_info.value).lower()

    def test_tampered_token_rejected(self):
        """Test that tampered tokens (invalid signature) are rejected."""
        # Create valid token
        user_data = {
            "user_id": "user-123",
            "email": "test@example.com",
            "tenant_ids": ["tenant-1"]
        }
        token = encode_user_token(user_data)

        # Tamper with the token signature
        tampered_token = token[:-10] + "TAMPERED12"

        # Attempt to validate tampered token
        with pytest.raises(ValueError) as exc_info:
            validate_user_token(tampered_token)

        assert "invalid" in str(exc_info.value).lower()

    def test_malformed_token_rejected(self):
        """Test that malformed tokens are rejected."""
        malformed_token = "not.a.valid.jwt.token"

        with pytest.raises(ValueError) as exc_info:
            validate_user_token(malformed_token)

        assert "invalid" in str(exc_info.value).lower()

    def test_token_with_wrong_secret_rejected(self):
        """Test that tokens signed with wrong secret are rejected."""
        # Create token with wrong secret
        wrong_secret = "wrong-secret-key-12345"
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "tenant_ids": ["tenant-1"],
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
            "iss": JWT_ISSUER
        }

        wrong_token = jwt.encode(payload, wrong_secret, algorithm=JWT_ALGORITHM)

        # Attempt to validate token signed with wrong secret
        with pytest.raises(ValueError) as exc_info:
            validate_user_token(wrong_token)

        assert "invalid" in str(exc_info.value).lower()


class TestTokenExpiryEdgeCases:
    """Test edge cases around token expiry."""

    def test_token_at_exact_expiry_time(self):
        """Test token validation at exact expiry time."""
        # Create token that expires in 1 second
        now = datetime.now(UTC)
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "tenant_ids": ["tenant-1"],
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=1)).timestamp()),
            "iss": JWT_ISSUER
        }

        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        # Should be valid immediately
        validated = validate_user_token(token)
        assert validated.sub == "user-123"

        # Wait for expiry
        time.sleep(2)

        # Should now be expired
        with pytest.raises(ValueError) as exc_info:
            validate_user_token(token)

        assert "expired" in str(exc_info.value).lower()

    def test_token_issued_in_future_rejected(self):
        """Test that tokens with future iat are rejected."""
        # Create token issued 1 hour in the future
        now = datetime.now(UTC)
        future_time = now + timedelta(hours=1)

        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "tenant_ids": ["tenant-1"],
            "iat": int(future_time.timestamp()),
            "exp": int((future_time + timedelta(hours=1)).timestamp()),
            "iss": JWT_ISSUER
        }

        future_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        # Should be rejected (iat verification enabled)
        with pytest.raises(ValueError):
            validate_user_token(future_token)
