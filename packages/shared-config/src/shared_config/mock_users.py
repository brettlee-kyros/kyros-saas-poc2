"""
Mock User Data for PoC

Pre-configured mock users with tenant mappings.
These MUST match the database seed data in Story 1.3.

⚠️ PoC ONLY: Real applications use proper authentication (Azure AD B2C, etc.)
"""

from typing import Any

from .jwt_utils import encode_user_token

# Mock user database
# UUIDs and mappings MUST match database/schema.sql seed data
MOCK_USERS: dict[str, dict[str, Any]] = {
    "analyst@acme.com": {
        "user_id": "f8d1e2c3-4b5a-6789-abcd-ef1234567890",
        "email": "analyst@acme.com",
        "password": "demo123",  # ⚠️ PoC only - plaintext password
        "tenant_ids": [
            "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"  # Acme Corporation
        ],
        "roles": {
            "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345": "viewer"
        }
    },
    "admin@acme.com": {
        "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "email": "admin@acme.com",
        "password": "demo123",
        "tenant_ids": [
            "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",  # Acme Corporation
            "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4"   # Beta Industries
        ],
        "roles": {
            "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345": "admin",
            "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4": "admin"
        }
    },
    "viewer@beta.com": {
        "user_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "email": "viewer@beta.com",
        "password": "demo123",
        "tenant_ids": [
            "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4"   # Beta Industries
        ],
        "roles": {
            "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4": "viewer"
        }
    }
}

# Pre-generated tokens for quick testing
# These are generated at module load time
MOCK_TOKENS: dict[str, str] = {}


def _generate_mock_tokens() -> None:
    """Generate pre-encoded tokens for all mock users."""
    for email, user_data in MOCK_USERS.items():
        MOCK_TOKENS[email] = encode_user_token(user_data)


# Generate tokens on module import
_generate_mock_tokens()


def get_user_by_email(email: str) -> dict[str, Any] | None:
    """
    Look up mock user by email.

    Args:
        email: User email address

    Returns:
        User data dict or None if not found
    """
    return MOCK_USERS.get(email)


def get_user_token(email: str) -> str | None:
    """
    Get pre-generated token for mock user.

    Args:
        email: User email address

    Returns:
        JWT token string or None if user not found
    """
    return MOCK_TOKENS.get(email)


def validate_password(email: str, password: str) -> bool:
    """
    Validate mock user password (PoC only).

    ⚠️ NEVER use plaintext password comparison in production!

    Args:
        email: User email
        password: Password to validate

    Returns:
        True if password matches, False otherwise
    """
    user = get_user_by_email(email)
    if not user:
        return False
    return user.get("password") == password
