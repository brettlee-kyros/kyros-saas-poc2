from unittest.mock import MagicMock, patch
import pytest
import sys
import pandas as pd
import plotly.graph_objects as go
from dash import html

# Mock the cache at global level before any imports!
mock_cache = MagicMock()
mock_cache.memoize = lambda *args, **kwargs: lambda f: f

# Patch the cache module before any imports
patch("kyros_plotly_common.core.cache.cache", mock_cache).start()

# Create and install the mock module BEFORE any tests run
mock_manager = MagicMock()
mock_module = MagicMock()
mock_module.dbx_manager = mock_manager
mock_module.DatabaseManager = MagicMock()

# Place the mock in sys.modules BEFORE any imports happen
sys.modules['dbx_client'] = mock_module

@pytest.fixture(scope="session")
def mock_dbx_client_manager():
    """
    Return the mock dbx_manager for tests to use
    """
    return sys.modules['dbx_client'].dbx_manager

@pytest.fixture
def mock_schema_properties():
    """Mock schema properties returned by parse_schema_properties"""
    return ({
        "targets": {
            "target1": {
                "development_metric": "dev",
                "denominator_weight": "denom_w_col_1",
                "actual": "actual_col_1",
                "expected": "expected_col_1",
                "numerator_weight": "num_w_col_1",
                "mask": "mask_col_1",
                "category": "category_A",
                "statistic": "average",
                "restated": "restated_col_1",
                "baseline": "baseline_col_1",
                "cpp": "cpp_col_1"
            },
            "target2": {
                "development_metric": "dev_since",
                "denominator_weight": "denom_w_col_2",
                "actual": "actual_col_2",
                "expected": "expected_col_2",
                "numerator_weight": "num_w_col_2",
                "mask": "mask_col_2",
                "category": "category_A",
                "statistic": "average",
                "restated": "restated_col_2",
                "baseline": "baseline_col_2",
                "cpp": "cpp_col_2"
            },
        },
        "current_snapshotDate": "2023-01-01",
        "first_snapshotDate": "2022-01-01",
        "cluster": "cluster_id_col",
        "snapshotDate": "snapshot_dt_col",
        "obsAge": "obs_age_col",
        "development_time_unit": "month",
        "manual_dimensions": ["man_dim1", "man_dim2"],
        "exposure": "exposure_col",
        "monitoring_snapshotDate": {
            "name": "monitoring_date_col", 
            "values": ["2023-01-01", "2023-02-01", "2023-03-01"]
        },
        "bubblers": {
            "dimensions": ["dim1", "dim2"]
        }
    }, "test.schema.path")

@pytest.fixture
def mock_redis(mocker, mock_schema_properties):
    """Common fixture for mocking Redis interactions"""
    mock_redis_instance = mocker.patch('kyros_plotly_common.core.redis_client.redis_instance')
    
    # Define the full path that will be used in parse_schema_properties
    full_path = "test.schema.path"
    
    # Mock the table mappings
    table_mappings = {
        'test_name': {'performance1': (full_path, 'test'), 'performance2': (full_path, 'test')},
        'test_consolidated': {'performance1': (full_path, 'test'), 'performance2': (full_path, 'test')}
    }
    
    # Mock lookup_mappings with the proper structure
    lookup_mappings = {
        full_path: {
            "properties": mock_schema_properties[0]
        }
    }
    
    # Set up the Redis mocks to return appropriate values for different keys
    def mock_get_from_redis_side_effect(key):
        if key == "table_mappings":
            return table_mappings
        elif key == "lookup_mappings":
            return lookup_mappings
        else:
            return {}  # Default for other keys
            
    mocker.patch('kyros_plotly_common.core.redis_client.get_from_redis', side_effect=mock_get_from_redis_side_effect)
    mocker.patch('utils.helper_functions.get_from_redis', side_effect=mock_get_from_redis_side_effect)
    
    # Mock the parse_schema_properties to return our comprehensive mock
    mocker.patch('utils.helper_functions.parse_schema_properties', return_value=mock_schema_properties)
    
    # Mock Redis get directly
    mocker.patch('kyros_plotly_common.core.redis_client.redis_instance.get', return_value=None)
    
    return mock_redis_instance

@pytest.fixture
def sample_figure():
    """Create a sample plotly figure for testing"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[1, 2, 3], y=[4, 5, 6], name="Test Trace"))
    return fig

@pytest.fixture
def sample_triangle_df():
    """Create a sample triangle DataFrame"""
    return pd.DataFrame({
        "development": [12, 24, 36], 
        "value": [100, 200, 300], 
        "snapshot_dt_col": ["2023-01-01", "2023-02-01", "2023-03-01"]
    })

@pytest.fixture
def mock_get_icon(mocker):
    """Mock the get_icon function used in UI components"""
    return mocker.patch('utils.components.get_icon', return_value=html.Div("Mock Icon"))

@pytest.fixture
def mock_dash_logger(mocker):
    """Mock dash_logger for testing error handling"""
    return mocker.patch('kyros_plotly_common.logger.dash_logger')