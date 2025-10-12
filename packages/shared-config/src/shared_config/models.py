"""
Pydantic Models for JWT Tokens

Defines typed models for user access tokens and tenant-scoped tokens
used throughout the authentication flow.
"""

from typing import Literal

from pydantic import BaseModel, Field


class UserAccessToken(BaseModel):
    """
    Multi-tenant user access token.

    Issued by mock auth endpoint after user login.
    Contains array of all tenant IDs the user can access.
    """
    sub: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email address")
    tenant_ids: list[str] = Field(..., description="Array of tenant UUIDs user can access")
    iat: int = Field(..., description="Issued at timestamp (Unix epoch)")
    exp: int = Field(..., description="Expiration timestamp (Unix epoch)")

    class Config:
        json_schema_extra = {
            "example": {
                "sub": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "email": "admin@acme.com",
                "tenant_ids": [
                    "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
                    "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4"
                ],
                "iat": 1697654400,
                "exp": 1697658000
            }
        }


class TenantScopedToken(BaseModel):
    """
    Single-tenant scoped token.

    Issued by token exchange endpoint after user selects a tenant.
    Short-lived (15-30 min) and restricted to single tenant context.
    """
    sub: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email address")
    tenant_id: str = Field(..., description="Single tenant UUID (active tenant)")
    role: Literal["admin", "viewer"] = Field(..., description="User role for this tenant")
    iat: int = Field(..., description="Issued at timestamp (Unix epoch)")
    exp: int = Field(..., description="Expiration timestamp (Unix epoch)")

    class Config:
        json_schema_extra = {
            "example": {
                "sub": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "email": "admin@acme.com",
                "tenant_id": "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345",
                "role": "admin",
                "iat": 1697654400,
                "exp": 1697656200
            }
        }
