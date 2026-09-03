import asyncio
import json

import pytest

from agency.domain.graph import NodeType
from agency.domain.runs import InboxKind, JobKind, JobStatus, RunStatus
from agency.engine.materialize import materialize
from agency.engine.plan import JobSpec, StageBlocked, StageDef, StagePlan
from agency.engine.runner import Engine
from agency.jobs import HANDLERS, STAGES, handler
from tests.fake_sdk import FakeQuery, make_result

CALLSPEC = {
    "call_id": "HE-2026-TEST", "title": "Test call", "funder": "European Commission", "instrument": "RIA",
    "pack": "generic", "abstract_word_limit": 400,
    "sections": [{"id": "1", "title": "Excellence", "kind": "excellence", "weight": 0.4, "criterion_ids": ["C1"]},
                 {"id": "2", "title": "Impact", "kind": "impact", "weight": 0.3, "criterion_ids": ["C2"]},
                 {"id": "3", "title": "Implementation", "kind": "implementation", "weight": 0.3, "criterion_ids": ["C3"]}],
    "criteria": [{"id": "C1", "name": "Excellence", "max_score": 5, "threshold": 3},
                 {"id": "C2", "name": "Impact", "max_score": 5}, {"id": "C3", "name": "Implementation", "max_score": 5}],
    "requirements": [{"id": "E1", "kind": "eligibility", "text": "Three partners from three member states",
                      "disqualifying": True}],
}

ALIGNMENT = {"overall_fit": 7.5, "verdict": "fits_with_changes",
             "criterion_fits": [{"criterion_id": "C1", "fit": 8, "comment": "strong on excellence"}],
             "scope_misfits": [], "eligibility_conflicts": [],
             "suggested_hypothesis": "A validated digital twin cuts scrap by 10% in LFP cathode plants",
             "rationale": "fits the excellence criterion; quantify impact"}


def evidence(prefix_start: int, n: int = 6, contract: str = "x"):
    return {"task_id": "t", "topic": "lfp", "summary": "s",
            "sources": [{"source_id": f"SRC-{prefix_start + i:03d}", "title": f"{contract} paper {i}", "year": 2024,
                         "type": "paper", "quality": "high", "extract": "e", "doi": f"10.1/{contract}{i}"} for i in range(n)],
            "claims": [{"claim_text": f"{contract} finding", "source_ids": [f"SRC-{prefix_start:03d}"], "confidence": 0.8}]}


def sota():
    return {"summary_markdown": "# SOTA\n\n" + "word " * 400,
            "claims": [{"claim_id": f"CLM-{i:03d}", "text": f"claim {i}", "type": "scientific_finding",
                        "supported_by": ["SRC-001"], "status": "supported"} for i in range(1, 8)]}


def novelty():
    return {"project_name": "demo", "minimum_anchors_met": True, "novelty_summary": "novel",
            "novelty_anchors": [{"anchor_id": f"NOV-00{i}", "claim": f"a{i}", "novelty_type": "first",
                                 "dimension": "technical", "supported_by": ["SRC-001"], "confidence": "high",
                                 "attack_surface": "x", "defensibility_score": 7} for i in range(1, 4)]}


def gaps_payload():
    return {"project_name": "demo", "top_gaps_for_proposal": ["GAP-001", "GAP-002"], "gaps": [
        {"gap_id": f"GAP-00{i}", "type": "technology", "sub_type": "not-studied", "description": f"g{i}",
         "evidence_of_gap": ["SRC-002"], "severity": "major", "strategic_importance": 8} for i in range(1, 5)]}


def responder(prompt: str, options):
    """Route by the agent named in the task prompt header."""
    head = prompt.splitlines()[0]
    if "call_parser" in head:
        return {"structured": CALLSPEC}
    if "eligibility_parser" in head:
        return {"structured": {"requirements": [{"id": "E2", "kind": "deadline", "text": "Submit by 1 March"}]}}
    if "literature_searcher" in head:
        start = int(prompt.split("SRC: SRC-")[1][:3])
        return {"structured": evidence(start, 8, "lit")}
    if "patent_scanner" in head:
        start = int(prompt.split("SRC: SRC-")[1][:3])
        return {"structured": evidence(start, 5, "pat")}
    if "state_of_art_synthesizer" in head:
        return {"structured": sota()}
    if "novelty_mapper" in head:
        return {"structured": novelty()}
    if "gap_analyzer" in head:
        return {"structured": gaps_payload()}
    if "idea_evaluator" in head and "CALL ALIGNMENT CHECK" in prompt:
        return {"structured": ALIGNMENT}
    return {"structured": None}


