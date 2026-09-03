"""The proposal graph: typed nodes with provenance edges."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Scope(str, Enum):
    PROJECT = "project"
    WORKSPACE = "workspace"


class NodeType(str, Enum):
    PROJECT = "Project"
    CALL_SPEC = "CallSpec"
    CRITERION = "Criterion"
    REQUIREMENT = "Requirement"
    SOURCE = "Source"
    CLAIM = "Claim"
    GAP = "Gap"
    NOVELTY_ANCHOR = "NoveltyAnchor"
    SECTION = "Section"
    FIGURE = "Figure"
    FINANCIAL_TABLE = "FinancialTable"
    DECISION = "Decision"
    REVIEW_FINDING = "ReviewFinding"
    PANEL_SCORE = "PanelScore"
    FEEDBACK = "Feedback"
    PATCH = "Patch"
    ENTITY = "Entity"
    CONCEPT = "Concept"
    IDEATION_BRIEF = "IdeationBrief"
    DOCUMENT = "Document"  # free-form artefacts: sota summary, outline, register, notes


class EdgeType(str, Enum):
    SUPPORTED_BY = "supported_by"      # Claim -> Source
    CITES = "cites"                    # Section -> Claim
    ADDRESSES = "addresses"            # Section -> Criterion | Gap
    ANCHORED_ON = "anchored_on"        # Section -> NoveltyAnchor
    SATISFIES = "satisfies"            # Section/Figure/Document -> Requirement
    DERIVED_FROM = "derived_from"      # any -> any (job provenance)
    FOUND_IN = "found_in"              # ReviewFinding -> Section
    SCORES = "scores"                  # PanelScore -> Criterion
    RESOLVED_BY = "resolved_by"        # Feedback -> Patch
    TARGETS = "targets"                # Patch/Feedback -> Section
    PROMOTED_TO = "promoted_to"        # project node -> workspace node
    EVIDENCE_OF = "evidence_of"        # Gap -> Source, NoveltyAnchor -> Source
    RELATES_TO = "relates_to"          # generic association
    PART_OF = "part_of"                # Section -> CallSpec, Criterion -> CallSpec


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Node(BaseModel):
    """Storage envelope for every typed node.

    `data` holds the type-specific payload (validated by the model in
    agency.domain.models that matches `type`). Version increments on every
    replace; earlier versions are retained by the store for history.
    """

    id: str
    type: NodeType
    scope: Scope = Scope.PROJECT
    project_id: str | None = None
    status: str = "active"
    version: int = 1
    created_by: str | None = None  # job id
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    data: dict[str, Any] = Field(default_factory=dict)

    def text(self) -> str:
        """Best-effort searchable text for the FTS index."""
        parts: list[str] = [self.id]
        for key in ("title", "text", "claim", "description", "statement", "comment",
                    "question", "decision", "name", "summary"):
            v = self.data.get(key)
            if isinstance(v, str):
                parts.append(v)
        return "\n".join(parts)


class Edge(BaseModel):
    src: str
    dst: str
    type: EdgeType
    created_by: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    data: dict[str, Any] = Field(default_factory=dict)
