"""Interactive sessions: a ClaudeSDKClient conversation whose questions go through the inbox."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from claude_agent_sdk import AssistantMessage, ClaudeSDKClient, ResultMessage, TextBlock, ToolUseBlock
from claude_agent_sdk.types import PermissionResultAllow

from agency.catalogue.loader import AgentContract
from agency.domain.runs import CostEntry
from agency.sdk.adapter import JobContext, SDKAdapter
from agency.tools.server import ToolContext


@dataclass
class SessionResult:
    ok: bool
    submissions: list[dict[str, Any]] = field(default_factory=list)
    transcript: list[dict[str, str]] = field(default_factory=list)   # {role, text}
    cost_usd: float = 0.0
    num_turns: int = 0
    duration_ms: int = 0
    session_id: str | None = None
    error: str | None = None
    user_turns: int = 0

    def latest(self, kind: str) -> dict[str, Any] | None:
        for s in reversed(self.submissions):
            if s.get("kind") == kind:
                return s.get("payload")
        return None

    def all(self, kind: str) -> list[dict[str, Any]]:
        return [s.get("payload") or {} for s in self.submissions if s.get("kind") == kind]


ChatFn = Callable[[str, list[dict[str, str]]], Awaitable[str | None]]


class SessionRunner:
    def __init__(self, adapter: SDKAdapter, client_factory: Callable[[Any], Any] | None = None):
        self.adapter = adapter
        self.client_factory = client_factory or (lambda options: ClaudeSDKClient(options=options))

    async def run(self, contract: AgentContract, jc: JobContext, opening_prompt: str, *, tool_ctx: ToolContext,
                  chat: ChatFn, until_kinds: set[str] | None = None, max_user_turns: int = 30,
                  budget_usd: float | None = None, on_submission: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
                  model_override: str | None = None) -> SessionResult:
        assert tool_ctx.ask is not None, "session tool context needs an ask() callback"

        async def can_use_tool(tool_name: str, input_data: dict[str, Any], context: Any):
            if tool_name == "AskUserQuestion":
                answers: dict[str, Any] = {}
                for q in input_data.get("questions", []):
                    options = [o.get("label") if isinstance(o, dict) else str(o) for o in q.get("options", [])]
                    ans = await tool_ctx.ask({"question": q.get("question", ""), "options": options,
                                              "header": q.get("header") or "Question", "multi": bool(q.get("multiSelect"))})
                    val = ans.get("choices") if q.get("multiSelect") and ans.get("choices") else (ans.get("choice") or ans.get("text") or "")
                    answers[q.get("question", "")] = val
                return PermissionResultAllow(updated_input={"questions": input_data.get("questions", []), "answers": answers})
            return PermissionResultAllow(updated_input=input_data)

        options, warnings = self.adapter.build_options(contract, jc, output_model=None, tool_ctx=tool_ctx,
                                                       can_use_tool=can_use_tool, budget_usd=budget_usd,
                                                       model_override=model_override)
        result = SessionResult(ok=False)
        started = time.monotonic()
        seen = 0
        self.adapter.events.emit("session:start", project_id=jc.project_id, run_id=jc.run_id, job_id=jc.job_id,
                                 agent=contract.name, warnings=warnings)
        try:
            client = self.client_factory(options)
            async with client:
                await client.query(opening_prompt)
                result.transcript.append({"role": "user", "text": opening_prompt[:2000]})
                while True:
                    last_text: list[str] = []
                    async for message in client.receive_response():
                        self._observe(message, result, last_text, jc, contract)
                    if last_text:
                        result.transcript.append({"role": "assistant", "text": "\n".join(last_text)})
                    for s in tool_ctx.submissions[seen:]:
                        if on_submission is not None:
                            await on_submission(s)
                    seen = len(tool_ctx.submissions)
                    kinds = {s.get("kind") for s in tool_ctx.submissions}
                    if tool_ctx.finished.is_set() or (until_kinds and until_kinds <= kinds):
                        break
                    if result.user_turns >= max_user_turns:
                        result.error = "max user turns reached"
                        break
                    reply = await chat("\n".join(last_text), result.transcript)
                    if reply is None:
                        break
                    result.user_turns += 1
                    result.transcript.append({"role": "user", "text": reply})
                    await client.query(reply)
            result.ok = result.error is None
        except Exception as e:
            result.error = f"{type(e).__name__}: {e}"
            result.ok = False
        result.submissions = list(tool_ctx.submissions)
        result.duration_ms = int((time.monotonic() - started) * 1000)
        self.adapter.events.emit("session:end", project_id=jc.project_id, run_id=jc.run_id, job_id=jc.job_id,
                                 agent=contract.name, ok=result.ok, cost_usd=result.cost_usd, turns=result.num_turns,
                                 user_turns=result.user_turns, error=result.error)
        return result

    def _observe(self, message: Any, result: SessionResult, texts: list[str], jc: JobContext, contract: AgentContract) -> None:
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock) and block.text.strip():
                    texts.append(block.text)
                elif isinstance(block, ToolUseBlock):
                    self.adapter.events.emit("tool:use", project_id=jc.project_id, run_id=jc.run_id, job_id=jc.job_id,
                                             agent=contract.name, tool_name=block.name)
        elif isinstance(message, ResultMessage):
            cost = float(message.total_cost_usd or 0.0)
            result.cost_usd += cost
            result.num_turns += int(message.num_turns or 0)
            result.session_id = message.session_id or result.session_id
            usage = message.usage or {}
            self.adapter.events.record_cost(CostEntry(
                project_id=jc.project_id, run_id=jc.run_id, job_id=jc.job_id, agent=contract.name,
                model=message.model_usage and next(iter(message.model_usage), None) if message.model_usage else None,
                cost_usd=cost, num_turns=int(message.num_turns or 0), duration_ms=int(message.duration_ms or 0),
                input_tokens=int(usage.get("input_tokens", 0) or 0), output_tokens=int(usage.get("output_tokens", 0) or 0)))
            if message.is_error and message.subtype not in ("success",):
                result.error = result.error or f"session turn ended with {message.subtype}"
