import pytest
import pandas as pd
from dash.exceptions import PreventUpdate
from utils.exception_handlers import DataSourceError, TM1PlotError, CalloutError

from dash import no_update
import plotly.graph_objects as go

from unittest.mock import patch, MagicMock
from utils.data_processors import fetch_and_store_data, gather_selected_snapshotdate
from utils.visualization import update_fetch_and_exposure_graph_combined


@pytest.fixture
def sample_triangle_df(): 
    """Create a sample triangle DataFrame"""
    return pd.DataFrame({"development": [12, 24, 36], "value": [100, 200, 300]})


@pytest.fixture
def sample_inputs():
    """Sample input values for testing"""
    return {
        "dev_values": ["dev1", "dev2", "dev3"],
        "consolidated_name": "test_consolidation",
        "selected_clusters": ["cluster1", "cluster2"],
        "target_value": ["target1"],
        "mask": {"key": "value"},
    }


@pytest.fixture
def mock_schema_properties():
    """Mock schema properties returned by parse_schema_properties"""
    return ({
        "targets": {
            "target1": {
                "development_metric": "dev",
                "denominator_weight": "denom_w_col_1",
                "actual": "actual_col_1",
                "expected": "expected_col_1",
                "numerator_weight": "num_w_col_1",
                "mask": "mask_col_1",
                "category": "category_A",
                "statistic": "average"
            },
            "target2": {
                "development_metric": "dev_since",
                "denominator_weight": "denom_w_col_2",
                "actual": "actual_col_2",
                "expected": "expected_col_2",
                "numerator_weight": "num_w_col_2",
                "mask": "mask_col_2",
                "category": "category_A",
                "statistic": "average"
            },
        },
        "current_snapshotDate": "2023-01-01",
        "cluster": "cluster_id_col",
        "snapshotDate": "snapshot_dt_col",
        "obsAge": "obs_age_col",
        "development_time_unit": "month",
    }, ["field1", "field2"])


def test_successful_fetch(sample_triangle_df, sample_inputs, mock_schema_properties):
    """Test when all data fetches are successful"""
    with patch("utils.dbx_utils.parse_schema_properties", return_value=mock_schema_properties), \
         patch("utils.data_processors.get_triangle_format_data") as mock_get_data:
        # Setup mock to return DataFrame for all dev_values
        mock_get_data.return_value = sample_triangle_df

        result = fetch_and_store_data(
            sample_inputs["dev_values"],
            sample_inputs["consolidated_name"],
            sample_inputs["selected_clusters"],
            sample_inputs["target_value"],
            sample_inputs["mask"],
        )

        # Verify function was called correctly for each dev_value
        assert mock_get_data.call_count == 3
        for dev_value in sample_inputs["dev_values"]:
            mock_get_data.assert_any_call(
                sample_inputs["consolidated_name"],
                dev_value,
                sample_inputs["selected_clusters"],
                sample_inputs["target_value"],
                sample_inputs["mask"],
            )

        # Verify results
        expected_dict = {
            "dev1": sample_triangle_df.to_dict("records"),
            "dev2": sample_triangle_df.to_dict("records"),
            "dev3": sample_triangle_df.to_dict("records"),
        }
        assert result == expected_dict


def test_all_fetches_fail(sample_inputs, mock_schema_properties):
    """Test when all data fetches fail"""
    with patch("utils.dbx_utils.parse_schema_properties", return_value=mock_schema_properties), \
         patch("utils.data_processors.get_triangle_format_data") as mock_get_data, \
         patch("builtins.print") as mock_print:
        # Setup mock to return None for all dev_values
        mock_get_data.return_value = None

        result = fetch_and_store_data(
            sample_inputs["dev_values"],
            sample_inputs["consolidated_name"],
            sample_inputs["selected_clusters"],
            sample_inputs["target_value"],
            sample_inputs["mask"],
        )

        # Verify function was called correctly for each dev_value
        assert mock_get_data.call_count == 3

        # Verify error messages were printed
        assert mock_print.call_count == 3
        for dev_value in sample_inputs["dev_values"]:
            mock_print.assert_any_call(
                f"Triangular data for '{dev_value}' could not be fetched."
            )

        # Verify results
        expected_dict = {"dev1": {}, "dev2": {}, "dev3": {}}
        assert result == expected_dict


