"""
Tests for ui_helpers utility functions.
"""
import pytest
from unittest.mock import patch, MagicMock, call
from dash import html, no_update
from dash.exceptions import PreventUpdate

from utils.ui_helpers import (
    update_canvas_content,
    toggle_validation_modal,
    update_selected_schema,
    toggle_modal_logic,
    handle_deletion_modal_logic,
    update_date_validation_notification_logic,
    update_mix_type_display_logic
)


class TestUpdateCanvasContent:
    """Test cases for update_canvas_content function."""
    
    def test_update_canvas_content_no_trigger(self):
        """Test that function raises PreventUpdate when no trigger."""
        with patch('utils.ui_helpers.ctx') as mock_ctx:
            mock_ctx.triggered = False
            
            with pytest.raises(PreventUpdate):
                update_canvas_content(1, 0, 0, False)
    
    @patch('utils.ui_helpers.ctx')
    def test_update_canvas_content_open_button(self, mock_ctx):
        """Test opening canvas with open button."""
        mock_ctx.triggered = [{"prop_id": "catalog-open-button.n_clicks"}]
        
        result = update_canvas_content(1, 0, 0, False)
        
        assert result == (True, no_update, no_update)
    
    @patch('utils.ui_helpers.ctx')
    def test_update_canvas_content_close_button(self, mock_ctx):
        """Test closing canvas with close button."""
        mock_ctx.triggered = [{"prop_id": "close-offcanvas.n_clicks"}]
        
        result = update_canvas_content(0, 1, 0, True)
        
        assert result == (False, no_update, no_update)
    
    @patch('utils.ui_helpers.create_accordion_items')
    @patch('utils.ui_helpers.create_blade_structure')
    @patch('utils.ui_helpers.catalog_initializer')
    @patch('utils.ui_helpers.ctx')
    @patch('utils.ui_helpers.ddk')
    @patch('utils.ui_helpers.html')
    def test_update_canvas_content_refresh_button(self, mock_html, mock_ddk, mock_ctx, 
                                                 mock_catalog_init, mock_blade_struct, 
                                                 mock_accordion_items):
        """Test refreshing canvas with refresh button."""
        mock_ctx.triggered = [{"prop_id": "catalog-refresh-button.n_clicks"}]
        mock_catalog_init._nconvention_failure = []
        mock_blade_struct.return_value = "test_blade_struct"
        mock_accordion_items.return_value = "test_accordion_items"
        
        # Mock notification
        mock_notification = MagicMock()
        mock_ddk.Notification.return_value = mock_notification
        mock_html.Div.return_value = "test_notification_container"
        
        result = update_canvas_content(0, 0, 1, True)
        
        # Verify catalog was initialized
        mock_catalog_init.initialize_catalog.assert_called_once()
        
        # Check return values
        assert result[0] == no_update  # is_open unchanged
        assert result[1] == "test_accordion_items"  # blade content updated
        assert result[2] == "test_notification_container"  # notification container
    
    @patch('utils.ui_helpers.create_accordion_items')
    @patch('utils.ui_helpers.create_blade_structure') 
    @patch('utils.ui_helpers.catalog_initializer')
    @patch('utils.ui_helpers.ctx')
    @patch('utils.ui_helpers.ddk')
    @patch('utils.ui_helpers.html')
    def test_update_canvas_content_refresh_with_failures(self, mock_html, mock_ddk, mock_ctx,
                                                        mock_catalog_init, mock_blade_struct,
                                                        mock_accordion_items):
        """Test refresh with naming convention failures."""
        mock_ctx.triggered = [{"prop_id": "catalog-refresh-button.n_clicks"}]
        mock_catalog_init._nconvention_failure = ["invalid_table1", "invalid_table2"]
        mock_blade_struct.return_value = "test_blade_struct"
        mock_accordion_items.return_value = "test_accordion_items"
        
        # Mock notification components
        mock_notification = MagicMock()
        mock_ddk.Notification.return_value = mock_notification
        mock_html.Div.return_value = "test_div"
        mock_html.P.return_value = "test_p"
        mock_html.Code.return_value = "test_code"
        
        result = update_canvas_content(0, 0, 1, True)
        
        # Should create multiple notifications (success + failure)
        assert mock_ddk.Notification.call_count == 2
        
        # Check return values
        assert result[0] == no_update
        assert result[1] == "test_accordion_items"
        assert result[2] == "test_div"  # notification container
    
    @patch('utils.ui_helpers.ctx')
    def test_update_canvas_content_boolean_trigger(self, mock_ctx):
        """Test handling of boolean trigger (for tests)."""
        mock_ctx.triggered = True  # Boolean instead of list
        mock_ctx.triggered_id = "catalog-open-button"
        
        result = update_canvas_content(1, 0, 0, False)
        
        assert result == (True, no_update, no_update)
    
    @patch('utils.ui_helpers.ctx')
    def test_update_canvas_content_invalid_button(self, mock_ctx):
        """Test behavior with invalid button ID."""
        mock_ctx.triggered = [{"prop_id": "invalid-button.n_clicks"}]
        
        with pytest.raises(PreventUpdate):
            update_canvas_content(1, 0, 0, False)


