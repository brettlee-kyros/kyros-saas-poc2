from dash import dcc, html
import dash_design_kit as ddk
import dash_bootstrap_components as dbc

from kyros_plotly_common.layout.datagrid import create_grid, GridConfig
from kyros_plotly_common.utils.ui import create_store
from utils.helper_functions import create_bubbler_signal_children
from kyros_plotly_common.utils.ui import get_icon


def get_guide_text():
    return open("MIXSHIFT_USER_GUIDE.md").read()

def create_store_components():
    """
    Creates a div containing store components for the MixShift dashboard.
    These stores are used to maintain state across callbacks.

    Returns:
        html.Div: A Dash HTML Div component containing Store components.
    """
    stores = [
        # Dataset and view stores
        create_store("db-store"),  # Stores the selected dataset name
        
        # Data stores
        create_store("segment-data-store"),  # Stores segment bubbler data
        create_store("variable-data-store"),  # Stores variable bubbler data
        create_store("distribution-data-store"),  # Stores distribution comparison data
        create_store("selected-variables-store", data=[]),  # Stores selected variables across date changes
    ]

    return html.Div(stores)


def create_welcoming_blog(app):
    """crease the welcoming blog with a huge kyros Logo"""

    return ddk.Block(
        id="welcoming-skin",
        style={"display": "block"},
        width=96,
        children=[
            ddk.Row(
                className="welcoming-row",
                children=[
                    html.Img(
                        className="welcoming-logo",
                        src=app.get_relative_path("/assets/logos/KYROS-logo.png"),
                    )
                ],
            )
        ],
    )

def create_bubbler(title, type):
    """
    Creates a bubbler card with a header and a body.
    
    Args:
        title (str): The title of the bubbler card.
        type (str): The type of bubbler card. "segment" or "variable"

    Returns:
        ddk.Card: A bubbler card.
    """
    if type not in ["segment", "variable"]:
        raise ValueError("Type must be either 'segment' or 'variable'")

    return ddk.Card(
        [
            html.Div(
                [
                    ddk.CardHeader(
                        title=title,
                        children=[
                            html.Div(
                                [
                                    html.Div(
                                        id=f"{type}-selector-signal",
                                        style={"margin-left": "auto"},
                                        children=[
                                            create_bubbler_signal_children([], type, total_count=None)
                                        ]
                                    ),
                                    html.Div(
                                        children=[
                                            dbc.Button(
                                                id=f"{type}-refresh-button",
                                                children=get_icon("flowbite:refresh-outline", 15),
                                                outline=True,
                                                color="primary",
                                                className="me-1 py-0 px-1 custom-xs-button",
                                                style={
                                                    "font-size": "1rem",
                                                    "background-color": "transparent",
                                                },
                                                n_clicks=0,
                                            )
                                        ], style={"margin-left": "auto"},
                                    ),
                                    dbc.Button(
                                        id=f"{type}-download-csv-button",
                                        children=get_icon(
                                            "flowbite:download-outline", 15
                                        ),
                                        title="Download Table",
                                        outline=True,
                                        color="primary",
                                        className="me-1 py-0 px-1 custom-xs-button",
                                        style={
                                            "font-size": "1rem",
                                            "background-color": "transparent",
                                        },
                                        n_clicks=0,
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "align-items": "center",
                                    "width": "100%",
                                    "height": "100%",
                                },
                            ),
                        ],
                        style={
                            "height": "35px",
                            "display": "flex",
                            "alignItems": "center",
                            "padding": "0 10px",
                            "width": "100%",
                            "backgroundColor": "transparent",
                            "borderBottom": "1px solid #e9ecef",
                        },
                    ),
                ],
                style={
                    "position": "relative",
                    "z-index": "100",
                    "width": "100%",
                },
            ),
            # Grid container with synchronized scrolling
        dcc.Loading(
            parent_style={"height": "100%"},
            children=ddk.Block(
                id=f"{type}-table-container",
                style={
                    "height": "calc(100% - 30px)",              # Fixed height for AG Grid
                    "width": "100%",
                },
                children=[
                    create_grid(GridConfig(
                        id=f"{type}-bubbler",
                        column_defs=[],
                        row_data=[],
                    ))
                ]
            )
        )
    ],
    style={
        "height": "100%",              # Fixed height to contain AG Grid
        "display": "flex",
        "flex-direction": "column",
        "width": "100%"
    }
)


########## Define control items ############
# Weight selector (repurposed from target_dropdown)
weight_dropdown = ddk.ControlItem(
    id="weight-dd-control",
    children=dcc.Dropdown(
        id="weight-dd",
        multi=False,
        clearable=False,
        placeholder="Select Weight",
        style={"width": "100%"},
        # Accessibility improvements
        searchable=True
    ),
    
    label="Weight",
    label_hover_text="Select the weight variable to use for distribution calculations",
    width=15,
    style={"marginRight": 5, "marginLeft": 5},
)

# Date selectors (repurposed from date_picker)
date1_dropdown = ddk.ControlItem(
    id="date1-dd-control",
    children=dcc.Dropdown(
        id="date1-dd",
        multi=False,
        clearable=False,
        placeholder="Select Date 1",
        # Accessibility improvements
        searchable=True,
        
    ),
    label="Date 1",
    label_hover_text="Select the first date to compare distributions",
    width=15,
    style={"marginRight": 5, "marginLeft": 5},
)

date2_dropdown = ddk.ControlItem(
    id="date2-dd-control",
    children=dcc.Dropdown(
        id="date2-dd",
        multi=False,
        clearable=False,
        placeholder="Select Date 2",
        # Accessibility improvements
        searchable=True,
        
    ),
    label="Date 2",
    label_hover_text="Select the second date to compare distributions",
    width=15,
    style={"marginRight": 5, "marginLeft": 5},
)

# View toggle (Histogram/Mix) - Changed to a single switch
view_toggle = ddk.ControlItem(
    id="view-toggle-control",
    children=
    dbc.RadioItems(
        id="view-toggle",
        options=[
            {"label": "Histogram View", "value": False},
            {"label": "Mix View", "value": True},
        ],
        value=False,  # False = Histogram, True = Mix View
        inline=False,
        className="custom-radio-items"
    ),
    label="Chart View",
    label_hover_text="Toggle between Histogram and Mix View visualizations",
    width=15,
    style={"marginRight": 5, "marginLeft": 5},
)

# Info button with modal
info_div = ddk.ControlItem(
    id="mixshift-info-control", 
    children=html.Div(
        [
            dbc.Button(
                children=[get_icon("bx:info-circle", 18)],
                outline=False,
                color="light",
                id="mixshift-modal-button",
                title="How to Use MixShift",
                className="me-1 py-0 px-1 custom-xs-button",
                style={"font-size": "1rem", "background-color": "transparent"},
                n_clicks=0,
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("How to Use MixShift")),
                    dbc.ModalBody(dcc.Markdown(get_guide_text())),
                ],
                id="mixshift-modal-lg",
                size="lg",
                is_open=False,
            ),
        ]
    ), 
    label="Info",
    label_hover_text="Learn how to use the MixShift dashboard",
    width=5,
    style={"display": "block"}
)

# Use these items in control_items
control_items = [
    date1_dropdown,
    date2_dropdown,
    weight_dropdown,
    view_toggle,
    info_div,
]

def create_control_items_card():
    return ddk.ControlCard(
        id="control-row",
        orientation="horizontal",
        children=control_items,
        label_style={
            "textTransform": "capitalize",
            "color": "grey",
        },
        padding=8,
        margin=3
    )