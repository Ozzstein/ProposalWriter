# Intake: call-first workflow and scope configuration — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the guided path call-first, add a typed four-module scope record decided in the inbox after parse-call, and enforce it through gates and the stage runner.

**Architecture:** A pure `ScopeConfig` module (`agency/domain/scope.py`) derives and validates scope; `Workspace` persists it in `project.settings["scope"]` and logs Decision nodes; parse-call gains two jobs (`configure_scope`, `align_concept`); the runner, gates, guide, planner, API, CLI and UI read the same record. Concept status (`none | preliminary | aligned`) lives on the context document.

**Tech Stack:** Python 3.10+, pydantic v2, FastAPI, typer, pytest (asyncio auto mode, mocked SDK via `tests/fake_sdk.py`); React + TypeScript + TanStack Query in `ui/web`, shared types in `ui/shared/src/state.ts`.

**Spec:** `docs/superpowers/specs/2026-09-03-intake-scope-design.md`

## Global Constraints

- Tests: `.venv/bin/python -m pytest -q` (all mocked; `tests/test_sdk_smoke.py` is skipped without `ANTHROPIC_API_KEY`).
- UI: `cd ui && npm run typecheck && npm run build` must pass at the end of every UI task.
- No new agent contracts; `agency doctor` must keep passing (`.venv/bin/agency doctor`).
- No store schema migration: scope lives in `project.settings["scope"]`, concept status in the context document's data.
- Thresholds in `agency/policy/thresholds.py` are not changed.
- Module names are exactly `finance`, `business_plan`, `figures`, `external_review`; states exactly `excluded`, `included`, `required`; sources exactly `call`, `pack`, `user`, `default`.
- Decision node types used: `scope_configured`, `scope_changed`, `concept_alignment`.
- This checkout has no git identity configured. Commit with
  `git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "..."` and end every commit message with:
  ```
  Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_014jWan98ut6ZUHkmXMG2bqW
  ```

## File structure

Create:
- `agency/domain/scope.py` — ScopeConfig model, derivation, change rules, concept-status helpers. Pure, no I/O.
- `tests/test_scope.py` — unit tests for the above plus the Workspace scope methods.

Modify:
- `agency/funders/packs.py` — `FunderPack.modules`.
- `packs/innovation-fund/pack.yaml` — `modules:` defaults.
- `agency/workspace.py` — packs, scope get/put/set/recommend, concept status, `create_project` extras, `STAGES` order, `status()` scope line.
- `agency/domain/models.py` — `ConceptAlignment`.
- `agency/policy/gates.py` — scope-aware `GateContext`, four new rules.
- `agency/engine/plan.py` — `StageDef.scope_key`.
- `agency/engine/runner.py` — scope check in `check_prerequisites`.
- `agency/engine/runtime.py` — `RunContext.scope()`.
- `agency/jobs/common.py` — `replace_hypothesis`.
- `agency/jobs/ideate.py` — concept status on choose.
- `agency/jobs/parse_call.py` — two jobs, two flags.
- `agency/jobs/drafting.py` — scope-aware `draftable_sections`.
- `agency/jobs/finance.py`, `figures.py`, `business_plan.py`, `feedback.py` — `scope_key`.
- `agency/jobs/plan.py` — brief scope section, `validate_plan` scope check.
- `agency/policy/guide.py` — call-first ordering, scope steps.
- `agency/server/app.py` — scope endpoints, `scope_preferences`.
- `agency/cli.py` — `agency scope`.
- `ui/shared/src/state.ts`, `ui/web/src/lib/api.ts`, `ui/web/src/pages/{NewProject,Overview,Inbox,Pipeline}.tsx`.
- `docs/architecture.md`, `README.md`.
- Tests: `tests/test_engine.py`, `tests/test_gates.py`, `tests/test_guide.py`, `tests/test_pipeline_stages.py`, `tests/test_interactive_stages.py`, `tests/test_planner.py`, `tests/test_server.py`.

---

### Task 1: ScopeConfig model, derivation and change rules

**Files:**
- Create: `agency/domain/scope.py`
- Modify: `agency/funders/packs.py:466-481` (add `modules`)
- Modify: `packs/innovation-fund/pack.yaml`
- Test: `tests/test_scope.py`

**Interfaces:**
- Produces:
  - `MODULES: tuple[str, ...]`, `STATES`, `MODULE_STAGE: dict[str, str]`, `MODULE_STATE_KEY: dict[str, str]`, `MODULE_LABEL: dict[str, str]`, `CONCEPT_STATUSES`
  - `class ModuleScope(BaseModel)`: `state`, `source`, `reason`
  - `class ScopeConfig(BaseModel)`: four modules + `configured_at`; methods `module(name)`, `state(name)`, `is_excluded(name)`, `locked(name)`, `required()`, `summary()`, `save(project)`, classmethod `load(project) -> ScopeConfig | None`
  - `derive_scope(callspec, pack=None, preferences=None, call_text="") -> ScopeConfig`
  - `rederive(current, derived) -> ScopeConfig`
  - `apply_scope_change(current, changes: dict[str, str], *, by="user", reason="") -> ScopeConfig`
  - `hypothesis_of(doc) -> str`, `concept_status_of(doc) -> str`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_scope.py
"""ScopeConfig: derivation precedence, change rules, concept status."""
import pytest

from agency.domain.callspec import CallSpec, SectionSpec
from agency.domain.scope import (MODULES, ScopeConfig, apply_scope_change, concept_status_of, derive_scope,
                                 hypothesis_of, rederive)
from agency.funders.packs import FunderPack


def _spec(**kw):
    sections = [SectionSpec(id="1", title="Excellence", kind="excellence")]
    return CallSpec(call_id="C", title="T", funder="F", sections=sections + kw.pop("sections", []),
                    criteria=[], **kw)


def test_derive_defaults_to_excluded_without_a_call():
    s = derive_scope(None)
    assert [s.state(m) for m in MODULES] == ["excluded"] * 4
    assert all(s.module(m).source == "default" for m in MODULES)
    assert s.configured_at is None


def test_call_requirements_win_over_everything():
    spec = _spec(sections=[SectionSpec(id="4", title="Financial", kind="financial")],
                 annexes=["Business Plan"])
    pack = FunderPack(id="p", name="P", modules={"finance": "excluded", "business_plan": "excluded"})
    s = derive_scope(spec, pack, {"finance": "excluded"})
    assert s.finance.state == "required" and s.finance.source == "call"
    assert s.business_plan.state == "required" and s.business_plan.source == "call"
    assert s.locked("finance") and s.locked("business_plan")
    assert s.required() == ["finance", "business_plan"]


def test_pack_then_preference_then_default():
    pack = FunderPack(id="p", name="P", modules={"figures": "required"})
    s = derive_scope(_spec(), pack, {"figures": "excluded", "external_review": "included"})
    assert s.figures.state == "required" and s.figures.source == "pack" and s.locked("figures")
    assert s.external_review.state == "included" and s.external_review.source == "user"
    assert s.finance.state == "excluded" and s.finance.source == "default"


def test_figures_included_when_the_call_mentions_them():
    assert derive_scope(_spec(), call_text="Include a Gantt chart of the work plan").figures.state == "included"
    spec = _spec(sections=[SectionSpec(id="3", title="Plan", guidance="Provide a diagram of the architecture")])
    assert derive_scope(spec).figures.state == "included"
    assert derive_scope(_spec(), call_text="no visuals").figures.state == "excluded"


def test_apply_change_rules():
    s = derive_scope(_spec(sections=[SectionSpec(id="4", title="Fin", kind="financial")]))
    with pytest.raises(ValueError, match="finance is required by the call"):
        apply_scope_change(s, {"finance": "included"})
    with pytest.raises(ValueError, match="unknown module"):
        apply_scope_change(s, {"budget": "included"})
    with pytest.raises(ValueError, match="invalid state"):
        apply_scope_change(s, {"figures": "maybe"})
    s2 = apply_scope_change(s, {"figures": "required", "finance": "required"}, by="cli", reason="want plots")
    assert s2.figures.state == "required" and s2.figures.source == "user" and s2.figures.reason == "want plots"
    assert s2.finance.source == "call"                       # a no-op on a locked module keeps its source
    assert s2.configured_at and not s2.locked("figures")     # user-required is not locked
    s3 = apply_scope_change(s2, {"figures": "excluded"})
    assert s3.figures.state == "excluded"


def test_rederive_keeps_user_choices_and_applies_call_upgrades():
    first = apply_scope_change(derive_scope(_spec()), {"figures": "included", "external_review": "included"})
    stamp = first.configured_at
    # nothing changed in the call → user choices and the confirmation survive
    again = rederive(first, derive_scope(_spec()))
    assert again.figures.state == "included" and again.configured_at == stamp
    # the call now requires finance → upgraded and the confirmation is reset
    spec2 = _spec(sections=[SectionSpec(id="4", title="Fin", kind="financial")])
    up = rederive(first, derive_scope(spec2))
    assert up.finance.state == "required" and up.finance.source == "call"
    assert up.figures.state == "included" and up.configured_at is None
    # the requirement disappears again → falls back to derivation (default excluded), confirmation reset
    down = rederive(up, derive_scope(_spec()))
    assert down.finance.state == "excluded" and down.finance.source == "default" and down.configured_at is None


def test_load_and_save_round_trip():
    class P:  # duck-typed project
        settings: dict = {}
    p = P()
    assert ScopeConfig.load(p) is None
    s = derive_scope(_spec())
    s.save(p)
    assert ScopeConfig.load(p) == s
    p.settings["scope"] = {"garbage": True}
    assert ScopeConfig.load(p) is None
    assert "finance: excluded (default)" in s.summary()


def test_concept_status_helpers():
    class Doc:
        def __init__(self, data):
            self.data = data
    assert concept_status_of(None) == "none"
    assert concept_status_of(Doc({"hypothesis": "_To be completed._"})) == "none"
    assert hypothesis_of(Doc({"hypothesis": "  A digital twin  "})) == "A digital twin"
    assert concept_status_of(Doc({"hypothesis": "A digital twin"})) == "preliminary"
    assert concept_status_of(Doc({"hypothesis": "A digital twin", "concept_status": "aligned"})) == "aligned"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_scope.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'agency.domain.scope'`

- [ ] **Step 3: Add `modules` to FunderPack and the innovation-fund pack**

In `agency/funders/packs.py`, inside `class FunderPack`, after `panel_personas`:

```python
    modules: dict[str, str] = Field(default_factory=dict)   # module -> excluded | included | required
```

In `packs/innovation-fund/pack.yaml`, after the `annexes:` line:

```yaml
modules:
  finance: required
  business_plan: required
  figures: included
```

- [ ] **Step 4: Write `agency/domain/scope.py`**

```python
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
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_scope.py -q`
Expected: 8 passed

- [ ] **Step 6: Commit**

```bash
git add agency/domain/scope.py agency/funders/packs.py packs/innovation-fund/pack.yaml tests/test_scope.py
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "Scope: ScopeConfig model, derivation precedence and change rules

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014jWan98ut6ZUHkmXMG2bqW"
```

---

### Task 2: Workspace scope and concept-status methods, call-first stage order

**Files:**
- Modify: `agency/workspace.py`
- Test: `tests/test_scope.py` (append), `tests/test_server.py:23-41` (no change expected; verify)

**Interfaces:**
- Consumes: Task 1.
- Produces on `Workspace`:
  - `self.packs: dict[str, FunderPack]`
  - `get_scope(project_id) -> ScopeConfig | None`
  - `recommend_scope(project_id) -> ScopeConfig`
  - `put_scope(project_id, scope: ScopeConfig) -> ScopeConfig` (persist only, no decision)
  - `set_scope(project_id, changes: dict[str, str], *, by="researcher", reason="") -> ScopeConfig` (validates, persists, Decision `scope_changed`, event `scope:changed`)
  - `concept_status(project_id) -> str`
  - `set_concept_status(project_id, status: str) -> None`
  - `create_project(..., scope_preferences: dict[str, str] | None = None)`
  - `STAGES` reordered with `call_parsing` first; `status()` gains `"scope"`.

- [ ] **Step 1: Append failing tests to `tests/test_scope.py`**

```python
from agency.domain.graph import NodeType


