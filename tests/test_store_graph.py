from agency.domain.graph import EdgeType, NodeType
from agency.domain.models import Claim, Source
from agency.domain.runs import CostEntry, Event, InboxItem, InboxKind, Job, JobKind, Run


def test_project_lifecycle(ws, project):
    assert ws.get_project("demo").name == "Demo Project"
    assert ws.current_stage(project) == "ideation"
    ws.set_stage("demo", "ideation", "skipped")
    ws.set_stage("demo", "call_parsing", "complete")
    assert ws.current_stage(ws.get_project("demo")) == "research"
    assert ws.graph("demo").document("context").data["hypothesis"].startswith("A digital twin")


def test_ids_are_allocated_by_store(ws, project):
    g = ws.graph("demo")
    a = g.add(NodeType.SOURCE, Source(title="A", extract=""))
    b = g.add(NodeType.SOURCE, Source(title="B", extract=""))
    assert (a.id, b.id) == ("SRC-001", "SRC-002")
    # explicit ids bump the counter so later allocations never collide
    g.add(NodeType.SOURCE, Source(title="C", extract=""), id="SRC-010")
    assert g.add(NodeType.SOURCE, Source(title="D", extract="")).id == "SRC-011"
    assert g.allocate("SRC", 2) == ["SRC-012", "SRC-013"]


def test_node_versions_and_edges(ws, project):
    g = ws.graph("demo")
    s = g.add(NodeType.SOURCE, Source(title="A", extract=""))
    c = g.add(NodeType.CLAIM, Claim(text="x", type="scientific_finding", status="supported",
                                    supported_by=[s.id]))
    g.link(c, s, EdgeType.SUPPORTED_BY)
    g.update(c, status="disputed")
    assert g.get(c.id).version == 2
    assert len(ws.store.node_versions(c.id)) == 2
    assert [n.id for n in g.out(c.id, EdgeType.SUPPORTED_BY)] == [s.id]
    assert [n.id for n in g.inn(s.id)] == [c.id]
    assert g.unregistered_refs("see CLM-001 and CLM-099 and SRC-001") == {"CLM-099"}
    assert g.summary() == {"Source": 1, "Claim": 1, "Document": 1}


def test_search_and_provenance(ws, project):
    g = ws.graph("demo")
    s = g.add(NodeType.SOURCE, Source(title="Lithium iron phosphate cathodes", extract=""))
    c = g.add(NodeType.CLAIM, Claim(text="LFP is safe", type="scientific_finding", status="supported"))
    g.link(c, s, EdgeType.SUPPORTED_BY)
    assert [n.id for n in ws.store.search_nodes("phosphate", "demo")] == [s.id]
    prov = g.provenance(c.id)
    assert {n.id for n in prov["nodes"]} == {c.id, s.id}


def test_runs_jobs_inbox_events_costs(ws, project):
    st = ws.store
    st.put_run(Run(id="r1", project_id="demo", stage="research"))
    st.put_job(Job(id="j1", run_id="r1", name="retrieve", kind=JobKind.AGENT))
    assert st.list_jobs("r1")[0].name == "retrieve"
    st.put_inbox(InboxItem(id="q1", project_id="demo", run_id="r1", kind=InboxKind.QUESTION, question="?"))
    assert len(st.list_inbox(project_id="demo", status="pending")) == 1
    e = ws.events.emit("test", project_id="demo", detail="x" * 1000)
    assert e.seq >= 1 and len(e.data["detail"]) < 1000
    ws.events.record_cost(CostEntry(project_id="demo", run_id="r1", cost_usd=0.25))
    assert st.sum_cost("demo") == 0.25
    assert [ev.kind for ev in ws.events.replay(project_id="demo")][-2:] == ["test", "cost"]
