"""Runs, jobs, inbox items, cost entries and events."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .graph import utcnow


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_USER = "waiting_for_user"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    INTERRUPTED = "interrupted"


class JobKind(str, Enum):
    AGENT = "agent"        # one contract invocation
    SESSION = "session"    # interactive ClaudeSDKClient session
    CODE = "code"          # deterministic python step
    INBOX = "inbox"        # wait for a human answer
    GATE = "gate"          # evaluate a gate policy
    LOOP = "loop"          # repeat a sub-DAG until a stop condition


class JobStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    INTERRUPTED = "interrupted"


class Job(BaseModel):
    id: str
    run_id: str
    name: str                              # e.g. "retrieve:literature"
    kind: JobKind
    contract: str | None = None            # agent contract name
    deps: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None
    cost_usd: float = 0.0
    started_at: datetime | None = None
    ended_at: datetime | None = None
    sdk_session_id: str | None = None


class Run(BaseModel):
    id: str
    project_id: str
    stage: str                             # the workflow name, e.g. "research"
    status: RunStatus = RunStatus.QUEUED
    flags: dict[str, Any] = Field(default_factory=dict)
    phase: str | None = None
    cost_usd: float = 0.0
    error: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    summary: str | None = None


class InboxKind(str, Enum):
    QUESTION = "question"    # options + free text
    APPROVAL = "approval"    # table of rows, per-row decisions
    FORM = "form"            # json-schema driven
    CHAT = "chat"            # interactive session turn


class InboxStatus(str, Enum):
    PENDING = "pending"
    ANSWERED = "answered"
    CANCELLED = "cancelled"


class InboxItem(BaseModel):
    id: str
    project_id: str
    run_id: str | None = None
    job_id: str | None = None
    kind: InboxKind
    header: str = ""
    question: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    answer: dict[str, Any] | None = None
    status: InboxStatus = InboxStatus.PENDING
    created_at: datetime = Field(default_factory=utcnow)
    answered_at: datetime | None = None


class CostEntry(BaseModel):
    id: int | None = None
    project_id: str
    run_id: str | None = None
    job_id: str | None = None
    agent: str | None = None
    model: str | None = None
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    num_turns: int = 0
    duration_ms: int = 0
    created_at: datetime = Field(default_factory=utcnow)


class Event(BaseModel):
    seq: int | None = None
    ts: datetime = Field(default_factory=utcnow)
    project_id: str | None = None
    run_id: str | None = None
    job_id: str | None = None
    kind: str                               # stage:start, job:start, tool:use, inbox:pending, ...
    agent: str | None = None
    tool_name: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class Project(BaseModel):
    id: str                                 # slug
    name: str
    funder: str | None = None
    mechanism: str | None = None
    topic: str | None = None
    deadline: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    stages: dict[str, dict[str, Any]] = Field(default_factory=dict)   # stage -> {status, updated_at}
    gates: dict[str, dict[str, Any]] = Field(default_factory=dict)    # gate -> {passed, checked_at}
    settings: dict[str, Any] = Field(default_factory=dict)
