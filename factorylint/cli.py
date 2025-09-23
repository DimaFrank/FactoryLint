import click
import os
import json
import glob
from factorylint.core import linter
from factorylint.core import config_validator
import sys 

DEFAULT_CONFIG_FILE = "./.adf-linter/rules_config.json"
EXECUTIONS_RESULTS_FILE = "./.adf-linter/linter_results.json"


@click.group()
def cli():
    """FactoryLint CLI - Validate your ADF resources against naming conventions"""
    pass


@cli.command()
def init():
    """Initialize the FactoryLint directory"""
    dir_path = './.adf-linter'

    if os.path.exists(dir_path):
        click.secho(f"⚠️  Directory '{dir_path}' already exists.", fg='yellow')
    else:
        try:
            os.mkdir(dir_path)
            click.secho("=" * 60, fg='cyan')
            click.secho("🎉 Welcome to FactoryLint! 🎉", fg='green', bold=True)
            click.secho("Start your journey to perfect ADF naming conventions...", fg='blue')
            click.secho("-" * 60, fg='cyan')
            click.secho("📁 Directory '.adf-linter' created successfully.", fg='green')
            click.secho("=" * 60, fg='cyan')
        except Exception as e:
            click.secho(f"❌ Failed to create directory: {e}", fg='red')


@cli.command()
@click.option("--config", "config_path", default=DEFAULT_CONFIG_FILE, show_default=True, help="Path to rules_config.json")
@click.option("--resources", "resources_path", required=True, help="Path to resources folder (pipeline/, dataset/, linkedService/, trigger/)")
@click.option("--fail-fast", is_flag=True, help="Fail fast on first error")
@click.pass_context
def lint(ctx, config_path, resources_path, fail_fast):
    """
    Lint all ADF resources in a given path.
    """
    # --- Load config ---
    if not os.path.exists(config_path):
        click.secho(f"❌ Rules config file not found: {config_path}", fg="red")
        if fail_fast:
            ctx.exit(1)
        return

    with open(config_path, "r", encoding="utf-8") as f:
        rules_config = json.load(f)

    # --- Validate config ---
    errors = config_validator.validate_rules_config(rules_config)
    if errors:
        click.secho("❌ Config validation failed:", fg="red", bold=True)
        for e in errors:
            click.secho(f" - {e}", fg="red")
        if fail_fast:
            ctx.exit(1)
        return

    click.secho(f"✅ Using config: {config_path}", fg="green")

    # --- Collect only relevant resources ---
    subfolders = ["pipeline", "dataset", "linkedService", "trigger"]
    resource_files = []
    for folder in subfolders:
        path = os.path.join(resources_path, folder, "**", "*.json")
        resource_files.extend(glob.glob(path, recursive=True))

    if not resource_files:
        click.secho(f"⚠️  No JSON resources found under {resources_path} (only looking in {subfolders})", fg="yellow")
        if fail_fast:
            ctx.exit(1)
        return

    click.secho(f"🔍 Found {len(resource_files)} resources to lint", fg="cyan")

    all_results = {}
    total_errors = 0

    for file in resource_files:
        with open(file, "r", encoding="utf-8") as f:
            try:
                resource_json = json.load(f)
            except Exception as e:
                click.secho(f"❌ Failed to parse {file}: {e}", fg="red")
                continue

        errors = linter.lint_resource(resource_json)
        if errors:
            click.secho(f"\n❌ {file}", fg="red", bold=True)
            for err in errors:
                click.secho(f"   - {err}", fg="red")
            all_results[file] = errors
            total_errors += len(errors)
        else:
            click.secho(f"✅ {file} passed", fg="green")

    # --- Save results ---
    os.makedirs(os.path.dirname(EXECUTIONS_RESULTS_FILE), exist_ok=True)
    with open(EXECUTIONS_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    click.secho("\n" + "=" * 60, fg="cyan")
    if total_errors > 0:
        click.secho(f"❌ Linting completed with {total_errors} errors", fg="red", bold=True)
        click.secho(f"📄 Detailed report saved to {EXECUTIONS_RESULTS_FILE}", fg="yellow")
        if fail_fast:
            ctx.exit(1)
    else:
        click.secho("🎉 All resources passed linting!", fg="green", bold=True)
    click.secho("=" * 60, fg="cyan")


if __name__ == "__main__":
    cli()
