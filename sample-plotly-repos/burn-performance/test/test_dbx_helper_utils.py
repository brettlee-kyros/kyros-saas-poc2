import pytest
import pandas as pd

import json
from unittest.mock import patch, MagicMock
from collections import namedtuple
from utils.dbx_helper_utils import (
    check_target_consistency)


class TestGroupFilter:
    @pytest.fixture
    def create_group_data(self):
        """
        Fixture to create group data with specific model, version, creation_date_time
        Each group should represent a specific combination of these fields
        """

        def _create_group(
            model="model1",
            version="1",
            date="20240101_1111",
            reports=None,
            schemas=None,
            extra_rows=None,
        ):

            if reports is None:
                reports = ["tml1", "tml2", "tml5"]
            if schemas is None:
                schemas = ["tml1", "tml2", "tml5"]
            rows = []

            # table_names
            for report in reports:
                rows.append(
                    {
                        "model": model,
                        "version": version,
                        "creation_date_time": date,
                        "report_type": report,
                        "schema_flag": False,
                    }
                )
            # schema table_names
            # Add schema entries
            for report in schemas:
                rows.append(
                    {
                        "model": model,
                        "version": version,
                        "creation_date_time": date,
                        "report_type": report,
                        "schema_flag": True,
                    }
                )

            # Add any extra rows
            if extra_rows:
                for row in extra_rows:
                    row_with_defaults = {
                        "model": model,
                        "version": version,
                        "creation_date_time": date,
                    }
                    row_with_defaults.update(row)
                    rows.append(row_with_defaults)
            return pd.DataFrame(rows)

        return _create_group


    def test_partial_schema_coverage(self, create_group_data):
        """Test group with only some reports having schemas"""
        # Create a group where tml1 and tml2 have both entries, but tml5 only has table
        rows = [
            # tml1 complete
            {"report_type": "tml1", "schema_flag": False},
            {"report_type": "tml1", "schema_flag": True},
            # tml2 complete
            {"report_type": "tml2", "schema_flag": False},
            {"report_type": "tml2", "schema_flag": True},
            # tml5 incomplete
            {"report_type": "tml5", "schema_flag": False},
        ]
        group = create_group_data(reports=[], schemas=[], extra_rows=rows)


class TestCheckTargetConsistency:
    @pytest.fixture
    def sample_properties(self):
        """Fixture providing sample properties dictionary"""
        return {
            "targets": {
                "target1": {
                    "development_metric": "metric1",
                    "category": "category1",
                    "statistic": "average",
                },
                "target2": {
                    "development_metric": "metric1",
                    "category": "category1",
                    "statistic": "average",
                },
                "target3": {
                    "development_metric": "metric1",
                    "category": "category1",
                    "statistic": "average",
                },
                "different_metric": {
                    "development_metric": "metric2",
                    "category": "category1",
                    "statistic": "average",
                },
                "different_category": {
                    "development_metric": "metric1",
                    "category": "category2",
                    "statistic": "variance",
                },
                "different_statistic": {
                    "development_metric": "metric1",
                    "category": "category1",
                    "statistic": "variance",
                },
            }
        }

    def test_all_consistent_targets(self, sample_properties):
        """Test when all targets have consistent properties"""
        target_list = ["target1", "target2", "target3"]
        result = check_target_consistency(sample_properties, target_list)
        assert result is True

    def test_different_metric(self, sample_properties):
        """Test when one target has a different metric"""
        target_list = ["target1", "different_metric", "target3"]
        result = check_target_consistency(sample_properties, target_list)
        assert result is False

    def test_different_category(self, sample_properties):
        """Test when one target has a different category"""
        target_list = ["target1", "different_category", "target3"]
        result = check_target_consistency(sample_properties, target_list)
        assert result is False

    def test_different_statistic(self, sample_properties):
        """Test when one target has a different statistic"""
        target_list = ["target1", "different_statistic", "target3"]
        result = check_target_consistency(sample_properties, target_list)
        assert result is False

    def test_single_target(self, sample_properties):
        """Test with single target in list"""
        target_list = ["target1"]
        result = check_target_consistency(sample_properties, target_list)
        assert result is True

    def test_none_values(self):
        """Test handling of None values in properties"""
        properties = {
            "targets": {
                "target1": {
                    "development_metric": "metric1",
                    "category": None,
                    "statistic": "mean",
                },
                "target2": {
                    "development_metric": "metric1",
                    "category": None,
                    "statistic": "mean",
                },
            }
        }
        target_list = ["target1", "target2"]
        result = check_target_consistency(properties, target_list)
        assert result is True