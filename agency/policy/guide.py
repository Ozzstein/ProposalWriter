"""Deterministic guidance: what the researcher should do next, derived from project state.

The UI's Overview, `agency status` and the planning brief all use this so every surface tells
the same story. No model calls; pure rules over stage statuses, gates, inbox, runs and the CallSpec.
"""
from __future__ import annotations

from typing import Any

from agency.domain.callspec import CallSpec
from agency.domain.runs import RunStatus

MAIN_PATH: list[tuple[str, str, str]] = [   # (state key, label, stage name)
    ("ideation", "Idea", "ideate"),
    ("call_parsing", "Call", "parse-call"),
    ("research", "Research", "research"),
    ("writing", "Draft", "write-proposal"),
    ("review", "Review", "review"),
    ("export", "Export", "export"),
]
SIDE_PATH: list[tuple[str, str, str]] = [
    ("finance", "Finance", "finance"),
    ("figures", "Figures", "figures"),
    ("business_plan", "Business plan", "business-plan"),
    ("external_review", "External feedback", "external-feedback"),
]
STAGE_ORDER = ["ideate", "parse-call", "research", "write-proposal", "finance", "figures", "business-plan",
               "review", "external-feedback", "export", "plan"]
OPTIONAL_STAGE_NAMES = {"ideate", "finance", "figures", "business-plan", "external-feedback", "plan"}