def test_workspace_scope_round_trip(ws, project):
    assert ws.get_scope("demo") is None
    rec = ws.recommend_scope("demo")                       # no call spec yet → all excluded
    assert rec.finance.state == "excluded" and rec.configured_at is None
    s = ws.set_scope("demo", {"figures": "included"}, by="test", reason="plots wanted")
    assert s.figures.state == "included" and s.configured_at
    assert ws.get_scope("demo").figures.state == "included"
    d = ws.graph("demo").decisions("scope_changed")
    assert len(d) == 1 and "figures: excluded -> included" in d[0].data["decision"]
    assert ws.status("demo")["scope"]["figures"]["state"] == "included"
    # a call that requires finance locks it
    from tests.test_engine import CALLSPEC
    spec = dict(CALLSPEC, sections=CALLSPEC["sections"] + [{"id": "4", "title": "Financial", "kind": "financial"}])
    ws.graph("demo").add(NodeType.CALL_SPEC, spec)
    assert ws.recommend_scope("demo").finance.state == "required"
    ws.put_scope("demo", ws.recommend_scope("demo"))
    with pytest.raises(ValueError):
        ws.set_scope("demo", {"finance": "excluded"})


def test_workspace_concept_status_and_preferences(ws):
    p = ws.create_project("Pref", project_id="pref", scope_preferences={"external_review": "included"})
    assert p.settings["scope_preferences"] == {"external_review": "included"}
    assert ws.concept_status("pref") == "none"
    assert ws.recommend_scope("pref").external_review.state == "included"
    ws.create_project("Hyp", project_id="hyp", hypothesis="A twin cuts scrap")
    assert ws.concept_status("hyp") == "preliminary"
    ws.set_concept_status("hyp", "aligned")
    assert ws.concept_status("hyp") == "aligned"
    with pytest.raises(ValueError):
        ws.set_concept_status("hyp", "maybe")


def test_stage_order_is_call_first(ws):
    from agency.workspace import STAGES
    assert STAGES[:2] == ["call_parsing", "ideation"]
    p = ws.create_project("Blank", project_id="blank")
    assert ws.current_stage(p) == "call_parsing"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_scope.py -q`
Expected: 3 failures (`AttributeError: 'Workspace' object has no attribute 'get_scope'`, etc.)

- [ ] **Step 3: Implement in `agency/workspace.py`**

Imports (add):

```python
from agency.domain.callspec import CallSpec
from agency.domain.scope import (CONCEPT_STATUSES, MODULES, ScopeConfig, apply_scope_change, concept_status_of,
                                 derive_scope)
from agency.funders.packs import load_packs
```

Replace the `STAGES` constant:

```python
STAGES = ["call_parsing", "ideation", "research", "writing", "finance", "figures",
          "business_plan", "review", "external_review", "export"]
```

In `__init__`, after `self.gates = ...`:

```python
        self.packs = load_packs(config.packs_dir)
```

Change `create_project` signature and body:

```python
    def create_project(self, name: str, *, funder: str | None = None, mechanism: str | None = None,
                       topic: str | None = None, deadline: str | None = None,
                       hypothesis: str | None = None, context_md: str | None = None,
                       project_id: str | None = None, settings: dict[str, Any] | None = None,
                       scope_preferences: dict[str, str] | None = None) -> Project:
        pid = project_id or slugify(name)
        if self.store.get_project(pid):
            raise ValueError(f"project '{pid}' already exists")
        settings = dict(settings or {})
        prefs = {m: s for m, s in (scope_preferences or {}).items() if m in MODULES and s in ("excluded", "included")}
        if prefs:
            settings["scope_preferences"] = prefs
        project = Project(
            id=pid, name=name, funder=funder, mechanism=mechanism, topic=topic, deadline=deadline,
            stages={s: {"status": "pending"} for s in STAGES},
            gates={g: {"passed": False} for g in GATES},
            settings=settings,
        )
        self.store.put_project(project)
        body = context_md or _default_context(project, hypothesis)
        self.graph(pid).put_document("context", f"{name} — research context", body,
                                     hypothesis=hypothesis or "",
                                     concept_status="preliminary" if (hypothesis or "").strip() else "none")
        self.config.project_dir(pid)
        self.events.emit("project:created", project_id=pid, name=name, funder=funder)
        return project
```

In `status()`, add to the returned dict:

```python
            "scope": (lambda s: s.model_dump(mode="json") if s else None)(ScopeConfig.load(project)),
```

Add these methods after `set_requirement_status`:

```python
    # ------------------------------------------------------------ scope
    def get_scope(self, project_id: str) -> ScopeConfig | None:
        return ScopeConfig.load(self.require_project(project_id))

    def recommend_scope(self, project_id: str) -> ScopeConfig:
        """Derive the scope from the current CallSpec, pack, preferences and extracted call text."""
        project = self.require_project(project_id)
        node = self.graph(project_id).callspec_node()
        spec: CallSpec | None = None
        if node is not None:
            try:
                spec = CallSpec.model_validate(node.data)
            except Exception:
                spec = None
        pack_id = (spec.pack if spec else None) or (project.settings or {}).get("pack") or "generic"
        pack = self.packs.get(pack_id, self.packs["generic"])
        inputs = self.config.project_dir(project_id) / "inputs"
        text = ""
        if inputs.exists():
            for p in sorted(inputs.rglob("*.extracted.txt")):
                text += p.read_text(errors="ignore")[:20000] + "\n"
        return derive_scope(spec, pack, (project.settings or {}).get("scope_preferences"), text)

    def put_scope(self, project_id: str, scope: ScopeConfig) -> ScopeConfig:
        project = self.require_project(project_id)
        scope.save(project)
        self.store.put_project(project)
        return scope

    def set_scope(self, project_id: str, changes: dict[str, str], *, by: str = "researcher",
                  reason: str = "") -> ScopeConfig:
        """Apply researcher changes (validated), persist, log a scope_changed decision."""
        project = self.require_project(project_id)
        current = ScopeConfig.load(project) or self.recommend_scope(project_id)
        new = apply_scope_change(current, changes, by=by, reason=reason)
        diffs = [f"{m}: {current.state(m)} -> {new.state(m)}" for m in MODULES if current.state(m) != new.state(m)]
        new.save(project)
        self.store.put_project(project)
        self.graph(project_id).add(NodeType.DECISION, {
            "question": "Change the proposal scope?", "decision": "; ".join(diffs) or "confirmed without changes",
            "rationale": [by, reason or "changed by the researcher"], "type": "scope_changed",
            "date": datetime.now(timezone.utc).date().isoformat()})
        self.events.emit("scope:changed", project_id=project_id, changes=changes, by=by)
        return new

    # ------------------------------------------------------------ concept status
    def concept_status(self, project_id: str) -> str:
        return concept_status_of(self.graph(project_id).document("context"))

    def set_concept_status(self, project_id: str, status: str) -> None:
        if status not in CONCEPT_STATUSES:
            raise ValueError(f"status must be one of {CONCEPT_STATUSES}")
        graph = self.graph(project_id)
        doc = graph.document("context")
        if doc is None:
            raise KeyError("no context document")
        graph.update(doc, concept_status=status)
        self.events.emit("concept:status", project_id=project_id, status=status)
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/test_scope.py tests/test_server.py::test_projects_and_status -q`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add agency/workspace.py tests/test_scope.py
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "Workspace: scope record, concept status, call-first stage order

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014jWan98ut6ZUHkmXMG2bqW"
```

---

### Task 3: Gate rules read the scope

**Files:**
- Modify: `agency/policy/gates.py`
- Test: `tests/test_gates.py`

**Interfaces:**
- Consumes: `ScopeConfig`, `MODULE_STATE_KEY`, `concept_status_of` (Task 1).
- Produces: `GateContext.scope`, `GateContext.stages`; `evaluate_gate(gate, graph, thresholds=None, callspec=None, project=None)`; rules `rule_scope_configured`, `rule_concept_aligned`, `rule_required_modules_complete`, `rule_external_review_required`.

- [ ] **Step 1: Write the failing tests (append to `tests/test_gates.py`)**

```python
from agency.domain.models import FeedbackEntry


def test_scope_gate_needs_configured_scope_and_aligned_concept(ws, project):
    g = ws.graph("demo")
    spec = _spec()
    spec.requirements[0].status = "met"
    g.add(NodeType.CALL_SPEC, spec.model_dump(mode="json"))
    g.put_document("outline", "Outline", "## 1. Abstract\n## 2. Innovation")
    r = evaluate_gate("scope", g)
    assert any("scope not configured" in b for b in r.blockers)
    assert any("preliminary concept not aligned" in b for b in r.blockers)
    ws.set_scope("demo", {})                       # confirm the derived scope
    ws.set_concept_status("demo", "aligned")
    assert evaluate_gate("scope", g).passed, evaluate_gate("scope", g).blockers


def test_scope_gate_alignment_passes_without_a_hypothesis(ws):
    ws.create_project("Empty", project_id="empty")
    g = ws.graph("empty")
    r = evaluate_gate("scope", g)
    aligned = next(c for c in r.criteria if c.criterion.startswith("Concept aligned"))
    assert aligned.met and "no hypothesis" in aligned.notes


def test_draft_gate_blocks_on_required_modules(ws, project):
    g = ws.graph("demo")
    spec = _spec()
    spec.sections.append(SectionSpec(id="4", title="Financial", kind="financial"))
    g.add(NodeType.CALL_SPEC, spec.model_dump(mode="json"))
    ws.put_scope("demo", ws.recommend_scope("demo"))      # finance required by the call
    r = evaluate_gate("draft", g)
    assert any("Required modules complete" in b and "finance" in b for b in r.blockers)
    ws.set_stage("demo", "finance", "complete")
    r = evaluate_gate("draft", g)
    assert not any("Required modules" in b for b in r.blockers)


def test_submission_gate_external_review_rule_only_when_required(ws, project):
    g = ws.graph("demo")
    names = [c.criterion for c in evaluate_gate("submission", g).criteria]
    assert not any("External review" in n for n in names)
    ws.set_scope("demo", {"external_review": "required"})
    r = evaluate_gate("submission", g)
    assert any("External review" in b and "no external feedback" in b for b in r.blockers)
    g.add(NodeType.FEEDBACK, FeedbackEntry(round=1, source_file="r.md", location="1", comment="x",
                                           category="writing", status="resolved", dedupe_key="k"))
    r = evaluate_gate("submission", g)
    ext = next(c for c in r.criteria if c.criterion.startswith("External review"))
    assert ext.met, ext.notes
```

If `FeedbackEntry` rejects these fields or `"resolved"` is not in `CLOSED_FEEDBACK_STATUSES` (both in
`agency/domain/models.py`), adjust the fixture to the model's required fields and a status that is in that set.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_gates.py -q`
Expected: the four new tests fail (no such blockers / rules)

- [ ] **Step 3: Implement in `agency/policy/gates.py`**

Imports (add):

```python
from agency.domain.scope import MODULE_STATE_KEY, ScopeConfig, concept_status_of
```

Extend `GateContext`:

```python
@dataclass
class GateContext:
    graph: Graph
    thresholds: dict[str, float]
    callspec: CallSpec | None = None
    scope: ScopeConfig | None = None
    stages: dict[str, dict[str, Any]] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)
```

Add rules after `rule_eligibility` (scope section):

```python
def rule_scope_configured(ctx: GateContext) -> Criterion:
    if ctx.scope is None:
        return crit("Proposal scope configured", False, "scope not configured; run parse-call with scope_only")
    ok = bool(ctx.scope.configured_at)
    return crit("Proposal scope configured", ok, ctx.scope.summary() if ok else "derived but not confirmed")


def rule_concept_aligned(ctx: GateContext) -> Criterion:
    status = concept_status_of(ctx.graph.document("context"))
    if status == "none":
        return crit("Concept aligned with the call", True, "no hypothesis yet")
    return crit("Concept aligned with the call", status == "aligned",
                "aligned" if status == "aligned" else
                "preliminary concept not aligned to the call; run parse-call with align_only")
```

After `rule_section_limits` (draft section):

```python
def rule_required_modules_complete(ctx: GateContext) -> Criterion:
    if ctx.scope is None:
        return crit("Required modules complete", True, "scope not configured")
    missing = [m for m in ("finance", "business_plan", "figures")
               if ctx.scope.state(m) == "required"
               and ctx.stages.get(MODULE_STATE_KEY[m], {}).get("status") != "complete"]
    return crit("Required modules complete", not missing,
                f"incomplete: {missing}" if missing else (f"{ctx.scope.required() or 'none'} required"))
```

