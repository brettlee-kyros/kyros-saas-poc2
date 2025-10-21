from dash import Input, Output, State, ALL, clientside_callback
from kyros_plotly_common.layout.sidebar import create_blade_structure, create_accordion_items


# Import refactored utility functions
from utils.ui_helpers import (
    update_canvas_content,
    toggle_validation_modal,
    update_selected_schema,
    toggle_modal_logic,
    handle_deletion_modal_logic,
    update_date_validation_notification_logic,
    update_mix_type_display_logic
)
from utils.component_options import (
    update_date_dropdown_callback_logic,
    update_weight_dropdown_callback_logic
)
from utils.data_processors import (
    validate_date_selections_logic
)


def register_common_callbacks(app):
    """Register all common callbacks for the MixShift dashboard."""

    # Clientside callback to immediately set loading state when confirm button is clicked on the deletion modal
    clientside_callback(
        """
        function updateLoadingState(n_clicks) {
            return true
        }
        """,
        Output("confirm-delete", "loading", allow_duplicate=True),
        Input("confirm-delete", "n_clicks"),
        prevent_initial_call=True,
    )
 
    
    @app.callback(
        Output("catalog-offcanvas", "is_open"),
        Output("blader-content", "children"),
        Output("schema-restart-notification", "children"),
        [
            Input("catalog-open-button", "n_clicks"),
            Input("close-offcanvas", "n_clicks"),
            Input("catalog-refresh-button", "n_clicks"),
        ],
        State("catalog-offcanvas", "is_open"),
        prevent_initial_call=True,
    )
    def callback_update_canvas_content(n_open, n_close, n_refresh, is_open):
        return update_canvas_content(n_open, n_close, n_refresh, is_open)

    @app.callback(
        Output("db-store", "data"),
        Output("welcoming-skin", "style"),
        Output("main-skin", "style"),
        Output("schema-table-div", "children"),
        Input({"type": "table", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def callback_update_selected_schema(n_clicks):
        return update_selected_schema(n_clicks)

    @app.callback(
        Output("deletion-modal", "is_open", allow_duplicate=True),
        Output("deletion-modal-body", "children"),
        Output("drop-table-id", "data"),
        Input({"type": "remove_table", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def callback_toggle_validation_modal(n_clicks):
        return toggle_validation_modal(n_clicks)

    @app.callback(
        Output("deletion-modal", "is_open"),
        Output("catalog-refresh-button", "n_clicks"),
        Output("main-skin", "style", allow_duplicate=True),
        Output("welcoming-skin", "style", allow_duplicate=True),
        Output("confirm-delete", "loading"),
        Input("confirm-delete", "n_clicks"),
        Input("cancel-delete", "n_clicks"),
        State("drop-table-id", "data"),
        prevent_initial_call=True,
    )
    def handle_deletion_modal(confirm_clicks, cancel_clicks, table_id):
        return handle_deletion_modal_logic(confirm_clicks, cancel_clicks, table_id)

    @app.callback(
        Output("modal-lg", "is_open"),
        Input("modal-button", "n_clicks"),
        State("modal-lg", "is_open"),
        prevent_initial_call=True,
    )
    def callback_toggle_modal(n_clicks, is_open):
        return toggle_modal_logic(n_clicks, is_open)

    @app.callback(
        Output("blader-content", "children", allow_duplicate=True),
        Input("page-load-trigger", "data"),  # just to trigger this callback/ contains only "trigger" str.
    )
    def on_page_load(trigger):
        """Callback to handle page load and initialize the catalog"""
        if trigger == "trigger":
            blade_struct = create_blade_structure()
            return create_accordion_items(blade_struct)
        return None

    @app.callback(
        [
            Output("date1-dd", "options"),
            Output("date2-dd", "options"),
            Output("date1-dd-control", "label"),
            Output("date2-dd-control", "label"),
            Output("mixshift-visualization-header", "title"),
            Output("date1-dd", "value"),
            Output("date2-dd", "value"),
            Output("date1-dd", "disabled"),
            Output("date2-dd", "disabled"),
            Output("date1-dd-control", "label_hover_text"),
            Output("date2-dd-control", "label_hover_text"),
            Output("notification-container", "children", allow_duplicate=True),
        ],
        [Input("db-store", "data")],
        prevent_initial_call=True,
        running=[(Output("notification-container", "children"), None, None)],
    )
    def update_date_dropdown_callback(consolidated_name):
        return update_date_dropdown_callback_logic(consolidated_name)

    @app.callback(
        [
            Output("date1-dd", "style"),
            Output("date2-dd", "style"),
            Output("date1-dd", "options", allow_duplicate=True),
            Output("date2-dd", "options", allow_duplicate=True)
        ],
        [
            Input("date1-dd", "value"),
            Input("date2-dd", "value"),
            Input("db-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def validate_date_selections(date1, date2, consolidated_name):
        return validate_date_selections_logic(date1, date2, consolidated_name)

    @app.callback(
        [
            Output("weight-dd", "options"),
            Output("weight-dd", "value"),
        ],
        [Input("db-store", "data")],
        prevent_initial_call=True,
    )
    def update_weight_dropdown_callback(consolidated_name):
        return update_weight_dropdown_callback_logic(consolidated_name)

    @app.callback(
        Output("notification-container", "children"),
        [
            Input("date1-dd", "value"),
            Input("date2-dd", "value"),
            Input("db-store", "data"),
        ],
        prevent_initial_call=True,
        running=[(Output("notification-container", "children"), None, None)],
    )
    def update_date_validation_notification(date1, date2, consolidated_name):
        return update_date_validation_notification_logic(date1, date2, consolidated_name)

    @app.callback(
        Output("mix-type-display", "children"),
        Output("mix-type-container", "style"),
        Input("db-store", "data"),
        prevent_initial_call=True,
    )
    def update_mix_type_display(consolidated_name):
        return update_mix_type_display_logic(consolidated_name)

    @app.callback(
        Output("mixshift-modal-lg", "is_open"),
        [Input("mixshift-modal-button", "n_clicks")],
        [State("mixshift-modal-lg", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_modal(n_clicks, is_open):
        return toggle_modal_logic(n_clicks, is_open)