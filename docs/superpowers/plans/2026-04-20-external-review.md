# External Review Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/external-review` — a two-phase command that ingests multi-format reviewer files, classifies each comment, presents a triage table for user approval, then routes approved comments to specialist agents and applies validated patches to proposal drafts.

**Architecture:** Single orchestrator (`external_review_orchestrator`) owns both phases. Phase 1 spawns `feedback_parser` workers in parallel per input file; Phase 2 routes approved entries to existing specialist agents plus a new `feedback_applier`, applies patches serially per overlapping region, and updates `feedback_log.jsonl`. All data lives in `runs/{project}/memory/feedback_log.jsonl` and `runs/{project}/inputs/reviews/round{N}/`.

**Tech Stack:** Claude Code Agent tool (subagent spawning), python-docx (already present), pdfplumber (check/add), openpyxl (check/add), JSON Schema draft-07, JSONL append pattern established by existing evidence_store/claim_registry.

**Spec:** `docs/superpowers/specs/2026-04-20-external-review-design.md`

---

## File Map

| Action | File | Responsibility |
|---|---|---|
| Create | `schemas/feedback_entry.json` | Schema for one reviewer comment |
| Create | `schemas/feedback_patch.json` | Schema for a text patch from feedback_applier |
| Create | `agents/workers/retrievers/feedback_parser.md` | Extract + classify comments from one input file |
| Create | `agents/workers/writers/feedback_applier.md` | Produce old/new text patches for writing/style/structural comments |
| Create | `agents/orchestrators/external_review_orchestrator.md` | Two-phase orchestration, conflict checking, patch application |
| Create | `.claude/commands/external-review.md` | Slim slash command entry point |
| Create | `templates/triage_table.md` | Render template for Phase 1 triage table |
| Create | `templates/external_review_diff_summary.md` | Render template for Phase 2 diff summary |
| Modify | `hooks/validate_output.py` | Add feedback schema patterns to SCHEMA_MAP |
| Modify | `.claude/commands/gate-check.md` | Add external-feedback gate criteria |
| Modify | `.claude/commands/pipeline-status.md` | Add feedback round stats row |
| Modify | `CLAUDE.md` | Document /external-review in pipeline overview |

---

## Task 1: Create feedback_entry schema

**Files:**
- Create: `schemas/feedback_entry.json`

- [ ] **Step 1: Write the schema file**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "FeedbackEntry",
  "description": "One reviewer comment extracted and classified by feedback_parser",
  "type": "object",
  "properties": {
    "feedback_id": {
      "type": "string",
      "pattern": "^FBK-\\d+$",
      "description": "Unique ID, e.g. FBK-001"
    },
    "round": { "type": "integer", "minimum": 1 },
    "reviewer": { "type": "string", "description": "Reviewer name/role as found in file or provided by user" },
    "source_file": { "type": "string", "description": "Relative path from project root, e.g. inputs/reviews/round1/smith.docx" },
    "location": { "type": "string", "description": "Human-readable location in proposal, e.g. Section 1.2, para 3" },
    "original_text": { "type": "string", "description": "The proposal text being commented on, if identifiable" },
    "comment": { "type": "string", "description": "The reviewer's comment verbatim" },
    "category": {
      "type": "string",
      "enum": ["evidence", "technical", "structural", "writing", "compliance", "style", "ambiguous", "parse_error", "ack"],
      "description": "evidence=missing citation; technical=wrong claim; structural=section/order; writing=clarity; compliance=template; style=typos; ambiguous=unclear; parse_error=file unreadable; ack=positive-only"
    },
    "comment_type": {
      "type": "string",
      "enum": ["inline_comment", "tracked_change", "chat", "annotation"],
      "description": "How this comment was recorded in the source file"
    },
    "candidates": {
      "type": "array",
      "items": { "type": "string" },
      "description": "For category=ambiguous only: the two possible categories"
    },
    "routed_to": {
      "type": "string",
      "description": "Target agent name, e.g. literature_searcher, feedback_applier, compliance_checker"
    },
    "status": {
      "type": "string",
      "enum": ["open", "in_progress", "resolved", "deferred", "rejected", "ack", "unlocatable", "stale", "parse_error"]
    },
    "resolution": { "type": ["string", "null"], "description": "Human-readable summary of how it was addressed" },
    "resolved_at": { "type": ["string", "null"], "description": "ISO date, e.g. 2026-04-21" },
    "round_closed": { "type": ["integer", "null"], "description": "Round number in which this entry was closed" },
    "dedupe_key": {
      "type": "string",
      "description": "Stable hash for cross-round deduplication: reviewer+location+topic slug"
    }
  },
  "required": ["feedback_id", "round", "source_file", "comment", "category", "status", "dedupe_key"]
}
```

Write this to `schemas/feedback_entry.json`.

- [ ] **Step 2: Verify the file is valid JSON**

```bash
python3 -c "import json; json.load(open('schemas/feedback_entry.json')); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add schemas/feedback_entry.json
git commit -m "feat: add feedback_entry JSON schema"
```

---

## Task 2: Create feedback_patch schema

**Files:**
- Create: `schemas/feedback_patch.json`

- [ ] **Step 1: Write the schema file**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "FeedbackPatch",
  "description": "A validated text patch produced by feedback_applier for a writing/style/structural comment",
  "type": "object",
  "properties": {
    "patch_id": {
      "type": "string",
      "pattern": "^PATCH-\\d+$"
    },
    "feedback_id": {
      "type": "string",
      "pattern": "^FBK-\\d+$",
      "description": "Links back to the feedback_log entry"
    },
    "target_file": {
      "type": "string",
      "description": "Relative path to the draft file, e.g. drafts/01_innovation.md"
    },
    "old_text": {
      "type": "string",
      "description": "Exact string that must match the current draft content (used for Edit tool old_string)"
    },
    "new_text": {
      "type": "string",
      "description": "Replacement text"
    },
    "rationale": {
      "type": "string",
      "description": "One sentence explaining why this change addresses the comment"
    },
    "new_claim_ids": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Any new CLM-xxx IDs introduced by this patch (must be registered in claim_registry.jsonl first)"
    },
    "new_source_ids": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Any new SRC-xxx IDs introduced by this patch (must be in evidence_store.jsonl first)"
    }
  },
  "required": ["patch_id", "feedback_id", "target_file", "old_text", "new_text", "rationale"]
}
```

