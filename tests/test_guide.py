"""Guidance: the deterministic 'what next' every surface shows."""
from agency.domain.graph import NodeType
from agency.policy.guide import next_step
from tests.test_engine import CALLSPEC


def test_guidance_walks_the_main_path(ws, project):
    pid = "demo"
    s = next_step(ws, pid)
    assert s["key"] == "upload_call" and s["action"]["kind"] == "upload_then_run"
    assert [p["label"] for p in s["path"]] == ["Call", "Idea", "Research", "Draft", "Review", "Export"]
    assert any("exploratory" in a for a in s["alternatives"]) and s["scope"] is None
    inputs = ws.config.project_dir(pid) / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    (inputs / "call.txt").write_text("call text")
    assert next_step(ws, pid)["action"] == {"kind": "run_stage", "stage": "parse-call"}
    g = ws.graph(pid)
    g.add(NodeType.CALL_SPEC, dict(CALLSPEC))
    ws.set_stage(pid, "call_parsing", "complete")
    # parsed but unconfigured scope → configure it (scope_only), then align the preliminary concept
    s = next_step(ws, pid)
    assert s["key"] == "configure_scope" and s["action"] == {"kind": "run_stage", "stage": "parse-call", "flags": {"scope_only": "1"}}
    ws.set_scope(pid, {})
    s = next_step(ws, pid)
    assert s["key"] == "align_concept" and s["action"]["flags"] == {"align_only": "1"}
    ws.set_concept_status(pid, "aligned")
    s = next_step(ws, pid)
    assert s["key"] == "confirm_eligibility" and [r["id"] for r in s["requirements"]] == ["E1"]
    ws.set_requirement_status(pid, "E1", "met", "three partners confirmed")
    assert next_step(ws, pid)["action"] == {"kind": "run_stage", "stage": "research"}
    g.put_document("outline", "Outline", "## 1. Excellence\n## 2. Impact\n## 3. Implementation")
    assert ws.check_gate(pid, "scope").passed is True
    ws.set_stage(pid, "research", "complete")
    ws.check_gate(pid, "evidence")
    assert next_step(ws, pid)["key"] == "evidence_gate"
    ws.set_stage(pid, "writing", "complete")
    assert next_step(ws, pid)["action"]["stage"] == "review"
    ws.set_stage(pid, "review", "complete")
    ws.check_gate(pid, "submission")
    assert next_step(ws, pid)["key"] == "submission_gate"
    ws.set_stage(pid, "export", "complete")
    s = next_step(ws, pid)
    assert s["key"] == "done" and s["action"]["kind"] == "none"          # external review excluded → not suggested


def test_guidance_call_first_then_ideation(ws):
    ws.create_project("Blank", project_id="blank")
    s = next_step(ws, "blank")
    assert s["key"] == "upload_call" and any("exploratory" in a for a in s["alternatives"])
    ws.set_stage("blank", "ideation", "skipped")
    assert next_step(ws, "blank")["key"] == "upload_call"
    g = ws.graph("blank")
    g.add(NodeType.CALL_SPEC, dict(CALLSPEC))
    ws.set_stage("blank", "call_parsing", "complete")
    ws.set_scope("blank", {})
    ws.set_stage("blank", "ideation", "pending")
    assert next_step(ws, "blank")["key"] == "ideate"
    from agency.domain.runs import InboxItem, InboxKind
    ws.store.put_inbox(InboxItem(id="i1", project_id="blank", kind=InboxKind.QUESTION, header="Q", question="Continue?",
                                 payload={}))
    s = next_step(ws, "blank")
    assert s["key"] == "inbox" and s["action"]["kind"] == "inbox"
    assert "next_step" in ws.status("blank")


def test_guidance_recommends_included_modules_and_hides_excluded(ws, project):
    pid = "demo"
    g = ws.graph(pid)
    g.add(NodeType.CALL_SPEC, dict(CALLSPEC))
    for key in ("call_parsing", "research"):
        ws.set_stage(pid, key, "complete")
    ws.set_concept_status(pid, "aligned")
    ws.set_scope(pid, {"finance": "included", "business_plan": "required", "figures": "excluded", "external_review": "included"})
    ws.set_requirement_status(pid, "E1", "met")
    ws.graph(pid).put_document("outline", "Outline", "## 1. x")
    s = next_step(ws, pid)
    assert s["key"] == "finance"                                # included finance comes before drafting
    side = {p["key"]: p for p in s["side"]}
    assert side["figures"]["scope_state"] == "excluded" and side["business_plan"]["scope_state"] == "required"
    ws.set_stage(pid, "finance", "complete")
    ws.set_stage(pid, "writing", "complete")
    assert next_step(ws, pid)["key"] == "business_plan"
    ws.set_stage(pid, "business_plan", "complete")
    assert next_step(ws, pid)["key"] not in ("figures",)       # excluded → never recommended
    for key in ("review", "export"):
        ws.set_stage(pid, key, "complete")
    s = next_step(ws, pid)
    assert s["key"] == "done" and s["action"]["stage"] == "external-feedback"


def test_requirement_status_validation(ws, project):
    import pytest
    with pytest.raises(KeyError):
        ws.set_requirement_status("demo", "E1", "met")        # no call spec yet
    ws.graph("demo").add(NodeType.CALL_SPEC, dict(CALLSPEC))
    with pytest.raises(ValueError):
        ws.set_requirement_status("demo", "E1", "maybe")
    with pytest.raises(KeyError):
        ws.set_requirement_status("demo", "E9", "met")
