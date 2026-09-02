"""Server-sent events: replay from the event log, then live fan-out."""
from __future__ import annotations

import asyncio
import time
from typing import AsyncIterator, Awaitable, Callable

from agency.workspace import Workspace


async def sse_stream(ws: Workspace, *, project: str | None, since: int = 0, replay: int = 200,
                     is_disconnected: Callable[[], Awaitable[bool]] | None = None,
                     ping_seconds: float = 15.0) -> AsyncIterator[str]:
    q = ws.events.subscribe()  # subscribe first so nothing is lost between replay and live
    yield "event: ready\ndata: {}\n\n"
    last = since
    recent = ws.events.replay(since, project, None, 100000)
    for ev in recent if since else recent[-replay:]:
        last = max(last, ev.seq or 0)
        yield f"event: event\nid: {ev.seq}\ndata: {ev.model_dump_json()}\n\n"
    try:
        while True:
            if is_disconnected is not None and await is_disconnected():
                break
            try:
                ev = await asyncio.wait_for(q.get(), timeout=ping_seconds)
            except asyncio.TimeoutError:
                yield f"event: ping\ndata: {int(time.time() * 1000)}\n\n"
                continue
            if project and ev.project_id and ev.project_id != project:
                continue
            if (ev.seq or 0) <= last:
                continue
            last = ev.seq or last
            yield f"event: event\nid: {ev.seq}\ndata: {ev.model_dump_json()}\n\n"
    finally:
        ws.events.unsubscribe(q)
