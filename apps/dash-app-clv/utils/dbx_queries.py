from itertools import chain, combinations


def generate_grouping_sets(dimensions, full_path):
    """Generate all non-empty subsets of dimensions."""
    if not dimensions:  # If dimensions list is empty
        return ""
    try:
        subsets = chain.from_iterable(
            combinations(dimensions, r) for r in range(1, len(dimensions) + 1)
        )

        return ", ".join(f"({', '.join(subset)})" for subset in subsets)

    except Exception as e:
        raise type(e)(
            f"Failed to constrcut subset of manual dimensions: {str(e)}"
        ) from e


def construct_mandim_query(select_clause, full_path):
    return f"""        
        -- bubbler/manual dimensions     
        SELECT {select_clause} 
        FROM {full_path}
        """


def construct_all_exposures_query(properties, full_path, where_clause):
    return f"""        
        -- all exposures     
        SELECT DISTINCT
            {properties['snapshotDate']} as snapshotDate, 
            {properties['exposure']} as current_snapshotDate_exposure
        FROM {full_path}
        {where_clause} 
        ORDER BY snapshotDate
        """


def construct_current_exp_query(
    properties,
    where_clause,
    full_path,
    manual_dimensions,
    is_cluster,
):

    if is_cluster:
        return f"""  
    -- current date exposures           
    SELECT 
        {properties['exposure']} as current_snapshotDate_exposure,
        {properties['cluster']} as cluster
    FROM {full_path}
    {where_clause} 
    ORDER BY 
        {properties['exposure']}
    """
    else:  # agg version
        grouping_sets = generate_grouping_sets(manual_dimensions, full_path)

        # Create the SELECT part, adding all grouping dimensions dynamically
        select_columns = ", ".join(manual_dimensions)

        return f"""
        -- Aggregated current date exposures with GROUPING SETS         
        SELECT
            SUM({properties['exposure']}) as current_snapshotDate_exposure,
            {select_columns}
        FROM
            {full_path}
        {where_clause}
        GROUP BY GROUPING SETS ({grouping_sets})
    """


def construct_r2_query(
    properties,
    actuals,
    expected,
    denominator_mask,
    where_clause,
    full_path,
    manual_dimensions,  # list of dimensions
    is_cluster,
    common_denominator,
):

    actual_select = " + ".join(actuals)
    expected_select = " + ".join(expected)

    if is_cluster or not manual_dimensions:  # Cluster level (no manual dimensions)
        groupby_clause = f"GROUP BY {properties['cluster']}, {properties['snapshotDate']}, {properties['obsAge']}"
        return f"""
            ---R2-calculations for Cluster Level
            WITH base_query AS (
                SELECT
                    {properties['cluster']} AS cluster, 
                    {properties['snapshotDate']} AS snapshotDate, 
                    {properties['obsAge']} AS obsAge,
                    SUM({actual_select}) AS actual,
                    SUM({expected_select}) AS expected,
                    AVG(SUM({actual_select})) OVER (PARTITION BY {properties['cluster']}) AS mean_actual
                FROM {full_path}
                {where_clause}
                {groupby_clause}
            ),
            r2_query AS (
                SELECT
                    cluster,
                    SUM(POWER(actual - expected, 2)) AS r2_num,
                    SUM(POWER(actual - mean_actual, 2)) AS r2_denom
                FROM base_query
                GROUP BY cluster
            )
            SELECT
                GREATEST(-1, (1 - (r2_num / NULLIF(r2_denom, 0)))) AS r2_dev, -- cap at -1
                cluster
            FROM r2_query
        """
    else:  # Aggregated version with GROUPING SETS
        grouping_sets = generate_grouping_sets(manual_dimensions, full_path)
        groupby_clause = f"GROUP BY GROUPING SETS ({grouping_sets}), {properties['snapshotDate']}, {properties['obsAge']}"

        return f"""
            ---R2-calculations with GROUPING SETS
            WITH pre_query AS (
                SELECT
                    {', '.join(manual_dimensions)},
                    {properties['snapshotDate']} AS snapshotDate, 
                    {properties['obsAge']} AS obsAge,
                    SUM(CASE WHEN {' OR '.join(denominator_mask)} THEN {common_denominator} ELSE 0 END) AS common_denominator,
                    SUM({actual_select}) AS actual_numerator,
                    SUM({expected_select}) AS expected_numerator
                FROM {full_path}
                {groupby_clause}
            ),
            base_query AS (
                SELECT
                    {', '.join(manual_dimensions)},
                    snapshotDate,
                    obsAge,
                    actual_numerator / NULLIF(common_denominator, 0) AS actual,
                    expected_numerator / NULLIF(common_denominator, 0) AS expected,
                    AVG(actual_numerator / NULLIF(common_denominator, 0)) 
                        OVER (PARTITION BY {', '.join(manual_dimensions)}) AS mean_actual
                FROM pre_query
            ),
            r2_query AS (
                SELECT
                    {', '.join(manual_dimensions)},
                    SUM(POWER(actual - expected, 2)) AS r2_num,
                    SUM(POWER(actual - mean_actual, 2)) AS r2_denom
                FROM base_query
                GROUP BY {', '.join(manual_dimensions)}
            )
            SELECT
                GREATEST(-1, (1 - (r2_num / NULLIF(r2_denom, 0))))  AS r2_dev, -- cap at -1!
                {', '.join(manual_dimensions)}
            FROM r2_query
        """
        
        
