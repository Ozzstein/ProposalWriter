"""Scope configuration: which optional modules a proposal includes.

User preference controls optional work; call requirements control mandatory work. Pure functions
over the CallSpec, the funder pack and the researcher's preferences — no I/O here.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel

ModuleState = Literal["excluded", "included", "required"]
ModuleSource = Literal["call", "pack", "user", "default"]

MODULES: tuple[str, ...] = ("finance", "business_plan", "figures", "external_review")
STATES: tuple[str, ...] = ("excluded", "included", "required")
MODULE_STAGE = {"finance": "finance", "business_plan": "business-plan",
                "figures": "figures", "external_review": "external-feedback"}
MODULE_STATE_KEY = {"finance": "finance", "business_plan": "business_plan",
                    "figures": "figures", "external_review": "external_review"}
MODULE_LABEL = {"finance": "Finance", "business_plan": "Business plan",
                "figures": "Figures", "external_review": "External review"}
CONCEPT_STATUSES: tuple[str, ...] = ("none", "preliminary", "aligned")

_FIGURE_HINTS = re.compile(r"\b(figure|diagram|gantt|chart)", re.I)


class ModuleScope(BaseModel):
    state: ModuleState
    source: ModuleSource
    reason: str = ""


class ScopeConfig(BaseModel):
    finance: ModuleScope
    business_plan: ModuleScope
    figures: ModuleScope
    external_review: ModuleScope
    configured_at: str | None = None    # ISO timestamp of the researcher's confirmation

    # ------------------------------------------------------------ access
    def module(self, name: str) -> ModuleScope:
        if name not in MODULES:
            raise KeyError(f"unknown module {name!r}")
        return getattr(self, name)

    def state(self, name: str) -> str:
        return self.module(name).state

    def is_excluded(self, name: str) -> bool:
        return self.state(name) == "excluded"

    def locked(self, name: str) -> bool:
        """Required by the call or the pack: the researcher cannot downgrade it."""
        m = self.module(name)
        return m.state == "required" and m.source in ("call", "pack")

    def required(self) -> list[str]:
        return [m for m in MODULES if self.state(m) == "required"]

    def summary(self) -> str:
        return "; ".join(f"{m}: {self.state(m)} ({self.module(m).source})" for m in MODULES)

    # ------------------------------------------------------------ persistence (project.settings)
    @classmethod
    def load(cls, project: Any) -> "ScopeConfig | None":
        raw = (getattr(project, "settings", None) or {}).get("scope") if project is not None else None
        if not raw:
            return None
        try:
            return cls.model_validate(raw)
        except Exception:
            return None

    def save(self, project: Any) -> None:
        project.settings["scope"] = self.model_dump(mode="json")


# ------------------------------------------------------------------ derivation

def _call_requires(module: str, callspec: Any) -> str | None:
    if callspec is None:
        return None
    if module == "finance" and callspec.has_financials():
        return "the call has financial sections or budget rules"
    if module == "business_plan" and callspec.needs_business_plan():
        return "the call requires a business plan"
    return None


def _derive_module(module: str, callspec: Any, pack_modules: dict[str, str], prefs: dict[str, str],
                   call_text: str) -> ModuleScope:
    reason = _call_requires(module, callspec)
    if reason:
        return ModuleScope(state="required", source="call", reason=reason)
    if pack_modules.get(module) in STATES:
        return ModuleScope(state=pack_modules[module], source="pack", reason="funder pack default")
    if prefs.get(module) in ("excluded", "included"):
        return ModuleScope(state=prefs[module], source="user", reason="chosen when the project was created")
    if module == "figures":
        guidance = " ".join(s.guidance or "" for s in (callspec.sections if callspec is not None else []))
        if _FIGURE_HINTS.search(f"{call_text} {guidance}"):
            return ModuleScope(state="included", source="default",
                               reason="the call mentions figures, diagrams or charts")
    return ModuleScope(state="excluded", source="default", reason="not requested by the call")


def derive_scope(callspec: Any, pack: Any = None, preferences: dict[str, str] | None = None,
                 call_text: str = "") -> ScopeConfig:
    """Precedence per module: call requirement > pack default > creation-time preference > default."""
    pack_modules = dict(getattr(pack, "modules", None) or {})
    prefs = dict(preferences or {})
    return ScopeConfig(**{m: _derive_module(m, callspec, pack_modules, prefs, call_text) for m in MODULES})


def rederive(current: ScopeConfig, derived: ScopeConfig) -> ScopeConfig:
    """After a re-parse: call-required upgrades (and downgrades) apply, everything else keeps the
    researcher's choice. The confirmation is reset only when some state actually changed."""
    picked: dict[str, ModuleScope] = {}
    changed = False
    for m in MODULES:
        cur, new = current.module(m), derived.module(m)
        pick = new if (new.source == "call" or cur.source == "call") else cur
        picked[m] = pick
        changed = changed or pick.state != cur.state
    return ScopeConfig(**picked, configured_at=None if changed else current.configured_at)


def apply_scope_change(current: ScopeConfig, changes: dict[str, str], *, by: str = "user",
                       reason: str = "") -> ScopeConfig:
    """Validate and apply researcher changes; always stamps ``configured_at`` (a user-originated write)."""
    data = current.model_dump()
    for module, state in changes.items():
        if module not in MODULES:
            raise ValueError(f"unknown module {module!r}; expected one of {MODULES}")
        if state not in STATES:
            raise ValueError(f"invalid state {state!r} for {module}; expected one of {STATES}")
        if current.locked(module):
            if state != "required":
                raise ValueError(f"{module} is required by the {current.module(module).source}")
            continue
        data[module] = {"state": state, "source": "user", "reason": reason or f"set by {by}"}
    data["configured_at"] = datetime.now(timezone.utc).isoformat()
    return ScopeConfig.model_validate(data)


# ------------------------------------------------------------------ concept status (context document)

def hypothesis_of(doc: Any) -> str:
    hyp = ((doc.data.get("hypothesis") if doc is not None else "") or "").strip()
    return "" if "to be completed" in hyp.lower() else hyp


def concept_status_of(doc: Any) -> str:
    if not hypothesis_of(doc):
        return "none"
    status = doc.data.get("concept_status")
    return status if status in CONCEPT_STATUSES and status != "none" else "preliminary"
