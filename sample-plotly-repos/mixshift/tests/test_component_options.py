"""
Tests for component_options utility functions.
"""
import pytest
from unittest.mock import patch
from datetime import date
from dash.exceptions import PreventUpdate

from utils.component_options import (
    update_weight_options,
    update_date_dropdown_callback_logic,
    update_weight_dropdown_callback_logic
)

class TestUpdateWeightOptions:
    """Test cases for update_weight_options function."""
    
    @patch('utils.component_options.parse_schema_properties')
    def test_update_weight_options_with_full_path(self, mock_parse_schema_properties):
        """Test that update_weight_options uses full path to get properties."""
        # Setup mock parse_schema_properties
        mock_parse_schema_properties.return_value = ({
            'weights': {
                'Member Count': 'count',
                'Points': 'points'
            }
        }, 'catalog.schema.table')
        
        # Call the function with full path
        consolidated_name = 'catalog.schema.table'
        result = update_weight_options(consolidated_name)
        
        # Verify that parse_schema_properties was called with the full path and report_type
        mock_parse_schema_properties.assert_called_once_with(consolidated_name, report_type="mix")
        
        # Check that the result contains the expected options
        assert len(result) == 2
        assert {"label": "Member Count", "value": "count"} in result
        assert {"label": "Points", "value": "points"} in result

    def test_update_weight_options_no_full_path(self):
        """Test that function raises PreventUpdate when full_path is None or empty."""
        with pytest.raises(PreventUpdate):
            update_weight_options(None)
        
        with pytest.raises(PreventUpdate):
            update_weight_options("")
    
    @patch('utils.component_options.parse_schema_properties')
    def test_update_weight_options_no_properties(self, mock_parse_schema_properties):
        """Test that function raises ValueError when no properties found."""
        mock_parse_schema_properties.return_value = (None, None)
        
        with pytest.raises(ValueError, match="No properties found for test_path"):
            update_weight_options("test_path")
    
    @patch('utils.component_options.parse_schema_properties')
    def test_update_weight_options_success(self, mock_parse_schema_properties):
        """Test successful weight options update."""
        mock_properties = {
            "weights": {
                "Member Count": "count", 
                "Earned Points": "earn",
                "Total Revenue": "revenue"
            }
        }
        mock_parse_schema_properties.return_value = (mock_properties, 'catalog.schema.table')
        
        result = update_weight_options("test_path")
        
        expected_options = [
            {"label": "Member Count", "value": "count"},
            {"label": "Earned Points", "value": "earn"},
            {"label": "Total Revenue", "value": "revenue"}
        ]
        
        assert result == expected_options
    
    @patch('utils.component_options.parse_schema_properties')
    @patch('utils.component_options.dash_logger')
    def test_update_weight_options_no_weights(self, mock_logger, mock_parse_schema_properties):
        """Test fallback when no weights in properties."""
        mock_properties = {"weights": None}
        mock_parse_schema_properties.return_value = (mock_properties, 'catalog.schema.table')
        
        result = update_weight_options("test_path")
        
        expected_options = [{"label": "Count", "value": "count"}]
        assert result == expected_options
        
        # Verify warning was logged
        mock_logger.warning.assert_called_once()
    
    @patch('utils.component_options.parse_schema_properties')
    @patch('utils.component_options.dash_logger')
    def test_update_weight_options_empty_weights(self, mock_logger, mock_parse_schema_properties):
        """Test fallback when weights dictionary is empty."""
        mock_properties = {"weights": {}}
        mock_parse_schema_properties.return_value = (mock_properties, 'catalog.schema.table')
        
        result = update_weight_options("test_path")
        
        expected_options = [{"label": "Count", "value": "count"}]
        assert result == expected_options
    
    @patch('utils.component_options.parse_schema_properties')
    @patch('utils.component_options.dash_logger')
    def test_update_weight_options_exception(self, mock_logger, mock_parse_schema_properties):
        """Test exception handling in update_weight_options."""
        mock_parse_schema_properties.side_effect = Exception("Test error")
        
        with pytest.raises(ValueError, match="Failed to update weight options: Test error"):
            update_weight_options("test_path")
        
        # Verify error was logged
        mock_logger.error.assert_called_once()


