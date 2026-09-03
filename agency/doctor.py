"""Installation health check."""
from __future__ import annotations

import importlib
import os
from typing import Any


def run_doctor(root: str | None = None) -> dict[str, Any]:
    from agency.workspace import Workspace

    report: dict[str, Any] = {"ok": True, "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        report["checks"].append({"check": name, "ok": ok, "detail": detail})
        if not ok:
            report["ok"] = False

    try:
        sdk = importlib.import_module("claude_agent_sdk")
        check("claude-agent-sdk importable", True, getattr(sdk, "__version__", "?"))
    except ImportError as e:  # pragma: no cover
        check("claude-agent-sdk importable", False, str(e))
    ws = Workspace.open(root)
    check("workspace database", True, ws.config.db_url)
    key = ws.config.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    check("ANTHROPIC_API_KEY present", bool(key), "set" if key else "missing — model calls will fail")
    for opt in ("FIRECRAWL_API_KEY", "FAL_KEY", "ELSEVIER_API_KEY"):
        report["checks"].append({"check": f"{opt} (optional)", "ok": True,
                                 "detail": "set" if ws.config.secrets.get(opt) else "not set"})
    try:
        from agency.catalogue.loader import load_catalogue
        cat = load_catalogue(ws.config.agents_dir)
        problems = cat.validate()
        check(f"agent catalogue ({len(cat.contracts)} contracts)", not problems, "; ".join(problems) or "valid")
    except Exception as e:
        check("agent catalogue", False, f"{type(e).__name__}: {e}")
    try:
        from agency.funders.packs import load_packs
        packs = load_packs(ws.config.packs_dir)
        check(f"funder packs ({len(packs)})", len(packs) > 0, ", ".join(sorted(packs)))
    except Exception as e:
        check("funder packs", False, f"{type(e).__name__}: {e}")
    report["projects"] = len(ws.list_projects())
    return report
