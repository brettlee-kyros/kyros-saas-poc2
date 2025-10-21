"""
Component options utility functions for building dropdown and form controls.

This module contains functions for building dropdown options and managing
component configurations for the MixShift dashboard.
"""

from datetime import datetime
from dash.exceptions import PreventUpdate
from kyros_plotly_common.logger import dash_logger
from kyros_plotly_common.utils.schema import parse_schema_properties
from kyros_plotly_common.utils.ui import create_date_dropdown_options
from kyros_plotly_common.alerts.alert import create_alert
from utils.dbx_utils import get_available_dates


def update_weight_options(consolidated_name):
    """
    Update weight dropdown options based on mix type and metadata properties
    
    Args:
        full_path: Full path to the table.
    """
    if not consolidated_name:
        raise PreventUpdate
    
    try:
        # Get properties to access weight definitions
        properties, _ = parse_schema_properties(consolidated_name,report_type="mix")
        if not properties:
            raise ValueError(f"No properties found for {consolidated_name}")
        
        # Get weights from properties
        weights = properties["weights"]
        
        if not weights:
            dash_logger.warning(f"No weights found in properties for {consolidated_name}. Using fallback weights.")
            weight_options = [{"label": "Count", "value": "count"}]
        else:
            # Convert weights dictionary to dropdown options
            # Format in metadata: {"Member Count": "count", "Earned Points": "earn", ...}
            weight_options = [{"label": label, "value": column} for label, column in weights.items()]
            
            # If no weights are found, add a default option
            if not weight_options:
                weight_options = [{"label": "Count", "value": "count"}]
        
        return weight_options
    
    except Exception as e:
        error_msg = f"Failed to update weight options: {e}"
        error_id = dash_logger.error(error_msg, exc_info=e)
        raise ValueError(error_msg)


def update_date_dropdown_callback_logic(consolidated_name):
    """
    Update the date dropdown options based on the full path
    
    Args:
        full_path: Full path to the table.
        
    Returns:
        tuple: (
            date1_options,
            date2_options,
            date1_label,
            date2_label,
            title,
            date1_value,
            date2_value,
            date1_disabled,
            date2_disabled,
            date1_tooltip,
            date2_tooltip,
            notification
        )
    """
    if not consolidated_name:
        raise PreventUpdate
        
    try:
        # Get properties for the full path
        properties, _ = parse_schema_properties(consolidated_name,report_type="mix")
        if not properties:
            error_msg = f"No properties found for {consolidated_name}"
            dash_logger.error(error_msg)
            notification = create_alert(
                message="Date range unavailable for the selected mix type",
                color="danger",
                icon="🚫",
                position="top-right"
            )
            return (
                [], [], "Date 1", "Date 2", "Mix Analysis", None, None, 
                True, True,
                "Date range unavailable for the selected mix type",
                "Date range unavailable for the selected mix type",
                notification
            )
        
        # Get mix type from properties
        mix_type = properties.get("mix_type", "Unknown")
        
        # Get date column from properties
        date_column = properties.get("date", "")
        if not date_column:
            error_msg = f"No date column found in properties for {consolidated_name}"
            dash_logger.error(error_msg)
            notification = create_alert(
                message="Date column metadata is missing",
                color="danger",
                icon="🚫",
                position="top-right"
            )
            return (
                [], [], "Date 1", "Date 2", f"{mix_type} Mix Analysis", None, None, 
                True, True,
                "Date range unavailable for the selected mix type",
                "Date range unavailable for the selected mix type",
                notification
            )
        
        # Get available dates from the database
        dates = get_available_dates(consolidated_name)
        if not dates or len(dates) < 2:
            error_msg = f"Insufficient dates found for {consolidated_name}"
            dash_logger.error(error_msg)
            notification = create_alert(
                message="Not enough dates available for comparison (at least 2 needed)",
                color="warning",
                icon="⚠️",
                position="top-right"
            )
            return (
                [], [], "Date 1", "Date 2", f"{mix_type} Mix Analysis", None, None, 
                True, True,
                "Not enough dates available for comparison",
                "Not enough dates available for comparison",
                notification
            )
        
        # Format dates for display
        date_options = create_date_dropdown_options(dates)
        
        # Set default dates (first and last available dates)
        default_date1 = dates[-1]  # First date (Date 1 should be earlier than Date 2)
        default_date2 = dates[0]  # Last date
        
        # Set date labels based on mix type
        date1_label = f"{mix_type} 1"
        date2_label = f"{mix_type} 2"
        
        # Set tooltips
        date1_tooltip = f"Select the base {mix_type.lower()} for comparison"
        date2_tooltip = f"Select the target {mix_type.lower()} for comparison"
        
        # Return all required outputs
        return (
            date_options, date_options,  # Date options for both dropdowns
            date1_label, date2_label,    # Labels for the dropdowns
            f"{mix_type} Mix Analysis",  # Title
            default_date1, default_date2, # Default values
            False, False,               # Not disabled
            date1_tooltip, date2_tooltip, # Tooltips
            None                        # No notification
        )
            
    except Exception as e:
        error_msg = f"Error updating date dropdowns: {str(e)}"
        dash_logger.error(error_msg, exc_info=e)
        notification = create_alert(
            message=error_msg,
            color="danger",
            icon="🚫",
            position="top-right"
        )
        return (
            [], [], "Date 1", "Date 2", "Mix Analysis", None, None, 
            True, True,
            "An error occurred",
            "An error occurred",
            notification
        )


def update_weight_dropdown_callback_logic(consolidated_name):
    """
    Update weight dropdown options based on full path
    """
    if not consolidated_name:
        raise PreventUpdate
    
    try:
        # Get weight options
        weight_options = update_weight_options(consolidated_name)
        
        # Set default weight value - use the first weight option
        weight_value = weight_options[0]["value"] if weight_options else None
        
        # Log the weight options for debugging
        dash_logger.info(f"Weight options for {consolidated_name}: {weight_options}")
        dash_logger.info(f"Default weight value: {weight_value}")
        
        return weight_options, weight_value
    
    except Exception as e:
        error_msg = f"Failed to update weight options: {e}"
        dash_logger.error(error_msg, exc_info=e)
        
        # Provide fallback options
        fallback_options = [{"label": "Count", "value": "count"}]
        return fallback_options, "count" 