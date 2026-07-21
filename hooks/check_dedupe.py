#!/usr/bin/env python3
"""PreToolUse hook for the Task (subagent) tool: prevent duplicate task spawning.

Reads task_registry.jsonl from the target project's memory directory and
blocks the spawn if a task with the same dedupe_key is currently running.

Prompt conventions (set by the orchestrating slash commands):
  - `dedupe_key: <value>` line — identifies the task for deduplication.
    No dedupe_key line means the spawn is always allowed (fail-open).
  - `project: <name>` line — names the target project under runs/.
    Without it, the most recently modified project is assumed.

Rules:
  - Registry is append-only: entries are grouped by task_id and the LAST
    line per task_id is the current state.
  - Only status "running" blocks. Completed tasks may be re-run (review
    rounds, revision loops are part of the normal workflow).
  - A "running" entry older than 24h (per its started_at/created_at
    field) is treated as crashed and does not block.

Contract:
  - allow: exit 0, no output
  - block: exit 0 + stdout JSON
    {"hookSpecificOutput": {"hookEventName": "PreToolUse",
     "permissionDecision": "deny", "permissionDecisionReason": "..."}}
    (older Claude Code versions accept {"decision": "block", "reason": ...})
  - internal error: exit 0, no output (fail-open)

Env: PW_RUNS_DIR overrides the runs/ directory (used by tests).
"""

import json
import sys
import glob
import os
from datetime import datetime, timedelta, timezone

STALE_RUNNING_HOURS = 24


def runs_dir():
    env = os.environ.get("PW_RUNS_DIR")
    if env:
        return env
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs")


def find_project_dir(project_name):
    base = runs_dir()
    if project_name:
        candidate = os.path.join(base, project_name)
        if os.path.isdir(candidate):
            return candidate
    # Fallback: most recently modified project with a state.json
    projects = glob.glob(os.path.join(base, "*", "state.json"))
    if not projects:
        return None
    return os.path.dirname(max(projects, key=os.path.getmtime))


def current_tasks(project_dir):
    """Load the task registry, last line per task_id wins."""
    registry_path = os.path.join(project_dir, "memory", "task_registry.jsonl")
    tasks = {}
    if os.path.exists(registry_path):
        with open(registry_path) as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    task = json.loads(line)
                except json.JSONDecodeError:
                    continue
                tasks[task.get("task_id", f"__line{i}")] = task
    return tasks.values()


def is_stale(task):
    """A running task older than STALE_RUNNING_HOURS is treated as crashed."""
    stamp = task.get("started_at") or task.get("created_at")
    if not stamp:
        return False
    try:
        started = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    except ValueError:
        return False
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - started > timedelta(hours=STALE_RUNNING_HOURS)


def prompt_field(prompt, field):
    for line in prompt.split("\n"):
        if f"{field}:" in line.lower():
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def block(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def main():
    hook_input = json.loads(sys.stdin.read())

    if hook_input.get("tool_name", "") not in ("Task", "Agent"):
        return

    prompt = hook_input.get("tool_input", {}).get("prompt", "")

    dedupe_key = prompt_field(prompt, "dedupe_key")
    if not dedupe_key:
        return  # No dedupe_key specified — allow the spawn

    project_dir = find_project_dir(prompt_field(prompt, "project"))
    if not project_dir:
        return

    for task in current_tasks(project_dir):
        if task.get("dedupe_key") == dedupe_key and task.get("status") == "running":
            if is_stale(task):
                continue
            block(
                f"Duplicate task: a task with dedupe_key '{dedupe_key}' is "
                f"already running (task_id: {task.get('task_id', 'unknown')}). "
                f"Wait for it to finish, or mark it complete/failed in "
                f"memory/task_registry.jsonl if it crashed."
            )
            return


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
