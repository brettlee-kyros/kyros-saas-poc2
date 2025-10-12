"""Token exchange endpoints for tenant scoping."""
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends

# Add shared_config to path
sys.path.insert(0, '/app/packages/shared-config/src')

try:
    from shared_config import encode_tenant_token, TENANT_TOKEN_EXPIRY
    SHARED_CONFIG_AVAILABLE = True
except ImportError:
    SHARED_CONFIG_AVAILABLE = False
    logging.warning("shared_config not available for token exchange")

from ..middleware.auth import get_current_user
from ..models.tokens import TokenExchangeRequest, TokenResponse
from ..database.connection import get_db_connection
from ..database.queries import get_user_tenant_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/token")


@router.post(
    "/exchange",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    tags=["Token Exchange"],
    summary="Exchange user token for tenant-scoped token",
    description="""
    Exchanges a multi-tenant user access token for a single-tenant scoped token.

    **This is the core PoC validation mechanism** - converting user tokens with multiple
    tenant_ids into a short-lived token scoped to a single tenant for hard data isolation.

    **Authentication Required:** Bearer token (user access token from /api/auth/mock-login)

    **Flow:**
    1. User logs in → receives user access token with tenant_ids array
    2. User selects tenant from /api/me list
    3. User exchanges token for that tenant → receives tenant-scoped token
    4. User accesses tenant-specific resources with tenant-scoped token

    **Token Differences:**
    - Input (user token): Contains tenant_ids array, 1-hour lifetime
    - Output (tenant token): Contains single tenant_id + role, 30-minute lifetime

    **Security:**
    - User must have access to requested tenant (validated against JWT tenant_ids)
    - Role fetched from database user_tenants table (not from JWT claims)
    - Short token lifetime (30 min) reduces exposure window
    - All exchange attempts logged for audit trail

    **Error Responses:**
    - 400: Missing tenant_id in request
    - 401: Invalid/expired user token
    - 403: User does not have access to requested tenant
    - 500: Server error (database, config unavailable)
    """
)
async def exchange_token(
    request: TokenExchangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> TokenResponse:
    """
    Exchange user access token for tenant-scoped token.

    Validates that user has access to requested tenant, queries their role,
    and generates a short-lived tenant-scoped JWT.

    Args:
        request: TokenExchangeRequest with tenant_id
        current_user: Validated user JWT claims from middleware

    Returns:
        TokenResponse with tenant-scoped access_token, token_type, expires_in

    Raises:
        HTTPException: 400 if tenant_id missing
        HTTPException: 401 if user token invalid (handled by middleware)
        HTTPException: 403 if user lacks access to tenant
        HTTPException: 500 if config unavailable or database error
    """
    if not SHARED_CONFIG_AVAILABLE:
        logger.error("Token exchange failed - shared_config not available")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "CONFIG_UNAVAILABLE",
                    "message": "Token exchange service unavailable",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )

    # Extract user data from validated JWT claims
    user_id = current_user.get("sub")
    email = current_user.get("email")
    user_tenant_ids = current_user.get("tenant_ids", [])
    requested_tenant_id = request.tenant_id

    logger.debug(
        f"Token exchange request: user_id={user_id}, email={email}, "
        f"requested_tenant={requested_tenant_id}, user_tenants={len(user_tenant_ids)}"
    )

    # Validate tenant_id is present
    if not requested_tenant_id:
        logger.warning(
            "Token exchange failed - missing tenant_id",
            extra={
                "user_id": user_id,
                "email": email,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "tenant_id is required",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )

    # Validate user has access to requested tenant
    if requested_tenant_id not in user_tenant_ids:
        logger.warning(
            "Token exchange denied - unauthorized tenant",
            extra={
                "user_id": user_id,
                "email": email,
                "requested_tenant_id": requested_tenant_id,
                "user_tenant_ids": user_tenant_ids,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "TENANT_ACCESS_DENIED",
                    "message": f"User does not have access to tenant {requested_tenant_id}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )

    # Query user's role for the tenant
    try:
        async with get_db_connection() as db:
            role = await get_user_tenant_role(db, user_id, requested_tenant_id)

        if not role:
            # This should not happen if validation passed, but handle gracefully
            logger.error(
                "Token exchange failed - role not found",
                extra={
                    "user_id": user_id,
                    "tenant_id": requested_tenant_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "ROLE_NOT_FOUND",
                        "message": "User role not found for tenant",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "request_id": str(uuid.uuid4())
                    }
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Token exchange failed - database error: {str(e)}",
            extra={
                "user_id": user_id,
                "tenant_id": requested_tenant_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "DATABASE_ERROR",
                    "message": "Failed to retrieve user role",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )

    # Generate tenant-scoped JWT
    tenant_token = encode_tenant_token({
        "user_id": user_id,
        "email": email,
        "tenant_id": requested_tenant_id,
        "role": role
    })

    logger.info(
        "Token exchange successful",
        extra={
            "user_id": user_id,
            "email": email,
            "tenant_id": requested_tenant_id,
            "role": role,
            "token_expires_in": TENANT_TOKEN_EXPIRY,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    return TokenResponse(
        access_token=tenant_token,
        token_type="Bearer",
        expires_in=TENANT_TOKEN_EXPIRY  # 1800 seconds (30 minutes)
    )