def test_mixed_fetch_results(sample_triangle_df, sample_inputs, mock_schema_properties):
    """Test when some fetches succeed and others fail"""
    with patch("utils.dbx_utils.parse_schema_properties", return_value=mock_schema_properties), \
         patch("utils.data_processors.get_triangle_format_data") as mock_get_data, \
         patch("builtins.print") as mock_print:
        # Setup mock to return DataFrame for first dev_value and None for others
        mock_get_data.side_effect = [
            sample_triangle_df,  # dev1 succeeds
            None,  # dev2 fails
            sample_triangle_df,  # dev3 succeeds
        ]

        result = fetch_and_store_data(
            sample_inputs["dev_values"],
            sample_inputs["consolidated_name"],
            sample_inputs["selected_clusters"],
            sample_inputs["target_value"],
            sample_inputs["mask"],
        )

        # Verify function was called correctly for each dev_value
        assert mock_get_data.call_count == 3

        # Verify error message was printed only for failed fetch
        assert mock_print.call_count == 1
        mock_print.assert_called_once_with(
            "Triangular data for 'dev2' could not be fetched."
        )

        # Verify results
        expected_dict = {
            "dev1": sample_triangle_df.to_dict("records"),
            "dev2": {},
            "dev3": sample_triangle_df.to_dict("records"),
        }
        assert result == expected_dict


def test_empty_dev_values(sample_inputs, mock_schema_properties):
    """Test with empty dev_values list"""
    with patch("utils.dbx_utils.parse_schema_properties", return_value=mock_schema_properties), \
         patch("utils.data_processors.get_triangle_format_data") as mock_get_data:
        result = fetch_and_store_data(
            [],
            sample_inputs["consolidated_name"],
            sample_inputs["selected_clusters"],
            sample_inputs["target_value"],
            sample_inputs["mask"],
        )

        # Verify function was never called
        mock_get_data.assert_not_called()

        # Verify empty result
        assert result == {}


def test_none_mask(sample_triangle_df, mock_schema_properties):
    """Test when mask is None"""
    dev_values = ["dev1"]
    with patch("utils.dbx_utils.parse_schema_properties", return_value=mock_schema_properties), \
         patch("utils.data_processors.get_triangle_format_data") as mock_get_data:
        mock_get_data.return_value = sample_triangle_df

        result = fetch_and_store_data(
            dev_values, "test_consolidation", ["cluster1"], ["target1"], None
        )

        # Verify function was called with None mask
        mock_get_data.assert_called_once_with(
            "test_consolidation", "dev1", ["cluster1"], ["target1"], None
        )

        # Verify results
        expected_dict = {"dev1": sample_triangle_df.to_dict("records")}
        assert result == expected_dict


@pytest.fixture
def sample_schema_properties():
    """Sample schema properties with different target configurations"""
    return {
        "properties": {
            "targets": {
                "target1": {"development_metric": "dev"},
                "target2": {"development_metric": "dev_since"},
            },
            "current_snapshotDate": "2023-01-01"
        },
        "required": ["field1", "field2"],
    }


@pytest.fixture
def sample_tri_df_dict():
    """Sample triangle dataframe dictionary"""
    return {"dev": {"data": "dev_data"}, "dev_since": {"data": "dev_since_data"}}


@pytest.fixture
def sample_exposure_fig():
    """Sample exposure figure"""
    fig = go.Figure(data=[go.Bar(x=["A", "B"], y=[1, 2])])
    # Set up the figure's data with required methods for our tests
    fig.data[0].update = MagicMock()
    return fig


def test_no_target_value():
    """Test behavior when no target value is provided"""
    result = update_fetch_and_exposure_graph_combined(
        selected_clusters=["cluster1"],
        target_value=None,
        mask={},
        monitoring_date = "2024-01-31",
        consolidated_name="test_cons",
        selected_dates=None,
    )

    expected_alert = "Oops! It looks like you have not selected any target values. Please choose at least one to proceed."
    assert result == (
        no_update,
        no_update,
        no_update,
        {"height": "100%", "display": "none"},
        {"height": "100%", "display": "block"},
        expected_alert,
        no_update
    )


