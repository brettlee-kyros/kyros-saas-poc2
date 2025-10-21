import datetime
from functools import reduce
import pandas as pd

from utils.dbx_utils import get_manual_dimensions
from kyros_plotly_common.utils.schema import parse_schema_properties
from kyros_plotly_common.layout.datagrid import GridConfig, create_grid

from utils.helper_functions import (
    convert_mandim_columns_type,
    conf_level_to_zscore,
    zscore_to_pvalue,
    pval_to_pscore,
)

from utils.viz_functions import (
    create_current_exposures_df,
    create_r2dev_df,
    create_pval_fin_impact_df,
    create_fimpact_df
)

TABLE_HEADERS = {
    "cluster": "Cluster",
    "r2_dev": "R² Dev",
    "current_snapshotDate_exposure": "Current Exposure",
    "p_score": "P-Score",
    "exposure_score": "Exposure Score",
    "financial_impact": "Liability Impact",
}

FIXED_COLUMNS = [
    "cluster",
    "current_snapshotDate_exposure",
    "r2_dev",
    "p_score",
    "exposure_score",
    "financial_impact",
]

BAR_RENDERER_COLUMNS = [
    "r2_dev",
    "current_snapshotDate_exposure",
    "p_score",
    "exposure_score",
    "financial_impact"
]


def create_table_csvfile_name(consolidated_name):
    timestamp = datetime.datetime.now().strftime("%Y%m%d__%H%M")
    return f"{consolidated_name}__{timestamp}.csv"


def create_custom_header_tooltip(consolidated_name, monitoring_date):
    # Get and process TM1 properties
    report_type = "performance1"
    properties, _ = parse_schema_properties(consolidated_name, report_type)
    current_snapshotdate = properties.get("current_snapshotDate", "")

    return {
        "cluster": "Cluster",
        "r2_dev": "R² Dev",
        "current_snapshotDate_exposure": f"Current Exposure ({current_snapshotdate})",
        "p_score": f"P-Score ({monitoring_date})",
        "exposure_score": f"Exposure Score ({monitoring_date})",
        "financial_impact": f"Financial Impact ({monitoring_date})",
    }


def extract_dynamic_column_value(data_list):
    """
    Extract unique combinations of man dim column key-value pairs,
    excluding constant columns.
    Manual dimension column names are dynamic!

    Returns:
        List of dictionaries with unique combinations of dynamic column key-value pairs.
    """
    try:
        constant_columns = FIXED_COLUMNS[1:]  # ignore 'clusters'

        # check the first row to identify dynamic keys
        dynamic_keys = [
            key for key in data_list[0].keys() if key not in constant_columns
        ]

        # Use a set to track unique combinations (tuples), then convert back to dictionaries
        unique_combinations = set()
        for row in data_list:
            # Extract only dynamic columns for this row
            dynamic_values = tuple((key, row[key]) for key in dynamic_keys)
            unique_combinations.add(dynamic_values)

        # Convert unique combinations back into a list of dictionaries
        unique_combinations_list = [
            dict(combination) for combination in unique_combinations
        ]
        return unique_combinations_list
    except Exception as e:
        raise type(e)(
            f"Failed to extract manual dimensions on bubbler: {str(e)}"
        ) from e


def get_column_order(df_columns, fixed_columns=FIXED_COLUMNS):
    """Determine the final column order with fixed columns first."""
    dynamic_columns = [col for col in df_columns if col not in fixed_columns]
    return fixed_columns + dynamic_columns


def create_bar_renderer_params(col_name, df):
    """Create bar renderer parameters for applicable columns."""
    try:
        max_values = {}
        for col in ["current_snapshotDate_exposure", "exposure_score", "p_score", "financial_impact"]:
            if col in df.columns:
                max_values[col] = df[col].dropna().max()

        if col_name not in BAR_RENDERER_COLUMNS:
            return {}

        max_value = 1 if col_name in {"r2_dev"} else max_values.get(col_name)
        return {
            "cellRenderer": "BarRenderer",
            "cellRendererParams": {"context": {"maxValue": max_value}},
        }
    except Exception as e:
        raise type(e)(
            f"Failed to create the bar renderers for bubbler: {str(e)}"
        ) from e


