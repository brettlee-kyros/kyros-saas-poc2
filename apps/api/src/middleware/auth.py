"""JWT authentication middleware for FastAPI."""
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Add shared_config to path
sys.path.insert(0, '/app/packages/shared-config/src')

try:
    from shared_config import validate_user_token, validate_tenant_token
    SHARED_CONFIG_AVAILABLE = True
except ImportError:
    SHARED_CONFIG_AVAILABLE = False
    logging.warning("shared_config not available for JWT validation")

logger = logging.getLogger(__name__)

# HTTPBearer security scheme for extracting JWT from Authorization header
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency that validates JWT user access token.

    Extracts JWT from Authorization header (Bearer token), validates signature
    and expiration, and returns decoded claims.

    Args:
        credentials: HTTPAuthorizationCredentials from HTTPBearer security scheme

    Returns:
        Dict containing validated JWT claims:
        - user_id (str): User UUID
        - email (str): User email address
        - tenant_ids (list[str]): Array of tenant UUIDs user has access to
        - iat (int): Issued at timestamp
        - exp (int): Expiration timestamp
        - iss (str): Issuer

    Raises:
        HTTPException: 401 if token is invalid, expired, or missing
        HTTPException: 500 if shared_config unavailable
    """
    if not SHARED_CONFIG_AVAILABLE:
        logger.error("JWT validation failed - shared_config not available")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "CONFIG_UNAVAILABLE",
                    "message": "Authentication service unavailable",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )

    # Extract token from Authorization header
    token = credentials.credentials

    if not token:
        logger.warning("Authentication failed - no token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "MISSING_TOKEN",
                    "message": "Authorization token is required",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            },
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Validate token and decode claims (returns UserAccessToken Pydantic model)
        user_token = validate_user_token(token)

        # Convert Pydantic model to dict for FastAPI dependency injection
        claims = user_token.model_dump()

        logger.info(
            "JWT validation successful",
            extra={
                "user_id": claims.get("sub"),
                "email": claims.get("email"),
                "tenant_count": len(claims.get("tenant_ids", [])),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

        return claims

    except Exception as e:
        # Handle token validation errors (expired, invalid signature, malformed)
        error_message = str(e)
        logger.warning(
            "JWT validation failed",
            extra={
                "error": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": f"Invalid or expired token: {error_message}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            },
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency that validates JWT tenant-scoped token.

    Extracts JWT from Authorization header (Bearer token), validates signature
    and expiration using tenant token validation, and returns decoded claims.

    Args:
        credentials: HTTPAuthorizationCredentials from HTTPBearer security scheme

    Returns:
        Dict containing validated JWT claims:
        - sub (str): User UUID
        - email (str): User email address
        - tenant_id (str): Single tenant UUID (not array)
        - role (str): User's role for this tenant
        - iat (int): Issued at timestamp
        - exp (int): Expiration timestamp
        - iss (str): Issuer

    Raises:
        HTTPException: 401 if token is invalid, expired, or missing
        HTTPException: 500 if shared_config unavailable
    """
    if not SHARED_CONFIG_AVAILABLE:
        logger.error("Tenant token validation failed - shared_config not available")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "CONFIG_UNAVAILABLE",
                    "message": "Authentication service unavailable",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )

    # Extract token from Authorization header
    token = credentials.credentials

    if not token:
        logger.warning("Tenant authentication failed - no token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "MISSING_TOKEN",
                    "message": "Authorization token is required",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            },
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Validate tenant-scoped token (returns TenantScopedToken Pydantic model)
        tenant_token = validate_tenant_token(token)

        # Convert Pydantic model to dict for FastAPI dependency injection
        claims = tenant_token.model_dump()

        logger.info(
            "Tenant token validation successful",
            extra={
                "user_id": claims.get("sub"),
                "email": claims.get("email"),
                "tenant_id": claims.get("tenant_id"),
                "role": claims.get("role"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

        return claims

    except Exception as e:
        # Handle token validation errors (expired, invalid signature, malformed)
        error_message = str(e)
        logger.warning(
            "Tenant token validation failed",
            extra={
                "error": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_TENANT_TOKEN",
                    "message": f"Invalid or expired tenant token: {error_message}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            },
            headers={"WWW-Authenticate": "Bearer"}
        )


async def validate_tenant_access(
    tenant_id: str,
    tenant_context: Dict[str, Any] = Depends(get_current_tenant)
) -> None:
    """
    Validates that the tenant_id in the JWT matches the path parameter.

    This is critical for tenant isolation - prevents users from accessing
    data for tenants they haven't been explicitly scoped to, even if they
    have multi-tenant access at the user level.

    Args:
        tenant_id: Tenant ID from path parameter
        tenant_context: Validated tenant JWT claims from get_current_tenant

    Raises:
        HTTPException: 403 if tenant_id mismatch detected
    """
    token_tenant_id = tenant_context.get("tenant_id")
    user_id = tenant_context.get("sub")

    if token_tenant_id != tenant_id:
        logger.warning(
            "Tenant access mismatch detected",
            extra={
                "token_tenant_id": token_tenant_id,
                "requested_tenant_id": tenant_id,
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "TENANT_MISMATCH",
                    "message": f"Token tenant_id {token_tenant_id} does not match requested tenant {tenant_id}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )
