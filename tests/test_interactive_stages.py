"""ideate, finance, business-plan and figures with a scripted session client and fake query."""
import json
import re
from pathlib import Path

import pytest

from agency.domain.graph import NodeType
from agency.domain.runs import InboxKind, RunStatus
from agency.engine.runner import Engine
from tests.fake_sdk import FakeQuery, FakeSessionClient, agency_handlers
from tests.test_engine import CALLSPEC, evidence, responder as research_responder
from tests.test_pipeline_stages import Scripted


async def ideation_script(turn: int, prompt: str, options) -> str:
    """Turn 1: ask a question through can_use_tool, then submit framings and finish."""
    handlers = agency_handlers(options)
    if turn == 1:
        res = await options.can_use_tool("AskUserQuestion", {"questions": [
            {"question": "What problem are you solving?", "header": "Problem",
             "options": [{"label": "Scrap in LFP cathode plants"}, {"label": "Something else"}], "multiSelect": False}]}, None)
        answer = res.updated_input["answers"]["What problem are you solving?"]
        await handlers["submit_result"]({"kind": "framings", "payload": {"raw_idea": "digital twin for LFP", "interview_notes": f"problem: {answer}",
            "framings": [{"framing_id": "FRM-001", "statement": "A physics-based digital twin cuts scrap 10%", "mechanism": "PBM+DEM coupling",
                          "novelty_type": "first", "target_gap": "no plant-scale DT", "closest_competitor": "TwinHeat"},
                         {"framing_id": "FRM-002", "statement": "ML-only scrap prediction", "mechanism": "gradient boosting",
                          "novelty_type": "application", "target_gap": "no ML for CAM"}]}})
        await handlers["finish"]({"summary": "interview done"})
        return "Here are two framings."
    return "ok"


async def bp_script(turn: int, prompt: str, options) -> str:
    handlers = agency_handlers(options)
    for b in (1, 2):
        await handlers["submit_result"]({"kind": "interview_batch", "payload": {"batch": b, "theme": f"t{b}", "answers": [
            {"question_id": f"q{b}", "answer": "42", "source": "user"}]}})
    await handlers["finish"]({"summary": "2 batches"})
    return "done"


