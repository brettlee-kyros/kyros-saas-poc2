from dash import Dash, _dash_renderer
from dash import dcc, html

from utils.catalog_initializer import catalog_initializer
from utils.components import info_bar

from utils.exception_handlers import custom_error_handler

import dash_bootstrap_components as dbc
import dash_design_kit as ddk
import dash_mantine_components as dmc

from kyros_plotly_common.core.cache import cache
import os

from pages.common import register_common_callbacks
from pages.tm2 import register_tm2_callbacks
from pages.tm5 import register_tm5_callbacks

from kyros_plotly_common.layout.header import create_header
from kyros_plotly_common.layout.sidebar import create_sidebar, create_offcanvas
from kyros_plotly_common.utils.ui import create_deletion_modal
from kyros_plotly_common.layout.app_theme import default_light_theme
from utils.components import (
    create_store_components,
    create_welcoming_blog,
    create_alert_block,
    create_bubbler,
    create_kl_bubbler,
    create_control_items_card,
)
from kyros_plotly_common.logger.dash_logger import dash_logger

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

# initialize the catalog drawer/blade
try:
    catalog_initializer.initialize_catalog()
except Exception as e:
    dash_logger.warning(
        f"Warning: Catalog initialization failed: {e}\n\nThe application will start with an empty catalog. You can refresh the catalog later."
    )

create_offcanvas()

app.layout = dmc.MantineProvider(
    [
        ddk.App(
            theme=default_light_theme,
            children=[
                create_deletion_modal(),
                html.Div(id="notification-container"),
                dcc.Store(id="rr-values"),
                dcc.Store(id="selected-points"),
                dcc.Store(id="drop-table-id"),
                dcc.Store(id="conf-level-store", data=0.9),
                dcc.Store(id="target-correlation-store", data=0.25),
                dcc.Store(id="cluster-correlation-store", data=0.25),
                dcc.Store(id="header-button-store"),
                dcc.Store(id="table-current-view", data="tabular-view"),
                dcc.Store(id="refresh-button-store"),
                dcc.Store(id="page-load-trigger", data="trigger"),
                html.Div(id="schema-restart-notification"),
                create_store_components(),
                create_header(
                    app,
                    tab_labels_values=[
                        ("Performance", "performance", False),
                        ("Characteristics", "characteristics", False),
                    ],
                ),
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
                                    id="control-ribbon",
                                    children=[create_control_items_card()],
                                    style={"height": "14vh"},
                                ),
                                ddk.Row(
                                    id="main-group",
                                    style={"height": "calc(79vh - 15px)"},
                                    children=[
                                        ddk.Block(
                                            id="bubbler",
                                            width=25,
                                            style={
                                                "height": "100%"
                                            },
                                            children=[create_bubbler()],
                                        ),
                                        create_alert_block(),
                                        ddk.Block(
                                            id="main-graphs",
                                            width=75,
                                            style={"height": "100%"},
                                            children=[
                                                ddk.Row(
                                                    id="info-row",
                                                    children=[info_bar],
                                                ),
                                                ddk.Row(
                                                    id="diagnostic-graphs2",
                                                    children=[
                                                        ddk.Card(
                                                            style={
                                                                "height": "100%",
                                                                "width": "100%",
                                                            },
                                                            children=[
                                                                ddk.CardHeader(
                                                                    title="Actual vs Expected",
                                                                    fullscreen=True,
                                                                    style={
                                                                        "height": "35px",
                                                                        "padding": 0,
                                                                    },
                                                                ),
                                                                html.Div(
                                                                    style={
                                                                        "height": "calc(100% - 35px)",
                                                                        "width": "100%",
                                                                    },
                                                                    children=[
                                                                        dcc.Loading(
                                                                            parent_style={
                                                                                "height": "100%"
                                                                            },
                                                                            children=[
                                                                                ddk.Graph(
                                                                                    id={
                                                                                        "type": "actual-fig",
                                                                                        "index": "tm2",
                                                                                    },
                                                                                    config={
                                                                                        'displayModeBar': False  # Hide modeBar
                                                                                    },
                                                                                    style={
                                                                                        "height": "100%"
                                                                                    },
                                                                                ),
                                                                            ],
                                                                        )
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                    ],
                                                ),
                                                ddk.Row(
                                                    id="exposure-graph-row",
                                                    children=[
                                                        ddk.Card(
                                                            style={
                                                                "height": "100%",
                                                                "width": "70%",
                                                            },
                                                            children=[
                                                                dcc.Loading(
                                                                    parent_style={
                                                                        "height": "100%"
                                                                    },
                                                                    children=[
                                                                        ddk.Graph(
                                                                            id={
                                                                                "type": "exposure-fig",
                                                                                "index": "common",
                                                                            },
                                                                            style={
                                                                                "height": "100%"
                                                                            },
                                                                        )
                                                                    ],
                                                                )
                                                            ],
                                                        )
                                                    ],
                                                ),
                                                ddk.Row(
                                                    id="diagnostic-graphs5",
                                                    style={
                                                        "margin-bottom": "10px",
                                                        "display": "none",
                                                        "width": "100%",
                                                        "flex-wrap": "nowrap",
                                                        "overflow": "hidden",
                                                    },
                                                    children=[
                                                        ddk.Block(
                                                            style={
                                                                "height": "100%",
                                                                "width": "calc(65% - 10px)",
                                                            },
                                                            children=[
                                                                ddk.Card(
                                                                    style={
                                                                        "height": "100%",
                                                                        "width": "100%",
                                                                    },
                                                                    children=[
                                                                        ddk.CardHeader(
                                                                            id="hist-title-id",
                                                                            fullscreen=True,
                                                                            title="Histogram by Predictors for Cluster vs Aggregate",
                                                                            style={
                                                                                "height": "35px",
                                                                                "padding": 0,
                                                                            },
                                                                        ),
                                                                        html.Div(
                                                                            style={
                                                                                "height": "calc(100% - 35px)",
                                                                                "width": "100%",
                                                                            },
                                                                            children=[
                                                                                dcc.Loading(
                                                                                    parent_style={
                                                                                        "height": "100%"
                                                                                    },
                                                                                    children=[
                                                                                        ddk.Graph(
                                                                                            id={
                                                                                                "type": "kl-histogram",
                                                                                                "index": "tm5",
                                                                                            },
                                                                                            style={
                                                                                                "height": "100%"
                                                                                            },
                                                                                        )
                                                                                    ],
                                                                                )
                                                                            ],
                                                                        ),
                                                                    ],
                                                                )
                                                            ],
                                                        ),
                                                        ddk.Block(
                                                            style={
                                                                "height": "100%",
                                                                "width": "30%",
                                                            },
                                                            children=[
                                                                create_kl_bubbler()
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
    ]
)


# register callbacks from respective scripts
register_common_callbacks(app)
register_tm2_callbacks(app)
register_tm5_callbacks(app)
# --------------------------------------- #


if __name__ == "__main__":
    app.run(debug=True)  # debug = True
