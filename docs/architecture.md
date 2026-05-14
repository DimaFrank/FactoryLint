# FactoryLint – Architecture

## Overview

FactoryLint is a Python CLI tool that lints Azure Data Factory (ADF) exported JSON resources against a user-supplied YAML/JSON rules config. It validates naming conventions, structural requirements, and annotation enforcement for pipelines, datasets, linked services, and triggers.

---

## Repository Layout

```
factorylint/
  cli.py                  # Click CLI entry point (init, lint commands)
  core/
    linter.py             # Resource type detection + validator dispatch
    validators.py         # BaseValidator + 4 concrete validators + helpers
    resources.py          # ResourceType enum (config key names)
    config_validator.py   # Pre-flight validation of the rules config file
  tests/                  # (empty – manual testing via df-sgbi-general-dev/)

docs/                     # This documentation
df-sgbi-general-dev/      # Sample ADF export used for manual testing
factorylint.yml           # Default rules configuration
pyproject.toml            # Package metadata and entry point
```

---

## Data Flow

```
factorylint lint --config factorylint.yml --resources ./df-sgbi-general-dev
        │
        ▼
  cli.py: load_config()
        │  loads YAML/JSON rules file
        ▼
  config_validator.validate_rules_config()
        │  pre-flight check: validates config shape, regex patterns
        │  exits 1 on error
        ▼
  cli.py: glob pipeline/**/*.json  dataset/**/*.json
               linkedService/**/*.json  trigger/**/*.json
        │
        ▼  (per file)
  linter.identify_adf_resource(resource_json)
        │  returns ADFResourceType enum value
        ▼
  linter.lint_resource(path, resource_type, rules)
        │  instantiates the correct *Validator
        │  calls validator.validate(path)
        │  returns (errors: List[str], skipped: List[str])
        ▼
  cli.py: collect results → print → write .adf-linter/linter_results.json
        │
        └─ exit 1 if any errors found (CI-safe)
```

---

## Module Descriptions

### `cli.py`

Entry point registered as the `factorylint` console script via `pyproject.toml`.

| Symbol | Kind | Description |
|--------|------|-------------|
| `cli` | Click group | Root command group |
| `init` | Click command | Creates `.adf-linter/` output directory |
| `lint` | Click command | Main linting command; accepts `--config`, `--resources`, `--fail-fast` |
| `load_config()` | function | Loads YAML or JSON config file into a dict |

**Options for `lint`:**

| Option | Required | Description |
|--------|----------|-------------|
| `--config` | ✅ | Path to the YAML/JSON rules config |
| `--resources` | ✅ | Root directory of exported ADF resources |
| `--fail-fast` | ❌ | Exit immediately on first error |

**Output:**
- Terminal: colourised per-resource pass/fail lines + summary
- File: `.adf-linter/linter_results.json` — a dict mapping relative file paths to lists of error strings

---

### `core/linter.py`

Handles resource type detection and validator dispatch.

#### `ADFResourceType` (Enum)

Singular values matching the ADF JSON `type` field.

| Member | Value |
|--------|-------|
| `PIPELINE` | `"Pipeline"` |
| `DATASET` | `"Dataset"` |
| `LINKED_SERVICE` | `"LinkedService"` |
| `TRIGGER` | `"Trigger"` |
| `UNKNOWN` | `"Unknown"` |

#### `identify_adf_resource(resource_json: dict) → ADFResourceType`

Two-pass detection strategy:
1. **Primary** – checks `resource_json["type"]` string suffix (e.g. `".../pipelines"`)
2. **Fallback** – inspects `properties` keys (`activities`, `linkedServiceName`, `connectVia`, `pipelines`)

#### `lint_resource(resource_path, resource_type, rules) → Tuple[List[str], List[str]]`

Dispatches to the correct validator via a `match` statement and returns `(errors, skipped)`.

---

### `core/validators.py`

Contains all validation logic.

#### Helper functions

| Function | Description |
|----------|-------------|
| `_validate_names(names, naming, entity_type)` | Validates a list of names (parameters, variables) against a flat `{pattern, case, prefix}` naming config |
| `_validate_annotations(annotations, rules)` | Validates a list of ADF annotation strings against the top-level `annotations:` config block |

#### `BaseValidator`

| Member | Description |
|--------|-------------|
| `__init__(resource_type, rules)` | Extracts `rules['resources'][resource_type.value]` into `self.rules` |
| `load_resource(path)` | Reads a JSON or YAML file; enforces UTF-8 encoding |
| `get_all_rules()` | Returns `self.rules` as a formatted JSON string |

#### Concrete validators

| Class | Resource | Checks |
|-------|----------|--------|
| `PipelineValidator` | Pipelines | description, pattern, case, prefix, separator/parts count, allowed actions, parameters, variables, annotations |
| `DatasetValidator` | Datasets | pattern, case, prefix, allowed formats, separator/parts count, source abbreviation position, parameters |
| `LinkedServiceValidator` | Linked Services | prefix, case, pattern, separator/parts count, allowed abbreviations |
| `TriggerValidator` | Triggers | prefix, case, pattern, separator/parts count, allowed types, allowed frequencies, annotations |

All `validate()` methods return `Tuple[List[str], List[str]]` → `(errors, skipped)`.

---

### `core/resources.py`

#### `ResourceType` (Enum)

Plural values used as keys into `rules['resources']`.

| Member | Value |
|--------|-------|
| `PIPELINE` | `"pipelines"` |
| `DATASET` | `"datasets"` |
| `LINKED_SERVICE` | `"linked_services"` |
| `TRIGGER` | `"triggers"` |
| `INTEGRATION_RUNTIME` | `"integration_runtimes"` |
| `UNKNOWN` | `"unknown"` |

> **Note:** Do not confuse `ResourceType` (plural, config keys) with `ADFResourceType` (singular, ADF JSON type field).

---

### `core/config_validator.py`

Pre-flight validation of the rules config before any linting begins.

| Function | Description |
|----------|-------------|
| `validate_rules_config(config)` | Top-level dispatcher; returns a list of error strings |
| `validate_annotations_config(annotations)` | Validates the `annotations:` block shape, types, and regex patterns |
| `validate_regex(pattern)` | Returns `True` if the string is a valid Python regex |

---

## Two Enum Types — Important Distinction

| Enum | Location | Values | Used for |
|------|----------|--------|----------|
| `ADFResourceType` | `linter.py` | Singular (`"Pipeline"`) | Detected from ADF JSON `type` field |
| `ResourceType` | `resources.py` | Plural (`"pipelines"`) | Keys into `rules['resources']` in the config |

---

## Output Files

| Path | Format | Description |
|------|--------|-------------|
| `.adf-linter/linter_results.json` | JSON object | Maps relative resource paths to lists of error strings. Empty dict if all pass. |

---

## Extending FactoryLint

To add a new resource type (e.g. Integration Runtimes):

1. Add a plural entry to `ResourceType` in `resources.py`
2. Add a singular entry to `ADFResourceType` in `linter.py`
3. Add detection logic to `identify_adf_resource()` in `linter.py`
4. Create a `*Validator(BaseValidator)` class in `validators.py`
5. Add a `case` branch in `lint_resource()` in `linter.py`
6. Add the resource config block under `resources:` in `factorylint.yml`

See [`validators.md`](validators.md) for the full validator API and [`configuration.md`](configuration.md) for the config schema.