class AutoApprove:
    """Inbox responder that approves everything and pastes call text when asked."""

    def __init__(self):
        self.items = []

    async def __call__(self, item):
        self.items.append(item)
        if item.kind == InboxKind.APPROVAL:
            return {"decision": "approve", "rows": {r["id"]: "approve" for r in item.payload["rows"]}}
        if item.kind == InboxKind.FORM:
            return {"data": {"text": "Call for proposals: three partners from three member states."}}
        return {"choice": "yes", "text": "yes"}


@pytest.fixture
def engine(ws, project):
    fake = FakeQuery(responder)
    eng = Engine(ws, query_fn=fake)
    eng.inbox.responder = AutoApprove()
    eng.fake = fake
    return eng


async def test_parse_call_then_research_end_to_end(ws, project, engine):
    run = await engine.run_stage("demo", "parse-call")
    assert run.status == RunStatus.COMPLETED, run.error
    jobs = {j.name: j for j in ws.store.list_jobs(run.id)}
    assert jobs["parse_call"].kind == JobKind.AGENT and jobs["approve_outline"].status == JobStatus.COMPLETED
    g = ws.graph("demo")
    spec = g.callspec_node().data
    assert [s["id"] for s in spec["sections"]] == ["0", "1", "2", "3"]      # abstract added by the pack merge
    assert {r["id"] for r in spec["requirements"]} == {"E1", "E2"}
    assert g.document("outline") and "Excellence" in g.document("outline").data["body"]
    assert ws.get_project("demo").stages["call_parsing"]["status"] == "complete"
    assert ws.get_project("demo").gates["scope"]["passed"] is False     # eligibility E1 still unknown
    assert engine.inbox.responder.items[0].kind == InboxKind.FORM       # no call file -> asked for text
    # research is blocked by the scope gate unless forced
    with pytest.raises(StageBlocked):
        await engine.run_stage("demo", "research")
    run2 = await engine.run_stage("demo", "research", force=True)
    assert run2.status == RunStatus.COMPLETED, run2.error
    assert g.decisions("gate_override")
    names = [c["prompt"].splitlines()[0] for c in engine.fake.calls]
    order = [n.split("`")[1] for n in names]
    assert order[:2] == ["call_parser", "eligibility_parser"]
    lit, pat, syn = order.index("literature_searcher"), order.index("patent_scanner"), order.index("state_of_art_synthesizer")
    assert max(lit, pat) < syn < order.index("novelty_mapper") and "web_scraper" not in order
    # reserved SRC ranges are disjoint and honoured
    srcs = g.sources()
    assert len(srcs) == 13 and len({s.id for s in srcs}) == 13
    assert len(g.claims()) == 7 + 2 and len(g.anchors()) == 3 and len(g.gaps()) == 4
    assert g.document("sota_summary")
    assert ws.get_project("demo").gates["evidence"]["passed"] is True, ws.get_project("demo").gates["evidence"]
    assert run2.cost_usd > 0 and ws.store.sum_cost("demo") == pytest.approx(run.cost_usd + run2.cost_usd)
    # the project dir mirrors the graph for agents
    pdir = ws.config.project_dir("demo")
    assert (pdir / "intermediate" / "novelty_map.json").exists()
    assert len((pdir / "memory" / "evidence_store.jsonl").read_text().splitlines()) == 13
    kinds = [e.kind for e in ws.events.replay(project_id="demo")]
    assert kinds.count("stage:start") == 2 and "inbox:pending" in kinds and "job:done" in kinds


