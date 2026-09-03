from agency.domain.graph import EdgeType, NodeType
from agency.legacy.importer import import_legacy_project, outline_to_sections
from agency.policy.gates import evaluate_gate


def test_outline_parser():
    secs = outline_to_sections("# Outline\n## 1. Abstract\n### 1.1 Summary\n## 2 — Innovation\n## 4.1b Impact")
    assert [s.id for s in secs] == ["1", "1.1", "2", "4.1b"]
    assert secs[0].kind == "abstract" and secs[2].kind == "excellence"


def test_import_legacy_run(ws, legacy_run):
    counts = import_legacy_project(ws, legacy_run)
    assert counts["Source"] == 13 and counts["Claim"] == 2 and counts["Section"] == 3
    p = ws.get_project("legacy-proj")
    assert p.stages["writing"]["status"] == "in_progress"
    g = ws.graph("legacy-proj")
    # last line wins: CLM-002 is supported by SRC-003
    clm2 = g.get("CLM-002")
    assert clm2.data["status"] == "supported"
    assert [n.id for n in g.out("CLM-002", EdgeType.SUPPORTED_BY)] == ["SRC-003"]
    # counters continue after imported ids
    assert g.allocate("SRC")[0] == "SRC-014"
    assert g.document("context").data["hypothesis"].startswith("LFP CAM")
    spec = g.callspec_node()
    assert spec.data["abstract_word_limit"] == 300 and len(spec.data["criteria"]) == 2
    assert [s["id"] for s in spec.data["sections"]] == ["1", "2", "3"]
    # gates evaluate on the imported graph
    r = evaluate_gate("scope", g)
    assert not r.passed and any("scope not configured" in b for b in r.blockers)
    assert any("not aligned" in b for b in r.blockers)
    ws.set_scope("legacy-proj", {})
    ws.set_concept_status("legacy-proj", "aligned")
    assert evaluate_gate("scope", g).passed
    assert evaluate_gate("evidence", g).passed, evaluate_gate("evidence", g).blockers
    assert evaluate_gate("draft", g).passed, evaluate_gate("draft", g).blockers
    assert len(g.findings("scientific")) == 1
    assert ws.blobs.exists(next(n for n in g.nodes(NodeType.DOCUMENT) if n.data["kind"] == "input").data["path"])
