# FactoryLint – Documentation

FactoryLint is a Python CLI tool that lints Azure Data Factory (ADF) exported JSON resources for naming convention compliance. It validates pipelines, datasets, linked services, and triggers against a user-supplied YAML/JSON rules config.

## Quick start

```bash
pip install -e .
factorylint init
factorylint lint --config factorylint.yml --resources ./df-sgbi-general-dev
```

---

## Documents

| Document | Description |
|----------|-------------|
| [architecture.md](architecture.md) | Project layout, data flow, module descriptions, all enums and public symbols |
| [configuration.md](configuration.md) | Full YAML config reference — every resource block, key, and annotation category |
| [validators.md](validators.md) | All validator classes and helper functions — signatures, logic, and error messages |
| [cli.md](cli.md) | CLI commands, options, exit codes, output format, and CI integration examples |

---

## At a glance

```
factorylint lint
        │
        ├─ loads config (YAML/JSON)
        ├─ pre-flight validates config → config_validator.py
        ├─ globs pipeline/ dataset/ linkedService/ trigger/ subdirs
        └─ per file:
              identify_adf_resource()   ← linter.py
              lint_resource()           ← linter.py
                    PipelineValidator   ← validators.py
                    DatasetValidator
                    LinkedServiceValidator
                    TriggerValidator
              collect errors → .adf-linter/linter_results.json
              exit 1 if any errors
```

## What is validated

| Resource | Naming | Annotations | Parameters/Variables |
|----------|--------|-------------|----------------------|
| Pipelines | prefix, case, pattern, parts, action, description, folder-skip | ✅ | ✅ |
| Datasets | prefix, case, pattern, parts, source abbreviation, format | — | ✅ |
| Linked Services | prefix, case, pattern, parts, abbreviation | — | — |
| Triggers | prefix, case, pattern, parts, type, frequency | ✅ | — |
