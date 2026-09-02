"""Cross-project knowledge base: workspace-scope nodes promoted from finished projects.

Promotion is deterministic (dedupe by DOI / normalised title / normalised claim
text). New projects import matching knowledge at research time with provenance
edges back to the workspace node. A markdown vault export keeps the Obsidian
workflow the previous system used.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agency.domain.graph import Edge, EdgeType, Node, NodeType, Scope
from agency.domain.ids import CLAIM_REF_RE, SOURCE_REF_RE
from agency.graph.repo import Graph
from agency.workspace import Workspace

PROMOTED_TYPES = [NodeType.SOURCE, NodeType.CLAIM, NodeType.GAP, NodeType.NOVELTY_ANCHOR, NodeType.CALL_SPEC,
                  NodeType.ENTITY, NodeType.CONCEPT]
KB_PREFIX = {NodeType.SOURCE: "WIKI-SRC", NodeType.CLAIM: "WIKI-CLM", NodeType.GAP: "WIKI-GAP",
             NodeType.NOVELTY_ANCHOR: "WIKI-NOV", NodeType.CALL_SPEC: "WIKI-CALL", NodeType.ENTITY: "WIKI-ENT",
             NodeType.CONCEPT: "WIKI-CPT"}
STOP = {"the", "a", "an", "of", "for", "and", "or", "in", "on", "to", "with", "by", "at", "from", "is", "are",
        "that", "this", "as", "be", "we", "our", "it", "its", "into", "via", "using", "based"}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _tokens(text: str) -> set[str]:
    return {t for t in _norm(text).split() if len(t) > 2 and t not in STOP}


def kb_graph(ws: Workspace) -> Graph:
    return Graph(ws.store, None)


# ------------------------------------------------------------------ promotion

def promote_project(ws: Workspace, project_id: str, *, job_id: str = "kb_promote") -> dict[str, int]:
    """Copy this project's durable knowledge into workspace scope (idempotent)."""
    project = ws.require_project(project_id)
    src = ws.graph(project_id)
    kb = kb_graph(ws)
    counts: dict[str, int] = {"promoted": 0, "linked": 0, "skipped": 0}
    existing_sources = kb.nodes(NodeType.SOURCE)
    by_doi = {n.data.get("doi", "").lower(): n for n in existing_sources if n.data.get("doi")}
    by_title = {_norm(n.data.get("title", "")): n for n in existing_sources}
    id_map: dict[str, str] = {}

    def link_promoted(local: Node, remote: Node) -> None:
        ws.store.add_edge(Edge(src=local.id, dst=remote.id, type=EdgeType.PROMOTED_TO, created_by=job_id,
                               data={"project_id": project_id}), project_id)
        id_map[local.id] = remote.id
        counts["linked"] += 1

    # sources
    for n in src.sources():
        if src.out_edges(n.id, EdgeType.PROMOTED_TO):
            id_map[n.id] = src.out_edges(n.id, EdgeType.PROMOTED_TO)[0].dst
            counts["skipped"] += 1
            continue
        doi = (n.data.get("doi") or "").lower()
        dup = by_doi.get(doi) if doi else None
        dup = dup or by_title.get(_norm(n.data.get("title", "")))
        if dup is None:
            data = {k: v for k, v in n.data.items() if k != "source_id"}
            data["origin_project"] = project_id
            data["origin_id"] = n.id
            dup = _add_ws(ws, NodeType.SOURCE, data, job_id)
            by_title[_norm(n.data.get("title", ""))] = dup
            if doi:
                by_doi[doi] = dup
            counts["promoted"] += 1
        link_promoted(n, dup)
    # claims (supported only) -> remap supported_by to workspace source ids
    existing_claims = {_norm(n.data.get("text", "")): n for n in kb.nodes(NodeType.CLAIM)}
    for n in src.claims():
        if n.data.get("status") != "supported" or n.status != "active":
            counts["skipped"] += 1
            continue
        if src.out_edges(n.id, EdgeType.PROMOTED_TO):
            continue
        key = _norm(n.data.get("text", ""))
        dup = existing_claims.get(key)
        if dup is None:
            data = {k: v for k, v in n.data.items() if k != "claim_id"}
            data["supported_by"] = [id_map.get(s, s) for s in n.data.get("supported_by", []) if s in id_map]
            data["origin_project"], data["origin_id"] = project_id, n.id
            dup = _add_ws(ws, NodeType.CLAIM, data, job_id)
            for s in data["supported_by"]:
                ws.store.add_edge(Edge(src=dup.id, dst=s, type=EdgeType.SUPPORTED_BY, created_by=job_id), None)
            existing_claims[key] = dup
            counts["promoted"] += 1
        link_promoted(n, dup)
    # gaps and anchors (active only)
    for ntype, text_key in ((NodeType.GAP, "description"), (NodeType.NOVELTY_ANCHOR, "claim")):
        existing = {_norm(n.data.get(text_key, "")): n for n in kb.nodes(ntype)}
        for n in src.nodes(ntype, status="active"):
            if src.out_edges(n.id, EdgeType.PROMOTED_TO):
                continue
            key = _norm(n.data.get(text_key, ""))
            dup = existing.get(key)
            if dup is None:
                data = {k: v for k, v in n.data.items() if k not in ("gap_id", "anchor_id", "priority_rank")}
                for field in ("evidence_of_gap", "supported_by"):
                    if field in data:
                        data[field] = [id_map.get(s, s) for s in data[field] if s in id_map]
                data["origin_project"], data["origin_id"] = project_id, n.id
                dup = _add_ws(ws, ntype, data, job_id)
                existing[key] = dup
                counts["promoted"] += 1
            link_promoted(n, dup)
    # the parsed call as funding-call intelligence
    spec = src.callspec_node()
    if spec is not None:
        key = _norm(spec.data.get("call_id", ""))
        dup = next((n for n in kb.nodes(NodeType.CALL_SPEC) if _norm(n.data.get("call_id", "")) == key), None)
        if dup is None:
            data = dict(spec.data)
            data["origin_project"], data["origin_id"] = project_id, spec.id
            dup = _add_ws(ws, NodeType.CALL_SPEC, data, job_id)
            counts["promoted"] += 1
        if not src.out_edges(spec.id, EdgeType.PROMOTED_TO):
            link_promoted(spec, dup)
    # entities / concepts if the project produced any
    for ntype in (NodeType.ENTITY, NodeType.CONCEPT):
        existing = {_norm(n.data.get("name", "")): n for n in kb.nodes(ntype)}
        for n in src.nodes(ntype):
            key = _norm(n.data.get("name", ""))
            if key in existing or src.out_edges(n.id, EdgeType.PROMOTED_TO):
                continue
            data = dict(n.data)
            data["origin_project"], data["origin_id"] = project_id, n.id
            dup = _add_ws(ws, ntype, data, job_id)
            existing[key] = dup
            counts["promoted"] += 1
            link_promoted(n, dup)
    project.settings["kb_promoted_at"] = datetime.now(timezone.utc).isoformat()
    ws.store.put_project(project)
    ws.events.emit("kb:promoted", project_id=project_id, **counts)
    return counts


