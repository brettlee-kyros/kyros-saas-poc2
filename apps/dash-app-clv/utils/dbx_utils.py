import pandas as pd
from kyros_plotly_common.core.cache import cache
from kyros_plotly_common.core.dbx_client import run_query
from kyros_plotly_common.logger.dash_logger import dash_logger

from kyros_plotly_common.core.redis_client import get_from_redis
from kyros_plotly_common.utils.schema import parse_schema_properties

from utils.dbx_queries import (
    construct_mandim_query,
    construct_all_exposures_query,
    construct_current_exp_query,
    construct_r2_query,
    construct_pval_financial_impact_query,
    construct_triangle_data_query,
    construct_reweighted_triangle_data_query,
    construct_fimpact_query
)

from utils.dbx_helper_utils import (
    check_target_consistency,
    build_mandim_select_clause,
    is_variance_statistic,
    extract_common_denominator,
)


@cache.memoize(timeout=7200)
def get_manual_dimensions(consolidated_name):
    """Fetches manual dimensions for each schema/client, and caches them into Redis."""
    try:
        # Validate and fetch schema
        report_type = "performance1"
        properties, full_path = parse_schema_properties(consolidated_name, report_type)

        # construct the query
        select_clause = build_mandim_select_clause(properties, consolidated_name)

        man_dim_query = construct_mandim_query(select_clause, full_path)
        man_dim_arrow_table = run_query(man_dim_query, result_type="arrow")

        if not man_dim_arrow_table or man_dim_arrow_table.num_rows == 0:  # type: ignore
            dash_logger.info("Manual dimensions query returned empty table.")

        try:
            return man_dim_arrow_table.to_pylist()  # type: ignore
        except:
            return []

    except Exception as e:
        raise type(e)(f"Failed to fetch manual dimensions: {str(e)}") from e


@cache.memoize(timeout=7200)
def get_exposures_data(consolidated_name, cluster_list):
    """Fetches exposures for all available snapshotDates for the selected list of cluster(s) or ALL clusters([]).

    Args:
        consolidated_name: Name of the consolidated schema.
        cluster_list: List of cluster IDs or empty list ([]) which means ALL.

    Returns:
        DataFrame: pandas DataFrame.

    Raises:
        KeyError: If required keys are missing in schema.
        ValueError: If input validation fails.
    """
    try:
        # Validate and parse schema
        report_type = "performance1"
        properties, full_path = parse_schema_properties(consolidated_name, report_type)

        if cluster_list:
            cluster_list = [cluster for cluster in cluster_list]
            if len(cluster_list) == 1: # mimic tuple
                if isinstance(cluster_list[0], str):
                    selected_clusters = f"('{cluster_list[0]}')"  # wrap with ' ' if string
                else:
                    selected_clusters = f"({cluster_list[0]})"  
            else:
                selected_clusters = tuple(cluster_list)
            where_clause = f"WHERE {properties['cluster']} IN {selected_clusters}"
        else:
            where_clause = ""

        all_exposures_query = construct_all_exposures_query(
            properties, full_path, where_clause
        )

        all_exposures_df = run_query(
            all_exposures_query, result_type="pandas"
        )
        if isinstance(all_exposures_df, pd.DataFrame) and all_exposures_df.shape[0] > 0:
            return all_exposures_df
        else:
            dash_logger.warning("Exposures query returned empty table for the selected clusters.")
            return []

    except Exception as e:
        raise type(e)(f"Failed to fetch exposures: {str(e)}") from e


@cache.memoize(timeout=7200)
def get_total_current_exposure(consolidated_name, current_snapshot_date):
    try:
        # Validate and fetch schema
        report_type = "performance1"
        properties, full_path = parse_schema_properties(consolidated_name, report_type)

        if "snapshotDate" not in properties:
            raise KeyError("'snapshotDate' child-key is missing in the lookup schema.")

        if not properties["snapshotDate"]:
            raise ValueError(
                "'snapshotDate' child-key is empty or invalid in the lookup schema."
            )

        if "obsAge" not in properties:
            raise KeyError("'obsAge' child-key is missing in the lookup schema.")

        if not properties["obsAge"]:
            raise ValueError(
                "'obsAge' child-key is empty or invalid in the lookup schema."
            )
            
        where_clause = (
            f"WHERE {properties['snapshotDate']} = '{current_snapshot_date}' "
            f"AND {properties['obsAge']} = 0"
        )
            
        total_curren_exp_query = f"""
            -- total current date exposures           
            SELECT 
                SUM({properties['exposure']}) as total_score
            FROM {full_path}
            {where_clause} 
            """
            
        # run query
        current_exp_arrow_table = run_query(
            total_curren_exp_query, result_type= "arrow"
        )
        if not current_exp_arrow_table or current_exp_arrow_table.num_rows == 0:
            dash_logger.info("Total recent exposures query returned empty table.")

        try:
            return current_exp_arrow_table.to_pylist()  # convert to dict
        except:
            return []

    except Exception as e:
        raise type(e)(f"Failed to fetch total current exposures: {str(e)}") from e

    
@cache.memoize(timeout=7200)
def get_current_exposures_data(
    consolidated_name, current_snapshot_date, cluster_list, groupby_dimension
):
    """
    Args:
        consolidated_name: Name of the consolidated schema.
        current_snapshot_date:  The most recent snapshotDate str(Date).
        cluster_list: List of cluster IDs or empty list ([]) which means ALL.
        groupby_dimension: Dimension to group by: either "cluster", "hybrid" or selected mandim colname.

    Returns:
        list: List of Rows containing current exposures.

    Raises:
        KeyError: If required keys are missing in schema.
        ValueError: If input validation fails.
    """

    try:
        # Validate and fetch schema
        report_type = "performance1"
        properties, full_path = parse_schema_properties(consolidated_name, report_type)

        if "snapshotDate" not in properties:
            raise KeyError("'snapshotDate' child-key is missing in the lookup schema.")

        if not properties["snapshotDate"]:
            raise ValueError(
                "'snapshotDate' child-key is empty or invalid in the lookup schema."
            )

        if "obsAge" not in properties:
            raise KeyError("'obsAge' child-key is missing in the lookup schema.")

        if not properties["obsAge"]:
            raise ValueError(
                "'obsAge' child-key is empty or invalid in the lookup schema."
            )

        # Construct the query variables
        is_cluster = groupby_dimension == "cluster"
        where_clause = (
            f"WHERE {properties['snapshotDate']} = '{current_snapshot_date}' "
            f"AND {properties['obsAge']} = 0"
        )

        if is_cluster and cluster_list:
            manual_dimensions = []
            cluster_list = [cluster for cluster in cluster_list]

            if len(cluster_list) == 1:  # mimic tuple
                if isinstance(cluster_list[0], str):
                    selected_clusters = f"('{cluster_list[0]}')"  # wrap with ' ' if string
                else:
                    selected_clusters = f"({cluster_list[0]})"  
            else:
                selected_clusters = tuple(cluster_list)
            where_clause += f" AND {properties['cluster']} IN {selected_clusters}"

        else:
            manual_dimensions = properties["manual_dimensions"]

        current_exp_query = construct_current_exp_query(
            properties, where_clause, full_path, manual_dimensions, is_cluster
        )

        # run query
        current_exp_arrow_table = run_query(
            current_exp_query, result_type="arrow"
        )
        if not current_exp_arrow_table or current_exp_arrow_table.num_rows == 0:
            dash_logger.warning("Recent exposures query returned empty table.")

        try:
            return current_exp_arrow_table.to_pylist()  # convert to dict
        except:
            return []

    except Exception as e:
        raise type(e)(f"Failed to fetch current exposures: {str(e)}") from e


