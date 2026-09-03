"""Agent catalogue: contracts + prompts on disk, validated at startup."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from agency.domain import callspec as callspec_models
from agency.domain import models as payload_models

Role = Literal["retriever", "synthesizer", "writer", "reviewer", "modeler", "renderer", "interviewer",
               "planner"]


class Budget(BaseModel):
    max_turns: int = 30
    max_usd: float = 5.0


class AgentContract(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    description: str = ""
    role: Role
    model_tier: Literal["fast", "balanced", "reasoning"] = "balanced"
    effort: Literal["low", "medium", "high", "xhigh", "max"] = "medium"
    tools: list[str] = Field(default_factory=lambda: ["Read", "Grep", "Glob"])
    connectors: list[str] = Field(default_factory=list)
    output: str | None = None
    output_mode: Literal["structured", "files", "session"] = "structured"
    budget: Budget = Field(default_factory=Budget)
    writes: list[str] = Field(default_factory=list)
    acceptance: list[dict[str, Any]] = Field(default_factory=list)
    env_keys: list[str] = Field(default_factory=list)
    session: bool = False
    notes: str = ""
    prompt_path: Path | None = None

    def output_model(self) -> type[BaseModel] | None:
        if not self.output:
            return None
        return resolve_output_model(self.output)

    def output_schema(self) -> dict[str, Any] | None:
        model = self.output_model()
        return model.model_json_schema() if model else None

    def load_prompt(self) -> str:
        if self.prompt_path is None or not self.prompt_path.exists():
            return ""
        return self.prompt_path.read_text()


def resolve_output_model(name: str) -> type[BaseModel]:
    for module in (payload_models, callspec_models):
        model = getattr(module, name, None)
        if isinstance(model, type) and issubclass(model, BaseModel):
            return model
    raise KeyError(f"unknown output model {name!r}")


class Catalogue(BaseModel):
    root: Path
    contracts: dict[str, AgentContract]
    conventions: str = ""

    def get(self, name: str) -> AgentContract:
        if name not in self.contracts:
            raise KeyError(f"no agent contract named {name!r}")
        return self.contracts[name]

    def by_role(self, role: str) -> list[AgentContract]:
        return [c for c in self.contracts.values() if c.role == role]

    def validate(self) -> list[str]:
        problems: list[str] = []
        for name, c in self.contracts.items():
            if c.prompt_path is None or not c.prompt_path.exists():
                problems.append(f"{name}: missing prompt.md")
            elif len(c.load_prompt()) < 200:
                problems.append(f"{name}: prompt.md is suspiciously short")
            if c.output:
                try:
                    resolve_output_model(c.output)
                except KeyError as e:
                    problems.append(f"{name}: {e}")
            if c.output_mode == "structured" and not c.output:
                problems.append(f"{name}: structured mode needs an output model")
            if c.session != (c.output_mode == "session"):
                problems.append(f"{name}: session flag and output_mode disagree")
            for conn in c.connectors:
                if conn not in KNOWN_CONNECTORS:
                    problems.append(f"{name}: unknown connector {conn!r}")
        for d in sorted(p for p in self.root.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))):
            if (d / "prompt.md").exists() and d.name not in self.contracts:
                problems.append(f"{d.name}: prompt.md without contract.yaml")
        if not self.conventions:
            problems.append("conventions.md missing")
        return problems


KNOWN_CONNECTORS = {"academic-search", "firecrawl"}


def load_catalogue(root: str | Path) -> Catalogue:
    root = Path(root)
    contracts: dict[str, AgentContract] = {}
    for cfile in sorted(root.glob("*/contract.yaml")):
        data = yaml.safe_load(cfile.read_text()) or {}
        data.setdefault("name", cfile.parent.name)
        contract = AgentContract.model_validate(data)
        contract.prompt_path = cfile.parent / "prompt.md"
        contracts[contract.name] = contract
    conv = root / "conventions.md"
    return Catalogue(root=root, contracts=contracts, conventions=conv.read_text() if conv.exists() else "")