After `rule_feedback_stale` (external feedback section):

```python
def rule_external_review_required(ctx: GateContext) -> Criterion | None:
    if ctx.scope is None or ctx.scope.state("external_review") != "required":
        return None
    fb = ctx.graph.feedback()
    if not fb:
        return crit("External review round ingested and closed", False, "no external feedback ingested")
    sub = [c for c in (rule_feedback_open(ctx), rule_feedback_statuses(ctx), rule_feedback_stale(ctx)) if c]
    failed = [c.notes or c.criterion for c in sub if not c.met]
    return crit("External review round ingested and closed", not failed,
                "; ".join(failed) if failed else f"{len(fb)} comments closed")
```

Update `GATE_RULES`:

```python
GATE_RULES: dict[str, list[Rule]] = {
    "scope": [rule_call_parsed, rule_criteria_mapped, rule_outline_exists, rule_context_documented,
              rule_eligibility, rule_scope_configured, rule_concept_aligned],
    "evidence": [rule_min_sources, rule_sota, rule_anchors, rule_gaps, rule_claims_registered,
                 rule_unsupported_ratio],
    "draft": [rule_all_sections_drafted, rule_drafts_cite_claims, rule_assumption_markers,
              rule_unregistered_refs, rule_abstract_limit, rule_section_limits, rule_required_modules_complete],
    "submission": [rule_scientific_scores, rule_no_critical_fixes, rule_compliance,
                   rule_unsupported_resolved, rule_hard_rules, rule_panel_score, rule_external_review_required],
    "external_feedback": [rule_feedback_open, rule_feedback_statuses, rule_feedback_stale],
}
```

Change `evaluate_gate` and `GatePolicy.check`:

```python
def evaluate_gate(gate: str, graph: Graph, thresholds: dict[str, float] | None = None,
                  callspec: CallSpec | None = None, project: Any = None) -> GateResult:
    gate = normalize_gate(gate)
    if gate not in GATE_RULES:
        raise ValueError(f"unknown gate {gate!r}; expected one of {GATES}")
    if project is None and graph.project_id:
        project = graph.store.get_project(graph.project_id)
    ctx = GateContext(graph=graph, thresholds=resolve(thresholds), callspec=callspec or load_callspec(graph),
                      scope=ScopeConfig.load(project) if project is not None else None,
                      stages=dict(project.stages) if project is not None else {})
    ...  # rest unchanged
```

```python
    def check(self, project_id: str, gate: str, write: bool = True,
              pack_thresholds: dict[str, float] | None = None) -> GateResult:
        graph = Graph(self.store, project_id)
        project = self.store.get_project(project_id)
        result = evaluate_gate(gate, graph, resolve(self.thresholds, pack_thresholds), project=project)
        if write and project is not None:
            entry = project.gates.setdefault(normalize_gate(gate), {})
            entry["passed"] = result.passed
            entry["checked_at"] = result.checked_at
            entry["not_applicable"] = result.not_applicable
            entry["blockers"] = result.blockers
            self.store.put_project(project)
        return result
```

- [ ] **Step 4: Run the gate tests and fix the existing ones**

Run: `.venv/bin/python -m pytest tests/test_gates.py -q`

`test_scope_gate` will now fail at its last assertion because the scope is unconfigured and the concept is preliminary. Update its tail:

```python
    spec.requirements[0].status = "met"
    ws.set_scope("demo", {})
    ws.set_concept_status("demo", "aligned")
    r = evaluate_gate("scope", g, callspec=spec)
    assert r.passed, r.blockers
```

Expected after the fix: all pass.

- [ ] **Step 5: Commit**

```bash
git add agency/policy/gates.py tests/test_gates.py
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "Gates: scope configured, concept aligned, required modules, external review rules

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014jWan98ut6ZUHkmXMG2bqW"
```

---

### Task 4: Engine enforces scope; drafting skips excluded finance sections

**Files:**
- Modify: `agency/engine/plan.py:38-47`, `agency/engine/runner.py:45-63`, `agency/engine/runtime.py` (RunContext), `agency/jobs/drafting.py:585-637`, `agency/jobs/finance.py:34`, `agency/jobs/figures.py:30`, `agency/jobs/business_plan.py:41`, `agency/jobs/feedback.py:47`
- Test: `tests/test_engine.py`, `tests/test_pipeline_stages.py`

**Interfaces:**
- Consumes: `ScopeConfig`, `Workspace.set_scope`.
- Produces: `StageDef.scope_key: str | None`; `RunContext.scope() -> ScopeConfig | None`; `draftable_sections(spec, only=None, scope=None)`.

- [ ] **Step 1: Write the failing tests (append to `tests/test_engine.py`)**

```python
async def test_excluded_stage_is_blocked_unless_forced(ws, project):
    from agency.domain.scope import ScopeConfig
    ws.set_scope("demo", {"figures": "excluded"})
    eng = Engine(ws, query_fn=FakeQuery())
    with pytest.raises(StageBlocked, match="excluded by the project scope"):
        await eng.run_stage("demo", "figures")
    run = await eng.run_stage("demo", "figures", force=True)     # empty register → completes with nothing to do
    assert run.status in (RunStatus.COMPLETED, RunStatus.FAILED)
    assert ScopeConfig.load(ws.get_project("demo")).figures.state == "included"
    d = ws.graph("demo").decisions("scope_changed")
    assert any("figures: excluded -> included" in x.data["decision"] for x in d)
    assert STAGES["figures"].scope_key == "figures" and STAGES["finance"].scope_key == "finance"
    assert STAGES["business-plan"].scope_key == "business_plan"
    assert STAGES["external-feedback"].scope_key == "external_review"
    assert STAGES["research"].scope_key is None


def test_draftable_sections_skip_excluded_finance(ws, project):
    from agency.domain.callspec import CallSpec
    from agency.domain.scope import apply_scope_change, derive_scope
    from agency.jobs.drafting import draftable_sections
    spec = CallSpec.model_validate(dict(CALLSPEC, sections=CALLSPEC["sections"] + [
        {"id": "4", "title": "Financial maturity", "kind": "financial"}]))
    scope = derive_scope(spec)                                     # finance required by the call
    assert "4" in [s.id for s, _ in draftable_sections(spec, scope=scope)]
    excluded = derive_scope(CallSpec.model_validate(CALLSPEC))     # a call without financials → excluded
    assert "4" not in [s.id for s, _ in draftable_sections(spec, scope=excluded)]
    assert "4" in [s.id for s, _ in draftable_sections(spec)]      # no scope → unchanged behaviour
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_engine.py -q -k "excluded or draftable"`
Expected: FAIL (`StageBlocked` not raised; `scope_key` attribute missing; `draftable_sections() got an unexpected keyword argument 'scope'`)

- [ ] **Step 3: Implement**

`agency/engine/plan.py`, in `StageDef`:

```python
    flags: dict[str, str] = field(default_factory=dict)   # flag -> help
    scope_key: str | None = None                          # module in ScopeConfig that governs this stage
```

`agency/engine/runner.py`, add the import `from agency.domain.scope import ScopeConfig` and extend `check_prerequisites` before the `requires_gate` block:

```python
        if sd.scope_key:
            scope = ScopeConfig.load(project)
            if scope is not None and scope.is_excluded(sd.scope_key):
                if not force:
                    raise StageBlocked(f"stage '{sd.name}' is excluded by the project scope; "
                                       f"run with --force to include it")
                self.ws.set_scope(project_id, {sd.scope_key: "included"}, by="engine",
                                  reason=f"forced run of {sd.name}")
                warnings.append(f"scope: {sd.scope_key} switched to included")
```

`agency/engine/runtime.py`, in `RunContext` after `callspec()`:

```python
    def scope(self):
        from agency.domain.scope import ScopeConfig
        return ScopeConfig.load(self.ws.get_project(self.project_id))
```

`agency/jobs/drafting.py`:

```python
def draftable_sections(spec: CallSpec, only: list[str] | None = None, scope=None) -> list[tuple[SectionSpec, str]]:
    out = []
    for s in spec.sections:
        if not s.required:
            continue
        if only and s.id not in only:
            continue
        if s.kind == "financial" and scope is not None and scope.is_excluded("finance"):
            continue
        w = writer_for(s)
        if w is None:
            continue
        out.append((s, w))
    return out
```

In `plan_write`, replace `sections = draftable_sections(spec, only)` with:

```python
    scope = ctx.scope()
    sections = draftable_sections(spec, only, scope)
    notes = [f"section {s.id} ({s.title}) skipped: finance excluded by scope"
             for s in spec.sections if s.kind == "financial" and s.required and scope is not None
             and scope.is_excluded("finance")]
```

and delete the later `notes = []` line. In `prepare`, use `draftable_sections(spec, scope=rt.ctx.scope())`.

Stage definitions — add `scope_key=` to each `stage(StageDef(...))` call:

- `agency/jobs/finance.py`: `scope_key="finance"`
- `agency/jobs/figures.py`: `scope_key="figures"`
- `agency/jobs/business_plan.py`: `scope_key="business_plan"`
- `agency/jobs/feedback.py`: `scope_key="external_review"`

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/test_engine.py tests/test_pipeline_stages.py tests/test_interactive_stages.py -q`
Expected: all pass (the interactive finance test runs with an unconfigured scope, which does not block).

- [ ] **Step 5: Commit**

```bash
git add agency/engine/plan.py agency/engine/runner.py agency/engine/runtime.py agency/jobs/drafting.py agency/jobs/finance.py agency/jobs/figures.py agency/jobs/business_plan.py agency/jobs/feedback.py tests/test_engine.py
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "Engine: scope_key on stages, excluded stages blocked unless forced, drafting honours scope

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014jWan98ut6ZUHkmXMG2bqW"
```

---

### Task 5: ConceptAlignment model and the shared hypothesis writer; ideate sets concept status

**Files:**
- Modify: `agency/domain/models.py` (after `IdeationBrief`), `agency/jobs/common.py`, `agency/jobs/ideate.py:387-398`
- Test: `tests/test_interactive_stages.py::test_ideate`, `tests/test_scope.py` (append)

**Interfaces:**
- Produces:
  - `class CriterionFit(Payload)`, `class ConceptAlignment(Payload)` in `agency/domain/models.py`
  - `replace_hypothesis(graph, block: str, statement: str, *, created_by=None, concept_status: str) -> None` in `agency/jobs/common.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_scope.py`:

```python
def test_replace_hypothesis_sets_status(ws, project):
    from agency.jobs.common import replace_hypothesis
    g = ws.graph("demo")
    replace_hypothesis(g, "New idea\n\n**Mechanism**: x", "New idea", created_by="t", concept_status="aligned")
    doc = g.document("context")
    assert doc.data["hypothesis"] == "New idea" and doc.data["concept_status"] == "aligned"
    assert doc.data["body"].count("## Hypothesis") == 1 and "**Mechanism**: x" in doc.data["body"]
    from agency.domain.models import ConceptAlignment
    al = ConceptAlignment(overall_fit=7, verdict="fits", criterion_fits=[], rationale="ok")
    assert al.suggested_hypothesis is None
```

In `tests/test_interactive_stages.py::test_ideate`, add after the hypothesis assertion:

```python
    assert g.document("context").data["concept_status"] == "preliminary"   # no call at ideation time
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_scope.py::test_replace_hypothesis_sets_status tests/test_interactive_stages.py::test_ideate -q`
Expected: FAIL (`ImportError: cannot import name 'replace_hypothesis'`; KeyError `concept_status`)

- [ ] **Step 3: Implement**

`agency/domain/models.py`, after `class IdeationBrief`:

```python
class CriterionFit(Payload):
    criterion_id: str
    fit: float = Field(ge=0, le=10)
    comment: str = ""


class ConceptAlignment(Payload):
    """parse-call align_concept output: how a preliminary hypothesis fits the parsed call."""
    overall_fit: float = Field(ge=0, le=10)
    verdict: Literal["fits", "fits_with_changes", "does_not_fit"]
    criterion_fits: list[CriterionFit] = Field(default_factory=list)
    scope_misfits: list[str] = Field(default_factory=list)
    eligibility_conflicts: list[str] = Field(default_factory=list)
    suggested_hypothesis: str | None = None
    rationale: str = ""
