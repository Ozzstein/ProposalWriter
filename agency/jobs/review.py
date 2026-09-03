"""review: scientific + compliance reviews and the simulated evaluator panel, then a
revise -> re-score loop until the predicted score plateaus or the budget is spent."""
from __future__ import annotations

import json
from typing import Any

from agency.domain.graph import NodeType
from agency.domain.models import EvaluatorSimulation, ReviewBatch
from agency.domain.runs import JobKind
from agency.engine.materialize import ingest_reviews
from agency.engine.plan import JobFailed, JobSpec, StageDef, StagePlan
from agency.engine.runtime import JobRuntime, RunContext
from agency.jobs import handler, stage
from agency.jobs.drafting import draft_one, writer_for


def plan_review(ctx: RunContext) -> StagePlan:
    jobs = [
        JobSpec("round_setup", "review.setup", kind=JobKind.CODE),
        JobSpec("review_scientific", "review.scientific", kind=JobKind.AGENT, deps=["round_setup"], contract="scientific_reviewer"),
        JobSpec("review_compliance", "review.compliance", kind=JobKind.AGENT, deps=["round_setup"], contract="compliance_checker", optional=True),
        JobSpec("panel", "review.panel", kind=JobKind.AGENT, deps=["round_setup"], contract="adversarial_evaluator_simulator"),
        JobSpec("compile_plan", "review.compile", kind=JobKind.CODE, deps=["review_scientific", "review_compliance", "panel"]),
        JobSpec("revise_loop", "review.revise_loop", kind=JobKind.LOOP, deps=["compile_plan"]),
        JobSpec("finalize", "finalize_stage", kind=JobKind.GATE, deps=["revise_loop"], params={"gate": "submission"}),
    ]
    return StagePlan(stage="review", jobs=jobs)


stage(StageDef(name="review", state_key="review", planner=plan_review, requires_gate="draft",
               requires_stages=("writing",),
               description="Red-team the drafts, simulate the evaluator panel, then revise the weakest sections "
                           "and re-score until the predicted score plateaus.",
               flags={"iterations": "max revise/re-score iterations (default from config)",
                      "auto_revise": "false to stop after the first panel and revision plan",
                      "min_gain": "stop when the predicted score gains fewer points than this"}))


def _review_inputs(rt: JobRuntime) -> list[tuple[str, str]]:
    d = rt.project_dir
    return [("all drafts", str(d / "drafts")), ("call spec", str(d / "intermediate" / "call_spec.json")),
            ("outline", str(d / "intermediate" / "proposal_outline.md")),
            ("claim registry", str(d / "memory" / "claim_registry.jsonl")),
            ("evidence store", str(d / "memory" / "evidence_store.jsonl")),
            ("novelty map", str(d / "intermediate" / "novelty_map.json")),
            ("gap analysis", str(d / "intermediate" / "gap_analysis.json")),
            ("research context", str(d / "context.md"))]


@handler("review.setup")
async def setup(rt: JobRuntime) -> dict[str, Any]:
    rt.ctx.materialize()
    prior = rt.graph.findings()
    round_no = max((int(f.data.get("round", 0) or 0) for f in prior), default=0) + 1
    if not rt.graph.sections():
        raise JobFailed("no drafted sections to review")
    return {"round": round_no, "summary": f"review round {round_no}, {len(rt.graph.sections())} sections"}


@handler("review.scientific")
async def scientific(rt: JobRuntime) -> dict[str, Any]:
    round_no = rt.result_of("round_setup")["round"]
    res = await rt.agent("scientific_reviewer", phase="scientific", inputs=_review_inputs(rt), output_model=ReviewBatch,
                         allowed_writes=set(), instructions=(
                             "Review every draft in drafts/. Return a `ReviewBatch` with one `ReviewReport` per section "
                             "(reviewer_type 'scientific'), scoring rigor, logical consistency and claim-evidence linkage; "
                             "list unsupported claim IDs and concrete fixes with priorities."))
    batch = ReviewBatch.model_validate(res.structured)
    ids = ingest_reviews(rt.graph, batch, reviewer_type="scientific", round_no=round_no, job_id=rt.job.id)
    low = [r.section_name for r in batch.sections if r.overall_score < 6]
    return {"findings": ids, "low": low, "summary": f"{len(ids)} section reports; below 6: {low or 'none'}"}