class TestUpdateDateDropdownCallbackLogic:
    """Test cases for update_date_dropdown_callback_logic function."""
    
    def test_update_date_dropdown_no_full_path(self):
        """Test that function raises PreventUpdate when full_path is None or empty."""
        with pytest.raises(PreventUpdate):
            update_date_dropdown_callback_logic(None)
        
        with pytest.raises(PreventUpdate):
            update_date_dropdown_callback_logic("")
    
    @patch('utils.component_options.parse_schema_properties')
    @patch('utils.component_options.create_alert')
    @patch('utils.component_options.dash_logger')
    def test_update_date_dropdown_no_properties(self, mock_logger, mock_alert, mock_parse_schema_properties):
        """Test behavior when no properties found."""
        mock_parse_schema_properties.return_value = (None, None)
        mock_alert.return_value = "test_notification"
        
        result = update_date_dropdown_callback_logic("test_path")
        
        # Should return disabled state with error notification
        expected = (
            [], [], "Date 1", "Date 2", "Mix Analysis", None, None, 
            True, True,
            "Date range unavailable for the selected mix type",
            "Date range unavailable for the selected mix type",
            "test_notification"
        )
        
        assert result == expected
        mock_logger.error.assert_called_once()
        mock_alert.assert_called_once()
    
    @patch('utils.component_options.parse_schema_properties')
    @patch('utils.component_options.create_alert')
    @patch('utils.component_options.dash_logger')
    def test_update_date_dropdown_no_date_column(self, mock_logger, mock_alert, mock_parse_schema_properties):
        """Test behavior when no date column in properties."""
        mock_properties = {"mix_type": "Snapshot", "date": ""}
        mock_parse_schema_properties.return_value = (mock_properties, 'catalog.schema.table')
        mock_alert.return_value = "test_notification"
        
        result = update_date_dropdown_callback_logic("test_path")
        
        # Should return disabled state with error notification
        expected = (
            [], [], "Date 1", "Date 2", "Snapshot Mix Analysis", None, None, 
            True, True,
            "Date range unavailable for the selected mix type",
            "Date range unavailable for the selected mix type",
            "test_notification"
        )
        
        assert result == expected
        mock_logger.error.assert_called_once()
        mock_alert.assert_called_once()
    
    @patch('utils.component_options.get_available_dates')
    @patch('utils.component_options.parse_schema_properties')
    @patch('utils.component_options.create_alert')
    @patch('utils.component_options.dash_logger')
    def test_update_date_dropdown_insufficient_dates(self, mock_logger, mock_alert, mock_parse_schema_properties, mock_get_dates):
        """Test behavior when insufficient dates available."""
        mock_properties = {"mix_type": "Snapshot", "date": "snapshot_date"}
        mock_parse_schema_properties.return_value = (mock_properties, 'catalog.schema.table')
        mock_get_dates.return_value = [date(2023, 1, 1)]  # Only one date
        mock_alert.return_value = "test_notification"
        
        result = update_date_dropdown_callback_logic("test_path")
        
        # Should return disabled state with warning notification
        expected = (
            [], [], "Date 1", "Date 2", "Snapshot Mix Analysis", None, None, 
            True, True,
            "Not enough dates available for comparison",
            "Not enough dates available for comparison",
            "test_notification"
        )
        
        assert result == expected
        mock_logger.error.assert_called_once()
        mock_alert.assert_called_once()
    
    @patch('utils.component_options.create_date_dropdown_options')
    @patch('utils.component_options.get_available_dates')
    @patch('utils.component_options.parse_schema_properties')
    def test_update_date_dropdown_success(self, mock_parse_schema_properties, mock_get_dates, mock_create_options):
        """Test successful date dropdown update."""
        mock_properties = {"mix_type": "Snapshot", "date": "snapshot_date"}
        mock_parse_schema_properties.return_value = (mock_properties, 'catalog.schema.table')
        
        dates = [date(2023, 1, 1), date(2023, 2, 1), date(2023, 3, 1)]
        mock_get_dates.return_value = dates
        
        date_options = [
            {"label": "2023-01-01", "value": "2023-01-01"},
            {"label": "2023-02-01", "value": "2023-02-01"},
            {"label": "2023-03-01", "value": "2023-03-01"}
        ]
        mock_create_options.return_value = date_options
        
        result = update_date_dropdown_callback_logic("test_path")
        
        expected = (
            date_options, date_options,
            "Snapshot 1", "Snapshot 2",
            "Snapshot Mix Analysis",
            date(2023, 3, 1), date(2023, 1, 1),  # Last date as date1, first as date2
            False, False,
            "Select the base snapshot for comparison",
            "Select the target snapshot for comparison",
            None
        )
        
        assert result == expected
    
    @patch('utils.component_options.parse_schema_properties')
    @patch('utils.component_options.create_alert')
    @patch('utils.component_options.dash_logger')
    def test_update_date_dropdown_exception(self, mock_logger, mock_alert, mock_parse_schema_properties):
        """Test exception handling in update_date_dropdown_callback_logic."""
        mock_parse_schema_properties.side_effect = Exception("Test error")
        mock_alert.return_value = "test_notification"
        
        result = update_date_dropdown_callback_logic("test_path")
        
        # Should return disabled state with error notification
        expected = (
            [], [], "Date 1", "Date 2", "Mix Analysis", None, None, 
            True, True,
            "An error occurred",
            "An error occurred",
            "test_notification"
        )
        
        assert result == expected
        mock_logger.error.assert_called_once()
        mock_alert.assert_called_once()