class TestToggleValidationModal:
    """Test cases for toggle_validation_modal function."""
    
    @patch('utils.ui_helpers.ctx')
    def test_toggle_validation_modal_no_trigger(self, mock_ctx):
        """Test that function raises PreventUpdate when no trigger."""
        mock_ctx.triggered = False
        
        with pytest.raises(PreventUpdate):
            toggle_validation_modal([None, None])
    
    @patch('utils.ui_helpers.html')
    @patch('utils.ui_helpers.ctx')
    def test_toggle_validation_modal_success(self, mock_ctx, mock_html):
        """Test successful modal toggle."""
        mock_ctx.triggered = True
        mock_ctx.triggered_id = {"index": "test_table"}
        
        # Mock HTML elements
        mock_html.B.return_value = "bold_table_name"
        
        result = toggle_validation_modal([1, 0])
        
        # Should return modal open state, modal body, and selected table
        is_open, modal_body, selected_table = result
        
        assert is_open is True
        assert selected_table == "test_table"
        assert isinstance(modal_body, list)
        
        # Verify HTML.B was called with table name
        mock_html.B.assert_called_once_with("test_table")
    
    @patch('utils.ui_helpers.ctx')
    def test_toggle_validation_modal_all_none_clicks(self, mock_ctx):
        """Test behavior when all n_clicks are None."""
        mock_ctx.triggered = False
        
        with pytest.raises(PreventUpdate):
            toggle_validation_modal([None, None, None])


class TestUpdateSelectedSchema:
    """Test cases for update_selected_schema function."""
    
    @patch('utils.ui_helpers.ctx')
    def test_update_selected_schema_no_trigger(self, mock_ctx):
        """Test that function raises PreventUpdate when no trigger."""
        mock_ctx.triggered = False
        
        with pytest.raises(PreventUpdate):
            update_selected_schema([1, 0])
    
    @patch('utils.ui_helpers.html')
    @patch('utils.ui_helpers.ctx')
    def test_update_selected_schema_success(self, mock_ctx, mock_html):
        """Test successful schema selection."""
        mock_ctx.triggered = True
        mock_ctx.triggered_id = {"type": "table", "index": "cat__model__1__2023_01_01"}
        
        # Mock HTML elements
        mock_div = MagicMock()
        mock_label = MagicMock()
        mock_html.Div.return_value = mock_div
        mock_html.Label.return_value = mock_label
        
        result = update_selected_schema([1, 0])
        
        full_path, welcoming_style, main_skin_style, header = result
        
        assert full_path == "cat__model__1__2023_01_01"
        assert welcoming_style == {"display": "none"}
        assert main_skin_style == {"display": "block"}
        assert header == mock_div
        
        # No external name resolution is called; index is already consolidated_name
    
    @patch('utils.ui_helpers.ctx')
    def test_update_selected_schema_wrong_type(self, mock_ctx):
        """Test behavior when triggered element is wrong type."""
        mock_ctx.triggered = True
        mock_ctx.triggered_id = {"type": "not_table", "index": "catalog.schema.table"}
        
        with pytest.raises(PreventUpdate):
            update_selected_schema([1, 0])
    
    @patch('utils.ui_helpers.ctx')
    def test_update_selected_schema_no_triggered_id(self, mock_ctx):
        """Test behavior when no triggered_id."""
        mock_ctx.triggered = True
        mock_ctx.triggered_id = None
        
        with pytest.raises(PreventUpdate):
            update_selected_schema([1, 0])


class TestToggleModalLogic:
    """Test cases for toggle_modal_logic function."""
    
    def test_toggle_modal_logic_no_clicks(self):
        """Test behavior when n_clicks is None."""
        result = toggle_modal_logic(None, True)
        assert result is True
        
        result = toggle_modal_logic(None, False)
        assert result is False
        
        result = toggle_modal_logic(None, None)
        assert result is False
    
    def test_toggle_modal_logic_toggle(self):
        """Test modal toggling."""
        result = toggle_modal_logic(1, False)
        assert result is True
        
        result = toggle_modal_logic(2, True)
        assert result is False
        
        result = toggle_modal_logic(3, False)
        assert result is True


