from dash import Input, Output, State, no_update, ALL, ctx, clientside_callback
from dash.exceptions import PreventUpdate
from kyros_plotly_common.logger.dash_logger import dash_logger
import time

from utils.exception_handlers import TM1PlotError

from utils.catalog_initializer import catalog_initializer

# Import new refactored modules
from utils.ui_helpers import (
    render_control_ribbon,
    render_diagnostic_graphs,
    toggle_modal,
)
from utils.data_processors import (
    update_canvas_content,
    gather_selected_clusters,
    gather_selected_snapshotdate,
)
from utils.visualization import (
    update_fetch_and_exposure_graph_combined,
    process_callout_metrics,
)
from utils.component_options import (
    update_common_component_options,
    update_selected_schema,
    toggle_validation_modal,
)
from utils.grid_helpers import combined_grid_callback


# define callback functions here --------------

def register_common_callbacks(app):
    """
    Register common callbacks for the application.
    
    Args:
        app: Dash application instance
    """
    
    # Clientside callback to immediately set loading state when confirm button is clicked
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
        [
            Output(f"{id}-control", "style")
            for id in [
                "empty",
                "currentdate-info-box",
                "actual-radio",
                "mask-radio",
                "monitoring-dd",
                "target-dd",
                "age-slider",
                "tm5-info",
                "stats-settings",
            ]
        ]
        + [
            Output("info-row", "style"),
            Output("diagnostic-graphs2", "style"),
            Output("exposure-graph-row", "style"),
            Output("diagnostic-graphs5", "style"),
        ],
        Input("tabs", "value"),
        prevent_initial_call=True,
    )
    def callback_render_ui_elements(tab):
        """Render UI elements based on selected tab."""
        control_components_styles = render_control_ribbon(tab)
        dynamic_layout_divs_style = render_diagnostic_graphs(tab)
        
        return [control_components_styles.empty_placeholder,
         control_components_styles.currentdate_info_textbox,
         control_components_styles.actual_radio,
         control_components_styles.mask_radio,
         control_components_styles.monitoring_dropdown,
         control_components_styles.target_dropddown,
         control_components_styles.age_slider,
         control_components_styles.tm5_info_button,
         control_components_styles.stats_settings_button,
         dynamic_layout_divs_style.callouts_div,
         dynamic_layout_divs_style.tm2_graph,
         dynamic_layout_divs_style.exposures_bar_graph,
         dynamic_layout_divs_style.tm5_graphs]
         

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
        """Update canvas content based on user interaction."""
        return update_canvas_content(n_open, n_close, n_refresh, is_open)

    @app.callback(
        Output({"type": "db-store", "index": "common"}, "data"),
        Output("welcoming-skin", "style"),
        Output("main-skin", "style"),
        Output("schema-table-div", "children"),
        Output(
            {"type": "cluster-filter-store", "index": "common"},
            "data",
            allow_duplicate=True,
        ),
        Output(
            {"type": "snapshot-filter-store", "index": "common"},
            "data",
            allow_duplicate=True,
        ),
        Output("header-button-store", "data"),
        Output("selector-signal", "children", allow_duplicate=True),
        Output("hierarchy-signal", "children", allow_duplicate=True),
        Input({"type": "table", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def callback_update_selected_schema(n_clicks):
        """Update selected schema based on table selection."""
        return update_selected_schema(n_clicks)

    @app.callback(
        Output("deletion-modal", "is_open", allow_duplicate=True),
        Output("deletion-modal-body", "children"),
        Output("drop-table-id", "data"),
        Input({"type": "remove_table", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def callback_toggle_validation_modal(n_clicks):
        """Toggle validation modal for table deletion."""
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
    def handle_modal(confirm_clicks, cancel_clicks, table_id):
        """Handle modal confirmation for table deletion."""
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

    @app.callback(
        [
            Output("target-dd", "data", allow_duplicate=True),
            Output("target-dd", "value"),
            Output("age-slider", "min"),
            Output("age-slider", "max"),
            Output("age-slider", "value"),
            Output("age-slider", "marks"),
            Output("monitoring-dd", "options"),
            Output("monitoring-dd", "value"),
            Output("tabs", "value"),
            Output("currentdate-info-box", "children"),
        ],
        Input({"type": "table", "index": ALL}, "n_clicks"),
        prevent_initial_call=False,
    )
    def callback_update_common_component_options(n_clicks):
        """Update common component options based on table selection."""
        return update_common_component_options(n_clicks)

    @app.callback(
        Output(
            {"type": "cluster-filter-store", "index": "common"},
            "data",
        ),
        Output("selector-signal", "children"),
        Input("bubbler-table", "selectedRows"),
        State({"type": "db-store", "index": "common"}, "data"),
        prevent_initial_call=True,
    )
    def callback_gather_selected_clusters(selectedRows, consolidated_name):
        """Gather selected clusters based on row selection."""
        return gather_selected_clusters(selectedRows, consolidated_name)
    
    @app.callback(
        Output("age-filter-text", "children"),
        Input("age-slider", "value"),
        prevent_initial_call=True,
    )
    def display_selected_age_range(slider_range):
        """Display the selected age range from the slider."""
        if not slider_range or len(slider_range) != 2:
            return "Invalid Age filter."

        start_date = slider_range[0]
        end_date = slider_range[1]
        return f"{start_date} → {end_date}"


    @app.callback(
        Output(
            {"type": "exposure-fig", "index": "common"},
            "figure",
            allow_duplicate=True,
        ),
        Output({"type": "fetched-data-store", "index": "tm1"}, "data"),
        Output({"type": "dev-fetched-data-store", "index": "tm1"}, "data"),
        Output("main-graphs", "style"),  # for the cases where target left blank
        Output("main-graphs-alert", "style"),  # for the cases where target left blank
        Output("target-alert", "children"), 
        Output("selected-points", "data"),
        Input({"type": "cluster-filter-store", "index": "common"}, "data"),
        Input("target-dd", "value"),
        Input("mask-radio", "value"),
        Input("monitoring-dd", "value"),
        State({"type": "db-store", "index": "common"}, "data"),
        State({"type": "snapshot-filter-store", "index": "common"}, "data"),
        prevent_initial_call=True,
    )
    def callback_update_fetch_and_exposure_graph_combined(
        selected_clusters, target_value, mask, monitoring_date, consolidated_name, selected_dates
    ):
        """Update graph and fetch data based on selections."""
        return update_fetch_and_exposure_graph_combined(
            selected_clusters, target_value, mask, monitoring_date, consolidated_name, selected_dates
        )
    
    @app.callback(
        Output(
            {"type": "snapshot-filter-store", "index": "common"},
            "data",
            allow_duplicate=True,
        ),
        Input({"type": "exposure-fig", "index": "common"}, "selectedData"),
        prevent_initial_call=True,
    )
    def callback_gather_selected_snapshotdate(selectedData):
        """Gather selected snapshot dates from the exposure graph."""
        return gather_selected_snapshotdate(selectedData)

    @app.callback(
        Output("modal-lg", "is_open"),
        Input("modal-button", "n_clicks"),
        State("modal-lg", "is_open"),
        prevent_initial_call=True,
    )
    def callback_toggle_modal(n_clicks, is_open):
        """Toggle a modal dialog based on button clicks."""
        return toggle_modal(n_clicks, is_open)

    @app.callback(
        Output("blader-content", "children", allow_duplicate=True),
        Input(
            "page-load-trigger", "data"
        ),  # just to trigger this callback/ contains only "trigger" str.
    )
    def on_page_load(trigger):
        """Update blader from redis at the beginning of each session."""
        if trigger is None:
            raise PreventUpdate
            
        from kyros_plotly_common.layout.sidebar import create_accordion_items, create_blade_structure
        blade_struct = create_blade_structure()  # get data from Redis
        return create_accordion_items(blade_struct)  # re-reate blade structure

    @app.callback(
        Output("bubbler-table", "selectedRows"),
        Input("refresh-button-store", "data"),
        prevent_initial_call=True,
    )
    def clear_selection(refresh_clicked):
        """Clear selected rows when refresh is clicked."""
        if refresh_clicked == "refresh":
            return []
        raise PreventUpdate

    @app.callback(
        [
            Output("table-container", "children"),
            Output("hierarchy-signal", "children")
        ],
        Input({"type": "db-store", "index": "common"}, "data"),
        Input("target-dd", "value"),
        Input("monitoring-dd", "value"),
        Input("conf-level-store", "data"),
        Input("header-button-store", "data"),
        State({"type": "cluster-filter-store", "index": "common"}, "data"),
        prevent_initial_call=False,
    )
    def callback_combined_grid_callback(
        consolidated_name,
        target_value,
        monitoring_date,
        conf_level,
        button_data,
        selected_clusters,
    ):
        """Generate and update the data grid based on selections."""
        return combined_grid_callback(
            consolidated_name,
            target_value,
            button_data,
            monitoring_date,
            conf_level,
            selected_clusters,
        )
         
    @app.callback(
        Output("bubbler-table", "exportDataAsCsv"),
        Input("download-csv-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def export_data_as_csv(n_clicks):
        """Export grid data as CSV when button is clicked."""
        if not ctx.triggered[0]["prop_id"].split(".")[0] == "download-csv-button":
            raise PreventUpdate
        
        return True

    @app.callback(
        Output("selected-points-val", "children"),
        Output("financial-impact-val", "children"),
        Output("observed-rr-val", "children"),
        Output("predicted-rr-val", "children"),
        Output("residual-rr-val", "children"),
        Output("significant-text-div", "children"),
        Input("rr-values", "data"),
        State("selected-points","data"),
        State("bubbler-table", "selectedRows"),
        State("target-dd", "value"),
        State("monitoring-dd", "value"),
        State({"type": "db-store", "index": "common"}, "data"),
        State("conf-level-store", "data"),
        prevent_initial_call=True
    )
    def update_info_boxes(rr_values, selected_points, selected_rows, target_list, monitoring_date, consolidated_name, conf_level):                
        """Update information boxes with metrics based on selections."""
        return process_callout_metrics(
            rr_values, 
            selected_points, 
            selected_rows, 
            target_list, 
            monitoring_date, 
            consolidated_name, 
            conf_level
        )

            