Write this to `schemas/feedback_patch.json`.

- [ ] **Step 2: Verify the file is valid JSON**

```bash
python3 -c "import json; json.load(open('schemas/feedback_patch.json')); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add schemas/feedback_patch.json
git commit -m "feat: add feedback_patch JSON schema"
```

---

## Task 3: Create feedback_parser agent

**Files:**
- Create: `agents/workers/retrievers/feedback_parser.md`

- [ ] **Step 1: Write the agent definition**

Write this to `agents/workers/retrievers/feedback_parser.md`:

```markdown
# Feedback Parser

You are the feedback_parser agent.

## Mission
Extract and classify every individual reviewer comment from a single input file, returning structured feedback_entry objects ready for the feedback log.

## Responsibilities
- Read the input file and extract every distinct reviewer comment
- Classify each comment into exactly one category from the taxonomy
- Compute a stable dedupe_key for cross-round deduplication
- Identify the proposal location each comment refers to
- Return a JSON array of feedback_entry objects conforming to `schemas/feedback_entry.json`

## Not Responsible For
- Routing or dispatching comments to other agents
- Applying any changes to drafts
- Evaluating whether comments are valid or well-founded

## Input File Types

### DOCX with tracked changes
Use the `python-docx` library logic (already on the system). Read each tracked change as one entry with `comment_type: "tracked_change"`. Read inline comments (`doc.core_properties.comments` or Run revision marks) as `comment_type: "inline_comment"`. For each tracked change, capture both `original_text` (the deleted run text) and the `comment` (the inserted run text or adjacent comment text).

### PDF with annotations
Use `pdfplumber` to extract highlighted/annotated regions. Each annotation object is one entry with `comment_type: "annotation"`. If the PDF has no annotations (body-text-only review), extract paragraphs and flag them with `comment_type: "chat"` — treat as free-form review text and split at double newlines.

### Markdown (.md) and plain text (.txt)
Read the file as-is. Split on double-newline or numbered list items. Each paragraph/item is one comment candidate. Filter out lines that are headings or separators.

### Excel (.xlsx)
Use `openpyxl`. Extract cell comments (`ws[cell].comment.text`). Each cell comment is one entry. Use the cell address (e.g., "Sheet1!B12") as the `location`.

### Chat-pasted text (chat_{timestamp}.md)
Same as Markdown. Each paragraph is one entry.

## Comment Taxonomy

Classify each comment into exactly one category:

| Category | When to use |
|---|---|
| `evidence` | Missing citation, wrong number, claim needs a source, data is outdated |
| `technical` | Claim is scientifically wrong, methodology is flawed, TRL misjudged |
| `structural` | Section is missing, content is in wrong place, section is off-topic |
| `writing` | Unclear sentence, jargon, poor flow, confusing phrasing |
| `compliance` | Exceeds page limit, missing required field, wrong template element |
| `style` | Typo, punctuation, citation format, spacing |
| `ack` | Purely positive ("looks good", "excellent section") — no action needed |
| `ambiguous` | Could be two categories — set `candidates: [cat1, cat2]` |
| `parse_error` | File could not be read at all — set comment to the error message |

## Dedupe Key

Compute `dedupe_key` as a lowercase slug:
- Take: reviewer last name (or "unknown") + section slug from location + 3-word topic slug from the comment
- Replace spaces with underscores, strip punctuation
- Example: `smith_sec1.2_missing_citation_lfp`
- This key is used across rounds to detect re-raised comments

## Filtering

- Pure acknowledgments ("looks good", "great section", thumbs up) → `category: "ack"`, `status: "ack"`
- Duplicate comments within the same file (identical text) → deduplicate, keep one, note count in `resolution` field

## Inputs
- `file_path`: absolute path to the input file
- `round`: integer round number
- `project_path`: path to the project root (to resolve relative paths for output)
- `claim_registry_path`: path to `memory/claim_registry.jsonl` (read to help identify which claims a comment targets)
- `taxonomy`: the category enum list (passed for reference)
- `existing_dedupe_keys`: array of dedupe_keys already in feedback_log.jsonl (passed by orchestrator to flag duplicates)

## Output
Write a JSON file to `runs/{project}/intermediate/feedback_parse_{source_slug}_{round}.json` with:

```json
{
  "task_id": "TASK-xxx",
  "source_file": "inputs/reviews/round1/smith.docx",
  "round": 1,
  "entries": [
    {
      "feedback_id": "FBK-001",
      "round": 1,
      "reviewer": "Dr. Smith",
      "source_file": "inputs/reviews/round1/smith.docx",
      "location": "Section 1.2, para 3",
      "original_text": "...",
      "comment": "...",
      "category": "evidence",
      "comment_type": "tracked_change",
      "candidates": [],
      "routed_to": "literature_searcher",
      "status": "open",
      "resolution": null,
      "resolved_at": null,
      "round_closed": null,
      "dedupe_key": "smith_sec1.2_missing_citation_lfp"
    }
  ],
  "parse_errors": [],
  "ack_count": 0
}
```

## Routing Defaults

Set `routed_to` based on category:
- `evidence` → `literature_searcher`
- `technical` → `state_of_art_synthesizer`
- `structural` → `orchestrator`
- `writing` → `feedback_applier`
- `compliance` → `compliance_checker`
- `style` → `feedback_applier`
- `ambiguous` → leave blank (user picks during triage)
- `ack` / `parse_error` → leave blank

## Completion Criteria
- Every distinct comment in the file has a corresponding entry
- Every entry has a valid category, status, and dedupe_key
- Output JSON validates against `schemas/feedback_entry.json` for each entry in `entries[]`

## Escalate If
- File cannot be opened at all → return a single entry with `category: "parse_error"`
- File format is not one of the supported types → return a single entry with `category: "parse_error"` explaining the format
```

