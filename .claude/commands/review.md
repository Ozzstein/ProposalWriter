You are the Review & Compliance Orchestrator.

The reviewer roster, wiki context flow, and outputs are defined in `agents/orchestrators/review_orchestrator.md` — that file is the single source of truth. Do not improvise a different roster.

## Steps

1. **Project**: Run `python3 scripts/state.py projects`. If exactly one project exists, use it; otherwise ask the user.

2. **Prerequisites**: Run `python3 scripts/state.py show {project}`. Warn (don't block) if `writing` is not complete or the draft gate has not passed (`python3 scripts/gate_check.py {project} draft --no-write` shows why).

3. **Mark started**: `python3 scripts/state.py stage {project} review in_progress`

4. **Execute the orchestrator**: Read `agents/orchestrators/review_orchestrator.md` and execute it exactly as written:
   - **Phase 0** — collect wiki entities/gaps paths for the evaluator simulator (skip silently if no wiki)
   - Spawn all three reviewers **in parallel**: `scientific_reviewer`, `compliance_checker`, and `adversarial_evaluator_simulator` (the simulator receives the Phase 0 wiki context)

   Spawn each as a native subagent (`subagent_type` = the worker's name). Every task prompt must include:
   ```
   project: {project}
   dedupe_key: {task_slug}_{project}_r{round}    # round number allows re-review after revisions
   ```
   plus the inputs/outputs the orchestrator assigns (`reviews/scientific_review.json`, `reviews/compliance_review.json`, `reviews/evaluator_simulation.json`).

5. **Compile the revision plan**: Read all three review files and produce `runs/{project}/reviews/revision_plan.md`, ordered by estimated score impact with `evaluator_simulation.json`'s `improvement_actions_ranked` as the primary input:
   - Critical issues (must fix before submission — includes any hard-rejection risks)
   - High priority (significant score impact)
   - Medium/low suggestions

6. **Mark complete**: `python3 scripts/state.py stage {project} review complete`

7. **Present to user**:
   - Predicted per-criterion scores and funding probability from the evaluator simulation
   - **Any `hard_rejection_risk: true` findings — escalate these immediately and prominently**
   - Scientific scores per section and critical issues
   - Unsupported claims found
   - Compliance status per requirement
   - Top revision actions in priority order

8. **Ask user**: revise and re-review (re-run `/review` with the next round number after fixes), or proceed toward `/gate-check submission`?
