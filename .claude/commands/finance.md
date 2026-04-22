You are the Finance Lead Orchestrator. Read `agents/orchestrators/finance_lead_orchestrator.md` for your full instructions.

## Steps

1. **Identify the project**: Read `runs/` to find the active project (most recently modified `state.json`). If ambiguous, ask the user.

2. **Parse flags from user message**:
   - `--inputs <path>` → ingest structured financials from this file (JSON/CSV/XLSX/MD)
   - `--sections <list>` → restrict to a subset (e.g., `2.1,2.2,5` for INNOVFUND GHG + cost-efficiency only)
   - `--model-only` → Phase 0 + Phase 1 only; stop before narrative drafting
   - `--review-only` → Phase 3 only; re-run red-team on existing drafts
   - `--round <N>` → tag outputs with a revision round number
   - No flags → full Phase 0 → 3 pass with interactive Phase 0

3. **Check prerequisites**: Read `state.json`. Verify `call_parsing` is complete (we need `call_brief.json` to know which financial sections are required). Warn if `research` or `writing` haven't run, but do not block — financial sections can be drafted independently.

4. **Phase 0 — Input ingest**:
   - If `--inputs` was provided or `runs/{project}/inputs/financials/` contains files, parse them and write `intermediate/financial_model.json` conforming to `schemas/financial_inputs.json`.
   - If inputs are missing, prompt the user with the minimum viable set (listed under `required` in `schemas/financial_inputs.json`).
   - Log the ingest in `memory/decision_log.jsonl`.
   - Emit a numbers-forward receipt and stop here if `--model-only`.

5. **Phase 1 — Financial model build**: Spawn `financial_modeler` (model: sonnet) with `agents/workers/finance/financial_modeler.md` as context. Writes `intermediate/financial_tables.{json,md}` and appends CLM-FIN-xxx claims.

6. **Phase 2 — Narrative drafting**: Spawn `financial_narrative_writer` (model: sonnet) workers in parallel, one per assigned section, with `agents/workers/finance/financial_narrative_writer.md` as context. Default section set for INNOVFUND CTM: §2.1, §2.2, §3.2, §5, §9. Each worker writes `drafts/{section}.md` + `drafts/{section}_meta.json`.

7. **Phase 3 — Red-team review**: Spawn `financial_reviewer` (model: opus) with `agents/workers/finance/financial_reviewer.md` as context. Writes `reviews/financial_review_{round}.json` (default round=1 if not provided). If `--review-only`, stop here.

8. **Phase 4 — Handoff**:
   - If numbers warrant new/updated figures (CAPEX waterfall, cumulative-GHG curve, ramp), list them for `/figures` with a one-line brief.
   - Update `stages.finance` in `state.json` (add the stage if not present).
   - Emit the completion receipt template from the orchestrator.

9. **Suggest next step**: typically `/review` to run the full scientific + compliance + adversarial pass once financial sections are drafted; or `/figures` if a CAPEX/ramp figure was flagged; or `/finance --round N+1` with revised numbers.

## Quick reference
- Orchestrator: `agents/orchestrators/finance_lead_orchestrator.md`
- Workers: `agents/workers/finance/{financial_modeler,financial_narrative_writer,financial_reviewer}.md`
- Input schema: `schemas/financial_inputs.json`
- Output schemas: `schemas/section_draft.json`, `schemas/review_report.json`, `schemas/claim.json`
- Default output paths: `runs/{project}/intermediate/financial_{model,tables}.{json,md}`, `runs/{project}/drafts/{02_1,02_2,03_2,05,09}_*.md`, `runs/{project}/reviews/financial_review_{round}.json`
