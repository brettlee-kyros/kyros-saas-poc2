"""
Helper functions for building component options and managing dropdown content.
"""
from dash import html, no_update, ctx
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
from utils.helper_functions import (
    format_component_options,
    parse_and_format_target_options,
    get_current_snapshotdate,
)

def update_common_component_options(n_clicks):
    """
    Update common component options based on selected table.
    
    Args:
        n_clicks: List of click counts for different buttons
        
    Returns:
        Tuple containing component options and values
        
    Raises:
        PreventUpdate: If no button was clicked
    """
    # Default values to return in case of error
    FALLBACK_RETURN = (
        [],  # target-dd options
        [],  # target-dd value
        0,  # age-slider min
        0,  # age-slider max
        [0, 0],  # age-slider value
        {},  # age-slider marks
        [],  # monitoring-dd options
        None,  # monitoring-dd value
        "performance",  # tabs value
        [],  # current-date
    )

    if not any(n_clicks):
        raise PreventUpdate

    clicked_index = next((i for i, clicks in enumerate(n_clicks) if clicks), None)
    if clicked_index is None:
        raise PreventUpdate

    from dash import ctx
    button_id = ctx.triggered_id
    consolidated_name = button_id["index"]  # corresponds to the Selected table_name

    options = format_component_options(consolidated_name)
    if not options:
        print("Errors with initial component options!")
        return FALLBACK_RETURN

    (
        min_obsage,
        max_obsage,
        age_slider_marks,
        monitoring_dd_options,
        date_range,
        date_slider_marks,
    ) = options

    # Get the first target as default
    target_dd_options = parse_and_format_target_options(consolidated_name)
    if not target_dd_options:
        print("Errors with initial target options")
        return FALLBACK_RETURN

    if target_dd_options and len(target_dd_options) > 0:
        initial_value = [target_dd_options[0]["value"]]
    else:
        initial_value = []

    current_date = html.Div(
        [
            html.Div(
                "Current Date",
                style={"fontSize": "0.9em", "fontWeight": "normal", "color": "grey"},
            ),
            html.Div(
                get_current_snapshotdate(consolidated_name),
                style={"fontSize": "1.1em", "fontWeight": 500},
            ),
        ],
    )

    return (
        target_dd_options,
        initial_value,
        min_obsage,
        max_obsage,
        [min_obsage, max_obsage],
        age_slider_marks,
        monitoring_dd_options,
        monitoring_dd_options[0]["value"],
        "performance",
        current_date,
    )

def update_selected_schema(n_clicks):
    """
    Update selected schema based on table selection.
    
    Args:
        n_clicks: List of click counts for different buttons
        
    Returns:
        Tuple containing updated schema and UI components
        
    Raises:
        PreventUpdate: If no button was clicked
    """
    from utils.components import get_icon
    import dash_bootstrap_components as dbc
    
    if not any(n_clicks):
        raise PreventUpdate

    from dash import ctx
    button_id = ctx.triggered_id

    if button_id:
        selected_table = button_id["index"]
        header = html.Div(
            style={
                "display": "flex",
                "flexDirection": "column",
                "alignItems": "center",
            },  # Flex container for alignment
            children=[
                html.Label(
                    "Current Data",
                    style={
                        "textTransform": "capitalize",
                        "color": "grey",
                        "fontSize": "0.9em",
                    },
                ),
                html.Div(
                    id="current-data",
                    children=selected_table,
                    style={
                        "fontSize": "1em",
                    },
                ),
            ],
        )

        selector_signal = "mynaui:letter-a-square"
        hierarchy_signal = "codicon:type-hierarchy-super"
        color = "orange"

        # Import here to avoid circular imports
        from utils.ui_helpers import create_cluster_signal_children, create_hierarchy_signal_children
        
        cluster_signal_children = create_cluster_signal_children({
            "icon": selector_signal, 
            "color": color, 
            "tooltip": "All"
        })

        hierarchy_signal_children = create_hierarchy_signal_children({
            "icon": hierarchy_signal,
            "tooltip": "Cluster Level"
        })

        return (
            button_id["index"],
            {"display": "none"},
            {"display": "block"},
            header,
            {},
            {},
            {},
            cluster_signal_children,
            hierarchy_signal_children,
        )  # {} means all for figures
    else:
        header = "Selected table doesn't have a corresponding data on the database. Please, try selecting another one!"
        return (
            no_update,
            {"display": "block"},
            {"display": "none"},
            header,
            {},
            {},
            {},
            no_update,
            no_update,
        )

def toggle_validation_modal(n_clicks):
    """
    Toggle validation modal for table deletion.
    
    Args:
        n_clicks: List of click counts for different buttons
        
    Returns:
        Tuple containing modal state, body content, and selected table
        
    Raises:
        PreventUpdate: If no button was clicked
    """
    
    if not ctx.triggered or all(click is None for click in n_clicks):
        raise PreventUpdate

    button_id = ctx.triggered_id
    if button_id:
        selected_table = button_id["index"]

    modal_body = [
        html.Div([
             # Selected table info
            html.Div([
                html.P([
                    "You are about to delete dataset: ",
                    html.Code(
                        selected_table,
                        style={
                            "backgroundColor": "#f8f9fa",
                            "padding": "4px 8px",
                            "borderRadius": "4px",
                            "color": "#495057",
                            "fontSize": "0.9rem",
                            "fontWeight": "600"
                        }
                    )
                ], style={"marginBottom": "16px"})
            ]),
            
            # Impact details
            html.Div([
                html.H6(
                    "This will remove:",
                    style={
                        "marginBottom": "12px",
                        "color": "#495057",
                        "fontWeight": "500"
                    }
                ),
                html.Ul([
                    html.Li([
                        DashIconify(icon="mdi:table", height=16, color="#6c757d", style={"marginRight": "8px"}),
                        "All TM1, TM2, and TM5 performance tables"
                    ], style={"marginBottom": "8px", "display": "flex", "alignItems": "center"}),
                    html.Li([
                        DashIconify(icon="mdi:link-variant", height=16, color="#6c757d", style={"marginRight": "8px"}),
                        "Associated lookup and reference tables"
                    ], style={"marginBottom": "8px", "display": "flex", "alignItems": "center"}),
                ], style={
                    "paddingLeft": "0",
                    "listStyle": "none"
                })
            ], style={
                "padding": "16px",
                "borderRadius": "8px",
                "border": "1px solid #e9ecef"
            })
        ])
    ]
    return True, modal_body, selected_table 