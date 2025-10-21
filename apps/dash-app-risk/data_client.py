"""Data API client for fetching tenant-scoped dashboard data.

This module provides a client for communicating with the FastAPI data
backend. It handles:
- Authorization header forwarding
- HTTP request/response handling
- Error handling and logging
- DataFrame conversion

Usage:
    from data_client import DataAPIClient

    df = DataAPIClient.fetch_dashboard_data('customer-lifetime-value')
    if df is not None:
        # Process data
        pass
"""
import os
import requests
import pandas as pd
from typing import Optional
import logging
from auth_middleware import get_current_token, get_current_tenant_id

logger = logging.getLogger(__name__)

# API base URL from environment or default to Docker Compose service name
API_BASE_URL = os.getenv('API_BASE_URL', 'http://api:8000')


class DataAPIClient:
    """Client for fetching tenant-scoped data from FastAPI backend.

    This client communicates with the FastAPI data layer to retrieve
    tenant-filtered data for dashboards. It automatically includes the
    Authorization header from the current request context.

    All methods are static as the client is stateless - tenant context
    comes from thread-local storage managed by auth_middleware.
    """

    @staticmethod
    def fetch_dashboard_data(dashboard_slug: str) -> Optional[pd.DataFrame]:
        """Fetch tenant-scoped data for a dashboard.

        This method:
        1. Retrieves JWT token from request context
        2. Makes authenticated request to data API
        3. Converts JSON response to pandas DataFrame
        4. Handles errors gracefully

        Args:
            dashboard_slug: Slug of the dashboard (e.g., 'customer-lifetime-value')

        Returns:
            DataFrame with tenant-filtered data, or None on error

        Example:
            df = DataAPIClient.fetch_dashboard_data('customer-lifetime-value')
            if df is not None and not df.empty:
                # Render visualization
                fig = create_figure(df)
            else:
                # Show error message
                return error_layout()
        """
        token = get_current_token()
        tenant_id = get_current_tenant_id()

        if not token:
            logger.error("No token available in request context")
            return None

        if not tenant_id:
            logger.error("No tenant_id available in request context")
            return None

        url = f"{API_BASE_URL}/api/dashboards/{dashboard_slug}/data"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            logger.info(f"Fetching data for dashboard: {dashboard_slug}, tenant: {tenant_id}")

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            records = data.get('data', [])

            logger.info(f"Received {len(records)} records for {dashboard_slug}")

            # Convert to DataFrame
            if records:
                df = pd.DataFrame(records)
                return df
            else:
                logger.warning(f"No data returned for {dashboard_slug}")
                return pd.DataFrame()  # Empty DataFrame

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"No data found for dashboard: {dashboard_slug} (404)")
            else:
                logger.error(f"Data API HTTP error: {e.response.status_code} - {str(e)}")
            return None

        except requests.exceptions.Timeout:
            logger.error(f"Data API request timed out for dashboard: {dashboard_slug}")
            return None

        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to Data API at {API_BASE_URL}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Data API request failed: {str(e)}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error fetching data: {str(e)}")
            return None

    @staticmethod
    def health_check() -> bool:
        """Check if Data API is available.

        Returns:
            bool: True if API is healthy, False otherwise

        Example:
            if not DataAPIClient.health_check():
                logger.error("Data API is unavailable")
        """
        try:
            url = f"{API_BASE_URL}/api/health"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
