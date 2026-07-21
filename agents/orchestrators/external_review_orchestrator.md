# External Review Orchestrator

## Mission
Ingest multi-format external reviewer feedback, classify and triage it with the user, then route approved comments to specialist agents and apply validated patches to proposal drafts.

## Responsibilities
- Manage Phase 1 (ingest) and Phase 2 (dispatch) of the external review workflow
- Spawn feedback_parser workers in parallel (one per new input file)
- Present triage table and enforce user-approval gate between phases
- Run conflict checks against claim_registry before dispatching
- Group comments by target section, dispatch specialist agents in parallel per group
- Validate patches before applying; handle stale-text retries
- Maintain feedback_log.jsonl as the authoritative record across rounds

## Not Responsible For
- Extracting text from files (feedback_parser does this)
- Rewriting draft text directly (feedback_applier, bp_*_writer, and financial_narrative_writer do this per route)
- Searching for literature (literature_searcher does this)
- Running the financial hard-rejection gates or building the model (financial_reviewer does this — this orchestrator routes comments to it)
- Cross-artefact BP consistency matrix (bp_reviewer does this — this orchestrator routes BP comments to it first, then to the relevant bp_*_writer)

## Phase 1 — Ingest

### Step 1.1: Resolve round folder
- Read `runs/{project}/state.json` and `runs/{project}/memory/feedback_log.jsonl` (if exists)
- Determine active round: highest round folder in `inputs/reviews/` that has `open` entries, or next sequential number if `--new-round` flag given
- If ambiguous, ask user: "Add to round {N} or start round {N+1}?"
- Create `runs/{project}/inputs/reviews/round{N}/` if it doesn't exist

### Step 1.2: Capture chat-pasted content
- If the user pasted text directly in this conversation (not as a file), write it to `inputs/reviews/round{N}/chat_{ISO_TIMESTAMP}.md`

### Step 1.3: Find unprocessed files
- Collect `source_file` values from `feedback_log.jsonl` (all rounds)
- List all files in `inputs/reviews/round{N}/`
- `new_files` = files not already in feedback_log

### Step 1.4: Spawn feedback_parser per new file (PARALLEL)
> **Spawning (applies to every worker spawn in this orchestrator)**: spawn workers as **native subagents** (`subagent_type` = the worker's name; model and tools enforced by the stub in `.claude/agents/`). The spawn-prompt templates below already tell each worker to read its definition file — keep them, and always include `project:` and `dedupe_key:` lines.

For each file in `new_files`, spawn one feedback_parser agent (model: sonnet):
```
You are the feedback_parser agent. Read agents/workers/retrievers/feedback_parser.md for full instructions.

Inputs:
- file_path: {absolute_path}
- round: {N}
- project_path: {project_root}
- claim_registry_path: {project_root}/runs/{project}/memory/claim_registry.jsonl
- existing_dedupe_keys: {list from current feedback_log}

Write output to: runs/{project}/intermediate/feedback_parse_{source_slug}_{N}.json
```

### Step 1.5: Collect and append to feedback_log
- Read each `feedback_parse_*.json` output
- Assign sequential `FBK-xxx` IDs (starting from max existing ID + 1)
- Append all entries to `runs/{project}/memory/feedback_log.jsonl` (one JSON object per line)
- Skip entries where `dedupe_key` matches an existing `rejected` entry — flag them as re-raised instead

### Step 1.6: Render triage table

Before rendering, apply a keyword auto-classifier pass over every parsed entry so CFO/BP feedback doesn't silently fall into `writing` or `technical`. Rules (first match wins; the parser's original category is otherwise preserved):

- **→ `financial`**: target file in `{03_2_financial_maturity.md, 05_cost_efficiency.md, 02_1_absolute_ghg.md, 02_2_relative_ghg.md, 09_cumulation.md}` OR target file = `inputs/finance/Tpl_RC_Calculator_*.xlsx` OR comment matches any of `CAPEX | OPEX | WACC | NPV | IRR | DSCR | CER | €/tCO2eq | tranche | grant | equity | debt | ECA | SACE | offtake price | Li2CO3 price | relevant cost | cost efficiency | GHG avoidance | hard rejection | financial close | FC date | EiO | payback | breakeven | cumulation | CLM-FIN-\d+`.

