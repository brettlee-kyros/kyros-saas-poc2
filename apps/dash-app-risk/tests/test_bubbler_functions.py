"""
Tests for bubbler functions.
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from utils.bubbler_functions import create_column_definitions


@patch('utils.bubbler_functions.parse_schema_properties')
def test_create_column_definitions_segment_type(mock_parse_schema_properties):
    """Test that create_column_definitions uses full path with segment type."""
    # Setup mock parse_schema_properties to return properties and consolidated name
    mock_parse_schema_properties.return_value = (
        {
            'segments': {
                'Region': 'region',
                'Age Group': 'age_group'
            }
        },
        'catalog.schema.table'
    )
    
    # Call the function with full path
    consolidated_name = 'catalog.schema.table'
    column_defs = create_column_definitions(consolidated_name, type="segment")
    
    # Verify that parse_schema_properties was called with the full path and report_type
    mock_parse_schema_properties.assert_called_once_with(consolidated_name, report_type="mix")
    
    # Check that the returned column definitions include the segment columns
    fields = [col.get('field') for col in column_defs]
    assert 'region' in fields
    assert 'age_group' in fields
    assert 'weight' in fields


@patch('utils.bubbler_functions.parse_schema_properties')
def test_create_column_definitions_variable_type(mock_parse_schema_properties):
    """Test that create_column_definitions uses full path with variable type."""
    # Setup mock parse_schema_properties to return properties and consolidated name
    mock_parse_schema_properties.return_value = (
        {
            'segments': {},
            'variables': {
                'Variable': 'variable',
                'KL Divergence': 'kl_divergence'
            }
        },
        'catalog.schema.table'
    )
    
    # Call the function with full path
    consolidated_name = 'catalog.schema.table'
    column_defs = create_column_definitions(consolidated_name, type="variable")
    
    # Verify that parse_schema_properties was called with the full path and report_type
    mock_parse_schema_properties.assert_called_once_with(consolidated_name, report_type="mix")
    
    # For variable type, we should get any fields from the defaults (variable, kl_divergence)
    assert len(column_defs) > 0


@patch('utils.bubbler_functions.parse_schema_properties')
def test_create_column_definitions_with_custom_config(mock_parse_schema_properties):
    """Test column definitions with custom configuration."""
    # Setup mock parse_schema_properties
    mock_parse_schema_properties.return_value = (
        {
            'segments': {
                'Region': 'region'
            }
        },
        'catalog.schema.table'
    )
    
    # Create custom column config for the KL divergence bar renderer
    column_config = {
        'kl_divergence': {
            'cellRenderer': 'BarRenderer',
            'cellRendererParams': {
                'context': {
                    'maxValue': 'auto',
                    'isCentered': True,
                    'barColor': '#64B5F6'
                }
            }
        }
    }
    
    # Call the function with full path and custom config
    consolidated_name = 'catalog.schema.table'
    column_defs = create_column_definitions(
        consolidated_name, 
        type="variable", 
        column_config=column_config
    )
    
    # Verify that parse_schema_properties was called with the full path and report_type
    mock_parse_schema_properties.assert_called_once_with(consolidated_name, report_type="mix")
    
    # Check that the returned column definitions are properly structured
    assert len(column_defs) > 0


@patch('utils.bubbler_functions.parse_schema_properties')
def test_create_column_definitions_with_tooltip_headers(mock_parse_schema_properties):
    """Test column definitions with tooltip headers."""
    # Setup mock parse_schema_properties
    mock_parse_schema_properties.return_value = (
        {
            'segments': {
                'Region': 'region'
            }
        },
        'catalog.schema.table'
    )
    
    # Create custom tooltip headers
    tooltip_headers = {
        'region': 'Geographic Region',
        'default': 'Segment'
    }
    
    # Call the function with full path and tooltip headers
    consolidated_name = 'catalog.schema.table'
    column_defs = create_column_definitions(
        consolidated_name, 
        type="segment", 
        tooltip_headers=tooltip_headers
    )
    
    # Verify that parse_schema_properties was called with the full path and report_type
    mock_parse_schema_properties.assert_called_once_with(consolidated_name, report_type="mix")
    
    # Check that tooltip headers are properly applied
    for col in column_defs:
        if col['field'] == 'region':
            assert col['tooltip'] == 'Geographic Region' 