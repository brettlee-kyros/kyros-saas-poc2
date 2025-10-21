"""User profile and tenant discovery endpoints."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends

from ..middleware.auth import get_current_user
from ..models.tenant import UserInfoResponse, TenantInfo
from ..database.connection import get_db_connection
from ..database.queries import get_user_by_id, get_user_tenants

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get(
    "/me",
    response_model=UserInfoResponse,
    status_code=status.HTTP_200_OK,
    tags=["User"],
    summary="Get current user profile and available tenants",
    description="""
    Returns the authenticated user's profile and list of accessible tenants.

    **Authentication Required:** Bearer token (user access token from /api/auth/mock-login)

    This endpoint:
    - Validates JWT user access token from Authorization header
    - Retrieves user profile from database
    - Queries active tenants the user has access to
    - Returns tenant list with role information for each tenant

    The tenant list enables the Shell UI to display available tenants for selection.
    Tenants are sorted alphabetically by name.

    **Authorization Header Format:**
    ```
    Authorization: Bearer <user_access_token>
    ```

    **Response includes:**
    - user_id: User UUID
    - email: User email address
    - tenants: Array of tenant objects with id, name, slug, role, config_json

    **Roles:**
    - admin: Full access to tenant resources
    - viewer: Read-only access to tenant resources
    """
)
async def get_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserInfoResponse:
    """
    Get current user profile and list of accessible tenants.

    Requires valid user access token in Authorization header.
    Validates token and returns user profile with tenant list.

    Args:
        current_user: Validated JWT claims from get_current_user middleware

    Returns:
        UserInfoResponse with user_id, email, and tenants array

    Raises:
        HTTPException: 404 if user_id from token not found in database
        HTTPException: 401 if token is invalid (handled by middleware)
    """
    # Extract user data from validated JWT claims
    user_id = current_user.get("sub")
    email = current_user.get("email")
    tenant_ids = current_user.get("tenant_ids", [])

    logger.debug(
        f"User info request for user_id={user_id}, email={email}, "
        f"tenant_ids={len(tenant_ids)}"
    )

    # Query database for user record
    async with get_db_connection() as db:
        # Verify user exists in database
        user = await get_user_by_id(db, user_id)

        if not user:
            logger.warning(
                "User not found in database",
                extra={
                    "user_id": user_id,
                    "email": email,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "message": f"User {user_id} not found",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "request_id": str(uuid.uuid4())
                    }
                }
            )

        # Query tenants the user has access to
        tenant_data = await get_user_tenants(db, user_id, tenant_ids)

    # Transform tenant data into Pydantic models
    tenants = [
        TenantInfo(
            tenant_id=t["id"],
            name=t["name"],
            slug=t["slug"],
            role=t["role"],
            config_json=t["config_json"]
        )
        for t in tenant_data
    ]

    logger.info(
        "User info request successful",
        extra={
            "user_id": user_id,
            "email": email,
            "tenant_count": len(tenants),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    return UserInfoResponse(
        user_id=user_id,
        email=email,
        tenants=tenants
    )