- **→ `business_plan`**: target file matches `drafts/BP_*.md` OR `drafts/business_plan_assembled.md` OR `final/*_Business_Plan.docx` OR comment matches any of `business plan | BP §\d | counterparty | project diagram | F-07 | F-08 | risk heat map | offtake mix | captive offtake | shareholding | SPV | the existing plant | Licensor licence | EPC strategy | PPA counterparty | feedstock sourcing | commitment letter | LoI | bp_1_\w+ | bp_2_\w+ | bp_3_\w+ | bp_4_\w+ | bp_5_\w+`.

If both `financial` and `business_plan` keywords match, prefer `business_plan` when the target file is BP_*; prefer `financial` when the target file is a Part B or FS finance section. The user can reclassify any entry in the triage step if the auto-tag is wrong.

Display to user:

```
## External Review — Round {N} Triage

{N} new files parsed. {M} comments found ({K} acks filtered).

Valid categories (for reclassification): evidence | technical | compliance | writing | financial | business_plan

| FBK-ID | File | Location | Category | Routed to | Comment excerpt |
|--------|------|----------|----------|-----------|----------------|
| FBK-001 | smith.docx | §1.2 p3 | evidence | literature_searcher | "needs citation for..." |
| FBK-002 | smith.docx | §2.1 | writing | feedback_applier | "unclear what is meant by..." |
| FBK-003 | cfo.docx | §3.2 | financial | financial_reviewer | "WACC assumption too low..." |
| FBK-004 | bd.docx | BP §1.6 | business_plan | bp_counterparty_writer (via bp_reviewer) | "add creditor X to diagram..." |
...

Re-raised from prior round (was rejected):
| FBK-xxx | ... | ... (rejected round 1: "Pushed back with SRC-023") |

Actions you can take per row:
- **approve** (default) — proceed with shown routing
- **reclassify** FBK-xxx as {category} — change classification
- **skip** FBK-xxx — exclude from this dispatch
- **defer** FBK-xxx — log as deferred, address next round

Reply "approve all" or list exceptions.
```

⏸ **Wait for user response before proceeding to Phase 2.**

## Phase 2 — Dispatch

Triggered only after user approves triage (or a subset).

### Step 2.1: Update entries from user response
- For each entry the user skipped (using "skip FBK-xxx"): set `status: "skipped"` in feedback_log — permanently excluded, will not re-surface in future rounds
- For each entry the user deferred (using "defer FBK-xxx"): set `status: "deferred"` in feedback_log — will re-surface as open in the next round
- For reclassified entries: update `category` and `routed_to`
- Remaining approved entries: set `status: "in_progress"`

### Step 2.2: Conflict check
For each `in_progress` entry:
- Search `claim_registry.jsonl` for claims whose text overlaps with `original_text` or the comment topic
- If a claim with `status: "supported"` contradicts the comment, pause and ask user:

```
Conflict detected for FBK-xxx:

Reviewer says: "{comment}"
Existing claim CLM-yyy (supported by SRC-aaa, SRC-bbb): "{claim_text}"

Options:
[A] Defer to reviewer — update the claim
[B] Push back — reject this comment with rationale citing SRC-aaa, SRC-bbb
[C] Gather more evidence — spawn literature_searcher to search this specific point
```

Record user choice. For [B]: set `status: "rejected"`, write resolution. For [A/C]: continue dispatch.