@cache.memoize(timeout=7200)
def get_r2_dev(consolidated_name, target_list, cluster_list, groupby_dimension):
    """
    Calculate R2 metrics for given targets.

    Args:
        consolidated_name: Name of the consolidated schema
        target_value: Target(s) to analyze (list)
        cluster_list: List of cluster IDs or empty list ([]) which means ALL
        groupby_dimension: Dimension to group by

    Returns:
        list: List of dictionaries containing R2 calculations.

    Raises:
        KeyError: If required keys are missing in schema
        ValueError: If input validation fails
    """
    try:
        # Parse and validate schema
        report_type = "performance1"
        properties, full_path = parse_schema_properties(consolidated_name, report_type)

        if "targets" not in properties:
            raise KeyError("'targets' child-key is missing in the lookup schema.")

        if not properties["targets"]:
            raise ValueError(
                "'targets' child-key is empty or invalid in the lookup schema."
            )

        # check pre-requisites
        ## check whether selected target shares common denom before aggregating them.
        common_denominator = extract_common_denominator(
            properties["targets"], target_list
        )
        ## check_target_consistency
        check_target_consistency(properties, target_list)

        # Initialize query components
        is_cluster = groupby_dimension == "cluster"
        actuals, expected, denominator_mask = [], [], []

        # Process each target
        for target in target_list:
            target_schema = properties["targets"][target]
            mask_str = str(target_schema["mask"])

            if is_cluster: # filter clusters
                actuals.append(f"({target_schema['actual']} * {mask_str})")
                expected.append(f"({target_schema['expected']} * {mask_str})")
            else:
                denominator_mask.append(f"({mask_str} = 1)") # Always use masking
                actuals.append(
                    f"({target_schema['actual']} * {target_schema['numerator_weight']} * {mask_str})"
                )
                expected.append(
                    f"({target_schema['expected']} * {target_schema['numerator_weight']} * {mask_str})"
                )

        # Process cluster information
        if cluster_list:
            manual_dimensions = []
            cluster_list = [cluster for cluster in cluster_list]
            if len(cluster_list) == 1: # mimic tuple
                if isinstance(cluster_list[0], str):
                    selected_clusters = f"('{cluster_list[0]}')"  # wrap with ' ' if string
                else:
                    selected_clusters = f"({cluster_list[0]})"  
            else:
                selected_clusters = tuple(cluster_list)

            where_clause = f"WHERE {properties['cluster']} IN {selected_clusters}"
        else:
            manual_dimensions = properties["manual_dimensions"]
            where_clause = ""

        # Construct and execute query
        r2_query = construct_r2_query(
            properties,
            actuals,
            expected,
            denominator_mask,
            where_clause,
            full_path,
            manual_dimensions,
            is_cluster,
            common_denominator,
        )

        # run query
        r2_arrow_table = run_query(r2_query, result_type="arrow")

        if not r2_arrow_table or r2_arrow_table.num_rows == 0:
            dash_logger.info("R2 dev metrics query returned empty table.")
        try:
            return r2_arrow_table.to_pylist()  # to dict
        except:
            return []

    except Exception as e:
        raise type(e)(f"Failed to fetch R2_dev metrics: {str(e)}") from e
    
@cache.memoize(timeout=7200)
def get_total_financial_impact(consolidated_name, target_list, monitoring_date):
    try:
        report_type = "performance2"
        properties, full_path = parse_schema_properties(consolidated_name, report_type) 
        # exist early
        if monitoring_date not in properties['monitoring_snapshotDate']['values']:
            return []
        
        ## check_target_consistency
        check_target_consistency(properties, target_list)
        
        # Initialize query components
        restated = []
        baseline = []
        for target in target_list:
            target_schema = properties["targets"][target] # get to the
            
            restated.append(
                f"( {target_schema['restated']} * perf2.{target_schema['numerator_weight']} * {target_schema['cpp']} )"
            )
            baseline.append(
                f"( {target_schema['baseline']} * perf2.{target_schema['numerator_weight']} * {target_schema['cpp']} )"
            )
            
        # Join columns for aggregations
        restated_row_sum = "+".join(restated)
        baseline_row_sum = "+".join(baseline)
    

        where_clause = f"WHERE perf2.{properties['monitoring_snapshotDate']['name']} == '{monitoring_date}'"
        groupby_clause = f"GROUP BY perf2.{properties['monitoring_snapshotDate']['name']}"
        
        
        # only for this metric get report1 for mandims
        report_type = "performance1"
        _, full_path1 = parse_schema_properties(consolidated_name, report_type) 
        
        fimpact_query = f"""
        WITH unique_dims AS (
            SELECT DISTINCT
                {properties['cluster']}
            FROM {full_path1}
        )
        SELECT
            SUM({restated_row_sum})  -  SUM({baseline_row_sum})  AS financial_impact
            FROM  {full_path} AS perf2
            JOIN unique_dims dims
                ON perf2.{properties['cluster']} = dims.{properties['cluster']}
                {where_clause}
            {groupby_clause}
        """

        fimpact_arrow_table = run_query(
            fimpact_query, result_type="arrow"
        )
        if (
            not fimpact_arrow_table
            or fimpact_arrow_table.num_rows == 0
        ):
            dash_logger.info(
                "Financial impact metrics query returned empty table."
            )

        try:
            return (
                fimpact_arrow_table.to_pylist()
            )  # convert to dict for easier chaching
        except:
            return []

    except Exception as e:
        raise type(e)(
            f"Failed to fetch financial impact metric: {str(e)}"
        ) from e
            
    
