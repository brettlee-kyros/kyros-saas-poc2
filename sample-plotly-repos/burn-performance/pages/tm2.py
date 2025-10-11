from dash import Output, Input, State, ctx, set_props, no_update
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import numpy as np

import pandas as pd

from utils.exception_handlers import TM2PlotError
from kyros_plotly_common.logger.dash_logger import dash_logger
from kyros_plotly_common.utils.schema import parse_schema_properties

from utils.dbx_utils import get_agg_stds_with_covariance, get_reweighted_triangle_format_data
from utils.viz_functions import generate_tm2_fig
from utils.helper_functions import flag_dev_since_dev_metric, months_between


# --------------------------------#


def construct_tm2_fig(
    monitoring_date,
    fetched_data,
    consolidated_name,
    selected_clusters,
    target_list,
    actual_type,
    snapshot_dates,
    age_filter_value,
    mask,
    conf_level,
    target_correlation,
    cluster_correlation
):

    if not target_list:
        raise PreventUpdate
    try:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="Oops! Required data is missing.",
            xaxis_title="",
            yaxis_title="",
        )
        empty_val = np.nan

        if flag_dev_since_dev_metric(consolidated_name, target_list) is None:
            return empty_fig, [empty_val, empty_val]

        if actual_type == "Reweighted":
            reweighted_tri_df = get_reweighted_triangle_format_data(
                consolidated_name, selected_clusters, target_list, monitoring_date, mask
            )
            if not reweighted_tri_df.empty:
                reweighted_tri_df["snapshotDate"] = pd.to_datetime(
                    reweighted_tri_df["snapshotDate"]
                )
            else:
                return empty_fig, [empty_val, empty_val]
        else:
            if not fetched_data:
                return empty_fig, [empty_val, empty_val]

            else:
                reweighted_tri_df = pd.DataFrame(fetched_data)  # regular one
                reweighted_tri_df["snapshotDate"] = pd.to_datetime(
                    reweighted_tri_df["snapshotDate"]
                )
                
        # get the callout info before applying any filters.
        report_type = "performance1"
        properties, _ = parse_schema_properties(consolidated_name, report_type)
        
        if "current_snapshotDate" not in properties:
            raise KeyError("'current_snapshotDate' child-key is missing in the lookup table. Unable to calculate callout metrics.")

        if not properties["current_snapshotDate"]:
            raise ValueError(
                "'current_snapshotDate' child-key is empty or invalid in the lookup table. Unable to calculate callout metrics"
            )

        # calculate current_monitoring_obs_age
        current_snapshotDate = properties["current_snapshotDate"]
        current_monitoring_obs_age = months_between(current_snapshotDate, monitoring_date)

        monitoring_snapshot_df = reweighted_tri_df[reweighted_tri_df['snapshotDate'] == monitoring_date]
        age_filter = monitoring_snapshot_df['obsAge'] == current_monitoring_obs_age

        try:
            current_actual_val = monitoring_snapshot_df[age_filter]['cum_actual'].values[0]
            current_expected_val = monitoring_snapshot_df[age_filter]['cum_expected'].values[0]

        except Exception:
            error_msg = 'No data found for the selected cluster(s) at the selected monitoring date'
            raise ValueError(error_msg)
            
        # filter part
        if snapshot_dates and "snapshotDates" in snapshot_dates:
            snapshot_dates_ = snapshot_dates["snapshotDates"]

            snapshot_dates = pd.to_datetime(snapshot_dates_)
            monitoring_date = pd.to_datetime(monitoring_date)
            combined_dates = snapshot_dates.append(pd.DatetimeIndex([monitoring_date]))

            reweighted_tri_df = reweighted_tri_df.loc[reweighted_tri_df.loc[:, "snapshotDate"].isin(combined_dates)]  # type: ignore

        if age_filter_value:
            lower_age = age_filter_value[0]
            upper_age = age_filter_value[1]
            reweighted_tri_df = reweighted_tri_df[(reweighted_tri_df["obsAge"] >= lower_age) & (reweighted_tri_df["obsAge"] <= upper_age)]  # type: ignore

        df_std = get_agg_stds_with_covariance(
            consolidated_name,
            selected_clusters,
            target_list,
            monitoring_date,
            mask,
            target_correlation=target_correlation,
            cluster_correlation=cluster_correlation
        )
        
        fig = generate_tm2_fig(
            reweighted_tri_df,
            df_std,
            monitoring_date,
            consolidated_name,
            selected_clusters,
            target_list,
            conf_level,
        )  # actual dev_since + black + black + restatemen lines
                
        return fig, [current_actual_val, current_expected_val]
    

    except Exception as e:
        error_msg = f"Error while populting the TM2 main figure: {e}"
        error_id = dash_logger.error(error_msg)
        raise TM2PlotError((f"{error_msg}"))
        # raise TM2PlotError((f"[Error ID: {error_id}] {error_msg}"))


