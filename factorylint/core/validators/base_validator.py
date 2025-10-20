import enum
import yaml
import json
import re
from resources import ResourceType


class Validator:
    """Base class for resource validators"""

    def __init__(self, resource_type: ResourceType, rules: dict):
        self.rules = rules['resources'][resource_type.value]

    def get_all_rules(self) -> dict:
        """Return rules as formatted JSON string"""
        return json.dumps(self.rules, indent=4)

    def resource_loader(self, resource_path: str) -> dict:
        """Load resource from a YAML or JSON file"""
        with open(resource_path, 'r') as file:
            if resource_path.endswith('.yaml'):
                return yaml.safe_load(file)
            elif resource_path.endswith('.json'):
                return json.load(file)
            else:
                raise ValueError("Unsupported file format")
