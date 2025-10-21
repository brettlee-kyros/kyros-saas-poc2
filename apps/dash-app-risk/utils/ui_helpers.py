"""
UI helper functions for the MixShift dashboard.

This module contains functions for UI interactions, modal handling, canvas updates,
and display formatting for the MixShift dashboard.
"""

import dash_design_kit as ddk
from dash import html, ctx, no_update
from dash.exceptions import PreventUpdate

from utils.catalog_initializer import catalog_initializer

from kyros_plotly_common.logger import dash_logger
from kyros_plotly_common.utils.schema import parse_schema_properties
from kyros_plotly_common.layout.sidebar import create_blade_structure, create_accordion_items


def update_canvas_content(n_open, n_close, n_refresh, is_open):
    """
    Handle canvas content updates for opening/closing catalog and refreshing data.
    
    Args:
        n_open: Number of clicks on open button
        n_close: Number of clicks on close button  
        n_refresh: Number of clicks on refresh button
        is_open: Current state of the canvas
        
    Returns:
        tuple: (is_open_state, blade_content, notification_container)
    """
    if not ctx.triggered:
        raise PreventUpdate

    # Handle the case where ctx.triggered might be a boolean (for tests) or a list (in production)
    if isinstance(ctx.triggered, bool):
        # If it's a boolean (likely in tests), use ctx.triggered_id directly
        button_id = ctx.triggered_id
    else:
        # Normal operation - ctx.triggered is a list
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "catalog-open-button":
        return True, no_update, no_update

    elif button_id == "close-offcanvas":
        return False, no_update, no_update

    elif button_id == "catalog-refresh-button":
        catalog_initializer.initialize_catalog()
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
            failure_msg = html.Div(
                [
                    html.P(
                        "Some tables are discarded due to violation of naming convention.",
                        style={"font-weight": "bold", "margin-bottom": "8px"},
                    ),
                    html.P(
                        [
                            "Naming convention ( fields separated by double underscores ): \n",
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
                        },
                    ),
                ]
            )

            notifications.append(
                ddk.Notification(
                    title="⚠️ Naming Convention Violations",
                    children=failure_msg,
                    user_dismiss=True,
                    type="info",
                    timeout=20 * 1000,
                    style={"max-width": "600px", "width": "auto"},
                )
            )

        notification_container = html.Div(notifications)
        return no_update, create_accordion_items(blade_struct), notification_container

    raise PreventUpdate


def toggle_validation_modal(n_clicks):
    """
    Handle validation modal toggle and create modal body content.
    
    Args:
        n_clicks: List of click counts for validation buttons
        
    Returns:
        tuple: (modal_open_state, modal_body_content, selected_table)
    """
    if not ctx.triggered or all(click is None for click in n_clicks):
        raise PreventUpdate

    button_id = ctx.triggered_id
    if button_id:
        selected_table = button_id["index"]

    modal_body = [
        "Are you sure you want to delete",
        " ",
        html.B(selected_table),
        " ",
        "? This will permanently remove all the related tables along with their associated lookup tables.",
    ]
    return True, modal_body, selected_table


def update_selected_schema(n_clicks):
    """
    Update the selected schema when a table is clicked in the catalog.
    
    Args:
        n_clicks: List of click counts for each table button
        
    Returns:
        tuple: (
            full_path,
            welcoming_style,
            main_skin_style,
            header
        )
    """
    if not ctx.triggered or not any(n_clicks):
        raise PreventUpdate

    # Get the triggered button's index (consolidated_name)
    triggered = ctx.triggered_id
    if triggered and triggered.get("type") == "table":
        consolidated_name = triggered["index"]
    else:
        raise PreventUpdate

    # Update styles and components
    welcoming_style = {"display": "none"}
    main_skin_style = {"display": "block"}
    
    # Create schema table div, which includes a table, Left is the table name and right is th
    header = html.Div(
            style={
                "display": "flex",
                "flexDirection": "row",
                "padding": "12px",
            },
            children=[
                # Current Data column
                html.Div(
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "flex": "1",
                        "borderRight": "1px solid #dee2e6",
                        "paddingRight": "20px",
                        "alignItems": "center",
                    },
                    children=[
                        html.Label(
                            "Current Data",
                            style={
                                "textTransform": "capitalize",
                                "color": "grey",
                                "fontSize": "0.9em",
                                "marginBottom": "4px",
                                "textAlign": "center",
                            },
                        ),
                        html.Div(
                            id="current-data",
                            children= consolidated_name,
                            style={
                                "fontSize": "1em",
                            },
                        ),
                    ],
                ),
                # Mix Type column           
                html.Div(
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "flex": "1",
                        "paddingLeft": "20px",
                        "alignItems": "center",
                    },
                    children=[
                        html.Label(
                            "Mix Type",
                            style={
                                "textTransform": "capitalize",
                                "color": "grey",
                                "fontSize": "0.9em",
                                "marginBottom": "4px",
                                "textAlign": "center",
                            },
                        ),
                        html.Div(
                            id="mix-type-display",
                            style={
                                "fontSize": "1em",
                            },
                        ),
                    ],
                    id="mix-type-container",
                    title="The type of mix analysis being displayed (e.g., Snapshot Date, Join Month, etc.)",
                )
            ],
        )

    return (
        consolidated_name,
        welcoming_style,
        main_skin_style,
        header
    )


