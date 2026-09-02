"""Workspace configuration.

A *workspace* is the tenant unit: one SQLite database, one blob directory,
one set of secrets. Defaults are local-first; every path can be overridden in
``agency.toml`` (repo root) or environment variables.
"""
from __future__ import annotations

import json
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_MODELS = {
    "fast": "claude-haiku-4-5",
    "balanced": "claude-sonnet-5",
    "reasoning": "claude-opus-5",
}


@dataclass
class WorkspaceConfig:
    root: Path
    db_url: str
    blobs_dir: Path
    agents_dir: Path
    packs_dir: Path
    schemas_dir: Path
    legacy_runs_dir: Path
    models: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_MODELS))
    max_concurrent_queries: int = 6
    default_budget_usd: float = 5.0
    stage_budget_usd: float = 40.0
    host: str = "127.0.0.1"
    port: int = 7777
    secrets: dict[str, str] = field(default_factory=dict)
    gate_thresholds: dict[str, float] = field(default_factory=dict)
    panel_max_iterations: int = 3
    panel_min_gain: float = 2.0

    @property
    def db_path(self) -> Path | None:
        if self.db_url.startswith("sqlite:///"):
            return Path(self.db_url[len("sqlite:///"):])
        return None

    def ensure_dirs(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.blobs_dir.mkdir(parents=True, exist_ok=True)
        (self.root / "projects").mkdir(exist_ok=True)

    def project_dir(self, project_id: str) -> Path:
        d = self.root / "projects" / project_id
        d.mkdir(parents=True, exist_ok=True)
        return d


def _load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def _load_secrets(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    return {k: str(v) for k, v in data.items() if not k.startswith("_") and isinstance(v, str) and v}


def load_config(root: str | os.PathLike | None = None) -> WorkspaceConfig:
    """Resolve the workspace config. Precedence: args > env > agency.toml > defaults."""
    toml = _load_toml(REPO_ROOT / "agency.toml")
    ws = toml.get("workspace", {})
    root_path = Path(root or os.environ.get("AGENCY_HOME") or ws.get("root") or (REPO_ROOT / "workspace"))
    root_path = root_path.expanduser().resolve()
    db_url = os.environ.get("AGENCY_DB_URL") or ws.get("db_url") or f"sqlite:///{root_path / 'workspace.db'}"
    models = dict(DEFAULT_MODELS)
    models.update(toml.get("models", {}))
    for tier in list(models):
        env_key = f"AGENCY_MODEL_{tier.upper()}"
        if os.environ.get(env_key):
            models[tier] = os.environ[env_key]
    limits = toml.get("limits", {})
    server = toml.get("server", {})
    secrets = _load_secrets(Path(ws.get("secrets_file", REPO_ROOT / "secrets.json")))
    for key in ("ANTHROPIC_API_KEY", "FAL_KEY", "FIRECRAWL_API_KEY", "ELSEVIER_API_KEY"):
        if os.environ.get(key):
            secrets[key] = os.environ[key]
    return WorkspaceConfig(
        root=root_path,
        db_url=db_url,
        blobs_dir=Path(ws.get("blobs_dir", root_path / "blobs")),
        agents_dir=Path(ws.get("agents_dir", REPO_ROOT / "agents")),
        packs_dir=Path(ws.get("packs_dir", REPO_ROOT / "packs")),
        schemas_dir=Path(ws.get("schemas_dir", REPO_ROOT / "schemas")),
        legacy_runs_dir=Path(ws.get("legacy_runs_dir", REPO_ROOT / "runs")),
        models=models,
        max_concurrent_queries=int(limits.get("max_concurrent_queries", 6)),
        default_budget_usd=float(limits.get("default_budget_usd", 5.0)),
        stage_budget_usd=float(limits.get("stage_budget_usd", 40.0)),
        host=os.environ.get("AGENCY_HOST", server.get("host", "127.0.0.1")),
        port=int(os.environ.get("AGENCY_PORT", server.get("port", 7777))),
        secrets=secrets,
        gate_thresholds={k: float(v) for k, v in toml.get("gates", {}).items()},
        panel_max_iterations=int(limits.get("panel_max_iterations", 3)),
        panel_min_gain=float(limits.get("panel_min_gain", 2.0)),
    )
