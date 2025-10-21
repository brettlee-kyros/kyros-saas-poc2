"""
Data loader for tenant-scoped dashboard data.

This module provides functions to load and filter CSV data by tenant_id,
with in-memory caching for performance.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# In-memory cache: {dashboard_slug: DataFrame}
_data_cache: Dict[str, pd.DataFrame] = {}


def load_tenant_data(tenant_id: str, dashboard_slug: str) -> Optional[pd.DataFrame]:
    """
    Load and filter data for a specific tenant and dashboard.

    Args:
        tenant_id: UUID of the tenant
        dashboard_slug: Slug of the dashboard (e.g., 'customer-lifetime-value')

    Returns:
        Filtered DataFrame or None if not found

    Example:
        >>> df = load_tenant_data("8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345", "customer-lifetime-value")
        >>> len(df)
        100
    """
    cache_key = dashboard_slug

    # Load from cache or file
    if cache_key not in _data_cache:
        data_file = _get_data_file_path(dashboard_slug)

        if not data_file.exists():
            logger.warning(f"Data file not found for dashboard: {dashboard_slug}")
            return None

        try:
            logger.info(f"Loading data for dashboard: {dashboard_slug}")
            df = pd.read_csv(data_file)
            _data_cache[cache_key] = df
            logger.info(f"Cached {len(df)} records for dashboard: {dashboard_slug}")
        except Exception as e:
            logger.error(f"Error loading data file {data_file}: {str(e)}")
            return None

    # Filter by tenant_id
    df = _data_cache[cache_key]

    if 'tenant_id' not in df.columns:
        logger.error(f"tenant_id column missing in dashboard: {dashboard_slug}")
        return None

    filtered_df = df[df['tenant_id'] == tenant_id].copy()

    logger.info(
        f"Loaded {len(filtered_df)} records for tenant {tenant_id}, "
        f"dashboard {dashboard_slug}"
    )

    return filtered_df if len(filtered_df) > 0 else None


def _get_data_file_path(dashboard_slug: str) -> Path:
    """
    Map dashboard slug to data file path.

    Args:
        dashboard_slug: Slug of the dashboard

    Returns:
        Path object pointing to the data file
    """
    # Base path relative to app directory
    # __file__ is /app/src/data/data_loader.py
    # Go up 3 levels to get to /app: parent -> /app/src/data, parent -> /app/src, parent -> /app
    base_path = Path(__file__).parent.parent.parent / "data" / "mock-data"

    slug_to_path = {
        'customer-lifetime-value': base_path / 'clv' / 'data.csv',
        'risk-analysis': base_path / 'risk' / 'data.csv',
    }

    return slug_to_path.get(dashboard_slug, Path(''))


def clear_cache():
    """
    Clear the in-memory data cache.

    Useful for testing or when data files are updated.
    """
    global _data_cache
    _data_cache = {}
    logger.info("Data cache cleared")


def get_cache_stats() -> Dict[str, int]:
    """
    Get statistics about the current cache.

    Returns:
        Dictionary with cache statistics
    """
    return {
        'cached_dashboards': len(_data_cache),
        'total_records': sum(len(df) for df in _data_cache.values())
    }
