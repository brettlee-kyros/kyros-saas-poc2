from ast import Raise
from datetime import datetime

# Dash imports
from dash import Output, Input, State, callback_context, no_update, html
from dash.exceptions import PreventUpdate

# Dash components
import dash_design_kit as ddk
import dash_bootstrap_components as dbc

# Common utilities
from kyros_plotly_common.logger import dash_logger
from kyros_plotly_common.utils.ui import create_empty_plot
from kyros_plotly_common.alerts.alert import create_alert
from kyros_plotly_common.layout.datagrid import create_grid, GridConfig

# Utility functions
from utils.bubbler_functions import create_column_definitions
from kyros_plotly_common.utils.ui import get_bar_renderer_config
from kyros_plotly_common.core.errors import BubblerError
from utils.helper_functions import (
    create_bubbler_signal_children,
)
from utils.dbx_utils import get_available_dates, get_segment_bubbler_data, get_variable_bubbler_data
from utils.viz_functions import update_distribution_comparison

# MixShift callbacks
ctx = callback_context

def update_segment_bubbler(consolidated_name, weight):
    """
    Update the segment bubbler based on the full path and weight
    
    Args:
        full_path: Full path to the table.
        weight: Weight column to use.
    """
    try:
        # Get segment data based on the full path and weight
        segments_data = get_segment_bubbler_data(consolidated_name, weight)
        
        if segments_data is None:
            return create_alert("No segments available for the selected data.", "warning")
        
        # Create custom configuration for weight column if needed
        # Example: Enable bar renderer for weight column
        # weight_bar_config = None
        # if weight and any(row.get("weight") for row in segments_data):
        #     weight_bar_config = get_bar_renderer_config(
        #         field="weight",
        #         max_value="auto",
        #         is_centered=False,  # Right-aligned bar
        #         color="#4CAF50"  # Green color
        #     )
            
        # Create column definitions for the grid with custom configuration
        column_defs = create_column_definitions(
            consolidated_name, 
            type="segment",
            tooltip_headers={
                "default": "Segment",
                "weight": "Weight"
            }
        )
        
        # Create the grid with a specific ID
        grid_config = GridConfig(
            id="segment-bubbler",
            column_defs=column_defs,
            row_data=segments_data,
            multi_select=True,
            selected_rows=[]
        )
        
        return create_grid(grid_config)
    except Exception as e:
        dash_logger.error(f"Error updating segment bubbler: {str(e)}")
        raise BubblerError(f"Error updating segment bubbler: {str(e)}", bubbler_type="segment")

def update_variable_bubbler(consolidated_name, selected_segments, date1, date2, weight, selected_variables, all_segments):
    """
    Update the variable bubbler based on the full path, selected segments, dates, and weight
    
    Args:
        full_path: Full path to the table.
        selected_segments: List of selected segments.
        date1: First date for comparison.
        date2: Second date for comparison.
        weight: Weight column to use.
        selected_variables: Previously selected variables to maintain selection.
    """
    try:
        # Get variable data based on all parameters
        variables_data = get_variable_bubbler_data(consolidated_name, selected_segments, date1, date2, weight, all_segments)
        
        if variables_data is None:
            return create_alert("No variables available for the selected segments and dates.", "warning")
        
        # Configure the bar renderer for KL Divergence
        kl_bar_config = get_bar_renderer_config(
            field="kl_divergence",
            max_value="auto",
            is_centered=False,
            color="#64B5F6"  # Blue color
        )
        
        # Create column definitions with custom configuration
        column_defs = create_column_definitions(
            consolidated_name, 
            type="variable",
            column_config=kl_bar_config,
            tooltip_headers={
                "variable": "Variable",
                "kl_divergence": "KL Divergence"
            }
        )
        
        if selected_variables:
            selected_variables = [variable for variable in variables_data if variable["variable"] in selected_variables[0]["variable"]]
        
        # Create the grid with a specific ID
        grid_config = GridConfig(
            id="variable-bubbler",
            column_defs=column_defs,
            row_data=variables_data,
            selected_rows=selected_variables,
            multi_select=False,
            side_bar=False
        )
        return create_grid(grid_config)
    except Exception as e:
        dash_logger.error(f"Error updating variable bubbler: {str(e)}")
        raise BubblerError(f"Error updating variable bubbler: {str(e)}", bubbler_type="variable")

