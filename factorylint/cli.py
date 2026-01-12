import click
import os
import json
import glob
import yaml
import os
from pathlib import Path

from factorylint.core import linter
from factorylint.core import config_validator
from factorylint.core.linter import ADFResourceType


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_FILE = f"{PROJECT_ROOT}/config.yml"
EXECUTIONS_RESULTS_FILE = f"{PROJECT_ROOT}/.adf-linter/linter_results.json"


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        if path.endswith((".yml", ".yaml")):
            return yaml.safe_load(f)
        elif path.endswith(".json"):
            return json.load(f)
        else:
            raise ValueError("Config must be .json, .yml or .yaml")


@click.group()
def cli():
    """FactoryLint CLI - Validate ADF resources naming conventions"""
    pass


@cli.command()
def init():
    dir_path = f"{PROJECT_ROOT}/.adf-linter"
    os.makedirs(dir_path, exist_ok=True)
    click.secho("✅ Initialized .adf-linter directory", fg="green")


@cli.command()
@click.option("--config", "config_path", default=DEFAULT_CONFIG_FILE, show_default=True)
@click.option("--resources", "resources_path", required=True)
@click.option("--fail-fast", is_flag=True)
@click.pass_context
def lint(ctx, config_path, resources_path, fail_fast):

    if not os.path.exists(config_path):
        click.secho(f"❌ Config not found: {config_path}", fg="red")
        ctx.exit(1)
    try:
        rules_config = load_config(config_path)
    except Exception as e:
        click.secho(f"❌ Failed to load config: {e}", fg="red")
        ctx.exit(1)

    if not isinstance(rules_config, dict):
        click.secho("❌ Config is empty or invalid", fg="red")
        ctx.exit(1)

    errors = config_validator.validate_rules_config(rules_config)
    if errors:
        for e in errors:
            click.secho(f"❌ {e}", fg="red")
        ctx.exit(1)

    subfolders = ["pipeline", "dataset", "linkedService", "trigger"]
    resource_files = []

    for folder in subfolders:
        resource_files.extend(
            glob.glob(os.path.join(resources_path, folder, "**", "*.json"), recursive=True)
        )

    if not resource_files:
        click.secho("⚠️ No resources found", fg="yellow")
        ctx.exit(0)

    all_results = {}
    total_errors = 0

    resource_count = {
        r.value: 0 for r in ADFResourceType if r != ADFResourceType.UNKNOWN
    }
     
    for file in resource_files:
        full_resource_path = os.path.join(PROJECT_ROOT, file)
        
        with open(full_resource_path, encoding="utf-8") as f:
            try:
                resource_json = json.load(f)
            except Exception as e:
                click.secho(f"❌ Failed to parse {file}: {e}", fg="red")
                continue

        resource_type = linter.identify_adf_resource(resource_json)
        resource_count[resource_type.value] += 1

        errors = linter.lint_resource(full_resource_path, resource_type)

        if errors:
            total_errors += len(errors)
            all_results[file] = errors
            click.secho(f"\n❌ {file}", fg="red", bold=True)
            for err in errors:
                click.secho(f"   - {err}", fg="red")
            if fail_fast:
                ctx.exit(1)
        else:
            click.secho(f"✅ {file}", fg="green")

    os.makedirs(os.path.dirname(EXECUTIONS_RESULTS_FILE), exist_ok=True)
    with open(EXECUTIONS_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    click.secho("\n📊 Summary", fg="cyan", bold=True)
    for rtype, count in resource_count.items():
        click.secho(f" - {rtype}: {count}")

    if total_errors:
        click.secho(f"\n❌ {total_errors} errors found", fg="red", bold=True)
        ctx.exit(1)

    click.secho("\n🎉 All resources passed linting!", fg="green", bold=True)


if __name__ == "__main__":
    cli()
