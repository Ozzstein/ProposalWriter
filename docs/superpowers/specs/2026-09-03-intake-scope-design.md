# Intake: call-first workflow and scope configuration — design

Date: 2026-09-03
Status: approved design, awaiting implementation plan
Source: `system-recommendation.md`, priorities 1 and 2 (sub-project A of the recommended evolution)

## 1. Context

`system-recommendation.md` proposes ten changes. This spec covers the first two:

1. Ingest the call before generating or refining ideas.
2. Let the user decide at intake which optional components the proposal includes, with the rule
   "user preference controls optional work; call requirements control mandatory work".

Today the `ideate` stage has no prerequisite, `research` requires `parse-call`, and the optional
stages (`finance`, `figures`, `business-plan`, `external-feedback`) are inferred from the CallSpec
only, are never enforced by a gate, and cannot be excluded by the user. The guide (`agency/policy/guide.py`)
recommends ideation before the call.

Later sub-projects (concept loop, blueprint and coverage gates, roster consolidation, integration
gate) build on the state introduced here and are out of scope.

## 2. Goals and non-goals

Goals

- The guided path is Call → Idea → Research → Draft → Review → Export.
- Ideation without a call remains possible (exploratory mode). Its result is marked preliminary
  and must pass an explicit call-alignment step before research can start.
- A typed scope record with four modules, each `excluded`, `included` or `required`, decided by the
  user after the call is parsed, with call requirements taking precedence.
- Scope is enforced: required modules block the draft gate; excluded stages are blocked unless
  forced, and forcing flips the module to included with a logged decision.
- Every surface (guide, Overview, CLI, planner brief) reads the same scope record.

Non-goals

- No new agent contracts. The alignment step reuses `idea_evaluator`. Consolidating the roster is
  sub-project D.
- No concept brief, no blueprint, no coverage gate, no integration gate.
- No store schema migration. Both new records live in existing JSON columns.

## 3. Data model

### 3.1 ScopeConfig (`agency/domain/scope.py`)

```python
ModuleState = Literal["excluded", "included", "required"]
ModuleSource = Literal["call", "pack", "user", "default"]

class ModuleScope(BaseModel):
    state: ModuleState
    source: ModuleSource
    reason: str = ""            # why the state was chosen (e.g. "call has financial sections")

class ScopeConfig(BaseModel):
    finance: ModuleScope
    business_plan: ModuleScope
    figures: ModuleScope
    external_review: ModuleScope
    configured_at: str | None = None   # ISO timestamp of the user's confirmation; None = unconfirmed

MODULES = ("finance", "business_plan", "figures", "external_review")
MODULE_STAGE = {"finance": "finance", "business_plan": "business-plan",
                "figures": "figures", "external_review": "external-feedback"}
MODULE_STATE_KEY = {"finance": "finance", "business_plan": "business_plan",
                    "figures": "figures", "external_review": "external_review"}
```

Storage: `project.settings["scope"]` holds `ScopeConfig.model_dump()`. Absence means "not configured".
`ScopeConfig.load(project)` returns `None` when absent or invalid; callers treat `None` as unconfigured.

Creation-time preferences: the New Project form may send `scope_preferences`
(`{module: "excluded" | "included"}`), stored as `project.settings["scope_preferences"]`. They are
inputs to derivation, never the scope itself.

### 3.2 Derivation (`derive_scope(callspec, pack, preferences, call_text) -> ScopeConfig`)

Pure function, evaluated per module in this precedence:

1. `required` with source `call` when the CallSpec demands the module:
   - finance: `CallSpec.has_financials()`;
   - business_plan: `CallSpec.needs_business_plan()`;
   - figures: never required by derivation (a call rarely mandates figures); may be set required by
     the pack;
   - external_review: never required by derivation.
2. The pack's `modules:` map (new optional key in `pack.yaml`, values `excluded | included | required`),
   source `pack`.
3. The user's creation-time preference, source `user`.
4. Default, source `default`: figures `included` when the call text or any section guidance contains
   "figure", "diagram", "gantt" or "chart" (case-insensitive), otherwise `excluded`; the other
   three `excluded`.

`configured_at` is `None` on the derived result.

### 3.3 Change rules (`apply_scope_change(current, changes, *, by) -> ScopeConfig`)

- A module in state `required` with source `call` or `pack` cannot be changed by the user; an attempt
  raises `ValueError("<module> is required by the call")`.
- Any other module may be set to `excluded` or `included` (source becomes `user`) or, by the user,
  to `required` (source `user`); a user-required module can later be downgraded by the user.
