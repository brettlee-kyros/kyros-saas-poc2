"""FastAPI application entry point."""
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for shared_config import
sys.path.insert(0, '/app/packages/shared-config/src')

try:
    from shared_config import JWT_ALGORITHM, JWT_ISSUER
    SHARED_CONFIG_LOADED = True
except ImportError:
    logging.warning("shared_config not available - will be mounted at runtime")
    SHARED_CONFIG_LOADED = False

from .config import settings
from .routers import health, auth, user, token, tenant_routes, dashboards
from .middleware.request_logging import RequestLoggingMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Kyros SaaS PoC API",
    description="FastAPI monolith for tenant-isolated dashboard platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add request logging middleware (before CORS)
app.add_middleware(RequestLoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["System"])
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(token.router)
app.include_router(tenant_routes.router)
app.include_router(dashboards.router)


@app.on_event("startup")
async def startup_event():
    """Log configuration on application startup."""
    logger.info("=" * 80)
    logger.info("Kyros SaaS PoC API - Starting Up")
    logger.info("=" * 80)
    logger.info(f"Database path: {settings.DATABASE_PATH}")

    if SHARED_CONFIG_LOADED:
        logger.info(f"Shared config loaded - JWT Algorithm: {JWT_ALGORITHM}")
        logger.info(f"Shared config loaded - JWT Issuer: {JWT_ISSUER}")
    else:
        logger.info("Shared config will be loaded from mounted volume")

    logger.info(f"Listening on: {settings.HOST}:{settings.PORT}")
    logger.info(f"OpenAPI docs: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info("=" * 80)