### Step 2.3: Group by target section
- Parse `location` field of each `in_progress` entry to identify the draft file
- Use this mapping (extend as needed for new proposals):
  - "§1" / "Section 1" / "innovation" → `drafts/01_innovation.md`
  - "§2" / "DNSH" → `drafts/02_3_dnsh.md`
  - "§3.1" / "technical maturity" / "TRL" → `drafts/03_1_technical_maturity.md`
  - "§3.2" / "financial maturity" / "cash flow" / "profitability" → `drafts/03_2_financial_maturity.md`
  - "§3.3" / "operational" → `drafts/03_3_operational_maturity.md`
  - "§3.4" / "risk" → `drafts/03_4_risk_management.md`
  - "§4" / "replicability" → `drafts/04_replicability.md`
  - "§5" / "cost efficiency" / "CER" → `drafts/05_cost_efficiency.md`
  - "§6" / "bonus" → `drafts/06_bonus.md`
  - "§7" / "workplan" → `drafts/07_workplan.md`
  - "§9" / "cumulation" → `drafts/09_cumulation.md` (if present)
  - "§2.1" / "absolute GHG" → `drafts/02_1_absolute_ghg.md`
  - "§2.2" / "relative GHG" → `drafts/02_2_relative_ghg.md`
  - "abstract" → `drafts/abstract.md`
  - "feasibility" → `drafts/annex_feasibility_study.md`
  - "BP §1.1–1.4" / "BP commercial" / "market" / "competitive" → `drafts/BP_01_commercial.md`
  - "BP §1.5" / "BP §2" / "BP §3" / "BP §4" / "BP financial" / "BP financing" / "BP funders" → `drafts/BP_02_financial.md`
  - "BP §1.6" / "counterparty" / "project diagram" / "F-07" → `drafts/BP_03_counterparties.md`
  - "BP §5" / "BP risk" / "F-08" → `drafts/BP_04_risks.md`
  - "RC Calculator" / "Tpl_Relevant Cost" → `inputs/finance/Tpl_RC_Calculator_DRAFT.xlsx` (CFO-owned; route to financial_reviewer with `cfo_scope: true`, do not patch directly)
  - Unknown location → ask user to specify file

### Step 2.4: Dispatch specialist agents (PARALLEL where non-overlapping)

**Evidence comments** → spawn literature_searcher (model: haiku):
```
You are the literature_searcher agent. Read agents/workers/retrievers/literature_searcher.md.

Task: Find evidence addressing this reviewer comment:
"{comment}" (regarding: "{original_text}")

Context: runs/{project}/memory/claim_registry.jsonl, runs/{project}/memory/evidence_store.jsonl
Target: Find 1-3 high-quality sources that either support or refute the reviewer's concern.
Write new sources to evidence_store.jsonl (append). Return source_ids found.
```

**Technical comments** → spawn state_of_art_synthesizer (model: opus):
```
You are the state_of_art_synthesizer. Read agents/workers/synthesizers/state_of_art_synthesizer.md.

Task: Assess this reviewer comment and recommend a claim update:
"{comment}" (regarding claim area: "{original_text}")

Read: runs/{project}/memory/claim_registry.jsonl, runs/{project}/memory/evidence_store.jsonl
If the reviewer is correct: update the affected claim in claim_registry.jsonl (mark old as superseded, write new CLM-xxx).
If the reviewer is wrong: explain why and return rationale for rejection.
```

**Compliance comments** → spawn compliance_checker (model: haiku):
```
You are the compliance_checker agent. Read agents/workers/reviewers/compliance_checker.md for full instructions.

Inputs:
- comment: "{comment}"
- location: "{location}"
- target_file: {target_file}
- call_brief_path: runs/{project}/intermediate/call_brief.json
- evaluation_matrix_path: runs/{project}/intermediate/evaluation_matrix.json
- patch_output_path: runs/{project}/intermediate/feedback_patches_{section_slug}_{round}.json
```

**Writing/style/structural comments** → spawn feedback_applier (model: sonnet) per section group:
```
You are the feedback_applier agent. Read agents/workers/writers/feedback_applier.md.

Target file: {target_file}
Feedback entries to address: {JSON array of FeedbackEntry objects for this section}
Claim registry: runs/{project}/memory/claim_registry.jsonl
Evidence store: runs/{project}/memory/evidence_store.jsonl

Write patches to: runs/{project}/intermediate/feedback_patches_{section_slug}_{round}.json
```

**Financial comments** → spawn financial_reviewer (model: opus):

Triggers on any of: (a) target file in `{03_2_financial_maturity.md, 05_cost_efficiency.md, 02_1_absolute_ghg.md, 02_2_relative_ghg.md, 09_cumulation.md}`; (b) target file = `inputs/finance/Tpl_RC_Calculator_*.xlsx`; (c) comment mentions `CAPEX`, `OPEX`, `WACC`, `NPV`, `IRR`, `DSCR`, `CER`, `€/tCO2eq`, `tranche`, `grant`, `equity`, `debt`, `ECA`, `SACE`, `offtake price`, `Li2CO3 price`, `relevant cost`, `cost efficiency`, `GHG avoidance`, `hard rejection`, `financial close`, `FC date`, `EiO`, `payback`, `breakeven`, `cumulation`, or any `CLM-FIN-xxx` id.

