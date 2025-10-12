"""
JWT Utility Functions

Provides token encoding, decoding, and validation functions
shared across all Python applications (FastAPI, Dash apps).
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from .config import JWT_ALGORITHM, JWT_ISSUER, JWT_SECRET_KEY, TENANT_TOKEN_EXPIRY, USER_TOKEN_EXPIRY
from .models import TenantScopedToken, UserAccessToken


def encode_user_token(user_data: dict[str, Any]) -> str:
    """
    Encode a user access token (multi-tenant).

    Args:
        user_data: Dictionary containing user_id, email, tenant_ids

    Returns:
        str: Encoded JWT token

    Example:
        >>> token = encode_user_token({
        ...     "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        ...     "email": "admin@acme.com",
        ...     "tenant_ids": ["8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"]
        ... })
    """
    now = datetime.now(UTC)
    payload = {
        "sub": user_data["user_id"],
        "email": user_data["email"],
        "tenant_ids": user_data["tenant_ids"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=USER_TOKEN_EXPIRY)).timestamp()),
        "iss": JWT_ISSUER
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def encode_tenant_token(tenant_data: dict[str, Any]) -> str:
    """
    Encode a tenant-scoped token (single tenant).

    Args:
        tenant_data: Dictionary containing user_id, email, tenant_id, role

    Returns:
        str: Encoded JWT token

    Example:
        >>> token = encode_tenant_token({
        ...     "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        ...     "email": "admin@acme.com",
        ...     "tenant_id": "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
        ...     "role": "admin"
        ... })
    """
    now = datetime.now(UTC)
    payload = {
        "sub": tenant_data["user_id"],
        "email": tenant_data["email"],
        "tenant_id": tenant_data["tenant_id"],
        "role": tenant_data["role"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=TENANT_TOKEN_EXPIRY)).timestamp()),
        "iss": JWT_ISSUER
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def validate_user_token(token: str) -> UserAccessToken:
    """
    Decode and validate a user access token.

    Args:
        token: JWT token string

    Returns:
        UserAccessToken: Validated token data

    Raises:
        ValueError: If token is expired, invalid, or has wrong structure
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": True, "verify_iat": True}
        )
        return UserAccessToken(**payload)
    except jwt.ExpiredSignatureError as e:
        raise ValueError("Token has expired") from e
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}") from e
    except Exception as e:
        raise ValueError(f"Token validation error: {str(e)}") from e


def validate_tenant_token(token: str) -> TenantScopedToken:
    """
    Decode and validate a tenant-scoped token.

    Args:
        token: JWT token string

    Returns:
        TenantScopedToken: Validated token data

    Raises:
        ValueError: If token is expired, invalid, or has wrong structure
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": True, "verify_iat": True}
        )
        return TenantScopedToken(**payload)
    except jwt.ExpiredSignatureError as e:
        raise ValueError("Token has expired") from e
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}") from e
    except Exception as e:
        raise ValueError(f"Token validation error: {str(e)}") from e
