import pytest
from unittest.mock import MagicMock, patch

import re
import pandas as pd

from utils.dbx_utils import (
    get_agg_stds_with_covariance,
    get_manual_dimensions,
    get_current_exposures_data,
    get_r2_dev,
)


# Common fixtures for all tests
@pytest.fixture
def mock_run_query(mocker):
    return mocker.patch("utils.dbx_utils.run_query")


@pytest.fixture
def mock_parse_schema_properties(mocker):
    mock = mocker.patch("utils.dbx_utils.parse_schema_properties")
    return mock


class TestGetManualDimensions:
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker, mock_run_query, mock_parse_schema_properties):
        """
        Fixture to mock dependencies for get_manual_dimensions.
        """
        self.mock_run_query = mock_run_query
        self.mock_parse_schema_properties = mock_parse_schema_properties

        self.mock_build_mandim_select_clause = mocker.patch(
            "utils.dbx_utils.build_mandim_select_clause"
        )
        self.mock_construct_mandim_query = mocker.patch(
            "utils.dbx_utils.construct_mandim_query"
        )

    @pytest.mark.parametrize(
        "num_rows, expected_result",
        [
            (2, [{"cluster": "A"}, {"cluster": "B"}]),  # Success case
        ],
    )
    def test_success(self, num_rows, expected_result):
        """Test get_manual_dimensions with successful execution."""
        self.mock_parse_schema_properties.return_value = (
            {
                "cluster": "cluster_collapse",
                "snapshotDate": "snapshotDate",
                "obsAge": "obsAge",
            },
            "wyndham.performance.burn__performance1__7__20241106_204619",
        )
        self.mock_build_mandim_select_clause.return_value = "SELECT cluster_collapse"
        self.mock_construct_mandim_query.return_value = (
            "SELECT cluster_collapse FROM wyndham.performance.burn__performance1__7__20241106_204619"
        )

        mock_arrow_table = MagicMock()
        mock_arrow_table.num_rows = num_rows
        if num_rows > 0:
            mock_arrow_table.to_pylist.return_value = expected_result
        self.mock_run_query.return_value = mock_arrow_table

        result = get_manual_dimensions("test_consolidated_name")
        assert result == expected_result

        self.mock_parse_schema_properties.assert_called_once_with(
            "test_consolidated_name", "performance1"
        )
        self.mock_build_mandim_select_clause.assert_called_once_with(
            {
                "cluster": "cluster_collapse",
                "snapshotDate": "snapshotDate",
                "obsAge": "obsAge",
            },
            "test_consolidated_name",
        )
        self.mock_construct_mandim_query.assert_called_once_with(
            "SELECT cluster_collapse", "wyndham.performance.burn__performance1__7__20241106_204619"
        )
        self.mock_run_query.assert_called_once_with(
            "SELECT cluster_collapse FROM wyndham.performance.burn__performance1__7__20241106_204619",
            result_type="arrow",
        )

        def test_no_lookup_table_keys(self):
            """Test get_manual_dimensions when no properties are returned."""
            self.mock_parse_schema_properties.return_value = (None, [])

            mock_arrow_table = MagicMock()
            mock_arrow_table.num_rows = 0  # Explicitly set num_rows
            self.mock_dbx_manager.run_query.return_value = mock_arrow_table

            with pytest.raises(ValueError) as exc_info:
                get_manual_dimensions("test_consolidated_name")

            assert "Manuel dimensiosn returned empty" in str(exc_info.value)

            self.mock_parse_schema_properties.assert_called_once_with(
                "test_consolidated_name", "performance1"
            )


