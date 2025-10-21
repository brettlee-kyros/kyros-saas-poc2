"""
Data processing and validation utility functions.

This module contains functions for validating data inputs, processing data,
and performing data-related operations for the MixShift dashboard.
"""

from datetime import datetime
from kyros_plotly_common.logger import dash_logger
from kyros_plotly_common.utils.schema import parse_schema_properties
from utils.dbx_utils import get_available_dates


def validate_date_selections_logic(date1, date2, consolidated_name):
    """
    Validate date selections and update styles and options
    
    Args:
        date1: Selected first date
        date2: Selected second date  
        consolidated_name: Consolidated name to the table
        
    Returns:
        tuple: (date1_style, date2_style, date1_options, date2_options)
    """
    # Default styles
    try:
        date1_style = {"width": "100%"}
        date2_style = {"width": "100%"}
        
        if not consolidated_name or not date1 or not date2:
            return date1_style, date2_style, [], []
        
        # Get available dates
        date1_options = get_available_dates(consolidated_name)
        date2_options = get_available_dates(consolidated_name)
    
        # Check if date1 is later than date2
        if date1 > date2:
            date1_style = {"width": "100%", "borderColor": "red", "boxShadow": "0 0 0 1px red"}
        elif date1 == date2:
            date1_style = {"width": "100%", "borderColor": "red", "boxShadow": "0 0 0 1px red"}
            date2_style = {"width": "100%", "borderColor": "red", "boxShadow": "0 0 0 1px red"}
        
        # Check if properties exist
        properties, _ = parse_schema_properties(consolidated_name)
        if not properties:
            date1_style = {"width": "100%", "borderColor": "red", "boxShadow": "0 0 0 1px red"}
            date2_style = {"width": "100%", "borderColor": "red", "boxShadow": "0 0 0 1px red"}
            
        # Filter date options
        date1_options = [option for option in date1_options if option < datetime.date(datetime.strptime(date2, "%Y-%m-%d"))]
        date2_options = [option for option in date2_options if option > datetime.date(datetime.strptime(date1, "%Y-%m-%d"))]
        
        # All validations passed
        return date1_style, date2_style, date1_options, date2_options
        
    except Exception as e:
        error_msg = f"Date validation error: {e}"
        dash_logger.error(error_msg, exc_info=e)
        return date1_style, date2_style, date1_options, date2_options 