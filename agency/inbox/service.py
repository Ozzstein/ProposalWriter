"""The single human channel: persisted inbox items that runs block on."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from agency.domain.runs import InboxItem, InboxKind, InboxStatus

Responder = Callable[[InboxItem], Awaitable[dict[str, Any] | None]]


class InboxService:
    def __init__(self, ws):
        self.ws = ws
        self._waiters: dict[str, asyncio.Future] = {}
        self.responder: Responder | None = None   # terminal adapter hooks in here

    # ------------------------------------------------------------ create / wait
    async def ask(self, *, project_id: str, kind: InboxKind | str, header: str, question: str,
                  payload: dict[str, Any] | None = None, run_id: str | None = None, job_id: str | None = None,
                  key: str | None = None) -> dict[str, Any]:
        """Create (or reuse) an inbox item and wait for its answer."""
        kind = InboxKind(kind)
        item_id = key or f"inb-{uuid.uuid4().hex[:10]}"
        existing = self.ws.store.get_inbox(item_id)
        if existing and existing.status == InboxStatus.ANSWERED and existing.answer is not None:
            return existing.answer
        if existing is None:
            item = InboxItem(id=item_id, project_id=project_id, run_id=run_id, job_id=job_id, kind=kind,
                             header=header, question=question, payload=payload or {})
            self.ws.store.put_inbox(item)
        else:
            item = existing
        self.ws.events.emit("inbox:pending", project_id=project_id, run_id=run_id, job_id=job_id,
                            item_id=item.id, item_kind=kind.value, header=header, question=question)
        loop = asyncio.get_running_loop()
        fut = self._waiters.get(item.id)
        if fut is None or fut.done():
            fut = loop.create_future()
            self._waiters[item.id] = fut
        if self.responder is not None:
            answer = await self.responder(item)
            if answer is not None:
                self.answer(item.id, answer)
        return await fut

    # ------------------------------------------------------------ answer
    def answer(self, item_id: str, answer: dict[str, Any]) -> InboxItem:
        item = self.ws.store.get_inbox(item_id)
        if item is None:
            raise KeyError(f"inbox item {item_id!r} not found")
        if item.status == InboxStatus.ANSWERED:
            raise ValueError(f"inbox item {item_id!r} already answered")
        item.answer = answer
        item.status = InboxStatus.ANSWERED
        item.answered_at = datetime.now(timezone.utc)
        self.ws.store.put_inbox(item)
        self.ws.events.emit("inbox:answered", project_id=item.project_id, run_id=item.run_id,
                            job_id=item.job_id, item_id=item.id, item_kind=item.kind.value)
        fut = self._waiters.pop(item_id, None)
        if fut is not None and not fut.done():
            fut.set_result(answer)
        return item

    def cancel(self, item_id: str, reason: str = "cancelled") -> None:
        item = self.ws.store.get_inbox(item_id)
        if item and item.status == InboxStatus.PENDING:
            item.status = InboxStatus.CANCELLED
            self.ws.store.put_inbox(item)
        fut = self._waiters.pop(item_id, None)
        if fut is not None and not fut.done():
            fut.set_exception(asyncio.CancelledError(reason))

    def pending(self, project_id: str | None = None) -> list[InboxItem]:
        return self.ws.store.list_inbox(project_id=project_id, status=InboxStatus.PENDING.value)

    def cancel_run(self, run_id: str) -> None:
        for item in self.ws.store.list_inbox(run_id=run_id, status=InboxStatus.PENDING.value):
            self.cancel(item.id, "run stopped")
