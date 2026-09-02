"""External MCP connectors (stdio servers) with per-connector secret injection."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

from agency.config import REPO_ROOT, WorkspaceConfig

ACADEMIC_SEARCH_SERVER = REPO_ROOT / "mcp-servers" / "academic-search" / "server.py"


def _python() -> str:
    return sys.executable


def connector_configs(config: WorkspaceConfig, names: list[str]) -> tuple[dict[str, Any], list[str]]:
    """Return (mcp_servers dict, warnings) for the requested connector names."""
    servers: dict[str, Any] = {}
    warnings: list[str] = []
    for name in names:
        if name == "academic-search":
            if not ACADEMIC_SEARCH_SERVER.exists():
                warnings.append("academic-search server missing")
                continue
            env = {}
            if config.secrets.get("ELSEVIER_API_KEY"):
                env["ELSEVIER_API_KEY"] = config.secrets["ELSEVIER_API_KEY"]
            servers["academic-search"] = {"type": "stdio", "command": _python(),
                                          "args": [str(ACADEMIC_SEARCH_SERVER)], "env": env}
        elif name == "firecrawl":
            key = config.secrets.get("FIRECRAWL_API_KEY")
            if not key:
                warnings.append("FIRECRAWL_API_KEY not set — firecrawl connector skipped")
                continue
            npx = shutil.which("npx")
            if not npx:
                warnings.append("npx not on PATH — firecrawl connector skipped")
                continue
            servers["firecrawl-mcp"] = {"type": "stdio", "command": npx, "args": ["-y", "firecrawl-mcp"],
                                        "env": {"FIRECRAWL_API_KEY": key}}
        else:
            warnings.append(f"unknown connector {name!r}")
    return servers, warnings


def connector_tool_patterns(servers: dict[str, Any]) -> list[str]:
    return [f"mcp__{name}__*" for name in servers]