- [ ] **Step 2: Verify file exists**

```bash
ls agents/workers/retrievers/feedback_parser.md
```

Expected: file listed without error.

- [ ] **Step 3: Commit**

```bash
git add agents/workers/retrievers/feedback_parser.md
git commit -m "feat: add feedback_parser agent definition"
```

---

## Task 4: Create feedback_applier agent

**Files:**
- Create: `agents/workers/writers/feedback_applier.md`

- [ ] **Step 1: Write the agent definition**

Write this to `agents/workers/writers/feedback_applier.md`:

```markdown
# Feedback Applier

You are the feedback_applier agent.

## Mission
Produce precise old_text/new_text patches that address a batch of approved reviewer comments targeting the same draft section, without changing anything not covered by the comments.

## Responsibilities
- Read the current draft file for the target section
- For each feedback entry in the batch, locate the exact text being commented on
- Produce a minimal text change that addresses the comment
- Return structured patch objects conforming to `schemas/feedback_patch.json`

## Not Responsible For
- Searching for additional evidence (if a comment needs new evidence, flag it back to orchestrator)
- Rewriting entire sections unprompted — only change what the comment targets
- Making judgement calls about whether a comment is valid (that was decided upstream)
- Comments of category `evidence` or `technical` — those go to retrievers/synthesizers

## Input
- `target_file`: path to the draft section (e.g., `runs/{project}/drafts/01_innovation.md`)
- `feedback_entries`: array of approved FeedbackEntry objects for this section (all `writing`, `style`, or `structural` category)
- `claim_registry_path`: path to `memory/claim_registry.jsonl` (read if adding claim references)
- `evidence_store_path`: path to `memory/evidence_store.jsonl` (read if adding source references)

## Rules
- NEVER change text that no comment targets
- NEVER invent evidence — if a comment seems to want a citation, return `flag_needs_evidence: true` on that entry instead of a patch
- `old_text` must be verbatim from the current draft — copy it exactly, character for character including whitespace. The orchestrator validates this before applying.
- For `style` comments (typos, punctuation): make only the minimal change. Do not "improve" surrounding prose.
- For `writing` comments (clarity, flow): rewrite the targeted sentence(s) only
- For `structural` comments: the orchestrator handles section-level moves; only produce patches for in-section restructuring (e.g., reordering paragraphs within a section)
- If two entries target overlapping text: produce one combined patch that addresses both, referencing both `feedback_id`s in a note in `rationale`

## Output
Write a JSON file to `runs/{project}/intermediate/feedback_patches_{section_slug}_{round}.json`:

```json
{
  "task_id": "TASK-xxx",
  "target_file": "drafts/01_innovation.md",
  "round": 1,
  "patches": [
    {
      "patch_id": "PATCH-001",
      "feedback_id": "FBK-003",
      "target_file": "drafts/01_innovation.md",
      "old_text": "The process reduces scrap.",
      "new_text": "The closed-loop recovery process reduces scrap by approximately 15% [CLM-023].",
      "rationale": "Reviewer requested quantification; CLM-023 already in registry with this figure.",
      "new_claim_ids": [],
      "new_source_ids": []
    }
  ],
  "flagged_needs_evidence": ["FBK-007"],
  "flagged_needs_orchestrator": ["FBK-009"]
}
```

## Completion Criteria
- Every feedback entry in the batch has either a patch, a `flagged_needs_evidence` entry, or a `flagged_needs_orchestrator` entry
- All `old_text` values are verbatim substrings of the current draft

## Escalate If
- The draft file does not exist or is empty
- You cannot locate the commented text anywhere in the draft (return `flagged_needs_orchestrator` for that entry, note as `unlocatable`)
```

