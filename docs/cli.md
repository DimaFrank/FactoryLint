# FactoryLint – CLI Reference

FactoryLint is installed as the `factorylint` console script (registered via `pyproject.toml`).

## Installation

```bash
# Development / editable install
pip install -e .

# From PyPI (when published)
pip install factorylint
```

Requires Python ≥ 3.9. Dependencies: `click >= 8.0.0`, `PyYAML >= 6.0.3`.

---

## Commands

### `factorylint init`

Creates the `.adf-linter/` output directory in the current working directory.

```
factorylint init
```

Run this once before the first lint. Safe to run multiple times (`exist_ok=True`).

**Output:**
```
✅ Initialized .adf-linter directory
```

---

### `factorylint lint`

Lints all ADF resources in a directory against a rules config file.

```
factorylint lint --config <config_path> --resources <resources_path> [--fail-fast]
```

**Options:**

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--config` | | ✅ | Path to the YAML or JSON rules config file |
| `--resources` | | ✅ | Root directory of exported ADF resources |
| `--fail-fast` | | ❌ | Exit with code 1 on the first file that has errors |

**Scanned subdirectories** (relative to `--resources`):

| Subdirectory | Resource type |
|-------------|---------------|
| `pipeline/**/*.json` | Pipelines |
| `dataset/**/*.json` | Datasets |
| `linkedService/**/*.json` | Linked Services |
| `trigger/**/*.json` | Triggers |

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | All resources passed |
| `1` | One or more errors found, config invalid, or config file not found |

**Terminal output:**

Each resource file is reported on a single line:

```
✅ pipeline\PL_MES_OBJECTS_INGEST.json
❌ pipeline\001_00_Master_MES_IoT.json
   - Pipeline '001_00_Master_MES_IoT' does not match pattern '^PL_[A-Z0-9_]+$'
   - Required annotation category 'domain' (prefix 'domain:') is missing
⚠️  Skipped PL_Config_Helper due to ignore_folder rule
```

A summary is printed at the end:

```
📊 Summary
 - Pipeline: 42
 - Dataset: 18
 - LinkedService: 12
 - Trigger: 9

❌ 37 errors found
```

**Output file:** `.adf-linter/linter_results.json`

A JSON object mapping relative resource paths to lists of error strings.  
Empty object `{}` if all resources pass.

```json
{
  "pipeline\\001_00_Master_MES_IoT.json": [
    "Pipeline '001_00_Master_MES_IoT' does not match pattern '^PL_[A-Z0-9_]+$'",
    "Required annotation category 'domain' (prefix 'domain:') is missing"
  ]
}
```

---

## CI / CD Integration

FactoryLint exits with code `1` when any errors are found, making it suitable as a CI step.

### GitHub Actions example

```yaml
- name: Lint ADF resources
  run: |
    pip install factorylint
    factorylint init
    factorylint lint --config factorylint.yml --resources ./adf-export
```

### Azure Pipelines example

```yaml
- script: |
    pip install factorylint
    factorylint init
    factorylint lint --config factorylint.yml --resources $(Build.SourcesDirectory)/adf-export
  displayName: Lint ADF resources
```

Use `--fail-fast` to stop at the first violation (useful for fast feedback in PR checks).

---

## Config file format

The rules config can be YAML (`.yml` / `.yaml`) or JSON (`.json`).  
See [`configuration.md`](configuration.md) for the full schema reference.

```bash
# YAML (recommended)
factorylint lint --config factorylint.yml --resources ./adf-export

# JSON
factorylint lint --config rules.json --resources ./adf-export
```