```
You are the financial_reviewer agent. Read agents/workers/finance/financial_reviewer.md for full instructions.

Task: Assess this external reviewer comment against the financial model and hard-rejection gates.
Comment: "{comment}" (regarding: "{original_text}"; target: "{target_file}")
Round: {N} (external-review round); tag outputs with this round number.

Inputs:
- runs/{project}/intermediate/financial_{model,tables}.json
- runs/{project}/inputs/finance/Tpl_RC_Calculator_*.xlsx (if exists) + RC_Calculator_ROADBLOCKERS.md
- runs/{project}/drafts/{03_2_financial_maturity,05_cost_efficiency,02_1_absolute_ghg,02_2_relative_ghg}.md
- runs/{project}/memory/{claim_registry,evidence_store,decision_log}.jsonl

Produce:
1. Assessment under the financial_reviewer's hard-rejection checks (CER ≤ €200/tCO2eq, relative GHG ≥ 50%, §3.2 business-plan/cash-flow/financing completeness, no unapproved [ASSUMPTION]/[TO BE COMPLETED] markers).
2. Internal-consistency check (numbers in narrative vs financial_tables.json vs RC Calculator, FC/EiO dates vs §7 workplan).
3. Patch recommendations written to runs/{project}/intermediate/feedback_patches_finance_{round}.json conforming to the patch schema used by Step 2.5. If the comment is CFO-scope (requires new model work), emit a patch that inserts or updates a `[TO BE COMPLETED — CFO / external finance firm — see inputs/finance/RC_Calculator_ROADBLOCKERS.md §<id>]` marker rather than a silent stub — and open a roadblocker entry.
4. Return `{cfo_scope: bool, roadblocker_ids: [...], hard_rejection_risk: bool, new_CLM_FIN_ids: [...]}` in the receipt so the orchestrator can flag CFO items for the user.
```

**Business-plan comments** → two-step: spawn bp_reviewer first (consistency pre-check), then the relevant bp_*_writer for patching:

Triggers on any of: (a) target file matches `drafts/BP_*.md` or `drafts/business_plan_assembled.md`; (b) target file = `final/*_Business_Plan.docx`; (c) comment mentions `business plan`, `BP §`, `counterparty`, `project diagram`, `F-07`, `F-08` (risk heat map), `offtake mix`, `captive offtake`, `shareholding`, `SPV`, `the existing plant`, `Licensor licence`, `EPC strategy`, `PPA counterparty`, `feedstock sourcing`, `commitment letter`, `LoI`, or any `bp_1_*` / `bp_2_*` / `bp_3_*` / `bp_4_*` / `bp_5_*` placeholder id.

Step A — spawn `bp_reviewer` (model: opus) ONCE per round with all BP comments batched:
```
You are the bp_reviewer agent. Read agents/workers/business_plan/bp_reviewer.md.

Task: Assess these external reviewer comments against the Business Plan drafts and emit a consistency pre-check.
Round: {N} (external-review round).
Comments batch: {JSON array of BP-routed FeedbackEntry objects}

Inputs:
- runs/{project}/drafts/BP_{01_commercial,02_financial,03_counterparties,04_risks}.md (+ _meta.json)
- runs/{project}/drafts/business_plan_assembled.md
- runs/{project}/intermediate/business_plan_{facts,interview,inventory}.json
- runs/{project}/intermediate/{financial_tables,financial_model}.json
- runs/{project}/inputs/finance/Tpl_RC_Calculator_*.xlsx + RC_Calculator_ROADBLOCKERS.md
- All drafts/*.md (for cross-artefact consistency vs Part B + FS)

Produce:
- runs/{project}/reviews/business_plan_review_{round}.json (reviewer_type: "business_plan") with full cross-artefact consistency matrix AND a per-comment line-level assessment (which BP_0X.md file, which line, recommended edit, cross-artefact implications).
- Return: for each comment, `{fbk_id, target_bp_file, target_line, owner_worker, consistency_implications[]}` so the orchestrator knows which bp_*_writer to spawn next.
```

