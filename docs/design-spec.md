# Multi-Agent Scientific Proposal Writing System — Design Spec & Implementation Plan

## Context

Build a hierarchical, evidence-grounded grant proposal writing system in Claude Code. The system uses a small number of orchestrator agents with bounded worker spawning, strict schemas, shared evidence memory, and review gates between pipeline stages.

**Target**: NIH/NSF (and EU-style) grant proposals — R01, R21, Innovation Fund, etc.
**Platform**: Claude Code CLI/App (no external application code)
**Supporting code**: ~350 lines Python (hooks + 1 MCP server)

---

## 1. Architecture Overview

```
User / Research Lead
        |
        v
[CLAUDE.md — Program Director / Supervisor]
        |
        +--> /parse-call       [A. Call & Scope Orchestrator]
        |
        +--> /research         [B. Research & Evidence Orchestrator]
        |
        +--> /technical-design [C. Technical Design Orchestrator]
        |
        +--> /write-proposal   [D. Proposal Writing Orchestrator]
        |
        +--> /review           [E. Review & Compliance Orchestrator]
```

**Mapping to Claude Code:**
- Program Director = CLAUDE.md (the session itself)
- Orchestrators = Slash commands in `.claude/commands/`
- Workers = Agent tool subagents (spawned by orchestrators)
- Shared memory = JSONL files in `runs/{project}/memory/`
- Review gates = `/gate-check` slash command
- Harness logic = Hooks in `.claude/settings.json`

---

## 2. Agent Taxonomy

### Three worker classes

**Retrievers** — gather material, not conclusions
- `literature_searcher`, `patent_scanner`, `call_parser`, `regulation_scanner`, `internal_docs_retriever`

**Synthesizers** — compare, rank, infer, structure
- `novelty_mapper`, `gap_analyzer`, `state_of_art_synthesizer`, `risk_synthesizer`, `wp_designer`

**Writers** — turn validated material into polished text
- `impact_writer`, `excellence_writer`, `implementation_writer`, `abstract_writer`, `wp_writer`

This separation reduces hallucination: writers don't invent evidence.

### v1 Roster (build this first)

| Agent | Type | Model | Implementation |
|---|---|---|---|
| `program_director` | Supervisor | opus | CLAUDE.md |
| `call_scope_orchestrator` | Orchestrator | opus | `/parse-call` command |
| `research_orchestrator` | Orchestrator | opus | `/research` command |
| `proposal_writer_orchestrator` | Orchestrator | opus | `/write-proposal` command |
| `review_orchestrator` | Orchestrator | opus | `/review` command |
| `literature_searcher` | Retriever | haiku | Agent subagent |
| `call_parser` | Retriever | sonnet | Agent subagent |
| `technical_synthesizer` | Synthesizer | opus | Agent subagent |
| `impact_writer` | Writer | sonnet | Agent subagent |
| `implementation_writer` | Writer | sonnet | Agent subagent |
| `scientific_reviewer` | Reviewer | opus | Agent subagent |
| `compliance_checker` | Reviewer | haiku | Agent subagent |

### v2 Additions (after v1 works)

- `technical_design_orchestrator` + `/technical-design` command
- `patent_scanner`, `regulation_scanner`, `competitor_mapper`
- Domain specialists: `materials_specialist`, `manufacturing_specialist`, etc.
- `evaluator_simulator`, `consistency_checker`, `citation_checker`, `style_editor`
- `visual_table_builder`, `executive_summary_writer`

---

## 3. Pipeline Stages & Review Gates

### Pipeline flow

```
1. /start-proposal      — Intake, create project
2. /parse-call           — Parse funding call, extract criteria
   --- Gate 1: Scope approved ---
3. /research             — Gather evidence, identify SOTA + gaps
   --- Gate 2: Evidence sufficient ---
4. /technical-design     — Objectives, methods, WPs, risks, KPIs  [v2]
   --- Gate 3: Technical design coherent ---
5. /write-proposal       — Draft narrative sections
   --- Gate 4: Draft complete ---
6. /review               — Red-team, compliance check, revision plan
   --- Gate 5: Submission readiness ---
7. Export final package
```

### Gate definitions

**Gate 1 — Scope approved** (before research begins):
- [ ] Target call identified
- [ ] Template/structure identified
- [ ] Scoring criteria mapped
- [ ] Major assumptions listed
- [ ] Eligibility confirmed

**Gate 2 — Evidence sufficient** (before technical design/writing):
- [ ] Minimum 12 quality sources in evidence store
- [ ] SOTA summary written
- [ ] Novelty anchors identified (>=2)
- [ ] Unsupported assumptions explicitly marked
- [ ] Key gaps documented

