from plotly.subplots import make_subplots
import plotly.graph_objs as go
import plotly.express as px

import pandas as pd
import numpy as np

from kyros_plotly_common.logger.dash_logger import dash_logger
from kyros_plotly_common.utils.schema import parse_schema_properties

from utils.dbx_utils import (
    get_restated_value,
    get_exposures_data,
    get_current_exposures_data,
    get_r2_dev,
    get_pval_and_fin_impact,
    get_all_financial_impact
)
from utils.helper_functions import (
    conf_level_to_zscore,
    get_monitoring_dates,
    check_burn_report,
)


color_points = [
    (0.0, (112, 99, 137)),  # Matte purple
    (0.125, (70, 100, 170)),  # Indigo blue
    (0.25, (131, 178, 208)),  # Original light blue
    (0.375, (149, 218, 182)),  # Original mint green
    (0.5, (200, 209, 150)),  # Olive
    (0.625, (242, 230, 177)),  # Original pale yellow
    (0.75, (233, 185, 155)),  # Peach
    (0.875, (220, 133, 128)),  # Original soft coral
    (1.0, (187, 97, 109)),  # Raspberry
]


def rgb_to_string(rgb):
    return f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"


def interpolate_color(color1, color2, factor):
    """
    Returns:
    - A tuple representing the interpolated color in RGB format.
    """
    return tuple(int(color1[i] + factor * (color2[i] - color1[i])) for i in range(3))


def get_color_for_date(date, min_date, max_date, color_points):
    """
    Interpolate the color for a given date based on the position of the date between min_date and max_date.

    Parameters:
    - date: The date for which the color is being determined.
    - min_date: The minimum date in the range.
    - max_date: The maximum date in the range.
    - color_points: A list of tuples where each tuple contains a position (between 0 and 1) and a color (RGB tuple).

    Returns:
    - A tuple representing the interpolated color in RGB format.
    """

    total_days = (max_date - min_date).days

    if total_days == 0:
        return color_points[0][1]  # return the first color if there is only one date

    days_from_start = (date - min_date).days
    position = days_from_start / total_days

    if position < 0:
        return color_points[0][1]  # Return the first color (min_date)
    if position > 1:
        return color_points[-1][1]  # Return the last color (max_date)

    # Interpolate
    for i in range(len(color_points) - 1):
        if color_points[i][0] <= position <= color_points[i + 1][0]:
            t = (position - color_points[i][0]) / (
                color_points[i + 1][0] - color_points[i][0]
            )
            return interpolate_color(color_points[i][1], color_points[i + 1][1], t)

    return color_points[-1][1]  # Return the last color if something went wrong


def add_restatement_line(
    fig, consolidated_name, cluster_list, target_list, monitoring_date
):
    dates_with_data = get_monitoring_dates(
        consolidated_name
    )  # returns list of dates with data
    if dates_with_data:
        monitoring_date_str = monitoring_date if isinstance(monitoring_date, str) else monitoring_date.strftime("%Y-%m-%d")
        if monitoring_date_str in dates_with_data:
            # Restatement Line
            restatement_line = get_restated_value(
                consolidated_name, cluster_list, target_list, monitoring_date
            )  # returns zero for exceptions
            if restatement_line:
                # get x-range
                expected_trace = next(
                        (trace for trace in fig.data if trace.name == 'Expected'),
                        None
                    )
                x_start, x_end = expected_trace.x[0], expected_trace.x[-1]
                num_points = 100  # rndom
                x_values = [x_start + (x_end - x_start) * i / (num_points - 1) for i in range(num_points)]
                y_values = [restatement_line] * num_points  # Same restatement value for all x points


                # Add a scatter trace for the horizontal line
                fig.add_scatter(
                    x = x_values,
                    y=y_values,
                    mode='lines',
                    line=dict(color='#228B22', dash='dash'),
                    name='Restatement Line',
                    showlegend=True,
                    legend="legend2",
                    hovertemplate=f'Restatement Line: {restatement_line:.3f}<extra></extra>',
                    hoverlabel=dict(
                            bgcolor="white",           
                            bordercolor="#228B22",       
                            font=dict(
                                family="Arial",        
                                size=12,               
                                color="#228B22"       
                            ),
                            align="left"               
                        )
                )
    return fig