def _add_ws(ws: Workspace, ntype: NodeType, data: dict[str, Any], job_id: str) -> Node:
    prefix = KB_PREFIX[ntype]
    node_id = ws.store.next_ids(prefix, None, 1)[0]
    node = Node(id=node_id, type=ntype, scope=Scope.WORKSPACE, project_id=None, status="active",
                created_by=job_id, data=data)
    return ws.store.put_node(node)


# ------------------------------------------------------------------ import into a project

def import_relevant(ws: Workspace, project_id: str, topic: str, *, job_id: str, limit: int = 40,
                    min_overlap: int = 2) -> dict[str, Any]:
    """Copy workspace sources/claims/gaps whose text overlaps the topic into the project (with provenance)."""
    kb = kb_graph(ws)
    ws_nodes = kb.nodes(NodeType.SOURCE) + kb.nodes(NodeType.CLAIM) + kb.nodes(NodeType.GAP)
    if not ws_nodes:
        return {"sources": 0, "claims": 0, "gaps": 0, "candidates": 0}
    want = _tokens(topic)
    proj = ws.graph(project_id)
    already = {e.dst for e in proj.edges(EdgeType.DERIVED_FROM)}
    scored = []
    for n in ws_nodes:
        text = " ".join(str(v) for k, v in n.data.items() if k in ("title", "text", "extract", "description", "relevance_tags"))
        overlap = len(want & _tokens(text))
        if overlap >= min_overlap and n.id not in already:
            scored.append((overlap, n))
    scored.sort(key=lambda x: -x[0])
    counts = {"sources": 0, "claims": 0, "gaps": 0, "candidates": len(scored)}
    id_map: dict[str, str] = {}
    for _, n in scored[:limit]:
        if n.type == NodeType.SOURCE:
            data = dict(n.data)
            data.pop("source_id", None)
            data["imported_from"] = n.id
            local = proj.add(NodeType.SOURCE, data, created_by=job_id)
            id_map[n.id] = local.id
            counts["sources"] += 1
            proj.link(local, n, EdgeType.DERIVED_FROM, created_by=job_id)
    for _, n in scored[:limit]:
        if n.type in (NodeType.CLAIM, NodeType.GAP):
            data = dict(n.data)
            data.pop("claim_id", None)
            data.pop("gap_id", None)
            data["imported_from"] = n.id
            for field in ("supported_by", "evidence_of_gap"):
                if field in data:
                    data[field] = [id_map[s] for s in data[field] if s in id_map]
            if n.type == NodeType.GAP and not data.get("evidence_of_gap"):
                continue
            local = proj.add(n.type, data, created_by=job_id)
            proj.link(local, n, EdgeType.DERIVED_FROM, created_by=job_id)
            for s in data.get("supported_by", data.get("evidence_of_gap", [])):
                proj.link(local, s, EdgeType.SUPPORTED_BY if n.type == NodeType.CLAIM else EdgeType.EVIDENCE_OF, created_by=job_id)
            counts["claims" if n.type == NodeType.CLAIM else "gaps"] += 1
    ws.events.emit("kb:imported", project_id=project_id, **counts)
    return counts


