import enum
import yaml
import json
import re
from base_validator import Validator
from resources import ResourceType


class PipelineValidator(Validator):
    """Validate pipeline names, supporting master/sub types"""

    def __init__(self, rules: dict):
        super().__init__(ResourceType.PIPELINE, rules)
        self.types_rules = self.rules.get("types", {})
        self.general_rules = self.rules.get("general_rules", {})

    def validate(self, pipeline_name: str, pipeline_type: str = "sub") -> list:
        errors = []

        # # Use type-specific rules
        # type_rules = self.types_rules.get(pipeline_type, {}).get("naming", {})

        # # Check pattern
        # pattern = type_rules.get("pattern")
        # if pattern and not re.match(pattern, pipeline_name):
        #     errors.append(f"Pipeline '{pipeline_name}' does not match pattern for '{pipeline_type}' pipelines")

        # # Check must_contain
        # must_contain = type_rules.get("must_contain")
        # if must_contain and must_contain not in pipeline_name:
        #     errors.append(f"Pipeline '{pipeline_name}' must contain '{must_contain}'")

        # # Check min_parts from general_rules
        # sep = type_rules.get("separator", "_")
        # parts = pipeline_name.split(sep)
        # min_parts = self.general_rules.get("min_parts", 0)
        # if len(parts) < min_parts:
        #     errors.append(
        #         f"Pipeline '{pipeline_name}' should have at least {min_parts} parts separated by '{sep}'"
        #     )

        # # Description requirement
        # desc_required = self.general_rules.get("description_required", False)
        # if desc_required and not type_rules.get("description"):
        #     errors.append(f"Pipeline '{pipeline_name}' must have a description in config")

        # return errors