def add_blue_line(fig, df, full_path):
    # BLUE (actual values)  @ monitoring snapshotDate
    required_columns = {"obsAge", "cum_actual"}
    if not all(col in df.columns for col in required_columns):
        missing_cols = required_columns - set(df.columns)
        error_msg = (
            f"Missing required columns in DataFrame: {missing_cols} for {full_path}"
        )
        dash_logger.error(error_msg)
        raise ValueError(error_msg)
    

    # Add blue line trace
    try:
        blue_line = go.Scatter(
            x=df["obsAge"],
            y=df["cum_actual"],
            mode="lines",
            name="Actual",
            line=dict(color="blue", width=2),
            legend="legend2",
            hovertemplate="<b>Actual</b><br>ObsAge: %{x}<br>Value: %{y:.6f}<extra></extra>",
            hoverlabel=dict(
                bgcolor="white",           # Background color
                bordercolor="blue",        # Border color
                font=dict(
                    family="Arial",        # Font family
                    size=12,               # Font size
                    color="blue"       # Font color
                ),
                align="left"               # Text alignment
            )
        )
        fig.add_trace(blue_line)
        return fig

    except Exception as e:
        error_msg = (
            f"Failed to add actual values (blue line) trace for {full_path}: {str(e)}"
        )
        dash_logger.error(error_msg)
        raise


def add_black_line_and_ci(fig, df_std, df, conf_level, is_burn, full_path):
    # BLACK (expected values) @ monitoring snapshotDate
    # add expected values line in black
    required_columns = {"obsAge", "cum_expected"}
    if not all(col in df.columns for col in required_columns):
        missing_cols = required_columns - set(df.columns)
        error_msg = f"Missing required columns in main DataFrame: {missing_cols} for {full_path}"
        dash_logger.error(error_msg)
        raise ValueError(error_msg)
    
    

    # Add expected values line in black
    try:
        black_trace = go.Scatter(
            x=df["obsAge"],
            y=df["cum_expected"],
            mode="lines",
            name="Expected",
            legend="legend2",
            line=dict(dash="dot", color="black", width=2.5),
            hovertemplate="<b>Expected</b><br>ObsAge: %{x}<br>Value: %{y:.6f}<extra></extra>",
            hoverlabel=dict(
                bgcolor="white",          
                bordercolor="black",       
                font=dict(
                    family="Arial",       
                    size=12,              
                    color="black"       
                ),
                align="left"              
            )
        )
        
        fig.add_trace(black_trace)
        
    except Exception as e:
        error_msg = f"Failed to add expected values (black line) trace for {full_path}: {str(e)}"
        dash_logger.error(error_msg)
        raise

    if df_std.empty:
        warning_message = "Variance(s) of the selected target(s) could not found: Skipping populating confidence intervals."
        dash_logger.info(warning_message)
        return fig

    # bring expected values and standard deviations to the same dataframe
    try:
        df_combined = pd.merge(df, df_std, on=["obsAge"], how="inner")
        if df_combined.empty:
            error_msg = f"Failed to populate Confidence Intervals: No matching observation ages found between DataFrames for {full_path}."
            dash_logger.error(error_msg)
            raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Failed to populate Confidence Intervals for {full_path}: {str(e)}"
        dash_logger.error(error_msg)
        raise

    z = conf_level_to_zscore(conf_level)

    # Calculate 90% confidence
    df_combined["lower_ci"] = df_combined["cum_expected"] - (z * df_combined["std"])
    df_combined["upper_ci"] = df_combined["cum_expected"] + (z * df_combined["std"])

    df_combined["lower_ci"] = df_combined["lower_ci"].clip(lower=0)
    df_combined["upper_ci"] = df_combined["upper_ci"].clip(lower=0)

    if is_burn:
        df_combined["lower_ci"] = df_combined["lower_ci"].clip(upper=1)
        df_combined["upper_ci"] = df_combined["upper_ci"].clip(upper=1)
        
    for ci_bound, ci_value in [("upper", "upper_ci"), ("lower", "lower_ci")]:
        fig.add_trace(
            go.Scatter(
                x=df_combined["obsAge"],
                y=df_combined[ci_value],
                fill=None,
                mode="lines",
                line=dict(dash="dot", color="red"),
                name=f"{int(conf_level*100)}% CI {ci_bound.title()}",
                legend="legend2",
                showlegend=True,
                hovertemplate=f"<b>{int(conf_level*100)}% CI {ci_bound.title()}</b><br>ObsAge: %{{x}}<br>Value: %{{y:6f}}<extra></extra>",                
                hoverlabel=dict(
                    bgcolor="white",           
                    bordercolor="red",        
                    font=dict(
                        family="Arial",        
                        size=12,               
                        color="red"       
                    ),
                    align="left"              
                )

            )
        )

    fig.update_layout(
        legend=dict(
            orientation="v",
            yanchor="bottom",
            y=0.035,
            xanchor="right",
            x=1,
            bgcolor="rgba(0, 0, 0, 0)",
        )
    )

    return fig


