"""Workspace facade: config + store + blobs + events + project lifecycle."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agency.config import WorkspaceConfig, load_config
from agency.domain.graph import NodeType
from agency.domain.runs import Project
from agency.events.log import EventLog
from agency.graph.repo import Graph
from agency.policy.gates import GatePolicy, GateResult, normalize_gate
from agency.store.blobs import LocalBlobStore
from agency.store.sqlite import SqlStore

STAGES = ["ideation", "call_parsing", "research", "writing", "finance", "figures",
          "business_plan", "review", "external_review", "export"]
OPTIONAL_STAGES = {"ideation", "finance", "figures", "business_plan", "external_review"}
STAGE_STATUSES = ("pending", "in_progress", "complete", "skipped", "failed")
GATES = ["scope", "evidence", "draft", "submission", "external_feedback"]

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    return _SLUG_RE.sub("-", name.lower()).strip("-") or "project"


class Workspace:
    def __init__(self, config: WorkspaceConfig):
        self.config = config
        config.ensure_dirs()
        self.store = SqlStore(config.db_url)
        self.blobs = LocalBlobStore(config.blobs_dir)
        self.events = EventLog(self.store)
        self.gates = GatePolicy(self.store, config.gate_thresholds)

    @classmethod
    def open(cls, root: str | Path | None = None) -> "Workspace":
        return cls(load_config(root))

    def close(self) -> None:
        self.store.close()

    # ------------------------------------------------------------ projects
    def graph(self, project_id: str | None) -> Graph:
        return Graph(self.store, project_id)

    def create_project(self, name: str, *, funder: str | None = None, mechanism: str | None = None,
                       topic: str | None = None, deadline: str | None = None,
                       hypothesis: str | None = None, context_md: str | None = None,
                       project_id: str | None = None, settings: dict[str, Any] | None = None) -> Project:
        pid = project_id or slugify(name)
        if self.store.get_project(pid):
            raise ValueError(f"project '{pid}' already exists")
        project = Project(
            id=pid, name=name, funder=funder, mechanism=mechanism, topic=topic, deadline=deadline,
            stages={s: {"status": "pending"} for s in STAGES},
            gates={g: {"passed": False} for g in GATES},
            settings=settings or {},
        )
        self.store.put_project(project)
        body = context_md or _default_context(project, hypothesis)
        self.graph(pid).put_document("context", f"{name} — research context", body,
                                     hypothesis=hypothesis or "")
        self.config.project_dir(pid)
        self.events.emit("project:created", project_id=pid, name=name, funder=funder)
        return project

    def get_project(self, project_id: str) -> Project | None:
        return self.store.get_project(project_id)

    def require_project(self, project_id: str) -> Project:
        p = self.store.get_project(project_id)
        if p is None:
            raise KeyError(f"project '{project_id}' not found")
        return p

    def list_projects(self) -> list[Project]:
        return self.store.list_projects()

    def set_stage(self, project_id: str, stage: str, status: str, note: str | None = None) -> Project:
        if status not in STAGE_STATUSES:
            raise ValueError(f"status must be one of {STAGE_STATUSES}")
        project = self.require_project(project_id)
        entry = project.stages.setdefault(stage, {})
        entry["status"] = status
        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
        if note:
            entry["note"] = note
        self.store.put_project(project)
        self.events.emit("stage:status", project_id=project_id, stage=stage, status=status)
        return project

    def current_stage(self, project: Project) -> str:
        for s in STAGES:
            st = project.stages.get(s, {}).get("status", "pending")
            if st in ("pending", "in_progress", "failed"):
                return s
        return "done"

    def check_gate(self, project_id: str, gate: str, write: bool = True) -> GateResult:
        self.require_project(project_id)
        result = self.gates.check(project_id, gate, write=write)
        self.events.emit("gate:result", project_id=project_id, gate=normalize_gate(gate),
                         passed=result.passed, blockers=result.blockers,
                         not_applicable=result.not_applicable)
        return result

    def status(self, project_id: str) -> dict[str, Any]:
        project = self.require_project(project_id)
        graph = self.graph(project_id)
        pending = self.store.list_inbox(project_id=project_id, status="pending")
        runs = self.store.list_runs(project_id=project_id)
        return {
            "project": project.model_dump(mode="json"),
            "current_stage": self.current_stage(project),
            "graph": graph.summary(),
            "cost_usd": round(self.store.sum_cost(project_id), 4),
            "pending_inbox": len(pending),
            "runs": [{"id": r.id, "stage": r.stage, "status": r.status.value,
                      "cost_usd": r.cost_usd} for r in runs[:10]],
            "next_step": self.next_step(project_id),
        }

    def next_step(self, project_id: str) -> dict[str, Any]:
        from agency.policy.guide import next_step
        return next_step(self, project_id)

    def set_requirement_status(self, project_id: str, requirement_id: str, status: str, note: str = "") -> dict[str, Any]:
        """Confirm a parsed requirement (met / unmet / not_applicable); gates read it from the CallSpec."""
        if status not in ("met", "unmet", "not_applicable", "unknown"):
            raise ValueError(f"invalid status {status!r}")
        graph = self.graph(project_id)
        node = graph.callspec_node()
        if node is None:
            raise KeyError("no call spec parsed yet")
        reqs = node.data.get("requirements", [])
        target = next((r for r in reqs if r.get("id") == requirement_id), None)
        if target is None:
            raise KeyError(f"unknown requirement {requirement_id!r}")
        target["status"] = status
        graph.store.put_node(node)
        graph.add(NodeType.DECISION, {"question": f"Requirement {requirement_id}: {target.get('text', '')[:160]}",
                                      "decision": status, "rationale": [note or "confirmed by the researcher"],
                                      "evidence_refs": [requirement_id], "type": "requirement_status",
                                      "date": datetime.now(timezone.utc).date().isoformat()})
        self.events.emit("requirement:status", project_id=project_id, requirement_id=requirement_id, status=status)
        return dict(target)

    def context_document(self, project_id: str):
        return self.graph(project_id).document("context")


def _default_context(project: Project, hypothesis: str | None) -> str:
    lines = [f"# {project.name} — Research Context", ""]
    if project.funder:
        lines.append(f"**Funding agency**: {project.funder}")
    if project.mechanism:
        lines.append(f"**Mechanism**: {project.mechanism}")
    if project.topic:
        lines.append(f"**Topic**: {project.topic}")
    if project.deadline:
        lines.append(f"**Deadline**: {project.deadline}")
    lines += ["", "## Hypothesis", "", hypothesis or "_To be completed._", ""]
    return "\n".join(lines)
