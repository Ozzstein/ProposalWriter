"""FastAPI application: projects, graph, runs, inbox, events (SSE), gates, agents."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agency import __version__
from agency.config import REPO_ROOT
from agency.domain.graph import NodeType
from agency.domain.runs import InboxStatus, RunStatus
from agency.engine.plan import StageBlocked
from agency.engine.runner import Engine
from agency.workspace import GATES, STAGES as STAGE_KEYS, Workspace

UI_DIST = REPO_ROOT / "ui" / "web" / "dist"


class CreateProject(BaseModel):
    name: str
    funder: str | None = None
    mechanism: str | None = None
    topic: str | None = None
    deadline: str | None = None
    hypothesis: str | None = None
    context_md: str | None = None
    project_id: str | None = None
    skip_ideation: bool = False
    pack: str | None = None


class StartRun(BaseModel):
    flags: dict[str, Any] = Field(default_factory=dict)
    resume: str | None = None
    force: bool = False


class Answer(BaseModel):
    answer: dict[str, Any]


class RequirementStatus(BaseModel):
    status: str
    note: str = ""


class StartPlan(BaseModel):
    goal: str
    budget_usd: float | None = None
    max_replans: int = 1
    execute: bool = True


class Override(BaseModel):
    target_id: str
    status: str | None = None
    note: str | None = None
    type: str = "override"


def _project_summary(ws: Workspace, project) -> dict[str, Any]:
    g = ws.graph(project.id)
    counts = g.summary()
    return {
        "id": project.id, "name": project.name,
        "state": {"project_name": project.id, "project_title": project.name, "funding_agency": project.funder,
                  "mechanism": project.mechanism, "topic": project.topic, "deadline": project.deadline,
                  "created_at": project.created_at.isoformat(), "stages": project.stages, "gates": project.gates,
                  "settings": project.settings},
        "current_stage": ws.current_stage(project),
        "memory": {"evidence": counts.get("Source", 0), "claims": counts.get("Claim", 0),
                   "decisions": counts.get("Decision", 0), "tasks": len(ws.store.list_runs(project.id)),
                   "feedback": counts.get("Feedback", 0), "sections": counts.get("Section", 0),
                   "gaps": counts.get("Gap", 0), "anchors": counts.get("NoveltyAnchor", 0)},
        "cost_usd": round(ws.store.sum_cost(project.id), 4),
        "pending_inbox": len(ws.store.list_inbox(project_id=project.id, status="pending")),
        "next_step": ws.next_step(project.id),
    }


MEMORY_STORES = {"evidence": NodeType.SOURCE, "claims": NodeType.CLAIM, "decisions": NodeType.DECISION,
                 "feedback": NodeType.FEEDBACK, "sections": NodeType.SECTION, "gaps": NodeType.GAP,
                 "anchors": NodeType.NOVELTY_ANCHOR, "findings": NodeType.REVIEW_FINDING,
                 "figures": NodeType.FIGURE}


def create_app(ws: Workspace, engine: Engine | None = None) -> FastAPI:
    app = FastAPI(title="Proposal Agency", version=__version__)
    app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
                       allow_methods=["*"], allow_headers=["*"])
    engine = engine or Engine(ws)
    app.state.ws = ws
    app.state.engine = engine
    api = "/api"

    @app.on_event("startup")
    async def _startup() -> None:
        for run in ws.store.list_runs(status=RunStatus.RUNNING.value) + ws.store.list_runs(status=RunStatus.WAITING_FOR_USER.value):
            run.status = RunStatus.INTERRUPTED
            run.error = "server restarted while the run was active"
            ws.store.put_run(run)

    # ------------------------------------------------------------ health / meta
    @app.get(f"{api}/health")
    def health() -> dict[str, Any]:
        return {"ok": True, "version": __version__, "workspace": str(ws.config.root),
                "api_key_present": bool(ws.config.secrets.get("ANTHROPIC_API_KEY")),
                "models": ws.config.models}

    @app.get(f"{api}/stages")
    def stages() -> dict[str, Any]:
        from agency.policy.guide import OPTIONAL_STAGE_NAMES, STAGE_ORDER
        order = {n: i for i, n in enumerate(STAGE_ORDER)}
        items = sorted(engine.stages.values(), key=lambda s: order.get(s.name, 99))
        return {"items": [{"name": s.name, "state_key": s.state_key, "description": s.description,
                           "requires_gate": s.requires_gate, "requires_stages": list(s.requires_stages),
                           "interactive": s.interactive, "flags": s.flags,
                           "order": order.get(s.name, 99), "optional": s.name in OPTIONAL_STAGE_NAMES}
                          for s in items],
                "stage_keys": STAGE_KEYS, "gates": GATES}

    # ------------------------------------------------------------ projects
    @app.get(f"{api}/projects")
    def list_projects() -> dict[str, Any]:
        return {"items": [_project_summary(ws, p) for p in ws.list_projects()]}

    @app.post(f"{api}/projects", status_code=201)
    def create_project(body: CreateProject) -> dict[str, Any]:
        try:
            p = ws.create_project(body.name, funder=body.funder, mechanism=body.mechanism, topic=body.topic,
                                 deadline=body.deadline, hypothesis=body.hypothesis, context_md=body.context_md,
                                 project_id=body.project_id, settings={"pack": body.pack} if body.pack else None)
        except ValueError as e:
            raise HTTPException(409, str(e))
        if body.skip_ideation or body.hypothesis:
            ws.set_stage(p.id, "ideation", "skipped", note="hypothesis supplied at intake")
        return _project_summary(ws, ws.get_project(p.id))

    @app.get(f"{api}/projects/{{pid}}")
    def get_project(pid: str) -> dict[str, Any]:
        p = ws.get_project(pid)
        if p is None:
            raise HTTPException(404, "project not found")
        return _project_summary(ws, p)

    @app.get(f"{api}/projects/{{pid}}/status")
    def project_status(pid: str) -> dict[str, Any]:
        try:
            return ws.status(pid)
        except KeyError:
            raise HTTPException(404, "project not found")

    @app.post(f"{api}/projects/{{pid}}/inputs")
    async def upload_inputs(pid: str, files: list[UploadFile] = File(...), subdir: str = Form("")) -> dict[str, Any]:
        ws.require_project(pid)
        pdir = ws.config.project_dir(pid) / "inputs" / subdir.strip("/") if subdir else ws.config.project_dir(pid) / "inputs"
        pdir.mkdir(parents=True, exist_ok=True)
        g = ws.graph(pid)
        saved = []
        for f in files:
            name = Path(f.filename or "upload").name
            data = await f.read()
            target = pdir / name
            target.write_bytes(data)
            key = ws.blobs.put(data, suffix=Path(name).suffix)
            rel = f"{subdir.strip('/')}/{name}" if subdir else name
            g.add(NodeType.DOCUMENT, {"kind": "input", "title": name, "path": key, "relative": rel}, created_by="upload")
            saved.append(rel)
        ws.events.emit("inputs:uploaded", project_id=pid, files=saved)
        return {"saved": saved}

    @app.get(f"{api}/projects/{{pid}}/files")
    def project_file(pid: str, path: str) -> dict[str, Any]:
        root = ws.config.project_dir(pid).resolve()
        target = (root / path).resolve()
        if root not in target.parents or not target.is_file():
            raise HTTPException(404, "file not found")
        if target.stat().st_size > 2_000_000:
            raise HTTPException(413, "file too large")
        return {"path": path, "body": target.read_text(errors="replace")}

    # ------------------------------------------------------------ graph
    @app.get(f"{api}/projects/{{pid}}/graph")
    def graph_nodes(pid: str, type: str | None = None, status: str | None = None, q: str | None = None,
                    limit: int = 200) -> dict[str, Any]:
        ws.require_project(pid)
        if q:
            nodes = ws.store.search_nodes(q, project_id=pid, type=type, limit=limit)
        else:
            nodes = ws.store.list_nodes(project_id=pid, type=type, status=status, limit=limit)
        return {"items": [n.model_dump(mode="json") for n in nodes], "summary": ws.graph(pid).summary()}

    @app.get(f"{api}/projects/{{pid}}/graph/edges")
    def graph_edges(pid: str, type: str | None = None) -> dict[str, Any]:
        return {"items": [e.model_dump(mode="json") for e in ws.store.list_edges(pid, type)]}

    @app.get(f"{api}/projects/{{pid}}/graph/{{node_id}}")
    def graph_node(pid: str, node_id: str, depth: int = 2) -> dict[str, Any]:
        g = ws.graph(pid)
        node = g.get(node_id)
        if node is None:
            raise HTTPException(404, "node not found")
        prov = g.provenance(node_id, depth=depth)
        return {"node": node.model_dump(mode="json"),
                "out": [e.model_dump(mode="json") for e in g.out_edges(node_id)],
                "in": [e.model_dump(mode="json") for e in g.in_edges(node_id)],
                "provenance": {"nodes": [n.model_dump(mode="json") for n in prov["nodes"]],
                               "edges": [e.model_dump(mode="json") for e in prov["edges"]]},
                "versions": [{"version": v.version, "updated_at": v.updated_at.isoformat()} for v in g.versions(node_id)]}

    @app.get(f"{api}/projects/{{pid}}/memory/{{store}}")
    def memory(pid: str, store: str, offset: int = 0, limit: int = 100) -> dict[str, Any]:
        ws.require_project(pid)
        if store == "overrides":
            items = [d.data | {"id": d.id} for d in ws.graph(pid).decisions("ui_override")]
        elif store == "tasks":
            items = [r.model_dump(mode="json") for r in ws.store.list_runs(project_id=pid)]
        elif store in MEMORY_STORES:
            items = [{"id": n.id, "status": n.status, "version": n.version, **n.data}
                     for n in ws.graph(pid).nodes(MEMORY_STORES[store])]
        else:
            raise HTTPException(404, f"unknown store {store}")
        return {"store": store, "total": len(items), "offset": offset, "limit": limit,
                "items": items[offset:offset + limit], "overrides": None}

    @app.post(f"{api}/projects/{{pid}}/memory/{{store}}/override")
    def override(pid: str, store: str, body: Override) -> dict[str, Any]:
        g = ws.graph(pid)
        node = g.add(NodeType.DECISION, {"question": f"UI {body.type} on {body.target_id}",
                                         "decision": body.status or body.note or "", "rationale": [body.note or ""],
                                         "evidence_refs": [body.target_id], "type": "ui_override",
                                         "target_store": store, "status": body.status, "note": body.note},
                     created_by="ui")
        if body.status and g.get(body.target_id):
            g.set_status(body.target_id, body.status)
        return {"ok": True, "id": node.id}

    @app.get(f"{api}/projects/{{pid}}/documents/{{kind}}")
    def document(pid: str, kind: str) -> dict[str, Any]:
        doc = ws.graph(pid).document(kind)
        if doc is None:
            raise HTTPException(404, "document not found")
        return doc.model_dump(mode="json")

    @app.get(f"{api}/projects/{{pid}}/sections")
    def sections(pid: str) -> dict[str, Any]:
        return {"items": [s.model_dump(mode="json") for s in ws.graph(pid).sections()]}

    # ------------------------------------------------------------ gates
    @app.get(f"{api}/projects/{{pid}}/gates")
    def gates(pid: str) -> dict[str, Any]:
        return {"gates": ws.require_project(pid).gates}

    @app.get(f"{api}/projects/{{pid}}/next")
    def next_step(pid: str) -> dict[str, Any]:
        ws.require_project(pid)
        return ws.next_step(pid)

    @app.get(f"{api}/projects/{{pid}}/requirements")
    def requirements(pid: str) -> dict[str, Any]:
        node = ws.graph(pid).callspec_node()
        return {"items": (node.data.get("requirements", []) if node else [])}

    @app.post(f"{api}/projects/{{pid}}/requirements/{{rid}}")
    def set_requirement(pid: str, rid: str, body: RequirementStatus) -> dict[str, Any]:
        ws.require_project(pid)
        try:
            return ws.set_requirement_status(pid, rid, body.status, body.note)
        except KeyError as e:
            raise HTTPException(404, str(e))
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.post(f"{api}/projects/{{pid}}/gates/{{gate}}")
    def run_gate(pid: str, gate: str, write: bool = True) -> dict[str, Any]:
        try:
            return ws.check_gate(pid, gate, write=write).model_dump(mode="json")
        except KeyError:
            raise HTTPException(404, "project not found")
        except ValueError as e:
            raise HTTPException(400, str(e))

    # ------------------------------------------------------------ runs
    @app.post(f"{api}/projects/{{pid}}/stages/{{stage}}", status_code=202)
    async def start_stage(pid: str, stage: str, body: StartRun | None = None) -> dict[str, Any]:
        body = body or StartRun()
        ws.require_project(pid)
        try:
            sd = engine.stage(stage)
        except KeyError as e:
            raise HTTPException(404, str(e))
        active = [r for r in ws.store.list_runs(project_id=pid)
                  if r.status in (RunStatus.RUNNING, RunStatus.WAITING_FOR_USER, RunStatus.QUEUED)]
        if active:
            raise HTTPException(409, f"run {active[0].id} ({active[0].stage}) is still active")
        try:
            engine.check_prerequisites(pid, sd, body.force)
        except StageBlocked as e:
            raise HTTPException(412, str(e))
        started: asyncio.Future = asyncio.get_running_loop().create_future()

        async def _go() -> None:
            try:
                await engine.run_stage(pid, stage, flags=body.flags, resume=body.resume, force=body.force)
            except Exception:  # surfaced through run status/events
                pass

        task = asyncio.create_task(_go())
        engine.active[id(task)] = task  # type: ignore[index]
        for _ in range(100):
            await asyncio.sleep(0.01)
            runs = [r for r in ws.store.list_runs(project_id=pid) if r.stage == stage]
            if runs and runs[0].status != RunStatus.QUEUED:
                run = runs[0]
                app.state.tasks = getattr(app.state, "tasks", {})
                app.state.tasks[run.id] = task
                return run.model_dump(mode="json")
        return {"status": "starting", "project_id": pid, "stage": stage}

    @app.post(f"{api}/projects/{{pid}}/plan", status_code=202)
    async def start_plan(pid: str, body: StartPlan) -> dict[str, Any]:
        """Start a campaign: planning agent → inbox approval → stage runs, in the background."""
        ws.require_project(pid)
        active = [r for r in ws.store.list_runs(project_id=pid)
                  if r.status in (RunStatus.RUNNING, RunStatus.WAITING_FOR_USER, RunStatus.QUEUED)]
        if active:
            raise HTTPException(409, f"run {active[0].id} ({active[0].stage}) is still active")
        before = {r.id for r in ws.store.list_runs(project_id=pid)}

        async def _go() -> None:
            try:
                await engine.run_campaign(pid, body.goal, budget_usd=body.budget_usd, max_replans=body.max_replans,
                                          execute=body.execute)
            except Exception:  # surfaced through run status/events
                pass

        task = asyncio.create_task(_go())
        engine.active[id(task)] = task  # type: ignore[index]
        app.state.campaigns = getattr(app.state, "campaigns", {})
        app.state.campaigns[pid] = task
        for _ in range(100):
            await asyncio.sleep(0.01)
            new = [r for r in ws.store.list_runs(project_id=pid) if r.id not in before]
            if new:
                app.state.tasks = getattr(app.state, "tasks", {})
                app.state.tasks[new[0].id] = task
                return new[0].model_dump(mode="json")
        return {"status": "starting", "project_id": pid, "stage": "plan"}

    @app.get(f"{api}/projects/{{pid}}/plan")
    def get_plan(pid: str) -> dict[str, Any]:
        from agency.jobs.plan import load_plan
        ws.require_project(pid)
        body = load_plan(ws.graph(pid))
        if body is None:
            raise HTTPException(404, "no plan yet")
        task = getattr(app.state, "campaigns", {}).get(pid)
        body["campaign_active"] = bool(task is not None and not task.done())
        return body

    @app.get(f"{api}/runs")
    def list_runs(project: str | None = None, status: str | None = None) -> dict[str, Any]:
        return {"items": [r.model_dump(mode="json") for r in ws.store.list_runs(project_id=project, status=status)]}

    @app.get(f"{api}/runs/{{run_id}}")
    def get_run(run_id: str) -> dict[str, Any]:
        run = ws.store.get_run(run_id)
        if run is None:
            raise HTTPException(404, "run not found")
        return {"run": run.model_dump(mode="json"),
                "jobs": [j.model_dump(mode="json") for j in ws.store.list_jobs(run_id)],
                "costs": [c.model_dump(mode="json") for c in ws.store.list_costs(run_id=run_id)]}

    @app.post(f"{api}/runs/{{run_id}}/stop")
    def stop_run(run_id: str) -> dict[str, Any]:
        run = ws.store.get_run(run_id)
        if run is None:
            raise HTTPException(404, "run not found")
        task = getattr(app.state, "tasks", {}).get(run_id)
        if task is not None and not task.done():
            task.cancel()
        engine.inbox.cancel_run(run_id)
        if run.status in (RunStatus.RUNNING, RunStatus.WAITING_FOR_USER, RunStatus.QUEUED):
            run.status = RunStatus.STOPPED
            ws.store.put_run(run)
        return {"stopped": run_id}

    # ------------------------------------------------------------ inbox
    @app.get(f"{api}/inbox")
    def inbox(project: str | None = None, status: str | None = "pending") -> dict[str, Any]:
        items = ws.store.list_inbox(project_id=project, status=None if status == "all" else status)
        return {"items": [i.model_dump(mode="json") for i in items]}

    @app.post(f"{api}/inbox/{{item_id}}/answer")
    def answer(item_id: str, body: Answer) -> dict[str, Any]:
        try:
            item = engine.inbox.answer(item_id, body.answer)
        except KeyError:
            raise HTTPException(404, "inbox item not found")
        except ValueError as e:
            raise HTTPException(409, str(e))
        return item.model_dump(mode="json")

    # ------------------------------------------------------------ events / costs
    @app.get(f"{api}/events")
    def events(project: str | None = None, run: str | None = None, since: int = 0, limit: int = 500) -> dict[str, Any]:
        return {"items": [e.model_dump(mode="json") for e in ws.events.replay(since, project, run, limit)]}

    @app.get(f"{api}/events/stream")
    async def event_stream(request: Request, project: str | None = None, since: int = Query(0),
                           replay: int = Query(200)) -> StreamingResponse:
        from agency.server.sse import sse_stream
        return StreamingResponse(sse_stream(ws, project=project, since=since, replay=replay,
                                            is_disconnected=request.is_disconnected),
                                 media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.get(f"{api}/costs")
    def costs(project: str | None = None, run: str | None = None) -> dict[str, Any]:
        rows = ws.store.list_costs(project_id=project, run_id=run)
        by_agent: dict[str, float] = {}
        for c in rows:
            by_agent[c.agent or "?"] = round(by_agent.get(c.agent or "?", 0.0) + c.cost_usd, 4)
        return {"total_usd": round(sum(c.cost_usd for c in rows), 4), "by_agent": by_agent,
                "items": [c.model_dump(mode="json") for c in rows[-500:]]}

    # ------------------------------------------------------------ agents
    @app.get(f"{api}/agents/graph")
    def agents_graph() -> dict[str, Any]:
        nodes, edges = [], []
        for c in engine.catalogue.contracts.values():
            nodes.append({"id": f"agents/{c.name}", "kind": c.role, "title": c.name, "description": c.description,
                          "model": c.model_tier, "file": f"agents/{c.name}/prompt.md"})
        for s in engine.stages.values():
            nodes.append({"id": f"stages/{s.name}", "kind": "stage", "title": s.name, "description": s.description,
                          "file": ""})
            for c in getattr(s, "agents", ()) or _stage_agents(s):
                edges.append({"from": f"stages/{s.name}", "to": f"agents/{c}"})
        return {"nodes": nodes, "edges": edges}

    @app.get(f"{api}/agents/file")
    def agent_file(path: str) -> dict[str, Any]:
        target = (REPO_ROOT / path).resolve()
        if REPO_ROOT.resolve() not in target.parents or not target.is_file() or target.suffix not in (".md", ".yaml"):
            raise HTTPException(404, "not found")
        return {"path": path, "body": target.read_text()}

    # ------------------------------------------------------------ knowledge base
    from agency.kb import service as kb

    @app.get(f"{api}/kb/status")
    def kb_status() -> dict[str, Any]:
        return kb.status(ws)

    @app.post(f"{api}/kb/promote/{{pid}}")
    def kb_promote(pid: str) -> dict[str, Any]:
        try:
            return kb.promote_project(ws, pid)
        except KeyError:
            raise HTTPException(404, "project not found")

    @app.get(f"{api}/kb/query")
    def kb_query(q: str, limit: int = 20) -> dict[str, Any]:
        return kb.query(ws, q, limit)

    @app.post(f"{api}/kb/lint")
    def kb_lint(fix: bool = False) -> dict[str, Any]:
        return kb.lint(ws, fix=fix)

    @app.post(f"{api}/kb/export")
    def kb_export() -> dict[str, Any]:
        return kb.export_vault(ws)

    @app.get(f"{api}/kb/nodes")
    def kb_nodes(type: str | None = None, limit: int = 200) -> dict[str, Any]:
        nodes = ws.store.list_nodes(project_id=None, type=type, scope="workspace", limit=limit)
        return {"items": [n.model_dump(mode="json") for n in nodes]}

    # ------------------------------------------------------------ static UI
    if UI_DIST.exists():
        app.mount("/assets", StaticFiles(directory=UI_DIST / "assets"), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa(full_path: str):
            candidate = UI_DIST / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(UI_DIST / "index.html")

    return app


def _stage_agents(sd) -> list[str]:
    """Best-effort: the contracts a stage's planner references (read from its module source)."""
    import inspect
    try:
        src = inspect.getsource(inspect.getmodule(sd.planner))
    except (OSError, TypeError):
        return []
    import re
    return sorted(set(re.findall(r'contract="([a-z_]+)"', src)) | set(re.findall(r'"([a-z_]+)"\)\s*,?\s*$', "")))