def add_year_legend_traces(fig, df, min_date, max_date, color_points):
    """
    Add year group traces for visible legend entries
    """
    # Handle empty DataFrame case
    if df.empty:
        return fig
    
    # Filter out NaT values and convert to datetime if necessary
    df_clean = df[df["snapshotDate"].notna()].copy()
    if df_clean.empty:
        return fig
    
    # Ensure snapshotDate is datetime
    if not pd.api.types.is_datetime64_any_dtype(df_clean["snapshotDate"]):
        df_clean["snapshotDate"] = pd.to_datetime(df_clean["snapshotDate"])
    
    # Extract unique years, filtering out NaN values
    years = df_clean["snapshotDate"].dt.year.dropna()
    unique_years = sorted(years.unique())
    
    for year in unique_years:
        # Get a representative snapshot date for this year
        year_data = df_clean[df_clean["snapshotDate"].dt.year == year]
        if len(year_data) > 0:
            sample_date = year_data["snapshotDate"].iloc[0]  # Use first date as representative
            color = get_color_for_date(sample_date, min_date, max_date, color_points)
            color_str = rgb_to_string(color)
            
            # Add a visible trace for the year - ensure year is formatted as integer
            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None], 
                    mode="lines",
                    name=str(int(year)),  # Format year as integer string
                    line=dict(color=color_str, width=2),
                    legend="legend1",
                    legendgroup=f"year_{int(year)}",
                    showlegend=True,
                    hoverinfo="skip"  # Don't show hover for these
                )
            )
    
    return fig


def add_snapshot_date_lines(fig, df, min_date, max_date, color_points):
    """
    Add individual snapshot date lines grouped by year
    """
    # Handle empty DataFrame case
    if df.empty:
        return fig
    
    # Filter out NaT values and convert to datetime if necessary
    df_clean = df[df["snapshotDate"].notna()].copy()
    if df_clean.empty:
        return fig
    
    # Ensure snapshotDate is datetime
    if not pd.api.types.is_datetime64_any_dtype(df_clean["snapshotDate"]):
        df_clean["snapshotDate"] = pd.to_datetime(df_clean["snapshotDate"])
    
    # Extract unique years, filtering out NaN values
    years = df_clean["snapshotDate"].dt.year.dropna()
    unique_years = sorted(years.unique())
    
    for year in unique_years:
        df_year = df_clean[df_clean["snapshotDate"].dt.year == year]
        
        for snapshot_date in sorted(df_year["snapshotDate"].unique()):
            df_subset = df_year[df_year["snapshotDate"] == snapshot_date]
            color = get_color_for_date(snapshot_date, min_date, max_date, color_points)
            trace_color_str = rgb_to_string(color)

            fig.add_trace(
                go.Scatter(
                    x=df_subset["obsAge"],
                    y=df_subset["cum_actual"],
                    mode="lines",
                    line=dict(width=1.35, color=trace_color_str),
                    opacity=0.35,
                    name=f"{year}",  # Same name as year group
                    legendgroup=f"year_{year}",  # Same group
                    showlegend=False,  # Don't show individual lines
                    customdata=df_subset[["obsDate"]],
                    text=[snapshot_date.strftime("%b %Y")] * len(df_subset),
                    hovertemplate="Date: %{text}<br>obsAge: %{x:.1f}<br>obsDate: %{customdata[0]|%Y-%m-%d}<br>Value: %{y:.6f}<extra></extra>",
                )
            )
    
    return fig