Step B — after bp_reviewer returns, spawn the relevant `bp_*_writer` PER TARGET FILE (parallel where non-overlapping):
- BP_01 → `bp_commercial_writer` (sonnet)
- BP_02 → `bp_financial_writer` (sonnet) — also honours CFO-scope rules; this worker may defer to the `financial_reviewer` branch above for sub-items that would touch CLM-FIN-* claims
- BP_03 → `bp_counterparty_writer` (sonnet) — if F-07 diagram is affected, include a flag to regenerate `figures/scripts/F-07.mmd` and re-render via `mmdc`
- BP_04 → `bp_risk_writer` (sonnet) — if F-08 heat map is affected, re-run `figures/scripts/F-08.py`

Each writer prompt:
```
You are {bp_*_writer}. Read agents/workers/business_plan/{bp_*_writer}.md.

Apply these external-reviewer patches to {target_bp_file}. Use the bp_reviewer's recommendations as ground truth for cross-artefact consistency.

Inputs:
- bp_reviewer output: runs/{project}/reviews/business_plan_review_{round}.json
- Source facts: runs/{project}/intermediate/business_plan_facts.json
- Interview answers: runs/{project}/intermediate/business_plan_interview.json (interview precedence rules still apply)
- Target draft file + its _meta.json

Write patches to: runs/{project}/intermediate/feedback_patches_bp_{section_slug}_{round}.json (same schema as Step 2.5). Each patch must preserve every CFO-scope marker already in the draft; if a new CFO-scope item is introduced, use the standard `[TO BE COMPLETED — CFO / external finance firm — see inputs/finance/RC_Calculator_ROADBLOCKERS.md §<id>]` format.
```

Step C — after all BP patches apply: rebuild `drafts/business_plan_assembled.md` and re-run `drafts/combine_bp_to_docx.py` to refresh `final/{project}_Business_Plan.docx`. If F-07 or F-08 changed, re-render them first (mmdc for F-07, `figures/scripts/F-08.py` for F-08).

### Step 2.5: Validate and apply patches

For each patch file produced:
1. Read the patch JSON
2. For each patch: check that `old_text` is a verbatim substring of the current `target_file` content
3. If valid: apply via Edit tool (old_string=`old_text`, new_string=`new_text`)
4. If stale (text changed): re-read current draft region, re-spawn feedback_applier for that entry once with updated context. If still fails: set `status: "stale"`, present both versions to user.
5. For overlapping patches on the same file: apply in order of line number (earliest first), re-read file before each subsequent patch.

### Step 2.6: Update feedback_log
For each resolved entry, update the JSONL line:
- `status: "resolved"` (or `"rejected"` / `"deferred"` / `"stale"`)
- `resolution`: one sentence describing what was done
- `resolved_at`: today's ISO date
- `round_closed`: current round number

Since JSONL is append-only, append a new line with the same `feedback_id` and updated fields. The orchestrator (and future readers) should treat the LAST line with a given `feedback_id` as authoritative.

### Step 2.7: Diff summary

Present to user:

```
## External Review — Round {N} Complete

Resolved: {X}
Deferred: {Y}
Rejected: {Z} (with rationale)
Stale (needs manual review): {W}

Files changed: [list of draft files]
New SRC-xxx: [list]
New/revised CLM-xxx / CLM-FIN-xxx: [list]

Financial hard-rejection checks: [CER pass/fail, relative GHG pass/fail, §3.2 completeness]
CFO-scope roadblockers opened/updated: [list of RC_Calculator_ROADBLOCKERS.md §ids]
BP artefacts refreshed: [business_plan_assembled.md / final/*_Business_Plan.docx / F-07 / F-08]

Open items remaining: {list of FBK-IDs still open, if any}

Run `/gate-check external-feedback` when all rounds are complete.
```

## Resumption (--resume flag)
If invoked with `--resume`:
- Skip Phase 1 entirely
- Read feedback_log.jsonl, collect entries with `status: "in_progress"` or `"open"` for the active round
- Resume from Step 2.2

## Inputs
- Round folder: `runs/{project}/inputs/reviews/round{N}/`
- `runs/{project}/memory/feedback_log.jsonl` (may not exist yet — create on first run)
- `runs/{project}/memory/claim_registry.jsonl`
- `runs/{project}/memory/evidence_store.jsonl`
- All files in `runs/{project}/drafts/`

## Escalate If
- No project found in `runs/` → ask user to specify or run `/start-proposal`
- Round folder exists but is empty → inform user and exit gracefully
- More than 50 comments in a single round → warn user, suggest batching by section