# ------------------------------------------------------------------ query / status / lint

def status(ws: Workspace) -> dict[str, Any]:
    kb = kb_graph(ws)
    counts = {t.value: len(kb.nodes(t)) for t in PROMOTED_TYPES}
    projects = [p.id for p in ws.list_projects() if p.settings.get("kb_promoted_at")]
    return {"counts": counts, "promoted_projects": projects, "total": sum(counts.values())}


def query(ws: Workspace, question: str, limit: int = 20) -> dict[str, Any]:
    kb = kb_graph(ws)
    want = _tokens(question)
    hits = []
    for t in PROMOTED_TYPES:
        for n in kb.nodes(t):
            text = " ".join(str(v) for v in n.data.values() if isinstance(v, str))
            score = len(want & _tokens(text))
            if score:
                hits.append((score, n))
    hits.sort(key=lambda x: -x[0])
    return {"question": question, "hits": [{"id": n.id, "type": n.type.value, "score": s,
                                            "summary": (n.data.get("title") or n.data.get("text") or n.data.get("description") or n.data.get("claim") or "")[:200],
                                            "origin_project": n.data.get("origin_project")} for s, n in hits[:limit]]}


def lint(ws: Workspace, fix: bool = False) -> dict[str, Any]:
    kb = kb_graph(ws)
    problems: list[str] = []
    ids = {n.id for t in PROMOTED_TYPES for n in kb.nodes(t)}
    for n in kb.nodes(NodeType.CLAIM):
        refs = n.data.get("supported_by", [])
        missing = [r for r in refs if r not in ids]
        if missing:
            problems.append(f"{n.id}: supported_by references unknown {missing}")
            if fix:
                n.data["supported_by"] = [r for r in refs if r in ids]
                ws.store.put_node(n)
        if not refs:
            problems.append(f"{n.id}: promoted claim has no sources")
    for n in kb.nodes(NodeType.GAP):
        missing = [r for r in n.data.get("evidence_of_gap", []) if r not in ids]
        if missing:
            problems.append(f"{n.id}: evidence_of_gap references unknown {missing}")
    seen: dict[str, str] = {}
    for n in kb.nodes(NodeType.SOURCE):
        key = _norm(n.data.get("title", ""))
        if key in seen:
            problems.append(f"{n.id}: duplicate title of {seen[key]}")
        seen[key] = n.id
    # contradictions: same normalised claim text with different status/origin is fine; flag near-duplicates
    texts: dict[frozenset, str] = {}
    for n in kb.nodes(NodeType.CLAIM):
        toks = frozenset(_tokens(n.data.get("text", "")))
        for other_toks, other in texts.items():
            if toks and len(toks & other_toks) / max(1, len(toks | other_toks)) > 0.8:
                problems.append(f"{n.id}: near-duplicate of {other}")
                break
        texts[toks] = n.id
    return {"problems": problems, "ok": not problems, "fixed": fix}


# ------------------------------------------------------------------ vault export

_PAGE_DIR = {NodeType.SOURCE: "sources", NodeType.CLAIM: "claims", NodeType.GAP: "gaps", NodeType.NOVELTY_ANCHOR: "gaps",
             NodeType.CALL_SPEC: "funding-calls", NodeType.ENTITY: "entities", NodeType.CONCEPT: "concepts"}


