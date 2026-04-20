#!/usr/bin/env python3
"""Emit a structured event line to runs/_events.jsonl.

Invoked from every Claude Code hook point (SessionStart, UserPromptSubmit,
PreToolUse, PostToolUse, Stop) so the Mission Control UI has a single, unified
live feed of everything the agent system does.

Usage:
    python hooks/emit_event.py <HookKind>

Reads the hook payload from stdin, enriches it with timestamps, a best-effort
project hint, and an agent hint (when the Agent/Task tool is invoked), and
appends one JSON line to runs/_events.jsonl.

Design constraints:
- **Fail open.** Any exception is swallowed so the emitter never blocks a
  real Claude Code operation. Errors are written to runs/_events.errors.log
  for debugging.
- **Non-blocking.** Target <20 ms; uses simple append with no locking beyond
  what the OS provides for O_APPEND writes.
- **Never writes tool output contents.** Only summaries (byte counts, line
  counts, first keys) — avoid leaking large file reads into the event log.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVENTS_FILE = REPO_ROOT / "runs" / "_events.jsonl"
ERROR_LOG = REPO_ROOT / "runs" / "_events.errors.log"
TIMING_FILE = REPO_ROOT / "runs" / "_events.timings.json"

MAX_SUMMARY_CHARS = 240
AGENT_FILE_RE = re.compile(
    r"agents/(?:orchestrators|workers/(?:retrievers|synthesizers|writers|reviewers))/([a-z0-9_]+)\.md",
    re.IGNORECASE,
)
PROJECT_PATH_RE = re.compile(r"runs/([a-zA-Z0-9_\-]+)(?:/|$)")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def short(value: object) -> object:
    """Summarize a value for inclusion in the event log without leaking bulk content."""
    if isinstance(value, str):
        if len(value) <= MAX_SUMMARY_CHARS:
            return value
        return value[:MAX_SUMMARY_CHARS] + "…"
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {
            k: short(v) if not isinstance(v, (dict, list)) else f"<{type(v).__name__}>"
            for k, v in list(value.items())[:10]
        }
    if isinstance(value, list):
        return f"<list len={len(value)}>"
    return f"<{type(value).__name__}>"


def summarize_input(tool_input: dict) -> dict:
    """Produce a compact summary of tool input keys + short values."""
    if not isinstance(tool_input, dict):
        return {}
    summary: dict[str, object] = {}
    for key, value in tool_input.items():
        # Preserve small strings verbatim; summarize big ones.
        if isinstance(value, str) and len(value) > MAX_SUMMARY_CHARS:
            summary[key] = value[:MAX_SUMMARY_CHARS] + "…"
            summary[f"_{key}_len"] = len(value)
        else:
            summary[key] = short(value)
    return summary


def summarize_output(tool_response: object) -> dict:
    """Summarize a tool output. Never include full contents."""
    if tool_response is None:
        return {}
    if isinstance(tool_response, dict):
        stdout = tool_response.get("stdout")
        stderr = tool_response.get("stderr")
        summary: dict[str, object] = {}
        if "success" in tool_response:
            summary["success"] = tool_response["success"]
        if isinstance(stdout, str):
            summary["stdout_bytes"] = len(stdout)
            summary["stdout_lines"] = stdout.count("\n")
        if isinstance(stderr, str) and stderr:
            summary["stderr_bytes"] = len(stderr)
        if "interrupted" in tool_response:
            summary["interrupted"] = tool_response["interrupted"]
        return summary
    if isinstance(tool_response, str):
        return {"bytes": len(tool_response), "lines": tool_response.count("\n")}
    return {"type": type(tool_response).__name__}


def infer_project_hint(tool_input: object, tool_response: object, cwd: str) -> str | None:
    """Best-effort extraction of which runs/<project> this event touched."""
    blob_parts: list[str] = [cwd or ""]
    if isinstance(tool_input, dict):
        try:
            blob_parts.append(json.dumps(tool_input)[:4000])
        except (TypeError, ValueError):
            pass
    if isinstance(tool_response, dict):
        try:
            blob_parts.append(json.dumps(tool_response)[:2000])
        except (TypeError, ValueError):
            pass
    blob = " ".join(blob_parts)
    match = PROJECT_PATH_RE.search(blob)
    return match.group(1) if match else None


def infer_agent_hint(tool_name: str, tool_input: object) -> str | None:
    """When the Agent/Task tool is used, detect which agent markdown file is referenced."""
    if tool_name not in ("Agent", "Task"):
        return None
    if not isinstance(tool_input, dict):
        return None
    prompt = tool_input.get("prompt")
    if not isinstance(prompt, str):
        return None
    match = AGENT_FILE_RE.search(prompt)
    if match:
        return match.group(0)
    return None


def load_timings() -> dict[str, float]:
    if not TIMING_FILE.exists():
        return {}
    try:
        return json.loads(TIMING_FILE.read_text() or "{}")
    except (json.JSONDecodeError, OSError):
        return {}


def save_timings(timings: dict[str, float]) -> None:
    try:
        TIMING_FILE.write_text(json.dumps(timings))
    except OSError:
        pass


def record_start(tool_use_id: str) -> None:
    if not tool_use_id:
        return
    timings = load_timings()
    # Prune old entries to keep the file small
    cutoff = time.time() - 3600
    timings = {k: v for k, v in timings.items() if v > cutoff}
    timings[tool_use_id] = time.time()
    save_timings(timings)


def pop_duration_ms(tool_use_id: str) -> float | None:
    if not tool_use_id:
        return None
    timings = load_timings()
    started = timings.pop(tool_use_id, None)
    save_timings(timings)
    if started is None:
        return None
    return (time.time() - started) * 1000.0


def append_event(event: dict) -> None:
    EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, ensure_ascii=False) + "\n"
    # O_APPEND guarantees atomic appends for writes <= PIPE_BUF on POSIX.
    fd = os.open(str(EVENTS_FILE), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)


def log_error(err: BaseException) -> None:
    try:
        ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ERROR_LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"{now_iso()} {type(err).__name__}: {err}\n")
    except Exception:  # noqa: BLE001 — emitter must not crash Claude Code
        pass


def main() -> int:
    try:
        hook_kind = sys.argv[1] if len(sys.argv) > 1 else "Unknown"

        try:
            payload_raw = sys.stdin.read()
            payload = json.loads(payload_raw) if payload_raw.strip() else {}
        except json.JSONDecodeError:
            payload = {"_raw_stdin_bytes": len(payload_raw)}

        tool_name = payload.get("tool_name")
        tool_input = payload.get("tool_input", {})
        tool_response = payload.get("tool_response")
        tool_use_id = payload.get("tool_use_id", "") or ""
        cwd = payload.get("cwd", "")

        duration_ms: float | None = None
        if hook_kind == "PreToolUse":
            record_start(tool_use_id)
        elif hook_kind == "PostToolUse":
            duration_ms = pop_duration_ms(tool_use_id)

        event = {
            "ts": now_iso(),
            "session_id": payload.get("session_id", ""),
            "hook": hook_kind,
            "cwd": cwd,
        }
        if tool_name:
            event["tool_name"] = tool_name
        if tool_use_id:
            event["tool_use_id"] = tool_use_id
        if hook_kind in ("PreToolUse", "PostToolUse") and tool_input:
            event["tool_input_summary"] = summarize_input(tool_input)
        if hook_kind == "PostToolUse":
            event["tool_output_summary"] = summarize_output(tool_response)
        if duration_ms is not None:
            event["duration_ms"] = round(duration_ms, 1)

        project_hint = infer_project_hint(tool_input, tool_response, cwd)
        if project_hint:
            event["project_hint"] = project_hint

        agent_hint = infer_agent_hint(tool_name or "", tool_input)
        if agent_hint:
            event["agent_hint"] = agent_hint

        # UserPromptSubmit carries a `prompt` field
        if hook_kind == "UserPromptSubmit":
            prompt = payload.get("prompt")
            if isinstance(prompt, str):
                event["extra"] = {"prompt": prompt[:MAX_SUMMARY_CHARS]}

        append_event(event)
    except BaseException as err:  # noqa: BLE001 — fail open, never block Claude Code
        log_error(err)

    # Always emit empty JSON so hook contract is satisfied (Claude Code ignores {}).
    try:
        sys.stdout.write("{}")
    except BaseException:  # noqa: BLE001
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