def construct_fimpact_query( 
            properties,
            restated,
            baseline,
            where_clause,
            full_path,
            full_path2,
            manual_dimensions,
            bubblers_dimensions,
            is_cluster
):
     # Join columns for aggregations
    restated_row_sum = "+".join(restated)
    baseline_row_sum = "+".join(baseline)
    
    # Determine grouping logic
    if is_cluster or not manual_dimensions:  # cluster-level
        groupby_clause = f"GROUP BY dims.{properties['cluster']}"
        group_select = f"{properties['cluster']}"
        group_select_w_alias = f"dims.{properties['cluster']} AS cluster"

    else:
        manual_dimensions_w_dims = ['dims.' + x for x in manual_dimensions]
        grouping_sets = generate_grouping_sets(manual_dimensions_w_dims, full_path)
        groupby_clause = f"GROUP BY GROUPING SETS ({grouping_sets})"
        
        group_select = ",".join(bubblers_dimensions)  # Valid column names directly
        group_select_w_alias = ", ".join(manual_dimensions_w_dims)  # Valid column names directly

        

    return f"""
        -- financial impact
        WITH unique_dims AS (
            SELECT DISTINCT
                {group_select}
            FROM {full_path2}
        )
        SELECT
            SUM({restated_row_sum})  -  SUM({baseline_row_sum})  AS financial_impact,
            {group_select_w_alias} 
            FROM  {full_path} AS perf2
            JOIN unique_dims dims
                ON perf2.{properties['cluster']} = dims.{properties['cluster']}
                {where_clause}
            {groupby_clause}
        """


