"""CallSpec — the parsed funding call that drives planning."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SectionSpec(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str                                # e.g. "1", "1.2", "abstract"
    title: str
    kind: Literal["abstract", "excellence", "impact", "implementation", "financial",
                  "business_plan", "annex", "other"] = "other"
    word_limit: int | None = None
    page_limit: float | None = None
    weight: float = 0.0                    # share of total score this section carries
    criterion_ids: list[str] = Field(default_factory=list)
    template_source: str | None = None     # uploaded template, builtin pack, or parsed call
    guidance: str = ""                     # what the call says the section must contain
    required: bool = True


class CriterionSpec(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str                                # e.g. "C1", "C2.1"
    name: str
    text: str = ""
    max_score: float = 5.0
    weight: float = 1.0
    threshold: float | None = None         # minimum score to stay eligible
    section_ids: list[str] = Field(default_factory=list)


RequirementKind = Literal["eligibility", "hard_rule", "format", "annex", "deadline", "budget"]


class RequirementSpec(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    kind: RequirementKind
    text: str
    rule: str | None = None                # evaluable expression, e.g. "cer_eur_per_tco2 <= 200"
    disqualifying: bool = False
    applies_to: list[str] = Field(default_factory=list)  # section ids / annex ids
    status: Literal["unknown", "met", "unmet", "not_applicable"] = "unknown"


class CallSpec(BaseModel):
    model_config = ConfigDict(extra="allow")
    call_id: str
    title: str
    funder: str
    programme: str | None = None
    instrument: str | None = None          # e.g. "RIA", "R01", "Large-scale"
    pack: str = "generic"                  # funder pack id
    deadline: str | None = None
    summary: str = ""
    sections: list[SectionSpec]
    criteria: list[CriterionSpec]
    requirements: list[RequirementSpec] = Field(default_factory=list)
    annexes: list[str] = Field(default_factory=list)
    budget_rules: dict[str, Any] = Field(default_factory=dict)
    abstract_word_limit: int | None = None
    total_page_limit: float | None = None
    source_documents: list[str] = Field(default_factory=list)

    def max_weighted_score(self) -> float:
        return sum(c.max_score * c.weight for c in self.criteria)

    def section(self, section_id: str) -> SectionSpec | None:
        return next((s for s in self.sections if s.id == section_id), None)

    def has_financials(self) -> bool:
        return bool(self.budget_rules) or any(s.kind == "financial" for s in self.sections)

    def needs_business_plan(self) -> bool:
        return any(s.kind == "business_plan" for s in self.sections) or any(
            "business plan" in a.lower() for a in self.annexes)
