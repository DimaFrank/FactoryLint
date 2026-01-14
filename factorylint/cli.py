import click
import os
import json
import glob
import yaml
from pathlib import Path

from factorylint.core import linter
from factorylint.core import config_validator
from factorylint.core.linter import ADFResourceType


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
    Path(".adf-linter").mkdir(exist_ok=True)
    click.secho("✅ Initialized .adf-linter directory", fg="green")


@cli.command()
@click.option("--config", "config_path", required=True)
@click.option("--resources", "resources_path", required=True)
@click.option("--fail-fast", is_flag=True)
@click.pass_context
def lint(ctx, config_path, resources_path, fail_fast):
    """
    Lint Azure Data Factory resources
    """

    config_path = Path(config_path).resolve()
    resources_path = Path(resources_path).resolve()

    if not config_path.exists():
        click.secho(f"❌ Config not found: {config_path}", fg="red")
        ctx.exit(1)

    try:
        rules_config = load_config(str(config_path))
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
    resource_files: list[Path] = []

    for folder in subfolders:
        resource_files.extend(
            resources_path.glob(f"{folder}/**/*.json")
        )

    if not resource_files:
        click.secho("⚠️ No resources found", fg="yellow")
        ctx.exit(0)

    all_results: dict = {}
    total_errors = 0

    resource_count = {
        r.value: 0 for r in ADFResourceType if r != ADFResourceType.UNKNOWN
    }

    for file_path in resource_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                resource_json = json.load(f)
        except Exception as e:
            click.secho(f"❌ Failed to parse {file_path}: {e}", fg="red")
            continue

        resource_type = linter.identify_adf_resource(resource_json)
        resource_count[resource_type.value] += 1

        errors, skipped = linter.lint_resource(
            resource_path=str(file_path),
            resource_type=resource_type,
            rules=rules_config,
        )

        relative_path = file_path.relative_to(resources_path)

        if errors:
            total_errors += len(errors)
            all_results[str(relative_path)] = errors

            click.secho(f"\n❌ {relative_path}", fg="red", bold=True)
            for err in errors:
                click.secho(f"   - {err}", fg="red")

            if fail_fast:
                ctx.exit(1)
        else:
            for skipped_name in skipped:
                click.secho(f"⚠️ Skipped {skipped_name} due to ignore_folder rule", fg="yellow")
            click.secho(f"✅ {relative_path}", fg="green")
            

    results_file = Path(".adf-linter/linter_results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, "w", encoding="utf-8") as f:
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
