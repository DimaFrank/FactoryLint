# FactoryLint – Configuration Reference

The rules config is a YAML (or JSON) file passed to `factorylint lint --config <path>`.  
The default file is [`factorylint.yml`](../factorylint.yml) at the project root.

---

## Top-level structure

```yaml
version: <number>
description: <string>

resources:
  pipelines:     { ... }
  datasets:      { ... }
  linked_services: { ... }
  triggers:      { ... }
  integration_runtimes: { ... }

parameters:   { ... }
variables:    { ... }
annotations:  { ... }
```

Only keys present in the config are validated. Any resource block with `enabled: false` is skipped entirely.

---

## `resources.pipelines`

```yaml
resources:
  pipelines:
    enabled: true
    description: "Human-readable description"
    naming:
      prefix: "PL_"
      case: "upper"               # upper | lower | any
      separator: "_"
      pattern: "^PL_[A-Z0-9_]+$" # full regex match
      min_separated_parts: 4
      max_separated_parts: 6
      allowed_actions:            # validates the last name segment
        - INGEST
        - TRANSFORM
        - ORCHESTRATE
        - LOAD
        - COPY
        - EXTRACT
        - PROCESS
      description_required: true  # pipeline JSON must have a non-empty description
      ignore_folder: "_Config"    # skip pipelines whose folder path contains this string
```

