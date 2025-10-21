"""
Data processing functions for dashboard components.
"""
import pandas as pd
from typing import Dict, List, Union
from dash.exceptions import PreventUpdate
from utils.catalog_initializer import catalog_initializer
from utils.dbx_utils import get_triangle_format_data, get_manual_dimensions
from kyros_plotly_common.logger.dash_logger import dash_logger
from utils.helper_functions import extract_clusters, get_matching_clusters, determine_selector_signal
from utils.bubbler_functions import extract_dynamic_column_value
from utils.ui_helpers import create_cluster_signal_children
from utils.exception_handlers import TM1PlotError
from dash import html, no_update, ctx
import dash_design_kit as ddk
from kyros_plotly_common.layout.sidebar import create_blade_structure, create_accordion_items
    
def fetch_and_store_data(
    dev_values: List[str], 
    consolidated_name: str, 
    selected_clusters: List[str], 
    target_value: Union[List[str], str], 
    mask: str
) -> Dict[str, Dict]:
    """
    Fetch triangle format data for development values and store as dictionary.
    
    Args:
        dev_values: List of development values to fetch
        consolidated_name: The consolidated table name
        selected_clusters: List of selected clusters
        target_value: Target value(s) for data fetching
        mask: Mask value for data filtering
        
    Returns:
        Dict containing fetched data for each development value
    """
    tri_df_dict = {}

    for dev_value in dev_values:
        df = get_triangle_format_data(
            consolidated_name, dev_value, selected_clusters, target_value, mask
        )

        if df is None:
            print(f"Triangular data for '{dev_value}' could not be fetched.")
            tri_df_dict[dev_value] = {}
        else:
            tri_df_dict[dev_value] = df.to_dict("records")  # type: ignore

    return tri_df_dict

def gather_selected_clusters(selectedRows, consolidated_name):
    """
    Process selected rows and extract clusters.
    
    Args:
        selectedRows: Selected rows from the data grid
        consolidated_name: The consolidated table name
        
    Returns:
        Tuple containing selected clusters and signal children components
        
    Raises:
        PreventUpdate: If no valid selection or processing error
    """
    if isinstance(selectedRows, dict) and "function" in selectedRows:
        raise PreventUpdate

    # Default signal for "All", []
    default_cluster_signal = {
        "icon": "mynaui:letter-a-square",
        "color": "orange",
        "tooltip": "All",
    }

    # Handle no selection
    if not selectedRows:
        return [], create_cluster_signal_children(default_cluster_signal)
    
    selected_clusters = extract_clusters(selectedRows)  # for cluster level
    if not selected_clusters:
        dim_key_values = extract_dynamic_column_value(selectedRows)
        if dim_key_values:
            man_dim_dict = get_manual_dimensions(consolidated_name)
            man_dim_df = pd.DataFrame(man_dim_dict)
            selected_clusters = get_matching_clusters(man_dim_df, dim_key_values)

    # Determine signal based on selection
    selector_signal = determine_selector_signal(selected_clusters)
    if not selected_clusters:
        return [], create_cluster_signal_children(selector_signal)

    # Return updated data and children
    return selected_clusters, create_cluster_signal_children(selector_signal)

def gather_selected_snapshotdate(selectedData):
    """
    Extract snapshot dates from the exposure graph.
    
    Args:
        selectedData: Selected data points from the exposure graph
        
    Returns:
        Dict: Contains snapshot dates and point indices
        
    Raises:
        TM1PlotError: If there's an error processing the selected data
    """
    # Handle no points selected case or invalid points structure
    if not selectedData or not selectedData.get("points", []) or not isinstance(selectedData, dict) or not isinstance(selectedData.get("points"), list):
        return {}  # empty dict means all dates
    
    try:
        # Store both dates and indices
        stored_filters = {
            "snapshotDates": [
                point["x"] for point in selectedData["points"] if "x" in point
            ],
            "point_indices": [
                point["pointIndex"]
                for point in selectedData["points"]
                if "pointIndex" in point
            ],
        }
        return stored_filters

    except Exception as e:
        error_msg = f"Unable to store selected snapshotDate! {e}"
        error_id = dash_logger.error(error_msg, exc_info=e)
        raise TM1PlotError(f"{error_msg}")