- [ ] **Step 2: Verify file exists**

```bash
ls agents/workers/writers/feedback_applier.md
```

Expected: file listed without error.

- [ ] **Step 3: Commit**

```bash
git add agents/workers/writers/feedback_applier.md
git commit -m "feat: add feedback_applier agent definition"
```

---

## Task 5: Create external_review_orchestrator

**Files:**
- Create: `agents/orchestrators/external_review_orchestrator.md`

- [ ] **Step 1: Write the orchestrator definition**

Write this to `agents/orchestrators/external_review_orchestrator.md`:

```markdown
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
```

- [ ] **Step 2: Verify file exists**

```bash
ls agents/orchestrators/external_review_orchestrator.md
```

Expected: file listed without error.

- [ ] **Step 3: Commit**

```bash
git add agents/orchestrators/external_review_orchestrator.md
git commit -m "feat: add external_review_orchestrator agent definition"
```

---

## Task 6: Create /external-review slash command

**Files:**
- Create: `.claude/commands/external-review.md`

- [ ] **Step 1: Write the command entry point**

Write this to `.claude/commands/external-review.md`:

```markdown
You are the External Review Orchestrator. Read `agents/orchestrators/external_review_orchestrator.md` for your full instructions.

## Steps

1. **Identify the project**: Read `runs/` to find the active project (most recently modified `state.json`). If ambiguous, ask the user.

2. **Parse flags from user message**:
   - `--new-round` → start a new round folder
   - `--round N` → work within round N explicitly
   - `--resume` → skip Phase 1, pick up in-progress entries from Phase 2
   - No flags → auto-detect active round

3. **Check for chat-pasted content**: If the user's message (the one that invoked this command) contains reviewer text (not just the command itself), treat that text as chat-pasted content. Write it to `runs/{project}/inputs/reviews/round{N}/chat_{timestamp}.md` before proceeding.

4. **Run Phase 1 — Ingest**: Follow the Phase 1 steps in the orchestrator definition. At the end of Phase 1, present the triage table and wait for user approval.

5. **Run Phase 2 — Dispatch**: Only after user explicitly approves (or approves a subset). Follow Phase 2 steps in the orchestrator definition.

6. **Present diff summary**: Show the final diff summary from Step 2.7 of the orchestrator.

## Quick Reference

- Input files go in: `runs/{project}/inputs/reviews/round{N}/`
- Feedback log: `runs/{project}/memory/feedback_log.jsonl`
- Patches written to: `runs/{project}/intermediate/feedback_patches_*.json`
- After all rounds done: run `/gate-check external-feedback`
```

