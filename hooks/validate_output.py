#!/usr/bin/env python3
"""PostToolUse hook for Write tool: validate output files against schemas.

When a file is written to runs/*/intermediate/ or runs/*/reviews/,
checks if there's a matching JSON schema and validates the content.

Contract:
  - pass (or nothing to validate): exit 0, no output
  - violation: message on stderr + exit 2 (Claude Code feeds stderr back
    to the model as feedback on the completed Write)
  - internal hook error: exit 0 (fail-open — a hook bug must never wedge
    the pipeline)

Validation uses the `jsonschema` package (Draft-07) when available and
falls back to a shallow required-fields check when it is not installed.
"""

import json
import sys
import os

try:
    import jsonschema
except ImportError:
    jsonschema = None

# Map filename patterns to schema files
SCHEMA_MAP = {
    "literature_results.json": "evidence_result.json",
    "patent_results.json": "evidence_result.json",
    "scientific_review.json": "review_report.json",
    "compliance_review.json": "review_report.json",
    "writing_review.json": "review_report.json",
}

MAX_ERRORS = 10


def find_schema(filename):
    """Find the matching schema for a given output filename."""
    basename = os.path.basename(filename)

    if basename in SCHEMA_MAP:
        return SCHEMA_MAP[basename]

    if basename.endswith("_results.json"):
        return "evidence_result.json"
    if basename.endswith("_review.json") or "_review_" in basename:
        return "review_report.json"
    if basename.startswith("feedback_parse_") and basename.endswith(".json"):
        return "feedback_entry.json"
    if basename.startswith("feedback_patches_") and basename.endswith(".json"):
        return "feedback_patch.json"

    return None


def load_schema(schema_name):
    schemas_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schemas")
    schema_path = os.path.join(schemas_dir, schema_name)
    if not os.path.exists(schema_path):
        return None
    with open(schema_path) as f:
        return json.load(f)


def validate_against(data, schema, prefix=""):
    """Validate one object against a schema. Returns a list of error strings."""
    if jsonschema is not None:
        errors = []
        validator = jsonschema.Draft7Validator(schema)
        for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
            path = "/".join(str(p) for p in err.absolute_path) or "(root)"
            errors.append(f"{prefix}{path}: {err.message}")
            if len(errors) >= MAX_ERRORS:
                break
        return errors
    # Fallback: shallow required-fields check
    errors = []
    for field in schema.get("required", []):
        if field not in data:
            errors.append(f"{prefix}Missing required field: '{field}'")
    return errors


def validate_feedback_file(data, schema_name):
    """Array-typed feedback files: validate each entry/patch individually."""
    item_schema = load_schema(schema_name)
    if item_schema is None:
        return []
    if schema_name == "feedback_entry.json":
        key = "entries"
    else:
        key = "patches"
    if key not in data:
        return [f"missing required top-level key '{key}'"]
    errors = []
    for i, item in enumerate(data.get(key, [])):
        errors.extend(validate_against(item, item_schema, prefix=f"{key}[{i}]/"))
        if len(errors) >= MAX_ERRORS:
            break
    return errors[:MAX_ERRORS]


def fail(message):
    print(message, file=sys.stderr)
    sys.exit(2)


def main():
    hook_input = json.loads(sys.stdin.read())

    if hook_input.get("tool_name", "") != "Write":
        return

    file_path = hook_input.get("tool_input", {}).get("file_path", "")

    # Only validate JSON files in runs/*/intermediate/ or runs/*/reviews/
    if "/runs/" not in file_path:
        return
    if "/intermediate/" not in file_path and "/reviews/" not in file_path:
        return
    if not file_path.endswith(".json"):
        return
    if not os.path.exists(file_path):
        return

    schema_name = find_schema(file_path)
    if not schema_name:
        return

    try:
        with open(file_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        fail(f"Output file {os.path.basename(file_path)} is not valid JSON: {e}. "
             f"Rewrite the file as valid JSON conforming to schemas/{schema_name}.")

    if schema_name in ("feedback_entry.json", "feedback_patch.json"):
        errors = validate_feedback_file(data, schema_name)
    else:
        schema = load_schema(schema_name)
        errors = validate_against(data, schema) if schema else []

    if errors:
        fail(f"Schema validation failed for {os.path.basename(file_path)} "
             f"(schema: schemas/{schema_name}):\n"
             + "\n".join(f"  - {e}" for e in errors)
             + f"\nRewrite the file to conform to schemas/{schema_name}.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        # Fail open: a hook bug must never wedge the pipeline.
        sys.exit(0)
