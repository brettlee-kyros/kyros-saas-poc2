"""Error page components for Dash application.

This module provides UI components for displaying errors to users,
including authentication failures and data loading errors.

Usage:
    from error_page import create_401_page, create_error_message

    # In callback
    if df is None:
        return create_error_message("Failed to load data")
"""
from dash import html
import dash_mantine_components as dmc


def create_401_page():
    """Create 401 Unauthorized error page.

    This page is displayed when JWT validation fails, including:
    - Missing Authorization header
    - Invalid JWT token
    - Expired JWT token
    - Token missing tenant_id claim

    Returns:
        Dash HTML component with error page layout

    Example:
        # In middleware when JWT validation fails
        return create_401_page()
    """
    return html.Div([
        html.Div([
            html.H1(
                "401 Unauthorized",
                style={
                    'color': '#d32f2f',
                    'font-size': '48px',
                    'margin-bottom': '20px'
                }
            ),
            html.P(
                "Your session has expired or your token is invalid.",
                style={'font-size': '18px', 'margin-bottom': '10px'}
            ),
            html.P(
                "Please return to the Shell UI and log in again.",
                style={'font-size': '16px', 'margin-bottom': '30px'}
            ),
            html.A(
                "Return to Login",
                href="http://localhost:3000/login",
                style={
                    'background-color': '#1976d2',
                    'color': 'white',
                    'padding': '12px 24px',
                    'text-decoration': 'none',
                    'border-radius': '4px',
                    'font-size': '16px'
                }
            )
        ], style={
            'text-align': 'center',
            'margin-top': '100px',
            'font-family': 'Arial, sans-serif',
            'max-width': '600px',
            'margin-left': 'auto',
            'margin-right': 'auto',
            'padding': '40px',
            'border': '1px solid #e0e0e0',
            'border-radius': '8px',
            'background-color': '#fafafa'
        })
    ])


def create_error_message(message: str, title: str = "Error") -> dict:
    """Create error message for Plotly graph figures.

    This function creates a Plotly figure dict that displays an error
    message when data cannot be loaded or processed.

    Args:
        message: Error message to display
        title: Title for the error display (default: "Error")

    Returns:
        dict: Plotly figure configuration with error message

    Example:
        # In callback when data API fails
        df = DataAPIClient.fetch_dashboard_data('customer-lifetime-value')
        if df is None:
            return create_error_message("Failed to load data from API")
    """
    return {
        'data': [],
        'layout': {
            'title': title,
            'xaxis': {'visible': False},
            'yaxis': {'visible': False},
            'annotations': [{
                'text': message,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 16, 'color': '#d32f2f'},
                'xanchor': 'center',
                'yanchor': 'middle'
            }],
            'height': 400,
            'margin': {'t': 40, 'b': 40, 'l': 40, 'r': 40}
        }
    }


def create_no_data_message(dashboard_name: str) -> dict:
    """Create no data message for Plotly graph figures.

    This function creates a Plotly figure dict that displays a friendly
    message when no data is available for the tenant.

    Args:
        dashboard_name: Name of the dashboard

    Returns:
        dict: Plotly figure configuration with no data message

    Example:
        # In callback when tenant has no data
        df = DataAPIClient.fetch_dashboard_data('customer-lifetime-value')
        if df is not None and df.empty:
            return create_no_data_message("Customer Lifetime Value")
    """
    return {
        'data': [],
        'layout': {
            'title': f'{dashboard_name} Dashboard',
            'xaxis': {'visible': False},
            'yaxis': {'visible': False},
            'annotations': [{
                'text': f'No data available for {dashboard_name}.<br>Please contact your administrator.',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 16, 'color': '#757575'},
                'xanchor': 'center',
                'yanchor': 'middle'
            }],
            'height': 400,
            'margin': {'t': 40, 'b': 40, 'l': 40, 'r': 40}
        }
    }


def create_loading_message() -> dict:
    """Create loading message for Plotly graph figures.

    Returns:
        dict: Plotly figure configuration with loading message

    Example:
        # In callback while loading
        return create_loading_message()
    """
    return {
        'data': [],
        'layout': {
            'title': 'Loading...',
            'xaxis': {'visible': False},
            'yaxis': {'visible': False},
            'annotations': [{
                'text': 'Loading data...',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 16, 'color': '#1976d2'},
                'xanchor': 'center',
                'yanchor': 'middle'
            }],
            'height': 400,
            'margin': {'t': 40, 'b': 40, 'l': 40, 'r': 40}
        }
    }
