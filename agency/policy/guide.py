"""Deterministic guidance: what the researcher should do next, derived from project state.

The UI's Overview, `agency next` and the planning brief all use this so every surface tells
the same story. No model calls; pure rules over stage statuses, gates, inbox, runs, scope and the CallSpec.
"""
from __future__ import annotations

from typing import Any

from agency.domain.callspec import CallSpec
from agency.domain.runs import RunStatus
from agency.domain.scope import MODULE_STATE_KEY, ScopeConfig, concept_status_of

MAIN_PATH: list[tuple[str, str, str]] = [   # (state key, label, stage name)
    ("call_parsing", "Call", "parse-call"),
    ("ideation", "Idea", "ideate"),
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
STAGE_ORDER = ["parse-call", "ideate", "research", "finance", "write-proposal", "business-plan", "figures",
               "review", "external-feedback", "export", "plan"]
OPTIONAL_STAGE_NAMES = {"ideate", "finance", "figures", "business-plan", "external-feedback", "plan"}
EXPLORATORY = "Or run an exploratory ideation now; it will be aligned to the call afterwards."


def _step(key: str, title: str, why: str, action: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    return {"key": key, "title": title, "why": why, "action": action or {"kind": "none"}, **extra}


def next_step(ws, project_id: str) -> dict[str, Any]:
    project = ws.require_project(project_id)
    stages, gates = project.stages, project.gates
    graph = ws.graph(project_id)
    scope = ScopeConfig.load(project)

    def st(key: str) -> str:
        return stages.get(key, {}).get("status", "pending")

    def done(key: str) -> bool:
        return st(key) in ("complete", "skipped")

    def gate_failed(name: str) -> list[str]:
        g = gates.get(name, {})
        if g.get("checked_at") and not g.get("passed") and not g.get("not_applicable"):
            return list(g.get("blockers") or ["not passed"])
        return []

    def module_state(key: str) -> str | None:
        module = next((m for m, k in MODULE_STATE_KEY.items() if k == key), None)
        return scope.state(module) if (scope is not None and module) else None

    path = [{"key": k, "label": lbl, "stage": s, "status": st(k), "optional": False} for k, lbl, s in MAIN_PATH]
    side = [{"key": k, "label": lbl, "stage": s, "status": st(k), "optional": True, "scope_state": module_state(k)}
            for k, lbl, s in SIDE_PATH]
    result = _guidance(ws, project_id, project, graph, scope, st, done, gate_failed)
    result["path"] = path
    result["side"] = side
    result["scope"] = scope.model_dump(mode="json") if scope is not None else None
    stage_name = result["action"].get("stage")
    if stage_name:
        last = next((r for r in ws.store.list_runs(project_id=project_id) if r.stage == stage_name), None)
        if last and last.status in (RunStatus.FAILED, RunStatus.STOPPED, RunStatus.INTERRUPTED):
            result["last_run"] = {"id": last.id, "status": last.status.value, "error": last.error}
            result["action"]["resume"] = last.id
            result["why"] += f" The last {stage_name} run {last.status.value}" + (f": {last.error[:200]}" if last.error else ".") + \
                " Resume it to reuse the completed jobs."
    return result


def _wanted(scope: ScopeConfig | None, module: str) -> bool:
    """Included or required → the guide recommends it; excluded or unconfigured → it does not."""
    return scope is not None and scope.state(module) in ("included", "required")


def _guidance(ws, pid, project, graph, scope, st, done, gate_failed) -> dict[str, Any]:
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
    if not done("call_parsing"):
        inputs = ws.config.project_dir(pid) / "inputs"
        files = [p for p in inputs.rglob("*") if p.is_file() and not p.name.endswith(".extracted.txt")] if inputs.exists() else []
        if not files:
            return _step("upload_call", "Upload the call document, then parse it",
                         "Everything downstream (sections, criteria, scope, gates) is planned from the parsed call. "
                         "Add the call text or PDF and the official application template if you have one.",
                         {"kind": "upload_then_run", "stage": "parse-call", "subdir": ""},
                         alternatives=["Or run parse-call without a file and paste the call text when asked.", EXPLORATORY])
        return _step("parse_call", "Parse the call",
                     f"{len(files)} input file(s) found. The call parser extracts sections, criteria, requirements "
                     "and limits; you approve the result and configure the scope in the Inbox.",
                     {"kind": "run_stage", "stage": "parse-call"}, alternatives=[EXPLORATORY])
    if scope is None or not scope.configured_at:
        return _step("configure_scope", "Configure the proposal scope",
                     "Decide which optional modules (finance, business plan, figures, external review) the proposal "
                     "includes. Modules the call requires are locked; everything else is your choice.",
                     {"kind": "run_stage", "stage": "parse-call", "flags": {"scope_only": "1"}})
    ctx = graph.document("context")
    concept = concept_status_of(ctx)
    if concept == "none" and not done("ideation"):
        return _step("ideate", "Develop the idea into a hypothesis",
                     "The call is parsed but the project has no hypothesis yet. The ideation interview asks you a "
                     "few batches of questions, probes prior art and scores 2–3 framings against the call; you pick one.",
                     {"kind": "run_stage", "stage": "ideate"},
                     alternatives=["Or write the hypothesis yourself in the project context and skip ideation."])
    if concept == "preliminary":
        alignments = sorted(graph.decisions("concept_alignment"), key=lambda d: d.created_at)
        if alignments and alignments[-1].data.get("decision") == "reopen_ideation":
            return _step("ideate", "Develop the idea again",
                         "The evaluator sent the preliminary concept back to ideation: it did not fit the call "
                         "well enough to align. Develop a new framing, then align it with the call again.",
                         {"kind": "run_stage", "stage": "ideate"},
                         alternatives=["Or re-run the alignment: parse-call with align_only."])
        return _step("align_concept", "Align the concept with the call",
                     "The hypothesis was written before the call was parsed. An evaluator scores it against the "
                     "call's criteria, scope and eligibility; you keep it, adopt the suggested adjustment, or reopen ideation.",
                     {"kind": "run_stage", "stage": "parse-call", "flags": {"align_only": "1"}})
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
    if _wanted(scope, "finance") and st("finance") == "pending":
        return _step("finance", "Build the financial model",
                     "Finance is in scope. Drop workbooks into inputs/financials/ or fill the form the stage asks "
                     "for; the modeler computes tables and hard-threshold checks so the financial sections can be drafted.",
                     {"kind": "run_stage", "stage": "finance"},
                     alternatives=["Skip it for now and draft the narrative sections first."])
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
    if _wanted(scope, "business_plan") and st("business_plan") == "pending":
        return _step("business_plan", "Build the business-plan annex",
                     "The business plan is in scope. A batched interview collects what no artefact has; "
                     "four writers and a red-team produce the annex.",
                     {"kind": "run_stage", "stage": "business-plan"},
                     alternatives=["Skip it for now and review the narrative sections first."])
    if _wanted(scope, "figures") and st("figures") == "pending":
        return _step("figures", "Render the figures",
                     "Figures are in scope. The figures register is rendered (plots and concept graphics) and indexed "
                     "so drafts can reference them.",
                     {"kind": "run_stage", "stage": "figures"},
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
    if _wanted(scope, "external_review"):
        return _step("done", "Proposal exported",
                     "Send it to colleagues; when their comments come back, drop the files into inputs/reviews/ and "
                     "run external-feedback. Promote what you learned to the knowledge base with `agency kb promote`.",
                     {"kind": "run_stage", "stage": "external-feedback"},
                     alternatives=["Ask the planner for a further improvement campaign."])
    return _step("done", "Proposal exported",
                 "Promote what you learned to the knowledge base with `agency kb promote`. External review is not in "
                 "scope; include it on the Overview if colleagues will comment.",
                 alternatives=["Ask the planner for a further improvement campaign."])


def _callspec(graph) -> CallSpec | None:
    node = graph.callspec_node()
    if node is None:
        return None
    try:
        return CallSpec.model_validate(node.data)
    except Exception:
        return None
