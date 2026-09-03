"""End-to-end (mocked SDK) coverage of write-proposal, review loop, external-feedback and export."""
import asyncio
import json
import re
from pathlib import Path

import pytest

from agency.domain.graph import NodeType
from agency.domain.runs import InboxKind, RunStatus
from agency.engine.runner import Engine
from tests.fake_sdk import FakeQuery
from tests.test_engine import CALLSPEC, AutoApprove, evidence, gaps_payload, novelty, sota, responder as research_responder


class Scripted:
    """Responder that also writes draft files for writer contracts and scores panels upward."""

    def __init__(self):
        self.panel_calls = 0
        self.writer_calls = []

    def __call__(self, prompt: str, options):
        head = prompt.splitlines()[0]
        agent = head.split("`")[1]
        if agent.endswith("_writer"):
            self.writer_calls.append(agent)
            m = re.search(r"Write the draft to `([^`]+)`", prompt)
            sid = re.search(r"Draft section \*\*([^.]+)\.", prompt).group(1)
            target = Path(m.group(1))

            async def write(opts):
                target.parent.mkdir(parents=True, exist_ok=True)
                body = f"## {sid}. Section\n\nWe propose X because of CLM-001 and CLM-002 [SRC-001].\n" + "word " * 120
                if "Revise the existing draft" in prompt:
                    body += "\nRevised per reviewers CLM-003."
                target.write_text(body)
                target.with_name(target.stem + "_meta.json").write_text(json.dumps(
                    {"section_name": f"Section {sid}", "draft_text": "", "claim_ids": ["CLM-001", "CLM-002"],
                     "source_ids": ["SRC-001"], "open_issues": []}))
            return {"hook": write, "structured": None}
        if agent == "scientific_reviewer" or agent == "compliance_checker":
            if "PatchBatch" in prompt:
                return {"structured": {"patches": []}}
            sections = re.findall(r"^## ([^.]+)\. Section", (Path(options.cwd) / "drafts" / "x").parent.read_text() if False else "", re.M)
            secs = sorted(p.stem for p in (Path(options.cwd) / "drafts").glob("*.md"))
            return {"structured": {"sections": [
                {"section_name": f"Section {sid_from(s)}", "reviewer_type": "scientific" if agent == "scientific_reviewer" else "compliance",
                 "overall_score": 7.5, "major_issues": [], "fixes": [{"priority": "high", "action": f"tighten {s}"}] if s.startswith("01") and agent == "scientific_reviewer" else []}
                for s in secs]}}
        if agent == "adversarial_evaluator_simulator":
            self.panel_calls += 1
            pct = 55 + 10 * self.panel_calls
            return {"structured": {
                "project_name": "demo", "call_topic": "HE-2026-TEST", "hard_rejection_checks": [],
                "criterion_scores": [{"criterion_id": c, "criterion_name": c, "max_score": 5, "weight": 1,
                                      "predicted_score_central": 3 + 0.4 * self.panel_calls,
                                      "improvement_actions": [f"improve {c}"]} for c in ("C1", "C2", "C3")],
                "summary": {"total_predicted_weighted_score": 15 * pct / 100, "total_max_weighted_score": 15,
                            "score_percentage": pct, "funding_probability": "medium",
                            "improvement_actions_ranked": [{"rank": 1, "criterion": "C1", "action": "sharpen novelty", "estimated_score_gain": "+1"},
                                                           {"rank": 2, "criterion": "C2", "action": "quantify impact", "estimated_score_gain": "+0.5"}]}}}
        if agent == "feedback_parser":
            rel = re.search(r"source_file must be `([^`]+)`", prompt).group(1)
            return {"structured": {"entries": [
                {"round": 1, "source_file": rel, "location": "Section 1", "comment": "Cite the 2024 benchmark study.",
                 "category": "evidence", "status": "open", "dedupe_key": "r1-evidence"},
                {"round": 1, "source_file": rel, "location": "Section 2", "original_text": "We propose X",
                 "comment": "Say who 'we' is.", "category": "writing", "status": "open", "dedupe_key": "r1-writing"},
                {"round": 1, "source_file": rel, "location": "?", "comment": "Nice work.", "category": "ack",
                 "status": "open", "dedupe_key": "r1-ack"}]}}
        if agent == "feedback_applier":
            return {"structured": {"patches": [{"patch_id": "PATCH-001", "feedback_id": re.search(r'"feedback_id": "(FBK-\d+)"', prompt).group(1),
                                                "target_file": re.search(r"on `([^`]+)`", prompt).group(1),
                                                "old_text": "We propose X", "new_text": "The consortium proposes X",
                                                "rationale": "names the actor"}]}}
        if agent == "literature_searcher" and "feedback:evidence" in prompt:
            start = int(prompt.split("SRC: SRC-")[1][:3])
            return {"structured": evidence(start, 1, "fb")}
        return research_responder(prompt, options)


def sid_from(stem: str) -> str:
    m = re.match(r"^(\d+)", stem)
    return str(int(m.group(1))) if m else stem


@pytest.fixture
async def researched(ws, project):
    """A project that has passed parse-call and research (mocked)."""
    scripted = Scripted()
    eng = Engine(ws, query_fn=FakeQuery(scripted))
    eng.inbox.responder = AutoApprove()
    eng.scripted = scripted
    r1 = await eng.run_stage("demo", "parse-call")
    assert r1.status == RunStatus.COMPLETED, r1.error
    # confirm eligibility so the scope gate passes without --force
    g = ws.graph("demo")
    spec = g.callspec_node()
    for r in spec.data["requirements"]:
        r["status"] = "met"
    ws.store.put_node(spec)
    r2 = await eng.run_stage("demo", "research")
    assert r2.status == RunStatus.COMPLETED, r2.error
    return eng


