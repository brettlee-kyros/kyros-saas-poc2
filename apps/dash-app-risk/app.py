"""Tenant-aware Risk Analysis Dashboard.

This Dash application provides a tenant-isolated view of Risk data.
It integrates with the FastAPI data layer to fetch tenant-filtered
data using JWT authentication.

Key features:
- JWT validation on every request
- Tenant-scoped data access via API
- Error handling for auth and data failures
- Logging for debugging and audit

Usage:
    python app.py
    # Access at http://localhost:8051 with Authorization header
"""
import sys
import dash
from dash import dcc, html, Input, Output
import logging
from flask import Flask
import plotly.graph_objs as go
import pandas as pd

# Add paths for shared_config import
sys.path.insert(0, '/app/packages/shared-config/src')

from auth_middleware import require_tenant_token, get_current_tenant_id
from data_client import DataAPIClient
from error_page import create_error_message, create_no_data_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask server
server = Flask(__name__)

# Configure Flask session for storing tenant context
# Session is used to maintain tenant_id across AJAX requests from iframe
import os
server.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
server.config['SESSION_TYPE'] = 'filesystem'
server.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Initialize Dash app with proxy-aware configuration
# For iframe embedding through reverse proxy:
# - url_base_pathname: Where browser accesses the app (through the proxy)
# - This tells Dash to generate all URLs (assets, callbacks) with this prefix
app = dash.Dash(
    __name__,
    server=server,
    url_base_pathname='/api/proxy/dash/risk-analysis/',
    suppress_callback_exceptions=True
)

# Set page title
app.title = "Risk Analysis Dashboard"

# Apply JWT validation middleware to all routes
@server.before_request
@require_tenant_token
def validate_jwt():
    """Validate JWT on every request.

    This function is executed before every request to ensure the
    client has a valid tenant-scoped JWT token.
    """
    pass


# Layout
app.layout = html.Div([
    html.Div([
        html.H1(
            "Risk Analysis Dashboard",
            style={
                'text-align': 'center',
                'color': '#d32f2f',
                'margin-bottom': '10px'
            }
        ),
        html.Div(
            id='tenant-info',
            style={
                'text-align': 'center',
                'margin-bottom': '20px',
                'color': '#666'
            }
        ),
    ]),

    # Main content area
    html.Div([
        # Risk Score Distribution
        html.Div([
            html.H3("Risk Score Distribution", style={'text-align': 'center'}),
            dcc.Graph(id='risk-distribution-graph', style={'height': '400px'}),
        ], style={'margin-bottom': '40px'}),

        # Risk by Category
        html.Div([
            html.H3("Risk by Category", style={'text-align': 'center'}),
            dcc.Graph(id='risk-category-graph', style={'height': '400px'}),
        ], style={'margin-bottom': '40px'}),

        # Risk Trends
        html.Div([
            html.H3("Risk Trends", style={'text-align': 'center'}),
            dcc.Graph(id='risk-trend-graph', style={'height': '400px'}),
        ]),
    ], style={'padding': '20px', 'max-width': '1400px', 'margin': '0 auto'}),

    # Auto-refresh interval (every 60 seconds)
    dcc.Interval(id='interval-component', interval=60000, n_intervals=0)
], style={'font-family': 'Arial, sans-serif', 'background-color': '#f5f5f5', 'min-height': '100vh'})


@app.callback(
    Output('tenant-info', 'children'),
    Input('interval-component', 'n_intervals')
)
def display_tenant_info(n):
    """Display current tenant context.

    Args:
        n: Interval trigger count (unused)

    Returns:
        html.Div: Tenant info display
    """
    tenant_id = get_current_tenant_id()
    timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

    return html.Div([
        html.P(f"Viewing risk data for tenant: {tenant_id}", style={'margin': '5px'}),
        html.P(f"Last updated: {timestamp}", style={'margin': '5px', 'font-size': '14px'})
    ])


