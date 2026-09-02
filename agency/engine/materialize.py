"""Materialise the graph as files for agents (graph -> project dir) and ingest
agent outputs back (files/structured results -> graph)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from agency.domain.callspec import CallSpec
from agency.domain.graph import EdgeType, NodeType
from agency.domain.models import (Claim, EvidenceResult, GapAnalysis, NoveltyMap, ReviewBatch,
                                  SectionDraft, Source)
from agency.graph.repo import Graph
from agency.store.blobs import BlobStore

SUBDIRS = ["inputs", "intermediate", "drafts", "reviews", "figures", "final", "memory", "scratch"]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40] or "section"


def section_filename(section_id: str, name: str) -> str:
    parts = [p for p in re.split(r"[.\s]", str(section_id)) if p]
    num = "_".join(_pad(p) for p in parts) or "00"
    return f"{num}_{_slug(name)}.md"


def _pad(part: str) -> str:
    m = re.match(r"^(\d+)([a-z]?)$", part)
    return f"{int(m.group(1)):02d}{m.group(2)}" if m else part


_STEM_ID = re.compile(r"^(\d+[a-z]?(?:_\d+[a-z]?)*)")


def section_id_from_stem(stem: str) -> str | None:
    """'04_1b_market' -> '4.1b'; 'abstract' -> None."""
    m = _STEM_ID.match(stem)
    if not m:
        return None
    out = []
    for part in m.group(1).split("_"):
        pm = re.match(r"^(\d+)([a-z]?)$", part)
        out.append(f"{int(pm.group(1))}{pm.group(2)}")
    return ".".join(out)


def materialize(graph: Graph, project_dir: Path, blobs: BlobStore | None = None) -> dict[str, int]:
    """Write a read-oriented mirror of the graph into the project directory."""
    project_dir = Path(project_dir)
    for sub in SUBDIRS:
        (project_dir / sub).mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    ctx = graph.document("context")
    if ctx:
        (project_dir / "context.md").write_text(ctx.data.get("body", ""))
    mem = project_dir / "memory"
    stores = {
        "evidence_store.jsonl": [{"source_id": n.id, **n.data} for n in graph.sources()],
        "claim_registry.jsonl": [{"claim_id": n.id, **n.data} for n in graph.claims()],
        "decision_log.jsonl": [{"decision_id": n.id, **n.data} for n in graph.nodes(NodeType.DECISION)],
        "feedback_log.jsonl": [{"feedback_id": n.id, **n.data} for n in graph.feedback()],
    }
    for fname, rows in stores.items():
        with open(mem / fname, "w") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        counts[fname] = len(rows)
    inter = project_dir / "intermediate"
    spec = graph.callspec_node()
    if spec:
        (inter / "call_spec.json").write_text(json.dumps(spec.data, indent=2, ensure_ascii=False))
        # legacy names many prompts still mention
        (inter / "call_brief.json").write_text(json.dumps({
            k: spec.data.get(k) for k in ("call_id", "title", "funder", "programme", "instrument", "deadline",
                                          "summary", "requirements", "annexes", "budget_rules",
                                          "abstract_word_limit", "total_page_limit")}, indent=2, default=str))
        (inter / "evaluation_matrix.json").write_text(json.dumps({"criteria": spec.data.get("criteria", [])}, indent=2))
    for kind, fname in (("sota_summary", "sota_summary.md"), ("outline", "proposal_outline.md"),
                        ("figures_register", "figures_register.md"), ("revision_plan", "revision_plan.md"),
                        ("financial_tables", "financial_tables.md"), ("ideation_notes", "ideation_notes.md")):
        doc = graph.document(kind)
        if doc:
            target = inter / fname if kind not in ("figures_register",) else project_dir / "drafts" / fname
            target.write_text(doc.data.get("body", ""))
    anchors = graph.anchors()
    if anchors:
        (inter / "novelty_map.json").write_text(json.dumps({
            "project_name": graph.project_id, "novelty_anchors": [{"anchor_id": a.id, **a.data} for a in anchors],
            "minimum_anchors_met": sum(1 for a in anchors if a.data.get("defensibility_score", 0) >= 6) >= 3,
            "weak_points": [a.id for a in anchors if a.data.get("confidence") == "low"]}, indent=2, default=str))
    gaps = graph.gaps()
    if gaps:
        ranked = sorted((g for g in gaps if g.data.get("priority_rank")), key=lambda g: g.data["priority_rank"])
        (inter / "gap_analysis.json").write_text(json.dumps({
            "project_name": graph.project_id, "gaps": [{"gap_id": g.id, **g.data} for g in gaps],
            "top_gaps_for_proposal": [g.id for g in ranked]}, indent=2, default=str))
    brief = graph.one(NodeType.IDEATION_BRIEF)
    if brief:
        (inter / "ideation_brief.json").write_text(json.dumps(brief.data, indent=2, default=str))
    for doc in graph.nodes(NodeType.DOCUMENT):
        if doc.data.get("kind") == "json" and doc.data.get("path"):
            (inter / doc.data["title"]).write_text(doc.data.get("body", ""))
    ddir = project_dir / "drafts"
    for s in graph.sections():
        fname = s.data.get("path") or section_filename(s.data.get("section_id", s.id), s.data.get("section_name", s.id))
        fname = Path(fname).name
        (ddir / fname).write_text(s.data.get("draft_text", ""))
        meta = {k: v for k, v in s.data.items() if k not in ("draft_text", "path")}
        (ddir / (Path(fname).stem + "_meta.json")).write_text(json.dumps(meta, indent=2, default=str))
        counts["drafts"] = counts.get("drafts", 0) + 1
    rdir = project_dir / "reviews"
    by_type: dict[str, list[dict[str, Any]]] = {}
    for f in graph.findings():
        by_type.setdefault(f.data.get("reviewer_type", "review"), []).append({"finding_id": f.id, **f.data})
    for rtype, rows in by_type.items():
        (rdir / f"{rtype}_review.json").write_text(json.dumps({"sections": rows}, indent=2, default=str))
    panel = graph.latest_panel()
    if panel:
        (rdir / "evaluator_simulation.json").write_text(json.dumps(panel.data, indent=2, default=str))
    if blobs is not None:
        for doc in graph.nodes(NodeType.DOCUMENT):
            if doc.data.get("kind") == "input" and doc.data.get("path") and blobs.exists(doc.data["path"]):
                target = project_dir / "inputs" / (doc.data.get("relative") or doc.data["title"])
                if not target.exists():
                    blobs.copy_to(doc.data["path"], target)
                counts["inputs"] = counts.get("inputs", 0) + 1
    return counts


# ------------------------------------------------------------------ ingestion

def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def ingest_evidence(graph: Graph, result: EvidenceResult, *, retrieved_by: str, job_id: str,
                    id_range: tuple[int, int] | None = None) -> dict[str, list[str]]:
    """Persist sources (deduped by DOI/title) and candidate claims. Returns ids by kind."""
    existing = graph.sources()
    by_doi = {n.data.get("doi", "").lower(): n for n in existing if n.data.get("doi")}
    by_title = {_norm_title(n.data.get("title", "")): n for n in existing}
    out: dict[str, list[str]] = {"sources": [], "duplicates": [], "claims": []}
    id_map: dict[str, str] = {}
    for src in result.sources:
        doi = (src.doi or "").lower()
        dup = by_doi.get(doi) if doi else None
        dup = dup or by_title.get(_norm_title(src.title))
        if dup is not None:
            id_map[src.source_id or ""] = dup.id
            out["duplicates"].append(dup.id)
            continue
        data = src.model_dump(mode="json", exclude_none=True)
        data["retrieved_by"] = retrieved_by
        requested = data.pop("source_id", None)
        node_id = None
        if requested and id_range and _in_range(requested, id_range) and graph.get(requested) is None:
            node_id = requested
        node = graph.add(NodeType.SOURCE, data, id=node_id, created_by=job_id)
        if requested:
            id_map[requested] = node.id
        by_title[_norm_title(src.title)] = node
        if doi:
            by_doi[doi] = node
        out["sources"].append(node.id)
    for cand in result.claims:
        refs = [id_map.get(s, s) for s in cand.source_ids]
        refs = [r for r in refs if graph.get(r)]
        claim = Claim(text=cand.claim_text, type="scientific_finding",
                      status="supported" if refs else "unsupported", supported_by=refs, owner_agent=retrieved_by)
        node = graph.add(NodeType.CLAIM, claim, created_by=job_id)
        for r in refs:
            graph.link(node, r, EdgeType.SUPPORTED_BY, created_by=job_id)
        out["claims"].append(node.id)
    return out


def _in_range(node_id: str, rng: tuple[int, int]) -> bool:
    m = re.search(r"-(\d+)$", node_id)
    return bool(m) and rng[0] <= int(m.group(1)) <= rng[1]


def ingest_claims(graph: Graph, claims: list[Claim], *, owner: str, job_id: str) -> list[str]:
    ids = []
    for c in claims:
        data = c.model_dump(mode="json", exclude_none=True)
        data.setdefault("owner_agent", owner)
        refs = [s for s in data.get("supported_by", []) if graph.get(s)]
        data["supported_by"] = refs
        if data.get("status") == "supported" and not refs:
            data["status"] = "unsupported"
        requested = data.pop("claim_id", None)
        node = graph.add(NodeType.CLAIM, data, id=requested if requested and graph.get(requested) is None else None,
                         created_by=job_id)
        for r in refs:
            graph.link(node, r, EdgeType.SUPPORTED_BY, created_by=job_id)
        ids.append(node.id)
    return ids


def ingest_novelty(graph: Graph, nm: NoveltyMap, *, job_id: str) -> list[str]:
    for old in graph.anchors():
        graph.set_status(old.id, "superseded")
    ids = []
    for a in nm.novelty_anchors:
        data = a.model_dump(mode="json", exclude_none=True)
        data.pop("anchor_id", None)
        data["novelty_summary"] = nm.novelty_summary
        node = graph.add(NodeType.NOVELTY_ANCHOR, data, created_by=job_id)
        for s in a.supported_by:
            if graph.get(s):
                graph.link(node, s, EdgeType.EVIDENCE_OF, created_by=job_id)
        for c in a.related_claims:
            if graph.get(c):
                graph.link(node, c, EdgeType.RELATES_TO, created_by=job_id)
        ids.append(node.id)
    graph.put_document("novelty_summary", "Novelty summary", nm.novelty_summary, created_by=job_id,
                       weak_points=nm.weak_points, minimum_anchors_met=nm.minimum_anchors_met)
    return ids


def ingest_gaps(graph: Graph, ga: GapAnalysis, *, job_id: str) -> list[str]:
    for old in graph.gaps():
        graph.set_status(old.id, "superseded")
    ranks = {gid: i + 1 for i, gid in enumerate(ga.top_gaps_for_proposal)}
    ids = []
    for g in ga.gaps:
        data = g.model_dump(mode="json", exclude_none=True)
        requested = data.pop("gap_id", None)
        if requested in ranks:
            data["priority_rank"] = ranks[requested]
        node = graph.add(NodeType.GAP, data, created_by=job_id)
        for s in g.evidence_of_gap:
            if graph.get(s):
                graph.link(node, s, EdgeType.EVIDENCE_OF, created_by=job_id)
        ids.append(node.id)
    graph.put_document("gap_summary", "Gap landscape", ga.gap_landscape_summary, created_by=job_id,
                       criterion_gap_mapping=ga.criterion_gap_mapping)
    return ids


def ingest_callspec(graph: Graph, spec: CallSpec, *, job_id: str) -> str:
    for old in graph.nodes(NodeType.CALL_SPEC):
        graph.set_status(old.id, "superseded")
    for old in graph.nodes(NodeType.CRITERION) + graph.nodes(NodeType.REQUIREMENT):
        graph.set_status(old.id, "superseded")
    node = graph.add(NodeType.CALL_SPEC, spec.model_dump(mode="json"), created_by=job_id)
    for c in spec.criteria:
        cn = graph.add(NodeType.CRITERION, c.model_dump(mode="json"), id=f"CRIT-{c.id}", created_by=job_id)
        graph.link(cn, node, EdgeType.PART_OF, created_by=job_id)
    for r in spec.requirements:
        rn = graph.add(NodeType.REQUIREMENT, r.model_dump(mode="json"), id=f"REQ-{r.id}", created_by=job_id)
        graph.link(rn, node, EdgeType.PART_OF, created_by=job_id)
    return node.id


def ingest_drafts(graph: Graph, project_dir: Path, *, job_id: str, section_ids: list[str] | None = None,
                  callspec: CallSpec | None = None) -> list[str]:
    """Read drafts/*.md (+ _meta.json) written by a writer and upsert Section nodes."""
    ddir = Path(project_dir) / "drafts"
    ids: list[str] = []
    if not ddir.is_dir():
        return ids
    known = {s.data.get("section_id"): s for s in graph.sections()}
    for md in sorted(ddir.glob("*.md")):
        if md.name == "figures_register.md":
            continue
        section_id = section_id_from_stem(md.stem) or ("0" if "abstract" in md.stem.lower() else md.stem)
        if section_ids and section_id not in section_ids:
            continue
        text = md.read_text()
        meta_path = md.with_name(md.stem + "_meta.json")
        meta: dict[str, Any] = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
            except json.JSONDecodeError:
                meta = {}
        title = meta.get("section_name") or next((ln.lstrip("# ").strip() for ln in text.splitlines()
                                                  if ln.startswith("#")), md.stem)
        spec_sec = callspec.section(section_id) if callspec else None
        draft = SectionDraft(section_name=title, draft_text=text,
                             claim_ids=meta.get("claim_ids") or sorted(graph.claim_refs(text)),
                             source_ids=meta.get("source_ids") or sorted(graph.source_refs(text)),
                             assumptions_used=meta.get("assumptions_used", []),
                             open_issues=meta.get("open_issues", []), word_count=len(text.split()))
        data = draft.model_dump(mode="json", exclude_none=True)
        data.update({"section_id": section_id, "path": md.name,
                     "kind": (spec_sec.kind if spec_sec else meta.get("kind", "other"))})
        existing = known.get(section_id)
        if existing:
            existing.data.update(data)
            existing.status = "draft"
            existing.created_by = job_id
            node = graph.store.put_node(existing)
        else:
            node = graph.add(NodeType.SECTION, data, id=f"SEC-{section_id}", status="draft", created_by=job_id)
        for cid in data["claim_ids"]:
            if graph.get(cid):
                graph.link(node, cid, EdgeType.CITES, created_by=job_id)
        if spec_sec:
            for crit in spec_sec.criterion_ids:
                if graph.get(f"CRIT-{crit}"):
                    graph.link(node, f"CRIT-{crit}", EdgeType.ADDRESSES, created_by=job_id)
        ids.append(node.id)
    return ids


def ingest_reviews(graph: Graph, batch: ReviewBatch, *, reviewer_type: str, round_no: int, job_id: str) -> list[str]:
    ids = []
    sections = {s.data.get("section_name"): s for s in graph.sections()}
    for r in batch.sections:
        data = r.model_dump(mode="json", exclude_none=True)
        data["reviewer_type"] = data.get("reviewer_type") or reviewer_type
        data["round"] = round_no
        for fx in data.get("fixes", []):
            fx.setdefault("status", "open")
        node = graph.add(NodeType.REVIEW_FINDING, data, created_by=job_id)
        sec = sections.get(r.section_name)
        if sec:
            graph.link(node, sec, EdgeType.FOUND_IN, created_by=job_id)
        ids.append(node.id)
    return ids