@handler("review.compliance")
async def compliance(rt: JobRuntime) -> dict[str, Any]:
    round_no = rt.result_of("round_setup")["round"]
    res = await rt.agent("compliance_checker", phase="compliance", inputs=_review_inputs(rt), output_model=ReviewBatch,
                         allowed_writes=set(), instructions=(
                             "REVIEW MODE (not patch mode): check every draft against the CallSpec — required "
                             "sections present, headings match the template, word/page limits (count words with Bash), "
                             "mandatory content from each section's guidance, disqualifying requirements, formatting rules. "
                             "Return a `ReviewBatch` with one `ReviewReport` per section (reviewer_type 'compliance'); "
                             "put every violation in major_issues and a fix for each."))
    batch = ReviewBatch.model_validate(res.structured)
    ids = ingest_reviews(rt.graph, batch, reviewer_type="compliance", round_no=round_no, job_id=rt.job.id)
    violations = sum(len(r.major_issues) for r in batch.sections)
    return {"findings": ids, "violations": violations, "summary": f"{violations} compliance violations"}


async def run_panel(rt: JobRuntime, iteration: int, phase: str = "panel") -> dict[str, Any]:
    spec = rt.ctx.callspec()
    pack = rt.ctx.pack()
    personas = "\n".join(f"- {p}" for p in pack.panel_personas) or "- three independent expert evaluators"
    hard_rules = [r for r in (spec.requirements if spec else []) if r.kind == "hard_rule"]
    instructions = f"""Simulate the evaluation panel for `{spec.title if spec else rt.project_id}` ({spec.funder if spec else ''}).
Evaluator personas:
{personas}
Run the hard-rejection checks first: {'; '.join(f'{r.id}: {r.text}' for r in hard_rules) or 'none defined by the call'}.
Then score EVERY criterion in call_spec.json (use its ids, max_score, weight, threshold) with a predicted range, a
central estimate, the weakest argument, a score ceiling and 2-4 improvement actions each. In `summary`, rank the
five actions with the highest expected score gain (`improvement_actions_ranked`, each naming its criterion) and
state the funding probability honestly. This is iteration {iteration} of the review loop."""
    res = await rt.agent("adversarial_evaluator_simulator", phase=phase, inputs=_review_inputs(rt),
                         output_model=EvaluatorSimulation, allowed_writes=set(), instructions=instructions)
    sim = EvaluatorSimulation.model_validate(res.structured)
    data = sim.model_dump(mode="json", exclude_none=True)
    if not data["summary"].get("score_percentage") and sim.summary.total_max_weighted_score:
        data["summary"]["score_percentage"] = round(100 * sim.summary.total_predicted_weighted_score / sim.summary.total_max_weighted_score, 1)
    data["iteration"] = iteration
    node = rt.graph.add(NodeType.PANEL_SCORE, data, created_by=rt.job.id)
    for cs in sim.criterion_scores:
        if rt.graph.get(f"CRIT-{cs.criterion_id}"):
            rt.graph.link(node, f"CRIT-{cs.criterion_id}", __import__("agency.domain.graph", fromlist=["EdgeType"]).EdgeType.SCORES,
                          created_by=rt.job.id, predicted=cs.predicted_score_central)
    pct = data["summary"].get("score_percentage")
    return {"node_id": node.id, "iteration": iteration, "score_pct": pct,
            "funding_probability": sim.summary.funding_probability,
            "hard_rejection_risks": sim.summary.hard_rejection_risks_detected,
            "actions": [a.model_dump(mode="json") for a in sim.summary.improvement_actions_ranked],
            "summary": f"panel {iteration}: {pct}% predicted, {sim.summary.funding_probability}, "
                       f"{len(sim.summary.hard_rejection_risks_detected)} hard-rejection risks"}


@handler("review.panel")
async def panel(rt: JobRuntime) -> dict[str, Any]:
    return await run_panel(rt, iteration=_next_iteration(rt))


def _next_iteration(rt: JobRuntime) -> int:
    latest = rt.graph.latest_panel()
    return int(latest.data.get("iteration", 0)) + 1 if latest else 1


