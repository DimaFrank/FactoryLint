import json
import re

VALID_RESOURCE_TYPES = {"pipelines", "datasets", "linked_services", "triggers", "integration_runtimes"}

def validate_regex(pattern: str) -> bool:
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False


def validate_annotations_config(annotations: dict) -> list:
    """Validate the top-level annotations: block in the rules config."""
    errors = []

    if not isinstance(annotations, dict):
        return ["'annotations' must be a dictionary"]

    if not isinstance(annotations.get("enabled"), bool):
        errors.append("annotations.enabled must be a boolean")

    if "min_count" in annotations and not isinstance(annotations["min_count"], int):
        errors.append("annotations.min_count must be an integer")

    applies_to = annotations.get("applies_to", [])
    if not isinstance(applies_to, list):
        errors.append("annotations.applies_to must be a list")
    else:
        for rt in applies_to:
            if rt not in VALID_RESOURCE_TYPES:
                errors.append(f"annotations.applies_to contains unknown resource type '{rt}'")

    categories = annotations.get("categories", {})
    if not isinstance(categories, dict):
        errors.append("annotations.categories must be a dictionary")
    else:
        for cat_name, cat_cfg in categories.items():
            if not isinstance(cat_cfg, dict):
                errors.append(f"annotations.categories.{cat_name} must be a dictionary")
                continue
            if "prefix" not in cat_cfg or not isinstance(cat_cfg["prefix"], str):
                errors.append(f"annotations.categories.{cat_name} must have a 'prefix' string")
            if not isinstance(cat_cfg.get("required", False), bool):
                errors.append(f"annotations.categories.{cat_name}.required must be a boolean")
            if "allowed_values" in cat_cfg:
                if not isinstance(cat_cfg["allowed_values"], list):
                    errors.append(f"annotations.categories.{cat_name}.allowed_values must be a list")
            if "pattern" in cat_cfg:
                if not isinstance(cat_cfg["pattern"], str):
                    errors.append(f"annotations.categories.{cat_name}.pattern must be a string")
                elif not validate_regex(cat_cfg["pattern"]):
                    errors.append(f"annotations.categories.{cat_name}.pattern is not a valid regex: {cat_cfg['pattern']}")

    return errors


def validate_rules_config(config: dict) -> list:
    errors = []

    # ---- Annotations (top-level) ----
    if "annotations" in config:
        errors.extend(validate_annotations_config(config["annotations"]))

    # ---- Pipeline ----
    if "Pipeline" in config:
        pipeline = config["Pipeline"]
        if "patterns" not in pipeline or not isinstance(pipeline["patterns"], dict):
            errors.append("Pipeline must contain 'patterns' dict")
        else:
            for key, pattern in pipeline["patterns"].items():
                if not validate_regex(pattern):
                    errors.append(f"Invalid regex in Pipeline pattern '{key}': {pattern}")

    # ---- Trigger ----
    if "Trigger" in config:
        trigger = config["Trigger"]
        if not isinstance(trigger, dict):
            errors.append("Trigger must be a dictionary")
        else:
            for trig_type, trig_cfg in trigger.items():
                if "allowed_prefixes" not in trig_cfg or not isinstance(trig_cfg["allowed_prefixes"], list):
                    errors.append(f"Trigger '{trig_type}' must have 'allowed_prefixes' as a list")
                if "pattern" not in trig_cfg or not isinstance(trig_cfg["pattern"], str):
                    errors.append(f"Trigger '{trig_type}' must have 'pattern' as a string")
                elif not validate_regex(trig_cfg["pattern"]):
                    errors.append(f"Invalid regex in Trigger '{trig_type}' pattern: {trig_cfg['pattern']}")

    # ---- LinkedService ----
    if "LinkedService" in config:
        ls = config["LinkedService"]
        if "prefix" not in ls or not isinstance(ls["prefix"], str):
            errors.append("LinkedService must have 'prefix' string")
        if "allowed_abbreviations" not in ls or not isinstance(ls["allowed_abbreviations"], list):
            errors.append("LinkedService must have 'allowed_abbreviations' as a list")
        else:
            for i, entry in enumerate(ls["allowed_abbreviations"]):
                if not all(k in entry for k in ("Type", "Service", "Abbreviation")):
                    errors.append(f"LinkedService abbreviation entry {i+1} must contain Type, Service, Abbreviation")

    # ---- Dataset ----
    if "Dataset" in config:
        ds = config["Dataset"]
        if "prefix" not in ds or not isinstance(ds["prefix"], str):
            errors.append("Dataset must have 'prefix' string")
        if "formats" not in ds or not isinstance(ds["formats"], dict):
            errors.append("Dataset must have 'formats' dict")
        if "allowed_chars" not in ds or not isinstance(ds["allowed_chars"], str):
            errors.append("Dataset must have 'allowed_chars' regex string")
        elif not validate_regex(ds["allowed_chars"]):
            errors.append(f"Invalid regex in Dataset.allowed_chars: {ds['allowed_chars']}")
        if "allowed_abbreviations" not in ds or not isinstance(ds["allowed_abbreviations"], list):
            errors.append("Dataset must have 'allowed_abbreviations' as a list")
        else:
            for i, entry in enumerate(ds["allowed_abbreviations"]):
                if not all(k in entry for k in ("Type", "Service", "Abbreviation")):
                    errors.append(f"Dataset abbreviation entry {i+1} must contain Type, Service, Abbreviation")

    return errors


if __name__ == "__main__":
    with open("rules_config.json", "r", encoding="utf-8") as f:
        rules_config = json.load(f)

    errors = validate_rules_config(rules_config)
    if errors:
        print("❌ Config validation failed:")
        for e in errors:
            print(" -", e)
    else:
        print("✅ Config file is valid")