def create_header_params(col_name, is_first_column, button_icon):
    """
    Create header parameters for columns.

    - If 'cluster' is the first column, use the combined header template.
    - If another column is the first column, use the refresh-only template.
    - Otherwise, use the standard grouping template.
    """
    if col_name in BAR_RENDERER_COLUMNS and not is_first_column:
        return {}

    if col_name == "cluster" and is_first_column:
        # Combined template for 'cluster' as the first column
        template = generate_combined_header_template(
            field=col_name, button_icon=button_icon
        )
    else:
        # Default behavior
        template = (
            generate_header_with_refresh()
            if is_first_column
            else generate_header_template(col_name, button_icon=button_icon)
        )

    return {"headerComponentParams": {"template": template}}


def create_column_definitions(
    df, consolidated_name, monitoring_date, button_icon="up", first_col_name=None
):
    """
    Create column definitions for the grid.

    Parameters:
        - df: DataFrame containing columns.
        - button_icon: Icon for grouping buttons (default "up").
        - first_col_name: Optional; column to treat as the first column.
    """
    final_column_order = get_column_order(df.columns)
    first_col_name = (
        first_col_name or final_column_order[0]
    )  # Default to the first column

    HEADER_TOOLTIPS = create_custom_header_tooltip(consolidated_name, monitoring_date)

    return [
        {
            "headerName": TABLE_HEADERS.get(col, col),
            "field": col,
            "headerTooltip": HEADER_TOOLTIPS.get(col, col),
            "sortable": True,
            "filter": True,
            "width": 90,
            **create_bar_renderer_params(col, df),
            **create_header_params(
                col_name=col,
                is_first_column=(col == first_col_name),
                button_icon=button_icon,
            ),
        }
        for col in final_column_order
        if col in df.columns
    ]


def create_bubbler_grid(
    consolidated_name, column_defs, row_data, conf_level, filter_conditions
):
    """
    Create the AG-Grid component with dynamic row filtering using the new GridConfig.
    Returns:
        AgGrid: Dash AG-Grid component with specified configurations.
    """
    alpha = 1 - conf_level
    p_score_threshold = alpha / 2

    # Define row styles based on p-score thresholds
    style_conditions = [
        # Highlight significant rows, but exclude None values
        {
            "condition": f"params.data.p_score != null && params.data.p_score <= {p_score_threshold}",
            "style": {"backgroundColor": "#FEDDC1"},
        },
    ]

    # Determine selected rows based on filter_conditions
    if isinstance(filter_conditions, dict) and "function" in filter_conditions:
        selected_rows = filter_conditions  # Use the provided filter function
    else:
        selected_rows = []  # Default to empty if no valid conditions

    # Define additional grid options specific to bubbler
    additional_options = {
        "alwaysShowHorizontalScroll": True,
        "rowMultiSelectWithClick": False,
        "suppressRowDeselection": False,
        "csvExportParams": {
            "fileName": create_table_csvfile_name(consolidated_name),
            "skipHeader": False,
        },
    }

    # Create GridConfig
    config = GridConfig(
        id="bubbler-table",
        column_defs=column_defs,
        row_data=row_data,
        multi_select=True,  # Enable multi-row selection
        header_checkbox=True,
        side_bar=False,
        selected_rows=selected_rows,
        style_conditions=style_conditions,
        additional_options=additional_options
    )

    # Create the grid using the common library
    grid = create_grid(config)
    
    # Override the style to match the original bubbler style
    grid.style = {
        "height": "calc(81vh - 90px)",
        "min-height": "calc(81vh - 90px)",
        "width": "100%",
    }

    return grid


