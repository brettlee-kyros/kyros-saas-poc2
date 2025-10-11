import pandas as pd

from kyros_plotly_common.utils.schema import parse_schema_properties


def create_column_definitions(consolidated_name, type="segment", column_config=None, tooltip_headers={"default": ""}):
    """
    Create column definitions for AG-Grid based on DataFrame columns
    
    Args:
        full_path (str): Full path to the table
        type (str): Either "segment" or "variable"
        column_config (dict, optional): Custom configuration for specific columns
            Example: {
                "kl_divergence": {
                    "cellRenderer": "BarRenderer",
                    "cellRendererParams": {
                        "context": {
                            "maxValue": "auto",
                            "isCentered": True
                        }
                    }
                }
            }
        tooltip_headers (dict, optional): A dictionary of fields and their tooltip headers
            Example: {
                "variable": "Variable",
                "kl_divergence": "KL Divergence"
            }
        
    Returns:
        list: Column definitions for AG-Grid
    """
    properties, _ = parse_schema_properties(consolidated_name,report_type="mix")
    column_defs = []
    column_config = column_config or {}
              
    # Get segment columns
    if type == "segment":
        for k, v in properties["segments"].items():
            column_def = {
                "field": v,
                "headerName": k,
                "tooltip": tooltip_headers[v] if tooltip_headers and v in tooltip_headers else tooltip_headers["default"],
                "sortable": True,
                "filter": True,
                "resizable": True,
                "flex": 1,
            }
            # Apply custom configuration if exists
            if v in column_config:
                column_def.update(column_config[v])
            column_defs.append(column_def)
        
        weight_column = {
            "field": "weight",
            "headerName": "Weight",
            "tooltip": tooltip_headers["weight"] if tooltip_headers and "weight" in tooltip_headers else tooltip_headers["default"],
            "sortable": True,
            "filter": True,
            "resizable": True,
            "flex": 1,
        }
        # Apply custom configuration if exists
        if "weight" in column_config:
            weight_column.update(column_config["weight"])
        column_defs.append(weight_column)
    elif type == "variable":
        variable_column = {
            "field": "variable",
            "headerName": "Variable",
            "tooltip": tooltip_headers["variable"] if tooltip_headers and "variable" in tooltip_headers else tooltip_headers["default"],
            "sortable": True,
            "filter": True,
        }
        # Apply custom configuration if exists
        if "variable" in column_config:
            variable_column.update(column_config["variable"])
        column_defs.append(variable_column)
        
        kl_column = {
            "field": "kl_divergence",
            "headerName": "KL Divergence",
            "tooltip": tooltip_headers["kl_divergence"] if tooltip_headers and "kl_divergence" in tooltip_headers else tooltip_headers["default"],
            "sortable": True,
            "filter": True,
            "resizable": True,
            "flex": 1,
        }
        # Apply custom configuration if exists
        if "kl_divergence" in column_config:
            kl_column.update(column_config["kl_divergence"])
        column_defs.append(kl_column)
    
    return column_defs






