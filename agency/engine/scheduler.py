"""Executes a StagePlan as an asyncio DAG with persisted Job rows."""
from __future__ import annotations

import asyncio
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any

from agency.domain.runs import Job, JobStatus
from agency.engine.plan import JobFailed, StagePlan
from agency.engine.runtime import JobRuntime, RunContext


class Scheduler:
    def __init__(self, handlers: dict[str, Any]):
        self.handlers = handlers

    async def run(self, ctx: RunContext, plan: StagePlan, resume_jobs: dict[str, Job] | None = None) -> bool:
        plan.validate()
        store = ctx.ws.store
        jobs: dict[str, Job] = {}
        for spec in plan.jobs:
            prev = (resume_jobs or {}).get(spec.name)
            if prev and prev.status == JobStatus.COMPLETED:
                prev.run_id = ctx.run.id
                jobs[spec.name] = prev
                ctx.results[spec.name] = prev.result or {}
                store.put_job(prev)
                continue
            job = Job(id=f"job-{uuid.uuid4().hex[:10]}", run_id=ctx.run.id, name=spec.name, kind=spec.kind,
                      contract=spec.contract, deps=list(spec.deps), params=dict(spec.params))
            jobs[spec.name] = job
            store.put_job(job)
        specs = {s.name: s for s in plan.jobs}
        running: dict[str, asyncio.Task] = {}
        failed = False
        while True:
            for name, job in jobs.items():
                if job.status != JobStatus.PENDING or name in running:
                    continue
                dep_states = [jobs[d].status for d in job.deps]
                if any(s in (JobStatus.FAILED, JobStatus.SKIPPED) for s in dep_states):
                    job.status = JobStatus.SKIPPED
                    job.error = "dependency failed"
                    store.put_job(job)
                    ctx.emit("job:skipped", job_id=job.id, name=name)
                    continue
                if all(s == JobStatus.COMPLETED for s in dep_states):
                    running[name] = asyncio.create_task(self._execute(ctx, specs[name], job))
            if not running:
                break
            done, _ = await asyncio.wait(running.values(), return_when=asyncio.FIRST_COMPLETED)
            for name in [n for n, t in running.items() if t in done]:
                task = running.pop(name)
                job = jobs[name]
                exc = task.exception() if not task.cancelled() else asyncio.CancelledError()
                if task.cancelled():
                    job.status = JobStatus.INTERRUPTED
                    job.error = "cancelled"
                    failed = True
                elif exc is not None:
                    job.status = JobStatus.FAILED
                    job.error = str(exc)[:2000]
                    if not specs[name].optional:
                        failed = True
                    ctx.emit("job:failed", job_id=job.id, name=name, error=job.error)
                    if not isinstance(exc, JobFailed):
                        job.error += "\n" + "".join(traceback.format_exception(exc))[-1500:]
                else:
                    job.status = JobStatus.COMPLETED
                    job.result = task.result() or {}
                    ctx.results[name] = job.result
                    ctx.emit("job:done", job_id=job.id, name=name, cost_usd=job.cost_usd,
                             summary=job.result.get("summary"))
                job.ended_at = datetime.now(timezone.utc)
                store.put_job(job)
                ctx.run.cost_usd = round(sum(j.cost_usd for j in jobs.values()), 4)
                ctx.ws.store.put_run(ctx.run)
        return not failed

    async def _execute(self, ctx: RunContext, spec, job: Job) -> dict[str, Any]:
        handler = self.handlers.get(spec.handler)
        if handler is None:
            raise JobFailed(f"no handler registered for {spec.handler!r}")
        job.status = JobStatus.RUNNING
        job.attempts += 1
        job.started_at = datetime.now(timezone.utc)
        ctx.ws.store.put_job(job)
        ctx.run.phase = spec.name
        ctx.ws.store.put_run(ctx.run)
        ctx.emit("job:start", job_id=job.id, name=spec.name, job_kind=spec.kind.value, contract=spec.contract)
        rt = JobRuntime(ctx, job)
        return await handler(rt)
