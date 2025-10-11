"""
Tests for the database utility functions.
"""
from unittest.mock import patch
import pandas as pd

from utils.dbx_utils import build_minimized_segment_where_clause

# Import the actual functions to patch
import utils.dbx_utils



@patch('utils.dbx_utils.parse_schema_properties')
def test_get_weight_options(mock_parse_schema_properties):
    """Test that get_weight_options correctly uses full path to get properties."""
    # Setup mock parse_schema_properties return
    mock_parse_schema_properties.return_value = ({
        'weights': {
            'Member Count': 'count',
            'Points': 'points'
        }
    }, 'catalog.schema.table')

    # Call the function directly
    result = utils.dbx_utils.get_weight_options('catalog.schema.table')
    
    # Expected output
    expected = [
        {'label': 'Member Count', 'value': 'count'},
        {'label': 'Points', 'value': 'points'}
    ]
    
    # Assertions - we don't care about the order
    assert len(result) == len(expected)
    assert all(item in result for item in expected)
    
    # Check that parse_schema_properties was called with the full path
    mock_parse_schema_properties.assert_called_once_with('catalog.schema.table', report_type="mix")

@patch('utils.dbx_utils.parse_schema_properties')
@patch('utils.dbx_utils.dbx_client')
def test_get_segment_bubbler_data(mock_dbx_client, mock_parse_schema_properties):
    """Test that get_segment_bubbler_data correctly uses full path for querying."""
    
    # Setup mock returns
    mock_parse_schema_properties.return_value = ({
        'segments': {
            'Region': 'region',
            'Age Group': 'age_group'
        },
        'date': 'date_column'
    }, 'catalog.schema.table')

    # Mock the database query return
    mock_df = pd.DataFrame({
        'region': ['North', 'South'],
        'age_group': ['18-24', '25-34'],
        'weight': [100, 200]
    })
    mock_dbx_client.run_query.return_value = mock_df

    # Call the function directly (with decorator)
    result = utils.dbx_utils.get_segment_bubbler_data('catalog.schema.table', 'count')

    # Verify that dbx_client.run_query was called
    mock_dbx_client.run_query.assert_called_once()
    
    # Verify the query contains the full path
    query = mock_dbx_client.run_query.call_args[0][0]
    assert 'catalog.schema.table' in query
    
    # Check the format of the result
    assert isinstance(result, list)
    assert len(result) == 2  # Same as mock_df rows
    
    # Check that parse_schema_properties was called with full path
    mock_parse_schema_properties.assert_called_once_with('catalog.schema.table', report_type="mix")

def test_get_variable_bubbler_data():
    """Test that get_variable_bubbler_data correctly uses full path for querying."""
    
    # Setup mock returns with correct field names
    variable_column = 'variable'
    bucket_id = 'bucket_id'
    bucket_name = 'bucket_name'
    
    # Create patchers
    dbx_patcher = patch('utils.dbx_utils.dbx_client')
    get_properties_patcher = patch('utils.dbx_utils.parse_schema_properties')
    
    # Start patchers
    mock_dbx_client = dbx_patcher.start()
    mock_parse_schema_properties = get_properties_patcher.start()
    
    try:
        # Setup mock returns
        mock_parse_schema_properties.return_value = ({
            'date': 'date_column',
            'variable': variable_column,
            'bucket_id': bucket_id,
            'bucket_name': bucket_name
        }, 'catalog.schema.table')
        
        # Mock selected segments
        selected_segments = [
            {
                'segment_values': {
                    'region': 'North'
                }
            }
        ]
        
        all_segments = [
            {
                'segment_values': {
                    'region': 'North'
                }
            },
            {
                'segment_values': {
                    'region': 'South'
                }
            },
            {
                'segment_values': {
                    'region': 'East'
                }
            }
        ]
        
        # Mock the database query returns
        variables_df = pd.DataFrame({
            variable_column: ['var1', 'var2'],
            'kl_divergence': [0.1, 0.2],
            'date1_weight': [100, 200],
            'date2_weight': [150, 250],
            'all_distributions': [
                {'2023-01-01': {'1': 0.5, '2': 0.5}, '2023-02-01': {'1': 0.4, '2': 0.6}},
                {'2023-01-01': {'1': 0.3, '2': 0.7}, '2023-02-01': {'1': 0.2, '2': 0.8}}
            ]
        })
        
        labels_df = pd.DataFrame({
            variable_column: ['var1', 'var1', 'var2', 'var2'],
            bucket_id: ['1', '2', '1', '2'],
            bucket_name: ['Category A', 'Category B', 'Category A', 'Category B']
        })
        
        # Setup mock to return different values on different calls
        mock_dbx_client.run_query.side_effect = [variables_df, labels_df]
        
        # Call the function directly (with decorator)
        result = utils.dbx_utils.get_variable_bubbler_data(
            'catalog.schema.table',
            selected_segments,
            '2023-01-01',
            '2023-02-01',
            'count',
            all_segments
        )
        
        # Check the format of the result
        assert isinstance(result, list)
        
        # Check structure of result items (we may get empty results due to mocking)
        # But the important thing is that get_properties was called with the full path
        mock_parse_schema_properties.assert_called_once_with('catalog.schema.table', report_type="mix")
        
        # Verify dbx_client was used with the full path
        assert mock_dbx_client.run_query.call_count >= 1
        
        # Check at least one query contains the full path
        calls = mock_dbx_client.run_query.call_args_list
        assert any('catalog.schema.table' in str(call) for call in calls)
    
    finally:
        # Stop patchers
        dbx_patcher.stop()
        get_properties_patcher.stop()


