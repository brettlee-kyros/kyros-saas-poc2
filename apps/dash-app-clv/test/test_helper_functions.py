import pytest
from unittest.mock import patch

import plotly.graph_objs as go
import pandas as pd
import numpy as np
from datetime import datetime
from calendar import monthrange


from utils.helper_functions import (
    parse_and_format_target_options,
    get_recent_exposures,
    fetch_exposures_from_redis,
    create_exposure_fig,
    interpolate_month_ends,
    create_age_slider_marks,
    get_monitoring_dates,
    format_component_options,
    is_numeric_column,
    convert_mandim_columns_type,
)
from kyros_plotly_common.utils.ui import create_date_dropdown_options
from kyros_plotly_common.layout.sidebar import create_blade_structure

from utils.dbx_helper_utils import extract_common_denominator


class TestParseAndFormatTargetOptions:
    @pytest.fixture
    def mock_table_mappings(self):
        """Sample table mappings that would be stored in Redis"""
        return {
            "burn__1__20241018_204345": {"tml1": ("catalog1.schema1.table1", "table1")},
            "burn__2__20241018_204345": {"tml1": ("catalog1.schema1.table2", "table2")},
        }

    @pytest.fixture
    def mock_lookup_mappings(self):
        """Sample lookup mappings that would be stored in Redis"""
        return {
            "table1": {
                "properties": {
                    "targets": {
                        "target1": {},
                        "target2": {},
                    }
                }
            },
            "table2": {
                "properties": {
                    "targets": {
                        "targetA": {},
                        "targetB": {},
                    }
                }
            },
        }

    def test_no_table_mapping_found(self, mocker):
        """Test handling of missing table mapping for the consolidated name"""
        mocker.patch("utils.helper_functions.get_from_redis", return_value={})

        result = parse_and_format_target_options("burn__nonexistent__20241018_204345")

        # Verify empty list is returned
        assert result == []

    def test_no_lookup_schema_found(self, mocker, mock_table_mappings):
        """Test handling of missing lookup schema for tml1_base_name"""
        mocker.patch(
            "utils.helper_functions.get_from_redis",
            side_effect=[mock_table_mappings, {}],
        )

        result = parse_and_format_target_options("burn__1__20241018_204345")

        # Verify empty list is returned
        assert result == []

    def test_empty_targets_in_lookup_schema(self, mocker, mock_table_mappings):
        """Test handling of empty targets in lookup schema"""
        mock_lookup_mappings = {"table1": {"properties": {"targets": {}}}}

        mocker.patch(
            "utils.helper_functions.get_from_redis",
            side_effect=[mock_table_mappings, mock_lookup_mappings],
        )

        result = parse_and_format_target_options("burn__1__20241018_204345")

        # Verify empty list is returned
        assert result == []


class TestGetRecentExposures:
    @pytest.fixture
    def mock_properties(self):
        """Fixture for tm1 properties with a current snapshot date."""
        return {"current_snapshotDate": "2020-06-30"}

    @pytest.fixture
    def mock_redis_data(self):
        """Sample Redis data with the same cluster_collapse values."""
        return [
            {"snapshotDate": "2020-06-30", "value": 500, "cluster_collapse": 1802},
            {"snapshotDate": "2020-01-31", "value": 200, "cluster_collapse": 1802},
        ]

    def test_successful_retrieval_with_matching_snapshot_date(
        self, mocker, mock_properties, mock_redis_data
    ):
        """Test successful retrieval of values matching the current snapshot date."""
        mocker.patch(
            "utils.helper_functions.get_tm1_properties", return_value=mock_properties
        )
        mocker.patch(
            "utils.helper_functions.get_from_redis", return_value=mock_redis_data
        )

        result = get_recent_exposures("test_consolidated_name", [1802])

        # Expected values are those for snapshotDate '2020-06-30'
        expected_result = ([500], [1802])
        assert result == expected_result

    def test_no_matching_snapshot_date(self, mocker, mock_properties, mock_redis_data):
        """Test retrieval when no data matches the current snapshot date."""
        mock_properties["current_snapshotDate"] = "2021-01-01"
        mocker.patch(
            "utils.helper_functions.get_tm1_properties", return_value=mock_properties
        )
        mocker.patch(
            "utils.helper_functions.get_from_redis", return_value=mock_redis_data
        )

        result = get_recent_exposures("test_consolidated_name", [1802])

        # No entries should match, resulting in None
        assert result is None

    def test_no_data_for_cluster_value(self, mocker, mock_properties):
        """Test handling of missing data in Redis for specific cluster values."""
        mocker.patch(
            "utils.helper_functions.get_tm1_properties", return_value=mock_properties
        )
        mocker.patch("utils.helper_functions.get_from_redis", return_value=None)

        result = get_recent_exposures(
            "test_consolidated_name", [9999]
        )  # Cluster 9999 has no data

        # No data should be found, resulting in None
        assert result is None

    def test_empty_cluster_list(self, mocker, mock_properties):
        """Test handling of empty cluster list."""
        mocker.patch(
            "utils.helper_functions.get_tm1_properties", return_value=mock_properties
        )

        result = get_recent_exposures("test_consolidated_name", [])

        # Expect empty lists as return value for empty cluster list input
        assert result == ([], [])

    def test_invalid_cluster_value(self, mocker, mock_properties, mock_redis_data):
        """Test handling of None or invalid values in cluster list."""
        mocker.patch(
            "utils.helper_functions.get_tm1_properties", return_value=mock_properties
        )
        mocker.patch(
            "utils.helper_functions.get_from_redis", return_value=mock_redis_data
        )

        result = get_recent_exposures("test_consolidated_name", [None, 1802])

        # Expect valid data only for valid cluster values
        expected_result = ([500], [1802])
        assert result == expected_result