- Every user-originated write (the inbox form, `PUT /scope`, the CLI, a forced run) sets
  `configured_at` to the current time.
- Re-running parse-call re-derives step 1 only: modules that become call-required are upgraded;
  modules that were call-required and no longer are fall back to derivation from step 2 onward;
  all other user choices are kept. `configured_at` is preserved when nothing changed and reset to
  `None` when any module's state changed, so the user re-confirms.

### 3.4 Audit

Every write of the scope record adds a Decision node:

- type `scope_configured` on the parse-call confirmation, decision = summary such as
  `finance: required (call); business_plan: included (user); figures: excluded; external_review: excluded`,
  rationale = per-module reasons;
- type `scope_changed` on later edits (API, CLI, forced run), decision = `module: before -> after`,
  rationale = `[by, reason]`.

### 3.5 Concept status

The context document (`graph.document("context")`) gains `concept_status` next to `hypothesis`:
`none` (no hypothesis), `preliminary`, `aligned`.

- `Workspace.create_project` with a hypothesis sets `preliminary`; without one, `none`.
- `ideate.choose` sets `aligned` when a CallSpec node exists at that moment, else `preliminary`.
- `parse-call`'s alignment job is the only other writer; it sets `aligned` on keep or adjust.
- Legacy or pre-existing projects with a hypothesis but no `concept_status` read as `preliminary`.

## 4. Stage flow

### 4.1 ideate (exploratory mode)

No prerequisite is added. `ideate.choose` writes `concept_status` as in 3.5. The stage description
and the guide text say that ideation without a call is exploratory and will be aligned later.

### 4.2 parse-call

Plan (new jobs in bold):

```
locate_inputs → parse_call ∥ parse_eligibility → merge_spec → approve_outline
  → **configure_scope** (inbox form)
  → **align_concept** (agent + inbox; only when concept_status == preliminary)
  → finalize (scope gate)
```

Two new flags let parts of the stage re-run without re-parsing:

- `scope_only`: the plan is `configure_scope → finalize`. Fails with "parse the call first" when no
  CallSpec exists.
- `align_only`: the plan is `align_concept → finalize`. Fails with "parse the call first" when no
  CallSpec exists and with "nothing to align" when the concept is not `preliminary`.

`configure_scope` (handler `parse_call.configure_scope`, kind INBOX):

1. Read the CallSpec, pack, preferences, extracted call text; call `derive_scope`; merge with any
   existing scope through the rules in 3.3 (so a re-parse keeps user choices).
2. Ask through `rt.form` with key `configure_scope`. Schema: one property per module, `type: string`,
   `enum: ["excluded", "included", "required"]`, `description` = the derived reason; locked modules
   carry `readOnly: true` and `enum: ["required"]`. The example is the derived scope. The question
   text states the governing rule.
3. Validate the answer with `apply_scope_change`; on a violation re-ask once with the error in the
   question; on a second violation keep the derived state for the offending modules and note it in
   the decision rationale.
4. Set `configured_at`, save to `project.settings["scope"]`, log the `scope_configured` decision,
   return a summary.

`align_concept` (handler `parse_call.align_concept`, kind AGENT):

1. Inputs: `context.md`, `intermediate/call_spec.json`, `intermediate/proposal_outline.md`,
   `intermediate/ideation_brief.json` when present.
2. Agent: `idea_evaluator`, phase `align`, `allowed_writes=set()`, output model `ConceptAlignment`
   (new, in `agency/domain/models.py`):

   ```python
   class CriterionFit(BaseModel):
       criterion_id: str
       fit: float            # 0-10
       comment: str

   class ConceptAlignment(BaseModel):
       overall_fit: float    # 0-10
       verdict: Literal["fits", "fits_with_changes", "does_not_fit"]
       criterion_fits: list[CriterionFit]
       scope_misfits: list[str]         # e.g. TRL, geography, consortium, duration
       eligibility_conflicts: list[str] # requirement ids or texts
       suggested_hypothesis: str | None # rewritten hypothesis when changes are recommended
       rationale: str
   ```

3. Persist as document `concept_alignment` (body = rationale, data = the model).
4. Ask through `rt.ask` with key `align_decision`, options:
   `keep the hypothesis as is`, `adopt the suggested hypothesis` (only when one exists),
   `reopen ideation`.
   - keep: `concept_status = aligned`; Decision type `concept_alignment`, decision `kept`.
   - adopt: rewrite the `## Hypothesis` block in the context document with `suggested_hypothesis`
     (same replacement logic as `ideate.choose`), set `hypothesis` and `concept_status = aligned`;
     Decision `adopted`, rationale includes the previous hypothesis.
   - reopen: leave `preliminary`; Decision `reopen_ideation`; the job succeeds, the scope gate fails
     on the alignment rule, and the guide points to `ideate`.