@cache.memoize(timeout=7200)
def get_all_financial_impact(consolidated_name, target_list, monitoring_date, groupby_dimension):
    try:
        # get properties child-key from the lookup table
        # Validate and parse schema
        report_type = "performance2"
        properties, full_path = parse_schema_properties(consolidated_name, report_type) 
        
        # exist early
        if monitoring_date not in properties['monitoring_snapshotDate']['values']:
            return []
            
        ## check_target_consistency
        check_target_consistency(properties, target_list)
        
        # Initialize query components
        is_cluster = groupby_dimension == "cluster"
        restated = []
        baseline = []
        for target in target_list:
            target_schema = properties["targets"][target] # get to the
            
            restated.append(
                f"( {target_schema['restated']} * perf2.{target_schema['numerator_weight']} * {target_schema['cpp']} )"
            )
            baseline.append(
                f"( {target_schema['baseline']} * perf2.{target_schema['numerator_weight']} * {target_schema['cpp']} )"
            )
            
        
        report_type2 = "performance1"
        properties2, full_path2 = parse_schema_properties(consolidated_name, report_type2)
        
        # Construct the cluster where clause
        if is_cluster:
            bubblers_dimensions = []
            manual_dimensions = [] 
        else:
            bubblers_dimensions = properties2["bubblers"]["dimensions"]
            manual_dimensions = properties2["manual_dimensions"]
            
        where_clause = f"WHERE perf2.{properties['monitoring_snapshotDate']['name']} == '{monitoring_date}'"
                
        all_fimapct_query = construct_fimpact_query(       
            properties,
            restated,
            baseline,
            where_clause,
            full_path,
            full_path2,
            manual_dimensions,
            bubblers_dimensions,
            is_cluster
        )
        
        # run query
        fimpact_arrow_table = run_query(
            all_fimapct_query, result_type="arrow"
        )
        if (
            not fimpact_arrow_table
            or fimpact_arrow_table.num_rows == 0
        ):
            dash_logger.info(
                "All financial impact metrics query returned empty table."
            )

        try:
            return (
                fimpact_arrow_table.to_pylist()
            )  # convert to dict for easier chaching
        except:
            return []

    except Exception as e:
        raise type(e)(
            f"Failed to fetch all financial impact metric: {str(e)}"
        ) from e

@cache.memoize(timeout=7200)
def get_agg_pval(
    consolidated_name,
    target_list,
    monitoring_snapshot_date,
    current_snapshot_date,
    cluster_list
):
    try:
        # Validate and parse schema
        report_type = "performance1"
        properties, full_path = parse_schema_properties(consolidated_name, report_type)

        if "targets" not in properties:
            raise KeyError("'targets' child-key is missing in the lookup schema.")

        if not properties["targets"]:
            raise ValueError(
                "'targets' child-key is empty or invalid in the lookup schema."
            )

        # check pre-requisites
        ## check whether selected target shares common denom before aggregating them.
        common_denominator = extract_common_denominator(
            properties["targets"], target_list
        )
        ## check_target_consistency
        check_target_consistency(properties, target_list)
        
        actuals, expected, denominator_mask, variance_expected = [], [], [], []
        for target in target_list:
            target_schema = properties["targets"][target]
            variance_target = f"{target}__total_variance"

            # check for variance_target keys
            if variance_target not in properties["targets"]:
                dash_logger.info(
                    f"'{variance_target}' child-key is missing in the lookup schema: {consolidated_name}."
                )
                return []

            variance_target_schema = properties["targets"][variance_target]
            if not variance_target_schema:
                dash_logger.info(
                    f"'{variance_target_schema}' value is invalid or empty in the lookup schema: {consolidated_name}."
                )
                return []

            mask_str = str(target_schema["mask"])  # ALWAYS USE MASKING
            denominator_mask.append(f"({mask_str} = 1)")
            actuals.append(
                f"({target_schema['actual']} * {target_schema['numerator_weight']} * {mask_str})"
            )
            expected.append(
                f"({target_schema['expected']} * {target_schema['numerator_weight']} * {mask_str})"
            )
            variance_expected.append(
                f"({variance_target_schema['expected']} * {variance_target_schema['numerator_weight']} * {mask_str})"
            )
            
            if cluster_list: # If not all clusters
                cluster_list = [cluster for cluster in cluster_list]
                if len(cluster_list) == 1: # mimic tuple
                    if isinstance(cluster_list[0], str):
                        selected_clusters = f"('{cluster_list[0]}')"  # wrap with ' ' if string
                    else:
                        selected_clusters = f"({cluster_list[0]})"  
                else:
                    selected_clusters = tuple(cluster_list)


                where_clause = f"WHERE {properties['cluster']} IN {selected_clusters} AND {properties['snapshotDate']} = '{monitoring_snapshot_date}'"
            else: # all []
                where_clause = (
                    f"WHERE {properties['snapshotDate']} = '{monitoring_snapshot_date}'"
                )
            
            # Join columns for aggregations
            actual_select = " + ".join(actuals)
            expected_select = " + ".join(expected)
            variance_select = " + ".join(variance_expected)
            denominator_mask_select = " OR ".join(denominator_mask)
            
            agg_p_val_query = f"""
            -- Aggregated Z-score
            WITH aggregated_data AS (
                SELECT
                    {properties['snapshotDate']} AS snapshotDate, 
                    {properties['obsAge']} AS obsAge,
                    SUM(CASE WHEN {denominator_mask_select} THEN {common_denominator} ELSE 0 END) AS common_denominator,
                    SUM({variance_select}) AS variance_numerator,
                    SUM({actual_select}) AS actual_numerator,
                    SUM({expected_select}) AS expected_numerator
                FROM
                    {full_path}
                {where_clause}
                GROUP BY
                    {properties['snapshotDate']},
                    {properties['obsAge']}
            ),
            computed_metrics AS (
                SELECT
                    common_denominator,
                    snapshotDate,
                    obsAge,
                    common_denominator,
                    SQRT(variance_numerator / NULLIF(POWER(common_denominator, 2), 0)) AS std,
                    SUM(actual_numerator) OVER (
                        PARTITION BY snapshotDate
                        ORDER BY obsAge ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ) / NULLIF(common_denominator, 0) AS cum_actual,
                    SUM(expected_numerator) OVER (
                        PARTITION BY snapshotDate
                        ORDER BY obsAge ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ) / NULLIF(common_denominator, 0) AS cum_expected
                FROM
                    aggregated_data
            )
            SELECT
                cum_actual,
                cum_expected,
                cum_actual - cum_expected as cum_residual,
                (cum_actual - cum_expected) / NULLIF(std, 0) AS z_score
            FROM 
                computed_metrics
            WHERE 
                obsAge = months_between('{current_snapshot_date}', snapshotDate) -- Current Date
        """
        
        # run query
        pval_pandas_table = run_query(
            agg_p_val_query, result_type="pandas"
        )
        
        if isinstance(pval_pandas_table, pd.DataFrame) and pval_pandas_table.shape[0] > 0:
            return pval_pandas_table
        else:
            dash_logger.info(
                "Aggregated Z-score query returned empty table."
            )
            return []
        
    except Exception as e:
        raise type(e)(
            f"Failed to fetch aggregated Z-score metric: {str(e)}"
        ) from e


