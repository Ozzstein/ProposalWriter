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

## Stages and gates

| Stage | Plan | Gate in → out |
|---|---|---|
| ideate | setup → interview (session) → probes ∥ + evaluator → choose (inbox, ≤2 rework loops) | – |
| parse-call | locate inputs → call_parser ∥ eligibility_parser → merge with pack → approve (inbox) | → scope |
| research | kb_import → literature ∥ web ∥ patents → synthesize → novelty ∥ gaps | scope → evidence |
| write-proposal | prepare → draft:<excellence> → draft:<others> ∥ → draft:abstract | evidence → draft |
| finance | intake (files or form) → model → narrative ∥ → financial review | – |
| figures | preflight → render (≤4 parallel) → index | – |
| business-plan | prereq → interview (session, per-batch persistence) → synthesize → 4 writers ∥ → review → assemble | – |
| review | setup → scientific ∥ compliance ∥ panel → compile plan → revise loop | draft → submission |
| external-feedback | resolve round → parse files ∥ → ingest → triage (inbox) → dispatch by route → summary | → external_feedback |
| export | assemble md → docx | submission |

Gate rules are plain functions over the graph (`agency/policy/gates.py`); thresholds come from `agency/policy/thresholds.py`, overridable per pack and in `agency.toml`.

## Hosting seams

Local-first today (SQLite, local blobs, no auth). The `Store`/`BlobStore` interfaces, engine state fully in the store, workspace as the tenant unit, and the event log as the only cross-process channel are the seams for Postgres, object storage, a `SessionStore` and an auth gateway.

## Legacy

`agency import-legacy` reads the previous `runs/{project}/` layout (state.json, JSONL memory stores, intermediates, drafts, reviews, inputs) into the graph. The old orchestrator prompts and design spec are kept for reference under `docs/reference/`.
