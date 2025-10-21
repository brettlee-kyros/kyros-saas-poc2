from plotly.subplots import make_subplots
import plotly.graph_objs as go
import plotly.express as px
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np

from kyros_plotly_common.utils.ui import create_empty_plot
from kyros_plotly_common.core.errors import PlotError
from kyros_plotly_common.logger import dash_logger
from kyros_plotly_common.utils.schema import parse_schema_properties
from kyros_plotly_common.utils.date import format_date_display
from kyros_plotly_common.layout.graph.comparison_charts import create_histogram_figure, create_mix_figure


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



def update_distribution_comparison(consolidated_name, selected_variable, date1, date2, weight, view_type):
    """
    Update the distribution comparison visualization
    
    Args:
        full_path: Full path to the table
        selected_variable: Selected variable for comparison
        date1: First date for comparison
        date2: Second date for comparison
        weight: Weight column to use
        view_type: View type (histogram or mix)
        
    Returns:
        dict: Plotly figure object
    """
    try:
        # Get properties for this table
        properties, _ = parse_schema_properties(consolidated_name,report_type="mix")
        if not properties:
            return create_empty_plot("Date range unavailable for the selected mix type")
        if date1 > date2:
            return create_empty_plot("Date 1 should be earlier than Date 2")
        date_label = properties.get("mix_type", "Date")
        distributions = selected_variable.get('distributions', {})
        bucket_labels = selected_variable.get('bucket_labels', {})
        if date1 not in distributions or date2 not in distributions:
            return create_empty_plot("Selected dates not available in the dataset")
        variable_name = selected_variable.get('variable', 'Unknown')
        if not view_type:
            date1_dist = dict(distributions.get(date1, {}))
            date2_dist = dict(distributions.get(date2, {}))
            cats = list(set(date1_dist.keys()) | set(date2_dist.keys()))
            # Sort by int(category)
            def parse_int(cat):
                try:
                    return int(cat)
                except Exception:
                    return 0
            cats_sorted = sorted(cats, key=parse_int)
            df = pd.DataFrame({
                'category': cats_sorted,
                'date1': [date1_dist.get(str(cat), 0) for cat in cats_sorted],
                'date2': [date2_dist.get(str(cat), 0) for cat in cats_sorted]
            })
            return create_histogram_figure(
                df,
                'date1',
                'date2', 
                variable_name,
                weight,
                date_label,
                format_date_display(date1),
                format_date_display(date2),
                bucket_labels
            )
        else:
            all_dates = sorted(distributions.keys())
            all_dates_dist = {date: dict(distributions.get(date, {})) for date in all_dates}
            categories = list(set().union(*[all_dates_dist[date].keys() for date in all_dates]))
            # Sort by int(category)
            def parse_int(cat):
                try:
                    return -int(cat)
                except Exception:
                    return 0
            categories_sorted = sorted(categories, key=parse_int)
            df = pd.DataFrame({
                'category': categories_sorted,
                **{date: [all_dates_dist[date].get(cat, 0) for cat in categories_sorted] for date in all_dates}
            })
            return create_mix_figure(
                df, 
                all_dates, 
                date1, 
                date2, 
                variable_name, 
                date_label, 
                bucket_labels=bucket_labels,
                column_formatter=format_date_display
            )
    except Exception as e:
        error_msg = f"Failed to update distribution comparison: {e}"
        error_id = dash_logger.error(error_msg, exc_info=e)
        raise PlotError(error_msg, error_id) from e