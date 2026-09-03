"""The planning agent: brief → RunPlan → validation → approval → campaign execution."""
import json

import pytest

from agency.domain.models import RunPlan
from agency.domain.runs import InboxKind, RunStatus
from agency.engine.runner import Engine
from agency.jobs import STAGES
from agency.jobs.plan import build_brief, load_plan, validate_plan
from tests.fake_sdk import FakeQuery
from tests.test_engine import AutoApprove, responder

GOOD_PLAN = {
    "goal": "reach the evidence gate",
    "assessment": "Nothing has run yet; the call must be parsed before research can be scoped.",
    "steps": [
        {"step": 1, "stage": "parse-call", "rationale": "call spec drives everything"},
        {"step": 2, "stage": "research", "flags": {"retrievers": "literature_searcher,patent_scanner", "focus": "digital twins"},
         "force": True, "rationale": "eligibility is unknown, not failed; proceed past the scope gate", "expected_outcome": "evidence gate passes"},
    ],
    "risks": ["scope gate forced"], "questions_for_researcher": ["Is the consortium eligible?"], "estimated_cost_usd": 4.0,
}
BAD_PLAN = {
    "goal": "reach the evidence gate", "assessment": "guessing",
    "steps": [{"step": 1, "stage": "draft", "rationale": "x"},
              {"step": 2, "stage": "research", "flags": {"topic": "x"}, "rationale": "y"}],
}


def make_responder(plans):
    """Planner answers come from ``plans`` in order; everything else routes to the shared responder."""
    def _r(prompt: str, options):
        if "run_planner" in prompt.splitlines()[0]:
            return {"structured": plans.pop(0)}
        return responder(prompt, options)
    return _r


def test_validate_plan_reports_every_problem(ws, project):
    plan = RunPlan.model_validate(BAD_PLAN)
    errors = validate_plan(plan, STAGES, ws.get_project("demo").stages)
    assert any("unknown stage 'draft'" in e for e in errors)
    assert any("unknown flags ['topic']" in e for e in errors)
    assert any("requires stage 'call_parsing'" in e for e in errors)
    good = RunPlan.model_validate(GOOD_PLAN)
    assert validate_plan(good, STAGES, ws.get_project("demo").stages) == []
    too_many = good.model_copy(update={"steps": [good.steps[0].model_copy(update={"step": i}) for i in range(1, 11)]})
    assert any("too many steps" in e for e in validate_plan(too_many, STAGES, ws.get_project("demo").stages))


def test_brief_lists_stages_gates_and_flags(ws, project):
    from agency.domain.runs import Run
    from agency.engine.runtime import RunContext
    eng = Engine(ws, query_fn=FakeQuery(responder))
    run = Run(id="run-x", project_id="demo", stage="plan")
    ctx = RunContext(ws=ws, project_id="demo", run=run, catalogue=eng.catalogue, adapter=eng.adapter, inbox=eng.inbox,
                     packs=eng.packs, project_dir=ws.config.project_dir("demo"), kb_dir=ws.config.root / "kb")
    brief = build_brief(ctx, STAGES, goal="ship it", budget_usd="10", previous_failure="step 2 failed")
    assert "**Goal**: ship it" in brief and "step 2 failed" in brief
    assert "### research" in brief and "`focus`" in brief and "### plan" not in brief
    assert "- scope: FAIL" in brief and "not parsed yet" in brief


