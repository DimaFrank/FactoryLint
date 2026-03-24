"""
Tests for factorylint.core.validators
"""
import json
import pytest

from factorylint.core.validators import (
    PipelineValidator,
    DatasetValidator,
    LinkedServiceValidator,
    TriggerValidator,
)


# ---------------------------------------------------------------------------
# Helper: write a resource JSON to a tmp file and return the path string
# ---------------------------------------------------------------------------

def _write(tmp_path, filename: str, data: dict) -> str:
    p = tmp_path / filename
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


# ---------------------------------------------------------------------------
# Rule-set factories (minimal configs accepted by each validator)
# ---------------------------------------------------------------------------

def _pipeline_rules(**naming_overrides):
    naming = {
        "prefix": "PL_",
        "case": "upper",
        "separator": "_",
        "pattern": "^PL_[A-Z0-9_]+$",
        "min_separated_parts": 4,
        "max_separated_parts": 6,
        "allowed_actions": ["INGEST", "TRANSFORM", "LOAD"],
        "description_required": False,
    }
    naming.update(naming_overrides)
    return {
        "resources": {"pipelines": {"enabled": True, "naming": naming}},
        "parameters": {"enabled": False},
        "variables": {"enabled": False},
    }


def _dataset_rules(**naming_overrides):
    naming = {
        "prefix": "DS_",
        "case": "upper",
        "separator": "_",
        "pattern": "^DS_[A-Z0-9_]+$",
        "min_separated_parts": 4,
        "max_separated_parts": 8,
    }
    naming.update(naming_overrides)
    return {
        "resources": {"datasets": {"enabled": True, "naming": naming}},
        "parameters": {"enabled": False},
    }


def _linked_service_rules(**naming_overrides):
    naming = {
        "prefix": "LS_",
        "case": "upper",
        "separator": "_",
        "pattern": "^LS_[A-Z0-9_]+$",
        "min_separated_parts": 2,
        "max_separated_parts": 5,
    }
    naming.update(naming_overrides)
    return {"resources": {"linked_services": {"enabled": True, "naming": naming}}}


def _trigger_rules(**naming_overrides):
    naming = {
        "prefix": "TR_",
        "case": "upper",
        "separator": "_",
        "pattern": "^TR_[A-Z0-9_]+$",
        "min_separated_parts": 4,
        "max_separated_parts": 7,
    }
    naming.update(naming_overrides)
    return {"resources": {"triggers": {"enabled": True, "naming": naming}}}


# ============================================================
# PipelineValidator
# ============================================================