def register_tm2_callbacks(app):
    @app.callback(
        Output("stats-settings-modal", "is_open"),
        [
            Input("stats-settings-button", "n_clicks"),
        ],
        [State("stats-settings-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_stats_settings_modal(stats_settings_n, is_open):
        if not stats_settings_n:
            raise PreventUpdate
        return not is_open
        
    @app.callback(
        Output("conf-level-store", "data"),
        Output("target-correlation-store", "data"),
        Output("cluster-correlation-store", "data"),
        Input("conf_level_input", "value"),
        Input("target-correlation-input", "value"),
        Input("cluster-correlation-input", "value"),
        prevent_initial_call=True,
    )
    def update_stats_settings(conf_level, target_corr, cluster_corr):
        """Update the stats settings and provide feedback (with upstream range validation assumed)"""

        # Safely get the triggering input ID
        if not ctx.triggered:
            return no_update, no_update, no_update

        input_id = ctx.triggered[0]["prop_id"].split(".")[0]

        def set_feedback(msg: str, color: str = "success"):
            alert = dbc.Alert(
                children=msg,
                color=color,
                fade=True,
                duration=3000,
                is_open=True
            )
            set_props("stats-settings-feedback", {"children": alert})

        # Use a list to allow item assignment
        update_return = [no_update, no_update, no_update]

        # Handle each input
        if input_id == "conf_level_input":
            if conf_level is None:
                set_feedback("⚠ Please enter a confidence level between 50 and 100", "danger")
            else:
                update_return[0] = conf_level / 100.0
                set_feedback("✓ Confidence level saved")

        elif input_id == "target-correlation-input":
            if target_corr is None:
                set_feedback("⚠ Please enter a target correlation value between -1 and 1", "danger")
            else:
                update_return[1] = target_corr
                set_feedback("✓ Target correlation saved")

        elif input_id == "cluster-correlation-input":
            if cluster_corr is None:
                set_feedback("⚠ Please enter a cluster correlation value between -1 and 1", "danger")
            else:
                update_return[2] = cluster_corr
                set_feedback("✓ Cluster correlation saved")

        return tuple(update_return)
    
    @app.callback(
        Output({"type": "actual-fig", "index": "tm2"}, "figure"),
        Output("rr-values", "data"),
        Input("monitoring-dd", "value"),
        Input({"type": "fetched-data-store", "index": "tm1"}, "data"),
        Input(
            {"type": "db-store", "index": "common"}, "data"
        ),  # Last clicked table info
        Input({"type": "cluster-filter-store", "index": "common"}, "data"),
        Input("target-dd", "value"),
        Input("actual-radio", "value"),
        Input({"type": "snapshot-filter-store", "index": "common"}, "data"),
        Input("age-slider", "value"),
        Input("mask-radio", "value"),
        Input("conf-level-store", "data"),
        Input("target-correlation-store", "data"),
        Input("cluster-correlation-store", "data"),
        prevent_initial_call=True,
    )
    def callback_construct_tm2_fig(
        monitoring_date,
        fetched_data,
        consolidated_name,
        selected_clusters,
        target_list,
        actual_type,
        snapshot_dates,
        age_filter_value,
        mask,
        conf_level,
        target_correlation,
        cluster_correlation
    ):
        return construct_tm2_fig(
            monitoring_date,
            fetched_data,
            consolidated_name,
            selected_clusters,
            target_list,
            actual_type,
            snapshot_dates,
            age_filter_value,
            mask,
            conf_level,
            target_correlation,
            cluster_correlation
        )
