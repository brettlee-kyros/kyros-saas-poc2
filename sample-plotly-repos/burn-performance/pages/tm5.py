from dash import Output, Input, callback, State
from dash.exceptions import PreventUpdate

import pandas as pd
import json

from utils.helper_functions import bar_chart_height_calculator
from utils.dbx_utils import fetch_kldivergence_data, fetch_histogram_data
from utils.viz_functions import create_predictor_figure, create_histogram_figure
from utils.components import get_icon

from kyros_plotly_common.logger.dash_logger import dash_logger
from utils.exception_handlers import (
    HistogramError,
    PredictorTableError,
)

# error_id = logger.error(error_msg)
# user_msg = f"[Error ID: {error_id}] {error_msg}" if error_id else error_msg

# --------------------------------#


def update_kl_blubber_data(snapshot_val, cluster_val, consolidated_name):
    if cluster_val is None:
        raise PreventUpdate
    try:
        df = fetch_kldivergence_data(consolidated_name, cluster_val, snapshot_val)
        return df.to_dict("records")
    except Exception as e:
        error_msg = f"Failed to update the predictor bubbler (TM5): {e}"
        error_id = dash_logger.error(error_msg, exc_info=e)
        # raise PredictorTableError(f"[Error ID: {error_id}] {error_msg}")
        raise PredictorTableError(f"{error_msg}")


def update_kl_blubber_fig(data, n_clicks, last_selected):
    """
    Update KL blubber figure based on data, sorting clicks, and selection.
    """
    if not data:
        raise PreventUpdate

    try:
        df = pd.DataFrame.from_dict(data)

        # Initialize variables
        filter_val = "descending"
        icon_size = 18
        children = get_icon("flat-color-icons:generic-sorting-desc", icon_size)

        # Handle sorting clicks
        if n_clicks:
            if n_clicks % 2 == 0:
                filter_val = "ascending"
                children = get_icon("flat-color-icons:generic-sorting-asc", icon_size)

        # Create figure with current sorting
        fig = create_predictor_figure(df, filter_val)

        # Calculate chart height
        style = bar_chart_height_calculator(len(df), k=2.2, unit="vh")

        # Apply previous selection if exists
        if last_selected:
            try:
                selected_category = json.loads(last_selected)["y"]
                opacities = [0.3] * len(fig.data[0].y)

                # Find and highlight selected category
                for i, y in enumerate(fig.data[0].y):
                    if y == selected_category:
                        opacities[i] = 1
                        break

                # Update marker opacities
                if hasattr(fig.data[0], "marker"):
                    fig.data[0].marker.opacity = opacities
                else:
                    fig.data[0].marker = {"opacity": opacities}

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                error_msg = f"Error processing the last_selected for the Predictor Bubbler (TM5): {str(e)}"
                dash_logger.error(error_msg, exc_info=e)

        return fig, children, style

    except Exception as e:
        error_msg = f"Failed to populate predictor bubbler (TM5): {e}"
        error_id = dash_logger.error(error_msg, exc_info=e)
        # raise PredictorTableError(f"[Error ID: {error_id}]" + " " + error_msg)
        raise PredictorTableError(error_msg)


def update_histogram(
    snapshot_val, cluster_val, selectedData, last_selected_category, consolidated_name
):
    if cluster_val is None or not selectedData or not last_selected_category:
        raise PreventUpdate
    try:
        # Parse selected_data or last_selected_category
        try:
            if selectedData:
                data = json.loads(selectedData)
            elif last_selected_category:
                data = json.loads(last_selected_category)
            else:
                data = None
        except json.JSONDecodeError as e:
            error_msg = f"Histogram eror while updating the last selected values: {e}"
            dash_logger.error(error_msg)

        predictor_val = data.get("y", [])
        if not isinstance(predictor_val, str):
            error_msg = f"Invalid predictor_val: {predictor_val}"
            dash_logger.error(error_msg)
            raise ValueError(error_msg)

        title = predictor_val.strip() if predictor_val else ""
        hist_df = fetch_histogram_data(
            consolidated_name, cluster_val, snapshot_val, predictor_val
        )
        fig_h_bar = create_histogram_figure(hist_df)
        return fig_h_bar, title

    except Exception as e:
        error_msg = f"Faield to update histogram (TM5): {e}"
        error_id = dash_logger.error(error_msg, exc_info=e)
        # raise HistogramError(f"[Error ID: {error_id}]" + " " + error_msg)
        raise HistogramError(error_msg)


