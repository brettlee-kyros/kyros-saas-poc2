from dash import dcc, html
import dash_design_kit as ddk
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from kyros_plotly_common.utils.ui import get_icon

def create_store(store_type, index, **kwargs):
    """
    Helper function to create a dcc.Store component.

    Args:
        store_type (str): The type of the store.
        index (str): The index of the store.
        **kwargs: Additional keyword arguments for the dcc.Store component.

    Returns:
        dcc.Store: A Dash Store component.
    """
    return dcc.Store(id={"type": store_type, "index": index}, **kwargs)


def create_store_components():
    """
    Creates a div containing multiple dcc.Store components for different data types and indices.

    Returns:
        html.Div: A Dash HTML Div component containing multiple Store components.
    """
    stores = [
        create_store("date-range-store", "common"),
        create_store("last-selected-kl", "tm5"),
        create_store("selected-kl-data", "tm5"),
        create_store("kl-data-store", "tm5"),
        create_store("db-store", "common"),
        create_store("cluster-filter-store", "common"),
        create_store("snapshot-filter-store", "common"),
        create_store("all-cluster-values-store", "common"),
        create_store("actual-data-store", "tm1"),
        create_store("expected-data-store", "tm1"),
        create_store("fetched-data-store", "tm1"),
        create_store("dev-fetched-data-store","tm1"),
        create_store("selected-points","common"),
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


def create_alert_block():
    """creata a block that becomes visible when no target selector is left blank."""

    alert_note = "Oops! It looks like you have not selected any target values. Please choose at least one to proceed."

    return ddk.Block(
        id="main-graphs-alert",
        width=75,
        style={"height": "100%", "display": "none"},
        children=[
            ddk.Card(
                style={"height": "100%", "width": "100%"},
                children=[
                    dbc.Alert(id="target-alert", children=alert_note, color="primary")
                ],
            )
        ],
    )


def create_bubbler():
    return ddk.Card(
        [
            # Card header
            html.Div(
                [
                    ddk.CardHeader(
                        title="Cluster Importance",
                        children=[
                            html.Div(
                                [
                                    html.Div(
                                        id="selector-signal",
                                        style={"margin-right": "0.5rem"},
                                    ),
                                    html.Div(
                                        id="hierarchy-signal",
                                        style={"margin-right": "0.5rem"},
                                    ),
                                    dbc.Button(
                                        id="download-csv-button",
                                        children=get_icon(
                                            "flowbite:download-outline", 18
                                        ),
                                        outline=True,
                                        color="primary",
                                        title="Download Table",
                                        className="btn-extra-small",
                                        style={"margin-left": "0.5rem"},
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
                            "height": "40px",
                            "display": "flex",
                            "alignItems": "center",
                            "padding": "0 10px",
                            "width": "100%",
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
            html.Div(
                [
                    dcc.Loading(
                        children=html.Div(
                            id="table-container",
                            style={
                                "height": "100%",
                                "white-space": "nowrap",
                                "min-width": "100%",
                                "width": "100%",
                            },
                        )
                    )
                ],
                style={
                    "flex": "1 1 auto",  # Allow it to grow and fill the space
                    "width": "100%",
                    "position": "relative",
                    "overflow": "hidden",  # Prevent double scrollbars
                    "marginTop": "0.75rem",
                },
            ),
        ],
        style={
            "height": "100%",
            "display": "flex",
            "flexDirection": "column",
            "width": "100%",
            "position": "relative",
            "overflow": "hidden",
        },
    )


########## Define control items ############
mask_radio = ddk.ControlItem(
    id="mask-radio-control",
    children=dcc.RadioItems(
        id="mask-radio",
        options=[
            {"label": "Unmasked", "value": "Unmasked"},
            {"label": "Masked", "value": "Masked"},
        ],
        value="Unmasked",
        style={"padding": "2px"},
    ),
    label="Masking",
    width=12,
)


actual_radio = ddk.ControlItem(
    id="actual-radio-control",
    style={"display": "none"},
    children=dcc.RadioItems(
        id="actual-radio",
        options=[
            {"label": "Original", "value": "Original"},
            {"label": "Reweighted", "value": "Reweighted"},
        ],
        value="Original",
    ),
    label="Actual Type",
    width=12,
)

empty_component = ddk.ControlItem(id="empty-control", width=12)


monitoring_dropdown = ddk.ControlItem(
    id="monitoring-dd-control",
    children=dcc.Dropdown(id="monitoring-dd", multi=False, clearable=False),
    label="Monitoring Date",
    width=15,
    style={"marginRigt": 5, "marginLeft": 5},
)

target_dropdown = ddk.ControlItem(
    id="target-dd-control",
    children=dmc.MultiSelect(
        id="target-dd",
        value=[],
        data=[],
        clearable=True,
        styles={"input": {"maxHeight": "60px", "overflowY": "auto"}},
    ),
    label="Target Selector",
    style={"margin-rigt": 5, "margin-left": 5},
    width=20,
)



age_slider = ddk.ControlItem(
    id="age-slider-control",
    children=html.Div(
        [
            html.Div(
                [
                    html.Span(
                        children="Age Filter",
                        className="control--label",
                        style={"white-space": "nowrap"},
                    ),
                    html.Div(id="age-filter-text", className="date-filter-text"),
                ],
                style={"display": "flex", "align-items": "center", "gap": "5px"},
            ),
            html.Div(
                dcc.RangeSlider(
                    id="age-slider",
                    step=1,
                    tooltip={"placement": "bottom", "always_visible": False},
                )
            ),
        ]
    ),
    width="auto",
)








def create_info_component(title, tooltip_info, tooltip_target):
    return [
        f"{title}\x20",
        get_icon("bx:info-circle", 16),
        dbc.Tooltip(f"{tooltip_info}", target=f"{tooltip_target}", placement="bottom"),
    ]


tm5_tooltip_context = """

1. **Populating the KL-Divergence Figure on the Right**:

- To generate a figure, make a selection on both the **snapshotDate** and **Cluster** components located on the left side.

- Each combination of a **snapshotDate** and **Cluster/Group of Clusters** will trigger the creation of a new figure for that specific pair.

  
2. **Populating the Histogram in the Middle**:

- Once you’ve made your selection on the **KL-Divergence figure**, a **histogram** will be populated in the middle of the dashboard.

- Ensure that you interact with the **KL-Divergence figure** on the right to populate the histogram with relevant data.

"""

modal = html.Div(
    [
        dbc.Button(
            children=[get_icon("bx:info-circle", 18)],
            outline=False,
            color="light",
            id="modal-button",
            title="How to Use This Tab",
            className="me-1 py-0 px-1 custom-xs-button",
            style={"font-size": "1rem", "background-color": "transparent"},
            n_clicks=0,
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("How to Use This Tab")),
                dbc.ModalBody(dcc.Markdown(tm5_tooltip_context)),
            ],
            id="modal-lg",
            size="lg",
            is_open=False,
        ),
    ]
)


tm5_info_div = ddk.ControlItem(
    id="tm5-info-control", children=modal, style={"display": "none"}
)

settings_modal = html.Div(
    [
        dbc.Button(
            # A plot icon
            children=[get_icon("mdi:chart-box-outline", 18)],
            outline=False,
            color="light",
            id="stats-settings-button",
            title="Stats Settings",
            className="me-1 py-0 px-1 custom-xs-button",
            style={"font-size": "1rem", "background-color": "transparent"},
            n_clicks=0,
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Stats Settings")),
                dbc.ModalBody([
                    html.Div([
                        html.Label("Confidence Level (%)", className="mb-2"),
                        dcc.Input(
                            id="conf_level_input",
                            type="number",
                            min=50,
                            max=100,
                            step=1,
                            value=90,
                            debounce=1,
                            placeholder="Enter confidence level",
                            className="form-control",
                        ),
                    ], className="mb-3"),
                    html.Div([
                        html.Label("Target Correlation", className="mb-2"),
                        dcc.Input(
                            id="target-correlation-input",
                            type="number",
                            min=-1,
                            max=1,
                            step=0.01,
                            value=0.25,
                            debounce=1,
                            className="form-control",
                        ),
                    ], className="mb-3"),
                    html.Div([
                        html.Label("Cluster Correlation", className="mb-2"),
                        dcc.Input(
                            id="cluster-correlation-input",
                            type="number",
                            min=-1,
                            max=1,
                            step=0.01,
                            value=0.25,
                            debounce=1,
                            className="form-control",
                        ),
                    ]),
                    html.Div(id="stats-settings-feedback", style={"margin-top": "1rem"}),
                ])
            ],
            id="stats-settings-modal",
            size="sm",
            is_open=False,
        ),
    ]
)


currentdate_info_box_ = ddk.ControlItem(
    id="currentdate-info-box-control",
    className="current-date-box",
    children=html.Div(
        id="currentdate-info-box",
    ),
    width=10,
)

stats_settings_div = ddk.ControlItem(
    id="stats-settings-control",
    # Center the modal
    style={"display": "flex", "justify-content": "center"},
    children=settings_modal,
    width=2,
)

control_items = [
    empty_component,
    actual_radio,
    mask_radio,
    monitoring_dropdown,
    target_dropdown,
    age_slider,
    currentdate_info_box_,
    tm5_info_div,
    stats_settings_div,
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
        padding=10,
    )


"""def create_control_items_card():
    return ddk.ControlCard(
        orientation="horizontal",
        children=[
            ddk.Block(
                id="control-row",
                children=control_items,
                style={"display": "flex", "flex-wrap": "wrap", "gap": "10px"},
            )
        ],
    )

"""


def create_kl_bubbler():
    return ddk.Card(
        [
            html.Div(
                [
                    ddk.CardHeader(
                        title="Predictors by KL-Divergence",
                        children=[
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            dbc.Button(
                                                children=get_icon(
                                                    "flat-color-icons:generic-sorting-desc",
                                                    18,
                                                ),
                                                outline=False,
                                                color="light",
                                                id="kl-bubbler-sort-button",
                                                title="Sort",
                                                className="me-1 py-0 px-1 custom-xs-button",
                                                style={
                                                    "font-size": "1rem",
                                                    "background-color": "transparent",
                                                },
                                            ),
                                        ],
                                        style={"margin-left": "auto"},
                                    )
                                ],
                                style={
                                    "display": "flex",
                                    "align-items": "center",
                                    "width": "calc(100% - 10px)",
                                    "height": "100%",
                                },
                            ),
                        ],
                        style={
                            "height": "100%",  # Ensure CardHeader uses full height
                            "display": "flex",
                            "alignItems": "center",
                        },
                    ),
                ],
                style={
                    "position": "sticky",
                    "hight": "40px",
                    "z-index": "100",
                    "width": "100%",
                },
            ),
            html.Div(
                [
                    dcc.Loading(
                        ddk.Graph(
                            id="kl-divergence-fig",
                            style={"height": "350vh"},
                            config={
                                "displaylogo": False,
                            },
                        )
                    )
                ],
                style={
                    "overflow-y": "auto",
                    "height": "calc(100% - 50px)",  # Adjusted based on new header height
                    "width": "100%",
                },
            ),
        ],
        style={
            "height": "100%",  # Use 100% height instead of calc
            "display": "flex",
            "flexDirection": "column",
            "width": "calc(100% - 10px)",
        },
    )


def create_collapse_structure(df):
    if df.empty:
        return dbc.Collapse(
            ["No manual dimensions found!"],
            id="manual-dims-collapse",
            className="custom-collapse",
            is_open=False,
        )

    columns = df.columns[1:]  # get rid of the first col, which is cluster_collapse!

    # Create accordion items
    accordion_items = []

    # Create an accordion item for each column
    for idx, column in enumerate(columns):
        unique_values = sorted(df[column].unique())

        # Create options for checklist
        options = [
            {"label": f"{str(dim)}", "value": f"{str(dim)}"} for dim in unique_values
        ]

        # Define the title with or without the button
        if idx == 0:
            # Create a small square button
            small_button = dbc.Button(
                children=get_icon("iconamoon:restart", 18),
                size="sm",
                color="subtle",
                outline=True,
                style={
                    "width": "24px",
                    "height": "24px",
                    "padding": "0.1rem",
                    "marginRight": "0.5rem",
                    "lineHeight": "1",
                    "textAlign": "center",
                    "borderRadius": "4px",
                },
                id="reset-mandim-button",
                n_clicks=0,
            )

            # Combine the column title and the button using a flex container
            title_content = html.Div(
                [
                    html.Span(
                        column, style={"flex": "1"}
                    ),  # Title takes up remaining space
                    small_button,  # Button on the right
                ],
                className="d-flex align-items-center",
                style={
                    "width": "100%",
                    "backgroundColor": "transparent",
                },
            )
        else:
            title_content = column

        # Create accordion item
        accordion_item = dbc.AccordionItem(
            dbc.Checklist(
                options=options,
                value=[],
                id={"type": "man-checklist", "index": idx},
                className="custom-checklist",
            ),
            title=title_content,
            className="custom-accordion-item",
            style={"border-radius": 0},
        )

        accordion_items.append(accordion_item)

    # Create the complete collapse structure
    collapse = dbc.Collapse(
        dbc.Card(
            dbc.CardBody(
                [
                    dbc.Accordion(
                        accordion_items,
                        start_collapsed=True,
                        always_open=True,
                        className="custom-accordion",
                    )
                ],
                style={
                    "padding": "0.25rem",
                    "backgroundColor": "transparent",
                    "border-radius": 0,
                },
            ),
            style={
                "width": "100%",
                "backgroundColor": "transparent",
                "border": "none",
                "boxShadow": "none",
                "border-radius": 0,
            },
        ),
        id="manual-dims-collapse",
        className="custom-collapse",
        is_open=False,
    )
    return collapse



###### info-boxes -- callouts


observed_rr_info_box = ddk.Card(
        width=20,
        className="info-card",
        children=[
            html.Div([
                dcc.Loading([
                html.Div([
                html.Div(id= "observed-rr-val", className="dynamic-info-content"), 
                html.Div('Observed Redemption Rate', className="static-info-content") 
            ], )
            ])
            
                
            ],className="content-center" )
            
        ],
    )


predicted_rr_info_box = ddk.Card(
        width=20,
        className="info-card",
        children=[
            html.Div([dcc.Loading([
                html.Div([
                html.Div(id= "predicted-rr-val", className="dynamic-info-content"), 
                html.Div('Predicted Redemption Rate', className="static-info-content") 
            ])
            ])],className="content-center")
            
            
            ]
    )

residual_rr_info_box = ddk.Card(
    width=20,
    className="info-card",
    children=[
        html.Div([
            dcc.Loading([
                html.Div([
                    html.Div(id="residual-rr-val", className="dynamic-info-content"),
                    html.Div('Observed - Predicted', className="static-info-content", style={
                        'position': 'relative'  # Only this element gets relative positioningxw
                    }),
                    html.Div(id='significant-text-div', style={
                        'color': 'red',
                        'fontWeight': 'bold',
                        'fontSize': '0.6em',
                        'position': 'absolute',
                        'top': '100%',
                        'left': '50%',
                        'transform': 'translateX(-50%)',
                        'whiteSpace': 'nowrap'
                    })
                ])
            ])
        ], className="content-center")
    ]
)

exposure_info_box = ddk.Card(
        width=20,
        className="info-card",
        children=[
            html.Div([
                dcc.Loading([
            html.Div([
                html.Div(id = "selected-points-val", className="dynamic-info-content"), 
                html.Div('Selected Points', className="static-info-content") 
            ])])
                
            ],className="content-center")
            
            
            ]
    )

fimpact_info_box = ddk.Card(
        width=20,
        className="info-card",
        children=[
            html.Div([
                dcc.Loading([
                html.Div([
                    html.Div(id = "financial-impact-val", className="dynamic-info-content"), 
                    html.Div('Liability Impact', className="static-info-content") 
                ])
            ])
            ],className="content-center")
            ], 
    )



info_bar = ddk.Row(id ='info-bar', children = [observed_rr_info_box, predicted_rr_info_box, residual_rr_info_box, exposure_info_box, fimpact_info_box],
            style={
                'height': '100%', 
                'display': 'flex',
                'justifyContent': 'space-between',
                'width': '100%',
                'alignItems': 'flex-start',  # Align items at the top
                'position': 'relative'  # For absolute positioning context
            })
