import yaml
import json
import re
from factorylint.core.resources import ResourceType
from typing import Tuple, List


def _validate_names(names: List[str], naming: dict, entity_type: str) -> List[str]:
    """Validate a list of names against a flat naming config (pattern, case, prefix)."""
    errors = []
    pattern = naming.get("pattern")
    case = naming.get("case")
    prefix = naming.get("prefix")
    for name in names:
        if pattern and not re.match(pattern, name):
            errors.append(f"{entity_type} '{name}' does not match pattern '{pattern}'")
        if case == "upper" and name != name.upper():
            errors.append(f"{entity_type} '{name}' must be uppercase")
        elif case == "lower" and name != name.lower():
            errors.append(f"{entity_type} '{name}' must be lowercase")
        if prefix and not name.startswith(prefix):
            errors.append(f"{entity_type} '{name}' must start with prefix '{prefix}'")
    return errors


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
        """Load resource from a YAML or JSON file (UTF-8 enforced)"""
        try:
            with open(resource_path, "r", encoding="utf-8") as file:
                if resource_path.endswith((".yaml", ".yml")):
                    return yaml.safe_load(file)
                elif resource_path.endswith(".json"):
                    return json.load(file)
                else:
                    raise ValueError(f"Unsupported file format: {resource_path}")
        except UnicodeDecodeError as e:
            raise ValueError(
                f"File is not valid UTF-8: {resource_path}"
            ) from e


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
        self.param_rules = rules.get("parameters", {})

    def validate(self, dataset_file_path: str) -> Tuple[List[str], List[str]]:
        errors = []
        skipped = []

        if not self.enabled:
            return errors, skipped

        dataset = self.load_resource(dataset_file_path)
        name = dataset.get("name", "")

        # -----------------------
        # Check pattern
        # -----------------------
        pattern = self.naming.get("pattern")
        if pattern and not re.match(pattern, name):
            errors.append(f"Dataset '{name}' does not match pattern '{pattern}'")

        # -----------------------
        # Check case
        # -----------------------
        case_rule = self.naming.get("case")
        if case_rule == "lower" and name != name.lower():
            errors.append(f"Dataset '{name}' must be lowercase")
        elif case_rule == "upper" and name != name.upper():
            errors.append(f"Dataset '{name}' must be uppercase")

        # -----------------------
        # Check prefix
        # -----------------------
        prefix = self.naming.get("prefix")
        if prefix and not name.startswith(prefix):
            errors.append(f"Dataset '{name}' must start with prefix '{prefix}'")

        # -----------------------
        # Check allowed formats
        # -----------------------
        allowed_formats = self.naming.get("allowed_formats", [])

        if allowed_formats:
            sep = self.naming.get("separator", "_")
            parts = name.split(sep)
            if len(parts) == 0:
                errors.append(f"Dataset '{name}' has no format part")
            else:
                format_part = parts[-1]

                if format_part not in allowed_formats:
                    errors.append(
                        f"Dataset '{name}' has invalid format '{format_part}'. "
                        f"Allowed formats: {allowed_formats}"
                    )

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

        # -----------------------
        # Parameters
        # -----------------------
        if self.param_rules.get("enabled", False):
            params = dataset.get("properties", {}).get("parameters", {})
            errors.extend(_validate_names(list(params.keys()), self.param_rules.get("naming", {}), "Parameter"))

        return errors, skipped


# =====================================================
# Pipeline Validator
# =====================================================
class PipelineValidator(BaseValidator):
    """Validate pipeline names"""

    def __init__(self, rules: dict):
        super().__init__(ResourceType.PIPELINE, rules)
        self.naming = self.rules.get("naming", {})
        self.enabled = self.rules.get("enabled", True)
        self.param_rules = rules.get("parameters", {})
        self.var_rules = rules.get("variables", {})

    def validate(self, pipeline_file_path: str) -> Tuple[List[str], List[str]]:

        errors = []
        skipped = []

        if not self.enabled:
            return errors, skipped

        pipeline = self.load_resource(pipeline_file_path)
        name = pipeline.get("name", "")

        # -----------------------
        # Ignore folder
        # -----------------------
        ignore_folder = self.naming.get("ignore_folder")
        folder_path = pipeline.get('properties', {}).get('folder', {}).get('name')
        if ignore_folder and folder_path and ignore_folder in folder_path:
            skipped.append(name)
            return errors, skipped

        # -----------------------
        # Description Requirement
        # -----------------------
        desc_required = self.naming.get("description_required", False)
        description = pipeline.get("description")
        if desc_required and (not description or not str(description).strip()):
            errors.append(f"Pipeline '{name}' must have a non-empty description")

        # -----------------------
        # Pattern
        # -----------------------
        pattern = self.naming.get("pattern")
        if pattern and not re.match(pattern, name):
            errors.append(f"Pipeline '{name}' does not match pattern '{pattern}'")

        # -----------------------
        # Case
        # -----------------------
        case = self.naming.get("case")
        if case == "upper" and name != name.upper():
            errors.append(f"Pipeline '{name}' must be uppercase")
        elif case == "lower" and name != name.lower():
            errors.append(f"Pipeline '{name}' must be lowercase")

        # -----------------------
        # Prefix
        # -----------------------
        prefix = self.naming.get("prefix")
        if prefix and not name.startswith(prefix):
            errors.append(f"Pipeline '{name}' must start with prefix '{prefix}'")

        # -----------------------
        # Separator / parts count
        # -----------------------
        sep = self.naming.get("separator", "_")
        parts = name.split(sep)
        min_parts = self.naming.get("min_separated_parts", 0)
        max_parts = self.naming.get("max_separated_parts", float("inf"))
        if not (min_parts <= len(parts) <= max_parts):
            errors.append(
                f"Pipeline '{name}' must have between {min_parts} and {max_parts} parts separated by '{sep}'"
            )

        # -----------------------
        # Parameters
        # -----------------------
        if self.param_rules.get("enabled", False):
            params = pipeline.get("properties", {}).get("parameters", {})
            errors.extend(_validate_names(list(params.keys()), self.param_rules.get("naming", {}), "Parameter"))

        # -----------------------
        # Variables
        # -----------------------
        if self.var_rules.get("enabled", False):
            variables = pipeline.get("properties", {}).get("variables", {})
            errors.extend(_validate_names(list(variables.keys()), self.var_rules.get("naming", {}), "Variable"))

        return errors, skipped
 