async def test_write_review_feedback_export(ws, project, researched):
    eng = researched
    run = await eng.run_stage("demo", "write-proposal")
    assert run.status == RunStatus.COMPLETED, run.error
    g = ws.graph("demo")
    sections = g.sections()
    assert [s.data["section_id"] for s in sections] == ["0", "1", "2", "3"]
    calls = eng.scripted.writer_calls
    assert calls[0] == "excellence_writer" and calls[-1] == "abstract_writer"
    assert set(calls[1:3]) == {"impact_writer", "implementation_writer"}
    assert all(g.out(s.id).__len__() >= 1 for s in sections)          # CITES edges exist
    assert ws.get_project("demo").gates["draft"]["passed"] is True, ws.get_project("demo").gates["draft"]
    jobs = {j.name: j for j in ws.store.list_jobs(run.id)}
    assert jobs["draft:2"].deps == ["prepare", "draft:1"] and jobs["draft:0"].deps == ["draft:1", "draft:2", "draft:3"]

    # ---- review with the panel loop: scores rise 65 -> 75 -> 85 then plateau below min_gain? (max 3 iters)
    run = await eng.run_stage("demo", "review", flags={"iterations": "2", "min_gain": "5"})
    assert run.status == RunStatus.COMPLETED, run.error
    panels = sorted(g.nodes(NodeType.PANEL_SCORE), key=lambda n: n.data["iteration"])
    assert [p.data["summary"]["score_percentage"] for p in panels] == [65, 75, 85]
    assert g.document("revision_plan") and "sharpen novelty" in g.document("revision_plan").data["body"]
    assert g.findings("scientific") and g.findings("compliance")
    assert g.decisions("review_iteration")
    assert "Revised per reviewers" in g.section("1").data["draft_text"]
    # submission gate: scientific >= 6, no critical, compliance clean, panel >= 50, hard rules none
    assert ws.get_project("demo").gates["submission"]["passed"] is True, ws.get_project("demo").gates["submission"]

    # ---- external feedback round with pasted text
    run = await eng.run_stage("demo", "external-feedback", flags={"text": "Reviewer A: please cite the benchmark."})
    assert run.status == RunStatus.COMPLETED, run.error
    fb = {f.data["dedupe_key"]: f for f in g.feedback()}
    assert fb["r1-ack"].data["status"] == "ack"
    assert fb["r1-writing"].data["status"] == "resolved" and "patched" in fb["r1-writing"].data["resolution"]
    assert fb["r1-evidence"].data["status"] == "resolved" and "SRC-" in fb["r1-evidence"].data["resolution"]
    assert "The consortium proposes X" in g.section("2").data["draft_text"]
    assert g.nodes(NodeType.PATCH) and g.inn(g.nodes(NodeType.PATCH)[0].id)   # Feedback -> Patch edge
    assert ws.get_project("demo").gates["external_feedback"]["passed"] is True
    assert any(i.kind == InboxKind.APPROVAL and i.header.startswith("Triage") for i in eng.inbox.responder.items)

    # ---- export
    run = await eng.run_stage("demo", "export")
    assert run.status == RunStatus.COMPLETED, run.error
    final = ws.config.project_dir("demo") / "final"
    md = (final / "proposal.md").read_text()
    assert md.startswith("# Demo Project") and "## References" in md and "[SRC-001]" in md
    assert (final / "proposal.docx").stat().st_size > 1000
    assert ws.get_project("demo").stages["export"]["status"] == "complete"
    assert ws.store.sum_cost("demo") > 0


async def test_write_proposal_blocked_without_evidence(ws, project):
    from agency.engine.plan import StageBlocked
    eng = Engine(ws, query_fn=FakeQuery())
    with pytest.raises(StageBlocked):
        await eng.run_stage("demo", "write-proposal")


async def test_apply_patches_marks_stale(ws, project):
    from agency.domain.models import FeedbackPatch
    from agency.engine.runtime import JobRuntime, RunContext
    from agency.jobs.feedback import apply_patches
    g = ws.graph("demo")
    sec = g.add(NodeType.SECTION, {"section_id": "1", "section_name": "S", "draft_text": "alpha beta gamma", "claim_ids": [], "path": "01_s.md"})
    fb = g.add(NodeType.FEEDBACK, {"round": 1, "source_file": "x", "comment": "c", "category": "writing", "status": "in_progress", "dedupe_key": "k"})
    eng = Engine(ws, query_fn=FakeQuery())
    from agency.domain.runs import Job, JobKind, Run
    run = Run(id="r", project_id="demo", stage="external-feedback")
    ctx = RunContext(ws=ws, project_id="demo", run=run, catalogue=eng.catalogue, adapter=eng.adapter, inbox=eng.inbox,
                     packs=eng.packs, project_dir=ws.config.project_dir("demo"), kb_dir=ws.config.root / "kb")
    rt = JobRuntime(ctx, Job(id="j", run_id="r", name="dispatch", kind=JobKind.CODE))
    res = apply_patches(rt, [FeedbackPatch(feedback_id=fb.id, target_file="01_s.md", old_text="beta", new_text="BETA", rationale="r"),
                             FeedbackPatch(feedback_id=fb.id, target_file="01_s.md", old_text="zeta", new_text="Z", rationale="r"),
                             FeedbackPatch(feedback_id=fb.id, target_file="nope.md", old_text="a", new_text="b", rationale="r")], 1)
    assert len(res["applied"]) == 1 and len(res["stale"]) == 2
    assert g.section("1").data["draft_text"] == "alpha BETA gamma"