def construct_pval_financial_impact_query(
    properties,
    actuals,
    expected,
    variance_expected,
    where_clause,
    full_path,
    manual_dimensions,  # List of valid column names
    is_cluster,
    common_denominator,
    current_snapshot_date,
    z_score,
):
    # Join columns for aggregations
    actual_select = " + ".join(actuals)
    expected_select = " + ".join(expected)
    variance_select = " + ".join(variance_expected)

    # Determine grouping logic
    if is_cluster or not manual_dimensions:  # cluster-level
        groupby_clause = f"GROUP BY {properties['cluster']}, {properties['snapshotDate']}, {properties['obsAge']}"
        group_select = f"{properties['cluster']} AS cluster"
        partition_by = "cluster"
    else:
        grouping_sets = generate_grouping_sets(manual_dimensions, full_path)
        groupby_clause = f"GROUP BY GROUPING SETS ({grouping_sets}), {properties['snapshotDate']}, {properties['obsAge']}"
        group_select = ", ".join(manual_dimensions)  # Valid column names directly
        partition_by = ", ".join(manual_dimensions)

    # Optional WHERE clause for denominator masking
    #denominator_mask_select = " OR ".join(denominator_mask)

    # Final SQL query
    return f"""
        ---P-Value and Exposure Score Calculations
        WITH aggregated_data AS (
            SELECT
                {group_select}, 
                {properties['snapshotDate']} AS snapshotDate, 
                {properties['obsAge']} AS obsAge,
                SUM({common_denominator}) AS common_denominator,
                SUM({variance_select}) AS variance_numerator,
                SUM({actual_select}) AS actual_numerator,
                SUM({expected_select}) AS expected_numerator
            FROM
                {full_path}
            {where_clause}
            {groupby_clause}
        ),
        computed_metrics AS (
            SELECT
                {partition_by},
                snapshotDate,
                obsAge,
                common_denominator,
                SQRT(variance_numerator / NULLIF(POWER(common_denominator, 2), 0)) AS std,
                SUM(actual_numerator) OVER (
                    PARTITION BY snapshotDate, {partition_by}
                    ORDER BY obsAge ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) / NULLIF(common_denominator, 0) AS cum_actual,
                SUM(expected_numerator) OVER (
                    PARTITION BY snapshotDate, {partition_by}
                    ORDER BY obsAge ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) / NULLIF(common_denominator, 0) AS cum_expected
            FROM
                aggregated_data
        )
        SELECT 
            (cum_actual - cum_expected) / NULLIF(std, 0) AS z_score,  
            CASE 
                WHEN ABS(cum_actual - cum_expected) > NULLIF({z_score} * std, 0) THEN 
                    (cum_actual - cum_expected) * common_denominator
                ELSE 
                    0 -- Within CI, no financial impact
            END AS exposure_score,
            {partition_by}
        FROM 
            computed_metrics
        WHERE 
            obsAge = months_between('{current_snapshot_date}', snapshotDate) -- Current Date
        ORDER BY 
            snapshotDate, obsAge;
    """


def construct_triangle_data_query(
    properties,
    actuals,
    expected,
    where_cluster_clause,
    dev_value,
    is_variance,
    full_path,
    denominator_mask_select,
    common_denominator,
):
    # aggregate actual and expected values
    actual_select = "+".join(actuals)
    expected_select = "+".join(expected)

    base_query = f"""
        WITH triangle_base_query AS(
        SELECT 
            {properties['snapshotDate']} as snapshotDate, 
            {properties['obsAge']} as obsAge,
            SUM(CASE WHEN {denominator_mask_select} THEN {common_denominator} ELSE 0 END) AS common_denominator, 
            SUM({actual_select}) AS actual_numerator,
            SUM({expected_select}) AS expected_numerator
        FROM {full_path}
        {where_cluster_clause}
        GROUP BY 
            {properties['snapshotDate']}, 
            {properties['obsAge']}
        )
        """

    if dev_value == "dev":
        query_extension = """
        SELECT 
            snapshotDate,
            obsAge,
            actual_numerator / NULLIF(common_denominator, 0) AS actual,
            expected_numerator / NULLIF(common_denominator, 0) AS expected,
            actual - expected AS residual
        FROM triangle_base_query
        ORDER BY 
            snapshotDate, 
            obsAge
        """
        triangle_data_query = base_query + query_extension

    else:  # dev_since
        if not is_variance:
            query_extension = """
            ,cumulative_query AS (
                SELECT 
                snapshotDate,
                obsAge,
                common_denominator,
                actual_numerator,
                expected_numerator,
                SUM(actual_numerator) OVER (PARTITION BY snapshotDate ORDER BY obsAge ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_actual_numerator,
                SUM(expected_numerator) OVER (PARTITION BY snapshotDate ORDER BY obsAge ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_expected_numerator
            FROM triangle_base_query
            )
            SELECT 
                snapshotDate,
                obsAge,
                cum_actual_numerator / NULLIF(common_denominator, 0) AS cum_actual,
                cum_expected_numerator / NULLIF(common_denominator, 0) AS cum_expected,
                (cum_actual - cum_expected) as cum_residual
            FROM cumulative_query
            ORDER BY
                snapshotDate,
                obsAge
            """
        else:  # variance related target
            query_extension = """
                    SELECT 
                        snapshotDate,
                        obsAge,
                        actual_numerator / NULLIF(POWER(common_denominator, 2), 0) AS actual,
                        expected_numerator / NULLIF(POWER(common_denominator, 2), 0) AS expected,
                        expected - actual AS residual
                    FROM triangle_base_query
                    ORDER BY 
                        snapshotDate, 
                        obsAge
                """

    triangle_data_query = base_query + query_extension
    return triangle_data_query


