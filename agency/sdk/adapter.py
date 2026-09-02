"""Turns an agent contract + job context into one Claude Agent SDK query."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Callable

from claude_agent_sdk import (AssistantMessage, ClaudeAgentOptions, ResultMessage, SystemMessage,
                              TextBlock, ToolUseBlock, query)
from pydantic import BaseModel, ValidationError

from agency.catalogue.loader import AgentContract, Catalogue
from agency.catalogue.prompts import system_prompt
from agency.config import WorkspaceConfig
from agency.connectors.mcp import connector_configs, connector_tool_patterns
from agency.domain.runs import CostEntry
from agency.events.log import EventLog
from agency.graph.repo import Graph
from agency.hooks.guards import HookContext, build_hooks
from agency.tools.server import (AGENCY_TOOLS_READ, AGENCY_TOOLS_SESSION, AGENCY_TOOLS_WRITE, ToolContext,
                                 build_agency_server)


@dataclass
class JobContext:
    project_id: str
    run_id: str
    job_id: str
    project_dir: Path
    kb_dir: Path
    graph: Graph
    allowed_writes: set[str] = field(default_factory=set)
    known_claim_ids: set[str] = field(default_factory=set)
    status_fn: Callable[[], dict[str, Any]] | None = None
    extra_roots: list[Path] = field(default_factory=list)


@dataclass
class AgentResult:
    ok: bool
    subtype: str
    structured: dict[str, Any] | None = None
    text: str = ""
    cost_usd: float = 0.0
    num_turns: int = 0
    duration_ms: int = 0
    session_id: str | None = None
    model: str | None = None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
    tool_uses: int = 0
    submissions: list[dict[str, Any]] = field(default_factory=list)

    def parsed(self, model: type[BaseModel]) -> BaseModel:
        return model.model_validate(self.structured or {})


QueryFn = Callable[..., AsyncIterator[Any]]


class SDKAdapter:
    def __init__(self, config: WorkspaceConfig, catalogue: Catalogue, events: EventLog,
                 query_fn: QueryFn | None = None, client_factory: Callable[[Any], Any] | None = None):
        self.config = config
        self.catalogue = catalogue
        self.events = events
        self.query_fn = query_fn or query
        self.client_factory = client_factory
        self.semaphore = asyncio.Semaphore(config.max_concurrent_queries)

    # ------------------------------------------------------------ options
    def build_options(self, contract: AgentContract, jc: JobContext, *, output_model: type[BaseModel] | None,
                      model_override: str | None = None, budget_usd: float | None = None,
                      max_turns: int | None = None, tool_ctx: ToolContext | None = None,
                      can_use_tool: Callable | None = None) -> tuple[ClaudeAgentOptions, list[str]]:
        warnings: list[str] = []
        servers, conn_warnings = connector_configs(self.config, contract.connectors)
        warnings += conn_warnings
        tool_ctx = tool_ctx or ToolContext(graph=jc.graph, project_id=jc.project_id, job_id=jc.job_id,
                                           allowed_writes=set(jc.allowed_writes), status=jc.status_fn,
                                           events=self.events)
        mcp_servers: dict[str, Any] = {"agency": build_agency_server(tool_ctx)}
        mcp_servers.update(servers)
        if tool_ctx.ask is not None:
            agency_tools = AGENCY_TOOLS_SESSION
        elif jc.allowed_writes:
            agency_tools = AGENCY_TOOLS_WRITE
        else:
            agency_tools = AGENCY_TOOLS_READ
        allowed = list(dict.fromkeys(contract.tools + agency_tools + connector_tool_patterns(servers)))
        hooks = build_hooks(HookContext(project_id=jc.project_id, job_id=jc.job_id, run_id=jc.run_id,
                                        agent=contract.name, allowed_roots=[jc.project_dir, *jc.extra_roots],
                                        events=self.events, known_claim_ids=set(jc.known_claim_ids)))
        env = {k: v for k, v in self.config.secrets.items() if k in contract.env_keys}
        env["CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH"] = "1"
        model = model_override or self.config.models.get(contract.model_tier, contract.model_tier)
        opts = ClaudeAgentOptions(
            system_prompt=system_prompt(self.catalogue, contract, jc.project_dir, jc.kb_dir),
            allowed_tools=allowed,
            disallowed_tools=["Agent", "Task"],
            permission_mode="bypassPermissions",
            model=model,
            effort=contract.effort,
            max_turns=max_turns or contract.budget.max_turns,
            max_budget_usd=budget_usd or contract.budget.max_usd,
            output_format={"type": "json_schema", "schema": output_model.model_json_schema()} if output_model else None,
            cwd=str(jc.project_dir),
            setting_sources=[],
            mcp_servers=mcp_servers,
            hooks=hooks,
            env=env,
            can_use_tool=can_use_tool,
        )
        return opts, warnings

    # ------------------------------------------------------------ execution
    async def run_agent(self, contract: AgentContract, jc: JobContext, task_prompt: str, *,
                        output_model: type[BaseModel] | None = None, model_override: str | None = None,
                        budget_usd: float | None = None, max_turns: int | None = None,
                        tool_ctx: ToolContext | None = None) -> AgentResult:
        output_model = output_model or (contract.output_model() if contract.output_mode == "structured" else None)
        options, warnings = self.build_options(contract, jc, output_model=output_model,
                                               model_override=model_override, budget_usd=budget_usd,
                                               max_turns=max_turns, tool_ctx=tool_ctx)
        result = AgentResult(ok=False, subtype="not_started", model=options.model, warnings=warnings)
        self.events.emit("agent:start", project_id=jc.project_id, run_id=jc.run_id, job_id=jc.job_id,
                         agent=contract.name, model=options.model, warnings=warnings)
        started = time.monotonic()
        last_text: list[str] = []
        async with self.semaphore:
            try:
                async for message in self.query_fn(prompt=task_prompt, options=options):
                    self._observe(message, result, last_text)
            except Exception as e:  # SDK process/connection failures
                result.error = f"{type(e).__name__}: {e}"
                result.subtype = result.subtype if result.subtype != "not_started" else "error"
        result.duration_ms = result.duration_ms or int((time.monotonic() - started) * 1000)
        result.text = "\n".join(last_text[-3:])
        if tool_ctx is not None:
            result.submissions = list(tool_ctx.submissions)
        self._finalise(contract, jc, result, output_model)
        return result

    def _observe(self, message: Any, result: AgentResult, texts: list[str]) -> None:
        if isinstance(message, SystemMessage):
            if message.subtype == "init":
                result.session_id = message.data.get("session_id", result.session_id)
        elif isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock) and block.text.strip():
                    texts.append(block.text)
                elif isinstance(block, ToolUseBlock):
                    result.tool_uses += 1
        elif isinstance(message, ResultMessage):
            result.subtype = message.subtype
            result.session_id = message.session_id or result.session_id
            result.cost_usd = float(message.total_cost_usd or 0.0)
            result.num_turns = int(message.num_turns or 0)
            result.duration_ms = int(message.duration_ms or 0)
            result.structured = message.structured_output if isinstance(message.structured_output, dict) else None
            if message.is_error and not result.error:
                errs = getattr(message, "errors", None)
                result.error = "; ".join(map(str, errs)) if errs else f"result subtype {message.subtype}"
            usage = message.usage or {}
            result._usage = usage  # type: ignore[attr-defined]

    def _finalise(self, contract: AgentContract, jc: JobContext, result: AgentResult,
                  output_model: type[BaseModel] | None) -> None:
        usage = getattr(result, "_usage", {}) or {}
        self.events.record_cost(CostEntry(
            project_id=jc.project_id, run_id=jc.run_id, job_id=jc.job_id, agent=contract.name,
            model=result.model, cost_usd=result.cost_usd, num_turns=result.num_turns,
            duration_ms=result.duration_ms, input_tokens=int(usage.get("input_tokens", 0) or 0),
            output_tokens=int(usage.get("output_tokens", 0) or 0),
            cache_read_tokens=int(usage.get("cache_read_input_tokens", 0) or 0)))
        if result.error:
            result.ok = False
        elif output_model is not None:
            if result.structured is None:
                result.ok = False
                result.error = f"no structured output (subtype={result.subtype})"
            else:
                try:
                    output_model.model_validate(result.structured)
                    result.ok = True
                except ValidationError as e:
                    result.ok = False
                    result.error = f"structured output failed {output_model.__name__} validation: {str(e)[:600]}"
        else:
            result.ok = result.subtype == "success"
            if not result.ok and not result.error:
                result.error = f"result subtype {result.subtype}"
        self.events.emit("agent:end", project_id=jc.project_id, run_id=jc.run_id, job_id=jc.job_id,
                         agent=contract.name, ok=result.ok, subtype=result.subtype, cost_usd=result.cost_usd,
                         num_turns=result.num_turns, duration_ms=result.duration_ms, error=result.error,
                         tool_uses=result.tool_uses)
