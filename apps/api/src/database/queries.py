"""Database query functions for API endpoints."""
import json
import logging
from typing import List, Dict, Any, Optional

import aiosqlite

logger = logging.getLogger(__name__)


async def get_user_by_id(db: aiosqlite.Connection, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Query user record by user_id.

    Args:
        db: aiosqlite database connection
        user_id: User UUID

    Returns:
        Dict with user data (id, email, created_at) or None if not found
    """
    cursor = await db.execute(
        "SELECT user_id, email, created_at FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = await cursor.fetchone()

    if not row:
        logger.debug(f"User not found: {user_id}")
        return None

    return {
        "user_id": row["user_id"],
        "email": row["email"],
        "created_at": row["created_at"]
    }


async def get_user_tenants(
    db: aiosqlite.Connection,
    user_id: str,
    tenant_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Query tenant records for user with role information.

    Joins tenants table with user_tenants table to get role for each tenant.
    Only returns active tenants that are in the provided tenant_ids list.
    Results are sorted alphabetically by tenant name.

    Args:
        db: aiosqlite database connection
        user_id: User UUID
        tenant_ids: List of tenant UUIDs from JWT claims

    Returns:
        List of dicts with tenant data (id, name, slug, role, config_json)
        Returns empty list if no tenants found (not an error condition)
    """
    if not tenant_ids:
        logger.debug(f"Empty tenant_ids list for user {user_id}")
        return []

    # Build parameterized query with correct number of placeholders
    placeholders = ",".join("?" * len(tenant_ids))
    query = f"""
        SELECT
            t.id,
            t.name,
            t.slug,
            t.config_json,
            ut.role
        FROM tenants t
        JOIN user_tenants ut ON t.id = ut.tenant_id
        WHERE ut.user_id = ?
            AND t.id IN ({placeholders})
            AND t.is_active = 1
        ORDER BY t.name ASC
    """

    # Parameters: user_id first, then all tenant_ids
    params = [user_id] + tenant_ids

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()

    tenants = []
    for row in rows:
        # Parse config_json from TEXT to dict
        config_json = {}
        if row["config_json"]:
            try:
                config_json = json.loads(row["config_json"])
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in config_json for tenant {row['id']}")
                config_json = {}

        tenants.append({
            "id": row["id"],
            "name": row["name"],
            "slug": row["slug"],
            "role": row["role"],
            "config_json": config_json
        })

    logger.debug(f"Found {len(tenants)} active tenants for user {user_id}")
    return tenants


async def get_user_tenant_role(
    db: aiosqlite.Connection,
    user_id: str,
    tenant_id: str
) -> Optional[str]:
    """
    Query user's role for a specific tenant.

    Args:
        db: aiosqlite database connection
        user_id: User UUID
        tenant_id: Tenant UUID

    Returns:
        Role string ('admin', 'viewer', etc.) or None if no relationship found
    """
    cursor = await db.execute(
        "SELECT role FROM user_tenants WHERE user_id = ? AND tenant_id = ?",
        (user_id, tenant_id)
    )
    row = await cursor.fetchone()

    if not row:
        logger.debug(f"No role found for user {user_id} and tenant {tenant_id}")
        return None

    return row["role"]


async def get_tenant_by_id(
    db: aiosqlite.Connection,
    tenant_id: str
) -> Optional[Dict[str, Any]]:
    """
    Query tenant record by tenant_id.

    Args:
        db: aiosqlite database connection
        tenant_id: Tenant UUID

    Returns:
        Dict with tenant data (id, name, slug, is_active, config_json, created_at)
        or None if not found
    """
    cursor = await db.execute(
        "SELECT id, name, slug, is_active, config_json, created_at FROM tenants WHERE id = ?",
        (tenant_id,)
    )
    row = await cursor.fetchone()

    if not row:
        logger.debug(f"Tenant not found: {tenant_id}")
        return None

    # Parse config_json from TEXT to dict
    config_json = {}
    if row["config_json"]:
        try:
            config_json = json.loads(row["config_json"])
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in config_json for tenant {tenant_id}")
            config_json = {}

    return {
        "id": row["id"],
        "name": row["name"],
        "slug": row["slug"],
        "is_active": row["is_active"],
        "config_json": config_json,
        "created_at": row["created_at"]
    }


async def get_tenant_dashboards(
    db: aiosqlite.Connection,
    tenant_id: str
) -> List[Dict[str, Any]]:
    """
    Query dashboards assigned to a tenant.

    Joins dashboards table with tenant_dashboards junction table to get
    all dashboards assigned to the specified tenant. Results are sorted
    alphabetically by dashboard title.

    Args:
        db: aiosqlite database connection
        tenant_id: Tenant UUID

    Returns:
        List of dicts with dashboard data (slug, title, description, config_json)
        Returns empty list if no dashboards assigned (not an error)
    """
    query = """
        SELECT
            d.slug,
            d.title,
            d.description,
            d.config_json
        FROM dashboards d
        JOIN tenant_dashboards td ON d.slug = td.slug
        WHERE td.tenant_id = ?
        ORDER BY d.title ASC
    """

    cursor = await db.execute(query, (tenant_id,))
    rows = await cursor.fetchall()

    dashboards = []
    for row in rows:
        # Parse config_json from TEXT to dict
        config_json = {}
        if row["config_json"]:
            try:
                config_json = json.loads(row["config_json"])
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in config_json for dashboard {row['slug']}")
                config_json = {}

        dashboards.append({
            "slug": row["slug"],
            "title": row["title"],
            "description": row["description"],
            "config_json": config_json
        })

    logger.debug(f"Found {len(dashboards)} dashboards for tenant {tenant_id}")
    return dashboards
