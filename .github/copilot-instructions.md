# FactoryLint – Copilot Instructions

## Project Overview

FactoryLint is a Python CLI tool that lints Azure Data Factory (ADF) resources for naming convention compliance. It validates pipelines, datasets, linked services, and triggers against a user-supplied YAML/JSON rules config.

## Install & Run

```bash
# Local development install
pip install -e .

# Run linting against sample ADF resources
factorylint lint --config ./factorylint.yml --resources ./df-sgbi-general-dev

# Initialize the output directory
factorylint init
```

There is no test suite yet — the `factorylint/tests/` directory is empty. Manual testing uses the real ADF resources in `df-sgbi-general-dev/`.

## Architecture

```
factorylint/
  cli.py              # Click CLI entry point: `init` and `lint` commands
  core/
    linter.py         # Resource type detection + validator dispatch
    validators.py     # BaseValidator + 4 concrete validators
    resources.py      # ResourceType enum (plural values, matches config keys)
    config_validator.py  # Pre-flight validation of the rules config
```

**Data flow:** `cli.py` → loads config → `config_validator.validate_rules_config()` → scans JSON files → `linter.identify_adf_resource()` per file → dispatches to a `*Validator` → collects errors → writes `.adf-linter/linter_results.json` → exits 1 if any errors.

## Key Conventions

### Two resource type enums (do not confuse them)

- `ADFResourceType` (in `linter.py`) — singular values (`"Pipeline"`, `"Dataset"`, …). Used to represent what was detected from the ADF JSON `type` field.
- `ResourceType` (in `resources.py`) — plural values (`"pipelines"`, `"datasets"`, `"linked_services"`, …). Used as dict keys into `rules['resources'][resource_type.value]`.

### All validators share the same structure

All four validators (`PipelineValidator`, `DatasetValidator`, `LinkedServiceValidator`, `TriggerValidator`) follow the same pattern:
- Read `self.naming = self.rules.get("naming", {})` in `__init__`
- `validate()` returns `Tuple[List[str], List[str]]` — `(errors, skipped)`
- Config key under `resources:` is the plural `ResourceType` value (e.g. `pipelines`, `datasets`)

`PipelineValidator` additionally reads `description_required` and `ignore_folder` from `self.naming`.

### Config structure

The rules config must have this shape (YAML or JSON):

```yaml
resources:
  pipelines:    { enabled, naming: { pattern, case, prefix, separator, min_separated_parts, max_separated_parts, description_required, ignore_folder } }
  datasets:     { enabled, naming: { ... } }
  linked_services: { enabled, naming: { ... } }
  triggers:     { enabled, naming: { ... } }
```

All validators access config via `self.rules = rules['resources'][ResourceType.value]` — the `resources:` top-level key is mandatory.

### Validator pattern

All validators inherit from `BaseValidator`. To add a new resource type:
1. Add an entry to `ResourceType` in `resources.py` (use plural lowercase, matching the config key).
2. Add the corresponding `ADFResourceType` entry in `linter.py` (singular).
3. Create a `*Validator(BaseValidator)` in `validators.py`.
4. Add a `case` branch in `linter.lint_resource()`.

### `lint_resource` return type

Returns `Tuple[List[str], List[str]]` — `(errors, skipped)`. The `skipped` list contains resource names excluded by `ignore_folder` rules.

### ADF resource type detection

`identify_adf_resource()` first checks `resource_json["type"]` (e.g., `"Microsoft.DataFactory/factories/pipelines"`), then falls back to inspecting `properties` keys (`activities`, `linkedServiceName`, `connectVia`, `pipelines`).

### Output

- Terminal: colorized via `click.secho` with ✅/❌/⚠️ prefix.
- File: `.adf-linter/linter_results.json` — a dict mapping relative file paths to lists of error strings.
- Exit code 1 if any errors found (CI-safe).