class TestPipelineValidator:

    def test_valid_pipeline_passes(self, tmp_path):
        resource = {
            "name": "PL_MES_ORDERS_INGEST",
            "properties": {"activities": [], "description": "desc"},
        }
        path = _write(tmp_path, "PL_MES_ORDERS_INGEST.json", resource)
        errors, skipped = PipelineValidator(_pipeline_rules()).validate(path)
        assert errors == []
        assert skipped == []

    def test_wrong_prefix_reports_error(self, tmp_path):
        resource = {"name": "XX_MES_ORDERS_INGEST", "properties": {"activities": []}}
        path = _write(tmp_path, "XX.json", resource)
        errors, _ = PipelineValidator(_pipeline_rules()).validate(path)
        assert any("prefix" in e for e in errors)

    def test_wrong_case_reports_error(self, tmp_path):
        resource = {"name": "PL_mes_orders_ingest", "properties": {"activities": []}}
        path = _write(tmp_path, "pl_mes.json", resource)
        errors, _ = PipelineValidator(_pipeline_rules()).validate(path)
        assert any("uppercase" in e for e in errors)

    def test_pattern_mismatch_reports_error(self, tmp_path):
        resource = {"name": "PL_MES-ORDERS-INGEST", "properties": {"activities": []}}
        path = _write(tmp_path, "bad_pattern.json", resource)
        errors, _ = PipelineValidator(_pipeline_rules()).validate(path)
        assert any("pattern" in e for e in errors)

    def test_too_few_parts_reports_error(self, tmp_path):
        resource = {"name": "PL_SHORT", "properties": {"activities": []}}
        path = _write(tmp_path, "short.json", resource)
        errors, _ = PipelineValidator(_pipeline_rules()).validate(path)
        assert any("parts" in e for e in errors)

    def test_too_many_parts_reports_error(self, tmp_path):
        resource = {"name": "PL_A_B_C_D_E_F_G", "properties": {"activities": []}}
        path = _write(tmp_path, "long.json", resource)
        errors, _ = PipelineValidator(_pipeline_rules()).validate(path)
        assert any("parts" in e for e in errors)

    def test_invalid_action_reports_error(self, tmp_path):
        resource = {"name": "PL_MES_ORDERS_BADACTION", "properties": {"activities": []}}
        path = _write(tmp_path, "bad_action.json", resource)
        errors, _ = PipelineValidator(_pipeline_rules()).validate(path)
        assert any("action" in e for e in errors)

    def test_description_required_missing(self, tmp_path):
        resource = {"name": "PL_MES_ORDERS_INGEST", "properties": {"activities": []}}
        path = _write(tmp_path, "no_desc.json", resource)
        rules = _pipeline_rules(description_required=True)
        errors, _ = PipelineValidator(rules).validate(path)
        assert any("description" in e for e in errors)

    def test_description_required_present(self, tmp_path):
        resource = {
            "name": "PL_MES_ORDERS_INGEST",
            "description": "my description",
            "properties": {"activities": []},
        }
        path = _write(tmp_path, "with_desc.json", resource)
        rules = _pipeline_rules(description_required=True)
        errors, _ = PipelineValidator(rules).validate(path)
        assert not any("description" in e for e in errors)

    def test_ignore_folder_skips_pipeline(self, tmp_path):
        resource = {
            "name": "PL_MES_ORDERS_INGEST",
            "properties": {
                "activities": [],
                "folder": {"name": "Modules/_Config/SubFolder"},
            },
        }
        path = _write(tmp_path, "skipped.json", resource)
        rules = _pipeline_rules(ignore_folder="_Config")
        errors, skipped = PipelineValidator(rules).validate(path)
        assert errors == []
        assert "PL_MES_ORDERS_INGEST" in skipped

    def test_disabled_validator_returns_empty(self, tmp_path):
        resource = {"name": "INVALID_NAME", "properties": {"activities": []}}
        path = _write(tmp_path, "disabled.json", resource)
        rules = {
            "resources": {"pipelines": {"enabled": False, "naming": {}}},
            "parameters": {"enabled": False},
            "variables": {"enabled": False},
        }
        errors, skipped = PipelineValidator(rules).validate(path)
        assert errors == []
        assert skipped == []

    def test_valid_parameters(self, tmp_path):
        resource = {
            "name": "PL_MES_ORDERS_INGEST",
            "properties": {
                "activities": [],
                "parameters": {"p_source": {"type": "string"}},
            },
        }
        path = _write(tmp_path, "with_params.json", resource)
        rules = _pipeline_rules()
        rules["parameters"] = {
            "enabled": True,
            "naming": {"prefix": "p_", "case": "lower", "pattern": "^p_[a-z0-9_]+$"},
        }
        errors, _ = PipelineValidator(rules).validate(path)
        assert not any("Parameter" in e for e in errors)

    def test_invalid_parameter_name(self, tmp_path):
        resource = {
            "name": "PL_MES_ORDERS_INGEST",
            "properties": {
                "activities": [],
                "parameters": {"BadParam": {"type": "string"}},
            },
        }
        path = _write(tmp_path, "bad_param.json", resource)
        rules = _pipeline_rules()
        rules["parameters"] = {
            "enabled": True,
            "naming": {"prefix": "p_", "case": "lower", "pattern": "^p_[a-z0-9_]+$"},
        }
        errors, _ = PipelineValidator(rules).validate(path)
        assert any("Parameter" in e for e in errors)

    def test_invalid_variable_name(self, tmp_path):
        resource = {
            "name": "PL_MES_ORDERS_INGEST",
            "properties": {
                "activities": [],
                "variables": {"BadVar": {"type": "string"}},
            },
        }
        path = _write(tmp_path, "bad_var.json", resource)
        rules = _pipeline_rules()
        rules["variables"] = {
            "enabled": True,
            "naming": {"prefix": "v_", "case": "lower", "pattern": "^v_[a-z0-9_]+$"},
        }
        errors, _ = PipelineValidator(rules).validate(path)
        assert any("Variable" in e for e in errors)


