#!/usr/bin/env python3
"""PostToolUse hook for Write tool: verify claim IDs in drafts.

When a file is written to runs/*/drafts/, scans for claim_id references
(CLM-xxx, WIKI-CLM-xxx, CLM-FIN-xxx patterns) and verifies each exists
in the claim registry.

Contract:
  - all claims registered (or no claims referenced): exit 0, no output
  - unregistered claim references: message on stderr + exit 2 (Claude Code
    feeds stderr back to the model as feedback on the completed Write)
  - internal hook error: exit 0 (fail-open)
"""

import json
import sys
import os
import re

CLAIM_REF_RE = re.compile(r"\b(?:WIKI-)?CLM(?:-FIN)?-\d+\b")


def load_claim_registry(project_dir):
    """Load all claim IDs from the claim registry."""
    registry_path = os.path.join(project_dir, "memory", "claim_registry.jsonl")
    claim_ids = set()
    if os.path.exists(registry_path):
        with open(registry_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    claim_ids.add(entry.get("claim_id", ""))
    return claim_ids


def find_project_dir(file_path):
    """Extract the project directory from a file path in runs/."""
    parts = file_path.split("/runs/")
    if len(parts) < 2:
        return None
    project_name = parts[1].split("/")[0]
    return os.path.join(parts[0], "runs", project_name)


def main():
    hook_input = json.loads(sys.stdin.read())

    if hook_input.get("tool_name", "") != "Write":
        return

    file_path = hook_input.get("tool_input", {}).get("file_path", "")

    # Only check files in runs/*/drafts/
    if "/runs/" not in file_path or "/drafts/" not in file_path:
        return
    if not os.path.exists(file_path):
        return

    with open(file_path) as f:
        content = f.read()

    referenced_claims = set(CLAIM_REF_RE.findall(content))
    if not referenced_claims:
        return

    project_dir = find_project_dir(file_path)
    if not project_dir:
        return

    registered_claims = load_claim_registry(project_dir)

    unregistered = referenced_claims - registered_claims
    if unregistered:
        print(
            f"Draft {os.path.basename(file_path)} references "
            f"{len(unregistered)} unregistered claim(s): "
            f"{', '.join(sorted(unregistered))}. "
            f"These should be added to the claim registry "
            f"(memory/claim_registry.jsonl) or marked as [ASSUMPTION].",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
