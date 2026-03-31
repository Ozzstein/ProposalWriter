#!/usr/bin/env python3
"""PreToolUse hook for Agent tool: enforce maximum delegation depth.

Blocks agent spawning if the current depth would exceed the maximum
allowed depth of 2 levels (orchestrator -> worker -> subworker).

Hook input (stdin): JSON with tool_name, tool_input, agent_id, agent_type.
Hook output (stdout): JSON with {"decision": "block", "reason": "..."} to block,
                      or {} to allow.
"""

import json
import sys

MAX_DEPTH = 2


def main():
    hook_input = json.loads(sys.stdin.read())

    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Agent":
        print(json.dumps({}))
        return

    # agent_type indicates what kind of agent is making this call.
    # "main" = the top-level session (depth 0)
    # Any subagent type = depth >= 1
    agent_type = hook_input.get("agent_type", "main")

    # If the caller is already a subagent (not main), this spawn would be
    # depth 2. If the caller is a sub-subagent, this would be depth 3+.
    # We allow depth 0 -> 1 (main spawns worker) and depth 1 -> 2 (worker
    # spawns subworker). We block depth 2+ -> 3+.
    #
    # Heuristic: if agent_type is not "main" and the prompt mentions
    # "depth: 2" or higher, block it.
    tool_input = hook_input.get("tool_input", {})
    prompt = tool_input.get("prompt", "")

    # Check for depth indicator in prompt
    current_depth = 0
    for line in prompt.split("\n"):
        if "current_depth:" in line.lower():
            try:
                current_depth = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
            break

    if agent_type != "main":
        current_depth = max(current_depth, 1)

    if current_depth >= MAX_DEPTH:
        print(json.dumps({
            "decision": "block",
            "reason": f"Maximum delegation depth ({MAX_DEPTH}) reached. "
                      f"Current depth: {current_depth}. "
                      f"This agent cannot spawn further subagents. "
                      f"Complete the task directly or escalate to parent."
        }))
        return

    print(json.dumps({}))


if __name__ == "__main__":
    main()
