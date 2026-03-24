"""
Tests for factorylint.cli
"""
import json
import os
import pytest
import yaml
from click.testing import CliRunner
from pathlib import Path

from factorylint.cli import cli, load_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_rules_config() -> dict:
    """Return a minimal valid rules config that passes validate_rules_config."""
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
                    "allowed_actions": ["INGEST", "TRANSFORM", "LOAD"],
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


def _write_config(directory: Path, filename: str = "config.yml") -> Path:
    config_path = directory / filename
    config_path.write_text(yaml.dump(_minimal_rules_config()), encoding="utf-8")
    return config_path


def _write_pipeline(directory: Path, name: str = "PL_MES_ORDERS_INGEST") -> Path:
    pipeline_dir = directory / "pipeline"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    resource = {
        "name": name,
        "type": "Microsoft.DataFactory/factories/pipelines",
        "properties": {"activities": [], "description": "desc"},
    }
    p = pipeline_dir / f"{name}.json"
    p.write_text(json.dumps(resource), encoding="utf-8")
    return p


# ============================================================
# load_config
# ============================================================

class TestLoadConfig:

    def test_load_yaml_config(self, tmp_path):
        config = {"key": "value"}
        p = tmp_path / "config.yml"
        p.write_text(yaml.dump(config), encoding="utf-8")
        loaded = load_config(str(p))
        assert loaded == config

    def test_load_yaml_with_yaml_extension(self, tmp_path):
        config = {"key": "value"}
        p = tmp_path / "config.yaml"
        p.write_text(yaml.dump(config), encoding="utf-8")
        loaded = load_config(str(p))
        assert loaded == config

    def test_load_json_config(self, tmp_path):
        config = {"key": "value"}
        p = tmp_path / "config.json"
        p.write_text(json.dumps(config), encoding="utf-8")
        loaded = load_config(str(p))
        assert loaded == config

    def test_unsupported_extension_raises(self, tmp_path):
        p = tmp_path / "config.txt"
        p.write_text("content", encoding="utf-8")
        with pytest.raises(ValueError, match="Config must be"):
            load_config(str(p))


# ============================================================
# init command
# ============================================================

