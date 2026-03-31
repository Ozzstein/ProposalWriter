#!/usr/bin/env python3
"""PostToolUse hook for Write tool: validate output files against schemas.

When a file is written to runs/*/intermediate/ or runs/*/reviews/,
checks if there's a matching JSON schema and validates the content.

Hook input (stdin): JSON with tool_name, tool_input, tool_output.
Hook output (stdout): JSON with warnings/errors if validation fails, or {}.
"""

import json
import sys
import os

# Map filename patterns to schema files
SCHEMA_MAP = {
    "literature_results.json": "evidence_result.json",
    "patent_results.json": "evidence_result.json",
    "scientific_review.json": "review_report.json",
    "compliance_review.json": "review_report.json",
    "writing_review.json": "review_report.json",
}


def find_schema(filename):
    """Find the matching schema for a given output filename."""
    basename = os.path.basename(filename)

    # Direct match
    if basename in SCHEMA_MAP:
        return SCHEMA_MAP[basename]

    # Pattern match: *_results.json -> evidence_result.json
    if basename.endswith("_results.json"):
        return "evidence_result.json"
    if basename.endswith("_review.json"):
        return "review_report.json"

    return None


def validate_required_fields(data, schema):
    """Simple validation: check required fields exist."""
    errors = []
    required = schema.get("required", [])
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")
    return errors


def main():
    hook_input = json.loads(sys.stdin.read())

    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Write":
        print(json.dumps({}))
        return

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only validate files in runs/*/intermediate/ or runs/*/reviews/
    if "/runs/" not in file_path:
        print(json.dumps({}))
        return
    if "/intermediate/" not in file_path and "/reviews/" not in file_path:
        print(json.dumps({}))
        return
    if not file_path.endswith(".json"):
        print(json.dumps({}))
        return

    schema_name = find_schema(file_path)
    if not schema_name:
        print(json.dumps({}))
        return

    # Load schema
    schemas_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schemas")
    schema_path = os.path.join(schemas_dir, schema_name)
    if not os.path.exists(schema_path):
        print(json.dumps({}))
        return

    with open(schema_path) as f:
        schema = json.load(f)

    # Load the written file
    if not os.path.exists(file_path):
        print(json.dumps({}))
        return

    try:
        with open(file_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "warning": f"Output file {os.path.basename(file_path)} is not valid JSON: {e}"
        }))
        return

    # Validate required fields
    errors = validate_required_fields(data, schema)
    if errors:
        print(json.dumps({
            "warning": f"Schema validation issues in {os.path.basename(file_path)} "
                       f"(schema: {schema_name}): {'; '.join(errors)}"
        }))
        return

    print(json.dumps({}))


if __name__ == "__main__":
    main()