# ============================================================
# DatasetValidator
# ============================================================

class TestDatasetValidator:

    def test_valid_dataset_passes(self, tmp_path):
        resource = {"name": "DS_ADLS_ORDERS_CSV", "properties": {}}
        path = _write(tmp_path, "DS_ADLS_ORDERS_CSV.json", resource)
        errors, skipped = DatasetValidator(_dataset_rules()).validate(path)
        assert errors == []

    def test_wrong_prefix_reports_error(self, tmp_path):
        resource = {"name": "XX_ADLS_ORDERS_CSV", "properties": {}}
        path = _write(tmp_path, "XX.json", resource)
        errors, _ = DatasetValidator(_dataset_rules()).validate(path)
        assert any("prefix" in e for e in errors)

    def test_wrong_case_reports_error(self, tmp_path):
        resource = {"name": "ds_adls_orders_csv", "properties": {}}
        path = _write(tmp_path, "lower.json", resource)
        errors, _ = DatasetValidator(_dataset_rules()).validate(path)
        assert any("lowercase" in e or "uppercase" in e or "pattern" in e for e in errors)

    def test_pattern_mismatch_reports_error(self, tmp_path):
        resource = {"name": "DS-ADLS-ORDERS-CSV", "properties": {}}
        path = _write(tmp_path, "bad_pattern.json", resource)
        errors, _ = DatasetValidator(_dataset_rules()).validate(path)
        assert any("pattern" in e for e in errors)

    def test_too_few_parts_reports_error(self, tmp_path):
        resource = {"name": "DS_SHORT", "properties": {}}
        path = _write(tmp_path, "short.json", resource)
        errors, _ = DatasetValidator(_dataset_rules()).validate(path)
        assert any("parts" in e for e in errors)

    def test_invalid_format_reports_error(self, tmp_path):
        resource = {"name": "DS_ADLS_ORDERS_BADFORMAT", "properties": {}}
        path = _write(tmp_path, "bad_fmt.json", resource)
        rules = _dataset_rules(allowed_formats=["CSV", "PARQUET"])
        errors, _ = DatasetValidator(rules).validate(path)
        assert any("format" in e for e in errors)

    def test_valid_format_passes(self, tmp_path):
        resource = {"name": "DS_ADLS_ORDERS_CSV", "properties": {}}
        path = _write(tmp_path, "ok_fmt.json", resource)
        rules = _dataset_rules(allowed_formats=["CSV", "PARQUET"])
        errors, _ = DatasetValidator(rules).validate(path)
        assert not any("format" in e for e in errors)

    def test_invalid_source_abbreviation_reports_error(self, tmp_path):
        resource = {"name": "DS_UNKWN_ORDERS_CSV", "properties": {}}
        path = _write(tmp_path, "bad_src.json", resource)
        rules = _dataset_rules(
            allowed_source_abbreviations={"Azure Data Lake Storage Gen2": "ADLS"},
            required_source_position=2,
        )
        errors, _ = DatasetValidator(rules).validate(path)
        assert any("source abbreviation" in e for e in errors)

    def test_valid_source_abbreviation_passes(self, tmp_path):
        resource = {"name": "DS_ADLS_ORDERS_CSV", "properties": {}}
        path = _write(tmp_path, "ok_src.json", resource)
        rules = _dataset_rules(
            allowed_source_abbreviations={"Azure Data Lake Storage Gen2": "ADLS"},
            required_source_position=2,
        )
        errors, _ = DatasetValidator(rules).validate(path)
        assert not any("source abbreviation" in e for e in errors)

    def test_disabled_validator_returns_empty(self, tmp_path):
        resource = {"name": "INVALID_NAME", "properties": {}}
        path = _write(tmp_path, "disabled.json", resource)
        rules = {
            "resources": {"datasets": {"enabled": False, "naming": {}}},
            "parameters": {"enabled": False},
        }
        errors, _ = DatasetValidator(rules).validate(path)
        assert errors == []

    def test_invalid_parameter_name(self, tmp_path):
        resource = {
            "name": "DS_ADLS_ORDERS_CSV",
            "properties": {"parameters": {"BadParam": {"type": "string"}}},
        }
        path = _write(tmp_path, "bad_param.json", resource)
        rules = _dataset_rules()
        rules["parameters"] = {
            "enabled": True,
            "naming": {"prefix": "p_", "case": "lower", "pattern": "^p_[a-z0-9_]+$"},
        }
        errors, _ = DatasetValidator(rules).validate(path)
        assert any("Parameter" in e for e in errors)


