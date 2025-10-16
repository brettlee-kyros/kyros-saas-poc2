"""Unit tests for tenant-scoped JWT validation middleware."""
import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch

from src.middleware.auth import get_current_tenant, validate_tenant_access


@pytest.mark.asyncio
async def test_get_current_tenant_with_valid_token():
    """Test tenant token validation with valid tenant-scoped token."""
    # Mock HTTPAuthorizationCredentials
    from unittest.mock import Mock
    mock_credentials = Mock()
    mock_credentials.credentials = "valid-tenant-token"

    # Mock validate_tenant_token to return valid claims
    with patch('src.middleware.auth.validate_tenant_token') as mock_validate:
        mock_token = Mock()
        mock_token.model_dump.return_value = {
            "sub": "user-uuid-123",
            "email": "analyst@acme.com",
            "tenant_id": "acme-uuid",
            "role": "viewer",
            "iat": int(datetime.now().timestamp()),
            "exp": int((datetime.now() + timedelta(minutes=30)).timestamp())
        }
        mock_validate.return_value = mock_token

        # Call dependency
        result = await get_current_tenant(mock_credentials)

        # Verify claims returned
        assert result["sub"] == "user-uuid-123"
        assert result["email"] == "analyst@acme.com"
        assert result["tenant_id"] == "acme-uuid"
        assert result["role"] == "viewer"
        assert "iat" in result
        assert "exp" in result


@pytest.mark.asyncio
async def test_get_current_tenant_with_expired_token():
    """Test that expired tenant token returns 401."""
    from unittest.mock import Mock
    mock_credentials = Mock()
    mock_credentials.credentials = "expired-token"

    with patch('src.middleware.auth.validate_tenant_token') as mock_validate:
        mock_validate.side_effect = Exception("Token has expired")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_tenant(mock_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "INVALID_TENANT_TOKEN"


@pytest.mark.asyncio
async def test_get_current_tenant_with_invalid_signature():
    """Test that token with invalid signature returns 401."""
    from unittest.mock import Mock
    mock_credentials = Mock()
    mock_credentials.credentials = "bad-signature-token"

    with patch('src.middleware.auth.validate_tenant_token') as mock_validate:
        mock_validate.side_effect = Exception("Invalid token signature")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_tenant(mock_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "INVALID_TENANT_TOKEN"
        assert "Invalid or expired tenant token" in exc_info.value.detail["error"]["message"]


@pytest.mark.asyncio
async def test_get_current_tenant_with_missing_token():
    """Test that missing token returns 401."""
    from unittest.mock import Mock
    mock_credentials = Mock()
    mock_credentials.credentials = None

    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant(mock_credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["error"]["code"] == "MISSING_TOKEN"


@pytest.mark.asyncio
async def test_validate_tenant_access_with_matching_tenant_id():
    """Test that matching tenant_id in token and path succeeds."""
    tenant_context = {
        "sub": "user-uuid",
        "tenant_id": "acme-uuid",
        "role": "viewer"
    }

    # Should not raise exception
    await validate_tenant_access("acme-uuid", tenant_context)


@pytest.mark.asyncio
async def test_validate_tenant_access_with_mismatched_tenant_id():
    """Test that mismatched tenant_id returns 403 TENANT_MISMATCH."""
    tenant_context = {
        "sub": "user-uuid",
        "tenant_id": "acme-uuid",
        "role": "viewer"
    }

    with pytest.raises(HTTPException) as exc_info:
        await validate_tenant_access("beta-uuid", tenant_context)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["error"]["code"] == "TENANT_MISMATCH"
    assert "acme-uuid" in exc_info.value.detail["error"]["message"]
    assert "beta-uuid" in exc_info.value.detail["error"]["message"]
    assert "request_id" in exc_info.value.detail["error"]
    assert "timestamp" in exc_info.value.detail["error"]


@pytest.mark.asyncio
async def test_validate_tenant_access_error_format():
    """Test that 403 error response matches standard format."""
    tenant_context = {
        "sub": "user-123",
        "tenant_id": "tenant-a",
        "role": "admin"
    }

    with pytest.raises(HTTPException) as exc_info:
        await validate_tenant_access("tenant-b", tenant_context)

    # Verify standard error format
    error = exc_info.value.detail["error"]
    assert "code" in error
    assert "message" in error
    assert "timestamp" in error
    assert "request_id" in error
    assert error["code"] == "TENANT_MISMATCH"