class InteractiveScripted(Scripted):
    def __call__(self, prompt, options):
        agent = prompt.splitlines()[0].split("`")[1]
        if agent == "literature_searcher" and "SHALLOW IDEATION PROBE" in prompt:
            start = int(prompt.split("SRC: SRC-")[1][:3])
            fid = re.search(r"Framing (FRM-\d+)", prompt).group(1)
            return {"structured": evidence(start, 3, fid.lower())}
        if agent == "idea_evaluator":
            framings = json.loads(prompt.split("Candidate framings:\n")[1].split("\nRaw idea")[0])
            return {"structured": {"project_name": "demo", "raw_idea": "dt", "status": "draft",
                                   "recommendation": "FRM-001 is the strongest",
                                   "candidate_framings": [{**{k: f.get(k, "") for k in ("framing_id", "statement", "mechanism", "novelty_type", "target_gap")},
                                                           "prior_art_summary": "close", "differentiation": "d",
                                                           "scores": {"novelty_defensibility": 8 if f["framing_id"] == "FRM-001" else 4,
                                                                      "gap_alignment": 7, "feasibility": 6}} for f in framings]}}
        if agent == "financial_modeler":
            if "INGEST MODE" in prompt:
                return {"structured": FIN_INPUTS}
            return {"structured": {"tables": {"capex": {"2027": 10}}, "metrics": {"cer_eur_per_tco2": 150, "payback_years": 6},
                                   "markdown": "| a | b |", "claims": [{"text": "CER is 150 €/t", "type": "financial", "status": "assumption", "supported_by": []}],
                                   "hard_threshold_checks": [{"check_id": "HR-CER", "description": "cer_eur_per_tco2 <= 200", "met": True, "hard_rejection_risk": True}]}}
        if agent == "financial_reviewer":
            return {"structured": {"sections": [{"section_name": "Section 4", "reviewer_type": "financial", "overall_score": 7, "major_issues": [], "fixes": []}],
                                   "hard_rejection_checks": [{"check_id": "HR-GHG", "description": "ghg >= 50", "met": False, "hard_rejection_risk": True}]}}
        if agent == "financial_narrative_writer":
            m = re.search(r"Write the draft to `([^`]+)`", prompt)
            sid = re.search(r"Draft section \*\*([^.]+)\.", prompt).group(1)
            async def write(opts):
                reg = Path(opts.cwd) / "memory" / "claim_registry.jsonl"
                cid = json.loads(reg.read_text().splitlines()[0])["claim_id"]
                Path(m.group(1)).write_text(f"## {sid}. Financial\n\nCER is 150 [{cid}].\n")
                Path(m.group(1)).with_name(Path(m.group(1)).stem + "_meta.json").write_text(
                    json.dumps({"section_name": "Financial maturity", "draft_text": "", "claim_ids": [cid]}))
            return {"hook": write, "structured": None}
        if agent == "bp_synthesizer":
            async def write(opts):
                p = Path(opts.cwd) / "intermediate" / "business_plan_facts.json"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps({"facts": [{"id": "f1", "value": 42, "source_ref": "interview:q1"}]}))
            return {"hook": write, "structured": None}
        if agent.startswith("bp_") and agent.endswith("_writer"):
            m = re.search(r"Write `([^`]+)`", prompt)
            async def write(opts):
                Path(m.group(1)).write_text(f"## {agent}\n\nBP text [TO BE COMPLETED — CFO] CLM-001\n")
            return {"hook": write, "structured": None}
        if agent == "bp_reviewer":
            return {"structured": {"sections": [{"section_name": "BP-1", "reviewer_type": "business_plan", "overall_score": 7, "major_issues": [], "fixes": []}]}}
        if agent in ("plot_renderer", "concept_image_generator"):
            fid = re.search(r"Render figure (F-\d+)", prompt).group(1)
            async def write(opts):
                p = Path(opts.cwd) / "figures" / f"{fid}.png"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b"\x89PNG fake " + fid.encode())
            return {"hook": write, "structured": {"figures": [{"figure_id": fid, "title": "t", "type": "bar", "generator": "matplotlib",
                                                                "location": "drafts/01.md", "status": "draft", "output_path": f"figures/{fid}.png"}]}}
        return super().__call__(prompt, options)


FIN_INPUTS = {"meta": {"project": "demo", "currency": "EUR", "base_year": 2026, "scenario_set": ["base"], "source": "test", "ingested_at": "2026-09-02"},
              "capex": {"categories": [{"name": "equipment", "scenario": "base", "by_year": {"2027": 10}}]},
              "opex": {"categories": [{"name": "labour", "scenario": "base", "by_year": {"2028": 2}}]},
              "financing": {"grant_request": {"amount": 5, "programme": "IF"}, "private_cofunding": [{"source": "x", "amount": 5, "instrument": "equity", "committed": True}]},
              "ghg_linkage": {"absolute_tco2_over_horizon": 100000, "relative_avoidance_pct": 60, "horizon_years": 10}}


class Answerer:
    """Inbox responder: picks the first option for questions, approves approvals, fills forms."""

    def __init__(self):
        self.items = []

    async def __call__(self, item):
        self.items.append(item)
        if item.kind == InboxKind.QUESTION:
            opts = item.payload.get("options") or []
            first = opts[0] if opts else "yes"
            label = first["label"] if isinstance(first, dict) else first
            return {"choice": label, "text": label}
        if item.kind == InboxKind.APPROVAL:
            return {"decision": "approve", "rows": {r["id"]: "approve" for r in item.payload["rows"]}}
        if item.kind == InboxKind.FORM:
            if "financial" in item.header.lower():
                return {"data": FIN_INPUTS}
            return {"data": {"text": "Call: three partners."}}
        return {"text": "continue"}


@pytest.fixture
def engine(ws, project):
    FakeSessionClient.scripts = {"idea_interviewer": ideation_script, "bp_interviewer": bp_script}
    scripted = InteractiveScripted()
    eng = Engine(ws, query_fn=FakeQuery(scripted), client_factory=FakeSessionClient)
    eng.inbox.responder = Answerer()
    return eng


