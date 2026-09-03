# Architecture

## Principles

1. **Graph, not folders.** Every artefact is a typed node with provenance edges; gates, reviews and exports query the graph (`agency/domain/graph.py`, `agency/graph/repo.py`).
2. **Call-driven planning.** `CallSpec` + funder pack → job DAG per stage (`agency/engine/plan.py`, `agency/jobs/*`).
3. **Agents are contracts.** `agents/<name>/contract.yaml` declares role, model tier, tools, connectors, output model, budget, acceptance; `prompt.md` is the role text. The engine composes prompts (`agency/catalogue/prompts.py`).
4. **Code owns control flow.** Scheduler, gates, budgets, ID allocation and writes are deterministic; model calls are bounded and structured (`agency/sdk/adapter.py`).
5. **One human channel.** Questions/approvals/forms/chat turns are persisted inbox items runs block on (`agency/inbox/service.py`).
6. **Quality is a loop.** Panel simulation → ranked revisions → redraft → re-score (`agency/jobs/review.py`).
7. **Replayable.** Event log + cost ledger per run (`agency/events/log.py`).

## Data model

Node types: Project, CallSpec, Criterion, Requirement, Source, Claim, Gap, NoveltyAnchor, Section, Figure, FinancialTable, Decision, ReviewFinding, PanelScore, Feedback, Patch, Entity, Concept, IdeationBrief, Document.
Edge types: supported_by, cites, addresses, anchored_on, satisfies, derived_from, found_in, scores, resolved_by, targets, promoted_to, evidence_of, relates_to, part_of.

Storage (`agency/store/sqlite.py`): `nodes(pkey, id, version)` keeps every version (`is_current` marks the head), `edges` are unique per `(pkey, src, dst, type)`, `counters` allocate IDs per project and prefix, plus `projects`, `runs`, `jobs`, `inbox`, `events`, `costs`. `pkey` is the project id or `__workspace__`, so legacy ids (`SRC-001`) can coexist across projects while workspace knowledge uses `WIKI-*` ids. Large files go to the content-addressed blob store.

## Runtime

```
CLI / FastAPI ──▶ Engine.run_stage(project, stage)
                    ├─ prerequisites: stage status warnings, blocking gate (or --force + gate_override decision)
                    ├─ StageDef.planner(ctx) ──▶ StagePlan (JobSpecs with deps)
                    └─ Scheduler: asyncio DAG, persisted Job rows, resume skips completed jobs
                         └─ handler(JobRuntime)
                              ├─ rt.agent(contract, …)   one query() with output_format, hooks, agency MCP tools
                              ├─ rt.session(contract, …) ClaudeSDKClient conversation; AskUserQuestion → inbox
                              ├─ rt.ask / approve / form  inbox items (restart-safe via stable keys)
                              └─ graph writes via agency.engine.materialize.ingest_* (validated)
```

Before every agent call the graph is materialised into the project working directory (`workspace/projects/<id>/`: `context.md`, `memory/*.jsonl`, `intermediate/*`, `drafts/*`, `reviews/*`), so prompts written against a file layout keep working. Structured results and files written by agents are ingested back into the graph; nothing an agent writes is trusted until validated.

SDK options per call: `system_prompt = conventions + prompt.md`, `allowed_tools` from the contract plus `mcp__agency__*` (read-only unless the contract declares writes), `disallowed_tools=["Agent","Task"]`, `permission_mode="bypassPermissions"` with PreToolUse guards (no subagents, writes only under the project dir, no direct store writes, no destructive shell), `setting_sources=[]`, `output_format` from the pydantic output model, `max_turns`/`max_budget_usd`/`effort` from the contract, connectors as stdio MCP servers only for the agents that need them, secrets only in those processes' env.

## Guidance

`agency/policy/guide.py` derives a deterministic *next step* from project state (pending inbox,
active run, hypothesis, input files, stage statuses, gate results and blockers, CallSpec needs) with
the action that performs it (run a stage with flags/force/resume, upload then run, confirm
requirements, open the inbox). The Overview card, `agency next` and `/projects/{id}/next` all read it,
so every surface tells the same story. Requirement confirmation
(`Workspace.set_requirement_status`) updates the CallSpec node that the scope gate reads and logs a
`requirement_status` decision.