5. Agent failure after the runtime's built-in retry fails the job; status stays `preliminary`.

### 4.3 Engine (`agency/engine/plan.py`, `agency/engine/runner.py`)

`StageDef` gains `scope_key: str | None = None`. Set on `finance` (`finance`), `business-plan`
(`business_plan`), `figures` (`figures`), `external-feedback` (`external_review`).

`Engine.check_prerequisites`: when `sd.scope_key` is set and the project's scope marks it `excluded`,
raise `StageBlocked("stage 'finance' is excluded by the project scope; run with --force to include it")`
unless `force` is true. With `force`: `apply_scope_change` to `included` (source `user`), save, log a
`scope_changed` decision with rationale `["forced run of <stage>"]`, and add the warning
`"scope: finance switched to included"`. An unconfigured scope does not block optional stages.

### 4.4 Drafting (`agency/jobs/drafting.py`)

`draftable_sections` takes the scope: sections of kind `financial` are skipped with the plan note
`"section X skipped: finance excluded by scope"` when finance is `excluded`. When finance is included or
required but no financial tables exist, the current note ("run finance first") stays. Sections of kind
`business_plan` remain unassigned to writers as today.

### 4.5 Guide (`agency/policy/guide.py`)

`MAIN_PATH` order becomes Call, Idea, Research, Draft, Review, Export. `next_step` returns `scope`
(the record or `null`) and each side-path entry carries `scope_state`.

Recommendation order in `_guidance`:

1. Pending inbox items.
2. Active run.
3. Call not parsed: `upload_call` or `parse_call` as today, with the alternative
   "Or run an exploratory ideation now; it will be aligned to the call afterwards."
4. Scope not configured (`configured_at` is `None`): step `configure_scope`, action
   `run_stage parse-call` with flag `scope_only`.
5. No hypothesis: `ideate`, with the alternative of writing it in the context.
6. Concept `preliminary`: step `align_concept`, action `run_stage parse-call` with `align_only`.
7. Unconfirmed disqualifying eligibility: `confirm_eligibility` as today.
8. Scope gate blockers as today.
9. Research not done: `research`.
10. Finance included or required and pending: `finance` (moved before drafting so financial
    sections can be written).
11. Writing not done: evidence gate blockers or `write`.
12. Business plan included or required and pending: `business_plan`.
13. Figures included or required and pending: `figures`.
14. Review, submission gate, export as today.
15. Done: external feedback suggestion only when external review is not `excluded`.

Excluded modules never appear as a recommendation or alternative.

## 5. Gates (`agency/policy/gates.py`)

`GateContext` gains `scope: ScopeConfig | None`, loaded by `evaluate_gate` from the project.

New rules:

- scope gate, `rule_scope_configured`: met when the scope exists and `configured_at` is set. Notes list
  the module states.
- scope gate, `rule_concept_aligned`: met when the context has no hypothesis, or `concept_status ==
  "aligned"`. Otherwise blocked with "preliminary concept not aligned to the call; run parse-call
  --align_only".
- draft gate, `rule_required_modules_complete`: for each of finance, business_plan, figures in state
  `required`, the corresponding stage status must be `complete`. Notes name the incomplete ones.
  Met trivially when the scope is unconfigured or nothing is required.
- submission gate, `rule_external_review_required`: returns `None` (omitted) unless external_review is
  `required`; then met when at least one Feedback node exists and the external_feedback gate rules all
  pass for the active round.

`rule_context_documented` is unchanged. Thresholds are unchanged.

## 6. Workspace, API, CLI

`Workspace`:

- `get_scope(project_id) -> ScopeConfig | None`
- `set_scope(project_id, changes: dict[str, str], *, by: str, reason: str = "") -> ScopeConfig`
  applies `apply_scope_change`, saves, logs the decision, emits `scope:changed`.
- `recommend_scope(project_id) -> ScopeConfig` runs `derive_scope` against the current CallSpec, pack,
  preferences and extracted call text (from `inputs/*.extracted.txt`).
- `create_project` accepts `scope_preferences` and sets `concept_status` in the context document.

API (`agency/server/app.py`):

- `GET /projects/{pid}/scope` → `{"scope": ScopeConfig | null, "recommended": ScopeConfig}`.
- `PUT /projects/{pid}/scope` body `{"changes": {module: state}, "reason": str}` → the new scope;
  `409` with the message when a change violates 3.3.