class TestUpdateWeightDropdownCallbackLogic:
    """Test cases for update_weight_dropdown_callback_logic function."""
    
    def test_update_weight_dropdown_no_full_path(self):
        """Test that function raises PreventUpdate when full_path is None or empty."""
        with pytest.raises(PreventUpdate):
            update_weight_dropdown_callback_logic(None)
        
        with pytest.raises(PreventUpdate):
            update_weight_dropdown_callback_logic("")
    
    @patch('utils.component_options.update_weight_options')
    @patch('utils.component_options.dash_logger')
    def test_update_weight_dropdown_success(self, mock_logger, mock_update_weights):
        """Test successful weight dropdown update."""
        weight_options = [
            {"label": "Member Count", "value": "count"},
            {"label": "Earned Points", "value": "earn"}
        ]
        mock_update_weights.return_value = weight_options
        
        result = update_weight_dropdown_callback_logic("test_path")
        
        expected = (weight_options, "count")
        assert result == expected
        
        # Verify logging
        mock_logger.info.assert_any_call(f"Weight options for test_path: {weight_options}")
        mock_logger.info.assert_any_call("Default weight value: count")
    
    @patch('utils.component_options.update_weight_options')
    @patch('utils.component_options.dash_logger')
    def test_update_weight_dropdown_empty_options(self, mock_logger, mock_update_weights):
        """Test behavior when no weight options returned."""
        mock_update_weights.return_value = []
        
        result = update_weight_dropdown_callback_logic("test_path")
        
        expected = ([], None)
        assert result == expected
    
    @patch('utils.component_options.update_weight_options')
    @patch('utils.component_options.dash_logger')
    def test_update_weight_dropdown_exception(self, mock_logger, mock_update_weights):
        """Test exception handling in update_weight_dropdown_callback_logic."""
        mock_update_weights.side_effect = Exception("Test error")
        
        result = update_weight_dropdown_callback_logic("test_path")
        
        # Should return fallback options
        expected = ([{"label": "Count", "value": "count"}], "count")
        assert result == expected
        
        # Verify error was logged
        mock_logger.error.assert_called_once() 