"""
UI helper functions for dashboard components.
"""
from typing import Dict, NamedTuple
from dash import html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from kyros_plotly_common.utils.ui import get_icon

class ControlComponentStyles(NamedTuple):
    empty_placeholder: Dict[str, str]
    currentdate_info_textbox: Dict[str, str]
    actual_radio: Dict[str, str]
    mask_radio: Dict[str, str]
    monitoring_dropdown: Dict[str, str]
    target_dropddown: Dict[str, str]
    age_slider: Dict[str, str]
    tm5_info_button: Dict[str, str]
    stats_settings_button: Dict[str, str]

class DynamicLayoutComponentStyles(NamedTuple):
    callouts_div: Dict[str, str]
    tm2_graph: Dict[str, str]
    exposures_bar_graph: Dict[str, str]
    tm5_graphs: Dict[str, str]

def render_control_ribbon(tab):
    """
    Render the control ribbon UI components based on the active tab.
    
    Args:
        tab (str): The active tab identifier ('performance' or 'characteristics')
        
    Returns:
        ControlComponentStyles: Named tuple with style specifications for each control component
    """
    if not tab:
        raise PreventUpdate

    if tab == "performance":
        return ControlComponentStyles(
            empty_placeholder = {"display": "none"},
            currentdate_info_textbox = {"display": "block"},
            actual_radio = {"display": "block"},
            mask_radio = {"display": "block"},
            monitoring_dropdown ={"display": "block"},
            target_dropddown = {"display": "block"},
            age_slider = {"display": "block"},
            tm5_info_button = {"display": "none"},
            stats_settings_button = {"display": "block"},
        )
    elif tab == "characteristics":
        return ControlComponentStyles(
            empty_placeholder = {"display": "none"},
            currentdate_info_textbox = {"display": "none"},
            actual_radio = {"display": "none"},
            mask_radio = {"display": "none"},
            monitoring_dropdown = {"display": "block"},
            target_dropddown = {"display": "none"},
            age_slider = {"display": "none"},
            tm5_info_button = {"display": "block"},
            stats_settings_button = {"display": "none"},
        )
    raise PreventUpdate

def render_diagnostic_graphs(tab):
    """
    Render the diagnostic graphs layout based on the active tab.
    
    Args:
        tab (str): The active tab identifier ('performance' or 'characteristics')
        
    Returns:
        DynamicLayoutComponentStyles: Named tuple with style specifications for layout components
    """
    if not tab:
        raise PreventUpdate
    
    elif tab == "performance":
        return DynamicLayoutComponentStyles(
            callouts_div = {"height": "12%",  "margin-bottom": "10px"},
            tm2_graph = {"height": "calc(70% - 10px)", "margin-bottom": "10px"},
            exposures_bar_graph = {"height": "calc(18% - 10px)", "margin-bottom": "10px"},
            tm5_graphs = {"display": "none"},
        )
        
    elif tab == "characteristics":
        return DynamicLayoutComponentStyles(
            callouts_div = {"display": "none"},
            tm2_graph = {"display": "none"},
            exposures_bar_graph = {"display": "none"},
            tm5_graphs = {"height": "100%", "margin-bottom": "10px"},
        )
    raise PreventUpdate

def create_cluster_signal_children(signal_config):
    """
    Create signal indicator for cluster selection.
    
    Args:
        signal_config (dict): Configuration with icon, color, and tooltip text
        
    Returns:
        list: Children components for signal display
    """
    return [
        html.Div(
            id="selector-signal-icon",
            children=get_icon(signal_config["icon"], 30, color=signal_config.get("color", None)),
        ),
        dbc.Tooltip(
            signal_config["tooltip"],
            id="clusters-tooltip",
            placement="left",
            target="selector-signal-icon",
            trigger="hover focus",
        ),
    ]

def create_hierarchy_signal_children(signal_config):
    """
    Create signal indicator for hierarchy level.
    
    Args:
        signal_config (dict): Configuration with icon and tooltip text
        
    Returns:
        list: Children components for signal display
    """
    return [
        html.Div(
            id="hierarchy-signal-icon",
            children=get_icon(signal_config["icon"], 23),
        ),
        dbc.Tooltip(
            signal_config["tooltip"],
            id="hierarchy-tooltip",
            placement="left",
            target="hierarchy-signal-icon",
            trigger="hover focus",
        ),
    ]

def toggle_modal(n_clicks, is_open):
    """
    Toggle the state of a modal dialog.
    
    Args:
        n_clicks (int): Number of clicks on the toggle button
        is_open (bool): Current state of the modal
        
    Returns:
        bool: Updated state of the modal
    """
    if n_clicks is None:
        return False if is_open is None else is_open
    return not is_open

def format_display_values(value, format_type="number", precision=4):
    """
    Format display values for UI display with proper formatting.
    
    Args:
        value: The value to format
        format_type (str): Type of formatting ('number', 'currency', etc.)
        precision (int): Decimal precision
        
    Returns:
        str: Formatted value string
    """
    if value is None:
        return " - "
        
    if format_type == "number":
        return round(value, precision)
    elif format_type == "currency":
        return "${:,}".format(int(value))
    elif format_type == "large_number":
        return "{:,.0f}".format(value)
        
    return value 