async def test_campaign_plans_retries_invalid_plan_and_executes(ws, project):
    fake = FakeQuery(make_responder([BAD_PLAN, GOOD_PLAN]))
    engine = Engine(ws, query_fn=fake)
    engine.inbox.responder = AutoApprove()
    result = await engine.run_campaign("demo", "reach the evidence gate", budget_usd=10)
    assert result["status"] == "completed", result
    assert [r["stage"] for r in result["runs"]] == ["plan", "parse-call", "research"]
    assert all(r["status"] == "completed" for r in result["runs"])
    # the invalid first plan was sent back with the validation errors
    planner_prompts = [c["prompt"] for c in fake.calls if "run_planner" in c["prompt"].splitlines()[0]]
    assert len(planner_prompts) == 2 and "unknown stage 'draft'" in planner_prompts[1]
    assert "## Planning brief" in planner_prompts[0] and "### research" in planner_prompts[0]
    # approval went through the inbox with one row per step
    approvals = [i for i in engine.inbox.responder.items if i.kind == InboxKind.APPROVAL and i.header == "Run plan"]
    assert len(approvals) == 1 and [r["stage"] for r in approvals[0].payload["rows"]] == ["parse-call", "research"]
    assert "Is the consortium eligible?" in approvals[0].question
    # the plan document tracks execution, flags reached the stage runs, the decision is logged
    g = ws.graph("demo")
    body = load_plan(g)
    assert body["status"] == "completed" and [s["status"] for s in body["steps"]] == ["completed", "completed"]
    research_run = ws.store.get_run(body["steps"][1]["run_id"])
    assert research_run.flags["focus"] == "digital twins" and g.decisions("gate_override")
    assert g.decisions("plan_approved") and ws.get_project("demo").gates["evidence"]["passed"] is True
    assert (ws.config.project_dir("demo") / "intermediate" / "planning_brief.md").exists()
    kinds = [e.kind for e in ws.events.replay(project_id="demo")]
    assert kinds.count("campaign:step") == 2 and "plan:approved" in kinds and "campaign:end" in kinds


async def test_campaign_honours_skip_and_stops_on_reject(ws, project):
    class SkipSecond(AutoApprove):
        async def __call__(self, item):
            if item.kind == InboxKind.APPROVAL and item.header == "Run plan":
                self.items.append(item)
                return {"decision": "approve", "rows": {"step-1": "approve", "step-2": "skip"}}
            return await super().__call__(item)

    engine = Engine(ws, query_fn=FakeQuery(make_responder([GOOD_PLAN])))
    engine.inbox.responder = SkipSecond()
    result = await engine.run_campaign("demo", "parse only")
    assert result["status"] == "completed" and [r["stage"] for r in result["runs"]] == ["plan", "parse-call"]

    class Reject(AutoApprove):
        async def __call__(self, item):
            if item.kind == InboxKind.APPROVAL and item.header == "Run plan":
                return {"decision": "reject", "rows": {}}
            return await super().__call__(item)

    engine2 = Engine(ws, query_fn=FakeQuery(make_responder([GOOD_PLAN])))
    engine2.inbox.responder = Reject()
    result = await engine2.run_campaign("demo", "again")
    assert result["status"] == "plan_failed" and "rejected" in result["error"]


async def test_campaign_replans_after_a_blocked_step(ws, project):
    blocked = {**GOOD_PLAN, "steps": [GOOD_PLAN["steps"][0], {**GOOD_PLAN["steps"][1], "force": False}]}
    fixed = {**GOOD_PLAN, "steps": [{**GOOD_PLAN["steps"][1], "step": 1}]}
    fake = FakeQuery(make_responder([blocked, fixed]))
    engine = Engine(ws, query_fn=fake)
    engine.inbox.responder = AutoApprove()
    result = await engine.run_campaign("demo", "reach the evidence gate", max_replans=1)
    assert result["status"] == "completed", result
    assert [r["stage"] for r in result["runs"]] == ["plan", "parse-call", "plan", "research"]
    second_brief = [c["prompt"] for c in fake.calls if "run_planner" in c["prompt"].splitlines()[0]][1]
    assert "Previous campaign stopped" in second_brief and "blocked" in second_brief
    assert result["attempts"] == 2


async def test_plan_only_mode(ws, project):
    engine = Engine(ws, query_fn=FakeQuery(make_responder([GOOD_PLAN])))
    engine.inbox.responder = AutoApprove()
    result = await engine.run_campaign("demo", "reach the evidence gate", execute=False)
    assert result["status"] == "planned" and [r["stage"] for r in result["runs"]] == ["plan"]
    assert load_plan(ws.graph("demo"))["status"] == "approved"
    assert ws.get_project("demo").stages["call_parsing"]["status"] == "pending"