**Checks performed:**
| Check | Config key | Condition |
|-------|-----------|-----------|
| Non-empty description | `description_required` | Pipeline JSON must have a non-empty top-level `description` field |
| Regex pattern | `pattern` | Full `re.match` against the pipeline name |
| Case | `case` | `upper` / `lower` |
| Prefix | `prefix` | `name.startswith(prefix)` |
| Part count | `min_separated_parts`, `max_separated_parts` | `len(name.split(separator))` in range |
| Last segment | `allowed_actions` | Last segment after splitting by `separator` |
| Parameters | see [`parameters`](#parameters) | Each parameter key validated |
| Variables | see [`variables`](#variables) | Each variable key validated |
| Annotations | see [`annotations`](#annotations) | `properties.annotations` list validated |
| Folder skip | `ignore_folder` | Skipped (not an error) if folder path contains the string |

---

## `resources.datasets`

```yaml
resources:
  datasets:
    enabled: true
    naming:
      prefix: "DS"
      separator: "_"
      case: "upper"
      pattern: "^[A-Z0-9_]+$"
      required_source_position: 2   # 1-indexed position of the source abbreviation
      allowed_source_abbreviations: # map of human name → abbreviation
        "Azure Data Lake Storage Gen2": ADLS
        "Azure SQL Database": ASQL
        # ... (see factorylint.yml for full list)
      allowed_formats:              # validates the last name segment
        - CSV
        - TABLE
        - PARQUET
        - JSON
        - EXCEL
        - AVRO
        - BIN
        - XML
        - ORC
      min_separated_parts: 4
      max_separated_parts: 8
```

**Checks performed:**
| Check | Config key | Condition |
|-------|-----------|-----------|
| Regex pattern | `pattern` | Full `re.match` |
| Case | `case` | `upper` / `lower` |
| Prefix | `prefix` | `name.startswith(prefix)` |
| Format (last segment) | `allowed_formats` | Last segment after splitting by `separator` |
| Part count | `min_separated_parts`, `max_separated_parts` | `len(name.split(separator))` in range |
| Source abbreviation | `allowed_source_abbreviations`, `required_source_position` | Segment at `required_source_position - 1` must be in the map values |
| Parameters | see [`parameters`](#parameters) | Each parameter key validated |

**Expected name structure:**  `DS_<SOURCE>_<DETAIL>_<FORMAT>`  
Example: `DS_ADLS_CUSTOMERS_CSV`

---

## `resources.linked_services`

```yaml
resources:
  linked_services:
    enabled: true
    naming:
      prefix: "LS_"
      case: "upper"
      pattern: "^[A-Z0-9_]+$"
      separator: "_"
      min_separated_parts: 2
      max_separated_parts: 5
      allowed_abbreviations:    # validates the second name segment
        - ADLS
        - ASQL
        - KV
        - BLOB
        # ... (see factorylint.yml for full list)
```

**Checks performed:**
| Check | Config key | Condition |
|-------|-----------|-----------|
| Prefix | `prefix` | `name.startswith(prefix)` |
| Case | `case` | `upper` / `lower` |
| Regex pattern | `pattern` | Full `re.match` |
| Part count | `min_separated_parts`, `max_separated_parts` | `len(name.split(separator))` in range |
| Abbreviation (2nd segment) | `allowed_abbreviations` | `parts[1]` must be in the list |

**Expected name structure:** `LS_<ABBR>_<DESCRIPTION>`  
Example: `LS_ADLS_DATALAKE`

---

## `resources.triggers`

```yaml
resources:
  triggers:
    enabled: true
    naming:
      prefix: "TR_"
      separator: "_"
      case: "upper"
      pattern: "^[A-Z0-9_]+$"
      min_separated_parts: 4
      max_separated_parts: 7
      allowed_types:          # validates the second name segment
        - SCHEDULE
        - EVENT
      allowed_frequencies:    # validates the third name segment
        - HOURLY
        - DAILY
        - NIGHTLY
        - WEEKLY
        - MONTHLY
        - QUARTERLY
        - REALTIME
```

**Checks performed:**
| Check | Config key | Condition |
|-------|-----------|-----------|
| Prefix | `prefix` | `name.startswith(prefix)` |
| Case | `case` | `upper` only (`lower` not checked for triggers) |
| Regex pattern | `pattern` | Full `re.match` |
| Part count | `min_separated_parts`, `max_separated_parts` | `len(name.split(separator))` in range |
| Type (2nd segment) | `allowed_types` | `parts[1]` must be in the list |
| Frequency (3rd segment) | `allowed_frequencies` | `parts[2]` must be in the list |
| Annotations | see [`annotations`](#annotations) | `properties.annotations` list validated |

**Expected name structure:** `TR_<TYPE>_<FREQUENCY>_<DESCRIPTION>`  
Example: `TR_SCHEDULE_DAILY_MES_IOT`

---

## `resources.integration_runtimes`

```yaml
resources:
  integration_runtimes:
    enabled: false   # disabled by default
    naming:
      prefix: "IR_"
      case: "upper"
      pattern: "^[A-Z0-9_]+$"
      allowed_types:
        - SHIR
        - AZURE
      min_separated_parts: 2
      max_separated_parts: 5
```

Disabled by default. Set `enabled: true` to activate.

---

## `parameters`

Applied to **pipeline** and **dataset** parameter keys when `enabled: true`.

```yaml
parameters:
  enabled: true
  naming:
    prefix: "p_"
    case: "lower"
    pattern: "^[a-z_][a-z0-9_]*$"
```

Checks each parameter key in `properties.parameters` against `pattern`, `case`, and `prefix`.

---

## `variables`

Applied to **pipeline** variable keys when `enabled: true`.

```yaml
variables:
  enabled: true
  naming:
    prefix: "v_"
    case: "lower"
    pattern: "^[a-z_][a-z0-9_]*$"
```

Checks each variable key in `properties.variables` against `pattern`, `case`, and `prefix`.

---

## `annotations`

Enforces that ADF resources carry a required set of key-value annotation strings.  
Annotations in ADF are stored as a flat `list[str]` under `properties.annotations` (e.g. `["domain:finance", "owner:bob", "tier:1"]`).

Applies to any resource type listed in `applies_to`.

```yaml
annotations:
  enabled: true
  required: true     # reserved for future use; categories.*.required controls per-category enforcement
  min_count: 3       # minimum total number of annotations the resource must have
  applies_to:
    - pipelines
    - triggers
  categories:
    <category_name>:
      prefix: "domain:"          # annotation must start with this string
      required: true             # missing annotation for this category is an error
      allowed_values:            # full annotation string must be one of these
        - "domain:finance"
        - "domain:supply-chain"
        - "domain:hr"
        - "domain:ops"
        - "domain:mes"
      pattern: "^domain:..."     # alternative or additional regex check (optional)
```

### Category config keys

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `prefix` | string | ✅ | String the annotation must start with to belong to this category |
| `required` | boolean | ❌ | If `true`, at least one annotation with this prefix must be present |
| `allowed_values` | list[str] | ❌ | Full annotation string must be one of these (exact match) |
| `pattern` | string | ❌ | Full annotation string must match this regex |

> `allowed_values` and `pattern` can coexist; both checks run if both are defined.  
> `allowed_values` uses full strings including the prefix: `"domain:finance"`, not `"finance"`.

### Validation rules

| Rule | Error produced |
|------|---------------|
| Total annotations < `min_count` | `Resource must have at least N annotation(s), found M` |
| Annotation doesn't match any category prefix | `Unknown annotation(s) not matching any configured category: [...]` |
| Required category missing | `Required annotation category '<name>' (prefix '...') is missing` |
| Category appears more than once | `Annotation category '<name>' must appear exactly once, found N: [...]` |
| Value not in `allowed_values` | `Annotation '...' is not an allowed value for category '<name>'. Allowed: [...]` |
| Value doesn't match `pattern` | `Annotation '...' does not match pattern '...' for category '<name>'` |

### Default categories (from `factorylint.yml`)

| Category | Prefix | Required | Validation |
|----------|--------|----------|------------|
| `domain` | `domain:` | ✅ | `allowed_values`: finance, supply-chain, hr, ops, mes |
| `owner` | `owner:` | ✅ | `pattern`: `^owner:[a-z][a-z0-9-]+$` |
| `tier` | `tier:` | ✅ | `allowed_values`: tier:1, tier:2, tier:3 |
| `pii` | `pii:` | ❌ | `allowed_values`: pii:true, pii:false |

---

## Naming config key reference

The following keys are available inside any `naming:` block (not all apply to every resource type):

| Key | Type | Description |
|-----|------|-------------|
| `prefix` | string | Name must start with this string |
| `case` | `upper` \| `lower` \| `any` | Case requirement for the whole name |
| `separator` | string | Character used to split name into parts (default: `_`) |
| `pattern` | string | Full Python regex that the name must match (`re.match`) |
| `min_separated_parts` | int | Minimum number of parts after splitting by `separator` |
| `max_separated_parts` | int | Maximum number of parts after splitting by `separator` |
| `allowed_actions` | list[str] | Valid values for the last segment (pipelines only) |
| `allowed_types` | list[str] | Valid values for the second segment (triggers, integration runtimes) |
| `allowed_frequencies` | list[str] | Valid values for the third segment (triggers only) |
| `allowed_abbreviations` | list[str] | Valid values for the second segment (linked services only) |
| `allowed_source_abbreviations` | dict | Map of service name → abbreviation; second segment (datasets only) |
| `required_source_position` | int | 1-indexed position of the source abbreviation (datasets only, default: `2`) |
| `allowed_formats` | list[str] | Valid values for the last segment (datasets only) |
| `description_required` | boolean | Pipeline JSON must have a non-empty `description` field |
| `ignore_folder` | string | Skip (without error) pipelines whose `folder.name` contains this string |