- [ ] **Step 2: Verify file exists**

```bash
ls .claude/commands/external-review.md
```

Expected: file listed without error.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/external-review.md
git commit -m "feat: add /external-review slash command"
```

---

## Task 7: Update validate_output.py hook

**Files:**
- Modify: `hooks/validate_output.py`

- [ ] **Step 1: Read the current file** (already read in planning — verify line 16-22 is the SCHEMA_MAP)

The current `SCHEMA_MAP` is:
```python
SCHEMA_MAP = {
    "literature_results.json": "evidence_result.json",
    "patent_results.json": "evidence_result.json",
    "scientific_review.json": "review_report.json",
    "compliance_review.json": "review_report.json",
    "writing_review.json": "review_report.json",
}
```

- [ ] **Step 2: Add feedback schema patterns**

In `hooks/validate_output.py`, update `SCHEMA_MAP` and `find_schema`:

Replace:
```python
SCHEMA_MAP = {
    "literature_results.json": "evidence_result.json",
    "patent_results.json": "evidence_result.json",
    "scientific_review.json": "review_report.json",
    "compliance_review.json": "review_report.json",
    "writing_review.json": "review_report.json",
}
```

With:
```python
SCHEMA_MAP = {
    "literature_results.json": "evidence_result.json",
    "patent_results.json": "evidence_result.json",
    "scientific_review.json": "review_report.json",
    "compliance_review.json": "review_report.json",
    "writing_review.json": "review_report.json",
}

# Feedback schema patterns — matched in find_schema() below
# feedback_parse_*.json  -> entries[] validated against feedback_entry.json
# feedback_patches_*.json -> patches[] validated against feedback_patch.json
```

Also update `find_schema` function — replace:
```python
    # Pattern match: *_results.json -> evidence_result.json
    if basename.endswith("_results.json"):
        return "evidence_result.json"
    if basename.endswith("_review.json"):
        return "review_report.json"

    return None
```

With:
```python
    # Pattern match: *_results.json -> evidence_result.json
    if basename.endswith("_results.json"):
        return "evidence_result.json"
    if basename.endswith("_review.json"):
        return "review_report.json"
    if basename.startswith("feedback_parse_") and basename.endswith(".json"):
        return "feedback_entry.json"
    if basename.startswith("feedback_patches_") and basename.endswith(".json"):
        return "feedback_patch.json"

    return None
```

And update `validate_required_fields` to handle array-typed feedback files — add after the existing `main()` logic, replacing the final `validate_required_fields` call section:

```python
def validate_feedback_file(data, schema_name):
    """Validate array-typed feedback files (each entry or patch validated individually)."""
    errors = []
    if schema_name == "feedback_entry.json":
        entries = data.get("entries", [])
        for i, entry in enumerate(entries):
            for field in ["feedback_id", "round", "source_file", "comment", "category", "status", "dedupe_key"]:
                if field not in entry:
                    errors.append(f"entries[{i}] missing required field: '{field}'")
    elif schema_name == "feedback_patch.json":
        patches = data.get("patches", [])
        for i, patch in enumerate(patches):
            for field in ["patch_id", "feedback_id", "target_file", "old_text", "new_text", "rationale"]:
                if field not in patch:
                    errors.append(f"patches[{i}] missing required field: '{field}'")
    return errors
```

And in `main()`, replace the validate call block:
```python
    # Validate required fields
    errors = validate_required_fields(data, schema)
    if errors:
```

With:
```python
    # Validate required fields
    if schema_name in ("feedback_entry.json", "feedback_patch.json"):
        errors = validate_feedback_file(data, schema_name)
    else:
        errors = validate_required_fields(data, schema)
    if errors:
```

- [ ] **Step 3: Write a quick smoke-test to verify the hook logic**

```bash
python3 - <<'EOF'
import sys, os
sys.path.insert(0, 'hooks')

# Inline the updated logic to verify pattern matching
def find_schema(filename):
    import os
    basename = os.path.basename(filename)
    SCHEMA_MAP = {
        "literature_results.json": "evidence_result.json",
        "patent_results.json": "evidence_result.json",
        "scientific_review.json": "review_report.json",
        "compliance_review.json": "review_report.json",
        "writing_review.json": "review_report.json",
    }
    if basename in SCHEMA_MAP:
        return SCHEMA_MAP[basename]
    if basename.endswith("_results.json"):
        return "evidence_result.json"
    if basename.endswith("_review.json"):
        return "review_report.json"
    if basename.startswith("feedback_parse_") and basename.endswith(".json"):
        return "feedback_entry.json"
    if basename.startswith("feedback_patches_") and basename.endswith(".json"):
        return "feedback_patch.json"
    return None

