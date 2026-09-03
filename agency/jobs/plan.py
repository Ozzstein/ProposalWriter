"""plan: the planning agent proposes a campaign of stage runs; the researcher approves; the engine executes.

The planner never runs anything. It reads a planning brief (stages, flags, statuses, gates,
recent runs, cost, goal) and returns a RunPlan; ``validate_plan`` checks it against the stage
registry; the approval is an inbox item; ``Engine.run_campaign`` executes the approved steps
one stage run at a time and re-plans once when a step stops the campaign.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from agency.domain.models import RunPlan
from agency.domain.runs import JobKind
from agency.engine.plan import JobFailed, JobSpec, StageDef, StagePlan
from agency.engine.runtime import JobRuntime, RunContext
from agency.jobs import STAGES, handler, stage
from agency.workspace import STAGES as STATE_KEYS

MAX_STEPS = 8
PLAN_DOCUMENT = "run_plan"


def plan_plan(ctx: RunContext) -> StagePlan:
    return StagePlan("plan", [
        JobSpec("survey", "plan.survey", kind=JobKind.CODE),
        JobSpec("propose", "plan.propose", kind=JobKind.AGENT, contract="run_planner", deps=["survey"]),
        JobSpec("approve", "plan.approve", kind=JobKind.INBOX, deps=["propose"]),
    ])


stage(StageDef(name="plan", state_key=None, planner=plan_plan, interactive=True,
               description="Ask the planning agent for the next campaign of stage runs given the project state and "
                           "a goal, approve it in the inbox; `agency plan` / POST /plan then execute it step by step.",
               flags={"goal": "what the researcher wants to achieve next",
                      "budget_usd": "soft cost ceiling for the whole campaign",
                      "previous_failure": "(set by the engine) why the previous campaign stopped"}))


# ------------------------------------------------------------------ brief
def build_brief(ctx: RunContext, stages: dict[str, StageDef], *, goal: str, budget_usd: str | None = None,
                previous_failure: str | None = None) -> str:
    ws, pid = ctx.ws, ctx.project_id
    project = ws.require_project(pid)
    graph = ctx.graph
    spec = ctx.callspec()
    lines = [f"# Planning brief — project `{pid}`", "",
             f"**Goal**: {goal}",
             f"**Cost ceiling**: {budget_usd + ' USD' if budget_usd else 'none given'}",
             f"**Cost so far**: {ws.store.sum_cost(pid):.2f} USD",
             f"**Deadline**: {project.deadline or 'unknown'}", ""]
    if previous_failure:
        lines += ["## Previous campaign stopped", previous_failure, ""]
    lines += ["## Project", f"- name: {project.name}", f"- funder: {project.funder or 'unknown'}",
              f"- mechanism: {project.mechanism or 'unknown'}", f"- topic: {project.topic or '-'}"]
    ctx_doc = graph.document("context")
    if ctx_doc and ctx_doc.data.get("hypothesis"):
        lines.append(f"- hypothesis: {ctx_doc.data['hypothesis']}")
    lines += ["", "## Stage status (workflow order)"]
    for key in STATE_KEYS:
        st = project.stages.get(key, {})
        note = st.get("note")
        lines.append(f"- {key}: {st.get('status', 'pending')}" + (f" ({note})" if note else ""))
    lines += ["", "## Gates (deterministic checks over the graph)"]
    for gate in project.gates:
        try:
            res = ws.check_gate(pid, gate, write=False)
        except Exception as e:  # a gate that cannot evaluate is still information
            lines.append(f"- {gate}: error {e}")
            continue
        if res.not_applicable:
            lines.append(f"- {gate}: not applicable")
        else:
            lines.append(f"- {gate}: {'PASS' if res.passed else 'FAIL'}" +
                         ("" if res.passed else " — " + "; ".join(res.blockers)))
    counts = graph.summary()
    lines += ["", "## Graph counts", ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "empty"]
    if spec:
        disq = [r.id for r in spec.requirements if r.disqualifying]
        lines += ["", "## Call spec",
                  f"- {spec.funder} — {spec.title} ({spec.instrument or 'n/a'}, pack {spec.pack})",
                  f"- sections: " + ", ".join(f"{s.id} {s.title} [{s.kind}]" for s in spec.sections),
                  f"- criteria: {len(spec.criteria)}; disqualifying requirements: {', '.join(disq) or 'none'}",
                  f"- needs finance: {bool(spec.budget_rules) or any(s.kind == 'financial' for s in spec.sections)}; "
                  f"needs business plan: {spec.needs_business_plan()}"]
    else:
        lines += ["", "## Call spec", "not parsed yet"]
    panel = graph.latest_panel()
    if panel:
        s = panel.data.get("summary", {})
        lines += ["", "## Latest panel simulation",
                  f"- predicted {s.get('total_predicted_weighted_score')}/{s.get('total_max_weighted_score')} "
                  f"({s.get('score_percentage')}%), funding probability {s.get('funding_probability')}",
                  f"- hard-rejection risks: {', '.join(s.get('hard_rejection_risks_detected') or []) or 'none'}"]
    runs = [r for r in ws.store.list_runs(project_id=pid) if r.stage != "plan"][:8]
    lines += ["", "## Recent runs (newest first)"]
    for r in runs:
        lines.append(f"- {r.stage}: {r.status.value}, {r.cost_usd:.2f} USD, flags {json.dumps(r.flags)}"
                     + (f"; error: {r.error[:300]}" if r.error else "") + (f"; summary: {r.summary[:300]}" if r.summary else ""))
    if not runs:
        lines.append("- none yet")
    pending = ws.store.list_inbox(project_id=pid, status="pending")
    lines += ["", f"## Pending inbox items: {len(pending)}", "", "## Available stages"]
    for name, sd in stages.items():
        if name == "plan":
            continue
        lines.append(f"### {name}")
        lines.append(sd.description or "")
        lines.append(f"- state key: {sd.state_key or 'none'}; requires stages: {', '.join(sd.requires_stages) or 'none'}; "
                     f"entry gate: {sd.requires_gate or 'none'}; interactive: {'yes' if sd.interactive else 'no'}")
        lines.append("- flags: " + ("; ".join(f"`{k}` — {v}" for k, v in sd.flags.items()) or "none"))
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ validation
def validate_plan(plan: RunPlan, stages: dict[str, StageDef], project_stages: dict[str, dict[str, Any]]) -> list[str]:
    """Deterministic checks the engine applies before anyone sees the plan."""
    errors: list[str] = []
    if len(plan.steps) > MAX_STEPS:
        errors.append(f"too many steps ({len(plan.steps)} > {MAX_STEPS})")
    seen_state_keys: set[str] = set()
    for i, s in enumerate(plan.steps, 1):
        if s.stage == "plan" or s.stage not in stages:
            errors.append(f"step {i}: unknown stage {s.stage!r}; known: {', '.join(n for n in stages if n != 'plan')}")
            continue
        sd = stages[s.stage]
        bad = sorted(set(s.flags) - set(sd.flags))
        if bad:
            errors.append(f"step {i} ({s.stage}): unknown flags {bad}; allowed: {sorted(sd.flags) or 'none'}")
        for req in sd.requires_stages:
            done = project_stages.get(req, {}).get("status") in ("complete", "skipped")
            if not done and req not in seen_state_keys:
                errors.append(f"step {i} ({s.stage}): requires stage '{req}' which is neither complete nor planned earlier")
        if sd.state_key:
            seen_state_keys.add(sd.state_key)
    return errors


# ------------------------------------------------------------------ handlers
@handler("plan.survey")
async def survey(rt: JobRuntime) -> dict[str, Any]:
    rt.ctx.materialize()
    goal = str(rt.flags.get("goal") or "advance the proposal to the next gate")
    brief = build_brief(rt.ctx, STAGES, goal=goal, budget_usd=rt.flags.get("budget_usd"),
                        previous_failure=rt.flags.get("previous_failure"))
    path = rt.project_dir / "intermediate" / "planning_brief.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(brief)
    return {"brief": brief, "goal": goal, "summary": f"brief with {len(STAGES) - 1} stages"}


@handler("plan.propose")
async def propose(rt: JobRuntime) -> dict[str, Any]:
    info = rt.result_of("survey")
    project = rt.ws.require_project(rt.project_id)
    errors: list[str] = []
    plan: RunPlan | None = None
    for attempt in range(3):
        instructions = (f"Goal: {info['goal']}\nPropose the campaign as a `RunPlan`. Use only the stages and flag keys "
                        "listed in the planning brief.")
        if errors:
            instructions += ("\n\nYour previous plan was invalid; fix every item and return the full plan again:\n- "
                             + "\n- ".join(errors))
        res = await rt.agent("run_planner", phase=f"propose:{attempt + 1}", allowed_writes=set(),
                             inputs=[("research context", str(rt.project_dir / "context.md")),
                                     ("call spec", str(rt.project_dir / "intermediate" / "call_spec.json")),
                                     ("drafts", str(rt.project_dir / "drafts")),
                                     ("reviews", str(rt.project_dir / "reviews"))],
                             instructions=instructions, output_model=RunPlan,
                             extra={"Planning brief": info["brief"]})
        plan = RunPlan.model_validate(res.structured)
        errors = validate_plan(plan, STAGES, project.stages)
        rt.emit("plan:proposed", attempt=attempt + 1, steps=[s.model_dump(mode="json") for s in plan.steps], errors=errors)
        if not errors:
            break
    if errors or plan is None:
        raise JobFailed("planner produced an invalid plan: " + "; ".join(errors))
    return {"plan": plan.model_dump(mode="json"),
            "summary": f"{len(plan.steps)} steps: " + " → ".join(s.stage for s in plan.steps)}


@handler("plan.approve")
async def approve(rt: JobRuntime) -> dict[str, Any]:
    plan = RunPlan.model_validate(rt.result_of("propose")["plan"])
    rows = [{"id": f"step-{s.step}", "stage": s.stage, "flags": s.flags, "force": s.force,
             "rationale": s.rationale, "expected_outcome": s.expected_outcome} for s in plan.steps]
    text = [f"**Goal**: {plan.goal}", "", f"**Assessment**: {plan.assessment}"]
    if plan.questions_for_researcher:
        text += ["", "**Questions from the planner**:", *[f"- {q}" for q in plan.questions_for_researcher]]
    if plan.risks:
        text += ["", "**Risks**:", *[f"- {r}" for r in plan.risks]]
    if plan.estimated_cost_usd is not None:
        text += ["", f"Estimated cost: {plan.estimated_cost_usd:.2f} USD"]
    text += ["", "Approve, skip or reject each step; rejecting a step stops the campaign there."]
    ans = await rt.approve("Run plan", "\n".join(text), rows, decisions=["approve", "skip", "reject"], key="plan")
    if ans.get("decision") == "reject":
        raise JobFailed("plan rejected by the researcher")
    row_dec = ans.get("rows") or {}
    steps = []
    for s in plan.steps:
        d = str(row_dec.get(f"step-{s.step}", "approve")).lower()
        if d == "reject":
            break
        if d == "skip":
            continue
        steps.append(s)
    if not steps:
        raise JobFailed("no steps approved")
    body = {"goal": plan.goal, "assessment": plan.assessment, "risks": plan.risks,
            "questions_for_researcher": plan.questions_for_researcher, "stop_conditions": plan.stop_conditions,
            "estimated_cost_usd": plan.estimated_cost_usd, "plan_run_id": rt.ctx.run.id, "status": "approved",
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "steps": [{**s.model_dump(mode="json"), "status": "pending", "run_id": None, "error": None} for s in steps]}
    rt.graph.put_document(PLAN_DOCUMENT, f"Run plan — {plan.goal[:80]}", json.dumps(body, indent=2),
                          created_by=rt.job.id, file="intermediate/run_plan.json")
    rt.log_decision("Which campaign runs next?", " → ".join(f"{s.stage} {json.dumps(s.flags)}" for s in steps),
                    [plan.assessment, *(f"step {s.step}: {s.rationale}" for s in steps)], type="plan_approved")
    rt.emit("plan:approved", steps=[s.stage for s in steps], note=ans.get("note"))
    return {"steps": body["steps"], "summary": f"{len(steps)} of {len(plan.steps)} steps approved"}


def load_plan(graph) -> dict[str, Any] | None:
    doc = graph.document(PLAN_DOCUMENT)
    if not doc or not doc.data.get("body"):
        return None
    try:
        return json.loads(doc.data["body"])
    except json.JSONDecodeError:
        return None


def save_plan(graph, body: dict[str, Any]) -> None:
    graph.put_document(PLAN_DOCUMENT, f"Run plan — {body.get('goal', '')[:80]}", json.dumps(body, indent=2),
                       file="intermediate/run_plan.json")