class TestHandleModalLogic:
    """Test cases for handle_deletion_modal_logic function."""
    
    @patch('utils.ui_helpers.ctx')
    def test_handle_deletion_modal_logic_no_trigger(self, mock_ctx):
        """Test that function raises PreventUpdate when no trigger."""
        mock_ctx.triggered = False
        
        with pytest.raises(PreventUpdate):
            handle_deletion_modal_logic(1, 0, "test_table")
    
    @patch('utils.ui_helpers.catalog_initializer')
    @patch('utils.ui_helpers.ctx')
    def test_handle_deletion_modal_logic_confirm_delete(self, mock_ctx, mock_catalog_initializer):
        """Test confirmation of delete operation."""
        mock_ctx.triggered = True
        mock_ctx.triggered_id = "confirm-delete"
        
        result = handle_deletion_modal_logic(1, 0, "test_table")
        
        # Should close modal, increment refresh, hide main skin, show welcoming, and stop loading (5 elements)
        expected = (False, 1, {"display": "none"}, {"display": "block"}, False)
        assert result == expected
        
        # Verify catalog_initializer.hide_tables was called
        mock_catalog_initializer.hide_tables.assert_called_once_with("test_table")
    
    @patch('utils.ui_helpers.ctx')
    def test_handle_deletion_modal_logic_cancel_delete(self, mock_ctx):
        """Test cancellation of delete operation."""
        mock_ctx.triggered = True
        mock_ctx.triggered_id = "cancel-delete"
        
        result = handle_deletion_modal_logic(0, 1, "test_table")
        
        # Should close modal, no refresh, no style change, no welcoming change, stop loading (5 elements)
        expected = (False, no_update, no_update, no_update, False)
        assert result == expected
    
    @patch('utils.ui_helpers.ctx')
    def test_handle_deletion_modal_logic_confirm_none_clicks(self, mock_ctx):
        """Test behavior when confirm clicks is None."""
        mock_ctx.triggered = True
        mock_ctx.triggered_id = "confirm-delete"
        
        with pytest.raises(PreventUpdate):
            handle_deletion_modal_logic(None, 0, "test_table")
    
    @patch('utils.ui_helpers.ctx')
    def test_handle_deletion_modal_logic_invalid_trigger(self, mock_ctx):
        """Test behavior with invalid trigger."""
        mock_ctx.triggered = True
        mock_ctx.triggered_id = "invalid-trigger"
        
        with pytest.raises(PreventUpdate):
            handle_deletion_modal_logic(1, 0, "test_table")


class TestUpdateDateValidationNotificationLogic:
    """Test cases for update_date_validation_notification_logic function."""
    
    def test_update_date_validation_no_full_path(self):
        """Test behavior when full_path is None."""
        result = update_date_validation_notification_logic("2023-01-01", "2023-02-01", None)
        assert result is None
        
        result = update_date_validation_notification_logic("2023-01-01", "2023-02-01", "")
        assert result is None
    
    def test_update_date_validation_no_dates(self):
        """Test behavior when dates are None."""
        result = update_date_validation_notification_logic(None, "2023-02-01", "test_path")
        assert result is None
        
        result = update_date_validation_notification_logic("2023-01-01", None, "test_path")
        assert result is None
    
    @patch('kyros_plotly_common.alerts.alert.create_alert')
    def test_update_date_validation_date1_later(self, mock_create_alert):
        """Test behavior when date1 is later than date2."""
        mock_alert = MagicMock()
        mock_create_alert.return_value = mock_alert
        
        result = update_date_validation_notification_logic("2023-02-01", "2023-01-01", "test_path")
        
        assert result == mock_alert
        mock_create_alert.assert_called_once_with(
            message="Date 1 should be earlier than Date 2",
            color="warning",
            icon="⚠️",
            position="top-right"
        )
    
    @patch('kyros_plotly_common.alerts.alert.create_alert')
    def test_update_date_validation_same_dates(self, mock_create_alert):
        """Test behavior when dates are the same."""
        mock_alert = MagicMock()
        mock_create_alert.return_value = mock_alert
        
        result = update_date_validation_notification_logic("2023-01-01", "2023-01-01", "test_path")
        
        assert result == mock_alert
        mock_create_alert.assert_called_once_with(
            message="Please select different dates for comparison",
            color="danger",
            icon="🚫",
            position="top-right"
        )
    
    @patch('kyros_plotly_common.utils.schema.parse_schema_properties')
    @patch('kyros_plotly_common.alerts.alert.create_alert')
    def test_update_date_validation_no_properties(self, mock_create_alert, mock_parse_schema_properties):
        """Test behavior when no properties found."""
        mock_parse_schema_properties.return_value = (None, None)
        mock_alert = MagicMock()
        mock_create_alert.return_value = mock_alert
        
        result = update_date_validation_notification_logic("2023-01-01", "2023-02-01", "test_path")
        
        assert result == mock_alert
        mock_create_alert.assert_called_once_with(
            message="Date range unavailable for the selected mix type",
            color="danger",
            icon="🚫",
            position="top-right"
        )
    
    @patch('kyros_plotly_common.utils.schema.parse_schema_properties')
    def test_update_date_validation_valid_dates(self, mock_parse_schema_properties):
        """Test behavior with valid dates and properties."""
        mock_parse_schema_properties.return_value = ({"date": "snapshot_date"}, 'catalog.schema.table')
        
        result = update_date_validation_notification_logic("2023-01-01", "2023-02-01", "test_path")
        
        assert result is None
    
    @patch('kyros_plotly_common.utils.schema.parse_schema_properties')
    @patch('kyros_plotly_common.alerts.alert.create_alert')
    @patch('kyros_plotly_common.logger.dash_logger')
    def test_update_date_validation_exception(self, mock_logger, mock_create_alert, mock_parse_schema_properties):
        """Test exception handling."""
        mock_parse_schema_properties.side_effect = Exception("Test error")
        mock_alert = MagicMock()
        mock_create_alert.return_value = mock_alert
        
        result = update_date_validation_notification_logic("2023-01-01", "2023-02-01", "test_path")
        
        assert result == mock_alert
        mock_create_alert.assert_called_once_with(
            message="Error validating dates: Test error",
            color="warning",
            icon="⚠️",
            position="top-right"
        )


