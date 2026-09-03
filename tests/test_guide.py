"""Guidance: the deterministic 'what next' every surface shows."""
import json

from agency.domain.graph import NodeType
from agency.policy.guide import next_step
from tests.test_engine import CALLSPEC


def test_guidance_walks_the_main_path(ws, project):
    pid = "demo"
    s = next_step(ws, pid)
    assert s["key"] == "upload_call" and s["action"]["kind"] == "upload_then_run"
    assert [p["label"] for p in s["path"]] == ["Idea", "Call", "Research", "Draft", "Review", "Export"]
    # a file in inputs/ turns it into "parse the call"
    inputs = ws.config.project_dir(pid) / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    (inputs / "call.txt").write_text("call text")
    assert next_step(ws, pid)["action"] == {"kind": "run_stage", "stage": "parse-call"}
    # parsed call with an unconfirmed disqualifying requirement → confirm eligibility
    g = ws.graph(pid)
    g.add(NodeType.CALL_SPEC, dict(CALLSPEC))
    ws.set_stage(pid, "call_parsing", "complete")
    s = next_step(ws, pid)
    assert s["key"] == "confirm_eligibility" and [r["id"] for r in s["requirements"]] == ["E1"]
    ws.set_requirement_status(pid, "E1", "met", "three partners confirmed")
    assert g.callspec_node().data["requirements"][0]["status"] == "met"
    assert g.decisions("requirement_status")
    assert next_step(ws, pid)["action"] == {"kind": "run_stage", "stage": "research"}
    g.put_document("outline", "Outline", "## 1. Excellence\n## 2. Impact\n## 3. Implementation")
    assert ws.check_gate(pid, "scope").passed is True
    ws.set_stage(pid, "research", "complete")
    # evidence gate fails on an empty graph → strengthen evidence, not draft
    ws.check_gate(pid, "evidence")
    assert next_step(ws, pid)["key"] == "evidence_gate"
    ws.set_stage(pid, "writing", "complete")
    assert next_step(ws, pid)["action"]["stage"] == "review"
    ws.set_stage(pid, "review", "complete")
    ws.check_gate(pid, "submission")
    assert next_step(ws, pid)["key"] == "submission_gate"
    ws.set_stage(pid, "export", "complete")
    assert next_step(ws, pid)["key"] == "done"


def test_guidance_prefers_inbox_and_hypothesis(ws):
    p = ws.create_project("Blank", project_id="blank")
    assert next_step(ws, "blank")["key"] == "ideate"
    ws.set_stage("blank", "ideation", "skipped")
    assert next_step(ws, "blank")["key"] == "upload_call"
    from agency.domain.runs import InboxItem, InboxKind
    ws.store.put_inbox(InboxItem(id="i1", project_id="blank", kind=InboxKind.QUESTION, header="Q", question="Continue?",
                                 payload={}))
    s = next_step(ws, "blank")
    assert s["key"] == "inbox" and s["action"]["kind"] == "inbox"
    assert "next_step" in ws.status("blank")


def test_requirement_status_validation(ws, project):
    import pytest
    with pytest.raises(KeyError):
        ws.set_requirement_status("demo", "E1", "met")        # no call spec yet
    ws.graph("demo").add(NodeType.CALL_SPEC, dict(CALLSPEC))
    with pytest.raises(ValueError):
        ws.set_requirement_status("demo", "E1", "maybe")
    with pytest.raises(KeyError):
        ws.set_requirement_status("demo", "E9", "met")
