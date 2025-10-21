from dash import set_props, html
import dash_design_kit as ddk
from plotly import graph_objects as go


# Custom Error Classes
class TM1PlotError(Exception):
    """Base class for plot-related errors"""

    pass


class TM2PlotError(Exception):
    """Base class for plot-related errors"""
    pass


class HistogramError(Exception):
    """Base class for histogram-related errors"""

    pass


class GridError(Exception):
    """Base class for grid-related errors"""

    pass


class PredictorTableError(Exception):
    """Base class for Predictor-table-related errors"""

    pass

class CalloutError(Exception):
    """Base class for plot-related errors"""
    pass



class DataSourceError(Exception):
    """Raised when no data is available for plotting"""

    pass


def create_empty_plot():
    """Creates an empty plotly figure"""
    empty_fig = go.Figure()
    empty_fig.update_layout(
        title="Oops! An error occurred while populating the figure.",
        xaxis_title="",
        yaxis_title="",
    )
    return empty_fig


def create_error_div():
    """ "Creates div with empty grid error"""
    return html.Div(["Oops! An error occured while populating the bubbler grid."])

def create_error_info_bar():
    """ "Creates div with empty grid error"""
    return ddk.Card(html.Div(["Oops! An error occured while fetching/calculating the callout metrics."]),className="content-center")


def custom_error_handler(err):
    """Unified error handler that handles different types of errors"""

    # Base notification settings
    notification_config = {
        "title": "Error",
        "type": "warn",
        "timeout": 20000,
        "user_dismiss": True,
    }

    # Handle different types of errors
    if isinstance(err, TM1PlotError):
        notification_config["title"] = "Plot Error"
        # Update both plots at once
        set_props({"type": "tm1-figs", "index": "tm1"}, {"figure": create_empty_plot()})

    elif isinstance(err, TM2PlotError):
        notification_config["title"] = "Plot Error"
        # Update both plots at once
        set_props(
            {"type": "actual-fig", "index": "tm2"}, {"figure": create_empty_plot()}
        )

    elif isinstance(err, GridError):
        notification_config["title"] = "Bubbler Error"
        set_props("table-container", {"children": create_error_div()})

    elif isinstance(err, HistogramError):
        notification_config["title"] = "Histogram Error"
        set_props(
            {"type": "kl-histogram", "index": "tm5"}, {"figure": create_empty_plot()}
        )

    elif isinstance(err, PredictorTableError):
        notification_config["title"] = "Predictor Table Error"
        set_props("kl-divergence-fig", {"figure": create_empty_plot()})
        
    elif isinstance(err, CalloutError):
        notification_config["title"] = "Callout Error"
        set_props("info-bar", {"children": create_error_info_bar()})
 
    else:
        pass
        # Generic error handling
        # Update both plots
        # set_props("control-ribbon", {"children": create_error_div()})

    # Create and show notification
    new_notification = ddk.Notification(children=[str(err)], **notification_config)
    set_props("notification-container", {"children": new_notification})