**Gate 3 — Technical design coherent** (before drafting) [v2]:
- [ ] Objectives align with call criteria
- [ ] WPs/tasks/milestones consistent
- [ ] Risk register populated
- [ ] KPI framework defined
- [ ] Impact logic documented

**Gate 4 — Draft complete** (before review):
- [ ] Every required section drafted
- [ ] Every major claim linked to evidence or explicit assumption
- [ ] Terminology consistent across sections
- [ ] All claim_ids in drafts exist in claim_registry

**Gate 5 — Submission readiness** (before export):
- [ ] Template compliance verified
- [ ] Citation integrity (all refs exist)
- [ ] Page/word limits met
- [ ] No contradictory numbers across sections
- [ ] Abstract matches content

---

## 4. Shared Memory Stores

All stored in `runs/{project}/memory/` as JSONL files.

### A. Evidence Store (`evidence_store.jsonl`)
```json
{
  "source_id": "SRC-018",
  "title": "...",
  "type": "paper|patent|standard|internal",
  "year": 2024,
  "quality": "low|medium|high",
  "key_points": ["..."],
  "limitations": ["..."],
  "relevance_tags": ["..."],
  "retrieved_by": "literature_searcher",
  "task_id": "TASK-042"
}
```

### B. Claim Registry (`claim_registry.jsonl`)
```json
{
  "claim_id": "CLM-101",
  "text": "The proposed process reduces scrap through closed-loop recovery.",
  "type": "technical_benefit|scientific_finding|impact_statement",
  "supported_by": ["SRC-018", "SRC-022"],
  "owner_agent": "technical_synthesizer",
  "status": "supported|assumption|unsupported",
  "created_at": "2026-03-31"
}
```

### C. Decision Log (`decision_log.jsonl`)
```json
{
  "decision_id": "DEC-011",
  "question": "Why select LFP chemistry?",
  "decision": "Use LFP-only production scope",
  "rationale": ["policy alignment", "safety", "manufacturing readiness"],
  "evidence_refs": ["SRC-002", "SRC-007"],
  "date": "2026-03-31"
}
```

### D. Task Registry (`task_registry.jsonl`)
```json
{
  "task_id": "TASK-042",
  "title": "Search recent LFP fast-charge evidence",
  "owner": "research_orchestrator",
  "status": "running|complete|failed",
  "spawned_by": "program_director",
  "dedupe_key": "lfp_fast_charge_recent_evidence",
  "depth": 1,
  "started_at": "2026-03-31T10:00:00Z"
}
```

---

## 5. Structured I/O Schemas

All in `schemas/` directory. Agents are instructed to read the schema before producing output.

### Key schemas to build

- `schemas/task.json` — Standard task input for every agent
- `schemas/evidence_result.json` — Retriever output
- `schemas/claim.json` — Claim registry entry
- `schemas/section_draft.json` — Writer output
- `schemas/review_report.json` — Reviewer output
- `schemas/decision.json` — Decision log entry
- `schemas/gate_check.json` — Gate check result

### Agent prompt template (compact)

```markdown
You are the {agent_name}.

Mission: {one sentence}

You are responsible for:
- ...

You are NOT responsible for:
- ...

Inputs: {listed artifacts to read}

Rules:
- Cite evidence for technical claims
- Distinguish facts from assumptions
- Do not duplicate tasks in the registry
- Return only the required output schema (read schemas/{schema_name}.json)

Completion criteria:
- ...

Escalate if:
- ...
```

---

## 6. Bounded Delegation Rules

Enforced via hooks + prompt instructions:

1. Maximum depth: **2 levels** (orchestrator -> worker -> subworker max)
2. Orchestrator can spawn workers
3. Worker can spawn a subworker **only with justification**
4. No subworker can spawn again
5. Every spawn must register a `dedupe_key` in task registry
6. Every spawn must specify why parent cannot do it directly
7. Every child must return structured output, not raw chatter

**Good reasons to spawn:** parallel search by topic, separate regulatory/patent scans, extracting tables from PDFs, drafting multiple sections in parallel

**Bad reasons:** "think harder", "just in case", rewriting trivial content

---

## 7. Hooks Design

Configured in `.claude/settings.json`. Each hook is a Python script in `hooks/`.

### `hooks/check_dedupe.py` (~50 lines)
- **Trigger**: PreToolUse on Agent tool
- **Logic**: Read `task_registry.jsonl`, check if `dedupe_key` already exists with status "running" or "complete". Block if duplicate.
- **Output**: Error message if blocked, empty if OK