def add_color_bar(fig, df, color_points):
    """
    Add colorbar to the figure
    """
    # Handle empty DataFrame case
    if df.empty:
        return fig

    try:
        unique_years = sorted(df["snapshotDate"].dt.year.unique())
        year_range = max(unique_years) - min(unique_years)
        
        if year_range == 0:
            # Handle the case where there's only one unique year
            tickvals = [0.5]
            ticktext = [str(unique_years[0])]
        else:
            tickvals = [
                (year - min(unique_years)) / year_range for year in unique_years
            ]
            ticktext = [str(year) for year in unique_years]

        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(
                    colorscale=[(cp[0], rgb_to_string(cp[1])) for cp in color_points],
                    showscale=True,
                    cmin=0,
                    cmax=1,
                    colorbar=dict(
                        thickness=12,
                        len=0.30,
                        orientation="h",
                        x=0.01,
                        y=1,
                        xanchor="left",
                        yanchor="top",
                        tickvals=tickvals,
                        ticktext=ticktext,
                        outlinewidth=0,
                        tickangle=0,
                        title=dict(font=dict(size=10)),
                        tickfont=dict(size=8, color='black'),
                    ),
                ),
                showlegend=False,
            )
        )
    except Exception as e:
        dash_logger.warning(f'Unable to construct the colorbar: {e}')
    
    return fig


def add_analytical_components(fig, df_std, monitoring_df, monitoring_df_full, 
                            consolidated_name, cluster_list, target_list, 
                            monitoring_date, conf_level, full_path):
    """
    An orchestration function that adds all analytical components: blue line (actuals), black line (expected) with CI, 
    and restatement line
    """
    
    # Check if this is a burn report
    is_burn = check_burn_report(consolidated_name)
    
    # Add blue line (actual values)
    fig = add_blue_line(fig, monitoring_df, full_path)
    
    # Add black line (expected values) with confidence interval
    fig = add_black_line_and_ci(
        fig, df_std, monitoring_df_full, conf_level, is_burn, full_path
    )
    
    # Add restatement line
    fig = add_restatement_line(
        fig, consolidated_name, cluster_list, target_list, monitoring_date
    )
    
    return fig


def generate_tm2_fig(
    df,
    df_std,
    monitoring_date,
    consolidated_name,
    cluster_list,
    target_list,
    conf_level,
):
    try:
        # Create the plot
        fig = go.Figure()
        
        # Prepare the data
        report_type = "performance1"
        properties, full_path = parse_schema_properties(consolidated_name, report_type)

        # Calculate obsDate variable for Hover info
        current_snapshotDate = properties["current_snapshotDate"]
        current_snapshotDate = pd.to_datetime(current_snapshotDate)
        df["obsDate"] = df.apply(
            lambda row: row["snapshotDate"] + pd.DateOffset(months=row["obsAge"]),
            axis=1,
        )
        
        # Use the full df for prediction and confidence interval calculations
        monitoring_df_full = df[df["snapshotDate"] == monitoring_date].copy()
        df = df[df["obsDate"] <= current_snapshotDate]
        
        # Use for actuals 
        monitoring_df = monitoring_df_full[
            monitoring_df_full["obsDate"] <= current_snapshotDate
        ]  

        min_date = df["snapshotDate"].min()
        max_date = df["snapshotDate"].max()

        # Add historical data visualization components
        fig = add_year_legend_traces(fig, df, min_date, max_date, color_points)
        fig = add_snapshot_date_lines(fig, df, min_date, max_date, color_points)
        fig = add_color_bar(fig, df, color_points)
        
        # Update basic layout
        fig.update_layout(
            yaxis_showticklabels=True,
            xaxis_title="Observation Age",
            yaxis_title="Weighted Cumulative Sum",
            xaxis=dict(
                range=[0, None],
                showspikes=True,
                spikemode="across",
                spikethickness=1,
                spikedash="solid",
            ),
            yaxis=dict(
                range=[0, None],
                showspikes=True,
                spikemode="across",
                spikethickness=1,
                spikedash="solid",
            ),
        )

        # Add analytical components (blue, black, restatement lines)
        fig = add_analytical_components(
            fig, df_std, monitoring_df, monitoring_df_full, 
            consolidated_name, cluster_list, target_list, 
            monitoring_date, conf_level, full_path
        )

        # Configure legends
        fig.update_layout(
            legend2=dict(
                orientation="v",
                yanchor="bottom",
                y=0.035,
                xanchor="right", 
                x=1,
                bgcolor='rgba(255, 255, 255, 1)', 
                bordercolor='rgba(0, 0, 0, 0.5)',
                borderwidth=0.25,
                font=dict(
                    size=10,
                    color='black'
                ),
            ),
            # Year legend
            legend1=dict(
                orientation="h",
                x=0.5,
                y=1,
                xanchor="center",
                yanchor="top",
                bgcolor='rgba(255, 255, 255, 1)', 
                bordercolor='rgba(0, 0, 0, 0.5)',
                borderwidth=0.25,
                font=dict(
                    size=10,
                    color='black'
                ),
            )
        )
        
        return fig
        
    except Exception as e:
        error_msg = f"Failed to populate TM2 Figure for schema: {full_path}.\n{e}"
        dash_logger.error(error_msg)
        raise