**Scope.** `ScopeConfig` (`agency/domain/scope.py`) records for finance, business plan, figures and external review whether the module is `excluded`, `included` or `required`, with the source (`call`, `pack`, `user`, `default`). It is derived after parse-call (call requirements first, then the pack's `modules:`, then creation-time preferences, then defaults), confirmed by the researcher in the inbox, stored in `project.settings["scope"]`, and every change is a Decision. The runner blocks excluded stages unless `--force` (which flips the module to included), the draft gate requires `required` modules to be complete, the submission gate requires a closed external-review round when external review is required, and the guide never recommends an excluded module. The guided path is Call → Idea → Research → Draft → Review → Export; a hypothesis written before the call is `preliminary` until the alignment step marks it `aligned`, which the scope gate checks.

*Existing projects.* A project created before this change has no scope record and a hypothesis (if any) reads as `preliminary`. Run `agency run PROJECT parse-call -f scope_only=1` to derive and confirm the scope, then either `agency run PROJECT parse-call -f align_only=1` to align a hypothesis written earlier or `agency concept PROJECT aligned` (`PUT /api/projects/{pid}/concept`) to set the status directly without re-running the alignment agent.

## Planning agent (campaigns)

The engine decides *how* a stage runs; the planning agent decides *which* stages run next. `agency plan
PROJECT --goal "…"` (or `POST /projects/{id}/plan`) runs the `plan` stage:

```
survey (code)  ──▶ propose (run_planner agent) ──▶ approve (inbox)
  planning brief:     RunPlan: ordered steps         one row per step; approve / skip / reject
  stages + flags,     {stage, flags, force,          approved plan stored as the run_plan document
  statuses, gates     rationale}, risks,             and a plan_approved decision
  + blockers, runs,   questions for the researcher
  cost, goal
```

`validate_plan` rejects unknown stages or flags, prerequisite order violations and plans over eight
steps; the planner gets the errors back and two more attempts. After approval `Engine.run_campaign`
executes each step as an ordinary `run_stage` call (gates, budgets, resume and inbox all apply) and
records the outcome per step in the plan document. When a step fails or is blocked by a gate, the
failure goes into a fresh planning brief and the planner gets one more attempt (`--max-replans`),
again subject to approval. The planner never executes anything and cannot invent stages, jobs or
flags: its levers are exactly the stage registry and the flags each stage declares.

## Stages and gates

| Stage | Plan | Gate in → out |
|---|---|---|
| parse-call | locate inputs → call_parser ∥ eligibility_parser → merge with pack → approve (inbox) → configure_scope (inbox form) → align_concept (agent + inbox, only for a preliminary concept); flags scope_only / align_only re-run just those jobs | → scope |
| ideate | Exploratory when no CallSpec exists: the hypothesis is marked `preliminary` and aligned by parse-call later. | – |
| research | kb_import → literature ∥ web ∥ patents → synthesize → novelty ∥ gaps | scope → evidence |
| write-proposal | prepare → draft:<excellence> → draft:<others> ∥ → draft:abstract | evidence → draft |
| finance | intake (files or form) → model → narrative ∥ → financial review | – |
| figures | preflight → render (≤4 parallel) → index | – |
| business-plan | prereq → interview (session, per-batch persistence) → synthesize → 4 writers ∥ → review → assemble | – |
| review | setup → scientific ∥ compliance ∥ panel → compile plan → revise loop | draft → submission |
| external-feedback | resolve round → parse files ∥ → ingest → triage (inbox) → dispatch by route → summary | → external_feedback |
| export | assemble md → docx | submission |
| plan | survey → run_planner → approve (inbox); then `run_campaign` executes the approved stage runs | – |

Gate rules are plain functions over the graph (`agency/policy/gates.py`); thresholds come from `agency/policy/thresholds.py`, overridable per pack and in `agency.toml`.

## Hosting seams

Local-first today (SQLite, local blobs, no auth). The `Store`/`BlobStore` interfaces, engine state fully in the store, workspace as the tenant unit, and the event log as the only cross-process channel are the seams for Postgres, object storage, a `SessionStore` and an auth gateway.

## Legacy

`agency import-legacy` reads the previous `runs/{project}/` layout (state.json, JSONL memory stores, intermediates, drafts, reviews, inputs) into the graph. The old orchestrator prompts and design spec are kept for reference under `docs/reference/`.