def _step(key: str, title: str, why: str, action: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    return {"key": key, "title": title, "why": why, "action": action or {"kind": "none"}, **extra}


def next_step(ws, project_id: str) -> dict[str, Any]:
    project = ws.require_project(project_id)
    stages, gates = project.stages, project.gates
    graph = ws.graph(project_id)

    def st(key: str) -> str:
        return stages.get(key, {}).get("status", "pending")

    def done(key: str) -> bool:
        return st(key) in ("complete", "skipped")

    def gate_failed(name: str) -> list[str]:
        g = gates.get(name, {})
        if g.get("checked_at") and not g.get("passed") and not g.get("not_applicable"):
            return list(g.get("blockers") or ["not passed"])
        return []

    path = [{"key": k, "label": lbl, "stage": s, "status": st(k), "optional": False} for k, lbl, s in MAIN_PATH]
    side = [{"key": k, "label": lbl, "stage": s, "status": st(k), "optional": True} for k, lbl, s in SIDE_PATH]
    result = _guidance(ws, project_id, project, graph, st, done, gate_failed)
    result["path"] = path
    result["side"] = side
    # last run of the recommended stage failed or stopped → offer resume
    stage_name = result["action"].get("stage")
    if stage_name:
        last = next((r for r in ws.store.list_runs(project_id=project_id) if r.stage == stage_name), None)
        if last and last.status in (RunStatus.FAILED, RunStatus.STOPPED, RunStatus.INTERRUPTED):
            result["last_run"] = {"id": last.id, "status": last.status.value, "error": last.error}
            result["action"]["resume"] = last.id
            result["why"] += f" The last {stage_name} run {last.status.value}" + (f": {last.error[:200]}" if last.error else ".") + \
                " Resume it to reuse the completed jobs."
    return result


def _guidance(ws, pid, project, graph, st, done, gate_failed) -> dict[str, Any]:
    pending = ws.store.list_inbox(project_id=pid, status="pending")
    if pending:
        n = len(pending)
        return _step("inbox", f"Answer {n} item{'s' if n > 1 else ''} in the Inbox",
                     f"A run is waiting for you: {pending[0].header} — {pending[0].question[:140]}",
                     {"kind": "inbox"})
    active = [r for r in ws.store.list_runs(project_id=pid)
              if r.status in (RunStatus.RUNNING, RunStatus.WAITING_FOR_USER, RunStatus.QUEUED)]
    if active:
        return _step("running", f"{active[0].stage} is running",
                     "Follow it on the Runs page; the Inbox badge lights up if it needs you.",
                     {"kind": "runs", "run_id": active[0].id})
    ctx = graph.document("context")
    hyp = (ctx.data.get("hypothesis") if ctx else "") or ""
    if (not hyp.strip() or "to be completed" in hyp.lower()) and not done("ideation"):
        return _step("ideate", "Develop the idea into a hypothesis",
                     "The project has no hypothesis yet. The ideation interview asks you a few batches of "
                     "questions, probes prior art and scores 2–3 framings; you pick one.",
                     {"kind": "run_stage", "stage": "ideate"},
                     alternatives=["Or write the hypothesis yourself in the project context and skip ideation."])
    if not done("call_parsing"):
        inputs = ws.config.project_dir(pid) / "inputs"
        files = [p for p in inputs.rglob("*") if p.is_file() and not p.name.endswith(".extracted.txt")] if inputs.exists() else []
        if not files:
            return _step("upload_call", "Upload the call document, then parse it",
                         "Everything downstream (sections, criteria, gates) is planned from the parsed call. "
                         "Add the call text or PDF and the official application template if you have one.",
                         {"kind": "upload_then_run", "stage": "parse-call", "subdir": ""},
                         alternatives=["Or run parse-call without a file and paste the call text when asked."])
        return _step("parse_call", "Parse the call",
                     f"{len(files)} input file(s) found. The call parser extracts sections, criteria, requirements "
                     "and limits; you approve the result in the Inbox.",
                     {"kind": "run_stage", "stage": "parse-call"})
    spec = _callspec(graph)
    unconfirmed = [r for r in (spec.requirements if spec else []) if r.kind == "eligibility" and r.disqualifying
                   and r.status == "unknown"]
    if not done("research"):
        if unconfirmed:
            return _step("confirm_eligibility", "Confirm eligibility",
                         "The scope gate blocks research until every disqualifying eligibility requirement is "
                         "marked met or not applicable. Decide each one below.",
                         {"kind": "confirm_requirements"},
                         requirements=[{"id": r.id, "text": r.text, "status": r.status} for r in unconfirmed],
                         alternatives=["Or run research with force; that records a gate-override decision."])
        blockers = gate_failed("scope")
        if blockers:
            return _step("scope_gate", "Fix the scope blockers, then run research",
                         "The scope gate failed: " + "; ".join(blockers),
                         {"kind": "run_stage", "stage": "research", "force": True},
                         alternatives=["Re-run parse-call if the call spec is wrong."])
        return _step("research", "Run research",
                     "Retrievers gather literature, repositories and patents in parallel; the synthesizer writes the "
                     "state of the art; novelty anchors and gaps are mapped. Expect the most expensive stage.",
                     {"kind": "run_stage", "stage": "research"})
    if not done("writing"):
        blockers = gate_failed("evidence")
        if blockers:
            return _step("evidence_gate", "Strengthen the evidence before drafting",
                         "The evidence gate failed: " + "; ".join(blockers) +
                         ". Re-run research with a focus on what is missing.",
                         {"kind": "run_stage", "stage": "research", "flags": {"focus": ""}},
                         alternatives=["Or run write-proposal with force."])
        return _step("write", "Draft the proposal",
                     "One writer per section from the call spec; excellence first, impact and implementation in "
                     "parallel, abstract last. Every claim must cite the registry.",
                     {"kind": "run_stage", "stage": "write-proposal"})
    needs_finance = bool(spec and (spec.budget_rules or any(s.kind == "financial" for s in spec.sections)))
    if needs_finance and st("finance") == "pending":
        return _step("finance", "Build the financial model",
                     "The call has financial sections or budget rules. Drop workbooks into inputs/financials/ or "
                     "fill the form the stage asks for; the modeler computes tables and hard-threshold checks.",
                     {"kind": "run_stage", "stage": "finance"},
                     alternatives=["Skip it for now and review the narrative sections first."])
    if spec and spec.needs_business_plan() and st("business_plan") == "pending":
        return _step("business_plan", "Build the business-plan annex",
                     "The call requires a business plan. A batched interview collects what no artefact has; "
                     "four writers and a red-team produce the annex.",
                     {"kind": "run_stage", "stage": "business-plan"},
                     alternatives=["Skip it for now and review the narrative sections first."])
    if not done("review"):
        blockers = gate_failed("draft")
        if blockers:
            return _step("draft_gate", "Complete the draft before review",
                         "The draft gate failed: " + "; ".join(blockers),
                         {"kind": "run_stage", "stage": "write-proposal"})
        return _step("review", "Review and improve",
                     "Scientific and compliance reviews plus a simulated evaluator panel; the loop redrafts the "
                     "weakest sections until the predicted score plateaus.",
                     {"kind": "run_stage", "stage": "review"})
    if not done("export"):
        blockers = gate_failed("submission")
        if blockers:
            return _step("submission_gate", "Close the submission blockers",
                         "The submission gate failed: " + "; ".join(blockers),
                         {"kind": "run_stage", "stage": "review"},
                         alternatives=["Or export with force for an internal draft."])
        return _step("export", "Export the proposal",
                     "Assembles Markdown and DOCX with a reference list built from cited sources.",
                     {"kind": "run_stage", "stage": "export"})
    return _step("done", "Proposal exported",
                 "Send it to colleagues; when their comments come back, drop the files into inputs/reviews/ and "
                 "run external-feedback. Promote what you learned to the knowledge base with `agency kb promote`.",
                 {"kind": "run_stage", "stage": "external-feedback"},
                 alternatives=["Ask the planner for a further improvement campaign."])


def _callspec(graph) -> CallSpec | None:
    node = graph.callspec_node()
    if node is None:
        return None
    try:
        return CallSpec.model_validate(node.data)
    except Exception:
        return None
