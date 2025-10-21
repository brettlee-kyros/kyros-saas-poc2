"""Request logging middleware for debugging."""
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log incoming request bodies for debugging."""

    async def dispatch(self, request: Request, call_next):
        # Only log token exchange requests
        if request.url.path == "/api/token/exchange":
            # Read the body
            body = await request.body()
            logger.info(f"[DEBUG] Token exchange request body: {body.decode('utf-8')}")

            # Create a new request with the body (since body can only be read once)
            async def receive():
                return {"type": "http.request", "body": body}

            request._receive = receive

        response = await call_next(request)
        return response