class TestInitCommand:

    def test_init_creates_adf_linter_directory(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            assert Path(".adf-linter").is_dir()

    def test_init_prints_success_message(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init"])
            assert "Initialized" in result.output

    def test_init_idempotent_when_directory_exists(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0


# ============================================================
# lint command
# ============================================================

class TestLintCommand:

    # --- Config errors ---

    def test_lint_missing_config_exits_1(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                ["lint", "--config", "nonexistent.yml", "--resources", str(tmp_path)],
            )
            assert result.exit_code == 1
            assert "Config not found" in result.output

    def test_lint_invalid_config_extension_exits_1(self, tmp_path):
        bad_config = tmp_path / "config.txt"
        bad_config.write_text("content", encoding="utf-8")
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                ["lint", "--config", str(bad_config), "--resources", str(tmp_path)],
            )
            assert result.exit_code == 1
            assert "Failed to load config" in result.output

    def test_lint_empty_config_exits_1(self, tmp_path):
        empty_config = tmp_path / "config.yml"
        empty_config.write_text("", encoding="utf-8")  # null/None YAML
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                ["lint", "--config", str(empty_config), "--resources", str(tmp_path)],
            )
            assert result.exit_code == 1
            assert "Config is empty or invalid" in result.output

    # --- No resources ---

    def test_lint_no_resource_files_exits_0(self, tmp_path):
        config_path = _write_config(tmp_path)
        resources_path = tmp_path / "resources"
        resources_path.mkdir()
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                [
                    "lint",
                    "--config", str(config_path),
                    "--resources", str(resources_path),
                ],
            )
            assert result.exit_code == 0
            assert "No resources found" in result.output

    # --- Passing lint ---

    def test_lint_valid_pipeline_exits_0(self, tmp_path):
        config_path = _write_config(tmp_path)
        resources_path = tmp_path / "resources"
        _write_pipeline(resources_path)
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                [
                    "lint",
                    "--config", str(config_path),
                    "--resources", str(resources_path),
                ],
            )
            assert result.exit_code == 0
            assert "All resources passed" in result.output

    def test_lint_creates_results_json(self, tmp_path):
        config_path = _write_config(tmp_path)
        resources_path = tmp_path / "resources"
        _write_pipeline(resources_path)
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(
                cli,
                [
                    "lint",
                    "--config", str(config_path),
                    "--resources", str(resources_path),
                ],
            )
            assert Path(".adf-linter/linter_results.json").exists()

    def test_lint_results_json_is_valid_json(self, tmp_path):
        config_path = _write_config(tmp_path)
        resources_path = tmp_path / "resources"
        _write_pipeline(resources_path)
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(
                cli,
                [
                    "lint",
                    "--config", str(config_path),
                    "--resources", str(resources_path),
                ],
            )
            with open(".adf-linter/linter_results.json", encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, dict)

    # --- Failing lint ---

    def test_lint_invalid_pipeline_exits_1(self, tmp_path):
        config_path = _write_config(tmp_path)
        resources_path = tmp_path / "resources"
        _write_pipeline(resources_path, name="bad_pipeline_name")
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                [
                    "lint",
                    "--config", str(config_path),
                    "--resources", str(resources_path),
                ],
            )
            assert result.exit_code == 1
            assert "errors found" in result.output

    def test_lint_invalid_pipeline_errors_in_results_json(self, tmp_path):
        config_path = _write_config(tmp_path)
        resources_path = tmp_path / "resources"
        _write_pipeline(resources_path, name="bad_pipeline_name")
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(
                cli,
                [
                    "lint",
                    "--config", str(config_path),
                    "--resources", str(resources_path),
                ],
            )
            with open(".adf-linter/linter_results.json", encoding="utf-8") as f:
                data = json.load(f)
            assert len(data) > 0

    # --- fail-fast flag ---

    def test_lint_fail_fast_exits_on_first_error(self, tmp_path):
        config_path = _write_config(tmp_path)
        resources_path = tmp_path / "resources"
        # Write two invalid pipelines
        _write_pipeline(resources_path, name="bad_name_one")
        _write_pipeline(resources_path, name="bad_name_two")
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                [
                    "lint",
                    "--config", str(config_path),
                    "--resources", str(resources_path),
                    "--fail-fast",
                ],
            )
            assert result.exit_code == 1

    # --- Summary output ---

    def test_lint_summary_printed(self, tmp_path):
        config_path = _write_config(tmp_path)
        resources_path = tmp_path / "resources"
        _write_pipeline(resources_path)
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                [
                    "lint",
                    "--config", str(config_path),
                    "--resources", str(resources_path),
                ],
            )
            assert "Summary" in result.output
            assert "Pipeline" in result.output

    # --- Malformed JSON resource ---

    def test_lint_malformed_resource_json_continues(self, tmp_path):
        config_path = _write_config(tmp_path)
        resources_path = tmp_path / "resources"
        pipeline_dir = resources_path / "pipeline"
        pipeline_dir.mkdir(parents=True)
        (pipeline_dir / "bad.json").write_text("{not valid json", encoding="utf-8")
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                [
                    "lint",
                    "--config", str(config_path),
                    "--resources", str(resources_path),
                ],
            )
            # Should report parse error but continue (not crash)
            assert "Failed to parse" in result.output

    # --- Multiple resource types ---

    def test_lint_counts_multiple_resource_types(self, tmp_path):
        config_path = _write_config(tmp_path)
        resources_path = tmp_path / "resources"

        # Pipeline
        _write_pipeline(resources_path)

        # Dataset
        ds_dir = resources_path / "dataset"
        ds_dir.mkdir(parents=True, exist_ok=True)
        (ds_dir / "DS_ADLS_ORDERS_CSV.json").write_text(
            json.dumps({
                "name": "DS_ADLS_ORDERS_CSV",
                "properties": {
                    "typeProperties": {},
                    "linkedServiceName": {"referenceName": "LS_ADLS"},
                },
            }),
            encoding="utf-8",
        )

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                [
                    "lint",
                    "--config", str(config_path),
                    "--resources", str(resources_path),
                ],
            )
            assert "Pipeline" in result.output
            assert "Dataset" in result.output
