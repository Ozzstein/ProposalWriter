#!/usr/bin/env python3
"""PreToolUse hook for Agent tool: prevent duplicate task spawning.

Reads task_registry.jsonl from the active project's memory directory.
Blocks the spawn if a task with the same dedupe_key already exists
with status "running" or "complete".

Hook input (stdin): JSON with tool_name, tool_input fields.
Hook output (stdout): JSON with {"decision": "block", "reason": "..."} to block,
                      or {} to allow.
"""

import json
import sys
import glob
import os


def find_active_project():
    """Find the most recently modified project in runs/."""
    runs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "runs")
    projects = glob.glob(os.path.join(runs_dir, "*/state.json"))
    if not projects:
        return None
    return max(projects, key=os.path.getmtime)


def load_task_registry(project_dir):
    """Load all tasks from the task registry."""
    registry_path = os.path.join(project_dir, "memory", "task_registry.jsonl")
    tasks = []
    if os.path.exists(registry_path):
        with open(registry_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    tasks.append(json.loads(line))
    return tasks


def main():
    hook_input = json.loads(sys.stdin.read())

    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Agent":
        print(json.dumps({}))
        return

    # Extract the agent prompt to look for dedupe_key
    tool_input = hook_input.get("tool_input", {})
    prompt = tool_input.get("prompt", "")

    # Look for dedupe_key pattern in the prompt: dedupe_key: <value>
    dedupe_key = None
    for line in prompt.split("\n"):
        if "dedupe_key:" in line.lower():
            dedupe_key = line.split(":", 1)[1].strip().strip('"').strip("'")
            break

    if not dedupe_key:
        # No dedupe_key specified — allow the spawn
        print(json.dumps({}))
        return

    # Find active project and check registry
    state_path = find_active_project()
    if not state_path:
        print(json.dumps({}))
        return

    project_dir = os.path.dirname(state_path)
    tasks = load_task_registry(project_dir)

    for task in tasks:
        if (task.get("dedupe_key") == dedupe_key
                and task.get("status") in ("running", "complete")):
            print(json.dumps({
                "decision": "block",
                "reason": f"Duplicate task: a task with dedupe_key '{dedupe_key}' "
                          f"already exists with status '{task['status']}' "
                          f"(task_id: {task.get('task_id', 'unknown')}). "
                          f"Skipping duplicate spawn."
            }))
            return

    print(json.dumps({}))


if __name__ == "__main__":
    main()