@cache.memoize(timeout=7200)
def get_pval_and_fin_impact(
    consolidated_name,
    target_list,
    monitoring_snapshot_date,
    current_snapshot_date,
    cluster_list,
    z_score,
    groupby_dimension,
):
    """
    Args:
        consolidated_name: Name of the consolidated schema.
        target_list: Selected Target(s) (list).
        monitoring_snapshot_date: str(Date).
        current_snapshot_date:  The most recent snapshotDate str(Date).
        cluster_list: List of cluster IDs or empty list ([]) which means ALL.
        z_score: Z-score (float).
        groupby_dimension: Dimension to group by: either "cluster", "hybrid" or selected mandim colname.

    Returns:
        list: List of Rows containing R2 calculations.

    Raises:
        KeyError: If required keys are missing in schema.
        ValueError: If input validation fails.
    """
    try:
        # Validate and parse schema
        report_type = "performance1"
        properties, full_path = parse_schema_properties(consolidated_name, report_type)

        if "targets" not in properties:
            raise KeyError("'targets' child-key is missing in the lookup schema.")

        if not properties["targets"]:
            raise ValueError(
                "'targets' child-key is empty or invalid in the lookup schema."
            )

        # check pre-requisites
        ## check whether selected target shares common denom before aggregating them.
        common_denominator = extract_common_denominator(
            properties["targets"], target_list
        )
        ## check_target_consistency
        check_target_consistency(properties, target_list)

        # Construct the query variables
        is_cluster = groupby_dimension == "cluster"
        if is_cluster:  # cluster level
            manual_dimensions = []
        else:
            manual_dimensions = properties["manual_dimensions"]

        actuals, expected, denominator_mask, variance_expected = [], [], [], []
        for target in target_list:
            target_schema = properties["targets"][target]
            variance_target = f"{target}__total_variance"

            # check for variance_target keys
            if variance_target not in properties["targets"]:
                dash_logger.info(
                    f"'{variance_target}' child-key is missing in the lookup schema: {consolidated_name}."
                )
                return []

            variance_target_schema = properties["targets"][variance_target]
            if not variance_target_schema:
                dash_logger.info(
                    f"'{variance_target_schema}' value is invalid or empty in the lookup schema: {consolidated_name}."
                )
                return []

            # masking
            actual_mask_case = (
                    f"CASE WHEN {target_schema['mask']} = 1 "
                    f"THEN {target_schema['actual']} "
                    f"ELSE {target_schema['expected']} END"
                )

            actuals.append(
                f"({actual_mask_case} * {target_schema['numerator_weight']})"
            )
            expected.append(
                f"({target_schema['expected']} * {target_schema['numerator_weight']})"
            )
            variance_expected.append(
                f"({variance_target_schema['expected']} * {variance_target_schema['numerator_weight']})"
            )

        if cluster_list:
            cluster_list = [cluster for cluster in cluster_list]
            if len(cluster_list) == 1: # mimic tuple
                if isinstance(cluster_list[0], str):
                    selected_clusters = f"('{cluster_list[0]}')"  # wrap with ' ' if string
                else:
                    selected_clusters = f"({cluster_list[0]})"  
            else:
                selected_clusters = tuple(cluster_list)

            where_clause = f"WHERE {properties['cluster']} IN {selected_clusters} AND {properties['snapshotDate']} = '{monitoring_snapshot_date}'"
        else:
            where_clause = (
                f"WHERE {properties['snapshotDate']} = '{monitoring_snapshot_date}'"
            )

        pval_financial_impact_query = construct_pval_financial_impact_query(
            properties,
            actuals,
            expected,
            variance_expected,
            where_clause,
            full_path,
            manual_dimensions,
            is_cluster,
            common_denominator,
            current_snapshot_date,
            z_score,
        )

        # run query
        pval_financial_impact_arrow_table = run_query(
            pval_financial_impact_query, result_type="arrow"
        )
        if (
            not pval_financial_impact_arrow_table
            or pval_financial_impact_arrow_table.num_rows == 0
        ):
            dash_logger.info(
                "Z-scores and financial impact metrics query returned empty table."
            )

        try:
            return (
                pval_financial_impact_arrow_table.to_pylist()
            )  # convert to dict for easier chaching
        except:
            return []

    except Exception as e:
        raise type(e)(
            f"Failed to fetch Z-scores and financial impact metrics: {str(e)}"
        ) from e


