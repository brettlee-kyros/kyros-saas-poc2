from collections import defaultdict
from dash import html
from datetime import datetime
from calendar import monthrange
import plotly.graph_objs as go
import pandas as pd
import re
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import numpy as np

from scipy.stats import norm
from kyros_plotly_common.logger.dash_logger import dash_logger
from kyros_plotly_common.core.redis_client import redis_instance, get_from_redis
from kyros_plotly_common.utils.schema import parse_schema_properties
from kyros_plotly_common.utils.ui import create_date_dropdown_options

def parse_and_format_target_options(consolidated_name):
    """
    Parse and format target options for a given consolidated name.

    Args:
        redis_instance: Redis instance connection
        consolidated_name: The consolidated name (e.g., 'burn__1__20241018_204345')

    Returns:
        list: List of dictionaries formatted for dropdown options, excluding 'exposure'
    """
    try:
        # Get table mappings from Redis
        table_mappings = get_from_redis("table_mappings")
        if not table_mappings or consolidated_name not in table_mappings:
            print(f"No table mapping found for {consolidated_name}")
            return []

        # Get tml1 information
        report_type = "performance1"
        properties, _ = parse_schema_properties(consolidated_name, report_type)
        targets = properties.get("targets", {})
        target_list = [key for key, value in targets.items() if value.get("statistic") == "average"]

        # Create dropdown options, excluding 'exposure'
        target_options = [{"label": target, "value": target} for target in target_list]

        # Sort alphabetically
        target_options = sorted(target_options, key=lambda x: x["value"])

        return target_options

    except Exception as e:
        print(f"Error processing target options: {str(e)}")
        return []


def get_recent_exposures(consolidated_name, cluster_list):
    """
    Retrieve the most recent exposure data from Redis for specific cluster_collapse values within a chosen schema.

    Parameters:
        consolidated_name
        cluster_list (list): List of cluster_collapse values to fetch data for.

    Returns:
        tuple: Two lists - one of recent exposure values and one of cluster values.
               Returns None if no data is found or if cluster_list is None.
    """
    if not cluster_list:
        print("Cluster list is None.")
        return [], []

    cluster_vals = []
    recent_exp_values = []
    row_key = None

    properties = get_tm1_properties(consolidated_name)
    if not properties:
        return None

    current_snapshotDate = properties["current_snapshotDate"]

    for cluster_value in cluster_list:
        if cluster_value is not None:
            try:
                # cluster_value = float(cluster_value)
                row_key = f"{consolidated_name}__cluster_exposures:{cluster_value}"
                data = get_from_redis(row_key)

                if not data:
                    print(f"No data found for key {row_key}")
                    continue

                # Find the entry that matches current_snapshotDate
                recent_entry = next(
                    (
                        entry
                        for entry in data
                        if entry.get("snapshotDate") == current_snapshotDate
                    ),
                    None,
                )

                # Only append if a matching entry with a non-None 'value' is found
                if recent_entry and recent_entry.get("value") is not None:
                    recent_exp_values.append(recent_entry["value"])
                    cluster_vals.append(cluster_value)
                # else:
                # print(f"No matching data found for current snapshot date in key {row_key}.")

            except (TypeError, KeyError) as e:
                print(f"Error processing data from Redis for key {row_key}: {e}")

    return (
        (recent_exp_values, cluster_vals)
        if recent_exp_values and cluster_vals
        else None
    )


def bar_chart_height_calculator(n, k=2.4, unit="px"):
    """
    Gets number of categories, growth factor and returns total height of the bar graph
    as a css dictionary format.
    Hint: Come up with a growth factor which in line with the selected unit.

    Parameters:
        n (int): (positive) number of categories (clusters for majority of cases).
        k (float): growth factor (Default = 1.8).
        unit (str): css units such as px, vh. (Default =  'px')

    Returns:
        style (dict): A dictionary contains css height attribute.
    """

    if not isinstance(n, int):
        raise TypeError("The number of categories 'n' must be an integer.")

    if n <= 0:
        raise ValueError("The number of categories 'n' must be a positive integer.")

    if not isinstance(k, (int, float)):
        raise TypeError("The growth factor 'k' must be a number.")

    if k < 1:
        raise ValueError("The growth factor 'k' should be bigger than 1 .")

    valid_units = ["vh", "cm", "mm", "in", "px", "pt", "pc"]

    # Check if the unit is valid, otherwise set it to 'px'.
    if unit not in valid_units:
        unit = "px"

    if n <= 5:
        n = n + 4

    height = round(n * k)

    style_height = f"{height}{unit}"
    style = {"height": style_height}

    return style


