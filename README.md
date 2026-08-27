# ProposalWriter

A multi-agent system for writing competitive grant proposals, built on [Claude Code](https://docs.anthropic.com/en/docs/claude-code). ProposalWriter coordinates 10 orchestrated pipeline stages across ~30 specialised agents — from idea development through parsing funding calls through evidence gathering, drafting, financials, figures, and adversarial review — producing evidence-grounded proposals aligned to evaluator scoring rubrics.

**Supported funding instruments**: EU Innovation Fund (large-scale), Horizon Europe (RIA/IA), NIH R01, NSF standard proposals.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Pipeline Stages](#pipeline-stages)
- [Agent Architecture](#agent-architecture)
- [Review Gates](#review-gates)
- [Scripts](#scripts)
- [Schemas and Data Contracts](#schemas-and-data-contracts)
- [Project File Structure](#project-file-structure)
- [Hooks](#hooks)
- [MCP Server](#mcp-server)
- [Templates](#templates)
- [The Wiki](#the-wiki)
- [Mission Control UI](#mission-control-ui)
- [Configuration](#configuration)
- [Example Walkthrough](#example-walkthrough)

---

## How It Works

ProposalWriter implements a **Program Director** pattern: you (the researcher) interact with a top-level orchestrator that delegates work to specialised agents in a strict hierarchy.

```
You (researcher)
 |
 v
Program Director (Claude Code session)
 |
 |-- /ideate ----------> interview (main conversation)
 |                       -> literature_searcher probes -> idea_evaluator
 |-- /parse-call ------> call_parser + eligibility_parser
 |-- /research --------> literature_searcher + web_scraper + patent_scanner
 |                       -> state_of_art_synthesizer
 |                       -> novelty_mapper + gap_analyzer
 |-- /write-proposal --> excellence_writer (first)
 |                       -> impact_writer + implementation_writer
 |                       -> abstract_writer (last)
 |-- /finance ---------> financial_modeler -> financial_narrative_writer -> financial_reviewer
 |-- /figures ---------> plot_renderer + concept_image_generator
 |-- /business-plan ---> bp_synthesizer -> 4 bp writers -> bp_reviewer
 |-- /review ----------> scientific_reviewer + compliance_checker
 |                       + adversarial_evaluator_simulator
 |-- /external-review -> feedback_parser -> triage -> specialist patching
 |-- /wiki ------------> cross-project knowledge ingest / query
```

**Key design principles:**
- **Evidence-first**: Writers never invent facts. Every claim must trace back to a source in the evidence store or be explicitly marked `[ASSUMPTION]`.
- **Native subagents**: Every worker is a Claude Code subagent with its model and tool restrictions pinned in `.claude/agents/` — writers and synthesizers physically cannot search the web, and no worker can spawn further agents.
- **Deterministic gates**: Stage-transition gates are computed by `scripts/gate_check.py` from project files alone — never by model judgment.
- **User in the loop**: The pipeline pauses at every stage and every review gate for your approval before advancing.
- **Schema-driven**: Agent outputs conform to JSON schemas in `schemas/`, validated automatically by hooks that feed violations back to the writing agent.

---

## Quick Start

```bash
git clone https://github.com/Ozzstein/ProposalWriter.git
cd ProposalWriter
pip install fastmcp httpx pypdf jsonschema

claude          # open the project in Claude Code
/start-proposal # begin
```

On Debian/Ubuntu (including WSL), the system Python is PEP 668-managed and the
`pip install` above will fail with `externally-managed-environment`. Use apt for
the hook dependencies and a project venv for the MCP server instead:

```bash
sudo apt install python3-jsonschema python3-pypdf   # hooks/scripts run under system python3
python3 -m venv .venv && .venv/bin/pip install fastmcp httpx pypdf
```

then point the academic-search server at the venv in `.claude/settings.local.json`
(gitignored, also where API keys go):

```json
{
  "mcpServers": {
    "academic-search": {
      "command": "/absolute/path/to/ProposalWriter/.venv/bin/python",
      "args": ["mcp-servers/academic-search/server.py"],
      "env": { "ELSEVIER_API_KEY": "<optional>" }
    }
  }
}
```

Claude walks you through gathering your project details, then you advance through the pipeline stage by stage using slash commands.

## Prerequisites

| Requirement | Why |
|---|---|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | The runtime harness — there is no separate application tier |
| Python 3.10+ | Hooks, gate/state scripts, and the MCP server |
| `fastmcp` + `httpx` | MCP server dependencies |
| `pypdf` | PDF text extraction for call documents |
| `jsonschema` | Full draft-07 validation in hooks and scripts (falls back to shallow checks without it) |
| Firecrawl (optional) | `web_scraper` agent searches EU repositories |
| Semantic Scholar MCP (optional) | Academic search for `literature_searcher` |
| Node.js ≥ 20 (optional) | Mission Control UI |

---

## Pipeline Stages

Each stage is a slash command. The command files in `.claude/commands/` are thin dispatchers — the corresponding orchestrator file in `agents/orchestrators/` is the single source of truth for which agents run, in what order, with what outputs.

| Stage | Command | What happens |
|---|---|---|
| 1. Initialise | `/start-proposal` | Gather project details; `scripts/state.py init` scaffolds the project |
| 2. Ideate | `/ideate` | *(optional, interactive)* Develop/refine the idea: interview, candidate framings, shallow prior-art probes, comparative scoring; chosen hypothesis written into `context.md` |
| 3. Parse call | `/parse-call` | Extract eligibility, evaluation criteria, section structure from the call document |
| 4. Research | `/research` | Retrieve evidence (literature, EU repositories, patents), synthesise SOTA, map novelty and gaps |
| 5. Write | `/write-proposal` | Draft all sections — excellence first, abstract last |
| 6. Finance | `/finance` | Build the financial model from user-supplied inputs, draft financial sections, red-team hard-rejection risks |
| 7. Figures | `/figures` | Render every figure in the figures register — data plots via Matplotlib/Plotly, concept art via Fal.ai |
| 8. Business plan | `/business-plan` | Assemble the Business Plan annex (interview → synthesis → 4 writers → red-team) |
| 9. Review | `/review` | Red-team: scientific rigour, compliance, adversarial evaluator simulation |
| 10. External review | `/external-review` | Ingest external reviewer comments (PDF/DOCX/XLSX/MD), triage, route to specialists, apply patches |

**Utility commands:**

| Command | Purpose |
|---|---|
| `/gate-check [gate]` | Run `scripts/gate_check.py` — deterministic readiness check (`scope`, `evidence`, `draft`, `submission`, `external-feedback`) |
| `/pipeline-status` | Render `scripts/state.py show` — stages, gates, store counts, feedback rounds |
| `/wiki` | Init / ingest / query / lint the cross-project knowledge base |

---

## Agent Architecture

### Worker classes

| Class | Role | Model | Tools |
|---|---|---|---|
| **Ideation** | Develop/refine the idea with the user | opus evaluator; interview runs in main conversation | File tools only |
| **Retrievers** | Gather material, not conclusions | haiku (call_parser and feedback_parser: sonnet) | Search retrievers inherit all tools (MCP search); document parsers get file tools + Bash |
| **Synthesizers** | Compare, rank, infer, structure | opus | File tools only — no web, no Bash |
| **Writers** | Turn validated material into polished text | sonnet | File tools only — no web, no Bash |
| **Reviewers** | Critique, score, identify weaknesses | opus (compliance_checker: haiku) | File tools (+ Bash for compliance word counts) |
| **Finance** | Model and narrate user-supplied numbers | sonnet (financial_reviewer: opus) | File tools + Bash |
| **Business plan** | Assemble the Business Plan annex | sonnet writers, opus synthesizer/reviewer | File tools |
| **Graphics** | Render figures | chosen per figure | File tools + Bash (+ WebFetch for Fal.ai) |

### Native subagents

Canonical worker definitions live in `agents/workers/{class}/{name}.md`. Each spawnable worker has a **generated stub** in `.claude/agents/{name}.md` whose frontmatter pins its model and tools — the harness enforces both, and subagents cannot spawn further agents, so delegation depth is platform-enforced.

```bash
python3 scripts/gen_agent_stubs.py           # regenerate after adding/renaming a worker
python3 scripts/gen_agent_stubs.py --check   # CI-style drift check
```

Never edit stubs by hand. `bp_interviewer` and `idea_interviewer` are deliberately not stubs — they are interview protocols the orchestrator runs in the main conversation.

Orchestrators spawn workers with `subagent_type` = the worker's name, and every task prompt carries `project:` and `dedupe_key:` lines (consumed by the dedupe hook).

### Roster

**Orchestrators** (10, in `agents/orchestrators/`): ideation, call_scope, research, proposal_writer, finance_lead, graphics, business_plan, review, external_review, wiki.

**Workers** (in `agents/workers/`):

| Class | Agents |
|---|---|
| ideation | idea_interviewer (protocol, orchestrator-run), idea_evaluator |
| retrievers | call_parser, eligibility_parser, feedback_parser, literature_searcher, web_scraper, patent_scanner |
| synthesizers | state_of_art_synthesizer, novelty_mapper, gap_analyzer |
| writers | excellence_writer, impact_writer, implementation_writer, abstract_writer, feedback_applier |
| reviewers | scientific_reviewer, compliance_checker, adversarial_evaluator_simulator |
| finance | financial_modeler, financial_narrative_writer, financial_reviewer |
| business_plan | bp_interviewer (protocol), bp_synthesizer, bp_commercial_writer, bp_financial_writer, bp_counterparty_writer, bp_risk_writer, bp_reviewer |
| graphics | plot_renderer, concept_image_generator |

---

## Review Gates

Gates prevent premature stage advancement. They are **computed deterministically** by `scripts/gate_check.py` — run via `/gate-check <name>`, which writes `intermediate/gate_check_<gate>.json` and updates `state.json` itself.

```
/start-proposal → /ideate (optional) → /parse-call → [scope] → /research → [evidence]
    → /write-proposal (+ /finance /figures /business-plan) → [draft]
    → /review → /external-review → [external-feedback] → [submission] → export
```

| Gate | Key criteria |
|---|---|
| `scope` | call_brief + evaluation_matrix parse, outline exists, context.md has a real (non-placeholder) hypothesis |
| `evidence` | ≥12 unique sources, SOTA summary, ≥3 novelty anchors, ≥4 gaps with top gaps selected, ≤20% unsupported claims |
| `draft` | Every outline section drafted, every draft cites claim IDs, ≤2 unlinked `[ASSUMPTION]` per section, abstract within limit |
| `submission` | Scientific score ≥6.0 per section, zero critical fixes, compliance clean, unsupported claims resolved or user-approved |
| `external-feedback` | Zero open/in-progress comments in the active round; stale items carry an explanation (N/A if no external review ingested) |

Exit codes: `0` pass, `1` fail (blockers listed), `2` project error, `3` not applicable.

---

## Scripts

| Script | Purpose |
|---|---|
| `scripts/state.py` | All state mutations: `init` (scaffold a project), `stage`, `gate`, schema-validated `append` to memory stores, `show`, `projects`. Never hand-edit `state.json`. |
| `scripts/gate_check.py` | Deterministic gate evaluation (see above) |
| `scripts/gen_agent_stubs.py` | Generate/refresh native subagent stubs from `agents/workers/` |

All accept `--runs-dir` for testing outside `runs/`.

---

## Schemas and Data Contracts

All agent I/O conforms to JSON schemas in `schemas/`, enforced by hooks.

| Schema | Used By |
|---|---|
| `evidence_result.json` | Retrievers (incl. `/ideate` probes) |
| `ideation_brief.json` | idea_evaluator |
| `claim.json` | Synthesizers, writers, `state.py append` |
| `novelty_map.json` / `gap_analysis.json` | novelty_mapper / gap_analyzer |
| `section_draft.json` | Writers (`*_meta.json` sidecars) |
| `review_report.json` | Reviewers |
| `evaluator_simulation.json` | adversarial_evaluator_simulator |
| `feedback_entry.json` / `feedback_patch.json` | External review pipeline |
| `financial_inputs.json` | `/finance` Phase 0 ingest |
| `figure_spec.json` | Graphics sidecar JSONs |
| `gate_check.json` | `scripts/gate_check.py` |
| `task.json` / `decision.json` | Task registry / decision log |

### ID Conventions

| Pattern | Used For |
|---|---|
| `SRC-###` / `WIKI-SRC-###` | Sources (project-local / imported from wiki) |
| `CLM-###` / `WIKI-CLM-###` / `CLM-FIN-###` | Claims (core / wiki-imported / financial) |
| `NOV-###` / `GAP-###` | Novelty anchors / documented gaps |
| `TASK-###` / `DEC-###` / `FBK-###` | Tasks / decisions / external feedback comments |
| `F-##` | Figures |

---

## Project File Structure

Each proposal lives in `runs/{project-name}/` (scaffolded by `state.py init`):

```
runs/{project-name}/
  state.json                 # Pipeline state — edit only via scripts/state.py
  context.md                 # Your research context, hypothesis, team
  inputs/                    # Call documents, templates, financial inputs
  memory/                    # Append-only JSONL stores
    evidence_store.jsonl     #   sources with quality ratings
    claim_registry.jsonl     #   claims linked to evidence
    decision_log.jsonl       #   why key choices were made
    task_registry.jsonl      #   spawned tasks (dedupe)
    feedback_log.jsonl       #   external review comments across rounds
  intermediate/              # Stage outputs (ideation_brief, call_brief, sota_summary,
                             #   novelty_map, gap_analysis, gate_check_*, …)
  drafts/                    # Section drafts + *_meta.json sidecars
  figures/                   # Rendered figures + sidecar JSONs + scripts
  reviews/                   # scientific / compliance / evaluator_simulation /
                             #   financial / business_plan reviews, revision_plan.md
  final/                     # Export-ready proposal
```

---

## Hooks

Configured in `.claude/settings.json`, run automatically by Claude Code. Violations are fed back to the model (stderr + exit 2 for PostToolUse; a deny decision for PreToolUse), so agents see and fix their own mistakes. All hooks fail open — a hook bug never wedges the pipeline.

| Hook | Event | Purpose |
|---|---|---|
| `check_dedupe.py` | PreToolUse (Task) | Blocks duplicate spawns of *running* tasks (keyed on the prompt's `dedupe_key:`/`project:` lines). Completed tasks may re-run; stale (>24h) running tasks don't block. |
| `validate_output.py` | PostToolUse (Write) | Full draft-07 validation of JSON written to `intermediate/`/`reviews/` against `schemas/` |
| `check_citations.py` | PostToolUse (Write) | Flags `CLM`/`WIKI-CLM`/`CLM-FIN` references in drafts that aren't in the claim registry |
| `emit_event.py` | All events | Telemetry to `runs/_events.jsonl` for the Mission Control UI |

---

## MCP Server

`mcp-servers/academic-search/server.py` provides PubMed and arXiv search/fetch tools (`search_pubmed`, `fetch_abstract`, `fetch_mesh_terms`, `search_arxiv`, `fetch_arxiv_paper`). It starts automatically with the project. Semantic Scholar and Firecrawl connect via Claude Code's MCP registry.

---

## Templates

Built-in proposal outlines in `templates/`: Innovation Fund large-scale, Horizon Europe RIA/IA, NIH R01, NSF standard — plus `reviewer_checklist.md` and triage/diff-summary templates for the review stages. An uploaded official call template (the Part B from the funder portal) always takes precedence over built-ins.

---

## The Wiki

`wiki/` is a persistent, cross-project knowledge base: sources, pre-validated claims, gaps, competitor entities, concepts, and funding-call intelligence. The research stage imports relevant wiki knowledge before searching (`WIKI-SRC`/`WIKI-CLM` prefixes); after a run completes, `/wiki ingest {project}` promotes new knowledge back. See `wiki/WIKI.md` for conventions.

---

## Mission Control UI

A local dashboard (`ui/`) for monitoring and driving the pipeline: project overview, live agent graph, streaming activity feed from the telemetry hook, memory-store browsing, and SDK-driven stage launches.

```sh
cd ui && npm install && npm run dev
# web: http://127.0.0.1:5173   api: http://127.0.0.1:7777
```

See `ui/README.md` for details.

---

## Configuration

`.claude/settings.json` wires the hooks and MCP servers (API keys for optional services belong in your environment or `settings.local.json`, not in committed files):

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Task", "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/hooks/check_dedupe.py\"" }] }
    ],
    "PostToolUse": [
      { "matcher": "Write", "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/hooks/validate_output.py\"" }] },
      { "matcher": "Write", "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/hooks/check_citations.py\"" }] }
    ]
  },
  "mcpServers": {
    "academic-search": { "command": "python3", "args": ["mcp-servers/academic-search/server.py"] }
  }
}
```

`.claude/agents/` holds the generated worker stubs (see [Native subagents](#native-subagents)). `.claude/settings.local.json` holds machine-specific permissions and is gitignored.

---

## Example Walkthrough

Writing an EU Innovation Fund proposal for an advanced battery-manufacturing project:

1. **`/start-proposal`** — provide the project name, topic, hypothesis (e.g. "a physics-based digital twin can cut scrap rates >10%"), team, and deadline; upload the call document and official Part B template when prompted. A firm hypothesis skips ideation; a fuzzy one routes to `/ideate`.
2. **`/ideate`** *(if the idea needs work)* — an interactive interview turns the raw notion into 2–3 candidate framings; shallow prior-art probes and a comparative scoring pass show which framing survives scrutiny; the chosen hypothesis lands in `context.md` with the probe sources already in the evidence store.
3. **`/parse-call`** — extracts the weighted scoring rubric, eligibility rules, and mandatory annexes; generates an outline matching the official template.
4. **`/gate-check scope`** — deterministic check that parsing produced everything research needs.
5. **`/research`** — searches literature, EU repositories, and patents; synthesises the SOTA; maps novelty anchors with defensibility scores and ranks gaps by strategic importance.
6. **`/gate-check evidence`** — ≥12 sources, ≥3 anchors, ≥4 gaps, ≤20% unsupported claims.
7. **`/write-proposal`** — excellence_writer drafts the highest-weighted section first from the novelty map; impact and implementation follow; abstract last.
8. **`/finance`**, **`/figures`**, **`/business-plan`** — financial model and narratives, all registered figures, and the Business Plan annex.
9. **`/review`** — the adversarial evaluator simulator predicts per-criterion scores, flags hard-rejection risks, and ranks revisions by score impact.
10. Iterate on the revision plan, ingest external reviewer feedback with **`/external-review`**, and close with **`/gate-check submission`**.

---

## License

All rights reserved.
