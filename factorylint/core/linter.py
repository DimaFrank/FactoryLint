from enum import Enum
from pathlib import Path
from .validators import (
    DatasetValidator,
    PipelineValidator,
    LinkedServiceValidator,
    TriggerValidator,
)


class ADFResourceType(Enum):
    PIPELINE = "Pipeline"
    DATASET = "Dataset"
    LINKED_SERVICE = "LinkedService"
    TRIGGER = "Trigger"
    UNKNOWN = "Unknown"


def identify_adf_resource(resource_json: dict) -> ADFResourceType:
    """
    Identify the type of Azure Data Factory resource from its JSON.
    """

    top_type = resource_json.get("type", "").lower()

    if top_type.endswith("/pipelines"):
        return ADFResourceType.PIPELINE
    if top_type.endswith("/datasets"):
        return ADFResourceType.DATASET
    if top_type.endswith("/linkedservices"):
        return ADFResourceType.LINKED_SERVICE
    if top_type.endswith("/triggers"):
        return ADFResourceType.TRIGGER

    props = resource_json.get("properties", {})

    if "activities" in props:
        return ADFResourceType.PIPELINE
    if "typeProperties" in props and "linkedServiceName" in props:
        return ADFResourceType.DATASET
    if "connectVia" in props and "type" in props:
        return ADFResourceType.LINKED_SERVICE
    if "pipelines" in props and "type" in props:
        return ADFResourceType.TRIGGER

    return ADFResourceType.UNKNOWN


def lint_resource(
    resource_path: str,
    resource_type: ADFResourceType,
    rules: dict,
) -> list[str]:
    """
    Lint a single ADF resource using provided rules
    """

    resource_path = Path(resource_path)

    match resource_type:
        case ADFResourceType.PIPELINE:
            validator = PipelineValidator(rules)
            return validator.validate(str(resource_path))

        case ADFResourceType.DATASET:
            validator = DatasetValidator(rules)
            return validator.validate(str(resource_path))

        case ADFResourceType.LINKED_SERVICE:
            validator = LinkedServiceValidator(rules)
            return validator.validate(str(resource_path))

        case ADFResourceType.TRIGGER:
            validator = TriggerValidator(rules)
            return validator.validate(str(resource_path))

        case _:
            return [f"Unknown resource type for {resource_path.name}"]
