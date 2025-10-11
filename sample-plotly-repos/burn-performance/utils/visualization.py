"""
Visualization functions for dashboard components.
"""
from typing import Dict, List, Any, Optional, Union, Tuple
import pandas as pd
from dash import html, no_update
from utils.dbx_utils import (
    get_manual_dimensions,
    get_agg_pval,
    get_total_financial_impact
)
from kyros_plotly_common.logger.dash_logger import dash_logger
from utils.viz_functions import create_exposure_bar_plot
from kyros_plotly_common.utils.schema import parse_schema_properties
from utils.helper_functions import (
    generate_significant_text,
)
from utils.exception_handlers import TM1PlotError, CalloutError

def is_agg_zscore_valid(agg_zscore):
    """
    Check if agg_zscore is valid and not empty.
    
    Args:
        agg_zscore: The aggregated z-score data to validate
        
    Returns:
        bool: True if agg_zscore is valid and not empty, False otherwise
    """
    return agg_zscore is not None and (
        (isinstance(agg_zscore, pd.DataFrame) and not agg_zscore.empty) or 
        (isinstance(agg_zscore, list) and len(agg_zscore) > 0)
    )

def update_fetch_and_exposure_graph_combined(
    selected_clusters: List[str], 
    target_value: Union[List[str], str], 
    mask: str, 
    monitoring_date: str, 
    consolidated_name: str, 
    selected_dates: Optional[Dict[str, Any]] = None
):
    """
    Combined function to fetch data and update the exposure graph.
    
    Args:
        selected_clusters: List of selected clusters
        target_value: Target value for data
        mask: Mask value
        monitoring_date: Selected monitoring date
        consolidated_name: Consolidated name for database queries
        selected_dates: Dictionary of selected date information
        
    Returns:
        Tuple containing figure, data stores, display styles, and current exposure
        
    Raises:
        TM1PlotError: On data fetch or visualization error
    """
    from utils.data_processors import fetch_and_store_data
    
    try:
        # Default styles
        display_style_visible = {"height": "100%", "display": "block"}
        display_style_hidden = {"height": "100%", "display": "none"}

        # Target dropdown can't be left blank, make the figures disappear and show an alert
        if not target_value:
            alert_note = "Oops! It looks like you have not selected any target values. Please choose at least one to proceed."
            return (
                no_update,
                no_update,
                no_update,
                display_style_hidden,
                display_style_visible,
                alert_note,
                no_update,
            )

        # Fetch schema properties
        properties, _ = parse_schema_properties(consolidated_name, "performance1")
        if not properties:
            print("Warning: Schema properties not found.")
            return (
                no_update,
                no_update,
                no_update,
                display_style_hidden,
                display_style_visible,
                no_update,
                no_update,
            )

        targets = properties.get("targets", {})
        if not targets:
            print("Warning: No targets found in schema properties.")
            return (
                no_update,
                no_update,
                no_update,
                display_style_hidden,
                display_style_visible,
                no_update,
                no_update,
            )

        # Handle target
        target_ = target_value[0] if isinstance(target_value, list) else target_value
        dev_metric = targets.get(target_, {}).get("development_metric", "")

        # Fetch and store data
        dev_values = ["dev", "dev_since"] if dev_metric == "dev" else ["dev_since"]
        tri_df_dict = fetch_and_store_data(
            dev_values, consolidated_name, selected_clusters, target_value, mask
        )
        if tri_df_dict is None:
            return (
                no_update,
                no_update,
                no_update,
                display_style_hidden,
                display_style_visible,
                no_update,
                no_update,
            )
            
        # Plot exposure bar
        fig = create_exposure_bar_plot(consolidated_name, selected_clusters)
        
        # Apply selection if available
        if selected_dates and "point_indices" in selected_dates:
            fig.data[0].update({"selectedpoints": selected_dates["point_indices"]})
        else:
            fig.data[0].update({"selectedpoints": None})
        
        x_values = fig.data[0].x
        y_values = fig.data[0].y
        
        # Find the index of monitoring date
        target_index = None
        for i, x_val in enumerate(x_values):
            if str(x_val) == str(monitoring_date):
                target_index = i
                break
            
        current_exposure = y_values[target_index] if target_index is not None else None
        
        # Highlight the monitoring date bar
        if target_index is not None:
            # Default color for all bars
            colors = ['rgba(22, 135, 255, 0.8)'] * len(x_values)
            # Special color for the monitoring date
            colors[target_index] = 'rgba(255, 153, 0, 0.9)'
            # Apply the colors
            fig.data[0].marker.color = colors

        return (
            fig,
            tri_df_dict.get("dev_since", {}),
            tri_df_dict.get("dev", {}),
            display_style_visible,
            display_style_hidden,
            no_update,
            current_exposure,
        )
    except Exception as e:
        error_msg = f"Error while fetching the data for TM1 main figure: {e}"
        error_id = dash_logger.error(error_msg, exc_info=e)
        raise TM1PlotError(f"{error_msg}")

