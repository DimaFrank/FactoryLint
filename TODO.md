# 🧾 FactoryLint TODO

> A roadmap for improving and expanding the **FactoryLint** CLI — the Azure Data Factory resource linter.

## 🚀 Planned Enhancements


### 1. Rule Severity Levels (error / warning / info)

Allow each rule to define its **severity** for better flexibility in CI.

**Example Config:**
```json
{
  "pipeline_name_pattern": {
    "regex": "^[a-z0-9-]+$",
    "severity": "error"
  },
  "dataset_naming_convention": {
    "regex": "^ds_[a-z0-9_]+$",
    "severity": "warning"
  }
}
```

```python
⚠️ Warning: Dataset name 'DS_sales' should be lowercase (ds_sales)
❌ Error: Pipeline name 'MyPipeline' violates naming convention (mypipeline)
```

### 2. Add Rule Types Beyond Naming

- Include additional types of validation:

- Ensure every pipeline has a description.

- Check that linked services use Key Vault references.

- Validate dataset file types (e.g., .parquet for Parquet datasets).

- Enforce trigger name pattern like trg_<pipeline_name>.

- Check activity names case style (camel case, snake case etc.)


### 3. Configurable Ignore Patterns

Allow ignoring specific folders or resources.

Example:
```python
"ignore_patterns": [
  "_Config/**",
  "test/**",
  "experimental_*.json"
]
```


### 4. Add Summary by Resource Type (DONE)

Provide aggregated stats at the end of linting.

Example:
```python
Lint Summary:
- Pipelines checked: 25 (3 errors)
- Datasets checked: 10 (0 errors)
- Linked Services checked: 5 (1 error)
```


### 5. Markdown / HTML Report Output

Generate a report file (report.html or report.md) with all violations, saved under .adf-linter/.

Use case: Publish as an artifact in Azure DevOps.


### 6. Pre-commit Hook Integration

Add support for running linting as a pre-commit check (via pre-commit).

Example pre-commit config:
```yaml
- repo: local
  hooks:
    - id: factorylint
      name: FactoryLint
      entry: factorylint lint --resources factory/
      language: system
      pass_filenames: false
```


### 7. Custom Rule Plugin System

Enable teams to write their own Python rules.

Example Custom Rule:
```python
# .adf-linter/custom_rules/my_rules.py
def rule_pipeline_name_starts_with_prefix(resource_json):
    name = resource_json.get("name", "")
    if not name.startswith("pl_"):
        return "Pipeline name must start with 'pl_'"
```
Config Reference:
```json
"custom_rules": ["custom_rules/my_rules.py"]
```


### 8. Machine-readable Output (JSONL / SARIF)

Allow export in formats suitable for automation and dashboards.

Example:
```bash
factorylint lint --output-format sarif --output-file lint-results.sarif
```
Use case: Integrate with SonarQube, GitHub Code Scanning, or DevOps dashboards.


### 9. Auto-fix Mode (--fix)

Allow FactoryLint to automatically correct simple violations.

Example:
```bash
factorylint lint --fix
```
Fixes could include:

Renaming PL_sales.json → pl_sales.json

Rewriting dataset/SalesData.json → dataset/ds_sales_data.json


### 10. Exit Code Control

Add control over which severities should fail the build.

Examples:
```bash
--error-level error      # Fail only on errors
--error-level warning    # Fail also on warnings
```


### 11. Azure DevOps PR Comment Integration

Post linting results as a comment on Pull Request with:

- Summary of issues

- File-level details

- Link to full report artifact


### 12. Rule Coverage Metrics

Show which rules are most often triggered.

Example Output:
```bash
Rule Stats:
✔ pipeline_name_pattern: 24 passed / 3 failed
✔ dataset_naming_convention: 10 passed / 0 failed
```


### 13. YAML Config Support

Support both .json and .yaml config formats for readability and flexibility.


### 14. Emoji Summary / Friendly Output

Add positive and fun CLI summaries.

Example:
```bash
✨ All 40 ADF resources look perfect! Great job!
```
or
```bash
💥 5 naming issues found. Let's fix them before merging.
```

### 15. Interactive Mode

Add --interactive flag to fix or skip issues one by one during linting.