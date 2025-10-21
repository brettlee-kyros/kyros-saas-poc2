"""
Helper functions for grid operations and data display.
"""
from typing import Dict, List, Any, Optional, Union, Tuple
from dash import no_update, ctx
from dash.exceptions import PreventUpdate
from kyros_plotly_common.logger.dash_logger import dash_logger
from utils.bubbler_functions import (
    create_bubbler_grid,
    generate_grid,
    get_selected_manual_dimensions,
)
from utils.exception_handlers import GridError
from utils.ui_helpers import create_hierarchy_signal_children

def combined_grid_callback(
    consolidated_name: str,
    target_value: Union[List[str], str],
    button_data: str,
    monitoring_date: str,
    conf_level: int,
    selected_clusters: List[str],
) -> Tuple:
    """
    Combined callback for grid creation and update.
    
    Args:
        consolidated_name: Name of the consolidated table
        target_value: Selected target value(s)
        button_data: Data from header button for view switching
        monitoring_date: Selected monitoring date
        conf_level: Confidence level percentage
        selected_clusters: List of selected clusters
        
    Returns:
        Tuple containing grid components, hierarchy signal, and confidence level
        
    Raises:
        PreventUpdate: If no consolidated name
        GridError: On grid creation error
    """
    if not consolidated_name:
        raise PreventUpdate

    if not conf_level or conf_level > 1 or conf_level < 0.5:
        raise PreventUpdate

    try:
        # Handle missing target value
        if not target_value:
            return (
                ["Oops! It looks like you have not selected any target values."],
                no_update
            )

        triggered = ctx.triggered_id
        
        # Default view is cluster level
        default_view = (
            button_data == "back-to-tabular-view" or not button_data
        )  

        # Determine grid logic based on view type
        if triggered != "header-button-store" and button_data and not default_view:
            # Manual dimension level view
            return _create_manual_dimension_grid(
                consolidated_name,
                target_value,
                monitoring_date,
                conf_level,
                button_data,
                selected_clusters,
            )

        if default_view:
            # Cluster level view (default)
            return _create_cluster_level_grid(
                consolidated_name,
                target_value,
                monitoring_date,
                conf_level,
                selected_clusters,
            )

        # Handle explicit groupby view change
        return _create_manual_dimension_grid(
            consolidated_name,
            target_value,
            monitoring_date,
            conf_level,
            button_data,
            selected_clusters,
        )
        
    except Exception as e:
        error_msg = f"Error while creating the bubbler: {e}"
        error_id = dash_logger.error(error_msg, exc_info=e)
        raise GridError(f"{error_msg}")

def _create_manual_dimension_grid(
    consolidated_name: str,
    target_value: Union[List[str], str],
    monitoring_date: str,
    conf_level: float,
    group_field: str,
    selected_clusters: List[str],
) -> Tuple:
    """
    Create a grid based on manual dimensions.
    
    Args:
        consolidated_name: Name of the consolidated table
        target_value: Selected target value(s)
        monitoring_date: Selected monitoring date
        conf_level: Confidence level as decimal
        group_field: Field to group by
        selected_clusters: List of selected clusters
        
    Returns:
        Tuple containing grid, hierarchy signal, and confidence level
    """
    hierarchy_signal = {
        "icon": "codicon:type-hierarchy-sub",
        "tooltip": "Man Dim Level",
    }

    df, column_defs = generate_grid(
        consolidated_name,
        target_value,
        monitoring_date,
        conf_level,
        group_field=group_field,
        skip_cluster_column=True,
    )
    
    filter_conditions = get_selected_manual_dimensions(
        consolidated_name, group_field, selected_clusters
    )
    
    return (
        create_bubbler_grid(
            consolidated_name,
            column_defs,
            df.to_dict("records"),
            conf_level,
            filter_conditions,
        ),
        create_hierarchy_signal_children(hierarchy_signal)
    )

def _create_cluster_level_grid(
    consolidated_name: str,
    target_value: Union[List[str], str],
    monitoring_date: str,
    conf_level: float,
    selected_clusters: List[str],
) -> Tuple:
    """
    Create a grid at the cluster level.
    
    Args:
        consolidated_name: Name of the consolidated table
        target_value: Selected target value(s)
        monitoring_date: Selected monitoring date
        conf_level: Confidence level as decimal
        selected_clusters: List of selected clusters
        
    Returns:
        Tuple containing grid, hierarchy signal, and confidence level
    """
    hierarchy_signal = {
        "icon": "codicon:type-hierarchy-super",
        "tooltip": "Cluster Level",
    }
    
    # Dynamically generate filter conditions for clusters
    if selected_clusters:
        filter_conditions = {
            "function": " || ".join(
                [
                    f"params.data.cluster == {repr(cluster)}"
                    for cluster in selected_clusters
                ]
            )
        }
    else:
        filter_conditions = []

    df, column_defs = generate_grid(
        consolidated_name,
        target_value,
        monitoring_date,
        conf_level,
        include_manual_dimensions=True,
    )

    return (
        create_bubbler_grid(
            consolidated_name,
            column_defs,
            df.to_dict("records"),
            conf_level,
            filter_conditions,
        ),
        create_hierarchy_signal_children(hierarchy_signal)
    ) 