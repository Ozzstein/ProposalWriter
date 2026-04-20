# External Review Integration — Design Spec

**Date**: 2026-04-20
**Feature**: `/external-review` slash command
**Status**: Approved, ready for implementation

---

## 1. Problem

The pipeline has no structured way to ingest external reviewer feedback. When a human reviewer sends comments (PDF, DOCX tracked changes, XLSX, MD, or chat-pasted text), there is no clear entry point, no routing to the right agent, no deduplication across rounds, and no persistent log. Users are forced to manually apply edits — often with a single agent handling everything, bypassing the evidence-grounded, specialist-routed architecture.

---

## 2. Solution Overview

A new `/external-review` slash command backed by `external_review_orchestrator` (opus). It runs in two phases within one invocation, with a mandatory user-approval gate between them:

- **Phase 1 — Ingest**: parse all new reviewer files for a round, classify each comment, present a triage table.
- **Phase 2 — Dispatch**: after user approval, route each comment to the specialist agent best suited to handle it, apply validated patches to drafts, update memory stores.

A persistent `feedback_log.jsonl` tracks all comments across rounds so reviewers can't re-raise already-addressed issues without detection.

---

## 3. Architecture

### New agents

| Agent | Type | Model | Purpose |
|---|---|---|---|
| `external_review_orchestrator` | Orchestrator | opus | Own the two-phase flow, conflict checking, patch application |
| `feedback_parser` | Retriever | sonnet | Extract + classify comments from one input file |
| `feedback_applier` | Writer | sonnet | Produce old/new patches for writing/style/structural comments |

### Reused agents (no changes)
`literature_searcher`, `patent_scanner`, `state_of_art_synthesizer`, `gap_analyzer`, `impact_writer`, `implementation_writer`, `excellence_writer`, `compliance_checker`, `scientific_reviewer`

### New memory store
`runs/{project}/memory/feedback_log.jsonl`

### New schemas
`schemas/feedback_entry.json`, `schemas/feedback_patch.json`

---

## 4. Comment Taxonomy

Every extracted comment is classified into exactly one category, which determines the target agent:

| Category | Target agent | Examples |
|---|---|---|
| `evidence` | `literature_searcher` / `patent_scanner` | missing citation, outdated data, wrong number |
| `technical` | `state_of_art_synthesizer` / `gap_analyzer` | wrong claim, methodology flaw, TRL misjudged |
| `structural` | orchestrator | section missing, wrong order, off-topic content |
| `writing` | `feedback_applier` | unclear sentence, jargon, flow |
| `compliance` | `compliance_checker` | exceeds page limit, missing required field |
| `style` | `feedback_applier` (light pass) | typos, punctuation, citation format |

---

## 5. Feedback Entry Schema

`runs/{project}/memory/feedback_log.jsonl` — one JSON object per line:

```json
{
  "feedback_id": "FBK-001",
  "round": 1,
  "reviewer": "Dr. Smith (external)",
  "source_file": "inputs/reviews/round1/smith.docx",
  "location": "Section 1.2, para 3",
  "original_text": "...",
  "comment": "this claim needs a citation",
  "category": "evidence",
  "routed_to": "literature_searcher",
  "status": "open",
  "resolution": null,
  "resolved_at": null,
  "round_closed": null,
  "dedupe_key": "fbk_smith_sec1.2_p3_citation",
  "comment_type": "inline_comment | tracked_change | chat | annotation"
}
```

**Status state machine**: `open` → `in_progress` → `resolved` | `deferred` | `rejected`

---

## 6. Patch Schema

`feedback_applier` output, validated before any Edit tool call:

```json
{
  "patch_id": "PATCH-001",
  "feedback_id": "FBK-001",
  "target_file": "drafts/01_innovation.md",
  "old_text": "exact string from current draft",
  "new_text": "revised string",
  "rationale": "one sentence",
  "new_claim_ids": [],
  "new_source_ids": ["SRC-045"]
}
```

---

## 7. Phase 1 — Ingest Flow

```
/external-review [--round N | --new-round]
  │
  ├── 1. Resolve round folder
  │       If --new-round or no active round: create inputs/reviews/round{N+1}/
  │       If ambiguous: ask user "new round or add to round {N}?"
  │
  ├── 2. Capture chat-pasted content
  │       Any text pasted by user → written to round{N}/chat_{timestamp}.md
  │
  ├── 3. Diff vs already-parsed source_files in feedback_log.jsonl
  │       → new_files[] = unprocessed files in round{N}/
  │
  ├── 4. Spawn feedback_parser per file IN PARALLEL
  │       Input: {file_path, round, claim_registry_path, taxonomy}
  │       Output: array of feedback_entry objects
  │
  ├── 5. Append all entries to feedback_log.jsonl (status=open)
  │       Filter: pure acks → status=ack (logged but not shown in triage)
  │
  └── 6. Render triage table → present to user
        FBK-ID | Round | File | Location | Category | Routed to | Comment excerpt
        Wait for: approve / reclassify / skip / defer
```

### DOCX tracked changes
Parser reads both accepted and proposed text. Each tracked change becomes a separate entry with `comment_type: "tracked_change"`.

### Input file conventions
- Files dropped into `runs/{project}/inputs/reviews/round{N}/` (any filename)
- File path referenced in chat → orchestrator copies to round folder before parsing
- Chat-pasted text → orchestrator writes to `round{N}/chat_{timestamp}.md`

