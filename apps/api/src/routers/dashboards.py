"""Dashboard data API endpoints."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends

from ..middleware.auth import get_current_tenant
from ..data.data_loader import load_tenant_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboards", tags=["Dashboards"])


async def get_tenant_from_token(
    tenant_context: Dict[str, Any] = Depends(get_current_tenant)
) -> str:
    """
    Extract tenant_id from validated tenant-scoped JWT.

    Args:
        tenant_context: Validated tenant JWT claims from get_current_tenant

    Returns:
        str: tenant_id from JWT claims
    """
    return tenant_context.get("tenant_id")


@router.get(
    "/{slug}/data",
    status_code=status.HTTP_200_OK,
    summary="Get tenant-scoped dashboard data",
    description="""
    Returns data for a specific dashboard, filtered by the tenant_id in the JWT token.

    **Authentication Required:** Bearer token (tenant-scoped token from /api/token/exchange)

    **Flow:**
    1. User exchanges user token for tenant-scoped token
    2. User includes tenant-scoped token in Authorization header
    3. Endpoint validates token and extracts tenant_id
    4. Data is loaded from CSV and filtered by tenant_id
    5. Tenant-filtered records returned as JSON array

    **Security:**
    - Requires valid tenant-scoped JWT (30-minute lifetime)
    - Data automatically filtered by tenant_id from token
    - No ability to access other tenants' data
    - All data access logged for audit trail

    **Error Responses:**
    - 401: Invalid/expired/missing token
    - 404: Dashboard not found or no data for tenant
    - 500: Server error (data loading failure)

    **Dashboard Slugs:**
    - `customer-lifetime-value`: CLV metrics (Acme only)
    - `risk-analysis`: Risk metrics (Acme + Beta)
    """
)
async def get_dashboard_data(
    slug: str,
    tenant_id: str = Depends(get_tenant_from_token)
) -> Dict[str, Any]:
    """
    Get tenant-scoped data for a dashboard.

    Args:
        slug: Dashboard slug (e.g., 'customer-lifetime-value', 'risk-analysis')
        tenant_id: Tenant UUID from validated JWT (injected by dependency)

    Returns:
        Dict containing:
        - tenant_id (str): Tenant UUID
        - dashboard_slug (str): Dashboard identifier
        - data (list[dict]): Array of records (tenant-filtered)

    Raises:
        HTTPException: 401 if token invalid (handled by middleware)
        HTTPException: 404 if dashboard not found or no data for tenant
    """
    logger.info(f"Data request: tenant={tenant_id}, dashboard={slug}")

    # Load tenant-filtered data
    df = load_tenant_data(tenant_id, slug)

    if df is None or df.empty:
        logger.warning(f"No data found: tenant={tenant_id}, dashboard={slug}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "DATA_NOT_FOUND",
                    "message": f"No data available for dashboard {slug}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )

    # Convert to records (list of dicts)
    records = df.to_dict('records')

    logger.info(
        f"Returning {len(records)} records for {slug}",
        extra={
            "tenant_id": tenant_id,
            "dashboard_slug": slug,
            "record_count": len(records),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    return {
        "tenant_id": tenant_id,
        "dashboard_slug": slug,
        "data": records
    }
