"""Tenant-related Pydantic models."""
from typing import Dict, Any, List
from pydantic import BaseModel


class TenantInfo(BaseModel):
    """Tenant information for user profile response."""
    tenant_id: str
    name: str
    slug: str
    role: str
    config_json: Dict[str, Any]


class UserInfoResponse(BaseModel):
    """Response model for GET /api/me endpoint."""
    user_id: str
    email: str
    tenants: List[TenantInfo]


class TenantMetadata(BaseModel):
    """Response model for GET /api/tenant/{tenant_id} endpoint."""
    id: str
    name: str
    slug: str
    is_active: int
    config_json: Dict[str, Any]
    created_at: str


class DashboardInfo(BaseModel):
    """Dashboard information for tenant dashboards list."""
    slug: str
    title: str
    description: str
    config_json: Dict[str, Any]