def fetch_exposures_from_redis(consolidated_name, cluster_list):
    """
    This function retrieves the data from Redis for specific cluster_collapse values within a single schema.

    Parameters:
    - consolidated_name
    - cluster_list: List of cluster_collapse values to fetch data for.

    Returns:
    - List of rows containing the data from Redis.
    """

    if not consolidated_name:
        return None

    rows = []

    if cluster_list:
        for cluster_value in cluster_list:
            row_key = f"{consolidated_name}__cluster_exposures:{cluster_value}"
            data = get_from_redis(row_key)

            if data is not None:
                rows.extend(data)
    else:  # if the cluster list is empty
        row_key_pattern = f"{consolidated_name}__cluster_exposures:*"
        all_keys = redis_instance.keys(row_key_pattern)  # Fetch all matching keys
        for row_key in all_keys:
            data = get_from_redis(row_key)
            if data is not None:
                rows.extend(data)

    return rows if rows else None


def create_exposure_fig(df):

    if df.empty:
        return go.Figure(layout=go.Layout(title="No data available"))

    # Create a bar plot using go.Bar
    fig = go.Figure(
        data=[
            go.Bar(
                x=df["snapshotDate"],
                y=df["value"],
                hovertemplate="%{y:,.0f}",
                name="",
            )
        ]
    )

    # Update layout
    fig.update_layout(
        clickmode="event+select",
        yaxis_title="Exposure",
        # xaxis_title='SnapshotDate',
        margin=dict(l=0, r=0, t=15, b=15),
        hovermode="x unified",
        hoverlabel=dict(font_size=12),
    )

    return fig

def check_burn_report(consolidated_name):
    return "burn" in consolidated_name.lower()


def interpolate_month_ends(start_date_str, end_date_str):
    """
    Generate a list of last days of each month between start_date and end_date (inclusive).

    Args:
        start_date_str (str): Start date in 'YYYY-MM-DD' format
        end_date_str (str): End date in 'YYYY-MM-DD' format

    Returns:
        list[str]: List of dates in 'YYYY-MM-DD' format representing the last day of each month
    """
    # Convert string dates to datetime objects
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    # Initialize result list
    result = []

    # Get the last day of start_date's month
    _, start_last_day = monthrange(start_date.year, start_date.month)
    current = datetime(start_date.year, start_date.month, start_last_day)

    while current <= end_date:
        # Only add dates that fall within our range (inclusive)
        if start_date <= current <= end_date:
            result.append(current.strftime("%Y-%m-%d"))

        # Move to last day of next month
        if current.month == 12:
            current = datetime(current.year + 1, 1, 31)
        else:
            _, last_day = monthrange(current.year, current.month + 1)
            current = datetime(current.year, current.month + 1, last_day)

    return result[::-1]  # order current to oldest


def get_tm1_properties(consolidated_name):
    """
    Get and validate TM1 properties.

    Args:
        consolidated_name: Base name for properties

    Returns:
        Dictionary of TM1 properties
    """
    report_type = "performance1"
    properties, _ = parse_schema_properties(consolidated_name, report_type)
    return properties


def create_age_slider_marks(max_obsage):
    """
    Create age slider marks dictionary.

    Args:
        max_obsage: Maximum observation age

    Returns:
        Dictionary of slider marks
    """

    interval = 10 if max_obsage <= 100 else 20
    marks = {i: str(i) for i in range(0, max_obsage + 1, interval)}
    marks[max_obsage] = str(max_obsage)
    return marks