```

`agency/jobs/common.py`, add `import re` and:

```python
def replace_hypothesis(graph, block: str, statement: str, *, created_by: str | None = None,
                       concept_status: str) -> None:
    """Rewrite the `## Hypothesis` block of the context document and set hypothesis + concept status."""
    doc = graph.document("context")
    body = doc.data.get("body", "") if doc else ""
    if "## Hypothesis" in body:
        body = re.sub(r"## Hypothesis\s*\n.*?(?=\n## |\Z)", f"## Hypothesis\n\n{block}\n", body, count=1, flags=re.S)
    else:
        body += f"\n\n## Hypothesis\n\n{block}\n"
    graph.put_document("context", doc.data.get("title", "context") if doc else "context", body,
                       created_by=created_by, hypothesis=statement, concept_status=concept_status)
```

`agency/jobs/ideate.py`, in `choose`, replace the block from `ctx_doc = rt.graph.document("context")` through `rt.graph.put_document("context", ...)` with:

```python
    hyp = f"{chosen.statement}\n\n**Mechanism**: {chosen.mechanism}\n\n**Novelty type**: {chosen.novelty_type} — target gap: {chosen.target_gap}"
    replace_hypothesis(rt.graph, hyp, chosen.statement, created_by=rt.job.id,
                       concept_status="aligned" if rt.graph.callspec_node() is not None else "preliminary")
```

and add `from agency.jobs.common import replace_hypothesis` to the imports. Keep `import re` (the rework branch still uses `re.match`).

Update the `ideate` stage description in the same file so the UI and planner brief say what exploratory mode means:

```python
               description="Develop the idea with you: interview, candidate framings, shallow prior-art probes, "
                           "comparative scoring, and a chosen hypothesis written into the context. Without a parsed "
                           "call this is exploratory: the hypothesis is marked preliminary and parse-call aligns it later.",
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/test_scope.py tests/test_interactive_stages.py -q`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add agency/domain/models.py agency/jobs/common.py agency/jobs/ideate.py tests/test_scope.py tests/test_interactive_stages.py
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "ConceptAlignment model; shared hypothesis writer; ideate records concept status

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014jWan98ut6ZUHkmXMG2bqW"
```

---

### Task 6: parse-call gains configure_scope and align_concept

**Files:**
- Modify: `agency/jobs/parse_call.py`
- Test: `tests/test_engine.py` (responder + end-to-end asserts), `tests/test_pipeline_stages.py`, `tests/test_interactive_stages.py` (responders)

**Interfaces:**
- Consumes: Tasks 1, 2, 5.
- Produces: handlers `parse_call.configure_scope`, `parse_call.align_concept`; flags `scope_only`, `align_only`; `scope_form_schema(scope) -> dict`; document kind `concept_alignment`; inbox keys `configure_scope`, `configure_scope_retry`, `align_decision`; header `"Configure proposal scope"`, `"Align the concept with the call"`.

- [ ] **Step 1: Update the test responders so the fake SDK answers the alignment call**

`tests/test_engine.py`, add after `CALLSPEC`:

```python
ALIGNMENT = {"overall_fit": 7.5, "verdict": "fits_with_changes",
             "criterion_fits": [{"criterion_id": "C1", "fit": 8, "comment": "strong on excellence"}],
             "scope_misfits": [], "eligibility_conflicts": [],
             "suggested_hypothesis": "A validated digital twin cuts scrap by 10% in LFP cathode plants",
             "rationale": "fits the excellence criterion; quantify impact"}
```

and in `responder`, before the final `return`:

```python
    if "idea_evaluator" in head and "CALL ALIGNMENT CHECK" in prompt:
        return {"structured": ALIGNMENT}
```

`tests/test_interactive_stages.py`, in `InteractiveScripted.__call__`, change the line
`if agent == "idea_evaluator":` to `if agent == "idea_evaluator" and "Candidate framings:" in prompt:`
(alignment prompts fall through to the shared responder). In `Answerer.__call__`, FORM branch, add before the financial check:

```python
            if "scope" in item.header.lower():
                return {"data": {"finance": "included", "business_plan": "included", "figures": "included",
                                 "external_review": "excluded"}}
```

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_engine.py`:

```python
async def test_parse_call_configures_scope_and_aligns_the_concept(ws, project, engine):
    from agency.domain.scope import ScopeConfig
    run = await engine.run_stage("demo", "parse-call")
    assert run.status == RunStatus.COMPLETED, run.error
    jobs = {j.name: j for j in ws.store.list_jobs(run.id)}
    assert jobs["configure_scope"].status == JobStatus.COMPLETED and jobs["align_concept"].status == JobStatus.COMPLETED
    scope = ScopeConfig.load(ws.get_project("demo"))
    assert scope.configured_at and scope.finance.state == "excluded"        # CALLSPEC has no financials
    g = ws.graph("demo")
    assert g.decisions("scope_configured") and g.decisions("concept_alignment")
    assert ws.concept_status("demo") == "aligned"                            # AutoApprove answers "yes" → keep
    assert g.document("concept_alignment").data["verdict"] == "fits_with_changes"
    kinds = [i.kind for i in engine.inbox.responder.items]
    assert kinds == [InboxKind.FORM, InboxKind.APPROVAL, InboxKind.FORM, InboxKind.QUESTION]
    assert engine.inbox.responder.items[2].header == "Configure proposal scope"
    # scope_only re-runs just the form; align_only refuses when nothing is preliminary
    run2 = await engine.run_stage("demo", "parse-call", flags={"scope_only": "1"})
    assert run2.status == RunStatus.COMPLETED and {j.name for j in ws.store.list_jobs(run2.id)} == {"configure_scope", "finalize"}
    run3 = await engine.run_stage("demo", "parse-call", flags={"align_only": "1"})
    assert run3.status == RunStatus.FAILED and "nothing to align" in run3.error


async def test_align_concept_adopt_and_reopen(ws, project):
    class Chooser(AutoApprove):
        def __init__(self, pick):
            super().__init__()
            self.pick = pick

        async def __call__(self, item):
            if item.kind == InboxKind.QUESTION and item.header.startswith("Align"):
                self.items.append(item)
                opts = item.payload["options"]
                assert opts[0].startswith("keep") and opts[1].startswith("adopt") and opts[2].startswith("reopen")
                return {"choice": opts[self.pick]}
            return await super().__call__(item)

    eng = Engine(ws, query_fn=FakeQuery(responder))
    eng.inbox.responder = Chooser(1)                                   # adopt
    run = await eng.run_stage("demo", "parse-call")
    assert run.status == RunStatus.COMPLETED, run.error
    ctx = ws.graph("demo").document("context").data
    assert ctx["hypothesis"] == ALIGNMENT["suggested_hypothesis"] and ctx["concept_status"] == "aligned"
    assert any(d.data["decision"] == "adopted" for d in ws.graph("demo").decisions("concept_alignment"))
    # reopen keeps it preliminary and the scope gate stays closed on alignment
    ws.set_concept_status("demo", "preliminary")
    eng.inbox.responder = Chooser(2)
    run = await eng.run_stage("demo", "parse-call", flags={"align_only": "1"})
    assert run.status == RunStatus.COMPLETED, run.error
    assert ws.concept_status("demo") == "preliminary"
    assert any("not aligned" in b for b in ws.check_gate("demo", "scope").blockers)


async def test_parse_call_scope_only_needs_a_callspec(ws, project):
    eng = Engine(ws, query_fn=FakeQuery(responder))
    run = await eng.run_stage("demo", "parse-call", flags={"scope_only": "1"})
    assert run.status == RunStatus.FAILED and "parse the call first" in run.error
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_engine.py -q -k "configures_scope or align_concept or scope_only"`
Expected: FAIL (`KeyError: 'configure_scope'`)

- [ ] **Step 4: Implement in `agency/jobs/parse_call.py`**

Imports (add):

```python
from agency.domain.models import ConceptAlignment
from agency.domain.scope import MODULES, MODULE_LABEL, STATES, ScopeConfig, apply_scope_change, hypothesis_of, rederive
from agency.jobs.common import replace_hypothesis
```

Replace `plan_parse_call` and the `stage(...)` registration:

```python
SCOPE_HEADER = "Configure proposal scope"
ALIGN_HEADER = "Align the concept with the call"


def plan_parse_call(ctx: RunContext) -> StagePlan:
    if ctx.flags.get("scope_only") or ctx.flags.get("align_only"):
        if ctx.callspec() is None:
            raise JobFailed("parse the call first")
        if ctx.flags.get("align_only"):
            if ctx.ws.concept_status(ctx.project_id) != "preliminary":
                raise JobFailed("nothing to align: the concept is not preliminary")
            first = JobSpec("align_concept", "parse_call.align_concept", kind=JobKind.AGENT, contract="idea_evaluator")
        else:
            first = JobSpec("configure_scope", "parse_call.configure_scope", kind=JobKind.INBOX)
        return StagePlan("parse-call", [first, JobSpec("finalize", "finalize_stage", kind=JobKind.GATE,
                                                       deps=[first.name], params={"gate": "scope"})])
    jobs = [
        JobSpec("locate_inputs", "parse_call.locate", kind=JobKind.CODE),
        JobSpec("parse_call", "parse_call.parse", kind=JobKind.AGENT, deps=["locate_inputs"], contract="call_parser"),
        JobSpec("parse_eligibility", "parse_call.eligibility", kind=JobKind.AGENT, deps=["locate_inputs"],
                contract="eligibility_parser", optional=True),
        JobSpec("merge_spec", "parse_call.merge", kind=JobKind.CODE, deps=["parse_call", "parse_eligibility"]),
        JobSpec("approve_outline", "parse_call.approve", kind=JobKind.INBOX, deps=["merge_spec"]),
        JobSpec("configure_scope", "parse_call.configure_scope", kind=JobKind.INBOX, deps=["approve_outline"]),
    ]
    last = "configure_scope"
    if ctx.ws.concept_status(ctx.project_id) == "preliminary":
        jobs.append(JobSpec("align_concept", "parse_call.align_concept", kind=JobKind.AGENT,
                            deps=["configure_scope"], contract="idea_evaluator"))
        last = "align_concept"
    jobs.append(JobSpec("finalize", "finalize_stage", kind=JobKind.GATE, deps=[last], params={"gate": "scope"}))
    return StagePlan(stage="parse-call", jobs=jobs)


stage(StageDef(name="parse-call", state_key="call_parsing", planner=plan_parse_call, interactive=True,
               description="Parse the funding call into a CallSpec, build the outline, confirm with the user, "
                           "configure the proposal scope and align a preliminary concept with the call.",
               flags={"call_file": "path or name of the call document inside inputs/",
                      "template_file": "official application template to follow exactly",
                      "pack": "force a funder pack id (innovation-fund, horizon-europe-ria, nih-r01, nsf, generic)",
                      "scope_only": "only (re)configure the scope for an already parsed call",
                      "align_only": "only align a preliminary concept with the parsed call"}))
```

Append the handlers at the end of the file:

```python
# ------------------------------------------------------------------ scope configuration

def scope_form_schema(scope: ScopeConfig) -> dict[str, Any]:
    props: dict[str, Any] = {}
    for m in MODULES:
        mod = scope.module(m)
        locked = scope.locked(m)
        props[m] = {"type": "string", "title": MODULE_LABEL[m],
                    "enum": ["required"] if locked else list(STATES),
                    "description": mod.reason + (" (required by the call; cannot be changed)" if locked else "")}
        if locked:
            props[m]["readOnly"] = True
    return {"type": "object", "properties": props}


