# ProposalWriter

A multi-agent system for writing competitive grant proposals, built on [Claude Code](https://docs.anthropic.com/en/docs/claude-code). ProposalWriter coordinates 17 specialised AI agents in a structured pipeline — from parsing funding calls through evidence gathering, drafting, and adversarial review — producing evidence-grounded proposals aligned to evaluator scoring rubrics.

**Supported funding instruments**: EU Innovation Fund (large-scale), Horizon Europe (RIA/IA), NIH R01, NSF standard proposals.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Pipeline Stages](#pipeline-stages)
- [Slash Commands](#slash-commands)
- [Agent Architecture](#agent-architecture)
- [Review Gates](#review-gates)
- [Schemas and Data Contracts](#schemas-and-data-contracts)
- [Project File Structure](#project-file-structure)
- [Hooks](#hooks)
- [MCP Server](#mcp-server)
- [Templates](#templates)
- [Configuration](#configuration)
- [Example Walkthrough](#example-walkthrough)

---

## How It Works

ProposalWriter implements a **Program Director** pattern: you (the user) interact with a top-level orchestrator that delegates work to specialised agents in a strict hierarchy.

```
You (researcher)
 |
 v
Program Director (Claude Code session)
 |
 |-- /parse-call -----> Call Scope Orchestrator
 |                        |-- call_parser (haiku)
 |                        |-- eligibility_parser (haiku)
 |
 |-- /research -------> Research Orchestrator
 |                        |-- Phase 1: literature_searcher + web_scraper + patent_scanner
 |                        |-- Phase 2: state_of_art_synthesizer (opus)
 |                        |-- Phase 3: novelty_mapper + gap_analyzer (opus)
 |
 |-- /write-proposal -> Writing Orchestrator
 |                        |-- Phase 1: excellence_writer + impact_writer + implementation_writer
 |                        |-- Phase 2: abstract_writer (last)
 |
 |-- /review ---------> Review Orchestrator
                          |-- scientific_reviewer (opus)
                          |-- compliance_checker (haiku)
                          |-- adversarial_evaluator_simulator (opus)
```

**Key design principles:**
- **Evidence-first**: Writers never invent facts. Every claim must trace back to a source in the evidence store or be explicitly marked `[ASSUMPTION]`.
- **Bounded delegation**: Maximum 2 levels of agent nesting, enforced by hooks.
- **User in the loop**: The pipeline pauses at every stage and every review gate for your approval before advancing.
- **Schema-driven**: All agent outputs conform to JSON schemas in `schemas/` — validated automatically by hooks.

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/Ozzstein/ProposalWriter.git
cd ProposalWriter

# 2. Install dependencies (for MCP server and hooks)
pip install fastmcp httpx pypdf

# 3. Open in Claude Code
claude

# 4. Start a new proposal
/start-proposal
```

Claude will walk you through gathering your project details, then you advance through the pipeline stage by stage using slash commands.

---

## Prerequisites

| Requirement | Why |
|---|---|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | The runtime harness — there is no separate application tier |
| Python 3.10+ | Hooks and MCP server |
| `fastmcp` + `httpx` | MCP server dependencies (`pip install fastmcp httpx`) |
| `pypdf` | PDF text extraction for call documents (`pip install pypdf`) |
| Firecrawl CLI (optional) | For the `web_scraper` agent to search EU repositories |
| Semantic Scholar MCP (optional) | Connected via Claude Code's MCP registry for academic search |

---

## Installation

```bash
git clone https://github.com/Ozzstein/ProposalWriter.git
cd ProposalWriter
pip install fastmcp httpx pypdf
```

The MCP server and hooks are configured automatically via `.claude/settings.json`. No additional setup is needed — open the project in Claude Code and start working.

---

## Pipeline Stages

The proposal pipeline has 5 main stages plus utility commands. Each stage is a slash command that orchestrates multiple agents.

| Stage | Command | What happens |
|---|---|---|
| 1. Initialise | `/start-proposal` | Gather project details, create directory structure, set up memory stores |
| 2. Parse call | `/parse-call` | Extract eligibility, evaluation criteria, section structure from the call document |
| 3. Research | `/research` | Gather evidence (literature, patents, web), synthesise SOTA, map novelty and gaps |
| 4. Write | `/write-proposal` | Draft all proposal sections using evidence from memory stores |
| 5. Review | `/review` | Red-team the proposal: scientific rigour, compliance, adversarial evaluator simulation |

**Utility commands:**
| Command | Purpose |
|---|---|
| `/gate-check [gate]` | Verify readiness before advancing (gates: `scope`, `evidence`, `draft`, `submission`) |
| `/pipeline-status` | Show current progress across all stages and gates |

---

## Slash Commands

### `/start-proposal`

Initialises a new proposal project. The system asks you for:
- Project name (kebab-case, used as directory name)
- Research topic and key hypothesis
- Funding agency and instrument (NIH R01, Horizon Europe, Innovation Fund, NSF)
- Prior work and preliminary data
- Team composition
- Target deadline

It also asks for the **call document** (the work programme / call fiche) and the **call template** (official Part B template). If you have an official template, it takes precedence over built-in templates.

**Output**: Creates `runs/{project-name}/` with `state.json`, `context.md`, and empty memory files.

### `/parse-call`

Parses the call document to extract everything needed to scope the proposal. Spawns two agents in parallel:
- **call_parser** (sonnet): extracts structure, evaluation criteria, page limits, deadlines
- **eligibility_parser** (haiku): extracts eligibility rules, disqualifiers, compliance requirements

Selects the appropriate proposal template (uploaded > built-in) and generates the proposal outline.

**Output**: `intermediate/call_brief.json`, `intermediate/evaluation_matrix.json`, `intermediate/proposal_outline.md`, `intermediate/eligibility_checklist.json`

### `/research`

Gathers and synthesises evidence in three phases:

**Phase 1 — Retrieval** (parallel):
- `literature_searcher` searches Consensus, PubMed, arXiv, Semantic Scholar
- `web_scraper` searches EU repositories (OpenAIRE, CORDIS, Zenodo, HAL) via Firecrawl
- `patent_scanner` searches Google Patents, USPTO, EPO

**Phase 2 — Synthesis** (sequential):
- `state_of_art_synthesizer` reads all evidence, produces a SOTA narrative, registers claims

**Phase 3 — Deep analysis** (parallel):
- `novelty_mapper` maps specific novelty positions with defensibility scores and attack surfaces
- `gap_analyzer` identifies and ranks gaps by strategic importance for the call

**Output**: `intermediate/sota_summary.md`, `intermediate/novelty_map.json`, `intermediate/gap_analysis.json`, populated `memory/evidence_store.jsonl` and `memory/claim_registry.jsonl`

### `/write-proposal`

Drafts all proposal sections, respecting the call's section structure and evaluation criteria.

**Phase 1** (parallel):
- `excellence_writer` drafts Section 1 (Innovation / Excellence) — the highest-weighted section
- `impact_writer` drafts significance, impact, GHG avoidance sections
- `implementation_writer` drafts methodology, maturity, workplan sections

**Phase 2** (sequential):
- `abstract_writer` synthesises all sections into the project summary (written last)

**Output**: `drafts/{section_name}.md` and `drafts/{section_name}_meta.json` for each section

### `/review`

Red-teams the proposal with three reviewer agents in parallel:
- `scientific_reviewer` checks scientific rigour, logical consistency, claim-evidence linkage
- `compliance_checker` checks template compliance, page limits, formatting, required sections
- `adversarial_evaluator_simulator` simulates an expert evaluation panel — predicts per-criterion scores, flags hard-rejection risks, ranks improvement actions by estimated score gain

**Output**: `reviews/scientific_review.json`, `reviews/compliance_review.json`, `reviews/evaluator_simulation.json`, `reviews/revision_plan.md`

### `/gate-check [gate-name]`

Verifies readiness before stage transitions. Four gates:

| Gate | When | Checks |
|---|---|---|
| `scope` | Before research | call_brief.json exists, evaluation_matrix.json exists, proposal_outline.md exists, context.md has hypothesis |
| `evidence` | Before writing | evidence store has >=12 entries, SOTA summary exists, novelty map has >=2 anchors, claim registry populated, <=20% unsupported claims |
| `draft` | Before review | all required sections have drafts, drafts reference claim_ids, <=2 unlinked `[ASSUMPTION]` markers per section, abstract exists |
| `submission` | Before export | scientific review score >=6.0 for all sections, no critical issues, compliance review passes, all unsupported claims resolved |

### `/pipeline-status`

Shows current progress: which stages are complete, which gates have passed, quick stats (evidence count, claim count, draft files, review scores).

---

## Agent Architecture

### Agent Types

| Type | Role | Model Tier | Example |
|---|---|---|---|
| **Retrievers** | Gather material, not conclusions | haiku | `literature_searcher`, `web_scraper`, `patent_scanner` |
| **Synthesizers** | Compare, rank, infer, structure | opus | `state_of_art_synthesizer`, `novelty_mapper`, `gap_analyzer` |
| **Writers** | Turn validated material into polished text | sonnet | `excellence_writer`, `impact_writer`, `implementation_writer` |
| **Reviewers** | Critique, score, identify weaknesses | opus | `adversarial_evaluator_simulator`, `scientific_reviewer` |

### Complete Agent Roster (17 agents)

**Orchestrators** (4):
| Agent | File | Mission |
|---|---|---|
| Call Scope Orchestrator | `agents/orchestrators/call_scope_orchestrator.md` | Parse call document, extract criteria and structure |
| Research Orchestrator | `agents/orchestrators/research_orchestrator.md` | Coordinate evidence retrieval and synthesis |
| Writing Orchestrator | `agents/orchestrators/proposal_writer_orchestrator.md` | Coordinate section drafting |
| Review Orchestrator | `agents/orchestrators/review_orchestrator.md` | Coordinate red-teaming and compliance |

**Workers — Retrievers** (5):
| Agent | File | Searches |
|---|---|---|
| `call_parser` | `agents/workers/retrievers/call_parser.md` | Call documents (PDF) |
| `eligibility_parser` | `agents/workers/retrievers/eligibility_parser.md` | Eligibility and compliance rules |
| `literature_searcher` | `agents/workers/retrievers/literature_searcher.md` | Consensus, PubMed, arXiv, Semantic Scholar |
| `web_scraper` | `agents/workers/retrievers/web_scraper.md` | OpenAIRE, CORDIS, Zenodo, HAL, bioRxiv (via Firecrawl) |
| `patent_scanner` | `agents/workers/retrievers/patent_scanner.md` | Google Patents, USPTO, EPO |

**Workers — Synthesizers** (3):
| Agent | File | Produces |
|---|---|---|
| `state_of_art_synthesizer` | `agents/workers/synthesizers/state_of_art_synthesizer.md` | `sota_summary.md`, claim registration |
| `novelty_mapper` | `agents/workers/synthesizers/novelty_mapper.md` | `novelty_map.json` (NOV-### anchors with defensibility scores) |
| `gap_analyzer` | `agents/workers/synthesizers/gap_analyzer.md` | `gap_analysis.json` (GAP-### entries ranked by strategic importance) |

**Workers — Writers** (4):
| Agent | File | Drafts |
|---|---|---|
| `excellence_writer` | `agents/workers/writers/excellence_writer.md` | Section 1 (IF: Degree of Innovation; HE: Excellence) |
| `impact_writer` | `agents/workers/writers/impact_writer.md` | Significance, impact, GHG avoidance sections |
| `implementation_writer` | `agents/workers/writers/implementation_writer.md` | Methodology, maturity, workplan sections |
| `abstract_writer` | `agents/workers/writers/abstract_writer.md` | Project summary / abstract (written last) |

**Workers — Reviewers** (1):
| Agent | File | Produces |
|---|---|---|
| `adversarial_evaluator_simulator` | `agents/workers/reviewers/adversarial_evaluator_simulator.md` | `evaluator_simulation.json` (per-criterion scores, hard-rejection checks, funding probability) |

### Bounded Delegation

Agent spawning follows strict rules enforced by hooks:
1. **Maximum depth: 2 levels** (orchestrator -> worker -> subworker)
2. Every spawn must have a clear justification
3. Every child must return structured output conforming to a schema
4. No duplicate spawns (deduplicated via `task_registry.jsonl`)

---

## Review Gates

Gates are checkpoints that prevent premature stage advancement. Run `/gate-check <name>` to check.

```
/start-proposal
      |
      v
  [scope gate] ---- /gate-check scope
      |
      v
   /parse-call
      |
      v
   /research
      |
      v
  [evidence gate] -- /gate-check evidence
      |
      v
  /write-proposal
      |
      v
  [draft gate] ----- /gate-check draft
      |
      v
   /review
      |
      v
  [submission gate] - /gate-check submission
      |
      v
   Export / Submit
```

If a gate fails, the system reports exactly which criteria are unmet and recommends actions to resolve each blocker.

---

## Schemas and Data Contracts

All agent I/O conforms to JSON schemas in `schemas/`. This enables automatic validation via hooks.

| Schema | Used By | Description |
|---|---|---|
| `evidence_result.json` | Retrievers | Sources with SRC-### IDs, quality ratings, extracts |
| `claim.json` | Synthesizers, Writers | Claims with CLM-### IDs, evidence linkage, status |
| `novelty_map.json` | `novelty_mapper` | NOV-### anchors with defensibility scores, attack surfaces |
| `gap_analysis.json` | `gap_analyzer` | GAP-### entries with severity, strategic importance, criterion mapping |
| `section_draft.json` | Writers | Section text with claim_ids, source_ids, assumptions, word count |
| `review_report.json` | Reviewers | Issues, unsupported claims, fixes ranked by priority |
| `evaluator_simulation.json` | `adversarial_evaluator_simulator` | Per-criterion predicted scores, hard-rejection checks, funding probability |
| `gate_check.json` | `/gate-check` | Gate pass/fail with criteria details and blockers |
| `task.json` | All agents | Standard input contract (task_id, goal, constraints) |
| `decision.json` | Program Director | Recorded decisions with rationale and alternatives considered |

### ID Conventions

| Pattern | Example | Used For |
|---|---|---|
| `SRC-###` | SRC-001 | Sources in evidence store |
| `CLM-###` | CLM-042 | Claims in claim registry |
| `NOV-###` | NOV-003 | Novelty anchors |
| `GAP-###` | GAP-007 | Documented gaps |
| `TASK-###` | TASK-015 | Spawned tasks |
| `DEC-###` | DEC-002 | Recorded decisions |

---

## Project File Structure

Each proposal lives in `runs/{project-name}/`:

```
runs/{project-name}/
  state.json                 # Pipeline state, stage status, gate status
  context.md                 # Your research context, hypothesis, team, project details

  inputs/                    # Call documents, research reports, templates (uploaded by you)
    call_document.pdf
    call_template.pdf
    research_report.pdf

  memory/                    # Shared stores (append-only JSONL)
    evidence_store.jsonl     # All retrieved sources with quality ratings
    claim_registry.jsonl     # Every proposal claim linked to evidence
    decision_log.jsonl       # Why key choices were made
    task_registry.jsonl      # Track all spawned tasks (deduplication)

  intermediate/              # Stage outputs (structured JSON + Markdown)
    call_brief.json          # Parsed call structure and criteria
    evaluation_matrix.json   # Full scoring rubric with weights and thresholds
    eligibility_checklist.json
    proposal_outline.md      # Section structure with page budgets
    sota_summary.md          # State-of-the-art narrative
    novelty_map.json         # Novelty anchors with defensibility scores
    gap_analysis.json        # Ranked gaps with criterion mapping

  drafts/                    # Section drafts (Markdown + JSON metadata)
    01_innovation.md
    01_innovation_meta.json
    ...

  reviews/                   # Review reports
    scientific_review.json
    compliance_review.json
    evaluator_simulation.json
    revision_plan.md

  final/                     # Export-ready proposal (assembled PDF)
```

---

## Hooks

Four Python hooks enforce system invariants. They are configured in `.claude/settings.json` and run automatically.

### PreToolUse hooks (run before agent spawning)

| Hook | File | Purpose |
|---|---|---|
| Deduplication | `hooks/check_dedupe.py` | Prevents spawning duplicate agents — checks `task_registry.jsonl` for existing tasks with the same `dedupe_key` |
| Depth limit | `hooks/check_depth.py` | Enforces max delegation depth of 2 — blocks agents from spawning sub-sub-agents |

### PostToolUse hooks (run after file writes)

| Hook | File | Purpose |
|---|---|---|
| Schema validation | `hooks/validate_output.py` | Validates JSON files written to `intermediate/` or `reviews/` against their schemas |
| Citation check | `hooks/check_citations.py` | Scans drafts for `CLM-###` references and warns if any are not in the claim registry |

---

## MCP Server

ProposalWriter includes a bundled MCP server for academic search:

**`mcp-servers/academic-search/server.py`**

Provides tools:
- `search_pubmed(query, max_results, date_from, date_to)` — Search PubMed via NCBI E-utilities
- `fetch_abstract(pmid)` — Fetch full abstract and MeSH terms for a PubMed article
- `fetch_mesh_terms(pmid)` — Fetch MeSH categorisation for related-paper discovery
- `search_arxiv(query, max_results, category, date_from, date_to)` — Search arXiv preprints
- `fetch_arxiv_paper(arxiv_id)` — Fetch full metadata for an arXiv paper

The server starts automatically when Claude Code opens the project (configured in `.claude/settings.json`).

**Additional search tools available via connected MCPs:**
- Semantic Scholar (connected via Claude Code's MCP registry)
- Firecrawl (for `web_scraper` agent — searches EU repositories)

---

## Templates

Built-in proposal templates in `templates/`:

| Template | File | Best For |
|---|---|---|
| Innovation Fund (large-scale) | `proposal_outline_innovation_fund_large.md` | EU Innovation Fund grants >7.5M |
| Horizon Europe RIA/IA | `proposal_outline_horizon_europe_ria.md` | Horizon Europe research/innovation actions |
| NIH R01 | `proposal_outline_nih_r01.md` | US NIH research project grants |
| NSF Standard | `proposal_outline_nsf.md` | US National Science Foundation |

**Template priority**: If you upload an official call template (the Part B document from the portal), it always takes precedence over built-in templates. The system asks for this during `/start-proposal`.

---

## Configuration

### `.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Agent", "command": "python hooks/check_dedupe.py" },
      { "matcher": "Agent", "command": "python hooks/check_depth.py" }
    ],
    "PostToolUse": [
      { "matcher": "Write", "command": "python hooks/validate_output.py" },
      { "matcher": "Write", "command": "python hooks/check_citations.py" }
    ]
  },
  "mcpServers": {
    "academic-search": {
      "command": "python3",
      "args": ["mcp-servers/academic-search/server.py"]
    }
  }
}
```

### `.claude/settings.local.json`

Machine-specific permissions (gitignored). Created automatically by Claude Code when you approve tool usage.

---

## Example Walkthrough

This walkthrough shows how to write an EU Innovation Fund proposal for an LFP battery manufacturing project.

### Step 1: Start the proposal

```
> /start-proposal
```

The system asks for project details. You provide:
- **Name**: `digital-twin-lfp-cam`
- **Topic**: Digital Twin for LFP cathode active material powder manufacturing
- **Instrument**: Innovation Fund large-scale
- **Hypothesis**: A physics-based, multi-scale digital twin can reduce scrap rates by >10% and energy consumption by 12-15%
- **Team**: FAAM (FIB S.p.A. & Eni)
- **Deadline**: 23 April 2026

Upload the call document and official application template when prompted.

### Step 2: Parse the call

```
> /parse-call
```

The system extracts evaluation criteria (105-point weighted scoring for CLEAN-TECH-MANUFACTURING topic), eligibility rules, mandatory annexes, and generates a proposal outline aligned to the official Part B template.

### Step 3: Check the scope gate

```
> /gate-check scope
```

Verifies: call_brief.json exists, evaluation_matrix.json exists, proposal_outline.md exists, context.md has hypothesis. All four criteria must pass before research can begin.

### Step 4: Run research

```
> /research
```

The system:
1. Searches literature databases (PubMed, arXiv, Semantic Scholar, Consensus)
2. Searches EU repositories (OpenAIRE, CORDIS, Zenodo) via Firecrawl
3. Scans patent databases (Google Patents, USPTO, EPO)
4. Synthesises all evidence into a SOTA narrative
5. Maps novelty positions (NOV-001: "No integrated DT for LFP CAM synthesis exists", defensibility: 9/10)
6. Ranks gaps (GAP-001: "No real-time PAT-driven calcination control for LFP", strategic importance: 10/10)

### Step 5: Check the evidence gate

```
> /gate-check evidence
```

Verifies: >=12 sources, SOTA summary, >=3 novelty anchors, >=4 gaps, <=20% unsupported claims.

### Step 6: Write the proposal

```
> /write-proposal
```

The system drafts all sections in parallel, with `excellence_writer` handling the highest-weighted Section 1 (Degree of Innovation) using novelty anchors and gap framing from the research stage.

### Step 7: Review

```
> /review
```

The adversarial evaluator simulator predicts scores per criterion, flags hard-rejection risks (e.g., GHG calculator not yet filled), and ranks the top 5 actions to improve the total score.

### Step 8: Iterate

Based on the review, you address the highest-impact issues first, then re-run `/review` until the submission gate passes.

```
> /gate-check submission
```

---

## License

This project is private. All rights reserved.