# =====================================================
# Linked Service Validator
# =====================================================
class LinkedServiceValidator(BaseValidator):
    """Validate Linked Service names"""

    def __init__(self, rules: dict):
        super().__init__(ResourceType.LINKED_SERVICE, rules)
        self.naming = self.rules.get("naming", {})
        self.enabled = self.rules.get("enabled", True)

    def validate(self, linked_service_file_path: str) -> Tuple[List[str], List[str]]:

        errors = []
        skipped = []

        if not self.enabled:
            return errors, skipped
    
        linked_service = self.load_resource(linked_service_file_path)
        name = linked_service.get("name", "")

        if not name:
            return ["Linked Service name is missing"], skipped

        # -----------------------
        # Prefix
        # -----------------------
        prefix = self.naming.get("prefix")
        if prefix and not name.startswith(prefix):
            errors.append(f"Linked Service '{name}' must start with prefix '{prefix}'")

        # -----------------------
        # Case
        # -----------------------
        case = self.naming.get("case")
        if case == "upper" and name != name.upper():
            errors.append(f"Linked Service '{name}' must be uppercase")
        elif case == "lower" and name != name.lower():
            errors.append(f"Linked Service '{name}' must be lowercase")

        # -----------------------
        # Pattern
        # -----------------------
        pattern = self.naming.get("pattern")
        if pattern and not re.match(pattern, name):
            errors.append(
                f"Linked Service '{name}' does not match pattern '{pattern}'"
            )

        # -----------------------
        # Split checks
        # -----------------------
        sep = self.naming.get("separator", "_")
        parts = name.split(sep)

        min_parts = self.naming.get("min_separated_parts", 0)
        max_parts = self.naming.get("max_separated_parts", float("inf"))

        if not (min_parts <= len(parts) <= max_parts):
            errors.append(
                f"Linked Service '{name}' must have between {min_parts} and {max_parts} parts separated by '{sep}'"
            )

        # -----------------------
        # Allowed abbreviations
        # -----------------------
        allowed_abbr = self.naming.get("allowed_abbreviations", [])
        if allowed_abbr and len(parts) > 1:
            abbr = parts[1]
            if abbr not in allowed_abbr:
                errors.append(
                    f"Linked Service '{name}' has invalid abbreviation '{abbr}'. "
                    f"Allowed: {allowed_abbr}"
                )

        return errors, skipped
    

# =====================================================
# Trigger Validator
# =====================================================
class TriggerValidator(BaseValidator):
    """Validate Trigger names"""

    def __init__(self, rules: dict):
        super().__init__(ResourceType.TRIGGER, rules)
        self.naming = self.rules.get("naming", {})
        self.enabled = self.rules.get("enabled", True)

    def validate(self, trigger_file_path: str) -> Tuple[List[str], List[str]]:
        errors = []
        skipped = []

        if not self.enabled:
            return errors, skipped

        trigger = self.load_resource(trigger_file_path)
        name = trigger.get("name", "")

        if not name:
            errors.append("Trigger name is missing")
            return errors, skipped

        # -----------------------
        # Prefix
        # -----------------------
        prefix = self.naming.get("prefix")
        if prefix and not name.startswith(prefix):
            errors.append(f"Trigger '{name}' must start with prefix '{prefix}'")

        # -----------------------
        # Case
        # -----------------------
        case = self.naming.get("case")
        if case == "upper" and name != name.upper():
            errors.append(f"Trigger '{name}' must be uppercase")

        # -----------------------
        # Pattern
        # -----------------------
        pattern = self.naming.get("pattern")
        if pattern and not re.match(pattern, name):
            errors.append(f"Trigger '{name}' does not match pattern '{pattern}'")

        # -----------------------
        # Split checks
        # -----------------------
        sep = self.naming.get("separator", "_")
        parts = name.split(sep)

        min_parts = self.naming.get("min_separated_parts", 0)
        max_parts = self.naming.get("max_separated_parts", float("inf"))
        if not (min_parts <= len(parts) <= max_parts):
            errors.append(
                f"Trigger '{name}' must have between {min_parts} and {max_parts} parts separated by '{sep}'"
            )

        # -----------------------
        # Allowed trigger types
        # -----------------------
        allowed_types = self.naming.get("allowed_types", [])
        if allowed_types and len(parts) > 1:
            if parts[1] not in allowed_types:
                errors.append(
                    f"Trigger '{name}' has invalid type '{parts[1]}'. "
                    f"Allowed: {allowed_types}"
                )

        return errors, skipped