class TestFetchExposuresFromRedis:
    @pytest.fixture
    def mock_redis_data(self):
        """Sample data that would be stored in Redis"""
        return [
            {"snapshotDate": "2024-01-01", "value": 100},
            {"snapshotDate": "2024-01-02", "value": 200},
        ]

    def test_successful_fetch_with_clusters(self, mocker, mock_redis_data):
        """Test fetching data for specific clusters"""
        mocker.patch(
            "utils.helper_functions.get_from_redis", return_value=mock_redis_data
        )

        result = fetch_exposures_from_redis(
            consolidated_name="model1__v1__20240101", cluster_list=[1, 2]
        )

        assert result is not None
        assert len(result) == 4  # 2 entries * 2 clusters
        assert isinstance(result, list)
        assert all(isinstance(item, dict) for item in result)

    def test_empty_consolidated_name(self):
        """Test handling of empty consolidated_name"""
        result = fetch_exposures_from_redis(consolidated_name="", cluster_list=[1, 2])

        assert result is None

    def test_no_clusters_specified(self, mocker, mock_redis_data):
        """Test fetching data when no clusters are specified"""
        # Mock redis_instance.keys
        mock_redis_instance = mocker.patch("utils.helper_functions.redis_instance")
        mock_redis_instance.keys.return_value = [
            "model1__v1__20240101__cluster_exposures:1",
            "model1__v1__20240101__cluster_exposures:2",
        ]

        mocker.patch(
            "utils.helper_functions.get_from_redis", return_value=mock_redis_data
        )

        result = fetch_exposures_from_redis(
            consolidated_name="model1__v1__20240101", cluster_list=None
        )

        assert result is not None
        assert len(result) == 4  # 2 entries * 2 clusters

    def test_no_data_found(self, mocker):
        """Test handling when no data is found in Redis"""
        mocker.patch("utils.helper_functions.get_from_redis", return_value=None)

        result = fetch_exposures_from_redis(
            consolidated_name="model1__v1__20240101", cluster_list=[1]
        )

        assert result is None


