import pytest

from agency.domain.callspec import CallSpec, CriterionSpec, RequirementSpec, SectionSpec
from agency.domain.graph import EdgeType, NodeType
from agency.domain.models import Claim, Gap, NoveltyAnchor, Source
from agency.policy.gates import evaluate_gate


def _spec():
    return CallSpec(call_id="C", title="T", funder="F", sections=[
        SectionSpec(id="1", title="Abstract", kind="abstract", word_limit=50),
        SectionSpec(id="2", title="Innovation", kind="excellence"),
    ], criteria=[CriterionSpec(id="C1", name="Innovation", max_score=5)],
        requirements=[RequirementSpec(id="R1", kind="eligibility", text="EU entity", disqualifying=True)])


def test_scope_gate(ws, project):
    g = ws.graph("demo")
    r = evaluate_gate("scope", g)
    assert not r.passed and any("CallSpec" in b for b in r.blockers)
    spec = _spec()
    g.add(NodeType.CALL_SPEC, spec.model_dump(mode="json"))
    g.put_document("outline", "Outline", "## 1. Abstract\n## 2. Innovation")
    r = evaluate_gate("scope", g)
    assert not r.passed and any("Eligibility" in b for b in r.blockers)
    spec.requirements[0].status = "met"
    ws.set_scope("demo", {})
    ws.set_concept_status("demo", "aligned")
    r = evaluate_gate("scope", g, callspec=spec)
    assert r.passed, r.blockers


def test_scope_gate_rejects_placeholder_context(ws):
    ws.create_project("Empty", project_id="empty")
    g = ws.graph("empty")
    g.add(NodeType.CALL_SPEC, _spec().model_dump(mode="json"))
    g.put_document("outline", "Outline", "## 1. x")
    r = evaluate_gate("scope", g)
    assert any("hypothesis" in b for b in r.blockers)


def _populate_evidence(g, n_sources=12, n_anchors=3, n_gaps=4, defensibility=7):
    srcs = [g.add(NodeType.SOURCE, Source(title=f"S{i}", extract="")) for i in range(n_sources)]
    g.put_document("sota_summary", "SOTA", "x " * 200)
    for i in range(n_anchors):
        g.add(NodeType.NOVELTY_ANCHOR, NoveltyAnchor(claim=f"a{i}", novelty_type="first", dimension="technical",
                                                     supported_by=[srcs[0].id], confidence="high",
                                                     attack_surface="x", defensibility_score=defensibility))
    for i in range(n_gaps):
        gap = g.add(NodeType.GAP, Gap(type="technology", sub_type="not-studied", description=f"g{i}",
                                      evidence_of_gap=[srcs[0].id], severity="major", strategic_importance=8))
        if i == 0:
            g.update(gap, priority_rank=1)
    c = g.add(NodeType.CLAIM, Claim(text="c", type="scientific_finding", status="supported", supported_by=[srcs[0].id]))
    return srcs, c


def test_evidence_gate_thresholds(ws, project):
    g = ws.graph("demo")
    _populate_evidence(g, n_sources=11)
    r = evaluate_gate("evidence", g)
    assert not r.passed and any(">= 12 sources" in b for b in r.blockers)
    g.add(NodeType.SOURCE, Source(title="extra", extract=""))
    assert evaluate_gate("evidence", g).passed
    # thresholds are overridable, never hard-coded elsewhere
    assert not evaluate_gate("evidence", g, thresholds={"min_evidence": 20}).passed
    # weak anchors fail
    for a in g.anchors():
        g.update(a, defensibility_score=4)
    assert any("defensibility" in b for b in evaluate_gate("evidence", g).blockers)


def test_unsupported_ratio(ws, project):
    g = ws.graph("demo")
    _populate_evidence(g)
    g.add(NodeType.CLAIM, Claim(text="u", type="assumption", status="unsupported"))
    r = evaluate_gate("evidence", g)
    assert any("unsupported" in b for b in r.blockers)


def test_draft_gate(ws, project):
    g = ws.graph("demo")
    spec = _spec()
    g.add(NodeType.CALL_SPEC, spec.model_dump(mode="json"))
    srcs, c = _populate_evidence(g)
    r = evaluate_gate("draft", g)
    assert not r.passed and any("missing: ['1', '2']" in b for b in r.blockers)
    s1 = g.add(NodeType.SECTION, {"section_id": "1", "section_name": "Abstract", "kind": "abstract",
                                  "draft_text": "We propose " + c.id, "claim_ids": [c.id]}, status="draft")
    g.link(s1, c, EdgeType.CITES)
    s2 = g.add(NodeType.SECTION, {"section_id": "2", "section_name": "Innovation",
                                  "draft_text": "Novel [ASSUMPTION] [ASSUMPTION] [ASSUMPTION] " + c.id,
                                  "claim_ids": [c.id]}, status="draft")
    r = evaluate_gate("draft", g)
    assert any("[ASSUMPTION]" in b for b in r.blockers)
    g.update(s2, draft_text="Novel because CLM-999 " + c.id)
    r = evaluate_gate("draft", g)
    assert any("CLM-999" in b for b in r.blockers)
    g.update(s2, draft_text="Novel because " + c.id)
    assert evaluate_gate("draft", g).passed, evaluate_gate("draft", g).blockers
    g.update(s1, draft_text="word " * 60 + c.id)
    assert any("word limit" in b for b in evaluate_gate("draft", g).blockers)