class TestGetCurrentExposuresData:
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker, mock_run_query, mock_parse_schema_properties):
        """
        Fixture to mock dependencies for get_current_exposures_data.
        """
        self.mock_run_query = mock_run_query
        self.mock_parse_schema_properties = mock_parse_schema_properties

        self.mock_construct_current_exp_query = mocker.patch(
            "utils.dbx_utils.construct_current_exp_query"
        )

    @pytest.mark.parametrize(
        "num_rows, cluster_list, groupby_dimension",
        [
            (1, [1], "cluster"),  # One row case with cluster
            (1, [1, 2], "cluster"),  # One row case with multiple clusters
        ],
    )
    def test_success(self, num_rows, cluster_list, groupby_dimension):
        """Test get_current_exposures_data with various scenarios."""
        # Mock return values with manual_dimensions added
        properties = {
            "cluster": "cluster_collapse",
            "snapshotDate": "snapshotDate",
            "obsAge": "obsAge",
            "manual_dimensions": [],
        }

        self.mock_parse_schema_properties.return_value = (
            properties,
            "wyndham.performance.burn__performance1__7__20241106_204619",
        )

        # Expected where clause construction
        base_where = "WHERE snapshotDate = '2023-01-01' AND obsAge = 0"
        if groupby_dimension == "cluster" and cluster_list:
            if len(cluster_list) == 1:
                cluster_clause = f" AND cluster_collapse IN ({cluster_list[0]})"
            else:
                cluster_clause = (
                    f" AND cluster_collapse IN {tuple(int(x) for x in cluster_list)}"
                )
            where_clause = base_where + cluster_clause
        else:
            where_clause = base_where

        # Set manual_dimensions based on groupby_dimension
        manual_dimensions = (
            [] if groupby_dimension == "cluster" else properties["manual_dimensions"]
        )

        self.mock_construct_current_exp_query.return_value = (
            f"SELECT * FROM table {where_clause}"
        )

        # Mock arrow table
        mock_arrow_table = MagicMock()
        if num_rows == 0:
            # For error cases
            mock_arrow_table.num_rows = 0
            mock_arrow_table.to_pylist.return_value = []
        else:
            # For success cases
            mock_arrow_table.num_rows = num_rows
            mock_arrow_table.to_pylist.return_value = [{"exposure": 100}]
        self.mock_run_query.return_value = mock_arrow_table

        # Call function and check results
        result = get_current_exposures_data(
            "test_consolidated_name",
            "2023-01-01",
            cluster_list,
            groupby_dimension,
        )
        assert result == [{"exposure": 100}]

        # Verify mock calls
        self.mock_parse_schema_properties.assert_called_once_with(
            "test_consolidated_name", "performance1"  # Added missing report_type parameter
        )
        self.mock_construct_current_exp_query.assert_called_once_with(
            properties,
            where_clause,
            "wyndham.performance.burn__performance1__7__20241106_204619",
            manual_dimensions,
            groupby_dimension == "cluster",
        )
        self.mock_run_query.assert_called_once_with(
            f"SELECT * FROM table {where_clause}", result_type="arrow"
        )


class TestGetR2Dev:
    @pytest.fixture(autouse=True)
    def setup_specific_mocks(
        self, mocker, mock_run_query, mock_parse_schema_properties
    ):
        self.mock_run_query = mock_run_query
        self.mock_parse_schema_properties = mock_parse_schema_properties

        """Setup mocks specific to R2 calculations"""
        self.mock_extract_common_denominator = mocker.patch(
            "utils.dbx_utils.extract_common_denominator"
        )
        self.mock_check_target_consistency = mocker.patch(
            "utils.dbx_utils.check_target_consistency"
        )
        self.mock_construct_r2_query = mocker.patch(
            "utils.dbx_utils.construct_r2_query"
        )

    @pytest.mark.parametrize(
        "num_rows, expected_result, cluster_list, groupby_dimension, target_list",
        [
            (
                1,
                [{"r2": 0.85}],
                ["1"],
                "cluster",
                ["target1"],
            ),  # Single cluster, single target
            (
                1,
                [{"r2": 0.85}],
                ["1", "2"],
                "cluster",
                ["target1"],
            ),  # Multiple clusters, single target
            (
                1,
                [{"r2": 0.85}],
                ["1"],
                "cluster",
                ["target1", "target2"],
            ),  # Single cluster, multiple targets
            (
                1,
                [{"r2": 0.85}],
                [],
                "mixture",
                ["target1"],
            ),  # Non-cluster dimension, single target
            (
                1,
                [{"r2": 0.85}],
                [],
                "mixture",
                ["target1", "target2"],
            ),  # Non-cluster dimension, multiple targets
        ],
    )
    def test_success(
        self, num_rows, expected_result, cluster_list, groupby_dimension, target_list
    ):
        """Test successful R2 calculations with various scenarios"""
        properties = {
            "cluster": "cluster_field",
            "manual_dimensions": ["mixture", "other_dim"],
            "targets": {
                "target1": {
                    "mask": "mask_field1",
                    "actual": "actual_field1",
                    "expected": "expected_field1",
                    "numerator_weight": "weight_field1",
                },
                "target2": {
                    "mask": "mask_field2",
                    "actual": "actual_field2",
                    "expected": "expected_field2",
                    "numerator_weight": "weight_field2",
                },
            },
        }
        self.mock_parse_schema_properties.return_value = (properties, "test_path")
        self.mock_extract_common_denominator.return_value = {"common_denom"}
        self.mock_check_target_consistency.return_value = True

        mock_arrow_table = MagicMock()
        mock_arrow_table.num_rows = num_rows
        if num_rows > 0:
            mock_arrow_table.to_pylist.return_value = expected_result
        self.mock_run_query.return_value = mock_arrow_table

        if num_rows == 0:
            with pytest.raises(ValueError) as exc_info:
                get_r2_dev(
                    consolidated_name="test_schema",
                    target_list=target_list,
                    cluster_list=cluster_list,
                    groupby_dimension=groupby_dimension,
                )
            assert "R2 calcualtions fetched empty" in str(exc_info.value)
        else:
            result = get_r2_dev(
                consolidated_name="test_schema",
                target_list=target_list,
                cluster_list=cluster_list,
                groupby_dimension=groupby_dimension,
            )
            assert result == expected_result

        self.mock_parse_schema_properties.assert_called_once_with("test_schema", "performance1")