class TestCreateExposureFig:
    @pytest.fixture
    def sample_df(self):
        """Sample DataFrame for figure creation"""
        return pd.DataFrame(
            {
                "snapshotDate": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "value": [100, 200, 300],
            }
        )

    def test_figure_creation(self, sample_df):
        """Test basic figure creation"""
        fig = create_exposure_fig(sample_df)

        assert isinstance(fig, go.Figure)
        assert isinstance(fig.data[0], go.Bar)

    def test_bar_properties(self, sample_df):
        """Test bar trace properties"""
        fig = create_exposure_fig(sample_df)

        bar = fig.data[0]
        assert list(bar.x) == sample_df["snapshotDate"].tolist()
        assert list(bar.y) == sample_df["value"].tolist()

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame"""
        empty_df = pd.DataFrame(columns=["snapshotDate", "value"])
        fig = create_exposure_fig(empty_df)

        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == "No data available"


class TestInterpolateMonthEnds:
    def test_same_month(self):
        """Test dates within same month"""
        result = interpolate_month_ends("2024-01-01", "2024-01-31")
        assert result == ["2024-01-31"]

    def test_multiple_months(self):
        """Test span of multiple months"""
        result = interpolate_month_ends("2024-01-01", "2024-03-31")
        assert result == ["2024-03-31", "2024-02-29", "2024-01-31"]

    def test_leap_year(self):
        """Test February in non-leap year"""
        result = interpolate_month_ends("2024-02-01", "2024-02-29")
        assert result == ["2024-02-29"]

    def test_multiple_years(self):
        """Test span of multiple years"""
        result = interpolate_month_ends("2023-12-01", "2025-01-31")
        expected = [
            "2025-01-31",
            "2024-12-31",
            "2024-11-30",
            "2024-10-31",
            "2024-09-30",
            "2024-08-31",
            "2024-07-31",
            "2024-06-30",
            "2024-05-31",
            "2024-04-30",
            "2024-03-31",
            "2024-02-29",
            "2024-01-31",
            "2023-12-31",
        ]
        assert result == expected

    def test_invalid_date_format(self):
        """Test handling of invalid date format"""
        with pytest.raises(ValueError):
            interpolate_month_ends("2024/01/01", "2024-01-31")

        with pytest.raises(ValueError):
            interpolate_month_ends("2024-01-01", "2024/01/31")

    def test_invalid_dates(self):
        """Test handling of invalid dates"""
        with pytest.raises(ValueError):
            interpolate_month_ends("2024-13-01", "2024-12-31")  # Invalid month

        with pytest.raises(ValueError):
            interpolate_month_ends("2024-01-32", "2024-12-31")  # Invalid day

    def test_end_date_before_start_date(self):
        """Test when end date is before start date"""
        result = interpolate_month_ends("2024-03-15", "2024-01-15")
        assert result == []  # or could raise ValueError depending on desired behavior

    def test_ordering(self):
        """Test that results are ordered from newest to oldest"""
        result = interpolate_month_ends("2024-01-01", "2024-03-31")
        # Verify ordering
        dates = [datetime.strptime(date, "%Y-%m-%d") for date in result]
        assert dates == sorted(dates, reverse=True)


class TestCreateAgeSliderMarks:

    def test_non_standard_max(self):
        """Test with max age not divisible by 10"""
        result = create_age_slider_marks(125)
        assert result[0] == "0"
        assert result[125] == "125"
        assert result[120] == "120"

    def test_small_range(self):
        """Test with small max age"""
        result = create_age_slider_marks(5)
        assert result[0] == "0"
        assert result[5] == "5"
        assert len(result) == 2


class TestGetMonitoringDates:

    def test_missing_properties(self, mocker):
        """Test handling of missing properties"""
        mocker.patch(
            "utils.helper_functions.parse_schema_properties", return_value=({}, "test_co")
        )

        result = get_monitoring_dates("model1__v1__20240101")
        assert result == []


class TestCreateDateDropdownOptions:
    def test_standard_options(self):
        """Test creation of standard dropdown options"""
        dates = ["2024-01-31", "2024-02-29", "2024-03-31"]
        highlighted = ["2024-02-29"]

        result = create_date_dropdown_options(dates, highlighted)

        assert len(result) == 3
        # Check highlighted date
        highlighted_option = next(opt for opt in result if opt["value"] == "2024-02-29")
        assert highlighted_option["label"].style["fontWeight"] == "bold"

        # Check non-highlighted date
        normal_option = next(opt for opt in result if opt["value"] == "2024-01-31")
        assert normal_option["label"] == "2024-01-31"

    def test_no_highlighted_dates(self):
        """Test with no highlighted dates"""
        dates = ["2024-01-31", "2024-02-29"]
        result = create_date_dropdown_options(dates, [])

        assert all(isinstance(opt["label"], str) for opt in result)

    def test_empty_dates_list(self):
        """Test with empty dates list"""
        result = create_date_dropdown_options([], [])
        assert result == []

    def test_error_handling(self, mocker):
        """Test handling of errors in dependencies"""
        mocker.patch(
            "utils.helper_functions.get_tm1_properties",
            side_effect=ValueError("Properties not found"),
        )

        with pytest.raises(ValueError):
            format_component_options("model1__v1__20240101")


class TestIsNumeric:
    def test_integer_strings(self):
        """Test detection of integer strings"""
        assert is_numeric_column(pd.Series(["123", "-456", "789"]))
        assert is_numeric_column(pd.Series(["0123", "0456", "0789"]))

    def test_float_strings(self):
        """Test detection of float strings"""
        assert is_numeric_column(pd.Series(["-123.45", "-456.78", "-789.01"]))
        assert is_numeric_column(pd.Series([".123", ".456", ".789"]))

    def test_mixed_content(self):
        """Test series with mixed content"""
        assert not is_numeric_column(pd.Series(["abc", "123", "456"]))

    def test_whitespace(self):
        """Test handling of whitespace"""
        assert is_numeric_column(pd.Series([" 123 ", "  456  ", "\t789\n"]))
        assert not is_numeric_column(pd.Series([" ", "  ", "\t\n"]))

    def test_empty_and_null(self):
        """Test handling of empty and null values"""
        # Empty series
        assert not is_numeric_column(pd.Series([]))
        assert is_numeric_column(pd.Series([None, "123", "456"]))
        assert is_numeric_column(pd.Series([np.nan, "123", "456"]))

    def test_non_string_types(self):
        """Test handling of non-string types"""
        # Integer types
        assert not is_numeric_column(pd.Series([123, 456, 789]))
        # Float types
        assert not is_numeric_column(pd.Series([123.45, 456.78, 789.01]))
        # Boolean
        assert not is_numeric_column(pd.Series([True, False, True]))
        # Mixed types
        assert not is_numeric_column(pd.Series([123, "456", 789.0]))

    def test_invalid_numeric_strings(self):
        """Test strings that look numeric but aren't valid!"""
        assert not is_numeric_column(pd.Series(["1.2.3", "4.5.6"]))
        assert not is_numeric_column(pd.Series(["123a", "b456"]))
        assert not is_numeric_column(pd.Series(["--123", "---456"]))
        assert not is_numeric_column(pd.Series(["$123", "456%"]))


