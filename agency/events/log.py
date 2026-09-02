"""Append-only event log with in-process fan-out for SSE and tests."""
from __future__ import annotations

import asyncio
from typing import Any

from agency.domain.runs import CostEntry, Event
from agency.store.base import Store


class EventLog:
    def __init__(self, store: Store):
        self.store = store
        self._subscribers: set[asyncio.Queue] = set()

    def emit(self, kind: str, *, project_id: str | None = None, run_id: str | None = None,
             job_id: str | None = None, agent: str | None = None, tool_name: str | None = None,
             **data: Any) -> Event:
        event = Event(kind=kind, project_id=project_id, run_id=run_id, job_id=job_id, agent=agent,
                      tool_name=tool_name, data=_compact(data))
        self.store.append_event(event)
        for q in list(self._subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:  # pragma: no cover - slow consumer
                pass
        return event

    def record_cost(self, entry: CostEntry) -> None:
        self.store.add_cost(entry)
        self.emit("cost", project_id=entry.project_id, run_id=entry.run_id, job_id=entry.job_id,
                  agent=entry.agent, cost_usd=entry.cost_usd, num_turns=entry.num_turns,
                  duration_ms=entry.duration_ms, model=entry.model)

    def subscribe(self, maxsize: int = 1000) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)

    def replay(self, since_seq: int = 0, project_id: str | None = None, run_id: str | None = None,
               limit: int = 500) -> list[Event]:
        return self.store.list_events(since_seq=since_seq, project_id=project_id, run_id=run_id,
                                      limit=limit)


def _compact(data: dict[str, Any], max_len: int = 400) -> dict[str, Any]:
    """Keep event payloads small: truncate long strings, never store file bodies."""
    out: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, str) and len(v) > max_len:
            out[k] = v[:max_len] + "…"
        elif isinstance(v, (list, tuple)) and len(v) > 20:
            out[k] = list(v[:20]) + [f"… (+{len(v) - 20})"]
        else:
            out[k] = v
    return out