- `POST /projects` accepts `scope_preferences`.
- `GET /projects/{pid}/next` already returns the guide result, now including `scope` and
  `scope_state` per side-path entry.

CLI (`agency/cli.py`): `agency scope PROJECT` prints the record and recommendation;
`agency scope PROJECT finance=included figures=excluded` applies changes. `agency status` prints the
scope line.

Planner brief (`agency/jobs/plan.py`): the survey adds the scope record so `run_planner` never proposes
an excluded stage; `validate_plan` rejects steps whose stage is excluded unless the step sets `force`.

## 7. UI (`ui/web`)

- New Project: four selects (finance, business plan, figures, external review) with options
  `auto | include | exclude`, sent as `scope_preferences` when not `auto`. Description text updated:
  "Upload the call first; you can still explore an idea before the call arrives."
- Overview: a `ScopeCard` showing each module with state, source and reason; a select for modules
  that are not call-required; changes go through `PUT /scope` and refresh the guide. Side-path stages
  in state `excluded` render greyed with "excluded" and no run button.
- Inbox form renderer: when the schema has several properties, render each `enum` string property
  as a select (disabled when `readOnly`), other string properties as inputs; keep the JSON textarea
  as a fallback for other shapes. The example pre-fills the values.
- Pipeline page: stage order follows the guide's path (Call before Idea).
- `api.ts`: `getScope`, `setScope`, `CreateProjectBody.scope_preferences`, `NextStep.scope` and
  `scope_state` typings.

## 8. Error handling and edge cases

- Old projects: no scope record → guide step 4 asks to configure it; the scope gate blocks research
  until then. Existing hypotheses read as `preliminary`, so the alignment step runs once.
- Re-parse after scope was configured: user choices survive; call-required upgrades apply;
  `configured_at` resets only when a state changed, so the form is shown again only when needed.
- Forced run of an excluded stage: scope flips to included with a decision; never silently.
- `parse-call --align_only` with no CallSpec: run fails with "parse the call first".
- Alignment agent returns a `suggested_hypothesis` identical to the current one: the adopt option is
  omitted.
- Inbox answer for the scope form missing a module: the derived value is used for it.
- `set_scope` on a call-required module: `ValueError` → API 409, CLI exit 2.

## 9. Testing

- `tests/test_scope.py`: derivation precedence per module, pack override, preference fallback,
  figures keyword default, change rules (required lock, downgrade of user-required, re-derive keeps
  user choices, `configured_at` reset semantics).
- `tests/test_gates.py`: the four new rules, including the omitted external-review rule and the
  unconfigured-scope behaviour.
- `tests/test_guide.py`: call-first ordering, exploratory alternative text, configure-scope and
  align-concept steps, finance recommended before drafting when included, excluded modules never
  recommended, `scope_state` on the side path.
- `tests/test_pipeline_stages.py`: parse-call plan contains the new jobs; `align_only` and
  `scope_only` plans; the scope form round trip with a scripted inbox; alignment keep / adopt /
  reopen paths with the fake SDK returning a `ConceptAlignment`; re-parse keeps user scope.
- `tests/test_engine.py`: excluded stage raises `StageBlocked`; forced run flips scope and logs the
  decision; drafting skips financial sections when finance is excluded.
- `tests/test_server.py`: scope GET and PUT, 409 on a locked module, `scope_preferences` on create.
- `tests/test_interactive_stages.py`: `ideate.choose` sets `preliminary` without a CallSpec and
  `aligned` with one.
- UI: `npm run typecheck && npm run build`.
- `agency doctor` still passes (no contract changes).

## 10. Documentation

- `docs/architecture.md`: stage table row for parse-call (new jobs and flags), a "Scope" paragraph
  under Guidance, the new gate rules, and the main-path order.
- `README.md`: the pipeline line (line 11) and the stage table put `parse-call` before `ideate` and
  mention exploratory ideation.
- `system-recommendation.md` is left as the source document; a short "implemented: priorities 1 and 2"
  note is added at the top once the plan is executed.

## 11. Follow-ups (other sub-projects)

- B. Concept loop: replaces the single alignment decision with the four-action loop and a
  ConceptBrief node; `concept_status` becomes the brief's status.
- C. Blueprint and coverage gate.
- D. Roster consolidation and bounded SDK subagents; renames `idea_evaluator` and `call_parser`
  into the strategy lead and call analyst.
- E. Integration gate and the compliance / evaluator review split; `rule_required_modules_complete`
  moves into the integration gate.