def construct_reweighted_triangle_data_query(
    properties,
    actuals,
    expected,
    common_denominator,
    is_variance,
    where_clause1,
    where_clause2,
    full_path,
):
    actual_select = "+".join(actuals)
    expected_select = "+".join(expected)

    if not is_variance:
        reweighted_triangledata_query = f"""
        WITH reweights_query AS(
            SELECT 
                {common_denominator} AS numerator_reweight,
                {properties['snapshotDate']} AS snapshotDate, 
                {properties['cluster']} AS cluster
            FROM {full_path}
            {where_clause1}
            GROUP BY 
                {properties['snapshotDate']}, 
                {properties['cluster']},
                {common_denominator}
            HAVING {common_denominator} IS NOT NULL -- not sure with this part!
        ),
        reweighted_values AS(
            SELECT 
                b.{properties['snapshotDate']} AS snapshotDate, 
                b.{properties['obsAge']} AS obsAge,
                SUM(w.numerator_reweight) AS reweighted_denominator,
                SUM({actual_select}) as actual_numerator,
                SUM({expected_select}) as expected_numerator
            FROM {full_path} b
            JOIN reweights_query w ON b.{properties['cluster']} = w.cluster
            {where_clause2}
            GROUP BY 
                b.{properties['snapshotDate']}, 
                b.{properties['obsAge']}
        ),
        cumulative_values AS (
            SELECT 
                snapshotDate,
                obsAge,
                reweighted_denominator,
                actual_numerator,
                SUM(actual_numerator) OVER (
                    PARTITION BY snapshotDate 
                    ORDER BY obsAge 
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS cum_actual_numerator,
                SUM(expected_numerator) OVER (
                    PARTITION BY snapshotDate 
                    ORDER BY obsAge 
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS cum_expected_numerator
            FROM reweighted_values
        )
            SELECT 
                snapshotDate,
                obsAge,
                cum_actual_numerator / NULLIF(reweighted_denominator, 0) AS cum_actual,
                cum_expected_numerator / NULLIF(reweighted_denominator, 0) AS cum_expected,
                (cum_actual - cum_expected) as cum_residual
            FROM cumulative_values
            ORDER BY snapshotDate, obsAge
        """
    else:
        reweighted_triangledata_query = f"""
        WITH reweights_query AS(
            SELECT 
                {common_denominator} AS numerator_reweight,
                {properties['snapshotDate']} AS snapshotDate, 
                {properties['cluster']} AS cluster
            FROM {full_path}
            {where_clause1}
            GROUP BY 
                {properties['snapshotDate']}, 
                {properties['cluster']},
                {common_denominator}
            HAVING {common_denominator} IS NOT NULL -- not sure with this part!
        ),
        reweighted_values AS(
            SELECT 
                {properties['snapshotDate']} AS snapshotDate, 
                {properties['obsAge']} AS obsAge,
                SUM(w.numerator_reweight) AS reweighted_denominator,
                SUM({actual_select}) as actual_numerator,
                SUM({expected_select}) as expected_numerator
            FROM {full_path} b
            JOIN reweights_query w ON b.{properties['cluster']} = w.cluster
            {where_clause2}
            GROUP BY 
                {properties['snapshotDate']}, 
                {properties['obsAge']}
        ),
        cumulative_values AS (
            SELECT 
                snapshotDate,
                obsAge,
                reweighted_denominator,
                actual_numerator,
                SUM(actual_numerator) OVER (
                    PARTITION BY snapshotDate 
                    ORDER BY obsAge 
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS cum_actual_numerator,
                SUM(expected_numerator) OVER (
                    PARTITION BY snapshotDate 
                    ORDER BY obsAge 
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS cum_expected_numerator
            FROM reweighted_values
        )
            SELECT 
                snapshotDate,
                obsAge,
                cum_actual_numerator / NULLIF(POWER(reweighted_denominator, 2), 0) AS cum_actual,
                cum_expected_numerator / NULLIF(POWER(reweighted_denominator, 2), 0) AS cum_expected,
                (cum_actual - cum_expected) as cum_residual
            FROM cumulative_values
            ORDER BY snapshotDate, obsAge
        """
    return reweighted_triangledata_query
