from dash import Dash, _dash_renderer
from dash import dcc, html

from utils.catalog_initializer import catalog_initializer
from kyros_plotly_common.logger import dash_logger
from kyros_plotly_common.utils.ui import create_deletion_modal, create_store
from kyros_plotly_common.layout.header import create_header
from kyros_plotly_common.layout.sidebar import create_sidebar
from kyros_plotly_common.layout.app_theme import default_light_theme
from pages.mixshift import register_mixshift_callbacks
from utils.exception_handlers import custom_error_handler

import dash_bootstrap_components as dbc
import dash_design_kit as ddk
import dash_mantine_components as dmc

from kyros_plotly_common.core.cache import cache
import os

from pages.common import register_common_callbacks

from utils.components import (
    create_store_components,
    create_welcoming_blog,
    create_bubbler,
    create_control_items_card,
)

_dash_renderer._set_react_version("18.2.0")

app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    prevent_initial_callbacks="initial_duplicate",
    external_stylesheets=[dbc.themes.BOOTSTRAP, dmc.styles.ALL],
    on_error=custom_error_handler,
)

# Production server configuration
server = app.server  # expose server variable for Procfile

# set redis as cache server
cache.init_app(
    server,
    config={
        "CACHE_TYPE": "RedisCache",
        "CACHE_REDIS_URL": os.environ.get(
            "REDIS_URL", "redis://127.0.0.1:6379"
        ),  # Redis URL
        "CACHE_DEFAULT_TIMEOUT": 3 * 60 * 60,  # Default timeout in seconds (3h)
    },
)

# Clear the cache
# cache.clear()

# initialize the catalog
try:
    catalog_initializer.initialize_catalog()
except Exception as e:
    dash_logger.warning(f"Warning: Catalog initialization failed: {e}\n\nThe application will start with an empty catalog. You can refresh the catalog later.")


app.layout = dmc.MantineProvider(
    [
        ddk.App(
            theme=default_light_theme,
            children=[
                create_deletion_modal(),
                html.Div(id="notification-container"),
                create_store("drop-table-id"),
                create_store("table-current-view", data="tabular-view"),
                create_store("page-load-trigger", data="trigger"),
                html.Div(id="schema-restart-notification"),
                create_store_components(),
                create_header(app, tab_labels_values=[("MixShift", "mixshift", False)]),
                ddk.Row(
                    id="main-row",
                    style={"margin-bottom": 0},
                    children=[
                        create_sidebar(),
                        create_welcoming_blog(app),
                        ddk.Block(
                            id="main-skin",
                            style={"display": "none"},
                            width=96,
                            children=[
                                ddk.Row(
                                    id="mixshift-control-ribbon",
                                    style={"height": "14vh"},
                                    children=[create_control_items_card()],
                                ),
                                ddk.Row(
                                    id="main-group",
                                    style={"height": "calc(79vh - 15px)"},
                                    children=[
                                                ddk.Block(
                                                    style={"height": "100%"},
                                                    width=17,
                                                    children=[
                                                        # Segment Bubbler Card
                                                        create_bubbler("Segment Bubbler", "segment")
                                                    ]
                                                ),
                                                ddk.Block(
                                                    style={"height": "100%"},
                                                    width=17,
                                                    children=[
                                                        # Variable Bubbler Card
                                                        create_bubbler("Variable Bubbler", "variable")
                                                    ]
                                                ),
                                                ddk.Block(
                                                    id="right-panel",
                                                    width=66,
                                                    style={"height": "100%"},
                                                    children=[
                                                        ddk.Card(
                                                            style={"height": "100%"},
                                                            children=[
                                                                ddk.CardHeader(
                                                                    id="mixshift-visualization-header",
                                                                    title="Distribution Comparison",
                                                                    fullscreen=True,
                                                                    style={"height": "35px"}
                                                                ),
                                                                html.Div(
                                                                    id="mixshift-visualization-container",
                                                                    style={"height": "calc(100% - 35px)"},
                                                                    children=[
                                                                        dcc.Loading(
                                                                            parent_style={"height": "100%"},
                                                                            children=[
                                                                                ddk.Graph(
                                                                                    id="mixshift-graph",
                                                                                    style={"height": "100%"},
                                                                                ),
                                                                            ],
                                                                        )
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )


# register callbacks from respective scripts
register_common_callbacks(app)
# --------------------------------------- #

# Import and register MixShift callbacks
register_mixshift_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True)  # debug = True