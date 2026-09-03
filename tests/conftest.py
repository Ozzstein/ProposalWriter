import json
from pathlib import Path

import pytest

from agency.config import WorkspaceConfig, load_config
from agency.workspace import Workspace


@pytest.fixture
def ws(tmp_path: Path) -> Workspace:
    cfg = load_config(tmp_path / "ws")
    cfg.secrets = {}
    w = Workspace(cfg)
    yield w
    w.close()


@pytest.fixture
def project(ws: Workspace):
    return ws.create_project("Demo Project", project_id="demo", funder="EU", mechanism="IF",
                             hypothesis="A digital twin cuts scrap by 10%")


@pytest.fixture
def legacy_run(tmp_path: Path) -> Path:
    """A minimal legacy runs/{project}/ directory."""
    d = tmp_path / "runs" / "legacy-proj"
    (d / "memory").mkdir(parents=True)
    (d / "intermediate").mkdir()
    (d / "drafts").mkdir()
    (d / "reviews").mkdir()
    (d / "inputs").mkdir()
    (d / "state.json").write_text(json.dumps({
        "project_name": "legacy-proj", "funding_agency": "EU Innovation Fund", "mechanism": "Large-scale",
        "created_at": "2026-04-01",
        "stages": {"call_parsing": {"status": "complete"}, "research": {"status": "complete"},
                   "writing": {"status": "in_progress"}},
        "gates": {"scope": {"passed": True}, "evidence": {"passed": True}},
    }))
    (d / "context.md").write_text("# legacy — Research Context\n\n## Hypothesis\n\nLFP CAM plant with 30% lower CER.\n")
    with open(d / "memory" / "evidence_store.jsonl", "w") as f:
        for i in range(1, 14):
            f.write(json.dumps({"source_id": f"SRC-{i:03d}", "title": f"Paper {i}", "year": 2020 + i % 5,
                                "type": "paper", "quality": "high", "extract": "finding"}) + "\n")
    with open(d / "memory" / "claim_registry.jsonl", "w") as f:
        f.write(json.dumps({"claim_id": "CLM-001", "text": "LFP is safer", "type": "scientific_finding",
                            "supported_by": ["SRC-001", "SRC-002"], "status": "supported"}) + "\n")
        f.write(json.dumps({"claim_id": "CLM-002", "text": "Scrap drops 10%", "type": "technical_benefit",
                            "supported_by": [], "status": "unsupported"}) + "\n")
        f.write(json.dumps({"claim_id": "CLM-002", "text": "Scrap drops 10%", "type": "technical_benefit",
                            "supported_by": ["SRC-003"], "status": "supported"}) + "\n")
    with open(d / "memory" / "decision_log.jsonl", "w") as f:
        f.write(json.dumps({"decision_id": "DEC-001", "question": "Chemistry?", "decision": "LFP",
                            "rationale": ["safety"], "date": "2026-04-02"}) + "\n")
    (d / "intermediate" / "call_brief.json").write_text(json.dumps({
        "call_id": "INNOVFUND-2025-NZT", "title": "Clean tech manufacturing", "funder": "CINEA",
        "abstract_word_limit": 300}))
    (d / "intermediate" / "evaluation_matrix.json").write_text(json.dumps({"criteria": [
        {"criterion_id": "C1", "name": "GHG avoidance", "max_score": 15, "weight": 1},
        {"criterion_id": "C2", "name": "Innovation", "max_score": 15, "weight": 1}]}))
    (d / "intermediate" / "proposal_outline.md").write_text(
        "# Proposal outline\n\n## 1. Abstract\n\n## 2. Innovation\n\n## 3. Implementation\n")
    (d / "intermediate" / "sota_summary.md").write_text("# SOTA\n\n" + "x " * 200)
    (d / "intermediate" / "novelty_map.json").write_text(json.dumps({
        "project_name": "legacy-proj", "minimum_anchors_met": True, "novelty_anchors": [
            {"anchor_id": f"NOV-00{i}", "claim": f"anchor {i}", "novelty_type": "first", "dimension": "technical",
             "supported_by": ["SRC-001"], "confidence": "high", "attack_surface": "x",
             "defensibility_score": 7} for i in range(1, 4)]}))
    (d / "intermediate" / "gap_analysis.json").write_text(json.dumps({
        "project_name": "legacy-proj", "top_gaps_for_proposal": ["GAP-001"], "gaps": [
            {"gap_id": f"GAP-00{i}", "type": "technology", "sub_type": "studied-and-open",
             "description": f"gap {i}", "evidence_of_gap": ["SRC-002"], "severity": "major",
             "strategic_importance": 8} for i in range(1, 5)]}))
    (d / "drafts" / "01_abstract.md").write_text("# Abstract\n\nWe propose X (CLM-001).\n")
    (d / "drafts" / "02_innovation.md").write_text("# Innovation\n\nNovel because CLM-002.\n")
    (d / "drafts" / "03_implementation.md").write_text("# Implementation\n\nWork packages. CLM-001\n")
    (d / "reviews" / "scientific_review.json").write_text(json.dumps({"sections": [
        {"section_name": "Abstract", "reviewer_type": "scientific", "overall_score": 7,
         "major_issues": [], "fixes": []}]}))
    (d / "inputs" / "call.txt").write_text("call document text")
    return d