def get_monitoring_dates(consolidated_name):
    """
    Get monitoring dates from TM2 properties.

    Args:
        consolidated_name: Base name for properties

    Returns:
        List of datetime objects for monitoring dates
    """
    report_type = "performance2"
    properties, _ = parse_schema_properties(consolidated_name, report_type)
    if not properties:
        return []

    try:
        monitoring_sdates = properties["monitoring_snapshotDate"]["values"]
        return monitoring_sdates
    except Exception as e:
        raise type(e)(f"Failed to process monitoring dates: {str(e)}") from e

def sort_labels(data):
    def get_sort_key(item):
        # Split into text and number parts
        text, num = item["manual_dimension"].split("_")
        # Convert number to integer for numerical sorting
        return (text, int(num))

    return sorted(data, key=get_sort_key)


def get_current_snapshotdate(consolidated_name):
    properties = get_tm1_properties(consolidated_name)
    if not properties:
        return []

    if "current_snapshotDate" not in properties:
        dash_logger.info("'current_snapshotDate' key is missing in the lookup schema")

    if not properties["current_snapshotDate"]:
        dash_logger.info(
            "'current_snapshotDate' key is empty or invalid in the lookup schema."
        )

    current_snapshotdate = properties["current_snapshotDate"]

    return current_snapshotdate


def get_range_slider_options(consolidated_name):
    properties = get_tm1_properties(consolidated_name)
    if not properties:
        return [], []

    start_date = datetime.strptime(properties["first_snapshotDate"], "%Y-%m-%d")
    end_date = datetime.strptime(properties["current_snapshotDate"], "%Y-%m-%d")

    date_range = (
        pd.date_range(start_date, end_date, freq="M").strftime("%Y-%m-%d").tolist()
    )

    def generate_year_marks(dates):
        marks = {}
        try:
            for i, date in enumerate(dates):
                year = date[:4]
                month = date[5:7]

                if month == "01":
                    marks[i] = str(int(year))
            return marks
        except:
            print("Returning empty range picker..")
            return marks

    date_slider_marks = generate_year_marks(date_range)

    return date_range, date_slider_marks


def format_component_options(consolidated_name):
    """
    Format component options for the dashboard.

    Args:
        consolidated_name: Base name for the component

    Returns:
        Tuple containing:
        - Maximum observation age
        - Dictionary of age slider marks
        - List of monitoring snapshot date options for dropdown
        - . . .
    """

    # Get and process TM1 properties
    properties = get_tm1_properties(consolidated_name)
    if not properties:
        return None

    max_obsage = properties["max_obsAge"]
    min_obsage = 0

    # Create slider marks
    age_slider_marks = create_age_slider_marks(max_obsage)

    # Get and process snapshot dates
    first_snapshotdate = properties["first_snapshotDate"]
    current_snapshotdate = properties["current_snapshotDate"]
    snapshotdates_list = interpolate_month_ends(
        first_snapshotdate, current_snapshotdate
    )

    # Get monitoring dates
    monitoring_snapshotdates = get_monitoring_dates(consolidated_name)

    # Create dropdown options
    monitoring_snapshotdate_options = create_date_dropdown_options(
        snapshotdates_list, monitoring_snapshotdates
    )

    date_range, date_slider_marks = get_range_slider_options(consolidated_name)

    return (
        min_obsage,
        max_obsage,
        age_slider_marks,
        monitoring_snapshotdate_options,
        date_range,
        date_slider_marks,
    )


def validate_targets(targets):
    """Validate and normalize targets input."""
    if isinstance(targets, str):
        return [targets]
    if not isinstance(targets, list):
        raise TypeError("targets must be either a string or a list of strings")
    if not all(isinstance(t, str) for t in targets):
        raise TypeError("Each target must be a string")
    return targets


def flag_dev_since_dev_metric(consolidated_name, targets):
    """
    Check if any target has dev_since development metric.

    Args:
        consolidated_name: Name of the consolidated schema
        targets: Single target string or list of target strings to check

    Returns:
        bool: True if dev_since metric is found, False if not found or error occurred

    Raises:
        TypeError: If targets input is invalid
        ValueError: If properties cannot be retrieved or are invalid
    """
    try:
        report_type = "performance1"
        properties, _ = parse_schema_properties(consolidated_name, report_type)
    except:
        print("Properties not found for the selected lookup schema.")
        return None

    targets = validate_targets(targets)

    try:
        return any(
            properties["targets"][target]["development_metric"] == "dev_since"
            for target in targets
        )
    except KeyError as e:
        print(f"Invalid properties structure: missing {e}")
        return None


