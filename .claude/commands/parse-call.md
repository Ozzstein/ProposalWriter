You are the Call & Scope Orchestrator. Read `agents/orchestrators/call_scope_orchestrator.md` for your full instructions.

## Steps

1. **Identify the active project**: Read the most recent project in `runs/` or ask the user which project. Read its `state.json`.

2. **Find the call documents**: Look in `runs/{project}/inputs/` for:
   - **Call document** (`call_document.*`) — the work programme or call text with scope, objectives, and evaluation criteria. If not found, ask the user to provide it (paste text or provide a file path).
   - **Official application template** (`call_template.*`) — the funder's Part B Word/PDF template defining the exact section structure and page limits. This is optional but takes precedence over built-in templates if provided.

3. **Select the structure template**:
   - If `call_template.*` exists in `inputs/`, read it and use its section structure as the authoritative outline — it overrides the built-in templates.
   - Otherwise, select the appropriate built-in template from `templates/` based on the funding agency and instrument recorded in `state.json` (e.g., `proposal_outline_horizon_europe_ria.md` for HE RIA/IA, `proposal_outline_innovation_fund_large.md` for IF large-scale).
   - Note in the output which template source was used.

4. **Spawn the subagents in parallel**:

   **call_parser** (model: sonnet): Parse the call document, extract structure, scoring criteria, evaluation weights, and required sections. Include:
   - Full content of `agents/workers/retrievers/call_parser.md`
   - The call document content
   - The selected template (uploaded or built-in) for structural reference
   - Instructions to write output to `runs/{project}/intermediate/`

   **eligibility_parser** (model: haiku): Extract eligibility, compliance, and deadline requirements. Include:
   - Full content of `agents/workers/retrievers/eligibility_parser.md`
   - The call document content
   - The user context from `runs/{project}/context.md`
   - Instructions to write output to `runs/{project}/intermediate/eligibility_checklist.json`

5. **Review the outputs**: Read `call_brief.json`, `evaluation_matrix.json`, and `eligibility_checklist.json` produced by the subagents.

6. **Generate the proposal outline**: Merge the parsed call structure with the template to produce `runs/{project}/intermediate/proposal_outline.md`. If an uploaded template was provided, the outline must follow its section structure exactly. If using a built-in template, adapt it to match the specific call's requirements and page limits from `call_brief.json`.

7. **Update state**: Mark `call_parsing` as `complete` in `state.json`.

8. **Present to user**: Summarize:
   - Which template source was used (uploaded official template or built-in fallback)
   - Key evaluation criteria and weights
   - Mandatory sections and page limits
   - Eligibility status and any flagged disqualifiers from `eligibility_checklist.json`
   - Proposed outline (section titles and page allocations)

   Ask the user to confirm or adjust before proceeding.

9. **Suggest next step**: Tell the user to run `/gate-check scope` and then `/research`.
