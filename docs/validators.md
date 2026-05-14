# FactoryLint – Validators Reference

This document describes every validator class and helper function in `factorylint/core/validators.py`.

---

## Helper Functions

### `_validate_names`

```python
def _validate_names(names: List[str], naming: dict, entity_type: str) -> List[str]
```

Validates a list of name strings against a flat naming config dict.  
Used internally by validators to check pipeline parameters and variables, and dataset parameters.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `names` | `List[str]` | List of names to validate (e.g. parameter or variable keys) |
| `naming` | `dict` | A naming config with optional `pattern`, `case`, `prefix` keys |
| `entity_type` | `str` | Label used in error messages (e.g. `"Parameter"`, `"Variable"`) |

**Returns:** `List[str]` — list of error messages (empty if all pass).

**Checks applied per name:**
1. `pattern` — `re.match(pattern, name)` must succeed
2. `case == "upper"` — `name == name.upper()`
3. `case == "lower"` — `name == name.lower()`
4. `prefix` — `name.startswith(prefix)`

---

### `_validate_annotations`

```python
def _validate_annotations(annotations: List[str], rules: dict) -> List[str]
```

Validates a list of ADF annotation strings against the top-level `annotations:` config block.

ADF annotations are stored as a flat list of strings under `properties.annotations`, e.g.:
```json
["domain:finance", "owner:bob-smith", "tier:1", "pii:false"]
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `annotations` | `List[str]` | Annotation strings from the ADF resource JSON |
| `rules` | `dict` | The top-level `annotations:` config block from the rules file |

**Returns:** `List[str]` — list of error messages (empty if all pass).

**Algorithm:**

1. Returns immediately (no errors) if `rules["enabled"]` is `False`.
2. Checks total count against `min_count`.
3. Builds a prefix → `[matching annotations]` map by iterating all annotations and matching them to known category prefixes.
4. Annotations not matching any category prefix are collected as "unknown" → error.
5. For each category in `categories`:
   - If `required: true` and no matches → error.
   - If more than one match → error (each category must appear at most once).
   - For the single match: validates against `allowed_values` (exact full-string match) and/or `pattern` (regex).

**Error messages produced:**

| Condition | Message |
|-----------|---------|
| Total < `min_count` | `Resource must have at least N annotation(s), found M` |
| No matching category prefix | `Unknown annotation(s) not matching any configured category: [...]` |
| Required category absent | `Required annotation category '<name>' (prefix '...') is missing` |
| Category duplicated | `Annotation category '<name>' must appear exactly once, found N: [...]` |
| Not in `allowed_values` | `Annotation '...' is not an allowed value for category '<name>'. Allowed: [...]` |
| Fails `pattern` | `Annotation '...' does not match pattern '...' for category '<name>'` |

---

## `BaseValidator`

```python
class BaseValidator:
    def __init__(self, resource_type: ResourceType, rules: dict)
    def load_resource(self, resource_path: str) -> dict
    def get_all_rules(self) -> str
```

Base class inherited by all four concrete validators.

### `__init__`

Slices the full rules config down to just the block for this resource type:

```python
self.rules = rules['resources'][resource_type.value]
```

### `load_resource(resource_path)`

Reads a JSON or YAML file and returns the parsed dict.  
Always opens files with `encoding="utf-8"` — raises `ValueError` on `UnicodeDecodeError`.

### `get_all_rules()`

Returns `self.rules` formatted as a JSON string (for debugging).

---

## `PipelineValidator`

```python
class PipelineValidator(BaseValidator):
    def __init__(self, rules: dict)
    def validate(self, pipeline_file_path: str) -> Tuple[List[str], List[str]]
```

Validates pipeline JSON files.

### `__init__`

```python
self.naming = self.rules.get("naming", {})
self.enabled = self.rules.get("enabled", True)
self.param_rules = rules.get("parameters", {})    # top-level parameters block
self.var_rules = rules.get("variables", {})        # top-level variables block
self.annotation_rules = rules.get("annotations", {})  # top-level annotations block
```

### `validate(pipeline_file_path)`

Returns `(errors, skipped)`.

**Validation sequence:**

| Step | Config key | Logic |
|------|-----------|-------|
| Skip if disabled | `enabled` | Returns `([], [])` immediately |
| Folder skip | `naming.ignore_folder` | If pipeline's `properties.folder.name` contains the string, adds name to `skipped` and returns early |
| Description | `naming.description_required` | Checks top-level `description` field is non-empty |
| Pattern | `naming.pattern` | `re.match` against pipeline name |
| Case | `naming.case` | `upper` / `lower` |
| Prefix | `naming.prefix` | `name.startswith(prefix)` |
| Part count | `naming.min_separated_parts`, `max_separated_parts` | `len(name.split(separator))` in range |
| Action (last segment) | `naming.allowed_actions` | `name.split(separator)[-1]` must be in the list |
| Parameters | `parameters.*` | Calls `_validate_names` on `properties.parameters` keys |
| Variables | `variables.*` | Calls `_validate_names` on `properties.variables` keys |
| Annotations | `annotations.*` | Calls `_validate_annotations` when `"pipelines"` is in `applies_to` |

---

## `DatasetValidator`

```python
class DatasetValidator(BaseValidator):
    def __init__(self, rules: dict)
    def validate(self, dataset_file_path: str) -> Tuple[List[str], List[str]]
