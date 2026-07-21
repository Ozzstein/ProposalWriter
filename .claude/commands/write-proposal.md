You are the Proposal Writing Orchestrator.

The agent roster, phase order, inputs, and rules are defined in `agents/orchestrators/proposal_writer_orchestrator.md` — that file is the single source of truth. Do not improvise a different roster.

## Steps

1. **Project**: Run `python3 scripts/state.py projects`. If exactly one project exists, use it; otherwise ask the user.

2. **Prerequisites**: Run `python3 scripts/state.py show {project}`. Warn (don't block) if `research` is not complete or the evidence gate has not passed (`python3 scripts/gate_check.py {project} evidence --no-write` shows why).

3. **Mark started**: `python3 scripts/state.py stage {project} writing in_progress`

4. **Execute the orchestrator**: Read `agents/orchestrators/proposal_writer_orchestrator.md` and execute its phases exactly as written:
   - **Phase 0** — wiki check; collect terminology/claim page paths for the writers (skip silently if no wiki)
   - **Phase 1** — spawn `excellence_writer` FIRST (it establishes the novelty narrative from `novelty_map.json` and `gap_analysis.json`); once its draft exists, spawn `impact_writer` and `implementation_writer` in parallel
   - **Phase 2** — after all sections are drafted, spawn `abstract_writer` last with the completed drafts as input

   Determine the concrete section list from `runs/{project}/intermediate/proposal_outline.md` and assign sections to writers per the orchestrator's roster. Spawn each worker as a native subagent (`subagent_type` = the worker's name). Every task prompt must include:
   ```
   project: {project}
   dedupe_key: {task_slug}_{project}    # e.g. excellence_writing_{project}
   ```
   plus the input/output paths and any wiki context from Phase 0.

5. **Mark complete**: `python3 scripts/state.py stage {project} writing complete`

6. **Present to user**: List drafted sections with word counts, claim coverage (all technical claims linked or marked `[ASSUMPTION]`), and any escalations from writers (missing evidence, contradictions, word-limit conflicts).

7. **Next step**: `/gate-check draft`, then `/review`.
