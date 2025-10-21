"""Unit tests for data_loader module."""
import pytest
import pandas as pd
from pathlib import Path

from src.data.data_loader import (
    load_tenant_data,
    clear_cache,
    get_cache_stats,
    _get_data_file_path
)

# Test tenant IDs
ACME_ID = "8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345"
BETA_ID = "2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4"


@pytest.fixture(autouse=True)
def reset_cache():
    """Clear cache before each test."""
    clear_cache()
    yield
    clear_cache()


class TestDataFilePaths:
    """Test dashboard slug to file path mapping."""

    def test_clv_dashboard_path(self):
        """Test CLV dashboard path mapping."""
        path = _get_data_file_path('customer-lifetime-value')
        assert path.name == 'data.csv'
        assert 'clv' in str(path)

    def test_risk_dashboard_path(self):
        """Test Risk dashboard path mapping."""
        path = _get_data_file_path('risk-analysis')
        assert path.name == 'data.csv'
        assert 'risk' in str(path)

    def test_invalid_dashboard_path(self):
        """Test invalid dashboard slug returns empty path."""
        path = _get_data_file_path('non-existent-dashboard')
        assert path == Path('')


class TestLoadTenantData:
    """Test load_tenant_data function."""

    def test_load_clv_data_acme(self):
        """Test loading CLV data for Acme tenant."""
        df = load_tenant_data(ACME_ID, "customer-lifetime-value")

        assert df is not None, "Should return DataFrame for Acme CLV data"
        assert len(df) > 0, "Should have records"
        assert 'tenant_id' in df.columns, "Should have tenant_id column"
        assert all(df['tenant_id'] == ACME_ID), "All records should belong to Acme"

    def test_load_clv_data_beta_returns_none(self):
        """Test that Beta cannot access CLV data."""
        df = load_tenant_data(BETA_ID, "customer-lifetime-value")

        # Beta should not have CLV data (demonstrates tenant isolation)
        assert df is None, "Beta should not have access to CLV data"

    def test_load_risk_data_acme(self):
        """Test loading Risk data for Acme tenant."""
        df = load_tenant_data(ACME_ID, "risk-analysis")

        assert df is not None, "Should return DataFrame for Acme Risk data"
        assert len(df) > 0, "Should have records"
        assert all(df['tenant_id'] == ACME_ID), "All records should belong to Acme"

    def test_load_risk_data_beta(self):
        """Test loading Risk data for Beta tenant."""
        df = load_tenant_data(BETA_ID, "risk-analysis")

        assert df is not None, "Should return DataFrame for Beta Risk data"
        assert len(df) > 0, "Should have records"
        assert all(df['tenant_id'] == BETA_ID), "All records should belong to Beta"

    def test_load_invalid_dashboard(self):
        """Test loading data for non-existent dashboard."""
        df = load_tenant_data(ACME_ID, "non-existent-dashboard")

        assert df is None, "Should return None for invalid dashboard"

    def test_tenant_data_isolation(self):
        """Test that tenants cannot see each other's data."""
        # Load data for both tenants
        df_acme = load_tenant_data(ACME_ID, "risk-analysis")
        df_beta = load_tenant_data(BETA_ID, "risk-analysis")

        assert df_acme is not None, "Acme should have Risk data"
        assert df_beta is not None, "Beta should have Risk data"

        # Verify no overlap in data
        acme_tenant_ids = set(df_acme['tenant_id'].unique())
        beta_tenant_ids = set(df_beta['tenant_id'].unique())

        assert acme_tenant_ids == {ACME_ID}, "Acme data should only contain Acme tenant_id"
        assert beta_tenant_ids == {BETA_ID}, "Beta data should only contain Beta tenant_id"
        assert acme_tenant_ids.isdisjoint(beta_tenant_ids), "No tenant_id overlap allowed"


