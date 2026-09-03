"""Handlers shared by several stages."""
from __future__ import annotations

from typing import Any

from agency.engine.runtime import JobRuntime
from agency.jobs import handler


@handler("finalize_stage")
async def finalize_stage(rt: JobRuntime) -> dict[str, Any]:
    """Run the stage's exit gate (if any) and assemble a summary from dependency results."""
    gate = rt.params.get("gate")
    summary_parts = []
    for dep in rt.job.deps:
        res = rt.result_of(dep)
        if res.get("summary"):
            summary_parts.append(f"{dep}: {res['summary']}")
    out: dict[str, Any] = {"summary": " | ".join(summary_parts)}
    if gate:
        result = rt.ws.check_gate(rt.project_id, gate, write=True)
        out["gate"] = result.model_dump(mode="json")
        out["summary"] += f" | gate {gate}: {'PASS' if result.passed else 'FAIL'}"
        if not result.passed:
            out["summary"] += " (" + "; ".join(result.blockers) + ")"
    rt.ctx.materialize()
    return out


@handler("noop")
async def noop(rt: JobRuntime) -> dict[str, Any]:
    return {"summary": rt.params.get("note", "skipped")}