### `hooks/check_depth.py` (~30 lines)
- **Trigger**: PreToolUse on Agent tool
- **Logic**: Count depth from task registry parent chain. Block if > 2.

### `hooks/validate_output.py` (~80 lines)
- **Trigger**: PostToolUse on Write tool (when writing to `runs/`)
- **Logic**: If file matches a known schema pattern (e.g., `*_results.json`), validate against corresponding schema in `schemas/`.
- **Output**: Warning if validation fails

### `hooks/check_citations.py` (~40 lines)
- **Trigger**: PostToolUse on Write tool (when writing drafts)
- **Logic**: Extract claim_ids from draft, verify each exists in `claim_registry.jsonl`.
- **Output**: List of unregistered claim IDs if any

### `.claude/settings.json` structure
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Agent",
        "command": "python hooks/check_dedupe.py"
      },
      {
        "matcher": "Agent",
        "command": "python hooks/check_depth.py"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "command": "python hooks/validate_output.py"
      },
      {
        "matcher": "Write",
        "command": "python hooks/check_citations.py"
      }
    ]
  },
  "mcpServers": {
    "academic-search": {
      "command": "python",
      "args": ["mcp-servers/academic-search/server.py"]
    }
  }
}
```

---

## 8. MCP Server: Academic Search

**File**: `mcp-servers/academic-search/server.py` (~150 lines)
**Framework**: FastMCP

### Tools provided:
- `search_pubmed(query, max_results, date_from, date_to)` — Search PubMed via E-utilities API
- `fetch_abstract(pmid)` — Get full abstract for a PubMed ID
- `fetch_mesh_terms(pmid)` — Get MeSH terms for a paper
- `search_patents(query, max_results)` — Search Google Patents (v2, via web scraping or API)

Note: Semantic Scholar is already available via the connected MCP tool.

---

## 9. Folder Structure

```
proposal-agent-system/
├── CLAUDE.md                              # Program Director system prompt
├── .claude/
│   ├── settings.json                      # Hooks + MCP server config
│   └── commands/
│       ├── start-proposal.md              # /start-proposal
│       ├── parse-call.md                  # /parse-call (Orchestrator A)
│       ├── research.md                    # /research (Orchestrator B)
│       ├── write-proposal.md              # /write-proposal (Orchestrator D)
│       ├── review.md                      # /review (Orchestrator E)
│       ├── gate-check.md                  # /gate-check [gate-name]
│       └── pipeline-status.md             # /pipeline-status
├── agents/
│   ├── orchestrators/
│   │   ├── call_scope_orchestrator.md
│   │   ├── research_orchestrator.md
│   │   ├── proposal_writer_orchestrator.md
│   │   └── review_orchestrator.md
│   └── workers/
│       ├── retrievers/
│       │   ├── literature_searcher.md
│       │   ├── patent_scanner.md
│       │   └── call_parser.md
│       ├── synthesizers/
│       │   ├── novelty_mapper.md
│       │   ├── gap_analyzer.md
│       │   └── state_of_art_synthesizer.md
│       └── writers/
│           ├── impact_writer.md
│           ├── implementation_writer.md
│           └── abstract_writer.md
├── schemas/
│   ├── task.json
│   ├── evidence_result.json
│   ├── claim.json
│   ├── decision.json
│   ├── review_report.json
│   ├── section_draft.json
│   └── gate_check.json
├── hooks/
│   ├── check_dedupe.py
│   ├── validate_output.py
│   ├── check_depth.py
│   └── check_citations.py
├── mcp-servers/
│   └── academic-search/
│       ├── pyproject.toml
│       └── server.py
├── templates/
│   ├── call_brief.md
│   ├── wp_template.md
│   ├── proposal_outline_nih_r01.md
│   ├── proposal_outline_nsf.md
│   └── reviewer_checklist.md
├── runs/
│   └── {project-name}/
│       ├── state.json
│       ├── context.md
│       ├── memory/
│       │   ├── evidence_store.jsonl
│       │   ├── claim_registry.jsonl
│       │   ├── decision_log.jsonl
│       │   └── task_registry.jsonl
│       ├── inputs/
│       ├── intermediate/
│       ├── drafts/
│       ├── reviews/
│       └── final/
└── docs/
    └── design-spec.md
