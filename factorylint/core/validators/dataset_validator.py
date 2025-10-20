import enum
import yaml
import json
import re
from base_validator import Validator
from resources import ResourceType


class DatasetValidator(Validator):
    """Validate dataset names"""

    def __init__(self, rules: dict):
        super().__init__(ResourceType.DATASET, rules)
        self.naming = self.rules.get("naming", {})
        self.enabled = self.rules.get("enabled", True)
        self.description = self.rules.get("description", "")

    def validate(self, dataset_file_path: str) -> list:

        if self.enabled:
            errors = []
                
            dataset = self.resource_loader(dataset_file_path)

            # Check pattern
            pattern = self.naming.get("pattern")
            if pattern and not re.match(pattern, dataset.get("name", "")):
                errors.append(f"Dataset '{dataset.get('name', '')}' does not match pattern '{pattern}'")

            # Check prefix
            prefix = self.naming.get("prefix")
            if prefix and not dataset.get("name", "").startswith(prefix):
                errors.append(f"Dataset '{dataset.get('name', '')}' must start with prefix '{prefix}'")

            # Split by separator to check min/max separated parts
            sep = self.naming.get("separator")
            parts = dataset.get("name", "").split(sep)
            
            if sep:
                min_parts = self.naming.get("min_separated_parts", 0)
                max_parts = self.naming.get("max_separated_parts", float("inf"))

                if len(parts) < min_parts or len(parts) > max_parts:
                    errors.append(
                        f"Dataset '{dataset.get('name', '')}' should have between {min_parts} and {max_parts} parts separated by '{sep}'"
                    )

            # Check allowed source abbreviations if specified
            allowed_sources = self.naming.get("allowed_source_abbreviations", {})
            source_abbreviation_position = self.naming.get("required_source_position", 1) - 1

            if allowed_sources and source_abbreviation_position:
                # Assuming second part is source
                if len(parts) > 1 and parts[source_abbreviation_position] not in allowed_sources.values():
                    errors.append(
                        f"Dataset '{dataset.get('name', '')}' has invalid source abbreviation '{parts[1]}'. Allowed: {list(allowed_sources.values())}"
                    )
            return errors
        
        else:
            return []