def revise_string(input_str):
    # Split into parts by comma
    parts = input_str.split(",")

    # Get the second part (value) from each section by splitting on ':'
    part1_value = parts[0].split(":")[1].strip()
    part2_value = parts[1].split(":")[1].strip()

    # Combine the values with ': ' between them
    return f"{part1_value}_{part2_value}"


def create_manual_dim_dict(df):
    """
    DataFrame containing 'manual_dimension' and 'cluster' columns

    Returns:
    dict: Mapping dictionary with manual dimensions as keys and cluster lists as values
    """
    # Initialize empty dictionary
    mapping_dict = {}

    df["manual_dimension"] = df["manual_dimension"].astype(str)
    df["manual_dimension"] = df["manual_dimension"].apply(lambda x: revise_string(x))

    # Convert DataFrame to list of dictionaries
    table = df.to_dict("records")

    # Create mapping
    for item in table:
        manual_dimension = item["manual_dimension"]
        # Split cluster string on commas, strip whitespace
        clusters = [cluster.strip() for cluster in item["cluster"].split(",")]
        mapping_dict[manual_dimension] = clusters

    return mapping_dict


def is_numeric_column(series):
    """
    Checks if a pandas Series contains numeric strings by examining the first non-null value.

    Parameters:
    series (pd.Series): Input series to analyze

    Returns:
    bool: True if the column contains numeric strings, False otherwise
    """
    # Get first non-null value
    first_value = series.dropna().iloc[0] if not series.empty else None

    if first_value is None:
        return False

    if isinstance(first_value, str):
        first_value = first_value.strip()
    else:
        return False  # If not string, it's not a numeric string

    # Check if it matches numeric patterns
    integer_pattern = r"^-?\d+$"
    float_pattern = r"^-?\d*\.?\d+$"

    return bool(
        re.match(integer_pattern, first_value) or re.match(float_pattern, first_value)
    )


def convert_mandim_columns_type(df):
    """
    Detect string columns containing only numeric values and convert them to integers.

    Parameters:
    df (pandas.DataFrame): Input DataFrame

    Returns:
    pandas.DataFrame: DataFrame with numeric strings converted to integers
    """
    # Create a copy to avoid modifying the original DataFrame
    df_copy = df.copy()

    # Get string columns
    string_columns = df_copy.select_dtypes(include=["object"]).columns

    for col in string_columns:
        # Check if all values in the column (excluding NaN) can be converted to integers
        try:
            # Remove whitespace and check if the strings are numeric
            is_numeric = df_copy[col].str.strip().str.match(r"^-?\d+$").fillna(False)

            if is_numeric.all():
                # Convert the column to integer
                df_copy[col] = df_copy[col].str.strip().astype(int)
        except:
            continue

    return df_copy


def get_icon(icon, height=None, color=None):
    return DashIconify(icon=icon, height=height, color=color)


def conf_level_to_zscore(confidence_level):
    # Validate the input
    if not (0 < confidence_level < 1):
        raise ValueError("Confidence level must be between 0 and 1!")
    # return the positive zscore
    return norm.ppf(
        1 - (1 - confidence_level) / 2
    )  # (1-confidence_level) = significance_level


def zscore_to_pvalue(z):
    if z is None or np.isnan(z):
        return np.nan
    return norm.cdf(z)


def pval_to_pscore(p_value):
    if p_value is None or np.isnan(p_value):
        return np.nan
    return 0.5 - abs(0.5 - p_value)


def create_hierarchy_signal_children(signal):
    return [
        html.Div(
            id="hierarchy-signal-icon",
            children=get_icon(signal["icon"], 20),
        ),
        dbc.Tooltip(
            signal["tooltip"],
            id="hierarchy-tooltip",
            placement="left",
            target="hierarchy-signal-icon",
            trigger="hover focus",
        ),
    ]

