from collections import defaultdict
from dash import html
import dash_bootstrap_components as dbc

from kyros_plotly_common.logger import dash_logger
from kyros_plotly_common.utils.ui import get_icon
from kyros_plotly_common.utils.schema import parse_schema_properties, parse_schema_properties
from kyros_plotly_common.utils.date import interpolate_month_auto, interpolate_month_ends

def create_bubbler_signal_children(selected_rows, type, total_count=None):
    """
    Create the signal icon and tooltip for bubblers.
    
    Args:
        selected_rows (list): List of selected rows from AG Grid
        type (str): Either "segment" or "variable"
        total_count (int, optional): Total count of available rows for checking if all are selected
    
    Returns:
        html.Div: Signal icon with tooltip based on the number of selected segments or variables
    """
    if not selected_rows:
        # yellow W if variable, n if segment
        signal = {
            "icon": "mynaui:letter-w-square" if type == "variable" else "mynaui:letter-a-square",
            "color": "#FFA500" if type == "variable" else "blue",
            "tooltip": f"No {type} selected!" if type == "variable" else f"All {type}s selected!"
        }
    elif total_count is not None and len(selected_rows) == total_count:
        # All items are selected
        signal = {
            "icon": "mynaui:letter-a-square",
            "color": "blue",
            "tooltip": f"All {type}s selected",
        }
    elif len(selected_rows) == 1:
        if type == "segment":
            segment_values = selected_rows[0]["segment_values"]
            first_value = next(iter(segment_values.values()))
            tooltip = str(first_value)
        else:  # variable
            variable = selected_rows[0]["variable"]
            kl_divergence = selected_rows[0]["kl_divergence"]
            kl_str = f"{kl_divergence:.2f}" if isinstance(kl_divergence, (int, float)) else str(kl_divergence)
            tooltip = f"{variable} (KL: {kl_str})"
            
        signal = {
            "icon": "mynaui:letter-s-square",
            "color": "green",
            "tooltip": tooltip,
        }
    else:
        # Multiple selections (only possible for segments)
        tooltips = []
        for row in selected_rows:
            if type == "segment":
                segment_values = row["segment_values"]
                first_value = next(iter(segment_values.values()))
                tooltips.append(str(first_value))
            
        signal = {
            "icon": "mynaui:letter-m-square",
            "color": "red",
            "tooltip": ", ".join(tooltips),
        }

    return html.Div(
        id=f"{type}-selector-signal-icon",
        children=[
            get_icon(signal["icon"], 30, color=signal["color"]),
            dbc.Tooltip(
                signal["tooltip"],
                id=f"{type}-tooltip",
                placement="left",
                target=f"{type}-selector-signal-icon",
                trigger="hover focus",
            )
        ]
    )