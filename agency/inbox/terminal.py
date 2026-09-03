"""Terminal responder for ``agency run``: prints inbox items and reads stdin."""
from __future__ import annotations

import asyncio
import json
from typing import Any

from agency.domain.runs import InboxItem, InboxKind


async def terminal_responder(item: InboxItem) -> dict[str, Any] | None:
    print(f"\n=== [{item.kind.value}] {item.header}")
    print(item.question)
    loop = asyncio.get_running_loop()
    if item.kind == InboxKind.QUESTION:
        options = item.payload.get("options") or []
        for i, opt in enumerate(options, 1):
            label = opt["label"] if isinstance(opt, dict) else opt
            desc = opt.get("description", "") if isinstance(opt, dict) else ""
            print(f"  {i}. {label}{' — ' + desc if desc else ''}")
        raw = await loop.run_in_executor(None, input, "> ")
        raw = raw.strip()
        if raw.isdigit() and options and 1 <= int(raw) <= len(options):
            opt = options[int(raw) - 1]
            return {"choice": opt["label"] if isinstance(opt, dict) else opt, "text": raw}
        return {"choice": raw, "text": raw}
    if item.kind == InboxKind.APPROVAL:
        rows = item.payload.get("rows") or []
        for r in rows:
            print(f"  - {r.get('id')}: {r.get('summary', '')[:100]}")
        print("Type 'approve' to approve all, 'reject' to reject all, or JSON {id: decision}.")
        raw = (await loop.run_in_executor(None, input, "> ")).strip()
        if raw.lower() in ("approve", "a", "y", "yes", ""):
            return {"decision": "approve", "rows": {r.get("id"): "approve" for r in rows}}
        if raw.lower() in ("reject", "r", "n", "no"):
            return {"decision": "reject", "rows": {r.get("id"): "reject" for r in rows}}
        try:
            return {"decision": "custom", "rows": json.loads(raw)}
        except json.JSONDecodeError:
            return {"decision": "approve", "rows": {r.get("id"): "approve" for r in rows}, "note": raw}
    if item.kind == InboxKind.FORM:
        print("Paste JSON for the form (schema in payload.schema), or a path to a JSON file:")
        raw = (await loop.run_in_executor(None, input, "> ")).strip()
        try:
            if raw.endswith(".json"):
                return {"data": json.load(open(raw))}
            return {"data": json.loads(raw)}
        except (OSError, json.JSONDecodeError):
            return {"data": {}, "text": raw}
    raw = await loop.run_in_executor(None, input, "> ")
    return {"text": raw.strip()}