@cache.memoize(timeout=7200)
def get_triangle_format_data(
    consolidated_name, dev_value, cluster_list, target_list, mask
):
    """
    Fetch Dev or Dev Since (cumulative) trianglular format data given list of cluster(s) or for ALL clusters ([]) for the selected target(s).
    -   Masking on actual values is applied in such a way that the masked actual values are replaced with their expected counterparts,
        while the expected values remain unaffected.

    Args:
        consolidated_name: Name of the consolidated schema.
        dev_value: Dev Since (cumulative) or Dev
        cluster_list: List of cluster IDs or empty list ([]) which means ALL clusters.
        target_list: Selected Target(s).
        mask (str): Masked or Unmasked.

    Returns:
        DataFrame: Either Cumulative (Dev Since) or (Dev) Pandas DataFrame containing triangle data.
    """
    try:
        # Validate and parse schema
        report_type = "performance1"
        properties, full_path = parse_schema_properties(consolidated_name, report_type)

        if "targets" not in properties:
            raise KeyError("'targets' child-key is missing in the lookup schema.")

        if not properties["targets"]:
            raise ValueError(
                "'targets' child-key is empty or invalid in the lookup schema."
            )

        # Check pre-requisites
        ## check whether selected target shares common denom before aggregating them.
        common_denominator = extract_common_denominator(
            properties["targets"], target_list
        )
        ## check_target_consistency
        check_target_consistency(properties, target_list)

        # check whether variance type targets are given
        is_variance = is_variance_statistic(properties, target_list, consolidated_name)

        # Construct the where clause
        if cluster_list:
            cluster_list = [cluster for cluster in cluster_list]
            if len(cluster_list) == 1: # mimic tuple
                if isinstance(cluster_list[0], str):
                    selected_clusters = f"('{cluster_list[0]}')"  # wrap with ' ' if string
                else:
                    selected_clusters = f"({cluster_list[0]})"  
            else:
                selected_clusters = tuple(cluster_list)

            where_cluster_clause = (
                f"WHERE {properties['cluster']} IN {selected_clusters}"
            )
        else:  # if empty [] which means ALL clusters
            where_cluster_clause = ""

        actuals = []
        expected = []
        denominator_mask = []
        for target in target_list:
            target_schema = properties["targets"][target]
            
            if mask == "Masked":
                mask_str = str(target_schema["mask"])
                denominator_mask.append("(" + mask_str + "= 1" + ")")  # 1=1 => TRUE ; 0=1 => FALSE

            else:
                mask_str = "1"
                denominator_mask.append("(1=1)")  # Random always TRUE statement

            # aggregate variables
            denominator_mask_select = "OR".join(denominator_mask)
            actuals.append(
                f"({target_schema['actual']} * {target_schema['numerator_weight']}* {mask_str})"
            )
            expected.append(
                f"({target_schema['expected']} * {target_schema['numerator_weight']}* {mask_str})"
            )


        triangle_data_query = construct_triangle_data_query(
            properties,
            actuals,
            expected,
            where_cluster_clause,
            dev_value,
            is_variance,
            full_path,
            denominator_mask_select,
            common_denominator,
        )

        triangle_df = run_query(
            triangle_data_query, result_type="pandas"
        )
        if isinstance(triangle_df, pd.DataFrame) and triangle_df.shape[0] > 0:
            return triangle_df
        else:
            raise ValueError("'triangle data' query returned empty table.")

    except Exception as e:
        raise type(e)(f"Failed to fetch triangle data: {str(e)}") from e


@cache.memoize(timeout=7200)
def get_reweighted_triangle_format_data(
    consolidated_name, cluster_list, target_list, monitoring_date, mask
):
    """
    Fetch Reweighted Dev Since (cumulative) trianglular format data given list of cluster(s) or for ALL clusters ([]) for the selected target(s).
    -   Masking on actual values is applied in such a way that the masked actual values are replaced with their expected counterparts,
        while the expected values remain unaffected.

    Args:
        consolidated_name: Name of the consolidated schema.
        dev_value: Dev Since (cumulative) or Dev
        cluster_list: List of cluster IDs or empty list ([]) which means ALL clusters.
        target_list: Selected Target(s).
        mask (str): Masked or Unmasked.

    Returns:
        DataFrame: Reweighted Cumulative (Dev Since) Pandas DataFrame containing triangle data.
    """
    try:
        # Validate and parse schema
        report_type = "performance1"
        properties, full_path = parse_schema_properties(consolidated_name, report_type)

        # check pre-requisites
        ## check whether selected target shares common denom before aggregating them.
        common_denominator = extract_common_denominator(
            properties["targets"], target_list
        )
        ## check_target_consistency
        check_target_consistency(properties, target_list)

        # is variance stat?
        is_variance = is_variance_statistic(properties, target_list, consolidated_name)

        actuals = []
        expected = []

        if cluster_list:
            cluster_list = [cluster for cluster in cluster_list]
            if len(cluster_list) == 1: # mimic tuple
                if isinstance(cluster_list[0], str):
                    selected_clusters = f"('{cluster_list[0]}')"  # wrap with ' ' if string
                else:
                    selected_clusters = f"({cluster_list[0]})"  
            else:
                selected_clusters = tuple(cluster_list)

            where_clause1 = f"WHERE {properties['cluster']} IN {selected_clusters} AND {properties['snapshotDate']} = '{monitoring_date}'"
            where_clause2 = f"WHERE b.{properties['cluster']} IN {selected_clusters}"
        else:
            where_clause1 = f"WHERE {properties['snapshotDate']} = '{monitoring_date}'"
            where_clause2 = ""

        for target in target_list:
            target_schema = properties["targets"][target]

            if mask == "Masked":
                actual_mask_case = (
                    f"CASE WHEN {target_schema['mask']} = 1 "
                    f"THEN {target_schema['actual']} "
                    f"ELSE {target_schema['expected']} END"
                )

            else:
                actual_mask_case = target_schema["actual"]

            actuals.append(f"({actual_mask_case} * w.numerator_reweight)")
            expected.append(f"({target_schema['expected']} * w.numerator_reweight)")

        reweighted_triangledata_query = construct_reweighted_triangle_data_query(
            properties,
            actuals,
            expected,
            common_denominator,
            is_variance,
            where_clause1,
            where_clause2,
            full_path,
        )

        reweighted_triangledata_df = run_query(
            reweighted_triangledata_query, result_type="pandas"
        )
        if (
            isinstance(reweighted_triangledata_df, pd.DataFrame)
            and reweighted_triangledata_df.shape[0] > 0
        ):
            return reweighted_triangledata_df
        else:
            raise ValueError("Reweighted 'triangle data' query returned empty table")

    except Exception as e:
        raise type(e)(f"Failed to fetch reweighted triangle data: {str(e)}") from e