def create_histogram_figure(df):
    """
    Args:
        df (pandas.DataFrame): A DataFrame containing the columns:
            - 'bucket_lb'
            - 'bucket_ub'
            - 'percentage_of_total'
            - 'percentage_of_grand_total'

    Returns:
        fig (plotly.graph_objects.Figure): A Plotly figure object with the bar plots.
    """
    df = df.round(3)
    # First try sorting by bucket_lb (numeric), then fallback to bucket_name for text categories
    try:
        # If bucket_lb is available and contains numeric data, sort by it
        if 'bucket_lb' in df.columns and not df['bucket_lb'].isna().all():
            df = df.sort_values('bucket_lb', key=lambda x: pd.to_numeric(x, errors='coerce'))
        elif 'bucket_name' in df.columns:
            # Otherwise sort by bucket_name with alphanumeric sorting
            df = df.sort_values('bucket_name', key=lambda x: pd.to_numeric(x, errors='coerce'))
        else:
            # Fallback to bucket_id if other columns are not available
            df = df.sort_values(by="bucket_id")
    except Exception:
        # If sorting fails, fallback to original bucket_id sorting
        df = df.sort_values(by="bucket_id")
    # Create the bucket labels
    df["bucket_label"] = [
        (
            f"[{lb if lb is not None else ''} - {ub if ub is not None else ''}]"
            if not (lb is None and ub is None)
            else (b_name if b_name is not None else "None")
        )
        for lb, ub, b_name in zip(df["bucket_lb"], df["bucket_ub"], df["bucket_name"])
    ]
    # Melt the DataFrame
    df_melted = df.melt(
        id_vars=["bucket_label"],
        value_vars=["Aggregate", "Cluster"],
        var_name="Percent_Type",
        value_name="Bucket Percentage (%)",
    )

    # Create the grouped bar chart using the bucket labels
    fig = px.bar(
        df_melted,
        x="bucket_label",
        y="Bucket Percentage (%)",
        color="Percent_Type",
        barmode="group",
        labels={
            "bucket_label": "Bucket Range",
            "Bucket Percentage (%)": "Bucket Percentage (%)",
        },
    )

    fig.update_layout(legend_title_text="", hovermode="x unified")

    return fig


def create_predictor_figure(df, filter):
    """
    Creates a horizontal bar chart showing KL divergence for predictors stored in Redis.
    """

    if not filter or df is None or df.empty:
        h_bar = px.bar(title="No data available")
        return h_bar

    if filter.lower() == "ascending":
        df = df.sort_values(by="kl_divergence", ascending=False).reset_index(drop=True)
    else:
        df = df.sort_values(by="kl_divergence", ascending=True).reset_index(drop=True)

    df["truncated_predictor"] = df["predictor"].apply(
        lambda x: (x[:15] + "...") if len(x) > 15 else x
    )
    h_bar = px.bar(
        df,
        x="kl_divergence",
        y="predictor",
        orientation="h",
        hover_data={"predictor": True, "kl_divergence": ":.2f"},
        opacity=0.5,
    )
    h_bar.update_traces(
        customdata=df[["predictor"]],
        hovertemplate="%{customdata[0]}<br>"
        + "<b>KL-Divergence</b>: %{x:.2f}<extra></extra>",
    )

    h_bar.update_layout(
        xaxis_title="KL-Divergence",
        yaxis_title="Predictors",
        yaxis=dict(
            type="category",
            automargin=True,
            tickmode="array",
            tickvals=df["predictor"],
            ticktext=df["truncated_predictor"],
        ),
        margin={"pad": 10},
        clickmode="event",
        dragmode=False,
        hovermode="y",
    )

    return h_bar