def test_schema_properties_not_found():
    """Test behavior when schema properties are not found"""
    with patch("utils.visualization.parse_schema_properties", return_value=({}, "test_co")), \
         patch("builtins.print") as mock_print:

        result = update_fetch_and_exposure_graph_combined(
            selected_clusters=["cluster1"],
            target_value=["target1"],
            mask={},
            monitoring_date = "2024-01-31",
            consolidated_name="test_cons",
            selected_dates=None,
        )

        assert result == (
            no_update,
            no_update,
            no_update,
            {"height": "100%", "display": "none"},
            {"height": "100%", "display": "block"},
            no_update,
            no_update
        )


def test_no_targets_in_schema():
    """Test behavior when no targets are found in schema properties"""
    with patch(
        "utils.visualization.parse_schema_properties",
        return_value=({"current_snapshotDate": "2023-01-01"}, ["required"])
    ), patch("builtins.print") as mock_print:

        result = update_fetch_and_exposure_graph_combined(
            selected_clusters=["cluster1"],
            target_value=["target1"],
            mask={},
            monitoring_date = "2024-01-31",
            consolidated_name="test_cons",
            selected_dates=None,
        )

        assert result == (
            no_update,
            no_update,
            no_update,
            {"height": "100%", "display": "none"},
            {"height": "100%", "display": "block"},
            no_update,
            no_update
        )


def test_successful_update_dev_metric(
    sample_schema_properties, sample_tri_df_dict, sample_exposure_fig
):
    """Test successful update with 'dev' development metric"""
    with patch(
        "utils.visualization.parse_schema_properties",
        return_value=(
            sample_schema_properties["properties"],
            sample_schema_properties["required"],
        ),
    ), patch(
        "utils.data_processors.fetch_and_store_data", return_value=sample_tri_df_dict
    ), patch(
        "utils.visualization.create_exposure_bar_plot", return_value=sample_exposure_fig
    ):
        # Setup the figure data with x and y values needed in the function
        sample_exposure_fig.data[0].x = ["2024-01-31", "2024-02-28"]
        sample_exposure_fig.data[0].y = [100, 200]
        
        result = update_fetch_and_exposure_graph_combined(
            selected_clusters=["cluster1"],
            target_value=["target1"],  # target with dev metric
            mask={},
            monitoring_date = "2024-01-31",
            consolidated_name="test_cons",
            selected_dates=None,
        )

        assert isinstance(result[0], go.Figure)  # exposure figure
        assert result[1] == {"data": "dev_since_data"}  # dev_since data
        assert result[2] == {"data": "dev_data"}  # dev data
        assert result[3] == {"height": "100%", "display": "block"}
        assert result[4] == {"height": "100%", "display": "none"}
        assert result[5] == no_update  # alert message
        # Check if update was called on figure data
        sample_exposure_fig.data[0].update.assert_called()


def test_successful_update_dev_since_metric(
    sample_schema_properties, sample_tri_df_dict, sample_exposure_fig
):
    """Test successful update with 'dev_since' development metric"""
    with patch(
        "utils.visualization.parse_schema_properties",
        return_value=(
            sample_schema_properties["properties"],
            sample_schema_properties["required"],
        ),
    ), patch(
        "utils.data_processors.fetch_and_store_data", return_value=sample_tri_df_dict
    ), patch(
        "utils.visualization.create_exposure_bar_plot", return_value=sample_exposure_fig
    ):
        # Setup the figure data with x and y values needed in the function
        sample_exposure_fig.data[0].x = ["2024-01-31", "2024-02-28"]
        sample_exposure_fig.data[0].y = [100, 200]
        
        result = update_fetch_and_exposure_graph_combined(
            selected_clusters=["cluster1"],
            target_value=["target2"],  # target with dev_since metric
            mask={},
            monitoring_date = "2024-01-31",
            consolidated_name="test_cons",
            selected_dates=None,
        )

        assert isinstance(result[0], go.Figure)
        # Check if update was called on figure data
        sample_exposure_fig.data[0].update.assert_called()


