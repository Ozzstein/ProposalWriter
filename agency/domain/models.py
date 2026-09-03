"""Typed payloads for graph nodes and agent outputs.

These are the pydantic successors of the JSON schemas in ``schemas/``.
Field names and enums are kept identical so legacy runs import cleanly and
existing prompts keep working. ``extra="allow"`` keeps rich agent output.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Payload(BaseModel):
    model_config = ConfigDict(extra="allow")


# --------------------------------------------------------------- evidence

SourceType = Literal["paper", "patent", "standard", "internal", "report", "review", "web", "dataset"]
Quality = Literal["low", "medium", "high"]


class Source(Payload):
    source_id: str | None = None
    title: str
    authors: str | None = None
    year: int | None = None
    type: SourceType = "paper"
    quality: Quality = "medium"
    extract: str = ""
    limitations: list[str] = Field(default_factory=list)
    relevance_tags: list[str] = Field(default_factory=list)
    url: str | None = None
    doi: str | None = None
    full_text_available: bool | None = None
    oa_url: str | None = None
    retrieved_by: str | None = None


class ClaimCandidate(Payload):
    claim_text: str
    source_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, default=0.5)


class EvidenceResult(Payload):
    """Retriever output (literature_searcher, web_scraper, patent_scanner, probes)."""

    task_id: str = ""
    topic: str
    summary: str
    sources: list[Source]
    claims: list[ClaimCandidate] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    paywalled_dois: list[str] = Field(default_factory=list)


ClaimType = Literal["technical_benefit", "scientific_finding", "impact_statement",
                    "methodology_claim", "novelty_claim", "assumption", "financial"]
ClaimStatus = Literal["supported", "assumption", "unsupported", "disputed"]


class Claim(Payload):
    claim_id: str | None = None
    text: str
    type: ClaimType
    supported_by: list[str] = Field(default_factory=list)
    owner_agent: str | None = None
    status: ClaimStatus
    created_at: date | str | None = None


class ClaimBatch(Payload):
    claims: list[Claim]


# --------------------------------------------------------------- synthesis

class NoveltyAnchor(Payload):
    anchor_id: str | None = None
    claim: str
    novelty_type: Literal["first", "only", "best", "combination", "scale", "application"]
    dimension: Literal["technical", "process", "integration", "application", "scale"]
    existing_art: str = ""
    gap: str = ""
    supported_by: list[str] = Field(min_length=1)
    confidence: Quality
    attack_surface: str
    defensibility_score: float = Field(ge=1, le=10)
    related_claims: list[str] = Field(default_factory=list)


class NoveltyMap(Payload):
    project_name: str
    generated_at: str | None = None
    novelty_summary: str = ""
    novelty_anchors: list[NoveltyAnchor] = Field(min_length=1)
    weak_points: list[str] = Field(default_factory=list)
    minimum_anchors_met: bool


class Gap(Payload):
    gap_id: str | None = None
    type: Literal["research", "technology", "application", "integration", "regulatory"]
    sub_type: Literal["studied-and-open", "not-studied", "solved-elsewhere-not-applied"]
    description: str
    evidence_of_gap: list[str] = Field(min_length=1)
    severity: Literal["critical", "major", "moderate", "minor"]
    project_solution: str = ""
    addressed_in_section: str = ""
    strategic_importance: float = Field(ge=1, le=10)
    competitor_risk: str = ""


class GapAnalysis(Payload):
    project_name: str
    generated_at: str | None = None
    gap_landscape_summary: str = ""
    gaps: list[Gap] = Field(min_length=1)
    top_gaps_for_proposal: list[str] = Field(min_length=1)
    criterion_gap_mapping: dict[str, list[str]] = Field(default_factory=dict)


class SotaOutput(Payload):
    """state_of_art_synthesizer structured return: the narrative lives in a file."""

    summary_markdown: str
    claims: list[Claim] = Field(default_factory=list)
    key_areas: list[str] = Field(default_factory=list)
    thin_areas: list[str] = Field(default_factory=list)


# --------------------------------------------------------------- writing

class SectionDraft(Payload):
    section_name: str
    target_audience: str | None = None
    draft_text: str
    claim_ids: list[str]
    source_ids: list[str] = Field(default_factory=list)
    assumptions_used: list[str] = Field(default_factory=list)
    open_issues: list[str] = Field(default_factory=list)
    word_count: int | None = None


class SectionDraftBatch(Payload):
    drafts: list[SectionDraft]


# --------------------------------------------------------------- review

class Fix(Payload):
    priority: Literal["critical", "high", "medium", "low"]
    action: str
    section_name: str | None = None
    estimated_score_gain: str | None = None


class ReviewReport(Payload):
    section_name: str
    reviewer_type: Literal["scientific", "compliance", "writing", "consistency",
                           "evaluator_simulation", "financial", "business_plan"]
    overall_score: float = Field(ge=0, le=10)
    major_issues: list[str]
    minor_issues: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    redundancies: list[str] = Field(default_factory=list)
    fixes: list[Fix]
    strengths: list[str] = Field(default_factory=list)


class ReviewBatch(Payload):
    sections: list[ReviewReport]
    hard_rejection_checks: list["HardRejectionCheck"] = Field(default_factory=list)


class HardRejectionCheck(Payload):
    check_id: str
    description: str
    met: bool
    hard_rejection_risk: bool
    evidence: str = ""
    action_required: str = ""


class CriterionScore(Payload):
    criterion_id: str
    criterion_name: str
    max_score: float
    weight: float = 1.0
    max_weighted_score: float | None = None
    predicted_score_range: list[float] | None = None
    predicted_score_central: float
    predicted_weighted_score: float | None = None
    score_rationale: str = ""
    weakest_argument: str = ""
    score_ceiling: float | None = None
    hard_rejection_risk: bool = False
    improvement_actions: list[str] = Field(default_factory=list)


class RankedAction(Payload):
    rank: int
    criterion: str
    action: str
    estimated_score_gain: str = ""
    section_name: str | None = None


class EvaluatorSummary(Payload):
    hard_rejection_risks_detected: list[str] = Field(default_factory=list)
    total_predicted_weighted_score: float
    total_max_weighted_score: float
    score_percentage: float | None = None
    funding_probability: Literal["high", "medium", "low", "at_risk"]
    percentile_estimate: str = ""
    top_3_risks: list[str] = Field(default_factory=list)
    top_3_strengths: list[str] = Field(default_factory=list)
    single_highest_impact_action: str = ""
    improvement_actions_ranked: list[RankedAction] = Field(default_factory=list)


class EvaluatorSimulation(Payload):
    project_name: str
    call_topic: str
    generated_at: str | None = None
    simulated_evaluator_profiles: list[str] = Field(default_factory=list)
    hard_rejection_checks: list[HardRejectionCheck]
    criterion_scores: list[CriterionScore]
    summary: EvaluatorSummary


# --------------------------------------------------------------- feedback

FeedbackCategory = Literal["evidence", "technical", "structural", "writing", "compliance",
                           "style", "financial", "business_plan", "ambiguous", "parse_error", "ack"]
FeedbackStatus = Literal["open", "in_progress", "resolved", "deferred", "skipped", "rejected",
                         "ack", "unlocatable", "stale", "parse_error"]
CLOSED_FEEDBACK_STATUSES = {"resolved", "deferred", "rejected", "ack", "stale", "skipped",
                            "unlocatable"}


class FeedbackEntry(Payload):
    feedback_id: str | None = None
    round: int = Field(ge=1)
    reviewer: str | None = None
    source_file: str
    location: str | None = None
    original_text: str | None = None
    comment: str
    category: FeedbackCategory
    comment_type: Literal["inline_comment", "tracked_change", "chat", "annotation"] | None = None
    candidates: list[str] = Field(default_factory=list)
    routed_to: str | None = None
    status: FeedbackStatus = "open"
    resolution: str | None = None
    resolved_at: str | None = None
    round_closed: int | None = None
    dedupe_key: str


class FeedbackParse(Payload):
    entries: list[FeedbackEntry]
    parse_notes: str = ""


class FeedbackPatch(Payload):
    patch_id: str | None = None
    feedback_id: str
    target_file: str
    old_text: str
    new_text: str
    rationale: str
    new_claim_ids: list[str] = Field(default_factory=list)
    new_source_ids: list[str] = Field(default_factory=list)


class PatchBatch(Payload):
    patches: list[FeedbackPatch]
    flagged_needs_evidence: list[str] = Field(default_factory=list)
    flagged_needs_orchestrator: list[str] = Field(default_factory=list)
    new_claims: list[Claim] = Field(default_factory=list)
    new_sources: list[Source] = Field(default_factory=list)


# --------------------------------------------------------------- figures

class FigureSpec(Payload):
    figure_id: str
    title: str
    type: Literal["concept", "schematic", "sankey", "gantt", "heatmap", "curve", "bar", "pie",
                  "map", "flow", "other"]
    generator: Literal["fal.ai", "matplotlib", "plotly", "mermaid", "graphviz", "manual"]
    model_version: str | None = None
    location: str
    owner: str | None = None
    status: Literal["tbd", "in_progress", "draft", "final"]
    data_inputs: list[str] = Field(default_factory=list)
    prompt: str | None = None
    negative_prompt: str | None = None
    script_path: str | None = None
    seed: int | None = None
    image_size: str | None = None
    output_path: str | None = None
    output_width_px: int | None = None
    output_height_px: int | None = None
    generated_at: str | None = None
    notes: str | None = None


class FigureBatch(Payload):
    figures: list[FigureSpec]


# --------------------------------------------------------------- decisions

class Decision(Payload):
    decision_id: str | None = None
    question: str
    decision: str
    rationale: list[str]
    evidence_refs: list[str] = Field(default_factory=list)
    alternatives_considered: list[str] = Field(default_factory=list)
    date: str | None = None
    type: str | None = None  # e.g. approve_unsupported_claim, gate_override, framing_chosen


# --------------------------------------------------------------- ideation

class FramingScores(Payload):
    novelty_defensibility: float = Field(ge=1, le=10)
    gap_alignment: float = Field(ge=1, le=10)
    feasibility: float = Field(ge=1, le=10)
    call_fit: float | None = Field(default=None, ge=1, le=10)


class Framing(Payload):
    framing_id: str
    statement: str
    mechanism: str
    novelty_type: Literal["first", "only", "best", "combination", "scale", "application"]
    target_gap: str
    prior_art_summary: str = ""
    closest_prior_art: list[str] = Field(default_factory=list)
    differentiation: str = ""
    scores: FramingScores | None = None
    risks: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class IdeationBrief(Payload):
    project_name: str
    generated_at: str | None = None
    raw_idea: str
    interview_summary: str = ""
    candidate_framings: list[Framing] = Field(min_length=1)
    recommendation: str = ""
    chosen_framing_id: str | None = None
    status: Literal["draft", "chosen", "needs_rework"] = "draft"


# --------------------------------------------------------------- planning

class PlannedStep(Payload):
    """One stage run inside a campaign proposed by the planning agent."""

    step: int = Field(ge=1)
    stage: str
    flags: dict[str, Any] = Field(default_factory=dict)
    force: bool = False
    rationale: str
    expected_outcome: str = ""
    stop_if: str = ""            # human-readable condition under which the campaign should stop after this step


class RunPlan(Payload):
    goal: str
    assessment: str
    steps: list[PlannedStep] = Field(min_length=1)
    risks: list[str] = Field(default_factory=list)
    questions_for_researcher: list[str] = Field(default_factory=list)
    stop_conditions: list[str] = Field(default_factory=list)
    estimated_cost_usd: float | None = None


# --------------------------------------------------------------- finance

class FinancialInputs(Payload):
    """User-supplied financials. Validated in depth by schemas/financial_inputs.json."""

    meta: dict[str, Any]
    capex: dict[str, Any]
    opex: dict[str, Any]
    headcount: dict[str, Any] | None = None
    revenues: dict[str, Any] | None = None
    financing: dict[str, Any]
    working_capital: dict[str, Any] | None = None
    ghg_linkage: dict[str, Any]
    milestones: dict[str, Any] | None = None
    assumptions_approved_by_user: list[dict[str, Any]] = Field(default_factory=list)


class FinancialTables(Payload):
    tables: dict[str, Any]
    metrics: dict[str, Any] = Field(default_factory=dict)
    markdown: str = ""
    claims: list[Claim] = Field(default_factory=list)
    hard_threshold_checks: list[HardRejectionCheck] = Field(default_factory=list)


# --------------------------------------------------------------- misc

class Entity(Payload):
    name: str
    kind: Literal["organisation", "project", "competitor", "person", "product", "other"] = "other"
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class Concept(Payload):
    name: str
    description: str = ""
    related_claims: list[str] = Field(default_factory=list)
    related_gaps: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class Document(Payload):
    """Free-form artefact: markdown body + kind (sota_summary, outline, register, ...)."""

    kind: str
    title: str
    body: str = ""
    path: str | None = None  # blob path when the body is large or binary


PAYLOAD_BY_NODE_TYPE: dict[str, type[Payload]] = {
    "Source": Source,
    "Claim": Claim,
    "Gap": Gap,
    "NoveltyAnchor": NoveltyAnchor,
    "Section": SectionDraft,
    "Figure": FigureSpec,
    "Decision": Decision,
    "Feedback": FeedbackEntry,
    "Patch": FeedbackPatch,
    "Entity": Entity,
    "Concept": Concept,
    "IdeationBrief": IdeationBrief,
    "Document": Document,
}