class TestBuildMinimizedSegmentWhereClause:
    """Test class for the build_minimized_segment_where_clause function."""
    
    def test_empty_segments(self):
        """Test with empty segments list."""
        result = build_minimized_segment_where_clause([], [])
        assert result == ""
    
    def test_single_segment_single_condition(self):
        """Test with a single segment having one condition."""
        segments = [
            {"segment_values": {"region": "North"}}
        ]
        result = build_minimized_segment_where_clause(segments, segments)
        assert result == "AND (region = 'North')"
    
    def test_single_segment_multiple_conditions(self):
        """Test with a single segment having multiple conditions."""
        segments = [
            {"segment_values": {"region": "North", "age_group": "25-34"}}
        ]
        result = build_minimized_segment_where_clause(segments, segments)
        # Should factor out common conditions
        assert "AND (" in result
        assert "region = 'North'" in result
        assert "age_group = '25-34'" in result
        assert " AND " in result
    
    def test_multiple_segments_same_values(self):
        """Test with multiple segments having identical values (should factor out)."""
        segments = [
            {"segment_values": {"region": "North", "age_group": "25-34"}},
            {"segment_values": {"region": "North", "age_group": "25-34"}}
        ]
        result = build_minimized_segment_where_clause(segments, segments)
        # Should factor out the common conditions
        assert "AND (" in result
        assert "region = 'North'" in result
        assert "age_group = '25-34'" in result
        assert " AND " in result
    
    def test_complex_factoring_scenario(self):
        """Test complex scenario with partial factoring."""
        segments = [
            {"segment_values": {"country": "USA", "region": "North", "age_group": "25-34"}},
            {"segment_values": {"country": "USA", "region": "South", "age_group": "25-34"}},
            {"segment_values": {"country": "USA", "region": "North", "age_group": "35-44"}}
        ]
        result = build_minimized_segment_where_clause(segments, segments)
        # Should factor out country (common to all)
        assert "AND (" in result
        assert "country = 'USA'" in result
        # Should have varying conditions for region and age_group
        assert "region = 'North'" in result or "region = 'South'" in result
        assert "age_group = '25-34'" in result or "age_group = '35-44'" in result
    
    def test_segments_with_missing_segment_values(self):
        """Test with segments missing segment_values key."""
        segments = [
            {"segment_values": {"region": "North"}},
            {"other_key": "value"},  # Missing segment_values
            {"segment_values": {"region": "South"}}
        ]
        # Should ignore segments without segment_values
        result = build_minimized_segment_where_clause(segments, segments)
        assert "AND (" in result
        assert "region" in result
    
    def test_segments_with_empty_segment_values(self):
        """Test with segments having empty segment_values."""
        segments = [
            {"segment_values": {"region": "North"}},
            {"segment_values": {}},  # Empty segment_values
            {"segment_values": {"region": "South"}}
        ]
        result = build_minimized_segment_where_clause(segments, segments)
        # Should ignore empty segment_values
        assert "AND (" in result
        assert "region" in result
    
    def test_three_way_branching(self):
        """Test scenario with three different values for same field."""
        segments = [
            {"segment_values": {"region": "North"}},
            {"segment_values": {"region": "South"}},
            {"segment_values": {"region": "East"}}
        ]
        result = build_minimized_segment_where_clause(segments, segments)
        # Should create IN condition with all three values
        assert "AND (" in result
        assert "region IN ('North', 'South', 'East')" in result
    
    def test_nested_factoring_with_multiple_levels(self):
        """Test deep nesting scenario with multiple levels of factoring."""
        segments = [
            {"segment_values": {"country": "USA", "state": "CA", "city": "LA"}},
            {"segment_values": {"country": "USA", "state": "CA", "city": "SF"}},
            {"segment_values": {"country": "USA", "state": "NY", "city": "NYC"}},
            {"segment_values": {"country": "USA", "state": "NY", "city": "Buffalo"}}
        ]
        result = build_minimized_segment_where_clause(segments, segments)
        # Should factor out country (common to all)
        assert "AND (" in result
        assert "country = 'USA'" in result
        # Should have proper nesting for state and city
        assert "state = 'CA'" in result or "state = 'NY'" in result
        assert "city IN (" in result
    
    def test_single_segment_empty_values(self):
        """Test with a single segment having empty segment_values."""
        segments = [
            {"segment_values": {}}
        ]
        result = build_minimized_segment_where_clause(segments, segments)
        assert result == ""
    
    def test_segments_with_none_values(self):
        """Test segments with None values in segment_values."""
        segments = [
            {"segment_values": {"region": "North", "age_group": None}},
            {"segment_values": {"region": "South", "age_group": "25-34"}}
        ]
        result = build_minimized_segment_where_clause(segments, segments)
        # Should ignore segments with None values
        assert "AND (" in result
        assert "region = 'South'" in result
        assert "age_group = '25-34'" in result
    
    def test_all_segments_key_order(self):
        """Test that key order from all_segments is respected."""
        selected = [
            {"segment_values": {"b": 1, "a": 2}}
        ]
        all_segments = [
            {"segment_values": {"a": 1, "b": 2}}
        ]
        result = build_minimized_segment_where_clause(selected, all_segments)
        # Keys should appear in all_segments order (a, b)
        assert result.index("a") < result.index("b")