import re
import os
import json
from enum import Enum

# Example abbreviation mapping for datasets and linked services

with open("system_abbreviations.json") as f:
    abbreviation = json.load(f)

ABBREVIATIONS = {
    "LinkedService": [entry["Abbreviation"] for entry in abbreviation["LinkedService"]],
    "Dataset": [entry["Abbreviation"] for entry in abbreviation["Dataset"]],
}

FORMAT_MAPPING = {
    "DelimitedText": "CSV",
    "AzureSqlTable": "TABLE",
    "Parquet": "PARQUET",
    "Json": "JSON",
    "Excel": "EXCEL",
    "Avro": "AVRO",
    "Binary": "BIN",
    "XML": "XML",
    "Orc": "ORC"
}


def lint_linked_service(ls_name: str) -> list:
    errors = []
    if not ls_name.startswith("LS_"):
        errors.append("Linked Service must start with 'LS_'")
    if not any(ls_name.startswith(prefix) for prefix in ABBREVIATIONS["LinkedService"]):
        errors.append(f"Linked Service '{ls_name}' does not match known prefixes")
    return errors


def lint_dataset(ds_name: str, dataset_type: str) -> list:
    errors = []
    if not ds_name.startswith("DS_"):
        errors.append("Dataset must start with 'DS_'")
    # Check FORMAT suffix
    expected_format = FORMAT_MAPPING.get(dataset_type)
    if expected_format and not ds_name.endswith(f"_{expected_format}"):
        errors.append(f"Dataset '{ds_name}' must end with format suffix '_{expected_format}'")
    # Uppercase and allowed chars
    detail_part = "_".join(ds_name.split("_")[2:-1])  # remove prefix and format
    if not re.match(r"^[A-Z0-9_]+$", detail_part):
        errors.append(f"Dataset detail part '{detail_part}' must be uppercase letters, numbers or underscores only")
    return errors


def lint_pipeline(pipeline_name: str) -> list:
    errors = []

    # Regex patterns
    master_pattern = r"^\d{3}_00_Master(_[A-Za-z0-9_]+)?_[A-Za-z0-9_]+$"
    sub_pattern = r"^\d{3}_(0[1-9]|[1-9][0-9])(_[A-Za-z0-9_]+)?_[A-Za-z0-9_]+$"

    if re.match(master_pattern, pipeline_name):
        # This is a master pipeline, valid
        pass
    elif re.match(sub_pattern, pipeline_name):
        # This is a sub-pipeline, valid
        # Optionally: check it does NOT contain 'Master'
        if "Master" in pipeline_name:
            errors.append(f"Sub-pipeline '{pipeline_name}' should not include 'Master' in its name")
    else:
        errors.append(f"Pipeline '{pipeline_name}' must follow naming conventions for Master or Sub-pipelines")
    
    return errors


def lint_trigger(trigger_name: str, trigger_type: str) -> list:
    errors = []
    if trigger_type == "ScheduleTrigger" and not trigger_name.startswith(("Daily-", "Hourly-", "Weekly-", "Monthly-")):
        errors.append(f"Scheduled trigger '{trigger_name}' must start with frequency (Daily/Hourly/Weekly/Monthly)")
    if trigger_type == "BlobEventsTrigger" and not trigger_name.startswith("File-"):
        errors.append(f"File trigger '{trigger_name}' must start with 'File-'")
    # Check ProjectName and PipelineName in trigger
    try:
        project_name = trigger_name.split('-')[1]
        pipeline_name = trigger_name.split('-')[-1]
    except IndexError:
        errors.append(f"Trigger '{trigger_name}' is not properly formatted")
        return errors

    pattern = rf"^(Daily|Hourly|Weekly|Monthly|File)-{project_name}-{pipeline_name}$"
    if not re.match(pattern, trigger_name):
        errors.append(f"Trigger '{trigger_name}' does not match required pattern '{pattern}'")
    return errors


