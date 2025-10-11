import pandas as pd
from datetime import datetime, timezone
import json

from utils.logger import dash_logger



def extract_common_denominator(lookup_targets, target_list):
    """
    Returns common denom given list of targets if exists.
    lookup_targets = properties["targets"]
    """

    if not target_list:
        raise ValueError("Target list cannot be empty.")

    valid_targets = [target for target in target_list if target in lookup_targets]
    invalid_targets = [target for target in target_list if target not in lookup_targets]

    if invalid_targets:
        raise ValueError(
            f"Following targets do not exist in the lookup schema: {', '.join(invalid_targets)}."
        )

    for target in valid_targets:
        target_data = lookup_targets[target]

        # Check if denominator_weight exists as a key
        if "denominator_weight" not in target_data:
            raise KeyError(
                f"Target '{target}' does not have denominator_weight in the lookup schema."
            )

        # Check if denominator_weight has a valid value (not None or empty)
        weight = target_data["denominator_weight"]
        if weight is None or (isinstance(weight, str) and not weight.strip()):
            raise ValueError(
                f"Target '{target}' has invalid denominator_weight: {weight}."
            )

    common_denominators = set(
        lookup_targets[target]["denominator_weight"] for target in valid_targets
    )

    if len(common_denominators) != 1:
        raise ValueError(
            f"Targets {valid_targets} dont have common denominators: {common_denominators}."
        )

    return common_denominators.pop()


def check_target_consistency(properties, target_list):
    """
    Rule: In order to aggreagate different targets their development_metric, category and statistics should be the same.
    """
    if not target_list:
        raise ValueError("Target list cannot be empty.")

    # Validate all targets exist in properties
    invalid_targets = [
        target for target in target_list if target not in properties["targets"]
    ]

    if invalid_targets:
        raise ValueError(
            f"Following targets do not exist in the lookup schema: {', '.join(invalid_targets)}."
        )

    # check first whether all input targets have required attributes.
    required_attributes = ["development_metric", "category", "statistic"]

    for target in target_list:
        for attr in required_attributes:
            if attr not in properties["targets"][target]:
                raise KeyError(f"Target '{target}' is missing {attr} sub-key.")

    # if its a single target stop here, and return True
    if len(target_list) == 1:
        return True

    # Extract the first target's values to compare against
    reference_values = {
        attr: properties["targets"][target_list[0]][attr]
        for attr in required_attributes
    }

    # Check each target in the list
    for target in target_list[1:]:
        target_info = properties["targets"][target]

        # Check for consistency
        mismatched_attrs = []
        for attr in required_attributes:
            if target_info[attr] != reference_values[attr]:
                mismatched_attrs.append(attr)

        if mismatched_attrs:
            dash_logger.error(
                f"Target '{target}' has inconsistent values for: {', '.join(mismatched_attrs)}"
            )
            return False

    return True


def build_mandim_select_clause(properties, consolidated_name):
    try:
        if "bubblers" not in properties:
            raise KeyError(
                f"'bubblers' child-key is missing in the lookup schema: {consolidated_name}."
            )

        if not properties["bubblers"]:
            raise ValueError(
                f"'bubblers' child-key is empty or invalid in the lookup schema: {consolidated_name}."
            )

        if "dimensions" not in properties["bubblers"]:
            raise KeyError(
                f"'dimensions' child-key is missing within 'bubblers' key. Lookup schema: {consolidated_name}."
            )

        if not properties["bubblers"]["dimensions"]:
            raise ValueError(
                f"'dimensions' child-key is empty or invalid in the lookup schema: {consolidated_name}."
            )

        CLUSTER_ALIAS = f"{properties['bubblers']['dimensions'][0]} AS cluster"  # The first one is always cluster
        fields = [
            CLUSTER_ALIAS if i == 0 else dim
            for i, dim in enumerate(properties["bubblers"]["dimensions"])
        ]
        return f"DISTINCT {', '.join(fields)}"

    except Exception as e:
        raise type(e)(
            f"Failed to create a manual dimension select clause: {str(e)}"
        ) from e


def is_variance_statistic(properties, target_list, consolidated_name):
    """Check whether selected target is a variance statistic type."""

    if not target_list:
        raise ValueError(
            f"target value is not provided. Lookup schema: {consolidated_name}."
        )

    if target_list[0] not in properties["targets"]:
        raise KeyError(
            f"'{target_list[0]}' child-key is missing in the lookup schema: {consolidated_name}."
        )

    if not properties["targets"][target_list[0]]:
        raise ValueError(
            f"'{target_list[0]}' child-key is empty or invalid in the lookup schema: {consolidated_name}."
        )

    if "statistic" not in properties["targets"][target_list[0]]:
        raise KeyError(
            f"'statistic' child-key for '{target_list[0]}' key is missing in the lookup schema: {consolidated_name}."
        )

    if not properties["targets"][target_list[0]]["statistic"]:
        raise ValueError(
            f"'statistic' child-key for '{target_list[0]}' key is empty or invalid in the lookup schema: {consolidated_name}."
        )

    if "variance" in properties["targets"][target_list[0]]["statistic"].lower():
        return True
    else:
        return False