def calculate_pscore_exp_score(
    consolidated_name, target_value, monitoring_date, conf_level, group_field
):
    """
    Calculates p-score and exposure score and returns the corresponding DataFrame.
    """
    z_score = conf_level_to_zscore(conf_level)

    pval_fin_impact_df = create_pval_fin_impact_df(
        consolidated_name, target_value, monitoring_date, z_score, group_field
    )

    if pval_fin_impact_df.empty:
        return pval_fin_impact_df

    try:
        pval_fin_impact_df["p_value"] = pval_fin_impact_df["z_score"].apply(
            zscore_to_pvalue
        )
        pval_fin_impact_df["p_score"] = pval_fin_impact_df["p_value"].apply(
            pval_to_pscore
        )

        # Drop intermediate columns
        pval_fin_impact_df.drop(["z_score", "p_value"], axis=1, inplace=True)

    except Exception as e:
        raise type(e)(f"Failed to convert Z-scores to P-values: {str(e)}") from e

    # Reorder columns to move 'cluster' to the end
    if "cluster" in pval_fin_impact_df.columns:
        columns = [col for col in pval_fin_impact_df.columns if col != "cluster"] + [
            "cluster"
        ]
        pval_fin_impact_df = pval_fin_impact_df[columns]

    return pval_fin_impact_df


def merge_dataframes(dataframes_dict, group_field):
    """
    Merges multiple dict of DataFrames on the specified group field using an outer join.
    """
    try:
        if not isinstance(dataframes_dict, dict):
            raise TypeError("Dictionary of dataframes must be provided.")

        # Convert dictionary to list for processing
        dataframes = list(dataframes_dict.values())
        if all(df.empty for df in dataframes):
            raise ValueError("All provided DataFrames are empty.")

        # Dynamically determine the merge field
        if group_field == "hybrid":
            # Get first non-empty dataframe for group field
            first_nonempty_df = next(df for df in dataframes if not df.empty)
            group_field = [
                col for col in first_nonempty_df.columns if col not in FIXED_COLUMNS
            ]

            if not group_field:
                raise ValueError(
                    "Provided Dataframes do not have valid dim column(s) for hybrid merge."
                )
        try:
            # Filter out empty dataframes
            non_empty_dfs = [df for df in dataframes if not df.empty]
            result = reduce(
                lambda left, right: left.merge(right, on=group_field, how="outer"),
                non_empty_dfs,
            )
            return result

        except Exception as e:
            raise type(e)(f"Failed to merge DataFrames: {str(e)}") from e

    except Exception as e:
        raise type(e)(f"Bubbler error on merging DataFrames: {str(e)}") from e


def create_combined_dataframe(
    consolidated_name,
    target_value,
    monitoring_date,
    conf_level,
    group_field=None,
    include_manual_dimensions=False,
):
    """
    Combines current exposures, R2 development, P-Score, Exposure Score and optional manual dimensions into a single DataFrame.
    """
    # Default to "cluster" if no group_field is provided
    group_field = group_field or "cluster"

    # Generate required DataFrames
    current_exposures_df = create_current_exposures_df(consolidated_name, group_field)
    r2dev_df = create_r2dev_df(consolidated_name, target_value, group_field)
    pscore_exp_score_df = calculate_pscore_exp_score(
        consolidated_name, target_value, monitoring_date, conf_level, group_field
    )
    fimpact_df =create_fimpact_df(consolidated_name, target_value, monitoring_date, group_field)
    
    bubbler_dfs = {
        "curret_exposures_df": current_exposures_df,
        "r2dev_df": r2dev_df,
        "pscore_exp_score_df": pscore_exp_score_df,
        "financial_impact_df": fimpact_df,
    }

    # Merge all DataFrames
    combined_df = merge_dataframes(bubbler_dfs, group_field)

    # Optionally include manual dimensions
    if include_manual_dimensions:
        man_dim_dict = get_manual_dimensions(consolidated_name)
        man_dim_df = pd.DataFrame(man_dim_dict)
        combined_df = combined_df.merge(man_dim_df, on=group_field, how="outer")

    combined_df = convert_mandim_columns_type(combined_df)
    return combined_df


def generate_grid(
    consolidated_name,
    target_value,
    monitoring_date,
    conf_level,
    group_field=None,
    include_manual_dimensions=False,
    skip_cluster_column=False,
):
    df = create_combined_dataframe(
        consolidated_name,
        target_value,
        monitoring_date,
        conf_level,
        group_field=group_field,
        include_manual_dimensions=include_manual_dimensions,
    )
    first_col_index = 1 if skip_cluster_column else 0
    first_col_name = get_column_order(df.columns)[first_col_index]
    button_icon = "down" if group_field else "up"
    column_defs = create_column_definitions(
        df,
        consolidated_name,
        monitoring_date,
        button_icon=button_icon,
        first_col_name=first_col_name,
    )
    return df, column_defs


