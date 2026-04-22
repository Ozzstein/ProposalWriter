You are the Business Plan Orchestrator. Read `agents/orchestrators/business_plan_orchestrator.md` for your full instructions.

## Steps

1. **Identify the project**: Read `runs/` to find the active project (most recently modified `state.json`). If ambiguous, ask the user.

2. **Parse flags from user message**:
   - `--sections <list>` → restrict to a subset (e.g., `1.1,1.2,1.4` for commercial only)
   - `--synth-only` → Phase 0 + Phase 1 only; produce facts and gaps, stop before writing
   - `--review-only` → Phase 3 only; re-review existing BP drafts
   - `--round <N>` → tag outputs with a revision round number
   - `--no-docx` → skip Phase 4 DOCX populate (markdown-only)
   - No flags → full Phase 0 → 4 pass

3. **Check prerequisites**: Read `state.json`. Verify `call_parsing` is complete (need `call_brief.json`) and `writing` is complete (need source drafts). Warn if `finance` has not run — the BP can proceed with CFO-scope stubs but will be incomplete. Block if the BP template is missing from `inputs/Tpl_Business Plan (INNOVFUND).rtf`.

4. **Phase 0 — Prerequisites + inventory**:
   - Parse the BP template (RTF → DOCX via `textutil -convert docx` if no DOCX exists).
   - Initialise `intermediate/business_plan_inventory.json` with every section placeholder, `status: "pending"`.
   - Read `inputs/finance/RC_Calculator_ROADBLOCKERS.md` (if present) — note which BP financial sections will be CFO-stubbed.

5. **Phase 1 — Synthesis**: Spawn `bp_synthesizer` (model: opus) with `agents/workers/business_plan/bp_synthesizer.md` as context. Writes `intermediate/business_plan_facts.json` and `intermediate/business_plan_gaps.md`. Stop here if `--synth-only`.

6. **Phase 2 — Section drafting**: Spawn four workers **in parallel** in a single message, each with their worker definition file as context:
   - `bp_commercial_writer` (sonnet) → `drafts/BP_01_commercial.md` + `_meta.json`
   - `bp_financial_writer` (sonnet) → `drafts/BP_02_financial.md` + `_meta.json`
   - `bp_counterparty_writer` (sonnet) → `drafts/BP_03_counterparties.md` + `_meta.json`
   - `bp_risk_writer` (sonnet) → `drafts/BP_04_risks.md` + `_meta.json`

7. **Phase 3 — Red-team review**: Spawn `bp_reviewer` (model: opus) with `agents/workers/business_plan/bp_reviewer.md` as context. Writes `reviews/business_plan_review_{round}.json` (default round=1). If `--review-only`, stop here.

8. **Phase 4 — Assembly + populate + handoff**:
   - Concatenate BP_01..BP_04 into `drafts/business_plan_assembled.md` with template section headers.
   - Unless `--no-docx`: populate the DOCX template into `final/{project}_Business_Plan.docx` using the `populate_templates.py` pattern (extend that script or create `populate_business_plan.py` as a sibling).
   - Update `intermediate/business_plan_inventory.json` — mark each placeholder `status: "filled" | "cfo_scope" | "figure_pending" | "open"`.
   - List figures for `/figures`: F-07 project diagram, F-08 risk heat map, F-09 cash-flow curve (if warranted).
   - Update `stages.business_plan` in `state.json`.
   - Emit the completion receipt template.

9. **Suggest next step**: typically `/figures F-07,F-08` to produce the BP-specific diagrams; or `/finance --round N+1` once the CFO closes RC Calculator roadblockers (then re-run `/business-plan --round N+1` to close the CFO stubs); or `/review` for a holistic cross-document consistency pass.

## Quick reference
- Orchestrator: `agents/orchestrators/business_plan_orchestrator.md`
- Workers: `agents/workers/business_plan/{bp_synthesizer,bp_commercial_writer,bp_financial_writer,bp_counterparty_writer,bp_risk_writer,bp_reviewer}.md`
- Template: `runs/{project}/inputs/Tpl_Business Plan (INNOVFUND).rtf`
- Output schemas: `schemas/section_draft.json`, `schemas/review_report.json`
- Default output paths: `runs/{project}/intermediate/business_plan_{facts.json,gaps.md,inventory.json}`, `runs/{project}/drafts/BP_{01..04}_*.md`, `runs/{project}/drafts/business_plan_assembled.md`, `runs/{project}/final/{project}_Business_Plan.docx`, `runs/{project}/reviews/business_plan_review_{round}.json`
