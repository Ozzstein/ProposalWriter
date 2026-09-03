import asyncio
import json

import httpx
import pytest

from agency.engine.runner import Engine
from agency.server.app import create_app
from tests.fake_sdk import FakeQuery
from tests.test_engine import responder


@pytest.fixture
async def client(ws):
    engine = Engine(ws, query_fn=FakeQuery(responder))
    app = create_app(ws, engine)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        c.engine = engine
        yield c


async def test_projects_and_status(client):
    r = await client.get("/api/health")
    assert r.status_code == 200 and r.json()["ok"]
    r = await client.post("/api/projects", json={"name": "Green Steel", "funder": "Horizon Europe",
                                                  "hypothesis": "H2 DRI cuts emissions"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == "green-steel" and body["state"]["stages"]["ideation"]["status"] == "skipped"
    assert (await client.post("/api/projects", json={"name": "Green Steel"})).status_code == 409
    r = await client.get("/api/projects")
    assert [p["id"] for p in r.json()["items"]] == ["green-steel"]
    r = await client.get("/api/projects/green-steel/status")
    assert r.json()["current_stage"] == "call_parsing"
    r = await client.get("/api/stages")
    assert {s["name"] for s in r.json()["items"]} >= {"parse-call", "research"}
    r = await client.post("/api/projects/green-steel/gates/scope")
    assert r.status_code == 200 and r.json()["passed"] is False
    assert (await client.get("/api/projects/nope")).status_code == 404


async def test_upload_graph_and_memory(client):
    await client.post("/api/projects", json={"name": "P1", "hypothesis": "h"})
    files = [("files", ("call.txt", b"Call text: three partners", "text/plain"))]
    r = await client.post("/api/projects/p1/inputs", files=files, data={"subdir": ""})
    assert r.json()["saved"] == ["call.txt"]
    r = await client.get("/api/projects/p1/graph", params={"type": "Document"})
    docs = r.json()["items"]
    assert {d["data"]["kind"] for d in docs} == {"context", "input"}
    r = await client.get("/api/projects/p1/files", params={"path": "inputs/call.txt"})
    assert r.json()["body"].startswith("Call text")
    assert (await client.get("/api/projects/p1/files", params={"path": "../../etc/passwd"})).status_code == 404
    r = await client.get("/api/projects/p1/memory/evidence")
    assert r.json()["total"] == 0
    r = await client.post("/api/projects/p1/memory/evidence/override", json={"target_id": "SRC-001", "note": "check"})
    assert r.json()["ok"]
    assert (await client.get("/api/projects/p1/memory/overrides")).json()["total"] == 1


async def test_run_stage_inbox_and_events(client):
    await client.post("/api/projects", json={"name": "P2", "hypothesis": "h"})
    r = await client.post("/api/projects/p2/stages/parse-call", json={})
    assert r.status_code == 202, r.text
    run_id = r.json()["id"]
    # the stage asks for the call text via the inbox
    for _ in range(100):
        await asyncio.sleep(0.02)
        pending = (await client.get("/api/inbox", params={"project": "p2"})).json()["items"]
        if pending:
            break
    assert pending and pending[0]["kind"] == "form"
    assert (await client.post("/api/projects/p2/stages/research", json={})).status_code == 409  # run active
    r = await client.post(f"/api/inbox/{pending[0]['id']}/answer", json={"answer": {"data": {"text": "Call: three partners."}}})
    assert r.status_code == 200
    assert (await client.post(f"/api/inbox/{pending[0]['id']}/answer", json={"answer": {}})).status_code == 409
    # then the outline approval
    for _ in range(200):
        await asyncio.sleep(0.02)
        pending = (await client.get("/api/inbox", params={"project": "p2"})).json()["items"]
        if pending and pending[0]["kind"] == "approval":
            break
    assert pending[0]["kind"] == "approval"
    rows = {row["id"]: "approve" for row in pending[0]["payload"]["rows"]}
    await client.post(f"/api/inbox/{pending[0]['id']}/answer", json={"answer": {"decision": "approve", "rows": rows}})
    # then the scope configuration form
    for _ in range(200):
        await asyncio.sleep(0.02)
        pending = (await client.get("/api/inbox", params={"project": "p2"})).json()["items"]
        if pending and pending[0]["kind"] == "form":
            break
    assert pending[0]["kind"] == "form" and pending[0]["header"] == "Configure proposal scope"
    await client.post(f"/api/inbox/{pending[0]['id']}/answer", json={"answer": {"data": {
        "finance": "excluded", "business_plan": "excluded", "figures": "excluded", "external_review": "excluded"}}})
    # then the preliminary concept's alignment with the parsed call
    for _ in range(200):
        await asyncio.sleep(0.02)
        pending = (await client.get("/api/inbox", params={"project": "p2"})).json()["items"]
        if pending and pending[0]["kind"] == "question":
            break
    assert pending[0]["kind"] == "question" and pending[0]["header"] == "Align the concept with the call"
    await client.post(f"/api/inbox/{pending[0]['id']}/answer", json={"answer": {"choice": "keep the hypothesis as is"}})
    for _ in range(200):
        await asyncio.sleep(0.02)
        run = (await client.get(f"/api/runs/{run_id}")).json()
        if run["run"]["status"] in ("completed", "failed"):
            break
    assert run["run"]["status"] == "completed", run["run"]["error"]
    assert {j["name"] for j in run["jobs"]} >= {"parse_call", "approve_outline", "configure_scope", "align_concept", "finalize"}
    assert run["costs"]
    # research is blocked by the scope gate (eligibility unknown) unless forced
    assert (await client.post("/api/projects/p2/stages/research", json={})).status_code == 412
    r = await client.get("/api/events", params={"project": "p2"})
    kinds = [e["kind"] for e in r.json()["items"]]
    assert "stage:start" in kinds and "inbox:answered" in kinds and "stage:end" in kinds
    r = await client.get("/api/costs", params={"project": "p2"})
    assert r.json()["total_usd"] > 0 and "call_parser" in r.json()["by_agent"]
    r = await client.get("/api/agents/graph")
    assert any(n["id"] == "agents/novelty_mapper" for n in r.json()["nodes"])
    assert any(e["from"] == "stages/research" and e["to"] == "agents/novelty_mapper" for e in r.json()["edges"])


async def test_sse_stream_replays_then_streams_live(ws):
    from agency.server.sse import sse_stream
    ws.create_project("P3", project_id="p3")
    calls = {"n": 0}

    async def disconnected():
        calls["n"] += 1
        return calls["n"] > 4

    chunks = []

    async def consume():
        async for chunk in sse_stream(ws, project="p3", is_disconnected=disconnected, ping_seconds=0.05):
            chunks.append(chunk)
            if len(chunks) == 2:
                ws.events.emit("live:test", project_id="p3")

    await asyncio.wait_for(consume(), timeout=5)
    assert chunks[0].startswith("event: ready")
    assert "project:created" in chunks[1] and any("live:test" in c for c in chunks[2:])


async def test_plan_endpoint_runs_a_campaign(ws):
    from tests.test_engine import AutoApprove
    from tests.test_planner import GOOD_PLAN, make_responder
    engine = Engine(ws, query_fn=FakeQuery(make_responder([GOOD_PLAN])))
    engine.inbox.responder = AutoApprove()
    app = create_app(ws, engine)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/projects", json={"name": "P3", "hypothesis": "h"})
        assert (await c.get("/api/projects/p3/plan")).status_code == 404
        r = await c.post("/api/projects/p3/plan", json={"goal": "reach the evidence gate"})
        assert r.status_code == 202 and r.json()["stage"] == "plan"
        for _ in range(300):
            await asyncio.sleep(0.02)
            runs = (await c.get("/api/runs?project=p3")).json()["items"]
            if len(runs) == 3 and all(x["status"] in ("completed", "failed") for x in runs):
                break
        plan = (await c.get("/api/projects/p3/plan")).json()
        assert plan["status"] == "completed" and [s["stage"] for s in plan["steps"]] == ["parse-call", "research"]
        assert all(s["status"] == "completed" for s in plan["steps"]) and plan["campaign_active"] is False


async def test_next_step_and_requirements_endpoints(client):
    await client.post("/api/projects", json={"name": "P4", "hypothesis": "h"})
    r = await client.get("/api/projects/p4/next")
    assert r.status_code == 200 and r.json()["key"] == "upload_call"
    assert (await client.get("/api/projects/p4")).json()["next_step"]["key"] == "upload_call"
    stages = (await client.get("/api/stages")).json()["items"]
    assert [s["name"] for s in stages][:3] == ["ideate", "parse-call", "research"] and stages[0]["optional"] is True
    assert (await client.post("/api/projects/p4/requirements/E1", json={"status": "met"})).status_code == 404
    from tests.test_engine import CALLSPEC
    from agency.domain.graph import NodeType
    client.engine.ws.graph("p4").add(NodeType.CALL_SPEC, dict(CALLSPEC))
    client.engine.ws.set_stage("p4", "call_parsing", "complete")
    assert (await client.get("/api/projects/p4/next")).json()["key"] == "confirm_eligibility"
    r = await client.post("/api/projects/p4/requirements/E1", json={"status": "met", "note": "ok"})
    assert r.status_code == 200 and r.json()["status"] == "met"
    assert (await client.post("/api/projects/p4/requirements/E1", json={"status": "bogus"})).status_code == 400
    assert (await client.get("/api/projects/p4/requirements")).json()["items"][0]["status"] == "met"
    assert (await client.get("/api/projects/p4/next")).json()["action"]["stage"] == "research"


async def test_agents_graph_covers_every_contract_and_role(client):
    """The Agents page groups by these kinds; a role the UI cannot render must not appear silently."""
    body = (await client.get("/api/agents/graph")).json()
    kinds = {n["kind"] for n in body["nodes"]}
    assert kinds <= {"stage", "planner", "interviewer", "retriever", "synthesizer", "writer", "modeler",
                     "renderer", "reviewer"}, kinds
    assert "planner" in kinds and "orchestrator" not in kinds
    agent_nodes = {n["id"] for n in body["nodes"] if n["id"].startswith("agents/")}
    assert len(agent_nodes) == len(client.engine.catalogue.contracts)
    assert all(n["file"] for n in body["nodes"] if n["id"].startswith("agents/"))