def update_canvas_content(n_open, n_close, n_refresh, is_open):
    """
    Update the canvas content based on user interactions.
 
    Args:
        n_open: Number of times open button clicked
        n_close: Number of times close button clicked
        n_refresh: Number of times refresh button clicked
        is_open: Current open state of canvas
 
    Returns:
        Tuple of (is_open, blade_content, notifications)
    """
    if not ctx.triggered:
        raise PreventUpdate
 
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
 
    if button_id == "catalog-open-button":
        return True, no_update, no_update
 
    elif button_id == "close-offcanvas":
        return False, no_update, no_update
 
    elif button_id == "catalog-refresh-button":
        # init catalog with the refresed data
        catalog_initializer.initialize_catalog()
 
 
        # update blade structure
        blade_struct = create_blade_structure()
 
        notifications = []
        notifications.append(
            ddk.Notification(
                title="🔄 Dashboard Refreshed",
                children="The dashboard has been successfully updated. Latest data and schema structures are now in place!",
                user_dismiss=True,
                type="info",
                timeout=4 * 1000,
            )
        )
 
        if catalog_initializer._nconvention_failure:
            failure_msg = _create_naming_convention_failure_message()
            notifications.append(failure_msg)
 
        if catalog_initializer._rejected_tables:
            rejected_msg = _create_rejected_tables_message()
            notifications.append(rejected_msg)
 
        notification_container = html.Div(notifications)
        return no_update, create_accordion_items(blade_struct), notification_container
 
    raise PreventUpdate
 
 
def _create_naming_convention_failure_message():
    """Create notification message for naming convention failures."""
    failure_msg = html.Div(
        [
            html.P(
                "Some tables are discarded due to violation of naming convention.",
                style={"font-weight": "bold", "margin-bottom": "8px"},
            ),
            html.P(
                [
                    "Naming convention ( fields separated by '__' ): \n",
                    html.Code(
                        "model_name__report_type__report_version__creation_date_time__schema_flag__schema_version",
                        style={
                            "background-color": "#f8f9fa",
                            "padding": "4px",
                            "border-radius": "4px",
                        },
                    ),
                ],
                style={"margin-bottom": "12px"},
            ),
            html.P(
                "Discarded tables:",
                style={"font-weight": "bold", "margin-bottom": "8px"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            "• ",  # Bullet point
                            html.Code(table, style={"margin-left": "4px"}),
                        ],
                        style={
                            "display": "flex",
                            "align-items": "center",
                            "margin-bottom": "4px",
                        },
                    )
                    for table in catalog_initializer._nconvention_failure
                ],
                style={
                    "max-height": "150px",
                    "overflow-y": "auto",
                    "padding": "8px",
                    "background-color": "#f8f9fa",
                    "border-radius": "4px",
                    "border": "1px solid #dee2e6",
                },
            ),
        ]
    )
 
    return ddk.Notification(
        title="⚠️ Naming Convention Violations",
        children=failure_msg,
        user_dismiss=True,
        type="info",
        timeout=20 * 1000,
        style={"max-width": "600px", "width": "auto"},
    )
 
 
def _create_rejected_tables_message():
    """Create notification message for rejected tables."""
    rejected_msg = html.Div(
        [
            html.P(
                "Some tables are discarded due to not having all the necessary report tables.",
                style={"font-weight": "bold", "margin-bottom": "8px"},
            ),
            html.P(
                [
                    "Client data needs to satisfy all the jm_performance1 and jm_performance2 reports and their corresponding lookup schema on the database!"
                ],
                style={"margin-bottom": "12px"},
            ),
            html.P(
                "Discarded tables:",
                style={"font-weight": "bold", "margin-bottom": "8px"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            "• ",
                            html.Code(
                                (
                                    table
                                    if isinstance(table, str)
                                    else table.get("table", str(table))
                                ),
                                style={"margin-left": "4px"},
                            ),
                        ],
                        style={
                            "display": "flex",
                            "align-items": "center",
                            "margin-bottom": "4px",
                        },
                    )
                    for table in catalog_initializer._rejected_tables
                ],
                style={
                    "max-height": "150px",
                    "overflow-y": "auto",
                    "padding": "8px",
                    "background-color": "#f8f9fa",
                    "border-radius": "4px",
                    "border": "1px solid #dee2e6",
                },
            ),
        ]
    )
 
    return ddk.Notification(
        title="❌ Missing Required Reports",
        children=rejected_msg,
        user_dismiss=True,
        type="info",
        timeout=15 * 1000,
        style={"max-width": "600px", "width": "auto"},
    )