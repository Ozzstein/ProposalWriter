"""Job handlers and stage definitions. Importing this package registers everything."""
from __future__ import annotations

from agency.engine.plan import Handler, StageDef

HANDLERS: dict[str, Handler] = {}
STAGES: dict[str, StageDef] = {}


def handler(name: str):
    def deco(fn: Handler) -> Handler:
        HANDLERS[name] = fn
        return fn
    return deco


def stage(sd: StageDef) -> StageDef:
    STAGES[sd.name] = sd
    return sd


from agency.jobs import (business_plan, common, drafting, export, feedback, figures, finance, ideate,  # noqa: E402,F401
                         parse_call, plan, research, review)
