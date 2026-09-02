"""Typed access to the proposal graph for one project (or the workspace)."""
from __future__ import annotations

from typing import Any, Iterable

from pydantic import BaseModel

from agency.domain.graph import Edge, EdgeType, Node, NodeType, Scope
from agency.domain.ids import CLAIM_REF_RE, SOURCE_REF_RE, parse_id
from agency.domain.models import PAYLOAD_BY_NODE_TYPE
from agency.store.base import Store

ID_FIELD_BY_TYPE = {
    NodeType.SOURCE: ("source_id", "SRC"),
    NodeType.CLAIM: ("claim_id", "CLM"),
    NodeType.GAP: ("gap_id", "GAP"),
    NodeType.NOVELTY_ANCHOR: ("anchor_id", "NOV"),
    NodeType.DECISION: ("decision_id", "DEC"),
    NodeType.FEEDBACK: ("feedback_id", "FBK"),
    NodeType.PATCH: ("patch_id", "PATCH"),
    NodeType.FIGURE: ("figure_id", "F"),
    NodeType.CRITERION: (None, "CRIT"),
    NodeType.REQUIREMENT: (None, "REQ"),
    NodeType.SECTION: (None, "SEC"),
    NodeType.REVIEW_FINDING: (None, "FND"),
    NodeType.PANEL_SCORE: (None, "SCR"),
    NodeType.ENTITY: (None, "ENT"),
    NodeType.CONCEPT: (None, "CPT"),
    NodeType.DOCUMENT: (None, "DOC"),
    NodeType.IDEATION_BRIEF: (None, "IDEA"),
    NodeType.CALL_SPEC: (None, "CALL"),
    NodeType.FINANCIAL_TABLE: (None, "FIN"),
}


