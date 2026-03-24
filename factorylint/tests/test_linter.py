"""
Tests for factorylint.core.linter
"""
import json
import pytest

from factorylint.core.linter import identify_adf_resource, lint_resource, ADFResourceType


# ---------------------------------------------------------------------------
# identify_adf_resource – type-field detection
# ---------------------------------------------------------------------------

def test_identify_pipeline_by_type_field():
    resource = {"type": "Microsoft.DataFactory/factories/pipelines"}
    assert identify_adf_resource(resource) == ADFResourceType.PIPELINE


def test_identify_dataset_by_type_field():
    resource = {"type": "Microsoft.DataFactory/factories/datasets"}
    assert identify_adf_resource(resource) == ADFResourceType.DATASET


def test_identify_linked_service_by_type_field():
    resource = {"type": "Microsoft.DataFactory/factories/linkedservices"}
    assert identify_adf_resource(resource) == ADFResourceType.LINKED_SERVICE


def test_identify_trigger_by_type_field():
    resource = {"type": "Microsoft.DataFactory/factories/triggers"}
    assert identify_adf_resource(resource) == ADFResourceType.TRIGGER


def test_type_field_case_insensitive():
    # The implementation calls .lower() so mixed-case should still work
    resource = {"type": "Microsoft.DataFactory/Factories/Pipelines"}
    assert identify_adf_resource(resource) == ADFResourceType.PIPELINE


# ---------------------------------------------------------------------------
# identify_adf_resource – properties-based detection (no type field)
# ---------------------------------------------------------------------------

def test_identify_pipeline_by_activities_in_properties():
    resource = {"properties": {"activities": []}}
    assert identify_adf_resource(resource) == ADFResourceType.PIPELINE


def test_identify_dataset_by_properties():
    resource = {
        "properties": {
            "typeProperties": {"location": {}},
            "linkedServiceName": {"referenceName": "LS_TEST"},
        }
    }
    assert identify_adf_resource(resource) == ADFResourceType.DATASET


def test_identify_linked_service_by_properties():
    resource = {
        "properties": {
            "connectVia": {"referenceName": "ir"},
            "type": "AzureDataLakeStorage",
        }
    }
    assert identify_adf_resource(resource) == ADFResourceType.LINKED_SERVICE


def test_identify_trigger_by_properties():
    resource = {
        "properties": {
            "pipelines": [{"pipelineReference": {"referenceName": "PL_TEST"}}],
            "type": "ScheduleTrigger",
        }
    }
    assert identify_adf_resource(resource) == ADFResourceType.TRIGGER


def test_identify_unknown_when_no_clues():
    assert identify_adf_resource({}) == ADFResourceType.UNKNOWN
    assert identify_adf_resource({"properties": {}}) == ADFResourceType.UNKNOWN
    assert identify_adf_resource({"type": "SomethingRandom"}) == ADFResourceType.UNKNOWN


# ---------------------------------------------------------------------------
# lint_resource – dispatching to the right validator
# ---------------------------------------------------------------------------

def _minimal_rules():
    """Return a minimal rules config accepted by all validators."""
    return {
        "resources": {
            "pipelines": {
                "enabled": True,
                "naming": {
                    "prefix": "PL_",
                    "case": "upper",
                    "separator": "_",
                    "pattern": "^PL_[A-Z0-9_]+$",
                    "min_separated_parts": 4,
                    "max_separated_parts": 6,
                    "allowed_actions": ["INGEST"],
                    "description_required": False,
                },
            },
            "datasets": {
                "enabled": True,
                "naming": {
                    "prefix": "DS_",
                    "case": "upper",
                    "separator": "_",
                    "pattern": "^DS_[A-Z0-9_]+$",
                    "min_separated_parts": 4,
                    "max_separated_parts": 8,
                },
            },
            "linked_services": {
                "enabled": True,
                "naming": {
                    "prefix": "LS_",
                    "case": "upper",
                    "separator": "_",
                    "pattern": "^LS_[A-Z0-9_]+$",
                    "min_separated_parts": 2,
                    "max_separated_parts": 5,
                },
            },
            "triggers": {
                "enabled": True,
                "naming": {
                    "prefix": "TR_",
                    "case": "upper",
                    "separator": "_",
                    "pattern": "^TR_[A-Z0-9_]+$",
                    "min_separated_parts": 4,
                    "max_separated_parts": 7,
                },
            },
        },
        "parameters": {"enabled": False},
        "variables": {"enabled": False},
    }


def test_lint_resource_unknown_type_returns_error(tmp_path):
    f = tmp_path / "unknown.json"
    f.write_text(json.dumps({"name": "foo"}), encoding="utf-8")
    result = lint_resource(str(f), ADFResourceType.UNKNOWN, {})
    # UNKNOWN branch returns a plain list (not a tuple) – assert it contains an error
    assert isinstance(result, list)
    assert any("Unknown resource type" in e for e in result)


def test_lint_resource_valid_pipeline_no_errors(tmp_path):
    resource = {
        "name": "PL_MES_ORDERS_INGEST",
        "type": "Microsoft.DataFactory/factories/pipelines",
        "properties": {"activities": [], "description": "some description"},
    }
    f = tmp_path / "PL_MES_ORDERS_INGEST.json"
    f.write_text(json.dumps(resource), encoding="utf-8")
    errors, skipped = lint_resource(str(f), ADFResourceType.PIPELINE, _minimal_rules())
    assert errors == []


def test_lint_resource_invalid_pipeline_reports_error(tmp_path):
    resource = {
        "name": "bad_name",
        "type": "Microsoft.DataFactory/factories/pipelines",
        "properties": {"activities": []},
    }
    f = tmp_path / "bad_name.json"
    f.write_text(json.dumps(resource), encoding="utf-8")
    errors, skipped = lint_resource(str(f), ADFResourceType.PIPELINE, _minimal_rules())
    assert len(errors) > 0


def test_lint_resource_valid_dataset_no_errors(tmp_path):
    resource = {"name": "DS_ADLS_ORDERS_CSV", "properties": {}}
    f = tmp_path / "DS_ADLS_ORDERS_CSV.json"
    f.write_text(json.dumps(resource), encoding="utf-8")
    errors, skipped = lint_resource(str(f), ADFResourceType.DATASET, _minimal_rules())
    assert errors == []


def test_lint_resource_valid_linked_service_no_errors(tmp_path):
    resource = {"name": "LS_ADLS_DATALAKE", "properties": {}}
    f = tmp_path / "LS_ADLS_DATALAKE.json"
    f.write_text(json.dumps(resource), encoding="utf-8")
    errors, skipped = lint_resource(str(f), ADFResourceType.LINKED_SERVICE, _minimal_rules())
    assert errors == []


def test_lint_resource_valid_trigger_no_errors(tmp_path):
    resource = {"name": "TR_SCHEDULE_DAILY_MES_IOT", "properties": {}}
    f = tmp_path / "TR_SCHEDULE_DAILY_MES_IOT.json"
    f.write_text(json.dumps(resource), encoding="utf-8")
    errors, skipped = lint_resource(str(f), ADFResourceType.TRIGGER, _minimal_rules())
    assert errors == []
