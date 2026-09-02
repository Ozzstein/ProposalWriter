"""Stage runner: prerequisites, plan, schedule, stage/gate bookkeeping."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from agency.catalogue.loader import load_catalogue
from agency.domain.runs import JobStatus, Run, RunStatus
from agency.engine.plan import StageBlocked, StageDef
from agency.engine.runtime import RunContext
from agency.engine.scheduler import Scheduler
from agency.funders.packs import load_packs
from agency.inbox.service import InboxService
from agency.sdk.adapter import SDKAdapter
from agency.workspace import Workspace


class Engine:
    """Long-lived per workspace (the server holds one); builds RunContexts and runs stages."""

    def __init__(self, ws: Workspace, inbox: InboxService | None = None, query_fn=None, client_factory=None):
        from agency import jobs as job_registry
        self.ws = ws
        self.catalogue = load_catalogue(ws.config.agents_dir)
        self.packs = load_packs(ws.config.packs_dir)
        self.adapter = SDKAdapter(ws.config, self.catalogue, ws.events, query_fn=query_fn, client_factory=client_factory)
        self.inbox = inbox or InboxService(ws)
        self.stages: dict[str, StageDef] = job_registry.STAGES
        self.scheduler = Scheduler(job_registry.HANDLERS)
        self.active: dict[str, asyncio.Task] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def stage(self, name: str) -> StageDef:
        if name not in self.stages:
            raise KeyError(f"unknown stage {name!r}; known: {sorted(self.stages)}")
        return self.stages[name]

    def _lock(self, project_id: str) -> asyncio.Lock:
        return self._locks.setdefault(project_id, asyncio.Lock())

    # ------------------------------------------------------------ prerequisites
    def check_prerequisites(self, project_id: str, sd: StageDef, force: bool) -> list[str]:
        project = self.ws.require_project(project_id)
        warnings: list[str] = []
        for s in sd.requires_stages:
            st = project.stages.get(s, {}).get("status")
            if st not in ("complete", "skipped"):
                warnings.append(f"stage '{s}' is {st or 'pending'}")
        if sd.requires_gate:
            result = self.ws.check_gate(project_id, sd.requires_gate, write=True)
            if not result.passed and not result.not_applicable:
                if not force:
                    raise StageBlocked(f"gate '{sd.requires_gate}' not passed: " + "; ".join(result.blockers))
                warnings.append(f"gate '{sd.requires_gate}' overridden with --force")
                self.ws.graph(project_id).add(
                    __import__("agency.domain.graph", fromlist=["NodeType"]).NodeType.DECISION,
                    {"question": f"Run '{sd.name}' although gate '{sd.requires_gate}' failed?",
                     "decision": "override", "rationale": result.blockers, "type": "gate_override",
                     "date": datetime.now(timezone.utc).date().isoformat()})
        return warnings

    # ------------------------------------------------------------ run
    async def run_stage(self, project_id: str, stage: str, *, flags: dict[str, Any] | None = None,
                        resume: str | None = None, force: bool = False) -> Run:
        sd = self.stage(stage)
        flags = dict(flags or {})
        async with self._lock(project_id):
            warnings = self.check_prerequisites(project_id, sd, force)
            run = Run(id=f"run-{uuid.uuid4().hex[:10]}", project_id=project_id, stage=stage, flags=flags,
                      status=RunStatus.RUNNING, started_at=datetime.now(timezone.utc))
            self.ws.store.put_run(run)
            resume_jobs = {}
            if resume:
                prev = self.ws.store.get_run(resume)
                if prev and prev.project_id == project_id and prev.stage == stage:
                    resume_jobs = {j.name: j for j in self.ws.store.list_jobs(prev.id)}
            ctx = RunContext(ws=self.ws, project_id=project_id, run=run, catalogue=self.catalogue,
                             adapter=self.adapter, inbox=self.inbox, packs=self.packs,
                             project_dir=self.ws.config.project_dir(project_id),
                             kb_dir=self.ws.config.root / "kb", flags=flags, force=force)
            ctx.emit("stage:start", stage=stage, flags=flags, warnings=warnings, resume=resume)
            if sd.state_key:
                self.ws.set_stage(project_id, sd.state_key, "in_progress")
            ctx.materialize()
            ok = False
            try:
                plan = sd.planner(ctx)
                ctx.emit("stage:plan", stage=stage, jobs=[{"name": j.name, "deps": j.deps, "kind": j.kind.value,
                                                             "contract": j.contract} for j in plan.jobs],
                         notes=plan.notes)
                ok = await self.scheduler.run(ctx, plan, resume_jobs)
                run.status = RunStatus.COMPLETED if ok else RunStatus.FAILED
                if not ok:
                    failed = [j for j in self.ws.store.list_jobs(run.id) if j.status == JobStatus.FAILED]
                    run.error = "; ".join(f"{j.name}: {j.error.splitlines()[0] if j.error else ''}" for j in failed)[:1500]
            except asyncio.CancelledError:
                run.status = RunStatus.STOPPED
                self.inbox.cancel_run(run.id)
                raise
            except Exception as e:  # planner or bookkeeping failure
                run.status = RunStatus.FAILED
                run.error = f"{type(e).__name__}: {e}"
            finally:
                run.ended_at = datetime.now(timezone.utc)
                run.summary = (ctx.results.get("finalize", {}).get("summary")
                               or next((r.get("summary") for r in reversed(list(ctx.results.values()))
                                        if r.get("summary")), None) or run.summary)
                self.ws.store.put_run(run)
                if sd.state_key:
                    self.ws.set_stage(project_id, sd.state_key,
                                      "complete" if run.status == RunStatus.COMPLETED else
                                      ("in_progress" if run.status == RunStatus.STOPPED else "failed"))
                ctx.emit("stage:end", stage=stage, status=run.status.value, cost_usd=run.cost_usd,
                         error=run.error, summary=run.summary)
            return run

    def start(self, project_id: str, stage: str, **kw) -> asyncio.Task:
        task = asyncio.create_task(self.run_stage(project_id, stage, **kw))
        self.active[id(task)] = task  # type: ignore[index]
        task.add_done_callback(lambda t: self.active.pop(id(t), None))
        return task


def run_stage_cli(root: str | None, project_id: str, stage: str, *, flags: dict[str, Any], resume: bool,
                  force: bool) -> int:
    from agency.inbox.terminal import terminal_responder
    ws = Workspace.open(root)
    engine = Engine(ws)
    engine.inbox.responder = terminal_responder
    resume_id = None
    if resume:
        prev = [r for r in ws.store.list_runs(project_id=project_id) if r.stage == stage]
        resume_id = prev[0].id if prev else None
    try:
        run = asyncio.run(engine.run_stage(project_id, stage, flags=flags, resume=resume_id, force=force))
    except StageBlocked as e:
        print(f"blocked: {e}")
        return 2
    print(run.model_dump_json(indent=2))
    return 0 if run.status == RunStatus.COMPLETED else 1
