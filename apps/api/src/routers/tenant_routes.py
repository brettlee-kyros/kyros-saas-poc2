"""Tenant metadata and dashboard endpoints."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, status, Depends

from ..middleware.auth import get_current_tenant, validate_tenant_access
from ..models.tenant import TenantMetadata, DashboardInfo
from ..database.connection import get_db_connection
from ..database.queries import get_tenant_by_id, get_tenant_dashboards

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tenant")


@router.get(
    "/{tenant_id}",
    response_model=TenantMetadata,
    status_code=status.HTTP_200_OK,
    tags=["Tenant"],
    summary="Get tenant metadata and configuration",
    description="""
    Returns tenant metadata including branding, feature flags, and configuration.

    **Authentication Required:** Bearer token (tenant-scoped token from /api/token/exchange)

    **Tenant Isolation:** Token tenant_id must match path parameter tenant_id.
    This prevents users from accessing configuration for other tenants.

    **Response includes:**
    - id: Tenant UUID
    - name: Tenant display name
    - slug: URL-safe identifier
    - is_active: Whether tenant is active (1) or disabled (0)
    - config_json: Tenant-specific configuration (branding, features, etc.)
    - created_at: ISO 8601 timestamp

    **Error Responses:**
    - 401: Invalid/expired tenant token
    - 403: Token tenant_id doesn't match path parameter
    - 404: Tenant not found
    """
)
async def get_tenant_metadata(
    tenant_id: str,
    tenant_context: Dict[str, Any] = Depends(get_current_tenant),
    _: None = Depends(validate_tenant_access)
) -> TenantMetadata:
    """
    Get tenant metadata and configuration.

    Args:
        tenant_id: Tenant UUID from path parameter
        tenant_context: Validated tenant JWT claims
        _: Tenant access validation (ensures token matches path)

    Returns:
        TenantMetadata with full tenant configuration

    Raises:
        HTTPException: 404 if tenant not found
        HTTPException: 403 if tenant_id mismatch (handled by validate_tenant_access)
    """
    user_id = tenant_context.get("sub")

    logger.debug(f"Tenant metadata request: tenant_id={tenant_id}, user_id={user_id}")

    # Query database for tenant
    async with get_db_connection() as db:
        tenant = await get_tenant_by_id(db, tenant_id)

    if not tenant:
        logger.warning(
            "Tenant not found",
            extra={
                "tenant_id": tenant_id,
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TENANT_NOT_FOUND",
                    "message": f"Tenant {tenant_id} not found",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )

    logger.info(
        "Tenant metadata retrieved",
        extra={
            "tenant_id": tenant_id,
            "user_id": user_id,
            "tenant_name": tenant["name"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    return TenantMetadata(**tenant)


@router.get(
    "/{tenant_id}/dashboards",
    response_model=List[DashboardInfo],
    status_code=status.HTTP_200_OK,
    tags=["Tenant"],
    summary="Get tenant's assigned dashboards",
    description="""
    Returns list of dashboards assigned to the tenant.

    **Authentication Required:** Bearer token (tenant-scoped token)

    **Tenant Isolation:** Token tenant_id must match path parameter tenant_id.

    **Response:**
    Array of dashboard objects sorted alphabetically by title.
    Returns empty array if no dashboards assigned (not an error).

    **Dashboard fields:**
    - slug: URL-safe dashboard identifier
    - title: Display name
    - description: Dashboard description
    - config_json: Dashboard-specific configuration

    **Error Responses:**
    - 401: Invalid/expired tenant token
    - 403: Token tenant_id doesn't match path parameter
    """
)
async def get_tenant_dashboards_list(
    tenant_id: str,
    tenant_context: Dict[str, Any] = Depends(get_current_tenant),
    _: None = Depends(validate_tenant_access)
) -> List[DashboardInfo]:
    """
    Get list of dashboards assigned to tenant.

    Args:
        tenant_id: Tenant UUID from path parameter
        tenant_context: Validated tenant JWT claims
        _: Tenant access validation

    Returns:
        List of DashboardInfo objects sorted by title

    Raises:
        HTTPException: 403 if tenant_id mismatch (handled by validate_tenant_access)
    """
    user_id = tenant_context.get("sub")

    logger.debug(f"Tenant dashboards request: tenant_id={tenant_id}, user_id={user_id}")

    # Query database for tenant's dashboards
    async with get_db_connection() as db:
        dashboards = await get_tenant_dashboards(db, tenant_id)

    logger.info(
        "Tenant dashboards retrieved",
        extra={
            "tenant_id": tenant_id,
            "user_id": user_id,
            "dashboard_count": len(dashboards),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    return [DashboardInfo(**d) for d in dashboards]