def _as_dict(data: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(data, BaseModel):
        return data.model_dump(mode="json", exclude_none=True)
    return dict(data)


class Graph:
    def __init__(self, store: Store, project_id: str | None):
        self.store = store
        self.project_id = project_id

    # ------------------------------------------------------------ writes
    def allocate(self, prefix: str, n: int = 1) -> list[str]:
        return self.store.next_ids(prefix, self.project_id, n)

    def add(self, type: NodeType, data: BaseModel | dict[str, Any], *, id: str | None = None,
            status: str = "active", created_by: str | None = None,
            scope: Scope = Scope.PROJECT) -> Node:
        payload = _as_dict(data)
        id_field, prefix = ID_FIELD_BY_TYPE.get(type, (None, type.value.upper()[:4]))
        node_id = id or (payload.get(id_field) if id_field else None)
        if node_id:
            parsed = parse_id(node_id)
            if parsed and parsed[0] == prefix:
                self.store.bump_counter(prefix, self.project_id if scope == Scope.PROJECT else None,
                                        parsed[1] + 1)
        else:
            node_id = self.store.next_ids(prefix, self.project_id if scope == Scope.PROJECT else None, 1)[0]
        if id_field:
            payload[id_field] = node_id
        model = PAYLOAD_BY_NODE_TYPE.get(type.value)
        if model is not None:
            payload = model.model_validate(payload).model_dump(mode="json", exclude_none=True)
        node = Node(id=node_id, type=type, scope=scope,
                    project_id=self.project_id if scope == Scope.PROJECT else None,
                    status=status, created_by=created_by, data=payload)
        return self.store.put_node(node)

    def update(self, node: Node, **changes: Any) -> Node:
        node.data.update(changes)
        return self.store.put_node(node)

    def set_status(self, node_id: str, status: str) -> Node | None:
        node = self.store.get_node(node_id)
        if node is None:
            return None
        node.status = status
        return self.store.put_node(node)

    def link(self, src: str | Node, dst: str | Node, type: EdgeType, created_by: str | None = None,
             **data: Any) -> Edge:
        edge = Edge(src=src.id if isinstance(src, Node) else src,
                    dst=dst.id if isinstance(dst, Node) else dst,
                    type=type, created_by=created_by, data=data)
        self.store.add_edge(edge)
        return edge

    def put_document(self, kind: str, title: str, body: str, *, id: str | None = None,
                     created_by: str | None = None, **extra: Any) -> Node:
        existing = self.document(kind) if id is None else self.store.get_node(id)
        data = {"kind": kind, "title": title, "body": body, **extra}
        if existing:
            existing.data.update(data)
            existing.created_by = created_by or existing.created_by
            return self.store.put_node(existing)
        return self.add(NodeType.DOCUMENT, data, id=id, created_by=created_by)

    # ------------------------------------------------------------ reads
    def get(self, node_id: str) -> Node | None:
        return self.store.get_node(node_id)

    def nodes(self, type: NodeType, status: str | None = None,
              include_workspace: bool = False) -> list[Node]:
        out = self.store.list_nodes(project_id=self.project_id, type=type.value, status=status)
        if include_workspace:
            out += self.store.list_nodes(project_id=None, type=type.value, scope=Scope.WORKSPACE.value,
                                         status=status)
        return out

    def one(self, type: NodeType, **match: Any) -> Node | None:
        for n in self.nodes(type):
            if all(n.data.get(k) == v for k, v in match.items()):
                return n
        return None

    def document(self, kind: str) -> Node | None:
        return self.one(NodeType.DOCUMENT, kind=kind)

    def out(self, node_id: str, type: EdgeType | None = None) -> list[Node]:
        edges = self.store.edges_from(node_id, type.value if type else None)
        return self.store.get_nodes([e.dst for e in edges])

    def inn(self, node_id: str, type: EdgeType | None = None) -> list[Node]:
        edges = self.store.edges_to(node_id, type.value if type else None)
        return self.store.get_nodes([e.src for e in edges])

    def edges(self, type: EdgeType | None = None) -> list[Edge]:
        if self.project_id is None:
            return []
        return self.store.list_edges(self.project_id, type.value if type else None)

    # ------------------------------------------------------------ convenience
    def sources(self) -> list[Node]:
        return self.nodes(NodeType.SOURCE)

    def claims(self) -> list[Node]:
        return self.nodes(NodeType.CLAIM)

    def gaps(self) -> list[Node]:
        return self.nodes(NodeType.GAP)

    def anchors(self) -> list[Node]:
        return self.nodes(NodeType.NOVELTY_ANCHOR)

    def sections(self) -> list[Node]:
        return sorted(self.nodes(NodeType.SECTION), key=lambda n: _section_sort_key(n.data.get("section_id", n.id)))

    def section(self, section_id: str) -> Node | None:
        return self.one(NodeType.SECTION, section_id=section_id)

    def callspec_node(self) -> Node | None:
        specs = self.nodes(NodeType.CALL_SPEC)
        return specs[-1] if specs else None

    def findings(self, reviewer_type: str | None = None) -> list[Node]:
        out = self.nodes(NodeType.REVIEW_FINDING)
        if reviewer_type:
            out = [n for n in out if n.data.get("reviewer_type") == reviewer_type]
        return out

    def latest_panel(self) -> Node | None:
        scores = self.nodes(NodeType.PANEL_SCORE)
        return max(scores, key=lambda n: n.data.get("iteration", 0)) if scores else None

    def feedback(self) -> list[Node]:
        return self.nodes(NodeType.FEEDBACK)

    def decisions(self, type: str | None = None) -> list[Node]:
        out = self.nodes(NodeType.DECISION)
        return [d for d in out if type is None or d.data.get("type") == type]

    def unsupported_claims(self) -> list[Node]:
        return [c for c in self.claims() if c.data.get("status") == "unsupported"]

    def approved_unsupported(self) -> set[str]:
        approved: set[str] = set()
        for d in self.decisions("approve_unsupported_claim"):
            approved.update(d.data.get("evidence_refs", []))
            approved.update(CLAIM_REF_RE.findall(d.data.get("decision", "")))
        return approved

    def known_ids(self, prefix_re) -> set[str]:
        return {n.id for n in self.store.list_nodes(project_id=self.project_id)} | {
            n.id for n in self.store.list_nodes(project_id=None, scope=Scope.WORKSPACE.value)}

    def claim_refs(self, text: str) -> set[str]:
        return set(CLAIM_REF_RE.findall(text or ""))

    def source_refs(self, text: str) -> set[str]:
        return set(SOURCE_REF_RE.findall(text or ""))

    def unregistered_refs(self, text: str) -> set[str]:
        refs = self.claim_refs(text) | self.source_refs(text)
        if not refs:
            return set()
        found = {n.id for n in self.store.get_nodes(refs)}
        return refs - found

    def sections_citing(self, claim_id: str) -> list[Node]:
        return self.inn(claim_id, EdgeType.CITES)

    def coverage(self, criteria_ids: Iterable[str]) -> dict[str, list[str]]:
        out = {cid: [] for cid in criteria_ids}
        for e in self.edges(EdgeType.ADDRESSES):
            if e.dst in out:
                out[e.dst].append(e.src)
        return out

    def provenance(self, node_id: str, depth: int = 3) -> dict[str, Any]:
        seen: dict[str, Node] = {}
        edges: list[Edge] = []
        frontier = [node_id]
        for _ in range(depth):
            nxt = []
            for nid in frontier:
                if nid in seen:
                    continue
                node = self.store.get_node(nid)
                if node is None:
                    continue
                seen[nid] = node
                for e in self.store.edges_from(nid):
                    edges.append(e)
                    nxt.append(e.dst)
            frontier = nxt
        return {"nodes": list(seen.values()), "edges": edges}

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for n in self.store.list_nodes(project_id=self.project_id):
            counts[n.type.value] = counts.get(n.type.value, 0) + 1
        return counts


def _section_sort_key(section_id: str) -> tuple:
    parts = []
    for p in str(section_id).replace("_", ".").split("."):
        parts.append((0, int(p)) if p.isdigit() else (1, p))
    return tuple(parts)