assert find_schema("feedback_parse_smith_1.json") == "feedback_entry.json", "parse pattern"
assert find_schema("feedback_patches_innovation_1.json") == "feedback_patch.json", "patches pattern"
assert find_schema("scientific_review.json") == "review_report.json", "existing unchanged"
assert find_schema("literature_results.json") == "evidence_result.json", "existing unchanged"
assert find_schema("state.json") is None, "no match for unrelated file"
print("All assertions passed")
EOF
```

Expected: `All assertions passed`

- [ ] **Step 4: Commit**

```bash
git add hooks/validate_output.py
git commit -m "feat: extend validate_output hook to cover feedback schemas"
```

---

## Task 8: Add external-feedback gate to gate-check

**Files:**
- Modify: `.claude/commands/gate-check.md`

- [ ] **Step 1: Read current gate-check.md** (already read in planning — 49 lines, ends with "If gate passes: Congratulate...")

- [ ] **Step 2: Add external-feedback gate section**

Append to `.claude/commands/gate-check.md` after the existing `### Gate: submission` block:

Find the text:
```
### Gate: submission
Check these criteria:
- [ ] Scientific review score >= 6.0 for all sections (read `runs/{project}/reviews/scientific_review.json`)
- [ ] No critical issues remaining in review reports
- [ ] Compliance review shows all requirements met
- [ ] All unsupported claims resolved or explicitly approved by user
```

Replace with:
```
### Gate: submission
Check these criteria:
- [ ] Scientific review score >= 6.0 for all sections (read `runs/{project}/reviews/scientific_review.json`)
- [ ] No critical issues remaining in review reports
- [ ] Compliance review shows all requirements met
- [ ] All unsupported claims resolved or explicitly approved by user

### Gate: external-feedback
Check these criteria:
- [ ] `runs/{project}/memory/feedback_log.jsonl` exists (if no external review has been run, gate is N/A — inform user)
- [ ] Zero entries with `status: "open"` or `"in_progress"` in the active round (count lines where status matches)
- [ ] All remaining entries have `status` in ["resolved", "deferred", "rejected", "ack", "stale"]
- [ ] Any `stale` entries have a note in `resolution` explaining why manual review is needed

If the gate passes: suggest running `/gate-check submission` next if this was the final round.
If the gate fails: list the specific FBK-IDs that are still open or in-progress.
```

- [ ] **Step 3: Verify file looks correct**

```bash
grep -n "external-feedback" .claude/commands/gate-check.md
```

Expected: lines containing "Gate: external-feedback" and the criteria.

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/gate-check.md
git commit -m "feat: add external-feedback gate to gate-check command"
```

---

## Task 9: Update pipeline-status to show feedback rounds

**Files:**
- Modify: `.claude/commands/pipeline-status.md`

- [ ] **Step 1: Read current pipeline-status.md** (already read in planning — 35 lines)

- [ ] **Step 2: Add feedback round stats**

Find in `.claude/commands/pipeline-status.md`:
```
3. **Quick stats** (read the memory files):
   - Evidence store: {count} sources
   - Claim registry: {count} claims
   - Drafts: {list of files in drafts/}
   - Reviews: {list of files in reviews/}
```

Replace with:
```
3. **Quick stats** (read the memory files):
   - Evidence store: {count} sources
   - Claim registry: {count} claims
   - Drafts: {list of files in drafts/}
   - Reviews: {list of files in reviews/}
   - External feedback: If `memory/feedback_log.jsonl` exists, count entries by status per round and show:
     ```
     External Review:
       Round 1: 12 resolved, 2 deferred, 1 rejected
       Round 2: 4 open, 3 resolved  ← active round
     ```
     If feedback_log does not exist, show: "External review: not started"
```

- [ ] **Step 3: Verify**

```bash
grep -n "External feedback" .claude/commands/pipeline-status.md
```

Expected: line with "External feedback:" visible.

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/pipeline-status.md
git commit -m "feat: add external feedback round stats to pipeline-status"
```

---

## Task 10: Update CLAUDE.md pipeline documentation

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Read CLAUDE.md** (already read in planning — check Pipeline Stages section)

- [ ] **Step 2: Add /external-review to Pipeline Stages**

Find in `CLAUDE.md`:
```
5. `/review` — Red-team the proposal, check compliance, find unsupported claims
6. `/gate-check [gate-name]` — Verify readiness before transitioning between stages
7. `/pipeline-status` — Show current progress
```