# ============================================================
# LinkedServiceValidator
# ============================================================

class TestLinkedServiceValidator:

    def test_valid_linked_service_passes(self, tmp_path):
        resource = {"name": "LS_ADLS_DATALAKE", "properties": {}}
        path = _write(tmp_path, "LS_ADLS.json", resource)
        errors, skipped = LinkedServiceValidator(_linked_service_rules()).validate(path)
        assert errors == []

    def test_missing_name_returns_error(self, tmp_path):
        resource = {"properties": {}}
        path = _write(tmp_path, "no_name.json", resource)
        errors, _ = LinkedServiceValidator(_linked_service_rules()).validate(path)
        assert any("missing" in e for e in errors)

    def test_wrong_prefix_reports_error(self, tmp_path):
        resource = {"name": "XX_ADLS_DATALAKE", "properties": {}}
        path = _write(tmp_path, "bad_prefix.json", resource)
        errors, _ = LinkedServiceValidator(_linked_service_rules()).validate(path)
        assert any("prefix" in e for e in errors)

    def test_wrong_case_reports_error(self, tmp_path):
        resource = {"name": "ls_adls_datalake", "properties": {}}
        path = _write(tmp_path, "lower.json", resource)
        errors, _ = LinkedServiceValidator(_linked_service_rules()).validate(path)
        assert any("uppercase" in e or "pattern" in e for e in errors)

    def test_pattern_mismatch_reports_error(self, tmp_path):
        resource = {"name": "LS-ADLS-DATALAKE", "properties": {}}
        path = _write(tmp_path, "bad_pattern.json", resource)
        errors, _ = LinkedServiceValidator(_linked_service_rules()).validate(path)
        assert any("pattern" in e for e in errors)

    def test_too_few_parts_reports_error(self, tmp_path):
        resource = {"name": "LS", "properties": {}}
        path = _write(tmp_path, "short.json", resource)
        errors, _ = LinkedServiceValidator(_linked_service_rules()).validate(path)
        assert any("parts" in e for e in errors)

    def test_invalid_abbreviation_reports_error(self, tmp_path):
        resource = {"name": "LS_UNKNOWN_DATALAKE", "properties": {}}
        path = _write(tmp_path, "bad_abbr.json", resource)
        rules = _linked_service_rules(allowed_abbreviations=["ADLS", "ASQL"])
        errors, _ = LinkedServiceValidator(rules).validate(path)
        assert any("abbreviation" in e for e in errors)

    def test_valid_abbreviation_passes(self, tmp_path):
        resource = {"name": "LS_ADLS_DATALAKE", "properties": {}}
        path = _write(tmp_path, "ok_abbr.json", resource)
        rules = _linked_service_rules(allowed_abbreviations=["ADLS", "ASQL"])
        errors, _ = LinkedServiceValidator(rules).validate(path)
        assert not any("abbreviation" in e for e in errors)

    def test_disabled_validator_returns_empty(self, tmp_path):
        resource = {"name": "INVALID_NAME", "properties": {}}
        path = _write(tmp_path, "disabled.json", resource)
        rules = {"resources": {"linked_services": {"enabled": False, "naming": {}}}}
        errors, _ = LinkedServiceValidator(rules).validate(path)
        assert errors == []


# ============================================================
# TriggerValidator
# ============================================================

