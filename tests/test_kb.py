import json

from agency.domain.graph import EdgeType, NodeType
from agency.domain.models import Claim, Gap, Source
from agency.kb import service as kb


def _seed(ws, pid: str):
    ws.create_project(pid, project_id=pid, hypothesis="LFP cathode digital twin")
    g = ws.graph(pid)
    s1 = g.add(NodeType.SOURCE, Source(title="Digital twins for LFP cathode plants", doi="10.1/lfp", year=2024, extract="scrap"))
    s2 = g.add(NodeType.SOURCE, Source(title="Unrelated fish study", year=2020, extract="fish"))
    c = g.add(NodeType.CLAIM, Claim(text="Digital twins reduce cathode scrap", type="technical_benefit", status="supported", supported_by=[s1.id]))
    g.link(c, s1, EdgeType.SUPPORTED_BY)
    g.add(NodeType.CLAIM, Claim(text="Unsupported guess", type="assumption", status="unsupported"))
    g.add(NodeType.GAP, Gap(type="technology", sub_type="not-studied", description="No plant-scale LFP digital twin exists",
                            evidence_of_gap=[s1.id], severity="major", strategic_importance=8))
    return g


def test_promote_is_idempotent_and_deduplicates(ws):
    _seed(ws, "p1")
    c1 = kb.promote_project(ws, "p1")
    assert c1["promoted"] == 4                       # 2 sources, 1 supported claim, 1 gap
    st = kb.status(ws)
    assert st["counts"]["Source"] == 2 and st["counts"]["Claim"] == 1 and st["promoted_projects"] == ["p1"]
    c2 = kb.promote_project(ws, "p1")
    assert c2["promoted"] == 0
    # second project with the same DOI and claim text: nothing new is created, links are added
    _seed(ws, "p2")
    c3 = kb.promote_project(ws, "p2")
    assert c3["promoted"] == 0 and c3["linked"] >= 3
    src = ws.graph("p2").sources()[0]
    assert ws.store.edges_from(src.id, EdgeType.PROMOTED_TO.value, "p2")[0].dst.startswith("WIKI-SRC")
    ws_claim = kb.kb_graph(ws).nodes(NodeType.CLAIM)[0]
    assert ws_claim.data["supported_by"][0].startswith("WIKI-SRC") and ws_claim.scope.value == "workspace"


def test_import_query_lint_export(ws, tmp_path):
    _seed(ws, "p1")
    kb.promote_project(ws, "p1")
    ws.create_project("New", project_id="new", hypothesis="a digital twin for cathode plants")
    counts = kb.import_relevant(ws, "new", "digital twin cathode plant scrap", job_id="t")
    assert counts["sources"] == 1 and counts["claims"] == 1 and counts["gaps"] == 1
    g = ws.graph("new")
    local_src = g.sources()[0]
    assert local_src.data["imported_from"].startswith("WIKI-SRC")
    assert g.out(local_src.id, EdgeType.DERIVED_FROM)[0].id.startswith("WIKI-SRC")
    assert g.claims()[0].data["supported_by"] == [local_src.id]
    # importing again does not duplicate
    assert kb.import_relevant(ws, "new", "digital twin cathode plant scrap", job_id="t")["sources"] == 0
    hits = kb.query(ws, "cathode digital twin")["hits"]
    assert hits and hits[0]["id"].startswith("WIKI-")
    assert kb.lint(ws)["ok"]
    res = kb.export_vault(ws, tmp_path / "vault")
    assert res["pages"] == 4
    page = (tmp_path / "vault" / "pages" / "claims" / "wiki-clm-001.md").read_text()
    assert page.startswith("---") and "[[wiki-src-001]]" in page
    assert "## sources (2)" in (tmp_path / "vault" / "index.md").read_text()


async def test_research_stage_imports_from_kb(ws):
    """The research stage's kb_import job pulls workspace knowledge into a new project."""
    from agency.engine.runner import Engine
    from tests.fake_sdk import FakeQuery
    from tests.test_engine import AutoApprove, responder
    _seed(ws, "p1")
    kb.promote_project(ws, "p1")
    ws.create_project("Demo", project_id="demo", hypothesis="digital twin for LFP cathode plants")
    from agency.domain.callspec import CallSpec
    from agency.engine.materialize import ingest_callspec
    from tests.test_engine import CALLSPEC
    ingest_callspec(ws.graph("demo"), CallSpec.model_validate(CALLSPEC), job_id="t")
    ws.graph("demo").put_document("outline", "o", "## 1. x")
    eng = Engine(ws, query_fn=FakeQuery(responder))
    eng.inbox.responder = AutoApprove()
    run = await eng.run_stage("demo", "research", force=True)
    assert run.status.value == "completed", run.error
    job = next(j for j in ws.store.list_jobs(run.id) if j.name == "kb_import")
    assert job.result["sources"] == 1 and "knowledge base" in job.result["summary"]