def _read_scope_answer(proposed: ScopeConfig, answer: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    data = answer.get("data") or {}
    chosen, notes = {}, []
    for m in MODULES:
        value = data.get(m)
        if value in STATES:
            chosen[m] = value
        else:
            notes.append(f"{m}: derived value '{proposed.state(m)}' used")
    return chosen, notes


@handler("parse_call.configure_scope")
async def configure_scope(rt: JobRuntime) -> dict[str, Any]:
    ws, pid = rt.ws, rt.project_id
    derived = ws.recommend_scope(pid)
    current = ws.get_scope(pid)
    proposed = rederive(current, derived) if current is not None else derived
    question = ("User preference controls optional work; call requirements control mandatory work. "
                "Choose for each module whether it is excluded, included or required.")
    example = {m: proposed.state(m) for m in MODULES}
    answer = await rt.form(SCOPE_HEADER, question, scope_form_schema(proposed), key="configure_scope", example=example)
    chosen, notes = _read_scope_answer(proposed, answer)
    try:
        scope = apply_scope_change(proposed, chosen, by="researcher", reason="confirmed at intake")
    except ValueError as e:
        answer = await rt.form(SCOPE_HEADER, f"{e}. {question}", scope_form_schema(proposed),
                               key="configure_scope_retry", example=example)
        chosen, more = _read_scope_answer(proposed, answer)
        notes += more
        try:
            scope = apply_scope_change(proposed, chosen, by="researcher", reason="confirmed at intake")
        except ValueError as e2:
            notes.append(f"kept the derived value for invalid choices: {e2}")
            scope = proposed
            for m, s in chosen.items():                       # apply the valid choices, skip the offending ones
                try:
                    scope = apply_scope_change(scope, {m: s}, by="researcher", reason="confirmed at intake")
                except ValueError:
                    continue
            scope = apply_scope_change(scope, {}, by="engine", reason="derived values kept")
    ws.put_scope(pid, scope)
    rt.log_decision("Which optional modules does the proposal include?", scope.summary(),
                    [f"{m}: {scope.module(m).reason}" for m in MODULES] + notes, type="scope_configured")
    rt.emit("scope:configured", scope=scope.model_dump(mode="json"))
    return {"scope": scope.model_dump(mode="json"), "summary": scope.summary()}


# ------------------------------------------------------------------ concept alignment

@handler("parse_call.align_concept")
async def align_concept(rt: JobRuntime) -> dict[str, Any]:
    spec = rt.ctx.callspec()
    if spec is None:
        raise JobFailed("parse the call first")
    ctx_doc = rt.graph.document("context")
    hyp = hypothesis_of(ctx_doc)
    d = rt.project_dir
    inputs = [("research context", str(d / "context.md")),
              ("call spec", str(d / "intermediate" / "call_spec.json")),
              ("proposal outline", str(d / "intermediate" / "proposal_outline.md"))]
    if (d / "intermediate" / "ideation_brief.json").exists():
        inputs.append(("ideation brief", str(d / "intermediate" / "ideation_brief.json")))
    crit_ids = ", ".join(c.id for c in spec.criteria) or "none parsed"
    instructions = f"""CALL ALIGNMENT CHECK — not a framing evaluation. The hypothesis below was developed before the
call was parsed. Assess how well it fits `{spec.title}` ({spec.funder}, {spec.instrument or 'n/a'}).
Hypothesis: {hyp}
Return a `ConceptAlignment`: one `criterion_fits` entry per evaluation criterion (ids: {crit_ids}); `scope_misfits`
for TRL, geography, consortium, duration, budget or topic mismatches; `eligibility_conflicts` for requirements the
idea may violate; `suggested_hypothesis` only when changes would improve the fit (null when it fits as is);
`verdict` fits | fits_with_changes | does_not_fit; `rationale` in 3-8 sentences."""
    res = await rt.agent("idea_evaluator", phase="align", inputs=inputs, instructions=instructions,
                         output_model=ConceptAlignment, allowed_writes=set())
    al = ConceptAlignment.model_validate(res.structured)
    rt.graph.put_document("concept_alignment", "Concept alignment with the call", al.rationale,
                          created_by=rt.job.id, **al.model_dump(mode="json", exclude={"rationale"}))
    suggested = (al.suggested_hypothesis or "").strip()
    options = ["keep the hypothesis as is"]
    if suggested and suggested != hyp:
        options.append("adopt the suggested hypothesis")
    options.append("reopen ideation")
    lines = [f"Verdict: {al.verdict} (overall fit {al.overall_fit:g}/10).", al.rationale]
    if al.scope_misfits:
        lines.append("Scope misfits: " + "; ".join(al.scope_misfits))
    if al.eligibility_conflicts:
        lines.append("Eligibility conflicts: " + "; ".join(al.eligibility_conflicts))
    if "adopt the suggested hypothesis" in options:
        lines.append(f"Suggested hypothesis: {suggested}")
    ans = await rt.ask("\n\n".join(lines), options, header=ALIGN_HEADER, key="align_decision")
    choice = str(ans.get("choice") or ans.get("text") or "").strip().lower()
    question = "Does the preliminary concept fit the call?"
    if choice.startswith("reopen"):
        rt.log_decision(question, "reopen_ideation", [al.rationale], type="concept_alignment")
        return {"verdict": al.verdict, "decision": "reopen_ideation",
                "summary": "concept sent back to ideation (still preliminary)"}
    if choice.startswith("adopt") and "adopt the suggested hypothesis" in options:
        replace_hypothesis(rt.graph, suggested, suggested, created_by=rt.job.id, concept_status="aligned")
        rt.log_decision(question, "adopted", [f"previous hypothesis: {hyp}", al.rationale], type="concept_alignment")
        rt.ctx.materialize()
        return {"verdict": al.verdict, "decision": "adopted", "summary": "suggested hypothesis adopted; concept aligned"}
    rt.ws.set_concept_status(rt.project_id, "aligned")
    rt.log_decision(question, "kept", [al.rationale], type="concept_alignment")
    return {"verdict": al.verdict, "decision": "kept", "summary": f"concept aligned ({al.verdict})"}
```

- [ ] **Step 5: Run the affected suites and update the end-to-end assertions**

Run: `.venv/bin/python -m pytest tests/test_engine.py tests/test_pipeline_stages.py tests/test_interactive_stages.py tests/test_planner.py -q`

`test_parse_call_then_research_end_to_end` still passes (the extra inbox items are answered by `AutoApprove`; `items[0]` is still the call-text form). If `test_campaign_*` fail because the align question is answered with "yes", that maps to keep and is fine; investigate any other failure rather than loosening assertions.

Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add agency/jobs/parse_call.py tests/test_engine.py tests/test_interactive_stages.py
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "parse-call: configure the scope in the inbox and align a preliminary concept with the call

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014jWan98ut6ZUHkmXMG2bqW"
```

---

### Task 7: Guide becomes call-first and scope-aware

**Files:**
- Modify: `agency/policy/guide.py`
- Test: `tests/test_guide.py`

**Interfaces:**
- Consumes: `Workspace.get_scope`, `Workspace.concept_status`, `MODULE_STATE_KEY`.
- Produces: `MAIN_PATH` order Call, Idea, Research, Draft, Review, Export; `STAGE_ORDER` starting `parse-call`, `ideate`; `next_step()` result gains `scope` and each `side` entry gains `scope_state`; step keys `configure_scope`, `align_concept`.

- [ ] **Step 1: Rewrite the guide tests**

Replace `tests/test_guide.py` with:

```python
"""Guidance: the deterministic 'what next' every surface shows."""
from agency.domain.graph import NodeType
from agency.policy.guide import next_step
from tests.test_engine import CALLSPEC


def test_guidance_walks_the_main_path(ws, project):
    pid = "demo"
    s = next_step(ws, pid)
    assert s["key"] == "upload_call" and s["action"]["kind"] == "upload_then_run"
    assert [p["label"] for p in s["path"]] == ["Call", "Idea", "Research", "Draft", "Review", "Export"]
    assert any("exploratory" in a for a in s["alternatives"]) and s["scope"] is None
    inputs = ws.config.project_dir(pid) / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    (inputs / "call.txt").write_text("call text")
    assert next_step(ws, pid)["action"] == {"kind": "run_stage", "stage": "parse-call"}
    g = ws.graph(pid)
    g.add(NodeType.CALL_SPEC, dict(CALLSPEC))
    ws.set_stage(pid, "call_parsing", "complete")
    # parsed but unconfigured scope → configure it (scope_only), then align the preliminary concept
    s = next_step(ws, pid)
    assert s["key"] == "configure_scope" and s["action"] == {"kind": "run_stage", "stage": "parse-call", "flags": {"scope_only": "1"}}
    ws.set_scope(pid, {})
    s = next_step(ws, pid)
    assert s["key"] == "align_concept" and s["action"]["flags"] == {"align_only": "1"}
    ws.set_concept_status(pid, "aligned")
    s = next_step(ws, pid)
    assert s["key"] == "confirm_eligibility" and [r["id"] for r in s["requirements"]] == ["E1"]
    ws.set_requirement_status(pid, "E1", "met", "three partners confirmed")
    assert next_step(ws, pid)["action"] == {"kind": "run_stage", "stage": "research"}
    g.put_document("outline", "Outline", "## 1. Excellence\n## 2. Impact\n## 3. Implementation")
    assert ws.check_gate(pid, "scope").passed is True
    ws.set_stage(pid, "research", "complete")
    ws.check_gate(pid, "evidence")
    assert next_step(ws, pid)["key"] == "evidence_gate"
    ws.set_stage(pid, "writing", "complete")
    assert next_step(ws, pid)["action"]["stage"] == "review"
    ws.set_stage(pid, "review", "complete")
    ws.check_gate(pid, "submission")
    assert next_step(ws, pid)["key"] == "submission_gate"
    ws.set_stage(pid, "export", "complete")
    s = next_step(ws, pid)
    assert s["key"] == "done" and s["action"]["kind"] == "none"          # external review excluded → not suggested


def test_guidance_call_first_then_ideation(ws):
    ws.create_project("Blank", project_id="blank")
    s = next_step(ws, "blank")
    assert s["key"] == "upload_call" and any("exploratory" in a for a in s["alternatives"])
    ws.set_stage("blank", "ideation", "skipped")
    assert next_step(ws, "blank")["key"] == "upload_call"
    g = ws.graph("blank")
    g.add(NodeType.CALL_SPEC, dict(CALLSPEC))
    ws.set_stage("blank", "call_parsing", "complete")
    ws.set_scope("blank", {})
    ws.set_stage("blank", "ideation", "pending")
    assert next_step(ws, "blank")["key"] == "ideate"
    from agency.domain.runs import InboxItem, InboxKind
    ws.store.put_inbox(InboxItem(id="i1", project_id="blank", kind=InboxKind.QUESTION, header="Q", question="Continue?",
                                 payload={}))
    s = next_step(ws, "blank")
    assert s["key"] == "inbox" and s["action"]["kind"] == "inbox"
    assert "next_step" in ws.status("blank")


def test_guidance_recommends_included_modules_and_hides_excluded(ws, project):
    pid = "demo"
    g = ws.graph(pid)
    g.add(NodeType.CALL_SPEC, dict(CALLSPEC))
    for key in ("call_parsing", "research"):
        ws.set_stage(pid, key, "complete")
    ws.set_concept_status(pid, "aligned")
    ws.set_scope(pid, {"finance": "included", "business_plan": "required", "figures": "excluded", "external_review": "included"})
    ws.set_requirement_status(pid, "E1", "met")
    ws.graph(pid).put_document("outline", "Outline", "## 1. x")
    s = next_step(ws, pid)
    assert s["key"] == "finance"                                # included finance comes before drafting
    side = {p["key"]: p for p in s["side"]}
    assert side["figures"]["scope_state"] == "excluded" and side["business_plan"]["scope_state"] == "required"
    ws.set_stage(pid, "finance", "complete")
    ws.set_stage(pid, "writing", "complete")
    assert next_step(ws, pid)["key"] == "business_plan"
    ws.set_stage(pid, "business_plan", "complete")
    assert next_step(ws, pid)["key"] not in ("figures",)       # excluded → never recommended
    for key in ("review", "export"):
        ws.set_stage(pid, key, "complete")
    s = next_step(ws, pid)
    assert s["key"] == "done" and s["action"]["stage"] == "external-feedback"


def test_requirement_status_validation(ws, project):
    import pytest
    with pytest.raises(KeyError):
        ws.set_requirement_status("demo", "E1", "met")        # no call spec yet
    ws.graph("demo").add(NodeType.CALL_SPEC, dict(CALLSPEC))
    with pytest.raises(ValueError):
        ws.set_requirement_status("demo", "E1", "maybe")
    with pytest.raises(KeyError):
        ws.set_requirement_status("demo", "E9", "met")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_guide.py -q`
Expected: 3 failures (path order, missing keys)

- [ ] **Step 3: Rewrite `agency/policy/guide.py`**

```python
"""Deterministic guidance: what the researcher should do next, derived from project state.

The UI's Overview, `agency next` and the planning brief all use this so every surface tells
the same story. No model calls; pure rules over stage statuses, gates, inbox, runs, scope and the CallSpec.
"""
from __future__ import annotations

from typing import Any

from agency.domain.callspec import CallSpec
from agency.domain.runs import RunStatus
from agency.domain.scope import MODULE_STATE_KEY, ScopeConfig, concept_status_of

MAIN_PATH: list[tuple[str, str, str]] = [   # (state key, label, stage name)
    ("call_parsing", "Call", "parse-call"),
    ("ideation", "Idea", "ideate"),
    ("research", "Research", "research"),
    ("writing", "Draft", "write-proposal"),
    ("review", "Review", "review"),
    ("export", "Export", "export"),
]
SIDE_PATH: list[tuple[str, str, str]] = [
    ("finance", "Finance", "finance"),
    ("figures", "Figures", "figures"),
    ("business_plan", "Business plan", "business-plan"),
    ("external_review", "External feedback", "external-feedback"),
]
STAGE_ORDER = ["parse-call", "ideate", "research", "finance", "write-proposal", "business-plan", "figures",
               "review", "external-feedback", "export", "plan"]
OPTIONAL_STAGE_NAMES = {"ideate", "finance", "figures", "business-plan", "external-feedback", "plan"}
EXPLORATORY = "Or run an exploratory ideation now; it will be aligned to the call afterwards."


def _step(key: str, title: str, why: str, action: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    return {"key": key, "title": title, "why": why, "action": action or {"kind": "none"}, **extra}


def next_step(ws, project_id: str) -> dict[str, Any]:
    project = ws.require_project(project_id)
    stages, gates = project.stages, project.gates
    graph = ws.graph(project_id)
    scope = ScopeConfig.load(project)

    def st(key: str) -> str:
        return stages.get(key, {}).get("status", "pending")

    def done(key: str) -> bool:
        return st(key) in ("complete", "skipped")

    def gate_failed(name: str) -> list[str]:
        g = gates.get(name, {})
        if g.get("checked_at") and not g.get("passed") and not g.get("not_applicable"):
            return list(g.get("blockers") or ["not passed"])
        return []

    def module_state(key: str) -> str | None:
        module = next((m for m, k in MODULE_STATE_KEY.items() if k == key), None)
        return scope.state(module) if (scope is not None and module) else None

    path = [{"key": k, "label": lbl, "stage": s, "status": st(k), "optional": False} for k, lbl, s in MAIN_PATH]
    side = [{"key": k, "label": lbl, "stage": s, "status": st(k), "optional": True, "scope_state": module_state(k)}
            for k, lbl, s in SIDE_PATH]
    result = _guidance(ws, project_id, project, graph, scope, st, done, gate_failed)
    result["path"] = path
    result["side"] = side
    result["scope"] = scope.model_dump(mode="json") if scope is not None else None
    stage_name = result["action"].get("stage")
    if stage_name:
        last = next((r for r in ws.store.list_runs(project_id=project_id) if r.stage == stage_name), None)
        if last and last.status in (RunStatus.FAILED, RunStatus.STOPPED, RunStatus.INTERRUPTED):
            result["last_run"] = {"id": last.id, "status": last.status.value, "error": last.error}
            result["action"]["resume"] = last.id
            result["why"] += f" The last {stage_name} run {last.status.value}" + (f": {last.error[:200]}" if last.error else ".") + \
                " Resume it to reuse the completed jobs."
    return result


def _wanted(scope: ScopeConfig | None, module: str) -> bool:
    """Included or required → the guide recommends it; excluded or unconfigured → it does not."""
    return scope is not None and scope.state(module) in ("included", "required")


def _guidance(ws, pid, project, graph, scope, st, done, gate_failed) -> dict[str, Any]:
    pending = ws.store.list_inbox(project_id=pid, status="pending")
    if pending:
        n = len(pending)
        return _step("inbox", f"Answer {n} item{'s' if n > 1 else ''} in the Inbox",
                     f"A run is waiting for you: {pending[0].header} — {pending[0].question[:140]}",
                     {"kind": "inbox"})
    active = [r for r in ws.store.list_runs(project_id=pid)
              if r.status in (RunStatus.RUNNING, RunStatus.WAITING_FOR_USER, RunStatus.QUEUED)]
    if active:
        return _step("running", f"{active[0].stage} is running",
                     "Follow it on the Runs page; the Inbox badge lights up if it needs you.",
                     {"kind": "runs", "run_id": active[0].id})
    if not done("call_parsing"):
        inputs = ws.config.project_dir(pid) / "inputs"
        files = [p for p in inputs.rglob("*") if p.is_file() and not p.name.endswith(".extracted.txt")] if inputs.exists() else []
        if not files:
            return _step("upload_call", "Upload the call document, then parse it",
                         "Everything downstream (sections, criteria, scope, gates) is planned from the parsed call. "
                         "Add the call text or PDF and the official application template if you have one.",
                         {"kind": "upload_then_run", "stage": "parse-call", "subdir": ""},
                         alternatives=["Or run parse-call without a file and paste the call text when asked.", EXPLORATORY])
        return _step("parse_call", "Parse the call",
                     f"{len(files)} input file(s) found. The call parser extracts sections, criteria, requirements "
                     "and limits; you approve the result and configure the scope in the Inbox.",
                     {"kind": "run_stage", "stage": "parse-call"}, alternatives=[EXPLORATORY])
    if scope is None or not scope.configured_at:
        return _step("configure_scope", "Configure the proposal scope",
                     "Decide which optional modules (finance, business plan, figures, external review) the proposal "
                     "includes. Modules the call requires are locked; everything else is your choice.",
                     {"kind": "run_stage", "stage": "parse-call", "flags": {"scope_only": "1"}})
    ctx = graph.document("context")
    concept = concept_status_of(ctx)
    if concept == "none" and not done("ideation"):
        return _step("ideate", "Develop the idea into a hypothesis",
                     "The call is parsed but the project has no hypothesis yet. The ideation interview asks you a "
                     "few batches of questions, probes prior art and scores 2–3 framings against the call; you pick one.",
                     {"kind": "run_stage", "stage": "ideate"},
                     alternatives=["Or write the hypothesis yourself in the project context and skip ideation."])
    if concept == "preliminary":
        return _step("align_concept", "Align the concept with the call",
                     "The hypothesis was written before the call was parsed. An evaluator scores it against the "
                     "call's criteria, scope and eligibility; you keep it, adopt the suggested adjustment, or reopen ideation.",
                     {"kind": "run_stage", "stage": "parse-call", "flags": {"align_only": "1"}})
    spec = _callspec(graph)
    unconfirmed = [r for r in (spec.requirements if spec else []) if r.kind == "eligibility" and r.disqualifying
                   and r.status == "unknown"]
    if not done("research"):
        if unconfirmed:
            return _step("confirm_eligibility", "Confirm eligibility",
                         "The scope gate blocks research until every disqualifying eligibility requirement is "
                         "marked met or not applicable. Decide each one below.",
                         {"kind": "confirm_requirements"},
                         requirements=[{"id": r.id, "text": r.text, "status": r.status} for r in unconfirmed],
                         alternatives=["Or run research with force; that records a gate-override decision."])
        blockers = gate_failed("scope")
        if blockers:
            return _step("scope_gate", "Fix the scope blockers, then run research",
                         "The scope gate failed: " + "; ".join(blockers),
                         {"kind": "run_stage", "stage": "research", "force": True},
                         alternatives=["Re-run parse-call if the call spec is wrong."])
        return _step("research", "Run research",
                     "Retrievers gather literature, repositories and patents in parallel; the synthesizer writes the "
                     "state of the art; novelty anchors and gaps are mapped. Expect the most expensive stage.",
                     {"kind": "run_stage", "stage": "research"})
    if _wanted(scope, "finance") and st("finance") == "pending":
        return _step("finance", "Build the financial model",
                     "Finance is in scope. Drop workbooks into inputs/financials/ or fill the form the stage asks "
                     "for; the modeler computes tables and hard-threshold checks so the financial sections can be drafted.",
                     {"kind": "run_stage", "stage": "finance"},
                     alternatives=["Skip it for now and draft the narrative sections first."])
    if not done("writing"):
        blockers = gate_failed("evidence")
        if blockers:
            return _step("evidence_gate", "Strengthen the evidence before drafting",
                         "The evidence gate failed: " + "; ".join(blockers) +
                         ". Re-run research with a focus on what is missing.",
                         {"kind": "run_stage", "stage": "research", "flags": {"focus": ""}},
                         alternatives=["Or run write-proposal with force."])
        return _step("write", "Draft the proposal",
                     "One writer per section from the call spec; excellence first, impact and implementation in "
                     "parallel, abstract last. Every claim must cite the registry.",
                     {"kind": "run_stage", "stage": "write-proposal"})
    if _wanted(scope, "business_plan") and st("business_plan") == "pending":
        return _step("business_plan", "Build the business-plan annex",
                     "The business plan is in scope. A batched interview collects what no artefact has; "
                     "four writers and a red-team produce the annex.",
                     {"kind": "run_stage", "stage": "business-plan"},
                     alternatives=["Skip it for now and review the narrative sections first."])
    if _wanted(scope, "figures") and st("figures") == "pending":
        return _step("figures", "Render the figures",
                     "Figures are in scope. The figures register is rendered (plots and concept graphics) and indexed "
                     "so drafts can reference them.",
                     {"kind": "run_stage", "stage": "figures"},
                     alternatives=["Skip it for now and review the narrative sections first."])
    if not done("review"):
        blockers = gate_failed("draft")
        if blockers:
            return _step("draft_gate", "Complete the draft before review",
                         "The draft gate failed: " + "; ".join(blockers),
                         {"kind": "run_stage", "stage": "write-proposal"})
        return _step("review", "Review and improve",
                     "Scientific and compliance reviews plus a simulated evaluator panel; the loop redrafts the "
                     "weakest sections until the predicted score plateaus.",
                     {"kind": "run_stage", "stage": "review"})
    if not done("export"):
        blockers = gate_failed("submission")
        if blockers:
            return _step("submission_gate", "Close the submission blockers",
                         "The submission gate failed: " + "; ".join(blockers),
                         {"kind": "run_stage", "stage": "review"},
                         alternatives=["Or export with force for an internal draft."])
        return _step("export", "Export the proposal",
                     "Assembles Markdown and DOCX with a reference list built from cited sources.",
                     {"kind": "run_stage", "stage": "export"})
    if _wanted(scope, "external_review"):
        return _step("done", "Proposal exported",
                     "Send it to colleagues; when their comments come back, drop the files into inputs/reviews/ and "
                     "run external-feedback. Promote what you learned to the knowledge base with `agency kb promote`.",
                     {"kind": "run_stage", "stage": "external-feedback"},
                     alternatives=["Ask the planner for a further improvement campaign."])
    return _step("done", "Proposal exported",
                 "Promote what you learned to the knowledge base with `agency kb promote`. External review is not in "
                 "scope; include it on the Overview if colleagues will comment.",
                 alternatives=["Ask the planner for a further improvement campaign."])


def _callspec(graph) -> CallSpec | None:
    node = graph.callspec_node()
    if node is None:
        return None
    try:
        return CallSpec.model_validate(node.data)
    except Exception:
        return None
```

- [ ] **Step 4: Run guide, server and planner tests; fix the stage-order assertion**

Run: `.venv/bin/python -m pytest tests/test_guide.py tests/test_server.py tests/test_planner.py -q`

`tests/test_server.py::test_next_step_and_requirements_endpoints` fails on two lines. Update them:

```python
    stages = (await client.get("/api/stages")).json()["items"]
    assert [s["name"] for s in stages][:3] == ["parse-call", "ideate", "research"] and stages[1]["optional"] is True
    ...
    client.engine.ws.graph("p4").add(NodeType.CALL_SPEC, dict(CALLSPEC))
    client.engine.ws.set_stage("p4", "call_parsing", "complete")
    assert (await client.get("/api/projects/p4/next")).json()["key"] == "configure_scope"
    client.engine.ws.set_scope("p4", {})
    client.engine.ws.set_concept_status("p4", "aligned")
    assert (await client.get("/api/projects/p4/next")).json()["key"] == "confirm_eligibility"
```

Expected after the fix: all pass

- [ ] **Step 5: Commit**

```bash
git add agency/policy/guide.py tests/test_guide.py tests/test_server.py
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "Guide: call-first path, scope and alignment steps, excluded modules never recommended

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014jWan98ut6ZUHkmXMG2bqW"
```

---

### Task 8: Planner brief and validation respect the scope

**Files:**
- Modify: `agency/jobs/plan.py:501-596, 612-633`
- Test: `tests/test_planner.py`

**Interfaces:**
- Produces: `validate_plan(plan, stages, project_stages, scope=None)`; brief section `## Scope`.

- [ ] **Step 1: Write the failing tests (append to `tests/test_planner.py`)**

```python
def test_validate_plan_rejects_excluded_stages_unless_forced(ws, project):
    scope = ws.set_scope("demo", {"figures": "excluded"})
    plan = RunPlan.model_validate({**GOOD_PLAN, "steps": GOOD_PLAN["steps"] + [
        {"step": 3, "stage": "figures", "rationale": "plots"}]})
    errors = validate_plan(plan, STAGES, ws.get_project("demo").stages, scope)
    assert any("step 3 (figures): excluded by the project scope" in e for e in errors)
    forced = RunPlan.model_validate({**GOOD_PLAN, "steps": GOOD_PLAN["steps"] + [
        {"step": 3, "stage": "figures", "rationale": "plots", "force": True}]})
    assert validate_plan(forced, STAGES, ws.get_project("demo").stages, scope) == []
    assert validate_plan(plan, STAGES, ws.get_project("demo").stages) == []       # no scope → no check


def test_brief_lists_the_scope(ws, project):
    from agency.domain.runs import Run
    from agency.engine.runtime import RunContext
    ws.set_scope("demo", {"finance": "included"})
    eng = Engine(ws, query_fn=FakeQuery(responder))
    run = Run(id="run-y", project_id="demo", stage="plan")
    ctx = RunContext(ws=ws, project_id="demo", run=run, catalogue=eng.catalogue, adapter=eng.adapter, inbox=eng.inbox,
                     packs=eng.packs, project_dir=ws.config.project_dir("demo"), kb_dir=ws.config.root / "kb")
    brief = build_brief(ctx, STAGES, goal="x")
    assert "## Scope" in brief and "- finance: included (user)" in brief and "- figures: excluded (default)" in brief
    assert "scope key: figures" in brief
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_planner.py -q -k "excluded or lists_the_scope"`
Expected: FAIL (`validate_plan() takes 3 positional arguments`; `## Scope` missing)

- [ ] **Step 3: Implement in `agency/jobs/plan.py`**

Add `from agency.domain.scope import MODULES, ScopeConfig` to the imports.

In `build_brief`, after the `## Stage status` block and before `## Gates`:

```python
    scope = ScopeConfig.load(project)
    lines += ["", "## Scope (excluded stages must not be planned unless the step sets force)"]
    if scope is None:
        lines.append("- not configured yet (parse-call asks for it)")
    else:
        lines += [f"- {m}: {scope.state(m)} ({scope.module(m).source})" for m in MODULES]
```

In the `## Available stages` loop, extend the metadata line:

```python
        lines.append(f"- state key: {sd.state_key or 'none'}; requires stages: {', '.join(sd.requires_stages) or 'none'}; "
                     f"entry gate: {sd.requires_gate or 'none'}; interactive: {'yes' if sd.interactive else 'no'}; "
                     f"scope key: {sd.scope_key or 'none'}")
```

Change `validate_plan`:

```python
def validate_plan(plan: RunPlan, stages: dict[str, StageDef], project_stages: dict[str, dict[str, Any]],
                  scope: ScopeConfig | None = None) -> list[str]:
    ...
        sd = stages[s.stage]
        if scope is not None and sd.scope_key and scope.is_excluded(sd.scope_key) and not s.force:
            errors.append(f"step {i} ({s.stage}): excluded by the project scope; change the scope or set force")
        bad = sorted(set(s.flags) - set(sd.flags))
    ...
```

In `propose`, pass the scope: `errors = validate_plan(plan, STAGES, project.stages, ScopeConfig.load(project))`.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/test_planner.py -q`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add agency/jobs/plan.py tests/test_planner.py
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "Planner: brief shows the scope; plans cannot schedule excluded stages unless forced

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014jWan98ut6ZUHkmXMG2bqW"
```

---

### Task 9: API and CLI

**Files:**
- Modify: `agency/server/app.py` (models, `create_project`, new routes after `set_requirement`), `agency/cli.py` (after `requirement`)
- Test: `tests/test_server.py`

**Interfaces:**
- Produces: `GET /api/projects/{pid}/scope` → `{"scope": ScopeConfig | null, "recommended": ScopeConfig}`; `PUT /api/projects/{pid}/scope` body `{"changes": {...}, "reason": ""}` → ScopeConfig, 409 on a locked module; `POST /api/projects` accepts `scope_preferences`; CLI `agency scope PROJECT [module=state ...]`.

- [ ] **Step 1: Write the failing tests (append to `tests/test_server.py`)**

```python
async def test_scope_endpoints(client):
    r = await client.post("/api/projects", json={"name": "P5", "hypothesis": "h",
                                                  "scope_preferences": {"figures": "included", "bogus": "x"}})
    assert r.status_code == 201 and r.json()["state"]["settings"]["scope_preferences"] == {"figures": "included"}
    r = await client.get("/api/projects/p5/scope")
    assert r.status_code == 200 and r.json()["scope"] is None and r.json()["recommended"]["figures"]["state"] == "included"
    r = await client.put("/api/projects/p5/scope", json={"changes": {"external_review": "included"}, "reason": "colleagues"})
    assert r.status_code == 200 and r.json()["external_review"]["state"] == "included" and r.json()["configured_at"]
    assert (await client.get("/api/projects/p5/scope")).json()["scope"]["figures"]["state"] == "included"
    assert (await client.put("/api/projects/p5/scope", json={"changes": {"figures": "maybe"}})).status_code == 409
    from tests.test_engine import CALLSPEC
    from agency.domain.graph import NodeType
    spec = dict(CALLSPEC, sections=CALLSPEC["sections"] + [{"id": "4", "title": "Fin", "kind": "financial"}])
    client.engine.ws.graph("p5").add(NodeType.CALL_SPEC, spec)
    client.engine.ws.put_scope("p5", client.engine.ws.recommend_scope("p5"))
    r = await client.put("/api/projects/p5/scope", json={"changes": {"finance": "excluded"}})
    assert r.status_code == 409 and "required by the call" in r.json()["detail"]
    assert (await client.get("/api/projects/nope/scope")).status_code == 404
    # the guide's side path carries the scope state
    side = {p["key"]: p for p in (await client.get("/api/projects/p5/next")).json()["side"]}
    assert side["finance"]["scope_state"] == "required"
```

Also update `test_run_stage_inbox_and_events`: after the outline approval is answered and before the "wait for completion" loop, answer the two new inbox items:

```python
    # then the scope form, then the alignment question (P2 has a preliminary hypothesis)
    for want in ("form", "question"):
        for _ in range(200):
            await asyncio.sleep(0.02)
            pending = (await client.get("/api/inbox", params={"project": "p2"})).json()["items"]
            if pending and pending[0]["kind"] == want:
                break
        assert pending and pending[0]["kind"] == want, pending
        answer = {"data": {"finance": "excluded"}} if want == "form" else {"choice": "keep the hypothesis as is"}
        await client.post(f"/api/inbox/{pending[0]['id']}/answer", json={"answer": answer})
```

and extend the job-name assertion to `>= {"parse_call", "approve_outline", "configure_scope", "align_concept", "finalize"}`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_server.py -q`
Expected: `test_scope_endpoints` fails with 404/405 on `/scope`; `test_run_stage_inbox_and_events` fails or hangs on the new inbox items until Step 3 (the loops bound it).

- [ ] **Step 3: Implement**

`agency/server/app.py`:

```python
class CreateProject(BaseModel):
    ...
    pack: str | None = None
    scope_preferences: dict[str, str] | None = None


class ScopeChange(BaseModel):
    changes: dict[str, str] = Field(default_factory=dict)
    reason: str = ""
```

In `create_project`, pass `scope_preferences=body.scope_preferences` to `ws.create_project`.

Add after `set_requirement`:

```python
    # ------------------------------------------------------------ scope
    @app.get(f"{api}/projects/{{pid}}/scope")
    def get_scope(pid: str) -> dict[str, Any]:
        try:
            scope = ws.get_scope(pid)
        except KeyError:
            raise HTTPException(404, "project not found")
        return {"scope": scope.model_dump(mode="json") if scope else None,
                "recommended": ws.recommend_scope(pid).model_dump(mode="json")}

    @app.put(f"{api}/projects/{{pid}}/scope")
    def put_scope(pid: str, body: ScopeChange) -> dict[str, Any]:
        try:
            ws.require_project(pid)
            return ws.set_scope(pid, body.changes, by="researcher", reason=body.reason).model_dump(mode="json")
        except KeyError:
            raise HTTPException(404, "project not found")
        except ValueError as e:
            raise HTTPException(409, str(e))
```

`agency/cli.py`, after the `requirement` command:

```python
@app.command()
def scope(ctx: typer.Context, project: str,
          change: list[str] = typer.Argument(None, help="module=state pairs, e.g. finance=included figures=excluded")):
    """Show or change the proposal scope (finance, business_plan, figures, external_review)."""
    ws = _ws(ctx.obj["root"])
    if change:
        try:
            changes = dict(c.split("=", 1) for c in change)
        except ValueError:
            typer.echo("error: expected module=state pairs")
            raise typer.Exit(2)
        try:
            typer.echo(ws.set_scope(project, changes, by="cli").model_dump_json(indent=2))
        except (KeyError, ValueError) as e:
            typer.echo(f"error: {e}")
            raise typer.Exit(2)
        return
    current = ws.get_scope(project)
    typer.echo(json.dumps({"scope": current.model_dump(mode="json") if current else None,
                           "recommended": ws.recommend_scope(project).model_dump(mode="json")}, indent=2))
```

In the `next` command, print the flags so `scope_only` / `align_only` are visible:

```python
    if action.get("stage"):
        flags = " ".join(f"-f {k}={v}" for k, v in (action.get("flags") or {}).items())
        typer.echo(f"  → agency run {project} {action['stage']}" + (f" {flags}" if flags else "")
                   + (" --force" if action.get("force") else "") + (" --resume" if action.get("resume") else ""))
```

- [ ] **Step 4: Run the tests and the CLI smoke**

Run: `.venv/bin/python -m pytest tests/test_server.py -q && .venv/bin/agency --help | grep -q scope && echo CLI-OK`
Expected: all pass; `CLI-OK`

- [ ] **Step 5: Commit**

```bash
git add agency/server/app.py agency/cli.py tests/test_server.py
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "API and CLI: read and change the proposal scope; scope preferences at project creation

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014jWan98ut6ZUHkmXMG2bqW"
```

---

### Task 10: UI — types, API client, New Project preferences, Scope card, enum forms, call-first copy

**Files:**
- Modify: `ui/shared/src/state.ts`, `ui/web/src/lib/api.ts`, `ui/web/src/pages/NewProject.tsx`, `ui/web/src/pages/Overview.tsx`, `ui/web/src/pages/Inbox.tsx:151-181`, `ui/web/src/pages/Pipeline.tsx:77-80`
- Verify: `cd ui && npm run typecheck && npm run build`

**Interfaces:**
- Consumes: the API from Task 9 and the guide fields from Task 7.
- Produces: shared types `ScopeState`, `ModuleScope`, `ScopeConfig`; `PathStep.scope_state?`; `NextStep.scope?`; `getScope(project)`, `setScope(project, changes, reason?)`; `CreateProjectBody.scope_preferences?`.

- [ ] **Step 1: Shared types (`ui/shared/src/state.ts`)**

Add near `PathStep`:

```ts
export type ScopeState = "excluded" | "included" | "required";
export type ScopeSource = "call" | "pack" | "user" | "default";
export interface ModuleScope { state: ScopeState; source: ScopeSource; reason: string; }
export interface ScopeConfig {
  finance: ModuleScope;
  business_plan: ModuleScope;
  figures: ModuleScope;
  external_review: ModuleScope;
  configured_at: string | null;
}
export const SCOPE_MODULES = ["finance", "business_plan", "figures", "external_review"] as const;
export type ScopeModule = (typeof SCOPE_MODULES)[number];
```

Add `scope_state?: ScopeState | null;` to `PathStep` and `scope?: ScopeConfig | null;` to `NextStep`.

- [ ] **Step 2: API client (`ui/web/src/lib/api.ts`)**

Add `ScopeConfig` to the type import and:

```ts
export interface CreateProjectBody {
  ...
  scope_preferences?: Record<string, "excluded" | "included">;
}

export async function getScope(project: string): Promise<{ scope: ScopeConfig | null; recommended: ScopeConfig }> {
  return getJson(`${BASE}/projects/${enc(project)}/scope`);
}

export async function setScope(project: string, changes: Record<string, string>, reason = ""): Promise<ScopeConfig> {
  const url = `${BASE}/projects/${enc(project)}/scope`;
  const res = await fetch(url, { method: "PUT", headers: { "content-type": "application/json" }, body: JSON.stringify({ changes, reason }) });
  return handle<ScopeConfig>(res, url);
}
```

- [ ] **Step 3: New Project preferences (`ui/web/src/pages/NewProject.tsx`)**

Add state and selects:

```tsx
const SCOPE_MODULES: Array<[string, string]> = [["finance", "Finance"], ["business_plan", "Business plan"], ["figures", "Figures"], ["external_review", "External review"]];
// inside the component
const [scope, setScope] = useState<Record<string, string>>({ finance: "", business_plan: "", figures: "", external_review: "" });
```

In the mutation body, compute and pass preferences:

```ts
const scope_preferences = Object.fromEntries(Object.entries(scope).filter(([, v]) => v === "excluded" || v === "included")) as Record<string, "excluded" | "included">;
const p = await createProject({ ..., scope_preferences: Object.keys(scope_preferences).length ? scope_preferences : undefined });
```

Under the pack select, render:

```tsx
<div className="grid gap-1 text-sm">
  <span className="text-foreground-muted">Optional modules (auto = decide after the call is parsed)</span>
  <div className="grid grid-cols-2 gap-2">
    {SCOPE_MODULES.map(([key, label]) => (
      <label key={key} className="grid gap-1 text-xs">
        <span>{label}</span>
        <select className="h-8 rounded border border-border bg-background px-2" value={scope[key]} onChange={(e) => setScope({ ...scope, [key]: e.target.value })}>
          <option value="">auto</option>
          <option value="included">include</option>
          <option value="excluded">exclude</option>
        </select>
      </label>
    ))}
  </div>
</div>
```

Update the card description to: "Step 1 of 3. Upload the call first; you can still explore an idea before the call arrives, and the app aligns it with the call afterwards. A firm hypothesis skips the ideation interview. After creating, the Overview tells you what to do next."

- [ ] **Step 4: Overview scope card and greyed excluded stages (`ui/web/src/pages/Overview.tsx`)**

Reorder `STAGE_KEYS` so `call_parsing` precedes `ideation`. Import `getScope, setScope` from the API. In `WorkflowPath`, render side badges as:

```tsx
{side.map((s) => (
  <Badge key={s.key} variant={s.status === "complete" ? "success" : "muted"} className={s.scope_state === "excluded" ? "opacity-50" : ""}>
    {s.label}{s.scope_state === "excluded" ? " · excluded" : s.scope_state === "required" ? " · required" : ""}
  </Badge>
))}
```

(If `Badge` does not accept `className`, wrap it in `<span className="opacity-50">`.)

Add the card:

```tsx
const SCOPE_ROWS: Array<[ScopeModule, string]> = [["finance", "Finance"], ["business_plan", "Business plan"], ["figures", "Figures"], ["external_review", "External review"]];

function ScopeCard({ project }: { project: string }): React.ReactElement {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["scope", project], queryFn: () => getScope(project) });
  const change = useMutation({
    mutationFn: ({ module, state }: { module: string; state: string }) => setScope(project, { [module]: state }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["scope", project] }); qc.invalidateQueries({ queryKey: ["project", project] }); },
  });
  const scope = data?.scope;
  const shown = scope ?? data?.recommended;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Scope</CardTitle>
        <CardDescription>{scope ? "Your preference controls optional work; the call controls mandatory work." : "Not configured yet — parse-call asks for it. Shown: the recommendation."}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-1.5 text-sm">
        {SCOPE_ROWS.map(([key, label]) => {
          const m = shown?.[key];
          const locked = m?.state === "required" && (m.source === "call" || m.source === "pack");
          return (
            <div key={key} className="flex items-center justify-between gap-2 rounded border border-border px-2 py-1">
              <div>
                <div>{label}</div>
                <div className="text-xs text-foreground-muted">{m?.reason}</div>
              </div>
              {locked || !scope ? (
                <Badge variant={m?.state === "required" ? "info" : "muted"}>{m?.state ?? "—"}{m ? ` · ${m.source}` : ""}</Badge>
              ) : (
                <select className="h-7 rounded border border-border bg-background px-1 text-xs" value={m?.state} disabled={change.isPending}
                  onChange={(e) => change.mutate({ module: key, state: e.target.value })}>
                  {["excluded", "included", "required"].map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              )}
            </div>
          );
        })}
        {change.error && <div className="text-xs text-destructive">{String(change.error)}</div>}
      </CardContent>
    </Card>
  );
}
```

Import `ScopeModule` from `@pw/shared`. Place `<ScopeCard project={active} />` in the right-hand column between the "Now" card and the "Graph" card.

- [ ] **Step 5: Inbox enum form (`ui/web/src/pages/Inbox.tsx`)**

Replace `JsonForm` with a version that renders multi-field string schemas as fields:

```tsx
type Prop = { type?: string; enum?: string[]; title?: string; description?: string; readOnly?: boolean };