```

Validates dataset JSON files.

### `__init__`

```python
self.naming = self.rules.get("naming", {})
self.enabled = self.rules.get("enabled", True)
self.param_rules = rules.get("parameters", {})
```

### `validate(dataset_file_path)`

**Validation sequence:**

| Step | Config key | Logic |
|------|-----------|-------|
| Skip if disabled | `enabled` | Returns `([], [])` immediately |
| Pattern | `naming.pattern` | `re.match` against dataset name |
| Case | `naming.case` | `upper` / `lower` |
| Prefix | `naming.prefix` | `name.startswith(prefix)` |
| Format (last segment) | `naming.allowed_formats` | `name.split(separator)[-1]` must be in the list |
| Part count | `naming.min_separated_parts`, `max_separated_parts` | `len(name.split(separator))` in range |
| Source abbreviation | `naming.allowed_source_abbreviations`, `naming.required_source_position` | Segment at position `required_source_position - 1` must be a value in the map |
| Parameters | `parameters.*` | Calls `_validate_names` on `properties.parameters` keys |

**Source abbreviation check detail:**  
`required_source_position` is 1-indexed. The validator compares `parts[required_source_position - 1]` against the **values** (abbreviations) in the `allowed_source_abbreviations` dict, not the keys.

---

## `LinkedServiceValidator`

```python
class LinkedServiceValidator(BaseValidator):
    def __init__(self, rules: dict)
    def validate(self, linked_service_file_path: str) -> Tuple[List[str], List[str]]
```

Validates linked service JSON files.

### `validate(linked_service_file_path)`

**Validation sequence:**

| Step | Config key | Logic |
|------|-----------|-------|
| Skip if disabled | `enabled` | Returns `([], [])` immediately |
| Missing name | — | Returns `["Linked Service name is missing"]` if name is empty |
| Prefix | `naming.prefix` | `name.startswith(prefix)` |
| Case | `naming.case` | `upper` / `lower` |
| Pattern | `naming.pattern` | `re.match` |
| Part count | `naming.min_separated_parts`, `max_separated_parts` | `len(name.split(separator))` in range |
| Abbreviation (2nd segment) | `naming.allowed_abbreviations` | `parts[1]` must be in the list |

---

## `TriggerValidator`

```python
class TriggerValidator(BaseValidator):
    def __init__(self, rules: dict)
    def validate(self, trigger_file_path: str) -> Tuple[List[str], List[str]]
```

Validates trigger JSON files.

### `__init__`

```python
self.naming = self.rules.get("naming", {})
self.enabled = self.rules.get("enabled", True)
self.annotation_rules = rules.get("annotations", {})
```

### `validate(trigger_file_path)`

**Validation sequence:**

| Step | Config key | Logic |
|------|-----------|-------|
| Skip if disabled | `enabled` | Returns `([], [])` immediately |
| Missing name | — | Returns error if name is empty |
| Prefix | `naming.prefix` | `name.startswith(prefix)` |
| Case | `naming.case` | `upper` only (lowercase branch not implemented for triggers) |
| Pattern | `naming.pattern` | `re.match` |
| Part count | `naming.min_separated_parts`, `max_separated_parts` | `len(name.split(separator))` in range |
| Type (2nd segment) | `naming.allowed_types` | `parts[1]` must be in the list |
| Frequency (3rd segment) | `naming.allowed_frequencies` | `parts[2]` must be in the list |
| Annotations | `annotations.*` | Calls `_validate_annotations` when `"triggers"` is in `applies_to` |

---

## Return types

All `validate()` methods return `Tuple[List[str], List[str]]`:

| Index | Name | Contents |
|-------|------|----------|
| `[0]` | `errors` | Error messages — each is a human-readable string describing one violation |
| `[1]` | `skipped` | Resource names skipped due to `ignore_folder` (pipelines only) |

A resource is considered **passing** when `errors` is empty, regardless of `skipped`.

---

## Adding a new validator

1. Add the plural resource type to `ResourceType` in `resources.py`
2. Add the singular type to `ADFResourceType` in `linter.py`
3. Add detection logic to `identify_adf_resource()` in `linter.py`
4. Subclass `BaseValidator`:
   ```python
   class MyValidator(BaseValidator):
       def __init__(self, rules: dict):
           super().__init__(ResourceType.MY_TYPE, rules)
           self.naming = self.rules.get("naming", {})
           self.enabled = self.rules.get("enabled", True)

       def validate(self, file_path: str) -> Tuple[List[str], List[str]]:
           errors, skipped = [], []
           if not self.enabled:
               return errors, skipped
           resource = self.load_resource(file_path)
           name = resource.get("name", "")
           # ... validation logic ...
           return errors, skipped
   ```
5. Add a `case` branch in `lint_resource()` in `linter.py`
6. Add the resource config block under `resources:` in `factorylint.yml`