---

## 8. Phase 2 — Dispatch Flow

Runs only after user approves triage. Triggered by user confirming triage table.

```
For each approved entry:
  │
  ├── CONFLICT CHECK
  │     Does comment contradict a claim in claim_registry with supported_by?
  │     If yes → show user:
  │       - The reviewer comment
  │       - The existing claim + source IDs
  │       → Options:
  │           [A] Update claim (defer to reviewer)
  │           [B] Reject with rationale (push back with evidence)
  │           [C] Spawn literature_searcher to find more evidence first
  │
  ├── GROUP by target_section
  │     (one agent pass per section, not per comment — avoids conflicting patches)
  │
  ├── Spawn target agents IN PARALLEL per independent group:
  │     evidence → literature_searcher / patent_scanner → new SRC-xxx
  │     technical → state_of_art_synthesizer → new/revised CLM-xxx
  │     writing/style → feedback_applier → patch
  │     structural → orchestrator decides (may spawn writer or flag for user)
  │     compliance → compliance_checker → patch or flag
  │
  ├── PATCH VALIDATION
  │     old_text must match current draft exactly
  │     If stale: re-read draft region, re-spawn feedback_applier once
  │     If still fails: escalate to user with both versions
  │
  ├── Apply patches via Edit tool (serialized for overlapping regions)
  │
  ├── Update feedback_log entries: status=resolved, resolution, resolved_at
  │
  ├── Update claim_registry / evidence_store as needed
  │
  └── Present diff summary:
        X resolved, Y deferred, Z rejected
        Files changed: [list]
        New SRC-xxx: [list]
        New/revised CLM-xxx: [list]
```

---

## 9. Resumption

If `/external-review` is interrupted mid-dispatch, re-invoke with `--resume`:
- Skips Phase 1 (no re-parsing)
- Picks up all entries with `status: "open"` or `"in_progress"` in the active round

---

## 10. Cross-Round Deduplication

On Phase 1 ingest, `feedback_parser` computes a `dedupe_key` for each comment (reviewer + location + topic hash). Before appending to `feedback_log.jsonl`, orchestrator checks for an existing entry with:
- Same `dedupe_key`
- `status: "rejected"`

If found, parser flags to user: *"This comment was raised in round {N} and rejected with rationale: [resolution]. Reopen?"*

---

## 11. Error Handling

| Scenario | Handling |
|---|---|
| File unreadable (corrupt, locked) | Emit entry with `category: "parse_error"`, user resolves manually |
| Ambiguous category | Emit `category: "ambiguous"`, `candidates: [...]`, user picks during triage |
| Comment location not found in draft | Emit `status: "unlocatable"`, flag for user |
| Patch old_text stale | One retry with fresh draft; if still fails, escalate to user |
| Overlapping patches same section | Serialize application (apply one, re-read, apply next) |
| PDF annotations | Use `pdfplumber`; fallback: parser reads body text only |
| Positive-only comments | Logged as `status: "ack"`, not shown in triage unless `--keep-positive` |

---

## 12. Gate Integration

New gate: `external-feedback`

`/gate-check external-feedback` passes when:
- Active round has zero entries with `status: "open"` or `"in_progress"`
- All comments either `resolved`, `deferred`, or `rejected` with rationale

`/pipeline-status` gains a new row showing: active round, open/resolved/deferred counts.

---

## 13. File Layout

### New files
```
.claude/commands/external-review.md
agents/orchestrators/external_review_orchestrator.md
agents/workers/retrievers/feedback_parser.md
agents/workers/writers/feedback_applier.md
schemas/feedback_entry.json
schemas/feedback_patch.json
templates/triage_table.md
templates/external_review_diff_summary.md
docs/superpowers/specs/2026-04-20-external-review-design.md
```

### Modified files
```
CLAUDE.md                          — add /external-review to pipeline docs
hooks/validate_output.py           — add feedback_*.json schema patterns
.claude/commands/gate-check.md     — add "external-feedback" gate
.claude/commands/pipeline-status.md — show external-review round status
```

### Per-run (created lazily)
```
runs/{project}/memory/feedback_log.jsonl
runs/{project}/inputs/reviews/round{N}/
```

---

## 14. Implementation Order

1. `schemas/feedback_entry.json` + `schemas/feedback_patch.json`
2. Test fixtures: `tests/fixtures/external-review/round1/` (DOCX, PDF, MD, chat)
3. `agents/workers/retrievers/feedback_parser.md`
4. `agents/workers/writers/feedback_applier.md`
5. `agents/orchestrators/external_review_orchestrator.md`
6. `.claude/commands/external-review.md`
7. `hooks/validate_output.py` — extend for feedback schemas
8. `gate-check.md` + `pipeline-status.md` — add external-feedback gate
9. `CLAUDE.md` — document new stage
10. `templates/triage_table.md` + `templates/external_review_diff_summary.md`
11. Golden fixtures + test run directory
12. Real-run validation on example-lfp-project

---

## 15. Dependencies

| Dependency | Used for | Status |
|---|---|---|
| `python-docx` | DOCX + tracked changes | Already present (populate_templates.py) |
| `pdfplumber` or `pypdf` | PDF annotation extraction | Check existing deps; add if missing |
| `openpyxl` | XLSX comment extraction | Likely already present |