class TestConvertMandimColumns:
    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing"""
        return pd.DataFrame(
            {
                "value1": ["123", "456", "789"],
                "text": ["abc", "def", "ghi"],
                "value2": ["42", "84", "126"],
            }
        )

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame"""
        empty_df = pd.DataFrame(columns=["value1", "text"])

        # Should not raise an error
        result = convert_mandim_columns_type(empty_df)

        # Should return empty DataFrame with same columns
        assert len(result) == 0
        assert list(result.columns) == ["value1", "text"]

    def test_whitespace_handling(self):
        """Test handling of whitespace in numeric strings"""
        df = pd.DataFrame(
            {"cluster": [1.0, 2.0, 3.0], "value1": [" 123 ", "  456  ", "\t789\n"]}
        )

        result = convert_mandim_columns_type(df)
        assert list(result["value1"]) == [123, 456, 789]


# denominator_extractor.py
class DenominatorExtractor:
    def extract_common_denominator(self, lookup_targets, target_list):
        """
        Extracts common denominators from a lookup dictionary based on specified targets.

        Args:
            lookup_targets: Dictionary containing target information with denominator weights
            target_list: List of target keys to check for common denominators

        Returns:
            Set of common denominators if found, None if no valid denominators exist
        """
        valid_targets = [target for target in target_list if target in lookup_targets]
        if not valid_targets:
            return None

        try:
            common_denominators = set(
                lookup_targets[target]["denominator_weight"] for target in valid_targets
            )
            return common_denominators if common_denominators else None

        except KeyError:
            return None


class TestDenominatorExtractor:
    @pytest.fixture
    def extractor(self):
        return DenominatorExtractor()

    @pytest.fixture
    def lookup_targets(self):
        return {
            "target1": {"denominator_weight": 0.5},
            "target2": {"denominator_weight": 0.7},
            "target3": {"denominator_weight": 0.5},
            "target4": {"wrong_key": 0.8},
            "target5": {},
        }

    def test_normal_case(self, extractor, lookup_targets):
        result = extractor.extract_common_denominator(
            lookup_targets, ["target1", "target2", "target3"]
        )
        assert result == {0.5, 0.7}

    def test_single_target(self, extractor, lookup_targets):
        result = extractor.extract_common_denominator(lookup_targets, ["target1"])
        assert result == {0.5}

    def test_nonexistent_targets(self, extractor, lookup_targets):
        result = extractor.extract_common_denominator(
            lookup_targets, ["nonexistent1", "nonexistent2"]
        )
        assert result is None

    def test_mixed_targets(self, extractor, lookup_targets):
        result = extractor.extract_common_denominator(
            lookup_targets, ["target1", "nonexistent1"]
        )
        assert result == {0.5}

    def test_empty_target_list(self, extractor, lookup_targets):
        result = extractor.extract_common_denominator(lookup_targets, [])
        assert result is None

    def test_missing_denominator_weight(self, extractor, lookup_targets):
        result = extractor.extract_common_denominator(lookup_targets, ["target4"])
        assert result is None

    def test_empty_dictionary(self, extractor, lookup_targets):
        result = extractor.extract_common_denominator(lookup_targets, ["target5"])
        assert result is None

    def test_none_input(self, extractor):
        with pytest.raises(TypeError):
            extractor.extract_common_denominator(None, ["target1"])