@cache.memoize(timeout=7200)
def get_agg_stds(consolidated_name, cluster_list, target_list, monitoring_date, mask):
    """
    This function constructs and executes a SQL query to calculate the standard deviation of values
    for the specified monitoring date with the given schema, cluster list, target list.

    Args:
        consolidated_name: Name of the consolidated schema.
        cluster_list: List of cluster IDs or empty list ([]) which means ALL.
        target_list: Selected Target(s) (list).
        monitoring_snapshot_date: str(Date).

    Returns:
        DataFrame: Pandas DataFrame containing standard deviations.

    Raises:
        KeyError: If required keys are missing in schema.
        ValueError: If input validation fails.
    """
    try:
        # Validate and parse schema
        report_type = "performance1"
        properties, full_path = parse_schema_properties(consolidated_name, report_type)

        if "targets" not in properties:
            raise KeyError("'targets' child-key is missing in the lookup schema.")

        if not properties["targets"]:
            raise ValueError(
                "'targets' child-key is empty or invalid in the lookup schema."
            )
            
        # check pre-requisites
        ## check whether selected target shares common denom before aggregating their variances.
        common_denominator = extract_common_denominator(
            properties["targets"], target_list
        )
        
        ## check_target_consistency
        check_target_consistency(properties, target_list)

        # get total_variance of the targets.
        variance_suffix = "__total_variance"
        variance_targets = [f"{target}{variance_suffix}" for target in target_list]

        # check for exit early
        for variance_target in variance_targets:
            if variance_target not in properties["targets"]:
                return pd.DataFrame(columns=["snapshotDate", "obsAge", "std"]) # empty df with predefined columns

        # constructu query variables
        expected = []
        denominator_mask = []

        if cluster_list:
            cluster_list = [cluster for cluster in cluster_list]
            if len(cluster_list) == 1: # mimic tuple
                if isinstance(cluster_list[0], str):
                    selected_clusters = f"('{cluster_list[0]}')"  # wrap with ' ' if string
                else:
                    selected_clusters = f"({cluster_list[0]})"  
            else:
                selected_clusters = tuple(cluster_list)

            where_clause1 = f"WHERE {properties['cluster']} IN {selected_clusters} AND {properties['snapshotDate']} = '{monitoring_date}'"
            where_clause2 = f"WHERE base.{properties['cluster']} IN {selected_clusters} AND base.{properties['snapshotDate']} = '{monitoring_date}'"

        else: # select all []
            where_clause1 = f"WHERE {properties['snapshotDate']} = '{monitoring_date}'"
            where_clause2 = f"WHERE base.{properties['snapshotDate']} = '{monitoring_date}'"
        

        for target in variance_targets:
            target_schema = properties["targets"][target]
            
            if mask == "Masked":
                mask_str = str(target_schema["mask"])
                denominator_mask.append("(" + mask_str + "= 1" + ")")  # 1=1 => TRUE ; 0=1 => FALSE

            else:
                mask_str = "1"
                denominator_mask.append("(1=1)")  # Random always TRUE statement

            expected.append(
                "("
                + target_schema["expected"]
                + " * "
                + target_schema['numerator_weight']
                + " * "
                + mask_str
                + ")"
            )

            expected_select = "+".join(expected)
            denominator_mask_select = "OR".join(denominator_mask)

            std_query = f"""
            --  Agg standard deviations
            WITH std_weights_query AS(
                SELECT 
                    {common_denominator} as denominator,  
                    {properties['snapshotDate']} AS snapshotDate, 
                    {properties['cluster']} AS cluster
                FROM {full_path}
                {where_clause1}
                GROUP BY 
                    {properties['snapshotDate']}, 
                    {properties['cluster']},
                    {common_denominator}
                HAVING {common_denominator} IS NOT NULL
            ),
            base_query AS(
            SELECT 
                base.{properties['snapshotDate']} AS snapshotDate, 
                {properties['obsAge']} AS obsAge,
                SUM(CASE WHEN {denominator_mask_select} THEN w.denominator ELSE 0 END) AS full_denominator, -- a+b not a^2 +b^2
                SUM({expected_select}) as expected_numerator -- a^2 + b^2
            FROM {full_path} base
            JOIN std_weights_query w ON base.{properties['cluster']} = w.cluster  
            {where_clause2}
            GROUP BY 
                base.{properties['snapshotDate']}, 
                {properties['obsAge']}
            )
            SELECT 
                snapshotDate,
                obsAge,
                SQRT(expected_numerator / NULLIF(POWER(full_denominator, 2), 0)) AS std
            FROM base_query
            ORDER BY snapshotDate, obsAge
            """

            std_df = run_query(std_query, result_type="pandas")
            if isinstance(std_df, pd.DataFrame) and std_df.shape[0] > 0:
                return std_df
            else:
                return pd.DataFrame(columns=["snapshotDate", "obsAge", "std"])

    except Exception as e:
        raise type(e)(f"Failed to fetch standard deviations: {str(e)}") from e
    
    
    
