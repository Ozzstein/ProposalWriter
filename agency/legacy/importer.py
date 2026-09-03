"""One-time import of a legacy ``runs/{project}/`` directory into the graph."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from agency.domain.callspec import CallSpec, CriterionSpec, SectionSpec
from agency.domain.graph import EdgeType, NodeType
from agency.graph.repo import Graph
from agency.workspace import GATES, STAGES, Workspace

LEGACY_STAGE_MAP = {  # legacy state.json keys -> new stage names (identical today)
    s: s for s in STAGES
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _last_wins(entries: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    current: dict[str, dict[str, Any]] = {}
    for e in entries:
        k = e.get(key)
        if k:
            current[k] = e
    return list(current.values())


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


_SECTION_HEAD = re.compile(r"^#{1,3}\s+(?:Section\s+)?(\d+(?:\.\d+)*[a-z]?)\.?(?:\s+[—:–-]?\s*(.*))?$", re.I)


def outline_to_sections(outline_md: str) -> list[SectionSpec]:
    sections: list[SectionSpec] = []
    for line in outline_md.splitlines():
        m = _SECTION_HEAD.match(line.strip())
        if m:
            sid, title = m.group(1), (m.group(2) or "").strip() or f"Section {m.group(1)}"
            kind = "other"
            t = title.lower()
            if "abstract" in t or "summary" in t:
                kind = "abstract"
            elif "excellence" in t or "innovation" in t or "novelty" in t:
                kind = "excellence"
            elif "impact" in t:
                kind = "impact"
            elif "implementation" in t or "work plan" in t or "approach" in t or "method" in t:
                kind = "implementation"
            elif "financ" in t or "budget" in t or "cost" in t:
                kind = "financial"
            elif "business plan" in t:
                kind = "business_plan"
            sections.append(SectionSpec(id=sid, title=title, kind=kind))
    return sections


def callspec_from_legacy(project_id: str, brief: dict[str, Any] | None, matrix: dict[str, Any] | None,
                         outline_md: str) -> CallSpec | None:
    if not brief and not matrix and not outline_md:
        return None
    brief = brief or {}
    sections = outline_to_sections(outline_md)
    criteria: list[CriterionSpec] = []
    rows = (matrix or {}).get("criteria") or (matrix or {}).get("evaluation_criteria") or []
    for i, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            continue
        criteria.append(CriterionSpec(
            id=str(row.get("criterion_id") or row.get("id") or f"C{i}"),
            name=str(row.get("name") or row.get("criterion") or f"Criterion {i}"),
            text=str(row.get("description") or row.get("text") or ""),
            max_score=float(row.get("max_score") or 5),
            weight=float(row.get("weight") or 1),
            threshold=row.get("threshold"),
        ))
    return CallSpec(
        call_id=str(brief.get("call_id") or brief.get("call_topic") or brief.get("title") or project_id),
        title=str(brief.get("title") or brief.get("call_name") or "Imported call"),
        funder=str(brief.get("funder") or brief.get("funding_agency") or "unknown"),
        programme=brief.get("programme"),
        instrument=brief.get("instrument") or brief.get("mechanism"),
        deadline=brief.get("deadline"),
        summary=str(brief.get("summary") or ""),
        sections=sections,
        criteria=criteria,
        abstract_word_limit=next((brief[k] for k in ("abstract_word_limit", "summary_word_limit")
                                  if isinstance(brief.get(k), int)), None),
    )


def import_legacy_project(ws: Workspace, project_dir: Path, project_id: str | None = None) -> dict[str, int]:
    project_dir = Path(project_dir)
    state = _load_json(project_dir / "state.json") or {}
    pid = project_id or state.get("project_name") or project_dir.name
    if ws.get_project(pid):
        raise ValueError(f"project '{pid}' already exists in the workspace")
    context_md = (project_dir / "context.md").read_text() if (project_dir / "context.md").exists() else None
    hypothesis = None
    if context_md:
        m = re.search(r"##\s*Hypothesis\s*\n+(.+?)(?:\n#|\Z)", context_md, re.S)
        if m and "_To be completed._" not in m.group(1):
            hypothesis = m.group(1).strip()
    project = ws.create_project(pid, project_id=pid, funder=state.get("funding_agency"),
                                mechanism=state.get("mechanism"), context_md=context_md,
                                hypothesis=hypothesis)
    for stage, entry in (state.get("stages") or {}).items():
        if stage in LEGACY_STAGE_MAP and isinstance(entry, dict) and entry.get("status"):
            project.stages[LEGACY_STAGE_MAP[stage]] = dict(entry)
    for gate, entry in (state.get("gates") or {}).items():
        g = gate.replace("-", "_")
        if g in GATES and isinstance(entry, dict):
            project.gates[g] = dict(entry)
    ws.store.put_project(project)

    graph = ws.graph(pid)
    counts: dict[str, int] = {}
    mem = project_dir / "memory"
    inter = project_dir / "intermediate"

    def bump(key: str) -> None:
        counts[key] = counts.get(key, 0) + 1

    # sources
    for e in _last_wins(_read_jsonl(mem / "evidence_store.jsonl"), "source_id"):
        e.setdefault("title", e.get("source_id", "untitled"))
        e.setdefault("extract", "")
        if e.get("type") not in ("paper", "patent", "standard", "internal", "report", "review", "web", "dataset"):
            e["type"] = "paper"
        if e.get("quality") not in ("low", "medium", "high"):
            e["quality"] = "medium"
        graph.add(NodeType.SOURCE, e, id=e["source_id"], created_by="import")
        bump("Source")
    # claims
    for e in _last_wins(_read_jsonl(mem / "claim_registry.jsonl"), "claim_id"):
        if e.get("type") not in ("technical_benefit", "scientific_finding", "impact_statement",
                                 "methodology_claim", "novelty_claim", "assumption", "financial"):
            e["type"] = "scientific_finding"
        if e.get("status") not in ("supported", "assumption", "unsupported", "disputed"):
            e["status"] = "unsupported"
        node = graph.add(NodeType.CLAIM, e, id=e["claim_id"], created_by="import")
        for sid in e.get("supported_by", []) or []:
            if graph.get(sid):
                graph.link(node, sid, EdgeType.SUPPORTED_BY, created_by="import")
        bump("Claim")
    # decisions
    for e in _last_wins(_read_jsonl(mem / "decision_log.jsonl"), "decision_id"):
        e.setdefault("rationale", [])
        e.setdefault("question", e.get("decision", ""))
        graph.add(NodeType.DECISION, e, id=e["decision_id"], created_by="import")
        bump("Decision")
    # feedback
    for e in _last_wins(_read_jsonl(mem / "feedback_log.jsonl"), "feedback_id"):
        try:
            graph.add(NodeType.FEEDBACK, e, id=e["feedback_id"], created_by="import")
            bump("Feedback")
        except Exception:
            continue
    # documents
    for kind, fname in (("sota_summary", "sota_summary.md"), ("outline", "proposal_outline.md"),
                        ("figures_register", "figures_register.md"), ("revision_plan", "revision_plan.md")):
        for base in (inter, project_dir / "drafts", project_dir / "reviews"):
            p = base / fname
            if p.exists():
                graph.put_document(kind, fname, p.read_text(), created_by="import")
                bump("Document")
                break
    # call spec
    brief = _load_json(inter / "call_brief.json")
    matrix = _load_json(inter / "evaluation_matrix.json")
    outline_md = (inter / "proposal_outline.md").read_text() if (inter / "proposal_outline.md").exists() else ""
    spec = callspec_from_legacy(pid, brief if isinstance(brief, dict) else None,
                                matrix if isinstance(matrix, dict) else None, outline_md)
    if spec:
        spec_node = graph.add(NodeType.CALL_SPEC, spec.model_dump(mode="json"), created_by="import")
        for c in spec.criteria:
            cn = graph.add(NodeType.CRITERION, c.model_dump(mode="json"), id=f"CRIT-{c.id}", created_by="import")
            graph.link(cn, spec_node, EdgeType.PART_OF)
        bump("CallSpec")
    # novelty map / gaps
    nov = _load_json(inter / "novelty_map.json")
    if isinstance(nov, dict):
        for a in nov.get("novelty_anchors", []):
            try:
                node = graph.add(NodeType.NOVELTY_ANCHOR, a, id=a.get("anchor_id"), created_by="import")
                for sid in a.get("supported_by", []):
                    if graph.get(sid):
                        graph.link(node, sid, EdgeType.EVIDENCE_OF)
                bump("NoveltyAnchor")
            except Exception:
                continue
    gaps = _load_json(inter / "gap_analysis.json")
    if isinstance(gaps, dict):
        top = {gid: i + 1 for i, gid in enumerate(gaps.get("top_gaps_for_proposal", []))}
        for g in gaps.get("gaps", []):
            try:
                if g.get("gap_id") in top:
                    g["priority_rank"] = top[g["gap_id"]]
                node = graph.add(NodeType.GAP, g, id=g.get("gap_id"), created_by="import")
                for sid in g.get("evidence_of_gap", []):
                    if graph.get(sid):
                        graph.link(node, sid, EdgeType.EVIDENCE_OF)
                bump("Gap")
            except Exception:
                continue
    # drafts
    ddir = project_dir / "drafts"
    if ddir.is_dir():
        for md in sorted(ddir.glob("*.md")):
            if md.name in ("figures_register.md",):
                continue
            text = md.read_text()
            m = re.match(r"^(\d+(?:_\d+)*)", md.stem)
            section_id = ".".join(str(int(x)) for x in m.group(1).split("_")) if m else md.stem
            title = next((ln.lstrip("# ").strip() for ln in text.splitlines() if ln.startswith("#")), md.stem)
            meta = _load_json(md.with_name(md.stem + "_meta.json")) or {}
            data = {"section_id": section_id, "section_name": meta.get("section_name", title),
                    "draft_text": text, "claim_ids": meta.get("claim_ids", sorted(graph.claim_refs(text))),
                    "source_ids": meta.get("source_ids", []), "kind": "abstract" if "abstract" in md.stem.lower() else "other",
                    "path": str(md.relative_to(project_dir))}
            node = graph.add(NodeType.SECTION, data, id=f"SEC-{section_id}", status="draft", created_by="import")
            for cid in data["claim_ids"]:
                if graph.get(cid):
                    graph.link(node, cid, EdgeType.CITES)
            bump("Section")
    # reviews
    rdir = project_dir / "reviews"
    if rdir.is_dir():
        for rj in sorted(rdir.glob("*.json")):
            data = _load_json(rj)
            if data is None:
                continue
            if isinstance(data, dict) and "criterion_scores" in data:
                graph.add(NodeType.PANEL_SCORE, {**data, "iteration": 1}, created_by="import")
                bump("PanelScore")
                continue
            reports = data if isinstance(data, list) else data.get("sections", [data]) if isinstance(data, dict) else []
            for r in reports:
                if not isinstance(r, dict) or "section_name" not in r:
                    continue
                r.setdefault("reviewer_type", "scientific" if rj.name.startswith("scientific") else
                             "compliance" if rj.name.startswith("compliance") else "scientific")
                r.setdefault("round", 1)
                r.setdefault("major_issues", [])
                r.setdefault("fixes", [])
                r.setdefault("overall_score", 0)
                node = graph.add(NodeType.REVIEW_FINDING, r, created_by="import")
                sec = next((s for s in graph.sections() if s.data.get("section_name") == r["section_name"]), None)
                if sec:
                    graph.link(node, sec, EdgeType.FOUND_IN)
                bump("ReviewFinding")
    # inputs -> blobs
    idir = project_dir / "inputs"
    if idir.is_dir():
        for f in idir.rglob("*"):
            if f.is_file():
                key = ws.blobs.put_file(f)
                graph.add(NodeType.DOCUMENT, {"kind": "input", "title": f.name, "path": key,
                                              "relative": str(f.relative_to(idir))}, created_by="import")
                bump("Input")
    ws.events.emit("project:imported", project_id=pid, counts=counts)
    return counts
