"""
Shared Configuration Package

Provides shared JWT configuration, validation, and mock data
for all Kyros SaaS PoC services (FastAPI, Dash apps).

Usage:
    from shared_config import JWT_SECRET_KEY, validate_tenant_token
    from shared_config.models import TenantScopedToken
"""

# Configuration constants
from .config import (
    JWT_ALGORITHM,
    JWT_ISSUER,
    JWT_SECRET_KEY,
    TENANT_TOKEN_EXPIRY,
    USER_TOKEN_EXPIRY,
)

# JWT utilities
from .jwt_utils import (
    encode_tenant_token,
    encode_user_token,
    validate_tenant_token,
    validate_user_token,
)

# Mock user data
from .mock_users import (
    MOCK_TOKENS,
    MOCK_USERS,
    get_user_by_email,
    get_user_token,
    validate_password,
)

# Pydantic models
from .models import (
    TenantScopedToken,
    UserAccessToken,
)

__version__ = "0.1.0"

__all__ = [
    # Configuration
    "JWT_SECRET_KEY",
    "JWT_ALGORITHM",
    "JWT_ISSUER",
    "USER_TOKEN_EXPIRY",
    "TENANT_TOKEN_EXPIRY",
    # Models
    "UserAccessToken",
    "TenantScopedToken",
    # JWT utilities
    "encode_user_token",
    "encode_tenant_token",
    "validate_user_token",
    "validate_tenant_token",
    # Mock data
    "MOCK_USERS",
    "MOCK_TOKENS",
    "get_user_by_email",
    "get_user_token",
    "validate_password",
]