def test_selected_dates_handling(
    sample_schema_properties, sample_tri_df_dict, sample_exposure_fig
):
    """Test handling of selected dates"""
    with patch(
        "utils.visualization.parse_schema_properties",
        return_value=(
            sample_schema_properties["properties"],
            sample_schema_properties["required"],
        ),
    ), patch(
        "utils.data_processors.fetch_and_store_data", return_value=sample_tri_df_dict
    ), patch(
        "utils.visualization.create_exposure_bar_plot", return_value=sample_exposure_fig
    ):
        # Setup the figure data with x and y values needed in the function
        sample_exposure_fig.data[0].x = ["2024-01-31", "2024-02-28"]
        sample_exposure_fig.data[0].y = [100, 200]
        selected_dates = {"point_indices": [0, 1, 2]}
        
        result = update_fetch_and_exposure_graph_combined(
            selected_clusters=["cluster1"],
            target_value=["target1"],
            mask={},
            monitoring_date = "2024-01-31",
            consolidated_name="test_cons",
            selected_dates=selected_dates,
        )

        # Verify that update was called on the figure data
        sample_exposure_fig.data[0].update.assert_called_with({"selectedpoints": [0, 1, 2]})


def test_fetch_data_failure(sample_schema_properties, sample_exposure_fig):
    """Test behavior when fetch_and_store_data returns None"""
    with patch(
        "utils.visualization.parse_schema_properties",
        return_value=(
            sample_schema_properties["properties"],
            sample_schema_properties["required"],
        ),
    ), patch("utils.data_processors.fetch_and_store_data", return_value=None), patch(
        "utils.visualization.create_exposure_bar_plot", return_value=sample_exposure_fig
    ):

        result = update_fetch_and_exposure_graph_combined(
            selected_clusters=["cluster1"],
            target_value=["target1"],
            mask={},
            monitoring_date = "2024-01-31",
            consolidated_name="test_cons",
            selected_dates=None,
        )

        assert result == (
            no_update,
            no_update,
            no_update,
            {"height": "100%", "display": "none"},
            {"height": "100%", "display": "block"},
            no_update,
            no_update
        )


def test_target_value_list_handling(
    sample_schema_properties, sample_tri_df_dict, sample_exposure_fig
):
    """Test handling of target_value as both list and string"""
    with patch(
        "utils.visualization.parse_schema_properties",
        return_value=(
            sample_schema_properties["properties"],
            sample_schema_properties["required"],
        ),
    ), patch(
        "utils.data_processors.fetch_and_store_data", return_value=sample_tri_df_dict
    ), patch(
        "utils.visualization.create_exposure_bar_plot", return_value=sample_exposure_fig
    ):
        # Setup the figure data with x and y values needed in the function
        sample_exposure_fig.data[0].x = ["2024-01-31", "2024-02-28"]
        sample_exposure_fig.data[0].y = [100, 200]
        
        # Test with list
        result_list = update_fetch_and_exposure_graph_combined(
            selected_clusters=["cluster1"],
            target_value=["target1"],
            mask={},
            monitoring_date = "2024-01-31",
            consolidated_name="test_cons",
            selected_dates=None,
        )

        # Reset the mock for next call
        sample_exposure_fig.data[0].update.reset_mock()
        
        # Test with string
        result_string = update_fetch_and_exposure_graph_combined(
            selected_clusters=["cluster1"],
            target_value="target1",
            mask={},
            monitoring_date = "2024-01-31",
            consolidated_name="test_cons",
            selected_dates=None,
        )

        # Results should be the same except for the figure which is regenerated
        assert result_list[1:] == result_string[1:]
        # Check that update was called both times
        assert sample_exposure_fig.data[0].update.call_count > 0


@pytest.fixture
def sample_schema_properties_extended():
    """Sample schema properties with different target configurations"""
    return {
        "properties": {
            "targets": {
                "target1": {
                    "statistic": "average",
                    "development_metric": "dev",
                    "mask": 0,
                },
                "target2": {
                    "statistic": "average",
                    "development_metric": "dev_since",
                    "mask": 1,
                },
                "target3": {
                    "statistic": "average",
                    "development_metric": "dev",
                    "mask": 0,
                },
                "target4": {
                    "statistic": "average",
                    "development_metric": "dev_since",
                    "mask": 0,
                },
            },
            "current_snapshotDate": "2023-01-01"
        },
        "required": ["field1", "field2"],
    }