```

---

## 10. Implementation Plan

### Phase 1: Foundation (build order)

1. **Initialize project** — Create folder structure, `pyproject.toml`, git init
2. **CLAUDE.md** — Write Program Director system prompt with pipeline overview, conventions, delegation rules
3. **Schemas** — Define all JSON schemas (`task.json`, `evidence_result.json`, `claim.json`, `section_draft.json`, `review_report.json`, `gate_check.json`, `decision.json`)
4. **Agent prompt files** — Write v1 agent definitions in `agents/` (v1 roster only: 7 worker agents)
5. **Templates** — Create proposal outline templates for NIH R01

### Phase 2: Slash Commands

6. **`/start-proposal`** — Initialize a run directory, gather user context, create state.json
7. **`/parse-call`** — Call & Scope Orchestrator: parse call document, spawn call_parser subagent, produce call_brief.json + evaluation_matrix.json
8. **`/gate-check`** — Read state.json + relevant files, check gate criteria, report pass/fail
9. **`/research`** — Research Orchestrator: spawn literature_searcher + patent_scanner in parallel, then state_of_art_synthesizer, write to memory stores
10. **`/write-proposal`** — Writing Orchestrator: read all intermediate outputs, spawn section writers, produce drafts
11. **`/review`** — Review Orchestrator: spawn scientific_reviewer + compliance_checker, produce review_report + revision_plan
12. **`/pipeline-status`** — Read state.json, display progress

### Phase 3: Supporting Code

13. **Hooks** — `check_dedupe.py`, `check_depth.py`, `validate_output.py`, `check_citations.py`
14. **`.claude/settings.json`** — Register hooks + MCP server
15. **MCP server** — `academic-search/server.py` with PubMed search tools

### Phase 4: Integration & Testing

16. **End-to-end test** — Run full pipeline with a sample NIH R01 topic
17. **Iterate on prompts** — Refine agent definitions based on output quality
18. **Gate testing** — Verify each gate correctly blocks when prerequisites aren't met
19. **Hook testing** — Verify deduplication, depth limits, schema validation work

### Verification

- Run `/start-proposal` with a sample topic -> verify directory structure created
- Run `/parse-call` with a sample NIH R01 call -> verify call_brief.json output
- Run `/gate-check scope` -> verify it correctly reports pass/fail
- Run `/research` -> verify parallel subagents produce evidence_store entries
- Run `/write-proposal` -> verify section drafts reference claim_ids
- Run `/review` -> verify review report identifies issues
- Check hooks fire correctly on Agent spawn and file writes
- Check MCP server returns PubMed results

---

## 11. Key Design Decisions

1. **Claude Code IS the harness** — No TypeScript/Python orchestration layer needed. CLAUDE.md + slash commands + hooks + Agent tool provide all orchestration.
2. **File-based state over database** — JSONL files are simple, debuggable, and Claude Code can read/write them natively.
3. **Schemas as contracts** — JSON schemas in `schemas/` are read by agents and validated by hooks. Not 100% programmatic enforcement, but very reliable with good prompts + validation hooks.
4. **Bounded delegation via hooks** — `check_depth.py` and `check_dedupe.py` enforce the 2-level max depth and prevent duplicate spawns at the harness level, not just via prompt instructions.
5. **Evidence-first writing** — Writers read from evidence store and claim registry. They don't search or invent evidence. This is the key architectural decision that reduces hallucination.
6. **User in the loop** — The supervisor (CLAUDE.md) presents results after each stage and gets user approval before gate transitions. Not a fully autonomous pipeline.

---

## 12. Critical Files to Create

| File | Purpose | Priority |
|---|---|---|
| `CLAUDE.md` | Program Director — the brain of the system | P0 |
| `.claude/commands/start-proposal.md` | Initialize runs | P0 |
| `.claude/commands/research.md` | Research orchestrator | P0 |
| `.claude/commands/write-proposal.md` | Writing orchestrator | P0 |
| `.claude/commands/review.md` | Review orchestrator | P0 |
| `.claude/commands/gate-check.md` | Gate checking | P0 |
| `schemas/evidence_result.json` | Evidence schema | P0 |
| `schemas/claim.json` | Claim schema | P0 |
| `schemas/section_draft.json` | Draft schema | P0 |
| `schemas/review_report.json` | Review schema | P0 |
| `agents/workers/retrievers/literature_searcher.md` | Lit search agent | P0 |
| `agents/workers/synthesizers/state_of_art_synthesizer.md` | SOTA synthesis | P0 |
| `agents/workers/writers/impact_writer.md` | Impact section | P0 |
| `hooks/check_dedupe.py` | Deduplication | P1 |
| `hooks/check_depth.py` | Depth limit | P1 |
| `hooks/validate_output.py` | Schema validation | P1 |
| `mcp-servers/academic-search/server.py` | PubMed tools | P1 |
| `.claude/settings.json` | Hook + MCP config | P1 |
