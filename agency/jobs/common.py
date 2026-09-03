"""Handlers shared by several stages."""
from __future__ import annotations

import re
from typing import Any

from agency.engine.runtime import JobRuntime
from agency.jobs import handler


def replace_hypothesis(graph, block: str, statement: str, *, created_by: str | None = None,
                       concept_status: str) -> None:
    """Rewrite the `## Hypothesis` block of the context document and set hypothesis + concept status."""
    doc = graph.document("context")
    body = doc.data.get("body", "") if doc else ""
    if "## Hypothesis" in body:
        body = re.sub(r"## Hypothesis\s*\n.*?(?=\n## |\Z)", f"## Hypothesis\n\n{block}\n", body, count=1, flags=re.S)
    else:
        body += f"\n\n## Hypothesis\n\n{block}\n"
    graph.put_document("context", doc.data.get("title", "context") if doc else "context", body,
                       created_by=created_by, hypothesis=statement, concept_status=concept_status)


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