def create_cluster_signal_children(signal):
    return [
        html.Div(
            id="selector-signal-icon",
            children=get_icon(signal["icon"], 30, color=signal["color"]),
        ),
        dbc.Tooltip(
            signal["tooltip"],
            id="clusters-tooltip",
            placement="left",
            target="selector-signal-icon",
            trigger="hover focus",
        ),
    ]


def determine_selector_signal(selected_clusters):
    """
    Determine the selector signal based on the number of selected clusters.

    Returns:
        dict: A dictionary representing the selector signal with icon, color, and tooltip.
    """
    if not selected_clusters:
        return {
            "icon": "mynaui:letter-w-square",
            "color": "black",
            "tooltip": "Warning: No cluster belongs to selected combination of manual dimensions!",  # no cluster name
        }

    elif len(selected_clusters) == 1:
        return {
            "icon": "mynaui:letter-s-square",
            "color": "green",
            "tooltip": selected_clusters[0],  # Single cluster name
        }
    else:
        # Filter out NaN values before converting
        valid_clusters = [x for x in selected_clusters if pd.notna(x)]
        return {
            "icon": "mynaui:letter-m-square",
            "color": "red",
            "tooltip": ", ".join(str(int(x)) for x in valid_clusters),
        }


def extract_clusters(data_list):
    """
    Extract 'cluster' values from a list of dictionaries.
    Returns None if no cluster key is found in any dictionary.
    """
    if not isinstance(data_list, list):
        raise TypeError("Input must be a list of dictionaries")

    clusters = [
        row.get("cluster") for row in data_list
    ]  # loop through number of selections.
    return [cluster for cluster in clusters if cluster is not None] or None


def get_matching_clusters(df, dynamic_key_values_list):
    """
    Extract cluster values from DataFrame where any (man dim) dynamic column values match the given combinations.

    Returns:
        List of unique cluster values matching any of the conditions.
    """
    if not dynamic_key_values_list:
        return None

    df = convert_mandim_columns_type(df)  # Convert columns if necessary

    # Build a single combined condition for all key-value pairs
    combined_condition = pd.Series(False, index=df.index)
    for key_values in dynamic_key_values_list:
        # For each combination, create a condition and 'OR' it with the combined condition
        condition = pd.Series(True, index=df.index)
        for key, value in key_values.items():
            condition &= df[key] == value
        combined_condition |= condition

    # Filter the DataFrame and extract unique clusters as list
    matching_clusters = df[combined_condition]["cluster"].dropna().unique().tolist()
    # matching_clusters = df[combined_condition]["cluster"].unique().tolist()
    return matching_clusters if matching_clusters else None


def to_percentage(value, decimals=3):
    """Convert a number between 0 and 1 to a percentage string."""
    return f"{value * 100:.{decimals}f}%"  


def generate_significant_text(calc_z_score, conf_level):
        if calc_z_score.isna().all():
            return " "
        
        p_val = zscore_to_pvalue(calc_z_score.iloc[0])
        p_score = pval_to_pscore(p_val)
        
        # calcualte threshold
        conf_level = conf_level / 100
        alpha = 1 - conf_level
        p_score_threshold = alpha / 2
        
        #pscore < p threshold flag
        return f"Statistically Significant ({p_score:.3f})" if p_score <= p_score_threshold else " "

def months_between(date1, date2):
    """
    Calculate the number of months between two end-of-month dates.
    Both dates should be in format 'YYYY-MM-DD'.
    
    Args:
        date1: String date in format 'YYYY-MM-DD'
        date2: String date in format 'YYYY-MM-DD'
    
    Returns:
        int: Absolute number of months between the two dates
    """
    # Parse the dates
    d1 = datetime.strptime(date1, "%Y-%m-%d")
    d2 = datetime.strptime(date2, "%Y-%m-%d")
    
    # Calculate difference in months
    # Formula: (year_difference * 12) + month_difference
    months_diff = abs((d2.year - d1.year) * 12 + (d2.month - d1.month))
    
    return months_diff