@cache.memoize(timeout=7200)
def get_agg_stds_with_covariance(
    consolidated_name,
    cluster_list,
    target_list,
    monitoring_date,
    mask,
    target_correlation=0.25,
    cluster_correlation=0.25,
):
    """
    Calculate standard deviations accounting for separate covariance between targets and clusters.

    Args:
        consolidated_name: Name of the consolidated schema.
        cluster_list: List of cluster IDs or empty list ([]) which means ALL.
        target_list: Selected Target(s) (list).
        monitoring_date: str(Date) for monitoring.
        mask: Whether to apply masking ("Masked" or "Unmasked").
        target_correlation: Correlation value between targets (default: 0.25).
        cluster_correlation: Correlation value between clusters (default: 0.25).

    Returns:
        DataFrame: Pandas DataFrame containing standard deviations with covariance adjustments.
    """
    try:
        # Validate and parse schema
        report_type = "performance1"
        properties, full_path = parse_schema_properties(consolidated_name, report_type)

        if "targets" not in properties:
            raise KeyError("'targets' child-key is missing in the lookup schema.")
        if not properties["targets"]:
            raise ValueError(
                "'targets' child-key is empty or invalid in the lookup schema."
            )

        # Target consistency check
        common_denominator = extract_common_denominator(
            properties["targets"], target_list
        )
        are_targets_consistent = check_target_consistency(properties, target_list)

        if not are_targets_consistent:
            dash_logger.warning(
                "Selected targets do not share the same development_metric, category and/or statistics. Returning empty standard deviations."
            )
            return pd.DataFrame(columns=["snapshotDate", "obsAge", "std"])

        # Get total_variance of the targets
        variance_suffix = "__total_variance"
        variance_targets = [f"{target}{variance_suffix}" for target in target_list]

        # Validate variance targets exist
        for variance_target in variance_targets:
            if variance_target not in properties["targets"]:
                dash_logger.warning(
                    "Selected variance targets couldn't find on the related schema! Returning empty standard deviations."
                )
                return pd.DataFrame(columns=["snapshotDate", "obsAge", "std"])

        # Construct query variables
        expected_variance = []
        denominator_mask = []

        # Setup cluster filtering
        if cluster_list:
            cluster_list = [cluster for cluster in cluster_list]
            if len(cluster_list) == 1:  # mimic tuple
                if isinstance(cluster_list[0], str):
                    selected_clusters = f"('{cluster_list[0]}')"
                else:
                    selected_clusters = f"({cluster_list[0]})"
            else:
                selected_clusters = tuple(cluster_list)

            base_where_clause = f"WHERE a.{properties['cluster']} IN {selected_clusters} AND a.{properties['snapshotDate']} = '{monitoring_date}'"
        else:
            base_where_clause = (
                f"WHERE a.{properties['snapshotDate']} = '{monitoring_date}'"
            )

        # Process masking and build variance terms
        target_variance_terms = []
        for target in variance_targets:
            target_schema = properties["targets"][target]
            # Handle both boolean and string mask values
            if mask == "Masked" or mask is True:
                mask_str = str(target_schema["mask"])
                denominator_mask.append(f"({mask_str} = 1)")
            else:  # "Unmasked" or False
                mask_str = "1"
                denominator_mask.append("(1=1)")
            
            target_variance_terms.append(f"({target_schema['expected']} * {mask_str})")
            expected_variance.append(f"({target_schema['expected']} * {mask_str})")

        # For target correlation, we need to handle cross-terms
        if len(target_list) > 1 and target_correlation != 0:
            # Generate all unique target pairs
            from itertools import combinations
            target_pairs = list(combinations(target_variance_terms, 2))
            cross_terms = []
            for (var1, var2) in target_pairs:
                cross_terms.append(f"{target_correlation} * SQRT({var1} * {var2})")
            
            # Combine all variance and cross terms
            combined_variance = f"{' + '.join(expected_variance)} + {' + '.join(cross_terms)}"
        else:
            combined_variance = " + ".join(expected_variance)

        denominator_mask_select = " OR ".join(denominator_mask)

        # Optimized query with separate correlations
        std_with_covariance_query = f"""
        WITH base_query AS (
          SELECT
            a.{properties['cluster']} AS cluster,
            a.{properties['obsAge']} AS obsAge,
            SUM(CASE WHEN {denominator_mask_select} THEN {common_denominator} ELSE 0 END) AS weight,
            POW(SUM(CASE WHEN {denominator_mask_select} THEN {common_denominator} ELSE 0 END), 2) AS weight_squared,
            SUM({combined_variance}) AS combined_variance
          FROM {full_path} a
          {base_where_clause}
          GROUP BY cluster, obsAge
          DISTRIBUTE BY obsAge
        ),
        weight_totals AS (
          SELECT
            obsAge,
            SUM(weight) AS total_weight,
            POW(SUM(weight), 2) AS total_weight_squared,
            SUM(weight_squared * combined_variance) AS numerator_variance,
            SUM(weight * SQRT(GREATEST(combined_variance, 0))) AS sum_A
          FROM base_query
          GROUP BY obsAge
        )
        SELECT 
          '{monitoring_date}' AS snapshotDate,
          obsAge,
          SQRT(
            GREATEST(
              (
                numerator_variance 
                + {cluster_correlation} * (sum_A * sum_A - numerator_variance)
              ) / NULLIF(total_weight_squared, 0),
              0
            )
          ) AS std
        FROM weight_totals
        ORDER BY obsAge
        """

        std_df = run_query(
            std_with_covariance_query, result_type="pandas"
        )

        if isinstance(std_df, pd.DataFrame) and not std_df.empty:
            return std_df
        else:
            dash_logger.warning(
                "Standard deviations with covariance query returned empty table."
            )
            return pd.DataFrame(columns=["snapshotDate", "obsAge", "std"])

    except Exception as e:
        raise type(e)(
            f"Failed to fetch standard deviations with covariance: {str(e)}"
        ) from e


def get_restated_value(consolidated_name, cluster_list, target_list, monitoring_date):
    """
    Given schema, cluster list, target list, and monitoring date, query the value
    to construct a restatement line.
    """
    report_type = "performance2"
    properties, full_path = parse_schema_properties(consolidated_name, report_type)

    common_denominator = extract_common_denominator(properties["targets"], target_list)
    check_target_consistency(properties, target_list)

    mask = False
    restated = []
    denominator_mask = []

    if cluster_list:
        cluster_list = [cluster for cluster in cluster_list]
        if len(cluster_list) == 1: # mimic tuple
            if isinstance(cluster_list[0], str):
                selected_clusters = f"('{cluster_list[0]}')"  # wrap with ' ' if string
            else:
                selected_clusters = f"({cluster_list[0]})"  
        else:
            selected_clusters = tuple(cluster_list)

        where_clause1 = f"WHERE {properties['cluster']} IN {selected_clusters} AND {properties['monitoring_snapshotDate']['name']} = '{monitoring_date}'"

    else:
        where_clause1 = f"WHERE {properties['monitoring_snapshotDate']['name']} = '{monitoring_date}'"

    for target in target_list:
        target_schema = properties["targets"][target]

        if mask == "Masked":
            mask_str = str(target_schema["mask"])
            denominator_mask.append("(" + mask_str + "= 1" + ")")
        else:
            mask_str = "1"
            denominator_mask.append("(1=1)")  # random always TRUE STATEMENT

        restated.append(
            "("
            + target_schema["restated"]  # restated
            + " * "
            + target_schema["numerator_weight"]
            + " * "
            + mask_str
            + ")"
        )

    restated_line = "+".join(restated)
    denominator_mask_select = "OR".join(denominator_mask)

    query = f"""
    -- restatement line
    WITH restatement_query AS (
        SELECT 
            {properties['monitoring_snapshotDate']['name']} AS monitoringDate, 
            SUM(CASE WHEN {denominator_mask_select} THEN {common_denominator} ELSE 0 END) AS common_denominator,
            SUM({restated_line}) AS restated_numerator
        FROM {full_path}
        {where_clause1}
        GROUP BY 
            {properties['monitoring_snapshotDate']['name']}
    )
    SELECT
        monitoringDate,
        restated_numerator / NULLIF(common_denominator, 0) AS restated_line
    FROM restatement_query
    """

    rows = run_query(query, result_type="rows")

    if rows:
        for row in rows:
            restated_line_val = row.restated_line
            return restated_line_val
    else:
        dash_logger.info(
            f"Failed to fetch restated-line for {full_path}: Empty rows, returning None."
        )
        return None