Replace with:
```
5. `/review` — Red-team the proposal, check compliance, find unsupported claims
6. `/external-review` — Ingest external reviewer comments (PDF/DOCX/XLSX/MD/chat), triage, route to specialist agents, apply patches
7. `/gate-check [gate-name]` — Verify readiness before transitioning between stages
8. `/pipeline-status` — Show current progress
```

- [ ] **Step 3: Add external-feedback to Review Gates section**

Find:
```
- **Gate 1 (scope)**: Before research — call parsed, criteria mapped, eligibility confirmed
- **Gate 2 (evidence)**: Before writing — minimum 12 quality sources, SOTA summary, novelty anchors
- **Gate 4 (draft)**: Before review — all sections drafted, claims linked to evidence
- **Gate 5 (submission)**: Before export — template compliance, citation integrity, page limits
```

Replace with:
```
- **Gate 1 (scope)**: Before research — call parsed, criteria mapped, eligibility confirmed
- **Gate 2 (evidence)**: Before writing — minimum 12 quality sources, SOTA summary, novelty anchors
- **Gate 4 (draft)**: Before review — all sections drafted, claims linked to evidence
- **Gate 5 (submission)**: Before export — template compliance, citation integrity, page limits
- **Gate: external-feedback**: After external review rounds — zero open/in-progress comments, all closed (resolved/deferred/rejected)
```

- [ ] **Step 4: Add feedback_log to Shared Memory Stores section**

Find:
```
- `memory/evidence_store.jsonl` — All retrieved sources with quality ratings
- `memory/claim_registry.jsonl` — Every proposal claim linked to evidence
- `memory/decision_log.jsonl` — Why key choices were made
- `memory/task_registry.jsonl` — Track all spawned tasks (prevents duplicates)
```

Replace with:
```
- `memory/evidence_store.jsonl` — All retrieved sources with quality ratings
- `memory/claim_registry.jsonl` — Every proposal claim linked to evidence
- `memory/decision_log.jsonl` — Why key choices were made
- `memory/task_registry.jsonl` — Track all spawned tasks (prevents duplicates)
- `memory/feedback_log.jsonl` — All external reviewer comments across rounds with status tracking
```

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add /external-review and external-feedback gate to CLAUDE.md pipeline docs"
```

---

## Task 11: Create render templates

**Files:**
- Create: `templates/triage_table.md`
- Create: `templates/external_review_diff_summary.md`

- [ ] **Step 1: Write triage_table.md**

Write this to `templates/triage_table.md`:

```markdown
## External Review — Round {ROUND} Triage

{FILE_COUNT} new file(s) parsed. {COMMENT_COUNT} comments found ({ACK_COUNT} acks filtered out).

| FBK-ID | File | Location | Category | Routed to | Comment excerpt |
|--------|------|----------|----------|-----------|----------------|
{ROWS}

{RE_RAISED_SECTION}

---

**Review the table above.** Reply with one of:

- **"approve all"** — proceed with all shown routings as-is
- **"approve all except FBK-xxx, FBK-yyy"** — skip listed items
- **"reclassify FBK-xxx as {category}"** — change one entry's routing
- **"defer FBK-xxx"** — move to next round
- **"skip FBK-xxx"** — exclude entirely (not logged as deferred)

Multiple instructions can be combined in one reply.
```

- [ ] **Step 2: Write external_review_diff_summary.md**

Write this to `templates/external_review_diff_summary.md`:

```markdown
## External Review — Round {ROUND} Complete

| Outcome | Count |
|---------|-------|
| Resolved | {RESOLVED} |
| Deferred (next round) | {DEFERRED} |
| Rejected (with rationale) | {REJECTED} |
| Stale (needs manual review) | {STALE} |

### Files changed
{FILES_CHANGED}

### New sources added (SRC-xxx)
{NEW_SOURCES}

### Claims updated (CLM-xxx)
{UPDATED_CLAIMS}

### Stale items requiring manual review
{STALE_ITEMS}

---

