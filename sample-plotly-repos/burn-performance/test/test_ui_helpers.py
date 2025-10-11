import pytest
from unittest.mock import patch, MagicMock
from dash import html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from utils.ui_helpers import (
    render_control_ribbon,
    render_diagnostic_graphs,
    create_cluster_signal_children,
    create_hierarchy_signal_children,
    toggle_modal,
    format_display_values,
    ControlComponentStyles,
    DynamicLayoutComponentStyles
)

def test_render_control_ribbon_performance_tab():
    expected_styles = ControlComponentStyles(
        empty_placeholder={"display": "none"},
        currentdate_info_textbox={"display": "block"},
        actual_radio={"display": "block"},
        mask_radio={"display": "block"},
        monitoring_dropdown={"display": "block"},
        target_dropddown={"display": "block"},
        stats_settings_button={"display": "block"},
        age_slider={"display": "block"},
        tm5_info_button={"display": "none"},
    )
    assert render_control_ribbon("performance") == expected_styles

def test_render_control_ribbon_characteristics_tab():
    expected_styles = ControlComponentStyles(
        empty_placeholder={"display": "none"},
        currentdate_info_textbox={"display": "none"},
        actual_radio={"display": "none"},
        mask_radio={"display": "none"},
        monitoring_dropdown={"display": "block"},
        target_dropddown={"display": "none"},
        stats_settings_button={"display": "none"},
        age_slider={"display": "none"},
        tm5_info_button={"display": "block"},
    )
    assert render_control_ribbon("characteristics") == expected_styles

def test_render_control_ribbon_invalid_tab():
    with pytest.raises(PreventUpdate):
        render_control_ribbon(None)
    with pytest.raises(PreventUpdate):
        render_control_ribbon("invalid_tab") # Assuming it should raise for unknown tabs

def test_render_diagnostic_graphs_performance_tab():
    expected_styles = DynamicLayoutComponentStyles(
        callouts_div={"height": "12%", "margin-bottom": "10px"},
        tm2_graph={"height": "calc(70% - 10px)", "margin-bottom": "10px"},
        exposures_bar_graph={"height": "calc(18% - 10px)", "margin-bottom": "10px"},
        tm5_graphs={"display": "none"},
    )
    assert render_diagnostic_graphs("performance") == expected_styles

def test_render_diagnostic_graphs_characteristics_tab():
    expected_styles = DynamicLayoutComponentStyles(
        callouts_div={"display": "none"},
        tm2_graph={"display": "none"},
        exposures_bar_graph={"display": "none"},
        tm5_graphs={"height": "100%", "margin-bottom": "10px"},
    )
    assert render_diagnostic_graphs("characteristics") == expected_styles

def test_render_diagnostic_graphs_invalid_tab():
    with pytest.raises(PreventUpdate):
        render_diagnostic_graphs(None)
    with pytest.raises(PreventUpdate):
        render_diagnostic_graphs("invalid_tab") # Assuming it should raise for unknown tabs

def test_create_cluster_signal_children():
    mock_icon = html.Div("Mock Icon")
    signal_config = {"icon": "test-icon", "color": "blue", "tooltip": "Test Tooltip"}
    
    with patch('utils.ui_helpers.get_icon', return_value=mock_icon) as mock_get_icon:
        children = create_cluster_signal_children(signal_config)
        
        assert len(children) == 2
        assert isinstance(children[0], html.Div)
        assert children[0].id == "selector-signal-icon"
        mock_get_icon.assert_called_once_with("test-icon", 30, color="blue")
        
        assert isinstance(children[1], dbc.Tooltip)
        assert children[1].children == "Test Tooltip"
        assert children[1].target == "selector-signal-icon"

def test_create_hierarchy_signal_children():
    mock_icon = html.Div("Mock Icon")
    signal_config = {"icon": "hierarchy-icon", "tooltip": "Hierarchy Tooltip"}
    
    with patch('utils.ui_helpers.get_icon', return_value=mock_icon) as mock_get_icon:
        children = create_hierarchy_signal_children(signal_config)
        
        assert len(children) == 2
        assert isinstance(children[0], html.Div)
        assert children[0].id == "hierarchy-signal-icon"
        mock_get_icon.assert_called_once_with("hierarchy-icon", 23) # Default color
        
        assert isinstance(children[1], dbc.Tooltip)
        assert children[1].children == "Hierarchy Tooltip"
        assert children[1].target == "hierarchy-signal-icon"

def test_toggle_modal():
    assert toggle_modal(n_clicks=1, is_open=False) is True
    assert toggle_modal(n_clicks=1, is_open=True) is False
    assert toggle_modal(n_clicks=None, is_open=True) is True
    assert toggle_modal(n_clicks=None, is_open=False) is False
    assert toggle_modal(n_clicks=None, is_open=None) is False

@pytest.mark.parametrize("value, format_type, precision, expected", [
    (1234.5678, "number", 4, 1234.5678),
    (1234.5678, "number", 2, 1234.57),
    (1234, "currency", 4, "$1,234"), # Precision is ignored for currency
    (1234567, "large_number", 4, "1,234,567"), # Precision is ignored
    (None, "number", 4, " - "),
    ("test", "unknown", 4, "test"), # Unknown format_type returns value as is
    (10.123, "number", 0, 10.0), 
])
def test_format_display_values(value, format_type, precision, expected):
    assert format_display_values(value, format_type, precision) == expected

def test_format_display_values_default_parameters():
    assert format_display_values(12.3456) == 12.3456 # Default type="number", precision=4
    assert format_display_values(12.3456, precision=2) == 12.35 