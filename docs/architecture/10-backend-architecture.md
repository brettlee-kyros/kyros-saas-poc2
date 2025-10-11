# 10. Backend Architecture

This section defines FastAPI service organization, middleware patterns, and authentication/authorization implementation.

## 10.1 Service Architecture (Monolith)

### Function Organization

```
apps/api/src/
├── main.py                       # FastAPI app entry point
├── config/
│   ├── __init__.py
│   └── settings.py               # Environment configuration
├── middleware/
│   ├── __init__.py
│   ├── auth.py                   # JWT validation middleware
│   └── cors.py                   # CORS configuration
├── routers/
│   ├── __init__.py
│   ├── auth.py                   # Mock auth endpoints
│   ├── token.py                  # Token exchange endpoints
│   ├── tenant.py                 # Tenant metadata endpoints
│   └── dashboard.py              # Dashboard data endpoints
├── models/
│   ├── __init__.py
│   ├── tokens.py                 # Pydantic models for JWTs
│   ├── tenant.py                 # Tenant data models
│   └── dashboard.py              # Dashboard data models
├── services/
│   ├── __init__.py
│   ├── jwt_service.py            # JWT encoding/decoding/validation
│   ├── tenant_service.py         # Tenant metadata business logic
│   └── data_service.py           # Dashboard data loading (DAL)
├── database/
│   ├── __init__.py
│   ├── connection.py             # SQLite async connection
│   └── queries.py                # SQL query functions
└── data/
    ├── __init__.py
    ├── mock_users.py             # Pre-generated JWTs and mock user data
    └── data_loader.py            # In-memory Pandas DataFrame loader
```

---