async def test_ideate(ws, engine):
    ws.create_project("Fuzzy", project_id="fuzzy")   # no hypothesis -> ideation pending
    run = await engine.run_stage("fuzzy", "ideate")
    assert run.status == RunStatus.COMPLETED, run.error
    g = ws.graph("fuzzy")
    brief = g.one(NodeType.IDEATION_BRIEF)
    assert brief.data["status"] == "chosen" and brief.data["chosen_framing_id"] == "FRM-001"
    assert "digital twin cuts scrap" in g.document("context").data["hypothesis"]
    assert "## Hypothesis" in g.document("context").data["body"] and "_To be completed._" not in g.document("context").data["body"]
    assert len(g.sources()) == 6 and g.decisions("framing_chosen")
    kinds = [i.kind for i in engine.inbox.responder.items]
    assert kinds[0] == InboxKind.QUESTION and "Problem" in engine.inbox.responder.items[0].header
    assert ws.get_project("fuzzy").stages["ideation"]["status"] == "complete"
    assert ws.get_project("fuzzy").gates["scope"]["passed"] is False    # no call yet, but context now real


async def test_finance_business_plan_figures(ws, project, engine):
    g = ws.graph("demo")
    spec = dict(CALLSPEC, sections=CALLSPEC["sections"] + [{"id": "4", "title": "Financial maturity", "kind": "financial"},
                                                             {"id": "5", "title": "Business plan", "kind": "business_plan"}])
    from agency.domain.callspec import CallSpec
    from agency.engine.materialize import ingest_callspec
    ingest_callspec(g, CallSpec.model_validate(spec), job_id="test")
    ws.set_stage("demo", "call_parsing", "complete")
    ws.set_stage("demo", "writing", "complete")
    # ---- finance via the inbox form (no workbooks present)
    run = await engine.run_stage("demo", "finance")
    assert run.status == RunStatus.COMPLETED, run.error
    assert g.document("financial_inputs") and g.nodes(NodeType.FINANCIAL_TABLE)
    assert (ws.config.project_dir("demo") / "intermediate" / "financial_model.json").exists()
    assert g.section("4") and g.section("4").data["kind"] == "financial"
    reqs = {r["id"]: r["status"] for r in g.callspec_node().data["requirements"]}
    assert g.findings("financial") and g.decisions("finance_risk_ack")
    assert any(i.header == "Escalation" for i in engine.inbox.responder.items)
    # ---- business plan with the scripted interview
    run = await engine.run_stage("demo", "business-plan")
    assert run.status == RunStatus.COMPLETED, run.error
    interview = json.loads(g.document("business_plan_interview").data["body"])
    assert sorted(interview["batches"]) == ["1", "2"]
    assert len([s for s in g.sections() if s.data.get("kind") == "business_plan"]) == 4
    assert "CFO markers" in run.summary and g.document("business_plan_assembled")
    # ---- figures from a register
    g.put_document("figures_register", "Figures", "| Figure | Location | Purpose | Owner | Tool | Status |\n|---|---|---|---|---|---|\n"
                                                  "| F-01 | drafts/01 | bar chart of scrap | PE | matplotlib | tbd |\n"
                                                  "| F-02 | drafts/02 | concept hero | Comm | Fal.ai | tbd |\n")
    run = await engine.run_stage("demo", "figures")
    assert run.status == RunStatus.COMPLETED, run.error
    figs = {f.data["figure_id"]: f for f in g.nodes(NodeType.FIGURE)}
    assert set(figs) == {"F-01"}                                     # F-02 skipped: no FAL_KEY
    assert figs["F-01"].data["status"] == "draft" and ws.blobs.exists(figs["F-01"].data["blob"])
    assert "| draft |" in g.document("figures_register").data["body"]
    assert json.loads((ws.config.project_dir("demo") / "figures" / "index.json").read_text())["count"] == 1
    assert ws.get_project("demo").stages["figures"]["status"] == "complete"
