"""
Unit tests for JWT utility functions
"""


import pytest

from shared_config import (
    encode_tenant_token,
    encode_user_token,
    validate_tenant_token,
    validate_user_token,
)


def test_user_token_encode_decode():
    """Test user token encoding and decoding round-trip."""
    user_data = {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "tenant_ids": ["tenant-1", "tenant-2"]
    }

    token = encode_user_token(user_data)
    assert isinstance(token, str)
    assert len(token) > 0

    decoded = validate_user_token(token)
    assert decoded.sub == "test-user-123"
    assert decoded.email == "test@example.com"
    assert len(decoded.tenant_ids) == 2


def test_tenant_token_encode_decode():
    """Test tenant token encoding and decoding round-trip."""
    tenant_data = {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "tenant_id": "tenant-1",
        "role": "admin"
    }

    token = encode_tenant_token(tenant_data)
    assert isinstance(token, str)

    decoded = validate_tenant_token(token)
    assert decoded.sub == "test-user-123"
    assert decoded.tenant_id == "tenant-1"
    assert decoded.role == "admin"


def test_invalid_token():
    """Test that invalid tokens are rejected."""
    with pytest.raises(ValueError, match="Invalid token"):
        validate_user_token("invalid-token-string")


def test_token_with_wrong_secret():
    """Test that tokens with wrong signature are rejected."""
    import jwt

    from shared_config.config import JWT_ALGORITHM

    # Create token with different secret
    payload = {"sub": "test", "email": "test@example.com", "tenant_ids": []}
    wrong_token = jwt.encode(payload, "wrong-secret", algorithm=JWT_ALGORITHM)

    with pytest.raises(ValueError, match="Invalid token"):
        validate_user_token(wrong_token)
