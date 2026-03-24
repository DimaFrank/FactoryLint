"""
Tests for factorylint.core.config_validator
"""
import pytest
from factorylint.core.config_validator import validate_rules_config


# ---------------------------------------------------------------------------
# Empty / minimal
# ---------------------------------------------------------------------------

def test_empty_config_returns_no_errors():
    assert validate_rules_config({}) == []


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def test_pipeline_valid_patterns():
    config = {"Pipeline": {"patterns": {"name": "^PL_[A-Z]+$"}}}
    assert validate_rules_config(config) == []


def test_pipeline_missing_patterns_key():
    errors = validate_rules_config({"Pipeline": {}})
    assert any("Pipeline must contain 'patterns' dict" in e for e in errors)


def test_pipeline_patterns_not_dict():
    errors = validate_rules_config({"Pipeline": {"patterns": "not-a-dict"}})
    assert any("Pipeline must contain 'patterns' dict" in e for e in errors)


def test_pipeline_invalid_regex():
    config = {"Pipeline": {"patterns": {"name": "[invalid("}}}
    errors = validate_rules_config(config)
    assert any("Invalid regex" in e and "Pipeline" in e for e in errors)


def test_pipeline_valid_multiple_patterns():
    config = {"Pipeline": {"patterns": {"name": "^PL_", "action": "^[A-Z]+$"}}}
    assert validate_rules_config(config) == []


# ---------------------------------------------------------------------------
# Trigger
# ---------------------------------------------------------------------------

def test_trigger_valid():
    config = {
        "Trigger": {
            "ScheduleTrigger": {
                "allowed_prefixes": ["TR_"],
                "pattern": "^TR_[A-Z0-9_]+$",
            }
        }
    }
    assert validate_rules_config(config) == []


def test_trigger_not_dict():
    errors = validate_rules_config({"Trigger": "not-a-dict"})
    assert any("Trigger must be a dictionary" in e for e in errors)


def test_trigger_missing_allowed_prefixes():
    config = {"Trigger": {"ScheduleTrigger": {"pattern": "^TR_[A-Z]+$"}}}
    errors = validate_rules_config(config)
    assert any("allowed_prefixes" in e for e in errors)


def test_trigger_allowed_prefixes_not_list():
    config = {"Trigger": {"ScheduleTrigger": {"allowed_prefixes": "TR_", "pattern": "^TR_"}}}
    errors = validate_rules_config(config)
    assert any("allowed_prefixes" in e for e in errors)


def test_trigger_missing_pattern():
    config = {"Trigger": {"ScheduleTrigger": {"allowed_prefixes": ["TR_"]}}}
    errors = validate_rules_config(config)
    assert any("pattern" in e for e in errors)


def test_trigger_invalid_regex():
    config = {
        "Trigger": {
            "ScheduleTrigger": {
                "allowed_prefixes": ["TR_"],
                "pattern": "[bad(",
            }
        }
    }
    errors = validate_rules_config(config)
    assert any("Invalid regex" in e and "Trigger" in e for e in errors)


# ---------------------------------------------------------------------------
# LinkedService
# ---------------------------------------------------------------------------

def test_linked_service_valid():
    config = {
        "LinkedService": {
            "prefix": "LS_",
            "allowed_abbreviations": [
                {"Type": "AzureBlob", "Service": "Azure Blob Storage", "Abbreviation": "ABLB"}
            ],
        }
    }
    assert validate_rules_config(config) == []


def test_linked_service_missing_prefix():
    config = {
        "LinkedService": {
            "allowed_abbreviations": [
                {"Type": "AzureBlob", "Service": "Azure Blob", "Abbreviation": "ABLB"}
            ]
        }
    }
    errors = validate_rules_config(config)
    assert any("LinkedService must have 'prefix' string" in e for e in errors)


def test_linked_service_prefix_not_string():
    config = {
        "LinkedService": {
            "prefix": 123,
            "allowed_abbreviations": [],
        }
    }
    errors = validate_rules_config(config)
    assert any("LinkedService must have 'prefix' string" in e for e in errors)


def test_linked_service_missing_allowed_abbreviations():
    config = {"LinkedService": {"prefix": "LS_"}}
    errors = validate_rules_config(config)
    assert any("allowed_abbreviations" in e for e in errors)