class TestUpdateMixTypeDisplayLogic:
    """Test cases for update_mix_type_display_logic function."""
    
    def test_update_mix_type_display_no_full_path(self):
        """Test behavior when full_path is None or empty."""
        text, style = update_mix_type_display_logic(None)
        assert text == "No dataset selected"
        assert "color" in style
        assert style["color"] == "#ffc107"
        
        text, style = update_mix_type_display_logic("")
        assert text == "No dataset selected"
        assert "color" in style
        assert style["color"] == "#ffc107"
    
    @patch('kyros_plotly_common.utils.schema.get_from_redis')
    def test_update_mix_type_display_no_lookup_schemas(self, mock_get_redis):
        """Test behavior when no lookup schemas found."""
        mock_get_redis.return_value = None
        
        text, style = update_mix_type_display_logic("test_path")

        assert text == "Error loading Mix Type"
        assert "color" in style
        assert style["color"] == "#ffc107"
    
    @patch('kyros_plotly_common.utils.schema.get_from_redis')
    def test_update_mix_type_display_path_not_in_schemas(self, mock_get_redis):
        """Test behavior when path not in lookup schemas."""
        mock_get_redis.return_value = {"other_path": {"properties": {"mix_type": "Snapshot"}}}
        
        text, style = update_mix_type_display_logic("test_path")

        assert text == "Error loading Mix Type"
        assert "color" in style
        assert style["color"] == "#ffc107"
    
    @patch('kyros_plotly_common.utils.schema.get_from_redis')
    def test_update_mix_type_display_success(self, mock_get_redis):
        """Test successful mix type display."""
        # First call for lookup_mappings
        mock_lookup = {
            "test_path": {
                "mix": {
                    "properties": {"mix_type": "Snapshot Analysis"}
                }
            }
        }
        # Second call for table_mappings
        mock_table = {
            "test_path": {
                "mix": ["catalog.schema.table", "model__mix__1__2023_01_01"]
            }
        }
        mock_get_redis.side_effect = [mock_lookup, mock_table]
        
        text, style = update_mix_type_display_logic("test_path")
        
        assert text == "Snapshot Analysis"
        assert "display" in style
        assert "flex" in style
        # Should not have warning color
        assert "color" not in style or style.get("color") != "#ffc107"
    
    @patch('kyros_plotly_common.utils.schema.get_from_redis')
    def test_update_mix_type_display_no_mix_type(self, mock_get_redis):
        """Test behavior when mix_type not in properties."""
        mock_lookup = {
            "test_path": {
                "mix": {
                    "properties": {}
                }
            }
        }
        mock_table = {
            "test_path": {
                "mix": ["catalog.schema.table", "model__mix__1__2023_01_01"]
            }
        }
        mock_get_redis.side_effect = [mock_lookup, mock_table]
        
        text, style = update_mix_type_display_logic("test_path")

        assert text == "Error loading Mix Type"
    
    @patch('kyros_plotly_common.utils.schema.get_from_redis')
    @patch('kyros_plotly_common.logger.dash_logger')
    def test_update_mix_type_display_exception(self, mock_logger, mock_get_redis):
        """Test exception handling."""
        mock_get_redis.side_effect = Exception("Test error")
        
        text, style = update_mix_type_display_logic("test_path")
        
        assert text == "Error loading Mix Type"
        assert "color" in style
        assert style["color"] == "#ffc107"
        assert style["color"] == "#ffc107"