def create_exposure_bar_plot(consolidated_name, cluster_list):  # bottom exposure fig
    try:
        # Retrieve exposure data
        df = get_exposures_data(consolidated_name, cluster_list)

        try:
            df_grouped = df.groupby("snapshotDate", as_index=False)[
                "current_snapshotDate_exposure"
            ].sum()
        except Exception as e:
            error_msg = "Unable to populate the exposure figure."
            dash_logger.error(f"error_msg: {e}")
            raise KeyError(error_msg)

        # Create a bar plot using go.Bar
        fig = go.Figure(
            data=[
                go.Bar(
                    x=df_grouped["snapshotDate"],
                    y=df_grouped["current_snapshotDate_exposure"],
                    hovertemplate="%{y:,.0f}",
                    name="",
                )
            ]
        )

        # Update layout
        fig.update_layout(
            clickmode="event+select",
            yaxis_title="Exposure",
            showlegend=False,
            margin=dict(l=0, r=0, t=15, b=15),
            hovermode="x unified",
            hoverlabel=dict(font_size=12),
        )
        return fig

    except Exception as e:
        error_msg = (
            f"Unable to populate the exposure figure for clusters {cluster_list}.\n {e}"
        )
        dash_logger.error(error_msg)
        raise RuntimeError(error_msg)


def filter_valid_grouping_sets(df, groupby_dimension, group_cols_start):
    """
    Filters rows from a GROUPING SETS generated table:
    - If groupby_dimension == 'hybrid': Keep only rows where ALL manual dimensions are non-null.
    - Otherwise: Keep rows where groupby_dimension is not null and all other grouping columns are null,
                 and drop unnecessary columns, keeping only the value columns and groupby_dimension.
    """

    try:
        # Grouping columns (from group_cols_start onward)
        grouping_columns = df.columns[group_cols_start:]
        if len(grouping_columns) == 1:
            return df.reset_index(drop=True)

        # Validate groupby_dimension exists in grouping columns
        if groupby_dimension not in grouping_columns and groupby_dimension != "hybrid":
            raise KeyError(
                f"man dim: '{groupby_dimension}' could not found on the data!"
            )

        # Step 1: Identify "other" columns (all except groupby_dimension)
        other_columns = [col for col in grouping_columns if col != groupby_dimension]

        # Step 2: Filter logic
        if groupby_dimension == "hybrid":
            # Keep only rows where ALL manual dimensions have values
            condition = df[grouping_columns].notnull().all(axis=1)
            return df[condition].reset_index(drop=True)
        else:
            # Keep rows where groupby_dimension is not null and all other grouping columns are null
            condition = df[groupby_dimension].notnull() & df[
                other_columns
            ].isnull().all(axis=1)
            filtered_df = df[condition]

            # Drop unnecessary columns, keeping only the value columns and groupby_dimension
            value_columns = df.columns[
                :group_cols_start
            ]  # All columns before grouping columns
            return filtered_df[list(value_columns) + [groupby_dimension]].reset_index(
                drop=True
            )
    except Exception as e:
        error_msg = f"Failed to filter valid grouping sets. Grouping logic: {groupby_dimension} \n{e}"
        dash_logger.error(error_msg)
        raise


def clean_exposure_data(df):
    """
    Cleans exposure data by removing rows with missing exposure values and converting types.
    """
    try:
        column = "current_snapshotDate_exposure"
        if column not in df.columns:
            raise ValueError(
                f"Column '{column}' not found in the Current Exposure DataFrame."
            )

        df["current_snapshotDate_exposure"] = (
            df["current_snapshotDate_exposure"].fillna(0).astype(int)
        )
        return df
    except Exception as e:
        error_msg = (
            f"Error cleaning column '{column}' for Current Exposure DataFrame. {e}"
        )
        dash_logger.error(error_msg)
        raise RuntimeError(error_msg)