def process_callout_metrics(
    rr_values: Tuple[float, float], 
    selected_points: Optional[float], 
    selected_rows: List[Dict[str, Any]], 
    target_list: List[str], 
    monitoring_date: str, 
    consolidated_name: str, 
    conf_level: int
):
    """
    Process and format metrics for callout display.
    
    Args:
        rr_values: Tuple of actual and expected values
        selected_points: Number of selected points
        selected_rows: Selected rows from grid
        target_list: List of selected targets
        monitoring_date: Selected monitoring date
        consolidated_name: Consolidated name for queries
        conf_level: Confidence level percentage
        
    Returns:
        Tuple of formatted values for display
        
    Raises:
        CalloutError: If error occurs during processing
    """
    from utils.exception_handlers import CalloutError
    from utils.ui_helpers import format_display_values
    from utils.bubbler_functions import extract_dynamic_column_value
    from utils.helper_functions import extract_clusters, get_matching_clusters
    
    try:
        # Fetch properties once
        report_type = "performance1"
        properties, _ = parse_schema_properties(consolidated_name, report_type)

        # Extract current snapshotDate
        current_snapshot_date = properties.get("current_snapshotDate")
        if not current_snapshot_date:
            error_msg = f"'current_snapshotDate' key is missing or invalid in the lookup table for {consolidated_name}"
            dash_logger.error(error_msg)
            raise KeyError(error_msg)
        
        # Process RR values
        actual_val, expected_val = rr_values
        
        formatted_actual = format_display_values(actual_val) if actual_val is not None else " - "
        formatted_expected = format_display_values(expected_val) if expected_val is not None else " - "
        formatted_selected_points = format_display_values(selected_points, "large_number") if selected_points else " - "

        # Calculate residual
        if expected_val is not None or actual_val is not None:
            exp_val = expected_val or 0
            act_val = actual_val or 0
            formatted_residual = format_display_values(act_val - exp_val)
        else:
            formatted_residual = " - "
                      
        # Process selected rows if available
        if selected_rows:
            # Filter out rows that contain the 'function' key
            filtered_rows = [row for row in selected_rows if isinstance(row, dict) and 'function' not in row]

            if filtered_rows:
                # Calculate total financial impact
                total_financial_impact = [
                    row['financial_impact'] for row in filtered_rows 
                    if 'financial_impact' in row and row['financial_impact'] is not None
                ]

                formatted_financial_impact = format_display_values(sum(total_financial_impact), "currency") if total_financial_impact else " - "
                
                # Extract clusters from selected rows
                selected_clusters = extract_clusters(selected_rows)
                if not selected_clusters:
                    dim_key_values = extract_dynamic_column_value(selected_rows)
                    if dim_key_values:
                        man_dim_dict = get_manual_dimensions(consolidated_name)
                        man_dim_df = pd.DataFrame(man_dim_dict)
                        selected_clusters = get_matching_clusters(man_dim_df, dim_key_values)
                        
                # Generate significance text based on aggregated z-score
                agg_zscore = get_agg_pval(consolidated_name, target_list, monitoring_date, 
                                         current_snapshot_date, selected_clusters)

                if is_agg_zscore_valid(agg_zscore):
                    significant_text = generate_significant_text(agg_zscore['z_score'], conf_level)
                else:
                    significant_text = " "
                    
                return (
                    formatted_selected_points, 
                    formatted_financial_impact, 
                    formatted_actual, 
                    formatted_expected, 
                    formatted_residual, 
                    significant_text
                )

        # Process all data if no rows selected
        financial_impact = get_total_financial_impact(consolidated_name, target_list, monitoring_date)
        formatted_financial_impact = format_display_values(
            financial_impact[0]['financial_impact'], "currency"
        ) if financial_impact else " - "
            
        # Fetch aggregated Z-score for all clusters
        cluster_list = []
        agg_zscore = get_agg_pval(
            consolidated_name, target_list, monitoring_date, current_snapshot_date, cluster_list
        )

        if is_agg_zscore_valid(agg_zscore):
            significant_text = generate_significant_text(agg_zscore['z_score'], conf_level)
        else:
            significant_text = " "

        return (
            formatted_selected_points, 
            formatted_financial_impact, 
            formatted_actual, 
            formatted_expected, 
            formatted_residual, 
            significant_text
        )
    
    except Exception as e:
        error_msg = f"Error while fetching/calculating the callout metrics: {e}"
        error_id = dash_logger.error(error_msg, exc_info=e)
        raise CalloutError(f"{error_msg}") 