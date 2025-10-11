"""
Example of how to use the modular bar renderer in other dashboards
"""
import pandas as pd
import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

# Import the modular components
from kyros_plotly_common.layout.datagrid import create_grid, GridConfig
from kyros_plotly_common.utils.ui import get_bar_renderer_config

# Sample data
def generate_sample_data(rows=10):
    """Generate sample data for the example"""
    import random
    
    data = []
    for i in range(rows):
        data.append({
            "id": i,
            "name": f"Item {i}",
            "value": round(random.uniform(0, 100), 2),
            "score": round(random.uniform(-1, 1), 4),
            "count": random.randint(0, 1000),
        })
    return data

# Example showing how to create a grid with bar renderers for different columns
def create_example_grid(grid_id="example-grid"):
    """Create an example grid with bar renderers"""
    
    # Generate sample data
    data = generate_sample_data(15)
    
    # Create column definitions manually
    column_defs = [
        {
            "field": "id",
            "headerName": "ID",
            "sortable": True,
            "filter": True,
        },
        {
            "field": "name",
            "headerName": "Name",
            "sortable": True,
            "filter": True,
            "flex": 1,
        }
    ]
    
    # Configure bar renderers for the value, score and count columns
    value_config = get_bar_renderer_config("value", max_value="auto", is_centered=False, color="#1E88E5")
    score_config = get_bar_renderer_config("score", max_value="auto", is_centered=True, color="#F44336")
    count_config = get_bar_renderer_config("count", max_value="auto", is_centered=False, color="#4CAF50")
    
    # Add the columns with bar renderers
    column_defs.append({
        "field": "value",
        "headerName": "Value",
        "sortable": True,
        "filter": True,
        **value_config["value"]
    })
    
    column_defs.append({
        "field": "score",
        "headerName": "Score",
        "sortable": True,
        "filter": True,
        **score_config["score"]
    })
    
    column_defs.append({
        "field": "count",
        "headerName": "Count",
        "sortable": True,
        "filter": True,
        **count_config["count"]
    })
    
    # Create the grid using GridConfig
    grid_config = GridConfig(
        id=grid_id,
        column_defs=column_defs,
        row_data=data,
        multi_select=False,
        selected_rows=[]
    )
    return create_grid(grid_config)

# Example Dash app
def create_example_app():
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    app.layout = dbc.Container([
        html.H1("Bar Renderer Example"),
        html.P("This example demonstrates the modular bar renderer component."),
        html.Hr(),
        html.Div(id="grid-container", children=create_example_grid())
    ])
    
    return app

# Run the example app
if __name__ == "__main__":
    app = create_example_app()
    app.run_server(debug=True) 