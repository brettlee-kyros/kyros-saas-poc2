"""Authentication endpoints for mock login."""
import logging
import sys
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

# Add shared_config to path
sys.path.insert(0, '/app/packages/shared-config/src')

try:
    from shared_config import get_user_by_email, encode_user_token
    SHARED_CONFIG_AVAILABLE = True
except ImportError:
    SHARED_CONFIG_AVAILABLE = False
    logging.warning("shared_config not available")

from ..models.tokens import MockLoginRequest, TokenResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth")


@router.post(
    "/mock-login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    tags=["Mock Auth"],
    summary="Mock login endpoint (PoC only)",
    description="""
    Returns a pre-generated user access token for testing.

    ⚠️ **NOT FOR PRODUCTION** - Replace with Azure AD B2C OIDC flow in MVP.

    This endpoint:
    - Looks up user by email in mock data
    - Generates a JWT user access token with tenant_ids array
    - Returns token with 1-hour expiration

    Mock users available:
    - analyst@acme.com (Acme Corporation - Viewer)
    - admin@acme.com (Acme + Beta Industries - Admin)
    - viewer@beta.com (Beta Industries - Viewer)
    """
)
async def mock_login(request: MockLoginRequest) -> TokenResponse:
    """
    Mock login endpoint that generates user access tokens.

    Args:
        request: MockLoginRequest containing email

    Returns:
        TokenResponse with access_token, token_type, and expires_in

    Raises:
        HTTPException: 404 if user not found, 500 if shared_config unavailable
    """
    if not SHARED_CONFIG_AVAILABLE:
        logger.error("Mock login failed - shared_config not available")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "CONFIG_UNAVAILABLE",
                    "message": "Shared configuration module not available",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )

    email = request.email

    # Look up user in mock data
    user = get_user_by_email(email)

    if not user:
        logger.warning(
            "Authentication failed - user not found",
            extra={"email": email, "success": False, "timestamp": datetime.now(timezone.utc).isoformat()}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": f"User with email {email} not found",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )

    # Extract user data
    user_id = user.get("user_id")
    tenant_ids = user.get("tenant_ids", [])

    # Generate user access token
    access_token = encode_user_token({
        "user_id": user_id,
        "email": email,
        "tenant_ids": tenant_ids
    })

    logger.info(
        "Authentication successful",
        extra={
            "email": email,
            "user_id": user_id,
            "tenant_count": len(tenant_ids),
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=3600  # 1 hour
    )