async def test_scheduler_skips_dependents_and_tolerates_optional(ws, project):
    calls = []

    @handler("t.ok")
    async def ok(rt):
        calls.append(rt.job.name)
        return {"summary": "ok"}

    @handler("t.fail")
    async def fail(rt):
        raise RuntimeError("boom")

    def planner(ctx):
        return StagePlan("t", [JobSpec("a", "t.ok"), JobSpec("b", "t.fail", deps=["a"], optional=True),
                               JobSpec("c", "t.ok", deps=["a"]), JobSpec("d", "t.fail", deps=["c"]),
                               JobSpec("e", "t.ok", deps=["d"])])

    STAGES["t-stage"] = StageDef(name="t-stage", state_key=None, planner=planner)
    eng = Engine(ws, query_fn=FakeQuery())
    run = await eng.run_stage("demo", "t-stage")
    jobs = {j.name: j.status for j in ws.store.list_jobs(run.id)}
    assert jobs == {"a": JobStatus.COMPLETED, "b": JobStatus.FAILED, "c": JobStatus.COMPLETED,
                    "d": JobStatus.FAILED, "e": JobStatus.SKIPPED}
    assert run.status == RunStatus.FAILED and "d: boom" in run.error
    # resume re-uses completed jobs
    run2 = await eng.run_stage("demo", "t-stage", resume=run.id)
    assert calls.count("a") == 1 and calls.count("c") == 1
    assert run2.status == RunStatus.FAILED
    del STAGES["t-stage"]


async def test_inbox_round_trip_without_responder(ws, project):
    @handler("t.ask")
    async def ask(rt):
        ans = await rt.ask("Proceed?", ["yes", "no"], key="q1")
        return {"summary": ans["choice"]}

    STAGES["t-ask"] = StageDef(name="t-ask", state_key=None, planner=lambda ctx: StagePlan("t-ask", [JobSpec("q", "t.ask")]))
    eng = Engine(ws, query_fn=FakeQuery())
    task = asyncio.create_task(eng.run_stage("demo", "t-ask"))
    for _ in range(50):
        await asyncio.sleep(0.01)
        pending = eng.inbox.pending("demo")
        if pending:
            break
    assert pending and pending[0].kind == InboxKind.QUESTION
    assert ws.store.get_run(pending[0].run_id).status == RunStatus.WAITING_FOR_USER
    eng.inbox.answer(pending[0].id, {"choice": "yes"})
    run = await task
    assert run.status == RunStatus.COMPLETED and run.summary == "yes"
    del STAGES["t-ask"]


def test_materialize_round_trip(ws, legacy_run):
    from agency.legacy.importer import import_legacy_project
    import_legacy_project(ws, legacy_run)
    g = ws.graph("legacy-proj")
    pdir = ws.config.project_dir("legacy-proj")
    counts = materialize(g, pdir, ws.blobs)
    assert counts["evidence_store.jsonl"] == 13 and counts["drafts"] == 3 and counts["inputs"] == 1
    assert (pdir / "drafts" / "01_abstract.md").read_text().startswith("# Abstract")
    assert json.loads((pdir / "intermediate" / "call_spec.json").read_text())["criteria"][0]["id"] == "C1"
    assert (pdir / "inputs" / "call.txt").read_text() == "call document text"


async def test_excluded_stage_is_blocked_unless_forced(ws, project):
    from agency.domain.scope import ScopeConfig
    ws.set_scope("demo", {"figures": "excluded"})
    eng = Engine(ws, query_fn=FakeQuery())
    with pytest.raises(StageBlocked, match="excluded by the project scope"):
        await eng.run_stage("demo", "figures")
    run = await eng.run_stage("demo", "figures", force=True)     # empty register → completes with nothing to do
    assert run.status in (RunStatus.COMPLETED, RunStatus.FAILED)
    assert ScopeConfig.load(ws.get_project("demo")).figures.state == "included"
    d = ws.graph("demo").decisions("scope_changed")
    assert any("figures: excluded -> included" in x.data["decision"] for x in d)
    assert STAGES["figures"].scope_key == "figures" and STAGES["finance"].scope_key == "finance"
    assert STAGES["business-plan"].scope_key == "business_plan"
    assert STAGES["external-feedback"].scope_key == "external_review"
    assert STAGES["research"].scope_key is None


