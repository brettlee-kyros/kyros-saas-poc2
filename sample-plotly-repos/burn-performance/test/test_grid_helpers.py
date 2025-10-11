import pytest
from unittest.mock import MagicMock
from dash import no_update
from dash.exceptions import PreventUpdate
from utils.grid_helpers import combined_grid_callback
from utils.exception_handlers import GridError

# --- Tests for combined_grid_callback ---
def test_combined_grid_no_consolidated_name():
    """Test that we properly prevent updates when no consolidated name is provided"""
    with pytest.raises(PreventUpdate):
        combined_grid_callback(None, ["tgt"], "btn_data", "date", 0.9, [])

@pytest.mark.parametrize("conf_level", [None, 40, 110])
def test_combined_grid_invalid_conf_level(conf_level):
    """Test that we properly prevent updates for invalid confidence levels"""
    with pytest.raises(PreventUpdate):
        combined_grid_callback("name", ["tgt"], "btn_data", "date", conf_level, [])

def test_combined_grid_no_target_value(monkeypatch):
    """Test handling when no target value is provided"""
    # Mock the needed components
    mock_ctx = MagicMock()
    mock_ctx.triggered_id = "target-dd"
    monkeypatch.setattr("utils.grid_helpers.ctx", mock_ctx)
    
    grid_content, hierarchy_sig = combined_grid_callback(
        "test_name", None, "back-to-tabular-view", "2023-01-01", 0.95, []
    )
    
    assert grid_content == ["Oops! It looks like you have not selected any target values."]
    assert hierarchy_sig == no_update

def test_combined_grid_default_view(monkeypatch):
    """Test the default cluster level view for the grid"""
    # Mock all the necessary functions that would be called
    mock_ctx = MagicMock()
    mock_ctx.triggered_id = "target-dd"
    monkeypatch.setattr("utils.grid_helpers.ctx", mock_ctx)
    
    # Mock the cluster grid creation function directly
    mock_cluster_grid = MagicMock(return_value=("ClusterGrid", "ClusterSignal", 0.9))
    monkeypatch.setattr("utils.grid_helpers._create_cluster_level_grid", mock_cluster_grid)
    
    # Call the function with a default view (button_data=None)
    result = combined_grid_callback(
        "test_consolidated", ["target1"], None, "2023-01-01", 0.9, ["clusterA"]
    )
    
    # Check that the correct function was called and results returned
    assert result == ("ClusterGrid", "ClusterSignal", 0.9)
    mock_cluster_grid.assert_called_once_with(
        "test_consolidated", ["target1"], "2023-01-01", 0.9, ["clusterA"]
    )

def test_combined_grid_manual_dimension_view(monkeypatch):
    """Test the manual dimension view for the grid"""
    # Mock all the necessary functions that would be called
    mock_ctx = MagicMock()
    mock_ctx.triggered_id = "header-button-XYZ"  # Not header-button-store
    monkeypatch.setattr("utils.grid_helpers.ctx", mock_ctx)
    
    # Mock the manual dimension grid creation function directly
    mock_manual_grid = MagicMock(return_value=("ManualGrid", "ManualSignal", 0.8))
    monkeypatch.setattr("utils.grid_helpers._create_manual_dimension_grid", mock_manual_grid)
    
    # Call the function with a manual dimension view
    result = combined_grid_callback(
        "test_consolidated", ["target1"], "groupby_dim_X", "2023-01-01", 0.8, ["clusterA"]
    )
    
    # Check that the correct function was called and results returned
    assert result == ("ManualGrid", "ManualSignal", 0.8)
    mock_manual_grid.assert_called_once_with(
        "test_consolidated", ["target1"], "2023-01-01", 0.8, "groupby_dim_X", ["clusterA"]
    )

def test_combined_grid_explicit_groupby_view(monkeypatch):
    """Test the explicit groupby view change for the grid"""
    # Mock all the necessary functions that would be called
    mock_ctx = MagicMock()
    mock_ctx.triggered_id = "header-button-store"  # Explicit header store button
    monkeypatch.setattr("utils.grid_helpers.ctx", mock_ctx)
    
    # Mock the manual dimension grid creation function directly
    mock_manual_grid = MagicMock(return_value=("ManualGrid", "ManualSignal", 0.8))
    monkeypatch.setattr("utils.grid_helpers._create_manual_dimension_grid", mock_manual_grid)
    
    # Call the function with a non-default button_data
    result = combined_grid_callback(
        "test_consolidated", ["target1"], "groupby_dim_Y", "2023-01-01", 0.8, ["clusterA"]
    )
    
    # Check that the correct function was called and results returned
    assert result == ("ManualGrid", "ManualSignal", 0.8)
    mock_manual_grid.assert_called_once_with(
        "test_consolidated", ["target1"], "2023-01-01", 0.8, "groupby_dim_Y", ["clusterA"]
    )

def test_combined_grid_exception_handling(monkeypatch):
    """Test that exceptions are properly wrapped in GridError"""
    # Mock the context object
    mock_ctx = MagicMock()
    mock_ctx.triggered_id = "target-dd"
    monkeypatch.setattr("utils.grid_helpers.ctx", mock_ctx)
    
    # Mock the logger
    mock_logger = MagicMock()
    monkeypatch.setattr("utils.grid_helpers.dash_logger", mock_logger)
    
    # Mock the cluster grid creation to raise an exception
    def mock_raise_exception(*args, **kwargs):
        raise ValueError("Test grid error message")
    
    monkeypatch.setattr("utils.grid_helpers._create_cluster_level_grid", mock_raise_exception)
    
    # Check that the exception is properly wrapped
    with pytest.raises(GridError) as exc_info:
        combined_grid_callback(
            "test_consolidated", ["target1"], None, "2023-01-01", 0.9, []
        )
    
    # Verify the exception message contains our test error
    assert "Test grid error message" in str(exc_info.value)
    # Verify the logger was called
    assert mock_logger.error.called 