function JsonForm({ item, onAnswer, disabled }: FormProps): React.ReactElement {
  const schema = item.payload.schema as { properties?: Record<string, Prop> } | undefined;
  const props = schema?.properties;
  const keys = props ? Object.keys(props) : [];
  const simpleText = keys.length === 1 && props![keys[0]!]?.type === "string" && !props![keys[0]!]?.enum;
  const fieldForm = keys.length > 1 && keys.every((k) => props![k]?.type === "string");
  const example = (item.payload.example ?? {}) as Record<string, string>;
  const [text, setText] = useState(Object.keys(example).length && !fieldForm ? JSON.stringify(example, null, 2) : "");
  const [values, setValues] = useState<Record<string, string>>(() => Object.fromEntries(keys.map((k) => [k, example[k] ?? props![k]?.enum?.[0] ?? ""])));
  const [err, setErr] = useState<string | null>(null);
  if (fieldForm) {
    return (
      <div className="space-y-2">
        {keys.map((k) => {
          const p = props![k]!;
          return (
            <label key={k} className="grid gap-1 text-sm">
              <span>{p.title ?? k}{p.description ? <span className="text-xs text-foreground-muted"> — {p.description}</span> : null}</span>
              {p.enum ? (
                <select className="h-8 rounded border border-border bg-background px-2" value={values[k]} disabled={p.readOnly || disabled}
                  onChange={(e) => setValues({ ...values, [k]: e.target.value })}>
                  {p.enum.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              ) : (
                <input className="h-8 rounded border border-border bg-background px-2" value={values[k]} disabled={p.readOnly || disabled}
                  onChange={(e) => setValues({ ...values, [k]: e.target.value })} />
              )}
            </label>
          );
        })}
        <Button size="sm" disabled={disabled} onClick={() => onAnswer({ data: values })}>Submit</Button>
      </div>
    );
  }
  const submit = () => {
    if (simpleText) {
      onAnswer({ data: { [keys[0]!]: text }, text });
      return;
    }
    try {
      onAnswer({ data: JSON.parse(text) });
      setErr(null);
    } catch (e) {
      setErr(`Invalid JSON: ${String(e)}`);
    }
  };
  return (
    <div className="space-y-2">
      <textarea className="mono h-48 w-full rounded border border-border bg-background p-2 text-xs" value={text} onChange={(e) => setText(e.target.value)}
        placeholder={simpleText ? "Paste text here" : "JSON matching payload.schema"} />
      {!simpleText && schema && (
        <details className="text-xs text-foreground-muted"><summary>schema</summary><pre className="mono max-h-40 overflow-auto">{JSON.stringify(schema, null, 2)}</pre></details>
      )}
      {err && <div className="text-xs text-destructive">{err}</div>}
      <Button size="sm" disabled={disabled || !text.trim()} onClick={submit}>Submit</Button>
    </div>
  );
}
```

- [ ] **Step 6: Pipeline copy (`ui/web/src/pages/Pipeline.tsx:78`)**

Change the order text to `parse-call → ideate → research → write-proposal → review → export` and the sentence after it to: "with finance, figures, business-plan and external-feedback as side steps governed by the project scope (excluded stages need force). Locked stages say what they wait for."

- [ ] **Step 7: Typecheck and build**

Run: `cd ui && npm run typecheck && npm run build`
Expected: both succeed with no errors

- [ ] **Step 8: Commit**

```bash
git add ui/shared/src/state.ts ui/web/src/lib/api.ts ui/web/src/pages/NewProject.tsx ui/web/src/pages/Overview.tsx ui/web/src/pages/Inbox.tsx ui/web/src/pages/Pipeline.tsx
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "UI: scope preferences and card, enum inbox forms, call-first workflow copy

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014jWan98ut6ZUHkmXMG2bqW"
```

---

### Task 11: Documentation and final verification

**Files:**
- Modify: `docs/architecture.md`, `README.md`

- [ ] **Step 1: Architecture doc**

In `docs/architecture.md`:

- Stage table: replace the `parse-call` row with
  `| parse-call | locate inputs → call_parser ∥ eligibility_parser → merge with pack → approve (inbox) → configure_scope (inbox form) → align_concept (agent + inbox, only for a preliminary concept); flags scope_only / align_only re-run just those jobs | → scope |`
  and the `ideate` row description with "Exploratory when no CallSpec exists: the hypothesis is marked `preliminary` and aligned by parse-call later."
- Under **Guidance**, add a paragraph:

  > **Scope.** `ScopeConfig` (`agency/domain/scope.py`) records for finance, business plan, figures and external review whether the module is `excluded`, `included` or `required`, with the source (`call`, `pack`, `user`, `default`). It is derived after parse-call (call requirements first, then the pack's `modules:`, then creation-time preferences, then defaults), confirmed by the researcher in the inbox, stored in `project.settings["scope"]`, and every change is a Decision. The runner blocks excluded stages unless `--force` (which flips the module to included), the draft gate requires `required` modules to be complete, the submission gate requires a closed external-review round when external review is required, and the guide never recommends an excluded module. The guided path is Call → Idea → Research → Draft → Review → Export; a hypothesis written before the call is `preliminary` until the alignment step marks it `aligned`, which the scope gate checks.

- [ ] **Step 2: README**

Line 11: change the pipeline line to
`idea ──▶ parse-call ──▶ ideate ──▶ research ──▶ write-proposal ──▶ review ──▶ external-feedback ──▶ export`
and add below the figure: "Ideation can also run before the call (exploratory mode); parse-call then aligns the hypothesis with the call and asks you to configure the scope: finance, business plan, figures and external review as excluded / included / required."

Stage table: swap the `ideate` and `parse-call` rows and change the `parse-call` cell to "`CallSpec` from the call document (+ eligibility parser, funder pack), outline, your approval, scope configuration, concept alignment".

- [ ] **Step 3: Mark the recommendation document**

Insert at the top of `system-recommendation.md` (currently untracked; this commit adds it to the repo):

```markdown
> Implemented: priorities 1 and 2 (call ingestion before ideation, intake scope configuration) —
> see `docs/superpowers/specs/2026-09-03-intake-scope-design.md`.
```

- [ ] **Step 4: Full verification**

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/agency doctor
cd ui && npm run typecheck && npm run build
```

Expected: all tests pass, doctor reports `"ok": true`, UI builds.

- [ ] **Step 5: Commit**

```bash
git add docs/architecture.md README.md system-recommendation.md
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "Docs: call-first workflow and scope configuration

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014jWan98ut6ZUHkmXMG2bqW"
```