def get_selected_manual_dimensions(consolidated_name, group_field, selected_clusters):
    """
    Dynamically create AG-Grid filter logic for hybrid or specific group_field.

    Returns:
        dict: Filter logic for AG-Grid's dynamic row filtering.
    """
    try:
        # Retrieve manual dimensions
        man_dim_dict = get_manual_dimensions(consolidated_name)
        man_dim_df = pd.DataFrame(man_dim_dict)
        man_dim_df = convert_mandim_columns_type(man_dim_df)

        if "cluster" not in man_dim_df.columns:
            raise KeyError(
                "'cluster' column is missing in manual dimensions DataFrame."
            )

        if man_dim_df["cluster"].empty or man_dim_df["cluster"].isna().all():
            raise ValueError(
                "'cluster' column is empty or invalid in manual dimensions DataFrame."
            )

        # Filter rows for selected clusters
        filtered_df = man_dim_df[man_dim_df["cluster"].isin(selected_clusters)]

        if filtered_df.empty:
            return {
                "function": "false"
            }  # No rows match, return a JS function that never matches

        # Handle "hybrid" case: dynamically construct conditions for all columns except 'cluster'
        if group_field == "hybrid":
            columns = [col for col in filtered_df.columns if col != "cluster"]
            conditions = []
            for _, row in filtered_df.iterrows():
                condition = " && ".join(
                    [f"params.data.{col} == {repr(row[col])}" for col in columns]
                )
                conditions.append(f"({condition})")
            return {"function": " || ".join(conditions)}

        # Handle specific group_field case: create conditions for the given column
        elif group_field in man_dim_df.columns:
            conditions = [
                f"params.data.{group_field} == {repr(value)}"
                for value in filtered_df[group_field].unique()
            ]
            return {"function": " || ".join(conditions)}

        # Return a default condition if the group_field is not valid
        return {"function": "false"}

    except Exception as e:
        raise type(e)(
            f"Bubbler Error: Failed to get selected manual dimensions: {str(e)}"
        ) from e


def generate_header_with_refresh():
    return """
    <div class="ag-cell-label-container" role="presentation">
        <span ref="eMenu" class="ag-header-icon ag-header-cell-menu-button"></span>
        <span ref="eFilterButton" class="ag-header-icon ag-header-cell-filter-button"></span>
        <div ref="eLabel" class="ag-header-cell-label" role="presentation" style="display: flex; align-items: center;">
            <i 
                class="fa-solid fa-rotate refresh-icon"
                style="font-size: 14px; cursor: pointer; padding: 0 2px; margin-right: 5px;"
                onclick="event.stopPropagation(); dash_clientside.set_props('refresh-button-store', {data: 'refresh'})"
                title="Deselect all rows"
            ></i>
            <span ref="eSortOrder" class="ag-header-icon ag-sort-order ag-hidden"></span>
            <span ref="eSortAsc" class="ag-header-icon ag-sort-ascending-icon ag-hidden"></span>
            <span ref="eSortDesc" class="ag-header-icon ag-sort-descending-icon ag-hidden"></span>
            <span ref="eSortMixed" class="ag-header-icon ag-sort-mixed-icon ag-hidden"></span>
            <span ref="eSortNone" class="ag-header-icon ag-sort-none-icon ag-hidden"></span>   
            <span ref="eText" class="ag-header-cell-text" role="columnheader"></span>       
            <span ref="eFilter" class="ag-header-icon ag-filter-icon"></span>
        </div>
    </div>
    """