def test_no_selected_data():
    """Test when no data is selected"""
    result = gather_selected_snapshotdate(None)
    assert result == {}


def test_empty_points():
    """Test when points list is empty"""
    selected_data = {"points": []}
    result = gather_selected_snapshotdate(selected_data)
    assert result == {}


def test_missing_points_key():
    """Test when points key is missing"""
    selected_data = {"other_key": "value"}
    result = gather_selected_snapshotdate(selected_data)
    assert result == {}


def test_single_point_selection():
    """Test when a single point is selected"""
    selected_data = {"points": [{"x": "2023-01-01", "pointIndex": 0}]}
    result = gather_selected_snapshotdate(selected_data)

    assert result == {"snapshotDates": ["2023-01-01"], "point_indices": [0]}


def test_multiple_points_selection():
    """Test when multiple points are selected"""
    selected_data = {
        "points": [
            {"x": "2023-01-01", "pointIndex": 0},
            {"x": "2023-02-01", "pointIndex": 1},
            {"x": "2023-03-01", "pointIndex": 2},
        ]
    }
    result = gather_selected_snapshotdate(selected_data)

    assert result == {
        "snapshotDates": ["2023-01-01", "2023-02-01", "2023-03-01"],
        "point_indices": [0, 1, 2],
    }


def test_missing_x_value():
    """Test when x value is missing from some points"""
    selected_data = {
        "points": [
            {"x": "2023-01-01", "pointIndex": 0},
            {"y": 100, "pointIndex": 1},  # Missing x
            {"x": "2023-03-01", "pointIndex": 2},
        ]
    }
    result = gather_selected_snapshotdate(selected_data)

    assert result == {
        "snapshotDates": ["2023-01-01", "2023-03-01"],
        "point_indices": [0, 1, 2],  # All indices should be included
    }


def test_missing_point_index():
    """Test when pointIndex is missing from some points"""
    selected_data = {
        "points": [
            {"x": "2023-01-01", "pointIndex": 0},
            {"x": "2023-02-01"},  # Missing pointIndex
            {"x": "2023-03-01", "pointIndex": 2},
        ]
    }
    result = gather_selected_snapshotdate(selected_data)

    assert result == {
        "snapshotDates": ["2023-01-01", "2023-02-01", "2023-03-01"],
        "point_indices": [0, 2],  # Only valid indices included
    }


def test_invalid_data_structure():
    """Test with invalid data structure"""
    invalid_data = {"points": "not a list"}  # Invalid points value
    result = gather_selected_snapshotdate(invalid_data)
    # Check that the function returns empty dict rather than raising an exception
    assert result == {}


def test_empty_dict():
    """Test with empty dictionary"""
    result = gather_selected_snapshotdate({})
    assert result == {}


def test_duplicate_points():
    """Test handling of duplicate points"""
    selected_data = {
        "points": [
            {"x": "2023-01-01", "pointIndex": 0},
            {"x": "2023-01-01", "pointIndex": 0},  # Duplicate
            {"x": "2023-02-01", "pointIndex": 1},
        ]
    }
    result = gather_selected_snapshotdate(selected_data)

    assert result == {
        "snapshotDates": ["2023-01-01", "2023-01-01", "2023-02-01"],
        "point_indices": [0, 0, 1],  # Duplicates preserved as they might be intentional
    }


@pytest.fixture
def sample_figure():
    """Create a sample figure with unsorted data"""
    return {
        "data": [{"x": [3, 1, 4, 2, 5], "y": ["C", "A", "D", "B", "E"], "type": "bar"}],
        "layout": {},
    }


@pytest.fixture
def sample_figure_data():
    """Sample figure data"""
    return {
        "data": [{"x": [100, 200, 300], "y": ["Cluster A", "Cluster B", "Cluster C"]}],
        "layout": {"xaxis": {"title": {"text": "Value"}}},
    }
