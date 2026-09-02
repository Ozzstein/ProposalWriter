"""A scripted stand-in for claude_agent_sdk.query used by the tests."""
from __future__ import annotations

import dataclasses
from typing import Any

from claude_agent_sdk import AssistantMessage, ResultMessage, SystemMessage, TextBlock, ToolUseBlock


def _fill(cls, **kw):
    for f in dataclasses.fields(cls):
        if f.name not in kw and f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING:
            kw[f.name] = None
    return cls(**kw)


def make_result(structured: Any = None, subtype: str = "success", cost: float = 0.01, turns: int = 2,
                text: str = "done", is_error: bool = False, errors: list[str] | None = None) -> ResultMessage:
    return _fill(ResultMessage, subtype=subtype, duration_ms=12, duration_api_ms=8, is_error=is_error,
                 num_turns=turns, session_id="sess-1", total_cost_usd=cost,
                 usage={"input_tokens": 100, "output_tokens": 50}, result=text, structured_output=structured,
                 errors=errors or [])


class FakeQuery:
    """Callable that records prompts/options and yields a canned stream per call."""

    def __init__(self, responder=None):
        self.calls: list[dict[str, Any]] = []
        self.responder = responder or (lambda prompt, options: {"structured": None})

    async def __call__(self, prompt: str, options=None):
        self.calls.append({"prompt": prompt, "options": options})
        spec = self.responder(prompt, options)
        if isinstance(spec, ResultMessage):
            spec = {"result": spec}
        yield _fill(SystemMessage, subtype="init", data={"session_id": "sess-1", "tools": []})
        for text in spec.get("texts", ["working"]):
            yield _fill(AssistantMessage, content=[TextBlock(text=text)], model="fake")
        for tool in spec.get("tool_uses", []):
            yield _fill(AssistantMessage, content=[ToolUseBlock(id="t1", name=tool, input={})], model="fake")
        if "hook" in spec:  # let tests drive the in-process tools directly
            await spec["hook"](options)
        yield spec.get("result") or make_result(spec.get("structured"), subtype=spec.get("subtype", "success"))