@cache.memoize(timeout=7200)
def fetch_kldivergence_data(consolidated_name, cluster_list, snapshot_date):
    """
    Args:
        consolidated_name: Name of the consolidated schema.
        cluster_list: List of cluster IDs or empty list ([]) which means ALL.
        snapshot_date: Str(Date)
    Returns:
        DataFrame: Pandas DataFrame containing kldivergence data.

    Raises:
        KeyError: If required keys are missing in schema.
        ValueError: If input validation fails.
    """

    try:
        report_type = "performance5"
        properties, full_path = parse_schema_properties(consolidated_name, report_type)

        if cluster_list:
            cluster_list = [cluster for cluster in cluster_list]
            if len(cluster_list) == 1: # mimic tuple
                if isinstance(cluster_list[0], str):
                    selected_clusters = f"('{cluster_list[0]}')"  # wrap with ' ' if string
                else:
                    selected_clusters = f"({cluster_list[0]})"  
            else:
                selected_clusters = tuple(cluster_list)

            where_clause1 = f"SUM(CASE WHEN {properties['cluster']} IN {selected_clusters} THEN {properties['bucket_value']} ELSE 0 END) AS selected_cluster_bucket_weight"

        else:  # all clusters
            where_clause1 = (
                f"SUM({properties['bucket_value']}) AS selected_cluster_bucket_weight"
            )

        kl_div_query = f"""
        WITH bucket_data AS (
            SELECT 
                {properties['snapshotDate']} as snapshotDate,
                {properties['predictor']} as predictor,
                {properties['bucket_id']} as bucket_id,
                bucket_lb, 
                bucket_ub,
                SUM({properties['bucket_value']}) AS accross_cluster_bucket_weight,
                {where_clause1}
            FROM 
                {full_path}
            GROUP BY 
                {properties['snapshotDate']},
                {properties['predictor']},
                {properties['bucket_id']}, 
                bucket_lb, 
                bucket_ub
        ),
        combined_data AS (
            SELECT
                snapshotDate,
                predictor,
                bucket_id,
                bucket_lb,
                bucket_ub,
                accross_cluster_bucket_weight,
                selected_cluster_bucket_weight,
                accross_cluster_bucket_weight / SUM(accross_cluster_bucket_weight) OVER (PARTITION BY snapshotDate, predictor) AS _pP,
                selected_cluster_bucket_weight / SUM(selected_cluster_bucket_weight) OVER (PARTITION BY snapshotDate, predictor) AS _pQ
            FROM bucket_data 
        ),
        kl_divergence AS (  
            SELECT
            snapshotDate,
            predictor,
                SUM(COALESCE(_pP * LOG(_pP / CASE WHEN _pQ = 0 THEN 0.000000001 ELSE _pQ END), 0)) AS kl_divergence    
            FROM
                combined_data
            GROUP BY
            snapshotDate,
                predictor
            ORDER BY
            snapshotDate,
            predictor
        )
            SELECT
            predictor,
                kl_divergence
            FROM
                kl_divergence
            WHERE 
            snapshotDate = '{snapshot_date}' -- example snapshotDate
        """

        kl_div_df = run_query(kl_div_query, result_type="pandas")

        if isinstance(kl_div_df, pd.DataFrame) and kl_div_df.shape[0] > 0:
            return kl_div_df
        else:
            raise ValueError("KL Divergence query for predictors returned empty table.")
    except Exception as e:
        raise type(e)(f"Failed to fetch KL Divergence data: {str(e)}") from e


@cache.memoize(timeout=7200)
def fetch_histogram_data(consolidated_name, cluster_list, snapshot_date, predictor):
    """
    Args:
        consolidated_name: Name of the consolidated schema.
        cluster_list: List of cluster IDs or empty list ([]) which means ALL.
        snapshot_date: Str(Date)
        predictor: List of selected predictors.
    Returns:
        DataFrame: Pandas DataFrame containing histogram data.

    Raises:
        KeyError: If required keys are missing in schema.
        ValueError: If input validation fails.
    """

    try:
        report_type = "performance5"
        properties, full_path = parse_schema_properties(consolidated_name, report_type)

        # construct the query string
        if cluster_list:
            cluster_list = [cluster for cluster in cluster_list]
            if len(cluster_list) == 1: # mimic tuple
                if isinstance(cluster_list[0], str):
                    selected_clusters = f"('{cluster_list[0]}')"  # wrap with ' ' if string
                else:
                    selected_clusters = f"({cluster_list[0]})"  
            else:
                selected_clusters = tuple(cluster_list)

            where_clause1 = f"SUM(CASE WHEN {properties['cluster']} IN {selected_clusters} THEN {properties['bucket_value']} ELSE 0 END) AS selected_cluster_bucket_weight"

        else:  # all clusters
            where_clause1 = (
                f"SUM({properties['bucket_value']}) AS selected_cluster_bucket_weight"
            )

        histogram_query = f"""
        -- Calculating KL-divergence for all predictors given snapshotDate/cluster
            WITH bucket_data AS (
                SELECT 
                    {properties['snapshotDate']} as snapshotDate,
                    {properties['predictor']} as predictor,
                    {properties['bucket_id']} as bucket_id,
                    {properties['bucket_name']} as bucket_name,
                    bucket_lb, 
                    bucket_ub,
                    SUM({properties['bucket_value']}) AS accross_cluster_bucket_weight,
                    {where_clause1}

                FROM 
                    {full_path}
                GROUP BY 
                    {properties['bucket_name']},
                    {properties['snapshotDate']},
                    {properties['predictor']},
                    {properties['bucket_id']},
                    bucket_lb, 
                    bucket_ub
            ),
            combined_data AS (
                SELECT
                    snapshotDate,
                    predictor,
                    bucket_id,
                    bucket_name,
                    bucket_lb,
                    bucket_ub,
                    accross_cluster_bucket_weight,
                    selected_cluster_bucket_weight,
                    accross_cluster_bucket_weight / SUM(accross_cluster_bucket_weight) OVER (PARTITION BY snapshotDate, predictor) AS _pP,
                    selected_cluster_bucket_weight / SUM(selected_cluster_bucket_weight) OVER (PARTITION BY snapshotDate, predictor) AS _pQ
                FROM bucket_data 
            )
            SELECT           -- Calculate pQ_Histogram 
                bucket_id,
                bucket_name,
                bucket_lb,
                bucket_ub,
                accross_cluster_bucket_weight,
                _pP AS Aggregate,
                combined_data.selected_cluster_bucket_weight,
                _pQ AS Cluster
            FROM 
                combined_data
            WHERE 
                snapshotDate  = '{snapshot_date}' -- example snapshotDate
                AND predictor = '{predictor}' -- example predictor
        """

        histogram_df = run_query(
            histogram_query, result_type="pandas"
        )

        if isinstance(histogram_df, pd.DataFrame) and histogram_df.shape[0] > 0:
            return histogram_df
        else:
            raise ValueError("Histogram query returned empty table.")

    except Exception as e:
        raise type(e)(f"Failed to fetch histogram data: {str(e)}") from e
