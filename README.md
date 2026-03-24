<p align="left">
  <img src="https://raw.githubusercontent.com/DimaFrank/FactoryLint/master/logo.png" alt="FactoryLint Logo" width="700"/>
</p>

# 🏭 FactoryLint

**FactoryLint** is a Python CLI tool for **linting Azure Data Factory (ADF) resources** to ensure they follow **consistent, enforceable naming conventions**.

It validates **pipelines, datasets, linked services, triggers, parameters, and variables** using a **fully configurable rules file**, making it ideal for **CI/CD pipelines (Azure DevOps, GitHub Actions)** and team-wide governance.

---

## ✨ Features

- ✅ Lint ADF resources:
  - Pipelines
  - Datasets
  - Linked Services
  - Triggers
  - Pipeline & Dataset Parameters
  - Pipeline Variables
- ⚙️ **Fully configurable rules** via YAML or JSON
- 🧠 Automatic **ADF resource type detection**
- 📊 Clear, colorized **terminal output**
- 💾 Machine-readable **JSON report output**
- 🚀 Designed for **CI/CD usage**
- 🛠 Simple, predictable CLI interface

---

## 📦 Installation

### Install from PyPI

```bash
pip install factorylint
```

## Local development install
```bash
git clone https://github.com/DimaFrank/FactoryLint.git
cd FactoryLint
pip install -e .
```


## 🚀 Usage
Initialize project (optional)

Creates the .adf-linter directory used for repo
```bash
factorylint init
```

## Lint ADF resources

Run linting against a directory containing ADF resources.
```bash
factorylint lint --config ./factorylint.yml --resources .
```

| Option        | Description                                     |
| ------------- | ----------------------------------------------- |
| `--config`    | Path to rules configuration file (YAML or JSON) |
| `--resources` | Root directory containing ADF resources         |
| `--fail-fast` | Stop on first error                             |


## 🗂 Expected Folder Structure

FactoryLint automatically scans these subfolders under --resources:
```text
pipeline/
dataset/
linkedService/
trigger/
```
Each folder may contain nested subdirectories.

## 📝 Configuration

The configuration file defines naming and validation rules for each ADF resource type.

Supported formats: YAML (.yml, .yaml) or JSON

The config is validated before linting starts

Invalid configs fail the run immediately (CI-safe)

The default config file name is `factorylint.yml`.

All rules live under a top-level `resources:` key. Parameters and variables are configured at the top level.

### Naming rules reference

| Resource | Structure | Example |
|---|---|---|
| Pipeline | `PL_<PROJECT>_<ENTITY>_<ACTION>` | `PL_MES_ORDERS_INGEST` |
| Dataset | `DS_<SOURCE>_<DETAIL...>_<FORMAT>` | `DS_ADLS_CUSTOMERS_PARQUET` |
| Linked Service | `LS_<ABBR>_<DESCRIPTION...>` | `LS_ADLS_BRONZE` |
| Trigger | `TR_<TYPE>_<FREQUENCY>_<DESCRIPTION...>` | `TR_SCHEDULE_DAILY_MES_IOT` |
| Parameter | `p_<name>` (lowercase) | `p_start_date` |
| Variable | `v_<name>` (lowercase) | `v_row_count` |

### Example factorylint.yml

```yaml
resources:

  pipelines:
    enabled: true
    naming:
      prefix: "PL_"
      case: "upper"
      separator: "_"
      pattern: "^PL_[A-Z0-9_]+$"
      min_separated_parts: 4
      max_separated_parts: 6
      allowed_actions:
        - INGEST
        - TRANSFORM
        - ORCHESTRATE
        - LOAD
        - COPY
        - EXTRACT
        - PROCESS
      description_required: true
      ignore_folder: "_Config"

  datasets:
    enabled: true
    naming:
      prefix: "DS"
      separator: "_"
      case: "upper"
      pattern: "^[A-Z0-9_]+$"
      required_source_position: 2
      allowed_source_abbreviations:
        "Azure Data Lake Storage Gen2": ADLS
        "Azure SQL Database": ASQL
        "SAP Table": SAPT
        "File System": FILE
      allowed_formats:
        - CSV
        - PARQUET
        - TABLE
        - JSON
        - EXCEL
        - AVRO
        - BIN
        - XML
        - ORC
      min_separated_parts: 4
      max_separated_parts: 8

  linked_services:
    enabled: true
    naming:
      prefix: "LS_"
      case: "upper"
      pattern: "^[A-Z0-9_]+$"
      separator: "_"
      min_separated_parts: 2
      max_separated_parts: 5
      allowed_abbreviations:
        - ADLS
        - ASQL
        - KV
        - ADBR
        - FILE

  triggers:
    enabled: true
    naming:
      prefix: "TR_"
      separator: "_"
      case: "upper"
      pattern: "^[A-Z0-9_]+$"
      min_separated_parts: 4
      max_separated_parts: 7
      allowed_types:
        - SCHEDULE
        - EVENT
      allowed_frequencies:
        - HOURLY
        - DAILY
        - NIGHTLY
        - WEEKLY
        - MONTHLY

parameters:
  enabled: true
  naming:
    prefix: "p_"
    case: "lower"
    pattern: "^[a-z_][a-z0-9_]*$"

variables:
  enabled: true
  naming:
    prefix: "v_"
    case: "lower"
    pattern: "^[a-z_][a-z0-9_]*$"
```


## 📊 Output
Terminal output

FactoryLint provides clear, colorized feedback:
```text
❌ pipeline/PL_MES_ORDERS_RUN.json
   - Pipeline 'PL_MES_ORDERS_RUN' has invalid action 'RUN'. Allowed: ['INGEST', 'TRANSFORM', ...]
   - Parameter 'StartDate' must start with prefix 'p_'
✅ pipeline/PL_MES_ORDERS_INGEST.json
✅ dataset/DS_ADLS_CUSTOMERS_PARQUET.json
```


## JSON report

All linting errors are saved to:
```text
.adf-linter/linter_results.json
```

Example:
```json
{
  "pipeline/PL_MES_ORDERS_RUN.json": [
    "Pipeline 'PL_MES_ORDERS_RUN' has invalid action 'RUN'. Allowed: ['INGEST', 'TRANSFORM', ...]"
  ]
}
```

## 🔁 CI/CD Usage (Azure DevOps example)
```yaml
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.x'

- script: |
    pip install factorylint
    factorylint lint --config ./factorylint.yml --resources .
  displayName: 'Run FactoryLint'
```
- Exit code 1 if errors are found

- Perfect for gating PRs and enforcing standards


## 🧠 Design Principles

 - ❌ No hardcoded paths

- ❌ No assumptions about project layout outside --resources

- ✅ Fully installable CLI

- ✅ Deterministic behavior in CI

- ✅ Clear separation of CLI and core logic


## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.

