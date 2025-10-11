from dash import set_props, html
from kyros_plotly_common.alerts.alert import create_alert
from kyros_plotly_common.utils.ui import create_empty_plot
from kyros_plotly_common.utils.ui import create_error_div
from kyros_plotly_common.core.errors import PlotError, BubblerError


def custom_error_handler(err):
    """Unified error handler that handles different types of errors"""

    # Default alert settings
    alert_color = "danger"
    alert_title = "Error"
    duration = 20000
    
    # Handle different types of errors
    if isinstance(err, PlotError):
        alert_title = "Plot Error"
        # Update both plots at once
        set_props("mixshift-graph", {"figure": create_empty_plot()})

    elif isinstance(err, BubblerError):
        alert_title = f"{err.bubbler_type.capitalize()} Bubbler Error"
        set_props(f"{err.bubbler_type}-table-container", {"children": create_error_div()})

    # Extract the actual error message from the tuple
    if isinstance(err, tuple):
        err_message = err[0]  # Get just the first part of the tuple
    else:
        err_message = str(err)

        
    # Create and show alert
    alert = create_alert(
        title=alert_title,
        message=err_message,
        color=alert_color,
        dismissable=True,
        duration=duration,
        position="top-right"
    )
    
    set_props("notification-container", {"children": alert})