def create_current_exposures_df(consolidated_name, groupby_dimension):
    """
    Creates a DataFrame containing current exposure data grouped by the specified dimension.
    """
    cluster_list = []
    group_field = "cluster" if groupby_dimension == "cluster" else "mandim"

    # Fetch properties from TM1
    report_type = "performance1"
    properties, _ = parse_schema_properties(consolidated_name, report_type)

    # Extract current snapshot date
    current_snapshot_date = properties["current_snapshotDate"]
    # Retrieve recent exposures data
    current_exp_dict = get_current_exposures_data(
        consolidated_name, current_snapshot_date, cluster_list, group_field
    )

    # create and clean Dataframe
    current_exposures_df = pd.DataFrame(current_exp_dict)
    if current_exposures_df.empty:
        return current_exposures_df

    current_exposures_df = clean_exposure_data(current_exposures_df)

    if groupby_dimension == "cluster":
        return current_exposures_df

    else:
        current_exposures_df = filter_valid_grouping_sets(
            current_exposures_df, groupby_dimension, 1
        )
        return current_exposures_df


def create_r2dev_df(consolidated_name, target_value, groupby_dimension):
    cluster_list = []
    group_field = "cluster" if groupby_dimension == "cluster" else "mandim"

    # Retrieve recent exposures data
    r2_dev_dict = get_r2_dev(consolidated_name, target_value, cluster_list, group_field)

    r2_dev_df = pd.DataFrame(r2_dev_dict)  # dict -> pandas df
    if r2_dev_df.empty:
        return r2_dev_df

    if groupby_dimension == "cluster":
        return r2_dev_df
    else:
        r2_dev_df = filter_valid_grouping_sets(r2_dev_df, groupby_dimension, 1)
        return r2_dev_df
    
    
def create_fimpact_df(consolidated_name, target_value, monitoring_snapshot_date, groupby_dimension):
    group_field = "cluster" if groupby_dimension == "cluster" else "mandim"
    
    # Retrieve fimpact calculations
    fimpact_dict = get_all_financial_impact(consolidated_name, target_value, monitoring_snapshot_date, group_field)
    
    fimpact_df = pd.DataFrame(fimpact_dict)  # dict -> pandas df

    if fimpact_df.empty:
        return fimpact_df
    
    if groupby_dimension == "cluster":
        #fimpact_df["cluster"] = pd.to_numeric(fimpact_df["cluster"], errors="coerce").astype("Int64")
        return fimpact_df
    else:
        fimpact_df = filter_valid_grouping_sets(fimpact_df, groupby_dimension, 1)
        return fimpact_df
    

def create_pval_fin_impact_df(  # change its nanme with pval_exposure_score
    consolidated_name,
    target_value,
    monitoring_snapshot_date,
    z_score,
    groupby_dimension,
):
    cluster_list = []
    group_field = "cluster" if groupby_dimension == "cluster" else "mandim"

    # Fetch properties from TM1
    report_type = "performance1"
    properties, _ = parse_schema_properties(consolidated_name, report_type)

    # Extract current snapshotDate
    if "current_snapshotDate" not in properties:
        error_msg = f"'current_snapshotDate' key is missing in the lookup table for {consolidated_name}"
        dash_logger.error(error_msg)
        raise KeyError(error_msg)

    current_snapshot_date = properties["current_snapshotDate"]
    if not current_snapshot_date:
        error_msg = f"'current_snapshot_date' key is empty or invalid in the lookup table for {consolidated_name}"
        dash_logger.error(error_msg)
        raise ValueError(error_msg)

    # Retrieve z-scores and exposure scores data
    pval_and_fin_impact_dict = get_pval_and_fin_impact(
        consolidated_name,
        target_value,
        monitoring_snapshot_date,
        current_snapshot_date,
        cluster_list,
        z_score,
        group_field,
    )

    # Convert dict to pandas df
    pval_and_fin_impact_df = pd.DataFrame(pval_and_fin_impact_dict)
    if pval_and_fin_impact_df.empty:
        return pval_and_fin_impact_df

    if groupby_dimension == "cluster":
        return pval_and_fin_impact_df
    else:
        pval_and_fin_impact_df = filter_valid_grouping_sets(
            pval_and_fin_impact_df, groupby_dimension, 2
        )
        return pval_and_fin_impact_df
