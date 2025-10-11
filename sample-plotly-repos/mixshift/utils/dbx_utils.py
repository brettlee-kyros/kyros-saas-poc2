from kyros_plotly_common.core.cache import cache
from kyros_plotly_common.core import dbx_client
from kyros_plotly_common.logger import dash_logger
from kyros_plotly_common.utils.schema import get_full_path_from_consolidated_name, parse_schema_properties



@cache.memoize(timeout=7200)
def get_available_dates(consolidated_name):
    """
    Fetches available dates for each schema/client, and caches them into Redis.
    
    Args:
        full_path: Full path to the table.
    Returns:
        list: List of available dates as list of date strings.
    """
    try:
        # Validate and fetch schema
        properties, full_path = parse_schema_properties(consolidated_name,report_type="mix")
        if "date" not in properties:
            raise KeyError("'date' child-key is missing in the lookup schema.")

        if not properties["date"]:
            raise ValueError("'date' child-key is empty or invalid in the lookup schema.")
        
        # Construct the query to fetch available dates
        date_column = properties["date"]
        select_clause = f"SELECT DISTINCT {date_column} FROM {full_path} ORDER BY {date_column} DESC"

        # Run the query
        dates_df = dbx_client.run_query(select_clause, result_type="pandas")

        # Convert the pandas DataFrame to a list of date strings
        dates_list = dates_df[date_column].tolist()

        return dates_list
    except Exception as e:
        raise type(e)(f"Failed to fetch available dates: {str(e)}") from e

@cache.memoize(timeout=7200)
def get_weight_options(consolidated_name):
    """
    Get weight dropdown options based on mix type and metadata properties
    
    Args:
        full_path: Full path to the table.
    
    Returns:
        list: List of dictionaries with weight options in format [{"label": label, "value": column}, ...]
    
    Raises:
        ValueError: If properties or weights are not found.
    """
    try:
        # Get properties to access weight definitions
        properties, _ = parse_schema_properties(consolidated_name,report_type="mix")
        if not properties:
            raise ValueError(f"No properties found for {consolidated_name}")
        
        # Get weights from properties
        weights = properties["weights"]
        
        if not weights:
            dash_logger.warning(f"No weights found in properties for {consolidated_name}. Using fallback weights.")
            weight_options = [{"label": "Count", "value": "count"}]
        else:
            # Convert weights dictionary to dropdown options
            weight_options = [{"label": label, "value": column} for label, column in weights.items()]
            
            # If no weights are found, add a default option
            if not weight_options:
                weight_options = [{"label": "Count", "value": "count"}]
        
        return weight_options
    
    except Exception as e:
        error_msg = f"Failed to get weight options: {e}"
        error_id = dash_logger.error(error_msg, exc_info=e)
        raise ValueError(error_msg)