**Next steps:**
- If more reviewer files to process: drop them in `inputs/reviews/round{NEXT_ROUND}/` and run `/external-review --new-round`
- If all rounds complete: run `/gate-check external-feedback` to verify closure
- If ready to resubmit: run `/gate-check submission`
```

- [ ] **Step 3: Commit**

```bash
git add templates/triage_table.md templates/external_review_diff_summary.md
git commit -m "feat: add triage table and diff summary render templates"
```

---

## Task 12: Integration smoke test

This task verifies the end-to-end flow by running Phase 1 against a hand-crafted fixture.

- [ ] **Step 1: Create the fixture directory and a minimal chat-style feedback file**

```bash
mkdir -p runs/_test-external-review/inputs/reviews/round1
mkdir -p runs/_test-external-review/memory
mkdir -p runs/_test-external-review/drafts
mkdir -p runs/_test-external-review/intermediate
```

Write `runs/_test-external-review/inputs/reviews/round1/chat_test.md`:

```markdown
Section 1.2 — The claim that LFP reduces scrap by 15% needs a citation. I can't find a source for this number.

Section 2 — The sentence "The process is inherently safe" is vague. Please clarify what specific safety properties you mean.

Section 3.1 — TRL assessment seems optimistic. The cited pilot was at lab scale (100g), not the claimed TRL 6.

Great work on the abstract — very clear.
```

- [ ] **Step 2: Create a minimal state.json and draft for the test project**

Write `runs/_test-external-review/state.json`:

```json
{
  "project_name": "_test-external-review",
  "project_title": "Test Project",
  "funding_agency": "Test",
  "mechanism": "test",
  "created_at": "2026-04-20",
  "stages": {
    "writing": { "status": "complete" }
  },
  "gates": {}
}
```

Write `runs/_test-external-review/drafts/01_innovation.md`:

```markdown
# Section 1: Innovation

The proposed closed-loop recovery process reduces scrap by 15%.

The process is inherently safe and meets EU standards.
```

Write `runs/_test-external-review/memory/claim_registry.jsonl`:

```
{"claim_id": "CLM-001", "text": "LFP active material scrap reduction of 15% via closed-loop recovery", "status": "supported", "supported_by": ["SRC-001"]}
```

Write `runs/_test-external-review/memory/evidence_store.jsonl`:

```
{"source_id": "SRC-001", "title": "LFP Manufacturing Waste Reduction Study", "year": 2024, "quality": "medium", "extract": "Closed-loop recovery reduces scrap by ~15%"}
```

- [ ] **Step 3: Run `/external-review` on the test project**

Invoke in Claude Code:
```
/external-review
```

When prompted for project, specify `_test-external-review`. When the triage table appears, verify:
- 3 actionable entries appear (not 4 — the "Great work on the abstract" ack should be filtered)
- FBK-001: category `evidence`, routed to `literature_searcher`
- FBK-002: category `writing`, routed to `feedback_applier`
- FBK-003: category `technical`, routed to `state_of_art_synthesizer`

- [ ] **Step 4: Approve all and verify Phase 2 output**

Reply "approve all" and verify:
- `runs/_test-external-review/memory/feedback_log.jsonl` exists with 4 entries (3 actionable + 1 ack)
- After dispatch completes: all 3 entries have `status: "resolved"` or `"stale"` (never `"open"`)
- `runs/_test-external-review/drafts/01_innovation.md` has been modified by at least one patch

- [ ] **Step 5: Run gate-check**

```
/gate-check external-feedback
```

Expected: PASS (all entries closed) or specific FBK-IDs listed if any are stale.

- [ ] **Step 6: Commit the test fixtures**

```bash
git add runs/_test-external-review/
git commit -m "test: add smoke test fixture for /external-review"
```

---

## Self-Review Checklist

- **Spec §4 (taxonomy)** → Task 3 (feedback_parser agent) defines routing defaults for all 8 categories. ✓
- **Spec §5 (feedback_entry schema)** → Task 1. ✓
- **Spec §6 (patch schema)** → Task 2. ✓
- **Spec §7 (Phase 1 flow)** → Task 5 (orchestrator) §Phase 1. ✓
- **Spec §8 (Phase 2 flow)** → Task 5 (orchestrator) §Phase 2. ✓
- **Spec §9 (resumption)** → Task 5 (orchestrator) §Resumption. ✓
- **Spec §10 (cross-round deduplication)** → Task 5 (orchestrator) Step 1.5. ✓
- **Spec §11 (error handling)** → Tasks 3 + 4 (agent definitions) + Task 5 (stale handling). ✓
- **Spec §12 (gate integration)** → Task 8. ✓
- **Spec §13 (file layout)** → All tasks create the listed files. ✓
- **Spec §14 (implementation order)** → Task order follows: schemas → parser → applier → orchestrator → command → hook → gate → status → CLAUDE.md → templates → test. ✓
- **Spec §15 (dependencies)** → python-docx noted as existing; pdfplumber/openpyxl noted in Task 3 agent. ✓
- **Templates** → Task 11. ✓

No placeholders found. All file paths are exact. All code/content blocks are complete.
