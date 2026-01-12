<p align="left">
  <img src="https://raw.githubusercontent.com/DimaFrank/FactoryLint/master/logo.png" alt="FactoryLint Logo" width="700"/>
</p>

# 🏭 FactoryLint

**FactoryLint** is a Python CLI tool for **linting Azure Data Factory (ADF) resources** to ensure they follow **consistent, enforceable naming conventions**.

It validates **pipelines, datasets, linked services, and triggers** using a **fully configurable rules file**, making it ideal for **CI/CD pipelines (Azure DevOps, GitHub Actions)** and team-wide governance.

---

## ✨ Features

- ✅ Lint ADF resources:
  - Pipelines
  - Datasets
  - Linked Services
  - Triggers
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
factorylint lint --config ./config.yml --resources .
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

Example config.yml

```yaml
Pipeline:
  enabled: true
  general_rules:
    min_parts: 3
    description_required: false
  types:
    master:
      naming:
        prefix: "PL_M_"
        case: upper
        separator: "_"
        pattern: "^PL_M_[A-Z0-9_]+$"
    sub:
      naming:
        prefix: "PL_S_"
        case: upper
        separator: "_"
        pattern: "^PL_S_[A-Z0-9_]+$"

Dataset:
  enabled: true
  naming:
    prefix: "DS_"
    case: upper
    separator: "_"
    pattern: "^DS_[A-Z0-9_]+$"
    min_separated_parts: 3
    max_separated_parts: 6
    allowed_formats:
      - PARQ
      - CSV
    allowed_source_abbreviations:
      AzureBlob: ABLB
      ADLS: ADLS

LinkedService:
  enabled: true
  naming:
    prefix: "LS_"
    case: upper
    separator: "_"
    min_separated_parts: 2
    max_separated_parts: 4
    allowed_abbreviations:
      - ABLB
      - ADLS

Trigger:
  enabled: true
  naming:
    prefix: "TR_"
    case: upper
    separator: "_"
    min_separated_parts: 3
    max_separated_parts: 5
    allowed_types:
      - SCH
      - EVT
```


## 📊 Output
Terminal output

FactoryLint provides clear, colorized feedback:
```text
❌ dataset/DS_INVALID_NAME.json
   - Dataset 'DS_INVALID_NAME' does not match pattern '^DS_[A-Z0-9_]+$'
✅ pipeline/PL_M_LOAD_CUSTOMERS.json
```


## JSON report

All linting errors are saved to:
```text
.adf-linter/linter_results.json
```

Example:
```text
{
  "dataset/DS_INVALID_NAME.json": [
    "Dataset 'DS_INVALID_NAME' does not match pattern '^DS_[A-Z0-9_]+$'"
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
    factorylint lint --config ./config.yml --resources .
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