@cache.memoize(timeout=7200)
def get_segment_bubbler_data(consolidated_name, weight):
    """
    Get segment bubbler data with real data from the database
    
    Args:
        full_path: Full path to the table.
        weight: Weight column to use.
    
    Returns:
        list: List of dictionaries containing segment data with weights.
    
    Raises:
        ValueError: If required properties or data are not found.
    """
    try:
        # Get properties for the table path
        properties, full_path = parse_schema_properties(consolidated_name,report_type="mix")
        if not properties:
            raise ValueError(f"No properties found for {consolidated_name}")
        
        # Get segments from properties
        segments = properties.get("segments", {})
        if not segments:
            raise ValueError(f"No segments found in properties for {consolidated_name}")
        
        # Get date column from properties
        date_column = properties.get("date", "")
        if not date_column:
            raise ValueError(f"No date column found in properties for {consolidated_name}")
        
        # Get all segment columns
        segment_columns = list(segments.values())
        
        # Build a query to get unique combinations of segment values
        segment_select = ", ".join(segment_columns)
        
        # Query to get unique segment combinations and their weights
        query = f"""
        SELECT {segment_select}, SUM({weight}) as weight
        FROM {full_path}
        GROUP BY {segment_select}
        ORDER BY weight DESC
        """
        
        # Execute query
        df = dbx_client.run_query(query, result_type="pandas")
        
        # Verify all segment columns exist in the DataFrame
        missing_columns = [col for col in segment_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing segment columns in query results: {', '.join(missing_columns)}")
        
        # Format segment data
        segment_data = []
        
        # For each unique segment combination
        for _, row in df.iterrows():
            # Create a segment entry with all segment values
            segment_entry = {
                "weight": f"{row['weight']:,.0f}",
                "segment_values": {col: row[col] for col in segment_columns}
            }
            
            # Add segment labels
            for col in segments.values():
                segment_entry[col] = row[col]
            
            segment_data.append(segment_entry)
        
        return segment_data
    
    except Exception as e:
        error_msg = f"Failed to get segment bubbler data: {e}"
        error_id = dash_logger.error(error_msg, exc_info=e)
        raise ValueError(error_msg)

@cache.memoize(timeout=7200)
def get_variable_bubbler_data(consolidated_name, selected_segments, date1, date2, weight, all_segments):
    """
    Get variable bubbler data for a selected segment using SQL for calculation
    
    Args:
        full_path: Full path to the table.
        selected_segments: List of dictionaries containing segment values to filter by. Each dictionary contains a segment label and value.
        date1: First date for comparison.
        date2: Second date for comparison.
        weight: Weight column to use.
    
    Returns:
        list: List of dictionaries containing variable data with KL divergence.
    
    Raises:
        ValueError: If required properties or data are not found.
    """
    try:
        # Get properties for the full path
        properties, full_path = parse_schema_properties(consolidated_name,report_type="mix")
        if not properties:
            raise ValueError(f"No properties found for {consolidated_name}")
        
        # Get date column from properties
        date_column = properties.get("date", "")
        if not date_column:
            raise ValueError(f"No date column found in properties for {consolidated_name}")
        
        # Get variable column from properties
        variable_column = properties.get("variable", "")
        if not variable_column:
            raise ValueError(f"No variable column found in properties for {consolidated_name}")
        
        # Get bucket columns from properties
        bucket_id = properties.get("bucket_id", "")
        bucket_name = properties.get("bucket_name", "")
        if not bucket_id or not bucket_name:
            raise ValueError(f"No bucket columns found in properties for {consolidated_name}")
        
        # Build WHERE clause for segment filtering using minimized helper function
        where_clause = build_minimized_segment_where_clause(selected_segments, all_segments)
        
        # SQL query to calculate KL divergence and distributions in one go
        query = f"""
        WITH bucket_weights AS (
            SELECT 
                {variable_column},
                {bucket_id},
                {bucket_name},
                {date_column},
                SUM({weight}) as weight
            FROM {full_path}
            WHERE 1=1 {where_clause}
            GROUP BY {variable_column}, {bucket_id}, {bucket_name}, {date_column}
        ),
        total_weights AS (
            SELECT 
                {variable_column},
                {date_column},
                SUM(weight) as total_weight
            FROM bucket_weights
            GROUP BY {variable_column}, {date_column}
        ),
        normalized_weights AS (
            SELECT 
                bw.{variable_column},
                bw.{bucket_id},
                bw.{bucket_name},
                bw.{date_column},
                bw.weight,
                tw.total_weight,
                CASE WHEN tw.total_weight > 0 
                     THEN bw.weight / tw.total_weight 
                     ELSE 0.000000001 END as normalized_weight
            FROM bucket_weights bw
            JOIN total_weights tw ON bw.{variable_column} = tw.{variable_column} 
                                 AND bw.{date_column} = tw.{date_column}
        ),
        date1_dist AS (
            SELECT 
                {variable_column},
                {bucket_id},
                normalized_weight as p
            FROM normalized_weights
            WHERE {date_column} = '{date1}'
        ),
        date2_dist AS (
            SELECT 
                {variable_column},
                {bucket_id},
                normalized_weight as q
            FROM normalized_weights
            WHERE {date_column} = '{date2}'
        ),
        combined_dist AS (
            SELECT 
                COALESCE(d1.{variable_column}, d2.{variable_column}) as {variable_column},
                COALESCE(d1.{bucket_id}, d2.{bucket_id}) as {bucket_id},
                COALESCE(d1.p, 0.0000000001) as p,
                COALESCE(d2.q, 0.0000000001) as q
            FROM date1_dist d1
            FULL OUTER JOIN date2_dist d2 ON d1.{variable_column} = d2.{variable_column} 
                                         AND d1.{bucket_id} = d2.{bucket_id}
        ),
        kl_divergence AS (
            SELECT 
                {variable_column},
                SUM(p * LOG(p / q)) as kl_divergence
            FROM combined_dist
            GROUP BY {variable_column}
        ),
        distributions AS (
            SELECT 
                {variable_column},
                {date_column},
                MAP_FROM_ENTRIES(COLLECT_LIST(
                    NAMED_STRUCT('key', CAST({bucket_id} AS STRING), 'value', weight)
                )) as dist_array
            FROM bucket_weights
            GROUP BY {variable_column}, {date_column}
        )
        SELECT 
            kd.{variable_column},
            kd.kl_divergence,
            MAP_FROM_ENTRIES(COLLECT_LIST(
                NAMED_STRUCT('key', CAST(d.{date_column} AS STRING), 'value', d.dist_array)
            )) as all_distributions
        FROM kl_divergence kd
        JOIN distributions d ON kd.{variable_column} = d.{variable_column}
        GROUP BY kd.{variable_column}, kd.kl_divergence
        ORDER BY kd.kl_divergence DESC
        """
        
        # Execute query
        result = dbx_client.run_query(query, result_type="pandas")
        
        # Fetch bucket_id to bucket_name mapping for each variable
        # Query all unique (variable, bucket_id, bucket_name) combinations
        # Apply the same segment filtering to ensure consistency
        label_query = f"""
        SELECT {variable_column}, {bucket_id}, {bucket_name}
        FROM {full_path}
        WHERE 1=1 {where_clause}
        GROUP BY {variable_column}, {bucket_id}, {bucket_name}
        """
        label_df = dbx_client.run_query(label_query, result_type="pandas")
        # Build mapping: {variable: {bucket_id: 'bucket_id - bucket_name'}}
        bucket_label_map = {}
        for _, row in label_df.iterrows():
            var = row[variable_column]
            bid = str(row[bucket_id])
            bname = str(row[bucket_name])
            label = f"{bid} - {bname}"
            if var not in bucket_label_map:
                bucket_label_map[var] = {}
            bucket_label_map[var][bid] = label

        # Process the result into the desired format
        variable_data = []
        for _, row in result.iterrows():
            var = row[variable_column]
            variable_data.append({
                "variable": var,
                "kl_divergence": row['kl_divergence'],
                "distributions": dict(row['all_distributions']),
                "bucket_labels": bucket_label_map.get(var, {})
            })
        return variable_data
    
    except Exception as e:
        error_msg = f"Failed to get variable bubbler data: {e}"
        error_id = dash_logger.error(error_msg, exc_info=e)
        raise ValueError(error_msg)


def build_minimized_segment_where_clause(selected_segments, all_segments):
    """
    Build a minimized SQL WHERE clause for segment filtering using tree factoring.
    Args:
        selected_segments: List of dicts with 'segment_values' key mapping to dict of column-value pairs.
        all_segments: List of dicts with 'segment_values' key mapping to dict of column-value pairs.

    Returns:
        str: Minimized SQL WHERE clause (including AND prefix if not empty).
    """
    if not selected_segments:
        return ""
    
    def escape_sql_value(val):
        return str(val).replace("'", "''")
    
    # Collect all unique keys while preserving order from first segment that has them
    all_keys = []
    # First look in all_segments to establish base ordering
    for seg in all_segments:
        if isinstance(seg, dict) and seg.get('segment_values'):
            for k in seg['segment_values']:
                if k not in all_keys:
                    all_keys.append(k)
    # Then add any remaining keys from selected_segments
    for seg in selected_segments:
        if isinstance(seg, dict) and seg.get('segment_values'):
            for k in seg['segment_values']:
                if k not in all_keys:
                    all_keys.append(k)
    
    # Filter valid segments: must have all keys with non-None values
    valid_segments = []
    for seg in selected_segments:
        if isinstance(seg, dict) and seg.get('segment_values'):
            seg_vals = seg['segment_values']
            if all(k in seg_vals and seg_vals[k] is not None for k in all_keys):
                valid_segments.append(seg)
    
    if not valid_segments:
        return ""
    
    # Build factoring tree recursively with IN clause optimization
    def build_tree(segments, keys):
        if not keys or not segments:
            return None
        
        key = keys[0]
        groups = {}
        for seg in segments:
            val = seg['segment_values'][key]
            groups.setdefault(val, []).append(seg)
        
        # If all segments have same value for this key, factor it out
        if len(groups) == 1:
            val, segs = next(iter(groups.items()))
            child = build_tree(segs, keys[1:])
            if child:
                return {key: (val, child)}
            else:
                return {key: (val, None)}
        else:
            # Check if we should use IN clause (when all children are None or simple)
            use_in_clause = True
            child_results = {}
            for val, segs in groups.items():
                child = build_tree(segs, keys[1:])
                child_results[val] = child
                if child is not None:
                    # Check if child is a simple {key: (value, None)} structure
                    if not (isinstance(child, dict) and len(child) == 1):
                        use_in_clause = False
                    else:
                        child_node = next(iter(child.values()))
                        if not (isinstance(child_node, tuple) and child_node[1] is None):
                            use_in_clause = False
            
            if use_in_clause:
                values = list(groups.keys())
                return {key: values}
            else:
                return {key: child_results}
    
    # Convert tree to SQL condition with proper grouping
    def tree_to_sql(tree, keys):
        if not tree or not keys:
            return ""
        
        key = next(iter(tree))
        node = tree[key]
        
        # Factored node: {key: (value, child_tree)}
        if isinstance(node, tuple):
            val, child = node
            escaped_val = escape_sql_value(val)
            cond = f"{key} = '{escaped_val}'"
            child_sql = tree_to_sql(child, keys[1:])
            if child_sql:
                return f"{cond} AND {child_sql}"
            return cond
        
        # IN clause node: {key: [value1, value2, ...]}
        elif isinstance(node, list):
            if len(node) == 1:
                escaped_val = escape_sql_value(node[0])
                return f"{key} = '{escaped_val}'"
            else:
                values_str = "', '".join(escape_sql_value(val) for val in node)
                return f"{key} IN ('{values_str}')"
        
        # Branch node: {key: {value: child_tree, ...}}
        elif isinstance(node, dict):
            or_clauses = []
            for val, child in node.items():
                escaped_val = escape_sql_value(val)
                cond = f"{key} = '{escaped_val}'"
                child_sql = tree_to_sql(child, keys[1:])
                if child_sql:
                    or_clauses.append(f"({cond} AND {child_sql})")
                else:
                    or_clauses.append(f"({cond})")
            
            if len(or_clauses) == 1:
                return or_clauses[0]
            else:
                return "(" + " OR ".join(or_clauses) + ")"
        
        return ""
    
    # Build tree and generate SQL
    tree = build_tree(valid_segments, all_keys)
    sql = tree_to_sql(tree, all_keys)
    
    return f"AND ({sql})" if sql else ""