@app.callback(
    Output('risk-distribution-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_risk_distribution_graph(n):
    """Load Risk data and render distribution histogram.

    Args:
        n: Interval trigger count (unused)

    Returns:
        dict: Plotly figure configuration
    """
    try:
        # Fetch tenant-scoped data from API
        df = DataAPIClient.fetch_dashboard_data('risk-analysis')

        if df is None:
            logger.error("Data API returned None (connection or auth error)")
            return create_error_message("Failed to load data from API. Please check logs.")

        if df.empty:
            logger.warning("No Risk data available for tenant")
            return create_no_data_message("Risk Analysis")

        # Analyze data structure and create visualization
        logger.info(f"Risk data columns: {list(df.columns)}")

        # Create histogram of first numeric column
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            col = numeric_cols[0]
            figure = {
                'data': [
                    go.Histogram(
                        x=df[col],
                        marker_color='#d32f2f',
                        nbinsx=20
                    )
                ],
                'layout': {
                    'xaxis': {'title': col},
                    'yaxis': {'title': 'Frequency'},
                    'margin': {'t': 20, 'b': 60, 'l': 60, 'r': 20}
                }
            }
        else:
            figure = create_error_message("No numeric columns found for distribution")

        logger.info(f"Rendered Risk distribution graph with {len(df)} records")
        return figure

    except Exception as e:
        logger.error(f"Error rendering Risk distribution graph: {str(e)}")
        return create_error_message(f"Error: {str(e)}")


@app.callback(
    Output('risk-category-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_risk_category_graph(n):
    """Load Risk data and render by category.

    Args:
        n: Interval trigger count (unused)

    Returns:
        dict: Plotly figure configuration
    """
    try:
        df = DataAPIClient.fetch_dashboard_data('risk-analysis')

        if df is None:
            return create_error_message("Failed to load data from API.")

        if df.empty:
            return create_no_data_message("Risk Analysis")

        # Look for category-like columns
        category_col = None
        value_col = None

        # Find suitable columns
        for col in df.columns:
            if 'category' in col.lower() or 'type' in col.lower():
                category_col = col
            if 'score' in col.lower() or 'value' in col.lower():
                value_col = col

        if category_col and value_col:
            # Group by category
            category_data = df.groupby(category_col)[value_col].mean().reset_index()
            figure = {
                'data': [
                    go.Bar(
                        x=category_data[category_col],
                        y=category_data[value_col],
                        marker_color='#d32f2f'
                    )
                ],
                'layout': {
                    'xaxis': {'title': category_col},
                    'yaxis': {'title': f'Average {value_col}'},
                    'margin': {'t': 20, 'b': 60, 'l': 60, 'r': 20},
                    'hovermode': 'closest'
                }
            }
        else:
            # Fallback: show first 10 records as bar chart
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                col = numeric_cols[0]
                figure = {
                    'data': [
                        go.Bar(
                            x=list(range(len(df.head(10)))),
                            y=df[col].head(10),
                            marker_color='#d32f2f'
                        )
                    ],
                    'layout': {
                        'xaxis': {'title': 'Record Index'},
                        'yaxis': {'title': col},
                        'margin': {'t': 20, 'b': 60, 'l': 60, 'r': 20},
                        'annotations': [{
                            'text': f'Showing sample data ({len(df)} total records)',
                            'xref': 'paper',
                            'yref': 'paper',
                            'x': 0.5,
                            'y': 1.1,
                            'showarrow': False,
                            'font': {'size': 12}
                        }]
                    }
                }
            else:
                figure = create_error_message("No suitable columns found for category view")

        return figure

    except Exception as e:
        logger.error(f"Error rendering Risk category graph: {str(e)}")
        return create_error_message(f"Error: {str(e)}")


@app.callback(
    Output('risk-trend-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_risk_trend_graph(n):
    """Load Risk data and render trends.

    Args:
        n: Interval trigger count (unused)

    Returns:
        dict: Plotly figure configuration
    """
    try:
        df = DataAPIClient.fetch_dashboard_data('risk-analysis')

        if df is None:
            return create_error_message("Failed to load data from API.")

        if df.empty:
            return create_no_data_message("Risk Analysis")

        # Look for date columns
        date_cols = df.select_dtypes(include=['datetime64']).columns
        numeric_cols = df.select_dtypes(include=['number']).columns

        if len(date_cols) > 0 and len(numeric_cols) > 0:
            date_col = date_cols[0]
            value_col = numeric_cols[0]

            # Sort by date and plot
            df_sorted = df.sort_values(by=date_col)

            figure = {
                'data': [
                    go.Scatter(
                        x=df_sorted[date_col],
                        y=df_sorted[value_col],
                        mode='lines+markers',
                        marker_color='#d32f2f',
                        line={'color': '#d32f2f'}
                    )
                ],
                'layout': {
                    'xaxis': {'title': date_col},
                    'yaxis': {'title': value_col},
                    'margin': {'t': 20, 'b': 60, 'l': 60, 'r': 20}
                }
            }
        else:
            # Fallback: show simple line plot of first numeric column
            if len(numeric_cols) > 0:
                col = numeric_cols[0]
                figure = {
                    'data': [
                        go.Scatter(
                            x=list(range(len(df))),
                            y=df[col],
                            mode='lines+markers',
                            marker_color='#d32f2f',
                            line={'color': '#d32f2f'}
                        )
                    ],
                    'layout': {
                        'xaxis': {'title': 'Index'},
                        'yaxis': {'title': col},
                        'margin': {'t': 20, 'b': 60, 'l': 60, 'r': 20}
                    }
                }
            else:
                figure = create_error_message("No data available for trend analysis")

        return figure

    except Exception as e:
        logger.error(f"Error rendering Risk trend graph: {str(e)}")
        return create_error_message(f"Error: {str(e)}")


if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("Starting Risk Analysis Dashboard")
    logger.info("=" * 80)
    logger.info("Listening on: 0.0.0.0:8051")
    logger.info("Note: This dashboard requires a valid tenant-scoped JWT token")
    logger.info("=" * 80)

    app.run_server(host='0.0.0.0', port=8051, debug=False)
