"""Token-related Pydantic models."""
from pydantic import BaseModel, EmailStr


class MockLoginRequest(BaseModel):
    """Request model for mock login endpoint."""
    email: EmailStr


class TokenResponse(BaseModel):
    """Response model for token endpoints."""
    access_token: str
    token_type: str
    expires_in: int


class TokenExchangeRequest(BaseModel):
    """Request model for token exchange endpoint."""
    tenant_id: str
