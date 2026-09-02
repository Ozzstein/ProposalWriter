"""In-process MCP server exposed to every agent as ``mcp__agency__*``."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Awaitable, Callable

from claude_agent_sdk import create_sdk_mcp_server, tool

from agency.domain.graph import NodeType
from agency.graph.repo import Graph

WRITABLE_TYPES = {"Source", "Claim", "Gap", "NoveltyAnchor", "Decision", "Entity", "Concept", "Document",
                  "Feedback", "Figure"}


@dataclass
class ToolContext:
    graph: Graph
    project_id: str
    job_id: str
    allowed_writes: set[str] = field(default_factory=set)       # node types this job may write
    ask: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]] | None = None  # sessions only
    status: Callable[[], dict[str, Any]] | None = None
    submissions: list[dict[str, Any]] = field(default_factory=list)
    finished: asyncio.Event = field(default_factory=asyncio.Event)
    events: Any = None
    handlers: dict[str, Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]] = field(default_factory=dict)


def _text(payload: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(payload, default=str, ensure_ascii=False)}]}


def _error(msg: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps({"error": msg})}], "is_error": True}


def build_agency_server(ctx: ToolContext):
    g = ctx.graph

    @tool("graph_read", "Read nodes from the proposal graph. type is one of Source, Claim, Gap, "
          "NoveltyAnchor, Section, Decision, Feedback, Figure, Criterion, Requirement, Document, "
          "ReviewFinding, PanelScore, Entity, Concept. Give id to fetch one node.",
          {"type": str, "id": str, "status": str, "limit": int})
    async def graph_read(args: dict[str, Any]) -> dict[str, Any]:
        if args.get("id"):
            node = g.get(args["id"])
            return _text(node.model_dump(mode="json") if node else None)
        try:
            ntype = NodeType(args.get("type", "Source"))
        except ValueError:
            return _error(f"unknown node type {args.get('type')!r}")
        nodes = g.nodes(ntype, status=args.get("status") or None)
        limit = int(args.get("limit") or 100)
        return _text([{"id": n.id, "status": n.status, **n.data} for n in nodes[:limit]])

    @tool("graph_search", "Full-text search over graph nodes (title, text, claim, description).",
          {"text": str, "type": str, "limit": int})
    async def graph_search(args: dict[str, Any]) -> dict[str, Any]:
        nodes = g.store.search_nodes(args.get("text", ""), project_id=ctx.project_id,
                                     type=args.get("type") or None, limit=int(args.get("limit") or 25))
        return _text([{"id": n.id, "type": n.type.value, **n.data} for n in nodes])

    @tool("graph_write", "Register a validated node in the graph (allocates its ID when omitted). "
          "type: Source | Claim | Gap | NoveltyAnchor | Decision | Entity | Concept | Document | Feedback | Figure. "
          "data: the node payload as an object. Returns the node id or validation errors.",
          {"type": str, "data": dict})
    async def graph_write(args: dict[str, Any]) -> dict[str, Any]:
        ntype = args.get("type")
        if ntype not in WRITABLE_TYPES:
            return _error(f"type {ntype!r} is not writable through this tool")
        if ctx.allowed_writes and ntype not in ctx.allowed_writes:
            return _error(f"this job may only write {sorted(ctx.allowed_writes)}")
        data = args.get("data")
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return _error("data must be a JSON object")
        if not isinstance(data, dict):
            return _error("data must be an object")
        try:
            node = g.add(NodeType(ntype), data, created_by=ctx.job_id)
        except Exception as e:  # pydantic ValidationError etc.
            return _error(f"validation failed: {e}")
        if ctx.events is not None:
            ctx.events.emit("graph:write", project_id=ctx.project_id, job_id=ctx.job_id,
                            node_id=node.id, node_type=ntype)
        return _text({"id": node.id, "type": ntype})

    @tool("next_ids", "Reserve n new identifiers for a prefix (SRC, CLM, GAP, NOV, DEC, FBK, PATCH, F).",
          {"prefix": str, "n": int})
    async def next_ids(args: dict[str, Any]) -> dict[str, Any]:
        prefix = str(args.get("prefix", "")).upper()
        if prefix not in {"SRC", "CLM", "GAP", "NOV", "DEC", "FBK", "PATCH", "F", "FRM"}:
            return _error("unsupported prefix")
        return _text(g.allocate(prefix, max(1, min(int(args.get("n") or 1), 100))))

    @tool("log_decision", "Record a decision with rationale in the decision log.",
          {"question": str, "decision": str, "rationale": list, "evidence_refs": list, "type": str})
    async def log_decision(args: dict[str, Any]) -> dict[str, Any]:
        data = {"question": args.get("question", ""), "decision": args.get("decision", ""),
                "rationale": list(args.get("rationale") or []), "evidence_refs": list(args.get("evidence_refs") or []),
                "date": date.today().isoformat(), "type": args.get("type") or "agent_decision"}
        node = g.add(NodeType.DECISION, data, created_by=ctx.job_id)
        return _text({"id": node.id})

    @tool("project_status", "Stages, gates and node counts for this project.", {})
    async def project_status(args: dict[str, Any]) -> dict[str, Any]:
        return _text(ctx.status() if ctx.status else {"graph": g.summary()})

    tools = [graph_read, graph_search, graph_write, next_ids, log_decision, project_status]

    if ctx.ask is not None:
        @tool("ask_user", "Ask the researcher a question and wait for the answer. options is a list of "
              "short labels (2-6); leave empty for free text.", {"question": str, "options": list,
                                                                  "header": str, "multi": bool})
        async def ask_user(args: dict[str, Any]) -> dict[str, Any]:
            answer = await ctx.ask({"question": args.get("question", ""), "options": list(args.get("options") or []),
                                    "header": args.get("header") or "Question", "multi": bool(args.get("multi"))})
            return _text(answer)

        @tool("submit_result", "Submit a structured result for this session (kind names the payload type, "
              "e.g. framings, choice, financial_inputs, interview_batch). May be called several times.",
              {"kind": str, "payload": dict})
        async def submit_result(args: dict[str, Any]) -> dict[str, Any]:
            ctx.submissions.append({"kind": args.get("kind", ""), "payload": args.get("payload") or {}})
            return _text({"accepted": True, "kind": args.get("kind", "")})

        @tool("finish", "End the interactive session with a short summary.", {"summary": str})
        async def finish(args: dict[str, Any]) -> dict[str, Any]:
            ctx.submissions.append({"kind": "finish", "payload": {"summary": args.get("summary", "")}})
            ctx.finished.set()
            return _text({"ok": True})

        tools += [ask_user, submit_result, finish]

    ctx.handlers = {t.name: t.handler for t in tools}
    server = create_sdk_mcp_server(name="agency", version="1.0.0", tools=tools)
    try:
        server["instance"]._agency_handlers = ctx.handlers  # convenient for tests/tooling
    except Exception:  # pragma: no cover
        pass
    return server


AGENCY_TOOLS_READ = ["mcp__agency__graph_read", "mcp__agency__graph_search", "mcp__agency__next_ids",
                     "mcp__agency__project_status", "mcp__agency__log_decision"]
AGENCY_TOOLS_WRITE = AGENCY_TOOLS_READ + ["mcp__agency__graph_write"]
AGENCY_TOOLS_SESSION = AGENCY_TOOLS_WRITE + ["mcp__agency__ask_user", "mcp__agency__submit_result",
                                             "mcp__agency__finish"]
