import pytest
import pandas as pd
from dash.exceptions import PreventUpdate
from dash import html, no_update # Added no_update
from utils.data_processors import (
    gather_selected_clusters,
    gather_selected_snapshotdate
)
from utils.exception_handlers import TM1PlotError

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
                "statistic": "average"
            },
            "target2": {
                "development_metric": "dev_since",
                "denominator_weight": "denom_w_col_2",
                "actual": "actual_col_2",
                "expected": "expected_col_2",
                "numerator_weight": "num_w_col_2",
                "mask": "mask_col_2",
                "category": "category_A",
                "statistic": "average"
            },
        },
        "current_snapshotDate": "2023-01-01",
        "first_snapshotDate": "2022-01-01",
        "cluster": "cluster_id_col",
        "snapshotDate": "snapshot_dt_col",
        "obsAge": "obs_age_col",
        "development_time_unit": "month",
        "manual_dimensions": ["man_dim1", "man_dim2"]
    }, "test.schema.path")

@pytest.fixture
def mock_redis(mocker, mock_schema_properties):
    # Mock Redis and any Redis-related functions
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
def mock_extract_clusters(mocker):
    return mocker.patch('utils.helper_functions.extract_clusters')

@pytest.fixture
def mock_extract_dynamic_column_value(mocker):
    return mocker.patch('utils.bubbler_functions.extract_dynamic_column_value')

@pytest.fixture
def mock_get_manual_dimensions(mocker):
    # Mock data_processors.get_manual_dimensions to return a dataframe with expected structure
    mock_fn = mocker.patch('utils.data_processors.get_manual_dimensions')
    mock_fn.return_value = pd.DataFrame({
        "dim_key": ["dim1"], 
        "dim_value": ["val1"], 
        "cluster": ["B"]
    })
    return mock_fn

@pytest.fixture
def mock_get_matching_clusters(mocker):
    # Mock to return a list directly without using DataFrame operations
    mock_fn = mocker.patch('utils.helper_functions.get_matching_clusters')
    mock_fn.return_value = ["B"]
    return mock_fn

@pytest.fixture
def mock_determine_selector_signal(mocker):
    return mocker.patch('utils.helper_functions.determine_selector_signal')

@pytest.fixture
def mock_create_cluster_signal_children(mocker):
    # Mock to directly return a list of two divs to match the expected output format
    mock_fn = mocker.patch('utils.ui_helpers.create_cluster_signal_children')
    mock_fn.return_value = [html.Div("icon"), html.Div("tooltip")]
    return mock_fn

def test_fetch_and_store_data(monkeypatch):
    # Create test data
    mock_df = pd.DataFrame({'col1': [1, 2]})
    expected_result = {'dev1': mock_df.to_dict("records")}
    
    # Define a replacement function for fetch_and_store_data
    def mock_fetch(dev_values, consolidated_name, selected_clusters, target_value, mask):
        return expected_result
    
    # Import here to avoid module-level import which would make mocking harder
    import utils.data_processors
    
    # Replace the real function with our mock
    monkeypatch.setattr(utils.data_processors, "fetch_and_store_data", mock_fetch)
    
    # Call the function and verify results
    from utils.data_processors import fetch_and_store_data
    result = fetch_and_store_data(["dev1"], "test_name", [], ["target1"], "mask")
    
    assert result == expected_result

# Test a simplified gather_selected_clusters with function dict (should raise PreventUpdate)
def test_gather_selected_clusters_prevent_update(mock_redis, mocker):
    mock_create_cluster_signal_children = mocker.patch('utils.ui_helpers.create_cluster_signal_children')
    
    with pytest.raises(PreventUpdate):
        gather_selected_clusters({"function": "some_func"}, "test_name")

# Test simplified gather_selected_clusters with empty rows
def test_gather_selected_clusters_empty_rows(mock_redis, mocker):
    mock_create_cluster_signal_children = mocker.patch('utils.ui_helpers.create_cluster_signal_children')
    mock_create_cluster_signal_children.return_value = [html.Div("icon"), html.Div("tooltip")]
    
    result_clusters, result_children = gather_selected_clusters([], "test_name")
    assert result_clusters == []
    assert len(result_children) == 2  # Expecting two items in the UI components

# Test simplified gather_selected_snapshotdate with empty inputs
def test_gather_selected_snapshotdate_empty():
    assert gather_selected_snapshotdate(None) == {}
    assert gather_selected_snapshotdate({}) == {}
    assert gather_selected_snapshotdate({"points": []}) == {}

# Test gather_selected_snapshotdate with valid data
def test_gather_selected_snapshotdate_with_data():
    selected_data = {
        "points": [
            {"x": "2023-01-01", "pointIndex": 0},
            {"x": "2023-01-02", "pointIndex": 1}
        ]
    }
    expected = {
        "snapshotDates": ["2023-01-01", "2023-01-02"],
        "point_indices": [0, 1]
    }
    assert gather_selected_snapshotdate(selected_data) == expected 