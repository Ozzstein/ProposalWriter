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
- Rewriting draft text directly (feedback_applier does this)
- Searching for literature (literature_searcher does this)

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
Display to user:

```
## External Review — Round {N} Triage

{N} new files parsed. {M} comments found ({K} acks filtered).

| FBK-ID | File | Location | Category | Routed to | Comment excerpt |
|--------|------|----------|----------|-----------|----------------|
| FBK-001 | smith.docx | §1.2 p3 | evidence | literature_searcher | "needs citation for..." |
| FBK-002 | smith.docx | §2.1 | writing | feedback_applier | "unclear what is meant by..." |
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
- For each entry the user skipped: set `status: "deferred"` in feedback_log
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
  - "§3.3" / "operational" → `drafts/03_3_operational_maturity.md`
  - "§3.4" / "risk" → `drafts/03_4_risk_management.md`
  - "§4" / "replicability" → `drafts/04_replicability.md`
  - "§6" / "bonus" → `drafts/06_bonus.md`
  - "§7" / "workplan" → `drafts/07_workplan.md`
  - "abstract" → `drafts/abstract.md`
  - "feasibility" → `drafts/annex_feasibility_study.md`
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
You are a compliance checker. The following reviewer comment flags a compliance issue:
"{comment}" (location: "{location}")

Read: runs/{project}/intermediate/call_brief.json, runs/{project}/intermediate/evaluation_matrix.json
Read the relevant draft section: {target_file}
Assess whether the comment is valid. If yes, produce a patch (old_text/new_text).
Write patch to runs/{project}/intermediate/feedback_patches_{section_slug}_{round}.json.
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
New/revised CLM-xxx: [list]

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