def test_submission_gate(ws, project):
    g = ws.graph("demo")
    g.add(NodeType.CALL_SPEC, _spec().model_dump(mode="json"))
    r = evaluate_gate("submission", g)
    assert not r.passed and len(r.blockers) >= 3
    s = g.add(NodeType.SECTION, {"section_id": "1", "section_name": "Abstract", "draft_text": "x", "claim_ids": []})
    g.add(NodeType.REVIEW_FINDING, {"section_name": "Abstract", "reviewer_type": "scientific", "overall_score": 7,
                                    "major_issues": [], "fixes": [{"priority": "critical", "action": "fix"}], "round": 1})
    g.add(NodeType.REVIEW_FINDING, {"section_name": "Abstract", "reviewer_type": "compliance", "overall_score": 9,
                                    "major_issues": [], "fixes": [], "round": 1})
    r = evaluate_gate("submission", g)
    assert any("critical" in b for b in r.blockers)
    g.add(NodeType.REVIEW_FINDING, {"section_name": "Abstract", "reviewer_type": "scientific", "overall_score": 8,
                                    "major_issues": [], "fixes": [], "round": 2})
    g.add(NodeType.PANEL_SCORE, {"iteration": 1, "summary": {"score_percentage": 72,
                                                             "hard_rejection_risks_detected": []}})
    u = g.add(NodeType.CLAIM, Claim(text="u", type="assumption", status="unsupported"))
    r = evaluate_gate("submission", g)
    assert any("unsupported" in b for b in r.blockers)
    g.add(NodeType.DECISION, {"question": "ok?", "decision": f"approve {u.id}", "rationale": ["r"],
                              "type": "approve_unsupported_claim", "evidence_refs": [u.id]})
    r = evaluate_gate("submission", g)
    assert r.passed, r.blockers


def test_external_feedback_gate(ws, project):
    g = ws.graph("demo")
    assert evaluate_gate("external-feedback", g).not_applicable
    f = g.add(NodeType.FEEDBACK, {"round": 1, "source_file": "r.md", "comment": "c", "category": "writing",
                                  "status": "open", "dedupe_key": "k"})
    r = evaluate_gate("external_feedback", g)
    assert not r.passed and "still open" in r.blockers[0]
    g.update(f, status="stale")
    assert any("stale" in b for b in evaluate_gate("external_feedback", g).blockers)
    g.update(f, status="resolved", resolution="done")
    assert evaluate_gate("external_feedback", g).passed


def test_unknown_gate(ws, project):
    with pytest.raises(ValueError):
        evaluate_gate("nope", ws.graph("demo"))


def test_workspace_gate_records_project(ws, project):
    r = ws.check_gate("demo", "scope")
    assert r.passed is False
    assert ws.get_project("demo").gates["scope"]["blockers"]


from agency.domain.models import FeedbackEntry


def test_scope_gate_needs_configured_scope_and_aligned_concept(ws, project):
    g = ws.graph("demo")
    spec = _spec()
    spec.requirements[0].status = "met"
    g.add(NodeType.CALL_SPEC, spec.model_dump(mode="json"))
    g.put_document("outline", "Outline", "## 1. Abstract\n## 2. Innovation")
    r = evaluate_gate("scope", g)
    assert any("scope not configured" in b for b in r.blockers)
    assert any("preliminary concept not aligned" in b for b in r.blockers)
    ws.set_scope("demo", {})                       # confirm the derived scope
    ws.set_concept_status("demo", "aligned")
    assert evaluate_gate("scope", g).passed, evaluate_gate("scope", g).blockers


def test_scope_gate_alignment_passes_without_a_hypothesis(ws):
    ws.create_project("Empty", project_id="empty")
    g = ws.graph("empty")
    r = evaluate_gate("scope", g)
    aligned = next(c for c in r.criteria if c.criterion.startswith("Concept aligned"))
    assert aligned.met and "no hypothesis" in aligned.notes


def test_draft_gate_blocks_on_required_modules(ws, project):
    g = ws.graph("demo")
    spec = _spec()
    spec.sections.append(SectionSpec(id="4", title="Financial", kind="financial"))
    g.add(NodeType.CALL_SPEC, spec.model_dump(mode="json"))
    ws.put_scope("demo", ws.recommend_scope("demo"))      # finance required by the call
    r = evaluate_gate("draft", g)
    assert any("Required modules complete" in b and "finance" in b for b in r.blockers)
    ws.set_stage("demo", "finance", "complete")
    r = evaluate_gate("draft", g)
    assert not any("Required modules" in b for b in r.blockers)


def test_submission_gate_external_review_rule_only_when_required(ws, project):
    g = ws.graph("demo")
    names = [c.criterion for c in evaluate_gate("submission", g).criteria]
    assert not any("External review" in n for n in names)
    ws.set_scope("demo", {"external_review": "required"})
    r = evaluate_gate("submission", g)
    assert any("External review" in b and "no external feedback" in b for b in r.blockers)
    g.add(NodeType.FEEDBACK, FeedbackEntry(round=1, source_file="r.md", location="1", comment="x",
                                           category="writing", status="resolved", dedupe_key="k"))
    r = evaluate_gate("submission", g)
    ext = next(c for c in r.criteria if c.criterion.startswith("External review"))
    assert ext.met, ext.notes