class TestCaching:
    """Test in-memory caching mechanism."""

    def test_cache_populated_on_first_load(self):
        """Test that cache is populated after first data load."""
        stats_before = get_cache_stats()
        assert stats_before['cached_dashboards'] == 0, "Cache should be empty initially"

        # Load data (should cache it)
        load_tenant_data(ACME_ID, "customer-lifetime-value")

        stats_after = get_cache_stats()
        assert stats_after['cached_dashboards'] == 1, "Cache should have 1 dashboard"
        assert stats_after['total_records'] > 0, "Cache should have records"

    def test_second_load_uses_cache(self, caplog):
        """Test that second load reuses cached data."""
        # First load (should hit file system)
        df1 = load_tenant_data(ACME_ID, "customer-lifetime-value")

        # Clear logs
        caplog.clear()

        # Second load (should use cache)
        df2 = load_tenant_data(ACME_ID, "customer-lifetime-value")

        # Should not see "Loading data for dashboard" message (cache hit)
        loading_messages = [record for record in caplog.records
                            if "Loading data for dashboard" in record.message]
        assert len(loading_messages) == 0, "Should not reload from file (cache hit)"

        # DataFrames should be equivalent
        assert df1.equals(df2), "Cached data should match original"

    def test_clear_cache(self):
        """Test cache clearing."""
        # Load some data
        load_tenant_data(ACME_ID, "customer-lifetime-value")
        load_tenant_data(ACME_ID, "risk-analysis")

        stats_before = get_cache_stats()
        assert stats_before['cached_dashboards'] == 2

        # Clear cache
        clear_cache()

        stats_after = get_cache_stats()
        assert stats_after['cached_dashboards'] == 0, "Cache should be empty"
        assert stats_after['total_records'] == 0, "Cache should have no records"

    def test_cache_shared_across_tenants(self):
        """Test that cache is shared (data filtered per tenant, not cached separately)."""
        # Load for Acme
        load_tenant_data(ACME_ID, "risk-analysis")

        stats_after_acme = get_cache_stats()

        # Load for Beta (same dashboard)
        load_tenant_data(BETA_ID, "risk-analysis")

        stats_after_beta = get_cache_stats()

        # Cache size should not increase (data is cached once, filtered at access time)
        assert stats_after_acme['cached_dashboards'] == stats_after_beta['cached_dashboards']


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_missing_tenant_id_column(self):
        """Test handling of data files without tenant_id column."""
        # This test would require a mock file without tenant_id
        # For now, we document the expected behavior
        pass

    def test_empty_dataframe(self):
        """Test handling when filtered data is empty."""
        # Create a fake tenant ID that has no data
        fake_tenant_id = "00000000-0000-0000-0000-000000000000"

        df = load_tenant_data(fake_tenant_id, "customer-lifetime-value")

        assert df is None, "Should return None when no records match tenant_id"

    def test_invalid_tenant_id_format(self):
        """Test loading with invalid tenant_id format."""
        df = load_tenant_data("invalid-uuid", "customer-lifetime-value")

        # Should return None (no records match invalid UUID)
        assert df is None, "Should return None for invalid tenant_id"


class TestDataIntegrity:
    """Test data integrity and expected structure."""

    def test_clv_data_has_expected_columns(self):
        """Test that CLV data has expected columns."""
        df = load_tenant_data(ACME_ID, "customer-lifetime-value")

        assert df is not None
        assert 'tenant_id' in df.columns, "Must have tenant_id column"
        # Note: Exact column names depend on source data structure

    def test_risk_data_has_expected_columns(self):
        """Test that Risk data has expected columns."""
        df = load_tenant_data(ACME_ID, "risk-analysis")

        assert df is not None
        assert 'tenant_id' in df.columns, "Must have tenant_id column"
        # Note: Exact column names depend on source data structure

    def test_no_data_modification_on_load(self):
        """Test that loading data doesn't modify the cached DataFrame."""
        # Load data twice
        df1 = load_tenant_data(ACME_ID, "customer-lifetime-value")
        original_len = len(df1)

        df2 = load_tenant_data(ACME_ID, "customer-lifetime-value")

        # Length should be the same
        assert len(df2) == original_len, "Data should not change between loads"
