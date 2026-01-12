import re
import os
import json
from enum import Enum
from .validators import DatasetValidator, PipelineValidator, LinkedServiceValidator, TriggerValidator
import yaml
from pathlib import Path

class ADFResourceType(Enum):
    PIPELINE = "Pipeline"
    DATASET = "Dataset"
    LINKED_SERVICE = "LinkedService"
    TRIGGER = "Trigger"
    UNKNOWN = "Unknown"

def identify_adf_resource(resource_json: dict) -> ADFResourceType:
    """
    Identify the type of Azure Data Factory resource from its JSON.
    Works for both ARM template exports and raw resource JSONs.
    """

    top_type = resource_json.get("type", "").lower()

    # ---- ARM template style detection ----
    if top_type.endswith("/pipelines"):
        return ADFResourceType.PIPELINE
    if top_type.endswith("/datasets"):
        return ADFResourceType.DATASET
    if top_type.endswith("/linkedservices"):
        return ADFResourceType.LINKED_SERVICE
    if top_type.endswith("/triggers"):
        return ADFResourceType.TRIGGER

    # ---- Fallback: raw JSON structure detection ----
    props = resource_json.get("properties", {})

    if "activities" in props:  # pipelines always have activities
        return ADFResourceType.PIPELINE
    if "typeProperties" in props and "linkedServiceName" in props:  # datasets
        return ADFResourceType.DATASET
    if "connectVia" in props and "type" in props:  # linked services
        return ADFResourceType.LINKED_SERVICE
    if "pipelines" in props and "type" in props:  # triggers
        return ADFResourceType.TRIGGER

    return ADFResourceType.UNKNOWN


def lint_resource(resource_path: dict, resource_type: ADFResourceType):
 
    rules = yaml.safe_load(open("config.yml"))

    match resource_type:
        case ADFResourceType.PIPELINE:
            pipeline_validator = PipelineValidator(rules)
            pipeline_errors = pipeline_validator.validate(resource_path)
            return pipeline_errors
                
        case ADFResourceType.DATASET:
            dataset_validator = DatasetValidator(rules)
            dataset_errors = dataset_validator.validate(resource_path)
            return dataset_errors
        
        case ADFResourceType.LINKED_SERVICE:
            linked_service_validator = LinkedServiceValidator(rules)
            linked_service_errors = linked_service_validator.validate(resource_path)
            return linked_service_errors

        case ADFResourceType.TRIGGER:
            trigger_validator = TriggerValidator(rules)
            trigger_errors = trigger_validator.validate(resource_path)
            return trigger_errors
        
        case _:
            return [f"Unknown resource type for {resource_path.get('name', 'N/A')}"]