def toggle_modal_logic(n_clicks, is_open):
    """
    Simple modal toggle functionality.
    
    Args:
        n_clicks: Number of clicks on modal toggle button
        is_open: Current modal open state
        
    Returns:
        bool: New modal open state
    """
    if n_clicks is None:
        return False if is_open is None else is_open
    return not is_open


def handle_deletion_modal_logic(confirm_clicks, cancel_clicks, table_id):
    """
    Handle modal confirmation and cancellation for table deletion operations.
    
    Processes user interactions with the delete confirmation modal, executing
    table hiding operations when confirmed or simply closing the modal when cancelled.
    When a deletion is confirmed, the table and its associated lookup tables are
    hidden from the catalog and the main interface is reset.
    
    Args:
        confirm_clicks: Number of clicks on confirm button
        cancel_clicks: Number of clicks on cancel button  
        table_id: ID of the table to be processed (consolidated_name)
        
    Returns:
        tuple: (modal_open_state, refresh_clicks, main_skin_style, welcoming_style, loading_state)
            - modal_open_state (bool): False to close the modal
            - refresh_clicks (int|no_update): 1 to trigger refresh on confirmation, no_update on cancel
            - main_skin_style (dict|no_update): {"display": "none"} on confirmation to hide main interface
            - welcoming_style (dict|no_update): {"display": "block"} on confirmation to show welcoming screen
            - loading_state (bool): False to stop any loading indicators
    """
    if not ctx.triggered:
        raise PreventUpdate

    triggered = ctx.triggered_id
    if triggered == "confirm-delete":
        if confirm_clicks is not None:
            # Perform the deletion operation
            catalog_initializer.hide_tables(table_id)  # table_id == consolidated_name
            
            # Return: close modal, refresh catalog, hide main skin, stop loading
            return False, 1, {"display": "none"}, {"display": "block"}, False

    if triggered == "cancel-delete":
        if cancel_clicks is not None:
            # Return: close modal, don't refresh, don't change skin, stop loading
            return False, no_update, no_update, no_update, False

    raise PreventUpdate


def update_date_validation_notification_logic(date1, date2, consolidated_name):
    """
    Update date validation notifications
    
    Args:
        date1: Selected first date
        date2: Selected second date
        consolidated_name: Consolidated name to the table
        
    Returns:
        Notification component or None
    """
    if not consolidated_name or not date1 or not date2:
        return None
    
    try:
        # Import create_alert here to avoid circular imports
        from kyros_plotly_common.alerts.alert import create_alert
        from kyros_plotly_common.utils.schema import parse_schema_properties
        from kyros_plotly_common.logger import dash_logger
        
        # Check if date1 is later than date2
        if date1 > date2:
            return create_alert(
                message="Date 1 should be earlier than Date 2",
                color="warning",
                icon="⚠️",
                position="top-right"
            )
        elif date1 == date2:
            return create_alert(
                message="Please select different dates for comparison",
                color="danger",
                icon="🚫",
                position="top-right"
            )
        
        # Get available dates
        properties, _ = parse_schema_properties(consolidated_name,report_type="mix")
        if not properties:
            return create_alert(
                message="Date range unavailable for the selected mix type",
                color="danger",
                icon="🚫",
                position="top-right"
            )
        
        # All validations passed
        return None
        
    except Exception as e:
        error_msg = f"Date validation error: {e}"
        dash_logger.error(error_msg, exc_info=e)
        return create_alert(
            message=f"Error validating dates: {str(e)}",
            color="warning",
            icon="⚠️",
            position="top-right"
        )


def update_mix_type_display_logic(consolidated_name):
    """
    Update the mix type display based on the selected dataset.
    
    Args:
        consolidated_name: Consolidated name to the table
        
    Returns:
        tuple: (mix_type_text, display_style)
    """
    default_style = {
        "display": "flex",
        "flexDirection": "column",
        "flex": "1",
        "paddingLeft": "20px",
        "alignItems": "center",
    }
    styles = {
        "warning": {
            "color": "#ffc107"
        },
        "danger": {
            "color": "#ffc107"
        }
    }
    
    if not consolidated_name:
        return "No dataset selected", {**default_style, **styles["warning"]}

    try:
        properties, _ = parse_schema_properties(consolidated_name, report_type="mix")
        mix_type = properties.get("mix_type", "Mix Type unavailable")
        return mix_type, {**default_style} 

    except Exception as e:
        dash_logger.error(f"Error fetching mix type: {str(e)}")
        return "Error loading Mix Type", {**default_style, **styles["danger"]} 