def _actions_to_sections(rt: JobRuntime, actions: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Map ranked panel actions (by criterion) and critical fixes to section ids."""
    spec = rt.ctx.callspec()
    by_section: dict[str, list[str]] = {}
    for a in actions:
        crit = str(a.get("criterion", ""))
        targets = [s.id for s in spec.sections if crit and (crit in s.criterion_ids or crit.lower() in s.title.lower())]
        if a.get("section_name"):
            targets += [s.id for s in spec.sections if s.title.lower() == str(a["section_name"]).lower()]
        for t in targets or []:
            by_section.setdefault(t, []).append(f"[{crit}] {a.get('action', '')} (gain: {a.get('estimated_score_gain', '?')})")
    return by_section


@handler("review.compile")
async def compile_plan(rt: JobRuntime) -> dict[str, Any]:
    round_no = rt.result_of("round_setup")["round"]
    panel_res = rt.result_of("panel")
    spec = rt.ctx.callspec()
    lines = [f"# Revision plan — round {round_no}", "",
             f"Predicted score: **{panel_res.get('score_pct')}%** (funding probability: {panel_res.get('funding_probability')})", ""]
    risks = panel_res.get("hard_rejection_risks") or []
    if risks:
        lines += ["## Hard-rejection risks (fix before anything else)", *[f"- {r}" for r in risks], ""]
        rt.emit("escalation", severity="critical", reason="hard_rejection_risk", details=risks)
    lines += ["## Ranked actions (from the simulated panel)"]
    for a in panel_res.get("actions", []):
        lines.append(f"{a.get('rank', '?')}. [{a.get('criterion')}] {a.get('action')} — expected gain {a.get('estimated_score_gain', '?')}")
    critical: list[str] = []
    for f in rt.graph.findings():
        if int(f.data.get("round", 0)) != round_no:
            continue
        for fx in f.data.get("fixes", []):
            if fx.get("priority") in ("critical", "high"):
                critical.append(f"- [{fx['priority']}] {f.data.get('section_name')}: {fx.get('action')}")
    if critical:
        lines += ["", "## Critical / high fixes from reviewers", *critical]
    by_section = _actions_to_sections(rt, panel_res.get("actions", []))
    for f in rt.graph.findings():
        if int(f.data.get("round", 0)) != round_no:
            continue
        sec = next((s for s in spec.sections if s.title.lower() == str(f.data.get("section_name", "")).lower()), None)
        for fx in f.data.get("fixes", []):
            if fx.get("priority") in ("critical", "high") and sec:
                by_section.setdefault(sec.id, []).append(f"[{f.data.get('reviewer_type')}] {fx.get('action')}")
    lines += ["", "## Sections to revise", *[f"- {sid}: {len(v)} action(s)" for sid, v in by_section.items()]]
    rt.graph.put_document("revision_plan", f"Revision plan round {round_no}", "\n".join(lines), created_by=rt.job.id,
                          round=round_no, by_section=by_section)
    return {"by_section": by_section, "risks": risks, "score_pct": panel_res.get("score_pct"),
            "summary": f"revision plan: {len(by_section)} sections, {len(risks)} hard risks"}


@handler("review.revise_loop")
async def revise_loop(rt: JobRuntime) -> dict[str, Any]:
    cfg = rt.ws.config
    auto = str(rt.flags.get("auto_revise", "true")).lower() not in ("false", "0", "no")
    max_iter = int(rt.flags.get("iterations") or cfg.panel_max_iterations)
    min_gain = float(rt.flags.get("min_gain") or cfg.panel_min_gain)
    plan = rt.result_of("compile_plan")
    by_section: dict[str, list[str]] = dict(plan.get("by_section", {}))
    score = plan.get("score_pct")
    history = [{"iteration": _next_iteration(rt) - 1, "score_pct": score}]
    if not auto or not by_section:
        return {"history": history, "summary": f"no revision loop ({'disabled' if not auto else 'nothing to revise'}); score {score}%"}
    spec = rt.ctx.callspec()
    iterations = 0
    while iterations < max_iter and by_section:
        iterations += 1
        revised = []
        for sid, actions in list(by_section.items())[:4]:
            section = spec.section(sid)
            writer = writer_for(section) if section else None
            if not section or not writer:
                continue
            extra = ("## Revise the existing draft (read it first) to address these reviewer findings, keeping "
                     "everything that already works:\n" + "\n".join(f"- {a}" for a in actions))
            try:
                await draft_one(rt, section, writer, extra=extra)
                revised.append(sid)
            except JobFailed as e:
                rt.emit("revise:failed", section=sid, error=str(e))
        if not revised:
            break
        res = await run_panel(rt, iteration=_next_iteration(rt), phase=f"panel:{iterations}")
        new_score = res.get("score_pct")
        history.append({"iteration": res["iteration"], "score_pct": new_score, "revised": revised})
        rt.log_decision(f"Review loop iteration {iterations}", f"revised {revised}; score {score} -> {new_score}",
                        [a for acts in by_section.values() for a in acts][:10], type="review_iteration")
        gain = (new_score or 0) - (score or 0)
        score = new_score
        if gain < min_gain and not res.get("hard_rejection_risks"):
            break
        by_section = _actions_to_sections(rt, res.get("actions", []))
    return {"history": history, "final_score_pct": score,
            "summary": f"{iterations} revision iteration(s); final predicted score {score}%"}
