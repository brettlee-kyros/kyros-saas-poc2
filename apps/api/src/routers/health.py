"""Health check endpoints."""
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..database import get_db_connection

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.

    Returns:
        dict: Status and timestamp
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/health/db")
async def database_health_check():
    """
    Database health check endpoint.

    Returns:
        dict: Database status and tenant count
    """
    try:
        async with get_db_connection() as db:
            cursor = await db.execute("SELECT COUNT(*) FROM tenants")
            tenant_count = (await cursor.fetchone())[0]

        return {
            "status": "ok",
            "database": "connected",
            "tenant_count": tenant_count,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "Database connection failed",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
        ) from e