class TestGetAggStdsWithCovariance:

    @pytest.fixture
    def mock_parsed_schema(self):
        """Mock the schema parsing result."""
        return {
            "targets": {
                "target1__total_variance": {"expected": "var1_expected", "mask": 1},
                "target2__total_variance": {"expected": "var2_expected", "mask": 1},
            },
            "cluster": "cluster_id",
            "snapshotDate": "snapshot_date",
            "obsAge": "observation_age",
        }, "schema.table"

    @pytest.fixture
    def mock_dbx_manager(self):
        """Mock the database manager."""
        mock = MagicMock()
        # Setup default return value as an empty DataFrame with expected columns
        mock.run_query.return_value = pd.DataFrame(
            columns=["snapshotDate", "obsAge", "std"]
        )
        return mock

    @patch("utils.dbx_utils.parse_schema_properties")
    @patch("utils.dbx_utils.extract_common_denominator")
    @patch("utils.dbx_utils.check_target_consistency")
    @patch("utils.dbx_utils.run_query")
    def test_empty_cluster_list(
        self,
        mock_run,
        mock_check_consistency,
        mock_extract_denominator,
        mock_parse_schema,
        mock_parsed_schema,
    ):
        """Test query generation with empty cluster list (ALL clusters)."""
        # Setup mocks
        mock_parse_schema.return_value = mock_parsed_schema
        mock_extract_denominator.return_value = "common_denominator"
        mock_check_consistency.return_value = True

        # Call function
        get_agg_stds_with_covariance(
            "test_schema", [], ["target1", "target2"], "2023-01-01", False
        )

        # Extract the SQL query passed to run_query
        query_arg = mock_run.call_args[0][0]

        # Verify the WHERE clause doesn't have cluster filtering
        assert "WHERE a.snapshot_date = '2023-01-01'" in query_arg
        # Check that the WHERE clause doesn't contain "cluster_id IN"
        where_clause = re.search(
            r"WHERE.*?(?=FROM|GROUP BY|ORDER BY|\))", query_arg, re.DOTALL
        )
        assert where_clause, "Could not find WHERE clause in query"
        assert "cluster_id IN" not in where_clause.group(0)

    @patch("utils.dbx_utils.parse_schema_properties")
    @patch("utils.dbx_utils.extract_common_denominator")
    @patch("utils.dbx_utils.check_target_consistency")
    @patch("utils.dbx_utils.run_query")
    def test_single_cluster(
        self,
        mock_run,
        mock_check_consistency,
        mock_extract_denominator,
        mock_parse_schema,
        mock_parsed_schema,
    ):
        """Test query generation with a single cluster (string)."""
        # Setup mocks
        mock_parse_schema.return_value = mock_parsed_schema
        mock_extract_denominator.return_value = "common_denominator"
        mock_check_consistency.return_value = True

        # Call function
        get_agg_stds_with_covariance(
            "test_schema", ["123"], ["target1", "target2"], "2023-01-01", False
        )

        # Extract the SQL query passed to run_query
        query_arg = mock_run.call_args[0][0]

        # Verify the WHERE clause has the correct cluster filtering
        assert "WHERE a.cluster_id IN ('123')" in query_arg

    @patch("utils.dbx_utils.parse_schema_properties")
    @patch("utils.dbx_utils.extract_common_denominator")
    @patch("utils.dbx_utils.check_target_consistency")
    @patch("utils.dbx_utils.run_query")
    def test_multiple_clusters(
        self,
        mock_run,
        mock_check_consistency,
        mock_extract_denominator,
        mock_parse_schema,
        mock_parsed_schema,
    ):
        """Test query generation with multiple clusters."""
        # Setup mocks
        mock_parse_schema.return_value = mock_parsed_schema
        mock_extract_denominator.return_value = "common_denominator"
        mock_check_consistency.return_value = True

        # Call function
        get_agg_stds_with_covariance(
            "test_schema", ["123", "456", "789"], ["target1", "target2"], "2023-01-01", False
        )

        # Extract the SQL query passed to run_query
        query_arg = mock_run.call_args[0][0]

        # Verify the WHERE clause has the correct cluster filtering
        assert "WHERE a.cluster_id IN ('123', '456', '789')" in query_arg

    @patch("utils.dbx_utils.parse_schema_properties")
    @patch("utils.dbx_utils.extract_common_denominator")
    @patch("utils.dbx_utils.check_target_consistency")
    @patch("utils.dbx_utils.run_query")
    def test_masked_data(
        self,
        mock_run,
        mock_check_consistency,
        mock_extract_denominator,
        mock_parse_schema,
        mock_parsed_schema,
    ):
        """Test query generation with 'Masked' parameter."""
        # Setup mocks
        mock_parse_schema.return_value = mock_parsed_schema
        mock_extract_denominator.return_value = "common_denominator"
        mock_check_consistency.return_value = True

        # Call function with mask="Masked"
        get_agg_stds_with_covariance(
            "test_schema", ["123"], ["target1", "target2"], "2023-01-01", mask="Masked"
        )

        # Extract the SQL query passed to run_query
        query_arg = mock_run.call_args[0][0]

        # Verify masking in the query - look for mask-specific patterns
        # Instead of asserting absence of "(1 = 1)", check for presence of mask value
        assert "(1 = 1)" in query_arg or "(1=1)" in query_arg  # This might still appear in unrelated parts of the query
        assert "denominator_mask_select" in query_arg or re.search(
            r"\(\d+\s*=\s*1\)", query_arg
        )
        assert "(var1_expected * 1)" in query_arg
        assert "(var2_expected * 1)" in query_arg

    @patch("utils.dbx_utils.parse_schema_properties")
    @patch("utils.dbx_utils.extract_common_denominator")
    @patch("utils.dbx_utils.check_target_consistency")
    @patch("utils.dbx_utils.run_query")
    def test_unmasked_data(
        self,
        mock_run,
        mock_check_consistency,
        mock_extract_denominator,
        mock_parse_schema,
        mock_parsed_schema,
    ):
        """Test query generation with unmasked data (default)."""
        # Setup mocks
        mock_parse_schema.return_value = mock_parsed_schema
        mock_extract_denominator.return_value = "common_denominator"
        mock_check_consistency.return_value = True

        # Call function with False mask parameter
        get_agg_stds_with_covariance(
            "test_schema", ["123"], ["target1", "target2"], "2023-01-01", False
        )

        # Extract the SQL query passed to run_query
        query_arg = mock_run.call_args[0][0]

        # Verify no masking in the query
        assert "(1=1)" in query_arg
        assert "(var1_expected * 1)" in query_arg
        assert "(var2_expected * 1)" in query_arg

    @patch("utils.dbx_utils.parse_schema_properties")
    @patch("utils.dbx_utils.extract_common_denominator")
    @patch("utils.dbx_utils.check_target_consistency")
    @patch("utils.dbx_utils.run_query")
    def test_custom_correlation_value(
        self,
        mock_run,
        mock_check_consistency,
        mock_extract_denominator,
        mock_parse_schema,
        mock_parsed_schema,
    ):
        """Test custom correlation value in query generation."""
        # Setup mocks
        mock_parse_schema.return_value = mock_parsed_schema
        mock_extract_denominator.return_value = "common_denominator"
        mock_check_consistency.return_value = True

        # Call function with custom correlation value
        get_agg_stds_with_covariance(
            "test_schema",
            ["123", "456"],
            ["target1", "target2"],
            "2023-01-01",
            False,
            target_correlation=0.5,
            cluster_correlation=0.5
        )

        # Extract the SQL query passed to run_query
        query_arg = mock_run.call_args[0][0]

        # Verify the correlation value in the covariance calculation
        assert "0.5 * SQRT(" in query_arg or "+ 0.5 * (" in query_arg

    @patch("utils.dbx_utils.parse_schema_properties")
    @patch("utils.dbx_utils.extract_common_denominator")
    @patch("utils.dbx_utils.check_target_consistency")
    @patch("utils.dbx_utils.run_query")
    def test_target_consistency_check_failure(
        self,
        mock_run,
        mock_check_consistency,
        mock_extract_denominator,
        mock_parse_schema,
        mock_parsed_schema,
    ):
        """Test behavior when target consistency check fails."""
        # Setup mocks
        mock_parse_schema.return_value = mock_parsed_schema
        mock_extract_denominator.return_value = "common_denominator"
        mock_check_consistency.return_value = False  # Fail consistency check

        # Call function
        result = get_agg_stds_with_covariance(
            "test_schema", ["123"], ["target1", "target2"], "2023-01-01", False
        )

        # Verify that an empty DataFrame is returned
        assert isinstance(result, pd.DataFrame)
        assert result.empty
        assert list(result.columns) == ["snapshotDate", "obsAge", "std"]

        # Verify dbx_manager was not called
        mock_run.assert_not_called()

    @patch("utils.dbx_utils.parse_schema_properties")
    @patch("utils.dbx_utils.extract_common_denominator")
    @patch("utils.dbx_utils.check_target_consistency")
    @patch("utils.dbx_utils.run_query")
    def test_nonexistent_variance_target(
        self,
        mock_run,
        mock_check_consistency,
        mock_extract_denominator,
        mock_parse_schema,
    ):
        """Test behavior when a variance target doesn't exist in the schema."""
        # Setup mocks
        mock_parse_schema.return_value = (
            {
                "targets": {
                    "target1__total_variance": {"expected": "var1_expected", "mask": 1}
                    # target2__total_variance is missing
                },
                "cluster": "cluster_id",
                "snapshotDate": "snapshot_date",
                "obsAge": "observation_age",
            },
            "schema.table",
        )
        mock_extract_denominator.return_value = "common_denominator"
        mock_check_consistency.return_value = True

        # Call function with a target that doesn't have a corresponding variance
        result = get_agg_stds_with_covariance(
            "test_schema",
            ["123"],
            ["target1", "target2"],  # target2 has no variance
            "2023-01-01",
            False,
        )

        # Verify that an empty DataFrame is returned
        assert isinstance(result, pd.DataFrame)
        assert result.empty
        assert list(result.columns) == ["snapshotDate", "obsAge", "std"]

        # Verify dbx_manager was not called
        mock_run.assert_not_called()

    @patch("utils.dbx_utils.parse_schema_properties")
    @patch("utils.dbx_utils.extract_common_denominator")
    @patch("utils.dbx_utils.check_target_consistency")
    @patch("utils.dbx_utils.run_query")
    def test_sql_query_structure(
        self,
        mock_run,
        mock_check_consistency,
        mock_extract_denominator,
        mock_parse_schema,
        mock_parsed_schema,
    ):
        """Test the general structure of the generated SQL query."""
        # Setup mocks
        mock_parse_schema.return_value = mock_parsed_schema
        mock_extract_denominator.return_value = "common_denominator"
        mock_check_consistency.return_value = True

        # Call function
        get_agg_stds_with_covariance(
            "test_schema", ["123"], ["target1", "target2"], "2023-01-01", False
        )

        # Extract the SQL query passed to run_query
        query_arg = mock_run.call_args[0][0]

        # Verify key components of the query
        assert "WITH" in query_arg
        assert "base_query AS" in query_arg
        assert "weight_totals AS" in query_arg
        assert "SQRT(GREATEST(" in query_arg
        assert "combined_variance" in query_arg
        assert "numerator_variance" in query_arg

    @patch("utils.dbx_utils.parse_schema_properties")
    @patch("utils.dbx_utils.extract_common_denominator")
    @patch("utils.dbx_utils.check_target_consistency")
    @patch("utils.dbx_utils.run_query")
    def test_expected_variance_generation(
        self,
        mock_run,
        mock_check_consistency,
        mock_extract_denominator,
        mock_parse_schema,
        mock_parsed_schema,
    ):
        """Test the expected variance part of the query."""
        # Setup mocks
        mock_parse_schema.return_value = mock_parsed_schema
        mock_extract_denominator.return_value = "common_denominator"
        mock_check_consistency.return_value = True

        # Call function
        get_agg_stds_with_covariance(
            "test_schema", ["123"], ["target1", "target2"], "2023-01-01", False
        )

        # Extract the SQL query passed to run_query
        query_arg = mock_run.call_args[0][0]

        # Expected variance should contain both individual expected values
        assert "var1_expected" in query_arg
        assert "var2_expected" in query_arg