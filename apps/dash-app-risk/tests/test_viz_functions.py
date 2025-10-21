"""
Tests for visualization functions.
"""
from unittest.mock import patch
import plotly.graph_objects as go

from utils.viz_functions import update_distribution_comparison


@patch('utils.viz_functions.parse_schema_properties')
def test_update_distribution_comparison_uses_full_path(mock_parse_schema_properties):
    """Test that update_distribution_comparison uses full path to get properties."""
    # Setup mock parse_schema_properties
    mock_parse_schema_properties.return_value = ({
        'mix_type': 'Snapshot Date',
    }, 'catalog.schema.table')
    
    # Create mock variable data
    variable_data = {
        'variable': 'age_group',
        'distributions': {
            '2023-01-01': {'1': 0.5, '2': 0.5},
            '2023-02-01': {'1': 0.4, '2': 0.6}
        },
        'bucket_labels': {'1': 'Group 1', '2': 'Group 2'}
    }
    
    # Create patchers for create_histogram_figure and create_mix_figure
    with patch('utils.viz_functions.create_histogram_figure') as mock_hist, \
         patch('utils.viz_functions.create_empty_plot') as mock_empty:
        
        # Mock return values
        mock_hist.return_value = go.Figure()
        mock_empty.return_value = go.Figure()
        
        # Call the function
        consolidated_name = 'catalog.schema.table'
        update_distribution_comparison(
            consolidated_name, 
            variable_data, 
            '2023-01-01', 
            '2023-02-01', 
            'count', 
            False
        )
        
        # Verify that parse_schema_properties was called with the full path and report_type
        mock_parse_schema_properties.assert_called_once_with(consolidated_name, report_type="mix")


@patch('utils.viz_functions.parse_schema_properties')
def test_update_distribution_comparison_histogram_view(mock_parse_schema_properties):
    """Test that update_distribution_comparison correctly handles histogram view."""
    # Setup mock parse_schema_properties
    mock_parse_schema_properties.return_value = ({
        'mix_type': 'Snapshot Date',
    }, 'catalog.schema.table')
    
    # Create mock variable data
    variable_data = {
        'variable': 'age_group',
        'distributions': {
            '2023-01-01': {'1': 0.5, '2': 0.5},
            '2023-02-01': {'1': 0.4, '2': 0.6}
        },
        'bucket_labels': {'1': 'Group 1', '2': 'Group 2'}
    }
    
    # Create patchers
    with patch('utils.viz_functions.create_histogram_figure') as mock_hist:
        # Mock return value
        mock_hist.return_value = go.Figure()
        
        # Call the function with histogram view (view_type = False)
        update_distribution_comparison(
            'catalog.schema.table', 
            variable_data, 
            '2023-01-01', 
            '2023-02-01', 
            'count', 
            False
        )
        
        # Verify that create_histogram_figure was called
        mock_hist.assert_called_once()
        
        # Check the df argument passed to create_histogram_figure
        df_arg = mock_hist.call_args[0][0]
        assert 'category' in df_arg.columns
        assert 'date1' in df_arg.columns
        assert 'date2' in df_arg.columns


@patch('utils.viz_functions.parse_schema_properties')
def test_update_distribution_comparison_mix_view(mock_parse_schema_properties):
    """Test that update_distribution_comparison correctly handles mix view."""
    # Setup mock parse_schema_properties
    mock_parse_schema_properties.return_value = ({
        'mix_type': 'Snapshot Date',
    }, 'catalog.schema.table')
    
    # Create mock variable data
    variable_data = {
        'variable': 'age_group',
        'distributions': {
            '2023-01-01': {'1': 0.5, '2': 0.5},
            '2023-02-01': {'1': 0.4, '2': 0.6},
            '2023-03-01': {'1': 0.3, '2': 0.7}
        },
        'bucket_labels': {'1': 'Group 1', '2': 'Group 2'}
    }
    
    # Create patchers
    with patch('utils.viz_functions.create_mix_figure') as mock_mix:
        # Mock return value
        mock_mix.return_value = go.Figure()
        
        # Call the function with mix view (view_type = True)
        update_distribution_comparison(
            'catalog.schema.table', 
            variable_data, 
            '2023-01-01', 
            '2023-02-01', 
            'count', 
            True
        )
        
        # Verify that create_mix_figure was called
        mock_mix.assert_called_once()
        
        # Check the arguments passed to create_mix_figure
        df_arg = mock_mix.call_args[0][0]
        all_dates = mock_mix.call_args[0][1]
        date1 = mock_mix.call_args[0][2]
        date2 = mock_mix.call_args[0][3]
        
        # Verify correct column structure and dates
        assert 'category' in df_arg.columns
        assert len(all_dates) == 3
        assert date1 == '2023-01-01'
        assert date2 == '2023-02-01'


@patch('utils.viz_functions.parse_schema_properties')
def test_update_distribution_comparison_error_handling(mock_parse_schema_properties):
    """Test error handling in update_distribution_comparison."""
    # Setup mock parse_schema_properties to return None (trigger error)
    mock_parse_schema_properties.return_value = (None, None)
    
    # Create mock variable data
    variable_data = {
        'variable': 'age_group',
        'distributions': {
            '2023-01-01': {'1': 0.5, '2': 0.5},
            '2023-02-01': {'1': 0.4, '2': 0.6}
        },
        'bucket_labels': {'1': 'Group 1', '2': 'Group 2'}
    }
    
    # Create patcher for create_empty_plot
    with patch('utils.viz_functions.create_empty_plot') as mock_empty:
        # Mock return value
        mock_empty.return_value = go.Figure()
        
        # Call the function
        update_distribution_comparison(
            'catalog.schema.table', 
            variable_data, 
            '2023-01-01', 
            '2023-02-01', 
            'count', 
            False
        )
        
        # Verify that create_empty_plot was called
        mock_empty.assert_called_once() 