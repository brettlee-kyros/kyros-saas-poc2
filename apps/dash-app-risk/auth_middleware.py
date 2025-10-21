"""JWT validation middleware for Dash application.

This module provides middleware functionality to validate tenant-scoped
JWT tokens on every request to the Dash application. It extracts the
Authorization header, validates the JWT using shared_config utilities,
and stores the tenant_id in thread-local context for use in callbacks.

Usage:
    from auth_middleware import require_tenant_token, get_current_tenant_id

    @server.before_request
    @require_tenant_token
    def validate_jwt():
        pass

    # In callbacks
    tenant_id = get_current_tenant_id()
"""
import sys
import threading
from functools import wraps
from flask import request, jsonify
import logging

# Add paths for shared_config import
sys.path.insert(0, '/app/packages/shared-config/src')

try:
    from shared_config import validate_tenant_token
    SHARED_CONFIG_LOADED = True
except ImportError:
    logging.warning("shared_config not available - will be mounted at runtime")
    SHARED_CONFIG_LOADED = False
    # Define fallback for development
    def validate_tenant_token(token):
        raise Exception("shared_config not loaded")

logger = logging.getLogger(__name__)

# Thread-local storage for tenant context
_context = threading.local()


def get_current_tenant_id() -> str:
    """Get tenant_id from current request context.

    Returns:
        str: Tenant UUID from validated JWT

    Example:
        tenant_id = get_current_tenant_id()
        logger.info(f"Processing request for tenant: {tenant_id}")
    """
    return getattr(_context, 'tenant_id', None)


def get_current_token() -> str:
    """Get JWT token from current request context.

    Returns:
        str: JWT token from Authorization header

    Example:
        token = get_current_token()
        headers = {"Authorization": f"Bearer {token}"}
    """
    return getattr(_context, 'token', None)


def require_tenant_token(f):
    """Decorator to validate tenant-scoped JWT on every request.

    This decorator:
    1. Extracts Authorization header from incoming request
    2. Validates JWT using shared_config.validate_tenant_token()
    3. Extracts tenant_id from JWT claims
    4. Stores tenant_id and token in thread-local context
    5. Returns 401 error for any validation failure

    Args:
        f: Flask route function to wrap

    Returns:
        Wrapped function with JWT validation

    Example:
        @server.before_request
        @require_tenant_token
        def validate_jwt():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication for static asset requests
        # The proxy handles token injection for all other requests
        if (request.path.startswith('/_dash-component-suites/') or
            request.path.startswith('/assets/') or
            request.path.endswith(('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.map'))):
            logger.debug(f"Skipping auth for static asset: {request.path}")
            return f(*args, **kwargs)

        # Extract Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            logger.warning("Missing Authorization header")
            return jsonify({
                'error': 'UNAUTHORIZED',
                'message': 'Authorization header required'
            }), 401

        # Extract token (format: "Bearer <token>")
        try:
            parts = auth_header.split(' ')
            if len(parts) != 2 or parts[0] != 'Bearer':
                raise ValueError("Invalid format")
            token = parts[1]
        except (IndexError, ValueError):
            logger.warning(f"Malformed Authorization header: {auth_header[:20]}...")
            return jsonify({
                'error': 'UNAUTHORIZED',
                'message': 'Malformed Authorization header. Expected format: Bearer <token>'
            }), 401

        # Validate JWT
        try:
            claims = validate_tenant_token(token)
            # claims is a Pydantic TenantScopedToken model, access attributes directly
            tenant_id = getattr(claims, 'tenant_id', None) if claims else None

            if not tenant_id:
                logger.warning("Missing tenant_id in JWT claims")
                return jsonify({
                    'error': 'UNAUTHORIZED',
                    'message': 'Invalid token: missing tenant_id claim'
                }), 401

            # Store in thread-local context
            _context.tenant_id = tenant_id
            _context.token = token

            logger.info(f"JWT validated successfully for tenant: {tenant_id}")

        except Exception as e:
            logger.warning(f"JWT validation failed: {str(e)}")
            return jsonify({
                'error': 'UNAUTHORIZED',
                'message': f'Invalid or expired token: {str(e)}'
            }), 401

        return f(*args, **kwargs)

    return decorated_function


def clear_context():
    """Clear thread-local context.

    Used for testing or cleanup. In production, thread-local context
    is automatically isolated per request.

    Example:
        # After each test
        clear_context()
    """
    _context.tenant_id = None
    _context.token = None