def test_draftable_sections_skip_excluded_finance(ws, project):
    from agency.domain.callspec import CallSpec
    from agency.domain.scope import apply_scope_change, derive_scope
    from agency.jobs.drafting import draftable_sections
    spec = CallSpec.model_validate(dict(CALLSPEC, sections=CALLSPEC["sections"] + [
        {"id": "4", "title": "Financial maturity", "kind": "financial"}]))
    scope = derive_scope(spec)                                     # finance required by the call
    assert "4" in [s.id for s, _ in draftable_sections(spec, scope=scope)]
    excluded = derive_scope(CallSpec.model_validate(CALLSPEC))     # a call without financials → excluded
    assert "4" not in [s.id for s, _ in draftable_sections(spec, scope=excluded)]
    assert "4" in [s.id for s, _ in draftable_sections(spec)]      # no scope → unchanged behaviour


async def test_parse_call_configures_scope_and_aligns_the_concept(ws, project, engine):
    from agency.domain.scope import ScopeConfig
    run = await engine.run_stage("demo", "parse-call")
    assert run.status == RunStatus.COMPLETED, run.error
    jobs = {j.name: j for j in ws.store.list_jobs(run.id)}
    assert jobs["configure_scope"].status == JobStatus.COMPLETED and jobs["align_concept"].status == JobStatus.COMPLETED
    scope = ScopeConfig.load(ws.get_project("demo"))
    assert scope.configured_at and scope.finance.state == "excluded"        # CALLSPEC has no financials
    g = ws.graph("demo")
    assert g.decisions("scope_configured") and g.decisions("concept_alignment")
    assert ws.concept_status("demo") == "aligned"                            # AutoApprove answers "yes" → keep
    assert g.document("concept_alignment").data["verdict"] == "fits_with_changes"
    kinds = [i.kind for i in engine.inbox.responder.items]
    assert kinds == [InboxKind.FORM, InboxKind.APPROVAL, InboxKind.FORM, InboxKind.QUESTION]
    assert engine.inbox.responder.items[2].header == "Configure proposal scope"
    # scope_only re-runs just the form; align_only refuses when nothing is preliminary
    run2 = await engine.run_stage("demo", "parse-call", flags={"scope_only": "1"})
    assert run2.status == RunStatus.COMPLETED and {j.name for j in ws.store.list_jobs(run2.id)} == {"configure_scope", "finalize"}
    run3 = await engine.run_stage("demo", "parse-call", flags={"align_only": "1"})
    assert run3.status == RunStatus.FAILED and "nothing to align" in run3.error


async def test_align_concept_adopt_and_reopen(ws, project):
    class Chooser(AutoApprove):
        def __init__(self, pick):
            super().__init__()
            self.pick = pick

        async def __call__(self, item):
            if item.kind == InboxKind.QUESTION and item.header.startswith("Align"):
                self.items.append(item)
                opts = item.payload["options"]
                assert opts[0].startswith("keep") and opts[1].startswith("adopt") and opts[2].startswith("reopen")
                return {"choice": opts[self.pick]}
            return await super().__call__(item)

    eng = Engine(ws, query_fn=FakeQuery(responder))
    eng.inbox.responder = Chooser(1)                                   # adopt
    run = await eng.run_stage("demo", "parse-call")
    assert run.status == RunStatus.COMPLETED, run.error
    ctx = ws.graph("demo").document("context").data
    assert ctx["hypothesis"] == ALIGNMENT["suggested_hypothesis"] and ctx["concept_status"] == "aligned"
    assert any(d.data["decision"] == "adopted" for d in ws.graph("demo").decisions("concept_alignment"))
    # reopen keeps it preliminary and the scope gate stays closed on alignment
    ctx_doc = ws.graph("demo").document("context")
    ws.graph("demo").update(ctx_doc, hypothesis="A digital twin cuts scrap by 10%", concept_status="preliminary")
    eng.inbox.responder = Chooser(2)
    run = await eng.run_stage("demo", "parse-call", flags={"align_only": "1"})
    assert run.status == RunStatus.COMPLETED, run.error
    assert ws.concept_status("demo") == "preliminary"
    assert any("not aligned" in b for b in ws.check_gate("demo", "scope").blockers)


async def test_parse_call_scope_only_needs_a_callspec(ws, project):
    eng = Engine(ws, query_fn=FakeQuery(responder))
    run = await eng.run_stage("demo", "parse-call", flags={"scope_only": "1"})
    assert run.status == RunStatus.FAILED and "parse the call first" in run.error