def register_mixshift_callbacks(app):
    """
    Register all MixShift dashboard callbacks
    """

    # NOTE: The following callbacks have been moved to common.py:
    # - update_date_dropdown_callback
    # - validate_date_selections 
    # - update_weight_dropdown_callback
    # - update_date_validation_notification
    # - update_mix_type_display
    # - toggle_modal

    # Callback to handle segment selection
    @app.callback(
        Output("variable-table-container", "children", allow_duplicate=True),
        [State("db-store", "data"),
         Input("segment-bubbler", "selectedRows"),
         Input("date1-dd", "value"),
         Input("date2-dd", "value"),
         Input("weight-dd", "value"),
         State("selected-variables-store", "data"),
         State("segment-bubbler", "rowData")],
        prevent_initial_call=True,
    )
    def handle_variable_bubbler_update(consolidated_name, selected_segments, date1, date2, weight, selected_variables, all_segments):
        """
        Handle
        - segment selection in the segment bubbler.
        - date selection in the date dropdowns.
        - weight selection in the weight dropdown.
        
        Updates the variable bubbler based on the selected segment.
        """
        
        if not consolidated_name or not date1 or not date2 or not weight:
            raise PreventUpdate
        
        # Validate dates
        if date1 and date2 and date1 > date2:
            dash_logger.warning("Date validation error in variable bubbler update: Date 1 is later than Date 2")
            raise PreventUpdate
        
        return update_variable_bubbler(consolidated_name, selected_segments, date1, date2, weight, selected_variables, all_segments)
    
    @app.callback(
        Output("segment-selector-signal", "children"),
        Input("segment-bubbler", "selectedRows"),
        Input("segment-bubbler", "rowData"),
        prevent_initial_call=True,
    )
    def callback_gather_selected_segments(selected_rows, row_data):
        """
        Update selector signal based on selected segments
        """
        total_count = len(row_data) if row_data else None
        return create_bubbler_signal_children(selected_rows, "segment", total_count)
    
    @app.callback(
        Output("variable-selector-signal", "children"),
        Input("variable-bubbler", "selectedRows"),
        Input("variable-bubbler", "rowData"),
        prevent_initial_call=True,
    )
    def callback_gather_selected_variables(selected_rows, row_data):
        """
        Update selector signal based on selected variable
        """
        total_count = len(row_data) if row_data else None
        return create_bubbler_signal_children(selected_rows, "variable", total_count)
    
    @app.callback(
        Output("segment-bubbler", "selectedRows"),
        Input("segment-refresh-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def clear_selection(segment_n_clicks):
        if segment_n_clicks:
            return []
        raise PreventUpdate
    
    @app.callback(
        Output("segment-bubbler", "exportDataAsCsv"),
        Output("variable-bubbler", "exportDataAsCsv"),
        Input("segment-download-csv-button", "n_clicks"),
        Input("variable-download-csv-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def export_data_as_csv(segment_n_clicks, variable_n_clicks):
        if not ctx.triggered:
            raise PreventUpdate

        triggered = ctx.triggered_id
        if triggered.startswith("segment-download-csv-button"):
            return True, False
        return False, True
    
    # Callback to handle variable selection
    @app.callback(
        Output("mixshift-graph", "figure"),
        [
         State("db-store", "data"),
         Input("selected-variables-store", "data"),
         State("date1-dd", "value"),
         State("date2-dd", "value"),
         State("weight-dd", "value"),
         Input("view-toggle", "value")
         ],
        prevent_initial_call=True,
    )
    def handle_variable_selection(consolidated_name, selected_variables, date1, date2, weight, view_type):
        
        if not consolidated_name or not date1 or not date2 or not weight:
            raise PreventUpdate
        
        if not selected_variables:
            return create_empty_plot("Select characteristic")
        
        # Validate dates
        if date1 and date2 and date1 > date2:
            return create_empty_plot("Date 1 should be earlier than Date 2")
        
        if date1 == date2:
            return create_empty_plot("Please select different dates for comparison")
        
        # Update the distribution comparison
        figure = update_distribution_comparison(consolidated_name, selected_variables[0], date1, date2, weight, view_type)
        
        return figure

    # Callback for storing variable selection
    @app.callback(
        Output("selected-variables-store","data"),
        Input("variable-bubbler", "selectedRows"),
        prevent_initial_call=True,
    )
    def store_selected_variable_rows_data(selectedRows):
        return selectedRows

    @app.callback(
        Output("segment-table-container", "children"),
        [
            Input("db-store", "data"),
            Input("weight-dd", "value"),
        ],
        prevent_initial_call=True,
    )
    def callback_update_segment_bubbler(consolidated_name, weight):
        if not consolidated_name:
            raise PreventUpdate
        
        return update_segment_bubbler(consolidated_name, weight) 