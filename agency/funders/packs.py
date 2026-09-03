"""Funder packs: outline templates, rubric hints, hard rules and default thresholds."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from agency.domain.callspec import RequirementSpec


class FunderPack(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    name: str
    funder: str = "unknown"
    match: list[str] = Field(default_factory=list)
    outline: str | None = None
    abstract_word_limit: int | None = None
    total_page_limit: float | None = None
    thresholds: dict[str, float] = Field(default_factory=dict)
    section_kinds: dict[str, str] = Field(default_factory=dict)
    criteria_hints: list[dict[str, Any]] = Field(default_factory=list)
    hard_rules: list[RequirementSpec] = Field(default_factory=list)
    annexes: list[str] = Field(default_factory=list)
    panel_personas: list[str] = Field(default_factory=list)
    root: Path | None = None

    def outline_text(self) -> str:
        if self.outline and self.root and (self.root / self.outline).exists():
            return (self.root / self.outline).read_text()
        return ""


def load_packs(root: str | Path) -> dict[str, FunderPack]:
    root = Path(root)
    packs: dict[str, FunderPack] = {}
    for pfile in sorted(root.glob("*/pack.yaml")):
        data = yaml.safe_load(pfile.read_text()) or {}
        pack = FunderPack.model_validate(data)
        pack.root = pfile.parent
        packs[pack.id] = pack
    if "generic" not in packs:
        packs["generic"] = FunderPack(id="generic", name="Generic")
    return packs


def detect_pack(packs: dict[str, FunderPack], *texts: str | None) -> FunderPack:
    """Pick the pack whose match keywords appear most in the given texts (funder name, call text)."""
    haystack = " ".join(t.lower() for t in texts if t)
    best, best_score = packs["generic"], 0
    for pack in packs.values():
        score = sum(len(k) for k in pack.match if k.lower() in haystack)
        if score > best_score:
            best, best_score = pack, score
    return best