def lint_key_vault(kv_name: str, kv_type: str) -> list:
    errors = []
    if kv_type.lower() not in ["username", "password", "url"]:
        errors.append(f"Key Vault '{kv_name}' type '{kv_type}' is invalid. Must be username/password/url")
    return errors


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


def lint_resource(resource_json: dict):
    resource_type = identify_adf_resource(resource_json)
    print(resource_type)
    
    match resource_type:
        case ADFResourceType.PIPELINE:
            return lint_pipeline(resource_json["name"])
        case ADFResourceType.DATASET:
            return lint_dataset(resource_json["name"], resource_json["properties"]["type"])
        case ADFResourceType.LINKED_SERVICE:
            return lint_linked_service(resource_json["name"])
        case ADFResourceType.TRIGGER:
            return lint_trigger(
                resource_json["name"],
                resource_json["properties"]["type"]
            )
        case _:
            return [f"Unknown resource type for {resource_json.get('name', 'N/A')}"]



# Example usage
if __name__ == "__main__":

    # ls_errors = lint_linked_service("LS_ADLS_LZ_ONPREMIR")
    # ds_errors = lint_dataset("DS_SQL_CUSTOMERS_CSV", "DelimitedText")
    # pipeline_errors = lint_pipeline("001_02_Hilan")
    # trigger_errors = lint_trigger("Daily-SAPBW-hilan", "Scheduled", "SAPBW", "hilan")
    # kv_errors = lint_key_vault("DataSource-username", "username")

    # print(ls_errors,'\n', ds_errors, '\n', pipeline_errors, '\n', trigger_errors, '\n', kv_errors)

    # print('-' * 40)

    # total_counter = 0
    # for dataset in os.listdir("./.azure_migration/df-sgbi-general-dev/dataset/"):
    #     print(f"Processing dataset: {dataset}")

    #     with open(f"./.azure_migration/df-sgbi-general-dev/dataset/{dataset}", encoding='utf-8') as f:
    #         resource_json = json.load(f)

    #         type = identify_adf_resource(resource_json)
    #         print(f"Type: {type}")

    #         errors = lint_resource(resource_json)
    #         print(f"Errors found: {len(errors)}")
    #         for i, error in enumerate(errors, start=1):
    #             print(f"Error {i}: {error}")

    #         total_counter += len(errors)

    #     print('-' * 40)

    # print(f"Total errors found so far: {total_counter}")


    print('-' * 40)

    total_counter = 0
    for pipeline in os.listdir("./.azure_migration/df-sgbi-general-dev/pipeline/"):
        print(f"Processing pipeline: {pipeline}")

        with open(f"./.azure_migration/df-sgbi-general-dev/pipeline/{pipeline}", encoding='utf-8') as f:
            resource_json = json.load(f)

            type = identify_adf_resource(resource_json)
            print(f"Type: {type}")

            errors = lint_resource(resource_json)
            print(f"Errors found: {len(errors)}")
            for i, error in enumerate(errors, start=1):
                print(f"Error {i}: {error}")

            total_counter += len(errors)

        print('-' * 40)

    print(f"Total errors found so far: {total_counter}")


    # print('-' * 40)

    # total_counter = 0
    # for linked_service in os.listdir("./.azure_migration/df-sgbi-general-dev/linkedService/"):
    #     print(f"Processing linked service: {linked_service}")

    #     with open(f"./.azure_migration/df-sgbi-general-dev/linkedService/{linked_service}", encoding='utf-8') as f:
    #         resource_json = json.load(f)

    #         type = identify_adf_resource(resource_json)
    #         print(f"Type: {type}")

    #         errors = lint_resource(resource_json)
    #         print(f"Errors found: {len(errors)}")
    #         for i, error in enumerate(errors, start=1):
    #             print(f"Error {i}: {error}")

    #         total_counter += len(errors)

    #     print('-' * 40)

    # print(f"Total errors found so far: {total_counter}")