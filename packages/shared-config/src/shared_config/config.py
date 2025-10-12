"""
JWT Configuration Constants

This module defines all JWT-related configuration used across
FastAPI and Dash applications to ensure consistency.

⚠️ PoC ONLY: Secret key is hardcoded. In MVP, load from environment
variable or secrets manager (e.g., Azure Key Vault).
"""

# JWT Secret Key
# ⚠️ CRITICAL: This is a mock secret for PoC only
# MVP MUST load from environment variable or secrets manager
JWT_SECRET_KEY = "kyros-poc-secret-key-CHANGE-IN-PRODUCTION-12345678"

# JWT Algorithm
JWT_ALGORITHM = "HS256"

# JWT Issuer
JWT_ISSUER = "kyros-poc"

# Token Expiry Times (in seconds)
USER_TOKEN_EXPIRY = 3600      # 1 hour - multi-tenant user access token
TENANT_TOKEN_EXPIRY = 1800    # 30 minutes - tenant-scoped token

# MVP TODO:
# import os
# JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
# if not JWT_SECRET_KEY:
#     raise ValueError("JWT_SECRET_KEY environment variable must be set")
