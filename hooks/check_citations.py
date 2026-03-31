#!/usr/bin/env python3
"""PostToolUse hook for Write tool: verify claim IDs in drafts.

When a file is written to runs/*/drafts/, scans for claim_id references
(CLM-xxx pattern) and verifies each exists in the claim registry.

Hook input (stdin): JSON with tool_name, tool_input.
Hook output (stdout): JSON with warnings if unregistered claims found, or {}.
"""

import json
import sys
import os
import re


def load_claim_registry(project_dir):
    """Load all claim IDs from the claim registry."""
    registry_path = os.path.join(project_dir, "memory", "claim_registry.jsonl")
    claim_ids = set()
    if os.path.exists(registry_path):
        with open(registry_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    claim_ids.add(entry.get("claim_id", ""))
    return claim_ids


def find_project_dir(file_path):
    """Extract the project directory from a file path in runs/."""
    # file_path looks like .../runs/project-name/drafts/section.md
    parts = file_path.split("/runs/")
    if len(parts) < 2:
        return None
    after_runs = parts[1]
    project_name = after_runs.split("/")[0]
    return os.path.join(parts[0], "runs", project_name)


def main():
    hook_input = json.loads(sys.stdin.read())

    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Write":
        print(json.dumps({}))
        return

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only check files in runs/*/drafts/
    if "/runs/" not in file_path or "/drafts/" not in file_path:
        print(json.dumps({}))
        return

    if not os.path.exists(file_path):
        print(json.dumps({}))
        return

    # Read the draft content
    with open(file_path) as f:
        content = f.read()

    # Find all CLM-xxx references
    referenced_claims = set(re.findall(r"CLM-\d+", content))
    if not referenced_claims:
        print(json.dumps({}))
        return

    # Load claim registry
    project_dir = find_project_dir(file_path)
    if not project_dir:
        print(json.dumps({}))
        return

    registered_claims = load_claim_registry(project_dir)

    # Find unregistered claims
    unregistered = referenced_claims - registered_claims
    if unregistered:
        print(json.dumps({
            "warning": f"Draft {os.path.basename(file_path)} references "
                       f"{len(unregistered)} unregistered claim(s): "
                       f"{', '.join(sorted(unregistered))}. "
                       f"These should be added to the claim registry or "
                       f"marked as [ASSUMPTION]."
        }))
        return

    print(json.dumps({}))


if __name__ == "__main__":
    main()
