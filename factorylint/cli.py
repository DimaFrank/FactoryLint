import click 
import os
import json


CONFIG_FILE = "./.adf-linter/config.json"
EXECUTIONS_RESULTS_FILE = "./.adf-linter/linter_results.json"


@click.group()
def cli():
    """FactoryLint CLI"""
    pass


@cli.command()
def init():
    """Initialize the FactoryLint directory and set up a connector."""
    dir_path = './.adf-linter'

    # Step 1: Create directory
    if os.path.exists(dir_path):
        click.secho(f"Directory '{dir_path}' already exists.", fg='yellow')
    else:
        try:
            os.mkdir(dir_path)
            click.secho("=" * 60, fg='cyan')
            click.secho("🎉 Welcome to FactoryLinter! 🎉", fg='green', bold=True)
            click.secho("Start your journey to perfect ADF naming conventions...", fg='blue')
            click.secho("-" * 60, fg='cyan')
            click.secho("📁 Directory '.adf-linter' created successfully.", fg='green')

            click.secho("🛠  You can now start adding rules with:", fg='blue')
            click.secho("    factorylint add --rule <rule_name>", fg='white')
            click.secho("=" * 60, fg='cyan')

        except Exception as e:
            click.secho(f"❌ Failed to create directory: {e}", fg='red')
            return


def all_rules():
    """Show all defined rules."""
    click.secho("📜 Defined Rules:", fg='blue')
    click.secho("-" * 60, fg='cyan')
    # Here you would typically load and display the rules from a file or database
    click.secho("No rules defined yet.", fg='yellow')


if __name__ == "__main__":
    cli()