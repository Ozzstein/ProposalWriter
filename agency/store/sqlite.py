"""SQLAlchemy Core store. Works on SQLite today; the schema uses only
portable types so Postgres is a URL change plus a migration run."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Iterable

import sqlalchemy as sa
from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, Integer, MetaData, String,
                        Table, Text, UniqueConstraint, and_, create_engine, func, select)

from agency.domain.graph import Edge, Node
from agency.domain.ids import format_id
from agency.domain.runs import CostEntry, Event, InboxItem, Job, Project, Run

metadata = MetaData()

projects = Table(
    "projects", metadata,
    Column("id", String(128), primary_key=True),
    Column("created_at", DateTime(timezone=True)),
    Column("json", JSON, nullable=False),
)

WORKSPACE_KEY = "__workspace__"


def _pk(project_id: str | None) -> str:
    return project_id or WORKSPACE_KEY


nodes = Table(
    "nodes", metadata,
    Column("pkey", String(128), primary_key=True),
    Column("id", String(128), primary_key=True),
    Column("version", Integer, primary_key=True),
    Column("type", String(64), nullable=False, index=True),
    Column("scope", String(16), nullable=False, index=True),
    Column("project_id", String(128), index=True),
    Column("status", String(32), nullable=False, index=True),
    Column("created_by", String(128)),
    Column("created_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
    Column("is_current", Boolean, nullable=False, default=True, index=True),
    Column("text", Text),
    Column("json", JSON, nullable=False),
)

edges = Table(
    "edges", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("src", String(128), nullable=False, index=True),
    Column("dst", String(128), nullable=False, index=True),
    Column("type", String(64), nullable=False, index=True),
    Column("project_id", String(128), index=True),
    Column("pkey", String(128), nullable=False, index=True),
    Column("created_by", String(128)),
    Column("created_at", DateTime(timezone=True)),
    Column("json", JSON, nullable=False),
    UniqueConstraint("pkey", "src", "dst", "type", name="uq_edge"),
)

counters = Table(
    "counters", metadata,
    Column("prefix", String(32), primary_key=True),
    Column("project_id", String(128), primary_key=True),
    Column("next", Integer, nullable=False),
)

runs = Table(
    "runs", metadata,
    Column("id", String(64), primary_key=True),
    Column("project_id", String(128), index=True),
    Column("status", String(32), index=True),
    Column("created_at", DateTime(timezone=True)),
    Column("json", JSON, nullable=False),
)

jobs = Table(
    "jobs", metadata,
    Column("id", String(64), primary_key=True),
    Column("run_id", String(64), index=True),
    Column("status", String(32), index=True),
    Column("json", JSON, nullable=False),
)

inbox = Table(
    "inbox", metadata,
    Column("id", String(64), primary_key=True),
    Column("project_id", String(128), index=True),
    Column("run_id", String(64), index=True),
    Column("status", String(32), index=True),
    Column("created_at", DateTime(timezone=True)),
    Column("json", JSON, nullable=False),
)

events = Table(
    "events", metadata,
    Column("seq", Integer, primary_key=True, autoincrement=True),
    Column("ts", DateTime(timezone=True)),
    Column("project_id", String(128), index=True),
    Column("run_id", String(64), index=True),
    Column("kind", String(64), index=True),
    Column("json", JSON, nullable=False),
)

costs = Table(
    "costs", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("project_id", String(128), index=True),
    Column("run_id", String(64), index=True),
    Column("job_id", String(64)),
    Column("cost_usd", Float, nullable=False, default=0.0),
    Column("created_at", DateTime(timezone=True)),
    Column("json", JSON, nullable=False),
)


def _dump(model) -> dict[str, Any]:
    return json.loads(model.model_dump_json())


def _dt(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


class SqlStore:
    def __init__(self, url: str):
        self.url = url
        kwargs: dict[str, Any] = {"future": True}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
        self.engine = create_engine(url, **kwargs)
        if url.startswith("sqlite"):
            @sa.event.listens_for(self.engine, "connect")
            def _pragmas(dbapi_conn, _):  # pragma: no cover - trivial
                cur = dbapi_conn.cursor()
                cur.execute("PRAGMA journal_mode=WAL")
                cur.execute("PRAGMA foreign_keys=ON")
                cur.close()
        metadata.create_all(self.engine)

    # ------------------------------------------------------------ helpers
    def _one(self, stmt):
        with self.engine.begin() as c:
            return c.execute(stmt).first()

    def _all(self, stmt):
        with self.engine.begin() as c:
            return c.execute(stmt).all()

    # ------------------------------------------------------------ projects
    def put_project(self, project: Project) -> None:
        data = _dump(project)
        with self.engine.begin() as c:
            existing = c.execute(select(projects.c.id).where(projects.c.id == project.id)).first()
            if existing:
                c.execute(projects.update().where(projects.c.id == project.id).values(json=data))
            else:
                c.execute(projects.insert().values(id=project.id, created_at=_dt(project.created_at),
                                                   json=data))

    def get_project(self, project_id: str) -> Project | None:
        row = self._one(select(projects.c.json).where(projects.c.id == project_id))
        return Project.model_validate(row[0]) if row else None

    def list_projects(self) -> list[Project]:
        rows = self._all(select(projects.c.json).order_by(projects.c.created_at.desc()))
        return [Project.model_validate(r[0]) for r in rows]

    def delete_project(self, project_id: str) -> None:
        with self.engine.begin() as c:
            for t in (nodes, edges, runs, inbox, events, costs, counters):
                c.execute(t.delete().where(t.c.project_id == project_id))
            c.execute(projects.delete().where(projects.c.id == project_id))

    # ------------------------------------------------------------ nodes
    def put_node(self, node: Node) -> Node:
        pkey = _pk(node.project_id if node.scope.value == "project" else None)
        with self.engine.begin() as c:
            cur = c.execute(
                select(nodes.c.version, nodes.c.created_at)
                .where(and_(nodes.c.pkey == pkey, nodes.c.id == node.id, nodes.c.is_current.is_(True)))
            ).first()
            if cur:
                node.version = cur[0] + 1
                node.created_at = _dt(cur[1]) or node.created_at
                c.execute(nodes.update().where(and_(nodes.c.pkey == pkey, nodes.c.id == node.id)).values(is_current=False))
            else:
                node.version = 1
            node.updated_at = datetime.now(timezone.utc)
            c.execute(nodes.insert().values(
                pkey=pkey, id=node.id, version=node.version, type=node.type.value, scope=node.scope.value,
                project_id=node.project_id, status=node.status, created_by=node.created_by,
                created_at=_dt(node.created_at), updated_at=_dt(node.updated_at),
                is_current=True, text=node.text(), json=_dump(node)))
        return node

    def get_node(self, node_id: str, project_id: str | None = None, version: int | None = None) -> Node | None:
        cond = and_(nodes.c.id == node_id, nodes.c.pkey == _pk(project_id))
        cond = and_(cond, nodes.c.version == version) if version else and_(cond, nodes.c.is_current.is_(True))
        row = self._one(select(nodes.c.json).where(cond))
        return Node.model_validate(row[0]) if row else None

    def get_nodes(self, node_ids: Iterable[str], project_id: str | None = None) -> list[Node]:
        ids = list(node_ids)
        if not ids:
            return []
        rows = self._all(select(nodes.c.json).where(and_(nodes.c.id.in_(ids), nodes.c.pkey == _pk(project_id),
                                                         nodes.c.is_current.is_(True))))
        by_id = {r[0]["id"]: Node.model_validate(r[0]) for r in rows}
        return [by_id[i] for i in ids if i in by_id]

    def list_nodes(self, project_id=None, type=None, scope=None, status=None, limit=None) -> list[Node]:
        stmt = select(nodes.c.json).where(nodes.c.is_current.is_(True))
        if project_id is not None:
            stmt = stmt.where(nodes.c.project_id == project_id)
        if type:
            stmt = stmt.where(nodes.c.type == type)
        if scope:
            stmt = stmt.where(nodes.c.scope == scope)
        if status:
            stmt = stmt.where(nodes.c.status == status)
        stmt = stmt.order_by(nodes.c.created_at, nodes.c.id)
        if limit:
            stmt = stmt.limit(limit)
        return [Node.model_validate(r[0]) for r in self._all(stmt)]

    def node_versions(self, node_id: str, project_id: str | None = None) -> list[Node]:
        rows = self._all(select(nodes.c.json).where(and_(nodes.c.id == node_id, nodes.c.pkey == _pk(project_id)))
                         .order_by(nodes.c.version))
        return [Node.model_validate(r[0]) for r in rows]

    def search_nodes(self, text: str, project_id=None, type=None, limit: int = 50) -> list[Node]:
        stmt = select(nodes.c.json).where(nodes.c.is_current.is_(True))
        for term in text.split():
            stmt = stmt.where(nodes.c.text.ilike(f"%{term}%"))
        if project_id is not None:
            stmt = stmt.where(nodes.c.project_id == project_id)
        if type:
            stmt = stmt.where(nodes.c.type == type)
        return [Node.model_validate(r[0]) for r in self._all(stmt.limit(limit))]

    def delete_node(self, node_id: str, project_id: str | None = None) -> None:
        pkey = _pk(project_id)
        with self.engine.begin() as c:
            c.execute(nodes.delete().where(and_(nodes.c.id == node_id, nodes.c.pkey == pkey)))
            c.execute(edges.delete().where(and_(edges.c.pkey == pkey,
                                                sa.or_(edges.c.src == node_id, edges.c.dst == node_id))))

    # ------------------------------------------------------------ edges
    def add_edge(self, edge: Edge, project_id: str | None = None) -> None:
        pkey = _pk(project_id)
        with self.engine.begin() as c:
            exists = c.execute(select(edges.c.id).where(and_(
                edges.c.pkey == pkey, edges.c.src == edge.src, edges.c.dst == edge.dst,
                edges.c.type == edge.type.value))).first()
            if exists:
                c.execute(edges.update().where(edges.c.id == exists[0]).values(json=_dump(edge)))
                return
            c.execute(edges.insert().values(
                src=edge.src, dst=edge.dst, type=edge.type.value, project_id=project_id, pkey=pkey,
                created_by=edge.created_by, created_at=_dt(edge.created_at), json=_dump(edge)))

    def _edges(self, stmt) -> list[Edge]:
        return [Edge.model_validate(r[0]) for r in self._all(stmt)]

    def edges_from(self, src: str, type: str | None = None, project_id: str | None = None) -> list[Edge]:
        stmt = select(edges.c.json).where(and_(edges.c.src == src, edges.c.pkey == _pk(project_id)))
        if type:
            stmt = stmt.where(edges.c.type == type)
        return self._edges(stmt)

    def edges_to(self, dst: str, type: str | None = None, project_id: str | None = None) -> list[Edge]:
        stmt = select(edges.c.json).where(and_(edges.c.dst == dst, edges.c.pkey == _pk(project_id)))
        if type:
            stmt = stmt.where(edges.c.type == type)
        return self._edges(stmt)

    def list_edges(self, project_id: str | None, type: str | None = None) -> list[Edge]:
        stmt = select(edges.c.json).where(edges.c.pkey == _pk(project_id))
        if type:
            stmt = stmt.where(edges.c.type == type)
        return self._edges(stmt)

    def remove_edge(self, src: str, dst: str, type: str, project_id: str | None = None) -> None:
        with self.engine.begin() as c:
            c.execute(edges.delete().where(and_(edges.c.pkey == _pk(project_id), edges.c.src == src,
                                                edges.c.dst == dst, edges.c.type == type)))

    # ------------------------------------------------------------ ids
    def next_ids(self, prefix: str, project_id: str | None, n: int = 1) -> list[str]:
        pid = project_id or "__workspace__"
        with self.engine.begin() as c:
            row = c.execute(select(counters.c.next).where(and_(
                counters.c.prefix == prefix, counters.c.project_id == pid)).with_for_update()).first()
            start = row[0] if row else 1
            if row:
                c.execute(counters.update().where(and_(
                    counters.c.prefix == prefix, counters.c.project_id == pid)).values(next=start + n))
            else:
                c.execute(counters.insert().values(prefix=prefix, project_id=pid, next=start + n))
        return [format_id(prefix, i) for i in range(start, start + n)]

    def bump_counter(self, prefix: str, project_id: str | None, at_least: int) -> None:
        pid = project_id or "__workspace__"
        with self.engine.begin() as c:
            row = c.execute(select(counters.c.next).where(and_(
                counters.c.prefix == prefix, counters.c.project_id == pid))).first()
            if row and row[0] >= at_least:
                return
            if row:
                c.execute(counters.update().where(and_(
                    counters.c.prefix == prefix, counters.c.project_id == pid)).values(next=at_least))
            else:
                c.execute(counters.insert().values(prefix=prefix, project_id=pid, next=at_least))

    # ------------------------------------------------------------ runs / jobs
    def put_run(self, run: Run) -> None:
        data = _dump(run)
        with self.engine.begin() as c:
            if c.execute(select(runs.c.id).where(runs.c.id == run.id)).first():
                c.execute(runs.update().where(runs.c.id == run.id).values(status=run.status.value, json=data))
            else:
                c.execute(runs.insert().values(id=run.id, project_id=run.project_id,
                                               status=run.status.value, created_at=_dt(run.created_at),
                                               json=data))

    def get_run(self, run_id: str) -> Run | None:
        row = self._one(select(runs.c.json).where(runs.c.id == run_id))
        return Run.model_validate(row[0]) if row else None

    def list_runs(self, project_id=None, status=None) -> list[Run]:
        stmt = select(runs.c.json)
        if project_id:
            stmt = stmt.where(runs.c.project_id == project_id)
        if status:
            stmt = stmt.where(runs.c.status == status)
        return [Run.model_validate(r[0]) for r in self._all(stmt.order_by(runs.c.created_at.desc()))]

    def put_job(self, job: Job) -> None:
        data = _dump(job)
        with self.engine.begin() as c:
            if c.execute(select(jobs.c.id).where(jobs.c.id == job.id)).first():
                c.execute(jobs.update().where(jobs.c.id == job.id).values(status=job.status.value, json=data))
            else:
                c.execute(jobs.insert().values(id=job.id, run_id=job.run_id, status=job.status.value, json=data))

    def get_job(self, job_id: str) -> Job | None:
        row = self._one(select(jobs.c.json).where(jobs.c.id == job_id))
        return Job.model_validate(row[0]) if row else None

    def list_jobs(self, run_id: str) -> list[Job]:
        return [Job.model_validate(r[0]) for r in self._all(select(jobs.c.json).where(jobs.c.run_id == run_id))]

    # ------------------------------------------------------------ inbox
    def put_inbox(self, item: InboxItem) -> None:
        data = _dump(item)
        with self.engine.begin() as c:
            if c.execute(select(inbox.c.id).where(inbox.c.id == item.id)).first():
                c.execute(inbox.update().where(inbox.c.id == item.id).values(status=item.status.value, json=data))
            else:
                c.execute(inbox.insert().values(id=item.id, project_id=item.project_id, run_id=item.run_id,
                                                status=item.status.value, created_at=_dt(item.created_at),
                                                json=data))

    def get_inbox(self, item_id: str) -> InboxItem | None:
        row = self._one(select(inbox.c.json).where(inbox.c.id == item_id))
        return InboxItem.model_validate(row[0]) if row else None

    def list_inbox(self, project_id=None, status=None, run_id=None) -> list[InboxItem]:
        stmt = select(inbox.c.json)
        if project_id:
            stmt = stmt.where(inbox.c.project_id == project_id)
        if status:
            stmt = stmt.where(inbox.c.status == status)
        if run_id:
            stmt = stmt.where(inbox.c.run_id == run_id)
        return [InboxItem.model_validate(r[0]) for r in self._all(stmt.order_by(inbox.c.created_at))]

    # ------------------------------------------------------------ events / costs
    def append_event(self, event: Event) -> Event:
        with self.engine.begin() as c:
            res = c.execute(events.insert().values(ts=_dt(event.ts), project_id=event.project_id,
                                                   run_id=event.run_id, kind=event.kind,
                                                   json=_dump(event)))
            event.seq = int(res.inserted_primary_key[0])
            c.execute(events.update().where(events.c.seq == event.seq).values(json=_dump(event)))
        return event

    def list_events(self, since_seq: int = 0, project_id=None, run_id=None, limit: int = 500) -> list[Event]:
        stmt = select(events.c.json).where(events.c.seq > since_seq)
        if project_id:
            stmt = stmt.where(events.c.project_id == project_id)
        if run_id:
            stmt = stmt.where(events.c.run_id == run_id)
        return [Event.model_validate(r[0]) for r in self._all(stmt.order_by(events.c.seq).limit(limit))]

    def add_cost(self, entry: CostEntry) -> None:
        with self.engine.begin() as c:
            res = c.execute(costs.insert().values(project_id=entry.project_id, run_id=entry.run_id,
                                                  job_id=entry.job_id, cost_usd=entry.cost_usd,
                                                  created_at=_dt(entry.created_at), json=_dump(entry)))
            entry.id = int(res.inserted_primary_key[0])

    def list_costs(self, project_id=None, run_id=None) -> list[CostEntry]:
        stmt = select(costs.c.json, costs.c.id)
        if project_id:
            stmt = stmt.where(costs.c.project_id == project_id)
        if run_id:
            stmt = stmt.where(costs.c.run_id == run_id)
        out = []
        for r in self._all(stmt.order_by(costs.c.id)):
            e = CostEntry.model_validate(r[0])
            e.id = r[1]
            out.append(e)
        return out

    def sum_cost(self, project_id=None, run_id=None) -> float:
        stmt = select(func.coalesce(func.sum(costs.c.cost_usd), 0.0))
        if project_id:
            stmt = stmt.where(costs.c.project_id == project_id)
        if run_id:
            stmt = stmt.where(costs.c.run_id == run_id)
        return float(self._one(stmt)[0])

    def close(self) -> None:
        self.engine.dispose()
