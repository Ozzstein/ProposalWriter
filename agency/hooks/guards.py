"""In-process hooks attached to every SDK query: guards + telemetry + write validation."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from claude_agent_sdk import HookMatcher

from agency.catalogue.loader import resolve_output_model
from agency.domain.ids import CLAIM_REF_RE

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
PROTECTED = re.compile(r"(^|/)(memory/[^/]+\.jsonl|state\.json|workspace\.db)$")
BASH_DENY = re.compile(r"(>\s*\S*memory/|rm\s+-rf\s+/|sudo\s|curl[^|]*\|\s*(ba)?sh)")

# filename -> output model used to validate JSON written into intermediate/ or reviews/
FILE_MODELS = {
    "novelty_map.json": "NoveltyMap",
    "gap_analysis.json": "GapAnalysis",
    "ideation_brief.json": "IdeationBrief",
    "call_spec.json": "CallSpec",
    "evaluator_simulation.json": "EvaluatorSimulation",
    "financial_model.json": "FinancialInputs",
}


@dataclass
class HookContext:
    project_id: str
    job_id: str
    run_id: str | None
    agent: str
    allowed_roots: list[Path]
    events: Any = None
    known_claim_ids: set[str] = field(default_factory=set)
    _started: dict[str, float] = field(default_factory=dict)


def _deny(reason: str) -> dict[str, Any]:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def _context(text: str) -> dict[str, Any]:
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text}}


def _path_allowed(path: str, roots: list[Path]) -> bool:
    try:
        p = Path(path).resolve()
    except OSError:
        return False
    return any(p == r or r in p.parents for r in (root.resolve() for root in roots))


def build_hooks(ctx: HookContext) -> dict[str, list[HookMatcher]]:
    async def guard(input_data: dict[str, Any], tool_use_id: str | None, _ctx: Any) -> dict[str, Any]:
        tool = input_data.get("tool_name", "")
        tin = input_data.get("tool_input") or {}
        if tool in ("Agent", "Task"):
            return _deny("This agency runs agents from code; do not spawn subagents.")
        if tool in WRITE_TOOLS:
            path = str(tin.get("file_path") or tin.get("notebook_path") or "")
            if PROTECTED.search(path):
                return _deny("memory/*.jsonl and state files are regenerated from the graph; "
                             "use mcp__agency__graph_write instead.")
            if path and not _path_allowed(path, ctx.allowed_roots):
                return _deny(f"Writes are restricted to {[str(r) for r in ctx.allowed_roots]}.")
        if tool == "Bash":
            cmd = str(tin.get("command", ""))
            if BASH_DENY.search(cmd):
                return _deny("Command touches protected files or is destructive; not allowed.")
        return {}

    async def telemetry_pre(input_data: dict[str, Any], tool_use_id: str | None, _ctx: Any) -> dict[str, Any]:
        if tool_use_id:
            ctx._started[tool_use_id] = time.monotonic()
        if ctx.events is not None:
            ctx.events.emit("tool:start", project_id=ctx.project_id, run_id=ctx.run_id, job_id=ctx.job_id,
                            agent=ctx.agent, tool_name=input_data.get("tool_name"),
                            input=_summarise(input_data.get("tool_input") or {}))
        return {}

    async def telemetry_post(input_data: dict[str, Any], tool_use_id: str | None, _ctx: Any) -> dict[str, Any]:
        dur = None
        if tool_use_id and tool_use_id in ctx._started:
            dur = int((time.monotonic() - ctx._started.pop(tool_use_id)) * 1000)
        if ctx.events is not None:
            ctx.events.emit("tool:end", project_id=ctx.project_id, run_id=ctx.run_id, job_id=ctx.job_id,
                            agent=ctx.agent, tool_name=input_data.get("tool_name"), duration_ms=dur,
                            output=_summarise(input_data.get("tool_response") or {}))
        return {}

    async def validate_written(input_data: dict[str, Any], tool_use_id: str | None, _ctx: Any) -> dict[str, Any]:
        tin = input_data.get("tool_input") or {}
        path = Path(str(tin.get("file_path") or ""))
        if not path.name:
            return {}
        if path.suffix == ".json" and path.name in FILE_MODELS and path.exists():
            try:
                data = json.loads(path.read_text())
                resolve_output_model(FILE_MODELS[path.name]).model_validate(data)
            except Exception as e:
                return _context(f"{path.name} does not conform to {FILE_MODELS[path.name]}: {str(e)[:800]}. "
                                "Fix the file and rewrite it.")
        if path.suffix == ".md" and path.parent.name == "drafts" and ctx.known_claim_ids and path.exists():
            refs = set(CLAIM_REF_RE.findall(path.read_text()))
            unknown = sorted(refs - ctx.known_claim_ids)
            if unknown:
                return _context(f"Draft cites claim IDs that are not registered: {unknown}. Register them "
                                "with mcp__agency__graph_write or cite existing claims.")
        return {}

    return {
        "PreToolUse": [HookMatcher(matcher="Write|Edit|MultiEdit|NotebookEdit|Bash|Agent|Task", hooks=[guard]),
                       HookMatcher(matcher=None, hooks=[telemetry_pre])],
        "PostToolUse": [HookMatcher(matcher="Write|Edit|MultiEdit", hooks=[validate_written]),
                        HookMatcher(matcher=None, hooks=[telemetry_post])],
    }


def _summarise(obj: Any, limit: int = 240) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in list(obj.items())[:8]:
            if k in ("content", "new_string", "old_string"):
                out[k] = f"<{len(str(v))} chars>"
            else:
                out[k] = _summarise(v, limit)
        return out
    if isinstance(obj, str):
        return obj if len(obj) <= limit else obj[:limit] + "…"
    if isinstance(obj, list):
        return [_summarise(x, limit) for x in obj[:5]]
    return obj