def test_linked_service_abbreviations_not_list():
    config = {"LinkedService": {"prefix": "LS_", "allowed_abbreviations": "not-a-list"}}
    errors = validate_rules_config(config)
    assert any("allowed_abbreviations" in e for e in errors)


def test_linked_service_invalid_abbreviation_entry_missing_fields():
    config = {
        "LinkedService": {
            "prefix": "LS_",
            "allowed_abbreviations": [{"Type": "AzureBlob"}],  # missing Service, Abbreviation
        }
    }
    errors = validate_rules_config(config)
    assert any("Type, Service, Abbreviation" in e for e in errors)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

def test_dataset_valid():
    config = {
        "Dataset": {
            "prefix": "DS_",
            "formats": {"csv": "CSV"},
            "allowed_chars": "^[A-Z0-9_]+$",
            "allowed_abbreviations": [
                {"Type": "AzureBlob", "Service": "Azure Blob Storage", "Abbreviation": "ABLB"}
            ],
        }
    }
    assert validate_rules_config(config) == []


def test_dataset_missing_prefix():
    config = {
        "Dataset": {
            "formats": {},
            "allowed_chars": "^[A-Z]+$",
            "allowed_abbreviations": [],
        }
    }
    errors = validate_rules_config(config)
    assert any("Dataset must have 'prefix' string" in e for e in errors)


def test_dataset_prefix_not_string():
    config = {
        "Dataset": {
            "prefix": 42,
            "formats": {},
            "allowed_chars": "^[A-Z]+$",
            "allowed_abbreviations": [],
        }
    }
    errors = validate_rules_config(config)
    assert any("Dataset must have 'prefix' string" in e for e in errors)


def test_dataset_missing_formats():
    config = {
        "Dataset": {
            "prefix": "DS_",
            "allowed_chars": "^[A-Z]+$",
            "allowed_abbreviations": [],
        }
    }
    errors = validate_rules_config(config)
    assert any("Dataset must have 'formats' dict" in e for e in errors)


def test_dataset_formats_not_dict():
    config = {
        "Dataset": {
            "prefix": "DS_",
            "formats": "not-a-dict",
            "allowed_chars": "^[A-Z]+$",
            "allowed_abbreviations": [],
        }
    }
    errors = validate_rules_config(config)
    assert any("Dataset must have 'formats' dict" in e for e in errors)


def test_dataset_missing_allowed_chars():
    config = {
        "Dataset": {
            "prefix": "DS_",
            "formats": {},
            "allowed_abbreviations": [],
        }
    }
    errors = validate_rules_config(config)
    assert any("Dataset must have 'allowed_chars' regex string" in e for e in errors)


def test_dataset_invalid_allowed_chars_regex():
    config = {
        "Dataset": {
            "prefix": "DS_",
            "formats": {},
            "allowed_chars": "[bad(",
            "allowed_abbreviations": [],
        }
    }
    errors = validate_rules_config(config)
    assert any("Invalid regex in Dataset.allowed_chars" in e for e in errors)


def test_dataset_missing_allowed_abbreviations():
    config = {
        "Dataset": {
            "prefix": "DS_",
            "formats": {},
            "allowed_chars": "^[A-Z]+$",
        }
    }
    errors = validate_rules_config(config)
    assert any("Dataset must have 'allowed_abbreviations' as a list" in e for e in errors)


def test_dataset_invalid_abbreviation_entry():
    config = {
        "Dataset": {
            "prefix": "DS_",
            "formats": {},
            "allowed_chars": "^[A-Z]+$",
            "allowed_abbreviations": [{"Type": "OnlyType"}],
        }
    }
    errors = validate_rules_config(config)
    assert any("Type, Service, Abbreviation" in e for e in errors)


# ---------------------------------------------------------------------------
# Multiple sections together
# ---------------------------------------------------------------------------

def test_multiple_sections_collect_all_errors():
    config = {
        "Pipeline": {},           # missing patterns
        "LinkedService": {},      # missing prefix and abbreviations
    }
    errors = validate_rules_config(config)
    assert len(errors) >= 2