def _fm(data: dict[str, Any]) -> str:
    lines = ["---"]
    for k, v in data.items():
        if v is None or v == "" or v == []:
            continue
        if isinstance(v, (list, tuple)):
            lines.append(f"{k}: [{', '.join(json.dumps(str(x)) for x in v)}]")
        else:
            lines.append(f"{k}: {json.dumps(v) if isinstance(v, str) else v}")
    lines.append("---")
    return "\n".join(lines)


def export_vault(ws: Workspace, out_dir: str | Path | None = None) -> dict[str, Any]:
    kb = kb_graph(ws)
    out = Path(out_dir) if out_dir else ws.config.root / "kb"
    for sub in set(_PAGE_DIR.values()):
        (out / "pages" / sub).mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir(exist_ok=True)
    index: dict[str, list[str]] = {}
    written = 0
    for t in PROMOTED_TYPES:
        for n in kb.nodes(t):
            d = n.data
            slug = n.id.lower()
            title = d.get("title") or d.get("text") or d.get("description") or d.get("claim") or d.get("name") or n.id
            fm = {"id": n.id, "type": t.value, "origin_project": d.get("origin_project"), "created": n.created_at.date().isoformat(),
                  "tags": d.get("relevance_tags") or d.get("tags") or [], "status": d.get("status"), "year": d.get("year"),
                  "doi": d.get("doi"), "quality": d.get("quality")}
            body = [_fm(fm), "", f"# {title[:120]}", ""]
            if t == NodeType.SOURCE:
                body += [f"**Authors**: {d.get('authors', '-')}  ", f"**Year**: {d.get('year', '-')}  ", f"**Type**: {d.get('type')}  ", "",
                         "## Key points", d.get("extract", ""), ""]
                if d.get("limitations"):
                    body += ["## Limitations", *[f"- {x}" for x in d["limitations"]], ""]
            elif t == NodeType.CLAIM:
                body += [d.get("text", ""), "", "## Evidence", *[f"- [[{s.lower()}]]" for s in d.get("supported_by", [])], ""]
            elif t in (NodeType.GAP, NodeType.NOVELTY_ANCHOR):
                body += [d.get("description") or d.get("claim", ""), "", "## Evidence",
                         *[f"- [[{s.lower()}]]" for s in d.get("evidence_of_gap", d.get("supported_by", []))], ""]
            elif t == NodeType.CALL_SPEC:
                body += [f"**Funder**: {d.get('funder')}  ", f"**Instrument**: {d.get('instrument')}  ", f"**Deadline**: {d.get('deadline')}  ", "",
                         "## Criteria", *[f"- {c.get('id')} {c.get('name')} (max {c.get('max_score')})" for c in d.get("criteria", [])], "",
                         "## Sections", *[f"- {s.get('id')}. {s.get('title')}" for s in d.get("sections", [])], ""]
            else:
                body += [d.get("description", ""), ""]
            (out / "pages" / _PAGE_DIR[t] / f"{slug}.md").write_text("\n".join(body))
            index.setdefault(_PAGE_DIR[t], []).append(f"- [[{slug}]] — {title[:80]}")
            written += 1
    idx = ["# Knowledge base index", "", f"Last updated: {datetime.now(timezone.utc).date().isoformat()}", ""]
    for sub, rows in sorted(index.items()):
        idx += [f"## {sub} ({len(rows)})", *rows, ""]
    (out / "index.md").write_text("\n".join(idx))
    wiki_md = ws.config.root.parent / "ProposalWriter" / "WIKI.md"
    if wiki_md.exists() and not (out / "WIKI.md").exists():
        (out / "WIKI.md").write_text(wiki_md.read_text())
    ws.events.emit("kb:exported", pages=written, path=str(out))
    return {"pages": written, "path": str(out)}


def kb_cli(ws: Workspace, action: str, arg: str | None) -> dict[str, Any]:
    if action == "status":
        return status(ws)
    if action == "promote":
        if not arg:
            raise SystemExit("usage: agency kb promote <project>")
        return promote_project(ws, arg)
    if action == "query":
        return query(ws, arg or "")
    if action == "lint":
        return lint(ws, fix=(arg == "--fix"))
    if action == "export":
        return export_vault(ws, arg)
    raise SystemExit(f"unknown kb action {action!r} (status|promote|query|lint|export)")
