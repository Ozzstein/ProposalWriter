"""Deterministic review gates evaluated against the proposal graph.

Each rule is a plain function ``(ctx) -> Criterion``. A gate is a named list
of rules. No model judgment is involved anywhere in this module.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from pydantic import BaseModel, Field

from agency.domain.callspec import CallSpec
from agency.domain.graph import EdgeType, Node
from agency.domain.models import CLOSED_FEEDBACK_STATUSES
from agency.domain.scope import MODULE_STATE_KEY, ScopeConfig, concept_status_of
from agency.graph.repo import Graph
from agency.policy.thresholds import GATES, resolve


class Criterion(BaseModel):
    criterion: str
    met: bool
    notes: str = ""


class GateResult(BaseModel):
    gate_name: str
    passed: bool
    not_applicable: bool = False
    checked_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    criteria: list[Criterion] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


@dataclass
class GateContext:
    graph: Graph
    thresholds: dict[str, float]
    callspec: CallSpec | None = None
    scope: ScopeConfig | None = None
    stages: dict[str, dict[str, Any]] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def t(self) -> dict[str, float]:
        return self.thresholds


Rule = Callable[[GateContext], Criterion | None]


def crit(name: str, met: bool, notes: str = "") -> Criterion:
    return Criterion(criterion=name, met=bool(met), notes=notes)


# ------------------------------------------------------------------ scope

def rule_call_parsed(ctx: GateContext) -> Criterion:
    ok = ctx.callspec is not None and bool(ctx.callspec.sections)
    return crit("Call document parsed into a CallSpec with sections", ok,
                f"{len(ctx.callspec.sections)} sections" if ok else "no CallSpec node")


def rule_criteria_mapped(ctx: GateContext) -> Criterion:
    n = len(ctx.callspec.criteria) if ctx.callspec else 0
    return crit("Evaluation criteria mapped", n > 0, f"{n} criteria")


def rule_outline_exists(ctx: GateContext) -> Criterion:
    doc = ctx.graph.document("outline")
    ok = doc is not None and bool(doc.data.get("body", "").strip())
    return crit("Proposal outline created", ok, "outline document present" if ok else "no outline")


def rule_context_documented(ctx: GateContext) -> Criterion:
    doc = ctx.graph.document("context")
    body = (doc.data.get("body", "") if doc else "")
    hyp = (doc.data.get("hypothesis") if doc else None) or ""
    has = bool(hyp.strip()) and "to be completed" not in hyp.lower()
    if not has and body:
        has = ("hypothes" in body.lower() or "central idea" in body.lower()) and \
            "_to be completed._" not in body.lower()
    return crit("Research context documented with a real hypothesis", has,
                "hypothesis present" if has else "context missing or still the placeholder")


def rule_eligibility(ctx: GateContext) -> Criterion:
    reqs = [r for r in (ctx.callspec.requirements if ctx.callspec else [])
            if r.kind == "eligibility" and r.disqualifying]
    unmet = [r.id for r in reqs if r.status == "unmet"]
    unknown = [r.id for r in reqs if r.status == "unknown"]
    ok = not unmet and not unknown
    notes = "all disqualifying eligibility requirements confirmed" if ok else (
        f"unmet: {unmet}" if unmet else f"unconfirmed: {unknown}")
    if not reqs:
        return crit("Eligibility confirmed", True, "no disqualifying requirements parsed")
    return crit("Eligibility confirmed", ok, notes)


def rule_scope_configured(ctx: GateContext) -> Criterion:
    if ctx.scope is None:
        return crit("Proposal scope configured", False, "scope not configured; run parse-call with scope_only")
    ok = bool(ctx.scope.configured_at)
    return crit("Proposal scope configured", ok, ctx.scope.summary() if ok else "derived but not confirmed")


def rule_concept_aligned(ctx: GateContext) -> Criterion:
    status = concept_status_of(ctx.graph.document("context"))
    if status == "none":
        return crit("Concept aligned with the call", True, "no hypothesis yet")
    return crit("Concept aligned with the call", status == "aligned",
                "aligned" if status == "aligned" else
                "preliminary concept not aligned to the call; run parse-call with align_only")


# ------------------------------------------------------------------ evidence

def rule_min_sources(ctx: GateContext) -> Criterion:
    n = len(ctx.graph.sources())
    m = int(ctx.t["min_evidence"])
    return crit(f"Evidence store has >= {m} sources", n >= m, f"{n} unique sources")


def rule_sota(ctx: GateContext) -> Criterion:
    doc = ctx.graph.document("sota_summary")
    ok = doc is not None and len(doc.data.get("body", "")) > 200
    return crit("SOTA summary exists", ok, "sota_summary document" if ok else "missing")


def rule_anchors(ctx: GateContext) -> Criterion:
    anchors = ctx.graph.anchors()
    m = int(ctx.t["min_anchors"])
    d = ctx.t["min_anchor_defensibility"]
    strong = [a for a in anchors if float(a.data.get("defensibility_score", 0)) >= d]
    ok = len(anchors) >= m and len(strong) >= m
    return crit(f"Novelty map has >= {m} anchors with defensibility >= {d:g}", ok,
                f"{len(anchors)} anchors, {len(strong)} defensible")


def rule_gaps(ctx: GateContext) -> Criterion:
    gaps = ctx.graph.gaps()
    m = int(ctx.t["min_gaps"])
    top = [g for g in gaps if g.data.get("priority_rank")]
    ok = len(gaps) >= m and bool(top)
    return crit(f"Gap analysis has >= {m} gaps with top gaps selected", ok,
                f"{len(gaps)} gaps, {len(top)} prioritised")


def rule_claims_registered(ctx: GateContext) -> Criterion:
    n = len(ctx.graph.claims())
    return crit("Claim registry populated", n >= 1, f"{n} claims")


def rule_unsupported_ratio(ctx: GateContext) -> Criterion:
    claims = ctx.graph.claims()
    unsupported = [c for c in claims if c.data.get("status") == "unsupported"]
    ratio = len(unsupported) / len(claims) if claims else 1.0
    m = ctx.t["max_unsupported_ratio"]
    return crit(f"<= {int(m * 100)}% unsupported claims", bool(claims) and ratio <= m,
                f"{len(unsupported)}/{len(claims)} unsupported ({ratio:.0%})" if claims else "no claims")


# ------------------------------------------------------------------ draft

def _required_sections(ctx: GateContext) -> list[str]:
    if not ctx.callspec:
        return []
    sections = [s for s in ctx.callspec.sections if s.required and s.kind != "annex"]
    if ctx.scope is not None and ctx.scope.state("finance") == "excluded":
        sections = [s for s in sections if s.kind != "financial"]  # drafting skips these too
    return [s.id for s in sections]


def rule_all_sections_drafted(ctx: GateContext) -> Criterion:
    required = _required_sections(ctx)
    drafted = {s.data.get("section_id") for s in ctx.graph.sections()
               if s.status in ("draft", "final", "active") and s.data.get("draft_text", "").strip()}
    if required:
        missing = [r for r in required if r not in drafted]
        return crit("All required sections have drafts", not missing,
                    f"missing: {missing}" if missing else f"{len(required)} sections covered")
    return crit("All required sections have drafts", len(drafted) >= 3,
                f"no CallSpec — fallback: {len(drafted)} drafts (need >= 3)")


def rule_drafts_cite_claims(ctx: GateContext) -> Criterion:
    sections = ctx.graph.sections()
    unlinked = []
    for s in sections:
        cites = ctx.graph.out(s.id, EdgeType.CITES)
        refs = ctx.graph.claim_refs(s.data.get("draft_text", ""))
        if not cites and not refs and not s.data.get("claim_ids"):
            unlinked.append(s.data.get("section_id", s.id))
    return crit("All drafts reference claim IDs", bool(sections) and not unlinked,
                f"no claim references in: {unlinked}" if unlinked else f"{len(sections)} drafts checked")


def rule_assumption_markers(ctx: GateContext) -> Criterion:
    m = int(ctx.t["max_assumptions_per_draft"])
    over = [s.data.get("section_id", s.id) for s in ctx.graph.sections()
            if s.data.get("draft_text", "").count("[ASSUMPTION]") > m]
    return crit(f"<= {m} [ASSUMPTION] markers per draft", not over,
                f"over limit: {over}" if over else "")


def rule_unregistered_refs(ctx: GateContext) -> Criterion:
    bad: dict[str, list[str]] = {}
    for s in ctx.graph.sections():
        missing = ctx.graph.unregistered_refs(s.data.get("draft_text", ""))
        if missing:
            bad[s.data.get("section_id", s.id)] = sorted(missing)
    return crit("All cited claim/source IDs exist in the graph", not bad,
                f"unknown refs: {bad}" if bad else "")


def rule_abstract_limit(ctx: GateContext) -> Criterion:
    limit = int(ctx.t["default_abstract_words"])
    if ctx.callspec:
        if ctx.callspec.abstract_word_limit:
            limit = ctx.callspec.abstract_word_limit
        else:
            for s in ctx.callspec.sections:
                if s.kind == "abstract" and s.word_limit:
                    limit = s.word_limit
    abstract = next((s for s in ctx.graph.sections()
                     if s.data.get("kind") == "abstract" or "abstract" in str(s.data.get("section_name", "")).lower()), None)
    if abstract is None:
        return crit("Abstract exists and is within word limit", False, "no abstract section drafted")
    words = len(abstract.data.get("draft_text", "").split())
    return crit("Abstract exists and is within word limit", words <= limit, f"{words} words (limit {limit})")


def rule_section_limits(ctx: GateContext) -> Criterion:
    if not ctx.callspec:
        return crit("Sections within word limits", True, "no CallSpec limits")
    over = []
    for spec in ctx.callspec.sections:
        if not spec.word_limit:
            continue
        node = ctx.graph.section(spec.id)
        if node and len(node.data.get("draft_text", "").split()) > spec.word_limit:
            over.append(spec.id)
    return crit("Sections within word limits", not over, f"over limit: {over}" if over else "")


def rule_required_modules_complete(ctx: GateContext) -> Criterion:
    if ctx.scope is None:
        return crit("Required modules complete", True, "scope not configured")
    missing = [m for m in ("finance", "business_plan", "figures")
               if ctx.scope.state(m) == "required"
               and ctx.stages.get(MODULE_STATE_KEY[m], {}).get("status") != "complete"]
    return crit("Required modules complete", not missing,
                f"incomplete: {missing}" if missing else (f"{ctx.scope.required() or 'none'} required"))


# ------------------------------------------------------------------ submission

def _latest_by_section(findings: list[Node]) -> dict[tuple[str, str], Node]:
    """Latest report per (section, reviewer_type); later rounds supersede earlier ones."""
    out: dict[tuple[str, str], Node] = {}
    for f in sorted(findings, key=lambda n: (int(n.data.get("round", 0) or 0), n.created_at)):
        out[(f.data.get("section_name", f.id), f.data.get("reviewer_type", ""))] = f
    return out


def rule_scientific_scores(ctx: GateContext) -> Criterion:
    m = ctx.t["min_scientific_score"]
    latest = _latest_by_section(ctx.graph.findings("scientific"))
    low = [(k[0], v.data.get("overall_score")) for k, v in latest.items()
           if not isinstance(v.data.get("overall_score"), (int, float)) or v.data["overall_score"] < m]
    return crit(f"Scientific review score >= {m:g} for all sections", bool(latest) and not low,
                f"below threshold: {low}" if low else (f"{len(latest)} section reports pass" if latest
                                                        else "no scientific review found"))


def rule_no_critical_fixes(ctx: GateContext) -> Criterion:
    critical = []
    for f in _latest_by_section(ctx.graph.findings()).values():
        for fx in f.data.get("fixes", []):
            if fx.get("priority") == "critical" and fx.get("status", "open") == "open":
                critical.append((f.data.get("section_name"), fx.get("action", "")[:60]))
    return crit("No critical issues open in latest review reports", not critical,
                f"critical fixes open: {critical}" if critical else "")


def rule_compliance(ctx: GateContext) -> Criterion:
    latest = _latest_by_section(ctx.graph.findings("compliance"))
    unmet = [(k[0], v.data.get("major_issues")) for k, v in latest.items() if v.data.get("major_issues")]
    return crit("Compliance review passes", bool(latest) and not unmet,
                f"major issues: {unmet}" if unmet else ("pass" if latest else "no compliance review found"))


def rule_unsupported_resolved(ctx: GateContext) -> Criterion:
    approved = ctx.graph.approved_unsupported()
    unresolved = sorted(c.id for c in ctx.graph.unsupported_claims() if c.id not in approved)
    return crit("All unsupported claims resolved or user-approved", not unresolved,
                f"unresolved: {unresolved}" if unresolved else "")


def rule_hard_rules(ctx: GateContext) -> Criterion:
    reqs = [r for r in (ctx.callspec.requirements if ctx.callspec else []) if r.kind == "hard_rule"]
    unmet = [r.id for r in reqs if r.status == "unmet"]
    unknown = [r.id for r in reqs if r.status == "unknown" and r.disqualifying]
    ok = not unmet and not unknown
    if not reqs:
        return crit("Hard-rejection rules satisfied", True, "no hard rules in CallSpec")
    return crit("Hard-rejection rules satisfied", ok, f"unmet: {unmet}, unconfirmed: {unknown}" if not ok
                else f"{len(reqs)} rules met")


def rule_panel_score(ctx: GateContext) -> Criterion:
    panel = ctx.graph.latest_panel()
    if panel is None:
        return crit("Simulated panel predicts a competitive score", False, "no panel simulation run")
    summary = panel.data.get("summary", {})
    pct = summary.get("score_percentage")
    if pct is None and summary.get("total_max_weighted_score"):
        pct = 100 * summary.get("total_predicted_weighted_score", 0) / summary["total_max_weighted_score"]
    risks = summary.get("hard_rejection_risks_detected", [])
    m = ctx.t["min_predicted_score_pct"]
    ok = pct is not None and pct >= m and not risks
    return crit(f"Simulated panel predicts >= {m:g}% with no hard-rejection risk", ok,
                f"predicted {pct:.0f}%, risks: {risks}" if pct is not None else "no score")


# ------------------------------------------------------------------ external feedback

def rule_feedback_open(ctx: GateContext) -> Criterion | None:
    fb = ctx.graph.feedback()
    if not fb:
        return None
    active = max((int(f.data.get("round", 0)) for f in fb), default=0)
    open_ids = sorted(f.id for f in fb if int(f.data.get("round", 0)) == active
                      and f.data.get("status") in ("open", "in_progress"))
    return crit(f"No open/in-progress comments in active round {active}", not open_ids,
                f"still open: {open_ids}" if open_ids else f"{len(fb)} comments tracked")


def rule_feedback_statuses(ctx: GateContext) -> Criterion | None:
    fb = ctx.graph.feedback()
    if not fb:
        return None
    bad = sorted(f.id for f in fb if f.data.get("status") not in CLOSED_FEEDBACK_STATUSES | {"open", "in_progress", "parse_error"})
    return crit("All comments have a recognised status", not bad, f"unexpected status on: {bad}" if bad else "")


def rule_feedback_stale(ctx: GateContext) -> Criterion | None:
    fb = ctx.graph.feedback()
    if not fb:
        return None
    stale = sorted(f.id for f in fb if f.data.get("status") == "stale" and not f.data.get("resolution"))
    return crit("All stale comments carry an explanatory resolution", not stale,
                f"missing resolution: {stale}" if stale else "")


def rule_external_review_required(ctx: GateContext) -> Criterion | None:
    if ctx.scope is None or ctx.scope.state("external_review") != "required":
        return None
    fb = ctx.graph.feedback()
    if not fb:
        return crit("External review round ingested and closed", False, "no external feedback ingested")
    sub = [c for c in (rule_feedback_open(ctx), rule_feedback_statuses(ctx), rule_feedback_stale(ctx)) if c]
    failed = [c.notes or c.criterion for c in sub if not c.met]
    return crit("External review round ingested and closed", not failed,
                "; ".join(failed) if failed else f"{len(fb)} comments closed")


GATE_RULES: dict[str, list[Rule]] = {
    "scope": [rule_call_parsed, rule_criteria_mapped, rule_outline_exists, rule_context_documented,
              rule_eligibility, rule_scope_configured, rule_concept_aligned],
    "evidence": [rule_min_sources, rule_sota, rule_anchors, rule_gaps, rule_claims_registered,
                 rule_unsupported_ratio],
    "draft": [rule_all_sections_drafted, rule_drafts_cite_claims, rule_assumption_markers,
              rule_unregistered_refs, rule_abstract_limit, rule_section_limits, rule_required_modules_complete],
    "submission": [rule_scientific_scores, rule_no_critical_fixes, rule_compliance,
                   rule_unsupported_resolved, rule_hard_rules, rule_panel_score, rule_external_review_required],
    "external_feedback": [rule_feedback_open, rule_feedback_statuses, rule_feedback_stale],
}

NEXT_STEP = {
    "scope": "research",
    "evidence": "write-proposal",
    "draft": "review",
    "submission": "export",
    "external_feedback": "submission gate",
}


def normalize_gate(name: str) -> str:
    return name.replace("-", "_")


def load_callspec(graph: Graph) -> CallSpec | None:
    node = graph.callspec_node()
    if node is None:
        return None
    try:
        return CallSpec.model_validate(node.data)
    except Exception:  # pragma: no cover - corrupt spec
        return None


def evaluate_gate(gate: str, graph: Graph, thresholds: dict[str, float] | None = None,
                  callspec: CallSpec | None = None, project: Any = None) -> GateResult:
    gate = normalize_gate(gate)
    if gate not in GATE_RULES:
        raise ValueError(f"unknown gate {gate!r}; expected one of {GATES}")
    if project is None and graph.project_id:
        project = graph.store.get_project(graph.project_id)
    ctx = GateContext(graph=graph, thresholds=resolve(thresholds), callspec=callspec or load_callspec(graph),
                      scope=ScopeConfig.load(project) if project is not None else None,
                      stages=dict(project.stages) if project is not None else {})
    criteria = [c for c in (rule(ctx) for rule in GATE_RULES[gate]) if c is not None]
    if gate == "external_feedback" and not criteria:
        return GateResult(gate_name=gate, passed=False, not_applicable=True,
                          recommendations=["No external review has been ingested yet."])
    passed = all(c.met for c in criteria)
    blockers = [c.criterion + (f" — {c.notes}" if c.notes else "") for c in criteria if not c.met]
    recs = [] if not passed else [f"Gate passed — next: {NEXT_STEP.get(gate, '')}"]
    return GateResult(gate_name=gate, passed=passed, criteria=criteria, blockers=blockers,
                      recommendations=recs)


class GatePolicy:
    """Binds thresholds (workspace + pack overrides) and records results on the project."""

    def __init__(self, store, thresholds: dict[str, float] | None = None):
        self.store = store
        self.thresholds = thresholds or {}

    def check(self, project_id: str, gate: str, write: bool = True,
              pack_thresholds: dict[str, float] | None = None) -> GateResult:
        graph = Graph(self.store, project_id)
        project = self.store.get_project(project_id)
        result = evaluate_gate(gate, graph, resolve(self.thresholds, pack_thresholds), project=project)
        if write and project is not None:
            entry = project.gates.setdefault(normalize_gate(gate), {})
            entry["passed"] = result.passed
            entry["checked_at"] = result.checked_at
            entry["not_applicable"] = result.not_applicable
            entry["blockers"] = result.blockers
            self.store.put_project(project)
        return result