def generate_header_template(field, button_icon="up"):
    """
    Get the grouby field from the button on the corresponding column header
    """
    icon_class = "fa-circle-up" if button_icon == "up" else "fa-circle-down"
    click_action = (
        f"dash_clientside.set_props('header-button-store', {{data: '{field}'}})"
        if button_icon == "up"
        else "dash_clientside.set_props('header-button-store', {data: 'back-to-tabular-view'})"
    )

    return f"""
    <div class="ag-cell-label-container" role="presentation" onmouseover="this.querySelector('.custom-group-icon').style.opacity = '1'" onmouseout="this.querySelector('.custom-group-icon').style.opacity = '0'">
        <span ref="eMenu" class="ag-header-icon ag-header-cell-menu-button"></span>
        <span ref="eFilterButton" class="ag-header-icon ag-header-cell-filter-button"></span>
        <div ref="eLabel" class="ag-header-cell-label" role="presentation">
            <span ref="eSortOrder" class="ag-header-icon ag-sort-order ag-hidden"></span>
            <span ref="eSortAsc" class="ag-header-icon ag-sort-ascending-icon ag-hidden"></span>
            <span ref="eSortDesc" class="ag-header-icon ag-sort-descending-icon ag-hidden"></span>
            <span ref="eSortMixed" class="ag-header-icon ag-sort-mixed-icon ag-hidden"></span>
            <span ref="eSortNone" class="ag-header-icon ag-sort-none-icon ag-hidden"></span>   
            <span ref="eText" class="ag-header-cell-text" role="columnheader"></span>       
            <span ref="eFilter" class="ag-header-icon ag-filter-icon"></span>
            <i 
                class="fa-solid {icon_class} custom-group-icon"
                style="font-size: 12px; margin-left: 10px; cursor: pointer; opacity: 0; transition: opacity 0.1s;"
                onclick="event.stopPropagation(); {click_action}"
                data-col-name="{field}"></i>
        </div>
    </div>
    """


def generate_combined_header_template(field, button_icon="up"):
    """
    Generate a header template that includes BOTH refresh and grouping icons.
    This will only be used for the 'cluster' column when it is the first column.
    """
    # Define the grouping icon and action
    icon_class = "fa-circle-up" if button_icon == "up" else "fa-circle-down"
    click_action = (
        "dash_clientside.set_props('header-button-store', {data: 'hybrid'})"
        if button_icon == "up"
        else "dash_clientside.set_props('header-button-store', {data: 'back-to-tabular-view'})"
    )
    refresh_icon = """
    <i class="fa-solid fa-rotate refresh-icon"
       style="font-size: 14px; cursor: pointer; padding: 0 2px; margin-right: 5px;"
       onclick="event.stopPropagation(); dash_clientside.set_props('refresh-button-store', {data: 'refresh'})"
       title="Deselect all rows">
    </i>
    """

    group_icon = f"""
    <i class="fa-solid {icon_class} custom-group-icon"
       style="font-size: 12px; margin-left: 10px; cursor: pointer; opacity: 0; transition: opacity 0.1s;"
       onclick="event.stopPropagation(); {click_action}"
       data-col-name="{field}">
    </i>
    """

    return f"""
    <div class="ag-cell-label-container" role="presentation" 
         onmouseover="this.querySelector('.custom-group-icon').style.opacity = '1'" 
         onmouseout="this.querySelector('.custom-group-icon').style.opacity = '0'">
        <span ref="eMenu" class="ag-header-icon ag-header-cell-menu-button"></span>
        <span ref="eFilterButton" class="ag-header-icon ag-header-cell-filter-button"></span>
        <div ref="eLabel" class="ag-header-cell-label" role="presentation" 
             style="display: flex; align-items: center;">
            {refresh_icon}  <!-- Always include the refresh icon -->
            <span ref="eSortOrder" class="ag-header-icon ag-sort-order ag-hidden"></span>
            <span ref="eSortAsc" class="ag-header-icon ag-sort-ascending-icon ag-hidden"></span>
            <span ref="eSortDesc" class="ag-header-icon ag-sort-descending-icon ag-hidden"></span>
            <span ref="eSortMixed" class="ag-header-icon ag-sort-mixed-icon ag-hidden"></span>
            <span ref="eSortNone" class="ag-header-icon ag-sort-none-icon ag-hidden"></span>   
            <span ref="eText" class="ag-header-cell-text" role="columnheader"></span>       
            <span ref="eFilter" class="ag-header-icon ag-filter-icon"></span>
            {group_icon}  <!-- Always include the grouping icon -->
        </div>
    </div>
    """
