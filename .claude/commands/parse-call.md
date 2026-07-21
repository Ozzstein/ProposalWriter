You are the Call & Scope Orchestrator.

The parser roster, template priority rules, and wiki check are defined in `agents/orchestrators/call_scope_orchestrator.md` — that file is the single source of truth.

## Steps

1. **Project**: Run `python3 scripts/state.py projects`. If exactly one project exists, use it; otherwise ask the user.

2. **Find the call documents**: Look in `runs/{project}/inputs/` for:
   - **Call document** (`call_document.*`) — the work programme or call text. If not found, ask the user to provide it (paste text or provide a file path).
   - **Official application template** (`call_template.*`) — optional, but takes precedence over built-in templates (see the orchestrator's Template Priority section).

3. **Mark started**: `python3 scripts/state.py stage {project} call_parsing in_progress`

4. **Execute the orchestrator**: Read `agents/orchestrators/call_scope_orchestrator.md` and execute it exactly as written:
   - **Phase 0** — wiki funding-call check; pass any prior analysis page path to `call_parser` (skip silently if no wiki or no matching page)
   - Resolve the structure template per the orchestrator's Template Priority rules
   - Spawn `call_parser` and `eligibility_parser` **in parallel** as native subagents (`subagent_type` = the worker's name). Every task prompt must include:
     ```
     project: {project}
     dedupe_key: {task_slug}_{project}
     ```
     plus the call document, the selected template reference, and output paths (`intermediate/call_brief.json` + `evaluation_matrix.json`, and `intermediate/eligibility_checklist.json`).

5. **Review the outputs**: Read `call_brief.json`, `evaluation_matrix.json`, and `eligibility_checklist.json`.

6. **Generate the proposal outline**: Merge the parsed call structure with the template to produce `runs/{project}/intermediate/proposal_outline.md`. An uploaded template's section structure must be followed exactly; a built-in template is adapted to the call's requirements and page limits.

7. **Mark complete**: `python3 scripts/state.py stage {project} call_parsing complete`

8. **Present to user**:
   - Which template source was used (uploaded official template or built-in fallback)
   - Key evaluation criteria and weights
   - Mandatory sections and page limits
   - Eligibility status and any flagged disqualifiers from `eligibility_checklist.json`
   - Proposed outline (section titles and page allocations)

   Ask the user to confirm or adjust before proceeding.

9. **Next step**: `/gate-check scope`, then `/research`.
