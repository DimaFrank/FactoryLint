<img src="logo.png" alt="image info" width="700"/>

# 🏭 FactoryLint

**FactoryLint** is a CLI tool to **lint your Azure Data Factory (ADF) resources** and ensure they follow consistent naming conventions. It checks **pipelines, datasets, linked services, and triggers**, and generates clear, visual reports.

---

## ✨ Features

- ✅ Lint ADF resources: **Pipeline, Dataset, Linked Service, Trigger**
- ⚙️ Fully **customizable rules** via `rules_config.json`
- 📊 **Visual error reports** in the terminal
- 💾 Saves **JSON reports** for further inspection
- 🛠 Easy CLI usage

---

## 📦 Installation

Install FactoryLint via `pip`:

```bash
pip install factorylint
```

Or install locally for development:

```bash
git clone <repo-url>
cd FactoryLint
pip install -e .
```

## 🚀 Usage
Initialize FactoryLint

Create the .adf-linter directory:
```bash
factorylint init
```
You’ll see a friendly welcome message and confirmation that the directory was created. 

## Lint ADF resources
Lint all ADF resources in a folder, using the default or custom configuration:
```bash
factorylint lint --resources /path/to/adf/resources
```
Specify a custom rules configuration:
```bash
factorylint lint --resources /path/to/adf/resources --config /path/to/rules_config.json
```


## 📝 Configuration
The **rules_config.json** file defines naming conventions for your ADF resources. You can edit this file to match your project standards. FactoryLint validates this file before linting.

Example structure:
```json
{
  "Pipeline": {
    "patterns": {
      "master": "^Master_.*$",
      "sub": "^Sub_.*$"
    }
  },
  "Dataset": {
    "prefix": "DS_",
    "formats": { "Parquet": "PARQ", "CSV": "CSV" },
    "allowed_chars": "^[A-Z0-9_]+$",
    "allowed_abbreviations": [
      { "Type": "Azure", "Service": "Blob Storage", "Abbreviation": "ABLB" }
    ]
  }
  // ... other rules
}
```


## 📊 Output

- Console: Colored, visual feedback for each resource 
- JSON report: Saved by default in .adf-linter/linter_results.json

Example: 
```pgsql
❌ dataset/DS_INVALID_NAME.json
   - Dataset detail part 'invalidName' must be uppercase letters, numbers or underscores only
✅ pipeline/Master_ExamplePipeline.json passed
```

## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.