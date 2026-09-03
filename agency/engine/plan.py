"""Stage plans: an explicit job DAG the scheduler executes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from agency.domain.runs import JobKind


@dataclass
class JobSpec:
    name: str
    handler: str                      # key into agency.jobs.HANDLERS
    kind: JobKind = JobKind.CODE
    deps: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)
    contract: str | None = None
    optional: bool = False            # failure does not fail the run


@dataclass
class StagePlan:
    stage: str
    jobs: list[JobSpec]
    notes: list[str] = field(default_factory=list)

    def validate(self) -> None:
        names = {j.name for j in self.jobs}
        if len(names) != len(self.jobs):
            raise ValueError("duplicate job names in plan")
        for j in self.jobs:
            for d in j.deps:
                if d not in names:
                    raise ValueError(f"job {j.name} depends on unknown job {d}")


@dataclass
class StageDef:
    name: str                          # "research"
    state_key: str | None              # project.stages key
    planner: Callable[..., StagePlan]
    requires_gate: str | None = None
    requires_stages: tuple[str, ...] = ()
    interactive: bool = False
    description: str = ""
    flags: dict[str, str] = field(default_factory=dict)   # flag -> help


Handler = Callable[..., Awaitable[dict[str, Any]]]


class JobFailed(Exception):
    pass


class StageBlocked(Exception):
    pass