class TestTriggerValidator:

    def test_valid_trigger_passes(self, tmp_path):
        resource = {"name": "TR_SCHEDULE_DAILY_MES_IOT", "properties": {}}
        path = _write(tmp_path, "TR_SCHEDULE_DAILY_MES_IOT.json", resource)
        errors, skipped = TriggerValidator(_trigger_rules()).validate(path)
        assert errors == []

    def test_missing_name_returns_error(self, tmp_path):
        resource = {"properties": {}}
        path = _write(tmp_path, "no_name.json", resource)
        errors, _ = TriggerValidator(_trigger_rules()).validate(path)
        assert any("missing" in e for e in errors)

    def test_wrong_prefix_reports_error(self, tmp_path):
        resource = {"name": "XX_SCHEDULE_DAILY_IOT", "properties": {}}
        path = _write(tmp_path, "bad_prefix.json", resource)
        errors, _ = TriggerValidator(_trigger_rules()).validate(path)
        assert any("prefix" in e for e in errors)

    def test_wrong_case_reports_error(self, tmp_path):
        resource = {"name": "tr_schedule_daily_iot", "properties": {}}
        path = _write(tmp_path, "lower.json", resource)
        errors, _ = TriggerValidator(_trigger_rules()).validate(path)
        assert any("uppercase" in e or "pattern" in e for e in errors)

    def test_pattern_mismatch_reports_error(self, tmp_path):
        resource = {"name": "TR-SCHEDULE-DAILY-IOT", "properties": {}}
        path = _write(tmp_path, "bad_pattern.json", resource)
        errors, _ = TriggerValidator(_trigger_rules()).validate(path)
        assert any("pattern" in e for e in errors)

    def test_too_few_parts_reports_error(self, tmp_path):
        resource = {"name": "TR_SHORT", "properties": {}}
        path = _write(tmp_path, "short.json", resource)
        errors, _ = TriggerValidator(_trigger_rules()).validate(path)
        assert any("parts" in e for e in errors)

    def test_invalid_type_reports_error(self, tmp_path):
        resource = {"name": "TR_BADTYPE_DAILY_IOT", "properties": {}}
        path = _write(tmp_path, "bad_type.json", resource)
        rules = _trigger_rules(allowed_types=["SCHEDULE", "EVENT"])
        errors, _ = TriggerValidator(rules).validate(path)
        assert any("type" in e for e in errors)

    def test_valid_type_passes(self, tmp_path):
        resource = {"name": "TR_SCHEDULE_DAILY_IOT", "properties": {}}
        path = _write(tmp_path, "ok_type.json", resource)
        rules = _trigger_rules(allowed_types=["SCHEDULE", "EVENT"])
        errors, _ = TriggerValidator(rules).validate(path)
        assert not any("type" in e for e in errors)

    def test_invalid_frequency_reports_error(self, tmp_path):
        resource = {"name": "TR_SCHEDULE_BADFREQ_IOT", "properties": {}}
        path = _write(tmp_path, "bad_freq.json", resource)
        rules = _trigger_rules(
            allowed_types=["SCHEDULE"], allowed_frequencies=["DAILY", "HOURLY"]
        )
        errors, _ = TriggerValidator(rules).validate(path)
        assert any("frequency" in e for e in errors)

    def test_valid_frequency_passes(self, tmp_path):
        resource = {"name": "TR_SCHEDULE_DAILY_IOT", "properties": {}}
        path = _write(tmp_path, "ok_freq.json", resource)
        rules = _trigger_rules(
            allowed_types=["SCHEDULE"], allowed_frequencies=["DAILY", "HOURLY"]
        )
        errors, _ = TriggerValidator(rules).validate(path)
        assert not any("frequency" in e for e in errors)

    def test_disabled_validator_returns_empty(self, tmp_path):
        resource = {"name": "INVALID_NAME", "properties": {}}
        path = _write(tmp_path, "disabled.json", resource)
        rules = {"resources": {"triggers": {"enabled": False, "naming": {}}}}
        errors, _ = TriggerValidator(rules).validate(path)
        assert errors == []