def update_bubbler_data(clickData, figure):
    if not figure or "data" not in figure or not figure["data"]:
        raise PreventUpdate

    try:
        bar_data = figure["data"][0]  # first trace is the bar plot
        x_data = bar_data["x"]
        y_data = bar_data["y"]

        # Set default opacity (reverse)
        default_opacity = 0.3
        selected_opacity = 1

        if clickData is None:
            # Reset all bars to full opacity
            bar_data["marker"]["opacity"] = [default_opacity] * len(x_data)
            return figure, None, None

        selected_point = clickData["points"][0]
        selected_x = selected_point["x"]
        selected_index = selected_point["pointIndex"]
        selected_y = y_data[selected_index]

        # Update opacities: selected bar is full opacity, others are reduced
        new_opacities = [
            default_opacity if x != selected_x else selected_opacity for x in x_data
        ]

        if "marker" not in bar_data:
            bar_data["marker"] = {}

        bar_data["marker"]["opacity"] = new_opacities

        # Prepare data for dcc.Store
        selected_data = {"x": selected_x, "y": selected_y}
        return figure, json.dumps(selected_data), json.dumps(selected_data)

    except Exception as e:
        error_msg = f"Failed to update predictor Bubbler (TM5): {e}"
        error_id = dash_logger.error(error_msg, exc_info=e)
        raise PredictorTableError(error_msg)
        # raise PredictorTableError(f"[Error ID: {error_id}]" + " " + error_msg)


def register_tm5_callbacks(app):
    @app.callback(
        Output({"type": "kl-data-store", "index": "tm5"}, "data"),
        Input("monitoring-dd", "value"),
        Input({"type": "cluster-filter-store", "index": "common"}, "data"),
        State({"type": "db-store", "index": "common"}, "data"),
        prevent_initial_call=True,
    )
    def callback_update_kl_blubber(snapshotDate, cluster, consolidated_name):
        return update_kl_blubber_data(snapshotDate, cluster, consolidated_name)

    @app.callback(
        Output("kl-divergence-fig", "figure"),
        Output("kl-bubbler-sort-button", "children"),
        Output("kl-divergence-fig", "style"),
        Input({"type": "kl-data-store", "index": "tm5"}, "data"),
        Input("kl-bubbler-sort-button", "n_clicks"),
        State({"type": "last-selected-kl", "index": "tm5"}, "data"),
        prevent_initial_call=True,
    )
    def callback_update_kl_bubbler_fig(data, n_clicks, last_selected):
        return update_kl_blubber_fig(data, n_clicks, last_selected)

    @app.callback(
        Output({"type": "kl-histogram", "index": "tm5"}, "figure"),
        Output("hist-title-id", "children"),
        Input("monitoring-dd", "value"),
        Input({"type": "cluster-filter-store", "index": "common"}, "data"),
        Input({"type": "selected-kl-data", "index": "tm5"}, "data"),
        Input({"type": "last-selected-kl", "index": "tm5"}, "data"),
        State(
            {"type": "db-store", "index": "common"}, "data"
        ),  # Last clicked table info
        prevent_initial_call=True,
    )
    def callback_update_histogram(
        snapshot_val,
        cluster_val,
        selectedData,
        last_selected_category,
        consolidated_name,
    ):
        return update_histogram(
            snapshot_val,
            cluster_val,
            selectedData,
            last_selected_category,
            consolidated_name,
        )

    @callback(
        Output("kl-divergence-fig", "figure", allow_duplicate=True),  # opacity
        Output({"type": "selected-kl-data", "index": "tm5"}, "data"),
        Output({"type": "last-selected-kl", "index": "tm5"}, "data"),
        Input("kl-divergence-fig", "clickData"),
        State("kl-divergence-fig", "figure"),
        prevent_initial_call=True,
    )
    def callback_update_bubbler_data(click_data, figure):
        return update_bubbler_data(click_data, figure)
