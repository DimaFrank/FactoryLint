import enum
import yaml
import json
import re
from factorylint.core.resources import ResourceType


# =====================================================
# Base Validator
# =====================================================
class BaseValidator:
    """Base class for resource validators"""

    def __init__(self, resource_type: ResourceType, rules: dict):
        self.rules = rules['resources'][resource_type.value]

    def get_all_rules(self) -> dict:
        """Return rules as formatted JSON string"""
        return json.dumps(self.rules, indent=4)

    def load_resource(self, resource_path: str) -> dict:
        """Load resource from a YAML or JSON file"""
        with open(resource_path, 'r') as file:
            if resource_path.endswith('.yaml'):
                return yaml.safe_load(file)
            elif resource_path.endswith('.json'):
                return json.load(file)
            else:
                raise ValueError(f"Unsupported file format: {resource_path}")


# =====================================================
# Dataset Validator
# =====================================================
class DatasetValidator(BaseValidator):
    """Validate dataset names"""

    def __init__(self, rules: dict):
        super().__init__(ResourceType.DATASET, rules)
        self.naming = self.rules.get("naming", {})
        self.enabled = self.rules.get("enabled", True)
        self.description = self.rules.get("description", "")

    def validate(self, dataset_file_path: str) -> list:
        if not self.enabled:
            return []

        errors = []
        dataset = self.load_resource(dataset_file_path)
        name = dataset.get("name", "")

        # -----------------------
        # Check pattern
        # -----------------------
        pattern = self.naming.get("pattern")
        if pattern and not re.match(pattern, name):
            errors.append(f"Dataset '{name}' does not match pattern '{pattern}'")

        # -----------------------
        # Check prefix
        # -----------------------
        prefix = self.naming.get("prefix")
        if prefix and not name.startswith(prefix):
            errors.append(f"Dataset '{name}' must start with prefix '{prefix}'")

        # -----------------------
        # Split by separator to check min/max parts
        # -----------------------
        sep = self.naming.get("separator")
        if sep:
            parts = name.split(sep)
            min_parts = self.naming.get("min_separated_parts", 0)
            max_parts = self.naming.get("max_separated_parts", float("inf"))
            if len(parts) < min_parts or len(parts) > max_parts:
                errors.append(
                    f"Dataset '{name}' should have between {min_parts} and {max_parts} parts separated by '{sep}'"
                )

            # -----------------------
            # Check allowed sources
            # -----------------------
            allowed_sources = self.naming.get("allowed_source_abbreviations", {})
            source_pos = self.naming.get("required_source_position", 2) - 1
            if allowed_sources and len(parts) > source_pos:
                if parts[source_pos] not in allowed_sources.values():
                    errors.append(
                        f"Dataset '{name}' has invalid source abbreviation '{parts[source_pos]}'. "
                        f"Allowed: {list(allowed_sources.values())}"
                    )

        return errors


# =====================================================
# Pipeline Validator
# =====================================================
class PipelineValidator(BaseValidator):
    """Validate pipeline names, supporting master/sub types"""

    def __init__(self, rules: dict):
        super().__init__(ResourceType.PIPELINE, rules)
        self.types_rules = self.rules.get("types", {})
        self.general_rules = self.rules.get("general_rules", {})

    def validate(self, pipeline_name: str, pipeline_type: str = "sub") -> list:
        errors = []

        # -----------------------
        # Type-specific rules
        # -----------------------
        type_rules = self.types_rules.get(pipeline_type, {}).get("naming", {})

        # Pattern check
        pattern = type_rules.get("pattern")
        if pattern and not re.match(pattern, pipeline_name):
            errors.append(
                f"Pipeline '{pipeline_name}' does not match pattern for '{pipeline_type}' pipelines"
            )

        # Must contain check
        must_contain = type_rules.get("must_contain")
        if must_contain and must_contain not in pipeline_name:
            errors.append(f"Pipeline '{pipeline_name}' must contain '{must_contain}'")

        # Min parts check
        sep = type_rules.get("separator", "_")
        parts = pipeline_name.split(sep)
        min_parts = self.general_rules.get("min_parts", 0)
        if len(parts) < min_parts:
            errors.append(
                f"Pipeline '{pipeline_name}' should have at least {min_parts} parts separated by '{sep}'"
            )

        # Description requirement
        desc_required = self.general_rules.get("description_required", False)
        if desc_required and not type_rules.get("description"):
            errors.append(f"Pipeline '{pipeline_name}' must have a description in config")

        return errors
