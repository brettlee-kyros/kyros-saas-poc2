"""Async SQLite database connection manager."""
import logging
from contextlib import asynccontextmanager

import aiosqlite

from ..config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_db_connection():
    """
    Async context manager for SQLite database connections.

    Usage:
        async with get_db_connection() as db:
            cursor = await db.execute("SELECT * FROM tenants")
            results = await cursor.fetchall()

    Yields:
        aiosqlite.Connection: Database connection
    """
    conn = None
    try:
        conn = await aiosqlite.connect(settings.DATABASE_PATH)
        conn.row_factory = aiosqlite.Row  # Enable dict-like row access
        logger.debug(f"Database connection established: {settings.DATABASE_PATH}")
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            await conn.close()
            logger.debug("Database connection closed")
