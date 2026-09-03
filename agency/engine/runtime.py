"""Per-run and per-job runtime handed to job handlers."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from agency.catalogue.loader import AgentContract, Catalogue
from agency.catalogue.prompts import TaskSpec, render_task
from agency.domain.callspec import CallSpec
from agency.domain.graph import NodeType
from agency.domain.runs import InboxKind, Job, Run
from agency.engine.materialize import materialize
from agency.engine.plan import JobFailed
from agency.funders.packs import FunderPack
from agency.graph.repo import Graph
from agency.inbox.service import InboxService
from agency.sdk.adapter import AgentResult, JobContext, SDKAdapter
from agency.sdk.session import SessionResult, SessionRunner
from agency.tools.server import ToolContext
from agency.workspace import Workspace


@dataclass
class RunContext:
    ws: Workspace
    project_id: str
    run: Run
    catalogue: Catalogue
    adapter: SDKAdapter
    inbox: InboxService
    packs: dict[str, FunderPack]
    project_dir: Path
    kb_dir: Path
    flags: dict[str, Any] = field(default_factory=dict)
    results: dict[str, dict[str, Any]] = field(default_factory=dict)
    force: bool = False

    @property
    def graph(self) -> Graph:
        return self.ws.graph(self.project_id)

    def callspec(self) -> CallSpec | None:
        node = self.graph.callspec_node()
        if node is None:
            return None
        try:
            return CallSpec.model_validate(node.data)
        except Exception:
            return None

    def scope(self):
        from agency.domain.scope import ScopeConfig
        return ScopeConfig.load(self.ws.get_project(self.project_id))

    def pack(self) -> FunderPack:
        spec = self.callspec()
        pid = spec.pack if spec else None
        if not pid:
            project = self.ws.get_project(self.project_id)
            pid = (project.settings or {}).get("pack") if project else None
        return self.packs.get(pid or "generic", self.packs["generic"])

    def materialize(self) -> None:
        materialize(self.graph, self.project_dir, self.ws.blobs)

    def emit(self, kind: str, **data: Any) -> None:
        self.ws.events.emit(kind, project_id=self.project_id, run_id=self.run.id, **data)


class JobRuntime:
    """What a handler gets: graph access, one-call agent invocation, inbox, results of deps."""

    def __init__(self, ctx: RunContext, job: Job):
        self.ctx = ctx
        self.job = job
        self.ws = ctx.ws
        self.project_id = ctx.project_id
        self.graph = ctx.graph
        self.project_dir = ctx.project_dir
        self.kb_dir = ctx.kb_dir
        self.params = job.params
        self.flags = ctx.flags

    # ------------------------------------------------------------ deps / project
    def result_of(self, job_name: str) -> dict[str, Any]:
        return self.ctx.results.get(job_name, {})

    def context_document(self) -> dict[str, Any]:
        doc = self.graph.document("context")
        return doc.data if doc else {}

    def topic(self) -> str:
        project = self.ws.get_project(self.project_id)
        ctx = self.context_document()
        parts = [project.name if project else self.project_id]
        if project and project.topic:
            parts.append(project.topic)
        if ctx.get("hypothesis"):
            parts.append(ctx["hypothesis"])
        return " — ".join(p for p in parts if p)

    def emit(self, kind: str, **data: Any) -> None:
        self.ws.events.emit(kind, project_id=self.project_id, run_id=self.ctx.run.id, job_id=self.job.id,
                            **data)

    def log_decision(self, question: str, decision: str, rationale: list[str], *, type: str = "engine",
                     evidence_refs: list[str] | None = None) -> str:
        node = self.graph.add(NodeType.DECISION, {"question": question, "decision": decision,
                                                  "rationale": rationale, "type": type,
                                                  "evidence_refs": evidence_refs or [],
                                                  "date": date.today().isoformat()}, created_by=self.job.id)
        return node.id

    def reserve_ids(self, prefix: str, n: int) -> tuple[int, int]:
        ids = self.graph.allocate(prefix, n)
        nums = [int(re.search(r"(\d+)$", i).group(1)) for i in ids]
        return min(nums), max(nums)

    # ------------------------------------------------------------ agents
    async def agent(self, contract_name: str, *, phase: str = "", inputs: list[tuple[str, str]] | None = None,
                    instructions: str = "", output_model=None, id_ranges: dict[str, tuple[int, int]] | None = None,
                    allowed_writes: set[str] | None = None, model_override: str | None = None,
                    budget_usd: float | None = None, max_turns: int | None = None,
                    constraints: list[str] | None = None, kb_context: list[str] | None = None,
                    extra: dict[str, Any] | None = None, retry: bool = True,
                    output_contract: str = "") -> AgentResult:
        contract: AgentContract = self.ctx.catalogue.get(contract_name)
        self.ctx.materialize()
        writes = set(allowed_writes) if allowed_writes is not None else set(contract.writes)
        jc = JobContext(project_id=self.project_id, run_id=self.ctx.run.id, job_id=self.job.id,
                        project_dir=self.project_dir, kb_dir=self.kb_dir, graph=self.graph,
                        allowed_writes=writes, known_claim_ids={c.id for c in self.graph.claims()},
                        status_fn=lambda: self.ws.status(self.project_id))
        spec = TaskSpec(project_id=self.project_id, project_dir=self.project_dir, kb_dir=self.kb_dir,
                        run_id=self.ctx.run.id, job_id=self.job.id, stage=self.ctx.run.stage, phase=phase,
                        dedupe_key=f"{self.job.name}_{self.project_id}", inputs=inputs or [],
                        id_ranges=id_ranges or {}, instructions=instructions, kb_context=kb_context or [],
                        constraints=constraints or [], tools=contract.tools, extra=extra or {},
                        output_contract=output_contract)
        prompt = render_task(contract, spec)
        model = output_model or (contract.output_model() if contract.output_mode == "structured" else None)
        result = await self.ctx.adapter.run_agent(contract, jc, prompt, output_model=model,
                                                  model_override=model_override, budget_usd=budget_usd,
                                                  max_turns=max_turns)
        self.job.cost_usd += result.cost_usd
        if result.session_id:
            self.job.sdk_session_id = result.session_id
        if not result.ok and retry and result.subtype not in ("error_max_budget_usd",):
            self.emit("agent:retry", agent=contract_name, error=result.error)
            spec.instructions = (instructions + "\n\n## Previous attempt failed\n" + (result.error or "") +
                                 "\nFix the problem and return the contracted output.").strip()
            prompt = render_task(contract, spec)
            result = await self.ctx.adapter.run_agent(contract, jc, prompt, output_model=model,
                                                      model_override=model_override, budget_usd=budget_usd,
                                                      max_turns=max_turns)
            self.job.cost_usd += result.cost_usd
        if not result.ok:
            raise JobFailed(f"{contract_name}: {result.error or result.subtype}")
        return result

    # ------------------------------------------------------------ sessions
    async def session(self, contract_name: str, opening_prompt: str, *, until_kinds: set[str] | None = None,
                      max_user_turns: int = 30, on_submission=None, budget_usd: float | None = None,
                      allowed_writes: set[str] | None = None, header: str = "Conversation") -> SessionResult:
        contract = self.ctx.catalogue.get(contract_name)
        self.ctx.materialize()
        jc = JobContext(project_id=self.project_id, run_id=self.ctx.run.id, job_id=self.job.id,
                        project_dir=self.project_dir, kb_dir=self.kb_dir, graph=self.graph,
                        allowed_writes=set(allowed_writes if allowed_writes is not None else contract.writes),
                        known_claim_ids={c.id for c in self.graph.claims()},
                        status_fn=lambda: self.ws.status(self.project_id))
        counter = {"n": 0}

        async def ask(q: dict[str, Any]) -> dict[str, Any]:
            counter["n"] += 1
            return await self.ask(q.get("question", ""), q.get("options") or [], header=q.get("header") or header,
                                  multi=bool(q.get("multi")), key=f"{self.job.name}:q{counter['n']}")

        async def chat(agent_text: str, transcript: list[dict[str, str]]) -> str | None:
            counter["n"] += 1
            self._waiting(True)
            try:
                ans = await self.ctx.inbox.ask(project_id=self.project_id, kind=InboxKind.CHAT, header=header,
                                               question=agent_text[:4000] or "(the agent is waiting for your input)",
                                               payload={"transcript": "\n\n".join(f"**{t['role']}**: {t['text']}" for t in transcript[-8:])},
                                               run_id=self.ctx.run.id, job_id=self.job.id,
                                               key=f"{self.ctx.run.id}:{self.job.name}:chat{counter['n']}")
            finally:
                self._waiting(False)
            text = ans.get("text") or ans.get("choice") or ""
            return None if text.strip().lower() in ("stop", "quit", "abort") else text

        tool_ctx = ToolContext(graph=self.graph, project_id=self.project_id, job_id=self.job.id,
                               allowed_writes=set(jc.allowed_writes), ask=ask, status=jc.status_fn,
                               events=self.ws.events)
        runner = SessionRunner(self.ctx.adapter, client_factory=getattr(self.ctx.adapter, "client_factory", None))
        result = await runner.run(contract, jc, opening_prompt, tool_ctx=tool_ctx, chat=chat, until_kinds=until_kinds,
                                  max_user_turns=max_user_turns, budget_usd=budget_usd, on_submission=on_submission)
        self.job.cost_usd += result.cost_usd
        if result.session_id:
            self.job.sdk_session_id = result.session_id
        if not result.ok:
            raise JobFailed(f"{contract_name} session: {result.error}")
        return result

    # ------------------------------------------------------------ inbox
    async def ask(self, question: str, options: list[str | dict[str, str]] | None = None, *, header: str = "Question",
                  multi: bool = False, key: str | None = None) -> dict[str, Any]:
        self._waiting(True)
        try:
            return await self.ctx.inbox.ask(project_id=self.project_id, kind=InboxKind.QUESTION, header=header,
                                            question=question, payload={"options": options or [], "multi": multi},
                                            run_id=self.ctx.run.id, job_id=self.job.id,
                                            key=key and f"{self.ctx.run.id}:{key}")
        finally:
            self._waiting(False)

    async def approve(self, header: str, question: str, rows: list[dict[str, Any]], *,
                      decisions: list[str] | None = None, key: str | None = None) -> dict[str, Any]:
        self._waiting(True)
        try:
            return await self.ctx.inbox.ask(project_id=self.project_id, kind=InboxKind.APPROVAL, header=header,
                                            question=question,
                                            payload={"rows": rows, "decisions": decisions or ["approve", "reject", "defer"]},
                                            run_id=self.ctx.run.id, job_id=self.job.id,
                                            key=key and f"{self.ctx.run.id}:{key}")
        finally:
            self._waiting(False)

    async def form(self, header: str, question: str, schema: dict[str, Any], *, key: str | None = None,
                   example: dict[str, Any] | None = None) -> dict[str, Any]:
        self._waiting(True)
        try:
            return await self.ctx.inbox.ask(project_id=self.project_id, kind=InboxKind.FORM, header=header,
                                            question=question, payload={"schema": schema, "example": example or {}},
                                            run_id=self.ctx.run.id, job_id=self.job.id,
                                            key=key and f"{self.ctx.run.id}:{key}")
        finally:
            self._waiting(False)

    def _waiting(self, flag: bool) -> None:
        from agency.domain.runs import JobStatus, RunStatus
        self.job.status = JobStatus.WAITING if flag else JobStatus.RUNNING
        self.ws.store.put_job(self.job)
        self.ctx.run.status = RunStatus.WAITING_FOR_USER if flag else RunStatus.RUNNING
        self.ws.store.put_run(self.ctx.run)
